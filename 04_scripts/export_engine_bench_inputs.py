#!/usr/bin/env python3
"""B-4 stage 1 [prereg 420 Amendment 5]: freeze engine-independent inputs.

For each corpus (A: sinnaedoro 132,521x512 text-query layer; B: 522 frames
143,830x512 image-query layer) this exports, per predicate (P1-locked reals
re-derived and asserted + NEW-seed same-size random controls):
  - the boolean mask, exact filtered top-10 GT (self-excluded, faiss FlatIP),
  - the M9 clustering covariate (median global exact rank of subset GT items),
and the query matrix / self ids. Engines (Milvus/Weaviate) then only search
and are scored against this frozen GT — no engine touches GT computation.

Controls: default_rng(20260712 + predicate_index) — deliberately a different,
declared draw than B-1's 20260710 stream (within-engine real-vs-control
pairing is the unit of claim). --faiss-seed-check additionally re-scores the
faiss shared-index methods (recall only) on these NEW control masks, giving
the M9 seed-sensitivity table (codex F7 response).

Run (kiise-vlmdb env):  export_engine_bench_inputs.py --corpus A [--faiss-seed-check]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

import run_filtered_ann_real_predicate as b1  # mask builders + paths (no faiss at import)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260712_engine_replication"
P1 = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260710_pillarB"
K = 10
CTRL_SEED = 20260712


def load_corpus(corpus: str):
    if corpus == "A":
        X = np.load(b1.SIN / "frame_embeddings.npy").astype("float32")
        X /= (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
        fi = pd.read_parquet(b1.SIN / "frame_index.parquet")
        Q = np.load(b1.SIN / "queries.npy").astype("float32")
        Q /= (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9)
        masks = b1.masks_corpus_a(fi)
        self_ids = np.full(len(Q), -1)
    else:
        V = b1.V522 / "visual_embeddings_clip"
        X = np.load(V / "frame_embeddings.npy").astype("float32")
        fi = pd.read_parquet(V / "frame_index.parquet")
        join = pd.read_parquet(b1.V522 / "visual_sensor_join.parquet")
        j = join[join.join_ok_120s][["visual_video_id", "split", "time_of_day", "hour",
                                     "sig_has_yellow", "sig_has_pedestrian", "veh_density_bin"]]
        f = fi.merge(j, on=["visual_video_id", "split"], how="left", suffixes=("_fn", ""))
        masks = b1.masks_corpus_b(f)
        # B-1 comparability: qidx is the FIRST draw from default_rng(20260710)
        qidx = np.random.default_rng(20260710).choice(len(X), 200, replace=False)
        Q = X[qidx]
        self_ids = qidx
    reg = pd.read_csv(P1 / f"P1_predicates_{corpus}.csv")
    reg = dict(zip(reg.predicate, reg["count"]))
    for n, _, m in masks:
        if n in reg:
            assert int(m.sum()) == int(reg[n]), f"P1 mismatch {n}: {m.sum()} != {reg[n]}"
    return X, Q, self_ids, masks


def gt_for_mask(faiss, X, Q, self_ids, mask, exact_top):
    sub_ids = np.flatnonzero(mask)
    sub = np.ascontiguousarray(X[sub_ids])
    gsub = faiss.IndexFlatIP(X.shape[1]); gsub.add(sub)
    _, gl = gsub.search(Q, K + 1)
    gt = []
    for row, sid in zip(sub_ids[gl], self_ids):
        gt.append([i for i in row if i != sid][:K])
    gt = np.array(gt, dtype="int64")
    med_rank = float(np.median([
        np.where(np.isin(exact_top[qi], gt[qi]))[0].mean()
        if np.isin(exact_top[qi], gt[qi]).any() else 1000.0
        for qi in range(len(Q))]))
    return gt, med_rank


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["A", "B"], required=True)
    ap.add_argument("--faiss-seed-check", action="store_true")
    args = ap.parse_args()
    import faiss
    faiss.omp_set_num_threads(0)
    OUT.mkdir(parents=True, exist_ok=True)

    X, Q, self_ids, masks = load_corpus(args.corpus)
    N, d = X.shape
    print(f"[{args.corpus}] corpus={N}x{d} queries={len(Q)} reals={len(masks)}", flush=True)

    flat = faiss.IndexFlatIP(d); flat.add(X)
    _, exact_top = flat.search(Q, 1000)

    rows, mask_stack, gt_stack = [], [], []
    for pi, (name, kind, mask) in enumerate(masks):
        m = int(mask.sum())
        if m < K + 1:
            print(f"  skip {name} (m={m} < K+1)"); continue
        ctrl = np.zeros(N, bool)
        ctrl[np.random.default_rng(CTRL_SEED + pi).choice(N, m, replace=False)] = True
        for tag, knd, mk in [(name, kind, mask),
                             (f"CTRL(s={m/N:.4f})|{name}", "control", ctrl)]:
            gt, med = gt_for_mask(faiss, X, Q, self_ids, mk, exact_top)
            rows.append({"mask_id": len(rows), "predicate": tag, "kind": knd,
                         "pair": name, "subset": int(mk.sum()),
                         "selectivity": round(mk.sum() / N, 5),
                         "gt_cluster_med_rank": round(med, 1)})
            mask_stack.append(np.packbits(mk)); gt_stack.append(gt)
        print(f"  [{pi+1}/{len(masks)}] {name} m={m} done", flush=True)

    meta = pd.DataFrame(rows)
    meta.to_csv(OUT / f"inputs_{args.corpus}_meta.csv", index=False)
    np.savez_compressed(
        OUT / f"inputs_{args.corpus}.npz",
        masks_packed=np.stack(mask_stack), n=N,
        gt=np.stack(gt_stack), queries=Q, self_ids=self_ids)
    print(f"[saved] {OUT}/inputs_{args.corpus}.npz + meta ({len(meta)} masks)")

    if args.faiss_seed_check:
        # F7 lane: recall-only re-score of shared-index faiss methods on NEW controls
        t0 = time.perf_counter()
        full_h = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT)
        full_h.hnsw.efConstruction = 200; full_h.add(X); full_h.hnsw.efSearch = 64
        quant = faiss.IndexFlatIP(d)
        full_ivf = faiss.IndexIVFFlat(quant, d, 1024, faiss.METRIC_INNER_PRODUCT)
        full_ivf.train(X); full_ivf.add(X)
        print(f"[seed-check] shared indexes built {time.perf_counter()-t0:.0f}s", flush=True)
        sc = []
        for r, mkp, gt in zip(rows, mask_stack, gt_stack):
            if r["kind"] != "control":
                continue
            mask = np.unpackbits(mkp)[:N].astype(bool)
            s = r["selectivity"]
            got_rows = {}
            for mult in (1, 2, 4):
                Kp = int(min(N, np.ceil(K / max(s, 1e-9)) * mult))
                _, aa = full_h.search(Q, Kp + 1)
                got = []
                for row_, sid in zip(aa, self_ids):
                    sel = row_[(mask[row_]) & (row_ != sid)][:K]
                    got.append(np.pad(sel, (0, K - len(sel)), constant_values=-1))
                got_rows[f"postfilter_hnsw_K{mult}x"] = np.array(got)
            sub_ids = np.flatnonzero(mask)
            sel = faiss.IDSelectorBatch(sub_ids.astype("int64"))
            for nprobe in (8, 32):
                sp = faiss.SearchParametersIVF(sel=sel, nprobe=nprobe)
                _, a = full_ivf.search(Q, K + 1, params=sp)
                got_rows[f"single_stage_ivf_batch_np{nprobe}"] = b1._self_excl(a, self_ids)
            for meth, got in got_rows.items():
                rec = float(b1.recall_rows(gt, got).mean())
                sc.append({"predicate": r["predicate"], "pair": r["pair"],
                           "selectivity": s, "method": meth,
                           "recall_at_10_newseed": round(rec, 4)})
        pd.DataFrame(sc).to_csv(OUT / f"faiss_seedcheck_{args.corpus}.csv", index=False)
        print(f"[saved] faiss_seedcheck_{args.corpus}.csv ({len(sc)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
