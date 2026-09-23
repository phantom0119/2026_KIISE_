# 본 연구 데이터셋 구성표

작성일: 2026-07-14  
용도: Notion 복사/붙여넣기용 데이터셋 구성 정리

---

## 데이터셋 전체 요약

| 구분 | 데이터셋 | 로컬 경로 | 본 연구에서의 역할 | 멀티모달 여부 | 멀티모달이라고 보는 이유 |
|---|---|---|---|---|---|
| 핵심 | AI Hub 522 교차로 신호체계 | `Datasets/external/교차로신호체계`, `Datasets/processed/aihub_522_intersection/20260710` | 주력 tri-source 워크로드 | 강함 | 영상/프레임, VLM caption, 센서·시공간 metadata, 사람 주석 qrels가 분리되어 연결됨 |
| 외부검증 | MEVA | `Datasets/external/meva`, `Datasets/processed/meva_kf1/20260713` | 해외 CCTV 외적 타당성 검증 | 강함 | CCTV 프레임, VLM caption, capture metadata, 사람 activity annotation이 연결됨 |
| DB 검증 | MIRIS | `Datasets/external/miris`, `Datasets/processed/miris_traffic/20260713` | partial/local index 정책 교차검증 | 제한적 | 영상 프레임 embedding과 시간·장소 predicate가 있으나 VLM-QA qrels 중심은 아님 |
| 색인 코퍼스 | Sinnaedoro traffic | `Datasets/processed/sinnaedoro_traffic` | 132K급 filtered ANN/index benchmark | 제한적 | 프레임 embedding과 시공간 predicate 중심. 검색 정답 qrels보다는 exact top-k 대비 recall 평가 |
| 보조 | UCA | `Datasets/external/UCA_surveillance`, `Datasets/processed/uca_anchor/20260712` | 영어 이상행동 외부 검증 | 중간 | 영상 프레임, VLM caption, 사람 문장 주석, container metadata가 연결됨. 독립 센서 채널은 없음 |
| 보조 | VRU-Accident | `Datasets/processed/vru_accident/20260706`, `Datasets/processed/vru_accident/20260710_noncircular` | collapse 검증, answer evidence 실험 | 중간 | 사고 영상, keyframe, caption/document, metadata, qrels가 있음. 고정 CCTV·센서형 데이터는 아님 |
| 보조 | AI Hub 지능형 CCTV | `Datasets/processed/aihub_intelligent_cctv/20260706`, `Datasets/processed/aihub_intelligent_cctv/20260710_noncircular` | collapse 검증, 국내 CCTV 이식성 | 중간 | CCTV clip, keyframe, 사건 caption, metadata, qrels가 있음 |
| 보조 | AI Hub 다각도 CCTV | `Datasets/processed/aihub_multi_angle_cctv/20260708` | 다중 시점 evidence 선택 / VLM 답변 실험 | 강함 | 동일 사건의 다중 view, evidence frame, caption/document, metadata, VLM answer 결과가 연결됨 |
| 보류/과거 | AI Hub 이상행동 CCTV | `Datasets/processed/aihub_abnormal_cctv/20260707` | 과거 text/metadata baseline | 제한적 | canonical과 text/metadata baseline은 있으나 최종 핵심 multimodal 주장에서는 보조 또는 보류 |

---

## AI Hub 522 교차로 신호체계 파일 구성

| 구성 | 실제 파일/폴더 | 내용 | 연구에서의 역할 |
|---|---|---|---|
| 원천 데이터 | `Datasets/external/교차로신호체계/1.Training/원천데이터/TS_*.zip` | AI Hub 원천 데이터 zip | 원본 교차로 데이터 |
| 라벨 데이터 | `Datasets/external/교차로신호체계/1.Training/라벨링데이터/TL_*.zip` | 통과차량, 보행량, 도로차량, 바운딩박스, 큐보이드 라벨 | 사람 주석/센서성 정보 추출 |
| 검증 원천 | `Datasets/external/교차로신호체계/2.Validation/원천데이터/VS_*.zip` | validation 원천 데이터 | 추가 원본 |
| 검증 라벨 | `Datasets/external/교차로신호체계/2.Validation/라벨링데이터/VL_*.zip` | validation 라벨 데이터 | 추가 라벨 |
| 센서 facet | `Datasets/processed/aihub_522_intersection/20260710/sensor_facets.parquet` | 시간대, 신호, 밀도 등 sensor predicate | metadata filter |
| 영상-센서 조인 | `visual_sensor_join.parquet` | visual video와 sensor clip의 시간/교차로 기반 조인 | 영상과 센서 연결 |
| 사람 주석 facet | `annotation_video_facets.parquet`, `annotation_frame_facets.parquet` | 주차, 정차, 다중버스, 이륜 등 장면 주석 | relevance/qrels 생성 |
| VLM caption | `captions/documents.parquet`, `captions/*.jsonl` | Qwen2.5-VL 기반 프레임 caption | 검색 문서 |
| canonical schema | `canonical_trisource_expanded/clips.parquet` | 검색 대상 clip 목록 | workload 기본 테이블 |
| canonical schema | `canonical_trisource_expanded/documents.parquet` | 검색 문서 | text/vector 검색 대상 |
| canonical schema | `canonical_trisource_expanded/metadata.parquet` | clip별 metadata | prefilter/postfilter 조건 |
| canonical schema | `canonical_trisource_expanded/queries.jsonl` | 자연어 질의와 metadata filter | 검색 query |
| canonical schema | `canonical_trisource_expanded/qrels.tsv` | strict qrels | hard constraint 평가 |
| canonical schema | `canonical_trisource_expanded/qrels_semantic.tsv` | semantic qrels | soft intent 평가 |
| 감사 파일 | `canonical_trisource_expanded/A6_trisource_audit.json` | 비순환성 감사 결과 | 평가 타당성 검증 |
| 텍스트 임베딩 | `embeddings_trisource_expanded/bge-m3/*.npy`, `*.parquet` | document/query embedding | dense vector 검색 |
| 시각 임베딩 | `visual_embeddings_clip/frame_embeddings.npy` | CLIP frame embedding | frame-vector / visual search |
| 시각 index | `visual_embeddings_clip/frame_index.parquet` | frame id, clip id, frame path | frame 검색 결과 해석 |
| 결과 | `results/trisource_expanded_b0_b5/*` | B0-B5 검색 결과와 지표 | 검색 구조 비교 |
| 저장 단위 결과 | `results/storage_unit/*` | clip-caption, frame-vector 등 비교 | 저장 설계 실험 |

---

## MEVA 파일 구성

| 구성 | 실제 파일/폴더 | 내용 | 연구에서의 역할 |
|---|---|---|---|
| 원본 repo | `Datasets/external/meva/meva-data-repo` | MEVA annotation repo | 원천 주석 |
| license/readme | `README.md`, `LICENSE` | 데이터 설명 및 라이선스 | 출처 확인 |
| activity presence | `Datasets/processed/meva_kf1/20260713/activity_presence.parquet` | activity 존재 정보 | relevance 생성 |
| predicate facets | `predicate_facets.parquet` 계열 | time/location/hour 등 capture metadata | metadata filter |
| 추출 프레임 | `frames/*.jpg` | clip별 대표 프레임 | visual evidence |
| VLM caption | `captions/` | Qwen2.5-VL caption | 검색 문서 |
| canonical clips | `canonical_trisource/clips.parquet` | 검색 clip 목록 | workload 기본 |
| canonical documents | `canonical_trisource/documents.parquet` | caption document | dense 검색 |
| canonical metadata | `canonical_trisource/metadata.parquet` | capture metadata | filter 조건 |
| canonical queries | `canonical_trisource/queries.jsonl` | 자연어 질의 | query |
| qrels | `canonical_trisource/qrels.tsv` | strict 정답 | hard constraint 평가 |
| semantic qrels | `canonical_trisource/qrels_semantic.tsv` | semantic 정답 | soft intent 평가 |
| 감사 | `canonical_trisource/A6_trisource_audit.json` | 비순환성 감사 | 검증 |
| 텍스트 임베딩 | `embeddings/bge-m3/*` | document/query embedding | text dense 검색 |
| 시각 임베딩 | `embeddings/clip-vit-b32/frame_embeddings.npy` | CLIP frame embedding | frame-vector 저장 단위 |
| 결과 | `results/meva_bgem3_b0_b5/*` | B0-B5 검색 결과 | 522 결론 외부 검증 |
| 저장 단위 결과 | `results/storage_unit/*` | storage-unit 비교 | 522와 결과 반전 확인 |

---

## MIRIS 파일 구성

| 구성 | 실제 파일/폴더 | 내용 | 연구에서의 역할 |
|---|---|---|---|
| 원본 zip | `Datasets/external/miris/ytstream-dataset.zip` | MIRIS traffic video dataset | 원본 |
| 원본 설명 | `Datasets/external/miris/data/README.txt` | 데이터 설명 | 출처 확인 |
| 다운로드 로그 | `Datasets/external/miris/download.log` | 확보 기록 | 재현성 |
| 처리 결과 | `Datasets/processed/miris_traffic/20260713` | MIRIS 처리 산출물 | DB index 실험 |
| query vectors | `miris_queries.npy` | 실험용 query vector | index recall 평가 |
| frame embeddings | 처리 산출물 내 frame embedding | CLIP frame vector | pgvector partial/local index 검증 |
| frame metadata | 처리 산출물 내 frame index/predicate | hour/location 등 | 선택도별 predicate 평가 |
| 결과 | `paper_assets/20260713_db_design/pgvector_partial_vs_global_miris.csv` | global vs partial index 결과 | DB 정책 교차검증 |
| 정책 결과 | `hotcold_miris_policy.csv` | hot/cold index 손익분기 | 운영 가이드 |

---

## Sinnaedoro traffic 파일 구성

| 구성 | 실제 파일/폴더 | 내용 | 연구에서의 역할 |
|---|---|---|---|
| frame embedding | `Datasets/processed/sinnaedoro_traffic/corpus_real/frame_embeddings.npy` | 132K급 CLIP frame vector | filtered ANN/index benchmark |
| frame index | `corpus_real/frame_index.parquet` | frame id, metadata, path | 결과 해석 |
| predicate 목록 | `corpus_real/predicate_inventory.csv` | location/date/hour 등 predicate | real predicate 평가 |
| query vectors | `corpus_real/queries.npy` | 검색 query vector | recall 평가 |
| index benchmark | `index_benchmark/*` | Flat/HNSW/IVF/PQ 성능 | 색인 구조 비교 |
| filtered ANN 결과 | `filtered_ann/filtered_ann.csv` | prefilter/postfilter/single-stage 결과 | random mask 대비 평가 |
| manifest | `filtered_ann/manifest.json` | 실행 설정 | 재현성 |
| 대규모 shard | `corpus300k_shard0`, `corpus300k_shard1` | 확장 frame vector shard | scale 실험 보조 |

---

## UCA 파일 구성

| 구성 | 실제 파일/폴더 | 내용 | 연구에서의 역할 |
|---|---|---|---|
| 원본 zip | `Datasets/external/UCA_surveillance/UCF_Crimes.zip` | UCF-Crime 원본 영상 | 원천 영상 |
| annotation repo | `Datasets/external/UCA_surveillance/repo` | UCA annotation | 사람 문장 주석 |
| annotation table | `Datasets/processed/uca_anchor/20260712/annotation_sentences.parquet` | 문장 주석 | relevance 후보 |
| relevance | `relevance.parquet` | 렉시콘 기반 relevance | qrels 생성 |
| frame images | `frames/*.jpg` | 추출 프레임 | visual evidence |
| captions | `captions/` | VLM caption | 검색 문서 |
| canonical clips | `canonical/clips.parquet` | segment/clip 목록 | 검색 대상 |
| canonical documents | `canonical/documents.parquet` | caption document | dense 검색 |
| canonical metadata | `canonical/metadata.parquet` | duration/class/container metadata | filter |
| canonical queries | `canonical/queries.jsonl` | 질의 | 검색 query |
| qrels | `canonical/qrels.tsv` | strict 정답 | hard constraint 평가 |
| semantic qrels | `canonical/qrels_semantic.tsv` | semantic 정답 | soft intent 평가 |
| 감사 | `canonical/A6_UCA_audit.json` | UCA용 비순환 감사 | 외부 검증 |
| 결과 | `results/` | 검색 결과 | 522 결론 탐색적 이식 |

---

## VRU-Accident 파일 구성

| 구성 | 실제 파일/폴더 | 내용 | 연구에서의 역할 |
|---|---|---|---|
| canonical clips | `Datasets/processed/vru_accident/20260706/canonical/clips.parquet` | 사고 clip 목록 | 검색 대상 |
| canonical documents | `canonical/documents.parquet` | 사고 설명/caption document | text 검색 |
| canonical metadata | `canonical/metadata.parquet` | 날씨, 도로, 장소 등 facet | metadata filter |
| canonical queries | `canonical/queries.jsonl` | 자연어 질의 | 검색 query |
| qrels | `canonical/qrels.tsv` | 정답 clip | 검색 평가 |
| manifest | `canonical/dataset_manifest.json` | 데이터셋 구성 정보 | 재현성 |
| keyframes | `keyframes/` | clip별 keyframe | visual evidence |
| CLIP embeddings | `visual_embeddings/clip-vit-base-patch32_full/*` | frame/query embedding | visual retrieval |
| SigLIP embeddings | `visual_embeddings/siglip-base-patch16-224_full/*` | visual encoder ablation | robustness |
| text embeddings | `embeddings/bge-m3/*`, `embeddings/e5-large-v2/*` | text embedding | dense 검색 |
| retrieval results | `results/*` | B0-B5, visual, image-to-video 결과 | 검색 구조 비교 |
| service packets | `service_testbed/*/service_packets.jsonl` | answer-ready evidence packet | VLM-QA 연결 |
| noncircular repair | `20260710_noncircular/*` | 수리된 비순환 워크로드 | collapse 실증 |

---

## AI Hub 지능형 CCTV 파일 구성

| 구성 | 실제 파일/폴더 | 내용 | 연구에서의 역할 |
|---|---|---|---|
| canonical | `Datasets/processed/aihub_intelligent_cctv/20260706/canonical/*` | clips, documents, metadata, queries, qrels | 검색 baseline |
| keyframes | `keyframes/` | event-centered keyframe | visual evidence |
| visual embeddings | `visual_embeddings/clip-vit-base-patch32_*/*` | CLIP frame/query embedding | visual retrieval |
| text embeddings | `embeddings/bge-m3/*`, `embeddings/e5-large-v2/*` | document/query embedding | dense 검색 |
| results | `results/*` | 검색 결과 | baseline 및 이식성 |
| service packets | `service_testbed/*` | evidence packet | answer-ready evidence |
| noncircular repair | `20260710_noncircular/*` | 수리된 워크로드 | collapse 실증 |

---

## AI Hub 다각도 CCTV 파일 구성

| 구성 | 실제 파일/폴더 | 내용 | 연구에서의 역할 |
|---|---|---|---|
| canonical | `Datasets/processed/aihub_multi_angle_cctv/20260708/canonical/*` | clips, documents, metadata, queries, qrels | 다각도 검색 워크로드 |
| stratified canonical | `canonical_stratified_event_split_5/*` | 층화 split | answer-level 실험 |
| views | `canonical*/views.parquet` | 사건별 view 정보 | multi-view 구조 |
| evidence frames | `canonical*/evidence_frames.parquet` | VLM에 제공할 frame | 답변 evidence |
| keyframes | `keyframes/` | 추출 프레임 | visual evidence |
| visual embeddings | `visual_embeddings/clip_vit_b32_*`, `visual_embeddings/siglip_*` | CLIP/SigLIP frame embedding | view/evidence 검색 |
| text embeddings | `embeddings/bge-m3*/*` | caption/document embedding | text 검색 |
| service packets | `service_testbed/*/service_packets.jsonl` | VLM 입력 evidence packet | VLM-QA 연결 |
| VLM answer 결과 | `results/multiview_answer_vlm_*/*` | VLM 답변 결과 | better-view vs worse-view 분석 |
| answer grounding | `results/answer_grounding_*/*` | evidence와 답변 연결 | evidence 선택 평가 |

---

## AI Hub 이상행동 CCTV 파일 구성

| 구성 | 실제 파일/폴더 | 내용 | 연구에서의 역할 |
|---|---|---|---|
| canonical | `Datasets/processed/aihub_abnormal_cctv/20260707/canonical/*` | clips, metadata, queries, qrels | 과거 text/metadata baseline |
| text embeddings | `embeddings/*` | document/query embedding | dense 검색 |
| visual embeddings | `visual_embeddings/*` | 일부 visual embedding 산출물 | 보조 |
| results | `results/*` | 검색 baseline 결과 | 최종 핵심 주장에서는 보조/보류 |

---

## 왜 본 연구 데이터셋을 멀티모달이라고 부를 수 있는가

| 기준 | 설명 | 본 연구에서의 구현 |
|---|---|---|
| 시각 모달리티 | 실제 영상, 프레임, keyframe, CCTV clip | `frames/*.jpg`, `keyframes/`, `frame_index.parquet`, `frame_embeddings.npy` |
| 텍스트 모달리티 | VLM caption, 사건 설명, 질의 문장 | `documents.parquet`, `captions/*.jsonl`, `queries.jsonl` |
| 구조화 metadata | 시간, 위치, 신호, 밀도, 카메라, 장소 등 | `metadata.parquet`, `sensor_facets.parquet`, `predicate_inventory.csv` |
| 정답/평가 모달리티 | 사람 주석 또는 annotation 기반 qrels | `qrels.tsv`, `qrels_semantic.tsv`, `activity_presence.parquet`, `annotation_*_facets.parquet` |
| 검색 연결성 | query가 text/vector/metadata를 함께 사용 | B0-B5, prefilter/postfilter/hybrid, storage-unit 실험 |
| DB 관점 | 저장 단위, 색인, 필터 결합 방식 비교 가능 | `embeddings/*`, `visual_embeddings/*`, `results/storage_unit/*`, pgvector 결과 |

---

## 멀티모달 강도 분류

| 분류 | 해당 데이터셋 | 이유 |
|---|---|---|
| 완전한 핵심 멀티모달 tri-source | AI Hub 522 | 센서 predicate, VLM caption document, 사람 annotation relevance가 분리되어 있음 |
| 외부 검증용 멀티모달 | MEVA | 영상 프레임, VLM caption, capture metadata, 사람 activity annotation이 연결됨 |
| 2.5-channel 멀티모달 | UCA | 영상, caption, 사람 문장 주석은 있으나 독립 센서 metadata는 약함 |
| 검색/답변 보조 멀티모달 | VRU, AI Hub 지능형 CCTV, AI Hub 다각도 CCTV | 영상, keyframe, caption, metadata, qrels 또는 VLM answer가 연결됨 |
| 색인/DB 검증용 멀티모달 | MIRIS, Sinnaedoro | frame vector와 시공간 predicate는 있으나 VLM-QA qrels 중심 데이터셋은 아님 |
| 보류/과거 baseline | AI Hub 이상행동 CCTV | text/metadata baseline 중심이며 최종 핵심 멀티모달 주장에서는 제한적으로만 사용 |

---

## 보고서용 한 문장

| 용도 | 문장 |
|---|---|
| 짧은 설명 | 본 연구의 데이터셋은 단순 영상 모음이 아니라, 영상/프레임, VLM caption, 센서·시공간 metadata, 사람 주석 기반 qrels가 canonical schema로 연결된 멀티모달 검색 워크로드이다. |
| 조금 더 정확한 설명 | 특히 AI Hub 522 교차로 데이터는 predicate를 센서 CSV에서, document를 프레임 기반 VLM caption에서, relevance를 사람 주석에서 분리해 구성했기 때문에 본 연구의 핵심 비순환 tri-source 멀티모달 데이터셋으로 사용된다. |
| 주의 표현 | 모든 데이터셋이 동일한 수준의 tri-source는 아니다. 522는 핵심 flagship이고, MEVA는 외부 검증, MIRIS와 Sinnaedoro는 DB 색인 정책 검증, VRU와 다각도 CCTV는 answer/evidence 보조 실험에 사용된다. |

