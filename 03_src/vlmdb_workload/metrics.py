"""Retrieval metrics for clip-level VLM-DB workload evaluation."""

from __future__ import annotations

import math
from collections.abc import Sequence


def recall_at_k(ranking: Sequence[str], positives: set[str], k: int) -> float:
    if not positives:
        return 0.0
    hits = len(set(ranking[:k]) & positives)
    return hits / len(positives)


def hit_at_k(ranking: Sequence[str], positives: set[str], k: int) -> float:
    return 1.0 if set(ranking[:k]) & positives else 0.0


def reciprocal_rank(ranking: Sequence[str], positives: set[str]) -> float:
    for idx, item_id in enumerate(ranking, start=1):
        if item_id in positives:
            return 1.0 / idx
    return 0.0


def ndcg_at_k(ranking: Sequence[str], positives: set[str], k: int, relevance: float = 3.0) -> float:
    if not positives:
        return 0.0
    gain = (2.0**relevance) - 1.0
    dcg = 0.0
    for rank, item_id in enumerate(ranking[:k], start=1):
        if item_id in positives:
            dcg += gain / math.log2(rank + 1)

    ideal_hits = min(len(positives), k)
    idcg = sum(gain / math.log2(rank + 1) for rank in range(1, ideal_hits + 1))
    return dcg / idcg if idcg else 0.0


def evaluate_ranking(ranking: Sequence[str], positives: set[str], top_ks: Sequence[int]) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for k in top_ks:
        metrics[f"recall_at_{k}"] = recall_at_k(ranking, positives, k)
        metrics[f"hit_at_{k}"] = hit_at_k(ranking, positives, k)
    metrics["mrr"] = reciprocal_rank(ranking, positives)
    metrics["ndcg_at_10"] = ndcg_at_k(ranking, positives, 10)
    return metrics
