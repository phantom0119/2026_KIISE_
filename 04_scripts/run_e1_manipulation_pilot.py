#!/usr/bin/env python3
"""E-1 step 1b [AMD-B3]: retrieval-only manipulation-check pilot.

Before spending 12-20 GPU-hours on the index-swap RAG-VQA run, verify that the
candidate ANN configs actually produce the intended evidence-recall degradation
bands on THIS corpus (VRU 1,000 captions, bge-m3 1024d) — the old spec cited an
IVFPQ figure that does not transfer (131K/512d CLIP != 1K/1024d bge-m3).

Replicates run_rag_vqa.py retrieval semantics exactly: query = the clip's OTHER
context facets (exclude the asked one), corpus = 1,000 captions, vector_only
channel, exclude=cid. Mediator per AMD-B2: evidence-recall@3 = fraction of items
whose top-3 contains >=1 OTHER-clip caption with facet f == answer value v.

Gate (relative to exact):  mid in [0.55, 0.85] x exact ; strong in [0.30, 0.55] x exact.
Ladder [AMD-B3]: HNSW ef 16->8->4->2, M 32->8 ; IVFPQ nlist{16,25} nprobe 8->4->2->1 m 8->4.

Output: paper_assets/20260710_pillarB/e1_pilot_configs.csv + e1_locked_configs.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DS = PROJECT_ROOT / "Datasets"
EXP = PROJECT_ROOT / "2026_KIISE" / "experiments_expansion" / "rag_vqa"
CAN = DS / "processed" / "vru_accident" / "20260706" / "canonical"
OUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260710_pillarB"

CAT2FACET = {
    "weather and light": "weather_light", "location": "location", "road type": "road_type",
    "accident type": "accident_type", "accident reason": "accident_reason",
    "prevention method": "prevention_method",
}
FILTER_FACETS = ["weather_light", "location", "road_type", "accident_type"]
K = 3


def load_data():
    vqa = pd.read_parquet(EXP / "vqa_joined.parquet")
    meta = pd.read_parquet(CAN / "metadata.parquet")
    facets = {cid: dict(zip(g["facet_name"], g["facet_value"]))
              for cid, g in meta.groupby("clip_id")}
    caps = vqa.drop_duplicates("clip_id").set_index("clip_id")["caption"].to_dict()
    return vqa, facets, caps


def build_query(item, facets):
    tgt = CAT2FACET[item["category"]]
    f = facets.get(item["clip_id"], {})
    ctx = [f"{k.replace('_',' ')}: {f[k]}" for k in FILTER_FACETS if k in f and k != tgt]
    return "; ".join(ctx) if ctx else item["question"]


def embed_bge(texts, device):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(str(DS / "models/huggingface/BAAI--bge-m3"), device=device)
    return np.asarray(m.encode(texts, batch_size=64, normalize_embeddings=True,
                               show_progress_bar=False), dtype="float32")


def build_index(kind, X, params):
    import faiss
    d = X.shape[1]
    if kind == "flat":
        idx = faiss.IndexFlatIP(d)
    elif kind == "hnsw":
        idx = faiss.IndexHNSWFlat(d, params["M"], faiss.METRIC_INNER_PRODUCT)
        idx.hnsw.efConstruction = 200
    elif kind == "ivfpq":
        quant = faiss.IndexFlatIP(d)
        idx = faiss.IndexIVFPQ(quant, d, params["nlist"], params["m"], params.get("nbits", 8),
                               faiss.METRIC_INNER_PRODUCT)
        idx.train(X)
    idx.add(X)
    if kind == "hnsw":
        idx.hnsw.efSearch = params["ef"]
    if kind == "ivfpq":
        idx.nprobe = params["nprobe"]
    return idx


def main() -> int:
    device = sys.argv[1] if len(sys.argv) > 1 else "cuda:0"
    OUT.mkdir(parents=True, exist_ok=True)
    vqa, facets, caps = load_data()
    cap_ids = list(caps.keys())
    id2pos = {c: i for i, c in enumerate(cap_ids)}
    print(f"[data] items={len(vqa)} captions={len(cap_ids)}")

    cap_mat = embed_bge([caps[c] for c in cap_ids], device)
    queries = [build_query(r, facets) for _, r in vqa.iterrows()]
    qmat = embed_bge(queries, device)
    print(f"[embed] captions {cap_mat.shape}, queries {qmat.shape}")

    # evidence sets per item [AMD-B2]: OTHER clips with facet f == this clip's value
    ev_sets, self_pos = [], []
    for _, it in vqa.iterrows():
        cid = it["clip_id"]; f = CAT2FACET[it["category"]]
        v = facets.get(cid, {}).get(f)
        ev = {id2pos[c] for c in cap_ids
              if c != cid and v is not None and facets.get(c, {}).get(f) == v}
        ev_sets.append(ev); self_pos.append(id2pos[cid])
    print(f"[qrels] mean evidence-set size = {np.mean([len(e) for e in ev_sets]):.1f}")

    def evidence_recall(index) -> float:
        _, I = index.search(qmat, K + 1)   # +1 to allow self-exclusion
        hit = 0
        for row, ev, sp in zip(I, ev_sets, self_pos):
            top = [i for i in row if i != sp][:K]
            if ev.intersection(top):
                hit += 1
        return hit / len(ev_sets)

    import faiss
    faiss.omp_set_num_threads(0)
    rows = []
    exact = build_index("flat", cap_mat, {})
    er_exact = evidence_recall(exact)
    rows.append({"config": "flat_exact", "evidence_recall@3": round(er_exact, 4), "rel": 1.0})
    print(f"[exact] evidence-recall@3 = {er_exact:.4f}")

    LADDER = ([("hnsw", {"M": M, "ef": ef}) for M in (32, 8) for ef in (16, 8, 4, 2, 1)]
              + [("ivfpq", {"nlist": nl, "m": m, "nprobe": np_}) for nl in (16, 25)
                 for m in (8, 4) for np_ in (8, 4, 2, 1)])
    for kind, p in LADDER:
        name = f"{kind}_" + "_".join(f"{k}{v}" for k, v in p.items())
        try:
            er = evidence_recall(build_index(kind, cap_mat, p))
        except Exception as e:
            print(f"  {name}: SKIP ({type(e).__name__}: {e})"); continue
        rel = er / er_exact if er_exact > 0 else 0
        rows.append({"config": name, "evidence_recall@3": round(er, 4), "rel": round(rel, 4)})
        print(f"  {name:28s} er@3={er:.4f}  rel={rel:.3f}")

    df = pd.DataFrame(rows)
    df.to_csv(OUT / "e1_pilot_configs.csv", index=False)

    # gate selection [AMD-B3]
    mid = df[(df.rel >= 0.55) & (df.rel <= 0.85)].sort_values("rel", ascending=False)
    strong = df[(df.rel >= 0.30) & (df.rel <= 0.55)].sort_values("rel", ascending=False)
    lock = {
        "exact": "flat_exact",
        "mid": mid.iloc[0]["config"] if len(mid) else None,
        "strong": strong.iloc[0]["config"] if len(strong) else None,
        "gate": "mid rel in [0.55,0.85]; strong rel in [0.30,0.55] (vs exact)",
        "exact_er3": round(er_exact, 4),
        "gate_pass": bool(len(mid) and len(strong)),
    }
    (OUT / "e1_locked_configs.json").write_text(json.dumps(lock, indent=2))
    print(f"\n[GATE] pass={lock['gate_pass']}  mid={lock['mid']}  strong={lock['strong']}")
    print(f"[saved] {OUT}/e1_pilot_configs.csv + e1_locked_configs.json")
    return 0 if lock["gate_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
