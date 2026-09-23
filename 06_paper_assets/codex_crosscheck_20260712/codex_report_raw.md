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
