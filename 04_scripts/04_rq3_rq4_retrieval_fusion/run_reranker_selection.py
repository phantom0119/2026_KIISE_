#!/usr/bin/env python3
"""⭐3 Evidence selection with a learned cross-encoder reranker (bge-reranker-v2-m3).

Extends RQ5: beyond weighted RRF, does a cross-encoder reranker improve rank-1 /
nDCG@10 over dense vector-only retrieval? Reranks the dense top-N candidates and
re-scores clip-level metrics against qrels.
"""
from __future__ import annotations
import argparse, json, glob
from pathlib import Path
import numpy as np, pandas as pd, torch

ROOT = Path(__file__).resolve().parents[3]
RERANKER = "/hdd2/huggingface_cache/hub/models--BAAI--bge-reranker-v2-m3"


def load(ds_root: Path, emb_root: Path):
    docs = pd.read_parquet(ds_root / "canonical/documents.parquet")[["doc_id", "clip_id", "text"]]
    q = [json.loads(l) for l in (ds_root / "canonical/queries.jsonl").read_text().splitlines()]
    qdf = pd.DataFrame(q)
    qrels = pd.read_csv(ds_root / "canonical/qrels.tsv", sep="\t")
    dcol = [c for c in qrels.columns]
    demb = np.load(emb_root / "document_embeddings.npy")
    qemb = np.load(emb_root / "query_embeddings.npy")
    didx = pd.read_parquet(emb_root / "document_index.parquet")
    qidx = pd.read_parquet(emb_root / "query_index.parquet")
    return docs, qdf, qrels, demb, qemb, didx, qidx


def ndcg_at_k(rel, k=10):
    rel = np.asarray(rel[:k], float)
    if rel.sum() == 0:
        return 0.0
    dcg = (rel / np.log2(np.arange(2, len(rel) + 2))).sum()
    ideal = np.sort(rel)[::-1]
    idcg = (ideal / np.log2(np.arange(2, len(ideal) + 2))).sum()
    return float(dcg / idcg) if idcg > 0 else 0.0


def clip_metrics(ranked_clips, rel_clips, ks=(1, 10, 20)):
    rel = [1 if c in rel_clips else 0 for c in ranked_clips]
    out = {}
    for k in ks:
        out[f"recall_at_{k}"] = (sum(rel[:k]) / len(rel_clips)) if rel_clips else 0.0
        out[f"hit_at_{k}"] = 1.0 if any(rel[:k]) else 0.0
    out["ndcg_at_10"] = ndcg_at_k(rel, 10)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="vru_accident")
    ap.add_argument("--emb", default="bge-m3")
    ap.add_argument("--topn", type=int, default=50)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    ds_root = ROOT / f"Datasets/processed/{args.dataset}/20260706"
    emb_root = ds_root / f"embeddings/{args.emb}"
    out = Path(args.out or ROOT / "2026_KIISE/experiments_expansion/reranker" / args.dataset)
    out.mkdir(parents=True, exist_ok=True)

    docs, qdf, qrels, demb, qemb, didx, qidx = load(ds_root, emb_root)
    doc_clip = didx["clip_id"].values if "clip_id" in didx else docs["clip_id"].values
    doc_text = didx.merge(docs, on="doc_id", how="left")["text"].values if "doc_id" in didx else docs["text"].values
    # qrels: relevant clips per query (target_type == 'clip', target_id = clip id)
    qc = qrels[qrels["target_type"] == "clip"] if "target_type" in qrels else qrels
    rel_by_q = qc.groupby("query_id")["target_id"].apply(set).to_dict()
    qids = qidx["query_id"].values

    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    sp = sorted(glob.glob(RERANKER + "/snapshots/*"))[0]
    tok = AutoTokenizer.from_pretrained(sp)
    rr = AutoModelForSequenceClassification.from_pretrained(sp, dtype=torch.float16).to(args.device).eval()

    @torch.no_grad()
    def rerank_scores(query, texts):
        pairs = [[query, t if isinstance(t, str) else ""] for t in texts]
        enc = tok(pairs, padding=True, truncation=True, max_length=512, return_tensors="pt").to(args.device)
        return rr(**enc).logits.view(-1).float().cpu().numpy()

    dnorm = demb / (np.linalg.norm(demb, axis=1, keepdims=True) + 1e-9)
    rows = []
    for i, qid in enumerate(qids):
        rel = rel_by_q.get(qid, set())
        if not rel:
            continue
        qtext = str(qdf[qdf.query_id == qid]["query_text"].iloc[0]) if (qdf.query_id == qid).any() else ""
        sims = dnorm @ (qemb[i] / (np.linalg.norm(qemb[i]) + 1e-9))
        top = np.argsort(-sims)[:args.topn]
        # base dense ranking -> clip order (first occurrence)
        def to_clips(order):
            seen, cl = set(), []
            for j in order:
                c = doc_clip[j]
                if c not in seen:
                    seen.add(c); cl.append(c)
            return cl
        base_clips = to_clips(top)
        # cross-encoder rerank of the top-N docs
        rr_scores = rerank_scores(qtext, [doc_text[j] for j in top])
        rr_order = top[np.argsort(-rr_scores)]
        rr_clips = to_clips(rr_order)
        mb = clip_metrics(base_clips, rel); mr = clip_metrics(rr_clips, rel)
        rows.append({"query_id": qid, **{f"base_{k}": v for k, v in mb.items()},
                     **{f"rerank_{k}": v for k, v in mr.items()}})
        if (i + 1) % 60 == 0:
            print(f"  {i+1}/{len(qids)}")
    df = pd.DataFrame(rows)
    df.to_parquet(out / f"reranker_{args.emb}.parquet")
    summ = {}
    for m in ["hit_at_1", "recall_at_10", "ndcg_at_10"]:
        summ[f"base_{m}"] = round(float(df[f"base_{m}"].mean()), 4)
        summ[f"rerank_{m}"] = round(float(df[f"rerank_{m}"].mean()), 4)
        summ[f"delta_{m}"] = round(summ[f"rerank_{m}"] - summ[f"base_{m}"], 4)
    (out / f"summary_{args.emb}.json").write_text(json.dumps(summ, indent=2))
    print(f"\n=== {args.dataset} cross-encoder rerank vs dense (n={len(df)}) ===")
    for m in ["hit_at_1", "recall_at_10", "ndcg_at_10"]:
        print(f"  {m}: base {summ[f'base_{m}']} -> rerank {summ[f'rerank_{m}']}  (Δ {summ[f'delta_{m}']:+.4f})")
    print("saved ->", out)


if __name__ == "__main__":
    main()
