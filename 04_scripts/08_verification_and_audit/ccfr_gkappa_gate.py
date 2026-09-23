#!/usr/bin/env python3
"""CC-FR G-κ gate [prereg 420 Amendment 7]: does the OFFLINE, query-independent
cluster-depth statistic κ_p predict the observed shared-index postfilter deficit?

κ_p (per predicate, query-independent): sample <=150 subset members as pseudo-
queries; for each, find its in-subset exact top-10 neighbors (self excluded) and
their median rank in the member's GLOBAL exact ranking; κ_p = median over samples.
High κ_p <=> subset's own neighbors sit deep globally <=> shared postfilter with
limited K'/nprobe misses them. This is the deployable analog of the query-driven
gt_cluster_med_rank.

Observed deficit (what κ_p must predict): per real predicate, the M9 overestimation
control_recall - real_recall for shared-index methods (postfilter K'=2x, single-
stage IVF np32) from filtered_ann_real_{A,B}.csv.

GATE: Spearman ρ(κ_p, deficit) >= 0.5 across the 29+25 predicates -> κ_p is a valid
routing signal. Also report ρ vs the query-driven gt_cluster_med_rank as an upper
reference. Output: paper_assets/20260712_ccfr/gkappa_gate.{csv,json}

Run (kiise-vlmdb env, CPU/read-only): ccfr_gkappa_gate.py
"""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr

import run_filtered_ann_real_predicate as b1

R2 = Path(__file__).resolve().parents[2]
PB = R2 / "paper_assets" / "20260710_pillarB"
OUT = R2 / "paper_assets" / "20260712_ccfr"
RNG = np.random.default_rng(20260712)
KTOP = 10
SAMPLE = 150


def load(corpus):
    if corpus == "A":
        X = np.load(b1.SIN / "frame_embeddings.npy").astype("float32")
        X /= (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
        fi = pd.read_parquet(b1.SIN / "frame_index.parquet")
        masks = b1.masks_corpus_a(fi)
    else:
        V = b1.V522 / "visual_embeddings_clip"
        X = np.load(V / "frame_embeddings.npy").astype("float32")
        fi = pd.read_parquet(V / "frame_index.parquet")
        join = pd.read_parquet(b1.V522 / "visual_sensor_join.parquet")
        j = join[join.join_ok_120s][["visual_video_id", "split", "time_of_day", "hour",
                                     "sig_has_yellow", "sig_has_pedestrian", "veh_density_bin"]]
        f = fi.merge(j, on=["visual_video_id", "split"], how="left", suffixes=("_fn", ""))
        masks = b1.masks_corpus_b(f)
    return X, masks


def kappa(X, sub_ids):
    """query-independent cluster depth of a predicate subset."""
    m = len(sub_ids)
    if m < KTOP + 2:
        return np.nan
    sub = np.ascontiguousarray(X[sub_ids])
    samp = sub_ids if m <= SAMPLE else sub_ids[RNG.choice(m, SAMPLE, replace=False)]
    # in-subset exact top-(K+1) for the sampled members (self excluded)
    ds = []
    Xs = X[samp]                                   # (s, d)
    sub_scores = Xs @ sub.T                         # (s, m)
    # for each sampled q', its in-subset neighbor global ids (top-K excl self)
    for i, qid in enumerate(samp):
        row = sub_scores[i]
        order = np.argpartition(-row, KTOP + 1)[:KTOP + 1]
        order = order[np.argsort(-row[order])]
        nbr_local = [o for o in order if sub_ids[o] != qid][:KTOP]
        nbr_global = sub_ids[nbr_local]
        # global exact scores for this q'
        g = X[qid] @ X.T                            # (N,)
        gv = g[nbr_global]
        ranks = (g[None, :] > gv[:, None]).sum(axis=1)   # rank = #items scoring higher
        ds.append(np.median(ranks))
    return float(np.median(ds))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for corpus in ["A", "B"]:
        X, masks = load(corpus)
        df = pd.read_csv(PB / f"filtered_ann_real_{corpus}.csv")
        real = df[~df.predicate.str.startswith("CTRL")]
        ctrl = df[df.predicate.str.startswith("CTRL")].copy()
        ctrl["pair"] = ctrl.predicate.str.split("|").str[1]
        def deficit(pred, meth):
            r = real[(real.predicate == pred) & (real.method == meth)]
            c = ctrl[(ctrl.pair == pred) & (ctrl.method == meth)]
            if len(r) and len(c):
                return float(c.recall_at_10.iloc[0] - r.recall_at_10.iloc[0])
            return np.nan
        for name, kind, mask in masks:
            sub_ids = np.flatnonzero(mask)
            k = kappa(X, sub_ids)
            gtrank = real[real.predicate == name].gt_cluster_med_rank
            rows.append({
                "corpus": corpus, "predicate": name, "kind": kind,
                "selectivity": round(len(sub_ids) / len(X), 5),
                "kappa_offline": round(k, 1) if k == k else np.nan,
                "gt_cluster_med_rank": float(gtrank.iloc[0]) if len(gtrank) else np.nan,
                "deficit_postfilter_K2x": deficit(name, "postfilter_hnsw_K2x"),
                "deficit_singlestage_np32": deficit(name, "single_stage_ivf_batch_np32"),
            })
        print(f"[{corpus}] {len([r for r in rows if r['corpus']==corpus])} predicates done", flush=True)

    d = pd.DataFrame(rows)
    d.to_csv(OUT / "gkappa_gate.csv", index=False)
    res = {}
    for defcol in ["deficit_postfilter_K2x", "deficit_singlestage_np32"]:
        v = d.dropna(subset=["kappa_offline", defcol])
        rho_off = spearmanr(v.kappa_offline, v[defcol]).correlation
        rho_gt = spearmanr(v.gt_cluster_med_rank, v[defcol]).correlation
        res[defcol] = {
            "n": len(v),
            "rho_kappa_offline": round(float(rho_off), 3),
            "rho_gt_cluster_query_driven": round(float(rho_gt), 3),
            "gate_pass_offline_ge_0.5": bool(rho_off >= 0.5),
        }
        # also κ_offline vs gt-cluster agreement (does offline proxy track query-driven?)
    v2 = d.dropna(subset=["kappa_offline", "gt_cluster_med_rank"])
    res["kappa_offline_vs_gt_query_driven_rho"] = round(
        float(spearmanr(v2.kappa_offline, v2.gt_cluster_med_rank).correlation), 3)
    res["overall_gate_pass"] = all(res[c]["gate_pass_offline_ge_0.5"]
                                   for c in ["deficit_postfilter_K2x", "deficit_singlestage_np32"])
    (OUT / "gkappa_gate.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
