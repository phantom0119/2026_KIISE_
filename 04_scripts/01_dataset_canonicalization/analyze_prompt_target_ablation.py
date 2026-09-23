#!/usr/bin/env python3
"""E0: compare task-aware and task-neutral caption retrieval, exactly paired."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VER = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
BASE_CANONICAL = VER / "canonical_trisource_expanded"
BASE_EMBEDDINGS = VER / "embeddings_trisource_expanded" / "bge-m3"
BASE_CAPTIONS = VER / "captions"
NEUTRAL_CANONICAL = VER / "canonical_trisource_expanded_task_neutral_20260723"
NEUTRAL_EMBEDDINGS = VER / "embeddings_trisource_expanded_task_neutral_20260723" / "bge-m3"
NEUTRAL_CAPTIONS = VER / "captions_task_neutral_20260723"
DEFAULT_OUT = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets"
    / "20260723_controlled_supplement" / "e0_prompt_target_ablation"
)
CATEGORY_PATTERN = re.compile(
    r"\b(?:traffic|car|cars|bus|buses|truck|trucks|two-wheelers?|bicycles?|"
    r"motorbikes?|pedestrians?|cyclists?|stopped|parked)\b",
    flags=re.IGNORECASE,
)
TARGET_TERM_GROUPS = {
    "traffic": re.compile(r"\btraffic\b", re.IGNORECASE),
    "car": re.compile(r"\bcars?\b", re.IGNORECASE),
    "bus": re.compile(r"\bbus(?:es)?\b", re.IGNORECASE),
    "truck": re.compile(r"\btrucks?\b", re.IGNORECASE),
    "two_wheeler": re.compile(
        r"\b(?:two-wheelers?|bicycles?|motorbikes?|cyclists?)\b", re.IGNORECASE
    ),
    "stopped_or_parked": re.compile(r"\b(?:stopped|parked)\b", re.IGNORECASE),
    "pedestrian": re.compile(r"\bpedestrians?\b", re.IGNORECASE),
}


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def load_caption_control(caption_dir: Path) -> tuple[dict, set[str], int]:
    manifests = [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted(caption_dir.glob("caption_manifest_shard*.json"))
    ]
    if not manifests:
        raise FileNotFoundError(f"no caption manifests in {caption_dir}")
    control_keys = (
        "snapshot", "max_new_tokens", "max_pixels", "decoding", "seed", "n_videos_target"
    )
    control = {key: manifests[0][key] for key in control_keys}
    for manifest in manifests[1:]:
        if {key: manifest[key] for key in control_keys} != control:
            raise AssertionError(f"caption controls differ across shards in {caption_dir}")
    prompt_hashes = {
        hashlib.sha256(manifest["prompt"].strip().encode()).hexdigest()
        for manifest in manifests
    }
    if len(prompt_hashes) != 1:
        raise AssertionError(f"caption prompt differs across shards in {caption_dir}")
    return control, prompt_hashes, len(manifests)


def assert_same_table(left: pd.DataFrame, right: pd.DataFrame, name: str) -> None:
    if list(left.columns) != list(right.columns):
        raise AssertionError(f"{name} columns changed")
    columns = list(left.columns)
    left_sorted = left.sort_values(columns).reset_index(drop=True)
    right_sorted = right.sort_values(columns).reset_index(drop=True)
    try:
        pd.testing.assert_frame_equal(left_sorted, right_sorted, check_dtype=True)
    except AssertionError as error:
        raise AssertionError(f"{name} changed between prompt conditions") from error


def top_indices(scores: np.ndarray, candidates: np.ndarray, k: int) -> np.ndarray:
    candidate_scores = scores[candidates]
    order = np.lexsort((candidates, -candidate_scores))
    return candidates[order[:k]]


def ranking_metrics(ranking: np.ndarray, relevant: np.ndarray, k: int = 10) -> dict[str, float]:
    gains = relevant[ranking].astype(float)
    cutoff = gains[:k]
    discounts = 1.0 / np.log2(np.arange(2, 2 + len(cutoff)))
    dcg = float(np.sum(cutoff * discounts))
    ideal_n = min(k, int(relevant.sum()))
    idcg = float(np.sum(1.0 / np.log2(np.arange(2, 2 + ideal_n)))) if ideal_n else 0.0
    positive_ranks = np.flatnonzero(gains)
    return {
        "ndcg_at_10": dcg / idcg if idcg else float("nan"),
        "mrr": 1.0 / (int(positive_ranks[0]) + 1) if len(positive_ranks) else 0.0,
        "recall_at_20": float(gains[:20].sum() / relevant.sum()) if relevant.sum() else float("nan"),
    }


def cluster_bootstrap(
    values: pd.DataFrame, value_column: str, seed: int, draws: int
) -> tuple[float, float]:
    families = sorted(values["family"].unique())
    by_family = {family: values.loc[values["family"] == family, value_column].to_numpy(float) for family in families}
    rng = np.random.default_rng(seed)
    sampled_means = np.empty(draws)
    for draw in range(draws):
        selected = rng.choice(families, len(families), replace=True)
        sampled_means[draw] = np.concatenate([by_family[family] for family in selected]).mean()
    return float(np.percentile(sampled_means, 2.5)), float(np.percentile(sampled_means, 97.5))


def cluster_signflip_p(
    values: pd.DataFrame, value_column: str, seed: int, draws: int
) -> float:
    family_values = values.groupby("family")[value_column].mean().to_numpy(float)
    observed = abs(float(family_values.mean()))
    rng = np.random.default_rng(seed)
    signs = rng.choice((-1.0, 1.0), size=(draws, len(family_values)))
    null = np.abs((signs * family_values).mean(axis=1))
    return float((1 + (null >= observed).sum()) / (draws + 1))


def holm_adjust(pvalues: np.ndarray) -> np.ndarray:
    order = np.argsort(pvalues)
    adjusted = np.empty_like(pvalues, dtype=float)
    running = 0.0
    total = len(pvalues)
    for rank, index in enumerate(order):
        value = min(1.0, float(pvalues[index]) * (total - rank))
        running = max(running, value)
        adjusted[index] = running
    return adjusted


def caption_diagnostics(documents: pd.DataFrame, generation_tokenizer, embedding_tokenizer) -> dict:
    texts = documents["text"].fillna("").astype(str)
    generation_token_counts = np.asarray(
        [
            len(generation_tokenizer(text, add_special_tokens=False)["input_ids"])
            for text in texts
        ],
        dtype=int,
    )
    embedding_token_counts = np.asarray(
        [
            len(embedding_tokenizer(text, add_special_tokens=False)["input_ids"])
            for text in texts
        ],
        dtype=int,
    )
    return {
        "documents": int(len(texts)),
        "empty": int(texts.str.strip().eq("").sum()),
        "characters": {
            "mean": float(texts.str.len().mean()),
            "median": float(texts.str.len().median()),
            "p95": float(texts.str.len().quantile(0.95)),
        },
        "whitespace_tokens": {
            "mean": float(texts.str.split().str.len().mean()),
            "median": float(texts.str.split().str.len().median()),
        },
        "qwen_generation_token_count": {
            "mean": float(generation_token_counts.mean()),
            "median": float(np.median(generation_token_counts)),
            "p95": float(np.percentile(generation_token_counts, 95)),
            "at_or_above_110": int((generation_token_counts >= 110).sum()),
        },
        "bge_embedding_token_count": {
            "mean": float(embedding_token_counts.mean()),
            "median": float(np.median(embedding_token_counts)),
            "p95": float(np.percentile(embedding_token_counts, 95)),
        },
        "target_category_term_documents": int(texts.str.contains(CATEGORY_PATTERN).sum()),
        "target_category_term_rate": float(texts.str.contains(CATEGORY_PATTERN).mean()),
        "target_term_group_document_rate": {
            name: float(texts.str.contains(pattern).mean())
            for name, pattern in TARGET_TERM_GROUPS.items()
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-canonical", type=Path, default=BASE_CANONICAL)
    parser.add_argument("--base-embeddings", type=Path, default=BASE_EMBEDDINGS)
    parser.add_argument("--base-captions", type=Path, default=BASE_CAPTIONS)
    parser.add_argument("--neutral-canonical", type=Path, default=NEUTRAL_CANONICAL)
    parser.add_argument("--neutral-embeddings", type=Path, default=NEUTRAL_EMBEDDINGS)
    parser.add_argument("--neutral-captions", type=Path, default=NEUTRAL_CAPTIONS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260723)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty; pass --overwrite")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    base_queries = pd.DataFrame(load_jsonl(args.base_canonical / "queries.jsonl"))
    neutral_queries = pd.DataFrame(load_jsonl(args.neutral_canonical / "queries.jsonl"))
    if base_queries.to_dict("records") != neutral_queries.to_dict("records"):
        raise AssertionError("query definitions changed between prompt conditions")
    qrel_hashes: dict[str, dict[str, str]] = {}
    for filename in ("qrels.tsv", "qrels_semantic.tsv"):
        base_qrels = pd.read_csv(args.base_canonical / filename, sep="\t")
        neutral_qrels = pd.read_csv(args.neutral_canonical / filename, sep="\t")
        assert_same_table(base_qrels, neutral_qrels, filename)
        qrel_hashes[filename] = {
            "base": sha256_file(args.base_canonical / filename),
            "neutral": sha256_file(args.neutral_canonical / filename),
        }
    base_metadata = pd.read_parquet(args.base_canonical / "metadata.parquet")
    neutral_metadata = pd.read_parquet(args.neutral_canonical / "metadata.parquet")
    assert_same_table(base_metadata, neutral_metadata, "metadata")

    base_control, base_prompt_hashes, base_shards = load_caption_control(args.base_captions)
    neutral_control, neutral_prompt_hashes, neutral_shards = load_caption_control(
        args.neutral_captions
    )
    if base_control != neutral_control:
        raise AssertionError("non-prompt caption generation controls changed")
    if base_prompt_hashes == neutral_prompt_hashes:
        raise AssertionError("caption prompt treatment did not change")
    base_caption_docs = pd.read_parquet(args.base_captions / "documents.parquet")
    neutral_caption_docs = pd.read_parquet(args.neutral_captions / "documents.parquet")
    identity_columns = [
        column
        for column in ("visual_video_id", "clip_id", "split", "source_frame")
        if column in base_caption_docs.columns and column in neutral_caption_docs.columns
    ]
    assert_same_table(
        base_caption_docs[identity_columns],
        neutral_caption_docs[identity_columns],
        "caption frame identities",
    )
    base_queries["family"] = (
        base_queries["difficulty"].astype(str) + "::" + base_queries["relevance_def"].astype(str)
    )

    base_doc_index = pd.read_parquet(args.base_embeddings / "document_index.parquet")
    neutral_doc_index = pd.read_parquet(args.neutral_embeddings / "document_index.parquet")
    if set(base_doc_index["clip_id"]) != set(neutral_doc_index["clip_id"]):
        raise AssertionError("document clip sets changed between prompt conditions")
    common_clips = sorted(base_doc_index["clip_id"].astype(str))
    base_position = dict(zip(base_doc_index["clip_id"].astype(str), base_doc_index.index, strict=True))
    neutral_position = dict(
        zip(neutral_doc_index["clip_id"].astype(str), neutral_doc_index.index, strict=True)
    )
    base_order = np.asarray([base_position[clip] for clip in common_clips])
    neutral_order = np.asarray([neutral_position[clip] for clip in common_clips])

    base_vectors = np.load(args.base_embeddings / "document_embeddings.npy").astype("float32")[base_order]
    neutral_vectors = np.load(args.neutral_embeddings / "document_embeddings.npy").astype("float32")[neutral_order]
    base_vectors /= np.maximum(np.linalg.norm(base_vectors, axis=1, keepdims=True), 1e-12)
    neutral_vectors /= np.maximum(np.linalg.norm(neutral_vectors, axis=1, keepdims=True), 1e-12)
    query_index = pd.read_parquet(args.base_embeddings / "query_index.parquet")
    query_vectors = np.load(args.base_embeddings / "query_embeddings.npy").astype("float32")
    query_vectors /= np.maximum(np.linalg.norm(query_vectors, axis=1, keepdims=True), 1e-12)
    query_position = dict(zip(query_index["query_id"], query_index.index, strict=True))

    metadata_wide = base_metadata.pivot_table(
        index="clip_id", columns="facet_name", values="facet_value", aggfunc="first"
    ).reindex(common_clips)
    qrels_by_scoring: dict[str, dict[str, set[str]]] = {}
    for scoring, filename in (("strict", "qrels.tsv"), ("semantic", "qrels_semantic.tsv")):
        qrels = pd.read_csv(args.base_canonical / filename, sep="\t")
        qrels_by_scoring[scoring] = qrels.groupby("query_id")["target_id"].apply(set).to_dict()

    rows: list[dict] = []
    all_candidates = np.arange(len(common_clips))
    clip_array = np.asarray(common_clips)
    for query in base_queries.itertuples(index=False):
        query_vector = query_vectors[query_position[query.query_id]]
        filter_map = dict(query.metadata_filter)
        candidate_mask = np.ones(len(common_clips), dtype=bool)
        for facet, value in filter_map.items():
            candidate_mask &= metadata_wide[facet].astype(str).to_numpy() == str(value)
        b4_candidates = np.flatnonzero(candidate_mask)
        scores_by_prompt = {
            "task_aware": base_vectors @ query_vector,
            "task_neutral": neutral_vectors @ query_vector,
        }
        for prompt_condition, scores in scores_by_prompt.items():
            rankings = {
                "B2_vector_only": top_indices(scores, all_candidates, 100),
                "B4_prefilter_vector": top_indices(scores, b4_candidates, 100),
            }
            for scoring, relevant_sets in qrels_by_scoring.items():
                relevant_set = relevant_sets[query.query_id]
                relevant = np.fromiter(
                    (clip in relevant_set for clip in clip_array),
                    dtype=bool,
                    count=len(clip_array),
                )
                for strategy, ranking in rankings.items():
                    rows.append(
                        {
                            "query_id": query.query_id,
                            "family": query.family,
                            "predicate": query.difficulty,
                            "relevance_def": query.relevance_def,
                            "prompt_condition": prompt_condition,
                            "strategy": strategy,
                            "scoring": scoring,
                            **ranking_metrics(ranking, relevant),
                        }
                    )
    long = pd.DataFrame(rows)
    key = ["query_id", "family", "predicate", "relevance_def", "strategy", "scoring"]
    paired = long.pivot(index=key, columns="prompt_condition").reset_index()
    paired.columns = [
        "_".join(value for value in column if value)
        if isinstance(column, tuple)
        else column
        for column in paired.columns
    ]
    for metric in ("ndcg_at_10", "mrr", "recall_at_20"):
        paired[f"{metric}_neutral_minus_aware"] = (
            paired[f"{metric}_task_neutral"] - paired[f"{metric}_task_aware"]
        )

    primary = paired[
        (paired["strategy"] == "B2_vector_only") & (paired["scoring"] == "semantic")
    ]
    primary_values = primary["ndcg_at_10_neutral_minus_aware"].to_numpy(float)
    primary_lo, primary_hi = cluster_bootstrap(
        primary, "ndcg_at_10_neutral_minus_aware", args.seed, args.bootstrap
    )
    primary_p = cluster_signflip_p(
        primary, "ndcg_at_10_neutral_minus_aware", args.seed, args.bootstrap
    )
    aware_mean = float(primary["ndcg_at_10_task_aware"].mean())
    neutral_mean = float(primary["ndcg_at_10_task_neutral"].mean())
    relative_drop = (
        max(0.0, aware_mean - neutral_mean) / aware_mean if aware_mean > 0 else float("nan")
    )

    comparisons: list[dict] = []
    for (strategy, scoring), subset in paired.groupby(["strategy", "scoring"]):
        for metric in ("ndcg_at_10", "mrr", "recall_at_20"):
            column = f"{metric}_neutral_minus_aware"
            lo, hi = cluster_bootstrap(subset, column, args.seed, args.bootstrap)
            p_value = cluster_signflip_p(
                subset, column, args.seed + len(comparisons), args.bootstrap
            )
            comparisons.append(
                {
                    "strategy": strategy,
                    "scoring": scoring,
                    "metric": metric,
                    "task_aware": float(subset[f"{metric}_task_aware"].mean()),
                    "task_neutral": float(subset[f"{metric}_task_neutral"].mean()),
                    "neutral_minus_aware": float(subset[column].mean()),
                    "family_cluster_ci_lo": lo,
                    "family_cluster_ci_hi": hi,
                    "family_cluster_signflip_p": p_value,
                    "is_primary": bool(
                        strategy == "B2_vector_only"
                        and scoring == "semantic"
                        and metric == "ndcg_at_10"
                    ),
                }
            )
    comparisons_frame = pd.DataFrame(comparisons)
    comparisons_frame["holm_p_secondary_family"] = np.nan
    secondary = ~comparisons_frame["is_primary"]
    comparisons_frame.loc[secondary, "holm_p_secondary_family"] = holm_adjust(
        comparisons_frame.loc[secondary, "family_cluster_signflip_p"].to_numpy()
    )

    from transformers import AutoTokenizer

    embedding_tokenizer = AutoTokenizer.from_pretrained(
        str(PROJECT_ROOT / "Datasets" / "models" / "huggingface" / "BAAI--bge-m3")
    )
    generation_tokenizer = AutoTokenizer.from_pretrained(
        "/hdd2/huggingface_cache/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/"
        "snapshots/cc594898137f460bfe9f0759e9844b3ce807cfb5"
    )
    base_documents = pd.read_parquet(args.base_canonical / "documents.parquet")
    neutral_documents = pd.read_parquet(args.neutral_canonical / "documents.parquet")
    diagnostics = {
        "task_aware": caption_diagnostics(
            base_documents, generation_tokenizer, embedding_tokenizer
        ),
        "task_neutral": caption_diagnostics(
            neutral_documents, generation_tokenizer, embedding_tokenizer
        ),
    }

    adverse_sensitivity_large = bool(relative_drop > 0.10 or primary_hi < -0.03)
    material_effect_either_direction = bool(primary_lo > 0.03 or primary_hi < -0.03)
    if adverse_sensitivity_large:
        interpretation = (
            "Large adverse sensitivity: disclose task-aware prompt dependence and "
            "avoid prompt-independent claims."
        )
    elif material_effect_either_direction:
        interpretation = (
            "A material prompt effect was observed in the opposite/non-adverse direction; "
            "report its direction and avoid general prompt-independence claims."
        )
    else:
        interpretation = (
            "Robust only to this one frozen task-neutral prompt; no general "
            "prompt-independence claim."
        )
    summary = {
        "analysis": "E0 task-aware versus task-neutral caption prompt",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "primary": {
            "metric": "B2 exact semantic nDCG@10",
            "queries": int(len(primary)),
            "families": int(primary["family"].nunique()),
            "task_aware": aware_mean,
            "task_neutral": neutral_mean,
            "neutral_minus_aware": float(primary_values.mean()),
            "family_cluster_bootstrap_ci": [primary_lo, primary_hi],
            "family_cluster_signflip_p_two_sided": primary_p,
            "win_tie_loss": {
                "neutral_win": int((primary_values > 0).sum()),
                "tie": int((primary_values == 0).sum()),
                "neutral_loss": int((primary_values < 0).sum()),
            },
            "relative_drop": relative_drop,
        },
        "caption_diagnostics": diagnostics,
        "adverse_prompt_sensitivity_large_by_frozen_rule": adverse_sensitivity_large,
        "material_prompt_effect_either_direction": material_effect_either_direction,
        "interpretation": interpretation,
    }
    manifest = {
        "script": Path(__file__).name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parameters": {
            "bootstrap": args.bootstrap,
            "seed": args.seed,
            "ranking": "exact normalized inner product, deterministic tie break",
            "query_vectors": "frozen task-aware-lane query vectors used for both conditions",
        },
        "input_sha256": {
            "base_queries": sha256_file(args.base_canonical / "queries.jsonl"),
            "neutral_queries": sha256_file(args.neutral_canonical / "queries.jsonl"),
            "qrels": qrel_hashes,
            "base_metadata": sha256_file(args.base_canonical / "metadata.parquet"),
            "neutral_metadata": sha256_file(args.neutral_canonical / "metadata.parquet"),
            "base_document_embeddings": sha256_file(
                args.base_embeddings / "document_embeddings.npy"
            ),
            "neutral_document_embeddings": sha256_file(
                args.neutral_embeddings / "document_embeddings.npy"
            ),
        },
        "controlled_equalities": {
            "caption_generation_except_prompt": base_control,
            "base_caption_shards": base_shards,
            "neutral_caption_shards": neutral_shards,
            "caption_frame_identities": len(base_caption_docs),
            "queries_equal": True,
            "strict_qrels_equal_after_sort": True,
            "semantic_qrels_equal_after_sort": True,
            "metadata_equal_after_sort": True,
        },
        "prompt_sha256": {
            "base": sorted(base_prompt_hashes)[0],
            "neutral": sorted(neutral_prompt_hashes)[0],
        },
    }
    long.to_parquet(args.output_dir / "metrics_long.parquet", index=False)
    paired.to_csv(args.output_dir / "paired_query_metrics.csv", index=False)
    comparisons_frame.to_csv(args.output_dir / "comparisons.csv", index=False)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
