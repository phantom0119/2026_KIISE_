# IntentStore P0-CPU 사전 분석 규칙

> 등록 시각: 2026-08-06 (결과의 서비스별 집계를 열람하기 전)  
> 목적: GPU를 사용하지 않고 IntentStore G1의 핵심 전제인 “서비스 의도에 따라 유리한 증거 표현이 달라지는가”를 선행 검증한다.  
> 판정 범위: **G1 전체 판정이 아닌 CPU 선행 증거**. 이 분석은 단일 교통 CCTV 검색 데이터의 재분석이므로 위험 감지 서비스 전체를 확정하지 않는다.

## 1. 고정 입력

- 질의별 지표: `paper_assets/20260717_joint_image_caption_validation/per_query_metrics.parquet`
- 질의 군집: `paper_assets/20260717_joint_image_caption_validation/query_clusters.csv`
- 표현별 비용: `paper_assets/20260717_joint_image_caption_validation/configuration_summary.csv`
- 원 실험 조건: 3,000 clips, 85 queries, 동일 Qwen3-VL-Embedding-2B 2,048차원 공간

입력 파일은 읽기 전용으로 사용하고 SHA-256을 결과 manifest에 기록한다.

## 2. 통제 셀

표현 이외의 효과를 제거하기 위해 다음 셀만 사용한다.

- 검색 계획: `B2_vector`
- 색인: `flat`
- 주 평가: `strict`
- 보조 평가: `semantic`
- 주 지표: `nDCG@10`
- seed: `20260806`
- bootstrap: 서비스 내부 질의 paired resampling 10,000회

## 3. 비교할 증거 표현

1. `caption`
2. `representative_frame`
3. `joint_image_caption`
4. `multi_frame`
5. `dual`

이 표현은 현재 IntentStore의 전체 후보인 원본, 궤적, 사건 그래프를 모두 포함하지 않는다. 따라서 본 분석은 시각·텍스트 검색 표현에 한정된 screening이다.

## 4. 서비스 의도 proxy

`query_clusters.csv`의 `intent`를 서비스군으로 사용한다.

- parked_vehicle
- crowded_scene
- buses
- stopped_vehicle
- two_wheeler

이들은 안전 위험비용과 실시간 경보를 직접 구현한 서비스가 아니라 교통 CCTV 검색 의도의 proxy다.

## 5. 통계 규칙

각 서비스에서 표현별 평균 nDCG@10을 계산하고 평균이 가장 높은 표현을 승자로 정한다. 승자와 차순위 표현의 질의별 차이에 대해 paired bootstrap 95% 신뢰구간을 계산한다.

승자가 실질적으로 지지되려면 다음 중 하나를 만족해야 한다.

### 품질 경로

- 승자−차순위 평균 차이 ≥ 0.05
- bootstrap 95% CI 하한 > 0

### 비용 경로

- 승자의 vector payload가 차순위의 50% 이하
- 승자−차순위 품질 차이의 bootstrap 95% CI 하한 ≥ −0.02

또한 두 표현 A/B가 서로 다른 두 서비스에서 반대 방향으로 각각 0.05 이상 우세하고 두 신뢰구간이 0을 제외하면 `strong reversal`로 기록한다.

## 6. 자동 판정

- `CONTINUE_STRONG`: strong reversal이 존재한다.
- `CONTINUE_SUPPORTED`: 서로 다른 표현인 지지된 서비스 승자가 2개 이상 존재한다.
- `INCONCLUSIVE`: 표현별 차이는 있으나 위 기준을 충족하지 못한다.
- `STOP_SIGNAL`: 모든 서비스의 승자가 동일하고, 비용 경로로도 다른 선택을 지지하지 못한다.

`CONTINUE_*`도 IntentStore G1 최종 통과를 의미하지 않는다. 위험 감지·관계 질의·원본 TTL을 포함한 별도 P0에서 재검증해야 한다. `STOP_SIGNAL`이면 신규 GPU 실험 전에 주제 축소를 우선 검토한다.

## 7. 필수 산출물

- `results/source_manifest.json`
- `results/service_representation_means.csv`
- `results/service_winner_bootstrap.csv`
- `results/pairwise_bootstrap.csv`
- `results/decision.json`
- `G1_CPU_REPORT.md`
- `INTENTSTORE_P0_CPU_LOG.md`

## 8. 금지 해석

- 기존 임베딩 생성 비용은 현재 파일에 없으므로 검색 지연을 end-to-end 경보 지연으로 해석하지 않는다.
- 검색 nDCG를 위험 탐지 F1이나 미탐 비용으로 바꾸어 말하지 않는다.
- 단일 데이터셋 결과를 범용 멀티모달 저장 정책의 확정 증거로 사용하지 않는다.
- 결과 확인 후 임계값, 주 지표, 서비스군을 변경하지 않는다.

## 9. 결과 확인 후 추가한 다중성 감사

> 상태: **사후 유효성 보정**. 최초 자동 판정 결과를 확인한 뒤 추가했으므로 사전 등록 분석으로 가장하지 않는다.

최초 규칙의 strong reversal 탐색은 주 평가에서 5개 서비스×10개 표현쌍, 총 50개 비교를 수행하지만 개별 bootstrap 신뢰구간만 사용했다. 이는 다중 비교에 따른 우연한 reversal을 과대평가할 수 있다. 최종 CPU 해석에는 다음 보수적 감사를 추가한다.

- strict nDCG@10의 50개 서비스-표현쌍 각각에 paired sign-flip randomization test 200,000회를 수행한다.
- 두 방향 p-value를 계산하고 50개 전체에 Benjamini-Hochberg FDR을 적용한다.
- `FDR_CONFIRMED_STRONG`: 동일 표현쌍이 서로 다른 서비스에서 반대 방향으로 각각 절대차 0.05 이상이고 두 q-value < 0.05.
- `FDR_INCONCLUSIVE`: 최초 reversal이 위 조건을 통과하지 못함.

최종 기록에서는 최초 `decision.json`을 수정하지 않고, `multiplicity_decision.json`에 보정 판정을 별도로 보존한다.
