#!/usr/bin/env python3
"""Statistical, Pareto, and SLA analysis for the joint validation grid."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROOT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260717_joint_optimization_validation"
DEFAULT_CANONICAL = Path(
    "/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/"
    "qwen35_9b/522/canonical"
)
SEED = 20260717


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    p.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL)
    p.add_argument("--bootstrap-reps", type=int, default=10000)
    p.add_argument("--seed", type=int, default=SEED)
    return p.parse_args()


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while data := f.read(chunk):
            h.update(data)
    return h.hexdigest()


def infer_intent(text: str) -> str:
    value = text.lower()
    if "parked at the roadside" in value:
        return "parked_vehicle"
    if "very crowded" in value:
        return "crowded_scene"
    if "two or more buses" in value:
        return "buses"
    if "stopped in the roadway" in value:
        return "stopped_vehicle"
    if "bicycles or motorbikes" in value:
        return "two_wheeler"
    raise ValueError(f"Unknown visual intent: {text}")


def quantiles(values: np.ndarray) -> tuple[float, float]:
    lo, hi = np.quantile(values, [0.025, 0.975])
    return float(lo), float(hi)


def bootstrap_delta(
    delta: np.ndarray,
    query_samples: np.ndarray,
    cluster_samples: np.ndarray,
    cluster_inverse: np.ndarray,
    cluster_sizes: np.ndarray,
) -> dict[str, float]:
    query_boot = delta[query_samples].mean(axis=1)
    cluster_means = np.array([delta[cluster_inverse == idx].mean() for idx in range(len(cluster_sizes))])
    numerator = (cluster_means[cluster_samples] * cluster_sizes[cluster_samples]).sum(axis=1)
    denominator = cluster_sizes[cluster_samples].sum(axis=1)
    cluster_boot = numerator / denominator
    q_lo, q_hi = quantiles(query_boot)
    c_lo, c_hi = quantiles(cluster_boot)
    p_query = min(1.0, 2.0 * min(float(np.mean(query_boot <= 0)), float(np.mean(query_boot >= 0))))
    p_cluster = min(1.0, 2.0 * min(float(np.mean(cluster_boot <= 0)), float(np.mean(cluster_boot >= 0))))
    return {
        "mean_delta": float(delta.mean()),
        "query_ci_lo": q_lo,
        "query_ci_hi": q_hi,
        "cluster_ci_lo": c_lo,
        "cluster_ci_hi": c_hi,
        "p_query": p_query,
        "p_cluster": p_cluster,
        "wins": int(np.sum(delta > 1e-12)),
        "ties": int(np.sum(np.abs(delta) <= 1e-12)),
        "losses": int(np.sum(delta < -1e-12)),
    }


def bh_adjust(values: pd.Series) -> np.ndarray:
    p = values.to_numpy(float)
    order = np.argsort(p)
    ranked = p[order]
    adjusted = np.minimum.accumulate((ranked * len(p) / np.arange(1, len(p) + 1))[::-1])[::-1]
    result = np.empty_like(adjusted)
    result[order] = np.clip(adjusted, 0.0, 1.0)
    return result


def is_pareto(frame: pd.DataFrame) -> np.ndarray:
    quality = frame["ndcg_at_10"].to_numpy()
    latency = frame["latency_p95_ms"].to_numpy()
    storage = frame["index_mb"].to_numpy()
    keep = np.ones(len(frame), dtype=bool)
    for i in range(len(frame)):
        dominates = (
            (quality >= quality[i])
            & (latency <= latency[i])
            & (storage <= storage[i])
            & ((quality > quality[i]) | (latency < latency[i]) | (storage < storage[i]))
        )
        dominates[i] = False
        if dominates.any():
            keep[i] = False
    return keep


def corrected_task_fidelity(root: Path) -> pd.DataFrame:
    ranking = pd.read_parquet(root / "rankings.parquet")
    grouped = {
        (config, qid): group.sort_values("rank")["clip_id"].astype(str).tolist()
        for (config, qid), group in ranking.groupby(["config", "query_id"], sort=False)
    }
    configs = ranking["config"].drop_duplicates().tolist()
    qids = ranking["query_id"].drop_duplicates().tolist()
    rows = []
    for config in configs:
        representation, search_plan, index = config.split("__", 2)
        exact_config = f"{representation}__{search_plan}__flat"
        values = []
        exact_result_counts = []
        empty_exact_queries = 0
        for qid in qids:
            truth = grouped.get((exact_config, qid), [])[:10]
            estimate = grouped.get((config, qid), [])[:10]
            exact_result_counts.append(len(truth))
            # Recall to an empty exact reference is undefined.  Excluding the
            # query keeps the Flat self-anchor at 1.0 and avoids treating an
            # empty-vs-empty match as a fidelity failure.
            if not truth:
                empty_exact_queries += 1
                continue
            values.append(len(set(truth) & set(estimate)) / len(truth))
        rows.append(
            {
                "config": config,
                "representation": representation,
                "search_plan": search_plan,
                "index": index,
                "task_recall_to_exact_at_10": float(np.mean(values)),
                "exact_result_count_mean_at_10": float(np.mean(exact_result_counts)),
                "fidelity_evaluable_queries": len(values),
                "empty_exact_queries": empty_exact_queries,
            }
        )
    return pd.DataFrame(rows)


def format_ci(row: pd.Series, prefix: str = "query") -> str:
    return f"{row['mean_delta']:+.4f} [{row[prefix + '_ci_lo']:+.4f}, {row[prefix + '_ci_hi']:+.4f}]"


def main() -> int:
    args = parse_args()
    root = args.root
    metrics = pd.read_parquet(root / "per_query_metrics.parquet")
    summary = pd.read_csv(root / "configuration_summary.csv")
    queries = pd.DataFrame(
        [json.loads(line) for line in (args.canonical_root / "queries.jsonl").read_text().splitlines() if line.strip()]
    )
    queries["intent"] = queries["query_text"].map(infer_intent)
    queries["cluster"] = queries["intent"] + "|" + queries["difficulty"].astype(str)
    qids = queries["query_id"].astype(str).tolist()
    clusters, cluster_inverse = np.unique(queries["cluster"].to_numpy(), return_inverse=True)
    cluster_sizes = np.bincount(cluster_inverse)
    queries[["query_id", "intent", "difficulty", "cluster"]].to_csv(root / "query_clusters.csv", index=False)

    rng = np.random.default_rng(args.seed)
    query_samples = rng.integers(0, len(qids), size=(args.bootstrap_reps, len(qids)), dtype=np.int16)
    cluster_samples = rng.integers(
        0, len(clusters), size=(args.bootstrap_reps, len(clusters)), dtype=np.int16
    )

    values: dict[tuple[str, str], np.ndarray] = {}
    for (config, scoring), group in metrics.groupby(["config", "scoring"], sort=False):
        ordered = group.set_index("query_id").loc[qids]
        values[(str(config), str(scoring))] = ordered["ndcg_at_10"].to_numpy(float)

    config_parts = summary[["config", "representation", "search_plan", "index"]].drop_duplicates()
    representations = config_parts["representation"].drop_duplicates().astype(str).tolist()
    comparisons: list[tuple[str, str, str]] = []
    caption_anchor = "caption__B2_vector__flat"
    for representation in representations:
        if representation == "caption":
            continue
        comparisons.append(("storage", f"{representation}__B2_vector__flat", caption_anchor))
    for representation in representations:
        baseline = f"{representation}__B2_vector__flat"
        for plan in ("B3_postfilter", "B4_prefilter"):
            comparisons.append(("search", f"{representation}__{plan}__flat", baseline))
        if representation == "caption":
            comparisons.append(("search", "caption__B5_lexical_vector_hybrid__flat", baseline))
    for row in config_parts.itertuples(index=False):
        if row.index == "flat":
            continue
        comparisons.append(
            (
                "index",
                row.config,
                f"{row.representation}__{row.search_plan}__flat",
            )
        )

    comparison_rows = []
    for family, candidate, baseline in comparisons:
        for scoring in ("strict", "semantic"):
            delta = values[(candidate, scoring)] - values[(baseline, scoring)]
            comparison_rows.append(
                {
                    "family": family,
                    "scoring": scoring,
                    "candidate": candidate,
                    "baseline": baseline,
                    "queries": len(delta),
                    "clusters": len(clusters),
                    **bootstrap_delta(delta, query_samples, cluster_samples, cluster_inverse, cluster_sizes),
                }
            )
    comparisons_frame = pd.DataFrame(comparison_rows)
    comparisons_frame["q_query_bh"] = np.nan
    comparisons_frame["q_cluster_bh"] = np.nan
    for (_family, _scoring), index in comparisons_frame.groupby(["family", "scoring"]).groups.items():
        comparisons_frame.loc[index, "q_query_bh"] = bh_adjust(comparisons_frame.loc[index, "p_query"])
        comparisons_frame.loc[index, "q_cluster_bh"] = bh_adjust(comparisons_frame.loc[index, "p_cluster"])
    comparisons_frame.to_csv(root / "paired_bootstrap_comparisons.csv", index=False)

    fidelity = corrected_task_fidelity(root)
    fidelity.to_csv(root / "task_fidelity_corrected.csv", index=False)
    analyzed = summary.merge(fidelity[["config", "task_recall_to_exact_at_10"]], on="config", how="left")
    pareto_parts = []
    for scoring, group in analyzed.groupby("scoring", sort=False):
        group = group.copy()
        group["pareto_quality_latency_storage"] = is_pareto(group)
        pareto_parts.append(group)
    analyzed = pd.concat(pareto_parts, ignore_index=True)
    analyzed.to_csv(root / "analyzed_configuration_summary.csv", index=False)
    analyzed[analyzed["pareto_quality_latency_storage"]].to_csv(root / "pareto_front.csv", index=False)

    profiles = [
        ("quality_unconstrained", lambda frame: np.ones(len(frame), dtype=bool)),
        (
            "interactive_high_fidelity",
            lambda frame: (frame["latency_p95_ms"] <= 5.0)
            & (frame["index_mb"] <= 100.0)
            & (frame["task_recall_to_exact_at_10"] >= 0.95),
        ),
        (
            "submillisecond",
            lambda frame: frame["latency_p95_ms"] <= 1.0,
        ),
        (
            "memory_10mb",
            lambda frame: frame["index_mb"] <= 10.0,
        ),
        (
            "filtered_interactive",
            lambda frame: frame["search_plan"].eq("B4_prefilter")
            & (frame["latency_p95_ms"] <= 5.0)
            & (frame["task_recall_to_exact_at_10"] >= 0.95),
        ),
    ]
    winner_rows = []
    for scoring, group in analyzed.groupby("scoring", sort=False):
        for profile, condition in profiles:
            eligible = group[condition(group)].copy()
            if eligible.empty:
                winner_rows.append({"scoring": scoring, "profile": profile, "eligible": 0, "config": "NONE"})
                continue
            winner = eligible.sort_values(
                ["ndcg_at_10", "latency_p95_ms", "index_mb"], ascending=[False, True, True]
            ).iloc[0]
            winner_rows.append(
                {
                    "scoring": scoring,
                    "profile": profile,
                    "eligible": len(eligible),
                    **winner.to_dict(),
                }
            )
    winners = pd.DataFrame(winner_rows)
    winners.to_csv(root / "sla_profile_winners.csv", index=False)

    def summary_row(config: str, scoring: str) -> pd.Series:
        return analyzed[(analyzed["config"] == config) & (analyzed["scoring"] == scoring)].iloc[0]

    def comparison_row(candidate: str, baseline: str, scoring: str) -> pd.Series:
        return comparisons_frame[
            (comparisons_frame["candidate"] == candidate)
            & (comparisons_frame["baseline"] == baseline)
            & (comparisons_frame["scoring"] == scoring)
        ].iloc[0]

    caption_sem = summary_row(caption_anchor, "semantic")
    rep_sem = summary_row("representative_frame__B2_vector__flat", "semantic")
    multi_sem = summary_row("multi_frame__B2_vector__flat", "semantic")
    dual_sem = summary_row("dual__B2_vector__flat", "semantic")
    joint_present = "joint_image_caption" in representations
    if joint_present:
        joint_sem = summary_row("joint_image_caption__B2_vector__flat", "semantic")
        joint_strict = summary_row("joint_image_caption__B2_vector__flat", "strict")
        d_joint_sem = comparison_row(
            "joint_image_caption__B2_vector__flat", caption_anchor, "semantic"
        )
        d_joint_strict = comparison_row(
            "joint_image_caption__B2_vector__flat", caption_anchor, "strict"
        )
        joint_storage_text = (
            f", joint image-caption {joint_sem.ndcg_at_10:.4f}"
        )
        joint_inference_text = f"""

단일 image-caption joint vector의 semantic nDCG@10은 {joint_sem.ndcg_at_10:.4f}, strict는
{joint_strict.ndcg_at_10:.4f}였다. Caption 대비 semantic 차이는 질의 bootstrap
{format_ci(d_joint_sem)}, 군집 bootstrap {format_ci(d_joint_sem, 'cluster')}이며, strict 차이는
질의 bootstrap {format_ci(d_joint_strict)}, 군집 bootstrap
{format_ci(d_joint_strict, 'cluster')}이다. 이 비교는 클립당 하나의 2,048차원 벡터라는 동일
저장 예산에서 수행된 early-fusion 대 caption-only 대조다.
"""
    else:
        joint_storage_text = ""
        joint_inference_text = ""
    multi_strict = summary_row("multi_frame__B2_vector__flat", "strict")
    b4_flat_strict = summary_row("multi_frame__B4_prefilter__flat", "strict")
    h64_b4_strict = summary_row("multi_frame__B4_prefilter__hnsw_ef64", "strict")
    h256_b4_strict = summary_row("multi_frame__B4_prefilter__hnsw_ef256", "strict")
    d_multi_sem = comparison_row("multi_frame__B2_vector__flat", caption_anchor, "semantic")
    d_multi_strict = comparison_row("multi_frame__B2_vector__flat", caption_anchor, "strict")
    d_b4_strict = comparison_row("multi_frame__B4_prefilter__flat", "multi_frame__B2_vector__flat", "strict")
    d_h64_strict = comparison_row(
        "multi_frame__B4_prefilter__hnsw_ef64", "multi_frame__B4_prefilter__flat", "strict"
    )

    report = f"""# 저장 × 검색 × 색인 통합 검증 결과

- 실행 완료: {datetime.now().astimezone().isoformat(timespec='seconds')}
- 동결 조건: 3,000 clips, 85 queries, 동일 Qwen3-VL-Embedding-2B 2,048차원 공간
- 구성: {len(representations)}개 저장 표현, 호환 검색 계획, 7개 색인 설정, 총 {analyzed['config'].nunique()}개 구성
- 추론: 질의 bootstrap {args.bootstrap_reps:,}회 + intent×facet {len(clusters)}개 군집 bootstrap {args.bootstrap_reps:,}회

## 1. 동일 인코더 저장 표현 통제

Flat/B2에서 semantic nDCG@10은 caption {caption_sem.ndcg_at_10:.4f}, 대표 프레임 {rep_sem.ndcg_at_10:.4f},
multi-frame {multi_sem.ndcg_at_10:.4f}, dual {dual_sem.ndcg_at_10:.4f}{joint_storage_text}였다. Multi-frame 대비 caption 차이는
질의 bootstrap {format_ci(d_multi_sem)}, 군집 bootstrap {format_ci(d_multi_sem, 'cluster')}이다.

Strict nDCG@10에서도 multi-frame은 {multi_strict.ndcg_at_10:.4f}였고 caption 대비 차이는
질의 bootstrap {format_ci(d_multi_strict)}, 군집 bootstrap {format_ci(d_multi_strict, 'cluster')}이다.
따라서 이전 CLIP/BGE 혼합 비교와 달리, 이 데이터에서는 동일 encoder 조건에서도 다중 프레임 저장의
semantic 이점이 관측됐다. 다만 storage family의 BH 보정 후 cluster q-value는 semantic
{d_multi_sem.q_cluster_bh:.4f}, strict {d_multi_strict.q_cluster_bh:.4f}이므로, 군집 수준 결과를
family-wise 0.05 유의로 과장하지 않는다. 대표 프레임과 caption의 차이는 별도 비교표의 신뢰구간으로 판단한다.
{joint_inference_text}

## 2. 검색 계획 효과

Multi-frame/Flat에서 B4 prefilter의 strict nDCG@10은 {b4_flat_strict.ndcg_at_10:.4f}로,
B2의 {multi_strict.ndcg_at_10:.4f}보다 높았다. 차이는 질의 bootstrap {format_ci(d_b4_strict)},
군집 bootstrap {format_ci(d_b4_strict, 'cluster')}이다. 반면 semantic-only 판단에서는 B2가 더 높아,
hard predicate 준수와 장면 의미 검색을 하나의 지표로 합쳐 단일 승자를 선언해서는 안 된다.

## 3. 색인 효과

Strict 품질 최고점은 `multi_frame + B4 + HNSW efSearch=64`의 {h64_b4_strict.ndcg_at_10:.4f}였다.
Flat 대비 차이는 질의 bootstrap {format_ci(d_h64_strict)}, 군집 bootstrap
{format_ci(d_h64_strict, 'cluster')}이며, p95 검색 지연은 {h64_b4_strict.latency_p95_ms:.3f} ms,
직렬화 색인 크기는 {h64_b4_strict.index_mb:.2f} MB였다. ANN의 작은 점 추정치 우위는 신뢰구간이
0을 포함하면 품질 향상으로 해석하지 않고 Flat 동등 범위의 근사 오차로 취급한다. 또한 이 구성의
exact-task top-10 fidelity는 {h64_b4_strict.task_recall_to_exact_at_10:.4f}에 불과하다. fidelity>=0.95를
요구하면 HNSW ef256은 {h256_b4_strict.task_recall_to_exact_at_10:.4f}, strict nDCG
{h256_b4_strict.ndcg_at_10:.4f}이며, 현재 측정의 최고 strict 품질은 Flat {b4_flat_strict.ndcg_at_10:.4f}였다.

## 4. 결론

단일 전역 최적 조합은 존재하지 않았다. Strict/hard-constraint 목적과 semantic 목적의 승자가 달랐고,
메모리 10 MB 이하에서는 PQ 계열이 선택되지만 exact-ranking fidelity가 크게 낮아졌다. 따라서 본 결과는
`sla_profile_winners.csv`와 `pareto_front.csv`처럼 목적·제약별 선택으로 제시해야 한다.

## 5. 주의

- task-quality 공동 실험의 규모는 동결된 3,000 clips이다.
- 지연 측정은 manifest에 기록된 공유 호스트 부하에서 수행됐다.
- postfilter는 고정 top-200 vector 후보 예산이다.
- 색인 크기는 FAISS 직렬화 크기이며 indexed vector payload를 포함한다.
"""
    (root / "RESULTS_KO.md").write_text(report, encoding="utf-8")

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "bootstrap_reps": args.bootstrap_reps,
        "seed": args.seed,
        "query_count": len(qids),
        "cluster_count": len(clusters),
        "cluster_definition": "visual intent x metadata facet (difficulty field)",
        "multiple_comparison": "Benjamini-Hochberg within family x scoring",
        "pareto_objectives": {"maximize": ["ndcg_at_10"], "minimize": ["latency_p95_ms", "index_mb"]},
        "input_hashes": {
            "per_query_metrics": sha256_file(root / "per_query_metrics.parquet"),
            "rankings": sha256_file(root / "rankings.parquet"),
            "configuration_summary": sha256_file(root / "configuration_summary.csv"),
            "queries": sha256_file(args.canonical_root / "queries.jsonl"),
        },
    }
    (root / "analysis_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(report)
    print(f"[done] comparisons={len(comparisons_frame)} pareto={int(analyzed['pareto_quality_latency_storage'].sum())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
