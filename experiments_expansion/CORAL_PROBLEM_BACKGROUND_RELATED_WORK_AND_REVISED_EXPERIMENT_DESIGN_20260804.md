# CORAL 문제 배경·관련 연구·문제 정의·수정 실험 설계 상세 보고서

> 기준일: 2026-08-04  
> 대상 문서: `RESEARCH_PLAN_CORAL_20260804.md`  
> 목적: “자연 상관”의 의미와 연구 필요성을 다시 정의하고, 기존 계획의 모순을 감사한 뒤, 연구를 계속할 조건과 중단할 조건을 포함한 실행 가능한 설계를 제시한다.

---

## 0. 결론부터 말하면

### 0.1 이 연구를 지금 상태 그대로 “반드시” 수행해야 하는 것은 아니다

연구를 수행해야만 한다는 절대적 이유는 없다. 현재 확인된 사실만으로는 **전체 CORAL 프로젝트를 곧바로 수행할 충분한 근거가 아직 없다.** 수행을 정당화할 수 있는 것은 다음의 조건부 명제뿐이다.

> 실제로 발생한 query–predicate workload의 기하 구조가 selectivity와 기존 α-hardness만으로 설명되지 않고, 최신 filtered-search 방법에서도 중요한 recall/SLA 오판을 만들며, 그 구조를 저비용으로 측정하는 것이 기존 benchmark table이나 직접 측정보다 더 나은 구축 결정을 만든다면 CORAL을 수행할 가치가 있다.

이 명제의 각 조건이 아직 검증되지 않았다. 따라서 권고는 다음과 같다.

- 전체 P1–P4를 즉시 실행하지 않는다.
- 먼저 정의 오류와 신규성을 검증하는 소규모 **P0 연구 타당성 감사**만 수행한다.
- P0에서 기존 연구가 이미 충분히 해결했다는 결과가 나오면 CORAL을 중단하거나 범위를 축소한다.
- P0를 통과한 경우에만 cross-domain benchmark 또는 advisor를 진행한다.

### 0.2 “기존 연구가 활발하다”와 “추가 연구가 필요할 수 있다”는 논리적으로 모순은 아니다

두 문장은 서로 다른 것을 말한다.

- “활발하다”는 것은 filtered ANN 알고리즘, benchmark, hardness, routing, partial index가 이미 많이 연구되고 있다는 뜻이다.
- “추가 연구가 필요하다”는 것은 그 연구들이 특정한 외적 타당성 또는 운영 의사결정 문제를 아직 해결하지 못했을 가능성이 있다는 뜻이다.

다만 **활발한 분야라는 사실만으로 추가 연구가 정당화되지는 않는다.** 정확한 잔여 문제가 존재하고, 중요하며, 현재 방법으로 해결되지 않는다는 증거가 필요하다. 기존 CORAL 문서는 이 마지막 연결을 충분히 입증하지 않은 채 “자연 상관”을 신규 축으로 선언했다. 이 점이 사용자가 느낀 모순의 핵심이며, 그 지적은 타당하다.

### 0.3 기존 계획에서 발견한 세 가지 중대한 문제

1. **서로 다른 ρ를 같은 상관계수처럼 혼용했다.**
   - 내부 결과의 `0.616–0.895`는 predicate-embedding 상관값이 아니다.
   - 이것은 predicate별 `recall 결손`과 `exact filtered neighbor의 전역 rank depth` 사이의 **Spearman 순위상관계수**다.
   - 이를 “CCTV 코퍼스의 자연 상관 ρ=0.62–0.895”라고 부른 것은 잘못이다.

2. **GLS의 방향과 recall 붕괴 서사가 뒤집혔다.**
   - GLS에서 양의 값은 query 주변에 filter 통과 벡터가 전역 비율보다 풍부한 local enrichment다.
   - 일반적으로 이는 valid neighbor를 쉽게 찾게 하므로 recall에 유리하다.
   - 음의 GLS, 즉 local depletion이 post-filter의 over-fetch와 recall 손실을 키운다.
   - 따라서 “높은 양의 자연 상관이 recall을 붕괴시킨다”는 문장은 GLS 기준으로 틀렸다.

3. **순수 pre-build와 target-calibrated conformal 보장이 충돌한다.**
   - configuration별 conformal residual을 계산하려면 대상 코퍼스에서 그 configuration의 실제 recall label이 필요하다.
   - 실제 recall을 얻으려면 해당 index/configuration을 적어도 표본 규모에서 구축·실행해야 한다.
   - 따라서 target 보정을 유지하려면 `pre-build`가 아니라 **proxy-build/build-frugal advisor**로 불러야 한다.
   - 대상 configuration label 없이 진정한 pre-build를 유지하려면 target-specific coverage 보장을 포기하고 cross-domain empirical prediction으로 한정해야 한다.

이 세 문제를 해소하기 전에는 기존 계획서의 L1과 L3를 논문 주장으로 사용할 수 없다.

---

## 1. 문제 배경

### 1.1 일반 벡터 검색

문장, 이미지, 영상은 embedding model을 거쳐 벡터 (x_i\in\mathbb{R}^d)로 저장된다. 질의도 벡터 (q_v)로 바꾼 뒤 거리가 가까운 top-(k) 항목을 찾는다.

모든 벡터와 거리를 계산하는 exact search는 정확하지만 데이터가 커질수록 비싸다. HNSW, IVF, DiskANN 같은 approximate nearest-neighbor(ANN) index는 일부 후보만 탐색하여 속도를 얻는 대신 exact top-(k) 일부를 놓칠 수 있다.

### 1.2 filtered vector search

실제 검색은 벡터 유사도만 요구하지 않는다.

- 문서: 주제가 비슷하면서 `year >= 2024`
- 상품: 사진이 비슷하면서 `category = shoes`, `price < 100`
- CCTV: 사람의 외형이 비슷하면서 `camera = A`, `time ∈ [18:00,20:00]`

각 데이터는 ((x_i,a_i)) 형태로 벡터 (x_i)와 메타데이터 (a_i)를 가진다. predicate (p(a_i)\in\{0,1\})를 만족하는 벡터 중에서만 top-(k)를 찾아야 한다.

정답은 다음과 같다.

\[
G_k(q,p)=\operatorname{TopK}_{i:p(a_i)=1}\ d(q_v,x_i)
\]

시스템 결과를 (A_k(q,p;c))라고 하면 configuration (c)의 recall은 다음과 같다.

\[
R(q,p,c)=\frac{|A_k(q,p;c)\cap G_k(q,p)|}{k}
\]

### 1.3 세 가지 기본 실행 방식

#### Filter first / exact pre-filter

predicate를 먼저 적용하고 통과한 subset을 정확히 스캔한다.

- 장점: recall 1.0
- 단점: 통과 집합이 크거나 질의가 많으면 느리다.

#### Search first / post-filter

전역 ANN에서 (k' > k)개를 가져온 뒤 predicate를 적용한다.

- 장점: 기존 ANN index를 그대로 쓸 수 있다.
- 단점: 상위 (k')에 valid item이 충분하지 않으면 결과가 부족하거나 recall이 낮다.

#### Filter-aware/hybrid index

predicate를 탐색 과정이나 graph 구조에 반영한다. ACORN, Filtered-DiskANN, UNG, SIEVE, Curator 등이 이 범주에 속한다.

- 장점: post-filter보다 견고하고 exact scan보다 빠를 수 있다.
- 단점: build cost, memory, predicate type, selectivity, workload knowledge에 대한 제약이 있다.

### 1.4 왜 selectivity만으로 부족한가

predicate의 global selectivity를 다음처럼 정의한다.

\[
s_p=\frac{|\{i:p(a_i)=1\}|}{N}
\]

두 predicate가 모두 10%의 데이터를 통과시켜도 질의 주변에서 valid item이 나타나는 방식은 다를 수 있다.

- 무작위 배치: top-100 중 약 10개가 valid다.
- local enrichment: top-100 중 40개가 valid다.
- local depletion: top-100 중 2개만 valid다.

post-filter가 100개만 확인한다면 첫 경우는 평균적이고, 두 번째는 쉽고, 세 번째는 매우 어렵다. 즉, 같은 selectivity라도 **query 주변의 local availability**가 달라지면 필요한 over-fetch 깊이와 recall이 달라진다.

### 1.5 왜 이 문제가 운영상 중요한가

filtered ANN 실패는 오류 메시지를 내지 않는다. 시스템은 그럴듯한 결과를 반환하지만 exact filtered top-(k) 일부가 빠져 있다. 문서 추천에서는 품질 저하일 수 있으나, 사건 영상·법률·의료 검색에서는 조건을 만족하는 핵심 증거의 누락이 될 수 있다.

그러나 “위험해 보인다”는 사실만으로 연구 신규성이 생기지는 않는다. 최신 hybrid index와 fallback이 이미 충분히 막는다면 남은 문제는 없을 수 있다. 따라서 연구는 **취약성을 전제하는 것이 아니라 최신 방법에서 잔존하는지를 시험**해야 한다.

---

## 2. “자연 상관”의 정확한 의미

### 2.1 자연이라는 말

여기서 `natural`은 상관의 크기나 방향을 뜻하지 않는다. **데이터와 predicate의 출처**를 뜻한다.

다음 조건을 만족할 때 자연 predicate workload라고 부를 수 있다.

1. 메타데이터가 benchmark를 어렵게 만들기 위해 embedding을 보고 인위적으로 붙인 label이 아니다.
2. 원 데이터 수집·업무 과정에서 시간, 위치, 범주, 저자, 태그 등이 기록되었다.
3. embedding은 원 콘텐츠로부터 생성되었다.
4. predicate 클래스는 성능을 본 뒤 고른 것이 아니라 schema/log 또는 사전 고정 규칙으로 열거되었다.
5. query와 predicate의 짝도 실제 query log 또는 사전 고정 생성 규칙을 따른다.

특히 5번이 중요하다. 상관은 dataset만의 속성이 아니라 **query–predicate workload의 속성**이다. 같은 `camera=A` subset도 어떤 질의와 결합하느냐에 따라 positive 또는 negative query correlation을 가질 수 있다.

### 2.2 상관보다 “자연 predicate–embedding 의존 구조”가 더 정확한 용어다

`상관`이라는 단어는 단일 Pearson 또는 Spearman coefficient를 떠올리게 하지만 실제 문제에는 여러 기하가 섞여 있다.

- query 주변 valid item의 enrichment/depletion
- predicate subset 자체의 내부 compactness 또는 multimodality
- global kNN graph에서 valid subset의 연결성
- exact filtered neighbor가 global vector ranking에서 나타나는 깊이
- 특정 index strategy가 요구하는 over-fetch cost

따라서 본 보고서는 상위 개념으로 **자연 predicate–embedding 의존 구조(natural predicate–embedding dependence)**를 사용한다. GLS, rank depth, conductance, α-hardness는 이 구조의 서로 다른 측정값이다.

### 2.3 GLS의 정의와 방향

[MoReVec/GLS 연구](https://arxiv.org/abs/2602.11443)는 global selectivity와 query의 exact (k)-NN 안에서의 local selectivity를 비교한다.

\[
\sigma_g=\frac{|\{i:p(a_i)=1\}|}{N}
\]

\[
\sigma_l(q,p)=\frac{|\{i\in N_k(q):p(a_i)=1\}|}{k}
\]

\[
r(q,p)=\frac{\sigma_l}{\sigma_g},\qquad
\rho_{GLS}(q,p)=\frac{r-1}{r+1}
\]

- (\rho_{GLS}=0): local 비율과 global 비율이 같음
- (\rho_{GLS}>0): local enrichment; valid item이 query 주변에 풍부함
- (\rho_{GLS}<0): local depletion; valid item이 query 주변에 부족함

예를 들어 (s_p=0.1)이고 top-100을 본다고 하자.

| top-100의 valid 수 | (sigma_l) | (r) | (\rho_{GLS}) | 일반적 난이도 |
|---:|---:|---:|---:|---|
| 10 | 0.10 | 1.0 | 0 | 중립 |
| 40 | 0.40 | 4.0 | +0.60 | 쉬워짐 |
| 2 | 0.02 | 0.2 | −0.67 | 어려워짐 |

MoReVec의 실험도 낮거나 음의 GLS에서 recall이 낮아지고 높은 GLS에서 recall이 높아지는 방향을 보고한다. [HCBGen](https://arxiv.org/abs/2606.14193) 역시 높은 query correlation은 보통 valid target이 query 주변에 모여 검색을 쉽게 한다고 설명한다.

### 2.4 내부 결과의 ρ는 GLS가 아니다

기존 KIISE 실험에서 보고된 값은 다음이다.

- 코퍼스 A: post-filter (\rho=0.699), IVF (\rho=0.780)
- 코퍼스 B: post-filter (\rho=0.616), IVF (\rho=0.895)

이 값은 다음 두 변수의 predicate-level Spearman correlation이다.

1. same-selectivity random control보다 실제 predicate에서 얼마나 recall이 더 낮았는가
2. exact filtered neighbor가 unfiltered global ranking에서 얼마나 깊게 있었는가

즉,

\[
\rho_{Spearman}(\text{recall deficit},\text{global rank depth})
\]

이지,

\[
\rho_{GLS}(\text{predicate},\text{embedding})
\]

가 아니다. 서로 측정 단위, 변수, 방향, 의미가 전부 다르다.

기존 계획서의 “CCTV 3코퍼스의 자연 상관 (\rho=0.62–0.895)”는 이 Spearman 값을 코퍼스의 GLS처럼 잘못 재해석한 것이다. 수정 후에는 다음처럼 써야 한다.

> 내부 두 코퍼스에서 실제 predicate의 random-control 대비 recall deficit은 exact filtered neighbor의 global rank depth와 양의 Spearman 연관을 보였다((\rho=0.616–0.895)). 이 결과는 local depletion/over-fetch hardness가 기전일 가능성을 지지하지만, predicate–embedding GLS 자체를 측정한 결과는 아니다.

### 2.5 “predicate가 군집한다”와 “query에 양의 상관이다”는 다르다

predicate를 만족하는 벡터가 embedding 공간의 한 섬에 서로 모여 있을 수 있다. 그러나 query가 그 섬 밖에 있다면 valid subset은 internally compact하면서도 query에는 멀다.

```text
query q ●    invalid neighbors ○○○○○

                         valid predicate cluster ●●●●●
```

이 경우:

- predicate subset의 내부 clustering은 강하다.
- query 주변 local availability는 낮다.
- query correlation/GLS는 음수일 수 있다.
- post-filter에는 어렵다.

따라서 “군집도가 높아서 recall이 무너진다”라는 문장도 불완전하다. **어떤 query에 대해 valid cluster가 어디에 있는지**가 필요하다.

### 2.6 이 연구에서 구분해야 할 다섯 지표

| 지표 | 무엇을 측정하는가 | 역할 | 같은 것으로 취급 가능한가 |
|---|---|---|---|
| global selectivity (s_p) | 전체 valid 비율 | 기본 난이도 | 아니오 |
| GLS (\rho_{GLS}(q,p)) | query 주변의 상대적 enrichment/depletion | signed local dependence | 아니오 |
| rank/over-fetch depth (alpha(q,p,k)) | (k)번째 valid item을 얻기 위해 global rank를 얼마나 내려가야 하는가 | post-filter 실행 난이도 | GLS와 관련되지만 동일하지 않음 |
| conductance | valid subset이 kNN graph에서 외부/내부와 어떻게 연결되는가 | graph traversal 난이도 | query-local 지표가 아님 |
| Spearman (\rho_{deficit,depth}) | predicate들 사이에서 결손과 rank depth가 함께 증가하는가 | 사후 연관 검증 | dependence magnitude 자체가 아님 |

앞으로는 모든 표와 그림에서 기호에 첨자를 붙여 혼용을 막아야 한다.

---

## 3. 내부 연구가 현재까지 실제로 보여 준 것

내부 정본은 [`EXP03_FILTERED_ANN_PHYSICAL_INDEX_AND_DEPLOYMENT.md`](../project_md/canonical/experiments/EXP03_FILTERED_ANN_PHYSICAL_INDEX_AND_DEPLOYMENT.md)다.

### 3.1 확증된 범위

두 CCTV 계열 코퍼스에서 각 실제 predicate와 통과 수가 같은 random mask를 짝지었다.

| 방법 | 코퍼스 A random−real recall | 코퍼스 B random−real recall |
|---|---:|---:|
| post-filter HNSW (K'=4k) | +0.611 | +0.289 |
| global IVF selector np8 | +0.627 | +0.217 |
| global IVF selector np32 | +0.498 | +0.116 |
| predicate subset HNSW | +0.017 | +0.004 |
| exact subset Flat | 0 | 0 |

허용되는 해석은 다음과 같다.

> 이 두 코퍼스와 잠긴 predicate 집합에서 same-selectivity random mask는 naive global post-filter/IVF 경로의 recall을 크게 낙관했다. exact/subset-local search는 이 차이에 거의 영향받지 않았다.

### 3.2 일반화할 수 없는 범위

이 결과만으로 다음은 말할 수 없다.

- 모든 자연 predicate가 random mask보다 어렵다.
- 높은 양의 correlation이 recall을 낮춘다.
- 텍스트·이미지·영상 전반에 같은 법칙이 있다.
- 최신 production engine도 모두 0.3–0.6의 recall 손실을 겪는다.
- correlation이 α-hardness보다 더 좋은 설명 변수다.

실제로 내부 engine replication에서는 robust path가 차이를 크게 줄였다.

- Weaviate sweeping A: +0.0098
- Milvus graph B: +0.0028
- brute-force fallback: 거의 0
- Weaviate ACORN B: 부호 역전 경향

이는 매우 중요하다. 내부 결과는 **현상이 보편적이라는 증거가 아니라 execution strategy에 따라 효과가 크게 달라진다는 증거**다. 이 결과는 [HCBGen](https://arxiv.org/abs/2606.14193)의 “correlation proxy가 strategy-inconsistent할 수 있다”는 주장과도 부합한다.

### 3.3 기존 결과의 가장 정직한 현재 지위

- 실재하는 현상: same-selectivity random label이 일부 global-search path를 과도하게 낙관할 수 있음
- 잠정 기전: valid exact neighbor가 global rank에서 깊어지는 local depletion/over-fetch
- 미검증: 그 기전이 공개 교차 도메인에서 일반적인가
- 미검증: 기존 α-hardness로 이미 충분히 설명 가능한가
- 미검증: 최신 robust method 선택 후에도 운영상 큰 잔여 위험이 있는가
- 미검증: 별도의 CORAL predictor가 기존 직접 측정/routing보다 비용상 유리한가

---

## 4. 관련 연구: 무엇이 이미 해결되었나

### 4.1 알고리즘과 failure mitigation

#### ACORN

[ACORN, SIGMOD 2024](https://arxiv.org/abs/2403.04871)는 이미 predicate clustering과 positive/negative query correlation을 정식화했다. post-filter가 낮은 selectivity와 낮거나 음의 query correlation에서 비싸진다고 설명하고, predicate subgraph traversal로 다양한 correlation regime에 견고한 index를 제안했다.

따라서 다음 주장은 불가능하다.

- filter–embedding correlation을 처음 발견했다.
- positive/negative correlation을 처음 정의했다.
- correlated predicate 때문에 post-filter가 실패한다는 것을 처음 보였다.

#### RACORN-1

[RACORN-1, 2026 preprint](https://arxiv.org/abs/2607.00768)는 low-selectivity에서 ACORN-1의 connectivity collapse를 다루고 transient bridge와 exact fallback으로 복구한다. K-means로 만든 negative-correlation 조건에서 ACORN-1의 recall 저하와 RACORN의 회복까지 보고한다.

즉, negative correlation과 graph connectivity failure 및 runtime fallback의 조합도 이미 직접 연구 중이다.

#### Curator·SIEVE·HONEYBEE

- [SIEVE, PVLDB 2025](https://arxiv.org/abs/2507.11907)는 workload에 맞춰 predicate용 sub-index collection을 선택한다.
- [Curator, SIGMOD 2026](https://arxiv.org/abs/2601.01291)는 low-selectivity filter를 위한 shared clustering tree 기반 specialized index를 만든다.
- [HONEYBEE, SIGMOD 2026](https://arxiv.org/abs/2505.01538)는 memory·latency·recall을 고려해 overlapping partition을 최적화한다.

따라서 partial/local index 또는 workload-aware physical design 자체도 신규하지 않다.

### 4.2 benchmark와 실험 연구

- [Unified FANNS Benchmark](https://arxiv.org/abs/2509.07789)는 알고리즘 분류, 공정한 parameter tuning, 실데이터 benchmark를 제공한다.
- [SIGMOD 2026 In-depth Study](https://arxiv.org/abs/2508.16263)는 10개 알고리즘·12개 방법·최대 10M 규모에서 pruning, entry point, edge filtering을 분석한다.
- [arxiv-for-fanns](https://arxiv.org/abs/2507.21989)는 270만 transformer embedding과 11개 real attribute를 공개한다.
- [VecBench, SIGMOD 2026](https://doi.org/10.1145/3802125)는 selectivity와 filter correlation을 제어하는 benchmark를 제공한다.

따라서 systematic benchmark, real attribute, correlation-controlled workload도 이미 연구되었다.

### 4.3 correlation과 hardness

#### MoReVec/GLS

[MoReVec/GLS](https://arxiv.org/abs/2602.11443)는 global–local selectivity로 query-filter dependence를 정량화하고, GLS가 recall의 query-level variance를 설명함을 보였다. correlation measurement는 이미 존재한다.

#### HCBGen/α-hardness

[HCBGen, PVLDB 2026](https://arxiv.org/abs/2606.14193)는 다음을 이미 수행한다.

- selectivity와 correlation만으로 query difficulty를 정렬하면 strategy에 따라 실패할 수 있음을 보임
- (k)번째 valid item을 얻기 위한 over-fetch를 중심으로 α-hardness를 정의
- global selectivity와 query-local valid density를 사용해 hardness를 추정
- 원하는 hardness profile을 갖는 synthetic workload 생성
- real workload의 hardness distribution을 synthetic proxy로 근사

이 논문은 CORAL의 직접적인 경쟁자가 아니라 **현재 자연 상관 중심 서사에 대한 반증 후보**다. CORAL은 HCBGen을 단순 baseline으로 넣는 수준을 넘어 다음을 물어야 한다.

> hardness distribution까지 맞춘 synthetic proxy가 natural workload의 engine ranking과 failure mechanism을 재현하는가?

재현한다면 “natural correlation이라는 별도 축이 필요하다”는 주장은 기각된다.

### 4.4 recall prediction과 routing

[Query-aware Routing, 2026](https://arxiv.org/abs/2606.19898)은 6개 학습 데이터와 5개 unseen validation data에서 candidate method별 query recall을 예측한다. 22개 후보 feature에는 distribution factor와 correlation ratio도 있었지만 최종 feature selection은 selectivity, dataset LID, predicate type 세 개를 선택했다.

이 결과는 CORAL에 양면적이다.

- 동기: 기존 학습 데이터가 고난도 natural-depletion regime를 충분히 포함하지 않았을 수 있다.
- 반증: correlation feature가 실제 routing에 추가 정보를 주지 못할 수 있다.

따라서 CORAL이 predictor를 만들려면 “우리 feature가 중요하다”고 가정하지 말고 nested ablation에서 실제 증분 예측력을 보여야 한다.

### 4.5 관련 연구 감사의 최종 판정

이미 점유된 것:

- correlation의 개념과 signed direction
- correlation-aware filtered search
- real metadata dataset
- controllable correlation benchmark
- execution-grounded hardness
- recall prediction과 cross-dataset routing
- workload-aware sub-index와 physical design
- low-selectivity fallback/repair

아직 가능성이 있으나 검증되지 않은 것:

1. 실제 업무에서 발생한 query–predicate pair의 dependence/hardness 분포를 여러 공개 도메인에서 측정한 대표성 연구
2. same-selectivity random과 hardness-matched synthetic가 natural workload의 method ranking을 각각 얼마나 재현하는지에 대한 정면 비교
3. target configuration을 전부 구축하지 않고도 현실적인 비용 이득을 보이는 configuration-level risk decision
4. 위 결과를 공개 영상/시공간 predicate까지 포함해 재현하는 artifact

이 네 항목이 바로 CORAL이 수행될 수 있는 유일한 이유다. 그러나 아직 어느 것도 확립된 사실은 아니다.

---

## 5. 우리가 이 연구를 해야 하는 이유와 하지 말아야 하는 이유

### 5.1 수행할 수 있는 과학적 이유

#### 이유 A: benchmark 외적 타당성

많은 benchmark는 real vector에 synthetic label을 붙이거나 query를 합성한다. 실제 업무에서는 metadata가 콘텐츠 생성 과정과 얽혀 있다. random filter와 hardness-controlled proxy 중 무엇이 실제 method ranking을 보존하는지 알면 benchmark 설계에 직접 기여할 수 있다.

#### 이유 B: metric 간 관계 규명

GLS, over-fetch depth, graph conductance, α-hardness가 어떤 조건에서 서로 같은 정보를 주고 어떤 조건에서 갈라지는지 아직 분명하지 않다. natural workload는 이 관계를 검증하는 외부 시험대가 될 수 있다.

#### 이유 C: 최신 엔진에서의 잔여 위험

내부 결과에서 robust path는 큰 손실을 대부분 막았지만 pgvector 일부 location predicate에는 recall/latency 문제가 남았다. 어떤 execution family가 어떤 dependence regime에서 안전한지 정리하면 실무적 가치가 있다.

#### 이유 D: 구축 전 의사결정 비용

Query-aware Routing은 target dataset×predicate type×method×parameter의 offline benchmark table을 사용한다. 후보가 많을 때 이 table을 만드는 비용이 크다면, 저비용 corpus profile로 후보를 줄이는 pre-screening은 의미가 있을 수 있다.

### 5.2 수행하지 말아야 할 조건

다음 중 하나가 나오면 현재 CORAL을 중단하거나 대폭 축소해야 한다.

1. HCBGen α-hardness가 natural-vs-random 차이와 engine ranking을 충분히 설명한다.
2. hardness-matched synthetic workload가 natural workload 결과를 실용적으로 같은 수준으로 재현한다.
3. ACORN/RACORN/Milvus/Weaviate/Curator 계열에서 자연-합성 차이가 SLA에 영향을 주지 않는다.
4. 공개 데이터에서는 내부 CCTV와 같은 regime가 관측되지 않아 결과가 private case study에 머문다.
5. configuration-level recall을 예측하려면 결국 configuration별 target index를 거의 모두 구축해야 한다.
6. direct sample-GT measurement 또는 Query-aware Routing보다 advisor의 총비용이 낮아지는 현실적 crossover가 없다.
7. target conformal lower bound가 너무 넓어 모든 configuration을 위험하다고 판단한다.

### 5.3 현재 권고

**전체 연구 실행 권고: 보류**  
**P0 타당성 감사 실행 권고: 예**

이유는 내부 결과에 흥미로운 real-vs-random 차이는 있으나, 그 차이의 정의가 잘못 명명되었고 기존 HCBGen·Query-aware Routing·RACORN과의 차별성이 아직 입증되지 않았기 때문이다.

---

## 6. 수정된 문제 정의

### 6.1 데이터와 workload

데이터:

\[
D=\{(x_i,a_i)\}_{i=1}^{N}
\]

- (x_i\in\mathbb{R}^{d}): embedding
- (a_i): metadata

질의 workload:

\[
W=\{(q_v,p,k)\}
\]

- (q_v): query embedding
- (p): metadata predicate
- (k): 결과 수

중요하게도 연구 대상은 (D)만이 아니라 joint distribution (P(q_v,p\mid D))다.

### 6.2 configuration

\[
c=(\text{engine},\text{index},\text{filter strategy},\theta)
\]

예:

- FAISS HNSW post-filter, efSearch=64, (k'=4k)
- ACORN-(\gamma)
- Milvus graph/fallback
- pgvector HNSW iterative scan
- IVF nprobe=32
- predicate-local HNSW

### 6.3 측정 문제

각 query–predicate pair에서 다음 feature vector를 정의한다.

\[
z(q,p,D)=
[s_p,\rho_{GLS},\alpha,\text{rank-depth},\text{conductance},\text{LID},N,d]
\]

측정 질문:

> natural workload의 (z) 분포는 random-mask 또는 hardness-matched synthetic workload와 어떻게 다르며, 그 차이가 configuration별 recall–latency 순위를 바꾸는가?

### 6.4 예측 문제

\[
\hat R=f(z,c)
\]

단, “pre-build” 주장은 두 버전으로 분리해야 한다.

#### Version A: strict pre-build empirical predictor

- target configuration index를 구축하지 않는다.
- 다른 corpus/configuration에서 학습한 모델과 target의 index-free profile만 사용한다.
- cross-domain empirical accuracy만 주장한다.
- target-specific conformal guarantee는 주장하지 않는다.

#### Version B: build-frugal calibrated predictor

- target corpus의 작은 sample 또는 축소 index를 configuration별로 구축한다.
- 그 proxy result로 target residual을 보정한다.
- sample-to-full-scale transfer를 별도로 검증한다.
- 전체 index build보다 싸다는 cost crossover를 입증한다.
- 이 경우 명칭은 `pre-build`보다 `proxy-build calibrated` 또는 `build-frugal`이 정확하다.

### 6.5 결정 문제

SLA를 recall (r^*), latency (ell^*), memory (m^*)로 두면 다음 결정을 찾는다.

\[
c^*=\arg\min_{c\in C}\ \text{TotalCost}(c)
\]

subject to

\[
P(R(q,p,c)\ge r^*)\ge1-\alpha,
\quad L(c)\le\ell^*,
\quad M(c)\le m^*
\]

여기서 TotalCost에는 반드시 다음이 포함되어야 한다.

- profile 계산
- exact GT probe
- proxy/full index build
- benchmark table 생성
- query execution
- SLA 위반 비용
- overprovisioning 비용
- partial index 유지·갱신 비용

---

## 7. 수정 연구 질문

### RQ1: 자연 dependence의 존재와 방향

> 공개 text/image/video corpus의 사전 고정 query–predicate workload에서 GLS, local availability, over-fetch depth, conductance는 어떤 분포를 가지는가?

이 질문은 “높은 상관이 있는가”가 아니라 positive, neutral, negative regime이 각각 얼마나 있는지를 묻는다.

### RQ2: benchmark 대표성

> same-selectivity random, correlation-controlled synthetic, hardness-matched HCBGen 중 어느 proxy가 natural workload의 recall–latency와 method ranking을 가장 잘 재현하는가?

### RQ3: 독립 설명력과 기전

> selectivity와 α-hardness를 조건화한 뒤 GLS/conductance가 configuration별 residual failure를 추가로 설명하는가?

### RQ4: 최신 방법의 잔여 취약성

> naive post-filter뿐 아니라 ACORN/RACORN/UNG/Curator/Milvus/Weaviate/pgvector의 최신 경로에서 어떤 dependence regime이 SLA 위반을 남기는가?

### RQ5: 저비용 구축 결정

> strict pre-build 또는 proxy-build profile이 직접 측정과 Query-aware Routing보다 낮은 총비용으로 configuration 선택을 수행하는 현실적 영역이 존재하는가?

RAG/VLM propagation은 위 RQ1–RQ5가 통과한 후 별도 후속 연구로 둔다. 현재 문제 정의에는 필요하지 않다.

---

## 8. 상세 실험 설계

### 8.1 Phase P0 — 정의 및 타당성 감사

### P0-1 내부 수치 재명명·재계산

기존 두 코퍼스의 모든 query–predicate pair에 대해 다음을 다시 계산한다.

- (s_p)
- GLS at (k\in\{10,50,100,1000\})
- (k)번째 valid item의 global rank (alpha_{exact})
- distance-ratio α-hardness
- valid-subgraph conductance
- subset compactness와 component 수
- method별 Recall@10, latency, short-result rate

필수 산출:

1. `ρ_GLS`, `ρ_Spearman` 기호 분리
2. positive/negative GLS별 recall curve
3. rank depth와 GLS/α-hardness 관계
4. query family와 predicate family별 분포

중단 기준:

- 기존 `0.616–0.895` 외에 실제 GLS 또는 hardness 차이가 확인되지 않으면 기존 natural-correlation 서사를 폐기한다.

### P0-2 공개 데이터 2개 최소 복제

후보:

- text: arxiv-for-fanns 또는 MoReVec
- image: YFCC real tags
- video: 공개 가능 MIRIS/기타 영상 embedding은 보조

최소 두 개의 공개 corpus에서 schema 기반 predicate를 사전 잠근다. 성능을 본 후 어렵거나 쉬운 predicate만 고르지 않는다.

### P0-3 세 workload arm

각 natural pair에 다음 대조를 만든다.

1. **Natural**: 원 metadata와 사전 고정 query–predicate pair
2. **Same-selectivity random**: valid count만 같은 random mask
3. **Hardness-matched synthetic**: HCBGen 방식으로 α-hardness distribution을 맞춘 proxy

가능하면 네 번째로 GLS-matched but hardness-unmatched arm을 추가한다. 이것이 correlation과 hardness를 분리한다.

### P0-4 최소 방법군

- exact subset Flat
- naive HNSW post-filter
- global IVF selector
- ACORN-(\gamma) 또는 최신 공식 구현
- RACORN-1/정확 fallback 가능 시
- 한 production engine의 robust path

P0 통과 기준:

1. natural과 random의 차이가 공개 corpus에서도 SLA 관점에서 실질적이다.
2. hardness matching 후에도 method ranking 또는 residual recall 차이가 남는다.
3. 그 차이가 최신 robust method 하나 이상에서 남는다.

세 조건 중 2번과 3번이 실패하면 “natural dependence가 별도 연구 축”이라는 CORAL은 중단한다.

### 8.2 Phase P1 — 자연 dependence spectrum benchmark

### 데이터 설계

| modality | 후보 corpus | metadata | 목적 |
|---|---|---|---|
| text | arxiv-for-fanns 2.7M | author/category/year | large public real attribute |
| text/relational | MoReVec | IMDb scalar/category/join | GLS 비교와 relational engine |
| image | YFCC 100K/1M/10M | user tag/time/location | scale와 multi-label |
| video | 공개 영상 embedding | scene/time/camera | spatiotemporal replication |
| internal case | CCTV A/B | location/date/hour/sensor | 기존 effect 재검증 |

`멀티모달`이라는 표현은 알고리즘이 cross-modal fusion을 하지 않으므로 “text/image/video corpora에 걸친 modality-agnostic evaluation”으로 한정한다.

### predicate registry

predicate마다 다음을 사전에 기록한다.

- source column과 의미
- equality/range/set operator
- valid count/selectivity
- query와 결합되는 규칙
- 업무상 정당성
- overlap/hierarchy family
- 공개 가능 여부

### query–predicate pairing

다음 세 방식의 우선순위를 둔다.

1. 실제 query log pair
2. 원 데이터의 query/label 관계로 정의된 pair
3. 사전 고정된 factorial pairing

무작위로 query와 predicate를 결합한 것을 natural workload라고 부르면 안 된다.

### 8.3 Phase P2 — 인과 및 기전 실험

### 실험 P2-A: permutation total effect

동일 corpus에서 metadata assignment를 부분 치환한다.

\[
\lambda\in\{0,0.25,0.5,0.75,1\}
\]

- (lambda=0): natural assignment
- (lambda=1): 완전 random assignment

보존:

- embedding
- query
- predicate count/selectivity
- engine/index parameter

변화:

- GLS
- rank depth
- conductance
- α-hardness

따라서 이 실험은 **dependence structure 전체의 total effect**를 식별하지만 GLS 하나의 인과효과를 식별하지는 않는다.

### 실험 P2-B: signed regime control

positive enrichment, neutral, negative depletion을 명시적으로 생성한다. 같은 selectivity에서 query 주변 valid density를 조절한다.

목적:

- GLS sign과 recall 방향 검증
- 기존 계획의 “positive correlation collapse” 오류 방지
- engine별 response curve 측정

### 실험 P2-C: hardness matching

natural과 synthetic pair의 α-hardness를 맞춘 뒤 결과를 비교한다.

- 성능 차이가 사라짐: hardness가 충분한 설명
- 성능 차이가 남음: graph topology/conductance 또는 다른 natural structure가 필요

### 실험 P2-D: mechanism tracing

engine별로 다음을 로그한다.

- visited nodes/candidates
- valid/invalid queue occupancy
- entry-point-to-valid-region distance
- valid-subgraph component/connectivity
- over-fetch depth
- fallback 발생 여부
- exact scan 전환 임계

평균 Recall@10 표만으로는 기전 논문이 되지 않는다.

### 8.4 Phase P3 — 예측기 검증

### 모델 비교

| 모델 | feature |
|---|---|
| B0 | selectivity only |
| B1 | selectivity + dataset LID + predicate type; Query-aware Routing 최소 feature 대응 |
| B2 | α-hardness only |
| B3 | GLS/local availability only |
| B4 | α-hardness + conductance/topology |
| Full | B1+B2+B3+B4+configuration encoding |

### 평가 분할

- leave-one-domain-out
- leave-one-predicate-family-out
- leave-one-engine-family-out는 engine 수가 충분할 때만 탐색적
- permutation variant는 원 natural parent와 반드시 같은 fold에 둔다.
- 동일 query 또는 겹치는 predicate가 train/test에 걸치지 않도록 group split한다.

### 지표

- Recall MAE/RMSE
- SLA violation AUROC와 precision–recall
- calibration error
- method/configuration ranking regret
- 선택된 configuration의 실제 SLA violation과 비용

### 유효한 성공 기준

통계적 유의성만으로는 부족하다. 사전 정의한 최소 실질 효과(SESOI)가 필요하다.

권장 예:

- Full이 B2(α-hardness) 대비 grouped-CV MAE를 상대 10% 이상 줄이고 bootstrap CI가 0을 배제
- SLA violation AUROC 또는 AUPRC가 B2 대비 사전 정의한 실질 폭 개선
- configuration decision regret가 best baseline보다 10% 이상 감소

정확한 수치는 P0의 variance와 업무 SLA 비용을 이용해 확정한다.

### 8.5 Phase P4 — 불확실성과 conformal

### 선택지 A: strict pre-build

- target configuration label 없음
- source-domain calibration만 사용
- distribution shift에서 formal target guarantee를 주장하지 않음
- empirical coverage만 보고

### 선택지 B: proxy-build target calibration

- target corpus 100K/1M sample에서 configuration별 index build
- actual recall residual로 target calibration
- 10M full-scale에 대한 scale transfer 검증
- 보장은 sample/full exchangeability와 calibration design 범위로 한정

### coverage 단위

predicate가 중첩·계층·시간 인접성을 가지므로 단순 iid class assumption을 쓰지 않는다.

- predicate family를 block으로 사용
- calibration/test를 family 단위로 분리
- marginal coverage와 family-wise simultaneous coverage를 구분
- 하한 폭과 `SLA 결정을 실제 바꾸는 비율`을 함께 보고

### 실패 기준

- 95% target coverage가 허용 오차를 벗어남
- median bound width가 SLA 판단에 쓸 수 없을 정도로 큼
- target label을 얻는 비용이 full benchmark table 비용에 근접

실패 시 conformal contribution을 삭제한다.

### 8.6 Phase P5 — physical-design decision

### 후보 행동

- global index 유지
- efSearch/nprobe 상향
- robust filtered method로 routing
- predicate-local/partial index 구축
- exact scan/fallback

### baseline

- direct sample-GT measurement
- selectivity threshold heuristic
- α-hardness rule
- Query-aware Routing
- SIEVE/Curator cost decision
- oracle

### cost crossover

다음 두 비용을 비교한다.

\[
C_{direct}(P,C)=\sum_{c=1}^{C}\text{full build}_c+\text{measure}(P,C)
\]

\[
C_{CORAL}=\text{profile}+\text{proxy builds}+\text{prediction}+\text{error cost}
\]

현실적 (P\times C) 영역에서 (C_{CORAL}<C_{direct})이면서 SLA violation이 비열등해야 한다.

이 crossover가 없으면 advisor 논문을 중단한다.

---

## 9. 통계 설계

### 9.1 분석 단위

기본 단위는 query–predicate–configuration이다. 동일 predicate의 여러 query와 동일 query의 여러 configuration은 독립이 아니다.

### 9.2 1차 estimand

#### Natural 대 random

\[
\Delta_R(c)=E[R_{natural}(q,p,c)-R_{random}(q,p,c)]
\]

같은 query, selectivity, configuration의 paired difference다.

#### Natural 대 hardness-matched

\[
\Delta_H(c)=E[R_{natural}-R_{HCBGen\ matched}]
\]

(Delta_H\approx0)이면 natural geometry가 hardness 너머에 추가 정보를 주지 않는다는 쪽의 증거다.

#### Feature incremental value

\[
\Delta MAE=MAE_{\alpha-only}-MAE_{full}
\]

### 9.3 모델

Recall@k는 (k)개 정답 중 찾은 개수이므로 query-level count로 다룰 수 있다. configuration interaction과 반복 측정을 고려한 mixed-effects/binomial 또는 cluster bootstrap을 사용한다.

예시:

\[
\text{logit}(E[R])=
\beta_0+f(\log s)+\beta_1\rho_{GLS}+f(\log\alpha)
+\beta_2 conductance+\text{configuration interactions}
+u_{domain}+u_{predicate}
\]

단, 목적이 예측이면 flexible learner와 grouped nested CV를 주 분석으로 두고 mixed model은 해석 보조로 사용한다.

### 9.4 불확실성

- query bootstrap이 아니라 predicate/domain cluster bootstrap을 우선
- latency는 warm-up과 반복 순서 무작위화
- seed별 index rebuild
- effect size와 CI를 중심으로 보고
- method×dataset 다중 비교는 Holm 또는 hierarchical testing
- threshold를 사후 선택하지 않음

### 9.5 검정력

내부 두 코퍼스의 predicate-level variance를 이용해 simulation-based power analysis를 한다. 단, 큰 naive-method 효과를 기준으로 표본 수를 정하면 robust method의 작은 효과를 놓치므로, 실제 1차 목표는 robust method에서 SLA-relevant effect를 검출하도록 정한다.

---

## 10. 결과에 따른 연구 및 논문 판정

| 결과 | 과학적 결론 | 다음 행동 |
|---|---|---|
| Natural≠random, Natural≈hardness-matched | random mask는 부적절하지만 α-hardness proxy는 충분 | HCBGen 확장/검증 논문으로 축소; CORAL correlation 축 중단 |
| Natural≠hardness-matched, topology가 residual 설명 | 자연 graph structure가 hardness 너머에 필요 | EA&B benchmark 진행 가치 있음 |
| 차이는 naive method에만 있고 최신 method에서는 SLA 무관 | 과거 baseline의 문제 | 최상위 시스템 논문 중단; engineering note/case study |
| 공개 다중 도메인·최신 method에서도 큰 잔여 차이 | 미해결 외적 타당성 문제 | CORAL L1/L2 진행 |
| predictor가 α-hardness/Query-aware보다 못함 | 별도 advisor 불필요 | L3 삭제 |
| predictor는 우수하나 cost crossover 없음 | 측정이 더 실용적 | advisor 삭제 또는 diagnostic tool로 축소 |
| strict pre-build가 경험적으로 전이되고 의사결정 우수 | 강한 시스템 결과 | 단, formal target guarantee 없이 보고 |
| proxy-build calibration이 싸고 informative coverage 달성 | build-frugal advisor 성립 | L3 가능 |
| RQ1–RQ4 실패, VLM 효과만 존재 | 별도 RAG 문제 | CORAL과 분리 |

### 논문 수준 판단

#### PVLDB EA&B 가능

- 공개 3개 이상 domain/양식
- natural, random, hardness-matched workload 비교
- 최신 method/engine의 ranking 또는 failure 차이
- metric·mechanism analysis와 대규모 artifact
- negative result까지 일관된 benchmark 교훈 제공

#### SIGMOD/VLDB research 가능

위 조건에 더해:

- 새로운 predictor/decision algorithm이 강한 baseline보다 우수
- 비용 crossover가 명확
- 시스템 구현과 scale/updates 평가
- 이론/보장의 범위가 정확

#### 축소가 필요한 경우

- CCTV 두 코퍼스만 재현
- naive post-filter에서만 큰 효과
- α-hardness가 모두 설명
- target calibration 비용이 full build와 유사

이 경우 국내 저널 확장 또는 공개 benchmark note가 적절하다.

---

## 11. 실행 순서와 의사결정 게이트

### 2–3주 P0만 먼저 수행

1. 내부 (0.616–0.895)를 Spearman으로 재명명하고 GLS를 실제 계산한다.
2. internal natural/random/hardness-matched 세 arm을 비교한다.
3. 공개 text와 image corpus 각각 하나에서 최소 복제한다.
4. naive path와 ACORN/robust path를 함께 측정한다.
5. α-hardness-only와 full dependence feature의 grouped-CV를 돌린다.
6. target conformal label을 얻는 데 필요한 실제 build 목록과 비용을 작성한다.

### Gate G1: 자연 구조의 독립 가치

- hardness matching 뒤에도 실질적 차이가 남는가?
- 아니오 → CORAL 자연 상관 축 중단

### Gate G2: 최신 방법의 잔여 문제

- robust method에서도 SLA-relevant gap이 남는가?
- 아니오 → 시스템 reliability 논문 중단

### Gate G3: 공개 일반성

- 공개 corpus 둘 이상에서 재현되는가?
- 아니오 → CCTV case study로 축소

### Gate G4: advisor feasibility

- α-hardness/Query-aware보다 예측과 결정이 낫고 cost crossover가 있는가?
- 아니오 → advisor 삭제

### Gate G5: calibration feasibility

- target label cost를 포함해도 proxy-build가 full benchmark보다 싼가?
- 아니오 → target conformal 삭제

---

## 12. 최종 권고 문구

### 더 이상 사용하면 안 되는 문장

> “자연 상관이 높을수록 filtered ANN recall이 붕괴한다.”

> “CCTV의 자연 상관은 ρ=0.62–0.895다.”

> “기존 실제 데이터는 전부 무상관이고 CORAL이 처음 자연 상관을 연구한다.”

> “인덱스를 구축하지 않고 target-calibrated configuration별 conformal 하한을 보장한다.”

### 현재 사용할 수 있는 문장

> 내부 두 CCTV 계열 corpus에서, 사전 고정 real predicate는 같은 selectivity의 random mask보다 naive global post-filter/IVF 검색을 크게 어렵게 했다. 이 차이는 exact filtered neighbor의 global rank depth와 연관되었으나, 최신 robust engine path에서는 크게 완화되거나 방향이 달라졌다. 따라서 후속 연구의 목적은 “높은 자연 상관의 보편 법칙”을 전제하는 것이 아니라, query-local depletion·over-fetch hardness·graph topology 중 무엇이 real-vs-synthetic 차이를 설명하며 최신 방법 선택에 추가 정보를 주는지를 공개 다중 도메인에서 반증 가능하게 시험하는 것이다.

### 연구를 계속할 경우 권장 제목

> **Do Natural Filter Workloads Matter Beyond Hardness? A Cross-Domain Evaluation of Filtered Vector Search**

이 제목은 결론을 미리 단정하지 않고 HCBGen과 정면으로 대화하며, negative result도 수용한다.

---

## 13. 핵심 1차 문헌

- Patel et al., [ACORN: Performant and Predicate-Agnostic Search Over Vector Embeddings and Structured Data](https://arxiv.org/abs/2403.04871), SIGMOD 2024.
- Li et al., [SIEVE: Effective Filtered Vector Search with Collection of Indexes](https://arxiv.org/abs/2507.11907), PVLDB 2025.
- Shi et al., [Filtered ANN Search: A Unified Benchmark and Systematic Experimental Study](https://arxiv.org/abs/2509.07789), 2025.
- Li et al., [Attribute Filtering in ANN Search: An In-depth Experimental Study](https://arxiv.org/abs/2508.16263), SIGMOD 2026.
- Iff et al., [Benchmarking FANNS on Transformer-based Embedding Vectors](https://arxiv.org/abs/2507.21989), SIGIR 2026.
- Amanbayev et al., [Filtered ANN Search in Vector Databases / MoReVec and GLS](https://arxiv.org/abs/2602.11443), 2026.
- Zhang et al., [VecBench](https://doi.org/10.1145/3802125), SIGMOD 2026.
- Lim et al., [HCBGen and α-Hardness](https://arxiv.org/abs/2606.14193), PVLDB 2026.
- Xiong and Zhang, [Query-aware Routing for Filtered ANN Search](https://arxiv.org/abs/2606.19898), 2026.
- Kim and Choe, [RACORN-1](https://arxiv.org/abs/2607.00768), 2026.
- Jin et al., [Curator: Efficient Vector Search with Low-Selectivity Filters](https://arxiv.org/abs/2601.01291), SIGMOD 2026.
- Zhong et al., [HONEYBEE](https://arxiv.org/abs/2505.01538), SIGMOD 2026.

---

## 14. 최종 한 문장 판정

> **현재 CORAL은 수행이 확정된 연구가 아니라, 잘못 혼용된 상관 정의를 바로잡고 “natural workload가 α-hardness 너머에 실제로 추가 정보를 주는가”를 먼저 검증해야 하는 조건부 연구 후보이며, P0에서 그 답이 ‘아니오’이면 수행하지 않는 것이 맞다.**
