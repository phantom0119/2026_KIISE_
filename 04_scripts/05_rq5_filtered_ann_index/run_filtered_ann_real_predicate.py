#!/usr/bin/env python3
"""Pillar B-1 [prereg 420 §1 + Amendments]: filtered-ANN on REAL predicates,
two real corpora, with paired same-s random-mask controls.

Implements the amended measurement discipline:
  M1  timing boundary = query arrival -> K results, INCLUDING postfilter mask
      filtering/truncation (vectorized); one-time prep (subset extraction,
      subset-index build, selector build) reported separately as build_s /
      selector_build_ms; efSearch unified (=64) across HNSW uses; faiss forces
      ef>=K' on postfilter (footnoted via kprime column); K' capped at N with
      degenerate label when K' >= 0.9N.
  M2  latency stats: warmup W kept but excluded; per-query median of R repeats
      -> query-distribution p50/p95 (+p99 when timed-n>=500); CI = query-level
      bootstrap (5,000); method order randomized per predicate block;
      single-thread timing, multi-thread recall/builds.
  M4  single_stage fairness: selector_build_ms separate; IDSelectorBitmap
      variant at s>=0.25; nprobe escalation to 128 when recall<0.9 at 32.
  M9  every real predicate gets a paired random-mask control at identical
      subset size; GT-clustering covariate = median global exact rank of the
      subset GT items (from full-corpus exact top-1000).
  M5  corpus B: full 143,830 frames indexed; unjoined frames facet-NULL (never
      pass); GT within joined-and-passing subset; frame-weighted selectivity.
  M6  corpus B queries: image layer (200 held-out frames, self-excluded)
      = confirmatory; text layer (32 CLIP-text) = descriptive only.
  B1  predicates = the LOCKED P1 tables (re-derived masks are asserted against
      the registered counts).

Run (background; hours-scale):
  ... run_filtered_ann_real_predicate.py --corpus A
  ... run_filtered_ann_real_predicate.py --corpus B
Smoke:
  ... --corpus A --limit-predicates 2 --timing-queries 50 --repeats 3
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DS = PROJECT_ROOT / "Datasets"
SIN = DS / "processed" / "sinnaedoro_traffic" / "corpus_real"
V522 = DS / "processed" / "aihub_522_intersection" / "20260710"
OUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260710_pillarB"
K = 10
RNG = np.random.default_rng(20260710)


# ---------------- predicate masks (must match P1 registration) ----------------
def masks_corpus_a(fi: pd.DataFrame):
    hour = fi["time"].astype(str).str[:2]
    hnum = pd.to_numeric(hour, errors="coerce")
    out = []
    for v in fi["location"].value_counts().head(6).index:
        out.append((f"location=={v}", "natural", fi["location"].eq(v)))
    for v in fi["date"].value_counts().head(4).index:
        out.append((f"date=={v}", "natural", fi["date"].eq(v)))
    for v in sorted(hour.value_counts().index):
        if hour.eq(v).sum() >= 1000:
            out.append((f"hour=={v}", "natural", hour.eq(v)))
    out += [("hour in [06,18] (daytime)", "composite", hnum.between(6, 18)),
            ("hour in [11,14] (midday)", "composite", hnum.between(11, 14)),
            ("hour in [17,19] (evening peak)", "composite", hnum.between(17, 19)),
            ("location in top-5", "composite",
             fi["location"].isin(fi["location"].value_counts().head(5).index)),
            ("date in 2020-09", "composite", fi["date"].astype(str).str.startswith("202009"))]
    return [(n, k, m.fillna(False).to_numpy()) for n, k, m in out]


def masks_corpus_b(f: pd.DataFrame):
    hs = pd.to_numeric(f["hour"], errors="coerce")
    out = []
    for v in ["morning", "afternoon", "evening"]:
        out.append((f"time_of_day=={v}", "natural", f["time_of_day"].eq(v)))
    for v in [True, False]:
        out.append((f"sig_has_yellow=={v}", "natural", f["sig_has_yellow"].eq(v)))
        out.append((f"sig_has_pedestrian=={v}", "natural", f["sig_has_pedestrian"].eq(v)))
    for v in ["low", "mid", "high"]:
        out.append((f"veh_density_bin=={v}", "natural", f["veh_density_bin"].astype(str).eq(v)))
    for v in sorted(hs.dropna().unique()):
        if hs.eq(v).sum() >= 2000:
            out.append((f"hour=={int(v)}", "natural", hs.eq(v)))
    out += [("hour in [11,14] (midday)", "composite", hs.between(11, 14)),
            ("hour in [8,18] (working)", "composite", hs.between(8, 18)),
            ("time_of_day in {morning,evening}", "composite",
             f["time_of_day"].isin(["morning", "evening"]))]
    return [(n, k, m.fillna(False).to_numpy()) for n, k, m in out]


# ---------------- measurement helpers ----------------
def timed(fn, queries, repeats, warmup):
    """M2: per-query median of R repeats (W warmups excluded) -> array of medians."""
    med = np.empty(len(queries))
    for i, q in enumerate(queries):
        qq = q.reshape(1, -1)
        for _ in range(warmup):
            fn(qq)
        t = np.empty(repeats)
        for r in range(repeats):
            t0 = time.perf_counter(); fn(qq); t[r] = (time.perf_counter() - t0) * 1e3
        med[i] = np.median(t)
    return med


def pct_ci(meds, boot=2000):
    """query-bootstrap CI for p50/p95 of the per-query-median distribution."""
    n = len(meds)
    idx = RNG.integers(0, n, size=(boot, n))
    s = meds[idx]
    p50s, p95s = np.percentile(s, 50, axis=1), np.percentile(s, 95, axis=1)
    r = {"p50_ms": float(np.percentile(meds, 50)),
         "p50_lo": float(np.percentile(p50s, 2.5)), "p50_hi": float(np.percentile(p50s, 97.5)),
         "p95_ms": float(np.percentile(meds, 95)),
         "p95_lo": float(np.percentile(p95s, 2.5)), "p95_hi": float(np.percentile(p95s, 97.5))}
    if n >= 500:
        r["p99_ms"] = float(np.percentile(meds, 99))
    return r


def recall_ci(per_q, boot=5000):
    n = len(per_q)
    idx = RNG.integers(0, n, size=(boot, n))
    m = per_q[idx].mean(axis=1)
    return (float(per_q.mean()), float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5)))


def recall_rows(gt, got, k=K):
    return np.array([len(set(a[:k]) & set(g[:k])) / k for a, g in zip(got, gt)])


# ---------------- per-predicate benchmark ----------------
def bench_block(tag, kind, mask, X, Qr, Qt, full_h, full_ivf, exact_top,
                self_ids, args, faiss):
    """Run all methods for one predicate mask. Qr=recall queries, Qt=timing queries."""
    rows = []
    N, d = X.shape
    sub_ids = np.flatnonzero(mask)
    m = len(sub_ids)
    s = m / N
    if m < K + 1:
        return rows

    # ---- GT: exact top-K within subset (self-excluded via +extra) ----
    t0 = time.perf_counter()
    sub = np.ascontiguousarray(X[sub_ids])
    prep_subset_s = time.perf_counter() - t0
    gsub = faiss.IndexFlatIP(d); gsub.add(sub)
    _, gl = gsub.search(Qr, K + 1)
    gt = []
    for row, sid in zip(sub_ids[gl], self_ids):
        gt.append([i for i in row if i != sid][:K])
    gt = np.array(gt)

    # M9 covariate: median global exact rank of subset GT items
    med_rank = float(np.median([
        np.where(np.isin(exact_top[qi], gt[qi]))[0].mean() if np.isin(exact_top[qi], gt[qi]).any() else 1000.0
        for qi in range(len(Qr))]))

    base = {"predicate": tag, "kind": kind, "selectivity": round(s, 5), "subset": m,
            "gt_cluster_med_rank": round(med_rank, 1)}

    def emit(method, got, meds, extra=None):
        pr = recall_rows(gt, got)
        rec, lo, hi = recall_ci(pr)
        row = {**base, "method": method, "recall_at_10": round(rec, 4),
               "r_lo": round(lo, 4), "r_hi": round(hi, 4), **{k: round(v, 4) for k, v in pct_ci(meds).items()}}
        if extra:
            row.update(extra)
        rows.append(row)
        return rec

    methods = []

    # prefilter_flat
    def m_pff():
        pf = faiss.IndexFlatIP(d); pf.add(sub)
        _, a = pf.search(Qr, K + 1)
        got = _self_excl(sub_ids[a], self_ids)
        faiss.omp_set_num_threads(1)
        meds = timed(lambda q: pf.search(q, K), Qt, args.repeats, args.warmup)
        faiss.omp_set_num_threads(0)
        emit("prefilter_flat", got, meds, {"build_s": round(prep_subset_s, 3)})
    methods.append(m_pff)

    # prefilter_hnsw
    def m_pfh():
        tb = time.perf_counter()
        ph = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT)
        ph.hnsw.efConstruction = 200; ph.add(sub); ph.hnsw.efSearch = 64
        bld = time.perf_counter() - tb
        _, a = ph.search(Qr, K + 1)
        got = _self_excl(sub_ids[a], self_ids)
        faiss.omp_set_num_threads(1)
        meds = timed(lambda q: ph.search(q, K), Qt, args.repeats, args.warmup)
        faiss.omp_set_num_threads(0)
        emit("prefilter_hnsw_ef64", got, meds, {"build_s": round(bld + prep_subset_s, 3)})
    methods.append(m_pfh)

    # postfilter_hnsw with K' sweep [M1: filtering inside timed region]
    for mult in (1, 2, 4):
        def m_post(mult=mult):
            Kp = int(min(N, np.ceil(K / max(s, 1e-9)) * mult))
            degen = Kp >= 0.9 * N
            _, aa = full_h.search(Qr, Kp + 1)
            got = []
            for row, sid in zip(aa, self_ids):
                sel = row[(mask[row]) & (row != sid)][:K]
                got.append(np.pad(sel, (0, K - len(sel)), constant_values=-1))
            got = np.array(got)

            def qfn(q):
                _, r = full_h.search(q, Kp)
                r = r[0]
                _ = r[mask[r]][:K]          # timed: filter + truncate [M1]
            faiss.omp_set_num_threads(1)
            meds = timed(qfn, Qt, args.repeats, args.warmup)
            faiss.omp_set_num_threads(0)
            emit(f"postfilter_hnsw_K{mult}x", got, meds,
                 {"kprime": Kp, "degenerate": degen})
        methods.append(m_post)

    # single_stage IVF + IDSelector [M4]
    def m_ss():
        ts = time.perf_counter()
        sel = faiss.IDSelectorBatch(sub_ids.astype("int64"))
        sel_ms = (time.perf_counter() - ts) * 1e3
        variants = [("batch", sel, 8), ("batch", sel, 32)]
        if s >= 0.25:
            ts = time.perf_counter()
            bm = np.zeros((N + 7) // 8, dtype="uint8")
            for i in sub_ids:
                bm[i >> 3] |= (1 << (i & 7))
            selb = faiss.IDSelectorBitmap(bm)
            selb_ms = (time.perf_counter() - ts) * 1e3
            variants.append(("bitmap", selb, 32))
        done_esc = False
        for name, selector, nprobe in variants:
            sp = faiss.SearchParametersIVF(sel=selector, nprobe=nprobe)
            _, a = full_ivf.search(Qr, K + 1, params=sp)
            got = _self_excl(a, self_ids)
            faiss.omp_set_num_threads(1)
            meds = timed(lambda q: full_ivf.search(q, K, params=sp), Qt, args.repeats, args.warmup)
            faiss.omp_set_num_threads(0)
            rec = emit(f"single_stage_ivf_{name}_np{nprobe}", got, meds,
                       {"selector_build_ms": round(sel_ms if name == "batch" else selb_ms, 2)})
            if name == "batch" and nprobe == 32 and rec < 0.9 and not done_esc:
                done_esc = True
                sp2 = faiss.SearchParametersIVF(sel=selector, nprobe=128)
                _, a2 = full_ivf.search(Qr, K + 1, params=sp2)
                got2 = _self_excl(a2, self_ids)
                faiss.omp_set_num_threads(1)
                meds2 = timed(lambda q: full_ivf.search(q, K, params=sp2), Qt, args.repeats, args.warmup)
                faiss.omp_set_num_threads(0)
                emit("single_stage_ivf_batch_np128", got2, meds2,
                     {"selector_build_ms": round(sel_ms, 2), "escalated": True})
    methods.append(m_ss)

    order = RNG.permutation(len(methods))   # M2: method-order randomization
    for i in order:
        methods[i]()
    return rows


def _self_excl(ids2d, self_ids):
    out = []
    for row, sid in zip(ids2d, self_ids):
        r = [i for i in row if i != sid][:K]
        out.append(np.pad(np.array(r), (0, K - len(r)), constant_values=-1))
    return np.array(out)


# ---------------- corpus setup ----------------
def setup(corpus, args, faiss):
    if corpus == "A":
        X = np.load(SIN / "frame_embeddings.npy").astype("float32")
        X /= (np.linalg.norm(X, axis=1, keepdims=True) + 1e-9)
        fi = pd.read_parquet(SIN / "frame_index.parquet")
        Q = np.load(SIN / "queries.npy").astype("float32")
        Q /= (np.linalg.norm(Q, axis=1, keepdims=True) + 1e-9)
        masks = masks_corpus_a(fi)
        self_ids = np.full(len(Q), -1)      # text queries: no self
        layer = "text_confirmatory"
    else:
        V = V522 / "visual_embeddings_clip"
        X = np.load(V / "frame_embeddings.npy").astype("float32")
        fi = pd.read_parquet(V / "frame_index.parquet")
        join = pd.read_parquet(V522 / "visual_sensor_join.parquet")
        j = join[join.join_ok_120s][["visual_video_id", "split", "time_of_day", "hour",
                                     "sig_has_yellow", "sig_has_pedestrian", "veh_density_bin"]]
        # suffixes must match build_p1_predicate_tables.py: filename-hour -> hour_fn,
        # sensor hour keeps the bare name (P1 masks are defined on sensor hour)
        f = fi.merge(j, on=["visual_video_id", "split"], how="left", suffixes=("_fn", ""))
        masks = masks_corpus_b(f)
        qidx = RNG.choice(len(X), 200, replace=False)   # image layer [M6]
        Q = X[qidx]
        self_ids = qidx
        layer = "image_confirmatory"
    reg = pd.read_csv(OUT / f"P1_predicates_{corpus}.csv")
    reg = dict(zip(reg.predicate, reg["count"]))
    for n, k, m in masks:                    # B1: assert masks match registration
        if n in reg:
            assert int(m.sum()) == int(reg[n]), f"P1 mismatch {n}: {m.sum()} != {reg[n]}"
    return X, Q, self_ids, masks, layer


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", choices=["A", "B"], required=True)
    ap.add_argument("--timing-queries", type=int, default=500)
    ap.add_argument("--repeats", type=int, default=15)
    ap.add_argument("--warmup", type=int, default=5)
    ap.add_argument("--limit-predicates", type=int, default=None)
    args = ap.parse_args()
    import faiss
    faiss.omp_set_num_threads(0)
    OUT.mkdir(parents=True, exist_ok=True)

    X, Q, self_ids, masks, layer = setup(args.corpus, args, faiss)
    N, d = X.shape
    Qt = Q[:min(args.timing_queries, len(Q))]
    print(f"[{args.corpus}] corpus={N}x{d} queries={len(Q)} timing_n={len(Qt)} "
          f"predicates={len(masks)} layer={layer}", flush=True)

    # shared structures (built once)
    t0 = time.perf_counter()
    full_h = faiss.IndexHNSWFlat(d, 32, faiss.METRIC_INNER_PRODUCT)
    full_h.hnsw.efConstruction = 200; full_h.add(X); full_h.hnsw.efSearch = 64
    t_h = time.perf_counter() - t0
    t0 = time.perf_counter()
    quant = faiss.IndexFlatIP(d)
    full_ivf = faiss.IndexIVFFlat(quant, d, 1024, faiss.METRIC_INNER_PRODUCT)
    full_ivf.train(X); full_ivf.add(X)
    t_i = time.perf_counter() - t0
    flat = faiss.IndexFlatIP(d); flat.add(X)
    _, exact_top = flat.search(Q, 1000)      # M9 covariate base
    print(f"[shared] full HNSW {t_h:.0f}s, full IVF {t_i:.0f}s", flush=True)

    if args.limit_predicates:
        masks = masks[:args.limit_predicates]
    rows = []
    for pi, (name, kind, mask) in enumerate(masks):
        m = int(mask.sum())
        t0 = time.perf_counter()
        rows += bench_block(name, kind, mask, X, Q, Qt, full_h, full_ivf,
                            exact_top, self_ids, args, faiss)
        # M9 paired random-mask control at identical size
        ctrl = np.zeros(N, bool)
        ctrl[RNG.choice(N, m, replace=False)] = True
        rows += bench_block(f"CTRL(s={m/N:.4f})|{name}", "control", ctrl, X, Q, Qt,
                            full_h, full_ivf, exact_top, self_ids, args, faiss)
        pd.DataFrame(rows).to_csv(OUT / f"filtered_ann_real_{args.corpus}.csv", index=False)
        print(f"  [{pi+1}/{len(masks)}] {name} (m={m}) done in {time.perf_counter()-t0:.0f}s "
              f"rows={len(rows)}", flush=True)

    manifest = {"corpus": args.corpus, "N": int(N), "dim": int(d), "k": K,
                "queries": int(len(Q)), "timing_queries": int(len(Qt)),
                "repeats": args.repeats, "warmup": "kept, excluded from stats [M2]",
                "efSearch_unified": 64, "layer": layer,
                "timing_boundary": "query->K results incl. postfilter mask+truncate [M1]",
                "controls": "paired random-mask at identical subset size [M9]",
                "full_hnsw_build_s": round(t_h, 1), "full_ivf_build_s": round(t_i, 1),
                "faiss_threads_timing": 1}
    (OUT / f"filtered_ann_real_{args.corpus}_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[saved] {OUT}/filtered_ann_real_{args.corpus}.csv ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
