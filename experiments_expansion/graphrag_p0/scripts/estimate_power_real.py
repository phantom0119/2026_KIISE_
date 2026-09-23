#!/usr/bin/env python3
"""P0 / F6 REAL: sample size from measured discordance and ICC (model pilot)."""
import json
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import norm as znorm

P0 = Path(__file__).resolve().parents[1]
ALPHA = 0.05 / 3
g = json.load(open(P0 / "results" / "model_pilot_gates.json"))
f6 = g["F6_inputs"]
ICC = f6["ICC_by_fact_cluster"]
M = f6["obs_per_cluster_mean"]
rows = []
for name in ("H1a_format", "H1b_structure", "H1_total_repr"):
    p_d = f6[name]["discordance"]
    for delta in (0.02, 0.03, 0.05, 0.08):
        for power in (0.80, 0.90):
            for m in (2, 4, M):
                deff = 1 + (m - 1) * ICC
                n_pairs = (znorm.ppf(1 - ALPHA / 2) + znorm.ppf(power)) ** 2 * p_d / delta ** 2
                rows.append({"contrast": name, "measured_discordance": p_d,
                             "measured_ICC": ICC, "delta": delta, "power": power,
                             "obs_per_cluster": round(m, 1), "DEFF": round(deff, 3),
                             "n_pairs": int(np.ceil(n_pairs)),
                             "n_clusters": int(np.ceil(n_pairs * deff / m))})
df = pd.DataFrame(rows)
df.to_csv(P0 / "results" / "power_real.csv", index=False)
key = df[(df.power == 0.80) & (df.obs_per_cluster == round(M, 1))]
out = {"measured": {"ICC": ICC, "obs_per_cluster": M,
                    "discordance": {k: f6[k]["discordance"] for k in
                                    ("H1a_format", "H1b_structure", "H1_total_repr")}},
       "clusters_needed_power80": {
           r.contrast + f"@delta{r.delta}": int(r.n_clusters) for r in key.itertuples()},
       "available_now": 400,
       "primekg_ceiling_drugs": 6282,
       "feasible_at_delta_0.03": {
           r.contrast: bool(r.n_clusters <= 6282)
           for r in key[key.delta == 0.03].itertuples()},
       "note": "delta = absolute difference in the paired binary outcome"}
(P0 / "results" / "power_real.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
