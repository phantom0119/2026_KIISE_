# AI Hub 71953 Pipeline Audit

created_at: `2026-07-08T01:37:31.933717+00:00`
canonical_root: `Datasets/processed/aihub_multi_angle_cctv/20260708/canonical`
pass: `True`

## Counts

| item | value |
|---|---:|
| clips | 4500 |
| views | 9000 |
| evidence_frames | 27000 |
| documents | 36000 |
| metadata_rows | 63000 |
| queries | 4572 |
| qrels | 18000 |
| distinct_event_classes | 11 |

## Integrity

| check | errors |
|---|---:|
| qrel_target_errors | 0 |
| qrel_query_errors | 0 |
| missing_two_views | 0 |
| missing_c1c2_view_pairs | 0 |
| low_evidence_pairs | 0 |
| missing_filter_facets | 0 |
| empty_filter_candidates | 0 |
| positive_not_in_filter | 0 |

## Frame Materialization

| item | value |
|---|---:|
| frame_root | Datasets/processed/aihub_multi_angle_cctv/20260708/keyframes/evidence_sample_50 |
| frames | 300 |
| clips_with_frames | 50 |
| views_with_frames | 100 |
| missing_frame_files | 0 |
