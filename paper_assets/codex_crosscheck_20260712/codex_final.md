74p;201,205p'" in /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE
 succeeded in 0ms:
   112	
   113	tri-source 85질의에서 B0(metadata-only)–B5(hybrid) 전략을 실행했다. strict 채점에서 B4(prefilter+vector)는 B2(vector-only)를 +0.0983(nDCG@10, 95% CI [0.068, 0.133])만큼 유의하게 앞선다 — predicate가 진짜 제약일 때 필터링의 고전적 가치다. 반면 **semantic 채점**에서는 통합 추정이 −0.016(CI [−0.047, 0.015])으로 유의하지 않고, 결합도에 따라 부호가 갈린다: 저결합 −0.036 [−0.065, −0.008], 자연결합 +0.134 [0.017, 0.249].
   114	
   115	질의 수준에서 (B4−B2)를 해당 쌍의 실측 V에 대응시키면 **단조 연속곡선**이 나타난다(그림 2): Spearman ρ=0.285(CI [0.071, 0.484], 0 배제), 구간 평균은 V<0.05에서 **−0.099**(n=27; V=0인 완전 독립 쌍 11개 포함), 0.05–0.15에서 −0.002, 0.15–0.3에서 +0.003, V≥0.3에서 **+0.134**다. 즉 소프트 의도 하에서 prefilter 가치의 부호는 predicate-정답 결합도가 결정하며, 집계 부호는 질의 믹스의 성질일 뿐이다.
   116	
   117	이 결론은 자기 교정의 산물이기도 하다. 최초 32질의(수작업으로 고른 초저결합 쌍 위주)에서는 semantic 손해가 −0.075로 유의했으나, 사전선언된 기계적 확장(교차곱, 동일 임계) 후 신규 53질의에서는 +0.020(비유의)으로 나타났고, 살아남은 것은 점추정이 아니라 곡선이었다. 표 2에 세 표본을 분리 보고한다. 이 경험은 필터드 검색 평가에서 **결합도 스펙트럼을 명시적 보고 축으로 삼아야 함**을 보여준다.
   118	
   119	![그림 2. 결합도 연속곡선: 질의별 Δ(B4−B2, semantic) 대 쌍의 실측 V. 굵은 선은 구간 평균(−0.099/−0.002/+0.003/+0.134).](2026_KIISE/paper_assets/20260711_v2_figures/fig1_coupling_curve.png){width=3.6in}
   120	
   121	**표 2. tri-source (B4−B2), semantic 채점 (nDCG@10)**
   170	### 7.3 색인 3축과 검색 Pareto
   171	
   172	두 실 코퍼스의 비필터 색인 그리드(Flat/IVF-Flat/HNSW/IVF-PQ)에서 3축(재현율, p50/p95, 색인 크기·구축 시간)을 측정했다. 131K/142K 실측에서 HNSW(ef64)는 재현율 0.997/0.9992에 p50 0.041/0.047ms로 Flat(13.4/14.2ms) 대비 약 300배 빠르고, IVF-PQ는 8–13MB로 22–35배 압축되나 재현율 0.33–0.49다. (p95, 재현율) 평면의 Pareto 전선은 두 코퍼스에서 구조적으로 동일하다(그림 3)(전선 12/46 구성: HNSW가 0.03–0.31ms 영역을 지배하고 Flat이 재현율 1.0의 앵커; 크기·구축 시간은 주석 축). 1M 규모 투영은 분포 보존 증강 데이터로만 보고하고 실측 주장에서 제외한다.
   173	
   174	![그림 3. 검색 Pareto 전선(두 실 코퍼스, p95 대 recall@10; 지배 판정은 두 축, 크기·구축 비용은 본문 표기).](2026_KIISE/paper_assets/20260711_v2_figures/fig2_retrieval_pareto.png){width=6.4in}
   201	**평가 방법론 교훈.** 순환성은 라벨이 풍부한 데이터셋일수록 쉽게 스며들며, 완벽 지표는 경고 신호다. 집계 결론은 질의 믹스에 좌우되므로(6절의 자기 교정), 결합도 스펙트럼과 이중 정답의 병행 보고가 프로토콜의 일부여야 한다.
   202	
   203	## 10. 한계와 향후 연구
   204	
   205	본 결과는 CLIP ViT-B/32 임베딩(색인·검색 실험)·주간 평일 기록·448px 프레임 조건에 한정되며, 색인→답변 결합 파일럿(8.2절)은 VLM 1종(Qwen2.5-VL)에 한정된다(답변 사다리는 생성기 2종, 다중 시점은 VLM 3종과 보조 1종에서 재현). 교차 카메라 조인은 동일 순간의 다른 뷰라는 근사를 포함한다. pgvector의 prefilter 대응물(부분 색인)은 측정하지 않았다. 악천후·시간대 카테고리 프레임(105,784장)은 센서 조인이 없어 큐레이션 predicate 기반 확장 트랙으로 남긴다. 국제 확장으로는 UCA[23]를 본 프로토콜의 2.5-채널(주석 정답, 큐레이션 predicate) 외적 타당성 코퍼스로 변환하는 것이 유망하다. 답변축은 두 벽을 넘는 설정에서의 재검증이 향후 과제다.

  ✓ Read governing docs and manuscript evidence map
  ✓ Inspect verification scripts and extracted checks
  ✓ Spot-check underlying assets for key claims
  ✓ Run verification suites or capture sandbox blocker
  ✓ Synthesize numbered adversarial findings with fixes
codex
I ran the checks: `run_full_verification_suite.py` passes 40/40 and `verify_manuscript_v2_numbers.py` passes 76/76 under `../Datasets/envs/kiise-vlmdb/bin/python`. That verifies number consistency, not all inferential validity.

1. [SEVERITY: BLOCKER] — `manuscript/kiise_dbr_manuscript_v2_noncircular.md`: §6 lines 113-117, §9 line 195; `project_md/500...`: lines 249-251 — coupling-continuum inference is pseudo-replicated.  
   Verified: `t3_coupling_curve.csv` has 85 query rows, but `V` is a predicate-type × relevance-definition property. Aggregating to 25 predicate×relevance pairs gives rho ≈ 0.272. Cluster bootstrap over pairs gives CI `[-0.036, 0.482]`; pair-bootstrap gives `[-0.173, 0.640]`. The V<0.05 bin is 27 query rows but only 8 pairs; cluster CI for its mean is `[-0.179, 0.013]`.  
   Fix: remove “CI excludes 0”, “determines”, and “monotone continuum” as confirmatory claims. Recompute CIs with pair/cluster bootstrap and make the curve exploratory unless it survives clustered inference.

2. [SEVERITY: MAJOR] — `canonical_trisource_expanded/A6_trisource_audit.json`: lines 5-33; `scripts/build_intersection_trisource_canonical.py`: lines 243-246; `captions/caption_manifest_shard0.json`: line 5 — A6 proves source/key separation, not prompt-target independence.  
   Verified: A6 checks machine tokens like `any_parked`, `max_objects`, `sig_has_`, `veh_density_bin`, `rel__`; it does not check semantic target terms. The caption prompt explicitly asks for traffic volume, buses, two-wheelers, stopped/parked vehicles, pedestrians/cyclists.  
   Fix: state “label/source leakage blocked” rather than “non-circularity 원천 차단”. Add a prompt-target coupling audit or re-caption with a task-agnostic prompt.

3. [SEVERITY: MAJOR] — `visual_sensor_join_stats.json`: lines 4-9; `manuscript`: §5.1 line 94 — residual temporal/scene coupling is real and not covered by A6.  
   Verified: cross-camera join rate is 90.18%, median gap is 0 seconds, same intersection+time. This is operationally valid, but temporal autocorrelation can correlate sensor predicates, captions, and annotations through the shared scene. Cramér’s V helps but is only marginal P-R dependence.  
   Fix: explicitly call this “same-moment cross-camera coupling”, not a leak-free independence guarantee. Use intersection/time-block bootstrap or report it as a limitation.

4. [SEVERITY: MAJOR] — `manuscript`: §8.2 lines 182-184; `project_md/420...`: lines 136-143; `project_md/630...`: lines 20-40 — the “perception wall” is too strongly closed.  
   Verified: mini-pilot is 360 VLM calls, with only 32 mediator-hit cases. `acc|hit=0.5625` vs `acc|no-hit=0.5823`, CI ≈ ±0.13. This supports a futility decision, not an established negative answer-layer result.  
   Fix: phrase as “pilot did not justify the preregistered full run” and “hypothesized perception bottleneck”. Do not say the wall is established unless the full powered run or a better mediator-randomized design is executed.

5. [SEVERITY: MAJOR] — `manuscript`: §6 line 129 — the parked-caption explanation is factually wrong.  
   Verified from `captions/documents.parquet`: 2,596/3,000 captions contain “parked”; 1,242 contain “no parked”. Cross-tab with annotation shows 59/69 annotated parked positives contain “parked”, but 2,537 non-parked negatives also contain it.  
   Fix: replace “captions do not describe parking” with “caption negation/overmention makes dense text retrieval confuse parked vs no-parked.”

6. [SEVERITY: MAJOR] — `project_md/430...`: §1.4 lines 35-42; `scripts/run_full_verification_suite.py`: lines 100-112; `scripts/build_intersection_trisource_canonical.py`: lines 70-74, 121-125 — V3 closes post-rule deletion, not all forking paths.  
   Verified: the suite re-derives the 85-query rule, but the expansion rule’s relevance-density window `[1%,12%]` admitted `two_plus_bikes` and rejected alternatives. The 12-value cap is not material here because `hour` has exactly 12 values, but the density window and SESOI choices remain researcher degrees of freedom.  
   Fix: add sensitivity tables for relevance-density thresholds, SESOI values, and candidate relevance definitions; explicitly say V3 guards “after rule declaration” selection, not all design-time choices.

7. [SEVERITY: MINOR] — `scripts/run_filtered_ann_real_predicate.py`: lines 350-353; `paper_assets/20260710_pillarB/B1_m9_control_{A,B}.csv` — same-selectivity random-mask control uses one random mask per predicate.  
   Verified: one `RNG.choice` mask is generated for each predicate. Large postfilter/selector gaps are robust-looking, but the small prefilter-HNSW deltas `+0.017/+0.0035` should not be overinterpreted.  
   Fix: repeat random controls across seeds or report seed sensitivity.

8. [SEVERITY: MINOR] — `manuscript`: §5.3 line 107, §7.2 line 157, §7.3 line 172, §9 line 195; `pgvector_manifest.json`: lines 6-7 — HW/SW latency control is mostly adequate, but operational thresholds are host-specific.  
   Verified: manuscript avoids FAISS↔pgvector latency ratios and states the boundary difference. The hot-predicate “~2K queries” rule comes from single-host FAISS build/latency amortization.  
   Fix: mark the ~2K/~2.4K thresholds as “on this i7-9700K, FAISS in-process, 132K/143K CLIP setup.”

9. [SEVERITY: NIT] — `manuscript`: §6 lines 115/119, §7.3 lines 172/174, §10 line 205 — mechanical manuscript errors remain.  
   Verified: first figure is called “그림 2” and Pareto is “그림 3” although no Figure 1 appears. Also `UCA[23]` is wrong; reference [23] is Idefics2, while UCA is [11,12].  
   Fix: renumber figures and change `UCA[23]` to `UCA[11,12]`.

**VERDICT:** The experimental system is not fake; the source-separated construction, collapse evidence, filtered-ANN benchmark, environment pinning, and verification suite are strong enough for a KIISE DBR submission. But it is not submission-ready as written. Must fix before submission: clustered coupling statistics and language, prompt-target coupling disclosure/audit, and answer-wall wording. Without those changes, the paper overclaims its most methodological headline.
tokens used
219,916
