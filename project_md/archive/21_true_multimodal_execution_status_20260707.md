# True Multimodal 검색 재설계 실행 결과

작성 기준일: 2026-07-07

2026-07-09 최신 갱신: 본 문서는 VRU와 AI Hub 지능형 CCTV의 true multimodal retrieval 실행 기록으로 보존한다. 이후 SigLIP ablation, LLM answer layer, AI Hub 다각도 CCTV answer-level VLM 실험, 시내도로 CCTV index benchmark가 추가 완료되었다. 최신 전체 판정은 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따르며, 이 문서의 "LLM/VLM 생성 모델 미사용" 표현은 retrieval core 기준으로만 해석한다.

## 핵심 정정

이전 B0-B5 실험은 `text evidence + metadata` 검색 기준선으로는 유효하지만, 실제 상용 서비스형 "멀티모달 데이터셋 기반 검색"의 주 실험으로 주장하면 안 된다. 영상 원본이 있어도 검색 표현에 프레임/이미지 임베딩이 들어가지 않으면 true multimodal retrieval이 아니다.

따라서 본 연구의 주 실험은 다음 구조로 재고정한다.

```text
video clips
  -> keyframe extraction
  -> visual frame embedding
  -> frame vector index

text evidence documents
  -> text embedding / BM25
  -> document index

metadata facets
  -> structured filter index

query(text or image + optional metadata filter)
  -> visual retrieval + text retrieval + metadata filtering
  -> clip/frame/timestamp/thumbnail/evidence 반환
```

## 멀티모달 데이터셋의 실험상 정의

본 논문에서 "멀티모달 데이터셋"은 단순히 비디오 파일과 텍스트 파일이 함께 있는 상태를 뜻하지 않는다. 검색 시스템 관점에서는 다음 산출물이 모두 있어야 한다.

| 구성 | 필요성 | 현재 상태 |
|---|---|---|
| 원본 영상 `mp4` | 실제 시각 모달리티 | VRU, AI Hub 지능형관제 확보 |
| 키프레임/이벤트 프레임 | 검색 가능한 이미지 단위 evidence | 구축 완료 |
| 시각 임베딩 | text/image-to-video 검색 표현 | CLIP 기반 구축 완료 |
| 텍스트 evidence | caption, VQA, event caption 검색 | 기존 B0-B5 구축 완료 |
| 구조화 metadata | 운영형 필터 조건 | 기존 canonical 구축 완료 |
| 텍스트 질의 | text-to-video, text-to-document | 구축 완료 |
| 이미지 질의 | screenshot/image-to-video 검색 | 신규 구축 완료 |
| 검색 결과 evidence | frame_id, timestamp, thumbnail path | 신규 구축 완료 |

이 기준을 만족해야 "상용형 멀티모달 검색 서비스"와 대응된다.

## 실행된 새 파이프라인

| 단계 | 스크립트 | 설명 |
|---|---|---|
| 키프레임 추출 | `2026_KIISE/scripts/extract_keyframes.py` | mp4에서 clip당 4개 대표 프레임 추출 |
| 시각 임베딩 생성 | `2026_KIISE/scripts/build_visual_embeddings.py` | CLIP image encoder로 프레임 임베딩, CLIP text encoder로 질의 임베딩 생성 |
| text-to-video 검색 | `2026_KIISE/scripts/run_visual_retrieval_baselines.py` | 텍스트 질의로 시각 프레임 색인 검색 |
| text+visual fusion | `2026_KIISE/scripts/run_multimodal_fusion_baselines.py` | 텍스트 evidence 순위와 시각 프레임 순위를 RRF로 결합 |
| image-to-video 검색 | `2026_KIISE/scripts/run_image_to_video_retrieval.py` | held-out keyframe을 이미지 질의로 사용해 원본 clip 검색 |
| 정성 예시 추출 | `2026_KIISE/scripts/export_multimodal_qualitative_examples.py` | frame/timestamp/thumbnail path를 포함한 논문용 사례 표 생성 |
| 이벤트 프레임 grounding | `2026_KIISE/scripts/evaluate_event_frame_grounding.py` | 검색된 evidence frame이 AI Hub event_start/end 범위 안에 있는지 검증 |

## 산출물 경로

### VRU-Accident

| 산출물 | 경로 |
|---|---|
| canonical | `Datasets/processed/vru_accident/20260706/canonical` |
| keyframes | `Datasets/processed/vru_accident/20260706/keyframes/clip4_full` |
| visual embeddings | `Datasets/processed/vru_accident/20260706/visual_embeddings/clip-vit-base-patch32_full` |
| text-to-video 결과 | `Datasets/processed/vru_accident/20260706/results/visual_clip_full_m2_m4` |
| text+visual fusion 결과 | `Datasets/processed/vru_accident/20260706/results/multimodal_fusion_clip_bgem3_m5_m6` |
| image-to-video 결과 | `Datasets/processed/vru_accident/20260706/results/image_to_video_clip_full` |
| qualitative examples | `2026_KIISE/paper_assets/20260707_true_multimodal_examples/vru_*.md` |
| service testbed packets | `Datasets/processed/vru_accident/20260706/service_testbed/m6_im1_top5` |

구축 상태:

| 항목 | 값 |
|---|---:|
| clips | 1,000 |
| keyframes | 4,000 |
| frame extraction errors | 0 |
| text queries | 244 |
| image queries | 1,000 |
| visual embedding dim | 512 |

### AI Hub 지능형 관제 서비스 CCTV 영상

| 산출물 | 경로 |
|---|---|
| canonical | `Datasets/processed/aihub_intelligent_cctv/20260706/canonical` |
| keyframes | `Datasets/processed/aihub_intelligent_cctv/20260706/keyframes/event4_full` |
| visual embeddings | `Datasets/processed/aihub_intelligent_cctv/20260706/visual_embeddings/clip-vit-base-patch32_full` |
| text-to-video 결과 | `Datasets/processed/aihub_intelligent_cctv/20260706/results/visual_clip_full_m2_m4` |
| text+visual fusion 결과 | `Datasets/processed/aihub_intelligent_cctv/20260706/results/multimodal_fusion_clip_bgem3_m5_m6` |
| image-to-video 결과 | `Datasets/processed/aihub_intelligent_cctv/20260706/results/image_to_video_clip_full` |
| qualitative examples | `2026_KIISE/paper_assets/20260707_true_multimodal_examples/aihub_cctv_*.md` |
| M4 event grounding | `Datasets/processed/aihub_intelligent_cctv/20260706/results/event_grounding_m4_visual` |
| M6 event grounding | `Datasets/processed/aihub_intelligent_cctv/20260706/results/event_grounding_m6_fusion` |
| IM1 event grounding | `Datasets/processed/aihub_intelligent_cctv/20260706/results/event_grounding_im1_image` |
| service testbed packets | `Datasets/processed/aihub_intelligent_cctv/20260706/service_testbed/m6_im1_top5` |

구축 상태:

| 항목 | 값 |
|---|---:|
| clips | 269 |
| event-centered keyframes | 1,076 |
| frame extraction errors | 0 |
| text queries | 133 |
| image queries | 269 |
| visual embedding dim | 512 |

## 검색 전략 재정의

| ID | 의미 | 모달리티 | 역할 |
|---|---|---|---|
| B0-B5 | 기존 텍스트/메타데이터 기준선 | text, metadata | baseline only |
| M2 | visual vector-only | text query -> visual frames | 텍스트가 영상 프레임을 직접 검색 |
| M4 | metadata prefilter + visual | text, visual, metadata | 운영형 필터 후 시각 검색 |
| M5 | text+visual RRF | text, visual | 메타데이터 없이 텍스트 evidence와 시각 검색 결합 |
| M6 | text+visual+metadata RRF | text, visual, metadata | 상용형 통합 검색 구조 |
| IM1 | image-to-video holdout | image, video | 스크린샷/증거 이미지로 원본 영상 검색 |

## 주요 결과

### Text-to-video visual retrieval

| Dataset | Strategy | Recall@10 | Recall@20 | MRR | nDCG@10 | Mean latency |
|---|---|---:|---:|---:|---:|---:|
| VRU | M2 visual-only | 0.0616 | 0.0983 | 0.1716 | 0.0883 | 7.050 ms |
| VRU | M4 metadata+visual | 0.2467 | 0.3440 | 0.3153 | 0.2452 | 66.159 ms |
| AI Hub CCTV | M2 visual-only | 0.1000 | 0.1953 | 0.2199 | 0.1331 | 9.624 ms |
| AI Hub CCTV | M4 metadata+visual | 0.7524 | 0.8139 | 0.7616 | 0.7437 | 31.749 ms |

해석:

- 두 데이터셋 모두에서 metadata prefilter를 visual search 앞에 두는 M4가 M2보다 크게 우수하다.
- 이는 기존 text baseline에서 확인한 "prefilter가 유리하다"는 결론이 시각 프레임 검색에서도 성립함을 보여준다.
- AI Hub CCTV는 event-centered frame을 사용하므로 상용 관제 검색 시나리오와 더 직접적으로 맞는다.

### Text+visual fusion retrieval

| Dataset | Strategy | Recall@10 | Recall@20 | MRR | nDCG@10 | Mean latency |
|---|---|---:|---:|---:|---:|---:|
| VRU | M5 text+visual | 0.2633 | 0.4311 | 0.5110 | 0.3500 | 125.547 ms |
| VRU | M6 text+visual+metadata | 0.4928 | 0.6590 | 0.7837 | 0.6232 | 245.613 ms |
| AI Hub CCTV | M5 text+visual | 0.3847 | 0.5281 | 0.5450 | 0.4261 | 23.248 ms |
| AI Hub CCTV | M6 text+visual+metadata | 0.8016 | 0.8799 | 0.9469 | 0.8951 | 48.929 ms |

해석:

- M6는 상용 서비스 구조를 가장 잘 반영한다. 질의 조건을 metadata로 좁히고, 텍스트 evidence와 시각 evidence를 함께 사용한다.
- 단, 기존 B5 text+metadata 기준선이 일부 데이터셋에서 M6보다 높게 나오는 구간이 있다. 이는 현재 qrels와 질의가 텍스트/라벨/메타데이터 생성 구조에 강하게 정렬되어 있기 때문이다.
- 따라서 논문에서는 "M6가 항상 최고 성능"이라고 주장하지 않는다. 올바른 주장은 "시각 evidence를 포함한 검색 경로를 구성하면 프레임/timestamp/thumbnail을 반환할 수 있고, metadata prefilter는 visual retrieval에서도 효과적이며, 질의 유형에 따라 text-only와 multimodal fusion의 장단점이 달라진다"이다.

### Image-to-video retrieval

| Dataset | Strategy | Image queries | Recall@1 | Recall@5 | Recall@10 | MRR | nDCG@10 | Mean latency |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| VRU | IM1 image-to-video holdout | 1,000 | 0.7550 | 0.9660 | 0.9800 | 0.8567 | 0.8875 | 6.852 ms |
| AI Hub CCTV | IM1 image-to-video holdout | 269 | 0.8810 | 0.9851 | 1.0000 | 0.9258 | 0.9442 | 10.973 ms |

해석:

- 이 트랙은 텍스트 질의가 아니라 이미지 질의가 영상 DB를 검색하는 구조다.
- 질의 프레임 자신은 후보에서 제외했으므로 동일 이미지 매칭 누수는 피했다.
- 상용 서비스 관점에서는 "현장 스크린샷 또는 증거 이미지로 원본 CCTV 클립을 찾는 기능"에 해당한다.

추가 사용자 설정 통제로 `query_frame_seq` 0, 1, 2, 3을 비교했다. 본문 IM1 결과는 `query_frame_seq=2` 기준이다.

| Dataset | qseq0 R@10 | qseq1 R@10 | qseq2 R@10 | qseq3 R@10 |
|---|---:|---:|---:|---:|
| VRU | 0.9020 | 0.9810 | 0.9800 | 0.9680 |
| AI Hub CCTV | 0.9963 | 0.9963 | 1.0000 | 0.8327 |

VRU는 중간 이후 프레임에서 안정적이고, AI Hub CCTV는 event-centered extraction의 마지막 프레임에서 성능이 낮아졌다. 따라서 image-to-video 결과를 원고에 쓸 때는 frame position 설정을 명시해야 한다.

### Service-level evidence packet

M6와 IM1 결과는 `build_service_testbed_packets.py`로 service-level evidence packet으로 변환했다. 이 산출물은 검색 결과를 `clip_id` ranking으로 끝내지 않고, `frame_id`, `timestamp_sec`, `thumbnail_path`, `media_path`, `supporting_text`, `metadata`, score를 포함하는 answer-ready context로 만든다.

| Dataset | Packets | Top-1 relevant | Hit@5 | Frame coverage | Supporting text coverage |
|---|---:|---:|---:|---:|---:|
| VRU | 1,244 | 0.7468 | 0.9486 | 0.9977 | 1.0000 |
| AI Hub CCTV | 402 | 0.8955 | 0.9826 | 1.0000 | 1.0000 |

이 결과는 중요한 통찰을 준다. top-k hit가 높아도 rank-1 evidence가 틀리면 evidence-only 답변은 틀릴 수 있다. 따라서 LLM을 붙이기 전에 evidence selection/reranking 구조를 DB 연구 문제로 다뤄야 한다. 상세 정리는 `2026_KIISE/project_md/23_service_testbed_and_answer_quality_20260707.md`를 기준으로 한다.

추가로 text/visual RRF weight sweep을 수행한 결과, `text_weight:visual_weight = 4:1`이 두 데이터셋에서 가장 높은 top-1 evidence 품질을 보였다. VRU text query Hit@1은 0.7131에서 0.8443으로, AI Hub CCTV text query Hit@1은 0.9248에서 0.9699로 개선되었다. 이는 모델 추가 없이도 DB/query-planning 수준의 evidence selection이 answer quality proxy를 개선할 수 있음을 보여준다.

### AI Hub event-frame grounding

| Strategy | Visual coverage@10 | Frame-in-event rate@10 | Event-grounded Hit@10 |
|---|---:|---:|---:|
| M4 metadata+visual | 1.0000 | 1.0000 | 0.9248 |
| M6 text+visual+metadata | 1.0000 | 1.0000 | 0.9850 |
| IM1 image-to-video | 1.0000 | 1.0000 | 1.0000 |

주의:

- AI Hub 지능형 CCTV는 event_start/end 구간을 기준으로 keyframe을 추출했으므로 `frame_in_event_rate`는 독립적인 temporal localization 성능이라기보다 evidence frame 경로가 라벨 구간과 모순되지 않는지 확인하는 무결성 지표에 가깝다.
- 독립적인 시간 위치추정 성능을 주장하려면 전체 영상에서 균일 프레임을 더 많이 색인하고, 검색된 프레임이 event segment 안으로 수렴하는지 별도 실험해야 한다.

## Vector DB와 LLM 사용 위치

현재 실행은 재현성을 위해 numpy/FAISS 및 기존 pgvector 결과를 함께 사용했다. 논문 시스템 설계에서는 다음 논리로 설명한다.

| 구성 | 현재 실행 | 논문/상용 설계상 역할 |
|---|---|---|
| frame visual vector store | numpy matrix exact search | `frame_visual` vector collection |
| text evidence vector store | FAISS, pgvector 보강 | `document_text` vector collection |
| metadata store | parquet filter | relational/columnar metadata index |
| fusion layer | RRF | rank fusion/query planner |
| LLM/VLM | retrieval core에서는 미사용 | 검색 결과 요약/답변 생성의 downstream layer |

LLM은 본 실험의 핵심 평가 대상이 아니다. LLM을 먼저 넣으면 검색 구조의 기여와 생성 모델 품질이 섞인다. 본 논문에서는 retrieval 결과가 `clip_id`, `frame_id`, `timestamp_sec`, `thumbnail_path`, `supporting_text`를 반환하고, LLM은 그 결과를 설명하는 선택적 후처리로 둔다.

사용 모델의 세부 spec과 로컬 weight/config 검증 경로는 `2026_KIISE/project_md/22_model_stack_spec_and_usage_20260707.md`를 기준으로 한다. 이 단계의 retrieval core에 사용한 모델은 `openai/clip-vit-base-patch32`, `BAAI/bge-m3`, `intfloat/e5-large-v2`이며, LLM/VLM 생성 모델은 retrieval core에는 사용하지 않았다. 최신 원고에서는 별도 answer-level 통제 실험에서 LLM/VLM을 고정 사용한다.

## 기존 원고와 발표에서 반드시 수정할 부분

삭제 또는 수정:

- 기존 B0-B5 결과만으로 "멀티모달 검색 실험을 완료했다"는 표현
- 영상 파일을 보유했다는 이유만으로 "영상 모달리티를 검색에 활용했다"는 표현
- LLM/VLM 기반 질의응답 시스템을 이미 구현한 것처럼 보이는 표현
- 모든 데이터셋에서 fusion이 text-only보다 항상 우월하다는 표현

새로 강조:

- 실제 mp4에서 프레임을 추출했고, 해당 프레임을 CLIP 시각 임베딩으로 색인했다.
- 텍스트 질의가 visual frame index를 직접 검색하는 M2/M4를 구현했다.
- 이미지 질의가 video DB를 검색하는 IM1을 구현했다.
- 결과는 clip ranking만이 아니라 frame/timestamp/thumbnail evidence를 포함한다.
- metadata prefilter의 효과가 text retrieval뿐 아니라 visual retrieval에서도 재현된다.

## 추가 데이터셋 필요성

지금 당장 논문 성립을 위해 추가 데이터셋이 필수는 아니다. 이미 두 개의 실제 mp4 기반 데이터셋에서 true multimodal 검색 경로가 실행됐다.

다만 다음 주장을 강하게 넣으려면 추가 데이터셋이 필요하다.

| 주장 | 추가 필요 |
|---|---|
| 고정형 도시 교통 CCTV에 완전히 특화 | AI Hub 도시/도로 CCTV, 다각도 CCTV 생활안전, WTS |
| 다중 카메라 동일 사건 검색 | WTS, AI Hub 다각도 CCTV |
| 센서 로그+영상 융합 | AI Hub 교차로 신호/보행자/차량 이동 복합 데이터 |
| frame-level qrels 기반 grounding | event segment annotation이 풍부한 CCTV 데이터 |

2주 일정에서는 새 데이터셋보다 현재 두 데이터셋의 evidence frame 평가와 원고 수정이 우선이다.

## 통제 요인 감사

추가 감사는 `2026_KIISE/scripts/audit_experiment_control_factors.py`로 수행했고 결과는 `2026_KIISE/paper_assets/20260707_control_factor_audit`에 저장했다.

핵심 결론:

- controlled env는 `Datasets/envs/kiise-vlmdb`다. base Python 환경은 재현 환경이 아니다.
- qrel target error, metadata filter error, embedding shape mismatch는 감사 대상 데이터셋에서 0이다.
- text model 다양성은 BGE-M3/E5-large-v2로 확보했다.
- visual-text model은 이후 SigLIP ablation으로 보강했다. 단, 둘 다 frame-level image-text encoder이며 video-native temporal encoder는 사용하지 않았다.

## 다음 우선순위

1. 최신 v1 원고와 발표자료에서는 기존 B0-B5를 baseline으로 낮추고, true multimodal 실험과 control factor audit을 본문 중심으로 유지한다.
2. 생성된 qualitative example을 그림/표로 변환해 검색 결과가 `clip/frame/timestamp/thumbnail/evidence text`를 반환함을 보여준다.
3. 독립적인 temporal localization까지 주장하려면 AI Hub CCTV에서 균일 프레임 색인을 추가해 event-centered extraction과 비교한다. 현재 투고 본문에서는 이 주장을 하지 않는다.
4. SigLIP ablation은 이후 완료되었고, 최신 해석은 `24_final_experiment_pipeline_spec_20260707.md`와 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 최종 판단

현재부터의 연구 주제는 다음처럼 고정해야 한다.

> 도시 감시형 영상 데이터베이스에서 시각 프레임, 텍스트 evidence, 구조화 metadata를 결합한 멀티모달 검색 구조의 성능과 한계 분석

이 표현은 실제 실행된 실험과 모순되지 않는다.
