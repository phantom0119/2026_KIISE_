#!/usr/bin/env python3
"""S2: intersection-blocked robustness analysis for coupling and B4-B2.

This is a post-main-result robustness analysis governed by
project_md/archive/legacy_premerge_20260728/912_SUPPLEMENT_CONTROL_PROTOCOL_FROZEN_20260723.md.  It never uses
query outcomes to form folds, never relaxes support thresholds, and uses exact
inner-product rankings within each held-out fold.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VER = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
DEFAULT_CANONICAL = VER / "canonical_trisource_expanded"
DEFAULT_EMBEDDINGS = VER / "embeddings_trisource_expanded" / "bge-m3"
DEFAULT_OUT = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets"
    / "20260723_controlled_supplement" / "s2_blocked_coupling"
)


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def cramers_v(a: pd.Series, b: pd.Series) -> float:
    table = pd.crosstab(a, b).to_numpy(dtype=float)
    if min(table.shape, default=0) < 2 or table.sum() <= 1:
        return float("nan")
    row = table.sum(axis=1, keepdims=True)
    col = table.sum(axis=0, keepdims=True)
    expected = row @ col / table.sum()
    chi2 = np.where(expected > 0, (table - expected) ** 2 / expected, 0.0).sum()
    n = table.sum()
    r, k = table.shape
    phi2_corrected = max(0.0, chi2 / n - (k - 1) * (r - 1) / (n - 1))
    r_corrected = r - (r - 1) ** 2 / (n - 1)
    k_corrected = k - (k - 1) ** 2 / (n - 1)
    denominator = min(k_corrected - 1, r_corrected - 1)
    return float(np.sqrt(phi2_corrected / denominator)) if denominator > 0 else float("nan")


def ndcg_binary(ranked_indices: np.ndarray, relevant_mask: np.ndarray, k: int = 10) -> float:
    gains = relevant_mask[ranked_indices[:k]].astype(float)
    discounts = 1.0 / np.log2(np.arange(2, 2 + len(gains)))
    dcg = float(np.sum(gains * discounts))
    ideal_n = min(k, int(relevant_mask.sum()))
    if ideal_n == 0:
        return float("nan")
    idcg = float(np.sum(1.0 / np.log2(np.arange(2, 2 + ideal_n))))
    return dcg / idcg


def top_indices(scores: np.ndarray, candidates: np.ndarray, k: int) -> np.ndarray:
    """Deterministic score-desc/index-asc top-k."""
    if len(candidates) == 0:
        return np.empty(0, dtype=np.int64)
    candidate_scores = scores[candidates]
    order = np.lexsort((candidates, -candidate_scores))
    return candidates[order[:k]]


def stable_folds(intersection_ids: pd.Series, folds: int, seed: int) -> dict[str, int]:
    """Outcome-blind, balanced assignment after stable-hash ordering."""
    unique = sorted({str(value) for value in intersection_ids})
    ordered = sorted(
        unique,
        key=lambda value: hashlib.sha256(f"{seed}:{value}".encode()).hexdigest(),
    )
    return {value: index % folds for index, value in enumerate(ordered)}


def percentile_ci(values: np.ndarray, rng: np.random.Generator, draws: int) -> tuple[float, float]:
    values = values[np.isfinite(values)]
    if not len(values):
        return float("nan"), float("nan")
    sampled = values[rng.integers(0, len(values), size=(draws, len(values)))]
    means = sampled.mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def bootstrap_spearman(
    x: np.ndarray, y: np.ndarray, rng: np.random.Generator, draws: int
) -> tuple[float, float]:
    keep = np.isfinite(x) & np.isfinite(y)
    x, y = x[keep], y[keep]
    if len(x) < 3:
        return float("nan"), float("nan")
    samples: list[float] = []
    for _ in range(draws):
        idx = rng.integers(0, len(x), size=len(x))
        if np.unique(x[idx]).size < 2 or np.unique(y[idx]).size < 2:
            continue
        samples.append(float(spearmanr(x[idx], y[idx]).statistic))
    if not samples:
        return float("nan"), float("nan")
    return float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--embedding-root", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260723)
    parser.add_argument("--bootstrap", type=int, default=10000)
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--min-semantic-positives", type=int, default=5)
    parser.add_argument("--min-b4-candidates", type=int, default=10)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty; pass --overwrite")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    query_path = args.canonical_root / "queries.jsonl"
    document_embeddings_path = args.embedding_root / "document_embeddings.npy"
    expected_hashes = {
        "queries.jsonl": "e7f7ac5c312de626ca964792fc7822bd2e7f39c1096ade3260b481f10c054a1f",
        "document_embeddings.npy": "bf0614273dccff59333c96ebb91b87eb821d9fe85668f153e2d6d6abd9d77708",
    }
    observed_hashes = {
        "queries.jsonl": sha256_file(query_path),
        "document_embeddings.npy": sha256_file(document_embeddings_path),
    }
    if observed_hashes != expected_hashes:
        raise ValueError(f"frozen input hash mismatch: {observed_hashes}")

    queries = pd.DataFrame(load_jsonl(query_path))
    doc_index = pd.read_parquet(args.embedding_root / "document_index.parquet").reset_index(drop=True)
    query_index = pd.read_parquet(args.embedding_root / "query_index.parquet").reset_index(drop=True)
    document_vectors = np.load(document_embeddings_path).astype("float32")
    query_vectors = np.load(args.embedding_root / "query_embeddings.npy").astype("float32")
    document_vectors /= np.maximum(np.linalg.norm(document_vectors, axis=1, keepdims=True), 1e-12)
    query_vectors /= np.maximum(np.linalg.norm(query_vectors, axis=1, keepdims=True), 1e-12)
    query_position = dict(zip(query_index["query_id"], query_index.index, strict=True))

    clips = pd.read_parquet(args.canonical_root / "clips.parquet")
    visual = pd.read_parquet(VER / "visual_videos.parquet")[
        ["split", "visual_video_id", "intersection_id", "dt"]
    ]
    document_frame = (
        doc_index.reset_index(names="doc_pos")
        .merge(clips[["clip_id", "split", "visual_video_id"]], on="clip_id", validate="one_to_one")
        .merge(visual, on=["split", "visual_video_id"], validate="many_to_one")
        .sort_values("doc_pos")
        .reset_index(drop=True)
    )
    if not np.array_equal(document_frame["doc_pos"].to_numpy(), np.arange(len(doc_index))):
        raise AssertionError("document alignment changed")

    metadata = pd.read_parquet(args.canonical_root / "metadata.parquet")
    metadata_wide = metadata.pivot_table(
        index="clip_id", columns="facet_name", values="facet_value", aggfunc="first"
    )
    metadata_wide = metadata_wide.reindex(doc_index["clip_id"]).reset_index(drop=True).fillna("")

    qrels = pd.read_csv(args.canonical_root / "qrels_semantic.tsv", sep="\t")
    relevant_sets = qrels.groupby("query_id")["target_id"].apply(set).to_dict()
    clip_ids = doc_index["clip_id"].astype(str).to_numpy()
    fold_map = stable_folds(document_frame["intersection_id"], args.folds, args.seed)
    doc_folds = document_frame["intersection_id"].astype(str).map(fold_map).to_numpy()

    # A family shares one relevance definition and one categorical predicate.
    queries["family"] = queries["difficulty"].astype(str) + "::" + queries["relevance_def"].astype(str)
    family_relevant: dict[str, np.ndarray] = {}
    for family, group in queries.groupby("family", sort=True):
        reference_query_id = group.iloc[0]["query_id"]
        ref_set = relevant_sets[reference_query_id]
        if any(relevant_sets[query_id] != ref_set for query_id in group["query_id"]):
            raise AssertionError(f"semantic qrels differ within family {family}")
        family_relevant[family] = np.fromiter(
            (clip_id in ref_set for clip_id in clip_ids), dtype=bool, count=len(clip_ids)
        )

    query_rows: list[dict] = []
    pair_fold_rows: list[dict] = []
    for fold in range(args.folds):
        heldout = doc_folds == fold
        train = ~heldout
        heldout_indices = np.flatnonzero(heldout)
        for family, group in queries.groupby("family", sort=True):
            predicate = str(group.iloc[0]["difficulty"])
            relevance_def = str(group.iloc[0]["relevance_def"])
            relevant_mask = family_relevant[family]
            train_v = cramers_v(
                pd.Series(metadata_wide[predicate].astype(str).to_numpy()[train]),
                pd.Series(relevant_mask[train].astype(str)),
            )
            deltas: list[float] = []
            for query in group.itertuples(index=False):
                metadata_filter = dict(query.metadata_filter)
                if set(metadata_filter) != {predicate}:
                    raise AssertionError(f"unexpected filter for {query.query_id}: {metadata_filter}")
                candidate_mask = heldout.copy()
                candidate_mask &= (
                    metadata_wide[predicate].astype(str).to_numpy()
                    == str(metadata_filter[predicate])
                )
                candidate_indices = np.flatnonzero(candidate_mask)
                positive_count = int((relevant_mask & heldout).sum())
                exclusion = None
                if positive_count < args.min_semantic_positives:
                    exclusion = "insufficient_semantic_positives"
                elif len(candidate_indices) < args.min_b4_candidates:
                    exclusion = "insufficient_b4_candidates"

                row = {
                    "fold": fold,
                    "family": family,
                    "predicate": predicate,
                    "relevance_def": relevance_def,
                    "query_id": query.query_id,
                    "metadata_value": str(metadata_filter[predicate]),
                    "train_cramers_v": train_v,
                    "heldout_documents": int(heldout.sum()),
                    "heldout_intersections": int(document_frame.loc[heldout, "intersection_id"].nunique()),
                    "semantic_positives": positive_count,
                    "b4_candidates": int(len(candidate_indices)),
                    "status": exclusion or "ok",
                }
                if exclusion is None:
                    vector = query_vectors[query_position[query.query_id]]
                    scores = document_vectors @ vector
                    b2 = top_indices(scores, heldout_indices, args.k)
                    b4 = top_indices(scores, candidate_indices, args.k)
                    b2_ndcg = ndcg_binary(b2, relevant_mask, args.k)
                    b4_ndcg = ndcg_binary(b4, relevant_mask, args.k)
                    delta = b4_ndcg - b2_ndcg
                    row.update(
                        {
                            "b2_ndcg_at_10": b2_ndcg,
                            "b4_ndcg_at_10": b4_ndcg,
                            "delta_b4_b2": delta,
                        }
                    )
                    deltas.append(delta)
                query_rows.append(row)
            pair_fold_rows.append(
                {
                    "fold": fold,
                    "family": family,
                    "predicate": predicate,
                    "relevance_def": relevance_def,
                    "train_cramers_v": train_v,
                    "eligible_queries": len(deltas),
                    "total_queries": len(group),
                    "mean_delta_b4_b2": float(np.mean(deltas)) if deltas else float("nan"),
                }
            )

    per_query = pd.DataFrame(query_rows)
    per_pair_fold = pd.DataFrame(pair_fold_rows)
    per_pair = (
        per_pair_fold.groupby(["family", "predicate", "relevance_def"], as_index=False)
        .agg(
            mean_train_cramers_v=("train_cramers_v", "mean"),
            mean_delta_b4_b2=("mean_delta_b4_b2", "mean"),
            eligible_queries=("eligible_queries", "sum"),
            folds_with_support=("mean_delta_b4_b2", "count"),
        )
    )

    x = per_pair["mean_train_cramers_v"].to_numpy(float)
    y = per_pair["mean_delta_b4_b2"].to_numpy(float)
    valid = np.isfinite(x) & np.isfinite(y)
    rho_result = spearmanr(x[valid], y[valid])
    rng = np.random.default_rng(args.seed)
    rho_lo, rho_hi = bootstrap_spearman(x, y, rng, args.bootstrap)

    per_pair["v_band"] = pd.cut(
        per_pair["mean_train_cramers_v"],
        bins=[-np.inf, 0.15, 0.30, np.inf],
        labels=["low", "mid", "high"],
        right=False,
    ).astype(str)
    band_rows: list[dict] = []
    for band in ("low", "mid", "high"):
        values = per_pair.loc[per_pair["v_band"] == band, "mean_delta_b4_b2"].to_numpy(float)
        lo, hi = percentile_ci(values, rng, args.bootstrap)
        band_rows.append(
            {
                "band": band,
                "families": int(np.isfinite(values).sum()),
                "mean_delta_b4_b2": float(np.nanmean(values)) if np.isfinite(values).any() else float("nan"),
                "ci_lo": lo,
                "ci_hi": hi,
            }
        )
    bands = pd.DataFrame(band_rows)

    sensitivity_rows: list[dict] = []
    for threshold in (0.15, 0.20, 0.25, 0.30, 0.35):
        selected = per_pair.loc[
            per_pair["mean_train_cramers_v"] >= threshold, "mean_delta_b4_b2"
        ].to_numpy(float)
        lo, hi = percentile_ci(selected, rng, args.bootstrap)
        sensitivity_rows.append(
            {
                "v_threshold": threshold,
                "families": int(np.isfinite(selected).sum()),
                "mean_delta_b4_b2": (
                    float(np.nanmean(selected)) if np.isfinite(selected).any() else float("nan")
                ),
                "ci_lo": lo,
                "ci_hi": hi,
            }
        )
    sensitivity = pd.DataFrame(sensitivity_rows)

    high_fold = per_pair_fold[per_pair_fold["train_cramers_v"] >= 0.30]
    fold_direction = (
        high_fold.groupby("fold")["mean_delta_b4_b2"].mean().reindex(range(args.folds))
    )
    high = bands.set_index("band").loc["high"]
    promotion_gate = {
        "high_families_at_least_5": bool(high["families"] >= 5),
        "high_family_ci_excludes_zero": bool(
            np.isfinite(high["ci_lo"]) and np.isfinite(high["ci_hi"])
            and (high["ci_lo"] > 0 or high["ci_hi"] < 0)
        ),
        "same_positive_direction_at_least_4_of_5_folds": bool((fold_direction > 0).sum() >= 4),
    }
    promotion_gate["all_pass"] = all(promotion_gate.values())

    summary = {
        "analysis": "S2 intersection-blocked post-main-result robustness",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "families": int(len(per_pair)),
        "queries": int(len(queries)),
        "intersections": int(document_frame["intersection_id"].nunique()),
        "fold_document_counts": {
            str(fold): int((doc_folds == fold).sum()) for fold in range(args.folds)
        },
        "eligible_query_fold_rows": int((per_query["status"] == "ok").sum()),
        "excluded_query_fold_rows": per_query.loc[
            per_query["status"] != "ok", "status"
        ].value_counts().to_dict(),
        "primary_spearman": {
            "rho": float(rho_result.statistic),
            "p_two_sided": float(rho_result.pvalue),
            "cluster_bootstrap_ci": [rho_lo, rho_hi],
        },
        "high_fold_mean_delta": {
            str(index): (None if not np.isfinite(value) else float(value))
            for index, value in fold_direction.items()
        },
        "promotion_gate": promotion_gate,
        "interpretation_rule": (
            "This is blocked robustness, not independent prospective confirmation. "
            "Keep the manuscript's exploratory wording unless every gate passes."
        ),
    }
    manifest = {
        "script": Path(__file__).name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parameters": vars(args) | {
            "canonical_root": str(args.canonical_root),
            "embedding_root": str(args.embedding_root),
            "output_dir": str(args.output_dir),
        },
        "input_sha256": observed_hashes,
        "fold_rule": "sort unique intersection_id by sha256(seed:id), then round-robin",
        "outcome_used_for_fold_assignment": False,
        "ranking": "exact normalized inner product, deterministic score-desc/index-asc",
    }

    per_query.to_csv(args.output_dir / "per_query_fold.csv", index=False)
    per_pair_fold.to_csv(args.output_dir / "per_pair_fold.csv", index=False)
    per_pair.to_csv(args.output_dir / "per_pair.csv", index=False)
    bands.to_csv(args.output_dir / "bands.csv", index=False)
    sensitivity.to_csv(args.output_dir / "threshold_sensitivity.csv", index=False)
    (args.output_dir / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    (args.output_dir / "sha256.txt").write_text(
        "\n".join(
            f"{sha256_file(path)}  {path.name}"
            for path in sorted(args.output_dir.iterdir())
            if path.is_file() and path.name != "sha256.txt"
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
