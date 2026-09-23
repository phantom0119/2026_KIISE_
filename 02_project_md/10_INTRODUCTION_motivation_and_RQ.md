# 10 — INTRODUCTION: 동기·Research Gap·RQ 통합 정본

## 0. 머리말

이 문서는 2026_KIISE 논문의 Introduction 관련 기록(연구 동기, 사회적 문제, Research Gap, Research Question, 기여)을 하나의 단일 정본으로 통합·관리하기 위한 문서다.

**통합 출처** (원본은 아래 경로로 이관 예정):

| 원본 파일 | 아카이브 경로 |
|---|---|
| 000_Introduction.md (2026-07-16, 구 통합 정본) | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/000_Introduction.md` |
| 100_INTRO_topic_selection_rationale.md (2026-07-06) | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/100_INTRO_topic_selection_rationale.md` |
| 770_INTRO_structure_and_draft_20260714.md | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/770_INTRO_structure_and_draft_20260714.md` |
| 780_INTRO_filtered_vector_search_factcheck_20260714.md | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/780_INTRO_filtered_vector_search_factcheck_20260714.md` |
| 800_Introduction_20260714.md | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/800_Introduction_20260714.md` |

**SYNC 기준: paper_final.pdf(2026-07-23) + 2026-07-28 검증 세션.** 본 문서의 모든 수치·RQ 구조·설계 축 서술은 제출 논문 정본(manuscript/paper_final.pdf, 총 21쪽 = 접수양식 1쪽 + 본문)을 절대 우선으로 한다. 소스 문서의 서술이 논문과 상충하는 경우 논문 기준으로 고치되, 의미 있는 이력은 `[정정 2026-07-28: ...]` 형태로 남긴다.

---

# 1부. 현행 정리

## 1.1 확정 서지 정보와 논문 정본 기준

- **확정 제목(국문)**: 종단형 멀티모달 RAG 파이프라인 성능 향상을 위한 비순환 평가 및 검색 품질-비용에 대한 실증 연구
- **확정 제목(영문)**: An Empirical Study of Non-circular Evaluation and Retrieval Quality-Cost for Enhancing the Performance of End-to-End Multimodal RAG Pipeline
- **코퍼스 정본**: 3,000 clips / 85 queries / strict qrels 6,809 / semantic qrels 24,872
- **설계공간 구성 산식**: 유효 데이터-계획 조합 1×4 + 4×3 = 16 × 색인 설정 7 = **112 구성**
- 러닝 헤드 p.7 이후에 구제목이 잔존하므로 재제출/개정 시 수정해야 한다.

  [정정 2026-07-28: 100_INTRO의 권장 제목 "멀티모달 도시 감시 데이터를 위한 하이브리드 VLM-DB 검색 워크로드 설계와 저장·색인 구조 비교" 및 대체 제목 2종은 초기 후보였으며, 제출본에서 위 확정 제목으로 대체되었다.]

### 2026-07-28 확정 용어 결정 (현 제출 PDF에는 미적용 — 보고서·향후 개정 원고용)

- '데이터베이스 계층' → **'벡터 데이터베이스 계층'**
- '증거(evidence)' 전면 치환:
  - DB가 반환하는 것 = **상위 k 검색 결과**
  - VLM 입력 = **검색 문맥(retrieved context)**
  - 정답 판정 = **관련 클립 / 검색 정답 집합**
  - RQ6 3관문 = **'관련 클립 회수 → 검색 문맥 인식 → 과제 편향'**
- **클립 조작적 정의**: 데이터셋 배포 mp4 1파일 = 1클립 (MEVA[20] 계보로 방어. 단 TTA 사전 미등재이며, AI Hub 공식 페이지는 '영상(mp4)' 표기임에 유의)

본 문서 이하에서는 새 용어를 기본으로 쓰고, 이력 인용 시 구 용어(evidence layer, evidence packet)를 괄호로 병기한다.

## 1.2 확정 Motivation

### 1.2.1 최종 판정 — 표현 수정 2건 (불변 규칙)

사용자가 제안했던 Research Gap의 큰 방향은 맞지만 다음 두 표현은 수정해야 한다. 이 판정은 이후 모든 원고·보고서에 적용되는 불변 규칙이다.

1. **"필터드 벡터 검색은 random mask로만 평가한다"는 사실이 아니다.** Filtered-DiskANN은 자연 라벨이 있는 세 개의 실세계 생산 데이터와 반합성 데이터를 함께 평가했고, ACORN은 predicate clustering과 query correlation을 직접 형식화하며 복잡한 멀티모달 데이터도 사용했다. UNIFY 역시 실제 속성이 포함된 데이터와 무작위로 생성한 속성을 함께 사용한다.
2. **"최초"와 "전무"는 체계적 문헌고찰 없이 사용하지 않는다.** 비디오 DB, 필터드 벡터 검색, VLM 벤치마크 각각에는 본 연구와 겹치는 부분이 있다. 본 연구의 공백은 각 요소의 개별 부재가 아니라, 이 요소들을 도시 감시 VLM-QA의 하나의 검증 가능한 DB 설계공간으로 통합한 연구가 드물다는 데 있다.

### 1.2.2 확정 Motivation 문장

> 대규모 도시 감시 영상 전체를 사용자 질의마다 VLM에 직접 입력할 수 없으므로, 벡터 데이터베이스 계층이 먼저 소수의 관련 클립을 상위 k 검색 결과로 선별해야 한다. 그러나 어떤 검색용 데이터 표현, 검색 계획, 검색 신호·순위 융합, 물리 색인과 배포 방식이 검색 정확도·지연·저장 및 구축 비용을 가장 잘 균형화하는지는 도메인과 predicate 성질에 따라 달라진다. 이 설계공간을 올바르게 비교하려면 질의 필터, 검색 문서와 정답 라벨이 같은 주석 계보를 공유하지 않는 평가 워크로드가 선행되어야 한다. 본 연구는 비순환 tri-source 프로토콜로 이 전제를 충족한 뒤, 고정된 생성 모델 환경에서 도시 감시 VLM-QA 벡터 데이터베이스 계층의 저장·색인·검색 구조와 답변 전파 경계를 실증한다.

[정정 2026-07-28: 구 정본(000)의 동일 문장은 "evidence layer / 증거 저장 단위 / evidence packet" 용어와 "메타데이터-벡터 결합 계획, ANN 색인과 DB 배치"라는 축 명명을 사용했다. 확정 용어와 논문 §4.2의 다섯 설계 축 명명(검색용 데이터/검색 계획/검색 신호·순위 융합/물리 색인/배포)으로 갱신했다.]

### 1.2.3 발표용 Motivation 불릿

- **운영상의 출발점**
  - 도시 감시 환경에서는 다수 카메라의 고화질 영상이 장기간 축적된다.
  - 사용자 질의마다 전체 원본 영상을 VLM에 입력하는 방식은 입력 길이, GPU 연산, 응답 지연과 추론 비용 때문에 현실적인 검색 구조가 될 수 없다.
- **필요한 시스템 계층**
  - 질의 서비스와 최종 VLM 사이에 벡터 데이터베이스 계층(구 database evidence layer)이 필요하다.
  - 이 계층은 원본 영상에서 오프라인으로 파생·저장한 프레임/이미지 벡터, VLM 생성 영상 설명문, 센서·시공간 메타데이터와 원본 참조를 검색한다.
  - 전체 코퍼스에서 소수의 관련 클립·이미지·설명문·센서 기록을 상위 k 검색 결과로 선별하고 검색 문맥(retrieved context)으로 구성해 최종 VLM에 전달한다.
- **핵심 DB 병목**
  - 같은 영상도 어떤 검색용 데이터 표현(영상 설명문, 대표 이미지, 이미지·설명문 결합, 다중 이미지, 이중 색인)으로 저장하는지에 따라 정확도·지연·저장비가 달라진다.
  - 자연어 의미 검색과 시간·장소·센서 predicate를 어떤 검색 계획(벡터 단독, 검색 전 조건, 검색 후 조건, 혼합)으로 결합하는지에 따라 recall과 latency가 달라진다.
  - Flat, HNSW, IVF 계열 물리 색인과 전역/조건별 부분 색인 배포는 구축 시간·색인 크기·검색 품질에 서로 다른 절충을 만든다.
  - 따라서 "가장 좋은 임베딩 모델"만 선택해서는 운영 구조를 결정할 수 없다.
- **기존 학계 연구 사이의 공백**
  - 비디오 DB 연구는 객체·트랙·시공간 이벤트 질의와 비디오 분석 비용 최적화를 발전시켰지만, 자유형 자연어 의미와 외생 센서 predicate로 VLM-QA용 검색 문맥을 구성하는 저장·색인 설계공간은 직접적인 평가 대상이 아니었다.
  - 필터드 ANNS 연구는 실제 라벨, predicate clustering과 query correlation까지 다루지만, 도시 감시 센서 predicate·영상 검색 데이터 표현·답변 계층을 하나의 워크로드에서 함께 평가하지 않는다.
  - 감시 VLM 연구는 모델의 영상 이해·이상행동 설명·QA 능력을 주로 평가한다. ForeSea처럼 검색 파이프라인을 포함하는 예외도 있지만, 저장 단위·ANN 색인·관계형 실행계획·색인 구축 및 저장 비용을 통제 비교하지 않는다.
- **평가 타당성이 먼저 필요한 이유**
  - predicate, 검색 document와 relevance가 같은 인간 주석에서 파생되면 검색 전 조건(prefilter)의 우위와 텍스트 검색의 높은 점수가 데이터 구성상 보장될 수 있다.
  - 잘못된 워크로드에서 얻은 결과는 실제 DB 구조의 우수성이 아니라 라벨 계보의 자기참조를 측정할 수 있다.
  - 따라서 DB 설계공간 실험 전에 세 요소의 생성 경로를 분리한 비순환 tri-source protocol과 기계 감사가 필요하다.
- **본 연구가 하려는 일**
  - 새로운 VLM이나 새로운 ANN 알고리즘을 제안하는 것이 목적이 아니다.
  - 생성 모델과 비교 조건을 고정하고, 비순환 워크로드 위에서 다섯 설계 축이 정확도·검색 계층 지연·저장 및 구축 비용에 미치는 영향을 통합 평가한다.
  - 최종 목적은 하나의 보편적 우승자를 선언하는 것이 아니라, predicate 선택도·결합도·질의 빈도와 설명문-질의 정합에 따른 **regime-specific DB 설계 지침**을 도출하는 것이다.

## 1.3 배경지식 없이도 이해되는 시스템 정의

### 1.3.1 사용자 질의는 어디로 입력되는가

"VLM 앞단의 벡터 데이터베이스 계층"은 사용자가 VLM에 직접 접속한다는 뜻이 아니다. 온라인 질의 흐름은 다음과 같다.

1. 사용자가 **질의 서비스**에 자연어 질문과 선택적인 시간·장소·센서 조건을 입력한다.
2. 질의 서비스는 자연어 의미 조건을 임베딩 질의로, 명시적 조건을 스칼라 predicate로 변환한다.
3. **벡터 데이터베이스 계층**이 저장된 코퍼스에서 관련 clip·frame·설명문·sensor record를 검색하고 순위를 정한다.
4. 검색기는 상위 k 검색 결과를 작은 **검색 문맥(retrieved context)**으로 구성한다.
5. VLM은 전체 영상 아카이브가 아니라 **사용자 질문과 검색 문맥만** 입력받아 최종 답변을 생성한다.

즉, VLM은 최종 사용자 인터페이스라기보다 검색 결과를 읽어 답을 만드는 마지막 생성 계층이며, 사용자의 요청은 먼저 질의 서비스와 벡터 데이터베이스 검색 계층을 거친다.

### 1.3.2 "전체 코퍼스"에는 무엇이 저장되는가

전체 코퍼스는 원본 CCTV 파일 자체만을 뜻하지 않는다. 운영 관점에서는 다음 자료가 clip/frame 식별자와 timestamp로 연결된다.

- 원본 비디오 또는 원본을 가리키는 URI·파일 경로
- clip/frame 식별자와 촬영 시각·카메라·교차로 정보
- 대표 이미지 임베딩 또는 클립별 다중 이미지 임베딩
- 픽셀만 본 VLM이 오프라인으로 생성한 영상 설명문과 그 텍스트 임베딩
- 질의 시 필터링할 수 있는 센서·시공간 메타데이터
- ANN 색인과 텍스트·메타데이터 보조 색인

본 연구의 검색용 데이터 다섯 형태(영상 설명문, 대표 이미지, 이미지·설명문 결합, 다중 이미지, 설명문·이미지 이중 색인)는 위 파생 자료 중 무엇을 검색 단위로 물질화할지를 나타낸다. 원본 영상 전체를 벡터 DB 내부에 복제해야 한다는 뜻은 아니다. 클립은 데이터셋 배포 mp4 1파일 = 1클립으로 조작적으로 정의한다.

[정정 2026-07-28: 구 문서들의 저장 단위 명칭 `clip-caption / frame-vector / multi-vector / dual-index`(4종)는 개발기 명명이다. 논문 §4.2 축①의 확정 명칭은 **영상 설명문 / 대표 이미지 / 이미지·설명문 결합 / 다중 이미지(클립당 최대 3) / 설명문·이미지 이중 색인(RRF k=60)**의 5종이다.]

### 1.3.3 검색 문맥(구 evidence packet)의 정의

검색 문맥은 한 개의 벡터가 아니라, 최종 VLM이 답변 근거로 사용할 수 있도록 상위 k 검색 결과를 묶은 제한된 크기의 자료 구조다. 최소 구성은 다음과 같다.

- `clip_id`, `camera_id`, timestamp와 원본 위치
- 상위 후보 이미지 또는 짧은 클립
- 픽셀 기반 VLM 영상 설명문
- 질의와 관련된 센서·시공간 메타데이터
- 검색 점수·순위와 검색 전략
- provenance와 추적 가능한 원본 참조

따라서 검색 문맥의 품질은 "관련 클립이 포함됐는가", "필수 predicate를 만족하는가", "불필요한 distractor가 얼마나 적은가", "답변 근거를 역추적할 수 있는가"로 평가해야 한다.

## 1.4 Research Gap 사실검증

| 제안한 주장 | 판정 | 논문에 사용할 안전한 표현 |
|---|---|---|
| 비디오 DB는 주로 객체 탐지·트랙 질의 효율화에 집중한다 | **대체로 맞지만 범위 보정 필요** | NoScope와 BlazeIt은 객체 기반 분류·집계·limit 질의를, Spatialyze는 객체와 지리·시공간 DSL을, EQUI-VOCAL은 scene graph 기반 복합 이벤트 질의 합성을 다룬다. 따라서 "객체 탐지만 다룬다"가 아니라 "VLM-QA용 자유형 의미 검색+외생 센서 predicate+검색 문맥 구성의 물리 설계 비교가 주된 평가 대상은 아니다"라고 쓴다. |
| 필터드 벡터 검색은 random mask로만 평가하며 clustering/correlation을 반영하지 않는다 | **그대로는 틀림** | Filtered-DiskANN은 자연 라벨 실데이터를 사용하고 random label의 비현실성을 직접 지적한다. ACORN은 predicate clustering과 query correlation을 형식화하고 멀티모달 데이터에서 평가한다. 본 연구의 공백은 "상관성의 미고려"가 아니라 "실제 도시 센서 predicate와 동일 선택도 random 대조군을 짝지어 VLM 검색 문맥·DB 배포까지 평가하지 않음"이다. |
| 감시 VLM 벤치마크는 모델 능력에 집중하고 DB 설계 변수 비교가 부족하다 | **대체로 맞음** | UCA/VALU와 HAWK는 모델·태스크 중심이다. 다만 ForeSea는 tracking→embedding index→top-k→VideoLLM 파이프라인을 포함하므로 예외를 명시한다. 차별점은 retrieval의 존재 여부가 아니라 storage unit·index family·filter plan·backend·build/storage cost의 통제 비교 여부다. |
| 모델을 고정하고 DB 설계공간을 최초로 정식화·실증한다 | **방향은 맞지만 '최초'는 삭제** | "본 연구가 검토한 선행 범위에서 개별적으로 다뤄진 축들을 비순환 도시 감시 VLM-QA 워크로드에서 통합적으로 정식화하고 실증한다"라고 쓴다. |

### 1.4.1 비디오 DB 계열의 정확한 공백

NoScope는 고정 영상과 목표 객체가 주어진 이진 분류 질의를, BlazeIt은 객체 탐지 출력에 대한 집계 및 limit 질의를 가속한다. Spatialyze는 지리 메타데이터와 객체의 물리 행동을 이용한 시공간 비디오 분석을 제공하며, EQUI-VOCAL은 사용자 예시로부터 scene graph 기반 복합 이벤트 질의를 합성한다. VIVA는 혼합 데이터 최적화와 저장·실행의 공동 최적화까지 제안한다.

따라서 비디오 DB 연구를 "객체 탐지만 하는 연구"로 축소해서는 안 된다. 본 연구가 메우는 구체적 공백은 **코퍼스 수준 자유형 자연어 의미 검색, 외생 센서 predicate, VLM용 검색 문맥, 검색용 데이터 표현과 ANN/RDB 물리 설계, 답변 전파를 동일 질의·정답 아래에서 함께 비교하는 것**이다.

### 1.4.2 필터드 벡터 검색 계열의 정확한 공백

Filtered-DiskANN은 세 개의 자연 라벨 생산 데이터와 다섯 개의 반합성 데이터를 함께 평가하며, 무작위 라벨은 실제 벡터-라벨 상관성을 반영하지 못한다고 명시한다. ACORN은 predicate를 통과한 벡터의 비균일 분포를 predicate clustering으로 정의하고, query correlation이 검색 성능을 바꾼다는 점을 이론과 실험에서 다룬다. UNIFY도 Paper와 WIT-Image의 실제 속성을 포함하지만, 나머지 데이터에는 무작위 수치 속성을 부여한다.

그러므로 본 연구는 "기존 연구가 clustering을 몰랐다"고 주장하지 않는다. 대신 다음 차이를 주장한다.

- 실제 교통·감시 센서와 시공간 predicate를 사용한다.
- 동일 predicate 선택도를 유지한 matched random mask를 대조군으로 둔다.
- 단순 QPS-recall을 넘어 predicate 군집성에 따른 부호와 기전을 비교한다.
- 다섯 가지 검색용 데이터 표현(영상 설명문·대표 이미지·이미지·설명문 결합·다중 이미지·이중 색인)을 함께 비교한다.
- 전역 색인과 조건별 부분 색인 배포, 그리고 전용 엔진 경로(Milvus/Weaviate의 전수 검색 자동 전환 규칙 포함)를 교차 확인한다.
- 검색 차이가 고정 VLM 답변으로 전파되는 조건과 실패 경계를 별도로 검증한다.

[정정 2026-07-28: 구 문서의 "pgvector의 global+WHERE·iterative scan·partial/local index 교차 확인" 서술은 개발기 실험 범위다. 제출 논문의 배포 축(축⑤)은 전역/조건별 부분 색인 비교와 Milvus/Weaviate 자동 전환 규칙(필터율≥92.3% 또는 조건 만족 벡터<40,000이면 전수 검색)으로 정리되었다(§1.7 RQ5 참조).]

### 1.4.3 감시 VLM·VideoRAG 계열의 정확한 공백

UCA/VALU는 시간적 문장 접지와 캡셔닝 등 감시 video-language understanding 태스크에서 모델을 비교하고, HAWK는 오픈월드 이상행동 설명과 QA 모델을 제안한다. 이들은 모델의 인지·언어 능력을 평가하는 연구다. ForeSea는 더 직접적으로 tracking, multimodal embedding index, top-k retrieval과 VideoLLM을 연결하므로 "감시 VLM 연구에는 retrieval이 없다"는 주장도 사용할 수 없다.

안전한 차별성은 다음과 같다.

> 기존 감시 VLM·VideoRAG 연구는 검색 또는 답변 정확도와 temporal grounding을 중심으로 평가한다. 본 연구는 생성 모델을 비교 대상으로 삼기보다, 동일 질의·정답 아래에서 검색용 데이터 표현, 검색 계획(필터 배치), ANN 색인 계열, 배포 방식, 검색 계층 지연, 색인 크기와 구축 비용을 조작 변수로 둔다.

ForeSea 관련 뉘앙스(100_INTRO에서 보존): ForeSeaQA는 감시 도메인 멀티모달·시간 grounding 비디오 QA 벤치마크(6개 하위 과제, 텍스트 전용·멀티모달 질의 양쪽 평가)이고, ForeSea 시스템은 추적 모듈→멀티모달 임베딩 색인→상위 K 검색→VideoLLM의 3단계 플러그앤플레이 파이프라인이다. 따라서 "모델 정확도만 평가"라는 표현은 벤치마크(ForeSeaQA)에는 맞지만 시스템(ForeSea)에는 부분적으로만 맞다. 그럼에도 저장 스키마·색인 구조에 따른 시스템 성능(처리량·비용·지연) 비교가 없다는 핵심 논지는 유효하다.

UrBench 관련(100_INTRO에서 보존): UrBench는 정지 이미지(스트리트 뷰·위성뷰) 기반 다중 시점 도시 시나리오 LMM 평가 벤치마크(11.6K 질문, 4개 과업 차원·14개 과업 유형)로, 비디오·시간적 grounding·RAG 검색 파이프라인과는 무관하다. 도메인 어휘("urban")는 겹치지만 데이터 양식과 문제 축이 모두 달라 본 연구와의 거리는 ForeSea보다 멀다.

## 1.5 Filtered Vector Search 기술 배경 (사실검증 완료본)

### 1.5.1 용어·서술 불변 규칙 (780 사실검증 결과 — 전량 보존)

1. **"High Selectivity" 용어 금지·수식 정의 사용.** "필터링된 결과 상위 데이터의 개수가 너무 적으면(높은 선택도, High Selectivity)" 같은 표현은 혼동을 부른다. 선택도는 수식으로 `s = |σ_p(D)| / |D|`를 정의하고, `s`가 작을수록 선택적 predicate(highly selective predicate; low pass ratio)라고 쓴다.
2. **Prefilter 병목의 정확한 서술.** "prefilter는 필터 결과가 작으면 HNSW를 못 쓰고 brute force로 전락한다"는 부분적으로만 맞다. 정확한 표현: 단순 prefilter는 predicate별 부분집합에 대한 별도 vector index가 없으면, 필터 통과 집합 위에서 exact scan을 수행하거나 임시 후보 집합을 만들어야 한다. 이 방식은 작은 집합에서는 오히려 빠를 수 있지만, predicate가 많고 동적이면 index 재사용성과 운영 비용 문제가 생긴다. 반대로 필터를 HNSW 탐색 내부에 단순히 넣으면 그래프 연결성이 깨져 탐색 품질과 속도가 저하될 수 있다. 즉 prefilter의 병목은 항상 "brute force라서 느리다"가 아니라 다음 다섯 가지로 정리한다: 부분집합별 index 부재 / predicate 조합 폭증 / 그래프 연결성 단절 / build·storage 비용 / 동적 predicate 운영 비용.
3. **Postfilter 서술은 원문대로 정확.** vector top-K를 먼저 뽑고 metadata 조건을 나중에 적용하면 결과가 부족하거나 recall이 떨어진다. pgvector 공식 문서도 approximate index에서는 filtering이 index scan 후 적용되므로 조건에 맞는 결과가 부족할 수 있고, 이를 완화하기 위해 iterative scan을 제공한다고 설명한다.
4. **Single-stage/in-graph filtering 서술 주의.** "최신 연구는 single-stage hybrid search를 고안하고 있다"는 대체로 맞다(ACORN, Filtered-DiskANN, Qdrant/Weaviate ACORN류, Milvus filtered search, Faiss IDSelector). 다만 시스템마다 구현이 다르므로 "모두 같은 방식"이라고 쓰면 안 된다.
5. **"기존 연구는 random mask만 사용한다"는 표현은 사용하지 않는다** (§1.2.1 판정 1과 동일).

### 1.5.2 네 가지 기술 패러다임

**패러다임 1 — Two-stage filtering (prefilter vs postfilter).** Prefilter는 metadata 조건으로 후보를 먼저 줄인 뒤 vector ranking을 수행한다. hard constraint에서는 정확한 결과 집합을 보장하기 쉽지만, 부분집합별 index가 없으면 exact scan이나 임시 후보 처리에 의존할 수 있고, predicate 조합이 많아지면 운영 비용이 커진다. Postfilter는 global vector index로 top-K 후보를 먼저 찾고 그 뒤 metadata 조건을 적용한다. 구현은 단순하지만, 필터 조건을 만족하는 결과가 top-K 안에 충분히 없으면 최종 결과가 부족하거나 recall이 떨어진다.

**패러다임 2 — Single-stage / in-graph filtered search.** 최근 filtered ANN 연구는 vector search와 scalar filtering을 별도 단계로 나누지 않고 ANN 탐색 과정 안에 predicate 평가를 통합하는 방향으로 발전한다. 예: Filtered-DiskANN(filter-aware graph construction/search), ACORN(HNSW 기반 predicate subgraph traversal), Qdrant/Weaviate ACORN류, Faiss IDSelector.

**패러다임 3 — Selectivity-aware / cost-based query planning.** 통과 비율이 매우 낮은 predicate는 local/partial index 또는 metadata-first plan이 유리할 수 있고, 통과 비율이 높으면 global vector index+postfilter나 iterative scan이 충분할 수 있으며, 중간 영역에서는 recall·latency·index build/storage 비용의 trade-off가 생긴다. AlloyDB filtered vector search처럼 optimizer가 selectivity·distribution·index availability를 보고 pre/post/inline filtering을 선택하는 흐름이 이에 해당한다.

**패러다임 4 — RDB-native vector search와 hardware acceleration.** pgvector, AlloyDB, ClickHouse/DuckDB 계열은 SQL WHERE 조건과 vector distance ordering을 함께 처리하려 한다. Faiss GPU, NVIDIA cuVS/CAGRA, VecFlow 같은 하드웨어 가속 연구는 대규모 vector search의 latency·throughput 문제를 낮은 수준에서 해결하려 한다. 하드웨어 가속은 본 연구의 직접 기여가 아니므로 Introduction에서는 "대규모 vector search의 또 다른 발전 방향"으로만 짧게 언급한다.

### 1.5.3 관련 연구 정리표

**Filtered vector search 알고리즘 연구**

| 연구 | venue/status | 핵심 내용 | 본 연구와 연결 |
|---|---|---|---|
| Filtered-DiskANN | WWW 2023 | label/filter를 고려한 graph-based ANNS | 필터 조건이 붙은 ANN의 대표 연구 |
| ACORN | SIGMOD/PACMMOD 2024 | HNSW 기반 predicate-agnostic hybrid search, predicate subgraph traversal | in-graph filtering 최신 핵심 연구 |
| CAPS | arXiv 2023 | graph가 아닌 partition 기반 constrained ANNS | graph 외 접근법 |
| UNIFY (Unified Index for Range Filtered ANN) | PVLDB 2025 | range filter와 ANN 통합 index | scalar/range predicate 확장 |
| FANNS survey | arXiv 2025 | vector-scalar hybrid data에서 filtered ANNS 분류 | 관련연구 구조화에 유용 |

**Vector DB / RDB 통합 연구**

| 연구/시스템 | 핵심 내용 | 본 연구와 연결 |
|---|---|---|
| VBASE, OSDI 2023 | vector similarity search와 relational operator를 relaxed monotonicity로 통합 | vector+relational query 통합의 대표 DB 연구 |
| pgvector 0.8+ | iterative index scan으로 overfiltering 완화 | 개발기 pgvector 실험과 연결 |
| AlloyDB filtered vector search | optimizer가 selectivity, distribution, index availability를 보고 pre/post/inline filtering 선택 | cost-based vector query optimization 흐름 |
| Qdrant | vector index와 payload index 결합, ACORN algorithm 옵션 | payload metadata filtering 시스템 사례 |
| Weaviate | HNSW에서 sweeping/acorn filter strategy 지원 | ACORN류 실용 시스템 사례; 논문 RQ5의 자동 전환 규칙 대상 |
| Milvus | standard filtering과 iterative filtering 제공 | filtered search 구현 사례; 논문 RQ5의 자동 전환 규칙 대상 |

### 1.5.4 차별성 문장 (확정)

> 기존 filtered vector search 연구는 일반 embedding과 attribute filter를 대상으로 vector-scalar hybrid query를 최적화하는 데 초점을 둔다. 반면 본 연구는 도시 감시 VLM-QA에서 시각·텍스트 검색용 데이터와 실제 센서·시공간 metadata predicate가 결합될 때 검색용 데이터 표현, 검색 계획, 색인 구조와 배포가 어떻게 달라져야 하는지를 평가한다. 특히 실제 predicate가 동일 선택도 random mask와 다른 recall-latency behavior를 만들 수 있음을 보이고(실측 군집 조건에서 전역 색인 재현율 손실 최대 0.627 대 무작위 대조 최대 0.047 변동), 벡터 데이터베이스 계층을 위한 저장·검색·부분 색인 배포 지침을 도출한다.

(영문판, 이력 보존: "Existing filtered vector search studies focus on optimizing vector-scalar hybrid queries over general benchmark embeddings and attributes. In contrast, our study asks how these design choices behave in multimodal urban surveillance VLM-QA, where dense visual/text evidence must be combined with real sensor and spatiotemporal predicates. We show that real predicates induce recall-latency behavior that differs from same-selectivity random masks, and derive storage, filtering, and partial-index deployment guidelines for the evidence layer." — 'evidence layer' 용어는 향후 개정 시 'vector database layer' 계열로 치환.)

## 1.6 최종 Problem Statement

> 전체 원본 데이터를 사용자 질의마다 VLM에 입력하는 대신, 도시 감시 멀티모달 코퍼스에서 필요한 관련 클립을 더 낮은 검색 비용과 지연으로 선별하면서 검색 정확도와 최종 답변 지원 가능성을 보존하려면 어떤 검색용 데이터 표현, 검색 계획, 검색 신호·순위 융합, 물리 색인 및 배포 정책을 선택해야 하는가? 그리고 이 비교가 특정 구조에 유리하도록 구성되지 않았음을 어떻게 검증할 것인가?

이 문제는 다음 두 층으로 나뉜다.

1. **평가 타당성 층:** predicate, document, relevance의 생성 계보를 분리해 구조 비교가 순환적으로 결정되지 않도록 한다.
2. **DB 설계 층:** 타당한 워크로드 위에서 다섯 설계 축의 정확도·지연·비용 절충을 비교한다.

## 1.7 확정 Research Questions (SYNC: paper_final.pdf §4.2, §5.2)

확정 구조는 **검증 RQ1 → 설계 RQ2-RQ5 → 전파 RQ6**이다. 설계 RQ는 벡터 데이터베이스 계층의 다섯 설계 축(§4.2)과 다음과 같이 매핑된다(5축↔4RQ: RQ5가 물리 색인과 배포를 겸임한다).

| RQ | 설계 축 | 축 내용(정본) |
|---|---|---|
| RQ1 (검증) | — | 순환 평가의 진단·수리·통제 재현 |
| RQ2 | ① 검색용 데이터 | 영상 설명문 / 대표 이미지 / 이미지·설명문 결합 / 다중 이미지(클립당 최대 3) / 설명문·이미지 이중 색인(RRF k=60) |
| RQ3 | ② 검색 계획 | 벡터 단독 / 검색 전 조건 / 검색 후 조건(상위 200 후보) / 혼합(영상 설명문 전용) |
| RQ4 | ③ 검색 신호·순위 융합 | 메타데이터 단독 / BM25 / 벡터 / BM25-벡터 RRF |
| RQ5 | ④ 물리 색인 + ⑤ 배포 | Flat / HNSW(M=32, efC=200, efSearch{64,256}) / IVF-Flat(nlist=64, nprobe{8,32}) / IVF-PQ(m=32, 6bit); 전역 / 조건별 부분 색인 |
| RQ6 (전파) | — | 검색 품질 차이의 답변 전파 3관문 |

구성 산식: 유효 데이터-계획 조합 1×4 + 4×3 = 16 × 색인 설정 7 = 112 구성.

### RQ1 — 비순환 검증 (선행 조건)

질의 필터·검색 문서·정답 라벨이 같은 주석 계보를 공유할 때 평가가 어떻게 왜곡되며, 계보 분리와 기계 감사로 이를 차단할 수 있는가?

- 정본 결과: 순환 경로 수정 전후 성능이 0.9736→0.3174(VRU), 1.0000→0.8395(지능형 관제)로 붕괴해 순환성이 성능을 인위적으로 부풀렸음을 보인다.
- 통제 주입 실험: 기준 0.181에서 정답 필터 주입 시 1.000, 라벨 재진술 주입 시 0.854로 상승 — 순환 기전의 재현.

### RQ2 — 검색용 데이터 (축①, 표4)

- 기준(영상 설명문): 0.063 / 0.181, 1.15ms, 24.6MB
- 다중 이미지(클립당 최대 3): 0.101 / 0.352 (Δ+0.171 유의), 3.65ms, 68.4MB (기준 대비 2.8배)
- 설명문·이미지 이중 색인(RRF k=60): 0.089 / 0.293, 4.96ms, 93.0MB (최고 비용)
- 저장 비교 전체 BH p=0.112

### RQ3 — 검색 계획 (축②, 표5·6)

- 엄격 기준: 검색 전 조건 Δ+0.0983 유의 — 단, '자명한 결과'로 해석(필터가 정답 정의와 정합하는 구성)
- 의미론 기준: 벡터 단독 0.170 최고, 검색 전 조건 Δ=-0.0158 무의미
- 고결합 부분군(V≥0.3): Δ+0.1335
- UCA 129질의 외부 재현: 3/4

[정정 2026-07-28: 구 초안(770 §5)의 "hard metadata constraint에서는 prefilter가 유리하지만 soft intent에서는 신중해야 한다"는 방향성 서술은 정본 결과로 대체한다. 엄격 기준의 prefilter 이득은 유의하나 자명한 결과로 해석하며, 의미론 기준에서는 벡터 단독이 최고이고 prefilter 이득은 무의미하다.]

### RQ4 — 검색 신호·순위 융합 (축③, §5.2.4)

- **전 신호 독립 이득 없음**: 메타데이터 단독 0.218/0.217, BM25 0.017/0.050, 벡터 0.059/0.170
- 혼합 RRF 0.133 < 벡터 0.154 — 융합이 벡터 단독보다 낮음
- 지식그래프 재조합 Lift 중앙값 0.002 — 무이득

[정정 2026-07-28: 구 초안들의 "metadata-aware hybrid retrieval이 검색 재현율과 근거 품질을 개선하는지 평가한다"(100 기여 문장 초안)는 기대 서술이었다. 정본 결과는 hybrid(RRF)가 벡터 단독을 넘지 못했다는 부정적 결과이며, 이것이 논문의 실증 기여다.]

### RQ5 — 물리 색인 + 배포 (축④+⑤, 표7-10)

- 실측 군집 조건에서 전역 색인 재현율 손실 최대 0.627. 동일 선택도 무작위 대조는 최대 0.047 변동에 그침 → 무작위 대조 평가는 손실을 과소평가
- 조건별 부분 색인: 재현율 98.12~100% 회복
- **배포 규칙(정본)**: 전역 색인 재현율 목표 0.95 미달 시 조건별 부분 색인 또는 전수 검색으로 전환하고, 색인 갱신 시점까지의 예상 질의 수에 대한 선택도별 손익분기로 선택한다
- 실무 참조: Milvus/Weaviate는 필터율≥92.3% 또는 조건 만족 벡터<40,000이면 전수 검색으로 자동 전환

[정정 2026-07-28: 구 문서들의 `N* = build_cost / per-query latency saving` 형태 hot/cold predicate 정책(pgvector partial/local index 기반)은 개발기 정식화다. 정본 배포 규칙은 위와 같이 "전역 재현율 목표 0.95 + 예상 질의 수 선택도별 손익분기 + 엔진 자동 전환 규칙"으로 확정되었다.]

### RQ6 — 답변 전파 (전파, §5.2.6)

3관문(2026-07-28 확정 용어): **관련 클립 회수 → 검색 문맥 인식 → 과제 편향**.

- 답변 정확도 사다리: 무증거 31% → 무관 문맥 53% → 벡터 검색 67% → 대상 설명문 75%
- 잘 보이는 단일 시점 +15.2%p, 두 시점 동시 제공은 무이득
- 근사 색인 재현율 차이의 답변 전파는 표본 부족으로 **탐색적(미확립)**

[정정 2026-07-28: 구 문서들의 전파 경계 3요소 "corpus scale, VLM perception, answer bias"는 정본의 3관문 '관련 클립 회수→검색 문맥 인식→과제 편향'으로 재정식화되었다. 또한 "index 차이가 항상 답변 정확도로 바로 전파되지는 않음을 보인다"는 단정 서술은 "표본 부족으로 탐색적"으로 강도를 낮춘다.]

### [이력] 구 RQ 구조 (000 정본, 2026-07-16)

[정정 2026-07-28: 아래 구조는 제출 전 정식화 이력이며, 위 확정 RQ1-RQ6 구조로 대체되었다.]

- 평가 선행조건(Validity prerequisite): predicate·document·relevance가 같은 라벨 계보를 공유하면 검색 구조 비교가 어떻게 왜곡되며, tri-source separation과 기계 감사로 차단할 수 있는가? → 확정 RQ1로 승격
- RQ-S(Structure): 저장 단위(clip-caption, frame-vector, multi-vector, dual-index) / 검색(metadata-only, sparse/BM25, dense, prefilter, postfilter, hybrid) / 색인(Flat, IVF-Flat, HNSW, IVF-PQ) / 실행(Faiss, PostgreSQL+pgvector, Milvus, Weaviate) → 확정 RQ2·RQ3·RQ4·RQ5로 분해. 실행 기반은 독립 축에서 제외되고 RQ5의 배포 규칙·엔진 자동 전환 참조로 흡수
- RQ-ALC(Accuracy·Latency·Cost): 각 구조의 Pareto 절충 → 별도 RQ가 아니라 RQ2-RQ5 각각의 품질·지연·저장 비용 보고로 흡수. "latency·cost 주장은 검색·색인 계층으로 한정한다"는 주의는 유지
- RQ-M(Multimodal coupling and answer propagation): → 결합은 RQ2(이미지·설명문 결합, 이중 색인)·RQ4(신호 융합)로, 답변 전파는 RQ6으로 분해

## 1.8 핵심 Contributions — 과장 제거본

1. **평가 타당성:** predicate, document, relevance의 생성 계보를 분리한 비순환 tri-source 워크로드와 strict/semantic 이중 qrels(6,809 / 24,872), 기계 감사 절차를 제시한다.
2. **순환성 사례 연구:** 초기 자체 워크로드에서 코드 수준의 순환 경로를 진단하고, 수리 전후 성능 붕괴(0.9736→0.3174, 1.0000→0.8395)와 통제 주입 재현(0.181→1.000/0.854)으로 구조 비교가 무효화되는 기전을 보인다.
3. **실측 predicate 대조:** 실제 센서·시공간 predicate와 동일 선택도 random mask를 짝지어 전역 색인의 filtered-ANN 재현율 손실 차이(실측 최대 0.627 대 무작위 최대 0.047)를 측정하고, 조건별 부분 색인의 회복(98.12~100%)과 엔진별 기전을 교차 확인한다.
4. **DB 설계공간:** 다섯 설계 축 112 구성을 정확도·검색 지연·색인 크기·구축 비용 위에서 비교해 조건별 선택 지침과 배포 손익분기 규칙을 도출한다.
5. **답변 전파 경계:** 검색·색인 차이를 최종 VLM-QA 성능으로 과대 해석하지 않도록, 3관문(관련 클립 회수→검색 문맥 인식→과제 편향)이 구조 차이의 전파를 차단하는 경계를 보고한다. 근사 색인 차이의 답변 전파는 탐색적 결과로만 보고한다.

"최초", "완전한 독립", "전무", "모든 데이터셋에서 우월"과 같은 표현은 사용하지 않는다.

## 1.9 주장 범위와 한계 (불변 규칙 — 전량 보존)

- 본 연구는 **24시간 스트리밍 적재 및 온라인 임베딩 비용을 직접 벤치마크하지 않았다.** 운영 Motivation은 타당하지만, 결과는 우선 오프라인으로 물질화된 아카이브의 검색·색인 계층에 적용된다.
- 검색 latency는 생성 모델 추론을 제외한 격리 측정값이므로 end-to-end 응답시간으로 확대하지 않는다.
- 영상 설명문 계열과 이미지 벡터 계열의 비교(구 `clip-caption` 대 `frame-vector`)는 텍스트 인코더와 시각 인코더 선택을 포함하는 실무 설계 대비다. 저장 단위만을 격리한 encoder-controlled ablation으로 표현하지 않는다.
- ACORN과 Filtered-DiskANN이 correlation을 무시했다고 주장하지 않는다. 본 연구의 차이는 도시 센서 matched control과 VLM 검색 문맥 계층의 통합 평가다.
- UCA/VALU와 HAWK를 "DB가 없는 불완전 연구"로 평가하지 않는다. 평가 대상이 모델/태스크로 다르며 본 연구와 상보적이라고 서술한다.
- ForeSea에는 retrieval/indexing pipeline이 있으므로 "기존 감시 VLM에는 검색이 없다"고 쓰지 않는다.
- 현재 결과는 단일 보편 최적 구조보다 데이터·질의 regime에 따른 선택 규칙을 지지한다.
- (2026-07-28 추가) RQ3 엄격 기준의 검색 전 조건 이득(Δ+0.0983)은 유의하더라도 '자명한 결과'로 해석하며 구조 우위 주장에 쓰지 않는다.
- (2026-07-28 추가) RQ6의 근사 색인 재현율 차이→답변 전파는 표본 부족으로 탐색적(미확립) 결과로만 서술한다.

## 1.10 주제 선정 이력과 DBR 포지셔닝 (100_INTRO 고유 내용, 이력)

작성 기준일 2026-07-06, 2026-07-09 갱신. 주제 선정 방향은 유지된 채 연구 범위가 초기 retrieval workload 설계에서 `true multimodal retrieval + service evidence packet + fixed LLM/VLM answer-level control + 시내도로 CCTV index benchmark`까지 확장되었고, 이후 제출본의 tri-source 비순환 벤치마크로 수렴했다.

### 1.10.1 연구 수행 방향 (초기 설계)

- 특정 데이터셋·모델의 우수성 주장이 아니라, 데이터셋·embedding model·vector backend가 교체되어도 동일 query/qrels와 canonical schema 위에서 metadata-aware retrieval 구조를 비교할 수 있는 모듈형 VLM-DB 실험 프레임워크를 지향.
- 도시 감시/교통 안전 공개 데이터가 비디오·캡션·VQA·CoT·시간·장소·카메라 메타데이터를 포함하는 방향으로 진화 → 이질적 데이터를 어떤 저장·색인·검색 구조로 결합할 것인지가 독립적인 데이터베이스 연구 문제.
- 국제적으로 문서·영상 RAG 연구는 빠르게 발전했지만, 운영형 시스템에서는 필터 가능한 벡터 검색, 멀티벡터 저장 비용, 시공간 조인, 근거 제시 가능한 답변, 온라인 지연·비용이 병목으로 남아 있음.

### 1.10.2 국내(DBR) 동향 근거

DBR 2025~2026 공개 논문 31편 분포:

| 토픽 | 편수 | 비율 |
|---|---:|---:|
| 생성형 AI·LLM·RAG·Text-to-SQL | 8 | 25.8% |
| 컴퓨터비전·멀티모달·센싱 | 7 | 22.6% |
| 그래프 분석·GNN | 5 | 16.1% |
| 응용 예측·추천·문서 마이닝 | 5 | 16.1% |
| 시계열·데이터 품질·전처리 | 3 | 9.7% |
| 분산 데이터 처리·벡터 인덱스·시스템 엔지니어링 | 3 | 9.7% |

- DBR은 KCI 등재 학술지, 최근 발행 42권 1호(2026-04). 최신호에 교통 표지 인식, LLM 사건 분류, 균열 분류 퓨샷, 다국어 VLM 의료 시각 일관성, RAG 하이브리드 윈도우 청킹 등이 수록 — DBR이 이미 RAG·LLM·VLM·도시/환경 비전 응용을 수용.
- 최신 DBR에서 "전통적 DB 코어 이슈"보다 "AI-중심 데이터 활용"이 전면화. 반면 시계열·데이터 품질·전처리, 분산 처리·벡터 인덱스·시스템 엔지니어링 분포는 적음.
- 국내 흐름 세 갈래: (1) RAG/LLM 기반 검색 설계(하이브리드 RAG 챗봇, 윈도우 청킹, LLM 사건 분류), (2) VLM·멀티모달 이해(다국어 의료 VQA), (3) 도메인 특화 대규모 데이터 관리(데이터 레이크 자동화, 해양관측 검색, 침수 탐지, 교통 표지 인식).
- CCTV 프레임·센서 로그·문서 보고서를 하나의 멀티모달 DB 질의 계층으로 통합한 국내 DB 논문은 2025-2026 공개호 기준으로 뚜렷하게 보이지 않음 — 이 지점이 연구 공백.
- 포지셔닝: "새 VLM 제안"보다 도시 감시용 하이브리드 아키텍처, event-grounded retrieval/VQA benchmark, metadata filtering과 multivector retrieval의 trade-off 분석. "멀티모달 도시 감시 VLM-DB"를 단순 모델 성능 연구가 아니라 저장 구조·멀티인덱스·질의 처리·비용 관리까지 포함하는 데이터 관리 연구로 세우는 것이 가장 설득력 있는 문제 정의.

### 1.10.3 연구 공백 구성 요소 (초기 정리)

국내 흐름에 각각 존재하는 것: RAG 검색·청킹 최적화 / PGvector·HNSW 벡터 인덱스 최적화 / VLM·VQA 성능 평가 / LLM 사건 분류 / 도메인 영상·문서 응용. 그러나 다음을 동시에 다루는 연구는 희소: 영상 또는 키프레임 + 사건 보고서·상황 일지 + 정형 메타데이터(시간·장소·카메라·날씨·교통량) + 벡터·sparse·metadata filter 결합 + 검색 결과 기반 VQA·event grounding + latency·cost까지 포함한 DB 관점 평가.

### 1.10.4 후보 주제 비교 (선정 이력)

| 후보 | 장점 | 약점 | 투고 적합성 |
|---|---|---|---|
| 한국어 도메인 문서 RAG 벤치마크 | 데이터 확보 쉬움 | 기존 연구와 겹칠 위험 | 중간 |
| 프라이버시 보장 라이프로그 데이터 관리 | 연구 갭 큼 | 데이터 접근·IRB 부담 | 낮음 |
| 한국어 엔터프라이즈 Text-to-SQL | DB 접점 강함 | 스키마/질의셋 구축 시간 | 중간 |
| **멀티모달 도시 감시 VLM-DB** | DBR 트렌드·연구 공백 동시 만족 | 원천 데이터 구성·라벨 생성이 관건 | **높음** |
| 스트리밍 시계열 이상치 보정 | DB 코어에 가까움 | VLM/RAG 흐름과 분리 | 중간 |
| 그래프-RAG | 참신성 높음 | 그래프 데이터·평가 신규 구축 필요 | 낮음~중간 |

결론(당시): "대규모 완성형 벤치마크"가 아니라 "축소형 공개 데이터 기반 워크로드 정의와 구조 비교"로 좁힌다. → 제출본에서 3,000 clips / 85 queries 규모의 tri-source 벤치마크로 실현.

### 1.10.5 데이터셋 후보 목록 (이력)

- AI Hub 이상행동 CCTV 영상 (dataSetSn=171)
- 다각도 CCTV 생활안전 데이터 (dataSetSn=71953)
- 지능형 관제 서비스 CCTV 영상 데이터 2024 (dataSetSn=71850) — RQ1 순환성 사례에 사용(1.0000→0.8395)
- AI City Challenge 2025
- VRU-Accident (arXiv:2507.09815) — RQ1 순환성 사례에 사용(0.9736→0.3174)
- TUMTraf VideoQA (1,000 roadside traffic videos, 85K QA)
- 교차로 신호 체계·보행자·차량 이동 복합 데이터 (dataSetSn=522) — tri-source 구축 중심
- 교통문제 해결을 위한 CCTV 교통 영상(시내도로) (dataSetSn=165)

## 1.11 관리 정책

- Introduction·Motivation·Research Gap·RQ·Contribution의 개념 정본은 **이 파일(10_INTRODUCTION_motivation_and_RQ.md)**이다.
- 수치·RQ 구조의 정본은 paper_final.pdf(2026-07-23)이며, 본 파일은 그 SYNC 사본이다. 실험 수치가 바뀌면 결과 정본을 먼저 갱신하고, 그다음 본 문서의 표현 강도를 갱신한다.
- 과거 파일은 archive/legacy_premerge_20260728/으로 이관하며 삭제하지 않되, 새로운 주장이나 수치를 추가하지 않는다.
- 향후 개정 원고는 2026-07-28 확정 용어 결정(§1.1)을 적용한다. 현 제출 PDF에는 미적용 상태임을 혼동하지 않는다.

## 1.12 1차 근거 문헌

### 비디오 DB·분석 시스템

- NoScope, PVLDB 2017: <https://www.vldb.org/pvldb/vol10/p1586-kang.pdf>
- BlazeIt, PVLDB 2020: <https://www.vldb.org/pvldb/vol13/p533-kang.pdf>
- EQUI-VOCAL, PVLDB 2023: <https://www.vldb.org/pvldb/vol16/p2714-zhang.pdf>
- Spatialyze, PVLDB 2024: <https://www.vldb.org/pvldb/vol17/p2136-kittivorawong.pdf>
- VIVA, CIDR 2022: <https://vldb.org/cidrdb/2022/viva-an-end-to-end-system-for-interactive-video-analytics.html>

### 필터드 벡터 검색

- Filtered-DiskANN, WWW 2023: <https://harsha-simhadri.org/pubs/Filtered-DiskANN23.pdf> / <https://dl.acm.org/doi/10.1145/3543507.3583552>
- VBASE, OSDI 2023: <https://www.usenix.org/conference/osdi23/presentation/zhang-qianxi>
- ACORN, SIGMOD 2024: <https://arxiv.org/abs/2403.04871> / <https://dl.acm.org/doi/10.1145/3654923>
- UNIFY, PVLDB 2025: <https://www.vldb.org/pvldb/vol18/p1118-yao.pdf>
- pgvector iterative scans: <https://github.com/pgvector/pgvector> / <https://www.postgresql.org/about/news/pgvector-080-released-2952/>
- Qdrant filtering/indexing: <https://qdrant.tech/documentation/search/search/> / <https://qdrant.tech/documentation/manage-data/indexing/>
- Weaviate filtering: <https://docs.weaviate.io/weaviate/concepts/filtering>
- Milvus filtered search: <https://milvus.io/docs/filtered-search.md>
- AlloyDB filtered vector search: <https://docs.cloud.google.com/alloydb/docs/ai/filtered-vector-search-overview>
- Faiss IDSelector: <https://github.com/facebookresearch/faiss/wiki/Setting-search-parameters-for-one-query>
- FANNS survey: <https://arxiv.org/abs/2505.06501>
- Faiss GPU / cuVS / CAGRA: <https://faiss.ai/> / <https://docs.nvidia.com/cuvs/user-guide/references>

### 감시 VLM·VideoRAG

- UCA/VALU, CVPR 2024: <https://openaccess.thecvf.com/content/CVPR2024/html/Yuan_Towards_Surveillance_Video-and-Language_Understanding_New_Dataset_Baselines_and_Challenges_CVPR_2024_paper.html>
- HAWK, NeurIPS 2024: <https://proceedings.neurips.cc/paper_files/paper/2024/hash/fca83589e85cb061631b7ebc5db5d6bd-Abstract-Conference.html>
- ForeSea, arXiv 2026: <https://arxiv.org/abs/2603.22872>
- UrBench: <https://arxiv.org/abs/2408.17267>

### 국내 동향·데이터 출처 (이력)

- KCI DBR 권호 목록: <https://www.kci.go.kr/kciportal/po/search/poSereArtiList.kci?sereId=002167>
- DBR 소개: <https://dbsociety.kr/dbr/> / 투고 규정: <https://dbsociety.kr/dbr_submission_guide/>
- KCI RAG 청킹 논문: <https://www.kci.go.kr/kciportal/mobile/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003335873>
- KCI VLM 의료 VQA 논문: <https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003335872>
- KCI PGvector HNSW 논문: <https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003293183>
- 데이터셋 URL 목록은 §1.10.5 참조

### 정식 서지 (800_Introduction References, 이력 보존)

- Gollapudi, S. et al. (2023). Filtered-DiskANN: Graph Algorithms for Approximate Nearest Neighbor Search with Filters. WWW '23, pp. 3406–3416.
- Liang, A. et al. (2024). UNIFY: Unified Index for Range Filtered Approximate Neighbors Search. PVLDB 18(4):460-473.
- Lin, Y. et al. (2025). Survey of Filtered Approximate Nearest Neighbor Search over the Vector-Scalar Hybrid Data. arXiv:2505.06501.
- Patel, L. et al. (2024). ACORN: Performant and Predicate-Agnostic Search Over Vector Embeddings and Structured Data. SIGMOD '24.
- pgvector (2024). GitHub repository. <https://github.com/pgvector/pgvector>
- Zhang, Q. et al. (2023). VBASE: Unifying Online Vector Similarity Search and Relational Queries via Relaxed Monotonicity. OSDI 23, pp. 377–395.

---

# 2부. 출처별 고유 내용 색인

각 소스에만 있던 핵심 내용과 아카이브 경로. (공통 내용은 1부에 통합됨)

## 000_Introduction.md (2026-07-16, 구 통합 정본)

아카이브: `archive/legacy_premerge_20260728/000_Introduction.md`

- 구 통합 정본으로서 본 문서의 골격 전체(시스템 정의, Motivation 불릿, Research Gap 사실검증 표, Problem Statement, Contribution, 주장 범위와 한계, 1차 근거 문헌)를 제공.
- 이 파일에만 있던 것:
  - 구 RQ 3축 구조(평가 선행조건 + RQ-S/RQ-ALC/RQ-M) 원문 — §1.7 이력 절에 보존, 확정 RQ1-RQ6으로 대체됨.
  - RQ-S의 실행 기반 4종(Faiss, PostgreSQL+pgvector, Milvus, Weaviate)을 독립 변수로 두는 정식화 — 제출본에서는 독립 축이 아님.
  - 구 통합 관리표(§9): 100/770/780/800/760계열/810/manuscript 계열 파일별 흡수 내용과 상태.
  - 실증 근거 문서 포인터: 620_RESULTS_filtered_ann_real_predicates_20260710.md, 700_MEVA_integration_execution_20260713.md, 720_RESULTS_db_design_storage_index_20260713.md, 660_GOAL3_regime_characterization_20260713.md, DATA_PROVENANCE_raw_vs_derived_20260715.md.
  - "제출용 산문은 6절 기준" 등 구 관리 정책 — §1.11의 새 정책으로 대체.

## 100_INTRO_topic_selection_rationale.md (2026-07-06)

아카이브: `archive/legacy_premerge_20260728/100_INTRO_topic_selection_rationale.md`

- 주제 선정 이력 전체(§1.10에 보존): 권장/대체 제목 후보, 후보 주제 6종 비교표, DBR 2025-2026 31편 토픽 분포표, DBR 42권 1호 수록 논문 목록, 국내 흐름 세 갈래 분석.
- DBR·KCI·데이터셋 URL 목록(§1.10.5, §1.12에 보존).
- ForeSea 뉘앙스(벤치마크 대 시스템 구분)와 UrBench 상세(11.6K 질문, 4과업 차원·14과업 유형, 정지 이미지라 본 연구와 거리 있음) — §1.4.3에 보존.
- 초기 기여 문장 초안("metadata-aware hybrid retrieval이 검색 재현율과 근거 품질을 개선하는지 평가") — RQ4 정본 결과(개선 없음)로 정정됨.
- "2주 내 투고 목표, 축소형 워크로드로 좁힌다"는 일정·범위 판단 이력.

## 770_INTRO_structure_and_draft_20260714.md

아카이브: `archive/legacy_premerge_20260728/770_INTRO_structure_and_draft_20260714.md`

- Introduction 5단 전개 구성안(기술 동향→문제 관찰→연구 필요성→사회적·기술적 의의→기여) — 구조적 대안으로 이력 보존.
- 사회적 기여 문단 원문: "사람이 검토해야 할 영상 범위를 줄이고, 의사결정에 사용되는 증거의 추적성과 설명 가능성을 높인다. 자동 감시 판단을 대체하려는 것이 아니라 관련 검색 결과를 신뢰성 있게 찾고 제시하는 데이터베이스 계층에 초점" — 향후 개정 원고에서 재사용 가치 있음.
- 압축 3-Contribution 버전(Validity / Design-space / Operational DB) — 지면 부족 시 대안.
- MEVA 외적 타당성 + MIRIS 색인 정책 교차검증 계획 서술 — 개발기 계획 이력.
- Introduction 마지막 문단 예시("hard constraint에서는 prefilter가 유리...") — RQ3/RQ5 정본 결과로 정정됨(§1.7 참조).

## 780_INTRO_filtered_vector_search_factcheck_20260714.md

아카이브: `archive/legacy_premerge_20260728/780_INTRO_filtered_vector_search_factcheck_20260714.md`

- Filtered vector search 사실검증 규칙 5종(§1.5.1에 전량 보존): High Selectivity 용어 금지·`s = |σ_p(D)| / |D|` 수식 정의, prefilter 병목 5분류, postfilter 서술 검증, single-stage 서술 주의.
- 네 가지 기술 패러다임 정리(§1.5.2에 보존).
- 관련 연구 상세표 2종(알고리즘 계열 + Vector DB/RDB 통합 계열, §1.5.3에 보존) — CAPS, FANNS survey, AlloyDB, Qdrant 등은 이 파일이 유일 출처.
- 하드웨어 가속(Faiss GPU, cuVS/CAGRA, VecFlow) 취급 지침: 직접 기여가 아니므로 짧게만 언급.
- 차별성 문장 영문/국문 쌍(§1.5.4에 보존).
- 관련 연구 URL 11종(§1.12에 흡수).

## 800_Introduction_20260714.md

아카이브: `archive/legacy_premerge_20260728/800_Introduction_20260714.md`

- 논문 산문체 장문 Introduction 초안(1.1~1.6) — 제출본 서론의 직접 전신. 산문 표현 자산으로 이력 보존.
- 순환성 설명의 구체 예시 문장("10시 15분 교차로 A에서 적색 차량이 신호를 위반했다"는 어노테이션에서 document·필터·정답이 동시 파생) — 순환 기전을 설명하는 가장 구체적인 예시로 재사용 가치 있음.
- prefilter 한계의 그래프 단절 설명(HNSW proximity graph에서 필터 탈락 노드가 탐색 경로를 단절, Gollapudi et al. 2023; Lin et al. 2025 인용) — 학술 인용이 붙은 유일한 판본.
- 정식 서지 6건(References) — §1.12에 보존.
- 이 파일에만 있던 정정 대상 서술:
  - "네 가지 핵심 데이터베이스 설계 차원" — [정정 2026-07-28: 제출본은 다섯 설계 축 112 구성]
  - "설계 공간을 최초로 체계화" — [정정 2026-07-28: '최초' 사용 금지 규칙(§1.2.1) 위반으로 폐기]
  - "$N^* = \text{build\_cost} / \text{latency\_saving}$ hot/cold 정책" — [정정 2026-07-28: 정본 배포 규칙으로 대체(§1.7 RQ5)]
  - "corpus scale, VLM perception, answer bias가 차단막(buffer) 역할" — [정정 2026-07-28: 3관문 정식화로 대체(§1.7 RQ6)]
