#!/usr/bin/env python3
"""Build service-level evidence packets for AI Hub 71953 retrieval runs."""

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


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(jsonable(row), ensure_ascii=False) + "\n")


def jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    if hasattr(value, "item"):
        return value.item()
    return value


def compact(value: Any, limit: int = 500) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def metadata_by_clip(metadata: pd.DataFrame) -> dict[str, dict[str, str]]:
    wide = (
        metadata.pivot_table(index="clip_id", columns="facet_name", values="facet_value", aggfunc="first")
        .reset_index()
        .fillna("")
    )
    return {
        str(row["clip_id"]): {str(k): str(v) for k, v in row.items() if k != "clip_id" and str(v) != ""}
        for row in wide.to_dict("records")
    }


def text_by_clip(documents: pd.DataFrame) -> dict[str, dict[str, str]]:
    priority = {
        "evidence_c1": 0,
        "evidence_c2": 0,
        "caption_c1": 1,
        "caption_c2": 1,
        "answer": 2,
        "event_statement": 3,
    }
    docs = documents.copy()
    docs["priority"] = docs["doc_type"].map(priority).fillna(10)
    rows: dict[str, dict[str, str]] = {}
    for clip_id, group in docs.sort_values(["clip_id", "priority", "doc_id"], kind="mergesort").groupby("clip_id", sort=False):
        first = group.iloc[0]
        rows[str(clip_id)] = {
            "supporting_doc_id": str(first["doc_id"]),
            "supporting_doc_type": str(first["doc_type"]),
            "supporting_text": compact(first["text"], 700),
        }
    return rows


def representative_frame_by_clip(frames: pd.DataFrame) -> dict[str, dict[str, Any]]:
    priority = {
        "label_evidence_frame": 0,
        "context_distractor_frame": 1,
    }
    work = frames.copy()
    work["frame_priority"] = work["extraction_strategy"].map(priority).fillna(10)
    rows: dict[str, dict[str, Any]] = {}
    for clip_id, group in work.sort_values(
        ["clip_id", "frame_priority", "view", "view_frame_seq", "frame_index"],
        kind="mergesort",
    ).groupby("clip_id", sort=False):
        rows[str(clip_id)] = group.iloc[0].to_dict()
    return rows


def load_retrieval_results(retrieval_root: Path) -> tuple[pd.DataFrame, str]:
    visual_path = retrieval_root / "visual_retrieval_results.parquet"
    text_path = retrieval_root / "retrieval_results.parquet"
    if visual_path.exists():
        return pd.read_parquet(visual_path), "visual_retrieval_results.parquet"
    if text_path.exists():
        return pd.read_parquet(text_path), "retrieval_results.parquet"
    raise FileNotFoundError(
        f"No retrieval result parquet found in {retrieval_root}. "
        "Expected visual_retrieval_results.parquet or retrieval_results.parquet."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--frame-root", type=Path, required=True)
    parser.add_argument("--retrieval-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--strategy", default="M4_metadata_prefilter_visual")
    parser.add_argument("--top-k", type=int, default=5)
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
    documents = pd.read_parquet(args.canonical_root / "documents.parquet")
    metadata = pd.read_parquet(args.canonical_root / "metadata.parquet")
    frames = pd.read_parquet(args.frame_root / "frames.parquet")
    results, result_file = load_retrieval_results(args.retrieval_root)

    query_map = {str(row["query_id"]): row for row in queries.to_dict("records")}
    frame_map = {str(row["frame_id"]): row for row in frames.to_dict("records")}
    representative_frames = representative_frame_by_clip(frames)
    metadata_map = metadata_by_clip(metadata)
    text_map = text_by_clip(documents)

    subset = results[results["strategy"].eq(args.strategy)].sort_values(["query_id", "rank"], kind="mergesort")
    packets: list[dict[str, Any]] = []
    flat_rows: list[dict[str, Any]] = []
    for query_id, group in subset.groupby("query_id", sort=False):
        query = query_map.get(str(query_id), {})
        evidence: list[dict[str, Any]] = []
        for row in group.head(args.top_k).to_dict("records"):
            frame_id = row.get("frame_id")
            frame = frame_map.get(str(frame_id), {})
            frame_selection_policy = "retrieved_frame"
            if not frame:
                frame = representative_frames.get(str(row["clip_id"]), {})
                frame_id = frame.get("frame_id")
                frame_selection_policy = "representative_label_evidence_frame"
            text = text_map.get(str(row["clip_id"]), {})
            item = {
                "rank": int(row["rank"]),
                "clip_id": row["clip_id"],
                "frame_id": frame_id,
                "frame_selection_policy": frame_selection_policy,
                "view": frame.get("view"),
                "frame_index": frame.get("frame_index"),
                "timestamp_sec": frame.get("timestamp_sec"),
                "thumbnail_path": frame.get("frame_path"),
                "media_path": frame.get("media_path"),
                "obj_id": frame.get("obj_id"),
                "obj_label": frame.get("obj_label"),
                "bbox": [frame.get("bbox_x1"), frame.get("bbox_y1"), frame.get("bbox_x2"), frame.get("bbox_y2")],
                "evidence_text": compact(frame.get("evidence_text"), 500),
                "supporting_doc_id": text.get("supporting_doc_id"),
                "supporting_doc_type": text.get("supporting_doc_type"),
                "supporting_text": text.get("supporting_text", ""),
                "metadata": metadata_map.get(str(row["clip_id"]), {}),
                "score": row.get("score"),
                "is_relevant": bool(row.get("is_relevant", False)),
            }
            evidence.append(item)
            flat_rows.append(
                {
                    "query_id": query_id,
                    "rank": item["rank"],
                    "clip_id": item["clip_id"],
                    "frame_id": item["frame_id"],
                    "frame_selection_policy": item["frame_selection_policy"],
                    "view": item["view"],
                    "is_relevant": item["is_relevant"],
                    "score": item["score"],
                }
            )

        top = evidence[0] if evidence else {}
        answer = (
            f"검색된 1순위 근거는 {top.get('clip_id')}의 {top.get('view')} view, "
            f"frame {top.get('frame_index')}이다. 근거 문장: {compact(top.get('evidence_text') or top.get('supporting_text'), 260)}"
            if top
            else "검색된 근거가 없다."
        )
        packet = {
            "request": {
                "request_id": f"aihub71953:{args.strategy}:{query_id}",
                "dataset_id": "aihub_multi_angle_cctv",
                "query_id": query_id,
                "query_text": query.get("query_text", ""),
                "metadata_filter": query.get("metadata_filter", {}),
                "strategy": args.strategy,
            },
            "evidence": evidence,
            "answer_context": "\n".join(
                f"rank={item['rank']}; clip={item['clip_id']}; view={item['view']}; "
                f"frame={item['frame_index']}; bbox={item['bbox']}; text={compact(item['evidence_text'] or item['supporting_text'], 240)}"
                for item in evidence[:3]
            ),
            "extractive_answer": {
                "answer_type": "evidence_only_template",
                "answer": answer,
                "grounded": True,
                "used_evidence_ranks": [1] if evidence else [],
            },
            "service_contract": {
                "answer_policy": "Use only returned frame/object/text/metadata evidence. Do not invent unseen events.",
                "llm_used": False,
                "vlm_generation_used": False,
            },
        }
        packets.append(packet)

    write_jsonl(args.output_dir / "service_packets.jsonl", packets)
    flat = pd.DataFrame(flat_rows)
    flat.to_parquet(args.output_dir / "service_evidence_rows.parquet", index=False)
    summary_df = (
        flat.groupby("query_id")["is_relevant"].agg(top_k_relevant="max", relevant_count="sum").reset_index()
        if not flat.empty
        else pd.DataFrame(columns=["query_id", "top_k_relevant", "relevant_count"])
    )
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "frame_root": str(args.frame_root),
        "retrieval_root": str(args.retrieval_root),
        "retrieval_result_file": result_file,
        "strategy": args.strategy,
        "top_k": args.top_k,
        "packets": int(len(packets)),
        "evidence_rows": int(len(flat)),
        "top_k_hit_rate": float(summary_df["top_k_relevant"].mean()) if not summary_df.empty else 0.0,
        "top_1_relevant_rate": float(flat[flat["rank"].eq(1)]["is_relevant"].mean()) if not flat.empty else 0.0,
    }
    (args.output_dir / "service_packet_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# AI Hub 71953 Service Packet Summary",
        "",
        f"created_at: `{summary['created_at']}`",
        f"strategy: `{summary['strategy']}`",
        "",
        "| item | value |",
        "|---|---:|",
        f"| packets | {summary['packets']} |",
        f"| evidence_rows | {summary['evidence_rows']} |",
        f"| top_k_hit_rate | {summary['top_k_hit_rate']:.4f} |",
        f"| top_1_relevant_rate | {summary['top_1_relevant_rate']:.4f} |",
    ]
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"output_dir={args.output_dir}")
    print(f"packets={summary['packets']}")
    print(f"evidence_rows={summary['evidence_rows']}")
    print(f"top_k_hit_rate={summary['top_k_hit_rate']:.4f}")
    print(f"top_1_relevant_rate={summary['top_1_relevant_rate']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
