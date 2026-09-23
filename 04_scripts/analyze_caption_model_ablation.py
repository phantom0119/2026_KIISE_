#!/usr/bin/env python3
"""Aggregate the completed caption-model ablation with integrity gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


DEFAULT_ROOT = Path("/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715")
DEFAULT_OUT = Path(__file__).resolve().parents[1] / "paper_assets" / "20260715_caption_model_ablation"
MODELS = ["qwen25vl_7b", "qwen3vl_8b", "qwen35_9b"]
DATASETS = ["522", "meva", "uca"]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def boot(values: np.ndarray, rng: np.random.Generator, draws: int) -> tuple[float, float]:
    indices = rng.integers(0, len(values), size=(draws, len(values)))
    means = values[indices].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def b0_signature(path: Path) -> str:
    frame = pd.read_parquet(path)
    frame = frame[frame.strategy == "B0_metadata_only"].sort_values(
        ["query_id", "rank", "clip_id"], kind="stable"
    )
    payload = frame[["query_id", "rank", "clip_id", "score"]].to_csv(index=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def markdown_table(frame: pd.DataFrame) -> list[str]:
    lines = ["| dataset | model | scoring | B2 | B4 | B5 |", "|---|---|---|---:|---:|---:|"]
    pivot = frame[frame.strategy.isin(["B2_vector_only", "B4_prefilter_vector", "B5_hybrid"])].pivot_table(
        index=["dataset", "model", "scoring"], columns="strategy", values="ndcg_at_10"
    ).reset_index()
    for row in pivot.to_dict("records"):
        lines.append(
            f"| {row['dataset']} | {row['model']} | {row['scoring']} | "
            f"{row['B2_vector_only']:.4f} | {row['B4_prefilter_vector']:.4f} | "
            f"{row['B5_hybrid']:.4f} |"
        )
    return lines


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260715)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    audits, caption_stats, summaries, per_query = [], [], [], []
    invariant_rows = []
    for dataset in DATASETS:
        reference_hashes = None
        reference_b0 = None
        reference_queries = None
        for model in MODELS:
            lane = args.root / model / dataset
            audit = json.loads((lane / "captions" / "caption_output_audit.json").read_text())
            audits.append(
                {
                    "model": model,
                    "dataset": dataset,
                    "integrity_pass": audit.get("integrity_pass", audit["overall_pass"]),
                    "quality_advisory_pass": audit.get(
                        "quality_advisory_pass", audit["checks"]["no_token_limit_hits"]
                    ),
                }
            )
            caption_stats.append({"model": model, "dataset": dataset, **audit["caption_stats"]})
            summary = pd.read_csv(lane / "results" / "b0_b5" / "metrics_dual_summary.csv")
            summary.insert(0, "dataset", dataset)
            summary.insert(1, "model", model)
            summaries.append(summary)
            query_metrics = pd.read_parquet(lane / "results" / "b0_b5" / "metrics_by_query_dual.parquet")
            query_metrics.insert(0, "dataset", dataset)
            query_metrics.insert(1, "model", model)
            per_query.append(query_metrics)

            invariant_files = ["clips.parquet", "metadata.parquet", "queries.jsonl", "qrels.tsv", "qrels_semantic.tsv"]
            hashes = {name: sha256_file(lane / "canonical" / name) for name in invariant_files}
            b0 = b0_signature(lane / "results" / "b0_b5" / "retrieval_results.parquet")
            query_hash = sha256_file(lane / "embeddings" / "bge-m3" / "query_embeddings.npy")
            if reference_hashes is None:
                reference_hashes, reference_b0, reference_queries = hashes, b0, query_hash
            invariant_rows.append(
                {
                    "dataset": dataset,
                    "model": model,
                    "canonical_non_document_equal": hashes == reference_hashes,
                    "b0_ranking_equal": b0 == reference_b0,
                    "query_embeddings_equal": query_hash == reference_queries,
                }
            )

    audit_frame = pd.DataFrame(audits)
    invariant_frame = pd.DataFrame(invariant_rows)
    summary_frame = pd.concat(summaries, ignore_index=True)
    query_frame = pd.concat(per_query, ignore_index=True)
    caption_frame = pd.DataFrame(caption_stats)
    audit_frame.to_csv(args.output_dir / "caption_audit_matrix.csv", index=False)
    invariant_frame.to_csv(args.output_dir / "invariant_gates.csv", index=False)
    summary_frame.to_csv(args.output_dir / "retrieval_metrics_all_models.csv", index=False)
    caption_frame.to_csv(args.output_dir / "caption_generation_stats.csv", index=False)

    pairwise = []
    baseline = query_frame[query_frame.model == "qwen25vl_7b"]
    keys = ["dataset", "query_id", "scoring", "strategy"]
    for model in ["qwen3vl_8b", "qwen35_9b"]:
        candidate = query_frame[query_frame.model == model]
        paired = baseline[keys + ["ndcg_at_10"]].merge(
            candidate[keys + ["ndcg_at_10"]], on=keys, suffixes=("_base", "_candidate"),
            validate="one_to_one"
        )
        paired["delta"] = paired["ndcg_at_10_candidate"] - paired["ndcg_at_10_base"]
        for (dataset, scoring, strategy), group in paired.groupby(
            ["dataset", "scoring", "strategy"], sort=False
        ):
            values = group.delta.to_numpy()
            lo, hi = boot(values, rng, args.bootstrap)
            pairwise.append(
                {
                    "candidate": model,
                    "baseline": "qwen25vl_7b",
                    "dataset": dataset,
                    "scoring": scoring,
                    "strategy": strategy,
                    "queries": len(values),
                    "mean_delta_ndcg10": float(values.mean()),
                    "ci_lo": lo,
                    "ci_hi": hi,
                    "wins": int((values > 0).sum()),
                    "ties": int((values == 0).sum()),
                    "losses": int((values < 0).sum()),
                }
            )
    pairwise_frame = pd.DataFrame(pairwise)
    pairwise_frame.to_csv(args.output_dir / "paired_model_deltas.csv", index=False)

    overall_pass = bool(
        audit_frame["integrity_pass"].all()
        and invariant_frame[
            ["canonical_non_document_equal", "b0_ranking_equal", "query_embeddings_equal"]
        ].all().all()
    )
    verdict = {
        "overall_pass": overall_pass,
        "caption_integrity_audits_pass": bool(audit_frame["integrity_pass"].all()),
        "caption_quality_advisories_pass": bool(audit_frame["quality_advisory_pass"].all()),
        "token_limit_hit_count": int(caption_frame["token_limit_hit_count"].sum()),
        "invariant_gates_pass": bool(
            invariant_frame[
                ["canonical_non_document_equal", "b0_ranking_equal", "query_embeddings_equal"]
            ].all().all()
        ),
        "primary_estimand": "paired per-query delta nDCG@10 versus Qwen2.5-VL",
        "selection_rule": (
            "Report each dataset and scoring regime separately; do not declare a universal winner "
            "unless the same model improves B2 semantic nDCG@10 in all three datasets."
        ),
    }
    (args.output_dir / "VERDICT.json").write_text(json.dumps(verdict, indent=2))

    lines = [
        "# Caption Model Ablation Results",
        "",
        f"Integrity gates: **{'PASS' if overall_pass else 'FAIL'}**",
        f"Token-limit quality advisory: **{'PASS' if audit_frame['quality_advisory_pass'].all() else 'WARN'}** ",
        f"({int(caption_frame['token_limit_hit_count'].sum())} captions reached the shared 110-token cap)",
        "",
        "## Retrieval",
        "",
        *markdown_table(summary_frame),
        "",
        "## Paired deltas versus Qwen2.5-VL",
        "",
        "| candidate | dataset | scoring | strategy | delta | 95% CI | W/T/L |",
        "|---|---|---|---|---:|---:|---:|",
    ]
    for row in pairwise_frame[
        pairwise_frame.strategy.isin(["B2_vector_only", "B4_prefilter_vector", "B5_hybrid"])
    ].to_dict("records"):
        lines.append(
            f"| {row['candidate']} | {row['dataset']} | {row['scoring']} | {row['strategy']} | "
            f"{row['mean_delta_ndcg10']:+.4f} | [{row['ci_lo']:+.4f}, {row['ci_hi']:+.4f}] | "
            f"{row['wins']}/{row['ties']}/{row['losses']} |"
        )
    (args.output_dir / "CAPTION_MODEL_ABLATION_RESULTS.md").write_text("\n".join(lines) + "\n")
    print(json.dumps(verdict, indent=2))
    return 0 if overall_pass else 2


if __name__ == "__main__":
    raise SystemExit(main())
