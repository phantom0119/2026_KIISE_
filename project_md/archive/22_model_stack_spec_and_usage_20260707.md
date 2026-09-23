# 실험 사용 모델 명세 및 사용 범위

작성 기준일: 2026-07-07

2026-07-09 최신 갱신: 이 문서의 2026-07-07 결론은 retrieval-only 단계 기준이다. 최신 원고에서는 검색 실험 자체에는 생성 모델을 사용하지 않지만, 6.8절 LLM answer layer와 6.13절 다각도 answer-level VLM 통제 실험에서는 생성 모델을 **고정된 평가 도구**로 사용한다. 따라서 모델 사용 범위는 `embedding/indexing layer`와 `fixed answer-level control layer`로 구분해 설명해야 한다. 최신 종합은 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 결론

본 연구 실험에서 실제로 사용한 모델은 분명히 존재한다. 다만 **검색 실험 자체**에는 LLM 생성 모델이나 VLM 답변 생성/비전 추론 모델을 사용하지 않았다. 이후 answer-level 통제 실험에서는 생성 모델을 고정하고 DB evidence 구성만 바꾸어 답변 정확도 변화를 측정했다.

정확한 표현은 다음과 같다.

- retrieval/indexing layer에서 사용함: visual-text embedding model, text embedding model
- answer-level control layer에서 사용함: 고정 LLM/VLM answer generator
- 사용하지 않음: object detector, video-native temporal reasoning model, 학습/파인튜닝된 새 VLM

따라서 논문에서는 “새 LLM/VLM을 제안했다” 또는 “VLM이 CCTV 사건을 일반적으로 잘 추론했다”고 쓰면 안 된다. 본 연구의 모델 사용은 DB 검색 구조 평가를 위한 embedding/indexing layer와, DB evidence 구성 차이를 측정하기 위한 fixed answer-level control layer로 제한된다.

## 실제 사용 모델

| 역할 | 모델 | 실제 사용 여부 | 산출물 |
|---|---|---:|---|
| 시각-텍스트 임베딩 | `openai/clip-vit-base-patch32` | 사용 | keyframe embedding, CLIP text query embedding |
| 시각-텍스트 robustness 임베딩 | `google/siglip-base-patch16-224` | 사용 | visual encoder ablation, image query robustness |
| 주 텍스트 임베딩 | `BAAI/bge-m3` | 사용 | text evidence/document/query embedding |
| robustness 텍스트 임베딩 | `intfloat/e5-large-v2` | 사용 | text baseline robustness |
| LLM 답변 생성 | `Qwen2.5-7B-Instruct`, `Meta-Llama-3-8B-Instruct` | 사용 | VRU VQA evidence 구성별 answer accuracy 통제 실험 |
| VLM 답변 생성 | `Qwen2.5-VL-7B-Instruct`, `Qwen2-VL-7B-Instruct`, `InternVL3-8B`, `Idefics2-8b` | 사용 | AI Hub 다각도 CCTV view evidence 통제 실험. Idefics2는 near-chance 보조 근거 |

## 모델 다양성 및 호환성 감사

2026-07-07 추가 통제 감사 결과는 `2026_KIISE/paper_assets/20260707_control_factor_audit/summary.md`와 `2026_KIISE/project_md/26_control_factors_and_additional_experiment_decision_20260707.md`에 기록했다.

| 항목 | 판단 |
|---|---|
| text embedding 다양성 | `BAAI/bge-m3`와 `intfloat/e5-large-v2`를 모두 사용했으므로 기본 robustness는 확보 |
| visual-text embedding 다양성 | `openai/clip-vit-base-patch32`와 `google/siglip-base-patch16-224` ablation 수행 |
| SigLIP cache | `Datasets/models/huggingface/models--google--siglip-base-patch16-224`에 구축 완료 |
| BGE/E5/CLIP/SigLIP shape compatibility | 감사 결과 shape/count mismatch 없음 |
| LLM/VLM generation | 검색 실험에는 미사용. answer-level 통제 실험에는 고정 모델로 사용 |

결론: visual-text encoder가 CLIP 단일 모델이라는 약점은 SigLIP ablation으로 보강했다. answer-level은 Qwen2.5/Llama, Qwen2.5-VL/Qwen2-VL/InternVL3/Idefics2로 보강했지만, 모델 성능 비교 논문이 아니므로 결론은 fixed-model paired delta와 DB evidence 구성 효과에 한정한다. frame-level image-text encoder 중심이므로 video-native temporal encoder까지 비교한 것은 아니다.

## CLIP visual-text embedding model

| 항목 | 값 |
|---|---|
| model id | `openai/clip-vit-base-patch32` |
| local cache root | `/hdd2/huggingface_cache/hub/models--openai--clip-vit-base-patch32` |
| main revision | `3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268` |
| config | `/hdd2/huggingface_cache/hub/models--openai--clip-vit-base-patch32/snapshots/3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268/config.json` |
| weight file | `/hdd2/huggingface_cache/hub/models--openai--clip-vit-base-patch32/snapshots/3d74acf9a28c67741b2f4f2ea7635f0aaf6f0268/pytorch_model.bin` |
| weight size | 605,247,071 bytes |
| model type | `clip` |
| projection dim | 512 |
| vision encoder | ViT, hidden 768, 12 layers, 12 heads |
| patch/image size | patch 32, image 224 |
| text encoder | hidden 512, 12 layers, 8 heads |
| max text positions | 77 |
| vocab size | 49,408 |
| output normalization | enabled |

실험 사용 방식:

- 영상 mp4에서 keyframe을 추출한다.
- CLIP image encoder로 keyframe embedding을 만든다.
- text-to-video 실험에서는 CLIP text encoder로 질의 텍스트 embedding을 만든다.
- image-to-video 실험에서는 held-out keyframe embedding을 이미지 질의로 사용한다.
- cosine similarity에 해당하는 normalized inner product로 frame ranking을 만든다.

중요한 한계:

- CLIP은 본 실험에서 generative VLM이 아니다.
- CLIP은 답변을 생성하지 않는다.
- CLIP은 객체 탐지나 시간적 사건 추론을 직접 수행하지 않는다.
- 본 실험의 “visual reasoning”은 엄밀히 말하면 visual-text embedding retrieval이다.

## SigLIP visual-text robustness embedding model

| 항목 | 값 |
|---|---|
| model id | `google/siglip-base-patch16-224` |
| local cache root | `Datasets/models/huggingface/models--google--siglip-base-patch16-224` |
| main revision | `7fd15f0689c79d79e38b1c2e2e2370a7bf2761ed` |
| config | `Datasets/models/huggingface/models--google--siglip-base-patch16-224/snapshots/7fd15f0689c79d79e38b1c2e2e2370a7bf2761ed/config.json` |
| weight file | `Datasets/models/huggingface/models--google--siglip-base-patch16-224/snapshots/7fd15f0689c79d79e38b1c2e2e2370a7bf2761ed/model.safetensors` |
| weight size | 812,672,320 bytes |
| model type | `siglip` |
| embedding dim in artifacts | 768 |
| vision patch size | 16 |
| text hidden size | 768 |
| text attention heads | 12 |
| vocab size | 32,000 |
| output normalization | enabled |

실험 사용 방식:

- CLIP과 동일한 keyframe, query, qrels에서 visual encoder ablation을 수행한다.
- M2/M4 visual retrieval, M5/M6 fusion, IM1 image-to-video, weighted RRF sweep을 재실행한다.
- 생성형 VLM 또는 비전 추론 모델로 사용하지 않고 embedding model로만 사용한다.

## BGE-M3 text embedding model

| 항목 | 값 |
|---|---|
| model id | `BAAI/bge-m3` |
| local path | `Datasets/models/huggingface/BAAI--bge-m3` |
| config | `Datasets/models/huggingface/BAAI--bge-m3/config.json` |
| weight file | `Datasets/models/huggingface/BAAI--bge-m3/pytorch_model.bin` |
| weight size | 2,271,145,830 bytes |
| model type | `xlm-roberta` |
| hidden size | 1024 |
| layers | 24 |
| attention heads | 16 |
| max positions | 8194 |
| vocab size | 250,002 |
| embedding dim in artifacts | 1024 |
| output normalization | enabled |

실험 사용 방식:

- caption, VQA, event text 등 text evidence document embedding 생성
- 자연어 query embedding 생성
- FAISS exact inner product search 및 pgvector 보강 실험에 사용
- B0-B5 text/metadata baseline의 주 dense encoder

## E5-large-v2 text embedding model

| 항목 | 값 |
|---|---|
| model id | `intfloat/e5-large-v2` |
| local path | `Datasets/models/huggingface/intfloat--e5-large-v2` |
| config | `Datasets/models/huggingface/intfloat--e5-large-v2/config.json` |
| weight file | `Datasets/models/huggingface/intfloat--e5-large-v2/model.safetensors` |
| weight size | 1,340,616,616 bytes |
| model type | `bert` |
| hidden size | 1024 |
| layers | 24 |
| attention heads | 16 |
| max positions | 512 |
| vocab size | 30,522 |
| embedding dim in artifacts | 1024 |
| output normalization | enabled |

실험 사용 방식:

- BGE-M3 결과가 특정 모델에만 의존하지 않는지 확인하는 robustness baseline
- VRU, AI Hub 지능형 CCTV, AI Hub 이상행동 CCTV text/metadata baseline에 사용

## Fixed LLM/VLM answer-level control models

| 역할 | 모델 | 산출물 |
|---|---|---|
| VRU VQA answer layer | `Qwen2.5-7B-Instruct` | `2026_KIISE/experiments_expansion/rag_vqa/results_full` |
| VRU VQA answer layer | `Meta-Llama-3-8B-Instruct` | `2026_KIISE/experiments_expansion/rag_vqa/results_full` |
| 다각도 CCTV primary VLM | `Qwen2.5-VL-7B-Instruct` | `Datasets/processed/aihub_multi_angle_cctv/20260708/results/multiview_answer_vlm_qwen25vl_400` |
| 다각도 CCTV robustness VLM | `Qwen2-VL-7B-Instruct` | `Datasets/processed/aihub_multi_angle_cctv/20260708/results/multiview_answer_vlm_qwen2vl_400` |
| 다각도 CCTV cross-vision VLM | `InternVL3-8B` | `Datasets/processed/aihub_multi_angle_cctv/20260708/results/multiview_answer_vlm_internvl3_400` |
| 다각도 CCTV LLM-family 보조 VLM | `Idefics2-8b` | `Datasets/processed/aihub_multi_angle_cctv/20260708/results/multiview_answer_vlm_idefics2_400` |

사용 원칙:

- temperature=0, greedy decoding, 동일 prompt/hash, 동일 evidence packet 조건을 유지한다.
- 모델 간 절대 정확도 비교가 목적이 아니라, 같은 모델 내부에서 DB evidence 조건만 바꾼 paired delta를 측정한다.
- Idefics2는 near-chance이므로 강한 주 결과가 아니라 보조 근거로만 둔다.

## 데이터셋별 실제 모델 산출물

### VRU-Accident

| 모델 | 산출물 경로 | 개수/차원 |
|---|---|---|
| CLIP ViT-B/32 | `Datasets/processed/vru_accident/20260706/visual_embeddings/clip-vit-base-patch32_full` | frames 4,000 / queries 244 / dim 512 |
| SigLIP base p16-224 | `Datasets/processed/vru_accident/20260706/visual_embeddings/siglip-base-patch16-224_full` | frames 4,000 / queries 244 / dim 768 |
| BGE-M3 | `Datasets/processed/vru_accident/20260706/embeddings/bge-m3` | documents 7,000 / queries 244 / dim 1024 |
| E5-large-v2 | `Datasets/processed/vru_accident/20260706/embeddings/e5-large-v2` | documents 7,000 / queries 244 / dim 1024 |

### AI Hub 지능형 CCTV

| 모델 | 산출물 경로 | 개수/차원 |
|---|---|---|
| CLIP ViT-B/32 | `Datasets/processed/aihub_intelligent_cctv/20260706/visual_embeddings/clip-vit-base-patch32_full` | frames 1,076 / queries 133 / dim 512 |
| SigLIP base p16-224 | `Datasets/processed/aihub_intelligent_cctv/20260706/visual_embeddings/siglip-base-patch16-224_full` | frames 1,076 / queries 133 / dim 768 |
| BGE-M3 | `Datasets/processed/aihub_intelligent_cctv/20260706/embeddings/bge-m3` | documents 807 / queries 133 / dim 1024 |
| E5-large-v2 | `Datasets/processed/aihub_intelligent_cctv/20260706/embeddings/e5-large-v2` | documents 807 / queries 133 / dim 1024 |

### AI Hub 이상행동 CCTV

| 모델 | 산출물 경로 | 개수/차원 |
|---|---|---|
| BGE-M3 | `Datasets/processed/aihub_abnormal_cctv/20260707/embeddings/bge-m3` | text/metadata baseline |
| E5-large-v2 | `Datasets/processed/aihub_abnormal_cctv/20260707/embeddings/e5-large-v2` | text/metadata baseline |

AI Hub 이상행동 CCTV는 zip 내부 mp4를 직접 visual embedding으로 처리하지 않았으므로, 현재 true multimodal main result에는 포함하지 않는다.

## 실행 환경

| 항목 | 값 |
|---|---|
| conda env | `Datasets/envs/kiise-vlmdb` |
| torch | `2.12.1+cu130` |
| transformers | `5.13.0` |
| sentence-transformers | `5.6.0` |
| FAISS | `1.14.3` |
| OpenCV | `5.0.0` |
| numpy | `2.2.6` |
| pandas | `2.3.3` |
| CLIP/SigLIP device | CUDA |
| text embedding device | CUDA |

## 논문 표현 가이드

사용 가능한 표현:

- "CLIP과 SigLIP visual-text embedding을 이용해 keyframe과 text/image query를 동일 벡터 공간에 매핑하고 visual encoder ablation을 수행하였다."
- "BGE-M3와 E5-large-v2를 text evidence retrieval baseline으로 사용하였다."
- "검색 실험에는 LLM/VLM generation을 사용하지 않았고, answer-level 통제 실험에서는 생성 모델을 고정한 채 DB evidence 구성만 변경하였다."
- "검색 결과는 clip ID뿐 아니라 evidence frame, timestamp, thumbnail path를 반환한다."

피해야 하는 표현:

- "LLM이 CCTV 영상을 이해하였다."
- "VLM이 사건을 일반적으로 잘 추론하였다."
- "비전 추론 모델을 통해 temporal reasoning을 수행하였다."
- "CLIP이 답변을 생성하였다."

## 현재 모델 관련 결론

본 연구에서 사용한 모델은 존재하고, 산출물 manifest와 로컬 weight/config 파일로 검증된다. 다만 모델 역할은 다음처럼 제한해 설명해야 한다.

> 본 연구는 새 LLM/VLM 생성 능력을 평가한 것이 아니라, 시각 프레임 임베딩, 텍스트 evidence 임베딩, 구조화 metadata를 데이터베이스 검색·선택 구조로 결합했을 때의 retrieval 성능, evidence 반환 가능성, 그리고 고정 생성 모델 조건에서의 answer-level evidence 효과를 평가한 연구다.
