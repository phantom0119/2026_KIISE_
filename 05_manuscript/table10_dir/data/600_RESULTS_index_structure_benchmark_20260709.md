# URBAN-INDEX: 저장·색인 구조의 정확도·지연·비용 벤치마크 (결과)

작성 기준일: 2026-07-09
연구질문: 도시 감시 멀티모달 데이터의 VLM-QA 검색에서 **어떤 벡터 색인 구조가 정확도·지연·비용을 가장 잘 균형화하는가.**
스크립트: `build_sinnaedoro_visual.py`(코퍼스), `run_index_structure_benchmark.py`(벤치마크).
산출물: `Datasets/processed/sinnaedoro_traffic/{corpus_real, corpus_aug_1m.npy, index_benchmark/}`, 그림 `paper_assets/20260707_submission_figures/fig_index_structure_pareto.png`.

## 코퍼스 (스케일 축)
- **real 132,521 벡터** — AI Hub 시내도로 교통 CCTV **JPG 프레임**을 131개 zip에서 층화(위치·카메라·시간 spread) 스트리밍 → **CLIP ViT-B/32 512-dim**. 16,107 카메라 / 39 위치. (목표 30만이었으나 원천 zip이 cap보다 작아 균형 샘플 132K; **10만 crossover 임계 초과로 충분**.)
- **분포 보존 synthetic 증강 → 1,000,000** — real 재표본+jitter(무작위 Gaussian 아님; real 최근접 유사도 0.961로 클러스터 구조 유지). 스케일 sweep에서 real(≤131K)과 synthetic(>131K)을 라벨 분리.

## 방법 (하자 없는 측정)
- **구조가 유일한 변수**: 동일 벡터·질의(held-out 1000)·하드웨어·top_k(10)·metric(cosine/IP). **FAISS Flat / IVF-Flat(nlist·nprobe) / HNSW(M·efSearch) / IVF-PQ(m)**.
- **정확도 = ANN-recall@10 vs exact Flat**(색인 충실도; task·답변 정확도와 분리).
- **지연 = 격리 측정**: `index.search`만 계측, **single-thread**(서빙 지연), warmup 폐기, 15반복 × 1000질의, **p50/p95/p99**.
- **빌드 = 전체 8스레드**(대표 build-time). **비용 벡터** = build 시간(s) + 직렬화 index 크기(MB).
- **스케일 sweep** N∈{1만,5만,10만,13.1만(real max),30만,50만,100만}; 13.1만에서 full 튜닝 grid. 52 config.

## 핵심 결과

**① 지연 crossover — Flat은 선형↑, ANN은 ~상수** (그림 좌):
| N | Flat p50 | HNSW(recall≥0.99) p50 | 배속 |
|---|---:|---:|---:|
| 1만 | 0.90ms | 0.018ms (r0.995) | 50× |
| 10만 | 10.2ms | 0.043ms (r0.997) | 237× |
| 13.1만 | 13.4ms | 0.041ms (r0.997) | 327× |
| 30만 | 30.9ms | 0.056ms (r0.997) | 551× |
| 100만 | 98.5ms | 0.061ms (r0.984, ef16) | ~1,600× |

→ Flat 지연은 N에 선형(선형 스캔), **HNSW는 N과 거의 무관하게 ~0.02–0.06ms 유지하며 recall 0.98–0.998**. ANN의 이점은 **1만에서도 50×**, 규모가 커질수록 확대.

**② IVF는 튜닝 가능**: nprobe로 recall↔지연 조절 (예 131K: nprobe1 r0.89/0.05ms ↔ nprobe32 r0.999/1.8ms).

**③ IVF-PQ = 메모리-비용 구조**: 131K에서 **index 8–12MB(vs Flat 268MB, ~33× 작음)** 이지만 **recall 0.33–0.48**로 급락 → 메모리 극한 제약 + 낮은 정확도 허용 시에만.

**④ 비용 trade-off (정확도·지연의 대가)**:
- **HNSW**: 질의 최속·고recall이나 **build 비쌈**(2s→743s, N↑) + **메모리 최대**(23MB→2320MB).
- **Flat**: build 사실상 0이나 **지연·메모리 모두 N에 선형**.
- **IVF-Flat**: 중간, nprobe로 조절, build 중간.
- **IVF-PQ**: 메모리 최소, build 중간, recall 최저.

## 연구질문에 대한 답
> 도시 감시 멀티모달 검색에서 색인 구조는 **정확도·지연·비용의 명확한 Pareto**를 이룬다. **HNSW가 정확도(0.99+)와 지연(규모 무관 ~상수)을 가장 잘 균형화**하며, 그 대가는 build-time과 메모리다. 메모리 제약이 극심하면 **IVF-PQ**(33× 절감, 낮은 recall), 튜닝 유연성이 필요하면 **IVF-Flat**(nprobe). **Flat(exact)은 소규모(<수만)에서만 실용적**이며 그 이상에선 지연이 선형 증가해 부적합하다. ANN이 이득을 주기 시작하는 지점은 이미 **1만 벡터(50×)**이고 규모와 함께 확대된다.

## 정직한 한계 (본문 명시)
- **real 132K + synthetic 확장**: 100만은 분포 보존 증강이며 real 최대는 132K(라벨 분리).
- **FAISS CPU-only**(get_num_gpus=0) — GPU 색인 지연은 미측정, 온-프레미스 CPU 서빙 회귀로 해석.
- **단일 modality**(시각 CLIP-512). 텍스트/융합 색인은 후속.
- **지연은 검색 레이어 내부 지표**: end-to-end VLM-QA에서는 VLM 추론이 색인 비용/지연을 크게 압도하므로, 본 결과는 **검색 계층의 구조 선택 trade-off**로 스코프하며 "index 선택이 end-to-end 비용을 좌우한다"고 과장하지 않는다.
- pgvector 등 SQL 백엔드는 in-process FAISS와 소켓/파서 오버헤드가 달라 직접 비교 시 별도 격리 필요(후속).

## 추가 실험: 메타데이터 selectivity × 필터 전략 (센서·시공간 축)

`run_filtered_ann_benchmark.py` — real 132K 코퍼스에 selectivity s(예: 특정 위치·시간대 predicate가 통과시키는 비율)를 controlled로 변화(1%~100%), 세 전략을 비교(GT = 부분집합 내 exact top-10). 산출물 `filtered_ann/filtered_ann.csv`, 그림 `fig_selectivity_filter.png`.

| selectivity | pre-filter+Flat | pre-filter+HNSW | post-filter(full HNSW) |
|---|---|---|---|
| 1% (n=1,325) | r1.00 / 0.07ms | r1.00 / **0.03ms** | **r0.742** / 0.37ms |
| 5% | r1.00 / 0.49ms | r1.00 / 0.03ms | r0.997 / 0.24ms |
| 10% | r1.00 / 1.28ms | r1.00 / 0.04ms | r1.00 / 0.17ms |
| 25% | r1.00 / 3.38ms | r0.999 / 0.04ms | r1.00 / 0.15ms |
| 50% | r1.00 / 6.83ms | r0.999 / 0.04ms | r0.999 / 0.14ms |
| 100% | r1.00 / **13.64ms** | r0.998 / 0.04ms | r0.999 / 0.14ms |

**핵심 발견:**
1. **post-filter는 고선택도에서 recall이 붕괴**(1%에서 0.742) — 사전구축 full ANN을 over-fetch해도 통과 후보가 부족. 저선택도(≥10%)에선 회복.
2. **pre-filter+Flat 지연은 부분집합 크기에 선형↑**(0.07→13.6ms) — 필터가 넓을수록 exact가 비싸짐.
3. **pre-filter+HNSW는 전 구간 상수·저지연(~0.04ms)+정확(0.998+)**이나, **predicate별 index 빌드 비용**이 필요.

**전략 선택 규칙(답):** 필터가 **매우 선택적(소수 통과)**이면 **pre-filter**(부분집합 exact/HNSW)가 우월 — post-filter는 recall 붕괴로 부적합. 필터가 **넓으면** 사전구축된 **full ANN + post-filter**가 per-query 빌드 없이 상수 지연으로 우월. 즉 **최적 색인·필터 구조는 metadata selectivity에 의존**하며, 이는 DBR 논문의 metadata-prefilter 우위 주장을 **지연·정확도 차원에서 정량화**한다(센서·시공간 메타데이터 modality의 기여).

한계: selectivity는 controlled random-mask predicate(실 metadata 분포와 다를 수 있음); pre-filter+HNSW의 predicate별 빌드 비용은 사전 인덱싱 가능한 저카디널리티 facet에서만 상수-지연 이점 유효.
