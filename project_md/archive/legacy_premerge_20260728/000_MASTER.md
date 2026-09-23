# 000_MASTER — 연구 종합 (단일 진입점)

최종 갱신: 2026-07-17 | 이 문서 하나로 연구 방향·현재 상태·다음 단계를 파악할 수 있도록 유지한다.
상세 이력은 `README.md`(문서 인덱스)와 개별 문서, 폐기·과거 기록은 `archive/`.

---

## 0. 최신 종합 (2026-07-13~17 확장) — 먼저 읽기

논문을 "저장·색인·검색 설계공간 연구"로 강화하고 데이터셋을 국제 교차검증으로 확장. 상세는 680–760, 전체 감사는 740_AUDIT.

**A. 데이터셋 국제 확장**
- 해외 멀티모달 데이터셋 2차 조사(690·730): 100+ 후보 적대검증 → **제2의 깨끗한 tri-source는 없음(522 단독)**; 외적타당성 arm으로 **MEVA(WACV 2021)** 채택 + **MIRIS(SIGMOD 2020)** 추가.
- **MEVA 통합(700)**: 비순환 tri-source 재구축(A6 6/6 PASS, 985클립·193질의). 검색축 재현 = strict prefilter 이득 **+0.093 [0.075, 0.113] (CI 0 배제)**, 522 +0.098과 근사; 캡션 dense 한계 재현; soft-intent는 null(정직).
- UCA(640): 영어 이상행동 2.5채널, 사전등록 3/4.

**B. DB 설계공간 실험(710 우선순위 → 720·821 결과)**
- **P1 저장단위**: 혼합 encoder 기준선에서는 522 clip-caption/MEVA frame의 도메인 의존성이 나타났고, 동일 Qwen 공간에서는 caption·representative-frame·단일 image+caption joint·multi-frame·dual이 서로 다른 품질–지연–공간 절충을 형성한다.
- **P2 pgvector partial index vs global+WHERE**: 선택적 필터서 global은 recall(공간 predicate 0.49 붕괴)·지연(시간 8.1ms) 딜레마, partial은 recall 0.99·지연 0.4ms 상수. sinnaedoro 132K + **MIRIS 교통(실제 카메라·차량수 predicate로 재확증)**.
- **P3 hot/cold 배포**: N*=1000·build/(지연이득); 선택적(≲0.05) 품질강제 LOCAL, 넓으면 global+postfilter.
- 원고 반영: v3 §7.5 신설 + 표13 확장 + §10 한계(pgvector 부분색인) 해소.

**C. 방법론·포지셔닝 점검**
- **전체 실험 감사(740_AUDIT)**: 데이터셋 10 중 **8 실사용**, cityflow_nl·abnormal_cctv 미사용; 전 실험축 real_measured; 완전 tri-source는 522 단독(최대 caveat).
- **표준 RAG baseline 확립(750_RAG)**: 우리 "문서 임베딩 + 별도 메타데이터 필터" = LangChain/LlamaIndex + 벡터DB 7종의 표준. 통합(joint) 임베딩 = 연구 대안(별도 팀). 비교 계약 고정(85질의·이중정답·랭킹출력).
- **연구 flow(760)** + **발표덱**: `presentations/kiise_vlmdb_deck_20260714.pptx` + `SLIDE_SPEC_for_external_agent_20260714.md`.

**D. 단일 image+caption 통합 벡터(820 프로토콜 → 821 결과)**
- 대표 프레임과 같은 clip의 Qwen3.5 캡션을 Qwen3-VL-Embedding-2B의 한 멀티모달 입력으로 인코딩해 **클립당 단일 2,048차원 벡터**를 생성했다.
- Flat/B2 semantic nDCG@10은 caption 0.181, frame 0.186, joint 0.218, multi-frame 0.352, dual 0.293이다. Joint는 caption보다 +0.037이지만 25개 군집 CI [-0.005,+0.074]로 보편 우위를 확증하지 않는다.
- Matched−shuffled joint 차이 +0.022의 군집 CI [-0.093,+0.144]도 0을 포함하므로, **정확한 image-caption 정렬이 향상의 원인이라는 인과 주장은 금지**한다.
- 기존 91개 호환 구성을 joint 21개 cell로 확장해 **5개 표현·112개 구성·19,040 metric cells·95,200 latency trials**로 재실행했고 독립 검증 17/17을 통과했다.
- 최신 제출원고 v6의 표 12·그림 6·초록·RQ2·기여문에 반영했으며, DOCX/PDF 투고양식 검증은 80개 항목 PASS다.

**⚠ 번호 충돌(사용자 정리 대기)**: 740·750·760 각각 2개 파일 — 내 것(AUDIT/RAG_baseline/RESEARCH_FLOW) + 병렬 작성본(RELATED_reinforcement / UNIFIED_EMBEDDING / RESEARCH_FLOW_systematic). 내용은 상보적이나 번호가 겹침 → README §충돌 참조.

---

## 1. 연구 주제 (LOCKED — 축소·재프레이밍 금지)

> **"Storage/Indexing/Retrieval Structures for Multimodal Urban Surveillance VLM-QA"**
> 자연어 질의 + 메타데이터 조건이 함께 주어질 때, 어떤 저장·색인·검색 구조가
> VLM 기반 질의응답을 더 정확하게(accuracy)·빠르게(latency)·저비용으로(cost) 지원하는가?
> — 이미지/영상 + 사건 보고서 + 센서/시공간 메타데이터의 결합 (도시 감시 데이터)

- 3대 RQ: **RQ-S**(storage·indexing·retrieval 구조 비교) / **RQ-ALC**(정확도·지연·비용 3축 균형) / **RQ-M**(3-모달 결합 위 VLM-QA).
- 투고처: KIISE DBR (KCI). 선정 근거: `100_INTRO_topic_selection_rationale.md`.
- 최우선 원칙(PI 지시): **논문 집필보다 실험 체계 완성이 먼저**, 심사에서 무너지지 않는 설계.

## 2. 한눈에 보는 현재 상태 (2026-07-10)

| 축 | 상태 | 근거 |
|---|---|---|
| 데이터셋 | ✅ **신규 확보 불필요 확정** — 전 모달리티 디스크 실재, 남은 건 가공·통합뿐 | 42 §1 |
| 검색 헤드라인(구 B0–B5) | ⚠️ **순환 결함 확정 → 비순환 재측정 완료** (collapse 실증) | 41 F1–F4, 43 |
| 답변계층(6.8)·다각도 선택(6.13) | ✅ 견고 — 불변 앵커로 유지 | 41 강점, 37/38 |
| 센서·시공간 모달리티 | ✅ **실현 완료** — 522 교차로 32,880클립 + 동기 시각조인 90.2% | 43 |
| 비순환 tri-source 워크로드 | ✅ **최종 실측 완료** (3,000 corpus, A6 감사 PASS) | 43, paper_assets |
| 저장·색인 3축 벤치마크 | ✅ **2-코퍼스+동일-encoder 5표현 완결** — B-1 실 predicate filtered-ANN, B-2 143K 그리드, 522 단일 joint 포함 112구성 | 620, 600, 820–821 |
| latency·cost 축 | ✅ **완결** — 격리 latency·비용 CI(620) + 답변축은 2-스케일 정직 종결(630: mediator 벽·perception 벽) | 620, 630 |
| 원고 | ✅ **v6 심사용 제출원고 갱신(07-17)** — A4 15쪽, 2단, 표 15개·그림 6개, 단일 joint 포함 112구성 반영, 양식 검사 80 PASS·저자 metadata 2건 pending | manuscript/v6 + 821 |

## 3. 연구 여정 (5막 요약)

1. **주제·설계·데이터 확보** (07-06, 문서 01–11) — DBR 동향/공백 분석으로 주제 확정, canonical schema 설계, VRU + AI Hub 3종 확보.
2. **1차 실험: 텍스트·메타데이터 검색** (07-06~07, 12–19) — B0–B5/pgvector 구축·측정. *(이후 이 결과의 순환성이 판명됨 → 막5)*
3. **True-Multimodal 재설계** (07-07, 20–28) — "텍스트 검색만으론 멀티모달이 아니다" 자기비판 → keyframe 시각 임베딩·M-계열·서비스 패킷·답변계층(6.8) 구축, 원고 v1 작성.
4. **다각도·확장** (07-08~09, 29–39) — instance-VQA ill-posed 정정(34), 다각도 사전등록 실험(35→36→38: **선택>축적**, TOST·permutation·4-VLM), 색인 구조 벤치마크(39: Flat/IVF/HNSW/IVF-PQ, 132K real+1M).
5. **비판 심사 → 실험 체계 완성** (07-09~10, 40–44) — 10차원 심사(41: Major Revision, **검색 헤드라인 순환 F1–F4 확정**), 마스터플랜(42: 순환 해소=센서 결합=동일 작업), **실행**(43: 센서 materialization·동기 시각조인·비순환 워크로드·collapse 실증), Pillar B/E 사전등록(44).

## 4. 확정된 핵심 결과 (검증 완료 수치)

**유지되는 견고한 발견 (원고 앵커):**
- 답변계층 통제(6.8): 고정 LLM에서 evidence 품질만 바꿔 closed 0.31 → oracle 0.75 (n=600, 2 LLM, exclude=self).
- 다각도 선택>축적(6.13): better>worse 유의(+0.056~+0.152), both≈better TOST 등가 — 사전등록·permutation·3~4 VLM 재현.

**신규 확정 (2026-07-10, `paper_assets/20260710_noncircular_collapse/`):**
- **Collapse 3중 실증**: 순환 v1 → 비순환 v2에서 VRU B4 nDCG 0.9736→0.3174, AIHub BM25 0.9600→0.1111(라벨 문자열 매칭 폭로), 완벽지표 소멸.
- **새 헤드라인(85질의 확장으로 정제, 500 부록)**: prefilter 가치는 제약의 성격 × **결합도 연속곡선**이 결정 — hard constraint 유의 이득(strict +0.098 [0.068,0.133] @85q); soft intent에선 부호가 결합도를 따름: V<0.05 **−0.099**(n=27) ↔ V≥0.3 **+0.134**, Spearman ρ=0.285 CI[0.071,0.484] 단조. (V=0 쌍 탈락 binning 버그를 F5 검증기가 적발·정정) (구 −0.075 점추정은 초저-V 편중 32질의 표본의 산물 — 기계적 확장이 자기 교정.)
- 522 tri-source 워크로드: 문서=VLM캡션(픽셀만)/predicate=센서CSV(카메라10)/relevance=사람주석(카메라11/22) — **소스 수준 분리**, A6 기계감사 6/6 PASS.
- 부수 발견: strict에서 B0 metadata-only(0.165) > B2 dense(0.064); VLM 캡션의 체계적 맹점(주차 미서술); 교차언어 sparse 실패/다국어 dense 생존.
- 색인 3축(구39→600): HNSW p50 0.04ms vs Flat 13.4ms@131K real; IVF-PQ 33× 압축; **B-2에서 522-visual 142K real로 복제**(HNSW ef64 0.9992 @ 0.047ms vs Flat 14.2ms; IVF-PQ 22–35× 압축) — real 코퍼스 2점.
- **B-1 (620, 2026-07-10)**: 실제 상관 predicate가 공유색인 filtered-ANN을 붕괴시킴 — **동일-s 랜덤 대조군 대비 recall 과대평가 postfilter +0.611(A)/+0.289(B), single-stage +0.50/+0.12~0.22 (전부 Holm-유의)**; prefilter 지역색인만 면역(0.98–1.00 @ 0.04ms); 메커니즘=GT 군집 심도 ρ 0.62–0.895; 확증가족 low/mid(A)·mid/high(B) Holm-유의. → "random-mask 방법론은 filtered-ANN을 과대평가한다" 시스템 헤드라인.
- **E-1 게이트 FAIL (420 Amd.2)**: 26-config 사다리 전부 rel≈1.0 — 1K-문서 RAG에선 색인 선택이 evidence 전달을 못 바꿈(정직 결과, 12–20 GPU-h 절약).
- **단일 image+caption joint(821)**: 동일 one-vector budget에서 semantic nDCG@10 0.218로 caption 0.181·frame 0.186보다 높은 점추정치. Multi 0.352·dual 0.293보다는 낮지만 payload 24.6MB와 p95 1.57ms로 각각 68.4/93.0MB, 4.27/5.66ms보다 작다. Matched–shuffled 음성 대조는 비유의이므로 정렬 인과 주장은 보류한다.

## 5. 알려진 결함(심사 41)과 해소 상태

| ID | 결함 | 상태 |
|---|---|---|
| F1/F2/F4 | 검색 헤드라인 순환(필터⊆정답, 라벨 재진술 문서, 템플릿 질의) | ✅ **해소** — 비순환 워크로드 3종 재측정 + collapse 대조표 (43) |
| F3 | B2 대조군 억압(합성 접속 질의) | ✅ 해소(동일 재측정에 포함) |
| F5 | ForeSea/UrBench 미인용 | ⏳ 원고 재작성 시 반영 |
| F6 | 색인 벤치마크 본문 부재 | 🔄 Pillar B (44) 진행 중 |
| F7 | latency 철회·cost 미정량 | 🔄 Pillar E (44) 진행 중 |
| F8 | 센서/시공간 부재 | ✅ **해소** — 522 materialization + 동기 조인 (43) |
| F9 | Recall 다수-positive 상한 | ✅ 설계 반영(희소 relevance + caveat 규칙, 43/44) |
| F10 | 데이터/코드 공개 진술 부재 | ⏳ 원고 재작성 시 반영 |

## 6. 불변 제약·금지 표현 (44개 문서에서 추출·중복 제거한 유효 규칙)

**A. 환경·재현**
1. 재현 실행은 반드시 `Datasets/envs/kiise-vlmdb` 환경 — base python 금지(parquet 읽기 오류로 재현성 붕괴). [16·26]
2. 물리경로 하드코딩 금지 — `Datasets` symlink 논리경로만 사용. [04]
3. 모델/캐시는 `Datasets/models`·`cache`, 산출물은 `processed/{dataset}/{version}/{canonical,embeddings,indexes,results}` 규칙. [11]
4. 모든 실험은 run_manifest(모델 revision·파라미터) 고정; 다각도 Qwen 계열 manifest는 사후 재구성임을 명시 유지. [10·38]
5. 대용량 원본은 전량 해제 대신 zip://·선택 추출 원칙(573GB 이상행동 등). *예외: 522 frames_src는 42/43 결정으로 전량 추출 완료.* [18·32]

**B. 워크로드·평가 통제 (비순환 원칙, 41/43으로 강화)**
6. 모든 전략 비교는 동일 queries/qrels; **결과를 본 뒤 query/qrels 수동 보정 금지**. [10·19]
7. metadata_filter 키 ⟂ relevance 정의(disjoint) — **A6 기계 감사**(키 disjoint / 정답 재진술 문서 0건 / 희소 relevance / B4−B2 부호분포에 음수) 통과 필수. [43·44]
8. strict(필터∧의미) + semantic(의미만) **이중 qrels** 병행 보고. [43]
9. 한국어-only 질의 추가 시 BM25 tokenizer(현 `[A-Za-z0-9]+`) 교체 + 전 결과 재생성 필수 — 미교체 상태 실험은 No-Go. [19]
10. 고정 설정: top-k {1,5,10,20}·max rank 100·RRF k=60; IM1 인용 시 `query_frame_seq`(본문=qseq2) 명시. [21·26]

**C. 데이터셋 역할·해석 한계**
11. VRU = '교통 안전/대시캠성 영상'(도시 고정 CCTV 아님) — 보수적 표현. [08·24]
12. 지능형 CCTV(269)=국내 보강·이식성 근거; 이상행동 CCTV=생활안전 이식성만(교통 일반화·embedding 우수성 주장 금지). [13·18]
13. CityFlow-NL: visual 추출 전 main 수치 사용 금지; leaderboard 주장 금지; 'CityFlow 사전학습 모델 금지' 벤치마크 규칙에 따라 사용 모델의 사전학습 출처 명시. [29·30]
14. instance-VQA 전역검색 = ill-posed 진단 근거로만(성능 주장 금지). [32–34]
15. 다각도 결론은 bbox 면적 기반 geometric visibility asymmetry + within-model paired delta에 한정; "다각도 무의미"·"상보정보 없음" 금지; Idefics2=near-chance 보조. [35·36·38]
16. 악천후/시간대 트랙(TS_4)은 센서 조인 0% — predicate=아카이브 큐레이션 카테고리임을 명시(센서-조인 트랙과 구분). [43]

**D. 금지 표현(과장)**
17. '최초 대규모 벤치마크'·'실제 관제 시스템 수준'·'상용 완성 시스템'·'감시 데이터 전반 일반화' 금지. [05·24·25]
18. 'LLM이 영상을 이해했다'·'VLM이 사건을 일반적으로 잘 추론'·'CLIP이 답변 생성' 금지. [22]
19. 색인/latency 결과를 end-to-end VLM-QA 비용으로 과장 금지(VLM 추론이 압도); FAISS↔PostgreSQL 절대 latency 비교 금지(격리 후 상대비교만). [19·24·39]
20. M4 이득=metadata 후보축소 효과로 해석(visual 의미 이해 개선 주장 금지); M6 fusion 상시 우월 주장 금지. [21·33]
21. **v1 순환 수치(B0–B5 완벽지표 포함) 인용 금지** — collapse 대조표(paper_assets/20260710_noncircular_collapse/)로만 언급. [41·43]

**E. 지표·통계**
22. 헤드라인 비교는 CI(부트스트랩 5,000)+n 필수; 등가 주장은 TOST+SESOI 사전등록. [35·44]
23. 다수-positive Recall 상한 caveat 필수; nDCG/MRR을 주지표로. [41-F9·44]
24. answer-level은 temperature=0 greedy·동일 프롬프트, 같은 모델 내 paired delta만(모델 간 절대 정확도 비교 금지). [22]
25. 1M synthetic은 real(≤143K)과 라벨 분리; crossover 주장은 real 관측에서만. [39·44]

**F. 범위 밖**
26. VLM fine-tuning·새 모델 제안 금지; closed-source API(GPT/Gemini)는 upper-bound 참고로만. [09]
27. 개인정보 포함 실제 관제 데이터·IRB 필요 인간평가·안심존(어린이보호구역 등) 데이터 사용 금지. [03·06]

**G. DBR 형식** [28]
28. 심사원고 HWP/Word·A4 20쪽 이내; IEEE CS 참고문헌 스타일; 심사본에 감사의 글 금지; 표 제목 상단·그림 제목 하단.

> **해제된 규칙(혼동 방지):** v1 투고 동결기의 "새 실험·새 데이터셋 투입 금지, 교차로신호체계는 후속 언급만"(19·27·31)은 심사 대응 국면 전환(41→42)으로 **공식 해제** — 교차로신호체계(522)는 현재 센서·시공간 헤드라인 트랙이다.

## 7. 지금 진행 중 / 다음 단계

**완료 (2026-07-10)**: 코퍼스B 임베딩 ✅ / P1 LOCK ✅ / E-1 파일럿 게이트 FAIL→착수금지(Amd.2) ✅ / B-1 2-코퍼스 확증 ✅(620) / B-2 143K 그리드 ✅.

**진행 중:** (없음 — Pillar B 완결. B-3: pgvector에서도 상관 predicate 부분복구 한계 재현, iterative_scan으로도 recall 0.30–0.66.)

**다음:**
1. ~~E-2 retrieval 패널~~ ✅ 완료(front 12/46, 두 코퍼스 구조 동일; answer 패널은 E-1 결정 후).
2. ~~E-1 재설계~~ ✅ 종결 — 게이트2 PASS 후 미니파일럿 중단규칙 발동(지렛대 null): 2-스케일 벽 실측으로 (b) 강화판 확정(630).
3. 원고 재작성 ✅(본문+제출 패키지 07-12): v2 + 그림 3종 + DBR 변환(docx/PDF 9쪽, `scripts/make_dbr_review_manuscript_v2.py`) + 저자정보(placeholder 이메일). 잔여: ForeSea 저자 확정, 공저자 직위·이메일 확정, (외부) codex 교차 검증 ✅ 반영 완료(paper_assets/codex_crosscheck_20260712/RESPONSE.md).

## 8. 문서 지도

**활성 문서 (project_md/ 최상위, 논문 섹션 순):**

| # | 문서 | 섹션 · 역할 |
|---|---|---|
| 000 | `000_MASTER.md` | Meta — **국문 단일 진입점** (본 문서) |
| 010 | `010_OVERVIEW_EN.md` | Abstract — **영문 대표 문서** (주제·설계방향·목표·데이터셋 상태) |
| 020 | `020_GLOSSARY_concepts.md` | Meta — 용어 사전 |
| 100 | `100_INTRO_topic_selection_rationale.md` | Introduction — 주제 선정 근거 |
| 200 | `200_RELATED_uca_valu_review_20260710.md` | Related Work — UCA/VALU 검토(비교군·재현성·차별성); 배경 `archive/06·07`·`survey/paper/` |
| 300 | `300_PROBLEM_critical_design_review_20260709.md` | Problem Definition — 비판 심사(구 41), F1–F10 |
| 400 | `400_METHOD_experiment_system_masterplan_20260710.md` | Methodology — 마스터플랜(구 42) |
| 410 | `410_METHOD_prereg_multiview_answer_level_20260708.md` | Methodology — 다각도 사전등록(구 35) |
| 420 | `420_METHOD_prereg_pillarBE_design_20260710.md` | Methodology — Pillar B/E 사전등록(구 44) |
| 430 | `430_METHOD_verification_framework_20260711.md` | Methodology — **검증 체계**(5중 스위트 40/40 + 환경 manifest) |
| 500 | `500_DATASETS_construction_noncircular_execution_20260710.md` | Datasets — 구축·비순환 실행 로그(구 43) |
| 600 | `600_RESULTS_index_structure_benchmark_20260709.md` | Results — 색인 3축(구 39) |
| 610 | `610_RESULTS_multiview_four_vlm_recheck_20260709.md` | Results — 다각도 4-VLM 검증(구 38) |
| 620 | `620_RESULTS_filtered_ann_real_predicates_20260710.md` | Results — **Pillar B 완결**: 실 predicate filtered-ANN(2-코퍼스+pgvector), 색인 그리드, retrieval Pareto |
| 630 | `630_RESULTS_answer_coupling_closure_20260711.md` | Results — E-1 답변-결합 2-스케일 종결(mediator 벽·perception 벽) |
| 820 | `820_JOINT_IMAGE_CAPTION_SINGLE_VECTOR_PROTOCOL_20260717.md` | Method amendment — 단일 image+caption 벡터 결과 전 프로토콜 |
| 821 | `821_RESULTS_joint_image_caption_single_vector_20260717.md` | Results — 동일 예산 대조·112구성·필터·색인·비용 절충 |
| — | `README.md` | 전 문서 인덱스 + 구↔신 번호 매핑 |

**아카이브 (`archive/`, 36편):** 여정 1–4막의 계획·조사·중간 상태·정정 기록. 전부 보존되며 supersede 관계는 `README.md` 인덱스 표 참조. 유효한 규칙은 본 문서 §6에 전량 흡수 완료.

## 9. 핵심 경로

| 무엇 | 어디 |
|---|---|
| 최신 심사용 원고 | `manuscript/kiise_dbr_manuscript_v6_submission_revision.{md,docx,pdf}` |
| 심사보고서 / 마스터플랜 / 실행로그 / B·E 사전등록 | `project_md/41 / 42 / 43 / 44` |
| collapse·유의성 asset | `paper_assets/20260710_noncircular_collapse/` |
| 522 데이터 | `Datasets/processed/aihub_522_intersection/20260710/` (sensor_facets, visual_sensor_join, annotation_*, canonical_trisource, frames_src, captions) |
| 색인 벤치마크 | `Datasets/processed/sinnaedoro_traffic/{index_benchmark,filtered_ann,corpus_real}/` |
| 실행 환경 | `Datasets/envs/kiise-vlmdb/bin/python` (torch 2.12/cu130, tf 5.13, faiss 1.14.3, py7zr) |
| 생성모델 | `/hdd2/huggingface_cache/hub/` (Qwen2.5-VL·Qwen2-VL·InternVL3·Idefics2·Qwen2.5-7B·Llama-3-8B) |
