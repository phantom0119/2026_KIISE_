# IntentStore P0-D: 다각도 구조 궤적·시각 증거 구제 게이트

> 등록일: 2026-08-06  
> 등록 상태: **새 COT 분류와 구조-vs-시각 교차 결과 계산 전 고정**  
> 실행 상태: **2026-08-06 완료 — `RESCUE_INCONCLUSIVE`, `VIEW_SELECTION_NARROW_PASS`**  
> 결과: [P0_D_MULTIVIEW_RESCUE_REPORT.md](P0_D_MULTIVIEW_RESCUE_REPORT.md)  
> 분석 성격: P0-C의 `STOP_CURRENT_SCOPE` 뒤 허용한 `ONE_NARROW_RESCUE_GATE`

## 1. 질문

P0-C에서는 회고적 사건 검색에서 caption이 CLIP keyframe보다 품질·저장량 모두 우세했다. P0-D는 caption이 직접 보존하지 않는 **단계별 객체 행동과 시점별 가시성**으로 범위를 좁힌다.

> 서로 다른 안전 서비스 계열이 label-derived 구조 궤적 텍스트와 다각도 시각 frame 가운데 서로 다른 증거 보존 arm을 필요로 하는가?

이 조건이 성립하지 않으면 범용 IntentStore를 구제하지 않는다. 단일한 구조 표현 또는 단일한 시점 선택 규칙만 우세하면 그 좁은 측정/저장 주제로만 전환할 수 있다.

## 2. 입력과 독립성

- AI Hub 다각도 CCTV 생활안전 사건 400 clips
- 사건 class 11개, 카메라 `c1/c2`, view당 label-evidence frame 3장
- bbox 평균 면적 비율로 만든 `asymmetric` 250 clips와 `symmetric` 150 clips
- source split: Training 223, Validation 177
- 동결 VLM 출력 4종:
  - Qwen2.5-VL-7B
  - Qwen2-VL-7B
  - Idefics2-8B
  - InternVL3-8B
- 시각 조건: no image, worse view 3 frames, better view 3 frames, both views 6 frames
- 구조 조건: canonical의 `cot_c1/c2`, 즉 객체 행동을 1·2·3단계로 기술한 label-derived 텍스트
- BGE-M3의 기존 normalized document/query embedding

기존 VLM별 조건 평균은 과거 실험에 존재하고 이번 자산 감사 중 확인했다. 따라서 VLM view 비교는 완전 맹검 confirmatory 실험이 아니라 **동결 출력 재감사**다. 새 결과는 COT zero-shot 분류, 같은 clip에서의 구조-vs-시각 비교, 서비스군별 비지배성 게이트다.

## 3. 누설 통제

`cot_c1/c2`는 원본 label JSON에서 만들어진 구조 oracle이며 운영 시스템이 자동 생성한 trajectory가 아니다. 이 한계를 결과 전체에 표시한다.

- COT 문자열에 gold event class 전체 문구가 그대로 들어간 clip은 주 평가에서 제외한다.
- 결과 계산 전 literal audit에서 400 clips 중 1개(`Training:ph_e2067`, COT 2개)가 확인되어 주 표본은 399 clips다.
- `answer`, `caption_c1/c2`, `event_statement`는 event class를 직접 쓰므로 사용 금지다.
- `evidence_c1/c2`도 정답 frame 범위를 직접 기술하므로 분류 arm에서 사용하지 않는다.

구조 COT는 class명을 직접 포함하지 않더라도 gold annotation에서 파생됐다. 따라서 이를 deployable 성능이 아니라 **구조 궤적 보존의 상한 proxy**로 해석한다.

## 4. 서비스군

### `temporal_relation`

- 비정상적인 경로로의 침범
- 경계선을 통한 침입
- 신체적 충돌을 동반한 싸움
- 특정 구역 내 지속 배회
- 특정 인물을 뒤따라가며 배회

### `attribute_count`

- 이륜 이동수단 운전자 1인 헬멧 미착용
- 이륜 이동수단 탑승자 일부 또는 전체 헬멧 미착용
- 전동킥보드 앞뒤 2인 탑승

### `path_mode`

- 오토바이 인도 주행
- 자전거 인도 주행
- 전동킥보드 인도 주행

각 clip은 정확히 한 서비스군에 속한다.

## 5. 표현 arm

### 구조 궤적 arm

- `cot_worse`: bbox가 작은 view의 COT BGE vector
- `cot_better`: bbox가 큰 view의 COT BGE vector
- `cot_both_mean`: 두 normalized COT vector 평균 후 재정규화
- `cot_both_max`: class별 두 view cosine의 max. 사전 고정 민감도 arm

분류는 11개 `weak_event` query embedding과의 cosine이 가장 큰 class를 선택한다. 학습·튜닝하지 않는다.

### 시각 arm

각 VLM의 동결 `worse_view_only`, `better_view_only`, `both_view` 예측을 그대로 사용한다. invalid/unmatched 출력은 오답이다.

## 6. 주 비교

각 서비스군×VLM 4개, 총 12개에서 다음 paired difference를 검사한다.

> `cot_better accuracy - visual_both accuracy`

시각 쪽에 유리하도록 6개 frame의 richest visual condition을 사용하고, 구조 쪽은 한 view만 사용한다.

- 최소 실질 차이: accuracy 5%p
- paired sign-flip 200,000회, 양측
- 12개 전체 BH-FDR
- clip bootstrap 20,000회 95% CI
- event class cluster bootstrap 20,000회 95% CI
- Training과 Validation split의 평균차가 같은 방향이어야 support 인정
- seed: 20260806

`cot_both_mean/max`와 visual better는 보조 민감도이며 주 12개 검정을 바꾸지 않는다.

## 7. view-retention 보조 게이트

asymmetric clips에서 각 VLM의 다음을 검사한다.

1. `better - worse >= 0.05`, BH-FDR 4개, CI 하한>0
2. `better - both`의 95% CI 하한이 −0.05보다 크면 both 대비 noninferior
3. better view는 JPEG frame 수가 both의 절반이어야 함

3/4 이상 VLM에서 2와 3을 만족하면 `VIEW_SELECTION_NARROW_PASS`다. 이것은 “좋은 한 시점을 보존하라”는 좁은 결과이며 서비스 의도 기반 IntentStore 구제와 동일하지 않다.

## 8. 구제 판정

- `RESCUE_PASS_SERVICE_NONDOMINANCE`: 같은 VLM에서 한 서비스군은 COT가 +5%p 이상 지지되고 다른 서비스군은 rich visual이 +5%p 이상 지지됨
- `RESCUE_FAIL_STRUCTURED_DOMINANCE`: 세 서비스군 각각에서 4개 VLM 중 최소 3개가 COT 우세를 지지하고 visual 우세 셀이 0개
- `RESCUE_FAIL_VISUAL_DOMINANCE`: 위의 반대
- `RESCUE_INCONCLUSIVE`: 어느 조건도 충족하지 않음

`RESCUE_PASS`여도 label-derived COT를 자동 trajectory로 대체하고 독립 공개 데이터에서 재현하기 전에는 EDBT급 주제 확정이 아니다. `RESCUE_FAIL_*`이면 합의한 한 번의 구제 기회를 소진한 것으로 보고 **범용 IntentStore를 종료**한다.

## 9. 저장비 proxy

- COT 1-view: UTF-8 COT + BGE float32 1,024차원 vector
- COT 2-view: 두 COT 문자열 + vector 2개
- visual 1-view: JPEG 3장
- visual 2-view: JPEG 6장

기존 artifact byte를 합산한다. COT/box/label 생성 비용, VLM GPU 비용, DB overhead는 별도이며 현재 비교에 포함하지 않는다.

## 10. 금지 해석

- COT 결과를 자동 trajectory extractor 성능으로 부르지 않는다.
- 다각도 frame 6장을 원본 video 또는 시간 순서 video encoder로 부르지 않는다.
- closed-set 11-class accuracy를 이상 탐지·환각 완화·실시간 SLA로 바꾸지 않는다.
- 같은 AI Hub 계열의 400 clips를 독립 공개 데이터 재현으로 부르지 않는다.
- 기존 VLM 결과를 신규 GPU 실험처럼 보고하지 않는다.

## 11. 산출물

- `scripts/analyze_p0d_multiview_rescue.py`
- `results/p0d_source_manifest.json`
- `results/p0d_per_clip.csv`
- `results/p0d_service_accuracy.csv`
- `results/p0d_primary_tests.csv`
- `results/p0d_view_tests.csv`
- `results/p0d_storage_summary.csv`
- `results/p0d_decision.json`
- `P0_D_MULTIVIEW_RESCUE_REPORT.md`
