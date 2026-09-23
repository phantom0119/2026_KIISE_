#!/usr/bin/env python3
"""Pillar C: frame/video-level VISUAL relevance facets from human CVAT annotations.

Parses the extracted 522 label XMLs (labels_src/):
  TL_3/VL_3 '도로차량'  — per-frame vehicle POLYLINE trajectories with labels
                          (car/bus/truck/small_truck/large_truck/small_bus/bike/
                          unknown) and attributes is_stopped/is_parked/is_visible.
  TL_4/VL_4 '바운딩박스' — per-frame vehicle BBOXes; task directory encodes the
                          environment category: 1.교차로 / 2.악천후 / 3.시간대.

Emits annotation-derived relevance facets that are INDEPENDENT BY SOURCE from
the sensor predicates (TL_1/TL_2 CSVs, camera x10) — annotations describe
cameras x11/x22 frames and were produced by human labelers, so using them as
retrieval relevance while filtering on sensor/env predicates is non-circular at
the file/camera level.

Outputs under processed/aihub_522_intersection/<ver>/:
  annotation_frame_facets.parquet   one row per annotated frame
  annotation_video_facets.parquet   aggregated per visual video (+task env category)

Run:
  Datasets/envs/kiise-vlmdb/bin/python \
    2026_KIISE/scripts/build_intersection_annotation_facets.py
"""
from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DS = PROJECT_ROOT / "Datasets"
VER = DS / "processed" / "aihub_522_intersection" / "20260710"

VEHICLE_LABELS = {"car", "bus", "small_bus", "truck", "small_truck", "large_truck", "bike"}
PRIVACY_LABELS = {"car_plate", "face"}


def parse_tl3_xml(path: Path, split: str) -> list[dict]:
    """Road-vehicle polylines: per-frame vehicle counts + behavior states."""
    rows = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return rows
    task = path.stem
    for img in root.iter("image"):
        name = img.attrib.get("name", "")
        stem = Path(name).stem
        if "_" not in stem:
            continue
        vid, frame = stem.rsplit("_", 1)
        cnt = Counter()
        n_stopped = n_parked = n_visible = n_total = 0
        for el in img:
            if el.tag not in ("polyline", "polygon", "points", "box"):
                continue
            label = el.attrib.get("label", "")
            attrs = {a.attrib.get("name"): (a.text or "").strip() for a in el.iter("attribute")}
            if attrs.get("is_correct") == "False":
                continue  # labeler-flagged invalid object
            n_total += 1
            if label in VEHICLE_LABELS:
                cnt[label] += 1
            if attrs.get("is_stopped") == "True":
                n_stopped += 1
            if attrs.get("is_parked") == "True":
                n_parked += 1
            if attrs.get("is_visible") == "True":
                n_visible += 1
        rows.append({
            "split": split, "task": task, "visual_video_id": vid, "frame": frame,
            "frame_name": name, "ann_source": "TL_3_polyline",
            "n_objects": n_total, "n_stopped": n_stopped, "n_parked": n_parked,
            "n_visible": n_visible,
            **{f"n_{k}": cnt.get(k, 0) for k in sorted(VEHICLE_LABELS)},
        })
    return rows


def parse_tl4_xml(path: Path, split: str, category: str) -> list[dict]:
    """BBox annotations: per-frame vehicle bbox counts + env category from dir."""
    rows = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return rows
    task = path.stem
    for img in root.iter("image"):
        name = img.attrib.get("name", "")
        stem = Path(name).stem
        if "_" not in stem:
            continue
        vid, frame = stem.rsplit("_", 1)
        cnt = Counter()
        n_priv = 0
        for el in img:
            if el.tag != "box":
                continue
            label = el.attrib.get("label", "")
            if label in VEHICLE_LABELS:
                cnt[label] += 1
            elif label in PRIVACY_LABELS:
                n_priv += 1
        rows.append({
            "split": split, "task": task, "visual_video_id": vid, "frame": frame,
            "frame_name": name, "ann_source": "TL_4_bbox", "env_category": category,
            "n_bbox_vehicles": sum(cnt.values()), "n_privacy_boxes": n_priv,
            **{f"bb_{k}": cnt.get(k, 0) for k in sorted(VEHICLE_LABELS)},
        })
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ver", default=str(VER))
    args = ap.parse_args()
    ver = Path(args.ver)

    # ---- TL_3 / VL_3 ----
    tl3_rows: list[dict] = []
    for split, tag in (("train", "TL_3"), ("val", "VL_3")):
        root = ver / "labels_src" / split / tag
        xmls = sorted(root.rglob("*.xml"))
        for x in xmls:
            tl3_rows.extend(parse_tl3_xml(x, split))
        print(f"[{tag}] xml={len(xmls)} frame_rows={len(tl3_rows)}")
    tl3 = pd.DataFrame(tl3_rows)

    # ---- TL_4 / VL_4 (env categories) ----
    tl4_rows: list[dict] = []
    for split, tag in (("train", "TL_4"), ("val", "VL_4")):
        root = ver / "labels_src" / split / tag
        for x in sorted(root.rglob("*.xml")):
            relparts = x.relative_to(root).parts
            category = relparts[0] if len(relparts) > 1 else "uncategorized"
            tl4_rows.extend(parse_tl4_xml(x, split, category))
        print(f"[{tag}] frame_rows(total)={len(tl4_rows)}")
    tl4 = pd.DataFrame(tl4_rows)

    frames = pd.concat([tl3, tl4], ignore_index=True)
    frames.to_parquet(ver / "annotation_frame_facets.parquet", index=False)

    # ---- per-video aggregation (relevance-ready) ----
    vt3 = tl3.groupby(["split", "visual_video_id"]).agg(
        n_frames_ann=("frame", "nunique"), max_objects=("n_objects", "max"),
        any_stopped=("n_stopped", lambda s: bool((s > 0).any())),
        any_parked=("n_parked", lambda s: bool((s > 0).any())),
        max_bus=("n_bus", "max"), max_truckish=("n_truck", "max"),
        max_car=("n_car", "max"), max_bike=("n_bike", "max"),
    ).reset_index()
    # merge in large/small truck for a combined truck-family count
    tfam = tl3.assign(truck_fam=tl3.n_truck + tl3.n_small_truck + tl3.n_large_truck) \
              .groupby(["split", "visual_video_id"])["truck_fam"].max().rename("max_truck_family")
    vt3 = vt3.merge(tfam.reset_index(), on=["split", "visual_video_id"], how="left")
    env = tl4.groupby(["split", "visual_video_id"])["env_category"].agg(
        lambda s: s.value_counts().index[0]).rename("env_category").reset_index()
    video = vt3.merge(env, on=["split", "visual_video_id"], how="left")
    video["env_category"] = video["env_category"].fillna("unannotated_tl4")
    video.to_parquet(ver / "annotation_video_facets.parquet", index=False)

    stats = {
        "frame_rows": int(len(frames)),
        "tl3_frames": int(len(tl3)), "tl4_frames": int(len(tl4)),
        "videos_with_tl3": int(vt3.shape[0]),
        "videos_with_env": int((video.env_category != "unannotated_tl4").sum()),
        "env_category_dist": video.env_category.value_counts().to_dict(),
        "any_stopped_rate": round(float(video.any_stopped.mean()), 4),
        "any_parked_rate": round(float(video.any_parked.mean()), 4),
        "bus_present_rate": round(float((video.max_bus > 0).mean()), 4),
        "bike_present_rate": round(float((video.max_bike > 0).mean()), 4),
    }
    (ver / "annotation_facets_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"[saved] {ver}/annotation_frame_facets.parquet , annotation_video_facets.parquet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
