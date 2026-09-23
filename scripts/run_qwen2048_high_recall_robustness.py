#!/usr/bin/env python3
"""Five-seed high-recall HNSW/IVF-Flat search-strength validation."""
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
    PROJECT_ROOT
    / "Datasets"
    / "processed"
    / "aihub_522_intersection"
    / "20260710"
    / "embeddings_qwen3vl2b_unified_qwen35captions"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "2026_KIISE"
    / "paper_assets"
    / "20260717_ablation_agent_crosscheck"
    / "qwen2048_high_recall_5seed"
)
K = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=EMBEDDING_ROOT / "frame_embeddings.npy")
    parser.add_argument("--queries", type=Path, default=EMBEDDING_ROOT / "query_embeddings.npy")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--seeds", default="20260717,20260718,20260719,20260720,20260721")
    parser.add_argument("--latency-repeats", type=int, default=10)
    parser.add_argument("--latency-warmup", type=int, default=3)
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def normalize(value: np.ndarray) -> np.ndarray:
    value = np.ascontiguousarray(value.astype("float32", copy=True))
    faiss.normalize_L2(value)
    return value


def recall_at_10(truth: np.ndarray, estimate: np.ndarray) -> float:
    return float(np.mean([len(set(left[:K]) & set(right[:K])) / K for left, right in zip(truth, estimate)]))


def index_size_mb(index) -> float:
    with tempfile.NamedTemporaryFile(suffix=".faiss", delete=False) as handle:
        path = handle.name
    try:
        faiss.write_index(index, path)
        return os.path.getsize(path) / 1e6
    finally:
        Path(path).unlink(missing_ok=True)


def latency(index, queries: np.ndarray, repeats: int, warmup: int) -> dict[str, float]:
    faiss.omp_set_num_threads(1)
    values: list[float] = []
    for query in queries:
        item = query.reshape(1, -1)
        for _ in range(warmup):
            index.search(item, K)
        for _ in range(repeats):
            start = time.perf_counter_ns()
            index.search(item, K)
            values.append((time.perf_counter_ns() - start) / 1e6)
    array = np.asarray(values)
    return {
        "latency_mean_ms": float(array.mean()),
        "latency_p50_ms": float(np.quantile(array, 0.50)),
        "latency_p95_ms": float(np.quantile(array, 0.95)),
        "latency_p99_ms": float(np.quantile(array, 0.99)),
    }


def evaluate_settings(
    rows: list[dict],
    index,
    truth: np.ndarray,
    queries: np.ndarray,
    seed: int,
    structure: str,
    build_s: float,
    size_mb: float,
    settings: list[int],
    repeats: int,
    warmup: int,
) -> None:
    for value in settings:
        if structure == "hnsw":
            index.hnsw.efSearch = value
            setting = {"M": 32, "efSearch": value, "nlist": np.nan, "nprobe": np.nan}
        else:
            index.nprobe = value
            setting = {"M": np.nan, "efSearch": np.nan, "nlist": 1024, "nprobe": value}
        faiss.omp_set_num_threads(0)
        _, estimate = index.search(queries, K)
        result = {
            "seed": seed,
            "structure": structure,
            **setting,
            "recall_at_10": recall_at_10(truth, estimate),
            "build_s": build_s,
            "index_mb": size_mb,
            **latency(index, queries, repeats, warmup),
        }
        rows.append(result)
        print(
            f"  {structure} setting={value} recall={result['recall_at_10']:.6f} "
            f"p95={result['latency_p95_ms']:.3f}ms",
            flush=True,
        )


def write_partial(rows: list[dict], output_dir: Path) -> None:
    pd.DataFrame(rows).to_csv(output_dir / "results_partial.csv", index=False)


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    seeds = [int(value) for value in args.seeds.split(",") if value.strip()]
    db = normalize(np.load(args.corpus))
    queries = normalize(np.load(args.queries))
    print(f"[data] N={len(db)} d={db.shape[1]} queries={len(queries)}", flush=True)

    faiss.omp_set_num_threads(0)
    exact = faiss.IndexFlatIP(db.shape[1])
    exact.add(db)
    _, truth = exact.search(queries, K)
    del exact

    partial_path = args.output_dir / "results_partial.csv"
    if args.resume and partial_path.exists():
        rows = pd.read_csv(partial_path).to_dict("records")
    else:
        rows: list[dict] = []
    completed = {(int(row["seed"]), str(row["structure"])) for row in rows}

    dim = db.shape[1]
    for seed in seeds:
        if (seed, "hnsw") not in completed:
            print(f"[seed={seed}] build HNSW M32 efConstruction=200", flush=True)
            faiss.omp_set_num_threads(0)
            start = time.perf_counter()
            index = faiss.IndexHNSWFlat(dim, 32, faiss.METRIC_INNER_PRODUCT)
            index.hnsw.efConstruction = 200
            index.hnsw.rng = faiss.RandomGenerator(seed)
            index.add(db)
            build_s = time.perf_counter() - start
            size_mb = index_size_mb(index)
            evaluate_settings(
                rows, index, truth, queries, seed, "hnsw", build_s, size_mb,
                [256, 512, 1024], args.latency_repeats, args.latency_warmup,
            )
            del index
            write_partial(rows, args.output_dir)

        if (seed, "ivfflat") not in completed:
            print(f"[seed={seed}] build IVF-Flat nlist=1024", flush=True)
            faiss.omp_set_num_threads(0)
            start = time.perf_counter()
            index = faiss.IndexIVFFlat(faiss.IndexFlatIP(dim), dim, 1024, faiss.METRIC_INNER_PRODUCT)
            index.cp.seed = seed
            index.train(db)
            index.add(db)
            build_s = time.perf_counter() - start
            size_mb = index_size_mb(index)
            evaluate_settings(
                rows, index, truth, queries, seed, "ivfflat", build_s, size_mb,
                [128, 256, 512], args.latency_repeats, args.latency_warmup,
            )
            del index
            write_partial(rows, args.output_dir)

    frame = pd.DataFrame(rows).sort_values(["structure", "seed", "efSearch", "nprobe"], na_position="last")
    frame.to_csv(args.output_dir / "results.csv", index=False)
    summary = (
        frame.groupby(["structure", "M", "efSearch", "nlist", "nprobe"], dropna=False, sort=False)
        .agg(
            seeds=("seed", "nunique"),
            recall_mean=("recall_at_10", "mean"),
            recall_std=("recall_at_10", "std"),
            recall_min=("recall_at_10", "min"),
            recall_max=("recall_at_10", "max"),
            latency_p95_median_ms=("latency_p95_ms", "median"),
            latency_p95_max_ms=("latency_p95_ms", "max"),
            build_s_mean=("build_s", "mean"),
            index_mb_mean=("index_mb", "mean"),
        )
        .reset_index()
    )
    summary["all_seeds_recall_ge_099"] = summary["recall_min"] >= 0.99
    summary.to_csv(args.output_dir / "summary.csv", index=False)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "corpus": str(args.corpus.resolve()),
        "queries": str(args.queries.resolve()),
        "n_vectors": len(db),
        "dimension": dim,
        "query_count": len(queries),
        "seeds": seeds,
        "settings": {"hnsw_M32_efSearch": [256, 512, 1024], "ivfflat_nlist1024_nprobe": [128, 256, 512]},
        "metric": "ANN recall@10 versus exact Flat top-10",
        "latency": {"threads": 1, "repeats": args.latency_repeats, "warmup": args.latency_warmup},
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(summary.to_string(index=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
