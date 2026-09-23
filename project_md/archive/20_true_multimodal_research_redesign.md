# True Multimodal Retrieval 연구 재설계

작성 기준일: 2026-07-07

2026-07-09 최신 갱신: 이 재설계는 실행 완료되었다. VRU와 AI Hub 지능형 CCTV에서 keyframe visual embedding, text-to-video, image-to-video, fusion, service packet이 생성되었고, 이후 fixed LLM/VLM answer-level 및 시내도로 CCTV index benchmark까지 확장되었다. 최신 실행 결과는 `21_true_multimodal_execution_status_20260707.md`, `38_four_vlm_multiview_final_recheck_20260709.md`, `39_index_structure_benchmark_results_20260709.md`, `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 결론

기존 실험은 멀티모달 데이터셋의 영상 원본을 보존했지만, 실제 검색 표현은 `text evidence + metadata` 중심이었다. 따라서 실제 상용형 “멀티모달 데이터셋 기반 검색 서비스”를 연구한다고 주장하기에는 부족하다.

본 연구는 즉시 다음 방향으로 재설계한다.

> 도시 감시형 영상 데이터에서 keyframe/segment visual embedding, text evidence embedding, 구조화 metadata를 함께 색인하고, text-to-video, image-to-video, text+metadata-to-video, multimodal hybrid 검색 구조를 비교한다.

기존 B0-B5 결과는 폐기하지 않는다. 다만 역할을 다음으로 낮춘다.

| 기존 결과 | 새 역할 |
|---|---|
| BM25/text embedding/metadata B0-B5 | text+metadata retrieval baseline |
| pgvector P2/P4 | metadata prefilter query processing baseline |
| AI Hub 이상행동 CCTV 결과 | label-aligned text/metadata 보조 분석 |

새 main claim은 반드시 visual embedding을 포함해야 한다.

## 기존 설계의 문제

| 항목 | 기존 설계 | 문제 |
|---|---|---|
| 영상 활용 | media path 보존 | 검색 representation에는 영상 시각 정보가 직접 들어가지 않음 |
| embedding | text document/query embedding | image/video embedding 없음 |
| query | text + metadata | image query 또는 multimodal query 없음 |
| 결과 | clip ranking | evidence frame/timestamp/thumbnail 없음 |
| LLM/VLM | 사용 안 함 | 상용 VLM 검색 서비스와 직접 대응 약함 |
| 논문 표현 | 멀티모달 DB retrieval | 실제로는 text-evidence retrieval에 가까움 |

따라서 “진정한 멀티모달 검색”을 위해서는 최소한 visual frame embedding과 image/text-to-video retrieval이 필요하다.

## 새 연구 질문

RQ1. 도시 감시형 영상 데이터에서 visual embedding 기반 text-to-video 검색은 text-evidence 검색과 어떤 차이를 보이는가?

RQ2. metadata prefilter는 visual vector search에서도 vector-only보다 관련 evidence clip/frame을 안정적으로 찾는가?

RQ3. text evidence, visual frame, metadata를 결합한 hybrid retrieval은 단일 modality 검색보다 나은 recall/grounding/latency 균형을 보이는가?

RQ4. 상용형 검색 서비스 관점에서 검색 결과를 clip ID가 아니라 frame/timestamp/thumbnail/evidence text와 함께 반환할 수 있는가?

## 새 canonical schema

기존 schema에 visual artifact를 추가한다.

| artifact | 상태 | 설명 |
|---|---|---|
| `clips.parquet` | 유지 | clip-level media path |
| `documents.parquet` | 유지 | caption, VQA, event/action text |
| `metadata.parquet` | 유지 | 구조화 facet |
| `queries.jsonl` | 확장 | text query, optional image query, metadata filter |
| `qrels.tsv` | 확장 | clip-level과 frame/segment-level relevance |
| `frames.parquet` | 신규 | 추출 frame의 path, timestamp, frame index |
| `visual_embeddings.npy` | 신규 | frame/keyframe visual embedding |
| `visual_index.parquet` | 신규 | frame_id, clip_id, timestamp, frame path |
| `multimodal_queries.jsonl` | 신규 | text-only, image-only, text+metadata, image+metadata, text+image+metadata query |

## 데이터셋 재판정

| 데이터셋 | true multimodal 적합성 | 즉시 사용 여부 | 이유 |
|---|---|---|---|
| VRU-Accident | 높음 | main | mp4 1,000개, dense caption/VQA/qrels 있음 |
| AI Hub 지능형 CCTV | 높음 | extension | mp4 269개, event frame 정보 있음 |
| AI Hub 이상행동 CCTV | 중간 | optional/subset | zip 내부 mp4, XML event segment 있음. 처리 비용 큼 |
| WTS | 높음 | 향후/승인 필요 | multi-view traffic safety, caption/VQA 가능 |
| TUMTraffic-VideoQA | 높음 | 향후/등록 필요 | roadside video QA benchmark |
| AI Hub 522 교차로 복합 | 중간~높음 | 향후 | 정형 교통 로그 보강에 유리 |

즉시 투입 가능한 true multimodal main track은 `VRU-Accident + AI Hub 지능형 CCTV`다. AI Hub 이상행동 CCTV는 zip-aware extraction을 구현하면 추가 가능하지만, 1차 재설계의 필수 경로로 두지 않는다.

## 모델 선택

최소 실행 모델:

| 역할 | 후보 | 이유 |
|---|---|---|
| visual-text embedding | `openai/clip-vit-base-patch32` 또는 `google/siglip-base-patch16-224` | text/image를 같은 공간에 embedding 가능 |
| text evidence embedding | 기존 `bge-m3`, `e5-large-v2` | 기존 baseline 유지 |
| optional VLM rerank/caption | Qwen2.5-VL, InternVL 계열 | 시간이 남을 때만 사용 |

2주 일정 기준 최소 선택:

1. 먼저 CLIP/SigLIP 계열 중 하나를 로컬에 확보한다.
2. keyframe visual embedding을 생성한다.
3. text query를 같은 visual-text embedding space에 넣어 visual frame search를 수행한다.
4. image query는 추출된 keyframe을 query image로 사용하는 self-retrieval/near-duplicate task부터 시작한다.

VLM answer generation은 이번 main experiment에서 제외한다. 이유는 모델 답변 품질이 DB 검색 구조의 기여를 흐릴 수 있기 때문이다.

## 새 검색 전략

기존 B0-B5를 다음처럼 확장한다.

| ID | 이름 | 검색 대상 | 설명 |
|---|---|---|---|
| M0 | Metadata-only | metadata | 조건 만족 clip/frame 반환 |
| M1 | Text evidence sparse/dense | documents | 기존 BM25/text embedding baseline |
| M2 | Visual vector-only | frames | text query 또는 image query로 frame visual index 검색 |
| M3 | Visual postfilter | frames + metadata | visual top-N 후 metadata filter |
| M4 | Metadata prefilter + visual | metadata + frames | metadata 후보 clip의 frame만 visual ranking |
| M5 | Text+visual hybrid | documents + frames | text evidence rank와 visual rank 결합 |
| M6 | Text+visual+metadata hybrid | all | metadata prefilter 후 text/visual fusion |

상용 서비스에 가장 가까운 구조는 M6다.

```text
query(text/image + filters)
  -> metadata candidate selection
  -> visual frame retrieval
  -> text evidence retrieval
  -> score fusion
  -> clip/frame/timestamp/thumbnail/snippet 반환
```

## 검색 결과 형식

기존 결과는 `clip_id` ranking이었다. 새 결과는 다음을 반환해야 한다.

| 필드 | 설명 |
|---|---|
| `rank` | 검색 순위 |
| `clip_id` | 영상 클립 |
| `frame_id` | 대표 evidence frame |
| `timestamp_sec` | frame timestamp |
| `thumbnail_path` | 확인 가능한 이미지 |
| `visual_score` | visual embedding score |
| `text_score` | text evidence score |
| `metadata_match` | metadata 조건 만족 여부 |
| `fusion_score` | 최종 점수 |
| `supporting_text` | caption/event/VQA evidence |

이 형식이어야 상용형 멀티모달 검색 서비스 설명에 부합한다.

## 평가 지표

기존 retrieval metric은 유지하되, visual grounding 지표를 추가한다.

| 지표 | 대상 |
|---|---|
| Recall@K | relevant clip 검색 여부 |
| nDCG@10 | ranking quality |
| MRR | 첫 relevant clip 순위 |
| Frame Hit@K | relevant clip 내부 evidence frame 포함 여부 |
| Timestamp error | event frame/time annotation이 있는 데이터셋 |
| Metadata satisfaction rate | top-k 결과가 filter 조건을 만족하는 비율 |
| Latency | query 처리 시간 |

AI Hub 지능형 CCTV는 `event_start_frame`, `event_end_frame`이 있어 frame/segment-level grounding 평가에 가장 유리하다.

## 최소 실행 계획

### Phase 1: VRU true multimodal pilot

목표: 1일 이내 visual retrieval 결과 확보

작업:

1. VRU 1,000개 mp4에서 clip당 4~8개 keyframe 추출
2. CLIP/SigLIP visual embedding 생성
3. 기존 text query를 visual-text model의 text encoder로 embedding
4. M2 visual vector-only 검색
5. M4 metadata prefilter + visual 검색
6. 기존 B2/B4 text baseline과 비교

판정:

- M4가 M2보다 metadata satisfaction과 nDCG@10을 개선하면 true multimodal main claim 가능
- M2 자체가 낮더라도 의미 있음. visual-only의 한계와 text evidence/metadata hybrid 필요성을 보여줄 수 있음

### Phase 2: AI Hub 지능형 CCTV event-frame grounding

목표: 상용 CCTV 검색 서비스에 더 가까운 evidence frame 반환

작업:

1. event_start/end 중심 frame 추출
2. event caption/text query와 visual frame 검색 비교
3. top-k result에 frame timestamp와 thumbnail 포함
4. event segment 안의 frame이 검색되는지 평가

판정:

- 이 결과가 확보되면 “clip ID 검색”을 넘어 evidence frame 검색으로 설명 가능

### Phase 3: AI Hub 이상행동 CCTV optional

목표: 국내 이상행동 CCTV 확장

작업:

1. zip-aware frame extraction 구현 또는 subset 추출
2. 12개 event class별 균형 subset 구성
3. event_starttime 중심 frame 추출

판정:

- 시간이 부족하면 본문 확장에 넣지 않고 appendix 또는 향후 연구로 둔다.

## 추가 데이터셋 필요성 재판정

true multimodal search로 바꾸더라도, 즉시 추가 데이터셋이 필수는 아니다. 로컬에 실제 mp4가 이미 있기 때문이다.

하지만 아래 주장을 넣으려면 추가 데이터셋이 필요하다.

| 넣고 싶은 주장 | 필요한 데이터셋 |
|---|---|
| roadside traffic video QA와 국제 비교 | TUMTraffic-VideoQA, WTS |
| multi-view CCTV search | WTS 또는 AI Hub 다각도 CCTV |
| sensor log + video fusion | AI Hub 522 교차로 복합 |
| image query benchmark | keyframe qrels가 있는 데이터셋 또는 직접 image query 생성 |

2주 일정에서는 새 데이터셋 확보보다 로컬 mp4 기반 visual retrieval track을 먼저 완성해야 한다.

## 기존 원고 수정 방향

반드시 수정:

- “현재 실험은 text evidence + metadata baseline”이라고 명시
- visual embedding track을 main 또는 new experiment로 추가
- 멀티모달 검색 결과를 clip/frame/timestamp/thumbnail로 설명
- LLM/VLM answer generation은 downstream optional로 유지

삭제/완화:

- 기존 text-only 결과만으로 “멀티모달 검색 구조”를 입증했다는 표현
- AI Hub 이상행동 CCTV를 main traffic dataset처럼 보이는 표현
- 실제 상용 서비스와 동일하다는 과장

새 제목 후보:

> 도시 감시형 영상 데이터베이스에서 시각-텍스트-메타데이터 하이브리드 검색 구조의 성능 분석

영문:

> Performance Analysis of Visual-Text-Metadata Hybrid Retrieval for Urban Surveillance Video Databases

## 최종 방침

1. 기존 결과는 text/metadata baseline으로 유지한다.
2. true multimodal main track은 visual keyframe embedding을 포함해 새로 구성한다.
3. 1차 데이터셋은 VRU-Accident와 AI Hub 지능형 CCTV로 고정한다.
4. AI Hub 이상행동 CCTV는 zip 처리 비용 때문에 optional 확장으로 둔다.
5. 지금부터 원고와 발표 자료는 `visual-text-metadata hybrid retrieval` 중심으로 재작성한다.

## 2026-07-07 실행 반영

위 재설계는 다음 산출물로 1차 실행 완료되었다.

| Dataset | Keyframes | Visual embedding | Text-to-video | Fusion | Image-to-video |
|---|---:|---|---|---|---|
| VRU-Accident | 4,000 / 1,000 clips | CLIP ViT-B/32 | M2/M4 완료 | M5/M6 완료 | IM1 완료 |
| AI Hub 지능형 CCTV | 1,076 / 269 clips | CLIP ViT-B/32 | M2/M4 완료 | M5/M6 완료 | IM1 완료 |

주요 경로와 결과 해석은 `2026_KIISE/project_md/21_true_multimodal_execution_status_20260707.md`를 기준으로 한다.

중요한 수정 사항:

- B0-B5는 더 이상 main multimodal experiment가 아니라 text/metadata baseline이다.
- M2/M4는 텍스트 질의가 시각 프레임 인덱스를 직접 검색하는 true multimodal text-to-video track이다.
- IM1은 이미지 질의가 영상 DB를 검색하는 image-to-video track이다.
- M6는 상용형 구조에 가장 가깝지만, 모든 metric에서 text-only B5보다 항상 좋아진다고 주장하지 않는다.
