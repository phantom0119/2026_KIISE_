# B-1 확증 분석 — 코퍼스 A (prereg 420 [AMD-M7/M9])

## 확증 가족: s-밴드 × 방법쌍 ΔRecall@10 (Holm 보정)

          band                                              pair  n   delta              ci        p   p_holm sig
  high(>=0.25)         prefilter_hnsw_ef64 - postfilter_hnsw_K4x  5  0.4615   [0.288,0.615] 0.043114 0.129343    
  high(>=0.25) prefilter_hnsw_ef64 - single_stage_ivf_batch_np32  5  0.2278   [0.050,0.413] 0.079616 0.129343    
  high(>=0.25) postfilter_hnsw_K4x - single_stage_ivf_batch_np32  5 -0.2336 [-0.342,-0.137] 0.043114 0.129343    
    low(<0.05)         prefilter_hnsw_ef64 - postfilter_hnsw_K4x 13  0.7673   [0.716,0.820] 0.001474 0.013264   ✓
    low(<0.05) prefilter_hnsw_ef64 - single_stage_ivf_batch_np32 13  0.6070   [0.521,0.695] 0.001474 0.013264   ✓
    low(<0.05) postfilter_hnsw_K4x - single_stage_ivf_batch_np32 13 -0.1602 [-0.206,-0.115] 0.001474 0.013264   ✓
mid(0.05-0.25)         prefilter_hnsw_ef64 - postfilter_hnsw_K4x 11  0.6671   [0.586,0.738] 0.003346 0.020074   ✓
mid(0.05-0.25) prefilter_hnsw_ef64 - single_stage_ivf_batch_np32 11  0.4498   [0.312,0.579] 0.003346 0.020074   ✓
mid(0.05-0.25) postfilter_hnsw_K4x - single_stage_ivf_batch_np32 11 -0.2173 [-0.293,-0.145] 0.003346 0.020074   ✓

## M9: 동일-s 랜덤 대조군 − 실제 predicate (recall 과대평가량, Holm)

                     method  n_pairs  ctrl_minus_real            ci        p  p_holm            sig
             prefilter_flat       29           0.0000 [0.000,0.000]      NaN     NaN (Δ≡0, no test)
        prefilter_hnsw_ef64       29           0.0170 [0.012,0.023] 0.000003 0.00001              ✓
        postfilter_hnsw_K4x       29           0.6110 [0.554,0.661] 0.000003 0.00001              ✓
 single_stage_ivf_batch_np8       29           0.6269 [0.550,0.699] 0.000003 0.00001              ✓
single_stage_ivf_batch_np32       29           0.4976 [0.407,0.585] 0.000003 0.00001              ✓

## 메커니즘(기술): recall 결손 ↔ GT 군집 심도(전역 exact 중앙순위)

                     method  spearman_rho(deficit, gt_cluster_rank)  n
        postfilter_hnsw_K4x                                   0.699 29
single_stage_ivf_batch_np32                                   0.780 29

## 방법별 평균 (실제 predicate / 대조군 recall 병기 — 탐색적)

                              recall_at_10  p50_ms  p95_ms  recall_ctrl
method                                                                 
postfilter_hnsw_K1x                 0.2415  0.0648  0.0844       0.8569
postfilter_hnsw_K2x                 0.2791  0.0817  0.1083       0.9172
postfilter_hnsw_K4x                 0.3062  0.1017  0.1332       0.9172
prefilter_flat                      1.0000  1.4501  1.5639       1.0000
prefilter_hnsw_ef64                 0.9827  0.0377  0.0493       0.9998
single_stage_ivf_batch_np128        0.7348  0.1795  0.5400          NaN
single_stage_ivf_batch_np32         0.5007  0.0921  0.2099       0.9984
single_stage_ivf_batch_np8          0.3422  0.0648  0.0974       0.9691
single_stage_ivf_bitmap_np32        0.7503  0.1529  0.3984       0.9995
