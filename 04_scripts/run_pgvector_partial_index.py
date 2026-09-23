#!/usr/bin/env python3
"""P2 (DB contribution) — pgvector PARTIAL/LOCAL index vs GLOBAL index + WHERE.

Reuses the persisted b3_frames table (sinnaedoro corpus_real 132,521 x 512,
denormalized location/hour), pgvector 0.8.4 on :5433.

Two ways to serve a filtered ANN query `WHERE p ORDER BY embedding <#> q LIMIT k`:
  GLOBAL + WHERE : one global HNSW index; the filter is applied during/after the
                   graph scan (iterative_scan off vs relaxed_order). Build cost is
                   amortized across all predicates, but recall/latency degrade as
                   the filter gets selective (postfilter over-fetch) [cf. 620].
  PARTIAL/LOCAL  : `CREATE INDEX ... USING hnsw (...) WHERE p` — a local graph over
                   ONLY the predicate subset. Clean ANN within the subset (recall
                   ~1.0, low constant latency), but a per-predicate build + storage.

Per predicate (selectivity sweep) we report, for each strategy: recall@10 vs
exact-filtered GT, client p50/p95, build_s, index_mb. These feed the P3 hot/cold
break-even (when a partial index's build pays for itself).

Honesty (620 rules): recall/latency are pg-internal, client round-trip; NO
faiss-vs-pg absolute ratios.

Run (background ~10-20 min): Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/04_scripts/run_pgvector_partial_index.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SIN = PROJECT_ROOT / "Datasets" / "processed" / "sinnaedoro_traffic" / "corpus_real"
OUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260713_db_design"
DSN = "host=localhost port=5433 dbname=vlmdb user=vlmdb password=vlmdb"
TABLE = "b3_frames"
K = 10
TIMING_N, REPEATS, WARM = 200, 5, 2

# candidate predicates spanning selectivity (computed live; kept if 0.01<=sel<=0.85)
CANDIDATES = [
    "hour BETWEEN 7 AND 7", "hour = 6", "hour BETWEEN 6 AND 9",
    "hour BETWEEN 6 AND 12", "hour BETWEEN 6 AND 18", "hour BETWEEN 6 AND 21",
]


def vec_literal(v):
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def main() -> int:
    import argparse
    import psycopg
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", default=TABLE)
    ap.add_argument("--query-npy", default=str(SIN / "queries.npy"))
    ap.add_argument("--out-name", default="pgvector_partial_vs_global.csv")
    ap.add_argument("--manifest-name", default="pgvector_partial_manifest.json")
    ap.add_argument("--corpus-label", default="sinnaedoro corpus_real 132521x512")
    ap.add_argument("--predicates-sql", default="", help="';'-separated WHERE clauses to use instead of the default hour+location candidates")
    args = ap.parse_args()
    table = args.table
    OUT.mkdir(parents=True, exist_ok=True)
    Q = np.load(args.query_npy).astype("float32")
    Q /= (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9)
    Qt = Q[:TIMING_N]
    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    cur.execute("SET jit = off;")
    cur.execute("SET maintenance_work_mem = '2GB';")
    cur.execute("SET max_parallel_maintenance_workers = 0;")
    cur.execute(f"SELECT count(*) FROM {table}")
    N = cur.fetchone()[0]

    # pick predicates + measured selectivity
    preds = []
    if args.predicates_sql:
        for w in [c.strip() for c in args.predicates_sql.split(";") if c.strip()]:
            cur.execute(f"SELECT count(*) FROM {table} WHERE {w}")
            s = cur.fetchone()[0] / N
            if 0.003 <= s <= 0.9:
                preds.append((w, round(s, 4)))
    else:
        for w in CANDIDATES:
            cur.execute(f"SELECT count(*) FROM {table} WHERE {w}")
            s = cur.fetchone()[0] / N
            if 0.01 <= s <= 0.85:
                preds.append((w, round(s, 4)))
        # add a selective single location
        cur.execute(f"SELECT location, count(*) c FROM {table} GROUP BY location ORDER BY c LIMIT 20")
        for loc, c in cur.fetchall():
            s = c / N
            if 0.01 <= s <= 0.06:
                preds.append((f"location = '{loc}'", round(s, 4))); break
    preds = sorted(set(preds), key=lambda x: x[1])
    print(f"[data] N={N} queries={len(Q)}  predicates(sel): {[(p,s) for p,s in preds]}", flush=True)

    def topk(qv, where=""):
        cur.execute(f"SELECT id FROM {table} {('WHERE ' + where) if where else ''} "
                    f"ORDER BY embedding <#> %s::vector LIMIT {K}", (vec_literal(qv),))
        return [r[0] for r in cur.fetchall()]

    def timed(qv, where=""):
        sql = (f"SELECT id FROM {table} {('WHERE ' + where) if where else ''} "
               f"ORDER BY embedding <#> %s::vector LIMIT {K}")
        lit = vec_literal(qv)
        for _ in range(WARM):
            cur.execute(sql, (lit,)); cur.fetchall()
        t = np.empty(REPEATS)
        for r in range(REPEATS):
            t0 = time.perf_counter(); cur.execute(sql, (lit,)); rows = cur.fetchall()
            t[r] = (time.perf_counter() - t0) * 1e3
        return float(np.median(t)), len(rows)

    def recall(gt, got):
        return float(np.mean([len(set(a) & set(g)) / K for a, g in zip(got, gt)]))

    def set_hnsw(ef, it):
        cur.execute(f"SET hnsw.ef_search = {ef};")
        cur.execute(f"SET hnsw.iterative_scan = {it};")

    # exact filtered GT (seq scan)
    cur.execute("SET enable_indexscan = off;"); cur.execute("SET enable_bitmapscan = off;")
    gt = {w: [topk(q, w) for q in Q] for w, _ in preds}
    cur.execute("SET enable_indexscan = on;"); cur.execute("SET enable_bitmapscan = on;")

    rows = []

    # ---- GLOBAL HNSW (build once, amortized) ----
    cur.execute(f"DROP INDEX IF EXISTS p2_global;")
    t0 = time.time()
    cur.execute(f"CREATE INDEX p2_global ON {table} USING hnsw (embedding vector_ip_ops)"
                f"WITH (m = 16, ef_construction = 200);")
    global_build = time.time() - t0
    cur.execute("SELECT pg_relation_size('p2_global')/1048576.0"); global_mb = float(cur.fetchone()[0])
    print(f"[global] build {global_build:.0f}s size {global_mb:.1f}MB", flush=True)
    for w, s in preds:
        for it in ("off", "relaxed_order"):
            set_hnsw(64, it)
            got = [topk(q, w) for q in Q]
            rec = recall(gt[w], got)
            meds = np.array([timed(q, w) for q in Qt])
            p50, p95 = float(np.percentile(meds[:, 0], 50)), float(np.percentile(meds[:, 0], 95))
            short = float(np.mean(meds[:, 1] < K))
            rows.append({"predicate": w, "selectivity": s, "strategy": f"global_where_{it}",
                         "recall_at_10": round(rec, 4), "p50_ms": round(p50, 3), "p95_ms": round(p95, 3),
                         "build_s": round(global_build, 1), "index_mb": round(global_mb, 1),
                         "build_amortized": True, "frac_short": round(short, 3)})
            print(f"  global/{it} {w} (s={s}): recall={rec:.3f} p50={p50:.2f}ms short={short:.0%}", flush=True)
    cur.execute("DROP INDEX p2_global;")

    # ---- PARTIAL/LOCAL index per predicate ----
    set_hnsw(64, "off")
    for i, (w, s) in enumerate(preds):
        name = f"p2_partial_{i}"
        cur.execute(f"DROP INDEX IF EXISTS {name};")
        t0 = time.time()
        cur.execute(f"CREATE INDEX {name} ON {table} USING hnsw (embedding vector_ip_ops)"
                    f"WITH (m = 16, ef_construction = 200) WHERE {w};")
        pbuild = time.time() - t0
        cur.execute(f"SELECT pg_relation_size('{name}')/1048576.0"); pmb = float(cur.fetchone()[0])
        got = [topk(q, w) for q in Q]
        rec = recall(gt[w], got)
        meds = np.array([timed(q, w) for q in Qt])
        p50, p95 = float(np.percentile(meds[:, 0], 50)), float(np.percentile(meds[:, 0], 95))
        short = float(np.mean(meds[:, 1] < K))
        rows.append({"predicate": w, "selectivity": s, "strategy": "partial_local",
                     "recall_at_10": round(rec, 4), "p50_ms": round(p50, 3), "p95_ms": round(p95, 3),
                     "build_s": round(pbuild, 2), "index_mb": round(pmb, 2),
                     "build_amortized": False, "frac_short": round(short, 3)})
        print(f"  partial {w} (s={s}): recall={rec:.3f} p50={p50:.2f}ms build={pbuild:.1f}s size={pmb:.1f}MB", flush=True)
        cur.execute(f"DROP INDEX {name};")

    df = pd.DataFrame(rows)
    df.to_csv(OUT / args.out_name, index=False)
    (OUT / args.manifest_name).write_text(json.dumps({
        "server": "PostgreSQL 16 / pgvector 0.8.4 (:5433)",
        "table": f"{table} ({N} x 512, {args.corpus_label})",
        "global_build_s": round(global_build, 1), "global_mb": round(global_mb, 1),
        "note": "global build cost amortized across all predicates; partial = per-predicate build+size. "
                "recall vs exact seq-scan filtered GT; client round-trip timing; no faiss cross-ratio.",
    }, ensure_ascii=False, indent=2))
    print(f"\n[saved] {OUT}/{args.out_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
