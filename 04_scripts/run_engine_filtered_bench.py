#!/usr/bin/env python3
"""B-4 stage 2 [prereg 420 Amendment 5]: third-engine filtered-ANN benchmark.

Scores Milvus v2.6.0 and Weaviate 1.35.3 native filtered-search paths against
the frozen stage-1 GT (export_engine_bench_inputs.py). Every mask (real
predicate AND its same-size random control) is materialized as a BOOLEAN
field/property so the filter-evaluation path is symmetric between real and
control — only the geometry of the allowed set differs, which is the
mechanism under test.

Index params mirror the faiss B-1 runs: HNSW M(maxConnections)=32,
efConstruction=200, search ef=64, metric=IP (vectors L2-normalized upstream).
Conditions:
  milvus     m1: expr bitset prefilter + HNSW (server default path)
  weaviate   w1: server-default flatSearchCutoff (flat fallback = the engine's
                 own mitigation; reported separately)
             w2: flatSearchCutoff=0 (pure filtered-HNSW path)
Recall pass may use a small thread pool (recall is timing-free); the optional
latency pass is single-threaded client-RT, within-engine descriptive only —
NO cross-engine latency comparison (§5.3 discipline).

Run (kiise-engines venv):
  run_engine_filtered_bench.py --engine weaviate --corpus A [--smoke]
  run_engine_filtered_bench.py --engine milvus   --corpus A [--smoke]
"""
from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DS = PROJECT_ROOT / "Datasets" / "processed"
OUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260712_engine_replication"
K = 10
EMB = {"A": DS / "sinnaedoro_traffic/corpus_real/frame_embeddings.npy",
       "B": DS / "aihub_522_intersection/20260710/visual_embeddings_clip/frame_embeddings.npy"}


def load_inputs(corpus):
    z = np.load(OUT / f"inputs_{corpus}.npz")
    meta = pd.read_csv(OUT / f"inputs_{corpus}_meta.csv")
    N = int(z["n"])
    masks = [np.unpackbits(mp)[:N].astype(bool) for mp in z["masks_packed"]]
    X = np.load(EMB[corpus]).astype("float32")
    X /= (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)  # A needs it; B is a no-op
    return X, z["queries"].astype("float32"), z["self_ids"], masks, z["gt"], meta, N


def recall_ci(per_q, boot=5000, seed=20260712):
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(per_q), size=(boot, len(per_q)))
    m = per_q[idx].mean(axis=1)
    return (float(per_q.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))


def score(gt, got):
    return np.array([len(set(a[:K]) & set(g[:K])) / K for a, g in zip(got, gt)])


# ---------------- engines ----------------
class Milvus:
    name = "milvus"

    def __init__(self, corpus, n_fields):
        from pymilvus import MilvusClient, DataType
        self.c = MilvusClient(uri="http://localhost:19530")
        self.coll = f"kiise_{corpus.lower()}_b4"
        self.DataType = DataType

    def ingest(self, X, masks, meta):
        from pymilvus import DataType
        if self.c.has_collection(self.coll):
            self.c.drop_collection(self.coll)
        schema = self.c.create_schema(auto_id=False, enable_dynamic_field=False)
        schema.add_field("id", DataType.INT64, is_primary=True)
        schema.add_field("vec", DataType.FLOAT_VECTOR, dim=X.shape[1])
        for i in range(len(masks)):
            schema.add_field(f"p{i}", DataType.BOOL)
        self.c.create_collection(self.coll, schema=schema, consistency_level="Strong")
        mstack = np.stack(masks)  # (n_masks, N)
        B = 2000
        for lo in range(0, len(X), B):
            hi = min(lo + B, len(X))
            rows = []
            for r in range(lo, hi):
                row = {"id": r, "vec": X[r].tolist()}
                for i in range(len(masks)):
                    row[f"p{i}"] = bool(mstack[i, r])
                rows.append(row)
            self.c.insert(self.coll, rows)
        self.c.flush(self.coll)
        idx = self.c.prepare_index_params()
        idx.add_index("vec", index_type="HNSW", metric_type="IP",
                      params={"M": 32, "efConstruction": 200})
        self.c.create_index(self.coll, idx)
        self.c.load_collection(self.coll)
        st = self.c.get_collection_stats(self.coll)
        return int(st["row_count"])

    def search_mask(self, Q, mask_id, k, threads=8):
        flt = f"p{mask_id} == true"
        sp = {"params": {"ef": 64}}
        res = self.c.search(self.coll, data=Q.tolist(), filter=flt, limit=k,
                            search_params=sp, output_fields=[])
        return [[h["id"] for h in hits] for hits in res]

    def search_unfiltered(self, Q, k):
        res = self.c.search(self.coll, data=Q.tolist(), limit=k,
                            search_params={"params": {"ef": 64}})
        return [[h["id"] for h in hits] for hits in res]

    def timed_single(self, q, mask_id, k):
        t0 = time.perf_counter()
        self.c.search(self.coll, data=[q.tolist()], filter=f"p{mask_id} == true",
                      limit=k, search_params={"params": {"ef": 64}})
        return (time.perf_counter() - t0) * 1e3

    def set_condition(self, cond):
        assert cond == "m1"
        self.strategy = "bitset-prefilter (knowhere BF fallback at filtered-out>~0.93)"

    def filtered_count(self, mask_id):
        r = self.c.query(self.coll, filter=f"p{mask_id} == true",
                         output_fields=["count(*)"])
        return int(r[0]["count(*)"])

    def version(self):
        from pymilvus import MilvusClient
        return "server 2.6.0 / pymilvus 3.0.0"


class Weaviate:
    name = "weaviate"

    def __init__(self, corpus, n_fields):
        import weaviate
        self.cl = weaviate.connect_to_local()
        self.coll = f"Kiise_{corpus.lower()}_b4"
        self.n_fields = n_fields

    def ingest(self, X, masks, meta):
        import weaviate.classes.config as wc
        if self.cl.collections.exists(self.coll):
            self.cl.collections.delete(self.coll)
        props = [wc.Property(name=f"p{i}", data_type=wc.DataType.BOOL,
                             index_filterable=True)
                 for i in range(len(masks))]
        self.cl.collections.create(
            self.coll, properties=props,
            vector_config=wc.Configure.Vectors.self_provided(
                vector_index_config=wc.Configure.VectorIndex.hnsw(
                    distance_metric=wc.VectorDistances.DOT,
                    max_connections=32, ef_construction=200, ef=64)),
        )
        col = self.cl.collections.get(self.coll)
        mstack = np.stack(masks)
        with col.batch.fixed_size(batch_size=1000, concurrent_requests=4) as b:
            for r in range(len(X)):
                b.add_object(properties={f"p{i}": bool(mstack[i, r]) for i in range(len(masks))},
                             vector=X[r].tolist(), uuid=self._uuid(r))
        errs = col.batch.failed_objects
        if errs:
            raise RuntimeError(f"weaviate batch errors: {len(errs)}; first={errs[0]}")
        # wait for async indexing to drain
        while True:
            agg = col.aggregate.over_all(total_count=True)
            n = agg.total_count
            time.sleep(2)
            try:
                st = self.cl.cluster.nodes(collection=self.coll, output="verbose")
                statuses = [sh.vector_indexing_status for nd in st for sh in nd.shards]
                if all(s == "READY" for s in statuses):
                    break
            except Exception:
                break
        return n

    def _uuid(self, r):
        return f"00000000-0000-0000-0000-{r:012d}"

    # Amendment 5a(2): w1 = acorn+40000 (server default; descriptive mitigation),
    # w2 = sweeping+0 (pure allowlist-HNSW; CONFIRMATORY), w3 = acorn+0 (ACORN lane)
    CONDS = {"w1": ("acorn", 40000), "w2": ("sweeping", 0), "w3": ("acorn", 0)}

    def set_condition(self, cond):
        import weaviate.classes.config as wc
        strat, cutoff = self.CONDS[cond]
        strat_enum = (wc.VectorFilterStrategy.SWEEPING if strat == "sweeping"
                      else wc.VectorFilterStrategy.ACORN)
        col = self.cl.collections.get(self.coll)
        col.config.update(vector_config=wc.Reconfigure.Vectors.update(
            name="default",
            vector_index_config=wc.Reconfigure.VectorIndex.hnsw(
                flat_search_cutoff=cutoff, filter_strategy=strat_enum)))
        vi = col.config.get().vector_config["default"].vector_index_config
        self.cutoff = vi.flat_search_cutoff
        self.strategy = str(vi.filter_strategy)
        assert self.cutoff == cutoff and strat in self.strategy.lower(), \
            f"condition not applied: cutoff={self.cutoff} strategy={self.strategy}"

    def filtered_count(self, mask_id):
        from weaviate.classes.query import Filter
        col = self.cl.collections.get(self.coll)
        return col.aggregate.over_all(
            filters=Filter.by_property(f"p{mask_id}").equal(True),
            total_count=True).total_count

    def search_mask(self, Q, mask_id, k, threads=8):
        from weaviate.classes.query import Filter
        col = self.cl.collections.get(self.coll)
        flt = Filter.by_property(f"p{mask_id}").equal(True)

        def one(q):
            r = col.query.near_vector(near_vector=q.tolist(), limit=k, filters=flt)
            return [int(str(o.uuid)[-12:]) for o in r.objects]
        with ThreadPoolExecutor(threads) as ex:
            return list(ex.map(one, Q))

    def search_unfiltered(self, Q, k):
        col = self.cl.collections.get(self.coll)

        def one(q):
            r = col.query.near_vector(near_vector=q.tolist(), limit=k)
            return [int(str(o.uuid)[-12:]) for o in r.objects]
        with ThreadPoolExecutor(8) as ex:
            return list(ex.map(one, Q))

    def timed_single(self, q, mask_id, k):
        from weaviate.classes.query import Filter
        col = self.cl.collections.get(self.coll)
        flt = Filter.by_property(f"p{mask_id}").equal(True)
        t0 = time.perf_counter()
        col.query.near_vector(near_vector=q.tolist(), limit=k, filters=flt)
        return (time.perf_counter() - t0) * 1e3

    def version(self):
        import weaviate
        return f"server 1.35.3 / weaviate-client {weaviate.__version__}"

    def close(self):
        self.cl.close()


# ---------------- driver ----------------
def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["milvus", "weaviate"], required=True)
    ap.add_argument("--corpus", choices=["A", "B"], required=True)
    ap.add_argument("--smoke", action="store_true", help="2 predicate pairs only")
    ap.add_argument("--skip-ingest", action="store_true")
    ap.add_argument("--conditions", default=None,
                    help="comma list; default m1 / w1,w2,w3 [Amd.5a]")
    ap.add_argument("--out-suffix", default="", help="appended to output csv name")
    ap.add_argument("--timing-queries", type=int, default=100)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--warmup", type=int, default=2)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    X, Q, self_ids, masks, gt, meta, N = load_inputs(args.corpus)
    eng = (Milvus if args.engine == "milvus" else Weaviate)(args.corpus, len(masks))
    print(f"[{args.engine}/{args.corpus}] N={N} masks={len(masks)} queries={len(Q)} "
          f"ver={eng.version()}", flush=True)

    if not args.skip_ingest:
        t0 = time.perf_counter()
        n = eng.ingest(X, masks, meta)
        print(f"[ingest] rows={n} in {time.perf_counter()-t0:.0f}s", flush=True)
        assert n == N, f"G-ingest FAIL: {n} != {N}"

    # G-ingest recall gate: unfiltered recall@10 vs local exact
    sub = Q[:200]
    sims = sub @ X.T
    part = np.argpartition(-sims, K + 1, axis=1)[:, :K + 1]
    exact_unf = []
    for qi in range(len(sub)):
        cand = part[qi][np.argsort(-sims[qi, part[qi]])]
        exact_unf.append([i for i in cand if i != self_ids[qi]][:K])
    got_unf = eng.search_unfiltered(sub, K + 1)
    got_unf = [[i for i in row if i != self_ids[qi]][:K] for qi, row in enumerate(got_unf)]
    gate = float(np.mean([len(set(a) & set(g)) / K for a, g in zip(got_unf, exact_unf)]))
    print(f"[gate] unfiltered recall@10 = {gate:.4f}", flush=True)
    if gate < 0.95:
        print("G-INGEST GATE FAIL (<0.95) — stopping per prereg"); return 2

    conds = (args.conditions.split(",") if args.conditions
             else (["m1"] if args.engine == "milvus" else ["w1", "w2", "w3"]))
    sel = meta if not args.smoke else meta[meta.pair.isin(meta.pair.unique()[:2])]

    # G-filter gate [Amd.5a(5)]: engine-side filtered count == local mask size
    bad = []
    for _, r in sel.iterrows():
        n_eng = eng.filtered_count(int(r.mask_id))
        if n_eng != int(r.subset):
            bad.append((r.predicate, n_eng, int(r.subset)))
    if bad:
        print(f"G-FILTER GATE FAIL ({len(bad)} masks): {bad[:3]} — stopping per Amd.5a")
        return 3
    print(f"[gate] G-filter: engine counts match local masks for {len(sel)} masks", flush=True)
    rows = []
    for cond in conds:
        eng.set_condition(cond)
        cutoff = getattr(eng, "cutoff", None)
        for _, r in sel.iterrows():
            mid = int(r.mask_id)
            t0 = time.perf_counter()
            got = eng.search_mask(Q, mid, K + 1)
            got = [[i for i in row if i != self_ids[qi]][:K] for qi, row in enumerate(got)]
            per_q = score(gt[mid], got)
            rec, lo, hi = recall_ci(per_q)
            # descriptive within-engine latency (single-thread client RT)
            meds = []
            for q in Q[:args.timing_queries]:
                for _ in range(args.warmup):
                    eng.timed_single(q, mid, K)
                meds.append(np.median([eng.timed_single(q, mid, K)
                                       for _ in range(args.repeats)]))
            row = {"engine": args.engine, "condition": cond,
                   "predicate": r.predicate, "kind": r.kind, "pair": r.pair,
                   "selectivity": r.selectivity, "subset": r.subset,
                   "gt_cluster_med_rank": r.gt_cluster_med_rank,
                   "recall_at_10": round(rec, 4), "r_lo": round(lo, 4),
                   "r_hi": round(hi, 4),
                   "p50_ms_clientRT": round(float(np.percentile(meds, 50)), 3),
                   "flat_cutoff": cutoff,
                   "flat_path": (cutoff is not None and cutoff > 0 and r.subset < cutoff),
                   "filter_strategy": getattr(eng, "strategy", None)}
            rows.append(row)
            pd.DataFrame(rows).to_csv(
                OUT / f"engine_{args.engine}_{args.corpus}{args.out_suffix}.csv", index=False)
            print(f"  [{cond}] {r.predicate[:44]:<46} rec={rec:.4f} "
                  f"({time.perf_counter()-t0:.0f}s)", flush=True)

    manifest = {"engine": args.engine, "corpus": args.corpus, "N": N, "k": K,
                "version": eng.version(), "queries": int(len(Q)),
                "index": {"type": "HNSW", "M": 32, "efConstruction": 200, "ef": 64,
                          "metric": "IP (L2-normalized vectors)"},
                "conditions": conds, "gate_unfiltered_recall": gate,
                "controls": f"same-size random masks, default_rng({20260712}+idx) [Amd.5]",
                "latency": "single-thread client RT p50, within-engine descriptive ONLY",
                "timing_queries": args.timing_queries, "repeats": args.repeats}
    (OUT / f"engine_{args.engine}_{args.corpus}{args.out_suffix}_manifest.json").write_text(
        json.dumps(manifest, indent=2))
    print(f"[saved] engine_{args.engine}_{args.corpus}.csv ({len(rows)} rows)")
    if hasattr(eng, "close"):
        eng.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
