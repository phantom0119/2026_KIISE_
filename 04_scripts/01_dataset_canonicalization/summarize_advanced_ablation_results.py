#!/usr/bin/env python3
"""Summarize advanced ablations added for submission strengthening."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
OUT_DIR = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260707_advanced_ablation"

DATASETS = {
    "VRU": PROJECT_ROOT / "Datasets" / "processed" / "vru_accident" / "20260706",
    "AI Hub CCTV": PROJECT_ROOT / "Datasets" / "processed" / "aihub_intelligent_cctv" / "20260706",
}


def all_rows(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "difficulty" in df.columns:
        return df[df["difficulty"].eq("all")].copy()
    return df.copy()


def metric(row: pd.Series, name: str) -> float:
    return float(row[name])


def collect_visual_encoder_ablation() -> pd.DataFrame:
    rows = []
    for dataset, root in DATASETS.items():
        for encoder, visual_dir, fusion_dir, image_dir, weighted_dir in [
            (
                "CLIP ViT-B/32",
                "visual_clip_full_m2_m4",
                "multimodal_fusion_clip_bgem3_m5_m6",
                "image_to_video_clip_full",
                "weighted_fusion_rerank_sweep_bgem3_clip",
            ),
            (
                "SigLIP base p16-224",
                "visual_siglip_full_m2_m4",
                "multimodal_fusion_siglip_bgem3_m5_m6",
                "image_to_video_siglip_full",
                "weighted_fusion_rerank_sweep_bgem3_siglip",
            ),
        ]:
            visual = all_rows(root / "results" / visual_dir / "metrics_summary.csv")
            fusion = all_rows(root / "results" / fusion_dir / "metrics_summary.csv")
            image = pd.read_csv(root / "results" / image_dir / "metrics_summary.csv").iloc[0]
            weighted = pd.read_csv(root / "results" / weighted_dir / "metrics_summary.csv")
            best = weighted.sort_values(["hit_at_1", "ndcg_at_10"], ascending=False).iloc[0]
            m2 = visual[visual["strategy"].eq("M2_visual_vector_only")].iloc[0]
            m4 = visual[visual["strategy"].eq("M4_metadata_prefilter_visual")].iloc[0]
            m6 = fusion[fusion["strategy"].eq("M6_text_visual_metadata_rrf")].iloc[0]
            rows.append(
                {
                    "dataset": dataset,
                    "encoder": encoder,
                    "m2_r10": metric(m2, "recall_at_10"),
                    "m4_r10": metric(m4, "recall_at_10"),
                    "m4_ndcg10": metric(m4, "ndcg_at_10"),
                    "m6_r10": metric(m6, "recall_at_10"),
                    "m6_ndcg10": metric(m6, "ndcg_at_10"),
                    "im1_r1": metric(image, "recall_at_1"),
                    "im1_r10": metric(image, "recall_at_10"),
                    "best_weight": best["strategy"],
                    "best_hit1": metric(best, "hit_at_1"),
                    "best_ndcg10": metric(best, "ndcg_at_10"),
                }
            )
    return pd.DataFrame(rows)


def collect_frame_budget_ablation() -> pd.DataFrame:
    rows = []
    specs = [
        ("K=1 seq2", "visual_clip_k1_seq2_m2_m4", 1),
        ("K=2 seq1,2", "visual_clip_k2_seq1_2_m2_m4", 2),
        ("K=4 all", "visual_clip_full_m2_m4", 4),
    ]
    for dataset, root in DATASETS.items():
        for label, result_dir, frames_per_clip in specs:
            visual = all_rows(root / "results" / result_dir / "metrics_summary.csv")
            m4 = visual[visual["strategy"].eq("M4_metadata_prefilter_visual")].iloc[0]
            rows.append(
                {
                    "dataset": dataset,
                    "budget": label,
                    "frames_per_clip": frames_per_clip,
                    "task": "text-to-video M4",
                    "recall_at_1": None,
                    "recall_at_5": None,
                    "recall_at_10": metric(m4, "recall_at_10"),
                    "mrr": metric(m4, "mrr"),
                    "ndcg_at_10": metric(m4, "ndcg_at_10"),
                }
            )
        for label, result_dir, frames_per_clip in [
            ("K=2 seq1,2", "image_to_video_clip_k2_seq1_2", 2),
            ("K=4 all", "image_to_video_clip_full", 4),
        ]:
            image = pd.read_csv(root / "results" / result_dir / "metrics_summary.csv").iloc[0]
            rows.append(
                {
                    "dataset": dataset,
                    "budget": label,
                    "frames_per_clip": frames_per_clip,
                    "task": "image-to-video IM1",
                    "recall_at_1": metric(image, "recall_at_1"),
                    "recall_at_5": metric(image, "recall_at_5"),
                    "recall_at_10": metric(image, "recall_at_10"),
                    "mrr": metric(image, "mrr"),
                    "ndcg_at_10": metric(image, "ndcg_at_10"),
                }
            )
    return pd.DataFrame(rows)


def collect_difficulty_ablation() -> pd.DataFrame:
    rows = []
    for dataset, root in DATASETS.items():
        for encoder, result_dir in [
            ("CLIP ViT-B/32", "visual_clip_full_m2_m4"),
            ("SigLIP base p16-224", "visual_siglip_full_m2_m4"),
        ]:
            df = pd.read_csv(root / "results" / result_dir / "metrics_summary.csv")
            for difficulty in ["weak", "medium", "strong", "all"]:
                subset = df[df["difficulty"].eq(difficulty)]
                if subset.empty:
                    continue
                m2 = subset[subset["strategy"].eq("M2_visual_vector_only")].iloc[0]
                m4 = subset[subset["strategy"].eq("M4_metadata_prefilter_visual")].iloc[0]
                rows.append(
                    {
                        "dataset": dataset,
                        "encoder": encoder,
                        "difficulty": difficulty,
                        "queries": int(m4["queries"]),
                        "m2_r10": metric(m2, "recall_at_10"),
                        "m4_r10": metric(m4, "recall_at_10"),
                        "delta_r10": metric(m4, "recall_at_10") - metric(m2, "recall_at_10"),
                        "m2_ndcg10": metric(m2, "ndcg_at_10"),
                        "m4_ndcg10": metric(m4, "ndcg_at_10"),
                        "delta_ndcg10": metric(m4, "ndcg_at_10") - metric(m2, "ndcg_at_10"),
                    }
                )
    return pd.DataFrame(rows)


def fmt(value: object) -> str:
    if value is None or pd.isna(value):
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


def markdown_table(df: pd.DataFrame, columns: list[str], headers: list[str]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in df[columns].to_dict("records"):
        lines.append("| " + " | ".join(fmt(row[col]) for col in columns) + " |")
    return lines


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    visual = collect_visual_encoder_ablation()
    budget = collect_frame_budget_ablation()
    difficulty = collect_difficulty_ablation()

    visual.to_csv(OUT_DIR / "visual_encoder_ablation.csv", index=False)
    budget.to_csv(OUT_DIR / "frame_budget_ablation.csv", index=False)
    difficulty.to_csv(OUT_DIR / "difficulty_ablation.csv", index=False)

    lines = [
        "# Advanced Ablation Summary",
        "",
        f"created_at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## 결론",
        "",
        "추가 보강 실험은 새 데이터셋을 무리하게 늘리는 대신, 현재 true multimodal testbed에서 심사 방어력이 큰 세 축을 점검했다.",
        "",
        "1. visual encoder ablation: CLIP과 SigLIP을 비교해 결론이 단일 visual encoder에 과적합되지 않는지 확인했다.",
        "2. frame budget ablation: clip당 keyframe 수가 text-to-video와 image-to-video 기능에 미치는 영향을 확인했다.",
        "3. query difficulty stratification: metadata filter가 필요한 medium/strong 질의에서 M4의 개선이 어디서 발생하는지 확인했다.",
        "",
        "## Visual Encoder Ablation",
        "",
    ]
    lines.extend(
        markdown_table(
            visual,
            [
                "dataset",
                "encoder",
                "m4_r10",
                "m4_ndcg10",
                "m6_r10",
                "m6_ndcg10",
                "im1_r1",
                "im1_r10",
                "best_weight",
                "best_hit1",
            ],
            ["Dataset", "Encoder", "M4 R@10", "M4 nDCG@10", "M6 R@10", "M6 nDCG@10", "IM1 R@1", "IM1 R@10", "Best RRF", "Best Hit@1"],
        )
    )
    lines.extend(
        [
            "",
            "해석: SigLIP은 text-to-video visual-only 성능은 낮지만, metadata prefilter를 결합한 M4와 weighted RRF의 최적 가중치 결론은 유지된다. 반대로 image-to-video에서는 SigLIP이 CLIP보다 높은 R@1을 보인다. 따라서 본 연구의 핵심 결론은 특정 visual encoder의 절대 성능이 아니라 metadata-aware query planning과 evidence selection 구조의 효과로 해석해야 한다.",
            "",
            "## Frame Budget Ablation",
            "",
        ]
    )
    lines.extend(
        markdown_table(
            budget,
            ["dataset", "task", "budget", "recall_at_1", "recall_at_5", "recall_at_10", "mrr", "ndcg_at_10"],
            ["Dataset", "Task", "Budget", "R@1", "R@5", "R@10", "MRR", "nDCG@10"],
        )
    )
    lines.extend(
        [
            "",
            "해석: text-to-video M4는 대표 프레임 1~2개에서도 성능이 크게 무너지지 않는다. 하지만 image-to-video는 질의 프레임을 제외한 같은 clip의 다른 프레임을 찾아야 하므로 K=4가 K=2보다 안정적이다. 이는 운영 시스템에서 text-to-video 색인과 image-to-video 기능의 frame budget을 별도 설계해야 함을 보여준다.",
            "",
            "## Query Difficulty Stratification",
            "",
        ]
    )
    diff_focus = difficulty[difficulty["difficulty"].isin(["weak", "medium", "strong"])].copy()
    lines.extend(
        markdown_table(
            diff_focus,
            ["dataset", "encoder", "difficulty", "queries", "m2_r10", "m4_r10", "delta_r10", "m2_ndcg10", "m4_ndcg10", "delta_ndcg10"],
            ["Dataset", "Encoder", "Difficulty", "Queries", "M2 R@10", "M4 R@10", "Delta R@10", "M2 nDCG@10", "M4 nDCG@10", "Delta nDCG@10"],
        )
    )
    lines.extend(
        [
            "",
            "해석: weak 질의는 metadata filter가 없으므로 M2와 M4가 동일하다. 개선은 medium/strong 질의에서 발생하며, 특히 AI Hub CCTV strong 질의에서는 CLIP과 SigLIP 모두 M4 R@10이 0.9665까지 상승한다. 이는 metadata prefilter가 단순 평균 성능 향상이 아니라 구조화 조건이 있는 운영 질의에서 효과를 내는 query planning 기법임을 뒷받침한다.",
            "",
            "## 원고 반영 권고",
            "",
            "- 본문에는 기존 결과표를 유지하되, 새 표 2개를 추가한다: visual encoder ablation, frame budget ablation.",
            "- difficulty stratification은 지면이 부족하면 논의 문단 또는 부록성 표로 축약한다.",
            "- 결론은 `CLIP이 최고`가 아니라 `metadata-aware retrieval과 weighted evidence selection이 encoder 교체 후에도 유지된다`로 써야 한다.",
            "- K=1이 text-to-video에서 충분해 보인다는 결과를 과장하지 않는다. image-to-video와 service evidence에는 K=4가 더 안정적이다.",
        ]
    )

    (OUT_DIR / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(OUT_DIR),
        "files": [
            "visual_encoder_ablation.csv",
            "frame_budget_ablation.csv",
            "difficulty_ablation.csv",
            "summary.md",
        ],
    }
    (OUT_DIR / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"output_dir={OUT_DIR}")
    print("files=visual_encoder_ablation.csv,frame_budget_ablation.csv,difficulty_ablation.csv,summary.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
