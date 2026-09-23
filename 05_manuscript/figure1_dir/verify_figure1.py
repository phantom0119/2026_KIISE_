#!/usr/bin/env python3
"""그림 1(파이프라인 개념도) 검증 스크립트.

그림 1은 데이터 기반 도표가 아니라 개념 도식이므로, 검증 대상은
(A) 파일 무결성(참조 파일 존재, 캡션 문구, 이미지 해상도/체크섬)과
(B) 도식에 인쇄된 모든 텍스트 요소가 현재 원고 본문과 정합하는지이다.
실행: python3 verify_figure1.py
"""
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path("/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE")
MS = ROOT / "manuscript" / "0_main_paper.md"
FIG = ROOT / "manuscript" / "Figure1.png"
FIG_VARIANT = ROOT / "manuscript" / "figure1_dir" / "Figure1_pre_terms_20260809.png"
PATCH = ROOT / "manuscript" / "figure1_dir" / "patch_figure1_terms_20260809.py"

EXPECTED_CAPTION = "&lt;그림 1&gt; 비순환 평가 작업 부하, 벡터 데이터베이스 계층 설계 및 VLM 답변 전파 분석 파이프라인"
EXPECTED_IMG_REF = "](./Figure1.png)"

# (검증 ID, 도식 내 텍스트 요소, 원고에서 요구되는 부분 문자열 목록[AND])
TEXT_CHECKS = [
    ("T01", "RQ1 박스: '정답 조건 주입'", ["정답 조건 주입"]),
    ("T02", "RQ1 박스: '정답 라벨 재진술 주입'", ["정답 라벨 재진술 주입"]),
    ("T03", "RQ1 박스: 비순환 평가 작업 부하 구성·순환성 진단", ["비순환 평가 작업 부하", "순환성 진단"]),
    ("T04", "RQ2 박스 제목: '검색용 데이터 구성(RQ2)'", ["검색용 데이터 구성(RQ2)"]),
    ("T05", "RQ2 항목: 영상 설명문/대표 이미지/이미지·설명문 결합/다중 이미지/이중 색인",
     ["영상 설명문", "대표 이미지", "이미지·설명문 결합", "다중 이미지", "이중 색인"]),
    ("T06", "RQ3 박스 제목: '검색 계획(RQ3)'", ["검색 계획(RQ3)"]),
    ("T07", "RQ3 항목: 벡터 단독/전·후 조건 적용/혼합 검색",
     ["벡터 단독 검색", "검색 전 조건 적용", "검색 후 조건 적용", "혼합 검색"]),
    ("T08", "RQ4 박스 제목: '검색 신호와 순위 융합(RQ4)'", ["검색 신호와 순위 융합(RQ4)"]),
    ("T09", "RQ4 항목: 메타데이터 단독/BM25/벡터/BM25–벡터 RRF",
     ["메타데이터 단독", "BM25 어휘 검색", "벡터", "BM25–벡터 RRF"]),
    ("T10", "RQ5 박스 제목: '물리 색인과 배포(RQ5)'", ["물리 색인과 배포(RQ5)"]),
    ("T11", "RQ5 항목: Flat/HNSW/IVF-Flat/IVF-PQ",
     ["Flat", "HNSW", "IVF-Flat", "IVF-PQ"]),
    ("T12", "RQ5 항목: 전역 색인/조건별 부분 색인", ["전역 색인", "조건별 부분 색인"]),
    ("T13", "RQ6 박스 제목: '답변 전파 진단(RQ6)'", ["VLM 답변 전파 진단"]),
    ("T14", "RQ6 항목: 관련 클립 회수/검색 문맥 인식/과제 편향 통제",
     ["관련 클립 회수", "검색 문맥 인식", "과제 편향 통제"]),
    ("T15", "정답 기준: '의미론적 정답'", ["의미론적 정답"]),
    ("T16", "정답 기준: '엄격한 정답'", ["엄격한 정답"]),
    ("T17", "근사 색인 평가 기준: 조건별 Flat 상위 10개", ["Flat 전수 검색", "재현율@10"]),
    ("T18", "평가 박스: nDCG@10", ["nDCG@10"]),
    ("T19", "평가 박스: 재현율@10(Recall@10)", ["재현율", "Recall@10"]),
    ("T20", "평가 박스: p50/p95 지연", ["p50", "p95"]),
    ("T21", "평가 박스: 색인 구축 시간", ["색인 구축 시간"]),
    ("T22", "평가 박스: 벡터 저장량·색인 크기", ["벡터 저장량", "색인 크기"]),
    ("T23", "원천①: 센서 기록", ["센서 기록"]),
    ("T24", "원천① 항목 '위치'", ["원본 위치"]),
    ("T25", "원천②: 영상 픽셀 기반 설명문", ["영상 픽셀", "설명문"]),
    ("T26", "원천③: 사람 주석 = 검색 정답 집합", ["사람 주석", "검색 정답 집합"]),
    ("T27", "의미 조건/메타데이터 조건 이원 입력", ["의미 조건", "메타데이터 조건"]),
    ("T28", "그림 도입문: 세 원천 자료 분리 문장", ["그림 1은 세 원천 자료의 분리부터"]),
    # 도식 전용 예시 문구: 원고 본문에는 없어야 정상(도식용 가상 질의)
    ("T29", "[도식 예시] 사용자 질의 '오전 10시경에 오토바이 2대'", ["오전 10시경에 오토바이"]),
]

FIGURE_TERMS = [
    "센서 기록",
    "영상 픽셀",
    "의미 조건",
    "메타데이터 조건",
    "비순환 평가 작업 부하",
    "구성·순환성 진단 (RQ1)",
    "생성 원천 분리",
    "직접적인 정답 정보 재사용 검사",
    "BM25–벡터RRF",
    "배포: 전역 색인, 조건별 부분 색인",
    "근사 색인 평가 기준: 조건별 Flat 상위 10개",
    "p50/p95 검색 지연",
    "벡터 저장량·색인 크기",
    "색인 구축 시간",
    "답변 전파 진단",
    "관련 클립 회수",
    "검색 문맥 인식",
    "과제 편향 통제",
]


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def main() -> int:
    text = MS.read_text(encoding="utf-8")
    lines = text.splitlines()
    ok = True

    print("== (A) 파일 무결성 ==")
    cap_line = next((i + 1 for i, l in enumerate(lines) if EXPECTED_CAPTION in l), None)
    ref_line = next((i + 1 for i, l in enumerate(lines) if EXPECTED_IMG_REF in l), None)
    print(f"A1 캡션 문구 원고 존재: {'PASS (행 %s)' % cap_line if cap_line else 'FAIL'}")
    print(f"A2 ./Figure1.png 참조 존재: {'PASS (행 %s)' % ref_line if ref_line else 'FAIL'}")
    print(f"A3 Figure1.png 존재: {'PASS' if FIG.exists() else 'FAIL'}"
          + (f" (md5={md5(FIG)}, {FIG.stat().st_size} bytes)" if FIG.exists() else ""))
    print(f"A4 교체 전 원본 백업 존재: {'PASS' if FIG_VARIANT.exists() else 'FAIL'}"
          + (f" (md5={md5(FIG_VARIANT)})" if FIG_VARIANT.exists() else ""))
    try:
        from PIL import Image
        im = Image.open(FIG)
        dimensions_ok = im.size == (2451, 1147)
        print(f"A5 Figure1.png 해상도/DPI: {'PASS' if dimensions_ok else 'FAIL'} {im.size}, dpi={im.info.get('dpi')}")
        ok &= dimensions_ok
    except Exception as e:  # noqa: BLE001
        print(f"A5 해상도 확인 불가: {e}")
    ok &= bool(cap_line and ref_line and FIG.exists())

    print("\n== (B) 도식 텍스트 요소 ↔ 원고 본문 대조 ==")
    for cid, label, needles in TEXT_CHECKS:
        hits = {}
        for n in needles:
            idx = [i + 1 for i, l in enumerate(lines) if n in l]
            hits[n] = idx[:3]
        if cid == "T29":  # 도식 전용 예시: 원고 미출현이 정상
            absent = all(not v for v in hits.values())
            print(f"{cid} {label}: {'예상대로 원고 미출현(도식 예시)' if absent else 'NOTE: 원고에도 출현 ' + str(hits)}")
            continue
        missing = [n for n, v in hits.items() if not v]
        if missing:
            ok = False
            print(f"{cid} {label}: FAIL (원고에 없음: {missing})")
        else:
            locs = "; ".join(f"'{n}'→행{v}" for n, v in hits.items())
            print(f"{cid} {label}: PASS ({locs})")

    print("\n== (C) 재생성 스크립트의 도식 정본 용어 ==")
    patch_text = PATCH.read_text(encoding="utf-8") if PATCH.exists() else ""
    for term in FIGURE_TERMS:
        present = term in patch_text
        ok &= present
        print(f"{'PASS' if present else 'FAIL'}  {term}")

    print(f"\n총괄: {'PASS' if ok else 'FAIL 존재'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
