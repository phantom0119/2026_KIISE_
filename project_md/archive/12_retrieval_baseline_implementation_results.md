# Retrieval Baseline 구현 및 1차 결과

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 본 문서는 VRU text/metadata B0--B5 baseline의 최초 실행 기록으로 보존한다. 이후 AI Hub 지능형 CCTV, visual keyframe retrieval, fusion, image-to-video, service packet, answer-level LLM/VLM, index benchmark가 추가되었으므로 최신 전체 실험 해석은 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 목적

이 문서는 KIISE 데이타베이스연구 투고용 실험의 첫 번째 동작 가능한 baseline을 고정한다. 핵심 목적은 특정 embedding 모델 하나의 우수성을 주장하는 것이 아니라, 교통 안전 멀티모달 데이터에서 **텍스트 증거 검색과 구조화 metadata 조건을 함께 다루는 검색 구조**가 실제로 BM25-only 또는 vector-only보다 유효한지 검증하는 것이다.

## 구현 범위

| 구성요소 | 구현 파일 | 상태 |
|---|---|---|
| VRU-Accident DatasetAdapter | `2026_KIISE/src/vlmdb_workload/adapters/vru_accident.py` | 완료 |
| canonical artifact builder | `2026_KIISE/scripts/build_vru_canonical.py` | 완료 |
| text embedding provider | `2026_KIISE/src/vlmdb_workload/embeddings.py` | 완료 |
| embedding build script | `2026_KIISE/scripts/build_text_embeddings.py` | 완료 |
| retrieval strategies/evaluator | `2026_KIISE/src/vlmdb_workload/retrieval.py` | 완료 |
| baseline runner | `2026_KIISE/scripts/run_retrieval_baselines.py` | 완료 |

## 데이터와 워크로드

주 데이터셋은 VRU-Accident다. 원본 영상은 `Datasets/raw/VRU-Accident/VRU_videos`에 있고, 실험용 canonical 산출물은 `Datasets/processed/vru_accident/20260706/canonical`에 있다.

| artifact | count |
|---|---:|
| clips | 1,000 |
| documents | 7,000 |
| metadata rows | 6,000 |
| retrieval queries | 244 |
| qrels | 5,488 |
| missing media | 0 |

질의 생성은 평가 누수를 피하기 위해 세 조건을 분리했다.

| 필드 | 의미 |
|---|---|
| `query_text` | 사고 유형 등 의미 검색 대상 |
| `metadata_filter` | road type, location, weather/light 같은 컨텍스트 조건 |
| `qrel_filter` | 의미 조건과 컨텍스트 조건을 함께 적용한 정답 조건 |

이 설계가 중요한 이유는 `metadata_filter`만으로 정답이 결정되는 실험을 피하고, "의미 검색 + metadata-aware filtering"의 결합 효과를 측정하기 위해서다.

## 비교 전략

| ID | 전략 | 구현 의미 |
|---|---|---|
| B0 | Metadata-only | metadata 조건만으로 후보를 정렬 |
| B1 | BM25-only | 텍스트 lexical baseline |
| B2 | Vector-only | dense embedding baseline |
| B3 | Vector + postfilter | dense top-N 검색 후 metadata 조건 적용 |
| B4 | Metadata prefilter + vector | metadata 조건으로 후보를 먼저 좁힌 뒤 dense 검색 |
| B5 | Hybrid sparse+dense+metadata | BM25와 vector를 결합하고 metadata 조건 적용 |

## 실행 명령

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/check_research_resources.py
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_vru_canonical.py --overwrite
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_text_embeddings.py --model-id bge-m3 --batch-size 16 --overwrite
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/run_retrieval_baselines.py --overwrite
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/generate_retrieval_paper_assets.py
```

robustness check:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_text_embeddings.py --model-id e5-large-v2 --batch-size 16 --overwrite
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/run_retrieval_baselines.py \
  --embedding-root Datasets/processed/vru_accident/20260706/embeddings/e5-large-v2 \
  --output-dir Datasets/processed/vru_accident/20260706/results/vru_e5_faiss_b0_b5 \
  --overwrite
```

## bge-m3 결과

결과 경로: `Datasets/processed/vru_accident/20260706/results/vru_bgem3_faiss_b0_b5`

| strategy | recall@10 | recall@20 | MRR | nDCG@10 | mean latency |
|---|---:|---:|---:|---:|---:|
| B0 metadata-only | 0.2141 | 0.2879 | 0.2424 | 0.2102 | 0.057 ms |
| B1 BM25-only | 0.3998 | 0.5434 | 0.4791 | 0.4495 | 131.103 ms |
| B2 vector-only | 0.3853 | 0.5230 | 0.4888 | 0.4476 | 118.295 ms |
| B3 vector postfilter | 0.7343 | 0.8217 | 0.9590 | 0.9488 | 4.877 ms |
| B4 prefilter vector | 0.7629 | 0.8591 | 0.9672 | 0.9736 | 49.442 ms |
| B5 hybrid | 0.7568 | 0.8605 | 0.9726 | 0.9651 | 179.300 ms |

해석:

- BM25-only와 vector-only는 비슷한 수준이며, 둘 다 metadata-aware 구조보다 낮다.
- B4는 recall@10과 nDCG@10에서 가장 강하다.
- B5는 recall@20과 MRR이 높아, 상위 후보 안정성 측면에서 보조 가치가 있다.
- strong query에서 B4/B5가 거의 포화 성능을 보이는 것은 컨텍스트 조건이 강해질수록 prefilter 구조가 유리하다는 논문 주장을 뒷받침한다.

## e5-large-v2 결과

결과 경로: `Datasets/processed/vru_accident/20260706/results/vru_e5_faiss_b0_b5`

| strategy | recall@10 | recall@20 | MRR | nDCG@10 | mean latency |
|---|---:|---:|---:|---:|---:|
| B0 metadata-only | 0.2141 | 0.2879 | 0.2424 | 0.2102 | 0.057 ms |
| B1 BM25-only | 0.3998 | 0.5434 | 0.4791 | 0.4495 | 131.554 ms |
| B2 vector-only | 0.3339 | 0.4876 | 0.3596 | 0.3482 | 119.605 ms |
| B3 vector postfilter | 0.6666 | 0.7673 | 0.7799 | 0.7911 | 5.031 ms |
| B4 prefilter vector | 0.7142 | 0.8259 | 0.8008 | 0.8311 | 48.247 ms |
| B5 hybrid | 0.7390 | 0.8482 | 0.9270 | 0.9229 | 178.970 ms |

해석:

- embedding 모델을 e5-large-v2로 바꿔도 metadata-aware 계열 B3/B4/B5가 우위라는 결론은 유지된다.
- e5-large-v2에서는 B5 hybrid가 가장 강해, embedding model 변화에 따라 hybrid 결합의 가치가 달라질 수 있음을 보인다.
- 이 결과는 본 연구가 "특정 모델 튜닝"이 아니라 모듈형 DB retrieval 구조 비교라는 점을 방어하는 데 유리하다.

## 논문에 사용할 수 있는 핵심 주장

1. 교통 안전 영상 검색에서 텍스트 evidence만 쓰는 BM25/vector baseline은 의미 조건과 상황 metadata가 결합된 질의를 충분히 처리하지 못한다.
2. metadata-aware retrieval은 두 embedding 모델 모두에서 일관되게 Recall@10과 nDCG@10을 크게 개선한다.
3. prefilter와 postfilter의 차이는 단순 구현 차이가 아니라 DB 질의 계획 관점의 연구 대상이다.
4. canonical schema와 adapter 구조를 통해 AI Hub CCTV, WTS, TUMTraffic 같은 추가 데이터셋으로 확장할 수 있다.

## 논문용 표/그림 산출물

산출물 경로: `2026_KIISE/paper_assets/20260706`

| 산출물 | 파일 |
|---|---|
| 전체 성능표 | `tables/table_overall_retrieval_metrics.md`, `.csv`, `.tex` |
| 난도별 성능표 | `tables/table_difficulty_retrieval_metrics.md`, `.csv`, `.tex` |
| latency 표 | `tables/table_latency_summary.md`, `.csv`, `.tex` |
| 전체 품질 그림 | `figures/fig_overall_quality_by_strategy.png`, `.pdf` |
| latency 그림 | `figures/fig_latency_by_strategy.png`, `.pdf` |
| 난도별 nDCG heatmap | `figures/fig_difficulty_ndcg_heatmap.png`, `.pdf` |
| recall-latency trade-off | `figures/fig_recall_latency_tradeoff.png`, `.pdf` |

## 남은 보강 작업

| 우선순위 | 작업 | 목적 |
|---:|---|---|
| 1 | 결과 표/그림 자동 생성 | 완료 |
| 2 | AI Hub 지능형 CCTV adapter | 완료. 국내 CCTV 보강 실험은 `13_aihub_cctv_extension_results.md` 참조 |
| 3 | pgvector backend 구현 | 완료. DB backend 결과는 `14_pgvector_backend_results.md` 참조 |
| 4 | 오류 사례 분석 | strong/medium/weak query별 정성 분석 |
| 5 | optional reranker | B6 upper-bound 실험 |
