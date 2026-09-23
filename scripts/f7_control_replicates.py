#!/usr/bin/env python3
"""B-4 [Amendment 5a (7)]: control-mask replicate draws for M9 seed sensitivity.

For each real predicate, draws r=1..5 additional same-size random control
masks (seed 20260712 + 1000*r + pi, pi = mask-generation order; r=0 is the
stage-1 draw) and scores the faiss shared-index methods (recall only) on each.
Output: per predicate x method, the distribution (mean/SD/range) of the
control recall and of the implied M9 overestimate across the 6 total draws.

Run (kiise-vlmdb env, background): f7_control_replicates.py --corpus A
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import pandas as pd

import run_filtered_ann_real_predicate as b1
from export_engine_bench_inputs import load_corpus, gt_for_mask

R2 = Path(__file__).resolve().parents[1]
OUT = R2 / "paper_assets" / "20260712_engine_replication"
K = 10
REPS = range(1, 6)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["A", "B"], required=True)
    args = ap.parse_args()
    import faiss
    faiss.omp_set_num_threads(0)

    X, Q, self_ids, masks = load_corpus(args.corpus)
    N, d = X.shape
    flat = faiss.IndexFlatIP(d); flat.add(X)
    _, exact_top = flat.search(Q, 1000)
    t0 = time.perf_counter()
    full_h = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT)
    full_h.hnsw.efConstruction = 200; full_h.add(X); full_h.hnsw.efSearch = 64
    quant = faiss.IndexFlatIP(d)
    full_ivf = faiss.IndexIVFFlat(quant, d, 1024, faiss.METRIC_INNER_PRODUCT)
    full_ivf.train(X); full_ivf.add(X)
    print(f"[shared] indexes built {time.perf_counter()-t0:.0f}s", flush=True)

    rows = []
    for pi, (name, kind, mask) in enumerate(masks):
        m = int(mask.sum())
        if m < K + 1:
            continue
        s = m / N
        for r in REPS:
            ctrl = np.zeros(N, bool)
            ctrl[np.random.default_rng(20260712 + 1000 * r + pi).choice(
                N, m, replace=False)] = True
            gt, _ = gt_for_mask(faiss, X, Q, self_ids, ctrl, exact_top)
            got = {}
            for mult in (1, 2, 4):
                Kp = int(min(N, np.ceil(K / max(s, 1e-9)) * mult))
                _, aa = full_h.search(Q, Kp + 1)
                g = []
                for row_, sid in zip(aa, self_ids):
                    sel = row_[(ctrl[row_]) & (row_ != sid)][:K]
                    g.append(np.pad(sel, (0, K - len(sel)), constant_values=-1))
                got[f"postfilter_hnsw_K{mult}x"] = np.array(g)
            sub_ids = np.flatnonzero(ctrl)
            selr = faiss.IDSelectorBatch(sub_ids.astype("int64"))
            for nprobe in (8, 32):
                sp = faiss.SearchParametersIVF(sel=selr, nprobe=nprobe)
                _, a = full_ivf.search(Q, K + 1, params=sp)
                got[f"single_stage_ivf_batch_np{nprobe}"] = b1._self_excl(a, self_ids)
            for meth, gg in got.items():
                rec = float(b1.recall_rows(gt, gg).mean())
                rows.append({"pair": name, "kind": kind, "selectivity": round(s, 5),
                             "replicate": r, "method": meth,
                             "recall_at_10": round(rec, 4)})
        pd.DataFrame(rows).to_csv(OUT / f"f7_replicates_{args.corpus}.csv", index=False)
        print(f"  [{pi+1}/{len(masks)}] {name} x{len(list(REPS))} reps done", flush=True)
    print(f"[saved] f7_replicates_{args.corpus}.csv ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
