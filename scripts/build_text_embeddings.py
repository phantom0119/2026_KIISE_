#!/usr/bin/env python3
"""Build document/query text embeddings for a canonical workload."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.embeddings import build_text_embeddings  # noqa: E402


MODEL_PATHS = {
    "bge-m3": PROJECT_ROOT / "Datasets" / "models" / "huggingface" / "BAAI--bge-m3",
    "e5-large-v2": PROJECT_ROOT / "Datasets" / "models" / "huggingface" / "intfloat--e5-large-v2",
}


def default_device() -> str:
    try:
        import torch

        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=PROJECT_ROOT / "Datasets" / "processed" / "vru_accident" / "20260706" / "canonical",
    )
    parser.add_argument("--model-id", default="bge-m3", choices=sorted(MODEL_PATHS))
    parser.add_argument("--model-path", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=None)
    parser.add_argument("--device", default=default_device())
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    model_path = args.model_path or MODEL_PATHS[args.model_id]
    output_dir = args.output_dir or args.canonical_root.parent / "embeddings" / args.model_id
    result = build_text_embeddings(
        canonical_root=args.canonical_root,
        output_dir=output_dir,
        model_id=args.model_id,
        model_path=model_path,
        device=args.device,
        batch_size=args.batch_size,
        overwrite=args.overwrite,
    )
    print(f"output_dir={result.output_dir}")
    print(f"model_id={result.model_id}")
    print(f"device={result.device}")
    print(f"document_count={result.document_count}")
    print(f"query_count={result.query_count}")
    print(f"embedding_dim={result.embedding_dim}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
