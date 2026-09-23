#!/usr/bin/env python3
"""Sweep text/visual RRF weights for evidence selection quality."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.io import load_canonical  # noqa: E402
from vlmdb_workload.metrics import evaluate_ranking  # noqa: E402


TEXT_STRATEGY = "B5_hybrid"
VISUAL_STRATEGY = "M4_metadata_prefilter_visual"


def parse_weights(spec: str) -> list[tuple[float, float]]:
    pairs: list[tuple[float, float]] = []
    for chunk in spec.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        left, right = chunk.split(":", 1)
        pairs.append((float(left), float(right)))
    return pairs


def strategy_name(text_weight: float, visual_weight: float) -> str:
    def fmt(value: float) -> str:
        text = f"{value:g}".replace(".", "p")
        return text

    return f"RW_t{fmt(text_weight)}_v{fmt(visual_weight)}"


def load_rankings(path: Path, strategy: str) -> dict[str, list[dict[str, Any]]]:
    df = pd.read_parquet(path)
    subset = df[df["strategy"].eq(strategy)].sort_values(["query_id", "rank"], kind="mergesort")
    if subset.empty:
        available = sorted(df["strategy"].dropna().unique().tolist())
        raise ValueError(f"{strategy!r} not found in {path}. Available: {available}")
    return {query_id: group.to_dict("records") for query_id, group in subset.groupby("query_id", sort=False)}


def weighted_rrf(
    text_rows: list[dict[str, Any]],
    visual_rows: list[dict[str, Any]],
    *,
    text_weight: float,
    visual_weight: float,
    rrf_k: int,
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
            item["text_score"] = row.get("score")
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
            item["visual_score"] = row.get("score")
            item["visual_frame_id"] = row.get("frame_id")
    return sorted(
        items.values(),
        key=lambda item: (
            -float(item["score"]),
            item["text_rank"] if item["text_rank"] is not None else 10**9,
            item["visual_rank"] if item["visual_rank"] is not None else 10**9,
            item["clip_id"],
        ),
    )[:max_rank]


def summarize(metrics_by_query: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        col
        for col in metrics_by_query.columns
        if col.startswith("recall_at_") or col.startswith("hit_at_") or col in {"mrr", "ndcg_at_10"}
    ]
    rows = []
    for strategy, group in metrics_by_query.groupby("strategy", sort=False):
        row = {"strategy": strategy, "queries": len(group)}
        row.update({col: group[col].mean() for col in metric_cols})
        rows.append(row)
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--text-result-path", type=Path, required=True)
    parser.add_argument("--visual-result-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--weights", default="4:1,2:1,1:1,1:2,1:4,3:1,1:3")
    parser.add_argument("--rrf-k", type=int, default=60)
    parser.add_argument("--top-ks", default="1,5,10,20")
    parser.add_argument("--max-rank", type=int, default=100)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    _clips, _documents, _metadata, queries, qrels = load_canonical(args.canonical_root)
    positives_by_query = {
        query_id: set(group["target_id"])
        for query_id, group in qrels.groupby("query_id", sort=False)
    }
    text_rankings = load_rankings(args.text_result_path, TEXT_STRATEGY)
    visual_rankings = load_rankings(args.visual_result_path, VISUAL_STRATEGY)
    weights = parse_weights(args.weights)
    top_ks = [int(value) for value in args.top_ks.split(",") if value.strip()]

    result_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    for text_weight, visual_weight in weights:
        strategy = strategy_name(text_weight, visual_weight)
        for query in queries.to_dict("records"):
            query_id = query["query_id"]
            positives = positives_by_query.get(query_id, set())
            fused = weighted_rrf(
                text_rankings.get(query_id, []),
                visual_rankings.get(query_id, []),
                text_weight=text_weight,
                visual_weight=visual_weight,
                rrf_k=args.rrf_k,
                max_rank=args.max_rank,
            )
            ranking = [item["clip_id"] for item in fused]
            metrics = evaluate_ranking(ranking, positives, top_ks)
            metric_rows.append(
                {
                    "strategy": strategy,
                    "text_weight": text_weight,
                    "visual_weight": visual_weight,
                    "query_id": query_id,
                    "difficulty": query["difficulty"],
                    "positive_count": int(query["positive_count"]),
                    **metrics,
                }
            )
            for rank, item in enumerate(fused, start=1):
                result_rows.append(
                    {
                        "strategy": strategy,
                        "text_weight": text_weight,
                        "visual_weight": visual_weight,
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
    summary = summarize(metrics_by_query)
    results.to_parquet(args.output_dir / "weighted_fusion_results.parquet", index=False)
    metrics_by_query.to_parquet(args.output_dir / "metrics_by_query.parquet", index=False)
    summary.to_csv(args.output_dir / "metrics_summary.csv", index=False)

    best_hit1 = summary.sort_values(["hit_at_1", "ndcg_at_10"], ascending=False).iloc[0]
    best_ndcg = summary.sort_values(["ndcg_at_10", "hit_at_1"], ascending=False).iloc[0]
    lines = [
        "# Weighted Fusion Rerank Sweep Summary",
        "",
        f"created_at: `{datetime.now(timezone.utc).isoformat()}`",
        f"text_result_path: `{args.text_result_path}`",
        f"visual_result_path: `{args.visual_result_path}`",
        f"rrf_k: `{args.rrf_k}`",
        "",
        "## Best Strategies",
        "",
        f"- best hit@1: `{best_hit1['strategy']}` = {best_hit1['hit_at_1']:.4f}",
        f"- best nDCG@10: `{best_ndcg['strategy']}` = {best_ndcg['ndcg_at_10']:.4f}",
        "",
        "## Summary",
        "",
        "| strategy | hit@1 | hit@5 | recall@5 | recall@10 | mrr | ndcg@10 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.sort_values(["hit_at_1", "ndcg_at_10"], ascending=False).to_dict("records"):
        lines.append(
            f"| {row['strategy']} | {row['hit_at_1']:.4f} | {row['hit_at_5']:.4f} | "
            f"{row['recall_at_5']:.4f} | {row['recall_at_10']:.4f} | {row['mrr']:.4f} | {row['ndcg_at_10']:.4f} |"
        )
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "text_result_path": str(args.text_result_path),
        "visual_result_path": str(args.visual_result_path),
        "output_dir": str(args.output_dir),
        "text_strategy": TEXT_STRATEGY,
        "visual_strategy": VISUAL_STRATEGY,
        "weights": weights,
        "rrf_k": args.rrf_k,
        "top_ks": top_ks,
        "max_rank": args.max_rank,
        "counts": {
            "queries": int(len(queries)),
            "result_rows": int(len(results)),
        },
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"output_dir={args.output_dir}")
    print(f"queries={len(queries)}")
    print(f"strategies={len(weights)}")
    print(f"best_hit1={best_hit1['strategy']}:{best_hit1['hit_at_1']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
