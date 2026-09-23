#!/usr/bin/env python3
"""Aggregate filled caption-quality ratings -> trust metrics.

Input: the CSV exported from review.html (caption_ratings_filled.csv) — columns
item_id, Q1_faithful, Q2_captures, Q3_hallucination, note. Joined to the pilot
manifest/template for stratum.

Outputs caption-quality numbers that directly answer "can we trust the captions":
  - 충실도 분포 (정확/부분/틀림 %)
  - 핵심요소 포착률 (전체 + 층화별; 특히 parked 맹점)
  - 환각률
  - 신뢰도 한 줄 판정

Run: Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/04_scripts/aggregate_caption_quality.py \
        --ratings <내보낸 caption_ratings_filled.csv>
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710" / "caption_quality_pilot"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratings", type=Path, default=OUT / "caption_ratings_filled.csv")
    args = ap.parse_args()
    if not args.ratings.exists():
        raise SystemExit(f"채점표 없음: {args.ratings} (review.html 에서 CSV 내보내기 먼저)")
    r = pd.read_csv(args.ratings)
    tmpl = pd.read_csv(OUT / "rating_template.csv")[["item_id", "stratum", "clip_id"]]
    df = r.merge(tmpl, on="item_id", how="left")
    df = df[df.Q1_faithful.notna() & (df.Q1_faithful != "")]
    n = len(df)
    if n == 0:
        raise SystemExit("채점된 항목이 없습니다.")

    faith = df.Q1_faithful.value_counts(normalize=True).to_dict()
    hallu = (df.Q3_hallucination == "예").mean()
    # 핵심요소 포착률: 해당있음(예/아니오)만 대상
    cap = df[df.Q2_captures.isin(["예", "아니오"])]
    capture_rate = (cap.Q2_captures == "예").mean() if len(cap) else float("nan")
    by_stratum = {}
    for s, g in cap.groupby("stratum"):
        by_stratum[s] = {"n": int(len(g)), "capture_rate": round(float((g.Q2_captures == "예").mean()), 3)}

    faithful_ok = round(float(faith.get("정확", 0) + faith.get("부분", 0)), 3)  # 정확+부분 = 사용가능
    summary = {
        "n_rated": n,
        "faithfulness_dist": {k: round(float(v), 3) for k, v in faith.items()},
        "faithful_usable(정확+부분)": faithful_ok,
        "accurate(정확)": round(float(faith.get("정확", 0)), 3),
        "hallucination_rate": round(float(hallu), 3),
        "target_capture_rate_overall": round(float(capture_rate), 3),
        "target_capture_by_stratum": by_stratum,
        "parked_blindspot_capture": by_stratum.get("parked", {}).get("capture_rate"),
    }
    (OUT / "caption_quality_result.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))

    print(f"=== 캡션 품질 사람검증 결과 (n={n}) ===")
    print(f"  충실도: 정확 {faith.get('정확',0):.0%} / 부분 {faith.get('부분',0):.0%} / 틀림 {faith.get('틀림',0):.0%}")
    print(f"  사용가능(정확+부분): {faithful_ok:.0%}")
    print(f"  환각률: {hallu:.0%}")
    print(f"  핵심요소 포착률(전체): {capture_rate:.0%}")
    print(f"  층화별 포착률: " + ", ".join(f"{s} {v['capture_rate']:.0%}(n{v['n']})" for s, v in by_stratum.items()))
    ps = summary["parked_blindspot_capture"]
    if ps is not None:
        print(f"  ⚑ parked(맹점) 포착률: {ps:.0%}  ← 낮으면 '캡션 주차 맹점'을 사람검증이 확증")
    verdict = ("높음" if faithful_ok >= 0.8 and hallu <= 0.1 else "중간" if faithful_ok >= 0.6 else "낮음")
    print(f"  판정: 전반 신뢰도 {verdict} (충실 {faithful_ok:.0%}·환각 {hallu:.0%}); "
          f"단 맹점(parked 등)은 층화별 포착률로 별도 보고")
    print(f"[saved] {OUT}/caption_quality_result.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
