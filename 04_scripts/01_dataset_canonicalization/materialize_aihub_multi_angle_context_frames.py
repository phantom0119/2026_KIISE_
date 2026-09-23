#!/usr/bin/env python3
"""Materialize context distractor frames for AI Hub 71953 evidence-selection tasks."""

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
import numpy as np
import pandas as pd


def safe_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")[:180]


def load_video_to_temp(source_zip_path: str, media_entry: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(prefix="aihub71953_ctx_", suffix=".mp4", delete=False)
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


def video_info(video_path: Path) -> tuple[int, float]:
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        return 0, 0.0
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
    cap.release()
    return frame_count, fps


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


def select_context_indices(frame_count: int, positive_indices: list[int], count: int, min_gap: int) -> list[int]:
    if frame_count <= 0 or count <= 0:
        return []
    positives = [idx for idx in positive_indices if idx is not None]
    selected: list[int] = []
    candidate_count = max(count * 8, 16)
    candidates = np.linspace(0.03, 0.97, candidate_count)
    for value in candidates:
        idx = int(round(float(value) * (frame_count - 1)))
        if idx in selected:
            continue
        if any(abs(idx - pos) <= min_gap for pos in positives):
            continue
        selected.append(idx)
        if len(selected) >= count:
            return selected
    for idx in np.linspace(0, frame_count - 1, candidate_count * 2):
        pos = int(round(float(idx)))
        if pos in selected:
            continue
        if any(abs(pos - positive) <= max(1, min_gap // 2) for positive in positives):
            continue
        selected.append(pos)
        if len(selected) >= count:
            break
    return selected


def add_grounding_columns(frames: pd.DataFrame, clips: pd.DataFrame) -> pd.DataFrame:
    clip_cols = clips[["clip_id", "event_class", "event_group", "category"]].copy()
    out = frames.merge(clip_cols, on="clip_id", how="left")
    out["is_label_evidence"] = out["extraction_strategy"].eq("label_evidence_frame")
    out["grounding_relevance"] = out["is_label_evidence"].astype(int)
    return out


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--evidence-frame-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--context-frames-per-view", type=int, default=4)
    parser.add_argument("--min-gap-frames", type=int, default=30)
    parser.add_argument("--image-size", type=int, default=512)
    parser.add_argument("--jpeg-quality", type=int, default=90)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    if args.output_dir.exists() and args.overwrite:
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    clips = pd.read_parquet(args.canonical_root / "clips.parquet")
    views = pd.read_parquet(args.canonical_root / "views.parquet")
    positives = pd.read_parquet(args.evidence_frame_root / "frames.parquet")
    positives = add_grounding_columns(positives, clips)
    clip_ids = set(positives["clip_id"].astype(str).unique().tolist())
    views = views[views["clip_id"].astype(str).isin(clip_ids)].copy()

    positive_by_clip_view = {
        (str(clip_id), str(view)): group["frame_index"].dropna().astype(int).tolist()
        for (clip_id, view), group in positives.groupby(["clip_id", "view"], sort=False)
    }

    frame_dir = args.output_dir / "frames"
    context_records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []

    for _, view in views.sort_values(["clip_id", "view"], kind="mergesort").iterrows():
        video_path: Path | None = None
        try:
            video_path = load_video_to_temp(str(view["source_zip_path"]), str(view["media_entry"]))
            frame_count, _fps = video_info(video_path)
            positives_for_view = positive_by_clip_view.get((str(view["clip_id"]), str(view["view"])), [])
            indices = select_context_indices(
                frame_count,
                positives_for_view,
                args.context_frames_per_view,
                args.min_gap_frames,
            )
            for seq, frame_index in enumerate(indices):
                clip_id = str(view["clip_id"])
                view_name = str(view["view"])
                frame_id = f"{safe_slug(clip_id)}:{view_name}:ctx{seq:02d}"
                frame_path = frame_dir / safe_slug(clip_id) / view_name / f"ctx{seq:02d}_f{frame_index:06d}.jpg"
                meta, error = extract_frame(
                    video_path,
                    frame_index,
                    frame_path,
                    image_size=args.image_size,
                    jpeg_quality=args.jpeg_quality,
                )
                if error:
                    errors.append({**view.to_dict(), "frame_index": frame_index, "error": error})
                    continue
                assert meta is not None
                context_records.append(
                    {
                        "frame_id": frame_id,
                        "clip_id": clip_id,
                        "dataset_id": view["dataset_id"],
                        "source_split": view["source_split"],
                        "view": view_name,
                        "frame_seq": len(context_records),
                        "view_frame_seq": seq,
                        "frame_index": meta["frame_index"],
                        "timestamp_sec": meta["timestamp_sec"],
                        "frame_path": str(frame_path),
                        "media_path": view["media_path"],
                        "extraction_strategy": "context_distractor_frame",
                        "original_width": meta["original_width"],
                        "original_height": meta["original_height"],
                        "fps": meta["fps"],
                        "frame_count": meta["frame_count"],
                        "obj_id": "",
                        "obj_label": "",
                        "bbox_x1": None,
                        "bbox_y1": None,
                        "bbox_x2": None,
                        "bbox_y2": None,
                        "evidence_text": "동일 clip에서 추출한 문맥 distractor frame이며 라벨 근거 bbox가 없다.",
                    }
                )
        except Exception as exc:
            errors.append({**view.to_dict(), "error": f"video_group_failed:{type(exc).__name__}:{exc}"})
        finally:
            if video_path is not None:
                try:
                    video_path.unlink(missing_ok=True)
                except Exception:
                    pass

    context = pd.DataFrame(context_records)
    if not context.empty:
        context = add_grounding_columns(context, clips)
    frames = pd.concat([positives, context], ignore_index=True, sort=False)
    frames = frames.sort_values(
        ["clip_id", "view", "extraction_strategy", "frame_index", "frame_id"],
        kind="mergesort",
    ).reset_index(drop=True)
    frames["frame_seq"] = range(len(frames))

    frames.to_parquet(args.output_dir / "frames.parquet", index=False)
    pd.DataFrame(errors).to_csv(args.output_dir / "frame_extract_errors.csv", index=False)

    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "evidence_frame_root": str(args.evidence_frame_root),
        "output_dir": str(args.output_dir),
        "context_frames_per_view": args.context_frames_per_view,
        "min_gap_frames": args.min_gap_frames,
        "positive_frames": int(len(positives)),
        "context_frames": int(len(context)),
        "total_frames": int(len(frames)),
        "clips": int(frames["clip_id"].nunique()) if not frames.empty else 0,
        "views": int(frames[["clip_id", "view"]].drop_duplicates().shape[0]) if not frames.empty else 0,
        "errors": int(len(errors)),
    }
    (args.output_dir / "frame_manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# AI Hub 71953 Evidence + Context Frame Summary",
        "",
        f"created_at: `{summary['created_at']}`",
        "",
        "| item | value |",
        "|---|---:|",
        f"| positive_frames | {summary['positive_frames']} |",
        f"| context_frames | {summary['context_frames']} |",
        f"| total_frames | {summary['total_frames']} |",
        f"| clips | {summary['clips']} |",
        f"| views | {summary['views']} |",
        f"| errors | {summary['errors']} |",
    ]
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"output_dir={args.output_dir}")
    print(f"positive_frames={summary['positive_frames']}")
    print(f"context_frames={summary['context_frames']}")
    print(f"total_frames={summary['total_frames']}")
    print(f"errors={summary['errors']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
