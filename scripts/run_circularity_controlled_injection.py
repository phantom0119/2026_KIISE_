#!/usr/bin/env python3
"""Controlled C1/C2 circularity injection on the frozen AIHub-522 workload.

This experiment changes exactly one information path at a time while keeping
the corpus membership, queries, qrels, metric implementation, and ranking
rules fixed.

C1 (qrel-oracle filter injection)
  - clean: global dense BGE-M3 ranking (B2)
  - oracle: restrict candidates to the positive qrel set
  - placebo: uniformly sampled candidate mask with the same cardinality

C2 (qrel-label document injection)
  - clean: original VLM captions
  - contaminated: append the exact relevance clause to documents positive for
    that relevance definition
  - BM25: clean/full primary comparison plus 25/50/75% label-edge dose arms
  - BGE-M3: clean/full corpora and queries re-embedded in one model session

The oracle arms are deliberately tautological upper bounds.  They quantify a
structural evaluation artifact; they are not deployable retrieval methods.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import math
import os
import platform
import shutil
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import faiss
import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from scipy.stats import wilcoxon


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.metrics import evaluate_ranking  # noqa: E402
from vlmdb_workload.retrieval import tokenize  # noqa: E402


DEFAULT_CANONICAL = (
    PROJECT_ROOT
    / "Datasets"
    / "processed"
    / "aihub_522_intersection"
    / "20260710"
    / "canonical_trisource_expanded"
)
DEFAULT_EMBEDDINGS = DEFAULT_CANONICAL.parent / "embeddings_trisource_expanded" / "bge-m3"
DEFAULT_MODEL = PROJECT_ROOT / "Datasets" / "models" / "huggingface" / "BAAI--bge-m3"
DEFAULT_OUTPUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260716_circularity_controlled_injection"

TOP_KS = [1, 5, 10, 20]
MAX_RANK = 100
EXPECTED_COUNTS = {"clips": 3000, "documents": 3000, "queries": 85, "pair_clusters": 25}
SCORINGS = ("strict", "semantic")
DOSES = (0.0, 0.25, 0.50, 0.75, 1.0)

# Exact qrel-definition clauses from build_intersection_trisource_canonical.py.
# A complete sentence is appended; tokenize() makes the prefix harmless and
# retains the exact query clause as the injected lexical signal.
LABEL_PHRASES = {
    "parked_vehicle": "This clip shows a vehicle parked at the roadside.",
    "dense_frame": "This clip shows a very crowded scene with many vehicles at once.",
    "multiple_buses": "This clip shows two or more buses in view.",
    "stopped_vehicles": "This clip shows vehicles stopped in the roadway.",
    "two_plus_bikes": "This clip shows two or more bicycles or motorbikes in view.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--embedding-root", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--device", default="cuda:1")
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--random-filter-reps", type=int, default=1000)
    parser.add_argument("--dose-reps", type=int, default=200)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260716)
    parser.add_argument("--skip-dense-c2", action="store_true", help="Development-only CPU smoke mode")
    parser.add_argument(
        "--resume-dense",
        action="store_true",
        help="Reuse validated C1/C2-BM25 artifacts after an interrupted dense step",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_strings(values: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def package_versions() -> dict[str, str | None]:
    names = [
        "numpy",
        "pandas",
        "pyarrow",
        "faiss-cpu",
        "rank-bm25",
        "scipy",
        "sentence-transformers",
        "torch",
        "transformers",
    ]
    versions: dict[str, str | None] = {}
    for name in names:
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def read_queries(path: Path) -> pd.DataFrame:
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return pd.DataFrame(rows)


def positive_sets(path: Path) -> tuple[pd.DataFrame, dict[str, set[str]]]:
    qrels = pd.read_csv(path, sep="\t")
    positives = qrels[qrels["relevance"] > 0].groupby("query_id", sort=False)["target_id"].apply(set).to_dict()
    return qrels, positives


def bootstrap_ci(values: np.ndarray, draws: int, seed: int) -> tuple[float, float]:
    """Percentile paired query bootstrap for the query-weighted mean."""
    values = np.asarray(values, dtype=np.float64)
    if not len(values):
        return float("nan"), float("nan")
    rng = np.random.default_rng(seed)
    means = np.empty(draws, dtype=np.float64)
    chunk = 2000
    for start in range(0, draws, chunk):
        size = min(chunk, draws - start)
        idx = rng.integers(0, len(values), size=(size, len(values)))
        means[start : start + size] = values[idx].mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def cluster_bootstrap_ci(
    values: np.ndarray, clusters: np.ndarray, draws: int, seed: int
) -> tuple[float, float]:
    """Pair-cluster bootstrap, retaining the query-weighted mean estimand."""
    values = np.asarray(values, dtype=np.float64)
    clusters = np.asarray(clusters, dtype=object)
    unique = np.unique(clusters)
    sums = np.array([values[clusters == cluster].sum() for cluster in unique], dtype=np.float64)
    counts = np.array([(clusters == cluster).sum() for cluster in unique], dtype=np.float64)
    rng = np.random.default_rng(seed)
    means = np.empty(draws, dtype=np.float64)
    chunk = 2000
    for start in range(0, draws, chunk):
        size = min(chunk, draws - start)
        idx = rng.integers(0, len(unique), size=(size, len(unique)))
        means[start : start + size] = sums[idx].sum(axis=1) / counts[idx].sum(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def wilcoxon_p(values: np.ndarray) -> float:
    values = np.asarray(values, dtype=np.float64)
    if not len(values) or np.allclose(values, 0.0):
        return 1.0
    return float(wilcoxon(values, zero_method="wilcox", alternative="two-sided", method="auto").pvalue)


def rank_scores(
    scores: np.ndarray,
    clip_ids: np.ndarray,
    candidate_indices: np.ndarray | None = None,
    max_rank: int = MAX_RANK,
) -> list[tuple[str, float]]:
    """Exact score-descending, clip-id-ascending ranking used by the baseline."""
    indices = np.arange(len(clip_ids)) if candidate_indices is None else np.asarray(candidate_indices, dtype=np.int64)
    ranked = sorted(
        ((str(clip_ids[idx]), float(scores[idx])) for idx in indices),
        key=lambda item: (-item[1], item[0]),
    )
    return ranked[:max_rank]


def metric_record(
    condition: str,
    scoring: str,
    query: pd.Series,
    ranking: list[tuple[str, float]],
    positives: set[str],
) -> dict[str, Any]:
    values = evaluate_ranking([clip_id for clip_id, _ in ranking], positives, TOP_KS)
    return {
        "condition": condition,
        "scoring": scoring,
        "query_id": query["query_id"],
        "relevance_def": query["relevance_def"],
        "predicate": query["difficulty"],
        "pair_cluster": f"{query['difficulty']}|{query['relevance_def']}",
        "positive_count": len(positives),
        **values,
    }


def ranking_records(
    experiment: str,
    condition: str,
    query_id: str,
    ranking: list[tuple[str, float]],
) -> list[dict[str, Any]]:
    return [
        {
            "experiment": experiment,
            "condition": condition,
            "query_id": query_id,
            "rank": rank,
            "clip_id": clip_id,
            "score": score,
        }
        for rank, (clip_id, score) in enumerate(ranking, start=1)
    ]


def summarize_conditions(per_query: pd.DataFrame) -> pd.DataFrame:
    metrics = ["recall_at_1", "recall_at_5", "recall_at_10", "recall_at_20", "mrr", "ndcg_at_10"]
    return per_query.groupby(["condition", "scoring"], sort=False)[metrics].mean().reset_index()


def contrast_record(
    per_query: pd.DataFrame,
    treatment: str,
    control: str,
    scoring: str,
    draws: int,
    seed: int,
) -> dict[str, Any]:
    subset = per_query[per_query["scoring"].eq(scoring)]
    wide = subset.pivot(index="query_id", columns="condition", values="ndcg_at_10")
    meta = subset.drop_duplicates("query_id").set_index("query_id")
    if treatment not in wide or control not in wide:
        raise KeyError(f"Missing contrast condition: {treatment} or {control}")
    wide = wide[[treatment, control]].dropna()
    delta = (wide[treatment] - wide[control]).to_numpy(dtype=np.float64)
    clusters = meta.loc[wide.index, "pair_cluster"].to_numpy()
    qlo, qhi = bootstrap_ci(delta, draws, seed)
    clo, chi = cluster_bootstrap_ci(delta, clusters, draws, seed + 1)
    return {
        "scoring": scoring,
        "treatment": treatment,
        "control": control,
        "queries": len(delta),
        "pair_clusters": int(len(np.unique(clusters))),
        "mean_delta_ndcg10": float(delta.mean()),
        "query_bootstrap_ci_lo": qlo,
        "query_bootstrap_ci_hi": qhi,
        "pair_cluster_bootstrap_ci_lo": clo,
        "pair_cluster_bootstrap_ci_hi": chi,
        "wilcoxon_p_two_sided": wilcoxon_p(delta),
        "negative": int((delta < 0).sum()),
        "zero": int((delta == 0).sum()),
        "positive": int((delta > 0).sum()),
    }


def validate_inputs(
    canonical_root: Path, embedding_root: Path
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    dict[str, dict[str, set[str]]],
    np.ndarray,
    np.ndarray,
    dict[str, Any],
]:
    clips = pd.read_parquet(canonical_root / "clips.parquet")
    documents = pd.read_parquet(canonical_root / "documents.parquet")
    metadata = pd.read_parquet(canonical_root / "metadata.parquet")
    queries = read_queries(canonical_root / "queries.jsonl")
    doc_index = pd.read_parquet(embedding_root / "document_index.parquet")
    query_index = pd.read_parquet(embedding_root / "query_index.parquet")
    frozen_docs = np.load(embedding_root / "document_embeddings.npy").astype("float32")
    frozen_queries = np.load(embedding_root / "query_embeddings.npy").astype("float32")
    strict_frame, strict = positive_sets(canonical_root / "qrels.tsv")
    semantic_frame, semantic = positive_sets(canonical_root / "qrels_semantic.tsv")
    qrels = {"strict": strict, "semantic": semantic}

    assertions: dict[str, Any] = {}

    def check(name: str, condition: bool, detail: Any = None) -> None:
        assertions[name] = {"pass": bool(condition), "detail": detail}
        if not condition:
            raise AssertionError(f"Input validation failed: {name}: {detail}")

    check("expected_clip_count", len(clips) == EXPECTED_COUNTS["clips"], len(clips))
    check("expected_document_count", len(documents) == EXPECTED_COUNTS["documents"], len(documents))
    check("expected_query_count", len(queries) == EXPECTED_COUNTS["queries"], len(queries))
    check("one_document_per_clip", documents["clip_id"].is_unique, documents["clip_id"].nunique())
    check("document_ids_unique", documents["doc_id"].is_unique, documents["doc_id"].nunique())
    check("query_ids_unique", queries["query_id"].is_unique, queries["query_id"].nunique())
    check("document_index_alignment", documents["doc_id"].tolist() == doc_index["doc_id"].tolist())
    check("query_index_alignment", queries["query_id"].tolist() == query_index["query_id"].tolist())
    check("document_embedding_rows", len(frozen_docs) == len(documents), frozen_docs.shape)
    check("query_embedding_rows", len(frozen_queries) == len(queries), frozen_queries.shape)
    check("corpus_document_clip_identity", set(clips["clip_id"]) == set(documents["clip_id"]))
    check("expected_relevance_definitions", set(queries["relevance_def"]) == set(LABEL_PHRASES))
    clusters = queries["difficulty"].astype(str) + "|" + queries["relevance_def"].astype(str)
    check("expected_pair_clusters", clusters.nunique() == EXPECTED_COUNTS["pair_clusters"], clusters.nunique())

    corpus = set(clips["clip_id"])
    query_ids = set(queries["query_id"])
    for scoring, frame, sets in [
        ("strict", strict_frame, strict),
        ("semantic", semantic_frame, semantic),
    ]:
        check(f"{scoring}_qrel_query_coverage", set(sets) == query_ids, len(sets))
        check(f"{scoring}_qrel_targets_in_corpus", set(frame["target_id"]) <= corpus)
        check(
            f"{scoring}_qrel_pairs_unique",
            not frame.duplicated(["query_id", "target_id"]).any(),
        )

    metadata_wide = metadata.pivot_table(
        index="clip_id", columns="facet_name", values="facet_value", aggfunc="first"
    ).fillna("")
    strict_equals_intersection = True
    semantic_same_within_definition = True
    semantic_by_definition: dict[str, set[str]] = {}
    for _, query in queries.iterrows():
        qid = query["query_id"]
        sem = semantic[qid]
        if not strict[qid] <= sem:
            strict_equals_intersection = False
            break
        metadata_filter = dict(query["metadata_filter"] or {})
        mask = pd.Series(True, index=metadata_wide.index)
        for facet, value in metadata_filter.items():
            mask &= metadata_wide[facet].eq(str(value))
        expected_strict = sem & set(metadata_wide.index[mask])
        if expected_strict != strict[qid]:
            strict_equals_intersection = False
            break
        relevance_def = query["relevance_def"]
        previous = semantic_by_definition.setdefault(relevance_def, sem)
        if previous != sem:
            semantic_same_within_definition = False
            break
        if int(query["positive_count_semantic"]) != len(sem):
            semantic_same_within_definition = False
            break
    check("strict_qrels_equal_semantic_intersect_predicate", strict_equals_intersection)
    check("semantic_qrels_constant_within_relevance_definition", semantic_same_within_definition)

    norms_d = np.linalg.norm(frozen_docs, axis=1)
    norms_q = np.linalg.norm(frozen_queries, axis=1)
    check("frozen_document_vectors_finite", np.isfinite(frozen_docs).all())
    check("frozen_query_vectors_finite", np.isfinite(frozen_queries).all())
    assertions["frozen_vector_norms"] = {
        "pass": True,
        "document_min_max": [float(norms_d.min()), float(norms_d.max())],
        "query_min_max": [float(norms_q.min()), float(norms_q.max())],
    }

    return documents, metadata, queries, doc_index, qrels, frozen_docs, frozen_queries, assertions


def normalized_copy(values: np.ndarray) -> np.ndarray:
    result = np.ascontiguousarray(values.astype("float32", copy=True))
    faiss.normalize_L2(result)
    return result


def run_c1(
    queries: pd.DataFrame,
    doc_index: pd.DataFrame,
    qrels: dict[str, dict[str, set[str]]],
    frozen_docs: np.ndarray,
    frozen_queries: np.ndarray,
    random_reps: int,
    bootstrap_draws: int,
    seed: int,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    print("[C1] exact dense scores and qrel-oracle/placebo filters", flush=True)
    docs = normalized_copy(frozen_docs)
    qvecs = normalized_copy(frozen_queries)
    clip_ids = doc_index["clip_id"].astype(str).to_numpy()
    clip_to_index = {clip_id: idx for idx, clip_id in enumerate(clip_ids)}
    score_matrix = qvecs @ docs.T

    primary_rows: list[dict[str, Any]] = []
    ranking_rows: list[dict[str, Any]] = []
    random_rows: list[dict[str, Any]] = []
    mask_digest = hashlib.sha256()

    for scoring_pos, scoring in enumerate(SCORINGS):
        for query_pos, query in queries.reset_index(drop=True).iterrows():
            qid = query["query_id"]
            positives = qrels[scoring][qid]
            scores = score_matrix[query_pos]
            clean = rank_scores(scores, clip_ids)
            oracle_indices = np.array(sorted(clip_to_index[clip_id] for clip_id in positives), dtype=np.int64)
            oracle = rank_scores(scores, clip_ids, oracle_indices)
            primary_rows.append(metric_record("clean_b2", scoring, query, clean, positives))
            primary_rows.append(metric_record("oracle_qrel_filter", scoring, query, oracle, positives))
            ranking_rows.extend(ranking_records("C1", f"clean_b2__{scoring}", qid, clean))
            ranking_rows.extend(ranking_records("C1", f"oracle_qrel_filter__{scoring}", qid, oracle))

            for rep in range(random_reps):
                rng = np.random.default_rng(np.random.SeedSequence([seed, 1101, scoring_pos, rep, query_pos]))
                candidates = np.sort(rng.choice(len(clip_ids), size=len(positives), replace=False))
                random_rank = rank_scores(scores, clip_ids, candidates)
                row = metric_record("random_same_selectivity", scoring, query, random_rank, positives)
                row["replicate"] = rep
                random_rows.append(row)
                mask_digest.update(scoring.encode("utf-8"))
                mask_digest.update(np.asarray([rep, query_pos], dtype="<i8").tobytes())
                mask_digest.update(candidates.astype("<i8", copy=False).tobytes())

    primary = pd.DataFrame(primary_rows)
    random_by_query = pd.DataFrame(random_rows)
    random_mean = (
        random_by_query.groupby(["scoring", "query_id"], sort=False)
        .agg(
            relevance_def=("relevance_def", "first"),
            predicate=("predicate", "first"),
            pair_cluster=("pair_cluster", "first"),
            positive_count=("positive_count", "first"),
            recall_at_1=("recall_at_1", "mean"),
            recall_at_5=("recall_at_5", "mean"),
            recall_at_10=("recall_at_10", "mean"),
            recall_at_20=("recall_at_20", "mean"),
            mrr=("mrr", "mean"),
            ndcg_at_10=("ndcg_at_10", "mean"),
            ndcg_at_10_random_sd=("ndcg_at_10", "std"),
        )
        .reset_index()
    )
    random_mean.insert(0, "condition", "random_same_selectivity_mean")
    combined = pd.concat([primary, random_mean], ignore_index=True, sort=False)
    summary = summarize_conditions(combined)

    contrast_rows = []
    for scoring_pos, scoring in enumerate(SCORINGS):
        contrast_rows.append(
            contrast_record(
                combined,
                "oracle_qrel_filter",
                "clean_b2",
                scoring,
                bootstrap_draws,
                seed + 1200 + scoring_pos * 10,
            )
        )
        contrast_rows.append(
            contrast_record(
                combined,
                "oracle_qrel_filter",
                "random_same_selectivity_mean",
                scoring,
                bootstrap_draws,
                seed + 1202 + scoring_pos * 10,
            )
        )
    contrasts = pd.DataFrame(contrast_rows)

    random_replicates = (
        random_by_query.groupby(["scoring", "replicate"], sort=False)[
            ["recall_at_10", "mrr", "ndcg_at_10"]
        ]
        .mean()
        .reset_index()
    )
    random_distribution = {}
    for scoring in SCORINGS:
        values = random_replicates.loc[random_replicates["scoring"].eq(scoring), "ndcg_at_10"].to_numpy()
        oracle_mean = float(
            summary.loc[
                summary["condition"].eq("oracle_qrel_filter") & summary["scoring"].eq(scoring),
                "ndcg_at_10",
            ].iloc[0]
        )
        random_distribution[scoring] = {
            "replicates": len(values),
            "mean": float(values.mean()),
            "sd": float(values.std(ddof=1)),
            "replicate_percentile_2_5": float(np.percentile(values, 2.5)),
            "replicate_percentile_97_5": float(np.percentile(values, 97.5)),
            "max": float(values.max()),
            "plus_one_randomization_p_ge_oracle": float((1 + (values >= oracle_mean).sum()) / (len(values) + 1)),
        }

    combined.to_parquet(output_dir / "c1_metrics_by_query.parquet", index=False)
    random_by_query.to_parquet(output_dir / "c1_random_masks_metrics_by_query.parquet", index=False)
    random_replicates.to_csv(output_dir / "c1_random_mask_replicates.csv", index=False)
    summary.to_csv(output_dir / "c1_summary.csv", index=False)
    contrasts.to_csv(output_dir / "c1_contrasts.csv", index=False)
    pd.DataFrame(ranking_rows).to_parquet(output_dir / "c1_rankings.parquet", index=False)

    audit = {
        "random_mask_stream_sha256": mask_digest.hexdigest(),
        "random_filter_replicate_distribution": random_distribution,
        "score_matrix_shape": list(score_matrix.shape),
    }
    return combined, summary, contrasts, audit


def semantic_sets_by_definition(
    queries: pd.DataFrame, semantic_qrels: dict[str, set[str]]
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for _, query in queries.iterrows():
        relevance_def = query["relevance_def"]
        values = semantic_qrels[query["query_id"]]
        if relevance_def in result and result[relevance_def] != values:
            raise AssertionError(f"Semantic qrels differ within {relevance_def}")
        result[relevance_def] = values
    return result


def selected_label_edges(
    semantic_by_def: dict[str, set[str]], dose: float, rep: int, seed: int
) -> tuple[dict[str, set[str]], list[dict[str, Any]]]:
    selected: dict[str, set[str]] = {}
    audit_rows: list[dict[str, Any]] = []
    for label_pos, relevance_def in enumerate(LABEL_PHRASES):
        population = np.array(sorted(semantic_by_def[relevance_def]), dtype=object)
        if dose <= 0:
            chosen = np.array([], dtype=object)
        elif dose >= 1:
            chosen = population
        else:
            rng = np.random.default_rng(np.random.SeedSequence([seed, 2102, rep, label_pos]))
            order = rng.permutation(len(population))
            count = int(math.floor(dose * len(population)))
            chosen = population[order[:count]]
        selected[relevance_def] = set(chosen.tolist())
        audit_rows.append(
            {
                "replicate": rep,
                "dose": dose,
                "relevance_def": relevance_def,
                "population_edges": len(population),
                "selected_edges": len(chosen),
                "selected_clip_ids_sha256": sha256_strings(sorted(str(value) for value in chosen)),
            }
        )
    return selected, audit_rows


def inject_documents(
    documents: pd.DataFrame, selected: dict[str, set[str]]
) -> tuple[list[str], list[list[str]], int]:
    texts: list[str] = []
    tokenized: list[list[str]] = []
    injected_edges = 0
    for row in documents.itertuples(index=False):
        additions = [
            phrase
            for relevance_def, phrase in LABEL_PHRASES.items()
            if row.clip_id in selected[relevance_def]
        ]
        injected_edges += len(additions)
        clean = str(row.text) if row.text is not None else ""
        contaminated = " ".join([clean, *additions]).strip()
        texts.append(contaminated)
        tokenized.append(tokenize(contaminated))
    return texts, tokenized, injected_edges


def bm25_metrics(
    tokenized_documents: list[list[str]],
    queries: pd.DataFrame,
    clip_ids: np.ndarray,
    qrels: dict[str, dict[str, set[str]]],
    condition: str,
    experiment: str,
    save_rankings: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    bm25 = BM25Okapi(tokenized_documents)
    metric_rows: list[dict[str, Any]] = []
    ranking_rows: list[dict[str, Any]] = []
    for _, query in queries.iterrows():
        scores = bm25.get_scores(tokenize(query["query_text"])).astype("float32")
        ranking = rank_scores(scores, clip_ids)
        for scoring in SCORINGS:
            metric_rows.append(metric_record(condition, scoring, query, ranking, qrels[scoring][query["query_id"]]))
        if save_rankings:
            ranking_rows.extend(ranking_records(experiment, condition, query["query_id"], ranking))
    return metric_rows, ranking_rows


def run_c2_bm25(
    documents: pd.DataFrame,
    queries: pd.DataFrame,
    doc_index: pd.DataFrame,
    qrels: dict[str, dict[str, set[str]]],
    dose_reps: int,
    seed: int,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, list[str], dict[str, Any]]:
    print("[C2/BM25] clean/full primary arms and partial-dose robustness arms", flush=True)
    semantic_by_def = semantic_sets_by_definition(queries, qrels["semantic"])
    clip_ids = doc_index["clip_id"].astype(str).to_numpy()
    rows: list[dict[str, Any]] = []
    rankings: list[dict[str, Any]] = []
    assignment_audit: list[dict[str, Any]] = []
    full_texts: list[str] | None = None

    for dose in DOSES:
        reps = 1 if dose in (0.0, 1.0) else dose_reps
        for rep in range(reps):
            selected, audit = selected_label_edges(semantic_by_def, dose, rep, seed)
            assignment_audit.extend(audit)
            texts, tokenized, injected_edges = inject_documents(documents, selected)
            condition = f"bm25_dose_{dose:.2f}"
            metric_rows, ranking_rows = bm25_metrics(
                tokenized,
                queries,
                clip_ids,
                qrels,
                condition,
                "C2",
                save_rankings=dose in (0.0, 1.0),
            )
            for row in metric_rows:
                row["dose"] = dose
                row["replicate"] = rep
                row["injected_label_edges"] = injected_edges
            rows.extend(metric_rows)
            rankings.extend(ranking_rows)
            if dose == 1.0:
                full_texts = texts
        print(f"  dose={dose:.2f} reps={reps}", flush=True)

    if full_texts is None:
        raise AssertionError("Full-contamination texts were not created")
    dose_by_query = pd.DataFrame(rows)
    replicate_means = (
        dose_by_query.groupby(["dose", "replicate", "scoring"], sort=False)[
            ["recall_at_10", "mrr", "ndcg_at_10"]
        ]
        .mean()
        .reset_index()
    )
    dose_summary_rows = []
    for (dose, scoring), group in replicate_means.groupby(["dose", "scoring"], sort=True):
        values = group["ndcg_at_10"].to_numpy()
        dose_summary_rows.append(
            {
                "dose": dose,
                "scoring": scoring,
                "replicates": len(values),
                "mean_ndcg_at_10": float(values.mean()),
                "assignment_sd": float(values.std(ddof=1)) if len(values) > 1 else 0.0,
                "assignment_percentile_2_5": float(np.percentile(values, 2.5)),
                "assignment_percentile_97_5": float(np.percentile(values, 97.5)),
                "min": float(values.min()),
                "max": float(values.max()),
            }
        )
    dose_summary = pd.DataFrame(dose_summary_rows)

    full_documents = documents.copy()
    full_documents["text"] = full_texts
    full_documents.to_parquet(output_dir / "c2_documents_full_contamination.parquet", index=False)
    dose_by_query.to_parquet(output_dir / "c2_bm25_dose_metrics_by_query.parquet", index=False)
    replicate_means.to_csv(output_dir / "c2_bm25_dose_replicates.csv", index=False)
    dose_summary.to_csv(output_dir / "c2_bm25_dose_summary.csv", index=False)
    pd.DataFrame(assignment_audit).to_csv(output_dir / "c2_dose_assignment_audit.csv", index=False)
    pd.DataFrame(rankings).to_parquet(output_dir / "c2_bm25_rankings_clean_full.parquet", index=False)

    total_edges = sum(len(values) for values in semantic_by_def.values())
    audit = {
        "semantic_positive_edges_by_definition": {
            key: len(value) for key, value in semantic_by_def.items()
        },
        "total_unique_label_edges": total_edges,
        "full_contaminated_text_sha256": sha256_strings(full_texts),
        "dose_selection_rule": "floor(dose * label-positive documents), nested within each replicate and relevance definition",
        "partial_dose_assignment_unit": "document x relevance-definition positive edge",
    }
    return dose_by_query, dose_summary, full_texts, audit


def token_length_audit(model: Any, clean: list[str], contaminated: list[str]) -> dict[str, Any]:
    tokenizer = model.tokenizer
    result: dict[str, Any] = {"model_max_seq_length": int(model.max_seq_length)}
    for name, texts in [("clean", clean), ("full_contamination", contaminated)]:
        lengths = []
        for start in range(0, len(texts), 128):
            encoded = tokenizer(
                texts[start : start + 128],
                add_special_tokens=True,
                truncation=False,
                padding=False,
            )["input_ids"]
            lengths.extend(len(ids) for ids in encoded)
        values = np.asarray(lengths)
        result[name] = {
            "min": int(values.min()),
            "median": float(np.median(values)),
            "max": int(values.max()),
            "over_model_max": int((values > model.max_seq_length).sum()),
        }
    return result


def run_c2_dense(
    documents: pd.DataFrame,
    full_texts: list[str],
    queries: pd.DataFrame,
    doc_index: pd.DataFrame,
    qrels: dict[str, dict[str, set[str]]],
    frozen_docs: np.ndarray,
    frozen_queries: np.ndarray,
    model_path: Path,
    device: str,
    batch_size: int,
    output_dir: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    print(f"[C2/BGE-M3] one-session clean/full/query re-embedding on {device}", flush=True)
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(str(model_path), device=device)
    clean_texts = documents["text"].fillna("").astype(str).tolist()
    query_texts = queries["query_text"].fillna("").astype(str).tolist()
    lengths = token_length_audit(model, clean_texts, full_texts)
    if lengths["clean"]["over_model_max"] or lengths["full_contamination"]["over_model_max"]:
        raise AssertionError(f"C2 text truncation would occur: {lengths}")

    def encode(texts: list[str]) -> np.ndarray:
        return model.encode(
            [" ".join(text.split()) for text in texts],
            batch_size=batch_size,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True,
        ).astype("float32")

    clean_vectors = encode(clean_texts)
    full_vectors = encode(full_texts)
    query_vectors = encode(query_texts)
    np.save(output_dir / "c2_bge_clean_document_embeddings.npy", clean_vectors)
    np.save(output_dir / "c2_bge_full_document_embeddings.npy", full_vectors)
    np.save(output_dir / "c2_bge_query_embeddings.npy", query_vectors)

    clip_ids = doc_index["clip_id"].astype(str).to_numpy()
    rows: list[dict[str, Any]] = []
    rankings: list[dict[str, Any]] = []
    for condition, doc_vectors in [
        ("bge_clean_reembedded", clean_vectors),
        ("bge_full_contamination", full_vectors),
    ]:
        scores = query_vectors @ doc_vectors.T
        for query_pos, query in queries.reset_index(drop=True).iterrows():
            ranking = rank_scores(scores[query_pos], clip_ids)
            for scoring in SCORINGS:
                rows.append(metric_record(condition, scoring, query, ranking, qrels[scoring][query["query_id"]]))
            rankings.extend(ranking_records("C2", condition, query["query_id"], ranking))

    per_query = pd.DataFrame(rows)
    summary = summarize_conditions(per_query)
    pd.DataFrame(rankings).to_parquet(output_dir / "c2_bge_rankings_clean_full.parquet", index=False)

    frozen_docs_norm = normalized_copy(frozen_docs)
    frozen_queries_norm = normalized_copy(frozen_queries)
    clean_norm = normalized_copy(clean_vectors)
    query_norm = normalized_copy(query_vectors)
    cosine_doc = np.sum(frozen_docs_norm * clean_norm, axis=1)
    cosine_query = np.sum(frozen_queries_norm * query_norm, axis=1)
    audit = {
        "token_lengths": lengths,
        "same_session_and_model_for_clean_full_query": True,
        "clean_vs_frozen_document_embedding": {
            "mean_cosine": float(cosine_doc.mean()),
            "min_cosine": float(cosine_doc.min()),
            "max_abs_element_difference": float(np.max(np.abs(clean_vectors - frozen_docs))),
        },
        "query_vs_frozen_embedding": {
            "mean_cosine": float(cosine_query.mean()),
            "min_cosine": float(cosine_query.min()),
            "max_abs_element_difference": float(np.max(np.abs(query_vectors - frozen_queries))),
        },
        "embedding_shapes": {
            "clean_documents": list(clean_vectors.shape),
            "full_documents": list(full_vectors.shape),
            "queries": list(query_vectors.shape),
        },
    }
    per_query.to_parquet(output_dir / "c2_bge_metrics_by_query.parquet", index=False)
    summary.to_csv(output_dir / "c2_bge_summary.csv", index=False)
    return per_query, summary, audit


def restore_predense_outputs(
    output_dir: Path,
    documents: pd.DataFrame,
    queries: pd.DataFrame,
    qrels: dict[str, dict[str, set[str]]],
    random_reps: int,
    dose_reps: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any], pd.DataFrame, pd.DataFrame, list[str], dict[str, Any]]:
    """Load and audit the completed CPU stage before resuming dense C2."""
    required = [
        "c1_metrics_by_query.parquet",
        "c1_summary.csv",
        "c1_contrasts.csv",
        "c1_random_mask_replicates.csv",
        "c2_bm25_dose_metrics_by_query.parquet",
        "c2_bm25_dose_summary.csv",
        "c2_documents_full_contamination.parquet",
        "c2_dose_assignment_audit.csv",
    ]
    missing = [name for name in required if not (output_dir / name).exists()]
    if missing:
        raise FileNotFoundError(f"Cannot resume; missing pre-dense outputs: {missing}")

    c1_per_query = pd.read_parquet(output_dir / "c1_metrics_by_query.parquet")
    c1_summary = pd.read_csv(output_dir / "c1_summary.csv")
    c1_contrasts = pd.read_csv(output_dir / "c1_contrasts.csv")
    c1_random = pd.read_csv(output_dir / "c1_random_mask_replicates.csv")
    c2_bm25_all = pd.read_parquet(output_dir / "c2_bm25_dose_metrics_by_query.parquet")
    dose_summary = pd.read_csv(output_dir / "c2_bm25_dose_summary.csv")
    full_documents = pd.read_parquet(output_dir / "c2_documents_full_contamination.parquet")
    dose_audit = pd.read_csv(output_dir / "c2_dose_assignment_audit.csv")

    if len(c1_random) != random_reps * len(SCORINGS):
        raise AssertionError(f"C1 resume replicate mismatch: {len(c1_random)}")
    expected_dose_rows = (2 + 3 * dose_reps) * len(queries) * len(SCORINGS)
    if len(c2_bm25_all) != expected_dose_rows:
        raise AssertionError(f"C2 BM25 resume row mismatch: {len(c2_bm25_all)} != {expected_dose_rows}")
    if documents["doc_id"].tolist() != full_documents["doc_id"].tolist():
        raise AssertionError("Full-contamination documents do not align with frozen documents")
    if len(dose_audit) != (2 + 3 * dose_reps) * len(LABEL_PHRASES):
        raise AssertionError(f"C2 dose audit row mismatch: {len(dose_audit)}")

    random_distribution: dict[str, Any] = {}
    for scoring in SCORINGS:
        values = c1_random.loc[c1_random["scoring"].eq(scoring), "ndcg_at_10"].to_numpy()
        oracle_mean = result_value(c1_summary, "oracle_qrel_filter", scoring)
        random_distribution[scoring] = {
            "replicates": len(values),
            "mean": float(values.mean()),
            "sd": float(values.std(ddof=1)),
            "replicate_percentile_2_5": float(np.percentile(values, 2.5)),
            "replicate_percentile_97_5": float(np.percentile(values, 97.5)),
            "max": float(values.max()),
            "plus_one_randomization_p_ge_oracle": float((1 + (values >= oracle_mean).sum()) / (len(values) + 1)),
        }

    # Recreate the candidate-mask stream receipt without rerunning retrieval.
    mask_digest = hashlib.sha256()
    n_documents = len(documents)
    for scoring_pos, scoring in enumerate(SCORINGS):
        for query_pos, query in queries.reset_index(drop=True).iterrows():
            n_positive = len(qrels[scoring][query["query_id"]])
            for rep in range(random_reps):
                rng = np.random.default_rng(np.random.SeedSequence([seed, 1101, scoring_pos, rep, query_pos]))
                candidates = np.sort(rng.choice(n_documents, size=n_positive, replace=False))
                mask_digest.update(scoring.encode("utf-8"))
                mask_digest.update(np.asarray([rep, query_pos], dtype="<i8").tobytes())
                mask_digest.update(candidates.astype("<i8", copy=False).tobytes())
    c1_audit = {
        "random_mask_stream_sha256": mask_digest.hexdigest(),
        "random_filter_replicate_distribution": random_distribution,
        "score_matrix_shape": [len(queries), len(documents)],
        "restored_after_interrupted_dense_step": True,
    }

    semantic_by_def = semantic_sets_by_definition(queries, qrels["semantic"])
    full_texts = full_documents["text"].fillna("").astype(str).tolist()
    c2_bm25_audit = {
        "semantic_positive_edges_by_definition": {
            key: len(value) for key, value in semantic_by_def.items()
        },
        "total_unique_label_edges": sum(len(value) for value in semantic_by_def.values()),
        "full_contaminated_text_sha256": sha256_strings(full_texts),
        "dose_selection_rule": "floor(dose * label-positive documents), nested within each replicate and relevance definition",
        "partial_dose_assignment_unit": "document x relevance-definition positive edge",
        "restored_after_interrupted_dense_step": True,
    }
    print("[resume] validated and restored completed C1/C2-BM25 outputs", flush=True)
    return (
        c1_per_query,
        c1_summary,
        c1_contrasts,
        c1_audit,
        c2_bm25_all,
        dose_summary,
        full_texts,
        c2_bm25_audit,
    )


def build_input_hashes(canonical_root: Path, embedding_root: Path, model_path: Path) -> dict[str, str]:
    paths = [
        canonical_root / "clips.parquet",
        canonical_root / "documents.parquet",
        canonical_root / "metadata.parquet",
        canonical_root / "queries.jsonl",
        canonical_root / "qrels.tsv",
        canonical_root / "qrels_semantic.tsv",
        embedding_root / "document_embeddings.npy",
        embedding_root / "query_embeddings.npy",
        embedding_root / "document_index.parquet",
        embedding_root / "query_index.parquet",
        embedding_root / "embedding_manifest.json",
    ]
    for name in [
        "pytorch_model.bin",
        "config.json",
        "modules.json",
        "sentence_bert_config.json",
        "sentencepiece.bpe.model",
        "tokenizer.json",
        "tokenizer_config.json",
    ]:
        path = model_path / name
        if path.exists():
            paths.append(path)
    return {str(path): sha256_file(path) for path in paths}


def environment_info(device: str) -> dict[str, Any]:
    info: dict[str, Any] = {
        "python": sys.version,
        "platform": platform.platform(),
        "executable": sys.executable,
        "packages": package_versions(),
        "device_argument": device,
    }
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=index,name,uuid,driver_version", "--format=csv,noheader"],
            check=True,
            capture_output=True,
            text=True,
        )
        info["nvidia_smi_gpus"] = result.stdout.strip().splitlines()
    except Exception as exc:  # pragma: no cover - environment receipt only
        info["nvidia_smi_error"] = repr(exc)
    return info


def output_hashes(output_dir: Path) -> dict[str, str]:
    excluded = {"manifest.json", "RESULTS_KO.md"}
    return {
        path.name: sha256_file(path)
        for path in sorted(output_dir.iterdir())
        if path.is_file() and path.name not in excluded
    }


def fmt(value: float, digits: int = 4, sign: bool = False) -> str:
    spec = f"{'+' if sign else ''}.{digits}f"
    return format(float(value), spec)


def result_value(summary: pd.DataFrame, condition: str, scoring: str, metric: str = "ndcg_at_10") -> float:
    return float(
        summary.loc[summary["condition"].eq(condition) & summary["scoring"].eq(scoring), metric].iloc[0]
    )


def write_report(
    output_dir: Path,
    args: argparse.Namespace,
    c1_summary: pd.DataFrame,
    c1_contrasts: pd.DataFrame,
    c1_audit: dict[str, Any],
    dose_summary: pd.DataFrame,
    c2_summary: pd.DataFrame,
    c2_contrasts: pd.DataFrame,
    validations: dict[str, Any],
) -> None:
    c1_sem = c1_contrasts[
        c1_contrasts["scoring"].eq("semantic")
        & c1_contrasts["treatment"].eq("oracle_qrel_filter")
        & c1_contrasts["control"].eq("clean_b2")
    ].iloc[0]
    c2_bm = c2_contrasts[
        c2_contrasts["scoring"].eq("semantic")
        & c2_contrasts["treatment"].eq("bm25_dose_1.00")
    ].iloc[0]
    c2_bge = c2_contrasts[
        c2_contrasts["scoring"].eq("semantic")
        & c2_contrasts["treatment"].eq("bge_full_contamination")
    ].iloc[0]
    dose_sem = dose_summary[dose_summary["scoring"].eq("semantic")].sort_values("dose")
    random_sem = c1_audit["random_filter_replicate_distribution"]["semantic"]

    lines = [
        "# 순환성 통제 주입 실험 결과",
        "",
        f"- 실행 시각(UTC): `{utc_now()}`",
        "- 데이터: AIHub-522 frozen tri-source expanded, 3,000 clips / 85 queries",
        "- 주 지표: semantic nDCG@10의 85질의 평균",
        "- 상태: 예비 계산을 본 뒤 정식화한 post-pilot 실험이며 사전등록 실험은 아님",
        "",
        "## C1: qrel-oracle 필터 주입",
        "",
        "| 조건 | strict nDCG@10 | semantic nDCG@10 |",
        "|---|---:|---:|",
    ]
    for condition in ["clean_b2", "random_same_selectivity_mean", "oracle_qrel_filter"]:
        lines.append(
            f"| {condition} | {result_value(c1_summary, condition, 'strict'):.6f} | "
            f"{result_value(c1_summary, condition, 'semantic'):.6f} |"
        )
    lines.extend(
        [
            "",
            f"semantic oracle−clean Δ={fmt(c1_sem['mean_delta_ndcg10'], 6, True)}, "
            f"query bootstrap 95% CI [{fmt(c1_sem['query_bootstrap_ci_lo'], 6, True)}, "
            f"{fmt(c1_sem['query_bootstrap_ci_hi'], 6, True)}], "
            f"pair-cluster bootstrap 95% CI [{fmt(c1_sem['pair_cluster_bootstrap_ci_lo'], 6, True)}, "
            f"{fmt(c1_sem['pair_cluster_bootstrap_ci_hi'], 6, True)}].",
            f"동일 선택률 무작위 필터 {args.random_filter_reps}회는 평균 {random_sem['mean']:.6f}, "
            f"replicate 95% 범위 [{random_sem['replicate_percentile_2_5']:.6f}, "
            f"{random_sem['replicate_percentile_97_5']:.6f}]였다.",
            "",
            "oracle=1.0은 정답 집합 자체를 후보 집합으로 사용했기 때문에 구성상 보장된다. "
            "따라서 이 결과는 검색 모델의 개선이 아니라 C1 경로가 평가를 포화시킬 수 있음을 정량화한다.",
            "",
            "## C2: qrel 라벨 문서 재진술",
            "",
            "| backend | clean semantic nDCG@10 | full contamination | Δ | query bootstrap 95% CI | pair-cluster 95% CI |",
            "|---|---:|---:|---:|---:|---:|",
            f"| BM25 | {result_value(c2_summary, 'bm25_dose_0.00', 'semantic'):.6f} | "
            f"{result_value(c2_summary, 'bm25_dose_1.00', 'semantic'):.6f} | "
            f"{fmt(c2_bm['mean_delta_ndcg10'], 6, True)} | "
            f"[{fmt(c2_bm['query_bootstrap_ci_lo'], 6, True)}, {fmt(c2_bm['query_bootstrap_ci_hi'], 6, True)}] | "
            f"[{fmt(c2_bm['pair_cluster_bootstrap_ci_lo'], 6, True)}, {fmt(c2_bm['pair_cluster_bootstrap_ci_hi'], 6, True)}] |",
            f"| BGE-M3 | {result_value(c2_summary, 'bge_clean_reembedded', 'semantic'):.6f} | "
            f"{result_value(c2_summary, 'bge_full_contamination', 'semantic'):.6f} | "
            f"{fmt(c2_bge['mean_delta_ndcg10'], 6, True)} | "
            f"[{fmt(c2_bge['query_bootstrap_ci_lo'], 6, True)}, {fmt(c2_bge['query_bootstrap_ci_hi'], 6, True)}] | "
            f"[{fmt(c2_bge['pair_cluster_bootstrap_ci_lo'], 6, True)}, {fmt(c2_bge['pair_cluster_bootstrap_ci_hi'], 6, True)}] |",
            "",
            "### BM25 오염량 강건성 분석",
            "",
            "| 라벨-edge 오염률 | 반복 | semantic nDCG@10 평균 | assignment 95% 범위 |",
            "|---:|---:|---:|---:|",
        ]
    )
    for row in dose_sem.itertuples(index=False):
        lines.append(
            f"| {row.dose:.2f} | {int(row.replicates)} | {row.mean_ndcg_at_10:.6f} | "
            f"[{row.assignment_percentile_2_5:.6f}, {row.assignment_percentile_97_5:.6f}] |"
        )
    passed = sum(bool(value.get("pass")) for value in validations.values())
    total = len(validations)
    lines.extend(
        [
            "",
            "부분 오염군은 라벨별 양성 문서의 고정 난수 순서를 사용해 한 반복 안에서 중첩된다. "
            "BM25의 IDF·문서길이 정규화 때문에 오염량에 대한 단조성은 검정하거나 주장하지 않는다.",
            "",
            "## 해석 경계",
            "",
            "- 모든 비교에서 corpus membership, query, qrel, metric, top-k와 tie-break를 고정했다.",
            "- C1은 의도적인 oracle 상한이고, C2는 의도적인 qrel→document 누수 개입이다.",
            "- 따라서 실험은 순환 경로가 성능을 인위적으로 부풀릴 수 있다는 within-workload 인과 증거다. "
            "실제 과거 시스템의 성능 상승분 전체를 순환성 하나에 귀속하지는 않는다.",
            "- 캡션에는 원래 task-aware 자연어가 포함되어 있다. clean→injected 차이는 그 기존 결합 위에 "
            "정답 라벨 재진술 경로를 추가한 효과다.",
            "- 85질의가 25개 predicate×relevance 군집에 종속되므로 query bootstrap과 군집 bootstrap을 함께 제시했다.",
            "",
            "## 재현성",
            "",
            f"- seed: `{args.seed}`; bootstrap: `{args.bootstrap}`; C1 random masks: `{args.random_filter_reps}`; "
            f"partial-dose assignments: `{args.dose_reps}`",
            f"- 입력 및 산출물 SHA-256은 `manifest.json`, 검증 {passed}/{total}은 `validation.json`에 기록했다.",
            "- 상세 질의별 지표와 랭킹은 같은 디렉터리의 Parquet/CSV 파일에 저장했다.",
        ]
    )
    (output_dir / "RESULTS_KO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    if args.random_filter_reps < 1 or args.dose_reps < 1 or args.bootstrap < 100:
        raise ValueError("Replicates must be >=1 and bootstrap draws must be >=100")
    output_dir = args.output_dir.resolve()
    if args.resume_dense and args.overwrite:
        raise ValueError("--resume-dense and --overwrite are mutually exclusive")
    if args.resume_dense:
        if not output_dir.exists():
            raise FileNotFoundError(f"Resume output does not exist: {output_dir}")
    elif output_dir.exists():
        if not args.overwrite:
            raise FileExistsError(f"{output_dir} exists; pass --overwrite")
        shutil.rmtree(output_dir)
    if not args.resume_dense:
        output_dir.mkdir(parents=True, exist_ok=False)

    started_at = utc_now()
    print("[validate] loading frozen workload and embeddings", flush=True)
    (
        documents,
        _metadata,
        queries,
        doc_index,
        qrels,
        frozen_docs,
        frozen_queries,
        validations,
    ) = validate_inputs(args.canonical_root.resolve(), args.embedding_root.resolve())

    if args.resume_dense:
        (
            c1_per_query,
            c1_summary,
            c1_contrasts,
            c1_audit,
            c2_bm25_all,
            dose_summary,
            full_texts,
            c2_bm25_audit,
        ) = restore_predense_outputs(
            output_dir,
            documents,
            queries,
            qrels,
            args.random_filter_reps,
            args.dose_reps,
            args.seed,
        )
    else:
        c1_per_query, c1_summary, c1_contrasts, c1_audit = run_c1(
            queries,
            doc_index,
            qrels,
            frozen_docs,
            frozen_queries,
            args.random_filter_reps,
            args.bootstrap,
            args.seed,
            output_dir,
        )
        c2_bm25_all, dose_summary, full_texts, c2_bm25_audit = run_c2_bm25(
            documents,
            queries,
            doc_index,
            qrels,
            args.dose_reps,
            args.seed,
            output_dir,
        )

    if args.skip_dense_c2:
        print("[C2/BGE-M3] skipped by development flag", flush=True)
        validation_path = output_dir / "validation.json"
        validation_path.write_text(json.dumps(validations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"[saved smoke output] {output_dir}", flush=True)
        return 0

    c2_dense, _c2_dense_summary, c2_dense_audit = run_c2_dense(
        documents,
        full_texts,
        queries,
        doc_index,
        qrels,
        frozen_docs,
        frozen_queries,
        args.model_path.resolve(),
        args.device,
        args.batch_size,
        output_dir,
    )

    # Primary clean/full BM25 arms plus clean/full dense arms.
    c2_bm25_primary = c2_bm25_all[
        c2_bm25_all["dose"].isin([0.0, 1.0]) & c2_bm25_all["replicate"].eq(0)
    ].copy()
    c2_primary = pd.concat([c2_bm25_primary, c2_dense], ignore_index=True, sort=False)
    c2_summary = summarize_conditions(c2_primary)
    c2_contrast_rows = []
    for scoring_pos, scoring in enumerate(SCORINGS):
        c2_contrast_rows.append(
            contrast_record(
                c2_primary,
                "bm25_dose_1.00",
                "bm25_dose_0.00",
                scoring,
                args.bootstrap,
                args.seed + 3100 + scoring_pos * 10,
            )
        )
        c2_contrast_rows.append(
            contrast_record(
                c2_primary,
                "bge_full_contamination",
                "bge_clean_reembedded",
                scoring,
                args.bootstrap,
                args.seed + 3102 + scoring_pos * 10,
            )
        )
    c2_contrasts = pd.DataFrame(c2_contrast_rows)
    c2_primary.to_parquet(output_dir / "c2_metrics_by_query_primary.parquet", index=False)
    c2_summary.to_csv(output_dir / "c2_summary.csv", index=False)
    c2_contrasts.to_csv(output_dir / "c2_contrasts.csv", index=False)

    # Output-level validation checks.
    def add_validation(name: str, condition: bool, detail: Any = None) -> None:
        validations[name] = {"pass": bool(condition), "detail": detail}
        if not condition:
            raise AssertionError(f"Output validation failed: {name}: {detail}")

    add_validation(
        "c1_all_query_condition_scoring_cells",
        len(c1_per_query) == len(queries) * len(SCORINGS) * 3,
        len(c1_per_query),
    )
    oracle_values = c1_per_query.loc[c1_per_query["condition"].eq("oracle_qrel_filter"), "ndcg_at_10"]
    add_validation("c1_oracle_ndcg_exactly_one", np.allclose(oracle_values, 1.0, atol=0.0), oracle_values.unique().tolist())
    add_validation("c2_primary_complete", len(c2_primary) == len(queries) * len(SCORINGS) * 4, len(c2_primary))
    add_validation("all_primary_metrics_finite", np.isfinite(c2_primary["ndcg_at_10"]).all())
    add_validation(
        "dense_clean_replicates_frozen_metric",
        abs(
            result_value(c2_summary, "bge_clean_reembedded", "semantic")
            - result_value(c1_summary, "clean_b2", "semantic")
        )
        <= 1e-6,
        {
            "reembedded": result_value(c2_summary, "bge_clean_reembedded", "semantic"),
            "frozen": result_value(c1_summary, "clean_b2", "semantic"),
        },
    )
    add_validation(
        "no_dense_token_truncation",
        c2_dense_audit["token_lengths"]["clean"]["over_model_max"] == 0
        and c2_dense_audit["token_lengths"]["full_contamination"]["over_model_max"] == 0,
        c2_dense_audit["token_lengths"],
    )

    (output_dir / "validation.json").write_text(
        json.dumps(validations, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print("[receipt] hashing frozen inputs, model, script, and outputs", flush=True)
    input_hashes = build_input_hashes(
        args.canonical_root.resolve(), args.embedding_root.resolve(), args.model_path.resolve()
    )
    manifest = {
        "experiment": "AIHub-522 controlled circularity injection C1/C2",
        "status": "post-pilot formalization; not preregistered",
        "started_at_utc": started_at,
        "completed_at_utc": utc_now(),
        "canonical_root": str(args.canonical_root.resolve()),
        "embedding_root": str(args.embedding_root.resolve()),
        "model_path": str(args.model_path.resolve()),
        "output_dir": str(output_dir),
        "design": {
            "fixed": [
                "3000-clip corpus membership",
                "85 query IDs and texts",
                "strict and semantic qrels",
                "binary nDCG@10 implementation",
                "top-k and deterministic tie break",
            ],
            "C1_intervention": "candidate set only: qrel positives versus uniform same-cardinality masks",
            "C2_intervention": "document text only: append exact relevance clause on positive label edges",
            "C2_dense_control": "clean, full-contamination, and query embeddings generated in one loaded model session",
            "primary_estimand": "query-weighted mean paired delta in semantic nDCG@10",
            "dependence_sensitivity": "25 predicate x relevance pair-cluster bootstrap",
            "partial_dose_role": "robustness only; no monotonicity claim",
        },
        "parameters": {
            "seed": args.seed,
            "top_ks": TOP_KS,
            "max_rank": MAX_RANK,
            "random_filter_reps": args.random_filter_reps,
            "dose_reps": args.dose_reps,
            "bootstrap_draws": args.bootstrap,
            "doses": DOSES,
            "batch_size": args.batch_size,
            "device": args.device,
            "label_phrases": LABEL_PHRASES,
        },
        "audits": {
            "C1": c1_audit,
            "C2_BM25": c2_bm25_audit,
            "C2_dense": c2_dense_audit,
        },
        "environment": environment_info(args.device),
        "script": {"path": str(Path(__file__).resolve()), "sha256": sha256_file(Path(__file__).resolve())},
        "input_sha256": input_hashes,
        "output_sha256": output_hashes(output_dir),
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(
        output_dir,
        args,
        c1_summary,
        c1_contrasts,
        c1_audit,
        dose_summary,
        c2_summary,
        c2_contrasts,
        validations,
    )
    print("\n=== C1 summary ===", flush=True)
    print(c1_summary.to_string(index=False), flush=True)
    print("\n=== C2 summary ===", flush=True)
    print(c2_summary.to_string(index=False), flush=True)
    print(f"\n[saved] {output_dir}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
