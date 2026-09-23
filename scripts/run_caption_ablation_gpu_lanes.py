#!/usr/bin/env python3
"""Wait for the first free GPU, then run resumable caption-model lanes safely."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT_ROOT / "2026_KIISE" / "scripts" / "run_caption_model_ablation.py"
AUDIT = PROJECT_ROOT / "2026_KIISE" / "scripts" / "audit_caption_ablation_output.py"
DEFAULT_ROOT = Path("/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715")
MODELS = ("qwen3vl_8b", "qwen35_9b")
DATASETS = ("522", "meva", "uca")
EXPECTED = {"522": 3000, "meva": 985, "uca": 6432}


def gpu_memory_used() -> list[int]:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [int(line.strip()) for line in result.stdout.splitlines() if line.strip()]


def wait_for_gpu(threshold_mib: int, poll_seconds: int, physical_gpu: int | None = None) -> int:
    while True:
        used = gpu_memory_used()
        candidates = range(len(used)) if physical_gpu is None else [physical_gpu]
        free = [index for index in candidates if used[index] <= threshold_mib]
        if free:
            print(f"[gpu-ready] gpu={free[0]} memory.used={used} MiB", flush=True)
            return free[0]
        print(
            f"[gpu-wait] {datetime.now(timezone.utc).isoformat()} memory.used={used[:2]} MiB",
            flush=True,
        )
        time.sleep(poll_seconds)


def run_logged(command: list[str], env: dict[str, str], log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[start] {log_path.name}", flush=True)
    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n[{datetime.now(timezone.utc).isoformat()}] {' '.join(command)}\n")
        log.flush()
        result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        tail = "\n".join(log_path.read_text(encoding="utf-8").splitlines()[-30:])
        raise RuntimeError(f"command failed ({result.returncode}): {log_path}\n{tail}")
    print(f"[pass] {log_path.name}", flush=True)


def command_base(root: Path, model: str, dataset: str) -> list[str]:
    return [
        sys.executable,
        str(SCRIPT),
        "--output-root",
        str(root),
        "--input-root",
        str(root / "inputs"),
        "--model-key",
        model,
        "--dataset",
        dataset,
        "--device",
        "cuda:0",
    ]


def generated_rows(root: Path, model: str, dataset: str) -> int:
    caption_root = root / model / dataset / "captions"
    rows = 0
    for path in caption_root.glob("captions_shard*.jsonl"):
        with path.open("r", encoding="utf-8") as handle:
            rows += sum(1 for line in handle if line.strip())
    return rows


def full_lane_ready(root: Path, model: str, dataset: str) -> bool:
    audit_path = root / model / dataset / "captions" / "caption_output_audit.json"
    if not audit_path.is_file():
        return False
    import json

    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    return bool(audit.get("overall_pass")) and audit.get("actual_items") == EXPECTED[dataset]


def run_lane(root: Path, model: str, physical_gpu: int, smoke_items: int) -> None:
    env = os.environ.copy()
    env["CUDA_VISIBLE_DEVICES"] = str(physical_gpu)
    env["TOKENIZERS_PARALLELISM"] = "false"
    logs = root / "logs" / model

    for dataset in DATASETS:
        if full_lane_ready(root, model, dataset):
            print(f"[skip] {model}/{dataset} full lane already passed", flush=True)
            continue
        if generated_rows(root, model, dataset) > smoke_items:
            print(f"[skip] {model}/{dataset} smoke already superseded by resumable full output", flush=True)
            continue
        base = command_base(root, model, dataset)
        run_logged(
            base + ["--limit", str(smoke_items), "--log-every", "1"],
            env,
            logs / f"{dataset}_smoke_generate.log",
        )
        run_logged(
            base + ["--limit", str(smoke_items), "--merge-only"],
            env,
            logs / f"{dataset}_smoke_merge.log",
        )
        run_logged(
            [
                sys.executable,
                str(AUDIT),
                "--root",
                str(root),
                "--model-key",
                model,
                "--dataset",
                dataset,
                "--allow-partial",
            ],
            env,
            logs / f"{dataset}_smoke_audit.log",
        )

    for dataset in DATASETS:
        if full_lane_ready(root, model, dataset):
            print(f"[skip] {model}/{dataset} full lane already passed", flush=True)
            continue
        base = command_base(root, model, dataset)
        run_logged(base, env, logs / f"{dataset}_full_generate.log")
        run_logged(base + ["--merge-only"], env, logs / f"{dataset}_full_merge.log")
        run_logged(
            [
                sys.executable,
                str(AUDIT),
                "--root",
                str(root),
                "--model-key",
                model,
                "--dataset",
                dataset,
            ],
            env,
            logs / f"{dataset}_full_audit.log",
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--free-threshold-mib", type=int, default=1000)
    parser.add_argument("--poll-seconds", type=int, default=60)
    parser.add_argument("--smoke-items", type=int, default=2)
    parser.add_argument("--physical-gpu", type=int, default=None)
    parser.add_argument("--models", nargs="+", choices=MODELS, default=list(MODELS))
    args = parser.parse_args()
    gpu = wait_for_gpu(args.free_threshold_mib, args.poll_seconds, args.physical_gpu)
    for model in args.models:
        run_lane(args.root, model, gpu, args.smoke_items)
    print("[complete] all caption-model lanes passed", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
