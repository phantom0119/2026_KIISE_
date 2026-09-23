# 522 tri-source 최종 결과 (비순환 시각 워크로드, 3,000 corpus / 32 queries)

채널 완전 분리: 문서=VLM캡션(픽셀만) / predicate=센서CSV(카메라10) / relevance=사람 CVAT주석(카메라11/22). A6 감사 6/6 PASS.

## B0–B5 (strict vs semantic)

| strategy | recall_at_10_strict | mrr_strict | ndcg_at_10_strict | recall_at_10_semantic | mrr_semantic | ndcg_at_10_semantic |
|---|---|---|---|---|---|---|
| B0_metadata_only | 0.0405 | 0.401 | 0.1646 | 0.0073 | 0.401 | 0.1646 |
| B1_bm25_only | 0.0002 | 0.0222 | 0.003 | 0.0005 | 0.0917 | 0.0304 |
| B2_vector_only | 0.013 | 0.1927 | 0.0643 | 0.0108 | 0.4624 | 0.2833 |
| B3_vector_postfilter | 0.043 | 0.3621 | 0.2041 | 0.0067 | 0.3621 | 0.2041 |
| B4_prefilter_vector | 0.0476 | 0.3726 | 0.2088 | 0.0069 | 0.3726 | 0.2088 |
| B5_hybrid | 0.0474 | 0.3432 | 0.1864 | 0.0064 | 0.3432 | 0.1864 |

## B4−B2 유의성 (nDCG@10, paired bootstrap 5000 + Wilcoxon)

| case | n | delta | ci | boot_p | wilcoxon_p | sign |
|---|---|---|---|---|---|---|
| 522 strict | 32 | 0.1445 | [0.082,0.216] | 0.0002 | 0.00013 | neg 0/zero 13/pos 19 |
| 522 semantic | 32 | -0.0745 | [-0.133,-0.012] | 0.0168 | 0.03449 | neg 16/zero 8/pos 8 |
| 522 semantic/low-coupling | 23 | -0.1308 | [-0.191,-0.075] | 0.0002 | 0.00135 | neg 13/zero 7/pos 3 |
| 522 semantic/contrast | 9 | 0.0693 | [-0.033,0.171] | 0.184 | 0.20758 | neg 3/zero 1/pos 5 |

## 핵심 발견 (헤드라인 후보)
1. **hard constraint(strict)**: prefilter 유의 이득 +0.1445 CI[0.082,0.216] — 진짜 filtered-search 가치.
2. **soft intent(semantic)**: prefilter가 유의하게 **해침** −0.0745 CI[−0.133,−0.012] (neg 16/32).
3. **메커니즘 분해**: 손해는 predicate⟂relevance인 low-coupling 쌍에 집중(−0.1308 CI[−0.191,−0.075]); 자연결합 contrast 쌍은 +0.069 n.s. — '독립 predicate로 soft 필터링 = 관련 문서 폐기'라는 이론 예측 그대로.
4. 희소 relevance×강한 predicate에서 **B0 metadata-only(0.165)가 B2 dense(0.064)를 상회**(strict) — 센서 메타데이터 단독의 가치.
5. 캡션 채널의 맹점(정직 보고): parked_vehicle 쌍은 dense 검색 ~0 — VLM 캡션이 '주차'를 잘 서술하지 않음. DB 문서로서 VLM 캡션의 체계적 커버리지 한계.

재현: build_intersection_captions.py(3,000, 2-GPU) → build_intersection_trisource_canonical.py → build_text_embeddings.py → run_retrieval_baselines.py; semantic=저장 랭킹+qrels_semantic 후처리.