#!/usr/bin/env python3
"""P0 model pilot / F5 (partial): LLM-judge reliability vs deterministic labels.

The pilot's outcome has a programmatic ground truth (the active world's answer
entity is known exactly), so judge sensitivity/specificity can be measured
WITHOUT human labels. Human double annotation remains required for the
unsupported-claim construct and stays PENDING.

Design: stratified sample over (domain x world x arm x deterministic label),
judged by BOTH pilot models. The judge sees evidence + question + answer and
must decide whether the answer is supported by the evidence — it never sees
the reference entity.

Reported: sensitivity, specificity, accuracy, and differential misclassification
across arms (the failure mode that would bias a representation comparison).
"""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import pandas as pd

P0 = Path(__file__).resolve().parents[1]
MODELS = {
    "llama3": "/hdd2/huggingface_cache/hub/models--meta-llama--Meta-Llama-3-8B-Instruct/"
              "snapshots/8afb486c1db24fe5011ec46dfbe5b5dccdb575c2",
    "qwen25": "/hdd2/huggingface_cache/hub/models--Qwen--Qwen2.5-7B-Instruct/"
              "snapshots/a09a35458c702b33eeacc393d103063234e8bc28",
}
ARMS = ["A1_text", "A1F_flat", "A2_path"]
KEY = {"A1_text": "A1_text", "A1F_flat": "A1F_flat_triples", "A2_path": "A2_graph_path"}
PER_CELL = 20
SEED = 20260807
SYS = ("You verify whether an answer is supported by the given evidence. "
       "Reply with exactly one word: SUPPORTED or UNSUPPORTED.")


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", choices=list(MODELS), required=True)
    args = ap.parse_args()
    os.environ.setdefault("VLLM_WORKER_MULTIPROC_METHOD", "spawn")
    os.environ.setdefault("FLASHINFER_SAMPLER", "0")
    from transformers import AutoTokenizer
    from vllm import LLM, SamplingParams

    worlds = {}
    for d in ("primekg", "amazon"):
        for r in (json.loads(l) for l in open(P0 / "results" / f"worlds_{d}.jsonl")):
            worlds[r["fact_id"]] = r
    rows = []
    for m in MODELS:
        p = P0 / "results" / f"model_pilot_{m}_holdout.jsonl"
        rows += [json.loads(l) for l in open(p)]
    df = pd.DataFrame(rows)
    df = df[df.arm.isin(ARMS)].copy()

    # stratified sample: balanced on the deterministic label within each cell
    parts = []
    for _, g in df.groupby(["domain", "world", "arm", "hit_active"]):
        parts.append(g.sample(min(PER_CELL, len(g)), random_state=SEED))
    samp = pd.concat(parts, ignore_index=True)

    tok = AutoTokenizer.from_pretrained(MODELS[args.judge])
    prompts = []
    for _, r in samp.iterrows():
        w = worlds[r.fact_id]
        ev = w["renderings"][r.world][KEY[r.arm]]
        user = (f"Evidence: {ev}\nQuestion: {w['question']}\n"
                f"Answer given: {r.output}\n\nIs the answer supported by the evidence?")
        prompts.append(tok.apply_chat_template(
            [{"role": "system", "content": SYS}, {"role": "user", "content": user}],
            tokenize=False, add_generation_prompt=True))

    llm = LLM(model=MODELS[args.judge], dtype="bfloat16", max_model_len=1024,
              gpu_memory_utilization=0.85, disable_log_stats=True)
    outs = llm.generate(prompts, SamplingParams(temperature=0.0, max_tokens=8))
    samp["judge_raw"] = [o.outputs[0].text.strip() for o in outs]
    samp["judge_supported"] = samp.judge_raw.map(
        lambda t: ("unsupported" not in norm(t)) and ("supported" in norm(t)))
    samp["judge_model"] = args.judge

    tp = int(((samp.hit_active) & (samp.judge_supported)).sum())
    fn = int(((samp.hit_active) & (~samp.judge_supported)).sum())
    tn = int(((~samp.hit_active) & (~samp.judge_supported)).sum())
    fp = int(((~samp.hit_active) & (samp.judge_supported)).sum())
    per_arm = {}
    for arm, g in samp.groupby("arm"):
        gt, gf = g[g.hit_active], g[~g.hit_active]
        per_arm[arm] = {
            "sensitivity": round(float(gt.judge_supported.mean()), 4) if len(gt) else None,
            "specificity": round(float((~gf.judge_supported).mean()), 4) if len(gf) else None,
            "n": int(len(g))}
    sens = tp / (tp + fn) if tp + fn else float("nan")
    spec = tn / (tn + fp) if tn + fp else float("nan")
    sens_vals = [v["sensitivity"] for v in per_arm.values() if v["sensitivity"] is not None]
    spec_vals = [v["specificity"] for v in per_arm.values() if v["specificity"] is not None]
    res = {"judge_model": args.judge, "n_judged": int(len(samp)),
           "confusion": {"TP": tp, "FN": fn, "TN": tn, "FP": fp},
           "sensitivity": round(sens, 4), "specificity": round(spec, 4),
           "accuracy": round((tp + tn) / len(samp), 4),
           "per_arm": per_arm,
           "differential_misclassification": {
               "sens_spread_across_arms": round(max(sens_vals) - min(sens_vals), 4),
               "spec_spread_across_arms": round(max(spec_vals) - min(spec_vals), 4)},
           "prereg_thresholds": {"sens_spec_min": 0.85, "arm_spread_max": 0.05},
           "meets_prereg": bool(sens >= 0.85 and spec >= 0.85
                                and max(sens_vals) - min(sens_vals) <= 0.05
                                and max(spec_vals) - min(spec_vals) <= 0.05),
           "note": "Deterministic reference only; human double annotation still PENDING."}
    samp.to_csv(P0 / "results" / f"judge_substudy_{args.judge}.csv", index=False)
    (P0 / "results" / f"judge_substudy_{args.judge}.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
