#!/usr/bin/env python3
"""그림 1 용어 통일 패치 (2026-08-11 개정).

편집 가능한 원본이 보존되지 않은 Figure1.png에서 텍스트 영역만 다시 그린다.
아이콘·CCTV 썸네일·화살표·상자 경계·색상과 1482×695 해상도는 보존한다.

실행: python3 patch_figure1_terms_20260809.py <입력PNG> <출력PNG>
"""
import sys
from PIL import Image, ImageDraw, ImageFont

SRC, DST = sys.argv[1], sys.argv[2]
BOLD = "/usr/share/fonts/truetype/nanum/NanumBarunGothicBold.ttf"
REGULAR = "/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf"

im = Image.open(SRC).convert("RGB")
if im.size != (1482, 695):
    raise SystemExit(f"unexpected Figure1 size: {im.size}")
d = ImageDraw.Draw(im)

WHITE = (255, 255, 255)
NAVY = (47, 85, 151)
BLUE = (31, 95, 168)
GREEN = (20, 110, 48)
PURPLE = (104, 63, 160)
ORANGE = (222, 105, 0)
RED = (204, 0, 0)
BROWN = (131, 91, 0)
BLACK = (0, 0, 0)
PALE_BLUE = (234, 241, 249)
PALE_YELLOW = (255, 249, 231)
PALE_RED = (255, 245, 243)


def font(size, bold=False):
    return ImageFont.truetype(BOLD if bold else REGULAR, size)


def fit(text, width, start, bold=False):
    size = start
    while size > 9:
        f = font(size, bold)
        if d.textlength(text, font=f) <= width:
            return f
        size -= 1
    return font(size, bold)


def center(text, x, y, size, color, width=None, bold=False):
    f = fit(text, width, size, bold) if width else font(size, bold)
    d.text((x, y), text, font=f, fill=color, anchor="mm")


def left(text, x, y, size, color=BLACK, width=None, bold=False):
    f = fit(text, width, size, bold) if width else font(size, bold)
    d.text((x, y), text, font=f, fill=color, anchor="lm")


# 세 원천의 정본 명칭.
d.rectangle([57, 54, 219, 83], fill=(240, 250, 243))
center("센서 기록", 139, 68, 19, GREEN, 150, True)
d.rectangle([70, 194, 220, 222], fill=(239, 246, 254))
center("영상 픽셀", 145, 208, 19, BLUE, 140, True)

# 질의의 두 조건명: 원어 병기를 제거하고 본문 정본만 사용한다.
d.rectangle([270, 143, 385, 223], fill=PALE_YELLOW)
center("의미 조건", 328, 181, 18, ORANGE, 100, True)
d.rectangle([411, 143, 527, 223], fill=PALE_YELLOW)
center("메타데이터", 469, 171, 17, ORANGE, 105, True)
center("조건", 469, 194, 17, ORANGE, 105, True)

# RQ1: 작업 부하 구성과 순환성 진단.
d.rectangle([282, 273, 516, 480], fill=WHITE)
center("비순환 평가 작업 부하", 399, 296, 19, RED, 222, True)
center("구성·순환성 진단 (RQ1)", 399, 322, 19, RED, 222, True)
left("• 생성 원천 분리", 300, 359, 15, width=205)
left("• 직접적인 정답 정보 재사용 검사", 300, 392, 15, width=205)
left("• 정답 조건 주입", 300, 425, 15, width=205)
left("• 정답 라벨 재진술 주입", 300, 458, 15, width=205)

# 벡터 데이터베이스 계층 헤더.
d.rectangle([570, 13, 980, 55], fill=NAVY)
center("벡터 데이터베이스 계층", 775, 33, 30, WHITE, 380, True)

# RQ2: 검색용 데이터 다섯 구성.
d.rectangle([585, 113, 969, 196], fill=WHITE)
left("• 영상 설명문", 603, 132, 16, width=160)
left("• 대표 이미지", 603, 164, 16, width=160)
left("• 이중 색인", 603, 190, 16, width=160)
left("• 이미지·설명문 결합", 785, 132, 16, width=175)
left("• 다중 이미지", 785, 164, 16, width=175)

# RQ3: 정본 순서(벡터 단독→검색 전→검색 후→혼합).
d.rectangle([585, 247, 969, 300], fill=WHITE)
left("• 벡터 단독 검색", 603, 261, 16, width=165)
left("• 검색 전 조건 적용", 603, 289, 16, width=165)
left("• 검색 후 조건 적용", 785, 261, 16, width=175)
left("• 혼합 검색", 785, 289, 16, width=175)

# RQ4: 네 검색 신호와 융합 명칭.
d.rectangle([585, 355, 969, 415], fill=WHITE)
left("• 메타데이터 단독", 603, 370, 16, width=165)
left("• BM25 어휘 검색", 603, 402, 16, width=165, bold=True)
left("• 벡터", 785, 370, 16, width=175)
left("• BM25–벡터RRF", 785, 402, 16, width=175)

# RQ5: 물리 색인과 배포 범위.
d.rectangle([585, 463, 969, 529], fill=WHITE)
left("• 물리 색인: Flat, HNSW, IVF-Flat, IVF-PQ", 603, 481, 16, width=350)
left("• 배포: 전역 색인, 조건별 부분 색인", 603, 514, 16, width=350)

# 검색 문맥 명칭.
d.rectangle([1027, 87, 1186, 119], fill=PALE_BLUE)
center("검색 문맥", 1106, 102, 23, BLUE, 150, True)

# 정답 및 근사 색인 평가 기준.
d.rectangle([585, 556, 969, 681], fill=WHITE)
left("• 의미론적 정답: 의미 조건 충족", 603, 581, 16, width=350)
left("• 엄격한 정답: 의미 조건·메타데이터 조건 충족", 603, 621, 16, width=350)
left("• 근사 색인 평가 기준: 조건별 Flat 상위 10개", 603, 661, 16, width=350)

# 품질·비용 지표의 정본 명칭.
d.rectangle([1068, 492, 1332, 634], fill=WHITE)
center("검색 품질·비용 평가", 1200, 510, 20, BROWN, 245, True)
left("• nDCG@10", 1085, 539, 14, width=230, bold=True)
left("• 재현율@10", 1085, 560, 14, width=230, bold=True)
left("• p50/p95 검색 지연", 1085, 581, 14, width=230, bold=True)
left("• 벡터 저장량·색인 크기", 1085, 602, 14, width=230)
left("• 색인 구축 시간", 1085, 623, 14, width=230)

# RQ6: 심사자 프레임과 본문 정본의 세 조건.
d.rectangle([1223, 88, 1373, 150], fill=PALE_RED)
center("답변 전파 진단", 1298, 111, 21, RED, 140, True)
center("(RQ6)", 1298, 137, 20, RED, 140, True)
d.rounded_rectangle([1223, 228, 1370, 406], radius=11, fill=WHITE, outline=(232, 46, 30), width=1)
left("• 관련 클립 회수", 1242, 273, 17, width=115)
left("• 검색 문맥 인식", 1242, 318, 17, width=115)
left("• 과제 편향 통제", 1242, 363, 17, width=115)

im.save(DST, dpi=(96, 96))
print(f"saved: {DST}")
