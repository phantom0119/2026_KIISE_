#!/usr/bin/env python3
"""Post-result validity audit excluding uninformative all-zero cost ties."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


MIN_QUERIES = 10
MIN_WINNER_MEAN = 0.05


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    results = root / "results"
    winners = pd.read_csv(results / "meva_service_winners.csv")
    primary = winners[winners["scoring"].eq("strict")].copy()
    primary["informative"] = (
        (primary["queries"] >= MIN_QUERIES)
        & (primary["winner_mean"] >= MIN_WINNER_MEAN)
    )
    primary["adjusted_supported"] = primary["quality_support"] | (
        primary["cost_support"] & primary["informative"]
    )
    supported = primary[primary["adjusted_supported"]]
    supported_reps = sorted(supported["winner"].unique())
    status = "REPLICATED_SUPPORTED" if len(supported_reps) >= 2 else "REPLICATION_INCONCLUSIVE"
    decision = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "status": status,
        "reason": (
            "At least two distinct supported winners remain after the informative-cell audit."
            if len(supported_reps) >= 2
            else "Fewer than two distinct supported winners remain after excluding uninformative cells."
        ),
        "min_queries": MIN_QUERIES,
        "min_winner_mean": MIN_WINNER_MEAN,
        "supported_winners": supported_reps,
        "supported_families": supported["service_family"].tolist(),
        "scope": "post-result informative-cell audit; not preregistered primary analysis",
    }
    primary.to_csv(results / "meva_informative_audit.csv", index=False)
    (results / "meva_informative_decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# MEVA 비용 대체 정보성 감사",
        "",
        "> 최초 결과 확인 뒤 추가한 사후 유효성 보정이다.",
        "",
        f"- 판정: **{status}**",
        f"- 정보성 기준: n≥{MIN_QUERIES}, 승자 strict nDCG@10≥{MIN_WINNER_MEAN:.2f}",
        f"- 보정 후 지지된 표현: {', '.join(supported_reps) or '없음'}",
        "",
        "| 서비스군 | n | 승자 평균 | 원 비용 지지 | 정보성 | 보정 지지 |",
        "|---|---:|---:|---|---|---|",
    ]
    for row in primary.itertuples(index=False):
        lines.append(
            f"| {row.service_family} | {row.queries} | {row.winner_mean:.4f} | "
            f"{row.cost_support} | {row.informative} | {row.adjusted_supported} |"
        )
    lines.extend([
        "",
        "`facility_access`의 전 표현 0점 동률은 저장비가 작더라도 서비스 효용을 입증하지 못하므로 최종 지지에서 제외한다.",
        "",
    ])
    (root / "MEVA_INFORMATIVE_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

