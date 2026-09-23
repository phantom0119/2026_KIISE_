#!/usr/bin/env python3
"""P1 (DB contribution) — STORAGE-UNIT comparison for VLM-QA evidence retrieval.

Same queries/qrels, four ways of STORING the clip evidence:

  clip-caption  : 1 text vector / clip  (bge-m3 caption)          -> text semantics
  frame-vector  : 1 CLIP vector / frame, flat frame index; a clip
                  is retrieved if a frame lands in the global top-N -> cross-modal, cutoff-limited
  multi-vector  : clip = its K frame CLIP vectors, scored by MAX-SIM
                  over ALL its frames (ColBERT-style, exhaustive)   -> cross-modal, no cutoff
  dual-index    : RRF fusion of clip-caption + multi-vector          -> text + visual

Reports, per condition x {strict, semantic} qrels: nDCG@10 / recall@10 / MRR,
plus isolated search latency (p50/p95) and storage (vectors x dim x 4B + FAISS
index bytes). This measures how the storage UNIT trades accuracy vs latency vs
space — the DB design axis the paper argues.

Cross-modal note: CLIP text-encodes the query_text to search CLIP image frames.
bge-m3 caption retrieval and CLIP visual retrieval are different embedding spaces;
we compare them as STORAGE designs, not as encoder ablations (stated as a caveat).

Run (522):
  Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/scripts/run_storage_unit_benchmark.py \
    --dataset s522 \
    --canonical-root Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded \
    --caption-emb Datasets/processed/aihub_522_intersection/20260710/embeddings_trisource_expanded/bge-m3 \
    --clip-frame-emb Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip \
    --out Datasets/processed/aihub_522_intersection/20260710/results/storage_unit
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import faiss
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "2026_KIISE" / "src"))
from vlmdb_workload.metrics import evaluate_ranking  # noqa: E402

CLIP_MODEL = PROJECT_ROOT / "Datasets" / "models" / "huggingface"
TOP_KS = [1, 5, 10, 20]
MAX_RANK = 100
FRAME_TOPN = 200  # frame-vector: global frame cutoff before collapsing to clips


def load_queries(canon: Path):
    q = [json.loads(l) for l in (canon / "queries.jsonl").read_text().splitlines() if l.strip()]
    return q


def qrels_positives(path: Path):
    df = pd.read_csv(path, sep="\t")
    return {qid: set(g["target_id"]) for qid, g in df.groupby("query_id", sort=False)}


def clip_text_embeddings(query_texts, device="cuda"):
    import torch
    from transformers import CLIPModel, CLIPProcessor
    mid = "openai/clip-vit-base-patch32"
    proc = CLIPProcessor.from_pretrained(mid, cache_dir=str(CLIP_MODEL))
    model = CLIPModel.from_pretrained(mid, cache_dir=str(CLIP_MODEL)).to(device).eval()
    out = []
    with torch.inference_mode():
        for i in range(0, len(query_texts), 64):
            b = query_texts[i:i + 64]
            inp = proc(text=b, padding=True, truncation=True, return_tensors="pt").to(device)
            emb = model.get_text_features(**inp)
            if not isinstance(emb, torch.Tensor):  # transformers 5.x returns a wrapped output
                to = model.text_model(input_ids=inp["input_ids"],
                                      attention_mask=inp.get("attention_mask"))
                emb = model.text_projection(to.pooler_output)  # -> projected 512d, image-embed space
            out.append(emb.detach().cpu().float().numpy())
    v = np.vstack(out).astype("float32")
    v /= np.clip(np.linalg.norm(v, axis=1, keepdims=True), 1e-8, None)
    return v


def frame_clip_ids(frame_index: pd.DataFrame, mode: str) -> np.ndarray:
    if mode == "s522":
        return ("aihub_522_intersection_vis:" + frame_index["split"].astype(str)
                + ":" + frame_index["visual_video_id"].astype(str)).to_numpy()
    if mode == "col":
        return frame_index["clip_id"].astype(str).to_numpy()
    raise ValueError(mode)


def rank_metrics(ranking, positives, tag):
    return evaluate_ranking(ranking, positives, TOP_KS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--canonical-root", type=Path, required=True)
    ap.add_argument("--caption-emb", type=Path, required=True, help="bge-m3 dir (document_embeddings.npy...)")
    ap.add_argument("--clip-frame-emb", type=Path, required=True, help="dir with frame_embeddings.npy + frame_index.parquet")
    ap.add_argument("--frame-clip-mode", default="s522", choices=["s522", "col"])
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    queries = load_queries(args.canonical_root)
    qids = [q["query_id"] for q in queries]
    qtexts = [q["query_text"] for q in queries]
    pos_strict = qrels_positives(args.canonical_root / "qrels.tsv")
    pos_sem = qrels_positives(args.canonical_root / "qrels_semantic.tsv")

    # ---- clip-caption (bge-m3) ----
    cap_docs = np.load(args.caption_emb / "document_embeddings.npy").astype("float32")
    cap_q = np.load(args.caption_emb / "query_embeddings.npy").astype("float32")
    cap_di = pd.read_parquet(args.caption_emb / "document_index.parquet")
    cap_qi = pd.read_parquet(args.caption_emb / "query_index.parquet")
    cap_clip = cap_di["clip_id"].to_numpy()
    corpus_clips = set(cap_clip)
    faiss.normalize_L2(cap_docs); faiss.normalize_L2(cap_q)
    cap_idx = faiss.IndexFlatIP(cap_docs.shape[1]); cap_idx.add(cap_docs)
    capq_by_id = {cap_qi.iloc[i]["query_id"]: cap_q[i] for i in range(len(cap_qi))}

    # ---- CLIP frames -> restrict to corpus clips ----
    fe = np.load(args.clip_frame_emb / "frame_embeddings.npy").astype("float32")
    fi = pd.read_parquet(args.clip_frame_emb / "frame_index.parquet")
    fcids = frame_clip_ids(fi, args.frame_clip_mode)
    keep = np.array([c in corpus_clips for c in fcids])
    fe = np.ascontiguousarray(fe[keep]); fcids = fcids[keep]
    faiss.normalize_L2(fe)
    frame_idx = faiss.IndexFlatIP(fe.shape[1]); frame_idx.add(fe)
    # per-clip frame row groups for multi-vector max-sim
    clip_to_rows: dict[str, list[int]] = {}
    for r, c in enumerate(fcids):
        clip_to_rows.setdefault(c, []).append(r)
    clip_list = list(clip_to_rows.keys())
    clip_row_arrays = [np.array(clip_to_rows[c]) for c in clip_list]

    # ---- CLIP query-text ----
    clip_qtext = clip_text_embeddings(qtexts, args.device)
    clipq_by_id = {qids[i]: clip_qtext[i] for i in range(len(qids))}

    print(f"[assets] clips(caption)={len(cap_clip)}  frames(kept)={len(fcids)}  "
          f"clips(with frames)={len(clip_list)}  queries={len(qids)}", flush=True)

    def cap_ranking(qid):
        v = capq_by_id[qid].reshape(1, -1).astype("float32")
        s, idx = cap_idx.search(v, min(MAX_RANK, len(cap_clip)))
        return [cap_clip[i] for i in idx[0] if i >= 0]

    def framevec_ranking(qid):
        v = clipq_by_id[qid].reshape(1, -1).astype("float32")
        s, idx = frame_idx.search(v, FRAME_TOPN)
        best: dict[str, float] = {}
        for sc, i in zip(s[0], idx[0]):
            if i < 0:
                continue
            c = fcids[i]
            if c not in best or sc > best[c]:
                best[c] = float(sc)
        return [c for c, _ in sorted(best.items(), key=lambda x: -x[1])[:MAX_RANK]]

    def multivec_ranking(qid):
        v = clipq_by_id[qid].astype("float32")
        sims = fe @ v  # (n_frames,)
        scores = np.array([sims[rows].max() for rows in clip_row_arrays])
        order = np.argsort(-scores)[:MAX_RANK]
        return [clip_list[i] for i in order]

    def rrf(r1, r2, k=60):
        sc: dict[str, float] = {}
        for r in (r1, r2):
            for rank, c in enumerate(r, 1):
                sc[c] = sc.get(c, 0.0) + 1.0 / (k + rank)
        return [c for c, _ in sorted(sc.items(), key=lambda x: -x[1])[:MAX_RANK]]

    conditions = {
        "clip_caption": cap_ranking,
        "frame_vector": framevec_ranking,
        "multi_vector": multivec_ranking,
        "dual_index": lambda qid: rrf(cap_ranking(qid), multivec_ranking(qid)),
    }

    rows, lat_rows = [], []
    per_q_rank = {c: {} for c in conditions}
    for cond, fn in conditions.items():
        lats = []
        for qid in qids:
            t = time.perf_counter()
            ranking = fn(qid)
            lats.append((time.perf_counter() - t) * 1000.0)
            per_q_rank[cond][qid] = ranking
        lat_rows.append({"condition": cond, "lat_mean_ms": np.mean(lats),
                         "lat_p50_ms": np.percentile(lats, 50), "lat_p95_ms": np.percentile(lats, 95)})

    for cond in conditions:
        for tag, pos in [("strict", pos_strict), ("semantic", pos_sem)]:
            ms = [evaluate_ranking(per_q_rank[cond][qid], pos.get(qid, set()), TOP_KS) for qid in qids]
            agg = {k: float(np.mean([m[k] for m in ms])) for k in ms[0]}
            rows.append({"condition": cond, "qrels": tag,
                         "ndcg_at_10": agg["ndcg_at_10"], "recall_at_10": agg["recall_at_10"],
                         "mrr": agg["mrr"]})

    # ---- storage (MB) ----
    cap_mb = cap_docs.nbytes / 1e6
    frame_mb = fe.nbytes / 1e6
    store = {"clip_caption": cap_mb, "frame_vector": frame_mb,
             "multi_vector": frame_mb, "dual_index": cap_mb + frame_mb}
    n_vec = {"clip_caption": len(cap_clip), "frame_vector": len(fcids),
             "multi_vector": len(fcids), "dual_index": len(cap_clip) + len(fcids)}

    metrics = pd.DataFrame(rows)
    lat = pd.DataFrame(lat_rows)
    metrics.to_csv(args.out / "storage_unit_metrics.csv", index=False)
    lat.to_csv(args.out / "storage_unit_latency.csv", index=False)

    # combined summary table
    summ = []
    for cond in conditions:
        r = {"condition": cond, "n_vectors": n_vec[cond], "storage_mb": round(store[cond], 2),
             "lat_p50_ms": round(float(lat[lat.condition == cond].lat_p50_ms.iloc[0]), 3),
             "lat_p95_ms": round(float(lat[lat.condition == cond].lat_p95_ms.iloc[0]), 3)}
        for tag in ["strict", "semantic"]:
            m = metrics[(metrics.condition == cond) & (metrics.qrels == tag)]
            r[f"ndcg10_{tag}"] = round(float(m.ndcg_at_10.iloc[0]), 4)
        summ.append(r)
    summ = pd.DataFrame(summ)
    summ.to_csv(args.out / "storage_unit_summary.csv", index=False)
    (args.out / "manifest.json").write_text(json.dumps({
        "dataset": args.dataset, "queries": len(qids),
        "caption_dim": int(cap_docs.shape[1]), "clip_dim": int(fe.shape[1]),
        "frame_topn": FRAME_TOPN, "max_rank": MAX_RANK,
        "caveat": "clip-caption uses bge-m3 text space; frame/multi use CLIP cross-modal space; "
                  "compared as STORAGE designs, not encoder ablation.",
    }, ensure_ascii=False, indent=2))

    print("\n=== STORAGE-UNIT SUMMARY ({}) ===".format(args.dataset))
    print(summ.to_string(index=False))
    print(f"\n[saved] {args.out}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
