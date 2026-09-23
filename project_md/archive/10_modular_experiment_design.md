# 모듈형 실험 설계

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 모듈형 설계는 실제로 VRU, AI Hub 지능형 CCTV, AI Hub 이상행동 CCTV, AI Hub 다각도 CCTV, 시내도로 CCTV 확장에 사용되었다. 최신 상태는 canonical schema, text/visual embedding, service packet, fixed answer-level control, ANN index benchmark까지 포함하므로 `24_final_experiment_pipeline_spec_20260707.md`와 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 기준으로 한다.

## 현재 구현 상태

2026-07-06 기준으로 첫 번째 DatasetAdapter, embedding 생성기, BM25/FAISS 기반 B0~B5 retrieval baseline, evaluator 실행까지 완료했다.

| 항목 | 상태 | 경로 |
|---|---|---|
| VRU-Accident adapter | 완료 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/src/vlmdb_workload/adapters/vru_accident.py` |
| canonical build script | 완료 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_vru_canonical.py` |
| embedding provider | 완료 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/src/vlmdb_workload/embeddings.py` |
| retrieval/evaluator | 완료 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/src/vlmdb_workload/retrieval.py` |
| canonical output | 생성 완료 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/vru_accident/20260706/canonical` |
| embedding output | 생성 완료 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/vru_accident/20260706/embeddings` |
| retrieval output | 생성 완료 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/vru_accident/20260706/results` |

생성된 산출물:

| artifact | count |
|---|---:|
| `clips.parquet` | 1,000 |
| `documents.parquet` | 7,000 |
| `metadata.parquet` | 6,000 |
| `queries.jsonl` | 244 |
| `qrels.tsv` | 5,488 |
| missing media | 0 |

query 난도 분포:

| difficulty | queries | qrels | avg positives |
|---|---:|---:|---:|
| weak | 39 | 1,703 | 43.67 |
| medium | 119 | 2,905 | 24.41 |
| strong | 86 | 880 | 10.23 |

재생성 명령:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_vru_canonical.py --overwrite
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_text_embeddings.py --model-id bge-m3 --batch-size 16 --overwrite
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/run_retrieval_baselines.py --overwrite
```

중요 구현 사항:

- `query_text`는 의미 검색 대상인 사고 유형을 포함한다.
- `metadata_filter`는 road/location/weather 같은 컨텍스트 조건만 포함한다.
- `qrel_filter`는 의미 조건과 컨텍스트 조건을 함께 포함한다.
- 이 분리는 metadata filter가 정답을 그대로 노출하는 평가 누수를 막기 위한 것이다.

## 설계 목표

본 연구는 특정 데이터셋, 특정 embedding model, 특정 vector database 하나의 성능을 주장하는 논문이 아니다. 핵심은 다음 질문이다.

> 멀티모달 교통 안전 데이터베이스에서 데이터셋, embedding model, vector backend가 바뀌어도 동일한 워크로드와 평가 프로토콜로 metadata-aware retrieval 구조를 비교할 수 있는가?

따라서 실험 시스템은 처음부터 다음 축을 독립적으로 교체할 수 있어야 한다.

| 확장 축 | 예시 |
|---|---|
| 데이터셋 | VRU-Accident, AI Hub 다각도 CCTV, WTS, TUMTraffic-VideoQA, CityFlow-NL |
| 문서 표현 | dense caption, VQA question/answer, event report, generated report, keyframe caption |
| metadata facet | weather, location, road type, accident type, camera id, timestamp, view angle |
| embedding model | bge-m3, e5-large-v2, SigLIP, Qwen embedding 계열 |
| vector backend | pgvector, FAISS, Milvus, Qdrant |
| sparse backend | BM25, Pyserini/Anserini, SPLADE 계열 |
| retrieval strategy | vector-only, postfilter, prefilter, hybrid, reranker |
| evaluation | Recall@K, MRR, nDCG, latency, index size, cost |

## 핵심 원칙

1. **Canonical schema first**: 모든 데이터셋은 먼저 공통 스키마로 정규화한다.
2. **Model/backend decoupling**: embedding 생성과 vector DB 저장/검색을 분리한다.
3. **Artifact immutability**: 원본, 정규화 산출물, embedding, index, result는 버전별로 보존한다.
4. **Experiment matrix**: 실험은 `dataset x embedding x backend x retrieval strategy` 조합으로 정의한다.
5. **Same qrels, same queries**: 구조 비교는 반드시 동일 query/qrels로 수행한다.
6. **Capability-aware fallback**: backend가 metadata prefilter를 지원하지 않으면 postfilter 또는 external filter로 대체하고, capability 차이를 manifest에 기록한다.

## 전체 파이프라인

```text
raw dataset
  -> DatasetAdapter
  -> canonical artifacts
       clips.parquet
       documents.parquet
       metadata.parquet
       queries.jsonl
       qrels.tsv
  -> EmbeddingProvider
       document_embeddings.npy/parquet
       query_embeddings.npy/parquet
  -> IndexBuilder
       vector index
       sparse index
       metadata index
  -> RetrievalStrategy
       B0 metadata-only
       B1 BM25-only
       B2 vector-only
       B3 vector + postfilter
       B4 metadata prefilter + vector
       B5 hybrid
  -> Evaluator
       retrieval metrics
       latency metrics
       index metrics
       cost metrics
  -> ExperimentReport
```

## 모듈 경계

### 1. DatasetAdapter

역할: 원본 데이터셋을 공통 스키마로 변환한다.

입력:

- 원본 영상, 이미지, parquet, JSON, CSV
- 데이터셋별 annotation
- 데이터셋별 metadata

출력:

- `clips.parquet`
- `documents.parquet`
- `metadata.parquet`
- `queries.jsonl`
- `qrels.tsv`
- `dataset_manifest.json`

필수 인터페이스:

```python
class DatasetAdapter:
    dataset_id: str

    def validate_raw(self) -> ValidationReport:
        ...

    def build_canonical(self, output_dir: Path) -> CanonicalDataset:
        ...

    def build_queries(self, output_dir: Path) -> QuerySet:
        ...
```

데이터셋 추가 시에는 이 모듈만 새로 작성한다. 나머지 embedding, indexing, retrieval, evaluation 코드는 바꾸지 않는다.

### 2. Canonical Schema

모든 데이터셋은 아래 공통 테이블로 들어와야 한다.

#### `clips.parquet`

| 컬럼 | 설명 |
|---|---|
| `clip_id` | 전역 고유 ID. 예: `vru_accident:CAP_DATA:VRU_1` |
| `dataset_id` | `vru_accident`, `aihub_71953`, `wts` 등 |
| `source_split` | train, val, test, all |
| `media_type` | video, image, frame |
| `media_path` | 논리 경로 기준 파일 위치 |
| `duration_sec` | 없으면 null |

#### `documents.parquet`

| 컬럼 | 설명 |
|---|---|
| `doc_id` | 검색 대상 문서 ID |
| `clip_id` | 연결된 clip |
| `doc_type` | dense_caption, qa_question, qa_answer, event_report, keyframe_caption |
| `text` | 검색 대상 텍스트 |
| `lang` | en, ko 등 |

#### `metadata.parquet`

| 컬럼 | 설명 |
|---|---|
| `clip_id` | 연결된 clip |
| `facet_name` | weather_light, location, road_type, accident_type 등 |
| `facet_value` | urban, intersection, car hits pedestrian 등 |
| `facet_source` | human, dataset_label, parsed_vqa, generated |
| `confidence` | 0~1. dataset label이면 1.0 |

#### `queries.jsonl`

| 컬럼 | 설명 |
|---|---|
| `query_id` | 질의 ID |
| `dataset_id` | 질의가 생성된 데이터셋 |
| `query_text` | 자연어 질의 |
| `task` | text_to_clip, text_metadata_retrieval, evidence_lookup |
| `metadata_filter` | JSON 조건 |
| `difficulty` | weak, medium, strong |

#### `qrels.tsv`

| 컬럼 | 설명 |
|---|---|
| `query_id` | 질의 ID |
| `target_id` | 정답 clip 또는 doc |
| `target_type` | clip, doc |
| `relevance` | 0~3 |

### 3. MetadataFacetExtractor

역할: VQA option/answer, annotation, filename, camera metadata 등을 구조화 facet으로 변환한다.

VRU-Accident 예시:

```text
category = "weather and light"
options = "A. rainy day, B. sunny afternoon, C. cloudy morning, D. stormy evening"
answer = "A"
=> facet_name = "weather_light"
=> facet_value = "rainy day"
```

AI Hub 또는 WTS가 추가되면 동일한 `facet_name` vocabulary에 맞춰 변환한다.

핵심은 dataset별 원본 라벨을 그대로 쓰지 않고, 논문 실험용 공통 facet으로 매핑하는 것이다.

### 4. EmbeddingProvider

역할: 문서와 질의를 embedding으로 변환한다.

필수 인터페이스:

```python
class EmbeddingProvider:
    model_id: str
    embedding_dim: int
    modality: str  # text, image, video

    def encode_documents(self, docs: list[str]) -> np.ndarray:
        ...

    def encode_queries(self, queries: list[str]) -> np.ndarray:
        ...
```

모델별 구현:

| 구현체 | 용도 |
|---|---|
| `BgeM3TextEmbedding` | main text embedding |
| `E5LargeTextEmbedding` | robustness check |
| `SiglipImageTextEmbedding` | optional keyframe/image-text ablation |
| `InternVideoEmbedding` | optional video embedding |

embedding artifact는 모델별로 분리한다.

```text
Datasets/processed/{dataset_id}/{dataset_version}/embeddings/
  bge-m3/
    document_embeddings.npy
    document_index.parquet
    query_embeddings.npy
    query_index.parquet
    embedding_manifest.json
  e5-large-v2/
    document_embeddings.npy
    document_index.parquet
    query_embeddings.npy
    query_index.parquet
    embedding_manifest.json
```

### 5. VectorStoreBackend

역할: embedding을 저장하고 top-k vector search를 수행한다.

필수 인터페이스:

```python
class VectorStoreBackend:
    backend_id: str
    capabilities: BackendCapabilities

    def create_collection(self, schema: CollectionSchema) -> None:
        ...

    def upsert(self, items: list[VectorItem]) -> None:
        ...

    def search(self, query_vector, top_k: int) -> list[SearchResult]:
        ...

    def filtered_search(self, query_vector, filters: dict, top_k: int) -> list[SearchResult]:
        ...
```

backend capability는 반드시 기록한다.

| capability | 의미 |
|---|---|
| `supports_sql_filter` | SQL/relational metadata filter 가능 |
| `supports_native_scalar_filter` | vector DB 내부 scalar filter 가능 |
| `supports_hnsw` | HNSW index 가능 |
| `supports_ivf` | IVF/IVFFlat 가능 |
| `supports_exact` | exact scan 가능 |

초기 구현 상태:

1. `FaissBackend` 역할은 local FAISS exact search와 parquet metadata 조합으로 구현했다.
2. `PgVectorBackend`는 DB 논문 성격을 강화하기 위한 다음 backend다.
3. `MilvusBackend` 또는 `QdrantBackend`는 확장 후보로 둔다.

### 6. SparseIndexBackend

역할: BM25 또는 sparse retrieval을 수행한다.

필수 인터페이스:

```python
class SparseIndexBackend:
    backend_id: str

    def build(self, documents: list[Document]) -> None:
        ...

    def search(self, query_text: str, top_k: int) -> list[SearchResult]:
        ...
```

초기 구현:

- `BM25PythonBackend`: 빠른 프로토타입
- `PyseriniBackend`: 논문용 reproducible backend

### 7. RetrievalStrategy

역할: backend와 metadata filter를 결합해 실제 ranking을 만든다.

필수 baseline:

| ID | 전략 | 목적 |
|---|---|---|
| B0 | Metadata-only | 정형 metadata만으로 가능한 수준 |
| B1 | BM25-only | lexical baseline |
| B2 | Vector-only | dense retrieval baseline |
| B3 | Vector + postfilter | top-N 후보 후 metadata 조건 적용 |
| B4 | Metadata prefilter + vector | 조건을 먼저 적용하고 vector search |
| B5 | Hybrid sparse+dense+metadata | BM25와 vector 결과를 RRF 또는 weighted sum으로 결합 |

확장 baseline:

| ID | 전략 | 목적 |
|---|---|---|
| B6 | Hybrid + reranker | top-k reranking upper bound |
| B7 | Text+visual fusion | keyframe embedding 추가 효과 |
| B8 | Cross-dataset retrieval | 데이터셋이 추가될 때 일반화 확인 |

RetrievalStrategy 인터페이스:

```python
class RetrievalStrategy:
    strategy_id: str

    def retrieve(self, query: Query, top_k: int) -> list[SearchResult]:
        ...
```

### 8. Evaluator

역할: 검색 품질과 시스템 비용을 동일 포맷으로 측정한다.

품질 지표:

- Recall@1/5/10/20
- MRR
- nDCG@10
- Hit@K

시스템 지표:

- p50/p95 latency
- index build time
- index size
- embedding generation time
- throughput

분석 축:

- dataset별 성능
- metadata difficulty별 성능
- filter selectivity별 성능
- embedding model별 성능
- vector backend별 성능
- retrieval strategy별 성능

## 실험 Matrix

논문 main experiment는 matrix를 너무 크게 만들면 안 된다. 따라서 1차 matrix는 작게 고정한다.

### Main Matrix

| 축 | 값 |
|---|---|
| dataset | `vru_accident` |
| embedding | `bge-m3` |
| vector backend | `pgvector_hnsw` |
| sparse backend | `bm25` |
| retrieval strategy | B0~B5 |
| difficulty | weak, medium, strong |

### Robustness Matrix

| 축 | 값 |
|---|---|
| embedding | `bge-m3`, `e5-large-v2` |
| vector backend | `pgvector_hnsw`, `faiss_flat` |
| retrieval strategy | B2, B4, B5 |

### Extension Matrix

AI Hub, WTS, TUMTraffic 데이터가 추가되면 다음만 추가 실행한다.

| 축 | 값 |
|---|---|
| dataset | 새 dataset_id |
| embedding | main과 동일한 `bge-m3` |
| vector backend | main과 동일한 `pgvector_hnsw` |
| retrieval strategy | B0~B5 |

이 구조를 사용하면 새 데이터셋이 추가되어도 논문 실험 설계는 바뀌지 않고, DatasetAdapter와 facet mapping만 늘어난다.

## Config 기반 실행

모든 실험은 config 파일 하나로 재현되어야 한다.

```yaml
experiment_id: vru_bgem3_pgvector_main
dataset:
  id: vru_accident
  version: 20260706
  canonical_root: Datasets/processed/vru_accident/20260706
embedding:
  provider: bge-m3
  batch_size: 32
  normalize: true
vector_backend:
  type: pgvector
  index: hnsw
  distance: cosine
sparse_backend:
  type: bm25
retrieval:
  strategies: [B0, B1, B2, B3, B4, B5]
  top_k: [1, 5, 10, 20]
evaluation:
  metrics: [recall, mrr, ndcg, latency, index_size]
  repetitions: 5
```

## 저장 구조

```text
Datasets/
  raw/
    {dataset_id}/
  processed/
    {dataset_id}/
      {dataset_version}/
        canonical/
          clips.parquet
          documents.parquet
          metadata.parquet
          queries.jsonl
          qrels.tsv
          dataset_manifest.json
        embeddings/
          {embedding_model_id}/
            documents.parquet
            queries.parquet
            embedding_manifest.json
        indexes/
          {backend_id}/
            index_manifest.json
        results/
          {experiment_id}/
            run_manifest.json
            retrieval_results.parquet
            metrics.csv
            latency.csv
            summary.md
```

## Run Manifest

각 실험은 `run_manifest.json`을 남긴다.

필수 필드:

- `experiment_id`
- `dataset_id`
- `dataset_version`
- `query_set_id`
- `qrels_version`
- `embedding_model_id`
- `embedding_model_revision`
- `embedding_dim`
- `vector_backend`
- `backend_version`
- `index_type`
- `index_params`
- `retrieval_strategy`
- `top_k`
- `hardware`
- `started_at`
- `finished_at`
- `git_commit` 또는 `code_snapshot`

이 manifest가 있어야 논문에서 재현성을 주장할 수 있다.

## 논문 실험 서술 방식

논문 방법론에는 "모듈형 실험 프레임워크"를 하나의 기여로 넣을 수 있다.

기여 문장:

> 본 연구는 데이터셋, embedding model, vector backend, retrieval strategy를 독립적으로 교체할 수 있는 모듈형 VLM-DB 실험 프레임워크를 설계하였다. 모든 원천 데이터는 clip-document-metadata-query-qrels의 canonical schema로 정규화되며, 동일한 qrels에 대해 sparse, dense, metadata-aware, hybrid retrieval 구조를 비교한다. 이를 통해 특정 모델이나 특정 데이터셋에 종속되지 않고 metadata-aware retrieval 구조의 효과를 분석할 수 있다.

## 2주 일정에서의 실행 범위

필수:

1. `VRUAccidentAdapter`
2. canonical schema 생성
3. `BgeM3TextEmbedding`
4. `BM25PythonBackend`
5. `PgVectorBackend` 또는 `FaissBackend`
6. B0~B5 retrieval
7. metrics/latency 산출

선택:

1. `E5LargeTextEmbedding`
2. `PyseriniBackend`
3. `BgeReranker`
4. `SigLIPKeyframeEmbedding`
5. `InternVL3` evidence-aware VQA

## 리스크 관리

| 리스크 | 대응 |
|---|---|
| pgvector 설치 지연 | FAISS + SQLite metadata filter로 먼저 실험하고 pgvector는 후속 backend로 추가 |
| embedding model 설치 지연 | sentence-transformers 호환 모델 또는 sklearn TF-IDF baseline으로 임시 검증 |
| 새 데이터셋 schema 불일치 | DatasetAdapter에서만 처리하고 canonical schema는 유지 |
| metadata facet 불균형 | weak/medium/strong query를 facet 빈도 기반으로 자동 생성 |
| vector backend마다 filter semantics 차이 | backend capability와 filtering mode를 run manifest에 기록 |
| VLM inference 지연 | VLM 실험은 optional로 두고 retrieval-only 결과로 논문 핵심 구성 |

## 최종 권장 결론

본 연구의 실험 시스템은 다음 세 문장으로 요약할 수 있다.

1. 데이터셋은 DatasetAdapter를 통해 공통 `clip-document-metadata-query-qrels` schema로 정규화한다.
2. embedding model과 vector backend는 독립 모듈로 두어 동일 query/qrels에서 교체 실험이 가능하게 한다.
3. 논문 main result는 B0~B5 retrieval strategy 비교로 고정하고, 데이터셋/모델/backend 추가는 robustness 및 extension matrix로 흡수한다.
