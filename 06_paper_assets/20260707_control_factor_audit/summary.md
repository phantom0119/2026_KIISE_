# Experiment Control Factor Audit

created_at: `2026-07-07T07:17:25.502044+00:00`

## Verdict

- Main experiment artifacts are present and internally consistent.
- The experiment must be reproduced in `Datasets/envs/kiise-vlmdb`; the base Python environment is not the controlled environment.
- Text model diversity is covered by BGE-M3 and E5-large-v2. Visual-text model diversity is not covered beyond CLIP and should be stated as a limitation unless a SigLIP ablation is added.
- No new large dataset should be added before submission. Image query frame-position sensitivity is now tracked as a small control check.

## System Controls

- python_executable: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/envs/kiise-vlmdb/bin/python`
- python_version: `3.10.20`
- conda_prefix: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/envs/kiise-vlmdb`
- datasets_root: `/hdd2/KIISE_datasociety/Datasets`
- datasets_free_gib: `2342.29`

## Dataset Integrity

| dataset | role | clips | docs | metadata | queries | qrels | keyframes | frame errors | qrel target errors | metadata filter errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| vru_accident | main true multimodal 1 | 1000 | 7000 | 6000 | 244 | 5488 | 4000 | 0 | 0 | 0 |
| aihub_intelligent_cctv | main true multimodal 2 | 269 | 807 | 2563 | 133 | 1358 | 1076 | 0 | 0 | 0 |
| aihub_abnormal_cctv | supplementary text/metadata baseline | 1968 | 5904 | 33456 | 424 | 21639 | NA | NA | 0 | 0 |

## Model Compatibility

| dataset | bge shape ok | e5 shape ok | visual shape ok | visual model | visual dim |
|---|---:|---:|---:|---|---:|
| vru_accident | True | True | True | clip-vit-base-patch32 | 512 |
| aihub_intelligent_cctv | True | True | True | clip-vit-base-patch32 | 512 |

## User-Setting Controls

- Retrieval `top_ks` are fixed to 1, 5, 10, 20 in main runs.
- `max_rank` is fixed to 100 in main runs.
- Fusion uses RRF with `rrf_k=60`; weighted rerank sweep covers 4:1, 3:1, 2:1, 1:1, 1:2, 1:3, 1:4.
- Image-to-video main result uses `query_frame_seq=2`; sensitivity over frame positions 0, 1, 2, and 3 is tracked below.
- Keyframe extraction is fixed to 4 frames per clip: uniform for VRU and event-centered for AI Hub CCTV.

## Image Query Frame-Position Sensitivity

| dataset | query_frame_seq | queries | R@1 | R@5 | R@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| vru_accident | 0 | 1000 | 0.5960 | 0.8630 | 0.9020 | 0.7203 | 0.7630 |
| vru_accident | 1 | 1000 | 0.7320 | 0.9640 | 0.9810 | 0.8404 | 0.8755 |
| vru_accident | 2 | 1000 | 0.7550 | 0.9660 | 0.9800 | 0.8567 | 0.8875 |
| vru_accident | 3 | 1000 | 0.7330 | 0.9540 | 0.9680 | 0.8370 | 0.8694 |
| aihub_intelligent_cctv | 0 | 269 | 0.8550 | 0.9814 | 0.9963 | 0.9122 | 0.9330 |
| aihub_intelligent_cctv | 1 | 269 | 0.8476 | 0.9888 | 0.9963 | 0.9072 | 0.9295 |
| aihub_intelligent_cctv | 2 | 269 | 0.8810 | 0.9851 | 1.0000 | 0.9258 | 0.9442 |
| aihub_intelligent_cctv | 3 | 269 | 0.6952 | 0.8216 | 0.8327 | 0.7462 | 0.7673 |

## Additional Experiment Decision

| Candidate | Need before submission | Reason |
|---|---|---|
| New large dataset | No | High acquisition/preprocessing risk; current two true multimodal datasets are enough for the main claim. |
| SigLIP visual ablation | Optional | Useful for visual model diversity, but not required if CLIP-only is stated as a limitation. |
| Image query frame-position sensitivity | Completed as control | Directly addresses user-setting dependence of IM1; main paper should state qseq2 and report sensitivity as supplementary/control. |
| HNSW/IVFFlat | No | Would require separate latency/index tuning claims. |
| Controlled LLM answer generation | No | Would confound DB evidence quality with generation quality. |
