# 실험 통제 요인 재점검 및 추가 실험 필요성 판단

작성 기준일: 2026-07-07

2026-07-08 갱신 메모: 이후 대형 신규 데이터셋이 추가 확보되어, "새 대형 데이터셋 추가는 불필요"라는 판단은 최신 실험 범위에는 그대로 적용하지 않는다. 최신 방침은 모든 확보 데이터셋을 사용하되 full-scale embedding이 아니라 계층형 sample/extension/system-evidence 실험으로 반영하는 것이다. 세부 설계는 `30_all_acquired_dataset_research_design_20260708.md`를 기준으로 한다.

2026-07-09 최신 갱신: 본 문서의 2026-07-07 판단 중 `controlled LLM answer generation`과 `HNSW/IVFFlat` 보류 판단은 더 이상 최신 상태가 아니다. 이후 fixed LLM answer-layer, fixed VLM multi-view answer-layer, 시내도로 CCTV index-structure benchmark가 완료되었다. 최신 종합 판정은 `40_latest_dataset_and_experiment_synthesis_20260709.md`, 다각도 VLM 결과는 `38_four_vlm_multiview_final_recheck_20260709.md`, 색인 구조 결과는 `39_index_structure_benchmark_results_20260709.md`를 기준으로 한다.

## 결론

“추가 실험이 전혀 없다”가 정확한 표현은 아니다. 2026-07-07 기준으로는 새 대형 데이터셋 투입을 보류하는 판단이 안전했지만, 2026-07-08에 시내도로 교통 CCTV, 교차로신호체계, CityFlow-NL raw zip 등 신규 데이터셋이 실제로 확보되었으므로 실험 범위를 확장한다. 최신 판단은 모든 확보 데이터셋을 본 연구에 반영하되, full-scale embedding이 아니라 `anchor full result + traffic CCTV extension + metadata/log extension + robustness extension`의 계층형 설계로 통제하는 것이다.

최종 판단은 다음이다.

| 항목 | 판단 | 이유 |
|---|---|---|
| 새 대형 데이터셋 추가 | 계층형 반영 | 전체 압축 해제/full embedding은 금지하지만, 확보 데이터셋 모두를 sample/extension/system-evidence 실험으로 사용한다. 세부는 `30_all_acquired_dataset_research_design_20260708.md` 기준 |
| 시스템/환경 통제 감사 | 완료 | conda env, GPU, 디스크, package version, parquet 호환성 확인 완료 |
| 사용자 설정 통제 | 보강 완료 | RRF weight sweep, image query frame position sensitivity, frame budget ablation 완료 |
| 데이터셋 적합성 감사 | 완료 | qrels, metadata filter, keyframe, embedding shape/count 무결성 확인 완료 |
| 모델 다양성 | text/visual 모두 보강 | BGE-M3/E5 text robustness, CLIP/SigLIP visual encoder ablation 완료 |
| SigLIP visual ablation | 완료 | M2/M4, M5/M6, IM1, weighted RRF sweep 재실행 완료 |
| LLM/VLM answer generation | 고정 모델 통제 실험 완료 | 생성 모델 비교가 아니라 DB evidence 구성만 바꾸는 answer-level 통제 실험으로 범위를 제한 |
| HNSW/IVFFlat | index benchmark 완료 | 시내도로 CCTV real visual vectors와 synthetic scale-up으로 Flat/IVF-Flat/HNSW/IVF-PQ trade-off 평가 |

## 산출물

| 산출물 | 경로 |
|---|---|
| 통제 감사 스크립트 | `2026_KIISE/scripts/audit_experiment_control_factors.py` |
| 통제 감사 JSON | `2026_KIISE/paper_assets/20260707_control_factor_audit/control_factor_audit.json` |
| 통제 감사 요약 | `2026_KIISE/paper_assets/20260707_control_factor_audit/summary.md` |
| VRU qseq0/1/3 image-to-video 결과 | `Datasets/processed/vru_accident/20260706/results/image_to_video_clip_full_qseq*` |
| AI Hub qseq0/1/3 image-to-video 결과 | `Datasets/processed/aihub_intelligent_cctv/20260706/results/image_to_video_clip_full_qseq*` |
| SigLIP/Frame budget 보강 실험 요약 | `2026_KIISE/paper_assets/20260707_advanced_ablation/summary.md` |

## 1. 시스템 환경 통제 요인

감사 결과, 실험은 반드시 `Datasets/envs/kiise-vlmdb` conda 환경에서 재현해야 한다. 시스템 기본 Python에서는 일부 parquet read가 실패할 수 있으므로, 기본 Python을 재현 환경으로 쓰면 안 된다.

| 항목 | 값 |
|---|---|
| controlled Python | `Datasets/envs/kiise-vlmdb/bin/python` |
| Python version | `3.10.20` |
| dataset logical root | `Datasets` |
| dataset physical root | `/hdd2/KIISE_datasociety/Datasets` |
| free space | 약 2.39 TiB |
| GPU | NVIDIA GeForce RTX 3090 24GB x 2 |
| driver | 580.126.09 |
| CPU | Intel Core i7-9700K, 8 cores |
| memory | 62 GiB |

주요 import 기준 package version:

| Package | Version |
|---|---|
| numpy | 2.2.6 |
| pandas | 2.3.3 |
| pyarrow | 24.0.0 |
| torch | 2.12.1+cu130 |
| transformers | 5.13.0 |
| sentence-transformers | 5.6.0 |
| faiss | 1.14.3 |
| psycopg | 3.3.4 |
| OpenCV/cv2 | 5.0.0 |
| Pillow | 12.3.0 |

논문 표현 기준:

- “실험은 `Datasets/envs/kiise-vlmdb` conda 환경에서 수행하였다.”
- “대용량 데이터는 `/hdd2/KIISE_datasociety/Datasets`에 저장하고 프로젝트에서는 `Datasets` symlink를 사용하였다.”
- “base Python 환경은 재현 환경이 아니다.”

## 2. 사용자 설정 통제 요인

### 고정된 설정

| 설정 | 값 | 상태 |
|---|---|---|
| retrieval top-k | 1, 5, 10, 20 | 고정 |
| max rank | 100 | 고정 |
| RRF k | 60 | 고정 |
| weighted RRF sweep | 4:1, 3:1, 2:1, 1:1, 1:2, 1:3, 1:4 | 완료 |
| VRU keyframe strategy | uniform, 4 frames/clip | 고정 |
| AI Hub keyframe strategy | event-centered, 4 frames/clip | 고정 |
| image-to-video main frame | `query_frame_seq=2` | 본문 기준 |
| frame budget ablation | K=1 seq2, K=2 seq1/2, K=4 all | 완료 |

### 추가 수행한 frame position sensitivity

IM1의 본문 결과는 `query_frame_seq=2` 기준이다. 이 설정이 임의 선택처럼 보일 수 있으므로, 같은 CLIP visual embedding에서 frame position 0, 1, 2, 3을 비교했다.

| Dataset | query frame seq | Queries | R@1 | R@5 | R@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| VRU | 0 | 1,000 | 0.5960 | 0.8630 | 0.9020 | 0.7203 | 0.7630 |
| VRU | 1 | 1,000 | 0.7320 | 0.9640 | 0.9810 | 0.8404 | 0.8755 |
| VRU | 2 | 1,000 | 0.7550 | 0.9660 | 0.9800 | 0.8567 | 0.8875 |
| VRU | 3 | 1,000 | 0.7330 | 0.9540 | 0.9680 | 0.8370 | 0.8694 |
| AI Hub CCTV | 0 | 269 | 0.8550 | 0.9814 | 0.9963 | 0.9122 | 0.9330 |
| AI Hub CCTV | 1 | 269 | 0.8476 | 0.9888 | 0.9963 | 0.9072 | 0.9295 |
| AI Hub CCTV | 2 | 269 | 0.8810 | 0.9851 | 1.0000 | 0.9258 | 0.9442 |
| AI Hub CCTV | 3 | 269 | 0.6952 | 0.8216 | 0.8327 | 0.7462 | 0.7673 |

해석:

1. VRU는 중간 이후 프레임인 seq 1/2/3에서 R@10 0.9680~0.9810으로 안정적이다. seq 0은 사고 맥락이 덜 나타날 가능성이 있어 낮다.
2. AI Hub는 event-centered extraction이므로 seq 0/1/2는 매우 높지만 seq 3은 낮다. 이는 event segment의 후반 프레임이 사건의 대표 장면이 아닐 수 있음을 의미한다.
3. 따라서 본문 IM1 결과는 “qseq2 기준 image-to-video service function”으로 명시하고, frame position 의존성은 보조 통제 결과로 보고하는 것이 안전하다.

## 3. 데이터셋 적합성 및 무결성

감사 스크립트는 canonical schema, qrels, metadata filter, keyframe, embedding shape/count를 확인했다.

| Dataset | Role | Clips | Docs | Metadata | Queries | Qrels | Keyframes | Frame errors | Qrel target errors | Metadata filter errors |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| VRU-Accident | main true multimodal 1 | 1,000 | 7,000 | 6,000 | 244 | 5,488 | 4,000 | 0 | 0 | 0 |
| AI Hub 지능형 CCTV | main true multimodal 2 | 269 | 807 | 2,563 | 133 | 1,358 | 1,076 | 0 | 0 | 0 |
| AI Hub 이상행동 CCTV | supplementary text/metadata baseline | 1,968 | 5,904 | 33,456 | 424 | 21,639 | NA | NA | 0 | 0 |

metadata filter selectivity:

| Dataset | Metadata-filtered queries | Min candidates | Median candidates | Max candidates | Zero candidate queries |
|---|---:|---:|---:|---:|---:|
| VRU-Accident | 205 | 2 | 111.0 | 873 | 0 |
| AI Hub 지능형 CCTV | 111 | 2 | 8.0 | 152 | 0 |
| AI Hub 이상행동 CCTV | 397 | 3 | 193.0 | 1872 | 0 |

해석:

- qrels target이 canonical clips에 없는 오류는 없다.
- query의 `positive_count`와 qrels 수가 불일치하는 경우는 없다.
- metadata filter가 0개 후보를 만드는 질의는 없다.
- metadata filter 후보 밖에 qrels positive가 존재하는 오류도 없다.
- 따라서 현재 canonical workload는 실험 가능 상태다.

## 4. 모델 다양성 및 호환성

| Dataset | BGE-M3 shape ok | E5 shape ok | CLIP shape ok | SigLIP shape ok | Visual dims |
|---|---:|---:|---:|---:|---|
| VRU-Accident | True | True | True | True | CLIP 512, SigLIP 768 |
| AI Hub 지능형 CCTV | True | True | True | True | CLIP 512, SigLIP 768 |

모델 cache 상태:

| Model | 상태 |
|---|---|
| `openai/clip-vit-base-patch32` | cache exists |
| `google/siglip-base-patch16-224` | cache exists |
| `BAAI/bge-m3` | local/cache exists |
| `intfloat/e5-large-v2` | local/cache exists |

판정:

- text embedding 다양성은 BGE-M3와 E5-large-v2로 방어 가능하다.
- visual-text embedding은 CLIP과 SigLIP ablation으로 보강했다.
- 다만 둘 다 frame-level image-text encoder이므로, video-native temporal encoder 부재는 한계로 명시한다.

## 5. 최종 추가 실험 판단

### 최신 기준에서 본문에 반영된 것

| 후보 | 최신 판단 |
|---|---|
| 새 데이터셋 | 확보 데이터셋을 계층형으로 반영한다. VRU/AI Hub 지능형 CCTV는 anchor, AI Hub 다각도 CCTV는 answer-level view-selection, 시내도로 CCTV는 visual vector index benchmark로 사용한다. |
| 추가 visual encoder | CLIP/SigLIP ablation은 retrieval 강건성으로 반영한다. video-native temporal encoder는 후속 과제로 둔다. |
| HNSW/IVFFlat | 시내도로 CCTV 기반 index benchmark로 반영한다. 다만 end-to-end VLM-QA latency가 아니라 search-layer index trade-off로 해석한다. |
| controlled LLM answer generation | Qwen2.5-7B와 Llama-3-8B를 고정한 answer-level evidence-control 실험으로 반영한다. |
| controlled VLM answer generation | Qwen2.5-VL, Qwen2-VL, InternVL3-8B, Idefics2-8b를 고정한 다각도 view-selection 실험으로 반영한다. |

### 이미 수행했거나 본문 방어에 반영할 것

| 항목 | 상태 | 원고 반영 방식 |
|---|---|---|
| pipeline audit | 완료 | 필수 파일 누락 0 |
| control factor audit | 완료 | 재현 환경, dataset/model/user setting 통제 문서화 |
| RRF weight sweep | 완료 | evidence selection 결과 표에 반영 |
| image frame-position sensitivity | 완료 | IM1 보조 통제 결과로 반영 |
| SigLIP visual encoder ablation | 완료 | 표 11에 반영 |
| frame budget ablation | 완료 | 표 12에 반영 |
| visual model diversity gap | 부분 해소 | CLIP/SigLIP는 반영, video-native temporal encoder는 한계로 명시 |
| fixed LLM answer control | 완료 | closed-book/vector/prefilter/oracle evidence 조건 비교로 반영 |
| fixed VLM multi-view answer control | 완료 | better-view, worse-view, both-view 조건 비교로 반영 |
| visual vector index benchmark | 완료 | Flat/IVF-Flat/HNSW/IVF-PQ와 filtered ANN trade-off로 반영 |

## 6. 원고에 넣어야 할 문장

방법/환경:

> 모든 실험은 `Datasets/envs/kiise-vlmdb` conda 환경에서 수행하였으며, 시스템 기본 Python 환경은 재현 환경으로 사용하지 않았다.

IM1 결과:

> IM1의 본문 결과는 `query_frame_seq=2`를 이미지 질의로 사용한 기준이며, 질의 프레임 자신은 후보에서 제외하였다. 추가 frame-position sensitivity에서는 VRU가 seq 1/2/3에서 R@10 0.9680~0.9810으로 안정적이었고, AI Hub CCTV는 event-centered 추출 특성상 seq 3에서 성능이 하락하였다.

한계:

> 시각-텍스트 임베딩은 CLIP ViT-B/32와 SigLIP base p16-224를 비교했지만, video-native temporal encoder와 최신 대형 VLM embedding까지 포함하지는 못했다.

## 7. 최종 답변

새 대형 데이터셋은 이제 모두 연구에 반영한다. 다만 기존 VRU/AI Hub 지능형 CCTV full-pipeline 결과를 anchor로 두고, AI Hub 다각도 CCTV는 fixed VLM view-selection, 시내도로 CCTV는 visual vector index benchmark, CityFlow-NL·교차로신호체계·이상행동 CCTV는 데이터셋 특성에 맞는 sample/extension/system-evidence 실험으로 편입한다. HNSW/IVF 계열과 controlled LLM/VLM answer generation은 최신 기준에서 완료되었으며, 해석은 각각 search-layer index trade-off와 fixed-model evidence-control 효과로 제한한다.
