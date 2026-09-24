#!/usr/bin/env python3
"""G1 verdict per the pre-registered rule (G1_DECISION_RULE.md).

Inputs : g1/<C>/method_recall/recall_{natural,random0..2,matched}.parquet
         g1/<C>/hardness_natural/hardness_v5.1_1000.json
         g1/<C>/hardness_matched/hardness_v5.1_1000.json
Outputs: g1/G1_REPORT.md + g1/g1_stats.json

Primary : Delta_H(method,corpus) = mean recall(natural) - mean recall(matched)
Inference: two-sample cluster bootstrap (natural cluster=predicate, matched
           cluster=condition-group), 5,000 reps, 95% CI. SESOI = 0.05.
Manipulation check: 1-Wasserstein(PostHardness_nat, PostHardness_matched)
           must be <= 0.5 * std(PostHardness_nat), else verdict withheld.
Sanity  : Delta_R(natural - random0) must replicate the known collapse.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

P0DIR = Path(__file__).resolve().parents[1]
G1 = P0DIR / "g1"
BOOT = 5000
SESOI = 0.05
RNG = np.random.default_rng(20260805)
METHODS = ["postfilter_hnsw_K4x", "single_stage_ivf_np8", "single_stage_ivf_np32"]


def cluster_boot_diff(a: pd.DataFrame, b: pd.DataFrame):
    """mean(a.recall) - mean(b.recall), cluster bootstrap CI."""
    ca = [g.recall.to_numpy() for _, g in a.groupby("cluster")]
    cb = [g.recall.to_numpy() for _, g in b.groupby("cluster")]
    point = a.recall.mean() - b.recall.mean()
    diffs = np.empty(BOOT)
    na, nb = len(ca), len(cb)
    for i in range(BOOT):
        sa = np.concatenate([ca[j] for j in RNG.integers(0, na, na)])
        sb = np.concatenate([cb[j] for j in RNG.integers(0, nb, nb)])
        diffs[i] = sa.mean() - sb.mean()
    return float(point), float(np.percentile(diffs, 2.5)), float(np.percentile(diffs, 97.5))


def main():
    stats = {"sesoi": SESOI, "boot": BOOT, "corpora": {}}
    lines = ["# G1 판정 보고서 — 사전 등록 규칙(G1_DECISION_RULE.md) 적용",
             "", f"생성: 자동 (g1_analyze.py), bootstrap {BOOT}회, SESOI {SESOI}", ""]
    pass_votes, rank_flips = [], []

    for C in ["A", "B"]:
        MR = G1 / C / "method_recall"
        arms = {a: pd.read_parquet(MR / f"recall_{a}.parquet")
                for a in ["natural", "random0", "random1", "random2", "matched"]
                if (MR / f"recall_{a}.parquet").exists()}
        if "matched" not in arms:
            print(f"[{C}] matched arm missing — cannot judge")
            continue
        hn = json.load(open(G1 / C / "hardness_natural" / "hardness_v5.1_1000.json"))
        hm = json.load(open(G1 / C / "hardness_matched" / "hardness_v5.1_1000.json"))
        ph_n = np.array([r["Post_Hardness"] for r in hn])
        ph_m = np.array([r["Post_Hardness"] for r in hm])
        w1 = float(np.abs(np.sort(ph_n) - np.sort(ph_m[: len(ph_n)])).mean()) \
            if len(ph_m) >= len(ph_n) else \
            float(np.abs(np.sort(ph_n[: len(ph_m)]) - np.sort(ph_m)).mean())
        w1_limit = 0.5 * float(ph_n.std())
        manip_ok = w1 <= w1_limit

        cres = {"wasserstein": w1, "wasserstein_limit": w1_limit,
                "manipulation_ok": bool(manip_ok), "methods": {}}
        lines += [f"## 코퍼스 {C}", "",
                  f"- 난이도 매칭 조작 확인: 1-Wasserstein={w1:.4f} "
                  f"(한계 {w1_limit:.4f}) → {'통과' if manip_ok else '실패(판정 보류 사유)'}",
                  f"- 자연 Post_Hardness: mean {ph_n.mean():.3f} std {ph_n.std():.3f} / "
                  f"매칭: mean {ph_m.mean():.3f} std {ph_m.std():.3f}", "",
                  "| method | R(자연) | R(매칭) | Δ_H [95% CI] | R(무작위) | Δ_R | 판정 기여 |",
                  "|---|---|---|---|---|---|---|"]

        for meth in METHODS:
            nat = arms["natural"][arms["natural"].method == meth]
            mat = arms["matched"][arms["matched"].method == meth]
            rnd = arms["random0"][arms["random0"].method == meth]
            dh, lo, hi = cluster_boot_diff(nat, mat)
            dr = float(nat.recall.mean() - rnd.recall.mean())
            sig = (abs(dh) >= SESOI) and (lo > 0 or hi < 0)
            cres["methods"][meth] = {
                "recall_natural": float(nat.recall.mean()),
                "recall_matched": float(mat.recall.mean()),
                "recall_random0": float(rnd.recall.mean()),
                "delta_H": dh, "ci": [lo, hi], "delta_R": dr,
                "meets_rule": bool(sig)}
            if manip_ok:
                pass_votes.append(sig)
            lines.append(f"| {meth} | {nat.recall.mean():.4f} | {mat.recall.mean():.4f} | "
                         f"{dh:+.4f} [{lo:+.4f},{hi:+.4f}] | {rnd.recall.mean():.4f} | "
                         f"{dr:+.4f} | {'O' if sig else 'X'}{'' if manip_ok else ' (보류)'} |")

        rank_n = tuple(pd.Series({m: cres["methods"][m]["recall_natural"] for m in METHODS})
                       .sort_values().index)
        rank_m = tuple(pd.Series({m: cres["methods"][m]["recall_matched"] for m in METHODS})
                       .sort_values().index)
        cres["rank_natural"], cres["rank_matched"] = list(rank_n), list(rank_m)
        rank_flips.append(rank_n != rank_m)
        lines += ["", f"- 방법 순위(오름차순): 자연 {rank_n} / 매칭 {rank_m} "
                  f"→ {'뒤집힘' if rank_n != rank_m else '동일'}", ""]
        stats["corpora"][C] = cres

    manip_all_ok = all(s.get("manipulation_ok", False) for s in stats["corpora"].values())
    any_sig = any(pass_votes)
    flip_consistent = len(rank_flips) == 2 and all(rank_flips)
    if not stats["corpora"]:
        verdict = "판정 불능(데이터 없음)"
    elif not manip_all_ok:
        verdict = ("판정 보류: 난이도 매칭 실패 코퍼스 존재 — HCBGen 설정 재시도 필요 "
                   "(사전 규칙의 판정 불능 조건)")
    elif any_sig or flip_consistent:
        verdict = ("G1 통과: 난이도 분포를 맞춘 합성 워크로드로 설명되지 않는 "
                   "자연 워크로드의 추가 어려움이 잔존")
    else:
        verdict = "G1 실패: 난이도 매칭으로 자연-합성 차이가 소멸 — 자연 워크로드 축 중단"
    stats["verdict"] = verdict
    lines += ["## 종합 판정", "", f"**{verdict}**", "",
              f"- SESOI 충족 방법 수: {sum(pass_votes)}/{len(pass_votes)}",
              f"- 순위 뒤집힘(두 코퍼스 일관): {flip_consistent}"]

    (G1 / "G1_REPORT.md").write_text("\n".join(lines))
    (G1 / "g1_stats.json").write_text(json.dumps(stats, indent=2))
    print(verdict)
    print("saved:", G1 / "G1_REPORT.md")


if __name__ == "__main__":
    main()
