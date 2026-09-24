#!/usr/bin/env python3
"""P0 model pilot analysis: gates F3, F4 + real F6 inputs (discordance, ICC).

F3 non-memorized sample : parametric knowledge probability (pkp) from the 9
                          closed-book probes; a fact is STABLY non-memorized
                          when pkp == 0 (no probe recovers the true tail).
                          Gate: >=100 such fact clusters per domain per model.
F4 treatment strength   : counterfactual oracle evidence must move the
                          active-world answer-following rate by >=20pp versus
                          closed-book (measured on the untouched HOLDOUT once).
F6 inputs               : paired discordance for the primary contrasts
                          (H1a = A1F-A1, H1b = A2-A1F, H1 = A2-A1) and the
                          cluster ICC of the binary outcome across the repeated
                          observations belonging to one canonical fact.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

P0 = Path(__file__).resolve().parents[1]
MODELS = ["llama3", "qwen25"]
ARMS = ["A1_text", "A1F_flat", "A2_path"]
F3_MIN, F4_MIN_PP = 100, 0.20


def load(split: str) -> pd.DataFrame:
    fr = []
    for m in MODELS:
        p = P0 / "results" / f"model_pilot_{m}_{split}.jsonl"
        if p.exists():
            fr += [json.loads(l) for l in open(p)]
    return pd.DataFrame(fr)


def icc_binary(df: pd.DataFrame, cluster: str, value: str) -> float:
    """One-way random-effects ICC(1) on a binary outcome."""
    g = df.groupby(cluster)[value]
    k = g.size()
    if len(k) < 2 or k.max() < 2:
        return float("nan")
    n_bar = k.mean()
    grand = df[value].mean()
    msb = (k * (g.mean() - grand) ** 2).sum() / (len(k) - 1)
    within = df.merge(g.mean().rename("gm"), on=cluster)
    msw = ((within[value] - within["gm"]) ** 2).sum() / max(len(df) - len(k), 1)
    denom = msb + (n_bar - 1) * msw
    return float((msb - msw) / denom) if denom > 0 else float("nan")


def main() -> int:
    out = {}
    # ---------------- F3 (both splits pooled; per model x domain) ----------
    f3 = {}
    for split in ("dev", "holdout"):
        d = load(split)
        if d.empty:
            continue
        cb = d[d.arm == "A0_closed"]
        pkp = (cb.groupby(["model", "domain", "fact_id"])["hit_original"].mean()
               .rename("pkp").reset_index())
        for (m, dom), g in pkp.groupby(["model", "domain"]):
            key = f"{m}|{dom}"
            e = f3.setdefault(key, {"n_facts": 0, "n_pkp0": 0, "pkp_mean": []})
            e["n_facts"] += len(g)
            e["n_pkp0"] += int((g.pkp == 0).sum())
            e["pkp_mean"] += g.pkp.tolist()
    for k, v in f3.items():
        v["pkp_mean"] = round(float(np.mean(v["pkp_mean"])), 4)
        v["frac_stably_nonmemorized"] = round(v["n_pkp0"] / v["n_facts"], 4)
        v["meets_F3_min100"] = v["n_pkp0"] >= F3_MIN
    out["F3"] = {"per_model_domain": f3,
                 "pass": all(v["meets_F3_min100"] for v in f3.values()) if f3 else False}

    # ---------------- F4 on HOLDOUT only (single measurement) --------------
    ho = load("holdout")
    f4 = {}
    if not ho.empty:
        cb_cf = 0.0          # closed-book cannot follow a counterfactual world
        for (m, dom), g in ho.groupby(["model", "domain"]):
            cf = g[(g.world == "counterfactual") & (g.arm.isin(ARMS))]
            follow = float(cf.hit_active.mean())
            per_arm = cf.groupby("arm").hit_active.mean().round(4).to_dict()
            f4[f"{m}|{dom}"] = {
                "cf_follow_rate": round(follow, 4),
                "closed_book_cf_baseline": cb_cf,
                "delta_pp": round(follow - cb_cf, 4),
                "meets_F4_20pp": (follow - cb_cf) >= F4_MIN_PP,
                "per_arm": per_arm,
                "memory_override_rate": round(float(cf.hit_original.mean()), 4),
                "abstain_rate": round(float(cf.abstain.mean()), 4),
                "one_sided_arm_effect": bool(max(per_arm.values()) - min(per_arm.values()) > 0.5),
            }
        out["F4"] = {"per_model_domain": f4,
                     "pass": all(v["meets_F4_20pp"] for v in f4.values())}

    # ---------------- F6 real inputs: discordance + ICC --------------------
    f6 = {}
    if not ho.empty:
        ev = ho[ho.arm.isin(ARMS)]
        wide = ev.pivot_table(index=["model", "domain", "fact_id", "world"],
                              columns="arm", values="hit_active", aggfunc="first")
        for a, b, name in (("A1_text", "A1F_flat", "H1a_format"),
                           ("A1F_flat", "A2_path", "H1b_structure"),
                           ("A1_text", "A2_path", "H1_total_repr")):
            sub = wide.dropna(subset=[a, b])
            disc = float((sub[a] != sub[b]).mean())
            f6[name] = {"n_pairs": int(len(sub)), "discordance": round(disc, 4),
                        "mean_a": round(float(sub[a].mean()), 4),
                        "mean_b": round(float(sub[b].mean()), 4),
                        "raw_diff": round(float(sub[b].mean() - sub[a].mean()), 4)}
        icc_rows = ev.copy()
        f6["ICC_by_fact_cluster"] = round(icc_binary(icc_rows, "fact_id", "hit_active"), 4)
        f6["obs_per_cluster_mean"] = round(float(ev.groupby("fact_id").size().mean()), 2)
        out["F6_inputs"] = f6

    # ---------------- descriptive: representation effects ------------------
    if not ho.empty:
        ev = ho[ho.arm.isin(ARMS)]
        out["descriptive_hit_active"] = (
            ev.groupby(["domain", "world", "arm"]).hit_active.mean().round(4)
            .reset_index().to_dict("records"))
        out["descriptive_by_model"] = (
            ev.groupby(["model", "world", "arm"]).hit_active.mean().round(4)
            .reset_index().to_dict("records"))

    (P0 / "results" / "model_pilot_gates.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: v for k, v in out.items() if not k.startswith("descriptive")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
