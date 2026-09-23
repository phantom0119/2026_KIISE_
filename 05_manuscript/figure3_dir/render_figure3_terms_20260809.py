#!/usr/bin/env python3
"""그림 3 재생성 (2026-08-09, 심사 대응 개정판 용어 반영).

원본 Figure3.png(07-20, 렌더 스크립트 미보존)과 동일한 데이터·팔레트로 재작도하되,
범례 라벨을 개정 원고 용어로 교체하고 파레토 판정 기준을 그림 안에 명시한다:
  클립 설명문 → 영상 설명문 / 대표 정지화면 → 대표 이미지 / 여러 정지화면 → 다중 이미지
팔레트 5색은 원본 PNG 범례 스와치에서 실측한 값이다.

실행: python3 render_figure3_terms_20260809.py [출력경로]
기본 출력: ./Figure3_terms_20260809.png (검토 후 manuscript/Figure3.png로 반영)
"""
import sys
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "Figure3_terms_20260809.png"

mpl.rcParams.update({
    "font.family": "NanumGothic",
    "axes.unicode_minus": False,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

REP_COLOR = {  # 원본 PNG 범례 스와치 실측색
    "caption": "#0282C9",
    "representative_frame": "#FDC307",
    "joint_image_caption": "#02B18F",
    "multi_frame": "#E082BF",
    "dual": "#EA5603",
}
REP_LABEL = {  # 개정 원고 용어 (2026-08-09)
    "caption": "영상 설명문",
    "representative_frame": "대표 이미지",
    "joint_image_caption": "이미지·설명문 결합",
    "multi_frame": "다중 이미지",
    "dual": "이중 색인",
}
PLAN_MARKER = {
    "B2_vector": "o",
    "B3_postfilter": "s",
    "B4_prefilter": "^",
    "B5_lexical_vector_hybrid": "D",
}
PLAN_LABEL = {
    "B2_vector": "벡터 단독 검색",
    "B3_postfilter": "검색 후 조건 적용",
    "B4_prefilter": "검색 전 조건 적용",
    "B5_lexical_vector_hybrid": "혼합 검색",
}
PANELS = [("semantic", "(a) 의미론적 정답", "의미론적 정답 nDCG@10"),
          ("strict", "(b) 엄격한 정답", "엄격한 정답 nDCG@10")]

an = pd.read_csv(HERE / "data" / "20260717_joint_image_caption_validation" /
                 "analyzed_configuration_summary.csv")
assert an.config.nunique() == 112 and len(an) == 224
assert int(an.pareto_quality_latency_storage.sum()) == 28

fig, axes = plt.subplots(1, 2, figsize=(8.84, 5.05), dpi=200)
fig.subplots_adjust(left=0.075, right=0.985, top=0.92, bottom=0.34, wspace=0.22)
# 2026-08-17 감사 반영: 캡션과 중복되는 그림 내부 제목(suptitle)은 넣지 않는다.

for ax, (scoring, title, ylabel) in zip(axes, PANELS):
    g = an[an.scoring == scoring]
    for pareto_pass in (False, True):  # 파레토 점을 위에 겹쳐 그림
        part_p = g[g.pareto_quality_latency_storage == pareto_pass]
        for (rep, plan), part in part_p.groupby(["representation", "search_plan"]):
            ax.scatter(part.latency_p95_ms, part.ndcg_at_10,
                       c=REP_COLOR[rep], marker=PLAN_MARKER[plan], s=52,
                       edgecolor="black" if pareto_pass else "white",
                       linewidth=1.5 if pareto_pass else 0.6,
                       zorder=3 if pareto_pass else 2)
    ax.set_xscale("log")
    ax.set_xlim(0.12, 7.0)
    ax.set_ylim(0.04, 0.41)
    ax.set_yticks([0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40])
    ax.set_yticklabels([f"{v:.2f}" for v in
                        (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40)], fontsize=11)
    ax.set_xticks([0.2, 0.5, 1, 2, 5])
    ax.set_xticklabels(["0.2", "0.5", "1", "2", "5"], fontsize=11)
    ax.minorticks_off()
    ax.set_title(title, fontsize=12.5, fontweight="bold", pad=9)
    ax.set_ylabel(ylabel, fontsize=11.5)
    ax.grid(axis="y", linestyle="--", linewidth=0.6, color="#CCCCCC", zorder=0)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_linewidth(1.4)

fig.supxlabel("p95 검색 지연 (ms, 로그 척도)", fontsize=12.5, y=0.25)

# 파레토 판정 지표를 그림만 읽어도 확인할 수 있게 중앙에 명시한다.
fig.text(0.5, 0.19, "파레토 기준: nDCG@10↑ · p95 검색 지연↓ · 색인 크기↓",
         fontsize=9.5, ha="center", va="center")

# ── 범례 2줄 (원본과 동일한 배치: 검색용 데이터 / 검색 계획) ──
# 텍스트 폭을 렌더러로 실측하여 항목 간 겹침 없이 배치한다.
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
fig_w = fig.get_window_extent(renderer).width

def legend_row(y, head, items, gap=0.024):
    t = fig.text(0.030, y, head, fontsize=11.5, va="center")
    x = 0.030 + t.get_window_extent(renderer).width / fig_w + gap
    for marker, face, edge, label in items:
        fig.add_artist(Line2D([x], [y], marker=marker, color="none",
                              markerfacecolor=face, markeredgecolor=edge,
                              markeredgewidth=1.6 if edge != "none" else 0,
                              markersize=10 if marker == "o" else 9,
                              transform=fig.transFigure))
        t = fig.text(x + 0.014, y, label, fontsize=11.5, va="center")
        x = x + 0.014 + t.get_window_extent(renderer).width / fig_w + gap

legend_row(0.11, "검색용 데이터:",
           [("o", REP_COLOR[r], "none", REP_LABEL[r])
            for r in ("caption", "representative_frame", "joint_image_caption",
                      "multi_frame", "dual")])
legend_row(0.04, "검색 계획:",
           [(PLAN_MARKER[p], "black", "none", PLAN_LABEL[p])
            for p in ("B2_vector", "B4_prefilter", "B3_postfilter",
                      "B5_lexical_vector_hybrid")]  # 정본 열거 순서(단독→전→후→혼합), 2026-08-17
           + [("o", "white", "black", "검은 테두리: 3지표 파레토")])

fig.savefig(OUT, dpi=200, facecolor="white")
print(f"saved: {OUT}")
