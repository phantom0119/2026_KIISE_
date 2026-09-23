#!/usr/bin/env python3
"""URBAN-INDEX: accuracy(ANN-recall) x latency x cost benchmark of vector index
STRUCTURES for VLM-QA retrieval over the scaled 시내도로 corpus.

Rigor (per the pre-registered design / prior-note traps):
- Isolate index.search ONLY (no embedding/glue); single-thread serving latency.
- Warm-up discarded; R repeats; per-query p50/p95/p99; heavy-tail reported.
- ANN-recall@10 vs the exact Flat ground-truth (index fidelity, separate from task acc).
- Cost VECTOR: build wall-time, index bytes (serialized), per-query CPU.
- Scale sweep N to locate the exact->ANN crossover; structure is the ONLY knob.
"""
from __future__ import annotations
import argparse, json, time, tempfile, os
from pathlib import Path
import numpy as np

K = 10


def recall_at_k(gt_ids, ann_ids, k=K):
    return float(np.mean([len(set(a[:k]) & set(g[:k])) / k for a, g in zip(ann_ids, gt_ids)]))


def measure_latency(index, queries, repeats, warmup):
    import faiss
    faiss.omp_set_num_threads(1)  # single-thread serving-latency isolation
    lat = []
    for q in queries:
        qq = q.reshape(1, -1)
        for _ in range(warmup):
            index.search(qq, K)
        for _ in range(repeats):
            t = time.perf_counter(); index.search(qq, K); lat.append((time.perf_counter() - t) * 1000)
    a = np.array(lat)
    return {"p50_ms": float(np.percentile(a, 50)), "p95_ms": float(np.percentile(a, 95)),
            "p99_ms": float(np.percentile(a, 99)), "mean_ms": float(a.mean())}


def index_bytes(index):
    import faiss
    with tempfile.NamedTemporaryFile(suffix=".faiss", delete=False) as f:
        faiss.write_index(index, f.name); n = os.path.getsize(f.name); os.unlink(f.name)
    return n


def structure_key(spec):
    kind = spec["kind"]
    if kind == "hnsw":
        return kind, spec["M"], spec.get("efC", 200)
    if kind == "ivfflat":
        return kind, spec["nlist"]
    if kind == "ivfpq":
        return kind, spec["nlist"], spec["m"]
    return (kind,)


def build_index(db, spec):
    import faiss
    faiss.omp_set_num_threads(0)  # ALL threads for build (representative build-time cost)
    d = db.shape[1]; kind = spec["kind"]
    t0 = time.time()
    if kind == "flat":
        idx = faiss.IndexFlatIP(d)
    elif kind == "ivfflat":
        quant = faiss.IndexFlatIP(d)
        idx = faiss.IndexIVFFlat(quant, d, spec["nlist"], faiss.METRIC_INNER_PRODUCT)
        idx.cp.seed = spec["_seed"]
        idx.train(db)
    elif kind == "ivfpq":
        quant = faiss.IndexFlatIP(d)
        idx = faiss.IndexIVFPQ(quant, d, spec["nlist"], spec["m"], 8, faiss.METRIC_INNER_PRODUCT)
        idx.cp.seed = spec["_seed"]
        idx.pq.cp.seed = spec["_seed"]
        idx.train(db)
    elif kind == "hnsw":
        idx = faiss.IndexHNSWFlat(d, spec["M"], faiss.METRIC_INNER_PRODUCT)
        idx.hnsw.efConstruction = spec.get("efC", 200)
        idx.hnsw.rng = faiss.RandomGenerator(spec["_seed"])
    idx.add(db)
    build_s = time.time() - t0
    return idx, build_s, index_bytes(idx)


def eval_index(idx, build_s, serialized_bytes, queries, gt_ids, spec):
    kind = spec["kind"]
    if kind in ("ivfflat", "ivfpq"):
        idx.nprobe = spec["nprobe"]
    if kind == "hnsw":
        idx.hnsw.efSearch = spec["efSearch"]
    _, ann = idx.search(queries, K)  # batch recall (multi-thread; result is thread-invariant)
    rec = 1.0 if kind == "flat" else recall_at_k(gt_ids, ann)
    lat = measure_latency(idx, queries, spec["_rep"], spec["_warm"])
    return {**{k: v for k, v in spec.items() if not k.startswith("_")},
            "recall_at_10": round(rec, 4), "build_s": round(build_s, 3),
            "index_mb": round(serialized_bytes / 1e6, 2), **{k: round(v, 4) for k, v in lat.items()}}


def specs_for(N):
    S = [{"kind": "flat"}]
    # FAISS warns below roughly 39 training vectors per centroid.  Keeping the
    # stricter threshold prevents small-scale IVF/PQ points from being based on
    # under-trained quantizers.
    nlists = [nl for nl in (256, 1024, 4096) if nl * 39 <= N]
    for nl in nlists:
        for npb in (1, 8, 32, 128):
            if npb <= nl:
                S.append({"kind": "ivfflat", "nlist": nl, "nprobe": npb})
    for M in (16, 32):
        for ef in (16, 64, 256):
            S.append({"kind": "hnsw", "M": M, "efSearch": ef, "efC": 200})
    if not nlists:
        return S
    nl = max(value for value in nlists if value <= 1024)
    for m in (32, 64):
        for npb in (8, 32):
            S.append({"kind": "ivfpq", "nlist": nl, "m": m, "nprobe": npb})
    return S


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="db pool frame_embeddings.npy (real-first if augmented)")
    ap.add_argument("--queries", default=None, help="held-out query vectors .npy (if omitted, split from corpus)")
    ap.add_argument("--real-n", type=int, default=0, help="scales <= real-n are labeled 'real', else 'synthetic_aug'")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-queries", type=int, default=1000)
    ap.add_argument("--scales", default="10000,50000,100000,200000,300000")
    ap.add_argument("--repeats", type=int, default=20)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--full-grid-at", type=int, default=300000, help="run full tuning grid only at this N")
    ap.add_argument("--seed", type=int, default=20260717)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    import faiss  # noqa
    X = np.load(args.corpus).astype("float32")
    X /= (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    if args.queries:
        queries = np.load(args.queries).astype("float32")
        queries /= (np.linalg.norm(queries, axis=1, keepdims=True) + 1e-9)
        db_pool = X  # in given order (real-first for augmented corpora)
    else:
        rng = np.random.default_rng(20260709)
        perm = rng.permutation(len(X))
        queries = X[perm[: args.n_queries]]; db_pool = X[perm[args.n_queries:]]
    print(f"[data] db_pool={len(db_pool)} dim={X.shape[1]} queries={len(queries)} real_n={args.real_n}")
    scales = [s for s in (int(x) for x in args.scales.split(",")) if s <= len(db_pool)]

    rows = []
    for N in scales:
        db = db_pool[:N]
        gt = faiss.IndexFlatIP(db.shape[1]); gt.add(db)
        faiss.omp_set_num_threads(0)
        _, gt_ids = gt.search(queries, K)
        specs = specs_for(N)
        # scale sweep: representative configs at every N; full grid only at --full-grid-at
        if N != args.full_grid_at:
            representative_nlist = 1024 if 1024 * 39 <= N else 256
            specs = [s for s in specs if s["kind"] == "flat"
                     or (s["kind"] == "ivfflat" and s.get("nlist") == representative_nlist
                         and s["nprobe"] in (1, 32))
                     or (s["kind"] == "hnsw" and s["M"] == 32 and s["efSearch"] in (16, 64))]
        built = {}
        for s in specs:
            s["_rep"], s["_warm"], s["_seed"] = args.repeats, args.warmup, args.seed
            key = structure_key(s)
            if key not in built:
                built[key] = build_index(db, s)
            idx, build_s, serialized_bytes = built[key]
            r = eval_index(idx, build_s, serialized_bytes, queries, gt_ids, s)
            r["N"] = N
            r["regime"] = "real" if (args.real_n == 0 or N <= args.real_n) else "synthetic_aug"
            rows.append(r)
            print(f"  N={N:>6} {r.get('kind'):8} "
                  f"{ {k:v for k,v in r.items() if k in ('nlist','nprobe','M','efSearch','m')} } "
                  f"recall={r['recall_at_10']:.3f} p50={r['p50_ms']:.3f}ms p95={r['p95_ms']:.3f}ms "
                  f"build={r['build_s']:.2f}s {r['index_mb']:.0f}MB")
    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_csv(out / "index_benchmark.csv", index=False)
    df.to_parquet(out / "index_benchmark.parquet")
    (out / "manifest.json").write_text(json.dumps({
        "corpus": args.corpus, "n_vectors": int(len(X)), "dim": int(X.shape[1]),
        "n_queries": args.n_queries, "scales": scales, "repeats": args.repeats,
        "seed": args.seed,
        "metric": "inner_product(cosine, normalized)", "k": K,
        "faiss_threads_latency": 1, "created": "20260709",
    }, ensure_ascii=False, indent=2))
    print(f"\n[done] {len(rows)} configs -> {out}")


if __name__ == "__main__":
    main()
