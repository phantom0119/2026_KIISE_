#!/usr/bin/env python3
"""Independent receipt checker for run_circularity_controlled_injection.py.

This checker intentionally reimplements tokenization, ranking, and binary
nDCG@10 instead of importing the workload metric/retrieval modules.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CANONICAL = (
    PROJECT_ROOT
    / "Datasets"
    / "processed"
    / "aihub_522_intersection"
    / "20260710"
    / "canonical_trisource_expanded"
)
DEFAULT_EMBEDDINGS = DEFAULT_CANONICAL.parent / "embeddings_trisource_expanded" / "bge-m3"
DEFAULT_OUTPUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260716_circularity_controlled_injection"
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


def args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--embedding-root", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--tolerance", type=float, default=1e-10)
    return parser.parse_args()


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(str(text).lower())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(8 * 1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def ndcg10(ranking: list[str], positives: set[str]) -> float:
    if not positives:
        return 0.0
    dcg = sum(1.0 / math.log2(rank + 1) for rank, item in enumerate(ranking[:10], start=1) if item in positives)
    ideal = min(10, len(positives))
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal + 1))
    return dcg / idcg


def rank(scores: np.ndarray, clip_ids: np.ndarray, candidates: np.ndarray | None = None) -> list[str]:
    indices = range(len(clip_ids)) if candidates is None else candidates.tolist()
    return [
        str(clip_ids[idx])
        for idx in sorted(indices, key=lambda idx: (-float(scores[idx]), str(clip_ids[idx])))[:100]
    ]


def normalize(values: np.ndarray) -> np.ndarray:
    values = values.astype("float32", copy=True)
    values /= np.linalg.norm(values, axis=1, keepdims=True)
    return values


def summary_value(frame: pd.DataFrame, condition: str, scoring: str) -> float:
    return float(
        frame.loc[frame["condition"].eq(condition) & frame["scoring"].eq(scoring), "ndcg_at_10"].iloc[0]
    )


def main() -> int:
    cfg = args()
    canonical = cfg.canonical_root.resolve()
    embeddings = cfg.embedding_root.resolve()
    output = cfg.output_dir.resolve()
    manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))

    checks: dict[str, dict[str, Any]] = {}

    def check(name: str, passed: bool, detail: Any = None) -> None:
        checks[name] = {"pass": bool(passed), "detail": detail}

    queries = [
        json.loads(line)
        for line in (canonical / "queries.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    semantic = pd.read_csv(canonical / "qrels_semantic.tsv", sep="\t")
    positives = semantic.groupby("query_id", sort=False)["target_id"].apply(set).to_dict()
    clean_documents = pd.read_parquet(canonical / "documents.parquet")
    full_documents = pd.read_parquet(output / "c2_documents_full_contamination.parquet")
    doc_index = pd.read_parquet(embeddings / "document_index.parquet")
    clip_ids = doc_index["clip_id"].astype(str).to_numpy()
    check("document_alignment", clean_documents["doc_id"].tolist() == full_documents["doc_id"].tolist())
    check("embedding_index_alignment", clean_documents["doc_id"].tolist() == doc_index["doc_id"].tolist())
    check("query_count_85", len(queries) == 85, len(queries))
    check("document_count_3000", len(clean_documents) == 3000, len(clean_documents))

    # Independent clean/full BM25 evaluation.
    bm25_means: dict[str, float] = {}
    bm25_per_query: dict[str, np.ndarray] = {}
    for condition, texts in [
        ("bm25_dose_0.00", clean_documents["text"].fillna("").tolist()),
        ("bm25_dose_1.00", full_documents["text"].fillna("").tolist()),
    ]:
        index = BM25Okapi([tokenize(text) for text in texts])
        values = []
        for query in queries:
            scores = index.get_scores(tokenize(query["query_text"])).astype("float32")
            values.append(ndcg10(rank(scores, clip_ids), positives[query["query_id"]]))
        bm25_per_query[condition] = np.asarray(values)
        bm25_means[condition] = float(np.mean(values))

    c2_summary = pd.read_csv(output / "c2_summary.csv")
    for condition, value in bm25_means.items():
        stored = summary_value(c2_summary, condition, "semantic")
        check(
            f"independent_{condition}",
            abs(value - stored) <= cfg.tolerance,
            {"independent": value, "stored": stored, "abs_diff": abs(value - stored)},
        )

    # Independent frozen dense B2 and scoring-specific qrel-oracle upper bound.
    frozen_docs = normalize(np.load(embeddings / "document_embeddings.npy"))
    frozen_queries = normalize(np.load(embeddings / "query_embeddings.npy"))
    frozen_values = []
    oracle_values = []
    clip_to_index = {clip_id: idx for idx, clip_id in enumerate(clip_ids)}
    for query_pos, query in enumerate(queries):
        gold = positives[query["query_id"]]
        scores = frozen_docs @ frozen_queries[query_pos]
        frozen_values.append(ndcg10(rank(scores, clip_ids), gold))
        candidates = np.asarray(sorted(clip_to_index[clip_id] for clip_id in gold), dtype=np.int64)
        oracle_values.append(ndcg10(rank(scores, clip_ids, candidates), gold))
    c1_summary = pd.read_csv(output / "c1_summary.csv")
    frozen_mean = float(np.mean(frozen_values))
    oracle_mean = float(np.mean(oracle_values))
    check(
        "independent_c1_clean_b2",
        abs(frozen_mean - summary_value(c1_summary, "clean_b2", "semantic")) <= cfg.tolerance,
        frozen_mean,
    )
    check("independent_c1_oracle_exact_one", oracle_mean == 1.0, oracle_mean)

    # Independently score the saved one-session BGE arrays.
    dense_query = normalize(np.load(output / "c2_bge_query_embeddings.npy"))
    dense_means = {}
    for condition, filename in [
        ("bge_clean_reembedded", "c2_bge_clean_document_embeddings.npy"),
        ("bge_full_contamination", "c2_bge_full_document_embeddings.npy"),
    ]:
        docs = normalize(np.load(output / filename))
        values = []
        for query_pos, query in enumerate(queries):
            scores = docs @ dense_query[query_pos]
            values.append(ndcg10(rank(scores, clip_ids), positives[query["query_id"]]))
        dense_means[condition] = float(np.mean(values))
        stored = summary_value(c2_summary, condition, "semantic")
        check(
            f"independent_{condition}",
            abs(dense_means[condition] - stored) <= cfg.tolerance,
            {"independent": dense_means[condition], "stored": stored, "abs_diff": abs(dense_means[condition] - stored)},
        )

    # Manifest hashes protect both frozen inputs and primary outputs.
    input_hash_failures = []
    for filename, expected in manifest["input_sha256"].items():
        path = Path(filename)
        actual = sha256_file(path)
        if actual != expected:
            input_hash_failures.append({"path": filename, "expected": expected, "actual": actual})
    check("manifest_input_hashes", not input_hash_failures, input_hash_failures)
    output_hash_failures = []
    for filename, expected in manifest["output_sha256"].items():
        path = output / filename
        actual = sha256_file(path)
        if actual != expected:
            output_hash_failures.append({"path": str(path), "expected": expected, "actual": actual})
    check("manifest_output_hashes", not output_hash_failures, output_hash_failures)

    failed = [name for name, payload in checks.items() if not payload["pass"]]
    receipt = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "verifier": str(Path(__file__).resolve()),
        "verifier_sha256": sha256_file(Path(__file__).resolve()),
        "status": "PASS" if not failed else "FAIL",
        "checks_passed": len(checks) - len(failed),
        "checks_total": len(checks),
        "failed_checks": failed,
        "independent_semantic_ndcg10": {
            "C1_clean_b2": frozen_mean,
            "C1_oracle": oracle_mean,
            **bm25_means,
            **dense_means,
        },
        "checks": checks,
    }
    (output / "independent_verification.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({key: receipt[key] for key in ["status", "checks_passed", "checks_total", "failed_checks"]}, indent=2))
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
