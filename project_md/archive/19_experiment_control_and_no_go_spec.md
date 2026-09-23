# 추가 데이터셋 필요성 및 실험 통제 명세

작성 기준일: 2026-07-07

2026-07-09 최신 갱신: 이 문서의 no-go 기준은 2026-07-07 text/metadata 및 early true-multimodal 단계 기준이다. 최신 기준에서는 추가 데이터셋 중 AI Hub 다각도 CCTV와 시내도로 CCTV가 실제로 본문 실험에 반영되었고, controlled LLM/VLM answer generation 및 HNSW/IVF 계열 index benchmark도 완료되었다. 최신 통제·no-go 기준은 `27_submission_execution_board_20260707.md`와 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

> 2026-07-07 정정: 이 문서는 B0-B5 text/metadata baseline 중심 단계에서 작성된 통제안이다. 이후 실제 mp4 keyframe 추출, CLIP visual embedding, text-to-video, image-to-video, text+visual fusion 실험이 완료되었으므로, true multimodal 검색 설계와 최종 실험 해석은 `20_true_multimodal_research_redesign.md`와 `21_true_multimodal_execution_status_20260707.md`를 우선 기준으로 한다.

## 결론

최신 투고 범위는 **도시 교통·감시형 영상 이벤트 데이터의 evidence retrieval/selection 구조 비교**를 중심으로 하되, fixed LLM/VLM answer-level control과 visual vector index benchmark까지 포함한다. 추가 데이터셋 수집은 더 필요하지 않다. 현재 본문 핵심은 VRU-Accident와 AI Hub 지능형 CCTV의 true multimodal retrieval, AI Hub 다각도 CCTV의 answer-level view-selection, 시내도로 CCTV의 index-structure benchmark다. AI Hub 이상행동 CCTV는 text/metadata 보조 baseline으로 유지한다.

반대로 논문에서 “센서 로그, 지도, 기상 API, 실제 관제 운영 규모까지 포함한 완전한 도시 교통 관제 시스템”을 주장하는 것은 여전히 과도하다. 교차로신호체계, CityFlow-NL, WTS/TUMTraffic 계열은 확장 가능성 또는 후속 연구로 두고, 현재 본문 수치 주장은 위 네 축으로 제한한다.

## 데이터셋 판정

| 데이터셋 | 현재 역할 | 상태 | 본문 사용 판정 |
|---|---|---|---|
| VRU-Accident | main traffic safety workload | canonical, bge/e5, FAISS B0-B5, pgvector, keyframe, visual/fusion/image/service 결과 완료 | 본문 핵심 결과 |
| AI Hub 지능형 CCTV | main CCTV workload | canonical, bge/e5 B0-B5, keyframe, visual/fusion/image/service 결과 완료 | 본문 핵심 결과 |
| AI Hub 이상행동 CCTV | 국내 이상행동 CCTV 보조 baseline | raw zip/XML 정리, canonical, bge/e5 B0-B5 완료 | 보조 결과 |
| AI Hub 다각도 CCTV 71953 | multi-view CCTV answer-level workload | canonical evidence DB, 400-clip stratum, 4-VLM answer-level 평가 완료 | 본문 핵심 결과 |
| 시내도로 CCTV | visual vector index workload | 132K real CLIP vectors, 1M synthetic scale benchmark 완료 | 본문 핵심 결과 |
| CityFlow-NL annotation | 자연어 vehicle retrieval annotation | annotation canonical 및 raw zip 확보, visual frame materialization 전 | 본문 핵심 수치 제외, 확장 후보 |
| WTS | multi-view traffic safety 후보 | repo만 확보, 원본 승인 필요 | 향후 연구 |
| TUMTraffic-VideoQA | roadside traffic VideoQA 후보 | 등록/원본 확보 필요 | 향후 연구 |
| AI Hub 522 교차로 복합 데이터 | 교통 정형 로그 보강 후보 | 원본 확보, metadata/log extension 설계 | 후속/보조 확장 |

최종 권고는 다음이다.

1. 2026년 8월호 투고 본문에는 현재 완료된 데이터셋 축 이상으로 새 수치 실험을 더 넣지 않는다.
2. 주장은 “영상 이벤트, 텍스트 evidence, 구조화 metadata를 결합한 retrieval/evidence-selection workload와 fixed answer-level control”로 제한한다.
3. AI Hub 이상행동 CCTV는 교통 데이터가 아니라 생활안전 CCTV이므로, traffic main claim이 아니라 surveillance external validity로만 사용한다.
4. CityFlow-NL과 교차로신호체계는 확보·설계 상태를 언급할 수 있지만, 본문 핵심 수치 주장은 하지 않는다.

## No-Go 기준

아래 조건 중 하나라도 해당하면 해당 확장 실험은 이번 투고 본문에 넣지 않는다.

| 조건 | 판정 |
|---|---|
| 원본 다운로드나 승인 절차가 남아 있다 | No-Go |
| canonical 변환 후 `queries.jsonl`과 `qrels.tsv`를 같은 날 검증할 수 없다 | No-Go |
| qrels 생성 규칙을 수동으로 고쳐야 결과가 좋아진다 | No-Go |
| query가 한국어 중심인데 BM25 tokenizer를 바꾸지 않았다 | No-Go |
| 새 dataset 결과가 기존 주장과 충돌하지만 원인 분석 시간이 없다 | No-Go |
| 영상 frame embedding, VLM answer generation, reranker를 넣어야만 의미 있는 데이터셋이다 | No-Go |
| 실험 결과가 논문 핵심 주장을 넓히기만 하고 방어 근거를 늘리지 못한다 | No-Go |

## 고정해야 할 실험 자원

| 항목 | 고정값 |
|---|---|
| project root | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety` |
| dataset logical root | `Datasets` |
| dataset physical root | `/hdd2/KIISE_datasociety/Datasets` |
| conda env | `Datasets/envs/kiise-vlmdb` |
| Python | 3.10.20 |
| pandas / pyarrow | 2.3.3 / 24.0.0 |
| numpy / torch | 2.2.6 / 2.12.1+cu130 |
| sentence-transformers | 5.6.0 |
| FAISS | 1.14.3 |
| PostgreSQL vector backend | `kiise-vlmdb-pgvector`, `pgvector/pgvector:pg16`, port 5433 |
| GPU | NVIDIA RTX 3090 24GB x2 |
| storage status | `/hdd2` 3.6T 중 1.1T 사용, 2.4T 여유 |

모든 재현 명령은 반드시 아래 형태로 실행한다.

```bash
conda run -p Datasets/envs/kiise-vlmdb python ...
```

기본 `/opt/anaconda3/bin/python`이나 base conda 환경을 사용하면 parquet/pyarrow 버전 차이로 결과 재현성이 깨질 수 있다.

## Canonical artifact 동결

실험 본문에 사용하는 canonical root는 아래 세 개로 고정한다.

| dataset | canonical root |
|---|---|
| VRU-Accident | `Datasets/processed/vru_accident/20260706/canonical` |
| AI Hub 지능형 CCTV | `Datasets/processed/aihub_intelligent_cctv/20260706/canonical` |
| AI Hub 이상행동 CCTV | `Datasets/processed/aihub_abnormal_cctv/20260707/canonical` |

각 canonical root는 다음 파일을 모두 포함해야 한다.

```text
clips.parquet
documents.parquet
metadata.parquet
queries.jsonl
qrels.tsv
dataset_manifest.json 또는 summary.md
```

금지 사항:

- 결과를 본 뒤 query/qrels를 수동 보정하지 않는다.
- `semantic_filter`를 retrieval code에서 직접 사용하지 않는다.
- dataset마다 다른 metric이나 다른 top-k를 사용하지 않는다.
- AI Hub 이상행동 CCTV의 zip 원본을 임의로 압축 해제하여 media path 체계를 바꾸지 않는다.

## 질의와 qrels 통제

현재 질의는 `query_text`, `metadata_filter`, `semantic_filter`, `qrel_filter`를 가진다.

| 필드 | 역할 | retrieval 사용 여부 |
|---|---|---|
| `query_text` | BM25와 embedding 검색 입력 | 사용 |
| `metadata_filter` | B0/B3/B4/B5의 구조화 조건 | 사용 |
| `semantic_filter` | 의미 조건 기록 | retrieval 직접 사용 금지 |
| `qrel_filter` | 정답 clip 생성 기준 | 평가에만 사용 |

평가 누수를 막기 위한 규칙:

1. 모든 전략은 동일한 `queries.jsonl`과 `qrels.tsv`를 사용한다.
2. B1/B2는 `metadata_filter` 없이 자연어만 사용한다.
3. B3/B4/B5는 동일한 `metadata_filter`를 사용한다.
4. B4가 좋은 이유를 주장할 때는 B3와의 차이도 함께 보고한다.
5. query text에 metadata 단어가 포함되는 것은 허용한다. 실제 사용자가 “비 오는 야간”처럼 자연어로 말하는 상황을 반영하기 때문이다. 다만 구조화 조건으로 추출된 `metadata_filter`를 쓰는 전략과 그렇지 않은 전략을 명확히 구분해야 한다.

한국어 질의 통제:

현재 BM25 tokenizer는 `[A-Za-z0-9]+` 기반이라 한국어 토큰을 사용하지 않는다. 따라서 이번 본문 실험에서는 영어 event term을 포함한 현재 query set을 유지한다. 한국어-only query를 추가하려면 Mecab, Kiwi, soynlp, character n-gram 중 하나로 BM25 tokenizer를 바꾸고 모든 BM25/hybrid 결과를 다시 생성해야 한다.

## Embedding 통제

| 항목 | 고정값 |
|---|---|
| main embedding | `BAAI/bge-m3` |
| robustness embedding | `intfloat/e5-large-v2` |
| embedding dim | 1024 |
| normalization | `normalize_embeddings=True` |
| e5 prefix | query는 `query:`, document는 `passage:` |
| training/fine-tuning | 없음 |

원칙:

- 논문 결과는 이미 생성된 embedding artifact를 기준으로 한다.
- 새로 생성할 경우 model path, batch size, device, package version을 manifest에 남긴다.
- embedding 생성 시간은 retrieval latency에 포함하지 않는다.

## 검색 메커니즘 통제

| 전략 | 고정 구현 | 통제 파라미터 |
|---|---|---|
| B0 metadata-only | pandas metadata pivot 후 exact facet match | `max_rank=100` |
| B1 BM25-only | `rank_bm25.BM25Okapi` | 현재 tokenizer 고정 |
| B2 vector-only | FAISS `IndexFlatIP`, L2 normalized vector | exact search |
| B3 vector postfilter | FAISS top-N 후 metadata filter | `postfilter_doc_k=200` |
| B4 prefilter vector | metadata 후보 내부에서 vector dot product | exact candidate scoring |
| B5 hybrid | metadata 후보 내부 BM25 + vector, RRF fusion | `rrf_k=60`, `max_rank=100` |
| P2 pgvector | PostgreSQL+pgvector vector-only | exact cosine ordering |
| P4 pgvector | SQL metadata candidate + vector ordering | exact cosine ordering |

중요한 해석 규칙:

- FAISS `IndexFlatIP`는 reference vector search backend이지, 운영형 vector DB 제품 비교 결과가 아니다.
- 논문에서 vector DB backend라고 말할 수 있는 것은 PostgreSQL+pgvector 실험이다.
- pgvector 결과는 HNSW/IVFFlat이 아니라 exact search다. approximate index 확장성 주장은 `39_index_structure_benchmark_results_20260709.md`의 별도 시내도로 CCTV benchmark 범위에서만 한다.
- latency는 같은 backend 안의 전략 비교에만 강하게 사용한다. Python/FAISS와 PostgreSQL latency를 절대 성능으로 직접 비교하지 않는다.

## Latency 측정 통제

현재 latency는 Python process 내부의 query 실행 시간을 측정한다. 다음 조건을 고정해야 한다.

| 항목 | 통제 |
|---|---|
| 실행 중 부하 | 대용량 다운로드, 압축 해제, embedding 생성과 동시에 측정 금지 |
| CPU/GPU | retrieval 자체는 대부분 CPU/메모리 연산. embedding 생성과 분리 |
| cold/warm 상태 | 최종 제출 전 동일 명령으로 1회 재실행하고 manifest 보관 |
| 비교 범위 | 같은 dataset/model/backend 내부 비교만 강하게 주장 |
| 보고값 | mean, p50, p95를 함께 보고 |

최종 재현 로그를 새로 만들 때는 기존 결과를 덮어쓰기 전에 output directory를 별도 suffix로 복사하거나, `run_manifest.json`과 `summary.md`를 보관한다.

## 결과 해석 통제

데이터셋별 해석은 다르게 해야 한다.

| dataset | 안전한 해석 | 피해야 할 해석 |
|---|---|---|
| VRU-Accident | traffic safety main workload에서 metadata prefilter가 vector-only보다 강함 | 실제 CCTV 관제센터 전체를 검증 |
| AI Hub 지능형 CCTV | 국내 CCTV schema portability와 external validity | 작은 269 clips 결과를 main claim으로 과장 |
| AI Hub 이상행동 CCTV | label-aligned CCTV에서 BM25/hybrid와 metadata-aware 구조가 강함 | 교통 CCTV 실험으로 표현 |
| AI Hub 다각도 CCTV | view 선택이 answer-level 정확도에 미치는 fixed VLM evidence-control 결과 | 다각도 CCTV가 일반적으로 항상 유리/무의미하다는 보편 명제 |
| 시내도로 CCTV | visual vector search-layer index trade-off | end-to-end VLM-QA latency/cost 결과 |

특히 AI Hub 이상행동 CCTV는 BM25와 hybrid가 매우 강하다. 이는 실패가 아니라 데이터셋 특성이다. XML label과 query term이 직접 정렬되어 있으므로, 본문에서는 “label-aligned 환경에서는 sparse/hybrid baseline이 중요하다”는 보강 근거로 사용한다.

## 제출 전 필수 체크리스트

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/check_research_resources.py
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/validate_experiment_freeze.py

python -m py_compile \
  2026_KIISE/scripts/check_research_resources.py \
  2026_KIISE/scripts/validate_experiment_freeze.py \
  2026_KIISE/scripts/build_text_embeddings.py \
  2026_KIISE/scripts/run_retrieval_baselines.py \
  2026_KIISE/scripts/run_pgvector_retrieval.py \
  2026_KIISE/src/vlmdb_workload/retrieval.py \
  2026_KIISE/src/vlmdb_workload/embeddings.py
```

필수 확인 항목:

| 항목 | 통과 기준 |
|---|---|
| resource check | `read_errors={}` |
| canonical counts | 원고 표 4와 일치 |
| embedding exists | bge/e5 모두 존재 |
| result summary | 각 결과 경로에 `summary.md`, `metrics_summary.csv`, `run_manifest.json` 존재 |
| pgvector | 컨테이너 `kiise-vlmdb-pgvector` up, port 5433 |
| Word 초안 | 표 10 포함 여부 확인 |
| 주장 범위 | retrieval core와 fixed answer-level control을 구분하고, index 결과는 search-layer benchmark로 명시 |

## 최종 방침

이번 투고에서 가장 안전한 선택은 다음이다.

1. 본문 핵심 데이터셋 축은 VRU, AI Hub 지능형 CCTV, AI Hub 다각도 CCTV, 시내도로 CCTV로 고정한다.
2. main claim은 실제 mp4/keyframe 기반 visual retrieval, text+visual+metadata fusion, image-to-video, service-level evidence selection, fixed answer-level evidence control에 둔다.
3. AI Hub 이상행동 CCTV는 보조 baseline 및 schema portability 근거로만 둔다.
4. approximate index 주장은 시내도로 CCTV search-layer benchmark로만 제한하고, end-to-end VLM-QA latency로 확장하지 않는다.
5. 새 데이터셋을 추가로 수집하거나 새 핵심 수치 실험을 늘리지 않는다. CityFlow-NL과 교차로신호체계는 확보·설계 상태 또는 후속 확장으로만 언급한다.
