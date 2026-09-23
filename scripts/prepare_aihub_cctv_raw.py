#!/usr/bin/env python3
"""Prepare AI Hub intelligent CCTV zip files for local experiments."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from zipfile import BadZipFile, ZipFile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCE_ROOT = PROJECT_ROOT / "Datasets/external/지능형관제서비스CCTV영상데이터"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "Datasets/raw/aihub_intelligent_cctv/20260706"

EVENT_SLUGS = {
    "군집": "crowd",
    "싸움": "fight",
    "쓰러짐": "fall",
    "침입": "intrusion",
    "인파밀집_할로윈데이 1주전_금": "crowd_density_halloween_minus1_fri",
    "인파밀집_할로윈데이 1주전_토": "crowd_density_halloween_minus1_sat",
    "인파밀집_할로윈데이 포함_목": "crowd_density_halloween_week_thu",
    "인파밀집_할로윈데이 포함_금": "crowd_density_halloween_week_fri",
    "인파밀집_할로윈데이 포함_일": "crowd_density_halloween_week_sun",
    "침수_0단계_골목길": "flood_level0_alley",
    "침수_0단계_교차로": "flood_level0_intersection",
    "침수_0단계_대로": "flood_level0_road",
    "침수_1단계_골목길": "flood_level1_alley",
    "침수_1단계_교차로": "flood_level1_intersection",
    "침수_1단계_기타": "flood_level1_other",
    "침수_1단계_대로": "flood_level1_road",
    "침수_2단계_골목길": "flood_level2_alley",
}


@dataclass
class FileEntry:
    split: str
    data_kind: str
    event_name: str
    event_slug: str
    zip_path: str
    member_name: str
    file_name: str
    output_path: str
    file_size: int
    status: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--inventory-only", action="store_true")
    return parser.parse_args()


def slug_for_event(event_name: str) -> str:
    if event_name in EVENT_SLUGS:
        return EVENT_SLUGS[event_name]
    digest = hashlib.sha1(event_name.encode("utf-8")).hexdigest()[:8]
    return f"event_{digest}"


def zip_context(zip_path: Path, source_root: Path) -> tuple[str, str, str, str]:
    rel_parts = zip_path.relative_to(source_root).parts
    if len(rel_parts) < 3:
        raise ValueError(f"Unexpected zip layout: {zip_path}")

    split_raw = rel_parts[0]
    data_raw = rel_parts[1]
    stem = zip_path.stem
    prefix, _, event_name = stem.partition("_")
    if not event_name:
        raise ValueError(f"Unexpected zip name: {zip_path.name}")

    split = {"Training": "train", "Validation": "val"}.get(split_raw)
    if split is None:
        raise ValueError(f"Unexpected split: {split_raw}")

    if "원천" in data_raw:
        data_kind = "media"
    elif "라벨" in data_raw:
        data_kind = "labels"
    else:
        raise ValueError(f"Unexpected data kind: {data_raw}")

    expected_prefixes = {
        ("train", "media"): "TS",
        ("train", "labels"): "TL",
        ("val", "media"): "VS",
        ("val", "labels"): "VL",
    }
    expected_prefix = expected_prefixes[(split, data_kind)]
    if prefix != expected_prefix:
        raise ValueError(f"Unexpected zip prefix {prefix}; expected {expected_prefix}: {zip_path}")

    return split, data_kind, event_name, slug_for_event(event_name)


def safe_member_name(member_name: str) -> str:
    name = Path(member_name).name
    if not name or name in {".", ".."}:
        raise ValueError(f"Unsafe member name: {member_name}")
    return name


def iter_zip_files(source_root: Path) -> list[Path]:
    return sorted(source_root.rglob("*.zip"))


def extract_member(zip_file: ZipFile, member_name: str, output_path: Path, overwrite: bool) -> str:
    if output_path.exists() and not overwrite:
        return "exists"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = output_path.with_suffix(output_path.suffix + ".tmp")
    with zip_file.open(member_name) as source, tmp_path.open("wb") as target:
        shutil.copyfileobj(source, target, length=1024 * 1024)
    tmp_path.replace(output_path)
    return "written"


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_pair_rows(entries: list[FileEntry]) -> list[dict]:
    grouped: dict[tuple[str, str, str], dict[str, FileEntry]] = defaultdict(dict)
    for entry in entries:
        stem = Path(entry.file_name).stem
        grouped[(entry.split, entry.event_slug, stem)][entry.data_kind] = entry

    rows = []
    for (split, event_slug, stem), item in sorted(grouped.items()):
        media_entry = item.get("media")
        label_entry = item.get("labels")
        event_name = (media_entry or label_entry).event_name
        rows.append(
            {
                "clip_id": f"aihub_cctv:{split}:{event_slug}:{stem}",
                "split": split,
                "event_slug": event_slug,
                "event_name": event_name,
                "file_stem": stem,
                "media_path": media_entry.output_path if media_entry else "",
                "label_path": label_entry.output_path if label_entry else "",
                "has_media": bool(media_entry),
                "has_label": bool(label_entry),
            }
        )
    return rows


def write_summary(path: Path, summary: dict, pair_rows: list[dict]) -> None:
    split_counts = Counter(row["split"] for row in pair_rows)
    event_counts = Counter((row["split"], row["event_slug"]) for row in pair_rows)
    lines = [
        "# AI Hub Intelligent CCTV Raw Preparation Summary",
        "",
        f"created_at: `{summary['created_at']}`",
        f"source_root: `{summary['source_root']}`",
        f"output_root: `{summary['output_root']}`",
        "",
        "## Counts",
        "",
        "| item | count |",
        "|---|---:|",
        f"| zip files | {summary['zip_files']} |",
        f"| media files | {summary['media_files']} |",
        f"| label files | {summary['label_files']} |",
        f"| paired clips | {summary['paired_clips']} |",
        f"| missing media | {summary['missing_media']} |",
        f"| missing labels | {summary['missing_labels']} |",
        "",
        "## Split Counts",
        "",
        "| split | clips |",
        "|---|---:|",
    ]
    for split, count in sorted(split_counts.items()):
        lines.append(f"| {split} | {count} |")

    lines.extend(["", "## Event Counts", "", "| split | event | clips |", "|---|---|---:|"])
    for (split, event_slug), count in sorted(event_counts.items()):
        event_name = next(
            row["event_name"]
            for row in pair_rows
            if row["split"] == split and row["event_slug"] == event_slug
        )
        lines.append(f"| {split} | {event_slug} ({event_name}) | {count} |")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    source_root = args.source_root.resolve()
    output_root = args.output_root.resolve()

    if not source_root.exists():
        raise FileNotFoundError(source_root)

    entries: list[FileEntry] = []
    zip_errors: list[dict] = []
    for zip_path in iter_zip_files(source_root):
        try:
            split, data_kind, event_name, event_slug = zip_context(zip_path, source_root)
            expected_suffix = ".mp4" if data_kind == "media" else ".json"
            with ZipFile(zip_path) as archive:
                for info in archive.infolist():
                    if info.is_dir():
                        continue
                    file_name = safe_member_name(info.filename)
                    if Path(file_name).suffix.lower() != expected_suffix:
                        raise ValueError(f"Unexpected member suffix in {zip_path}: {info.filename}")
                    output_path = output_root / data_kind / split / event_slug / file_name
                    status = "inventory"
                    if not args.inventory_only:
                        status = extract_member(archive, info.filename, output_path, args.overwrite)
                    entries.append(
                        FileEntry(
                            split=split,
                            data_kind=data_kind,
                            event_name=event_name,
                            event_slug=event_slug,
                            zip_path=str(zip_path),
                            member_name=info.filename,
                            file_name=file_name,
                            output_path=str(output_path),
                            file_size=info.file_size,
                            status=status,
                        )
                    )
        except (BadZipFile, ValueError) as exc:
            zip_errors.append({"zip_path": str(zip_path), "error": str(exc)})

    output_root.mkdir(parents=True, exist_ok=True)
    entry_rows = [asdict(entry) for entry in entries]
    pair_rows = build_pair_rows(entries)
    missing_media = sum(1 for row in pair_rows if not row["has_media"])
    missing_labels = sum(1 for row in pair_rows if not row["has_label"])
    summary = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(source_root),
        "output_root": str(output_root),
        "zip_files": len(iter_zip_files(source_root)),
        "zip_errors": zip_errors,
        "media_files": sum(1 for entry in entries if entry.data_kind == "media"),
        "label_files": sum(1 for entry in entries if entry.data_kind == "labels"),
        "paired_clips": sum(1 for row in pair_rows if row["has_media"] and row["has_label"]),
        "missing_media": missing_media,
        "missing_labels": missing_labels,
        "inventory_only": args.inventory_only,
    }

    write_json(output_root / "manifest.json", summary)
    write_jsonl(output_root / "file_manifest.jsonl", entry_rows)
    write_csv(
        output_root / "clip_pairs.csv",
        pair_rows,
        [
            "clip_id",
            "split",
            "event_slug",
            "event_name",
            "file_stem",
            "media_path",
            "label_path",
            "has_media",
            "has_label",
        ],
    )
    write_summary(output_root / "summary.md", summary, pair_rows)

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
