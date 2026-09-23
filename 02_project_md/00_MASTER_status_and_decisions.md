# 00_MASTER — 연구 현황·결정 통합 정리본 (국문 단일 진입점)

최종 갱신: 2026-07-28

## 0. 머리말

이 문서는 KIISE DBR 2026 연구(비순환 멀티모달 RAG 평가·검색 품질-비용 실증)의 현황, LOCKED 주제, 핵심 결과, 불변 규칙, 결정 로그, 원고 버전 이력을 하나로 통합한 단일 진입점이다.

**통합 출처(원본은 아래 경로로 이관 예정):**

| 원본 문서 | 이관(아카이브) 경로 |
|---|---|
| 000_MASTER.md (연구 종합, ~07-17) | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/000_MASTER.md` |
| 010_OVERVIEW_EN.md (영문 개요, ~07-10) | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/010_OVERVIEW_EN.md` |
| 020_GLOSSARY_concepts.md (용어 사전) | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/020_GLOSSARY_concepts.md` |
| 650_MANUSCRIPT_v3_expansion_20260712.md (v3 확장 기록) | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/650_MANUSCRIPT_v3_expansion_20260712.md` |

**SYNC 기준: paper_final.pdf(2026-07-23) + 2026-07-28 검증 세션.**
모든 수치·해석은 제출 정본 `manuscript/paper_final.pdf`(2026-07-23 제출본, 총 21쪽 = 접수양식 1쪽 + 본문)를 절대 우선한다. 구 문서와 상충하는 서술은 논문 기준으로 정정하되, 의미 있는 이력은 "[정정 2026-07-28: …]" 형태로 남긴다.

---

# 제1부. 현행 정리

## 1. 연구 주제 (LOCKED — 축소·재프레이밍 금지)와 확정 제목

> **연구 주제(불변):** "Storage/Indexing/Retrieval Structures for Multimodal Urban Surveillance VLM-QA"
> 자연어 질의 + 메타데이터 조건이 함께 주어질 때, 어떤 저장·색인·검색 구조가
> VLM 기반 질의응답을 더 정확하게(accuracy)·빠르게(latency)·저비용으로(cost) 지원하는가?
> — 이미지/영상 + 사건 보고서 + 센서/시공간 메타데이터의 결합 (도시 감시 데이터)

- 3대 RQ 축: **RQ-S**(storage·indexing·retrieval 구조 비교) / **RQ-ALC**(정확도·지연·비용 3축 균형) / **RQ-M**(3-모달 결합 위 VLM-QA).
- 투고처: KIISE DBR (KCI). 선정 근거: `100_INTRO_topic_selection_rationale.md`.
- 최우선 원칙(PI 지시): **논문 집필보다 실험 체계 완성이 먼저**, 심사에서 무너지지 않는 설계.

**확정 논문 제목(paper_final, 2026-07-23 제출):**
- 국문: **"종단형 멀티모달 RAG 파이프라인 성능 향상을 위한 비순환 평가 및 검색 품질-비용에 대한 실증 연구"**
- 영문: *An Empirical Study of Non-circular Evaluation and Retrieval Quality-Cost for Enhancing the Performance of End-to-End Multimodal RAG Pipeline*

[정정 2026-07-28: 구 010_OVERVIEW_EN이 "열린 프레이밍 결정"(A=워크로드/벤치마크가 기여 vs B=가이드라인이 기여)을 미결로 남겼으나, 제출 정본 제목·구성에서 두 프레이밍이 결합 확정됨 — 비순환 평가(워크로드)를 방법적 축으로, 검색 품질-비용 실증(가이드라인)을 결과 축으로 병렬 제시.]

## 2. 제출 정본 요약 — paper_final.pdf (2026-07-23) 확정 수치

### 2.1 벡터 데이터베이스 계층의 다섯 설계 축 (§4.2)

1. **검색용 데이터**: 영상 설명문 / 대표 이미지 / 이미지·설명문 결합 / 다중 이미지(클립당 최대 3) / 설명문·이미지 이중 색인(RRF k=60)
2. **검색 계획**: 벡터 단독 / 검색 전 조건 / 검색 후 조건(상위 200 후보) / 혼합(영상 설명문 전용)
3. **검색 신호·순위 융합**: 메타데이터 단독 / BM25 / 벡터 / BM25-벡터 RRF
4. **물리 색인**: Flat / HNSW(M=32, efC=200, efSearch{64,256}) / IVF-Flat(nlist=64, nprobe{8,32}) / IVF-PQ(m=32, 6bit)
5. **배포**: 전역 / 조건별 부분 색인

**구성 산식**: 유효 데이터-계획 조합 1×4+4×3=16 × 색인 설정 7 = **112 구성**.

### 2.2 코퍼스 정본

**3,000 clips / 85 queries / strict qrels 6,809 / semantic qrels 24,872.**

[정정 2026-07-28: 구 010_OVERVIEW_EN의 "32 queries, strict 1,472 / semantic 9,062"는 07-10 시점 초기 빌드 수치로 폐기. 85질의 확장본이 정본이며, 650 감사 기록의 "semantic=strict의 72.6%↑" 검증도 6,809/24,872 기준으로 일치 확인됨.]

### 2.3 RQ별 확정 결과 (SYNC 절대 우선)

- **RQ1 (순환성 붕괴 실증)**: 수정 전후 0.9736→0.3174(VRU), 1.0000→0.8395(지능형 관제); 통제 주입 0.181→1.000(정답 필터)/0.854(라벨 재진술).
  - 보조 이력(붕괴 대조표에 함께 실린 값): 지능형 CCTV BM25 0.9600→0.1111(라벨 문자열 매칭 폭로), VRU B2 vector-only 0.4476→0.1845(strict)/0.2649(semantic). semantic 채점에서 B4−B2 부호가 음수인 질의가 존재(v1에서는 구조적으로 불가능) — 이 부호 반전이 A6 감사 항목으로 편입됨.
- **RQ2 (저장 표현, 표4)**: 설명문 0.063/0.181/1.15ms/24.6MB 기준; 다중 이미지 0.101/0.352(Δ+0.171 유의)/3.65ms/68.4MB(2.8배); 이중 색인 0.089/0.293/4.96ms/93.0MB(최고 비용); **저장 비교 전체 BH p=0.112**.
  - [정정 2026-07-28: 구 000_MASTER의 표현별 지연 수치(joint p95 1.57ms, multi 4.27ms, dual 5.66ms)는 사전 측정치로 폐기 — 정본 표4는 설명문 1.15ms / 다중 이미지 3.65ms / 이중 색인 4.96ms.]
  - 단일 image+caption joint(0.218)는 caption 0.181·frame 0.186보다 높은 점추정이나, 25개 군집 CI [-0.005,+0.074]로 보편 우위 미확증; matched−shuffled 대조 +0.022 CI [-0.093,+0.144]도 0 포함 → **정렬 인과 주장 금지** 유지.
- **RQ3 (검색 계획, 표5·6)**: 엄격 기준 검색 전 조건 Δ+0.0983 유의 — **단 '자명한 결과'로 해석**(필터가 정의상 이득인 설정); 의미론 기준 벡터 단독 0.170 최고, Δ=-0.0158 무의미; 고결합(V≥0.3) Δ+0.1335; UCA 129질의 재현 3/4.
  - [정정 2026-07-28: 구 010의 "strict +0.145 [0.082,0.216] / soft −0.075 [−0.133,−0.012]"는 32질의 초기 표본의 산물로 폐기(000_MASTER가 이미 "초저-V 편중 표본의 산물, 기계적 확장이 자기 교정"으로 진단). 결합도 연속곡선 서사(V<0.05 음수 ↔ V≥0.3 양수, 단조성)는 유지되나 정본 수치는 Δ=-0.0158(전체 무의미)·V≥0.3 Δ+0.1335다. 또한 strict 이득을 "헤드라인 발견"으로 승격했던 구 서술은 정본에서 '자명한 결과'로 해석 강등됨.]
- **RQ4 (검색 신호, §5.2.4)**: **전 신호 독립 이득 없음** — 메타 단독 0.218/0.217, BM25 0.017/0.050, 벡터 0.059/0.170, 혼합 RRF 0.133<벡터 0.154; 지식그래프 재조합 Lift 중앙값 0.002 무이득.
  - [정정 2026-07-28: 구 000_MASTER/010의 "B0 metadata-only 0.165 > B2 dense 0.064"는 32질의 시점 수치로 폐기 — 정본은 메타 단독 0.218/0.217, 벡터 0.059/0.170. "센서 메타데이터 단독이 희소 장면 사건에 강한 기준선"이라는 정성 결론 자체는 유지.]
- **RQ5 (물리 색인·배포, 표7-10)**: 실측 군집 조건에서 전역 색인 재현율 손실 최대 **0.627**(무작위 대조는 최대 0.047 변동 → **random-mask 방법론은 손실을 과소평가**); 조건별 부분 색인 **98.12~100% 회복**; 배포 규칙 = 전역 재현율 목표 0.95 미달 시 부분 색인/전수 검색 + 색인 갱신 시점까지 예상 질의 수의 선택도별 손익분기; Milvus/Weaviate는 필터율≥92.3% 또는 조건 만족 벡터<40,000이면 전수 검색 자동 전환.
  - 실험 이력(B-1, 620): 실제 상관 predicate가 공유색인 filtered-ANN을 붕괴시킴 — 동일-s 랜덤 대조군 대비 recall 과대평가 postfilter +0.611(A)/+0.289(B), single-stage +0.50/+0.12~0.22(전부 Holm-유의); prefilter 지역색인만 면역(0.98–1.00 @ 0.04ms); 메커니즘 = GT 군집 심도 ρ 0.62–0.895. pgvector에서도 부분복구 한계 재현(iterative_scan으로도 recall 0.30–0.66).
  - 색인 3축 이력(600): HNSW p50 0.04ms vs Flat 13.4ms@131K real; IVF-PQ 33× 압축; 522-visual 142K real로 복제(HNSW ef64 0.9992 @ 0.047ms vs Flat 14.2ms; IVF-PQ 22–35× 압축).
- **RQ6 (답변 전파, §5.2.6)**: 답변 정확도 **31%(무증거)→53%(무관)→67%(벡터 검색)→75%(대상 설명문)**; 잘 보이는 단일 시점 +15.2%p, 두 시점 동시 무이득(선택>축적); 근사 색인 재현율 차이의 답변 전파는 **표본 부족으로 탐색적(미확립)**.
  - [정정 2026-07-28: 구 000_MASTER의 "closed 0.31→oracle 0.75(2단)"·"better>worse +0.056~+0.152"는 정본에서 4단계 사다리(31→53→67→75%)와 "+15.2%p 단일 대표값"으로 정리됨. E-1 게이트 FAIL(26-config 사다리 전부 rel≈1.0, 1K-문서 RAG에선 색인 선택이 evidence 전달을 못 바꿈)은 "탐색적(미확립)" 판정의 실험적 배경으로 보존.]

### 2.4 국제 교차검증·외적타당성 arm (이력 보존)

- 해외 멀티모달 데이터셋 2차 조사(690·730): 100+ 후보 적대검증 → **제2의 깨끗한 tri-source는 없음(522 단독)**; 외적타당성 arm으로 **MEVA(WACV 2021)** 채택 + **MIRIS(SIGMOD 2020)** 추가.
- **MEVA 통합(700)**: 비순환 tri-source 재구축(A6 6/6 PASS, 985클립·193질의). 검색축 재현 = strict prefilter 이득 +0.093 [0.075, 0.113](CI 0 배제), 522의 +0.098과 근사; 캡션 dense 한계 재현; soft-intent는 null(정직). [정정 2026-07-28: 522 쪽 대응 수치의 정본 표기는 Δ+0.0983이며 '자명한 결과' 해석이 부가됨.]
- **MIRIS 교통**: 실제 카메라·차량수 predicate로 P2(부분 색인 vs 전역+WHERE) 재확증.
- UCA(640): 영어 이상행동, 정본 표기는 **129질의 재현 3/4**.

## 3. 연구 여정 (5막 요약 + 종결)

1. **주제·설계·데이터 확보** (07-06) — DBR 동향/공백 분석으로 주제 확정, canonical schema 설계, VRU + AI Hub 3종 확보.
2. **1차 실험: 텍스트·메타데이터 검색** (07-06~07) — B0–B5/pgvector 구축·측정. *(이후 순환성 판명 → 막5)*
3. **True-Multimodal 재설계** (07-07) — "텍스트 검색만으론 멀티모달이 아니다" 자기비판 → keyframe 시각 임베딩·M-계열·서비스 패킷·답변계층 구축, 원고 v1.
4. **다각도·확장** (07-08~09) — instance-VQA ill-posed 정정, 다각도 사전등록 실험(**선택>축적**, TOST·permutation·4-VLM), 색인 구조 벤치마크(Flat/IVF/HNSW/IVF-PQ, 132K real+1M).
5. **비판 심사 → 실험 체계 완성 → 제출** (07-09~23) — 10차원 심사(Major Revision, 검색 헤드라인 순환 F1–F4 확정), 마스터플랜(순환 해소=센서 결합=동일 작업), 실행(센서 materialization·동기 시각조인·비순환 워크로드·collapse 실증), Pillar B/E 사전등록, 설계공간 확장(112구성), 원고 v2→v3→v6→**paper_final(07-23) 제출**.

**현재 국면(2026-07-28)**: 제출 완료. 심사 대비 검증·수정 + 자산 디렉터리 13종 정비 완료(07-23, ASSETS_INDEX.md, 가드 37/37). 남은 작업 = S2-S4 보강실험, 신제목 확정 반영(910 문서), 2026-07-28 용어 결정의 향후 개정 원고 적용(제2부 결정 로그 참조).

## 4. 확정된 핵심 결과 (제출 정본 앵커 + 검증 이력)

**정본 앵커(§2.3의 RQ1–RQ6이 최종본).** 아래는 이를 뒷받침하는 검증 이력으로 보존한다.

- 522 tri-source 워크로드: 문서=VLM캡션(픽셀만) / predicate=센서CSV(카메라10) / relevance=사람주석(카메라11/22) — **소스 수준 분리**, A6 기계감사 6/6 PASS. 센서-시각 동기 조인 90.2%(±120s, 중앙값 0s). 독립성은 가정이 아닌 정량화: predicate×relevance 30쌍 중 25쌍 Cramér's V<0.3; 자연 결합쌍(러시아워×정체)은 폐기하지 않고 "결합도 연속곡선" 대조 arm으로 유지.
- 부수 발견: VLM 캡션의 체계적 맹점(주차 미서술 — "no parked vehicles" 실물 예시로 표 제시); 교차언어 sparse 실패 / 다국어 dense 생존(한국어 캡션에서 다국어 dense 0.82 vs BM25 0.17).
- 다각도 선택>축적: better>worse 유의, both≈better TOST 등가 — 사전등록·permutation·3~4 VLM 재현(Idefics2는 near-chance 0.145 보조 분리). 정본 대표값은 RQ6의 +15.2%p.
- 단일 image+caption joint(821): 동일 one-vector budget에서 semantic nDCG@10 0.218로 caption 0.181·frame 0.186보다 높은 점추정. multi 0.352·dual 0.293보다 낮으나 비용이 작다(정본 비용 수치는 §2.3 RQ2의 표4 값). matched–shuffled 음성 대조 비유의 → 정렬 인과 주장 보류.
- E-1 게이트 FAIL(420 Amd.2): 26-config 사다리 전부 rel≈1.0 — 1K-문서 RAG에선 색인 선택이 evidence 전달을 못 바꿈(정직 결과, 12–20 GPU-h 절약) → 정본 RQ6 "탐색적(미확립)" 판정의 근거.
- E-1/E-2 종결(630): 2-스케일 벽 실측(mediator 벽·perception 벽); retrieval 패널 front 12/46, 두 코퍼스 구조 동일.

**금지 유지**: v1 순환 수치(B0–B5 완벽지표 포함)는 §6 규칙 21 및 §7의 불변 조항 4에 따라 붕괴 진단 맥락에서만 인용.

## 5. 알려진 결함(비판 심사 F1–F10)과 해소 상태

| ID | 결함 | 상태 |
|---|---|---|
| F1/F2/F4 | 검색 헤드라인 순환(필터⊆정답, 라벨 재진술 문서, 템플릿 질의) | ✅ 해소 — 비순환 워크로드 3종 재측정 + collapse 대조표 → 정본 RQ1 |
| F3 | B2 대조군 억압(합성 접속 질의) | ✅ 해소(동일 재측정에 포함) |
| F5 | ForeSea/UrBench 미인용 | ✅ 해소 — v3 이후 원고 반영 |
| F6 | 색인 벤치마크 본문 부재 | ✅ 해소 — Pillar B 완결 → 정본 RQ5 |
| F7 | latency 철회·cost 미정량 | ✅ 해소 — 격리 latency·비용 CI(620) → 정본 표4·RQ5 |
| F8 | 센서/시공간 부재 | ✅ 해소 — 522 materialization + 동기 조인 |
| F9 | Recall 다수-positive 상한 | ✅ 설계 반영(희소 relevance + caveat 규칙) |
| F10 | 데이터/코드 공개 진술 부재 | ✅ 해소 — 원고 재작성 시 반영 |

## 6. 불변 제약·금지 표현 (28개 규칙 — 전량 보존, 요약 금지)

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

> **해제된 규칙(혼동 방지):** v1 투고 동결기의 "새 실험·새 데이터셋 투입 금지, 교차로신호체계는 후속 언급만"(19·27·31)은 심사 대응 국면 전환(41→42)으로 **공식 해제** — 교차로신호체계(522)는 센서·시공간 헤드라인 트랙이 되었고 제출 정본의 코퍼스 기반이다.

> **원고 불변 조항 4 명확화(650, 통합자 결정 — 유효 유지):** "v1 순환 수치는 **붕괴 진단 맥락(붕괴 표·그림·진단 서사)** 내부에서만 인용" — 순환성 진단 절에서 v1 수치를 진단 근거로 제시하는 것은 취지에 부합하며, 타 절에서의 결과 제시 금지는 유지된다.

## 7. 비순환 설계 원칙·사전등록 규율 (헤드라인 실험의 4대 관문 — 전량 보존)

모든 헤드라인 실험은 다음 4개 관문을 통과해야 한다(010에서 확립, 정본까지 유지).

1. **구성적 비순환(Non-circularity by construction)** — 필터 predicate·relevance 정의·검색 대상 문서가 **서로 다른 소스**(다른 카메라·다른 파일·다른 생산 주체)에서 나오며, 기계 감사(A6)로 강제: ①필터/relevance 키 disjoint ②정답 재진술 문서 0건 ③희소 relevance ④B4−B2 부호분포에 음수 존재.
2. **이중 정답(Dual ground truth)** — 모든 필터 검색 실험은 두 번 채점: *strict*(의미 일치 ∧ predicate 성립; prefilter가 정의상 이득인 고전 설정)와 *semantic-only*(predicate 무관 의미 일치; prefilter가 정당하게 해로울 수 있음). 둘 다 보고해야 비교가 정직하다.
3. **사전등록 + 적대적 설계 심사** — 설계는 실행 **전에** 작성·동결(예: Pillar B/E 사전등록), 독립 심사 렌즈(DB-시스템/통계/측정-정직성)의 공격 후 blocker 반영이 끝나야 실행 개시.
4. **정직성 게이트(Honesty gates)** — ANN/스케일 주장은 ≥100K 벡터 코퍼스에서만; 합성 증강은 라벨 분리·헤드라인 사용 금지; 단일 스레드 격리 latency는 "검색 계층 지표이며 end-to-end 서빙 latency가 아님" caveat 필수; 모든 헤드라인 비교에 부트스트랩 CI + 다중성 통제.

이 규율이 존재하는 구체적 이유: 내부 10차원 적대 심사에서 v1 원고의 검색 헤드라인이 **순환**임이 판명되었기 때문이다(메타데이터 필터가 정답 정의 facet의 부분집합 + 라벨 재진술 문서 → prefilter≥vector-only가 구조적으로 보장, MRR=nDCG=1.0000). 그 결함의 수리와 야심적 주제의 실현은 **같은 작업**이었다 — 진짜 외생적 센서 predicate가 정확히 순환성을 깨는 재료이기 때문이다.

## 8. 데이터셋 현황 (역할·정직 caveat 포함)

**확보 판정(최종): 신규 데이터셋 불필요** — 전 모달리티 디스크 실재, 남은 것은 가공·통합뿐이었고 이는 완료됨. 전 실험축 real_measured; 완전 tri-source는 522 단독(최대 caveat). 데이터셋 10 중 8 실사용(cityflow_nl·abnormal_cctv 일부 미사용, 740_AUDIT).

- **AI Hub 522 교차로신호체계** — 멀티모달 헤드라인 앵커. 32,880클립×63교차로 센서 CSV; TS_3/VS_3 사전 추출 JPG 143,830 프레임; CVAT XML 주석(TL_3 궤적/TL_4 박스); 산출물 sensor_facets·visual_sensor_join(90.2% ≤120s)·annotation_video_facets·captions(3,000 VLM 캡션, 소스 분리)·canonical_trisource. caveat: 평일·주간 녹화만; 악천후/시간대(TS_4/VS_4, 105,784 프레임)는 센서 조인 0% — 외생 predicate = 큐레이션 카테고리 + 파일명 시각.
- **VRU-Accident** — 답변계층 앵커 + 순환성 사례연구. 1,000 mp4 + dense captions + 6지선다 VQA; v1(순환) 보존 + 비순환 v2 재구축(감사 PASS). caveat: 대시캠성 교통안전 영상(고정 도시 CCTV 아님).
- **신내동 도시도로 CCTV** — 색인 스케일 코퍼스. 132,521 real CLIP 벡터(512-d) + 실측 시공간 메타데이터(39 지점·51 일자·18 시간대, 선택도 ~1e-4…0.18) + 분포 보존 1M 합성(항상 synthetic 라벨).
- **AI Hub 다각도 CCTV** — "선택>축적" 앵커. 4,500 이벤트×2시점; 400클립 bbox 비대칭 층화 사전등록 실험 완료.
- **AI Hub 지능형 CCTV(269) / 이상행동 CCTV(1,968)** — 스키마 이식성·한국어 외적타당성만(주장 금지 규칙 12 적용). 교차언어 발견(다국어 dense 0.82 vs BM25 0.17) 포함.
- **CityFlow-NL** — 보류(주석 canonical화만, main 수치 금지).
- **MEVA / MIRIS / UCA** — 국제 외적타당성 arm(§2.4).

## 9. English Overview (축약)

**Topic (locked):** Which storage, indexing, and retrieval structures best support VLM-based question answering — more accurately, faster, and at lower cost — when natural-language queries and metadata conditions are given together over multimodal urban-surveillance data (images/video + incident reports + sensor/spatiotemporal metadata)?

**Central instrument:** a non-circular, tri-source evaluation workload over real urban-surveillance video — documents (VLM captions from pixels only), predicates (sensor CSVs from a separate camera), and relevance (human annotations from other cameras) produced independently, enforced by the machine-checked A6 audit and scored with dual strict/semantic ground truth. [정정 2026-07-28: final corpus 3,000 clips / 85 queries / strict 6,809 / semantic 24,872 — the earlier 32-query build is obsolete.]

**Why "non-circular" is load-bearing:** the v1 workload defined queries, answers, filters, and even corpus documents from the same facet labels, structurally guaranteeing prefilter ≥ vector-only and perfect scores (MRR = nDCG = 1.0000). Repairing and re-measuring produced the collapse table (VRU B4 0.9736→0.3174; Intelligent-CCTV B4 1.0000→0.8395; BM25 0.9600→0.1111), which is now the RQ1 diagnostic of the submitted paper. A sign flip of B4−B2 under semantic scoring — impossible by construction in v1 — is the empirical proof and a standing audit assertion.

**Submitted paper (2026-07-23, paper_final.pdf):** *An Empirical Study of Non-circular Evaluation and Retrieval Quality-Cost for Enhancing the Performance of End-to-End Multimodal RAG Pipeline* — five design axes of the vector-database layer (retrieval data representation / search plan / signal & rank fusion / physical index / deployment), 112 configurations, six RQs. Headline outcomes: multi-image representation wins quality at 2.8× storage (RQ2); prefilter gains are significant only under strict scoring and are interpreted as self-evident (RQ3); no retrieval signal yields independent gains (RQ4); real correlated predicates collapse global-index recall by up to 0.627 while random masks move at most 0.047 — partial per-condition indexes recover 98.12–100% (RQ5); answer accuracy climbs 31→53→67→75% as retrieved context quality improves, with the index-approximation→answer link remaining exploratory (RQ6).

**Framing resolution:** the once-open choice between "the workload is the contribution" and "the guidelines are the contribution" was settled by combining both in the final title and structure — non-circular evaluation as method, quality-cost findings as results.

## 10. 용어 사전 (2026-07-28 용어 결정 반영)

### 10.1 확정 용어 체계 (2026-07-28 결정 — 보고서·향후 개정 원고용; 현 제출 PDF 미적용)

- **벡터 데이터베이스 계층**: 구 '데이터베이스 계층'의 확정 대체어. 검색용 데이터 표현·검색 계획·신호 융합·물리 색인·배포의 다섯 설계 축을 갖는 계층(§2.1).
- **'증거(evidence)' 전면 치환 체계**:
  - DB가 반환하는 것 = **상위 k 검색 결과**
  - VLM 입력으로 주어지는 것 = **검색 문맥(retrieved context)**
  - 정답 판정 대상 = **관련 클립 / 검색 정답 집합**
  - RQ6의 3관문 = **관련 클립 회수 → 검색 문맥 인식 → 과제 편향**
- **클립(조작적 정의)**: 데이터셋 배포 mp4 1파일 = 1클립. MEVA[20] 계보로 방어한다. 유의: TTA 사전에 미등재이며 AI Hub 공식 페이지는 '영상(mp4)'으로 표기한다.

### 10.2 기본 개념 용어 (020 유래, 보존)

- **VQA (Visual Question Answering, 시각 질의응답)**: 이미지·비디오 같은 시각 입력과 자연어 질문이 주어졌을 때 시각 정보를 분석해 자연어 답변을 도출하는 기술. 본 연구 맥락: "교차로에서 흰색 차량이 언제 급정거했는가?", "우회전 차량과 보행자 간 충돌 위험이 있었는가?" 같은 구체 질문에 시스템이 영상을 분석해 답하는 기능.
- **CoT (Chain of Thought)**: LLM/VLM이 최종 정답만이 아니라 정답에 이르는 논리적 사고 과정·중간 추론 단계를 단계별로 생성하도록 유도하는 기법. 본 연구 맥락: 교통사고 데이터에서 "1. A 차량의 무리한 차선 변경 → 2. 후방 B 차량 급제동 → 3. 뒤따르던 C 차량 추돌"처럼 사건 인과를 단계별로 기술·추론해 둔 데이터 구조.
- **VLM (Vision-Language Model)**: 시각 정보와 언어 정보를 동시에 이해·연계 처리하는 모델. 본 연구의 VLM-DB는 VLM의 멀티모달 이해 능력과 전통 DB의 대규모 저장·색인·검색 기능을 결합한 시스템 개념.
- **이질적 모달리티(Heterogeneous Modality)**: 형태·구조·성격이 다른 데이터들이 혼재하는 상태. 본 연구 맥락: CCTV 영상(비디오), 교통·기상 정보(수치/로그 메타데이터), 지도(공간 정보), 민원·상황일지(정형/비정형 텍스트)가 한 시스템에서 융합되어야 함.
- **Multimodal Retrieval**: 서로 다른 형태의 질의와 대상을 매칭하는 교차 검색 기술. 본 연구 맥락: "어제 오후 비 오는 날 발생한 킥보드 사고 영상"(텍스트 질의)에 기상 데이터·민원 일지를 참조해 정확한 CCTV 클립(비디오 결과)을 찾는 시스템.
- **Event Grounding**: 비디오에서 특정 사건의 정확한 시간 구간·공간 위치를 찾아 언어 설명과 시각 대상을 연결하는 기술. 본 연구 맥락: 장시간 CCTV에서 "무단횡단"·"차량 접촉 사고"가 발생한 정확한 구간을 식별·타임라인 매핑.

### 10.3 연구 내부 용어 (통합 시 추가)

- **tri-source(3-소스 분리)**: 문서·predicate·relevance가 서로 다른 생산 주체에서 나온 워크로드 구성(§7 관문 1).
- **A6 감사**: 비순환성 기계 감사 4항목(키 disjoint / 정답 재진술 0건 / 희소 relevance / B4−B2 부호 음수 존재).
- **strict / semantic qrels**: 이중 정답 체계(§7 관문 2). 정본 규모는 6,809 / 24,872.
- **결합도(Cramér's V)**: predicate와 relevance의 통계적 결합 강도. 고결합(V≥0.3)에서만 검색 전 조건의 의미론 이득이 관측됨(RQ3).
- **RRF (Reciprocal Rank Fusion)**: 순위 융합 기법, 본 연구 고정 k=60(이중 색인·혼합 신호에 사용).
- **검색 전/후 조건(pre/post-filter)**: 벡터 검색 전에 조건을 적용(부분 후보군)하거나 검색 후 상위 200 후보에 조건을 적용하는 검색 계획.
- **부분 색인(partial index) / 전역 색인(global index)**: 조건별로 분리 구축한 색인 vs 전체 단일 색인(RQ5 배포 축).

## 11. 원고 버전 이력

| 버전 | 시점 | 내용 | 상태 |
|---|---|---|---|
| v1 | 07-07 | true-multimodal 초판 — 검색 헤드라인이 순환(F1–F4)으로 판명 | 폐기(붕괴 진단 소재로만 인용) |
| v2 | 07-12 | 비순환 재작성 + 그림 3종 + DBR 변환(docx/PDF 9쪽) + codex 교차 검증 반영 | v3로 대체 |
| **v3** | **07-12** | **11쪽→20쪽 종합 확장(650)**. 정본 `manuscript/kiise_dbr_manuscript_v3.md`, DBR 제출본 A4 20쪽(≤20 충족). 검증 스위트 40/40 + F5 검증기 141/141(원 127 + 구조/감사 가드 14). 다중 에이전트 교차검증(비평 3 → 작성 6(W1–W6) → 감사 12; Fable 한도 실패 10건은 Opus 전환 resume으로 완료). 신규 시각 자료: 표1 VALU 차별성 / 표3 3채널 실물예시("no parked vehicles" 맹점 실체화) / 표4 데이터셋 요약 / 표6 UCA 판정 / 표10 색인3축 / 표11 사다리 / 표13 가이드라인(지위 열); 표5(계산비용)는 20쪽 맞춤 위해 산문화. 그림2 붕괴 / 그림4 UCA 산점(Cramér's V) / 그림5 M9 짝지은 산점. 참고문헌 [1]–[31], IEEE first-appearance 재번호. 적대 감사에서 qrels 6,809/24,872·85q semantic mean −0.0158 등 신규 수치 전건 디스크 재검증; 확증(Holm 가족 한정)/탐색적 분류 수정; 불변 조항 4 명확화 | v6로 대체 |
| v6 | 07-17 | 심사용 제출원고 갱신 — A4 15쪽, 2단, 표 15개·그림 6개, 단일 joint 포함 112구성 반영(821), DOCX/PDF 투고양식 검증 80항목 PASS. 잔여였던 저자 metadata 2건(ForeSea 저자, 공저자 직위·이메일)은 제출 과정에서 처리 | paper_final로 대체 |
| **paper_final** | **07-23** | **제출 정본** `manuscript/paper_final.pdf` — 총 21쪽(접수양식 1쪽 + 본문). 확정 제목(§1), 5설계축·112구성·RQ1–RQ6(§2). 본 문서의 모든 수치 SYNC 기준 | **현행 정본** |

[정정 2026-07-28: 구 000_MASTER의 "최신 원고 = v6(07-17)" 서술은 paper_final(07-23) 제출로 대체됨.]

## 12. 핵심 경로

| 무엇 | 어디 |
|---|---|
| **제출 정본** | `manuscript/paper_final.pdf` (2026-07-23) |
| 직전 심사용 원고 | `manuscript/kiise_dbr_manuscript_v6_submission_revision.{md,docx,pdf}` |
| v3 정본·DBR 변환 | `manuscript/kiise_dbr_manuscript_v3.md`, `..._v3_DBR_review.{md,docx,pdf}` |
| collapse·유의성 asset | `paper_assets/20260710_noncircular_collapse/` |
| codex 교차 검증 | `paper_assets/codex_crosscheck_20260712/RESPONSE.md` |
| 522 데이터 | `Datasets/processed/aihub_522_intersection/20260710/` (sensor_facets, visual_sensor_join, annotation_*, canonical_trisource, frames_src, captions) |
| 색인 벤치마크 | `Datasets/processed/sinnaedoro_traffic/{index_benchmark,filtered_ann,corpus_real}/` |
| 실행 환경 | `Datasets/envs/kiise-vlmdb/bin/python` (torch 2.12/cu130, tf 5.13, faiss 1.14.3, py7zr) |
| 생성모델 | `/hdd2/huggingface_cache/hub/` (Qwen2.5-VL·Qwen2-VL·InternVL3·Idefics2·Qwen2.5-7B·Llama-3-8B) |
| 발표덱 | `presentations/kiise_vlmdb_deck_20260714.pptx` + `SLIDE_SPEC_for_external_agent_20260714.md` |
| 자산 디렉터리 인덱스 | `ASSETS_INDEX.md` (07-23, 13종, 가드 37/37) |

---

# 제2부. 결정 로그

## 2026-07-28 용어 결정 (3건) — 현 제출 PDF 미적용, 보고서·향후 개정 원고에 적용

| # | 결정 | 내용 |
|---|---|---|
| D1 | '데이터베이스 계층' → **'벡터 데이터베이스 계층'** | 다섯 설계 축을 갖는 계층의 공식 명칭을 벡터 데이터베이스 계층으로 확정. |
| D2 | **'증거' 전면 치환** | DB 반환 = 상위 k 검색 결과; VLM 입력 = 검색 문맥(retrieved context); 정답 판정 = 관련 클립/검색 정답 집합. RQ6 3관문 = '관련 클립 회수 → 검색 문맥 인식 → 과제 편향'. |
| D3 | **클립 조작적 정의** | 데이터셋 배포 mp4 1파일 = 1클립. MEVA[20] 계보로 방어. 유의: TTA 사전 미등재, AI Hub 공식 페이지는 '영상(mp4)' 표기. |

## 알려진 원고 이슈 (재제출/개정 시 처리)

- **러닝 헤드**: paper_final p.7 이후에 구제목이 잔존 — 재제출/개정 시 확정 제목으로 수정 필요.
- 2026-07-28 용어 결정(D1–D3)은 현 제출 PDF에 미적용 상태 — 개정 원고에서 일괄 반영.

## 과거 결정 (이력 보존)

- 프레이밍 A/B 병합 확정(제출 정본 제목·구성으로 종결, §1).
- v1 동결기 규칙(새 실험·새 데이터셋 금지) 공식 해제(§6 말미).
- 불변 조항 4 명확화(v1 순환 수치는 붕괴 진단 맥락 내부에서만 인용, §6 말미).
- E-1 게이트 FAIL 시 착수 금지(Amd.2) — 발동·종결됨(§4).
- (구 000_MASTER 미결) 740·750·760 문서 번호 충돌(각 2개 파일: AUDIT/RAG_baseline/RESEARCH_FLOW vs RELATED_reinforcement/UNIFIED_EMBEDDING/RESEARCH_FLOW_systematic) — 내용 상보, 번호 정리 사용자 대기.

---

# 제3부. 출처별 고유 내용 색인

### 000_MASTER.md
아카이브: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/000_MASTER.md`
이 파일에만 있던 핵심 내용:
- 불변 제약·금지 표현 28개 규칙 전문(§6에 전량 흡수)과 해제된 규칙 주석.
- 연구 여정 5막 요약, F1–F10 결함·해소표, 활성 문서 지도(000–821)·핵심 경로 표.
- 2026-07-13~17 확장 종합: 해외 데이터셋 2차 조사("제2의 깨끗한 tri-source 없음"), MEVA(+0.093 CI)·MIRIS·UCA arm, P1/P2/P3 DB 설계공간 결과, B-1 filtered-ANN 붕괴 수치(+0.611/+0.289 Holm-유의), E-1 게이트 FAIL, 821 joint 단일벡터 결과(0.218, CI 0 포함)와 112구성·19,040 metric cells·95,200 latency trials.
- 740/750/760 번호 충돌 미결 메모, 표준 RAG baseline 확립(750) 및 비교 계약, 발표덱 경로.
- (정정 대상이었던 것) v6=최신 원고 서술, joint/multi/dual 지연 사전 측정치, B0 0.165/B2 0.064 등 32질의 시점 수치.

### 010_OVERVIEW_EN.md
아카이브: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/010_OVERVIEW_EN.md`
이 파일에만 있던 핵심 내용:
- 영문 주제 선언문·중심 연구도구(instrument) 문장, RQ-S/RQ-ALC/RQ-M 영문 정의표.
- 헤드라인 실험 4대 관문(비순환 구성·이중 정답·사전등록+적대 심사·정직성 게이트)의 체계적 서술(§7에 전량 흡수).
- "Open framing decision"(A 워크로드 기여 vs B 가이드라인 기여)과 결정 규칙 — 정본 제목으로 병합 종결됨을 결정 로그에 기록.
- 순환성 붕괴 상세 대조표(VRU B2 0.4476→0.1845/0.2649, BM25 0.9600→0.1111 포함)와 "semantic에서 B4−B2 음수 = 구조 보장 붕괴의 실증" 논리.
- tri-source 채널 표(문서/predicate/relevance 소스·역할), 동기 조인 90.2%·중앙값 0s, Cramér's V 25/30 정량 독립성, 데이터셋별 상태·목적·방법·caveat 상세(522 원자료 검증 내역, TS_1/TS_2 비공개 placeholder, 143,830 프레임 등).
- (정정 대상이었던 것) 32질의·qrels 1,472/9,062, +0.145/−0.075 CI 초기 수치.

### 020_GLOSSARY_concepts.md
아카이브: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/020_GLOSSARY_concepts.md`
이 파일에만 있던 핵심 내용:
- 기본 개념 용어 6종(VQA·CoT·VLM·이질적 모달리티·Multimodal Retrieval·Event Grounding)의 개념 정의와 본문 맥락 예시(§10.2에 전량 흡수; §10.1의 2026-07-28 확정 용어 체계·§10.3 연구 내부 용어는 통합 시 신규 추가).

### 650_MANUSCRIPT_v3_expansion_20260712.md
아카이브: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/650_MANUSCRIPT_v3_expansion_20260712.md`
이 파일에만 있던 핵심 내용:
- v3 확장(11→20쪽) 제작 방식: 청사진(불변 조항 7 + 삭감 우선순위) → 다중 에이전트 워크플로우(비평 3·작성 6·감사 12, Opus resume), 초안 보존 경로(`manuscript/v3_working/named/`), 통합 스크립트 2종(stage1 앵커/표·그림 토큰, stage2 IEEE 참고문헌 재번호).
- 신규 표·그림 목록(표1·3·4·6·10·11·13, 그림2·4·5)과 표5 산문화 결정.
- 적대 감사 반영 내역: qrels 6,809/24,872(정본과 일치하는 최초 기록), 85q semantic 부호 26/30/29·mean −0.0158, v1 진단 수치 실측 재검증, 확증/탐색 분류 수정, 독립성 격자 30 vs 질의 25 구분, 손익분기 per-predicate 문구, Idefics2 보조 분리, 불변 조항 4 명확화(§6 말미에 흡수).
- F5 검증기 `verify_manuscript_v3.py` 141/141, 당시 잔여 사람 작업(ForeSea 저자·공저자 정보) 기록.
