#!/usr/bin/env python3
"""Audit coverage and generation health for one caption-ablation output."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_ROOT = Path("/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715")
LEAK_TOKENS = {
    "522": ("sig_has_", "veh_density_bin", "ped_density_bin", "any_parked", "max_objects"),
    "meva": ("person_", "vehicle_", "hand_interacts", "act__", "cnt__", "facet_"),
    "uca": (
        "video_class", "video_duration_bin", "event_position_bin", "_x264",
        "normal_videos", "roadaccidents",
    ),
}


def repeated_ngram_ratio(text: str, n: int = 4) -> float:
    tokens = re.findall(r"[a-z0-9']+", text.lower())
    grams = [tuple(tokens[i : i + n]) for i in range(max(0, len(tokens) - n + 1))]
    if not grams:
        return 0.0
    return 1.0 - len(set(grams)) / len(grams)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--model-key", required=True)
    parser.add_argument("--dataset", required=True, choices=["522", "meva", "uca"])
    parser.add_argument("--allow-partial", action="store_true")
    parser.add_argument("--max-new-tokens", type=int, default=110)
    args = parser.parse_args()

    expected = pd.read_parquet(args.root / "inputs" / f"{args.dataset}_items.parquet")
    cap_dir = args.root / args.model_key / args.dataset / "captions"
    records = pd.read_parquet(cap_dir / "caption_records.parquet")
    texts = records["caption"].fillna("").astype(str)
    ids = set(records["item_id"])
    expected_ids = set(expected["item_id"])
    missing = sorted(expected_ids - ids)
    extra = sorted(ids - expected_ids)
    machine_pattern = "|".join(re.escape(value) for value in LEAK_TOKENS[args.dataset])
    leak_mask = texts.str.contains(machine_pattern, case=False, regex=True)
    prompt = str(expected["prompt"].iloc[0]).strip().lower()
    word_counts = texts.map(lambda text: len(re.findall(r"[A-Za-z0-9']+", text)))
    repeated = texts.map(repeated_ngram_ratio)
    output_tokens = pd.to_numeric(records["output_tokens"], errors="coerce")
    elapsed = pd.to_numeric(records["elapsed_ms"], errors="coerce")

    checks = {
        "unique_item_ids": bool(records["item_id"].is_unique),
        "no_extra_items": not extra,
        "complete_coverage": not missing,
        "no_blank_captions": bool(~texts.str.strip().eq("").any()),
        "no_machine_label_tokens": bool(~leak_mask.any()),
        "no_exact_prompt_echo": bool(~texts.str.lower().str.contains(re.escape(prompt), regex=True).any()),
        "no_extreme_repetition": bool((repeated < 0.35).all()),
        "no_token_limit_hits": bool(~(output_tokens >= args.max_new_tokens).fillna(False).any()),
    }
    # Hitting the shared decoding budget is a model outcome, not a corpus-integrity
    # failure. Keep it visible as a quality advisory so a verbose model is not
    # silently favored by raising its token budget or excluded before retrieval.
    integrity_checks = [key for key in checks if key != "no_token_limit_hits"]
    if args.allow_partial:
        integrity_checks.remove("complete_coverage")
    integrity_pass = all(checks[key] for key in integrity_checks)
    quality_advisory_pass = checks["no_token_limit_hits"]
    report = {
        "model_key": args.model_key,
        "dataset": args.dataset,
        "expected_items": int(len(expected)),
        "actual_items": int(len(records)),
        "missing_items": len(missing),
        "extra_items": len(extra),
        "checks": checks,
        "integrity_checks": integrity_checks,
        "integrity_pass": integrity_pass,
        "quality_advisory_checks": ["no_token_limit_hits"],
        "quality_advisory_pass": quality_advisory_pass,
        # Backward-compatible field consumed by the lane orchestrator/finalizer.
        "overall_pass": integrity_pass,
        "caption_stats": {
            "word_count_mean": round(float(word_counts.mean()), 3),
            "word_count_p50": round(float(word_counts.median()), 3),
            "word_count_p95": round(float(word_counts.quantile(0.95)), 3),
            "exact_duplicate_rate": round(float(texts.duplicated().mean()), 6),
            "machine_leak_count": int(leak_mask.sum()),
            "token_limit_hit_count": int((output_tokens >= args.max_new_tokens).fillna(False).sum()),
            "latency_ms_mean": None if elapsed.notna().sum() == 0 else round(float(elapsed.mean()), 3),
            "latency_ms_p50": None if elapsed.notna().sum() == 0 else round(float(elapsed.median()), 3),
            "latency_ms_p95": None if elapsed.notna().sum() == 0 else round(float(elapsed.quantile(0.95)), 3),
        },
        "examples": {
            "missing": missing[:5],
            "extra": extra[:5],
            "machine_leaks": records.loc[leak_mask, "item_id"].head().tolist(),
        },
    }
    (cap_dir / "caption_output_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if integrity_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
