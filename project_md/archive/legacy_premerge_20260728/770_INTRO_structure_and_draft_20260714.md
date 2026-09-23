# 770 — Introduction 구성안 및 문단 초안 (2026-07-14)

> 상태: **HISTORY** — 본 구성안은 [`000_Introduction.md`](000_Introduction.md)에 통합되었다. 신규 수정은 통합 정본에서 수행한다.

목적: 본 연구 논문의 Introduction에 포함해야 할 핵심 내용을 체계적으로 정리한다.  
구성 요소: 현재 기술 동향, 문제 관찰 및 정의, 세부 연구 필요성, 사회적·기술적 기여, 최종 contribution.

---

## 1. Introduction 전체 흐름

Introduction은 다음 순서로 전개하는 것이 가장 자연스럽다.

1. **현재 기술 동향**
   - 도시 감시·교통 데이터가 영상, 텍스트, 센서·시공간 metadata를 함께 생산한다.
   - VLM/LLM과 multimodal RAG의 발전으로 영상 기반 질의응답 가능성이 커졌다.
   - vector database와 filtered vector search가 자연어 검색과 구조화 조건을 결합하는 핵심 기술로 부상했다.

2. **문제 관찰 및 정의**
   - 하지만 VLM-QA는 모델이 바로 모든 영상을 보는 구조가 아니다.
   - 먼저 DB가 관련 증거 clip/frame/document를 찾아야 한다.
   - 단일 vector search만으로는 시간·위치·센서 조건을 안정적으로 보장하기 어렵다.
   - 반대로 metadata filter를 무조건 먼저 적용하면 soft intent에서 관련 결과를 제거할 수 있다.
   - 더 심각하게, 평가 데이터셋을 만들 때 filter, relevance, document가 같은 라벨에서 파생되면 prefilter 성능이 구성상 과장될 수 있다.

3. **세부 관찰과 연구 필요성**
   - 기존 비디오 DB 연구는 객체·트랙 질의처리에 강하지만 VLM-QA evidence layer를 직접 다루지 않는다.
   - 기존 filtered vector search 연구는 일반 vector+attribute filter 문제를 다루지만 실제 감시 센서 predicate와 VLM-QA 워크로드의 연결은 부족하다.
   - 기존 감시 VLM benchmark는 모델 이해 능력을 평가하지만, DB 저장·색인·검색 구조를 통제 변수로 비교하지 않는다.
   - 따라서 모델을 고정한 상태에서 DB evidence layer의 설계 선택지를 정량 비교할 필요가 있다.

4. **사회적·기술적 의의**
   - 사회적으로는 도시 감시·교통 데이터에서 필요한 증거를 더 정확하고 설명 가능하게 찾는 기반을 제공한다.
   - 기술적으로는 multimodal surveillance retrieval을 단순 embedding 모델 문제가 아니라 DB 설계 문제로 정식화한다.
   - 실제 시스템 관점에서는 정확도뿐 아니라 latency, storage, index build cost까지 포함한 설계 가이드를 제공한다.

5. **기여**
   - 비순환 tri-source 워크로드 프로토콜
   - 저장·색인·검색 설계공간 비교
   - 실제 predicate 기반 filtered ANN 및 partial/local index 정책
   - 검색 결과가 VLM-QA 답변으로 전파되는 경계 분석
   - MEVA/MIRIS를 통한 외적 타당성 보강

---

## 2. Introduction 문단 초안

### 2.1 기술 동향: 멀티모달 감시 데이터와 VLM-QA

도시 교통·감시 환경은 더 이상 단일 영상 스트림만을 생산하지 않는다. CCTV 프레임과 클립뿐 아니라, 사건 설명 텍스트, 차량·보행자 주석, 신호 상태, 시간대, 위치, 교통량과 같은 센서·시공간 metadata가 함께 축적된다. 최근 VLM과 LLM의 발전은 이러한 데이터를 자연어로 질의하고, 관련 영상 증거를 바탕으로 답변을 생성하는 VLM-QA 또는 multimodal RAG 응용을 가능하게 만들고 있다. 동시에 vector database와 filtered vector search는 자연어 의미 검색과 구조화 조건을 결합하기 위한 핵심 인프라로 부상하고 있다. 예컨대 VBASE, ACORN, pgvector 계열 시스템은 vector similarity search와 relational predicate를 함께 처리하는 방향으로 발전하고 있으며, UCA/VALU, HAWK, UrBench와 같은 감시·도시 VLM benchmark는 감시 영상 이해가 여전히 어렵고 중요한 문제임을 보여준다.

### 2.2 문제 관찰: 좋은 모델만으로 충분하지 않다

그러나 VLM-QA 시스템에서 모델은 모든 원본 영상을 직접 탐색하지 않는다. 실제 시스템에서는 먼저 데이터베이스가 질문과 관련된 clip, frame, caption, metadata record를 찾아 evidence packet으로 구성하고, 그 다음에 VLM 또는 LLM이 이 증거를 바탕으로 답변한다. 따라서 답변 품질은 생성 모델의 능력뿐 아니라, 그 이전 단계에서 어떤 증거가 검색되어 전달되는지에 크게 의존한다.

이때 감시 데이터 질의는 단순한 의미 검색이 아니다. 예를 들어 “오전 시간대에 도로변에 주차된 차량이 보이는 CCTV clip을 찾아라”라는 질의에는 “주차 차량”이라는 자연어 의미 조건과 “오전”이라는 구조화 metadata 조건이 함께 포함된다. 단일 임베딩 기반 vector search는 의미적으로 유사한 장면을 찾는 데 유용하지만, 시간·위치·센서 조건처럼 반드시 만족해야 하는 조건을 보장하지 못할 수 있다. 반대로 metadata 조건을 먼저 적용하는 prefilter 방식은 hard constraint에서는 효과적일 수 있지만, 사용자의 의도가 느슨한 soft intent라면 의미적으로 관련 있는 결과를 제거할 위험이 있다.

### 2.3 평가상의 함정: 순환성

또 하나의 중요한 문제는 평가 워크로드 자체의 타당성이다. 공개 데이터셋의 라벨을 이용해 검색 질의, metadata filter, 정답(qrels), 검색 문서를 동시에 구성하면, filter 조건과 정답 정의가 같은 라벨에서 파생되는 순환성(circularity)이 발생할 수 있다. 이 경우 prefilter가 좋은 결과를 보이는 것은 실제 검색 구조의 우수성 때문이 아니라, 정답이 애초에 filter 통과 집합 안에만 존재하도록 구성되었기 때문일 수 있다. 또한 검색 문서가 라벨을 그대로 재진술하면 BM25나 dense retrieval이 실제 영상 이해 없이도 높은 점수를 얻을 수 있다.

본 연구는 이러한 문제를 단순한 구현 오류가 아니라 멀티모달 감시 검색 평가에서 발생할 수 있는 구조적 위험으로 본다. 따라서 filter predicate, relevance, searched document가 서로 다른 소스에서 생성되도록 분리하고, strict/semantic 이중 정답과 기계 감사 절차를 포함하는 비순환 워크로드가 필요하다.

### 2.4 기존 연구와의 차이

기존 연구들은 이 문제의 일부를 다루었지만, 본 연구가 다루는 교차 영역을 직접적으로 포괄하지는 않는다. 비디오 DB 연구는 고정 카메라 영상에서 객체 탐지, 트랙 질의, 시공간 질의처리를 효율화해 왔다. 그러나 이들은 주로 detector나 tracker의 산출물을 대상으로 하며, 자연어 질의와 센서·시공간 metadata가 결합된 VLM-QA evidence retrieval 구조를 직접 비교하지 않는다.

Filtered vector search 연구는 vector similarity search와 structured predicate를 결합하는 알고리즘과 시스템을 제안해 왔다. 그러나 일반 benchmark의 attribute filter나 random mask 기반 평가가 실제 감시 센서 predicate의 군집성, 선택도, correlation을 충분히 반영한다고 보기는 어렵다. 감시 VLM benchmark 연구는 어떤 모델이 감시 영상을 잘 이해하는지를 평가하지만, 모델을 고정한 상태에서 저장 단위, 색인 구조, 필터 결합 방식, 관계형 DB 구현을 통제 비교하지는 않는다.

따라서 본 연구는 기존 연구를 대체하려는 것이 아니라, 그 사이의 비어 있는 층인 **VLM-QA evidence layer의 데이터베이스 설계 문제**를 다룬다.

### 2.5 본 연구의 접근

본 연구는 새로운 VLM/LLM 모델을 제안하거나 학습하지 않는다. 대신 고정된 모델 환경에서, 데이터베이스의 저장·색인·검색 구조가 검색 품질과 VLM-QA 답변 지원 가능성에 어떤 영향을 미치는지 평가한다. 이를 위해 AI Hub 522 교차로 신호체계 데이터를 중심으로, 센서 기록을 predicate 채널로, 사람 주석을 relevance 채널로, 프레임 픽셀만 본 VLM caption을 document 채널로 분리한 tri-source 워크로드를 구축한다. 또한 MEVA를 해외 CCTV 외적 타당성 검증에, MIRIS를 DB index 정책 교차검증에 활용한다.

실험에서는 동일한 질의와 정답 아래에서 저장 단위(clip-caption, frame-vector, multi-vector, dual-index), 검색 전략(metadata-only, BM25, dense vector, postfilter, prefilter, hybrid), 색인 구조(Flat, HNSW, IVF, IVF-PQ), 관계형 DB 구현(global index + WHERE, partial/local index)을 비교한다. 평가는 nDCG, Recall, MRR뿐 아니라 latency, storage, index build cost, 그리고 answer-level propagation까지 포함한다.

### 2.6 사회적 기여와 기술적 통찰

사회적으로, 도시 감시·교통 데이터는 공공 안전, 교통 운영, 사고 분석과 직접 연결된다. 이러한 데이터에서 필요한 증거를 더 정확하고 빠르게 찾는 것은 단순한 검색 성능 향상을 넘어, 사람이 검토해야 할 영상 범위를 줄이고, 의사결정에 사용되는 증거의 추적성과 설명 가능성을 높이는 데 기여할 수 있다. 특히 본 연구는 자동 감시 판단을 대체하려는 것이 아니라, 질의와 관련된 evidence를 더 신뢰성 있게 찾고 제시하는 데이터베이스 계층에 초점을 둔다.

기술적으로, 본 연구는 멀티모달 감시 검색을 “좋은 embedding model 하나를 고르는 문제”가 아니라, 저장 단위, metadata predicate, filter placement, index deployment를 함께 설계해야 하는 데이터 관리 문제로 정식화한다. 이는 VLM-QA 시스템에서 모델 계층과 데이터베이스 계층의 역할을 분리하고, 어떤 조건에서 어떤 검색 구조가 적합한지 설명 가능한 설계 지침을 제공한다.

---

## 3. Contribution 초안

본 연구의 기여는 다음과 같다.

1. **비순환 멀티모달 감시 검색 워크로드 프로토콜**  
   본 연구는 filter predicate, searched document, relevance가 같은 라벨에서 파생될 때 발생하는 순환성 문제를 정의하고, 이를 피하기 위해 predicate=센서 기록, document=픽셀 기반 VLM caption, relevance=사람 주석으로 분리한 tri-source 워크로드를 구축한다. 또한 strict/semantic 이중 qrels와 기계 감사 절차를 통해 평가 타당성을 검증한다.

2. **VLM-QA evidence layer의 저장·검색 설계공간 비교**  
   동일 질의와 동일 정답 아래에서 clip-caption, frame-vector, multi-vector, dual-index 저장 단위와 metadata-only, BM25, dense vector, postfilter, prefilter, hybrid 검색 전략을 비교한다. 이를 통해 최적 저장 단위와 filter 결합 방식이 데이터셋, caption 품질, query regime에 따라 달라짐을 보인다.

3. **실제 predicate 기반 filtered vector search 분석**  
   실측 센서·시공간 predicate가 random mask와 다르게 동작하며, 공유 index 기반 postfilter 또는 단일 단계 filtered ANN 평가가 recall을 과대평가할 수 있음을 보인다. 이는 filtered vector search를 실제 운영 predicate로 평가해야 함을 시사한다.

4. **관계형 DB 구현 지침 도출**  
   PostgreSQL+pgvector 환경에서 global index + WHERE, iterative scan, partial/local index를 비교하고, 선택적 predicate에서는 partial/local index가 recall과 latency를 안정화함을 보인다. 이를 바탕으로 predicate 선택도와 질의 빈도에 따른 hot/cold index 정책을 제시한다.

5. **검색 결과와 VLM-QA 답변 사이의 경계 분석**  
   evidence 품질이 답변 품질에 영향을 줄 수 있음을 확인하는 동시에, index 차이가 항상 답변 정확도로 바로 전파되지는 않음을 보인다. corpus scale, VLM perception, answer bias가 검색 구조와 답변 품질 사이의 경계로 작동함을 분석한다.

---

## 4. 더 압축한 Contribution 3개 버전

논문 지면이 부족하면 다음 3개로 압축하는 것이 좋다.

1. **Validity contribution**  
   순환성을 차단한 source-separated multimodal surveillance retrieval workload와 strict/semantic 이중 평가 프로토콜을 제안한다.

2. **Design-space contribution**  
   고정 모델 환경에서 저장 단위, 필터 결합 방식, 색인 구조가 accuracy·latency·storage에 미치는 영향을 비교하고 regime-specific 설계 지침을 도출한다.

3. **Operational DB contribution**  
   실제 센서·시공간 predicate 하에서 filtered vector search와 pgvector partial/local index를 평가하고, selective predicate에 대한 hot/cold index 운영 정책을 제시한다.

---

## 5. Introduction 마지막 문단 예시

요컨대 본 연구는 멀티모달 감시 VLM-QA를 모델 성능 문제가 아니라 데이터베이스 evidence layer의 설계 문제로 정식화한다. 본 연구의 결과는 hard metadata constraint에서는 prefilter가 유리하지만 soft intent에서는 신중해야 하며, 최적 저장 단위는 caption과 visual evidence의 정합에 따라 달라지고, 실제 센서 predicate에서는 random mask 기반 filtered ANN 평가가 성능을 과대평가할 수 있음을 보여준다. 또한 관계형 DB 구현에서는 선택적 predicate에 대해 partial/local index가 recall과 latency를 안정화하며, 이를 통해 VLM-QA evidence retrieval을 위한 실용적 저장·색인·검색 설계 가이드를 제공한다.
