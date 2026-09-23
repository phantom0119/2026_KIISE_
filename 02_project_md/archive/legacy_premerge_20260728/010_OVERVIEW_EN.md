# Storage, Indexing, and Retrieval Structures for Multimodal Urban-Surveillance VLM-QA
### Research Overview — English Companion Document

*Last updated: 2026-07-10. This is the representative English summary of the project. The operational (Korean) master document is [`000_MASTER.md`](000_MASTER.md); the full document index is [`README.md`](README.md).*

---

## 1. Research Topic and Design Direction (locked)

**Topic (fixed — no scope reduction):**

> *Which storage, indexing, and retrieval structures best support VLM-based question answering — more accurately, faster, and at lower cost — when natural-language queries and metadata conditions are given together over multimodal urban-surveillance data (images/video + incident reports + sensor/spatiotemporal metadata)?*

**The central research instrument we build and use:**

> *A non-circular multimodal workload to evaluate which search, index, and storage structures best support VLM-based responses when natural-language queries and sensor/spatiotemporal metadata conditions are given together in urban surveillance video.*

Three research-question axes:

| Axis | Question |
|---|---|
| **RQ-S** (structures) | How do retrieval strategies (sparse/dense/filtered), index structures (Flat / IVF-Flat / HNSW / IVF-PQ; FAISS and pgvector), and storage policies compare? |
| **RQ-ALC** (accuracy · latency · cost) | What are the three-axis trade-offs, measured with isolated latency and explicit cost proxies (index size, build time, GPU-seconds)? |
| **RQ-M** (multimodality) | Does the combination of visual frames + reports/captions + sensor/spatiotemporal metadata actually change what the right structure is, and does it propagate to VLM answer quality? |

**Design direction.** The project deliberately puts *experiment-system completeness before manuscript writing*. Every headline experiment must pass:

1. **Non-circularity by construction** — the filter predicate, the relevance definition, and the searched documents come from *different sources* (different cameras, different files, different producers), enforced by a machine-checked audit (the "A6 audit": disjoint filter/relevance keys; zero answer-restating documents; sparse relevance; the sign distribution of B4−B2 must contain negatives).
2. **Dual ground truth** — every filtered-retrieval experiment is scored twice: *strict* (relevant = semantic match **and** predicate holds; the classic filtered-search setting where prefiltering can only help) and *semantic-only* (relevant = semantic match regardless of the predicate; prefiltering may legitimately *hurt*). Reporting both is what makes the comparison honest.
3. **Preregistration + adversarial design review** — designs are written and locked *before* execution (e.g., `44_pillarBE_prereg_design`), then attacked by independent reviewer lenses (DB-systems / statistics / measurement-honesty); execution starts only after blocker fixes are folded in.
4. **Honesty gates** — ANN/scale claims only at ≥100K-vector corpora; synthetic augmentation labeled and never used for headline claims; single-thread isolated latency with the explicit caveat that it is a search-layer metric, not end-to-end serving latency; bootstrap CIs and multiplicity control on every headline comparison.

This discipline exists for a concrete reason: an internal 10-dimension adversarial review (`41_critical_design_review`) found that the *original* retrieval headline of the v1 manuscript was **circular** — the metadata filter was a subset of the very facets that defined the answers, and the corpus contained label-restating documents, which structurally guaranteed prefilter ≥ vector-only and produced perfect scores (MRR = nDCG = 1.0000). Fixing that defect and realizing the ambitious topic turned out to be **the same piece of work**, because genuinely exogenous sensor predicates are exactly what breaks the circularity.

---

## 2. Goals, and an Open Question About the Core Contribution

**Committed goals (what "done" means):**

1. A **non-circular, tri-source evaluation workload** over real urban-surveillance data, with machine-checked audits and dual ground truth (built — see §4).
2. **Structure comparisons on that workload**: retrieval strategies, filtered-ANN plans (prefilter / postfilter / single-stage), index structures, and a relational backend (pgvector with real HNSW/IVF indexes), each with CIs.
3. The **accuracy–latency–cost triangle** measured, including the causal link from index approximation to *answer* accuracy with a fixed VLM/LLM (mediated through evidence recall).
4. **Actionable guidelines** — e.g., our already-verified finding that *the value of metadata prefiltering depends on whether the predicate is a hard constraint or a soft preference, and on how strongly it couples with the semantic need*.
5. A manuscript in which every number survives the adversarial review that killed the v1 headline.

**Open framing decision (deliberately kept open until the evidence settles it):**

> *We can attempt to determine whether the core contribution of this study is the "proposal of a new evaluation workload (benchmark)" itself, or "finding the optimal structure and providing guidelines" through that workload.*

Current evidence supports both candidate framings:

- **Framing A — the workload/benchmark is the contribution.** What is genuinely new is the *construction*: source-separated channels (sensor CSVs from one camera, human annotations from other cameras, VLM captions from pixels only), the A6 non-circularity audit as a reusable protocol, dual strict/semantic ground truth, and the demonstrated *collapse* of a circular workload's perfect scores when the protocol is applied. This framing is robust even if individual structure rankings turn out to be corpus-specific.
- **Framing B — the guidelines are the contribution.** The workload already yields a clean, mechanism-level finding (prefiltering helps under hard constraints, +0.145 nDCG CI [0.08, 0.22]; *hurts significantly* under soft intent, −0.075 CI [−0.13, −0.01]; the harm concentrates exactly in low-coupling predicate–relevance pairs). If the Pillar B/E experiments produce equally clean index/latency/cost guidelines that replicate across our two real corpora, the guideline framing becomes the stronger paper.

The decision rule we are working toward: **if the structure-level findings replicate across corpora and generators, lead with Framing B and present the workload as the enabling method; otherwise lead with Framing A and present the findings as demonstrations.** Both framings keep the same locked topic; only the emphasis of the contributions section changes.

---

## 3. Why "Non-Circular" Is the Load-Bearing Word

The v1 workload defined queries from facet templates, defined answers as the clips matching those same facets, applied the *same* facets as the metadata filter, and inserted facet-statement documents (e.g., "accident type: X") into the searched corpus. Under that construction:

- prefilter ≥ vector-only is guaranteed *by construction* (the filter can never remove a relevant clip);
- BM25 achieves near-perfect scores by literal label-string matching;
- nothing about real system behavior is measured.

We proved this empirically by **repairing the workloads and re-measuring** (`43`, assets in `paper_assets/20260710_noncircular_collapse/`):

| nDCG@10 | circular v1 | repaired v2 (strict) | repaired v2 (semantic) |
|---|---:|---:|---:|
| VRU B4 (prefilter+vector) | 0.9736 | 0.3174 | 0.2974 |
| VRU B2 (vector-only) | 0.4476 | 0.1845 | 0.2649 |
| Intelligent-CCTV B1 (BM25) | 0.9600 | 0.1111 | — |
| Intelligent-CCTV B4 | 1.0000 | 0.8395 | 0.8395 |

Under semantic-only scoring the per-query sign of B4−B2 becomes **negative for 18/85 queries** (VRU) — an outcome that was *structurally impossible* in v1. That sign flip is the empirical proof that the guarantee is broken, and it is now one of the audit assertions every new workload must pass.

---

## 4. The Tri-Source Workload (built and audited)

The headline workload combines three **independently produced** channels over the same 63 real intersections:

| Channel | Source | Role |
|---|---|---|
| **Documents** (searched) | Qwen2.5-VL dense captions of frame pixels only — the captioner never sees sensor data or annotations | what dense/sparse retrieval operates on |
| **Predicates** (filter) | Per-vehicle / per-pedestrian sensor label CSVs from camera `…10` (signal phase, lane, departure time, counts, time-of-day) | exogenous, operational filter conditions |
| **Relevance** (ground truth) | Human CVAT annotations (trajectories, boxes, `is_stopped` / `is_parked`, 8 vehicle types) from cameras `…11`/`…22` | sparse scene events (median density 3.6%) |

Key verified facts: sensor and visual cameras were recorded in **synchronized sessions** (90.2% of visual videos have a same-intersection sensor clip within ±120 s; median gap 0 s), so the cross-camera join is the same stream-join a real surveillance DB performs. Independence is *quantified*, not assumed: 25/30 predicate×relevance pairs have Cramér's V < 0.3 (best pairs ≈ 0.005–0.05); naturally coupled pairs (rush-hour × stopped traffic) are kept as an explicit "coupling-continuum" contrast arm rather than discarded.

Final build: **3,000-video captioned corpus, 32 queries (23 low-coupling + 9 contrast), dual qrels (strict 1,472 / semantic 9,062), A6 audit 6/6 PASS.**

---

## 5. Datasets — Construction Status, Purpose, and Method

**Acquisition verdict (final): no new datasets are needed.** Every modality the topic requires already exists on disk; all remaining work is materialization and integration. All processing uses the pinned environment `Datasets/envs/kiise-vlmdb` (PyTorch 2.12/cu130, transformers 5.13, FAISS 1.14.3), and artifacts live under `Datasets/processed/<dataset>/<version>/`.

### 5.1 AI Hub 522 "Intersection Signal System" — *the multimodal headline anchor*

- **Raw contents (verified on disk):** label zips with per-vehicle CSVs (`signal phase, departure time, car type, lane, movement`) and per-pedestrian CSVs (`type, time, direction`) for **32,880 clips × 63 intersections**; `TS_3/VS_3` archives that turn out to contain **pre-extracted JPG frames** (143,830 frames ≈ 3/video — no video decoding ever needed; solid 7z despite the .zip extension); CVAT XML annotation sets (`TL_3` trajectories, `TL_4` boxes with environment categories); `TS_4/VS_4` frames for the weather/time-slot categories (105,784 frames). The numeric raw feeds (`TS_1/TS_2`) are empty "undisclosed" placeholders — **not needed**, the label CSVs carry the sensor records.
- **Built artifacts:** `sensor_facets.parquet` (32,880 clips; predicate + scene facets, all `facet_source='sensor_csv'`); `visual_sensor_join.parquet` (52,462 visual videos; 47,308 joined ≤120 s); `annotation_video_facets.parquet` (52,210 videos with human-annotation relevance); `captions/documents.parquet` (3,000 VLM captions, source-separated); `canonical_trisource/` (the audited workload of §4); CLIP ViT-B/32 frame embeddings for all 143,830 frames (512-d, encoder-identical to the sinnaedoro corpus — *in progress, ~2/3 remaining at the time of writing*).
- **Purpose:** realizes the sensor/spatiotemporal modality; supplies exogenous predicates that break circularity; provides the second *real* 143K-vector corpus for filtered-ANN and index benchmarks; programmatically verifiable sensor QA for the answer layer.
- **Method summary:** streaming zip/7z extraction (block-aligned, single pass); CSV aggregation into per-clip facets; camera-code normalization (`…10` = sensor, `…11/22` = visual) + timestamp join; XML parsing into per-frame/per-video relevance events; VLM captioning with a strict source-separation contract and token-leak assertion.
- **Honest caveats (recorded):** weekday/daytime recordings only; the weather (악천후) and time-slot (시간대) frame sets come from *separate recording campaigns* with **0% sensor join** — for those extension tracks the exogenous predicate is the curation category + filename time, not the sensor stream.

### 5.2 VRU-Accident — *answer-layer anchor + circularity case study*

- **Status:** 1,000 mp4 dashcam-style accident clips with dense captions and 6-category multiple-choice VQA; canonical v1 (circular) preserved for the collapse comparison; **repaired non-circular v2 built** (caption-only corpus; relevance = accident-type semantic axis; filters = independent operational facets; dual qrels; audit PASS).
- **Purpose:** (a) the fixed-generator answer-layer experiment — accuracy rises monotonically closed-book 0.31 → oracle 0.75 with the LLM held fixed (n = 600, 2 LLMs); (b) the E-1 experiment linking index approximation → evidence recall → answer accuracy (to run on all 6,000 VQA items per the power analysis); (c) the before/after collapse table.
- **Caveat:** traffic-safety/dashcam footage, not fixed urban CCTV — always described conservatively.

### 5.3 Sinnaedoro (urban-road) CCTV — *index-scale corpus*

- **Status:** **132,521 real CLIP vectors** (512-d) with real spatiotemporal metadata (39 locations, 51 dates, 18 hours; natural selectivities ~1e-4…0.18, inventoried in `predicate_inventory.csv`), plus a distribution-preserving synthetic 1M augmentation (always labeled synthetic). Full index benchmark already computed: Flat / IVF-Flat / HNSW / IVF-PQ × recall@10 × p50/p95 latency × index MB × build seconds, N = 10K…1M; plus a filtered-ANN selectivity study (to be re-run with the real predicates replacing the original random masks).
- **Purpose:** the RQ-S/RQ-ALC scale axis — where ANN trade-offs are real (e.g., HNSW p50 0.04 ms vs Flat 13.4 ms at 131K; IVF-PQ 33× compression at recall 0.33–0.48).

### 5.4 AI Hub Multi-Angle CCTV — *"select, don't accumulate" anchor*

- **Status:** 4,500 events × two views; preregistered answer-level experiment complete (400-clip bbox-asymmetry stratum): better-view > worse-view significant in 3–4 VLMs; both-views ≈ better-view (TOST-equivalent). Kept unchanged as a manuscript anchor.
- **Purpose:** evidence *selection* over accumulation at the answer layer; multi-view dimension of RQ-M.

### 5.5 AI Hub Intelligent CCTV (269 clips) & Abnormal-Behavior CCTV (1,968 clips)

- **Status:** canonical + repaired non-circular v2 (Intelligent); text/metadata baselines (Abnormal).
- **Purpose:** schema portability and Korean-language external validity only — never main claims. The repaired v2 also exposed an honest cross-lingual signal (multilingual dense 0.82 nDCG vs BM25 0.17 on Korean captions).

### 5.6 CityFlow-NL — *deferred*

- **Status:** annotations canonicalized; frames not yet extracted. Excluded from all main numbers; kept as a future NL-vehicle-retrieval extension.

---

## 6. Verified Results So Far (all with CIs, reproducible from result files)

1. **Circularity proven and repaired** (§3) — the collapse table is itself a publishable diagnostic.
2. **New headline finding:** metadata prefiltering helps **iff the predicate is a hard constraint** (strict: +0.145 CI [0.082, 0.216]); under soft intent it **hurts significantly** (−0.075 CI [−0.133, −0.012]; negative for 16/32 queries), and the harm concentrates in independent (low-coupling) predicate–relevance pairs (−0.131 CI [−0.191, −0.075]) while vanishing for naturally coupled pairs — the mechanism, not just the effect.
3. **Metadata-only retrieval (B0) beats dense retrieval (B2)** under strict scoring on the tri-source workload (0.165 vs 0.064 nDCG) — sensor metadata alone is a strong baseline for sparse scene events.
4. **VLM captions have systematic blind spots as DB documents** — parked-vehicle queries score ≈ 0 in dense retrieval because captions rarely mention parking; a document-coverage finding for caption-based indexing.
5. **Answer layer and multi-view anchors** (5.2, 5.4) unchanged and robust.
6. **Index three-axis numbers** (5.3) computed and ready for promotion into the manuscript.

---

## 7. Current Execution State and Next Steps

- **In flight:** CLIP embedding of the 522 frame corpus (143,830 frames, 2 GPUs).
- **Locked and adversarially reviewed:** the Pillar B/E preregistration (`44`) covering real-predicate filtered-ANN on two real corpora, index benchmarks, pgvector with real HNSW/IVF indexes, the index-approximation → answer-accuracy experiment, and the 3-axis Pareto synthesis. An independent 3-lens design attack returned 5 blockers (all evidence-verified — e.g., a mediator variable that would have been identically zero, and a sample size mathematically incompatible with the preregistered equivalence margin); these fixes are being folded into the spec **before** execution.
- **Then:** manuscript rewrite around the new headline structure (demote the v1 circular tables to a diagnostic; lead with the non-circular workload + guidelines; add the index/latency/cost section; cite ForeSea/UrBench; add data/code availability).

---

## 8. Repository Map (short)

| What | Where |
|---|---|
| Korean master doc / doc index | `project_md/000_MASTER.md` / `project_md/README.md` |
| Critical review · master plan · execution log · B/E prereg | `project_md/41 · 42 · 43 · 44` |
| Collapse & significance assets | `paper_assets/20260710_noncircular_collapse/` |
| Tri-source workload | `Datasets/processed/aihub_522_intersection/20260710/canonical_trisource/` |
| Index benchmark corpus & results | `Datasets/processed/sinnaedoro_traffic/` |
| Manuscript v1 (to be rewritten) | `manuscript/kiise_dbr_manuscript_v1_true_multimodal.md` |
| Historical research log (36 docs) | `project_md/archive/` |
