# 620_RESULTS — 실 predicate filtered-ANN 2-코퍼스 결과 (Pillar B-1)

실행: 2026-07-10 | 사전등록: `420_METHOD_prereg_pillarBE_design_20260710.md` §1 + Amendments (M1 타이밍경계·M2 통계·M4 공정성·M5 NULL·M9 대조군, P1 LOCK)
Asset: `paper_assets/20260710_pillarB/{filtered_ann_real_{A,B}.csv, B1_analysis_{A,B}.md, B1_confirmatory_*.csv, B1_m9_control_*.csv, P1_*, *_manifest.json}`
러너: `scripts/run_filtered_ann_real_predicate.py` / 분석: `scripts/analyze_filtered_ann_results.py`

## 설계 요약

- 코퍼스 **A** = sinnaedoro 132,521×512 (시공간 predicate: location/date/hour; 질의=텍스트 1,000)
- 코퍼스 **B** = 522-visual 143,830×512 (센서 predicate: time_of_day/signal/density/hour; 질의=이미지 200 확증층; 미조인 9.8%=NULL 불통과)
- 방법: prefilter_flat / prefilter_hnsw(ef64) / postfilter_hnsw(K'∈{1,2,4}×⌈k/s⌉) / single_stage IVF(IDSelectorBatch np8/32, 에스컬레이션 np128, s≥0.25에 Bitmap)
- **모든 실제 predicate에 동일-s 랜덤 대조군 짝지음(M9)**; GT=subset 내 exact top-10(self 제외); recall CI=질의 부트스트랩; latency=단일스레드, 질의별 R15 중앙값 분포의 p50/p95+질의 부트스트랩 CI(워밍업 5 제외); 방법 순서 무작위화.

## 헤드라인: 실제 상관 predicate는 공유색인 filtered-ANN을 붕괴시킨다 (2-코퍼스 복제)

### M9 — 동일-s 랜덤 대조군 대비 recall 과대평가량 (Holm 보정, 전부 유의)

| 방법 | A (n=29쌍) | B (n=25쌍) |
|---|---:|---:|
| postfilter_hnsw_K4x | **+0.611** [0.554, 0.661] | **+0.289** [0.219, 0.359] |
| single_stage_ivf np8 | **+0.627** [0.550, 0.699] | +0.217 [0.144, 0.294] |
| single_stage_ivf np32 | **+0.498** [0.407, 0.585] | +0.116 [0.072, 0.159] |
| prefilter_hnsw ef64 | +0.017 [0.012, 0.023] | +0.0035 [0.002, 0.006] |
| prefilter_flat | Δ≡0 (검정 불능) | Δ≡0 |

→ **기존 문헌(및 우리 구 벤치마크 600/구39)의 random-mask 방법론은 postfilter·공유색인 selector 방식의 filtered-ANN recall을 실사용 조건에서 크게 과대평가한다** (A에서 최대 ~0.63 절대치). prefilter(부분집합-지역 색인) 계열만 방법론 편향에 면역.

### 확증 가족 — s-밴드 × 방법쌍 ΔRecall@10 (사전등록 쌍, Holm)

| 밴드 | prefilter−postfilter | prefilter−single_stage(np32) | 판정 |
|---|---:|---:|---|
| A low(<0.05) n=13 | +0.767 [0.716,0.820] | +0.607 [0.521,0.695] | ✓ |
| A mid n=11 | +0.667 [0.586,0.738] | +0.450 [0.312,0.579] | ✓ |
| A high n=5 | +0.462 | +0.228 | 방향 동일, 비유의(n=5) |
| B low n=3 | +0.485 | +0.204 | 방향 동일, 비유의(n=3) |
| B mid n=10 | +0.419 [0.340,0.506] | +0.181 [0.121,0.238] | ✓ |
| B high n=12 | +0.217 [0.123,0.325] | +0.035 [0.005,0.083] | ✓ |

### 메커니즘 — 결손은 predicate의 임베딩 군집도를 따른다

recall 결손(대조군−실제) ↔ GT 군집 심도(전역 exact 중앙순위) Spearman ρ:
A postfilter 0.699 / single_stage 0.780 · B postfilter 0.616 / **single_stage 0.895** (n=29/25).
코퍼스 간 gradient도 정합: A의 위치 predicate(장면을 결정 → 강군집)가 B의 센서 predicate(조명/밀도만 상관 → 약군집)보다 열화가 큼 — 열화 크기는 predicate-임베딩 결합도의 함수.

### 운영 가이드라인 (3축, 실제 predicate 평균)

| 방법 | A recall / p50 | B recall / p50 | 비고 |
|---|---|---|---|
| prefilter_flat | 1.000 / 1.45ms | 1.000 / 3.21ms | 상한; s에 비례한 지연 |
| **prefilter_hnsw ef64** | **0.983 / 0.038ms** | **0.997 / 0.040ms** | 강건+최저지연; build_s는 predicate당 상각(핫/정적 파티션 전제) |
| postfilter K4x | 0.306 / 0.102ms | 0.667 / 0.082ms | 실제 predicate에서 신뢰 불가 |
| single_stage bitmap np32 | 0.750 / 0.153ms | 0.960 / 0.187ms | 재구축 없는 차선책(s≥0.25) |
| single_stage batch np128 | 0.735 / 0.180ms | 0.979 / 0.267ms | 에스컬레이션 비용 |

## 정직성 주기 (원고 반영 시 필수)

- 결론은 "본 하드웨어(CPU faiss, 단일스레드)·본 두 코퍼스(512-d CLIP)·P1 predicate 집합" 스코프. FAISS↔pgvector 절대 latency 비교 금지.
- A high(n=5)·B low(n=3) 밴드는 검정력 부족으로 확증 미달(방향은 동일) — 표에 그대로 표기.
- prefilter_hnsw의 predicate별 재색인 비용(build_s)은 CSV에 1급 열로 존재; "저카디널리티·정적 facet 파티션에서만 유효" 한계 유지(구39 규칙 승계).
- 대조군은 M9 사전등록 설계이며 사후 선택 아님. 확증 방법쌍·s-밴드는 유의성 계산 전 스크립트 헤더에 선언(M7).

## B-2 — 색인 3축 그리드, 두 번째 real 코퍼스 복제 (`index_grid_522visual/`)

522-visual **142K real** 전 스케일(10K/50K/100K/142K, synthetic 불필요), 38 config: HNSW ef64 = **0.9992 @ 0.047ms** vs Flat 14.2ms(≈300×); IVF-PQ m32/64 = 8–13MB(**22–35× 압축**) @ recall 0.35–0.49; build HNSW 47s/IVF 15–28s. sinnaedoro 131K(600)와 정합 — **색인 trade-off의 real 2점 확보**.

## B-3 — pgvector 실색인 (PG 16.14 / pgvector 0.8.4, `pgvector_ann_sweep.csv`+`pgvector_filtered.csv`)

- **비필터**(132K, 동일 `<#>` 연산자, exact=seq-scan GT): HNSW m16 ef16 **0.987 @ 0.26ms**(클라이언트 왕복; exact 218ms) ~ ef256 0.996 @ 0.78ms; IVFFlat probes8 0.996 @ 0.9–1.9ms. 빌드 49–88s(비병렬; 도커 /dev/shm 64MB↔병렬 DSM 충돌로 `max_parallel_maintenance_workers=0` 필요 — 재현 각주). index 333–350MB(faiss 268MB 직렬화 대비 페이지 오버헤드 — M11 각주 예측 그대로).
- **필터드 × iterative_scan GUC — B-1 메커니즘의 관계형 엔진 교차 재현**:

| predicate (s) | HNSW off | HNSW relaxed_order | IVF1024 relaxed |
|---|---|---|---|
| location=BC2000801 (0.086) | **0.121, short 88%** | 0.658 @ 19.0ms | 0.556 @ 10.6ms |
| location=중동사거리 (0.049) | **0.034, short 97%** | **0.302 @ 29.5ms, short 51%** | 0.481 @ 23.8ms |
| hour=6 (0.183) | 0.310, short 75% | **0.984 @ 1.0ms** | 0.806 |
| hour∈[6,18] (0.774) | 0.876 | 0.994 @ 0.44ms | 0.974 |

→ 상관 predicate(location)는 **pgvector의 공식 해법(0.8 iterative scan)으로도 부분 복구에 그침**(recall 0.30–0.66, 지연 20–70×), 약상관(hour)은 완전 복구 — faiss B-1과 동일한 군집 메커니즘. prefilter 아날로그(partial index per facet)는 미측정·후속 1줄 언급.
- 주장 한계 준수: faiss↔pgvector **latency 비율 서술 금지**(계측 경계 상이; exact 218ms vs 13ms가 그 자체 증거), 비교는 recall·planner 경로만. 단일 커넥션.

## E-2 — retrieval 패널 Pareto (`E2_retrieval_pareto.csv`)

(p95, recall) 지배 판정, 크기/빌드는 주석[AMD-B5]: **front 12/46**, 두 코퍼스 구조 동일 — HNSW(M16 ef16→256)가 0.03–0.31ms 영역 지배(recall 0.985–0.9998), IVF-Flat 고probe가 1–2ms 중간점, Flat=recall 1.0 앵커 @ 14.4/15.3ms. IVF-PQ는 front 밖이나 **압축 축**(8–13MB) 대표. answer 패널은 E-1 재설계(420 Amd.2) 결정 후.

## 검증·파생 분석 부록 (2026-07-11)

**수치 재집계 감사: 17/17 PASS** — 본 문서의 모든 헤드라인 수치(M9·확증가족·가이드라인 평균·B-2/B-3/E-2)를 원시 CSV에서 재집계해 일치 확인(F5 검증기 원칙).

**① prefilter 빌드 상각 손익분기** (subset-HNSW build_s ÷ (flat−hnsw p50), predicate별):
- A: build 중앙값 0.9s → **~1,869 질의**에서 손익분기 (IQR 1,789–1,990)
- B: build 중앙값 4.3s → **~2,442 질의** (IQR 2,138–2,773)
→ 운영 규칙: **predicate당 예상 질의 ≥ ~2K면 부분집합 색인 구축이 이득**, 미만이면 prefilter_flat(정확·무구축)이 합리적. "핫/정적 파티션 전제" 한계를 정량 임계값으로 대체.

**② K'-민감도: 과잉 인출은 군집을 못 고친다** — postfilter K'×1→×4에서 실제 predicate recall +0.065(A: 0.242→0.306) / +0.147(B: 0.520→0.667)에 그침(대조군은 0.86→0.92/0.96). 결손은 예산 문제가 아니라 **구조적**(부분집합의 진짜 이웃이 전역 랭킹 깊숙이 있음) — K' sweep 자체가 이를 증명.

**③ single-stage 에스컬레이션 발동률** — recall<0.9@np32로 np128 승급 필요: **A 25/29, B 13/25 predicates**. 상관 predicate에서 공유 IVF는 공격적 probing 없이는 신뢰 불가(그 비용 p50 0.18–0.27ms).

## 연결

- 600(구39) random-mask selectivity 결과는 "무상관 predicate 상한"으로 재해석·병치(폐기 아님).
- **Pillar B 완결**(B-1/B-2/B-3/E-2 retrieval). 남은 것: E-1 재설계 PI 결정, 원고 §Storage-Indexing 집필.


## B-4 제3 엔진 기전 재현 (2026-07-12) — Milvus·Weaviate

프리레지 420 Amendment 5/5a(3-렌즈 적대 검토 wf_1ad02af8-bf5의 확정 8건 반영: Milvus BF 폴백 경계 (0.923,0.934] 실측 분리, Weaviate 조건 재정의 w1=acorn+40K/w2=sweeping+0(확증)/w3=acorn+0, 확증 ={m1-graph,w2}×{A,B} Holm-4, 자연 predicate만, facet-가족 군집 부트스트랩 의무). 정본: `paper_assets/20260712_engine_replication/B4_RESULTS.md`.

- **확증**: 4/4 셀 방향 일치(실측 결손>무작위), 2/4 Holm-유의 — w2×A **+0.0098**(p 7e-5)·m1×B **+0.0028**(p .022), 둘 다 이중 CI 0 배제. 크기는 faiss naive(+0.61)의 1/40 이하.
- **완화 문서화**: Milvus BF 폴백(무성·설정 불가)·Weaviate flat cutoff(40K) 체제는 양팔 ≈1.0; **ACORN은 부호 역전**(B −0.018; 기전 ρ 음수 — 군집 역이용). 무작위-마스크 벤치마크는 방향까지 왜곡 가능.
- **기전 잔존**: m1-graph×B Δ↔군집심도 ρ=0.676(p=.002) — B-1과 동일 기전.
- **F7(시드 견고성)**: 대조군 7드로우 SD 0.001–0.010(최대 범위 0.047) ≪ M9 효과 → M9 결론 시드-견고. 원고 §7.1 문구 교체 완료.
- 게이트: G-ingest(0.996/0.997)·G-filter(엔진 카운트 108/108)·P1 양방향(29/25)·qidx sha256 고정. 원고 §7.2 확장+표5(구 표5→표6), ACORN=[23](Idefics2→[24]). F5 109/109·스위트 40/40.
