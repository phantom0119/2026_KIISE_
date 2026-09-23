#!/usr/bin/env python3
"""Pillar B step 1a [AMD-B1]: preregister the P1 predicate tables for both corpora.

Emits the LOCKED predicate sets with measured (frame-weighted) selectivities,
labeled [natural] (single-facet equality) vs [composite] (range/IN-set; derivation
rule recorded). NOT-predicates are excluded by design (AMD-R5).

Corpus A = sinnaedoro corpus_real (132,521 frames; location/camera/date/hour)
Corpus B = 522-visual (143,830 frames; sensor facets via cross-camera join;
           unjoined frames are facet-NULL and never pass any predicate [AMD-M5])

Output: paper_assets/20260710_pillarB/P1_predicates_{A,B}.csv + P1_manifest.json
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DS = PROJECT_ROOT / "Datasets"
SIN = DS / "processed" / "sinnaedoro_traffic" / "corpus_real"
V522 = DS / "processed" / "aihub_522_intersection" / "20260710"
OUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260710_pillarB"


def corpus_a() -> pd.DataFrame:
    fi = pd.read_parquet(SIN / "frame_index.parquet")
    n = len(fi)
    hour = fi["time"].astype(str).str[:2]
    rows = []

    def add(name, mask, kind, rule=""):
        c = int(mask.sum())
        rows.append({"corpus": "A_sinnaedoro", "predicate": name, "kind": kind,
                     "rule": rule, "count": c, "selectivity": round(c / n, 5)})

    # natural: top location / date values spanning the low-mid range, all hour values
    for v in fi["location"].value_counts().head(6).index:
        add(f"location=={v}", fi["location"].eq(v), "natural")
    for v in fi["date"].value_counts().head(4).index:
        add(f"date=={v}", fi["date"].eq(v), "natural")
    for v in sorted(hour.value_counts().index):
        if hour.eq(v).sum() >= 1000:
            add(f"hour=={v}", hour.eq(v), "natural")
    # composite: documented derivation rules
    hnum = pd.to_numeric(hour, errors="coerce")
    add("hour in [06,18] (daytime)", hnum.between(6, 18), "composite", "range on filename hour")
    add("hour in [11,14] (midday)", hnum.between(11, 14), "composite", "range on filename hour")
    add("hour in [17,19] (evening peak)", hnum.between(17, 19), "composite", "range on filename hour")
    top5loc = list(fi["location"].value_counts().head(5).index)
    add("location in top-5", fi["location"].isin(top5loc), "composite", "IN-set of 5 most frequent locations")
    add("date in 2020-09", fi["date"].astype(str).str.startswith("202009"), "composite", "month prefix")
    return pd.DataFrame(rows)


def corpus_b() -> pd.DataFrame:
    fi = pd.read_parquet(V522 / "visual_embeddings_clip" / "frame_index.parquet")
    join = pd.read_parquet(V522 / "visual_sensor_join.parquet")
    j = join[join.join_ok_120s][["visual_video_id", "split", "time_of_day", "hour",
                                 "sig_has_yellow", "sig_has_pedestrian", "veh_density_bin"]]
    f = fi.merge(j, on=["visual_video_id", "split"], how="left",
                 suffixes=("_fn", ""))  # unjoined -> NaN facets (never pass) [AMD-M5]
    n = len(f)
    joined = f["time_of_day"].notna()
    rows = [{"corpus": "B_522visual", "predicate": "(joined frames)", "kind": "meta",
             "rule": "sensor join ok within ±120s", "count": int(joined.sum()),
             "selectivity": round(float(joined.mean()), 5)}]

    def add(name, mask, kind, rule=""):
        m = mask.fillna(False)
        c = int(m.sum())
        rows.append({"corpus": "B_522visual", "predicate": name, "kind": kind,
                     "rule": rule, "count": c, "selectivity": round(c / n, 5)})

    for v in ["morning", "afternoon", "evening"]:
        add(f"time_of_day=={v}", f["time_of_day"].eq(v), "natural")
    for v in [True, False]:
        add(f"sig_has_yellow=={v}", f["sig_has_yellow"].eq(v), "natural")
        add(f"sig_has_pedestrian=={v}", f["sig_has_pedestrian"].eq(v), "natural")
    for v in ["low", "mid", "high"]:
        add(f"veh_density_bin=={v}", f["veh_density_bin"].astype(str).eq(v), "natural",
            "derived tertile of sensor n_vehicles [AMD-M5]")
    hs = pd.to_numeric(f["hour"], errors="coerce")
    for v in sorted(hs.dropna().unique()):
        if hs.eq(v).sum() >= 2000:
            add(f"hour=={int(v)}", hs.eq(v), "natural")
    add("hour in [11,14] (midday)", hs.between(11, 14), "composite", "range on joined sensor hour")
    add("hour in [8,18] (working)", hs.between(8, 18), "composite", "range on joined sensor hour")
    add("time_of_day in {morning,evening}", f["time_of_day"].isin(["morning", "evening"]),
        "composite", "IN-set")
    return pd.DataFrame(rows)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    a, b = corpus_a(), corpus_b()
    a.to_csv(OUT / "P1_predicates_A.csv", index=False)
    b.to_csv(OUT / "P1_predicates_B.csv", index=False)
    manifest = {
        "locked": "2026-07-10 [AMD-B1]",
        "not_predicates": "excluded (AMD-R5)",
        "corpusA": {"n_frames": 132521,
                    "natural_range": [float(a[a.kind == "natural"].selectivity.min()),
                                       float(a[a.kind == "natural"].selectivity.max())],
                    "composite_range": [float(a[a.kind == "composite"].selectivity.min()),
                                         float(a[a.kind == "composite"].selectivity.max())]},
        "corpusB": {"n_frames": 143830,
                    "joined_fraction": float(b[b.kind == "meta"].selectivity.iloc[0]),
                    "natural_range": [float(b[b.kind == "natural"].selectivity.min()),
                                       float(b[b.kind == "natural"].selectivity.max())],
                    "composite_range": [float(b[b.kind == "composite"].selectivity.min()),
                                         float(b[b.kind == "composite"].selectivity.max())]},
        "cross_corpus_claim_zone": "intersection of the two achieved s-ranges only [AMD-B1]",
    }
    (OUT / "P1_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[A] {len(a)} predicates  natural s∈{manifest['corpusA']['natural_range']}  composite s∈{manifest['corpusA']['composite_range']}")
    print(f"[B] {len(b)-1} predicates  joined={manifest['corpusB']['joined_fraction']:.3f}  natural s∈{manifest['corpusB']['natural_range']}  composite s∈{manifest['corpusB']['composite_range']}")
    print(a.to_string(index=False))
    print(b.to_string(index=False))
    print(f"[saved] {OUT}/P1_predicates_{{A,B}}.csv + P1_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
