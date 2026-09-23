# Claude 독립 ablation 감사 결과

- 실행일: 2026-07-17 KST
- 실행 방식: 새 session, plan mode, Read/Bash only, Edit/Write 금지, high effort
- 최종 판정: **PASS_WITH_LIMITATIONS**

## 판정 요약

축 분리·통제·다중비교·근사오차 처리는 대체로 건전하고 치명적 설계 오류는 없다고 판정했다. 다만 핵심 storage 효과의 cluster BH q-value, 32/32 검산의 제한된 보증 범위, 사후 명세의 비사전등록 성격, BGE-M3 순환성 실험과 Qwen 주 격자의 불연속 때문에 주장 강도를 제한해야 한다.

## finding

### 치명적

- 없음.

### 중대

1. Multi-frame−caption storage 효과는 semantic cluster q_BH=0.0852, strict=0.0888로 family-wise 0.05 유의가 아니다.
2. 기존 `independent_verification.json` 32/32는 runner가 만든 ranking에서 metric을 재계산하고 shape/hash/seed를 확인하지만 retrieve treatment, bootstrap CI, BH, qrel 논리 정합성을 독립 재현하지 않는다. 따라서 “지표 산술+데이터 무결성 gate”라고 불러야 한다.
3. 프로토콜은 사후 통합 명세다. 결과 관측 뒤 지정한 핵심 비교를 사전등록 의미의 confirmatory test라고 부르면 안 된다.
4. 기존 순환성 실험은 `canonical_trisource_expanded`와 BGE-M3를 사용하고, 주 격자는 Qwen3-VL-Embedding-2B 통합 자산을 사용한다. clean semantic 0.170033과 주 격자 caption/B2 0.181005를 하나의 연속 비교처럼 쓰면 안 된다.

### 경미

1. Dual−caption은 저장 표현과 RRF fusion을 함께 바꾸므로 순수 storage 주효과가 아니다.
2. bootstrap 10,000회에서 관측 p=0은 `p<1e-4`로 표기해야 한다.
3. 대규모 recall은 task relevance가 아니다.
4. seed 강건성은 3개 seed 관측 범위다.
5. latency는 shared host, 1 thread 결과다.

## 핵심 수치 교차검산

| 주장 | raw source | 확인값 | 판정 |
|---|---|---:|---|
| Multi-frame−caption semantic | paired bootstrap storage/semantic | Δ 0.170783, query CI [0.098939,0.239865], cluster CI [0.017792,0.316181] | 일치 |
| Multi-frame−caption strict | paired bootstrap storage/strict | Δ 0.038728, query CI [0.004700,0.073037] | 일치 |
| Multi-frame B4−B2 strict | paired bootstrap search/strict | Δ 0.161163, cluster CI [0.104798,0.209341] | 일치 |
| Multi-frame B4−B2 semantic | paired bootstrap search/semantic | Δ -0.093236 | 일치 |
| Multi-frame+B4+HNSW ef64 strict | configuration summary | 0.2685099 | 일치 |
| Storage cluster BH q | p_cluster를 3-comparison BH 재계산 | semantic 0.0852, strict 0.0888 | 일치 |
| Scale 3-seed mean | seed raw rows 직접 평균 | HNSW 0.98863, IVF-Flat 0.99334 | 일치 |
| Joint metric rows | config×query×scoring | 91×85×2=15,470 | 일치 |
| C1 oracle | 후보=정답집합 구성 | nDCG@10=1.0 | 일치 |

## 축별 평가

| 축 | 통제 | 통계 | 경계 |
|---|---|---|---|
| A1 storage | 동일 Qwen/B2/Flat 고정 | query CI 강, cluster BH q>0.05 | 522 내부, dual은 fusion 혼입 |
| A2 filter placement | storage/Flat 고정 | strict·semantic CI 분리 적절 | top-200 postfilter 예산 의존 |
| A3 index | representation/plan 고정 | Flat fidelity 우선 적절 | 3,000 clips |
| A4 interaction | 비호환 cell 제외 적절 | 91-rank/SLA는 탐색적 | 전역 최적 금지 |
| A5 scale | real vectors/query 고정 | exact fidelity만 존재 | task relevance 금지 |
| A6 seed | 실제 3회 재구축 | n=3 범위 | 3-seed에 한정 |
| A7 MEVA | 동일 encoder | query/cluster CI | one-frame이므로 multi-frame 재현 아님 |
| A8 circularity | 실험 내부 조건 고정 | query/cluster/random/dose | BGE-M3라 주 Qwen 격자와 불연속 |

## 가능한 주장

- 동일 Qwen 공간에서 storage, filter placement, index를 축별 통제 비교했다.
- 단일 전역 최적은 없고 strict/semantic/SLA별 Pareto 선택이 필요하다.
- Multi-frame은 큰 양의 점 추정치와 paired-query 증거를 보였다.
- Prefilter는 hard predicate에 유리하고 unfiltered는 scene semantic에 유리했다.
- 의도적 순환 주입은 실험 내부에서 지표를 인위적으로 포화시킬 수 있다.

## 금지할 주장

- Multi-frame 우위를 family-wise 유의한 일반 법칙으로 부르는 것.
- 32/32를 pipeline·CI까지 독립 재현한 것으로 부르는 것.
- 91개 중 관측 최고점을 통계적 전역 최적으로 부르는 것.
- scale recall을 task quality로 부르는 것.
- MEVA를 multi-frame 외부 재현으로 부르는 것.
- 순환성 Δ를 과거 시스템 차이 전체의 원인으로 귀속하는 것.
- 사후 핵심 비교를 사전등록 확인적 증거로 부르는 것.

## 추가 실험 판정

- 필수: 현재 해석 경계를 지키면 없음.
- 권고: 외부 multi-frame 데이터, scale task qrels, Qwen-aligned circularity, 별도 preregistered holdout.
- 현재 결과에 불필요: 3,000-clip 격자 단순 재실행, bootstrap 횟수만 증가.

## 감사 한계

- Parquet raw ranking/per-query metric은 직접 로드하지 않았고 검산기 결과와 스크립트 검토에 의존했다.
- task fidelity 수치 자체와 일부 MEVA raw pair는 직접 대조하지 못했다.
- latency/build/GPU embedding 실행은 재현하지 않았다.
- 다른 에이전트 결과를 보지 않았다.
