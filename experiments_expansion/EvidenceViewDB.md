# EvidenceViewDB

## 전문 도메인 RAG를 위한 답변 효용 기반 다중 해상도 증거 뷰의 물리 설계 및 증분 유지관리

> 영문 가제: **EvidenceViewDB: Answer-Utility-Aware Physical Design and Incremental Maintenance of Multi-Granularity Evidence Views for Domain RAG**

- 문서 상태: **P0-A 종료 / STOP_NO_PHYSICAL_GAIN**
- 최초 작성일: 2026-08-07
- 최근 문헌 확인일: 2026-08-07
- 연구 확정 여부: **현재 설계로는 확정하지 않음 — 선택적 물질화의 holdout 실질 이득 미달**
- 목표 연구 분야: 벡터 데이터베이스, 물리 설계, RAG 증거 검색, 색인 유지관리
- 우선 목표 학회: EDBT/ICDE급 데이터베이스 학회
- 상향 목표: PVLDB Research 또는 Experiment, Analysis & Benchmark

---

## 0. 핵심 요약

### 0.1 연구 질문

전문 도메인 RAG 시스템에서 문서를 모두 동일한 크기의 청크로 나누어 동일한 방식으로 벡터화하는 것이 정말 최선인가?

질문마다 필요한 증거의 단위는 서로 다르다. 어떤 질문에는 하나의 정확한 문장이나 표 행이 필요하지만, 다른 질문에는 용어 정의가 포함된 문단이나 여러 문서에 흩어진 증거가 필요하다. 그럼에도 일반적인 RAG 시스템은 하나의 고정된 저장 단위, 임베딩 모델, 색인 형식과 Top-k를 모든 질문에 적용한다.

EvidenceViewDB는 이 문제를 **검색 모델만의 문제가 아니라 데이터베이스 물리 설계 문제**로 정의한다.

### 0.2 한 문장 정의

> EvidenceViewDB는 원문에서 파생된 문단·문장·명제·표 행·그래프 사실 등의 증거 뷰 중, 질의 워크로드에서 실제 답변 품질에 기여하는 뷰만 저장 예산과 지연시간 제약 아래 선택적으로 임베딩·색인하고, 원문 변경 시 영향받은 뷰만 증분 갱신하는 RAG 데이터베이스 시스템이다.

### 0.3 핵심 기여 후보

1. 원문과 다양한 증거 단위의 관계를 보존하는 **다중 해상도 증거 뷰 데이터 모델**
2. Recall이 아닌 최종 답변 효용을 목적함수로 사용하는 **물리 설계 조언자**
3. 저장공간·p95 지연시간·갱신 비용·최신성 제약을 함께 고려하는 **선택적 물질화 알고리즘**
4. 질의별로 최소 충분 증거 집합을 선택하는 **증거 질의 계획기**
5. 원문 변경 시 관련 하위 뷰만 재생성하는 **계보 기반 증분 유지관리**

### 0.4 현재 판정

> **2026-08-07 P0-A 갱신:** 776개 법률 질의의 사전등록 CPU 게이트에서 G0·G1·G2·G4는 통과했으나, 동일 저장 예산의 선택적 물질화 이득인 G3가 실패했다. 자동 판정은 `STOP_NO_PHYSICAL_GAIN`이며 P0-B와 본실험으로 확대하지 않는다. 상세 결과는 [P0-A 최종 보고서](evidenceviewdb_p0/P0A_FINAL_REPORT_20260807.md)에 있다.

연구 설계는 가능하다. 그러나 다음 주장은 이미 선행연구와 겹치므로 사용할 수 없다.

- “처음으로 문서를 여러 해상도로 저장한다.”
- “처음으로 문장·문단·트리플을 함께 검색한다.”
- “처음으로 질문마다 청크 크기를 바꾼다.”
- “적은 문맥이 항상 많은 문맥보다 정확하다.”

현재 남아 있을 가능성이 있는 공백은 다음의 **결합된 데이터베이스 문제**지만, 이번 P0에서는 그 물리적 이득을 입증하지 못했다.

> 어떤 증거 뷰를 실제로 물질화할 것인지, 어떤 색인과 파라미터를 적용할 것인지, 문서 갱신 시 무엇을 재계산할 것인지를 답변 효용과 시스템 비용을 함께 사용해 결정하는 문제

이 공백은 아직 유망하지만, “신규성의 결합”에 의존한다는 위험이 있다. 따라서 본실험 전에 원문 수준의 신규성 감사와 조기 중단 P0가 필요하다.

---

## 1. 문제 배경

### 1.1 일반적인 RAG 저장 방식

일반적인 RAG 파이프라인은 다음과 같이 동작한다.

1. 문서를 고정 길이 청크로 분할한다.
2. 각 청크를 하나의 임베딩 벡터로 변환한다.
3. 모든 벡터를 HNSW, IVF 등의 ANN 색인에 저장한다.
4. 질의 벡터와 가까운 Top-k 청크를 검색한다.
5. 검색된 청크를 생성 모델의 프롬프트에 모두 넣는다.

이 방식은 구현이 간단하지만 다음 세 가지를 고정한다.

- 저장 단위: 모든 문서에 동일한 청크 규칙
- 검색 단위: 모든 질의에 동일한 벡터 표현
- 반환 단위: 모든 질의에 동일한 k 또는 토큰 예산

### 1.2 전문 도메인에서 문제가 커지는 이유

전문 문서는 일반 서술문과 구조가 다르다.

- 금융 문서는 표의 행·열, 기간, 단위와 계산식이 함께 해석되어야 한다.
- 의학 문서는 질환, 개입, 환자 집단, 수치와 예외 조건이 중요하다.
- 법률 문서는 조항, 정의, 적용 범위와 예외 조항의 연결이 중요하다.
- 과학 논문은 주장, 실험 조건, 비교 대상, 표와 그림 설명이 서로 떨어져 있다.

큰 청크는 해석 문맥을 보존하지만 불필요한 내용과 상충 문장을 함께 가져올 수 있다. 작은 청크는 정밀하지만 질의와 매칭할 어휘 또는 필요한 전후 조건을 잃을 수 있다.

따라서 “작은 청크가 좋다” 또는 “많은 문맥이 좋다” 중 하나를 보편적 규칙으로 만들 수 없다. 핵심은 질의마다 **정확하면서도 충분한 증거 단위**를 선택하는 것이다.

### 1.3 연구 목표의 올바른 정의

단순한 Precision@k 최대화는 적절하지 않다. 예를 들어 다중 홉 질문에서 검색된 세 문장이 모두 관련 문장이더라도, 두 번째 추론 단계에 필요한 증거가 없으면 답을 만들 수 없다.

EvidenceViewDB가 목표로 하는 검색 결과는 다음 조건을 만족해야 한다.

- 정밀성: 불필요한 증거가 적다.
- 충분성: 답변에 필요한 모든 핵심 증거가 포함된다.
- 비중복성: 같은 사실의 반복으로 토큰을 낭비하지 않는다.
- 비모순성: 오래되거나 충돌하는 버전이 함께 반환되지 않는다.
- 최신성: 현재 정본과 일치한다.
- 추적 가능성: 모든 반환 증거를 원문 위치와 버전으로 역추적할 수 있다.

이를 본 문서에서는 **최소 충분 증거 집합(minimal sufficient evidence set)**이라고 부른다.

---

## 2. 연구 범위와 비범위

### 2.1 연구 범위

- 텍스트 및 표 중심 전문 도메인 RAG
- 문서–섹션–문단–문장–명제–표 행–관계 사실의 다중 해상도 표현
- 선택적 임베딩 및 색인 물질화
- 워크로드 기반 물리 설계
- ANN/정확 검색과 최종 답변 효용의 연결
- 원문 변경, 삭제, 재청킹 및 임베딩 모델 버전 변경의 증분 유지관리
- 저장량, 검색 지연, 갱신량, 답변 정확도의 공동 평가

### 2.2 초기 연구의 비범위

- 대규모 임베딩 기초모델을 처음부터 학습하는 연구
- GraphRAG 자체의 환각 완화 효과를 다시 검증하는 연구
- 멀티모달 전체를 초기 주 실험으로 포함하는 연구
- 새로운 ANN 그래프 구조를 C++로 처음부터 구현하는 연구
- LLM 판사 점수를 유일한 정답 지표로 사용하는 연구

멀티모달 증거 뷰는 후속 확장으로 남긴다. 텍스트·표에서 물리 설계 기여가 먼저 입증되지 않으면 영상·이미지를 추가해도 연구의 핵심 문제가 해결되지 않는다.

---

## 3. 핵심 용어

| 용어 | 정의 |
|---|---|
| 정본 원문(canonical source) | 답변과 증거가 최종적으로 참조해야 하는 원본 문서 및 버전 |
| 증거 단위(evidence unit) | 문단, 문장, 명제, 표 행, 그래프 사실처럼 독립적으로 검색·인용 가능한 단위 |
| 증거 뷰(evidence view) | 정본 원문에서 파생되고 계보가 보존된 검색용 표현 |
| 논리 뷰 | 생성 규칙과 계보는 등록됐지만 벡터 또는 색인이 실제로 생성되지 않은 후보 뷰 |
| 물질화 뷰 | 텍스트 표현·벡터·색인 엔트리가 실제 저장된 증거 뷰 |
| 증거 격자(evidence lattice) | 문서부터 원자 사실까지의 상하위 및 교차 참조 관계 |
| 답변 효용(answer utility) | 특정 증거 집합이 최종 답변 정확도·근거성·충분성에 기여한 정도 |
| 증거 충분성 | 현재 증거만으로 정답을 지지하는 데 필요한 정보가 갖춰졌는지 여부 |
| write amplification | 원문 한 건의 변경이 몇 개의 파생 표현·벡터·색인 갱신을 유발하는지 나타내는 비용 |
| 색인 드리프트 | 삭제·수정된 원문과 벡터 색인의 상태가 불일치하는 현상 |

---

## 4. 관련 연구 동향과 신규성 경계

### 4.1 적응형 청킹

**Adaptive Chunking**은 문서별 특성에 따라 청킹 방식을 선택하고, 법률·기술·사회과학 문서에서 고정 전략보다 답변 성능이 향상될 수 있음을 보였다.

- 관련성: 고정된 하나의 청킹 규칙이 최선이 아니라는 동기를 지지한다.
- 차이: 문서별 청킹 선택이 중심이며, 질의 워크로드 아래 뷰 물질화·색인·갱신의 데이터베이스 최적화가 중심은 아니다.
- 출처: [Adaptive Chunking: Optimizing Chunking-Method Selection for RAG](https://arxiv.org/abs/2603.25333)

### 4.2 다중 해상도 검색

**UMG-RAG**는 여러 청크 해상도와 dense/sparse 검색 결과를 질의별 불확실성으로 결합하고, 미세 단위 적중 시 더 넓은 부모 문맥을 반환한다.

- 관련성: 작은 단위의 정밀성과 큰 단위의 문맥 보존 사이에 질의별 trade-off가 있음을 명시한다.
- 차이: 여러 해상도 색인이 이미 존재한다는 전제에서 온라인 결과 결합에 초점을 둔다. 무엇을 물질화할지와 갱신 비용은 핵심 문제가 아니다.
- 출처: [Uncertainty-Aware Hybrid Retrieval for Long-Document RAG](https://arxiv.org/abs/2606.13550)

**MEGRAG**는 2026년 8월 3일 공개된 매우 가까운 위험 선행연구다. passage–sentence–triple을 교차 해상도 색인으로 연결하고, 필요한 경우에만 더 넓은 문맥을 추가한다.

- 관련성: “passage–sentence–triple 다중 해상도 색인”과 “필요한 만큼 문맥 확대”는 이미 독립적인 신규 주장으로 사용할 수 없다.
- 확인된 한계: 공개 원문은 영어 factoid QA 밖의 평가와 고정된 triple-first 순서를 향후 과제로 명시한다.
- EvidenceViewDB의 차별화 후보: 전체 교차 색인을 전제로 하지 않고, 저장·지연·갱신 예산 아래 물질화할 뷰 자체를 선택하며 수명주기를 관리한다.
- 출처: [MEGRAG: Multi-Granular Evidence Graphs for Answer-Aware Multi-Hop RAG](https://arxiv.org/abs/2608.02195)

### 4.3 명제와 구조화된 증거

**PropRAG**는 트리플의 문맥 손실을 지적하고, 문맥이 풍부한 명제와 LLM-free beam search를 사용한다.

- 관련성: 명제는 EvidenceViewDB의 후보 증거 단위 중 하나다.
- 차이: PropRAG의 주 기여는 표현과 온라인 경로 검색이다. EvidenceViewDB는 명제를 포함한 여러 후보 표현 중 무엇을 저장·색인할지 결정한다.
- 출처: [PropRAG: Guiding Retrieval with Beam Search over Proposition Paths, EMNLP 2025](https://aclanthology.org/2025.emnlp-main.317/)

### 4.4 충분성 판단과 간결한 증거

**S2G-RAG**는 검색을 더 수행해야 하는지 판단하고, 검색된 문서에서 관련 문장만 추출해 compact Evidence Context를 유지한다.

- 관련성: “많은 문맥”보다 “충분한 문맥”이 중요하다는 동기를 지지한다.
- 차이: 검색 후 문장 메모리 관리가 중심이며, 저장 계층의 선택적 물질화나 증분 유지관리는 다루지 않는다.
- 출처: [S2G-RAG: Structured Sufficiency and Gap Judging for Iterative Retrieval-Augmented QA, ACL 2026](https://aclanthology.org/2026.acl-long.1185/)

### 4.5 검색 지표와 최종 답변 효용

**eRAG**는 전통적인 문서 관련성 라벨과 RAG의 다운스트림 성능 사이 상관이 낮을 수 있음을 보이고, 각 검색 문서로 생성된 결과의 실제 과제 성능을 문서 효용 라벨로 사용한다.

- 관련성: EvidenceViewDB가 단순 Recall 대신 답변 효용을 목적함수로 사용하는 근거다.
- 차이: eRAG는 검색 평가 방법이며, 답변 효용을 데이터베이스 물리 설계와 증분 유지관리의 목적함수로 사용하지 않는다.
- 출처: [Evaluating Retrieval Quality in Retrieval-Augmented Generation, SIGIR 2024](https://arxiv.org/abs/2404.13781)

**ANN Search: Recall What Matters**는 ANN의 Recall@k가 실제 검색 결과 품질과 다운스트림 RAG 효용을 과도하게 비관할 수 있으며, 큰 Recall 하락에도 답변 지표가 안정적인 조건이 있음을 보고한다.

- 관련성: EvidenceViewDB가 “Recall을 높이면 답변도 반드시 좋아진다”는 가정을 사용하면 안 된다는 직접적인 경고다.
- 차이: 해당 연구는 ANN 결과 거리 품질을 평가하는 지표가 중심이다. 어떤 증거 표현과 색인을 물질화할지 결정하는 저장 설계는 다루지 않는다.
- 출처: [ANN Search: Recall What Matters](https://arxiv.org/abs/2606.04522)

### 4.6 벡터 데이터베이스 자동 튜닝

**VDTuner**는 Milvus의 색인 유형과 시스템·색인 파라미터를 다목적 Bayesian optimization으로 조정해 검색 속도와 Recall의 균형을 찾는다.

- 관련성: 벡터 데이터베이스 물리 설정을 워크로드에 맞게 자동 선택할 수 있음을 보인다.
- 차이: 주 목적은 검색 속도와 Recall이며, 후보 증거 뷰의 물질화나 최종 답변 효용을 직접 최적화하지 않는다.
- 출처: [VDTuner: Automated Performance Tuning for Vector Data Management Systems, ICDE 2024](https://arxiv.org/abs/2404.10413)

### 4.7 증분 RAG 색인

**MCHRAG: Multi-Centroid Hierarchical Indexing for Efficient Incremental RAG**가 ICMR 2026에 발표됐다.

- 위험성: “incremental RAG indexing”이라는 큰 표현은 이미 점유됐다.
- 현재 확인 범위: DBLP 메타데이터와 DOI는 확인했지만, 이 문서 작성 시점에는 ACM 원문 접근이 되지 않았다.
- 필수 후속 조치: 본실험 사전 등록 전 PDF를 확보해 삽입·삭제 알고리즘, 계보 관리, 뷰 해상도, 비교 기준을 원문 수준으로 감사해야 한다.
- 출처: [DBLP: MCHRAG, ICMR 2026](https://dblp.org/rec/conf/mir/RenLZPL26.html)

### 4.8 관련 연구 비교표

| 연구 | 적응형 단위 | 다중 해상도 | 답변 효용 | 선택적 물질화 | 증분 갱신 | EvidenceViewDB와의 핵심 차이 |
|---|---:|---:|---:|---:|---:|---|
| Adaptive Chunking | O | 제한적 | 다운스트림 평가 | X | X | 문서별 청킹 선택 |
| UMG-RAG | O | O | 생성 품질 평가 | X | X | 온라인 다중 검색 결합 |
| PropRAG | 명제 중심 | 경로 구조 | QA 성능 | X | X | 명제 경로 검색 |
| S2G-RAG | 문장 메모리 | 제한적 | 충분성 판단 | X | X | 검색 후 문맥 압축 |
| MEGRAG | O | O | answer-aware | 확인 필요 | X | passage–sentence–triple 경로 검색 |
| eRAG | X | X | O | X | X | 답변 효용 기반 검색 평가 |
| VDTuner | X | X | X | 색인 유형·파라미터 | X | 속도–Recall 자동 튜닝 |
| MCHRAG | 계층형 | 제목상 계층형 | 원문 확인 필요 | 원문 확인 필요 | O | 증분 RAG 색인 위험 선행 |
| EvidenceViewDB | O | O | O | O | O | 답변 효용 기반 물리 설계와 수명주기 관리 |

표의 `확인 필요`는 차별성이 입증됐다는 의미가 아니다. 원문 미확인 위험을 그대로 표시한 것이다.

### 4.9 현재 남아 있는 연구 공백의 정확한 문장

2026-08-07까지 확인한 문헌 범위에서 다음 문제의 공개 선행은 확인되지 않았다.

> 전문 도메인 RAG 질의 워크로드에서 후보 증거 뷰의 답변 한계효용을 추정하고, 저장공간·지연시간·최신성 제약 아래 물질화할 뷰와 벡터 색인을 공동 선택하며, 원문 변경 시 계보를 이용해 선택된 뷰를 증분 유지하는 데이터베이스 물리 설계

이 문장은 **부재의 수학적 증명이나 최초성 선언이 아니다**. 본실험 전 DBLP, ACM DL, IEEE Xplore, arXiv, ACL Anthology를 대상으로 `RAG physical design`, `evidence view materialization`, `incremental multi-granularity index`, `answer-utility vector index` 조합을 재검색해야 한다.

---

## 5. 연구 질문

### RQ1. 질의별 최적 증거 단위는 실제로 다른가?

전문 도메인 질의에서 문장, 명제, 문단, 표 행 및 부모 문맥 중 하나의 고정 표현이 모든 질의와 데이터셋을 지배하는지 확인한다.

### RQ2. 모든 증거 뷰를 저장할 필요가 있는가?

동일 저장공간 또는 동일 색인 엔트리 예산에서 선택적으로 물질화한 증거 뷰가 고정 청크 또는 전체 다중 해상도 물질화보다 높은 품질–비용 효율을 제공하는지 측정한다.

### RQ3. Recall 기반 물리 설계와 답변 효용 기반 물리 설계는 다른 결정을 내리는가?

높은 Recall을 만드는 뷰·색인 조합과 실제 정답률을 높이는 조합이 일치하는지 확인한다. 두 설계가 동일한 결정을 내린다면 EvidenceViewDB의 핵심 기여는 약해진다.

### RQ4. 최소 충분 증거 집합이 최종 답변을 개선하는가?

동일한 생성 모델과 토큰 예산에서 EvidenceViewDB가 불필요한 문맥을 줄이면서 gold support를 유지하고 정답률·근거성을 개선하는지 평가한다.

### RQ5. 증거 뷰의 계보 기반 증분 유지가 실질적인 시스템 이득을 만드는가?

삽입·수정·삭제와 임베딩 모델 버전 변경에서 전체 재색인 대비 갱신량, 최신성 지연 및 stale hit를 줄이는지 확인한다.

---

## 6. 가설과 반증 조건

아래 수치는 본실험의 확정 SESOI가 아니라 P0에서 사용할 조기 판정 기준이다. P0 분산과 클러스터 ICC를 측정한 후 본실험 사전 등록에서 다시 고정한다.

| 가설 | 예상 | 반증 또는 중단 조건 |
|---|---|---|
| H1: 질의별 최적 해상도 이질성 | 질의의 15% 이상에서 최적 뷰 유형이 달라짐 | 한 뷰가 모든 데이터셋에서 2%p 이내로 사실상 지배 |
| H2: 검색 개선 여지 | oracle evidence가 표준 검색보다 답변 정확도 5%p 이상 우수 | oracle–retrieved 차이가 3%p 미만이고 동등성 범위 내 |
| H3: 효용 기반 물질화 이득 | 동일 저장 예산에서 Recall 기반 설계보다 답변 정확도 3%p 이상 또는 정밀도 10%p 이상 개선 | 결정된 뷰 집합과 성능이 사실상 동일 |
| H4: 최소 충분 증거 | support recall 손실 2%p 이내에서 문맥 토큰과 중복 감소 | 압축이 support를 지속적으로 누락하거나 답변을 악화 |
| H5: 증분 유지 이득 | 전체 재색인 대비 재임베딩·색인 작업 50% 이상 감소 | 정확한 무효화 비용이 전체 재색인과 유사 |

결과가 “차이 없음”일 때 이를 숨기지 않는다. 특히 H1, H2, H3 중 하나라도 핵심 중단 조건을 만족하면 대규모 시스템 구현 전에 연구를 중단하거나 갱신·일관성 문제로 주제를 축소한다.

---

## 7. EvidenceViewDB 시스템 설계

### 7.1 논리 데이터 모델

```text
SourceDocument
  ├─ doc_id
  ├─ version_id
  ├─ valid_from / valid_to
  ├─ source_uri
  └─ content_hash

EvidenceUnit
  ├─ unit_id
  ├─ doc_id / version_id
  ├─ parent_unit_id
  ├─ unit_type
  │    ├─ section
  │    ├─ passage
  │    ├─ sentence
  │    ├─ proposition
  │    ├─ table_row
  │    └─ relation_fact
  ├─ source_span
  └─ unit_hash

EvidenceView
  ├─ view_id
  ├─ unit_id
  ├─ representation_type
  ├─ embedding_model / version
  ├─ index_type / parameters
  ├─ materialized
  ├─ storage_bytes
  └─ build_timestamp

ViewDependency
  ├─ parent_id
  ├─ child_id
  └─ derivation_rule

WorkloadStatistics
  ├─ query_class
  ├─ view_id or view_type
  ├─ access_frequency
  ├─ support_gain
  ├─ answer_utility_gain
  ├─ latency
  └─ maintenance_cost
```

### 7.2 증거 격자

```text
문서 버전
 └─ 섹션
     └─ 문단
         ├─ 문장
         │   └─ 명제
         ├─ 표
         │   ├─ 머리글
         │   └─ 행
         └─ 관계 사실
```

격자는 검색 결과를 생성 모델에 그대로 전달하기 위한 그래프가 아니다. 다음 세 가지 데이터 관리 기능을 위한 계보다.

1. 미세 증거가 검색됐을 때 필요한 부모 문맥을 안전하게 가져온다.
2. 원문 변경 시 무효화해야 할 파생 뷰를 찾는다.
3. 반환된 답변의 근거를 정본 원문 위치와 버전으로 역추적한다.

### 7.3 물리 설계 조언자

후보 뷰 집합을 `V`, 질의 워크로드를 `Q`, 물질화 결정을 `x_v ∈ {0,1}`로 둔다.

개념적 목적함수는 다음과 같다.

\[
\max_{x,\pi}
\sum_{q \in Q} p(q) U(q,\pi_q(x))
- \lambda_L L(q,\pi_q)
- \lambda_M M(x)
\]

제약조건:

\[
Storage(x) \le B,\quad
p95Latency(\pi) \le D,\quad
Staleness(x) \le \delta
\]

- `U`: gold evidence 포함, 최종 답변 정확도, 근거성으로 측정한 효용
- `L`: 질의 지연 및 생성 모델 입력 토큰 비용
- `M`: 재임베딩, 색인 삽입·삭제 및 재구축 비용
- `B`: 저장공간 또는 색인 엔트리 예산
- `D`: 서비스 지연시간 SLO
- `δ`: 허용되는 최신성 지연

초기 구현은 정수계획 최적해를 주장하기보다 greedy marginal-utility-per-byte와 Bayesian optimization 또는 비용 모델 기반 휴리스틱을 비교한다. 이론적 보장이 불가능하면 정직하게 제한된 비용 모델에서만 근사 성질을 제시한다.

### 7.4 온라인 질의 계획

1. 질의를 단일 사실, 표 계산, 정의+조건, 다중 홉 등으로 분류한다.
2. 물질화된 증거 뷰 중 후보 검색 경로를 선택한다.
3. 미세 단위 검색 결과에서 필요할 때만 부모 문맥을 승격한다.
4. 중복·버전 충돌을 제거한다.
5. 충분성 또는 토큰 예산을 만족할 때 검색을 종료한다.
6. 임베딩 텍스트가 아니라 정본 원문 구간을 생성 모델에 전달한다.

온라인 질의 계획이 복잡한 LLM agent에 의존하면 지연과 평가 불확실성이 커진다. 초기 시스템은 규칙·학습된 경량 비용 모델·deterministic provenance fetch를 중심으로 구현한다.

### 7.5 증분 유지관리

문서가 변경되면 다음 절차를 수행한다.

1. 문서와 단위별 content hash로 변경 범위를 탐지한다.
2. 삭제·수정된 단위와 그 하위 파생 뷰를 무효화한다.
3. 동일한 단위는 기존 벡터를 재사용한다.
4. 변경된 단위 중 현재 물질화 정책에 필요한 뷰만 재생성한다.
5. 새 색인 버전이 준비된 뒤 원자적으로 활성 버전을 전환한다.
6. 삭제 문서, orphan vector, 중복 벡터와 stale hit를 감사한다.

---

## 8. 임베딩 알고리즘의 위치

### 8.1 주 기여로 권하지 않는 이유

새 임베딩 모델 학습은 다음 부담이 크다.

- 대규모 도메인별 학습 데이터와 hard negative 구축 필요
- 여러 강한 dense/sparse/late-interaction 모델과 비교 필요
- 2×RTX 3090 환경에서 대규모 사전학습은 비현실적
- 데이터베이스 논문보다 IR 또는 NLP 모델 논문으로 보일 가능성
- 저장 구조의 효과와 임베딩 모델의 효과가 혼동됨

### 8.2 보조 실험으로 가능한 방향

P0가 통과한 뒤 다음을 부가 실험으로 검토할 수 있다.

- 부모–자식 증거 표현의 계층 정합성 regularization
- 전문 용어와 정의 문맥을 함께 보존하는 domain adapter
- 질문 유형별 embedding expert 선택
- dense/sparse/late-interaction 표현의 선택적 물질화
- Matryoshka 차원 또는 양자화 수준을 뷰별로 다르게 선택

핵심 논문 주장은 “새 임베딩이 더 좋다”가 아니라 “기존 표현들을 포함한 후보 중 무엇을 물질화해야 하는가”로 유지한다.

---

## 9. 실험 데이터 구성

### 9.1 품질 트랙

| 도메인 | 후보 데이터 | 역할 | 주의사항 |
|---|---|---|---|
| 금융 | FinQA | 표·텍스트·계산식 기반 전문 QA, 기존 하니스 재사용 | gold program과 증거 구간 매핑 검증 필요 |
| 과학 | QASPER | 논문 질문과 근거 구간 | 원문 구조 파싱 품질 확인 필요 |
| 법률 | ContractNLI 또는 근거 구간이 있는 법률 QA 1종 | 조항·정의·예외 조건 | 라이선스와 재배포 조건 재확인 |
| 일반 다중 홉 | HotpotQA 또는 MuSiQue | 전문 도메인 밖 일반화와 충분성 평가 | 전문 도메인 주 결과로 사용하지 않음 |

주 결과는 최소 두 개의 전문 도메인에서 재현되어야 한다. FinQA 하나만으로는 도메인 특수성 비판을 피하기 어렵다.

### 9.2 규모 트랙

- arxiv-for-fanns 또는 공개 arXiv 문서: 100K–1M–2.7M 단계
- 공개 Wikipedia/arXiv distractor에 품질 트랙의 정답 문서를 삽입하는 통제 실험
- YFCC-10M: 저장량·색인·갱신 처리량 실험에는 사용할 수 있으나, 텍스트 전문 QA의 답변 품질 주 결과로 사용하지 않음

규모 트랙은 품질 트랙을 대체하지 않는다. 합성 distractor 확장은 시스템 스케일을 측정하고, 실제 근거 라벨이 있는 전문 데이터는 최종 답변 효과를 측정한다.

### 9.3 현재 재사용 가능한 로컬 자산

- FinQA 및 HotpotQA RAG 하니스
- 기존 임베딩과 검색 평가 파이프라인
- arxiv-for-fanns 100K 공개 데이터
- YFCC-10M 10,000,000×192 uint8 벡터
- 2×RTX 3090에서 7–9B급 생성 모델 평가 경험
- 클러스터 bootstrap, TOST, 사전 등록 및 자동 게이트 판정 코드 경험

---

## 10. 비교군과 절제 실험

### 10.1 핵심 비교군

| Arm | 설명 |
|---|---|
| B0 FixedChunk | 고정 512-token 청크, dense embedding, 고정 Top-k |
| B1 Small-to-Big | 작은 청크를 검색하고 부모 문맥을 반환 |
| B2 Proposition | 명제 단위 색인과 검색 |
| B3 Full-MultiView | 모든 해상도를 전부 물질화하는 상한선 |
| B4 Recall-Design | Recall·지연·저장량으로 뷰와 색인을 선택 |
| B5 Utility-Design | EvidenceViewDB의 답변 효용 기반 선택적 물질화 |
| B6 Exact/Oracle | 정확 검색, gold evidence, 또는 전체 후보 물질화 상한선 |

### 10.2 반드시 고정할 조건

- 같은 원문 버전
- 같은 임베딩 모델과 차원
- 같은 생성 모델과 decoding 설정
- 같은 최종 문맥 토큰 예산
- 같은 query set과 데이터 split
- 같은 ANN 품질 또는 정확 검색 절제
- 같은 reranker 사용 여부

### 10.3 효과 분해

다음 요인을 한 번에 바꾸지 않는다.

1. 저장 단위 효과
2. 임베딩 표현 효과
3. ANN 근사 효과
4. 질의 계획 효과
5. 생성 모델의 증거 활용 효과

`exact retrieval → ANN retrieval → generation` 순으로 실험하면 검색 단위의 문제와 ANN 근사의 문제를 분리할 수 있다.

---

## 11. 평가 지표

### 11.1 증거 검색 품질

- Gold support Recall@token-budget
- Evidence Precision@token-budget
- 필요한 증거 nugget coverage
- 중복 토큰 비율
- 모순 또는 버전 충돌 비율
- 최소 충분 증거 도달률
- 반환된 정본 source span 정확도

### 11.2 최종 답변 품질

- Exact Match / token F1
- FinQA 프로그램 실행 결과 정확도
- 사실 단위 support coverage
- 지원되지 않은 주장 비율
- 올바른 인용·source-span attribution
- 충분한 증거가 없을 때의 선택적 답변 또는 abstention

### 11.3 시스템 지표

- 원문 및 파생 뷰 저장 바이트
- 벡터 수와 인덱스 크기
- 구축 시간과 peak RAM
- p50/p95/p99 검색 지연
- query throughput
- 질의당 검색 및 생성 토큰 비용
- 원문 변경당 재임베딩 수
- 색인 삽입·삭제 수
- write amplification
- freshness lag
- stale/deleted/orphan vector 반환률

### 11.4 LLM 판사의 사용 제한

기존 모델 파일럿에서 7–9B급 판사가 표현 형식에 따라 상이한 오분류율을 보였으므로, EvidenceViewDB에서도 LLM 판사를 주 지표로 사용하지 않는다.

우선순위:

1. gold evidence와 결정론적 span 매칭
2. 프로그램 실행 또는 EM/F1
3. 개체·수치·관계 단위 검증
4. 사람 이중 주석 표본
5. LLM 판사는 보조 민감도 분석

---

## 12. 통계 분석 계획

- 질의별 paired comparison
- 문서 또는 사실 단위 cluster bootstrap
- 이진 정답률: paired McNemar 또는 cluster-aware bootstrap
- 연속 지표: paired bootstrap CI
- 다중 주 비교: Holm 보정
- 무효과 주장: 사전 정의한 등가 범위의 TOST
- 질의 유형·도메인·증거 홉 수는 사전 정의한 층화 분석만 수행
- 개발 데이터로 조정한 물리 설계를 잠긴 시험 데이터에서 한 번 평가

주 분석 단위는 개별 생성 문장이 아니라 질의 또는 정본 사실 클러스터로 둔다. 동일 문서에서 파생된 여러 뷰를 독립 표본으로 취급하지 않는다.

---

## 13. P0 타당성 파일럿

### 13.1 목적

P0는 좋은 결과를 만들기 위한 축소 본실험이 아니다. 다음 네 가지 전제를 빠르게 반증하기 위한 절차다.

1. 질의별로 필요한 증거 해상도가 실제로 다른가?
2. 현재 검색에는 최종 답변을 개선할 headroom이 있는가?
3. 답변 효용 기반 물리 설계가 Recall 기반 설계와 다른 결정을 내리는가?
4. 증분 유지관리의 절감량이 시스템 연구로서 충분한가?

### 13.2 P0-A: CPU 중심 구조·검색 게이트

예상 기간: 3–5 근무일

1. FinQA와 HotpotQA/QASPER 중 500–1,000질의를 선택한다.
2. passage, sentence, proposition, table-row, parent-child 뷰를 생성한다.
3. 모든 뷰를 정본 evidence span에 매핑한다.
4. exact 또는 FAISS Flat 검색으로 ANN 효과를 제거한다.
5. 동일 토큰 예산에서 뷰별 gold support와 중복을 비교한다.
6. 문서 1%, 5%, 10% 변경 시나리오에서 무효화 범위와 재임베딩량을 계산한다.

게이트:

- G0 매핑: gold evidence의 95% 이상을 증거 격자에 매핑
- G1 이질성: 질의의 15% 이상에서 최적 뷰 유형이 다름
- G2 비지배: 한 뷰가 두 데이터셋에서 모든 품질 지표를 사실상 지배하지 않음
- G3 유지관리: 정확한 무효화를 유지하며 전체 재생성 대비 작업량 50% 이상 절감 가능

### 13.3 P0-B: 소규모 생성 모델 게이트

예상 기간: GPU가 비어 있을 때 1–2 근무일

1. B0, B3, B4, B5, B6에 동일한 생성 모델을 적용한다.
2. 개발 질의에서 물리 설계를 선택하고 holdout에서 한 번 평가한다.
3. oracle evidence와 일반 검색 사이의 답변 headroom을 측정한다.
4. Recall 기반 설계와 답변 효용 기반 설계의 선택 및 성능 차이를 측정한다.

게이트:

- G4 headroom: oracle–retrieved 답변 정확도 차이가 5%p 이상이거나 하한이 3%p 이상
- G5 결정 차이: Recall 기반과 utility 기반이 선택하는 뷰 구성이 실질적으로 다름
- G6 효용 이득: 동일 저장 예산에서 답변 정확도 3%p 이상 또는 evidence precision 10%p 이상 개선하면서 support recall 손실 2%p 이내

### 13.4 P0 종합 판정

| 판정 | 조건 | 후속 조치 |
|---|---|---|
| GO | G0–G6 핵심 게이트 통과 | 본실험 사전 등록과 시스템 구현 |
| CONDITIONAL GO | 구조 게이트 통과, 모델 효과 또는 신규성 미확정 | 데이터/비교군 보강 후 한 번만 재시험 |
| PIVOT-UPDATE | 검색 효용 이득 없음, 증분 유지 이득 큼 | freshness·consistency 중심 주제로 축소 |
| STOP | 단일 뷰 지배, headroom 없음, utility 설계 동일 | 대규모 구현 중단 |

---

## 14. 전체 실험 단계

### Phase 1. 신규성 및 데이터 감사

- MCHRAG 원문 확보와 차별성 표 작성
- 2026년 8월 이후 arXiv/DBLP 월별 재검색
- 각 데이터셋 라이선스와 증거 라벨 검증
- 질의·문서·증거 단위 split 고정

### Phase 2. P0 파일럿

- 증거 격자 생성
- 구조·검색·갱신 게이트
- 소규모 답변 효용 게이트
- GO/STOP 판정

### Phase 3. 프로토타입

- PostgreSQL/Parquet 기반 정본·메타데이터 카탈로그
- FAISS 또는 pgvector/Qdrant 기반 벡터 색인
- 물리 설계 advisor
- 최소 충분 증거 query planner
- 증분 invalidation 및 version switch

### Phase 4. 품질 본실험

- 전문 도메인 2종 이상
- 일반 다중 홉 1종
- 복수의 고정 생성 모델
- deterministic 평가와 사람 anchor

### Phase 5. 시스템 본실험

- 100K/1M/2.7M 또는 10M 규모
- 저장 예산 3수준 이상
- update ratio 1/5/10%와 burst update
- cold/warm cache
- 정확 검색과 ANN 분리
- 최소 두 개의 엔진 또는 in-process 구현+상용 엔진 검증

---

## 15. 시스템 호환성

### 15.1 현재 환경에서 가능한 부분

- P0의 증거 격자, exact retrieval, 저장량과 갱신량 평가는 CPU로 가능하다.
- 물리 설계 advisor는 Python 수준의 구현으로 시작할 수 있다.
- 기존 7–9B 모델과 두 대의 3090은 P0-B 및 제한된 본실험 생성에 충분하다.
- YFCC-10M의 192차원 uint8 원시 벡터는 규모 실험에 유리하다.

### 15.2 주의할 부분

- 10M 문서에 768차원 다중 뷰를 모두 생성하면 RAM과 저장량이 급증한다.
- 전체 다중 뷰는 작은 부분표본 또는 상한선으로만 사용하고, 선택적 물질화가 주 시스템이 되어야 한다.
- QASPER/법률 문서 파싱은 PDF 구조 복원 오류를 별도 측정해야 한다.
- PostgreSQL/pgvector만으로 모든 실험을 수행하면 엔진 특수성 비판을 받을 수 있다.
- 전문 문서의 실제 갱신 로그가 없다면 update workload가 합성이라는 한계를 명시해야 한다.

---

## 16. 학회 투고 가능성

PVLDB 2027의 관심 주제에는 embeddings/vector databases, access methods, memory/storage management, query processing and optimization, views/indexing/search가 명시돼 있다. 그러나 공식 범위 정책은 저장·확장성·효율·수명주기·질의 가능성 같은 핵심 데이터 관리 문제와 DB 문헌 연결을 요구한다.

- [PVLDB 2027 Research Track Topics](https://www.vldb.org/2027/call-for-research-track.html)
- [PVLDB 2027 Scope Policy](https://www.vldb.org/2027/submission-guidelines.html)

### 16.1 결과 수준별 현실적 목표

| 완성 수준 | 예상 투고 적합성 |
|---|---|
| 청킹 또는 reranking만 개선 | NLP/IR 워크숍 또는 응용 논문, 상위 DB에는 부족 |
| 답변 효용 기반 뷰 선택 + 두 전문 도메인 | IR/NLP 또는 EDBT 응용·실험 논문 후보 |
| 물리 설계 advisor + 증분 유지 + 1M 이상 평가 | EDBT/ICDE급 후보 |
| 강한 최적화·엔진 통합 + 10M급 + 갱신 워크로드 + 재현 패키지 | PVLDB Research 후보 |
| 광범위한 시스템 비교와 양방향 결론 | PVLDB EA&B 후보 |

### 16.2 EDBT급 최소 조건

1. 단순 청킹 비교가 아닌 명시적인 물리 설계 문제와 알고리즘
2. 전체 물질화보다 선택적 물질화가 필요한 실측 근거
3. 답변 효용 기반 설계가 Recall 기반 설계와 다른 결정을 내린다는 증거
4. 전문 도메인 두 종 이상의 품질 결과
5. 1M 이상 규모에서 저장·지연·갱신 비용 측정
6. 계보 기반 증분 유지의 정확성과 stale-hit 감사
7. 공개 코드, 데이터 생성 규칙, 잠긴 평가 split

---

## 17. 예상 기여와 활용성

### 17.1 학술 기여

- RAG 검색 단위를 데이터베이스의 논리·물리 뷰 문제로 재정의
- 검색 Recall과 답변 효용의 불일치를 물리 설계 수준에서 분석
- 다중 해상도 RAG 색인의 저장–품질–갱신 trade-off 정량화
- 정본–파생 뷰 계보를 이용한 최신성 및 재현성 평가

### 17.2 실무 활용성

- 금융·의학·법률 문서에서 불필요한 검색 문맥과 토큰 비용 감소
- 문서 수정·삭제 후 과거 증거가 계속 검색되는 문제 탐지
- 질의 종류가 달라져도 모든 표현을 무조건 저장하지 않고 워크로드에 맞게 조정
- 답변 근거를 원문 버전과 위치로 추적
- 임베딩 모델 교체 시 전체 재색인 대신 우선순위 기반 마이그레이션 가능

### 17.3 미래 확장

- 이미지의 장면–객체–영역 증거 뷰
- 비디오의 영상–클립–프레임–객체 궤적 증거 뷰
- 표·텍스트·그래프의 교차 모달 계보
- 위험 감지 서비스에서 이벤트별 증거 뷰 물질화
- 테넌트·보안 등급별 접근 가능한 증거 뷰 설계

---

## 18. 주요 위험과 대응

| 위험 | 심각도 | 대응 |
|---|---:|---|
| MEGRAG 등으로 다중 해상도 주장이 이미 점유 | 높음 | 물리 설계·선택적 물질화·수명주기로 기여 제한 |
| MCHRAG가 증분 유지 범위까지 점유할 가능성 | 높음 | PDF 원문 감사 전 연구 확정 금지 |
| 신규성이 여러 요소의 결합에만 의존 | 높음 | 각 요소의 독립적인 알고리즘·비용 모델 기여 확보 |
| 한 청크 방식이 사실상 지배 | 높음 | G1/G2 실패 시 즉시 중단 |
| 검색 개선이 답변으로 전파되지 않음 | 높음 | oracle headroom과 utility-vs-recall 게이트 선행 |
| LLM 판사 편향 | 높음 | 결정론적 지표와 사람 anchor 사용 |
| 합성 update workload 비판 | 중간 | 실제 문서 revision history 확보 또는 한계 명시 |
| 10M 다중 뷰의 메모리 부족 | 중간 | 선택적 물질화, streaming build, 저차원 규모 트랙 |
| 시스템이 Python orchestration에 그침 | 중간 | 실제 DB 카탈로그·인덱스·버전 전환 구현 |
| 전문 도메인 하나에만 효과 | 중간 | 최소 두 도메인과 일반화 데이터셋 사용 |

---

## 19. 연구 확정 체크리스트

- [x] MCHRAG의 공개 서지·초록·알고리즘 범위 감사(코퍼스 증분 색인으로 확인; 원문 PDF 재확인은 본실험 진입 시 필요했으나 P0 중단으로 보류)
- [ ] MEGRAG 코드·부록에서 저장량과 갱신 지원 여부 확인
- [x] `physical design + RAG + evidence view` 최신 문헌 재검색(Agentic Data Environments, SPIRE, MAGE-RAG, EraRAG 추가)
- [ ] FinQA gold program–evidence span 매핑률 측정
- [x] 두 번째 전문 도메인 데이터와 라이선스 확인(ContractNLI CC BY 4.0, FinQA 로컬 자산)
- [x] P0-A 프로토콜과 데이터 split 고정
- [x] P0-A CPU 게이트 실행 — `STOP_NO_PHYSICAL_GAIN`
- [ ] P0-B 모델 게이트 실행 — **P0-A 중단 규칙에 따라 실행하지 않음**
- [ ] 효과 크기와 ICC를 이용한 본실험 표본 수 산정
- [ ] 본실험 가설·SESOI·중단 조건 사전 등록
- [ ] EDBT/ICDE/PVLDB용 데이터 관리 기여 문장 재검토

---

## 20. 최종 권고

EvidenceViewDB는 이전 GraphRAG 환각 검증 주제보다 데이터베이스 연구의 통제 변수가 명확하며 현재 실험 자산과도 잘 맞는다. 특히 다음 질문은 실험과 시스템 구현으로 직접 검증할 수 있다.

> “질의별로 필요한 증거 단위가 다른 상황에서, 모든 표현을 저장하는 대신 실제 답변 효용이 높은 증거 뷰만 물질화하고 정확하게 갱신하면, 같은 저장·지연 예산으로 더 정확하고 최신인 RAG 문맥을 제공할 수 있는가?”

2026년의 관련 연구 속도가 매우 빠르며 MEGRAG와 MCHRAG가 인접 영역에 존재한다. 여기에 2026-08-07 P0-A 결과를 반영한 최종 판정은 **STOP_NO_PHYSICAL_GAIN**이다.

당초 연구 주제는 다음 두 조건을 모두 만족한 뒤 확정할 예정이었다.

1. 원문 감사에서 답변 효용 기반 선택적 물질화와 계보 기반 증분 유지라는 공백이 남아 있을 것 — **부분 충족: 공백은 좁고 결합 신규성임**
2. P0에서 질의별 뷰 이질성, 검색 headroom 및 utility 기반 설계의 추가 이득이 확인될 것 — **미충족: oracle headroom은 있으나 실현 가능한 선택 설계의 추가 이득 없음**

따라서 대규모 EvidenceViewDB 시스템 구현과 P0-B에 들어가지 않는다. 검색 효용과 분리된 대안인 **FreshEvidenceDB: 버전 일관성과 최신성을 보장하는 RAG 증거 뷰 유지관리**는 새 사전등록과 실제 revision workload를 갖춘 별도 후보로만 남긴다.

---

## 21. 핵심 참고문헌

1. de Moura Júnior et al. *Adaptive Chunking: Optimizing Chunking-Method Selection for RAG*. arXiv:2603.25333, 2026. <https://arxiv.org/abs/2603.25333>
2. Jung and Wang. *Uncertainty-Aware Hybrid Retrieval for Long-Document RAG*. arXiv:2606.13550, 2026. <https://arxiv.org/abs/2606.13550>
3. Bao et al. *MEGRAG: Multi-Granular Evidence Graphs for Answer-Aware Multi-Hop RAG*. arXiv:2608.02195, 2026. <https://arxiv.org/abs/2608.02195>
4. Wang and Han. *PropRAG: Guiding Retrieval with Beam Search over Proposition Paths*. EMNLP 2025. <https://aclanthology.org/2025.emnlp-main.317/>
5. Li et al. *S2G-RAG: Structured Sufficiency and Gap Judging for Iterative Retrieval-Augmented QA*. ACL 2026. <https://aclanthology.org/2026.acl-long.1185/>
6. Salemi and Zamani. *Evaluating Retrieval Quality in Retrieval-Augmented Generation*. SIGIR 2024. <https://arxiv.org/abs/2404.13781>
7. Dimitropoulos and Mamoulis. *ANN Search: Recall What Matters*. arXiv:2606.04522, 2026. <https://arxiv.org/abs/2606.04522>
8. Yang et al. *VDTuner: Automated Performance Tuning for Vector Data Management Systems*. ICDE 2024. <https://arxiv.org/abs/2404.10413>
9. Ren et al. *MCHRAG: Multi-Centroid Hierarchical Indexing for Efficient Incremental RAG*. ICMR 2026. <https://dblp.org/rec/conf/mir/RenLZPL26.html>
10. PVLDB 2027 Research Track and Scope Policy. <https://www.vldb.org/2027/call-for-research-track.html>, <https://www.vldb.org/2027/submission-guidelines.html>

---

## 22. 변경 기록

| 날짜 | 변경 내용 |
|---|---|
| 2026-08-07 | 최초 문서 작성. 연구 정의, 관련 연구, 신규성 경계, 시스템 설계, P0 게이트, 투고 조건 통합 |
| 2026-08-07 | 위험 선행연구·로컬 자기 중복 감사, P0-A 사전등록 및 CPU 실험 완료. G3 실패로 STOP_NO_PHYSICAL_GAIN 판정, P0-B 중단 |

---

## 23. P0-A 실행 결과

### 23.1 자동 판정

| 게이트 | 결과 |
|---|---|
| G0 데이터·정합성 | 통과 |
| G1 질의별 최적 뷰 이질성 | 통과 |
| G2 질의별 선택 가능 상한 | 통과 |
| G3 동일 예산 선택적 물질화 이득 | **실패** |
| G4 계보 기반 국소 무효화 가능성 | 통과 |

- 질의별 oracle–단일 뷰 F1: +0.0479, 95% CI [0.0333, 0.0640]
- 실현 가능한 선택 설계–고정512 F1: +0.0052, 95% CI [-0.0058, 0.0149]
- 선택 설계: 복수 뷰가 아니라 recursive 512 한 종류
- 최종 자동 판정: **STOP_NO_PHYSICAL_GAIN**

질의별 최적 단위가 다르다는 현상은 존재하지만, 개발 워크로드로 선택한 물리 설계가 holdout에서 그 차이를 활용하지 못했다. 질의별 oracle은 연구 시스템이 아니며, 이를 근거로 여러 뷰를 모두 저장하면 선택적 물질화의 저장 기여가 사라진다.

### 23.2 연결 문서

- [위험 선행연구·로컬 선행자산 감사](evidenceviewdb_p0/LITERATURE_AND_LOCAL_PRIOR_ART_AUDIT_20260807.md)
- [P0-A CPU 사전등록](evidenceviewdb_p0/P0A_CPU_PREREGISTRATION.md)
- [P0-A 최종 보고서](evidenceviewdb_p0/P0A_FINAL_REPORT_20260807.md)
- [자동 판정 보고](evidenceviewdb_p0/results_run1/AUTO_REPORT.md)
- [전체 요약 JSON](evidenceviewdb_p0/results_run1/summary.json)
- [재현 코드](evidenceviewdb_p0/run_p0a_cpu.py)
