# IntentStore P0-CPU MEVA 독립 복제 보고서

> 자동 생성: 2026-08-06T06:53:07.263833+00:00  
> 동일 encoder의 기존 MEVA 산출물을 CPU로 재분석했다.

- 판정: **REPLICATED_SUPPORTED**
- 서비스군 승자 종류: caption, dual, frame
- 사전 지지 기준을 통과한 승자: caption, frame
- FDR 확인 reversal: 0개

## 서비스군별 결과

| 서비스군 | n | 승자 | 차순위 | 차이 [95% CI] | q(BH) | index 비율 | 지지 |
|---|---:|---|---|---:|---:|---:|---|
| body_social | 56 | frame | dual | +0.0068 [-0.0181, +0.0336] | 0.972 | 0.500 | True |
| facility_access | 6 | caption | dual | +0.0000 [+0.0000, +0.0000] | 1 | 0.500 | True |
| object_interaction | 41 | frame | dual | +0.0049 [-0.0274, +0.0399] | 1 | 0.500 | False |
| vehicle_contact | 64 | dual | frame | +0.0142 [-0.0101, +0.0398] | 0.6037 | 2.000 | False |
| vehicle_maneuver | 26 | caption | dual | +0.0017 [-0.0426, +0.0447] | 1 | 0.500 | False |

## 해석

- 이 데이터는 522 데이터와 독립적이지만 대표 프레임 한 장만 있어 multi-frame 가설을 복제하지 못한다.
- 서비스군은 사전에 의미론적으로 묶었으며, 위험비용·실시간 경보가 아니라 검색 proxy다.
- 이 결과는 522 screening과 함께 다음 CPU 단계의 우선순위를 정하는 데만 사용한다.
