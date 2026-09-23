# Experiment Scaling and Control Plan

작성 기준일: 2026-07-08

## 2026-07-08 정정 사항

본 문서의 초기 해석 중 “metadata-aware visual retrieval이 visual 검색 성능을 직접 개선했다”는 표현은 최종 claim으로 사용하지 않는다. 후속 피드백 검토와 보강 실험 결과, 기존 `instance_vqa` 전역 검색은 질의가 target clip을 식별하지 못하는 ill-posed task이며, SigLIP visual-only 성능은 매우 낮아 M4 개선분의 상당 부분이 metadata candidate 축소에서 온 것으로 판단한다.

정정된 최종 실험 체계는 `34_feedback_response_and_corrected_experiment_design_20260708.md`를 우선한다. 이 문서는 T1 계층화 표본의 산출 경로와 재실행 명령을 보존하기 위한 운영 문서로 유지한다.

2026-07-09 최신 갱신: T1 stratified diagnostic subset은 다각도 CCTV evidence DB와 검색/packet pipeline의 운영 검증으로 유지한다. 최종 논문 claim은 T1 visual retrieval 수치가 아니라, 400-clip bbox-asymmetry stratum의 answer-level VLM 결과와 4-VLM 재검증을 따른다(`38_four_vlm_multiview_final_recheck_20260709.md`, `40_latest_dataset_and_experiment_synthesis_20260709.md`). 따라서 T1 결과는 "metadata로 candidate를 줄였을 때 global instance retrieval의 착시와 한계가 드러난다"는 진단 근거로 사용한다.

## 문제 인식

이전 단계의 주의점은 두 가지였다.

1. **표본 규모 문제**: visual result가 50-event sample이라 본문 최종 수치로 쓰기에는 작다.
2. **표본 편향 문제**: 단순히 앞에서부터 N개 event를 자르면 특정 event class 또는 split에 치우칠 수 있다.

따라서 본 연구는 무작정 전체 데이터를 모두 처리하는 방식 대신, 다음처럼 계층형 실험 체계를 고정한다.

## 실험 계층

| tier | 목적 | 범위 | 논문에서의 사용 |
|---|---|---|---|
| T0 full canonical audit | 데이터셋 전체 구조 검증 | 4,500 events, 9,000 views, 27,000 evidence frames | 데이터셋 규모, schema completeness, qrels integrity 근거 |
| T1 stratified diagnostic subset | 편향을 줄인 실제 multimodal 검색 검증 | event_class x source_split 22 strata, 각 5개, 총 110 events | visual/text/service packet 주 실험 표본 |
| T2 larger stratified subset | 시간 허용 시 안정성 보강 | 각 strata 10개, 총 220 events | sensitivity/robustness 추가 |
| T3 full text retrieval | visual materialization 없이 전체 text/metadata retrieval 검증 | 4,572 queries, 36,000 documents | 장시간 실행 가능 시 최종 text table |
| T4 full visual retrieval | 모든 evidence frame materialization | 27,000 frames | 2주 일정에서는 no-go. 저장/시간 비용 대비 과함 |

## 현재 확정된 T1 계층화 표본

산출물:

- sample: `Datasets/processed/aihub_multi_angle_cctv/20260708/samples/stratified_event_split_5_seed20260708`
- frame root: `Datasets/processed/aihub_multi_angle_cctv/20260708/keyframes/evidence_stratified_event_split_5`
- canonical subset: `Datasets/processed/aihub_multi_angle_cctv/20260708/canonical_stratified_event_split_5`

표본 정책:

- `event_class x source_split` 기준 22개 strata
- 각 strata에서 seed `20260708`로 5개 event 선택
- 총 110 event
- 각 event는 c1/c2 두 view
- 각 view에서 label evidence frame 최대 3개

| item | value |
|---|---:|
| sampled clips/events | 110 |
| views | 220 |
| materialized frames | 660 |
| frame extraction errors | 0 |
| subset queries | 175 |
| subset qrels | 440 |

## T1 Text Retrieval Result

산출물:

- embedding: `Datasets/processed/aihub_multi_angle_cctv/20260708/embeddings/bge-m3_stratified_event_split_5`
- result: `Datasets/processed/aihub_multi_angle_cctv/20260708/results/bgem3_faiss_b0_b5_stratified_event_split_5`

| strategy | R@10 | R@20 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|
| B0 metadata-only | 0.7410 | 0.8137 | 0.2579 | 0.3608 |
| B1 BM25-only | 0.2295 | 0.3570 | 0.1434 | 0.1476 |
| B2 vector-only | 0.9277 | 1.0000 | 0.4263 | 0.5417 |
| B3 vector postfilter | 1.0000 | 1.0000 | 0.5642 | 0.6634 |
| B4 prefilter+vector | 1.0000 | 1.0000 | 0.5642 | 0.6634 |
| B5 hybrid | 0.9189 | 0.9870 | 0.4354 | 0.5330 |

해석:

- 같은 계층화 표본에서 B3/B4가 vector-only보다 MRR/nDCG@10을 개선한다.
- B3와 B4의 품질이 같은 것은 같은 candidate set을 놓고 정확도만 본 결과이며, latency/실행 계획 관점에서는 prefilter가 DB system claim에 더 적합하다.

## T1 Visual Retrieval Result

산출물:

- visual embedding: `Datasets/processed/aihub_multi_angle_cctv/20260708/visual_embeddings/siglip_stratified_event_split_5`
- result: `Datasets/processed/aihub_multi_angle_cctv/20260708/results/visual_siglip_stratified_event_split_5_m2_m4`

| strategy | R@10 | R@20 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|
| M2 visual vector-only | 0.0711 | 0.1581 | 0.0756 | 0.0431 |
| M4 metadata-prefilter visual | 0.7330 | 0.8183 | 0.2602 | 0.3438 |

해석:

- Visual-only text-to-frame 검색은 event class가 섞이면 거의 동작하지 않는다.
- M4의 높은 R@10/R@20은 visual model의 semantic understanding 개선이라기보다 metadata prefilter가 후보군을 강하게 줄인 효과로 해석해야 한다.
- 따라서 이 결과는 “visual retrieval이 잘된다”의 근거가 아니라, generic visual embedding만으로는 CCTV instance grounding이 어렵고 DB-level candidate/evidence control이 필요하다는 진단 근거로 사용한다.

## T1 Service Evidence Packet

산출물:

- `Datasets/processed/aihub_multi_angle_cctv/20260708/service_testbed/visual_m4_top5_stratified_event_split_5`

| item | value |
|---|---:|
| packets | 175 |
| evidence rows | 875 |
| top-k hit rate | 0.4571 |
| top-1 relevant rate | 0.0800 |

해석:

- top-k 안에 관련 evidence가 들어오는 비율과 top-1 evidence 선택 품질은 다르다.
- LLM/VLM 답변 품질을 높이려면 단순 검색 hit@K가 아니라 top-k evidence selection/reranking이 필요하다.
- 이 지점이 본 연구의 DB-level 후속 기여 지점이다.

## 논문 Claim Control

논문에서 사용할 수 있는 표현:

- “AI Hub 71953 전체 4,500 event를 canonical evidence DB schema로 정규화했다.”
- “전체 qrels, c1/c2 view pair, evidence frame metadata의 integrity audit를 통과했다.”
- “event_class x split 계층화 표본 110개 event에서 실제 frame materialization과 visual/text retrieval을 수행했다.”
- “계층화 표본에서 metadata prefilter는 후보군을 강하게 줄이며, 이 효과는 특히 visual-only embedding의 취약성을 드러내는 진단 신호다.”
- “전역 instance-VQA 검색 결과는 최종 성능 claim이 아니라 task design failure와 grounding risk 분석에 사용한다.”
- “answer-grounding packet 평가와 within-event evidence selection 평가를 추가해 LLM/VLM 입력 근거 품질을 별도로 측정했다.”
- “검색 결과를 LLM/VLM 입력 가능한 service evidence packet으로 변환했다.”

논문에서 피해야 할 표현:

- “전체 27,000 evidence frame에 대해 visual embedding을 완료했다.”
- “전체 4,572 query에 대한 최종 text retrieval metric이다.”
- “LLM이 실제로 답변을 생성했고 품질이 향상됐다.”
- “본 방법이 모든 CCTV 도메인에서 일반적으로 우월하다.”
- “SigLIP visual retrieval이 도시 CCTV 사건 instance 검색을 해결했다.”
- “metadata-aware visual R@10 개선은 visual semantic understanding 개선을 뜻한다.”
- “instance-VQA 전역 retrieval은 방어 가능한 최종 task다.”

## 남은 선택 작업

2주 일정에서 추가로 가장 가치 있는 작업은 다음 순서다.

1. T2 larger stratified subset: 각 strata 10개, 총 220 event로 visual result 안정화
2. T3 full text retrieval: 4,572 query 전체 B0-B5 결과 생성
3. service packet reranking: visual M4 top-k에서 top-1 relevant rate 개선
4. 원고 표/그림 갱신: T1 결과를 main multimodal anchor result로 반영

## 재실행 명령

계층화 표본 생성:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/sample_aihub_multi_angle_stratified_clips.py \
  --canonical-root Datasets/processed/aihub_multi_angle_cctv/20260708/canonical \
  --output-dir Datasets/processed/aihub_multi_angle_cctv/20260708/samples/stratified_event_split_5_seed20260708 \
  --per-event-class-split 5 --seed 20260708 --overwrite
```

계층화 frame materialization:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/materialize_aihub_multi_angle_evidence_frames.py \
  --canonical-root Datasets/processed/aihub_multi_angle_cctv/20260708/canonical \
  --clip-ids-file Datasets/processed/aihub_multi_angle_cctv/20260708/samples/stratified_event_split_5_seed20260708/clip_ids.txt \
  --output-dir Datasets/processed/aihub_multi_angle_cctv/20260708/keyframes/evidence_stratified_event_split_5 \
  --max-frames-per-view 3 --overwrite
```

T2 확장은 위 명령에서 `--per-event-class-split 10`으로 별도 output directory를 지정한다.
