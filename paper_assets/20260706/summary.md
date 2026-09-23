# Retrieval Paper Assets

created_at: `2026-07-06T08:45:19.343454+00:00`

## Best Overall Strategies

| model | best strategy | recall@10 | nDCG@10 | mean latency ms |
|---|---|---:|---:|---:|
| bge-m3 | B4 Prefilter | 0.7629 | 0.9736 | 49.442 |
| e5-large-v2 | B5 Hybrid | 0.7390 | 0.9229 | 178.970 |

## Tables

- `overall_csv`: `tables/table_overall_retrieval_metrics.csv`
- `overall_md`: `tables/table_overall_retrieval_metrics.md`
- `overall_tex`: `tables/table_overall_retrieval_metrics.tex`
- `difficulty_csv`: `tables/table_difficulty_retrieval_metrics.csv`
- `difficulty_md`: `tables/table_difficulty_retrieval_metrics.md`
- `difficulty_tex`: `tables/table_difficulty_retrieval_metrics.tex`
- `latency_csv`: `tables/table_latency_summary.csv`
- `latency_md`: `tables/table_latency_summary.md`
- `latency_tex`: `tables/table_latency_summary.tex`

## Figures

- `overall_quality`: `figures/fig_overall_quality_by_strategy.png`, `figures/fig_overall_quality_by_strategy.pdf`
- `latency`: `figures/fig_latency_by_strategy.png`, `figures/fig_latency_by_strategy.pdf`
- `difficulty_ndcg`: `figures/fig_difficulty_ndcg_heatmap.png`, `figures/fig_difficulty_ndcg_heatmap.pdf`
- `recall_latency_tradeoff`: `figures/fig_recall_latency_tradeoff.png`, `figures/fig_recall_latency_tradeoff.pdf`

## Paper Interpretation

- Metadata-aware strategies B3/B4/B5 consistently outperform BM25-only and vector-only baselines.
- bge-m3 favors B4 metadata prefilter + vector search in nDCG@10.
- e5-large-v2 favors B5 hybrid retrieval, showing that the modular protocol can expose model-dependent backend choices.
- The recall-latency trade-off figure should be used to frame the contribution as a database query planning problem, not only an embedding benchmark.
