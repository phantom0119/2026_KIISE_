#!/usr/bin/env python3
"""P0 CPU pilot / F6: power ENVELOPE simulation (not a power decision).

Per v1.1 amendment §4, real discordance and cluster ICC require model outputs,
so the CPU stage only maps the assumption space: for a grid of (discordance,
ICC, effect size) it reports the number of independent fact clusters needed for
80% and 90% power on the paired primary comparisons (McNemar-style paired
binary outcome with design-effect inflation for within-cluster correlation).

n_pairs        = (z_{1-a/2}+z_{1-b})^2 * p_d / delta^2      [paired binary]
n_clusters     = n_pairs * DEFF / m,  DEFF = 1 + (m-1)*ICC,  m = obs/cluster
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm as znorm

P0 = Path(__file__).resolve().parents[1]
ALPHA = 0.05 / 3          # Holm-conservative for 3 primary comparisons
DISCORDANCE = [0.05, 0.10, 0.20, 0.30, 0.40]
ICC = [0.0, 0.05, 0.10, 0.20, 0.30]
DELTA = [0.03, 0.05, 0.08, 0.10]      # absolute effect in the paired metric
M_PER_CLUSTER = [2, 4, 6]             # questions x models per canonical fact


def n_pairs(p_d: float, delta: float, power: float) -> float:
    z_a = znorm.ppf(1 - ALPHA / 2)
    z_b = znorm.ppf(power)
    return (z_a + z_b) ** 2 * p_d / (delta ** 2)


def main() -> int:
    t0 = time.time()
    rows = []
    for p_d in DISCORDANCE:
        for icc in ICC:
            for d in DELTA:
                for m in M_PER_CLUSTER:
                    if d > p_d:       # effect cannot exceed the discordant share
                        continue
                    deff = 1 + (m - 1) * icc
                    for power in (0.80, 0.90):
                        npair = n_pairs(p_d, d, power)
                        rows.append({
                            "discordance": p_d, "ICC": icc, "delta": d,
                            "obs_per_cluster": m, "power": power,
                            "DEFF": round(deff, 3),
                            "n_pairs": int(np.ceil(npair)),
                            "n_clusters_needed": int(np.ceil(npair * deff / m)),
                        })
    df = pd.DataFrame(rows)
    df.to_csv(P0 / "results" / "power_scenarios.csv", index=False)

    # Feasibility envelope against realistic asset ceilings
    ceilings = {"pilot_now": 200, "primekg_reachable": 6282, "two_domains_target": 1000}
    env = {}
    for name, cap in ceilings.items():
        sub = df[(df.power == 0.80)]
        env[name] = {
            "frac_scenarios_feasible": round(float((sub.n_clusters_needed <= cap).mean()), 3),
            "feasible_at_delta_0.05": sorted(
                set(sub[(sub.delta == 0.05) & (sub.n_clusters_needed <= cap)]
                    .discordance.tolist())),
            "min_clusters_delta_0.05_icc_0.10_m4": int(
                sub[(sub.delta == 0.05) & (sub.ICC == 0.10) & (sub.obs_per_cluster == 4)]
                .n_clusters_needed.min()),
            "max_clusters_delta_0.05_icc_0.10_m4": int(
                sub[(sub.delta == 0.05) & (sub.ICC == 0.10) & (sub.obs_per_cluster == 4)]
                .n_clusters_needed.max()),
        }
    out = {"alpha_per_comparison": round(ALPHA, 5), "n_scenarios": len(df),
           "envelope": env, "wall_s": round(time.time() - t0, 1),
           "note": "CPU stage = envelope only; real discordance/ICC pending model pilot."}
    (P0 / "results" / "power_envelope.json").write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
