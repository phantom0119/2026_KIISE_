#!/usr/bin/env python3
"""Read-only alignment and embedding sanity checks for IntentStore P0-C."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_safety_representation as base


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def main() -> int:
    rows = []
    failures = []
    for dataset, config in base.CONFIGS.items():
        canonical = Path(config["canonical"])
        visual = Path(config["visual"])
        text_root = Path(config["text_results"])
        queries = base.read_queries(canonical / "queries.jsonl")
        qrels = pd.read_csv(canonical / "qrels.tsv", sep="\t")
        clips = pd.read_parquet(canonical / "clips.parquet")
        frame_index = pd.read_parquet(visual / "frame_index.parquet")
        frame_embeddings = np.load(visual / "frame_embeddings.npy").astype("float32")
        new_embeddings = np.load(RESULTS / f"safety_clip_query_embeddings_{dataset.lower()}.npy").astype("float32")
        text_results = pd.read_parquet(text_root / "retrieval_results.parquet")
        old_queries = base.read_queries(visual / "query_index.jsonl")
        old_embeddings = np.load(visual / "query_text_embeddings.npy").astype("float32")

        old_by_text = {
            str(query["query_text"]).strip().lower(): old_embeddings[pos]
            for pos, query in enumerate(old_queries)
        }
        exact_cosines = []
        for pos, query in enumerate(queries):
            key = str(query["query_text"]).strip().lower()
            if key in old_by_text:
                exact_cosines.append(float(new_embeddings[pos] @ old_by_text[key]))

        needed = set()
        for query in queries:
            strategy = "B2_vector_only" if not dict(query.get("metadata_filter") or {}) else "B4_prefilter_vector"
            needed.add((strategy, str(query["query_id"])))
        available = set(zip(text_results["strategy"].astype(str), text_results["query_id"].astype(str), strict=False))
        missing_text = sorted(needed - available)
        positives = set(qrels["target_id"].astype(str))
        clip_ids = set(clips["clip_id"].astype(str))
        frame_clips = set(frame_index["clip_id"].astype(str))
        frame_norms = np.linalg.norm(frame_embeddings, axis=1)
        query_norms = np.linalg.norm(new_embeddings, axis=1)

        checks = {
            "dataset": dataset,
            "queries": len(queries),
            "clips": len(clip_ids),
            "qrel_targets_outside_corpus": len(positives - clip_ids),
            "clips_without_frames": len(clip_ids - frame_clips),
            "frame_count": len(frame_index),
            "frames_per_clip_min": int(frame_index.groupby("clip_id").size().min()),
            "frames_per_clip_max": int(frame_index.groupby("clip_id").size().max()),
            "frame_norm_min": float(frame_norms.min()),
            "frame_norm_max": float(frame_norms.max()),
            "query_norm_min": float(query_norms.min()),
            "query_norm_max": float(query_norms.max()),
            "missing_required_text_rankings": len(missing_text),
            "exact_old_query_text_matches": len(exact_cosines),
            "exact_match_cosine_min": min(exact_cosines) if exact_cosines else None,
            "exact_match_cosine_max": max(exact_cosines) if exact_cosines else None,
        }
        rows.append(checks)
        if checks["qrel_targets_outside_corpus"] or checks["clips_without_frames"] or checks["missing_required_text_rankings"]:
            failures.append(dataset)
        if not (0.999 <= checks["frame_norm_min"] <= checks["frame_norm_max"] <= 1.001):
            failures.append(f"{dataset}:frame_norm")
        if not (0.999 <= checks["query_norm_min"] <= checks["query_norm_max"] <= 1.001):
            failures.append(f"{dataset}:query_norm")
        if exact_cosines and min(exact_cosines) < 0.9999:
            failures.append(f"{dataset}:exact_query_reproduction")

    decision = {"status": "ALIGNMENT_PASS" if not failures else "ALIGNMENT_FAIL", "failures": failures, "datasets": rows}
    (RESULTS / "safety_alignment_audit.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# P0-C 입력 정합성 감사",
        "",
        f"> 판정: **`{decision['status']}`**",
        "",
        "| dataset | queries | clips | qrel outside | clips w/o frames | frames/clip | frame norm | query norm | missing text ranks | exact old-text matches | min cosine |",
        "|---|---:|---:|---:|---:|---|---|---|---:|---:|---:|",
    ]
    for row in rows:
        cosine = "n/a" if row["exact_match_cosine_min"] is None else f"{row['exact_match_cosine_min']:.6f}"
        lines.append(
            f"| {row['dataset']} | {row['queries']} | {row['clips']} | {row['qrel_targets_outside_corpus']} | "
            f"{row['clips_without_frames']} | {row['frames_per_clip_min']}–{row['frames_per_clip_max']} | "
            f"{row['frame_norm_min']:.6f}–{row['frame_norm_max']:.6f} | "
            f"{row['query_norm_min']:.6f}–{row['query_norm_max']:.6f} | {row['missing_required_text_rankings']} | "
            f"{row['exact_old_query_text_matches']} | {cosine} |"
        )
    lines.extend(
        [
            "",
            "동일 문구가 과거 CLIP query index에도 존재하는 경우 새 CPU embedding과 기존 embedding의 cosine을 확인했다. AI Hub 비순환 질의는 문구가 모두 바뀌어 exact-text 재현 셀이 없지만 norm·coverage 검사는 통과해야 한다.",
            "",
        ]
    )
    (ROOT / "P0_CPU_SAFETY_ALIGNMENT_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())

