#!/usr/bin/env python3
"""Run one frozen S4 three-class perception-gate category with InternVL3.

Use one process per category/GPU. Results are resumable JSONL and are converted
to parquet only after all 540 category-condition rows complete.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VER = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
DEFAULT_GATE = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets"
    / "20260723_controlled_supplement" / "s4_mcq_gate"
)
MODEL_ROOT = Path("/hdd2/huggingface_cache/hub/models--OpenGVLab--InternVL3-8B-hf")
VALID_CATEGORIES = ("bus_count", "bike_count")


def snapshot_dir() -> Path:
    snapshots = MODEL_ROOT / "snapshots"
    if snapshots.exists():
        values = sorted(path for path in snapshots.iterdir() if path.is_dir())
        if len(values) != 1:
            raise ValueError(f"expected one InternVL3 snapshot, found {values}")
        return values[0]
    return MODEL_ROOT


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def load_done(path: Path) -> dict[tuple[str, str, str], dict]:
    rows: dict[tuple[str, str, str], dict] = {}
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            row = json.loads(line)
            rows[(row["item_id"], row["category"], row["condition"])] = row
        except Exception:
            continue
    return rows


def resize_to_pixel_budget(image: Image.Image, max_pixels: int) -> Image.Image:
    width, height = image.size
    if width * height <= max_pixels:
        return image
    scale = math.sqrt(max_pixels / (width * height))
    size = (max(1, int(width * scale)), max(1, int(height * scale)))
    return image.resize(size, Image.Resampling.LANCZOS)


def parse_choice(text: str) -> str | None:
    match = re.search(r"(?<![A-Za-z])([ABC])(?![A-Za-z])", text.strip(), flags=re.IGNORECASE)
    return match.group(1).upper() if match else None


def macro_accuracy(frame: pd.DataFrame) -> float:
    class_values = frame.groupby("gold_class")["correct"].mean()
    return float(class_values.mean()) if len(class_values) == 3 else float("nan")


def cluster_bootstrap(
    frame: pd.DataFrame, condition: str, draws: int, seed: int
) -> tuple[float, float]:
    subset = frame[frame["condition"] == condition]
    clusters = sorted(subset["source_intersection_id"].astype(str).unique())
    by_cluster = {cluster: subset[subset["source_intersection_id"].astype(str) == cluster] for cluster in clusters}
    rng = np.random.default_rng(seed)
    values: list[float] = []
    for _ in range(draws):
        sampled = rng.choice(clusters, len(clusters), replace=True)
        boot = pd.concat([by_cluster[value] for value in sampled], ignore_index=True)
        value = macro_accuracy(boot)
        if np.isfinite(value):
            values.append(value)
    return float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))


def paired_cluster_bootstrap(
    frame: pd.DataFrame, draws: int, seed: int
) -> tuple[float, float]:
    pivot = frame.pivot(
        index=["item_id", "source_intersection_id"],
        columns="condition",
        values="correct",
    ).reset_index()
    clusters = sorted(pivot["source_intersection_id"].astype(str).unique())
    by_cluster = {
        cluster: pivot[pivot["source_intersection_id"].astype(str) == cluster] for cluster in clusters
    }
    rng = np.random.default_rng(seed)
    values = np.empty(draws)
    for draw in range(draws):
        sampled = rng.choice(clusters, len(clusters), replace=True)
        boot = pd.concat([by_cluster[value] for value in sampled], ignore_index=True)
        values[draw] = float((boot["oracle"] - boot["distractor"]).mean())
    return float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))


def analyze(frame: pd.DataFrame, category: str, draws: int, seed: int) -> dict:
    condition_results: dict[str, dict] = {}
    for condition in ("closed", "distractor", "oracle"):
        subset = frame[frame["condition"] == condition].copy()
        subset["pred_class_report"] = subset["pred_class"].fillna("INVALID")
        lo, hi = cluster_bootstrap(frame, condition, draws, seed)
        condition_results[condition] = {
            "rows": int(len(subset)),
            "valid_parse": int(subset["pred_class"].notna().sum()),
            "accuracy": float(subset["correct"].mean()),
            "macro_accuracy": macro_accuracy(subset),
            "intersection_cluster_bootstrap_ci": [lo, hi],
            "prediction_share": (
                subset["pred_class_report"].value_counts(normalize=True).to_dict()
            ),
            "confusion": pd.crosstab(
                subset["gold_class"], subset["pred_class_report"], dropna=False
            ).to_dict(),
        }
    oracle = frame[frame["condition"] == "oracle"]
    pivot = frame.pivot(index="item_id", columns="condition", values="correct")
    oracle_minus_distractor = float((pivot["oracle"] - pivot["distractor"]).mean())
    diff_lo, diff_hi = paired_cluster_bootstrap(frame, draws, seed + 1)
    max_share = float(oracle["pred_class"].fillna("INVALID").value_counts(normalize=True).max())
    gates = {
        "oracle_macro_ci_lower_gt_chance": bool(
            condition_results["oracle"]["intersection_cluster_bootstrap_ci"][0] > 1 / 3
        ),
        "oracle_minus_distractor_at_least_10pp": bool(oracle_minus_distractor >= 0.10),
        "oracle_max_prediction_share_at_most_70pct": bool(max_share <= 0.70),
    }
    gates["all_pass"] = all(gates.values())
    return {
        "category": category,
        "conditions": condition_results,
        "oracle_minus_distractor": oracle_minus_distractor,
        "oracle_minus_distractor_cluster_bootstrap_ci": [diff_lo, diff_hi],
        "gates": gates,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--category", choices=VALID_CATEGORIES, required=True)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--gate-dir", type=Path, default=DEFAULT_GATE)
    parser.add_argument("--max-pixels", type=int, default=200704)
    parser.add_argument("--max-new-tokens", type=int, default=4)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260723)
    args = parser.parse_args()

    plan_path = args.gate_dir / "gate_plan.parquet"
    plan = pd.read_parquet(plan_path)
    plan = plan[plan["category"] == args.category].copy()
    if len(plan) != 540:
        raise ValueError(f"expected 540 rows for {args.category}, found {len(plan)}")
    output_jsonl = args.gate_dir / f"gate_results_{args.category}.jsonl"
    done = load_done(output_jsonl)
    todo = plan[
        ~plan.apply(
            lambda row: (row["item_id"], row["category"], row["condition"]) in done,
            axis=1,
        )
    ]
    print(f"[{args.category}] total={len(plan)} done={len(done)} todo={len(todo)}", flush=True)

    if len(todo):
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor

        snapshot = snapshot_dir()
        started = time.time()
        model = AutoModelForImageTextToText.from_pretrained(
            str(snapshot), torch_dtype=torch.float16, device_map=args.device
        ).eval()
        processor = AutoProcessor.from_pretrained(str(snapshot))
        print(f"[model] loaded {snapshot.name} in {time.time() - started:.1f}s", flush=True)

        def ask(row: pd.Series) -> tuple[str, str | None]:
            if row["condition"] == "closed":
                messages = [{"role": "user", "content": [{"type": "text", "text": row["prompt"]}]}]
                prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
                inputs = processor(text=prompt, return_tensors="pt").to(args.device)
            else:
                image_path = VER / str(row["evidence_relpath"])
                with Image.open(image_path) as source:
                    image = resize_to_pixel_budget(source.convert("RGB"), args.max_pixels)
                messages = [
                    {
                        "role": "user",
                        "content": [{"type": "image"}, {"type": "text", "text": row["prompt"]}],
                    }
                ]
                prompt = processor.apply_chat_template(messages, add_generation_prompt=True)
                inputs = processor(images=[image], text=prompt, return_tensors="pt").to(args.device)
                if "pixel_values" in inputs:
                    inputs["pixel_values"] = inputs["pixel_values"].to(torch.float16)
            with torch.no_grad():
                generated = model.generate(
                    **inputs, max_new_tokens=args.max_new_tokens, do_sample=False
                )
            raw = processor.batch_decode(
                generated[:, inputs["input_ids"].shape[1]:], skip_special_tokens=True
            )[0].strip()
            return raw, parse_choice(raw)

        started = time.time()
        with output_jsonl.open("a", encoding="utf-8") as stream:
            for index, (_, row) in enumerate(todo.iterrows(), start=1):
                raw, choice = ask(row)
                option_map = json.loads(row["option_map"])
                predicted_class = option_map.get(choice) if choice is not None else None
                output = {
                    **row.to_dict(),
                    "raw_output": raw,
                    "parsed_choice": choice,
                    "pred_class": predicted_class,
                    "correct": int(predicted_class == row["gold_class"]),
                }
                stream.write(json.dumps(output, ensure_ascii=False, default=str) + "\n")
                stream.flush()
                if index % 30 == 0:
                    rate = index / (time.time() - started)
                    print(
                        f"  {index}/{len(todo)} {rate:.2f} calls/s "
                        f"ETA={(len(todo) - index) / max(rate, 1e-9) / 60:.1f} min",
                        flush=True,
                    )

    completed = pd.DataFrame(load_done(output_jsonl).values())
    completed = completed[completed["category"] == args.category]
    if len(completed) != len(plan):
        print(f"[incomplete] {len(completed)}/{len(plan)}", flush=True)
        return 3
    summary = analyze(completed, args.category, args.bootstrap, args.seed)
    result_path = args.gate_dir / f"gate_results_{args.category}.parquet"
    completed.to_parquet(result_path, index=False)
    summary_path = args.gate_dir / f"gate_summary_{args.category}.json"
    summary_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manifest = {
        "script": Path(__file__).name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "category": args.category,
        "model_snapshot": str(snapshot_dir()),
        "plan_sha256": sha256_file(plan_path),
        "parameters": {
            "device": args.device,
            "max_pixels": args.max_pixels,
            "resize": "LANCZOS preserving aspect ratio when area exceeds max_pixels",
            "max_new_tokens": args.max_new_tokens,
            "decoding": "greedy",
            "bootstrap": args.bootstrap,
            "seed": args.seed,
        },
    }
    (args.gate_dir / f"gate_run_manifest_{args.category}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2), flush=True)
    return 0 if summary["gates"]["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
