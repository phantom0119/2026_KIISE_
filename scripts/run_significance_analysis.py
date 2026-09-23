#!/usr/bin/env python3
"""⭐7 Statistical rigor: paired bootstrap 95% CI + paired test for the headline
retrieval comparisons, from the existing per-query metrics parquets."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RES = ROOT / "Datasets/processed"
OUT = ROOT / "2026_KIISE/experiments_expansion/significance"
OUT.mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(20260707)

COMPARISONS = [
    ("VRU", "텍스트 B4 vs B2", "vru_accident/20260706/results/vru_bgem3_faiss_b0_b5",
     "B4_prefilter_vector", "B2_vector_only"),
    ("AI Hub CCTV", "텍스트 B4 vs B2", "aihub_intelligent_cctv/20260706/results/aihub_bgem3_faiss_b0_b5",
     "B4_prefilter_vector", "B2_vector_only"),
    ("VRU", "시각 M4 vs M2", "vru_accident/20260706/results/visual_clip_full_m2_m4",
     "M4_metadata_prefilter_visual", "M2_visual_vector_only"),
    ("AI Hub CCTV", "시각 M4 vs M2", "aihub_intelligent_cctv/20260706/results/visual_clip_full_m2_m4",
     "M4_metadata_prefilter_visual", "M2_visual_vector_only"),
    ("VRU", "rerank RW_t4_v1 vs Equal", "vru_accident/20260706/results/weighted_fusion_rerank_sweep_bgem3_clip",
     "RW_t4_v1", "RW_t1_v1"),
    ("AI Hub CCTV", "rerank RW_t4_v1 vs Equal", "aihub_intelligent_cctv/20260706/results/weighted_fusion_rerank_sweep_bgem3_clip",
     "RW_t4_v1", "RW_t1_v1"),
]
METRIC = "ndcg_at_10"


def paired(df, a, b, metric):
    da = df[df.strategy == a].groupby("query_id")[metric].mean()
    db = df[df.strategy == b].groupby("query_id")[metric].mean()
    idx = da.index.intersection(db.index)
    return da.loc[idx].values, db.loc[idx].values


def boot_ci_diff(x, y, n=5000):
    d = x - y
    m = len(d)
    idx = RNG.integers(0, m, size=(n, m))
    means = d[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    # two-sided bootstrap p-value for mean diff != 0
    p = 2 * min((means <= 0).mean(), (means >= 0).mean())
    return d.mean(), lo, hi, max(p, 1.0 / n)


def wilcoxon_p(x, y):
    """Wilcoxon signed-rank two-sided p (normal approx), no scipy needed."""
    d = x - y
    d = d[d != 0]
    n = len(d)
    if n == 0:
        return 1.0
    r = pd.Series(np.abs(d)).rank().values
    W = r[d > 0].sum()
    mu = n * (n + 1) / 4
    sigma = np.sqrt(n * (n + 1) * (2 * n + 1) / 24)
    if sigma == 0:
        return 1.0
    z = (W - mu) / sigma
    # two-sided normal tail
    from math import erf, sqrt
    p = 2 * (1 - 0.5 * (1 + erf(abs(z) / sqrt(2))))
    return min(max(p, 0.0), 1.0)


def main():
    rows = []
    for ds, name, path, a, b in COMPARISONS:
        f = RES / path / "metrics_by_query.parquet"
        if not f.exists():
            rows.append({"dataset": ds, "comparison": name, "note": "MISSING"}); continue
        df = pd.read_parquet(f)
        if not {a, b}.issubset(set(df.strategy.unique())):
            rows.append({"dataset": ds, "comparison": name, "note": f"strategy missing {set([a,b])-set(df.strategy.unique())}"}); continue
        x, y = paired(df, a, b, METRIC)
        mean_d, lo, hi, pboot = boot_ci_diff(x, y)
        pw = wilcoxon_p(x, y)
        win = float((x > y).mean())
        rows.append({"dataset": ds, "comparison": name, "n": len(x),
                     f"{a}_mean": round(float(x.mean()), 4), f"{b}_mean": round(float(y.mean()), 4),
                     "delta_nDCG": round(float(mean_d), 4), "CI95_lo": round(float(lo), 4), "CI95_hi": round(float(hi), 4),
                     "ci_excludes_0": bool(lo > 0 or hi < 0), "wilcoxon_p": float(f"{pw:.2e}"),
                     "boot_p": float(f"{pboot:.2e}"), "win_rate": round(win, 3)})
    out = pd.DataFrame(rows)
    out.to_csv(OUT / "significance_table.csv", index=False)
    print(out.to_string(index=False))
    # markdown table for the paper
    md = ["**<표> Headline 비교의 통계적 유의성 (paired, metric=nDCG@10)**", "",
          "| Dataset | 비교 | n | Δ nDCG@10 | 95% CI | CI≠0 | Wilcoxon p | 승률 |",
          "|---|---|---:|---:|---|:--:|---:|---:|"]
    for r in rows:
        if r.get("note"):
            continue
        md.append(f"| {r['dataset']} | {r['comparison']} | {r['n']} | {r['delta_nDCG']:+.4f} | "
                  f"[{r['CI95_lo']:.3f}, {r['CI95_hi']:.3f}] | {'O' if r['ci_excludes_0'] else 'X'} | "
                  f"{r['wilcoxon_p']:.1e} | {r['win_rate']:.2f} |")
    (OUT / "significance_table.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\nsaved ->", OUT)


if __name__ == "__main__":
    main()
