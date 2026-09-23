#!/usr/bin/env python3
"""Build answer-ready service packets from multimodal retrieval outputs."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "03_src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.io import load_canonical  # noqa: E402


TEXT_STRATEGY = "M6_text_visual_metadata_rrf"
IMAGE_STRATEGY = "IM1_image_to_video_holdout"


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
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def compact_text(value: Any, limit: int = 700) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def metadata_by_clip(metadata: pd.DataFrame) -> dict[str, dict[str, str]]:
    if metadata.empty:
        return {}
    wide = (
        metadata.pivot_table(index="clip_id", columns="facet_name", values="facet_value", aggfunc="first")
        .reset_index()
        .fillna("")
    )
    return {
        str(row["clip_id"]): {
            str(k): str(v)
            for k, v in row.items()
            if k != "clip_id" and str(v) != ""
        }
        for row in wide.to_dict("records")
    }


def supporting_text_by_clip(documents: pd.DataFrame) -> dict[str, dict[str, str]]:
    rows = []
    priority = {"event_caption": 0, "dense_caption": 1, "caption": 2, "vqa": 3}
    docs = documents.copy()
    docs["doc_priority"] = docs["doc_type"].map(priority).fillna(10)
    for clip_id, group in docs.sort_values(["clip_id", "doc_priority", "doc_id"], kind="mergesort").groupby("clip_id", sort=False):
        first = group.iloc[0]
        rows.append(
            {
                "clip_id": clip_id,
                "supporting_text": compact_text(first["text"]),
                "supporting_doc_id": first["doc_id"],
                "supporting_doc_type": first["doc_type"],
            }
        )
    return {str(row["clip_id"]): row for row in rows}


def frame_lookup(frame_index: pd.DataFrame) -> dict[str, dict[str, Any]]:
    return {
        str(row["frame_id"]): {
            "frame_id": row["frame_id"],
            "frame_index": row["frame_index"],
            "timestamp_sec": row["timestamp_sec"],
            "thumbnail_path": row["frame_path"],
            "media_path": row["media_path"],
            "extraction_strategy": row["extraction_strategy"],
        }
        for row in frame_index.to_dict("records")
    }


def representative_frame_by_clip(frame_index: pd.DataFrame) -> dict[str, dict[str, Any]]:
    rows = []
    for clip_id, group in frame_index.sort_values(["clip_id", "frame_seq"], kind="mergesort").groupby("clip_id", sort=False):
        rows.append(group.iloc[len(group) // 2])
    return {
        str(row["clip_id"]): {
            "frame_id": row["frame_id"],
            "frame_index": row["frame_index"],
            "timestamp_sec": row["timestamp_sec"],
            "thumbnail_path": row["frame_path"],
            "media_path": row["media_path"],
            "extraction_strategy": row["extraction_strategy"],
        }
        for row in rows
    }


def make_evidence(
    row: dict[str, Any],
    *,
    frame_id: str | None,
    frames: dict[str, dict[str, Any]],
    representative_frames: dict[str, dict[str, Any]],
    texts: dict[str, dict[str, str]],
    metadata: dict[str, dict[str, str]],
) -> dict[str, Any]:
    clip_id = str(row["clip_id"])
    frame = frames.get(str(frame_id), {}) if frame_id else {}
    frame_source = "retrieved_visual_frame" if frame else None
    if not frame:
        frame = representative_frames.get(clip_id, {})
        frame_source = "fallback_clip_representative" if frame else None
    text = texts.get(clip_id, {})
    return {
        "rank": int(row["rank"]),
        "clip_id": clip_id,
        "frame_id": frame.get("frame_id"),
        "timestamp_sec": frame.get("timestamp_sec"),
        "thumbnail_path": frame.get("thumbnail_path"),
        "media_path": frame.get("media_path"),
        "frame_index": frame.get("frame_index"),
        "frame_source": frame_source,
        "supporting_doc_id": text.get("supporting_doc_id"),
        "supporting_doc_type": text.get("supporting_doc_type"),
        "supporting_text": text.get("supporting_text", ""),
        "metadata": metadata.get(clip_id, {}),
        "scores": {
            "fusion_score": row.get("score"),
            "text_rank": row.get("text_rank"),
            "text_score": row.get("text_score"),
            "visual_rank": row.get("visual_rank"),
            "visual_score": row.get("visual_score"),
        },
        "is_relevant": bool(row.get("is_relevant", False)),
    }


def evidence_context(evidence: list[dict[str, Any]], top_n: int = 3) -> str:
    chunks = []
    for item in evidence[:top_n]:
        chunks.append(
            "rank={rank}; clip={clip}; frame={frame}; time={time}; text={text}".format(
                rank=item["rank"],
                clip=item["clip_id"],
                frame=item.get("frame_id") or "NA",
                time=f"{item.get('timestamp_sec'):.2f}s" if isinstance(item.get("timestamp_sec"), (int, float)) else "NA",
                text=compact_text(item.get("supporting_text"), 260),
            )
        )
    return "\n".join(chunks)


def extractive_answer(request: dict[str, Any], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    top = evidence[0] if evidence else None
    if not top:
        return {
            "answer_type": "evidence_only_template",
            "answer": "No evidence was retrieved.",
            "grounded": True,
            "used_evidence_ranks": [],
        }
    frame_part = ""
    if top.get("timestamp_sec") is not None:
        frame_part = f" The primary evidence frame is at {float(top['timestamp_sec']):.2f} seconds."
    text_part = compact_text(top.get("supporting_text"), 300)
    answer = (
        f"The top retrieved clip is {top['clip_id']}.{frame_part} "
        f"The supporting evidence says: {text_part}"
    ).strip()
    return {
        "answer_type": "evidence_only_template",
        "answer": answer,
        "grounded": True,
        "used_evidence_ranks": [top["rank"]],
    }


def make_text_packets(
    *,
    dataset_name: str,
    queries: pd.DataFrame,
    result_path: Path,
    text_strategy: str,
    top_k: int,
    frames: dict[str, dict[str, Any]],
    representative_frames: dict[str, dict[str, Any]],
    texts: dict[str, dict[str, str]],
    metadata: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results = pd.read_parquet(result_path)
    subset = results[results["strategy"].eq(text_strategy)].sort_values(["query_id", "rank"], kind="mergesort")
    query_map = {str(row["query_id"]): row for row in queries.to_dict("records")}
    packets: list[dict[str, Any]] = []
    flat_rows: list[dict[str, Any]] = []
    for query_id, group in subset.groupby("query_id", sort=False):
        request = query_map.get(str(query_id), {})
        evidence = [
            make_evidence(
                row,
                frame_id=row.get("visual_frame_id"),
                frames=frames,
                representative_frames=representative_frames,
                texts=texts,
                metadata=metadata,
            )
            for row in group.head(top_k).to_dict("records")
        ]
        request_record = {
            "request_id": f"{dataset_name}:text:{query_id}",
            "dataset_name": dataset_name,
            "query_id": query_id,
            "query_type": "text_metadata",
            "query_text": request.get("query_text", ""),
            "metadata_filter": request.get("metadata_filter", {}),
            "strategy": text_strategy,
        }
        packet = {
            "request": request_record,
            "evidence": evidence,
            "answer_context": evidence_context(evidence),
            "extractive_answer": extractive_answer(request_record, evidence),
            "service_contract": {
                "answer_policy": "Evidence-only; no claims outside returned frame/text/metadata evidence.",
                "llm_used": False,
                "vlm_generation_used": False,
            },
        }
        packets.append(packet)
        for item in evidence:
            flat_rows.append({"request_id": request_record["request_id"], "query_type": "text_metadata", **item})
    return packets, flat_rows


def make_image_packets(
    *,
    dataset_name: str,
    image_query_root: Path,
    result_path: Path,
    top_k: int,
    frames: dict[str, dict[str, Any]],
    representative_frames: dict[str, dict[str, Any]],
    texts: dict[str, dict[str, str]],
    metadata: dict[str, dict[str, str]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    queries = pd.read_parquet(image_query_root / "image_queries.parquet")
    query_map = {str(row["query_id"]): row for row in queries.to_dict("records")}
    results = pd.read_parquet(result_path)
    subset = results[results["strategy"].eq(IMAGE_STRATEGY)].sort_values(["query_id", "rank"], kind="mergesort")
    packets: list[dict[str, Any]] = []
    flat_rows: list[dict[str, Any]] = []
    for query_id, group in subset.groupby("query_id", sort=False):
        request = query_map.get(str(query_id), {})
        evidence = [
            make_evidence(
                row,
                frame_id=row.get("frame_id"),
                frames=frames,
                representative_frames=representative_frames,
                texts=texts,
                metadata=metadata,
            )
            for row in group.head(top_k).to_dict("records")
        ]
        request_record = {
            "request_id": f"{dataset_name}:image:{query_id}",
            "dataset_name": dataset_name,
            "query_id": query_id,
            "query_type": "image",
            "query_image_path": request.get("query_frame_path"),
            "query_clip_id": request.get("query_clip_id"),
            "query_frame_id": request.get("query_frame_id"),
            "strategy": IMAGE_STRATEGY,
        }
        packet = {
            "request": request_record,
            "evidence": evidence,
            "answer_context": evidence_context(evidence),
            "extractive_answer": extractive_answer(request_record, evidence),
            "service_contract": {
                "answer_policy": "Evidence-only; no claims outside returned frame/text/metadata evidence.",
                "llm_used": False,
                "vlm_generation_used": False,
            },
        }
        packets.append(packet)
        for item in evidence:
            flat_rows.append({"request_id": request_record["request_id"], "query_type": "image", **item})
    return packets, flat_rows


def summarize(flat_rows: pd.DataFrame, packets: list[dict[str, Any]]) -> pd.DataFrame:
    rows = []
    for query_type, group in flat_rows.groupby("query_type", sort=False):
        requests = group["request_id"].nunique()
        hit_at_k = group.groupby("request_id")["is_relevant"].max().mean()
        top1 = group[group["rank"].eq(1)]
        rows.append(
            {
                "query_type": query_type,
                "requests": int(requests),
                "evidence_rows": int(len(group)),
                "top1_relevant_rate": float(top1["is_relevant"].mean()),
                "hit_at_k": float(hit_at_k),
                "frame_coverage": float(group["frame_id"].notna().mean()),
                "timestamp_coverage": float(group["timestamp_sec"].notna().mean()),
                "supporting_text_coverage": float(group["supporting_text"].astype(str).str.len().gt(0).mean()),
                "relevant_evidence_rate": float(group["is_relevant"].mean()),
            }
        )
    all_top1 = flat_rows[flat_rows["rank"].eq(1)]
    rows.append(
        {
            "query_type": "all",
            "requests": len(packets),
            "evidence_rows": int(len(flat_rows)),
            "top1_relevant_rate": float(all_top1["is_relevant"].mean()),
            "hit_at_k": float(flat_rows.groupby("request_id")["is_relevant"].max().mean()),
            "frame_coverage": float(flat_rows["frame_id"].notna().mean()),
            "timestamp_coverage": float(flat_rows["timestamp_sec"].notna().mean()),
            "supporting_text_coverage": float(flat_rows["supporting_text"].astype(str).str.len().gt(0).mean()),
            "relevant_evidence_rate": float(flat_rows["is_relevant"].mean()),
        }
    )
    return pd.DataFrame(rows)


def write_summary(path: Path, dataset_name: str, summary: pd.DataFrame, top_k: int, packet_count: int) -> None:
    lines = [
        "# Service Testbed Packet Summary",
        "",
        f"created_at: `{datetime.now(timezone.utc).isoformat()}`",
        f"dataset_name: `{dataset_name}`",
        f"top_k: `{top_k}`",
        f"packets: `{packet_count}`",
        "",
        "| query_type | requests | evidence_rows | top1_relevant_rate | hit_at_k | frame_coverage | timestamp_coverage | supporting_text_coverage | relevant_evidence_rate |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        lines.append(
            f"| {row['query_type']} | {row['requests']} | {row['evidence_rows']} | "
            f"{row['top1_relevant_rate']:.4f} | {row['hit_at_k']:.4f} | "
            f"{row['frame_coverage']:.4f} | {row['timestamp_coverage']:.4f} | "
            f"{row['supporting_text_coverage']:.4f} | {row['relevant_evidence_rate']:.4f} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--frame-index-path", type=Path, required=True)
    parser.add_argument("--fusion-result-path", type=Path, required=True)
    parser.add_argument("--image-query-root", type=Path, required=True)
    parser.add_argument("--image-result-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--text-strategy", default=TEXT_STRATEGY)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    _clips, documents, metadata_df, queries, _qrels = load_canonical(args.canonical_root)
    frames = frame_lookup(pd.read_parquet(args.frame_index_path))
    representative_frames = representative_frame_by_clip(pd.read_parquet(args.frame_index_path))
    texts = supporting_text_by_clip(documents)
    metadata = metadata_by_clip(metadata_df)

    text_packets, text_flat = make_text_packets(
        dataset_name=args.dataset_name,
        queries=queries,
        result_path=args.fusion_result_path,
        text_strategy=args.text_strategy,
        top_k=args.top_k,
        frames=frames,
        representative_frames=representative_frames,
        texts=texts,
        metadata=metadata,
    )
    image_packets, image_flat = make_image_packets(
        dataset_name=args.dataset_name,
        image_query_root=args.image_query_root,
        result_path=args.image_result_path,
        top_k=args.top_k,
        frames=frames,
        representative_frames=representative_frames,
        texts=texts,
        metadata=metadata,
    )
    packets = text_packets + image_packets
    flat_rows = pd.DataFrame(text_flat + image_flat)
    summary = summarize(flat_rows, packets)

    write_jsonl(args.output_dir / "service_packets.jsonl", packets)
    flat_rows.to_parquet(args.output_dir / "service_evidence_rows.parquet", index=False)
    summary.to_csv(args.output_dir / "service_packet_summary.csv", index=False)
    write_summary(args.output_dir / "summary.md", args.dataset_name, summary, args.top_k, len(packets))

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "dataset_name": args.dataset_name,
        "canonical_root": str(args.canonical_root),
        "frame_index_path": str(args.frame_index_path),
        "fusion_result_path": str(args.fusion_result_path),
        "image_query_root": str(args.image_query_root),
        "image_result_path": str(args.image_result_path),
        "output_dir": str(args.output_dir),
        "text_strategy": args.text_strategy,
        "image_strategy": IMAGE_STRATEGY,
        "top_k": args.top_k,
        "counts": {
            "packets": len(packets),
            "evidence_rows": int(len(flat_rows)),
            "text_packets": len(text_packets),
            "image_packets": len(image_packets),
        },
        "service_contract": {
            "llm_used": False,
            "vlm_generation_used": False,
            "answer_policy": "Evidence-only extractive answer context.",
        },
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"output_dir={args.output_dir}")
    print(f"dataset_name={args.dataset_name}")
    print(f"packets={len(packets)}")
    print(f"evidence_rows={len(flat_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
