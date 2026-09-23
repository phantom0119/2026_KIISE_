# EXP03 — 실측 predicate filtered-ANN, 물리 색인과 배포

- 대응 질문: RQ5
- 상태: 완료
- 주 코퍼스: 시내도로 132,521×512, 522 visual 143,830×512
- 외부 DB 교차검증: MIRIS 59,019×512
- 결과 지위: real-vs-random 짝 비교는 확증, 색인·배포는 실측 설계 지침

## 1. 목적

동일 선택도의 무작위 mask가 실제 시간·위치·센서 predicate를 대표하는지 검증하고, 실측 predicate 아래에서 ANN 계획·엔진·색인·partial index의 품질–지연–공간–구축비 절충을 측정한다.

## 2. 데이터와 정답

| 코퍼스 | 벡터 | query | predicate |
|---|---:|---:|---|
| A 시내도로 | 132,521×512 CLIP ViT-B/32 | holdout 1,000 | 장소·일자·시각, natural 29쌍 |
| B 522 visual | 143,830×512 CLIP ViT-B/32 | 등록 query | 조인 센서 facet, natural 25쌍 |
| MIRIS | PostgreSQL 59,019×512 CLIP | DB query | scene + 상대 stream segment |

관련도 qrels 대신 각 predicate 부분집합에서 exact Flat top-10을 정답 이웃으로 사용한다. 그러므로 이 실험은 **ANN fidelity**를 평가하며 semantic task quality를 직접 평가하지 않는다.

## 3. 실험 A — real predicate 대 same-selectivity random mask

### 3.1 처리군

- subset Flat: predicate 부분집합 exact
- subset HNSW: predicate 부분집합 별도 ANN
- global HNSW postfilter: 전역 ANN 상위 \(K'=4k\) 후 필터
- IVF selector: 전역 IVF 탐색 내부에서 predicate selector 적용, nprobe 8/32

각 natural predicate의 통과 수와 같은 random mask를 만든다. 모든 natural predicate에 대조군이 존재해야 한다.

### 3.2 estimand

\[
\Delta_{\text{mask}} =
\text{Recall@10}_{random}
-
\text{Recall@10}_{real}
\]

positive는 random mask가 실제 성능을 과대평가한다는 뜻이다.

### 3.3 결과

| 방법 | 코퍼스 A Δ [95% CI] | 코퍼스 B Δ [95% CI] |
|---|---:|---:|
| postfilter \(K'=4k\) | +0.611 [0.554,0.661] | +0.289 [0.219,0.359] |
| IVF selector np8 | +0.627 [0.550,0.699] | +0.217 [0.144,0.294] |
| IVF selector np32 | +0.498 [0.407,0.585] | +0.116 [0.072,0.159] |
| subset HNSW | +0.017 [0.012,0.023] | +0.004 [0.002,0.006] |
| subset Flat | 0, 정의상 | 0, 정의상 |

표의 검정 가능한 차이는 Holm 보정 후 유의하다. \(K'=4k\)에서도 real postfilter recall은 A 0.306, B 0.667인 반면 random은 0.917/0.956이다.

결손은 exact 이웃의 전역 중앙 순위와 양의 상관을 보인다.

- A: \(\rho=0.699/0.780\)
- B: \(\rho=0.616/0.895\)

선택도뿐 아니라 predicate가 표현 공간에서 만든 군집과 전역 순위 깊이가 기전이다.

## 4. 실험 B — 관계형·전용 엔진

### 4.1 pgvector

PostgreSQL 16.14와 pgvector 0.8.4 HNSW에서 다음을 비교한다.

- iterative scan off + `WHERE`
- `relaxed_order`
- predicate별 partial index

대표 global 결과:

| predicate (selectivity) | off recall | relaxed recall | relaxed p50 |
|---|---:|---:|---:|
| 장소=BC2000801 (0.086) | 0.121 | 0.658 | 19.0ms |
| 장소=중동사거리 (0.049) | 0.034 | 0.302 | 29.5ms |
| hour=06 (0.183) | 0.310 | 0.984 | 1.0ms |
| hour∈[06,18] (0.774) | 0.876 | 0.994 | 0.44ms |

relaxed scan은 약결합 시간 조건을 회복하지만 군집형 위치 predicate에서는 recall 부족과 지연 비용이 남는다.

### 4.2 Milvus·Weaviate

엔진의 fallback/완화 체제를 분리해 분석한다.

| 엔진 경로 | 코퍼스 | n | random−real recall Δ [95% CI] | 지위 |
|---|---|---:|---:|---|
| Weaviate sweeping | A | 24 | +0.0098 [0.0049,0.0159] | 확증 |
| Milvus graph regime | B | 18 | +0.0028 [0.0009,0.0049] | 확증 |
| Milvus graph regime | A | 6 | +0.0140 [0.0079,0.0220] | 방향 일치 |
| Weaviate sweeping | B | 22 | +0.0006 [0.0000,0.0015] | 효과 극소 |
| Milvus brute-force fallback | A/B | 18/4 | ≤+0.0014 | 완화 체제 |
| Weaviate ACORN | B | 22 | -0.0181 [-0.046,+0.003] | 부호 역전 경향 |

random mask는 naive 공유 계획을 낙관할 수 있고, real-cluster를 활용하는 ACORN류 완화는 반대로 비관할 수 있다.

## 5. 실험 C — 비필터 색인 3축

### 5.1 비교군

- Flat
- HNSW M16/M32, fixed construction and search settings
- IVF-Flat
- IVF-PQ m32/m64

### 5.2 지표

- Recall@10
- p50/p95 latency
- build seconds
- serialized MB
- Pareto domination

### 5.3 대표 결과

| 코퍼스 | 구성 | recall@10 | p50 | p95 | build | size |
|---|---|---:|---:|---:|---:|---:|
| A 131K | Flat | 1.000 | 13.43ms | 14.37ms | 0.11s | 268MB |
| A 131K | HNSW M16 | 0.997 | 0.041ms | 0.055ms | 34.8s | 287MB |
| A 131K | IVF-PQ m64 | 0.481 | 0.135ms | 0.158ms | 26.1s | 12MB |
| B 142K | Flat | 1.000 | 14.18ms | 15.34ms | 0.12s | 290.8MB |
| B 142K | HNSW M16 | 0.9994 | 0.044ms | 0.061ms | 44.3s | 311.3MB |
| B 142K | IVF-PQ m64 | 0.4938 | 0.134ms | 0.172ms | 27.9s | 12.9MB |

HNSW는 약 7–13%의 추가 공간과 35–47초 구축으로 Flat 대비 약 300배 낮은 탐색 지연을 얻는다. IVF-PQ는 22–35배 압축하지만 recall 0.33–0.49로 낮아진다.

## 6. 실험 D — partial/local index와 hot/cold 정책

### 6.1 partial index

시내도로 pgvector에서 `CREATE INDEX ... WHERE predicate`를 실제 구축한다.

| selectivity | global relaxed recall/p50 | partial recall/p50 | partial build/size |
|---:|---:|---:|---:|
| 0.011 | 0.167 / 31.8ms | 0.986 / 0.41ms | 0.4s / 3.8MB |
| 0.047 | 0.895 / 6.89ms | 0.988 / 0.45ms | 1.9s / 15.7MB |
| 0.183 | 0.986 / 1.09ms | 0.990 / 0.41ms | 7.1s / 61MB |
| 0.260 | 0.986 / 0.91ms | 0.981 / 0.42ms | 10.7s / 87MB |
| 0.473 | 0.993 / 0.43ms | 0.983 / 0.42ms | 21s / 158MB |
| 0.774 | 0.997 / 0.45ms | 0.995 / 0.42ms | 39s / 258MB |

### 6.2 손익분기

\[
N^*(p)=\frac{1000\cdot T_{\text{build},s}(p)}
{L_{\text{global},ms}(p)-L_{\text{partial},ms}(p)}
\]

정책:

\[
\text{build local}(p)
\iff
\text{global recall}(p)<0.95
\;\lor\;
\text{expected queries}(p)>N^*(p)
\]

- \(s\lesssim0.05\): 품질 강제 local
- \(s\approx0.18\)–0.26: 약 1–2만 질의 이상인 hot predicate만 local
- \(s\gtrsim0.47\): global+postfilter

### 6.3 MIRIS 교차검증

MIRIS에서도 partial recall 0.998–1.000, p50 0.34–0.49ms가 유지됐다. \(N^*\)는 선택도 0.042에서 81질의, 0.167에서 9,495, 0.292에서 30,330, 0.542에서 119K, 0.667에서 1.4M으로 증가했다.

MIRIS 최저 선택도에서는 global recall 붕괴 대신 scan fallback의 23배 지연이 병목이었다. “선택적/hot predicate에 local”이라는 정책은 재현됐지만, 우위의 원인은 데이터·planner에 따라 recall 또는 latency로 바뀐다.

## 7. Qwen 대규모 5-seed 강건성

143,830 real Qwen 2,048차원 벡터에서 seed마다 index를 다시 구축했다.

| 구성 | mean recall@10 | min | median p95 | 5/5 ≥0.99 |
|---|---:|---:|---:|---:|
| HNSW ef256 | 0.989412 | 0.987059 | 3.179ms | 아니오 |
| HNSW ef512 | 0.998118 | 0.996471 | 5.757ms | 예 |
| HNSW ef1024 | 1.000000 | 1.000000 | 10.148ms | 예 |
| IVF-Flat np128 | 0.993176 | 0.989412 | 21.155ms | 아니오 |
| IVF-Flat np256 | 0.999529 | 0.998824 | 37.587ms | 예 |
| IVF-Flat np512 | 1.000000 | 1.000000 | 68.580ms | 예 |

관측 범위의 균형점은 HNSW ef512지만 모든 데이터·seed에 대한 수학적 보장은 아니다.

## 8. 결과 지위와 허용 주장

### 허용

- same-selectivity random mask는 실제 군집형 predicate의 공유 ANN recall을 크게 과대평가할 수 있다.
- subset/local index는 이 결손을 구조적으로 완화한다.
- partial index의 우위는 선택도와 질의 빈도에 따른 품질·상각 규칙으로 표현할 수 있다.
- HNSW, Flat, PQ의 선택은 recall·latency·space SLA에 의존한다.

### 금지

- exact-neighbor recall을 semantic task relevance로 부르지 않는다.
- HNSW ef512를 보편적 최적값이라고 부르지 않는다.
- in-process FAISS와 PostgreSQL 왕복 latency를 직접 순위화하지 않는다.
- random mask가 언제나 무효라고 일반화하지 않는다. 실제 predicate와의 차이를 먼저 측정한다.
- MIRIS의 `tseg`를 실제 시계 시간 ground truth라고 부르지 않는다.

## 9. 원자산

- filtered-ANN: `2026_KIISE/paper_assets/20260710_pillarB/`
- 색인 benchmark A: `Datasets/processed/sinnaedoro_traffic/index_benchmark/`
- 색인 benchmark B: `2026_KIISE/paper_assets/20260710_pillarB/index_grid_522visual/index_benchmark.csv`
- DB design: `2026_KIISE/paper_assets/20260713_db_design/`
- 5-seed: `2026_KIISE/paper_assets/20260717_ablation_agent_crosscheck/`의 high-recall 자산
- 결과 정리: `2026_KIISE/project_md/620_RESULTS_filtered_ann_real_predicates_20260710.md` [정정 2026-07-28: 레거시 흡수 완료, 아카이브 경로 `project_md/archive/legacy_premerge_20260728/620_RESULTS_filtered_ann_real_predicates_20260710.md`]
- partial/hot-cold: `2026_KIISE/project_md/720_RESULTS_db_design_storage_index_20260713.md` [정정 2026-07-28: 레거시 흡수 완료, 아카이브 경로 `project_md/archive/legacy_premerge_20260728/720_RESULTS_db_design_storage_index_20260713.md`]

## 10. 변경 시 재실행 조건

- predicate registry·selectivity band 변경
- random mask 생성 또는 seed 정책 변경
- exact neighbor 정의·k·oversampling 변경
- index build/search 파라미터 변경
- 엔진 버전·fallback threshold 변경
- DB table, planner option, concurrency 또는 client/server 계측 경계 변경
- hot/cold recall threshold 또는 비용식 변경

## 레거시 결과 문서 흡수 (2026-07-28)

SYNC 기준: paper_final.pdf(2026-07-23 제출본). 아래 소스 3종의 고유 정보는 본 섹션에 보존하고, 원본은 아카이브로 이관한다. RQ2·RQ5 수치 인용은 항상 paper_final이 우선한다.

### S1. 600_RESULTS_index_structure_benchmark_20260709.md

**(a) 요약** — 시내도로 real 132,521×512(+분포보존 synthetic 1M) FAISS 색인 구조 벤치마크 52 config와 controlled random-mask selectivity(1–100%) 필터 전략 비교. 본 문서 §5(실험 C)의 최초 원천.

**(b) EXP 본문에 없는 고유 정보**
- 코퍼스 구축 세부: AI Hub 시내도로 교통 CCTV JPG 프레임을 131개 zip에서 층화(위치·카메라·시간) 스트리밍, 16,107 카메라/39 위치. 목표 30만이었으나 원천 zip cap으로 132,521. synthetic 1M = real 재표본+jitter(무작위 Gaussian 아님, real 최근접 유사도 0.961), real(≤131K)/synthetic(>131K) 라벨 분리.
- 스케일 sweep N∈{1만,5만,10만,13.1만,30만,50만,100만} 지연 crossover: Flat p50 0.90ms(1만)→98.5ms(100만) 선형, HNSW(recall≥0.99) 0.018–0.061ms 상수. 배속 50×(1만)→327×(13.1만)→~1,600×(100만). ANN 이점은 이미 1만 벡터에서 50×.
- HNSW 비용 스케일링: build 2s→743s, 메모리 23MB→2,320MB(N 증가).
- IVF-Flat 튜닝 범위(131K): nprobe1 r0.89/0.05ms ↔ nprobe32 r0.999/1.8ms.
- controlled selectivity 3전략 표: post-filter(full HNSW) s=1%에서 r0.742(그 외 ≥0.997), pre-filter+HNSW 전 구간 ~0.03–0.04ms/r0.998+, pre-filter+Flat 0.07→13.64ms 선형.
- 측정 프로토콜: 검색은 single-thread `index.search`만 계측(warmup 폐기, 15반복×1,000질의, p50/p95/p99), build는 8스레드, FAISS CPU-only(GPU 미측정).
- 자산·스크립트: `Datasets/processed/sinnaedoro_traffic/{corpus_real, corpus_aug_1m.npy, index_benchmark/, filtered_ann/filtered_ann.csv}`, 그림 `paper_assets/20260707_submission_figures/fig_index_structure_pareto.png`·`fig_selectivity_filter.png`, 스크립트 `build_sinnaedoro_visual.py`·`run_index_structure_benchmark.py`·`run_filtered_ann_benchmark.py`.

**(c) 상충과 정정**
- 600의 "전략 선택 규칙"(선택도 넓으면 post-filter 회복, ≥10%에서 recall 회복)은 random-mask 방법론에 기반한 것으로, 실측 predicate 결과(본 문서 §3, 620)와 상충한다. 실제 군집형 predicate에서는 postfilter recall이 K'=4k에서도 A 0.306에 그치고 random mask는 최대 +0.63 과대평가한다. 620의 결정대로 600 결과는 "무상관 predicate 상한"으로만 인용한다(폐기 아님). paper_final RQ5도 무작위 대조는 최대 0.047 변동으로 실측 손실(최대 0.627)을 과소평가한다고 명시한다.
- 600은 s=1%를 "고선택도"로 표기하나 이후 문서(620·720·paper_final)는 s=통과 비율(작을수록 선택적)로 통일했다. 인용 시 용어 혼동 주의.
- synthetic(>131K) 구간 수치는 real 관측이 아니므로 인용 시 항상 라벨 병기.

**(d) 아카이브 경로** — `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/600_RESULTS_index_structure_benchmark_20260709.md`

### S2. 620_RESULTS_filtered_ann_real_predicates_20260710.md

**(a) 요약** — 실측 predicate filtered-ANN 2-코퍼스 확증(M9 동일-s 대조군, Holm)·색인 그리드 2차 real 코퍼스(B-2)·pgvector 교차재현(B-3)·제3 엔진 Milvus/Weaviate(B-4)·retrieval Pareto(E-2). 본 문서 §3–5의 원천 정본.

**(b) EXP 본문에 없는 고유 정보**
- 사전등록 계보: `420_METHOD_prereg_pillarBE_design_20260710.md` §1+Amendments(M1 타이밍경계·M2 통계·M4 공정성·M5 NULL·M9 대조군, P1 LOCK). M9 대조군은 사전등록 설계이며 사후 선택 아님.
- 코퍼스 B 질의 세부: 이미지 질의 200(확증층), 미조인 9.8%=NULL 불통과.
- 확증 가족 s-밴드×방법쌍 ΔRecall@10: A low(<0.05, n=13) prefilter−postfilter +0.767 [0.716,0.820]/prefilter−single_stage(np32) +0.607, A mid(n=11) +0.667/+0.450, B mid(n=10) +0.419/+0.181, B high(n=12) +0.217/+0.035 (모두 유의). A high(n=5)·B low(n=3)는 방향 동일하나 검정력 부족으로 확증 미달.
- 운영 3축 실측치(실제 predicate 평균): prefilter_flat 1.000/1.45ms(A)·1.000/3.21ms(B), prefilter_hnsw ef64 0.983/0.038ms·0.997/0.040ms, postfilter K4x 0.306/0.102ms·0.667/0.082ms, single_stage bitmap np32 0.750/0.153ms·0.960/0.187ms, batch np128 0.735/0.180ms·0.979/0.267ms.
- 수치 재집계 감사 17/17 PASS(원시 CSV 재집계, F5 검증기 원칙).
- prefilter 빌드 상각 손익분기: A build 중앙값 0.9s→~1,869질의(IQR 1,789–1,990), B 4.3s→~2,442질의(IQR 2,138–2,773). "predicate당 예상 질의 ≥~2K면 부분집합 색인 이득" 정량 임계값.
- K'-민감도: postfilter K'×1→×4에서 실제 predicate recall +0.065(A 0.242→0.306)/+0.147(B 0.520→0.667)에 그침(대조군은 0.86→0.92/0.96) — 결손은 예산이 아니라 구조적임을 K' sweep 자체가 증명.
- single-stage 에스컬레이션 발동률: recall<0.9@np32→np128 승급 필요 A 25/29·B 13/25 predicates(비용 p50 0.18–0.27ms).
- B-2 세부: 38 config, 스케일 10K/50K/100K/142K(synthetic 불필요), HNSW ef64 0.9992@0.047ms, build HNSW 47s/IVF 15–28s.
- B-3 pgvector 비필터: HNSW m16 ef16 0.987@0.26ms(클라이언트 왕복, exact seq-scan 218ms)~ef256 0.996@0.78ms, IVFFlat probes8 0.996@0.9–1.9ms, build 49–88s(비병렬), index 333–350MB. 재현 각주: 도커 /dev/shm 64MB↔병렬 DSM 충돌로 `max_parallel_maintenance_workers=0` 필요.
- B-3 필터드 표의 IVF1024 relaxed 열(0.556/0.481/0.806/0.974)과 frac_short(location off 88–97%, relaxed 51%) — 본 문서 §4.1 표에는 없는 열.
- E-2 retrieval Pareto: front 12/46, 두 코퍼스 구조 동일 — HNSW(M16 ef16→256)가 0.03–0.31ms 영역 지배(recall 0.985–0.9998), IVF-Flat 고probe 1–2ms 중간점, Flat=recall 1.0 앵커 @14.4/15.3ms.
- B-4 세부: Amendment 5/5a(적대 검토 wf_1ad02af8-bf5 확정 8건), Milvus BF 폴백 경계 (0.923,0.934] 실측 분리, Weaviate flat cutoff 40K. 확증 4/4 방향 일치·2/4 Holm 유의(w2×A p=7e-5, m1×B p=.022), 효과 크기는 faiss naive(+0.61)의 1/40 이하. 기전 잔존 m1-graph×B Δ↔군집심도 ρ=0.676(p=.002). F7 시드 견고성: 대조군 7드로우 SD 0.001–0.010(최대 범위 0.047)≪M9 효과. 게이트 G-ingest 0.996/0.997·G-filter 108/108·qidx sha256 고정. 정본 `paper_assets/20260712_engine_replication/B4_RESULTS.md`.

**(c) 상충과 정정**
- 본 문서 §3–5와 실질 상충 없음(§3–5는 620의 압축). 세부 표기 차이: 본 문서 §3.3 prefilter_hnsw B Δ +0.004는 620의 +0.0035 반올림, §2의 B "등록 query"는 620 기준 "이미지 질의 200(확증층)"이 정확한 서술.
- paper_final과의 연결(출처 확인): 논문 RQ5의 "무작위 대조는 최대 0.047 변동"은 B-4 F7 시드 견고성의 최대 범위 0.047이 출처. 논문의 "Milvus/Weaviate 필터율≥92.3% 또는 조건 만족 벡터<40,000이면 전수 검색 자동 전환"은 B-4의 Milvus BF 폴백 경계 (0.923,0.934] 실측과 Weaviate flat cutoff 40K가 출처.
- 620의 "600(구39) random-mask 결과는 무상관 predicate 상한으로 재해석·병치(폐기 아님)" 결정은 S1(c)의 정정 근거로 승계.

**(d) 아카이브 경로** — `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/620_RESULTS_filtered_ann_real_predicates_20260710.md`

### S3. 720_RESULTS_db_design_storage_index_20260713.md

**(a) 요약** — 저장단위 비교(P1)·pgvector partial/local index(P2)·hot/cold 손익분기 정책(P3)과 MIRIS 독립 교차검증. 본 문서 §6의 원천 정본(단 P1 저장단위는 본 문서 범위 밖이며 RQ2 계열에 속함).

**(b) EXP 본문에 없는 고유 정보**
- P2 global `iterative_scan=off` 열: s=0.011에서 recall 0.010/0.37ms(frac_short 98%), 0.047에서 0.175/0.42ms, 0.183에서 0.313/0.38ms 등 — "빠르지만 틀림(off) vs 맞지만 느림(relaxed)" 딜레마의 off쪽 실측. global HNSW(m16,efC200) build 50.4s/333.5MB(1개 상각).
- P3 sinnaedoro N* 실측치: s=0.011→12, 0.047→291, 0.183→10,594, 0.260→21,509, 0.473→2.1M, 0.774→1.2M — 본 문서 §6.2는 밴드 규칙만 있고 N* 수치가 없음. s≲0.05 두 predicate는 품질강제 LOCAL(N* 무관).
- MIRIS 구성 세부: SIGMOD 2020 교통교차로, Warsaw+Shibuya 12영상(uav 드론·beach 비교통 제외), MIT 주석, 59,019 프레임 CLIP ViT-B/32-512(sinnaedoro와 동일 인코더), global HNSW build 26s/154MB, 영상 저작권상 임베딩 비재배포·수치만 보고.
- MIRIS 선택도별 표: hour=6(0.042) global off 1.000/7.75ms·partial 1.000/0.34ms(0.6s/6.4MB)부터 hour 6-21(0.667) partial 0.999/0.49ms(15.8s/102MB)까지. 품질강제 predicate=공집합(테스트 범위 내 global recall 항상 ≥0.99) — 본 문서 §6.3 서술("recall 붕괴 대신 지연 병목")의 수치 근거.
- P1 저장단위(본 문서 범위 밖, 보존 기록): 522 tri-source 85질의·3,000클립/8,349프레임에서 clip-caption(bge-m3 1024d) 12.3MB/0.59ms·semantic nDCG@10 0.1692로 Pareto-최적, MEVA 985클립에서는 frame-vector(CLIP-512)가 정확도(0.1610 vs 0.1029)·저장(2.02 vs 4.03MB) 양쪽 지배로 반전 — "최적 저장단위는 캡션-질의 정합에 의존" 발견. caveat: 저장단위 선택이 인코더 선택을 내포(인코더 격리 ablation 아님).
- 스크립트·자산: `run_storage_unit_benchmark.py`·`run_pgvector_partial_index.py`·`score_hotcold_policy.py`·`build_miris_pgvector.py`, `results/storage_unit/{storage_unit_summary,_metrics,_latency}.csv`, `paper_assets/20260713_db_design/{pgvector_partial_vs_global,hotcold_policy}.csv`·`hotcold_summary.json`·`p2.log`, MIRIS `pgvector_partial_vs_global_miris.csv`·`hotcold_miris_policy.csv`·`p2p3_miris.log`, MEVA CLIP `embeddings/clip-vit-b32/`.

**(c) 상충과 정정**
- **P1 저장단위 판정은 paper_final 표4(RQ2)와 상충 — paper_final이 정본.** 720은 multi-vector 무이득(semantic 0.1681≈caption 0.1692)·dual-index 희석(0.1644)으로 결론했으나, 제출 논문 표4는 다중 이미지(클립당 최대 3) 0.352(Δ+0.171 유의)·이중 색인(RRF k=60) 0.293으로 설명문 0.181 대비 우위를 보고한다. 720 P1은 8,349 전 프레임 exhaustive max-sim 설계·상이한 qrels의 초기 런으로 논문의 다중 이미지/이중 색인 설계와 저장단위 정의 자체가 다르다. 저장·지연 수치도 구식(720 caption 12.3MB/0.59ms vs 논문 표4 24.6MB/1.15ms). RQ2 인용은 반드시 paper_final 표4 기준.
- 같은 이유로 720 말미의 "강화된 기여 문장" (i)항(clip-caption Pareto-최적·multi-vector/dual 무이득)은 제출 논문과 불일치하므로 사용 금지. (ii)(iii)항(partial index·hot/cold 규칙)은 논문 RQ5 배포 규칙과 정합.
- P3 규칙(global recall<0.95 품질강제 또는 N* 상각)은 paper_final의 배포 규칙과 정합 — 상충 없음.
- 용어: 720의 "VLM-QA evidence layer" 표현은 2026-07-28 확정 용어 결정('증거' 전면 치환)에 따라 향후 문서에서 "검색 계층/검색 문맥"으로 표기한다.

**(d) 아카이브 경로** — `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/720_RESULTS_db_design_storage_index_20260713.md`
