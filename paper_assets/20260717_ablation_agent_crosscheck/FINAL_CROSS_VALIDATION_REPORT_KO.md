# Ablation study 다중 에이전트 교차검증 최종 보고서

- 완료일: 2026-07-17 KST
- 최종 판정: **PASS_WITH_LIMITATIONS**
- 외부 감사: `agy`와 Claude가 서로 독립적으로 동일 판정
- 치명적 설계 오류: 두 감사 모두 없음
- 의미: ablation 결과는 논문에 사용할 수 있으나, 사전등록·family-wise 유의·외부 일반화 범위를 과장하면 안 됨

## 1. 실행된 비교 연구 범위

| 축 | 실행 내용 | 결과 상태 |
|---|---|---|
| Storage | caption, representative frame, multi-frame, dual; 동일 Qwen/Flat/B2 | 완료 |
| Search/filter | B2, B3 top-200 postfilter, B4 prefilter, caption B5 hybrid | 완료 |
| Index | Flat, HNSW 2 settings, IVF-Flat 2 settings, IVF-PQ 2 settings | 완료 |
| Interaction | 유효한 storage×search×index 91 configurations | 완료 |
| Scale | 10k–143,830 real Qwen-2048 vectors | 완료 |
| Seed | 기본 설정 3 seeds + 강화 설정 5 seeds | 완료 |
| External | MEVA 985 clips/193 queries, 동일 encoder, BH 보정 | 완료 |
| Circularity | BGE C1/C2 + 주 격자와 같은 Qwen C1/C2 | 완료 |

이 범위는 다방면 비교를 충족하지만 완전 요인설계는 아니다. Frame-only에 lexical search를 붙이는 것과 같은 비호환 cell은 설계상 제외했다.

## 2. 두 에이전트 교차감사

| 항목 | agy | Claude | 통합 판단 |
|---|---|---|---|
| 최종 판정 | PASS_WITH_LIMITATIONS | PASS_WITH_LIMITATIONS | 일치 |
| 치명적 오류 | 없음 | 없음 | 일치 |
| Storage family-wise 유의 | q_cluster 0.0852/0.0888 한계 | 같은 한계 | 과장 금지 |
| Scale task qrels | 부재 지적 | 부재 지적 | exact fidelity로만 해석 |
| Seed 안정성 | ef/nprobe 확대 권고 | 3-seed 범위 한계 | 5-seed 강화 실험 수행 |
| 32/32 보증 범위 | 대체로 신뢰 | pipeline·CI까지는 미검증 지적 | 별도 treatment/stat gate 추가 |
| 사후 명세 | 한계 기술 | confirmatory 라벨 금지 | “사후 우선 비교”로 수정 |
| 순환성 encoder 정렬 | 원 실험 수용 | BGE↔Qwen 불연속 지적 | Qwen 정렬 C1/C2 추가 |

두 감사 결과 원문 요약은 `AGY_AUDIT_KO.md`, `CLAUDE_AUDIT_KO.md`에 보존했다.

## 3. 교차감사에서 발견해 수정한 사항

### 3.1 Fidelity empty-reference

`multi_frame+B3+Flat`에서 한 질의의 exact postfilter 결과가 비어 있었다. 기존 식은 empty exact reference를 0으로 세어 Flat 자기 fidelity를 0.9882로 만들었다. Recall-to-exact가 정의되지 않는 이 질의를 평균에서 제외하도록 수정했다.

- 수정 후 모든 Flat self-anchor: 1.0
- 해당 구성의 evaluable queries: 84/85
- A1 storage, A2 B4−B2, 주요 B4 index 결론 변화: 없음

### 3.2 기존 32/32의 명칭

기존 검산은 raw ranking의 metric 산술, ID/rank, vector shape/norm, seed/hash를 검증한다. Retrieve treatment와 bootstrap/BH까지 독립 재현하지는 않으므로 “지표 산술·데이터 무결성 32/32”로 명칭을 제한했다.

새 treatment/statistics 검산은 다음을 직접 확인해 12/12 PASS했다.

- 정확한 91개 호환 configuration 집합
- 15,470 metric cells와 77,350 latency trials 완전성
- filtered ranking 382,193행의 metadata predicate 위반 0건
- strict qrels = semantic qrels ∩ metadata predicate
- 85/85 metadata 후보 집합이 qrel-oracle 집합과 다름
- B2 unfiltered anchor와 B4 treatment가 실제로 구별됨
- per-query→summary, paired mean delta, BH와 MEVA BH 독립 재계산
- Flat self-anchor의 empty-reference 처리

### 3.3 MEVA 다중비교

- Frame−caption semantic Δ +0.0239: cluster CI [-0.0292,+0.0813], storage BH cluster q=0.4008
- Dual−caption semantic Δ +0.0690: cluster CI [+0.0369,+0.1004], storage BH cluster q<0.0001

따라서 MEVA에서 one-frame 단독 우위는 불확실하고, dual 결합효과만 보정 후에도 양수다. Dual은 표현과 RRF fusion을 함께 바꾸므로 순수 storage 효과로 부르지 않는다.

## 4. Qwen-aligned 순환성 보강

주 91-config 격자와 동일한 522 canonical, Qwen3-VL-Embedding-2B, query, qrels를 사용했다. Clean/full/query를 한 model session에서 재임베딩하고, 주 runner와 같은 float32 L2 정규화를 적용했다.

| 실험 | clean semantic | treatment | Δ | query 95% CI | cluster 95% CI |
|---|---:|---:|---:|---:|---:|
| C1 qrel-oracle filter | 0.181005 | 1.000000 | +0.818995 | [+0.780200,+0.855287] | [+0.737950,+0.881682] |
| C2 full document contamination | 0.181005 | 0.853687 | +0.672682 | [+0.626129,+0.718190] | [+0.567532,+0.752005] |

C1 동일 선택률 random filter 평균은 0.120041이었다. Clean 0.181005는 주 격자 caption+B2+Flat과 일치한다. 별도 구현이 입력 hash, 1,367개 오염 label-edge, token truncation 0건, embedding/ranking/metric/bootstrap/anchor를 재계산해 10/10 PASS했다.

이로써 “순환성이 측정치를 인위적으로 부풀릴 수 있다”는 결론은 BGE뿐 아니라 주 Qwen 공간에서도 재현됐다. 실제 과거 성능 차이 전체를 순환성에 귀속할 근거는 아니다.

## 5. 고정밀 ANN 5-seed 보강

143,830 real Qwen-2048 vectors에서 HNSW/IVF 구조는 고정하고 search strength만 확대했다. 각 seed에서 인덱스를 실제 재구축했다.

| 구성 | mean recall@10 | min | max | median p95 | max p95 | 5/5 seed ≥0.99 |
|---|---:|---:|---:|---:|---:|---|
| HNSW M32/ef256 | 0.989412 | 0.987059 | 0.991765 | 3.179 ms | 3.295 ms | 아니오 |
| HNSW M32/ef512 | 0.998118 | 0.996471 | 1.000000 | 5.757 ms | 6.356 ms | **예** |
| HNSW M32/ef1024 | 1.000000 | 1.000000 | 1.000000 | 10.148 ms | 10.655 ms | **예** |
| IVF-Flat nprobe128 | 0.993176 | 0.989412 | 0.996471 | 21.155 ms | 23.003 ms | 아니오 |
| IVF-Flat nprobe256 | 0.999529 | 0.998824 | 1.000000 | 37.587 ms | 39.009 ms | **예** |
| IVF-Flat nprobe512 | 1.000000 | 1.000000 | 1.000000 | 68.580 ms | 70.300 ms | **예** |

30-cell 완전성, 설정별 monotonic recall, raw→summary, 0.99 flag, 기존 3-seed anchor 재현을 별도 검산해 8/8 PASS했다. 관측 범위의 운영 균형점은 HNSW ef512다. Exact top-10 우선이면 ef1024가 5/5 seed에서 1.0이지만 다른 corpus/query/seed에 대한 수학적 보장은 아니다.

## 6. 최종 주장 경계

논문에서 가능한 주장:

- 동일 encoder 조건에서 storage, search/filter, index 효과를 축별로 비교했다.
- Multi-frame−caption은 큰 양의 점 추정치와 paired-query/cluster CI를 보였다.
- B4 prefilter는 strict를 높이고 semantic을 낮추는 목적함수 trade-off를 보였다.
- Qwen/BGE 양쪽의 통제 주입에서 circular path가 지표를 크게 부풀렸다.
- 143,830 Qwen-2048에서 HNSW ef512는 관측 5 seeds 모두 recall≥0.99였고 IVF nprobe256보다 낮은 p95를 보였다.
- 단일 전역 최적이 아니라 목적·SLA별 Pareto 선택이 필요하다.

금지할 주장:

- Multi-frame이 cluster family-wise 0.05에서 유의한 일반 법칙이라고 선언하는 것.
- 91개 관측 최고점을 통계적으로 검증된 전역 최적이라고 부르는 것.
- MEVA가 multi-frame 이점을 외부 재현했다고 부르는 것.
- 32/32가 pipeline·bootstrap 전체를 독립 재현했다고 부르는 것.
- 사후 통합 명세를 preregistered confirmatory study라고 부르는 것.
- 순환성 주입 효과를 과거 시스템 차이 전체의 원인으로 귀속하는 것.
- 5-seed 관측을 모든 데이터와 구축의 0.99 보장으로 일반화하는 것.

## 7. 남은 공백

1. 다른 데이터셋에서 동일한 multi-frame storage ablation은 아직 없다.
2. 143,830-vector 확장 corpus에는 완전한 task qrels가 없어 exact-neighbor fidelity로만 평가한다.
3. 24시간 적재·갱신·삭제·재색인·caption 생성 비용은 포함하지 않는다.
4. latency는 shared host, single-thread 관측치다.
5. 별도 preregistered holdout 확증 연구는 수행하지 않았다.

이 공백들은 현재 결과를 무효화하는 필수 결함이 아니라 외적 타당성과 확증 강도의 한계다.

## 8. 최종 gate 현황

| 검증층 | 결과 | 보장 범위 |
|---|---:|---|
| Joint metric·artifact verifier | 32/32 PASS | metric 산술, ranking/vector/hash/seed 무결성 |
| Ablation treatment/stat verifier | 12/12 PASS | grid, treatment, qrel logic, latency cells, delta/BH |
| 기존 BGE circularity verifier | 12/12 PASS | 원 BGE C1/C2 독립 재계산 |
| Qwen-aligned circularity verifier | 10/10 PASS | treatment text, embedding, ranking, metric, bootstrap, anchor |
| High-recall 5-seed ANN verifier | 8/8 PASS | 30-cell, seed, summary, threshold, prior-anchor 재현 |
| agy methods audit | PASS_WITH_LIMITATIONS | 읽기 전용 독립 비판 감사 |
| Claude methods audit | PASS_WITH_LIMITATIONS | 읽기 전용 독립 비판 감사 |

최종적으로 실험 실행과 산출물 무결성은 통과했고, 남은 위험은 데이터 오류보다 주장 과장과 외적 일반화에 있다.
