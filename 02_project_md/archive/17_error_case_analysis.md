# 검색 오류 사례 분석과 논문 반영 전략

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 본 문서는 VRU B0--B5 및 pgvector 기반 retrieval 오류 사례 분석 기록이다. 최신 원고에서는 이 분석을 retrieval/evidence-selection 근거로 유지하되, answer-level LLM/VLM 결과와 index benchmark는 별도 최신 문서(`38_four_vlm_multiview_final_recheck_20260709.md`, `39_index_structure_benchmark_results_20260709.md`)를 기준으로 해석한다.

## 목적

현재 가장 중요한 작업은 새 모델이나 DB를 더 붙이는 것이 아니라, 이미 생성된 B0~B5 및 pgvector 결과가 논문 기여로 연결되는 이유를 query 단위로 증명하는 것이다.

이를 위해 VRU-Accident bge-m3 main result를 대상으로 오류 사례 분석 스크립트를 추가하고, 다음 유형의 query를 자동 추출했다.

- vector-only가 실패했지만 metadata prefilter가 복구한 query
- postfilter보다 prefilter가 우수한 query
- hybrid가 prefilter보다 유리한 query
- BM25가 vector-only보다 유리한 query
- metadata prefilter도 실패하는 hard case
- metadata filter가 없는 weak query control

## 생성 산출물

| 산출물 | 경로 |
|---|---|
| 분석 스크립트 | `2026_KIISE/scripts/analyze_retrieval_error_cases.py` |
| 분석 결과 루트 | `2026_KIISE/paper_assets/20260706/error_analysis` |
| 대표 사례 markdown | `2026_KIISE/paper_assets/20260706/error_analysis/summary.md` |
| query별 delta | `2026_KIISE/paper_assets/20260706/error_analysis/query_delta_summary.csv` |
| failure mode 요약 | `2026_KIISE/paper_assets/20260706/error_analysis/failure_mode_summary.csv` |
| pgvector/FAISS 일치성 | `2026_KIISE/paper_assets/20260706/error_analysis/pgvector_faiss_consistency_summary.csv` |

재생성 명령:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/analyze_retrieval_error_cases.py
```

## 핵심 결과

| 분석 항목 | 결과 |
|---|---:|
| 전체 query | 244 |
| B4가 B2 top-10 miss를 복구한 query | 61 |
| B4가 B3보다 Recall@10이 높은 query | 15 |
| B5가 B4보다 Recall@20이 높은 query | 3 |
| BM25가 vector-only보다 nDCG@10 기준 0.10 이상 우수한 query | 23 |
| B4도 top-10 hit에 실패한 query | 5 |

핵심 해석은 명확하다. 단일 dense vector retrieval은 자연어 의미는 잘 잡지만 road type, weather/light, location 같은 구조화 조건을 top-k 안에서 안정적으로 보장하지 못한다. 반면 B4는 먼저 metadata 조건으로 후보 공간을 줄이고 그 안에서 vector ranking을 수행하므로, medium/strong query에서 큰 차이를 만든다.

## 난도별 효과

| difficulty | queries | avg positives | B2 R@10 | B4 R@10 | B2 nDCG@10 | B4 nDCG@10 |
|---|---:|---:|---:|---:|---:|---:|
| weak | 39 | 43.67 | 0.4895 | 0.4895 | 0.9118 | 0.9118 |
| medium | 119 | 24.41 | 0.4552 | 0.7662 | 0.4852 | 0.9795 |
| strong | 86 | 10.23 | 0.2413 | 0.8823 | 0.1851 | 0.9935 |

이 표는 논문에서 매우 중요하다.

- weak query는 metadata filter가 비어 있으므로 B2/B3/B4가 거의 동일하다.
- medium/strong query에서만 B4가 크게 개선된다.
- 따라서 성능 향상은 단순 구현 편향이 아니라 metadata 조건이 있는 질의에서 후보 공간을 제어한 효과로 해석할 수 있다.

## 대표 사례 1: vector-only 실패를 prefilter가 복구

대표 query:

```text
vru:medium:0056
Find videos where the accident type is ego-car hits a crossing pedestrian on a curve road.
metadata_filter = {"road_type": "curve"}
```

| strategy | R@10 | Hit@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|
| B2 vector-only | 0.0000 | 0 | 0.0139 | 0.0000 |
| B4 prefilter-vector | 1.0000 | 1 | 1.0000 | 1.0000 |

B2의 top results는 accident type은 유사하지만 road type이 `arterials`, `intersection` 등으로 섞인다. B4는 `road_type=curve` 후보 내부에서만 vector ranking을 수행하므로 top-5가 모두 relevant clip으로 바뀐다.

논문 해석:

> Dense retrieval은 사고 유형의 의미적 근접성은 포착하지만, 구조화 조건인 도로 유형을 top-k 순위 안에서 안정적으로 만족시키지 못한다. Metadata prefilter는 semantic ranking 전에 후보 공간을 질의 조건에 맞게 제한하여, 높은 선택도를 갖는 조건 질의에서 evidence recall을 크게 개선한다.

## 대표 사례 2: postfilter보다 prefilter가 유리

대표 query:

```text
vru:medium:0149
Find videos recorded in rainy night where the accident type is car hits pedestrian.
metadata_filter = {"weather_light": "rainy night"}
```

| strategy | R@10 | Hit@10 | MRR | nDCG@10 |
|---|---:|---:|---:|---:|
| B2 vector-only | 0.0000 | 0 | 0.0000 | 0.0000 |
| B3 postfilter | 0.0000 | 0 | 0.0000 | 0.0000 |
| B4 prefilter-vector | 1.0000 | 1 | 1.0000 | 1.0000 |

B3는 먼저 vector top-N을 뽑은 뒤 metadata 조건을 적용하므로, rainy night 관련 clip이 초기 vector 후보에 충분히 들어오지 않으면 실패한다. B4는 rainy night 후보 집합 안에서 ranking을 새로 수행하므로 relevant clip을 복구한다.

논문 해석:

> Post-filtering은 구현이 쉽지만, vector retrieval의 초기 후보 집합에 정답이 포함되어야만 동작한다. 반대로 pre-filtering은 metadata 조건을 query operator의 일부로 먼저 적용하므로, 조건 선택도가 높을수록 정답 후보를 보존한 상태에서 semantic ranking을 수행할 수 있다.

## 대표 사례 3: BM25와 hybrid의 필요성

대표 query:

```text
vru:weak:0029
Find accidents caused by: vehicles do not notice the pedestrians when turning or changling lanes.
```

이 query에서는 B2/B4가 top-10 hit에 실패하지만 B5 hybrid가 hit를 복구한다. 원인은 사고 원인처럼 긴 문장형 facet에서는 caption/document의 lexical phrase overlap이 dense vector보다 더 강하게 작동하는 경우가 있기 때문이다.

논문 해석:

> Hybrid retrieval은 전체 평균에서는 B4보다 항상 우수하지 않지만, 긴 문장형 원인 설명이나 특정 표현이 반복되는 query에서는 BM25가 dense retrieval을 보완한다. 따라서 본 연구의 결론은 vector-only 우위가 아니라, metadata-aware filtering과 sparse/dense 결합을 질의 유형에 따라 선택해야 한다는 것이다.

## hard case 해석

B4도 top-10 hit에 실패한 query는 5개뿐이지만, 이 사례는 논문 한계 분석에 중요하다.

대표 query:

```text
vru:medium:0081
Find videos where the accident type is ego-car hits pedestrian on a arterials road.
```

이 query의 qrels는 `accident_type = ego-car hits pedestrian`를 기준으로 생성되었다. 그러나 top-ranked clip들에는 `ego-car hits a pedestrian`처럼 관사 차이가 있는 거의 동일한 사고 유형 라벨이 존재한다. 또 다른 hard case인 `vru:weak:0027`에서는 `accident_reason`의 마침표 유무와 source split 차이로 semantically equivalent한 clip이 false positive처럼 평가된다.

따라서 남은 hard case의 일부는 검색 구조 자체의 실패라기보다 문장형/구문형 facet의 canonicalization 한계다.

논문 한계 문장:

> 일부 실패 사례는 vector retrieval 또는 metadata filtering의 구조적 한계라기보다, 원천 VQA annotation에서 동일한 의미를 갖는 facet 값이 관사, 구두점, 표현 변형에 따라 별도 값으로 분리되는 데서 발생하였다. 본 연구에서는 평가 누수를 피하기 위해 원천 라벨 기반 qrels를 보수적으로 사용했으며, 향후에는 facet normalization 또는 ontology mapping을 통해 의미적으로 동등한 라벨을 통합할 필요가 있다.

## pgvector backend 검증

pgvector P4와 FAISS B4는 query-level quality metric이 완전히 일치했다.

| comparison | metric | mean abs diff | max abs diff |
|---|---|---:|---:|
| P4 pgvector prefilter vs B4 FAISS prefilter | Recall@10 | 0.0000 | 0.0000 |
| P4 pgvector prefilter vs B4 FAISS prefilter | Recall@20 | 0.0000 | 0.0000 |
| P4 pgvector prefilter vs B4 FAISS prefilter | MRR | 0.0000 | 0.0000 |
| P4 pgvector prefilter vs B4 FAISS prefilter | nDCG@10 | 0.0000 | 0.0000 |

이는 본 논문의 DB backend 주장을 강화한다. 즉, Python/FAISS prototype에서 확인한 metadata prefilter 효과가 PostgreSQL+pgvector 내부 SQL filter와 vector ordering으로도 동일하게 재현된다.

P2 vector-only는 FAISS B2와 일부 query에서 top-k 차이가 있다. 이는 dense score tie 또는 backend별 tie ordering 차이로 해석하는 것이 안전하다. 논문에서는 P2보다 P4의 일치성을 핵심으로 제시한다.

## 논문 반영 위치

이 분석은 원고에서 다음 위치에 들어가야 한다.

1. 실험 결과 섹션: 난도별 B2/B4 성능 차이 표
2. 오류 분석 섹션: 대표 query 2~3개와 top-k evidence 비교
3. DB backend 섹션: pgvector P4와 FAISS B4의 quality metric 일치
4. 한계 섹션: 문장형 facet canonicalization, strict qrels, source별 annotation variation

## 최종 판단

이 분석으로 본 연구의 핵심 주장은 더 명확해졌다.

> 본 연구의 기여는 단순히 embedding model을 바꿔 성능을 높인 것이 아니라, 메타데이터 조건이 포함된 도시 감시형 멀티모달 검색에서 filter를 vector ranking 전후 어느 위치에 결합하는지가 evidence retrieval 품질을 결정한다는 점을 query-level 사례로 보인 것이다.

따라서 다음 작업은 추가 모델 구축이 아니라, 이 분석 결과를 원고의 실험 결과와 오류 분석 문단으로 전환하는 것이다.
