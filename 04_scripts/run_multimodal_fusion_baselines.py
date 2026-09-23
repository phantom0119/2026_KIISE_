#!/usr/bin/env python3
"""Fuse text-evidence and visual-frame retrieval results for multimodal baselines."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "03_src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.io import load_canonical  # noqa: E402
from vlmdb_workload.metrics import evaluate_ranking  # noqa: E402


def load_strategy_rows(path: Path, strategy: str) -> dict[str, list[dict[str, Any]]]:
    df = pd.read_parquet(path)
    subset = df[df["strategy"].eq(strategy)].sort_values(["query_id", "rank"], kind="mergesort")
    if subset.empty:
        available = sorted(df["strategy"].dropna().unique().tolist())
        raise ValueError(f"Strategy {strategy!r} not found in {path}. Available: {available}")
    return {
        query_id: group.to_dict("records")
        for query_id, group in subset.groupby("query_id", sort=False)
    }


def load_latency(path: Path, strategy: str) -> dict[str, float]:
    df = pd.read_parquet(path)
    subset = df[df["strategy"].eq(strategy)]
    if subset.empty:
        return {}
    return dict(zip(subset["query_id"], subset["latency_ms"], strict=False))


def rrf_fuse(
    text_rows: list[dict[str, Any]],
    visual_rows: list[dict[str, Any]],
    *,
    rrf_k: int,
    text_weight: float,
    visual_weight: float,
    max_rank: int,
) -> list[dict[str, Any]]:
    items: dict[str, dict[str, Any]] = {}

    for row in text_rows:
        clip_id = str(row["clip_id"])
        rank = int(row["rank"])
        item = items.setdefault(
            clip_id,
            {
                "clip_id": clip_id,
                "score": 0.0,
                "text_rank": None,
                "text_score": None,
                "visual_rank": None,
                "visual_score": None,
                "visual_frame_id": None,
            },
        )
        item["score"] += text_weight / (rrf_k + rank)
        if item["text_rank"] is None or rank < item["text_rank"]:
            item["text_rank"] = rank
            item["text_score"] = float(row["score"])

    for row in visual_rows:
        clip_id = str(row["clip_id"])
        rank = int(row["rank"])
        item = items.setdefault(
            clip_id,
            {
                "clip_id": clip_id,
                "score": 0.0,
                "text_rank": None,
                "text_score": None,
                "visual_rank": None,
                "visual_score": None,
                "visual_frame_id": None,
            },
        )
        item["score"] += visual_weight / (rrf_k + rank)
        if item["visual_rank"] is None or rank < item["visual_rank"]:
            item["visual_rank"] = rank
            item["visual_score"] = float(row["score"])
            item["visual_frame_id"] = row.get("frame_id")

    ranked = sorted(
        items.values(),
        key=lambda item: (
            -float(item["score"]),
            item["text_rank"] if item["text_rank"] is not None else 10**9,
            item["visual_rank"] if item["visual_rank"] is not None else 10**9,
            item["clip_id"],
        ),
    )
    return ranked[:max_rank]


def summarize_metrics(metrics_by_query: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        col
        for col in metrics_by_query.columns
        if col.startswith("recall_at_") or col.startswith("hit_at_") or col in {"mrr", "ndcg_at_10"}
    ]
    rows = []
    for (strategy, difficulty), group in metrics_by_query.groupby(["strategy", "difficulty"], sort=False):
        row = {"strategy": strategy, "difficulty": difficulty, "queries": len(group)}
        row.update({col: group[col].mean() for col in metric_cols})
        rows.append(row)
    for strategy, group in metrics_by_query.groupby("strategy", sort=False):
        row = {"strategy": strategy, "difficulty": "all", "queries": len(group)}
        row.update({col: group[col].mean() for col in metric_cols})
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_latency(metrics_by_query: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for strategy, group in metrics_by_query.groupby("strategy", sort=False):
        rows.append(
            {
                "strategy": strategy,
                "queries": len(group),
                "latency_mean_ms": group["latency_ms"].mean(),
                "latency_p50_ms": group["latency_ms"].quantile(0.50),
                "latency_p95_ms": group["latency_ms"].quantile(0.95),
            }
        )
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--text-result-root", type=Path, required=True)
    parser.add_argument("--visual-result-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--top-ks", default="1,5,10,20")
    parser.add_argument("--max-rank", type=int, default=100)
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument("--text-weight", type=float, default=1.0)
    parser.add_argument("--visual-weight", type=float, default=1.0)
    parser.add_argument("--text-open-strategy", default="B2_vector_only")
    parser.add_argument("--visual-open-strategy", default="M2_visual_vector_only")
    parser.add_argument("--text-filtered-strategy", default="B5_hybrid")
    parser.add_argument("--visual-filtered-strategy", default="M4_metadata_prefilter_visual")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    _clips, _documents, _metadata, queries, qrels = load_canonical(args.canonical_root)
    top_ks = [int(value) for value in args.top_ks.split(",") if value.strip()]
    positives_by_query = {
        query_id: set(group["target_id"])
        for query_id, group in qrels.groupby("query_id", sort=False)
    }

    text_result_path = args.text_result_root / "retrieval_results.parquet"
    visual_result_path = args.visual_result_root / "visual_retrieval_results.parquet"
    text_metrics_path = args.text_result_root / "metrics_by_query.parquet"
    visual_metrics_path = args.visual_result_root / "metrics_by_query.parquet"

    strategy_specs = [
        {
            "strategy": "M5_text_visual_rrf",
            "text_strategy": args.text_open_strategy,
            "visual_strategy": args.visual_open_strategy,
            "description": "text dense retrieval plus visual text-to-frame retrieval without metadata filtering",
        },
        {
            "strategy": "M6_text_visual_metadata_rrf",
            "text_strategy": args.text_filtered_strategy,
            "visual_strategy": args.visual_filtered_strategy,
            "description": "metadata-aware text hybrid retrieval plus metadata-aware visual text-to-frame retrieval",
        },
    ]

    text_rows_by_strategy = {
        spec["text_strategy"]: load_strategy_rows(text_result_path, spec["text_strategy"])
        for spec in strategy_specs
    }
    visual_rows_by_strategy = {
        spec["visual_strategy"]: load_strategy_rows(visual_result_path, spec["visual_strategy"])
        for spec in strategy_specs
    }
    text_latency_by_strategy = {
        spec["text_strategy"]: load_latency(text_metrics_path, spec["text_strategy"])
        for spec in strategy_specs
    }
    visual_latency_by_strategy = {
        spec["visual_strategy"]: load_latency(visual_metrics_path, spec["visual_strategy"])
        for spec in strategy_specs
    }

    result_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []

    for query in queries.to_dict("records"):
        query_id = query["query_id"]
        positives = positives_by_query.get(query_id, set())
        for spec in strategy_specs:
            text_strategy = spec["text_strategy"]
            visual_strategy = spec["visual_strategy"]
            text_rows = text_rows_by_strategy[text_strategy].get(query_id, [])
            visual_rows = visual_rows_by_strategy[visual_strategy].get(query_id, [])

            start = time.perf_counter()
            fused = rrf_fuse(
                text_rows,
                visual_rows,
                rrf_k=args.rrf_k,
                text_weight=args.text_weight,
                visual_weight=args.visual_weight,
                max_rank=args.max_rank,
            )
            fusion_latency_ms = (time.perf_counter() - start) * 1000.0
            text_latency_ms = text_latency_by_strategy[text_strategy].get(query_id, 0.0)
            visual_latency_ms = visual_latency_by_strategy[visual_strategy].get(query_id, 0.0)
            total_latency_ms = text_latency_ms + visual_latency_ms + fusion_latency_ms

            ranking = [item["clip_id"] for item in fused]
            metrics = evaluate_ranking(ranking, positives, top_ks)
            metric_rows.append(
                {
                    "strategy": spec["strategy"],
                    "query_id": query_id,
                    "difficulty": query["difficulty"],
                    "positive_count": int(query["positive_count"]),
                    "latency_ms": total_latency_ms,
                    "text_latency_ms": text_latency_ms,
                    "visual_latency_ms": visual_latency_ms,
                    "fusion_latency_ms": fusion_latency_ms,
                    **metrics,
                }
            )
            for rank, item in enumerate(fused, start=1):
                result_rows.append(
                    {
                        "strategy": spec["strategy"],
                        "query_id": query_id,
                        "rank": rank,
                        "clip_id": item["clip_id"],
                        "score": item["score"],
                        "text_rank": item["text_rank"],
                        "text_score": item["text_score"],
                        "visual_rank": item["visual_rank"],
                        "visual_score": item["visual_score"],
                        "visual_frame_id": item["visual_frame_id"],
                        "is_relevant": item["clip_id"] in positives,
                    }
                )

    results = pd.DataFrame(result_rows)
    metrics_by_query = pd.DataFrame(metric_rows)
    summary = summarize_metrics(metrics_by_query)
    latency = summarize_latency(metrics_by_query)

    results.to_parquet(args.output_dir / "multimodal_fusion_results.parquet", index=False)
    metrics_by_query.to_parquet(args.output_dir / "metrics_by_query.parquet", index=False)
    summary.to_csv(args.output_dir / "metrics_summary.csv", index=False)
    latency.to_csv(args.output_dir / "latency_summary.csv", index=False)

    run_manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "text_result_root": str(args.text_result_root),
        "visual_result_root": str(args.visual_result_root),
        "output_dir": str(args.output_dir),
        "strategies": strategy_specs,
        "rrf_k": args.rrf_k,
        "text_weight": args.text_weight,
        "visual_weight": args.visual_weight,
        "top_ks": top_ks,
        "max_rank": args.max_rank,
        "counts": {
            "queries": int(len(queries)),
            "qrels": int(len(qrels)),
            "result_rows": int(len(results)),
        },
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    all_rows = summary[summary["difficulty"].eq("all")].copy()
    lines = [
        "# Multimodal Fusion Retrieval Summary",
        "",
        f"created_at: `{run_manifest['created_at']}`",
        f"canonical_root: `{args.canonical_root}`",
        f"text_result_root: `{args.text_result_root}`",
        f"visual_result_root: `{args.visual_result_root}`",
        f"rrf_k: `{args.rrf_k}`",
        "",
        "## Overall Metrics",
        "",
        "| strategy | recall_at_10 | recall_at_20 | mrr | ndcg_at_10 |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in all_rows.to_dict("records"):
        lines.append(
            f"| {row['strategy']} | {row['recall_at_10']:.4f} | {row['recall_at_20']:.4f} | "
            f"{row['mrr']:.4f} | {row['ndcg_at_10']:.4f} |"
        )
    lines.extend(["", "## Latency", "", "| strategy | mean ms | p50 ms | p95 ms |", "|---|---:|---:|---:|"])
    for row in latency.to_dict("records"):
        lines.append(
            f"| {row['strategy']} | {row['latency_mean_ms']:.3f} | {row['latency_p50_ms']:.3f} | "
            f"{row['latency_p95_ms']:.3f} |"
        )
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"output_dir={args.output_dir}")
    print(f"queries={len(queries)}")
    print(f"strategies={','.join(spec['strategy'] for spec in strategy_specs)}")
    print(f"result_rows={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
