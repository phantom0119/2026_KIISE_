#!/usr/bin/env python3
"""Independently verify treatment assignment and ablation-grid integrity.

This verifier intentionally does not import project retrieval or metric helpers.
It complements the ranking/metric verifier with gates for configuration coverage,
metadata-filter treatment integrity, qrel construction, latency repetitions, and
reported paired deltas.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260717_joint_optimization_validation"
DEFAULT_CANONICAL = Path(
    "/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/"
    "qwen35_9b/522/canonical"
)
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "2026_KIISE"
    / "paper_assets"
    / "20260717_ablation_agent_crosscheck"
    / "treatment_integrity_verification.json"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    return parser.parse_args()


def load_positive_sets(path: Path) -> dict[str, set[str]]:
    frame = pd.read_csv(path, sep="\t", dtype=str)
    return {
        str(query_id): set(group["target_id"].astype(str))
        for query_id, group in frame.groupby("query_id", sort=False)
    }


def bh_adjust(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    ranked = values[order]
    adjusted = np.minimum.accumulate(
        (ranked * len(values) / np.arange(1, len(values) + 1))[::-1]
    )[::-1]
    result = np.empty_like(adjusted)
    result[order] = np.clip(adjusted, 0.0, 1.0)
    return result


def main() -> int:
    args = parse_args()
    root = args.root
    canonical = args.canonical_root

    queries = [
        json.loads(line)
        for line in (canonical / "queries.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    qids = [str(row["query_id"]) for row in queries]
    metadata = pd.read_parquet(canonical / "metadata.parquet")
    rankings = pd.read_parquet(root / "rankings.parquet")
    metrics = pd.read_parquet(root / "per_query_metrics.parquet")
    summary = pd.read_csv(root / "configuration_summary.csv")
    latency = pd.read_parquet(root / "latency_trials.parquet")
    comparisons = pd.read_csv(root / "paired_bootstrap_comparisons.csv")
    fidelity = pd.read_csv(root / "task_fidelity_corrected.csv")

    wide = metadata.pivot(index="clip_id", columns="facet_name", values="facet_value")
    allowed: dict[str, set[str]] = {}
    for row in queries:
        mask = np.ones(len(wide), dtype=bool)
        for key, value in dict(row.get("metadata_filter") or {}).items():
            mask &= wide[key].astype(str).to_numpy() == str(value)
        allowed[str(row["query_id"])] = set(wide.index[mask].astype(str))

    strict = load_positive_sets(canonical / "qrels.tsv")
    semantic = load_positive_sets(canonical / "qrels_semantic.tsv")

    representations = ["caption", "representative_frame", "multi_frame", "dual"]
    plans = {
        "caption": ["B2_vector", "B3_postfilter", "B4_prefilter", "B5_lexical_vector_hybrid"],
        "representative_frame": ["B2_vector", "B3_postfilter", "B4_prefilter"],
        "multi_frame": ["B2_vector", "B3_postfilter", "B4_prefilter"],
        "dual": ["B2_vector", "B3_postfilter", "B4_prefilter"],
    }
    indexes = [
        "flat",
        "hnsw_ef64",
        "hnsw_ef256",
        "ivfflat_np8",
        "ivfflat_np32",
        "ivfpq6_np8",
        "ivfpq6_np32",
    ]
    expected_configs = {
        f"{representation}__{plan}__{index}"
        for representation in representations
        for plan in plans[representation]
        for index in indexes
    }
    observed_configs = set(summary["config"].astype(str))

    checks: list[dict[str, object]] = []

    def add(gate: str, passed: bool, **evidence: object) -> None:
        checks.append({"gate": gate, "pass": bool(passed), **evidence})

    add(
        "exact_compatible_configuration_set",
        observed_configs == expected_configs,
        expected=len(expected_configs),
        observed=len(observed_configs),
        missing=sorted(expected_configs - observed_configs),
        unexpected=sorted(observed_configs - expected_configs),
    )
    metric_counts = metrics.groupby(["config", "scoring"])["query_id"].agg(["size", "nunique"])
    add(
        "complete_metric_cells",
        bool((metric_counts["size"] == len(qids)).all() and (metric_counts["nunique"] == len(qids)).all()),
        cells=len(metric_counts),
        expected_cells=len(expected_configs) * 2,
        min_rows=int(metric_counts["size"].min()),
        max_rows=int(metric_counts["size"].max()),
    )

    ranked = rankings.copy()
    parts = ranked["config"].str.split("__", n=2, expand=True)
    ranked["representation"] = parts[0]
    ranked["search_plan"] = parts[1]
    filtered = ranked[ranked["search_plan"].isin(["B3_postfilter", "B4_prefilter", "B5_lexical_vector_hybrid"])]
    violations = [
        (str(row.config), str(row.query_id), str(row.clip_id))
        for row in filtered.itertuples(index=False)
        if str(row.clip_id) not in allowed[str(row.query_id)]
    ]
    add(
        "filtered_rankings_obey_metadata_predicate",
        len(violations) == 0,
        checked_rows=len(filtered),
        violations=len(violations),
        examples=violations[:5],
    )

    qrel_mismatches = []
    nonoracle = []
    for qid in qids:
        expected_strict = semantic.get(qid, set()) & allowed[qid]
        if strict.get(qid, set()) != expected_strict:
            qrel_mismatches.append(qid)
        nonoracle.append(allowed[qid] != strict.get(qid, set()))
    add(
        "strict_qrels_equal_semantic_intersection_metadata",
        len(qrel_mismatches) == 0,
        mismatches=qrel_mismatches,
    )
    add(
        "metadata_candidate_sets_are_not_qrel_oracle_sets",
        all(nonoracle),
        nonoracle_queries=int(sum(nonoracle)),
        total_queries=len(qids),
        mean_candidate_count=float(np.mean([len(allowed[qid]) for qid in qids])),
        mean_strict_positive_count=float(np.mean([len(strict.get(qid, set())) for qid in qids])),
    )

    b2 = ranked[ranked["search_plan"].eq("B2_vector")]
    b2_off_predicate = sum(
        str(row.clip_id) not in allowed[str(row.query_id)] for row in b2.itertuples(index=False)
    )
    add(
        "unfiltered_anchor_is_distinct_from_prefilter_treatment",
        b2_off_predicate > 0,
        off_predicate_rows=int(b2_off_predicate),
        checked_rows=len(b2),
    )

    latency_counts = latency.groupby(["config", "query_id", "repeat"]).size()
    add(
        "complete_latency_repetitions",
        len(latency_counts) == len(expected_configs) * len(qids) * 10 and bool((latency_counts == 1).all()),
        observed_trials=len(latency),
        expected_trials=len(expected_configs) * len(qids) * 10,
        unique_cells=len(latency_counts),
    )

    recomputed = (
        metrics.groupby(["config", "representation", "search_plan", "index", "scoring"], sort=False)
        .agg(ndcg_at_10=("ndcg_at_10", "mean"), mrr=("mrr", "mean"), recall_at_10=("recall_at_10", "mean"))
        .reset_index()
    )
    merged = summary.merge(
        recomputed,
        on=["config", "representation", "search_plan", "index", "scoring"],
        suffixes=("_reported", "_recomputed"),
        validate="one_to_one",
    )
    metric_error = max(
        float(np.max(np.abs(merged[f"{name}_reported"] - merged[f"{name}_recomputed"])))
        for name in ("ndcg_at_10", "mrr", "recall_at_10")
    )
    add("summary_matches_per_query_metrics", metric_error < 1e-12, max_abs_error=metric_error)

    metric_lookup = metrics.set_index(["config", "scoring", "query_id"])["ndcg_at_10"].sort_index()
    delta_errors = []
    for row in comparisons.itertuples(index=False):
        candidate = metric_lookup.loc[(row.candidate, row.scoring)].reindex(qids).to_numpy(float)
        baseline = metric_lookup.loc[(row.baseline, row.scoring)].reindex(qids).to_numpy(float)
        delta_errors.append(abs(float(np.mean(candidate - baseline)) - float(row.mean_delta)))
    add(
        "paired_mean_deltas_match_raw_metrics",
        max(delta_errors) < 1e-12,
        comparisons=len(delta_errors),
        max_abs_error=float(max(delta_errors)),
    )

    bh_errors = []
    for (_family, _scoring), group in comparisons.groupby(["family", "scoring"], sort=False):
        expected_query = bh_adjust(group["p_query"].to_numpy(float))
        expected_cluster = bh_adjust(group["p_cluster"].to_numpy(float))
        bh_errors.extend(np.abs(expected_query - group["q_query_bh"].to_numpy(float)).tolist())
        bh_errors.extend(np.abs(expected_cluster - group["q_cluster_bh"].to_numpy(float)).tolist())
    add(
        "bh_adjustments_match_independent_recalculation",
        max(bh_errors) < 1e-12,
        max_abs_error=float(max(bh_errors)),
    )

    meva_comparisons = pd.read_csv(root / "meva_same_encoder_control" / "paired_bootstrap.csv")
    meva_bh_errors = []
    for (_family, _scoring), group in meva_comparisons.groupby(["family", "scoring"], sort=False):
        expected_query = bh_adjust(group["p_query"].to_numpy(float))
        expected_cluster = bh_adjust(group["p_cluster"].to_numpy(float))
        meva_bh_errors.extend(np.abs(expected_query - group["q_query_bh"].to_numpy(float)).tolist())
        meva_bh_errors.extend(np.abs(expected_cluster - group["q_cluster_bh"].to_numpy(float)).tolist())
    add(
        "meva_bh_adjustments_match_independent_recalculation",
        max(meva_bh_errors) < 1e-12,
        max_abs_error=float(max(meva_bh_errors)),
    )

    flat_fidelity = fidelity[fidelity["index"].eq("flat")]["task_recall_to_exact_at_10"]
    add(
        "flat_task_fidelity_is_exact_anchor",
        len(flat_fidelity) == sum(len(value) for value in plans.values())
        and bool(np.allclose(flat_fidelity, 1.0, atol=0.0, rtol=0.0)),
        flat_configs=len(flat_fidelity),
        min_fidelity=float(flat_fidelity.min()),
        max_fidelity=float(flat_fidelity.max()),
    )

    passed = sum(bool(row["pass"]) for row in checks)
    output = {
        "overall_pass": passed == len(checks),
        "passed": passed,
        "total": len(checks),
        "checks": checks,
        "interpretation": (
            "These gates validate executed treatment assignment and artifact consistency; "
            "they do not establish external validity, causal transportability, or preregistration."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: output[key] for key in ("overall_pass", "passed", "total")}, indent=2))
    return 0 if output["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
