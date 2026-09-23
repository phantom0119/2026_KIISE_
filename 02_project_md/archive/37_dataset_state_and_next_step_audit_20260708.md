# Dataset State and Next-step Audit

작성 기준일: 2026-07-08

2026-07-09 최신 갱신: 본 문서에서 "다음 단계"로 제안했던 원고 정합성 보강, manifest 보강, InternVL cross-model 복제는 이후 대부분 완료되었다. 4개 VLM 결과 디렉터리와 run manifest는 `38_four_vlm_multiview_final_recheck_20260709.md`에서 재검증되었고, 최신 종합 상태는 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다. 따라서 이 문서는 2026-07-08 중간 감사 기록으로 보존하며, 현재 실행 우선순위는 추가 실험보다 제출 전 품질관리다.

## 판정

다른 에이전트가 수행한 다각도 CCTV answer-level VLM 실험 산출물은 실제로 존재하며, 데이터셋 물리 상태와 결과 파일의 기본 무결성은 대체로 정상이다. 다만 원고에 반영된 일부 문장은 현재 산출물과 모순되므로, 추가 실험보다 먼저 원고 정합성 수정과 재현성 manifest 보강이 필요하다.

즉, **InternVL cross-family 복제나 초록 확장으로 바로 넘어가기 전에 원고/manifest 정합성 보강을 선행**해야 한다.

## 확인한 주요 산출물

### 사전등록 및 결과 문서

- 사전등록: `2026_KIISE/project_md/35_multiview_answer_level_prereg_20260708.md`
- 결과 문서: `2026_KIISE/project_md/36_multiview_answer_level_results_20260708.md`
- 원고 반영본: `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal.md`
- PDF: `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal_DBR_review.pdf`

PDF 상태:

- A4, 15 pages
- 생성 시각: 2026-07-08 19:56 KST

### 다각도 stratum

- stratum manifest: `Datasets/processed/aihub_multi_angle_cctv/20260708/samples/bbox_asymmetry_stratum/stratum_manifest.parquet`
- sampled clips: 400
- asymmetric: 250
- symmetric: 150
- better_view count: c1=252, c2=148
- 전체 class 수: 11

표본 class 분포:

| event_class | count |
|---|---:|
| 비정상적인 경로로의 침범 | 45 |
| 오토바이 인도 주행 | 43 |
| 자전거 인도 주행 | 42 |
| 특정 인물을 뒤따라가며 배회 | 42 |
| 전동킥보드 인도 주행 | 40 |
| 특정 구역 내 지속 배회 | 37 |
| 전동킥보드 앞뒤 2인 탑승 | 35 |
| 이륜 이동수단 탑승자 일부 또는 전체 헬멧 미착용 | 34 |
| 이륜 이동수단 운전자 1인 헬멧 미착용 | 34 |
| 경계선을 통한 침입 | 29 |
| 신체적 충돌을 동반한 싸움 | 19 |

주의:

- 완전 균형 표본은 아니다.
- symmetric control은 일부 class가 적다. 특히 `경계선을 통한 침입` symmetric는 1건뿐이다.
- 따라서 symmetric control은 주 결론이 아니라 보조 대조군으로 표현해야 한다.

### materialized frames

- frame root: `Datasets/processed/aihub_multi_angle_cctv/20260708/keyframes/stratum_bbox_asymmetry_400`
- clips with frames: 400
- views with frames: 800
- frames: 2,400
- view당 frames: 정확히 3
- extraction errors: 0
- missing frame paths: 0
- extraction_strategy: `label_evidence_frame` only

이 상태는 answer-level VLM 실험에 사용할 수 있는 물리 데이터셋으로 적합하다.

## Answer-level VLM 결과 무결성

### Qwen2.5-VL-7B

산출물:

- `Datasets/processed/aihub_multi_angle_cctv/20260708/results/multiview_answer_vlm_qwen25vl_400/vlm_answers.parquet`
- `Datasets/processed/aihub_multi_angle_cctv/20260708/results/multiview_answer_vlm_qwen25vl_400/eval/multiview_answer_report.json`

기본 무결성:

- rows: 1,600 = 400 clips x 4 conditions
- condition별 rows: 400
- classes: 11
- valid JSON: 100%
- match: exact 1,600

정확도:

| condition | accuracy |
|---|---:|
| closed_book | 0.1000 |
| worse_view_only | 0.1400 |
| better_view_only | 0.1900 |
| both_view | 0.2000 |

asymmetric stratum 주요 비교:

- better-worse: +0.056, 95% CI [0.020, 0.092], p=0.0016
- both-better: +0.012, TOST equivalent within SESOI 0.05
- verdict: `SELECT_BETTER_VIEW`

### Qwen2-VL-7B

산출물:

- `Datasets/processed/aihub_multi_angle_cctv/20260708/results/multiview_answer_vlm_qwen2vl_400/vlm_answers.parquet`
- `Datasets/processed/aihub_multi_angle_cctv/20260708/results/multiview_answer_vlm_qwen2vl_400/eval/multiview_answer_report.json`

기본 무결성:

- rows: 1,600 = 400 clips x 4 conditions
- condition별 rows: 400
- classes: 11
- valid JSON: 98.44%
- unmatched: 2

정확도:

| condition | accuracy |
|---|---:|
| closed_book | 0.1125 |
| worse_view_only | 0.1925 |
| better_view_only | 0.2825 |
| both_view | 0.3025 |

asymmetric stratum 주요 비교:

- better-worse: +0.152, 95% CI [0.092, 0.212], p=0.0002
- both-better: +0.008, TOST equivalent within SESOI 0.05
- verdict: `SELECT_BETTER_VIEW`

## 현재 결론의 방어 가능성

다음 결론은 방어 가능하다.

> bbox 면적 proxy로 정의한 geometric visibility asymmetry 조건에서, 고정 VLM에 어떤 view evidence를 공급하는지가 답변 정확도를 유의하게 바꾼다. better-view는 worse-view보다 정확도가 높지만, both-view는 better-view 대비 추가 이득이 통계적으로 확인되지 않고 SESOI 0.05 내 등가로 판정된다. 따라서 이 데이터와 모델 조건에서 다각도 CCTV DB의 역할은 view를 많이 쌓는 것이 아니라 더 나은 view를 선택하는 것이다.

반드시 좁혀야 하는 부분:

- “다각도는 일반적으로 무의미하다” 금지
- “두 view에 상보 정보가 없다” 금지
- “대형 VLM 일반 결론” 금지
- “occlusion을 해결했다” 금지
- “Qwen 계열 밖으로 일반화” 금지

## 발견된 문제

### 1. 원고의 모델 사용 범위 모순

원고 4.1절과 기여 항목에는 아직 다음 취지의 문장이 남아 있다.

- “LLM/VLM 생성 모델을 사용하지 않았다.”
- “LLM/VLM generation: 없음”

하지만 원고 6.8절은 Qwen2.5-7B/Llama-3-8B LLM 답변 실험을 사용하고, 6.13절은 Qwen2.5-VL/Qwen2-VL VLM 답변 실험을 사용한다.

수정 필요:

- 4.1 모델 표에 answer generation LLM과 answer-level VLM을 별도 행으로 추가한다.
- 기여 5번은 “생성 모델을 사용하지 않고”가 아니라 “생성 모델을 고정하고 DB evidence 구성만 바꾸는 통제 실험”으로 수정한다.

### 2. “동기 촬영” 표현 위험

원고 3.1절과 6.13절에는 다각도 CCTV를 “동기 촬영된 두 시점”으로 표현한다. 이전 검증에서는 c1/c2 evidence 시각차가 존재하고, 두 view가 같은 순간의 완전 동기 evidence로 보기 어렵다는 지적이 있었다.

수정 필요:

- “동기 촬영된 두 시점” 대신 “동일 사건에 대해 제공되는 두 카메라 시점(c1/c2)”로 표현한다.
- 한계에는 “evidence frame은 완전 시간 동기화된 동일 순간 쌍이 아니다”를 유지한다.

### 3. 초록과 Abstract가 다각도 CCTV 결과를 반영하지 않음

현재 초록/Abstract는 VRU와 AI Hub 지능형 CCTV 중심이며, AI Hub 다각도 CCTV와 `selection > availability` 결론이 들어가 있지 않다.

수정 필요:

- 초록에 한 문장 압축 반영 권장.
- Abstract에도 multi-view answer-level selection 결과를 1문장 반영 권장.

### 4. 재현성 manifest 부족

`run_multiview_answer_vlm.py`는 결과 parquet와 candidates만 저장한다. 다음 정보가 결과 디렉터리에 manifest로 고정되어 있지 않다.

- model path
- resolved snapshot commit
- transformers/torch/qwen_vl_utils version
- decoding parameters
- prompt hash 또는 prompt text
- frame root
- stratum manifest path
- command line

현재 확인한 모델 snapshot:

- Qwen2.5-VL-7B-Instruct: `cc594898137f460bfe9f0759e9844b3ce807cfb5`
- Qwen2-VL-7B-Instruct: `eed13092ef92e448dd6875b2a00151bd3f7db0ac`
- Python: 3.10.20
- PyTorch: 2.12.1+cu130
- Transformers: 5.13.0

수정 필요:

- 두 결과 디렉터리에 `run_manifest.json`을 보강 생성한다.
- 스크립트에도 향후 실행 시 manifest를 자동 저장하도록 수정한다.

### 5. class별 절대 정확도 편차 큼

class별 accuracy를 보면 일부 class는 거의 맞히지 못하고, 일부 class는 closed-book에서도 높다.

예:

- Qwen2.5-VL에서 `전동킥보드 인도 주행`은 closed_book 1.00, both_view 0.98
- Qwen2-VL에서 `비정상적인 경로로의 침범`은 closed_book 1.00, both_view 0.91
- 여러 헬멧/배회 class는 거의 0에 가깝다.

따라서 절대 성능 또는 class-general VLM 성능 주장은 금지한다. paired condition delta와 gate 통과만 주장해야 한다.

## 다음 단계 권고

### 바로 하면 안 되는 것

- InternVL cross-family 복제부터 바로 실행
- 초록에 다각도 결과를 넣기 전에 본문 모델 사용 범위 모순을 방치
- “동기 촬영” 표현 유지
- `모델-강건`을 Qwen 계열 두 모델만으로 과장

### 먼저 해야 할 것

1. 원고 정합성 수정
   - 모델 표와 기여 항목에서 LLM/VLM 사용 범위 수정
   - “동기 촬영” 표현 제거
   - 초록/Abstract에 다각도 결과 1문장 압축 반영

2. 다각도 VLM 결과 manifest 보강
   - Qwen2.5-VL/Qwen2-VL 결과 디렉터리에 `run_manifest.json` 생성
   - `run_multiview_answer_vlm.py`도 향후 manifest를 자동 저장하도록 수정

3. 결과 문장 톤 조정
   - “모델-강건” 대신 “Qwen 계열 2개 VLM에서 반복 관찰”
   - “visibility asymmetry”는 “bbox 면적 기반 geometric visibility proxy”로 한정
   - symmetric control은 보조 근거로만 서술

### 그 다음 선택 작업

1. Cross-family VLM 복제
   - InternVL 등 Qwen 계열이 아닌 VLM으로 재현하면 robustness가 강해진다.
   - 단, 현재 투고 일정이 촉박하면 필수는 아니다.

2. 초록/Contributions 압축 반영
   - 위 정합성 수정 후 진행하는 것이 안전하다.

## 최종 판단

현재 데이터셋 상태는 다각도 answer-level VLM 실험을 지탱할 만큼 정상이다. 하지만 현재 원고는 새 결과를 일부 반영하면서도 과거 “VLM 미사용” 범위 문장이 남아 있어 내부 모순이 있다. 따라서 앞으로의 올바른 순서는 다음이다.

1. 원고/manifest 정합성 보강
2. 초록/기여 반영
3. 필요 시 InternVL cross-family 복제

이 순서를 지키면 추가 작업은 타당하다. 반대로 지금 상태에서 바로 “완성본”으로 제출하거나 추가 실험만 늘리는 것은 위험하다.
