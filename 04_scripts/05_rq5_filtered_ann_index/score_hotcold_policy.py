#!/usr/bin/env python3
"""P3 (DB contribution) — hot/cold predicate policy: when to build a local/partial
index vs use the global index + postfilter. Consumes P2's pgvector_partial_vs_global.csv.

Two decision axes per predicate p (selectivity s):
  QUALITY  : does global+WHERE meet a recall bar? If global recall collapses
             (postfilter over-fetch at high selectivity, cf. 620), a partial/local
             index is REQUIRED regardless of query volume.
  AMORTIZE : a partial index costs B_p seconds to build once, then saves
             (L_global - L_partial) ms per query. Break-even query count
             N* = 1000*B_p / (L_global - L_partial). A "hot" predicate (queried
             > N* before the next reindex) should get a local index; a "cold" one
             stays on global + postfilter.

Rule emitted: build a local index for p iff  recall_global(p) < R_bar  (quality-
forced)  OR  expected_queries(p) > N*(p)  (amortized). Otherwise global+postfilter.

Run: Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/04_scripts/score_hotcold_policy.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260713_db_design"
R_BAR = 0.95  # recall bar the served path must meet


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="pgvector_partial_vs_global.csv")
    ap.add_argument("--out-prefix", default="hotcold")
    args = ap.parse_args()
    df = pd.read_csv(OUT / args.csv)
    rows = []
    for (pred, s), g in df.groupby(["predicate", "selectivity"]):
        part = g[g.strategy == "partial_local"]
        grelax = g[g.strategy == "global_where_relaxed_order"]
        goff = g[g.strategy == "global_where_off"]
        if part.empty or grelax.empty:
            continue
        part = part.iloc[0]; grelax = grelax.iloc[0]
        # global "served" path = relaxed_order (the one that keeps recall up)
        Lg, Rg = float(grelax.p50_ms), float(grelax.recall_at_10)
        Lp, Rp = float(part.p50_ms), float(part.recall_at_10)
        Bp = float(part.build_s)
        gain = Lg - Lp  # ms saved per query by the local index
        n_star = (1000.0 * Bp / gain) if gain > 1e-6 else float("inf")
        quality_forced = Rg < R_BAR
        rows.append({
            "predicate": pred, "selectivity": s,
            "recall_global_relaxed": round(Rg, 4), "recall_global_off": round(float(goff.iloc[0].recall_at_10), 4) if not goff.empty else None,
            "recall_partial": round(Rp, 4),
            "L_global_ms": round(Lg, 3), "L_partial_ms": round(Lp, 3),
            "build_partial_s": round(Bp, 2), "partial_index_mb": round(float(part.index_mb), 2),
            "latency_gain_ms": round(gain, 3),
            "breakeven_queries_Nstar": (round(n_star, 1) if np.isfinite(n_star) else None),
            "quality_forced_local": bool(quality_forced),
            "policy": ("LOCAL (quality-forced)" if quality_forced
                       else ("LOCAL if hot: >%.0f q" % n_star if np.isfinite(n_star) and n_star >= 0
                             else "GLOBAL+postfilter (local never pays on latency)")),
        })
    pol = pd.DataFrame(rows).sort_values("selectivity")
    pol.to_csv(OUT / f"{args.out_prefix}_policy.csv", index=False)

    # summary rule
    quality_forced_preds = pol[pol.quality_forced_local]
    summary = {
        "R_bar": R_BAR,
        "n_predicates": int(len(pol)),
        "quality_forced_count": int(len(quality_forced_preds)),
        "quality_forced_selectivities": quality_forced_preds.selectivity.tolist(),
        "median_breakeven_when_amortizable": (
            float(np.nanmedian([r for r in pol.breakeven_queries_Nstar.dropna()]))
            if pol.breakeven_queries_Nstar.notna().any() else None),
        "rule": "build LOCAL/partial index for p iff recall_global(p) < R_bar (quality) "
                "OR expected_queries(p) > N*(p) (amortize); else GLOBAL + postfilter.",
    }
    (OUT / f"{args.out_prefix}_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    print("=== HOT/COLD PARTIAL-INDEX POLICY ===")
    cols = ["selectivity", "recall_global_relaxed", "recall_partial", "L_global_ms",
            "L_partial_ms", "build_partial_s", "breakeven_queries_Nstar", "policy"]
    print(pol[cols].to_string(index=False))
    print("\nquality-forced (global recall < %.2f): selectivities %s" % (R_BAR, summary["quality_forced_selectivities"]))
    print(f"[saved] {OUT}/{args.out_prefix}_policy.csv , {args.out_prefix}_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
