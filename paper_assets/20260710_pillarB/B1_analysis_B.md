# B-1 확증 분석 — 코퍼스 B (prereg 420 [AMD-M7/M9])

## 확증 가족: s-밴드 × 방법쌍 ΔRecall@10 (Holm 보정)

          band                                              pair  n   delta              ci        p   p_holm sig
  high(>=0.25)         prefilter_hnsw_ef64 - postfilter_hnsw_K4x 12  0.2166   [0.123,0.325] 0.002218 0.019959   ✓
  high(>=0.25) prefilter_hnsw_ef64 - single_stage_ivf_batch_np32 12  0.0354   [0.005,0.083] 0.007686 0.035434   ✓
  high(>=0.25) postfilter_hnsw_K4x - single_stage_ivf_batch_np32 12 -0.1812 [-0.256,-0.111] 0.002218 0.019959   ✓
    low(<0.05)         prefilter_hnsw_ef64 - postfilter_hnsw_K4x  3  0.4850   [0.409,0.548] 0.108809 0.326428    
    low(<0.05) prefilter_hnsw_ef64 - single_stage_ivf_batch_np32  3  0.2040   [0.191,0.214] 0.108809 0.326428    
    low(<0.05) postfilter_hnsw_K4x - single_stage_ivf_batch_np32  3 -0.2810 [-0.335,-0.218] 0.108809 0.326428    
mid(0.05-0.25)         prefilter_hnsw_ef64 - postfilter_hnsw_K4x 10  0.4190   [0.340,0.506] 0.005062 0.035434   ✓
mid(0.05-0.25) prefilter_hnsw_ef64 - single_stage_ivf_batch_np32 10  0.1810   [0.121,0.238] 0.005062 0.035434   ✓
mid(0.05-0.25) postfilter_hnsw_K4x - single_stage_ivf_batch_np32 10 -0.2380 [-0.275,-0.203] 0.005062 0.035434   ✓

## M9: 동일-s 랜덤 대조군 − 실제 predicate (recall 과대평가량, Holm)

                     method  n_pairs  ctrl_minus_real            ci        p   p_holm            sig
             prefilter_flat       25           0.0000 [0.000,0.000]      NaN      NaN (Δ≡0, no test)
        prefilter_hnsw_ef64       25           0.0035 [0.002,0.006] 0.000089 0.000089              ✓
        postfilter_hnsw_K4x       25           0.2890 [0.219,0.359] 0.000012 0.000049              ✓
 single_stage_ivf_batch_np8       25           0.2173 [0.144,0.294] 0.000025 0.000076              ✓
single_stage_ivf_batch_np32       25           0.1155 [0.072,0.159] 0.000027 0.000076              ✓

## 메커니즘(기술): recall 결손 ↔ GT 군집 심도(전역 exact 중앙순위)

                     method  spearman_rho(deficit, gt_cluster_rank)  n
        postfilter_hnsw_K4x                                   0.616 25
single_stage_ivf_batch_np32                                   0.895 25

## 방법별 평균 (실제 predicate / 대조군 recall 병기 — 탐색적)

                              recall_at_10  p50_ms  p95_ms  recall_ctrl
method                                                                 
postfilter_hnsw_K1x                 0.5196  0.0542  0.0809       0.8752
postfilter_hnsw_K2x                 0.6138  0.0653  0.0955       0.9557
postfilter_hnsw_K4x                 0.6667  0.0817  0.1202       0.9557
prefilter_flat                      1.0000  3.2096  3.3574       1.0000
prefilter_hnsw_ef64                 0.9965  0.0403  0.0591       1.0000
single_stage_ivf_batch_np128        0.9786  0.2667  0.5234          NaN
single_stage_ivf_batch_np32         0.8826  0.1468  0.2418       0.9981
single_stage_ivf_batch_np8          0.7675  0.0759  0.0998       0.9848
single_stage_ivf_bitmap_np32        0.9603  0.1866  0.3296       0.9999
