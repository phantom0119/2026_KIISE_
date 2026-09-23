#!/usr/bin/env python3
"""Materialize one Qwen3-VL joint image-caption vector per frozen 522 clip.

The primary treatment jointly encodes the representative frame and its matched
generated caption in one Qwen3-VL-Embedding-2B input.  A deterministic
derangement mode materializes image + wrong-caption vectors as a negative
control while preserving the image order and caption distribution.

The script is resumable.  Unfinished rows in the N x 2048 output memmap remain
NaN and are recomputed on the next invocation with ``--resume``.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_ROOT = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
DEFAULT_CANONICAL = Path(
    "/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/"
    "qwen35_9b/522/canonical"
)
DEFAULT_QWEN_ROOT = PROJECT_ROOT / "Qwen3-VL-Embedding"
DEFAULT_MODEL = DEFAULT_QWEN_ROOT / "models" / "Qwen3-VL-Embedding-2B"
DEFAULT_OUTPUT = DEFAULT_DATA_ROOT / "embeddings_qwen3vl2b_joint_image_caption_qwen35captions"
DEFAULT_INSTRUCTION = "Represent the user's input."
DIMENSION = 2048
SEED = 20260717


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    parser.add_argument("--qwen-root", type=Path, default=DEFAULT_QWEN_ROOT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--caption-pair", choices=("matched", "shuffled"), default="matched")
    parser.add_argument("--instruction", default=DEFAULT_INSTRUCTION)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--max-pixels", type=int, default=534600)
    parser.add_argument(
        "--attention",
        choices=("sdpa", "eager", "flash_attention_2"),
        default="flash_attention_2",
        help="Use the Qwen project .venv for the default FlashAttention2 control",
    )
    parser.add_argument("--max-items", type=int)
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while data := handle.read(chunk):
            digest.update(data)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_derangement(size: int, seed: int) -> np.ndarray:
    """Return a deterministic permutation with no fixed points."""
    if size < 2:
        raise ValueError("A shuffled-caption control requires at least two clips")
    rng = np.random.default_rng(seed)
    permutation = rng.permutation(size)
    fixed = np.flatnonzero(permutation == np.arange(size))
    if len(fixed) == 1:
        i = int(fixed[0])
        j = (i + 1) % size
        permutation[i], permutation[j] = permutation[j], permutation[i]
    elif len(fixed) > 1:
        permutation[fixed] = np.roll(permutation[fixed], 1)
    if np.any(permutation == np.arange(size)):
        raise RuntimeError("Failed to construct a derangement")
    return permutation


def resolve_media_path(data_root: Path, raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else data_root / path


def build_input_index(args: argparse.Namespace) -> pd.DataFrame:
    clips = pd.read_parquet(args.canonical_root / "clips.parquet").reset_index(drop=True)
    documents = pd.read_parquet(args.canonical_root / "documents.parquet").reset_index(drop=True)
    if clips["clip_id"].duplicated().any() or documents["clip_id"].duplicated().any():
        raise RuntimeError("clips/documents must contain exactly one row per clip_id")
    merged = clips.merge(
        documents[["clip_id", "doc_id", "text", "doc_type"]],
        on="clip_id",
        how="left",
        validate="one_to_one",
    )
    if merged["text"].isna().any() or merged["doc_id"].isna().any():
        raise RuntimeError("Every clip must have one generated-caption document")
    paths = [resolve_media_path(args.data_root, str(raw)) for raw in merged["media_path"]]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing representative frames: {missing[:10]} (n={len(missing)})")
    merged["resolved_media_path"] = [str(path.resolve()) for path in paths]
    merged["image_clip_id"] = merged["clip_id"].astype(str)
    merged["caption_clip_id"] = merged["clip_id"].astype(str)
    merged["caption_doc_id"] = merged["doc_id"].astype(str)
    merged["caption_text"] = merged["text"].astype(str)

    if args.caption_pair == "shuffled":
        order = make_derangement(len(merged), args.seed)
        merged["caption_clip_id"] = merged.iloc[order]["clip_id"].astype(str).to_numpy()
        merged["caption_doc_id"] = merged.iloc[order]["doc_id"].astype(str).to_numpy()
        merged["caption_text"] = merged.iloc[order]["text"].astype(str).to_numpy()
    merged["caption_match"] = merged["image_clip_id"].eq(merged["caption_clip_id"])
    if args.caption_pair == "matched" and not merged["caption_match"].all():
        raise RuntimeError("Matched treatment contains a mismatched caption")
    if args.caption_pair == "shuffled" and merged["caption_match"].any():
        raise RuntimeError("Shuffled treatment contains a matched caption")

    if args.max_items is not None:
        if args.max_items <= 0:
            raise ValueError("--max-items must be positive")
        merged = merged.iloc[: args.max_items].copy()
    merged.insert(0, "row_id", np.arange(len(merged), dtype=np.int64))
    return merged[
        [
            "row_id",
            "clip_id",
            "image_clip_id",
            "caption_clip_id",
            "caption_doc_id",
            "caption_match",
            "visual_video_id",
            "split",
            "media_path",
            "resolved_media_path",
            "caption_text",
        ]
    ].reset_index(drop=True)


def make_embedder(args: argparse.Namespace):
    sys.path.insert(0, str(args.qwen_root))
    from src.models.qwen3_vl_embedding import Qwen3VLEmbedder

    return Qwen3VLEmbedder(
        model_name_or_path=str(args.model),
        dtype=torch.bfloat16,
        attn_implementation=args.attention,
        max_pixels=args.max_pixels,
        default_instruction=args.instruction,
    )


def initialize_output(args: argparse.Namespace, index: pd.DataFrame) -> np.memmap:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    vector_path = args.output_dir / "joint_embeddings.npy"
    index_path = args.output_dir / "joint_index.parquet"
    manifest_path = args.output_dir / "embedding_manifest.json"
    progress_path = args.output_dir / "progress.json"

    existing = [path for path in (vector_path, index_path, manifest_path, progress_path) if path.exists()]
    if args.overwrite:
        for path in existing:
            path.unlink()
        existing = []
    if existing and not args.resume:
        raise FileExistsError(
            f"{args.output_dir} already contains outputs; pass --resume or --overwrite"
        )

    if vector_path.exists():
        matrix = np.load(vector_path, mmap_mode="r+")
        if tuple(matrix.shape) != (len(index), DIMENSION) or matrix.dtype != np.float32:
            raise RuntimeError(
                f"Existing vector shape/dtype differs: {matrix.shape}/{matrix.dtype}, "
                f"expected {(len(index), DIMENSION)}/float32"
            )
        old_index = pd.read_parquet(index_path)
        if not old_index["clip_id"].astype(str).equals(index["clip_id"].astype(str)):
            raise RuntimeError("Existing joint_index clip order differs from the frozen input")
        if not old_index["caption_clip_id"].astype(str).equals(index["caption_clip_id"].astype(str)):
            raise RuntimeError("Existing joint_index caption pairing differs")
        return matrix

    index.drop(columns=["caption_text"]).to_parquet(index_path, index=False)
    matrix = np.lib.format.open_memmap(
        vector_path,
        mode="w+",
        dtype="float32",
        shape=(len(index), DIMENSION),
    )
    matrix[:] = np.nan
    matrix.flush()
    return matrix


def write_progress(args: argparse.Namespace, payload: dict[str, Any]) -> None:
    path = args.output_dir / "progress.json"
    temp = path.with_suffix(".json.tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def main() -> int:
    args = parse_args()
    if args.batch_size <= 0:
        raise ValueError("--batch-size must be positive")
    index = build_input_index(args)
    matrix = initialize_output(args, index)
    completed_mask = np.isfinite(matrix).all(axis=1)
    completed_before = int(completed_mask.sum())
    remaining = np.flatnonzero(~completed_mask)
    print(
        f"[input] pair={args.caption_pair} clips={len(index)} "
        f"completed={completed_before} remaining={len(remaining)}",
        flush=True,
    )

    started_at = utc_now()
    wall_start = time.perf_counter()
    model = None
    active_batch = args.batch_size
    batch_times: list[float] = []
    if len(remaining):
        model = make_embedder(args)
        position = 0
        while position < len(remaining):
            rows = remaining[position : position + active_batch]
            inputs = [
                {
                    "image": str(index.iloc[int(row)]["resolved_media_path"]),
                    "text": str(index.iloc[int(row)]["caption_text"]),
                    "instruction": args.instruction,
                }
                for row in rows
            ]
            batch_start = time.perf_counter()
            try:
                vectors = model.process(inputs).detach().float().cpu().numpy().astype("float32")
            except torch.cuda.OutOfMemoryError:
                torch.cuda.empty_cache()
                if active_batch == 1:
                    raise
                active_batch = max(1, active_batch // 2)
                print(f"[joint] CUDA OOM; retrying with batch={active_batch}", flush=True)
                continue
            elapsed = time.perf_counter() - batch_start
            if tuple(vectors.shape) != (len(rows), DIMENSION):
                raise RuntimeError(f"Unexpected joint vector shape: {vectors.shape}")
            norms = np.linalg.norm(vectors, axis=1)
            if not np.isfinite(vectors).all() or float(np.max(np.abs(norms - 1.0))) > 5e-3:
                raise RuntimeError(f"Invalid joint vectors; norm range={norms.min()}..{norms.max()}")
            matrix[rows] = vectors
            matrix.flush()
            position += len(rows)
            batch_times.append(elapsed)
            completed = completed_before + position
            rate = position / max(1e-9, time.perf_counter() - wall_start)
            eta_s = (len(remaining) - position) / max(1e-9, rate)
            progress = {
                "updated_at": utc_now(),
                "caption_pair": args.caption_pair,
                "rows": len(index),
                "completed": completed,
                "remaining": len(index) - completed,
                "active_batch_size": active_batch,
                "processed_this_run": position,
                "items_per_second_this_run": rate,
                "eta_seconds": eta_s,
            }
            write_progress(args, progress)
            if completed % 20 == 0 or position == len(remaining):
                print(
                    f"[joint] {completed}/{len(index)} rate={rate:.3f} item/s "
                    f"eta={eta_s / 60:.1f} min",
                    flush=True,
                )

    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    final = np.load(args.output_dir / "joint_embeddings.npy", mmap_mode="r")
    finite = np.isfinite(final).all(axis=1)
    norms = np.linalg.norm(final, axis=1)
    if not finite.all() or float(np.max(np.abs(norms - 1.0))) > 5e-3:
        raise RuntimeError(
            f"Final vector audit failed: finite={int(finite.sum())}/{len(final)}, "
            f"norm={norms.min()}..{norms.max()}"
        )

    elapsed_s = time.perf_counter() - wall_start
    index_path = args.output_dir / "joint_index.parquet"
    vector_path = args.output_dir / "joint_embeddings.npy"
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "CPU"
    manifest = {
        "created_at": utc_now(),
        "started_at": started_at,
        "purpose": "single-vector early-fusion image-caption storage treatment",
        "caption_pair": args.caption_pair,
        "seed": args.seed,
        "model": str(args.model.resolve()),
        "model_family": "Qwen3-VL-Embedding-2B",
        "dimension": DIMENSION,
        "persisted_dtype": "float32",
        "normalization": "L2 by model.process",
        "instruction": args.instruction,
        "image_settings": {
            "dtype": "bfloat16 inference",
            "max_pixels": args.max_pixels,
            "attention": args.attention,
        },
        "canonical_root": str(args.canonical_root.resolve()),
        "data_root": str(args.data_root.resolve()),
        "counts": {
            "vectors": len(index),
            "matched_pairs": int(index["caption_match"].sum()),
            "mismatched_pairs": int((~index["caption_match"]).sum()),
        },
        "runtime": {
            "elapsed_seconds_this_run": elapsed_s,
            "completed_before_run": completed_before,
            "processed_this_run": len(remaining),
            "items_per_second_this_run": len(remaining) / elapsed_s if elapsed_s else None,
            "batch_size_requested": args.batch_size,
            "batch_size_final": active_batch,
            "gpu": gpu_name,
            "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES"),
            "host": platform.node(),
        },
        "audits": {
            "unique_clip_ids": int(index["clip_id"].nunique()) == len(index),
            "all_media_exist": True,
            "all_finite": bool(finite.all()),
            "norm_min": float(norms.min()),
            "norm_max": float(norms.max()),
            "pairing_matches_treatment": bool(
                index["caption_match"].all()
                if args.caption_pair == "matched"
                else (~index["caption_match"]).all()
            ),
        },
        "input_hashes": {
            "clips": sha256_file(args.canonical_root / "clips.parquet"),
            "documents": sha256_file(args.canonical_root / "documents.parquet"),
            "queries": sha256_file(args.canonical_root / "queries.jsonl"),
            "qrels": sha256_file(args.canonical_root / "qrels.tsv"),
            "qrels_semantic": sha256_file(args.canonical_root / "qrels_semantic.tsv"),
        },
        "output_hashes": {
            "joint_embeddings": sha256_file(vector_path),
            "joint_index": sha256_file(index_path),
        },
        "vector_payload_mb": final.nbytes / 1e6,
    }
    (args.output_dir / "embedding_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_progress(
        args,
        {
            "updated_at": utc_now(),
            "caption_pair": args.caption_pair,
            "rows": len(index),
            "completed": len(index),
            "remaining": 0,
            "status": "complete",
        },
    )
    print(
        f"[done] pair={args.caption_pair} vectors={len(index)} "
        f"elapsed={elapsed_s / 60:.2f} min payload={final.nbytes / 1e6:.3f} MB "
        f"-> {args.output_dir}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
