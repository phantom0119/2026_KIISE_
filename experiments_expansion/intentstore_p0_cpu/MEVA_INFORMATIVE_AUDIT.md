# MEVA 비용 대체 정보성 감사

> 최초 결과 확인 뒤 추가한 사후 유효성 보정이다.

- 판정: **REPLICATION_INCONCLUSIVE**
- 정보성 기준: n≥10, 승자 strict nDCG@10≥0.05
- 보정 후 지지된 표현: frame

| 서비스군 | n | 승자 평균 | 원 비용 지지 | 정보성 | 보정 지지 |
|---|---:|---:|---|---|---|
| body_social | 56 | 0.1118 | True | True | True |
| facility_access | 6 | 0.0000 | True | False | False |
| object_interaction | 41 | 0.0855 | False | True | False |
| vehicle_contact | 64 | 0.1199 | False | True | False |
| vehicle_maneuver | 26 | 0.0773 | False | True | False |

`facility_access`의 전 표현 0점 동률은 저장비가 작더라도 서비스 효용을 입증하지 못하므로 최종 지지에서 제외한다.
