#!/usr/bin/env python3
"""Export qualitative examples for visual and multimodal retrieval results."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "03_src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.io import load_canonical  # noqa: E402


def truncate(value: Any, limit: int = 220) -> str:
    text = " ".join(str(value or "").split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def enrich_with_frame(rows: pd.DataFrame, frame_index: pd.DataFrame, frame_col: str) -> pd.DataFrame:
    frame_cols = frame_index[
        ["frame_id", "timestamp_sec", "frame_path", "media_path"]
    ].rename(
        columns={
            "frame_id": frame_col,
            "timestamp_sec": "evidence_timestamp_sec",
            "frame_path": "evidence_frame_path",
            "media_path": "media_path",
        }
    )
    return rows.merge(frame_cols, on=frame_col, how="left")


def write_markdown(path: Path, title: str, rows: pd.DataFrame) -> None:
    lines = [f"# {title}", ""]
    if rows.empty:
        lines.append("No examples found.")
    else:
        cols = [col for col in rows.columns if col not in {"supporting_text"}]
        lines.extend(markdown_table(rows[cols]))
        lines.extend(["", "## Supporting Text"])
        for idx, row in enumerate(rows.to_dict("records"), start=1):
            lines.extend(
                [
                    "",
                    f"### Example {idx}",
                    "",
                    f"- query_id: `{row.get('query_id', '')}`",
                    f"- clip_id: `{row.get('clip_id', '')}`",
                    f"- supporting_text: {truncate(row.get('supporting_text', ''), 500)}",
                ]
            )
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def markdown_cell(value: Any) -> str:
    text = truncate(value, 120)
    return text.replace("|", "\\|").replace("\n", " ")


def markdown_table(rows: pd.DataFrame) -> list[str]:
    if rows.empty:
        return ["No rows."]
    cols = rows.columns.tolist()
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join(["---"] * len(cols)) + " |",
    ]
    for row in rows.to_dict("records"):
        lines.append("| " + " | ".join(markdown_cell(row.get(col, "")) for col in cols) + " |")
    return lines


def select_first_relevant(results: pd.DataFrame, strategy: str, limit: int) -> pd.DataFrame:
    subset = results[
        results["strategy"].eq(strategy)
        & results["is_relevant"].eq(True)
        & results["rank"].le(10)
    ].sort_values(["query_id", "rank"], kind="mergesort")
    return subset.groupby("query_id", sort=False).head(1).head(limit).reset_index(drop=True)


def build_text_examples(
    *,
    canonical_root: Path,
    frame_index: pd.DataFrame,
    results_path: Path,
    strategy: str,
    frame_col: str,
    limit: int,
) -> pd.DataFrame:
    _clips, documents, _metadata, queries, _qrels = load_canonical(canonical_root)
    query_map = queries[["query_id", "query_text", "difficulty"]]
    doc_text = (
        documents.sort_values(["clip_id", "doc_id"], kind="mergesort")
        .groupby("clip_id", sort=False)["text"]
        .first()
        .reset_index()
        .rename(columns={"text": "supporting_text"})
    )

    results = pd.read_parquet(results_path)
    rows = select_first_relevant(results, strategy, limit)
    if rows.empty:
        return rows
    rows = rows.merge(query_map, on="query_id", how="left")
    rows = rows.merge(doc_text, on="clip_id", how="left")
    rows = enrich_with_frame(rows, frame_index, frame_col)
    selected_cols = [
        "strategy",
        "query_id",
        "difficulty",
        "query_text",
        "rank",
        "clip_id",
        frame_col,
        "evidence_timestamp_sec",
        "evidence_frame_path",
        "media_path",
        "score",
        "supporting_text",
    ]
    return rows[[col for col in selected_cols if col in rows.columns]]


def build_image_examples(
    *,
    image_result_root: Path,
    frame_index: pd.DataFrame,
    limit: int,
) -> pd.DataFrame:
    queries = pd.read_parquet(image_result_root / "image_queries.parquet")
    results = pd.read_parquet(image_result_root / "image_query_results.parquet")
    rows = select_first_relevant(results, "IM1_image_to_video_holdout", limit)
    if rows.empty:
        return rows
    rows = rows.merge(queries, on="query_id", how="left")
    rows = enrich_with_frame(rows, frame_index, "frame_id")
    selected_cols = [
        "strategy",
        "query_id",
        "query_clip_id",
        "query_frame_id",
        "query_timestamp_sec",
        "query_frame_path",
        "rank",
        "clip_id",
        "frame_id",
        "evidence_timestamp_sec",
        "evidence_frame_path",
        "score",
    ]
    return rows[[col for col in selected_cols if col in rows.columns]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-name", required=True)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--visual-embedding-root", type=Path, required=True)
    parser.add_argument("--visual-result-root", type=Path, required=True)
    parser.add_argument("--fusion-result-root", type=Path, required=True)
    parser.add_argument("--image-result-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    frame_index = pd.read_parquet(args.visual_embedding_root / "frame_index.parquet")

    visual_examples = build_text_examples(
        canonical_root=args.canonical_root,
        frame_index=frame_index,
        results_path=args.visual_result_root / "visual_retrieval_results.parquet",
        strategy="M4_metadata_prefilter_visual",
        frame_col="frame_id",
        limit=args.limit,
    )
    fusion_examples = build_text_examples(
        canonical_root=args.canonical_root,
        frame_index=frame_index,
        results_path=args.fusion_result_root / "multimodal_fusion_results.parquet",
        strategy="M6_text_visual_metadata_rrf",
        frame_col="visual_frame_id",
        limit=args.limit,
    )
    image_examples = build_image_examples(
        image_result_root=args.image_result_root,
        frame_index=frame_index,
        limit=args.limit,
    )

    stem = args.dataset_name
    visual_examples.to_csv(args.output_dir / f"{stem}_m4_visual_examples.csv", index=False)
    fusion_examples.to_csv(args.output_dir / f"{stem}_m6_fusion_examples.csv", index=False)
    image_examples.to_csv(args.output_dir / f"{stem}_im1_image_examples.csv", index=False)
    write_markdown(args.output_dir / f"{stem}_m4_visual_examples.md", f"{stem} M4 Visual Examples", visual_examples)
    write_markdown(args.output_dir / f"{stem}_m6_fusion_examples.md", f"{stem} M6 Fusion Examples", fusion_examples)
    write_markdown(args.output_dir / f"{stem}_im1_image_examples.md", f"{stem} IM1 Image-to-Video Examples", image_examples)

    print(f"output_dir={args.output_dir}")
    print(f"dataset={args.dataset_name}")
    print(f"m4_examples={len(visual_examples)}")
    print(f"m6_examples={len(fusion_examples)}")
    print(f"im1_examples={len(image_examples)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
