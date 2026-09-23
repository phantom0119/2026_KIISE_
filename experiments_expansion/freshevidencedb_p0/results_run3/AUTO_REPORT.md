# FreshEvidenceDB P0 자동 보고

- 판정: **CONDITIONAL_GO_REAL_REVISION_CROSS_ENGINE**
- 게이트: `{"G0_harness": true, "G1_reproducible_failure": true, "G2_simple_filter_sufficient": false, "G3_staged_manifest_effective": true, "G4_blue_green_system_value": true, "blue_to_staged_write_amp_ratio": 8.392976649600502, "read_filter_p95_overhead": 0.016830634300462943, "staged_p95_overhead": 0.01827689912935626}`

| protocol | update queries | error | stale | mixed | missing | p95 ms | write amp |
|---|---:|---:|---:|---:|---:|---:|---:|
| naive_eager | 2382 | 0.7019 | 0.7019 | 0.3073 | 0.2565 | 31.12 | 1.00 |
| read_version_filter | 2318 | 0.1519 | 0.0000 | 0.0000 | 0.1519 | 31.65 | 1.00 |
| blue_green_epoch | 2034 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 90.09 | 8.39 |
| staged_manifest | 2015 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 31.69 | 1.00 |

상세 결과는 `aggregate.json`, 질의 이벤트는 `query_events.csv`에 있다.
