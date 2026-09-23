# Retrieval Baseline Summary

created_at: `2026-07-06T08:08:32.148120+00:00`
canonical_root: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/vru_accident/20260706/canonical`
embedding_root: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/vru_accident/20260706/embeddings/bge-m3`

## Overall Metrics

| strategy | recall_at_1 | recall_at_5 | recall_at_10 | recall_at_20 | mrr | ndcg_at_10 |
|---|---:|---:|---:|---:|---:|---:|
| B0_metadata_only | 0.0299 | 0.1423 | 0.2141 | 0.2879 | 0.2424 | 0.2102 |
| B1_bm25_only | 0.0531 | 0.2528 | 0.3998 | 0.5434 | 0.4791 | 0.4495 |
| B2_vector_only | 0.0532 | 0.2556 | 0.3853 | 0.5230 | 0.4888 | 0.4476 |
| B3_vector_postfilter | 0.2096 | 0.6236 | 0.7343 | 0.8217 | 0.9590 | 0.9488 |
| B4_prefilter_vector | 0.2123 | 0.6441 | 0.7629 | 0.8591 | 0.9672 | 0.9736 |
| B5_hybrid | 0.2088 | 0.6334 | 0.7568 | 0.8605 | 0.9726 | 0.9651 |

## Latency

| strategy | mean ms | p50 ms | p95 ms |
|---|---:|---:|---:|
| B0_metadata_only | 0.057 | 0.030 | 0.139 |
| B1_bm25_only | 131.103 | 129.233 | 145.354 |
| B2_vector_only | 118.295 | 117.452 | 122.352 |
| B3_vector_postfilter | 4.877 | 4.848 | 5.050 |
| B4_prefilter_vector | 49.442 | 22.915 | 138.097 |
| B5_hybrid | 179.300 | 159.966 | 263.677 |
