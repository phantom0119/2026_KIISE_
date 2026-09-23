#!/usr/bin/env python3
"""Independently verify joint image-caption materialization and retrieval outputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
DEFAULT_CANONICAL = Path(
    "/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/"
    "qwen35_9b/522/canonical"
)
DEFAULT_MATCHED = DATA_ROOT / "embeddings_qwen3vl2b_joint_image_caption_qwen35captions"
DEFAULT_SHUFFLED = DATA_ROOT / "embeddings_qwen3vl2b_joint_image_caption_qwen35captions_shuffled"
DEFAULT_CONTROLS = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260717_joint_image_caption_controls"
)
DEFAULT_GRID = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260717_joint_image_caption_validation"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--matched-root", type=Path, default=DEFAULT_MATCHED)
    parser.add_argument("--shuffled-root", type=Path, default=DEFAULT_SHUFFLED)
    parser.add_argument("--controls-root", type=Path, default=DEFAULT_CONTROLS)
    parser.add_argument("--grid-root", type=Path, default=DEFAULT_GRID)
    return parser.parse_args()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def positive_sets(path: Path) -> dict[str, set[str]]:
    frame = pd.read_csv(path, sep="\t")
    return {
        str(query_id): set(group["target_id"].astype(str))
        for query_id, group in frame.groupby("query_id", sort=False)
    }


def ndcg_at_10(ranking: list[str], positives: set[str]) -> float:
    top = ranking[:10]
    gains = np.array([1.0 if clip in positives else 0.0 for clip in top], dtype=float)
    discounts = 1.0 / np.log2(np.arange(2, len(top) + 2))
    dcg = float(np.sum(gains * discounts))
    ideal_n = min(10, len(positives))
    if not ideal_n:
        return 0.0
    idcg = float(np.sum(1.0 / np.log2(np.arange(2, ideal_n + 2))))
    return dcg / idcg


def main() -> int:
    args = parse_args()
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, **details: Any) -> None:
        checks.append({"check": name, "pass": bool(passed), **details})

    clips = pd.read_parquet(args.canonical_root / "clips.parquet").reset_index(drop=True)
    metadata = pd.read_parquet(args.canonical_root / "metadata.parquet")
    queries = load_jsonl(args.canonical_root / "queries.jsonl")
    query_ids = [str(row["query_id"]) for row in queries]
    strict = positive_sets(args.canonical_root / "qrels.tsv")
    semantic = positive_sets(args.canonical_root / "qrels_semantic.tsv")

    matched_index = pd.read_parquet(args.matched_root / "joint_index.parquet")
    shuffled_index = pd.read_parquet(args.shuffled_root / "joint_index.parquet")
    matched_vectors = np.load(args.matched_root / "joint_embeddings.npy", mmap_mode="r")
    shuffled_vectors = np.load(args.shuffled_root / "joint_embeddings.npy", mmap_mode="r")
    expected_shape = (len(clips), 2048)
    check(
        "materialized_shapes",
        tuple(matched_vectors.shape) == expected_shape
        and tuple(shuffled_vectors.shape) == expected_shape,
        matched_shape=list(matched_vectors.shape),
        shuffled_shape=list(shuffled_vectors.shape),
    )
    check(
        "materialized_finite",
        bool(np.isfinite(matched_vectors).all() and np.isfinite(shuffled_vectors).all()),
    )
    matched_norms = np.linalg.norm(matched_vectors, axis=1)
    shuffled_norms = np.linalg.norm(shuffled_vectors, axis=1)
    check(
        "materialized_l2_norm",
        float(np.max(np.abs(matched_norms - 1.0))) <= 5e-3
        and float(np.max(np.abs(shuffled_norms - 1.0))) <= 5e-3,
        matched_min=float(matched_norms.min()),
        matched_max=float(matched_norms.max()),
        shuffled_min=float(shuffled_norms.min()),
        shuffled_max=float(shuffled_norms.max()),
    )
    check(
        "matched_pairing",
        len(matched_index) == len(clips) and matched_index["caption_match"].astype(bool).all(),
        matched=int(matched_index["caption_match"].astype(bool).sum()),
    )
    check(
        "shuffled_derangement",
        len(shuffled_index) == len(clips)
        and not shuffled_index["caption_match"].astype(bool).any()
        and shuffled_index["caption_clip_id"].astype(str).nunique() == len(clips),
        fixed_points=int(shuffled_index["caption_match"].astype(bool).sum()),
        unique_caption_sources=int(shuffled_index["caption_clip_id"].astype(str).nunique()),
    )
    canonical_order = clips["clip_id"].astype(str).tolist()
    check(
        "materialized_clip_order",
        matched_index["clip_id"].astype(str).tolist() == canonical_order
        and shuffled_index["clip_id"].astype(str).tolist() == canonical_order,
    )
    matched_manifest = json.loads((args.matched_root / "embedding_manifest.json").read_text())
    shuffled_manifest = json.loads((args.shuffled_root / "embedding_manifest.json").read_text())
    check(
        "frozen_encoder_settings",
        matched_manifest["model_family"] == "Qwen3-VL-Embedding-2B"
        and shuffled_manifest["model_family"] == "Qwen3-VL-Embedding-2B"
        and matched_manifest["instruction"] == "Represent the user's input."
        and shuffled_manifest["instruction"] == "Represent the user's input."
        and matched_manifest["image_settings"]["attention"] == "flash_attention_2"
        and shuffled_manifest["image_settings"]["attention"] == "flash_attention_2",
    )

    controls_metrics = pd.read_parquet(args.controls_root / "per_query_metrics.parquet")
    controls_quality = pd.read_csv(args.controls_root / "quality_summary.csv")
    controls_comparisons = pd.read_csv(args.controls_root / "paired_bootstrap_comparisons.csv")
    check(
        "control_cell_counts",
        len(controls_metrics) == 4 * len(query_ids) * 2
        and controls_metrics["representation"].nunique() == 4
        and controls_metrics.groupby(["representation", "scoring"]).size().eq(len(query_ids)).all(),
        metric_rows=len(controls_metrics),
    )
    recomputed_control = (
        controls_metrics.groupby(["representation", "scoring"], sort=False)["ndcg_at_10"]
        .mean()
        .sort_index()
    )
    reported_control = (
        controls_quality.set_index(["representation", "scoring"])["ndcg_at_10"].sort_index()
    )
    check(
        "control_summary_recomputed",
        float(np.max(np.abs(recomputed_control.to_numpy() - reported_control.to_numpy()))) < 1e-12,
    )
    joint_control_delta = controls_comparisons[
        controls_comparisons["candidate"].eq("joint_matched")
        & controls_comparisons["baseline"].eq("caption")
        & controls_comparisons["scoring"].eq("semantic")
    ].iloc[0]
    per_query_joint = controls_metrics[
        controls_metrics["representation"].eq("joint_matched")
        & controls_metrics["scoring"].eq("semantic")
    ].set_index("query_id")
    per_query_caption = controls_metrics[
        controls_metrics["representation"].eq("caption")
        & controls_metrics["scoring"].eq("semantic")
    ].set_index("query_id")
    delta_recomputed = float(
        (
            per_query_joint.loc[query_ids, "ndcg_at_10"]
            - per_query_caption.loc[query_ids, "ndcg_at_10"]
        ).mean()
    )
    check(
        "control_delta_recomputed",
        abs(delta_recomputed - float(joint_control_delta["mean_delta"])) < 1e-12,
        recomputed=delta_recomputed,
        reported=float(joint_control_delta["mean_delta"]),
    )

    controls_rankings = pd.read_parquet(args.controls_root / "rankings.parquet")
    control_joint_rank = controls_rankings[
        controls_rankings["representation"].eq("joint_matched")
    ]
    recomputed_ndcg = []
    for query_id in query_ids:
        ranking = (
            control_joint_rank[control_joint_rank["query_id"].eq(query_id)]
            .sort_values("rank")["clip_id"]
            .astype(str)
            .tolist()
        )
        recomputed_ndcg.append(ndcg_at_10(ranking, semantic[query_id]))
    reported_joint_ndcg = controls_quality[
        controls_quality["representation"].eq("joint_matched")
        & controls_quality["scoring"].eq("semantic")
    ]["ndcg_at_10"].iloc[0]
    check(
        "raw_ranking_ndcg_recomputed",
        abs(float(np.mean(recomputed_ndcg)) - float(reported_joint_ndcg)) < 1e-12,
        recomputed=float(np.mean(recomputed_ndcg)),
        reported=float(reported_joint_ndcg),
    )

    grid_manifest = json.loads((args.grid_root / "manifest.json").read_text())
    grid_metrics = pd.read_parquet(args.grid_root / "per_query_metrics.parquet")
    grid_rankings = pd.read_parquet(args.grid_root / "rankings.parquet")
    grid_summary = pd.read_csv(args.grid_root / "configuration_summary.csv")
    configs = grid_summary["config"].drop_duplicates().astype(str)
    joint_configs = configs[configs.str.startswith("joint_image_caption__")]
    check(
        "grid_configuration_counts",
        configs.nunique() == 112
        and len(joint_configs) == 21
        and grid_manifest["representations"] == [
            "caption",
            "representative_frame",
            "joint_image_caption",
            "multi_frame",
            "dual",
        ],
        configs=int(configs.nunique()),
        joint_configs=len(joint_configs),
    )
    check(
        "grid_metric_cell_counts",
        len(grid_metrics) == 112 * len(query_ids) * 2
        and grid_metrics.groupby(["config", "scoring"]).size().eq(len(query_ids)).all(),
        metric_rows=len(grid_metrics),
    )
    recomputed_grid = (
        grid_metrics.groupby(["config", "scoring"], sort=False)["ndcg_at_10"].mean().sort_index()
    )
    reported_grid = grid_summary.set_index(["config", "scoring"])["ndcg_at_10"].sort_index()
    check(
        "grid_summary_recomputed",
        float(np.max(np.abs(recomputed_grid.to_numpy() - reported_grid.to_numpy()))) < 1e-12,
    )
    grid_joint_anchor = grid_summary[
        grid_summary["config"].eq("joint_image_caption__B2_vector__flat")
        & grid_summary["scoring"].eq("semantic")
    ]["ndcg_at_10"].iloc[0]
    check(
        "control_grid_joint_anchor_equal",
        abs(float(grid_joint_anchor) - float(reported_joint_ndcg)) < 1e-12,
        controls=float(reported_joint_ndcg),
        grid=float(grid_joint_anchor),
    )

    metadata_wide = metadata.pivot_table(
        index="clip_id", columns="facet_name", values="facet_value", aggfunc="first"
    )
    candidates: dict[str, set[str]] = {}
    for query in queries:
        allowed = metadata_wide
        for name, value in dict(query.get("metadata_filter") or {}).items():
            allowed = allowed[allowed[name].astype(str).eq(str(value))]
        candidates[str(query["query_id"])] = set(allowed.index.astype(str))
    filtered_joint = grid_rankings[
        grid_rankings["config"].str.startswith("joint_image_caption__")
        & (
            grid_rankings["config"].str.contains("__B3_postfilter__")
            | grid_rankings["config"].str.contains("__B4_prefilter__")
        )
    ]
    violations = sum(
        str(row.clip_id) not in candidates[str(row.query_id)]
        for row in filtered_joint.itertuples(index=False)
    )
    check(
        "joint_filtered_rankings_obey_predicates",
        violations == 0,
        rankings=len(filtered_joint),
        violations=violations,
    )

    qrel_logic_ok = all(
        strict[query_id] == semantic[query_id] & candidates[query_id] for query_id in query_ids
    )
    check("strict_qrel_logic", qrel_logic_ok)

    result = {
        "status": "PASS" if all(row["pass"] for row in checks) else "FAIL",
        "checks_passed": sum(row["pass"] for row in checks),
        "checks_total": len(checks),
        "checks": checks,
    }
    output_json = args.grid_root / "joint_image_caption_independent_verification.json"
    output_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Joint image-caption 실험 독립 검산",
        "",
        f"- 최종 상태: **{result['status']}**",
        f"- 통과: {result['checks_passed']}/{result['checks_total']}",
        "",
        "| 검산 | 결과 |",
        "|---|---:|",
    ]
    lines.extend(
        f"| {row['check']} | {'PASS' if row['pass'] else 'FAIL'} |" for row in checks
    )
    (args.grid_root / "JOINT_IMAGE_CAPTION_VERIFICATION_KO.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    print(
        f"[verify] {result['status']} {result['checks_passed']}/{result['checks_total']} "
        f"-> {output_json}",
        flush=True,
    )
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
