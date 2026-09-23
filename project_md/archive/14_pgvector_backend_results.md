# pgvector Backend 보강 실험

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 이 문서의 pgvector 결과는 VRU text embedding에 대한 DB backend feasibility와 SQL prefilter 재현성 근거로 유지한다. 대규모 ANN 색인 구조 평가는 이후 시내도로 CCTV 132K real vector와 1M scale benchmark에서 별도로 수행되었으며, 최신 index 해석은 `39_index_structure_benchmark_results_20260709.md`를 따른다.

## 목적

FAISS/parquet baseline은 빠른 실험에는 적합하지만, DBR 논문에서는 데이터베이스 내부에서 metadata filter와 vector search가 결합되는 구조를 보여주는 것이 중요하다. 이 문서는 VRU-Accident bge-m3 workload를 PostgreSQL 16 + pgvector에 적재하고, SQL metadata prefilter + vector search가 기존 B4 결과를 재현하는지 확인한 결과다.

## 구현

| 구성요소 | 파일/경로 |
|---|---|
| docker compose | `2026_KIISE/infra/docker-compose.pgvector.yml` |
| pgvector runner | `2026_KIISE/scripts/run_pgvector_retrieval.py` |
| 결과 경로 | `Datasets/processed/vru_accident/20260706/results/vru_bgem3_pgvector_p2_p4` |
| PostgreSQL table prefix | `vru_accident_20260706_bge_m3` |

적재 테이블:

| table | rows |
|---|---:|
| `vru_accident_20260706_bge_m3_documents` | 7,000 |
| `vru_accident_20260706_bge_m3_metadata` | 6,000 |

## 실행 명령

```bash
docker compose -f 2026_KIISE/infra/docker-compose.pgvector.yml up -d
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/run_pgvector_retrieval.py --overwrite
```

## 비교 전략

| ID | 의미 |
|---|---|
| P2 | pgvector vector-only exact cosine search |
| P4 | SQL metadata prefilter 후 pgvector exact cosine search |

## 전체 결과

| strategy | recall@10 | recall@20 | MRR | nDCG@10 | mean latency |
|---|---:|---:|---:|---:|---:|
| P2 pgvector vector-only | 0.3799 | 0.5142 | 0.4992 | 0.4473 | 20.309 ms |
| P4 pgvector prefilter vector | 0.7629 | 0.8591 | 0.9672 | 0.9736 | 10.239 ms |

난도별 핵심 결과:

| difficulty | P2 recall@10 | P2 nDCG@10 | P4 recall@10 | P4 nDCG@10 |
|---|---:|---:|---:|---:|
| weak | 0.4895 | 0.9118 | 0.4895 | 0.9118 |
| medium | 0.4425 | 0.4807 | 0.7662 | 0.9795 |
| strong | 0.2435 | 0.1905 | 0.8823 | 0.9935 |

## 해석

- P4 pgvector는 FAISS B4와 동일한 품질을 재현했다.
- medium/strong query에서 SQL metadata prefilter가 vector-only 대비 큰 폭으로 개선된다.
- P4 평균 latency는 10.239 ms로, 현재 Python 기반 FAISS prefilter 구현보다 낮다. 이는 DB 내부 후보 필터링과 vector 계산을 결합하는 설계가 실험 규모에서도 실용적임을 보여준다.
- 본 결과는 논문에서 "metadata-aware retrieval은 모델 문제가 아니라 DB 질의 계획과 저장 구조의 문제"라는 주장을 강화하는 근거로 사용할 수 있다.

## 주의

현재 pgvector 실험은 exact search다. 따라서 이 문서만으로 pgvector HNSW/IVFFlat 확장성을 주장하지 않는다. 다만 2026-07-09 최신 기준에서는 별도 시내도로 CCTV visual vector corpus에서 FAISS Flat/IVF-Flat/HNSW/IVF-PQ benchmark를 완료했으므로, 대규모 색인 구조 trade-off는 `39_index_structure_benchmark_results_20260709.md`를 기준으로 해석한다.
