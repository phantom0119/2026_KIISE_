# IntentStore P0-CPU MEVA 독립 복제 규칙

> 등록 시각: 2026-08-06, 522 교통 CCTV 결과의 다중성 감사 이후  
> 상태: 독립 데이터 복제 분석. MEVA의 서비스군별 표현 결과는 아직 집계하지 않은 상태에서 규칙을 고정했다.

## 목적

522 교통 CCTV에서 관찰된 “서비스에 따라 caption/frame 계열의 상대 순위가 달라질 수 있다”는 신호를 독립 MEVA 산출물에서 CPU로 검증한다.

## 입력과 고정 셀

- 입력: `paper_assets/20260717_joint_optimization_validation/meva_same_encoder_control`
- 규모: 985 clips, 193 queries, 57 intent×facet clusters
- 표현: `caption`, `frame`, `dual`
- 검색 계획: `B2_vector`
- 주 평가: `strict` nDCG@10
- 보조 평가: `semantic` nDCG@10
- bootstrap: 10,000회
- paired sign-flip randomization: 비교당 200,000회
- BH-FDR family: 주 평가의 5개 서비스군×3개 표현쌍=15개
- seed: `202608062`

MEVA는 클립당 대표 프레임 한 장만 보존하므로 multi-frame을 검증하지 못한다.

## 사전 서비스군 매핑

- `vehicle_contact`: person_loads_vehicle, person_unloads_vehicle, vehicle_picks_up_person, vehicle_drops_off_person, person_opens_trunk, person_closes_trunk, person_enters_vehicle
- `object_interaction`: person_purchases, person_reads_document, person_transfers_object, person_carries_heavy_object
- `body_social`: person_stands_up, person_sits_down, person_embraces_person, hand_interacts_with_person, person_rides_bicycle
- `vehicle_maneuver`: vehicle_makes_u_turn, vehicle_reverses
- `facility_access`: person_closes_facility_door

매핑되지 않은 relevance definition이 있으면 실행을 실패시킨다.

## 판정

- 실질 품질 차이: 절대 nDCG@10 차이 0.05 이상, BH q<0.05
- 비용 대체: 승자 index가 차순위의 50% 이하이며 paired bootstrap CI 하한 ≥ −0.02
- `REPLICATED_STRONG`: 동일 표현쌍의 방향이 두 서비스군에서 반대로 뒤집히고 양쪽 모두 실질 품질 차이 기준을 통과
- `REPLICATED_SUPPORTED`: 서로 다른 지지된 서비스 승자가 2개 이상
- `INCONCLUSIVE`: 이질성은 보이나 위 기준 미달
- `STOP_SIGNAL`: 모든 서비스군에서 하나의 표현이 지배하고 비용 대체도 없음

이 결과도 원본 TTL·궤적·위험 F1을 포함하지 않으므로 IntentStore G1 최종 판정이 아니다.

## 결과 확인 후 추가한 정보성 감사

> 상태: **사후 유효성 보정**. 최초 MEVA 판정을 본 뒤 추가했으므로 사전 등록 기준이 아니다.

최초 비용 대체 규칙은 모든 표현의 nDCG@10이 0인 `facility_access`도 “같은 품질에서 절반 비용”으로 인정하는 결함이 있었다. 해결 능력이 전혀 없는 동률은 유용한 비열등성이 아니므로 최종 종합 판정에서는 비용 경로에 다음 정보성 조건을 추가한다.

- 서비스군 질의 수 ≥ 10
- 승자 평균 strict nDCG@10 ≥ 0.05

원 `meva_decision.json`은 수정하지 않고 `meva_informative_decision.json`을 별도 보존한다.
