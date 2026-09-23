#!/usr/bin/env python3
"""B-4 stage 3 [prereg 420 Amendment 5 + 5a]: confirmatory analysis.

Declared BEFORE confirmatory computation (Amendment 5a):
  CONFIRMATORY family = {m1-graph, w2-sweeping} x {A, B} = 4 tests,
  NATURAL predicates only (A 24, B 22; composites -> descriptive).
    m1-graph: Milvus rows with filtered-out ratio (1-s) < 0.93 (knowhere BF
              boundary; declared constant, empirically bracketed (0.923,0.934]).
    w2: Weaviate filterStrategy=sweeping + flatSearchCutoff=0.
  Per test: paired Δ = recall(control) − recall(real) per predicate;
  mean Δ, predicate-bootstrap 95% CI (B=10,000, seed 20260712), Wilcoxon,
  Holm over the 4-family. HEADLINE requires BOTH the predicate bootstrap AND
  the facet-family cluster bootstrap CI to exclude 0 [5a(4)].
  DESCRIPTIVE lanes (혼입 금지): m1-BF, w1 (acorn+cutoff40000: flat-fallback
  coverage), w3 (acorn+cutoff0: ACORN mitigation), composites everywhere.
  Secondary: Spearman rho of Δ vs gt_cluster_med_rank per lane.
F7: two-seed spot-check + r=6-draw control distribution (SD/range) per method.

Run (kiise-vlmdb env): analyze_engine_replication.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, wilcoxon

R2 = Path(__file__).resolve().parents[1]
OUT = R2 / "paper_assets" / "20260712_engine_replication"
PB = R2 / "paper_assets" / "20260710_pillarB"
RNG = np.random.default_rng(20260712)
BF_BOUNDARY = 0.93  # knowhere kHnswSearchKnnBFFilterThreshold (declared, 5a(1))


def facet_family(pair: str) -> str:
    p = pair.lower()
    for fam, prefix in [("location", "location"), ("date", "date"),
                        ("time_of_day", "time_of_day"), ("signal", "sig_has"),
                        ("veh_density", "veh_density"), ("hour", "hour")]:
        if p.startswith(prefix):
            return fam
    return "other"


def paired(df):
    real = df[df.kind != "control"].set_index("pair")
    ctrl = df[df.kind == "control"].set_index("pair")
    common = real.index.intersection(ctrl.index)
    d = pd.DataFrame({
        "pair": common,
        "kind": real.loc[common, "kind"].values,
        "recall_real": real.loc[common, "recall_at_10"].values,
        "recall_ctrl": ctrl.loc[common, "recall_at_10"].values,
        "gt_rank": real.loc[common, "gt_cluster_med_rank"].values,
        "selectivity": real.loc[common, "selectivity"].values,
    }).reset_index(drop=True)
    d["delta"] = d.recall_ctrl - d.recall_real
    d["family"] = d.pair.map(facet_family)
    return d


def boot_ci(x, B=10_000):
    x = np.asarray(x)
    idx = RNG.integers(0, len(x), size=(B, len(x)))
    m = x[idx].mean(axis=1)
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def family_boot_ci(d, B=10_000):
    fams = d.family.unique()
    groups = {f: d[d.family == f].delta.values for f in fams}
    means = []
    for _ in range(B):
        pick = RNG.choice(fams, len(fams), replace=True)
        means.append(np.concatenate([groups[f] for f in pick]).mean())
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def one_test(d, engine, lane, corpus, confirmatory):
    if len(d) < 5:
        return {"engine": engine, "lane": lane, "corpus": corpus,
                "confirmatory": confirmatory, "n_pairs": len(d),
                "note": "n<5 — reported, not tested"}
    lo, hi = boot_ci(d.delta)
    flo, fhi = family_boot_ci(d)
    try:
        p = float(wilcoxon(d.delta, zero_method="wilcox").pvalue)
    except ValueError:
        p = 1.0
    return {"engine": engine, "lane": lane, "corpus": corpus,
            "confirmatory": confirmatory, "n_pairs": len(d),
            "n_families": int(d.family.nunique()),
            "mean_delta": round(float(d.delta.mean()), 4),
            "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
            "fam_ci_lo": round(flo, 4), "fam_ci_hi": round(fhi, 4),
            "wilcoxon_p": p,
            "mean_recall_real": round(float(d.recall_real.mean()), 4),
            "mean_recall_ctrl": round(float(d.recall_ctrl.mean()), 4)}


def main() -> int:
    results, mech = [], []

    for corpus in ["A", "B"]:
        # ---- Milvus m1: split graph vs BF regime [5a(1)] ----
        f = OUT / f"engine_milvus_{corpus}.csv"
        if f.exists():
            df = pd.read_csv(f)
            d = paired(df[df.condition == "m1"])
            d["bf"] = (1 - d.selectivity) >= BF_BOUNDARY
            nat = d[d.kind == "natural"]
            results.append(one_test(nat[~nat.bf], "milvus", "m1-graph", corpus, True))
            results.append(one_test(nat[nat.bf], "milvus", "m1-BF", corpus, False))
            results.append(one_test(d[(d.kind == "composite") & (~d.bf)],
                                    "milvus", "m1-graph-composite", corpus, False))
            g = nat[~nat.bf]
            if len(g) >= 5:
                rho = spearmanr(g.gt_rank, g.delta)
                mech.append({"engine": "milvus", "lane": "m1-graph", "corpus": corpus,
                             "rho": round(float(rho.correlation), 3),
                             "p": round(float(rho.pvalue), 4), "n": len(g)})

        # ---- Weaviate: w1/w3 from chain csv (w2-old relabeled w3), w2 sweep file ----
        wf = OUT / f"engine_weaviate_{corpus}.csv"
        if wf.exists():
            wdf = pd.read_csv(wf)
            for cond_raw, lane in [("w1", "w1-acorn-cutoff40k"), ("w3", "w3-acorn-cutoff0")]:
                sub = wdf[wdf.condition == cond_raw]
                if sub.empty:
                    continue
                d = paired(sub)
                if lane.startswith("w1"):
                    # flat-fallback rows (subset < cutoff) separated [혼입 금지]
                    flat = d[d.selectivity * {"A": 132521, "B": 143830}[corpus] < 40000]
                    hnsw = d[~d.index.isin(flat.index)]
                    results.append({"engine": "weaviate", "lane": "w1-flat-fallback",
                                    "corpus": corpus, "confirmatory": False,
                                    "n_pairs": len(flat),
                                    "mean_recall_real": round(float(flat.recall_real.mean()), 4)
                                    if len(flat) else None,
                                    "note": "engine mitigation: brute-force below cutoff"})
                    results.append(one_test(hnsw[hnsw.kind == "natural"],
                                            "weaviate", lane + "-aboveCutoff", corpus, False))
                else:
                    results.append(one_test(d[d.kind == "natural"], "weaviate", lane,
                                            corpus, False))
                    g = d[d.kind == "natural"]
                    if len(g) >= 5:
                        rho = spearmanr(g.gt_rank, g.delta)
                        mech.append({"engine": "weaviate", "lane": lane, "corpus": corpus,
                                     "rho": round(float(rho.correlation), 3),
                                     "p": round(float(rho.pvalue), 4), "n": len(g)})
        # w2-sweeping: corpus B collected in the main csv (post-amendment runner),
        # corpus A in the _w2sweep suffix file (see relabel note)
        w2_frames = []
        if wf.exists():
            w2_frames.append(pd.read_csv(wf).query("condition == 'w2'"))
        sf = OUT / f"engine_weaviate_{corpus}_w2sweep.csv"
        if sf.exists():
            w2_frames.append(pd.read_csv(sf).query("condition == 'w2'"))
        sdf = pd.concat(w2_frames) if w2_frames else pd.DataFrame()
        if len(sdf):
            d = paired(sdf[sdf.condition == "w2"])
            nat = d[d.kind == "natural"]
            results.append(one_test(nat, "weaviate", "w2-sweeping", corpus, True))
            results.append(one_test(d[d.kind == "composite"],
                                    "weaviate", "w2-sweeping-composite", corpus, False))
            if len(nat) >= 5:
                rho = spearmanr(nat.gt_rank, nat.delta)
                mech.append({"engine": "weaviate", "lane": "w2-sweeping", "corpus": corpus,
                             "rho": round(float(rho.correlation), 3),
                             "p": round(float(rho.pvalue), 4), "n": len(nat)})

    rdf = pd.DataFrame(results)
    conf = rdf[(rdf.confirmatory == True) & rdf.wilcoxon_p.notna()]  # noqa: E712
    m = len(conf)
    holm = {}
    running = 0.0
    for rank, i in enumerate(conf.wilcoxon_p.sort_values().index):
        adj = min(1.0, (m - rank) * conf.loc[i, "wilcoxon_p"])
        running = max(running, adj)
        holm[i] = running
    rdf["holm_p"] = rdf.index.map(holm)
    rdf["holm_sig_05"] = rdf.holm_p < 0.05
    rdf["headline_pass"] = (rdf.holm_sig_05 & (rdf.ci_lo > 0) & (rdf.fam_ci_lo > 0))
    rdf.to_csv(OUT / "B4_results.csv", index=False)
    pd.DataFrame(mech).to_csv(OUT / "B4_mechanism.csv", index=False)
    print(rdf.to_string(index=False))
    print(pd.DataFrame(mech).to_string(index=False))

    # ---------------- F7: seed spot-check + replicate distribution ----------------
    f7 = []
    for corpus in ["A", "B"]:
        og = PB / f"filtered_ann_real_{corpus}.csv"
        sc = OUT / f"faiss_seedcheck_{corpus}.csv"
        rp = OUT / f"f7_replicates_{corpus}.csv"
        if not (og.exists() and sc.exists()):
            continue
        old = pd.read_csv(og)
        oc = old[old.predicate.str.startswith("CTRL")].copy()
        oc["pair"] = oc.predicate.str.split("|").str[1]
        draws = [oc[["pair", "method", "recall_at_10"]].assign(draw="b1_20260710")]
        new = pd.read_csv(sc).rename(columns={"recall_at_10_newseed": "recall_at_10"})
        draws.append(new[["pair", "method", "recall_at_10"]].assign(draw="r0_20260712"))
        if rp.exists():
            rep = pd.read_csv(rp)
            rep["draw"] = "r" + rep.replicate.astype(str)
            draws.append(rep[["pair", "method", "recall_at_10", "draw"]])
        alld = pd.concat(draws)
        for meth, g in alld.groupby("method"):
            piv = g.pivot_table(index="pair", columns="draw", values="recall_at_10")
            piv = piv.dropna()
            if piv.empty:
                continue
            sd = piv.std(axis=1, ddof=1)
            rng_ = piv.max(axis=1) - piv.min(axis=1)
            f7.append({"corpus": corpus, "method": meth, "n_pairs": len(piv),
                       "n_draws": piv.shape[1],
                       "mean_ctrl_recall": round(float(piv.values.mean()), 4),
                       "mean_sd_across_draws": round(float(sd.mean()), 4),
                       "max_sd": round(float(sd.max()), 4),
                       "mean_range": round(float(rng_.mean()), 4),
                       "max_range": round(float(rng_.max()), 4)})
    f7df = pd.DataFrame(f7)
    f7df.to_csv(OUT / "B4_f7_seed_sensitivity.csv", index=False)
    print(f7df.to_string(index=False))
    print(f"[saved] {OUT}/B4_results.csv, B4_mechanism.csv, B4_f7_seed_sensitivity.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
