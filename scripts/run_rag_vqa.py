#!/usr/bin/env python3
"""Controlled LLM answer layer (⭐1): Retrieval-Augmented multiple-choice VQA.

Tests the paper thesis end-to-end: the DB retrieval configuration determines
which evidence reaches a FIXED LLM, hence the answer accuracy. Exact-match gold
(MC letter) → no judge model needed.

Configs (evidence source), LLM held fixed:
  closed       : no evidence (LLM prior only)               -> lower bound
  vector_only  : dense-retrieved top-k captions (B2-style)  -> retrieval, no metadata
  prefilter    : metadata-filtered then dense top-k (B4)    -> metadata-aware retrieval
  oracle       : the target clip's own caption              -> perfect retrieval, upper bound

Usage:
  run_rag_vqa.py --model qwen --per-cat 20 --topk 3 --out <dir> [--configs ...]
"""
from __future__ import annotations
import argparse, glob, json, re, time
from pathlib import Path
import numpy as np, pandas as pd, torch

ROOT = Path(__file__).resolve().parents[2]
CAN = ROOT / "Datasets/processed/vru_accident/20260706/canonical"
EXP = ROOT / "2026_KIISE/experiments_expansion/rag_vqa"
MODELS = {
    "qwen": "/hdd2/huggingface_cache/hub/models--Qwen--Qwen2.5-7B-Instruct",
    "llama3": "/hdd2/huggingface_cache/hub/models--meta-llama--Meta-Llama-3-8B-Instruct",
}
CAT2FACET = {
    "weather and light": "weather_light", "location": "location", "road type": "road_type",
    "accident type": "accident_type", "accident reason": "accident_reason",
    "prevention method": "prevention_method",
}
# categorical facets usable as metadata filter context
FILTER_FACETS = ["weather_light", "location", "road_type", "accident_type"]


def snap(mid):
    return sorted(glob.glob(mid + "/snapshots/*"))[0]


def load_data():
    vqa = pd.read_parquet(EXP / "vqa_joined.parquet")
    meta = pd.read_parquet(CAN / "metadata.parquet")
    # clip -> {facet_name: value}
    facets = {}
    for cid, g in meta.groupby("clip_id"):
        facets[cid] = dict(zip(g["facet_name"], g["facet_value"]))
    caps = vqa.drop_duplicates("clip_id").set_index("clip_id")["caption"].to_dict()
    return vqa, facets, caps


def embed_bge(texts, batch=64):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer(str(ROOT / "Datasets/models/huggingface/BAAI--bge-m3"), device="cuda:0")
    return np.asarray(m.encode(texts, batch_size=batch, normalize_embeddings=True, show_progress_bar=False))


def build_query(item, facets):
    """Operational context query: the clip's OTHER known facets (exclude the asked one)."""
    tgt = CAT2FACET[item["category"]]
    f = facets.get(item["clip_id"], {})
    ctx = [f"{k.replace('_',' ')}: {f[k]}" for k in FILTER_FACETS if k in f and k != tgt]
    return "; ".join(ctx) if ctx else item["question"]


def retrieve(qvec, cap_ids, cap_mat, allow_ids, topk, exclude=None):
    mask = np.array([cid in allow_ids and cid != exclude for cid in cap_ids])
    if mask.sum() == 0:
        mask = np.array([cid != exclude for cid in cap_ids])
    idx = np.where(mask)[0]
    sims = cap_mat[idx] @ qvec
    order = idx[np.argsort(-sims)[:topk]]
    return [cap_ids[i] for i in order]


def make_prompt(item, evidence_caps):
    ev = ""
    if evidence_caps:
        ev = "다음은 검색된 영상 증거(caption)입니다:\n" + "\n".join(
            f"[증거 {i+1}] {c}" for i, c in enumerate(evidence_caps)) + "\n\n"
    return (f"{ev}질문: {item['question']}\n선택지: {item['options']}\n"
            f"위 증거에 근거하여 정답 보기의 알파벳(A, B, C, D) 하나만 출력하시오.\n정답:")


def parse_letter(text):
    m = re.search(r"[ABCD]", text.upper())
    return m.group(0) if m else "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen", choices=list(MODELS))
    ap.add_argument("--per-cat", type=int, default=20)
    ap.add_argument("--topk", type=int, default=3)
    ap.add_argument("--configs", nargs="+", default=["closed", "vector_only", "prefilter", "oracle"])
    ap.add_argument("--out", default=str(EXP / "results_pilot"))
    ap.add_argument("--seed", type=int, default=20260707)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    vqa, facets, caps = load_data()
    # balanced sample per category
    samp = pd.concat([g.sample(min(args.per_cat, len(g)), random_state=args.seed)
                      for _, g in vqa.groupby("category")]).reset_index(drop=True)
    print(f"[data] sampled {len(samp)} VQA items ({args.per_cat}/cat)")

    # caption corpus + embeddings
    cap_ids = list(caps.keys()); cap_texts = [caps[c] for c in cap_ids]
    t0 = time.time(); cap_mat = embed_bge(cap_texts); print(f"[embed] captions {time.time()-t0:.1f}s")
    queries = [build_query(r, facets) for _, r in samp.iterrows()]
    qmat = embed_bge(queries)

    # LLM
    from transformers import AutoModelForCausalLM, AutoTokenizer
    sp = snap(MODELS[args.model])
    t0 = time.time()
    tok = AutoTokenizer.from_pretrained(sp)
    model = AutoModelForCausalLM.from_pretrained(sp, dtype=torch.float16, device_map="cuda:0")
    model.eval(); print(f"[llm] {args.model} loaded {time.time()-t0:.1f}s")

    @torch.no_grad()
    def answer(prompt):
        msg = [{"role": "user", "content": prompt}]
        enc = tok.apply_chat_template(msg, add_generation_prompt=True, return_tensors="pt", return_dict=True)
        enc = {k: v.to("cuda:0") for k, v in enc.items()}
        o = model.generate(**enc, max_new_tokens=6, do_sample=False, pad_token_id=tok.eos_token_id)
        return parse_letter(tok.decode(o[0, enc["input_ids"].shape[1]:], skip_special_tokens=True))

    all_ids_set = set(cap_ids)
    rows = []
    t0 = time.time()
    for i, (_, item) in enumerate(samp.iterrows()):
        cid = item["clip_id"]; qvec = qmat[i]; tgt = CAT2FACET[item["category"]]
        # prefilter candidate set: clips matching this clip's context facets
        f = facets.get(cid, {})
        pre_ids = {c for c in cap_ids if all(
            facets.get(c, {}).get(k) == f.get(k) for k in FILTER_FACETS if k != tgt and k in f)}
        for cfg in args.configs:
            if cfg == "closed":
                ev = []
            elif cfg == "distractor":
                j = int(rng.integers(0, len(cap_ids)))
                while cap_ids[j] == cid:
                    j = int(rng.integers(0, len(cap_ids)))
                ev = [caps[cap_ids[j]]]
            elif cfg == "oracle":
                ev = [caps[cid]]
            elif cfg == "vector_only":
                ev = [caps[c] for c in retrieve(qvec, cap_ids, cap_mat, all_ids_set, args.topk, exclude=cid)]
            elif cfg == "prefilter":
                ev = [caps[c] for c in retrieve(qvec, cap_ids, cap_mat, pre_ids, args.topk, exclude=cid)]
            pred = answer(make_prompt(item, ev))
            rows.append({"clip_id": cid, "category": item["category"], "config": cfg,
                         "gold": item["answer"], "pred": pred, "correct": int(pred == item["answer"]),
                         "n_pre": len(pre_ids)})
        if (i + 1) % 20 == 0:
            print(f"  {i+1}/{len(samp)} ({(time.time()-t0)/(i+1):.2f}s/item)")
    df = pd.DataFrame(rows)
    df.to_parquet(out / f"rag_vqa_{args.model}.parquet")
    # summary
    acc = df.groupby("config")["correct"].mean().reindex(args.configs)
    per = df.groupby(["config", "category"])["correct"].mean().unstack(0).reindex(columns=args.configs)
    print(f"\n=== {args.model} accuracy (n={len(samp)}/config, random=0.25) ===")
    print(acc.round(4).to_string())
    print("\n--- per category ---"); print(per.round(3).to_string())
    summ = {"model": args.model, "n_per_config": int(len(samp)), "topk": args.topk,
            "accuracy": {k: round(float(v), 4) for k, v in acc.items()},
            "median_prefilter_candidates": int(df["n_pre"].median())}
    (out / f"summary_{args.model}.json").write_text(json.dumps(summ, indent=2, ensure_ascii=False))
    print("\nsaved ->", out)


if __name__ == "__main__":
    main()
