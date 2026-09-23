#!/usr/bin/env python3
"""Selectivity axis: how metadata pre/post-filtering interacts with index STRUCTURE
on accuracy x latency, over the real 시내도로 corpus (spatiotemporal metadata modality).

For a metadata predicate of selectivity s (fraction of corpus passing), compare:
  prefilter_flat : restrict to the s*N subset, exact search   (recall 1.0, latency ~ s*N)
  prefilter_hnsw : build HNSW on the subset, search           (recall ~1, latency ~const)
  postfilter_hnsw: search FULL HNSW top-K'(=k/s over-fetch), filter to subset, take k
  full_flat      : exact over full corpus then filter          (recall 1.0, latency ~ N)
Ground truth = exact top-k within the filtered subset.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import numpy as np

K = 10


def recall(gt, got, k=K):
    return float(np.mean([len(set(a[:k]) & set(g[:k])) / k for a, g in zip(got, gt)]))


def lat_ms(fn, queries, rep, warm):
    t = []
    for q in queries:
        for _ in range(warm):
            fn(q)
        for _ in range(rep):
            t0 = time.perf_counter(); fn(q); t.append((time.perf_counter() - t0) * 1000)
    a = np.array(t)
    return float(np.percentile(a, 50)), float(np.percentile(a, 95))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True)
    ap.add_argument("--queries", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--selectivities", default="0.01,0.05,0.1,0.25,0.5,1.0")
    ap.add_argument("--repeats", type=int, default=15)
    ap.add_argument("--warmup", type=int, default=5)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    import faiss
    X = np.load(args.corpus).astype("float32"); X /= (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    Q = np.load(args.queries).astype("float32"); Q /= (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9)
    N, d = X.shape
    rng = np.random.default_rng(20260709)
    print(f"[data] corpus={N} dim={d} queries={len(Q)}")

    # full-corpus HNSW (built once) for postfilter
    faiss.omp_set_num_threads(0)
    full_h = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT); full_h.hnsw.efConstruction = 200
    full_h.add(X); full_h.hnsw.efSearch = 256
    full_flat = faiss.IndexFlatIP(d); full_flat.add(X)

    rows = []
    for s in (float(x) for x in args.selectivities.split(",")):
        m = int(s * N)
        mask = np.zeros(N, bool); mask[rng.choice(N, m, replace=False)] = True
        sub_ids = np.where(mask)[0]
        sub = X[sub_ids]
        # ground truth: exact top-k within subset
        faiss.omp_set_num_threads(0)
        gsub = faiss.IndexFlatIP(d); gsub.add(sub)
        _, gt_local = gsub.search(Q, K); gt = sub_ids[gt_local]

        # prefilter_flat
        pf = faiss.IndexFlatIP(d); pf.add(sub)
        _, a = pf.search(Q, K); r_pff = recall(gt, sub_ids[a])
        faiss.omp_set_num_threads(1)
        p50, p95 = lat_ms(lambda q: pf.search(q.reshape(1, -1), K), Q, args.repeats, args.warmup)
        rows.append({"selectivity": s, "subset": m, "method": "prefilter_flat", "recall_at_10": round(r_pff, 4), "p50_ms": round(p50, 4), "p95_ms": round(p95, 4)})

        # prefilter_hnsw (build on subset)
        faiss.omp_set_num_threads(0); tb = time.time()
        ph = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT); ph.hnsw.efConstruction = 200; ph.add(sub); ph.hnsw.efSearch = 64
        bld = time.time() - tb
        _, a = ph.search(Q, K); r_pfh = recall(gt, sub_ids[a])
        faiss.omp_set_num_threads(1)
        p50, p95 = lat_ms(lambda q: ph.search(q.reshape(1, -1), K), Q, args.repeats, args.warmup)
        rows.append({"selectivity": s, "subset": m, "method": "prefilter_hnsw", "recall_at_10": round(r_pfh, 4), "p50_ms": round(p50, 4), "p95_ms": round(p95, 4), "build_s": round(bld, 2)})

        # postfilter over full HNSW: over-fetch K' = min(N, ceil(k/s)*3), filter
        Kp = int(min(N, np.ceil(K / max(s, 1e-6)) * 3))
        faiss.omp_set_num_threads(0)
        _, aa = full_h.search(Q, Kp)
        got = [ [i for i in row if mask[i]][:K] for row in aa ]
        got = [ g + [-1] * (K - len(g)) for g in got ]
        r_post = recall(gt, np.array(got))
        faiss.omp_set_num_threads(1)
        p50, p95 = lat_ms(lambda q: full_h.search(q.reshape(1, -1), Kp), Q, args.repeats, args.warmup)
        rows.append({"selectivity": s, "subset": m, "method": f"postfilter_hnsw(K'={Kp})", "recall_at_10": round(r_post, 4), "p50_ms": round(p50, 4), "p95_ms": round(p95, 4)})

        print(f"  s={s:5.2f} (n={m:>7}): prefilter_flat r{r_pff:.3f} {rows[-3]['p50_ms']:.3f}ms | prefilter_hnsw r{r_pfh:.3f} {rows[-2]['p50_ms']:.3f}ms | postfilter r{r_post:.3f} {rows[-1]['p50_ms']:.3f}ms")

    import pandas as pd
    pd.DataFrame(rows).to_csv(out / "filtered_ann.csv", index=False)
    (out / "manifest.json").write_text(json.dumps({"corpus": args.corpus, "N": N, "k": K,
        "selectivities": args.selectivities, "note": "random-mask metadata predicate; GT=exact within subset"}, indent=2))
    print(f"\n[done] -> {out}")


if __name__ == "__main__":
    main()
