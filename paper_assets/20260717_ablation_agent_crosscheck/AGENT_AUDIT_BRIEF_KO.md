# 독립 에이전트용 ablation 감사 요청서

당신은 논문의 저자나 구현자가 아닌 독립적인 방법론·재현성 감사자다. 아래 로컬 산출물을 실제로 읽고, 요약문을 신뢰하지 말고 가능한 범위에서 CSV/JSON/Parquet와 구현 스크립트를 대조하라.

## 권한과 범위

- 읽기 전용 감사다. 파일을 생성·수정·삭제하지 말고, 실험을 재실행하거나 외부 통신을 하지 말라.
- 다른 에이전트의 평가를 보지 말고 독립적으로 판단하라.
- 결과가 유리하게 보이도록 결론을 보정하지 말라.
- 보고서는 한국어로 작성하되 설정명과 통계 용어는 원문 표기를 유지해도 된다.

## 핵심 감사 질문

1. `ABLATION_STUDY_PROTOCOL_KO.md`가 저장 표현, 검색/filter 배치, 색인 구조, 규모, seed, 외부 데이터, 순환성의 주요 대안을 충분히 분리하는가?
2. 각 주효과 비교에서 query/qrels/encoder와 나머지 축이 실제로 고정되어 있는가? 한 번에 둘 이상의 요인이 바뀐 비교를 단일 요인 효과로 잘못 부르는 곳이 있는가?
3. 91개 격자의 비호환 cell 제외가 정당하고, “완전 요인설계” 또는 “전역 최적”을 과장하지 않는가?
4. strict/semantic/task-fidelity 지표가 섞이지 않았는가? ANN의 근사 오차가 task quality 개선으로 오해되지 않게 처리됐는가?
5. paired query bootstrap, intent×facet/activity×facet cluster bootstrap, BH 보정, 3-seed 반복이 주장 강도에 맞는가? pseudoreplication, multiple testing, winner's curse가 남아 있는가?
6. 규모·외부·순환성 실험이 본 결과를 실제로 보강하는 범위와 보강하지 못하는 범위가 올바르게 적혀 있는가?
7. raw artifact에서 보고서 핵심 수치 중 최소 5개를 독립 확인하고, 확인한 파일/열/행 조건을 적어라.
8. 재현성 gate 32/32가 무엇을 보장하고 무엇을 보장하지 않는지 평가하라.
9. 논문에 ablation 결과를 넣기 전에 반드시 수정하거나 추가 실행해야 할 치명적 설계 오류가 있는가?

## 반드시 읽을 파일

- `ABLATION_STUDY_PROTOCOL_KO.md`
- `../20260717_joint_optimization_validation/FINAL_VALIDATION_REPORT_KO.md`
- `../20260717_joint_optimization_validation/REPRODUCIBILITY_RUNBOOK.md`
- `../20260717_joint_optimization_validation/configuration_summary.csv`
- `../20260717_joint_optimization_validation/paired_bootstrap_comparisons.csv`
- `../20260717_joint_optimization_validation/independent_verification.json`
- `../20260717_joint_optimization_validation/qwen2048_scaled_index/RESULTS_KO.md`
- `../20260717_joint_optimization_validation/qwen2048_seed_robustness/seed_results.csv`
- `../20260717_joint_optimization_validation/meva_same_encoder_control/RESULTS_KO.md`
- `../20260716_circularity_controlled_injection/RESULTS_KO.md`

필요하면 다음 구현도 읽어라.

- `../../scripts/run_joint_storage_search_index.py`
- `../../scripts/analyze_joint_optimization_validation.py`
- `../../scripts/verify_joint_optimization_independently.py`
- `../../scripts/run_index_structure_benchmark.py`
- `../../scripts/run_qwen2048_ann_seed_robustness.py`
- `../../scripts/run_circularity_controlled_injection.py`

## 출력 형식

1. 최종 판정: `PASS`, `PASS_WITH_LIMITATIONS`, `FAIL` 중 하나
2. 치명적/중대/경미 finding: 각각 근거 파일과 재현 가능한 확인 방법
3. 핵심 수치 교차검산 표: 주장, raw source, 독립 확인값, 일치 여부
4. ablation coverage 표: 축, 통제 적절성, 통계 적절성, 일반화 한계
5. 논문에서 가능한 주장 / 금지할 주장
6. 추가 실험: `필수`, `권고`, `불필요`로 구분
7. 감사 신뢰도와 읽지 못했거나 직접 검산하지 못한 항목

문체는 비판적으로 유지하고 2,500단어 이내로 작성하라.
