# 순환성 통제 주입 실험 결과

- 실행 시각(UTC): `2026-07-16T12:48:48.396569+00:00`
- 데이터: AIHub-522 frozen tri-source expanded, 3,000 clips / 85 queries
- 주 지표: semantic nDCG@10의 85질의 평균
- 상태: 예비 계산을 본 뒤 정식화한 post-pilot 실험이며 사전등록 실험은 아님

## C1: qrel-oracle 필터 주입

| 조건 | strict nDCG@10 | semantic nDCG@10 |
|---|---:|---:|
| clean_b2 | 0.058839 | 0.170033 |
| random_same_selectivity_mean | 0.032543 | 0.106752 |
| oracle_qrel_filter | 1.000000 | 1.000000 |

semantic oracle−clean Δ=+0.829967, query bootstrap 95% CI [+0.792333, +0.866565], pair-cluster bootstrap 95% CI [+0.747695, +0.912452].
동일 선택률 무작위 필터 1000회는 평균 0.106752, replicate 95% 범위 [0.085628, 0.129290]였다.

oracle=1.0은 정답 집합 자체를 후보 집합으로 사용했기 때문에 구성상 보장된다. 따라서 이 결과는 검색 모델의 개선이 아니라 C1 경로가 평가를 포화시킬 수 있음을 정량화한다.

## C2: qrel 라벨 문서 재진술

| backend | clean semantic nDCG@10 | full contamination | Δ | query bootstrap 95% CI | pair-cluster 95% CI |
|---|---:|---:|---:|---:|---:|
| BM25 | 0.050068 | 0.745794 | +0.695726 | [+0.640215, +0.749209] | [+0.593401, +0.790481] |
| BGE-M3 | 0.170033 | 0.801141 | +0.631108 | [+0.580243, +0.680292] | [+0.535840, +0.718070] |

### BM25 오염량 강건성 분석

| 라벨-edge 오염률 | 반복 | semantic nDCG@10 평균 | assignment 95% 범위 |
|---:|---:|---:|---:|
| 0.00 | 1 | 0.050068 | [0.050068, 0.050068] |
| 0.25 | 200 | 0.812707 | [0.751179, 0.858168] |
| 0.50 | 200 | 0.804326 | [0.764750, 0.838208] |
| 0.75 | 200 | 0.774791 | [0.744361, 0.806168] |
| 1.00 | 1 | 0.745794 | [0.745794, 0.745794] |

부분 오염군은 라벨별 양성 문서의 고정 난수 순서를 사용해 한 반복 안에서 중첩된다. BM25의 IDF·문서길이 정규화 때문에 오염량에 대한 단조성은 검정하거나 주장하지 않는다.

## 해석 경계

- 모든 비교에서 corpus membership, query, qrel, metric, top-k와 tie-break를 고정했다.
- C1은 의도적인 oracle 상한이고, C2는 의도적인 qrel→document 누수 개입이다.
- 따라서 실험은 순환 경로가 성능을 인위적으로 부풀릴 수 있다는 within-workload 인과 증거다. 실제 과거 시스템의 성능 상승분 전체를 순환성 하나에 귀속하지는 않는다.
- 캡션에는 원래 task-aware 자연어가 포함되어 있다. clean→injected 차이는 그 기존 결합 위에 정답 라벨 재진술 경로를 추가한 효과다.
- 85질의가 25개 predicate×relevance 군집에 종속되므로 query bootstrap과 군집 bootstrap을 함께 제시했다.

## 재현성

- seed: `20260716`; bootstrap: `10000`; C1 random masks: `1000`; partial-dose assignments: `200`
- 입력 및 산출물 SHA-256은 `manifest.json`, 검증 30/30은 `validation.json`에 기록했다.
- 상세 질의별 지표와 랭킹은 같은 디렉터리의 Parquet/CSV 파일에 저장했다.
