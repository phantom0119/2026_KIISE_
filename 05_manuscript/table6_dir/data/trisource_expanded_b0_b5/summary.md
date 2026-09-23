# Retrieval Baseline Summary

created_at: `2026-07-10T17:03:02.887041+00:00`
canonical_root: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded`
embedding_root: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/embeddings_trisource_expanded/bge-m3`

## Overall Metrics

| strategy | recall_at_1 | recall_at_5 | recall_at_10 | recall_at_20 | mrr | ndcg_at_10 |
|---|---:|---:|---:|---:|---:|---:|
| B0_metadata_only | 0.0070 | 0.0217 | 0.0437 | 0.0700 | 0.4678 | 0.2181 |
| B1_bm25_only | 0.0000 | 0.0009 | 0.0019 | 0.0039 | 0.0500 | 0.0165 |
| B2_vector_only | 0.0039 | 0.0099 | 0.0119 | 0.0173 | 0.1548 | 0.0588 |
| B3_vector_postfilter | 0.0061 | 0.0261 | 0.0380 | 0.0546 | 0.2917 | 0.1523 |
| B4_prefilter_vector | 0.0061 | 0.0289 | 0.0439 | 0.0796 | 0.3032 | 0.1571 |
| B5_hybrid | 0.0047 | 0.0217 | 0.0331 | 0.0632 | 0.2904 | 0.1351 |

## Latency

| strategy | mean ms | p50 ms | p95 ms |
|---|---:|---:|---:|
| B0_metadata_only | 0.121 | 0.132 | 0.310 |
| B1_bm25_only | 59.190 | 55.044 | 71.304 |
| B2_vector_only | 49.939 | 49.636 | 52.308 |
| B3_vector_postfilter | 4.021 | 3.984 | 4.272 |
| B4_prefilter_vector | 14.927 | 16.778 | 35.701 |
| B5_hybrid | 73.392 | 70.493 | 100.892 |
