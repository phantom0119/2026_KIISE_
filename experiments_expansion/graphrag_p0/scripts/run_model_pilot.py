#!/usr/bin/env python3
"""P0 model pilot / gates F3, F4 (and inputs for real F6).

Arms per canonical fact (v1.1 amendment):
  A0  closed-book, 3 paraphrases x 3 samples  -> parametric knowledge probability
  A1 / A1F / A2 in ORIGINAL world             -> oracle evidence, 3 representations
  A1 / A1F / A2 in COUNTERFACTUAL world       -> memory-vs-evidence conflict

Scoring is DETERMINISTIC (no LLM judge in this stage):
  hit_active   : the active world's answer string appears in the output
  hit_original : the ORIGINAL answer appears (in CF arms = memory override)
  abstain      : the output declares UNKNOWN

Splits: dev = first DEV_N facts of the fixed-seed file order, holdout = rest.
Prompt wording may be adjusted at most ONCE on dev; the holdout is measured once.

Run (one model at a time, single GPU):
  CUDA_VISIBLE_DEVICES=0 python run_model_pilot.py --model llama3 --split dev
"""
from __future__ import annotations

import argparse
import json
import os
import re
import time
from pathlib import Path

P0 = Path(__file__).resolve().parents[1]
DEV_N = 60
MODELS = {
    "llama3": "/hdd2/huggingface_cache/hub/models--meta-llama--Meta-Llama-3-8B-Instruct/"
              "snapshots/8afb486c1db24fe5011ec46dfbe5b5dccdb575c2",
    "qwen25": "/hdd2/huggingface_cache/hub/models--Qwen--Qwen2.5-7B-Instruct/"
              "snapshots/a09a35458c702b33eeacc393d103063234e8bc28",
}
PARAPHRASE = {
    "primekg_clinical": [
        "Which disease is associated with the protein that the drug {h} targets?",
        "The drug {h} targets a protein. Which disease is that protein associated with?",
        "Name the disease linked to the protein that is targeted by the drug {h}.",
    ],
    "stark_amazon_ecommerce": [
        "Which other product is made by the brand of '{h}'?",
        "The product '{h}' has a brand. Name another product made by that same brand.",
        "Identify a different product manufactured by the brand that makes '{h}'.",
    ],
}
SYS_EVID = ("You answer questions using ONLY the evidence provided. "
            "Reply with the exact name from the evidence and nothing else. "
            "If the evidence does not contain the answer, reply exactly: UNKNOWN")
SYS_CB = ("You answer questions from your own knowledge. "
          "Reply with the exact name and nothing else. "
          "If you do not know, reply exactly: UNKNOWN")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def build_jobs(rows: list[dict]) -> list[dict]:
    jobs = []
    for r in rows:
        dom, h = r["domain"], r["head"]
        for pi, tmpl in enumerate(PARAPHRASE[dom]):
            q = tmpl.format(h=h)
            for si in range(3):
                jobs.append({"fact_id": r["fact_id"], "domain": dom, "arm": "A0_closed",
                             "world": "original", "paraphrase": pi, "sample": si,
                             "sys": SYS_CB, "user": f"Question: {q}\nAnswer:",
                             "temp": 0.7, "seed": 1000 + si})
        for world in ("original", "counterfactual"):
            ren = r["renderings"][world]
            for arm, key in (("A1_text", "A1_text"), ("A1F_flat", "A1F_flat_triples"),
                             ("A2_path", "A2_graph_path")):
                jobs.append({"fact_id": r["fact_id"], "domain": dom, "arm": arm,
                             "world": world, "paraphrase": 0, "sample": 0,
                             "sys": SYS_EVID,
                             "user": f"Evidence: {ren[key]}\nQuestion: {r['question']}\nAnswer:",
                             "temp": 0.0, "seed": 0})
    return jobs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=list(MODELS), required=True)
    ap.add_argument("--split", choices=["dev", "holdout"], required=True)
    ap.add_argument("--domains", nargs="+", default=["primekg", "amazon"])
    ap.add_argument("--limit", type=int, default=None, help="smoke-test cap on facts")
    args = ap.parse_args()
    os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
    os.environ.setdefault("FLASHINFER_SAMPLER", "0")
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    rows = []
    for d in args.domains:
        rs = [json.loads(l) for l in open(P0 / "results" / f"worlds_{d}.jsonl")]
        rs = rs[:DEV_N] if args.split == "dev" else rs[DEV_N:]
        if args.limit:
            rs = rs[: args.limit]
        rows += rs
    answers = {r["fact_id"]: {"original": r["tail_original"],
                              "counterfactual": r["tail_counterfactual"]} for r in rows}
    jobs = build_jobs(rows)
    print(f"[{args.model}/{args.split}] facts={len(rows)} jobs={len(jobs)}", flush=True)

    tok = AutoTokenizer.from_pretrained(MODELS[args.model])
    prompts = [tok.apply_chat_template(
        [{"role": "system", "content": j["sys"]}, {"role": "user", "content": j["user"]}],
        tokenize=False, add_generation_prompt=True) for j in jobs]

    t0 = time.time()
    llm = LLM(model=MODELS[args.model], dtype="bfloat16", max_model_len=1024,
              gpu_memory_utilization=0.85, enforce_eager=False, disable_log_stats=True)
    greedy_idx = [i for i, j in enumerate(jobs) if j["temp"] == 0.0]
    samp_idx = [i for i, j in enumerate(jobs) if j["temp"] > 0.0]
    outs: dict[int, str] = {}
    if greedy_idx:
        sp = SamplingParams(temperature=0.0, max_tokens=48)
        for i, o in zip(greedy_idx, llm.generate([prompts[i] for i in greedy_idx], sp)):
            outs[i] = o.outputs[0].text.strip()
    for si in sorted({j["seed"] for j in jobs if j["temp"] > 0.0}):
        idx = [i for i in samp_idx if jobs[i]["seed"] == si]
        sp = SamplingParams(temperature=0.7, top_p=0.95, max_tokens=48, seed=si)
        for i, o in zip(idx, llm.generate([prompts[i] for i in idx], sp)):
            outs[i] = o.outputs[0].text.strip()
    gen_s = time.time() - t0

    recs = []
    for i, j in enumerate(jobs):
        text = outs.get(i, "")
        n = norm(text)
        a = answers[j["fact_id"]]
        active = a[j["world"]]
        recs.append({**{k: j[k] for k in ("fact_id", "domain", "arm", "world",
                                          "paraphrase", "sample")},
                     "model": args.model, "split": args.split, "output": text,
                     "hit_active": norm(active) in n,
                     "hit_original": norm(a["original"]) in n,
                     "hit_cf": norm(a["counterfactual"]) in n,
                     "abstain": "unknown" in n})
    outp = P0 / "results" / f"model_pilot_{args.model}_{args.split}.jsonl"
    with open(outp, "w") as fh:
        for r in recs:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    meta = {"model": args.model, "split": args.split, "n_facts": len(rows),
            "n_jobs": len(jobs), "gen_wall_s": round(gen_s, 1),
            "total_wall_s": round(time.time() - t0, 1)}
    (P0 / "results" / f"model_pilot_{args.model}_{args.split}_meta.json").write_text(
        json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
