#!/usr/bin/env python3
"""Evaluate answer-grounding risk from AI Hub 71953 service evidence packets."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def has_bbox(item: dict[str, Any]) -> bool:
    bbox = item.get("bbox")
    return isinstance(bbox, list) and len(bbox) >= 4 and all(value is not None for value in bbox[:4])


def has_text(item: dict[str, Any]) -> bool:
    return bool(str(item.get("evidence_text") or item.get("supporting_text") or "").strip())


def summarize(rows: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        "top1_relevant",
        "topk_relevant",
        "grounded_top1",
        "grounded_topk",
        "wrong_same_class_top1",
        "wrong_top1",
        "has_any_bbox_topk",
        "has_any_text_topk",
        "target_view_coverage_topk",
        "first_relevant_rank",
        "relevant_count_topk",
    ]
    out: list[dict[str, Any]] = []
    for difficulty, group in rows.groupby("difficulty", sort=False):
        row: dict[str, Any] = {"difficulty": difficulty, "queries": len(group)}
        for col in metric_cols:
            values = group[col]
            row[col] = values[values.notna()].mean() if values.notna().any() else None
        out.append(row)
    row = {"difficulty": "all", "queries": len(rows)}
    for col in metric_cols:
        values = rows[col]
        row[col] = values[values.notna()].mean() if values.notna().any() else None
    out.append(row)
    return pd.DataFrame(out)


def format_value(value: Any) -> str:
    if value is None or pd.isna(value):
        return ""
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--service-packet-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    if args.output_dir.exists() and args.overwrite:
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    queries = pd.DataFrame(read_jsonl(args.canonical_root / "queries.jsonl"))
    qrels = pd.read_csv(args.canonical_root / "qrels.tsv", sep="\t")
    packets = read_jsonl(args.service_packet_root / "service_packets.jsonl")

    query_map = {str(row["query_id"]): row for row in queries.to_dict("records")}
    positives_by_query = {
        str(query_id): {str(value) for value in group["target_id"].tolist()}
        for query_id, group in qrels.groupby("query_id", sort=False)
    }

    rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    for packet in packets:
        request = packet.get("request") or {}
        query_id = str(request.get("query_id") or "")
        query = query_map.get(query_id, {})
        positives = positives_by_query.get(query_id, set())
        semantic_filter = query.get("semantic_filter") or {}
        target_event_class = semantic_filter.get("event_class") or (query.get("metadata_filter") or {}).get("event_class")
        evidence = packet.get("evidence") or []
        top = evidence[0] if evidence else {}

        relevant_items = [item for item in evidence if str(item.get("clip_id")) in positives]
        first_relevant_rank = min((int(item.get("rank")) for item in relevant_items), default=None)
        top1_relevant = bool(top) and str(top.get("clip_id")) in positives
        wrong_top1 = bool(top) and not top1_relevant
        top_metadata = top.get("metadata") or {}
        wrong_same_class_top1 = (
            wrong_top1
            and bool(target_event_class)
            and str(top_metadata.get("event_class") or "") == str(target_event_class)
        )
        grounded_top1 = top1_relevant and has_bbox(top) and has_text(top)
        grounded_topk = any(has_bbox(item) and has_text(item) for item in relevant_items)
        target_views = {
            str(item.get("view"))
            for item in relevant_items
            if item.get("view") is not None and str(item.get("view")) != ""
        }
        all_target_views = {"c1", "c2"}
        target_view_coverage = len(target_views & all_target_views) / len(all_target_views)

        rows.append(
            {
                "query_id": query_id,
                "task": query.get("task"),
                "difficulty": query.get("difficulty", "unknown"),
                "strategy": request.get("strategy"),
                "positive_count": len(positives),
                "evidence_count": len(evidence),
                "top1_clip_id": top.get("clip_id"),
                "top1_event_class": top_metadata.get("event_class"),
                "target_event_class": target_event_class,
                "top1_relevant": float(top1_relevant),
                "topk_relevant": float(bool(relevant_items)),
                "grounded_top1": float(grounded_top1),
                "grounded_topk": float(grounded_topk),
                "wrong_same_class_top1": float(wrong_same_class_top1),
                "wrong_top1": float(wrong_top1),
                "has_any_bbox_topk": float(any(has_bbox(item) for item in evidence)),
                "has_any_text_topk": float(any(has_text(item) for item in evidence)),
                "target_view_coverage_topk": target_view_coverage,
                "first_relevant_rank": float(first_relevant_rank) if first_relevant_rank is not None else None,
                "relevant_count_topk": float(len(relevant_items)),
            }
        )
        for item in evidence:
            evidence_rows.append(
                {
                    "query_id": query_id,
                    "strategy": request.get("strategy"),
                    "rank": item.get("rank"),
                    "clip_id": item.get("clip_id"),
                    "frame_id": item.get("frame_id"),
                    "view": item.get("view"),
                    "frame_selection_policy": item.get("frame_selection_policy"),
                    "event_class": (item.get("metadata") or {}).get("event_class"),
                    "is_target_clip": str(item.get("clip_id")) in positives,
                    "has_bbox": has_bbox(item),
                    "has_text": has_text(item),
                }
            )

    by_query = pd.DataFrame(rows)
    evidence_df = pd.DataFrame(evidence_rows)
    summary = summarize(by_query)

    by_query.to_parquet(args.output_dir / "answer_grounding_by_query.parquet", index=False)
    evidence_df.to_parquet(args.output_dir / "answer_grounding_evidence_rows.parquet", index=False)
    summary.to_csv(args.output_dir / "answer_grounding_summary.csv", index=False)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "service_packet_root": str(args.service_packet_root),
        "output_dir": str(args.output_dir),
        "counts": {
            "queries": int(len(by_query)),
            "evidence_rows": int(len(evidence_df)),
        },
        "metric_semantics": {
            "topk_relevant": "At least one returned evidence item belongs to the qrel target clip.",
            "grounded_topk": "At least one target-clip evidence item has both bbox and textual evidence.",
            "wrong_same_class_top1": "Rank-1 evidence is not the target clip but has the same event_class, indicating class-only grounding risk.",
            "llm_used": False,
        },
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# AI Hub 71953 Answer Grounding Summary",
        "",
        f"created_at: `{manifest['created_at']}`",
        f"service_packet_root: `{args.service_packet_root}`",
        "",
        "| difficulty | queries | top1_relevant | topk_relevant | grounded_top1 | grounded_topk | wrong_same_class_top1 | first_relevant_rank | target_view_coverage_topk |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        lines.append(
            f"| {row['difficulty']} | {row['queries']} | {format_value(row['top1_relevant'])} | "
            f"{format_value(row['topk_relevant'])} | {format_value(row['grounded_top1'])} | "
            f"{format_value(row['grounded_topk'])} | {format_value(row['wrong_same_class_top1'])} | "
            f"{format_value(row['first_relevant_rank'])} | {format_value(row['target_view_coverage_topk'])} |"
        )
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"output_dir={args.output_dir}")
    print(f"queries={len(by_query)}")
    print(f"evidence_rows={len(evidence_df)}")
    all_row = summary[summary["difficulty"].eq("all")].iloc[0].to_dict()
    print(f"top1_relevant={all_row['top1_relevant']:.4f}")
    print(f"topk_relevant={all_row['topk_relevant']:.4f}")
    print(f"grounded_topk={all_row['grounded_topk']:.4f}")
    print(f"wrong_same_class_top1={all_row['wrong_same_class_top1']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
