#!/usr/bin/env python3
"""Build a fair canonical subset from clips that have materialized frames."""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


OPTIONAL_CLIP_TABLES = ["views.parquet", "evidence_frames.parquet"]


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--frame-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    if args.output_dir.exists() and args.overwrite:
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    frames = pd.read_parquet(args.frame_root / "frames.parquet")
    selected_clip_ids = set(frames["clip_id"].dropna().astype(str))
    if not selected_clip_ids:
        raise ValueError(f"No clip_id values found in {args.frame_root / 'frames.parquet'}")

    clips = pd.read_parquet(args.canonical_root / "clips.parquet")
    documents = pd.read_parquet(args.canonical_root / "documents.parquet")
    metadata = pd.read_parquet(args.canonical_root / "metadata.parquet")
    qrels = pd.read_csv(args.canonical_root / "qrels.tsv", sep="\t")
    queries = pd.DataFrame(read_jsonl(args.canonical_root / "queries.jsonl"))

    subset_clips = clips[clips["clip_id"].astype(str).isin(selected_clip_ids)].reset_index(drop=True)
    subset_documents = documents[documents["clip_id"].astype(str).isin(selected_clip_ids)].reset_index(drop=True)
    subset_metadata = metadata[metadata["clip_id"].astype(str).isin(selected_clip_ids)].reset_index(drop=True)
    subset_qrels = qrels[qrels["target_id"].astype(str).isin(selected_clip_ids)].reset_index(drop=True)

    positives = subset_qrels.groupby("query_id").size().rename("positive_count").reset_index()
    subset_queries = queries.merge(positives, on="query_id", how="inner", suffixes=("", "_subset"))
    subset_queries["positive_count"] = subset_queries["positive_count_subset"].astype(int)
    subset_queries = subset_queries.drop(columns=["positive_count_subset"])

    allowed_query_ids = set(subset_queries["query_id"])
    subset_qrels = subset_qrels[subset_qrels["query_id"].isin(allowed_query_ids)].reset_index(drop=True)

    subset_clips.to_parquet(args.output_dir / "clips.parquet", index=False)
    subset_documents.to_parquet(args.output_dir / "documents.parquet", index=False)
    subset_metadata.to_parquet(args.output_dir / "metadata.parquet", index=False)
    subset_qrels.to_csv(args.output_dir / "qrels.tsv", sep="\t", index=False)
    write_jsonl(args.output_dir / "queries.jsonl", subset_queries.to_dict("records"))

    for table_name in OPTIONAL_CLIP_TABLES:
        src = args.canonical_root / table_name
        if not src.exists():
            continue
        table = pd.read_parquet(src)
        if "clip_id" in table.columns:
            table = table[table["clip_id"].astype(str).isin(selected_clip_ids)].reset_index(drop=True)
        table.to_parquet(args.output_dir / table_name, index=False)

    source_manifest = {}
    manifest_path = args.canonical_root / "dataset_manifest.json"
    if manifest_path.exists():
        source_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    manifest = {
        "dataset_id": source_manifest.get("dataset_id", "canonical_subset"),
        "dataset_version": f"{source_manifest.get('dataset_version', 'unknown')}_frame_subset",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_canonical_root": str(args.canonical_root),
        "source_frame_root": str(args.frame_root),
        "output_dir": str(args.output_dir),
        "subset_policy": "Keep only clips with materialized frames; filter qrels and adjust query positive_count.",
        "counts": {
            "source_clips": int(len(clips)),
            "subset_clips": int(len(subset_clips)),
            "frames": int(len(frames)),
            "documents": int(len(subset_documents)),
            "metadata_rows": int(len(subset_metadata)),
            "queries": int(len(subset_queries)),
            "qrels": int(len(subset_qrels)),
        },
    }
    (args.output_dir / "dataset_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Canonical Frame Subset Summary",
        "",
        f"created_at: `{manifest['created_at']}`",
        f"source_canonical_root: `{args.canonical_root}`",
        f"source_frame_root: `{args.frame_root}`",
        "",
        "| artifact | count |",
        "|---|---:|",
    ]
    for key, value in manifest["counts"].items():
        lines.append(f"| {key} | {value} |")
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"output_dir={args.output_dir}")
    for key, value in manifest["counts"].items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
