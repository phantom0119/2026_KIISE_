#!/usr/bin/env python3
"""P0-1 W1: per-(query,predicate) workload-geometry features on internal corpora.

Computes, for every (query, predicate-arm) pair on corpora A/B, the five feature
families the validity audit requires with SEPARATED symbols (audit 2026-08-04
terminology decision — never conflate these):

  s_p           global selectivity of predicate p
  rho_GLS(q,p)  signed local enrichment/depletion: r = sigma_l/sigma_g,
                rho_GLS = (r-1)/(r+1), with sigma_l measured at k in
                {10,50,100,1000} over the EXACT global similarity ranking
  rank10(q,p)   0-based global rank of the 10th predicate-satisfying item
                (over-fetch depth for Recall@10; N if fewer than 10 valid)
  alpha_sim     sim(q, 10th global item) / sim(q, 10th valid item)
                (distance-ratio hardness analogue on IP similarity; >1 = the
                10th valid item is farther than the 10th unfiltered item)
  conductance   boundary/volume of the predicate set on the exact kNN graph
                (k=16, directed edges counted both ways; degree = in+out)
  compact       mean pairwise cosine within the predicate set (<=2048 sample)

Arms: natural (LOCKED P1 masks, asserted against the registry via the original
setup()) + 3 fresh seeded random-mask controls per predicate at identical
subset size (seed 20260805; control mask indices are PERSISTED so later method
reruns pair recall with the exact same masks).

Validation anchor: replicates the original M9 covariate gt_cluster_med_rank
(median-over-queries of mean global-top-1000 rank of the subset-GT items,
capped at 1000, computed with the ORIGINAL convention incl. self handling) and
compares against paper_assets/20260710_pillarB/filtered_ann_real_{A,B}.csv.

Corpus B nuance: image queries are the 200 frames chosen by the original
seeded RNG (reproduced exactly by importing setup() and calling it FIRST);
feature ranking excludes each query's own frame (sim set to -inf), matching
the original GT's self-exclusion; the validation covariate uses the original
convention (self NOT excluded from the global top-1000 list).

Run:  CUDA_VISIBLE_DEVICES=0 .../kiise-vlmdb/bin/python w1_compute_workload_features.py --corpus A
Output: p0_validity_audit/w1_features/{pair_features,predicate_features}_{A,B}.parquet
        + control_masks_{A,B}_seed20260805.npz + summary_{A,B}.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
P0DIR = HERE.parents[1]                      # p0_validity_audit
KIISE = next((p for p in HERE.parents if (p / "00_env").exists() or (p / "04_scripts").exists()), HERE.parents[3])                      # 2026_KIISE
sys.path.insert(0, str(KIISE / "scripts"))
import run_filtered_ann_real_predicate as base  # noqa: E402  (masks + setup + registry asserts)

OUT = P0DIR / "w1_features"
PAPER = KIISE / "paper_assets" / "20260710_pillarB"
K = 10
GLS_KS = (10, 50, 100, 1000)
CTRL_SEED = 20260805
N_CTRL = 3


def get_device():
    try:
        import torch
        if torch.cuda.is_available():
            return torch, "cuda"
        return torch, "cpu"
    except Exception:
        return None, "numpy"


def full_ranking(X: np.ndarray, Q: np.ndarray, self_ids: np.ndarray):
    """Exact IP similarity ranking of the whole corpus per query.
    Returns sorted_ids (nq,N) int32 desc-by-sim and sims_sorted (nq,N) fp16.
    Self items (self_ids>=0) are pushed to the very end via -inf."""
    torch, dev = get_device()
    nq, N = len(Q), len(X)
    if torch is not None:
        with torch.no_grad():
            Xt = torch.from_numpy(X).to(dev)
            Qt = torch.from_numpy(Q).to(dev)
            sims = Qt @ Xt.T                                    # (nq, N) fp32
            for qi, sid in enumerate(self_ids):
                if sid >= 0:
                    sims[qi, sid] = float("-inf")
            order = torch.argsort(sims, dim=1, descending=True)
            ss = torch.gather(sims, 1, order)
            sorted_ids = order.to(torch.int32).cpu().numpy()
            sims_sorted = ss.to(torch.float16).cpu().numpy()
            del Xt, Qt, sims, order, ss
            if dev == "cuda":
                torch.cuda.empty_cache()
    else:
        sims = Q @ X.T
        for qi, sid in enumerate(self_ids):
            if sid >= 0:
                sims[qi, sid] = -np.inf
        sorted_ids = np.argsort(-sims, axis=1).astype(np.int32)
        sims_sorted = np.take_along_axis(sims, sorted_ids, 1).astype(np.float16)
    return sorted_ids, sims_sorted


def knn_graph(X: np.ndarray, k: int = 16, chunk: int = 8192) -> np.ndarray:
    """Exact kNN neighbor ids (N,k) int32, self excluded, IP metric."""
    torch, dev = get_device()
    N = len(X)
    nbrs = np.empty((N, k), dtype=np.int32)
    if torch is not None:
        with torch.no_grad():
            Xt = torch.from_numpy(X).to(dev)
            Xh = Xt.half() if dev == "cuda" else Xt
            for s in range(0, N, chunk):
                e = min(s + chunk, N)
                sims = (Xh[s:e] @ Xh.T).float()
                rows = torch.arange(e - s, device=sims.device)
                sims[rows, torch.arange(s, e, device=sims.device)] = float("-inf")
                _, idx = torch.topk(sims, k, dim=1)
                nbrs[s:e] = idx.to(torch.int32).cpu().numpy()
                del sims, idx
            del Xt, Xh
            if dev == "cuda":
                torch.cuda.empty_cache()
    else:
        for s in range(0, N, 2048):
            e = min(s + 2048, N)
            sims = X[s:e] @ X.T
            sims[np.arange(e - s), np.arange(s, e)] = -np.inf
            nbrs[s:e] = np.argpartition(-sims, k, axis=1)[:, :k].astype(np.int32)
            # order within top-k not needed for graph edges
    return nbrs


def conductance(mask: np.ndarray, nbrs: np.ndarray, in_deg: np.ndarray) -> float:
    """phi(S) = directed crossing edges / min(vol(S), vol(V-S)), degree=in+out."""
    nb_in_S = mask[nbrs]                       # (N,k) bool
    cross = int((nb_in_S != mask[:, None]).sum())
    deg = nbrs.shape[1] + in_deg               # (N,) total degree
    vol_S = int(deg[mask].sum())
    vol_C = int(deg.sum()) - vol_S
    denom = min(vol_S, vol_C)
    return float(cross) / denom if denom > 0 else float("nan")


def compactness(X: np.ndarray, ids: np.ndarray, rng: np.random.Generator,
                cap: int = 2048) -> float:
    take = ids if len(ids) <= cap else rng.choice(ids, cap, replace=False)
    S = X[take]
    S = S / (np.linalg.norm(S, axis=1, keepdims=True) + 1e-9)
    G = S @ S.T
    n = len(S)
    return float((G.sum() - np.trace(G)) / (n * (n - 1)))


def pair_features(mask: np.ndarray, sorted_ids: np.ndarray,
                  sims_sorted: np.ndarray) -> dict:
    """Vectorized per-query features for one predicate arm."""
    nq, N = sorted_ids.shape
    s_g = mask.sum() / N
    mS = mask[sorted_ids]                              # (nq,N) bool in rank order
    cs = np.cumsum(mS, axis=1, dtype=np.int32)
    out = {"sel": np.full(nq, s_g, dtype=np.float32)}
    for k in GLS_KS:
        cnt = cs[:, k - 1].astype(np.float32)
        r = (cnt / k) / max(s_g, 1e-12)
        out[f"valid_top{k}"] = cnt
        out[f"rho_gls_k{k}"] = ((r - 1) / (r + 1)).astype(np.float32)
    total = cs[:, -1]
    rank10 = (cs < K).sum(axis=1).astype(np.int64)     # 0-based rank of 10th valid
    rank10[total < K] = N
    out["rank10_depth"] = rank10
    sim10_global = sims_sorted[:, K - 1].astype(np.float32)
    idx = np.clip(rank10, 0, N - 1)
    sim10_valid = sims_sorted[np.arange(nq), idx].astype(np.float32)
    out["sim10_global"] = sim10_global
    out["sim10_valid"] = sim10_valid
    with np.errstate(divide="ignore", invalid="ignore"):
        out["alpha_sim"] = np.where(sim10_valid > 0, sim10_global / sim10_valid,
                                    np.nan).astype(np.float32)
    return out


def m9_covariate(mask: np.ndarray, X: np.ndarray, Q: np.ndarray,
                 self_ids: np.ndarray, exact_top1000: np.ndarray) -> float:
    """Replicates the ORIGINAL gt_cluster_med_rank exactly (validation anchor):
    GT = exact IP top-K within subset, self-excluded via K+1; per-query mean
    rank of GT items inside the ORIGINAL global top-1000 (self included),
    1000.0 when none found; median over queries."""
    sub_ids = np.flatnonzero(mask)
    sub = np.ascontiguousarray(X[sub_ids])
    sims = Q @ sub.T                                    # (nq, m)
    kk = min(K + 1, sub.shape[0])
    part = np.argpartition(-sims, kk - 1, axis=1)[:, :kk]
    vals = []
    for qi in range(len(Q)):
        cand = part[qi][np.argsort(-sims[qi, part[qi]])]
        row = sub_ids[cand]
        gt = [i for i in row if i != self_ids[qi]][:K]
        hit = np.isin(exact_top1000[qi], gt)
        vals.append(float(np.where(hit)[0].mean()) if hit.any() else 1000.0)
    return float(np.median(vals))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["A", "B"], required=True)
    ap.add_argument("--skip-knn", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    t_all = time.time()

    # 1. corpus + LOCKED masks via the original setup (registry asserts inside).
    #    Must be the first consumer of the module RNG so corpus-B query
    #    selection reproduces the original run exactly.
    X, Q, self_ids, masks, layer = base.setup(args.corpus, None, None)
    N, d = X.shape
    print(f"[{args.corpus}] corpus={N}x{d} queries={len(Q)} layer={layer} "
          f"predicates={len(masks)}", flush=True)

    # 2. exact global ranking (features: self-excluded for B) + original-
    #    convention top-1000 (self included) for the validation covariate
    t0 = time.time()
    sorted_ids, sims_sorted = full_ranking(X, Q, self_ids)
    no_self = np.full(len(Q), -1)
    if (self_ids >= 0).any():
        orig_top, _ = full_ranking(X, Q, no_self)
        exact_top1000 = orig_top[:, :1000].copy()
        del orig_top
    else:
        exact_top1000 = sorted_ids[:, :1000]
    print(f"[rank] full ranking in {time.time()-t0:.1f}s", flush=True)

    # 3. kNN graph for conductance
    if not args.skip_knn:
        t0 = time.time()
        nbrs = knn_graph(X, 16)
        in_deg = np.bincount(nbrs.ravel(), minlength=N).astype(np.int64)
        print(f"[knn] k=16 exact graph in {time.time()-t0:.1f}s", flush=True)

    # 4. arms: natural + 3 seeded controls each (persisted)
    rng = np.random.default_rng(CTRL_SEED)
    comp_rng = np.random.default_rng(CTRL_SEED + 1)
    ctrl_store = {}
    pair_rows, pred_rows = [], []
    existing = pd.read_csv(PAPER / f"filtered_ann_real_{args.corpus}.csv")
    anchor = (existing[existing.kind != "control"]
              .groupby("predicate")["gt_cluster_med_rank"].first().to_dict())

    for pi, (name, kind, mask) in enumerate(masks):
        m = int(mask.sum())
        if m < K + 1:
            continue
        arms = [("natural", mask)]
        for r_i in range(N_CTRL):
            ctrl = np.zeros(N, bool)
            ids = rng.choice(N, m, replace=False)
            ctrl[ids] = True
            ctrl_store[f"{name}||ctrl{r_i}"] = ids.astype(np.int32)
            arms.append((f"random_ctrl_{r_i}", ctrl))
        t0 = time.time()
        for arm_name, am in arms:
            pf = pair_features(am, sorted_ids, sims_sorted)
            nq = len(Q)
            df = pd.DataFrame({"query_idx": np.arange(nq), **pf})
            df.insert(0, "arm", arm_name)
            df.insert(0, "kind", kind)
            df.insert(0, "predicate", name)
            pair_rows.append(df)
            prow = {"predicate": name, "kind": kind, "arm": arm_name,
                    "subset": m, "selectivity": m / N,
                    "compact": compactness(X, np.flatnonzero(am), comp_rng)}
            if not args.skip_knn:
                prow["conductance"] = conductance(am, nbrs, in_deg)
            if arm_name == "natural":
                med = m9_covariate(am, X, Q, self_ids, exact_top1000)
                prow["m9_med_rank_replicated"] = round(med, 1)
                prow["m9_med_rank_original"] = anchor.get(name, np.nan)
            pred_rows.append(prow)
        print(f"  [{pi+1}/{len(masks)}] {name} (m={m}) 4 arms in "
              f"{time.time()-t0:.1f}s", flush=True)

    pairs = pd.concat(pair_rows, ignore_index=True)
    preds = pd.DataFrame(pred_rows)
    pairs.to_parquet(OUT / f"pair_features_{args.corpus}.parquet", index=False)
    preds.to_parquet(OUT / f"predicate_features_{args.corpus}.parquet", index=False)
    np.savez_compressed(OUT / f"control_masks_{args.corpus}_seed{CTRL_SEED}.npz",
                        **ctrl_store)

    nat = preds[preds.arm == "natural"].dropna(subset=["m9_med_rank_original"])
    diff = (nat.m9_med_rank_replicated - nat.m9_med_rank_original).abs()
    summary = {
        "corpus": args.corpus, "N": int(N), "dim": int(d), "queries": int(len(Q)),
        "layer": layer, "predicates": int(len(masks)),
        "arms_per_predicate": 1 + N_CTRL, "ctrl_seed": CTRL_SEED,
        "gls_ks": list(GLS_KS), "knn_k": 16,
        "validation": {
            "n_anchored": int(len(nat)),
            "med_rank_abs_diff_max": float(diff.max()) if len(nat) else None,
            "med_rank_abs_diff_mean": float(diff.mean()) if len(nat) else None,
        },
        "wall_s": round(time.time() - t_all, 1),
    }
    (OUT / f"summary_{args.corpus}.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary["validation"], indent=2))
    print(f"[saved] {OUT} in {summary['wall_s']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
