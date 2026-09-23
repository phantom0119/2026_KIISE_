#!/usr/bin/env python3
"""Materialize AI Hub 71953 evidence frames from zip-stored mp4 videos."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import cv2
import pandas as pd


def safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:180]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-events", type=int, default=None)
    parser.add_argument("--clip-ids-file", type=Path, default=None)
    parser.add_argument("--max-frames-per-view", type=int, default=3)
    parser.add_argument("--image-size", type=int, default=512)
    parser.add_argument("--jpeg-quality", type=int, default=90)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def load_video_to_temp(source_zip_path: str, media_entry: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(prefix="aihub71953_", suffix=".mp4", delete=False)
    tmp_path = Path(tmp.name)
    try:
        with ZipFile(source_zip_path) as zf, zf.open(media_entry) as src:
            while True:
                chunk = src.read(1024 * 1024)
                if not chunk:
                    break
                tmp.write(chunk)
    finally:
        tmp.close()
    return tmp_path


def extract_frame(
    video_path: Path,
    frame_index: int,
    frame_path: Path,
    *,
    image_size: int,
    jpeg_quality: int,
) -> tuple[dict[str, Any] | None, str | None]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return None, "opencv_open_failed"
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    if frame_count <= 0:
        cap.release()
        return None, "empty_video"
    pos = max(0, min(int(frame_index), frame_count - 1))
    cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
    ok, frame = cap.read()
    cap.release()
    if not ok or frame is None:
        return None, "frame_read_failed"
    height, width = frame.shape[:2]
    scale = image_size / max(height, width) if image_size > 0 else 1.0
    if 0 < scale < 1.0:
        frame = cv2.resize(frame, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)
    frame_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(frame_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
    return {
        "original_width": width,
        "original_height": height,
        "fps": fps,
        "frame_count": frame_count,
        "timestamp_sec": float(pos / fps) if fps > 0 else None,
        "frame_index": pos,
    }, None


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    if args.output_dir.exists() and args.overwrite:
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    evidence = pd.read_parquet(args.canonical_root / "evidence_frames.parquet")
    if args.clip_ids_file is not None:
        clip_ids = {
            line.strip()
            for line in args.clip_ids_file.read_text(encoding="utf-8").splitlines()
            if line.strip()
        }
        evidence = evidence[evidence["clip_id"].astype(str).isin(clip_ids)]
    if args.max_events is not None:
        event_ids = evidence["clip_id"].drop_duplicates().head(args.max_events)
        evidence = evidence[evidence["clip_id"].isin(set(event_ids))]

    evidence = (
        evidence.sort_values(["clip_id", "view", "frame_seq"], kind="mergesort")
        .groupby(["clip_id", "view"], sort=False)
        .head(args.max_frames_per_view)
        .drop_duplicates(["clip_id", "view", "frame_index"])
        .reset_index(drop=True)
    )

    frame_dir = args.output_dir / "frames"
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    grouped = evidence.groupby(["source_zip_path", "media_entry"], sort=False)
    for (source_zip_path, media_entry), group in grouped:
        video_path: Path | None = None
        try:
            video_path = load_video_to_temp(str(source_zip_path), str(media_entry))
            for _, row in group.iterrows():
                clip_id = str(row["clip_id"])
                view = str(row["view"])
                frame_index = int(row["frame_index"])
                view_frame_seq = int(row["frame_seq"])
                frame_id = f"{safe_slug(clip_id)}:{view}:ef{view_frame_seq:02d}"
                frame_path = frame_dir / safe_slug(clip_id) / view / f"ef{view_frame_seq:02d}_f{frame_index:06d}.jpg"
                meta, error = extract_frame(
                    video_path,
                    frame_index,
                    frame_path,
                    image_size=args.image_size,
                    jpeg_quality=args.jpeg_quality,
                )
                if error:
                    errors.append({**row.to_dict(), "error": error})
                    continue
                assert meta is not None
                records.append(
                    {
                        "frame_id": frame_id,
                        "clip_id": clip_id,
                        "dataset_id": row["dataset_id"],
                        "source_split": row["source_split"],
                        "view": view,
                        "frame_seq": len(records),
                        "view_frame_seq": view_frame_seq,
                        "frame_index": meta["frame_index"],
                        "timestamp_sec": meta["timestamp_sec"],
                        "frame_path": str(frame_path),
                        "media_path": row["media_path"],
                        "extraction_strategy": "label_evidence_frame",
                        "original_width": meta["original_width"],
                        "original_height": meta["original_height"],
                        "fps": meta["fps"],
                        "frame_count": meta["frame_count"],
                        "obj_id": row.get("obj_id", ""),
                        "obj_label": row.get("obj_label", ""),
                        "bbox_x1": row.get("bbox_x1"),
                        "bbox_y1": row.get("bbox_y1"),
                        "bbox_x2": row.get("bbox_x2"),
                        "bbox_y2": row.get("bbox_y2"),
                        "evidence_text": row.get("evidence_text", ""),
                    }
                )
        except Exception as exc:
            for _, row in group.iterrows():
                errors.append({**row.to_dict(), "error": f"video_group_failed:{type(exc).__name__}:{exc}"})
        finally:
            if video_path is not None:
                try:
                    video_path.unlink(missing_ok=True)
                except Exception:
                    pass

    frames = pd.DataFrame(records)
    errors_df = pd.DataFrame(errors)
    frames.to_parquet(args.output_dir / "frames.parquet", index=False)
    errors_df.to_csv(args.output_dir / "frame_extract_errors.csv", index=False)

    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "output_dir": str(args.output_dir),
        "max_events": args.max_events,
        "clip_ids_file": str(args.clip_ids_file) if args.clip_ids_file else None,
        "max_frames_per_view": args.max_frames_per_view,
        "image_size": args.image_size,
        "evidence_rows_seen": int(len(evidence)),
        "clips_with_frames": int(frames["clip_id"].nunique()) if not frames.empty else 0,
        "views_with_frames": int(frames[["clip_id", "view"]].drop_duplicates().shape[0]) if not frames.empty else 0,
        "frames": int(len(frames)),
        "errors": int(len(errors_df)),
    }
    (args.output_dir / "frame_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "summary.md").write_text(
        "\n".join(
            [
                "# AI Hub 71953 Evidence Frame Materialization Summary",
                "",
                f"created_at: `{summary['created_at']}`",
                f"canonical_root: `{summary['canonical_root']}`",
                "",
                "| item | value |",
                "|---|---:|",
                f"| evidence_rows_seen | {summary['evidence_rows_seen']} |",
                f"| clips_with_frames | {summary['clips_with_frames']} |",
                f"| views_with_frames | {summary['views_with_frames']} |",
                f"| frames | {summary['frames']} |",
                f"| errors | {summary['errors']} |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"output_dir={args.output_dir}")
    print(f"clips_with_frames={summary['clips_with_frames']}")
    print(f"views_with_frames={summary['views_with_frames']}")
    print(f"frames={summary['frames']}")
    print(f"errors={summary['errors']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
