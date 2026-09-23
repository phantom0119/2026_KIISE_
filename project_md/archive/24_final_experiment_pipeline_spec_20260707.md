# 최종 실험 파이프라인 통합 사양

작성 기준일: 2026-07-07

2026-07-08 갱신 메모: 이후 `Datasets/external`에 시내도로 교통 CCTV, 교차로신호체계, CityFlow-NL raw zip 등 대형 멀티모달 데이터셋이 추가 확보되었다. 따라서 본 문서의 "새 대형 데이터셋은 이번 투고 본문에 추가하지 않는다"는 동결 판단은 최신 상태가 아니다. 새 데이터셋을 모두 연구에 반영하는 계층형 설계는 `30_all_acquired_dataset_research_design_20260708.md`를 우선 기준으로 한다. 단, 아래에 기록된 VRU/AI Hub 지능형 CCTV full-pipeline 결과는 계속 anchor result로 사용한다.

2026-07-09 최신 갱신: 데이터셋 구축은 canonical schema와 retrieval pipeline을 넘어, AI Hub 다각도 CCTV의 answer-level VLM view-selection 실험과 시내도로 CCTV 기반 index structure benchmark까지 확장되었다. 최신 종합 판정은 `40_latest_dataset_and_experiment_synthesis_20260709.md`, 다각도 최종 재검증은 `38_four_vlm_multiview_final_recheck_20260709.md`, 색인 구조 결과는 `39_index_structure_benchmark_results_20260709.md`를 우선 기준으로 한다. 본 문서의 VRU/AI Hub 지능형 CCTV 결과는 anchor full-pipeline 결과로 유지하되, "LLM/VLM 생성 모델 미사용"은 검색 실험에만 해당한다. 6.8·6.13절 answer-level 통제 실험에서는 생성 모델을 고정하고 DB evidence 구성만 바꾸는 방식으로 LLM/VLM을 사용한다.

## 최종 연구 목적

본 연구의 목적은 도시 교통·감시형 멀티모달 데이터베이스에서 AI 응답 품질을 높이기 위해, 데이터베이스 수준의 evidence retrieval 및 selection 구조가 어떤 역할을 하는지 실험적으로 분석하는 것이다.

본 연구는 LLM이나 VLM 생성 모델의 성능 비교 논문이 아니다. 핵심은 다음 질문이다.

> 대량 멀티모달 도시 감시 데이터에서 시각 프레임, 텍스트 evidence, 구조화 metadata를 어떤 저장·색인·검색·선택 구조로 결합해야 answer-ready evidence의 정확도와 근거 충실도를 높일 수 있는가?

## 최종 연구 질문

| ID | 연구 질문 |
|---|---|
| RQ1 | text-to-video visual retrieval에서 metadata prefilter는 visual vector-only 검색보다 관련 evidence clip/frame을 더 안정적으로 찾는가? |
| RQ2 | text evidence rank와 visual frame rank를 결합한 M6 구조는 단일 modality 검색보다 service-level evidence 반환에 유리한가? |
| RQ3 | image-to-video 검색은 실제 스크린샷/증거 이미지 기반 CCTV 검색 기능으로 동작 가능한가? |
| RQ4 | top-k retrieval 성능과 rank-1 answer evidence 품질은 어떻게 다른가? |
| RQ5 | LLM을 추가하지 않고도 DB/query-planning 수준의 evidence selection으로 answer quality proxy를 개선할 수 있는가? |
| RQ6 | 생성 모델을 고정하고 DB evidence 구성만 바꾸면 LLM/VLM 답변 정확도가 달라지는가? |
| RQ7 | 도시 감시 visual vector corpus에서 Flat, IVF, HNSW, IVF-PQ는 정확도·지연·비용을 어떻게 trade-off하는가? |

## 데이터셋 최종 사용 범위

| 데이터셋 | 역할 | true multimodal 사용 여부 | 이유 |
|---|---|---:|---|
| VRU-Accident | 주 실험 1 | 예 | 1,000개 mp4, dense caption/VQA/metadata/qrels, 도시 교통 안전 사고 장면 |
| AI Hub 지능형 관제 서비스 CCTV 영상 | 주 실험 2 | 예 | 269개 실제 CCTV mp4, event caption, event frame range, 국내 CCTV 성격 |
| AI Hub 다각도 CCTV 생활안전 | 주 실험 3 | 부분 | 4,500 event, c1/c2 view, VQA/CoT/evidence frame/bbox. answer-level view-selection 핵심 |
| 시내도로 CCTV | 색인 구조 실험 | 예 | real 132,521 CLIP vectors + synthetic 1M scale ANN benchmark |
| AI Hub 이상행동 CCTV | 보조 baseline | 아니오 | zip 내부 mp4와 XML 라벨은 확보했으나, 현재 true visual embedding main track에는 미포함 |

주의:

- AI Hub 이상행동 CCTV는 text/metadata baseline 보강에는 사용했지만, 본 논문의 true multimodal main result에는 넣지 않는다.
- VRU는 고정 CCTV가 아니라 대시캠/교통 안전 영상 성격이므로, "도시 교통·감시형 영상"으로 보수적으로 표현한다.

## 저장 경로

| 항목 | 경로 |
|---|---|
| 논리 데이터 루트 | `Datasets` |
| 물리 데이터 루트 | `/hdd2/KIISE_datasociety/Datasets` |
| VRU canonical | `Datasets/processed/vru_accident/20260706/canonical` |
| AI Hub CCTV canonical | `Datasets/processed/aihub_intelligent_cctv/20260706/canonical` |
| AI Hub 다각도 CCTV canonical | `Datasets/processed/aihub_multi_angle_cctv/20260708/canonical` |
| AI Hub 다각도 CCTV stratum frames | `Datasets/processed/aihub_multi_angle_cctv/20260708/keyframes/stratum_bbox_asymmetry_400` |
| 시내도로 index corpus | `Datasets/processed/sinnaedoro_traffic/{corpus_real,corpus_aug_1m.npy,index_benchmark}` |
| VRU keyframes | `Datasets/processed/vru_accident/20260706/keyframes/clip4_full` |
| AI Hub CCTV keyframes | `Datasets/processed/aihub_intelligent_cctv/20260706/keyframes/event4_full` |

## 데이터 규모

| Dataset | Clips | Keyframes | Frame errors | Text queries | Image queries |
|---|---:|---:|---:|---:|---:|
| VRU-Accident | 1,000 | 4,000 | 0 | 244 | 1,000 |
| AI Hub CCTV | 269 | 1,076 | 0 | 133 | 269 |
| AI Hub 다각도 CCTV stratum | 400 | 2,400 | 0 | 400 answer tasks x 4 conditions | 해당 없음 |
| 시내도로 CCTV index corpus | frame vectors 132,521 real | 해당 없음 | 해당 없음 | 1,000 held-out vector queries | 해당 없음 |

## 모델 최종 사양

상세 weight/config 경로는 `22_model_stack_spec_and_usage_20260707.md`에 고정한다.

| 역할 | 모델 | 사용 범위 | 차원 |
|---|---|---|---:|
| visual-text embedding | `openai/clip-vit-base-patch32` | keyframe image embedding, text query CLIP embedding, image query embedding | 512 |
| visual-text robustness embedding | `google/siglip-base-patch16-224` | visual encoder ablation, image query robustness | 768 |
| text evidence embedding | `BAAI/bge-m3` | 주 text/metadata retrieval baseline | 1024 |
| text robustness embedding | `intfloat/e5-large-v2` | text baseline robustness | 1024 |
| answer-generation LLM | `Qwen2.5-7B-Instruct`, `Meta-Llama-3-8B-Instruct` | 6.8절 evidence 구성별 답변 정확도 통제 실험 | 해당 없음 |
| answer-level VLM | `Qwen2.5-VL-7B-Instruct`, `Qwen2-VL-7B-Instruct`, `InternVL3-8B`, `Idefics2-8b` | 6.13절 다각도 view evidence 통제 실험. Idefics2는 near-chance 보조 근거 | 해당 없음 |

정확한 표현:

- "CLIP과 SigLIP visual-text embedding을 사용하였다."
- "BGE-M3/E5-large-v2를 text evidence embedding baseline으로 사용하였다."
- "검색 실험 자체에는 생성 모델을 사용하지 않았고, answer-level 통제 실험에서는 생성 모델을 고정한 채 DB evidence 구성만 변경하였다."

피해야 할 표현:

- "LLM이 영상을 이해했다."
- "VLM이 CCTV 사건을 일반적으로 잘 추론했다."
- "비전 추론 모델로 temporal reasoning을 수행했다."

## 최종 파이프라인

```text
raw mp4
  -> canonical clip/document/metadata/query/qrels
  -> keyframe extraction
  -> CLIP/SigLIP visual frame embedding
  -> CLIP/SigLIP text query embedding
  -> BGE-M3/E5 text evidence embedding
  -> retrieval baselines
       B0-B5 text/metadata
       M2/M4 visual text-to-video
       M5/M6 text+visual fusion
       IM1 image-to-video
  -> service-level evidence packet
  -> weighted evidence reranking
  -> answer-ready evidence context
  -> fixed LLM/VLM answer-level control
  -> index structure benchmark for visual vector corpus
```

## 스크립트 사양

| 단계 | 스크립트 | 산출물 |
|---|---|---|
| text embedding | `build_text_embeddings.py` | `embeddings/{bge-m3,e5-large-v2}` |
| B0-B5 baseline | `run_retrieval_baselines.py` | `results/*_faiss_b0_b5` |
| pgvector 보강 | `run_pgvector_retrieval.py` | `results/vru_bgem3_pgvector_p2_p4` |
| keyframe extraction | `extract_keyframes.py` | `keyframes/*_full` |
| CLIP/SigLIP visual embedding | `build_visual_embeddings.py` | `visual_embeddings/{clip-vit-base-patch32,siglip-base-patch16-224}_full` |
| M2/M4 visual retrieval | `run_visual_retrieval_baselines.py` | `results/visual_clip_full_m2_m4` |
| M5/M6 fusion | `run_multimodal_fusion_baselines.py` | `results/multimodal_fusion_clip_bgem3_m5_m6` |
| IM1 image-to-video | `run_image_to_video_retrieval.py` | `results/image_to_video_clip_full` |
| frame budget subset | `make_visual_embedding_frame_subsets.py` | `visual_embeddings/clip-vit-base-patch32_k*` |
| advanced ablation summary | `summarize_advanced_ablation_results.py` | `paper_assets/20260707_advanced_ablation` |
| event grounding | `evaluate_event_frame_grounding.py` | `results/event_grounding_*` |
| qualitative examples | `export_multimodal_qualitative_examples.py` | `paper_assets/20260707_true_multimodal_examples` |
| service packet | `build_service_testbed_packets.py` | `service_testbed/*_top5` |
| weighted rerank | `run_weighted_fusion_rerank_sweep.py` | `results/weighted_fusion_rerank_sweep_bgem3_clip` |
| LLM answer layer | `run_rag_vqa.py` | `experiments_expansion/rag_vqa/results_full` |
| 다각도 stratum | `build_bbox_asymmetry_stratum.py` | `samples/bbox_asymmetry_stratum` |
| 다각도 VLM answer | `run_multiview_answer_vlm.py`, `eval_multiview_answer_vlm.py` | `results/multiview_answer_vlm_*_400` |
| 시내도로 visual corpus | `build_sinnaedoro_visual.py` | `Datasets/processed/sinnaedoro_traffic/corpus_real` |
| 색인 구조 benchmark | `run_index_structure_benchmark.py` | `Datasets/processed/sinnaedoro_traffic/index_benchmark` |
| pipeline audit | `audit_true_multimodal_pipeline.py` | `paper_assets/20260707_pipeline_audit` |
| control factor audit | `audit_experiment_control_factors.py` | `paper_assets/20260707_control_factor_audit` |

## 검색 전략 정의

| ID | 전략 | 설명 | 원고 역할 |
|---|---|---|---|
| B0 | metadata-only | 구조화 metadata 조건만 사용 | baseline |
| B1 | BM25-only | text evidence sparse retrieval | baseline |
| B2 | dense vector-only | BGE/E5 text vector retrieval | baseline |
| B3 | vector postfilter | dense ranking 후 metadata filter | baseline |
| B4 | metadata prefilter + dense | metadata 후보 내 text vector ranking | baseline |
| B5 | text hybrid | BM25+dense+metadata | text/metadata strong baseline |
| M2 | visual vector-only | CLIP text query로 frame index 검색 | true multimodal baseline |
| M4 | metadata prefilter + visual | metadata 후보 내 visual frame ranking | main visual result |
| M5 | text+visual RRF | text dense + visual rank fusion | multimodal fusion |
| M6 | text+visual+metadata RRF | metadata-aware text/visual fusion | service-level base strategy |
| IM1 | image-to-video | held-out keyframe image query로 video 검색 | image query track |
| RW_t4_v1 | weighted rerank | B5 text rank와 M4 visual rank를 4:1 RRF 결합 | answer evidence selection |

## 핵심 결과

### Visual text-to-video

| Dataset | M2 R@10 | M2 nDCG@10 | M4 R@10 | M4 nDCG@10 |
|---|---:|---:|---:|---:|
| VRU | 0.0616 | 0.0883 | 0.2467 | 0.2452 |
| AI Hub CCTV | 0.1000 | 0.1331 | 0.7524 | 0.7437 |

해석: metadata prefilter는 visual retrieval에서도 vector-only보다 관련 evidence를 더 잘 찾는다.

### Text+visual+metadata fusion

| Dataset | M6 R@10 | M6 R@20 | M6 MRR | M6 nDCG@10 |
|---|---:|---:|---:|---:|
| VRU | 0.4928 | 0.6590 | 0.7837 | 0.6232 |
| AI Hub CCTV | 0.8016 | 0.8799 | 0.9469 | 0.8951 |

해석: M6는 service-level evidence 반환의 기본 구조로 사용한다. 다만 기존 text-only B5보다 모든 경우에 항상 우수하다고 주장하지 않는다.

### Image-to-video

| Dataset | Image queries | R@1 | R@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|---:|
| VRU | 1,000 | 0.7550 | 0.9800 | 0.8567 | 0.8875 |
| AI Hub CCTV | 269 | 0.8810 | 1.0000 | 0.9258 | 0.9442 |

해석: 이미지/스크린샷 기반 원본 영상 검색 기능이 실험적으로 동작한다.

추가 사용자 설정 통제로 `query_frame_seq` 0, 1, 2, 3을 비교했다. 본문 IM1 결과는 `query_frame_seq=2` 기준이다.

| Dataset | qseq0 R@10 | qseq1 R@10 | qseq2 R@10 | qseq3 R@10 |
|---|---:|---:|---:|---:|
| VRU | 0.9020 | 0.9810 | 0.9800 | 0.9680 |
| AI Hub CCTV | 0.9963 | 0.9963 | 1.0000 | 0.8327 |

해석: VRU는 중간 이후 프레임에서 안정적이고, AI Hub CCTV는 event-centered 추출 특성상 마지막 프레임에서 성능이 낮아진다. 따라서 image-to-video 결과는 frame position을 명시하고 보조 민감도 결과와 함께 해석해야 한다.

### Service-level evidence packet

| Dataset | Equal M6 service top-1 | Equal M6 Hit@5 | Reranked service top-1 | Reranked Hit@5 | Frame coverage |
|---|---:|---:|---:|---:|---:|
| VRU | 0.7468 | 0.9486 | 0.7725 | 0.9662 | 1.0000 |
| AI Hub CCTV | 0.8955 | 0.9826 | 0.9104 | 0.9900 | 1.0000 |

해석: top-k retrieval과 answer context의 rank-1 evidence 품질은 다르다. AI 응답 품질 향상을 위해서는 retrieval 이후 evidence selection이 필요하다.

### Weighted reranking

| Dataset | Best strategy | Hit@1 | Hit@5 | nDCG@10 |
|---|---|---:|---:|---:|
| VRU | `RW_t4_v1` | 0.8443 | 0.9672 | 0.8847 |
| AI Hub CCTV | `RW_t4_v1` | 0.9699 | 1.0000 | 0.9768 |

해석: LLM을 추가하지 않아도 DB/query-planning 수준의 text/visual evidence selection이 answer quality proxy를 개선할 수 있다. 이후 answer-level 통제 실험에서는 LLM/VLM을 고정하여 evidence 품질 차이가 실제 답변 정확도로 전파되는지도 별도로 검증했다.

### Answer-level evidence control

| Evidence 구성 | Qwen2.5-7B acc | Llama-3-8B acc |
|---|---:|---:|
| closed | 0.3083 | 0.3067 |
| vector-only | 0.6650 | 0.6650 |
| prefilter | 0.6800 | 0.6667 |
| oracle | 0.7467 | 0.6900 |

해석: 답변 수준에서 prefilter와 vector-only의 차이는 작으므로 과장하지 않는다. 핵심은 evidence 품질이 높아질수록 답변 정확도가 상승한다는 점이다.

### Multi-view answer-level selection

| Model | both acc | better-worse | p | both-better |
|---|---:|---:|---:|---|
| Qwen2.5-VL | 0.2000 | +0.056 | 0.0016 | TOST equivalent |
| Qwen2-VL | 0.3025 | +0.152 | 0.0002 | TOST equivalent |
| InternVL3-8B | 0.2450 | +0.084 | 0.0002 | TOST equivalent |
| Idefics2-8b | 0.1450 | +0.044 | 0.0256 | TOST equivalent, near-chance caveat |

해석: 세 개의 강한 VLM에서 better-view가 worse-view보다 유의하게 높고 both-view는 better-view와 등가였다. 따라서 다각도 CCTV DB의 역할은 시점을 많이 쌓는 것이 아니라 더 나은 시점을 선택하는 것이다.

### Index structure benchmark

| N | Flat p50 | HNSW p50 | 해석 |
|---:|---:|---:|---|
| 10K | 0.90ms | 0.018ms | ANN 이점 시작 |
| 100K | 10.2ms | 0.043ms | HNSW 약 237배 빠름 |
| 131K real | 13.4ms | 0.041ms | real corpus 기준 crossover 명확 |
| 1M synthetic | 98.5ms | 0.061ms | Flat 선형 악화, HNSW 거의 상수 |

해석: HNSW는 높은 recall과 낮은 지연을 가장 잘 균형화하지만 build time과 memory 비용이 크다. IVF-PQ는 메모리 절감형이나 recall이 낮다. filtered ANN 실험에서는 매우 선택적인 predicate에서 post-filter recall이 붕괴하므로 metadata selectivity에 따라 pre-filter/full ANN 전략을 선택해야 한다.

## Pipeline audit

| 항목 | 값 |
|---|---:|
| audit output | `2026_KIISE/paper_assets/20260707_pipeline_audit` |
| required files | 32 |
| missing files | 0 |

## Control factor audit

| 항목 | 값 |
|---|---|
| audit output | `2026_KIISE/paper_assets/20260707_control_factor_audit` |
| controlled env | `Datasets/envs/kiise-vlmdb` |
| Python | 3.10.20 |
| GPU | NVIDIA GeForce RTX 3090 24GB x 2 |
| dataset root | `/hdd2/KIISE_datasociety/Datasets` |
| qrel target errors | 0 for all audited datasets |
| metadata filter errors | 0 for all audited datasets |
| BGE/E5/CLIP/SigLIP embedding shape check | pass |

통제 결론:

1. base Python 환경은 재현 환경이 아니며, 반드시 `Datasets/envs/kiise-vlmdb`에서 실행한다.
2. text model 다양성은 BGE-M3/E5-large-v2로 확보했다.
3. visual-text model은 CLIP과 SigLIP로 보강했지만, video-native temporal encoder는 사용하지 않았으므로 한계로 명시한다.
4. 2026-07-08 이후 확보된 새 대형 데이터셋은 `30_all_acquired_dataset_research_design_20260708.md` 기준으로 계층형 extension 실험에 반영한다.
5. 2026-07-09 기준 controlled LLM/VLM answer generation과 HNSW/IVF/IVF-PQ index benchmark는 추가 완료되었다. 최신 결과는 `38_four_vlm_multiview_final_recheck_20260709.md`, `39_index_structure_benchmark_results_20260709.md`, `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 원고 산출물

| 항목 | 경로 | 상태 |
|---|---|---|
| v1 원고 본문 | `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal.md` | true multimodal/service evidence 기준 재작성 완료 |
| DBR review Word | `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal_DBR_review.docx` | DBR 심사용 규정 반영본 |
| DBR review PDF | `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal_DBR_review.pdf` | A4 기준 확인 |
| 제출 전 preflight | `2026_KIISE/manuscript/pre_submission_preflight_20260707.md` | 최신 v1 기준 갱신 |

## 원고 작성 기준

반드시 반영:

1. B0-B5는 text/metadata baseline이다.
2. true multimodal main experiment는 M2/M4/M5/M6/IM1이다.
3. service-level contribution은 evidence packet과 rank-1 evidence selection이다.
4. visual encoder ablation과 frame budget ablation은 심사 방어용 robustness 결과로 사용한다.
5. 검색 실험 자체에는 생성 모델을 사용하지 않았고, answer-level 통제 실험에서는 생성 모델을 고정한 채 DB evidence 구성만 바꾸었다.
6. 가장 중요한 DB 연구 통찰은 "AI 응답 품질은 LLM 이전의 evidence retrieval/selection 구조에 크게 의존하며, 다각도 환경에서는 evidence availability보다 evidence selection이 중요하다"이다.

삭제 또는 완화:

1. B0-B5만으로 멀티모달 검색을 입증했다는 표현.
2. CLIP을 비전 추론 모델처럼 설명하는 표현.
3. 실제 상용 시스템을 완성했다는 과장.
4. M6가 모든 baseline보다 항상 좋다는 주장.

## 후속 작업 우선순위

| 우선순위 | 작업 | 이유 |
|---|---|---|
| 1 | Word/HWP 제출 양식 육안 검수 | 자동 변환 후 표, 그림, 줄바꿈, 참고문헌 형식 확인 |
| 2 | 저자/세부분야/교신저자 정보 반영 | DBR 첫 쪽 필수 항목 |
| 3 | qualitative evidence 그림 최종 배치 | service-level evidence contribution을 시각적으로 설명 |
| 4 | 제출 직전 pipeline audit 재실행 | 필수 산출물 누락 방지 |
| 5 | 제출 자료 색인 최신화 | 4-VLM 다각도 결과, index benchmark, 최신 종합 문서 반영 |
