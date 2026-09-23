# CORAL 연구계획 해설 및 최신 연구동향 재검토

> **정정(2026-08-04): 본 문서의 기존 “자연 상관” 설명 중 높은 상관과 recall 붕괴를 직접 연결한 부분은 폐기한다.** 내부 `ρ=0.616–0.895`는 GLS가 아니라 recall 결손과 global rank depth의 Spearman 상관이다. GLS에서는 양의 값이 local enrichment라 일반적으로 검색을 쉽게 하고, 음의 local depletion이 post-filter를 어렵게 한다. 연구 필요성, 관련 연구, 문제 정의와 수정 실험 설계는 [CORAL_PROBLEM_BACKGROUND_RELATED_WORK_AND_REVISED_EXPERIMENT_DESIGN_20260804.md](CORAL_PROBLEM_BACKGROUND_RELATED_WORK_AND_REVISED_EXPERIMENT_DESIGN_20260804.md)를 정본으로 사용한다.

> 검토 대상: `RESEARCH_PLAN_CORAL_20260804.md`  
> 검토 기준일: 2026-08-04  
> 목적: 설계된 연구의 정체성, 예정 실험, 결과에 따른 논문 수준, 최신 선행연구와의 중복 및 잔여 신규성을 이해하기 쉽게 정리한다.

---

## 0. 먼저 내릴 수 있는 결론

CORAL은 **멀티모달 데이터셋, 벡터 데이터베이스, 환각, RAG를 각각 하나씩 기여하는 네 갈래 연구가 아니다.** 핵심은 다음 한 문장으로 표현하는 것이 가장 정확하다.

> **텍스트·이미지·비디오의 실제 query–predicate 결합이 같은 selectivity의 무작위 filter와 다른 local depletion·over-fetch·graph topology를 만들 때, filtered ANN의 recall과 방법 순위가 어떻게 달라지며 이를 구축 결정에 사용할 수 있는가?**

네 키워드의 실제 역할은 다음과 같다.

| 키워드 | CORAL에서의 역할 | 핵심 기여 여부 |
|---|---|---|
| 벡터 데이터베이스 | filtered ANN의 recall 붕괴, 엔진·인덱스 선택, 검색 파라미터와 부분색인 설계가 연구 본체다. | **핵심** |
| 멀티모달 데이터셋 | 텍스트·이미지·비디오에서 같은 현상이 재현되는지 확인하는 교차 도메인 평가 자산이다. | **핵심 근거** |
| RAG 시스템 | filtered vector search가 사용되는 대표 응용이며, 검색 손실이 답변까지 전달되는지를 확인하는 조건부 종단 실험이다. | **부차적·조건부** |
| 환각 실험 | 현재 계획에는 독립된 조작, 정의, 지표가 없다. RQ5의 “답변 품질”이 환각을 자동으로 뜻하지도 않는다. | **현재는 미설계** |

여기서 “멀티모달”도 정확히 구분해야 한다. 현재 설계는 주로 **서로 다른 양식의 코퍼스에 같은 FANNS 평가를 반복하는 multi-domain/multi-modality evaluation**이다. 텍스트 질의로 영상을 찾고 이미지와 표를 함께 추론하는 식의 **cross-modal retrieval 또는 multimodal fusion 알고리즘**을 새로 제안하는 연구는 아니다.

최신성에 대한 총평은 다음과 같다.

- filtered ANN의 체계적 벤치마크, 상관 지표, 난이도 모델, recall 예측, 질의별 라우팅, 부분색인, 적응형 인덱스는 이미 2024–2026년에 매우 활발히 연구되었다.
- 멀티모달 RAG의 증거 선택, 검색-답변 불일치, 비디오 환각, 충돌 증거, conformal 보장도 이미 밀집된 연구 분야다.
- 그럼에도 **실제 업무에서 생긴 query–predicate dependence를 random 및 hardness-matched synthetic workload와 정면 비교하고, 최신 방법의 잔여 오판을 구축 결정으로 연결하는 결합**은 추가 검증 여지가 있다.
- 다만 이 잔여 문제가 실제로 존재하는지는 아직 확인되지 않았다. “최초의 멀티모달 RAG/환각 연구”나 “높은 자연 상관의 보편 법칙”을 전제하지 말고, **natural workload가 α-hardness 너머에 추가 정보를 주는가**부터 P0에서 반증 가능하게 시험해야 한다.

---

## 1. 이 연구가 풀려는 문제

### 1.1 쉬운 예시

도시 영상 검색에서 다음 질의를 생각할 수 있다.

> “A 구역에서 오후 6–8시에 촬영된 영상 중 빨간 상의를 입은 사람과 가장 유사한 장면 10개”

이 질의는 두 조건을 동시에 만족해야 한다.

1. `A 구역`, `오후 6–8시`라는 메타데이터 predicate를 만족해야 한다.
2. 질의 이미지 또는 문장의 embedding과 가까워야 한다.

정확 검색은 조건을 만족하는 모든 벡터를 확인하므로 느리지만 정답을 찾을 수 있다. approximate nearest-neighbor index는 그래프나 파티션 일부만 탐색해 빠르다. 그러나 query 주변의 전역 이웃이 대부분 filter를 통과하지 않고 valid item이 global ranking 깊은 곳에 있거나, filter 통과 subgraph의 연결이 끊기면 정답을 놓칠 수 있다. 시스템은 결과를 정상적으로 반환하므로 사용자는 누락을 알아채기 어렵다. 계획서가 말하는 **silent recall collapse**는 이런 execution-dependent failure다.

### 1.2 핵심 가설

계획서의 과학적 중심 가설은 다음과 같이 분해된다.

- H1: 실제 query–predicate workload는 local enrichment, neutral, local depletion과 서로 다른 graph topology를 가진다.
- H2: 같은 selectivity의 random mask는 일부 natural-depletion workload의 over-fetch와 recall 손실을 과소평가할 수 있다. 반대로 positive enrichment에서는 natural workload가 더 쉬울 수도 있다.
- H3: 이 차이가 selectivity뿐 아니라 α-hardness로도 충분히 설명되지 않을 때에만 GLS·conductance 같은 추가 dependence/topology 특성이 연구 가치가 있다.
- H4: 작은 exact-ground-truth probe로 코퍼스를 프로파일링하면 모든 후보 인덱스를 먼저 구축하지 않고도 구성별 recall 위험을 예측할 수 있다.
- H5: 위험 예측과 하한을 이용하면 SLA 위반과 과잉 자원 사용을 함께 줄이는 물리 설계 결정을 내릴 수 있다.
- H6(RQ5, 조건부): 검색 recall 손실이 충분히 크고 정답 증거를 실제로 제거하면 VLM 답변도 달라질 수 있다. 반대로 중복 증거가 많으면 큰 Recall@k 손실에도 답변은 유지될 수 있다.

### 1.3 이 연구가 만들려는 산출물

연구 산출물은 세 층으로 이해하면 된다.

1. **경험 법칙(L1, 조건부)**: signed local dependence와 topology가 어떤 엔진·인덱스의 recall에 추가 영향을 주는지, 또는 α-hardness가 이를 모두 설명하는지에 관한 반증 가능한 관찰.
2. **측정 하니스(L2)**: 임베딩, 메타데이터, 소량의 정확 정답을 입력하면 predicate별 특성과 층화 workload, 엔진 평가를 만드는 공개 도구.
3. **CORAL 어드바이저(L3)**: 후보 인덱스를 전부 구축하기 전에 클래스×구성별 recall과 보수적 하한을 예측하고, 전역 인덱스 유지·탐색량 상향·부분색인·exact scan 중 하나를 권하는 시스템.

따라서 L1은 “현상이 있는가”, L2는 “누구나 같은 방법으로 측정할 수 있는가”, L3는 “그 측정이 실제 설계 결정을 개선하는가”에 해당한다.

---

## 2. 반드시 이해해야 하는 핵심 개념

| 개념 | 의미 | 이 연구에서 중요한 이유 |
|---|---|---|
| embedding | 문장·이미지·영상 등을 거리 비교가 가능한 고차원 벡터로 표현한 것 | 의미적 유사 검색의 대상이다. |
| predicate/filter | 시간, 장소, 저자, 태그처럼 검색 결과가 만족해야 하는 구조 조건 | 벡터 그래프의 탐색 경로와 후보 수를 바꾼다. |
| FANNS | filter를 만족하면서 질의와 가까운 이웃을 근사적으로 찾는 검색 | CORAL의 직접 연구 대상이다. |
| Recall@k | exact top-k 정답 중 ANN 결과에 포함된 비율 | 침묵 누락을 측정하는 핵심 품질 지표다. |
| selectivity | 전체 데이터 중 filter를 만족하는 비율 | 낮을수록 후보가 적지만, 같은 selectivity라도 임베딩 배치에 따라 난이도가 다를 수 있다. |
| exact GT | 필터를 만족하는 전체 후보를 정확히 스캔해 얻은 정답 | recall 계산의 기준이다. CORAL은 GT-free가 아니라 **GT-frugal**이다. |
| 자연 predicate–embedding dependence | 실제 수집·업무 과정에서 생긴 metadata와 embedding, query–predicate 결합의 비무작위 구조 | positive/negative/neutral일 수 있으며 random label과 달라질 수 있다. |
| GLS | 질의 주변의 local selectivity와 전체 global selectivity를 비교한 signed 지표 | 양수는 local enrichment로 일반적으로 쉬워지고, 음수는 depletion으로 어려워진다. CORAL이 만든 지표가 아니다. |
| conductance | predicate 만족 노드 집합이 kNN 그래프의 나머지 부분과 얼마나 잘 연결되는지 나타내는 값 | 상관만 아니라 그래프 접근 가능성을 근사한다. |
| α-hardness | 검색 전략이 후보를 추가로 가져와야 하는 실행 난이도를 나타내는 HCBGen의 지표 | “상관보다 실행 난이도가 더 직접적”이라는 강력한 경쟁 설명이다. |
| conformal lower bound | 보정 표본에서의 예측 오차를 이용해 새 항목의 recall에 보수적 하한을 부여하는 방법 | 점추정만 보고 SLA를 지키는 위험을 줄인다. 단, 보정 단위의 교환가능성 등 조건이 필요하다. |
| physical design | 인덱스 종류, 파라미터, 부분색인, exact routing처럼 구축·실행 구조를 선택하는 것 | CORAL이 예측을 운영 행동으로 전환하는 지점이다. |

중요한 통계적 주의점이 있다. “대상 코퍼스 내부에서 보정했다”는 사실만으로 predicate 클래스의 교환가능성이 자동 보장되지는 않는다. 겹치는 태그, 계층형 범주, 인접 시간 구간은 서로 의존할 수 있다. 논문에서는 **무엇을 하나의 calibration unit으로 무작위 표집하는지**, 중첩 predicate를 어떻게 그룹화하는지, 새 predicate에 대한 주변부 coverage인지 미리 열거된 전체 클래스에 대한 동시 coverage인지 명확히 정의해야 한다.

---

## 3. 예정된 실험을 순서대로 해석

### 3.1 전체 흐름

```text
실제 코퍼스와 메타데이터
        ↓
predicate 클래스 열거
        ↓
상관·선택도·그래프 구조·소량 exact GT 프로파일
        ↓
자연 workload / 상관 절제 synthetic workload 생성
        ↓
여러 FANNS 알고리즘·엔진·파라미터 평가
        ↓
recall 붕괴의 존재·원인·일반성 검증
        ↓
구성별 recall 점추정 + 대상 보정 하한
        ↓
SLA와 비용에 따른 물리 설계 권고
        ↓
(게이트 통과 시) VLM 답변으로 손실이 전파되는지 확인
```

### 3.2 실험별 목적, 판정 기준, 실패 의미

| 실험 | 묻는 질문 | 주요 비교·통제 | 핵심 결과 | 실패할 경우의 의미 |
|---|---|---|---|---|
| E0 공개 데이터 de-risk | 공개 데이터에도 충분한 자연 상관이 있는가? | YFCC, arxiv-for-fanns, 공개 영상 자산 | ρ/GLS/conductance 분포와 고상관 predicate 수 | CCTV 전용·비공개 현상이라면 일반성과 재현성이 약해진다. |
| E1 자연 dependence 스펙트럼 | 텍스트·이미지·비디오에서 signed GLS, over-fetch, topology가 실제로 다른가? | 동일한 predicate 열거·표본화 규칙 | 도메인별 분포, 불확실성, 안정성 | 공개 코퍼스에 variation이 없으면 교차 도메인 연구를 줄여야 한다. |
| E2 자연 대 합성 | random 및 hardness-matched synthetic가 natural workload를 재현하는가? | natural vs same-selectivity random vs HCBGen-matched | recall·method ranking 차이와 CI | hardness matching 후 차이가 없으면 별도 자연 축의 동기가 약해진다. |
| E3 dependence 절제 | recall 변화가 domain name이 아닌 metadata–embedding assignment 때문인가? | 같은 코퍼스에서 속성-벡터 할당을 부분 치환, selectivity 고정 | GLS·α-hardness·topology와 recall의 within-corpus response | total effect가 없으면 단순 dataset 관찰만 남는다. |
| E4 경쟁 설명 비교 | 상관 특성이 selectivity와 α-hardness 이상을 설명하는가? | selectivity-only, α-hardness-only, 결합 모델 | 층내 AUROC, MAE 개선, 부분효과 | α-hardness가 모두 흡수하면 “상관 중심” 신규성은 약해진다. |
| E5 엔진·인덱스 기전 | 어떤 설계가 어느 상관 체제에서 실패하는가? | filter-first/post-filter/hybrid, HNSW/IVF/부분색인, 엔진 | recall–latency–memory와 진입점·간선·fallback 분석 | 성능표만 남고 기전 귀속이 안 되면 EA&B 분석 깊이가 부족하다. |
| E6 예측기 | Stage-0 특성으로 아직 만들지 않은 구성의 recall을 예측할 수 있는가? | 직접 측정, selectivity, α-hardness, Query-aware Routing 계열 | leave-one-domain-out MAE, collapse AUROC | 교차 도메인 실패 시 in-domain 어드바이저로 축소한다. |
| E7 conformal 하한 | 실제 recall이 약속한 비율로 하한 위에 놓이는가? | target calibration, group/blocked split, 여러 α | coverage, 하한 폭, SLA 근처 정보성 | coverage가 틀리면 보장 주장은 삭제; 폭이 너무 크면 운영 가치가 없다. |
| E8 결정·비용 | 예측이 실제 구축 결정을 더 싸고 안전하게 하는가? | sample-GT direct measurement, Query-aware Routing, SIEVE, oracle | SLA 위반, 비용, overprovisioning, P×C crossover | 단순 측정이 항상 더 싸면 CORAL의 사용 시나리오가 성립하지 않는다. |
| E9 규모 전이 | 100K에서 배운 관계가 1M·10M에서도 유지되는가? | YFCC 100K/1M/10M | 특성 안정성, 임계 변화, 예측오차 | 소규모 실험만으로 대규모 DBMS 주장을 할 수 없게 된다. |
| E10 RQ5 종단 실험 | 검색 누락이 답변 오류로 이어지는가? | exact/oracle, ANN, 강제 evidence miss, no-evidence | answer accuracy, evidence support, 효과크기 | 실패해도 RQ1–4는 남는다. RQ5를 본문에서 제외하면 된다. |

### 3.3 가장 중요한 식별 실험

논문의 성패를 가르는 실험은 E3의 **상관 절제(correlation ablation)**다. 서로 다른 데이터셋끼리 비교해 “CCTV는 상관도 높고 recall도 낮다”고만 말하면 영상 도메인, 데이터 크기, 임베딩 모델, 태그 품질 등의 차이가 원인일 수 있다.

같은 코퍼스 안에서 predicate의 빈도와 selectivity는 유지한 채 벡터에 연결된 속성만 점진적으로 치환하면 다음 관계를 관찰할 수 있다.

```text
자연 연결 100% → 75% → 50% → 25% → 완전 치환
      높은 상관                         0에 가까운 상관
```

이때 recall 붕괴가 상관 감소와 함께 일관되게 회복되고, 그 기울기가 엔진·인덱스별로 설명된다면 “자연 상관이 원인 축”이라는 주장이 강해진다. 반대로 기울기가 없거나 α-hardness를 넣으면 사라진다면 상관은 원인이라기보다 간접 proxy일 가능성이 크다.

### 3.4 CORAL이 직접 측정과 경쟁하는 정확한 지점

인덱스가 이미 하나 구축되어 있다면 수백 개 질의를 exact GT와 비교하는 직접 측정이 예측보다 더 정확할 수 있다. CORAL이 필요한 상황은 다음과 같다.

- predicate 클래스가 `P`개 있다.
- 엔진·인덱스·파라미터·부분색인 후보가 `C`개 있다.
- 구축 전에 어느 구성을 만들지 골라야 한다.
- 직접 확인하려면 후보 인덱스 `C`개를 모두 구축하고 `P×C`를 측정해야 한다.

따라서 논문은 단순히 예측 MAE가 낮다고 끝내면 안 된다. **인덱스 구축비, Stage-0 프로파일 비용, exact GT 비용, 오선택 비용을 모두 포함한 P×C 평면에서 언제 CORAL이 직접 측정보다 유리해지는지**를 보여야 한다. 이 crossover가 없으면 훌륭한 회귀 모델이어도 시스템 기여가 약하다.

---

## 4. 결과가 논문의 수준을 어떻게 결정하는가

### 4.1 최상위 DB 논문으로 설득력 있는 결과

PVLDB Experiment, Analysis & Benchmark 또는 SIGMOD급을 노리려면 다음 네 축이 함께 필요하다.

1. **현상의 일반성과 인과성**
   - 공개 가능한 둘 이상의 도메인에서 자연 상관 스펙트럼과 큰 recall 붕괴가 재현된다.
   - 상관 절제에서 selectivity 고정 후에도 일관된 기울기가 나온다.
   - 상관 특성이 α-hardness와 selectivity를 통제한 뒤에도 추가 설명력을 보인다.

2. **시스템적 유용성**
   - CORAL이 최근접 경쟁자인 Query-aware Routing 및 강한 직접 측정 기준과 정면 비교된다.
   - SLA 위반을 줄이면서 oracle 대비 과잉 비용이 작다.
   - 여러 후보 인덱스를 모두 구축하는 것보다 유리한 crossover 영역이 현실적인 P와 C에서 나타난다.

3. **통계적 신뢰성**
   - target-calibrated 하한이 사전 지정한 coverage를 만족한다.
   - 하한이 너무 넓어 항상 0에 가까운 공허한 보장이 아니며 SLA 부근에서 결정을 실제로 바꾼다.
   - 중첩 predicate, 다중 하한, domain shift에 관한 보장 범위를 정확히 한정한다.

4. **재현성과 규모**
   - 공개 티어만으로 대표 자연 상관과 recall 붕괴가 재현된다.
   - 10M급 규모 전이가 포함되고 엔진·인덱스 구현 차이와 비용 원장이 공개된다.
   - CCTV 결과만 비공개 자산에 의존하지 않는다.

이 경우 논문의 가장 강한 메시지는 “새 인덱스가 더 빠르다”가 아니라 다음과 같다.

> 기존 벤치마크가 보지 못한 자연 상관 체제를 정립했고, 그 체제가 실제 시스템의 recall 신뢰성과 구축 전 설계 결정을 바꾼다는 것을 공개적·인과적·통계적으로 입증했다.

### 4.2 결과별 현실적인 강등 경로

| 관측 결과 | 적절한 논문 형태 | 판정 |
|---|---|---|
| L1·L2·L3 모두 성공, 공개 재현, 강한 baseline 우위 | PVLDB EA&B / SIGMOD 연구 트랙 후보 | 가장 강함 |
| 자연 상관과 합성 과소평가는 강하지만 교차 도메인 예측이 실패 | 자연 상관 benchmark + in-domain advisor + transfer limit | 충분히 출판 가능, 주장 축소 |
| L1·L2는 강하지만 CORAL이 직접 측정/Query-aware Routing보다 못함 | EA&B형 측정 연구, 어드바이저는 부정 결과 또는 부록 | 기여 2층으로 축소 |
| α-hardness가 상관의 효과를 거의 모두 설명 | “자연 상관”이 hardness의 발생 원인인지 분석하는 반박·통합 연구 | 현재 제목과 핵심 주장은 수정 필요 |
| 높은 자연 상관이 소규모·비공개 CCTV에서만 관측 | 사례 연구 또는 국내 저널 확장 | 최상위권 일반성 부족 |
| 합성 workload가 자연 workload를 잘 재현 | HCBGen을 반박하기보다 지지하는 negative result | 정직한 결과지만 CORAL 고유성 약화 |
| RQ5만 성공하고 RQ1–4가 약함 | 멀티모달 RAG 후속 연구로 재설계 | DB 논문의 핵심을 구하지 못함 |
| RQ5가 실패하고 RQ1–4가 성공 | RQ5 제외, DB reliability 논문 유지 | 핵심에는 문제 없음 |

즉, RQ5는 논문의 수준을 올릴 수 있는 보조 증거일 뿐이다. **VLM 답변 효과가 크다고 해서 CORAL predictor가 약한 문제가 해결되지 않고, 답변 효과가 0이라고 해서 filtered ANN reliability 연구가 실패하는 것도 아니다.**

---

## 5. 2026년 8월 기준 최신 연구동향 재검토

### 5.1 filtered vector search와 벡터 DB

이 영역은 이미 매우 빠르게 진행 중이다.

| 연구 | 이미 수행한 내용 | CORAL과의 중복 | 남는 차이 |
|---|---|---|---|
| [ACORN, PACMMOD/SIGMOD 2024](https://doi.org/10.1145/3654923) | 다양한 predicate를 지원하는 HNSW 기반 predicate-subgraph traversal | 혼합 양식 데이터와 filtered ANN 평가 | 자연 상관 스펙트럼 및 pre-build 위험 예측은 아님 |
| [SIEVE, PVLDB 2025](https://arxiv.org/abs/2507.11907) | workload를 이용해 여러 predicate용 부분색인을 offline 선택하고 recall–비용 모델로 질의 시 인덱스 선택 | 부분색인과 물리 설계 행동 | 자연 상관 risk predictor, target-calibrated 하한과는 다름 |
| [Unified FANNS Benchmark, 2025](https://arxiv.org/abs/2509.07789) | 분류 체계, 통합 파라미터 튜닝, 실데이터 기반 체계적 비교 | “최초의 체계적 평가” 주장을 선점 | correlation-regime-specific 분석은 명시적 중심이 아님 |
| [In-depth Experimental Study, SIGMOD 2026](https://arxiv.org/abs/2508.16263) | 10개 알고리즘·12개 방법·최대 10M, pruning/entry point/edge filtering 분석 | 엔진 기전 분석과 대규모 비교 | 측정된 자연 상관 축은 별도 공백 |
| [arxiv-for-fanns, SIGIR 2026](https://arxiv.org/abs/2507.21989) | 270만 transformer text embedding과 11개 실제 속성, 11개 FANNS 방법 평가 | 공개 텍스트 데이터와 실제 속성 | 자연 상관을 연구 중심 변수로 정량화·절제하지 않음 |
| [MoReVec/GLS, 2026](https://arxiv.org/abs/2602.11443) | 실제 relational metadata, GLS 상관 지표, FAISS/Milvus/pgvector 비교 | “상관 지표/측정 최초” 주장을 선점 | CORAL은 고상관 자연 체제의 스펙트럼과 붕괴 법칙을 보여야 함 |
| [VecBench, PACMMOD/SIGMOD 2026](https://doi.org/10.1145/3802125) | filter rate와 vector–attribute 관계를 제어 가능한 workload로 평가 | “상관을 제어한 benchmark” 주장을 선점 | 자연 발생 속성의 측정 스펙트럼과 natural-vs-synthetic 차이가 남는 쟁점 |
| [HCBGen, PVLDB 2026](https://arxiv.org/abs/2606.14193) | α-hardness를 제안하고 hardness-matched synthetic workload 생성; 상관·선택도가 전략에 따라 불안정할 수 있다고 보고 | CORAL의 중심 가설에 대한 직접 반론 | CORAL은 α-hardness 너머의 자연 상관 효과를 실험으로 입증해야 함 |
| [Query-aware Routing, 2026](https://arxiv.org/abs/2606.19898) | 질의별로 각 후보 방법의 recall을 예측하고 offline recall–QPS 표를 이용해 최적 방법으로 routing; 6개 학습·5개 unseen 데이터 | recall 예측과 cross-dataset 전이를 직접 선점 | 대상별 benchmark table 없이 하는 pre-build class×config 설계와 보정 하한이 잔여 차이 |
| [Quake, OSDI 2025](https://arxiv.org/abs/2506.03437) | 동적 workload에서 적응형 partition과 recall estimation으로 파라미터 조절 | adaptive index와 recall estimation | metadata predicate 및 자연 상관 중심 연구는 아님 |
| [CatapultDB, 2026](https://arxiv.org/abs/2603.02164) | query locality에 따라 그래프 시작점을 동적으로 개선하며 filtered search도 보존 | workload-adaptive vector index라는 넓은 표현을 선점 | predicate별 recall-risk/부분색인 문제와는 다름 |

이 표가 뜻하는 것은 분명하다.

- “filtered ANN을 처음 체계적으로 평가한다”는 주장은 불가능하다.
- “실제 속성을 처음 사용한다”, “상관을 처음 측정한다”, “recall을 처음 예측한다”, “workload-aware 물리 설계를 처음 한다”도 불가능하다.
- 가장 가까운 위협은 HCBGen과 Query-aware Routing이다.
- CORAL의 유효한 차이는 **natural correlation spectrum + within-corpus causal ablation + pre-build class×configuration decision + target-calibrated lower bound**의 결합이다.

### 5.2 conformal 보장과 “최초” 주장

RAG/검색 시스템에서 conformal prediction을 이용한 신뢰성 보장은 이미 존재한다.

- [TRAQ, NAACL 2024](https://aclanthology.org/2024.naacl-long.210/)는 conformal prediction set으로 관련 passage와 의미적으로 올바른 답을 포함할 확률을 제어한다.
- [C-RAG, ICML 2024](https://proceedings.mlr.press/v235/kang24a.html)는 RAG generation risk에 conformal upper confidence bound를 부여한다.
- [Conformal Information Retrieval, FEVER 2024](https://aclanthology.org/2024.fever-1.22/)도 관련 정보가 포함되는 검색 집합의 coverage와 크기를 다룬다.

이번 검색에서 **filtered ANN의 predicate-class×configuration recall에 대상 코퍼스 보정 하한을 부여하고 이를 물리 설계 행동으로 연결한 동일 논문**은 확인하지 못했다. 그러나 검색 부재만으로 “세계 최초”를 증명할 수는 없다. 따라서 계획서의 다음 표현은 제출 전까지 보류하는 편이 안전하다.

> “filtered ANN recall의 최초 분포무관 하한”

권장 표현은 다음과 같다.

> “To our knowledge, a target-calibrated recall lower bound designed for pre-build physical-design decisions in filtered ANN has not been evaluated; we scope the guarantee to the stated target-corpus calibration protocol and marginal coverage.”

또한 “distribution-free”는 모델 분포를 가정하지 않는다는 뜻이지 아무 조건도 없다는 뜻이 아니다. calibration/test exchangeability, score 정의, finite-sample correction, predicate 의존성, multiple outputs, distribution shift 범위를 반드시 함께 써야 한다.

### 5.3 멀티모달 RAG·증거 선택

멀티모달 RAG는 이미 retrieval, reranking, fine-grained evidence, 비용, 답변 효용을 함께 다루는 단계에 들어섰다.

- [REAL-MM-RAG, ACL 2025](https://aclanthology.org/2025.acl-long.1528/)는 실제 문서에 가까운 멀티모달 retrieval benchmark를 제안했다.
- [Utility-Oriented Visual Evidence Selection, ACL 2026](https://aclanthology.org/2026.acl-long.1620/)은 단순 유사도가 아니라 downstream output utility를 기준으로 시각 증거를 선택한다.
- [GranuRAG, ACL Findings 2026](https://aclanthology.org/2026.findings-acl.509/)은 장면 전체가 아니라 element-level evidence를 검색해 검증 가능성을 높인다.
- [Chart-MRAG, ACL 2026](https://aclanthology.org/2026.acl-long.1164/)은 oracle retrieval을 줘도 generation 성능이 완벽하지 않고 text-over-visual bias가 남는다고 보고한다.
- [VideoStir, ACL 2026](https://aclanthology.org/2026.acl-long.1656/)은 장시간 영상을 시공간 그래프로 구조화해 intent-aware multi-hop retrieval을 수행한다.
- [R³AG, ACL 2026](https://aclanthology.org/2026.acl-long.939/)은 retriever의 검색 품질과 generation utility를 함께 학습해 질의별 retriever routing을 한다.

따라서 RQ5가 성공해도 “retrieval quality와 answer quality의 관계를 처음 밝혔다”거나 “멀티모달 증거 선택을 처음 했다”고 주장할 수 없다. CORAL의 RQ5는 **자연 상관 때문에 발생한 filtered-index approximation error가 답변으로 전파되는지에 대한 제한된 종단 검증**으로만 자리 잡아야 한다.

### 5.4 환각 연구

비디오·멀티모달 환각 자체도 이미 독립적인 대형 분야다.

- [VideoHallucer, 2024](https://arxiv.org/abs/2406.16338)는 intrinsic/extrinsic video hallucination과 세부 유형을 평가한다.
- [VidHalluc, CVPR 2025](https://openaccess.thecvf.com/content/CVPR2025/html/Li_VidHalluc_Evaluating_Temporal_Hallucinations_in_Multimodal_Large_Language_Models_for_CVPR_2025_paper.html)는 action, temporal sequence, scene transition 환각을 통제된 영상 쌍으로 측정한다.
- [CMC-Bench, MAGMaR 2026](https://aclanthology.org/volumes/2026.magmar-main/)는 이미지와 텍스트가 충돌하는 네 가지 증거 조건을 평가하고 fabrication과 abstention을 구분해야 함을 보인다.
- [Stable-RAG, ACL 2026](https://aclanthology.org/2026.acl-long.1188/)는 같은 문서 집합의 순서 변화만으로 발생하는 RAG 답변 불안정과 환각을 다룬다.

그러므로 CORAL 문서의 현재 RQ5를 “환각 실험”이라고 부르면 안 된다. answer accuracy 하락은 다음 중 무엇이든 될 수 있기 때문이다.

- 검색기가 정답 증거를 놓친 retrieval failure
- 정답 영상이 있지만 VLM이 보지 못한 perception failure
- 증거를 잘 읽고도 추론을 틀린 reasoning failure
- 증거에 없는 내용을 만들어 낸 unsupported fabrication
- 확신이 없어 답하지 않은 abstention

이들을 분리하지 않으면 환각 연구로서 해석할 수 없다.

---

## 6. RQ5를 실제 환각 실험으로 확장하려면

이 확장은 CORAL 본체에 필수적이지 않으며, DB 논문의 초점을 흐릴 수 있으므로 **P0 manipulation gate를 통과한 경우에만 부록 또는 후속 연구로 수행**하는 것이 바람직하다.

### 6.1 권장 질문

> 자연 상관 workload에서 ANN이 정답 증거를 누락했을 때, VLM은 답변을 틀리는 데 그치는가, 근거 없는 내용을 생성하는가, 아니면 적절히 답변을 보류하는가?

### 6.2 최소 실험 조건

같은 질의와 VLM을 고정하고 evidence만 조작한다.

| 조건 | 목적 |
|---|---|
| oracle exact evidence | 생성기가 사용할 수 있는 상한 확인 |
| ANN evidence | 실제 시스템 효과 확인 |
| forced-miss ANN evidence | 정답 증거 제거의 인과 효과 확인 |
| distractor evidence | 무관 증거에 끌리는지 확인 |
| conflicting/counterfactual evidence | 잘못된 근거를 따라 fabrication하는지 확인 |
| no evidence | closed-book 기준 확인 |

추가로 exact와 ANN의 top-k 크기, evidence 순서, VLM decoding, prompt, 영상 해상도와 프레임 수를 고정해야 retrieval approximation 효과만 분리할 수 있다.

### 6.3 지표

- retrieval: Recall@k, 정답 evidence 포함 여부, evidence sufficiency
- answer: exact match 또는 task accuracy, confidence/calibration
- faithfulness: 답변 claim 중 제공된 evidence가 지지하는 비율
- hallucination: unsupported fabrication rate
- behavior: abstention rate와 fabrication rate를 분리
- propagation: `forced miss → evidence insufficiency → answer/fabrication`의 매개 효과

통계 분석은 같은 질의에 여러 evidence 조건을 적용한 paired design으로 해야 한다. 이항 결과는 McNemar 검정 또는 질의/데이터셋 random effect를 둔 mixed-effects logistic model을 사용할 수 있고, 효과크기에는 query-cluster bootstrap 신뢰구간을 함께 제시한다. 여러 VLM·데이터셋·조건을 동시에 검정하면 family-wise error 또는 FDR 통제가 필요하다.

### 6.4 성공 판정

- forced-miss가 oracle 대비 answer accuracy뿐 아니라 unsupported fabrication을 유의하게 높인다.
- 이 효과가 no-evidence 또는 distractor 효과와 구분된다.
- retrieval miss의 영향이 evidence sufficiency를 통해 매개됨을 보인다.
- 여러 VLM 또는 최소 둘 이상의 공개 데이터에서 방향이 재현된다.

이 조건을 만족해야 “filtered ANN recall collapse가 RAG hallucination risk로 전파된다”고 말할 수 있다. 단순히 oracle과 ANN의 답변 정확도가 다르다는 결과만으로는 부족하다.

---

## 7. 신규성 판정표

| 주장 후보 | 판정 | 이유 및 권장 처리 |
|---|---|---|
| 최초의 filtered ANN benchmark | **불가** | Unified Benchmark, VecBench, SIGMOD 2026 실험 연구가 존재한다. |
| 최초의 실제 메타데이터 FANNS 데이터 | **불가** | YFCC, arxiv-for-fanns, MoReVec 등 이미 존재한다. |
| 최초의 filter–embedding 상관 지표 | **불가** | GLS가 명시적으로 제안되었다. |
| 상관-controlled benchmark 최초 | **불가** | VecBench가 synthetic control을 제공한다. |
| recall/방법 선택 예측 최초 | **불가** | Query-aware Routing과 Quake 계열이 존재한다. |
| workload-aware 부분색인 최초 | **불가** | SIEVE가 이미 수행한다. |
| 자연 상관 스펙트럼을 측정한 교차 양식 FANNS 연구 | **조건부 방어 가능** | 공개 데이터에서 실제 스펙트럼과 자연-합성 격차를 재현해야 한다. |
| 상관 절제로 recall 붕괴의 인과 효과 식별 | **유망** | selectivity와 α-hardness를 통제한 within-corpus slope가 필요하다. |
| pre-build class×configuration 위험 예측과 물리 설계 권고 | **조건부 방어 가능** | Query-aware Routing·직접 측정·SIEVE 대비 사용 시나리오와 crossover를 입증해야 한다. |
| filtered ANN recall의 최초 분포무관 하한 | **현재 보류** | 동일 타깃 연구는 찾지 못했지만 conformal 검색/RAG 선행연구가 있고 “최초” 증명은 더 엄격한 검토가 필요하다. |
| 최초의 멀티모달 RAG/환각 실험 | **불가** | 증거 선택, 검색-답변 분리, video hallucination 연구가 이미 밀집되어 있다. |

가장 방어 가능한 논문 정체성은 다음과 같다.

> **CORAL is an experiment-and-analysis study and pre-build advisor for reliability failures caused by naturally correlated predicates in filtered vector search—not a new multimodal RAG or hallucination architecture.**

---

## 8. 계획서에서 즉시 조정할 표현

### 8.1 결과와 가설을 분리

계획서의 `실측 최대 −0.627`, `13× 과소평가`, `ρ 0.62–0.895`는 현재 내부 예비 결과다. 최종 논문에서는 다음을 함께 제시하기 전까지 일반 사실처럼 쓰지 않는다.

- 데이터·predicate·embedding·engine·parameter의 정확한 정의
- 독립 질의 수와 분석 단위
- uncertainty interval과 반복 실행
- 사후 선택된 최대값인지 사전 지정된 대표값인지
- 공개 티어에서의 재현 여부

권장 문장은 “preliminary measurements observed ...; the preregistered study will test whether ...”와 같이 가설 검증 전 상태를 드러낸다.

### 8.2 `최초 분포무관 하한` 완화

§10의 “filtered ANN recall의 최초 분포무관(대상 보정) 하한”은 다음처럼 바꿀 것을 권한다.

> “대상 코퍼스의 명시된 보정 프로토콜 아래에서 filtered ANN recall 하한의 coverage와 의사결정 유용성을 평가한다.”

최종 systematic review가 끝난 뒤에만 `to our knowledge`를 붙인 제한적 최초 주장을 고려한다.

### 8.3 RQ5 용어 정리

- 현재: “색인 재현율 손실은 언제 VLM 답변 품질에 도달하는가?”
- 정확한 명칭: **retrieval-approximation-to-answer propagation**
- 환각을 주장하려면 §6의 fabrication/abstention/evidence-support 정의와 조작을 추가한다.

### 8.4 멀티모달 표현 정리

“임의의 멀티모달 코퍼스”보다는 다음이 정확하다.

> “modality-agnostic harness evaluated across text, image, and video corpora”

하나의 코퍼스 안에서 여러 양식을 결합하지 않는다면 `multimodal corpus`라는 표현은 reviewer에게 cross-modal algorithm을 기대하게 할 수 있다.

---

## 9. 권장 실행 우선순위와 중단 기준

### 9.1 먼저 해야 할 일

1. **공개 데이터 자연 상관 게이트**: YFCC와 arxiv-for-fanns에서 사전 고정 predicate 규칙으로 GLS/ρ/conductance 분포를 측정한다.
2. **한 코퍼스 상관 절제 파일럿**: selectivity를 고정하고 최소 5개 치환 강도에서 recall 기울기를 확인한다.
3. **α-hardness 정면 비교**: 상관 특성의 증분 설명력이 있는지 확인한다.
4. **비용 원장 파일럿**: Stage 0, exact GT, 인덱스 구축, 전체 grid 측정 비용을 같은 하드웨어에서 잰다.
5. **Query-aware Routing 비교 가능성 확보**: 동일 후보군·예산·평가 단위를 정의한다.
6. **conformal calibration unit 확정**: 중첩 predicate를 그룹화하고 coverage estimand를 사전등록한다.
7. 위 게이트를 통과한 뒤에만 엔진 전체 캠페인과 RQ5를 수행한다.

### 9.2 Go / Rescope / Stop 기준

| 판정 | 조건 | 조치 |
|---|---|---|
| Go | 공개 데이터에서 상관 체제가 존재하고, 절제 기울기와 α-hardness 너머 설명력이 확인됨 | L1–L3 전체 진행 |
| Rescope-A | 현상은 강하지만 교차 도메인 predictor가 약함 | natural-correlation benchmark + in-domain advisor로 축소 |
| Rescope-B | 상관은 α-hardness에 흡수되지만 자연 workload가 synthetic보다 어렵고 원인이 설명됨 | correlation을 주인공이 아닌 hardness-generating mechanism으로 재정의 |
| Stop/Pivot | 공개 데이터에서 현상이 재현되지 않고 CCTV도 규모 확대 시 사라지며 직접 측정이 항상 우세 | CORAL 어드바이저를 중단하고 negative benchmark 또는 다른 설계로 전환 |

---

## 10. 최종 평가

이 계획은 **연구 질문 자체는 명확하고, 실패 결과까지 고려한 강등 경로가 있으며, 최신 DB 연구와 경쟁할 수 있는 실험형 논문 구조**를 갖고 있다. 특히 natural-vs-synthetic 비교, within-corpus 상관 절제, killer baseline인 직접 측정 포함, target-corpus calibration, 공개 아티팩트 게이트는 좋은 설계다.

그러나 현재 가장 큰 위험은 네 키워드를 한 논문에 모두 넣으려는 인상과 `최초` 표현이다. 2026년의 연구 지형에서는 각 주변 분야가 이미 충분히 성숙했다. CORAL이 높은 수준의 논문이 되려면 범위를 넓히기보다 다음 세 결과를 강하게 만들어야 한다.

1. **자연 상관이 선택도와 α-hardness로 환원되지 않는 실재 난이도 축이라는 인과 증거**
2. **합성 평가가 그 축에서 실제 recall 위험을 체계적으로 오판한다는 공개·대규모 증거**
3. **그 정보를 사용한 pre-build 결정이 직접 측정 및 최신 routing 방법보다 현실적인 비용 구간에서 더 나은 SLA–비용 결정을 만든다는 증거**

이 세 가지가 성립하면 RQ5 없이도 강한 vector DB reliability 논문이 된다. 반대로 이 세 가지가 약한데 환각·RAG 실험만 추가하면 논문의 정체성이 분산될 가능성이 높다.

---

## 11. 검토에 사용한 핵심 1차 문헌

### Filtered ANN·벡터 DB

- Patel et al., [ACORN: Performant and Predicate-Agnostic Search Over Vector Embeddings and Structured Data](https://doi.org/10.1145/3654923), PACMMOD/SIGMOD 2024.
- Li et al., [SIEVE: Effective Filtered Vector Search with Collection of Indexes](https://arxiv.org/abs/2507.11907), PVLDB 2025.
- Shi et al., [Filtered Approximate Nearest Neighbor Search: A Unified Benchmark and Systematic Experimental Study](https://arxiv.org/abs/2509.07789), 2025.
- Li et al., [Attribute Filtering in Approximate Nearest Neighbor Search: An In-depth Experimental Study](https://arxiv.org/abs/2508.16263), SIGMOD 2026.
- Iff et al., [Benchmarking FANNS on Transformer-based Embedding Vectors](https://arxiv.org/abs/2507.21989), SIGIR 2026.
- Amanbayev et al., [Filtered ANN Search in Vector Databases: System Design and Performance Analysis](https://arxiv.org/abs/2602.11443), 2026.
- Zhang et al., [VecBench: A Controllable Benchmark for Filtered Vector Search](https://doi.org/10.1145/3802125), PACMMOD/SIGMOD 2026.
- Lim et al., [HCBGen: A Hardness-Controlled Benchmark Generator](https://arxiv.org/abs/2606.14193), PVLDB 2026.
- Xiong and Zhang, [Query-aware Routing for Filtered Approximate Nearest Neighbors Search](https://arxiv.org/abs/2606.19898), 2026.
- Mohoney et al., [Quake: Adaptive Indexing for Vector Search](https://arxiv.org/abs/2506.03437), OSDI 2025.

### 신뢰성·RAG·멀티모달·환각

- Li et al., [TRAQ: Trustworthy Retrieval Augmented Question Answering via Conformal Prediction](https://aclanthology.org/2024.naacl-long.210/), NAACL 2024.
- Kang et al., [C-RAG: Certified Generation Risks for Retrieval-Augmented Language Models](https://proceedings.mlr.press/v235/kang24a.html), ICML 2024.
- Wasserman et al., [REAL-MM-RAG](https://aclanthology.org/2025.acl-long.1528/), ACL 2025.
- Luo et al., [Utility-Oriented Visual Evidence Selection for Multimodal RAG](https://aclanthology.org/2026.acl-long.1620/), ACL 2026.
- Chen et al., [From Scenes to Elements: Multi-Granularity Evidence Retrieval for Verifiable Multimodal RAG](https://aclanthology.org/2026.findings-acl.509/), ACL Findings 2026.
- Yang et al., [Chart-MRAG](https://aclanthology.org/2026.acl-long.1164/), ACL 2026.
- Wang et al., [VideoHallucer](https://arxiv.org/abs/2406.16338), 2024.
- Li et al., [VidHalluc](https://openaccess.thecvf.com/content/CVPR2025/html/Li_VidHalluc_Evaluating_Temporal_Hallucinations_in_Multimodal_Large_Language_Models_for_CVPR_2025_paper.html), CVPR 2025.
- Zhang et al., [Stable-RAG](https://aclanthology.org/2026.acl-long.1188/), ACL 2026.

### 검토 한계

본 재검토는 2026-08-04 현재 공개된 논문·학회 원문과 프로젝트 내부 선행연구표를 교차 확인한 결과다. “동일 연구를 찾지 못했다”는 것은 해당 범위의 문헌 검색 결과이지 절대적인 최초성 증명이 아니다. 특허, 비공개 산업 연구, 이후 공개될 2026–2027 preprint까지 포함한 최초성 판단은 제출 직전 다시 갱신해야 한다.
