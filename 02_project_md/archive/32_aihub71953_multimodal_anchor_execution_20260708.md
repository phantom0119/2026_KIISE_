# AI Hub 71953 Multimodal Anchor Execution

작성 기준일: 2026-07-08

2026-07-08 정정: 이 문서의 초기 검색 성능 해석은 후속 피드백 검토 후 일부 폐기/격하되었다. 특히 `instance_vqa` 전역 검색은 질의가 target clip을 식별하지 못하는 ill-posed task이며, SigLIP visual-only 검색은 near-random에 가까운 진단 결과로 해석해야 한다. 최종 논문 claim과 보강 실험 체계는 `34_feedback_response_and_corrected_experiment_design_20260708.md`를 우선한다.

2026-07-08 후속 갱신: 초기 50-event diagnostic result는 계층화 표본 설계 전의 sanity check로만 유지한다. 논문 실험 체계의 기준 결과는 `33_experiment_scaling_and_control_plan_20260708.md`의 T1 stratified diagnostic subset, 즉 event_class x source_split 22개 strata에서 각 5개씩 뽑은 110-event 결과를 우선 사용한다.

2026-07-09 최신 갱신: 본 문서는 AI Hub 71953을 evidence DB로 편입한 실행 기록으로 보존한다. 최종 논문 claim은 더 이상 50-event 또는 T1 global instance retrieval 수치에 의존하지 않고, `35_multiview_answer_level_prereg_20260708.md`로 사전등록한 400-clip answer-level VLM 실험과 `38_four_vlm_multiview_final_recheck_20260709.md`의 4-VLM 재검증을 따른다. 최신 종합은 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 기준으로 한다.

## 연구 주제 이해와 최종 청사진

본 연구의 주제는 **도시 CCTV/교통 멀티모달 데이터에서 LLM/VLM 응답 품질을 높이기 위한 데이터베이스 수준의 evidence retrieval 구조**이다.

핵심 질문은 다음이다.

1. 영상, 프레임, 자연어 질의, VQA/CoT, 객체 bbox, 시간/카메라 메타데이터를 하나의 evidence database schema로 정규화할 수 있는가?
2. 단순 vector-only 검색보다 metadata prefilter, evidence packet, view-aware evidence selection이 검색 품질과 답변 근거성을 개선하는가?
3. LLM이 답을 잘하게 만드는 핵심 병목이 LLM 자체가 아니라, DB가 어떤 frame/object/text evidence를 골라 공급하느냐에 있는가?

본 연구가 제안하는 청사진은 **Multimodal Evidence Database for Urban CCTV Retrieval**이다. 논문에서는 과도한 “세계 최초” 표현 대신, 다음처럼 방어 가능한 신규성으로 쓴다.

> 본 연구는 국내 도시 CCTV/생활안전/교통 공개 데이터셋을 대상으로 multi-view VQA evidence, visual frame evidence, structured metadata를 통합한 DB-level retrieval testbed와 평가 절차를 제안한다.

## 왜 AI Hub 71953이 Main Anchor인가

AI Hub 71953 다각도 CCTV 생활안전 데이터는 본 연구의 “멀티모달” 요건을 가장 강하게 만족한다.

| 요건 | 데이터 내 근거 |
|---|---|
| multi-view video | event마다 `c1`, `c2` 두 CCTV view |
| natural language query | label JSON의 `question` |
| answer target | label JSON의 `answer` |
| reasoning text | view별 `caption`과 `cot` |
| visual grounding | `frame_id`, `obj_id`, `obj_bbox`, `obj_label` |
| DB filter | event class, split, date, time bucket, camera, angle, distribution |
| service evidence | frame thumbnail, bbox, supporting text, metadata packet 생성 가능 |

따라서 이 데이터셋은 optional extension이 아니라 본 연구의 main multimodal anchor이다.

## 구현 완료 산출물

### 1. Canonical Adapter

추가 구현:

- `2026_KIISE/src/vlmdb_workload/adapters/aihub_multi_angle_cctv.py`
- `2026_KIISE/scripts/build_aihub_multi_angle_cctv_canonical.py`

산출물:

- `Datasets/processed/aihub_multi_angle_cctv/20260708/canonical`

| artifact | count |
|---|---:|
| clips/event | 4,500 |
| views/video | 9,000 |
| evidence frame rows | 27,000 |
| documents | 36,000 |
| metadata rows | 63,000 |
| queries | 4,572 |
| qrels | 18,000 |
| missing media entries | 0 |

중요한 설계 결정:

- `clips.parquet`: event 단위
- `views.parquet`: `c1/c2` view별 mp4 `zip://...!entry` URI
- `evidence_frames.parquet`: frame/object/bbox grounding 단위
- 원본 mp4는 full unzip하지 않고 필요한 evidence frame만 materialize
- label question은 query로 쓰되, question text는 document에 넣지 않아 query leakage를 줄임

### 2. Evidence Frame Materialization

추가 구현:

- `2026_KIISE/scripts/materialize_aihub_multi_angle_evidence_frames.py`

산출물:

- `Datasets/processed/aihub_multi_angle_cctv/20260708/keyframes/evidence_sample_50`

| item | value |
|---|---:|
| clips with frames | 50 |
| views with frames | 100 |
| frames | 300 |
| errors | 0 |
| missing frame files | 0 |

주의: 이 단계는 전체 27,000 frame을 모두 추출한 것이 아니라, 검증 가능한 50-event sample을 materialize한 것이다. 논문 최종 수치로 쓰려면 sample size를 명시하거나 더 큰 sample을 추가 실행한다.

### 3. Pipeline Audit

추가 구현:

- `2026_KIISE/scripts/audit_aihub_multi_angle_cctv_pipeline.py`

산출물:

- `2026_KIISE/paper_assets/20260708_aihub71953_pipeline_audit`

| check | errors |
|---|---:|
| qrel target errors | 0 |
| qrel query errors | 0 |
| missing two views | 0 |
| missing c1/c2 view pairs | 0 |
| low evidence pairs | 0 |
| missing filter facets | 0 |
| empty filter candidates | 0 |
| positive not in filter | 0 |

Audit pass: `True`

### 4. Text Retrieval Baseline

산출물:

- embedding: `Datasets/processed/aihub_multi_angle_cctv/20260708/embeddings/bge-m3`
- retrieval: `Datasets/processed/aihub_multi_angle_cctv/20260708/results/bgem3_faiss_b0_b5_sampled50`

Embedding:

| item | value |
|---|---:|
| documents | 36,000 |
| queries | 4,572 |
| embedding dim | 1,024 |
| model | BAAI/bge-m3 |

Retrieval 표본:

| item | value |
|---|---:|
| executed queries | 122 |
| max queries per difficulty | 50 |
| result rows | 35,727 |

Overall metrics:

| strategy | R@10 | R@20 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|
| B0 metadata-only | 0.0867 | 0.1734 | 0.0944 | 0.0946 |
| B1 BM25-only | 0.0927 | 0.1853 | 0.1600 | 0.1602 |
| B2 vector-only | 0.1290 | 0.1736 | 0.3550 | 0.3210 |
| B3 vector postfilter | 0.1942 | 0.2774 | 0.6271 | 0.6370 |
| B4 prefilter+vector | 0.1999 | 0.2928 | 0.6271 | 0.6413 |
| B5 hybrid | 0.1554 | 0.2929 | 0.4109 | 0.3864 |

해석: 다각도 CCTV에서는 metadata-aware vector retrieval이 vector-only보다 더 강하다. 특히 B4는 nDCG@10 기준 B2 대비 약 2배 수준으로 높다. 이는 본 연구의 DB-level prefilter 주장을 뒷받침한다.

### 5. Visual Retrieval Baseline

추가 구현:

- `2026_KIISE/scripts/build_canonical_subset_from_frames.py`

산출물:

- subset canonical: `Datasets/processed/aihub_multi_angle_cctv/20260708/canonical_evidence_sample_50`
- visual embedding: `Datasets/processed/aihub_multi_angle_cctv/20260708/visual_embeddings/siglip_evidence_sample_50`
- visual retrieval: `Datasets/processed/aihub_multi_angle_cctv/20260708/results/visual_siglip_evidence_sample_50_m2_m4`

Subset:

| item | value |
|---|---:|
| subset clips | 50 |
| frames | 300 |
| documents | 400 |
| metadata rows | 700 |
| queries | 55 |
| qrels | 200 |

Visual embedding:

| item | value |
|---|---:|
| model | SigLIP base patch16-224 |
| frame embeddings | 300 |
| query text embeddings | 55 |
| embedding dim | 768 |

Visual retrieval metrics:

| strategy | R@10 | R@20 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|
| M2 visual vector-only | 0.1649 | 0.4231 | 0.1232 | 0.1079 |
| M4 metadata-prefilter visual | 0.1864 | 0.4456 | 0.1468 | 0.1426 |

해석: visual-only 검색에서도 metadata prefilter가 R@10, R@20, MRR, nDCG@10을 모두 개선했다. 수치 자체는 50-event sample의 sanity result로 해석해야 하지만, 실제 frame-level multimodal retrieval이 동작함은 확인했다.

### 6. Service Evidence Packet

추가 구현:

- `2026_KIISE/scripts/build_aihub_multi_angle_service_packets.py`

산출물:

- `Datasets/processed/aihub_multi_angle_cctv/20260708/service_testbed/visual_m4_top5_evidence_sample_50`

| item | value |
|---|---:|
| packets | 55 |
| evidence rows | 273 |
| top-k hit rate | 0.1091 |
| top-1 relevant rate | 0.0909 |

각 service packet은 다음을 포함한다.

- request/query
- metadata filter
- top-k evidence
- clip id
- view
- frame id/index
- thumbnail path
- media `zip://` URI
- object id/label/bbox
- evidence text
- supporting document
- answer context
- evidence-only extractive answer contract

이 산출물은 “LLM이 답을 생성하기 전에 DB가 어떤 evidence를 공급했는가”를 재현 가능하게 남긴다.

## 현재 결론

현재까지 가장 중요한 결론은 다음이다.

1. 다각도 CCTV는 본 연구의 main multimodal anchor로 정상 편입됐다.
2. event-level, view-level, frame/object-level evidence schema가 모두 구축됐다.
3. source mp4를 full unzip하지 않고도 `zip://` URI와 selective frame materialization으로 실험 가능하다.
4. text retrieval과 visual retrieval 모두에서 metadata-aware retrieval이 vector-only보다 개선되는 경향을 보였다.
5. 검색 결과를 service evidence packet으로 변환해 LLM/VLM answer grounding 실험의 입력 단위까지 만들었다.

## 아직 최종 본문 수치로 쓰기 전 주의할 점

- visual retrieval 결과는 50-event sample이다. 본문 최종 수치로 쓰려면 sample size를 명시하거나 200/500-event sample을 추가 실행한다.
- text retrieval은 122-query sampled run이다. 전체 4,572-query run은 시간이 오래 걸리므로 장시간 작업으로 재실행하는 편이 좋다.
- service packet의 top-k hit rate는 visual M4 sample 기준이므로, text+visual fusion packet과 비교하면 더 설득력이 생긴다.

## 재실행 명령

전체 canonical:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_aihub_multi_angle_cctv_canonical.py --dataset-version 20260708 --overwrite
```

50-event evidence frame:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/materialize_aihub_multi_angle_evidence_frames.py \
  --canonical-root Datasets/processed/aihub_multi_angle_cctv/20260708/canonical \
  --output-dir Datasets/processed/aihub_multi_angle_cctv/20260708/keyframes/evidence_sample_50 \
  --max-events 50 --max-frames-per-view 3 --overwrite
```

text sampled baseline:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/run_retrieval_baselines.py \
  --canonical-root Datasets/processed/aihub_multi_angle_cctv/20260708/canonical \
  --embedding-root Datasets/processed/aihub_multi_angle_cctv/20260708/embeddings/bge-m3 \
  --output-dir Datasets/processed/aihub_multi_angle_cctv/20260708/results/bgem3_faiss_b0_b5_sampled50 \
  --top-ks 1,5,10,20 --max-rank 50 --postfilter-doc-k 200 \
  --max-queries-per-difficulty 50 --overwrite
```

full text baseline은 위 명령에서 `--max-queries-per-difficulty 50`을 제거하면 된다.
