# 전체 실험 파이프라인 재점검 및 원고 재작성 보고서

작성 기준일: 2026-07-07

2026-07-09 최신 갱신: 본 문서는 v1 true multimodal 원고 재작성 당시의 재점검 기록이다. 이후 다각도 CCTV answer-level VLM 실험, LLM answer layer, reranker/한국어 인코더 보강, 시내도로 CCTV index benchmark가 추가 반영되어 최신 기준은 `40_latest_dataset_and_experiment_synthesis_20260709.md`와 최신 원고 `kiise_dbr_manuscript_v1_true_multimodal.md`를 따른다.

## 결론

본 연구는 v0/v0.1 단계의 text/metadata 중심 실험에서 벗어나, 실제 mp4 기반 true multimodal retrieval과 service-level evidence selection을 중심으로 재정리되었다. 최신 투고 기준은 `kiise_dbr_manuscript_v1_true_multimodal.md`이며, 연구 체계, 방법론, 데이터셋, 모델, 검색 전략, 산출물 경로는 `24_final_experiment_pipeline_spec_20260707.md`에 통합 기록했다.

pipeline audit 결과 필수 산출물 32개 중 누락 파일은 0개다. 다만 추가 질의 이후 시스템 환경, 사용자 설정, 데이터셋 적합성, 모델 호환성 통제 감사를 보강했고, IM1 image-to-video의 frame position sensitivity를 추가 수행했다. 따라서 현재 남은 핵심 작업은 새 대형 실험이 아니라 통제 결과를 원고에 반영하고 Word/HWP 제출 양식을 검수하는 일이다.

## 최신 원고 산출물

| 산출물 | 경로 | 상태 |
|---|---|---|
| v1 원고 본문 | `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal.md` | 재작성 완료 |
| v1 A4 Word | `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal_A4.docx` | 생성 완료 |
| v1 A4 PDF | `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal_A4.pdf` | 이전 A4 12쪽 보조 검수본 |
| DBR review Word | `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal_DBR_review.docx` | 최신 제출 후보 |
| DBR review PDF | `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal_DBR_review.pdf` | 최신 A4 16쪽 검수본 |
| preflight | `2026_KIISE/manuscript/pre_submission_preflight_20260707.md` | v1 기준 갱신 |
| 자료 색인 | `2026_KIISE/manuscript/submission_materials_index.md` | v1 산출물 반영 |
| 제출 형식 체크리스트 | `2026_KIISE/manuscript/submission_format_checklist.md` | v1/A4 기준 갱신 |
| 통제 요인 판단 | `2026_KIISE/project_md/26_control_factors_and_additional_experiment_decision_20260707.md` | 시스템/사용자/데이터/모델 통제 감사 반영 |

형식 점검:

| 항목 | 값 |
|---|---:|
| 국문 초록 | 공백 제외 401자 |
| 영문 초록 | 132단어 |
| 키워드 | 국문 6개, 영문 6개 |
| PDF 페이지 크기 | A4 |
| PDF 페이지 수 | 최신 DBR review PDF 16쪽 |

## 연구 체계 기록 위치

| 범주 | 기준 문서 | 기록 내용 |
|---|---|---|
| 최종 연구 질문과 파이프라인 | `24_final_experiment_pipeline_spec_20260707.md` | RQ1~RQ5, 데이터셋 범위, 모델, 검색 전략, 핵심 결과 |
| true multimodal 재설계 | `20_true_multimodal_research_redesign.md` | B0~B5 중심 설계의 한계와 M2/M4/M5/M6/IM1 재설계 |
| 실행 결과 | `21_true_multimodal_execution_status_20260707.md` | keyframe, CLIP visual embedding, visual/fusion/image 검색 결과 |
| 모델 spec | `22_model_stack_spec_and_usage_20260707.md` | CLIP/SigLIP, BGE/E5, fixed LLM/VLM answer control 범위 |
| service evidence | `23_service_testbed_and_answer_quality_20260707.md` | answer-ready evidence packet, top-k와 rank-1 evidence 차이, weighted RRF |
| 통제 요인 | `26_control_factors_and_additional_experiment_decision_20260707.md` | 시스템 환경, 사용자 설정, 데이터셋 적합성, 모델 다양성/호환성, 추가 실험 판단 |
| 제출 절차 | `2026_KIISE/manuscript/submission_workplan.md` | 2026-07-20까지의 남은 작업과 No-Go 기준 |

## 데이터셋 최종 범위

| 데이터셋 | 최종 역할 | 핵심 산출물 |
|---|---|---|
| VRU-Accident | 주 실험 1 | 1,000 clips, 4,000 keyframes, visual/fusion/image/service 결과 |
| AI Hub 지능형 CCTV | 주 실험 2 | 269 clips, 1,076 keyframes, visual/fusion/image/service 결과 |
| AI Hub 이상행동 CCTV | 보조 baseline | canonical/text metadata baseline까지 사용, true multimodal main result에서는 제외 |
| AI Hub 다각도 CCTV | answer-level multi-view | canonical 전체, 400-clip stratum, 4-VLM 결과 |
| 시내도로 CCTV | index benchmark | real 132K CLIP vectors, synthetic 1M ANN benchmark |

저장 경로:

| 항목 | 경로 |
|---|---|
| 논리 데이터 루트 | `Datasets` |
| 물리 데이터 루트 | `/hdd2/KIISE_datasociety/Datasets` |
| VRU processed | `Datasets/processed/vru_accident/20260706` |
| AI Hub 지능형 CCTV processed | `Datasets/processed/aihub_intelligent_cctv/20260706` |
| AI Hub 이상행동 CCTV processed | `Datasets/processed/aihub_abnormal_cctv/20260707` |

## 모델 및 DB 사용 범위

| 구성 | 사용 여부 | 역할 |
|---|---:|---|
| `openai/clip-vit-base-patch32` | 사용 | keyframe image embedding, text query CLIP embedding, image query embedding |
| `BAAI/bge-m3` | 사용 | text evidence main embedding |
| `intfloat/e5-large-v2` | 사용 | text embedding robustness |
| FAISS | 사용 | local exact vector retrieval prototype |
| BM25 | 사용 | sparse retrieval baseline |
| PostgreSQL + pgvector | 보조 사용 | VRU bge-m3 SQL metadata prefilter 재현성 |
| LLM answer generator | 고정 사용 | 6.8절 answer-level evidence control |
| VLM generative reasoning | 고정 사용 | 6.13절 다각도 view evidence control |

주의: CLIP은 비전 추론 모델로 쓰지 않았고, visual-text embedding 모델로만 사용했다.

## 최종 핵심 결과

| Dataset | Keyframes | M4 R@10 | M4 nDCG@10 | M6 R@10 | IM1 R@10 | Rerank best | Rerank Hit@1 | Service top1 |
|---|---:|---:|---:|---:|---:|---|---:|---:|
| VRU-Accident | 4,000 | 0.2467 | 0.2452 | 0.4928 | 0.9800 | `RW_t4_v1` | 0.8443 | 0.7725 |
| AI Hub CCTV | 1,076 | 0.7524 | 0.7437 | 0.8016 | 1.0000 | `RW_t4_v1` | 0.9699 | 0.9104 |

해석:

1. metadata prefilter는 visual retrieval에서도 vector-only보다 안정적이다.
2. image-to-video 검색은 실제 증거 이미지 기반 영상 검색 기능으로 동작한다.
3. top-k retrieval 성능과 rank-1 answer evidence 품질은 다르다.
4. weighted RRF는 LLM을 붙이지 않고도 evidence selection 품질을 개선한다.
5. 본 논문의 DB 연구 기여는 AI 응답 품질을 LLM 이전의 retrieval/selection 구조로 분해한 데 있다.

## 추가 통제 감사 결과

| 범주 | 결과 |
|---|---|
| controlled env | `Datasets/envs/kiise-vlmdb`에서 재현해야 함. base Python은 통제 환경이 아님 |
| dataset root | `/hdd2/KIISE_datasociety/Datasets` |
| GPU | NVIDIA GeForce RTX 3090 24GB x 2 |
| qrels integrity | main/supplementary datasets 모두 qrel target errors 0 |
| metadata filter integrity | metadata filter zero candidate/query mismatch 0 |
| embedding compatibility | BGE-M3, E5-large-v2, CLIP shape/count check 통과 |
| text model diversity | BGE-M3/E5-large-v2로 확보 |
| visual model diversity | CLIP/SigLIP ablation 완료. 단, video-native temporal encoder는 미사용 |

IM1 image-to-video frame position sensitivity:

| Dataset | qseq0 R@10 | qseq1 R@10 | qseq2 R@10 | qseq3 R@10 |
|---|---:|---:|---:|---:|
| VRU | 0.9020 | 0.9810 | 0.9800 | 0.9680 |
| AI Hub CCTV | 0.9963 | 0.9963 | 1.0000 | 0.8327 |

이 결과는 IM1의 본문 기준이 `query_frame_seq=2`임을 명시해야 함을 보여준다. VRU는 중간 이후 프레임에서 안정적이지만 AI Hub CCTV는 event-centered extraction의 마지막 프레임에서 성능이 낮아진다.

## 모순 제거 기준

원고와 발표자료에서 반드시 지킬 표현:

- B0~B5는 text/metadata baseline이다.
- true multimodal main result는 M2/M4/M5/M6/IM1/RW_t4_v1이다.
- 검색 실험 자체에는 LLM/VLM 생성 모델을 사용하지 않았다. answer-level 통제 실험에서는 생성 모델을 고정 사용했다.
- AI Hub 이상행동 CCTV는 보조 baseline이며 true multimodal main result가 아니다.
- 상용 완성 시스템이 아니라 상용 서비스형 검색 테스트베드 수준의 evidence retrieval/selection 실험이다.

피해야 할 표현:

- B0~B5만으로 멀티모달 검색을 완료했다.
- LLM 또는 VLM이 CCTV 영상을 이해하고 답변했다.
- CLIP이 사건을 추론했다.
- HNSW/IVF/IVF-PQ 결과를 end-to-end VLM-QA 지연으로 과장했다.
- AI Hub 이상행동 CCTV를 주 실험 true multimodal 결과로 포함했다.

## 제출 전 남은 작업

| 우선순위 | 작업 | 상태 |
|---:|---|---|
| 1 | 저자 성명, 소속, 직위, 세부분야, 교신저자 정보 확정 | 대기 |
| 2 | v1 A4 Word/HWP에서 표·그림 배치 육안 검수 | 대기 |
| 3 | qualitative evidence 그림 최종 삽입 | 대기 |
| 4 | 제출 직전 pipeline audit 재실행 | 대기 |
| 5 | DBR 공식 투고 규정 재확인 | 대기 |

공식 투고 규정 확인 경로: https://dbsociety.kr/dbr_submission_guide/
