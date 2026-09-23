# 900 — ECIR 2027 Introduction 정리·관리 정본 (Reframing Layer)

작성일: 2026-07-16
상태: **ACTIVE — ECIR 2027 투고본의 Introduction 개념·서사·근거를 이 문서에서 관리한다.**

- 이 문서는 KIISE DBR용으로 확정된 [`000_Introduction.md`](000_Introduction.md)(개념 canonical)를
  **삭제·대체하지 않는다.** 대신 그 연구를 **ECIR 2027(IR 학회, 영문 LNCS ≤12pp, 익명 심사)** 로
  **재정렬(reframe)** 하기 위한 상위 관리 레이어다.
- **방화벽:** `000_Introduction.md`·`000_MASTER.md`는 KIISE 트리의 소스·정본으로 그대로 둔다. 본 문서는
  같은 substrate 위에서 **강조점(emphasis)과 서사(narrative)만 IR 관점으로 재배치**한다. 새 실험·새 수치를
  만들지 않으며, 수치는 결과 정본(600/620/630/660/700/720 등)을 그대로 인용한다.
- **핵심 원칙 한 줄:** *KIISE = "어떤 DB 구조가 이기는가"(systems 설계공간). ECIR = "멀티모달 감시 검색을
  신뢰할 수 있게 평가하려면 무엇이 선행되어야 하며, 실측 predicate는 검색 결론을 어떻게 바꾸는가"(retrieval +
  evaluation validity).* 같은 실험, 다른 척추.

---

## 0. 이 문서의 역할과 갱신 정책

| 구분 | KIISE 정본 (`000_Introduction.md`) | 본 ECIR 레이어 (`900_...`) |
|---|---|---|
| 투고처 | KIISE DBR (KCI, 국문 HWP, ≤20pp) | ECIR 2027 (LNCS, 영문 ≤12pp, 익명) |
| 1순위 기여 | DB 저장·색인·배치 설계공간(RQ-S/ALC/M) | 비순환 평가 프로토콜 + 순환성 붕괴 사례연구 |
| DB backend·pgvector·hot/cold | 헤드라인 | **downstream 함의(2차)로 강등** |
| filtered-ANN matched control | 기여 3 | **헤드라인 retrieval 발견으로 승격** |
| 어휘 | 저장 단위·질의 계획·구축 비용 | recall/nDCG·filtered retrieval·evidence layer·construct/workload validity |

- Motivation·Gap·RQ·Contribution의 **개념**은 여전히 `000_Introduction.md` §6이 근거. 본 문서는 그 개념을
  ECIR 서사 순서로 재배열하고, 학회 포지셔닝·영문 골격·가드레일을 추가한다.
- 실험 수치가 바뀌면 결과 정본 → `000_Introduction.md` → 본 문서 순으로 갱신한다.

---

## 1. 한 문장 핵심 (ECIR 재프레이밍)

> **대규모 도시 감시 영상을 질의마다 VLM에 통째로 넣을 수 없으므로 DB가 소수의 증거를 선별하는
> evidence layer가 반드시 선행되어야 한다. 그런데 이 검색 계층을 "무엇이 더 잘 검색하는가"로 비교하려면,
> 필터·문서·정답이 같은 주석 계보를 공유하지 않는 비순환(non-circular) 워크로드가 먼저 성립해야 한다.
> 본 연구는 predicate(외생 센서)·document(픽셀-only VLM 캡션)·relevance(독립 인간 주석)를 소스 수준에서
> 분리한 tri-source 프로토콜과 기계 감사를 세우고, 그 위에서 실측 상관 predicate가 필터드 검색 결론을
> 어떻게 바꾸는지(그리고 언제 최종 VLM 답변으로 전파되는지)를 실증한다.**

### 1.1 ECIR 척추(spine) — 2층 구조

1. **평가 타당성 층 (validity-first, ECIR 심장):** 멀티모달 감시 검색 벤치마크는 순환하기 쉽다.
   필터·검색문서·정답이 한 주석에서 파생되면, 어떤 구조의 "우위"는 검색 품질이 아니라 **라벨의 자기참조**를
   측정한 것일 수 있다. 우리는 이 순환을 **재현·붕괴(collapse)로 실증**하고, 이를 차단하는 tri-source
   분리 + 기계 감사(A6)를 제시한다.
2. **검색 방법론 층 (retrieval finding):** 타당한 워크로드 위에서, **실제 도시 센서 predicate**는 검색을
   난수 마스크(random-mask) 벤치마크가 예측하는 것과 **다르게** 만든다. 동일 선택도 matched random 대조군
   대비 공유 색인 filtered-ANN의 recall이 과대평가되며, prefilter 지역색인만 이에 면역이다. 그리고 이
   검색 차이가 고정 VLM 답변으로 **전파되는/막히는 경계**를 규명한다.

> 저장 단위·색인 계열·pgvector 배치·구축 비용은 **버리지 않되**, 위 두 층의 **downstream 함의**로 둔다.
> (LLM-judge 논문이 factor-impact·routing을 "2차"로 둔 것과 같은 전략.)

---

## 2. 왜 이 연구가 반드시 이루어져야 하는가 (Necessity / 당위성)

세 개의 독립적 필연성 기둥이 서로를 보강한다. Introduction은 이 순서로 긴장을 쌓는다.

### 2.1 운영적 필연성 — evidence layer는 선택이 아니라 강제다
- 도시 감시 환경은 다수 카메라의 고화질 영상을 장기 축적한다. 질의마다 전체 아카이브를 VLM에 입력하는 것은
  입력 길이·GPU 연산·지연·추론 비용상 **불가능**하다.
- 따라서 질의 서비스와 최종 VLM 사이에 **DB evidence layer**(오프라인 물질화된 프레임 벡터 + 픽셀-only
  캡션 + 센서·시공간 메타데이터에서 소수 증거를 검색해 evidence packet으로 구성)가 **반드시** 끼어든다.
- 그런데 이 계층의 물리 설계(저장 단위·필터 결합·색인)는 **미결정**이다. "가장 좋은 임베딩 모델"만 골라서는
  운영 구조가 결정되지 않는다. → **연구할 대상이 실재한다.**

### 2.2 방법론적 필연성 — 순환 워크로드는 결론을 위조한다 (ECIR 최강 훅)
- 멀티모달 감시 검색에서 필터(predicate)·검색문서(document)·정답(relevance)이 **같은 인간 주석에서 파생**되면:
  - prefilter가 정답을 절대 제거하지 못하도록 구성되고,
  - 검색 문서가 정답 라벨을 재진술해 특정 전략의 우위가 **사실상 미리 결정**된다.
- 이는 가설이 아니다. **우리 자신의 초기 워크로드에서 코드 수준 순환을 진단**했고, 비순환으로 수리하자
  완벽 지표가 **붕괴**했다(§8 앵커: VRU nDCG 0.9736→0.3174, AIHub BM25 0.9600→0.1111 — 라벨 문자열
  매칭 폭로). → **잘못된 평가 위에서 얻은 어떤 DB 결론도 무효**임을 우리가 몸소 보였다.
- ECIR 정합성: ECIR 2025~2026은 relevance-scale 효과, LLM-judge bias, chunking reliability, RAG
  answer-quality 등 **"평가 도구·워크로드의 타당성"** 계열을 적극 채택한다. 비순환 멀티모달 검색 워크로드
  구성은 바로 이 계보에 속하며, **video/surveillance 도메인에서는 아직 정식화되지 않았다.**

### 2.3 경험적 필연성 — 실측 predicate는 벤치마크 통념을 깬다
- 타당한 워크로드가 있어도, 검색 결론은 **predicate의 실제 성질**에 좌우된다.
  - **hard constraint**(예: 신호·시간): strict prefilter가 유의 이득(+0.098 [0.068,0.133], MEVA +0.093로 복제).
  - **soft intent**: 부호가 **결합도(coupling) 연속곡선**을 따른다(V<0.05 −0.099 ↔ V≥0.3 +0.134,
    Spearman ρ=0.285 단조). 즉 "prefilter가 항상 좋다"는 통념은 틀렸다.
  - 실증 근거: semantic positive의 **72.6%가 센서 메타데이터 필터를 통과하지 못한다** → soft-intent에서
    hard prefilter는 의미상 중요한 증거를 사전 누락시킨다.
- **filtered-ANN**: 동일 선택도 matched random 대조군은 공유 색인 검색을 **과대평가**한다(postfilter
  +0.611/+0.289, single-stage +0.50/+0.12~0.22 recall 과대, Holm-유의). 기전 = GT 군집 심도(ρ 0.62–0.895).
  prefilter 지역색인만 면역(0.98–1.00 @0.04ms). → **"난수 마스크로 평가하면 filtered-ANN을 과대평가한다"**
  는, ACORN/Filtered-DiskANN 계보를 **실측 도시 센서**로 확장하는 IR 발견.
- **전파 경계**: 검색 차이가 답변으로 무조건 전파되지 않는다. 고정 VLM에서 evidence 품질만 바꾸면
  closed 0.31 → oracle 0.75로 크게 움직이지만(전파 가능성은 실재), 1K-문서 RAG에선 색인 선택이 evidence
  전달을 못 바꾸는 등 **세 경계(mediator 벽·perception 벽·VLM 답변-편향)** 가 존재. → 검색 이득을
  end-to-end로 과대 해석하지 않는 **정직한 경계 규명**이 필요.

### 2.4 왜 지금(Why now) · 왜 ECIR(Why here)
- **왜 지금:** RAG가 IR 평가 대상을 "랭킹된 문서"에서 "생성된 답변"으로 옮겼고, video/surveillance
  VLM-QA(ForeSea 등)가 검색 파이프라인을 포함하기 시작했다. 멀티모달 evidence 검색의 **평가 타당성**을
  지금 못 세우면, 이후 모든 감시 VLM-QA 비교가 순환 위에 쌓인다.
- **왜 ECIR:** 이 연구의 힘은 DB 백엔드 벤치마크가 아니라 **retrieval 방법론 + 평가 타당성**에 있다. ECIR는
  filtered/multi-vector retrieval(HNSW Hubs, Multivector Reranking), chunking reliability,
  LLM-judgment bias, RAG utility를 채택하는 IR 학회 → **주제 적합도가 KIISE의 DB-systems 프레임보다 오히려
  이 척추에 더 맞는다.**

---

## 3. 무엇을 주장하는가 — ECIR용 Contributions (재배열·과장 제거)

`000_Introduction.md` §7의 5개 기여를 **ECIR 순서로 재배치**한다(핵심을 먼저).

| # | 기여 (ECIR 강조 순서) | 근거 정본 | 성격 |
|---|---|---|---|
| **C1** | **비순환 tri-source 평가 프로토콜** — predicate/document/relevance의 생성 계보 분리, strict·semantic 이중 qrels, 기계 감사(A6 6/6 PASS). | 500, `000_Introduction.md` §7-1 | 평가 방법론 (헤드라인) |
| **C2** | **순환성 사례연구** — 초기 워크로드의 코드 수준 순환 진단 + 수리 전후 성능 붕괴 재현으로 구조 비교가 무효화되는 기전 제시. | paper_assets/20260710_noncircular_collapse, 300(F1–F4) | 평가 방법론 (헤드라인) |
| **C3** | **실측 predicate 필터드 검색 발견** — 실제 센서·시공간 predicate와 동일 선택도 random mask를 짝지어 공유 색인 filtered-ANN 과대평가를 정량화, 관계형·전용 엔진 교차 확인. | 620 | retrieval 발견 (헤드라인) |
| **C4** | **DB 설계공간 함의(2차)** — 저장 단위·필터 계획·ANN 색인·pgvector global/partial를 정확도·검색 지연·색인 크기·구축 비용 위에서 비교, 조건별 선택 지침·hot/cold 손익분기(N*). | 600, 720 | systems 함의 (downstream) |
| **C5** | **답변 전파 경계** — 검색·색인 차이가 고정 VLM 답변으로 전파되는/막히는 세 경계를 정직하게 보고(과대 해석 차단). | 630, 660 | generative IR (경계) |
| **C6** | **재현 자원 공개** — 비순환 멀티모달 감시 검색 워크로드 + 감사 절차 + 결과를 감사 가능한 형태로 공개. | artifact 계열 | 자원 |

- **금지 표현(유지):** "최초", "완전한 독립", "전무", "모든 데이터셋에서 우월". C3은 "기존이 clustering을
  몰랐다"가 아니라 **"실측 도시 센서 matched control + VLM evidence layer의 통합 평가"** 로만 주장.

---

## 4. 어떻게 목적을 달성하는가 (Method → Objective 매핑)

각 필연성(§2)과 기여(§3)를, **이미 확보된 근거**로 어떻게 닫는지의 지도.

| 달성 목표 | 방법 (수단) | 산출 근거 | 상태 |
|---|---|---|---|
| 워크로드 타당성 확보 (§2.2 → C1) | tri-source 소스 격리 + A6 기계 감사(키 disjoint / 정답 재진술 문서 0건 / 희소 relevance / B4−B2 음수 분포) | 522 3,000 corpus·85q, A6 6/6 PASS | ✅ 완료 |
| 순환이 결론을 위조함을 증명 (§2.2 → C2) | 순환 v1 → 비순환 v2 재측정, collapse 대조표 | VRU/AIHub collapse asset | ✅ 완료 |
| 실측 predicate 발견 (§2.3 → C3) | 실 센서 predicate vs 동일 선택도 random mask 대조 + Faiss/pgvector/전용 엔진 교차 확인 | 620 (2-코퍼스 + pgvector B-3) | ✅ 완료 |
| 설계공간 절충 (§2.1 → C4) | 격리 latency(생성 제외) + 색인 그리드(Flat/IVF/HNSW/IVF-PQ) + global/partial + N* 손익분기 | 600, 720 | ✅ 완료 |
| 전파 경계 (§2.3 → C5) | 고정 VLM·greedy, evidence 품질만 조작(closed→oracle 사다리), 스케일 2점, E-1 게이트 | 630, 660 | ✅ 완료(경계=긍정 결과) |
| 외적 타당성 사다리 | 522(flagship tri-source) → MEVA(해외, +0.093 복제) → UCA(2.5채널) → VRU/지능형/다각도(보조) | 500/640/700 | ✅ 8종 실사용 |

- **핵심 방법론 태도:** "하나의 보편 우승 구조" 선언이 아니라 **predicate 선택도·결합도·질의 빈도·캡션-질의
  정합에 따른 regime-specific 지침**을 목적으로 삼는다. → 붕괴·null·경계도 **은폐 없이** 결과로 보고.

---

## 5. ECIR용 Introduction 골격 (Beat Structure, ≤12pp LNCS 영문)

각 beat = 1~2문단. 괄호 = 앵커 근거/그림.

1. **B1 — 문제 전환:** 도시 감시는 영상+센서를 함께 생산하고, 사용자는 "오전에 자전거 2대 이상 보이는
   교차로"처럼 의미+구조 조건이 결합된 질의를 던진다. 질의마다 전체 영상을 VLM에 넣는 것은 비현실적 → DB
   evidence layer가 필수. (§2.1)
2. **B2 — 진짜 병목:** 답변 품질·비용은 모델만으로 결정되지 않는다. 저장 단위·필터 결합·색인 배치가 recall·
   지연·저장·구축 비용을 바꾼다. → "임베딩 모델 선택 문제"가 아니라 **evidence layer 설계·질의 계획 문제**.
3. **B3 — 그러나 먼저 타당성:** 이 설계공간 비교는 워크로드가 비순환일 때만 의미가 있다. 필터·문서·정답이
   한 계보면 우위가 미리 결정된다. **(핵심 전환점)** (§2.2)
4. **B4 — 우리가 본 붕괴:** 우리 초기 워크로드가 실제로 순환했고, 비순환 수리 시 완벽 지표가 붕괴했다.
   (Fig: collapse 대조; §8 앵커)
5. **B5 — 관련 연구 좌표:** 비디오 DB(NoScope/BlazeIt/Spatialyze/EQUI-VOCAL/VIVA), 필터드 ANNS
   (Filtered-DiskANN/ACORN/UNIFY/VBASE), 감시 VLM/VideoRAG(UCA·VALU/HAWK/ForeSea) 각각을 정확히 인정한 뒤,
   **세 축을 하나의 비순환 도시 감시 VLM-QA 워크로드로 통합한 평가가 드묾**을 공백으로 특정. (§6, "최초" 금지)
6. **B6 — 접근:** tri-source 프로토콜 + 기계 감사 → 그 위에서 실측 predicate vs matched random,
   저장·색인·배치, 답변 전파를 고정 모델·동일 qrels로 비교.
7. **B7 — 주요 결과 미리보기:** 실측 predicate가 filtered-ANN 결론을 바꿈(random-mask 과대평가), soft-intent
   결합도 곡선, 전파 세 경계. (Fig: filtered-ANN matched control; 결합도 곡선)
8. **B8 — 기여 목록 + 범위 선언:** §3의 C1–C6. 마지막에 "단일 보편 우승보다 regime-specific 지침 / latency는
   검색 계층 격리 측정 / matched control 정직성" 범위 문장.

> **RQ 배치:** `000_Introduction.md` §5처럼 **비순환성을 별도 RQ가 아니라 모든 RQ에 선행하는 validity
> prerequisite**로 두고, RQ-S(구조)/RQ-ALC(정확도·지연·비용)/RQ-M(멀티모달 결합·답변 전파) 3축 유지.
> ECIR 버전에서는 RQ 리드에 **validity prerequisite를 명시적으로 전면 배치**한다.

---

## 6. 학회 포지셔닝 & Related Work 좌표 (ECIR)

ECIR가 최근 채택한 인접 계열과, 우리의 상보적 주장:

| ECIR/IR 계열 | 대표 | 그들이 다루는 것 | 우리의 상보적 공백 |
|---|---|---|---|
| 필터드/멀티벡터 retrieval | Filtered-DiskANN, ACORN, UNIFY, VBASE; ECIR26 HNSW-Hubs·Multivector Reranking | 자연 라벨·predicate clustering·query correlation·색인 효율 | 실측 도시 센서 matched control + VLM evidence layer 통합 평가 |
| 비디오 DB/분석 | NoScope, BlazeIt, Spatialyze, EQUI-VOCAL, VIVA | 객체·시공간 이벤트 질의, 분석 비용 | 자유형 자연어 의미 + 외생 센서 predicate + evidence packet 물리 설계 통제 비교 |
| 감시 VLM / VideoRAG | UCA·VALU, HAWK, ForeSea | 모델의 이해·이상행동 설명·temporal grounding·(ForeSea) retrieval 파이프라인 | 저장 입도·색인 계열·필터 배치·검색 지연·구축 비용의 **통제 변수화** + 비순환 평가 |
| RAG 평가 타당성 | ECIR25~26: relevance-scale, LLM-judge bias, chunking reliability, RAG utility | 텍스트 RAG 평가 도구·판정 편향 | **멀티모달 감시 검색 워크로드의 순환성**이라는 새 타당성 축 |

- **정확성 규율(`000_Introduction.md` §3 사실검증 유지):** "필터드 검색은 random mask로만 평가한다"(거짓),
  "감시 VLM엔 retrieval이 없다"(ForeSea 반례로 거짓)는 **쓰지 않는다.** 공백은 "개별 부재"가 아니라
  **"이 축들을 비순환 도시 감시 VLM-QA 워크로드에서 통합 평가한 연구가 드묾"**.

---

## 7. 재프레이밍에서 유지할 스코프 가드레일

`000_MASTER.md` §6에서 ECIR에 특히 유효한 규칙을 승계:

- **latency는 검색·색인 계층 격리 측정.** end-to-end VLM 응답시간으로 확대 금지(VLM 추론이 압도).
  FAISS↔PostgreSQL 절대 latency 비교 금지(격리 후 상대비교만).
- **matched-control 정직성:** ACORN/Filtered-DiskANN가 correlation을 무시했다고 주장하지 않는다. 차이는
  "실측 도시 센서 matched control + VLM evidence layer 통합".
- **다수-positive Recall 상한 caveat** 필수, nDCG/MRR 주지표. 헤드라인은 CI(bootstrap 5,000)+n, 등가는 TOST+SESOI.
- **답변 layer:** 같은 모델 내 paired delta만(모델 간 절대 정확도 비교 금지). "LLM이 영상을 이해했다"류 금지.
- **v1 순환 수치(B0–B5 완벽지표) 인용 금지** — collapse 대조표로만 언급.
- **데이터셋 역할 한계:** VRU=대시캠(도시 고정 CCTV 아님), 이상행동 CCTV=생활안전 이식성만, CityFlow-NL
  main 수치 금지. 522가 유일한 완전 tri-source(최대 caveat, 은폐 말 것).
- **금지 표현:** 최초·전무·완전 독립·전반 일반화·상용 완성 시스템.

---

## 8. 핵심 수치 앵커 (Introduction 인용용 — 결과 정본에서 확정)

| 주장 | 수치 | 근거 |
|---|---|---|
| 순환 붕괴 (C2) | VRU B4 nDCG 0.9736→0.3174; AIHub BM25 0.9600→0.1111 | collapse asset, 300 |
| hard-constraint prefilter (C3/RQ-S) | strict +0.098 [0.068, 0.133] @85q; MEVA +0.093 [0.075, 0.113] | 500, 700 |
| soft-intent 결합도 곡선 (C3) | V<0.05 −0.099 (n=27) ↔ V≥0.3 +0.134; Spearman ρ=0.285 [0.071,0.484] | 500 |
| semantic positive의 필터 미통과율 | 72.6% | 810 §6 |
| filtered-ANN random-mask 과대평가 (C3) | postfilter +0.611(A)/+0.289(B), single-stage +0.50/+0.12~0.22 (Holm-유의); 기전 GT 군집심도 ρ 0.62–0.895 | 620 |
| prefilter 지역색인 면역 | recall 0.98–1.00 @ 0.04ms | 620 |
| pgvector global vs partial | 공간 predicate global recall 0.49 붕괴 vs partial 0.99 @0.4ms 상수 | 720 |
| 색인 3축 (C4) | HNSW p50 0.04ms vs Flat 13.4ms @131K real; IVF-PQ 33× 압축; 522-visual 142K 복제(HNSW ef64 0.9992@0.047ms) | 600 |
| 답변 전파 가능성 (C5) | evidence 품질만 바꿔 closed 0.31 → oracle 0.75 (n=600, 2 LLM) | 630 |
| 전파 경계 (C5) | 1K-문서 RAG에서 26-config rel≈1.0 (색인 선택이 evidence 전달 불변) | 630, 420 Amd.2 |
| 워크로드 규모 | 522 tri-source 3,000 clip·85q·A6 6/6; MEVA 985 clip·193q; 8종 실사용 | 500, 740 |

> 인용 시 반드시 결과 정본(.md)의 값을 재확인. 표현 강도는 CI·n을 동반.

---

## 9. 열린 결정 & 리스크 (ECIR 재프레이밍 PI 결정 대기)

1. **제목(영문).** 후보:
   - *"Non-Circular Evaluation of Filtered Multimodal Retrieval for Urban-Surveillance VLM Question Answering"*
   - *"When Filters, Documents, and Labels Share a Lineage: A Non-Circular Benchmark for Multimodal Surveillance Retrieval"*
   - *"Real Predicates Change Filtered Retrieval: A Validity-First Study of Surveillance Video Evidence Search"*
   → C1/C2(타당성) vs C3(retrieval 발견) 중 **무엇을 제목에 세울지** 결정 필요.
2. **헤드라인 무게 배분.** 타당성(C1/C2) 단독 헤드라인 vs 타당성+실측 predicate(C3) 이중 헤드라인. (권장: 이중 —
   ECIR는 방법론+실증을 함께 선호.)
3. **DB-systems 강등 폭.** pgvector·hot/cold·backend를 §5 downstream 1개 소절로 압축할지, 부록으로 뺄지.
   (12pp 예산에 직접 영향.)
4. **페이지 예산.** LNCS ≤12pp 본문. KIISE 20pp 원고에서 **무엇을 잘라낼지** — 색인 그리드 상세·다각도
   실험은 압축/부록 후보.
5. **국문→영문 이관.** `000_Introduction.md` §6 문단 3개가 영문화 시드. 익명화(기관·데이터 경로·환경명 제거).
6. **마감.** ECIR 2027 abstract/full 마감 확정 필요(별도 VENUE 스캔). 백업(WSDM/SIGIR-short) 검토.
7. **KIISE와의 관계.** KIISE DBR 투고와 ECIR 투고를 **동시/순차** 중 무엇으로 둘지(중복투고 규정·firewall).
   → 두 논문의 **비중복 경계**를 명시(KIISE=DB 설계공간 상세, ECIR=평가 타당성+retrieval 방법론).

**주요 리스크:**
- (R1) "또 하나의 벡터DB 비교"로 읽히면 ECIR desk-reject 위험 → **타당성·retrieval 방법론을 확실히 전면화**.
- (R2) 완전 tri-source가 522 단독 → 외적 타당성 공격 가능. MEVA 복제(+0.093)·UCA·MIRIS를 **정직한 사다리**로 방어.
- (R3) 답변 전파가 null/경계 위주 → "부정 결과"로 폄훼 가능 → **경계 규명 = 과대해석 차단이라는 기여**로 프레이밍.
- (R4) "최초/전무" 유혹 → §6 사실검증 규율로 봉쇄.

---

## 10. 관계 문서 & Provenance

| 문서 | 역할 (ECIR 관점) |
|---|---|
| [`000_Introduction.md`](000_Introduction.md) | 개념 canonical (Motivation/Gap/RQ/Contribution 근거) — 본 문서의 원천 |
| [`000_MASTER.md`](000_MASTER.md) | 연구 종합·불변 가드레일(§6) — §7 스코프 승계 원천 |
| [`100_INTRO_topic_selection_rationale.md`](100_INTRO_topic_selection_rationale.md) | 주제 선정·초기 공백 (HISTORY) |
| 300 / 500 | 순환 진단(F1–F4) / 비순환 구축·A6 감사 로그 |
| 600 / 620 / 720 | 색인 3축 / filtered-ANN matched control / DB 설계·partial index |
| 630 / 660 | 답변 결합 2-스케일 종결 / 전파 세 경계 |
| 700 | MEVA 해외 복제(외적 타당성) |
| `paper_assets/20260710_noncircular_collapse/` | collapse 대조표·유의성 asset |
| (별도) `experiments/ecir2027_lncs/` | **주의:** 그 디렉터리는 *다른* ECIR 논문(LLM-judge 구성 타당도). 본 연구와 혼동 금지 |

**관리 정책:** 본 문서는 ECIR 서사·골격·포지셔닝·리스크를 관리한다. 개념·수치가 바뀌면
결과 정본 → `000_Introduction.md` → 본 문서 순으로 갱신하고, 실제 영문 원고는 §5 골격과 §3 기여를
기준으로 작성한다.
