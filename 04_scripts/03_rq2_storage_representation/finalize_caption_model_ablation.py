#!/usr/bin/env python3
"""Wait for complete captions, then execute and aggregate every downstream lane."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = PROJECT_ROOT / "2026_KIISE" / "scripts"
DEFAULT_ROOT = Path("/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715")
MODELS = ("qwen25vl_7b", "qwen3vl_8b", "qwen35_9b")
DATASETS = ("522", "meva", "uca")
EXPECTED = {"522": 3000, "meva": 985, "uca": 6432}


def gpu_memory_used() -> list[int]:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        check=True, capture_output=True, text=True,
    )
    return [int(line.strip()) for line in result.stdout.splitlines() if line.strip()]


def wait_for_complete_captions(root: Path, poll_seconds: int) -> None:
    while True:
        ready = 0
        for model in MODELS:
            for dataset in DATASETS:
                cap_dir = root / model / dataset / "captions"
                error_files = [path for path in cap_dir.glob("errors_shard*.jsonl") if path.stat().st_size]
                if error_files:
                    raise RuntimeError(f"caption inference error recorded: {error_files[0]}")
                audit_path = cap_dir / "caption_output_audit.json"
                records_path = cap_dir / "caption_records.parquet"
                if not audit_path.exists() or not records_path.exists():
                    continue
                audit = json.loads(audit_path.read_text())
                if audit["actual_items"] == EXPECTED[dataset]:
                    if not audit["overall_pass"]:
                        raise RuntimeError(f"full caption audit failed: {audit_path}")
                    ready += 1
        if ready == len(MODELS) * len(DATASETS):
            print("[caption-ready] all 9 lanes passed full coverage audits", flush=True)
            return
        print(
            f"[caption-wait] {datetime.now(timezone.utc).isoformat()} ready={ready}/9",
            flush=True,
        )
        time.sleep(poll_seconds)


def wait_for_gpu(threshold_mib: int, poll_seconds: int) -> int:
    while True:
        used = gpu_memory_used()
        free = [index for index, value in enumerate(used) if value <= threshold_mib]
        if free:
            print(f"[gpu-ready] gpu={free[0]} memory.used={used} MiB", flush=True)
            return free[0]
        print(f"[gpu-wait] memory.used={used} MiB", flush=True)
        time.sleep(poll_seconds)


def run_logged(command: list[str], env: dict[str, str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[start] {log_path.name}", flush=True)
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.now(timezone.utc).isoformat()}] {' '.join(command)}\n")
        log.flush()
        result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        tail = "\n".join(log_path.read_text(encoding="utf-8").splitlines()[-40:])
        raise RuntimeError(f"downstream command failed: {log_path}\n{tail}")
    print(f"[pass] {log_path.name}", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--free-threshold-mib", type=int, default=1000)
    args = parser.parse_args()
    wait_for_complete_captions(args.root, args.poll_seconds)
    physical_gpu = wait_for_gpu(args.free_threshold_mib, args.poll_seconds)
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(physical_gpu)
    env["TOKENIZERS_PARALLELISM"] = "false"
    logs = args.root / "logs" / "downstream"
    for model in MODELS:
        for dataset in DATASETS:
            run_logged(
                [
                    sys.executable,
                    str(SCRIPTS / "run_caption_ablation_downstream.py"),
                    "--root", str(args.root),
                    "--model-key", model,
                    "--dataset", dataset,
                    "--stage", "all",
                    "--embedding-device", "cuda:0",
                    "--embedding-batch-size", "32",
                    "--overwrite",
                ],
                env,
                logs / f"{model}_{dataset}.log",
            )

    run_logged(
        [sys.executable, str(SCRIPTS / "analyze_caption_model_ablation.py"), "--root", str(args.root)],
        env,
        logs / "aggregate_retrieval.log",
    )
    run_logged(
        [sys.executable, str(SCRIPTS / "analyze_caption_content_diagnostics.py"), "--root", str(args.root)],
        env,
        logs / "aggregate_caption_diagnostics.log",
    )
    print("[complete] caption model ablation finalized", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
