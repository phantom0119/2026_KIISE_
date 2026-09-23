#!/usr/bin/env python3
"""P1 submission figures (B&W, bootstrap-CI) for the KIISE DBR v1 manuscript.

Outputs (PNG 220dpi + PDF) to paper_assets/20260707_submission_figures/:
  - fig_difficulty_gain_v2      : metadata-prefilter gain concentrates in medium/strong (visual M2->M4), weak delta = 0 disclosed, bootstrap 95% CI.
  - fig_evidence_gap_sweep_v2   : (a) top-k Hit != rank-1 evidence gap + rerank shift; (b) full 7-point weighted-RRF Hit@1 sweep with bootstrap CI.

All numbers come from real metrics_summary.csv / metrics_by_query.parquet / service_packet_summary.csv.
Black-and-white safe: grayscale fills + hatch patterns + distinct markers (no hue dependence).
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

for _c in ("NanumGothic", "NanumBarunGothic"):
    try:
        font_manager.findfont(_c, fallback_to_default=False)
        plt.rcParams["font.family"] = _c
        break
    except Exception:
        continue
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["savefig.dpi"] = 220

ROOT = Path(__file__).resolve().parents[3]
RES = ROOT / "Datasets" / "processed"
OUT = ROOT / "2026_KIISE" / "paper_assets" / "20260707_submission_figures"
OUT.mkdir(parents=True, exist_ok=True)

DS = {"vru_accident": "VRU-Accident", "aihub_intelligent_cctv": "AI Hub 지능형 CCTV"}
RNG = np.random.default_rng(20260707)


def save(fig, name):
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def boot_ci(vals, n=2000, lo=2.5, hi=97.5):
    vals = np.asarray(vals, float)
    if len(vals) == 0:
        return (np.nan, np.nan)
    idx = RNG.integers(0, len(vals), size=(n, len(vals)))
    means = vals[idx].mean(axis=1)
    return np.percentile(means, [lo, hi])


# ---------------------------------------------------------------------------
# 그림 2 (P1): difficulty-stratified metadata-prefilter gain — VISUAL M2 vs M4
# ---------------------------------------------------------------------------
def fig_difficulty_gain():
    diffs = ["weak", "medium", "strong"]
    dlabel = {"weak": "약함(weak)", "medium": "보통(medium)", "strong": "강함(strong)"}
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.7), sharey=True)
    for ax, (ds, title) in zip(axes, DS.items()):
        summ = pd.read_csv(RES / ds / "20260706/results/visual_clip_full_m2_m4/metrics_summary.csv")
        pq = pd.read_parquet(RES / ds / "20260706/results/visual_clip_full_m2_m4/metrics_by_query.parquet")
        m2s, m4s, ci2, ci4, deltas = [], [], [], [], []
        for d in diffs:
            r = summ[summ["difficulty"] == d]
            m2 = float(r[r["strategy"] == "M2_visual_vector_only"]["recall_at_10"])
            m4 = float(r[r["strategy"] == "M4_metadata_prefilter_visual"]["recall_at_10"])
            m2s.append(m2); m4s.append(m4)
            q2 = pq[(pq["strategy"] == "M2_visual_vector_only") & (pq["difficulty"] == d)][["query_id", "recall_at_10"]]
            q4 = pq[(pq["strategy"] == "M4_metadata_prefilter_visual") & (pq["difficulty"] == d)][["query_id", "recall_at_10"]]
            mg = q2.merge(q4, on="query_id", suffixes=("_m2", "_m4"))
            delta = (mg["recall_at_10_m4"] - mg["recall_at_10_m2"]).values
            lo, hi = boot_ci(delta)
            deltas.append((delta.mean(), lo, hi))
            ci2.append(np.subtract(*boot_ci(q2["recall_at_10"].values)[::-1]) / 2 if len(q2) else 0)
            ci4.append(np.subtract(*boot_ci(q4["recall_at_10"].values)[::-1]) / 2 if len(q4) else 0)
        x = np.arange(3); w = 0.36
        b2 = ax.bar(x - w / 2, m2s, w, label="M2 시각 vector-only", facecolor="0.80", edgecolor="black", hatch="///", linewidth=1.1)
        b4 = ax.bar(x + w / 2, m4s, w, label="M4 조건 prefilter + 시각", facecolor="0.35", edgecolor="black", linewidth=1.1)
        for xi, (dm, lo, hi) in zip(x, deltas):
            top = max(m2s[xi], m4s[xi])
            txt = "Δ=0.000" if abs(dm) < 1e-6 else f"Δ={dm:+.3f}\n[{lo:.3f},{hi:.3f}]"
            ax.annotate(txt, (xi, top + 0.03), ha="center", va="bottom", fontsize=8.2,
                        fontweight="bold" if abs(dm) > 1e-6 else "normal", color="black")
        ax.set_xticks(x); ax.set_xticklabels([dlabel[d] for d in diffs])
        ax.set_title(f"{title}", fontsize=12, fontweight="bold")
        ax.set_ylim(0, 1.12)
        ax.grid(axis="y", alpha=0.3, linewidth=0.6)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("Recall@10", fontsize=11)
    axes[0].legend(loc="upper left", fontsize=9, framealpha=0.9)
    fig.suptitle("metadata prefilter의 이득은 조건이 강한 질의에 집중된다 (weak Δ=0)", fontsize=13, fontweight="bold", y=1.02)
    save(fig, "fig_difficulty_gain_v2")


# ---------------------------------------------------------------------------
# 그림 5 (P1): (a) top-k Hit != rank-1 gap + rerank ; (b) full RRF sweep
# ---------------------------------------------------------------------------
def fig_evidence_gap_sweep():
    fig, (axA, axB) = plt.subplots(1, 2, figsize=(11.2, 4.7))

    # (a) gap dumbbell: text_metadata query_type
    rows = []
    for ds, title in DS.items():
        for strat, name in [("m6_im1_top5", "Equal"), ("rw_t4_v1_im1_top5", "Reranked")]:
            sp = pd.read_csv(RES / ds / f"20260706/service_testbed/{strat}/service_packet_summary.csv")
            r = sp[sp["query_type"] == "text_metadata"].iloc[0]
            rows.append((title, name, float(r["top1_relevant_rate"]), float(r["hit_at_k"])))
    ylabels, y = [], 0
    yticks = []
    for title in DS.values():
        for name in ["Equal", "Reranked"]:
            rec = next(r for r in rows if r[0] == title and r[1] == name)
            _, _, top1, hit5 = rec
            mk = "s" if name == "Reranked" else "o"
            axA.plot([top1, hit5], [y, y], "-", color="0.4", lw=2, zorder=1)
            axA.scatter([top1], [y], marker=mk, s=70, facecolor="white", edgecolor="black", linewidth=1.5, zorder=3, label="Top-1 relevant" if y == 0 else None)
            axA.scatter([hit5], [y], marker=mk, s=70, facecolor="black", edgecolor="black", linewidth=1.5, zorder=3, label="Hit@5" if y == 0 else None)
            axA.annotate(f"{top1:.3f}", (top1, y), textcoords="offset points", xytext=(-4, 7), ha="right", fontsize=7.6)
            axA.annotate(f"{hit5:.3f}", (hit5, y), textcoords="offset points", xytext=(4, 7), ha="left", fontsize=7.6)
            ylabels.append(f"{title.split()[0]} · {name}"); yticks.append(y)
            y += 1
        y += 0.5
    axA.set_yticks(yticks); axA.set_yticklabels(ylabels, fontsize=9)
    axA.set_xlabel("비율 (텍스트 질의 기준)", fontsize=10)
    axA.set_xlim(0.6, 1.03)
    axA.set_title("(a) top-k Hit ≠ rank-1 evidence 격차\n(○ Equal, □ Reranked; 흰=Top-1, 검정=Hit@5)", fontsize=10.5, fontweight="bold")
    axA.grid(axis="x", alpha=0.3, linewidth=0.6)
    for s in ("top", "right"):
        axA.spines[s].set_visible(False)
    axA.invert_yaxis()

    # (b) full 7-point sweep Hit@1 with bootstrap CI
    order = ["RW_t4_v1", "RW_t3_v1", "RW_t2_v1", "RW_t1_v1", "RW_t1_v2", "RW_t1_v3", "RW_t1_v4"]
    xlab = ["4:1", "3:1", "2:1", "1:1", "1:2", "1:3", "1:4"]
    markers = {"vru_accident": "o", "aihub_intelligent_cctv": "s"}
    for ds, title in DS.items():
        summ = pd.read_csv(RES / ds / "20260706/results/weighted_fusion_rerank_sweep_bgem3_clip/metrics_summary.csv")
        pq = pd.read_parquet(RES / ds / "20260706/results/weighted_fusion_rerank_sweep_bgem3_clip/metrics_by_query.parquet")
        ys, los, his = [], [], []
        for st in order:
            ys.append(float(summ[(summ["strategy"] == st) & (summ.get("difficulty", "all") == "all")]["hit_at_1"]) if "difficulty" in summ.columns else float(summ[summ["strategy"] == st]["hit_at_1"]))
            vals = pq[pq["strategy"] == st]["hit_at_1"].values
            lo, hi = boot_ci(vals)
            los.append(lo); his.append(hi)
        xs = np.arange(len(order))
        axB.plot(xs, ys, "-", marker=markers[ds], color="black", mfc="white" if ds == "vru_accident" else "black",
                 ms=7, lw=1.8, label=title)
        axB.fill_between(xs, los, his, color="0.6", alpha=0.25, linewidth=0)
    axB.axvline(0, color="0.5", ls=":", lw=1)
    axB.annotate("RW_t4_v1\n(최적)", (0, axB.get_ylim()[0]), xytext=(0.15, 0.42), fontsize=8, color="0.2")
    axB.set_xticks(range(len(order))); axB.set_xticklabels(xlab)
    axB.set_xlabel("가중치 text:visual", fontsize=10)
    axB.set_ylabel("Hit@1", fontsize=10)
    axB.set_title("(b) 가중 RRF sweep: 텍스트 우세 최적\n(음영 = bootstrap 95% CI)", fontsize=10.5, fontweight="bold")
    axB.legend(loc="lower left", fontsize=9)
    axB.grid(alpha=0.3, linewidth=0.6)
    for s in ("top", "right"):
        axB.spines[s].set_visible(False)
    save(fig, "fig_evidence_gap_sweep_v2")


if __name__ == "__main__":
    fig_difficulty_gain()
    fig_evidence_gap_sweep()
    print("done →", OUT)
