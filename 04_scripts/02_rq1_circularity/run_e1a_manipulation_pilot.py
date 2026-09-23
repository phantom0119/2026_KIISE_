#!/usr/bin/env python3
"""E-1(a) manipulation-check pilot [prereg 420 Amendment 3, gate BEFORE VLM spend].

Redesigned answer-coupling experiment at 143K scale (522-visual), where B-2
measured real index degradation (IVFPQ recall .35-.49, IVFFlat np1 .80).

Item = (visual video v, scene question about v's moment, gold from the
        human-annotation channel of v).
Retrieval = query embedding of v's MIDDLE frame over the FULL 143,830-frame
        corpus (self excluded); DB supplies top-k frames as VLM evidence.
MEDIATOR = moment-recall@k: >=1 retrieved frame from v's MOMENT GROUP =
        {sibling frames of v} ∪ {frames of cross-camera videos joined to the
        SAME sensor clip}. Index degradation must move this mediator for the
        answer experiment to be interpretable.

Gate (relative to exact): mid in [0.55, 0.85], strong in [0.30, 0.55].
Ladder: HNSW ef {16,8,4,2,1} x M {32,8}; IVFFlat nlist1024 nprobe {8,4,2,1};
        IVFPQ nlist1024 m {32,64} nprobe {8,1}  (all buildable from B-2 grid).

Output: paper_assets/20260711_e1a/e1a_pilot_mediator.csv + e1a_locked_configs.json
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
V = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
OUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260711_e1a"
K = 3
N_ITEMS = 3000
RNG = np.random.default_rng(20260711)


def main() -> int:
    import faiss
    OUT.mkdir(parents=True, exist_ok=True)
    X = np.load(V / "visual_embeddings_clip" / "frame_embeddings.npy").astype("float32")
    fi = pd.read_parquet(V / "visual_embeddings_clip" / "frame_index.parquet")
    fi = fi.reset_index(drop=True).reset_index(names="row")
    join = pd.read_parquet(V / "visual_sensor_join.parquet")
    ann = pd.read_parquet(V / "annotation_video_facets.parquet")

    # moment groups: videos sharing the same joined sensor clip
    jok = join[join.join_ok_120s][["visual_video_id", "split", "sensor_clip_id"]]
    fi = fi.merge(jok, on=["visual_video_id", "split"], how="left")
    grp = fi.dropna(subset=["sensor_clip_id"]).groupby("sensor_clip_id")["row"].apply(list)
    row2grp = {}
    for gid, rows in grp.items():
        for r in rows:
            row2grp[r] = gid
    print(f"[groups] moment groups={len(grp)}  frames in groups={len(row2grp)}")

    # item pool: joined + annotated videos, middle frame as query
    pool = (jok.merge(ann[["visual_video_id", "split", "max_bus", "any_stopped", "max_bike"]],
                      on=["visual_video_id", "split"]))
    vids = pool.drop_duplicates(["visual_video_id", "split"])
    vids = vids.sample(min(N_ITEMS, len(vids)), random_state=20260711)
    frames_by_vid = fi.groupby(["visual_video_id", "split"])["row"].apply(sorted)
    q_rows, ev_sets = [], []
    for _, r in vids.iterrows():
        rows = frames_by_vid.get((r.visual_video_id, r.split))
        if not rows or len(rows) < 2:
            continue
        qrow = rows[len(rows) // 2]
        gid = row2grp.get(qrow)
        if gid is None:
            continue
        ev = set(grp[gid]) - {qrow}
        if not ev:
            continue
        q_rows.append(qrow); ev_sets.append(ev)
    Q = X[q_rows]
    print(f"[items] n={len(q_rows)}  median evidence-frames/item="
          f"{np.median([len(e) for e in ev_sets]):.0f}")

    def mediator(index) -> float:
        _, I = index.search(Q, K + 1)
        hit = 0
        for row, ev, qr in zip(I, ev_sets, q_rows):
            top = [i for i in row if i != qr][:K]
            if ev.intersection(top):
                hit += 1
        return hit / len(q_rows)

    d = X.shape[1]
    faiss.omp_set_num_threads(0)
    results = []
    flat = faiss.IndexFlatIP(d); flat.add(X)
    m_exact = mediator(flat)
    results.append({"config": "flat_exact", "moment_recall@3": round(m_exact, 4), "rel": 1.0})
    print(f"[exact] moment-recall@3 = {m_exact:.4f}", flush=True)

    LADDER = ([("hnsw", {"M": M, "ef": ef}) for M in (32, 8) for ef in (16, 8, 4, 2, 1)]
              + [("ivfflat", {"nlist": 1024, "nprobe": p}) for p in (8, 4, 2, 1)]
              + [("ivfpq", {"nlist": 1024, "m": m, "nprobe": p})
                 for m in (64, 32) for p in (8, 1)])
    for kind, prm in LADDER:
        t0 = time.time()
        if kind == "hnsw":
            idx = faiss.IndexHNSWFlat(d, prm["M"], faiss.METRIC_INNER_PRODUCT)
            idx.hnsw.efConstruction = 200; idx.add(X); idx.hnsw.efSearch = prm["ef"]
        elif kind == "ivfflat":
            qz = faiss.IndexFlatIP(d)
            idx = faiss.IndexIVFFlat(qz, d, prm["nlist"], faiss.METRIC_INNER_PRODUCT)
            idx.train(X); idx.add(X); idx.nprobe = prm["nprobe"]
        else:
            qz = faiss.IndexFlatIP(d)
            idx = faiss.IndexIVFPQ(qz, d, prm["nlist"], prm["m"], 8, faiss.METRIC_INNER_PRODUCT)
            idx.train(X); idx.add(X); idx.nprobe = prm["nprobe"]
        mr = mediator(idx)
        rel = mr / m_exact
        name = f"{kind}_" + "_".join(f"{k}{v}" for k, v in prm.items())
        results.append({"config": name, "moment_recall@3": round(mr, 4), "rel": round(rel, 4)})
        print(f"  {name:26s} mr@3={mr:.4f} rel={rel:.3f} ({time.time()-t0:.0f}s)", flush=True)

    df = pd.DataFrame(results)
    df.to_csv(OUT / "e1a_pilot_mediator.csv", index=False)
    mid = df[(df.rel >= 0.55) & (df.rel <= 0.85)].sort_values("rel", ascending=False)
    strong = df[(df.rel >= 0.30) & (df.rel < 0.55)].sort_values("rel", ascending=False)
    lock = {"exact": "flat_exact", "exact_mr3": round(m_exact, 4),
            "mid": mid.iloc[0]["config"] if len(mid) else None,
            "strong": strong.iloc[0]["config"] if len(strong) else None,
            "gate_pass": bool(len(mid) and len(strong)),
            "n_items_pilot": len(q_rows),
            "gate": "mid rel in [0.55,0.85]; strong in [0.30,0.55) vs exact"}
    (OUT / "e1a_locked_configs.json").write_text(json.dumps(lock, indent=2))
    print(f"\n[GATE] pass={lock['gate_pass']}  mid={lock['mid']}  strong={lock['strong']}")
    return 0 if lock["gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
