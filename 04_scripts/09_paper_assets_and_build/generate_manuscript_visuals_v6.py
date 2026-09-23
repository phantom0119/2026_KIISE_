#!/usr/bin/env python3
"""Generate consistent, print-safe figures for the DBR v6 submission draft."""

from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import ticker as mticker
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle


ROOT = Path(__file__).resolve().parents[3]
KIISE = ROOT / "2026_KIISE"
OUT = KIISE / "paper_assets" / "20260717_manuscript_visuals_v6"
OUT.mkdir(parents=True, exist_ok=True)

BLUE = "#2468A2"
LIGHT_BLUE = "#83B6D9"
NAVY = "#173A5E"
ORANGE = "#D97732"
GREEN = "#3A8D6D"
PURPLE = "#7851A9"
GRAY = "#A7ADB4"
DARK = "#202832"
RED = "#B94B4B"
PALE_BLUE = "#EAF2F8"
PALE_GREEN = "#EAF5EF"
PALE_ORANGE = "#FBF1E7"
PALE_GRAY = "#F3F4F6"

mpl.rcParams.update(
    {
        # Matplotlib's packaged font cache exposes the installed Korean TTF
        # reliably under this family name (the Noto CJK TTC is not indexed).
        "font.family": "NanumGothic",
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9,
        "xtick.labelsize": 8,
        "ytick.labelsize": 8,
        "legend.fontsize": 7.5,
        "axes.unicode_minus": False,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
    }
)


def save(fig: plt.Figure, stem: str) -> None:
    fig.savefig(OUT / f"{stem}.png", dpi=320, bbox_inches="tight", pad_inches=0.08)
    fig.savefig(OUT / f"{stem}.pdf", bbox_inches="tight", pad_inches=0.08)
    fig.savefig(OUT / f"{stem}.svg", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)


def panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.08,
        1.04,
        label,
        transform=ax.transAxes,
        fontweight="bold",
        fontsize=10,
        va="bottom",
    )


def clean_axes(ax: plt.Axes, grid_axis: str = "y") -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis=grid_axis, color="#E5E7EB", linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)


def figure_1_pipeline() -> None:
    fig, ax = plt.subplots(figsize=(11.2, 5.35))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    def box(
        x: float,
        y: float,
        w: float,
        h: float,
        title: str,
        subtitle: str,
        face: str,
        edge: str = "#637080",
        title_size: float = 9.0,
        subtitle_size: float = 7.2,
    ) -> None:
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.012,rounding_size=0.018",
            linewidth=1.15,
            facecolor=face,
            edgecolor=edge,
        )
        ax.add_patch(patch)
        ax.text(
            x + w / 2,
            y + h * 0.66,
            title,
            ha="center",
            va="center",
            fontsize=title_size,
            fontweight="bold",
            color=DARK,
        )
        ax.text(
            x + w / 2,
            y + h * 0.31,
            subtitle,
            ha="center",
            va="center",
            fontsize=subtitle_size,
            color="#46515D",
            linespacing=1.15,
        )

    def arrow(x1: float, y1: float, x2: float, y2: float, color: str = "#66717D") -> None:
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle="-|>",
                mutation_scale=11,
                linewidth=1.25,
                color=color,
                shrinkA=2,
                shrinkB=2,
            )
        )

    # Three horizontal bands separate data preparation, online selection, and evaluation.
    bands = [
        (0.625, 0.335, "#F8FAFC", "오프라인 검색용 데이터 준비"),
        (0.315, 0.255, "#F7FBF9", "온라인 증거 선별과 답변"),
        (0.035, 0.205, "#FCF9F6", "비순환 평가와 비용 측정"),
    ]
    for y, h, face, label in bands:
        ax.add_patch(
            FancyBboxPatch(
                (0.012, y),
                0.976,
                h,
                boxstyle="round,pad=0.006,rounding_size=0.012",
                linewidth=0.9,
                facecolor=face,
                edgecolor="#CCD3DB",
            )
        )
        ax.text(
            0.025,
            y + h - 0.028,
            label,
            ha="left",
            va="top",
            fontsize=8.2,
            color=NAVY,
            fontweight="bold",
        )

    # Offline path
    box(0.035, 0.815, 0.115, 0.080, "원본 영상", "도시 감시 클립", PALE_ORANGE, title_size=8.3)
    box(0.035, 0.715, 0.115, 0.080, "센서 기록", "시간, 위치, 신호", PALE_BLUE, title_size=8.3)
    box(0.035, 0.615, 0.115, 0.080, "사람 주석", "사건과 상태", PALE_GREEN, title_size=8.3)
    box(
        0.185,
        0.795,
        0.145,
        0.120,
        "검색용 데이터 생성",
        "클립 설명문\n대표/여러 정지화면",
        "#F7EEE6",
    )
    box(
        0.365,
        0.795,
        0.135,
        0.120,
        "벡터 변환",
        "텍스트, 시각\n결합 입력",
        "#F1EEFA",
    )
    box(
        0.535,
        0.795,
        0.145,
        0.120,
        "검색용 데이터 저장",
        "설명문, 정지화면\n벡터와 식별자",
        "#EEF3F8",
    )
    box(
        0.715,
        0.795,
        0.115,
        0.120,
        "벡터 색인",
        "Flat, HNSW\nIVF 계열",
        "#EDF5F3",
    )
    box(
        0.865,
        0.795,
        0.095,
        0.120,
        "배포 구조",
        "전역, 부분\n지역 색인",
        PALE_GRAY,
        title_size=8.3,
    )
    for x1, x2 in [(0.15, 0.185), (0.33, 0.365), (0.50, 0.535), (0.68, 0.715), (0.83, 0.865)]:
        arrow(x1, 0.855, x2, 0.855)

    # Independent paths used only for conditions and answers.
    box(0.185, 0.675, 0.145, 0.080, "메타데이터 조건", "센서 및 시공간 열", "#E6F0F7", title_size=8.3)
    box(0.365, 0.615, 0.135, 0.080, "관련성 정답", "엄격한/의미론적 정답", "#E6F3EC", title_size=8.3)
    arrow(0.15, 0.755, 0.185, 0.715)
    arrow(0.15, 0.655, 0.365, 0.655)

    # Online path
    box(
        0.035,
        0.365,
        0.115,
        0.145,
        "사용자 질의",
        "자연어 의미 조건\n메타데이터 조건",
        PALE_BLUE,
    )
    box(
        0.365,
        0.365,
        0.135,
        0.145,
        "검색 계획",
        "조건 적용 시점\n검색 신호 결합",
        "#EEF3F8",
    )
    box(
        0.535,
        0.365,
        0.145,
        0.145,
        "후보 검색과 선별",
        "전수/근사 검색\n상위 k개 근거",
        "#EDF5F3",
    )
    box(
        0.715,
        0.365,
        0.115,
        0.145,
        "증거 패킷",
        "클립 식별자\n시점과 정지화면",
        "#F1EEFA",
    )
    box(
        0.865,
        0.365,
        0.095,
        0.145,
        "고정 VLM",
        "질의응답\n결과",
        PALE_ORANGE,
        title_size=8.3,
    )
    arrow(0.15, 0.438, 0.365, 0.438)
    arrow(0.50, 0.438, 0.535, 0.438)
    arrow(0.68, 0.438, 0.715, 0.438)
    arrow(0.83, 0.438, 0.865, 0.438)
    arrow(0.772, 0.795, 0.607, 0.510, color=GREEN)
    arrow(0.922, 0.795, 0.772, 0.510, color=GREEN)
    arrow(0.258, 0.675, 0.432, 0.510, color=BLUE)

    # Evaluation contract
    box(
        0.035,
        0.075,
        0.185,
        0.105,
        "세 원천 소스 분리",
        "센서 기록 / 픽셀 기반 검색 문서 / 사람 주석",
        "#EEF3F8",
        subtitle_size=6.7,
    )
    box(
        0.255,
        0.075,
        0.145,
        0.105,
        "자동 검증",
        "순환 경로 차단과 A6 확인",
        PALE_GRAY,
    )
    box(
        0.435,
        0.075,
        0.165,
        0.105,
        "검색 품질",
        "nDCG@10, MRR\n재현율@10",
        PALE_GREEN,
    )
    box(
        0.635,
        0.075,
        0.155,
        0.105,
        "자원 비용",
        "질의 지연 시간\n저장 공간, 구축 시간",
        PALE_BLUE,
    )
    box(
        0.825,
        0.075,
        0.135,
        0.105,
        "답변 전파",
        "증거 회수, 지각\n답변 정확도",
        PALE_ORANGE,
    )
    for x1, x2 in [(0.22, 0.255), (0.40, 0.435), (0.60, 0.635), (0.79, 0.825)]:
        arrow(x1, 0.127, x2, 0.127)

    save(fig, "fig1_system_architecture_v7")


def figure_2_experiment_map() -> None:
    fig, ax = plt.subplots(figsize=(10.9, 3.7))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    stages = [
        (
            0.025,
            "1단계",
            "평가 타당성",
            "RQ1",
            "세 원천 소스 분리\n순환 요소 통제 주입\n엄격한/의미론적 정답",
            "5-6절",
            PALE_BLUE,
        ),
        (
            0.225,
            "2단계",
            "검색용 데이터 선택",
            "RQ2",
            "설명문 생성 모델\n정지화면 수\n결합 및 이중 색인",
            "7절",
            PALE_ORANGE,
        ),
        (
            0.425,
            "3단계",
            "검색 계획과 신호",
            "RQ3, RQ4",
            "조건 적용 시점\n어휘 및 밀집 검색\n순위 융합",
            "8절",
            PALE_GREEN,
        ),
        (
            0.625,
            "4단계",
            "색인과 배포",
            "RQ5",
            "실측/무작위 조건\nFlat, HNSW, IVF\n전역/부분/지역 색인",
            "9절",
            "#F1EEFA",
        ),
        (
            0.825,
            "5단계",
            "최종 답변 전파",
            "RQ6",
            "증거 회수 변화\nVLM 지각 능력\n질문 및 답변 편향",
            "10절",
            PALE_GRAY,
        ),
    ]

    for x, stage, title, rq, body, section, face in stages:
        ax.add_patch(
            FancyBboxPatch(
                (x, 0.25),
                0.15,
                0.56,
                boxstyle="round,pad=0.012,rounding_size=0.018",
                linewidth=1.2,
                facecolor=face,
                edgecolor="#697583",
            )
        )
        ax.text(x + 0.075, 0.86, stage, ha="center", va="center", fontsize=8, color="#65707B")
        ax.text(
            x + 0.075,
            0.71,
            title,
            ha="center",
            va="center",
            fontsize=9.2,
            fontweight="bold",
            color=DARK,
        )
        ax.text(
            x + 0.075,
            0.60,
            rq,
            ha="center",
            va="center",
            fontsize=8.2,
            color=NAVY,
            fontweight="bold",
        )
        ax.text(
            x + 0.075,
            0.43,
            body,
            ha="center",
            va="center",
            fontsize=7.2,
            color="#45515E",
            linespacing=1.35,
        )
        ax.text(
            x + 0.075,
            0.29,
            section,
            ha="center",
            va="center",
            fontsize=7.2,
            color="#65707B",
        )

    for x in [0.175, 0.375, 0.575, 0.775]:
        ax.add_patch(
            FancyArrowPatch(
                (x, 0.53),
                (x + 0.05, 0.53),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.3,
                color="#66717D",
            )
        )

    ax.add_patch(
        FancyBboxPatch(
            (0.025, 0.055),
            0.95,
            0.11,
            boxstyle="round,pad=0.008,rounding_size=0.012",
            linewidth=0.9,
            facecolor="white",
            edgecolor="#C7CED6",
        )
    )
    ax.text(
        0.50,
        0.11,
        "고정 비교 축: 검색 품질, 질의 지연 시간, 저장 공간, 색인 구축 시간"
        "    |    마지막 검증 축: 최종 VLM 질의응답 정확도",
        ha="center",
        va="center",
        fontsize=8.1,
        color="#3F4A55",
    )
    save(fig, "fig2_experiment_dependency_v7")


def figure_2_circularity() -> None:
    circ_dir = KIISE / "paper_assets/20260717_ablation_agent_crosscheck/qwen_aligned_circularity"
    summary = pd.read_csv(circ_dir / "summary.csv")
    contrasts = pd.read_csv(circ_dir / "contrasts.csv")

    clean_score = float(
        summary[
            (summary.experiment == "C1")
            & (summary.condition == "qwen_clean")
            & (summary.scoring == "semantic")
        ].ndcg_at_10.iloc[0]
    )
    random_score = float(
        summary[
            (summary.experiment == "C1")
            & (summary.condition == "random_same_selectivity_mean")
            & (summary.scoring == "semantic")
        ].ndcg_at_10.iloc[0]
    )
    rows = []
    for experiment, treatment in [
        ("C1", "oracle_qrel_filter"),
        ("C2", "qwen_full_contamination"),
    ]:
        rows.append(
            contrasts[
                (contrasts.experiment == experiment)
                & (contrasts.scoring == "semantic")
                & (contrasts.treatment == treatment)
                & (contrasts.control == "qwen_clean")
            ].iloc[0]
        )
    treatment_scores = [
        float(
            summary[
                (summary.experiment == experiment)
                & (summary.condition == treatment)
                & (summary.scoring == "semantic")
            ].ndcg_at_10.iloc[0]
        )
        for experiment, treatment in [
            ("C1", "oracle_qrel_filter"),
            ("C2", "qwen_full_contamination"),
        ]
    ]

    fig, ax = plt.subplots(figsize=(3.55, 2.20))
    ypos = {
        "무작위 대조 조건": 2,
        "정답 조건 주입": 1,
        "정답 라벨\n재진술 주입": 0,
    }
    ax.axvline(0, color=DARK, linewidth=1.5, zorder=1)
    ax.scatter(
        random_score - clean_score,
        ypos["무작위 대조 조건"],
        color="#6B7280",
        edgecolor="white",
        s=72,
        zorder=4,
    )
    ax.text(
        0.02,
        ypos["무작위 대조 조건"],
        f"{random_score - clean_score:+.3f} ({random_score:.3f})",
        va="center",
        fontsize=8.6,
    )
    for label, row, score, color in [
        ("정답 조건 주입", rows[0], treatment_scores[0], RED),
        ("정답 라벨\n재진술 주입", rows[1], treatment_scores[1], ORANGE),
    ]:
        yi = ypos[label]
        ax.hlines(
            yi,
            float(row.cluster_ci_lo),
            float(row.cluster_ci_hi),
            color=color,
            linewidth=10,
            alpha=0.28,
            zorder=2,
        )
        ax.hlines(
            yi,
            float(row.query_ci_lo),
            float(row.query_ci_hi),
            color=color,
            linewidth=2.8,
            zorder=3,
        )
        ax.scatter(
            float(row.mean_delta),
            yi,
            color=color,
            edgecolor="white",
            s=86,
            zorder=4,
        )
        ax.text(
            float(row.cluster_ci_hi) + 0.02,
            yi,
            f"{float(row.mean_delta):+.3f} ({score:.3f})",
            va="center",
            fontsize=8.6,
        )
    ax.set_yticks(list(ypos.values()), list(ypos.keys()))
    ax.tick_params(axis="both", labelsize=9.0)
    ax.set_xlim(-0.12, 0.98)
    ax.set_xticks([-0.1, 0.0, 0.2, 0.4, 0.6, 0.8])
    ax.set_ylim(-0.55, 2.62)
    ax.set_xlabel("정답 정보 미주입 기준 대비 Δ nDCG@10", fontsize=10.0)
    clean_axes(ax, grid_axis="x")
    ax.text(
        -0.10,
        2.42,
        f"정답 정보 미주입 기준 {clean_score:.3f}",
        fontsize=8.2,
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.8},
        zorder=5,
    )
    ax.legend(
        handles=[
            Line2D(
                [0],
                [0],
                color="#555555",
                linewidth=2.8,
                label="질의 95% 신뢰구간",
            ),
            Line2D(
                [0],
                [0],
                color="#999999",
                linewidth=9,
                alpha=0.4,
                label="군집 95% 신뢰구간",
            ),
        ],
        frameon=False,
        fontsize=8.0,
        loc="upper right",
        bbox_to_anchor=(1.0, 1.0),
        borderaxespad=0.0,
        handlelength=1.8,
        handletextpad=0.7,
    )
    save(fig, "fig2_circularity_integrated_v6")


def figure_4_caption_model_effect() -> None:
    base = KIISE / "paper_assets/20260715_caption_model_ablation"
    metrics = pd.read_csv(base / "retrieval_metrics_all_models.csv")
    deltas = pd.read_csv(base / "paired_model_deltas.csv")
    stats = pd.read_csv(base / "caption_generation_stats.csv")

    model_order = ["qwen25vl_7b", "qwen3vl_8b", "qwen35_9b"]
    model_labels = ["Qwen2.5-VL", "Qwen3-VL", "Qwen3.5"]
    model_colors = [GRAY, BLUE, ORANGE]
    datasets = ["522", "meva", "uca"]
    dataset_labels = ["AI Hub\n교차로", "MEVA", "UCA"]

    fig, axes = plt.subplots(
        1,
        3,
        figsize=(10.8, 3.45),
        gridspec_kw={"width_ratios": [1.2, 1.15, 1.0], "wspace": 0.38},
    )

    ax = axes[0]
    x = np.arange(len(datasets))
    width = 0.23
    for offset, model, label, color in zip(
        [-width, 0.0, width], model_order, model_labels, model_colors
    ):
        vals = []
        for dataset in datasets:
            row = metrics[
                (metrics.dataset == dataset)
                & (metrics.model == model)
                & (metrics.scoring == "semantic")
                & (metrics.strategy == "B2_vector_only")
            ]
            vals.append(float(row.ndcg_at_10.iloc[0]))
        ax.bar(x + offset, vals, width, color=color, label=label, zorder=3)
    ax.set_xticks(x, dataset_labels)
    ax.set_ylim(0, 0.50)
    ax.set_ylabel("의미론적 정답 nDCG@10")
    ax.set_xlabel("데이터셋")
    clean_axes(ax)
    ax.legend(frameon=False, fontsize=6.7, loc="upper left")
    panel_label(ax, "(a)")

    ax = axes[1]
    rows = []
    for dataset in datasets:
        for candidate in ["qwen3vl_8b", "qwen35_9b"]:
            row = deltas[
                (deltas.dataset == dataset)
                & (deltas.candidate == candidate)
                & (deltas.scoring == "semantic")
                & (deltas.strategy == "B2_vector_only")
            ].iloc[0]
            rows.append((dataset, candidate, row))
    y = np.arange(len(rows))[::-1]
    for yi, (dataset, candidate, row) in zip(y, rows):
        color = BLUE if candidate == "qwen3vl_8b" else ORANGE
        ax.plot(
            [row.ci_lo, row.ci_hi],
            [yi, yi],
            color=color,
            linewidth=2.7,
            solid_capstyle="round",
        )
        ax.scatter(row.mean_delta_ndcg10, yi, s=45, color=color, edgecolor="white", zorder=4)
    ax.axvline(0, color="#8D959D", linestyle=":", linewidth=1)
    ax.set_yticks(
        y,
        [
            f"{dataset.upper() if dataset != '522' else dataset} "
            f"{'Qwen3-VL' if candidate == 'qwen3vl_8b' else 'Qwen3.5'}"
            for dataset, candidate, _ in rows
        ],
    )
    ax.set_xlabel("Qwen2.5-VL 대비 nDCG@10 변화")
    clean_axes(ax, grid_axis="x")
    panel_label(ax, "(b)")

    ax = axes[2]
    candidates = stats[stats.model.isin(["qwen3vl_8b", "qwen35_9b"])].copy()
    counts = {
        (row.dataset, row.model): row.token_limit_hit_count
        for _, row in candidates.iterrows()
    }
    corpus_sizes = {"522": 3000, "meva": 985, "uca": 6432}
    for model, label, color, marker in [
        ("qwen3vl_8b", "Qwen3-VL", BLUE, "o"),
        ("qwen35_9b", "Qwen3.5", ORANGE, "s"),
    ]:
        vals = [
            100 * counts[(dataset, model)] / corpus_sizes[dataset]
            for dataset in datasets
        ]
        ax.plot(
            x,
            vals,
            marker=marker,
            linewidth=2,
            color=color,
            label=label,
            zorder=3,
        )
    ax.set_xticks(x, dataset_labels)
    ax.set_ylim(0, 92)
    ax.set_ylabel("110토큰 상한 도달률(%)")
    ax.set_xlabel("데이터셋")
    clean_axes(ax)
    ax.legend(frameon=False, fontsize=6.8, loc="upper left")
    panel_label(ax, "(c)")
    save(fig, "fig4_caption_model_effect_v7")


def figure_3_coupling() -> None:
    data = pd.read_csv(
        ROOT
        / "Datasets/processed/aihub_522_intersection/20260710/results/"
        "trisource_expanded_b0_b5/t3_coupling_curve.csv"
    )
    inference = json.loads(
        (
            KIISE
            / "paper_assets/20260712_codex_crosscheck_fixes/t3_cluster_inference.json"
        ).read_text()
    )
    fig, axes = plt.subplots(
        1, 2, figsize=(7.15, 3.25), gridspec_kw={"width_ratios": [1.55, 1.0], "wspace": 0.36}
    )

    ax = axes[0]
    colors = {
        "parked_vehicles": BLUE,
        "dense_traffic": ORANGE,
        "multiple_buses": GREEN,
        "stopped_vehicles": PURPLE,
        "multiple_bikes": "#8C6D43",
    }
    for rel, group in data.groupby("relevance_def"):
        ax.scatter(
            group.V,
            group.delta,
            s=28,
            alpha=0.62,
            color=colors.get(rel, GRAY),
            edgecolor="white",
            linewidth=0.35,
            label=rel.replace("_", " "),
            zorder=3,
        )
    ax.axhline(0, color="#8D959D", linestyle=":", linewidth=1)
    ax.axvline(0.3, color="#B7BDC4", linestyle="--", linewidth=0.9)
    ax.set_xlim(-0.015, 0.48)
    ax.set_ylim(-0.45, 0.50)
    ax.set_xlabel("메타데이터 조건과 관련성 정답의 결합도(Cramér's V)")
    ax.set_ylabel("검색 전 조건 적용−벡터 단독 검색 nDCG@10 차이")
    clean_axes(ax)
    ax.legend(frameon=False, ncol=2, fontsize=6.4, loc="lower right")
    ax.text(
        0.02,
        0.96,
        f"쌍 평균 ρ={inference['rho_pair_agg']:.3f}, "
        f"95% 신뢰구간 [{inference['rho_cluster_ci'][0]:+.2f}, "
        f"{inference['rho_cluster_ci'][1]:+.2f}]",
        transform=ax.transAxes,
        va="top",
        fontsize=7.2,
        color="#4C5661",
    )
    panel_label(ax, "(a)")

    ax = axes[1]
    bands = [
        ("V<0.05", inference["band V<0.05"]),
        ("V<0.30", inference["band V<0.3"]),
        ("V≥0.30", inference["band V>=0.3"]),
    ]
    y = np.arange(3)[::-1]
    for yi, (name, item), color in zip(y, bands, [BLUE, "#5F8CB2", ORANGE]):
        lo, hi = item["cluster_ci"]
        ax.plot([lo, hi], [yi, yi], color=color, linewidth=3.2, solid_capstyle="round")
        ax.scatter(item["mean"], yi, s=48, color=color, edgecolor="white", zorder=4)
        ax.text(
            item["mean"],
            yi + 0.2,
            f"{item['mean']:+.3f}",
            ha="center",
            fontsize=7.2,
            fontweight="bold",
        )
    ax.axvline(0, color="#8D959D", linestyle=":", linewidth=1)
    ax.set_yticks(y, [f"{name}\n(n={item['n_q']})" for name, item in bands])
    ax.set_xlim(-0.22, 0.39)
    ax.set_ylim(-0.55, 2.55)
    ax.set_xlabel("평균 변화와 쌍 군집 95% 신뢰구간")
    clean_axes(ax, grid_axis="x")
    ax.text(
        0.02,
        0.02,
        "신뢰구간이 0을 포함하면 탐색적",
        transform=ax.transAxes,
        fontsize=6.8,
        color="#59636D",
    )
    panel_label(ax, "(b)")
    save(fig, "fig3_coupling_inference_v6")


def figure_4_uca() -> None:
    base = KIISE / "paper_assets/20260712_uca_external"
    metrics = pd.read_csv(base / "UCA_results.csv")
    contrasts = json.loads((base / "UCA_contrasts.json").read_text())
    fig, axes = plt.subplots(
        1, 2, figsize=(7.15, 3.25), gridspec_kw={"width_ratios": [1.4, 1.0], "wspace": 0.40}
    )

    ax = axes[0]
    order = [
        "B0_metadata_only",
        "B1_bm25_only",
        "B2_vector_only",
        "B3_vector_postfilter",
        "B4_prefilter_vector",
        "B5_hybrid",
    ]
    short = [
        "메타데이터\n단독",
        "BM25\n어휘",
        "벡터\n단독",
        "검색 후\n조건",
        "검색 전\n조건",
        "혼합\n검색",
    ]
    strict = [
        float(metrics[(metrics.strategy == s) & (metrics.scoring == "strict")].mean_ndcg10_primary.iloc[0])
        for s in order
    ]
    semantic = [
        float(metrics[(metrics.strategy == s) & (metrics.scoring == "semantic")].mean_ndcg10_primary.iloc[0])
        for s in order
    ]
    x = np.arange(6)
    width = 0.36
    ax.bar(x - width / 2, strict, width, color=BLUE, label="엄격한 정답", zorder=3)
    ax.bar(x + width / 2, semantic, width, color=LIGHT_BLUE, label="의미론적 정답", zorder=3)
    ax.set_xticks(x, short, fontsize=6.2)
    ax.set_ylim(0, 0.29)
    ax.set_ylabel("UCA nDCG@10")
    ax.set_xlabel("검색 전략")
    clean_axes(ax)
    ax.legend(frameon=False, ncol=2, loc="upper left")
    panel_label(ax, "(a)")

    ax = axes[1]
    forest = [
        (
            "대조 1 엄격한 정답 전체",
            contrasts["c1_strict_pooled_positive"]["detail"]["mean"],
            contrasts["c1_strict_pooled_positive"]["detail"]["pair_ci"],
            True,
        ),
        (
            "대조 2 의미론적 정답 조건",
            contrasts["c2_semantic_container_negative"]["detail"]["mean"],
            contrasts["c2_semantic_container_negative"]["detail"]["pair_ci"],
            True,
        ),
        (
            "대조 4 사건 등급과 길이 구간",
            contrasts["c4_label_gt_container_semantic"]["label"]["mean"],
            contrasts["c4_label_gt_container_semantic"]["label"]["pair_ci"],
            False,
        ),
    ]
    y = np.array([2, 1, 0])
    for yi, (name, mean, ci, holds) in zip(y, forest):
        color = GREEN if holds else RED
        ax.plot(ci, [yi, yi], color=color, linewidth=3.0, solid_capstyle="round")
        ax.scatter(mean, yi, s=52, color=color, edgecolor="white", zorder=4)
        ax.text(
            mean,
            yi + 0.21,
            f"{mean:+.3f}",
            ha="center",
            fontsize=7.1,
            fontweight="bold",
        )
    ax.axvline(0, color="#8D959D", linestyle=":", linewidth=1)
    ax.set_yticks(y, [x[0] for x in forest])
    ax.set_xlim(-0.19, 0.22)
    ax.set_ylim(-0.55, 2.55)
    ax.set_xlabel("검색 전 조건 적용−벡터 단독 검색 차이, 쌍 부트스트랩 95% 신뢰구간")
    clean_axes(ax, grid_axis="x")
    ax.text(
        0.02,
        0.02,
        "대조 3: 의미론적 정답에서 음수 68/129\n판정: 4건 중 3건 방향 일치",
        transform=ax.transAxes,
        fontsize=6.8,
        color="#59636D",
    )
    panel_label(ax, "(b)")
    save(fig, "fig4_uca_external_v6")


def figure_5_real_predicate() -> None:
    pillar = KIISE / "paper_assets/20260710_pillarB"
    methods = [
        "prefilter_flat",
        "prefilter_hnsw_ef64",
        "postfilter_hnsw_K4x",
        "single_stage_ivf_batch_np8",
        "single_stage_ivf_batch_np32",
    ]
    labels = [
        "검색 전 Flat",
        "검색 전 HNSW",
        "검색 후 HNSW",
        "탐색 중 IVF np8",
        "탐색 중 IVF np32",
    ]
    colors = [NAVY, BLUE, ORANGE, GREEN, PURPLE]

    real_means: dict[str, list[float]] = {"A": [], "B": []}
    controls: dict[str, pd.DataFrame] = {}
    for corpus in ["A", "B"]:
        real = pd.read_csv(pillar / f"filtered_ann_real_{corpus}.csv")
        real = real[real.kind.isin(["natural", "composite"])]
        for method in methods:
            real_means[corpus].append(float(real[real.method == method].recall_at_10.mean()))
        controls[corpus] = pd.read_csv(pillar / f"B1_m9_control_{corpus}.csv").set_index("method")

    fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.35), gridspec_kw={"wspace": 0.30})
    ax = axes[0]
    x = np.arange(len(methods))
    width = 0.36
    ax.bar(x - width / 2, real_means["A"], width, color=BLUE, label="Corpus A", zorder=3)
    ax.bar(x + width / 2, real_means["B"], width, color=LIGHT_BLUE, label="Corpus B", zorder=3)
    ax.set_xticks(x, labels, rotation=18, ha="right")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("실측 조건 재현율@10")
    clean_axes(ax)
    ax.legend(frameon=False, ncol=2, loc="upper right")
    panel_label(ax, "(a)")

    ax = axes[1]
    y = np.arange(len(methods))[::-1]
    offsets = {"A": 0.10, "B": -0.10}
    corpus_colors = {"A": BLUE, "B": ORANGE}
    for corpus in ["A", "B"]:
        for yi, method in zip(y, methods):
            row = controls[corpus].loc[method]
            lo, hi = [float(v) for v in re.findall(r"-?\d+\.\d+", row["ci"])]
            yy = yi + offsets[corpus]
            ax.plot([lo, hi], [yy, yy], color=corpus_colors[corpus], linewidth=2.3)
            ax.scatter(row.ctrl_minus_real, yy, s=38, color=corpus_colors[corpus], edgecolor="white", zorder=4)
    ax.axvline(0, color="#8D959D", linestyle=":", linewidth=1)
    ax.set_yticks(y, labels)
    ax.set_xlim(-0.03, 0.73)
    ax.set_xlabel("동일 선택도 무작위 조건과 실측 조건의 재현율 차이")
    clean_axes(ax, grid_axis="x")
    ax.legend(
        handles=[
            Line2D([0], [0], color=BLUE, marker="o", label="Corpus A"),
            Line2D([0], [0], color=ORANGE, marker="o", label="Corpus B"),
        ],
        frameon=False,
        loc="lower right",
    )
    panel_label(ax, "(b)")
    save(fig, "fig5_real_vs_random_v6")


def figure_6_joint_design() -> None:
    joint = KIISE / "paper_assets/20260717_joint_image_caption_validation"
    data = pd.read_csv(joint / "configuration_summary.csv")
    part = data[
        (data.search_plan == "B2_vector")
        & (data["index"] == "flat")
        & (data.scoring == "semantic")
    ].copy()

    rep_order = [
        "caption",
        "representative_frame",
        "joint_image_caption",
        "multi_frame",
        "dual",
    ]
    rep_colors = {
        "caption": BLUE,
        "representative_frame": GREEN,
        "joint_image_caption": RED,
        "multi_frame": ORANGE,
        "dual": PURPLE,
    }
    rep_labels = {
        "caption": "설명문",
        "representative_frame": "정지화면",
        "joint_image_caption": "결합",
        "multi_frame": "여러 정지화면",
        "dual": "이중 색인",
    }
    label_positions = {
        "caption": (0.75, 0.163),
        "representative_frame": (1.48, 0.198),
        "joint_image_caption": (1.55, 0.232),
        "multi_frame": (3.82, 0.360),
        "dual": (5.02, 0.304),
    }

    fig, ax = plt.subplots(figsize=(3.35, 3.05))
    for rep in rep_order:
        row = part[part.representation == rep].iloc[0]
        size = 55 + float(row.vector_payload_mb) * 1.8
        ax.scatter(
            float(row.latency_p50_ms),
            float(row.ndcg_at_10),
            s=size,
            color=rep_colors[rep],
            edgecolor="white",
            linewidth=0.9,
            zorder=3,
        )
        ax.annotate(
            f"{rep_labels[rep]}\n({float(row.vector_payload_mb):.1f}MB)",
            (float(row.latency_p50_ms), float(row.ndcg_at_10)),
            xytext=label_positions[rep],
            textcoords="data",
            fontsize=6.5,
            arrowprops={
                "arrowstyle": "-",
                "color": "#8D959D",
                "linewidth": 0.7,
            },
        )
    ax.set_xlim(0.70, 5.35)
    ax.set_ylim(0.155, 0.375)
    ax.set_xlabel("p50 질의 지연 시간(ms)", fontsize=8)
    ax.set_ylabel("의미론적 정답 nDCG@10", fontsize=8)
    ax.tick_params(labelsize=7)
    clean_axes(ax)
    ax.text(
        0.98,
        0.04,
        "점 크기: float32 벡터 저장량",
        transform=ax.transAxes,
        ha="right",
        fontsize=6.2,
        color="#59636D",
    )
    save(fig, "fig3_storage_tradeoff_v7")


def figure_9_index_resource_tradeoff() -> None:
    data = pd.read_csv(KIISE / "paper_assets/20260710_pillarB/E2_retrieval_pareto.csv")
    kind_colors = {"flat": DARK, "hnsw": BLUE, "ivfflat": GREEN, "ivfpq": ORANGE}
    kind_labels = {
        "flat": "Flat 전수 검색",
        "hnsw": "HNSW",
        "ivfflat": "IVF-Flat",
        "ivfpq": "IVF-PQ",
    }
    corpus_markers = {"A_sinnaedoro_131K": "o", "B_522visual_142K": "s"}
    corpus_labels = {
        "A_sinnaedoro_131K": "시내도로(131K)",
        "B_522visual_142K": "AI Hub 교차로(142K)",
    }

    fig, axes = plt.subplots(1, 3, figsize=(10.9, 3.35), gridspec_kw={"wspace": 0.34})
    for ax, xcol, xlabel, xlog, label in [
        (axes[0], "p95_ms", "p95 질의 지연 시간(ms)", True, "(a)"),
        (axes[1], "index_mb", "색인 크기(MB)", True, "(b)"),
        (axes[2], "build_s", "색인 구축 시간(초)", True, "(c)"),
    ]:
        for (corpus, kind), group in data.groupby(["corpus", "kind"]):
            ax.scatter(
                group[xcol],
                group.recall_at_10,
                s=36,
                marker=corpus_markers.get(corpus, "o"),
                color=kind_colors[kind],
                alpha=0.72,
                edgecolor="white",
                linewidth=0.5,
                zorder=3,
            )
        if xlog:
            ax.set_xscale("log")
            ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda value, _: f"{value:g}"))
        ax.axhline(0.99, color=RED, linestyle="--", linewidth=0.9)
        ax.set_ylim(0.28, 1.025)
        ax.set_xlabel(xlabel + "(로그)")
        ax.set_ylabel("전수 검색 대비 재현율@10")
        clean_axes(ax)
        panel_label(ax, label)

    axes[0].legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=color,
                markeredgecolor="white",
                label=kind_labels[kind],
            )
            for kind, color in kind_colors.items()
        ],
        frameon=False,
        fontsize=6.5,
        loc="lower right",
    )
    axes[1].legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker=marker,
                color="#59636D",
                linestyle="None",
                label=corpus_labels[corpus],
            )
            for corpus, marker in corpus_markers.items()
        ],
        frameon=False,
        fontsize=6.7,
        loc="lower right",
    )
    axes[2].text(
        0.03,
        0.04,
        "빨간 점선: 재현율@10=0.99",
        transform=axes[2].transAxes,
        fontsize=6.8,
        color="#59636D",
    )
    save(fig, "fig9_index_resource_tradeoff_v7")


def figure_10_deployment_policy() -> None:
    base = KIISE / "paper_assets/20260713_db_design"
    sources = [
        ("시내도로", pd.read_csv(base / "hotcold_policy.csv"), BLUE, "o"),
        ("MIRIS", pd.read_csv(base / "hotcold_miris_policy.csv"), ORANGE, "s"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(10.9, 3.35), gridspec_kw={"wspace": 0.34})

    ax = axes[0]
    for label, data, color, marker in sources:
        ordered = data.sort_values("selectivity")
        ax.plot(
            ordered.selectivity,
            ordered.recall_global_relaxed,
            color=color,
            marker=marker,
            linewidth=1.8,
            linestyle="--",
            alpha=0.75,
            label=f"{label} 전역",
        )
        ax.plot(
            ordered.selectivity,
            ordered.recall_partial,
            color=color,
            marker=marker,
            linewidth=2.2,
            label=f"{label} 부분",
        )
    ax.axhline(0.95, color=RED, linestyle=":", linewidth=1)
    ax.set_xlabel("메타데이터 조건 선택도")
    ax.set_ylabel("재현율@10")
    ax.set_ylim(0, 1.04)
    clean_axes(ax)
    ax.legend(frameon=False, fontsize=6.1, ncol=2, loc="lower right")
    panel_label(ax, "(a)")

    ax = axes[1]
    for label, data, color, marker in sources:
        ordered = data.sort_values("selectivity")
        ax.plot(
            ordered.selectivity,
            ordered.L_global_ms,
            color=color,
            marker=marker,
            linewidth=1.8,
            linestyle="--",
            label=f"{label} 전역",
        )
        ax.plot(
            ordered.selectivity,
            ordered.L_partial_ms,
            color=color,
            marker=marker,
            linewidth=2.2,
            label=f"{label} 부분",
        )
    ax.set_yscale("log")
    ax.set_xlabel("메타데이터 조건 선택도")
    ax.set_ylabel("p50 질의 지연 시간(ms, 로그)")
    clean_axes(ax)
    panel_label(ax, "(b)")

    ax = axes[2]
    for label, data, color, marker in sources:
        finite = data[np.isfinite(data.breakeven_queries_Nstar)].copy()
        regular = finite[~finite.quality_forced_local.astype(bool)]
        forced = finite[finite.quality_forced_local.astype(bool)]
        ax.scatter(
            regular.selectivity,
            regular.breakeven_queries_Nstar,
            color=color,
            marker=marker,
            s=45,
            edgecolor="white",
            label=label,
            zorder=3,
        )
        ax.scatter(
            forced.selectivity,
            forced.breakeven_queries_Nstar,
            facecolor="none",
            edgecolor=color,
            marker=marker,
            s=70,
            linewidth=1.5,
            zorder=4,
        )
    ax.set_yscale("log")
    ax.set_xlabel("메타데이터 조건 선택도")
    ax.set_ylabel("부분 색인 구축 시간을 회수하는 질의 수")
    clean_axes(ax)
    ax.text(
        0.03,
        0.04,
        "빈 표식: 전역 색인 재현율이\n0.95 미만인 품질 우선 전환",
        transform=ax.transAxes,
        fontsize=6.7,
        color="#59636D",
    )
    panel_label(ax, "(c)")
    save(fig, "fig10_deployment_policy_v7")


def figure_11_evidence_ladder() -> None:
    conditions = [
        "무증거",
        "무관 증거",
        "벡터만 검색",
        "검색 전 조건 적용",
        "정답 증거",
    ]
    qwen = np.array([0.3083, 0.5383, 0.6650, 0.6800, 0.7467])
    llama = np.array([0.3067, 0.5283, 0.6650, 0.6667, 0.6900])
    x = np.arange(len(conditions))

    fig, axes = plt.subplots(
        1,
        2,
        figsize=(9.4, 3.45),
        gridspec_kw={"width_ratios": [1.55, 1.0], "wspace": 0.35},
    )
    ax = axes[0]
    width = 0.36
    ax.bar(x - width / 2, qwen, width, color=BLUE, label="Qwen2.5-7B", zorder=3)
    ax.bar(x + width / 2, llama, width, color=ORANGE, label="Llama-3-8B", zorder=3)
    ax.axhline(0.25, color=RED, linestyle="--", linewidth=1, label="무작위 정확도")
    ax.set_xticks(x, conditions, rotation=18, ha="right")
    ax.set_ylim(0.20, 0.80)
    ax.set_ylabel("다지선다 VQA 정확도")
    clean_axes(ax)
    ax.legend(frameon=False, fontsize=6.7, ncol=2, loc="upper left")
    panel_label(ax, "(a)")

    ax = axes[1]
    gains_q = qwen - qwen[0]
    gains_l = llama - llama[0]
    y = np.arange(1, len(conditions))[::-1]
    for yi, idx in zip(y, range(1, len(conditions))):
        ax.plot(
            [gains_l[idx], gains_q[idx]],
            [yi, yi],
            color="#B7BEC6",
            linewidth=2.2,
            zorder=1,
        )
        ax.scatter(gains_q[idx], yi, color=BLUE, s=45, edgecolor="white", zorder=3)
        ax.scatter(gains_l[idx], yi, color=ORANGE, s=45, edgecolor="white", zorder=3)
    ax.set_yticks(y, conditions[1:])
    ax.set_xlim(0.18, 0.47)
    ax.set_xlabel("무증거 대비 답변 정확도 변화")
    clean_axes(ax, grid_axis="x")
    panel_label(ax, "(b)")
    save(fig, "fig11_evidence_ladder_v7")


def figure_12_propagation_boundaries() -> None:
    fig, ax = plt.subplots(figsize=(10.6, 3.6))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    boxes = [
        (
            0.035,
            "검증 기준 1\n증거 회수 변화",
            "VRU-Accident 설명문 1,000개\n전수 검색 대비 증거 재현율@3 0.974–1.053\n증거 회수 차이 불충분",
            PALE_BLUE,
            RED,
        ),
        (
            0.285,
            "검증 기준 2\n시각 차이 인식",
            "AI Hub 교차로 정지화면 143,830개\n동일 순간 증거 재현율@3 0.120→0.056\n답변 정확도 차이 -0.020",
            PALE_GREEN,
            RED,
        ),
        (
            0.535,
            "검증 기준 3\n질문과 답변 편향",
            "명확한 질문 정확도 0.72\n이진 질문에서\n'예' 응답 편향",
            PALE_ORANGE,
            ORANGE,
        ),
        (
            0.785,
            "최종 판정\n답변 정확도 전파",
            "세 기준의 동시 충족 필요\n본 색인 근사 실험에서는\n전파를 확인하지 못함",
            "#F1EEFA",
            DARK,
        ),
    ]
    for x, title, body, face, status in boxes:
        ax.add_patch(
            FancyBboxPatch(
                (x, 0.26),
                0.18,
                0.54,
                boxstyle="round,pad=0.012,rounding_size=0.018",
                linewidth=1.2,
                facecolor=face,
                edgecolor="#687481",
            )
        )
        ax.text(
            x + 0.09,
            0.68,
            title,
            ha="center",
            va="center",
            fontsize=9.1,
            fontweight="bold",
            color=DARK,
            linespacing=1.25,
        )
        ax.text(
            x + 0.09,
            0.45,
            body,
            ha="center",
            va="center",
            fontsize=7.3,
            color="#46515D",
            linespacing=1.35,
        )
        ax.add_patch(
            Rectangle(
                (x + 0.02, 0.285),
                0.14,
                0.027,
                facecolor=status,
                edgecolor="none",
                alpha=0.85,
            )
        )
    for x in [0.215, 0.465, 0.715]:
        ax.add_patch(
            FancyArrowPatch(
                (x, 0.53),
                (x + 0.07, 0.53),
                arrowstyle="-|>",
                mutation_scale=12,
                linewidth=1.3,
                color="#66717D",
            )
        )
    ax.text(
        0.5,
        0.10,
        "색인의 재현율 차이만으로 최종 답변 개선을 판단하지 않고,"
        " 증거 회수, VLM 지각, 질문 및 답변 분포를 차례로 검증",
        ha="center",
        va="center",
        fontsize=8.2,
        color="#46515D",
    )
    save(fig, "fig12_propagation_boundaries_v7")


def main() -> None:
    figure_1_pipeline()
    figure_2_experiment_map()
    figure_2_circularity()
    figure_4_caption_model_effect()
    figure_3_coupling()
    figure_4_uca()
    figure_5_real_predicate()
    figure_6_joint_design()
    figure_9_index_resource_tradeoff()
    figure_10_deployment_policy()
    figure_11_evidence_ladder()
    figure_12_propagation_boundaries()
    for path in sorted(OUT.glob("fig*.png")):
        print(path)


if __name__ == "__main__":
    main()
