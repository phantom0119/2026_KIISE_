#!/usr/bin/env python3
"""Multi-view (다각도) evidence-selection experiment for AI Hub 71953.

Tests whether the dataset's defining feature — two synchronized CCTV views
(c1/c2) per event — actually matters for grounding the answer, using the
already-valid within-event evidence-selection task.

Design (all conditions share the SAME queries and the SAME visual text->frame
scoring; per-view candidate pools have the SAME positive base rate ~0.43, so
conditions are directly comparable and the random floor is ~equal):

  random        deterministic random ranking over the union pool (floor)
  c1_only       rank ONLY the c1 frames of the clip
  c2_only       rank ONLY the c2 frames of the clip
  single_view   per-query mean(c1_only, c2_only)  = expected fixed single camera
  dual_union    rank BOTH views together          = existing W1 (sanity: ~0.618 SigLIP)
  oracle_view   per-query best of {c1_only, c2_only} = upper bound of a view selector
  label_oracle  sort by is_label_evidence (ceiling = 1.0)

Claims tested:
  (1) dual_union > single_view   -> having both views helps retrieval
  (2) oracle_view > single_view  -> the two views are COMPLEMENTARY (a view
      selector would help) -> motivates view-aware DB evidence selection
  (3) data property: fraction of events whose answer evidence spans BOTH views
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import numpy as np, pandas as pd

TOPKS = [1, 3, 5]


def read_jsonl(p: Path):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def rand_score(qid, fid):
    d = hashlib.sha256(f"{qid}\t{fid}".encode()).digest()
    return int.from_bytes(d[:8], "big") / float(2**64 - 1)


def metrics_from_rel(rel, views_label, views_top_by_k):
    """rel: list[int] label flags in ranked order. Returns MRR/Hit/nDCG/viewcov."""
    out = {"candidate_count": float(len(rel)), "positive_count": float(sum(rel))}
    out["mrr"] = 0.0
    for i, r in enumerate(rel, 1):
        if r:
            out["mrr"] = 1.0 / i
            break
    ideal = sorted(rel, reverse=True)
    for k in TOPKS:
        top = rel[:k]
        dcg = sum(1.0 / np.log2(i + 1) for i, r in enumerate(top, 1) if r)
        idcg = sum(1.0 / np.log2(i + 1) for i, r in enumerate(ideal[:k], 1) if r)
        out[f"hit_at_{k}"] = float(any(top))
        out[f"ndcg_at_{k}"] = float(dcg / idcg) if idcg > 0 else 0.0
        # view coverage: of views that hold evidence, how many are in top-k positives
        pv = views_label
        tv = views_top_by_k[k]
        out[f"positive_view_coverage_at_{k}"] = float(len(tv & pv) / len(pv)) if pv else 0.0
    return out


def rank_and_score(cand, score_col, qid):
    """cand: DataFrame with view,is_label_evidence,frame_id + score_col. Returns metrics."""
    r = cand.sort_values([score_col, "frame_id"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
    rel = r["is_label_evidence"].astype(int).tolist()
    views_label = set(r[r.is_label_evidence]["view"].astype(str))
    views_top = {k: set(r.head(k)[r.head(k).is_label_evidence]["view"].astype(str)) for k in TOPKS}
    return metrics_from_rel(rel, views_label, views_top)


def boot_ci(delta, n=5000, seed=20260708):
    rng = np.random.default_rng(seed)
    d = np.asarray(delta, float)
    idx = rng.integers(0, len(d), size=(n, len(d)))
    means = d[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    p = 2 * min((means <= 0).mean(), (means >= 0).mean())
    return float(d.mean()), float(lo), float(hi), float(max(p, 1.0 / n))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--emb-root", required=True)
    ap.add_argument("--frame-root", required=True)
    ap.add_argument("--canonical-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model-name", default="model")
    args = ap.parse_args()
    er, fr, cr, out = Path(args.emb_root), Path(args.frame_root), Path(args.canonical_root), Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    fidx = pd.read_parquet(er / "frame_index.parquet")
    femb = np.load(er / "frame_embeddings.npy").astype("float32")
    femb /= (np.linalg.norm(femb, axis=1, keepdims=True) + 1e-9)
    qemb = np.load(er / "query_text_embeddings.npy").astype("float32")
    qemb /= (np.linalg.norm(qemb, axis=1, keepdims=True) + 1e-9)
    qidx = read_jsonl(er / "query_index.jsonl")
    frames = pd.read_parquet(fr / "frames.parquet")
    if "is_label_evidence" not in frames:
        frames["is_label_evidence"] = frames["extraction_strategy"].eq("label_evidence_frame")
    queries = pd.DataFrame(read_jsonl(cr / "queries.jsonl"))
    queries = queries[queries["difficulty"].eq("instance_vqa")].reset_index(drop=True)

    qpos = {str(r["query_id"]): i for i, r in enumerate(qidx)}
    fpos = {str(r): i for i, r in enumerate(fidx["frame_id"].astype(str))}
    # frame_id -> view / label from frames.parquet
    fmeta = frames.set_index(frames["frame_id"].astype(str))[["clip_id", "view", "is_label_evidence"]]

    CONDS = ["random", "c1_only", "c2_only", "dual_union", "oracle_view", "pseudo_oracle_view", "label_oracle"]
    rows = []
    ev_view_dist = []  # data property: evidence view distribution per event
    for q in queries.to_dict("records"):
        qid = str(q["query_id"])
        clip = str((q.get("semantic_filter") or {}).get("clip_id") or "")
        if not clip or qid not in qpos:
            continue
        cand = frames[frames["clip_id"].astype(str) == clip].copy()
        if cand.empty:
            continue
        cand["view"] = cand["view"].astype(str)
        cand["is_label_evidence"] = cand["is_label_evidence"].astype(bool)
        qv = qemb[qpos[qid]]
        cand["vscore"] = [float(femb[fpos[str(fid)]] @ qv) if str(fid) in fpos else -1e9
                          for fid in cand["frame_id"].astype(str)]
        cand["rscore"] = [rand_score(qid, str(fid)) for fid in cand["frame_id"].astype(str)]
        cand["lscore"] = cand["is_label_evidence"].astype(float)

        # evidence view distribution (data property)
        lc1 = int(((cand.view == "c1") & cand.is_label_evidence).sum())
        lc2 = int(((cand.view == "c2") & cand.is_label_evidence).sum())
        ev_view_dist.append({"query_id": qid, "clip_id": clip, "label_c1": lc1, "label_c2": lc2,
                             "both_views": lc1 > 0 and lc2 > 0, "single_view_only": (lc1 == 0) ^ (lc2 == 0)})

        c1 = cand[cand.view == "c1"]; c2 = cand[cand.view == "c2"]
        m = {}
        m["c1_only"] = rank_and_score(c1, "vscore", qid) if len(c1) else None
        m["c2_only"] = rank_and_score(c2, "vscore", qid) if len(c2) else None
        m["dual_union"] = rank_and_score(cand, "vscore", qid)
        m["random"] = rank_and_score(cand, "rscore", qid)
        m["label_oracle"] = rank_and_score(cand, "lscore", qid)
        # oracle_view: per-query pick the single REAL view with higher MRR
        if m["c1_only"] and m["c2_only"]:
            m["oracle_view"] = m["c1_only"] if m["c1_only"]["mrr"] >= m["c2_only"]["mrr"] else m["c2_only"]
        else:
            m["oracle_view"] = m["c1_only"] or m["c2_only"]
        # CONTROL: pseudo-view oracle. Split the SAME frames into two RANDOM
        # balanced pseudo-views (matching the real 3-label/4-distractor per view),
        # take the max-MRR one. Averaged over K seeds. If real oracle_view >>
        # pseudo_oracle_view, the gain is genuine view-complementarity, not a
        # mechanical max-of-two-noisy-draws artifact.
        K = 25
        pseudo_acc = None
        lab = cand[cand.is_label_evidence]; dis = cand[~cand.is_label_evidence]
        for s in range(K):
            rng = np.random.default_rng(hash((qid, s)) % (2**32))
            lp = rng.permutation(lab.index.values); dp = rng.permutation(dis.index.values)
            pv_a = cand.loc[list(lp[: len(lp)//2]) + list(dp[: len(dp)//2])]
            pv_b = cand.loc[list(lp[len(lp)//2:]) + list(dp[len(dp)//2:])]
            ma = rank_and_score(pv_a, "vscore", qid) if len(pv_a) else None
            mb = rank_and_score(pv_b, "vscore", qid) if len(pv_b) else None
            best = ma if (ma and (not mb or ma["mrr"] >= mb["mrr"])) else mb
            if best:
                pseudo_acc = {k: pseudo_acc.get(k, 0.0) + v for k, v in best.items()} if pseudo_acc else dict(best)
        if pseudo_acc:
            m["pseudo_oracle_view"] = {k: v / K for k, v in pseudo_acc.items()}
        for cond in CONDS:
            if m.get(cond):
                rows.append({"strategy": cond, "query_id": qid, **m[cond]})

    mbq = pd.DataFrame(rows)
    metric_cols = ["mrr"] + [f"{p}_at_{k}" for k in TOPKS for p in ["hit", "ndcg", "positive_view_coverage"]]
    summ = mbq.groupby("strategy")[metric_cols + ["candidate_count", "positive_count"]].mean().reindex(CONDS)
    # single_view = mean of c1_only and c2_only per query
    piv = mbq.pivot_table(index="query_id", columns="strategy", values=metric_cols, aggfunc="mean")
    sv = {mc: ((piv[(mc, "c1_only")] + piv[(mc, "c2_only")]) / 2).mean() for mc in metric_cols}
    summ.loc["single_view"] = pd.Series(sv)
    summ = summ.reindex(["random", "c1_only", "c2_only", "single_view", "dual_union",
                         "pseudo_oracle_view", "oracle_view", "label_oracle"])

    # bootstrap CI on the key deltas (per-query paired)
    def per_query(cond, metric):
        return piv[(metric, cond)] if (metric, cond) in piv else pd.Series(dtype=float)
    sv_series = (per_query("c1_only", "mrr") + per_query("c2_only", "mrr")) / 2
    deltas = {}
    for metric in ["mrr", "hit_at_1", "ndcg_at_5"]:
        svm = (per_query("c1_only", metric) + per_query("c2_only", metric)) / 2
        for cond in ["dual_union", "oracle_view"]:
            cm = per_query(cond, metric)
            idx = svm.index.intersection(cm.index)
            mean_d, lo, hi, p = boot_ci((cm.loc[idx] - svm.loc[idx]).values)
            deltas[f"{cond}_vs_single_view[{metric}]"] = {"delta": round(mean_d, 4),
                "ci95": [round(lo, 4), round(hi, 4)], "ci_excl_0": bool(lo > 0 or hi < 0), "boot_p": round(p, 5)}
        # dual vs random
        rm = per_query("random", metric); dm = per_query("dual_union", metric)
        idx = rm.index.intersection(dm.index)
        mean_d, lo, hi, p = boot_ci((dm.loc[idx] - rm.loc[idx]).values)
        deltas[f"dual_union_vs_random[{metric}]"] = {"delta": round(mean_d, 4),
            "ci95": [round(lo, 4), round(hi, 4)], "ci_excl_0": bool(lo > 0 or hi < 0), "boot_p": round(p, 5)}
        # DECISIVE CONTROL: real oracle_view vs pseudo (random-view) oracle.
        # >0 with CI excl 0 => genuine view-complementarity beyond max-of-two artifact.
        om = per_query("oracle_view", metric); pm = per_query("pseudo_oracle_view", metric)
        idx = om.index.intersection(pm.index)
        mean_d, lo, hi, p = boot_ci((om.loc[idx] - pm.loc[idx]).values)
        deltas[f"oracle_view_vs_PSEUDO_oracle[{metric}]"] = {"delta": round(mean_d, 4),
            "ci95": [round(lo, 4), round(hi, 4)], "ci_excl_0": bool(lo > 0 or hi < 0), "boot_p": round(p, 5)}

    evd = pd.DataFrame(ev_view_dist)
    data_prop = {
        "events": int(len(evd)),
        "evidence_in_both_views_pct": round(100 * evd["both_views"].mean(), 1),
        "evidence_single_view_only_pct": round(100 * evd["single_view_only"].mean(), 1),
        "mean_label_c1": round(evd["label_c1"].mean(), 2), "mean_label_c2": round(evd["label_c2"].mean(), 2),
    }

    summ.round(4).to_csv(out / "multiview_summary.csv")
    mbq.to_parquet(out / "multiview_metrics_by_query.parquet")
    (out / "multiview_report.json").write_text(json.dumps({
        "model": args.model_name, "n_queries": int(mbq["query_id"].nunique()),
        "summary": summ.round(4).to_dict("index"), "data_property": data_prop,
        "bootstrap_deltas": deltas,
    }, ensure_ascii=False, indent=2))
    print(f"=== {args.model_name} multi-view evidence selection (n={mbq['query_id'].nunique()}) ===")
    print(summ.round(4)[["mrr", "hit_at_1", "hit_at_3", "ndcg_at_5"]].to_string())
    print("\ndata property:", data_prop)
    print("\nkey bootstrap deltas:")
    for k, v in deltas.items():
        print(f"  {k}: Δ={v['delta']:+.4f} CI{v['ci95']} excl0={v['ci_excl_0']} p={v['boot_p']}")
    print("saved ->", out)


if __name__ == "__main__":
    main()
