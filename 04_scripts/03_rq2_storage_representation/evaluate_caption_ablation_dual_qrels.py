#!/usr/bin/env python3
"""Re-score saved rankings against strict and semantic qrels."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "2026_KIISE" / "03_src"))
from vlmdb_workload.metrics import evaluate_ranking  # noqa: E402


def bootstrap_ci(values: np.ndarray, rng: np.random.Generator, draws: int) -> tuple[float, float]:
    if len(values) == 0:
        return float("nan"), float("nan")
    indices = rng.integers(0, len(values), size=(draws, len(values)))
    means = values[indices].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--results-dir", type=Path, required=True)
    parser.add_argument("--top-ks", default="1,5,10,20")
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--seed", type=int, default=20260715)
    args = parser.parse_args()
    top_ks = [int(value) for value in args.top_ks.split(",")]

    rankings = pd.read_parquet(args.results_dir / "retrieval_results.parquet")
    queries = pd.DataFrame(
        [json.loads(line) for line in (args.canonical_root / "queries.jsonl").read_text().splitlines()]
    )
    query_meta = queries.set_index("query_id").to_dict("index")
    qrels_paths = {
        "strict": args.canonical_root / "qrels.tsv",
        "semantic": args.canonical_root / "qrels_semantic.tsv",
    }
    relsets = {}
    for scoring, path in qrels_paths.items():
        qrels = pd.read_csv(path, sep="\t")
        relsets[scoring] = qrels.groupby("query_id")["target_id"].apply(set).to_dict()

    rows = []
    for (strategy, query_id), group in rankings.groupby(["strategy", "query_id"], sort=False):
        ranking = group.sort_values("rank")["clip_id"].tolist()
        for scoring in ("strict", "semantic"):
            metrics = evaluate_ranking(ranking, relsets[scoring].get(query_id, set()), top_ks)
            meta = query_meta[query_id]
            rows.append(
                {
                    "strategy": strategy,
                    "query_id": query_id,
                    "scoring": scoring,
                    "difficulty": meta.get("difficulty"),
                    "coupling": meta.get("coupling"),
                    "relevance_def": meta.get("relevance_def"),
                    **metrics,
                }
            )
    per_query = pd.DataFrame(rows)
    per_query.to_parquet(args.results_dir / "metrics_by_query_dual.parquet", index=False)
    metric_columns = [
        column
        for column in per_query.columns
        if column.startswith(("recall_at_", "hit_at_")) or column in {"mrr", "ndcg_at_10"}
    ]
    summary = per_query.groupby(["scoring", "strategy"], sort=False)[metric_columns].mean().reset_index()
    summary.to_csv(args.results_dir / "metrics_dual_summary.csv", index=False)

    rng = np.random.default_rng(args.seed)
    deltas = []
    for scoring in ("strict", "semantic"):
        subset = per_query[per_query.scoring == scoring]
        pivot = subset.pivot(index="query_id", columns="strategy", values="ndcg_at_10")
        qmeta = queries.set_index("query_id")
        for coupling in ["all", *sorted(queries["coupling"].dropna().unique())]:
            use = pivot if coupling == "all" else pivot.loc[
                pivot.index.intersection(qmeta.index[qmeta["coupling"] == coupling])
            ]
            values = (use["B4_prefilter_vector"] - use["B2_vector_only"]).dropna().to_numpy()
            lo, hi = bootstrap_ci(values, rng, args.bootstrap)
            deltas.append(
                {
                    "scoring": scoring,
                    "coupling": coupling,
                    "queries": len(values),
                    "delta_B4_B2": float(values.mean()),
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "negative": int((values < 0).sum()),
                    "zero": int((values == 0).sum()),
                    "positive": int((values > 0).sum()),
                }
            )
    pd.DataFrame(deltas).to_csv(args.results_dir / "b4_vs_b2_dual.csv", index=False)
    print(summary.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
