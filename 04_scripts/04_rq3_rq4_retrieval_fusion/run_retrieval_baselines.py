#!/usr/bin/env python3
"""Run B0-B5 retrieval baselines for a canonical workload."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "03_src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.retrieval import RetrievalExperimentRunner  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=PROJECT_ROOT / "Datasets" / "processed" / "vru_accident" / "20260706" / "canonical",
    )
    parser.add_argument(
        "--embedding-root",
        type=Path,
        default=PROJECT_ROOT / "Datasets" / "processed" / "vru_accident" / "20260706" / "embeddings" / "bge-m3",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT
        / "Datasets"
        / "processed"
        / "vru_accident"
        / "20260706"
        / "results"
        / "vru_bgem3_faiss_b0_b5",
    )
    parser.add_argument("--top-ks", default="1,5,10,20")
    parser.add_argument("--max-rank", type=int, default=100)
    parser.add_argument("--postfilter-doc-k", type=int, default=200)
    parser.add_argument("--max-queries", type=int, default=None)
    parser.add_argument("--max-queries-per-difficulty", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    top_ks = [int(value) for value in args.top_ks.split(",") if value.strip()]
    runner = RetrievalExperimentRunner(
        canonical_root=args.canonical_root,
        embedding_root=args.embedding_root,
        output_dir=args.output_dir,
        top_ks=top_ks,
        max_rank=args.max_rank,
        postfilter_doc_k=args.postfilter_doc_k,
        max_queries=args.max_queries,
        max_queries_per_difficulty=args.max_queries_per_difficulty,
    )
    result = runner.run(overwrite=args.overwrite)
    print(f"output_dir={result.output_dir}")
    print(f"queries={result.queries}")
    print(f"strategies={','.join(result.strategies)}")
    print(f"result_rows={result.result_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
