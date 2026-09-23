# Feedback Response and Corrected Experiment Design

작성 기준일: 2026-07-08

2026-07-09 최신 갱신: 이 문서에서 제안한 corrected path는 실행 완료되었다. 다각도 answer-level 실험은 400 clip bbox-asymmetry stratum에서 Qwen2.5-VL, Qwen2-VL, InternVL3-8B, Idefics2-8b로 평가되었고, 세 개의 강한 VLM에서 `better-view > worse-view`, `both-view ≈ better-view` 결론이 반복 관찰되었다. Idefics2는 near-chance라 보조 근거로만 둔다. 최신 수치와 원고 반영 상태는 `38_four_vlm_multiview_final_recheck_20260709.md`와 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 결론

외부 피드백은 본 연구 흐름과 직접 연결되며, 핵심 지적은 타당하다. 기존 schema, raw integrity audit, frame materialization, embedding, service packet 구축은 연구 자산으로 유지할 수 있다. 그러나 기존 instance-VQA retrieval 결과와 visual retrieval 결과를 그대로 “멀티모달 검색 우수성”의 근거로 쓰는 것은 방어되지 않는다.

따라서 본 연구의 실험 주장은 다음처럼 정정한다.

- 폐기/격하: 모호한 자연어 VQA 질의만으로 전역 corpus에서 특정 instance clip을 식별했다는 주장
- 폐기/격하: SigLIP visual-only 검색이 도시 CCTV event instance retrieval을 실질적으로 해결한다는 주장
- 유지: multi-view video, question/answer, CoT/caption, frame/object/bbox, structured metadata를 통합한 evidence DB schema
- 보강: LLM/VLM 답변 품질을 좌우하는 DB-level evidence packet 품질과 within-event evidence-frame selection 평가

## 왜 기존 Instance-VQA가 Ill-Posed인가

`instance_vqa` 질의 예시는 다음과 같다.

> 관찰된 영상에 '비정상적인 경로로의 침범' 상황이 있었는지 설명하고, 그 판단의 증거를 제시하라.

이 질의는 `event_class`만 표현하고 특정 clip을 식별할 정보가 없다. 하지만 qrel은 단일 target clip을 정답으로 둔다. 즉 같은 class의 다른 사건은 질의 의미상 틀렸다고 보기 어렵지만, 평가에서는 오답 처리된다.

정량 근거:

| corpus | clips | event_class 수 | same-class 후보 수 |
|---|---:|---:|---:|
| full canonical | 4,500 | 11 | class별 45~617 |
| stratified subset | 110 | 11 | class별 10 |

따라서 subset에서 instance-VQA 점수가 오른 것은 target instance를 더 잘 식별했기 때문이 아니라, 같은 class 경쟁 후보가 최대 617개에서 10개로 줄어든 효과가 크게 개입된 것이다. 이 결과는 최종 논문 성능 주장으로 쓰지 않고, task design failure를 보여주는 진단 결과로만 사용한다.

## 기존 Visual Retrieval 해석 정정

T1 stratified subset에서 SigLIP visual retrieval 결과는 다음과 같다.

| strategy | R@10 | R@20 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|
| M2 visual vector-only | 0.0711 | 0.1581 | 0.0756 | 0.0431 |
| M4 metadata-prefilter visual | 0.7330 | 0.8183 | 0.2602 | 0.3438 |

정정된 해석:

- M2가 매우 낮으므로, 한국어 text-to-CCTV-frame generic visual embedding만으로 event instance를 찾는 것은 거의 동작하지 않는다.
- M4의 개선은 visual model이 사건을 잘 이해했기 때문이라기보다, metadata filter가 후보군을 같은 class로 강하게 줄인 효과다.
- 따라서 “visual retrieval에서도 metadata-aware가 결정적”이라는 표현은 과장이다.
- 논문에서는 “generic VLM embedding은 도시 CCTV instance grounding에 취약하며, DB-level metadata/evidence 구조가 필요하다”로 프레이밍한다.

## Answer-Grounding 재평가

기존 검색 결과를 LLM 입력 packet 관점에서 재평가했다. 지표는 top-k 결과 안에 qrel target clip의 frame/bbox/text evidence가 실제로 들어왔는지 측정한다. LLM 생성은 수행하지 않았고, evidence-only answer contract로 평가했다.

산출물:

- visual M4 packet: `Datasets/processed/aihub_multi_angle_cctv/20260708/service_testbed/visual_m4_top5_stratified_event_split_5`
- text B4 packet: `Datasets/processed/aihub_multi_angle_cctv/20260708/service_testbed/text_b4_top5_stratified_event_split_5`
- visual grounding eval: `Datasets/processed/aihub_multi_angle_cctv/20260708/results/answer_grounding_visual_m4_top5_stratified_event_split_5`
- text grounding eval: `Datasets/processed/aihub_multi_angle_cctv/20260708/results/answer_grounding_text_b4_top5_stratified_event_split_5`

Overall:

| packet source | queries | top1_relevant | top5_relevant | grounded_top5 | wrong_same_class_top1 |
|---|---:|---:|---:|---:|---:|
| visual M4 top5 | 175 | 0.0800 | 0.4571 | 0.4571 | 0.5714 |
| text B4 top5 | 175 | 0.4457 | 0.7086 | 0.7086 | 0.5543 |

Instance-VQA만 분리하면 다음과 같다.

| packet source | queries | top1_relevant | top5_relevant | grounded_top5 | wrong_same_class_top1 |
|---|---:|---:|---:|---:|---:|
| visual M4 top5 | 110 | 0.0909 | 0.5000 | 0.5000 | 0.9091 |
| text B4 top5 | 110 | 0.1182 | 0.5364 | 0.5364 | 0.8818 |

이 결과는 두 가지를 분명히 보여준다.

1. 기존 전역 instance-VQA 검색은 답변 grounding 관점에서도 충분하지 않다.
2. 같은 class의 다른 사건을 rank-1 근거로 제시하는 위험이 매우 높다.

따라서 기존 전역 instance-VQA 결과는 논문에서 성능 주장으로 쓰면 안 된다. 대신 “class-level retrieval과 instance-level answer grounding은 다른 문제이며, DB가 이 차이를 노출하고 통제해야 한다”는 연구 질문의 근거로 사용한다.

## Corrected Task 1: Within-Event Evidence Selection

실제 CCTV VQA 서비스에서는 사용자가 현재 관측 중인 clip/session을 열어 질문하는 상황이 자연스럽다. 이 경우 target event/clip은 UI 또는 upstream detector가 제공하고, DB의 역할은 해당 clip 내부에서 LLM/VLM 답변에 쓸 frame/view/bbox/text evidence를 고르는 것이다.

정의:

| 항목 | 정의 |
|---|---|
| input | target clip/session id + Korean VQA-style event question |
| candidate set | 같은 clip의 label evidence frames + context distractor frames |
| positive | `extraction_strategy=label_evidence_frame` |
| negative | 같은 clip에서 추출한 `context_distractor_frame`, bbox 없음 |
| metrics | Hit@K, MRR, P@K, nDCG@K, positive view coverage |
| LLM 사용 | 아직 없음. evidence packet 품질 계층 평가 |

새 산출물:

- context frame root: `Datasets/processed/aihub_multi_angle_cctv/20260708/keyframes/evidence_context_stratified_event_split_5`
- SigLIP embedding: `Datasets/processed/aihub_multi_angle_cctv/20260708/visual_embeddings/siglip_evidence_context_stratified_event_split_5`
- CLIP embedding: `Datasets/processed/aihub_multi_angle_cctv/20260708/visual_embeddings/clip_vit_b32_evidence_context_stratified_event_split_5`
- SigLIP result: `Datasets/processed/aihub_multi_angle_cctv/20260708/results/within_event_evidence_selection_siglip_stratified_event_split_5`
- CLIP result: `Datasets/processed/aihub_multi_angle_cctv/20260708/results/within_event_evidence_selection_clip_vit_b32_stratified_event_split_5`
- model comparison: `Datasets/processed/aihub_multi_angle_cctv/20260708/results/within_event_model_comparison.csv`

Frame set:

| item | value |
|---|---:|
| clips | 110 |
| views | 220 |
| label evidence frames | 660 |
| context distractor frames | 880 |
| total frames | 1,540 |
| extraction errors | 0 |
| candidates/query | 14.0 |
| positives/query | 6.0 |

Within-event evidence selection 결과:

| model | strategy | queries | MRR | Hit@1 | Hit@3 | Hit@5 | P@3 | nDCG@5 | ViewCov@5 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| SigLIP base patch16-224 | random | 110 | 0.6702 | 0.4636 | 0.8818 | 0.9818 | 0.4515 | 0.4581 | 0.7909 |
| SigLIP base patch16-224 | visual text-frame | 110 | 0.7688 | 0.6182 | 0.9182 | 0.9909 | 0.5333 | 0.5077 | 0.6318 |
| SigLIP base patch16-224 | structured label oracle | 110 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| CLIP ViT-B/32 | random | 110 | 0.6702 | 0.4636 | 0.8818 | 0.9818 | 0.4515 | 0.4581 | 0.7909 |
| CLIP ViT-B/32 | visual text-frame | 110 | 0.7194 | 0.5364 | 0.8909 | 1.0000 | 0.4697 | 0.4523 | 0.5955 |
| CLIP ViT-B/32 | structured label oracle | 110 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |

해석:

- 같은 clip 내부 evidence selection에서는 visual embedding이 random보다 유의미한 신호를 제공한다.
- SigLIP이 CLIP ViT-B/32보다 Hit@1과 MRR에서 더 낫다.
- 그러나 후보 14개 중 positive가 6개라 random baseline도 높다. 따라서 이 실험도 “visual model 단독 해결” 주장이 아니라, evidence selection 계층의 제한적 신호와 구조화 label/evidence metadata의 필요성을 보여주는 보강 실험으로 사용한다.

## 논문에 반영할 최종 Claim

사용 가능한 claim:

- 도시 CCTV multi-view VQA 데이터는 event/video/frame/object/text/metadata가 결합된 evidence DB schema로 정규화할 수 있다.
- 전역 자연어 instance retrieval은 질의와 qrel 정의가 어긋나면 쉽게 ill-posed가 되며, 단순 Recall/MRR 개선은 candidate 축소 착시일 수 있다.
- generic CLIP/SigLIP cross-modal embedding은 한국어 CCTV event instance retrieval에서 취약하다.
- LLM/VLM 답변 품질을 높이려면 retrieval hit@K만 볼 것이 아니라, answer packet 안에 target frame/bbox/text evidence가 실제로 포함되는지 평가해야 한다.
- 실제 서비스형 VQA에서는 target clip/session이 주어진 상태에서 within-event evidence frame/view selection을 분리 평가해야 한다.
- DB-level schema, metadata filter, evidence packet, label-evidence indexing은 AI 답변 grounding 실패를 드러내고 통제하는 핵심 계층이다.

피해야 할 claim:

- “SigLIP visual retrieval이 도시 CCTV 사건 검색을 잘 해결했다.”
- “metadata-aware visual retrieval의 높은 R@10은 visual semantic understanding 개선을 뜻한다.”
- “전역 instance-VQA retrieval이 방어 가능한 최종 task다.”
- “text_metadata B4 성능만으로 멀티모달 답변 품질 향상을 입증했다.”

## 다음 우선순위

1. 원고의 task 정의를 `global class/event retrieval`, `answer-grounding packet evaluation`, `within-event evidence selection`으로 분리한다.
2. 기존 instance-VQA 전역 검색 수치는 실패/진단 결과로만 배치한다.
3. 본문 결과표는 answer-grounding과 within-event evidence selection을 중심으로 재구성한다.
4. 가능하면 후속 실험에서 candidate positive 비율을 낮추기 위해 context distractor frame 수를 view당 8~12개로 늘리는 sensitivity run을 추가한다.
5. 시간이 허용되면 실제 LLM answer layer는 evidence-only template 이후에 offline LLM/VLM judge가 아니라 rule-based grounding score를 우선 사용한다.
