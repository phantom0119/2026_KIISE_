#!/usr/bin/env python3
"""G1 method runner: per-pair Recall@10 of the naive paths on any arm.

Methods (EXP03-identical configs, recall path only — no timing):
  postfilter_hnsw_K4x   full HNSW (M=32, efC=200, efS=64, IP), K'=min(N,ceil(10/s)*4)
  single_stage_ivf_np8  full IVF1024 + IDSelectorBatch, nprobe=8
  single_stage_ivf_np32 idem, nprobe=32

Arms:
  natural   g1/<C>/natural/pair_manifest.parquet + locked P1 masks (base.setup)
  random{r} same manifest, W1 stored control masks (seed 20260805, replicate r)
  matched   g1/<C>/matched/tests.jsonl (HCBGen match_pdf output); masks rebuilt
            from payloads.jsonl; query_idx recovered by exact fp32 byte match
            against the real query set (B: enables self-exclusion)

GT: this script's exact IP filtered top-10 (B: self-excluded) for EVERY arm
(uniform convention; HCBGen closest_ids used only as a cross-check).
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
P0DIR = HERE.parents[1]
KIISE = HERE.parents[3]
sys.path.insert(0, str(KIISE / "scripts"))
import run_filtered_ann_real_predicate as base  # noqa: E402

K = 10
W1 = P0DIR / "w1_features"


def gpu_topk_filtered(X, Q, mask, k, self_ids=None):
    import torch
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    sub_ids = np.flatnonzero(mask)
    with torch.no_grad():
        S = torch.from_numpy(np.ascontiguousarray(X[sub_ids])).to(dev)
        Qt = torch.from_numpy(np.ascontiguousarray(Q)).to(dev)
        sims = Qt @ S.T
        if self_ids is not None:
            pos = {int(g): j for j, g in enumerate(sub_ids)}
            for qi, sid in enumerate(self_ids):
                j = pos.get(int(sid), -1)
                if j >= 0:
                    sims[qi, j] = float("-inf")
        kk = min(k, len(sub_ids))
        _, idx = sims.topk(kk, dim=1)
        out = sub_ids[idx.cpu().numpy()]
        del S, Qt, sims, idx
        if dev == "cuda":
            torch.cuda.empty_cache()
    return out


def recall_rows(gt, got):
    return np.array([len(set(a[:K]) & set(g[:K])) / K for a, g in zip(got, gt)])


def run_group(name, arm, mask, Qg, qsids, X, full_h, full_ivf, faiss):
    """All methods for one (predicate/condition, query-batch) group."""
    N = len(X)
    sub_ids = np.flatnonzero(mask)
    s = len(sub_ids) / N
    if len(sub_ids) < K + 1:
        return None
    gt = gpu_topk_filtered(X, Qg, mask, K, qsids)
    rows = {}

    Kp = int(min(N, np.ceil(K / max(s, 1e-9)) * 4))
    _, aa = full_h.search(Qg, Kp + 1)
    got = []
    for row, sid in zip(aa, qsids if qsids is not None else np.full(len(Qg), -1)):
        sel = row[(mask[row]) & (row != sid)][:K]
        got.append(np.pad(sel, (0, K - len(sel)), constant_values=-1))
    rows["postfilter_hnsw_K4x"] = recall_rows(gt, np.array(got))

    sel = faiss.IDSelectorBatch(sub_ids.astype("int64"))
    for nprobe in (8, 32):
        sp = faiss.SearchParametersIVF(sel=sel, nprobe=nprobe)
        _, a = full_ivf.search(Qg, K + 1, params=sp)
        got = []
        for row, sid in zip(a, qsids if qsids is not None else np.full(len(Qg), -1)):
            r = [i for i in row if i != sid and i >= 0][:K]
            got.append(np.pad(np.array(r), (0, K - len(r)), constant_values=-1))
        rows[f"single_stage_ivf_np{nprobe}"] = recall_rows(gt, np.array(got))
    return rows, s, gt


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["A", "B"], required=True)
    ap.add_argument("--arms", nargs="+", required=True,
                    help="subset of: natural random0 random1 random2 matched")
    args = ap.parse_args()
    import faiss
    faiss.omp_set_num_threads(0)
    G1 = P0DIR / "g1" / args.corpus
    OUT = G1 / "method_recall"
    OUT.mkdir(exist_ok=True)

    X, Q, self_ids, masks, _ = base.setup(args.corpus, None, None)
    N, d = X.shape
    mask_by_name = {n: m for n, k_, m in masks}
    manifest = pd.read_parquet(G1 / "natural" / "pair_manifest.parquet")
    have_self = (self_ids >= 0).any()

    t0 = time.time()
    full_h = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT)
    full_h.hnsw.efConstruction = 200
    full_h.add(X)
    full_h.hnsw.efSearch = 64
    full_ivf = faiss.IndexIVFFlat(faiss.IndexFlatIP(d), d, 1024, faiss.METRIC_INNER_PRODUCT)
    full_ivf.train(X)
    full_ivf.add(X)
    print(f"[{args.corpus}] indexes built in {time.time()-t0:.0f}s", flush=True)

    for arm in args.arms:
        t0 = time.time()
        recs = []
        if arm in ("natural",) or arm.startswith("random"):
            ctrl = None
            if arm.startswith("random"):
                r = int(arm[-1])
                z = np.load(W1 / f"control_masks_{args.corpus}_seed20260805.npz")
                ctrl = {k.split("||")[0]: z[k] for k in z.files if k.endswith(f"ctrl{r}")}
            for name, grp in manifest.groupby("predicate", sort=False):
                if ctrl is None:
                    m = mask_by_name[name]
                else:
                    m = np.zeros(N, bool)
                    m[ctrl[name]] = True
                qidx = grp.query_idx.to_numpy()
                qsids = self_ids[qidx] if have_self else None
                res = run_group(name, arm, m, Q[qidx], qsids, X, full_h, full_ivf, faiss)
                if res is None:
                    continue
                rows, s, _ = res
                for meth, rec in rows.items():
                    for ti, rv in zip(grp.index.to_numpy(), rec):
                        recs.append({"test_idx": int(ti), "cluster": name, "arm": arm,
                                     "method": meth, "sel": s, "recall": float(rv)})
        elif arm == "matched":
            tests = [json.loads(l) for l in open(G1 / "matched" / "tests.jsonl")]
            payloads = [json.loads(l) for l in open(G1 / "matched" / "payloads.jsonl")]
            cols = {}
            for a_ in set(k for p in payloads for k in p):
                cols[a_] = np.array([p.get(a_, -1) for p in payloads], dtype=np.int64)
            qhash = {Q[i].astype("<f4").tobytes(): i for i in range(len(Q))}
            n_selfmap = 0
            groups: dict[str, dict] = {}
            for ti, t in enumerate(tests):
                conds = tuple(sorted((a_, r_["match"]["value"])
                                     for c in t["conditions"]["and"] for a_, r_ in c.items()))
                g = groups.setdefault(str(conds), {"conds": conds, "ti": [], "qv": [], "qi": []})
                g["ti"].append(ti)
                qv = np.array(t["query"], dtype="<f4")
                g["qv"].append(qv)
                qi = qhash.get(qv.tobytes(), -1)
                g["qi"].append(qi)
                if qi >= 0:
                    n_selfmap += 1
            print(f"[matched] {len(tests)} tests, {len(groups)} condition groups, "
                  f"{n_selfmap} queries matched to real query set", flush=True)
            xcheck_ok, xcheck_n = 0, 0
            for g in groups.values():
                m = np.ones(N, bool)
                for a_, v in g["conds"]:
                    m &= cols[a_] == v
                if m.sum() < K + 1:
                    continue
                Qg = np.stack(g["qv"])
                qi = np.array(g["qi"])
                qsids = (self_ids[qi] * (qi >= 0) + -1 * (qi < 0)) if have_self else None
                res = run_group(str(g["conds"]), arm, m, Qg, qsids, X, full_h, full_ivf, faiss)
                if res is None:
                    continue
                rows, s, gt = res
                for j, ti in enumerate(g["ti"]):
                    theirs = set(tests[ti]["closest_ids"][:K])
                    if qsids is None or qsids[j] < 0:      # cross-check only w/o self
                        xcheck_n += 1
                        xcheck_ok += len(theirs & set(gt[j])) >= K - 1
                for meth, rec in rows.items():
                    for j, ti in enumerate(g["ti"]):
                        recs.append({"test_idx": int(ti), "cluster": str(g["conds"]),
                                     "arm": arm, "method": meth, "sel": s,
                                     "recall": float(rec[j])})
            if xcheck_n:
                print(f"[matched] GT cross-check (no-self pairs): {xcheck_ok}/{xcheck_n} "
                      f"agree >=9/10 with HCBGen closest_ids", flush=True)
        df = pd.DataFrame(recs)
        df.to_parquet(OUT / f"recall_{arm}.parquet", index=False)
        print(f"[{args.corpus}][{arm}] {len(df)} rows "
              f"({df.test_idx.nunique()} pairs) in {time.time()-t0:.0f}s; "
              f"mean recall by method: "
              f"{df.groupby('method').recall.mean().round(4).to_dict()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
