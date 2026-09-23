# KIISE DBR 심사 보고서 — 도시 감시형 멀티모달 VLM-DB 논문

**대상 원고:** `manuscript/kiise_dbr_manuscript_v1_true_multimodal.md` (v1, 2026-07-07)
**심사 종합:** 9개 차원 findings + 독립 검증 반영 · 심사 총괄 종합

---

## 1. 총평 (Editor Summary)

본 원고는 VRU-Accident와 AI Hub CCTV를 공통 canonical 스키마로 정규화하고, 시각(text/image-to-video)·텍스트·메타데이터 evidence의 검색·선택 구조가 AI 답변 품질을 좌우한다는 것을 통제 실험으로 보이려는 논문이다. **실제로 잘 입증한 것**은 두 가지다. (1) 생성 모델을 고정하고 DB evidence 구성만 바꾼 답변 계층 실험에서 evidence 품질이 정확도를 단조로 끌어올린다는 것(표 13, closed 0.31 → oracle 0.75), (2) 다각도 CCTV에서 "두 시점을 쌓는 것"이 "더 나은 한 시점을 고르는 것"과 통계적으로 등가라는 사전등록·TOST·permutation 대조·다중 VLM 재현으로 방어된 발견(표 20). **반면 초록의 헤드라인 검색 결과**(metadata prefilter nDCG 0.13→0.74, AI Hub 완벽 지표)는 코드 검증 결과 상당 부분이 검색 품질이 아니라, 정답을 정의하는 facet이 후보 필터·코퍼스·질의에 직접 흘러든 **순환/누수의 구조적 산물**이며 원고는 이를 flagship 결과에서 공개하지 않는다. 또한 제목·투고 주제가 약속한 3축(정확도·지연·비용)과 저장·색인 구조 비교는 본문에서 정확도 1축으로 축소되었고, "센서·시공간 메타데이터 결합"은 어떤 main 데이터셋에서도 실현되지 않았다. 요컨대 **정직하게 방어되는 진짜 기여(답변 계층·시점 선택 통제 실험)와, 공개되지 않은 순환에 기댄 검색 헤드라인이 한 논문에 공존**한다.

---

## 2. 심사 판정

### 판정: **Major Revision** (재심 필수 · 조건부)

**근거 (DBR 학회지 기준):**

- **Reject가 아닌 이유:** 논문의 지적 무게중심(저자 스스로 §7.1·§7.4·§7.6에서 "가장 중요한 결과"로 지목하는 답변 계층 통제 실험과 다각도 시점 선택)은 누수 결함과 **독립적**이며 방법론적으로 견고하다(사전등록, TOST, permutation 대조, 다중 VLM, closed/distractor 하한, IM1 self-frame 제외, full-frame 사용). 재현성도 견실하다(심사 가설이던 '버전 조작'은 실제 conda 환경 대조로 반증됨). 즉 살릴 수 있는 실체가 분명하다.
- **Accept/Minor가 아닌 이유:** 초록·표 6/7의 헤드라인 검색 이득이 CONFIRMED·load-bearing인 순환/누수(F1·F2·F3)에 의해 부분적으로 예정되어 있고 원고가 이를 flagship에서 공개하지 않는다. DB 학회지에서 "검색 품질 향상"이 워크로드 설계의 산물이라는 점은 결과 해석의 타당성을 직접 흔든다. 여기에 (a) 핵심 DB-시스템 기여축(저장·색인 구조 비교)의 본문 부재, (b) 가장 근접한 선행 시스템(ForeSea) 미인용, (c) 데이터/코드 공개 진술 부재가 겹친다. 이는 문구 수정 수준을 넘는 **재실험·재측정·재프레이밍**을 요구한다.
- **조건 명시:** 본 Major Revision은 사소하지 않다. 재심에서 **F1–F3의 순환을 (i) 정답 정의와 독립된 relevance/질의 셋으로 재확립하거나, (ii) 검색 헤드라인을 진단 결과로 격하하고 논문을 답변 계층·시점 선택 기여로 재포지셔닝**하지 못하면 Reject로 귀결된다.

---

## 3. 강점 (공정하게 인정)

- **엔지니어링·데이터 위생:** 4종 이질 데이터셋을 단일 canonical 스키마(clips/documents/metadata/queries/qrels/frames/embeddings)로 정규화하고 adapter로 재현 가능하게 구축. media/label 무결성 audit로 `missing_media=0, missing_labels=0` 확인(표 3 Errors=0).
- **다각도 답변 실험(6.13, 표 20)은 진짜 발견:** 사전등록(LOCKED)·Go/No-Go gate·both−better TOST 등가·permutation 대조로 겉보기 시점 상보성을 자기반증·3~4개 VLM 재현. evidence frame을 bbox crop이 아닌 full-frame 512px로 공급해 주석 누수를 통제. 심사에서 가장 방어력 높은 축이다.
- **답변 계층 통제 실험(6.8, 표 13)의 논리적 견고성:** closed·distractor 하한을 포함하고, priming 교란을 감안해도 방향(vector-only 0.665 ≫ closed 0.308)이 유지된다. 즉 "evidence 유무·품질이 답변을 좌우"라는 결론은 흔들리지 않는다.
- **문서화된 자기비판이 실제 반영된 부분:** LLM/VLM '미사용' 자기모순 정정(표 4에 answer-gen LLM·answer-level VLM 행 추가), 기여 5의 '고정 통제 실험' 재작성, '동기 촬영' 표현 제거(grep 0건), latency 우위 명시적 미주장(L196).
- **통계 처리 KCI 평균 이상:** 사전등록 SESOI·gate·해석규칙, per-query paired 설계, 올바른 TOST(90% CI ⊂ ±SESOI), full-query n(244/133), 고정 seed 5,000회 bootstrap.
- **재현성·인용 무결성:** 원고 부록 A 버전이 실제 `kiise-vlmdb` 환경과 정확히 일치(조작 반증). 표 13/16/18/20 수치가 결과 파일과 자릿수까지 일치. 참고문헌 [1]–[22] 실재·과거일자·id 정확, 기여문이 '최초/유일' 과장 회피.

---

## 4. 치명적/주요 결함 (우선순위 순)

> 최상단 F1–F5는 **load-bearing** (핵심 주장의 타당성에 직결). F1·F2는 **CONFIRMED critical**.

### ■ F1 [LEAK-1 / METRIC-2 / DATA-1(qrels)] — metadata prefilter 헤드라인이 정답 정의 facet에 대한 후보 축소(순환)인데 'query planning 성과'로 재프레이밍 · **CONFIRMED · critical · load-bearing**
- **문제:** 두 어댑터(`vru_accident.py` L368–436, `aihub_intelligent_cctv.py` L438–497)에서 prefilter가 쓰는 `metadata_filters`는 **항상 qrel을 정의하는 facet의 진부분집합**(의미 facet인 accident_type/event_class는 필터에서 제외). relevant clip은 모든 qrel facet을 만족하므로 부분집합 필터를 절대 통과 → `retrieval.py` `_vector_prefilter_ranking`(L300–314)에서 **B4 ≥ B2가 구조적으로 보장**. 난도별 CSV가 실측 증명: 필터 facet 0개 weak 질의에서 B2=B4(이득 정확히 0.0000), 필터 facet 3개 strong에서 nDCG 0.185→0.9935.
- **타당성 위협:** 초록 헤드라인 "nDCG 0.13→0.74"(L9·L15)와 표 6 B4 nDCG 0.9736 vs B2 0.4476(L185)이 **부분적으로 tautological**. 프로젝트 자체가 project_md/34에서 동일 병(候補 축소 착시)을 이미 인정했으나 그 교훈이 flagship 결과표에는 미적용.
- **수정 요구:** (P0) prefilter facet을 qrel 정의에서 **독립**시킨 워크로드(relevance는 사람 판단/임베딩 최근접, 필터는 무관 운영 조건)로 재측정하거나, 불가하면 prefilter 이득을 **성능 주장에서 빼고 진단 결과로 격하**. 본문에 `metadata_filters ⊂ qrel_filters`와 B4≥B2 구조 보장을 명시.

### ■ F2 [LEAK-2] — 검색 코퍼스에 정답 라벨을 그대로 재진술하는 문서가 포함되어 완벽 지표를 견인 · **CONFIRMED · critical · load-bearing**
- **문제:** `vru_accident.py` L253–263이 qrel/metadata를 정의하는 동일 라벨로 facet 문서를 생성하고, `aihub_intelligent_cctv.py` L286–309의 event/temporal statement가 event_class 라벨을 축자 재진술. `retrieval.py` L114/L132가 이 문서들을 BM25·FAISS 코퍼스에 그대로 적재. 질의는 동일 라벨 문자열 사용.
- **타당성 위협:** 표 6 AI Hub B3/B4 MRR=nDCG@10=**1.0000**(L192–193), B5=0.9977은 의미 검색이 아니라 **라벨 자기재진술 순환**의 산물. 원고는 '질의-라벨 어휘 정렬'만 부분 공개(L196·L221)하고, **코퍼스가 정답을 재진술한다는 사실은 미공개**.
- **수정 요구:** (P0) 정답 facet 재진술 문서(vqa_facet_statement/event_statement/temporal_statement)를 코퍼스에서 제외하고 실제 caption만으로 재측정. 포함 시 완벽 지표를 그 artifact로 명시 설명.

### ■ F3 [LEAK-3] — B2 vector-only에 합성 4-facet 접속 질의를 투입해 대조군을 억압, B4−B2 델타를 양방향 팽창 · **CONFIRMED · major · load-bearing**
- **문제:** `vru_accident.py` L426–430의 strong 질의는 4개 facet 기계적 접속("Find {weather} {location} accident videos on {road_type} roads where the accident type is {accident_type}"). 동일 인코더가 weak B2 nDCG 0.9117 → strong B2 0.1851로 붕괴 — 질의 합성 artifact.
- **타당성 위협:** 표 16 헤드라인(VRU 텍스트 B4 vs B2, +0.5260, CI[0.475,0.575], L358)이 **양끝에서 팽창**(B2는 접속 질의로 억압, B4는 F1 후보 축소로 상승).
- **수정 요구:** (P0) B2에 실제 사용자형 질의(또는 semantic_filter만 반영한 질의)를 공정 제공하거나, 개선을 '동일 질의·필터 유무'로만 격리 재측정. 표 16에 대조군 억압 caveat 명기.

### ■ F4 [DATA-1(표현)] — 평가 질의를 '자연어 질의'로 제시하나 실제로는 facet 조합 템플릿 + relevance≡3 합성 범주매칭(positive 최대 419) · **PLAUSIBLE · major · load-bearing**
- **문제:** `queries.jsonl`은 `"Find videos where the accident type is {value}"` 템플릿(.format 채움)이고 동일 facet 값을 가진 모든 clip에 relevance=3 부여(질의당 positive 최대 419). 원고 표 2(L101)는 이를 "자연어 질의와 metadata filter"로 표기.
- **타당성 위협:** class-membership 질의에 nDCG를 적용하면 검색 지표가 의미검색이 아니라 라벨 부기(bookkeeping)를 측정. F1·F2 순환의 근원.
- **수정 요구:** (P0) "자연어 질의"를 "구조화 조건 기반 템플릿 질의"로 정정하고 relevance 합성 방식을 §3에 명시. 관제 시나리오 실제 자연어 질의 소규모 셋으로 템플릿-비의존 재현 제시. positive 수백 질의에는 set-retrieval 지표 논의.

### ■ F5 [NOV-1] — 가장 직접적인 선행 시스템 ForeSea/ForeSeaQA 미인용·미차별화 · **CONFIRMED · major · load-bearing**
- **문제:** 감시영상 image+text 멀티모달 질의 VideoRAG 시스템 ForeSea/ForeSeaQA를 팀이 survey/paper/에 PDF 보관·project_md/01에서 분석까지 했으나 원고 본문·참고문헌 어디에도 언급 0(grep 0건). UrBench 등 multi-view 도시 LMM 벤치마크도 6.13 헤드라인에 anchoring 안 됨.
- **타당성 위협:** novelty 포지셔닝 결함. 최근접 선행 시스템 대비 본 연구 차별점(생성모델 고정 통제로 DB evidence 계층 분리, selection>accumulation)이 서술되지 않음.
- **수정 요구:** (P0/P1) 2절에 ForeSea/ForeSeaQA·UrBench를 인용하고 평가축 차이를 명시 차별화.
- (참고) 이 findings의 하위주장 중 'ForeSea arXiv id 미래·조작 의심'은 **REFUTED** — 실재 논문·과거일자로 확인. 인용 추가 시 provenance 문제 없음.

---

### ■ F6 [SCOPE-2 / CONSIST-1(writing) / VENUE-1] — 핵심 DB-시스템 기여(저장·색인 구조 비교)가 본문 부재 + 부속문서 과약속 + 고아 그림 · **CONFIRMED · major**
- **문제:** RQ7 색인 벤치마크(Flat/IVF/HNSW/IVF-PQ Pareto, filtered-ANN selectivity)는 프로젝트 기록·제출 그림 폴더에 실재하나 원고 grep(HNSW/IVF/Pareto/selectivity) 0건. `fig_index_structure_pareto.png`·`fig_selectivity_filter.png`가 제출 폴더에 있으나 원고 참조 0건(고아). README·submission_materials_index·preflight는 'index benchmark 포함 v1'을 반복 선언. 그나마도 main과 다른 데이터셋(시내도로 CCTV 132K + synthetic 1M)에서 QA와 분리된 ANN 충실도 지표로 측정됨.
- **타당성 위협:** DBR의 DB-시스템 기여로 내세울 축이 본문에 없어, 사실상 "멀티모달 IR + RAG 답변 평가" 논문이 됨(§6 표 전부 검색·답변 품질, latency/cost/index 표 0건).
- **수정 요구:** (P0) 다음 중 택1을 확정: **(A)** 색인 벤치마크를 6절/부록에 정식 통합(별개 코퍼스·synthetic·충실도 지표임을 한계로 명시)하고 제목의 storage/indexing 축 회복, **(B)** 색인 벤치마크를 범위에서 제외하고 README·부속문서·제목의 'indexing 비교' 문구를 'metadata-aware 검색·선택 구조 분석'으로 정정·고아 그림 분리. 어느 쪽이든 부속문서-원고 정합.

### ■ F7 [SCOPE-1] — 지향 3축(정확도·지연·비용) 중 정확도만 전달, latency 명시 포기·cost 미정량화 · **CONFIRMED · major**
- **문제:** L196에서 latency 우위 명시 포기(미격리 wall-clock), cost는 정성 언급 2건(L71, L459)뿐 정량 표 0건. 폐기된 latency 표는 paper_assets에 실재하나 원고 참조 0건.
- **타당성 위협:** 투고 주제가 약속한 3축 균형 비교가 1축으로 축소. (원고가 거짓 주장을 하진 않으므로 원고 내부 결함이라기보다 지향 대비 범위 축소.)
- **수정 요구:** (P1) 서론/1.1절에 명시적 scope 경계 문장 추가("evidence 검색·선택 정확도에 집중, latency/cost는 후속"). build-time·index/artifact 크기·검색 연산량 같은 **offline cost 대리지표**라도 표로 부분 정량화. 제목·초록의 '성능'을 'evidence 검색·선택 품질'로 좁힘.

### ■ F8 [DATA-4 / SCOPE-3 / DATA-2] — '영상+사건보고서+센서·시공간 메타데이터' 3요소 결합이 어떤 main 데이터셋에서도 미실현 · **CONFIRMED · major**
- **문제:** main 데이터(VRU 1,000 + AIHub 269)에 센서/GPS/시공간 로그 부재(원고 sensor/시공간/GPS grep 0건). 메타데이터 실체는 저카디널리티 범주 facet(event_class/night/road_type/weather 등). VRU facet은 **VQA 4지선다 정답을 역파싱**한 것(`vru_accident.py` L186–199, facet_source='parsed_vqa')이며 accident_reason(distinct 142/1000)·prevention_method(210/1000)는 준자유텍스트인데 '구조화 facet'으로 병기. '사건 보고서'는 QA 파생 caption. 정형 로그(CityFlow-NL, sinnaedoro_traffic 통과차량/보행량 CSV)는 processed/에 실재하나 main 미포함.
- **타당성 위협:** '멀티모달 데이터베이스'·'센서/시공간 메타데이터 결합' 명명이 현재 자산으로는 방어 약함.
- **수정 요구:** (P1) 제목·초록의 '센서/시공간 메타데이터'·'사건 보고서'를 실제 자산(범주형 event/time/context facet, QA 캡션)에 맞게 좁히고, facet별 카디널리티·자유텍스트성을 표로 투명 공개(accident_reason/prevention_method는 free-text로 재분류). (P2) 정형 로그 1개(CityFlow-NL/sinnaedoro_traffic)를 실제 결합 워크로드로 승격.

### ■ F9 [METRIC-1] — Recall@10/@20이 다수-positive qrels로 구조적 상한, caveat 없이 절대값 제시 · **CONFIRMED · major**
- **문제:** `metrics.py` L9–13에서 `recall@k = |top-k ∩ positives| / |positives|`이므로 positives>k면 상한 k/|positives|<1. 표 6 AI Hub B3/B4는 nDCG@10=**1.0000**(랭킹 이상적)인데 Recall@10=0.8644 — 0.1356 미달은 검색 오류가 아니라 순전히 정답 수>10 때문. 원고에 many-positives caveat 없음(grep 0건).
- **타당성 위협:** 절대 Recall이 회수율로 오독될 수 있음(상대비교만 유효).
- **수정 요구:** (P0) 각 Recall 표에 정답 집합 크기 분포·max-achievable Recall 병기, 또는 nDCG@10/MRR을 주지표로 격상하고 capped-Recall/R-precision 병용. "Recall@10은 다수 정답으로 상한이 걸려 절대값 직접 해석 불가" caveat 추가.

### ■ F10 [REPRO-2] — 데이터·임베딩 전량 리포 외부 로컬 경로, 데이터/코드 availability 진술 부재로 제3자 재현 불가 · **CONFIRMED · major**
- **문제:** `KIISE_datasociety/Datasets → /hdd2/...` symlink, audit·freeze 산출물이 절대경로·머신 하드코딩. 원고에 availability/DOI/공개 리포 진술 전무.
- **타당성 위협:** DBR가 중시하는 재현성의 전달 가능성 결여(단 AI Hub는 재배포 불가 라이선스라는 불가피성 병존).
- **수정 요구:** (P0) 데이터 availability statement 명시(VRU 출처/버전, AI Hub 승인 절차, 파생 canonical/임베딩 공개·요청 경로), 코드+파생 아티팩트(qrels·임베딩 manifest·집계 결과) 공개, audit 스크립트를 상대경로+환경변수화.

---

## 5. 사용자 3대 질문에 대한 직접 답변

### (a) '멀티모달 데이터셋' 정의·구축이 타당한 수준인가? → **조건부 (Conditional yes)**
정규화 엔지니어링과 무결성 audit은 타당하다(canonical 스키마, missing_media=0). 그러나 '멀티모달'의 세 핵심 요소가 모두 이름보다 얇게 실현됐다: **(i) 영상 = clip당 정지 keyframe 4장**(시간구조·모션 없음, `extract_keyframes.py` L125·`build_visual_embeddings.py` L78–86)인데 text/image-to-video로 광고; **(ii) 구조화/센서 메타데이터 = 저카디널리티 범주 facet**이며 VRU는 VQA 정답 역파싱(F8), 센서/시공간 축 부재; **(iii) 자연어 질의·relevance = facet 템플릿 + relevance≡3 합성 범주매칭**(F4). 따라서 아티팩트는 실재·재현 가능하나, **'이미지+사건보고서+센서/시공간 메타데이터 결합'이라는 정의는 정직한 재프레이밍·용어 축소를 조건으로만 타당**하다. 현재 명명("멀티모달 데이터베이스", "센서/시공간")은 자산 대비 과대.

### (b) 3개 RQ를 충분히 연구했는가? → **부분적 / 아니오 (systems·결합 축은 미흡)**
- **RQ①(storage·indexing·retrieval):** retrieval·query planning(prefilter/postfilter, fusion, reranking)은 연구됨. 그러나 **storage/indexing 구조 비교는 본문 부재**(F6, RQ7 색인 벤치마크가 별개 데이터셋 마이크로벤치로만 존재). retrieval 헤드라인도 순환(F1–F3)으로 오염.
- **RQ②(accuracy·latency·cost):** **정확도만 전달**, latency 명시 포기(L196), cost 미정량화(F7).
- **RQ③(이미지·보고서·센서메타데이터 결합):** **미실현** — 어떤 main 데이터셋에도 센서/시공간 로그 없음(F8).
- **결론:** 원래 표방한 3개 RQ 기준으로는 **불충분**. 원고가 실제 전달한 것은 더 좁은 "멀티모달 evidence 검색·선택 + 답변 계층 통제" 연구이며, 이 좁힌 범위 안에서는 답변 계층·시점 선택 RQ가 충실히 연구됐다. 다만 원고는 이 **범위 축소를 독자에게 명시 전환하지 않았다**(SCOPE-4).

### (c) 결과의 타당성을 보장할 만큼 실험이 수행됐는가? → **부분적 (핵심 통제 실험은 예, 검색 헤드라인은 아니오)**
- **답변 계층(6.8)·다각도(6.13) 통제 실험:** 타당성 보장 수준 **충분**. 사전등록·TOST·permutation·다중 VLM·Go/No-Go gate·하한 조건 모두 갖춤. priming 교란(LEAK-4)을 감안해도 방향 유지, bbox proxy 순환(LEAK-5)은 원고가 의도한 thesis로 투명 공개·완화 — 둘 다 결함으로 성립 안 함.
- **검색 헤드라인(표 6/7/16):** 타당성 **미보장**. 정답 정의 facet이 필터·코퍼스·질의에 흘러든 순환(F1–F3)과 다수-positive 상한(F9)으로 절대 수치·헤드라인 강도가 과대. **정답과 독립된 relevance/질의 셋 + 공정 baseline으로 재실험**해야 타당성 확보.

---

## 6. 경미한 문제 (묶음)

- **통계(minor):** 다중비교 보정 전무(answer-level 20검정, `run_significance_analysis.py`) — 단 헤드라인 better>worse는 Bonferroni 후에도 생존, Idefics2만 marginal [STAT-1]; near-chance 바닥권 등가(SESOI 0.05가 신호폭 54–73%) [STAT-2]; SESOI 0.05 도메인 정당화 문서 부재 [STAT-3]; permutation '88–92%'는 MRR 한정·대조 n=110 미공개 [STAT-4]; p값 표기 인공물(boot 하한 0.0002를 '='로, Wilcoxon '<1e-16' 언더플로) [STAT-5].
- **지표 표현(minor):** 표 9 coverage=1.0은 대표프레임 fallback으로 구조상 보장(품질 신호 아님) [METRIC-3]; nDCG 상수 grade=3(사실상 uniform gain) [METRIC-4]; §7.1 Top-1 0.7468 vs Hit@5 0.9486이 text+image 질의 pool(1,244), text-only는 0.7131/0.8770로 분리 보고 필요 [METRIC-5].
- **주장 수위(minor):** 초록·결론이 '본 데이터·모델(near-floor)' 한정어 생략 [OVERCLAIM-1]; '세 VLM 반복'이 재진술에서 Qwen 계열 LLM backbone 공유 caveat 누락(결론·§7.6·그림7) [HEDGE-1]; 초록의 검색 이득/답변 이득 병치 [ABSTRACT-1]; 표 16이 승률(<0.5인 2/6 비교) 미노출 [OVERCLAIM/STAT-1]; 결론이 본문에 없는 저장·색인을 소프트하게 호명 [SCOPE-1 overclaim].
- **재현성(minor):** lockfile 부재(정확 버전은 프로즈에만) [REPRO-1]; audit이 존재·자기일치 확인이며 해시·재실행 아님 [REPRO-3]; 다각도 manifest 사후 재구성·qwen_vl_utils 'unknown' [REPRO-4]; base 임베딩 manifest에 HF revision pin 부재 [REPRO-5].
- **작성·형식(minor):** 초록 자수 체크리스트 stale(실측 445자/공백포함 544자, 편집간사에 공백포함 여부 확인 필요) [FORMAT-1]; submission_materials_index 참고문헌·표/그림 매핑표가 최종 [1]–[22]와 불일치(내부 추적문서) [CONSIST-2]; §6 과세분(6.1–6.13)·6.12 잡화절·헤드라인 6.13 후치 [STRUCT-1]; 서론 RQ 5개가 다각도 헤드라인 미포괄 [STRUCT-2]; 국문/영문 용어·절 제목 혼용 [EXPR-1]; 그림 경로 빌드 취약·표 5에 P2/P4 정의 누락 [ROBUST-1]; 'video'가 실은 keyframe 4장 [DATA-3].

---

## 7. 게재 가능성을 높이기 위한 실행 로드맵

### P0 — 반드시 고칠 것 (미이행 시 재심 Reject)
1. **순환/누수 해소(F1·F2·F3·F4):** prefilter facet을 qrel 정의와 **독립**시키거나 검색 헤드라인을 **진단으로 격하**; 정답 재진술 문서를 코퍼스에서 제외하고 caption만으로 재측정; B2에 공정 질의 제공; "자연어 질의"→"구조화 조건 템플릿"으로 정정하고 relevance≡3 합성·positive 수백을 §3에 공개. project_md/34의 자기 지침을 **flagship 결과표에도 적용**.
2. **Recall 상한 caveat + 지표 재편(F9):** nDCG@10/MRR 주지표화, capped-Recall/R-precision 병용, many-positives 상한 명시.
3. **선행 시스템 배치(F5):** ForeSea/ForeSeaQA·UrBench 인용·차별화(평가축 차이 명시).
4. **DB-시스템 축 확정(F6):** 색인 벤치마크를 본문/부록 통합(한계 명시) 또는 범위에서 제외(부속문서·제목 정정, 고아 그림 분리) 중 택1하여 부속문서-원고 정합.
5. **데이터/코드 availability 진술(F10)** 추가.

### P1 — 고치면 좋은 것
- 제목·초록 재프레이밍('성능'→'evidence 검색·선택 품질'), 서론 말미에 명시적 범위 선언(정확도 집중, latency/cost·색인은 후속) [F7·SCOPE-4].
- offline cost 대리지표(build-time·index 크기·연산량) 부분 정량화 [F7].
- answer-level 20검정 Holm/BH 보정(헤드라인 생존 명시) + p값 표기 정정 [STAT-1·STAT-5]; 표 16 승률 열 추가·near-floor 한정어·backbone 공유 caveat [OVERCLAIM-1·HEDGE-1].
- 표 9 coverage를 'completeness(구조적)'로 재명명·§7.1 text/image 트랙 분리 [METRIC-3·METRIC-5].
- 메타데이터 카디널리티·자유텍스트성 투명 공개, accident_reason/prevention_method 재분류 [F8].
- lockfile·HF revision pin·sha256 manifest·재실행 검증 [REPRO-1/3/5].
- §6 재구조화(6.12 해체, 6.13 전진 배치), 서론에 다각도 RQ 추가, 용어·절 제목 통일, 'video'→'frame-level' [STRUCT-1/2·EXPR-1·DATA-3].

### P2 — 향후연구로 정직히 이관
- 센서/시공간 정형 로그(CityFlow-NL / sinnaedoro_traffic) 승격을 통한 **진짜 3-모달 결합** [F8].
- pgvector에 실제 HNSW/IVF 색인 적재·recall-latency 비교로 DB-시스템 기여 강화 [VENUE-1].
- video-native/temporal 인코더·segment pooling으로 시간축 기여 실증 [DATA-3].
- 절대 정확도 여유 있는 대형 VLM·강한 LLM-독립 복제로 다각도 결과 재현 [STAT-2].
- open-ended 생성의 citation correctness·hallucination 평가(원고 §8 이미 명시).
- better-view를 bbox 면적이 아닌 occlusion 라벨/사람 시인성으로 정의한 재현(LEAK-5는 결함 아님이나 보강 시 결론 강화).

---

### 검토했으나 문제 아님 (기각·완화 확인)
- **[NOV-5] REFUTED:** ForeSea arXiv id 미래·조작 의심 → 실재 논문·과거일자로 확인. 원고 인용 [1]–[22]에 hallucinated·미래일자 id 없음.
- **재현성 '버전 조작' 가설 REFUTED:** 실제 conda 환경이 부록 A와 정확 일치.
- **[LEAK-5] 대부분 REFUTED(숨은 위협 아님):** 다각도 better-view=bbox 면적은 원고가 **의도적으로 표방한 thesis**이며 대칭 대조·TOST·permutation·사전등록으로 완전 완화.
- **[LEAK-4] 대부분 REFUTED:** RAG-VQA self-facet priming은 결론 방향을 조작하지 않음(vector-only 0.665 ≫ closed 0.308). oracle이 상한임을 원고가 이미 명시.
- **37번/34번/'동기 촬영' 자기모순:** 실제로 정정되어 원고에 반영됨(표 4 행 추가, 기여 5 재작성, grep 0건) — 결함 목록에서 제외하고 강점으로 인정.
