# 최신 데이터셋·실험 체계 종합

작성 기준일: 2026-07-09

## 판정

현재 데이터셋 구축은 **체계를 잡은 상태**로 볼 수 있다. 단순히 원본 데이터를 모아 둔 단계가 아니라, 다음 조건을 대부분 충족한다.

| 기준 | 상태 | 근거 |
|---|---|---|
| 원본 확보 | 완료 | VRU, AI Hub 지능형 CCTV, 이상행동 CCTV, 다각도 CCTV, CityFlow-NL, 시내도로 CCTV, 교차로신호체계 확보 |
| 공통 스키마 | 완료 | `clips/documents/metadata/queries/qrels` canonical schema 구축 |
| 실제 영상 프레임 | 완료 | VRU 4,000 frames, AI Hub 지능형 CCTV 1,076 frames, 다각도 CCTV stratum 2,400 frames |
| 시각 임베딩 | 완료 | CLIP/SigLIP 기반 frame embedding 및 text-query embedding |
| 텍스트 임베딩 | 완료 | BGE-M3, E5-large-v2, bge-m3-ko 보강 |
| 검색 baseline | 완료 | B0-B5, pgvector P2/P4, M2/M4, M5/M6, IM1 |
| answer evidence 평가 | 완료 | service packet, weighted RRF, LLM answer layer, multi-view VLM answer layer |
| 색인 구조 벤치마크 | 완료 | 시내도로 CCTV real 132K + synthetic 1M, Flat/IVF/HNSW/IVF-PQ |
| 재현성 감사 | 대체로 완료 | pipeline audit, control audit, run manifests, 4-VLM result manifests |

따라서 현 상태는 **데이터셋 구축 완료 + 실험 체계 안정화 + 제출 전 품질관리 단계**다. 남은 일은 새 데이터를 더 모으는 것이 아니라, 원고와 제출 패키지의 정합성 검수, 표·그림·참고문헌 확인, 일부 결과의 한계 표현 조정이다.

## 최신 연구 프레임

최신 논문 프레임은 다음 한 문장으로 정리한다.

> 도시 교통·감시형 멀티모달 데이터베이스에서 AI 응답 품질은 모델만이 아니라, DB가 영상 프레임·텍스트 evidence·구조화 metadata를 어떻게 저장·색인·검색·선택하는지에 의해 좌우된다.

이제 연구는 세 계층으로 나뉜다.

| 계층 | 질문 | 대표 결과 |
|---|---|---|
| Evidence DB 구축 | 서로 다른 도시 감시 데이터를 같은 DB schema로 정규화할 수 있는가? | VRU, AI Hub 지능형 CCTV, 이상행동 CCTV, 다각도 CCTV canonical 구축 완료 |
| Retrieval/selection | 어떤 검색·선택 구조가 좋은 evidence를 반환하는가? | B4/M4/RW_t4_v1, service packet, reranker 결과 |
| Answer-level 검증 | DB evidence 구성만 바꾸면 답변 정확도가 달라지는가? | LLM evidence ladder, 다각도 better-view selection 결과 |

## 데이터셋별 최신 상태

| 데이터셋 | 원본 상태 | canonical | visual materialization | 최신 역할 |
|---|---:|---:|---:|---|
| VRU-Accident | 1,000 mp4, 6,000 VQA, 1,000 caption | 완료 | 4,000 frames | 교통 안전 video QA anchor |
| AI Hub 지능형 CCTV | 269 mp4/json pair | 완료 | 1,076 frames | 국내 CCTV event anchor |
| AI Hub 이상행동 CCTV | 1,968 usable clips/XML | 완료 | 본문 visual track 미포함 | text/metadata robustness |
| AI Hub 다각도 CCTV 71953 | 44 zip, 9,000 mp4 entries, 4,500 labels | 완료 | 2,400 stratum frames + T1 samples | multi-view evidence DB 및 answer-level 핵심 |
| 시내도로 CCTV | 132,521 real CLIP vectors 구축 | index corpus 중심 | JPG streaming sample | index structure benchmark |
| CityFlow-NL | annotation + raw zip 확보 | annotation canonical 완료 | full visual 추출 전 | NL vehicle retrieval extension 후보 |
| 교차로신호체계 | CSV/7z 원본 확보 | 설계 완료 | visual sample 전 | metadata/log extension 후보 |

핵심 판단: **논문 본문 주장은 VRU + AI Hub 지능형 CCTV + AI Hub 다각도 CCTV + 시내도로 index benchmark까지로 방어 가능**하다. CityFlow-NL과 교차로신호체계는 확보·설계는 되었지만, 본문 핵심 수치로 강하게 주장하기보다는 확장 가능성과 후속 연구로 두는 편이 안전하다.

## 최신 주요 결과

### 1. Text/metadata baseline

VRU에서 metadata prefilter + dense vector(B4)는 vector-only(B2)보다 크게 높았다.

| Dataset | 비교 | nDCG@10 |
|---|---|---:|
| VRU | B2 vector-only | 0.4476 |
| VRU | B4 metadata prefilter+vector | 0.9736 |
| AI Hub CCTV | B2 vector-only | 0.7014 |
| AI Hub CCTV | B4 metadata prefilter+vector | 1.0000 |

pgvector P4도 VRU에서 FAISS B4와 같은 품질 지표를 재현했다. 단, latency 우위는 주장하지 않는다.

### 2. Visual text-to-video 및 fusion

| Dataset | M2 visual-only R@10 | M4 metadata+visual R@10 | M6 R@10 |
|---|---:|---:|---:|
| VRU | 0.0616 | 0.2467 | 0.4928 |
| AI Hub CCTV | 0.1000 | 0.7524 | 0.8016 |

해석은 “visual encoder가 사건을 잘 이해했다”가 아니라, **metadata-aware query planning이 visual frame retrieval에서도 후보 공간을 안정화한다**는 것이다.

### 3. Image-to-video

| Dataset | R@1 | R@10 | nDCG@10 |
|---|---:|---:|---:|
| VRU | 0.7550 | 0.9800 | 0.8875 |
| AI Hub CCTV | 0.8810 | 1.0000 | 0.9442 |

이미지나 스크린샷으로 원본 영상 clip을 찾는 서비스 기능은 실험적으로 동작했다. 단, frame position sensitivity를 함께 명시해야 한다.

### 4. Service evidence selection

| Dataset | Equal M6 Hit@1 | RW_t4_v1 Hit@1 | RW_t4_v1 nDCG@10 |
|---|---:|---:|---:|
| VRU | 0.7131 | 0.8443 | 0.8847 |
| AI Hub CCTV | 0.9248 | 0.9699 | 0.9768 |

top-k 안에 정답이 있어도 rank-1 evidence가 틀리면 답변 품질이 떨어질 수 있으므로, retrieval 이후 selection/reranking이 필요하다는 주장이 강화되었다.

### 5. LLM answer layer

VRU VQA 600문항에서 LLM을 고정하고 DB evidence 구성만 바꾸었다.

| Evidence 구성 | Qwen2.5-7B | Llama-3-8B |
|---|---:|---:|
| closed | 0.3083 | 0.3067 |
| vector-only | 0.6650 | 0.6650 |
| prefilter | 0.6800 | 0.6667 |
| oracle | 0.7467 | 0.6900 |

답변 수준에서는 prefilter와 vector-only 차이가 작으므로, 과장하면 안 된다. 핵심은 **evidence 품질이 높아질수록 답변 정확도가 상승한다**는 점이다.

### 6. 다각도 CCTV answer-level VLM

AI Hub 다각도 CCTV 400 clip stratum에서 고정 VLM에 어떤 view evidence를 공급하는지만 바꾸었다.

| Model | both acc | better-worse | p | both-better |
|---|---:|---:|---:|---|
| Qwen2.5-VL | 0.2000 | +0.056 | 0.0016 | TOST equivalent |
| Qwen2-VL | 0.3025 | +0.152 | 0.0002 | TOST equivalent |
| InternVL3-8B | 0.2450 | +0.084 | 0.0002 | TOST equivalent |
| Idefics2-8b | 0.1450 | +0.044 | 0.0256 | TOST equivalent, near-chance caveat |

방어 가능한 결론은 다음이다.

> bbox 면적 기반 geometric visibility asymmetry 조건에서, 세 개의 강한 VLM은 better-view가 worse-view보다 유의하게 높고, both-view는 better-view와 등가였다. 따라서 다각도 CCTV DB의 역할은 모든 시점을 많이 쌓는 것이 아니라 더 나은 시점을 선택해 공급하는 것이다.

금지 표현:

- “다각도 CCTV는 일반적으로 무의미하다.”
- “두 view에 상보 정보가 없다.”
- “Idefics2로 강한 LLM-family independent 검증이 완료됐다.”
- “VLM이 CCTV event class를 전반적으로 잘 분류한다.”

### 7. 저장·색인 구조 벤치마크

시내도로 CCTV JPG에서 132,521개 real CLIP vector를 구축하고, 분포 보존 synthetic 증강으로 1M scale까지 벤치마크했다.

| N | Flat p50 | HNSW p50 | 해석 |
|---:|---:|---:|---|
| 10K | 0.90ms | 0.018ms | ANN 이점 시작 |
| 100K | 10.2ms | 0.043ms | HNSW 약 237배 빠름 |
| 131K | 13.4ms | 0.041ms | real corpus 기준 crossover 명확 |
| 1M | 98.5ms | 0.061ms | scale 증가 시 Flat 선형 악화 |

Filtered ANN 벤치마크에서는 selectivity가 매우 낮을 때 post-filter recall이 붕괴했다(1%에서 0.742). 따라서 metadata predicate가 강한 운영 질의에서는 pre-filter가 품질상 필요하고, 넓은 predicate에서는 full ANN + post-filter도 선택지가 된다.

## 최신 기준 문서

| 용도 | 문서 |
|---|---|
| 최신 원고 | `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal.md` |
| 전체 pipeline 사양 | `2026_KIISE/project_md/24_final_experiment_pipeline_spec_20260707.md` |
| 전체 확보 데이터 설계 | `2026_KIISE/project_md/30_all_acquired_dataset_research_design_20260708.md` |
| 추가 확보 필요성 판정 | `2026_KIISE/project_md/31_additional_dataset_need_review_20260708.md` |
| 다각도 결과 최종 재검증 | `2026_KIISE/project_md/38_four_vlm_multiview_final_recheck_20260709.md` |
| index benchmark | `2026_KIISE/project_md/39_index_structure_benchmark_results_20260709.md` |
| 본 종합 상태 | `2026_KIISE/project_md/40_latest_dataset_and_experiment_synthesis_20260709.md` |

## 남은 작업

1. 제출용 Word/PDF 육안 검수: 표 20, 그림 6/7, index benchmark 그림, 참고문헌 [19]-[22].
2. `submission_materials_index.md`에 4-VLM, index benchmark, latest synthesis 반영.
3. 원고에서 “LLM/VLM 미사용”처럼 과거 단계 표현이 남지 않았는지 최종 검색.
4. Idefics2 결과는 보조·near-chance로만 유지.
5. CityFlow-NL/교차로신호체계는 후속 확장으로 두고 본문 핵심 claim에 과도하게 넣지 않는다.
