# DBR 2026년 8월호 투고 실행 보드

작성 기준일: 2026-07-07
최신 갱신 기준일: 2026-07-09
목표 제출일: 2026-07-20
최신 원고: `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal.md`

## 결론

남은 기간의 최선은 새 연구 주제를 더 넓히는 것이 아니라, 이미 수행한 true multimodal/service evidence, answer-level LLM/VLM, multi-view view-selection, index benchmark 결과를 심사자가 검증 가능한 논문 패키지로 잠그는 것이다. 추가 수집은 중단하고, 통제·형식·논리·그림·재현성만 정밀하게 닫는다.

## 작업 우선순위

| 우선순위 | 작업 | 마감 | 상태 | 산출물 |
|---:|---|---|---|---|
| P0 | 주장-근거-파일 추적표 고정 | 2026-07-07 | 완료 | 이 문서 3장 |
| P0 | 원고 v1과 통제 감사 결과 정합성 반영 | 2026-07-07 | 완료 | `kiise_dbr_manuscript_v1_true_multimodal.md` |
| P0 | pipeline/control audit 재실행 | 제출 직전 반복 | 완료, 제출 직전 반복 필요 | `paper_assets/20260707_*_audit` |
| P1 | 표 1~20 최종 번호와 본문 참조 검수 | 2026-07-09 | 재검수 필요 | 최신 원고 기준 |
| P1 | 그림 1~7 제출용 구성 | 2026-07-09 | 재검수 필요 | `paper_assets/20260707_submission_figures` |
| P1 | 저자 정보, 소속, 직위, 세부분야, 교신저자 정보 반영 | 2026-07-09 | 사용자 입력 대기 | `author_info_and_word_hwp_checklist.md` |
| P1 | 참고문헌 번호·본문 인용 일치 검수 | 2026-07-10 | 재검수 필요 | refs 1~22, 특히 [19]-[22] |
| P2 | 문장 압축과 주장 수위 교정 | 2026-07-12 | 대기 | 제출 초안 v1.1 |
| P2 | 개인정보·데이터 라이선스·윤리 문단 최종화 | 2026-07-13 | 대기 | 원고 8장/한계 |
| P2 | 내부 검토/공저자 피드백 반영 | 2026-07-16 | 대기 | 제출 초안 v2 |
| P0 | 최종 제출 패키징 | 2026-07-19 | 대기 | Word/HWP 원본, PDF, 그림 |

## No-Go

아래 작업은 지금 하지 않는다.

| 작업 | 이유 |
|---|---|
| 새 대형 데이터셋 추가 수집 | 현재 데이터셋 구축과 실험 체계가 충분하며 제출 전 리스크만 키움 |
| 새 LLM/VLM 추가 | 이미 Qwen/Llama/Qwen-VL/InternVL/Idefics 축이 있으므로 원고 메시지를 흐릴 수 있음 |
| index 결과를 end-to-end VLM-QA 지연으로 과장 | index benchmark는 검색 계층의 정확도·지연·비용 trade-off로만 해석해야 함 |
| 새 ablation을 본문 필수 결과로 추가 | 결과가 늘수록 제출 전 정합성 리스크가 커짐 |
| AI Hub 이상행동 CCTV를 true multimodal main으로 승격 | 현재 visual embedding main track에 포함하지 않았으므로 과장 위험 |

## 주장-근거-파일 추적표

| 논문 주장 | 방어 근거 | 핵심 파일 | 상태 |
|---|---|---|---|
| 실제 mp4 기반 true multimodal 검색을 수행했다 | VRU/AI Hub CCTV에서 keyframe extraction, CLIP visual embedding, text/image query 검색 완료 | `Datasets/processed/*/keyframes/*_full`, `Datasets/processed/*/visual_embeddings/clip-vit-base-patch32_full` | 통과 |
| metadata prefilter는 visual retrieval에도 유효하다 | M4가 M2보다 두 데이터셋 모두에서 R@10/nDCG@10 향상 | `Datasets/processed/*/results/visual_clip_full_m2_m4/summary.md` | 통과 |
| image-to-video 검색은 서비스 기능으로 동작 가능하다 | IM1 qseq2 기준 VRU R@10 0.9800, AI Hub R@10 1.0000 | `Datasets/processed/*/results/image_to_video_clip_full/summary.md` | 통과 |
| IM1 결과는 프레임 위치 설정에 대한 통제 결과가 있다 | qseq0/1/2/3 sensitivity 완료 | `paper_assets/20260707_control_factor_audit/summary.md` | 통과 |
| top-k retrieval과 rank-1 answer evidence 품질은 다르다 | service packet에서 Hit@5와 Top-1 relevant 차이 확인 | `Datasets/processed/*/service_testbed/*/summary.md` | 통과 |
| DB/query-planning 수준 evidence selection이 품질을 개선한다 | weighted RRF `RW_t4_v1`이 Hit@1/nDCG@10 개선 | `Datasets/processed/*/results/weighted_fusion_rerank_sweep_bgem3_clip/summary.md` | 통과 |
| 검색 실험에는 LLM/VLM 생성 모델을 쓰지 않았다 | service contract와 모델 spec에 retrieval-core 미사용 명시 | `23_service_testbed_and_answer_quality_20260707.md`, `22_model_stack_spec_and_usage_20260707.md` | 통과 |
| answer-level에서 DB evidence 효과를 검증했다 | fixed LLM/VLM 조건에서 evidence 구성만 변경 | `36_multiview_answer_level_results_20260708.md`, `38_four_vlm_multiview_final_recheck_20260709.md` | 통과 |
| 저장·색인 구조 trade-off를 실험했다 | 시내도로 132K real + 1M scale benchmark | `39_index_structure_benchmark_results_20260709.md` | 통과 |
| 데이터셋/qrels/metadata filter 무결성은 검증됐다 | qrel target error 0, metadata filter error 0 | `paper_assets/20260707_control_factor_audit/summary.md` | 통과 |
| 재현 환경은 고정됐다 | controlled conda env, GPU, package version 기록 | `paper_assets/20260707_control_factor_audit/control_factor_audit.json` | 통과 |
| visual model 다양성은 범위를 제한해 보강했다 | CLIP/SigLIP retrieval ablation 완료, answer-level은 Qwen/Qwen-VL/InternVL/Idefics 축으로 보강하되 video-native temporal encoder는 후속 과제로 명시 | 원고 8장, `22_model_stack_spec_and_usage_20260707.md`, `38_four_vlm_multiview_final_recheck_20260709.md` | 통과 |

## 오늘 즉시 처리할 순서

1. P0 주장-근거-파일 추적표 작성: 완료.
2. P1 표·그림 배치안 확정: 완료.
3. P1 qualitative evidence 그림 후보 선별: 완료, `fig3_service_evidence_examples_v1.png`.
4. P1 Word/HWP 육안 검수 항목 생성: 완료, `2026_KIISE/manuscript/author_info_and_word_hwp_checklist.md`.
5. P0 audit 재실행 명령을 제출 전 checklist에 고정: 완료, 제출 직전 반복.

## 제출 직전 반복 명령

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/audit_true_multimodal_pipeline.py
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/audit_experiment_control_factors.py
pdfinfo 2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal_DBR_review.pdf | rg "Pages|Page size"
```

## 다음 작업의 정확한 완료 조건

P1 표·그림 배치안은 다음 조건을 만족해야 완료로 본다.

- 표 1~20의 제목, 원고 위치, 근거 파일이 모두 확정된다.
- 그림 1~7의 목적, 입력 파일, 생성 방식, 캡션이 확정된다. 현재 `2026_KIISE/paper_assets/20260707_submission_figures/figure_index.md`와 최신 원고 기준으로 재검수한다.
- 기존 v0 B0-B5 그림은 보조 baseline으로 낮추고 v1 main 그림과 혼동하지 않는다.
- Word/HWP에 삽입할 PNG/PDF 후보 경로가 명시된다.

현재 자동 검수 결과:

- 표 번호: 최신 원고 표 1~20 재검수 필요.
- 그림 번호: 최신 원고 그림 1~7 재검수 필요.
- 참고문헌: 1~22 순서와 본문 인용 재검수 필요.
- DBR review PDF: 16쪽, A4 유지.

최근 재실행 결과:

- `audit_true_multimodal_pipeline.py`: `missing_files=0`.
- `audit_experiment_control_factors.py`: `status=ok`.
- `generate_submission_figures_v1.py`: 제출 그림 재생성 기반.
- DBR review PDF: 16쪽, A4 유지.
