# P2-B Weaviate 자동 보고

- T2: **CROSS_ENGINE_GENERALIZED**

| domain | protocol | queries | error | missing | p95 ms |
|---|---|---:|---:|---:|---:|
| flask | weaviate_naive | 735 | 0.9197 | 0.9197 | 21.69 |
| flask | weaviate_read_filter | 647 | 0.9150 | 0.9150 | 24.77 |
| flask | weaviate_staged | 6085 | 0.0000 | 0.0000 | 14.23 |
| kubernetes | weaviate_naive | 1236 | 0.9191 | 0.9191 | 24.65 |
| kubernetes | weaviate_read_filter | 872 | 0.9163 | 0.9163 | 26.10 |
| kubernetes | weaviate_staged | 5610 | 0.0000 | 0.0000 | 17.74 |
