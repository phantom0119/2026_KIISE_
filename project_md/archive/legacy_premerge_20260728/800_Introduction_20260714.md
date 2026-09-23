# 800 — Introduction (2026-07-14)

> 상태: **SUPERSEDED** — 최신 Motivation·Research Gap·RQ·논문 삽입용 산문은 [`000_Introduction.md`](000_Introduction.md)를 사용한다.

---

## 1. 서론 (Introduction)

### 1.1 기술 동향: 멀티모달 감시 데이터와 VLM-QA

도시 교통 및 방범 감시 환경은 더 이상 단일 채널의 영상 스트림만을 생산하지 않는다. 실시간으로 수집되는 CCTV 프레임과 비디오 클립 외에도, 사고 발생 정보, 차량 및 보행자의 주석, 신호등 상태, 시간대, 위치 정보, 그리고 실시간 교통량과 같은 이기종의 센서 및 시공간 메타데이터(spatiotemporal metadata)가 함께 축적되고 있다. 최근 Vision-Language Model(VLM) 및 Large Language Model(LLM)의 급격한 발전은 이러한 대규모 멀티모달 데이터에 대해 자연어로 질의하고, 질의와 관련된 영상 증거를 기반으로 근거 있는 답변을 생성하는 VLM-QA(Vision-Language Model Question Answering) 또는 멀티모달 RAG(Retrieval-Augmented Generation) 시스템의 실현 가능성을 열어주었다. 

동시에 벡터 데이터베이스(Vector Database)와 필터링된 벡터 검색(Filtered Vector Search)은 자연어의 의미적 맥락을 포착하는 Dense Vector 검색과 전통적인 구조화 메타데이터 필터링 조건을 결합하기 위한 핵심 인프라 기술로 부상하고 있다. 예를 들어, 관계형 DB 내에 벡터 검색을 통합하는 VBASE (Zhang et al., 2023)나 그래프 인덱스 상에서 구조화 조건을 최적화하는 ACORN (Patel et al., 2024) 등은 벡터 유사도 검색과 관계형 조건 검색(relational predicate)을 단일 시스템으로 융합하는 패러다임을 제시하고 있다. 아울러 UCA/VALU, HAWK, UrBench 등 최신 도시 감시 VLM 벤치마크 연구들은 감시 도메인 내 시각적 이해와 추론이 여전히 고난도의 도전적 과제임을 실증하고 있다.

---

### 1.2 문제 관찰 및 정의: VLM-QA Evidence Layer의 한계

그러나 실제 대규모 멀티모달 감시 환경을 지원하는 VLM-QA 시스템에서 생성 모델이 모든 원본 영상을 직접 스캔하거나 추론하는 것은 하드웨어 리소스와 지연 시간(latency) 관점에서 불가능에 가깝다. 따라서 실용적인 시스템에서는 그림 1(생략)과 같이 데이터베이스가 입력 질의에 대응하는 클립, 프레임, 캡션, 그리고 센서 레코드를 사전에 검색하여 최적의 '증거 패킷(evidence packet)'을 구성하고, VLM/LLM은 이 제한된 크기의 증거만을 입력받아 최종 답변을 추론하는 2단계(2-stage) 구조를 취한다. 결과적으로 최종 답변의 품질은 생성 모델의 추론 능력뿐 아니라, 이전 단계의 데이터베이스 계층(Database Evidence Layer)에서 얼마나 정확하고 풍부한 증거를 누락 없이 검색하여 전달하는지에 크게 의존하게 된다.

감시 데이터에 대한 사용자의 자연어 질의는 단순한 시각적 의미 검색에 머무르지 않고, 특정 시공간 제약 조건을 동반한다. 예를 들어, *"오전 출근 시간대에 교차로 인근 도로변에 불법 주차된 적색 차량이 포함된 CCTV 클립을 찾아라"*라는 질의에는 "불법 주차된 적색 차량"이라는 의미적 검색 조건과 "오전 출근 시간대", "교차로 인근"이라는 구조화된 메타데이터 필터 조건이 결합되어 있다.

이와 같은 벡터 유사도와 스칼라 메타데이터의 하이브리드 검색을 처리하기 위해 전통적으로 pre-filtering과 post-filtering 방식이 사용되어 왔으나, 감시 RAG 환경에서는 다음과 같은 명확한 한계를 노출한다.

1. **Pre-filtering의 한계 (Selective Predicate & Graph Disconnection)**
   Pre-filtering은 스칼라 메타데이터 조건을 만족하는 후보 데이터셋을 먼저 선별한 후 벡터 유사도 검색을 수행하므로, 하드 제약 조건(hard constraint)을 완벽히 보존할 수 있다. 그러나 스칼라 필터 조건의 선택도(selectivity) $s = |\sigma_p(D)| / |D|$가 극도로 낮아 특정 교차로 혹은 좁은 시간 범위만 통과시키는 Highly Selective Predicate(low pass ratio) 상황이 발생할 경우 두 가지 병목에 부딪힌다. 
   - 첫째, 각 속성 조합이나 동적 쿼리에 대해 사전에 구축된 전용 벡터 인덱스가 없다면, 필터를 통과한 임의의 부분집합 위에서 전체 스캔(exact scan)을 수행하거나 메모리 상에 임시 후보 집합을 생성하여 유사도를 계산해야 하므로 연산 비용이 폭증한다.
   - 둘째, 탐색 속도를 높이기 위해 인라인 그래프 기반 검색(in-graph filtering)을 수행할 경우, HNSW와 같은 근접 그래프(proximity graph) 상에서 필터 조건을 통과하지 못하는 노드들이 탐색 경로 상의 연결점들을 단절시켜 그래프 연결성(graph connectivity)이 깨지게 된다. 이는 탐색 알고리즘이 그래프 내에서 조기에 고립되는 현상을 초래하여 검색 품질(Recall)이 저하되는 원인이 된다 (Gollapudi et al., 2023; Lin et al., 2025).

2. **Post-filtering의 한계 (Recall Degradation)**
   Post-filtering은 데이터베이스 내의 전체 벡터에 대해 글로벌 벡터 인덱스(global vector index)를 활용해 유사도 상위 $K$개의 후보를 먼저 추출하고, 이후 스칼라 필터 조건을 사후 적용한다. 이는 기존 벡터 인덱스를 재사용할 수 있어 구현이 단순하고 인덱스 빌드 비용이 추가로 들지 않는 장점이 있다. 그러나 스칼라 필터 조건이 Highly Selective Predicate인 경우, 글로벌 $K$개의 벡터 중에 해당 조건을 만족하는 레코드가 전혀 포함되지 않거나 극소수만 남게 되어, 최종 반환 데이터가 부족해지거나 검색의 재현율(Recall)이 심각하게 하락하게 된다. 
   
   이러한 현상을 방지하기 위해 `pgvector` 등의 최근 RDB 시스템은 동적 반복 스캔(iterative index scan)을 통해 조건에 맞는 $K$개의 결과가 채워질 때까지 추가 스캔을 수행하는 기능을 지원하고 있으나 (pgvector, 2024), 이 또한 쿼리 탐색 경로가 길어짐에 따라 시스템 지연 시간(latency)을 예측하기 어렵게 만드는 한계를 지닌다.

---

### 1.3 평가상의 함정: 데이터셋 구축에서의 순환성 (Circularity)

기존 멀티모달 RAG 또는 감시 비디오 검색 시스템 평가 연구들에서는 흔히 인식하지 못한 구조적 함정이 존재한다. 그것은 바로 평가 벤치마크 데이터셋 구축 시 발생하는 **순환성(circularity)** 문제이다. 대다수의 벤치마크는 단일 어노테이션 소스(human annotation label)로부터 질의(query), 메타데이터 필터(metadata filter), 정답셋(relevance ground truth/qrels), 그리고 검색 대상 문서(document)를 동시에 도출한다. 

예를 들어, 라벨러가 영상 내 특정 영역을 보고 *"10시 15분 교차로 A에서 적색 차량이 신호를 위반했다"*라는 어노테이션을 작성했다면, 이 문장을 가공해 검색 대상 document(캡션), 스칼라 필터 조건(교차로 A, 오전 시간대), 그리고 정답 레이블을 동시에 생성하게 된다. 이러한 구조에서는 필터 통과 집합 내에 정답이 무조건 존재하도록 설정되어 있기 때문에, pre-filter 방식의 검색 성능이 실제 아키텍처의 우수성 덕분이 아니라 **평가 데이터셋 구성의 순환성으로 인해 인위적으로 과장**되는 결과를 낳는다. 또한 검색 대상 텍스트 문서가 메타데이터 라벨을 그대로 재진술(re-statement)하고 있어, 실질적인 비주얼 이해 없이 키워드 매칭(BM25)이나 단순 Dense Retrieval만으로도 왜곡되게 높은 평가 점수를 얻는 문제가 생긴다.

본 연구는 이러한 순환성을 평가 신뢰성을 저해하는 치명적인 위험 요인으로 정의한다. 이를 방지하기 위해, 필터 조건(predicate), 검색 문서(document), 그리고 적합도 평가 기준(relevance)이 서로 독립적인 세 가지 소스에서 유도되어 상호 작용하도록 만드는 새로운 비순환 평가 프로토콜의 수립이 시급하다.

---

### 1.4 기존 연구와의 관계 및 차별성

본 연구와 연관된 기존 연구는 크게 세 가지 범주로 분류할 수 있으나, 본 연구가 집중하는 교차 영역을 종합적으로 다루지는 못했다.

*   **비디오 데이터베이스 연구 (Video Databases):** 기존 비디오 DBMS 연구들은 주로 CCTV와 같은 고정 카메라 환경에서 객체 탐지(object detection), 다중 객체 추적(multi-object tracking), 시공간 쿼리 처리 최적화에 중점을 두어 왔다. 그러나 이들 시스템은 주로 객체 감지기나 트래커의 정적인 메타데이터 출력만을 인덱싱할 뿐, 임의의 자연어 질의와 실시간 센서 메타데이터가 역동적으로 결합하는 VLM-QA 용 데이터베이스 근거 계층(evidence layer)의 설계 구조를 체계적으로 평가하고 비교하지는 않았다.
*   **필터링된 벡터 검색 연구 (Filtered Vector Search):** 최근 데이터베이스 및 검색 알고리즘 학계에서는 벡터 데이터에 대한 하이브리드 스칼라 쿼리 속도를 최적화하기 위해 Filtered-DiskANN (Gollapudi et al., 2023), ACORN (Patel et al., 2024), UNIFY (Liang et al., 2024), 그리고 다양한 하이브리드 인덱싱 서베이 (Lin et al., 2025) 연구들이 활발히 진행되고 있다. 그러나 이러한 연구들은 주로 일반적인 벤치마크 임베딩이나 합성된(synthetic) 임의 마스킹 필터(random mask filter) 환경에서 최적화 성능을 측정한다. 실제 교통 감시 센서 메타데이터가 가지는 고유의 상관성(correlation), 시공간적 군집성(clustering), 그리고 질의 선택도가 임베딩 공간 및 인덱스 탐색 거동에 미치는 실질적인 영향에 대한 심층적 분석은 부족하다.
*   **멀티모달 감시 벤치마크 연구 (Multimodal Surveillance Benchmarks):** UCA/VALU 등 최근의 감시 비디오 벤치마크들은 다양한 오픈 VLM 및 LLM이 감시 비디오의 복잡한 이벤트를 얼마나 잘 이해하고 추론하는지 평가하는 데 치중되어 있다. 그러나 이들은 대개 모델의 매개변수 크기나 아키텍처 학습 방식을 변수로 두며, 검색 대상 데이터의 저장 방식(storage unit), 색인 구조(index structure), RDBMS 쿼리 계획 등 **데이터베이스 아키텍처 설계 변수들을 통제 변수로 두고 정량적으로 분석**하지는 않는다.

따라서 본 연구는 새로운 VLM/LLM 아키텍처를 학습하거나 별도의 벡터 유사도 알고리즘을 설계하여 기존의 연구들과 경쟁하는 것을 목표로 하지 않는다. 대신, 기존 모델 및 인프라를 고정한 상태에서 **VLM-QA evidence retrieval을 위한 데이터베이스 계층의 설계 공간(Design Space)을 최초로 체계화하고 실증하는 브릿지 연구**로서 고유한 가치를 지닌다.

---

### 1.5 본 연구의 접근법 및 실험 구성

이러한 문제들을 해결하기 위해, 본 연구는 국내 최대 교통 데이터 소스인 AI Hub 522 교차로 신호체계 데이터를 중심으로, 실제 물리 루프 디텍터 및 신호 제어기 등의 메타데이터 기록을 **Predicate 소스(센서 채널)**로, 비디오 프레임 픽셀 정보만을 입력받아 VLM이 독자 생성한 캡션을 **Document 소스(텍스트 채널)**로, 인간 전문가의 수동 레이블링 정보를 **Relevance 소스(인간 정답 채널)**로 각각 완벽히 분리하여 데이터 생성 간의 순환성을 원천 차단한 **비순환 Tri-Source 워크로드**를 구축한다. 추가적으로 해외 CCTV 데이터셋인 MEVA를 활용하여 지리적 환경에 따른 검색 구조의 외적 타당성(external validity)을 검증하고, MIRIS 엔진 및 DB 인덱스 배치 시뮬레이션을 통해 교차 검증을 병행한다.

본 연구의 실증 실험은 동일한 테스트 질의 및 정답 데이터셋 아래에서 다음의 네 가지 핵심 데이터베이스 설계 차원을 통제 변수로 두어 전방위적으로 비교 분석한다.
*   **저장 단위 (Storage Units):** 클립 단위 캡션 저장(clip-caption), 개별 프레임 임베딩 벡터 저장(frame-vector), 멀티 벡터 구조(multi-vector), 그리고 이중 인덱스(dual-index) 저장 아키텍처의 트레이드오프 분석.
*   **검색 및 필터링 전략 (Retrieval & Filtering Strategies):** 단순 메타데이터 매칭(metadata-only), 키워드 검색(BM25), 밀집 벡터 검색(dense vector), postfilter, prefilter 및 하이브리드(hybrid) 기법의 효율성 평가.
*   **색인 구조 (Index Structures):** Flat, HNSW, IVF, IVF-PQ 등 대표적 근사 벡터 검색(ANNS) 인덱스 환경 하에서의 정확도(Recall, nDCG, MRR) 및 시스템 자원(지연 시간, 저장 공간, 인덱스 빌드 비용) 측정.
*   **관계형 데이터베이스 구현체 (Relational DB Implementations):** 대중적인 오픈소스 시스템인 PostgreSQL+pgvector 환경에서 Global Index + WHERE 조건문, Iterative index scan, 그리고 부분 인덱스(partial/local index) 적용 방식을 비교 실험하여 실무적인 가이드를 도출한다.

---

### 1.6 본 연구의 핵심 기여 (Contributions)

본 연구의 학술적 및 기술적 기여는 다음과 같이 요약할 수 있다.

1.  **비순환 멀티모달 감시 검색 워크로드 프로토콜 제안:** 필터 조건(Predicate), 타겟 문서(Document), 적합성 라벨(Relevance)이 각기 다른 소스로부터 유도되도록 분리한 Tri-source 워크로드를 제안하여 데이터 구축 상의 순환성으로 인한 성능 왜곡 함정을 원천 차단한다. 또한, strict/semantic 이중 qrels 및 기계 감사(machine audit) 절차를 통해 평가의 내적 타당성을 극대화한다.
2.  **VLM-QA Evidence Layer의 저장·검색 설계 공간 규명:** 고정된 생성 모델 아키텍처 하에서 비디오 저장 단위와 메타데이터 필터 결합 방식이 쿼리 유형 및 데이터의 캡션 품질에 따라 미치는 영향을 정량적으로 비교 분석하고, 최적의 조합을 선택하기 위한 구간별(regime-specific) 설계 가이드라인을 제공한다.
3.  **실제 감시 Predicate 기반 Filtered ANNS 분석:** 가상의 무작위 마스킹(random mask) 조건과 달리, 실제 시공간 및 물리 센서 predicate 하에서는 필터 통과 집합이 임베딩 공간에서 뚜렷한 군집성(clustering)을 형성함을 실증한다. 이를 통해 기존 벤치마크 평가 방식이 실제 운영 환경에서의 recall 및 latency를 과대평가할 수 있음을 규명한다.
4.  **관계형 DB에서의 Partial/Local 인덱스 기반 최적화 및 핫/콜드 운영 정책 수립:** PostgreSQL+pgvector 환경 하에서 Highly Selective Predicate 쿼리에 대해 global index + WHERE 방식이 겪는 성능 저하를 극복하기 위한 부분 인덱스(partial/local index) 적용 효과를 실측한다. 더 나아가 인덱스 빌드 비용과 쿼리당 지연 시간 단축 효과 간의 관계를 바탕으로 $N^* = \text{build\_cost} / \text{latency\_saving}$ 비율을 기반으로 하는 최적의 hot/cold predicate 인덱스 구축 운영 정책을 제시한다.
5.  **검색 결과와 VLM-QA 답변 품질 간의 연계 전파 분석:** 검색 품질 지표(nDCG, Recall 등)의 차이가 최종 VLM-QA의 텍스트 답변 정확도로 직접 전파되는 경계를 분석한다. 이 과정에서 코퍼스 규모(corpus scale), VLM 인지 오류(perception limits), 답변 편향(answer bias)이 데이터베이스 검색 구조와 최종 답변 품질 사이에서 차단막(buffer) 역할을 수행하는 양상을 정량적으로 밝힌다.

---

## References

*   Gollapudi, S., Karia, N., Sivashankar, V., Krishnaswamy, R., Begwani, N., Raz, S., Lin, Y., Zhang, Y., Mahapatro, N., Srinivasan, P., Singh, A., & Simhadri, H. V. (2023). Filtered-DiskANN: Graph Algorithms for Approximate Nearest Neighbor Search with Filters. In *Proceedings of the ACM Web Conference 2023 (WWW '23)*, pages 3406–3416.
*   Liang, A., Zhang, P., Yao, B., Chen, Z., Song, Y., & Cheng, G. (2024). UNIFY: Unified Index for Range Filtered Approximate Neighbors Search. *Proceedings of the VLDB Endowment (PVLDB)*, 18(4):460-473.
*   Lin, Y., Fan, Y., Liu, Y., Zhang, C., & Yang, F. (2025). Survey of Filtered Approximate Nearest Neighbor Search over the Vector-Scalar Hybrid Data. *arXiv preprint arXiv:2505.06501*.
*   Patel, L., Kraft, P., Guestrin, C., & Zaharia, M. (2024). ACORN: Performant and Predicate-Agnostic Search Over Vector Embeddings and Structured Data. In *Proceedings of the 2024 International Conference on Management of Data (SIGMOD '24)*.
*   pgvector. (2024). pgvector: Open-source vector similarity search for PostgreSQL. GitHub repository. https://github.com/pgvector/pgvector.
*   Zhang, Q., Xu, S., Chen, Q., Sui, G., Xie, J., Cai, Z., Chen, Y., He, Y., Yang, Y., Yang, F., Yang, M., & Zhou, L. (2023). VBASE: Unifying Online Vector Similarity Search and Relational Queries via Relaxed Monotonicity. In *Proceedings of the 17th USENIX Symposium on Operating Systems Design and Implementation (OSDI 23)*, pages 377–395.
