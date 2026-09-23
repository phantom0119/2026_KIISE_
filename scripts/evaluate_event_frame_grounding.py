#!/usr/bin/env python3
"""Evaluate whether retrieved evidence frames fall inside labeled event frame ranges."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def load_results(result_path: Path, strategy: str, frame_col: str) -> pd.DataFrame:
    df = pd.read_parquet(result_path)
    subset = df[df["strategy"].eq(strategy)].copy()
    if subset.empty:
        available = sorted(df["strategy"].dropna().unique().tolist())
        raise ValueError(f"Strategy {strategy!r} not found in {result_path}. Available: {available}")
    if frame_col not in subset.columns:
        raise ValueError(f"Frame column {frame_col!r} not found in {result_path}.")
    return subset


def add_event_grounding(results: pd.DataFrame, clips: pd.DataFrame, frame_index: pd.DataFrame, frame_col: str) -> pd.DataFrame:
    frames = frame_index[["frame_id", "frame_index", "timestamp_sec", "frame_path"]].rename(
        columns={
            "frame_id": frame_col,
            "frame_index": "evidence_frame_index",
            "timestamp_sec": "evidence_timestamp_sec",
            "frame_path": "evidence_frame_path",
        }
    )
    event_cols = clips[["clip_id", "event_start_frame", "event_end_frame"]].copy()
    merged = results.merge(frames, on=frame_col, how="left").merge(event_cols, on="clip_id", how="left")
    merged["has_visual_frame"] = merged[frame_col].notna() & merged["evidence_frame_index"].notna()
    merged["frame_in_event"] = (
        merged["has_visual_frame"]
        & merged["event_start_frame"].notna()
        & merged["event_end_frame"].notna()
        & merged["evidence_frame_index"].ge(merged["event_start_frame"])
        & merged["evidence_frame_index"].le(merged["event_end_frame"])
    )
    return merged


def summarize_by_query(results: pd.DataFrame, top_ks: list[int]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for query_id, group in results.sort_values(["query_id", "rank"], kind="mergesort").groupby("query_id", sort=False):
        row: dict[str, Any] = {"query_id": query_id}
        for k in top_ks:
            top = group[group["rank"].le(k)]
            denom = max(len(top), 1)
            visual = top[top["has_visual_frame"]]
            visual_denom = max(len(visual), 1)
            relevant = top[top["is_relevant"].eq(True)]
            grounded_relevant = relevant[relevant["frame_in_event"].eq(True)]
            row[f"visual_coverage_at_{k}"] = len(visual) / denom
            row[f"frame_in_event_rate_at_{k}"] = visual["frame_in_event"].mean() if len(visual) else 0.0
            row[f"event_grounded_hit_at_{k}"] = 1.0 if len(grounded_relevant) else 0.0
            row[f"relevant_hit_at_{k}"] = 1.0 if len(relevant) else 0.0
            row[f"grounded_relevant_ratio_at_{k}"] = len(grounded_relevant) / visual_denom
        rows.append(row)
    return pd.DataFrame(rows)


def summarize(metrics_by_query: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [col for col in metrics_by_query.columns if col != "query_id"]
    row = {"queries": len(metrics_by_query)}
    row.update({col: metrics_by_query[col].mean() for col in metric_cols})
    return pd.DataFrame([row])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--frame-index-path", type=Path, required=True)
    parser.add_argument("--result-path", type=Path, required=True)
    parser.add_argument("--strategy", required=True)
    parser.add_argument("--frame-col", default="frame_id")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--top-ks", default="1,5,10")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    clips = pd.read_parquet(args.canonical_root / "clips.parquet")
    frame_index = pd.read_parquet(args.frame_index_path)
    results = load_results(args.result_path, args.strategy, args.frame_col)
    grounded = add_event_grounding(results, clips, frame_index, args.frame_col)
    top_ks = [int(value) for value in args.top_ks.split(",") if value.strip()]
    metrics_by_query = summarize_by_query(grounded, top_ks)
    summary = summarize(metrics_by_query)

    grounded.to_parquet(args.output_dir / "event_frame_grounding_results.parquet", index=False)
    metrics_by_query.to_parquet(args.output_dir / "metrics_by_query.parquet", index=False)
    summary.to_csv(args.output_dir / "metrics_summary.csv", index=False)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "frame_index_path": str(args.frame_index_path),
        "result_path": str(args.result_path),
        "strategy": args.strategy,
        "frame_col": args.frame_col,
        "top_ks": top_ks,
        "counts": {
            "result_rows": int(len(results)),
            "queries": int(len(metrics_by_query)),
            "frames_with_event_hit": int(grounded["frame_in_event"].sum()),
        },
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    row = summary.iloc[0].to_dict()
    lines = [
        "# Event Frame Grounding Summary",
        "",
        f"created_at: `{manifest['created_at']}`",
        f"strategy: `{args.strategy}`",
        f"result_path: `{args.result_path}`",
        f"frame_col: `{args.frame_col}`",
        "",
        "| metric | value |",
        "|---|---:|",
    ]
    for key, value in row.items():
        lines.append(f"| {key} | {value:.4f} |" if isinstance(value, float) else f"| {key} | {value} |")
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"output_dir={args.output_dir}")
    print(f"strategy={args.strategy}")
    print(f"queries={len(metrics_by_query)}")
    print(f"result_rows={len(results)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
