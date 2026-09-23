#!/usr/bin/env python3
"""Pillar C: clip-level multimodal join between 522 visual frames and sensor records.

Discovery (2026-07-10 T1 probe): the '도로차량' archives hold pre-extracted JPG
frames from cameras <intersection>+{11,22}, while the TL_1/TL_2 sensor CSVs come
from camera <intersection>+10 — DIFFERENT cameras at the SAME 63 intersections,
recorded in the SAME sessions: 90.0% of visual videos have a sensor clip at the
same intersection within ±120 s. This script materializes that join:

  visual_videos.parquet     one row per visual video (cam, intersection, dt,
                            n_frames, task, split, frame relpaths)
  visual_sensor_join.parquet  visual video -> nearest sensor clip (gap_sec,
                            quality flags) + the sensor predicate facets
                            (time_of_day, hour, sig_*, densities) attached.

Honest caveat encoded in columns: join_type='cross_camera_time_window' — the
sensor record describes the same intersection's traffic state within the window,
not the identical camera view. This is exactly the stream-join a real urban
surveillance DB performs (intersection_id + timestamp), and the gap is recorded
per row so downstream experiments can tighten the window.

Run:
  Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/04_scripts/build_visual_sensor_join.py
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import py7zr

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DS = PROJECT_ROOT / "Datasets"
EXT = DS / "external" / "교차로신호체계"
VER = DS / "processed" / "aihub_522_intersection" / "20260710"

FRAME_ARCHIVES = {
    "train": EXT / "1.Training" / "원천데이터" / "TS_3.도로차량.zip",
    "val": EXT / "2.Validation" / "원천데이터" / "VS_3.도로차량.zip",
}

VID_RE = re.compile(r"^(\d+)_(\d{14})(\d*)$")

SENSOR_FACETS = ["time_of_day", "hour", "sig_has_yellow", "sig_has_pedestrian",
                 "sig_has_left", "sig_phase_set", "n_vehicles", "veh_density_bin",
                 "n_pedestrians", "ped_density_bin", "has_bus", "has_truck",
                 "has_uturn_veh", "has_bicycle_ped", "n_bicycle_ped"]


def parse_video_id(vid: str):
    m = VID_RE.match(vid)
    if not m:
        return None
    cam, ts = m.group(1), m.group(2)
    try:
        dt = datetime.strptime(ts, "%Y%m%d%H%M%S")
    except ValueError:
        return None
    return {"camera_id": cam, "intersection_id": cam[:-2], "cam_code": cam[-2:], "dt": dt}


def list_visual_videos() -> pd.DataFrame:
    rows: dict[str, dict] = {}
    for split, arch in FRAME_ARCHIVES.items():
        with py7zr.SevenZipFile(arch, "r") as z:
            names = z.getnames()
        for n in names:
            if not n.endswith(".jpg"):
                continue
            parts = n.split("/")           # <cam>/<task>/<video_id>_<frame>.jpg
            stem = Path(n).stem
            vid, frame = stem.rsplit("_", 1)
            p = parse_video_id(vid)
            if p is None:
                continue
            key = f"{split}:{vid}"
            rec = rows.setdefault(key, {
                "visual_video_id": vid, "split": split, "task": parts[1] if len(parts) >= 3 else "",
                **p, "n_frames": 0, "frame_relpaths": []})
            rec["n_frames"] += 1
            rec["frame_relpaths"].append(str(Path("frames_src") / split / n))
    df = pd.DataFrame(list(rows.values()))
    df["frame_relpaths"] = df["frame_relpaths"].map(sorted)
    return df


def nearest_sensor_join(vdf: pd.DataFrame, sdf: pd.DataFrame) -> pd.DataFrame:
    out = []
    sg = {k: g.sort_values("dt").reset_index(drop=True)
          for k, g in sdf.groupby("intersection_id")}
    for inter, g in vdf.groupby("intersection_id"):
        s = sg.get(inter)
        if s is None:
            for _, r in g.iterrows():
                out.append({"visual_video_id": r.visual_video_id, "split": r.split,
                            "sensor_clip_id": None, "gap_sec": np.inf})
            continue
        st = s["dt"].to_numpy()
        for _, r in g.iterrows():
            t = np.datetime64(r["dt"])
            i = np.searchsorted(st, t)
            cand = []
            if i < len(st):
                cand.append((abs((st[i] - t) / np.timedelta64(1, "s")), i))
            if i > 0:
                cand.append((abs((st[i - 1] - t) / np.timedelta64(1, "s")), i - 1))
            gap, j = min(cand)
            out.append({"visual_video_id": r.visual_video_id, "split": r.split,
                        "sensor_clip_id": s.iloc[j]["clip_id"], "gap_sec": float(gap)})
    return pd.DataFrame(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--facets", default=str(VER / "sensor_facets.parquet"))
    ap.add_argument("--out", default=str(VER))
    args = ap.parse_args()
    out = Path(args.out)

    sdf = pd.read_parquet(args.facets)
    sdf = sdf.assign(dt=pd.to_datetime(
        sdf["video_id"].str.extract(r"_(\d{14})")[0], format="%Y%m%d%H%M%S", errors="coerce"))
    sdf = sdf.dropna(subset=["dt"])
    # normalize join key: sensor 'intersection_id' column is the zip folder = CAMERA id
    # (e.g. '101010' = intersection '1010' + cam code '10'); visual side uses cam[:-2].
    sdf = sdf.assign(intersection_id=sdf["video_id"].str.extract(r"^(\d+)_")[0].str[:-2])

    vdf = list_visual_videos()
    print(f"[visual] videos={len(vdf)}  frames={int(vdf.n_frames.sum())}  "
          f"cams={vdf.cam_code.value_counts().to_dict()}  intersections={vdf.intersection_id.nunique()}")

    join = nearest_sensor_join(vdf, sdf[["clip_id", "intersection_id", "dt"]])
    join["join_type"] = "cross_camera_time_window"
    for w in (120, 300, 900):
        join[f"join_ok_{w}s"] = join["gap_sec"] <= w

    # attach sensor predicate facets for joined rows
    facet_cols = [c for c in SENSOR_FACETS if c in sdf.columns]
    join = join.merge(sdf[["clip_id"] + facet_cols].rename(columns={"clip_id": "sensor_clip_id"}),
                      on="sensor_clip_id", how="left")
    vdf.to_parquet(out / "visual_videos.parquet", index=False)
    join.to_parquet(out / "visual_sensor_join.parquet", index=False)

    stats = {
        "visual_videos": int(len(vdf)),
        "visual_frames": int(vdf.n_frames.sum()),
        "join_rate_120s": round(float(join["join_ok_120s"].mean()), 4),
        "join_rate_300s": round(float(join["join_ok_300s"].mean()), 4),
        "join_rate_900s": round(float(join["join_ok_900s"].mean()), 4),
        "median_gap_sec": float(join["gap_sec"].replace(np.inf, np.nan).median()),
        "unjoined": int((~np.isfinite(join["gap_sec"])).sum()),
        "note": "sensor cam=xx10, visual cams=xx11/xx22 at same intersections; join is operational stream-join by intersection+time",
    }
    (out / "visual_sensor_join_stats.json").write_text(
        json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"[saved] {out}/visual_videos.parquet , visual_sensor_join.parquet , visual_sensor_join_stats.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
