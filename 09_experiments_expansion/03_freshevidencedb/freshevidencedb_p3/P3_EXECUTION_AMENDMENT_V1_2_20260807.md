# P3 실행 수정 기록 v1.2

- 시점: P3-C Flask 12개 scenario 완료 후 Elasticsearch kill scenario의 재기동 직후
- 변경하지 않은 것: fault scenario, 반복·도메인, recovery, 안전성 임계값

Elasticsearch container restart 뒤 `/_cluster/health`가 HTTP 200을 반환했지만 cluster state가 아직 `SERVICE_UNAVAILABLE/state not recovered`라 첫 snapshot query가 503으로 중단됐다. 이는 데이터 불일치 결과가 아니라 readiness probe의 위양성이다.

readiness 조건을 HTTP 200에서 `status ∈ {yellow, green}` 및 `timed_out=false`로 강화했다. 첫 실행은 end-of-run 결과 파일을 만들기 전에 중단됐으며, 동일 run key를 초기화해 P3-C 전체를 처음부터 재실행한다.
