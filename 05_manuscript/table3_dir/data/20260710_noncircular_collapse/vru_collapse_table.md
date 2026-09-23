# VRU old(순환 v1) vs new(비순환 v2) collapse 대조표

v1 = 20260706 canonical (facet-statement 문서 + facet템플릿 질의 + qrel⊆filter) — 원고 표6 수치.
v2 = 20260710_noncircular (캡션-only corpus, relevance=사고유형 의미축, filter=독립 운영facet[weather/road/location]), n=85 queries, bge-m3.

| strategy | v1_circular_ndcg10 | v2_strict_ndcg10 | v2_semantic_ndcg10 | v1_circular_mrr | v2_strict_mrr |
|---|---|---|---|---|---|
| B0_metadata_only | 0.2102 | 0.1449 | 0.1356 | 0.2424 | 0.201 |
| B1_bm25_only | 0.4495 | 0.0918 | 0.1607 | 0.4791 | 0.2313 |
| B2_vector_only | 0.4476 | 0.1845 | 0.2649 | 0.4888 | 0.3741 |
| B3_vector_postfilter | 0.9488 | 0.302 | 0.2857 | 0.959 | 0.4832 |
| B4_prefilter_vector | 0.9736 | 0.3174 | 0.2974 | 0.9672 | 0.4832 |
| B5_hybrid | 0.9651 | 0.2771 | 0.261 | 0.9726 | 0.4076 |

핵심:
- B4 prefilter nDCG@10: **0.9736 → 0.3174** (strict) — '완벽 지표'는 워크로드 구성 artifact였음이 실측 확정
- B4−B2 격차: +0.526 → +0.133(strict, 합법적 filtered-search 이득) / +0.033(semantic-only)
- **semantic-only per-query B4−B2 부호: 음수 18 / 0 34 / 양수 33 (n=85)** — v1에서 구조적으로 불가능했던 음수 등장 = F1 보장 붕괴의 직접 증거
- B1 BM25: 0.4495 → 0.0918 — 정답라벨 재진술 문서 제거(F2)의 효과
- 결합도(사고유형 vs filter facet): road_type V=0.039 / weather V=0.177 / location V=0.249

재현: scripts/build_vru_noncircular_canonical.py → build_text_embeddings.py → run_retrieval_baselines.py; semantic 평가는 저장 랭킹 + qrels_semantic.tsv 후처리 (metrics_semantic.csv).