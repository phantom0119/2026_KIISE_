# VLM-DB Workload 코어 엔진 (`vlmdb_workload`)

`vlmdb_workload`는 2026 KIISE 논문의 **멀티모달 비디오 RAG 및 벡터 데이터베이스 계층 실험을 구동하는 핵심 파이썬 패키지**입니다.  
이기종 원천 데이터셋의 비순환 표준화(Canonicalization), 텍스트/시각 임베딩 생성, B0~B5 검색 전략 수행, 정밀 랭킹 평가 지표(nDCG, Recall, MRR) 산출을 전담합니다.

---

## 📁 패키지 구조 및 모듈 개요

```
vlmdb_workload/
├── __init__.py           # 패키지 버전(0.1.0) 및 엔트리포인트
├── io.py                 # 표준 5대 Canonical 아티팩트 입출력 및 파싱
├── metrics.py            # IR 랭킹 평가 지표 계산 (Recall@k, Hit@k, MRR, nDCG@k)
├── embeddings.py         # SentenceTransformers 임베딩 공급자 및 배치 빌더
├── retrieval.py          # B0~B5 검색 베이스라인 실행기 및 RRF 순위 융합
└── adapters/             # 이기종 데이터셋을 Canonical 표준 규격으로 변환하는 어댑터 모음
    ├── __init__.py
    ├── vru_accident.py             # VRU-Accident 사고 영상 데이터셋 어댑터
    ├── aihub_intelligent_cctv.py   # AI Hub 지능형 관제 CCTV 데이터셋 어댑터
    ├── aihub_abnormal_cctv.py      # AI Hub 이상행동 CCTV 데이터셋 어댑터
    └── aihub_multi_angle_cctv.py   # AI Hub 다각도 CCTV 생활안전 데이터셋 어댑터
```

---

## 🛠️ 주요 모듈별 상세 기능 명세

### 1. [`io.py`](io.py) — 표준 데이터 입출력
- **`load_canonical(canonical_root)`**:
  - 연구의 표준 정본 데이터셋을 구성하는 **5대 Canonical 아티팩트**를 일괄 로드하여 Pandas 데이터프레임 튜플로 반환합니다:
    1. `clips.parquet`: 비디오 클립 메타데이터 (clip_id, duration, video_path 등)
    2. `documents.parquet`: 검색 대상 텍스트 (설명문, 객체 라벨, 시간 구간)
    3. `metadata.parquet`: 시공간/환경 패싯 (날씨, 조도, 위치, 사고 유형 등)
    4. `queries.jsonl`: 평가용 자연어 질의 및 메타데이터 필터 조건
    5. `qrels.tsv`: 엄격(Strict) 정답 판정 매핑 테이블
- **`read_jsonl(path)` / `write_json(path, obj)`**: JSONL 및 JSON 직렬화 유틸리티.

### 2. [`metrics.py`](metrics.py) — 랭킹 및 검색 품질 평가
- **`recall_at_k(ranking, positives, k)`**: 상위 $k$개 결과 내 정답 클립 포함 비율 ($\text{Hits} / |\text{Positives}|$)
- **`hit_at_k(ranking, positives, k)`**: 상위 $k$개 결과 내 정답이 1개라도 존재하는지 여부 (Binary)
- **`reciprocal_rank(ranking, positives)`**: 첫 번째 정답 클립이 등장한 순위의 역수 (MRR 계산용)
- **`ndcg_at_k(ranking, positives, k, relevance=3.0)`**: 이진 관련도 기준 Discounted Cumulative Gain 및 이상적 IDCG 정규화 ($n\text{DCG}@k$)
- **`evaluate_ranking(ranking, positives, top_ks)`**: 지정한 Top-$k$ 목록에 대해 전체 지표를 딕셔너리로 일괄 집계.

### 3. [`embeddings.py`](embeddings.py) — 임베딩 런타임 및 빌더
- **`SentenceTransformerEmbeddingProvider`**:
  - `SentenceTransformer` 모델(e5-large-v2, bge-m3 등)을 래핑하여 배치 단위 인코딩 지원
  - E5 계열 모델용 `query: ` / `passage: ` 비대칭 프리픽스 자동 처리
  - 코사인 유사도 연산을 위한 L2 정규화(`normalize_embeddings=True`) 기본 지원
- **`build_text_embeddings(...)`**:
  - Canonical 문서와 질의를 일괄 인코딩하여 `document_embeddings.npy`, `query_embeddings.npy`, 매핑 parquet 및 메타 manifest를 산출.

### 4. [`retrieval.py`](retrieval.py) — 6대 검색 베이스라인 실행기
논문 본문에서 다룬 6대 검색 전략(B0~B5)을 동일 작업 부하에서 체계적으로 실행하고 지연시간과 품질을 측정합니다.

| 전략 ID | 전략 명칭 | 동작 원리 |
|:---:|---|---|
| **B0** | `metadata_only` | 질의 텍스트를 배제하고 시공간 메타데이터 필터 조건만 만족하는 클립 반환 |
| **B1** | `bm25_only` | Okapi BM25 기반 키워드 어휘 검색 순위 산출 |
| **B2** | `vector_only` | Dense 임베딩 코사인/내적 유사도 기반 순수 벡터 검색 |
| **B3** | `vector_postfilter` | 상위 200개 벡터 검색 후보 풀을 먼저 추출한 후 메타데이터 조건 사후 필터링 |
| **B4** | `prefilter_vector` | 메타데이터 조건을 만족하는 후보군만 사전에 추린 후 내부 벡터 검색 |
| **B5** | `hybrid` | BM25 순위와 벡터 검색 순위를 Reciprocal Rank Fusion ($k=60$)으로 결합 |

- **`RetrievalExperimentRunner`**:
  - 입력받은 Canonical 및 임베딩 데이터를 바탕으로 B0~B5를 순차 평가
  - 질의별 지연시간(`latency_ms`) 및 메트릭을 `retrieval_results.parquet`, `metrics_by_query.parquet`, `metrics_summary.csv`로 저장.

### 5. [`adapters/`](adapters/) — 이기종 데이터셋 Canonical 어댑터
- **`VRUAccidentAdapter`** (`vru_accident.py`):
  - Hugging Face VRU-Accident 원천 데이터를 파싱하여 날씨, 도로, 위치 속성을 추출하고 순환 누수 없는 1,000 clips / 85 queries 정본 생성.
- **`AIHubIntelligentCCTVAdapter`** (`aihub_intelligent_cctv.py`):
  - AI Hub 지능형 관제(싸움, 쓰러짐, 침입 등)의 XML/JSON 라벨을 파싱하여 사건 분류 및 시공간 패싯 정규화.
- **`AIHubMultiAngleCCTVAdapter`** (`aihub_multi_angle_cctv.py`):
  - AI Hub 다각도 CCTV 생활안전(71953) 압축 아카이브를 스트리밍 탐색하여 다중 카메라 시점(Multi-view) 및 VLM QA용 증거 프레임 인덱스 생성.

---

## 💻 사용 예시 (Usage Example)

```python
from pathlib import Path
from vlmdb_workload.io import load_canonical
from vlmdb_workload.retrieval import RetrievalExperimentRunner

# 1. 표준 데이터 로드
canonical_root = Path("Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded")
clips, documents, metadata, queries, qrels = load_canonical(canonical_root)
print(f"Loaded {len(clips)} clips and {len(queries)} queries.")

# 2. 검색 베이스라인 일괄 벤치마크 실행
runner = RetrievalExperimentRunner(
    canonical_root=canonical_root,
    embedding_root=Path("Datasets/processed/aihub_522_intersection/embeddings/bge-m3"),
    output_dir=Path("experiments/retrieval_benchmark_results"),
    top_ks=[1, 3, 5, 10],
    max_rank=100,
)
result = runner.run(overwrite=True)
print(f"Completed benchmark: {result.strategies} for {result.queries} queries.")
```

---

## 🔗 연계 디렉터리
- **실행 스크립트**: [`04_scripts/`](../../04_scripts/) 내의 모든 전처리, 색인 생성, 벤치마크 스크립트가 본 패키지의 API를 호출합니다.
- **연구 정본 문서**: 본 패키지의 아키텍처 및 B0~B5 설계 근거는 [`02_project_md/00_KIISE_DBR_FINAL_MASTER_SPECIFICATION.md`](../../02_project_md/00_KIISE_DBR_FINAL_MASTER_SPECIFICATION.md)에 상세히 기술되어 있습니다.
