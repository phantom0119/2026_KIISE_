# P2-C 서버 장애 자동 보고

- T3: **SERVER_FAULT_GATE_PASS**
- 시나리오 실행: 20
- restart/recovery 관측: 1000, 오류: 0, Wilson 상한: 0.3827%
- duplicate: 0, orphan: 0
- recovery p95: 33.30 ms

장애 중 서비스 가용성은 별도 지표이다. `after_restart_before_recovery`는 container가 다시 health/readiness를 통과한 직후를 뜻한다.
