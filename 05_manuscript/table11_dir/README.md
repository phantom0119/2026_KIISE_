# 표 11 — 설명문 증거 조건별 VLM 답변 정확도 (RQ6, §5.2.6)

2026-08-09 심사 대응 개정(`0_main_paper.md`)에서 신설한 표. 심사위원 2의 요구
(답변 모델·프롬프트·표본 수·채점 기준·반복·불확실성 명시 + 표 정리)에 대응한다.

## 1. 대상 수치 ↔ 원천 매핑

| 원고 수치 | 원천 파일 | 비고 |
|---|---|---|
| 조건별 정확도 5종 × 모델 2종 | `data/summary_qwen.json`, `data/summary_llama3.json` | `accuracy` 필드, n_per_config=600 |
| 95% 신뢰구간·대비 Δ·McNemar p | `data/ladder_ci_analysis_20260723.json` | (clip_id×category) 600문항 대응, 부트스트랩 B=10,000, 시드 20260723 |
| 범주별 무관−없음 이득 분해 | `data/percategory_closed_distractor.csv` | `data/compute_percategory_gap.py`로 재현(결정적, 부트스트랩 없음) |
| 사전 필터 후보 수 중앙값 29개 | `data/summary_*.json` | `median_prefilter_candidates` |

## 2. 실험 체계 (원고 §5.2.6 방법 문단의 근거)

- 러너: `../../scripts/run_rag_vqa.py` (시드 20260707, 범주 6종 균형 100문항/범주)
- 원자료: `../table1_dir/data/vru_rag_vqa/rag_vqa_{qwen,llama3}.parquet` (3,000행 = 600문항 × 5조건)
- 프롬프트: `[증거 i] {설명문}` 나열 + `질문/선택지` + "정답 보기의 알파벳(A, B, C, D) 하나만 출력하시오" (make_prompt 함수)
- 검색 질의: 문항이 묻는 속성을 제외한 해당 클립의 나머지 알려진 맥락 속성(build_query 함수) — 정답 속성 누출 방지
- 조건별 제공 설명문 수: 증거 없음 0 / 무관 1 / 벡터 상위 3 / 사전 필터+벡터 상위 3 / 대상 1 (자기 클립 설명문은 검색 후보에서 제외, 대상 조건에서만 제공)
- 생성: 탐욕적 디코딩, 최대 신규 6토큰 → 결정적 1회 실행(반복 불필요)
- 채점: 생성 텍스트의 첫 A–D 문자 추출 후 정답 기호 정확 일치, 무효 응답 0/6,000

## 3. 검증

- `summary_*.json` 정확도 ↔ parquet 재계산 일치 (60_REVIEW S1, 2026-07-23에서 검증 완료)
- 범주별 CSV는 `python3 data/compute_percategory_gap.py` 재실행으로 재현 가능 (2026-08-09 생성)
