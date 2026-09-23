#!/usr/bin/env python3
"""Pillar B-1 analysis per prereg 420 [AMD-M7/M9] — declared BEFORE significance:

CONFIRMATORY FAMILY (Holm within corpus):
  s-bands (pre-specified): low s<0.05 / mid 0.05<=s<0.25 / high s>=0.25
  method pairs (pre-specified):
    P1 prefilter_hnsw_ef64        vs postfilter_hnsw_K4x
    P2 prefilter_hnsw_ef64        vs single_stage_ivf_batch_np32
    P3 postfilter_hnsw_K4x        vs single_stage_ivf_batch_np32
  test: per-predicate paired dRecall@10 (real predicates only), Wilcoxon signed-rank
        (normal approx) + predicate-level bootstrap CI(5,000); Holm over the family.

M9 PREREGISTERED PAIRED COMPARISON (Holm within corpus, 5 tests):
  per core method: real vs same-s random control, paired by predicate.

MECHANISM (descriptive): Spearman rho between per-predicate recall deficit
  (control - real) and gt_cluster_med_rank covariate.

Everything else = exploratory (CI only, no stars).
Output: paper_assets/20260710_pillarB/B1_analysis_<corpus>.{md,csv}
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parents[1] / "paper_assets" / "20260710_pillarB"
RNG = np.random.default_rng(20260710)

PAIRS = [("prefilter_hnsw_ef64", "postfilter_hnsw_K4x"),
         ("prefilter_hnsw_ef64", "single_stage_ivf_batch_np32"),
         ("postfilter_hnsw_K4x", "single_stage_ivf_batch_np32")]
CORE = ["prefilter_flat", "prefilter_hnsw_ef64", "postfilter_hnsw_K4x",
        "single_stage_ivf_batch_np8", "single_stage_ivf_batch_np32"]


def band(s):
    return "low(<0.05)" if s < 0.05 else ("mid(0.05-0.25)" if s < 0.25 else "high(>=0.25)")


def wilcoxon_p(d):
    d = np.asarray(d, float); d = d[d != 0]
    n = len(d)
    if n < 3:
        return np.nan
    r = pd.Series(np.abs(d)).rank().to_numpy()
    W = r[d > 0].sum()
    mu, sd = n * (n + 1) / 4, np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    from math import erf, sqrt
    z = (W - mu) / sd
    return 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))


def boot_ci(d, n=5000):
    d = np.asarray(d, float)
    idx = RNG.integers(0, len(d), size=(n, len(d)))
    m = d[idx].mean(axis=1)
    return float(d.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def holm(pvals):
    order = np.argsort(pvals)
    m = len(pvals)
    adj = np.empty(m)
    running = 0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def main() -> int:
    corpus = sys.argv[1] if len(sys.argv) > 1 else "A"
    df = pd.read_csv(OUT / f"filtered_ann_real_{corpus}.csv")
    real = df[df.kind.isin(["natural", "composite"])].copy()
    ctrl = df[df.kind.eq("control")].copy()
    ctrl["predicate_base"] = ctrl.predicate.str.split("|").str[1]
    real["band"] = real.selectivity.map(band)
    piv = real.pivot_table(index=["predicate", "band"], columns="method",
                           values="recall_at_10")
    lines = [f"# B-1 확증 분석 — 코퍼스 {corpus} (prereg 420 [AMD-M7/M9])", ""]

    # ---- confirmatory family ----
    fam = []
    for bd in sorted(piv.index.get_level_values("band").unique()):
        sub = piv.xs(bd, level="band")
        for a, b in PAIRS:
            if a not in sub or b not in sub:
                continue
            d = (sub[a] - sub[b]).dropna()
            if len(d) < 3:
                fam.append({"band": bd, "pair": f"{a} - {b}", "n": len(d),
                            "delta": round(float(d.mean()), 4) if len(d) else np.nan,
                            "ci": "n<3", "p": np.nan})
                continue
            m, lo, hi = boot_ci(d.values)
            fam.append({"band": bd, "pair": f"{a} - {b}", "n": len(d),
                        "delta": round(m, 4), "ci": f"[{lo:.3f},{hi:.3f}]",
                        "p": wilcoxon_p(d.values)})
    famdf = pd.DataFrame(fam)
    ok = famdf.p.notna()
    famdf.loc[ok, "p_holm"] = holm(famdf.loc[ok, "p"].values)
    famdf["sig"] = famdf.p_holm.map(lambda x: "✓" if pd.notna(x) and x < 0.05 else "")
    lines += ["## 확증 가족: s-밴드 × 방법쌍 ΔRecall@10 (Holm 보정)", "",
              famdf.to_string(index=False), ""]

    # ---- M9 real vs control ----
    m9 = []
    cpiv = ctrl.pivot_table(index="predicate_base", columns="method", values="recall_at_10")
    rpiv = real.pivot_table(index="predicate", columns="method", values="recall_at_10")
    common = rpiv.index.intersection(cpiv.index)
    for meth in CORE:
        if meth not in rpiv or meth not in cpiv:
            continue
        d = (cpiv.loc[common, meth] - rpiv.loc[common, meth]).dropna()
        m, lo, hi = boot_ci(d.values)
        m9.append({"method": meth, "n_pairs": len(d),
                   "ctrl_minus_real": round(m, 4), "ci": f"[{lo:.3f},{hi:.3f}]",
                   "p": wilcoxon_p(d.values)})
    m9df = pd.DataFrame(m9)
    ok9 = m9df.p.notna()                      # Δ≡0 rows are untestable, excluded from Holm
    m9df.loc[ok9, "p_holm"] = holm(m9df.loc[ok9, "p"].values)
    m9df["sig"] = m9df.p_holm.map(lambda x: "✓" if pd.notna(x) and x < 0.05 else "")
    m9df.loc[~ok9, "sig"] = "(Δ≡0, no test)"
    lines += ["## M9: 동일-s 랜덤 대조군 − 실제 predicate (recall 과대평가량, Holm)", "",
              m9df.to_string(index=False), ""]

    # ---- mechanism (descriptive) ----
    mech = []
    cov = real.pivot_table(index="predicate", values="gt_cluster_med_rank", aggfunc="first")
    for meth in ["postfilter_hnsw_K4x", "single_stage_ivf_batch_np32"]:
        deficit = (cpiv.loc[common, meth] - rpiv.loc[common, meth]).dropna()
        cc = cov.loc[deficit.index, "gt_cluster_med_rank"]
        rho = pd.Series(deficit.values).rank().corr(pd.Series(cc.values).rank())
        mech.append({"method": meth, "spearman_rho(deficit, gt_cluster_rank)": round(float(rho), 3),
                     "n": len(deficit)})
    lines += ["## 메커니즘(기술): recall 결손 ↔ GT 군집 심도(전역 exact 중앙순위)", "",
              pd.DataFrame(mech).to_string(index=False), ""]

    # ---- descriptive per-method summary ----
    summ = real.groupby("method")[["recall_at_10", "p50_ms", "p95_ms"]].mean().round(4)
    csumm = ctrl.groupby("method")[["recall_at_10"]].mean().round(4).rename(
        columns={"recall_at_10": "recall_ctrl"})
    lines += ["## 방법별 평균 (실제 predicate / 대조군 recall 병기 — 탐색적)", "",
              summ.join(csumm).to_string(), ""]

    text = "\n".join(lines)
    (OUT / f"B1_analysis_{corpus}.md").write_text(text, encoding="utf-8")
    famdf.to_csv(OUT / f"B1_confirmatory_{corpus}.csv", index=False)
    m9df.to_csv(OUT / f"B1_m9_control_{corpus}.csv", index=False)
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
