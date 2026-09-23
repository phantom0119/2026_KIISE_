# Retrieval Baseline Summary

created_at: `2026-07-12T03:38:31.425857+00:00`
canonical_root: `/hdd2/KIISE_datasociety/Datasets/processed/uca_anchor/20260712/canonical`
embedding_root: `/hdd2/KIISE_datasociety/Datasets/processed/uca_anchor/20260712/embeddings/bge-m3`

## Overall Metrics

| strategy | recall_at_1 | recall_at_5 | recall_at_10 | recall_at_20 | mrr | ndcg_at_10 |
|---|---:|---:|---:|---:|---:|---:|
| B0_metadata_only | 0.0027 | 0.0095 | 0.0180 | 0.0431 | 0.1825 | 0.0661 |
| B1_bm25_only | 0.0013 | 0.0032 | 0.0073 | 0.0163 | 0.1047 | 0.0404 |
| B2_vector_only | 0.0009 | 0.0052 | 0.0125 | 0.0238 | 0.1369 | 0.0600 |
| B3_vector_postfilter | 0.0080 | 0.0306 | 0.0569 | 0.0858 | 0.3760 | 0.2005 |
| B4_prefilter_vector | 0.0080 | 0.0311 | 0.0630 | 0.1112 | 0.3896 | 0.2085 |
| B5_hybrid | 0.0055 | 0.0306 | 0.0573 | 0.1073 | 0.3835 | 0.1983 |

## Latency

| strategy | mean ms | p50 ms | p95 ms |
|---|---:|---:|---:|
| B0_metadata_only | 0.204 | 0.091 | 0.488 |
| B1_bm25_only | 130.423 | 127.418 | 153.878 |
| B2_vector_only | 120.501 | 117.676 | 141.685 |
| B3_vector_postfilter | 5.132 | 5.037 | 5.969 |
| B4_prefilter_vector | 24.925 | 13.842 | 57.553 |
| B5_hybrid | 152.881 | 161.945 | 200.605 |
