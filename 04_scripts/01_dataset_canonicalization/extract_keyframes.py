#!/usr/bin/env python3
"""Extract keyframes for true multimodal retrieval experiments."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:180]


def frame_positions(row: pd.Series, frame_count: int, frames_per_clip: int, strategy: str) -> list[int]:
    if frame_count <= 0:
        return []

    start = 0
    end = frame_count - 1
    if strategy == "event" and {"event_start_frame", "event_end_frame"}.issubset(row.index):
        try:
            event_start = int(row.get("event_start_frame"))
            event_end = int(row.get("event_end_frame"))
            if event_end > event_start >= 0:
                start = max(0, min(event_start, frame_count - 1))
                end = max(start, min(event_end, frame_count - 1))
        except Exception:
            pass

    if frames_per_clip <= 1:
        return [(start + end) // 2]

    span = max(1, end - start)
    positions = [round(start + (span * i / (frames_per_clip - 1))) for i in range(frames_per_clip)]
    return sorted({max(0, min(int(pos), frame_count - 1)) for pos in positions})


def extract_frames_for_clip(
    row: pd.Series,
    output_frame_dir: Path,
    frames_per_clip: int,
    strategy: str,
    image_size: int,
    jpeg_quality: int,
) -> tuple[list[dict[str, Any]], str | None]:
    media_path = str(row.get("media_path", ""))
    if media_path.startswith("zip://"):
        return [], "zip_media_not_supported_in_fast_path"

    path = Path(media_path)
    if not path.exists():
        return [], "media_missing"

    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return [], "opencv_open_failed"

    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    positions = frame_positions(row, frame_count, frames_per_clip, strategy)
    if not positions:
        cap.release()
        return [], "no_frame_positions"

    clip_id = str(row["clip_id"])
    clip_dir = output_frame_dir / safe_slug(clip_id)
    clip_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    for seq, pos in enumerate(positions):
        cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
        ok, frame = cap.read()
        if not ok or frame is None:
            continue

        height, width = frame.shape[:2]
        scale = image_size / max(height, width) if image_size > 0 else 1.0
        if 0 < scale < 1.0:
            frame = cv2.resize(frame, (int(width * scale), int(height * scale)), interpolation=cv2.INTER_AREA)

        frame_id = f"{safe_slug(clip_id)}:kf{seq:02d}"
        frame_path = clip_dir / f"kf{seq:02d}_f{pos:06d}.jpg"
        cv2.imwrite(str(frame_path), frame, [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality])
        timestamp = float(pos / fps) if fps > 0 else None
        records.append(
            {
                "frame_id": frame_id,
                "clip_id": clip_id,
                "dataset_id": row.get("dataset_id"),
                "source_split": row.get("source_split"),
                "frame_seq": seq,
                "frame_index": pos,
                "timestamp_sec": timestamp,
                "frame_path": str(frame_path),
                "media_path": media_path,
                "extraction_strategy": strategy,
                "original_width": width,
                "original_height": height,
                "fps": fps,
                "frame_count": frame_count,
            }
        )

    cap.release()
    if not records:
        return [], "frame_read_failed"
    return records, None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--frames-per-clip", type=int, default=4)
    parser.add_argument("--strategy", choices=["uniform", "event"], default="uniform")
    parser.add_argument("--image-size", type=int, default=512)
    parser.add_argument("--jpeg-quality", type=int, default=90)
    parser.add_argument("--max-clips", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    clips = pd.read_parquet(args.canonical_root / "clips.parquet")
    if args.max_clips:
        clips = clips.head(args.max_clips)

    frame_dir = args.output_dir / "frames"
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for _, row in clips.iterrows():
        clip_records, error = extract_frames_for_clip(
            row,
            frame_dir,
            frames_per_clip=args.frames_per_clip,
            strategy=args.strategy,
            image_size=args.image_size,
            jpeg_quality=args.jpeg_quality,
        )
        records.extend(clip_records)
        if error:
            errors.append({"clip_id": row.get("clip_id"), "media_path": row.get("media_path"), "error": error})

    frames = pd.DataFrame(records)
    errors_df = pd.DataFrame(errors)
    frames.to_parquet(args.output_dir / "frames.parquet", index=False)
    errors_df.to_csv(args.output_dir / "frame_extract_errors.csv", index=False)

    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "output_dir": str(args.output_dir),
        "frames_per_clip": args.frames_per_clip,
        "strategy": args.strategy,
        "image_size": args.image_size,
        "clips_seen": int(len(clips)),
        "clips_with_frames": int(frames["clip_id"].nunique()) if not frames.empty else 0,
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
                "# Keyframe Extraction Summary",
                "",
                f"created_at: `{summary['created_at']}`",
                f"canonical_root: `{summary['canonical_root']}`",
                "",
                "| item | value |",
                "|---|---:|",
                f"| clips_seen | {summary['clips_seen']} |",
                f"| clips_with_frames | {summary['clips_with_frames']} |",
                f"| frames | {summary['frames']} |",
                f"| errors | {summary['errors']} |",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    print(f"output_dir={args.output_dir}")
    print(f"clips_seen={summary['clips_seen']}")
    print(f"clips_with_frames={summary['clips_with_frames']}")
    print(f"frames={summary['frames']}")
    print(f"errors={summary['errors']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
