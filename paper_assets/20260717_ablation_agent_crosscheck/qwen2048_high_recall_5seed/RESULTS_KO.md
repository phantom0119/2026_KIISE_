# Qwen-2048 고정밀 ANN 5-seed 강건성

143,830개 real Qwen-2048 vectors와 85개 query에서 각 seed마다 구조를 실제 재구축했다.

| 구조 | 탐색 강도 | 5-seed mean | min | max | median p95 | max p95 | 모든 seed ≥0.99 |
|---|---:|---:|---:|---:|---:|---:|---|
| HNSW M32 | ef256 | 0.989412 | 0.987059 | 0.991765 | 3.179 ms | 3.295 ms | 아니오 |
| HNSW M32 | ef512 | 0.998118 | 0.996471 | 1.000000 | 5.757 ms | 6.356 ms | 예 |
| HNSW M32 | ef1024 | 1.000000 | 1.000000 | 1.000000 | 10.148 ms | 10.655 ms | 예 |
| IVF-Flat nlist1024 | nprobe128 | 0.993176 | 0.989412 | 0.996471 | 21.155 ms | 23.003 ms | 아니오 |
| IVF-Flat nlist1024 | nprobe256 | 0.999529 | 0.998824 | 1.000000 | 37.587 ms | 39.009 ms | 예 |
| IVF-Flat nlist1024 | nprobe512 | 1.000000 | 1.000000 | 1.000000 | 68.580 ms | 70.300 ms | 예 |

운영 균형점은 HNSW ef512다. 관측한 5개 seed 모두 recall≥0.99이고 IVF nprobe256보다 p95가 훨씬 낮다. exact top-10이 필요하면 HNSW ef1024가 5/5 seed에서 1.0이었지만, 이 보장은 관측한 corpus·query·seed 범위에만 한정한다.
