#!/usr/bin/env python3
"""Run visual text-to-frame/video retrieval baselines."""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.io import load_canonical  # noqa: E402
from vlmdb_workload.metrics import evaluate_ranking  # noqa: E402
from vlmdb_workload.retrieval import filter_clip_ids, metadata_pivot  # noqa: E402


def rank_frames_to_clips(
    scores: np.ndarray,
    frame_index: pd.DataFrame,
    *,
    candidate_clips: set[str] | None = None,
    max_rank: int,
) -> list[tuple[str, str, float]]:
    order = np.argsort(-scores, kind="mergesort")
    best: dict[str, tuple[str, float]] = {}
    for idx in order.tolist():
        row = frame_index.iloc[int(idx)]
        clip_id = row["clip_id"]
        if candidate_clips is not None and clip_id not in candidate_clips:
            continue
        score = float(scores[idx])
        if clip_id not in best or score > best[clip_id][1]:
            best[clip_id] = (row["frame_id"], score)
        if len(best) >= max_rank:
            break
    ranked = sorted(best.items(), key=lambda item: (-item[1][1], item[0]))
    return [(clip_id, frame_id, score) for clip_id, (frame_id, score) in ranked[:max_rank]]


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
    parser.add_argument("--visual-embedding-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--top-ks", default="1,5,10,20")
    parser.add_argument("--max-rank", type=int, default=100)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    _clips, _documents, metadata, queries, qrels = load_canonical(args.canonical_root)
    metadata_wide = metadata_pivot(metadata)
    frame_index = pd.read_parquet(args.visual_embedding_root / "frame_index.parquet")
    frame_embeddings = np.load(args.visual_embedding_root / "frame_embeddings.npy").astype("float32")
    query_embeddings = np.load(args.visual_embedding_root / "query_text_embeddings.npy").astype("float32")
    manifest = json.loads((args.visual_embedding_root / "visual_embedding_manifest.json").read_text(encoding="utf-8"))

    if len(frame_index) != len(frame_embeddings):
        raise ValueError("Frame index and embedding count differ.")
    if len(queries) != len(query_embeddings):
        raise ValueError("Query and embedding count differ.")

    positives_by_query = {
        query_id: set(group["target_id"])
        for query_id, group in qrels.groupby("query_id", sort=False)
    }
    top_ks = [int(value) for value in args.top_ks.split(",") if value.strip()]

    result_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    strategies = ["M2_visual_vector_only", "M4_metadata_prefilter_visual"]

    for query_pos, query in queries.reset_index(drop=True).iterrows():
        query_id = query["query_id"]
        positives = positives_by_query.get(query_id, set())
        filters = dict(query["metadata_filter"] or {})
        candidate_clips = filter_clip_ids(metadata_wide, filters)
        query_vector = query_embeddings[query_pos]

        start = time.perf_counter()
        scores = frame_embeddings @ query_vector
        m2 = rank_frames_to_clips(scores, frame_index, max_rank=args.max_rank)
        m2_latency = (time.perf_counter() - start) * 1000.0

        start = time.perf_counter()
        m4 = rank_frames_to_clips(scores, frame_index, candidate_clips=candidate_clips, max_rank=args.max_rank)
        m4_latency = (time.perf_counter() - start) * 1000.0

        per_strategy = {
            "M2_visual_vector_only": (m2, m2_latency),
            "M4_metadata_prefilter_visual": (m4, m4_latency),
        }
        for strategy, (ranking, latency_ms) in per_strategy.items():
            ranked_clips = [clip_id for clip_id, _frame_id, _score in ranking]
            metrics = evaluate_ranking(ranked_clips, positives, top_ks)
            metric_rows.append(
                {
                    "strategy": strategy,
                    "query_id": query_id,
                    "difficulty": query["difficulty"],
                    "positive_count": int(query["positive_count"]),
                    "latency_ms": latency_ms,
                    **metrics,
                }
            )
            for rank, (clip_id, frame_id, score) in enumerate(ranking, start=1):
                result_rows.append(
                    {
                        "strategy": strategy,
                        "query_id": query_id,
                        "rank": rank,
                        "clip_id": clip_id,
                        "frame_id": frame_id,
                        "score": score,
                        "is_relevant": clip_id in positives,
                    }
                )

    results = pd.DataFrame(result_rows)
    metrics_by_query = pd.DataFrame(metric_rows)
    summary = summarize_metrics(metrics_by_query)
    latency = summarize_latency(metrics_by_query)

    results.to_parquet(args.output_dir / "visual_retrieval_results.parquet", index=False)
    metrics_by_query.to_parquet(args.output_dir / "metrics_by_query.parquet", index=False)
    summary.to_csv(args.output_dir / "metrics_summary.csv", index=False)
    latency.to_csv(args.output_dir / "latency_summary.csv", index=False)

    run_manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "visual_embedding_root": str(args.visual_embedding_root),
        "output_dir": str(args.output_dir),
        "visual_embedding_manifest": manifest,
        "strategies": strategies,
        "top_ks": top_ks,
        "max_rank": args.max_rank,
        "counts": {
            "frames": int(len(frame_index)),
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
        "# Visual Retrieval Baseline Summary",
        "",
        f"created_at: `{run_manifest['created_at']}`",
        f"canonical_root: `{args.canonical_root}`",
        f"visual_embedding_root: `{args.visual_embedding_root}`",
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
    print(f"frames={len(frame_index)}")
    print(f"strategies={','.join(strategies)}")
    print(f"result_rows={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
