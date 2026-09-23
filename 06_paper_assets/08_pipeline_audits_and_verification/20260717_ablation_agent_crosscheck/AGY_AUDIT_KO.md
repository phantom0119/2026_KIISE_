# agy 독립 ablation 감사 결과

- 실행일: 2026-07-17 KST
- 실행 방식: 새 headless session, plan+sandbox, 로컬 읽기 승인, 파일 수정 금지
- 유효 호출: 세 번째 호출(첫 호출은 인자 파싱, 두 번째는 읽기 권한 거부로 무효)
- 최종 판정: **PASS_WITH_LIMITATIONS**

## 판정 요약

실험 설계의 투명성, 데이터 무결성, raw artifact와 보고서 핵심 수치의 일치를 확인했다. 치명적 오류는 없다고 판정했다. 다만 storage family의 cluster-level BH q-value가 0.05를 넘고, 대규모 ANN의 3개 seed 모두에서 recall@10≥0.99가 보장되지 않으며, 대규모 색인에는 task qrels가 없다는 한계를 강조했다.

## finding

### 치명적

- 없음.

### 중대

- HNSW와 IVF-Flat의 구축 seed 민감도 때문에 recall@10≥0.99를 안정적으로 보장한다는 주장을 금지해야 한다.
  - HNSW M32/ef256: mean 0.9886, range [0.9871, 0.9906]
  - IVF-Flat nlist1024/nprobe128: mean 0.9933, range [0.9894, 0.9965]

### 경미

- Multi-frame−caption의 storage family cluster BH q-value는 semantic 0.0852, strict 0.0888이므로 family-wise 0.05 유의라고 쓰면 안 된다.
- 143,830-vector 규모 실험은 task qrels가 없어 exact-neighbor fidelity와 latency만 검증한다.

## 핵심 수치 교차검산

| 주장 | raw source | 독립 확인값 | 판정 |
|---|---|---:|---|
| Multi-frame−caption semantic Δ | `paired_bootstrap_comparisons.csv` | +0.17078, query CI [0.0989, 0.2399], cluster CI [0.0178, 0.3162] | 일치 |
| Multi-frame−caption strict Δ | `paired_bootstrap_comparisons.csv` | +0.03873, query CI [0.0047, 0.0730], cluster CI [0.0037, 0.0762] | 일치 |
| Multi-frame B4−B2 strict Δ | `paired_bootstrap_comparisons.csv` | +0.16116, query CI [0.1289, 0.1952], cluster CI [0.1048, 0.2093] | 일치 |
| Multi-frame B4−B2 semantic Δ | `paired_bootstrap_comparisons.csv` | -0.09324, query CI [-0.1398, -0.0482], cluster CI [-0.1629, -0.0187] | 일치 |
| MEVA frame−caption semantic Δ | `meva_same_encoder_control/paired_bootstrap.csv` | +0.02394, query CI [-0.0053, 0.0535], cluster CI [-0.0292, 0.0813] | 일치 |
| MEVA dual−caption semantic Δ | `meva_same_encoder_control/paired_bootstrap.csv` | +0.06902, query CI [0.0510, 0.0875], cluster CI [0.0369, 0.1004] | 일치 |
| HNSW M32/ef256 seed 20260717 recall | `qwen2048_seed_robustness/seed_results.csv` | 0.9906 | 일치 |
| HNSW M32/ef256 3-seed mean | `qwen2048_seed_robustness/seed_results.csv` | 0.98863 | 일치 |
| Circularity C1 oracle−clean semantic Δ | circularity raw summaries | +0.82997, query CI [0.7923, 0.8666], cluster CI [0.7477, 0.9125] | 일치 |
| Circularity C2 BM25 dose=0.25 mean | `c2_bm25_dose_summary.csv` | 0.81271 | 일치 |

## 축별 평가

| 축 | 통제 | 통계 | 핵심 경계 |
|---|---|---|---|
| A1 storage | 적절 | paired/cluster 증거는 있으나 cluster BH q>0.05 | multi-frame 효과는 522 내부 결과 |
| A2 search plan | 적절 | strict/semantic 분리 적절 | 두 목적의 trade-off |
| A3 index | 적절 | Flat fidelity anchor 병기 적절 | 3k task grid의 규모 한계 |
| A4 interaction | 비호환 cell 제외 적절 | Pareto로 제한한 해석 적절 | 완전 요인설계 아님 |
| A5 scale | 고정 real embeddings 적절 | task qrels 없음 | relevance 일반화 금지 |
| A6 seed | 설정 고정 적절 | 3-seed mean/range 적절 | 3회만 관측 |
| A7 external | 동일 encoder/Flat+B2 적절 | query/cluster CI 적절 | MEVA는 one-frame, multi-frame 재현 아님 |
| A8 circularity | 순환 요소만 주입 | random/dose 반복 적절 | 기존 성능 차이 전체의 귀속 근거 아님 |

## 허용·금지 주장

허용:

- 동일 encoder의 paired-query 분석에서 multi-frame이 caption보다 높은 semantic nDCG@10 점 추정치를 보였다.
- B4 prefilter는 strict를 높이고 semantic을 낮추는 trade-off를 보였다.
- 의도적 qrel→filter/document 순환 주입이 측정치를 크게 부풀릴 수 있다.

금지:

- 91개 구성에서 단일 통계적 전역 최적 조합을 확정했다.
- HNSW M32/ef256이 모든 구축에서 recall 0.99 이상을 보장한다.
- MEVA가 522의 multi-frame 이점을 외부 재현했다.
- storage family의 cluster-level family-wise 유의성을 확보했다.

## 추가 실험 판정

- 필수: 없음.
- 권고: efSearch>256, nprobe 확장과 seed 5~10회 반복.
- 현재 MEVA frozen one-frame 자산으로 multi-frame 재현을 억지로 주장하는 실험: 불필요.

## 감사 한계

- 개별 latency raw trial을 독립 하드웨어에서 재측정하지 않았다.
- 143,830-vector `.npy`의 모든 float 값을 별도 구현으로 전수 재연산하지 않았다.
- 다른 에이전트의 결과를 보지 않았다.

> 참고: 위 문서는 `agy` 원출력의 사실·판정·수치·제안 전체를 구조만 정리해 보존한 것이다. 원출력에는 감사 신뢰도 99%라는 주관적 표현이 있었으나, 본 교차검증에서는 그러한 확률 수치를 근거로 사용하지 않는다.
