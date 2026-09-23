# 멀티모달 VLM-DB 통합 검색 워크로드 동향과 논문 설계 보고서

## Executive Summary

귀하가 2주 내 작성하려는 논문 주제인 **“멀티모달 도시 감시 데이터용 하이브리드 VLM-DB 검색 워크로드 설계 및 저장·색인 구조 비교”**는 2025–2026년 시점에서 **충분히 시의성이 있고**, 해외 상위 DB/IR/ML/CV 학계에서 그 구성 요소들은 활발히 연구되고 있으나, **영상·보고서·센서·시공간 메타데이터를 하나의 재현 가능한 DB/IR/VLM 워크로드로 묶어 저장·색인·검색 구조를 체계 비교하는 연구는 여전히 공백이 크다**고 판단됩니다. 국내 DBR 쪽에서도 2025년 최근 권호에서 RAG, Text-to-SQL, 언어모델 기반 문서 표현, 시계열 처리 등이 등장해 **LLM/검색/데이터관리 융합 방향**은 분명하지만, 귀하가 제안한 수준의 **멀티모달 이벤트 중심 통합 벤치마크**는 확인되지 않았습니다. citeturn39search4turn33view0turn34view0turn31view1turn30search6turn30search7turn41view0

해외 상위 학회에서는 DB 커뮤니티가 **filtered vector search, hybrid query, vector DB benchmarking, graph/vector/RAG 통합**에 집중하고 있고, IR/CV/ML 커뮤니티는 **text-to-video retrieval, composed image retrieval, video question grounding, video temporal grounding, explainable multimodal time-series**로 빠르게 확장 중입니다. 다만 이 흐름은 아직 **“저장 구조와 인덱스 설계가 멀티모달 질의응답 정확도·지연·비용에 어떤 영향을 주는가”**를 동일한 실험 프레임에서 답하지는 못하고 있습니다. 즉, **연구 요소는 활발하지만, 귀하의 정확한 문제 정의는 아직 분절된 상태**입니다. citeturn25view0turn25view3turn25view4turn25view5turn27view0turn27view1turn27view2turn27view3turn20search11turn40view6

데이터 확보는 도시 감시 도메인 기준으로는 **상당히 실현 가능**합니다. AI Hub의 이상행동 CCTV와 지하철 역사 이상행동 데이터가 존재하고, AI City Challenge는 **데이터 접근 요청서 없이 Quick Access**를 제공하고 있습니다. 특히 AI City 2025 Track 2는 **교통 안전 시나리오 비디오 + 상세 캡션 + 바운딩박스**를 제공하며, AI City 2026 Track 3 TAR는 **3,670개 CCTV 교통 영상과 44,040개 reasoning annotation**을 제공해 event grounding 및 설명 가능한 VLM 평가에 적합합니다. 서울 교통 CCTV 위치, 실시간 돌발 API, 기상청 자료를 결합하면 센서·시공간 메타데이터 축도 쉽게 만들 수 있습니다. citeturn10view0turn10view1turn10view2turn10view4turn36view0turn37search0turn18search0turn18search4turn19search0turn19search1

의료 도메인으로의 전환도 **기술적으로는 가능**하지만, **2주 내 실험 완성**이라는 현실 제약을 고려하면 **한국 환자 수준 임상 멀티모달 데이터로 바로 가는 것은 고위험**입니다. 한국의 보건의료 빅데이터는 통합 플랫폼과 분석센터 중심의 절차, 추가 비식별화, 반출 심의, 경우에 따라 IRB가 필요해 준비 시간이 길 수 있습니다. 반면 **MIMIC-IV, MIMIC-IV-Note, MIMIC-CXR, eICU, Symile-MIMIC** 같은 공개·비식별 해외 데이터는 의료 멀티모달 워크로드 파일럿에 현실적인 대안입니다. 따라서 **도시 감시 도메인으로 논문 초고를 완성하고, 의료는 후속 확장 또는 별도 실험 섹션**으로 두는 전략이 가장 안전합니다. citeturn17search0turn17search3turn17search13turn12search6turn12search4turn12search7turn12search3turn14search0turn14search2turn14search8turn13search0turn13search1turn13search9turn14search3

결론적으로, **지금 당장 가장 논문 가능성이 높은 방향은 도시 감시 도메인 유지**입니다. 추천 실행안은 **AI City 2025/2026 + 서울 교통/기상/지도 메타데이터 + PostgreSQL/pgvector 또는 hybrid sparse+dense 엔진 기반 파일럿**으로 시작하고, AI Hub는 승인 여부에 따라 추가하는 것입니다. 의료는 **공개 MIMIC 기반 보조 검증**으로 넣되, 한국 임상 데이터는 본문에서 “확장 가능성 및 제약”으로 정리하는 편이 가장 합리적입니다. citeturn10view2turn10view4turn36view0turn11search0turn11search2turn38search0turn38search2turn38search16turn14search0turn13search0

## 연구 문제 정의와 국내외 동향

귀하의 문제는 단순한 “멀티모달 검색”이 아니라, **이미지/영상, 사건 보고서 텍스트, 센서·시공간 메타데이터를 포함하는 이벤트 단위 객체를 데이터베이스적으로 저장하고, 질의 시에는 벡터 검색·키워드 검색·메타데이터 필터·시간 구간 정렬·증거 재순위화를 함께 수행해 VLM 질의응답까지 연결하는 통합 워크로드**를 정의하는 일입니다. 이 문제는 DB 관점에서는 **hybrid query planning, filtered vector search, multi-vector storage, update/ingestion**, IR 관점에서는 **sparse+dense fusion, cross-modal retrieval, reranking**, CV/VLM 관점에서는 **event grounding, temporal localization, grounded VQA**를 한꺼번에 다뤄야 한다는 점에서 어렵습니다. citeturn25view0turn25view2turn25view3turn25view5turn27view1turn27view2

이 워크로드가 실제로 요구하는 기능은 비교적 명확합니다. 첫째, 사용자는 텍스트 질의로 “어젯밤 교차로에서 보행자 급정거를 유발한 사건”처럼 **영상 이벤트를 찾고**, 동시에 보고서와 센서값을 함께 보고 싶어 합니다. 둘째, 질의 결과는 단순 top-k가 아니라 **근거 프레임, 시간 구간, 관련 보고서 문장, 해당 시점의 기상·위치 메타데이터**를 함께 제시해야 합니다. 셋째, 영상은 길고 비싸므로 **키프레임/세그먼트/캡션 단위 청킹과 coarse-to-fine retrieval**이 필요합니다. 넷째, 시스템은 정확도뿐 아니라 **P50/P95 지연, 추론 비용, 저장비용, 재색인 비용**까지 관리해야 합니다. 다섯째, 특히 CCTV나 의료로 갈수록 **개인정보, 재식별 금지, 폐쇄 환경 분석, IRB 또는 IRB 면제 판단**이 중요해집니다. citeturn27view2turn11search1turn12search6turn12search7turn12search3turn17search0turn14search3

국내 DBR 동향은 이 문제에 직접 닿아 있지는 않지만, **분명 같은 방향의 하위 기술들**을 축적하고 있습니다. 2025년 DBR 41권 2호에는 오픈소스 RAG 아키텍처 기반 도메인 문서 QA 시스템이 게재되었고, 여기서는 **semantic chunking, ANN retrieval, reranking, local LLM, semantic cache**를 통합했습니다. 같은 호에는 **강화학습 기반 소규모 언어모델 Text-to-SQL** 논문이 실려, DB 인터페이스를 LLM으로 확장하는 실험을 보여 주었습니다. 41권 1호에서는 **언어모델 요약 기반 뉴스 문서 표현**이 문서 군집화 성능을 높였고, 장문을 요약·표현으로 전환하는 전략이 효과적임을 보였습니다. 이런 흐름은 DBR이 2025년 시점에 **RAG·LLM·문서표현·데이터 접근 자동화**를 DB 연구의 합법적 주제로 받아들이고 있음을 시사합니다. citeturn33view0turn34view0turn31view1turn30search6turn30search7

또한 DBR 자체는 KCI 등재지이며, 현재도 **연 3회 발행(4월·8월·12월 말)** 구조를 유지하고 있습니다. 따라서 귀하의 주제가 DBR에 투고될 때도, 엄밀한 시스템 평가와 데이터 관리 기여가 분명하다면 **저널 범위와 완전히 어긋나지 않습니다**. 다만 “비전 모델 응용”처럼 보이기보다, **워크로드 정의, 저장·색인 설계 비교, 필터드 검색 계획, 데이터 관리 관점의 실험 엄밀성**을 전면에 내세우는 편이 훨씬 유리합니다. citeturn39search4turn39search0turn39search5

해외 상위 학회의 추세를 한 문장으로 정리하면 이렇습니다. **DB는 벡터와 구조 질의의 통합을, IR은 멀티모달 검색을, CV/ML은 grounded video understanding을 밀고 있다. 하지만 세 축을 하나의 재현 가능한 시스템 논문 문제로 묶는 연구는 아직 적다.** 이 점이 귀하의 타당한 진입점입니다. citeturn25view0turn25view3turn25view4turn20search11turn27view0turn27view1turn27view2turn40view6

## 관련 연구 서베이

아래 표는 귀하의 주제와 직접적으로 연결되는 대표 논문들을 국내 DBR, 해외 DB, IR, CV, ML 흐름으로 압축한 것입니다. 표의 목적은 “무엇이 이미 풀렸고, 무엇이 아직 안 풀렸는가”를 빠르게 보여주는 데 있습니다.

| 구분 | 대표 논문 | 문제와 방법 | 데이터/결과 | 본 주제와의 관련성 및 한계 |
|---|---|---|---|---|
| 국내 DBR | **오픈소스 RAG 아키텍처를 활용한 도메인 지식 문서 질의응답 시스템의 설계 및 구현** (DBR 2025) | semantic embedding, ANN, reranking, local LLM, semantic cache를 통합한 RAG QA 시스템 설계 | 기존 방식 대비 답변 정확도·문서 커버리지·응답속도 우수라고 보고. 멀티모달은 아님. citeturn33view0 | **RAG 파이프라인과 cache, chunking, reranking**를 DBR 문맥에서 정당화하는 근거. 그러나 영상·센서·grounding이 없음. |
| 국내 DBR | **강화학습을 활용한 소규모 언어 모델 기반 Text-to-SQL 성능 향상** (DBR 2025) | SLM에 GRPO 기반 강화학습을 적용해 Text-to-SQL 성능 향상 | Spider/BIRD-SQL에서 동일 규모 지도학습 모델보다 우수, 일부는 더 큰 모델과 유사하거나 상회. citeturn34view0 | DB 질의 인터페이스 자동화에 대한 국내 최신 흐름. 그러나 **검색·멀티모달·증거 grounding**은 다루지 않음. |
| 국내 DBR | **뉴스 문서 계층적·점증적 군집화 성능 향상을 위한 언어 모델 기반 문서 표현 방법 고찰** (DBR 2025) | 장문 대신 요약문을 사용한 문서 표현으로 clustering 개선 | LLM 요약 품질을 높일수록 군집화가 더 개선됨. 제목+첫 문장 조합이 가장 우수. citeturn31view1 | 장문 보고서/이벤트 리포트를 **요약·청킹·표현 단위**로 변환해야 하는 귀하의 문제와 직접 연결됨. |
| DB | **DEG: Efficient Hybrid Vector Search Using the Dynamic Edge Navigation Graph** (SIGMOD 2025) | 이미지-텍스트 등 **bimodal data**에 대한 hybrid vector query에서 query별 가중치 α 변화에 강한 그래프 인덱스 제안 | 변하는 α에 대해 기존 방법 대비 더 좋은 accuracy-efficiency trade-off 보고. citeturn25view0turn25view1 | 귀하의 late fusion 또는 multi-vector fusion 질의에 핵심. 그러나 **메타데이터·시간·보고서 텍스트**까지 함께 최적화하지 않음. |
| DB | **SIEVE: Effective Filtered Vector Search with Collection of Indexes** (PVLDB 2025) | hard predicate가 있는 filtered vector search를 위해 index collection 전략 제안 | “videos tagged kids” 같은 실문제를 filtered similarity search로 정의. citeturn25view3 | **vector + metadata filter** 문제의 정면 해법. 하지만 멀티모달 retrieval 자체나 VQA 품질까지는 평가하지 않음. |
| DB | **GaussDB-Vector** (PVLDB 2025) | persistent, distributed, real-time vector DB 구조와 hybrid scalar-vector filtering 지원 | low-latency search, real-time insert/delete, hybrid scalar-vector filtering 지원을 강조. citeturn25view4 | 실제 시스템 구축 시 **대용량 지속 저장+실시간 갱신** 관점의 비교 축이 됨. 다만 워크로드는 주로 vector DB 관점이다. |
| DB | **BigVectorBench** (PVLDB 2025) | heterogeneous embedding과 compound query를 포함하는 vector DB benchmark 제안 | compound query에서 throughput과 recall이 크게 떨어지고, **recall이 unimodal 대비 거의 절반**까지 감소할 수 있다고 보고. citeturn25view5turn40view2 | 귀하 논문의 핵심 명분. 즉, **복합 질의가 성능을 크게 바꾼다**는 것을 공식적으로 뒷받침한다. |
| DB | **An Experimental Evaluation of Hybrid Querying on Vectors** (PVLDB 2026) | vector + structured filter 질의의 통합 벤치마킹 필요성을 제기 | 기존 평가가 통일된 기준과 체계적 비교가 부족하다고 지적. citeturn25view2 | 귀하 논문의 “왜 새로운 benchmark/workload가 필요한가”를 뒷받침하는 직접 근거. |
| IR | **Continual Text-to-Video Retrieval with Frame Fusion and Task-Aware Routing** (SIGIR 2025) | 지속적으로 유입되는 비디오를 다루는 continual text-to-video retrieval 문제 정의 | 최초의 CTVR benchmark를 제안하고 기존 TVR/CL 방법의 한계를 보임. citeturn20search16turn28search0turn28search8 | 실제 CCTV/교통 시스템처럼 데이터가 증가하는 상황에서 **지속 색인과 갱신** 문제를 연결할 수 있다. |
| IR | **WISE: A Multimodal Search Engine for Visual Scenes, Audio, Objects, Faces, Speech, and Metadata** (SIGIR 2026 예정) | 장면, 객체, 음성, speech, metadata를 하나의 검색 엔진에서 통합 | 수백만 이미지·수천 시간 비디오까지 확장 가능하다고 제시. citeturn20search2turn20search11turn40view5 | 귀하 주제와 가장 가까운 **시스템형 멀티모달 검색 엔진** 사례. 다만 CCTV 사건 보고서+센서 중심 벤치마크 비교는 아니다. |
| CV | **CoLLM: A Large Language Model for Composed Image Retrieval** (CVPR 2025) | reference image + text modification 기반 composed retrieval | 3.4M 규모 MTCIR를 도입하고 최대 15% 개선 보고. citeturn27view0turn40view7 | 멀티모달 query composition의 강력한 사례. 다만 정적인 이미지 중심이며 시간·event grounding 없음. |
| CV | **Cross-modal Causal Relation Alignment for Video Question Grounding** (CVPR 2025) | 질문 답변과 동시에 관련 video segment를 찾는 VideoQG | cross-modal causal alignment로 grounding과 reasoning robustness 개선. citeturn27view1 | 귀하의 **evidence-grounded VQA** 실험 설정에 매우 직접적이다. 단, DB 저장/인덱스 비교는 범위 밖. |
| ML | **UniTime: Universal Video Temporal Grounding with Generative Multi-modal LLMs** (NeurIPS 2025) | MLLM 기반 universal video temporal grounding | 5개 grounding benchmark에서 SOTA를 넘어섰고, VideoQA 정확도도 개선. 예시로 Ego4D-NLQ +6.39%, TaCoS +9.10%. citeturn27view2turn40view3turn40view4 | retrieval-then-reasoning 구조를 정당화하는 핵심 논문. 그러나 저장 구조와 인덱스 비용 비교는 다루지 않는다. |
| ML | **CausalVTG** (NeurIPS 2025) | video temporal grounding에서 dataset bias와 absent query 문제 | causal disentanglement와 counterfactual reasoning 도입. citeturn27view3 | 실제 도시 감시의 **false positive/negative grounding** 문제에 유용. 하지만 시스템·DB 관점 부족. |
| ML | **TimeXL: Explainable Multi-modal Time Series Prediction with LLM-in-the-Loop** (2025) | 시계열+텍스트 멀티모달 예측과 설명 가능성 | 4개 데이터셋에서 최대 8.9% AUC 개선 및 human-centric explanation 보고. citeturn22search2turn40view6 | 센서 로그와 설명 생성, 의료 전환 시 **explainable multimodal time-series** 축을 보강한다. 다만 retrieval workload는 아니다. |

이 표를 종합하면, 해외 탑 티어는 이미 **하이브리드 벡터 검색**, **멀티모달 질의 조합**, **video grounding**, **설명 가능한 시계열 AI**를 각각 빠르게 발전시키고 있습니다. 그러나 **CCTV/교통/도시 이벤트를 단위 객체로 보고, 영상·보고서·센서·시공간 메타데이터를 함께 저장한 뒤, 서로 다른 저장·색인 설계가 retrieval/VQA/grounding/latency/cost에 미치는 영향을 한 논문 안에서 비교하는 작업**은 여전히 드뭅니다. 이 점에서 귀하의 주제는 단순 응용이 아니라 **분절된 연구 흐름을 연결하는 시스템형 연구**로 자리 잡을 수 있습니다. citeturn25view0turn25view2turn25view3turn25view5turn20search11turn27view1turn27view2turn40view6

## 데이터셋과 접근성 조사

실험 성공 가능성은 사실상 데이터 접근성에서 갈립니다. 아래 표는 도시 감시와 의료 전환까지 고려해, **2주 내 파일럿 가능성** 기준으로 정리한 것입니다.

| 데이터셋 | 데이터 타입 | 규모와 특징 | 접근/라이선스 | 개인정보·IRB 쟁점 | 전처리 난이도 | 2주 파일럿 적합성 |
|---|---|---|---|---|---|---|
| **AI Hub 이상행동 CCTV 영상** | 비디오, 어노테이션 | 12종 이상행동, 약 700시간, 8,400컷 이상. AI Hub 설명에는 717시간·8,436컷 통계도 병기됨. citeturn10view0 | AI Hub 신청 필요. 휴대폰 인증 후 자동승인 사례가 있으나, 데이터별 정책 적용. 비상업 연구 활용 중심. citeturn11search0turn11search2 | AI Hub 약관상 재식별 금지와 의심 개인정보 발견 시 신고·삭제 의무. citeturn11search1 | 중상. 긴 영상, 이벤트 단위 재분절 필요 | **높음**. 승인만 빠르면 가장 직접적 |
| **AI Hub 지하철 역사 내 CCTV 이상행동** | 이미지, JSON/XML | 13종 이상행동, 7,030개 클립에서 추출한 100만 장 이상 이미지. citeturn10view1 | AI Hub 다운로드 절차 적용. citeturn11search2 | 공공 보안 영상 계열이라 재식별 금지 원칙 동일. citeturn11search1 | 중간. 이미지 기반이라 키프레임 실험이 쉬움 | **중상**. retrieval-only 파일럿에 용이 |
| **AI City Challenge 2025 Track 2** | 비디오, long caption, bbox | 810개 비디오, 155개 시나리오, 시나리오당 약 5세그먼트, segment당 상세 캡션 2개, 1080p/30fps. BDD100K 기반 외부 검증용 3.4K 비디오도 제공. citeturn10view4 | 공식 Quick Access 제공, 별도 요청서 제거. citeturn10view2 | 공개 챌린지 데이터라 IRB 부담 낮음 | 중간. 캡션이 있어 synthetic report 제작이 매우 쉬움 | **매우 높음** |
| **AI City Challenge 2026 Track 3 TAR** | CCTV 비디오, reasoning QA, 요약/설명 | 3,670개 CCTV 교통 영상, 44,040 reasoning annotation, 10개 과업. 8개 공개 데이터셋에서 구성. citeturn36view0turn37search0 | 공개 챌린지 배포. Hugging Face 공식 릴리스 병행. citeturn37search2turn37search4 | 공개 연구용이지만 교통 영상 특성상 결과물 공개 시 시각정보 재노출 주의 필요 | 중상. 과업이 많아 스키마 설계 필요 | **매우 높음**. explainable event grounding에 최적 |
| **AI City Challenge 2026 Track 1** | multi-camera synthetic video, 2D/3D labels | 1,500 카메라, 250시간 이상 synthetic video, 2D/3D annotation 및 cross-camera identity. citeturn36view0 | 챌린지 배포 | synthetic 중심이라 개인정보 부담 낮음 | 높음. 3D perception 파이프라인 필요 | 중간. retrieval보다 tracking 비중 큼 |
| **서울시 도시고속도로 교통소통 CCTV 설치위치** | 위치 메타데이터 | CCTV 위치 좌표, 지점명 등 제공. citeturn18search0 | 서울 열린데이터광장 공개 | 개인정보 거의 없음 | 낮음 | **매우 높음**. 공간 메타데이터 결합용 |
| **서울시 실시간 돌발 정보 OpenAPI** | 사건 메타데이터, 시간 정보 | 서울 TOPIS 기반 돌발 아이디, 발생 일자/시각 등 OpenAPI 제공. citeturn18search4 | API 키 발급 후 사용 | 개인정보 낮음 | 낮음 | **매우 높음**. 이벤트 보고서·메타 생성용 |
| **기상청 기상자료개방포털 및 API** | 기상 시계열, 예보, 관측 | ASOS는 1904년~, 105개 지점. 단기·초단기 예보 API도 제공. citeturn19search4turn19search1turn19search11 | 공식 포털 및 공공데이터 API | 개인정보 없음 | 낮음 | **매우 높음**. 센서/환경 신호 결합용 |
| **MIMIC-IV / MIMIC-IV-Note** | 구조화 EHR, 자유 텍스트 노트 | 병원·ICU·ED 모듈 포함. Note는 331,794 discharge summary와 2,321,355 radiology report 포함. citeturn14search4turn14search8turn14search2 | PhysioNet credentialed access 필요. 데이터 제3자 공유/온라인 서비스 업로드 금지. citeturn14search3 | 비식별 데이터지만 접근 통제 엄격 | 높음 | **중간**. 승인된 계정이 있으면 강력한 의료 파일럿 가능 |
| **MIMIC-CXR / MIMIC-CXR-JPG** | 흉부 X-ray + radiology report | 약 377,110 이미지, 227,835 study, 비식별 report 포함. citeturn13search0turn13search3turn13search15 | PhysioNet credentialed access | HIPAA Safe Harbor 기준 비식별. 그래도 사용 규정 엄수 필요. citeturn13search0turn14search3 | 중간 | **높음**. 의료 멀티모달 검색의 대표 |
| **eICU / Symile-MIMIC** | ICU structured data / CXR+ECG+labs | eICU는 20만+ ICU admission. Symile-MIMIC은 CXR-ECG-lab 결합 멀티모달. citeturn13search1turn13search7turn13search9 | PhysioNet 공식 접근 | 비식별이지만 credentialed use | 높음 | **중간**. 의료 멀티모달 확장에 적합 |
| **HIRA 보건의료빅데이터개방시스템 / KDCA 국민건강통계 / 보건의료 빅데이터 통합 플랫폼** | 공개 통계, 제한적 환자데이터, 분석센터 환경 | HIRA는 공공데이터·통계·빅데이터센터를 운영. KDCA 건강통계는 무료 공개. 통합 플랫폼은 결합데이터·분산연구·폐쇄망 분석센터 제공. citeturn12search11turn12search5turn15search1turn16search2turn17search0 | 공개 통계는 즉시 사용 가능. 환자 수준 데이터는 신청·심의·분석센터 절차 필요. citeturn17search0turn17search13 | 국내 환자데이터는 법·심의 이슈 큼 | 중간~높음 | **통계 기반은 높음**, **환자 수준은 낮음** |

도시 감시 논문을 2주 내 마무리해야 한다면, **우선순위 데이터 조합은 AI City 2025 Track 2 + 서울 돌발/기상/지도 메타데이터**입니다. 이 조합은 접근성이 높고, 캡션과 박스가 이미 있어 **synthetic incident report**, **event grounding**, **metadata filter** 실험을 곧바로 설계할 수 있습니다. AI City 2026 TAR는 explainable video reasoning에 매우 좋지만, 과업이 많아 논문 범위를 넓힐 위험이 있으므로 **보조 실험 또는 후속 확장**으로 넣는 것이 안정적입니다. AI Hub CCTV는 연구 타당성을 가장 잘 보여 주지만, 승인 지연 가능성이 있어 **성공하면 채택, 지연되면 AI City로 대체**하는 전략이 합리적입니다. citeturn10view2turn10view4turn36view0turn37search0turn11search0turn11search2

의료 도메인에서는 공개성과 재현성을 중시하면 **MIMIC-IV + MIMIC-CXR + MIMIC-IV-Note** 조합이 가장 좋습니다. 하나의 환자/입원 축을 기준으로 **이미지, 보고서, 구조화 임상 변수**를 정렬할 수 있어, 도시 감시 주제의 “영상+보고서+센서 로그” 구조를 의료의 “영상+임상노트+vitals/labs”로 거의 그대로 이식할 수 있습니다. 반대로 한국 환자수준 임상 데이터는 제도적으로 더 가치가 크지만, 2주 안에 신규 승인·반출까지 끝내는 것은 대체로 어렵습니다. citeturn14search2turn14search8turn13search0turn14search3turn17search0turn16search2

## 저장·색인 아키텍처와 파일럿 실험 설계

현재 문헌이 강하게 시사하는 것은, 이 문제에서 승부를 가르는 요소가 단지 “좋은 임베딩 모델”이 아니라 **어디에 무엇을 어떤 단위로 저장하고, 메타데이터 필터와 벡터 검색을 어느 순서에 어떤 비용모델로 실행하느냐**라는 점입니다. 특히 BigVectorBench와 filtered vector search 연구들은 compound query에서 추론 품질과 시스템 성능이 크게 흔들린다고 보고하고 있으며, pgvector·Milvus·Elastic 계열 시스템은 각각 장단점이 분명합니다. 따라서 귀하의 논문은 “어떤 인덱스가 빠르냐”가 아니라, **멀티모달 이벤트 객체를 저장하는 스키마와 질의 계획이 VLM downstream 품질까지 어떻게 바꾸는가**를 비교하는 방식이 가장 강합니다. citeturn25view5turn25view2turn38search15turn38search0turn38search2turn38search16

```mermaid
flowchart LR
    A[수집\n비디오·이미지·보고서·센서·시공간 메타] --> B[전처리\n세그먼트화·캡션/요약·OCR/ASR optional·익명화]
    B --> C[표현 생성\n영상 임베딩·텍스트 임베딩·센서 피처]
    C --> D[저장 계층\n원문 객체 저장]
    C --> E[색인 계층\n벡터 인덱스·역색인·시계열 인덱스·공간 인덱스]
    E --> F[검색 계획기\nsparse+dense+filter+time-range]
    F --> G[재순위화\ncross-encoder or VLM reranker]
    G --> H[근거 패키징\n프레임·시간구간·리포트 문장·메타데이터]
    H --> I[VLM QA 또는 이벤트 grounding]
    I --> J[평가\nRecall@k·MRR·Temporal IoU·VQA Acc·Latency·Cost]
```

위 파이프라인은 DB 쪽의 hybrid vector query, filtered search, vector benchmarking 연구와 IR/CV 쪽 retrieval-then-reasoning 및 grounding 논문을 통합한 형태입니다. 귀하 논문의 가치가 생기는 지점은 바로 **F 단계의 검색 계획기**와 **E 단계의 저장·색인 설계**를 바꿔 가며 downstream을 비교하는 데 있습니다. citeturn25view0turn25view2turn25view3turn27view1turn27view2

아래는 구현 후보를 연구 목적에 맞게 재구성한 비교표입니다. 정확도·지연·비용 평가는 절대 수치가 아니라, 문헌과 공식 기술문서를 바탕으로 한 **정성적 추정**입니다. citeturn38search0turn38search2turn38search16turn38search4turn25view3turn25view4turn38search15

| 아키텍처 후보 | 설계 설명 | 장점 | 약점 | 예상 정확도 | 예상 지연 | 예상 비용 | 구현 난이도 | 적합도 |
|---|---|---|---|---|---|---|---|---|
| **PostgreSQL + pgvector + JSONB/PostGIS** | 하나의 RDB에 벡터, 구조화 속성, 공간 질의를 통합 | SQL 일관성, JOIN 쉬움, 실험 재현성 높음 | filtered ANN 최적화가 약할 수 있고 optimizer 선택이 민감 | 중상 | 중간 | 낮음~중간 | 낮음 | **최초 파일럿 최적** citeturn38search0turn26view0turn38search15 |
| **OpenSearch/Elasticsearch hybrid** | BM25 + vector + metadata filter를 한 검색 엔진에서 통합 | sparse+dense fusion, 재현성 좋은 hybrid retrieval | 관계형 JOIN과 시계열 연계는 약함 | 상 | 중상 | 중간 | 중간 | **보고서+메타 비중이 클 때 강함** citeturn38search16 |
| **Milvus + 외부 RDB** | 벡터 검색은 Milvus, 메타/관계 데이터는 PostgreSQL | multi-vector hybrid, metadata filtered search 지원 | 이중 저장소 동기화 부담 | 상 | 상 | 중간~높음 | 중상 | **정확도/확장성 비교 실험에 좋음** citeturn38search2turn38search8turn38search11 |
| **Timescale/시계열 DB + vector** | 시계열·이벤트 로그와 벡터를 시간축 중심으로 통합 | 시간 범위 필터와 최근성 질의에 강함 | 영상/문서 다중모달 조합은 추가 설계 필요 | 중상 | 상 | 중간 | 중간 | **센서 로그 비중이 클 때 유리** citeturn38search4turn38search13 |
| **Lakehouse + FAISS/Lance 계열** | 원천 데이터를 파일 중심으로 저장하고 오프라인 색인 | 대용량 원천 보관·실험 확장 쉬움 | 온라인 지연/재색인/실시간성 약함 | 중상 | 낮음~중간 | 낮음 | 중상 | **배치형 벤치마크에 적합** citeturn25view5 |

2주 파일럿 논문 기준으로는 **두 가지 체제만 비교해도 충분히 논문다운 메시지**를 만들 수 있습니다. 가장 안전한 조합은 다음과 같습니다.  
첫째, **단일 저장소형**: PostgreSQL + pgvector + JSONB/PostGIS.  
둘째, **하이브리드 엔진형**: OpenSearch 또는 Milvus + PostgreSQL.  
이 두 체제를 비교하면 “단일 시스템의 단순성”과 “전용 벡터 엔진의 검색력”을 동시에 말할 수 있고, 구현량도 통제 가능합니다. citeturn38search0turn38search2turn38search16turn26view0

실험 설계는 다음처럼 잡는 것이 좋습니다.

| 실험 축 | 질의 예시 | 비교 베이스라인 | 평가지표 | 기대 메시지 |
|---|---|---|---|---|
| **멀티모달 retrieval** | “비 오는 날 횡단보도 앞 급정거 유발 장면” | BM25 보고서만 / dense caption만 / sparse+dense hybrid | Recall@5, Recall@10, MRR, nDCG | 텍스트만보다 영상+보고서+메타 융합이 유리한가 |
| **vector + metadata filtering** | “야간, 강수, 교차로, 보행자 포함 사건” | post-filter / pre-filter / hybrid query planner | Recall@k, P50/P95 latency, filter selectivity별 성능 | 필터 전략이 정확도와 latency를 어떻게 바꾸는가 |
| **event grounding** | 질의에 해당하는 핵심 시간 구간 찾기 | caption segment retrieval / coarse-to-fine retrieval / reranker 추가 | Temporal IoU, mAP, grounding accuracy | 세그먼트화와 재순위화가 grounding에 미치는 영향 |
| **evidence-grounded VQA** | “왜 차량이 정지했는가?”, “사건 전후 보행자 행동은?” | no-retrieval VLM / retrieval-only / retrieval+rationale | VQA accuracy, faithfulness 체크, citation hit rate | retrieval이 설명 가능성과 정확도를 동시에 높이는가 |
| **비용·운영성** | 동일 질의 묶음 반복 실행 | semantic cache 유무 / keyframe 수 변화 | $/1k query 추정, GPU/CPU 시간, 저장공간 | 실무형 시스템으로서 유지 가능한가 |

파일럿에서는 **질적 지표보다 검색·grounding 지표를 우선**하는 것이 안전합니다. 즉, 2주 내 목표는 “end-to-end 앱 완성”이 아니라,  
**(a) 데이터 스키마 정의 → (b) 두 아키텍처 비교 → (c) retrieval/grounding에서 차이 확인**입니다.  
VQA는 retrieval 결과를 소비하는 **보조 실험**으로 두는 편이 낫습니다. 그 이유는 VQA까지 주력으로 가면 모델 선택, prompt 편차, API 비용이 변수가 너무 많아져서 저장·인덱스 논문의 메시지가 흐려지기 때문입니다. citeturn25view2turn27view1turn27view2turn38search15

## 의료 도메인 전환 가능성 분석

질문에 대한 결론부터 말하면, **같은 연구 주제를 대한민국 의료 데이터 도메인으로 재설계하는 것은 기술적으로 가능하지만, 현재 2주 일정 기준에서는 “공개·비식별 데이터 기반 파일럿”과 “국내 환자수준 데이터 확장”을 분리하는 것이 필수**입니다. 도시 감시에서의 객체는 “사건 세그먼트”이고, 의료에서의 객체는 “환자 방문/입원 에피소드”가 됩니다. 영상은 CXR/CT/병리 이미지로, 사건 보고서는 radiology report/clinical note로, 센서 로그는 vital signs/lab time-series로 치환하면 동일한 멀티모달 VLM-DB 워크로드를 설계할 수 있습니다. citeturn13search0turn14search4turn14search8turn13search9

다만 한국의 의료 데이터는 법·윤리 장벽이 분명합니다. 개인정보 보호법은 개인정보 처리와 보호의 기본 원칙을 두고 있고, 생명윤리 및 안전에 관한 법률은 인간대상연구와 IRB 절차를 규정합니다. 2024년 개정 보건의료데이터 활용 가이드라인은 연구 목적의 보건의료데이터 활용에서도 **접근권한 통제, 폐쇄환경 활용, 추가적인 안전조치**를 강조하고 있습니다. 또한 보건의료 빅데이터 통합 플랫폼은 데이터 이용 신청, 통합 사전검토, 연구평가위원회 심의, 데이터 결합 및 추가 비식별화, 반출 적정성 심의 절차를 명시합니다. 즉, 한국 환자수준 데이터는 “받아서 내 서버에 바로 저장”하는 방식이 아니라 **폐쇄망 분석센터 또는 원격 분석 환경**을 전제로 설계해야 합니다. citeturn12search6turn12search4turn12search7turn12search3turn17search0turn17search3turn17search13

이 때문에 2주 파일럿 관점에서는 의료 전환 전략을 세 단계로 보는 것이 현실적입니다.

| 전환 경로 | 데이터 | 장점 | 제약 | 권장 용도 |
|---|---|---|---|---|
| **공개 멀티모달 파일럿** | MIMIC-IV + MIMIC-IV-Note + MIMIC-CXR + eICU/Symile-MIMIC | 이미지·노트·구조화 시계열을 직접 결합 가능, 국제 재현성 높음 | PhysioNet credential 필요, 외부 온라인 서비스 전송 금지 | **가장 현실적인 의료 파일럿** citeturn14search0turn14search8turn13search0turn13search1turn13search9turn14search3 |
| **국내 공개 통계 기반 실험** | KDCA 국민건강통계, HIRA 공개 통계, KOSIS | 즉시 접근 가능, 법적 부담 낮음 | 환자 수준 event grounding/VLM QA는 제한적 | **서론·확장성 정리용** citeturn15search1turn12search11turn39search12 |
| **국내 환자수준 임상 확장** | HIRA/NHIS/보건의료 빅데이터 통합 플랫폼 | 한국 의료 현실성과 정책 기여가 큼 | 신청·심의·분석센터·반출 절차로 2주 내 신규 진입이 사실상 어려움 | **후속 6개월 과제용** citeturn17search0turn16search2turn17search8turn16search12 |

의료에서 특히 중요한 것은 **질의의 의미가 검색보다 더 고위험**이라는 점입니다. 예를 들어 도시 감시에서 “사건을 놓쳤다”는 것은 시스템 성능 이슈이지만, 의료에서 “잘못된 근거를 붙인 답변”은 임상적 위험이 됩니다. 따라서 의료 도메인으로 갈 경우, 평가 지표도 Recall@k와 latency만으로는 부족하고, **evidence faithfulness, clinician review, error severity**가 필요합니다. TimeXL 계열 연구는 멀티모달 시계열과 설명 가능성을 강화하고 있으므로, 의료 확장 시에는 단순 retrieval보다 **retrieval + explanation + auditability** 구조를 강하게 가져가는 편이 좋습니다. citeturn40view6turn22search5turn22search16

정리하면, **의료 도메인 전환은 가능하다. 그러나 한국 의료 데이터로 바로 논문을 완성하는 것이 아니라, 공개 MIMIC 계열로 워크로드를 검증한 뒤 한국 HIRA/NHIS/통합 플랫폼 방향을 “실제 적용 가능성”으로 제시하는 것이 현 시점 최적 전략**입니다. 이 구조로 가면 귀하의 논문은 도시 감시를 주실험으로 유지하면서도, 토론 섹션에서 의료 확장성을 매우 설득력 있게 제시할 수 있습니다. citeturn14search2turn13search0turn17search0turn12search3

## 연구 공백과 구체적 주제 제안

가장 중요한 연구 공백은 세 가지입니다. 첫째, DB 연구는 filtered vector search와 hybrid query를 깊이 다루지만, **멀티모달 event grounding 품질**과는 아직 강하게 연결되지 않습니다. 둘째, IR/CV/ML 연구는 VLM 기반 retrieval·grounding·VQA를 빠르게 발전시키지만, **저장 구조·색인 비용·갱신성·SQL/metadata filter planning**을 거의 다루지 않습니다. 셋째, 멀티모달 time-series 설명 가능성 연구는 늘고 있지만, **검색 워크로드와 VLM evidence retrieval**을 함께 다루는 방향은 아직 약합니다. 즉, 귀하 주제의 핵심 갭은 **모델 연구와 데이터관리 연구 사이의 공백**입니다. citeturn25view2turn25view5turn27view1turn27view2turn40view6

이 공백을 바탕으로, 논문 수준의 독립 주제를 다음 네 가지로 구체화할 수 있습니다.

| 제안 주제 | 목표와 핵심 기여 | 필요 데이터 | 예상 방법론 | 2주 파일럿 | 6개월 확장 |
|---|---|---|---|---|---|
| **멀티모달 도시 감시 데이터를 위한 하이브리드 VLM-DB 검색 워크로드 설계와 저장·색인 구조 비교** | 귀하의 현재 최우선 주제. 이벤트 객체 스키마와 저장·색인 설계를 정의하고 retrieval/grounding/latency/cost 비교 | AI City 2025 T2, AI City 2026 TAR, 서울 돌발/기상/지도, AI Hub optional | Postgres 단일형 vs hybrid 엔진형 비교, sparse+dense+filter, reranking | **즉시 가능** | DBR 논문 → 후속 SIGMOD/VLDB demo/benchmark로 확장 |
| **Selectivity-aware Filter Planning for Multimodal Event Retrieval** | 필터 selectivity가 멀티모달 검색 품질을 어떻게 바꾸는지 체계화 | AI City + synthetic metadata | pre/post/runtime filtering, selectivity bucketing, planner heuristic | 작게 가능 | filtered vector search 논문으로 독립 가능 |
| **Evidence-grounded Video QA over DB-managed Multimodal Corpora** | retrieval 근거를 명시하는 VLM QA 구조와 신뢰성 평가 | TAR, Track2, 보고서/캡션 | retrieved evidence package + VLM QA + citation hit rate/faithfulness 평가 | 보조 실험 가능 | explainable VLM 시스템 논문으로 확장 |
| **의료 멀티모달 임상 검색 워크로드의 설계와 공개 데이터 기반 검증** | 도시 감시 설계를 의료로 이식한 benchmark 제안 | MIMIC-IV, Note, CXR, eICU/Symile-MIMIC | episode-centric schema, image+note+vitals retrieval, clinical grounding | credential 있으면 소규모 가능 | 한국 HIRA/NHIS 방향의 확장 제안 가능 |

이 중에서 **지금 가장 성립 가능성이 높은 것은 첫 번째 주제**입니다. 이유는 명확합니다. 데이터 접근성이 좋고, 저장·색인 비교라는 DB 핵심 메시지가 있으며, 해외 상위권 커뮤니티가 보고 있는 **hybrid vector search**와 **multimodal grounding** 사이의 빈 공간을 메울 수 있기 때문입니다. 두 번째 주제는 첫 번째 주제 안의 “방법론적 심화판”으로 볼 수 있고, 세 번째 주제는 2주 파일럿에서는 부차적이지만 논문의 설득력을 크게 높입니다. 의료 주제는 분명 매력적이지만, 지금 당장 메인 실험으로 가져가면 일정 리스크가 큽니다. citeturn25view0turn25view2turn25view3turn20search11turn27view1turn27view2turn17search0

논문 제목 후보를 연구자 시점에서 다듬으면 다음 두 버전이 강합니다.  
**버전 A**: “멀티모달 도시 감시 데이터를 위한 하이브리드 VLM-DB 검색 워크로드 설계와 저장·색인 구조 비교”  
**버전 B**: “도시 이벤트 질의응답을 위한 멀티모달 VLM-DB 통합 검색: 영상·보고서·시공간 메타데이터의 저장·색인 비교”  
A는 **DBR/국내저널형**, B는 **국제 워크숍/컨퍼런스형** 느낌이 강합니다. citeturn39search4turn39search0

## 우선순위 작업과 위험요인 대응

지금 필요한 것은 자료를 더 넓게 모으는 일이 아니라, **실패 확률이 낮은 실행 순서**를 잡는 일입니다. 아래 우선순위는 2주 기준의 현실적인 작업 순서입니다.

| 우선순위 | 작업 | 이유 | 주요 위험 | 대응책 |
|---|---|---|---|---|
| **즉시** | AI City 2025 Track 2와 2026 TAR 샘플 다운로드 및 스키마 초안 작성 | 공식 Quick Access, 즉시 실험 가능 | 범위 과대 | Track2를 주실험, TAR는 보조로 제한 citeturn10view2turn10view4turn37search0 |
| **즉시** | 이벤트 객체 스키마 정의: `segment_id`, `video_id`, `time_range`, `caption/report`, `bbox`, `weather`, `location`, `event_type` | 논문 메시지의 핵심이 DB 스키마/워크로드 정의에 있음 | 스키마 과복잡화 | 필수 속성만 먼저 정의, optional 컬럼은 뒤로 |
| **즉시** | PostgreSQL + pgvector 단일형 프로토타입 구현 | 구현 난이도 낮고 DBR형 메시지에 적합 | filter recall 저하 | exact search와 ANN 둘 다 측정 citeturn38search0turn38search15 |
| **차순위** | OpenSearch 또는 Milvus 기반 대조군 구현 | 하이브리드 검색 비교축 확보 | 인프라 복잡성 | 한 가지만 선택. 추천은 OpenSearch if reports 중요, Milvus if vectors 중요 citeturn38search2turn38search16 |
| **차순위** | 서울 돌발 API·CCTV 위치·기상 데이터 결합 | 메타필터 실험을 실전형으로 바꿔 줌 | 시간 정렬 오류 | UTC/KST 정규화와 공간 키 표준화 citeturn18search0turn18search4turn19search1 |
| **조건부** | AI Hub CCTV 신청 | 국내 데이터 타당성 강화 | 승인 지연 | 논문 본실험은 AI City로 유지하고, AI Hub는 추가 검증으로 처리 citeturn11search0turn11search2 |
| **조건부** | 의료 공개데이터 경로 사전 점검 | 후속 확장성 확보 | credential 없음 | 본문에서는 설계 가능성으로만 논의, 실험은 도시 중심 유지 citeturn14search3turn14search0turn13search0 |

가장 큰 위험은 세 가지입니다. 첫째, **AI Hub 승인 지연**입니다. 이 경우에도 AI City는 이미 충분히 강한 주실험 데이터이므로, 논문 일정 자체는 흔들리지 않습니다. 둘째, **보고서 텍스트 부족**입니다. 이를 해결하려면 Track 2의 long caption을 기반으로 간단한 incident report template를 생성하고, 사람이 50–100개 정도만 샘플 검수하면 됩니다. 중요한 것은 이를 반드시 **“synthetic/templated report”**라고 논문에 명시하는 것입니다. 셋째, **VLM 추론 비용 과다**입니다. 이 경우 keyframe/segment retrieval 중심으로 먼저 실험하고, VQA는 retrieval 결과 1–3개 세그먼트에만 제한해 비용을 낮추면 됩니다. citeturn10view4turn37search0turn38search0turn27view2

마지막으로, 현재 시점의 최종 권고는 다음과 같습니다.  
도시 감시 도메인을 유지하되, **논문 서술의 중심을 “모델 성능”이 아니라 “워크로드 정의와 저장·색인 비교”에 둔다.**  
데이터는 **AI City 2025 Track 2를 기본**, **TAR를 보조 reasoning 실험**, **서울 메타데이터를 필터 실험**, **AI Hub는 승인 시 국내 검증 데이터**로 둔다.  
의료는 **MIMIC 기반 확장 가능성**으로 별도 절을 두고, 한국 의료 환자수준 데이터는 **후속 연구 계획**으로 정리한다.  
이 구성이 현재 조건에서 가장 **엄밀하고, 실현 가능하며, DBR에도 맞고, 해외 상위권 흐름과의 연결도 분명한 설계**입니다. citeturn10view2turn10view4turn37search0turn18search4turn19search1turn33view0turn25view2turn25view5turn27view2turn14search2