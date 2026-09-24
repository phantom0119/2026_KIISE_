# IntentStore P0-C 안전 서비스 표현 검증 보고서

> 자동 판정: **`SAFETY_G1_STOP_SIGNAL`**  
> 범위: 실제 안전 검색 질의에서 G1 표현 비지배성만 검사. 연구 주제 최종 확정은 아님.

## 1. 실행 무결성

- CLIP query embedding 장치: `cpu`
- offline/local-only: `True`
- 질의: 103개, 평가 행: 412개
- 기존 frame/caption embedding과 순위를 읽기 전용으로 재사용했으며 영상 decoding이나 GPU 추론은 수행하지 않았다.

## 2. 서비스군별 결과

| service | representation | queries | event clusters | nDCG@10 | Hit@10 | support rate | vector B/clip | Pareto |
|---|---|---:|---:|---:|---:|---:|---:|---|
| dynamic_event | caption | 93 | 18 | 0.3558 | 0.7742 | 0.7742 | 4096 | yes |
| dynamic_event | center_frame | 93 | 18 | 0.1471 | 0.4839 | 0.4839 | 2048 | yes |
| dynamic_event | visual_4frame | 93 | 18 | 0.1565 | 0.5484 | 0.5484 | 8192 | no |
| dynamic_event | fusion | 93 | 18 | 0.2995 | 0.7957 | 0.7957 | 12288 | no |
| scene_state | caption | 10 | 3 | 0.8994 | 1.0000 | 1.0000 | 4096 | yes |
| scene_state | center_frame | 10 | 3 | 0.7525 | 1.0000 | 1.0000 | 2048 | yes |
| scene_state | visual_4frame | 10 | 3 | 0.7090 | 1.0000 | 1.0000 | 8192 | no |
| scene_state | fusion | 10 | 3 | 0.8754 | 1.0000 | 1.0000 | 12288 | no |
| context_filtered | caption | 82 | 20 | 0.4027 | 0.8293 | 0.8293 | 4096 | yes |
| context_filtered | center_frame | 82 | 20 | 0.2094 | 0.5366 | 0.5366 | 2048 | yes |
| context_filtered | visual_4frame | 82 | 20 | 0.2165 | 0.6098 | 0.6098 | 8192 | no |
| context_filtered | fusion | 82 | 20 | 0.3591 | 0.8171 | 0.8171 | 12288 | no |
| open_event | caption | 21 | 21 | 0.4315 | 0.6667 | 0.6667 | 4096 | yes |
| open_event | center_frame | 21 | 21 | 0.1922 | 0.5238 | 0.5238 | 2048 | yes |
| open_event | visual_4frame | 21 | 21 | 0.1852 | 0.5238 | 0.5238 | 8192 | no |
| open_event | fusion | 21 | 21 | 0.3409 | 0.8095 | 0.8095 | 12288 | no |

## 3. 사전 고정 주 검정

| ID | service | contrast | n | clusters | mean diff | query 95% CI | cluster 95% CI | p | q(BH) | expected support | opposite support |
|---|---|---|---:|---:|---:|---|---|---:|---:|---|---|
| H1 | dynamic_event | visual_4frame−caption | 93 | 18 | -0.1993 | [-0.2576, -0.1441] | [-0.3603, -0.1060] | 0.000005 | 0.000020 | no | yes |
| H2 | scene_state | caption−visual_4frame | 10 | 3 | +0.1904 | [+0.0600, +0.3363] | [+0.1029, +0.3492] | 0.031320 | 0.041760 | yes | no |
| H3 | context_filtered | fusion−caption | 82 | 20 | -0.0436 | [-0.0801, -0.0083] | [-0.1069, -0.0012] | 0.020450 | 0.040900 | no | no |
| H4 | all | visual_4frame−center_frame | 103 | 21 | +0.0042 | [-0.0129, +0.0216] | [-0.0162, +0.0282] | 0.634937 | 0.634937 | no | no |

## 4. 판정

- 상태: **`SAFETY_G1_STOP_SIGNAL`**
- query-contract 지지 검정: `H2`
- 독립 event cluster까지 지지된 검정: `H2`
- 서비스별 최선 단일 arm: `{"context_filtered": "caption", "dynamic_event": "caption", "open_event": "caption", "scene_state": "caption"}`
- fusion의 최선 단일 arm 대비 이득: `{"context_filtered": -0.04359063922379053, "dynamic_event": -0.056311146021011116, "open_event": -0.09060389605431118, "scene_state": -0.024017765353732123}`
- 최초 실행의 `CONTINUE`는 STOP 조건과의 중첩을 잘못 처리한 자동 판정 우선순위 버그였다. 임계값 변경 없이 `STOP_SIGNAL`을 먼저 적용하도록 사후 수정했다.
- 연구 주제 최종 확정: **아직 아님**. 이 결과는 저장 형식 선택의 필요조건만 다룬다.

## 5. 해석 한계

1. CLIP과 BGE-M3를 비교하므로 형식만이 아니라 encoder를 포함한 표현 stack 비교다.
2. 네 frame max는 순서·궤적을 이해하지 않는다.
3. 같은 event type의 조건 변형 질의가 반복되므로 query CI보다 cluster CI를 최종 일반화에 우선한다.
4. vector payload만 비교했고 생성 비용, JPEG, 문자열, DB 오버헤드는 제외했다.
5. 실제 원본 삭제 뒤 새 detector/VLM을 재실행한 실험이 아니므로 미래 서비스 완전성을 증명하지 않는다.

## 6. 다음 게이트

같은 stream에 두 개 이상의 안전 서비스를 동시에 replay하고, raw TTL 뒤의 사건 F1·위험가중 손실·p95 deadline miss·저장/GPU 비용을 측정한다. `IntentStore`가 `best-static`보다 품질/SLA 제약을 지키면서 자원을 절감할 때만 연구 주제를 확정한다.
