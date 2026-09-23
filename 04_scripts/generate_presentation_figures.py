#!/usr/bin/env python3
"""발표용 초심자 친화 그림 생성 (개념도 + 결과 차트).

모든 수치는 프로젝트 최종 실험 결과(project_md/archive/ 21·23·24, control audit)에서 가져온 상수다.
출력: 2026_KIISE/paper_assets/20260707_presentation_figures/*.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
import numpy as np  # noqa: E402

# ---- 스타일 ----------------------------------------------------------------
for _cand in ("NanumGothic", "NanumBarunGothic", "NanumSquare"):
    try:
        font_manager.findfont(_cand, fallback_to_default=False)
        plt.rcParams["font.family"] = _cand
        break
    except Exception:
        continue
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams["figure.dpi"] = 200
plt.rcParams["savefig.dpi"] = 200

INK = "#213241"
TEXT_BLUE = "#2b5d8a"     # baseline / 텍스트
VISUAL_GREEN = "#2e8b6f"  # 시각 / 멀티모달
META_ORANGE = "#cf8a3e"   # metadata
SELECT_PURPLE = "#6a4c93"  # selection / rerank
WRONG_RED = "#c0433a"
GOOD_GREEN = "#3b8c5a"
NEUTRAL = "#9aa0a8"
BG_BLUE = "#e7f0f8"
BG_GREEN = "#e3f2ec"
BG_ORANGE = "#f7ecdd"  # light orange
BG_PURPLE = "#efe9f5"
BG_GRAY = "#eef1f4"

OUT = Path(__file__).resolve().parents[1] / "paper_assets" / "20260707_presentation_figures"
OUT.mkdir(parents=True, exist_ok=True)


def rbox(ax, cx, cy, w, h, text, fc, ec=None, tc="white", fs=11, bold=True, z=2):
    ec = ec or fc
    ax.add_patch(FancyBboxPatch(
        (cx - w / 2, cy - h / 2), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.14",
        linewidth=1.6, edgecolor=ec, facecolor=fc, zorder=z))
    ax.text(cx, cy, text, ha="center", va="center", color=tc, fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=z + 1, linespacing=1.4)


def arrow(ax, x1, y1, x2, y2, color=INK, lw=2.2, style="-|>"):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle=style, color=color, lw=lw,
                                shrinkA=3, shrinkB=3), zorder=1)


def concept_ax(w=11, h=6.2, xlim=(0, 16), ylim=(0, 9)):
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    return fig, ax


def title(ax, t, sub=None, x=0.5):
    ax.set_title(t, fontsize=17, fontweight="bold", color=INK, pad=14)
    if sub:
        ax.text(x, 1.005, sub, transform=ax.transAxes, ha="center", va="bottom",
                fontsize=11, color=NEUTRAL)


def save(fig, name):
    fig.tight_layout()
    p = OUT / name
    fig.savefig(p, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("wrote", p.name)


def barlabels(ax, bars, fmt="{:.3f}", dy=0.008, fs=10, color=INK):
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + dy,
                fmt.format(b.get_height()), ha="center", va="bottom",
                fontsize=fs, fontweight="bold", color=color)


# ---- 1. 큰 그림: 왜 이 연구인가 -------------------------------------------
def fig01():
    fig, ax = concept_ax()
    title(ax, "이 연구의 위치: AI가 답하기 '전'의 데이터베이스 단계",
          "질문에 답하려면, 먼저 관련 증거를 정확히 찾아 골라야 한다")
    rbox(ax, 2.2, 4.5, 3.0, 1.5, "사용자 질문\n(자연어/이미지)", TEXT_BLUE, fs=12)
    rbox(ax, 8.0, 5.6, 5.4, 2.9,
         "데이터베이스 검색·선택 계층\n(본 연구의 초점)\n\n영상 프레임 · 텍스트 · 메타데이터에서\n관련 증거를 찾고(retrieval) 고른다(selection)",
         VISUAL_GREEN, fs=12)
    rbox(ax, 8.0, 2.4, 5.4, 1.4, "증거: 클립 · 프레임 · 시각 · 텍스트 · 시간", GOOD_GREEN, fs=11)
    rbox(ax, 13.7, 4.5, 3.2, 1.7, "LLM / VLM\n답변 생성\n(다음 단계·선택)", NEUTRAL, fs=11)
    arrow(ax, 3.7, 4.5, 5.3, 5.0)
    arrow(ax, 8.0, 4.15, 8.0, 3.1, color=VISUAL_GREEN)
    arrow(ax, 10.7, 4.9, 12.1, 4.6, color=NEUTRAL, style="-|>")
    ax.text(8.0, 0.7, "본 연구는 새 LLM/VLM을 만들지 않는다. '답을 만드는 모델'이 아니라 '증거를 찾아 고르는 DB 구조'를 다룬다.",
            ha="center", fontsize=11.5, color=INK,
            bbox=dict(boxstyle="round,pad=0.5", fc=BG_BLUE, ec=TEXT_BLUE, lw=1.2))
    save(fig, "fig01_overview.png")


# ---- 2. 멀티모달이란? ------------------------------------------------------
def fig02():
    fig, ax = concept_ax(11, 6.0, xlim=(0, 16), ylim=(0, 9))
    title(ax, "'멀티모달 데이터'란? 한 사건에 세 종류의 정보가 함께 있다",
          "영상 한 장면 = 시각(프레임) + 텍스트(설명) + 구조화 정보(메타데이터)")
    rbox(ax, 3.0, 5.4, 3.6, 2.2, "CCTV / 사고 영상\n한 장면(clip)", INK, fs=12)
    rbox(ax, 10.5, 7.3, 6.0, 1.5, "① 영상 프레임 (이미지)\n대표 장면 keyframe", VISUAL_GREEN, fs=11)
    rbox(ax, 10.5, 5.0, 6.0, 1.5, "② 텍스트 증거\n사고 설명 · 캡션 · 사건 라벨", TEXT_BLUE, fs=11)
    rbox(ax, 10.5, 2.7, 6.0, 1.5, "③ 메타데이터(구조화)\n시간 · 날씨 · 장소 · 도로 · 사건종류", META_ORANGE, fs=11)
    arrow(ax, 4.8, 5.7, 7.5, 7.2, color=VISUAL_GREEN)
    arrow(ax, 4.8, 5.4, 7.5, 5.0, color=TEXT_BLUE)
    arrow(ax, 4.8, 5.1, 7.5, 2.9, color=META_ORANGE)
    ax.text(8.0, 0.7, "세 정보를 함께 저장·색인·검색하는 것이 '멀티모달 데이터베이스 검색'이다.",
            ha="center", fontsize=11.5, color=INK,
            bbox=dict(boxstyle="round,pad=0.5", fc=BG_GREEN, ec=VISUAL_GREEN, lw=1.2))
    save(fig, "fig02_multimodal.png")


# ---- 3. 질의 분해 ----------------------------------------------------------
def fig03():
    fig, ax = concept_ax(11, 5.6, xlim=(0, 16), ylim=(0, 8))
    title(ax, "질문은 두 종류의 조건으로 나뉜다",
          "예: \"비 오는 야간에 보행자 사고가 발생한 장면을 찾아라\"")
    rbox(ax, 8.0, 6.4, 11.5, 1.3,
         "\"비 오는 야간에 보행자 사고가 발생한 장면\"", INK, fs=13)
    rbox(ax, 4.2, 3.6, 6.2, 1.9,
         "의미 조건 (semantic)\n\"보행자 사고\"\n→ 텍스트/시각 임베딩으로 검색", TEXT_BLUE, fs=11.5)
    rbox(ax, 11.8, 3.6, 6.2, 1.9,
         "구조화 조건 (metadata)\n\"날씨=비, 시간=야간\"\n→ 조건 필터로 검색", META_ORANGE, fs=11.5)
    arrow(ax, 6.5, 5.75, 4.5, 4.6, color=TEXT_BLUE)
    arrow(ax, 9.5, 5.75, 11.5, 4.6, color=META_ORANGE)
    ax.text(8.0, 1.2,
            "핵심 질문: 이 두 조건을 '어떤 순서로' 결합해야 관련 증거를 잘 찾을까?",
            ha="center", fontsize=12, color=INK, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", fc=BG_GRAY, ec=NEUTRAL, lw=1.2))
    save(fig, "fig03_query.png")


# ---- 4. prefilter 핵심 개념 ------------------------------------------------
def result_dots(ax, x0, y, n, greens, r=0.16, gap=0.42):
    """greens: 0-based index 집합이 관련/조건충족(초록), 나머지는 회색."""
    for i in range(n):
        c = GOOD_GREEN if i in greens else NEUTRAL
        ax.add_patch(plt.Circle((x0 + i * gap, y), r, color=c, zorder=3))


def fig04():
    fig, ax = concept_ax(12, 7.2, xlim=(0, 16), ylim=(0, 10))
    title(ax, "핵심 개념: 조건(메타데이터)을 '언제' 거를까?",
          "동그라미 = 검색 상위 결과 (● 초록 = 조건 충족·정답, ● 회색 = 조건 위반)")
    rows = [
        (8.4, "vector-only (조건 무시)", WRONG_RED,
         "의미만 보고 순위 → 조건 안 맞는 장면이 위로", {3, 7}),
        (5.4, "postfilter (먼저 검색, 나중 필터)", META_ORANGE,
         "상위 N개에 정답이 없으면 걸러도 복구 불가", {5}),
        (2.4, "prefilter (먼저 조건 필터, 나중 순위)", GOOD_GREEN,
         "조건 맞는 후보만 남기고 순위 → 정답 보존, 안정적", {0, 1, 2, 3}),
    ]
    for y, name, col, note, greens in rows:
        rbox(ax, 2.5, y, 4.2, 1.3, name, col, fs=11)
        arrow(ax, 4.7, y, 6.0, y, color=col)
        result_dots(ax, 6.4, y, 8, greens)
        ax.text(15.4, y, note, ha="right", va="center", fontsize=10.5, color=INK)
    ax.text(8.0, 0.5,
            "결과: 조건을 먼저 거르는 prefilter(B4/M4)가 특히 조건이 강한 질문에서 가장 안정적이다.",
            ha="center", fontsize=11.5, color=INK, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", fc=BG_GREEN, ec=GOOD_GREEN, lw=1.3))
    save(fig, "fig04_prefilter_concept.png")


# ---- 5. 전체 파이프라인 ----------------------------------------------------
def fig05():
    fig, ax = concept_ax(12.5, 6.4, xlim=(0, 18), ylim=(0, 9))
    title(ax, "전체 파이프라인: 영상에서 답변용 증거까지",
          "실제 mp4 → 프레임 추출 → 임베딩·색인 → 검색 전략 → 증거 패킷")
    rbox(ax, 2.0, 7.2, 3.0, 1.2, "원본 영상\nmp4", INK, fs=11)
    rbox(ax, 2.0, 4.8, 3.0, 1.2, "keyframe\n추출", VISUAL_GREEN, fs=11)
    rbox(ax, 6.2, 7.2, 3.4, 1.2, "CLIP 시각 임베딩\n(프레임→벡터)", VISUAL_GREEN, fs=10.5)
    rbox(ax, 6.2, 5.4, 3.4, 1.2, "BGE-M3 / E5\n텍스트 임베딩", TEXT_BLUE, fs=10.5)
    rbox(ax, 6.2, 3.6, 3.4, 1.2, "메타데이터\n필터 색인", META_ORANGE, fs=10.5)
    rbox(ax, 10.8, 5.4, 3.4, 2.9,
         "검색 전략\nB0–B5 (텍스트)\nM2/M4/M5/M6\nIM1 (이미지질의)", SELECT_PURPLE, fs=10.5)
    rbox(ax, 15.2, 6.2, 4.0, 1.5, "증거 선택\n가중 rerank (RW_t4_v1)", SELECT_PURPLE, fs=10.5)
    rbox(ax, 15.2, 3.6, 4.0, 1.9,
         "증거 패킷\nclip·frame·시간\n썸네일·설명", GOOD_GREEN, fs=10.5)
    arrow(ax, 2.0, 6.6, 2.0, 5.4, color=VISUAL_GREEN)
    arrow(ax, 3.5, 4.9, 4.5, 6.9, color=VISUAL_GREEN)
    arrow(ax, 3.5, 7.2, 4.5, 7.2, color=NEUTRAL)
    for yy in (7.2, 5.4, 3.6):
        arrow(ax, 7.9, yy, 9.1, 5.4 + (yy - 5.4) * 0.35, color=NEUTRAL)
    arrow(ax, 12.5, 5.9, 13.2, 6.1, color=SELECT_PURPLE)
    arrow(ax, 15.2, 5.45, 15.2, 4.6, color=GOOD_GREEN)
    ax.text(9.0, 1.1, "LLM/VLM 답변 생성은 이 다음의 선택적 단계이며, 본 실험에서는 사용하지 않았다.",
            ha="center", fontsize=11, color=INK,
            bbox=dict(boxstyle="round,pad=0.45", fc=BG_GRAY, ec=NEUTRAL, lw=1.1))
    save(fig, "fig05_pipeline.png")


# ---- 6. 두 검색 방식 -------------------------------------------------------
def fig06():
    fig, ax = concept_ax(11, 5.6, xlim=(0, 16), ylim=(0, 8))
    title(ax, "두 가지 검색 방식", "글로 찾기(text-to-video)와 사진으로 찾기(image-to-video)")
    rbox(ax, 3.2, 5.6, 4.8, 1.4, "텍스트 질의\n\"야간 보행자 사고\"", TEXT_BLUE, fs=11)
    rbox(ax, 3.2, 2.4, 4.8, 1.4, "이미지 질의\n(현장 스크린샷)", VISUAL_GREEN, fs=11)
    rbox(ax, 9.6, 4.0, 3.0, 3.0, "영상 프레임\n색인", INK, fs=11)
    rbox(ax, 14.0, 5.6, 3.4, 1.4, "M2 / M4\n관련 영상", TEXT_BLUE, fs=10.5)
    rbox(ax, 14.0, 2.4, 3.4, 1.4, "IM1\n같은 원본 영상", VISUAL_GREEN, fs=10.5)
    arrow(ax, 5.6, 5.6, 8.1, 4.6, color=TEXT_BLUE)
    arrow(ax, 5.6, 2.4, 8.1, 3.4, color=VISUAL_GREEN)
    arrow(ax, 11.1, 4.6, 12.3, 5.4, color=TEXT_BLUE)
    arrow(ax, 11.1, 3.4, 12.3, 2.6, color=VISUAL_GREEN)
    ax.text(8.0, 0.7, "두 방식 모두 CLIP이 이미지와 글을 같은 '벡터 공간'에 놓기 때문에 가능하다.",
            ha="center", fontsize=11.5, color=INK,
            bbox=dict(boxstyle="round,pad=0.5", fc=BG_GREEN, ec=VISUAL_GREEN, lw=1.2))
    save(fig, "fig06_query_modes.png")


# ---- 7. top-k vs rank-1 ----------------------------------------------------
def fig07():
    fig, ax = concept_ax(11, 6.0, xlim=(0, 16), ylim=(0, 9))
    title(ax, "왜 '증거 선택'이 중요한가",
          "상위 목록(top-k) 안에 정답이 있어도, 1등이 틀리면 답이 틀린다")
    # 목록
    items = [("1위", NEUTRAL, "관련 없음"), ("2위", NEUTRAL, "관련 없음"),
             ("3위", GOOD_GREEN, "정답 ●"), ("4위", NEUTRAL, ""), ("5위", NEUTRAL, "")]
    for i, (rk, col, tag) in enumerate(items):
        y = 7.0 - i * 1.15
        rbox(ax, 4.2, y, 5.2, 0.95, f"{rk}   {tag}", col, fs=11)
    ax.text(4.2, 8.1, "검색 결과 목록", ha="center", fontsize=12, fontweight="bold", color=INK)
    rbox(ax, 11.4, 6.0, 4.4, 1.4, "LLM이 1위만 보고\n답하면 → 오답", WRONG_RED, fs=11.5)
    rbox(ax, 11.4, 2.7, 4.4, 1.6, "증거 선택(rerank)으로\n정답을 1위로 올리면\n→ 정답", GOOD_GREEN, fs=11)
    arrow(ax, 6.9, 6.85, 9.2, 6.1, color=WRONG_RED)
    arrow(ax, 6.9, 4.55, 9.2, 3.0, color=GOOD_GREEN)
    ax.text(8.0, 0.6,
            "그래서 검색(retrieval) 뿐 아니라 '무엇을 1위로 둘까'(selection)가 답변 품질을 좌우한다.",
            ha="center", fontsize=11.5, color=INK, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", fc=BG_PURPLE, ec=SELECT_PURPLE, lw=1.2))
    save(fig, "fig07_topk_rank1.png")


# ---- 8. baseline 막대 ------------------------------------------------------
def fig08():
    fig, ax = plt.subplots(figsize=(9, 5.2))
    labels = ["B2\nvector-only", "B3\npostfilter", "B4\nprefilter", "B5\nhybrid"]
    vals = [0.4476, 0.9488, 0.9736, 0.9651]
    cols = [NEUTRAL, META_ORANGE, GOOD_GREEN, TEXT_BLUE]
    bars = ax.bar(labels, vals, color=cols, width=0.62, edgecolor="white", linewidth=1.5)
    barlabels(ax, bars)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("nDCG@10 (검색 품질, 1에 가까울수록 좋음)", fontsize=11)
    ax.set_title("텍스트 baseline: 조건을 먼저 거른 prefilter(B4)가 가장 높다\n(VRU 데이터, BGE-M3)",
                 fontsize=14, fontweight="bold", color=INK)
    ax.axhline(0.4476, ls="--", lw=1, color=NEUTRAL, alpha=0.7)
    ax.grid(axis="y", alpha=0.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    save(fig, "fig08_baseline_bar.png")


# ---- 9. 난도별 ------------------------------------------------------------
def fig09():
    fig, ax = plt.subplots(figsize=(9, 5.2))
    groups = ["약함\n(weak)", "보통\n(medium)", "강함\n(strong)"]
    b2 = [0.9118, 0.4852, 0.1851]
    b4 = [0.9118, 0.9795, 0.9935]
    x = np.arange(len(groups))
    w = 0.36
    r1 = ax.bar(x - w / 2, b2, w, label="B2 vector-only", color=NEUTRAL, edgecolor="white")
    r2 = ax.bar(x + w / 2, b4, w, label="B4 prefilter", color=GOOD_GREEN, edgecolor="white")
    barlabels(ax, r1, fs=9)
    barlabels(ax, r2, fs=9)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("nDCG@10", fontsize=11)
    ax.set_xlabel("질문의 조건이 강해질수록 →", fontsize=11)
    ax.set_title("조건이 강한 질문일수록 prefilter의 이점이 커진다\n(VRU, BGE-M3)",
                 fontsize=14, fontweight="bold", color=INK)
    ax.legend(loc="lower left", fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    save(fig, "fig09_difficulty.png")


# ---- 10. 시각 검색 M2 vs M4 -----------------------------------------------
def fig10():
    fig, ax = plt.subplots(figsize=(9, 5.2))
    groups = ["VRU\n(교통사고)", "AI Hub\n지능형 CCTV"]
    m2 = [0.0883, 0.1331]
    m4 = [0.2452, 0.7437]
    x = np.arange(len(groups))
    w = 0.36
    r1 = ax.bar(x - w / 2, m2, w, label="M2 시각 vector-only", color=NEUTRAL, edgecolor="white")
    r2 = ax.bar(x + w / 2, m4, w, label="M4 조건 prefilter + 시각", color=VISUAL_GREEN, edgecolor="white")
    barlabels(ax, r1, fs=9)
    barlabels(ax, r2, fs=9)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylim(0, 0.9)
    ax.set_ylabel("nDCG@10", fontsize=11)
    ax.set_title("시각(이미지) 검색에서도 prefilter가 유리하다\n(텍스트 baseline과 같은 결론이 시각 검색에서 재현)",
                 fontsize=13.5, fontweight="bold", color=INK)
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    save(fig, "fig10_visual_m2_m4.png")


# ---- 11. fusion M5 vs M6 ---------------------------------------------------
def fig11():
    fig, ax = plt.subplots(figsize=(9, 5.2))
    groups = ["VRU\n(교통사고)", "AI Hub\n지능형 CCTV"]
    m5 = [0.3500, 0.4261]
    m6 = [0.6232, 0.8951]
    x = np.arange(len(groups))
    w = 0.36
    r1 = ax.bar(x - w / 2, m5, w, label="M5 텍스트+시각", color="#7fb0d0", edgecolor="white")
    r2 = ax.bar(x + w / 2, m6, w, label="M6 텍스트+시각+메타데이터", color=VISUAL_GREEN, edgecolor="white")
    barlabels(ax, r1, fs=9)
    barlabels(ax, r2, fs=9)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("nDCG@10", fontsize=11)
    ax.set_title("세 정보를 합친 M6가 상용 서비스 구조에 가장 가깝다\n(단, 모든 경우 텍스트 baseline보다 항상 좋지는 않음)",
                 fontsize=13, fontweight="bold", color=INK)
    ax.legend(loc="upper left", fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    save(fig, "fig11_fusion_m5_m6.png")


# ---- 12. image-to-video ----------------------------------------------------
def fig12():
    fig, ax = plt.subplots(figsize=(9, 5.2))
    metrics = ["Recall@1", "Recall@5", "Recall@10"]
    vru = [0.7550, 0.9660, 0.9800]
    aih = [0.8810, 0.9851, 1.0000]
    x = np.arange(len(metrics))
    w = 0.36
    r1 = ax.bar(x - w / 2, vru, w, label="VRU (질의 1,000장)", color=TEXT_BLUE, edgecolor="white")
    r2 = ax.bar(x + w / 2, aih, w, label="AI Hub CCTV (질의 269장)", color=VISUAL_GREEN, edgecolor="white")
    barlabels(ax, r1, fs=9)
    barlabels(ax, r2, fs=9)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("정답 포함 비율 (높을수록 좋음)", fontsize=11)
    ax.set_title("사진으로 원본 영상 찾기(IM1)는 높은 정확도로 동작한다\n(본문 기준 query_frame_seq=2)",
                 fontsize=13.5, fontweight="bold", color=INK)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    save(fig, "fig12_image2video.png")


# ---- 13. IM1 민감도 --------------------------------------------------------
def fig13():
    fig, ax = plt.subplots(figsize=(9, 5.2))
    seq = [0, 1, 2, 3]
    vru = [0.9020, 0.9810, 0.9800, 0.9680]
    aih = [0.9963, 0.9963, 1.0000, 0.8327]
    ax.plot(seq, vru, "-o", color=TEXT_BLUE, lw=2.4, ms=9, label="VRU")
    ax.plot(seq, aih, "-s", color=VISUAL_GREEN, lw=2.4, ms=9, label="AI Hub CCTV")
    for xi, yi in zip(seq, vru):
        ax.text(xi, yi + 0.012, f"{yi:.3f}", ha="center", fontsize=9, color=TEXT_BLUE)
    for xi, yi in zip(seq, aih):
        ax.text(xi, yi - 0.028, f"{yi:.3f}", ha="center", fontsize=9, color=VISUAL_GREEN)
    ax.axvline(2, ls="--", color=NEUTRAL, lw=1)
    ax.text(2.02, 0.86, "본문 기준\n(seq=2)", fontsize=9.5, color=NEUTRAL)
    ax.set_xticks(seq)
    ax.set_xlabel("질의로 사용한 프레임 위치 (query_frame_seq)", fontsize=11)
    ax.set_ylabel("Recall@10", fontsize=11)
    ax.set_ylim(0.78, 1.03)
    ax.set_title("이미지 질의는 '어느 프레임을 쓰는지'에 민감하다 (통제 실험)\nAI Hub는 사건 후반 프레임(seq=3)에서 성능이 떨어짐",
                 fontsize=13, fontweight="bold", color=INK)
    ax.legend(loc="lower left", fontsize=10)
    ax.grid(alpha=0.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    save(fig, "fig13_im1_sensitivity.png")


# ---- 14. rerank ------------------------------------------------------------
def fig14():
    fig, ax = plt.subplots(figsize=(9, 5.2))
    groups = ["VRU", "AI Hub CCTV"]
    before = [0.7131, 0.9248]
    after = [0.8443, 0.9699]
    x = np.arange(len(groups))
    w = 0.36
    r1 = ax.bar(x - w / 2, before, w, label="rerank 전 (동일 가중)", color=NEUTRAL, edgecolor="white")
    r2 = ax.bar(x + w / 2, after, w, label="rerank 후 (RW_t4_v1, 4:1)", color=SELECT_PURPLE, edgecolor="white")
    barlabels(ax, r1, fs=9)
    barlabels(ax, r2, fs=9)
    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("Hit@1 (1위 증거가 정답인 비율)", fontsize=11)
    ax.set_title("LLM 없이 '증거 선택(가중 rerank)'만으로 1위 정확도 개선\n모델을 바꾸지 않고 순위 결합 가중치만 조정",
                 fontsize=13, fontweight="bold", color=INK)
    ax.legend(loc="lower right", fontsize=10)
    ax.grid(axis="y", alpha=0.25)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    save(fig, "fig14_rerank.png")


# ---- 15. pgvector ----------------------------------------------------------
def fig15():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.8))
    labels = ["P2\nvector-only", "P4\nprefilter+vector"]
    ndcg = [0.4473, 0.9736]
    ms = [20.309, 10.239]
    b1 = ax1.bar(labels, ndcg, color=[NEUTRAL, GOOD_GREEN], width=0.6, edgecolor="white")
    barlabels(ax1, b1)
    ax1.set_ylim(0, 1.08)
    ax1.set_ylabel("nDCG@10", fontsize=11)
    ax1.set_title("검색 품질", fontsize=12, fontweight="bold", color=INK)
    b2 = ax2.bar(labels, ms, color=[NEUTRAL, TEXT_BLUE], width=0.6, edgecolor="white")
    barlabels(ax2, b2, fmt="{:.1f} ms", dy=0.3)
    ax2.set_ylim(0, 24)
    ax2.set_ylabel("평균 지연 (ms, 낮을수록 좋음)", fontsize=11)
    ax2.set_title("응답 시간", fontsize=12, fontweight="bold", color=INK)
    for ax in (ax1, ax2):
        ax.grid(axis="y", alpha=0.25)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    fig.suptitle("실제 DB(PostgreSQL+pgvector)에서도 prefilter가 재현된다: 더 정확하고 더 빠름",
                 fontsize=13.5, fontweight="bold", color=INK)
    save(fig, "fig15_pgvector.png")


def main():
    for f in (fig01, fig02, fig03, fig04, fig05, fig06, fig07,
              fig08, fig09, fig10, fig11, fig12, fig13, fig14, fig15):
        f()
    print("\n총", len(list(OUT.glob("*.png"))), "개 그림 생성 →", OUT)


if __name__ == "__main__":
    main()
