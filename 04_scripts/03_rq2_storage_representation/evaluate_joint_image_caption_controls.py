#!/usr/bin/env python3
"""Evaluate equal-budget one-vector image-caption fusion controls on frozen 522."""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CANONICAL = Path(
    "/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/"
    "qwen35_9b/522/canonical"
)
DEFAULT_BASE = (
    PROJECT_ROOT
    / "Datasets"
    / "processed"
    / "aihub_522_intersection"
    / "20260710"
    / "embeddings_qwen3vl2b_unified_qwen35captions"
)
DEFAULT_MATCHED = (
    PROJECT_ROOT
    / "Datasets"
    / "processed"
    / "aihub_522_intersection"
    / "20260710"
    / "embeddings_qwen3vl2b_joint_image_caption_qwen35captions"
)
DEFAULT_SHUFFLED = (
    PROJECT_ROOT
    / "Datasets"
    / "processed"
    / "aihub_522_intersection"
    / "20260710"
    / "embeddings_qwen3vl2b_joint_image_caption_qwen35captions_shuffled"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260717_joint_image_caption_controls"
)
TOP_KS = (1, 5, 10, 20)
MAX_RANK = 100
SEED = 20260717


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--base-embedding-root", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--matched-root", type=Path, default=DEFAULT_MATCHED)
    parser.add_argument("--shuffled-root", type=Path, default=DEFAULT_SHUFFLED)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--latency-repeats", type=int, default=10)
    parser.add_argument("--latency-warmup", type=int, default=2)
    parser.add_argument("--bootstrap-reps", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while data := handle.read(chunk):
            digest.update(data)
    return digest.hexdigest()


def normalize(matrix: np.ndarray) -> np.ndarray:
    value = np.ascontiguousarray(matrix.astype("float32", copy=True))
    faiss.normalize_L2(value)
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def positives(path: Path) -> dict[str, set[str]]:
    frame = pd.read_csv(path, sep="\t")
    return {
        str(query_id): set(group["target_id"].astype(str))
        for query_id, group in frame.groupby("query_id", sort=False)
    }


def evaluate_ranking(ranking: list[str], relevant: set[str]) -> dict[str, float]:
    values: dict[str, float] = {}
    first = next((rank for rank, clip in enumerate(ranking, start=1) if clip in relevant), None)
    values["mrr"] = 0.0 if first is None else 1.0 / first
    for k in TOP_KS:
        top = ranking[:k]
        gains = np.array([1.0 if clip in relevant else 0.0 for clip in top], dtype=float)
        discounts = 1.0 / np.log2(np.arange(2, len(top) + 2))
        dcg = float(np.sum(gains * discounts))
        ideal_n = min(k, len(relevant))
        idcg = float(np.sum(1.0 / np.log2(np.arange(2, ideal_n + 2)))) if ideal_n else 0.0
        values[f"ndcg_at_{k}"] = dcg / idcg if idcg else 0.0
        values[f"recall_at_{k}"] = len(set(top) & relevant) / len(relevant) if relevant else 0.0
        values[f"hit_at_{k}"] = float(bool(set(top) & relevant))
    return values


def quantiles(values: np.ndarray) -> tuple[float, float]:
    low, high = np.quantile(values, (0.025, 0.975))
    return float(low), float(high)


def bootstrap_delta(
    delta: np.ndarray,
    query_samples: np.ndarray,
    cluster_samples: np.ndarray,
    cluster_inverse: np.ndarray,
    cluster_sizes: np.ndarray,
) -> dict[str, float]:
    query_boot = delta[query_samples].mean(axis=1)
    cluster_means = np.array(
        [delta[cluster_inverse == cluster].mean() for cluster in range(len(cluster_sizes))]
    )
    numerator = (cluster_means[cluster_samples] * cluster_sizes[cluster_samples]).sum(axis=1)
    denominator = cluster_sizes[cluster_samples].sum(axis=1)
    cluster_boot = numerator / denominator
    query_low, query_high = quantiles(query_boot)
    cluster_low, cluster_high = quantiles(cluster_boot)
    return {
        "mean_delta": float(delta.mean()),
        "query_ci_lo": query_low,
        "query_ci_hi": query_high,
        "cluster_ci_lo": cluster_low,
        "cluster_ci_hi": cluster_high,
        "p_query": min(
            1.0,
            2.0 * min(float(np.mean(query_boot <= 0)), float(np.mean(query_boot >= 0))),
        ),
        "p_cluster": min(
            1.0,
            2.0 * min(float(np.mean(cluster_boot <= 0)), float(np.mean(cluster_boot >= 0))),
        ),
        "wins": int(np.sum(delta > 1e-12)),
        "ties": int(np.sum(np.abs(delta) <= 1e-12)),
        "losses": int(np.sum(delta < -1e-12)),
    }


def bh_adjust(values: pd.Series) -> np.ndarray:
    source = values.to_numpy(float)
    order = np.argsort(source)
    ranked = source[order]
    adjusted = np.minimum.accumulate(
        (ranked * len(source) / np.arange(1, len(source) + 1))[::-1]
    )[::-1]
    result = np.empty_like(adjusted)
    result[order] = np.clip(adjusted, 0.0, 1.0)
    return result


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty; pass --overwrite")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    canonical = args.canonical_root
    base = args.base_embedding_root
    clips = pd.read_parquet(canonical / "clips.parquet").reset_index(drop=True)
    queries = load_jsonl(canonical / "queries.jsonl")
    query_ids = [str(row["query_id"]) for row in queries]
    query_index = pd.read_parquet(base / "query_index.parquet")
    document_index = pd.read_parquet(base / "document_index.parquet")
    representative_index = pd.read_parquet(base / "representative_frame_index.parquet")
    matched_index = pd.read_parquet(args.matched_root / "joint_index.parquet")
    shuffled_index = pd.read_parquet(args.shuffled_root / "joint_index.parquet")
    clip_ids = clips["clip_id"].astype(str).to_numpy()

    if query_index["query_id"].astype(str).tolist() != query_ids:
        raise RuntimeError("Query order differs from the frozen workload")
    for label, values in (
        ("caption", document_index["clip_id"]),
        ("representative_frame", representative_index["clip_id"]),
        ("joint_matched", matched_index["clip_id"]),
        ("joint_shuffled", shuffled_index["clip_id"]),
    ):
        if values.astype(str).tolist() != clip_ids.tolist():
            raise RuntimeError(f"{label} clip order differs from the frozen workload")
    if not matched_index["caption_match"].astype(bool).all():
        raise RuntimeError("Matched control has incorrect caption pairs")
    if shuffled_index["caption_match"].astype(bool).any():
        raise RuntimeError("Shuffled control has matched caption pairs")

    query_vectors = normalize(np.load(base / "query_embeddings.npy"))
    lanes = {
        "caption": normalize(np.load(base / "document_embeddings.npy")),
        "representative_frame": normalize(np.load(base / "representative_frame_embeddings.npy")),
        "joint_matched": normalize(np.load(args.matched_root / "joint_embeddings.npy")),
        "joint_shuffled": normalize(np.load(args.shuffled_root / "joint_embeddings.npy")),
    }
    expected = (len(clips), query_vectors.shape[1])
    for name, vectors in lanes.items():
        if tuple(vectors.shape) != expected:
            raise RuntimeError(f"{name} vector shape {vectors.shape} != {expected}")

    strict = positives(canonical / "qrels.tsv")
    semantic = positives(canonical / "qrels_semantic.tsv")
    metric_rows: list[dict[str, Any]] = []
    ranking_rows: list[dict[str, Any]] = []
    latency_rows: list[dict[str, Any]] = []
    indexes: dict[str, faiss.IndexFlatIP] = {}
    rankings: dict[str, dict[str, list[str]]] = {}
    rng = np.random.default_rng(args.seed)
    faiss.omp_set_num_threads(1)

    for name, vectors in lanes.items():
        index = faiss.IndexFlatIP(vectors.shape[1])
        index.add(vectors)
        indexes[name] = index
        rankings[name] = {}
        scores, ids = index.search(query_vectors, MAX_RANK)
        for query_position, query_id in enumerate(query_ids):
            ranking = [str(clip_ids[item]) for item in ids[query_position] if item >= 0]
            rankings[name][query_id] = ranking
            for scoring, qrels in (("strict", strict), ("semantic", semantic)):
                metric_rows.append(
                    {
                        "representation": name,
                        "query_id": query_id,
                        "scoring": scoring,
                        **evaluate_ranking(ranking, qrels.get(query_id, set())),
                    }
                )
            for rank, (clip_id, score) in enumerate(
                zip(ranking, scores[query_position], strict=True), start=1
            ):
                ranking_rows.append(
                    {
                        "representation": name,
                        "query_id": query_id,
                        "rank": rank,
                        "clip_id": clip_id,
                        "score": float(score),
                    }
                )

        for _ in range(args.latency_warmup):
            for query_position in rng.permutation(len(query_ids)):
                index.search(query_vectors[int(query_position)].reshape(1, -1), MAX_RANK)
        for repeat in range(args.latency_repeats):
            for order, query_position in enumerate(rng.permutation(len(query_ids))):
                started = time.perf_counter_ns()
                index.search(query_vectors[int(query_position)].reshape(1, -1), MAX_RANK)
                latency_rows.append(
                    {
                        "representation": name,
                        "repeat": repeat,
                        "order": order,
                        "query_id": query_ids[int(query_position)],
                        "latency_ms": (time.perf_counter_ns() - started) / 1e6,
                    }
                )

    metrics = pd.DataFrame(metric_rows)
    latency = pd.DataFrame(latency_rows)
    quality = (
        metrics.groupby(["representation", "scoring"], sort=False)
        .agg(
            queries=("query_id", "size"),
            ndcg_at_10=("ndcg_at_10", "mean"),
            mrr=("mrr", "mean"),
            recall_at_10=("recall_at_10", "mean"),
            hit_at_10=("hit_at_10", "mean"),
        )
        .reset_index()
    )
    latency_summary = (
        latency.groupby("representation", sort=False)["latency_ms"]
        .agg(
            latency_mean_ms="mean",
            latency_p50_ms="median",
            latency_p95_ms=lambda values: values.quantile(0.95),
        )
        .reset_index()
    )
    quality = quality.merge(latency_summary, on="representation")
    quality["vector_payload_mb"] = quality["representation"].map(
        {name: vectors.nbytes / 1e6 for name, vectors in lanes.items()}
    )

    query_frame = pd.DataFrame(queries)
    query_frame["cluster"] = (
        query_frame["relevance_def"].astype(str) + "|" + query_frame["difficulty"].astype(str)
    )
    clusters, cluster_inverse = np.unique(query_frame["cluster"].to_numpy(), return_inverse=True)
    cluster_sizes = np.bincount(cluster_inverse)
    bootstrap_rng = np.random.default_rng(args.seed)
    query_samples = bootstrap_rng.integers(
        0, len(query_ids), size=(args.bootstrap_reps, len(query_ids)), dtype=np.int16
    )
    cluster_samples = bootstrap_rng.integers(
        0, len(clusters), size=(args.bootstrap_reps, len(clusters)), dtype=np.int16
    )
    metric_values = {
        (representation, scoring): group.set_index("query_id").loc[query_ids]["ndcg_at_10"].to_numpy(float)
        for (representation, scoring), group in metrics.groupby(
            ["representation", "scoring"], sort=False
        )
    }
    pairs = (
        ("joint_matched", "caption"),
        ("joint_matched", "representative_frame"),
        ("joint_matched", "joint_shuffled"),
        ("joint_shuffled", "caption"),
    )
    comparison_rows = []
    for candidate, baseline_name in pairs:
        for scoring in ("strict", "semantic"):
            delta = metric_values[(candidate, scoring)] - metric_values[(baseline_name, scoring)]
            comparison_rows.append(
                {
                    "candidate": candidate,
                    "baseline": baseline_name,
                    "scoring": scoring,
                    "queries": len(query_ids),
                    "clusters": len(clusters),
                    **bootstrap_delta(
                        delta,
                        query_samples,
                        cluster_samples,
                        cluster_inverse,
                        cluster_sizes,
                    ),
                }
            )
    comparisons = pd.DataFrame(comparison_rows)
    comparisons["q_query_bh"] = np.nan
    comparisons["q_cluster_bh"] = np.nan
    for scoring, row_index in comparisons.groupby("scoring").groups.items():
        _ = scoring
        comparisons.loc[row_index, "q_query_bh"] = bh_adjust(
            comparisons.loc[row_index, "p_query"]
        )
        comparisons.loc[row_index, "q_cluster_bh"] = bh_adjust(
            comparisons.loc[row_index, "p_cluster"]
        )

    diagnostics = {
        "joint_matched_cosine_to_caption_mean": float(
            np.sum(lanes["joint_matched"] * lanes["caption"], axis=1).mean()
        ),
        "joint_matched_cosine_to_frame_mean": float(
            np.sum(lanes["joint_matched"] * lanes["representative_frame"], axis=1).mean()
        ),
        "matched_to_shuffled_joint_cosine_mean": float(
            np.sum(lanes["joint_matched"] * lanes["joint_shuffled"], axis=1).mean()
        ),
        "matched_joint_unique_vectors": int(np.unique(lanes["joint_matched"], axis=0).shape[0]),
        "shuffled_joint_unique_vectors": int(np.unique(lanes["joint_shuffled"], axis=0).shape[0]),
    }

    metrics.to_parquet(args.output_dir / "per_query_metrics.parquet", index=False)
    pd.DataFrame(ranking_rows).to_parquet(args.output_dir / "rankings.parquet", index=False)
    latency.to_parquet(args.output_dir / "latency_trials.parquet", index=False)
    quality.to_csv(args.output_dir / "quality_summary.csv", index=False)
    comparisons.to_csv(args.output_dir / "paired_bootstrap_comparisons.csv", index=False)
    query_frame[["query_id", "relevance_def", "difficulty", "cluster"]].to_csv(
        args.output_dir / "query_clusters.csv", index=False
    )
    (args.output_dir / "diagnostics.json").write_text(
        json.dumps(diagnostics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "experiment": "equal-budget one-vector image-caption early-fusion controls",
        "queries": len(query_ids),
        "clips": len(clips),
        "dimension": query_vectors.shape[1],
        "representations": list(lanes),
        "search": "FAISS IndexFlatIP exact, text-only query vectors, top-100",
        "scoring": ["strict", "semantic"],
        "bootstrap_reps": args.bootstrap_reps,
        "cluster_definition": "relevance_def x metadata difficulty/facet",
        "multiple_comparison": "BH within scoring across four declared comparisons",
        "latency": {
            "threads": 1,
            "warmup": args.latency_warmup,
            "repeats": args.latency_repeats,
            "scope": "vector search only; excludes query embedding and evidence fetch",
        },
        "hashes": {
            "queries": sha256_file(canonical / "queries.jsonl"),
            "qrels": sha256_file(canonical / "qrels.tsv"),
            "qrels_semantic": sha256_file(canonical / "qrels_semantic.tsv"),
            "matched_manifest": sha256_file(args.matched_root / "embedding_manifest.json"),
            "shuffled_manifest": sha256_file(args.shuffled_root / "embedding_manifest.json"),
        },
        "audits": {
            "matched_pairs": int(matched_index["caption_match"].astype(bool).sum()),
            "shuffled_fixed_points": int(shuffled_index["caption_match"].astype(bool).sum()),
            "all_vector_shapes_equal": all(tuple(value.shape) == expected for value in lanes.values()),
            "all_vectors_finite": all(np.isfinite(value).all() for value in lanes.values()),
        },
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"[done] representations={len(lanes)} metrics={len(metrics)} "
        f"comparisons={len(comparisons)} -> {args.output_dir}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
