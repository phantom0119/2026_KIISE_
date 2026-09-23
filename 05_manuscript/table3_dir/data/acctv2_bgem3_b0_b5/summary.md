# Retrieval Baseline Summary

created_at: `2026-07-09T19:32:37.917796+00:00`
canonical_root: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_intelligent_cctv/20260710_noncircular/canonical`
embedding_root: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_intelligent_cctv/20260710_noncircular/embeddings/bge-m3`

## Overall Metrics

| strategy | recall_at_1 | recall_at_5 | recall_at_10 | recall_at_20 | mrr | ndcg_at_10 |
|---|---:|---:|---:|---:|---:|---:|
| B0_metadata_only | 0.0118 | 0.0589 | 0.1178 | 0.1840 | 0.2893 | 0.2778 |
| B1_bm25_only | 0.0023 | 0.0124 | 0.0248 | 0.0495 | 0.1334 | 0.1111 |
| B2_vector_only | 0.0227 | 0.1161 | 0.2015 | 0.3937 | 0.7811 | 0.6285 |
| B3_vector_postfilter | 0.0373 | 0.1732 | 0.3371 | 0.5572 | 0.9306 | 0.8395 |
| B4_prefilter_vector | 0.0373 | 0.1732 | 0.3371 | 0.5572 | 0.9306 | 0.8395 |
| B5_hybrid | 0.0180 | 0.1194 | 0.2597 | 0.3962 | 0.5812 | 0.5537 |

## Latency

| strategy | mean ms | p50 ms | p95 ms |
|---|---:|---:|---:|
| B0_metadata_only | 0.025 | 0.023 | 0.040 |
| B1_bm25_only | 5.298 | 4.518 | 6.795 |
| B2_vector_only | 6.023 | 4.288 | 9.106 |
| B3_vector_postfilter | 3.542 | 3.211 | 4.263 |
| B4_prefilter_vector | 2.879 | 2.578 | 4.805 |
| B5_hybrid | 7.364 | 7.162 | 9.065 |
