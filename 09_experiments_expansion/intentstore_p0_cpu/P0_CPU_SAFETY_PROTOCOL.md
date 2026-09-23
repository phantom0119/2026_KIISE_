# IntentStore P0-C 안전 서비스 표현 검증 규칙

> 등록일: 2026-08-06  
> 상태: **신규 교차 표현 결과 생성 전 고정**  
> 범위: VRU-Accident와 AI Hub 지능형 CCTV의 비순환 질의에서, 원본 영상이 만료되고 파생 표현만 남았다고 가정한 검색 지원력 proxy를 CPU로 검증한다.

## 1. 이 검증이 답하는 질문

이 단계는 다음 한 가지를 검사한다.

> 실제 안전 사건 질의에서 caption, 한 장의 중앙 keyframe, 네 장의 keyframe, caption+네 장 keyframe 가운데 하나가 모든 서비스에 지배적인가, 아니면 서비스 의도에 따라 보존 가치가 달라지는가?

검색 nDCG는 위험 감지 F1이나 실제 경보 지연이 아니다. 따라서 이 단계는 IntentStore의 **G1 표현 비지배성**만 선별하며, 온라인 보존 제어기·원본 TTL·위험가중 손실·tail latency까지 통과시키지 않는다.

## 2. 고정 입력

### VRU-Accident

- 비순환 canonical: `Datasets/processed/vru_accident/20260710_noncircular/canonical`
- caption 검색 결과: `.../results/vru2_bgem3_b0_b5`
- 동결 CLIP frame embedding: `Datasets/processed/vru_accident/20260706/visual_embeddings/clip-vit-base-patch32_full`
- 규모: 1,000 clips, 85 query contracts, clip당 4개 균등 keyframe

### AI Hub 지능형 CCTV

- 비순환 canonical: `Datasets/processed/aihub_intelligent_cctv/20260710_noncircular/canonical`
- caption 검색 결과: `.../results/acctv2_bgem3_b0_b5`
- 동결 CLIP frame embedding: `Datasets/processed/aihub_intelligent_cctv/20260706/visual_embeddings/clip-vit-base-patch32_full`
- 규모: 269 clips, 18 query contracts, clip당 4개 event 구간 keyframe

두 데이터셋의 문서 코퍼스는 label statement를 제거한 caption-only 비순환 버전이다. CLIP frame embedding은 영상 frame에서 만들어졌으므로 caption label 누설과 독립이다. 새로 필요한 103개 CLIP text-query embedding만 로컬에 캐시된 `openai/clip-vit-base-patch32`를 **CPU·offline 모드**로 생성한다.

이 분석의 구성요소 결과 일부는 이전 논문 실험에서 이미 존재하므로 완전한 맹검은 아니다. 다만 새 비순환 질의에 대한 CLIP 재임베딩, 표현 간 동일-qrels 결합, 서비스군 통계와 게이트 판정은 이 문서 뒤에 처음 실행한다.

## 3. 고정 표현 arm

| arm | 보존한 파생 증거 | vector payload/clip | 검색 방식 |
|---|---|---:|---|
| `caption` | BGE-M3 caption vector | 4,096 B | no-filter는 B2, 조건 질의는 B4 prefilter |
| `center_frame` | CLIP 중앙 keyframe 1개 | 2,048 B | exact inner-product, 조건 질의는 동일 metadata prefilter |
| `visual_4frame` | CLIP keyframe 4개 | 8,192 B | frame 점수의 clip별 max, 동일 prefilter |
| `fusion` | caption + 4 keyframes | 12,288 B | 두 순위의 RRF, `k=60`, 가중치 1:1 |

`center_frame`은 frame 수가 짝수일 때 앞쪽 중앙 frame, 즉 정렬된 `frame_seq=1`을 사용한다. `visual_4frame`은 순서를 모델링하지 않는 max pooling이므로 “시간 추론 모델” 또는 “multi-frame VLM”으로 부르지 않는다.

payload는 float32 vector만 센 값이다. caption 문자열, keyframe JPEG, 메타데이터, DB 오버헤드와 원본 영상은 제외하므로 총 저장비가 아니라 **통제된 vector payload proxy**다.

## 4. qrels와 평가

- strict qrels만 주 평가에 사용한다.
- 주 지표: query별 nDCG@10
- 보조 지표: Hit@10, Recall@10
- 모든 arm은 같은 query text, 같은 strict qrels, 같은 clip 모집단을 사용한다.
- filtered query는 caption과 visual 모두 같은 metadata candidate set을 사용한다.
- 최대 반환 수: 100 clips
- 정보성 바닥: 서비스군 query contracts `n>=10`, 승자 평균 nDCG@10 `>=0.05`
- 최소 실질 효과: nDCG@10 절대차 `0.05`

## 5. 사전 서비스군

event type은 각 query의 strict-positive clips에서 공통인 `accident_type` 또는 `event_class`로 복원한다.

1. `dynamic_event`: VRU의 모든 충돌·near-miss·낙상과 AI Hub의 intrusion, fall-down, fight
2. `scene_state`: AI Hub의 gathering, flood, crowd-density
3. `context_filtered`: 시간대·도로·장소·날씨 metadata 조건이 있는 모든 query
4. `open_event`: metadata 조건이 없는 사건 의미 query

앞의 두 군은 사건 메커니즘, 뒤의 두 군은 서비스 계약 구조를 나타낸다. 군이 겹친다는 사실을 숨기지 않고, 모든 주 검정을 한 family로 함께 FDR 보정한다.

## 6. 주 가설과 통계

고정된 네 대비만 검사한다.

| ID | 서비스군 | paired difference | 설계상 기대 |
|---|---|---|---|
| H1 | dynamic_event | `visual_4frame - caption` | 여러 시점 시각 증거 우세 가능 |
| H2 | scene_state | `caption - visual_4frame` | 장면 상태의 언어 요약 우세 가능 |
| H3 | context_filtered | `fusion - caption` | 조건 사건에서 보완 증거 이득 가능 |
| H4 | 전체 | `visual_4frame - center_frame` | keyframe coverage 이득 가능 |

- query contract 단위 paired sign-flip randomization 200,000회, 양측 p-value
- H1~H4 전체 Benjamini-Hochberg FDR
- query contract paired bootstrap 20,000회 95% CI
- 같은 event type의 반복 조건 질의 의존성을 보기 위해 `(dataset, event_type)` cluster bootstrap 20,000회 CI를 민감도 분석으로 병기
- seed: `20260806`

confirmatory support는 `|평균차|>=0.05`, `q<0.05`, query bootstrap CI가 0 제외, 기대 방향 일치가 모두 필요하다. cluster CI가 0을 포함하면 결과를 “query-contract 수준 지지, 독립 event 일반화 미확정”으로 강등한다.

## 7. 원본 만료 지원 proxy

원본 영상이 삭제되고 각 arm만 남은 상황을 다음과 같이 측정한다.

- 서비스군별 arm 평균 nDCG@10와 Hit@10
- nDCG@10이 0.05 이상인 query contract 비율
- 서비스군별 품질-비용 Pareto arm
- `fusion`이 최선 단일 arm보다 0.02 이상 개선하는지

이것은 기존 파생 증거만으로 과거 사건을 검색하는 **retrospective support**다. 아직 등장하지 않은 새 서비스, 실제 detector 재실행, 원본 재해석 가능성을 직접 측정하지 않으므로 “future-query completeness”로 과장하지 않는다.

## 8. G1 안전 게이트

- `SAFETY_G1_PROVISIONAL_PASS`: H1과 H2가 각각 기대 방향으로 confirmatory support를 받고, 서로 다른 저비용 Pareto arm이 남으며, cluster 민감도 방향도 일치한다.
- `SAFETY_G1_CONTINUE`: 적어도 하나의 실제 안전 서비스 대비가 confirmatory support를 받거나, 서로 다른 서비스군에서 서로 다른 단일 arm이 0.05 이상 우세하지만 provisional pass의 전체 조건은 부족하다.
- `SAFETY_G1_INCONCLUSIVE`: 차이는 있으나 FDR·효과량·정보성·독립 event 일반화 조건을 통과하지 못한다.
- `SAFETY_G1_STOP_SIGNAL`: 모든 정보성 서비스군에서 같은 단일 arm이 다른 단일 arm보다 0.05 이상 우세하고, fusion의 추가 이득도 0.02 미만이다.

`PROVISIONAL_PASS`조차 연구 주제 최종 확정은 아니다. 최종 확정에는 같은 stream의 다중 서비스 replay에서 원본 TTL을 적용하고, IntentStore 정책이 best-static보다 위험/SLA 제약을 지키면서 자원을 실질 절감하는 G2가 필요하다.

## 9. 금지 해석

- CLIP/BGE encoder 차이를 순수한 데이터 형식 효과로 해석하지 않는다. arm은 encoder까지 포함한 **end-to-end representation stack**이다.
- 네 keyframe max를 사건 순서 이해라고 부르지 않는다.
- 검색 nDCG를 위험 미탐률, 사건 F1, 최종 VLM 답변 정확도로 바꾸지 않는다.
- AI Hub 269 clips를 운영 규모 실시간 검증으로 부르지 않는다.
- 기존 GPU 생성 비용이나 실시간 ingest 비용이 없으므로 현재 검색 latency를 end-to-end SLA 증거로 쓰지 않는다.

## 10. 예정 산출물

- `scripts/analyze_safety_representation.py`
- `results/safety_source_manifest.json`
- `results/safety_per_query_metrics.csv`
- `results/safety_service_means.csv`
- `results/safety_primary_tests.csv`
- `results/safety_pareto.csv`
- `results/safety_decision.json`
- `P0_CPU_SAFETY_REPORT.md`

## 11. 결과 확인 뒤 발견한 자동 판정 우선순위 결함

> 상태: **사후 구현 감사(2026-08-06)**. 효과량·검정·임계값을 바꾸지 않는다.

최초 스크립트는 `CONTINUE`의 “적어도 한 대비 지지”를 `STOP_SIGNAL`보다 먼저 검사했다. 그러나 한 표현이 모든 서비스군에서 우세하면, 그 우세를 확인하는 유의한 대비 자체가 동시에 `CONTINUE`를 만족할 수 있다. 실제 첫 실행에서 이 논리적 중첩이 발생했다.

두 규칙의 취지상 더 구체적인 지배 조건을 우선해야 하므로 자동 판정 순서를 다음처럼 바로잡는다.

1. H1+H2와 서로 다른 Pareto arm을 모두 만족하면 `PROVISIONAL_PASS`
2. 동일 단일 arm이 네 정보성 서비스군을 실질 지배하고 fusion 이득이 없으면 `STOP_SIGNAL`
3. 그 밖에 일부 대비만 지지되면 `CONTINUE`
4. 나머지는 `INCONCLUSIVE`

최초 실행 산출물은 덮어쓰기 전에 콘솔 기록으로 남아 있으며, 통합 기록에는 최초 `SAFETY_G1_CONTINUE`가 판정 순서 버그였음을 명시한다. 수정 뒤 통계량 자체가 변하지 않는지도 재실행으로 확인한다.
