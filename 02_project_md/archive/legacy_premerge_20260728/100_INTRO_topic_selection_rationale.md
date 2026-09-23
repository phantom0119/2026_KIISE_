# 주제 선정 타당성

> 상태: **HISTORY** — 유효한 Motivation·Research Gap 내용은 [`000_Introduction.md`](000_Introduction.md)에 통합되었다. 신규 수정은 통합 정본에서 수행한다.

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 주제 선정 방향은 유지하되, 연구 범위는 초기 retrieval workload 설계에서 `true multimodal retrieval + service evidence packet + fixed LLM/VLM answer-level control + 시내도로 CCTV index benchmark`까지 확장되었다. 최신 데이터셋 구축 상태와 실험 수치는 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 기준으로 한다.

## 최종 주제

권장 제목:

> 멀티모달 도시 감시 데이터를 위한 하이브리드 VLM-DB 검색 워크로드 설계와 저장·색인 구조 비교

대체 제목:

- 도시 감시형 멀티모달 데이터베이스에서 메타데이터 필터와 벡터 검색 결합 구조의 성능 분석
- VLM 기반 도시 감시 질의응답을 위한 멀티모달 검색 워크로드와 하이브리드 색인 평가

핵심 연구 질문:

> 이미지/영상, 사건 보고서, 센서·시공간 메타데이터가 결합된 도시 감시 데이터에서 VLM 질의응답을 지원하려면 어떤 저장·색인·검색 구조가 정확도, 지연시간, 비용을 가장 잘 균형화하는가?


## 연구 수행 방향 설계
- 본 연구는 특정 데이터셋이나 특정 모델의 우수성을 주장하는 것이 아니라, 데이터셋·embedding model·vector backend가 교체되어도 동일 query/qrels와 canonical schema 위에서 metadata-aware retrieval 구조를 비교할 수 있는 모듈형 VLM-DB 실험 프레임워크를 제안한다.

- 최근 공개된 도시 감시/교통 안전 데이터는 이미 비디오, 캡션, VQA, CoT, 시간·장소·카메라 메타데이터를 포함하는 방향으로 진화하고 있다. 따라서 VLM 성능 평가만으로는 부족하며, 이질적 evidence를 어떤 저장·색인·검색 구조로 결합할 것인지가 독립적인 데이터베이스 연구 문제가 된다.

- 본 주제의 핵심은 도시 감시 데이터의 이질적 모달리티를 하나의 질의 계층에서 결합하는 것이다. 구체적으로는 CCTV 프레임/클립, 교통·기상·지도 메타데이터, 센서 로그, 이벤트 보고서·민원·상황일지 같은 문서를 통합 저장하고, 사용자 질의에 대해 멀티모달 retrieval, VQA, event grounding을 수행하는 VLM-DB를 설계·평가하는 문제다. 

- 국제적으로 문서·영상 RAG 연구는 빠르게 발전했지만, 실제 운영형 시스템에서는 여전히 필터 가능한 벡터 검색, 멀티벡터 저장 비용, 시공간 조인, 근거 제시 가능한 답변, 온라인 지연과 비용이 병목으로 남아 있다.



## 국내 동향 근거

기존 조사 자료는 DBR 2025~2026 공개 논문을 31편으로 정리했고, 다음 분포를 제시했다.

| 토픽 | 편수 | 비율 |
|---|---:|---:|
| 생성형 AI·LLM·RAG·Text-to-SQL | 8 | 25.8% |
| 컴퓨터비전·멀티모달·센싱 | 7 | 22.6% |
| 그래프 분석·GNN | 5 | 16.1% |
| 응용 예측·추천·문서 마이닝 | 5 | 16.1% |
| 시계열·데이터 품질·전처리 | 3 | 9.7% |
| 분산 데이터 처리·벡터 인덱스·시스템 엔지니어링 | 3 | 9.7% |

KCI 권호 목록에서도 DBR은 KCI 등재 학술지이며 최근 발행 정보가 2026년 4월 42권 1호로 확인된다. 해당 호에는 다음 주제가 함께 나타난다.

- 객체 기반 데이터 증강을 통한 교통 표지 인식 성능 향상
- 대기오염 관련 사건 탐지를 위한 LLM 기반 뉴스 기사 분류
- 노후 주택의 균열 분류를 위한 프로토타입 기반 앙상블 퓨샷 러닝 프레임워크
- 다국어 환경에서 VLM의 의료 시각 성능 및 언어 간 일관성 분석
- RAG 시스템에서의 경계 정보 손실 완화를 위한 하이브리드 의미 기반 윈도우 청킹 기법

이는 DBR 최신호가 이미 RAG, LLM 사건 탐지, VLM 평가, 도시/환경 비전 응용을 수용하고 있음을 보여준다. 따라서 본 주제는 DBR 범위 밖의 순수 AI 논문이 아니라, 최신 DBR 흐름을 데이터 관리 문제로 묶어내는 연구로 볼 수 있다.


-  2026년 현재 확인 가능한 최신호에서는 “전통적 DB 코어 이슈”보다 “AI-중심 데이터 활용”이 훨씬 강하게 전면화
- 최종 분류 체계는 다음과 같다. 생성형 AI·LLM·RAG·Text-to-SQL, 그래프 분석·응집 서브그래프·GNN, 시계열·데이터 품질·전처리, 분산 데이터 처리·벡터 인덱스·시스템 엔지니어링, 컴퓨터비전·멀티모달·센싱, 응용 예측·추천·문서 마이닝이다. 이 분류는 사용자 예시 범주 가운데 그래프 DB, 시계열, 데이터 품질, ML-DB 통합, 데이터 관리 자동화, 시스템 구현/엔지니어링, 벤치마크/성능에 가장 가깝게 대응한다. 예컨대 RAG·Text-to-SQL은 ML-DB 통합, PGvector HNSW는 벡터 인덱스/시스템 엔지니어링, 라이프로그 결측 처리나 시계열 이상치 보정은 데이터 품질·자동화로 보았다.
- 최신 DBR에서 데이터베이스가 전통적 저장·질의·트랜잭션보다 AI 활용·검색 증강·멀티모달 데이터 처리의 응용 중심으로 재배치되고 있다. 반면 시계열·데이터 품질·전처리, 분산 처리·벡터 인덱스·시스템 엔지니어링 분야에서는 그 분포가 적음을 확인했다.
- 생성형 AI 영역에서는 오픈소스 RAG QA 시스템, 하이브리드 RAG 챗봇, 소규모 언어모델 기반 Text-to-SQL, RAG 청킹 최적화가 기술 축을 이루었다. 그래프 영역에서는 (k,o)-core, 트러스 기반 커뮤니티 탐지, 결합 모듈러리티 기반 커뮤니티 탐지, 양자 최소 k-core가 연속적인 응집 서브그래프 계열을 구성했다. 데이터 품질 영역에서는 제조 공정 불균형 전처리, 시계열 이상치 보정, 라이프로그 결측·편향 해결이 묶인다. 시스템 영역에서는 분산형 기계학습 프레임워크, Spark 기반 스팸 탐지, PGvector HNSW I/O 감소가 확인되며, 비전·멀티모달 영역에서는 교통표지 인식, 침수 탐지, 균열 분류, VLM 의료 시각 질의응답, Wi‑Fi CSI 운동량 추론이 대표적이다.


구체적으로는 프라이버시·보안의 약함, RAG/벡터DB의 평가 표준 부족, 데이터 품질 자동화의 저빈도, 도메인 특화 Text-to-SQL 및 멀티모달 DB 벤치마크 부재를 문제로 보고 설계했으며 그 결과로 도출된 건이 본 연구 주제에 해당한다.

> 제안 주제: 멀티모달 도시 감시 데이터용 VLM-DB 벤치마크
> 핵심 연구 질문: 이미지·문서·센서 로그를 함께 다루는 VLM 질의응답에서 어떤 데이터 저장/색인 구조가 가장 효율적인가?
> 예상 방법론: 데이터: CCTV 샘플, 교통·기상·지도 메타데이터, 이벤트 보고서. 실험: multimodal retrieval, vector+metadata filter, event grounding. 지표: retrieval recall, VQA accuracy, latency, cost
> 예상 기여: VLM 시대의 DB/IR 통합 워크로드 정의


DBR의 2025–2026 공개 논문 목록을 보면, 국내 동향은 크게 세 갈래다.
- 첫째, RAG/LLM 기반 검색 설계다. 2025년에는 약전 문서용 하이브리드 RAG 챗봇이 등장했고, 2026년에는 하이브리드 의미 기반 윈도우 청킹과 LLM 기반 사건 분류가 실렸다.
- 둘째, VLM·멀티모달 이해다. 2026년 DBR에는 다국어 의료 VQA에서의 VLM 성능 및 언어 간 일관성 분석이 직접 실렸다.
- 셋째, 도메인 특화 대규모 데이터 관리다. DBR에는 오픈 데이터 레이크 자동화, 대규모 해양관측 데이터 검색, 실시간 침수 탐지, 교통 표지 인식 등 저장·검색·분석이 결합된 응용 논문이 이어진다. 반면, CCTV 프레임·센서 로그·문서 보고서를 하나의 멀티모달 DB 질의 계층으로 통합한 국내 DB 논문은 2025–2026 공개호 최신 기준으로 아직 뚜렷하게 보이지 않는다. 
이 지점이 바로 연구 공백이다.

논문 포지셔닝은 "새 VLM 제안"보다 도시 감시용 하이브리드 아키텍처, event-grounded retrieval/VQA benchmark, metadata filtering과 multivector retrieval의 trade-off 분석으로 잡는 편이 DBR 및 국제 DB·IR·멀티모달 흐름에 더 잘 맞는다.

> 가장 설득력 있는 문제 정의는 "멀티모달 도시 감시 데이터를 위한 VLM-DB" 를 단순 모델 성능 연구가 아니라, 저장 구조·멀티인덱스·질의 처리·비용 관리까지 포함하는 데이터 관리 연구로 세우는 것이다.



## 국외 학술 논문 및 상위 학회 연구 동향 근거

기존 조사 자료는 2024~2026 학회에 등재된 논문을 정리하며, 다음과 같은 정보를 제공한다.

1) ForeSea: AI Forensic Search with Multi-modal Queries for Video Surveillance
- URL: https://arxiv.org/abs/2603.22872

- ForeSeaQA는 감시 도메인에서 멀티모달·시간적으로 grounding된 비디오 QA를 다루는 최초의 벤치마크로, 여섯 개 하위 과제를 다루며 텍스트 전용 질의와 멀티모달 질의 양쪽에서 다중선택 정확도와 시간적 위치추정을 함께 평가한다. ForeSea 시스템 자체는 추적 모듈이 무관한 영상을 걸러내고, 멀티모달 임베딩 모듈이 남은 클립을 색인하며, 추론 시 상위 K개 후보 클립을 검색해 Video LLM이 답하고 이벤트를 위치추정하는 3단계 플러그앤플레이 파이프라인이다.

- ForeSeaQA에서 이전 VideoRAG 모델 대비 정확도 3.5%, temporal IoU 11.0 향상처럼 정확도·grounding 중심으로 보고된다. 다만 한 가지 뉘앙스를 덧붙이면, ForeSea는 순수 평가 벤치마크만이 아니라 검색 시스템(파이프라인)까지 제안하므로 "모델 정확도만 평가"라는 표현은 벤치마크(ForeSeaQA)에는 맞지만 시스템(ForeSea)에는 부분적으로만 맞다. 그럼에도 저장 스키마·색인 구조에 따른 시스템 성능(처리량·비용·지연) 비교가 없다는 핵심 논지는 유효하다.

2) UrBench: A Comprehensive Benchmark for Evaluating Large Multimodal Models in Multi-View Urban Scenarios
- URL: https://arxiv.org/abs/2408.17267

- 대형 멀티모달 모델(Large Multimodal Models, LMM)에 대한 평가는 다양한 도메인에서 그 성능을 탐색하고 있으나, 도시 환경에 특화된 벤치마크는 극히 드문 실정이다. 또한, 기존의 도시 관련 벤치마크는 단일 시점(singular view) 하에서 기본적인 지역 수준(region-level)의 도시 과업으로 LMM을 평가하는 데 국한되어 있어, 도시 환경에서의 LMM 역량에 대한 불완전한 평가를 초래하고 있음을 언급함.

- 이러한 한계를 극복하기 위해, 본 논문에서는 복잡한 다중 시점(multi-view) 도시 시나리오에서 LMM을 평가하도록 설계된 종합적인 벤치마크인 UrBench를 제안한다. UrBench는 지역 수준 및 역할 수준(role-level) 모두에서 세심하게 큐레이션된 11.6K개의 질문을 포함하며, 이는 지리적 위치 추정(Geo-Localization), 장면 추론(Scene Reasoning), 장면 이해(Scene Understanding), 객체 이해(Object Understanding)의 4개 과업 차원과 총 14개의 과업 유형을 아우른다.

- UrBench는 정지 이미지(스트리트 뷰·위성뷰) 기반 공간 추론 벤치마크이지 비디오나 시간적 grounding, RAG 검색 파이프라인과는 무관하다. 따라서 본 연구실 주제(멀티모달 도시 감시 영상의 저장·색인·검색)와의 거리는 ForeSea보다 더 멀다 — 도메인 어휘("urban")는 겹치지만 데이터 양식(영상 대 정지 이미지)과 문제 축(검색 시스템 대 모델 평가)이 모두 다르다.


## 연구 공백

확인된 국내 흐름에는 다음 구성 요소가 각각 존재한다.

- RAG 검색과 청킹 최적화
- PGvector/HNSW 등 벡터 인덱스 최적화
- VLM/VQA 성능 평가
- LLM 기반 사건 분류
- 교통, 환경, 의료, 균열 등 도메인 영상/문서 응용

그러나 다음을 동시에 다루는 연구는 희소하다.

- 영상 또는 키프레임
- 사건 보고서 또는 상황 일지
- 시간, 장소, 카메라, 날씨, 교통량 같은 정형 메타데이터
- 벡터 검색과 sparse 검색, metadata filter의 결합
- 검색 결과를 근거로 하는 VQA와 event grounding
- 정확도뿐 아니라 latency와 cost까지 포함한 DB 관점의 평가

이 공백이 “멀티모달 도시 감시 VLM-DB” 주제의 핵심 타당성이다.

## 후보 주제 비교

| 후보 | 장점 | 약점 | 7월 20일 투고 적합성 |
|---|---|---|---|
| 한국어 도메인 문서 RAG 벤치마크 | 데이터 확보 쉬움, 기존 VLDB/ECIR 작업과 연결 쉬움 | 기존 연구와 겹칠 위험, DBR 최신호 RAG 청킹 논문과 차별화 필요 | 중간 |
| 프라이버시 보장 라이프로그 데이터 관리 | 연구 갭 큼, 사회적 중요성 높음 | 데이터 접근·IRB·프라이버시 실험 부담 큼 | 낮음 |
| 한국어 엔터프라이즈 Text-to-SQL | DB 접점 강함 | 스키마/질의셋 구축 시간이 필요하고 기존 국제 benchmark 의존이 커짐 | 중간 |
| 멀티모달 도시 감시 VLM-DB | DBR 최신 트렌드와 연구 공백을 동시에 만족, 공개 영상/메타데이터 활용 가능 | 원천 데이터 구성과 라벨 생성이 관건 | 높음 |
| 스트리밍 시계열 이상치 보정 | DB 코어에 가까움 | VLM/RAG 최신 흐름과 약간 분리, 실험 설계가 별도 | 중간 |
| 그래프-RAG | 참신성 높음 | 그래프 데이터와 RAG 평가를 새로 구축해야 함 | 낮음~중간 |

결론: 2주 내 투고를 목표로 한다면 “멀티모달 도시 감시 VLM-DB”가 가장 높은 효율을 낸다. 다만 범위를 “대규모 완성형 벤치마크”로 잡으면 실패 위험이 높으므로, “축소형 공개 데이터 기반 워크로드 정의와 구조 비교”로 좁혀야 한다.

## 최종 프레이밍

논문은 다음 순서로 전개한다.

1. 국내 DBR 2025~2026 동향상 RAG, VLM, 도시/환경 이벤트 분석이 부상하고 있음을 보인다.
2. 하지만 이들은 각각 별도 컴포넌트로 존재하고, 멀티모달 도시 감시 데이터의 저장·색인·검색 워크로드는 충분히 정식화되지 않았다고 지적한다.
3. 도시 감시형 VLM-DB 워크로드를 정의한다.
4. 단일 벡터 검색, sparse 검색, metadata filter, hybrid retrieval을 비교한다.
5. retrieval recall, nDCG, event grounding, VQA accuracy, latency, cost를 함께 측정한다.
6. 결과를 통해 “VLM-DB에서 성능은 모델만이 아니라 데이터 관리 구조에 의해 크게 좌우된다”는 결론을 제시한다.

## 기여 문장 초안

본 논문은 도시 감시형 멀티모달 데이터베이스에서 VLM 질의응답을 지원하기 위한 검색 워크로드를 정의하고, 영상 키프레임, 사건 보고서, 시공간 메타데이터를 결합한 하이브리드 저장·색인 구조를 비교한다. 공개 CCTV/교통 이벤트 데이터를 바탕으로 text-to-clip retrieval, report-to-frame grounding, evidence-aware VQA를 구성하고, 단일 벡터 검색 대비 metadata-aware hybrid retrieval이 검색 재현율과 근거 품질을 개선하는지 평가한다. 이를 통해 VLM 시대의 데이터베이스 연구가 모델 정확도 중심 평가를 넘어, 근거 검색, 필터링, 지연시간, 비용을 함께 고려해야 함을 보인다.

## 주요 근거 출처

- KCI DBR 권호 목록: https://www.kci.go.kr/kciportal/po/search/poSereArtiList.kci?sereId=002167
- DBR 소개: https://dbsociety.kr/dbr/
- DBR 투고 규정: https://dbsociety.kr/dbr_submission_guide/
- KCI RAG 청킹 논문: https://www.kci.go.kr/kciportal/mobile/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003335873
- KCI VLM 의료 VQA 논문: https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003335872
- KCI PGvector HNSW 논문: https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003293183

- AI Hub 이상행동 CCTV 영상: https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=171
- 다각도 CCTV 생활안전 데이터: https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=71953
- 지능형 관제 서비스 CCTV 영상 데이터 (2024년): https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=71850
- AI City Challenge 2025: https://www.aicitychallenge.org/2025-ai-city-challenge/
- VRU-Accident: https://arxiv.org/abs/2507.09815
- TUMTraf VideoQA 데이터셋 및 벤치마크: https://traffix-videoqa.github.io/
   -> 1,000개 roadside traffic videos, 85K QA, captioning, spatio-temporal grounding 포함
- 교차로 신호 체계, 보행자, 차량 이동 복합 데이터: https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=522
   -> CCTV 기반, 비디오+텍스트+VQA+CoT+카메라 메타데이터
- 교통문제 해결을 위한 CCTV 교통 영상(시내도로): https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=165

