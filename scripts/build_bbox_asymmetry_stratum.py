#!/usr/bin/env python3
"""Build the bbox-asymmetry stratum for the answer-level multi-view VLM experiment.

Per clip: better_view = view with larger mean evidence-frame bbox area.
  asymmetric  : area_ratio (larger/smaller) >= --asym-thr   (MAIN)
  symmetric   : area_ratio <= --sym-thr                     (CONTROL)
Samples N_asym asymmetric + N_sym symmetric clips, balanced round-robin across
event_class x source_split, deterministic (seed). Writes a manifest parquet/csv.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", default=str(ROOT / "Datasets/processed/aihub_multi_angle_cctv/20260708/canonical"))
    ap.add_argument("--n-asym", type=int, default=250)
    ap.add_argument("--n-sym", type=int, default=150)
    ap.add_argument("--asym-thr", type=float, default=2.0)
    ap.add_argument("--sym-thr", type=float, default=1.2)
    ap.add_argument("--seed", type=int, default=20260708)
    ap.add_argument("--out", default=str(ROOT / "Datasets/processed/aihub_multi_angle_cctv/20260708/samples/bbox_asymmetry_stratum"))
    args = ap.parse_args()
    C = Path(args.canonical); out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    ef = pd.read_parquet(C / "evidence_frames.parquet")
    ef["area"] = (ef.bbox_x2 - ef.bbox_x1).clip(lower=0) * (ef.bbox_y2 - ef.bbox_y1).clip(lower=0)
    area = ef.groupby(["clip_id", "view"])["area"].mean().unstack("view").dropna()
    clips = pd.read_parquet(C / "clips.parquet")[["clip_id", "event_class", "source_split"]]
    df = area.reset_index().merge(clips, on="clip_id", how="left")
    df["better_view"] = np.where(df["c1"] >= df["c2"], "c1", "c2")
    df["worse_view"] = np.where(df["c1"] >= df["c2"], "c2", "c1")
    df["better_area"] = df[["c1", "c2"]].max(axis=1)
    df["worse_area"] = df[["c1", "c2"]].min(axis=1)
    df["area_ratio"] = df["better_area"] / df["worse_area"].clip(lower=1.0)
    df["stratum"] = np.where(df.area_ratio >= args.asym_thr, "asymmetric",
                             np.where(df.area_ratio <= args.sym_thr, "symmetric", "mid"))

    def balanced_sample(pool: pd.DataFrame, n: int, seed: int) -> pd.DataFrame:
        # round-robin across (event_class, source_split) cells for balance
        rng = np.random.default_rng(seed)
        pool = pool.sample(frac=1.0, random_state=seed).reset_index(drop=True)
        groups = {k: list(g.index) for k, g in pool.groupby(["event_class", "source_split"])}
        order = sorted(groups)
        picked = []
        while len(picked) < n and any(groups[k] for k in order):
            for k in order:
                if groups[k]:
                    picked.append(groups[k].pop(0))
                    if len(picked) >= n:
                        break
        return pool.loc[picked]

    asym = balanced_sample(df[df.stratum == "asymmetric"], args.n_asym, args.seed)
    sym = balanced_sample(df[df.stratum == "symmetric"], args.n_sym, args.seed + 1)
    sel = pd.concat([asym, sym], ignore_index=True)
    sel.to_parquet(out / "stratum_manifest.parquet", index=False)
    sel.to_csv(out / "stratum_manifest.csv", index=False)

    print(f"FULL: {len(df)} clips | asymmetric(ratio>={args.asym_thr})={int((df.stratum=='asymmetric').sum())} "
          f"symmetric(ratio<={args.sym_thr})={int((df.stratum=='symmetric').sum())} mid={int((df.stratum=='mid').sum())}")
    print(f"SAMPLED: asym={len(asym)} sym={len(sym)} total={len(sel)}")
    print("  asym area_ratio: median=%.2f p90=%.2f" % (asym.area_ratio.median(), asym.area_ratio.quantile(.9)))
    print("  event_class balance (sampled):")
    print(sel.groupby(["stratum", "event_class"]).size().unstack("stratum").fillna(0).astype(int).to_string())
    print("  split balance:", sel.groupby(["stratum", "source_split"]).size().to_dict())
    print("  better_view side (should be ~50/50, no c1/c2 bias):", sel.better_view.value_counts().to_dict())
    print("saved ->", out)


if __name__ == "__main__":
    main()
