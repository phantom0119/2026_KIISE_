# FreshEvidenceDB P1-B 자동 보고

- 판정: **GO_FRESHEVIDENCEDB_CORE_TOPIC**
- 게이트: `{"B0_data_harness": true, "B1_answer_value": true, "B2_client_crash_safety": true, "B3_recovery": true}`

| domain | protocol | observations | snapshot error | v2 current accuracy | missing | ambiguous |
|---|---|---:|---:|---:|---:|---:|
| flask | cross_naive | 450 | 0.6667 | 0.2000 | 0.3333 | 0.3333 |
| flask | cross_read_filter | 450 | 0.3333 | 0.6000 | 0.3333 | 0.0000 |
| flask | cross_staged | 450 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| flask | pg_atomic | 150 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| kubernetes | cross_naive | 450 | 0.6667 | 0.2000 | 0.3333 | 0.3333 |
| kubernetes | cross_read_filter | 450 | 0.3333 | 0.6000 | 0.3333 | 0.0000 |
| kubernetes | cross_staged | 450 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |
| kubernetes | pg_atomic | 150 | 0.0000 | 1.0000 | 0.0000 | 0.0000 |

- crash/recovery observations: 1500
- crash/recovery errors: 0
- duplicate rows: 0
- orphan rows after GC: 0
- recovery p95: 77.00 ms
