# 이관 지도 — 2026-07-28 주제별 통합

원본 47개는 전부 `archive/legacy_premerge_20260728/`에 무손실 보존. 아래 표의 "통합 위치"가 현행 정리본이다.
실행 기록: 11개 병합 에이전트(주제 통합 6 + canonical EXP 흡수 5), SYNC 기준 paper_final.pdf(2026-07-23).

| 구 파일 | 통합 위치 |
|---|---|
| 000_MASTER.md | 00_MASTER_status_and_decisions.md |
| 010_OVERVIEW_EN.md | 00_MASTER_status_and_decisions.md (English Overview 절) |
| 020_GLOSSARY_concepts.md | 00_MASTER_status_and_decisions.md (용어 사전 절, 07-28 용어 결정 반영) |
| 650_MANUSCRIPT_v3_expansion_20260712.md | 00_MASTER_status_and_decisions.md (원고 버전 이력 절) |
| 000_Introduction.md | 10_INTRODUCTION_motivation_and_RQ.md (골격) |
| 100_INTRO_topic_selection_rationale.md | 10_INTRODUCTION_motivation_and_RQ.md §1.10 |
| 770_INTRO_structure_and_draft_20260714.md | 10_INTRODUCTION_motivation_and_RQ.md |
| 780_INTRO_filtered_vector_search_factcheck_20260714.md | 10_INTRODUCTION_motivation_and_RQ.md (불변 규칙 5종 보존) |
| 800_Introduction_20260714.md | 10_INTRODUCTION_motivation_and_RQ.md |
| 200_RELATED_uca_valu_review_20260710.md | 20_RELATED_WORK.md |
| 740_RELATED_reinforcement_design_review_20260714.md | 20_RELATED_WORK.md |
| 300_PROBLEM_critical_design_review_20260709.md | 30_METHODOLOGY_and_verification.md |
| 400_METHOD_experiment_system_masterplan_20260710.md | 30_METHODOLOGY_and_verification.md (Pillar↔RQ 매핑 포함) |
| 410_METHOD_prereg_multiview_answer_level_20260708.md | 30_METHODOLOGY_and_verification.md (사전등록 규칙 전량 보존) |
| 420_METHOD_prereg_pillarBE_design_20260710.md | 30_METHODOLOGY_and_verification.md (사전등록 규칙 전량 보존) |
| 430_METHOD_verification_framework_20260711.md | 30_METHODOLOGY_and_verification.md |
| 710_METHOD_db_experiment_priorities_20260713.md | 30_METHODOLOGY_and_verification.md |
| 740_AUDIT_experiment_structure_20260714.md | 30_METHODOLOGY_and_verification.md |
| 760_RESEARCH_FLOW_20260714.md | 30_METHODOLOGY_and_verification.md (상세본 정본) |
| 760_RESEARCH_FLOW_systematic_explanation_20260714.md | 30_METHODOLOGY_and_verification.md |
| 810_overall_blueprint_20260715.md | 30_METHODOLOGY_and_verification.md |
| 000_Datasets.md | 40_DATASETS_and_provenance.md |
| 500_DATASETS_construction_noncircular_execution_20260710.md | 40_DATASETS_and_provenance.md |
| 680_DATASET_foundation_audit_20260713.md | 40_DATASETS_and_provenance.md |
| 690_DATASET_overseas_verify_extend_20260713.md | 40_DATASETS_and_provenance.md |
| 730_DATASET_landscape_expanded_20260713.md | 40_DATASETS_and_provenance.md |
| 790_DATASET_TABLES_for_Notion_20260714.md | 40_DATASETS_and_provenance.md |
| DATA_PROVENANCE_raw_vs_derived_20260715.md | 40_DATASETS_and_provenance.md (계보 구분 전량 보존) |
| 910_REVIEW_response_and_supplementary_design_20260723.md | 60_REVIEW_response_and_supplements.md (verbatim) |
| 911_REVIEW_residual_audit_and_revision_20260723.md | 60_REVIEW_response_and_supplements.md (verbatim) |
| 912_SUPPLEMENT_CONTROL_PROTOCOL_FROZEN_20260723.md | 60_REVIEW_response_and_supplements.md (FROZEN 무변경 verbatim) |
| 913_CONTROLLED_SUPPLEMENT_RESULTS_20260723.md | 60_REVIEW_response_and_supplements.md (verbatim) |
| 914_REVIEWER_RISK_REGISTER_20260723.md | 60_REVIEW_response_and_supplements.md (verbatim) |
| 670_P9_KG_extension_collapse_20260713.md | canonical/experiments/EXP02 흡수 섹션 |
| 600_RESULTS_index_structure_benchmark_20260709.md | canonical/experiments/EXP03 흡수 섹션 |
| 620_RESULTS_filtered_ann_real_predicates_20260710.md | canonical/experiments/EXP03 흡수 섹션 |
| 720_RESULTS_db_design_storage_index_20260713.md | canonical/experiments/EXP03 흡수 섹션 (P1 저장단위는 RQ2 상충 정정 포함) |
| 750_RAG_baseline_contract_20260714.md | canonical/experiments/EXP04 흡수 섹션 |
| 750_UNIFIED_EMBEDDING_baseline_framing_20260714.md | canonical/experiments/EXP04 흡수 섹션 |
| 810_CAPTION_MODEL_ABLATION_20260715.md | canonical/experiments/EXP04 흡수 섹션 |
| 820_JOINT_IMAGE_CAPTION_SINGLE_VECTOR_PROTOCOL_20260717.md | canonical/experiments/EXP04 흡수 섹션 |
| 821_RESULTS_joint_image_caption_single_vector_20260717.md | canonical/experiments/EXP04 흡수 섹션 |
| 610_RESULTS_multiview_four_vlm_recheck_20260709.md | canonical/experiments/EXP05 흡수 섹션 |
| 630_RESULTS_answer_coupling_closure_20260711.md | canonical/experiments/EXP05 흡수 섹션 |
| 660_GOAL3_regime_characterization_20260713.md | canonical/experiments/EXP05 흡수 섹션 |
| 640_RESULTS_uca_external_20260712.md | canonical/experiments/EXP06 흡수 섹션 |
| 700_MEVA_integration_execution_20260713.md | canonical/experiments/EXP06 흡수 섹션 |
| 900_ECIR2027_Introduction_management.md | 90_ECIR2027_multimodal_paper_intro_management.md (개명만, 별도 논문) |

## 스크립트 참조 갱신 (5건)

`scripts/eval_multiview_answer_vlm.py`, `run_multiview_answer_vlm.py`, `run_coupling_blocked_validation.py`,
`run_full_verification_suite.py`, `run_filtered_ann_cluster_mechanism.py`의 구경로 참조(410·420·500·630·912)를
`project_md/archive/legacy_premerge_20260728/` 경로로 일괄 갱신했다.

## PI 확인 필요 사항 (통합 중 발견)

1. **EXP02 §9 포인터**: `trisource_522_final_metrics.csv`가 확장 전(522) 런 수치 — 확장(3,000/85) 정본 CSV로 갱신할지 결정 필요.
2. **750 계약 B5 hybrid 0.135 vs 논문 혼합 RRF 0.133**: 반올림으로 설명 불가한 스냅샷 차이 — 파이프라인 수정 이력 확인 권장.
3. **RQ6 '무관 53%' 셀 출처**: Qwen 0.5383(→54%) / Llama 0.5283 / 평균 0.5333 중 논문 표기 기준 확인 권장.
4. **EXP06 UCA 135(구축)/129(분석)**: §2 표에 각주 추가 여부.
5. **UNIFY 서지 상충**: 'Liang et al. PVLDB 18(4)' vs 'PVLDB 2025 p1118-yao' — 인용 전 원문 확인.
6. **914 체크리스트 미완 3건**: 아티팩트 URL, 개정 PDF 지면 검수(러닝 헤드 포함), 재배포·윤리 문구.
