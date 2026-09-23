#!/usr/bin/env python3
"""Phase 2 unblock (T1 follow-through): one-pass extraction of 522 visual sources.

TS_3/VS_3 '도로차량' archives are solid 7z (LZMA2; .zip extension is a misnomer)
holding PRE-EXTRACTED JPG frames (~3 frames/video), NOT mp4 — so no video
decoding is ever needed. T1 probe measured block-seek extraction at
2.6s/7.6s/80.8s per 30 files (head/mid/tail), so a full sequential pass
(~70.7 GiB train + 8.9 GiB val) is the cheapest way to unblock Pillars A/C/D
at once. Disk: /hdd2 has ~1.3 TB free.

Also extracts the small label archives TL_3/TL_4/TL_5 (+VL_*) — CVAT XMLs with
road-vehicle annotations and the 악천후/시간대 environment categories.

Outputs under Datasets/processed/aihub_522_intersection/<ver>/:
  frames_src/{train,val}/<cam>/<task>/<video_id>_<frame>.jpg   (verbatim source)
  labels_src/{train,val}/{TL_3,TL_4,TL_5}/...                  (verbatim XMLs)
  extract_manifest.json

Run (background; ~30-60 min for train):
  Datasets/envs/kiise-vlmdb/bin/python \
    2026_KIISE/scripts/extract_intersection_visual_sources.py [--only train|val|labels]
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import py7zr

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DS = PROJECT_ROOT / "Datasets"
EXT = DS / "external" / "교차로신호체계"
OUT = DS / "processed" / "aihub_522_intersection" / "20260710"

FRAME_ARCHIVES = {
    "train": EXT / "1.Training" / "원천데이터" / "TS_3.도로차량.zip",
    "val": EXT / "2.Validation" / "원천데이터" / "VS_3.도로차량.zip",
}
# TS_4/VS_4 hold the frames referenced by the 악천후(bad-weather)/시간대(time-slot)
# TL_4 annotation categories — absent from TS_3/VS_3 (verified: 0 overlap).
BBOX_FRAME_ARCHIVES = {
    "train_bbox": EXT / "1.Training" / "원천데이터" / "TS_4.바운딩박스.zip",
    "val_bbox": EXT / "2.Validation" / "원천데이터" / "VS_4.바운딩박스.zip",
}
LABEL_ARCHIVES = {
    ("train", "TL_3"): EXT / "1.Training" / "라벨링데이터" / "TL_3.도로차량.zip",
    ("train", "TL_4"): EXT / "1.Training" / "라벨링데이터" / "TL_4.바운딩박스.zip",
    ("train", "TL_5"): EXT / "1.Training" / "라벨링데이터" / "TL_5.큐보이드.zip",
    ("val", "VL_3"): EXT / "2.Validation" / "라벨링데이터" / "VL_3.도로차량.zip",
    ("val", "VL_4"): EXT / "2.Validation" / "라벨링데이터" / "VL_4.바운딩박스.zip",
    ("val", "VL_5"): EXT / "2.Validation" / "라벨링데이터" / "VL_5.큐보이드.zip",
}


def extract_all(archive: Path, dest: Path) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    with py7zr.SevenZipFile(archive, "r") as z:
        info = z.archiveinfo()
        z.extractall(path=dest)
    dt = time.time() - t0
    n_files = sum(1 for p in dest.rglob("*") if p.is_file())
    return {"archive": str(archive), "dest": str(dest), "solid": info.solid,
            "blocks": info.blocks, "uncompressed_gib": round(info.uncompressed / 2**30, 2),
            "wall_sec": round(dt, 1), "files_on_disk": n_files}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", choices=["train", "val", "labels", "bbox"], default=None)
    args = ap.parse_args()

    manifest = {"created_at": datetime.now(timezone.utc).isoformat(), "jobs": []}
    jobs: list[tuple[str, Path, Path]] = []
    if args.only in (None, "labels"):
        for (split, tag), arch in LABEL_ARCHIVES.items():
            jobs.append((f"labels/{split}/{tag}", arch, OUT / "labels_src" / split / tag))
    if args.only in (None, "val"):
        jobs.append(("frames/val", FRAME_ARCHIVES["val"], OUT / "frames_src" / "val"))
    if args.only in (None, "train"):
        jobs.append(("frames/train", FRAME_ARCHIVES["train"], OUT / "frames_src" / "train"))
    if args.only == "bbox":  # weather/time-category frames; run AFTER the main pass
        jobs.append(("frames/val_bbox", BBOX_FRAME_ARCHIVES["val_bbox"], OUT / "frames_src" / "val_bbox"))
        jobs.append(("frames/train_bbox", BBOX_FRAME_ARCHIVES["train_bbox"], OUT / "frames_src" / "train_bbox"))

    mf_name = f"extract_manifest{'_' + args.only if args.only else ''}.json"
    for tag, arch, dest in jobs:
        print(f"[extract] {tag}: {arch.name} -> {dest}", flush=True)
        rec = extract_all(arch, dest)
        rec["tag"] = tag
        manifest["jobs"].append(rec)
        print(f"          done in {rec['wall_sec']}s, files={rec['files_on_disk']}", flush=True)
        # persist manifest incrementally so progress survives interruption
        (OUT / mf_name).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[saved] {OUT}/{mf_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
