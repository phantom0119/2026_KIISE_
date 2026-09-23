#!/usr/bin/env python3
"""Post-result weighted-RRF robustness audit for IntentStore P0-C."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import analyze_safety_representation as base


WEIGHTS = [(8, 1), (4, 1), (2, 1), (1, 1), (1, 2), (1, 4)]
SERVICES = ["dynamic_event", "scene_state", "context_filtered", "open_event"]
MIN_GAIN = 0.02
ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def weighted_rrf(left: list[str], right: list[str], left_weight: float, right_weight: float) -> list[str]:
    scores: dict[str, float] = {}
    for rank, clip_id in enumerate(left, start=1):
        scores[clip_id] = scores.get(clip_id, 0.0) + left_weight / (base.RRF_K + rank)
    for rank, clip_id in enumerate(right, start=1):
        scores[clip_id] = scores.get(clip_id, 0.0) + right_weight / (base.RRF_K + rank)
    return sorted(scores, key=lambda clip: (-scores[clip], clip))[: base.MAX_RANK]


def rebuild_rankings(dataset: str, config: dict, query_embeddings: np.ndarray) -> tuple[list[dict], dict[str, dict]]:
    canonical = Path(config["canonical"])
    visual = Path(config["visual"])
    text_root = Path(config["text_results"])
    queries = base.read_queries(canonical / "queries.jsonl")
    metadata = pd.read_parquet(canonical / "metadata.parquet")
    qrels = pd.read_csv(canonical / "qrels.tsv", sep="\t")
    frame_index = pd.read_parquet(visual / "frame_index.parquet").reset_index(drop=True)
    frame_embeddings = np.load(visual / "frame_embeddings.npy").astype("float32")
    text_results = pd.read_parquet(text_root / "retrieval_results.parquet")
    clip_meta, facet_lookup = base.metadata_map(metadata)
    clip_ids = set(clip_meta)
    positives = {
        str(query_id): set(group["target_id"].astype(str))
        for query_id, group in qrels.groupby("query_id", sort=False)
    }
    text_lookup = {
        (str(strategy), str(query_id)): group.sort_values("rank")["clip_id"].astype(str).tolist()
        for (strategy, query_id), group in text_results.groupby(["strategy", "query_id"], sort=False)
    }
    metas: list[dict] = []
    ranks: dict[str, dict] = {}
    for pos, query in enumerate(queries):
        query_id = str(query["query_id"])
        filters = dict(query.get("metadata_filter") or {})
        candidates = base.candidates_for(filters, clip_ids, facet_lookup)
        text_strategy = "B2_vector_only" if not filters else "B4_prefilter_vector"
        caption = text_lookup[(text_strategy, query_id)][: base.MAX_RANK]
        scores = frame_embeddings @ query_embeddings[pos]
        visual_rank = base.rank_visual(scores, frame_index, candidates, "all")
        event_type = base.infer_event_type(positives[query_id], str(config["semantic_facet"]), clip_meta)
        metas.append(
            {
                "dataset": dataset,
                "query_id": query_id,
                "event_type": event_type,
                "event_family": base.event_family(dataset, event_type),
                "contract_family": "open_event" if not filters else "context_filtered",
                "cluster": f"{dataset}|{event_type}",
            }
        )
        ranks[query_id] = {"caption": caption, "visual": visual_rank, "positives": positives[query_id]}
    return metas, ranks


def main() -> int:
    metric_rows: list[dict] = []
    meta_rows: list[dict] = []
    all_ranks: dict[str, dict] = {}
    for dataset, config in base.CONFIGS.items():
        embeddings = np.load(RESULTS / f"safety_clip_query_embeddings_{dataset.lower()}.npy").astype("float32")
        metas, ranks = rebuild_rankings(dataset, config, embeddings)
        meta_rows.extend(metas)
        all_ranks.update(ranks)

    meta = pd.DataFrame(meta_rows).set_index("query_id")
    for query_id, row in meta.iterrows():
        item = all_ranks[query_id]
        caption_metric = base.evaluate(item["caption"], item["positives"])["ndcg_at_10"]
        for text_weight, visual_weight in WEIGHTS:
            strategy = f"rrf_t{text_weight}_v{visual_weight}"
            ranking = weighted_rrf(item["caption"], item["visual"], text_weight, visual_weight)
            metric_rows.append(
                {
                    **row.to_dict(),
                    "query_id": query_id,
                    "strategy": strategy,
                    "text_weight": text_weight,
                    "visual_weight": visual_weight,
                    "caption_ndcg_at_10": caption_metric,
                    "fusion_ndcg_at_10": base.evaluate(ranking, item["positives"])["ndcg_at_10"],
                }
            )
    metrics = pd.DataFrame(metric_rows)
    metrics["diff"] = metrics["fusion_ndcg_at_10"] - metrics["caption_ndcg_at_10"]

    test_rows = []
    offset = 0
    for service in SERVICES:
        if service in {"dynamic_event", "scene_state"}:
            service_part = metrics[metrics["event_family"].eq(service)]
        else:
            service_part = metrics[metrics["contract_family"].eq(service)]
        for strategy, group in service_part.groupby("strategy", sort=False):
            diff = group["diff"].to_numpy(dtype="float64")
            clusters = group["cluster"].to_numpy()
            rng = np.random.default_rng(base.SEED + 50_000 + offset * 1000)
            ci_low, ci_high = base.bootstrap_ci(diff, rng)
            cluster_mean, cluster_low, cluster_high, n_clusters = base.cluster_bootstrap(diff, clusters, rng)
            test_rows.append(
                {
                    "service": service,
                    "strategy": strategy,
                    "queries": len(diff),
                    "event_clusters": n_clusters,
                    "caption_mean": group["caption_ndcg_at_10"].mean(),
                    "fusion_mean": group["fusion_ndcg_at_10"].mean(),
                    "mean_diff": diff.mean(),
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "cluster_mean_diff": cluster_mean,
                    "cluster_ci_low": cluster_low,
                    "cluster_ci_high": cluster_high,
                    "p_value": base.signflip_pvalue(diff, rng),
                }
            )
            offset += 1
    tests = pd.DataFrame(test_rows)
    tests["q_value_bh"] = base.bh_adjust(tests["p_value"].tolist())
    tests["robust_gain"] = (
        tests["mean_diff"].ge(MIN_GAIN)
        & tests["q_value_bh"].lt(0.05)
        & tests["ci_low"].gt(0)
        & tests["cluster_ci_low"].gt(0)
    )
    status = "ROBUST_FUSION_GAIN_FOUND" if tests["robust_gain"].any() else "NO_ROBUST_FUSION_GAIN"

    metrics.to_csv(RESULTS / "safety_fusion_weight_metrics.csv", index=False)
    tests.to_csv(RESULTS / "safety_fusion_weight_tests.csv", index=False)
    decision = {
        "status": status,
        "robust_cells": tests.loc[tests["robust_gain"], ["service", "strategy"]].to_dict("records"),
        "best_fixed_weight_by_service": {
            service: str(group.sort_values("fusion_mean", ascending=False).iloc[0]["strategy"])
            for service, group in tests.groupby("service")
        },
        "maximum_gain_by_service": {
            service: float(group["mean_diff"].max()) for service, group in tests.groupby("service")
        },
        "analysis_type": "post-result robustness; not confirmatory",
    }
    (RESULTS / "safety_fusion_robustness_decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# P0-C 가중 fusion 사후 민감도 보고서",
        "",
        f"> 판정: **`{status}`**  ",
        "> P0-C 주 결과 확인 뒤 실행한 강건성 분석이며 confirmatory 결과가 아니다.",
        "",
        "| service | strategy | n | clusters | caption | fusion | diff | cluster 95% CI | q(BH-24) | robust gain |",
        "|---|---|---:|---:|---:|---:|---:|---|---:|---|",
    ]
    for row in tests.sort_values(["service", "fusion_mean"], ascending=[True, False]).to_dict("records"):
        lines.append(
            f"| {row['service']} | {row['strategy']} | {int(row['queries'])} | {int(row['event_clusters'])} | "
            f"{row['caption_mean']:.4f} | {row['fusion_mean']:.4f} | {row['mean_diff']:+.4f} | "
            f"[{row['cluster_ci_low']:+.4f}, {row['cluster_ci_high']:+.4f}] | {row['q_value_bh']:.6f} | "
            f"{'yes' if row['robust_gain'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## 해석",
            "",
            f"- robust gain 셀: `{len(decision['robust_cells'])}`개",
            f"- 서비스별 최대 평균 이득: `{json.dumps(decision['maximum_gain_by_service'], ensure_ascii=False)}`",
            "- 가중치 탐색 결과는 현재 CLIP 4-frame 표현의 보완성만 검사한다. temporal encoder·trajectory·event graph의 무가치를 뜻하지 않는다.",
            "",
        ]
    )
    (ROOT / "P0_CPU_FUSION_SENSITIVITY_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

