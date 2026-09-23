#!/usr/bin/env python3
"""FreshEvidenceDB P2-D: CPU-only low-resource answer gate."""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


P1_DIR = Path(__file__).resolve().parent.parent / "freshevidencedb_p1"
sys.path.insert(0, str(P1_DIR))
from run_p1b_answer_failure import FactCorpus  # noqa: E402


MODEL_PATH = Path("/hdd2/huggingface_cache/hub/models--meta-llama--Llama-3.2-1B-Instruct/snapshots/9213176726f574b556790deb65791e0c5aa438b6")
SEED = 20260807
ARMS = ("current_only", "missing", "mixed_old_last", "mixed_new_last")


def make_prompt(fact, arm: str, rng: random.Random):
    if rng.random() < 0.5:
        option_a, option_b, current_letter = fact.old_answer, fact.new_answer, "B"
    else:
        option_a, option_b, current_letter = fact.new_answer, fact.old_answer, "A"
    if arm == "current_only":
        evidence = f"[source_epoch=2] {fact.doc.new_chunks[0]}"
    elif arm == "missing":
        evidence = "(no retrieved evidence)"
    elif arm == "mixed_old_last":
        evidence = f"[source_epoch=2] {fact.doc.new_chunks[0]}\n[source_epoch=1] {fact.doc.old_chunks[0]}"
    elif arm == "mixed_new_last":
        evidence = f"[source_epoch=1] {fact.doc.old_chunks[0]}\n[source_epoch=2] {fact.doc.new_chunks[0]}"
    else:
        raise ValueError(arm)
    content = (
        "Use only the retrieved evidence. If multiple sources conflict, use the answer supported by the largest source_epoch. "
        "If there is no retrieved evidence, answer U. Return exactly one letter: A, B, or U.\n\n"
        f"Question: {fact.question}\n\nRetrieved evidence:\n{evidence}\n\n"
        f"A: {option_a}\nB: {option_b}\nU: insufficient evidence\n\nAnswer:"
    )
    expected = "U" if arm == "missing" else current_letter
    return content, expected, current_letter, option_a, option_b


def parse_letter(text: str) -> str:
    match = re.search(r"(?<![A-Za-z])[ABU](?![A-Za-z])", text.upper())
    return match.group(0) if match else "INVALID"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--batch-size", type=int, default=8)
    args = parser.parse_args()
    if not MODEL_PATH.exists():
        raise FileNotFoundError(MODEL_PATH)
    torch.set_num_threads(min(16, max(1, torch.get_num_threads())))
    corpus = FactCorpus(args.manifest.resolve())
    tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, local_files_only=True)
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_PATH, local_files_only=True, torch_dtype=torch.float32, device_map=None
    )
    model.eval()

    requests = []
    for domain in sorted(corpus.facts):
        for fact in corpus.facts[domain]:
            for arm in ARMS:
                rng = random.Random(SEED + fact.fact_id * 97 + sum(map(ord, domain + arm)))
                prompt, expected, current_letter, option_a, option_b = make_prompt(fact, arm, rng)
                chat = tokenizer.apply_chat_template(
                    [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
                )
                requests.append(
                    {
                        "domain": domain, "fact_id": fact.fact_id, "arm": arm,
                        "expected_letter": expected, "current_letter": current_letter,
                        "option_a": option_a, "option_b": option_b, "prompt": chat,
                    }
                )

    rows = []
    for start in range(0, len(requests), args.batch_size):
        batch = requests[start : start + args.batch_size]
        encoded = tokenizer(
            [item["prompt"] for item in batch], return_tensors="pt", padding=True, truncation=True, max_length=2048
        )
        input_len = encoded["input_ids"].shape[1]
        with torch.inference_mode():
            generated = model.generate(
                **encoded, max_new_tokens=4, do_sample=False, pad_token_id=tokenizer.pad_token_id
            )
        outputs = tokenizer.batch_decode(generated[:, input_len:], skip_special_tokens=True)
        for item, raw in zip(batch, outputs):
            predicted = parse_letter(raw)
            rows.append(
                {
                    "domain": item["domain"], "fact_id": item["fact_id"], "arm": item["arm"],
                    "expected_letter": item["expected_letter"], "current_letter": item["current_letter"],
                    "predicted_letter": predicted, "task_correct": int(predicted == item["expected_letter"]),
                    "latest_answer_correct": int(predicted == item["current_letter"]),
                    "option_a": item["option_a"], "option_b": item["option_b"], "raw_output": raw.strip(),
                }
            )
        print(json.dumps({"completed": min(start + len(batch), len(requests)), "total": len(requests)}), flush=True)

    aggregate = {}
    for arm in ARMS:
        selected = [row for row in rows if row["arm"] == arm]
        aggregate[arm] = {
            "n": len(selected),
            "task_accuracy": sum(row["task_correct"] for row in selected) / len(selected),
            "latest_answer_accuracy": sum(row["latest_answer_correct"] for row in selected) / len(selected),
            "invalid_rate": sum(row["predicted_letter"] == "INVALID" for row in selected) / len(selected),
        }
    competence = aggregate["current_only"]["latest_answer_accuracy"] >= 0.70
    answer_gap = aggregate["current_only"]["latest_answer_accuracy"] - aggregate["missing"]["latest_answer_accuracy"]
    position_gap = abs(
        aggregate["mixed_old_last"]["latest_answer_accuracy"] - aggregate["mixed_new_last"]["latest_answer_accuracy"]
    )
    if not competence:
        t4 = "MODEL_GATE_INCONCLUSIVE"
    elif answer_gap >= 0.20:
        t4 = "MODEL_ANSWER_GATE_PASS"
    else:
        t4 = "MODEL_ANSWER_GATE_FAIL"
    gates = {
        "T4": t4,
        "competence_pass": competence,
        "current_vs_missing_gap": answer_gap,
        "mixed_position_gap": position_gap,
        "position_sensitive": position_gap > 0.15,
    }
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    with (out / "model_outputs.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    (out / "aggregate.json").write_text(
        json.dumps({"model": str(MODEL_PATH), "arms": aggregate, "gates": gates}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    lines = ["# P2-D CPU 모델 자동 보고", "", f"- T4: **{t4}**", "", "| arm | n | task accuracy | latest accuracy |", "|---|---:|---:|---:|"]
    for arm in ARMS:
        item = aggregate[arm]
        lines.append(f"| {arm} | {item['n']} | {item['task_accuracy']:.3f} | {item['latest_answer_accuracy']:.3f} |")
    lines.extend(["", f"- current−missing latest gap: {answer_gap:.3f}", f"- mixed position gap: {position_gap:.3f}"])
    (out / "AUTO_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(gates, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
