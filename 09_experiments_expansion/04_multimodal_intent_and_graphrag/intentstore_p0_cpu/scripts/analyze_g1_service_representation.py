#!/usr/bin/env python3
"""CPU-only preregistered screening for IntentStore G1.

This script reads frozen per-query retrieval metrics. It does not invoke a GPU,
load a neural model, or mutate the source experiment.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


REPRESENTATIONS = [
    "caption",
    "representative_frame",
    "joint_image_caption",
    "multi_frame",
    "dual",
]
PRIMARY_SCORING = "strict"
SECONDARY_SCORING = "semantic"
SEARCH_PLAN = "B2_vector"
INDEX = "flat"
METRIC = "ndcg_at_10"
SEED = 20260806
BOOTSTRAP_REPS = 10_000
QUALITY_MARGIN = 0.05
NONINFERIOR_MARGIN = 0.02
COST_RATIO = 0.50


@dataclass
class BootstrapResult:
    n: int
    mean_delta: float
    ci_low: float
    ci_high: float


def parse_args() -> argparse.Namespace:
    default_root = next((p for p in Path(__file__).resolve().parents if (p / "00_env").exists() or (p / "04_scripts").exists()), Path(__file__).resolve().parents[3])
    default_source = default_root / "paper_assets" / "20260717_joint_image_caption_validation"
    parser = argparse.ArgumentParser()
    parser.add_argument("--metrics", type=Path, default=default_source / "per_query_metrics.parquet")
    parser.add_argument("--clusters", type=Path, default=default_source / "query_clusters.csv")
    parser.add_argument("--costs", type=Path, default=default_source / "configuration_summary.csv")
    parser.add_argument("--output", type=Path, default=Path(__file__).resolve().parents[1] / "results")
    return parser.parse_args()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def paired_bootstrap(a: np.ndarray, b: np.ndarray, rng: np.random.Generator) -> BootstrapResult:
    mask = np.isfinite(a) & np.isfinite(b)
    delta = (a[mask] - b[mask]).astype(np.float64)
    n = len(delta)
    if n == 0:
        raise ValueError("No paired observations")
    samples = rng.integers(0, n, size=(BOOTSTRAP_REPS, n))
    boot = delta[samples].mean(axis=1)
    low, high = np.quantile(boot, [0.025, 0.975])
    return BootstrapResult(n=n, mean_delta=float(delta.mean()), ci_low=float(low), ci_high=float(high))


def load_controlled_data(metrics_path: Path, clusters_path: Path) -> pd.DataFrame:
    metrics = pd.read_parquet(metrics_path)
    clusters = pd.read_csv(clusters_path)
    required_metrics = {
        "representation", "search_plan", "index", "query_id", "scoring", METRIC
    }
    required_clusters = {"query_id", "intent", "difficulty", "cluster"}
    if missing := required_metrics.difference(metrics.columns):
        raise ValueError(f"metrics missing columns: {sorted(missing)}")
    if missing := required_clusters.difference(clusters.columns):
        raise ValueError(f"clusters missing columns: {sorted(missing)}")

    controlled = metrics[
        metrics["representation"].isin(REPRESENTATIONS)
        & metrics["search_plan"].eq(SEARCH_PLAN)
        & metrics["index"].eq(INDEX)
        & metrics["scoring"].isin([PRIMARY_SCORING, SECONDARY_SCORING])
    ].copy()
    controlled = controlled.merge(clusters, on="query_id", how="inner", validate="many_to_one")

    expected = len(clusters) * len(REPRESENTATIONS) * 2
    if len(controlled) != expected:
        raise ValueError(f"controlled cell has {len(controlled)} rows; expected {expected}")
    duplicates = controlled.duplicated(["query_id", "representation", "scoring"]).sum()
    if duplicates:
        raise ValueError(f"controlled cell contains {duplicates} duplicates")
    return controlled


def load_costs(costs_path: Path) -> pd.DataFrame:
    costs = pd.read_csv(costs_path)
    controlled = costs[
        costs["representation"].isin(REPRESENTATIONS)
        & costs["search_plan"].eq(SEARCH_PLAN)
        & costs["index"].eq(INDEX)
        & costs["scoring"].eq(PRIMARY_SCORING)
    ][["representation", "vector_payload_mb", "index_mb", "latency_p95_ms"]].copy()
    if controlled["representation"].nunique() != len(REPRESENTATIONS):
        raise ValueError("cost table does not contain exactly one controlled row per representation")
    if controlled.duplicated("representation").any():
        raise ValueError("cost table contains duplicate controlled rows")
    return controlled.set_index("representation")


def service_means(controlled: pd.DataFrame, costs: pd.DataFrame) -> pd.DataFrame:
    means = (
        controlled.groupby(["scoring", "intent", "representation"], as_index=False)
        .agg(queries=("query_id", "nunique"), ndcg_at_10=(METRIC, "mean"))
    )
    means["vector_payload_mb"] = means["representation"].map(costs["vector_payload_mb"])
    means["index_mb"] = means["representation"].map(costs["index_mb"])
    means["latency_p95_ms"] = means["representation"].map(costs["latency_p95_ms"])
    return means.sort_values(["scoring", "intent", "ndcg_at_10"], ascending=[True, True, False])


def analyze_winners(controlled: pd.DataFrame, means: pd.DataFrame, costs: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    rows: list[dict[str, object]] = []
    for scoring in [PRIMARY_SCORING, SECONDARY_SCORING]:
        scoped = controlled[controlled["scoring"].eq(scoring)]
        for intent in sorted(scoped["intent"].unique()):
            ranked = means[(means["scoring"].eq(scoring)) & (means["intent"].eq(intent))]
            ranked = ranked.sort_values(["ndcg_at_10", "representation"], ascending=[False, True])
            winner = str(ranked.iloc[0]["representation"])
            runner = str(ranked.iloc[1]["representation"])
            pivot = scoped[scoped["intent"].eq(intent)].pivot(
                index="query_id", columns="representation", values=METRIC
            )
            result = paired_bootstrap(pivot[winner].to_numpy(), pivot[runner].to_numpy(), rng)
            winner_cost = float(costs.loc[winner, "vector_payload_mb"])
            runner_cost = float(costs.loc[runner, "vector_payload_mb"])
            ratio = winner_cost / runner_cost
            quality_support = result.mean_delta >= QUALITY_MARGIN and result.ci_low > 0.0
            cost_support = ratio <= COST_RATIO and result.ci_low >= -NONINFERIOR_MARGIN
            rows.append({
                "scoring": scoring,
                "intent": intent,
                "queries": result.n,
                "winner": winner,
                "runner_up": runner,
                "winner_mean": float(ranked.iloc[0]["ndcg_at_10"]),
                "runner_up_mean": float(ranked.iloc[1]["ndcg_at_10"]),
                "mean_delta": result.mean_delta,
                "ci_low": result.ci_low,
                "ci_high": result.ci_high,
                "winner_payload_mb": winner_cost,
                "runner_up_payload_mb": runner_cost,
                "payload_ratio": ratio,
                "quality_support": bool(quality_support),
                "cost_support": bool(cost_support),
                "supported_winner": bool(quality_support or cost_support),
            })
    return pd.DataFrame(rows)


def analyze_pairwise(controlled: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED + 1)
    rows: list[dict[str, object]] = []
    for scoring in [PRIMARY_SCORING, SECONDARY_SCORING]:
        scoped = controlled[controlled["scoring"].eq(scoring)]
        for intent in sorted(scoped["intent"].unique()):
            pivot = scoped[scoped["intent"].eq(intent)].pivot(
                index="query_id", columns="representation", values=METRIC
            )
            for i, rep_a in enumerate(REPRESENTATIONS):
                for rep_b in REPRESENTATIONS[i + 1 :]:
                    result = paired_bootstrap(pivot[rep_a].to_numpy(), pivot[rep_b].to_numpy(), rng)
                    rows.append({
                        "scoring": scoring,
                        "intent": intent,
                        "representation_a": rep_a,
                        "representation_b": rep_b,
                        **asdict(result),
                    })
    return pd.DataFrame(rows)


def find_reversals(pairwise: pd.DataFrame) -> list[dict[str, object]]:
    primary = pairwise[pairwise["scoring"].eq(PRIMARY_SCORING)]
    reversals: list[dict[str, object]] = []
    for (rep_a, rep_b), group in primary.groupby(["representation_a", "representation_b"]):
        a_wins = group[(group["mean_delta"] >= QUALITY_MARGIN) & (group["ci_low"] > 0)]
        b_wins = group[(group["mean_delta"] <= -QUALITY_MARGIN) & (group["ci_high"] < 0)]
        for left in a_wins.itertuples(index=False):
            for right in b_wins.itertuples(index=False):
                reversals.append({
                    "representation_a": rep_a,
                    "representation_b": rep_b,
                    "a_wins_intent": left.intent,
                    "a_wins_delta": float(left.mean_delta),
                    "b_wins_intent": right.intent,
                    "b_wins_delta": float(right.mean_delta),
                })
    return reversals


def decide(winners: pd.DataFrame, pairwise: pd.DataFrame) -> dict[str, object]:
    primary = winners[winners["scoring"].eq(PRIMARY_SCORING)].copy()
    reversals = find_reversals(pairwise)
    supported = primary[primary["supported_winner"]]
    unique_all = sorted(primary["winner"].unique().tolist())
    unique_supported = sorted(supported["winner"].unique().tolist())

    if reversals:
        status = "CONTINUE_STRONG"
        reason = "At least one material cross-service ranking reversal was observed."
    elif len(unique_supported) >= 2:
        status = "CONTINUE_SUPPORTED"
        reason = "At least two distinct service winners met the preregistered quality or cost support rule."
    elif len(unique_all) == 1 and supported.empty:
        status = "STOP_SIGNAL"
        reason = "All services selected one representation and no alternative was supported by the cost rule."
    else:
        status = "INCONCLUSIVE"
        reason = "Observed winner variation did not meet the preregistered materiality rules."

    return {
        "status": status,
        "reason": reason,
        "primary_scoring": PRIMARY_SCORING,
        "metric": METRIC,
        "unique_winners": unique_all,
        "unique_supported_winners": unique_supported,
        "supported_service_count": int(len(supported)),
        "strong_reversal_count": len(reversals),
        "strong_reversals": reversals,
        "scope": "CPU screening evidence only; not the final IntentStore G1 decision",
        "thresholds": {
            "quality_margin": QUALITY_MARGIN,
            "noninferior_margin": NONINFERIOR_MARGIN,
            "cost_ratio": COST_RATIO,
            "bootstrap_reps": BOOTSTRAP_REPS,
            "seed": SEED,
        },
    }


def write_report(output_root: Path, means: pd.DataFrame, winners: pd.DataFrame, decision: dict[str, object]) -> None:
    primary_winners = winners[winners["scoring"].eq(PRIMARY_SCORING)]
    lines = [
        "# IntentStore G1 CPU 선행 검증 보고서",
        "",
        f"> 자동 생성: {datetime.now(timezone.utc).isoformat()}  ",
        "> 이 결과는 동결된 기존 검색 산출물의 CPU 재분석이며, 신규 GPU 추론을 수행하지 않았다.  ",
        "> 판정 범위: 위험 감지 전체가 아닌 시각·텍스트 검색 표현의 선행 screening.",
        "",
        "## 자동 판정",
        "",
        f"- 상태: **{decision['status']}**",
        f"- 이유: {decision['reason']}",
        f"- 주 평가: `{PRIMARY_SCORING}` `{METRIC}`",
        f"- 서로 다른 전체 승자: {', '.join(decision['unique_winners']) or '없음'}",
        f"- 사전 기준을 충족한 승자: {', '.join(decision['unique_supported_winners']) or '없음'}",
        f"- strong reversal 수: {decision['strong_reversal_count']}",
        "",
        "## 서비스별 승자",
        "",
        "| 서비스 proxy | n | 승자 | 차순위 | 승자 평균 | 차순위 평균 | 차이 [95% CI] | payload 비율 | 품질 지지 | 비용 지지 |",
        "|---|---:|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in primary_winners.itertuples(index=False):
        lines.append(
            f"| {row.intent} | {row.queries} | {row.winner} | {row.runner_up} | "
            f"{row.winner_mean:.4f} | {row.runner_up_mean:.4f} | "
            f"{row.mean_delta:+.4f} [{row.ci_low:+.4f}, {row.ci_high:+.4f}] | "
            f"{row.payload_ratio:.3f} | {row.quality_support} | {row.cost_support} |"
        )

    lines.extend([
        "",
        "## 표현별 서비스 평균",
        "",
        "아래 표는 검색 계획과 색인을 `B2_vector + flat`으로 고정한 strict nDCG@10이다.",
        "",
        "| 서비스 proxy | " + " | ".join(REPRESENTATIONS) + " |",
        "|---|" + "---:|" * len(REPRESENTATIONS),
    ])
    primary_means = means[means["scoring"].eq(PRIMARY_SCORING)]
    pivot = primary_means.pivot(index="intent", columns="representation", values="ndcg_at_10")
    for intent, row in pivot.sort_index().iterrows():
        lines.append("| " + intent + " | " + " | ".join(f"{row[r]:.4f}" for r in REPRESENTATIONS) + " |")

    lines.extend([
        "",
        "## 해석 제한",
        "",
        "- 이 분석은 교통 CCTV 검색 의도 5종을 서비스 proxy로 사용한다.",
        "- 궤적, 사건 그래프, 원본 TTL, 경보 F1, 위험비용, end-to-end SLA를 포함하지 않는다.",
        "- 따라서 `CONTINUE_*`는 다음 CPU/공개 데이터 실험으로 진행할 근거이지 G1 최종 통과가 아니다.",
        "- `STOP_SIGNAL`은 GPU를 투입하기 전에 연구 문제를 축소해야 한다는 경고다.",
        "",
        "## 재현",
        "",
        "```bash",
        "python scripts/analyze_g1_service_representation.py",
        "```",
        "",
    ])
    (output_root.parent / "G1_CPU_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    for path in [args.metrics, args.clusters, args.costs]:
        if not path.is_file():
            raise FileNotFoundError(path)
    args.output.mkdir(parents=True, exist_ok=True)

    controlled = load_controlled_data(args.metrics, args.clusters)
    costs = load_costs(args.costs)
    means = service_means(controlled, costs)
    winners = analyze_winners(controlled, means, costs)
    pairwise = analyze_pairwise(controlled)
    decision = decide(winners, pairwise)

    means.to_csv(args.output / "service_representation_means.csv", index=False)
    winners.to_csv(args.output / "service_winner_bootstrap.csv", index=False)
    pairwise.to_csv(args.output / "pairwise_bootstrap.csv", index=False)
    (args.output / "decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "command": "python scripts/analyze_g1_service_representation.py",
        "python": sys.version,
        "platform": platform.platform(),
        "pandas": pd.__version__,
        "numpy": np.__version__,
        "inputs": {
            "metrics": {"path": str(args.metrics.resolve()), "sha256": sha256(args.metrics)},
            "clusters": {"path": str(args.clusters.resolve()), "sha256": sha256(args.clusters)},
            "costs": {"path": str(args.costs.resolve()), "sha256": sha256(args.costs)},
        },
        "controlled_rows": int(len(controlled)),
        "queries": int(controlled["query_id"].nunique()),
        "intents": sorted(controlled["intent"].unique().tolist()),
        "representations": REPRESENTATIONS,
        "search_plan": SEARCH_PLAN,
        "index": INDEX,
        "scoring": [PRIMARY_SCORING, SECONDARY_SCORING],
    }
    (args.output / "source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    write_report(args.output, means, winners, decision)
    print(json.dumps(decision, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
