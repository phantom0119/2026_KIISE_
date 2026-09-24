# FreshEvidenceDB P1-A 자동 보고

- 판정: **GO_P1B_ANSWER_AND_FAILURE_INJECTION**
- 게이트: `{"G0_data_harness": true, "G1_real_revision_failure": true, "G2_simple_filter_sufficient": false, "G3_staged_effective": true, "G4_blue_green_cost_value": true, "G5_pg_atomic_baseline": true, "blue_to_staged_write_amp_ratio": {"flask": 9.973575367647058, "kubernetes": 9.897669491525424}, "read_filter_p95_overhead": {"flask": 0.04577395297280562, "kubernetes": 0.002368494684895639}, "staged_p95_overhead": {"flask": -0.06420550006697079, "kubernetes": -0.042116448445544075}}`

| domain | protocol | update queries | error | stale | mixed | missing | p95 ms | write amp |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| flask | cross_naive | 6256 | 0.7634 | 0.7634 | 0.6833 | 0.7604 | 53.28 | 1.00 |
| flask | cross_read_filter | 6263 | 0.7068 | 0.0000 | 0.0000 | 0.7068 | 55.72 | 1.00 |
| flask | cross_staged | 6749 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 49.86 | 1.00 |
| flask | cross_blue_green | 50739 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 66.04 | 9.97 |
| flask | pg_atomic | 5974 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 20.52 | 1.00 |
| kubernetes | cross_naive | 7374 | 0.7373 | 0.7364 | 0.6564 | 0.7323 | 55.80 | 1.00 |
| kubernetes | cross_read_filter | 7603 | 0.7071 | 0.0000 | 0.0000 | 0.7071 | 55.93 | 1.00 |
| kubernetes | cross_staged | 7291 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 53.45 | 1.00 |
| kubernetes | cross_blue_green | 52279 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 70.43 | 9.90 |
| kubernetes | pg_atomic | 6764 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 22.05 | 1.00 |

상세 결과는 `aggregate.json`, 질의별 결과는 `query_events.csv`에 있다.
