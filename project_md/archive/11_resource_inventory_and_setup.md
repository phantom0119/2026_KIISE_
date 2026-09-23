# 연구 리소스 인벤토리와 구축 방법

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 이 문서의 "현재 단계" 설명은 2026-07-06 baseline 시점이다. 최신 기준에서는 다각도 CCTV, 시내도로 CCTV, 교차로신호체계, CityFlow-NL이 추가 확보되었고, fixed LLM/VLM answer-level 실험과 시내도로 ANN index benchmark까지 완료되었다. 최신 리소스·산출물 기준은 `40_latest_dataset_and_experiment_synthesis_20260709.md`와 `manuscript/submission_materials_index.md`를 따른다.

## 목적

이 문서는 KIISE 데이타베이스연구 투고 실험을 진행하기 위해 필요한 데이터, 코드, 모델, 실행 환경, vector database 리소스의 저장 위치와 구축 방법, 활용 방법을 고정한다.

현재 단계는 **테스트 목적의 워크로드 구현과 1차 검색 baseline 검증 완료 단계**다. 원본 데이터, canonical workload, embedding, BM25/FAISS 기반 B0~B5 retrieval baseline을 확보했고, 다음은 논문용 표/그림 정리와 pgvector backend 보강이다.

2026-07-06 현재 연구용 conda 환경, 필수 embedding 모델 asset, bge-m3/e5-large-v2 embedding 산출물, retrieval 결과 산출물까지 확보했다.

## 저장소 루트

| 구분 | 경로 | 상태 |
|---|---|---|
| 프로젝트 루트 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety` | 현재 작업 루트 |
| 논리 데이터 루트 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets` | symlink |
| 물리 데이터 루트 | `/hdd2/KIISE_datasociety/Datasets` | 실제 저장 위치 |
| 잔여 공간 | `/hdd2` 약 3.0T | 대용량 모델/DB/결과 저장 가능 |

실험 코드에서는 항상 논리 경로 `Datasets`를 사용한다.

## 확보된 데이터 리소스

### 1. VRU-Accident

| 항목 | 경로 | 상태 |
|---|---|---|
| Hugging Face 원본 clone | `Datasets/external/VRU-Accident_hf` | 확보 완료 |
| source code repo | `Datasets/external/VRU-Accident_repo` | 확보 완료 |
| 원본 영상 zip | `Datasets/external/VRU-Accident_hf/VRU_videos.zip` | 확보 완료 |
| 압축 해제 영상 | `Datasets/raw/VRU-Accident/VRU_videos` | 1,000 mp4 |
| canonical workload | `Datasets/processed/vru_accident/20260706/canonical` | 생성 완료 |

canonical 산출물:

| 파일 | 수량/역할 |
|---|---:|
| `clips.parquet` | 1,000 clips |
| `documents.parquet` | 7,000 searchable documents |
| `metadata.parquet` | 6,000 facet rows |
| `queries.jsonl` | 244 retrieval queries |
| `qrels.tsv` | 5,488 relevance rows |
| `summary.md` | canonical 요약 |

재생성:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_vru_canonical.py --overwrite
```

활용:

- main experiment의 1차 데이터셋.
- dense caption과 VQA-derived facet을 이용해 BM25/vector/metadata-aware retrieval을 평가한다.
- AI Hub/WTS/TUMTraffic 데이터가 추가되면 같은 canonical schema로 확장한다.

### 2. AI Hub 지능형 관제 서비스 CCTV 영상 데이터

| 항목 | 경로 | 상태 |
|---|---|---|
| 압축 원본/라벨 루트 | `Datasets/external/지능형관제서비스CCTV영상데이터` | 확보됨 |
| 실험용 raw 루트 | `Datasets/raw/aihub_intelligent_cctv/20260706` | 추출/정리 완료 |
| 크기 | 압축 원본 약 13G, 실험용 raw 약 13G | `/hdd2` 저장 |
| 파일 구성 | Training/Validation, 원천 mp4 zip 31개, 라벨 json zip 31개 | 총 62 zip |
| 정리 결과 | mp4 269개, json 269개, paired clips 269개 | missing 0 |
| raw manifest | `Datasets/raw/aihub_intelligent_cctv/20260706/summary.md` | 생성 완료 |

활용:

- 현재는 **확보 완료, raw 추출 완료, canonical 변환 및 B0~B5 보강 실험 완료** 상태다.
- `event_caption`, `event_class`, `event_frame`, `night`, `width/height/frame_count`가 있어 국내 CCTV 보강 실험에 바로 투입할 수 있다.
- 다음 작업은 `AIHubIntelligentCCTVAdapter`를 추가해 VRU-Accident와 동일한 canonical schema로 변환하는 것이다.

### 3. 보조 repository

| 리소스 | 경로 | 활용 |
|---|---|---|
| WTS repo | `Datasets/external/WTS_repo` | 데이터 구조/관련연구/승인 후 adapter 작성 참고 |
| CityFlow-NL repo | `Datasets/external/cityflow_nl/cityflow-nl` | annotation-only text-to-track schema sanity check. canonical은 `Datasets/processed/cityflow_nl/20260707/canonical` |
| SUTD-TrafficQA repo | `Datasets/external/SUTD-TrafficQA_repo` | traffic VQA 관련연구 및 sample annotation |
| TUMTraffic-VideoQA baseline | `Datasets/external/TUMTraffic-VideoQA_baseline_repo` | roadside VideoQA baseline 구조 참고 |
| UDVideoQA finetune repo | `Datasets/external/UDVideoQA_finetune_repo` | 교차로 VideoQA 확장 참고 |

### 4. 확보 완료 및 신청/등록 대기 데이터

| 데이터 | 경로 | 상태 |
|---|---|---|
| AI Hub 71953 다각도 CCTV 생활안전 | `Datasets/external/21.다각도 CCTV 생활안전 데이터` | 확보 완료. main multimodal anchor |
| AI Hub 165 시내도로 CCTV | `Datasets/external/교통문제 해결을 위한 CCTV 교통 영상(시내도로)`, `Datasets/external/101.교통문제 해결을 위한 CCTV 교통 데이터(시내도로)` | 확보 완료. urban traffic CCTV extension |
| AI Hub 522 교차로 복합 데이터 | `Datasets/external/교차로신호체계` | 확보 완료. metadata/log extension |
| WTS 원본 | `Datasets/restricted/WTS` | Google Form/Drive 승인 필요 |
| TUMTraffic-VideoQA 원본 | `Datasets/restricted/TUMTraffic-VideoQA` | registration 필요 |

## 코드 리소스

| 코드 | 경로 | 역할 |
|---|---|---|
| Python package root | `2026_KIISE/src/vlmdb_workload` | 공통 실험 코드 |
| VRU adapter | `2026_KIISE/src/vlmdb_workload/adapters/vru_accident.py` | 원본 -> canonical 변환 |
| canonical build script | `2026_KIISE/scripts/build_vru_canonical.py` | VRU canonical 산출물 생성 |
| AI Hub raw preparation script | `2026_KIISE/scripts/prepare_aihub_cctv_raw.py` | AI Hub CCTV zip 원본을 실험용 mp4/json raw 구조로 정리 |
| AI Hub canonical build script | `2026_KIISE/scripts/build_aihub_cctv_canonical.py` | AI Hub CCTV canonical 산출물 생성 |
| paper asset generation script | `2026_KIISE/scripts/generate_retrieval_paper_assets.py` | B0~B5 결과를 논문용 표/그림으로 변환 |
| embedding provider | `2026_KIISE/src/vlmdb_workload/embeddings.py` | bge-m3/e5-large-v2 문서·질의 embedding 생성 |
| embedding build script | `2026_KIISE/scripts/build_text_embeddings.py` | embedding artifact 생성 |
| retrieval/evaluator | `2026_KIISE/src/vlmdb_workload/retrieval.py` | B0~B5 검색 전략과 평가 지표 계산 |
| retrieval run script | `2026_KIISE/scripts/run_retrieval_baselines.py` | BM25/FAISS baseline 실행 |
| pgvector retrieval script | `2026_KIISE/scripts/run_pgvector_retrieval.py` | PostgreSQL+pgvector P2/P4 backend 실행 |
| resource check script | `2026_KIISE/scripts/check_research_resources.py` | 데이터/환경 리소스 점검 |
| environment setup script | `2026_KIISE/scripts/setup_experiment_resources.sh` | conda env 및 패키지 설치 |
| model download script | `2026_KIISE/scripts/download_model_assets.py` | HF 모델 asset 다운로드 |
| pgvector compose | `2026_KIISE/infra/docker-compose.pgvector.yml` | PostgreSQL+pgvector 서비스 |

## 실행 환경 리소스

### 하드웨어

| 항목 | 상태 |
|---|---|
| GPU | NVIDIA GeForce RTX 3090 24GB x 2 |
| Driver | 580.126.09 |
| 대용량 저장소 | `/hdd2`, 약 3.0T free |

### Python 환경

기본 Python은 `/opt/anaconda3/bin/python`, Python 3.13이다. PyTorch/transformers 계열 패키지는 Python 3.13 호환성 리스크가 있으므로 연구용 전용 conda 환경을 새로 만든다.

연구 환경 경로:

```text
Datasets/envs/kiise-vlmdb
```

상태: 구축 완료. `torch`, `transformers`, `sentence-transformers`, `FlagEmbedding`, `faiss`, `rank_bm25`, `psycopg`, `pgvector`, `huggingface_hub` import를 확인했다.

구축:

```bash
bash 2026_KIISE/scripts/setup_experiment_resources.sh
```

활성화:

```bash
conda activate /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/envs/kiise-vlmdb
export PYTHONPATH=/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/src:${PYTHONPATH:-}
export HF_HOME=/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/cache/huggingface
export HF_HUB_CACHE=/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/models/huggingface
export TRANSFORMERS_CACHE=/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/cache/transformers
export TORCH_HOME=/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/cache/torch
```

점검:

```bash
python 2026_KIISE/scripts/check_research_resources.py
```

## 모델 리소스

모델은 루트 디스크가 아니라 아래 경로에 저장한다.

```text
Datasets/models/huggingface
Datasets/cache/huggingface
Datasets/cache/transformers
Datasets/cache/torch
```

필수 모델:

| 모델 | 용도 | 저장 위치 |
|---|---|---|
| `BAAI/bge-m3` | main dense text embedding | `Datasets/models/huggingface/BAAI--bge-m3` |
| `intfloat/e5-large-v2` | robustness embedding | `Datasets/models/huggingface/intfloat--e5-large-v2` |

상태: 필수 모델 2개 다운로드 완료. 두 모델 모두 로컬 경로에서 `sentence-transformers`로 로드했고, 테스트 문장 embedding shape `(1, 1024)` 생성을 확인했다.

선택 모델:

| 모델 | 용도 | 저장 위치 |
|---|---|---|
| `BAAI/bge-reranker-v2-m3` | optional reranker | `Datasets/models/huggingface/BAAI--bge-reranker-v2-m3` |
| `OpenGVLab/InternVL3-8B` 계열 | optional VLM | `Datasets/models/huggingface` 또는 `Datasets/models/manual` |
| `Qwen/Qwen2.5-VL-7B-Instruct` | optional VLM robustness | `Datasets/models/huggingface` 또는 `Datasets/models/manual` |

다운로드:

```bash
python 2026_KIISE/scripts/download_model_assets.py
```

이 스크립트는 PyTorch weight와 tokenizer 중심으로 다운로드하며, main 실험에 불필요한 ONNX/OpenVINO 산출물은 제외한다.

선택 reranker까지 다운로드:

```bash
python 2026_KIISE/scripts/download_model_assets.py --include-optional
```

주의: VLM 모델은 용량과 라이선스/게이트 여부를 확인한 뒤 별도 다운로드한다. main experiment에는 필수가 아니다.

## Vector Database 리소스

### 빠른 baseline

1차 실험은 FAISS + local parquet metadata로 실행 완료했다.

활용:

- `FAISS IndexFlatIP` exact search로 dense retrieval을 수행한다.
- metadata prefilter/postfilter는 canonical `metadata.parquet`를 이용한다.
- 현재 산출물은 `Datasets/processed/vru_accident/20260706/results`에 저장되어 있다.

### DB 논문용 backend

PostgreSQL+pgvector는 DBR 논문 성격을 강화하는 backend다.

서비스 데이터 위치:

```text
Datasets/services/postgres_pgvector
```

실행:

```bash
docker compose -f 2026_KIISE/infra/docker-compose.pgvector.yml up -d
```

접속 정보:

| 항목 | 값 |
|---|---|
| host | `localhost` |
| port | `5433` |
| database | `vlmdb` |
| user | `vlmdb` |
| password | `vlmdb` |

활용:

- `clips`, `documents`, `metadata`, `queries`, `qrels` 테이블을 적재한다.
- `documents.embedding`에 pgvector vector column을 추가한다.
- `WHERE` metadata prefilter와 `ORDER BY embedding <=> query_embedding` 조합으로 B4 실험을 수행한다.

## 실험 산출물 저장 규칙

```text
Datasets/processed/{dataset_id}/{dataset_version}/
  canonical/
  embeddings/{embedding_model_id}/
  indexes/{backend_id}/
  results/{experiment_id}/
```

현재 생성된 주요 산출물:

```text
Datasets/processed/vru_accident/20260706/
  embeddings/bge-m3/
  embeddings/e5-large-v2/
  results/vru_bgem3_faiss_b0_b5/
  results/vru_e5_faiss_b0_b5/
Datasets/processed/aihub_intelligent_cctv/20260706/
  canonical/
  embeddings/bge-m3/
  embeddings/e5-large-v2/
  results/aihub_bgem3_faiss_b0_b5/
  results/aihub_e5_faiss_b0_b5/
Datasets/processed/vru_accident/20260706/
  results/vru_bgem3_pgvector_p2_p4/
```

논문용 표/그림 산출물:

```text
2026_KIISE/paper_assets/20260706/
  tables/
  figures/
  summary.md
```

## 즉시 실행 순서

현재 리소스 점검:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/check_research_resources.py
```

canonical workload 재생성 또는 검증:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_vru_canonical.py --overwrite
```

AI Hub 지능형 CCTV raw 정리 재실행:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/prepare_aihub_cctv_raw.py
```

AI Hub 지능형 CCTV canonical 변환:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_aihub_cctv_canonical.py --overwrite
```

bge-m3 main embedding 생성:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_text_embeddings.py --model-id bge-m3 --batch-size 16 --overwrite
```

B0~B5 retrieval baseline 실행:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/run_retrieval_baselines.py --overwrite
```

논문용 표/그림 생성:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/generate_retrieval_paper_assets.py
```

e5-large-v2 robustness embedding과 baseline 실행:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_text_embeddings.py --model-id e5-large-v2 --batch-size 16 --overwrite
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/run_retrieval_baselines.py \
  --embedding-root Datasets/processed/vru_accident/20260706/embeddings/e5-large-v2 \
  --output-dir Datasets/processed/vru_accident/20260706/results/vru_e5_faiss_b0_b5 \
  --overwrite
```

pgvector backend 실행:

```bash
docker compose -f 2026_KIISE/infra/docker-compose.pgvector.yml up -d
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/run_pgvector_retrieval.py --overwrite
```

현재 다음 작업은 아래 순서다.

1. `metrics_summary.csv`와 `latency_summary.csv` 기반 오류 사례 분석을 추가한다.
2. VRU main result, AI Hub 보강 result, pgvector backend result를 논문 실험 섹션에 반영한다.
3. HNSW/IVFFlat 같은 approximate index 실험은 시간이 남을 때 선택적으로 추가한다.

## 현재 미완료 또는 확인 필요 항목

| 항목 | 상태 | 다음 조치 |
|---|---|---|
| bge-m3/e5 모델 asset | 확보 완료 | optional reranker는 필요 시 추가 다운로드 |
| 연구용 conda env | 구축 완료 | `Datasets/envs/kiise-vlmdb` 사용 |
| FAISS/BM25 retrieval 코드 | 구현 완료 | B0~B5 결과 생성 완료 |
| 논문용 표/그림 | 생성 완료 | `2026_KIISE/paper_assets/20260706` |
| pgvector 서비스 | 실행 완료 | `kiise-vlmdb-pgvector`, port 5433 |
| pgvector backend 결과 | 생성 완료 | `vru_bgem3_pgvector_p2_p4` |
| AI Hub 지능형 CCTV raw 정리 | 완료 | `Datasets/raw/aihub_intelligent_cctv/20260706` 사용 |
| AI Hub 지능형 CCTV canonical/retrieval | 완료 | bge-m3/e5-large-v2 B0~B5 결과 생성 |
