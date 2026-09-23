#!/usr/bin/env python3
"""Pillar B-3 [prereg 420 §3 + AMD-M3]: real ANN indexes inside PostgreSQL/pgvector.

Corpus = sinnaedoro corpus_real (132,521 x 512, L2-normalized) with denormalized
facet columns (location/date/hour) — single-row schema, `ORDER BY embedding <#> q
LIMIT k` (no EAV/GROUP BY; those cannot use vector indexes) [M3a].

Measures, on ONE warm connection (jit off):
  unfiltered: exact (seq-scan GT) vs HNSW(m in {16,32}, efC=200, ef_search in
              {16,64,256}) vs IVFFlat(lists in {364,1024}, probes in {1,8,32})
              -> recall@10 vs exact, client p50/p95 (W=2 warm + R=5 repeats,
              per-query median), build wall, pg_relation_size.
  filtered  : 4 preregistered P1 predicates x GUC matrix
              hnsw.iterative_scan in {off, relaxed_order} [M3b, pgvector 0.8.4]
              -> recall vs exact-filtered GT, rows_returned(<k flag) [M3c],
              EXPLAIN ANALYZE captured separately from timed runs.
  claims    : recall/planner-path comparisons only; NO faiss-vs-pg latency ratio
              (instrumentation boundary differs: client-server round-trip) [M3e].

Run (background ~30-60 min):
  Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/04_scripts/run_pgvector_ann_benchmark.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIN = PROJECT_ROOT / "Datasets" / "processed" / "sinnaedoro_traffic" / "corpus_real"
OUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260710_pillarB"
DSN = "host=localhost port=5433 dbname=vlmdb user=vlmdb password=vlmdb"
K = 10
TIMING_N, REPEATS, WARM = 300, 5, 2
RNG = np.random.default_rng(20260710)

FILTERED_PREDICATES = [  # from LOCKED P1 corpus-A table
    ("location = 'BC2000801'", 0.086),
    ("location = '중동사거리'", 0.049),
    ("hour = 6", 0.183),
    ("hour BETWEEN 6 AND 18", 0.774),
]


def vec_literal(v):
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def pct(meds):
    return float(np.percentile(meds, 50)), float(np.percentile(meds, 95))


def main() -> int:
    import argparse
    import psycopg
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit-rows", type=int, default=None, help="smoke: load only first N rows")
    ap.add_argument("--n-queries", type=int, default=None, help="smoke: use only first N queries")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    X = np.load(SIN / "frame_embeddings.npy").astype("float32")
    X /= (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
    fi = pd.read_parquet(SIN / "frame_index.parquet")
    hour = pd.to_numeric(fi["time"].astype(str).str[:2], errors="coerce").fillna(-1).astype(int)
    Q = np.load(SIN / "queries.npy").astype("float32")
    Q /= (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9)
    if args.limit_rows:
        X, fi, hour = X[:args.limit_rows], fi.iloc[:args.limit_rows], hour.iloc[:args.limit_rows]
    if args.n_queries:
        Q = Q[:args.n_queries]
    Qt = Q[:min(TIMING_N, len(Q))]
    N, d = X.shape
    print(f"[data] {N}x{d}, queries={len(Q)} (timing {len(Qt)})", flush=True)

    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    cur.execute("SET jit = off;")
    cur.execute("SET maintenance_work_mem = '2GB';")
    cur.execute("SET work_mem = '256MB';")
    # docker /dev/shm is 64MB; parallel index build allocates DSM ~= maintenance_work_mem
    # -> DiskFull. Non-parallel build uses backend-local memory instead.
    cur.execute("SET max_parallel_maintenance_workers = 0;")

    # ---------- schema + load (denormalized single-row) [M3a] ----------
    cur.execute("DROP TABLE IF EXISTS b3_frames;")
    cur.execute(f"""CREATE TABLE b3_frames (
        id int PRIMARY KEY, location text, date text, hour int,
        embedding vector({d}));""")
    t0 = time.time()
    with cur.copy("COPY b3_frames (id, location, date, hour, embedding) FROM STDIN") as cp:
        for i in range(N):
            cp.write_row((i, fi.location.iat[i], str(fi.date.iat[i]),
                          int(hour.iat[i]), vec_literal(X[i])))
        # progress marker inside copy not possible; fine
    load_s = time.time() - t0
    cur.execute("ANALYZE b3_frames;")
    print(f"[load] {N} rows in {load_s:.0f}s", flush=True)

    def topk(qv, where="", k=K):
        cur.execute(
            f"SELECT id FROM b3_frames {('WHERE ' + where) if where else ''} "
            f"ORDER BY embedding <#> %s::vector LIMIT {k}", (vec_literal(qv),))
        return [r[0] for r in cur.fetchall()]

    def timed_ids(qv, where=""):
        sql = (f"SELECT id FROM b3_frames {('WHERE ' + where) if where else ''} "
               f"ORDER BY embedding <#> %s::vector LIMIT {K}")
        lit = vec_literal(qv)
        for _ in range(WARM):
            cur.execute(sql, (lit,)); cur.fetchall()
        t = np.empty(REPEATS)
        for r in range(REPEATS):
            t0 = time.perf_counter()
            cur.execute(sql, (lit,)); rows = cur.fetchall()
            t[r] = (time.perf_counter() - t0) * 1e3
        return np.median(t), len(rows)

    def set_gucs(kind, **kw):
        if kind == "hnsw":
            cur.execute(f"SET hnsw.ef_search = {kw['ef']};")
            cur.execute(f"SET hnsw.iterative_scan = {kw.get('iter', 'off')};")
        elif kind == "ivfflat":
            cur.execute(f"SET ivfflat.probes = {kw['probes']};")
            cur.execute(f"SET ivfflat.iterative_scan = {kw.get('iter', 'off')};")
        else:  # exact
            cur.execute("SET enable_indexscan = on;")

    def force_exact(on: bool):
        cur.execute(f"SET enable_indexscan = {'off' if on else 'on'};")
        cur.execute(f"SET enable_bitmapscan = {'off' if on else 'on'};")

    rows_out, filt_out = [], []

    # ---------- exact GT (unfiltered + filtered), seq scan ----------
    force_exact(True)
    gt = [topk(q) for q in Q]
    meds = np.array([timed_ids(q)[0] for q in Qt])
    p50, p95 = pct(meds)
    rows_out.append({"index": "exact_seqscan", "params": "", "recall_at_10": 1.0,
                     "p50_ms": round(p50, 3), "p95_ms": round(p95, 3),
                     "build_s": 0.0, "index_mb": 0.0})
    print(f"[exact] p50={p50:.1f}ms", flush=True)
    gt_filtered = {w: [topk(q, w) for q in Q] for w, _ in FILTERED_PREDICATES}
    force_exact(False)

    def recall_against(gt_list, got_list):
        return float(np.mean([len(set(a) & set(g)) / K for a, g in zip(got_list, gt_list)]))

    def bench_unfiltered(index_name, kind, sweep):
        for kw in sweep:
            set_gucs(kind, **kw)
            got = [topk(q) for q in Q]
            rec = recall_against(gt, got)
            meds = np.array([timed_ids(q)[0] for q in Qt])
            p50, p95 = pct(meds)
            cur.execute("SELECT pg_relation_size(%s)/1048576.0", (index_name,))
            mb = cur.fetchone()[0]
            rows_out.append({"index": index_name, "params": json.dumps(kw),
                             "recall_at_10": round(rec, 4), "p50_ms": round(p50, 3),
                             "p95_ms": round(p95, 3), "build_s": round(build_s, 1),
                             "index_mb": round(float(mb), 1)})
            print(f"  {index_name} {kw}: recall={rec:.4f} p50={p50:.2f}ms", flush=True)

    def bench_filtered(index_name, kind, base_kw, iters=("off", "relaxed_order")):
        for w, s in FILTERED_PREDICATES:
            for it in iters:
                set_gucs(kind, **{**base_kw, "iter": it})
                got, nret = [], []
                for q in Q:
                    ids = topk(q, w)
                    got.append(ids); nret.append(len(ids))
                rec = recall_against(gt_filtered[w], got)
                tmeds = np.array([timed_ids(q, w)[0] for q in Qt])
                p50, p95 = pct(tmeds)
                cur.execute("EXPLAIN (ANALYZE, BUFFERS) SELECT id FROM b3_frames WHERE "
                            + w + f" ORDER BY embedding <#> %s::vector LIMIT {K}",
                            (vec_literal(Q[0]),))
                plan = "\n".join(r[0] for r in cur.fetchall())
                filt_out.append({"index": index_name, "predicate": w, "selectivity": s,
                                 "iterative_scan": it, "recall_at_10": round(rec, 4),
                                 "p50_ms": round(p50, 3), "p95_ms": round(p95, 3),
                                 "mean_rows_returned": round(float(np.mean(nret)), 2),
                                 "frac_short": round(float(np.mean(np.array(nret) < K)), 4),
                                 "plan_node": ("IndexScan" if "Index Scan" in plan else
                                               "SeqScan" if "Seq Scan" in plan else "other")})
                print(f"  [filtered] {index_name} {w} iter={it}: recall={rec:.3f} "
                      f"short={np.mean(np.array(nret)<K):.2%}", flush=True)

    # ---------- HNSW ----------
    for m in (16, 32):
        name = f"b3_hnsw_m{m}"
        cur.execute(f"DROP INDEX IF EXISTS {name};")
        t0 = time.time()
        cur.execute(f"CREATE INDEX {name} ON b3_frames USING hnsw (embedding vector_ip_ops) "
                    f"WITH (m = {m}, ef_construction = 200);")
        build_s = time.time() - t0
        print(f"[build] {name} in {build_s:.0f}s", flush=True)
        bench_unfiltered(name, "hnsw", [{"ef": e} for e in (16, 64, 256)])
        if m == 16:
            bench_filtered(name, "hnsw", {"ef": 64})
        cur.execute(f"DROP INDEX {name};")

    # ---------- IVFFlat ----------
    for lists in (364, 1024):
        name = f"b3_ivf_l{lists}"
        cur.execute(f"DROP INDEX IF EXISTS {name};")
        t0 = time.time()
        cur.execute(f"CREATE INDEX {name} ON b3_frames USING ivfflat (embedding vector_ip_ops) "
                    f"WITH (lists = {lists});")
        build_s = time.time() - t0
        print(f"[build] {name} in {build_s:.0f}s", flush=True)
        bench_unfiltered(name, "ivfflat", [{"probes": p} for p in (1, 8, 32)])
        if lists == 1024:
            bench_filtered(name, "ivfflat", {"probes": 8})
        cur.execute(f"DROP INDEX {name};")

    pd.DataFrame(rows_out).to_csv(OUT / "pgvector_ann_sweep.csv", index=False)
    pd.DataFrame(filt_out).to_csv(OUT / "pgvector_filtered.csv", index=False)
    (OUT / "pgvector_manifest.json").write_text(json.dumps({
        "server": "PostgreSQL 16.14, pgvector 0.8.4 (docker kiise-vlmdb-pgvector :5433)",
        "corpus": "sinnaedoro corpus_real 132521x512 L2-normalized",
        "operator": "<#> (negative inner product; == cosine on normalized vectors, faiss-IP equivalent)",
        "schema": "single-row denormalized (id, location, date, hour, embedding) [M3a]",
        "timing": f"single warm connection, jit=off, W={WARM} R={REPEATS}, per-query median -> p50/p95 over {TIMING_N} queries",
        "boundary": "client-side round-trip; NO cross-system latency ratios vs faiss [M3e]",
        "recall_gt": "seq-scan exact (enable_indexscan=off), same operator",
        "load_s": round(load_s, 1)}, indent=2, ensure_ascii=False))
    print(f"[saved] {OUT}/pgvector_ann_sweep.csv, pgvector_filtered.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
