#!/usr/bin/env python3
"""Clean 16:9 KIISE deck generator (python-pptx). Layout-controlled so text never
overflows: fixed body font, <=5 short bullets/slide, real figures embedded.

Run: Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/scripts/build_deck_pptx.py
Out: presentations/kiise_vlmdb_deck_20260714.pptx  (then libreoffice -> pdf)
"""
from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

ROOT = Path(__file__).resolve().parents[1]
FIGP = ROOT / "paper_assets" / "20260707_presentation_figures"
FIGS = ROOT / "paper_assets" / "20260707_submission_figures"
OUT = ROOT / "presentations" / "kiise_vlmdb_deck_20260714.pptx"

NAVY = RGBColor(0x1B, 0x2A, 0x4A)
BLUE = RGBColor(0x2E, 0x74, 0xB5)
TEXT = RGBColor(0x22, 0x22, 0x22)
MUTED = RGBColor(0x5A, 0x5A, 0x5A)
LIGHT = RGBColor(0xEC, 0xF2, 0xF9)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
BLANK = prs.slide_layouts[6]
SW, SH = prs.slide_width, prs.slide_height


def _box(slide, l, t, w, h):
    return slide.shapes.add_textbox(Inches(l), Inches(t), Inches(w), Inches(h))


def _fill(shape, color):
    shape.fill.solid(); shape.fill.fore_color.rgb = color; shape.line.fill.background()


def _set(p, text, size, color=TEXT, bold=False, align=PP_ALIGN.LEFT):
    p.text = text; p.alignment = align
    r = p.runs[0]; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color


def header(slide, kicker, title):
    bar = slide.shapes.add_shape(1, 0, 0, SW, Inches(1.25)); _fill(bar, NAVY)
    tb = _box(slide, 0.6, 0.12, 12.1, 1.05); tf = tb.text_frame; tf.word_wrap = True
    _set(tf.paragraphs[0], kicker, 13, RGBColor(0x9E, 0xC4, 0xE8), bold=True)
    p = tf.add_paragraph(); _set(p, title, 27, WHITE, bold=True)
    # accent underline
    ac = slide.shapes.add_shape(1, Inches(0.6), Inches(1.25), Inches(2.2), Inches(0.07)); _fill(ac, BLUE)


def bullets(slide, items, top=1.7, left=0.75, width=11.8, size=19, gap=True):
    tb = _box(slide, left, top, width, 5.3); tf = tb.text_frame; tf.word_wrap = True
    for i, it in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        lvl = it[0] if isinstance(it, tuple) else 0
        txt = it[1] if isinstance(it, tuple) else it
        bold = it[2] if isinstance(it, tuple) and len(it) > 2 else False
        mark = "•  " if lvl == 0 else "–  "
        _set(p, mark + txt, size - (lvl * 2), NAVY if (lvl == 0 and bold) else (MUTED if lvl else TEXT), bold=(lvl == 0))
        p.level = 0
        p.space_after = Pt(10 if gap else 4)
        p.space_before = Pt(2)


def figure(slide, img, top=1.6, max_w=7.2, max_h=5.3, left=None, caption=None):
    from PIL import Image
    iw, ih = Image.open(img).size
    ar = iw / ih
    w = Inches(max_w); h = Emu(int(w / ar))
    if h > Inches(max_h):
        h = Inches(max_h); w = Emu(int(h * ar))
    L = Inches(left) if left is not None else Emu(int((SW - w) / 2))
    slide.shapes.add_picture(str(img), L, Inches(top), width=w, height=h)
    if caption:
        cb = _box(slide, Emu(int(L)) / 914400, top + Emu(int(h)) / 914400 + 0.05, Emu(int(w)) / 914400, 0.4)
        _set(cb.text_frame.paragraphs[0], caption, 12, MUTED, align=PP_ALIGN.CENTER)


def table(slide, headers, rows, top=1.7, left=0.75, width=11.8, fs=15):
    nr, nc = len(rows) + 1, len(headers)
    gt = slide.shapes.add_table(nr, nc, Inches(left), Inches(top), Inches(width), Inches(0.4 * nr)).table
    for j, hdr in enumerate(headers):
        c = gt.cell(0, j); c.fill.solid(); c.fill.fore_color.rgb = NAVY
        c.text_frame.paragraphs[0].text = hdr
        rr = c.text_frame.paragraphs[0].runs[0]; rr.font.size = Pt(fs); rr.font.bold = True; rr.font.color.rgb = WHITE
    for i, row in enumerate(rows, 1):
        for j, val in enumerate(row):
            c = gt.cell(i, j); c.fill.solid(); c.fill.fore_color.rgb = LIGHT if i % 2 else WHITE
            c.text_frame.paragraphs[0].text = str(val)
            rr = c.text_frame.paragraphs[0].runs[0]; rr.font.size = Pt(fs); rr.font.color.rgb = TEXT
            if j == 0:
                rr.font.bold = True; rr.font.color.rgb = NAVY


def slide():
    return prs.slides.add_slide(BLANK)


def title_slide():
    s = slide(); bg = s.shapes.add_shape(1, 0, 0, SW, SH); _fill(bg, NAVY)
    band = s.shapes.add_shape(1, 0, Inches(2.7), SW, Inches(0.09)); _fill(band, BLUE)
    tb = _box(s, 1.0, 2.9, 11.3, 2.3); tf = tb.text_frame; tf.word_wrap = True
    _set(tf.paragraphs[0], "도시 감시 멀티모달 데이터의", 30, WHITE, bold=True)
    p = tf.add_paragraph(); _set(p, "저장 · 색인 · 검색 구조 실험 체계", 30, WHITE, bold=True)
    p2 = tf.add_paragraph(); _set(p2, "비순환 워크로드 위에서 정확도 · 지연 · 저장을 비교하다", 17, RGBColor(0xBF, 0xD6, 0xEE))
    fb = _box(s, 1.0, 6.3, 11.3, 0.6)
    _set(fb.text_frame.paragraphs[0], "KIISE DBR 2026 투고 준비   ·   2026-07-14", 14, RGBColor(0x9E, 0xC4, 0xE8))


def divider(num, text):
    s = slide(); bg = s.shapes.add_shape(1, 0, 0, SW, SH); _fill(bg, LIGHT)
    bar = s.shapes.add_shape(1, 0, Inches(3.0), Inches(0.25), Inches(1.5)); _fill(bar, BLUE)
    tb = _box(s, 0.9, 2.95, 11.5, 1.6); tf = tb.text_frame
    _set(tf.paragraphs[0], f"PART {num}", 16, BLUE, bold=True)
    p = tf.add_paragraph(); _set(p, text, 32, NAVY, bold=True)


# ---------------- BUILD ----------------
title_slide()

# 1. one-line summary
s = slide(); header(s, "한 장 요약", "새 모델이 아니라 'DB가 증거를 찾는 법'을 연구한다")
bullets(s, [
    (0, "AI가 답하기 전에, 데이터베이스가 어떤 증거를 어떻게 찾아 줄 것인가", True),
    (1, "대상: 도시 감시·교통 CCTV 영상 + 자연어 질의 + 센서·시공간 메타데이터"),
    (1, "비교: 저장 단위 · 색인 구조 · 필터 결합 방식 · 관계형 DB 구현"),
    (1, "평가: 정확도 · 지연시간 · 저장공간, 그리고 VLM 답변까지의 전파"),
    (0, "핵심 기여: 결과를 부풀리는 '순환성'을 먼저 차단한 뒤 구조를 비교", True),
])

divider("1", "연구 배경과 문제 정의")

# 2. background - what is multimodal here
s = slide(); header(s, "배경", "하나의 질의가 세 가지 정보를 함께 써야 한다")
bullets(s, [
    (0, "관제 질의 예: \"오전에 도로변에 주차된 차가 있는 클립\""),
    (1, "영상/프레임 — CCTV 장면 자체"),
    (1, "텍스트 — 장면을 서술한 캡션(사건 설명)"),
    (1, "메타데이터 — 시간·위치·신호·차량밀도 (센서 기록)"),
    (0, "→ 이 조합 위에서 VLM이 답하려면 DB가 먼저 올바른 증거를 찾아야 한다", True),
], top=1.6, width=6.2)
figure(s, FIGP / "fig02_multimodal.png", top=1.7, max_w=6.2, max_h=5.2, left=6.9)

# 3. problem - circularity
s = slide(); header(s, "문제 발견 (기존 벤치마크의 함정)", "필터·정답·문서가 같은 라벨에서 나오면 결과가 '보장'된다")
bullets(s, [
    (0, "라벨 풍부한 공개 데이터셋으로 워크로드를 짜면 흔히 발생하는 함정"),
    (1, "필터 조건 ⊆ 정답  →  필터가 벡터 검색을 이기는 것이 '구성상 보장'"),
    (1, "라벨을 재진술한 문서 →  어휘 매칭만으로 완벽 지표(MRR=nDCG=1.0)"),
    (0, "= 순환성(circularity). 검색을 잘해서가 아니라 답을 베낀 것", True),
    (1, "이 상태에서 어떤 구조가 좋은지 비교하면 결론이 오염된다"),
])

# 4. problem quantified - collapse
s = slide(); header(s, "문제의 정량 확인", "순환 워크로드를 '수리'하면 완벽 지표가 무너진다")
table(s, ["워크로드", "지표", "수리 전(순환)", "수리 후(비순환)"], [
    ["VRU 사고영상", "B4 nDCG@10", "0.97", "0.32"],
    ["지능형 CCTV", "BM25 nDCG@10", "0.96", "0.11"],
    ["522 교차로", "semantic 부호", "(음수 불가능)", "음수 등장"],
], top=1.9)
bullets(s, [(0, "완벽 지표는 성능이 아니라 '경고 신호'였다 — 그래서 평가 체계부터 바로잡는다", True)], top=4.6)

divider("2", "실험 설정: 데이터셋과 워크로드")

# 5. solution - tri-source
s = slide(); header(s, "해법", "세 채널을 서로 다른 출처로 분리한다 (비순환 tri-source)")
table(s, ["채널", "무엇", "출처", "쓰임"], [
    ["PREDICATE(필터)", "시간·위치·신호·밀도", "센서 기록", "조건으로 거르기"],
    ["RELEVANCE(정답)", "정차·주차 등 장면", "사람 주석", "채점 기준"],
    ["DOCUMENT(문서)", "장면 설명 문장", "VLM 캡션(픽셀만)", "검색 대상"],
], top=1.9)
bullets(s, [(0, "세 출처가 다르므로 '진짜 검색을 잘했는지' 공정하게 잴 수 있다 (A6 기계감사 통과)", True)], top=4.7)

# 6. datasets
s = slide(); header(s, "확보한 데이터셋", "국내 522를 중심으로, 해외·타도메인으로 교차검증")
table(s, ["역할", "데이터셋", "쓰임"], [
    ["메인 헤드라인", "AI-Hub 522 교차로 CCTV (63교차로·32,880클립)", "비순환 tri-source 검색"],
    ["색인 코퍼스", "시내도로 132K + 522-visual 143K (CLIP 512d)", "색인·filtered-ANN"],
    ["외적타당성", "MEVA(검색) · MIRIS(색인) · UCA(검색)", "국제·타도메인 재현"],
    ["붕괴 데모", "VRU · 지능형 CCTV", "순환→수리 붕괴"],
], top=1.9, fs=14)

# 7. workload flow
s = slide(); header(s, "워크로드 동작 흐름", "클립 하나가 저장·색인·검색되기까지")
bullets(s, [
    (0, "① 클립에서 3정보 추출: 캡션(문서)·센서(조건)·주석(정답)"),
    (0, "② 저장: 캡션을 임베딩(숫자 벡터)으로 바꿔 조건·정답과 함께 DB에"),
    (0, "③ 색인: 비슷한 벡터끼리 묶은 '지도'를 만들어 빠른 검색"),
    (0, "④ 검색: 조건으로 거르고 → 질의 벡터로 상위 K개 → 정답표로 채점"),
], top=1.7, width=6.3, size=18)
figure(s, FIGP / "fig05_pipeline.png", top=1.7, max_w=6.2, max_h=5.2, left=6.9)

divider("3", "방법론: 설계공간을 변수화한 파이프라인")

# 8. design space
s = slide(); header(s, "방법론", "저장·색인·필터·배포의 선택지를 변수화해 통제 비교")
table(s, ["설계 축", "변수화한 선택지"], [
    ["검색 전략", "metadata / BM25 / vector / postfilter / prefilter / hybrid"],
    ["저장 단위", "clip-caption / frame-vector / multi-vector / dual-index"],
    ["색인 구조", "Flat / IVF-Flat / HNSW / IVF-PQ (1만→1M 스케일)"],
    ["필터 결합", "prefilter / postfilter / 무작위-마스크 대조"],
    ["관계형 구현", "pgvector / Milvus / Weaviate · global vs partial index"],
    ["배포 정책", "hot/cold 손익분기 N*"],
], top=1.85, fs=14)
bullets(s, [(0, "동일 질의·정답·지표(nDCG@10·recall·MRR + 격리 지연 + 저장공간)로 비교", True)], top=6.35, size=15)

divider("4", "실험 결과와 결론")

# 9. result - prefilter value
s = slide(); header(s, "결과 ① 검색", "필터의 가치는 '조건의 성격'이 결정한다")
bullets(s, [
    (0, "하드 제약(반드시 만족): prefilter가 유의하게 이득", True),
    (1, "522 strict  B4−B2 = +0.098  (95% CI [0.068, 0.133])"),
    (1, "MEVA에서 독립 재현  = +0.093  (CI [0.075, 0.113])"),
    (0, "소프트 의도(느슨): 결합도에 따라 부호가 갈림 (탐색적)", True),
    (1, "독립 조건이면 오히려 관련 문서를 깎아 손해가 날 수 있음"),
])

# 10. result - filtered-ANN bias
s = slide(); header(s, "결과 ② 색인 위 필터", "공유 색인 postfilter는 재현율을 과대평가한다")
figure(s, FIGS / "fig_selectivity_filter.png", top=1.55, max_w=7.4, max_h=5.4, left=0.5)
bullets(s, [
    (0, "실제 predicate는 '군집'한다", True),
    (1, "무작위 마스크 대비 재현율 최대 +0.63 과대평가"),
    (1, "pgvector에서도 같은 기전 재현"),
    (0, "→ 선택적 필터엔 partial/local index", True),
], top=1.8, left=8.2, width=4.7, size=16)

# 11. result - index 3-axis
s = slide(); header(s, "결과 ③ 색인 구조", "HNSW가 지연-정확도 전선을 지배, PQ는 저장 극한용")
figure(s, FIGS / "fig_index_structure_pareto.png", top=1.55, max_w=7.4, max_h=5.4, left=0.5)
bullets(s, [
    (0, "143K 실측 (정확도·지연·저장 3축)", True),
    (1, "HNSW: 재현율 0.99+, 지연 ~상수(≈300× 이득)"),
    (1, "IVF-PQ: 22–35× 압축, 대신 재현율↓"),
    (1, "Flat: 소규모만, 이상은 선형 증가"),
], top=1.8, left=8.2, width=4.7, size=16)

# 12. result - storage/partial/hotcold
s = slide(); header(s, "결과 ④ 저장 단위 · 부분 색인 · 배포", "데이터셋에 따라 최적 저장이 다르고, 선택적 필터엔 partial")
bullets(s, [
    (0, "저장 단위 = 캡션-질의 정합에 의존", True),
    (1, "522: clip-caption 최적 / MEVA: frame-vector 지배 / multi·dual 무익"),
    (0, "partial/local index가 선택적 조건에서 global을 지배", True),
    (1, "공간(카메라) 조건: global 재현율 0.49 붕괴 vs partial 0.99"),
    (1, "시간 조건: global 8.1ms vs partial 0.4ms — 둘 다 partial이 안정"),
    (0, "배포 규칙: recall<0.95 또는 질의>N* → 지역 색인 (MIRIS 재현)", True),
], size=17)

# 13. external validity
s = slide(); header(s, "결과 ⑤ 외적 타당성", "국내 522의 발견이 해외·타도메인에서 재현된다")
table(s, ["데이터셋", "학회/도메인", "재현된 발견"], [
    ["MEVA", "WACV·해외 CCTV", "하드 prefilter 이득 + 캡션 검색 한계"],
    ["MIRIS", "SIGMOD·교통 영상", "선택적 조건서 partial index 우위"],
    ["UCA", "영어·이상행동", "이중 정답 + 소프트 필터 손해 방향"],
], top=1.9, fs=15)

# 14. conclusion
s = slide(); header(s, "결론", "구조 선택은 '타당성'과 '결합도' 위에서 평가되어야 한다")
bullets(s, [
    (0, "① 완벽 지표는 경고 신호 — 워크로드의 비순환성부터 기계 감사"),
    (0, "② 필터의 가치는 조건의 경성 × predicate-정답 결합도가 결정"),
    (0, "③ 저장→색인→필터→배포 설계공간에 데이터셋-의존적 최적점이 있다"),
    (0, "④ 선택적 필터엔 partial index, HNSW가 색인 전선을 지배"),
    (0, "→ 국내 522 + 해외 MEVA·MIRIS·영어 UCA로 교차 재현 (외적타당성)", True),
])

prs.save(str(OUT))
print(f"saved {OUT}  ({len(prs.slides.__iter__.__self__._sldIdLst)} slides)")
