#!/usr/bin/env python3
"""Semantic (soft-intent) re-scoring of saved MEVA B0-B5 rankings + B4-B2 significance.

run_retrieval_baselines.py scores rankings against STRICT qrels (filter AND
activity). This re-scores the SAME saved rankings against qrels_semantic.tsv
(activity regardless of predicate) — the non-circular headline eval where
prefilter can REMOVE relevant clips, so B4 >= B2 is NOT guaranteed.

Reproduces the 522 analysis for the overseas MEVA arm:
  - per-strategy semantic nDCG@10 / recall@10 / MRR
  - B4(prefilter) - B2(vector-only) paired delta: mean, 95% bootstrap CI,
    sign distribution (neg/zero/pos), split by coupling. MEVA pairs are all
    low-coupling, so the 522 low-coupling prediction is B4-B2 <= 0.

Run:
  Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/04_scripts/score_meva_semantic.py \
    --results-dir Datasets/processed/meva_kf1/20260713/results/meva_bgem3_b0_b5 \
    --canonical-root Datasets/processed/meva_kf1/20260713/canonical_trisource
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT / "2026_KIISE" / "03_src"))
from vlmdb_workload.metrics import evaluate_ranking  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", type=Path, required=True)
    ap.add_argument("--canonical-root", type=Path, required=True)
    ap.add_argument("--top-ks", default="1,5,10,20")
    ap.add_argument("--boot", type=int, default=5000)
    ap.add_argument("--seed", type=int, default=20260713)
    args = ap.parse_args()
    top_ks = [int(x) for x in args.top_ks.split(",")]

    res = pd.read_parquet(args.results_dir / "retrieval_results.parquet")
    qsem = pd.read_csv(args.canonical_root / "qrels_semantic.tsv", sep="\t")
    sem_pos = {qid: set(g["target_id"]) for qid, g in qsem.groupby("query_id", sort=False)}
    queries = pd.DataFrame([json.loads(l) for l in
                            (args.canonical_root / "queries.jsonl").read_text().splitlines()])
    coupling = dict(zip(queries["query_id"], queries["coupling"]))

    # per (strategy, query) semantic metrics from saved rankings
    rows = []
    for (strat, qid), g in res.groupby(["strategy", "query_id"], sort=False):
        ranking = g.sort_values("rank")["clip_id"].tolist()
        m = evaluate_ranking(ranking, sem_pos.get(qid, set()), top_ks)
        rows.append({"strategy": strat, "query_id": qid,
                     "coupling": coupling.get(qid, "?"), **m})
    per_q = pd.DataFrame(rows)

    metric_cols = [c for c in per_q.columns if c.startswith(("recall_at_", "hit_at_"))] + ["mrr", "ndcg_at_10"]
    summary = per_q.groupby("strategy")[metric_cols].mean().reset_index()
    summary.to_csv(args.results_dir / "metrics_semantic.csv", index=False)

    # ---- B4 - B2 paired delta (semantic nDCG@10) with bootstrap CI + sign dist ----
    piv = per_q.pivot_table(index="query_id", columns="strategy", values="ndcg_at_10")
    piv["coupling"] = piv.index.map(coupling)
    rng = np.random.default_rng(args.seed)

    def boot_ci(d: np.ndarray) -> tuple[float, float, float]:
        if len(d) == 0:
            return (float("nan"),) * 3
        idx = rng.integers(0, len(d), size=(args.boot, len(d)))
        means = d[idx].mean(axis=1)
        return float(d.mean()), float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))

    sig_rows = []
    for label, sub in [("all", piv), *[(c, piv[piv.coupling == c]) for c in sorted(piv.coupling.unique())]]:
        d = (sub["B4_prefilter_vector"] - sub["B2_vector_only"]).to_numpy()
        mean, lo, hi = boot_ci(d)
        sig_rows.append({"subset": label, "n": int(len(d)), "delta_B4_B2": round(mean, 4),
                         "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
                         "neg": int((d < -1e-9).sum()), "zero": int((np.abs(d) <= 1e-9).sum()),
                         "pos": int((d > 1e-9).sum()),
                         "ci_excludes_0": bool(hi < 0 or lo > 0)})
    sig = pd.DataFrame(sig_rows)
    sig.to_csv(args.results_dir / "b4_vs_b2_semantic.csv", index=False)

    print("=== per-strategy SEMANTIC metrics (nDCG@10 / recall@10 / MRR) ===")
    for r in summary.to_dict("records"):
        print(f"  {r['strategy']:22s} ndcg@10={r['ndcg_at_10']:.4f}  "
              f"recall@10={r['recall_at_10']:.4f}  mrr={r['mrr']:.4f}")
    print("\n=== B4(prefilter) - B2(vector) paired delta, SEMANTIC nDCG@10 ===")
    for r in sig.to_dict("records"):
        print(f"  {r['subset']:10s} n={r['n']:3d}  Δ={r['delta_B4_B2']:+.4f}  "
              f"CI[{r['ci_lo']:+.4f},{r['ci_hi']:+.4f}]  "
              f"sign(neg/zero/pos)={r['neg']}/{r['zero']}/{r['pos']}  "
              f"CI_excl_0={r['ci_excludes_0']}")
    print(f"\n[saved] {args.results_dir}/metrics_semantic.csv , b4_vs_b2_semantic.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
