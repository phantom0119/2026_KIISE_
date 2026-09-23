#!/usr/bin/env python3
"""Build the S4 top-1 exact-vs-strong retrieval audit population.

The E1A video sample and middle-frame rule are reconstructed with seed
20260711. Both source and retrieval corpus are restricted to TL_3 annotated
frames, so source and evidence use one count-label definition.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VER = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
DEFAULT_OUT = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets"
    / "20260723_controlled_supplement" / "s4_retrieval_population"
)
LOCK_PATH = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260711_e1a" / "e1a_locked_configs.json"


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype="float32")
    return values / np.maximum(np.linalg.norm(values, axis=1, keepdims=True), 1e-12)


def to_class(values: np.ndarray) -> np.ndarray:
    return np.where(values < 0.5, "0", np.where(values < 1.5, "1", "2+"))


def self_excluded_top1(
    index,
    queries: np.ndarray,
    self_local_ids: np.ndarray,
    corpus_global_ids: np.ndarray,
) -> np.ndarray:
    _, ranks = index.search(queries, 8)
    output = np.full(len(queries), -1, dtype=np.int64)
    for query_index, (row, self_id) in enumerate(zip(ranks, self_local_ids, strict=True)):
        eligible = row[(row >= 0) & (row != self_id)]
        if len(eligible):
            output[query_index] = corpus_global_ids[eligible[0]]
    if (output < 0).any():
        raise RuntimeError(f"top-1 retrieval failed for {(output < 0).sum()} queries")
    return output


def reconstruct_e1a_source_rows(frame_index: pd.DataFrame) -> tuple[list[int], dict]:
    joined = pd.read_parquet(VER / "visual_sensor_join.parquet")
    video_annotations = pd.read_parquet(VER / "annotation_video_facets.parquet")
    valid_join = joined[joined.join_ok_120s][
        ["visual_video_id", "split", "sensor_clip_id"]
    ]
    frame_joined = frame_index.merge(
        valid_join, on=["visual_video_id", "split"], how="left"
    )
    moment_groups = (
        frame_joined.dropna(subset=["sensor_clip_id"])
        .groupby("sensor_clip_id")["row"]
        .apply(list)
    )
    row_to_group: dict[int, str] = {}
    for group_id, rows in moment_groups.items():
        for row in rows:
            row_to_group[int(row)] = group_id

    pool = valid_join.merge(
        video_annotations[
            ["visual_video_id", "split", "max_bus", "any_stopped", "max_bike"]
        ],
        on=["visual_video_id", "split"],
    )
    videos = pool.drop_duplicates(["visual_video_id", "split"])
    videos = videos.sample(min(3000, len(videos)), random_state=20260711)
    frames_by_video = frame_joined.groupby(["visual_video_id", "split"])["row"].apply(sorted)
    output: list[int] = []
    insufficient_video_frames = 0
    missing_group = 0
    empty_evidence = 0
    for video in videos.itertuples(index=False):
        rows = frames_by_video.get((video.visual_video_id, video.split))
        if rows is None or len(rows) < 2:
            insufficient_video_frames += 1
            continue
        query_row = int(rows[len(rows) // 2])
        group_id = row_to_group.get(query_row)
        if group_id is None:
            missing_group += 1
            continue
        evidence = set(moment_groups[group_id]) - {query_row}
        if not evidence:
            empty_evidence += 1
            continue
        output.append(query_row)
    return output, {
        "sampled_videos": int(len(videos)),
        "reconstructed_source_rows": int(len(output)),
        "insufficient_video_frames": insufficient_video_frames,
        "missing_moment_group": missing_group,
        "empty_moment_evidence": empty_evidence,
    }


def cluster_bootstrap_difference(
    exact: np.ndarray,
    strong: np.ndarray,
    clusters: np.ndarray,
    seed: int,
    draws: int,
) -> tuple[float, float]:
    unique = sorted(set(map(str, clusters)))
    indices = {cluster: np.flatnonzero(clusters.astype(str) == cluster) for cluster in unique}
    rng = np.random.default_rng(seed)
    values = np.empty(draws)
    for draw in range(draws):
        sampled = rng.choice(unique, len(unique), replace=True)
        picked = np.concatenate([indices[value] for value in sampled])
        values[draw] = float((exact[picked] - strong[picked]).mean())
    return float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260723)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty; pass --overwrite")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    embedding_path = VER / "visual_embeddings_clip" / "frame_embeddings.npy"
    annotation_path = VER / "annotation_frame_facets.parquet"
    frame_index_path = VER / "visual_embeddings_clip" / "frame_index.parquet"
    hashes = {
        "frame_embeddings.npy": sha256_file(embedding_path),
        "annotation_frame_facets.parquet": sha256_file(annotation_path),
        "frame_index.parquet": sha256_file(frame_index_path),
        "e1a_locked_configs.json": sha256_file(LOCK_PATH),
    }
    expected = {
        "frame_embeddings.npy": "6add5013ba9c4033a014da0bab51a434f4fa6e2ee33b364f1a6689331ccc5716",
        "annotation_frame_facets.parquet": "4c9bbefb6be3d989d359ffc510fe9b36403caab270b90e0c468bd888b7b0a663",
        "frame_index.parquet": "f8aba458c5b0712ea3439dc4905372354afe3da9b832023c5b0baad8920210a4",
        "e1a_locked_configs.json": "81d5fde76a6f986c8bd51226597e83cb7cba4abcd24e086b7127c3d6c656c4ff",
    }
    if hashes != expected:
        raise ValueError(f"frozen input hash mismatch: {hashes}")

    all_vectors = normalize(np.load(embedding_path))
    frame_index = pd.read_parquet(frame_index_path).reset_index(names="row")
    annotations = pd.read_parquet(annotation_path)
    annotations = annotations[annotations["ann_source"] == "TL_3_polyline"][
        ["split", "visual_video_id", "frame", "n_bus", "n_bike"]
    ]
    annotated = frame_index.merge(
        annotations,
        on=["split", "visual_video_id", "frame"],
        how="inner",
        validate="one_to_one",
    ).sort_values("row")
    annotated["bus_count"] = to_class(annotated["n_bus"].to_numpy(float))
    annotated["bike_count"] = to_class(annotated["n_bike"].to_numpy(float))
    corpus_global_ids = annotated["row"].to_numpy(np.int64)
    corpus_vectors = np.ascontiguousarray(all_vectors[corpus_global_ids])
    global_to_local = {global_id: local for local, global_id in enumerate(corpus_global_ids)}

    reconstructed, reconstruction = reconstruct_e1a_source_rows(frame_index)
    missing_annotation = [row for row in reconstructed if row not in global_to_local]
    source_global_ids = np.asarray(
        [row for row in reconstructed if row in global_to_local], dtype=np.int64
    )
    source_local_ids = np.asarray([global_to_local[row] for row in source_global_ids], dtype=np.int64)
    query_vectors = np.ascontiguousarray(all_vectors[source_global_ids])
    reconstruction["missing_source_annotation"] = int(len(missing_annotation))
    reconstruction["eligible_source_rows"] = int(len(source_global_ids))
    if not len(source_global_ids):
        raise RuntimeError("no eligible S4 source rows")

    import faiss

    faiss.omp_set_num_threads(0)
    dimension = corpus_vectors.shape[1]
    start = time.perf_counter()
    exact_index = faiss.IndexFlatIP(dimension)
    exact_index.add(corpus_vectors)
    exact_global = self_excluded_top1(
        exact_index, query_vectors, source_local_ids, corpus_global_ids
    )
    exact_seconds = time.perf_counter() - start

    lock = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
    if lock["strong"] != "ivfpq_nlist1024_m32_nprobe8":
        raise ValueError(f"unexpected frozen strong config: {lock['strong']}")
    start = time.perf_counter()
    quantizer = faiss.IndexFlatIP(dimension)
    strong_index = faiss.IndexIVFPQ(
        quantizer, dimension, 1024, 32, 8, faiss.METRIC_INNER_PRODUCT
    )
    if hasattr(strong_index, "cp"):
        strong_index.cp.seed = 20260711
    strong_index.train(corpus_vectors)
    strong_index.add(corpus_vectors)
    strong_index.nprobe = 8
    strong_global = self_excluded_top1(
        strong_index, query_vectors, source_local_ids, corpus_global_ids
    )
    strong_seconds = time.perf_counter() - start

    annotated_by_row = annotated.set_index("row")
    source_meta = annotated_by_row.loc[source_global_ids]
    exact_meta = annotated_by_row.loc[exact_global]
    strong_meta = annotated_by_row.loc[strong_global]
    rows: list[dict] = []
    summary_categories: dict[str, dict] = {}
    for category_index, category in enumerate(("bus_count", "bike_count")):
        source_class = source_meta[category].to_numpy(str)
        exact_class = exact_meta[category].to_numpy(str)
        strong_class = strong_meta[category].to_numpy(str)
        exact_hit = exact_class == source_class
        strong_hit = strong_class == source_class
        difference = float(exact_hit.mean() - strong_hit.mean())
        ci_lo, ci_hi = cluster_bootstrap_difference(
            exact_hit.astype(float),
            strong_hit.astype(float),
            source_meta["intersection_id"].astype(str).to_numpy(),
            args.seed + category_index,
            args.bootstrap,
        )
        discordant_good = int((exact_hit & ~strong_hit).sum())
        gate = {
            "exact_minus_strong_at_least_5pp": bool(difference >= 0.05),
            "exact_hit_strong_miss_at_least_200": bool(discordant_good >= 200),
        }
        gate["all_pass"] = all(gate.values())
        stratum = np.char.add(
            np.where(exact_hit, "exact_hit", "exact_miss"),
            np.where(strong_hit, "__strong_hit", "__strong_miss"),
        )
        summary_categories[category] = {
            "source_items": int(len(source_class)),
            "source_class_counts": pd.Series(source_class).value_counts().to_dict(),
            "exact_class_match": float(exact_hit.mean()),
            "strong_class_match": float(strong_hit.mean()),
            "exact_minus_strong": difference,
            "intersection_cluster_bootstrap_ci": [ci_lo, ci_hi],
            "strata": pd.Series(stratum).value_counts().to_dict(),
            "retrieval_gate": gate,
        }
        for index, source_row in enumerate(source_global_ids):
            rows.append(
                {
                    "category": category,
                    "source_row": int(source_row),
                    "source_relpath": source_meta.iloc[index]["relpath"],
                    "source_intersection_id": str(source_meta.iloc[index]["intersection_id"]),
                    "source_hour": int(source_meta.iloc[index]["hour"]),
                    "gold_class": source_class[index],
                    "exact_evidence_row": int(exact_global[index]),
                    "exact_evidence_relpath": exact_meta.iloc[index]["relpath"],
                    "exact_evidence_class": exact_class[index],
                    "strong_evidence_row": int(strong_global[index]),
                    "strong_evidence_relpath": strong_meta.iloc[index]["relpath"],
                    "strong_evidence_class": strong_class[index],
                    "exact_hit": bool(exact_hit[index]),
                    "strong_hit": bool(strong_hit[index]),
                    "stratum": stratum[index],
                }
            )

    population = pd.DataFrame(rows)
    exclusions = pd.DataFrame(
        {
            "source_row": missing_annotation,
            "status": "missing_source_annotation",
        }
    )
    summary = {
        "analysis": "S4 frozen top-1 retrieval manipulation check",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "retrieval_corpus_frames": int(len(annotated)),
        "reconstruction": reconstruction,
        "categories": summary_categories,
        "rule": "Only categories passing both retrieval gates may enter VLM answer propagation.",
    }
    manifest = {
        "script": Path(__file__).name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "input_sha256": hashes,
        "parameters": {
            "sample_seed": 20260711,
            "analysis_seed": args.seed,
            "bootstrap": args.bootstrap,
            "retrieval_k": 1,
            "self_exclusion": True,
            "corpus": "TL_3 annotated frames",
            "exact": "IndexFlatIP",
            "strong": lock["strong"],
            "strong_training_seed": 20260711,
            "strong_nprobe": 8,
        },
        "timing_seconds": {"exact_search": exact_seconds, "strong_build_and_search": strong_seconds},
    }
    population.to_parquet(args.output_dir / "retrieval_population.parquet", index=False)
    exclusions.to_csv(args.output_dir / "excluded_source_rows.csv", index=False)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
