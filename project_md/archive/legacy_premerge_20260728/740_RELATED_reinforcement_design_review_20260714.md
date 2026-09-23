# 740 — 관련연구 대비 기여 강화 설계 검토 (2026-07-14)

목적: 본 연구의 확실한 결론, 기존 연구와의 차이, 논문 기여를 더 분명하게 보이기 위해 어떤 설계 보강이 필요한지 점검한다.  
검토 기준: 로컬 원고/실험 문서 + 2026-07-14 기준 웹 확인.

---

## 1. 결론 요약

**동일 주제를 그대로 수행한 상위 학회/저널 논문은 확인되지 않는다.**  
다만 인접한 상위권 연구는 세 축으로 강하게 존재한다.

1. **비디오 DB/시스템 질의처리**: NoScope, Focus, BlazeIt, MIRIS, OTIF, EQUI-VOCAL.
2. **filtered vector search / vector DB**: Filtered-DiskANN, VBASE, ACORN, pgvector iterative scan.
3. **감시·도시 VLM/Video-Language 벤치마크**: UCA/VALU, HAWK, UrBench, ForeSea.

따라서 본 연구는 “완전히 새로운 모든 것을 제안했다”가 아니라, 다음 교차점에 위치한다고 말해야 한다.

> 기존 비디오 DB 연구는 객체·트랙·시공간 질의처리에 강하지만 VLM-QA evidence layer와 비순환 멀티모달 워크로드를 다루지 않는다.  
> 기존 filtered vector search 연구는 vector+structured predicate의 알고리즘/시스템을 다루지만 감시 영상의 실제 센서 predicate, 저장 단위, VLM-QA 답변 연결을 다루지 않는다.  
> 기존 감시 VLM 연구는 모델 이해·QA 성능을 평가하지만 DB의 저장·색인·검색 구조를 통제 비교하지 않는다.  
> 본 연구는 이 세 축의 교차점에서, 고정 모델 환경의 evidence layer를 accuracy·latency·storage 관점으로 평가한다.

---

## 2. 상위 학회/저널 관련연구 확인

### 2.1 비디오 DB/시스템 질의처리

| 연구 | venue | 핵심 내용 | 본 연구와의 차이 |
|---|---|---|---|
| NoScope | PVLDB 2017 | 고정 카메라/감시 영상에서 NN query 비용을 줄이는 특화 모델 cascade | binary/object query 중심, 자연어+metadata+VLM-QA 아님 |
| Focus | OSDI 2018 | ingest-time approximate index와 query-time expensive CNN을 나눠 low-cost/low-latency video query 지원 | 객체 클래스 검색 중심, VLM evidence retrieval 구조 비교 아님 |
| BlazeIt | PVLDB 2020 | FrameQL로 video analytics aggregation/limit query 최적화 | declarative object/spatiotemporal query 중심 |
| MIRIS | SIGMOD 2020 | object track query를 추적과 질의처리로 통합 | 트랙 predicate 질의. 본 연구는 MIRIS를 index 정책 검증에 활용 가능 |
| OTIF | SIGMOD 2022 | large video에서 general-purpose object tracks를 효율적으로 전처리 | track extraction/V-ETL 계열. 자연어+센서+VLM-QA 아님 |
| EQUI-VOCAL | PVLDB 2023 | 사용자 피드백으로 compositional video event query를 합성 | scene graph/query synthesis 중심. 저장 단위·filtered vector DB 비교 아님 |

판정: 이 축은 본 연구의 DB 정당성을 뒷받침하는 필수 관련연구다. 다만 직접 비교군이라기보다는 “기존 VDBMS가 다루던 질의처리 문제를 VLM-QA evidence layer로 확장한다”는 위치 설정에 사용한다.

### 2.2 filtered vector search / vector DB

| 연구 | venue | 핵심 내용 | 본 연구와의 차이 |
|---|---|---|---|
| Filtered-DiskANN | WWW 2023 | filter-aware ANN graph로 filtered ANNS 지원 | 일반 ANN 알고리즘. 감시 센서 predicate·VLM-QA workload 아님 |
| VBASE | OSDI 2023 | vector similarity search와 relational query를 relaxed monotonicity로 통합 | DBMS+vector query 일반론. 영상 evidence layer 설계 아님 |
| ACORN | SIGMOD 2024 | HNSW 기반 predicate-agnostic hybrid search | 강한 직접 관련. 본 연구는 ACORN류를 발명하는 것이 아니라 실제 감시 predicate에서 평가 편향과 설계 정책을 보임 |
| pgvector iterative scan | system feature | filtered vector search에서 충분한 결과가 나올 때까지 index scan 확장 | 본 연구의 관계형 DB 구현 실험과 직접 연결 |

판정: 본 연구의 P2/P3는 이 분야와 직접 연결된다. 차별점은 “새 filtered ANN 알고리즘”이 아니라, **실측 센서·시공간 predicate가 random-mask 평가와 다르게 작동하며, local/partial index 정책이 필요함을 실제 감시·교통 코퍼스에서 보였다**는 점이다.

### 2.3 감시·도시 VLM/Video-Language 벤치마크

| 연구 | venue/status | 핵심 내용 | 본 연구와의 차이 |
|---|---|---|---|
| UCA/VALU | CVPR 2024, TCSVT 2025 | 감시 video-language understanding 데이터셋과 모델 벤치마크 | 모델 이해 평가. DB 저장·색인·검색 구조 비교 아님 |
| HAWK | NeurIPS 2024 | open-world video anomaly understanding, VLM QA/description | 모델/데이터셋 기여. evidence layer DB 설계 아님 |
| UrBench | AAAI 2025 | multi-view urban scenario에서 LMM 평가 | 도시 LMM 벤치마크. 코퍼스 검색·vector DB 구현 아님 |
| ForeSea | arXiv 2026 | image+text query 기반 forensic surveillance video QA/retrieval | 주제는 매우 가깝지만, 현재 확인 기준 top venue 게재 논문은 아님. DB 저장 단위·partial index·non-circular audit 중심은 아님 |

판정: UCA/VALU, HAWK, UrBench는 “감시·도시 도메인에서 VLM이 어렵다”는 동기 근거로 매우 중요하다. ForeSea는 최신 직접 인접 연구로 반드시 언급하되, 본 연구의 DB 시스템 기여와 구분해야 한다.

### 2.4 GraphRAG / multimodal RAG

| 연구 | 핵심 내용 | 본 연구와의 차이 |
|---|---|---|
| Microsoft GraphRAG | text corpus에서 entity/relation graph와 community summary를 이용한 RAG | 주로 텍스트 corpus의 전역 요약/QA. 감시 영상 센서 predicate DB 구조 아님 |
| LightRAG | graph+vector를 결합한 경량 RAG | text/document RAG 중심 |
| RAG-Anything / multimodal graph RAG 계열 | multimodal document를 entity/graph로 연결 | multimodal document QA 중심. 도시 감시 센서·영상 evidence layer의 storage/index 실험과 다름 |

판정: GraphRAG는 본 연구의 주력 비교축으로 올리기보다 boundary/negative result로 두는 것이 안전하다. 현재 본 연구의 KG 실험은 새로운 독립 신호를 만들지 못했고, sensor/caption 정보를 그래프로 재표현한 수준에 가깝다.

---

## 3. 본 연구의 확실한 결론으로 남길 수 있는 것

현재 실험 체계에서 확실하게 주장 가능한 결론은 다음이다.

1. **비순환 워크로드가 필요하다.**  
   filter, relevance, document가 같은 라벨에서 나오면 prefilter 우위가 구성상 보장될 수 있다. 본 연구는 이를 collapse 실험으로 보였고, 522 tri-source에서 소스 분리를 구현했다.

2. **hard constraint에서는 prefilter가 강하다.**  
   시간·위치·센서 조건처럼 반드시 만족해야 하는 조건에서는 먼저 후보를 거르는 구조가 효과적이다. 522와 MEVA에서 재현된다.

3. **soft intent에서는 prefilter 효과를 과장하면 안 된다.**  
   의미적으로는 맞지만 metadata 조건을 만족하지 않는 결과가 유효할 수 있는 경우, prefilter가 관련 결과를 제거할 수 있다. 이 효과는 결합도와 질의 성격에 의존한다.

4. **실제 predicate는 random mask와 다르다.**  
   실제 센서·시공간 조건은 임베딩 공간에서 군집성을 가지며, 동일 선택도 random mask로 filtered ANN을 평가하면 recall을 과대평가할 수 있다.

5. **저장 단위는 데이터셋/encoder 정합에 따라 달라진다.**  
   522에서는 clip-caption이 Pareto 효율적이고, MEVA에서는 frame-vector가 유리하다. 단, encoder 선택이 저장 단위 선택과 결합되어 있으므로 스코프를 “실무적 storage design comparison”으로 둔다.

6. **관계형 DB 구현에서는 partial/local index 정책이 필요하다.**  
   선택적 predicate에서는 global index+WHERE가 recall 또는 latency 문제를 만든다. partial/local index와 hot/cold 손익분기 규칙은 실제 DB 설계 기여다.

7. **검색 구조 차이가 답변 품질로 항상 직결되지는 않는다.**  
   evidence 품질은 답변에 중요하지만, corpus scale, VLM perception, answer bias가 검색 효과의 전파를 제한한다.

---

## 4. 가장 필요한 보강 설계안

### P0. 관련연구 대비 표를 원고 앞쪽에 넣어야 한다

현재 원고의 관련연구 설명은 충분히 길지만, 심사자가 빠르게 차이를 이해하기 어렵다. 다음 축의 comparison matrix가 필요하다.

| 축 | 기존 VDBMS | 기존 filtered vector search | 기존 감시 VLM benchmark | 본 연구 |
|---|---|---|---|---|
| 평가 대상 | query processing / tracking | ANN+structured filters | VLM/model understanding | storage/index/retrieval structure |
| 질의 | object/track SQL류 | vector+attribute filter | QA/caption/grounding | natural language + sensor/spatiotemporal predicate |
| 데이터 | video frames/tracks | generic embeddings | surveillance video-language | video + caption + sensor metadata + qrels |
| 모델 | detector/tracker 최적화 | ANN index | VLM/LMM 성능 비교 | model fixed, DB structure varied |
| 지표 | latency/cost/F1 | recall/QPS/latency | QA/caption/grounding score | nDCG/recall/latency/storage/answer propagation |
| 타당성 | task-specific | filter benchmark | human annotation | non-circular audit, strict/semantic qrels |

효과: “우리 논문이 어느 기존 연구와 겹치고 어디서 다르냐”가 한 장에 정리된다.

### P0. Contribution을 세 문장으로 재고정해야 한다

권장 contribution:

1. **Validity contribution**: source-separated non-circular multimodal surveillance retrieval workload.
2. **Design-space contribution**: storage unit, filter placement, hybrid retrieval, index structure를 accuracy·latency·storage로 비교.
3. **Operational DB contribution**: real-predicate filtered vector search에서 partial/local index와 hot/cold policy 도출.

이렇게 쓰면 “모델 논문이 아니다”가 분명해진다.

### P1. 저장 단위 비교의 encoder confounding을 줄이는 보조 실험

현재 저장 단위 비교는 실무적으로 타당하지만, 심사자가 “clip-caption은 bge-m3, frame-vector는 CLIP이므로 storage unit이 아니라 encoder 차이 아닌가?”라고 물을 수 있다.

보강안:

- CLIP text encoder로 caption을 임베딩한 `clip-caption(CLIP-text)` 추가.
- CLIP image encoder로 frame-vector와 비교.
- 가능하면 522와 MEVA에서 같은 표에 추가.

목적:

- 저장 단위 효과와 encoder 효과가 완전히 분리되지는 않더라도, “같은 CLIP 계열 안에서도 caption vs frame 차이가 어떻게 나는지”를 보여줄 수 있다.

시간이 부족하면 실험 대신 caveat를 본문에 명시한다.

### P1. 결과 요약을 “regime table”로 압축해야 한다

각 결과를 따로 설명하면 복잡하다. 아래 형태의 regime table이 필요하다.

| regime | 권장 구조 | 근거 |
|---|---|---|
| hard constraint | prefilter/local candidate search | 522, MEVA strict |
| soft intent + low coupling | vector-only 또는 cautious filtering | semantic qrels |
| real correlated predicate | random-mask 평가 금지 | filtered-ANN collapse |
| selective predicate | partial/local index | pgvector, MIRIS |
| broad predicate | global+postfilter | hot/cold policy |
| caption weak domain | frame-vector | MEVA storage unit |
| caption aligned domain | clip-caption | 522 storage unit |

효과: 논문 결론이 “몇 개 수치의 나열”이 아니라 설계 지침으로 보인다.

### P1. GraphRAG/KG는 주력 baseline이 아니라 boundary result로 처리

GraphRAG를 주력으로 넣으면 기존 GraphRAG 논문과 비교해야 하고, 본 연구의 DB 설계 프레이밍이 흐려진다. 현재 KG 결과는 독립 신호가 약하므로 다음처럼 처리한다.

> We also tested a KG-style extension, but when graph edges are derived from the same sensor/caption channels, the graph does not provide an independent retrieval signal. Therefore, we treat graph-structured retrieval as a boundary case rather than a primary baseline.

### P2. 네이티브 QA 데이터셋 추가는 선택 사항

HAWK, SurveillanceVQA, ForeSea류는 “VLM-QA” 이름에는 매력적이지만, 본 연구의 DB contribution을 흐릴 수 있다.

추가한다면 목적은 하나다.

- “우리 evidence layer가 native QA 데이터에서도 도움이 되는가?”를 소규모 sanity check로만 사용.

그러나 2026-07-20 마감 기준으로는 새 QA 데이터셋을 넣기보다 기존 522+MEVA+MIRIS 결과를 정리하는 편이 안전하다.

---

## 5. 원고에서 강화해야 할 표현

### 좋은 표현

> 본 연구는 감시 영상 이해 모델을 새로 제안하는 것이 아니라, 고정된 VLM/LLM 환경에서 DB evidence layer의 저장·색인·검색 구조가 검색 품질과 답변 지원 가능성에 미치는 영향을 평가한다.

> 기존 비디오 DB 연구가 객체·트랙 질의처리 비용을 줄이는 데 집중했다면, 본 연구는 자연어 의미 조건과 센서·시공간 predicate가 결합된 VLM-QA evidence retrieval workload를 다룬다.

> 기존 filtered vector search 연구가 일반 embedding과 attribute filter의 알고리즘 효율을 다룬다면, 본 연구는 실제 감시 센서 predicate가 만드는 correlation과 random-mask 평가 편향, 그리고 관계형 DB 구현 정책을 실측한다.

> 기존 감시 VLM benchmark가 어떤 모델이 영상을 이해하는가를 묻는다면, 본 연구는 모델을 고정한 상태에서 어떤 DB 구조가 좋은 증거를 전달하는가를 묻는다.

### 피해야 할 표현

- “최초의 멀티모달 감시 VLM-QA 연구”
- “GraphRAG보다 우수”
- “VLM-QA end-to-end 성능을 index가 결정”
- “MEVA/MIRIS도 522와 동일한 tri-source”
- “prefilter가 항상 최선”
- “저장 단위 효과가 encoder와 완전히 분리됨”

---

## 6. 최종 권고

추가 데이터셋을 더 늘리는 것보다, **관련연구 대비 차이와 설계 지침을 보이는 원고 구조 보강**이 우선이다.

우선순위:

1. Related-work comparison matrix 추가.
2. Contribution을 validity / design-space / operational policy 3개로 재정렬.
3. Regime table 추가.
4. 저장 단위 비교의 encoder caveat 또는 CLIP-text caption 보조 실험 추가.
5. GraphRAG/KG는 boundary result로 축소.
6. MEVA/MIRIS는 “제2 flagship”이 아니라 외적타당성/구현 검증으로 표현.

이렇게 정리하면 본 연구는 기존 논문과 직접 충돌하지 않고, 오히려 세 연구 흐름의 빈칸을 메우는 DB 시스템 논문으로 설득력을 갖는다.

