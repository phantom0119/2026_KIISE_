#!/usr/bin/env python3
"""MEVA (WACV 2021) tri-source facets — the OVERSEAS external-validity arm.

Mirrors the 522 pipeline (build_intersection_signal_sensors +
build_intersection_annotation_facets) for the MEVA KF1 / DIVA-phase-2 release,
keeping the SAME source-separation discipline that makes the workload
non-circular:

  PREDICATE  = capture metadata (date / time / location / camera / modality),
               parsed from the clip filename + clip-camera-time table.
               Producer = the recording rig. NEVER sees pixels or annotations.
               facet_source = "meva_capture_metadata"
  RELEVANCE  = DIVA/ActEV human activity annotations (37 activity classes),
               parsed from KPF *.activities.yml.
               Producer = the human annotator. facet_source = "meva_diva_activity".
  DOCUMENT   = VLM caption of frame pixels (built later by build_meva_captions.py).

Critical non-circularity rule (enforced by the A6 audit in the canonical step):
the human-annotated ACTIVITY label is RELEVANCE ONLY and must never be reused as
a filter predicate; the predicate is drawn strictly from capture metadata, which
is physically independent of both the pixels and the activity annotation.

Inputs (local clone):
  Datasets/external/meva/meva-data-repo/
     annotation/DIVA-phase-2/MEVA/kitware-meva-training/<date>/<hour>/<clip>.activities.yml
     metadata/meva-clip-camera-and-time-table.txt   (EO/IR modality)

Outputs: Datasets/processed/meva_kf1/<ver>/
  clips.parquet            one row per annotated clip (+ S3 avi key)
  predicate_facets.parquet long-form capture-metadata predicates
  activity_presence.parquet wide per-clip activity presence(0/1)+count
  meva_independence.json   predicate x activity Cramer's V (T3 coupling) + densities
  meva_facets_stats.json

Run:
  Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/04_scripts/build_meva_facets.py
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DS = PROJECT_ROOT / "Datasets"
REPO = DS / "external" / "meva" / "meva-data-repo"
DATASET_ID = "meva_kf1"

# DIVA/ActEV 37 activity classes = the RELEVANCE vocabulary (documents/activity-names.txt)
ACTIVITY_NAMES_FILE = REPO / "documents" / "activity-names.txt"
CLIP_TABLE = REPO / "metadata" / "meva-clip-camera-and-time-table.txt"
# annotation sub-collections to include (kitware-meva-training = the main KF1 training set)
ANN_SUBSETS = ["kitware-meva-training"]


def time_of_day(hour: int) -> str:
    if hour < 6:
        return "night"
    if hour < 12:
        return "morning"
    if hour < 17:
        return "afternoon"
    if hour < 21:
        return "evening"
    return "night"


def parse_clip_base(clip_base: str) -> dict | None:
    """'2018-03-07.10-55-00.10-59-59.admin.G329' -> capture-metadata predicate."""
    parts = clip_base.split(".")
    if len(parts) != 5:
        return None
    date, start, end, location, camera = parts
    try:
        hh = int(start.split("-")[0])
    except Exception:
        return None
    wd = pd.Timestamp(date).day_name() if _valid_date(date) else "unknown"
    return {
        "clip_base": clip_base, "date": date, "weekday": wd,
        "start_hms": start, "end_hms": end, "hour": hh,
        "time_of_day": time_of_day(hh), "location": location, "camera": camera,
    }


def _valid_date(d: str) -> bool:
    try:
        pd.Timestamp(d); return True
    except Exception:
        return False


def load_modality_table() -> dict[str, str]:
    """clip_base -> 'IR' | 'EO' from the clip-camera-time table (IR = thermal)."""
    mod = {}
    if not CLIP_TABLE.exists():
        return mod
    for line in CLIP_TABLE.read_text(errors="ignore").splitlines():
        toks = line.split()
        if not toks:
            continue
        cb = toks[0]
        mod[cb] = "IR" if any(t == "IR" for t in toks[1:]) else "EO"
    return mod


def extract_activities(fp: str) -> list[str]:
    """KPF *.activities.yml -> list of activity-class names (one per instance).
    Record schema (locked on real files):
      {'act': {'act2': {<name>: 1.0}, 'actors': [...], 'timespan': [...]}}
    Handles act2/act3 and the flat {name:conf} variant defensively."""
    try:
        recs = yaml.safe_load(open(fp)) or []
    except Exception:
        return []
    out = []
    for r in recs:
        if not (isinstance(r, dict) and "act" in r):
            continue
        a = r["act"]
        if not isinstance(a, dict):
            continue
        nm = None
        for cs in ("act2", "act3"):
            if cs in a and isinstance(a[cs], dict) and a[cs]:
                nm = next(iter(a[cs])); break
        if nm is None:  # flat {name: conf, actors:..., id2:...}
            cand = [k for k in a if k not in ("actors", "id2", "timespan", "src_status", "src")]
            if len(cand) == 1 and isinstance(a[cand[0]], (int, float)):
                nm = cand[0]
        if nm:
            out.append(nm)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ver", default="20260713")
    ap.add_argument("--drop", default="drops-123-r13", help="S3 video drop prefix")
    args = ap.parse_args()
    out = DS / "processed" / DATASET_ID / args.ver
    out.mkdir(parents=True, exist_ok=True)

    vocab = [x.strip() for x in ACTIVITY_NAMES_FILE.read_text().splitlines() if x.strip()]
    assert len(vocab) == 37, f"expected 37 activity classes, got {len(vocab)}"
    modality = load_modality_table()

    files = []
    for sub in ANN_SUBSETS:
        files += glob.glob(str(REPO / "annotation" / "DIVA-phase-2" / "MEVA" / sub
                               / "**" / "*.activities.yml"), recursive=True)
    files = sorted(set(files))
    print(f"[scan] {len(files)} activities.yml across {ANN_SUBSETS}")

    rows, presence = [], []
    for fp in files:
        clip_base = Path(fp).name[: -len(".activities.yml")]
        meta = parse_clip_base(clip_base)
        if meta is None:
            continue
        acts = extract_activities(fp)
        counts = {a: acts.count(a) for a in set(acts)}
        hour = meta["hour"]
        avi_key = f"{args.drop}/{meta['date']}/{hour:02d}/{clip_base}.r13.avi"
        clip_id = f"{DATASET_ID}:{clip_base}"
        meta.update({
            "clip_id": clip_id, "dataset_id": DATASET_ID,
            "modality": modality.get(clip_base, "EO"),
            "avi_s3_key": avi_key,
            "n_activity_instances": len(acts),
            "n_activity_types": len(counts),
            "has_activity": len(acts) > 0,
        })
        rows.append(meta)
        prow = {"clip_id": clip_id}
        for v in vocab:
            prow[f"act__{v}"] = int(v in counts)
            prow[f"cnt__{v}"] = int(counts.get(v, 0))
        presence.append(prow)

    clips = pd.DataFrame(rows)
    pres = pd.DataFrame(presence)
    clips.to_parquet(out / "clips.parquet", index=False)
    pres.to_parquet(out / "activity_presence.parquet", index=False)
    print(f"[clips] {len(clips)}  with>=1 activity: {int(clips.has_activity.sum())}")

    # ---- predicate facets (long form; capture metadata only) ----
    P_FACETS = ["time_of_day", "hour", "location", "camera", "modality", "weekday"]
    pf = []
    for rec in clips.to_dict("records"):
        for f in P_FACETS:
            pf.append({"clip_id": rec["clip_id"], "dataset_id": DATASET_ID,
                       "facet_name": f, "facet_value": str(rec[f]),
                       "facet_role": "predicate", "facet_source": "meva_capture_metadata"})
    pd.DataFrame(pf).to_parquet(out / "predicate_facets.parquet", index=False)

    # ---- relevance densities (fraction of corpus clips with each activity) ----
    dens = {v: round(float(pres[f"act__{v}"].mean()), 4) for v in vocab}
    dens = dict(sorted(dens.items(), key=lambda kv: kv[1]))

    # ---- T3 coupling: predicate x activity-presence Cramer's V ----
    def cramers_v(a: pd.Series, b: pd.Series) -> float:
        t = pd.crosstab(a, b).to_numpy(float)
        if min(t.shape) < 2:
            return float("nan")
        r = t.sum(1, keepdims=True); c = t.sum(0, keepdims=True); e = r @ c / t.sum()
        chi = np.where(e > 0, (t - e) ** 2 / e, 0.0).sum()
        n = t.sum(); rr, kk = t.shape
        ph = max(0.0, chi / n - (kk - 1) * (rr - 1) / (n - 1))
        rc = rr - (rr - 1) ** 2 / (n - 1); kc = kk - (kk - 1) ** 2 / (n - 1)
        d = min(kc - 1, rc - 1)
        return float(np.sqrt(ph / d)) if d > 0 else float("nan")

    m = clips.merge(pres, on="clip_id")
    coupling = []
    cand_preds = ["time_of_day", "location", "modality"]  # low-cardinality categorical predicates
    # activities present in >=1.5% and <=25% of clips = usable retrieval relevance
    usable_acts = [v for v in vocab if 0.015 <= dens[v] <= 0.25]
    for p in cand_preds:
        for v in usable_acts:
            cv = cramers_v(m[p].astype(str), m[f"act__{v}"].astype(str))
            coupling.append({"predicate": p, "relevance": v,
                             "cramers_v": None if np.isnan(cv) else round(cv, 4),
                             "rel_density": dens[v],
                             "coupling": "contrast" if (not np.isnan(cv) and cv >= 0.3) else "low"})
    cdf = pd.DataFrame(coupling)
    indep = {
        "n_clips": int(len(clips)),
        "n_clips_with_activity": int(clips.has_activity.sum()),
        "relevance_densities": dens,
        "usable_relevance_acts_1p5_to_25pct": usable_acts,
        "n_low_coupling_pairs": int((cdf.coupling == "low").sum()) if len(cdf) else 0,
        "n_contrast_pairs": int((cdf.coupling == "contrast").sum()) if len(cdf) else 0,
        "max_cramers_v": None if not len(cdf) else float(cdf.cramers_v.dropna().max() or 0),
        "coupling_pairs": coupling,
        "source_separation": {
            "predicate_source": "meva_capture_metadata (filename + clip-camera-time table)",
            "relevance_source": "meva_diva_activity (KPF human annotation)",
            "document_source": "vlm_caption_pixels_only (deferred)",
            "note": "activity label is RELEVANCE ONLY; predicate is capture metadata, "
                    "physically independent of pixels and annotation.",
        },
    }
    (out / "meva_independence.json").write_text(json.dumps(indep, ensure_ascii=False, indent=2))

    stats = {
        "n_activities_yml": len(files), "n_clips": int(len(clips)),
        "n_clips_with_activity": int(clips.has_activity.sum()),
        "locations": clips.location.value_counts().to_dict(),
        "modality": clips.modality.value_counts().to_dict(),
        "time_of_day": clips.time_of_day.value_counts().to_dict(),
        "n_cameras": int(clips.camera.nunique()),
        "sparsest_5_activities": dict(list(dens.items())[:5]),
        "densest_5_activities": dict(list(dens.items())[-5:]),
    }
    (out / "meva_facets_stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"[facets] predicate rows={len(pf)}  usable-relevance acts={len(usable_acts)}  "
          f"low/contrast pairs={indep['n_low_coupling_pairs']}/{indep['n_contrast_pairs']}  "
          f"maxV={indep['max_cramers_v']}")
    print(f"[stats] locations={stats['locations']}  modality={stats['modality']}  cams={stats['n_cameras']}")
    print(f"[saved] {out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
