# 760 — 본 연구 실험 체계 설명 Flow 정리 (2026-07-14)

목적: 본 연구를 보고서, 발표, 원고에서 일관되게 설명하기 위한 핵심 서사 구조를 정리한다.  
권장 순서: **연구 배경 → 문제 정의 → 실험 설정 → 방법론 → 실험 결과 → 결론/가이드**.

---

## 1. 전체 한 문장

본 연구는 도시 감시·교통 멀티모달 데이터에서 자연어 질의와 센서·시공간 메타데이터 조건이 함께 주어질 때, VLM-QA가 사용할 증거를 데이터베이스가 어떤 단위로 저장하고, 어떤 색인으로 구성하며, 어떤 검색 구조로 찾아야 정확도·지연시간·저장공간 측면에서 가장 효율적인지를 평가하는 연구이다.

---

## 2. 연구 배경: 기존 연구를 보며 발견한 문제

기존 연구는 크게 세 흐름으로 나뉜다.

첫째, 비디오 데이터베이스 연구는 고정 카메라 영상에서 객체 탐지, 트랙 질의, 시공간 질의처리를 효율화하는 데 강점이 있다. NoScope, BlazeIt, MIRIS, OTIF, EQUI-VOCAL 같은 연구가 이 축에 해당한다. 그러나 이들은 주로 객체·트랙·시공간 질의를 다루며, VLM-QA가 사용할 evidence를 자연어 질의와 metadata 조건으로 찾는 문제를 직접 다루지는 않는다.

둘째, filtered vector search 연구는 벡터 검색과 구조화 필터를 결합하는 알고리즘과 시스템을 다룬다. Filtered-DiskANN, VBASE, ACORN, pgvector의 iterative scan 등이 이 축에 있다. 그러나 이들은 일반적인 vector+attribute filter 문제에 가깝고, 실제 감시 영상에서 센서·시간·위치 조건이 어떻게 검색 결과와 답변 evidence에 영향을 주는지는 충분히 다루지 않는다.

셋째, 감시 영상 VLM benchmark 연구는 어떤 모델이 감시 영상을 잘 이해하는지를 평가한다. UCA/VALU, HAWK, UrBench, ForeSea 등이 이 축에 있다. 그러나 이들은 모델의 이해 능력이나 QA 성능을 평가하는 데 초점이 있고, 데이터베이스의 저장·색인·검색 구조를 통제 변수로 비교하지 않는다.

따라서 본 연구는 기존 연구들의 교차점에서 다음 빈칸을 발견했다.

> 감시·교통 멀티모달 데이터에서 VLM-QA를 지원하려면, 모델 자체만 볼 것이 아니라 DB가 어떤 증거를 어떻게 저장·색인·검색해서 모델에 전달하는지를 평가해야 한다.

---

## 3. 문제 정의: 왜 단순 벡터 검색만으로 부족한가

일반적으로는 영상, 프레임, caption을 하나의 임베딩 공간에 넣고 벡터 검색을 수행하면 충분하다고 생각할 수 있다. 그러나 도시 감시 데이터의 질의는 보통 단순 의미 검색이 아니다.

예를 들어 다음과 같은 질의가 주어진다.

> “오전 시간대에 도로변에 정차 또는 주차된 차량이 보이는 CCTV clip을 찾아라.”

이 질의에는 두 종류의 조건이 섞여 있다.

- 의미 조건: 정차/주차 차량이 보이는가
- 구조화 조건: 오전 시간대인가

벡터 검색은 의미적으로 비슷한 장면을 찾는 데 유리하지만, 시간·위치·센서 조건처럼 반드시 만족해야 하는 조건을 안정적으로 보장하지 못할 수 있다. 반대로 metadata filter를 먼저 적용하면 hard constraint에서는 유리하지만, soft intent에서는 의미적으로 관련 있는 결과를 제거할 수도 있다.

또한 초기 실험 과정에서 중요한 평가 함정도 확인되었다. filter 조건, 정답 정의, 검색 문서가 같은 라벨에서 파생되면 prefilter가 좋아 보이는 결과가 구성상 보장될 수 있다. 이를 순환성(circularity)이라고 정의했고, 본 연구는 이 문제를 피하기 위해 소스 분리 기반의 비순환 워크로드를 설계했다.

---

## 4. 연구 질문

본 연구의 핵심 질문은 다음 세 가지다.

### RQ1. 저장 단위

멀티모달 감시 데이터를 어떤 단위로 저장해야 하는가?

- clip-caption
- frame-vector
- multi-vector
- dual-index

### RQ2. 검색 구조

자연어 의미 조건과 metadata 조건을 어떤 순서로 결합해야 하는가?

- vector-only
- metadata-only
- postfilter
- prefilter
- hybrid

### RQ3. 색인 및 DB 구현

실제 DB에서 metadata 조건이 붙은 vector search를 어떻게 구현해야 하는가?

- global index + WHERE
- relaxed iterative scan
- partial/local index
- hot/cold predicate policy

---

## 5. 실험 설정: 사용 데이터셋과 역할

본 연구는 하나의 데이터셋에 모든 주장을 의존하지 않고, 각 데이터셋에 명확한 역할을 부여한다.

### AI Hub 522 교차로 신호체계 데이터

주력 데이터셋이다. 센서 조건, 영상, 사람 주석을 서로 다른 소스로 분리할 수 있어 본 연구의 핵심 tri-source workload로 사용한다.

- predicate: 센서 CSV 기반 시간, 신호, 밀도 등
- document: 프레임 픽셀만 본 VLM caption
- relevance: 사람 주석 기반 장면 사건

### MEVA

해외 CCTV 기반 외부 검증 데이터셋이다. 522에서 얻은 hard constraint, caption blind spot, prefilter 효과가 국내 데이터에만 의존하지 않는지 확인한다.

### MIRIS

교통 영상 기반 DB 구현 검증 데이터셋이다. partial/local index와 hot/cold predicate 정책이 독립적인 교통 영상 데이터에서도 유효한지 확인한다.

### Sinnaedoro / 522 visual frame corpus

13만~14만 개 규모의 frame vector corpus로, filtered ANN과 index latency/recall/storage 실험에 사용한다.

### VRU / 다각도 CCTV

검색 결과가 VLM-QA 답변 품질에 어떻게 연결되는지, 그리고 좋은 evidence selection이 왜 중요한지 확인하는 보조 실험에 사용한다.

---

## 6. 워크로드 Flow

본 연구의 실험은 다음 흐름으로 실행된다.

```text
1. 원천 데이터 확보
   - CCTV 영상, 프레임, 센서 CSV, 사람 주석, 공개 benchmark 데이터

2. canonical schema 정규화
   - clips
   - frames
   - documents/captions
   - metadata
   - queries
   - qrels

3. 비순환 소스 분리
   - predicate = 센서/시공간 기록
   - document = 픽셀만 본 VLM caption
   - relevance = 사람 주석

4. 임베딩 및 색인 생성
   - text embedding
   - visual/frame embedding
   - BM25
   - HNSW/IVF/Flat/PQ
   - pgvector index

5. 검색 전략 실행
   - vector-only
   - metadata-only
   - prefilter
   - postfilter
   - hybrid
   - partial/local index

6. 평가
   - strict qrels
   - semantic qrels
   - nDCG@10, Recall@10, MRR
   - latency
   - storage MB
   - answer-level propagation
```

---

## 7. 방법론: 선택지를 변수화한 방식

본 연구는 특정 방법 하나를 제안하는 것이 아니라, 설계 선택지를 변수화해서 비교한다.

### 변수 1. 저장 단위

| 저장 단위 | 의미 |
|---|---|
| clip-caption | clip 하나를 VLM caption 하나로 표현 |
| frame-vector | 프레임 단위 시각 임베딩 저장 |
| multi-vector | 하나의 clip에 여러 frame vector 저장 |
| dual-index | caption index와 visual index를 함께 사용 |

### 변수 2. 검색 방식

| 검색 방식 | 의미 |
|---|---|
| metadata-only | 구조화 조건만 사용 |
| BM25 | 키워드 기반 검색 |
| dense vector | 임베딩 기반 의미 검색 |
| postfilter | vector 검색 후 metadata 조건 적용 |
| prefilter | metadata 조건으로 먼저 후보 제한 후 vector 검색 |
| hybrid | sparse, dense, metadata 결합 |

### 변수 3. 색인 구조

| 색인 | 의미 |
|---|---|
| Flat | 정확하지만 선형 탐색 |
| HNSW | 빠른 ANN 검색 |
| IVF | coarse partition 기반 ANN |
| IVF-PQ | 압축형 ANN |
| pgvector global index | 관계형 DB 내 전역 vector index |
| partial/local index | 조건별 부분집합 index |

### 변수 4. 임베딩 모델

본 연구는 모델을 새로 학습하지 않고 고정 모델을 사용한다.

- caption/text embedding: bge-m3, e5-large-v2 등
- visual/text embedding: CLIP, SigLIP
- caption 생성: Qwen2.5-VL
- 답변 평가: Qwen, Llama, InternVL, Idefics 등 고정 모델

추가 확장으로는 단일 통합 임베딩 baseline을 넣어, vector-only 성능이 embedding model 선택에 얼마나 의존하는지 확인할 수 있다.

---

## 8. 평가 방식

평가는 두 종류의 정답 기준을 사용한다.

### strict qrels

의미 조건과 metadata 조건을 모두 만족하는 결과만 정답으로 본다.  
예: 오전 조건이 붙은 질의라면, 실제로 오전에 촬영된 관련 장면만 정답이다.

### semantic qrels

의미 조건을 만족하면 metadata 조건과 무관하게 관련 결과로 본다.  
예: 오후에 촬영된 주차 차량 장면도 의미적으로는 관련이 있을 수 있다.

이 두 평가를 함께 사용하기 때문에, 본 연구는 다음을 구분할 수 있다.

- hard constraint에서는 prefilter가 좋은가
- soft intent에서는 prefilter가 관련 결과를 제거하는가
- metadata 조건이 정답 정의와 얼마나 결합되어 있는가

---

## 9. 실험 결과의 핵심 흐름

### 결과 1. 순환 워크로드는 위험하다

초기 워크로드에서는 filter, qrels, document가 같은 라벨에서 파생되어 prefilter가 지나치게 좋아 보였다. 수리 후 완벽 지표가 붕괴했다.

통찰:

> 멀티모달 검색 평가에서는 데이터셋 구축 방식 자체를 감사해야 한다.

### 결과 2. hard constraint에서는 prefilter가 유리하다

시간, 위치, 센서 조건처럼 반드시 만족해야 하는 조건에서는 metadata filter를 먼저 적용하는 것이 효과적이다. 522와 MEVA에서 이 결론이 재현되었다.

통찰:

> 조건이 진짜 제약이라면, 의미 검색 전에 DB가 후보 공간을 제한하는 것이 합리적이다.

### 결과 3. soft intent에서는 prefilter를 조심해야 한다

metadata 조건이 의미 조건과 약하게 결합되어 있거나, 의미적으로 관련 있는 결과가 metadata 조건 밖에도 존재할 수 있으면 prefilter가 관련 결과를 제거할 수 있다.

통찰:

> prefilter는 항상 좋은 것이 아니라, 조건의 성격과 결합도에 따라 선택해야 한다.

### 결과 4. 저장 단위의 최적해는 데이터셋마다 다르다

522에서는 clip-caption이 Pareto 효율적이었다. MEVA에서는 frame-vector가 더 유리했다.

통찰:

> caption이 질의 의미를 잘 담으면 clip-caption이 효율적이고, caption이 세밀한 시각 사건을 놓치면 frame-vector가 유리하다.

### 결과 5. 실제 predicate는 random mask와 다르다

실제 시간·위치·센서 predicate는 임베딩 공간에서 군집을 만들 수 있다. 동일 선택도 random mask로 filtered ANN을 평가하면 recall을 과대평가할 수 있다.

통찰:

> filtered vector search는 실제 predicate로 평가해야 한다.

### 결과 6. partial/local index는 선택적 조건에서 유리하다

pgvector 실험에서 global index + WHERE 방식은 선택적 predicate에서 recall 또는 latency 문제가 발생했다. partial/local index는 좁은 조건에서 안정적인 recall과 낮은 latency를 보였다.

통찰:

> 선택적 predicate에는 local index가 필요하고, 넓은 predicate에는 global index가 충분하다.

### 결과 7. 검색 성능이 답변 성능으로 항상 직결되지는 않는다

좋은 evidence는 답변 품질을 높일 수 있지만, index 차이가 항상 VLM-QA 답변 차이로 바로 이어지지는 않았다. corpus scale, VLM perception, answer bias가 중간 경계로 작동한다.

통찰:

> DB evidence layer는 중요하지만, 답변 품질로의 전파는 모델 능력과 과제 설계에 의해 제한된다.

---

## 10. 최종 설계 가이드

본 연구가 제시하는 실용적 가이드는 다음과 같다.

| 상황 | 권장 설계 |
|---|---|
| metadata가 반드시 만족해야 하는 조건 | prefilter |
| 의미적으로 넓은 soft intent 질의 | vector-only 또는 cautious filtering |
| caption이 질의 의미를 잘 담는 데이터 | clip-caption |
| caption이 세밀한 시각 사건을 놓치는 데이터 | frame-vector |
| 선택도가 낮은 시간·위치 조건 | partial/local index |
| 선택도가 넓은 조건 | global index + postfilter |
| 실제 운영 predicate 평가 | random mask가 아니라 real predicate 사용 |
| VLM-QA 답변 평가 | evidence retrieval과 answer generation 경계를 분리 |

---

## 11. 보고용 흐름 문장

본 연구는 기존 비디오 DB 연구, filtered vector search 연구, 감시 VLM benchmark 연구를 검토하는 과정에서, VLM-QA를 위한 evidence layer의 저장·색인·검색 구조가 독립적인 DB 문제로 충분히 다루어지지 않았다는 공백을 발견했다. 이를 확인하기 위해 본 연구는 도시 감시 데이터에서 자연어 의미 조건과 센서·시공간 metadata 조건이 함께 주어지는 검색 워크로드를 설계했다. 특히 filter, document, relevance가 같은 라벨에서 파생될 때 발생하는 순환 평가 문제를 확인하고, 이를 피하기 위해 센서 기록, VLM caption, 사람 주석을 분리한 비순환 tri-source 워크로드를 구축했다.

실험에서는 AI Hub 522 교차로 데이터를 주력으로 사용하고, MEVA를 해외 CCTV 외부 검증, MIRIS를 DB index 정책 교차검증 데이터로 활용했다. 모든 데이터는 clip, frame, caption, metadata, query, qrels로 구성된 canonical schema로 정리되며, strict qrels와 semantic qrels를 함께 사용해 hard constraint와 soft intent를 구분했다.

방법론적으로는 저장 단위, 검색 방식, 색인 구조, DB 구현 방식을 각각 변수화했다. 저장 단위는 clip-caption, frame-vector, multi-vector, dual-index를 비교했고, 검색 방식은 vector-only, metadata-only, postfilter, prefilter, hybrid를 비교했다. 색인 구조는 Flat, HNSW, IVF, IVF-PQ와 pgvector 기반 global/partial index를 비교했으며, 정확도뿐 아니라 지연시간과 저장공간까지 함께 측정했다.

결과적으로 본 연구는 hard metadata constraint에서는 prefilter가 유리하지만, soft intent에서는 filtering이 관련 결과를 제거할 수 있음을 보였다. 또한 최적 저장 단위는 데이터셋과 caption 품질에 따라 달라지며, 실제 센서·시공간 predicate는 random mask와 다르게 동작하므로 filtered vector search는 real predicate로 평가해야 함을 확인했다. 관계형 DB 구현에서는 선택적 predicate에 대해 partial/local index가 recall과 latency를 안정화하며, 이를 바탕으로 hot/cold predicate 정책을 도출했다.

따라서 본 연구의 결론은 단순히 어떤 embedding model이나 vector search가 좋다는 것이 아니다. 멀티모달 감시 데이터에서 VLM-QA를 안정적으로 지원하려면, evidence를 어떤 단위로 저장하고, metadata 조건을 언제 적용하며, 어떤 index를 만들고, 어떤 조건에서 local index를 운영할지까지 함께 설계해야 한다.

---

## 12. 30초 요약

본 연구는 새 VLM 모델을 만드는 것이 아니라, 멀티모달 감시 데이터에서 VLM-QA가 사용할 증거를 DB가 어떻게 저장·색인·검색해야 하는지 평가하는 연구이다. 기존 연구들은 비디오 질의처리, filtered vector search, 감시 VLM benchmark를 각각 다루었지만, 자연어 질의와 센서·시공간 metadata가 결합된 VLM-QA evidence layer의 DB 설계 문제는 충분히 다루지 않았다. 본 연구는 AI Hub 522를 중심으로 비순환 tri-source 워크로드를 구축하고, MEVA와 MIRIS로 외적 타당성을 보강했다. 실험 결과 hard constraint에서는 prefilter가 유리하고, 저장 단위는 데이터셋과 caption 품질에 따라 달라지며, 선택적인 predicate에서는 partial/local index가 안정적이라는 설계 가이드를 도출했다.

