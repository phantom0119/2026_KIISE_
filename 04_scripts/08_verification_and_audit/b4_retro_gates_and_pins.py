#!/usr/bin/env python3
"""B-4 [Amendment 5a (5)(6)]: retroactive gates + reproducibility pins.

1. qidx_B.npy saved + sha256 (corpus-B query indices; cross-version numpy
   agreement was verified by the review, this pins it as an artifact).
2. Bidirectional P1 assertion: re-derived predicate-name set == registered
   non-meta rows EXACTLY (A 29, B 25), counts equal.
3. Retroactive G-filter gate on already-collected Milvus data: engine-side
   count(p_i==true) == frozen local mask size, all masks, both corpora.

Run in kiise-vlmdb env (faiss not needed; pymilvus present).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

import run_filtered_ann_real_predicate as b1

R2 = Path(__file__).resolve().parents[2]
OUT = R2 / "paper_assets" / "20260712_engine_replication"
P1 = R2 / "paper_assets" / "20260710_pillarB"

report = {}

# (1) pin corpus-B query indices
z = np.load(OUT / "inputs_B.npz")
qidx = z["self_ids"]
np.save(OUT / "qidx_B.npy", qidx)
sha = hashlib.sha256(qidx.tobytes()).hexdigest()
rederive = np.random.default_rng(20260710).choice(143830, 200, replace=False)
assert np.array_equal(qidx, rederive), "qidx re-derivation mismatch!"
report["qidx_B"] = {"sha256": sha, "first5": qidx[:5].tolist(),
                    "rederivation_match": True}
print(f"[pin] qidx_B.npy sha256={sha[:16]}… rederivation OK")

# (2) bidirectional P1 set assertion
for corpus in ["A", "B"]:
    if corpus == "A":
        fi = pd.read_parquet(b1.SIN / "frame_index.parquet")
        masks = b1.masks_corpus_a(fi)
    else:
        V = b1.V522 / "visual_embeddings_clip"
        fi = pd.read_parquet(V / "frame_index.parquet")
        join = pd.read_parquet(b1.V522 / "visual_sensor_join.parquet")
        j = join[join.join_ok_120s][["visual_video_id", "split", "time_of_day", "hour",
                                     "sig_has_yellow", "sig_has_pedestrian", "veh_density_bin"]]
        f = fi.merge(j, on=["visual_video_id", "split"], how="left", suffixes=("_fn", ""))
        masks = b1.masks_corpus_b(f)
    reg = pd.read_csv(P1 / f"P1_predicates_{corpus}.csv")
    reg = reg[~reg.predicate.str.contains(r"\(joined frames\)", regex=True)]
    derived = {n: int(m.sum()) for n, _, m in masks}
    reg_map = dict(zip(reg.predicate, reg["count"]))
    assert set(derived) == set(reg_map), \
        f"{corpus}: name sets differ: {set(derived) ^ set(reg_map)}"
    mism = {n: (derived[n], reg_map[n]) for n in derived if derived[n] != reg_map[n]}
    assert not mism, f"{corpus}: count mismatches {mism}"
    report[f"P1_bidirectional_{corpus}"] = {"n": len(derived), "pass": True}
    print(f"[P1] {corpus}: bidirectional set+count equality OK (n={len(derived)})")

# (3) retroactive Milvus G-filter gate
from pymilvus import MilvusClient
c = MilvusClient(uri="http://localhost:19530")
for corpus in ["A", "B"]:
    meta = pd.read_csv(OUT / f"inputs_{corpus}_meta.csv")
    coll = f"kiise_{corpus.lower()}_b4"
    bad = []
    for _, r in meta.iterrows():
        n_eng = int(c.query(coll, filter=f"p{int(r.mask_id)} == true",
                            output_fields=["count(*)"])[0]["count(*)"])
        if n_eng != int(r.subset):
            bad.append((r.predicate, n_eng, int(r.subset)))
    assert not bad, f"{corpus}: milvus count mismatches {bad[:5]}"
    report[f"milvus_gfilter_{corpus}"] = {"masks": len(meta), "pass": True}
    print(f"[G-filter] milvus {corpus}: {len(meta)} masks all match")

(OUT / "retro_gates_report.json").write_text(json.dumps(report, indent=2))
print(f"[saved] {OUT}/retro_gates_report.json")
