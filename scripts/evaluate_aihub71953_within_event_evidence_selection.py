#!/usr/bin/env python3
"""Evaluate within-event evidence-frame selection for AI Hub 71953 VQA queries."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def deterministic_random_score(query_id: str, frame_id: str) -> float:
    digest = hashlib.sha256(f"{query_id}\t{frame_id}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big") / float(2**64 - 1)


def dcg(relevances: list[int], k: int) -> float:
    score = 0.0
    for idx, rel in enumerate(relevances[:k], start=1):
        if rel:
            score += 1.0 / np.log2(idx + 1)
    return float(score)


def rank_metrics(ranked: pd.DataFrame, top_ks: list[int]) -> dict[str, float]:
    rel = ranked["is_label_evidence"].astype(int).tolist()
    positives = int(sum(rel))
    metrics: dict[str, float] = {
        "candidate_count": float(len(ranked)),
        "positive_count": float(positives),
        "mrr": 0.0,
    }
    for pos, value in enumerate(rel, start=1):
        if value:
            metrics["mrr"] = 1.0 / pos
            break
    for k in top_ks:
        top = rel[:k]
        ideal = sorted(rel, reverse=True)
        denom = dcg(ideal, k)
        metrics[f"hit_at_{k}"] = float(any(top))
        metrics[f"precision_at_{k}"] = float(sum(top) / min(k, len(rel))) if rel else 0.0
        metrics[f"ndcg_at_{k}"] = float(dcg(top, k) / denom) if denom > 0 else 0.0
        positive_views = set(ranked[ranked["is_label_evidence"].eq(True)]["view"].dropna().astype(str))
        top_positive_views = set(
            ranked.head(k)[ranked.head(k)["is_label_evidence"].eq(True)]["view"].dropna().astype(str)
        )
        metrics[f"positive_view_coverage_at_{k}"] = (
            float(len(top_positive_views & positive_views) / len(positive_views)) if positive_views else 0.0
        )
    return metrics


def summarize(metrics_by_query: pd.DataFrame, top_ks: list[int]) -> pd.DataFrame:
    metric_cols = ["mrr"] + [
        col
        for k in top_ks
        for col in [f"hit_at_{k}", f"precision_at_{k}", f"ndcg_at_{k}", f"positive_view_coverage_at_{k}"]
    ]
    rows: list[dict[str, Any]] = []
    for strategy, group in metrics_by_query.groupby("strategy", sort=False):
        row: dict[str, Any] = {"strategy": strategy, "queries": len(group)}
        row.update({col: group[col].mean() for col in metric_cols})
        row["candidate_count_mean"] = group["candidate_count"].mean()
        row["positive_count_mean"] = group["positive_count"].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--visual-embedding-root", type=Path, required=True)
    parser.add_argument("--frame-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--top-ks", default="1,3,5")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    if args.output_dir.exists() and args.overwrite:
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    queries = pd.DataFrame(read_jsonl(args.canonical_root / "queries.jsonl"))
    queries = queries[queries["difficulty"].eq("instance_vqa")].reset_index(drop=True)
    frame_index = pd.read_parquet(args.visual_embedding_root / "frame_index.parquet")
    frames = pd.read_parquet(args.frame_root / "frames.parquet")
    frame_embeddings = np.load(args.visual_embedding_root / "frame_embeddings.npy").astype("float32")
    query_embeddings = np.load(args.visual_embedding_root / "query_text_embeddings.npy").astype("float32")
    query_index = pd.DataFrame(read_jsonl(args.visual_embedding_root / "query_index.jsonl"))
    manifest = json.loads((args.visual_embedding_root / "visual_embedding_manifest.json").read_text(encoding="utf-8"))

    if len(frame_index) != len(frame_embeddings):
        raise ValueError("Frame index and embedding count differ.")
    if len(query_index) != len(query_embeddings):
        raise ValueError("Query index and embedding count differ.")
    if "is_label_evidence" not in frames.columns:
        frames["is_label_evidence"] = frames["extraction_strategy"].eq("label_evidence_frame")

    query_pos_by_id = {str(row["query_id"]): pos for pos, row in query_index.reset_index(drop=True).iterrows()}
    frame_pos_by_id = {str(row["frame_id"]): pos for pos, row in frame_index.reset_index(drop=True).iterrows()}
    top_ks = [int(value) for value in args.top_ks.split(",") if value.strip()]

    ranking_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    strategies = ["W0_random_within_clip", "W1_visual_text_frame_within_clip", "W2_structured_label_oracle"]

    for query in queries.to_dict("records"):
        query_id = str(query["query_id"])
        semantic_filter = query.get("semantic_filter") or {}
        target_clip_id = str(semantic_filter.get("clip_id") or "")
        if not target_clip_id or query_id not in query_pos_by_id:
            continue
        candidates = frames[frames["clip_id"].astype(str).eq(target_clip_id)].copy()
        if candidates.empty:
            continue
        query_vector = query_embeddings[query_pos_by_id[query_id]]
        scores: list[float] = []
        for frame_id in candidates["frame_id"].astype(str).tolist():
            frame_pos = frame_pos_by_id.get(frame_id)
            scores.append(float(frame_embeddings[frame_pos] @ query_vector) if frame_pos is not None else float("-inf"))
        candidates["visual_score"] = scores
        candidates["random_score"] = [
            deterministic_random_score(query_id, str(frame_id)) for frame_id in candidates["frame_id"].tolist()
        ]
        candidates["oracle_score"] = candidates["is_label_evidence"].astype(float)

        ranked_by_strategy = {
            "W0_random_within_clip": candidates.sort_values(
                ["random_score", "frame_id"], ascending=[False, True], kind="mergesort"
            ),
            "W1_visual_text_frame_within_clip": candidates.sort_values(
                ["visual_score", "frame_id"], ascending=[False, True], kind="mergesort"
            ),
            "W2_structured_label_oracle": candidates.sort_values(
                ["oracle_score", "view", "frame_index", "frame_id"],
                ascending=[False, True, True, True],
                kind="mergesort",
            ),
        }

        for strategy, ranked in ranked_by_strategy.items():
            ranked = ranked.reset_index(drop=True)
            metrics = rank_metrics(ranked, top_ks)
            metric_rows.append(
                {
                    "strategy": strategy,
                    "query_id": query_id,
                    "target_clip_id": target_clip_id,
                    "event_class": semantic_filter.get("event_class"),
                    **metrics,
                }
            )
            for rank, row in enumerate(ranked.head(max(top_ks)).to_dict("records"), start=1):
                score_col = {
                    "W0_random_within_clip": "random_score",
                    "W1_visual_text_frame_within_clip": "visual_score",
                    "W2_structured_label_oracle": "oracle_score",
                }[strategy]
                ranking_rows.append(
                    {
                        "strategy": strategy,
                        "query_id": query_id,
                        "rank": rank,
                        "clip_id": row["clip_id"],
                        "frame_id": row["frame_id"],
                        "view": row.get("view"),
                        "frame_index": row.get("frame_index"),
                        "extraction_strategy": row.get("extraction_strategy"),
                        "is_label_evidence": bool(row.get("is_label_evidence")),
                        "score": row.get(score_col),
                    }
                )

    metrics_by_query = pd.DataFrame(metric_rows)
    rankings = pd.DataFrame(ranking_rows)
    summary = summarize(metrics_by_query, top_ks)

    metrics_by_query.to_parquet(args.output_dir / "within_event_metrics_by_query.parquet", index=False)
    rankings.to_parquet(args.output_dir / "within_event_rankings.parquet", index=False)
    summary.to_csv(args.output_dir / "within_event_summary.csv", index=False)

    run_manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "frame_root": str(args.frame_root),
        "visual_embedding_root": str(args.visual_embedding_root),
        "output_dir": str(args.output_dir),
        "embedding_manifest": manifest,
        "strategies": strategies,
        "top_ks": top_ks,
        "counts": {
            "queries": int(metrics_by_query["query_id"].nunique()) if not metrics_by_query.empty else 0,
            "ranking_rows": int(len(rankings)),
        },
        "task_definition": {
            "input": "target clip/session id plus Korean VQA-style event question",
            "candidate_set": "label evidence frames and context distractor frames from the same clip",
            "positive": "frame rows with extraction_strategy=label_evidence_frame",
            "llm_used": False,
        },
    }
    (args.output_dir / "run_manifest.json").write_text(
        json.dumps(run_manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# AI Hub 71953 Within-Event Evidence Selection Summary",
        "",
        f"created_at: `{run_manifest['created_at']}`",
        f"model_key: `{manifest.get('model_key')}`",
        "",
        "| strategy | queries | MRR | Hit@1 | Hit@3 | Hit@5 | P@3 | nDCG@5 | ViewCov@5 | candidates | positives |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        lines.append(
            f"| {row['strategy']} | {row['queries']} | {row['mrr']:.4f} | "
            f"{row.get('hit_at_1', 0.0):.4f} | {row.get('hit_at_3', 0.0):.4f} | "
            f"{row.get('hit_at_5', 0.0):.4f} | {row.get('precision_at_3', 0.0):.4f} | "
            f"{row.get('ndcg_at_5', 0.0):.4f} | {row.get('positive_view_coverage_at_5', 0.0):.4f} | "
            f"{row['candidate_count_mean']:.1f} | {row['positive_count_mean']:.1f} |"
        )
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"output_dir={args.output_dir}")
    print(f"queries={run_manifest['counts']['queries']}")
    for row in summary.to_dict("records"):
        print(
            f"{row['strategy']}: hit@1={row.get('hit_at_1', 0.0):.4f}, "
            f"hit@5={row.get('hit_at_5', 0.0):.4f}, mrr={row['mrr']:.4f}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
