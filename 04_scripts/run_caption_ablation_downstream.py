#!/usr/bin/env python3
"""Run canonicalization, BGE-M3 embedding, retrieval, and dual-qrels scoring."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = PROJECT_ROOT / "2026_KIISE" / "scripts"
DEFAULT_ROOT = Path("/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715")
SOURCE_ROOTS = {
    "522": PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710",
    "meva": PROJECT_ROOT / "Datasets" / "processed" / "meva_kf1" / "20260713",
    "uca": PROJECT_ROOT / "Datasets" / "processed" / "uca_anchor" / "20260712",
}


def run(command: list[str]) -> None:
    print("[run] " + " ".join(command), flush=True)
    subprocess.run(command, check=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--model-key", required=True)
    parser.add_argument("--dataset", required=True, choices=["522", "meva", "uca"])
    parser.add_argument("--stage", choices=["canonical", "embed", "retrieve", "evaluate", "all"], default="all")
    parser.add_argument("--embedding-device", default="cpu")
    parser.add_argument("--embedding-batch-size", type=int, default=16)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    python = sys.executable
    lane = args.root / args.model_key / args.dataset
    captions = lane / "captions" / "documents.parquet"
    canonical = lane / "canonical"
    embeddings = lane / "embeddings" / "bge-m3"
    results = lane / "results" / "b0_b5"
    source = SOURCE_ROOTS[args.dataset]
    stages = ["canonical", "embed", "retrieve", "evaluate"] if args.stage == "all" else [args.stage]

    if "canonical" in stages:
        audit_path = lane / "captions" / "caption_output_audit.json"
        if not audit_path.exists() or not json.loads(audit_path.read_text())["overall_pass"]:
            raise RuntimeError(f"caption audit missing or failed: {audit_path}")
        if args.dataset == "522":
            command = [python, str(SCRIPTS / "build_intersection_trisource_canonical.py"),
                       "--expanded", "--ver", str(source), "--captions-path", str(captions),
                       "--out-dir", str(canonical)]
        elif args.dataset == "meva":
            command = [python, str(SCRIPTS / "build_meva_trisource_canonical.py"),
                       "--ver", source.name, "--captions-path", str(captions),
                       "--out-dir", str(canonical)]
        else:
            command = [python, str(SCRIPTS / "build_uca_workload.py"), "--root", str(source),
                       "--captions-path", str(captions), "--out-dir", str(canonical)]
        run(command)

    if "embed" in stages:
        command = [python, str(SCRIPTS / "build_text_embeddings.py"),
                   "--canonical-root", str(canonical), "--output-dir", str(embeddings),
                   "--device", args.embedding_device, "--batch-size", str(args.embedding_batch_size)]
        if args.overwrite:
            command.append("--overwrite")
        run(command)

    if "retrieve" in stages:
        command = [python, str(SCRIPTS / "run_retrieval_baselines.py"),
                   "--canonical-root", str(canonical), "--embedding-root", str(embeddings),
                   "--output-dir", str(results)]
        if args.overwrite:
            command.append("--overwrite")
        run(command)

    if "evaluate" in stages:
        run([python, str(SCRIPTS / "evaluate_caption_ablation_dual_qrels.py"),
             "--canonical-root", str(canonical), "--results-dir", str(results)])

    receipt = {
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "model_key": args.model_key,
        "dataset": args.dataset,
        "stages": stages,
        "canonical": str(canonical),
        "embeddings": str(embeddings),
        "results": str(results),
    }
    lane.mkdir(parents=True, exist_ok=True)
    (lane / "downstream_receipt.json").write_text(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
