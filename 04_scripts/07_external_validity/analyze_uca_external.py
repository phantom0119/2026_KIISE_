#!/usr/bin/env python3
"""UCA external-validity analysis [prereg 420 Amendment 6+6a — decision rule
PINNED IN CODE BEFORE retrieval data exists, per house discipline].

FROZEN direction-consistency rule (6a(6)) — vs the 522 findings:
  c1  strict  pooled Δ(B4−B2) > 0                      (522: +0.098)
  c2  semantic pooled Δ over container_clean queries < 0  (522 low-V: −0.099)
  c3  negative per-query semantic Δ EXISTS              (C1-collapse witness)
  c4  semantic Δ(label_stratum, non-degenerate) > Δ(container_clean)
      (522: natural-coupling +0.134 > low-coupling −0.099)
Verdict "direction-consistent with 522" iff >=3 of 4 hold; tally reported
either way. Signs must agree across the plain mean and the medians of the
(field x lexicon)-pair and lexicon cluster bootstraps [6a(7)].
Primary pool = non-degenerate AND not Normal_Videos stratum; degenerate /
Normal / annotation_timing strata reported separately (혼입 금지).
Extra lane: video-deduplicated scoring (max one credit per video in top-10).

Run (kiise-vlmdb env) after run_retrieval_baselines.py.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/hdd2/KIISE_datasociety/Datasets/processed/uca_anchor/20260712")
CAN = ROOT / "canonical"
RES = ROOT / "results" / "uca_b0_b5"
OUT = Path("/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE"
           "/paper_assets/20260712_uca_external")
RNG = np.random.default_rng(20260712)
K = 10


def ndcg10(ranked_clips, rel_set, clip2vid=None, dedup=False):
    gains, seen = [], set()
    for c in ranked_clips[:K]:
        g = 1.0 if c in rel_set else 0.0
        if dedup and g > 0:
            v = clip2vid[c]
            if v in seen:
                g = 0.0
            seen.add(v)
        gains.append(g)
    dcg = sum(g / np.log2(i + 2) for i, g in enumerate(gains))
    if dedup:
        n_ideal_vids = len({clip2vid[c] for c in rel_set})
        ideal_n = min(K, n_ideal_vids)
    else:
        ideal_n = min(K, len(rel_set))
    idcg = sum(1 / np.log2(i + 2) for i in range(ideal_n))
    return dcg / idcg if idcg > 0 else 0.0


def cluster_median(deltas, clusters, B=5000):
    labs = np.asarray(clusters)
    uniq = np.unique(labs)
    groups = {u: np.asarray(deltas)[labs == u] for u in uniq}
    means = []
    for _ in range(B):
        pick = RNG.choice(uniq, len(uniq), replace=True)
        means.append(np.concatenate([groups[u] for u in pick]).mean())
    return float(np.median(means)), (float(np.percentile(means, 2.5)),
                                     float(np.percentile(means, 97.5)))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rr = pd.read_parquet(RES / "retrieval_results.parquet")
    queries = pd.DataFrame([json.loads(l) for l in open(CAN / "queries.jsonl")])
    clips = pd.read_parquet(CAN / "clips.parquet")
    clip2vid = dict(zip(clips.clip_id, clips.visual_video_id))
    qrels = {"strict": pd.read_csv(CAN / "qrels.tsv", sep="\t"),
             "semantic": pd.read_csv(CAN / "qrels_semantic.tsv", sep="\t")}
    relsets = {sc: df.groupby("query_id").target_id.apply(set).to_dict()
               for sc, df in qrels.items()}

    ranked = rr.sort_values("rank").groupby(["strategy", "query_id"]).clip_id \
               .apply(list).to_dict()
    rows = []
    for (_, q) in queries.iterrows():
        for sc in ("strict", "semantic"):
            rs = relsets[sc].get(q.query_id, set())
            for strat in ("B2_vector_only", "B4_prefilter_vector"):
                lst = ranked.get((strat, q.query_id), [])
                rows.append({"query_id": q.query_id, "scoring": sc, "strategy": strat,
                             "ndcg10": ndcg10(lst, rs),
                             "ndcg10_videodedup": ndcg10(lst, rs, clip2vid, True)})
    m = pd.DataFrame(rows).pivot_table(
        index=["query_id", "scoring"], columns="strategy",
        values=["ndcg10", "ndcg10_videodedup"])
    m.columns = [f"{a}_{b.split('_')[0]}" for a, b in m.columns]
    m = m.reset_index().merge(queries, on="query_id")
    m["delta"] = m.ndcg10_B4 - m.ndcg10_B2
    m["delta_dedup"] = m.ndcg10_videodedup_B4 - m.ndcg10_videodedup_B2
    m["pair"] = m.difficulty + "|" + m.relevance_def
    m.to_csv(OUT / "UCA_query_deltas.csv", index=False)

    prim = m[(~m.degenerate) & (~m.normal_stratum)]

    def lanes(sub):
        if len(sub) == 0:
            return None
        mean = float(sub.delta.mean())
        pmed, pci = cluster_median(sub.delta.values, sub.pair.values)
        lmed, lci = cluster_median(sub.delta.values, sub.relevance_def.values)
        return {"n": len(sub), "mean": round(mean, 4),
                "pair_boot_median": round(pmed, 4), "pair_ci": [round(x, 4) for x in pci],
                "lex_boot_median": round(lmed, 4), "lex_ci": [round(x, 4) for x in lci],
                "mean_dedup": round(float(sub.delta_dedup.mean()), 4),
                "signs_agree": bool(np.sign(mean) == np.sign(pmed) == np.sign(lmed))}

    strict_p = lanes(prim[prim.scoring == "strict"])
    sem_cont = lanes(prim[(prim.scoring == "semantic") &
                          (prim.stratum == "container_clean")])
    sem_lab = lanes(prim[(prim.scoring == "semantic") &
                         (prim.stratum == "label_stratum")])
    sem_all = prim[prim.scoring == "semantic"]
    n_neg = int((sem_all.delta < 0).sum())

    c1 = strict_p is not None and strict_p["mean"] > 0 and strict_p["signs_agree"]
    c2 = sem_cont is not None and sem_cont["mean"] < 0 and sem_cont["signs_agree"]
    c3 = n_neg > 0
    c4 = (sem_lab is not None and sem_cont is not None
          and sem_lab["mean"] > sem_cont["mean"])
    tally = sum([c1, c2, c3, c4])
    contrasts = {
        "c1_strict_pooled_positive": {"holds": bool(c1), "detail": strict_p},
        "c2_semantic_container_negative": {"holds": bool(c2), "detail": sem_cont},
        "c3_negative_semantic_signs_exist": {"holds": bool(c3),
                                             "n_negative": n_neg,
                                             "n_semantic": len(sem_all)},
        "c4_label_gt_container_semantic": {"holds": bool(c4), "label": sem_lab},
        "tally": tally, "verdict_direction_consistent": bool(tally >= 3),
        "rule": "frozen Amendment 6a(6): consistent iff >=3/4",
    }

    # separated strata (혼입 금지) — descriptive
    strata = {}
    for name, sub in [
        ("degenerate", m[m.degenerate]),
        ("normal_stratum", m[m.normal_stratum & ~m.degenerate]),
        ("annotation_timing_semantic",
         m[(m.stratum == "annotation_timing") & (m.scoring == "semantic")
           & ~m.degenerate & ~m.normal_stratum])]:
        if len(sub):
            strata[name] = {"n": len(sub),
                            "mean_delta": round(float(sub.delta.mean()), 4)}
    contrasts["separated_strata"] = strata
    (OUT / "UCA_contrasts.json").write_text(json.dumps(contrasts, indent=2))

    # full strategy summary (all six strategies, both scorings) for the paper table
    summ = []
    for strat in rr.strategy.unique():
        for sc in ("strict", "semantic"):
            vals = [ndcg10(ranked.get((strat, q.query_id), []),
                           relsets[sc].get(q.query_id, set()))
                    for _, q in queries.iterrows()
                    if not q.degenerate and not q.normal_stratum]
            summ.append({"strategy": strat, "scoring": sc,
                         "mean_ndcg10_primary": round(float(np.mean(vals)), 4)})
    pd.DataFrame(summ).to_csv(OUT / "UCA_results.csv", index=False)
    print(json.dumps(contrasts, indent=2)[:2000])
    print(pd.DataFrame(summ).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
