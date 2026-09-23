#!/usr/bin/env python3
"""S3: selectivity-preserving controls for filtered-ANN clustering effects.

Primary index: HNSW M32/efConstruction200/efSearch64 with postfilter K'=4K/s.
Negative control: 100 uniformly shuffled masks with exactly the natural-mask
count. Positive control: fixed-size masks with a controlled nearest-anchor
fraction. See the frozen protocol in project_md/archive/legacy_premerge_20260728/912_*.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = PROJECT_ROOT / "2026_KIISE" / "scripts"
sys.path.insert(0, str(SCRIPTS))
from run_filtered_ann_real_predicate import masks_corpus_a, masks_corpus_b  # noqa: E402

SIN = PROJECT_ROOT / "Datasets" / "processed" / "sinnaedoro_traffic" / "corpus_real"
V522 = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
PILLAR_B = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260710_pillarB"
DEFAULT_OUT = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets"
    / "20260723_controlled_supplement" / "s3_cluster_mechanism"
)
K = 10


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def mask_sha256(mask: np.ndarray) -> str:
    return hashlib.sha256(np.packbits(mask).tobytes()).hexdigest()


def stable_seed(*parts: object) -> int:
    payload = ":".join(map(str, parts)).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "little") % (2**32)


def normalize(array: np.ndarray) -> np.ndarray:
    array = np.asarray(array, dtype="float32")
    return array / np.maximum(np.linalg.norm(array, axis=1, keepdims=True), 1e-12)


def load_corpus(corpus: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[tuple[str, str, np.ndarray]], Path]:
    if corpus == "A":
        embedding_path = SIN / "frame_embeddings.npy"
        vectors = normalize(np.load(embedding_path))
        frame = pd.read_parquet(SIN / "frame_index.parquet")
        queries = normalize(np.load(SIN / "queries.npy"))
        self_ids = np.full(len(queries), -1, dtype=np.int64)
        masks = masks_corpus_a(frame)
    else:
        embedding_path = V522 / "visual_embeddings_clip" / "frame_embeddings.npy"
        vectors = normalize(np.load(embedding_path))
        frame_index = pd.read_parquet(V522 / "visual_embeddings_clip" / "frame_index.parquet")
        joined = pd.read_parquet(V522 / "visual_sensor_join.parquet")
        joined = joined[joined.join_ok_120s][
            [
                "visual_video_id", "split", "time_of_day", "hour",
                "sig_has_yellow", "sig_has_pedestrian", "veh_density_bin",
            ]
        ]
        frame = frame_index.merge(
            joined, on=["visual_video_id", "split"], how="left", suffixes=("_fn", "")
        )
        masks = masks_corpus_b(frame)
        rng = np.random.default_rng(20260710)
        self_ids = rng.choice(len(vectors), 200, replace=False)
        queries = vectors[self_ids]

    natural_masks = [(name, kind, mask) for name, kind, mask in masks if kind == "natural"]
    registered = pd.read_csv(PILLAR_B / f"P1_predicates_{corpus}.csv")
    count_by_name = dict(zip(registered["predicate"], registered["count"], strict=True))
    for name, _kind, mask in natural_masks:
        if name not in count_by_name:
            raise AssertionError(f"unregistered predicate: {name}")
        if int(mask.sum()) != int(count_by_name[name]):
            raise AssertionError(
                f"registered-count mismatch for {name}: {mask.sum()} != {count_by_name[name]}"
            )
    return vectors, queries, self_ids, natural_masks, embedding_path


def filtered_top(rankings: np.ndarray, mask: np.ndarray, self_ids: np.ndarray, k: int = K) -> tuple[np.ndarray, np.ndarray]:
    output = np.full((len(rankings), k), -1, dtype=np.int64)
    counts = np.zeros(len(rankings), dtype=np.int16)
    for query_index, (row, self_id) in enumerate(zip(rankings, self_ids, strict=True)):
        valid = row >= 0
        valid &= mask[np.maximum(row, 0)]
        if self_id >= 0:
            valid &= row != self_id
        selected = row[valid][:k]
        output[query_index, : len(selected)] = selected
        counts[query_index] = len(selected)
    return output, counts


def recall_at_k(exact: np.ndarray, approximate: np.ndarray, k: int = K) -> np.ndarray:
    result = np.empty(len(exact), dtype="float32")
    for index, (truth, got) in enumerate(zip(exact, approximate, strict=True)):
        truth_set = set(truth[truth >= 0].tolist())
        got_set = set(got[got >= 0].tolist())
        result[index] = len(truth_set & got_set) / k
    return result


def pairwise_cosine_mean(vectors: np.ndarray, mask: np.ndarray) -> float:
    selected = vectors[mask].astype("float64", copy=False)
    n = len(selected)
    if n < 2:
        return float("nan")
    vector_sum = selected.sum(axis=0)
    return float((vector_sum @ vector_sum - n) / (n * (n - 1)))


def holm_adjust(pvalues: np.ndarray) -> np.ndarray:
    order = np.argsort(pvalues)
    adjusted = np.empty_like(pvalues, dtype=float)
    running = 0.0
    m = len(pvalues)
    for rank, index in enumerate(order):
        value = min(1.0, float(pvalues[index]) * (m - rank))
        running = max(running, value)
        adjusted[index] = running
    return adjusted


def bootstrap_mean_ci(values: np.ndarray, seed: int, draws: int) -> tuple[float, float]:
    values = values[np.isfinite(values)]
    if not len(values):
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    sampled = values[rng.integers(0, len(values), size=(draws, len(values)))]
    means = sampled.mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


class ExactGroundTruth:
    def __init__(
        self,
        vectors: np.ndarray,
        queries: np.ndarray,
        self_ids: np.ndarray,
        faiss_module,
        start_l: int,
        max_l: int,
        failure_fraction: float,
    ) -> None:
        self.vectors = vectors
        self.queries = queries
        self.self_ids = self_ids
        self.faiss = faiss_module
        self.start_l = start_l
        self.max_l = max_l
        self.failure_fraction = failure_fraction
        self.flat = faiss_module.IndexFlatIP(vectors.shape[1])
        self.flat.add(vectors)
        self.cache: dict[int, np.ndarray] = {}

    def rankings(self, l_value: int) -> np.ndarray:
        l_value = min(len(self.vectors), l_value)
        if l_value not in self.cache:
            _, indices = self.flat.search(self.queries, min(len(self.vectors), l_value + 1))
            self.cache[l_value] = indices
        return self.cache[l_value]

    def for_mask(self, mask: np.ndarray) -> tuple[np.ndarray, dict]:
        l_value = self.start_l
        while True:
            top, counts = filtered_top(self.rankings(l_value), mask, self.self_ids)
            failed_fraction = float((counts < K).mean())
            if failed_fraction <= self.failure_fraction:
                return top, {
                    "gt_mode": "global_top_l_filter",
                    "exact_top_l": int(l_value),
                    "coverage_failure_fraction": failed_fraction,
                }
            if l_value >= self.max_l or l_value >= len(self.vectors):
                break
            l_value = min(self.max_l, len(self.vectors), l_value * 2)

        subset_ids = np.flatnonzero(mask).astype(np.int64)
        subset = np.ascontiguousarray(self.vectors[subset_ids])
        index = self.faiss.IndexFlatIP(self.vectors.shape[1])
        index.add(subset)
        _, local = index.search(self.queries, K + 1)
        global_ranks = subset_ids[np.maximum(local, 0)]
        exact, counts = filtered_top(global_ranks, mask, self.self_ids)
        if np.any(counts < K):
            raise AssertionError("subset Flat failed to supply K exact neighbors")
        return exact, {
            "gt_mode": "subset_flat_fallback",
            "exact_top_l": int(l_value),
            "coverage_failure_fraction": float((counts < K).mean()),
        }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", choices=["A", "B"], required=True)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--methods", default="hnsw", help="comma-separated: hnsw,ivf")
    parser.add_argument("--shuffles", type=int, default=100)
    parser.add_argument("--anchors", type=int, default=10)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260723)
    parser.add_argument("--exact-top-l", type=int, default=5000)
    parser.add_argument("--exact-top-l-max", type=int, default=40000)
    parser.add_argument("--coverage-failure-fraction", type=float, default=0.005)
    parser.add_argument("--limit-predicates", type=int, default=None)
    parser.add_argument("--limit-anchors", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    methods = [value.strip() for value in args.methods.split(",") if value.strip()]
    if not methods or not set(methods) <= {"hnsw", "ivf"}:
        raise ValueError("--methods must contain hnsw and/or ivf")

    output_dir = args.output_root / f"corpus_{args.corpus}_{'-'.join(methods)}"
    if output_dir.exists() and any(output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{output_dir} is not empty; pass --overwrite")
    output_dir.mkdir(parents=True, exist_ok=True)

    import faiss

    faiss.omp_set_num_threads(0)
    vectors, queries, self_ids, natural_masks, embedding_path = load_corpus(args.corpus)
    expected_hash = {
        "A": "40e80ea12fd4f95f95a0a4cb656f98d6162071fddf4160bf2c7997181ff4278b",
        "B": "6add5013ba9c4033a014da0bab51a434f4fa6e2ee33b364f1a6689331ccc5716",
    }[args.corpus]
    observed_hash = sha256_file(embedding_path)
    if observed_hash != expected_hash:
        raise ValueError(f"frozen embedding hash mismatch: {observed_hash}")
    if args.limit_predicates is not None:
        natural_masks = natural_masks[: args.limit_predicates]

    n_documents, dimension = vectors.shape
    print(
        f"[{args.corpus}] documents={n_documents} dim={dimension} queries={len(queries)} "
        f"natural_predicates={len(natural_masks)} methods={methods}",
        flush=True,
    )
    build_seconds: dict[str, float] = {}
    hnsw = None
    if "hnsw" in methods:
        start = time.perf_counter()
        hnsw = faiss.IndexHNSWFlat(dimension, 32, faiss.METRIC_INNER_PRODUCT)
        hnsw.hnsw.efConstruction = 200
        hnsw.add(vectors)
        hnsw.hnsw.efSearch = 64
        build_seconds["hnsw"] = time.perf_counter() - start
        print(f"[index] HNSW built in {build_seconds['hnsw']:.1f}s", flush=True)

    ivf = None
    if "ivf" in methods:
        start = time.perf_counter()
        quantizer = faiss.IndexFlatIP(dimension)
        ivf = faiss.IndexIVFFlat(quantizer, dimension, 1024, faiss.METRIC_INNER_PRODUCT)
        ivf.train(vectors)
        ivf.add(vectors)
        build_seconds["ivf"] = time.perf_counter() - start
        print(f"[index] IVF-Flat built in {build_seconds['ivf']:.1f}s", flush=True)

    gt_provider = ExactGroundTruth(
        vectors,
        queries,
        self_ids,
        faiss,
        args.exact_top_l,
        args.exact_top_l_max,
        args.coverage_failure_fraction,
    )
    approximate_cache: dict[tuple[str, int], np.ndarray] = {}

    def approximate_for_mask(method: str, mask: np.ndarray) -> tuple[np.ndarray, int]:
        selectivity = float(mask.mean())
        if method == "hnsw":
            kprime = min(n_documents, int(np.ceil(K / selectivity) * 4))
            key = (method, kprime)
            if key not in approximate_cache:
                assert hnsw is not None
                _, ranks = hnsw.search(queries, min(n_documents, kprime + 1))
                approximate_cache[key] = ranks
            top, _counts = filtered_top(approximate_cache[key], mask, self_ids)
            return top, kprime
        assert ivf is not None
        subset_ids = np.flatnonzero(mask).astype("int64")
        selector = faiss.IDSelectorBatch(subset_ids)
        parameters = faiss.SearchParametersIVF(sel=selector, nprobe=8)
        _, ranks = ivf.search(queries, K + 1, params=parameters)
        top, _counts = filtered_top(ranks, mask, self_ids)
        return top, K

    aggregate_rows: list[dict] = []
    per_query_rows: list[dict] = []

    def evaluate_mask(
        name: str,
        mask_type: str,
        mask: np.ndarray,
        *,
        repeat: int | None = None,
        anchor: int | None = None,
        selectivity_target: float | None = None,
        concentration: float | None = None,
        save_per_query: bool = False,
        clustering_metric: float | None = None,
    ) -> None:
        exact, gt_meta = gt_provider.for_mask(mask)
        for method in methods:
            approximate, kprime = approximate_for_mask(method, mask)
            recalls = recall_at_k(exact, approximate)
            row = {
                "corpus": args.corpus,
                "method": method,
                "mask_type": mask_type,
                "name": name,
                "repeat": repeat,
                "anchor": anchor,
                "selectivity_target": selectivity_target,
                "concentration": concentration,
                "count": int(mask.sum()),
                "selectivity": float(mask.mean()),
                "mask_sha256": mask_sha256(mask),
                "mean_recall_at_10": float(recalls.mean()),
                "recall_loss": float(1.0 - recalls.mean()),
                "queries_below_full_recall": int((recalls < 1.0).sum()),
                "kprime": int(kprime),
                "mean_pairwise_cosine": clustering_metric,
                **gt_meta,
            }
            aggregate_rows.append(row)
            if save_per_query:
                for query_index, recall in enumerate(recalls):
                    per_query_rows.append(
                        {
                            "corpus": args.corpus,
                            "method": method,
                            "mask_type": mask_type,
                            "name": name,
                            "repeat": repeat,
                            "anchor": anchor,
                            "selectivity_target": selectivity_target,
                            "concentration": concentration,
                            "query_index": query_index,
                            "recall_at_10": float(recall),
                        }
                    )

    # Negative control.
    for predicate_index, (name, _kind, natural_mask) in enumerate(natural_masks):
        started = time.perf_counter()
        natural_mask = np.asarray(natural_mask, dtype=bool)
        natural_count = int(natural_mask.sum())
        evaluate_mask(
            name,
            "natural",
            natural_mask,
            save_per_query=True,
            clustering_metric=pairwise_cosine_mean(vectors, natural_mask),
        )
        for repeat in range(args.shuffles):
            rng = np.random.default_rng(stable_seed(args.seed, args.corpus, predicate_index, repeat))
            shuffle_mask = np.zeros(n_documents, dtype=bool)
            shuffle_mask[rng.choice(n_documents, natural_count, replace=False)] = True
            if int(shuffle_mask.sum()) != natural_count:
                raise AssertionError("shuffle did not preserve the exact count")
            evaluate_mask(name, "shuffle", shuffle_mask, repeat=repeat)
        pd.DataFrame(aggregate_rows).to_csv(output_dir / "aggregate_partial.csv", index=False)
        print(
            f"[negative {predicate_index + 1}/{len(natural_masks)}] {name} "
            f"count={natural_count} elapsed={time.perf_counter() - started:.1f}s",
            flush=True,
        )

    # Positive control.
    anchor_count = args.limit_anchors or args.anchors
    stable_order = sorted(
        range(n_documents),
        key=lambda index: hashlib.sha256(f"{args.seed}:{index}".encode()).digest(),
    )
    anchor_ids = stable_order[:anchor_count]
    selectivities = (0.05, 0.10, 0.20, 0.40)
    concentrations = (0.0, 0.25, 0.50, 0.75, 1.0)
    for anchor_number, anchor_id in enumerate(anchor_ids):
        similarities = vectors @ vectors[anchor_id]
        nearest_order = np.lexsort((np.arange(n_documents), -similarities))
        for selectivity in selectivities:
            count = int(round(selectivity * n_documents))
            uniform_rng = np.random.default_rng(
                stable_seed(args.seed, args.corpus, "synthetic", anchor_number, selectivity)
            )
            uniform_order = uniform_rng.permutation(n_documents)
            for concentration in concentrations:
                nearest_count = int(round(concentration * count))
                selected = list(nearest_order[:nearest_count])
                selected_set = set(selected)
                if len(selected) < count:
                    for index in uniform_order:
                        if index not in selected_set:
                            selected.append(int(index))
                            selected_set.add(int(index))
                            if len(selected) == count:
                                break
                synthetic_mask = np.zeros(n_documents, dtype=bool)
                synthetic_mask[np.asarray(selected, dtype=np.int64)] = True
                if int(synthetic_mask.sum()) != count:
                    raise AssertionError("synthetic mask did not preserve the exact count")
                evaluate_mask(
                    f"synthetic_s{selectivity:.2f}_c{concentration:.2f}",
                    "synthetic",
                    synthetic_mask,
                    anchor=anchor_number,
                    selectivity_target=selectivity,
                    concentration=concentration,
                    save_per_query=True,
                    clustering_metric=pairwise_cosine_mean(vectors, synthetic_mask),
                )
        pd.DataFrame(aggregate_rows).to_csv(output_dir / "aggregate_partial.csv", index=False)
        print(f"[positive {anchor_number + 1}/{anchor_count}] anchor_doc={anchor_id}", flush=True)

    aggregate = pd.DataFrame(aggregate_rows)
    per_query = pd.DataFrame(per_query_rows)
    negative_rows: list[dict] = []
    for method in methods:
        subset = aggregate[(aggregate["method"] == method) & aggregate["mask_type"].isin(["natural", "shuffle"])]
        for name, group in subset.groupby("name", sort=False):
            natural_loss = float(group.loc[group["mask_type"] == "natural", "recall_loss"].iloc[0])
            null = group.loc[group["mask_type"] == "shuffle", "recall_loss"].to_numpy(float)
            upper = (1 + int((null >= natural_loss).sum())) / (len(null) + 1)
            lower = (1 + int((null <= natural_loss).sum())) / (len(null) + 1)
            p_two_sided = min(1.0, 2 * min(upper, lower))
            null_sd = float(null.std(ddof=1))
            negative_rows.append(
                {
                    "method": method,
                    "predicate": name,
                    "natural_loss": natural_loss,
                    "shuffle_mean_loss": float(null.mean()),
                    "natural_minus_shuffle": natural_loss - float(null.mean()),
                    "shuffle_sd": null_sd,
                    "z_score": (
                        (natural_loss - float(null.mean())) / null_sd if null_sd > 0 else float("nan")
                    ),
                    "p_two_sided": p_two_sided,
                }
            )
    negative = pd.DataFrame(negative_rows)
    negative["holm_p"] = np.nan
    for method in methods:
        use = negative["method"] == method
        negative.loc[use, "holm_p"] = holm_adjust(negative.loc[use, "p_two_sided"].to_numpy())

    slope_rows: list[dict] = []
    synthetic = aggregate[aggregate["mask_type"] == "synthetic"]
    for method in methods:
        method_frame = synthetic[synthetic["method"] == method]
        for anchor, anchor_frame in method_frame.groupby("anchor"):
            selectivity_slopes: list[float] = []
            for _selectivity, cell in anchor_frame.groupby("selectivity_target"):
                x = cell["concentration"].to_numpy(float)
                y = cell["recall_loss"].to_numpy(float)
                selectivity_slopes.append(float(np.polyfit(x, y, 1)[0]))
            slope_rows.append(
                {
                    "method": method,
                    "anchor": int(anchor),
                    "mean_within_selectivity_slope": float(np.mean(selectivity_slopes)),
                }
            )
    slopes = pd.DataFrame(slope_rows)

    gate_by_method: dict[str, dict] = {}
    for method in methods:
        differences = negative.loc[negative["method"] == method, "natural_minus_shuffle"].to_numpy(float)
        neg_lo, neg_hi = bootstrap_mean_ci(differences, args.seed, args.bootstrap)
        anchor_slopes = slopes.loc[
            slopes["method"] == method, "mean_within_selectivity_slope"
        ].to_numpy(float)
        slope_lo, slope_hi = bootstrap_mean_ci(anchor_slopes, args.seed + 1, args.bootstrap)
        gate_by_method[method] = {
            "negative_control": {
                "predicates": int(len(differences)),
                "mean_natural_minus_shuffle_loss": float(np.mean(differences)),
                "predicate_bootstrap_ci": [neg_lo, neg_hi],
                "positive_predicate_fraction": float((differences > 0).mean()),
                "pass": bool(neg_lo > 0 and (differences > 0).mean() >= 0.5),
            },
            "positive_control": {
                "anchors": int(len(anchor_slopes)),
                "mean_within_selectivity_slope": float(np.mean(anchor_slopes)),
                "anchor_bootstrap_ci": [slope_lo, slope_hi],
                "pass": bool(slope_lo > 0),
            },
        }
        gate_by_method[method]["within_corpus_pass"] = bool(
            gate_by_method[method]["negative_control"]["pass"]
            and gate_by_method[method]["positive_control"]["pass"]
        )

    summary = {
        "analysis": "S3 selectivity-preserving filtered-ANN mechanism controls",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "corpus": args.corpus,
        "documents": int(n_documents),
        "dimension": int(dimension),
        "queries": int(len(queries)),
        "natural_predicates": int(len(natural_masks)),
        "shuffle_repetitions": int(args.shuffles),
        "synthetic_anchors": int(anchor_count),
        "methods": methods,
        "gates": gate_by_method,
        "claim_rule": (
            "Causal wording requires both negative and positive HNSW gates in both corpora; "
            "a single-corpus pass is insufficient."
        ),
    }
    manifest = {
        "script": Path(__file__).name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parameters": vars(args) | {
            "output_root": str(args.output_root),
            "methods": methods,
        },
        "embedding_path": str(embedding_path),
        "embedding_sha256": observed_hash,
        "build_seconds": build_seconds,
        "index_parameters": {
            "hnsw": {"M": 32, "efConstruction": 200, "efSearch": 64, "postfilter_multiplier": 4},
            "ivfflat": {"nlist": 1024, "nprobe": 8, "selector": "IDSelectorBatch"},
        },
        "query_rule": (
            "A: frozen 1000 text query vectors; "
            "B: 200 image vectors selected by numpy RNG seed 20260710, self-excluded"
        ),
        "anchor_document_ids": anchor_ids,
    }

    aggregate.to_csv(output_dir / "aggregate.csv", index=False)
    per_query.to_parquet(output_dir / "per_query_primary.parquet", index=False)
    negative.to_csv(output_dir / "negative_control.csv", index=False)
    slopes.to_csv(output_dir / "positive_control_slopes.csv", index=False)
    (output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    (output_dir / "sha256.txt").write_text(
        "\n".join(
            f"{sha256_file(path)}  {path.name}"
            for path in sorted(output_dir.iterdir())
            if path.is_file() and path.name not in {"sha256.txt", "aggregate_partial.csv"}
        )
        + "\n",
        encoding="utf-8",
    )
    if (output_dir / "aggregate_partial.csv").exists():
        (output_dir / "aggregate_partial.csv").unlink()
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
