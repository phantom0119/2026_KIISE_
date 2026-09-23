# 독립 검산

- overall: **PASS**
- gates: 32/32
- 프로젝트 metric helper를 import하지 않고 raw ranking에서 nDCG/MRR/recall을 재계산했다.

| scope | gate | result |
|---|---|---|
| joint_522 | config_count | PASS |
| joint_522 | query_count | PASS |
| joint_522 | metric_row_count | PASS |
| joint_522 | ndcg_recompute | PASS |
| joint_522 | mrr_recompute | PASS |
| joint_522 | recall_recompute | PASS |
| joint_522 | ranking_unique_within_query | PASS |
| joint_522 | rank_bounds | PASS |
| meva | config_count | PASS |
| meva | query_count | PASS |
| meva | metric_row_count | PASS |
| meva | ndcg_recompute | PASS |
| meva | mrr_recompute | PASS |
| meva | recall_recompute | PASS |
| meva | ranking_unique_within_query | PASS |
| meva | rank_bounds | PASS |
| assets_522 | query_vectors | PASS |
| assets_522 | caption_vectors | PASS |
| assets_522 | representative_vectors | PASS |
| assets_522 | full_frame_vectors | PASS |
| assets_meva | query_vectors | PASS |
| assets_meva | caption_vectors | PASS |
| assets_meva | frame_vectors | PASS |
| scaled_index | row_count | PASS |
| scaled_index | ivf_training_minimum | PASS |
| scaled_index | fixed_seed_manifest | PASS |
| scaled_index | metric_bounds | PASS |
| seed_robustness | three_seeds_per_config | PASS |
| seed_robustness | seed_set | PASS |
| seed_robustness | metric_bounds | PASS |
| hashes | joint_qrels_hash | PASS |
| hashes | meva_qrels_hash | PASS |
