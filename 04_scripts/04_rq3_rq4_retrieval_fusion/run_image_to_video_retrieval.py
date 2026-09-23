#!/usr/bin/env python3
"""Run image-to-video retrieval using held-out keyframe embeddings as image queries."""

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


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "03_src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.metrics import evaluate_ranking  # noqa: E402


STRATEGY = "IM1_image_to_video_holdout"


def select_query_frames(frame_index: pd.DataFrame, query_frame_seq: int) -> pd.DataFrame:
    rows = []
    for _clip_id, group in frame_index.sort_values(["clip_id", "frame_seq"], kind="mergesort").groupby("clip_id", sort=False):
        exact = group[group["frame_seq"].eq(query_frame_seq)]
        row = exact.iloc[0] if not exact.empty else group.iloc[len(group) // 2]
        rows.append(row)
    return pd.DataFrame(rows).reset_index(drop=True)


def rank_frames_to_clips(
    scores: np.ndarray,
    frame_index: pd.DataFrame,
    *,
    excluded_frame_id: str,
    max_rank: int,
) -> list[tuple[str, str, float]]:
    order = np.argsort(-scores, kind="mergesort")
    best: dict[str, tuple[str, float]] = {}
    for idx in order.tolist():
        row = frame_index.iloc[int(idx)]
        frame_id = row["frame_id"]
        if frame_id == excluded_frame_id:
            continue
        clip_id = row["clip_id"]
        score = float(scores[idx])
        if clip_id not in best or score > best[clip_id][1]:
            best[clip_id] = (frame_id, score)
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
    row = {"strategy": STRATEGY, "queries": len(metrics_by_query)}
    row.update({col: metrics_by_query[col].mean() for col in metric_cols})
    return pd.DataFrame([row])


def summarize_latency(metrics_by_query: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "strategy": STRATEGY,
                "queries": len(metrics_by_query),
                "latency_mean_ms": metrics_by_query["latency_ms"].mean(),
                "latency_p50_ms": metrics_by_query["latency_ms"].quantile(0.50),
                "latency_p95_ms": metrics_by_query["latency_ms"].quantile(0.95),
            }
        ]
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--visual-embedding-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--query-frame-seq", type=int, default=2)
    parser.add_argument("--top-ks", default="1,5,10,20")
    parser.add_argument("--max-rank", type=int, default=100)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    frame_index = pd.read_parquet(args.visual_embedding_root / "frame_index.parquet")
    frame_embeddings = np.load(args.visual_embedding_root / "frame_embeddings.npy").astype("float32")
    manifest = json.loads((args.visual_embedding_root / "visual_embedding_manifest.json").read_text(encoding="utf-8"))
    if len(frame_index) != len(frame_embeddings):
        raise ValueError("Frame index and embedding count differ.")

    query_frames = select_query_frames(frame_index, args.query_frame_seq)
    top_ks = [int(value) for value in args.top_ks.split(",") if value.strip()]
    frame_pos_by_id = dict(zip(frame_index["frame_id"], range(len(frame_index)), strict=False))

    result_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    query_rows: list[dict[str, Any]] = []

    for query_no, query_frame in enumerate(query_frames.to_dict("records"), start=1):
        query_id = f"image:{query_no:06d}"
        query_frame_id = query_frame["frame_id"]
        query_pos = frame_pos_by_id[query_frame_id]
        query_vector = frame_embeddings[query_pos]
        positives = {query_frame["clip_id"]}

        start = time.perf_counter()
        scores = frame_embeddings @ query_vector
        ranking = rank_frames_to_clips(scores, frame_index, excluded_frame_id=query_frame_id, max_rank=args.max_rank)
        latency_ms = (time.perf_counter() - start) * 1000.0

        ranked_clips = [clip_id for clip_id, _frame_id, _score in ranking]
        metrics = evaluate_ranking(ranked_clips, positives, top_ks)
        metric_rows.append(
            {
                "strategy": STRATEGY,
                "query_id": query_id,
                "positive_count": 1,
                "latency_ms": latency_ms,
                **metrics,
            }
        )
        query_rows.append(
            {
                "query_id": query_id,
                "query_clip_id": query_frame["clip_id"],
                "query_frame_id": query_frame_id,
                "query_frame_path": query_frame["frame_path"],
                "query_timestamp_sec": query_frame["timestamp_sec"],
            }
        )
        for rank, (clip_id, frame_id, score) in enumerate(ranking, start=1):
            result_rows.append(
                {
                    "strategy": STRATEGY,
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
    queries = pd.DataFrame(query_rows)
    summary = summarize_metrics(metrics_by_query)
    latency = summarize_latency(metrics_by_query)

    queries.to_parquet(args.output_dir / "image_queries.parquet", index=False)
    results.to_parquet(args.output_dir / "image_query_results.parquet", index=False)
    metrics_by_query.to_parquet(args.output_dir / "metrics_by_query.parquet", index=False)
    summary.to_csv(args.output_dir / "metrics_summary.csv", index=False)
    latency.to_csv(args.output_dir / "latency_summary.csv", index=False)

    run_manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "visual_embedding_root": str(args.visual_embedding_root),
        "output_dir": str(args.output_dir),
        "visual_embedding_manifest": manifest,
        "strategy": STRATEGY,
        "query_frame_seq": args.query_frame_seq,
        "top_ks": top_ks,
        "max_rank": args.max_rank,
        "counts": {
            "frames": int(len(frame_index)),
            "queries": int(len(queries)),
            "result_rows": int(len(results)),
        },
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    row = summary.iloc[0]
    lat = latency.iloc[0]
    lines = [
        "# Image-to-Video Retrieval Summary",
        "",
        f"created_at: `{run_manifest['created_at']}`",
        f"visual_embedding_root: `{args.visual_embedding_root}`",
        f"query_frame_seq: `{args.query_frame_seq}`",
        "",
        "## Overall Metrics",
        "",
        "| strategy | queries | recall_at_1 | recall_at_5 | recall_at_10 | mrr | ndcg_at_10 |",
        "|---|---:|---:|---:|---:|---:|---:|",
        f"| {STRATEGY} | {int(row['queries'])} | {row['recall_at_1']:.4f} | {row['recall_at_5']:.4f} | "
        f"{row['recall_at_10']:.4f} | {row['mrr']:.4f} | {row['ndcg_at_10']:.4f} |",
        "",
        "## Latency",
        "",
        "| strategy | mean ms | p50 ms | p95 ms |",
        "|---|---:|---:|---:|",
        f"| {STRATEGY} | {lat['latency_mean_ms']:.3f} | {lat['latency_p50_ms']:.3f} | {lat['latency_p95_ms']:.3f} |",
    ]
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"output_dir={args.output_dir}")
    print(f"queries={len(queries)}")
    print(f"frames={len(frame_index)}")
    print(f"strategy={STRATEGY}")
    print(f"result_rows={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
