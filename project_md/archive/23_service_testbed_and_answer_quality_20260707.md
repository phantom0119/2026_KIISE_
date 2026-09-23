# 서비스형 멀티모달 검색 테스트베드 및 AI 응답 품질 실험 체계

작성 기준일: 2026-07-07

2026-07-09 최신 갱신: 본 문서는 2026-07-07 기준 service-level evidence packet 구축과 evidence-only 응답 템플릿 결과를 기록한 것이다. 이후 fixed LLM answer control, AI Hub 다각도 CCTV 기반 fixed VLM answer control, 시내도로 CCTV index benchmark가 완료되었으므로 최신 전체 판정은 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다. 아래의 생성 모델 분리 원칙은 service packet 생성 단계에 한정된다.

## 목적

본 연구의 최종 목표는 단순히 멀티모달 데이터셋에서 retrieval score를 높이는 것이 아니다. 실제 도시 교통·감시형 멀티모달 데이터가 대량으로 축적되는 환경에서, 데이터베이스 수준의 저장·색인·검색 구조가 AI 응답 품질과 근거 충실도에 어떤 영향을 주는지 밝히는 것이다.

이를 위해 기존 retrieval 결과를 서비스형 테스트베드의 응답 단위로 변환하였다.

```text
query(text/image + optional metadata)
  -> M6 or IM1 retrieval
  -> evidence packet
     - clip_id
     - frame_id
     - timestamp_sec
     - thumbnail_path
     - media_path
     - supporting_text
     - metadata
     - text/visual/fusion scores
  -> answer-ready context
  -> evidence-only extractive answer template
```

이 2026-07-07 service packet 생성 단계에서는 생성 모델을 호출하지 않는다. 이유는 검색 구조의 품질과 생성 모델 품질을 먼저 분리해야 하기 때문이다. 최신 원고에서는 이 분리 위에 fixed LLM/VLM answer-level 통제 실험을 추가하여, 모델을 고정한 상태에서 DB evidence 구성만 바꾸는 효과를 평가한다.

## 구현 산출물

| 항목 | 경로 |
|---|---|
| 스크립트 | `2026_KIISE/scripts/build_service_testbed_packets.py` |
| VRU service packets | `Datasets/processed/vru_accident/20260706/service_testbed/m6_im1_top5` |
| AI Hub CCTV service packets | `Datasets/processed/aihub_intelligent_cctv/20260706/service_testbed/m6_im1_top5` |

각 output directory에는 다음 파일이 생성된다.

| 파일 | 설명 |
|---|---|
| `service_packets.jsonl` | 요청, top-k evidence, answer context, extractive answer contract |
| `service_evidence_rows.parquet` | evidence row 단위 분석용 테이블 |
| `service_packet_summary.csv` | query type별 품질 요약 |
| `summary.md` | 사람이 읽는 요약 |
| `run_manifest.json` | 입력 경로, 전략, top-k, service packet 단계의 evidence-only 정책 |

추가로 text/visual RRF 가중치에 따른 evidence selection 성능을 평가하기 위해 다음 산출물을 생성했다.

| 항목 | 경로 |
|---|---|
| rerank sweep script | `2026_KIISE/scripts/run_weighted_fusion_rerank_sweep.py` |
| VRU rerank sweep | `Datasets/processed/vru_accident/20260706/results/weighted_fusion_rerank_sweep_bgem3_clip` |
| AI Hub rerank sweep | `Datasets/processed/aihub_intelligent_cctv/20260706/results/weighted_fusion_rerank_sweep_bgem3_clip` |
| VRU reranked service packets | `Datasets/processed/vru_accident/20260706/service_testbed/rw_t4_v1_im1_top5` |
| AI Hub reranked service packets | `Datasets/processed/aihub_intelligent_cctv/20260706/service_testbed/rw_t4_v1_im1_top5` |

## 서비스 응답 스키마

`service_packets.jsonl`의 각 record는 다음 구조다.

| 필드 | 설명 |
|---|---|
| `request` | query id, query type, query text/image path, metadata filter |
| `evidence` | top-k 검색 결과의 clip/frame/text/metadata evidence |
| `answer_context` | LLM 또는 후처리 모델에 넘길 수 있는 evidence-only context |
| `extractive_answer` | rank-1 evidence 기반 template answer |
| `service_contract` | service packet 단계의 evidence-only 정책 |

핵심은 AI가 답변을 생성하기 전 데이터베이스가 어떤 evidence를 공급했는지 완전히 추적 가능하게 만드는 것이다.

## 실행 결과

### VRU-Accident

| Query type | Requests | Top-1 relevant | Hit@5 | Frame coverage | Timestamp coverage | Supporting text coverage |
|---|---:|---:|---:|---:|---:|---:|
| text_metadata | 244 | 0.7131 | 0.8770 | 0.9884 | 0.9884 | 1.0000 |
| image | 1,000 | 0.7550 | 0.9660 | 1.0000 | 1.0000 | 1.0000 |
| all | 1,244 | 0.7468 | 0.9486 | 0.9977 | 0.9977 | 1.0000 |

### AI Hub 지능형 CCTV

| Query type | Requests | Top-1 relevant | Hit@5 | Frame coverage | Timestamp coverage | Supporting text coverage |
|---|---:|---:|---:|---:|---:|---:|
| text_metadata | 133 | 0.9248 | 0.9774 | 1.0000 | 1.0000 | 1.0000 |
| image | 269 | 0.8810 | 0.9851 | 1.0000 | 1.0000 | 1.0000 |
| all | 402 | 0.8955 | 0.9826 | 1.0000 | 1.0000 | 1.0000 |

## Evidence selection reranking 결과

M6 equal fusion은 text evidence rank와 visual frame rank를 같은 가중치로 결합한다. 하지만 서비스 답변은 보통 rank-1 evidence에 크게 의존하므로, top-k hit보다 top-1 relevant rate가 더 직접적인 answer quality proxy다.

가중치 sweep 결과, 두 데이터셋 모두 `text_weight:visual_weight = 4:1`이 가장 높은 top-1 품질을 보였다.

### Rerank sweep summary

| Dataset | Strategy | Hit@1 | Hit@5 | Recall@10 | MRR | nDCG@10 |
|---|---|---:|---:|---:|---:|---:|
| VRU | equal M6 `1:1` | 0.7131 | 0.8770 | 0.4928 | 0.7837 | 0.6232 |
| VRU | reranked `4:1` | 0.8443 | 0.9672 | 0.7289 | 0.8966 | 0.8847 |
| AI Hub CCTV | equal M6 `1:1` | 0.9248 | 0.9774 | 0.8016 | 0.9469 | 0.8951 |
| AI Hub CCTV | reranked `4:1` | 0.9699 | 1.0000 | 0.8563 | 0.9812 | 0.9768 |

### Reranked service packet summary

| Dataset | Query type | Top-1 relevant | Hit@5 | Frame coverage | Supporting text coverage |
|---|---|---:|---:|---:|---:|
| VRU | text_metadata | 0.8443 | 0.9672 | 1.0000 | 1.0000 |
| VRU | all | 0.7725 | 0.9662 | 1.0000 | 1.0000 |
| AI Hub CCTV | text_metadata | 0.9699 | 1.0000 | 1.0000 | 1.0000 |
| AI Hub CCTV | all | 0.9104 | 0.9900 | 1.0000 | 1.0000 |

해석:

- text-heavy rerank가 좋은 이유는 현재 qrels와 질의가 event/caption/metadata 의미에 강하게 정렬되어 있기 때문이다.
- 그러나 visual evidence는 여전히 필요하다. 서비스 응답에는 frame/timestamp/thumbnail이 필요하고, image-to-video query는 visual index 없이는 수행할 수 없다.
- text-heavy rerank로 인해 visual top list에 없던 clip이 상위로 올라올 수 있으므로, 서비스 패킷 생성 단계에서는 `fallback_clip_representative` frame을 제공한다.
- fallback은 서비스 completeness를 위한 장치이지, visual retrieval evidence와 동일한 의미로 해석하면 안 된다.

## 핵심 통찰

### 1. Retrieval Hit@K와 AI 답변 품질은 같은 문제가 아니다

VRU는 Hit@5가 0.9486으로 높지만, top-1 relevant rate는 0.7468이다. 만약 LLM이 rank-1 evidence만 보고 답변한다면, top-k 안에 정답이 있더라도 답변은 틀릴 수 있다.

Reranking sweep 결과는 이 문제를 더 명확히 보여준다. VRU text query에서 equal fusion의 top-1 relevant rate는 0.7131이었지만, 단순한 RRF weight 조정만으로 0.8443까지 개선되었다. 즉, AI 응답 품질을 높이려면 단순 Recall@K뿐 아니라 다음 문제가 중요하다.

- top-k 후보를 어떻게 재정렬할 것인가
- 어떤 evidence를 LLM context에 넣을 것인가
- LLM이 rank-1만 신뢰할지, top-k evidence를 비교하도록 할지
- metadata constraint를 답변 검증 단계에서 다시 확인할지

### 2. Evidence completeness는 서비스화의 최소 조건이다

두 데이터셋 모두 frame/timestamp/supporting text coverage가 거의 1.0에 도달했다. 이는 검색 결과를 단순 clip ID가 아니라 실제 서비스 응답에 필요한 근거 단위로 반환할 수 있음을 의미한다.

하지만 completeness가 높다고 correctness가 보장되지는 않는다. 따라서 다음 단계는 evidence completeness가 아니라 evidence selection accuracy를 높이는 것이다.

### 3. 데이터베이스 연구의 기여 지점은 LLM 이전에 존재한다

LLM은 evidence를 생성하지 않는다. LLM은 DB가 공급한 evidence를 사용해 답변을 구성한다. 따라서 대량 멀티모달 환경에서 AI 응답 정확도를 높이는 DB 연구는 다음 계층에서 이루어져야 한다.

| 계층 | 연구 문제 |
|---|---|
| Storage | 영상, 프레임, 텍스트, metadata를 어떤 단위로 저장할 것인가 |
| Indexing | visual/text vector와 structured metadata를 어떻게 함께 색인할 것인가 |
| Query planning | prefilter, postfilter, fusion, rerank 순서를 어떻게 정할 것인가 |
| Evidence selection | top-k 중 어떤 frame/text를 answer context에 넣을 것인가 |
| Answer grounding | 답변이 사용한 evidence가 실제 검색 결과와 일치하는지 어떻게 검증할 것인가 |

## 다음 실험 우선순위

### Priority 1: Evidence selection/reranking

현재 가장 중요한 추가 실험은 LLM을 붙이는 것이 아니라, top-k evidence 중 rank-1 선택 품질을 높이는 것이다. 1차 실험으로 weighted RRF sweep은 완료되었고, text-heavy `4:1`이 현재 최선이다.

후보:

1. metadata consistency rerank
2. text evidence score + visual score calibrated rerank
3. query-type별 동적 가중치 조정
4. top-k evidence diversity 제약
5. lightweight cross-encoder/reranker 적용

평가:

- Top-1 relevant rate
- Hit@5
- nDCG@10
- evidence completeness
- latency overhead

### Priority 2: Controlled LLM/VLM answer layer

2026-07-09 기준으로 이 후속 단계는 완료되었다. 핵심 원칙은 2026-07-07 설계와 동일하게 유지했다. 즉, 모델 비교가 아니라 DB evidence 구성의 효과를 보기 위해 생성 모델은 고정하고 입력 evidence만 바꾸었다.

- 입력은 `service_packets.jsonl`의 evidence context로 제한
- 답변은 evidence citation을 포함
- evidence 밖의 주장은 금지
- 평가 지표는 answer accuracy, citation correctness, hallucination rate

LLM answer layer에서는 Qwen2.5-7B와 Llama-3-8B를 고정하고 closed-book, vector evidence, metadata-prefilter evidence, oracle evidence를 비교했다. VLM answer layer에서는 AI Hub 다각도 CCTV 400 clip stratum에서 Qwen2.5-VL, Qwen2-VL, InternVL3-8B, Idefics2-8b를 사용해 better-view, worse-view, both-view evidence 조건을 비교했다. 최신 해석은 `38_four_vlm_multiview_final_recheck_20260709.md`를 따른다.

### Priority 3: Backend integration

현재 service packet은 offline replay 방식이다. 상용형 테스트베드로 더 가까워지려면 다음을 추가한다.

- visual frame embeddings를 pgvector 또는 전용 vector DB에 적재
- text evidence embeddings와 visual embeddings를 별도 collection/table로 관리
- metadata는 relational table로 관리
- query planner가 metadata candidate set을 생성하고 vector search에 연결

## 논문 반영 문장

사용 가능한 핵심 주장:

> 본 연구는 도시 감시형 멀티모달 데이터에서 검색 결과를 clip ranking으로 끝내지 않고, frame, timestamp, thumbnail, supporting text를 포함하는 service-level evidence packet으로 변환하였다. 실험 결과, top-k retrieval 성능이 높더라도 rank-1 evidence 선택 오류가 AI 응답 품질 저하로 이어질 수 있음을 확인하였다. 이는 대량 멀티모달 데이터 환경에서 AI 응답 품질 개선이 LLM 자체보다 데이터베이스 수준의 evidence retrieval 및 selection 구조에 크게 의존함을 시사한다.

## 현재 판단

현재 연구는 다음 단계까지 성립했다.

- true multimodal retrieval testbed: 완료
- service-level evidence packet: 완료
- answer-ready context: 완료
- evidence-only answer template: 완료
- fixed LLM answer-level control: 완료
- fixed VLM multi-view answer-level control: 완료

아직 완료되지 않았거나 후속 확장으로 남긴 단계:

- learned reranker
- online API
- end-to-end DB backend 통합 시각 vector search
- open-ended generation의 citation correctness/hallucination rate 평가

최신 투고 기준에서는 service packet과 weighted RRF 결과를 retrieval/evidence-selection 근거로 두고, fixed LLM/VLM answer-level 결과는 DB evidence 품질이 실제 답변 정확도에 미치는 영향을 보이는 통제 실험으로 사용한다.
