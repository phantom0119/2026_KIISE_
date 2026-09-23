#!/usr/bin/env python3
"""Independently verify the Qwen-aligned C1/C2 controlled injection outputs."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROOT = (
    PROJECT_ROOT
    / "2026_KIISE"
    / "paper_assets"
    / "20260717_ablation_agent_crosscheck"
    / "qwen_aligned_circularity"
)
DEFAULT_CANONICAL = Path(
    "/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/"
    "qwen35_9b/522/canonical"
)
DEFAULT_JOINT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260717_joint_optimization_validation"
LABEL_PHRASES = {
    "parked_vehicle": "This clip shows a vehicle parked at the roadside.",
    "dense_frame": "This clip shows a very crowded scene with many vehicles at once.",
    "multiple_buses": "This clip shows two or more buses in view.",
    "stopped_vehicles": "This clip shows vehicles stopped in the roadway.",
    "two_plus_bikes": "This clip shows two or more bicycles or motorbikes in view.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--joint-root", type=Path, default=DEFAULT_JOINT)
    return parser.parse_args()


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while value := handle.read(chunk):
            digest.update(value)
    return digest.hexdigest()


def positive_sets(path: Path) -> dict[str, set[str]]:
    frame = pd.read_csv(path, sep="\t")
    return {
        str(query_id): set(group["target_id"].astype(str))
        for query_id, group in frame.groupby("query_id", sort=False)
    }


def metrics(result: list[str], positives: set[str]) -> dict[str, float]:
    gains = np.asarray([1.0 if value in positives else 0.0 for value in result[:10]])
    discounts = 1.0 / np.log2(np.arange(2, len(gains) + 2))
    dcg = float(np.sum(gains * discounts))
    count = min(10, len(positives))
    idcg = float(np.sum(1.0 / np.log2(np.arange(2, count + 2)))) if count else 0.0
    ranks = [index for index, value in enumerate(result, start=1) if value in positives]
    return {
        "ndcg_at_10": dcg / idcg if idcg else 0.0,
        "mrr": 1.0 / ranks[0] if ranks else 0.0,
        "recall_at_10": float(sum(value in positives for value in result[:10]) / len(positives)) if positives else 0.0,
    }


def bootstrap(delta: np.ndarray, clusters: np.ndarray, reps: int, seed: int) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    query_idx = rng.integers(0, len(delta), size=(reps, len(delta)))
    query_values = delta[query_idx].mean(axis=1)
    unique, inverse = np.unique(clusters, return_inverse=True)
    sizes = np.bincount(inverse)
    means = np.asarray([delta[inverse == index].mean() for index in range(len(unique))])
    cluster_idx = rng.integers(0, len(unique), size=(reps, len(unique)))
    cluster_values = (means[cluster_idx] * sizes[cluster_idx]).sum(axis=1) / sizes[cluster_idx].sum(axis=1)
    return {
        "mean_delta": float(delta.mean()),
        "query_ci_lo": float(np.quantile(query_values, 0.025)),
        "query_ci_hi": float(np.quantile(query_values, 0.975)),
        "cluster_ci_lo": float(np.quantile(cluster_values, 0.025)),
        "cluster_ci_hi": float(np.quantile(cluster_values, 0.975)),
    }


def main() -> int:
    args = parse_args()
    root = args.root
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    documents = pd.read_parquet(args.canonical_root / "documents.parquet").reset_index(drop=True)
    full_documents = pd.read_parquet(root / "full_contaminated_documents.parquet").reset_index(drop=True)
    queries = [
        json.loads(line)
        for line in (args.canonical_root / "queries.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    strict = positive_sets(args.canonical_root / "qrels.tsv")
    semantic = positive_sets(args.canonical_root / "qrels_semantic.tsv")
    qrels = {"strict": strict, "semantic": semantic}
    per_query = pd.read_parquet(root / "per_query_metrics.parquet")
    summary = pd.read_csv(root / "summary.csv")
    contrasts = pd.read_csv(root / "contrasts.csv")
    rankings = pd.read_parquet(root / "rankings_semantic.parquet")
    clean = np.load(root / "clean_document_embeddings.npy")
    full = np.load(root / "full_document_embeddings.npy")
    qvecs = np.load(root / "query_embeddings.npy")
    doc_index = pd.read_parquet(
        PROJECT_ROOT
        / "Datasets"
        / "processed"
        / "aihub_522_intersection"
        / "20260710"
        / "embeddings_qwen3vl2b_unified_qwen35captions"
        / "document_index.parquet"
    )
    clip_ids = doc_index["clip_id"].astype(str).to_numpy()

    checks: list[dict[str, object]] = []

    def add(gate: str, passed: bool, **evidence: object) -> None:
        checks.append({"gate": gate, "pass": bool(passed), **evidence})

    add(
        "input_hash_alignment",
        manifest["hashes"]["queries"] == sha256_file(args.canonical_root / "queries.jsonl")
        and manifest["hashes"]["qrels"] == sha256_file(args.canonical_root / "qrels.tsv")
        and manifest["hashes"]["qrels_semantic"] == sha256_file(args.canonical_root / "qrels_semantic.tsv"),
    )
    add(
        "embedding_shape_finite_norm",
        clean.shape == (3000, 2048)
        and full.shape == (3000, 2048)
        and qvecs.shape == (85, 2048)
        and np.isfinite(clean).all()
        and np.isfinite(full).all()
        and np.isfinite(qvecs).all()
        and max(float(np.max(np.abs(np.linalg.norm(value, axis=1) - 1))) for value in (clean, full, qvecs)) < 5e-3,
        shapes=[list(clean.shape), list(full.shape), list(qvecs.shape)],
    )
    add(
        "no_token_truncation",
        all(
            details.get("over_model_max", 0) == 0
            for details in manifest["token_lengths"].values()
            if isinstance(details, dict)
        ),
        token_lengths=manifest["token_lengths"],
    )

    by_definition: dict[str, set[str]] = {}
    for query in queries:
        definition = str(query["relevance_def"])
        values = semantic[str(query["query_id"])]
        by_definition.setdefault(definition, values)
        if by_definition[definition] != values:
            raise AssertionError("Semantic qrels vary within definition")
    expected_full = []
    edge_count = 0
    for row in documents.itertuples(index=False):
        additions = [
            LABEL_PHRASES[definition]
            for definition, values in by_definition.items()
            if str(row.clip_id) in values
        ]
        edge_count += len(additions)
        expected_full.append(" ".join([str(row.text or ""), *additions]).strip())
    add(
        "full_documents_exact_single_treatment",
        expected_full == full_documents["text"].astype(str).tolist()
        and edge_count == int(manifest["injected_label_edges"]),
        injected_edges=edge_count,
    )

    grouped_rankings = {
        (condition, qid): group.sort_values("rank")["clip_id"].astype(str).tolist()
        for (condition, qid), group in rankings.groupby(["condition", "query_id"], sort=False)
    }
    metric_errors = []
    score_by_condition = {"qwen_clean": qvecs @ clean.T, "qwen_full_contamination": qvecs @ full.T}
    for condition, scores in score_by_condition.items():
        for query_pos, query in enumerate(queries):
            qid = str(query["query_id"])
            order = sorted(
                ((str(clip_ids[index]), float(scores[query_pos, index])) for index in range(len(clip_ids))),
                key=lambda pair: (-pair[1], pair[0]),
            )[:100]
            result = [clip_id for clip_id, _ in order]
            add_key = (condition, qid)
            if grouped_rankings.get(add_key) != result:
                metric_errors.append(float("inf"))
                continue
            experiment = "C1" if condition == "qwen_clean" else "C2"
            if condition == "qwen_clean":
                experiment = "C1"
            for scoring in ("strict", "semantic"):
                expected = metrics(result, qrels[scoring][qid])
                observed = per_query[
                    per_query["experiment"].eq(experiment)
                    & per_query["condition"].eq(condition)
                    & per_query["scoring"].eq(scoring)
                    & per_query["query_id"].eq(qid)
                ].iloc[0]
                metric_errors.extend(abs(expected[name] - float(observed[name])) for name in expected)
    add(
        "dense_rankings_and_metrics_independent_recompute",
        max(metric_errors) < 1e-12,
        max_abs_error=float(max(metric_errors)),
    )

    oracle = per_query[per_query["condition"].eq("oracle_qrel_filter")]
    add(
        "oracle_structural_upper_bound",
        len(oracle) == 85 * 2 and bool(np.allclose(oracle["ndcg_at_10"], 1.0, atol=0, rtol=0)),
        rows=len(oracle),
    )
    semantic_oracle_violations = 0
    for query in queries:
        qid = str(query["query_id"])
        values = grouped_rankings[("oracle_qrel_filter", qid)]
        semantic_oracle_violations += sum(value not in semantic[qid] for value in values)
    add("oracle_rankings_contain_only_qrels", semantic_oracle_violations == 0, violations=semantic_oracle_violations)

    summary_errors = []
    for row in summary.itertuples(index=False):
        values = per_query[
            per_query["experiment"].eq(row.experiment)
            & per_query["condition"].eq(row.condition)
            & per_query["scoring"].eq(row.scoring)
        ]["ndcg_at_10"]
        if row.condition == "random_same_selectivity_mean":
            continue
        summary_errors.append(abs(float(values.mean()) - float(row.ndcg_at_10)))
    add("summary_matches_per_query", max(summary_errors) < 1e-12, max_abs_error=float(max(summary_errors)))

    qids = [str(row["query_id"]) for row in queries]
    clusters = np.asarray([f"{row['difficulty']}|{row['relevance_def']}" for row in queries], dtype=object)
    contrast_errors = []
    for row in contrasts.itertuples(index=False):
        if row.control == "random_same_selectivity_mean":
            continue
        frame = per_query[
            per_query["experiment"].eq(row.experiment) & per_query["scoring"].eq(row.scoring)
        ].pivot(index="query_id", columns="condition", values="ndcg_at_10").reindex(qids)
        delta = frame[row.treatment].to_numpy(float) - frame[row.control].to_numpy(float)
        scoring_pos = 0 if row.scoring == "strict" else 1
        expected = bootstrap(delta, clusters, int(manifest["bootstrap_reps"]), int(manifest["seed"]) + 500 + scoring_pos)
        contrast_errors.extend(abs(expected[name] - float(getattr(row, name))) for name in expected)
    add(
        "contrast_bootstrap_independent_recompute",
        max(contrast_errors) < 1e-12,
        max_abs_error=float(max(contrast_errors)),
    )

    joint = pd.read_csv(args.joint_root / "configuration_summary.csv")
    joint_anchor = joint[
        joint["config"].eq("caption__B2_vector__flat")
    ].set_index("scoring")["ndcg_at_10"]
    qwen_clean_summary = summary[
        summary["experiment"].eq("C1") & summary["condition"].eq("qwen_clean")
    ].set_index("scoring")["ndcg_at_10"]
    anchor_error = float(np.max(np.abs(joint_anchor.loc[["strict", "semantic"]] - qwen_clean_summary.loc[["strict", "semantic"]])))
    add("clean_qwen_matches_joint_grid_anchor", anchor_error < 1e-12, max_abs_error=anchor_error)

    passed = sum(bool(check["pass"]) for check in checks)
    result = {
        "overall_pass": passed == len(checks),
        "passed": passed,
        "total": len(checks),
        "checks": checks,
        "scope": "Independent arithmetic, treatment-text, rank, bootstrap, and anchor verification.",
    }
    (root / "independent_verification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: result[key] for key in ("overall_pass", "passed", "total")}, indent=2))
    return 0 if result["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
