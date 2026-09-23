# 2026년 7월 20일 전 투고 실행 계획

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 이 문서의 일정표와 미완료 체크리스트는 초기 계획 기록이다. 현재는 canonical 구축, text/visual retrieval, service packet, fixed LLM/VLM answer-level 실험, 시내도로 CCTV index benchmark, DBR review 원고/PDF 생성까지 진행되었다. 최신 제출 실행 기준은 `27_submission_execution_board_20260707.md`, `40_latest_dataset_and_experiment_synthesis_20260709.md`, `manuscript/submission_materials_index.md`를 따른다.

목표: 2026년 7월 20일 전까지 데이타베이스연구(DBR) 투고 가능한 원고와 최소 실험 결과를 확보한다.

## 논문 범위

반드시 지켜야 할 범위:

- 논문 성격: 워크로드 정의 + 시스템 구조 비교 + 파일럿 실험
- 연구 대상: 도시 감시형 멀티모달 데이터베이스
- 핵심 비교: metadata-aware hybrid retrieval vs vector-only/sparse-only/post-filter baselines
- 핵심 지표: Recall@k, nDCG, latency, index size, query cost
- 선택 지표: event grounding, evidence-aware VQA

범위 밖으로 밀어낼 내용:

- 대규모 신규 벤치마크 완성 주장
- 새 VLM 모델 학습
- 개인정보가 포함된 실제 관제 데이터 사용
- IRB/승인이 필요한 민감 데이터 실험
- 인간 평가

## 일정

| 날짜 | 작업 | 산출물 | 판정 기준 |
|---|---|---|---|
| 07-06 | 주제 고정, 연구 설계 문서화 | `project_md` 문서 세트 | 논문 제목/RQ/실험 범위 확정 |
| 07-07 | 데이터 접근 확인, 대체 데이터 결정 | data source memo | 최소 1개 영상/이미지 소스 접근 가능 |
| 07-08 | 인제스트 스키마와 질의셋 포맷 작성 | schema, query TSV/JSON | frame/report/metadata/evidence ID 연결 |
| 07-09 | BM25, vector-only baseline 구현 | baseline scripts | Recall@k 산출 가능 |
| 07-10 | metadata filter, hybrid fusion 구현 | hybrid scripts | B0~B5 비교 가능 |
| 07-11 | 1차 retrieval 실험 실행 | results CSV/MD | Table 4 초안 생성 |
| 07-12 | latency/index size/cost 측정 | system metrics | DB 논문 성격 확보 |
| 07-13 | grounding 또는 VQA 최소 추가 | optional results | 가능하면 Figure 3 생성 |
| 07-14 | 관련연구와 방법론 초안 | paper draft v0 | 50% 이상 원고화 |
| 07-15 | 결과/분석/위협요인 작성 | paper draft v1 | 핵심 표/그림 삽입 |
| 07-16 | 초록/서론/결론 강화 | paper draft v2 | 논문 메시지 일관성 확보 |
| 07-17 | 형식, 참고문헌, 그림 정리 | submission draft | 투고 형식 점검 |
| 07-18 | 내부 검토와 수정 | near-final PDF | 누락 실험/문장 정리 |
| 07-19 | 최종 교정 | final PDF/source | 제출 준비 완료 |
| 07-20 | 제출 | submission record | 제출 완료 |

## 원고 구조

1. 서론
   - DBR 2025~2026 동향에서 RAG, VLM, 도시/환경 이벤트 연구가 부상했음을 제시.
   - 하지만 멀티모달 도시 감시 데이터를 DB/IR/VLM 워크로드로 통합한 연구가 부족하다고 문제화.
   - 본 논문의 기여 3개를 명시.

2. 관련 연구
   - 국내 DBR: RAG 청킹, 의료/법률/금융/교통 등의 전문 도메인 VLM, PGvector HNSW, LLM 사건 분류.
   - 국제: multimodal RAG, video RAG, visual document retrieval, vector DB, AI City/VRU accident benchmark.
   - 차별점: 모델이 아니라 저장·색인·검색 구조와 워크로드 평가.

3. 문제 정의와 워크로드
   - 데이터 모델: frame/clip, report chunk, metadata, evidence bundle.
   - 질의 유형: text-to-clip, text+metadata retrieval, report-to-frame grounding, evidence-aware VQA.
   - 정답과 평가 지표 정의.

4. 시스템 설계
   - 저장 계층, 인덱스 계층, 질의 처리 파이프라인.
   - B0~B5 baseline 정의.

5. 실험
   - 데이터셋 구성.
   - 질의셋 생성 방법.
   - 구현 환경.
   - 검색 품질, latency, cost 결과.

6. 분석
   - metadata selectivity에 따른 trade-off.
   - retrieval miss가 grounding/VQA에 미치는 영향.
   - 어떤 구조가 어떤 조건에서 유리한지 정리.

7. 한계와 윤리
   - 공개/샘플 데이터 기반 축소 실험임을 명시.
   - 개인정보·감시 데이터 사용의 윤리적 제약 논의.
   - 실제 관제 시스템 적용 전 필요한 비식별화/감사/접근통제 요구사항.

8. 결론
   - VLM-DB 성능은 VLM backbone만이 아니라 retrieval architecture와 metadata-aware indexing에 의해 좌우된다는 결론.

## 산출물 체크리스트

| 산출물 | 필수 여부 | 상태 |
|---|---|---|
| 주제 선정 근거 문서 | 필수 | 완료 |
| 연구 설계 문서 | 필수 | 완료 |
| 투고 일정 문서 | 필수 | 완료 |
| 데이터 소스/스키마 메모 | 필수 | 완료 |
| 데이터 인제스트 스크립트 | 필수 | 미완료 |
| baseline 검색 스크립트 | 필수 | 미완료 |
| 실험 결과 CSV | 필수 | 미완료 |
| 결과 요약 MD | 필수 | 미완료 |
| 논문 원고 | 필수 | 미완료 |
| 그림/표 파일 | 필수 | 미완료 |
| VQA/grounding 추가 실험 | 선택 | 미완료 |

## Go/No-Go 기준

7월 12일까지 다음이 확보되면 본 주제로 투고를 계속한다.

- 최소 100개 이상의 frame/clip 또는 image item
- 최소 100개 이상의 retrieval query
- B1 BM25, B2 vector-only, B5 hybrid 결과
- Recall@k와 latency 결과표

7월 12일까지 위 조건을 만족하지 못하면, 논문을 다음 축소 주제로 전환한다.

> 도시 감시형 멀티모달 검색 워크로드 설계와 공개 데이터 기반 파일럿 분석

이 경우 “성능 우수성”보다 “워크로드 정식화, 평가 프로토콜, 연구 공백 분석”을 더 강하게 써야 한다.

## 리스크와 대응

| 리스크 | 영향 | 대응 |
|---|---|---|
| AI Hub 접근 지연 | 데이터 부족 | AI City/VRU-Accident 또는 샘플 프레임 기반 실험으로 대체 |
| VLM 실행 비용 과다 | VQA 결과 부족 | retrieval-only + caption QA로 축소 |
| 라벨 부족 | grounding 평가 부족 | event label 기반 retrieval 평가로 축소 |
| 실험 결과 차이가 작음 | 기여 약화 | latency/cost/selectivity 분석을 강화 |
| DBR 투고 형식 지연 | 제출 위험 | 7월 17일까지 원고 형식 선확정 |

## 다음 실행 명령

가장 먼저 할 일은 데이터 접근 확인과 최소 실험 파이프라인 생성이다.

1. `data_sources.md` 작성: 사용 가능한 영상/이미지/문서/메타데이터 소스 확정.
2. `schema.md` 작성: clip, frame, report_chunk, metadata, query, relevance 테이블 정의.
3. `scripts/` 생성: 인제스트, BM25, vector baseline, hybrid fusion 순서로 구현.

## 주요 확인 출처

- KCI DBR 권호 목록: https://www.kci.go.kr/kciportal/po/search/poSereArtiList.kci?sereId=002167
- DBR 투고 규정: https://dbsociety.kr/dbr_submission_guide/
- AI Hub 이상행동 CCTV 영상: https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=171
- AI City Challenge 2025: https://www.aicitychallenge.org/2025-ai-city-challenge/
- VRU-Accident: https://arxiv.org/abs/2507.09815
