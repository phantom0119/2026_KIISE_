# Ablation study 실행 명세와 해석 경계

- 작성일: 2026-07-17 KST
- 성격: 이미 수행된 실험을 재현·감사하기 위한 **사후 통합 실행 명세**
- 주의: 이 문서는 사전등록 문서가 아니며, 결과를 보기 전에 고정된 계획이었다고 주장하지 않는다.
- 기본 단위: 동일 질의에 대한 paired comparison
- 주 검증 데이터: AI Hub 522 교차로 3,000 clips, 85 queries
- 외부 검증 데이터: MEVA 985 clips, 193 queries

## 공통 고정 조건

1. 데이터 split, query, strict/semantic qrels, query cluster를 비교 내에서 고정한다.
2. 저장 표현 비교에서는 query·caption·frame을 동일 Qwen3-VL-Embedding-2B 2,048차원 공간에 둔다.
3. 저장 표현, 검색 계획, 색인 설정 중 한 축의 주효과를 볼 때 나머지 축은 명시한 anchor로 고정한다.
4. 모든 결과는 strict와 semantic 평가를 분리하며, 둘을 임의 가중합한 단일 점수로 합치지 않는다.
5. ANN의 task metric 상승은 exact Flat 대비 top-10 fidelity와 paired CI를 함께 확인하며, 근사 오차를 품질 개선으로 해석하지 않는다.
6. 주 비교는 query-paired bootstrap과 intent×facet cluster bootstrap을 병기한다. family 내 다중 비교는 BH q-value를 병기한다.
7. latency는 shared-host 관측치로만 해석하고, 품질 지표와 합쳐 사후 단일 최적점을 만들지 않는다.

## 실행된 ablation 축

| ID | 질문 / 제거·교체 축 | 비교와 고정 anchor | 주 estimand | 상태 | 허용되는 결론 |
|---|---|---|---|---|---|
| A1 | 저장 표현 자체가 영향을 주는가 | caption, representative frame, multi-frame, dual; Flat+B2 고정 | paired Δ nDCG@10 | 완료 | 동일 encoder·동일 query/qrels에서 표현 효과 비교. 단, dual은 표현+RRF fusion 결합효과 |
| A2 | hard filter 배치가 영향을 주는가 | B2 post-filter, B3 oversample, B4 prefilter, 호환 시 B5 hybrid; storage와 Flat 고정 | paired Δ strict/semantic nDCG@10 | 완료 | strict와 semantic 목적의 trade-off |
| A3 | 색인 구조·탐색 강도가 영향을 주는가 | Flat, HNSW ef64/256, IVF-Flat nprobe8/32, IVF-PQ nprobe8/32; storage·plan 고정 | exact top-10 fidelity, task Δ, latency | 완료 | fidelity 조건부 Pareto 선택 |
| A4 | 축 간 상호작용이 있는가 | 유효 조합만으로 4 storage×plans×7 index settings, 총 91 configurations | configuration별 quality/cost | 완료 | 호환 영역에서 목적별 후보 비교; 완전 요인설계 주장 금지 |
| A5 | 3,000-clip 결론이 큰 실제 임베딩 색인에서도 유지되는가 | 143,830 Qwen-2048 frame vectors, 85 text queries; Flat exact anchor | recall@10, p95, serialized bytes | 완료 | 동일 자산 내 ANN 확장성; task relevance 일반화 금지 |
| A6 | ANN 구축 난수에 민감한가 | 기본 설정 3 seeds + 강화 설정 5 seeds; HNSW·IVF 구조 고정 후 탐색 강도만 증가 | seed mean/std/range/min recall@10 | 완료 | 관측한 5개 seed에서 0.99 안정 후보 판정 |
| A7 | 다른 데이터에서도 저장 표현 경향이 보이는가 | MEVA caption/frame/dual, Flat+B2, 동일 encoder | paired Δ nDCG@10, query/cluster CI | 완료 | caption 대 one-frame/dual 외부 검증; multi-frame 재현 주장 금지 |
| A8 | 순환성이 측정치를 인위적으로 높이는가 | 실험 내부 데이터·query·answer·encoder 고정 후 filter/document circularity만 주입; BGE 원 실험과 주 격자 정렬 Qwen 반복 | oracle/random/clean 대비 Δ | 완료 | 통제 주입에서 순환성의 인과적 영향 |

## 사후 우선 비교·탐색적 구분

- 사후 우선 핵심 비교: A1의 multi-frame−caption, A2의 B4−B2, A3의 ANN−Flat fidelity, A8의 circular−clean/random.
- 강건성/일반화 보조: A5 규모, A6 seed, A7 외부 데이터.
- 탐색적 비교: 91개 configuration의 전체 순위, latency를 포함한 SLA winner, 오염 비율별 비단조 dose 결과.
- 91개 configuration에서 관측된 최고점을 사후에 “통계적으로 검증된 전역 최적”으로 부르지 않는다.
- 이 구분은 사후 해석 우선순위이며 preregistered confirmatory status를 부여하지 않는다.

## 성공·실패 판정 규칙

1. 효과 방향은 query CI와 cluster CI를 모두 제시한다.
2. cluster family BH q-value가 0.05를 넘으면 family-wise 유의라고 쓰지 않는다.
3. ANN 후보는 exact top-10 fidelity를 우선 통과해야 하며, task metric의 작은 우위만으로 채택하지 않는다.
4. 규모 실험의 recall은 exact-neighbor fidelity이지 task relevance가 아니다.
5. 외부 데이터의 표현 단위가 다르면 동일 ablation의 직접 재현으로 부르지 않는다.
6. 결측·비호환 cell을 0점으로 대체하지 않고 설계상 제외하며 그 이유를 기록한다.

## 원자료와 검증 산출물

- 공동 최적화 보고서: `../20260717_joint_optimization_validation/FINAL_VALIDATION_REPORT_KO.md`
- raw rankings: `../20260717_joint_optimization_validation/rankings.parquet`
- query별 지표: `../20260717_joint_optimization_validation/per_query_metrics.parquet`
- 구성 격자: `../20260717_joint_optimization_validation/configuration_summary.csv`
- paired/cluster bootstrap: `../20260717_joint_optimization_validation/paired_bootstrap_comparisons.csv`
- 독립 재계산: `../20260717_joint_optimization_validation/independent_verification.json`
- 규모·seed·외부 검증: `../20260717_joint_optimization_validation/qwen2048_scaled_index/`, `../20260717_joint_optimization_validation/qwen2048_seed_robustness/`, `../20260717_joint_optimization_validation/meva_same_encoder_control/`
- 순환성 통제 주입: `../20260716_circularity_controlled_injection/`
- Qwen 정렬 순환성: `qwen_aligned_circularity/`
- 고정밀 5-seed ANN: `qwen2048_high_recall_5seed/`
- treatment/statistics 독립 gate: `treatment_integrity_verification.json`

## 명시적으로 남는 공백

1. 외부 데이터에서 동일한 multi-frame 저장 ablation은 아직 없다.
2. 대규모 색인에는 task qrels가 없어 task relevance를 재검증하지 못한다.
3. 24시간 적재·갱신·삭제·재색인과 caption 생성 비용은 포함하지 않는다.
4. 이 명세는 사후 통합 문서이므로 향후 확증 연구에는 별도 사전등록과 holdout이 필요하다.
