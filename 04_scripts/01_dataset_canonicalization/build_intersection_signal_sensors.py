#!/usr/bin/env python3
"""Phase-0 T2 / Pillar A1=C1: materialize 교차로신호체계(522) sensor facets.

Streams the AI-Hub intersection-signal LABEL zips (plain zip; the numeric raw
TS_1/TS_2 are the empty '미개방' placeholders and are NOT needed) and aggregates,
per clip (video_id), the structured spatiotemporal sensor records into a canonical
facet table.

Design intent (non-circular workload, kills F1/F2/F4):
  - P-series facets (EXOGENOUS predicates, independent of any QA answer):
      intersection_id, time_of_day, is_weekend, hour, signal-phase presence.
    -> usable as metadata FILTER predicates.
  - R-series facets (relevance/semantic side, may become QA answers):
      vehicle density, car-type presence, turn behavior, pedestrian density, bicycle.
    -> used to DEFINE questions/relevance, NEVER as the filter predicate.
The T2 deliverable is the printed cardinality/selectivity report + the
predicate<->relevance Cramér's V independence matrix.

Run:
  Datasets/envs/kiise-vlmdb/bin/python \
    2026_KIISE/04_scripts/build_intersection_signal_sensors.py [--out <dir>]
"""
from __future__ import annotations

import argparse
import csv
import io
import itertools
import json
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # .../KIISE_datasociety
DS = PROJECT_ROOT / "Datasets"
LABEL_ROOT = DS / "external" / "교차로신호체계"

# (split, vehicle_zip, pedestrian_zip)
ZIP_SETS = [
    ("train", "1.Training/라벨링데이터/TL_1.통과차량.zip", "1.Training/라벨링데이터/TL_2.보행량.zip"),
    ("val", "2.Validation/라벨링데이터/VL_1.통과차량.zip", "2.Validation/라벨링데이터/VL_2.보행량.zip"),
]

TRUCK_TYPES = {"truck", "large_truck", "small_truck"}
BIKE_TYPES = {"bike", "motorcycle", "bicycle"}


def parse_video_id(video_id: str, folder: str) -> dict:
    """video_id like '101010_2021090813495200' -> intersection + timestamp facets."""
    intersection = folder  # zip folder == intersection id (authoritative)
    tail = video_id[len(intersection) + 1 :] if video_id.startswith(intersection + "_") else ""
    dt = None
    digits = "".join(ch for ch in tail if ch.isdigit())
    if len(digits) >= 12:
        try:
            dt = datetime.strptime(digits[:14] if len(digits) >= 14 else digits[:12],
                                   "%Y%m%d%H%M%S" if len(digits) >= 14 else "%Y%m%d%H%M")
        except ValueError:
            dt = None
    if dt is None:
        return {"intersection_id": intersection, "date": "", "hour": -1,
                "time_of_day": "unknown", "weekday": "unknown", "is_weekend": None}
    hour = dt.hour
    tod = ("dawn" if hour < 6 else "morning" if hour < 12
           else "afternoon" if hour < 18 else "evening")
    wd = dt.strftime("%a")
    return {"intersection_id": intersection, "date": dt.strftime("%Y-%m-%d"), "hour": hour,
            "time_of_day": tod, "weekday": wd, "is_weekend": wd in ("Sat", "Sun")}


def read_csv_rows(zf: zipfile.ZipFile, name: str) -> list[dict]:
    txt = zf.read(name).decode("utf-8-sig", errors="replace")
    return list(csv.DictReader(io.StringIO(txt)))


def agg_vehicle(rows: list[dict]) -> dict:
    sig = Counter(r.get("signal_info.movement", "").strip() for r in rows)
    mv = Counter(r.get("car_info.movement", "").strip() for r in rows)
    ct = Counter(r.get("car_type", "").strip() for r in rows)
    lanes = {r.get("lane", "").strip() for r in rows if r.get("lane", "").strip()}
    n = len(rows)
    sigset = {k for k in sig if k}
    return {
        "n_vehicles": n,
        # R-series (behavior / semantic)
        "has_bus": ("bus" in ct or "small_bus" in ct),
        "has_truck": any(t in ct for t in TRUCK_TYPES),
        "has_bike_veh": any(t in ct for t in BIKE_TYPES),
        "n_car_types": sum(1 for k, v in ct.items() if k and v),
        "has_left_turn_veh": (mv.get("l", 0) > 0),
        "has_right_turn_veh": (mv.get("r", 0) > 0),
        "has_uturn_veh": (mv.get("u", 0) > 0),
        "n_lanes_used": len(lanes),
        # P-series (signal infrastructure state = exogenous)
        "sig_has_left": ("l" in sigset or "tl" in sigset),
        "sig_has_straight": ("s" in sigset or "tl" in sigset or "t" in sigset),
        "sig_has_yellow": ("y" in sigset),
        "sig_has_pedestrian": ("p" in sigset),
        "sig_phase_set": ",".join(sorted(sigset)),
        "_sig_counts": dict(sig),
        "_carmv_counts": dict(mv),
        "_ctype_counts": dict(ct),
    }


def agg_pedestrian(rows: list[dict]) -> dict:
    types = Counter(r.get("pedestrian_info.pedestrian_type", "").strip() for r in rows)
    dirs = Counter(r.get("pedestrian_info.direction", "").strip() for r in rows)
    n_ped = sum(v for k, v in types.items() if k in ("pedestrian", ""))
    n_bike = sum(v for k, v in types.items() if k in BIKE_TYPES)
    return {
        "n_pedestrians": n_ped,
        "n_bicycle_ped": n_bike,
        "has_bicycle_ped": n_bike > 0,
        "ped_dir_set": ",".join(sorted(k for k in dirs if k)),
    }


def qbin(series: pd.Series, labels=("low", "mid", "high")) -> pd.Series:
    """Robust tercile binning."""
    try:
        return pd.qcut(series.rank(method="first"), len(labels), labels=list(labels))
    except Exception:
        return pd.cut(series, len(labels), labels=list(labels))


def cramers_v(a: pd.Series, b: pd.Series) -> float:
    tab = pd.crosstab(a, b)
    if tab.shape[0] < 2 or tab.shape[1] < 2:
        return float("nan")
    chi2 = _chi2(tab.to_numpy(dtype=float))
    n = tab.to_numpy().sum()
    r, k = tab.shape
    phi2 = chi2 / n
    phi2corr = max(0.0, phi2 - (k - 1) * (r - 1) / (n - 1))
    rcorr = r - (r - 1) ** 2 / (n - 1)
    kcorr = k - (k - 1) ** 2 / (n - 1)
    denom = min(kcorr - 1, rcorr - 1)
    return float(np.sqrt(phi2corr / denom)) if denom > 0 else float("nan")


def _chi2(obs: np.ndarray) -> float:
    row = obs.sum(1, keepdims=True)
    col = obs.sum(0, keepdims=True)
    exp = row @ col / obs.sum()
    with np.errstate(divide="ignore", invalid="ignore"):
        term = np.where(exp > 0, (obs - exp) ** 2 / exp, 0.0)
    return float(term.sum())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(DS / "processed" / "aihub_522_intersection" / "20260710"))
    ap.add_argument("--dataset-id", default="aihub_522_intersection")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    clips: dict[str, dict] = {}
    for split, vzip, pzip in ZIP_SETS:
        vpath, ppath = LABEL_ROOT / vzip, LABEL_ROOT / pzip
        # vehicles
        with zipfile.ZipFile(vpath) as zf:
            for name in zf.namelist():
                if not name.endswith(".csv"):
                    continue
                folder = name.split("/")[0]
                rows = read_csv_rows(zf, name)
                if not rows:
                    continue
                vid = rows[0].get("video_id") or Path(name).stem
                rec = {"clip_id": f"{args.dataset_id}:{split}:{vid}", "video_id": vid,
                       "split": split, "source_folder": folder}
                rec.update(parse_video_id(vid, folder))
                rec.update(agg_vehicle(rows))
                clips[rec["clip_id"]] = rec
        # pedestrians (join)
        with zipfile.ZipFile(ppath) as zf:
            for name in zf.namelist():
                if not name.endswith(".csv"):
                    continue
                rows = read_csv_rows(zf, name)
                vid = (rows[0].get("video_id") if rows else None) or Path(name).stem
                cid = f"{args.dataset_id}:{split}:{vid}"
                if cid in clips:
                    clips[cid].update(agg_pedestrian(rows))
        print(f"[{split}] clips so far: {len(clips)}")

    df = pd.DataFrame(list(clips.values()))
    # fill pedestrian gaps
    for col, val in {"n_pedestrians": 0, "n_bicycle_ped": 0, "has_bicycle_ped": False, "ped_dir_set": ""}.items():
        if col not in df:
            df[col] = val
        df[col] = df[col].fillna(val)
    # density bins
    df["veh_density_bin"] = qbin(df["n_vehicles"])
    df["ped_density_bin"] = qbin(df["n_pedestrians"].clip(lower=0))

    # persist (drop debug dict columns from parquet-facing copy but keep counts json)
    debug_cols = ["_sig_counts", "_carmv_counts", "_ctype_counts"]
    df_out = df.drop(columns=[c for c in debug_cols if c in df])
    df_out.to_parquet(out / "sensor_facets.parquet", index=False)

    # ---------- T2 REPORT ----------
    P_PREDICATES = ["intersection_id", "time_of_day", "is_weekend", "hour",
                    "sig_has_left", "sig_has_yellow", "sig_has_pedestrian", "veh_density_bin"]
    R_FEATURES = ["has_bus", "has_truck", "has_left_turn_veh", "has_right_turn_veh",
                  "has_uturn_veh", "has_bicycle_ped", "ped_density_bin", "n_car_types"]

    report = {"n_clips": int(len(df)), "n_intersections": int(df["intersection_id"].nunique()),
              "predicate_selectivity": {}, "signal_phase": {}, "independence_cramers_v": {}}
    lines = ["=" * 78, f"T2 SENSOR FACET REPORT — {len(df)} clips, {df['intersection_id'].nunique()} intersections",
             "=" * 78, "", "## P-series PREDICATE cardinality & selectivity (min class fraction)"]
    for c in P_PREDICATES:
        vc = df[c].value_counts(dropna=False)
        frac = (vc / len(df))
        sel = float(frac.min())
        report["predicate_selectivity"][c] = {"cardinality": int(vc.shape[0]),
                                               "min_class_frac": round(sel, 4),
                                               "top": {str(k): int(v) for k, v in vc.head(5).items()}}
        lines.append(f"  {c:22s} card={vc.shape[0]:3d}  min_sel={sel:.4f}  top={dict(itertools.islice(((str(k),int(v)) for k,v in vc.items()),4))}")

    # signal phase (T2 tripwire: is it >>'t'?)
    sig_total = Counter()
    for d in df["_sig_counts"]:
        sig_total.update(d)
    tot = sum(sig_total.values()) or 1
    report["signal_phase"] = {"global_movement_dist": {k: int(v) for k, v in sig_total.items()},
                              "t_fraction": round(sig_total.get("t", 0) / tot, 4),
                              "clips_with_left_signal": int(df["sig_has_left"].sum()),
                              "clips_with_yellow": int(df["sig_has_yellow"].sum()),
                              "clips_with_pedestrian_phase": int(df["sig_has_pedestrian"].sum())}
    lines += ["", "## SIGNAL PHASE (T2 tripwire — must be richer than all-'t')",
              f"  global signal_info.movement: {dict(sig_total)}",
              f"  't' fraction of all vehicle rows: {sig_total.get('t',0)/tot:.3f}",
              f"  clips w/ left-signal: {int(df['sig_has_left'].sum())}/{len(df)}"
              f"  yellow: {int(df['sig_has_yellow'].sum())}  ped-phase: {int(df['sig_has_pedestrian'].sum())}"]

    # independence matrix (T3 probe): P-predicate vs R-feature Cramér's V
    lines += ["", "## PREDICATE ⟂ RELEVANCE independence (Cramér's V; low=good, ~1.0=circular)"]
    for p in P_PREDICATES:
        row = {}
        for r in R_FEATURES:
            v = cramers_v(df[p].astype(str), df[r].astype(str))
            row[r] = None if np.isnan(v) else round(v, 3)
        report["independence_cramers_v"][p] = row
    vmax = 0.0
    for p, row in report["independence_cramers_v"].items():
        vals = [x for x in row.values() if x is not None]
        mx = max(vals) if vals else 0.0
        vmax = max(vmax, mx)
        worst = max(row.items(), key=lambda kv: (kv[1] is not None, kv[1] or 0))
        lines.append(f"  {p:22s} max V={mx:.3f}  (worst: {worst[0]}={worst[1]})")
    lines += ["", f"## VERDICT: global max Cramér's V(P,R) = {vmax:.3f}  "
              + ("→ predicates broadly independent of relevance (F1/F4 breakable)"
                 if vmax < 0.5 else "→ some P–R coupling; select low-V pairs for headline")]

    (out / "T2_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out / "T2_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n".join(lines))
    print(f"\n[saved] {out}/sensor_facets.parquet  ({len(df)} rows, {df_out.shape[1]} cols)")
    print(f"[saved] {out}/T2_report.md , T2_report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
