#!/usr/bin/env python3
"""Evaluate the answer-level multi-view VLM experiment per pre-reg (project_md/archive/legacy_premerge_20260728/410_METHOD_prereg_multiview_answer_level_20260708.md, 구 35).
Gate -> deltas (paired bootstrap CI + TOST vs SESOI) -> supporting_view -> verdict."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np, pandas as pd

SESOI = 0.05
CONDS = ["closed_book", "worse_view_only", "better_view_only", "both_view"]
RNG = np.random.default_rng(20260708)


def paired(df, a, b):
    """Per-clip paired accuracy (0/1) for conditions a,b on the common clips."""
    pa = df[df.condition == a].set_index("clip_id")["correct"].astype(float)
    pb = df[df.condition == b].set_index("clip_id")["correct"].astype(float)
    idx = pa.index.intersection(pb.index)
    return pa.loc[idx].values, pb.loc[idx].values


def boot(d, n=5000, pcts=(2.5, 97.5)):
    idx = RNG.integers(0, len(d), size=(n, len(d)))
    m = d[idx].mean(axis=1)
    lo, hi = np.percentile(m, list(pcts))
    p = 2 * min((m <= 0).mean(), (m >= 0).mean())
    return float(d.mean()), float(lo), float(hi), float(max(p, 1.0 / n))


def compare(df, a, b, label):
    x, y = paired(df, a, b)
    d = x - y
    mean_d, lo, hi, p = boot(d)                       # 95% CI + two-sided p
    _, lo90, hi90, _ = boot(d, pcts=(5, 95))          # 90% CI for TOST
    equivalent = bool(lo90 > -SESOI and hi90 < SESOI)  # TOST: 90% CI within +/-SESOI
    return {"comparison": label, "a": a, "b": b, "n": int(len(d)),
            "acc_a": round(float(x.mean()), 4), "acc_b": round(float(y.mean()), 4),
            "delta": round(mean_d, 4), "ci95": [round(lo, 4), round(hi, 4)],
            "ci_excl_0": bool(lo > 0 or hi < 0), "p": round(p, 5),
            "tost_ci90": [round(lo90, 4), round(hi90, 4)], "equivalent_within_SESOI": equivalent}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--answers", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    df = pd.read_parquet(args.answers)
    n_clip = df.clip_id.nunique()
    chance = 1.0 / df.event_class_gold.nunique()

    acc = df.groupby("condition")["correct"].mean().reindex(CONDS)
    acc_by_stratum = df.groupby(["stratum", "condition"])["correct"].mean().unstack("condition").reindex(columns=CONDS)
    quality = {"invalid_json_rate": round(1 - df.valid_json.mean(), 4),
               "unmatched_rate": round((df.match.isin(["unmatched", "ambiguous"])).mean(), 4),
               "snap_substr_rate": round((df.match == "snap_substr").mean(), 4)}

    # GATE (pre-reg §6): both_view > chance AND both_view > closed_book (CI excl 0)
    bc = compare(df, "both_view", "closed_book", "both_view - closed_book")
    gate = {"both_view_acc": round(float(acc["both_view"]), 4), "chance": round(chance, 4),
            "both_gt_chance": bool(acc["both_view"] > chance),
            "both_gt_closedbook_ci_excl0": bc["ci_excl_0"] and bc["delta"] > 0,
            "passes": bool(acc["both_view"] > chance and bc["ci_excl_0"] and bc["delta"] > 0)}

    # MAIN comparisons on the ASYMMETRIC stratum (where 다각도 should matter)
    asym = df[df.stratum == "asymmetric"]; sym = df[df.stratum == "symmetric"]
    comps = {
        "asym_better_vs_worse": compare(asym, "better_view_only", "worse_view_only", "better - worse (asym)"),
        "asym_both_vs_better": compare(asym, "both_view", "better_view_only", "both - better (asym)"),
        "asym_both_vs_closed": compare(asym, "both_view", "closed_book", "both - closed (asym)"),
        "sym_better_vs_worse": compare(sym, "better_view_only", "worse_view_only", "better - worse (sym-control)"),
        "sym_both_vs_better": compare(sym, "both_view", "better_view_only", "both - better (sym-control)"),
    }

    # supporting_view (both_view only): does named view == actual better view?
    bv = df[(df.condition == "both_view") & (df.supporting_view.isin(["c1", "c2"]))].copy()
    sv = {"n_named_single_view": int(len(bv)),
          "matches_better_view_rate": round(float((bv.supporting_view == bv.better_view).mean()), 4) if len(bv) else None}

    # pre-registered verdict (§7)
    def verdict():
        if not gate["passes"]:
            return "GATE_FAIL", ("VLM이 evidence를 grounding하지 못함(both_view가 chance/closed_book를 못 넘음) "
                                 "-> view 조건 비교 무효, VLM-limitation으로 보고. '다각도 무의미' 결론 금지.")
        bw = comps["asym_better_vs_worse"]; bb = comps["asym_both_vs_better"]
        if bb["ci_excl_0"] and bb["delta"] > 0:
            return "BOTH>BETTER", "다각도 evidence가 answer-level에서 추가 이득(both>better, CI excl 0)."
        if bw["ci_excl_0"] and bw["delta"] > 0 and bb["equivalent_within_SESOI"]:
            return "SELECT_BETTER_VIEW", "better≈both>worse -> DB는 view를 쌓지 말고 좋은 view를 선택해야."
        if bb["equivalent_within_SESOI"] and bw["equivalent_within_SESOI"]:
            return "NO_VIEW_EFFECT", ("현재 데이터/모델에서 view 다각도가 답변 품질로도 미관측(TOST 등가). "
                                      "데이터·모델 조건부; '다각도 일반적으로 무의미' 결론 금지.")
        return "INCONCLUSIVE", "유의도 미달·등가 미입증(검정력 부족). n 확대 또는 모델 교체 필요."

    v, vtext = verdict()
    report = {"n_clips": int(n_clip), "chance": round(chance, 4), "accuracy_by_condition": acc.round(4).to_dict(),
              "accuracy_by_stratum": acc_by_stratum.round(4).to_dict(), "answer_quality": quality,
              "gate": gate, "comparisons": comps, "supporting_view": sv, "verdict": v, "verdict_text": vtext}
    (out / "multiview_answer_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2))
    acc_by_stratum.round(4).to_csv(out / "accuracy_by_stratum.csv")

    print(f"n_clips={n_clip} chance={chance:.3f}")
    print("\naccuracy by condition:\n", acc.round(4).to_string())
    print("\naccuracy by stratum:\n", acc_by_stratum.round(4).to_string())
    print("\nquality:", quality)
    print("\nGATE:", gate)
    print("\ncomparisons:")
    for k, c in comps.items():
        print(f"  {c['comparison']}: Δ={c['delta']:+.4f} CI{c['ci95']} excl0={c['ci_excl_0']} equiv={c['equivalent_within_SESOI']} p={c['p']}")
    print("\nsupporting_view:", sv)
    print(f"\n>>> VERDICT: {v} — {vtext}")
    print("saved ->", out)


if __name__ == "__main__":
    main()
