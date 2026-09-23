# Retrieval Baseline Summary

created_at: `2026-07-09T19:24:25.961891+00:00`
canonical_root: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/vru_accident/20260710_noncircular/canonical`
embedding_root: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/vru_accident/20260710_noncircular/embeddings/bge-m3`

## Overall Metrics

| strategy | recall_at_1 | recall_at_5 | recall_at_10 | recall_at_20 | mrr | ndcg_at_10 |
|---|---:|---:|---:|---:|---:|---:|
| B0_metadata_only | 0.0073 | 0.0417 | 0.0607 | 0.1081 | 0.2010 | 0.1449 |
| B1_bm25_only | 0.0033 | 0.0156 | 0.0388 | 0.0742 | 0.2313 | 0.0918 |
| B2_vector_only | 0.0192 | 0.0514 | 0.0776 | 0.1323 | 0.3741 | 0.1845 |
| B3_vector_postfilter | 0.0281 | 0.0885 | 0.1518 | 0.2385 | 0.4832 | 0.3020 |
| B4_prefilter_vector | 0.0281 | 0.0944 | 0.1756 | 0.2673 | 0.4832 | 0.3174 |
| B5_hybrid | 0.0173 | 0.0818 | 0.1421 | 0.2483 | 0.4076 | 0.2771 |

## Latency

| strategy | mean ms | p50 ms | p95 ms |
|---|---:|---:|---:|
| B0_metadata_only | 0.103 | 0.115 | 0.184 |
| B1_bm25_only | 27.258 | 26.203 | 30.996 |
| B2_vector_only | 22.760 | 22.566 | 24.609 |
| B3_vector_postfilter | 4.997 | 5.052 | 5.460 |
| B4_prefilter_vector | 17.060 | 19.910 | 37.509 |
| B5_hybrid | 42.912 | 44.117 | 67.496 |
