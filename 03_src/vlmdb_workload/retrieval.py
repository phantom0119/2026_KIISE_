"""BM25, vector, metadata, and hybrid retrieval baselines."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi

from .io import load_canonical, write_json
from .metrics import evaluate_ranking


TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+")


@dataclass(frozen=True)
class RetrievalRunResult:
    output_dir: Path
    strategies: list[str]
    queries: int
    result_rows: int


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(str(text).lower())


def metadata_pivot(metadata: pd.DataFrame) -> pd.DataFrame:
    return (
        metadata.pivot_table(index="clip_id", columns="facet_name", values="facet_value", aggfunc="first")
        .reset_index()
        .fillna("")
    )


def filter_clip_ids(metadata_wide: pd.DataFrame, filters: dict[str, Any]) -> set[str]:
    if not filters:
        return set(metadata_wide["clip_id"])
    mask = pd.Series(True, index=metadata_wide.index)
    for facet, value in filters.items():
        if facet not in metadata_wide.columns:
            return set()
        mask &= metadata_wide[facet].eq(value)
    return set(metadata_wide.loc[mask, "clip_id"])


def rank_docs_to_clips(
    doc_indices: np.ndarray,
    scores: np.ndarray,
    doc_index: pd.DataFrame,
    *,
    candidate_clips: set[str] | None = None,
    max_rank: int = 100,
) -> list[tuple[str, float]]:
    best: dict[str, float] = {}
    for doc_idx, score in zip(doc_indices.tolist(), scores.tolist(), strict=False):
        if doc_idx < 0:
            continue
        clip_id = doc_index.iloc[int(doc_idx)]["clip_id"]
        if candidate_clips is not None and clip_id not in candidate_clips:
            continue
        score = float(score)
        if clip_id not in best or score > best[clip_id]:
            best[clip_id] = score
    ranked = sorted(best.items(), key=lambda item: (-item[1], item[0]))
    return ranked[:max_rank]


def rrf_fuse(
    rankings: list[list[tuple[str, float]]],
    *,
    rrf_k: int = 60,
    max_rank: int = 100,
) -> list[tuple[str, float]]:
    scores: dict[str, float] = {}
    for ranking in rankings:
        for rank, (clip_id, _score) in enumerate(ranking, start=1):
            scores[clip_id] = scores.get(clip_id, 0.0) + 1.0 / (rrf_k + rank)
    return sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:max_rank]


class RetrievalExperimentRunner:
    """Run B0-B5 retrieval baselines on a canonical workload."""

    def __init__(
        self,
        canonical_root: Path,
        embedding_root: Path,
        output_dir: Path,
        top_ks: list[int],
        max_rank: int = 100,
        postfilter_doc_k: int = 200,
        max_queries: int | None = None,
        max_queries_per_difficulty: int | None = None,
    ) -> None:
        self.canonical_root = canonical_root
        self.embedding_root = embedding_root
        self.output_dir = output_dir
        self.top_ks = top_ks
        self.max_rank = max_rank
        self.postfilter_doc_k = postfilter_doc_k
        self.max_queries = max_queries
        self.max_queries_per_difficulty = max_queries_per_difficulty

        self.clips, self.documents, self.metadata, self.queries, self.qrels = load_canonical(canonical_root)
        self.metadata_wide = metadata_pivot(self.metadata)
        self.doc_index = pd.read_parquet(embedding_root / "document_index.parquet")
        self.query_index = pd.read_parquet(embedding_root / "query_index.parquet")
        self.doc_embeddings = np.load(embedding_root / "document_embeddings.npy").astype("float32")
        self.query_embeddings = np.load(embedding_root / "query_embeddings.npy").astype("float32")
        self.embedding_manifest = json.loads((embedding_root / "embedding_manifest.json").read_text(encoding="utf-8"))

        if len(self.documents) != len(self.doc_embeddings):
            raise ValueError("Document count and document embedding count differ.")
        if len(self.queries) != len(self.query_embeddings):
            raise ValueError("Query count and query embedding count differ.")

        self.positives_by_query = {
            query_id: set(group["target_id"])
            for query_id, group in self.qrels.groupby("query_id", sort=False)
        }

        self.tokenized_docs = [tokenize(text) for text in self.documents["text"].fillna("").tolist()]
        start = time.perf_counter()
        self.bm25 = BM25Okapi(self.tokenized_docs)
        self.bm25_build_sec = time.perf_counter() - start

        vectors = np.ascontiguousarray(self.doc_embeddings.copy())
        faiss.normalize_L2(vectors)
        start = time.perf_counter()
        self.faiss_index = faiss.IndexFlatIP(vectors.shape[1])
        self.faiss_index.add(vectors)
        self.faiss_build_sec = time.perf_counter() - start
        self._faiss_vectors = vectors

    def run(self, overwrite: bool = False) -> RetrievalRunResult:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if any(self.output_dir.iterdir()) and not overwrite:
            raise FileExistsError(f"{self.output_dir} is not empty. Use overwrite=True.")

        result_rows: list[dict[str, Any]] = []
        metric_rows: list[dict[str, Any]] = []
        strategies = ["B0_metadata_only", "B1_bm25_only", "B2_vector_only", "B3_vector_postfilter", "B4_prefilter_vector", "B5_hybrid"]

        query_iter = self.queries.reset_index(drop=True).reset_index(names="_query_pos")
        if self.max_queries_per_difficulty is not None:
            query_iter = (
                query_iter.groupby("difficulty", sort=False)
                .head(self.max_queries_per_difficulty)
                .sort_values("_query_pos", kind="mergesort")
                .reset_index(drop=True)
            )
        if self.max_queries is not None:
            query_iter = query_iter.head(self.max_queries)
        executed_queries = int(len(query_iter))

        for _, query in query_iter.iterrows():
            query_pos = int(query["_query_pos"])
            query_id = query["query_id"]
            positives = self.positives_by_query.get(query_id, set())
            filters = dict(query["metadata_filter"] or {})
            query_text = query["query_text"]
            query_vector = np.ascontiguousarray(self.query_embeddings[query_pos].reshape(1, -1).astype("float32"))
            faiss.normalize_L2(query_vector)

            per_strategy = self._retrieve_all_strategies(query_text, query_vector, filters)
            for strategy, payload in per_strategy.items():
                ranking = [clip_id for clip_id, _score in payload["ranking"]]
                metrics = evaluate_ranking(ranking, positives, self.top_ks)
                metric_rows.append(
                    {
                        "strategy": strategy,
                        "query_id": query_id,
                        "difficulty": query["difficulty"],
                        "positive_count": int(query["positive_count"]),
                        "latency_ms": payload["latency_ms"],
                        **metrics,
                    }
                )
                for rank, (clip_id, score) in enumerate(payload["ranking"], start=1):
                    result_rows.append(
                        {
                            "strategy": strategy,
                            "query_id": query_id,
                            "rank": rank,
                            "clip_id": clip_id,
                            "score": score,
                            "is_relevant": clip_id in positives,
                        }
                    )

        results = pd.DataFrame(result_rows)
        metrics_by_query = pd.DataFrame(metric_rows)
        results.to_parquet(self.output_dir / "retrieval_results.parquet", index=False)
        metrics_by_query.to_parquet(self.output_dir / "metrics_by_query.parquet", index=False)

        summary = self._summarize_metrics(metrics_by_query)
        latency = self._summarize_latency(metrics_by_query)
        summary.to_csv(self.output_dir / "metrics_summary.csv", index=False)
        latency.to_csv(self.output_dir / "latency_summary.csv", index=False)
        self._write_manifest(strategies, len(results), executed_queries)
        self._write_summary_md(summary, latency)

        return RetrievalRunResult(
            output_dir=self.output_dir,
            strategies=strategies,
            queries=executed_queries,
            result_rows=len(results),
        )

    def _retrieve_all_strategies(
        self,
        query_text: str,
        query_vector: np.ndarray,
        filters: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        payloads: dict[str, dict[str, Any]] = {}

        candidate_clips = filter_clip_ids(self.metadata_wide, filters)

        start = time.perf_counter()
        metadata_ranking = [(clip_id, 1.0) for clip_id in sorted(candidate_clips)[: self.max_rank]]
        payloads["B0_metadata_only"] = {
            "ranking": metadata_ranking,
            "latency_ms": (time.perf_counter() - start) * 1000.0,
        }

        start = time.perf_counter()
        bm25_ranking = self._bm25_clip_ranking(query_text)
        payloads["B1_bm25_only"] = {
            "ranking": bm25_ranking,
            "latency_ms": (time.perf_counter() - start) * 1000.0,
        }

        start = time.perf_counter()
        vector_ranking = self._faiss_clip_ranking(query_vector, top_docs=len(self.documents))
        payloads["B2_vector_only"] = {
            "ranking": vector_ranking,
            "latency_ms": (time.perf_counter() - start) * 1000.0,
        }

        start = time.perf_counter()
        post_ranking = self._faiss_clip_ranking(
            query_vector,
            top_docs=min(self.postfilter_doc_k, len(self.documents)),
            candidate_clips=candidate_clips,
        )
        payloads["B3_vector_postfilter"] = {
            "ranking": post_ranking,
            "latency_ms": (time.perf_counter() - start) * 1000.0,
        }

        start = time.perf_counter()
        pref_vector_ranking = self._vector_prefilter_ranking(query_vector, candidate_clips)
        payloads["B4_prefilter_vector"] = {
            "ranking": pref_vector_ranking,
            "latency_ms": (time.perf_counter() - start) * 1000.0,
        }

        start = time.perf_counter()
        pref_bm25_ranking = self._bm25_clip_ranking(query_text, candidate_clips=candidate_clips)
        pref_vector_for_hybrid = self._vector_prefilter_ranking(query_vector, candidate_clips)
        hybrid_ranking = rrf_fuse([pref_bm25_ranking, pref_vector_for_hybrid], max_rank=self.max_rank)
        payloads["B5_hybrid"] = {
            "ranking": hybrid_ranking,
            "latency_ms": (time.perf_counter() - start) * 1000.0,
        }

        return payloads

    def _bm25_clip_ranking(
        self,
        query_text: str,
        *,
        candidate_clips: set[str] | None = None,
    ) -> list[tuple[str, float]]:
        scores = self.bm25.get_scores(tokenize(query_text)).astype("float32")
        order = np.argsort(-scores, kind="mergesort")
        return rank_docs_to_clips(order, scores[order], self.doc_index, candidate_clips=candidate_clips, max_rank=self.max_rank)

    def _faiss_clip_ranking(
        self,
        query_vector: np.ndarray,
        *,
        top_docs: int,
        candidate_clips: set[str] | None = None,
    ) -> list[tuple[str, float]]:
        scores, indices = self.faiss_index.search(query_vector, top_docs)
        return rank_docs_to_clips(indices[0], scores[0], self.doc_index, candidate_clips=candidate_clips, max_rank=self.max_rank)

    def _vector_prefilter_ranking(
        self,
        query_vector: np.ndarray,
        candidate_clips: set[str],
    ) -> list[tuple[str, float]]:
        if not candidate_clips:
            return []
        doc_clip_ids = self.doc_index["clip_id"].to_numpy()
        mask = np.array([clip_id in candidate_clips for clip_id in doc_clip_ids])
        indices = np.flatnonzero(mask)
        if len(indices) == 0:
            return []
        scores = self._faiss_vectors[indices] @ query_vector[0]
        order = np.argsort(-scores, kind="mergesort")
        return rank_docs_to_clips(indices[order], scores[order], self.doc_index, max_rank=self.max_rank)

    def _summarize_metrics(self, metrics_by_query: pd.DataFrame) -> pd.DataFrame:
        metric_cols = [
            col
            for col in metrics_by_query.columns
            if col.startswith("recall_at_") or col.startswith("hit_at_") or col in {"mrr", "ndcg_at_10"}
        ]
        rows = []
        for (strategy, difficulty), group in metrics_by_query.groupby(["strategy", "difficulty"], sort=False):
            row = {"strategy": strategy, "difficulty": difficulty, "queries": len(group)}
            row.update({col: group[col].mean() for col in metric_cols})
            rows.append(row)
        for strategy, group in metrics_by_query.groupby("strategy", sort=False):
            row = {"strategy": strategy, "difficulty": "all", "queries": len(group)}
            row.update({col: group[col].mean() for col in metric_cols})
            rows.append(row)
        return pd.DataFrame(rows)

    def _summarize_latency(self, metrics_by_query: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for strategy, group in metrics_by_query.groupby("strategy", sort=False):
            rows.append(
                {
                    "strategy": strategy,
                    "queries": len(group),
                    "latency_mean_ms": group["latency_ms"].mean(),
                    "latency_p50_ms": group["latency_ms"].quantile(0.50),
                    "latency_p95_ms": group["latency_ms"].quantile(0.95),
                }
            )
        return pd.DataFrame(rows)

    def _write_manifest(self, strategies: list[str], result_rows: int, executed_queries: int) -> None:
        manifest = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "canonical_root": str(self.canonical_root),
            "embedding_root": str(self.embedding_root),
            "output_dir": str(self.output_dir),
            "embedding_manifest": self.embedding_manifest,
            "strategies": strategies,
            "top_ks": self.top_ks,
            "max_rank": self.max_rank,
            "postfilter_doc_k": self.postfilter_doc_k,
            "max_queries": self.max_queries,
            "max_queries_per_difficulty": self.max_queries_per_difficulty,
            "bm25_backend": "rank_bm25.BM25Okapi",
            "vector_backend": "faiss.IndexFlatIP",
            "vector_filtering": "external metadata filter for B3/B4/B5",
            "bm25_build_sec": self.bm25_build_sec,
            "faiss_build_sec": self.faiss_build_sec,
            "counts": {
                "clips": int(len(self.clips)),
                "documents": int(len(self.documents)),
                "queries": int(len(self.queries)),
                "executed_queries": int(executed_queries),
                "qrels": int(len(self.qrels)),
                "result_rows": int(result_rows),
            },
        }
        write_json(self.output_dir / "run_manifest.json", manifest)

    def _write_summary_md(self, metrics_summary: pd.DataFrame, latency_summary: pd.DataFrame) -> None:
        all_rows = metrics_summary[metrics_summary["difficulty"].eq("all")].copy()
        metric_cols = ["recall_at_1", "recall_at_5", "recall_at_10", "recall_at_20", "mrr", "ndcg_at_10"]
        lines = [
            "# Retrieval Baseline Summary",
            "",
            f"created_at: `{datetime.now(timezone.utc).isoformat()}`",
            f"canonical_root: `{self.canonical_root}`",
            f"embedding_root: `{self.embedding_root}`",
            "",
            "## Overall Metrics",
            "",
            "| strategy | " + " | ".join(metric_cols) + " |",
            "|---" + "|---:" * len(metric_cols) + "|",
        ]
        for row in all_rows.to_dict("records"):
            values = [f"{float(row[col]):.4f}" for col in metric_cols]
            lines.append(f"| {row['strategy']} | " + " | ".join(values) + " |")

        lines.extend(
            [
                "",
                "## Latency",
                "",
                "| strategy | mean ms | p50 ms | p95 ms |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in latency_summary.to_dict("records"):
            lines.append(
                f"| {row['strategy']} | {row['latency_mean_ms']:.3f} | "
                f"{row['latency_p50_ms']:.3f} | {row['latency_p95_ms']:.3f} |"
            )
        (self.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
