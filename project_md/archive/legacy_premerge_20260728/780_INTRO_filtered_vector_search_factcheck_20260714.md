# 780 — Introduction 보강: Dense Vector + Scalar Metadata 결합 검색 동향 검증 (2026-07-14)

> 상태: **FACT-CHECK HISTORY** — 유효한 문헌 판정과 수정 사항은 [`000_Introduction.md`](000_Introduction.md)에 반영되었다. 특히 “기존 연구는 random mask만 사용한다”는 표현은 사용하지 않는다.

목적: Introduction에 포함할 filtered vector search 기술 동향, 병목, 관련 연구, 본 연구와의 연결을 사실 검증 후 정리한다.

---

## 1. 사실 검증 요약

사용자가 제시한 큰 방향은 **대체로 사실**이다. 다만 논문에 넣을 때 다음 표현은 수정해야 한다.

### 1.1 수정해야 할 용어: High Selectivity

원문:

> 필터링된 결과 상위 데이터의 개수가 너무 적으면(높은 선택도, High Selectivity)

수정 권장:

> 필터 조건이 매우 선택적일 때, 즉 통과 비율이 낮을 때(highly selective predicate; low pass ratio)

이유: DB 문헌에서 selectivity는 “통과 비율”로 쓰이는 경우도 있고, “선별성”이라는 자연어 의미로 쓰이는 경우도 있어 혼동된다. 본 논문에서는 수식으로 `s = |σ_p(D)| / |D|`를 정의하고, `s`가 작을수록 선택적 predicate라고 쓰는 것이 가장 안전하다.

### 1.2 Pre-filtering 설명 보정

원문 취지:

> prefilter는 필터 결과가 작으면 HNSW를 못 쓰고 brute force로 전락한다.

부분적으로 맞지만 보정이 필요하다.

정확한 표현:

> 단순 prefilter는 predicate별 부분집합에 대한 별도 vector index가 없으면, 필터 통과 집합 위에서 exact scan을 수행하거나 임시 후보 집합을 만들어야 한다. 이 방식은 작은 집합에서는 오히려 빠를 수 있지만, predicate가 많고 동적이면 index 재사용성과 운영 비용 문제가 생긴다. 반대로 필터를 HNSW 탐색 내부에 단순히 넣으면 그래프 연결성이 깨져 탐색 품질과 속도가 저하될 수 있다.

즉, prefilter의 병목은 항상 “brute force라서 느리다”가 아니라:

- 부분집합별 index 부재
- predicate 조합 폭증
- 그래프 연결성 단절
- build/storage 비용
- 동적 predicate 운영 비용

으로 정리해야 한다.

### 1.3 Post-filtering 설명

원문 취지:

> vector top-K를 먼저 뽑고 metadata 조건을 나중에 적용하면 결과가 부족하거나 recall이 떨어진다.

이는 정확하다. pgvector 공식 문서도 approximate index에서는 filtering이 index scan 후 적용되므로 조건에 맞는 결과가 부족할 수 있고, 이를 완화하기 위해 iterative scan을 제공한다고 설명한다.

### 1.4 Single-stage / in-graph filtering

원문 취지:

> 최신 연구는 single-stage hybrid search를 고안하고 있다.

대체로 맞다. ACORN, Filtered-DiskANN, Qdrant/Weaviate ACORN류, Milvus의 filtered search, Faiss IDSelector 계열이 이 흐름과 연결된다. 다만 시스템마다 구현이 다르므로 “모두 같은 방식”이라고 쓰면 안 된다.

---

## 2. 관련 연구 정리

### 2.1 Filtered vector search 알고리즘 연구

| 연구 | venue/status | 핵심 내용 | 본 연구와 연결 |
|---|---|---|---|
| Filtered-DiskANN | WWW 2023 | label/filter를 고려한 graph-based ANNS | 필터 조건이 붙은 ANN의 대표 연구 |
| ACORN | SIGMOD/PACMMOD 2024 | HNSW 기반 predicate-agnostic hybrid search, predicate subgraph traversal | in-graph filtering 최신 핵심 연구 |
| CAPS | arXiv 2023 | graph가 아닌 partition 기반 constrained ANNS | graph 외 접근법 |
| Unified Index for Range Filtered ANN | PVLDB 2025 | range filter와 ANN 통합 index | scalar/range predicate 확장 |
| FANNS survey | arXiv 2025 | vector-scalar hybrid data에서 filtered ANNS 분류 | 관련연구 구조화에 유용 |

핵심: 이 연구들은 vector+scalar filter 결합 자체를 최적화한다. 본 연구는 새 filtered ANN 알고리즘을 제안하는 것이 아니라, **실제 감시·교통 predicate에서 이 문제가 어떻게 나타나는지**를 측정하고 DB 설계 지침으로 연결한다.

### 2.2 Vector DB / RDB 통합 연구

| 연구/시스템 | 핵심 내용 | 본 연구와 연결 |
|---|---|---|
| VBASE, OSDI 2023 | vector similarity search와 relational operator를 relaxed monotonicity로 통합 | vector+relational query 통합의 대표 DB 연구 |
| pgvector 0.8+ | iterative index scan으로 overfiltering 완화 | 본 연구의 pgvector 실험과 직접 연결 |
| AlloyDB filtered vector search | optimizer가 selectivity, distribution, index availability를 보고 pre/post/inline filtering 선택 | cost-based vector query optimization 흐름 |
| Qdrant | vector index와 payload index 결합, ACORN algorithm 옵션 | payload metadata filtering 시스템 사례 |
| Weaviate | HNSW에서 sweeping/acorn filter strategy 지원 | ACORN류 실용 시스템 사례 |
| Milvus | standard filtering과 iterative filtering 제공 | filtered search 구현 사례 |

핵심: RDB/Vector DB 통합 연구는 이미 활발하다. 본 연구의 차별점은 **감시 영상의 실제 센서·시공간 predicate, 저장 단위, VLM-QA evidence layer**를 함께 다룬다는 점이다.

### 2.3 비용 기반 query routing / selectivity-aware optimization

관련 흐름:

- predicate 통과 비율 `s`를 추정한다.
- `s`가 매우 작으면 metadata index 또는 local/partial index가 유리할 수 있다.
- `s`가 크면 global vector index + postfilter 또는 iterative scan이 충분할 수 있다.
- 중간 영역에서는 recall, latency, index build/storage 비용의 trade-off가 생긴다.

이 흐름은 본 연구의 P2/P3 실험과 정확히 맞는다. 본 연구는 실제로 `global+WHERE`, `relaxed iterative scan`, `partial/local index`를 비교하고, `N* = build_cost / per-query latency saving` 형태의 hot/cold 정책을 도출했다.

### 2.4 하드웨어 가속

하드웨어 가속은 broader trend로 넣을 수 있다.

관련 예:

- Faiss는 GPU 구현을 제공한다.
- NVIDIA cuVS/CAGRA는 GPU 기반 graph vector search를 제공한다.
- VecFlow 같은 연구는 GPU에서 filtered ANNS를 직접 가속하려는 방향을 제시한다.

다만 본 연구의 핵심 contribution은 hardware acceleration이 아니다. Introduction에서는 “대규모 vector search의 또 다른 발전 방향”으로만 짧게 언급하는 것이 좋다.

---

## 3. 네 가지 기술 패러다임으로 정리

### 패러다임 1. Two-stage filtering: prefilter vs postfilter

가장 기본적인 접근은 두 단계 방식이다.

**Prefilter**는 metadata 조건으로 후보를 먼저 줄인 뒤 vector ranking을 수행한다. hard constraint에서는 정확한 결과 집합을 보장하기 쉽지만, 부분집합별 index가 없으면 exact scan이나 임시 후보 처리에 의존할 수 있고, predicate 조합이 많아지면 운영 비용이 커진다.

**Postfilter**는 global vector index로 top-K 후보를 먼저 찾고, 그 뒤 metadata 조건을 적용한다. 구현은 단순하지만, 필터 조건을 만족하는 결과가 top-K 안에 충분히 없으면 최종 결과가 부족하거나 recall이 떨어진다.

본 연구 연결:

> 522와 MEVA에서 hard/soft qrels를 나누어 prefilter와 vector-only/postfilter의 장단점을 실측한다.

### 패러다임 2. Single-stage / in-graph filtered search

최근 filtered ANN 연구는 vector search와 scalar filtering을 별도 단계로 나누지 않고, ANN 탐색 과정 안에 predicate 평가를 통합하려는 방향으로 발전하고 있다.

예:

- Filtered-DiskANN: filter-aware graph construction/search.
- ACORN: HNSW 기반 predicate subgraph traversal.
- Qdrant/Weaviate ACORN류: filterable HNSW 또는 ACORN-inspired strategy.
- Faiss IDSelector: subset search를 위한 selector 제공.

본 연구 연결:

> 본 연구의 filtered-ANN 실험은 prefilter, postfilter, single-stage 계열을 실제 센서·시공간 predicate에서 비교하고, random mask 기반 평가가 실제 predicate의 군집성을 과소평가할 수 있음을 보인다.

### 패러다임 3. Selectivity-aware / cost-based query planning

필터 조건의 선택도와 데이터 분포에 따라 최적 실행 계획은 달라진다.

- 통과 비율이 매우 낮은 predicate: local/partial index 또는 metadata-first plan이 유리할 수 있음.
- 통과 비율이 높은 predicate: global vector index와 postfilter가 충분할 수 있음.
- 중간 predicate: 질의 빈도와 index build/storage 비용에 따라 결정.

본 연구 연결:

> 본 연구는 pgvector 실험을 통해 선택적 predicate에서 global+WHERE가 recall-latency dilemma를 만들고, partial/local index가 이를 완화함을 보이며, hot/cold predicate 정책을 도출한다.

### 패러다임 4. RDB-native vector search와 hardware acceleration

벡터 전용 DB뿐 아니라 기존 RDB/OLAP 시스템에 vector search를 통합하려는 흐름도 강하다. pgvector, AlloyDB, ClickHouse/DuckDB 계열은 SQL의 WHERE 조건과 vector distance ordering을 함께 처리하려고 한다. 동시에 Faiss GPU, cuVS, VecFlow와 같은 하드웨어 가속 연구는 대규모 vector search의 latency와 throughput 문제를 낮은 수준에서 해결하려 한다.

본 연구 연결:

> 본 연구는 RDB-native 흐름에 맞춰 PostgreSQL+pgvector에서 global index, iterative scan, partial/local index를 직접 비교한다. 하드웨어 가속은 본 논문의 직접 기여는 아니지만, 향후 대규모 운영 확장 방향으로 언급할 수 있다.

---

## 4. 본 연구 Introduction에 넣을 수 있는 보강 문단

도시 감시 VLM-QA에서 검색은 단순한 semantic vector search가 아니다. 자연어 질의는 영상 장면의 의미를 담은 dense vector로 표현되지만, 실제 운영 질의는 시간, 위치, 센서, 카테고리와 같은 scalar metadata 조건을 동시에 포함한다. 따라서 시스템은 "질의와 의미적으로 가까운 장면"뿐 아니라 "특정 시간대, 특정 교차로, 특정 신호 상태를 만족하는 장면"을 함께 찾아야 한다. 이 문제는 최근 vector database와 database system 연구에서 filtered vector search 또는 vector-scalar hybrid query로 다루어지고 있다.

기본적인 결합 방식은 prefilter와 postfilter이다. Prefilter는 scalar predicate를 먼저 적용한 뒤 통과 집합에서 vector ranking을 수행하므로 hard constraint를 보존하기 쉽지만, predicate 조합이 다양하거나 부분집합별 index가 없을 경우 exact scan, 임시 후보 생성, index build/storage 비용 문제가 발생한다. Postfilter는 global vector index를 그대로 활용할 수 있어 구현이 단순하지만, top-K 후보 안에 predicate를 만족하는 항목이 충분하지 않으면 결과가 부족하거나 recall이 하락한다. 이러한 한계 때문에 최근 연구는 graph traversal 중 predicate를 평가하는 single-stage filtered search, predicate-aware graph construction, selectivity-aware query planning, RDB-native vector search, GPU 기반 가속 등으로 확장되고 있다.

그러나 기존 filtered vector search 연구는 주로 일반 embedding benchmark와 synthetic 또는 benchmark attribute filter를 중심으로 평가되어 왔다. 도시 감시 데이터에서는 시간대, 위치, 교차로, 신호, 차량 밀도 같은 predicate가 임베딩 공간에서 군집성을 가질 수 있으며, 이는 동일 선택도 random mask와 다른 recall-latency behavior를 만든다. 또한 VLM-QA에서는 검색 결과가 단순 top-K item이 아니라 모델에 전달될 evidence packet이므로, 저장 단위와 metadata 결합 방식이 답변 지원 가능성에도 영향을 줄 수 있다. 따라서 감시 VLM-QA를 지원하는 데이터베이스에서는 dense vector와 scalar metadata를 결합하는 방법을 실제 predicate, 실제 storage unit, 실제 DB 실행 방식 위에서 평가해야 한다.

본 연구는 이 관점에서 AI Hub 522 교차로 데이터를 중심으로 video frame, VLM caption, sensor/spatiotemporal metadata, human annotation qrels를 분리한 비순환 워크로드를 구축한다. 동일 질의와 정답 아래에서 vector-only, prefilter, postfilter, hybrid search를 비교하고, Flat/HNSW/IVF/IVF-PQ 및 PostgreSQL+pgvector partial/local index를 accuracy, latency, storage 관점에서 측정한다. 이를 통해 hard constraint와 soft intent에서 filter placement가 어떻게 달라져야 하는지, 실제 predicate가 random mask 평가와 어떻게 다른지, 그리고 어떤 predicate에 local index를 만들어야 하는지에 대한 설계 지침을 도출한다.

---

## 5. Introduction에 넣을 관련 연구 목록

논문 본문 관련연구/Introduction에서 최소 다음 연구는 언급하는 것이 좋다.

1. Filtered-DiskANN, WWW 2023  
   https://dl.acm.org/doi/10.1145/3543507.3583552

2. VBASE, OSDI 2023  
   https://www.usenix.org/conference/osdi23/presentation/zhang-qianxi

3. ACORN, SIGMOD/PACMMOD 2024  
   https://dl.acm.org/doi/10.1145/3654923

4. pgvector 0.8 iterative scans  
   https://www.postgresql.org/about/news/pgvector-080-released-2952/  
   https://github.com/pgvector/pgvector

5. Qdrant filtering / ACORN  
   https://qdrant.tech/documentation/search/search/  
   https://qdrant.tech/documentation/manage-data/indexing/

6. Weaviate filtering / ACORN  
   https://docs.weaviate.io/weaviate/concepts/filtering

7. Milvus filtered search  
   https://milvus.io/docs/filtered-search.md

8. AlloyDB filtered vector search  
   https://docs.cloud.google.com/alloydb/docs/ai/filtered-vector-search-overview

9. Faiss / IDSelector  
   https://github.com/facebookresearch/faiss/wiki/Setting-search-parameters-for-one-query

10. FANNS survey  
   https://arxiv.org/abs/2505.06501

11. Faiss GPU / cuVS / CAGRA trend  
   https://faiss.ai/  
   https://docs.nvidia.com/cuvs/user-guide/references

---

## 6. 본 연구와의 차별성 문장

> Existing filtered vector search studies focus on optimizing vector-scalar hybrid queries over general benchmark embeddings and attributes. In contrast, our study asks how these design choices behave in multimodal urban surveillance VLM-QA, where dense visual/text evidence must be combined with real sensor and spatiotemporal predicates. We show that real predicates induce recall-latency behavior that differs from same-selectivity random masks, and derive storage, filtering, and partial-index deployment guidelines for the evidence layer.

국문:

> 기존 filtered vector search 연구는 일반 embedding과 attribute filter를 대상으로 vector-scalar hybrid query를 최적화하는 데 초점을 둔다. 반면 본 연구는 도시 감시 VLM-QA에서 dense visual/text evidence와 실제 센서·시공간 metadata predicate가 결합될 때 저장 단위, 필터 결합 방식, 색인 구조가 어떻게 달라져야 하는지를 평가한다. 특히 실제 predicate가 동일 선택도 random mask와 다른 recall-latency behavior를 만들 수 있음을 보이고, evidence layer를 위한 저장·검색·partial index 설계 지침을 도출한다.
