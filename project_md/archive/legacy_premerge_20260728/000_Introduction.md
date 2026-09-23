# 000 — Introduction·Motivation 통합 정본

작성일: 2026-07-16  
상태: **CANONICAL — Introduction과 Motivation은 이 문서에서만 갱신한다.**

이 문서는 기존의 Introduction 관련 초안, 문헌 사실검증, 연구 흐름 문서와 현재 원고를 통합한 단일 관리본이다. 과거 파일은 작성 이력과 provenance 보존을 위해 삭제하지 않지만, 이후 Motivation·Research Gap·Research Question·Contribution의 표현은 본 문서를 기준으로 한다.

---

## 0. 최종 판정

사용자가 제안한 Research Gap의 큰 방향은 맞지만 다음 두 표현은 수정해야 한다.

1. **“필터드 벡터 검색은 random mask로만 평가한다”는 사실이 아니다.** Filtered-DiskANN은 자연 라벨이 있는 세 개의 실세계 생산 데이터와 반합성 데이터를 함께 평가했고, ACORN은 predicate clustering과 query correlation을 직접 형식화하며 복잡한 멀티모달 데이터도 사용했다. UNIFY 역시 실제 속성이 포함된 데이터와 무작위로 생성한 속성을 함께 사용한다.
2. **“최초”와 “전무”는 체계적 문헌고찰 없이 사용하지 않는다.** 비디오 DB, 필터드 벡터 검색, VLM 벤치마크 각각에는 본 연구와 겹치는 부분이 있다. 본 연구의 공백은 각 요소의 개별 부재가 아니라, 아래 요소들을 도시 감시 VLM-QA의 하나의 검증 가능한 DB 설계공간으로 통합한 연구가 드물다는 데 있다.

따라서 본 연구의 진짜 Motivation은 다음과 같이 확정한다.

> 대규모 도시 감시 영상 전체를 사용자 질의마다 VLM에 직접 입력할 수 없으므로, 데이터베이스가 먼저 소수의 관련 증거를 선별하는 evidence layer가 필요하다. 그러나 어떤 증거 저장 단위, 메타데이터-벡터 결합 계획, ANN 색인과 DB 배치가 검색 정확도·지연·저장 및 구축 비용을 가장 잘 균형화하는지는 도메인과 predicate 성질에 따라 달라진다. 이 설계공간을 올바르게 비교하려면 질의 필터, 검색 문서와 정답 라벨이 같은 주석 계보를 공유하지 않는 평가 워크로드가 선행되어야 한다. 본 연구는 비순환 tri-source 프로토콜로 이 전제를 충족한 뒤, 고정된 생성 모델 환경에서 도시 감시 VLM-QA evidence layer의 저장·색인·검색 구조와 답변 전파 경계를 실증한다.

---

## 1. 배경지식 없이도 이해되는 시스템 정의

### 1.1 사용자 질의는 어디로 입력되는가

“VLM 앞단의 DB evidence layer”는 사용자가 VLM에 직접 접속한다는 뜻이 아니다. 온라인 질의 흐름은 다음과 같다.

1. 사용자가 **질의 서비스**에 자연어 질문과 선택적인 시간·장소·센서 조건을 입력한다.
2. 질의 서비스는 자연어 의미 조건을 임베딩 질의로, 명시적 조건을 스칼라 predicate로 변환한다.
3. **데이터베이스 evidence layer**가 저장된 코퍼스에서 관련 clip·frame·caption·sensor record를 검색하고 순위를 정한다.
4. 검색기는 상위 결과를 작은 **evidence packet**으로 구성한다.
5. VLM은 전체 영상 아카이브가 아니라 **사용자 질문과 evidence packet만** 입력받아 최종 답변을 생성한다.

즉, VLM은 최종 사용자 인터페이스라기보다 검색 결과를 읽어 답을 만드는 마지막 생성 계층이며, 사용자의 요청은 먼저 질의 서비스와 DB 검색 계층을 거친다.

### 1.2 “전체 코퍼스”에는 무엇이 저장되는가

전체 코퍼스는 원본 CCTV 파일 자체만을 뜻하지 않는다. 운영 관점에서는 다음 자료가 clip/frame 식별자와 timestamp로 연결된다.

- 원본 비디오 또는 원본을 가리키는 URI·파일 경로
- clip/frame 식별자와 촬영 시각·카메라·교차로 정보
- 프레임 이미지 임베딩 또는 클립별 다중 프레임 임베딩
- 픽셀만 본 VLM이 오프라인으로 생성한 장면 캡션과 그 텍스트 임베딩
- 질의 시 필터링할 수 있는 센서·시공간 메타데이터
- ANN 색인과 텍스트·메타데이터 보조 색인

본 연구의 `clip-caption`, `frame-vector`, `multi-vector`, `dual-index`는 위 파생 자료 중 무엇을 검색 단위로 물질화할지를 나타낸다. 원본 영상 전체를 벡터 DB 내부에 복제해야 한다는 뜻은 아니다.

### 1.3 evidence packet의 정의

Evidence packet은 한 개의 벡터가 아니라, 최종 VLM이 답변 근거로 사용할 수 있도록 검색 결과를 묶은 제한된 크기의 자료 구조다. 최소 구성은 다음과 같다.

- `clip_id`, `camera_id`, timestamp와 원본 위치
- 상위 후보 프레임 또는 짧은 클립
- 픽셀 기반 VLM 캡션
- 질의와 관련된 센서·시공간 메타데이터
- 검색 점수·순위와 검색 전략
- provenance와 추적 가능한 원본 참조

따라서 evidence packet의 품질은 “관련 영상이 포함됐는가”, “필수 predicate를 만족하는가”, “불필요한 distractor가 얼마나 적은가”, “답변 근거를 역추적할 수 있는가”로 평가해야 한다.

---

## 2. 확정 Motivation — 발표용 불릿

- **운영상의 출발점**
  - 도시 감시 환경에서는 다수 카메라의 고화질 영상이 장기간 축적된다.
  - 사용자 질의마다 전체 원본 영상을 VLM에 입력하는 방식은 입력 길이, GPU 연산, 응답 지연과 추론 비용 때문에 현실적인 검색 구조가 될 수 없다.

- **필요한 시스템 계층**
  - 질의 서비스와 최종 VLM 사이에 database evidence layer가 필요하다.
  - 이 계층은 원본 영상에서 오프라인으로 파생·저장한 프레임 벡터, VLM 캡션, 센서·시공간 메타데이터와 원본 참조를 검색한다.
  - 전체 코퍼스에서 소수의 관련 프레임·클립·캡션·센서 기록을 evidence packet으로 구성해 최종 VLM에 전달한다.

- **핵심 DB 병목**
  - 같은 영상도 clip-caption, frame-vector, multi-vector 또는 dual-index 중 어떤 단위로 저장하는지에 따라 정확도·지연·저장비가 달라진다.
  - 자연어 의미 검색과 시간·장소·센서 predicate를 prefilter, postfilter, single-stage 또는 hybrid 중 어떻게 결합하는지에 따라 recall과 latency가 달라진다.
  - Flat, HNSW, IVF 계열과 global/partial index, 그리고 Faiss·pgvector·전용 벡터 엔진의 실행 방식은 구축 시간·색인 크기·검색 품질에 서로 다른 절충을 만든다.
  - 따라서 “가장 좋은 임베딩 모델”만 선택해서는 운영 구조를 결정할 수 없다.

- **기존 학계 연구 사이의 공백**
  - 비디오 DB 연구는 객체·트랙·시공간 이벤트 질의와 비디오 분석 비용 최적화를 발전시켰지만, 자유형 자연어 의미와 외생 센서 predicate로 VLM-QA evidence packet을 구성하는 저장·색인 설계공간은 직접적인 평가 대상이 아니었다.
  - 필터드 ANNS 연구는 실제 라벨, predicate clustering과 query correlation까지 다루지만, 도시 감시 센서 predicate·영상 증거 저장 단위·답변 계층을 하나의 워크로드에서 함께 평가하지 않는다.
  - 감시 VLM 연구는 모델의 영상 이해·이상행동 설명·QA 능력을 주로 평가한다. ForeSea처럼 검색 파이프라인을 포함하는 예외도 있지만, 저장 단위·ANN 색인·관계형 실행계획·색인 구축 및 저장 비용을 통제 비교하지 않는다.

- **평가 타당성이 먼저 필요한 이유**
  - predicate, 검색 document와 relevance가 같은 인간 주석에서 파생되면 prefilter의 우위와 텍스트 검색의 높은 점수가 데이터 구성상 보장될 수 있다.
  - 잘못된 워크로드에서 얻은 결과는 실제 DB 구조의 우수성이 아니라 라벨 계보의 자기참조를 측정할 수 있다.
  - 따라서 DB 설계공간 실험 전에 세 요소의 생성 경로를 분리한 비순환 tri-source protocol과 기계 감사가 필요하다.

- **본 연구가 하려는 일**
  - 새로운 VLM이나 새로운 ANN 알고리즘을 제안하는 것이 목적이 아니다.
  - 생성 모델과 비교 조건을 고정하고, 비순환 워크로드 위에서 저장 단위, 검색·필터 결합, 색인 구조와 DB 배치가 정확도·검색 계층 지연·저장 및 구축 비용에 미치는 영향을 통합 평가한다.
  - 최종 목적은 하나의 보편적 우승자를 선언하는 것이 아니라, predicate 선택도·결합도·질의 빈도와 캡션-질의 정합에 따른 **regime-specific DB 설계 지침**을 도출하는 것이다.

---

## 3. Research Gap 사실검증

| 제안한 주장 | 판정 | 논문에 사용할 안전한 표현 |
|---|---|---|
| 비디오 DB는 주로 객체 탐지·트랙 질의 효율화에 집중한다 | **대체로 맞지만 범위 보정 필요** | NoScope와 BlazeIt은 객체 기반 분류·집계·limit 질의를, Spatialyze는 객체와 지리·시공간 DSL을, EQUI-VOCAL은 scene graph 기반 복합 이벤트 질의 합성을 다룬다. 따라서 “객체 탐지만 다룬다”가 아니라 “VLM-QA용 자유형 의미 검색+외생 센서 predicate+evidence packet의 물리 설계 비교가 주된 평가 대상은 아니다”라고 쓴다. |
| 필터드 벡터 검색은 random mask로만 평가하며 clustering/correlation을 반영하지 않는다 | **그대로는 틀림** | Filtered-DiskANN은 자연 라벨 실데이터를 사용하고 random label의 비현실성을 직접 지적한다. ACORN은 predicate clustering과 query correlation을 형식화하고 멀티모달 데이터에서 평가한다. 본 연구의 공백은 “상관성의 미고려”가 아니라 “실제 도시 센서 predicate와 동일 선택도 random 대조군을 짝지어 VLM evidence·DB 배치까지 평가하지 않음”이다. |
| 감시 VLM 벤치마크는 모델 능력에 집중하고 DB 설계 변수 비교가 부족하다 | **대체로 맞음** | UCA/VALU와 HAWK는 모델·태스크 중심이다. 다만 ForeSea는 tracking→embedding index→top-k→VideoLLM 파이프라인을 포함하므로 예외를 명시한다. 차별점은 retrieval의 존재 여부가 아니라 storage unit·index family·filter plan·backend·build/storage cost의 통제 비교 여부다. |
| 모델을 고정하고 DB 설계공간을 최초로 정식화·실증한다 | **방향은 맞지만 ‘최초’는 삭제** | “본 연구가 검토한 선행 범위에서 개별적으로 다뤄진 축들을 비순환 도시 감시 VLM-QA 워크로드에서 통합적으로 정식화하고 실증한다”라고 쓴다. |

### 3.1 비디오 DB 계열의 정확한 공백

NoScope는 고정 영상과 목표 객체가 주어진 이진 분류 질의를, BlazeIt은 객체 탐지 출력에 대한 집계 및 limit 질의를 가속한다. Spatialyze는 지리 메타데이터와 객체의 물리 행동을 이용한 시공간 비디오 분석을 제공하며, EQUI-VOCAL은 사용자 예시로부터 scene graph 기반 복합 이벤트 질의를 합성한다. VIVA는 혼합 데이터 최적화와 저장·실행의 공동 최적화까지 제안한다.

따라서 비디오 DB 연구를 “객체 탐지만 하는 연구”로 축소해서는 안 된다. 본 연구가 메우는 구체적 공백은 **코퍼스 수준 자유형 자연어 의미 검색, 외생 센서 predicate, VLM용 evidence packet, 저장 단위와 ANN/RDB 물리 설계, 답변 전파를 동일 질의·정답 아래에서 함께 비교하는 것**이다.

### 3.2 필터드 벡터 검색 계열의 정확한 공백

Filtered-DiskANN은 세 개의 자연 라벨 생산 데이터와 다섯 개의 반합성 데이터를 함께 평가하며, 무작위 라벨은 실제 벡터-라벨 상관성을 반영하지 못한다고 명시한다. ACORN은 predicate를 통과한 벡터의 비균일 분포를 predicate clustering으로 정의하고, query correlation이 검색 성능을 바꾼다는 점을 이론과 실험에서 다룬다. UNIFY도 Paper와 WIT-Image의 실제 속성을 포함하지만, 나머지 데이터에는 무작위 수치 속성을 부여한다.

그러므로 본 연구는 “기존 연구가 clustering을 몰랐다”고 주장하지 않는다. 대신 다음 차이를 주장한다.

- 실제 교통·감시 센서와 시공간 predicate를 사용한다.
- 동일 predicate 선택도를 유지한 matched random mask를 대조군으로 둔다.
- 단순 QPS-recall을 넘어 predicate 군집성에 따른 부호와 기전을 비교한다.
- clip-caption·frame-vector·multi-vector·dual-index 저장 단위를 함께 비교한다.
- pgvector의 global+WHERE·iterative scan·partial/local index와 전용 엔진 경로를 교차 확인한다.
- 검색 차이가 고정 VLM 답변으로 전파되는 조건과 실패 경계를 별도로 검증한다.

### 3.3 감시 VLM·VideoRAG 계열의 정확한 공백

UCA/VALU는 시간적 문장 접지와 캡셔닝 등 감시 video-language understanding 태스크에서 모델을 비교하고, HAWK는 오픈월드 이상행동 설명과 QA 모델을 제안한다. 이들은 모델의 인지·언어 능력을 평가하는 연구다. ForeSea는 더 직접적으로 tracking, multimodal embedding index, top-k retrieval과 VideoLLM을 연결하므로 “감시 VLM 연구에는 retrieval이 없다”는 주장도 사용할 수 없다.

안전한 차별성은 다음과 같다.

> 기존 감시 VLM·VideoRAG 연구는 검색 또는 답변 정확도와 temporal grounding을 중심으로 평가한다. 본 연구는 생성 모델을 비교 대상으로 삼기보다, 동일 질의·정답 아래에서 evidence의 저장 입도, metadata filter placement, ANN 색인 계열, 관계형·전용 실행 경로, 검색 계층 지연, 색인 크기와 구축 비용을 조작 변수로 둔다.

---

## 4. 최종 Problem Statement

> 전체 원본 데이터를 사용자 질의마다 VLM에 입력하는 대신, 도시 감시 멀티모달 코퍼스에서 필요한 증거를 더 낮은 검색 비용과 지연으로 선별하면서 검색 정확도와 최종 답변 지원 가능성을 보존하려면 어떤 DB 저장 단위, 메타데이터-벡터 결합 계획, ANN 색인 및 물리적 배치 정책을 선택해야 하는가? 그리고 이 비교가 특정 구조에 유리하도록 구성되지 않았음을 어떻게 검증할 것인가?

이 문제는 다음 두 층으로 나뉜다.

1. **평가 타당성 층:** predicate, document, relevance의 생성 계보를 분리해 구조 비교가 순환적으로 결정되지 않도록 한다.
2. **DB 설계 층:** 타당한 워크로드 위에서 storage unit, retrieval/filter plan, index/backend와 배포 정책의 정확도·지연·비용 절충을 비교한다.

---

## 5. 확정 Research Questions

현재 원고의 세 축을 유지한다. 비순환성은 별도 RQ 번호를 추가하기보다 모든 RQ에 선행하는 평가 조건으로 둔다.

### 평가 선행조건 — Validity prerequisite

> Predicate, searched document와 relevance가 같은 라벨 계보를 공유하면 검색 구조 비교의 결론이 어떻게 왜곡되며, tri-source separation과 기계 감사로 이를 차단할 수 있는가?

### RQ-S — Structure

> 동일 질의와 동일 정답 아래에서 저장 단위, 검색 전략, 필터 결합 계획, 색인 계열과 실행 기반의 선택이 검색 품질을 어떻게 바꾸는가?

- 저장 단위: clip-caption, frame-vector, multi-vector, dual-index
- 검색: metadata-only, sparse/BM25, dense, prefilter, postfilter, hybrid
- 색인: Flat, IVF-Flat, HNSW, IVF-PQ
- 실행: Faiss, PostgreSQL+pgvector, Milvus, Weaviate

### RQ-ALC — Accuracy·Latency·Cost

> 각 구조는 검색 정확도, 격리된 검색 계층 p50/p95 latency, 색인 크기·구축 시간과 질의당 상각 비용 사이에서 어떤 Pareto 절충을 형성하는가?

주의: 본 연구의 latency·cost 주장은 전체 VLM 서비스의 end-to-end 비용이 아니라 **검색·색인 계층**으로 한정한다.

### RQ-M — Multimodal coupling and answer propagation

> 영상 프레임, VLM 캡션과 구조화 센서 기록의 결합은 최적 DB 구조를 어떻게 바꾸며, 검색·색인 차이는 어떤 조건에서 고정 VLM의 최종 답변으로 전파되거나 전파되지 않는가?

---

## 6. 논문 삽입용 Motivation·Research Gap 문단

대규모 도시 교통·감시 환경은 연속적인 CCTV 영상뿐 아니라 신호 상태, 시간, 위치, 교통량과 같은 센서·시공간 기록을 함께 생산한다. 사용자는 이러한 아카이브에 대해 “오전 시간대에 자전거가 두 대 이상 보이는 교차로 장면을 찾아라”와 같이 자연어 의미와 구조화 조건이 결합된 질문을 제기한다. 그러나 질의마다 장기간 축적된 전체 영상을 VLM에 입력하는 방식은 입력 길이, 연산 비용과 응답 지연 측면에서 현실적이지 않다. 따라서 실용적인 시스템은 먼저 데이터베이스가 오프라인으로 물질화한 프레임 벡터, VLM 캡션, 센서·시공간 메타데이터에서 소수의 관련 클립과 프레임을 검색하고, 원본 참조와 함께 evidence packet으로 구성하여 최종 VLM에 전달해야 한다.

이 구조에서는 답변 품질과 운영 비용이 생성 모델만으로 결정되지 않는다. 동일한 영상도 clip-caption, frame-vector, multi-vector 또는 dual-index 중 어떤 단위로 저장하는지, 자연어 벡터 검색과 메타데이터 predicate를 prefilter·postfilter·single-stage 중 어디에서 결합하는지, Flat·HNSW·IVF 계열 색인과 global·partial index를 어떻게 배치하는지에 따라 검색 품질, 지연, 저장공간과 구축 비용이 달라진다. 따라서 도시 감시 VLM-QA는 모델 선택 문제인 동시에 database evidence layer의 물리 설계와 질의 계획 문제다.

관련 연구들은 이 문제의 일부를 깊이 다루어 왔다. 비디오 DB 시스템은 객체·시공간 이벤트 질의와 영상 분석 비용을 최적화하고, 필터드 ANNS 연구는 자연 라벨, predicate clustering과 query correlation을 포함한 벡터-속성 결합 검색을 발전시켰다. 감시 VLM 및 VideoRAG 연구도 영상 이해, 이상행동 설명, temporal grounding과 검색 기반 QA를 확장하고 있다. 그러나 이들 축을 실제 도시 센서 predicate, 다중 증거 저장 단위, ANN/RDB 물리 구조, 검색 계층 비용과 최종 답변 전파를 포함하는 하나의 통제된 설계공간으로 연결한 평가는 드물다.

더 근본적으로, 이러한 설계공간의 비교는 워크로드 구성 자체가 비순환적일 때만 의미가 있다. 질의 필터, 검색 문서와 relevance label이 같은 주석에서 파생되면 prefilter가 정답을 제거하지 못하도록 구성되고, 검색 문서가 정답 라벨을 재진술해 특정 전략의 우위가 사실상 미리 결정될 수 있다. 본 연구는 predicate를 외생 센서·시공간 기록에서, document를 픽셀만 본 VLM 캡션에서, relevance를 독립 인간 주석에서 생성하는 tri-source protocol과 기계 감사를 먼저 구축한다. 그 위에서 생성 모델을 고정하고 저장 단위, 검색·필터 계획, 색인 및 DB 배치가 정확도·검색 지연·저장 및 구축 비용에 미치는 영향을 비교하며, 검색 차이가 답변으로 전파되는 조건과 경계를 규명한다.

---

## 7. 핵심 Contributions — 과장 제거본

1. **평가 타당성:** predicate, document, relevance의 생성 계보를 분리한 비순환 tri-source 워크로드와 strict/semantic 이중 qrels, 기계 감사 절차를 제시한다.
2. **순환성 사례 연구:** 초기 자체 워크로드에서 코드 수준의 순환 경로를 진단하고, 수리 전후 성능 붕괴를 재현해 구조 비교가 무효화되는 기전을 보인다.
3. **실측 predicate 대조:** 실제 센서·시공간 predicate와 동일 선택도 random mask를 짝지어 공유 색인의 filtered-ANN 거동 차이를 측정하고, 관계형·전용 엔진에서 기전을 교차 확인한다.
4. **DB 설계공간:** 저장 단위, 검색·필터 계획, ANN 색인, pgvector global/partial 배치를 정확도·검색 지연·색인 크기·구축 비용 위에서 비교해 조건별 선택 지침과 hot/cold 배포 손익분기를 도출한다.
5. **답변 전파 경계:** 검색·색인 차이를 최종 VLM-QA 성능으로 과대 해석하지 않도록, 스케일·VLM 지각 능력·답변 편향이 구조 차이의 전파를 차단하는 경계를 보고한다.

“최초”, “완전한 독립”, “전무”, “모든 데이터셋에서 우월”과 같은 표현은 사용하지 않는다.

---

## 8. 주장 범위와 한계

- 본 연구는 **24시간 스트리밍 적재 및 온라인 임베딩 비용을 직접 벤치마크하지 않았다.** 운영 Motivation은 타당하지만, 결과는 우선 오프라인으로 물질화된 아카이브의 검색·색인 계층에 적용된다.
- 검색 latency는 생성 모델 추론을 제외한 격리 측정값이므로 end-to-end 응답시간으로 확대하지 않는다.
- `clip-caption`과 `frame-vector` 비교는 텍스트 인코더와 시각 인코더 선택을 포함하는 실무 설계 대비다. 저장 단위만을 격리한 encoder-controlled ablation으로 표현하지 않는다.
- ACORN과 Filtered-DiskANN이 correlation을 무시했다고 주장하지 않는다. 본 연구의 차이는 도시 센서 matched control과 VLM evidence layer의 통합 평가다.
- UCA/VALU와 HAWK를 “DB가 없는 불완전 연구”로 평가하지 않는다. 평가 대상이 모델/태스크로 다르며 본 연구와 상보적이라고 서술한다.
- ForeSea에는 retrieval/indexing pipeline이 있으므로 “기존 감시 VLM에는 검색이 없다”고 쓰지 않는다.
- 현재 결과는 단일 보편 최적 구조보다 데이터·질의 regime에 따른 선택 규칙을 지지한다.

---

## 9. 통합된 기존 문서와 관리 정책

다음 파일의 유효 내용을 본 문서에 통합했다.

| 기존 파일 | 흡수한 내용 | 이후 상태 |
|---|---|---|
| [100_INTRO_topic_selection_rationale.md](100_INTRO_topic_selection_rationale.md) | 주제 선정, 초기 연구 공백과 DBR 포지셔닝 | 역사·provenance |
| [770_INTRO_structure_and_draft_20260714.md](770_INTRO_structure_and_draft_20260714.md) | Background→problem→gap→approach→contribution 흐름 | 역사·provenance |
| [780_INTRO_filtered_vector_search_factcheck_20260714.md](780_INTRO_filtered_vector_search_factcheck_20260714.md) | pre/post/single-stage, selectivity 용어와 관련연구 | 사실검증 근거 |
| [800_Introduction_20260714.md](800_Introduction_20260714.md) | 기존 장문 Introduction 초안 | 본 문서로 대체 |
| [760_RESEARCH_FLOW_20260714.md](760_RESEARCH_FLOW_20260714.md) | 연구 전체 flow 요약 | 발표용 보조자료 |
| [760_RESEARCH_FLOW_systematic_explanation_20260714.md](760_RESEARCH_FLOW_systematic_explanation_20260714.md) | 세부 RQ와 데이터셋·실험 연결 | 방법·결과 설명 보조자료 |
| [810_overall_blueprint_20260715.md](810_overall_blueprint_20260715.md) | 사용자 질의→DB→evidence packet→VLM 흐름 | 시스템 청사진 |
| [../manuscript/main_introduction.md](../manuscript/main_introduction.md) | Motivation, 도메인 선정, 4개 연구 흐름 | 역사 초안 |
| [../manuscript/v3_working/named/W1-intro-related.md](../manuscript/v3_working/named/W1-intro-related.md) | RQ 세 축, 증거 지위, 관련연구 보강 | 현재 원고 삽입 provenance |
| [../manuscript/v3_working/named/W1-intro-related.provenance.md](../manuscript/v3_working/named/W1-intro-related.provenance.md) | W1 삽입 블록의 값·문헌 출처 추적 | provenance |
| [../manuscript/kiise_dbr_manuscript_v3_DBR_review_sample_based.md](../manuscript/kiise_dbr_manuscript_v3_DBR_review_sample_based.md) | 현재 제출 원고의 실제 Introduction·Related Work·결과 범위 | 제출 원고 |

관리 정책:

- Motivation·Research Gap·RQ·Contribution의 개념 정본은 이 파일이다.
- 제출용 산문은 본 파일의 6절을 기준으로 원고에 반영한다.
- 과거 파일은 삭제하지 않되 새로운 주장이나 수치를 추가하지 않는다.
- 실험 수치가 바뀌면 결과 정본을 먼저 갱신하고, 그다음 본 문서의 표현 강도를 갱신한다.

---

## 10. 1차 근거 문헌

### 비디오 DB·분석 시스템

- NoScope, PVLDB 2017: <https://www.vldb.org/pvldb/vol10/p1586-kang.pdf>
- BlazeIt, PVLDB 2020: <https://www.vldb.org/pvldb/vol13/p533-kang.pdf>
- EQUI-VOCAL, PVLDB 2023: <https://www.vldb.org/pvldb/vol16/p2714-zhang.pdf>
- Spatialyze, PVLDB 2024: <https://www.vldb.org/pvldb/vol17/p2136-kittivorawong.pdf>
- VIVA, CIDR 2022: <https://vldb.org/cidrdb/2022/viva-an-end-to-end-system-for-interactive-video-analytics.html>

### 필터드 벡터 검색

- Filtered-DiskANN, WWW 2023: <https://harsha-simhadri.org/pubs/Filtered-DiskANN23.pdf>
- VBASE, OSDI 2023: <https://www.usenix.org/conference/osdi23/presentation/zhang-qianxi>
- ACORN, SIGMOD 2024: <https://arxiv.org/abs/2403.04871>
- UNIFY, PVLDB 2025: <https://www.vldb.org/pvldb/vol18/p1118-yao.pdf>
- pgvector iterative scans: <https://github.com/pgvector/pgvector>

### 감시 VLM·VideoRAG

- UCA/VALU, CVPR 2024: <https://openaccess.thecvf.com/content/CVPR2024/html/Yuan_Towards_Surveillance_Video-and-Language_Understanding_New_Dataset_Baselines_and_Challenges_CVPR_2024_paper.html>
- HAWK, NeurIPS 2024: <https://proceedings.neurips.cc/paper_files/paper/2024/hash/fca83589e85cb061631b7ebc5db5d6bd-Abstract-Conference.html>
- ForeSea, arXiv 2026: <https://arxiv.org/abs/2603.22872>

### 본 연구의 실증 근거

- [620_RESULTS_filtered_ann_real_predicates_20260710.md](620_RESULTS_filtered_ann_real_predicates_20260710.md): 실측 predicate 대 matched random mask와 엔진 교차 재현
- [700_MEVA_integration_execution_20260713.md](700_MEVA_integration_execution_20260713.md): 해외 감시 데이터 이식
- [720_RESULTS_db_design_storage_index_20260713.md](720_RESULTS_db_design_storage_index_20260713.md): 저장 단위, partial/local index와 hot/cold 정책
- [660_GOAL3_regime_characterization_20260713.md](660_GOAL3_regime_characterization_20260713.md): 구조→답변 전파의 세 경계
- [DATA_PROVENANCE_raw_vs_derived_20260715.md](DATA_PROVENANCE_raw_vs_derived_20260715.md): raw·파생·AI 생성 데이터 계보
