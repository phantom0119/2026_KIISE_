# IntentStore P0-CPU 통합 실험 기록

> 실행일: 2026-08-06  
> 상태: **P0-D 단일 구제 게이트 완료 — `RESCUE_INCONCLUSIVE`, 범용 IntentStore 주제 확정 금지**  
> 목적: IntentStore 전체를 구현하기 전에 “서비스에 따라 유리한 증거 표현이 달라진다”는 G1 전제를 기존 동결 산출물로 검증한다.

## 1. 한 문장 결론

1차 proxy 분석은 불확정이었고, VRU·AI Hub 103개 실제 안전 질의에서는 **caption stack이 네 서비스군 모두에서 최선 단일 arm이면서 frame arm보다 작아** P0-C가 중단됐다. 이후 허용한 단 한 번의 P0-D 구제 게이트에서 label-derived 구조 궤적 oracle과 다각도 VLM을 399 clips·11 사건에서 비교했지만, 서비스별 표현 비지배성은 확인되지 않았다. 구조 oracle은 `attribute_count` 4/4, `path_mode` 3/4 모델보다 지지됐으나 `temporal_relation`은 0/4였고 시각 증거 우세도 0/12였다. 따라서 결과는 `RESCUE_INCONCLUSIVE`이며, **범용 IntentStore는 연구 주제로 확정하지 않고 GPU 본실험도 시작하지 않는다.** 다만 bbox가 큰 한 시점 3장은 두 시점 6장 대비 3/4 VLM에서 비열등하고 저장량이 50.2%여서 좁은 view-selection 결과는 남았다.

## 2. GPU 비사용 원칙

- 기존 GPU 작업을 중단하거나 변경하지 않았다.
- 신규 모델 추론, 임베딩 생성, 캡션 생성, 프레임 디코딩을 수행하지 않았다.
- 분석 스크립트는 동결된 Parquet/CSV를 pandas·NumPy로 읽고 bootstrap/randomization만 수행한다.
- 522 분석: 0.89초, 최대 RSS 약 129MiB.
- 522 다중성 감사: 1.39초, 최대 RSS 약 128MiB.
- MEVA 복제: 1.14초, 최대 RSS 약 130MiB.

## 3. 실험 A: 522 교통 CCTV 서비스별 표현 분석

### 3.1 사전 고정

[P0_CPU_PROTOCOL.md](P0_CPU_PROTOCOL.md)에 다음을 결과 집계 전에 고정했다.

- 3,000 clips, 85 queries
- 동일 Qwen3-VL-Embedding-2B 2,048차원 공간
- 검색 계획 `B2_vector`, 색인 `flat`
- 주 평가 `strict` nDCG@10
- 표현: caption, representative frame, joint image-caption, multi-frame, dual
- 서비스 proxy: buses, crowded scene, parked vehicle, stopped vehicle, two wheeler
- paired bootstrap 10,000회, seed 20260806

### 3.2 입력 고정성

| 입력 | SHA-256 |
|---|---|
| `per_query_metrics.parquet` | `d107585657c656efceb6bc4a99befb4b0b083c3170c24d6544b60c972bcd1321` |
| `query_clusters.csv` | `3c527793be216eca9c586138af6b12c917e7f21dc61a2cb71504b95d12ca034b` |
| `configuration_summary.csv` | `fcd4c61f781e3c548ed744d82deec900416b49811746dee703d224656aaeb4c8` |

총 850개 통제 행(85질의×5표현×2평가)을 사용했다.

### 3.3 최초 자동 결과

[G1_CPU_REPORT.md](G1_CPU_REPORT.md)의 최초 판정은 `CONTINUE_STRONG`이었다. 표현쌍의 순위가 서비스에 따라 반대로 바뀐 후보가 5개 발견됐다.

| 표현쌍 | A 우세 서비스 | A−B | B 우세 서비스 | A−B |
|---|---|---:|---|---:|
| caption−dual | crowded_scene | +0.0887 | stopped_vehicle | −0.1169 |
| caption−dual | crowded_scene | +0.0887 | two_wheeler | −0.0585 |
| caption−representative_frame | crowded_scene | +0.1170 | stopped_vehicle | −0.0551 |
| joint_image_caption−multi_frame | crowded_scene | +0.1007 | stopped_vehicle | −0.1147 |
| joint_image_caption−multi_frame | crowded_scene | +0.1007 | two_wheeler | −0.0624 |

그러나 서비스별 승자와 차순위의 차이는 어느 서비스에서도 사전 지지 기준을 통과하지 못했다. 즉 “순위 뒤집힘 후보”는 있었지만 “각 서비스 최적 표현 확정”은 아니었다.

### 3.4 발견한 통계 결함과 보정

최초 strong reversal 탐색은 5서비스×10표현쌍=50개 비교를 수행하면서 개별 bootstrap CI만 사용했다. 이 다중성 문제를 결과 확인 뒤 발견했으며, 이를 사전 분석처럼 포장하지 않고 [MULTIPLICITY_AUDIT.md](MULTIPLICITY_AUDIT.md)에 사후 감사로 기록했다.

- 비교당 paired sign-flip randomization 200,000회
- 50개 전체 BH-FDR 보정
- q<0.05 비교: 1개
- FDR을 통과한 반대 방향 reversal: 0개
- 보정 판정: **`FDR_INCONCLUSIVE`**

유일하게 FDR을 통과한 비교는 다음과 같다.

| 서비스 | 비교 | nDCG@10 차이 | p | q(BH) |
|---|---|---:|---:|---:|
| stopped_vehicle | multi_frame−caption | +0.1658 | 0.000890 | 0.04450 |

이는 시간·다중 시점 정보가 필요한 정지 차량 검색에서 단일 caption이 충분하지 않을 수 있다는 유효한 신호다. 그러나 혼잡 장면에서 caption이 우세하다는 반대편 결과가 FDR을 통과하지 않아, G1의 서비스별 비지배성을 확정하지는 못했다.

## 4. 실험 B: 독립 MEVA 복제

### 4.1 사전 고정

[P0_CPU_MEVA_REPLICATION_PROTOCOL.md](P0_CPU_MEVA_REPLICATION_PROTOCOL.md)에 MEVA 서비스군 매핑과 15개 비교의 BH-FDR을 결과 집계 전에 고정했다.

- 985 clips, 193 queries, 57 intent×facet clusters
- 표현: caption, representative frame, dual
- 검색 계획 `B2_vector`, 주 평가 `strict` nDCG@10
- 서비스군: vehicle contact, object interaction, body/social, vehicle maneuver, facility access
- 15개 paired randomization test에 BH-FDR 적용
- 주의: MEVA 산출물은 클립당 대표 프레임 한 장뿐이므로 multi-frame 복제가 아니다.

### 4.2 최초 복제 결과

[MEVA_REPLICATION_REPORT.md](MEVA_REPLICATION_REPORT.md)의 자동 결과는 `REPLICATED_SUPPORTED`였다.

- 전체 승자 종류: caption, frame, dual
- 품질 기준을 통과한 winner: 없음
- 비용 비열등 경로로 지지된 winner: body_social의 frame, facility_access의 caption
- FDR 확인 strong reversal: 없음
- FDR을 통과한 표현 차이: vehicle_contact에서 dual−caption +0.0316, q=0.0123

vehicle_contact의 차이는 통계적으로는 확인됐지만 사전 최소 실질 차이 0.05에는 미달했다.

### 4.3 정보성 결함과 보정

`facility_access`는 caption, frame, dual이 모두 strict nDCG@10=0이었다. 원 규칙은 caption이 dual의 절반 저장량이라는 이유만으로 이를 비용 효율 승자로 인정했다. 아무 질의도 해결하지 못한 동률은 유용한 비열등성이 아니므로 [MEVA_INFORMATIVE_AUDIT.md](MEVA_INFORMATIVE_AUDIT.md)에 다음 사후 유효성 검사를 추가했다.

- 서비스군 n≥10
- 승자 평균 strict nDCG@10≥0.05

보정 뒤에는 body_social의 frame 하나만 지지되어 서로 다른 승자가 두 개라는 조건을 충족하지 못했다.

- 보정 판정: **`REPLICATION_INCONCLUSIVE`**
- 남은 신호: body_social에서 frame은 dual의 절반 index 크기이며 품질차 CI가 비열등 한계 −0.02 안에 있음(차이 +0.0068, 95% CI [−0.0181, +0.0336])

## 5. 1차 proxy 종합 판정(당시 중간 상태)

| 질문 | 판정 | 근거 |
|---|---|---|
| 표현에 따라 품질이 달라지는가? | 예 | 522 stopped_vehicle의 multi-frame−caption 차이가 BH-FDR 통과 |
| 서비스별 최적 표현이 확실히 다른가? | 아직 불명 | 522 reversal은 FDR 미통과, MEVA는 두 개의 정보성 지지 winner를 확보하지 못함 |
| 싼 단일 표현이 일부 서비스에서 충분한가? | 제한적 예 | MEVA body_social에서 frame이 dual 대비 비용 비열등 경로 통과 |
| IntentStore G1을 최종 통과했는가? | 아니오 | 위험 서비스, 궤적, 원본 TTL, 사건 F1을 아직 평가하지 않음 |
| 지금 연구를 중단해야 하는가? | 아니오 | 적어도 한 서비스에서 표현 선택의 큰 효과가 확인됨 |
| 지금 GPU 본실험으로 넘어가야 하는가? | 아니오 | 비지배성의 독립 확인이 부족함 |

**당시 중간 상태: `INCONCLUSIVE — CONTINUE CPU ONLY`.** 이 상태는 아래 P0-C 실제 안전 서비스 결과로 대체됐다.

## 6. 현재 결과가 말해 주는 설계 수정

1. 서비스별 표현 선택의 가능성은 있으나 모든 서비스에 복잡한 표현을 유지해야 한다는 증거는 없다.
2. `multi_frame`의 가치가 stopped vehicle처럼 시간·다중 시점 정보가 필요한 서비스에 집중되는지 검증해야 한다.
3. 캡션과 대표 프레임의 차이는 서비스에 따라 작을 수 있으므로 원본 TTL과 재해석 가능성을 별도 효용으로 측정해야 한다.
4. 표현쌍 전수 탐색을 주 검정으로 사용하면 다중성 부담이 크다. 다음 실험은 서비스 메커니즘에 따른 소수의 사전 대비를 사용해야 한다.
5. “검색 nDCG 차이”를 “위험 미탐 감소”로 해석해서는 안 된다.

## 7. 다음 CPU-only 게이트

GPU를 기다리는 동안 다음 순서로 진행한다.

### C1. 실제 안전 서비스 매트릭스 작성

기존 VRU/AI Hub의 qrels·메타데이터·원본 파일명을 이용해 최소 세 서비스 계열을 고정한다.

- 정적 장면 의미: 혼잡, 특정 객체/상태
- 시간 변화 사건: 정지, 접근, 충돌·낙상 전후
- 구조 조건 사건: 시간대·장소·객체 조건

각 서비스의 사건 단위, 허용 증거, 미탐/오탐 비용 범위를 MD와 JSON으로 고정한다.

### C2. 표현 가용성·정보 손실 표

새 모델 생성 없이 이미 있는 원본/키프레임/캡션/임베딩/qrels를 공통 `Evidence` manifest로 연결한다. 현재 파일명 정찰에서는 완성된 궤적 산출물을 확인하지 못했으므로, 궤적 arm은 기존 메타데이터로 대체 가능한지 먼저 판단한다.

### C3. 소수 사전 대비

다음 대비를 독립 데이터에서 사전 고정한다.

- 시간 사건: multi-frame vs caption
- 장면 의미: caption vs representative frame
- 결합 사건: dual vs 단일 표현

각 대비는 사건/질의 단위 paired 분석과 BH-FDR을 처음부터 포함한다.

### C4. GPU 사용 승인 조건

다음 중 하나가 CPU 자료에서 확인될 때만 누락 표현 생성에 GPU를 사용한다.

- 서로 다른 두 안전 서비스에서 서로 다른 표현이 실질 우세
- 동일 품질에서 표현 저장비가 2배 이상 차이
- 원본 만료 뒤 새 서비스 지원률이 표현에 따라 실질적으로 달라짐

## 8. 재현 명령

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/experiments_expansion/intentstore_p0_cpu
python scripts/analyze_g1_service_representation.py
python scripts/audit_g1_multiplicity.py
python scripts/analyze_meva_replication.py
python scripts/audit_meva_informative_floor.py
```

## 9. 산출물 색인

- 최초 규칙: [P0_CPU_PROTOCOL.md](P0_CPU_PROTOCOL.md)
- 522 최초 보고서: [G1_CPU_REPORT.md](G1_CPU_REPORT.md)
- 522 다중성 감사: [MULTIPLICITY_AUDIT.md](MULTIPLICITY_AUDIT.md)
- MEVA 복제 규칙: [P0_CPU_MEVA_REPLICATION_PROTOCOL.md](P0_CPU_MEVA_REPLICATION_PROTOCOL.md)
- MEVA 최초 보고서: [MEVA_REPLICATION_REPORT.md](MEVA_REPLICATION_REPORT.md)
- MEVA 정보성 감사: [MEVA_INFORMATIVE_AUDIT.md](MEVA_INFORMATIVE_AUDIT.md)
- 기계 판정과 표: [`results/`](results/)
- 재현 스크립트: [`scripts/`](scripts/)

## 10. P0-C: 실제 안전 서비스 표현 검증

### 10.1 사전 고정과 입력

[P0_CPU_SAFETY_PROTOCOL.md](P0_CPU_SAFETY_PROTOCOL.md)에 새 교차 표현 결과를 만들기 전에 다음을 고정했다.

- VRU-Accident: 1,000 clips, 비순환 안전 query contracts 85개
- AI Hub 지능형 CCTV: 269 clips, 비순환 안전 query contracts 18개
- strict qrels, nDCG@10, 최소 실질 효과 0.05
- arm: caption, 중앙 frame 1장, CLIP 4-frame max, caption+4-frame RRF
- 주 대비 4개만 사용하고 200,000회 paired sign-flip의 p-value를 BH-FDR 보정
- query bootstrap과 `(dataset,event_type)` cluster bootstrap 각 20,000회
- 실제 사건군: dynamic event, scene state
- 서비스 계약군: open event, context-filtered event

새로 생성한 것은 103개 CLIP text-query embedding뿐이며, `CUDA_VISIBLE_DEVICES=''`, offline/local-only, 명시적 `device=cpu`로 실행했다. 영상 decoding, image embedding 생성, GPU 모델 호출은 없었다.

### 10.2 입력 정합성

[P0_CPU_SAFETY_ALIGNMENT_AUDIT.md](P0_CPU_SAFETY_ALIGNMENT_AUDIT.md)의 판정은 `ALIGNMENT_PASS`다.

- qrels target이 corpus 밖에 있는 경우: 0
- frame 없는 clip: 0
- clip당 frame: 두 데이터 모두 정확히 4개
- 필요한 B2/B4 caption ranking 누락: 0
- VRU에서 과거와 문구가 완전히 같은 query 15개의 새 CPU/기존 GPU CLIP embedding cosine 최솟값: 0.99999988
- frame·query vector norm: 모두 1±약 2×10⁻⁷

따라서 caption 우세가 query 순서, normalization, frame coverage 누락에 의해 만들어졌다는 신호는 없다.

## 11. P0-C 주 결과

### 11.1 서비스군별 평균

| 서비스군 | n | event clusters | caption | center frame | visual 4-frame | fusion | 최선 단일 arm |
|---|---:|---:|---:|---:|---:|---:|---|
| dynamic event | 93 | 18 | **0.3558** | 0.1471 | 0.1565 | 0.2995 | caption |
| scene state | 10 | 3 | **0.8994** | 0.7525 | 0.7090 | 0.8754 | caption |
| context filtered | 82 | 20 | **0.4027** | 0.2094 | 0.2165 | 0.3591 | caption |
| open event | 21 | 21 | **0.4315** | 0.1922 | 0.1852 | 0.3409 | caption |

표의 값은 strict nDCG@10이다. caption의 차순위 단일 arm 대비 마진은 서비스군별 0.1469~0.2393이었다.

### 11.2 사전 주 검정

| ID | 대비 | 평균차 | query CI | cluster CI | q(BH) | 해석 |
|---|---|---:|---|---|---:|---|
| H1 | dynamic: 4-frame−caption | −0.1993 | [−0.2576, −0.1441] | [−0.3603, −0.1060] | 0.000020 | 설계 기대와 반대; caption 우세 |
| H2 | scene: caption−4-frame | +0.1904 | [+0.0600, +0.3363] | [+0.1029, +0.3492] | 0.041760 | caption 우세 지지 |
| H3 | filtered: fusion−caption | −0.0436 | [−0.0801, −0.0083] | [−0.1069, −0.0012] | 0.040900 | fusion 열세; 0.05 실질 기준에는 소폭 미달 |
| H4 | 전체: 4-frame−center | +0.0042 | [−0.0129, +0.0216] | [−0.0162, +0.0282] | 0.634937 | 4장 coverage 이득 없음 |

dynamic 사건에서 visual 4-frame이 유리할 것이라는 핵심 기대가 단순히 미확정된 것이 아니라 **반대 방향으로 기각**됐다. 4-frame max는 순서형 temporal model이 아니므로 “시간 정보는 무가치하다”가 아니라 “현재 CLIP keyframe stack은 caption을 대체하거나 보완하지 못한다”가 정확한 결론이다.

## 12. 가중 fusion 강건성

1:1 RRF만 잘못 고른 가능성을 배제하기 위해 결과 확인 뒤 [P0_CPU_FUSION_SENSITIVITY_PROTOCOL.md](P0_CPU_FUSION_SENSITIVITY_PROTOCOL.md)를 먼저 고정하고 text:visual을 8:1, 4:1, 2:1, 1:1, 1:2, 1:4로 바꿨다. 24개 서비스군×가중치 검정을 함께 BH-FDR 보정했다.

[P0_CPU_FUSION_SENSITIVITY_REPORT.md](P0_CPU_FUSION_SENSITIVITY_REPORT.md)의 결과는 `NO_ROBUST_FUSION_GAIN`이다.

| 서비스군 | 가장 높은 고정 가중치 | caption 대비 최대 평균차 |
|---|---|---:|
| dynamic event | text:visual 8:1 | −0.0137 |
| scene state | text:visual 8:1 | −0.0073 |
| context filtered | text:visual 8:1 | −0.0144 |
| open event | text:visual 8:1 | −0.0079 |

어떤 가중치도 caption 대비 +0.02의 보완 이득을 만들지 못했다.

## 13. 실제 파일 저장량 감사

[P0_CPU_SAFETY_STORAGE_AUDIT.md](P0_CPU_SAFETY_STORAGE_AUDIT.md)는 모든 raw video·JPEG·caption 파일을 stat하여 `STORAGE_AUDIT_PASS`를 기록했다. 다음 값은 기존 artifact byte이며 생성 GPU 비용과 DB 오버헤드는 제외한다.

| 데이터 | raw video | caption stack | center-frame stack | 4-frame stack | fusion stack |
|---|---:|---:|---:|---:|---:|
| VRU 1,000 clips | 2.9822 GiB | **0.0047 GiB** | 0.0307 GiB | 0.1240 GiB | 0.1287 GiB |
| AI Hub 269 clips | 12.9725 GiB | **0.0011 GiB** | 0.0128 GiB | 0.0494 GiB | 0.0504 GiB |

caption stack은 raw보다 VRU 637.5배, AI Hub 12,246.6배 작았다. JPEG까지 포함하면 caption은 center-frame보다도 작으면서 네 서비스군의 검색 품질이 모두 높았다. 즉 현재 arm에서는 caption이 품질만 높은 것이 아니라 저장량까지 실질적으로 지배한다.

이 결과는 caption 생성 비용과 caption에 적히지 않은 미래 정보 손실을 측정하지 않았으므로 “raw를 모두 삭제하라”는 운영 결론은 아니다. 하지만 현재 qrels로 IntentStore의 복잡한 선택 제어기를 정당화할 수 없다는 결론은 강화한다.

## 14. 자동 판정 결함과 수정

최초 실행 코드는 H2의 유의한 caption 우세를 보고 `CONTINUE`를 먼저 반환했다. 동시에 “같은 단일 arm이 모든 군에서 0.05 이상 우세하고 fusion 이득이 없음”이라는 더 구체적인 `STOP_SIGNAL`도 충족했지만, 조건문 순서 때문에 도달하지 못했다.

이를 결과에 맞춘 임계값 변경으로 숨기지 않고 P0-C protocol §11에 사후 구현 감사로 기록했다. 판정 우선순위를 `PROVISIONAL_PASS > STOP_SIGNAL > CONTINUE > INCONCLUSIVE`로 바로잡고 재실행했으며 통계량은 변하지 않았다.

**수정 자동 판정: `SAFETY_G1_STOP_SIGNAL`.**

## 15. 연구 주제 수렴 판정

### 15.1 지금 확정해도 되는가

**아니다. 현재 범위의 범용 IntentStore를 연구 주제로 확정하지 않는다.**

사전 G1은 서로 다른 안전 서비스가 서로 다른 최적 표현을 요구해야 한다고 규정했다. 실제 안전 데이터 두 종에서 그 조건이 성립하지 않았고, caption이 품질·저장량 모두 우세했다. 이 상태로 online controller를 구현하면 “왜 caption-only가 아닌가”에 답할 수 없으며 EDBT급 시스템 기여를 방어하기 어렵다.

### 15.2 무엇을 중단하는가

- 현재 caption/CLIP keyframe/fusion arm만으로 범용 표현 선택을 주장하는 설계
- P1~P3 전체 구현과 GPU 신규 생성
- “서비스마다 최적 표현이 다르다”는 현재 증거 기반의 주장
- 현 결과를 위험 감지 F1·환각 감소·미래 서비스 지원으로 확대하는 해석

### 15.3 무엇이 아직 기각되지 않았는가

- 순서를 학습한 temporal video representation
- detector trajectory와 객체 관계
- 사건 graph와 provenance
- caption 작성 시 예상하지 못한 새 질의에서의 raw 재해석 가치
- 실제 사건 F1, 위험가중 손실, p95 deadline을 포함한 online retention

현재 P0-C는 이들을 시험하지 않았다. 또한 522의 `stopped_vehicle`에서 Qwen multi-frame−caption +0.1658(q=0.0445) 신호가 하나 남아 있다. 따라서 **전체 아이디어를 즉시 폐기하는 대신 좁은 temporal/novel-service 구제 게이트 한 번만 허용**한다.

### 15.4 다음 단 하나의 구제 게이트

새 주장은 다음처럼 좁혀야 한다.

> caption이 잘 처리하는 회고적 사건 검색이 아니라, caption에 기록되지 않은 시간 순서·궤적·관계 또는 사후 추가된 서비스에서만 선택적 원본/temporal 증거 보존이 필요한가?

GPU 사용 전에 CPU로 다음을 완성한다.

1. 최소 두 서비스: `temporal-critical`과 `scene/caption-sufficient`
2. caption 작성 시 사용하지 않은 독립 qrels 또는 사람이 확정한 사건/관계 정답
3. raw TTL 전후에 동일 질의를 평가할 replay trace
4. caption, raw/on-demand, temporal/trajectory, static-all의 비용·품질 정의
5. 조기 중단: temporal/trajectory arm이 caption보다 사건 F1 5%p 또는 위험손실 10% 개선하지 못하면 IntentStore 전체 종료

이 query/qrels를 CPU에서 객관적으로 구성할 수 없거나, 기존 자산에 순서형/trajectory 결과가 없어서 새 GPU 생성만으로 가설을 찾아야 한다면 구제 실험도 시작하지 않는다.

**운영 상태: `STOP_CURRENT_SCOPE — ONE_NARROW_RESCUE_GATE_ALLOWED`.**

## 16. 갱신된 재현 명령

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/experiments_expansion/intentstore_p0_cpu
CUDA_VISIBLE_DEVICES='' HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python scripts/analyze_safety_representation.py
python scripts/audit_safety_input_alignment.py
python scripts/audit_safety_fusion_robustness.py
python scripts/audit_safety_storage_costs.py
```

추가 산출물:

- 실제 안전 규칙: [P0_CPU_SAFETY_PROTOCOL.md](P0_CPU_SAFETY_PROTOCOL.md)
- 주 결과: [P0_CPU_SAFETY_REPORT.md](P0_CPU_SAFETY_REPORT.md)
- 정합성: [P0_CPU_SAFETY_ALIGNMENT_AUDIT.md](P0_CPU_SAFETY_ALIGNMENT_AUDIT.md)
- fusion 규칙/결과: [P0_CPU_FUSION_SENSITIVITY_PROTOCOL.md](P0_CPU_FUSION_SENSITIVITY_PROTOCOL.md), [P0_CPU_FUSION_SENSITIVITY_REPORT.md](P0_CPU_FUSION_SENSITIVITY_REPORT.md)
- 실제 저장량: [P0_CPU_SAFETY_STORAGE_AUDIT.md](P0_CPU_SAFETY_STORAGE_AUDIT.md)
- 기계 판정: [`results/safety_decision.json`](results/safety_decision.json)

## 17. P0-D: 다각도 구조 궤적·시각 증거 구제 게이트

### 17.1 사전 고정

[P0_D_MULTIVIEW_RESCUE_PROTOCOL.md](P0_D_MULTIVIEW_RESCUE_PROTOCOL.md)를 새 COT zero-shot 분류와 구조-vs-시각 대비 계산 전에 고정했다.

- AI Hub 다각도 CCTV 안전 사건 400 clips, 11 사건 class, 두 카메라와 view당 3개 label-evidence frame
- 사건명이 COT에 그대로 들어간 1개 clip을 제외한 주 표본 399개
- 구조 arm: label JSON에서 파생된 3단계 행동 `cot_c1/c2`의 기존 BGE-M3 vector
- 시각 arm: Qwen2.5-VL, Qwen2-VL, Idefics2, InternVL3의 과거 동결 출력
- 주 대비: 서비스군×4 VLM의 `cot_better − visual_both` 12개
- 5%p 최소 효과, paired sign-flip 200,000회, BH-FDR, clip 및 사건 class cluster bootstrap 각 20,000회, Training/Validation 방향 일치
- 통과 조건: 같은 VLM에서 한 서비스군은 구조 표현, 다른 서비스군은 rich visual 표현의 우세가 각각 지지되는 비지배성

COT는 자동 trajectory extractor가 아니다. 정답 label JSON에서 사람이 기술한 행동 단계를 가져온 **oracle 상한선**이며, 이 제한을 protocol과 결과에 모두 고정했다.

### 17.2 입력 정합성 및 누설 통제

- 400 clips 중 exact gold 사건명 문자열이 COT에 들어간 `aihub_multi_angle_cctv:Training:ph_e2067` 1개 제외
- 399 clips에서 COT c1/c2와 1,024차원 normalized BGE-M3 vector가 모두 존재
- 11개 `weak_event` query prototype과 COT vector norm이 1±0.001 범위
- 4모델×399 clips×4조건 = 6,384 VLM 행의 condition, gold label, 저장된 `correct` 값을 재계산해 일치 확인
- 399×6 = 2,394 JPEG 파일 존재와 실제 byte 확인
- 신규 GPU 추론, 영상 decoding, 임베딩 생성 없음

첫 dry run은 400개 표본 밖 COT 행에 빈 gold 문자열을 적용한 누설 감사 구현 오류로 결과 계산 전에 중단됐다. 표본 범위를 먼저 제한하도록 수정했으며, 판정 기준·표현 arm·표본 제외 규칙은 바꾸지 않았다.

## 18. P0-D 결과

### 18.1 서비스별 주 결과

| 서비스군 | n | COT better | Qwen2.5 visual both | Qwen2 visual both | Idefics2 visual both | InternVL3 visual both | 구조 지지 | 시각 지지 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| temporal relation | 171 | 0.327 | 0.058 | 0.439 | 0.187 | 0.140 | 0/4 | 0/4 |
| attribute/count | 103 | 0.718 | 0.010 | 0.019 | 0.000 | 0.068 | 4/4 | 0/4 |
| path/mode | 125 | 0.928 | 0.544 | 0.352 | 0.208 | 0.528 | 3/4 | 0/4 |

`attribute_count`에서는 4개 모델, `path_mode`에서는 Qwen2·Idefics2·InternVL3 대비 구조 oracle 우세가 모든 사전 조건을 만족했다. 그러나 `temporal_relation`은 COT 정확도가 0.327이고 사건 class 간 이질성이 커서 어떤 모델 대비도 class-cluster CI를 통과하지 못했다. Qwen2 visual both의 평균은 0.439로 COT보다 0.111 높았지만 95% clip CI [−0.228, +0.006], BH q=0.078815여서 visual 우세로 인정되지 않았다.

따라서 동일 모델 안에서 서비스군에 따라 구조와 시각 우세가 서로 갈리는 셀은 없었다.

**사전 판정: `RESCUE_INCONCLUSIVE`.**

### 18.2 민감도와 실패 경계

| 범위 | COT worse | COT better | both mean | both max |
|---|---:|---:|---:|---:|
| 전체 | 0.612 | 0.617 | 0.619 | 0.624 |
| temporal relation | 0.310 | 0.327 | 0.316 | 0.316 |
| attribute/count | 0.709 | 0.718 | 0.748 | 0.709 |
| path/mode | 0.944 | 0.928 | 0.928 | 0.976 |

두 view 결합법을 바꿔도 결과가 바뀌지 않았다. temporal relation에서 `비정상적인 경로로의 침범`과 `특정 구역 내 지속 배회`의 COT zero-shot 정확도는 각각 0이었다. 이 결과는 궤적이 무가치하다는 증거가 아니라, 현재의 label-derived 자연어 단계와 사건명 query prototype이 인접 관계 class를 안정적으로 구분하지 못한다는 실패 경계다.

### 18.3 좁은 view-selection 보조 결과

asymmetric 249 clips에서 bbox가 큰 better view 3장과 작은 worse view 3장을 비교했다.

| 모델 | worse | better | both | better−worse | better의 both 대비 비열등 |
|---|---:|---:|---:|---:|---|
| Qwen2.5-VL | 0.133 | 0.189 | 0.197 | +0.056 | 예 |
| Qwen2-VL | 0.157 | 0.309 | 0.317 | +0.153 | 아니오 |
| Idefics2 | 0.096 | 0.141 | 0.124 | +0.044 | 예 |
| InternVL3 | 0.161 | 0.245 | 0.253 | +0.084 | 예 |

better view의 JPEG 바이트는 both의 50.2%였고 3/4 모델에서 5%p margin 기준 비열등했다. 판정은 `VIEW_SELECTION_NARROW_PASS`다. 이는 정답 bbox를 이용해 잘 보이는 시점을 안다는 oracle 조건의 저장 축소 결과이지, IntentStore 서비스 의도 제어기의 타당성은 아니다.

### 18.4 실제 저장량

| 표현 | clip당 평균 | 399개 전체 |
|---|---:|---:|
| COT 1-view 텍스트+vector | 4.3 KiB | 1.7 MiB |
| COT 2-view 텍스트+vector | 8.6 KiB | 3.3 MiB |
| visual 1-view JPEG 3장 | 154.6 KiB | 60.2 MiB |
| visual 2-view JPEG 6장 | 307.6 KiB | 119.9 MiB |

구조 추출, bbox/label 생성, VLM 추론과 DB overhead는 포함하지 않았다.

## 19. 최종 연구 주제 수렴

### 19.1 범용 IntentStore를 확정하는가

**아니다.** P0-C의 caption 지배 뒤 P0-D에서도 서비스별 표현 비지배성을 확인하지 못했다. `RESCUE_INCONCLUSIVE`는 “IntentStore 가설이 거짓임을 입증했다”는 뜻은 아니지만, 연구 주제를 확정하고 수개월의 GPU·시스템 구현에 들어갈 양의 근거가 없다는 뜻이다.

따라서 현재 운영 결론은 다음과 같다.

- 범용 IntentStore를 주력 연구 주제로 선정하지 않는다.
- P1~P3, 새 GPU 생성, 온라인 controller 구현을 승인하지 않는다.
- 이번 결과를 EDBT급 시스템 기여로 확대하지 않는다.
- 같은 데이터에서 임계값이나 서비스군을 다시 나눠 통과를 찾지 않는다.
- 재개하려면 자동 trajectory extractor, 독립 공개 데이터, open-world/미래 질의라는 새 자산을 먼저 확보하고 별도 protocol로 시작한다.

### 19.2 남길 수 있는 좁은 후보

1. **Oracle-free multiview evidence selection**: 정답 bbox 없이 view utility를 예측하고 1-view가 2-view 대비 안전 품질을 유지하는지 평가한다.
2. **Trajectory representation extraction**: label-derived COT가 아니라 detector/tracker 출력에서 관계 표현을 자동 생성하고 인접 temporal class 구분 실패를 줄인다.
3. **Caption failure-boundary benchmark**: caption이 직접 쓰지 않은 미래 질의에서 raw/trajectory를 보존할 가치만 독립적으로 측정한다.

현재 P0-D 결과만으로는 어느 후보도 EDBT급이 아니다. 공개 데이터 일반화, 강한 시스템 baseline, 비용·지연, 실제 query workload가 추가돼야 한다.

**최종 운영 상태: `DO_NOT_CONFIRM_INTENTSTORE — CURRENT_RESEARCH_DESIGN_CLOSED`.**

## 20. P0-D 재현 명령과 산출물

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/experiments_expansion
python -m py_compile intentstore_p0_cpu/scripts/analyze_p0d_multiview_rescue.py
python intentstore_p0_cpu/scripts/analyze_p0d_multiview_rescue.py
```

CPU 재실행은 약 7~10초였고, 핵심 CSV와 JSON 6개의 SHA-256이 연속 두 실행에서 모두 일치했다.

- P0-D 규칙: [P0_D_MULTIVIEW_RESCUE_PROTOCOL.md](P0_D_MULTIVIEW_RESCUE_PROTOCOL.md)
- P0-D 결과: [P0_D_MULTIVIEW_RESCUE_REPORT.md](P0_D_MULTIVIEW_RESCUE_REPORT.md)
- 분석 코드: [scripts/analyze_p0d_multiview_rescue.py](scripts/analyze_p0d_multiview_rescue.py)
- 기계 판정: [results/p0d_decision.json](results/p0d_decision.json)
- 주 검정: [results/p0d_primary_tests.csv](results/p0d_primary_tests.csv)
- clip별 결과: [results/p0d_per_clip.csv](results/p0d_per_clip.csv)
- 입력 hash·정합성: [results/p0d_source_manifest.json](results/p0d_source_manifest.json)
