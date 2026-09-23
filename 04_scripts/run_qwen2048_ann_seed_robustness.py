#!/usr/bin/env python3
"""Repeat selected 143,830-vector ANN structures across construction seeds."""
from __future__ import annotations

import argparse
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EMBEDDING_ROOT = (
    PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
    / "embeddings_qwen3vl2b_unified_qwen35captions"
)
DEFAULT_MAIN = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260717_joint_optimization_validation"
    / "qwen2048_scaled_index" / "index_benchmark.csv"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260717_joint_optimization_validation"
    / "qwen2048_seed_robustness"
)
N = 143830


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--corpus", type=Path, default=EMBEDDING_ROOT / "frame_embeddings.npy")
    p.add_argument("--queries", type=Path, default=EMBEDDING_ROOT / "query_embeddings.npy")
    p.add_argument("--main-result", type=Path, default=DEFAULT_MAIN)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--base-seed", type=int, default=20260717)
    p.add_argument("--additional-seeds", default="20260718,20260719")
    p.add_argument("--include-pq", action="store_true", help="Also repeat the already low-fidelity PQ control")
    return p.parse_args()


def normalize(value: np.ndarray) -> np.ndarray:
    value = np.ascontiguousarray(value.astype("float32", copy=True))
    faiss.normalize_L2(value)
    return value


def recall_at_10(truth: np.ndarray, estimate: np.ndarray) -> float:
    return float(np.mean([len(set(a[:10]) & set(b[:10])) / 10.0 for a, b in zip(truth, estimate)]))


def size_bytes(index) -> int:
    with tempfile.NamedTemporaryFile(suffix=".faiss", delete=False) as handle:
        path = handle.name
    try:
        faiss.write_index(index, path)
        return os.path.getsize(path)
    finally:
        Path(path).unlink(missing_ok=True)


def add_rows(rows: list[dict], index, truth, queries, seed, structure, build_s, settings):
    for setting in settings:
        if structure == "hnsw":
            index.hnsw.efSearch = setting["efSearch"]
        else:
            index.nprobe = setting["nprobe"]
        _, estimate = index.search(queries, 10)
        rows.append(
            {
                "seed": seed,
                "structure": structure,
                **setting,
                "recall_at_10": recall_at_10(truth, estimate),
                "build_s": build_s,
                "index_mb": size_bytes(index) / 1e6,
            }
        )


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    db = normalize(np.load(args.corpus))
    queries = normalize(np.load(args.queries))
    faiss.omp_set_num_threads(0)
    exact = faiss.IndexFlatIP(db.shape[1])
    exact.add(db)
    _, truth = exact.search(queries, 10)
    del exact

    rows: list[dict] = []
    main = pd.read_csv(args.main_result)
    main = main[main["N"].eq(N)]
    selected_parts = [
            main[(main.kind == "hnsw") & (main.M == 32) & (main.efSearch.isin([64, 256]))],
            main[(main.kind == "ivfflat") & (main.nlist == 1024) & (main.nprobe.isin([32, 128]))],
    ]
    if args.include_pq:
        selected_parts.append(
            main[(main.kind == "ivfpq") & (main.nlist == 1024) & (main.m == 64) & (main.nprobe.isin([8, 32]))]
        )
    selected = pd.concat(selected_parts, ignore_index=True)
    for row in selected.to_dict("records"):
        rows.append(
            {
                "seed": args.base_seed,
                "structure": str(row["kind"]),
                "M": row.get("M"),
                "efSearch": row.get("efSearch"),
                "nlist": row.get("nlist"),
                "m": row.get("m"),
                "nprobe": row.get("nprobe"),
                "recall_at_10": row["recall_at_10"],
                "build_s": row["build_s"],
                "index_mb": row["index_mb"],
            }
        )

    seeds = [int(value) for value in args.additional_seeds.split(",") if value.strip()]
    dim = db.shape[1]
    for seed in seeds:
        print(f"[seed={seed}] HNSW M=32", flush=True)
        start = time.perf_counter()
        hnsw = faiss.IndexHNSWFlat(dim, 32, faiss.METRIC_INNER_PRODUCT)
        hnsw.hnsw.efConstruction = 200
        hnsw.hnsw.rng = faiss.RandomGenerator(seed)
        hnsw.add(db)
        add_rows(
            rows, hnsw, truth, queries, seed, "hnsw", time.perf_counter() - start,
            [{"M": 32, "efSearch": 64}, {"M": 32, "efSearch": 256}],
        )
        del hnsw
        pd.DataFrame(rows).to_csv(args.output_dir / "seed_results_partial.csv", index=False)

        print(f"[seed={seed}] IVF-Flat nlist=1024", flush=True)
        start = time.perf_counter()
        ivf = faiss.IndexIVFFlat(faiss.IndexFlatIP(dim), dim, 1024, faiss.METRIC_INNER_PRODUCT)
        ivf.cp.seed = seed
        ivf.train(db)
        ivf.add(db)
        add_rows(
            rows, ivf, truth, queries, seed, "ivfflat", time.perf_counter() - start,
            [{"nlist": 1024, "nprobe": 32}, {"nlist": 1024, "nprobe": 128}],
        )
        del ivf
        pd.DataFrame(rows).to_csv(args.output_dir / "seed_results_partial.csv", index=False)

        if args.include_pq:
            print(f"[seed={seed}] IVF-PQ nlist=1024 m=64", flush=True)
            start = time.perf_counter()
            pq = faiss.IndexIVFPQ(faiss.IndexFlatIP(dim), dim, 1024, 64, 8, faiss.METRIC_INNER_PRODUCT)
            pq.cp.seed = seed
            pq.pq.cp.seed = seed
            pq.train(db)
            pq.add(db)
            add_rows(
                rows, pq, truth, queries, seed, "ivfpq", time.perf_counter() - start,
                [{"nlist": 1024, "m": 64, "nprobe": 8}, {"nlist": 1024, "m": 64, "nprobe": 32}],
            )
            del pq
            pd.DataFrame(rows).to_csv(args.output_dir / "seed_results_partial.csv", index=False)

    frame = pd.DataFrame(rows)
    frame.to_csv(args.output_dir / "seed_results.csv", index=False)
    group_cols = ["structure", "M", "efSearch", "nlist", "m", "nprobe"]
    summary = (
        frame.groupby(group_cols, dropna=False, sort=False)
        .agg(
            seeds=("seed", "nunique"),
            recall_mean=("recall_at_10", "mean"),
            recall_std=("recall_at_10", "std"),
            recall_min=("recall_at_10", "min"),
            recall_max=("recall_at_10", "max"),
            build_s_mean=("build_s", "mean"),
            index_mb_mean=("index_mb", "mean"),
        )
        .reset_index()
    )
    summary.to_csv(args.output_dir / "seed_summary.csv", index=False)
    (args.output_dir / "manifest.json").write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "corpus": str(args.corpus.resolve()),
                "queries": str(args.queries.resolve()),
                "n_vectors": len(db),
                "dimension": dim,
                "query_count": len(queries),
                "seeds": [args.base_seed, *seeds],
                "structures": ["hnsw", "ivfflat"] + (["ivfpq"] if args.include_pq else []),
                "metric": "ANN recall@10 versus exact Flat top-10",
                "note": "Base-seed values are imported from the fixed-seed full benchmark; additional seeds are rebuilt here. PQ is excluded by default because its fixed-seed recall is too low for the high-fidelity deployment candidate set.",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
