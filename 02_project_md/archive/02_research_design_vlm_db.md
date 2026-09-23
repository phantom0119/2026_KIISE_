# 연구 설계: 도시 감시형 VLM-DB

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 이 설계는 초기 연구 질문의 출발점으로 보존한다. 실제 실행 결과는 VRU/AI Hub 지능형 CCTV true multimodal retrieval, AI Hub 다각도 CCTV fixed VLM answer control, 시내도로 CCTV ANN index benchmark까지 확장되었다. 최신 RQ와 수치 기준은 `24_final_experiment_pipeline_spec_20260707.md`와 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 문제 정의

도시 감시 데이터는 영상/이미지, 사건 보고서, 교통·기상·지도 메타데이터, 시간·공간 로그가 함께 존재한다. 하지만 일반적인 VLM 질의응답 실험은 모델에 이미지 또는 비디오를 직접 넣어 답을 생성하는 데 집중하고, 데이터베이스 관점의 저장·색인·검색 구조가 최종 품질에 미치는 영향을 충분히 분리하지 않는다.

본 연구는 도시 감시형 멀티모달 데이터베이스에서 다음 문제를 다룬다.

> 자연어 질의와 메타데이터 조건이 함께 주어질 때, 어떤 저장·색인·검색 구조가 정답 증거를 더 잘 찾고, 더 빠르고, 더 낮은 비용으로 VLM 답변을 지원하는가?

## 연구 질문

| ID | 연구 질문 |
|---|---|
| RQ1 | 단일 벡터 검색, sparse 검색, metadata filter, hybrid retrieval은 text-to-event 검색에서 어떤 정확도와 지연시간 차이를 보이는가? |
| RQ2 | 시간·장소·카메라·날씨 같은 metadata condition이 강해질수록 각 인덱스 구조의 recall 손실은 어떻게 달라지는가? |
| RQ3 | retrieval recall이 event grounding과 VQA accuracy에 어느 정도 전파되는가? |
| RQ4 | 성능 향상 대비 저장 비용, 인덱스 구축 비용, query latency의 trade-off는 무엇인가? |

## 가설

| ID | 가설 |
|---|---|
| H1 | metadata-aware hybrid retrieval은 단일 vector-only 검색보다 Recall@k와 nDCG@k가 높다. |
| H2 | vector-only 후처리 필터는 조건이 강한 질의에서 후보 손실이 커져 recall이 하락한다. |
| H3 | retrieval recall이 낮은 구간에서는 VLM backbone을 바꾸더라도 VQA accuracy 개선이 제한된다. |
| H4 | full hybrid 구조는 가장 높은 recall을 보이지만, 2주 프로토타입 기준에서는 PostgreSQL/SQLite + vector index + BM25의 경량 구조가 cost/performance 균형이 가장 좋다. |

## 데이터 구성

우선순위는 “바로 실험 가능한 공개/샘플 데이터”다.

| 계층 | 후보 데이터 | 역할 | 상태 |
|---|---|---|---|
| 영상/키프레임 | AI Hub 이상행동 CCTV 영상 샘플, AI City Challenge, VRU-Accident | visual evidence, event clip | 접근성 확인 필요 |
| 문서 | 사건 설명, 데이터셋 라벨, 합성 상황 보고서, 공개 사고/교통 이벤트 텍스트 | sparse retrieval, report-to-frame grounding | 생성/수집 가능 |
| 메타데이터 | 카메라 ID, 시간, 이벤트 타입, 날씨, 위치, 도로/교차로 | metadata filter, DB query | 일부 합성 가능 |
| QA | 이벤트 타입, 장소/시간 조건, 원인/상황 설명 질의 | VQA/evidence QA | 반자동 생성 가능 |

AI Hub 이상행동 CCTV 영상은 12가지 이상행동과 약 700시간 규모의 비디오 데이터로 공개 설명이 확인된다. 다만 실제 다운로드와 이용 조건은 계정/신청 절차가 필요할 수 있으므로, 접근이 지연되면 AI City Challenge 또는 VRU-Accident 같은 공개 접근 가능한 국제 데이터로 최소 실험을 대체한다.

## 최소 데이터셋 스케일

투고 전 최소 목표:

| 항목 | 최소 목표 | 권장 목표 |
|---|---:|---:|
| 비디오/클립 | 100 | 300 |
| 키프레임 | 1,000 | 5,000 |
| 문서/캡션/보고서 청크 | 300 | 1,000 |
| metadata rows | 1,000 | 10,000 |
| retrieval queries | 100 | 300 |
| grounding queries | 50 | 150 |
| VQA queries | 50 | 150 |

논문 투고 가능성은 데이터 크기보다 “워크로드 정의와 비교 실험의 일관성”에 달려 있다. 작은 데이터셋이어도 모든 baseline이 같은 질의와 정답 표에서 비교되면 논문화 가능하다.

## 시스템 구조

권장 MVP 구조:

```text
raw videos/images
  -> keyframe extraction
  -> visual caption/embedding
  -> object store or local file paths

event reports / labels / generated descriptions
  -> chunking
  -> BM25 index
  -> text embedding

metadata
  -> relational table
  -> time/location/event filters

query
  -> query parser
  -> metadata filter
  -> vector search + BM25 search
  -> rank fusion
  -> optional VLM answerer
  -> metrics logger
```

초기 구현은 과도한 인프라보다 재현성이 중요하다.

- 관계형 계층: SQLite 또는 PostgreSQL
- 벡터 검색: FAISS 또는 pgvector
- sparse 검색: BM25
- hybrid fusion: reciprocal rank fusion 또는 weighted sum
- VLM/VQA: 가능하면 오픈소스 VLM, 시간이 부족하면 caption 기반 QA로 축소

## 비교할 저장·색인 구조

| 구조 | 설명 | 목적 |
|---|---|---|
| B0 Metadata-only | event type/time/location 조건만 사용 | 정형 조건만으로 어디까지 가능한지 확인 |
| B1 BM25-only | 보고서/캡션 텍스트 sparse 검색 | 텍스트 기반 baseline |
| B2 Vector-only | CLIP 또는 text/image embedding ANN 검색 | 단일 벡터 검색 baseline |
| B3 Vector + post-filter | vector top-N 후 metadata filtering | 후처리 필터의 recall 손실 확인 |
| B4 Metadata pre-filter + vector | 조건으로 후보 축소 후 vector search | DB-aware 검색의 이점 확인 |
| B5 Hybrid sparse+dense+metadata | BM25, vector, metadata score 결합 | 최종 제안 구조 |

## 워크로드

| 태스크 | 입력 | 출력 | 정답 |
|---|---|---|---|
| T1 Text-to-clip retrieval | “밤 시간대 배회 장면을 찾아라” | top-k clip/frame IDs | event label, clip ID |
| T2 Text+metadata retrieval | “비 오는 오후 특정 위치의 사고/위험 장면” | top-k evidence bundle | metadata 조건 + event label |
| T3 Report-to-frame grounding | 사건 보고서 문장 | 관련 frame/span | clip/time/frame label |
| T4 Evidence-aware VQA | 질의 + 검색 evidence | 답변 + 근거 ID | QA answer, evidence ID |

## 평가 지표

| 범주 | 지표 |
|---|---|
| 검색 품질 | Recall@1/5/10/20, MRR, nDCG@10 |
| grounding | Hit@1/5, temporal IoU, span F1 |
| VQA | accuracy, exact match, token F1, evidence precision |
| 시스템 | index build time, index size, p50/p95 latency, query throughput |
| 비용 | embedding cost, VLM inference cost, storage per 1K items, query cost |

## 실험 우선순위

1. Retrieval-only 실험을 먼저 완성한다. 논문 최소 성립 조건은 T1/T2와 B0~B5 비교다.
2. Grounding은 라벨이 있는 클립에서 T3만 최소 수행한다.
3. VQA는 시간이 남을 때 T4로 추가한다. VQA가 실패해도 retrieval/grounding 논문으로 축소 가능해야 한다.
4. Latency/cost는 반드시 기록한다. DBR 투고에서 “데이터베이스 연구” 성격을 강화하는 핵심 근거다.

## 예상 표와 그림

| 산출물 | 내용 |
|---|---|
| Table 1 | DBR 2025~2026 관련 연구 동향 요약 |
| Table 2 | 제안 VLM-DB 워크로드 정의 |
| Table 3 | 저장·색인 구조별 기능 비교 |
| Table 4 | baseline별 Recall@k/nDCG/latency/cost 결과 |
| Figure 1 | 전체 시스템 아키텍처 |
| Figure 2 | metadata selectivity에 따른 recall-latency trade-off |
| Figure 3 | retrieval recall과 VQA/grounding 품질의 관계 |

## 실패 시 축소 전략

| 문제 | 축소안 |
|---|---|
| 영상 데이터 접근 지연 | 공개 이미지/프레임 샘플과 합성 보고서로 retrieval 워크로드만 수행 |
| VLM inference 비용 과다 | caption 기반 QA 또는 retrieval-only 논문으로 축소 |
| grounding label 부족 | event label retrieval과 evidence precision 중심으로 축소 |
| PostgreSQL/pgvector 설정 지연 | FAISS + SQLite + BM25 로컬 구조로 대체 |
| 데이터 규모 부족 | 벤치마크 논문 표현을 줄이고 “pilot workload study”로 명시 |

## 주요 확인 출처

- KCI DBR 권호 목록: https://www.kci.go.kr/kciportal/po/search/poSereArtiList.kci?sereId=002167
- AI Hub 이상행동 CCTV 영상: https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=171
- AI City Challenge 2025: https://www.aicitychallenge.org/2025-ai-city-challenge/
- VRU-Accident: https://arxiv.org/abs/2507.09815
