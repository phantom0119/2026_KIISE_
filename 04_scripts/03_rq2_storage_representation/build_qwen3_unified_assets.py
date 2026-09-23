#!/usr/bin/env python3
"""Materialize encoder-controlled Qwen3-VL assets for the 522 workload.

The script aligns query text, caption text, representative images, and all
frames in the *same* Qwen3-VL-Embedding-2B space.  Existing per-task frame
embeddings are reused after a coverage/value audit.  Missing frames can be
recomputed with the exact image-embedding settings used by the original run.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_DATA_ROOT = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
DEFAULT_CANONICAL = Path(
    "/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/"
    "qwen35_9b/522/canonical"
)
DEFAULT_QWEN_ROOT = PROJECT_ROOT / "Qwen3-VL-Embedding"
DEFAULT_OUTPUT = DEFAULT_DATA_ROOT / "embeddings_qwen3vl2b_unified_qwen35captions"
DEFAULT_INSTRUCTION = "Represent the user's input."


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-root", type=Path, default=DEFAULT_DATA_ROOT)
    p.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL)
    p.add_argument("--qwen-root", type=Path, default=DEFAULT_QWEN_ROOT)
    p.add_argument("--frame-pt-root", type=Path, default=DEFAULT_QWEN_ROOT / "aihub_522_embeddings")
    p.add_argument("--model", type=Path, default=DEFAULT_QWEN_ROOT / "models" / "Qwen3-VL-Embedding-2B")
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--text-batch-size", type=int, default=16)
    p.add_argument("--image-batch-size", type=int, default=4)
    p.add_argument("--repair-missing", action="store_true")
    p.add_argument("--overwrite-text", action="store_true")
    return p.parse_args()


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while data := f.read(chunk):
            h.update(data)
    return h.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_frame_vectors(pt_root: Path, repair_path: Path | None = None) -> tuple[dict[str, np.ndarray], dict]:
    paths = sorted((pt_root / "train").glob("*.pt")) + sorted((pt_root / "val").glob("*.pt"))
    if repair_path is not None and repair_path.exists():
        paths.append(repair_path)
    vectors: dict[str, np.ndarray] = {}
    duplicate_equal = 0
    duplicate_conflict: list[str] = []
    rows = 0
    for number, path in enumerate(paths, start=1):
        payload = torch.load(path, map_location="cpu", weights_only=False)
        for row in payload:
            key = str(row["imgKey"])
            vector = row["vector"].detach().float().cpu().numpy().astype("float32", copy=False)
            rows += 1
            if key in vectors:
                if np.array_equal(vectors[key], vector):
                    duplicate_equal += 1
                    continue
                duplicate_conflict.append(key)
                continue
            vectors[key] = vector
        if number % 500 == 0:
            print(f"[frame-load] files={number}/{len(paths)} unique={len(vectors)}", flush=True)
    if duplicate_conflict:
        raise RuntimeError(f"Conflicting duplicate frame embeddings: {duplicate_conflict[:10]}")
    dims = sorted({tuple(value.shape) for value in vectors.values()})
    if dims != [(2048,)]:
        raise RuntimeError(f"Unexpected frame dimensions: {dims}")
    return vectors, {
        "pt_files": len(paths),
        "pt_rows": rows,
        "unique_keys": len(vectors),
        "duplicate_equal_rows": duplicate_equal,
        "duplicate_conflicts": len(duplicate_conflict),
    }


def make_embedder(args: argparse.Namespace):
    sys.path.insert(0, str(args.qwen_root))
    from src.models.qwen3_vl_embedding import Qwen3VLEmbedder

    return Qwen3VLEmbedder(
        model_name_or_path=str(args.model),
        dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
        max_pixels=534600,
        default_instruction=DEFAULT_INSTRUCTION,
    )


def process_with_backoff(model, inputs: list[dict], batch_size: int, label: str) -> np.ndarray:
    outputs: list[np.ndarray] = []
    pos = 0
    active_batch = max(1, batch_size)
    while pos < len(inputs):
        batch = inputs[pos : pos + active_batch]
        try:
            value = model.process(batch).detach().float().cpu().numpy().astype("float32")
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            if active_batch == 1:
                raise
            active_batch = max(1, active_batch // 2)
            print(f"[{label}] CUDA OOM; retrying with batch={active_batch}", flush=True)
            continue
        outputs.append(value)
        pos += len(batch)
        if pos % max(100, active_batch) == 0 or pos == len(inputs):
            print(f"[{label}] {pos}/{len(inputs)}", flush=True)
    matrix = np.vstack(outputs).astype("float32")
    norms = np.linalg.norm(matrix, axis=1)
    if not np.all(np.isfinite(matrix)) or float(np.max(np.abs(norms - 1.0))) > 5e-3:
        raise RuntimeError(f"Invalid {label} embeddings; norm range={norms.min()}..{norms.max()}")
    return matrix


def repair_missing_frames(
    args: argparse.Namespace,
    model,
    frame_index: pd.DataFrame,
    missing: list[str],
    repair_path: Path,
) -> None:
    rel_by_name = {Path(rel).name: str(rel) for rel in frame_index["relpath"]}
    paths = [args.data_root / rel_by_name[key] for key in missing]
    absent = [str(path) for path in paths if not path.exists()]
    if absent:
        raise FileNotFoundError(f"Missing source images: {absent[:10]}")
    matrix = process_with_backoff(model, [{"image": str(path)} for path in paths], args.image_batch_size, "repair")
    payload = [
        {"imgKey": missing[i], "vector": torch.from_numpy(matrix[i]).to(torch.bfloat16)}
        for i in range(len(missing))
    ]
    torch.save(payload, repair_path)
    print(f"[repair] wrote {len(payload)} vectors -> {repair_path}", flush=True)


def save_text_assets(args: argparse.Namespace, model) -> dict:
    docs = pd.read_parquet(args.canonical_root / "documents.parquet").reset_index(drop=True)
    queries = load_jsonl(args.canonical_root / "queries.jsonl")
    q_index = pd.DataFrame(
        {
            "query_id": [row["query_id"] for row in queries],
            "difficulty": [row.get("difficulty", "") for row in queries],
            "positive_count": [row.get("positive_count", 0) for row in queries],
        }
    )
    d_index = docs[["doc_id", "clip_id", "doc_type"]].copy()
    d_path = args.output_dir / "document_embeddings.npy"
    q_path = args.output_dir / "query_embeddings.npy"
    if args.overwrite_text or not (d_path.exists() and q_path.exists()):
        d_vec = process_with_backoff(
            model,
            [{"text": str(text)} for text in docs["text"].fillna("")],
            args.text_batch_size,
            "caption-text",
        )
        q_vec = process_with_backoff(
            model,
            [{"text": str(row["query_text"])} for row in queries],
            args.text_batch_size,
            "query-text",
        )
        np.save(d_path, d_vec)
        np.save(q_path, q_vec)
    else:
        d_vec = np.load(d_path, mmap_mode="r")
        q_vec = np.load(q_path, mmap_mode="r")
    d_index.to_parquet(args.output_dir / "document_index.parquet", index=False)
    q_index.to_parquet(args.output_dir / "query_index.parquet", index=False)
    if tuple(d_vec.shape) != (len(docs), 2048) or tuple(q_vec.shape) != (len(queries), 2048):
        raise RuntimeError(f"Text asset shape mismatch: documents={d_vec.shape}, queries={q_vec.shape}")
    return {"documents": len(docs), "queries": len(queries)}


def save_frame_assets(
    args: argparse.Namespace,
    vectors: dict[str, np.ndarray],
    frame_index: pd.DataFrame,
) -> dict:
    names = [Path(rel).name for rel in frame_index["relpath"].astype(str)]
    missing = [name for name in names if name not in vectors]
    if missing:
        raise RuntimeError(f"Frame coverage is incomplete after repair: {missing[:10]} ({len(missing)})")
    if len(set(names)) != len(names):
        raise RuntimeError("frame_index basenames are not unique")

    frame_path = args.output_dir / "frame_embeddings.npy"
    mm = np.lib.format.open_memmap(frame_path, mode="w+", dtype="float32", shape=(len(names), 2048))
    for start in range(0, len(names), 4096):
        batch_names = names[start : start + 4096]
        mm[start : start + len(batch_names)] = np.stack([vectors[name] for name in batch_names])
    mm.flush()
    del mm

    fi = frame_index.copy()
    fi["clip_id"] = (
        "aihub_522_intersection_vis:"
        + fi["split"].astype(str)
        + ":"
        + fi["visual_video_id"].astype(str)
    )
    fi.to_parquet(args.output_dir / "frame_index.parquet", index=False)

    clips = pd.read_parquet(args.canonical_root / "clips.parquet").reset_index(drop=True)
    representative_names = [Path(path).name for path in clips["media_path"].astype(str)]
    rep_missing = [name for name in representative_names if name not in vectors]
    if rep_missing:
        raise RuntimeError(f"Representative-frame coverage missing: {rep_missing[:10]}")
    rep = np.stack([vectors[name] for name in representative_names]).astype("float32")
    np.save(args.output_dir / "representative_frame_embeddings.npy", rep)
    clips[["clip_id", "visual_video_id", "split", "media_path"]].to_parquet(
        args.output_dir / "representative_frame_index.parquet", index=False
    )
    return {"frames": len(fi), "frame_clips": int(fi["clip_id"].nunique()), "representative_frames": len(rep)}


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    repair_path = args.output_dir / "repair_missing_frames.pt"
    frame_index = pd.read_parquet(args.data_root / "visual_embeddings_clip" / "frame_index.parquet")
    frame_vectors, frame_audit_before = load_frame_vectors(args.frame_pt_root, repair_path)
    wanted = {Path(rel).name for rel in frame_index["relpath"].astype(str)}
    missing = sorted(wanted - set(frame_vectors))
    extras = sorted(set(frame_vectors) - wanted)
    print(
        f"[coverage-before] wanted={len(wanted)} found={len(wanted) - len(missing)} "
        f"missing={len(missing)} extra={len(extras)}",
        flush=True,
    )

    model = None
    if missing:
        if not args.repair_missing:
            raise RuntimeError(f"{len(missing)} frame embeddings are missing; use --repair-missing")
        model = make_embedder(args)
        repair_missing_frames(args, model, frame_index, missing, repair_path)
        frame_vectors, frame_audit_after = load_frame_vectors(args.frame_pt_root, repair_path)
    else:
        frame_audit_after = frame_audit_before

    frame_counts = save_frame_assets(args, frame_vectors, frame_index)
    del frame_vectors
    if model is None:
        model = make_embedder(args)
    text_counts = save_text_assets(args, model)
    del model
    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    output_files = [
        "document_embeddings.npy",
        "query_embeddings.npy",
        "document_index.parquet",
        "query_index.parquet",
        "frame_embeddings.npy",
        "frame_index.parquet",
        "representative_frame_embeddings.npy",
        "representative_frame_index.parquet",
    ]
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "same-encoder storage/retrieval/index control",
        "model": str(args.model.resolve()),
        "model_family": "Qwen3-VL-Embedding-2B",
        "dimension": 2048,
        "normalization": "L2 by model.process",
        "instruction": DEFAULT_INSTRUCTION,
        "image_settings": {"dtype": "bfloat16 inference", "max_pixels": 534600, "attention": "flash_attention_2"},
        "persisted_vector_dtype": "float32",
        "canonical_root": str(args.canonical_root.resolve()),
        "data_root": str(args.data_root.resolve()),
        "frame_source_root": str(args.frame_pt_root.resolve()),
        "coverage_before": {
            **frame_audit_before,
            "wanted": len(wanted),
            "missing": len(missing),
            "extra_keys_not_in_frozen_index": len(extras),
        },
        "coverage_after": frame_audit_after,
        "counts": {**frame_counts, **text_counts},
        "input_hashes": {
            "canonical_documents": sha256_file(args.canonical_root / "documents.parquet"),
            "canonical_queries": sha256_file(args.canonical_root / "queries.jsonl"),
            "canonical_qrels": sha256_file(args.canonical_root / "qrels.tsv"),
            "canonical_qrels_semantic": sha256_file(args.canonical_root / "qrels_semantic.tsv"),
            "frame_index": sha256_file(args.data_root / "visual_embeddings_clip" / "frame_index.parquet"),
        },
        "output_hashes": {name: sha256_file(args.output_dir / name) for name in output_files},
    }
    (args.output_dir / "embedding_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest["counts"], ensure_ascii=False, indent=2))
    print(f"[done] {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
