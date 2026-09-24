# P3 실행 수정 기록 v1.1

- 시점: P3-A 12개 page 중 5개 API 응답 수령 후, 전체 집계·게이트 생성 전
- 변경하지 않은 것: page 목록, 기간, 노출 공식, 임계값, 다른 P3 arm

Wikimedia API가 여섯 번째 page에서 HTTP 429와 `Retry-After: 11`을 반환해 첫 실행이 중단됐다. 응답 누락을 결과로 처리하지 않고 다음 두 transport-only 수정을 했다.

1. `Retry-After`를 준수하고 exponential backoff와 최대 8회 재시도를 적용
2. 이미 받은 raw JSON은 SHA가 유지되도록 재사용하고 미수령 page만 요청

첫 5개 page의 개별 중간 수치는 stdout에 출력됐지만 전체 T1은 계산되지 않았다. 수정은 결과 임계값이나 대상 선택에 영향을 주지 않는다.
