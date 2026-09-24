#!/usr/bin/env python3
"""Post-result multiplicity audit for the IntentStore CPU screening."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


REPS = ["caption", "representative_frame", "joint_image_caption", "multi_frame", "dual"]
PLAN = "B2_vector"
INDEX = "flat"
SCORING = "strict"
METRIC = "ndcg_at_10"
MARGIN = 0.05
PERMUTATIONS = 200_000
SEED = 202608061


def sign_flip_pvalue(delta: np.ndarray, rng: np.random.Generator) -> float:
    delta = delta[np.isfinite(delta)].astype(np.float64)
    observed = abs(float(delta.mean()))
    exceed = 0
    completed = 0
    batch_size = 10_000
    while completed < PERMUTATIONS:
        batch = min(batch_size, PERMUTATIONS - completed)
        signs = rng.integers(0, 2, size=(batch, len(delta)), dtype=np.int8) * 2 - 1
        stats = np.abs((signs * delta).mean(axis=1))
        exceed += int(np.count_nonzero(stats >= observed - 1e-15))
        completed += batch
    return (exceed + 1.0) / (PERMUTATIONS + 1.0)


def bh_adjust(p_values: np.ndarray) -> np.ndarray:
    n = len(p_values)
    order = np.argsort(p_values)
    ranked = p_values[order]
    adjusted = ranked * n / np.arange(1, n + 1)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0.0, 1.0)
    result = np.empty(n, dtype=np.float64)
    result[order] = adjusted
    return result


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    project = next((p for p in Path(__file__).resolve().parents if (p / "00_env").exists() or (p / "04_scripts").exists()), Path(__file__).resolve().parents[3])
    source = project / "paper_assets" / "20260717_joint_image_caption_validation"
    metrics = pd.read_parquet(source / "per_query_metrics.parquet")
    clusters = pd.read_csv(source / "query_clusters.csv")
    data = metrics[
        metrics["representation"].isin(REPS)
        & metrics["search_plan"].eq(PLAN)
        & metrics["index"].eq(INDEX)
        & metrics["scoring"].eq(SCORING)
    ].merge(clusters[["query_id", "intent"]], on="query_id", how="inner", validate="many_to_one")

    rng = np.random.default_rng(SEED)
    rows: list[dict[str, object]] = []
    for intent in sorted(data["intent"].unique()):
        pivot = data[data["intent"].eq(intent)].pivot(
            index="query_id", columns="representation", values=METRIC
        )
        for i, rep_a in enumerate(REPS):
            for rep_b in REPS[i + 1 :]:
                delta = pivot[rep_a].to_numpy() - pivot[rep_b].to_numpy()
                rows.append({
                    "intent": intent,
                    "representation_a": rep_a,
                    "representation_b": rep_b,
                    "n": int(len(delta)),
                    "mean_delta": float(np.mean(delta)),
                    "p_randomization": sign_flip_pvalue(delta, rng),
                })
    tests = pd.DataFrame(rows)
    tests["q_bh_50"] = bh_adjust(tests["p_randomization"].to_numpy())
    tests["material_positive"] = (tests["mean_delta"] >= MARGIN) & (tests["q_bh_50"] < 0.05)
    tests["material_negative"] = (tests["mean_delta"] <= -MARGIN) & (tests["q_bh_50"] < 0.05)

    reversals: list[dict[str, object]] = []
    for (rep_a, rep_b), group in tests.groupby(["representation_a", "representation_b"]):
        positive = group[group["material_positive"]]
        negative = group[group["material_negative"]]
        for pos in positive.itertuples(index=False):
            for neg in negative.itertuples(index=False):
                reversals.append({
                    "representation_a": rep_a,
                    "representation_b": rep_b,
                    "positive_intent": pos.intent,
                    "positive_delta": float(pos.mean_delta),
                    "positive_q": float(pos.q_bh_50),
                    "negative_intent": neg.intent,
                    "negative_delta": float(neg.mean_delta),
                    "negative_q": float(neg.q_bh_50),
                })

    status = "FDR_CONFIRMED_STRONG" if reversals else "FDR_INCONCLUSIVE"
    decision = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "reason": (
            "At least one material cross-service reversal survived BH-FDR over 50 tests."
            if reversals
            else "No material cross-service reversal survived BH-FDR over 50 tests."
        ),
        "tests": int(len(tests)),
        "permutations_per_test": PERMUTATIONS,
        "seed": SEED,
        "reversal_count": len(reversals),
        "reversals": reversals,
        "scope": "post-result multiplicity audit; not preregistered primary analysis",
    }

    results = root / "results"
    tests.to_csv(results / "multiplicity_audit.csv", index=False)
    (results / "multiplicity_decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    significant = tests[tests["q_bh_50"] < 0.05].sort_values("q_bh_50")
    lines = [
        "# IntentStore G1-CPU 다중성 감사",
        "",
        "> 최초 결과 확인 뒤 추가한 사후 유효성 보정이다. 사전 등록 분석으로 해석하지 않는다.",
        "",
        f"- 판정: **{status}**",
        f"- paired sign-flip randomization: 테스트당 {PERMUTATIONS:,}회",
        f"- BH-FDR family: {len(tests)}개 비교",
        f"- q<0.05 비교: {len(significant)}개",
        f"- FDR 확인 reversal: {len(reversals)}개",
        "",
        "## q<0.05인 서비스-표현쌍",
        "",
        "| 서비스 proxy | 표현 A | 표현 B | A−B | p | q(BH) |",
        "|---|---|---|---:|---:|---:|",
    ]
    for row in significant.itertuples(index=False):
        lines.append(
            f"| {row.intent} | {row.representation_a} | {row.representation_b} | "
            f"{row.mean_delta:+.4f} | {row.p_randomization:.6g} | {row.q_bh_50:.6g} |"
        )
    lines.extend(["", "## 확인된 reversal", ""])
    if reversals:
        lines.extend([
            "| 표현쌍 | A 우세 서비스 | A−B / q | B 우세 서비스 | A−B / q |",
            "|---|---|---:|---|---:|",
        ])
        for item in reversals:
            lines.append(
                f"| {item['representation_a']} vs {item['representation_b']} | "
                f"{item['positive_intent']} | {item['positive_delta']:+.4f} / {item['positive_q']:.4g} | "
                f"{item['negative_intent']} | {item['negative_delta']:+.4f} / {item['negative_q']:.4g} |"
            )
    else:
        lines.append("없음. 최초 `CONTINUE_STRONG`은 보정 후 확정되지 않았다.")
    lines.extend([
        "",
        "## 해석",
        "",
        "이 감사는 다중 비교 위양성 위험을 낮춘다. 여전히 단일 데이터셋의 검색 proxy이며 IntentStore G1 최종 판정은 아니다.",
        "",
    ])
    (root / "MULTIPLICITY_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

