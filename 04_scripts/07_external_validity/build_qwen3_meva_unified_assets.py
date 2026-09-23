#!/usr/bin/env python3
"""Build same-encoder Qwen3-VL text/image assets for the external MEVA workload."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[3]
QWEN_ROOT = PROJECT_ROOT / "Qwen3-VL-Embedding"
MODEL = QWEN_ROOT / "models" / "Qwen3-VL-Embedding-2B"
CANONICAL = Path(
    "/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/"
    "qwen35_9b/meva/canonical"
)
SOURCE_ROOT = PROJECT_ROOT / "Datasets" / "processed" / "meva_kf1" / "20260713"
OUTPUT = SOURCE_ROOT / "embeddings" / "qwen3vl2b-unified-qwen35captions"
INSTRUCTION = "Represent the user's input."


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--canonical-root", type=Path, default=CANONICAL)
    p.add_argument("--source-root", type=Path, default=SOURCE_ROOT)
    p.add_argument("--qwen-root", type=Path, default=QWEN_ROOT)
    p.add_argument("--model", type=Path, default=MODEL)
    p.add_argument("--output-dir", type=Path, default=OUTPUT)
    p.add_argument("--image-batch-size", type=int, default=4)
    p.add_argument("--text-batch-size", type=int, default=16)
    p.add_argument("--overwrite", action="store_true")
    return p.parse_args()


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while data := handle.read(chunk):
            h.update(data)
    return h.hexdigest()


def load_queries(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def make_model(args):
    sys.path.insert(0, str(args.qwen_root))
    from src.models.qwen3_vl_embedding import Qwen3VLEmbedder

    return Qwen3VLEmbedder(
        model_name_or_path=str(args.model),
        dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
        max_pixels=534600,
        default_instruction=INSTRUCTION,
    )


def embed(model, inputs: list[dict], initial_batch: int, label: str) -> np.ndarray:
    rows = []
    pos = 0
    batch_size = initial_batch
    while pos < len(inputs):
        batch = inputs[pos : pos + batch_size]
        try:
            value = model.process(batch).detach().float().cpu().numpy().astype("float32")
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            if batch_size == 1:
                raise
            batch_size = max(1, batch_size // 2)
            print(f"[{label}] OOM -> batch={batch_size}", flush=True)
            continue
        rows.append(value)
        pos += len(batch)
        if pos % max(100, batch_size) == 0 or pos == len(inputs):
            print(f"[{label}] {pos}/{len(inputs)}", flush=True)
    matrix = np.vstack(rows).astype("float32")
    norms = np.linalg.norm(matrix, axis=1)
    if not np.isfinite(matrix).all() or np.max(np.abs(norms - 1.0)) > 5e-3:
        raise RuntimeError(f"Invalid {label} embeddings")
    return matrix


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = ["document_embeddings.npy", "query_embeddings.npy", "frame_embeddings.npy"]
    if not args.overwrite and any((args.output_dir / name).exists() for name in outputs):
        raise FileExistsError(f"{args.output_dir} already contains vector assets")

    documents = pd.read_parquet(args.canonical_root / "documents.parquet").reset_index(drop=True)
    queries = load_queries(args.canonical_root / "queries.jsonl")
    frame_index = pd.read_parquet(args.source_root / "embeddings" / "clip-vit-b32" / "frame_index.parquet")
    clips = pd.read_parquet(args.canonical_root / "clips.parquet")
    if frame_index["clip_id"].astype(str).tolist() != clips["clip_id"].astype(str).tolist():
        raise RuntimeError("MEVA frame index is not aligned with canonical clips")
    paths = []
    for raw in frame_index["frame_path"].astype(str):
        path = Path(raw)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        paths.append(path)
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing MEVA frames: {missing[:10]}")

    model = make_model(args)
    frame_vectors = embed(model, [{"image": str(path)} for path in paths], args.image_batch_size, "frame")
    document_vectors = embed(
        model,
        [{"text": str(value)} for value in documents["text"].fillna("")],
        args.text_batch_size,
        "caption-text",
    )
    query_vectors = embed(
        model,
        [{"text": str(row["query_text"])} for row in queries],
        args.text_batch_size,
        "query-text",
    )
    np.save(args.output_dir / "frame_embeddings.npy", frame_vectors)
    np.save(args.output_dir / "document_embeddings.npy", document_vectors)
    np.save(args.output_dir / "query_embeddings.npy", query_vectors)
    frame_index.to_parquet(args.output_dir / "frame_index.parquet", index=False)
    documents[["doc_id", "clip_id", "doc_type"]].to_parquet(args.output_dir / "document_index.parquet", index=False)
    pd.DataFrame(
        {
            "query_id": [row["query_id"] for row in queries],
            "difficulty": [row["difficulty"] for row in queries],
            "positive_count": [row["positive_count"] for row in queries],
        }
    ).to_parquet(args.output_dir / "query_index.parquet", index=False)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "external same-encoder storage control",
        "model": str(args.model.resolve()),
        "dimension": 2048,
        "instruction": INSTRUCTION,
        "persisted_dtype": "float32",
        "canonical_root": str(args.canonical_root.resolve()),
        "counts": {"documents": len(documents), "queries": len(queries), "frames": len(frame_index)},
        "input_hashes": {
            "documents": sha256_file(args.canonical_root / "documents.parquet"),
            "queries": sha256_file(args.canonical_root / "queries.jsonl"),
            "qrels": sha256_file(args.canonical_root / "qrels.tsv"),
            "qrels_semantic": sha256_file(args.canonical_root / "qrels_semantic.tsv"),
            "frame_index": sha256_file(args.source_root / "embeddings" / "clip-vit-b32" / "frame_index.parquet"),
        },
        "output_hashes": {name: sha256_file(args.output_dir / name) for name in outputs},
    }
    (args.output_dir / "embedding_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
