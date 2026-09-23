# 913 — 통제 보강 실험 결과 및 심사 대응 판정

- 기준 프로토콜: `project_md/912_SUPPLEMENT_CONTROL_PROTOCOL_FROZEN_20260723.md`
- 판정용 산출물: `paper_assets/20260723_controlled_supplement/`
- 원칙: 후속 보강 실험이며 원 연구의 사전등록으로 표현하지 않는다. gate 실패도 성공 결과와 같은 수준으로 보존·보고한다.

## 1. 현재 결론

1. **RQ5 군집 기전은 보강 성공**: 선택도를 정확히 고정한 라벨 셔플 음성 대조와 합성 군집 농도-반응 양성 대조가 2개 코퍼스×2개 색인에서 모두 통과했다. 따라서 검증 범위를 “두 CLIP 코퍼스의 postfilter HNSW·IVF-Flat”으로 한정하면, 군집 집중이 재현율 손실을 유발한다는 기전 표현이 가능하다.
2. **RQ3 고결합 일반화는 승격 불가**: 교차로를 5-fold로 완전히 분리해도 고결합 방향은 5/5 fold에서 양수였지만, 고결합 family 수가 5개 미만이다. 현 원고의 “탐색적, 2쌍 한정”을 유지한다.
3. **ANN→답변 대규모 호출은 중단이 정답**: 편향을 줄인 3지선다 답변 실험에 앞서 top-1 task-label 조작을 확인했으나 exact−strong 차이가 bus +0.8%p, bike −1.1%p였다. 사전 5%p 조작 gate를 모두 실패했으므로 VLM을 호출하지 않았다. 현재 병목은 표본 수가 아니라 **과제 관련 검색 처치의 부재**다.
4. **E0 프롬프트-표적 결합은 중대한 민감 요인**: 동일한 3,000개 프레임·모델 snapshot·디코딩·질의·정답표·BGE-M3·정확 검색에서 프롬프트만 과제-중립형으로 바꾸자 B2 의미론적 nDCG@10이 0.1700에서 0.0855로 49.7% 하락했다. 따라서 직접 정답 재사용을 차단했다는 사실을 프롬프트 중립성으로 확대하면 안 된다.

## 2. E0 — 과제-중립 캡션 프롬프트 대조

- 같은 3,000개 중간 프레임, Qwen2.5-VL-7B snapshot, `max_pixels=200704`, `max_new_tokens=110`, greedy decoding을 고정했다.
- 질의 85개, 25개 `(predicate, relevance_def)` family, semantic qrels, 기존 질의 벡터, BGE-M3 snapshot, L2 정규화와 exact inner-product 검색을 양 조건에서 동일하게 사용했다.
- 1차 결과인 B2 의미론적 nDCG@10은 과제-인지 `0.1700`, 과제-중립 `0.0855`, 차이 `−0.0845`였다.
- family-cluster bootstrap 95% CI는 `[−0.1672, −0.0044]`, family-cluster sign-flip 양측 `p=0.0346`이었다.
- 질의별 과제-중립 승/동률/패는 `20/18/47`, 상대 하락은 `49.7%`였다.
- 빈 캡션은 양 조건 모두 0건이었다. 과제-인지/중립 캡션의 평균 Qwen token 수는 `73.9/93.9`, 110-token 이상 진단 건수는 `11/507`이었다. 길이와 잘림 가능성은 프롬프트 처치가 만든 매개이므로 주 추정량에서 사후 보정하지 않았다.
- 과제 범주별 문서 출현률은 과제-인지/중립에서 bus `0.974/0.338`, truck `0.870/0.154`, two-wheeler `0.970/0.053`, stopped-or-parked `0.992/0.618`로 감소했다.

**판정**: 본 작업 부하는 정답 주석의 직접 재사용을 차단하지만, 과제 범주를 열거한 캡션 프롬프트에 강하게 의존한다. E0은 어떤 단일 매개가 하락을 만들었는지 분해하지 않으므로 “범주 단어가 성능을 인과적으로 높였다”까지 주장하지 않는다. 허용되는 표현은 “이 결과는 과제-인지 프롬프트 조건부이며 프롬프트 비의존적이지 않다”이다.

## 3. S2 — 교차로 차단 결합도

- 63개 `intersection_id`를 결과와 무관한 안정 hash로 5-fold 배정했다.
- 각 fold에서 Cramér's V는 나머지 4-fold에서만, B4−B2 semantic nDCG@10은 held-out 교차로에서만 계산했다.
- 85질의×5-fold 425개 중 407개가 고정 support gate를 통과했다. 제외는 semantic positive 부족 12개, B4 후보 부족 6개다.
- 연속 V와 held-out Δ의 Spearman ρ는 `0.383`, 양측 `p=0.059`, family bootstrap 95% CI `[-0.088, 0.727]`이다.
- high fold 평균 Δ는 `+0.139, +0.111, +0.283, +0.218, +0.147`로 5/5 양수였다.
- 그러나 유효 high family 수가 사전 기준 5개에 못 미쳐 promotion gate는 실패했다.

**판정**: 동일 교차로 누출을 막아도 방향은 유지되지만, 지지 family 수 부족은 해소되지 않았다. “강한 결합에서 사전필터가 일반적으로 유의하게 우세하다”는 문구는 금지한다.

## 4. S3 — 선택도 보존 군집 기전

### 4.1 설계

- 자연 predicate: 코퍼스 A 24개, B 22개.
- 음성 대조: 각 predicate에서 통과 수를 bit 수준으로 동일하게 유지한 uniform label shuffle 100회.
- 양성 대조: 선택도 `0.05/0.10/0.20/0.40`×집중도 `0/0.25/0.5/0.75/1`×anchor 10개.
- 색인: postfilter HNSW `M=32, efConstruction=200, efSearch=64, K'=4K/s`; IVF-Flat `nlist=1024, nprobe=8, IDSelectorBatch`.
- exact subset GT와 query-level 결과를 보존했다.

### 4.2 결과

| 코퍼스·색인 | 자연 손실−shuffle 손실 [predicate-bootstrap 95% CI] | 농도-손실 기울기 [anchor-bootstrap 95% CI] | gate |
|---|---:|---:|---|
| A·HNSW | +0.639 [0.592, 0.686] | +0.521 [0.501, 0.541] | 통과 |
| A·IVF-Flat | +0.677 [0.609, 0.741] | +0.424 [0.405, 0.446] | 통과 |
| B·HNSW | +0.305 [0.231, 0.381] | +0.465 [0.442, 0.490] | 통과 |
| B·IVF-Flat | +0.234 [0.158, 0.316] | +0.349 [0.322, 0.378] | 통과 |

- 자연−shuffle 차이는 A의 24/24 predicate, B HNSW의 22/22, B IVF의 21/22에서 양수였다.
- 100회 permutation은 24개 개별 predicate Holm 검정에 충분한 최소 p 해상도를 주지 않으므로, 개별 Holm p가 아니라 사전 지정한 predicate-level aggregate gate를 1차 판정으로 사용했다.
- 시각화: `s3_cluster_mechanism/s3_selectivity_preserving_controls.png`.

**허용되는 주장**: “두 고정 CLIP 코퍼스와 시험한 postfilter HNSW·IVF-Flat 구성에서, 선택도를 고정한 상태의 embedding-space 군집 집중은 재현율 손실을 인과적으로 증가시켰다.”

**금지되는 확대**: 모든 ANN 구현, encoder, 데이터셋, predicate, 운영 부하에 대한 보편 인과 법칙.

## 5. S4 — 편향 억제 답변 전파 gate

### 5.1 문항과 장면 통제

- yes/no를 버리고 `bus_count`, `bike_count`의 `0/1/2+` 3지선다를 사용한다.
- category별 180개(클래스별 60개) oracle/distractor/closed 계획을 생성했다.
- distractor 360건 중 359건은 source와 같은 `intersection_id×hour`의 다른 class frame, 1건은 같은 intersection의 다른 class frame이다.
- 보기 순서는 item hash로 6개 순열에 균형 배정했다.

### 5.2 검색 조작 gate

- 원 E1A seed·중간 frame 규칙으로 2,967개 source를 재구성했다.
- 최초 3,000개 video 중 중간 frame 규칙을 적용할 frame이 부족한 33개를 먼저 제외해 2,967개 source를 재구성했고, 이 중 TL_3 source가 없는 228개를 결과와 무관하게 제외하여 2,739개를 분석했다.
- source와 retrieval corpus를 모두 TL_3 count annotation이 있는 133,977 frame으로 고정했다.

| category | exact class-match | strong class-match | exact−strong [교차로 bootstrap 95% CI] | exact-hit/strong-miss | gate |
|---|---:|---:|---:|---:|---|
| bus | 0.7605 | 0.7525 | +0.0080 [−0.0102, +0.0271] | 288 | 실패 |
| bike | 0.7101 | 0.7211 | −0.0110 [−0.0308, +0.0083] | 307 | 실패 |

두 category 모두 불일치 층의 수는 충분했지만 원 분포의 검색 조작 크기가 5%p 기준에 못 미쳤다. 프로토콜에 따라 InternVL3 gate와 full answer generation을 실행하지 않았다.

**판정**: 기존 원고의 “ANN 검색 차이가 답변으로 자동 전파되지 않았다”는 결론을 유지한다. 후속 실험의 첫 과제는 VLM 표본 확대가 아니라, 별도 development intersection에서 task-relevant evidence 조작을 선택하고 held-out intersection에서 그 조작을 검증하는 것이다.

## 6. 원고 반영 원칙

- S2는 표 5의 탐색적 한계를 유지하는 보조 근거로만 쓴다.
- S3는 RQ5의 “직접 조작 미실시” 한계를 해소하되 범위를 postfilter HNSW·IVF-Flat과 두 코퍼스로 한정한다.
- S4는 실패 결과와 중단 사유를 함께 보고하고, “표본만 늘리면 된다”는 표현을 “과제 관련 검색 조작이 먼저 성립해야 한다”로 바꾼다.
- E0에 따라 비순환성의 의미를 “직접 정답 정보 재사용 차단”으로 한정하고, 캡션 기반 절대 성능과 데이터베이스 설계 비교가 과제-인지 프롬프트 조건부임을 초록·방법·한계·결론에 공시한다.
- E0은 프롬프트 전체를 처치했으므로 범주 열거, 출력 길이, 잘림 가능성 중 어느 한 매개에 하락을 단독 귀속하지 않는다.
