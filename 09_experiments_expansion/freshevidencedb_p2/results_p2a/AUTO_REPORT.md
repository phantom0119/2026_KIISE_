# FreshEvidenceDB P2-A timestamp-calibrated exposure

- T1: **APPLICABLE_HIGH_TRAFFIC**
- Git timestamp는 실제지만 query rate는 scenario grid다.

| domain | updates/day | protocol | error-sec/update | break-even qps | errors/day @20qps |
|---|---:|---|---:|---:|---:|
| flask | 0.0676 | cross_naive | 0.048483 | 304.99 | 0.0656 |
| flask | 0.0676 | cross_read_filter | 0.046793 | 316.01 | 0.0633 |
| flask | 0.0676 | cross_staged | 0.000000 | ∞ | 0.0000 |
| kubernetes | 0.8811 | cross_naive | 0.060365 | 18.80 | 1.0637 |
| kubernetes | 0.8811 | cross_read_filter | 0.062469 | 18.17 | 1.1008 |
| kubernetes | 0.8811 | cross_staged | 0.000000 | ∞ | 0.0000 |
