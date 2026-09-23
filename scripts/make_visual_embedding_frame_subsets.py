#!/usr/bin/env python3
"""Create frame-budget subsets from an existing visual embedding directory."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


def parse_frame_seqs(spec: str) -> list[int]:
    values = [int(value.strip()) for value in spec.split(",") if value.strip()]
    if not values:
        raise ValueError("At least one frame sequence must be provided.")
    return values


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-embedding-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--frame-seqs", required=True, help="Comma-separated frame_seq values to retain, e.g. 2 or 1,2.")
    parser.add_argument("--subset-name", required=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    frame_seqs = parse_frame_seqs(args.frame_seqs)
    frame_index = pd.read_parquet(args.source_embedding_root / "frame_index.parquet")
    frame_embeddings = np.load(args.source_embedding_root / "frame_embeddings.npy").astype("float32")
    if len(frame_index) != len(frame_embeddings):
        raise ValueError("Frame index and frame embedding count differ.")

    keep_mask = frame_index["frame_seq"].isin(frame_seqs).to_numpy()
    subset_index = frame_index.loc[keep_mask].reset_index(drop=True)
    subset_embeddings = frame_embeddings[keep_mask]
    if subset_index.empty:
        raise ValueError(f"No frames matched frame_seqs={frame_seqs}.")

    subset_index.to_parquet(args.output_dir / "frame_index.parquet", index=False)
    np.save(args.output_dir / "frame_embeddings.npy", subset_embeddings)
    shutil.copy2(args.source_embedding_root / "query_text_embeddings.npy", args.output_dir / "query_text_embeddings.npy")
    shutil.copy2(args.source_embedding_root / "query_index.jsonl", args.output_dir / "query_index.jsonl")

    source_manifest = json.loads((args.source_embedding_root / "visual_embedding_manifest.json").read_text(encoding="utf-8"))
    manifest = {
        **source_manifest,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_embedding_root": str(args.source_embedding_root),
        "output_dir": str(args.output_dir),
        "subset_name": args.subset_name,
        "retained_frame_seq": frame_seqs,
        "frame_count": int(len(subset_index)),
        "clip_count": int(subset_index["clip_id"].nunique()),
        "source_frame_count": int(len(frame_index)),
        "source_clip_count": int(frame_index["clip_id"].nunique()),
        "files": {
            "frame_embeddings": "frame_embeddings.npy",
            "query_text_embeddings": "query_text_embeddings.npy",
            "frame_index": "frame_index.parquet",
            "query_index": "query_index.jsonl",
        },
    }
    (args.output_dir / "visual_embedding_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"output_dir={args.output_dir}")
    print(f"subset_name={args.subset_name}")
    print(f"retained_frame_seq={frame_seqs}")
    print(f"frames={len(subset_index)}")
    print(f"clips={subset_index['clip_id'].nunique()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
