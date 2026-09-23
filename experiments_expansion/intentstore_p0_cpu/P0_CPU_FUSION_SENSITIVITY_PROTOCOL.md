# P0-C 사후 fusion 민감도 규칙

> 등록일: 2026-08-06  
> 상태: **P0-C 주 결과 확인 뒤, 가중 fusion 결과 계산 전 고정한 사후 강건성 분석**

P0-C의 1:1 RRF가 caption보다 낮았다는 결과가 단지 부적절한 가중치 때문인지 확인한다. 이 분석은 사후 분석이므로 P0-C 주 가설을 새 가설로 바꾸거나 최초성을 주장하는 근거로 사용하지 않는다.

## 고정 조건

- 입력 query, qrels, caption ranking, CLIP 4-frame ranking은 P0-C와 동일
- RRF `k=60`
- 가중치: text:visual = `8:1`, `4:1`, `2:1`, `1:1`, `1:2`, `1:4`
- 서비스군: `dynamic_event`, `scene_state`, `context_filtered`, `open_event`
- 주 지표: strict nDCG@10
- 총 6×4=24개 paired sign-flip test, 각 200,000회
- 24개 전체 BH-FDR
- query bootstrap 및 `(dataset,event_type)` cluster bootstrap 각 20,000회
- 최소 추가 이득: caption 대비 nDCG@10 `+0.02`
- seed: `20260806`

## 판정

- `ROBUST_FUSION_GAIN_FOUND`: 한 개 이상의 서비스군·고정 가중치가 평균차 ≥0.02, BH q<0.05, query/cluster CI 하한>0을 모두 만족
- `NO_ROBUST_FUSION_GAIN`: 위 조건을 만족하는 셀이 없음

첫 판정이면 현재 `STOP_SIGNAL`은 `HOLD`로 약화한다. 두 번째 판정이면 **현재 CLIP+BGE 안전 표현 arm 범위에서** caption 지배 결론을 강화한다. 어느 경우에도 더 강한 temporal/trajectory/event-graph 표현을 시험하지 않고 범용 IntentStore 전체를 기각하지 않는다.

