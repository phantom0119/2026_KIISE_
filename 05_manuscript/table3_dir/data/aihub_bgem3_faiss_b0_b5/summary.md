# Retrieval Baseline Summary

created_at: `2026-07-06T08:52:17.163765+00:00`
canonical_root: `Datasets/processed/aihub_intelligent_cctv/20260706/canonical`
embedding_root: `Datasets/processed/aihub_intelligent_cctv/20260706/embeddings/bge-m3`

## Overall Metrics

| strategy | recall_at_1 | recall_at_5 | recall_at_10 | recall_at_20 | mrr | ndcg_at_10 |
|---|---:|---:|---:|---:|---:|---:|
| B0_metadata_only | 0.1541 | 0.5831 | 0.7296 | 0.7708 | 0.6472 | 0.6985 |
| B1_bm25_only | 0.2367 | 0.7207 | 0.8524 | 0.9380 | 0.9570 | 0.9600 |
| B2_vector_only | 0.1235 | 0.4461 | 0.6565 | 0.8423 | 0.7332 | 0.7014 |
| B3_vector_postfilter | 0.2584 | 0.7435 | 0.8644 | 0.9404 | 1.0000 | 1.0000 |
| B4_prefilter_vector | 0.2584 | 0.7435 | 0.8644 | 0.9404 | 1.0000 | 1.0000 |
| B5_hybrid | 0.2584 | 0.7434 | 0.8639 | 0.9393 | 1.0000 | 0.9977 |

## Latency

| strategy | mean ms | p50 ms | p95 ms |
|---|---:|---:|---:|
| B0_metadata_only | 0.010 | 0.003 | 0.037 |
| B1_bm25_only | 14.289 | 14.186 | 14.668 |
| B2_vector_only | 13.469 | 13.460 | 13.754 |
| B3_vector_postfilter | 3.475 | 3.449 | 3.632 |
| B4_prefilter_vector | 3.296 | 0.605 | 14.281 |
| B5_hybrid | 17.131 | 14.414 | 28.405 |
