# 실험 리소스 구축 상태 재점검

작성 기준일: 2026-07-07

2026-07-09 최신 갱신: 본 문서의 "3개 데이터셋 기준 구축 완료" 판단은 2026-07-07 중간 상태다. 이후 다각도 CCTV와 시내도로 CCTV가 본문 실험에 추가 반영되었고, fixed LLM/VLM answer-level 및 ANN index benchmark까지 완료되었다. 최신 리소스 준비 상태는 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 결론

KIISE DBR 투고용 main experiment 체계는 현재 3개 데이터셋 기준으로 구축 완료 상태로 판단한다.

현재 실험 시스템은 다음 주장을 방어할 수 있는 수준이다.

> 동일한 canonical workload 위에서 embedding model, sparse retrieval, vector backend, metadata filtering 위치를 분리해 비교할 수 있다.

추가로 반드시 구축해야 하는 embedding model, VLM, vector database는 없다. 남은 리소스는 논문 범위를 넓히기 위한 선택 항목이다.

## 점검 기준

이번 점검은 다음을 확인했다.

| 영역 | 점검 내용 | 판정 |
|---|---|---|
| 실행 환경 | 연구용 conda env와 핵심 Python module | 정상 |
| GPU/저장소 | RTX 3090 24GB x2, `/hdd2` 여유 공간 | 정상 |
| 모델 asset | `bge-m3`, `e5-large-v2` 로컬 모델 | 정상 |
| canonical workload | VRU, AI Hub 지능형 CCTV, AI Hub 이상행동 CCTV parquet/jsonl/tsv | 정상 |
| embedding artifact | dataset x model별 document/query embedding | 정상 |
| retrieval baseline | BM25/FAISS B0~B5 | 정상 |
| DB backend | PostgreSQL 16 + pgvector P2/P4 | 정상 |
| 논문 산출물 | 표/그림, 결과 summary | 정상 |
| optional model | reranker, VLM, SigLIP | 미구축, 필수 아님 |

## 실행 환경

연구용 Python은 반드시 아래 환경을 사용해야 한다.

```bash
Datasets/envs/kiise-vlmdb/bin/python
```

확인 결과:

| 항목 | 상태 |
|---|---|
| Python | 3.10.20 |
| pandas | 2.3.3 |
| pyarrow | 24.0.0 |
| torch | 2.12.1+cu130 |
| sentence-transformers | 5.6.0 |
| faiss | 1.14.3 |
| psycopg | 3.3.4 |
| pgvector Python package | import 가능 |

주의: 기본 `/opt/anaconda3/bin/python` 환경에서는 현재 parquet 파일 읽기에서 `Repetition level histogram size mismatch` 오류가 발생했다. 이는 리소스 부재가 아니라 실행 환경 불일치 문제다. 따라서 모든 재현 명령은 `conda run -p Datasets/envs/kiise-vlmdb ...` 또는 위 env의 Python으로 수행해야 한다.

리소스 점검 명령:

```bash
Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/scripts/check_research_resources.py
```

## 하드웨어와 저장소

| 항목 | 확인 결과 |
|---|---|
| GPU 0 | NVIDIA GeForce RTX 3090, 24576 MiB |
| GPU 1 | NVIDIA GeForce RTX 3090, 24576 MiB |
| `/hdd2` | 3.6T 중 1.1T 사용, 약 2.4T 여유 |
| `/hdd` | 3.6T 중 900G 사용, 약 2.6T 여유 |
| project root disk | 916G 중 517G 사용, 약 353G 여유 |

현재 모델과 처리 산출물의 사용량은 작다.

| 경로 | 사용량 |
|---|---:|
| `Datasets/models` | 7.1G |
| `Datasets/external` | 592G |
| `Datasets/raw` | 16G |
| `Datasets/processed` | 121M |
| `Datasets/services` | 8.0K |

따라서 현재 동결된 실험 범위에서는 저장소가 병목이 아니다. 단, 500GB급 신규 영상 데이터셋을 추가로 압축 해제하는 확장 실험은 이번 투고 본문에서는 금지한다.

## 모델 리소스

필수 모델은 이미 확보되어 있다.

| 모델 | 경로 | 상태 | 역할 |
|---|---|---|---|
| `BAAI/bge-m3` | `Datasets/models/huggingface/BAAI--bge-m3` | 확보 | main dense text embedding |
| `intfloat/e5-large-v2` | `Datasets/models/huggingface/intfloat--e5-large-v2` | 확보 | embedding robustness |

모델 파일 확인:

| 모델 | 주요 파일 |
|---|---|
| `bge-m3` | `config.json`, `modules.json`, `tokenizer.json`, `pytorch_model.bin` |
| `e5-large-v2` | `config.json`, `modules.json`, `tokenizer.json`, `model.safetensors`, `pytorch_model.bin` |

이미 생성된 embedding:

| dataset | model | document embedding | query embedding |
|---|---|---:|---:|
| VRU-Accident | bge-m3 | `(7000, 1024)` | `(244, 1024)` |
| VRU-Accident | e5-large-v2 | `(7000, 1024)` | `(244, 1024)` |
| AI Hub CCTV | bge-m3 | `(807, 1024)` | `(133, 1024)` |
| AI Hub CCTV | e5-large-v2 | `(807, 1024)` | `(133, 1024)` |
| AI Hub 이상행동 CCTV | bge-m3 | `(5904, 1024)` | `(424, 1024)` |
| AI Hub 이상행동 CCTV | e5-large-v2 | `(5904, 1024)` | `(424, 1024)` |

따라서 main 논문을 위해 추가 embedding model을 반드시 받을 필요는 없다.

## 미구축 선택 모델

아래 모델들은 현재 로컬에 없다.

| 모델 | 상태 | 판단 |
|---|---|---|
| `BAAI/bge-reranker-v2-m3` | 미구축 | B6 reranker upper-bound용 선택 항목 |
| `google/siglip-*` 계열 | 미구축 | keyframe image-text ablation용 선택 항목 |
| `OpenGVLab/InternVL3-8B` | 미구축 | VLM answer generation 선택 항목 |
| `Qwen/Qwen2.5-VL-7B-Instruct` | 미구축 | VLM robustness 선택 항목 |

이들은 현재 논문 주장의 필수 조건이 아니다. 특히 VLM answer generation을 넣으면 모델 backbone 효과가 커져 DB 구조 기여가 흐려질 수 있다. 2주 투고 일정에서는 retrieval-only main result를 유지하는 편이 더 안전하다.

다만 시간이 남을 때 가장 비용 대비 효과가 큰 선택 항목은 `BAAI/bge-reranker-v2-m3`다. 이유는 기존 B5 top-k 결과 위에 reranking upper-bound를 얹을 수 있어, 새 데이터셋보다 실험 범위 증가가 작기 때문이다.

## Vector Database 리소스

현재 실행 중인 vector/database 관련 컨테이너:

| container | image | 상태 | 본 연구 사용 여부 |
|---|---|---|---|
| `kiise-vlmdb-pgvector` | `pgvector/pgvector:pg16` | Up | 사용 |
| `qdrant` | `qdrant/qdrant:v1.15.5` | Up | 미사용, 확장 후보 |
| `milvus-standalone` | `milvusdb/milvus:v2.6.0` | Up | 미사용, 확장 후보 |
| `weaviate-1.35.3` | `semitechnologies/weaviate:1.35.3` | Up | 미사용, 확장 후보 |

본 연구의 DB backend는 PostgreSQL 16 + pgvector다.

접속 정보:

| 항목 | 값 |
|---|---|
| host | `localhost` |
| port | `5433` |
| database | `vlmdb` |
| user | `vlmdb` |
| password | `vlmdb` |

DB 확인 결과:

| table | rows |
|---|---:|
| `vru_accident_20260706_bge_m3_documents` | 7,000 |
| `vru_accident_20260706_bge_m3_metadata` | 6,000 |

`vector` extension도 활성화되어 있다.

현재 pgvector 결과는 exact cosine search 기반이다. 문서 일부에 `pgvector_hnsw`라고 적힌 표현은 최종 원고에서 `pgvector exact search`로 고쳐 쓰는 것이 정확하다. HNSW/IVFFlat index 실험은 대규모 확장성 주장까지 하려는 경우에만 선택적으로 추가한다.

## Retrieval 결과 리소스

현재 main/robustness/extension 결과는 생성되어 있다.

| dataset | model/backend | 결과 경로 | 상태 |
|---|---|---|---|
| VRU-Accident | bge-m3 + BM25/FAISS B0~B5 | `Datasets/processed/vru_accident/20260706/results/vru_bgem3_faiss_b0_b5` | 완료 |
| VRU-Accident | e5-large-v2 + BM25/FAISS B0~B5 | `Datasets/processed/vru_accident/20260706/results/vru_e5_faiss_b0_b5` | 완료 |
| VRU-Accident | bge-m3 + pgvector P2/P4 | `Datasets/processed/vru_accident/20260706/results/vru_bgem3_pgvector_p2_p4` | 완료 |
| AI Hub CCTV | bge-m3 + BM25/FAISS B0~B5 | `Datasets/processed/aihub_intelligent_cctv/20260706/results/aihub_bgem3_faiss_b0_b5` | 완료 |
| AI Hub CCTV | e5-large-v2 + BM25/FAISS B0~B5 | `Datasets/processed/aihub_intelligent_cctv/20260706/results/aihub_e5_faiss_b0_b5` | 완료 |
| AI Hub 이상행동 CCTV | bge-m3 + BM25/FAISS B0~B5 | `Datasets/processed/aihub_abnormal_cctv/20260707/results/abnormal_bgem3_faiss_b0_b5` | 완료 |
| AI Hub 이상행동 CCTV | e5-large-v2 + BM25/FAISS B0~B5 | `Datasets/processed/aihub_abnormal_cctv/20260707/results/abnormal_e5_faiss_b0_b5` | 완료 |

논문용 표/그림:

```text
2026_KIISE/paper_assets/20260706
```

## 추가 리소스 필요성 판단

### 필수로 추가 구축할 필요가 없는 것

| 리소스 | 이유 |
|---|---|
| 추가 text embedding model | bge-m3 main, e5 robustness로 이미 모델 의존성 방어 가능 |
| Qdrant/Milvus/Weaviate backend | 본 논문은 DB 제품 비교가 아니라 metadata filter 결합 위치 비교가 핵심 |
| VLM/LLM answer generator | 현재 연구 질문은 evidence retrieval 구조 비교로 충분히 성립 |
| SigLIP/CLIP visual embedding | 이미지 질의 또는 keyframe fusion까지 주장하지 않으면 필수 아님 |
| Pyserini | 현재 Python BM25로 baseline은 존재하며, 일정상 교체 실익이 제한적 |

### 추가하면 좋은 선택 항목

| 우선순위 | 리소스 | 추가 가치 | 리스크 |
|---:|---|---|---|
| 1 | 오류 사례 분석용 sampling script | 논문 설득력 직접 상승 | 낮음 |
| 2 | pgvector HNSW/IVFFlat index 실험 | DB index 논문성 강화 | 중간 |
| 3 | `bge-reranker-v2-m3` | B6 upper-bound 제공 | 중간 |
| 4 | AI Hub 522 데이터셋 adapter | 센서/교통 구조화 메타데이터 공백 보강 | 데이터 확보 필요 |
| 5 | SigLIP keyframe embedding | 이미지 질의 확장 | 프레임 추출/추론 비용 |
| 6 | VLM answer generation | VLM-DB 명칭 강화 | 시간 비용 큼, DB 기여 흐림 |

2주 일정 기준으로는 1번만 사실상 필수에 가깝고, 2~3번은 시간이 남을 때 선택하면 된다.

## 최종 판정

현재 상태는 다음처럼 정리한다.

1. 현재 3개 데이터셋 기준 main experiment 체계는 제대로 구축되어 있다.
2. 필수 모델은 `bge-m3`와 `e5-large-v2`로 충분하다.
3. 필수 DB backend는 PostgreSQL+pgvector로 충분하며, FAISS는 reference backend 역할을 한다.
4. Qdrant, Milvus, Weaviate는 이미 컨테이너가 떠 있지만 본 연구에는 필수로 연결할 필요가 없다.
5. 추가 구축보다 우선할 작업은 오류 사례 분석, 결과 해석, 원고 실험 섹션 작성이다.

따라서 다음 단계는 새 모델/DB 구축이 아니라, 현재 결과를 논문 주장으로 묶는 분석 작업이다.
