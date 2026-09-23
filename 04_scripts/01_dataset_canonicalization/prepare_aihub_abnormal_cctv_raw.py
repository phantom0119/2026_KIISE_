#!/usr/bin/env python3
"""Prepare AI Hub abnormal behavior CCTV zip files without extracting videos."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "Datasets" / "external" / "이상탐지" / "이상행동 CCTV 영상"
DEFAULT_RAW_ROOT = PROJECT_ROOT / "Datasets" / "raw" / "aihub_abnormal_cctv" / "20260707"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--raw-root", type=Path, default=DEFAULT_RAW_ROOT)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def slug(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9가-힣]+", "_", text).strip("_")


def parse_category(path: Path, source_root: Path) -> dict[str, str]:
    rel_parts = path.relative_to(source_root).parts
    category = rel_parts[0] if rel_parts else ""
    match = re.match(r"(?P<order>\d+)\.(?P<ko>.+)\((?P<en>.+)\)", category)
    if not match:
        return {"category_dir": category, "category_order": "", "event_ko": category, "event_en": ""}
    event_en = match.group("en")
    if event_en == "assult":
        event_en = "assault"
    return {
        "category_dir": category,
        "category_order": match.group("order"),
        "event_ko": match.group("ko"),
        "event_en": event_en,
    }


def make_label_path(label_root: Path, zip_path: Path, source_root: Path, entry_name: str) -> Path:
    zip_rel = zip_path.relative_to(source_root)
    zip_slug = "__".join(slug(part) for part in zip_rel.with_suffix("").parts)
    return label_root / zip_slug / entry_name


def main() -> int:
    args = parse_args()
    source_root = args.source_root
    raw_root = args.raw_root
    labels_root = raw_root / "labels"
    if not source_root.exists():
        print(f"source root does not exist: {source_root}", file=sys.stderr)
        return 2
    if raw_root.exists() and any(raw_root.iterdir()) and not args.overwrite:
        print(f"{raw_root} is not empty. Use --overwrite.", file=sys.stderr)
        return 2
    raw_root.mkdir(parents=True, exist_ok=True)
    labels_root.mkdir(parents=True, exist_ok=True)

    zip_rows: list[dict[str, str | int]] = []
    pair_rows: list[dict[str, str | int]] = []
    entry_rows: list[dict[str, str | int]] = []
    errors: list[dict[str, str]] = []

    for zip_path in sorted(source_root.rglob("*.zip")):
        category = parse_category(zip_path, source_root)
        try:
            with zipfile.ZipFile(zip_path) as archive:
                infos = [info for info in archive.infolist() if not info.is_dir()]
                videos = {Path(info.filename).with_suffix("").as_posix(): info for info in infos if info.filename.lower().endswith(".mp4")}
                labels = {Path(info.filename).with_suffix("").as_posix(): info for info in infos if info.filename.lower().endswith(".xml")}
                zip_rows.append(
                    {
                        "zip_path": str(zip_path),
                        "zip_relpath": str(zip_path.relative_to(source_root)),
                        "zip_size_bytes": zip_path.stat().st_size,
                        "category_dir": category["category_dir"],
                        "category_order": category["category_order"],
                        "event_ko": category["event_ko"],
                        "event_en": category["event_en"],
                        "mp4_entries": len(videos),
                        "xml_entries": len(labels),
                    }
                )
                for info in infos:
                    suffix = Path(info.filename).suffix.lower().lstrip(".")
                    entry_rows.append(
                        {
                            "zip_path": str(zip_path),
                            "zip_relpath": str(zip_path.relative_to(source_root)),
                            "entry_name": info.filename,
                            "suffix": suffix,
                            "entry_size_bytes": info.file_size,
                            "category_dir": category["category_dir"],
                            "event_ko": category["event_ko"],
                            "event_en": category["event_en"],
                        }
                    )
                for stem, video_info in sorted(videos.items()):
                    label_info = labels.get(stem)
                    label_path = ""
                    if label_info is not None:
                        label_target = make_label_path(labels_root, zip_path, source_root, label_info.filename)
                        label_target.parent.mkdir(parents=True, exist_ok=True)
                        if args.overwrite or not label_target.exists():
                            label_target.write_bytes(archive.read(label_info))
                        label_path = str(label_target)
                    video_name = Path(video_info.filename).name
                    clip_stem = Path(video_name).stem
                    clip_id = f"aihub_abnormal_cctv:{slug(clip_stem)}"
                    pair_rows.append(
                        {
                            "clip_id": clip_id,
                            "dataset_id": "aihub_abnormal_cctv",
                            "split": "all",
                            "category_dir": category["category_dir"],
                            "category_order": category["category_order"],
                            "event_ko": category["event_ko"],
                            "event_en": category["event_en"],
                            "file_stem": clip_stem,
                            "file_name": video_name,
                            "media_uri": f"zip://{zip_path}!{video_info.filename}",
                            "media_zip_path": str(zip_path),
                            "media_entry": video_info.filename,
                            "media_size_bytes": video_info.file_size,
                            "label_path": label_path,
                            "label_entry": label_info.filename if label_info is not None else "",
                            "label_exists": bool(label_info),
                        }
                    )
                for stem, label_info in sorted(labels.items()):
                    if stem in videos:
                        continue
                    label_target = make_label_path(labels_root, zip_path, source_root, label_info.filename)
                    label_target.parent.mkdir(parents=True, exist_ok=True)
                    if args.overwrite or not label_target.exists():
                        label_target.write_bytes(archive.read(label_info))
                    errors.append(
                        {
                            "zip_path": str(zip_path),
                            "entry_name": label_info.filename,
                            "error": "xml_without_matching_mp4",
                        }
                    )
        except Exception as exc:
            errors.append({"zip_path": str(zip_path), "entry_name": "", "error": f"{type(exc).__name__}: {exc}"})

    def write_csv(path: Path, rows: list[dict[str, str | int]]) -> None:
        if not rows:
            path.write_text("", encoding="utf-8")
            return
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    write_csv(raw_root / "zip_manifest.csv", zip_rows)
    write_csv(raw_root / "zip_entries.csv", entry_rows)
    write_csv(raw_root / "clip_pairs.csv", pair_rows)
    write_csv(raw_root / "prepare_errors.csv", errors)

    summary = {
        "dataset_id": "aihub_abnormal_cctv",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(source_root),
        "raw_root": str(raw_root),
        "zip_count": len(zip_rows),
        "zip_bytes": sum(int(row["zip_size_bytes"]) for row in zip_rows),
        "entry_count": len(entry_rows),
        "mp4_entries": sum(int(row["mp4_entries"]) for row in zip_rows),
        "xml_entries": sum(int(row["xml_entries"]) for row in zip_rows),
        "paired_clips": len(pair_rows),
        "pairs_with_label": sum(1 for row in pair_rows if row["label_exists"]),
        "errors": len(errors),
        "strategy": "Videos remain inside source zip files; XML labels are extracted for canonical conversion.",
    }
    (raw_root / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# AI Hub Abnormal CCTV Raw Preparation",
        "",
        f"created_at: `{summary['created_at']}`",
        f"source_root: `{source_root}`",
        f"raw_root: `{raw_root}`",
        "",
        "| item | count |",
        "|---|---:|",
        f"| zip files | {summary['zip_count']} |",
        f"| zip bytes | {summary['zip_bytes']} |",
        f"| entries | {summary['entry_count']} |",
        f"| mp4 entries | {summary['mp4_entries']} |",
        f"| xml entries | {summary['xml_entries']} |",
        f"| paired clips | {summary['paired_clips']} |",
        f"| pairs with label | {summary['pairs_with_label']} |",
        f"| errors | {summary['errors']} |",
        "",
        "Videos are referenced as `zip://...!entry` URIs and are not extracted.",
    ]
    (raw_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
