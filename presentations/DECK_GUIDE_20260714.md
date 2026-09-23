# 발표 덱 제작·편집 가이드 (2026-07-14)

## 산출물
- **`kiise_vlmdb_deck_20260714.pptx`** (19슬라이드, 16:9) + `.pdf`
- 생성기(편집 소스): **`2026_KIISE/scripts/build_deck_pptx.py`** — 이 파이썬 파일이 덱의 "원본"이다. 슬라이드 내용을 바꾸려면 이 파일을 고치고 재빌드한다.

## 재빌드 방법 (2줄)
```bash
cd 2026_KIISE
../Datasets/envs/kiise-vlmdb/bin/python scripts/build_deck_pptx.py
soffice --headless --convert-to pdf --outdir presentations presentations/kiise_vlmdb_deck_20260714.pptx
```

## 왜 기존 덱이 엉망이었나 → 무엇을 고쳤나
| 기존 문제 | 해결 |
|---|---|
| 텍스트가 슬라이드 밖으로 넘침(잘림) | 슬라이드당 짧은 불릿 ≤5개, 폰트 크기 고정, 텍스트박스 위치 통제 |
| 그림 0장 (텍스트만) | 실제 결과 그림 삽입(pareto·selectivity·pipeline·multimodal) |
| 밋밋한 기본 pandoc 템플릿 | 네이비/블루 디자인 시스템(헤더바·섹션 divider·스타일 표) |
| 문장이 너무 길고 빽빽 | 문장→핵심 구(句)로 압축 |

## 슬라이드 구성 (4부)
1. 타이틀
2. 한 장 요약
- **PART 1 배경·문제**: (3)배경·멀티모달 (4)순환성 함정 (5)붕괴 정량확인
- **PART 2 실험설정**: (6)tri-source 3채널 (7)데이터셋 (8)워크로드 흐름
- **PART 3 방법론**: (9)설계공간 변수화 표
- **PART 4 결과·결론**: (10)검색 prefilter (11)filtered-ANN 그림 (12)색인3축 그림 (13)저장/partial/배포 (14)외적타당성 (15)결론

## 편집 팁 (build_deck_pptx.py 안에서)
- 새 불릿 슬라이드: `header(s, "머리말", "제목")` + `bullets(s, [(0,"큰항목",True),(1,"세부")])` — `0`=큰불릿, `1`=들여쓴 세부, 3번째 `True`=강조.
- 그림 슬라이드: `figure(s, 경로, max_w=.., left=..)` — 자동으로 비율 유지·중앙정렬.
- 표: `table(s, [헤더...], [[행...]])`.
- 색/폰트: 상단 상수(NAVY/BLUE/TEXT/LIGHT, 폰트 Pt) 수정.

## 알려진 사소한 caveat (정직)
- **PDF에서 괄호·숫자 앞뒤 공백**("클립 )")처럼 보이는 것은 **LibreOffice의 한글+ASCII 혼합 렌더 특성**이다. pptx에 저장된 실제 텍스트에는 공백이 없으며, **PowerPoint로 열면 정상**이다.
- 그림 일부는 원본 PNG에 제목/부제가 이미 박혀 있어(예: multimodal 도식) 슬라이드 제목과 중복될 수 있다 — 필요시 다른 그림으로 교체(paper_assets/20260707_presentation_figures/fig01–15, submission_figures/).

## 외부 에이전트 위임 시
이 가이드 + `build_deck_pptx.py` + `project_md/760_RESEARCH_FLOW`(내용 근거) + `720/740`(수치)을 넘기면, 에이전트가 (a) 내용은 760/720에서, (b) 스타일·레이아웃은 build_deck_pptx.py에서, (c) 그림은 paper_assets에서 가져와 재빌드할 수 있다. 수치는 반드시 결과 CSV(`results/`, `paper_assets/20260713_db_design/`)와 대조.
