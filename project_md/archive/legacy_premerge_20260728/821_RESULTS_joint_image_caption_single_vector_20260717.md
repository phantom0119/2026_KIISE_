# 단일 Image+Caption 통합 벡터 비교 실험 결과

- 실행일: 2026-07-17
- 사전 정의 프로토콜: `820_JOINT_IMAGE_CAPTION_SINGLE_VECTOR_PROTOCOL_20260717.md`
- 데이터: 522 교차로 파생 비순환 워크로드, 3,000 clips, 85 queries
- 공통 임베더: Qwen3-VL-Embedding-2B, 2,048 dimensions, L2 normalization
- 주평가: Flat exact search, B2 pure similarity, strict/semantic nDCG@10
- 불확실성: query bootstrap 10,000회와 intent×facet 25개 cluster bootstrap 10,000회

## 1. 실험 목적

이 실험은 대표 이미지와 그 이미지에서 생성한 캡션을 하나의 멀티모달 입력으로 동시에 인코딩하여
클립당 하나의 벡터로 저장하는 `joint_image_caption` 표현을 기존 비교군에 추가한다. 주 질문은
다음 세 가지다.

1. 같은 2,048차원 단일 벡터 예산에서 joint 표현이 caption-only 및 representative-frame보다
   검색 품질을 높이는가?
2. 올바르게 정렬된 image-caption 쌍이 무작위로 뒤섞인 image-caption 쌍보다 우수한가?
3. joint 표현은 multi-frame 또는 dual-index보다 낮은 비용의 중간 운용점이 되는가?

## 2. 벡터 생성 및 무결성

| 처리군 | Pairing | 벡터 수×차원 | payload | GPU 실행 시간 | 처리율 |
|---|---:|---:|---:|---:|---:|
| joint matched | 동일 clip의 image+caption | 3,000×2,048 | 24.576 MB | 827.45초(13.79분) | 3.63 clips/s |
| joint shuffled | 고정점 없는 caption 치환 | 3,000×2,048 | 24.576 MB | 727.81초(12.13분) | 4.12 clips/s |

두 처리군은 BF16 추론, FlashAttention2, `Represent the user's input.` 지시문 및 같은 모델 가중치를
사용했다. Matched는 3,000/3,000 쌍이 동일 clip이고, shuffled는 고정점 0개이며 3,000개 caption
source가 중복 없이 한 번씩 사용되었다. 모든 벡터는 finite이고 L2 norm 범위는 matched
0.9975–1.0025, shuffled 0.9974–1.0025였다.

독립 검증기는 shape, pairing, clip order, frozen encoder settings, 원시 ranking 기반 nDCG 재계산,
필터 predicate 위반 여부 등을 포함한 17개 검사를 모두 통과했다.

## 3. 동일 단일-벡터 예산의 주 비교

Flat/B2 결과는 다음과 같다. 네 처리군 모두 클립당 하나의 2,048차원 float32 벡터이므로 벡터
payload는 24.576 MB로 같다.

| 표현 | strict nDCG@10 | semantic nDCG@10 | p50 latency | p95 latency |
|---|---:|---:|---:|---:|
| caption | 0.0626 | 0.1810 | 1.146 ms | 1.488 ms |
| representative frame | 0.0625 | 0.1865 | 1.172 ms | 1.479 ms |
| **joint matched** | **0.0794** | **0.2182** | **1.138 ms** | **1.443 ms** |
| joint shuffled | 0.0572 | 0.1958 | 1.170 ms | 1.523 ms |

점추정치 기준으로 joint matched는 caption 대비 semantic nDCG@10이 +0.0372
(상대 +20.53%), representative frame 대비 +0.0317(상대 +16.98%) 높다. 저장 payload와 검색
지연은 사실상 같은 범위이므로, `joint_image_caption`은 단일 벡터 비교군으로 포함할 실질적 가치가
있다.

그러나 통계적 결론은 반복 단위에 따라 다르다.

| 비교 | 평가 | 평균 차이 | Query 95% CI | Cluster 95% CI |
|---|---|---:|---:|---:|
| joint matched − caption | semantic | +0.0372 | [+0.0156, +0.0586] | [-0.0048, +0.0742] |
| joint matched − caption | strict | +0.0168 | [-0.0014, +0.0364] | [+0.0059, +0.0289] |
| joint matched − representative frame | semantic | +0.0317 | [+0.0030, +0.0614] | [-0.0165, +0.0836] |
| joint matched − representative frame | strict | +0.0169 | [-0.0049, +0.0403] | [+0.0001, +0.0358] |

따라서 “85개 질의에서 평균적으로 우수한 단일 벡터 운용점”이라는 결론은 가능하지만,
“새로운 intent×facet 군집에도 항상 일반화되는 우위”로 과장해서는 안 된다. 특히 semantic의
caption 대비 query CI는 양수이나 cluster CI는 0을 포함한다.

## 4. Matched–Shuffled 음성 대조

Matched와 shuffled의 차이는 strict +0.0223, semantic +0.0224였으나 두 평가 모두 query 및
cluster bootstrap 신뢰구간이 0을 포함했다.

| 평가 | 평균 차이 | Query 95% CI | Cluster 95% CI |
|---|---:|---:|---:|
| strict | +0.0223 | [-0.0095, +0.0555] | [-0.0120, +0.0611] |
| semantic | +0.0224 | [-0.0345, +0.0799] | [-0.0930, +0.1445] |

따라서 현재 결과만으로는 joint matched의 향상이 “정확한 image-caption 정렬” 때문에 발생했다고
인과적으로 주장할 수 없다. Qwen 임베더에 시각·텍스트 토큰을 함께 제공하는 입력 형식 자체의 효과,
caption 정보의 우세 또는 표본 변동 가능성이 남는다. 이 음성 대조는 joint 비교군의 가치는 지지하지만,
정렬 기반 융합 메커니즘의 입증은 보류하게 한다.

## 5. 다중 벡터·이중 색인과의 비용–품질 절충

전체 5개 표현의 Flat/B2 결과는 다음과 같다.

| 표현 | strict nDCG@10 | semantic nDCG@10 | p50 latency | p95 latency | vector payload |
|---|---:|---:|---:|---:|---:|
| caption | 0.0626 | 0.1810 | 1.155 ms | 1.488 ms | 24.576 MB |
| representative frame | 0.0625 | 0.1865 | 1.207 ms | 1.529 ms | 24.576 MB |
| **joint image+caption** | **0.0794** | **0.2182** | **1.243 ms** | **1.574 ms** | **24.576 MB** |
| multi-frame | 0.1014 | 0.3518 | 3.651 ms | 4.274 ms | 68.395 MB |
| dual-index RRF | 0.0889 | 0.2933 | 4.959 ms | 5.661 ms | 92.971 MB |

Joint는 정확도 최고점이 아니다. Multi-frame 대비 semantic nDCG@10은 0.1336 낮지만 vector
payload는 64.07%, p95 latency는 63.18% 낮다. Dual-index 대비 semantic nDCG@10은 0.0751
낮지만 payload는 73.57%, p95 latency는 약 72.2% 낮다. 그러므로 joint는 caption/frame보다 높은
검색 품질과 multi-frame/dual보다 낮은 비용을 연결하는 **중간 Pareto 후보**로 해석하는 것이 맞다.

## 6. 필터 결합 계획

Joint/Flat의 검색 계획별 결과는 다음과 같다.

| 검색 계획 | strict nDCG@10 | semantic nDCG@10 | p50 | p95 |
|---|---:|---:|---:|---:|
| B2 pure similarity | 0.0794 | 0.2182 | 1.243 ms | 1.574 ms |
| B3 postfilter, top-200 | 0.1805 | 0.1777 | 1.284 ms | 1.603 ms |
| B4 prefilter | 0.1861 | 0.1829 | 0.532 ms | 1.137 ms |

B4−B2의 strict 차이는 +0.1067이며 query CI [+0.0818,+0.1334], cluster CI
[+0.0666,+0.1418]로 모두 양수다. 반면 semantic 차이는 -0.0353으로, query CI
[-0.0648,-0.0059], cluster CI [-0.0676,-0.0024]다. 즉 명시적 hard predicate 준수에는
prefilter가 유리하지만, metadata와 독립적인 장면 의미 검색에서는 순수 유사도 검색이 더 낫다.
두 목적을 하나의 “정확도”로 합치지 않아야 한다.

## 7. 색인 비교

Joint/B2의 주요 색인 결과는 다음과 같다.

| 색인 | semantic nDCG@10 | p95 | index size | Exact-task top-10 fidelity |
|---|---:|---:|---:|---:|
| Flat | 0.2182 | 1.574 ms | 24.576 MB | 1.0000 |
| HNSW ef64 | 0.2193 | 0.312 ms | 25.392 MB | 0.9647 |
| **HNSW ef256** | **0.2182** | **0.865 ms** | **25.392 MB** | **1.0000** |
| IVF-Flat nprobe32 | 0.2182 | 0.810 ms | — | 0.9988 |
| IVF-PQ nprobe8 | 0.1928 | 0.142 ms | 1.145 MB | 0.3824 |

HNSW ef256은 Flat과 동일한 task score 및 top-10 fidelity를 유지하면서 p95를 45.05% 줄이고,
직렬화 색인 크기를 3.32% 늘린다. IVF-PQ는 Flat 대비 약 95.34% 작은 색인을 제공하지만 fidelity가
0.3824로 급락하므로, 메모리 제약이 극단적인 경우가 아니라면 정확 검색 대체재로 해석하면 안 된다.

## 8. 논문에 허용되는 결론

- 포함 가능: `joint_image_caption`은 동일한 단일 벡터 예산에서 caption/frame보다 높은
  nDCG@10 점추정치를 보인 유효한 비교군이다.
- 포함 가능: joint는 multi-frame/dual보다 품질은 낮지만 저장 공간과 지연이 크게 작은 중간
  비용–품질 운용점이다.
- 포함 가능: joint에서도 prefilter의 hard-constraint 이득과 semantic 손실의 목적 충돌이
  재현된다.
- 포함 가능: 높은 fidelity가 필요할 때 HNSW ef256은 Flat과 같은 task 결과를 보존하며 지연을
  낮춘다.
- 보류: 정확히 정렬된 image-caption 쌍 자체가 향상의 원인이라는 인과 주장.
- 보류: 3,000-clip 단일 522 파생 워크로드의 결과를 모든 도시 감시 데이터로 일반화하는 주장.
- 보류: VLM 최종 답변 정확도 향상. 본 실험의 직접 종속변수는 evidence retrieval 품질이다.

## 9. 산출물

- 벡터 생성기: `2026_KIISE/scripts/build_qwen3_joint_image_caption_assets.py`
- 동일 예산 대조 평가: `2026_KIISE/scripts/evaluate_joint_image_caption_controls.py`
- 전체 비교 파이프라인: `2026_KIISE/scripts/run_joint_storage_search_index.py`
- 통합 분석기: `2026_KIISE/scripts/analyze_joint_optimization_validation.py`
- 독립 검증기: `2026_KIISE/scripts/verify_joint_image_caption_experiment.py`
- 대조 결과: `2026_KIISE/paper_assets/20260717_joint_image_caption_controls/`
- 112개 구성 결과: `2026_KIISE/paper_assets/20260717_joint_image_caption_validation/`
- 독립 검증 보고서:
  `2026_KIISE/paper_assets/20260717_joint_image_caption_validation/JOINT_IMAGE_CAPTION_VERIFICATION_KO.md`

