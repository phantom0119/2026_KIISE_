# IntentStore P0-D 다각도 구조 궤적·시각 증거 구제 실험 보고서

> 판정: **RESCUE_INCONCLUSIVE**  
> 운영 결론: **DO_NOT_CONFIRM_TOPIC; RESCUE_GATE_INCONCLUSIVE**  
> 요약: **판정 불충분 — IntentStore 주제 확정 근거를 얻지 못함**

## 1. 무엇을 검증했는가

P0-C에서 caption이 keyframe을 압도한 뒤 허용한 단 한 번의 좁은 구제 실험이다. 11개 안전 사건 399개에서, 한 카메라의 단계별 객체 행동 COT를 BGE-M3 zero-shot으로 분류한 결과와 두 카메라 6장을 입력한 동결 VLM 결과를 같은 clip 단위로 비교했다.

COT는 정답 라벨 JSON에서 사람이 기술한 행동 단계다. 사건명 직접 누설 clip은 제외했지만, 자동 생성된 운영 표현이 아니라 **구조 궤적이 완벽히 추출됐다고 가정한 oracle 상한선**이다.

## 2. 주 결과

| 서비스군 | COT better 정확도 | Qwen2.5 visual both | Qwen2 visual both | Idefics2 visual both | InternVL3 visual both | 구조 지지 수 | 시각 지지 수 |
|---|---:|---:|---:|---:|---:|---:|---:|
| temporal_relation | 0.327 | 0.058 | 0.439 | 0.187 | 0.140 | 0/4 | 0/4 |
| attribute_count | 0.718 | 0.010 | 0.019 | 0.000 | 0.068 | 4/4 | 0/4 |
| path_mode | 0.928 | 0.544 | 0.352 | 0.208 | 0.528 | 3/4 | 0/4 |

주 검정은 `COT better − visual both` 12개 비교다. 5%p 효과, paired sign-flip 20만 회, BH-FDR, clip bootstrap, 사건 class cluster bootstrap, Training/Validation 방향 일치를 모두 만족해야 지지로 인정했다.

| 서비스군 | 모델 | 차이 | 95% CI | class-cluster 95% CI | BH q | 판정 |
|---|---|---:|---:|---:|---:|---|
| temporal_relation | Qwen2.5-VL-7B | 0.269 | [0.193, 0.345] | [0.000, 0.598] | 0.000007 | 없음 |
| temporal_relation | Qwen2-VL-7B | -0.111 | [-0.228, 0.006] | [-0.562, 0.442] | 0.078815 | 없음 |
| temporal_relation | Idefics2-8B | 0.140 | [0.035, 0.246] | [-0.316, 0.653] | 0.015005 | 없음 |
| temporal_relation | InternVL3-8B | 0.187 | [0.105, 0.269] | [-0.220, 0.543] | 0.000030 | 없음 |
| attribute_count | Qwen2.5-VL-7B | 0.709 | [0.621, 0.796] | [0.412, 0.971] | 0.000007 | COT |
| attribute_count | Qwen2-VL-7B | 0.699 | [0.612, 0.786] | [0.412, 0.943] | 0.000007 | COT |
| attribute_count | Idefics2-8B | 0.718 | [0.631, 0.806] | [0.412, 1.000] | 0.000007 | COT |
| attribute_count | InternVL3-8B | 0.650 | [0.553, 0.738] | [0.412, 0.800] | 0.000007 | COT |
| path_mode | Qwen2.5-VL-7B | 0.384 | [0.280, 0.488] | [-0.150, 0.976] | 0.000007 | 없음 |
| path_mode | Qwen2-VL-7B | 0.576 | [0.488, 0.664] | [0.372, 0.881] | 0.000007 | COT |
| path_mode | Idefics2-8B | 0.720 | [0.640, 0.800] | [0.372, 0.976] | 0.000007 | COT |
| path_mode | InternVL3-8B | 0.400 | [0.296, 0.504] | [0.075, 0.976] | 0.000007 | COT |

### 구조 arm 민감도

| 범위 | worse 1-view | better 1-view | both mean | both max |
|---|---:|---:|---:|---:|
| all | 0.612 | 0.617 | 0.619 | 0.624 |
| temporal_relation | 0.310 | 0.327 | 0.316 | 0.316 |
| attribute_count | 0.709 | 0.718 | 0.748 | 0.709 |
| path_mode | 0.944 | 0.928 | 0.928 | 0.976 |

한 시점/두 시점 결합법을 바꿔도 결론은 바뀌지 않았다. 특히 temporal_relation은 모든 구조 arm이 약 0.31~0.33에 머물렀다.

### 사건 class별 구조 분류

| 서비스군 | 사건 class | n | COT better 정확도 |
|---|---|---:|---:|
| attribute_count | 이륜 이동수단 운전자 1인 헬멧 미착용 | 34 | 0.735 |
| attribute_count | 이륜 이동수단 탑승자 일부 또는 전체 헬멧 미착용 | 34 | 0.412 |
| attribute_count | 전동킥보드 앞뒤 2인 탑승 | 35 | 1.000 |
| path_mode | 오토바이 인도 주행 | 43 | 0.977 |
| path_mode | 자전거 인도 주행 | 42 | 0.976 |
| path_mode | 전동킥보드 인도 주행 | 40 | 0.825 |
| temporal_relation | 경계선을 통한 침입 | 29 | 0.276 |
| temporal_relation | 비정상적인 경로로의 침범 | 45 | 0.000 |
| temporal_relation | 신체적 충돌을 동반한 싸움 | 18 | 0.556 |
| temporal_relation | 특정 구역 내 지속 배회 | 37 | 0.000 |
| temporal_relation | 특정 인물을 뒤따라가며 배회 | 42 | 0.905 |

`비정상적인 경로로의 침범`과 `특정 구역 내 지속 배회`는 COT zero-shot 정확도가 0이었다. 이는 단계 서술이 무의미하다는 뜻이 아니라, 현재 query prototype과 label-derived 서술만으로 인접 관계 class를 구분하지 못했다는 뜻이다.

## 3. 다각도 view 보존 보조 결과

보조 판정은 **VIEW_SELECTION_NARROW_PASS**이다. better 한 시점은 both 두 시점 JPEG의 총 50.2% 바이트를 사용했다.

| 모델 | worse | better | both | better−worse | 95% CI | better의 both 대비 비열등 |
|---|---:|---:|---:|---:|---:|---|
| Qwen2.5-VL-7B | 0.133 | 0.189 | 0.197 | 0.056 | [0.020, 0.092] | 예 |
| Qwen2-VL-7B | 0.157 | 0.309 | 0.317 | 0.153 | [0.092, 0.213] | 아니오 |
| Idefics2-8B | 0.096 | 0.141 | 0.124 | 0.044 | [0.004, 0.084] | 예 |
| InternVL3-8B | 0.161 | 0.245 | 0.253 | 0.084 | [0.040, 0.129] | 예 |

이 결과가 통과하더라도 의미는 ‘bbox가 더 잘 보이는 한 시점 3장을 두 시점 6장 대신 보존할 수 있다’는 좁은 선택 규칙이다. 서비스 의도에 따라 서로 다른 표현을 저장해야 한다는 IntentStore 핵심 가설의 증거는 아니다.

## 4. 저장량

| 표현 | clip당 평균 | 중앙값 | 전체 |
|---|---:|---:|---:|
| cot_1view | 4.3 KiB | 4.3 KiB | 1.7 MiB |
| cot_2view | 8.6 KiB | 8.6 KiB | 3.3 MiB |
| visual_1view | 154.6 KiB | 153.7 KiB | 60.2 MiB |
| visual_2view | 307.6 KiB | 303.4 KiB | 119.9 MiB |

COT 비용은 UTF-8 텍스트+BGE-M3 float32 1,024차원만 포함한다. 구조 추출 비용, bbox/label 생성 비용, VLM 추론 비용과 DB overhead는 포함하지 않았다.

## 5. 최종 해석과 연구 주제 판정

구제 통과도 명시적 dominance 실패도 성립하지 않았다. 이 결과로는 IntentStore를 확정할 수 없다. 추가 실험을 하려면 이번 결과를 본 뒤 기준을 완화하지 말고, 새로운 독립 데이터·자동 궤적 추출을 갖춘 별도 사전 등록 연구로 시작해야 한다.

### 제한 사항

- COT는 label-derived oracle이며 실제 배포 가능한 자동 추출기가 아니다.
- VLM 출력은 이전 GPU 실험의 동결 산출물이며 이번 실행에서 GPU를 사용하지 않았다.
- 11-class closed-set 정확도는 open-world 이상 탐지, 실시간 지연 또는 환각 완화 성능이 아니다.
- 단일 AI Hub 계열 399 clips이므로 외부 일반화가 입증되지 않았다.
- view의 better/worse는 정답 bbox 면적으로 정해져 운영 시에는 별도 view-quality estimator가 필요하다.

## 6. 재현성과 정합성

- 분석 표본: 400개 중 직접 사건명 누설 1개 제외, 최종 399개
- 제외 clip: `aihub_multi_angle_cctv:Training:ph_e2067`
- VLM: 4모델×399 clips×4조건 = 6,384행 정합성 확인
- frame: 2,394개 JPEG 존재 및 바이트 실측
- CPU 실행 시간: 7.0초
- Python: 3.10.19, NumPy: 2.2.6, pandas: 2.3.3
- CUDA 작업: 실행하지 않음 (`CUDA_VISIBLE_DEVICES=<unset>`; 스크립트는 GPU 라이브러리/모델을 호출하지 않음)
- seed: 20260806; randomization 200,000; bootstrap 20,000
- 첫 dry run은 표본 밖 행에 빈 gold를 적용한 누설 감사 구현 오류로 결과 계산 전에 중단했다. 400개 등록 표본으로 범위를 제한한 뒤 실행했으며 판정 기준은 변경하지 않았다.

상세 수치는 `results/p0d_*.csv`, 입력 SHA-256은 `results/p0d_source_manifest.json`, 기계 판정은 `results/p0d_decision.json`에 보존했다.
