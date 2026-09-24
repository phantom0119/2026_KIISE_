#!/usr/bin/env python3
"""G1 prep: convert internal corpora to HCBGen inputs + build the NATURAL-arm
workload (tests.jsonl with exact filtered GT) per G1_DECISION_RULE.md.

Per corpus writes into p0_validity_audit/g1/<corpus>/:
  base.fvecs, vectors.npy          corpus vectors (fp32, already L2-normalized)
  queries.fvecs                    the real query set (A:1000 text, B:200 image)
  payloads.jsonl                   integer-encoded REAL attributes (NaN -> key omitted)
  attr_encoding.json               value<->int mappings (reproducibility)
  natural/tests.jsonl              1,000 stratified (query, equality-predicate)
                                   pairs, seed 20260805, with exact IP top-10 GT
                                   (B: self-excluded)
  natural/vectors.npy, payloads.jsonl   symlink-free copies for the estimator
  natural/pair_manifest.parquet    test_idx -> (predicate, query_idx, attr, value)

Safety: every parsed (attr==value) condition mask is asserted EQUAL to the
original locked P1 mask from base.setup() before anything is written.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve()
P0DIR = HERE.parents[1]
KIISE = next((p for p in HERE.parents if (p / "00_env").exists() or (p / "04_scripts").exists()), HERE.parents[3])
sys.path.insert(0, str(KIISE / "scripts"))
import run_filtered_ann_real_predicate as base  # noqa: E402

SEED = 20260805
N_PAIRS = 1000
K = 10


def write_fvecs(path: Path, X: np.ndarray) -> None:
    n, d = X.shape
    rec = np.empty((n, d + 1), dtype="<f4")
    rec[:, 0:1] = np.frombuffer(np.array([d], dtype="<i4").tobytes(), dtype="<f4")
    rec[:, 1:] = X.astype("<f4")
    rec.tofile(path)


def gpu_topk_filtered(X, Q, mask, k, self_ids=None):
    """Exact IP top-k within mask per query; returns global ids (nq,k)."""
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


def build_corpus(corpus: str) -> None:
    out = P0DIR / "g1" / corpus
    nat = out / "natural"
    nat.mkdir(parents=True, exist_ok=True)
    X, Q, self_ids, masks, layer = base.setup(corpus, None, None)
    N, d = X.shape

    # ---- payload columns + encodings ----
    enc: dict[str, dict] = {}
    cols: dict[str, np.ndarray] = {}       # attr -> int array with -1 = missing
    if corpus == "A":
        fi = pd.read_parquet(base.SIN / "frame_index.parquet")
        loc_vals = sorted(fi["location"].dropna().astype(str).unique())
        enc["location"] = {v: i for i, v in enumerate(loc_vals)}
        cols["location"] = fi["location"].astype(str).map(enc["location"]).fillna(-1).astype(int).to_numpy()
        date_num = pd.to_numeric(fi["date"], errors="coerce")
        cols["date"] = date_num.fillna(-1).astype(int).to_numpy()
        enc["date"] = "identity:int(yyyymmdd)"
        hour_num = pd.to_numeric(fi["time"].astype(str).str[:2], errors="coerce")
        cols["hour"] = hour_num.fillna(-1).astype(int).to_numpy()
        enc["hour"] = "identity:int(0-23)"

        def parse(name: str):
            attr, v = name.split("==")
            if attr == "location":
                return attr, int(enc["location"][v])
            return attr, int(v)
    else:
        V = base.V522 / "visual_embeddings_clip"
        fi = pd.read_parquet(V / "frame_index.parquet")
        join = pd.read_parquet(base.V522 / "visual_sensor_join.parquet")
        j = join[join.join_ok_120s][["visual_video_id", "split", "time_of_day", "hour",
                                     "sig_has_yellow", "sig_has_pedestrian", "veh_density_bin"]]
        f = fi.merge(j, on=["visual_video_id", "split"], how="left", suffixes=("_fn", ""))
        assert len(f) == N, (len(f), N)
        enc["time_of_day"] = {"morning": 0, "afternoon": 1, "evening": 2}
        enc["veh_density_bin"] = {"low": 0, "mid": 1, "high": 2}
        enc["sig_has_yellow"] = {"False": 0, "True": 1}
        enc["sig_has_pedestrian"] = {"False": 0, "True": 1}
        enc["hour"] = "identity:int"
        cols["time_of_day"] = f["time_of_day"].map(enc["time_of_day"]).fillna(-1).astype(int).to_numpy()
        cols["veh_density_bin"] = f["veh_density_bin"].astype(str).map(enc["veh_density_bin"]).fillna(-1).astype(int).to_numpy()
        for c in ["sig_has_yellow", "sig_has_pedestrian"]:
            s = f[c].map({True: 1, False: 0})
            cols[c] = s.fillna(-1).astype(int).to_numpy()
        cols["hour"] = pd.to_numeric(f["hour"], errors="coerce").fillna(-1).astype(int).to_numpy()

        def parse(name: str):
            attr, v = name.split("==")
            if attr in ("sig_has_yellow", "sig_has_pedestrian"):
                return attr, int(enc[attr][v])
            if attr in ("time_of_day", "veh_density_bin"):
                return attr, int(enc[attr][v])
            return attr, int(v)

    # ---- natural equality predicates: parse + ASSERT mask equality ----
    nat_preds = []
    for name, kind, m in masks:
        if kind != "natural":
            continue
        attr, val = parse(name)
        rebuilt = cols[attr] == val
        assert np.array_equal(rebuilt, m), f"mask mismatch {corpus}:{name}"
        nat_preds.append((name, attr, int(val), m))
    print(f"[{corpus}] equality predicates verified: {len(nat_preds)}")

    # ---- stratified pair sample ----
    rng = np.random.default_rng(SEED)
    per = int(np.ceil(N_PAIRS / len(nat_preds)))
    pairs = []
    for name, attr, val, m in nat_preds:
        qs = rng.choice(len(Q), size=min(per, len(Q)), replace=False)
        for qi in qs:
            pairs.append((name, attr, val, int(qi)))
    pairs = pairs[:N_PAIRS]
    print(f"[{corpus}] pairs: {len(pairs)} ({per}/predicate x {len(nat_preds)})")

    # ---- exact filtered GT per predicate group ----
    manifest = pd.DataFrame(pairs, columns=["predicate", "attr", "value", "query_idx"])
    gt_all = np.empty((len(manifest), K), dtype=np.int64)
    for name, grp in manifest.groupby("predicate", sort=False):
        m = next(mm for nn, _, _, mm in nat_preds if nn == name)
        qidx = grp.query_idx.to_numpy()
        sids = self_ids[qidx] if (self_ids >= 0).any() else None
        gt = gpu_topk_filtered(X, Q[qidx], m, K, sids)
        assert gt.shape == (len(qidx), K)
        gt_all[grp.index.to_numpy()] = gt

    # ---- write artifacts ----
    np.save(out / "vectors.npy", X.astype("float32"))
    write_fvecs(out / "base.fvecs", X)
    write_fvecs(out / "queries.fvecs", Q)
    with open(out / "payloads.jsonl", "w") as fh:
        for i in range(N):
            rec = {a: int(v[i]) for a, v in cols.items() if v[i] >= 0}
            fh.write(json.dumps(rec) + "\n")
    (out / "attr_encoding.json").write_text(json.dumps(enc, ensure_ascii=False, indent=2, default=str))

    with open(nat / "tests.jsonl", "w") as fh:
        for r, (name, attr, val, qi) in enumerate(pairs):
            rec = {"query": [float(x) for x in Q[qi]],
                   "conditions": {"and": [{attr: {"match": {"value": int(val)}}}]},
                   "closest_ids": [int(x) for x in gt_all[r]]}
            fh.write(json.dumps(rec) + "\n")
    shutil.copy(out / "vectors.npy", nat / "vectors.npy")
    shutil.copy(out / "payloads.jsonl", nat / "payloads.jsonl")
    manifest.to_parquet(nat / "pair_manifest.parquet", index=False)
    print(f"[{corpus}] written -> {out}")


if __name__ == "__main__":
    for c in sys.argv[1:] or ["A", "B"]:
        build_corpus(c)
