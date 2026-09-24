#!/usr/bin/env python3
"""Independent CPU replication of intent-dependent representation utility on MEVA."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


REPS = ["caption", "frame", "dual"]
PLAN = "B2_vector"
PRIMARY = "strict"
SECONDARY = "semantic"
METRIC = "ndcg_at_10"
BOOTSTRAPS = 10_000
PERMUTATIONS = 200_000
SEED = 202608062
QUALITY_MARGIN = 0.05
NONINFERIOR_MARGIN = 0.02
COST_RATIO = 0.50

FAMILY_MAP = {
    "person_loads_vehicle": "vehicle_contact",
    "person_unloads_vehicle": "vehicle_contact",
    "vehicle_picks_up_person": "vehicle_contact",
    "vehicle_drops_off_person": "vehicle_contact",
    "person_opens_trunk": "vehicle_contact",
    "person_closes_trunk": "vehicle_contact",
    "person_enters_vehicle": "vehicle_contact",
    "person_purchases": "object_interaction",
    "person_reads_document": "object_interaction",
    "person_transfers_object": "object_interaction",
    "person_carries_heavy_object": "object_interaction",
    "person_stands_up": "body_social",
    "person_sits_down": "body_social",
    "person_embraces_person": "body_social",
    "hand_interacts_with_person": "body_social",
    "person_rides_bicycle": "body_social",
    "vehicle_makes_u_turn": "vehicle_maneuver",
    "vehicle_reverses": "vehicle_maneuver",
    "person_closes_facility_door": "facility_access",
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def paired_bootstrap(delta: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    n = len(delta)
    samples = rng.integers(0, n, size=(BOOTSTRAPS, n))
    values = delta[samples].mean(axis=1)
    low, high = np.quantile(values, [0.025, 0.975])
    return float(low), float(high)


def randomization_p(delta: np.ndarray, rng: np.random.Generator) -> float:
    observed = abs(float(delta.mean()))
    exceed = 0
    done = 0
    while done < PERMUTATIONS:
        batch = min(10_000, PERMUTATIONS - done)
        signs = rng.integers(0, 2, size=(batch, len(delta)), dtype=np.int8) * 2 - 1
        exceed += int(np.count_nonzero(np.abs((signs * delta).mean(axis=1)) >= observed - 1e-15))
        done += batch
    return (exceed + 1.0) / (PERMUTATIONS + 1.0)


def bh(p: np.ndarray) -> np.ndarray:
    order = np.argsort(p)
    ranked = p[order]
    adjusted = ranked * len(p) / np.arange(1, len(p) + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    result = np.empty(len(p), dtype=float)
    result[order] = np.clip(adjusted, 0, 1)
    return result


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    project = next((p for p in Path(__file__).resolve().parents if (p / "00_env").exists() or (p / "04_scripts").exists()), Path(__file__).resolve().parents[3])
    source = project / "paper_assets" / "20260717_joint_optimization_validation" / "meva_same_encoder_control"
    metrics_path = source / "per_query_metrics.parquet"
    clusters_path = source / "query_clusters.csv"
    costs_path = source / "summary.csv"

    metrics = pd.read_parquet(metrics_path)
    clusters = pd.read_csv(clusters_path)
    observed_defs = set(clusters["relevance_def"].unique())
    unmapped = sorted(observed_defs.difference(FAMILY_MAP))
    if unmapped:
        raise ValueError(f"Unmapped relevance definitions: {unmapped}")
    clusters["service_family"] = clusters["relevance_def"].map(FAMILY_MAP)

    data = metrics[
        metrics["representation"].isin(REPS)
        & metrics["search_plan"].eq(PLAN)
        & metrics["scoring"].isin([PRIMARY, SECONDARY])
    ].merge(clusters, on="query_id", how="inner", validate="many_to_one")
    expected = len(clusters) * len(REPS) * 2
    if len(data) != expected:
        raise ValueError(f"Expected {expected} controlled rows, found {len(data)}")

    costs_raw = pd.read_csv(costs_path)
    costs = costs_raw[
        costs_raw["representation"].isin(REPS)
        & costs_raw["search_plan"].eq(PLAN)
        & costs_raw["scoring"].eq(PRIMARY)
    ][["representation", "index_mb", "latency_p95_ms"]]
    if len(costs) != len(REPS) or costs.duplicated("representation").any():
        raise ValueError("Unexpected controlled cost rows")
    costs = costs.set_index("representation")

    means = (
        data.groupby(["scoring", "service_family", "representation"], as_index=False)
        .agg(queries=("query_id", "nunique"), ndcg_at_10=(METRIC, "mean"))
    )
    means["index_mb"] = means["representation"].map(costs["index_mb"])

    rng = np.random.default_rng(SEED)
    pair_rows: list[dict[str, object]] = []
    for scoring in [PRIMARY, SECONDARY]:
        scoped = data[data["scoring"].eq(scoring)]
        for family in sorted(scoped["service_family"].unique()):
            pivot = scoped[scoped["service_family"].eq(family)].pivot(
                index="query_id", columns="representation", values=METRIC
            )
            for i, rep_a in enumerate(REPS):
                for rep_b in REPS[i + 1 :]:
                    delta = (pivot[rep_a] - pivot[rep_b]).to_numpy(dtype=float)
                    low, high = paired_bootstrap(delta, rng)
                    pair_rows.append({
                        "scoring": scoring,
                        "service_family": family,
                        "representation_a": rep_a,
                        "representation_b": rep_b,
                        "n": len(delta),
                        "mean_delta": float(delta.mean()),
                        "ci_low": low,
                        "ci_high": high,
                        "p_randomization": randomization_p(delta, rng) if scoring == PRIMARY else np.nan,
                    })
    pairs = pd.DataFrame(pair_rows)
    primary_mask = pairs["scoring"].eq(PRIMARY)
    pairs.loc[primary_mask, "q_bh_15"] = bh(pairs.loc[primary_mask, "p_randomization"].to_numpy())

    winner_rows: list[dict[str, object]] = []
    for scoring in [PRIMARY, SECONDARY]:
        for family in sorted(data["service_family"].unique()):
            ranked = means[(means["scoring"].eq(scoring)) & (means["service_family"].eq(family))]
            ranked = ranked.sort_values(["ndcg_at_10", "representation"], ascending=[False, True])
            winner = str(ranked.iloc[0]["representation"])
            runner = str(ranked.iloc[1]["representation"])
            pair = pairs[
                pairs["scoring"].eq(scoring)
                & pairs["service_family"].eq(family)
                & (
                    (pairs["representation_a"].eq(winner) & pairs["representation_b"].eq(runner))
                    | (pairs["representation_a"].eq(runner) & pairs["representation_b"].eq(winner))
                )
            ].iloc[0]
            orientation = 1.0 if pair["representation_a"] == winner else -1.0
            delta = orientation * float(pair["mean_delta"])
            low = float(pair["ci_low"]) if orientation > 0 else -float(pair["ci_high"])
            high = float(pair["ci_high"]) if orientation > 0 else -float(pair["ci_low"])
            q = float(pair["q_bh_15"]) if scoring == PRIMARY else np.nan
            cost_ratio = float(costs.loc[winner, "index_mb"] / costs.loc[runner, "index_mb"])
            quality_support = scoring == PRIMARY and delta >= QUALITY_MARGIN and q < 0.05
            cost_support = cost_ratio <= COST_RATIO and low >= -NONINFERIOR_MARGIN
            winner_rows.append({
                "scoring": scoring,
                "service_family": family,
                "queries": int(ranked.iloc[0]["queries"]),
                "winner": winner,
                "runner_up": runner,
                "winner_mean": float(ranked.iloc[0]["ndcg_at_10"]),
                "runner_up_mean": float(ranked.iloc[1]["ndcg_at_10"]),
                "mean_delta": delta,
                "ci_low": low,
                "ci_high": high,
                "q_bh_15": q,
                "cost_ratio": cost_ratio,
                "quality_support": bool(quality_support),
                "cost_support": bool(cost_support),
                "supported": bool(quality_support or cost_support),
            })
    winners = pd.DataFrame(winner_rows)

    primary_pairs = pairs[pairs["scoring"].eq(PRIMARY)]
    reversals: list[dict[str, object]] = []
    for (rep_a, rep_b), group in primary_pairs.groupby(["representation_a", "representation_b"]):
        pos = group[(group["mean_delta"] >= QUALITY_MARGIN) & (group["q_bh_15"] < 0.05)]
        neg = group[(group["mean_delta"] <= -QUALITY_MARGIN) & (group["q_bh_15"] < 0.05)]
        for a in pos.itertuples(index=False):
            for b in neg.itertuples(index=False):
                reversals.append({
                    "representation_a": rep_a,
                    "representation_b": rep_b,
                    "positive_family": a.service_family,
                    "positive_delta": float(a.mean_delta),
                    "positive_q": float(a.q_bh_15),
                    "negative_family": b.service_family,
                    "negative_delta": float(b.mean_delta),
                    "negative_q": float(b.q_bh_15),
                })

    primary_winners = winners[winners["scoring"].eq(PRIMARY)]
    supported_reps = sorted(primary_winners[primary_winners["supported"]]["winner"].unique())
    all_winners = sorted(primary_winners["winner"].unique())
    if reversals:
        status = "REPLICATED_STRONG"
    elif len(supported_reps) >= 2:
        status = "REPLICATED_SUPPORTED"
    elif len(all_winners) == 1 and not primary_winners["supported"].any():
        status = "STOP_SIGNAL"
    else:
        status = "INCONCLUSIVE"
    decision = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "all_winners": all_winners,
        "supported_winners": supported_reps,
        "reversal_count": len(reversals),
        "reversals": reversals,
        "scope": "independent MEVA CPU replication; no multi-frame, raw TTL, or risk-SLA evaluation",
    }

    results = root / "results"
    means.to_csv(results / "meva_service_representation_means.csv", index=False)
    pairs.to_csv(results / "meva_pairwise_tests.csv", index=False)
    winners.to_csv(results / "meva_service_winners.csv", index=False)
    (results / "meva_decision.json").write_text(json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "inputs": {
            "metrics": {"path": str(metrics_path), "sha256": sha256(metrics_path)},
            "clusters": {"path": str(clusters_path), "sha256": sha256(clusters_path)},
            "costs": {"path": str(costs_path), "sha256": sha256(costs_path)},
        },
        "controlled_rows": len(data),
        "queries": data["query_id"].nunique(),
        "families": sorted(data["service_family"].unique()),
        "family_map": FAMILY_MAP,
        "seed": SEED,
        "bootstraps": BOOTSTRAPS,
        "permutations": PERMUTATIONS,
    }
    (results / "meva_source_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# IntentStore P0-CPU MEVA 독립 복제 보고서",
        "",
        f"> 자동 생성: {datetime.now(timezone.utc).isoformat()}  ",
        "> 동일 encoder의 기존 MEVA 산출물을 CPU로 재분석했다.",
        "",
        f"- 판정: **{status}**",
        f"- 서비스군 승자 종류: {', '.join(all_winners)}",
        f"- 사전 지지 기준을 통과한 승자: {', '.join(supported_reps) or '없음'}",
        f"- FDR 확인 reversal: {len(reversals)}개",
        "",
        "## 서비스군별 결과",
        "",
        "| 서비스군 | n | 승자 | 차순위 | 차이 [95% CI] | q(BH) | index 비율 | 지지 |",
        "|---|---:|---|---|---:|---:|---:|---|",
    ]
    for row in primary_winners.itertuples(index=False):
        lines.append(
            f"| {row.service_family} | {row.queries} | {row.winner} | {row.runner_up} | "
            f"{row.mean_delta:+.4f} [{row.ci_low:+.4f}, {row.ci_high:+.4f}] | "
            f"{row.q_bh_15:.4g} | {row.cost_ratio:.3f} | {row.supported} |"
        )
    lines.extend([
        "",
        "## 해석",
        "",
        "- 이 데이터는 522 데이터와 독립적이지만 대표 프레임 한 장만 있어 multi-frame 가설을 복제하지 못한다.",
        "- 서비스군은 사전에 의미론적으로 묶었으며, 위험비용·실시간 경보가 아니라 검색 proxy다.",
        "- 이 결과는 522 screening과 함께 다음 CPU 단계의 우선순위를 정하는 데만 사용한다.",
        "",
    ])
    (root / "MEVA_REPLICATION_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

