# 30 — 문제 정의·방법론·사전등록·검증 체계 통합본 (METHODOLOGY & Verification)

## 0. 머리말

**문서 목적:** 2026 KIISE DBR 제출 논문(paper_final.pdf)에 이르기까지의 문제 정의(심사 결함 진단)·실험 방법론(마스터플랜·Pillar 체계)·사전등록(다각도 answer-level, Pillar B/E + Amendment 1–9)·검증 체계(40/40 스위트·구조 감사·연구 흐름·아키텍처 청사진)를 단일 문서로 통합해, 심사 대응·후속 개정·보고서 작성 시 유일 참조점으로 쓰기 위한 정리본이다.

**SYNC 기준: paper_final.pdf(2026-07-23 제출본, `manuscript/paper_final.pdf`, 총 21쪽=접수양식 1쪽+본문) + 2026-07-28 검증 세션.** 본 문서의 모든 수치·용어는 이 SYNC 기준을 절대 우선하며, 소스 문서의 구(舊) 수치와 상충하는 곳에는 `[정정 2026-07-28: …]` 형태로 정정 이력을 남겼다.

**통합 출처 (원본은 아래 아카이브 경로로 이관):**
아카이브 루트 = `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/`

1. `300_PROBLEM_critical_design_review_20260709.md` — v1 원고 자체 심사 보고서(F1–F10 결함 진단)
2. `400_METHOD_experiment_system_masterplan_20260710.md` — 실험 체계 마스터플랜(Pillar A–F, Phase 0–5, Exit criteria)
3. `410_METHOD_prereg_multiview_answer_level_20260708.md` — 다각도 answer-level 사전등록(LOCKED)
4. `420_METHOD_prereg_pillarBE_design_20260710.md` — Pillar B/E 사전등록 + Amendment 1–9(및 KILL 판정)
5. `430_METHOD_verification_framework_20260711.md` — 검증 체계(40/40 스위트, V1–V6)
6. `710_METHOD_db_experiment_priorities_20260713.md` — PI 지시 DB 기여 강화 우선순위(LOCKED)
7. `740_AUDIT_experiment_structure_20260714.md` — 실험 전체 구조 디스크 실측 감사
8. `760_RESEARCH_FLOW_20260714.md` — 연구 흐름 요약본
9. `760_RESEARCH_FLOW_systematic_explanation_20260714.md` — 연구 흐름 상세본(본 통합의 서사 정본)
10. `810_overall_blueprint_20260715.md` — 종합 아키텍처·데이터 흐름 청사진

---

## 1. 최종 논문 정본 스냅샷 (SYNC 기준 — 이 절의 수치가 전 문서를 지배한다)

### 1.1 확정 제목
- 국문: **"종단형 멀티모달 RAG 파이프라인 성능 향상을 위한 비순환 평가 및 검색 품질-비용에 대한 실증 연구"**
- 영문: *An Empirical Study of Non-circular Evaluation and Retrieval Quality-Cost for Enhancing the Performance of End-to-End Multimodal RAG Pipeline*
- ⚠ 러닝 헤드 p.7 이후에 구제목이 잔존 — 재제출/개정 시 수정 필요.

### 1.2 벡터 데이터베이스 계층의 다섯 설계 축 (§4.2)
1. **검색용 데이터**: 영상 설명문 / 대표 이미지 / 이미지·설명문 결합 / 다중 이미지(클립당 최대 3) / 설명문·이미지 이중 색인(RRF k=60)
2. **검색 계획**: 벡터 단독 / 검색 전 조건 / 검색 후 조건(상위 200 후보) / 혼합(영상 설명문 전용)
3. **검색 신호·순위 융합**: 메타데이터 단독 / BM25 / 벡터 / BM25-벡터 RRF
4. **물리 색인**: Flat / HNSW(M=32, efC=200, efSearch{64,256}) / IVF-Flat(nlist=64, nprobe{8,32}) / IVF-PQ(m=32, 6bit)
5. **배포**: 전역 / 조건별 부분 색인

**구성 산식**: 유효 데이터-계획 조합 1×4+4×3=16 × 색인 설정 7 = **112 구성**.

### 1.3 코퍼스 정본
**3,000 clips / 85 queries / strict qrels 6,809 / semantic qrels 24,872.**

### 1.4 RQ별 헤드라인 정본
- **RQ1 (순환성 진단·수리)**: 수정 전후 0.9736→0.3174(VRU), 1.0000→0.8395(지능형 관제); 통제 주입 0.181→1.000(정답 필터)/0.854(라벨 재진술).
- **RQ2 (검색용 데이터/저장 단위, 표4)**: 설명문 0.063/0.181/1.15ms/24.6MB 기준; 다중 이미지 0.101/0.352(Δ+0.171 유의)/3.65ms/68.4MB(2.8배); 이중 색인 0.089/0.293/4.96ms/93.0MB(최고 비용); 저장 비교 전체 BH p=0.112.
- **RQ3 (검색 계획, 표5·6)**: 엄격 기준 검색 전 조건 Δ+0.0983 유의(단 '자명한 결과'로 해석); 의미론 기준 벡터 단독 0.170 최고, Δ=−0.0158 무의미; 고결합(V≥0.3) Δ+0.1335; UCA 129질의 재현 3/4.
- **RQ4 (검색 신호, §5.2.4)**: 전 신호 독립 이득 없음 — 메타 단독 0.218/0.217, BM25 0.017/0.050, 벡터 0.059/0.170, 혼합 RRF 0.133<벡터 0.154; 지식그래프 재조합 Lift 중앙값 0.002 무이득.
- **RQ5 (물리 색인·배포, 표7–10)**: 실측 군집 조건 전역 색인 재현율 손실 최대 0.627(무작위 대조는 최대 0.047 변동→과소평가); 조건별 부분 색인 98.12~100% 회복; 배포 규칙=전역 재현율 목표 0.95 미달 시 부분 색인/전수 검색 + 색인 갱신 시점까지 예상 질의 수의 선택도별 손익분기; Milvus/Weaviate는 필터율≥92.3% 또는 조건 만족 벡터<40,000이면 전수 검색 자동 전환.
- **RQ6 (답변 전파, §5.2.6)**: 답변 정확도 31%(무증거)→53%(무관)→67%(벡터 검색)→75%(대상 설명문); 잘 보이는 단일 시점 +15.2%p, 두 시점 동시 무이득; 근사 색인 재현율 차이의 답변 전파는 표본 부족으로 탐색적(미확립).

### 1.5 2026-07-28 확정 용어 결정 (현 제출 PDF 미적용 — 보고서·향후 개정 원고용)
- '데이터베이스 계층' → **'벡터 데이터베이스 계층'**.
- '증거(evidence)' 전면 치환: DB 반환 = **상위 k 검색 결과**, VLM 입력 = **검색 문맥(retrieved context)**, 정답 판정 = **관련 클립/검색 정답 집합**. RQ6의 3관문 = '관련 클립 회수 → 검색 문맥 인식 → 과제 편향'.
- 클립 조작적 정의: **데이터셋 배포 mp4 1파일 = 1클립**(MEVA[20] 계보로 방어; TTA 사전 미등재·AI Hub 공식 페이지는 '영상(mp4)' 표기임에 유의).
- 본 문서의 "현행 정리" 서술은 이 용어를 따르고, 사전등록·감사 원문 인용부는 당시 용어(evidence 등)를 보존한다.

---

## 2. 구 명칭 ↔ 최종 RQ1–RQ6 매핑 (필수 대응표)

### 2.1 Pillar/구 실험축 → 최종 RQ

| 구 명칭 (300/400/410/420/710/760) | 당시 내용 | 최종 논문 대응 |
|---|---|---|
| 300 F1·F2·F3·F4 (순환/누수 결함) + Pillar **A** (비순환 워크로드) + Pillar **C** (센서/시공간 tri-source; G1으로 A와 병합) | `metadata_filter⊆qrel_filter` 순환 진단, 어댑터 수리 붕괴 대조, tri-source 소스 분리, 통제 주입 | **RQ1** (0.9736→0.3174 / 1.0000→0.8395; 통제 주입 0.181→1.000/0.854) + RQ3·RQ4의 워크로드 기반 |
| 710 **P1 저장 단위** + Pillar **D** (영상/시간축, 다중 프레임) + Pillar **E** 일부(지연·저장 비용 계측) + 760구RQ1 | clip-caption / frame-vector / multi-vector / dual-index 비교 | **RQ2** (표4: 설명문/대표 이미지/결합/다중 이미지/이중 색인 = 설계 축 ①) |
| Pillar **A** A8 (B0–B5 재측정) + 420 **Amd.6/6a** (UCA 외적 타당성) + 760구RQ2 | 검색 계획(B2 벡터 단독/B4 검색 전/B3 검색 후/B5 혼합) × 결합도 스펙트럼, 이중 정답 | **RQ3** (표5·6: Δ+0.0983 '자명한 결과', 의미론 Δ=−0.0158, 고결합 +0.1335, UCA 129질의 3/4) |
| Pillar **A** (B0/B1/B2/B5 신호 비교) + 420 **Amd.9** (P9 KG-as-index, KILL 후 CPU 실측 영수증화) | 메타/BM25/벡터/RRF 신호와 KG 재조합 | **RQ4** (§5.2.4: 전 신호 독립 이득 없음, KG Lift 중앙값 0.002) |
| Pillar **B** (filtered-ANN·색인 3축·pgvector) + 710 **P2 partial index·P3 hot/cold** + 420 **Amd.5/5a** (Milvus·Weaviate 엔진 재현) | 실측 predicate vs 무작위 마스크, 전역 vs 부분 색인, 손익분기 N*, 엔진 완화 기전 | **RQ5** (표7–10: 손실 최대 0.627, 부분 색인 98.12~100% 회복, 92.3%/40,000 자동 전환, 손익분기 배포 규칙) |
| v1 §6.8 답변 사다리(KEEP) + **410** 다각도 answer-level 사전등록 + 420 **Amd.1–4** (E-1/E-1a '두 벽') + Pillar **E** E3 | 검색 문맥 구성만 바꾼 통제 실험, 시점 선택>축적, 색인 근사→답변 결합 | **RQ6** (§5.2.6: 31→53→67→75%, 단일 잘 보이는 시점 +15.2%p·두 시점 무이득, 색인→답변 전파는 탐색적) |
| Pillar **F** (통합·거버넌스) + **430** 검증 스위트 | RQ 커버리지 매트릭스, per-query 재집계 검증기, 40/40 체크 | 전 RQ 공통 검증 기반(논문 재현성·감사 서술) |

### 2.2 구 3-RQ(400)·구 RQ 3종(760) → 최종 RQ

| 구 프레임 | 최종 RQ 대응 |
|---|---|
| 400 **RQ-S** (저장·색인·검색 구조) | RQ3 + RQ4 + RQ5 |
| 400 **RQ-ALC** (정확도·지연·비용) | RQ2(비용 열) + RQ5(지연·저장) + RQ6(답변축, 탐색적 종결) |
| 400 **RQ-M** (3-모달 결합) | RQ1(비순환 tri-source) + RQ3(prefilter 가치) + RQ6(답변 계층) |
| 760 구RQ1 (저장 단위) | RQ2 |
| 760 구RQ2 (검색 구조) | RQ3 + RQ4 |
| 760 구RQ3 (색인·DB 구현) | RQ5 |

[정정 2026-07-28: 300/400의 "RQ7 색인 벤치마크", "지향 3-RQ" 등 구 명칭은 제출 논문에서 위 표의 RQ1–RQ6 6문항 체계로 최종 재편되었다. 구 문서를 인용할 때는 반드시 이 표로 환산할 것.]

---

## 3. 문제 정의 — v1 원고 자체 심사와 결함 목록 (300 기반, 이력 전량 보존)

### 3.1 심사 판정과 총평
- 대상: `kiise_dbr_manuscript_v1_true_multimodal.md`(v1, 2026-07-07). 판정: **Major Revision(재심 필수·조건부)**.
- 실제로 잘 입증된 것: (1) 생성 모델 고정·검색 문맥 구성만 변경한 답변 계층 실험(closed 0.31→oracle 0.75 — 최종 논문 RQ6의 31→75%로 승계), (2) 다각도에서 "두 시점 축적 ≈ 더 나은 한 시점 선택"의 사전등록·TOST·permutation 방어(최종 RQ6의 +15.2%p/무이득으로 승계).
- 반면 검색 헤드라인(v1 표6/7/16)은 정답 정의 facet이 필터·코퍼스·질의에 흘러든 **순환/누수의 구조적 산물**이며 v1은 이를 공개하지 않았다. → 이 진단이 최종 논문의 **RQ1(비순환 평가)** 자체가 되었다.
- 재심 조건: F1–F3 순환을 (i) 정답과 독립된 relevance/질의 셋으로 재확립하거나 (ii) 검색 헤드라인을 진단으로 격하하고 답변 계층·시점 선택 기여로 재포지셔닝. → 최종 논문은 (i)+(ii)를 모두 수행(비순환 tri-source 재구축 + 순환 수치의 RQ1 진단 격하).

### 3.2 치명적/주요 결함 F1–F10 (전량 보존; 상태 표기)
- **F1 [LEAK-1/METRIC-2/DATA-1] CONFIRMED·critical·load-bearing** — prefilter의 `metadata_filters`가 항상 qrel 정의 facet의 진부분집합이라 **B4≥B2가 코드로 보장**(순환). v1 표6 B4 nDCG 0.9736 vs B2 0.4476이 부분적으로 tautological. 수정 요구: prefilter facet을 qrel과 독립시키거나 진단 격하. [정정 2026-07-28: 최종 논문 RQ1이 이 수치를 진단으로 승계 — 수리 후 0.9736→0.3174 붕괴.]
- **F2 [LEAK-2] CONFIRMED·critical·load-bearing** — 코퍼스에 정답 라벨 재진술 문서(vqa_facet_statement/event·temporal_statement) 포함 → AI Hub MRR=nDCG=1.0000은 라벨 자기재진술 순환. 수정 요구: 재진술 문서 제외 후 재측정. [정정 2026-07-28: 최종 논문 RQ1 — 지능형 관제 1.0000→0.8395; 통제 주입 실험(0.181→1.000 정답 필터/0.854 라벨 재진술)이 이 기전의 정량 재현.]
- **F3 [LEAK-3] CONFIRMED·major·load-bearing** — B2에 4-facet 기계 접속 질의를 투입해 대조군 억압(weak 0.9117→strong 0.1851), B4−B2 델타 양방향 팽창. 수정 요구: 공정 질의 제공 또는 '동일 질의·필터 유무' 격리.
- **F4 [DATA-1 표현] PLAUSIBLE·major·load-bearing** — '자연어 질의'가 실제로는 facet 템플릿 + relevance≡3 합성 범주매칭(positive 최대 419). 수정 요구: "구조화 조건 템플릿 질의"로 정정, 합성 방식 공개.
- **F5 [NOV-1] CONFIRMED·major·load-bearing** — 최근접 선행 ForeSea/ForeSeaQA·UrBench 미인용. (하위주장 'ForeSea id 조작 의심'은 REFUTED — 실재 논문.) 수정 요구: 인용·차별화.
- **F6 [SCOPE-2/CONSIST-1/VENUE-1] CONFIRMED·major** — DB-시스템 기여축(저장·색인 비교)이 본문 부재 + 고아 그림. 택1: 본문 통합 또는 범위 제외. [정정 2026-07-28: 최종 논문은 통합 경로 — 설계 축 ④⑤(물리 색인·배포)=RQ5, 저장 단위=RQ2로 본문 정식 편입.]
- **F7 [SCOPE-1] CONFIRMED·major** — 3축(정확·지연·비용) 중 정확도만 전달, latency 철회·cost 미정량. [정정 2026-07-28: 최종 논문 표4·표7–10이 지연(ms)·저장(MB)·손익분기를 정량 보고 — 해소.]
- **F8 [DATA-4/SCOPE-3/DATA-2] CONFIRMED·major** — '영상+사건보고서+센서·시공간 메타데이터' 3요소 결합이 main 데이터셋 어디에도 미실현(VRU facet은 VQA 정답 역파싱). [정정 2026-07-28: 522 교차로 tri-source(센서 CSV predicate ⟂ 사람 주석 relevance ⟂ 픽셀-only 캡션 문서)로 실현 — 최종 논문 워크로드의 근간.]
- **F9 [METRIC-1] CONFIRMED·major** — 다수-positive qrels로 Recall@k 구조적 상한(positives>k), caveat 없이 절대값 제시. 수정 요구: nDCG/MRR 주지표화 + 상한 caveat.
- **F10 [REPRO-2] CONFIRMED·major** — 데이터·임베딩 전량 로컬 경로, availability 진술 부재. 수정 요구: availability statement + 파생물 공개.

### 3.3 경미 문제 묶음 (이력 보존)
- 통계: 다중비교 보정 전무(단 헤드라인은 Bonferroni 생존)[STAT-1]; near-chance 바닥권 등가[STAT-2]; SESOI 0.05 정당화 부재[STAT-3]; permutation 88–92%는 MRR 한정[STAT-4]; p값 표기 인공물[STAT-5].
- 지표: coverage=1.0 구조 보장[METRIC-3]; nDCG 상수 grade=3[METRIC-4]; text/image 질의 pool 분리 필요[METRIC-5].
- 주장 수위: near-floor 한정어 생략[OVERCLAIM-1]; Qwen backbone 공유 caveat 누락[HEDGE-1]; 검색/답변 이득 병치[ABSTRACT-1]; 승률 미노출; 본문에 없는 저장·색인 소프트 호명.
- 재현성: lockfile 부재[REPRO-1]; audit이 해시 재실행 아님[REPRO-3]; manifest 사후 재구성[REPRO-4]; HF revision pin 부재[REPRO-5].
- 작성·형식: 초록 자수 stale[FORMAT-1]; 내부 추적문서 불일치[CONSIST-2]; §6 과세분[STRUCT-1]; RQ 미포괄[STRUCT-2]; 국/영 혼용[EXPR-1]; 'video'가 실은 keyframe 4장[DATA-3].

### 3.4 기각·완화 확인(검토했으나 문제 아님)
- [NOV-5] ForeSea id 조작 의심 → REFUTED(실재·과거일자).
- 재현성 '버전 조작' 가설 → REFUTED(conda 환경 부록 A와 정확 일치).
- [LEAK-5] better-view=bbox 면적 → 의도된 thesis, 사전등록·TOST·permutation으로 완화(결함 아님).
- [LEAK-4] RAG-VQA self-facet priming → 결론 방향 불변(vector-only 0.665 ≫ closed 0.308).
- '동기 촬영' 표현·LLM 미사용 자기모순 → 이미 정정 반영.

### 3.5 사용자 3대 질문 직답 (당시 결론)
- (a) 멀티모달 데이터셋 정의·구축 타당성 → **조건부 yes**(정직한 재프레이밍·용어 축소 조건).
- (b) 3개 RQ 충분 연구 → **부분적/아니오**(systems·결합 축 미흡). [정정 2026-07-28: 이 미흡분이 이후 Pillar B/C/E + 710 P1–P3로 전부 채워져 최종 RQ2·RQ5가 됨.]
- (c) 결과 타당성 보장 실험 → **부분적**(답변 계층·다각도는 충분, 검색 헤드라인은 재실험 필요 → 수행됨).

---

## 4. 실험 체계 마스터플랜 (400 기반 — 규칙·게이트 전량 보존)

### 4.1 한 줄 결론과 '완성'의 정의
부족한 것은 데이터가 아니라 **(1) 비순환 워크로드, (2) 실현된 센서/시공간 모달리티, (3) 3축(정확·지연·비용) 계측**을 하나의 감사 가능한 실험 체계로 봉합하는 작업. '완성' = 교차로신호체계(522) 실센서 CSV를 QA 정답과 독립인 predicate로 materialize해 F1/F2/F4를 데이터 수준에서 붕괴시키고 → 그 위에서 검색 구조·filtered-ANN·색인 3축·답변 계층을 재측정하고 → 답변 계층·다각도를 diff-proven 불변 앵커로 접합하고 → 전 RQ 셀이 non-circular·CI 실험 ≥1개로 채워졌음을 자동 검증기(per-query 재집계)가 PASS. **주제 실현(센서 결합)과 결함 해소(순환 제거)가 동일 작업**이라는 것이 중심 지렛대.

### 4.2 데이터셋 확정 판정 (2026-07-10 디스크 실측)
- 추가 신규 확보 필요? → **NO.** 필요한 것은 materialization + 비순환 통합. TL_1(통과차량, plain Zip 14.96MB·29,234 CSV·63교차로)/TL_2(보행량, 9.65MB) 즉시 파싱 가능; TS_3(영상 원천)=75.18GB 솔리드 7z(고비용); TS_1/TS_2=22바이트 placeholder(라벨 CSV로 대체 가능, 불필요); sinnaedoro corpus_real=132,521×512 CLIP + frame_index 실재; MAIN QA bge-m3 임베딩·VLM 가중치 전량 실재.
- 역할 확정: 522=SENSOR/tri-source 헤드라인, VRU=답변계층 anchor+순환 재측정 대조, 다각도=선택>축적 anchor(KEEP), 지능형=누수독립 재측정, sinnaedoro=색인 3축+실측 predicate filtered-ANN, 이상행동=이식성만, CityFlow-NL=후순위. [정정 2026-07-28: 최종 사용 구성은 740 감사(§10) 기준 — 외적 타당성이 MEVA·MIRIS·UCA로 확정되고 이상행동·CityFlow-NL은 미사용.]
- 거버넌스 결정 **G1**: Pillar A와 C는 동일 522 원천 이중 빌드이므로 단일 canonical(`aihub_522_intersection`)로 병합. **G2**: B5(522 센서 predicate를 sinnaedoro에 조인)=No-Go 확정(namespace 완전 disjoint).

### 4.3 Pillar별 핵심 통제 규칙 (전량 보존)
- **Pillar A (비순환 워크로드; F1/F2/F4 해소)**: P계열(predicate, exogenous) ⟂ R계열(relevance) 컬럼셋 disjoint 스키마 강제; 캡션은 dense caption 단일 doc_type만(**정답 라벨 재진술 doc 절대 금지, verbatim 수치 금지**); 판정기(InternVL3)는 캡셔너(Qwen2.5-VL)와 다른 패밀리·프레임만 열람; 캡션무관 CLIP/SigLIP 대조 arm 필수; **A6 감사 어서션 5종**(①keys(metadata_filter)∩keys(qrel_filter)=∅ ②vqa_facet_statement 0건 ③facet_source='sensor_csv' ④predicate↔relevance Cramér's V/MI ≠1.0 문서화 ⑤B4−B2 Δrecall 부호분포에 음수 포함) — **실패 시 빌드 중단**; collapse 표는 human-gold nDCG 보존 동반 제시.
- **Pillar B (저장·색인; F6 해소)**: search-only 격리; 소형 N에서 ANN≈exact 명시; crossover는 synthetic_aug로만 주장 금지(honest framing); recall=index fidelity(정답 라벨 분리).
- **Pillar C (센서/시공간)**: predicate⟂relevance를 가정 아닌 데이터로 검증; 결합 강도를 연속 축으로 'B4 이득 vs 결합강도' 곡선 보고(저결합만 cherry-pick 금지); 정답=CSV 집계(doc verbatim 부재); exclude=self 계승; leakage_scan은 문자열+단위변형+부분합 커버.
- **Pillar D (영상/시간축; OPTIONAL·비차단)**: 검색 pool=전체 clip 균일 dense(evidence-frame 주입 금지→F2 재발 방지); event window=GT로만(retriever 미제공→F1 재발 방지); near-dup 중복제거·holdout.
- **Pillar E (지연·비용 3축; F7 해소)**: faiss threads=1·batch=1·clock pin; latency 헤드라인은 'filter-plan별 격리 지연'으로 재정의; **3축→2축 붕괴 방지** — answer가 recall에 반응하는 층을 먼저 입증한 뒤에만 3축 headline; 절대 $ 비-headline·민감도 band만.
- **Pillar F (통합·거버넌스)**: GPU 0; exit MUST/NICE 등급화; **존재≠검증(per-query parquet 재집계 강제)**; '동일 원천 이중 빌드' 탐지 규칙.

### 4.4 Exit Criteria 체크리스트 (E1–E12, 전량 보존)
- **[MUST] E1** 비순환 재측정: 522·수리 VRU에서 B0–B5 재측정 manifest + 델타 정직 보고 + A6/C8 어서션 5/5 PASS.
- **[MUST] E2** 센서 결합 headline: QA-독립 센서 predicate 기반(순환 수치 아님).
- **[MUST] E3** verbatim-leak 0: 색인 문서에 QA 정답 수치가 문자열/단위변형/부분합으로 미등장(하드게이트).
- **[MUST] E4** predicate⟂relevance 정량화: V/MI 행렬 + 'B4 이득 vs 결합강도' 연속곡선 + bin당 최소 질의수(cherry-pick 아님).
- **[MUST] E5** 색인 3축 접합: recall×latency×index_mb(real 우선+synthetic 라벨)가 본문 표/그림 참조.
- **[MUST] E6** RQ-ALC 최소 커버: answer accuracy + ≥1 cost proxy + latency 범위선언; answer가 recall에 반응하는 층 ≥1 입증.
- **[MUST] E7** 답변계층·다각도 diff-proven 불변(closed 0.308→oracle 0.747, n=600, 2 LLM; selection>accumulation).
- **[NICE] E8** temporal 승격 or 명시 한계(비차단).
- **[MUST] E9** 3-RQ 커버리지: 각 RQ에 non-circular·CI 실험 ≥1('없음' 0셀).
- **[MUST] E10** 검증기 신뢰: manifest 존재만이 아니라 per-query 재집계로 헤드라인 재계산 대조 PASS; B5 No-Go 문서화 포함.
- **[NICE] E11** tri-modal 독립성: 보고서 채널이 재인코딩 아님을 진짜 join or MI-독립으로 증명. 미증명 시 headline lock 금지.
- **[MUST] E12** 인용·재현성: ForeSea/ForeSeaQA·UrBench 인용 + data/code availability statement.

### 4.5 트립와이어·No-Go 분기 (T1–T11, 전량 보존)
| # | 트립와이어 | 판정 기준 | No-Go 분기 (주제 축소 없이) |
|---|---|---|---|
| T1 | TS_3 솔리드 7z 롱폴 | 블록정렬 PoC wall-clock 예산 초과 | 시각 subset 최소 층화; frame-free 센서·텍스트 헤드라인으로 방어 |
| T2 | 신호위상 predicate 희소('t' 편중) | TL_1 전수에서 selectivity 범위 불가 | 차종·차로·밀도·시각·보행 predicate로 교체(주제 불변) |
| T3 | predicate⟂relevance 붕괴(고결합) | 운영유의 질의가 predicate와 공선 | 'B4 이득 vs 결합강도' 연속곡선 자체를 결과로(배제 아님) |
| T4 | 522↔sinnaedoro 조인(B5) | 이미 No-Go 확정(namespace disjoint) | 센서 predicate=C 자체 코퍼스; MAIN 일반화=sinnaedoro 자체 시공간 predicate |
| T5 | VLM-A↔VLM-B 공유편향 | retrieval 성공 vs VLM 합의 상관 과다 | CLIP/SigLIP 캡션무관 대조 arm으로 격리 |
| T6 | human-gold κ 미달 | κ<게이트 or 검정력 부족 | 검정력 사전산정 gold-only 축소셋 |
| T7 | env 분절(faiss+VLM) | tf 5.13에서 VLM 로더 파손 | nrf2에 faiss-cpu 설치; 커밋 전 스모크 필수 |
| T8 | B4/E3 null(캡션 recall-강건) | recall↓해도 accuracy 평탄 | null 사전등록; '소규모 코퍼스=ANN 불요'를 정직 결과로 |
| T9 | synthetic 1M 국소기하 왜곡 | 증강 kNN/LID가 real과 이탈 | crossover는 민감도 band로만; real 관측 regime만 강주장 |
| T10 | GPU 경합(2×RTX3090) | pillar 중첩 일정 붕괴 | 횡단 공유 스케줄; Phase 1(CPU/저GPU) 우선 |
| T11 | tri-modal=2-modal+파생 | 보고서가 센서/이미지 재인코딩 | 독립 조인 or MI-독립 증명 전 headline lock 금지 |

**메타 원칙**: 어떤 No-Go도 주제를 축소하지 않는다. frame-free 센서 결합 + 색인 3축 + 답변계층·다각도 앵커가 축소불가한 정직 백본.

### 4.6 Phase 로드맵 요약과 자산 분류
- Phase 0(CPU-only 트립와이어 게이트: T1 PoC/T2 전수 카디널리티/T3 No-Go 확정/T4 검정력/T5 env 스모크/T6 canonical 병합) → Phase 1(frame-free 척추: 522 센서 canonical+QA+B0–B5, 색인 3축 승격, F 매트릭스) → Phase 2(시각 비순환: 캡션·독립 판정·대조 arm) → Phase 3(answer-coupling+3축 Pareto+pgvector) → Phase 4(확장: temporal·tri-modal·CityFlow) → Phase 5(완성 감사·freeze).
- 자산 분류: 답변계층(표13)·다각도(표20)=KEEP; 순환 검색 헤드라인(표6/7/16)=REMEASURE+진단 격하; index_benchmark=PROMOTE; filtered_ann(random-mask)=개념 유지+실측 predicate 재측정; pgvector=확장 재측정; VRU/AIHub facet_docs 분기=DROP; CityFlow-NL=DEFER; 이상행동=일반화만.
- 부록 실측(2026-07-10): 답변 사다리 `summary_qwen.json` closed 0.3083→distractor 0.5383→vector 0.665→prefilter 0.680→oracle 0.7467(n=600, topk=3). [정정 2026-07-28: 최종 논문 RQ6 표기 = 31%→53%→67%→75%(무증거→무관→벡터 검색→대상 설명문) — 동일 실험의 반올림 표기.] env: kiise-vlmdb = faiss 1.14.3 + torch 2.12.1/cu130 + transformers 5.13.0 + py7zr 1.1.3.

---

## 5. 연구 흐름 서사 (760 상세본 정본 흡수 — 배경→문제→설정→방법→결과)

### 5.1 큰 그림 (한 줄 flow)
**[기존연구 조사 → 순환성 발견] → [붕괴로 정량 확인] → [비순환 tri-source 프로토콜 제안] → [522 중심 데이터셋 + 표준 RAG 워크로드 구축] → [저장·색인·필터·배포·엔진을 변수화한 설계공간 파이프라인] → [구조 선택 지침 + 외적 타당성(MEVA·MIRIS·UCA)]**

단계 간 인과: ① 순환성을 발견·정량화했기에 → ② 비순환 워크로드부터 구축해야 하고 → ③ 그 타당한 워크로드 위에서만 구조 선택지 비교가 의미를 가지며 → ④ 그 비교에서 결합도·데이터셋-의존적 설계 지침이 나온다. "타당성 없는 벤치마크는 구조 비교를 오염시킨다"가 전 단계를 관통.

### 5.2 연구 배경 — 기존 연구 세 흐름과 공백
1. **비디오 데이터베이스**(NoScope, BlazeIt, MIRIS, OTIF, EQUI-VOCAL): 객체·트랙·시공간 질의 효율화에 강점이나, VLM-QA용 검색 문맥을 자연어+메타데이터 조건으로 찾는 문제는 직접 다루지 않음.
2. **Filtered vector search**(Filtered-DiskANN, VBASE, ACORN, pgvector iterative scan): 일반 vector+attribute filter 문제에 가깝고, 실제 감시 영상에서 센서·시간·위치 조건이 검색 결과·검색 문맥에 주는 영향은 미비.
3. **감시 영상 VLM 벤치마크**(UCA/VALU, HAWK, UrBench, ForeSea): 모델 이해 능력 평가에 초점, DB의 저장·색인·검색 구조를 통제 변수로 비교하지 않음.
→ 공백: "모델 자체만 볼 것이 아니라 DB가 어떤 검색 문맥을 어떻게 저장·색인·검색해 모델에 전달하는지를 평가해야 한다."

### 5.3 문제 정의 — 순환성
관제 질의는 의미 조건("정차/주차 차량이 보이는가")과 구조화 조건("오전 시간대인가")이 결합된 형태. 벡터 검색만으로는 hard constraint를 보장 못 하고, 필터 선적용은 soft intent에서 관련 결과를 제거할 수 있다. 여기에 평가 함정: 필터 조건·정답 정의·검색 문서가 같은 주석 라벨에서 파생되면 **(C1) 필터⊆정답 → prefilter 우위가 구성상 보장, (C2) 라벨 재진술 문서 → 어휘 매칭만으로 완벽 지표**. 이를 순환성(circularity)으로 형식화(논문 §3에 C1–C3)하고, 소스 분리 기반 비순환 워크로드를 설계했다.

**정량 확인(붕괴):** VRU B4 nDCG 0.9736→0.3174, 지능형 관제 1.0000→0.8395(수리 전후). 수리 후 semantic에서 질의별 (B4−B2) 부호에 음수 등장 = "prefilter 우위 보장"이 실제로 깨진 직접 증거. 통제 주입 실험이 기전을 재현: 0.181 → 1.000(정답 필터 주입) / 0.854(라벨 재진술 주입). [정정 2026-07-28: 760 구본의 "지능형 CCTV: BM25 0.96→0.11" 서술은 BM25 어휘 매칭 폭로 관찰이며, 제출 논문 RQ1의 정본 수치는 1.0000→0.8395(지능형 관제)다.]

### 5.4 실험 설정 — 데이터셋 역할
| 역할 | 데이터셋 | 용도 |
|---|---|---|
| 메인 헤드라인 | AI-Hub 522 교차로 CCTV(63교차로) | 비순환 tri-source(A6 6/6 PASS), 코퍼스 정본 3,000 clips/85 queries/strict 6,809/semantic 24,872 |
| 색인 코퍼스 | sinnaedoro 132K + 522-visual 143K(CLIP 512d) | filtered-ANN·색인 3축·pgvector |
| 외적 타당성 | MEVA(검색)·MIRIS(색인/배포)·UCA(검색, 129질의) | 국제·타도메인 재현 |
| 붕괴 데모 | VRU·지능형 CCTV | 순환→수리 붕괴(RQ1) |
| 답변 계층 | 다각도 CCTV·VRU | 다시점 답변 선택·검색 문맥 사다리(RQ6) |

**워크로드 flow(비순환 tri-source):** raw(프레임+CVAT 주석+센서 CSV) → facet 분리(PREDICATE=센서 기록 ⟂ RELEVANCE=사람 주석 ⟂ DOCUMENT=픽셀만 본 VLM 캡션) → canonical(clips/documents/metadata/queries + strict·semantic 이중 qrels) → A6 기계감사 → 임베딩(문서/질의=bge-m3 1024d, 프레임=CLIP ViT-B/32 512d) → 검색/색인(표준 RAG: embed+ANN+분리 메타필터+고정 VLM). 핵심 축 = 이중 정답(strict=필터∧의미 / semantic=의미만) + 결합도 스펙트럼(Cramér's V).

### 5.5 방법론 — 설계 선택지의 변수화
동일 질의·동일 정답·동일 지표 아래 축마다 선택지를 변수화해 통제 비교(격리 latency, recall=exact GT 대비):

| 설계 축(구 명칭) | 변수화 선택지 | 최종 논문 대응 |
|---|---|---|
| 검색 전략 B0–B5 | metadata/BM25/vector/postfilter/prefilter/hybrid | 설계 축 ②③ → RQ3·RQ4 |
| 저장 단위 P1 | clip-caption/frame-vector/multi-vector/dual-index | 설계 축 ① → RQ2(설명문/대표 이미지/결합/다중 이미지/이중 색인) |
| 색인 구조 | Flat/IVF-Flat/HNSW/IVF-PQ | 설계 축 ④ → RQ5 |
| 필터 결합 | prefilter/postfilter/single-stage vs 동일선택도 무작위 대조 | RQ5 |
| 관계형/엔진 구현 | pgvector/Milvus/Weaviate; global+WHERE vs partial/local index | 설계 축 ⑤ → RQ5 |
| 배포 정책 | hot/cold 손익분기 N* | 설계 축 ⑤ → RQ5 배포 규칙 |
| 답변 전파 | 검색 문맥 사다리·다시점·색인→답변 게이트 | RQ6 |

고정 모델: 캡션=Qwen2.5-VL, 텍스트 임베딩=bge-m3(+e5-large-v2), 시각=CLIP/SigLIP, 답변=Qwen·Llama·InternVL·Idefics 고정(학습 없음). 측정: nDCG@10·recall@10·MRR(strict+semantic) + p50/p95 격리 지연 + 색인 크기·구축시간.

### 5.6 평가 방식 — 이중 정답
- **strict qrels**: 의미∧메타데이터 모두 만족만 정답(예: 오전 조건 질의면 실제 오전 촬영 관련 장면만).
- **semantic qrels**: 의미 조건만 만족하면 관련(오후 촬영 주차 장면도 의미상 관련).
- 이 구분으로 (i) hard constraint에서 prefilter 유리 여부, (ii) soft intent에서 prefilter의 관련 결과 제거 여부, (iii) 메타데이터-정답 결합도를 분리 측정. 핵심 실측: **semantic positive의 72.6%가 필터를 통과하지 못함** → prefilter의 비보장성.

### 5.7 실험 결과 핵심 흐름 (SYNC 정본으로 정정 반영)
1. **순환 워크로드는 위험하다** — 붕괴 재현으로 실증(RQ1: 0.9736→0.3174 / 1.0000→0.8395; 통제 주입 0.181→1.000/0.854). 통찰: 멀티모달 검색 평가에서는 데이터셋 구축 방식 자체를 감사해야 한다.
2. **hard constraint에서 검색 전 조건(prefilter)이 유리하나 '자명한 결과'** — 엄격 기준 Δ+0.0983 유의(MEVA 재현 +0.093 [0.075,0.113]). [정정 2026-07-28: 제출 논문은 이 유의 이득을 '자명한 결과(정의상 보장에 가까움)'로 해석 격하해 서술한다 — 구 문서의 "확증 헤드라인" 톤을 그대로 쓰지 말 것.]
3. **soft intent에서 prefilter 주의** — 의미론 기준 벡터 단독 0.170 최고, 전체 Δ=−0.0158 무의미; 고결합(V≥0.3) Δ+0.1335. [정정 2026-07-28: 구 문서의 밴드 수치 "저결합 −0.099(binning 버그 정정 후)·자연결합 +0.134, 쌍 군집 CI 0 포함=탐색적"은 이력으로 유지하되, 정본 표기는 위 논문 수치. UCA 외적 타당성은 129질의 재현 3/4(구 감사 문서의 "135질의"는 129로 정정).]
4. **검색 신호는 독립 이득 없음(RQ4)** — 메타 단독 0.218/0.217, BM25 0.017/0.050, 벡터 0.059/0.170, 혼합 RRF 0.133<벡터 0.154; KG 재조합 Lift 중앙값 0.002 무이득.
5. **저장 단위(RQ2)** — 설명문 기준(0.063/0.181, 1.15ms, 24.6MB) 대비 다중 이미지 0.101/0.352(의미론 Δ+0.171 유의)·3.65ms·68.4MB(2.8배), 이중 색인 0.089/0.293·4.96ms·93.0MB(최고 비용), 저장 비교 전체 BH p=0.112. [정정 2026-07-28: 740/760 구본의 "522=clip-caption Pareto, multi·dual 무익"은 제출 전 보강실험으로 갱신됨 — 정본은 표4: 다중 이미지가 의미론 기준 유의 개선이되 2.8배 비용, 이중 색인은 최고 비용. 품질-비용 트레이드오프 서술로 읽을 것. "MEVA=frame-vector 지배"는 외적 타당성 이력으로 유지.]
6. **filtered-ANN 재현율 편향(RQ5)** — 실측 군집 조건에서 전역 색인 재현율 손실 최대 0.627, 동일선택도 무작위 대조는 최대 0.047 변동(무작위 마스크 평가는 과소평가); 조건별 부분 색인이 98.12~100% 회복; pgvector 재현; 전용 엔진(Milvus·Weaviate)은 다층 완화로 대부분 흡수 — **필터율≥92.3% 또는 조건 만족 벡터<40,000이면 전수 검색 자동 전환**.
7. **배포 규칙(RQ5)** — 전역 재현율 목표 0.95 미달 시 부분 색인/전수 검색; 색인 갱신 시점까지 예상 질의 수의 선택도별 손익분기(hot/cold N*). MIRIS 교통 데이터 교차 재현.
8. **색인 3축** — 143K 실측에서 HNSW 지배(≈300× 지연 이득), PQ는 저장 극한(22–35× 압축/recall↓).
9. **색인→답변 전파(RQ6)** — 검색 문맥 사다리 31%→53%→67%→75%; 잘 보이는 단일 시점 +15.2%p, 두 시점 동시 무이득; 근사 색인 재현율 차이의 답변 전파는 표본 부족으로 **탐색적(미확립)** — 스케일·생성기 능력·과제 비오염 세 경계의 좁은 교집합에서만 관측 가능.

### 5.8 최종 설계 가이드 (전량 보존)
| 상황 | 권장 설계 |
|---|---|
| metadata가 반드시 만족해야 하는 조건 | prefilter(검색 전 조건) |
| 의미적으로 넓은 soft intent 질의 | vector-only 또는 cautious filtering |
| 설명문(캡션)이 질의 의미를 잘 담는 데이터 | clip-caption(영상 설명문) |
| 설명문이 세밀한 시각 사건을 놓치는 데이터 | frame-vector(이미지 계열; 비용 트레이드오프 명시) |
| 선택도가 낮은 시간·위치 조건 | partial/local index(조건별 부분 색인) |
| 선택도가 넓은 조건 | global index + postfilter |
| 실제 운영 predicate 평가 | random mask가 아니라 real predicate 사용 |
| VLM-QA 답변 평가 | 검색 계층과 답변 생성 경계를 분리 |

### 5.9 30초 요약
본 연구는 새 VLM을 만드는 것이 아니라, 멀티모달 감시 데이터에서 VLM-QA가 사용할 검색 문맥을 벡터 데이터베이스 계층이 어떻게 저장·색인·검색해야 하는지 평가한다. 기존 연구(비디오 질의처리·filtered vector search·감시 VLM 벤치마크)가 다루지 않은 종단형 RAG 파이프라인의 DB 설계 문제를, AI Hub 522 중심 비순환 tri-source 워크로드(112 구성) 위에서 측정하고 MEVA·MIRIS·UCA로 외적 타당성을 보강했다. hard constraint에서는 검색 전 조건이 유리하나 자명하고, 저장 단위는 품질-비용 트레이드오프이며, 선택적 predicate에서는 부분 색인이 재현율을 회복한다는 설계 가이드를 도출했다.

---

## 6. 아키텍처·데이터 흐름 청사진 (810 기반)

### 6.1 전체 구조
시스템 = **오프라인 가공/인덱싱 파이프라인** + **온라인 하이브리드 검색/평가 파이프라인**.

```
[오프라인] CCTV 원본 프레임 ─→ 로컬 VLM(Qwen2.5-VL) 픽셀 전용 캡셔닝 ─→ bge-m3 임베딩 ─→ Documents 테이블(캡션+벡터)
           물리 센서 로그(CSV/XML) ─→ 스칼라 속성 파싱(시간·위치·신호) ─→ Metadata 테이블(속성-값 쌍)
           인간 주석(CVAT XML) ─→ 룰 기반 파서(주정차·이륜차 등) ─→ qrels 파일(DB 외부 격리 보관)
[온라인]  자연어 질문+센서 필터 ─→ (질의 벡터, 스칼라 조건) ─→ 하이브리드 조인 검색(PostgreSQL+pgvector)
           ─→ Ranked clip_id 리스트 ─→ ①평가 모듈(외부 qrels 대조, nDCG/Recall) ②검색 문맥 패킷 → VLM-QA(Qwen2.5-VL-7B) → 최종 답변
```

### 6.2 Tri-source 소스 격리 파이프라인 (순환성 원천 차단)
1. **Predicate(필터 채널)**: 루프 디텍터·신호 제어기·관측기의 기계 수집 CSV/XML → 텍스트·픽셀 개입 없이 `time_of_day`, `sig_has_yellow`, `sig_has_pedestrian` 등 스칼라 조건 파싱.
2. **Document(문서 채널)**: 원본 프레임 픽셀만 → 인간 라벨 일절 미참조로 독립 VLM(Qwen2.5-VL)이 캡션 기계 생성 → bge-m3 임베딩.
3. **Relevance(정답 채널)**: CVAT 주석 XML → 룰 파서로 `is_parked`, `bike` 존재 등 파싱 → qrels 빌드. **격리 정책: 이 채널은 DB 테이블·색인에 전혀 사용하지 않고 채점 모듈에서만 외부 파일로 보관.**

### 6.3 저장 스키마 (PostgreSQL + pgvector)
```sql
CREATE TABLE aihub522_documents (
    doc_id text PRIMARY KEY, clip_id text NOT NULL,
    doc_type text NOT NULL,          -- 저장 입도 (frame / clip / chunk)
    text text NOT NULL,              -- VLM 생성 캡션
    embedding vector(512)
);
CREATE TABLE aihub522_metadata (
    clip_id text NOT NULL, facet_name text NOT NULL, facet_value text NOT NULL
);
```
`clip_id`를 FK처럼 사용해 상호 JOIN. [정정 2026-07-28: 810 원문 DDL의 `vector(512)`는 bge-m3 캡션 임베딩 차원(1024d, 740·430 실측)과 불일치 — 512d는 CLIP 프레임 임베딩 차원이다. 청사진 예시의 차원 표기 오류로 기록.]

### 6.4 질의 계획 3분기 (설계 축 ②⑤의 구현 대응)
- **Pre-filtering(검색 전 조건)**: 메타데이터 만족 clip_id 먼저 식별 후 그 후보 안에서만 벡터 탐색(`WHERE clip_id IN (SELECT …)`). 하드 조건 100% 보장이나, 고선택 조건에서 exact scan 이행 또는 그래프 색인 단절(Graph Disconnection) 관찰.
- **Post-filtering(검색 후 조건)**: 전역 벡터 색인 상위 K 인출 후 필터(제출 논문은 상위 200 후보). pgvector 0.8+는 iterative scan으로 반경 동적 확대 — 빌드 비용 없으나 저선택도에서 지연 요동.
- **Partial/Local Indexing(조건별 부분 색인)**: 질의 빈도 높고 선택도 극단인 조건에 대해 해당 범위만 커버하는 특화 색인 개설(`CREATE INDEX … WHERE …`). **hot/cold 배포 모델**: N* = Index Build Cost / Per-Query Latency Saving. 누적 질의 수가 N*를 상회하는 핫 predicate에만 부분 색인을 물질화하고, 콜드는 global+iterative scan으로 라우팅. [SYNC: 제출 논문 배포 규칙 = 전역 재현율 0.95 미달 시 부분 색인/전수 검색 + 색인 갱신 시점까지 예상 질의 수의 선택도별 손익분기.]

### 6.5 비순환 채점·답변 연계
- strict/semantic 이중 채점(외부 qrels 대조). 핵심 실측: semantic positive의 72.6%가 센서 필터 미통과 → pre-filtering의 soft-intent 비보장성 정량화.
- 답변 연계 예시: 질문("교차로 A 부근 불법 주정차 적색 차량 몇 대?") → 검색된 프레임(검색 문맥 패킷) → VLM 프롬프트 결합 → 근거 프레임 판독 답변. 검색 문맥 품질(재현율)과 답변 정확도의 상관을 측정하되, 코퍼스 규모·모델 지각력이 전파를 제한(RQ6 탐색적 판정).

---

## 7. 사전등록 원문 요지 (410·420 — 규칙 단위 전량 보존; 원문은 아카이브 참조)

> 아래는 사전등록 문서의 절차·확증 가족·게이트·중단 규칙을 **규칙 단위로 전량** 옮긴 것이다. 수치 결과가 제출 논문과 다른 표기인 곳은 [정정]으로 연결했다. 당시 용어(evidence 등)는 원문대로 보존한다.

### 7.1 410 — 다각도 answer-level 사전등록 (2026-07-08 LOCKED, 실행 완료)

**배경**: retrieval-level 다각도는 통제된 negative(naive dual-view 병합 ≈ single view; 겉보기 상보성은 max-of-two 착시 — permutation control이 이득의 88–92% 재현). AI Hub 71953의 evidence layer가 라벨링상 대칭(4,500 clip 전부 view당 정확히 3 human-bbox frame)이라 retrieval은 진짜 다각도 이점에 구조적으로 blind → 유일한 방어 경로 = answer-level VLM 실험 on view-asymmetry stratum.

**규칙 전량:**
1. **Task(누출 없는 중립 질의)**: 고정 질의 "제시된 증거만 보고 관찰되는 사건 유형을 후보 중 하나로 고르라"; 후보 = 11개 event_class 전체(seed=20260708 고정 셔플, 모든 조건 동일); 출력 JSON `{event_class, confidence, supporting_view, rationale}`; 정답 = clip의 실제 event_class. **원본 VQA 질문 사용 금지**(event_class 누출); 프롬프트에 후보 목록 외 event_class 노출 금지.
2. **조건**: better_view = 평균 bbox 면적이 큰 view / worse_view = 작은 view; closed_book(이미지 없음, prior floor) / worse_view_only(3장) / better_view_only(3장) / both_view(6장). strata: asymmetric(ratio≥2)=MAIN, symmetric(ratio<1.2)=CONTROL.
3. **표본**: 디스크 실측 full 4,500 중 ratio≥2 = 1,536(34.1%); subset-110은 30(27.3%)로 검정력 부족 → full canonical에서 새로 materialize: asymmetric 250 + symmetric 150 = **400 clip**, 11 class×Train/Val 균형, seed 20260708, 조건당 400문항 paired. 목표 검정력: SESOI |Δacc|<0.05에서 stratum당 n≥150.
4. **지표**: 조건별 exact-match 정확도; Δ(better−worse), Δ(both−better), Δ(any−closed); invalid-JSON/hallucination 비율; supporting_view 일치율(both_view 조건에만); paired bootstrap 95% CI(5,000)+Wilcoxon; null 주장 시 TOST 등가검정 vs SESOI |Δacc|<0.05.
5. **모델·프롬프트 고정**: Qwen2.5-VL-7B-Instruct(resolved commit pin), temperature=0, greedy, max_new_tokens 고정, 템플릿·리사이즈·후보 순서 모든 조건 동일. GPU 2×RTX3090.
6. **Go/No-Go GATE(해석 전 필수)**: (i) both_view acc > chance(1/11≈0.091) **그리고** (ii) both_view > closed_book(CI excl 0). 하나라도 실패 → VLM이 한국어 CCTV 검색 문맥을 grounding 못함 → view 비교 무효, VLM-limitation으로 보고(데이터셋 결론 아님).
7. **사전등록 해석 규칙**: both>better(CI excl 0, Δ>SESOI) → 다각도가 answer-level 추가 이득 / better≈both>worse → **DB는 view를 쌓지 말고 좋은 view를 선택해야** / 모두 등가(TOST) → 현 데이터·모델에서 미관측(조건부) / gate 실패 → 해석 무효. **금지(어떤 경우에도): "다각도는 일반적으로 무의미하다."**
8. **산출물**: stratum manifest, view-condition packet, VLM 추론, JSON parsing/eval, paired bootstrap+TOST, symmetric control, claim/no-go 문서.
9. **알려진 위험(사전 명시)**: bbox 면적은 "잘 보임"의 proxy일 뿐(결론은 geometric visibility asymmetry로 한정); 두 view 시간 비동기(median 2.03s, 26% 무overlap); 11-way 분류가 3 keyframe으로 가능한지 자체 불확실(gate가 검출); VLM 한국어 CCTV 역량 미검증(gate로 방어).

**실행 결과(2026-07-09 갱신)**: 설계 실행 완료. 세 개의 강한 VLM에서 `better-view > worse-view`, `both-view ≈ better-view` 반복; Idefics2는 near-chance 보조 근거. [정정 2026-07-28: 제출 논문 RQ6 정본 표기 = **잘 보이는 단일 시점 +15.2%p, 두 시점 동시 무이득**.]

### 7.2 420 — Pillar B/E 사전등록 (2026-07-10 LOCKED) + Amendment 1–9

#### 7.2.1 본문 설계(심사-방어 규칙)
**§0 예상 지적별 방어 설계(전량):**
- 미격리 wall-clock → 검색계층만 격리: `omp_set_num_threads(1)`, batch=1, 워밍업 W=5 유지·통계 제외, 반복 R=15, 질의별 중앙값→질의분포 p50/p95(+p99는 n≥500만), CI=질의 리샘플 부트스트랩, config 무작위 인터리빙+taskset; 동일 호스트 상대비교만, 절대 ms는 하드웨어 한정.
- random-mask 장난감 → **실측 predicate 주결과 + 동일-s random-mask 대조군 짝지어 병행**(합성 fraction은 주결과 금지, 대조군 라벨만).
- postfilter K' 임의 → K'∈{⌈k/s⌉, 2⌈k/s⌉, 4⌈k/s⌉} 전부 보고, 단일 K' 결론 금지.
- 작은 코퍼스 ANN 주장 → N-스케일 정직 게이트: ANN 이득/crossover 주장은 N≥100K에서만; 소형 코퍼스는 "이 규모엔 Flat 최적"을 결과로.
- CI/다중비교 → recall=query-부트스트랩 95% CI, latency=반복블록 백분위 CI, 답변=paired bootstrap+Wilcoxon+Holm; 등가 주장 시 SESOI 사전등록.
- synthetic 1M 대표성 → synthetic_aug 라벨 분리, real 관측 + "증강 투영" 명시.
- prefilter_hnsw 재구축 비현실 → build_s 1급 비용 + "핫/정적 파티션에만 유효" + single_stage(IVF+IDSelector) 대안 실측.
- 3축이 2축 → E-1에서 동일 QA 파이프라인에 색인만 스왑, 정확도·evidence-caption 회수율 동시 측정, 결과는 3-outcome으로만 서술.

**B-1 실측 predicate filtered-ANN**: 코퍼스 A=sinnaedoro 132,521×512(+frame_index), 코퍼스 B=522-visual 143,830 전 프레임(미조인 9.8%=facet-NULL 전 predicate 불통과, 조인 실측 ≈129.7K); predicate 셋은 부속표 P1로 사전등록·고정(natural=단일 facet 등호 / composite=범위·IN; NOT 불사용; 코퍼스 간 비교는 s-범위 교집합에서만); 방법=prefilter_flat/prefilter_hnsw(M32,efC200,efS64)/postfilter_hnsw(K' 3점)/single_stage(IVFFlat+IDSelectorBatch); GT=subset 내 exact top-10; 질의 A=1,000(구 "500" 정정), B=image 200(확증층)/text 32(기술층, 풀링 금지).

**B-2 색인 3축**: `index_benchmark_from_log.csv`(10K–1M, 55 config) 신규 계산 0으로 본문 자산화(real/synthetic 분리 라벨); 522-visual 143K 동일 그리드 1회(2번째 real 점); VRU 1K는 E-1 스왑셋과 동일 3점; "Flat 최적" 근거는 recall=1·build 0·운영 단순성으로 서술(latency 교차 아님).

**B-3 pgvector 실색인**: HNSW(m∈{16,32}, efC=200, efS∈{16,64,256})/IVFFlat(lists=√N≈364·1024, probes∈{1,8,32}); recall@10 vs pgvector exact, p50/p95(warm·단일 커넥션), pg_relation_size, build wall; 필터드는 EXPLAIN(ANALYZE)로 planner 경로 기록; TPS/동시성 주장 금지.

**E-1 색인 근사→답변 결합**: `run_rag_vqa.py`(고정 LLM 2종) 색인만 스왑; exclude=cid 유지(해제 시 순환 재도입); **조작점검 게이트**: LLM 실행 전 retrieval-only 파일럿으로 evidence-recall@3 실측 → 중간 [0.55,0.85]·강열화 [0.30,0.55] 밴드 → 조정 사다리 → 통과 3-config diff-LOCK 후에만 착수, 사다리 소진 시 착수 금지·재회부; null 해석은 게이트 통과 전제에서만. 측정=(a) 답변 정확도 (b) evidence-caption 회수율(사전 계산·고정 qrels; 구 "gold-caption-in-context"는 exclude=cid 하 항등 0이라 폐기) (c) Δacc vs Δevidence-recall 산점. 해석 3-outcome: ①우월(Holm 유의) ②등가(TOST 90% CI ⊂ ±0.02) ③결론불가('강건/평탄' 주장 금지, CI만). n=6,000/config 전량(n=600은 SESOI 0.02와 양립 불가); Holm 계층(primary=Flat vs 강열화×2LLM); SESOI 0.02 정당화=oracle−closed 격차 0.438의 ~4.6%. 매개분석: 간접효과 부트스트랩 CI(5,000)+logistic 직접효과, "완전매개 증명" 표현 금지.

**E-2 3축 Pareto**: 두 패널 분리(단일 frontier 합성 금지) — (i) retrieval Pareto(y=recall@10; 구 "nDCG" 폐기) (ii) answer Pareto(VRU 1K, y=acc). x=p95; 마커 크기=index_mb, 색=build_s(합성 금지); Pareto 판정은 (p95,품질) 2축만, 비용은 tie-break; pgvector 점 미포함(계측 경계 상이); 비용 스코프 각주(storage=색인 계층 한정, 임베딩=1회성 ingest 별도, faiss vs pgvector index_mb 정의 차이, 검색 ms vs LLM 초 규모 차이).

**§7 공통 규칙(전 실험)**: 모든 헤드라인 비교에 95% CI(부트스트랩 5,000)+n 명시; Holm 확증 가족은 유의성 계산 전 선언(B-1은 코퍼스×사전지정 s-3구간×방법쌍 recall만 확증, 나머지 전 조합=탐색적·별표 금지); 등가 주장 SESOI: retrieval recall 0.02/answer acc 0.02; 모든 표에 코퍼스 N·real/synthetic 라벨·질의 수·반복 수 병기; **수치는 결과 파일에서만(스크립트 재집계 가능) — F5 검증기 원칙**.

#### 7.2.2 Amendment 1 (07-10, 적대 검증 3-렌즈 반영)
- BLOCKER 반영: B1 predicate 2등급제·교집합 규칙 / B2 매개변수=evidence-caption 회수율 재정의 / B3 허위 인용 폐기+조작점검 게이트·사다리 / B4 n=6,000·3-outcome·SESOI 정당화 / B5 E-2 두 패널·비용 표현 분리.
- MAJOR 반영(스크립트 구속): M1 타이밍 경계 통일(postfilter의 mask 필터·절단 포함; build_s/selector_build_ms 분리; ef≥k 강제; K'≤N 캡+"K'≈N 축퇴" 라벨) / M2 latency 통계(R=15 중앙값→질의분포; 워밍업 W=5 유지·통계 제외로 §0 "warmup 폐기" 정정; 무작위 인터리빙+taskset; p99는 n≥500만) / M3 pgvector(행 facet 비정규화 단일행 쿼리 — EAV+GROUP BY 금지; GUC 매트릭스 iterative_scan∈{off,relaxed_order}·max_scan_tuples·SET LOCAL; 반환 행수 열; EXPLAIN은 timed 반복과 분리; `<#>`+정규화로 faiss IP 동치; faiss↔pgvector latency 비율 서술 금지) / M4 single_stage 공정성(selector_build_ms 별도 열; s≥0.25에 IDSelectorBitmap 병행; nprobe=32 recall<0.9면 128 추가) / M5 코퍼스 B 정직화(전 프레임 색인·NULL 비율 열·GT 분모 정정·selectivity 프레임 가중·queries 1,000 정정) / M6 질의 층화(text 32/image 200 풀링 금지; 확증은 image-200만; tri-source 연속성 주장 금지) / M9 s-교락 대조군(자연 predicate마다 동일-s random-mask 짝; 기존 코드=대조군 강등; GT top-10 전역 rank 중앙값 기록; 결론은 predicate 유형별 한정) / M10 "crossover" 어휘 금지→"regime" / M11 비용 스코프 각주.
- 기각(기록): R1 pg heap+index 이중보고(전제 사실오류) / R2 공통상수 비용 산입 / R3 저s postfilter 붕괴=병리 확인 가치 / R4 n·SESOI 완화안 / R5 NOT-predicate / R6 exclude=cid 해제(순환 재도입) / R7 패러프레이즈 정량 주장.

#### 7.2.3 Amendment 2 (07-10) — E-1 조작점검 게이트 FAIL, 착수 금지
- 파일럿 실측(n=6,000×26 config): exact evidence-recall@3=0.5162; 사다리 전 구간 rel∈[0.974,1.053] — 목표 밴드 도달 0개(일부는 exact보다 높음).
- 기전: (i) evidence 집합 과밀(평균 334.3/1,000=33%) (ii) 1K 벡터에선 PQ급 근사도 의미 이웃 보존 (iii) 근사 오차가 무작위화로 작동해 회수율을 올림(random-3 기대 0.705>exact 0.516).
- 판정: 사다리 소진 → **본 실험 착수 금지**(게이트 규칙 그대로; GPU 12–20h 소비 전 차단). 정직한 부산물: "1K-문서급 RAG 코퍼스에서는 색인 선택이 evidence 전달을 사실상 바꾸지 못한다(26 config 실측)". 재설계 선택지 (a) 143K 이전 / (b) 축소 종결.

#### 7.2.4 Amendment 3 (07-11) — E-1(a) 143K 재설계 프리레지
- 설계: 항목=(시각 비디오 v, 이진 장면 질문, 정답=사람 주석 채널); 검색=중간 프레임 임베딩으로 143,830 전프레임 top-3, 자기 제외; VLM은 검색된 프레임만 봄; 매개변수=moment-recall@3(순간 그룹 31,380, 항목당 evidence 중앙값 4프레임 — 희소); 질문 3종(bus/stopped/bikes) 층화 50/50; Qwen2.5-VL greedy yes/no.
- 조작점검 게이트 PASS: exact moment-recall@3=0.1203(n=2,967); mid=hnsw_M8_ef1(rel 0.807), strong=ivfpq_m32_np8(rel 0.451), LOCK 파일 고정. 기저 12%의 원인=동일 카메라 배경 유사성(그 자체 보고 가치).
- 규모 규칙(사전등록): 미니 파일럿 쌍대 불일치율 d̂로 CI 반너비 ≤ SESOI 0.02 만족 최소 n, 상한 6,000(초과 필요 시 착수 금지·재회부); 해석=3-outcome+Holm.
- **중단 규칙**: 미니 파일럿에서 인과 지렛대(acc|hit − acc|no-hit)가 CI로 0과 구별 불가 → 본실험 착수 금지, "143K에서도 답변축은 mediator 희소성에 의해 제한"을 정직 결과로.

#### 7.2.5 Amendment 4 (07-11) — 중단 규칙 발동, 답변-결합 축 정직 종결
- 미니 파일럿(360콜): 지렛대 −0.020, CI ≈ ±0.13(0 포함) → **중단 규칙 그대로 발동, 본실험 착수 금지.** 매개변수 조작은 성공(hit-rate 0.122→0.056) — 사슬은 **지각 단에서 단절**(VLM 절대 정확도 0.567–0.594, chance 0.5).
- **종결 판정('두 벽')**: ①소형(1K) 코퍼스 — 색인 열화가 evidence 전달을 못 움직임(mediator 벽) ②대형(143K) — 전달은 움직이나 고정 VLM 지각이 병목(perception 벽). "색인→end-to-end 과장 금지" 상시 규칙의 실증 근거로 승격. E-2 answer 패널 미게시 확정. [정정 2026-07-28: 이 종결이 제출 논문 RQ6의 "근사 색인 재현율 차이의 답변 전파는 표본 부족으로 탐색적(미확립)" 서술의 근거 계보다.]

#### 7.2.6 Amendment 5 (07-12) — B-4: 제3 엔진(Milvus·Weaviate) 기전 재현 프리레지
- 가설 H-B4: 실측(상관) predicate가 공유 색인 filtered-ANN 재현율을 동일 선택도 무작위 마스크 대비 떨어뜨리는 기전이 전용 벡터 DB 네이티브 필터드 경로에서도 재현. 재현 실패도 그대로 보고(엔진 완화 설계가 기전을 흡수하면 그 자체가 발견).
- 고정: Weaviate 1.35.3+client v4 / Milvus standalone 2.6.0+pymilvus 3.0.0; 컬렉션 `kiise_*` 접두·보존. 데이터·질의 B-1과 동일(A: CLIP-text 1,000, B: 이미지 200, 시드 재현). 대조군 시드 `default_rng(20260712+predicate_index)`(B-1과 독립 드로우 명시).
- 파라미터: HNSW M=32, efC=200, ef=64, IP(정규화). 조건 (m1) Milvus 기본 필터드, (w1) Weaviate 기본(flatSearchCutoff 서버 기본 — flat 폴백은 엔진 완화책 발견으로 보고), (w2) cutoff=0. **엔진 간 지연 절대 비교 금지**, 엔진 내 상대만.
- GT=부분집합 내 exact top-10(엔진 무관 로컬, 스테이지-1 고정). 게이트 G-ingest: 적재 수=N 정확 일치 AND 비필터 recall@10≥0.95 — 미달 시 본실험 금지. 확증 가족={m1,w1,w2}×{A,B}=6검정, paired Δ(control−real), predicate-부트스트랩 CI+Wilcoxon+Holm. 중단 규칙: G-ingest 실패 엔진만 제외.

#### 7.2.7 Amendment 5a (07-12) — B-4 설계 정정(확증 계산 전 재선언)
1. **엔진 폴백 대칭 처리**: Milvus knowhere는 filtered-out>~0.93에서 무성 브루트포스 폴백 — 실측 경계 **(0.923, 0.934]**. m1을 m1-graph(확증)/m1-BF(기술, 혼입 금지)로 분리, 경계는 s 스윕으로 실측·manifest 기록. [정정 2026-07-28: 제출 논문 RQ5의 "필터율≥92.3% … 전수 검색 자동 전환"이 이 실측 경계의 정본 표기.]
2. **Weaviate 조건 재정의**: 1.34+ 기본 filterStrategy=ACORN → w1:=acorn+cutoff=40000(기술), w2:=sweeping+cutoff=0(**확증** — 공유 색인 기전의 진짜 대응 경로), w3:=acorn+cutoff=0(기술); 기존 'w2' 행은 w3으로 재라벨(manifest 기록). [정정 2026-07-28: cutoff=40000이 제출 논문의 "조건 만족 벡터<40,000이면 전수 검색 자동 전환"의 근거.]
3. **확증 가족 재선언**: {m1-graph, w2-sweeping}×{A,B}=4 Holm 검정; w1은 구조적 기각 불능으로 기술 레인 강등.
4. **의사반복 방지**: 1차 확증=자연 predicate만(A 24·B 22); 헤드라인 재현 주장은 predicate-부트스트랩과 facet-가족 군집 부트스트랩 CI **모두** 0 배제 필요; 질의 공유 의존은 한계 명기.
5. **G-filter 게이트**: 엔진측 필터 카운트==로컬 마스크 크기 어서션; Milvus index_building_progress 100%·세그먼트 상태 기록(기수집분 소급 검증).
6. **재현 산출물 보강**: qidx_B.npy+sha256; P1 양방향 집합 동등(A 29·B 25); 대조군 시드 정의 명문화; 서버 에코 설정 덤프.
7. **F7 레인**: '시드 재현 스팟체크'로 재명명 + predicate당 대조군 r=5 반복 드로우 분포(SD/range); 엔진 레인 1드로우 MC 노이즈는 한계 명기.
- 기각 3건(반박 성립): 코퍼스 B 자기 제외(이미 K+1 구현), 확증 규칙 미고정(사전 고정됨), 대조군 오염(사전 동결됨).

#### 7.2.8 Amendment 6 (07-12) — UCA 외적 타당성 워크로드 프리레지 (2.5-채널, 탐색적)
- 목적: 비순환 프로토콜의 도메인 외적 타당성(영어·이상행동 UCA/UCF-Crime) — (i) 이중 정답 구조 재현, (ii) 결합도-Δ 방향 경향 재현. **지위=탐색적 외적 타당성 트랙: 새 확증 헤드라인을 만들지 않는다.**
- 데이터: UCA 주석(1,854 비디오·23,542 문장, 분할 1,165/379/310 논문 일치) + UCF-Crimes.zip(Content-Length 102,957,372,377B 실측); 학술 연구 전용 라이선스 명기.
- 코퍼스 규칙: 비디오별 timestamps 정렬 후 `round(linspace(0,n−1,min(n,4)))`로 비디오당 최대 4 이벤트(결정론); 문서=중앙 시점 프레임 1장을 Qwen2.5-VL 캡션(렉시콘 용어를 프롬프트에 넣지 않음).
- 정답 채널: 자기 주석 문장 정규식 렉시콘 10종 동결; 채택=밀도 창 [1%,12%]+strict 양성 ≥5, **사후 추가·수정 금지**; 채택 <3이면 워크로드 부적합 정직 보고(강행 금지).
- predicate 채널 3필드: video_class(14값)/video_duration_bin(3분위)/event_position_bin(3분위, 주석 타이밍 유래 별도 공개).
- 질의: (필드값×렉시콘) 기계 교차곱, strict 양성 ≥5; 렉시콘당 1개 동결 영어 문구; 이중 qrels; V 라벨; 채택 <30이면 "저검정력, 보고 전용".
- **A6-UCA 감사 6 어서션**: (a) 필터 키 ⊂ 3필드 (b) 정답 ⊂ 동결 렉시콘 (c) 키 교집합 ∅ (d) metadata에 정답 플래그 없음 (e) verbatim 8-gram 중복 0+라벨 키 누출 0(픽셀 유래 어휘 중복률은 별도 보고 — 2.5채널 정직 한계) (f) 정답 밀도 ∈[1,12]%. + B4−B2 semantic 부호분포의 음수 존재를 C1 붕괴 동반 지표로 보고.
- 검색·통계: B0/B1/B2/B4/B5 체인 재사용; 질의 부트스트랩+쌍 군집 부트스트랩 병기; **방향 서술만, CI 0 배제 주장 금지**(탐색 지위).
- 게이트: G-B(zip 무결·주석 id 전부 존재), G-C(캡션 파일럿 50 PASS 전 전체 GPU 금지), G-D(A6-UCA 6/6).

#### 7.2.9 Amendment 6a (07-12) — UCA 설계 정정 동결본 (12건 확정+5 보완)
1. **렉시콘 정정·재동결**(BLOCKER: `hit`가 'white' 내부 매칭 — 위양성 81%): 전 렉시콘 좌측 단어 경계+IGNORECASE. 동결표(10/10 채택): falls `\b(fell|falls|falling|knocked down|collaps)` 1.40% / fight `\b(fight|punch|kick|beat|hit(ting)?)` 4.62% / fire 2.13% / weapon 2.22% / running `\b(ran|runs?|running)\b` 4.77% / crash 1.12% / money 1.82% / door `\bdoors?\b` 10.93% / take 6.36% / enterexit 5.07%.
2. **중복 붕괴 규칙**: 동일 (video_id, midpoint) 세그먼트 1문서 붕괴(58개→6,432 문서); linspace 경계 재가중 공개(V≤0.062라 결론 불변).
3. **qrels 명문+퇴화 스크린**: strict=렉시콘∧predicate, semantic=렉시콘만; **class-필드 질의는 'C1-재라벨링 계층'으로 별도 보고, 고전적 prefilter 가치 재현 근거로 인용 금지**; 퇴화 스크린(필터 밖 semantic 양성<10 또는 봉쇄율>0.9)=분리 보고(현 데이터 1쌍: RoadAccidents×crash 0.904); V는 퇴화 탐지 못함 명기.
4. **predicate 재분류**: duration_bin=유일한 채널-청정 헤드라인 필드; position_bin=보고 전용 강등; class=라벨-부호화 계층. A6-UCA에 predicate 출처 어서션(소스 파일·필드·생산자 기계 매핑) 추가.
5. **결합도 이중 계층**: 스펙트럼 쌍봉(컨테이너·타이밍 V≤0.077 vs class V∈[0.125,0.569]) → **단조 곡선 주장 금지**; Δ-V 산점+채널 계층 주석; 질의 결합 라벨=값-수준 φ.
6. **방향-일치 반증 가능 규칙(4-대조 동결)**: ①strict 풀 Δ(B4−B2) 부호>0 ②semantic 저-V 필드 풀 Δ 부호 ③semantic 질의별 부호 음수 존재 ④semantic에서 Δ(class 계층)>Δ(저-V 필드) 순서. **'522와 방향 일치' 판정 = 4중 3 이상**; 어느 쪽이든 집계 그대로 보고. [정정 2026-07-28: 제출 논문 RQ3의 "UCA 129질의 재현 3/4"가 이 규칙의 최종 판정이다. 740 감사의 "135질의" 표기는 논문 정본 129로 정정.]
7. **의존 구조 3-레인**: (필드×렉시콘) 쌍 군집(27) / 렉시콘-수준 군집(10, 최보수) / 비디오-중복제거 채점 레인 병기; 질의 채택에 '서로 다른 비디오 ≥5' 추가.
8. **감사 (e) 재구성**: (e1) 하드: 라벨-키 누출 0 (e2) 하드: 렉시콘 용어 포함 8-gram 문서-주석 중복 0 (e3) 일반 verbatim 8-gram은 보고(코퍼스 2% 초과 시 중단).
9. **게이트 보강**: class 값 상한 철폐(14값 전수); Normal_Videos(47.1%)는 고선택도 계층 분리 보고; G-B 전단사 규칙; **G-B′(GPU 전 CPU 게이트)**: 1,854 전체 ffprobe, container_duration≥max midpoint+0.5s, 위반 시 clamp+건수 보고, ffmpeg 시간-기반 시킹(프레임 인덱스 산술 금지); G-C 파일럿 50에 적대 계층 강제; 저검정력 재정의(렉시콘<5 또는 필드 가족<2면 '보고 전용').
- 기각 3건 기록(밀도 분모/대역 공동화/값 상한 모순). 게이트 집행 기록: 전단사 위반 49건(Normal id 폴더 중복, 동일 파일) → **해소 규칙(사용 전 선언): 멤버 경로 사전순 첫 항목 채택**, `id_to_member.json` 동결.

#### 7.2.10 Amendment 7 (07-12) — CC-FR 프리레지 → 착수 전 KILL (컴퓨트 미집행)
- 제안: CC-FR(Coupling-and-Cluster-aware Filtered Retrieval) — 경성 h_p·결합도 V_p·군집 심도 κ_p·빈도 f_p로 검색 계획 라우팅(하드→prefilter 필수+핫이면 지역 색인 물질화; 소프트→V_p<0.3이면 필터 생략 vector-only). 기준선 S1–S4+오라클. 이중 조작점검 게이트 G-EP((a) 증거 이동 ∧ (b) 답변 민감 통과 시에만 답변 실험).
- **판정 KILL(전부 실측)**: [BLOCKER] G-κ FAIL — 질의 무관 κ_offline이 공유-postfilter 결손 예측 못함(ρ −0.38/−0.05 부호 반대; 유효한 것은 질의-구동 신호 ρ 0.70–0.90뿐, 순수 오프라인 불가); [BLOCKER] κ 죽으면 CC-FR=기존 가이드라인의 2비트 룩업(제안 구조 프레이밍 붕괴); [MAJOR] V_p와 군집 분기가 서로 다른 코퍼스·인코더에 존재(관련도+스케일 동시 보유 코퍼스 부재); [MAJOR] 비용 우위가 미측정 f_p 의존; [MAJOR] G-EP가 두 벽을 못 닫음.
- 정직한 귀결: 방어 가능한 기여는 비순환 워크로드 프로토콜+기전 발견+가이드라인에 머문다.

#### 7.2.11 Amendment 8 (07-13) — P8 색인→답변 확증 프리레지 → 착수 전 KILL
- 제안: 존재 질문("predicate 조건 만족 클립 중 event가 보이는가") + 매개변수=양성-클립 재현율@k + 완전 매개 가설 H8; SESOI 0.10, n≈200, G-manip(스프레드≥0.30) 게이트.
- **판정 KILL(P1 데이터 자체로 반증)**: [BLOCKER] "무관 클립만 보면 no" 전제가 거짓 — distractor에서 InternVL3 P(yes)=0.64가 gold와 무관(**내용-유발 yes-편향**); distractor≈closed는 상반 편향의 우연한 상쇄; [BLOCKER] 완전 매개 구조적 불가(gold=no엔 매개변수 부재, gold=yes에선 동어반복); [MAJOR] G-manip 오인용(다른 양); [MAJOR] 통계(불일치율 가정·TOST 도달 불가·군집 무시); [MAJOR] 독창성 절대 주장 과대.
- 정직한 귀결: "구조가 답변에 전파되는지는 좁은 체제(스케일×VLM 능력×태스크 비오염)에 갇혀 있음"의 경계 규명 자체가 신규 결과. [정정 2026-07-28: 이 경계 규명이 제출 논문 RQ6의 탐색적 판정으로 수렴.]

#### 7.2.12 Amendment 9 (07-13) — P9 KG-as-index 프리레지 → "KG 우위" 가지 KILL
- 제안: 경량 KG-as-index(노드=클립+센서-facet 값+캡션-엔티티; 엣지 소스 분리, **주석 채널 유래 엣지 0**)를 tri-source 위 추가 구조로; A6-KG 감사(KG-a~f + 엣지-출처 표); 질의 유형(단순 vs 합성 다중-홉); H-KG 등가/우위 어느 쪽이든 정직 보고.
- **판정 KILL(구축 전, 3 BLOCKER 생존)**: ①세 번째 신호 채널이 없음(tri-source는 정확히 3채널 — KG 엣지=센서(=B0/B4)∪캡션(=B1/B2), 구성상 강제) ②predicate 축≡B4(정의상; strict에서 KG=B4 by construction) ③캡션-엔티티 채널 실측 near-chance(과잉 언급 bus 97.4% 등+대량 부정문; P(gold|엔티티)≈기저율).
- 정직-함정 정정: 엔티티-중첩을 필터 안에서 계산하면 ~0.232 strict(B0 0.218 위) — 단 "틀린 이유로" 이길 수 있음 → G-KG-floor 게이트(B0을 SESOI만큼 상회 선결) 필요.
- 추가 강제(생존 MAJOR): affirmative-only 부정-인지 추출 sha-동결; KG-g(렉시콘은 공개 질의-의미어에서만, gold 참조 전 동결)·KG-h(극성 규칙 사전 동결); 랭킹 함수 diff-잠금; 합성 확증은 독립 facet-family 쌍 6개뿐(2-홉=확증/3-홉=탐색); "그래프 계열 빠짐" 동기 재서술.
- 생존 코어: (1) A6-KG 감사=비순환 프로토콜의 그래프 백엔드 확장(방법론 기여) (2) KG를 정직하게 라벨된 구조 baseline (3) 경계/음성 결과("캡션 기반 코퍼스에서 entity-KG 검색은 sparse-entity-match로 붕괴, dense에 지배"). Path B 후보: intersection_id 관계형 2-홉(B4가 구조적으로 표현 불가한 유일한 진짜 그래프 기전; 재검토 선결). [정정 2026-07-28: 제출 논문 RQ4의 "지식그래프 재조합 Lift 중앙값 0.002 무이득"이 이 경계 결과의 정본 수치.]

---

## 8. 검증 체계 (430 기반 — 40/40 스위트, 규칙·판정 전량 보존)

원칙: **"실험을 했다"가 아니라 "누가 검증해도 성립한다"** — 모든 보증은 (i) 기계 실행 가능한 체크 (ii) 증거 파일 경로 (iii) 원고 서술 위치의 3요소. 실행기 `scripts/run_full_verification_suite.py` → **40/40 PASS**(`paper_assets/verification_suite_20260711/`).

### 8.1 5중(+외부) 검증 스위트
| 층 | 보증 대상 | 체크 수 | 재실행 |
|---|---|---:|---|
| V1 데이터셋 무결성 | 코퍼스 산출물 수량·정렬·정규화 | 9 | 스위트 |
| V2 워크로드 타당성 | 비순환 감사(A6/A9) 재어서션 + P1 predicate 재도출 | 10 | 스위트 |
| V3 체리피킹 방지 | 사전등록 이력·기계적 질의 재도출·대조군 완전성·사다리 전건·부정결과 보존 | 14 | 스위트 |
| V4 원고 수치 | 본문 전 수치의 원시 파일 재집계(94 체크 위임) | 1(→94) | `verify_manuscript_v2_numbers.py` |
| V5 환경 통제 | HW/SW 캡처 + 원고 핀-라이브 일치 | 6 | 스위트 |
| V6 외부 교차 검증 | 독립 모델(codex, 읽기 전용) 적대 감사 — 9건 판정 전 건 재현·처리 | 1회(07-12) | codex_crosscheck 산출물 |

### 8.2 데이터셋 4대 성질의 기계 보증
- **타당성**: 채널 소스 분리(필터=센서 CSV 카메라 10 / 정답=사람 CVAT 주석 카메라 11·22 / 문서=픽셀만 본 캡션) — A6 6-어서션(`document_token_leak_zero`, `filter_relevance_disjoint` 등)이 재검증. 조인 실재성: 조인율 90.2%@±120s·중앙값 0초 고정 파일. 결합도는 가정이 아니라 Cramér's V 실측·질의별 라벨.
- **재현성**: 원천→산출 전 경로 스크립트 고정(각 단계 manifest); P1 predicate 재도출성(24/24 일치); 라이선스·availability 명시.
- **충분성**: 검색 85질의(기계 교차곱)×3,000 캡션, strict 양성 ≥5; filtered-ANN 29+25 predicate×대조군, 132K/143K 두 실측 코퍼스; 답변 n=600(사다리)·400(다각도). 검정력 부족 밴드(A-high n=5, B-low n=3)는 "방향 동일·비유의"로 그대로.
- **객관성(V3 — 심장, 전량 보존)**:
  | 가드 | 기계 체크 | 의미 |
  |---|---|---|
  | 질의셋 무선별 | 85질의가 사전선언 규칙(5×5 교차곱, min_pos≥5, V<0.3 라벨)에서 비트-동일 재도출 | 유리한 질의만 고르지 않음의 구성적 증명 |
  | 표본 분리 보고 | 원본-32/신규-53/통합-85 세 행이 결과 파일에 존재 | 불리한 집계를 숨기지 않음(헤드라인 자기 교정) |
  | 대조군 완전성 | 실측 predicate 전건에 동일-s 랜덤 대조군 짝(29/29·25/25) | 유리한 predicate만 대조하지 않음 |
  | 사다리 전건 보고 | E-1 27행·E-1a 19행 전부 CSV 존재 | 게이트 통과 config만 남기지 않음 |
  | 부정 결과 보존 | '두 벽' 문서 + Amendment 2·4 착수 금지 기록 | 안 된 실험이 1급 기록 |
  | 정정 이력 공개 | binning 버그(−0.142→−0.099) 정정 주석 존재 | 조용한 수정 없음 |
  | 이중 정답 | strict+semantic qrels 세 워크로드 모두 존재 | prefilter에 유리한 채점만 쓰지 않음 |
  | 사전등록 우선 | Amendment 1–4가 실행 전 기록 | 결과 보고 규칙 변경 없음 |
  | 군집(쌍) 추론 병행 | 결합도 곡선 질의/쌍 이중 CI 재도출 — 쌍 군집 CI 0 포함 → 탐색적 강등 고정 | 의사반복으로 유의성 부풀리지 않음 |
  | 범위 한정(명문) | V3는 규칙 선언 이후의 선별만 차단; 설계 시점 자유도(밀도 창·SESOI·수리 대상·캡션 프롬프트)는 보증 밖 — 원고 공개 | 가드 보증 범위 과대 표기 방지 |

### 8.3 방법론 성질
- 타당성: 순환성 형식화(C1–C3)+경험 검증(붕괴 표+질의별 부호 음수=C1 보장 붕괴 직접 증거); 통계 규율=질의 부트스트랩 CI(5,000)·Holm 사전 선언·TOST+SESOI·탐색/확증 구분.
- 독창성(기여 1–4): ①3채널 소스분리+이중정답+기계감사+결합도축 워크로드 프로토콜 ②자기 워크로드의 진단·붕괴 사례연구 ③실측 predicate×동일-s 대조군 filtered-ANN 설계(무작위-마스크 과대평가 정량 폭로, 엔진 교차재현) ④게이트·중단규칙 기반 답변-결합 검증.
- 설명 가능성: 모든 효과에 메커니즘 동반(결합도 곡선, 결손↔군집 심도 ρ 0.62–0.895, 두 벽, 캡션 맹점). "왜"가 없는 수치는 헤드라인에 없다.

### 8.4 하드웨어/소프트웨어 스펙 (기계 판독 manifest)
Python 3.10.20 / PyTorch 2.12.1+cu130 / Transformers 5.13.0 / FAISS 1.14.3 / sentence-transformers 5.6.0 / numpy 2.2.6 / pandas 2.3.3 / CPU i7-9700K 8코어·RAM 62GB / RTX 3090 24GB×2(드라이버 580.126.09) / Linux 5.15 / PostgreSQL 16.14+pgvector 0.8.4(도커, `max_parallel_maintenance_workers=0`) / 시드 {20260709,10,11}. 핀-라이브 일치 어서션(V5). 계측 통제: 단일 스레드·워밍업 5 제외·R=15 중앙값 분포·계측 경계 다른 시스템 간 절대 비교 금지(faiss 13ms vs pg 왕복 218ms가 그 자체 증거).

### 8.5 심사자 재현 절차와 잔여 한계
- 재현: ①스위트 1회 실행=40 체크+94 재집계+환경 일치 ②증거 지도에서 질의 수준 parquet까지 심층 검증 ③설계 이력(420 Amendment→실행 로그→결과)의 시계열 완결.
- 잔여 한계(원고 명시): 단일 호스트(상대 비교만), VLM 파일럿 1종, 주간·평일 기록, cross-camera 조인 근사, pgvector partial-index 당시 미측정(→이후 710 P2로 측정됨), 결합도 곡선 탐색적(쌍 군집 CI 0 포함), 캡션 프롬프트-과제 결합, 동일 순간 잔여 장면 상관, 무작위 대조군 predicate당 단일 시드, 설계 자유도 민감도 미분석.

---

## 9. DB 기여 강화 실험 우선순위 (710, PI LOCKED 지시 — 전량 보존)

**PI 판단**: 새 데이터셋·새 모델보다 **저장 단위 + partial/local index 실험**이 게재 가능성·DB 기여도를 가장 크게 올린다. MEVA 실험은 이 과정에 자연 통합.

1. **저장 단위 비교(1순위, 최고 ROI)** — clip-caption vs frame-vector vs multi-vector vs dual-index; 정확도·지연·저장공간 영향. → **최종 논문 RQ2(설계 축 ①)로 편입.**
2. **pgvector partial/partitioned index(2순위)** — global+WHERE(postfilter) vs 조건별 partial/local index; recall·지연·build·storage. → **RQ5.**
3. **hot/cold predicate 운영 정책(3순위)** — local index 손익분기(선택도×질의빈도×build 상각). → **RQ5 배포 규칙.**
4. **외적 타당성(4순위)** — MEVA tri-source 구축·A6 PASS 완료, 1·2순위 실험의 제2 데이터셋으로 포함.
5. **추가 모델(5순위, 필수 아님)** — reranker upper bound 정도만 선택.

**강화된 기여 문장(반영 목표)**: "저장 단위, 색인 구성, 필터 결합 방식, 관계형 DB 구현 방식이 정확도·지연·저장공간에 미치는 영향을 함께 분석 … global index, postfilter, local/partial index 성능 차이를 측정함으로써 VLM-QA evidence layer의 데이터베이스 설계 지침 제시."

**통합 원칙(전량)**: 저장단위·partial-index는 522+MEVA 양쪽 측정(MEVA가 외적 타당성 자연 충족); 색인 3축은 재사용; 정직성 규칙 계승 — latency 격리·상대비교만, FAISS↔pgvector 절대비교 금지, real predicate 상관붕괴 caveat, 1M synthetic 라벨 분리.

**실행 계획**: P1 저장단위(522/MEVA, 동일 질의·qrels, nDCG·latency·index MB·recall@10) / P2 partial-index(pgvector global HNSW+WHERE vs `CREATE INDEX … WHERE`, selectivity sweep) / P3 hot/cold 정책(N*(s, build_cost, per-query 이득) 도표).

---

## 10. 실험 전체 구조 감사 (740, 2026-07-14 디스크 실측 — 감사 결과 전량 보존)

방법: 20-에이전트 workflow가 데이터셋 10 + 실험축 9를 디스크 실측으로 독립 검증. 전 축 `real_measured`, 데이터셋 8/10 실사용.

### 10.1 데이터셋 인벤토리 (확보×역할×실사용)
| 데이터셋 | 크기 | 역할 | 판정 | 사용처 |
|---|---|---|---|---|
| aihub_522_intersection | 142G | 헤드라인 tri-source+색인코퍼스 B | ✅ | 검색 B0–B5(85질의 expanded)·filtered-ANN 코퍼스B(143,830×512 CLIP)·저장단위·KG붕괴·지각벽. A6 6/6 PASS |
| sinnaedoro_traffic | 2.5G | 색인코퍼스 A | ✅ | 132,521×512 CLIP+1,000질의; filtered-ANN·색인3축 Pareto·pgvector. tri-source 아님(predicate-only) |
| meva_kf1 | 638M | 외적 타당성(검색+저장) | ✅ | 저장단위 P1(985클립)·B0–B5 외적검증. 헤드라인 아님 |
| miris_traffic | 2.0M | 외적 타당성(색인·배포) | ✅ | 59,019 CLIP프레임→pgvector→P2/P3 교차검증 |
| vru_accident | 265M | 붕괴데모+답변 | ✅ | v1순환→수리 collapse(RQ1)·검색 문맥 사다리(RQ6). A9 축소감사 |
| uca_anchor(UCA) | 176M | 외적 타당성(검색) | ✅ | B0–B5 영어 이상행동 외적검증, 사전등록 3/4. 2.5-채널(센서 없음). [정정 2026-07-28: 질의 수 정본은 논문 기준 **129질의**(감사 원문 "135질의"는 구 표기)] |
| aihub_intelligent_cctv | 85M | 붕괴데모+이식성 | ✅ | v1순환(완벽지표)→수리 collapse. A9 3-어서션 감사 |
| aihub_multi_angle_cctv | 426M | 답변계층(다시점) | ✅ | 400-event bbox-비대칭 stratum→4 VLM 다시점 답변선택 |
| cityflow_nl | 4.2M | (의도) 미사용 | ⚠️ | annotation-only staging; 소비자 0, 프레임 0장 |
| aihub_abnormal_cctv | 71M | (의도) 미사용·고아 | ⚠️ | 결과 실재하나 최종본 미사용(역할이 UCA로 재배정) |

### 10.2 워크로드 동작 방식 (비순환 tri-source, 522)
raw 프레임+CVAT 라벨(TL_3/4)+센서 CSV(TL_1/2) → facets(sensor=predicate / annotation=relevance / Qwen2.5-VL 픽셀-only 캡션=document) → canonical_trisource_expanded: clips 3,000 / documents 3,000 / metadata 27,000 / queries 85(low 75+contrast 10) / **strict qrels 6,809 / semantic qrels 24,872** [정정 2026-07-28: 감사 원문의 "6,810/24,873"은 논문 정본 6,809/24,872로 정정] → A6 감사 overall_pass=true(6/6) → bge-m3 임베딩 → B0–B5.
- 세 채널: PREDICATE=센서(time_of_day/hour/sig_has_yellow/sig_has_pedestrian/veh_density_bin) ⟂ RELEVANCE=사람주석 희소 scene(parked 2.3%/dense 2.2%/multi_bus 8.2%/bike 11.5%/stopped 21.2%) ⟂ DOCUMENT=캡션.
- 이중 정답: semantic positive의 72.6%가 필터 실패 → soft-intent에서 prefilter가 관련 문서 제거 가능(비보장성 실측).
- 설계 시 독립성: 30쌍 중 25쌍 V<0.3, global max 0.454.

### 10.3 축 × 데이터셋 × 결과파일 매핑 (실재 확인)
| 축 | 비교 대상 | 데이터셋 | 결과파일 |
|---|---|---|---|
| 검색 B0–B5(→RQ3·RQ4) | metadata/BM25/vector/postfilter/prefilter/hybrid × strict·semantic × 결합도 | 522(헤드라인)·MEVA·UCA·VRU·intelligent | results/trisource_expanded_b0_b5/* |
| 붕괴(→RQ1) | v1 순환 완벽지표→수리 붕괴 | VRU·intelligent | paper_assets/20260710_noncircular_collapse/* |
| filtered-ANN(→RQ5) | prefilter/postfilter/single-stage vs 동일선택도 무작위 대조 | sinnaedoro 132K·522-visual 143K | paper_assets/20260710_pillarB/filtered_ann_real_{A,B}.csv |
| 엔진(→RQ5) | pgvector·Milvus·Weaviate 네이티브 필터드 | sinnaedoro·코퍼스B | pgvector_*.csv + 엔진 bench |
| 색인 3축(→RQ5) | Flat/IVF-Flat/HNSW/IVF-PQ × 스케일(1만→1M) | sinnaedoro 132K+1M aug+522-visual 143K | index_benchmark.csv, fig_index_structure_pareto |
| 저장단위 P1(→RQ2) | clip-caption/frame-vector/multi-vector/dual | 522·MEVA | results/storage_unit/*.csv |
| P2/P3 부분색인·hot/cold(→RQ5) | global+WHERE vs partial; N* 손익분기 | sinnaedoro 132K·MIRIS 59K | paper_assets/20260713_db_design/* |
| 답변계층(→RQ6) | 고정 VLM에 검색 문맥 구성만 변경 | VRU(사다리)·multi_angle(다시점)·522(지각벽) | 답변 assets, gmanip_gate.json |

### 10.4 정직한 플래그 (감사 적발, 전량 보존)
1. cityflow_nl=미사용(구축만), abnormal_cctv=미사용·고아 → 논문 미등장이 맞음; 저장 정리 후보.
2. **완전 tri-source(full A6)는 522 단독** — UCA는 2.5채널, VRU·intelligent는 붕괴데모(A9 축소감사), multi_angle·abnormal은 label 단일채널. "비순환 헤드라인" rigor가 522 1종에 의존(최대 caveat, 원고 명시).
3. stale 산출물: sinnaedoro 구 무작위마스크 filtered_ann.csv(대체됨); VRU v1 결과트리 259M·intelligent 84M 다수 미소비.
4. §7.5 경로 정밀도: MEVA 저장단위 원자산과 pgvector P2/P3 경로 분리 표기 권장(경미).
5. exec-doc 700 초기 수치 stale: MEVA 1443클립/202질의는 캡션 전 수치, 최종 985클립/193질의(SUPERSEDED 정정됨).
6. 522 질의 3변형: 헤드라인=expanded(85q, 5×5 교차곱), 원본 32q(손선별)는 selection-bias 자기교정으로 공개, 15q는 붕괴용 수리 v1.

**총평**: 저장·검색·색인 비교 핵심 축은 전부 실측 결과파일로 뒷받침, 데이터셋→축 매핑 교차검증 일치. 유일한 실질 미사용 2종(정리 후보), 유일한 구조적 caveat=완전 tri-source 522 단독 의존.

---

## 11. 출처별 고유 내용 색인 (아카이브 위치 포함)

각 원본: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/<파일명>`

1. **300_PROBLEM_critical_design_review_20260709.md** — 이 파일에만 있는 것: v1 원고에 대한 Major Revision 판정 전문(9차원 findings), F1–F10 각각의 코드 수준 근거(어댑터 라인 번호, `metadata_filters⊂qrel_filters` 증명, weak/strong 질의 CSV 실측), 경미 문제 26건 태그 목록(STAT/METRIC/OVERCLAIM/HEDGE/REPRO/FORMAT/STRUCT/EXPR), 사용자 3대 질문 직답, P0/P1/P2 실행 로드맵, REFUTED 판정 4건(ForeSea id·버전 조작·LEAK-4/5).
2. **400_METHOD_experiment_system_masterplan_20260710.md** — 고유: 2026-07-10 디스크 실측 표(TL_1/TL_2 plain-zip 스키마, TS_3 75.18GB 솔리드 7z, TS_1/2 22바이트 placeholder), 거버넌스 결정 G1(A/C canonical 병합)·G2(B5 No-Go), 통합 실험 매트릭스(구 3-RQ×데이터셋×상태), Phase 0–5 로드맵과 T1–T11 트립와이어·No-Go 분기 전량, Exit criteria E1–E12, 자산 KEEP/REMEASURE/PROMOTE/DROP 분류표, env 실측(kiise-vlmdb faiss 1.14.3 등).
3. **410_METHOD_prereg_multiview_answer_level_20260708.md** — 고유: 다각도 answer-level 사전등록 원문(LOCKED) — 중립 질의 규칙·11 후보 고정 셔플·JSON 출력 스키마·bbox 면적 기반 better/worse 정의·400 clip 표본 규칙·Go/No-Go 게이트·해석 규칙 4종과 금지 규칙("다각도는 일반적으로 무의미하다" 금지)·알려진 위험 4종; retrieval-level max-of-two 착시(permutation 88–92%) 배경.
4. **420_METHOD_prereg_pillarBE_design_20260710.md** — 고유: Pillar B/E 사전등록 전문과 Amendment 1–9의 규칙·게이트·중단규칙·KILL 판정 전체(§7.2에 규칙 단위 보존). 특히 E-1 '두 벽' 실측 계보(Amd.2 mediator 벽 → Amd.4 perception 벽), Milvus BF 폴백 경계 (0.923,0.934] 실측, Weaviate ACORN/sweeping/cutoff=40000 조건 재정의, UCA 렉시콘 10종 동결표·4-대조 방향-일치 규칙, CC-FR/P8/P9 3연속 착수-전 KILL의 결함 증거, P9의 G-KG-floor·intersection_id Path B 후보.
5. **430_METHOD_verification_framework_20260711.md** — 고유: 40/40 검증 스위트의 층별 구성(V1–V6), V3 체리피킹 방지 가드 11행 표, 환경 manifest 전 항목(HW/SW/시드), 심사자 재현 3단계 절차, 검증 체계가 덮지 않는 잔여 한계 목록(codex 교차 검증 후 추가분 포함).
6. **710_METHOD_db_experiment_priorities_20260713.md** — 고유: PI LOCKED 우선순위 5개(저장 단위 최우선), 강화된 기여 문장 원문, MEVA 통합 원칙, P1/P2/P3 실행 계획. 최종 논문 RQ2·RQ5의 직접 기획 문서.
7. **740_AUDIT_experiment_structure_20260714.md** — 고유: 데이터셋 10종 인벤토리(크기·역할·실사용 판정), 축×데이터셋×결과파일 실재 매핑, 정직한 플래그 6건(미사용 2종, tri-source 522 단독 의존, stale 산출물, 522 질의 3변형), relevance facet 희소율(parked 2.3% 등), 설계 독립성 실측(25/30쌍 V<0.3, max 0.454), semantic positive 72.6% 필터 실패.
8. **760_RESEARCH_FLOW_20260714.md** — 고유: 한 줄 flow와 단계 간 인과 사슬(①→④), 핵심 발견 7종의 압축 수치 서술(MEVA strict +0.093 CI, HNSW ≈300× 지연 이득, PQ 22–35× 압축 등). 나머지는 상세본에 흡수.
9. **760_RESEARCH_FLOW_systematic_explanation_20260714.md** — 본 통합의 서사 정본. 고유: 기존 연구 3흐름 명시적 정리(NoScope~EQUI-VOCAL / Filtered-DiskANN~ACORN / UCA~ForeSea), 구 RQ 3문항 체계, 데이터셋 역할 서술, 변수 4종 표, strict/semantic 채점 예시, 결과 1–7 통찰 문장, 최종 설계 가이드 8행 표, 보고용 흐름 문장·30초 요약.
10. **810_overall_blueprint_20260715.md** — 고유: 오프라인/온라인 파이프라인 조감도(mermaid 원본은 아카이브 참조), tri-source 채널별 입력·처리·격리 정책 명세, PostgreSQL DDL·INSERT 예시, 질의 계획 3분기 SQL 구현(pre/post/partial)과 각 방식의 실패 모드(Graph Disconnection, iterative scan 지연 요동), hot/cold N* 손익분기 수식, VLM-QA 답변 연계 프롬프트 예시.

---

## 12. 미결·주의 사항 (PI 확인 대상)

1. **러닝 헤드**: p.7 이후 구제목 잔존 — 재제출/개정 시 수정 필요.
2. **RQ2 결론 갱신 주의**: 구 문서(740/760)의 "multi·dual 무익" 서술과 제출 논문 표4(다중 이미지 의미론 Δ+0.171 유의, 2.8배 비용)가 다름 — 구 문서를 인용한 후속 보고서 작성 시 반드시 표4 기준으로.
3. **qrels 계수 표기**: 감사 문서 6,810/24,873 vs 논문 정본 6,809/24,872 — 본 통합본은 논문 기준으로 통일했으나, 원천 parquet 재집계로 1건 차이의 출처(중복 제거 등) 확인 권장.
4. **UCA 질의 수 이력 3종**: 기대 ~122(Amd.6a) → 감사 135 → 논문 정본 **129**. 정본=129로 통일; 원천 확인 권장.
5. **810 DDL 차원 표기**: bge-m3 캡션 임베딩에 `vector(512)`는 오기(정본 1024d; 512d는 CLIP 프레임) — 청사진 재사용 시 수정.
6. **용어 치환 미적용**: 2026-07-28 확정 용어('벡터 데이터베이스 계층', '검색 문맥' 등)는 제출 PDF에 미적용 — 개정 원고에서 일괄 치환 필요.
7. **자산 정리 후보**: cityflow_nl·aihub_abnormal_cctv(미사용), VRU v1 결과트리 259M, intelligent 84M 미소비 산출물.
