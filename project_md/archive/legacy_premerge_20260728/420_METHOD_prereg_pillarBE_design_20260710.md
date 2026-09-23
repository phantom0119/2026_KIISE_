# Pillar B/E 사전등록 설계 스펙 (색인 3축 + 답변 결합) — 심사-방어판

작성: 2026-07-10 (실행 전 LOCKED; 변경 시 본 문서에 diff 기록)
전제: 마스터플랜(42) Pillar B/E + 심사보고서(41) F6/F7/F9 대응. 실행 전 적대 검증 통과 후 착수.

## 0. 심사에서 죽는 지점과 본 설계의 방어

| 예상 지적 | 방어 설계 |
|---|---|
| "latency가 미격리 wall-clock" (원고가 이미 한 번 철회) | 검색계층만 격리: faiss `omp_set_num_threads(1)`, batch=1, **워밍업 W=5 유지·통계 제외**[AMD-M2], 반복 R=15, 질의별 중앙값→질의분포 p50/p95(+p99, n≥500 질의만), CI=질의 리샘플 부트스트랩, config 무작위 인터리빙+taskset. 동일 호스트·프로세스 내 상대비교만 주장; 절대 ms는 "본 하드웨어(2×RTX3090 호스트, CPU 검색)" 한정 |
| "random-mask predicate는 장난감" | **실제 predicate 주결과** + 각 predicate에 **동일-s random-mask 대조군 짝지어 병행**[AMD-M9](s-교락 분리; 합성 fraction은 주결과 금지·대조군 라벨만): sinnaedoro=location/camera/hour/date, 522=센서 조인 facet |
| "postfilter K'=×3은 임의" | **K' 민감도 sweep**: K' ∈ {⌈k/s⌉, 2⌈k/s⌉, 4⌈k/s⌉} 전부 보고, 단일 K' 결론 금지 |
| "작은 코퍼스에서 ANN 주장" (F9류) | **N-스케일 정직 게이트**: ANN 이득/crossover 주장은 N≥100K(sinnaedoro 132K, 522-visual 143K)에서만. 3K/1K 텍스트 코퍼스는 "이 규모엔 Flat이 최적"을 결과로 보고(그 자체가 운영 함의) |
| "CI 없음/다중비교" | recall: query-부트스트랩 95% CI. latency: 반복블록 백분위 CI. 답변정확도: paired bootstrap+Wilcoxon+**Holm 보정**(config 패밀리). 등가 주장 시 SESOI 사전등록 |
| "synthetic 1M 대표성" | synthetic_aug 행은 라벨 분리, crossover는 real≤143K 관측 + synthetic은 "증강 투영" 명시(기존 39 관례 유지) |
| "prefilter_hnsw는 predicate별 인덱스 재구축 = 비현실" | build_s를 1급 비용으로 보고 + "핫/정적 predicate 파티션에만 유효" 명시 + **single_stage(IVF+IDSelector) 추가**로 재구축 없는 대안 실측 |
| "답변 결합 없음 = 3축이 2축" (rq-coverage gap) | E-1에서 **동일 QA 파이프라인에 색인만 스왑**(exact→게이트 통과 중간·강열화 config[AMD-B3]), 정확도·**evidence-caption 회수율**[AMD-B2] 동시 측정, 매개 분석. 결과는 3-outcome(우월/등가/결론불가)으로만 서술[AMD-B4] |

## 1. B-1: 실 predicate filtered-ANN (2 코퍼스 복제)

- **코퍼스 A**: sinnaedoro `corpus_real/frame_embeddings.npy` 132,521×512 + `frame_index.parquet`(location/camera/date/time → hour 파생).
- **코퍼스 B [AMD-M5]**: 522-visual — 색인=**143,830 전 프레임**(CLIP ViT-B/32 512d, sinnaedoro 동일 인코더; ✅임베딩 완료·검증). predicate=`visual_sensor_join` 센서 facet; **미조인 프레임(≈9.8%)=facet-NULL로 전 predicate 불통과** + NULL 비율 열 병기(조인 프레임 실측 ≈129.7K). GT 분모=조인∩predicate 부분집합 내 exact top-10; selectivity는 프레임 가중; density_bin은 derived(tertile) 라벨; cross-camera ≤120s 조인의 라벨 근사성 1문장 한계 명시.
- **predicate 셋 [AMD-B1]**: 착수 전 실측표(**부속표 P1**)로 사전등록·고정. 두 등급 — **[natural]**=단일 facet 등호(camera=X, location=L, date=D, hour=h, sig_has_yellow 등), **[composite]**=범위·IN-집합(hour∈[h1,h2], location∈{top-k}; 파생규칙 명문화). 부정형(NOT) 불사용. 달성 범위 정직 기재: A=[~1e-4, 0.18] natural + [~0.3, ~0.77] composite / B=[~0.02, ~0.95]. 코퍼스 간 방법 비교 주장은 두 s-범위의 **교집합 구간에서만**. *(구 "[0.005,0.9] 자연 스펙트럼" 문구는 실데이터로 반증되어 폐기 — 단일 facet 최대 s=0.097.)*
- **방법**: prefilter_flat / prefilter_hnsw(M32,efC200,efS64; build_s 보고) / postfilter_hnsw(K' 3점 sweep) / **single_stage**: IVFFlat(nlist=1024,nprobe 8·32) + `IDSelectorBatch` (faiss SearchParametersIVF) — 재구축 없는 필터 통합.
- **GT**: subset 내 exact top-10. **지표**: recall@10(+query-bootstrap CI), p50/p95(single-thread), build_s, index_mb.
- **질의 [AMD-M5·M6]**: 코퍼스 A=기존 queries.npy(**1,000** — 구 "500" 표기 정정). 코퍼스 B=**층 분리 보고(풀링 금지)**: image-query 200개(held-out 프레임)=확증 층 / text-query 32개(캡션 질의 CLIP-text)=CI 병기 기술통계 층(패러프레이즈 클러스터 주석). tri-source B4−B2 결과와의 연속성 주장 금지(인코더·모달리티 상이).
- 재사용: `run_filtered_ann_benchmark.py` fork → `run_filtered_ann_real_predicate.py` (predicate-parquet 인자, K' sweep, single_stage, CI 추가).

## 2. B-2: 색인 3축 (기존 결과 승격 + QA 코퍼스 보강)

- sinnaedoro `index_benchmark_from_log.csv`(10K–1M, 55 config, p50/p95/index_mb/build_s) → **신규 계산 0, 본문 자산화**(real≤131K/synthetic 분리 라벨).
- 보강: 522-visual 143K에서 동일 그리드(flat/ivfflat/hnsw/ivfpq) 1회 실행 — real 코퍼스 2번째 점.
- 소형 QA 텍스트 코퍼스 [AMD-B5]: 522 3K는 flat vs hnsw 2점; **VRU 1K는 E-1 최종 스왑셋과 동일한 3점**(Flat/HNSW-final/IVFPQ-final)의 p50/p95·index_mb·build_s를 동일 bge-m3 1024d로 실측(CPU 수 분) — E-2 answer 패널 정합용. "Flat 최적" 근거는 latency 교차가 아니라 recall=1·build 0·운영 단순성으로 서술 [AMD-M10].

## 3. B-3: pgvector 실색인

- 컨테이너: `infra/docker-compose.pgvector.yml` (기존 P2/P4는 exact only였음).
- 코퍼스: sinnaedoro 132K(512d) + 522 텍스트 3K(1024d).
- 색인: HNSW(m∈{16,32}, ef_construction=200, ef_search∈{16,64,256}) / IVFFlat(lists=√N≈364·1024, probes∈{1,8,32}).
- 지표: recall@10 vs pgvector exact(동일 연산자), p50/p95(클라이언트 perf_counter, warm, 단일 커넥션), `pg_relation_size`(index_mb), build wall.
- 필터드: `WHERE facet=… ORDER BY emb <#> q LIMIT 10` — EXPLAIN(ANALYZE)로 planner 경로(iterative scan 여부) 기록, prefilter/postfilter faiss 결과와 병치.
- 주장 한계: "관계형 통합 시 품질-지연 재현" — TPS/동시성 주장 금지(단일 커넥션).

## 4. E-1: 색인 근사 → 답변 정확도 결합 (기존 검증 파이프라인 재사용)

- 파이프라인: `run_rag_vqa.py` (고정 LLM Qwen2.5-7B + Llama-3-8B, exact-match) — **이미 검증된 답변계층에 검색 색인만 스왑**. `exclude=cid`(자기 캡션 배제)는 **유지** [AMD-R6: 해제 시 순환 재도입 + oracle 포화].
- 스왑 조건 [AMD-B3]: {Flat(exact), 중간열화, 강열화} — 구 문구 "IVFPQ(m=8) recall 0.33-0.48 (131K 실측 근거)"는 **허위 인용으로 폐기**(실측 CSV에 m=8 행 없음; 0.334/0.481은 m=32/64이며 131K·512d CLIP 조건 → 1K·1024d bge-m3 전이 미확인). **조작점검 게이트 신설**: LLM 실행 전 retrieval-only 파일럿으로 후보 색인들의 evidence-recall@3 vs exact 실측 → 게이트: 중간 config ∈ [0.55,0.85]·강열화 ∈ [0.30,0.55](상대 밴드) → 조정 사다리(HNSW ef 16→8→4→2·M 32→8; IVFPQ nlist∈{16,25}·nprobe 8→4→2→1·m 8→4·nbits 8→6; 시도 전부 로그) → 게이트 통과 3-config를 diff로 LOCK 후에만 착수. 사다리 소진에도 미달 시 착수 금지·설계 재회부. null 해석은 본 게이트 통과(조작 성공)를 전제로만 발동.
- 측정 [AMD-B2]: (a) 답변 정확도, (b) **evidence-caption 회수율**(매개변수) — 문항(클립 c, 대상 facet f, 정답값 v)에 대해 top-3 캡션 중 metadata 기준 f=v인 **타 클립** 캡션 ≥1 포함 비율; qrels(facet-일치 캡션 집합)는 LLM 실행 전 사전 계산·고정; 문항×config `evidence_in_context`(0/1)를 결과 파일에 기록. *(구 "gold-caption-in-context"는 exclude=cid 하에서 항등 0이라 폐기)*, (c) Δacc vs Δevidence-recall 산점.
- 사전등록 가설/해석: H1 "recall 열화가 evidence 회수율을 낮추고 그만큼 정확도가 떨어진다". 해석은 3-outcome [AMD-B4]: ① 우월(Holm 유의) ② 등가(TOST 90% CI ⊂ ±0.02) ③ **결론불가(둘 다 아님 — '강건/평탄' 주장 금지, CI만 보고)**. null 해석 문구는 ②에서만 발동.
- 통계 [AMD-B4]: **n=6,000/config (vqa_joined.parquet 전량; 표본추출 없음)** — n=600은 CI 반너비 0.034-0.058로 SESOI 0.02와 양립 불가(실측 불일치율 기반 사전 계산; 6,000이면 0.011-0.019). Holm 계층화 [AMD-M7]: primary=Flat vs 강열화×2LLM(2검정), secondary=나머지 4검정. SESOI 0.02 정당화: oracle−closed 실측 격차 0.438의 ~4.6% — 검색 기여분의 5% 미만 변화를 실무적 무의미로 정의.
- 매개분석 [AMD-M8]: 간접효과=Δevidence-recall×(acc|ev−acc|no-ev)의 문항 부트스트랩 CI(5,000); 직접효과=logistic `correct ~ config + evidence_in_context`(문항 클러스터 부트스트랩); sequential ignorability 한계 명시, "완전매개 증명" 표현 금지.
- GPU 예산: 6,000×3config×2LLM = 36,000 생성 ≈ **12-20h (백그라운드; 게이트 통과 즉시 착수해 CPU 단계와 병렬)**.

## 5. E-2: 3축 Pareto 종합 [AMD-B5]

- **두 패널 분리(단일 frontier 합성 금지)**: (i) **retrieval Pareto** — 132K/143K 코퍼스, y=**recall@10**(B-1/B-2 등록 지표와 일치; 구 "nDCG" 표기 폐기); (ii) **answer Pareto** — VRU 1K 전용, y=answer acc, 보조 x=evidence-recall@3.
- x=p95 latency. 비용 표현: **마커 크기=index_mb, 색=build_s(합성 금지)**; Pareto 지배 판정은 (p95, 품질) 2축만, 비용은 동률해소(tie-break)로만. *(구 "z=index_mb+build_s" 단위 비정합 폐기)*
- 동일 코퍼스·동일 config에서 축들이 모두 실측된 점만 표기. pgvector 점은 E-2 미포함(계측 경계 상이) [AMD-M3].
- 비용 스코프 각주 [AMD-M11]: storage 주장은 색인 계층 한정 + 원본 자산 크기 문맥 행 병기; 임베딩=1회성 ingest 비용 별도 보고; faiss(직렬화) vs pgvector(릴레이션 페이지) index_mb 정의 차이 각주; E-1 결론에 검색 ms vs LLM 초의 규모 차이 명시.

## 6. 실행 순서·산출물 [AMD 재확정 — E-1(12-20h)이 임계경로이므로 게이트 통과 즉시 백그라운드 착수]

| 단계 | 자원 | 내용 | 의존 |
|---|---|---|---|
| 0 | CPU | 본 Amendment 반영(완료) | — |
| 1a | CPU 수 분 | **부속표 P1**: 코퍼스 A/B predicate·실측 selectivity 표 생성·등록 (B1) | 0 |
| 1b | GPU ~2분+CPU | **E-1 조작점검 파일럿**: VRU 1K bge-m3 evidence-recall@3 실측 → 게이트/사다리 → 스왑 3-config LOCK (B3) | 0 |
| 2 | GPU | 522 프레임 CLIP 임베딩 → `visual_embeddings_clip/` ✅ **완료(143,830×512 검증)** | 0 |
| 3 | GPU 12-20h, bg | E-1 색인스왑 RAG-VQA **n=6,000**×3config×2LLM (B4) → `rag_vqa_indexswap_*.parquet` | 1b |
| 4 | CPU | B-1 real-predicate + **동일-s random-mask 대조군**(M9) filtered-ANN (M1·M2·M4 반영, A→B) → `paper_assets/20260710_pillarB/` | 1a, 2 |
| 5 | CPU 수 분 | B-2: 522-visual 143K 그리드 + VRU 1K 스왑셋 3점 + 522 3K 2점 (B5) | 1b, 2 |
| 6 | docker | B-3 pgvector: 비정규화 스키마 + GUC 매트릭스 + EXPLAIN 분리 (M3) | 1a |
| 7 | CPU | E-1 통계(3-outcome·계층 Holm) + 문항수준 매개분석 (B4·M7·M8) | 3 |
| 8 | CPU | E-2 두 패널 Pareto (B5·M10·M11) | 4,5,7 |

## 7. 통계·정직성 공통 규칙 (전 실험 적용)

- 모든 헤드라인 비교에 95% CI(부트스트랩 5,000) + n 명시; 가족 단위 Holm — **Holm 확증 가족 명세 [AMD-M7]**: B-1은 코퍼스×사전지정 s-3구간(저/중/고)×방법쌍 recall 비교만 확증, 나머지 전 조합=탐색적(별표 금지·CI만); B-2/B-3/E-2는 확증 검정 없음(기술+CI).
- 등가 주장 시 SESOI: retrieval recall 0.02 / answer acc 0.02 (사전등록; E-1 정당화는 §4).
- 모든 표에 코퍼스 N·real/synthetic 라벨·질의 수·반복 수 병기.
- 수치는 결과 파일에서만(스크립트 재집계 가능해야 함) — F5 검증기 원칙.

---

## Amendment 1 (2026-07-10, 적대 검증 3-렌즈 종합 반영 — 상세는 검증 워크플로우 산출물)

**BLOCKER 반영(본문 인라인, [AMD-B*] 태그):** B1 predicate 2등급制·교집합 규칙(§1) / B2 매개변수를 evidence-caption 회수율로 재정의(§4) / B3 허위 인용 폐기+조작점검 게이트·사다리(§4) / B4 n=6,000·3-outcome·SESOI 정당화(§4) / B5 E-2 두 패널·VRU 1K 3점·비용 표현 분리(§2·§5).

**MAJOR 반영(실행 스크립트에 구속):**
- M1 타이밍 경계 통일: 방법별 계측=질의 도착→K개 반환 전 구간(postfilter의 mask 필터·절단 **포함**, numpy 벡터화); 사전 구축물은 build_s/selector_build_ms 분리; efSearch 방법 간 통일 또는 sweep 축 승격; faiss HNSW ef≥k 강제 각주; K'≤N 캡+저s "K'≈N 축퇴" 라벨.
- M2 latency 통계: 질의별 R=15 반복의 중앙값→질의분포 p50/p95, CI=질의 리샘플 5,000; **워밍업 W=5 유지하되 통계 제외**(§0 "warmup 폐기" 문구 정정); config 실행 순서 무작위 인터리빙+taskset; p99는 질의 n≥500 코퍼스만.
- M3 pgvector: documents 행 facet 비정규화+단일행 `ORDER BY embedding <#> q LIMIT 10`(기존 EAV+GROUP BY 경로 금지 — 벡터 인덱스 불가); GUC 매트릭스 `hnsw.iterative_scan∈{off,relaxed_order}`(+ivfflat 대응)·`max_scan_tuples`, `SET LOCAL` 질의별 고정(0.8.4 실측 기록); 반환 행수(<10) 열; EXPLAIN(ANALYZE)은 timed 반복과 분리; `<#>` 사용 시 정규화 삽입으로 faiss IP 동치; 병치표에 계측 경계 열 의무 + faiss↔pgvector latency 비율 서술 금지(비교는 recall·planner 경로만).
- M4 single_stage 공정성: selector_build_ms 별도 열(predicate당 1회 상각); s≥0.25 행에 IDSelectorBitmap 변형 병행; nprobe=32 recall<0.9면 nprobe=128 1점 추가.
- M5 코퍼스 B 정직화: 색인=143,830 전 프레임, 미조인 프레임=facet-NULL 전 predicate 불통과 + NULL 비율(9.8%) 열; "조인 141K"→실측 ≈129.7K 정정; GT 분모="조인∩predicate 부분집합 내 exact top-10"; selectivity는 프레임 가중; density_bin은 derived(tertile) 라벨; cross-camera ≤120s 조인 근사성 1문장; §1 `queries.npy(500)`→**(1000)** 정정.
- M6 코퍼스 B 질의 층화: text 32 / image 200 풀링 금지·별도 행; 확증 주장은 image-200 층만, text-32는 CI 병기 기술통계(패러프레이즈 클러스터 주석); tri-source B4−B2 결과와의 연속성 주장 금지(인코더·모달리티 상이).
- M7·M8: §7·§4에 인라인 반영.
- M9 s-교락 대조군: 각 자연 predicate에 동일-s random-mask 대조군 짝지어 실행(기존 코드=대조군으로 강등); §0 "합성 fraction 금지"→"주결과 금지, 동일-s 대조군 라벨만 허용"; predicate별 GT top-10 전역 rank 중앙값(군집도 공변량) 기록; 결론은 predicate 유형별 한정.
- M10 "crossover" 어휘 금지→"regime" (실측 교차점은 10K 미만); M11 비용 스코프 각주(§5 반영).

**기각(근거 요약):** R1 pg heap+index 이중보고 의무(전제 사실오류) / R2 공통상수 비용 산입 / R3 저s postfilter 붕괴=병리 확인 가치 / R4 n·SESOI 완화안(6,000 전량이 우월) / R5 NOT-predicate / R6 exclude=cid 해제(순환 재도입) / R7 패러프레이즈 정량 주장(주석 의무만).

---

## Amendment 2 (2026-07-10, E-1 조작점검 게이트 FAIL — 사전등록 규칙에 따른 착수 금지 기록)

**파일럿 실측** (`paper_assets/20260710_pillarB/e1_pilot_configs.csv`, n=6,000 질의 × 26 ladder config):
- exact evidence-recall@3 = **0.5162**; 사다리 전 구간(HNSW M∈{32,8}×ef∈{16..1}, IVFPQ nlist∈{16,25}×m∈{8,4}×nprobe∈{8..1}) **rel ∈ [0.974, 1.053]** — 중간밴드[0.55,0.85]·강밴드[0.30,0.55] 도달 config **0개**. 일부 config는 exact보다 높음.
- **기전 진단**: (i) evidence 집합 과밀(평균 334.3/1,000 = 33%) — facet 값 공유 클립이 코퍼스의 1/3이라 어떤 top-3도 고확률 적중, (ii) 1K 벡터에선 PQ급 근사도 의미 이웃을 대체로 보존, (iii) 근사 오차가 무작위화로 작동해 밀집 evidence에서 회수율을 **올림**(random-3 기대 0.705 > exact 0.516).
- **판정**: 사다리 소진 → **E-1(색인근사→답변 결합) 본 실험 착수 금지** (§4 게이트 규칙 그대로 적용). GPU 12–20h 소비 전 차단됨.

**정직한 부산물(그 자체로 보고 가치)**: "1K-문서급 RAG 코퍼스에서는 색인 선택이 evidence 전달을 사실상 바꾸지 못한다(mediator 불변, 26 config 실측)" — §2의 '소형 코퍼스 Flat 최적' 행을 **답변계층 수준의 조작점검 영수증**으로 보강.

**재설계 선택지 (PI 결정 대기; 결정 전 E-2 answer 패널 보류, retrieval 패널은 무관):**
- **(a) E-1을 143K 코퍼스로 이전**: 522-visual 프레임 검색 + 센서-집계 프로그램 검증 QA + 고정 VLM — 색인 근사가 실제로 작동하는 규모에서 결합 측정(신규 프리레지 필요, VLM 프레임 answering ≈ 유사한 GPU 예산).
- **(b) E-1 축소 종결**: 위 부산물을 결과로 확정하고, 색인→답변 결합은 "small-corpus에선 무결합(실측), large-corpus는 향후"로 정직 보고.
- (b)는 즉시 가능·비용 0, (a)는 RQ-ALC의 답변축을 완전히 닫음.

---

## Amendment 3 (2026-07-11) — E-1(a) 재설계: 143K 답변-결합 실험 프리레지

Amd.2의 재설계 선택지 (a) 실행. 1K에서 불가능했던 조작이 143K에서 성립함을 게이트로 먼저 확인.

**설계 (비순환 유지):**
- 항목 = (시각 비디오 v, v의 순간에 대한 이진 장면 질문, **정답=사람 주석 채널**(TL_3/4) of v).
- 검색 = v의 중간 프레임 임베딩으로 **143,830 전프레임 코퍼스** top-K(K=3), 자기 제외. VLM은 **검색된 프레임만** 본다(질의 프레임 미노출 — DB가 evidence를 공급하는 구조 그대로).
- **매개변수 = moment-recall@3**: top-K ∩ {v의 형제 프레임 ∪ 동일 sensor_clip에 조인된 교차카메라 프레임}. 순간 그룹 31,380개, 항목당 evidence 중앙값 4프레임/143,830 — 희소.
- 질문 3종(주석 gold, 층화로 50/50 균형): bus(max_bus≥1) / stopped(any_stopped) / bikes(max_bike≥2). 고정 VLM Qwen2.5-VL, greedy, yes/no 강제.
- 배제 규칙 유지: exclude=self (프레임 수준).

**조작점검 게이트 (실행 완료, PASS — `paper_assets/20260711_e1a/e1a_pilot_mediator.csv`):**
- exact moment-recall@3 = **0.1203** (n=2,967 파일럿 항목).
- 사다리 18 config: HNSW/IVFFlat은 rel≥0.87(조작 부족), **IVF-PQ가 열화 제공** — mid=**hnsw_M8_ef1**(rel 0.807)…실은 [0.55,0.85] 상단, 대안 ivfpq_m64(rel 0.627–0.650); strong=**ivfpq_m32_np8**(rel 0.451). LOCK: `e1a_locked_configs.json`.
- 정직 주기: 기저 12%가 낮은 이유 = 동일 카메라 배경 유사성(형제 프레임이 타 순간 동일-카메라 프레임에 묻힘). 이는 CCTV 프레임 임베딩 검색의 실제 한계이며 그 자체 보고 가치.

**본실험 규모 규칙(사전등록):** n = 미니 파일럿(360콜, 3질문×gold균형×{exact,strong})의 **쌍대 불일치율 d̂**로 paired CI 반너비 1.96√(d̂/n) ≤ SESOI 0.02를 만족하는 최소 n, **상한 6,000 항목**(초과 필요 시 착수 금지·재회부). 해석은 Amd.1의 3-outcome(우월/등가 TOST ±0.02/결론불가) + Holm(primary=exact vs strong×3질문형).
**중단 규칙:** 미니 파일럿에서 인과 지렛대(acc|hit − acc|no-hit)가 CI로 0과 구별 불가하면 → 효과 전달 경로 부재로 판정, 본실험 착수 금지, "143K에서도 답변축은 mediator 희소성에 의해 제한"을 정직 결과로 보고.

## Amendment 4 (2026-07-11) — E-1(a) 중단 규칙 발동, 답변-결합 축 정직 종결

미니 파일럿(360콜, 3질문형×gold균형×{exact, strong=ivfpq_m32_np8}, `paper_assets/20260711_e1a/e1a_vlm_minipilot.parquet`):
- **인과 지렛대 null**: acc|mediator-hit 0.5625 vs no-hit 0.5823 → 지렛대 −0.020, CI ≈ ±0.13 (0 포함) — **Amd.3 중단 규칙 그대로 발동, 본실험(≈12–20 GPU-h) 착수 금지.**
- 매개변수 조작은 성공(hit-rate exact 0.122 → strong 0.056; 게이트 파일럿과 정합) — 사슬은 검색 단이 아니라 **지각 단에서 단절**: VLM 절대 정확도 0.567–0.594(chance 0.5; bikes 0.52≈chance). 부수: Δacc(exact−strong)=+0.028, 쌍대 불일치율 0.206(n=2,000이면 CI ±0.020 — 그러나 지렛대 부재로 무의미).

**종결 판정(= 선택지 (b)의 강화판):** 색인근사→답변 결합은 본 설정들에서 **두 개의 벽**으로 차단됨을 실측 — ①소형(1K) 코퍼스: 색인 열화가 evidence 전달을 못 움직임(Amd.2) ②대형(143K) 프레임 코퍼스: evidence 전달은 움직이나 고정 VLM의 미세 장면 지각이 병목이라 정확도로 전달 안 됨(본 Amd.). → 원고 서술: "본 체제에서 색인 선택의 답변축 효과는 지지 불가 — 소형에선 mediator 벽, 대형에선 perception 벽. 'end-to-end 평가'가 색인 효과를 보려면 두 벽을 모두 넘는 설정이 필요함을 정량 제시." 기존 상시 규칙(색인→end-to-end 과장 금지)의 **실증 근거**로 승격. E-2 answer 패널은 미게시 확정(retrieval 패널만 게시).

## Amendment 5 (2026-07-12) — B-4 프리레지: 제3 엔진(Milvus·Weaviate) 기전 재현

**목적(가설).** H-B4: "실측(상관) predicate가 공유 색인 filtered-ANN의 재현율을 동일-선택도 무작위 마스크 대비 떨어뜨린다"는 B-1(faiss)·B-3(pgvector) 기전이 **전용 벡터 DB의 네이티브 필터드 경로에서도 재현**된다. 예상 부호: real 재현율 < control 재현율; 결손은 GT-군집 심도와 양의 상관. 재현 실패 시 그대로 보고(엔진별 완화 설계가 기전을 흡수할 수 있음 — 그 자체가 발견).

**대상·버전(고정).** Weaviate 서버 1.35.3(도커, 기가동) + weaviate-client v4(신규 venv `Datasets/envs/kiise-engines`), Milvus standalone v2.6.0(도커, 기가동) + pymilvus 3.0.0. 기존 컬렉션 0개 확인(충돌 없음); 본 실험 컬렉션은 `kiise_*` 접두, 실험 후 보존(재실행 가능성) 및 문서화.

**데이터·질의(고정, B-1과 동일).** 코퍼스 A=시내도로 132,521×512 CLIP(질의=CLIP-text 1,000, 자기 제외 없음), 코퍼스 B=522 프레임 143,830×512(질의=이미지 200 = `default_rng(20260710).choice(N,200,replace=False)` 첫 호출 재현, 자기 제외). predicate = P1 잠금 테이블 재도출(등록 카운트 어서션 통과 필수; A 29·B 25).

**대조군(신규 시드, 선언).** 무작위 마스크는 predicate당 동일 크기, `default_rng(20260712 + predicate_index)` — B-1의 20260710 스트림과 **다른 독립 드로우**임을 명시(엔진 내 real-vs-control 짝 비교가 주장 단위이므로 비트 동일성 불요). **보너스 레인(codex F7 응답)**: 동일 신규 대조군에서 faiss postfilter K'1x·single_stage np8/np32 재현율만 재계산(타이밍 없음) → M9 과대평가량의 시드 민감도 표.

**색인·탐색 파라미터(faiss 미러링).** HNSW M(maxConnections)=32, efConstruction=200, 탐색 ef=64, metric=IP(정규화 벡터). 조건: (m1) Milvus 기본 필터드 경로(expr→bitset prefilter+HNSW). (w1) Weaviate 기본(flatSearchCutoff=서버 기본값 — 소선택도에서 flat 폴백이 기대되며 이는 **엔진의 공학적 완화책 발견**으로 보고), (w2) flatSearchCutoff=0(순수 필터드-HNSW 경로 노출). 배치 검색 허용(재현율), 지연은 클라이언트 RT 단건 p50 — **엔진 간 지연 절대 비교 금지**(계측 경계 상이, §5.3 원칙), 엔진 내 상대 서술만.

**GT·지표(고정).** GT = 부분집합 내 exact top-10(faiss FlatIP, 자기 제외) — 엔진 무관 로컬 계산, 스테이지-1 산출물로 고정 저장. 지표 = recall@10 vs GT, 질의 부트스트랩 CI(5,000).

**게이트(착수 전).** G-ingest: 엔진별 적재 수 = N 정확 일치 AND 비필터 recall@10 ≥ 0.95(faiss ef64는 0.997/0.9992였음) — 미달 시 파라미터/적재 조사, 본실험 금지. 스모크: predicate 2개 한정 전 경로 관통.

**확증 통계(계산 전 선언).** 가족 = {m1, w1, w2} × {A, B} = 6 검정: predicate-쌍 단위 paired Δ(control−real) 평균, predicate-부트스트랩 CI + Wilcoxon, **Holm 6-가족**. 기전 상관(결손 vs gt_cluster_med_rank Spearman)은 기술(secondary). w1의 flat 폴백 구간(부분집합<cutoff)은 별도 행으로 분리 보고(혼입 금지).

**중단 규칙.** G-ingest 실패 엔진은 해당 엔진만 제외하고 나머지 진행(전체 중단 아님). 산출물: `paper_assets/20260712_engine_replication/`.

## Amendment 5a (2026-07-12) — B-4 설계 정정 (3-렌즈 적대 검토 8건 확정 반영; 확증 계산 전)

검토 산출물: 워크플로우 wf_1ad02af8-bf5 (15 에이전트, BLOCKER 3·MAJOR 5 확정, 3건 반박 기각). 원시 recall 수집은 유효(재수집 불요); 조건 정의·확증 가족·게이트만 아래와 같이 **분석 전 재선언**한다.

**(1) 엔진 폴백의 대칭 처리.** Milvus knowhere는 filtered-out 비율 >~0.93에서 무성 브루트포스 폴백(설정 불가) — 이미 수집된 m1×A 데이터에서 경계 (0.923, 0.934] 실증(저 s 18/29쌍 양팔 recall≥0.9986). 따라서 m1을 **m1-graph**(filtered-out<경계; 확증)와 **m1-BF**(기술; w1 flat 폴백의 Milvus 대응물, 혼입 금지)로 분리한다. 경계는 등급별 s 무작위 마스크 스윕으로 실측해 manifest에 기록한다.

**(2) Weaviate 조건 재정의.** 1.34+ 기본 filterStrategy=**ACORN**(상관-필터 완화책)이므로: **w1** := acorn + cutoff=40000(서버 기본; 기술 — flat 폴백 완화 문서화), **w2** := **sweeping** + cutoff=0(순수 allowlist-HNSW; **확증** — 공유 색인 기전의 진짜 대응 경로), **w3** := acorn + cutoff=0(ACORN 완화 문서화; 기술). 기존 수집분의 'w2' 행은 정의상 w3으로 재라벨(변경 기록 manifest). filterStrategy는 행 단위로 기록.

**(3) 확증 가족 재선언** = {m1-graph, w2-sweeping} × {A,B} = **4 Holm 검정**. w1×A는 cutoff 초과쌍 3개로 구조적 기각 불능(Wilcoxon min p=0.25) → w1 전체를 기술 레인으로 강등(검토 지적 그대로).

**(4) 의사반복 방지.** 1차 확증 = **자연 predicate만**(A 24·B 22; 합성은 결정론적 합집합이라 기술로 강등). 헤드라인 재현 주장에는 predicate-부트스트랩과 **facet-가족 군집 부트스트랩**(A: location/date/hour, B: time_of_day/signal/density/hour 가족 재표집) CI가 **모두** 0을 배제해야 한다. 질의 공유로 인한 쌍 간 의존은 한계로 명기.

**(5) 게이트 확장(G-filter).** 모든 마스크에 대해 엔진측 필터 카운트 == 로컬 마스크 크기 어서션(Milvus count(expr) / Weaviate 필터 aggregate); Milvus는 index_building_progress 100%·세그먼트 상태를 manifest에 기록. (기수집분에도 소급 검증.)

**(6) 재현 산출물 보강.** qidx_B.npy + sha256 고정(넘파이 교차 버전 일치 실측됨); P1 어서션을 양방향 집합 동등(재도출 == 등록 비메타 행, A 29·B 25)으로 강화; 대조군 시드 정의 명문화 = `default_rng(20260712 + pi)`, pi = 마스크 생성 순서(masks_corpus_*() 열거 순, 등록표 비메타 행 순과 동일); 서버 에코 설정(describe/schema) manifest 덤프.

**(7) F7 레인 재명명·확장.** 2-시드 비교는 '시드 재현 스팟체크'로 명명하고, 민감도 주장용으로 predicate당 대조군 **r=5 반복 드로우**(시드 `20260712 + 1000·r + pi`, r=1..5)의 faiss recall-only 분포(SD/range)를 추가한다. 엔진 레인의 대조군이 1드로우인 MC 노이즈는 한계로 명기.

기각된 지적(기록): 코퍼스 B 자기 제외 프로토콜(이미 K+1 구현), 확증 규칙 미고정(분석 스크립트가 사전 고정), 대조군 오염(스테이지-1에서 사전 동결) — 3건 반박 성립.

## Amendment 6 (2026-07-12) — UCA 외적 타당성 워크로드 프리레지 (2.5-채널, 탐색적)

**목적.** 비순환 프로토콜(3절)의 도메인 외적 타당성: 한국 교통(VRU/AIHub/522) 밖의 영어·이상행동 도메인(UCA/UCF-Crime[11,12])에서 (i) 이중 정답 구조(strict의 구성적 prefilter 우위 vs semantic의 비보장 — 질의별 부호에 음수 존재), (ii) 결합도-Δ 방향 경향이 재현되는지 보고한다. **지위 = 탐색적 외적 타당성 트랙: 새 확증 헤드라인을 만들지 않는다**(522 곡선의 탐색 지위와 대칭; 방향 일치/불일치 자체를 정직 보고). 200_RELATED §3 채택 스케치의 실행이다.

**데이터·라이선스.** UCA 주석(GitHub 공개; G-A 게이트 PASS: 1,854 비디오·23,542 문장·분할 1,165/379/310 논문 일치) + UCF-Crimes.zip(CRCV 직링크, Content-Length 102,957,372,377B 실측 — 견적 37GB 아님). 프로젝트 페이지 기준 학술 연구 전용을 원고 availability에 명기.

**코퍼스(세그먼트) — 기계 규칙.** 비디오별 timestamps 정렬 후 균등 간격 인덱스 `round(linspace(0, n−1, min(n, 4)))`로 **비디오당 최대 4 이벤트** 선별(1,179문장 장영상의 지배 방지; 결정론). 문서 = 각 이벤트 **중앙 시점 프레임 1장**을 Qwen2.5-VL로 캡션(픽셀만; 장면 서술 프롬프트 — 렉시콘 용어를 프롬프트에 넣지 않음; 프롬프트-과제 결합은 522와 동일하게 공개 한계). 예상 규모 ~6K 세그먼트, 2×3090 ≈ 3-4 GPU-h.

**정답 채널(주석) — 후보 렉시콘 10종 동결.** 세그먼트의 자기 주석 문장에 대한 정규식 매칭: ①falls: fell|falls|falling|knock(ed)? down|collaps ②fight: fight|fighting|punch|kick|beat|hit(ting)? ③fire: fire|smoke|flame|burn ④weapon: gun|pistol|rifle|knife|weapon ⑤running: \bran\b|running ⑥crash: crash|collid|collision|accident ⑦money: money|cash|register ⑧door: \bdoor\b ⑨take: took|grabbed|picked up ⑩enterexit: entered|exited|left the. **채택 = 522와 동일 밀도 창 [1%, 12%] + 질의당 strict 양성 ≥5** — 사후 추가·수정 금지. 채택 렉시콘 <3이면 워크로드 부적합으로 정직 보고(강행 금지).

**predicate 채널(큐레이션·컨테이너) — 3필드.** ①video_class(14값; UCF-Crime 저자의 큐레이션 — 정답과 강결합 예상, V로 실측해 스펙트럼 축으로 사용, 저결합 predicate가 헤드라인) ②video_duration_bin(비디오 길이 3분위; 컨테이너 메타데이터) ③event_position_bin(이벤트 중앙시점/duration 3분위; **주석 타이밍 채널 유래 — 내용 무관이나 별도 공개**). 값 상한 12(522 규칙).

**질의 — 기계 교차곱.** (필드값 × 채택 렉시콘), strict 양성 ≥5; 질의문 = 렉시콘당 1개 동결 영어 문구 + metadata_filter. 이중 qrels(strict/semantic). 쌍별 Cramér's V 라벨(저결합 V<0.3). 채택 질의 <30이면 "저검정력, 보고 전용".

**감사 A6-UCA (6 어서션 + 부호 동반).** (a) 필터 키 ⊂ {class, duration_bin, position_bin} (b) 정답 ⊂ 동결 렉시콘 (c) 키 교집합 ∅ (d) metadata 테이블에 정답 플래그 없음 (e) 문서-주석 **verbatim 8-gram 중복 0** + 라벨 키 누출 0(단, 동일 픽셀 유래의 어휘 중복률은 별도 보고 — 2.5채널 정직 한계: 주석자·캡셔너가 같은 픽셀을 봄) (f) 채택 정답 밀도 ∈ [1,12]%. 부호 분포(B4−B2 semantic)의 음수 존재를 C1 붕괴의 경험 동반 지표로 보고.

**검색·통계.** B0(메타만)/B1(BM25)/B2(dense bge-m3)/B4(prefilter+dense)/B5(postfilter) — 522 체인 재사용. 통계는 **처음부터 군집 인지**: 질의 부트스트랩 + (필드×렉시콘) 쌍 군집 부트스트랩 병기(07-12 군집 교훈 선제 적용); 방향 서술만, CI 0 배제 주장 금지(탐색 지위).

**게이트.** G-B: zip 크기=Content-Length·unzip -t 표본·주석 id 1,854개 전부 zip 내 존재. G-C: 캡션 파일럿 50(층화) — 비어있지 않음·영어·중앙 토큰 ≥15·(e) 누출 어서션·프레임 타임스탬프 유효 → PASS 전 전체 GPU 금지. G-D: A6-UCA 6/6. 산출물: `Datasets/processed/uca_anchor/20260712/` + `paper_assets/20260712_uca_external/`.

## Amendment 6a (2026-07-12) — UCA 설계 정정 (3-렌즈 적대 검토 12건 확정 + 5 보완 반영; 빌드·GPU 전)

검토: wf_d349a707-48e (18 에이전트; 검증자들이 주석 원본 JSON에서 전 수치 재현). 아래가 Amendment 6을 대체·구체화하는 **동결본**이다.

**(1) 렉시콘 정정·재동결 (BLOCKER: `hit`가 'white' 내부 매칭 — 위양성 81%, fight가 코드 버그로 부당 탈락할 뻔).** 전 렉시콘 좌측 단어 경계 + `re.IGNORECASE` 명시. 수정 밀도 실측(중복 붕괴 후 6,432 문서) — **10/10 채택**:
| 렉시콘 | 정규식(동결) | 밀도 |
|---|---|---|
| falls | `\b(fell|falls|falling|knocked down|collaps)` | 1.40% |
| fight | `\b(fight|punch|kick|beat|hit(ting)?)` | 4.62% |
| fire | `\b(fire|smoke|flame|burn)` | 2.13% |
| weapon | `\b(gun|pistol|rifle|knife|weapon)` | 2.22% |
| running | `\b(ran|runs?|running)\b` | 4.77% |
| crash | `\b(crash|collid|collision|accident)` | 1.12% |
| money | `\b(money|cash\b|register)` | 1.82% |
| door | `\bdoors?\b` | 10.93% |
| take | `\b(took|grabbed|picked up)` | 6.36% |
| enterexit | `\b(entered|exited|left the)` | 5.07% |

**(2) 코퍼스 중복 붕괴 규칙.** 동일 (video_id, midpoint) 세그먼트는 1 문서로 붕괴, 문장은 합집합으로 렉시콘 매칭(58개 붕괴 → 6,432 문서; <1s 근접 중복은 카운트 보고). linspace 규칙이 비디오 양끝 이벤트를 항상 포함해 밀도를 재가중함을 공개(측정: 경계 이벤트에서 falls 0.40× 등; V(position×lex)≤0.062라 결론 불변).

**(3) qrels 정의 명문 + 퇴화 스크린 (MAJOR: class 필드의 C1-재라벨링).** strict = 렉시콘 ∧ predicate, semantic = 렉시콘만(§3 정의 상속). **class-필드 질의는 'C1-재라벨링 계층'으로 별도 보고**하고 고전적 prefilter 가치의 재현 근거로 인용 금지(큐레이터 라벨이 정답 내용과 동일 사건을 부호화 — v1 패턴; 522의 외생 센서와 다름). 퇴화 스크린(사전등록): 필터 클래스 밖 semantic 양성 <10 또는 클래스 내 봉쇄율 >0.9인 쌍은 확률적 부호 관찰이 구조적으로 불가 → 분리 보고(현 데이터에서 정확히 1쌍: RoadAccidents×crash, 봉쇄 0.904). V는 퇴화를 탐지하지 못함을 명기(V=0.351<0.569인데 더 퇴화).

**(4) predicate 채널 재분류 (MAJOR).** **duration_bin(컨테이너 속성) = 유일한 채널-청정 헤드라인 필드**; position_bin = 주석-타이밍 유래로 강등(보고 전용, 헤드라인 금지); class = 라벨-부호화 계층(위 (3)). A6-UCA에 **predicate 출처 어서션** 추가: 각 predicate → 소스 파일·필드·생산자 기계 매핑 표(키-이름 분리가 아니라 소스 분리를 감사). 코퍼스 멤버십 자체가 주석 주도(어떤 프레임이 문서가 되는가)임을 공개 1줄.

**(5) 결합도 축의 이중 계층 보고 (MAJOR: 스펙트럼이 쌍봉 — 고 V는 전부 라벨 필드).** 실측: 컨테이너·타이밍 필드 V≤0.077, class 필드 V∈[0.125,0.569], 빈 대역 (0.068,0.125). 따라서 UCA에서는 **단조 곡선 주장 금지**; Δ-V 산점을 채널 계층 주석과 함께 그리고, 주장은 부호 구조로 한정. 질의 결합 라벨 = **값-수준 φ**(질의의 실제 2×2 대비; 필드-V는 기술 열; 4/68 질의의 라벨이 갈리는 것 실측).

**(6) 방향-일치의 반증 가능 규칙 (BLOCKER: 미선언 시 반증 불가).** 대조 목록 4개 동결: ①strict 풀 Δ(B4−B2) 부호 >0 ②semantic 저-V 필드(duration_bin) 풀 Δ 부호 ③semantic 질의별 부호에 음수 존재(C1 붕괴 증인) ④semantic에서 Δ(class 계층) > Δ(저-V 필드) 순서. **'522와 방향 일치' 판정 = 4중 3 이상**; 어느 쪽이든 집계 그대로 보고. 부호는 질의·군집 부트스트랩 점추정 모두에서 확인.

**(7) 의존 구조 3-레인 (MAJOR).** ①(필드×렉시콘) 쌍 군집(27) ②**렉시콘-수준 군집(10; 최보수 — 동결 질의문이 렉시콘당 1개라 B1/B2 랭킹이 필드 간 공유됨)** ③비디오-중복제거 채점 레인(top-10에서 비디오당 정답 1회) 병기. 질의 채택에 '**서로 다른 비디오 ≥5**' 추가(현 데이터 비용: 1/122 질의).

**(8) 감사 (e) 재구성 (BLOCKER: 정형 문구 위양성으로 무조건 하드 실패 예정).** (e1) 하드: 라벨-키 누출 0 — 동결 토큰 = 클래스명 14 + predicate 필드/값 문자열 (e2) 하드: **렉시콘 용어 포함 8-gram** 문서-주석 중복 0 (e3) 일반 verbatim 8-gram 중복은 **보고**(세그먼트 제외 처리 규칙 + 코퍼스 2% 초과 시 중단). 픽셀 매개 어휘 중복은 2.5채널의 공개 잔여 한계.

**(9) 게이트 보강.** class 값 상한 **철폐**(14값 전수; 522 상한은 고카디널리티용이었음 — 대체 근거 기록), Normal_Videos(문서 47.1%)는 합법 필터 값이되 **고선택도 계층으로 분리 보고**. G-B에 id↔멤버 **전단사 규칙**(basename−'.mp4' == id, 대소문자 구분; 1,854 전단사 + 미매칭 멤버 수(≈46) 보고 — 사전 range-요청 검증 완료). **G-B′(신설, GPU 전 CPU 게이트)**: 1,854 전체 ffprobe — container_duration ≥ 해당 비디오 최대 midpoint + 0.5s, 위반 시 clamp(mid←container−0.5) + 건수 보고; 추출은 ffmpeg 시간-기반 시킹(OpenCV 프레임 인덱스 산술 금지). G-C 파일럿 50에 적대 계층 강제 포함: 최장 비디오·근말단 midpoint 6건·Normal 두 id 스타일·폴더별 ≥1. 저검정력 게이트 재정의: 채택 렉시콘 <5 또는 채택 필드 가족 <2면 '보고 전용'(기대치 동결: 문서 6,432·렉시콘 10·질의 ~122+fight 추가분).

기각 3건(기록): 밀도 분모 모호(자기 문장 규칙으로 유일), 522 대역 공동화(빈 대역이 기존 대역 내부), 값 상한 12 내부 모순(규칙 자체는 결정론 — 단 (9)에서 상한 철폐로 대체).

**Amendment 6a 게이트 집행 기록 (2026-07-12, 빌드 전).** G-B 실측: mp4 멤버 1,950 · 고유 basename 1,900 · 주석 1,854 전부 존재 · 미매칭 멤버 47(≈46 기대와 일치). **전단사 위반 49건 검출**(Normal id가 `Testing_Normal_Videos_Anomaly/`와 `z_Normal_Videos_event/` 두 폴더에 중복) — 50쌍 전부 압축 해제 크기 동일(동일 파일 중복). **해소 규칙(사용 전 선언): 멤버 경로 사전순 첫 항목 채택**; 채택 매핑은 `id_to_member.json`으로 동결, 중복 건수는 manifest에 보고.

## Amendment 7 (2026-07-12) — P7: 결합도·군집 인지 필터드 검색 구조 (CC-FR) 프리레지

**동기(목표 #3 정면 타격).** 지금까지의 실험은 "실측 상관 predicate가 공유 색인 filtered-ANN을 무너뜨린다(결손=임베딩 군집 심도의 함수)"와 "prefilter 가치는 제약 경성·결합도의 함수"라는 **기전**을 확증했다. 이 기전은 곧 설계 원리다. 본 Amendment는 그 기전으로부터 **우리만의 구조**를 고안·구현·검증하고, 그 구조를 실어 **색인·검색 구조 선택 → VLM-QA 정확도**의 인과 사슬(목표 #3, RQ-M 종착점)을 두 벽을 우회하는 설계로 닫는다. 주제 불변(재프레이밍 아님) — 기여를 "벤치마크+가이드라인"에서 "제안 구조"로 격상.

**구조 정의 (CC-FR = Coupling-and-Cluster-aware Filtered Retrieval; 동결).**
질의 q(=의미 조건 + predicate p)에 대해, 오프라인 predicate 통계 3종으로 검색 계획을 라우팅한다:
- **경성 h_p**: 하드 제약(strict 계약) vs 소프트 의도(질의 타입 라벨; 워크로드가 부여).
- **결합도 V_p**: predicate×의미조건 Cramér's V(오프라인 산정; 3절).
- **군집 심도 κ_p(질의 무관, 신규)**: subset S_p에서 최대 200개 멤버를 유사질의로 삼아, 각 멤버의 **전역 exact 랭킹에서 자신의 in-subset exact top-10 이웃(자기 제외)의 중앙 순위** d를 구하고 κ_p = median_q'(d). κ_p↑ ⇒ subset의 최근접이 전역 랭킹 깊이에 위치 ⇒ 제한된 K'/nprobe의 공유 색인이 in-subset 이웃을 놓침 ⇒ 공유 postfilter 위험. gt_cluster_med_rank(질의 구동)의 배포 가능 대응물이며 임베딩+마스크만으로 계산.
- **빈도 f_p**: 질의 트래픽(상각 판정용).

**플래너 결정 규칙 (동결):**
- h_p = 하드 → prefilter 필수(계약). 색인: f_p ≥ τ_amort(핫)이면 부분집합 지역 HNSW 물질화; 콜드면 지역 Flat; 재구축 불가면 전역 IVF + bitmap selector. (κ_p는 "공유 postfilter가 왜 위험한가"의 사후 근거이자, 지역 색인 물질화 우선순위 정렬 신호.)
- h_p = 소프트 → 결합도 라우팅: V_p < τ_V(저결합) → **필터 생략, vector-only**(실측: prefilter가 의미 정답을 깎음); V_p ≥ τ_V(자연결합) → prefilter 병용.
- 임계 동결: τ_V=0.3(3절), τ_amort=predicate별 상각 손익분기의 중앙값(A~1,900/B~2,400, 7.1절 산정), τ_κ=G-κ에서 "공유 postfilter 결손>0.1을 예측하는 κ 컷"으로 데이터에서 결정(사전등록 규칙).

**기준선 (동결):** (S1) 공유 전역 HNSW + postfilter K'=2×(무작위-마스크 벤치마크가 승인하는 naive); (S2) prefilter-always(모든 predicate에 지역 색인 — 소프트·콜드에서 낭비); (S3) vector-only(하드 제약 무시); (S4) 전역 IVF + ID selector; (참고) 오라클-플랜(질의별 사후 최적 계획, 상한). **주장 구조**: CC-FR는 S2의 정확도를 유지하되(핫·결합 질의) S3의 정확도를 회복하고(소프트·저결합, semantic 채점) **더 낮은 총비용(물질화 색인 수 < S2)**으로 — 3축 Pareto 지배 + 소프트·저결합 semantic에서 S2 대비 정확도 우위(진짜 정확도 이득).

**3축 지표.** 정확도: 재현율@10(exact 필터드 GT 대비) + 이중 qrels nDCG@10. 지연: 단일 스레드 p50/p95(라우팅 결정 오버헤드 포함, 무시 가능 예상). 비용: 물질화 지역 색인 수 × 구축 시간 + 메모리, 질의당 상각. 두 실 코퍼스(132K/143K) + 85 tri-source 질의(경성·결합 라벨 보유).

**VLM-QA 종착점 (목표 #3; 두 벽 우회 설계).** "색인을 망가뜨리면 답이 나빠지는가"(지각 벽에 깔림)가 아니라 **"CC-FR가 S1 대비 더 나은 증거를 회수해 더 나은 VLM 답을 내는가"**를, **VLM이 답할 수 있는 질문 대역**에서 측정. 두 조건을 착수 전 검증하는 **이중 조작점검 게이트 G-EP**(두 벽 교훈의 직접 반영):
- (a) 증거 이동: CC-FR vs S1의 top-k 증거 집합이 관련 클립 재현율에서 유의 격차(Δrecall ≥ 사전등록 컷)를 보임 — 계획 선택이 증거를 실제로 움직임.
- (b) 답변 민감: 해당 질문에서 oracle-증거 정확도 − closed-book 정확도 ≥ 0.15(증거 사다리가 입증한 민감 대역; near-chance 질문 배제) — VLM 답이 증거에 반응 가능.
- **(a)∧(b) 통과 시에만** 본 답변 실험 착수. 통과 후: CC-FR-증거 vs S1-증거의 VQA 정확도 짝지은 비교(질문당 paired), 생성기 ≥2종.

**게이트.** G-κ(핵심 실현가능성, 착수 전): Spearman ρ(κ_p, 실측 공유-postfilter 결손) ≥ 0.5(29+25 predicate). 미달 시 라우팅 신호 재설계(설계 사망 아님, 재지정). G-plan: 플래너 결정이 결정론적·기계 재현. G-EP(위, 답변축). 산출물: `paper_assets/20260712_ccfr/`.

**통계.** 3축: predicate 짝지은 Δ(질의 부트스트랩 CI 5,000 + facet-가족 군집), Holm; 오라클-플랜 대비 상대 손실. 답변축: paired 이항(McNemar), 사전등록 SESOI, 검정력.

**검정력.** 검색 3축: predicate 29/25 짝(B-1이 충분 입증). 답변축: 증거 사다리 기울기(~0.5 정확도/증거-재현율 단위)로부터 CC-FR의 Δrecall(예상 +0.1~0.2)이 Δacc +0.05~0.10을 유발 → paired 이항 Δ0.05·불일치율 0.3 검출에 n≈300~400 질문·조건(power 0.8, α 0.05); 파일럿(질문 50)→중단규칙(G-EP (a)∧(b) 미통과 시 재설계, 낭비 회피). VLM 생성 비용은 게이트 통과 후에만.

**중단규칙.** G-κ 미달 → 신호 재설계 후 재프리레지. G-EP (a) 또는 (b) 미통과 → 해당 질문셋 부적합 보고 + 대역 재선정(near-chance 질문셋으로 지각 벽 재현하는 실수 반복 금지). 어느 경우든 정직 보고.

## Amendment 7 판정 (2026-07-12) — CC-FR 착수 전 설계 검토로 KILL (컴퓨트 미집행)

G-κ 게이트(내가 실행) + 3-렌즈 적대 검토(wf_e66b51ef-a05, 18 에이전트)가 독립적으로 동일 결론. **CC-FR은 설계된 형태로 미통과 → 착수하지 않음.** 확정 결함(전부 실측):

- **[BLOCKER] G-κ FAIL**: 질의-무관 κ_offline이 공유-postfilter 결손을 예측 못함(ρ −0.38/−0.05, 부호 반대; κ_offline vs 질의-구동 gt_cluster ρ 0.19–0.25). 기전: κ_offline은 subset 멤버를 유사질의로 써 동일-카메라 배경 유사성 때문에 바닥값에 깔림 — 실제 결손을 만드는 것은 **외부 교차모달 질의**(CLIP-text)로 질의-상대적 성질이라 멤버-질의 프록시가 구조적으로 못 봄. 질의-구동 신호(ρ 0.70–0.90)는 유효하나 순수 오프라인 불가.
- **[BLOCKER] κ 죽으면 CC-FR = 원고 표 13(가이드라인)**: 라우팅이 h_p×V_p 2비트 룩업으로 축소 → "제안 구조" 프레이밍 붕괴, 기존 결과의 룩업일 뿐(κ는 어떤 분기도 구동 안 하는 고아 신호, τ_κ는 어느 분기에도 미참조).
- **[MAJOR] 결합도(V_p)와 군집 분기가 서로 다른 코퍼스·인코더에 산다**: V_p는 tri-source(bge-m3 캡션 3,000, 관련도 있음), 군집/filtered-ANN은 132K/143K(CLIP 프레임, 관련도 없음). **관련도 有 + 스케일 有인 단일 코퍼스가 없어 통합 플래너를 측정 불가.** (이것이 두 벽의 근본 원인과 동일한 결핍.)
- **[MAJOR] 비용 우위는 미측정 f_p(질의 빈도)에 의존**; prefilter-always는 이미 정확도 최적(부분집합 내부 exact)이라 CC-FR은 정확도로 못 이기고 비용으로만 — 그 비용 논거의 근거 데이터가 없음.
- **[MAJOR] G-EP가 두 벽을 못 닫음**(Amd.4의 조건부-지렛대 점검을 빠뜨림), 검정력이 상단 평탄 영역 기울기 무시, null 해석 불가(TOST/SESOI 미고정), 미선언 임계 다수.

**정직한 귀결.** 현 자산으로는 "우리만의 구조"가 성립하지 않는다 — 아이디어가 나빠서가 아니라 (i) 배포 가능한 군집 신호가 CLIP에 존재하지 않고(모달리티 갭), (ii) **관련도 라벨 + 스케일을 동시에 가진 코퍼스가 없기** 때문. **논문의 방어 가능한 기여는 비순환 워크로드 프로토콜 + 기전 발견 + 가이드라인(Framing A/B)에 머문다.** 신규 구조와 목표 #3은 **같은 결핍(스케일 코퍼스 + 관련도 + 답변 가능 질문)** 을 선결 조건으로 공유한다. 잔존 가능성(축소): 질의-구동 군집 신호로 "지역 색인 선택적 물질화(비용)"만 index 코퍼스에서 측정 — 비용-only·워크로드-조건화이며 별도 재프리레지·재검토 필요. 이 결정은 PI 몫.

## Amendment 8 (2026-07-13) — P8: 색인→답변 확증 실험 (구조→양성-재현율→VLM-QA 매개)

**동기(목표 #3 긍정 입증).** 두 벽은 (매개변수 벽) 1K에서 색인이 증거를 못 움직임 + (지각 벽) Qwen2.5-VL이 준-우연이라 답이 못 반응, 때문이었다. P1이 둘 다 해제: (지각) InternVL3+well-posed 질문 균형 0.72 판별; (조건 b) oracle 0.726 ≫ distractor 0.504 ≈ closed 0.500, gap +0.226 — 답이 *올바른* 증거에만 반응. 남은 것은 **실제 색인·검색 구조가 스케일에서 증거 품질을 움직여 답을 바꾸는지의 확증**이다.

**태스크(비순환·매개 설계, 동결).** 존재 질문을 코퍼스에 던진다: "[predicate 조건]을 만족하는 클립 중 [event]가 보이는 것이 있는가?" (event = well-posed 물체-존재: 버스≥1, 이륜≥2). gold = 주석 채널 진실(해당 predicate 부분집합에 양성 클립 존재 여부). 시스템은 구조 X로 top-k 클립을 회수하고, InternVL3이 회수된 top-k 프레임을 보고 이진 답. **답의 정오는 "양성 클립이 top-k에 회수됐는가"에 달림** — 색인 구조가 통제하는 바로 그 양. 무관 클립만 보면 "no"(P1 distractor≈closed 확인) → 비순환.

**H8(가설).** 답변 정확도는 회수된 **양성-클립 재현율(mediator)** 의 단조 함수이고, 색인 구조 X의 답변 효과는 이 매개변수를 **통해서만** 발생한다(완전 매개). 예측: 구조들이 양성-재현율에서 스프레드를 만드는 스케일(143K)·well-posed·유능 VLM 체제에서 답변 정확도가 구조별로 갈리며, 양성-재현율 통제 시 구조의 잔여 답변 효과는 소멸.

**설명력(mediation, 명시).** 세 검정: (i) X→mediator: 구조가 양성-재현율을 움직임(조작점검; **선행 filtered-ANN에서 이미 실측: prefilter-HNSW 0.98 vs postfilter/single-stage 0.24–0.50 vs IVF-PQ 저재현율 — 스프레드 大**); (ii) mediator→답변: 양성-재현율↑ → 답변↑(조건 b 실증); (iii) 매개: X의 답변 효과가 mediator로 흡수(부트스트랩 매개 비율). 결론 형태: **"색인 구조는 관련 증거의 재현율을 통해서만 답변에 영향한다 — 그 재현율을 움직이는 체제(스케일·군집 predicate)에서만 구조 선택이 답을 바꾼다."** 이는 효과가 아니라 *기전*을 보고한다.

**독창성(선행 대비, 재확인).** (a) 필터드-ANN/벡터DB 문헌[1-9]은 재현율·지연에서 멈추고 **다운스트림 VLM 답변으로의 전파를 측정하지 않는다**; (b) RAG/VLM-QA[10-14]는 검색을 쓰나 **색인 구조(Flat/HNSW/IVF-PQ/필터 계획)를 조작 변수로 격리하지 않고** 매개도 측정 안 함; (c) 감시 VALU/UCA/ForeSea/UrBench[15-18]는 **모델**을 벤치마크(구조 아님). 따라서 "저장·색인·검색 **구조** 선택이 VLM-QA 정확도로 전파되는가를 매개변수 격리로 확증"은 **선행에 없는 신규 측정**이며, 본 연구의 filtered-ANN 발견(군집 predicate가 공유 색인 재현율을 무너뜨림)을 **답변까지** 연결하는 유일한 실험이다 — 목표 #3/RQ-M의 핵심.

**구조 X (증거-품질 조작, 동결).** oracle(양성 프레임; 상한) / dense-B2(무필터 CLIP top-k) / prefilter-HNSW(고재현율) / postfilter-K'(중) / single-stage-IVF(하) / IVF-PQ 열화(저) / distractor(무관; 하한) / closed(무증거). 회수 top-k=6 프레임(2 클립×3), InternVL3 답변.

**매개변수·지표.** mediator = 양성-클립 재현율@k (top-k에 양성 클립 포함 여부/비율). 답변 = 균형 정확도(gold yes/no 균형). 지연·비용은 7절 값 인용(구조별). 매개 = 부트스트랩 간접효과 비율.

**검정력·SESOI.** SESOI = 구조 간 답변 균형정확도 차 **0.10**(조건 b가 0.22 스팬을 입증했으므로 0.10은 검출 의미 有). paired McNemar(구조쌍), 불일치율 ~0.30 가정 → Δ0.10·power 0.8·α 0.05에 **n≈200 아이템**(P1 180 확장; qtype 균형). 매개 검정 부트스트랩 5,000.

**게이트·중단규칙.** G-manip(확증 전): 구조들이 양성-재현율에서 사전등록 스프레드(최고−최저 ≥ 0.30) — 미달 시 매개변수 벽 재발로 판정·중단(현 filtered-ANN 데이터로 사전 충족 예상). G-b(조건 b): 이미 통과(P1). 확증은 두 게이트 통과 후. **중단규칙**: 매개 조작이 성립하나 답변이 mediator에 반응 안 하면(지각 벽 재발) → 정직한 부정 결과로 보고(이번엔 near-chance 혼입 없어 해석 가능). null도 3-결과(우위/등가 TOST SESOI 0.05/열위)로 판정. 산출물 `paper_assets/20260713_index_answer/`.

## Amendment 8 판정 (2026-07-13) — P8 착수 전 설계 검토로 KILL (컴퓨트 미집행)

3-렌즈 적대 검토(wf_3c7bfa50-9de, 16 에이전트, **12/13 확정**)가 P8의 핵심 전제를 **P1 데이터 자체로 반증**. 착수하지 않음.

- **[BLOCKER] 비순환 전제가 거짓**: "무관 클립만 보면 no"라 했으나 condb 실측 — distractor에서 InternVL3의 P(yes)=0.64가 gold와 **무관**(gold=yes 0.647 / gold=no 0.638, 판별 ~0). VLM은 회수 프레임에 객체가 있으면 "yes"하는 **내용-유발 yes-편향**. "distractor≈closed(0.504≈0.500)"는 **상반된 편향(closed 순수 no 0%, distractor yes 64%)의 우연한 상쇄**일 뿐. → 존재 질문의 답이 "올바른 클립 회수"를 검사하지 못함.
- **[BLOCKER] H8 완전-매개 구조적 불가**: 양성-재현율은 gold=yes에서만 정의(gold=no엔 양성 클립 부재→매개변수 부재)인데 답은 구조별로 변함(yes-편향 직접 경로). 균형 정확도로 풀링하면 이 비매개 no-반쪽 효과가 상쇄돼 **가짜 "완전 매개"** 산출. gold=yes 반쪽에선 매개가 **동어반복**(재현율↑→양성 봄→yes).
- **[MAJOR] G-manip 오인용**: 스프레드 0.48을 620의 *일반 질의 exact-NN 재현율*에서 가져왔으나, 이는 존재-질문의 *양성-클립 재현율@6*과 **다른 양** — 매개 조작이 실제 태스크에서 미확립.
- **[MAJOR] 통계**: n≈200이 불일치율 0.30 가정인데 P1은 0.43–0.7; 3-결과 null의 TOST ±0.05 도달 불가; McNemar(풀 정오)≠균형정확도 대비; 28쌍 Holm 미지정; 아이템·predicate 군집 무시.
- **[MAJOR] 독창성 과대**: "구조→VLM답변 전파 측정 전무"는 축-수준 절대 주장이라 과대 — 더 좁은 정직 주장만 생존.

**정직한 귀결.** 존재 질문 + 이진 답 + 유능 VLM 조합은 **VLM yes-편향**으로 근본 오염되어, "구조→답변"이 동어반복(gold=yes)이거나 비매개(gold=no)가 된다. 세 번째 설계(CC-FR·P8) kill — **목표 #3의 깨끗한 긍정 확증이 진짜로 어려움**을 반복 확인. 남는 정직한 기여 후보: 두 벽 + P1(지각 벽 부분 해제) + yes-편향 = **"구조가 답변에 전파되는지가 좁은 체제(스케일×VLM 능력×태스크 비오염)에 갇혀 있음"의 경계 규명** 자체가 신규·설명적 결과. 대안(P8b): MC/값 질문(yes-편향 회피) + per-target 값 답 — 별도 프리레지·재검토 필요, 지각/동어반복 위험 잔존.

## Amendment 9 (2026-07-13) — P9: 그래프-구조(KG-as-index) 검색을 비순환 워크로드에 추가

**동기.** 본 연구는 저장·색인·검색 **구조**를 비교하나 지금까지 전부 벡터-유사도+메타데이터-필터 계열(전략6·계획3·색인4·엔진4)이다. 활발한 그래프 계열(GraphRAG/KG)이 빠져 "왜 벡터 구조만?"의 여지가 있다. 본 Amendment는 **경량 KG-as-index**를 하나의 추가 구조로 같은 비순환 워크로드 위에 올려, ① 비순환성을 그래프 구축까지 확장(A6-KG)하고 ② **질의 유형 × 구조** 승패를 규명해 "질의 유형→최적 구조" 가이드라인을 만든다. 주제 불변(구조 비교의 계열 추가; 재프레이밍 아님).

**구조 정의(KG-as-index, 동결).** tri-source 522(캡션 3,000·질의·이중 정답 보유 워크로드) 위에 그래프 G 구축:
- 노드: 클립 3,000 + **센서-facet 값 노드**(time_of_day/hour/신호위상/밀도분위) + **캡션-엔티티 노드**(버스·차·트럭·이륜·보행자 등 동결 렉시콘으로 캡션에서 추출).
- 엣지(**소스 분리 필수**): 클립→센서-facet(센서 채널, 카메라 10) · 클립→캡션-엔티티(문서 채널, 픽셀만 본 캡션). **주석 채널(정답 정의)에서 나온 엣지 0.**
- 검색: 질의(의미 조건 + predicate)→ predicate facet 노드 순회로 후보 클립 ∩ 의미-엔티티 노드 연결 클립, 엣지-가중/엔티티-중첩으로 순위.

**A6-KG 감사(비순환 차단, 동결).** 원 A6를 그래프로 확장: (KG-a) predicate 엣지는 센서 채널만; (KG-b) 의미 엣지는 문서 채널(캡션 렉시콘)만; (KG-c) **주석 채널 유래 엣지 0**(정답 정의 채널을 구축에서 전면 배제); (KG-d) 정답=주석 채널로 유지·전 엣지와 소스 분리; (KG-e) 주석 정의 노드(is_parked·is_stopped·차량수 등) 금지, 캡션 엔티티만; (KG-f) prefilter 우위 비보장 부호 지표 유지. + **엣지-출처 표**(엣지 유형→소스 채널→생산자) 기계 감사. 이로써 "비순환 프로토콜을 그래프 백엔드까지 확장"이 방법론 각도가 된다.

**질의 유형(기계 생성, 동결).** (a) **단순**: predicate 1 + 의미 조건 1(현 85질의 계열); (b) **합성 다중-홉**: predicate ≥2 접속 + 의미 조건 1(예: 오전 ∧ 황색 ∧ 고밀도 ∧ 버스). 5 predicate × 5 정답정의의 접속 교차곱에서 strict 양성 ≥5 규칙으로 채택. 이중 정답(strict/semantic).

**기준선(구조 비교).** KG-as-index vs B4(prefilter+vector) vs B2(dense) vs B0(metadata-only) — 동일 워크로드·이중 정답.

**가설(H-KG, 정직).** 단순 질의: KG ≈ 벡터+필터(사전등록 등가 TOST SESOI 0.05). 합성 다중-홉: KG가 다관계를 순회로 조합해 dense 유사도 희석 없이 우위 — **또는** 우위 없음(구조 선택이 질의 유형 불변). 어느 쪽이든 정직 보고. 주의: strict 채점에서 predicate는 KG·prefilter 모두 정확 강제라 차이는 **의미 연결(캡션-엔티티 순회 vs dense)**·합성 조합 효율에서만 발생 — 이를 명시.

**지표·통계.** 질의 유형별 nDCG@10/재현율(이중 정답), 질의별 Δ(KG−벡터) 질의 부트스트랩 + 쌍 군집; Holm(유형×구조쌍). 지연: 그래프 순회 vs 벡터 검색(엔진 내 상대; 절대 비교 금지). 비용: 그래프 구축·크기.

**게이트·중단규칙.** G-KG-audit(착수 전): A6-KG 전 어서션 통과·엣지 출처표 기계 검증·주석 유래 엣지 0 — 미달 시 순환 재발로 판정·중단. G-construct: 결정론적 구축·노드/엣지 수 로그. G-query: 합성 질의 strict 양성 ≥5, 미달 시(3K 소규모라 합성 양성 희소 가능) 저검정력 보고. **중단**: KG 우위 미검출도 정직 결과(구조 선택 질의-유형 불변). 순환성 위반 발견 시 즉시 중단. 산출물 `paper_assets/20260713_kg/`.

## Amendment 9 판정 (2026-07-13) — P9 "KG 우위" 가지 KILL (구축 전, 3-렌즈 적대검토 3 BLOCKER 생존)

**절차.** 구축·GPU 착수 전 3-렌즈(순환성-A6KG / 질의유형-구조 공정성 / 구축-정직성) 적대 검토 → BLOCKER·MAJOR는 반증(verify) 파이프라인. 17 에이전트. **BLOCKER 3 전부 refuted=false(생존), MAJOR 7 생존.** 산출물: `subagents/workflows/wf_b364e1b8-b13/journal.jsonl`.

**판정: H-KG의 "KG 우위(합성 다중-홉)" 가지 KILL — 컴퓨트 전에 이미 아는 붕괴.** CC-FR(Amd.7 고아 신호)·P8(Amd.8 동어반복)과 동일 실패류. 이유 세 겹(전부 실측 확증):

1. **세 번째 신호 채널이 없음(구조적 강제).** tri-source는 정확히 3 채널(센서=필터, 주석=정답, VLM캡션=문서; `A6_trisource_audit.json`). A6-KG가 주석-채널 엣지=0을 강제하므로 KG 엣지 = 센서-facet(=B0/B4) ∪ 캡션-엔티티(=B1/B2). **네 번째 소스가 데이터에 없어** 새 신호가 나올 곳이 없다. 경험이 아니라 구성상 강제.
2. **predicate 축 ≡ B4(정의상).** "합성 다중-홉"을 predicate ≥2 접속에 둠 → 센서-facet 집합 교차 = B4 prefilter와 동일(설계 자백 "predicate는 KG·prefilter 모두 정확 강제"). strict에서 KG=B4 by construction; 유일 잔차(의미 조건 1)는 단순·합성 공통이라 질의-유형 의존 우위를 못 만든다. 진짜 그래프-우위 자리(다중 의미 조건 or 관계형 2-홉)를 설계가 테스트 안 함.
3. **캡션-엔티티 채널은 실측 near-chance.** 3,000 캡션 직접 측정: 과잉 언급(bus 97.4%·car 99%·truck 87%·two-wheeler 86%·pedestrian 98%) + 대량 부정(parked 언급의 89%·two-wheeler 76%·bus 35%가 부정문 "There are no buses…"). P(gold|엔티티 present) ≈ 기저율(bus 0.114 vs 0.082). = 논문이 이미 보고한 B1 BM25 바닥(strict 0.017). 유일한 비-정의적 KG 신호가 죽은 채널.

**⇒ KG = B0/B4(센서) ∪ B1/B2(캡션) 재조합, 제3 신호 없음. strict에서 B4와 동률/열세, semantic에서 B2와 동률/열세. "합성 우위" 기전 부재.**

**정직-함정 정정(중요, verify가 발견).** 엔티티-중첩을 **필터 안에서** 계산하면 BM25 전-코퍼스 0.017이 아니라 ~0.232 strict(B0 0.218·B2/B4 위)이다 — BM25 0.017은 전-코퍼스 어휘 희석 아티팩트. 즉 KG가 B4를 **이길 수도** 있으나 **틀린 이유로**(dense가 메타데이터 바닥 아래라서지 KG가 의미력이 있어서가 아님). ⇒ 등가·우위 어느 주장도 **B0(0.218)를 SESOI만큼 상회**를 선결로 요구하는 G-KG-floor 게이트 필요(TOST 바닥-효과 함정 = P8 재발 방지). parked는 affirmative 추출조차 lift≈0 → 바닥 엔티티로 사전 라벨.

**추가 강제(생존 MAJOR).** (a) 렉시콘 추출에 **부정-인지(affirmative-only, 문장 스코프)** 규칙 sha-동결 + 엔티티-노드 차수>40% 코퍼스면 G-construct reject; (b) A6-KG에 **KG-g**(렉시콘은 공개 질의-의미어에서만 도출, gold 참조 전 동결, gold-전용 필드/임계 미개입 기계검사)·**KG-h**(부정/극성 규칙 사전 동결) 추가 — 순환성-누출은 없으나(affirmative precision 2~16%≪1) lexicon·polarity가 gold-정보 forking-path DOF; (c) 검색 랭킹 함수(hard/soft 교차·엣지가중·깊이·결합·타이브레이크) **미동결 → E-1 LOCK처럼 diff-잠금** 선결; (d) 합성 확증은 독립 facet-family-쌍 **6개뿐**(hour는 time_of_day에 nested) → 2-홉=확증/3-홉=탐색, 쌍-군집 부트스트랩 1차 CI(§6 교훈); (e) 동기 재서술: §2.1이 이미 그래프-ANN(Filtered-DiskANN/VBASE/Milvus/ACORN) 다룸 → "그래프 계열 빠짐"은 과장, 진짜 신규 단위는 **entity/KG 구축의 A6-KG 비순환 감사(방법론)** + 정직한 경계/음성 결과.

**생존하는 방어 가능 코어(P9에서 살릴 것).** (1) **A6-KG 감사** = 비순환 프로토콜을 그래프 백엔드로 확장(엣지-출처 표·주석엣지=0 기계검증) — 진짜 방법론 기여; (2) KG를 **정직하게 라벨된 구조 baseline**(B0/B4∪B1 재조합, ≈B4 strict/≈B2 semantic, 붕괴를 앞세워 명시); (3) **경계/음성 결과**: "캡션 기반 멀티모달 코퍼스에서 entity-KG 검색은 sparse-entity-match로 붕괴하고, 캡션 엔티티의 과잉언급+부정 때문에 dense에 지배당한다 — 그래프 계열이 새 품질 축을 더하지 않는다." 프로젝트 정직 바에 부합, 경계 발견으로 게재 가능.

**verify가 발굴한 유일한 진짜 그래프 기전(Path B 후보, PI 결정 대상).** `intersection_id`는 facet_role='context' 노드, **3000/3000 채워짐, 63 값(~48 클립/교차로)**. 관계형 2-홉 질의 "X를 보인 클립과 **같은 교차로**의 클립"(clip→intersection→other-clips)은 **B4가 구조적으로 표현 불가**(per-clip 'intersection_has_bus' 필드를 materialize하려면 파생 필요) → KG가 native로 표현. gold 비퇴화: dense_frame 16%·multiple_buses 59%·parked_vehicle 57%; **퇴화(제외): stopped_vehicles 100%·two_plus_bikes 90%**. 단 seed는 여전히 noisy 캡션 채널에 의존 + 새 relevance 정의 → 자체 A6-KG 감사 + 재검토 필요. = 다-일 재설계.

**결론.** P9는 CC-FR/P8처럼 "이기는 구조"로는 KILL(컴퓨트 전 확정). 남은 선택은 PI 몫: **(A)** 정직 경계+A6-KG 방법론을 지금 확정(저비용 CPU 측정으로 붕괴를 실측 영수증화, GPU 불필요) vs **(B)** intersection_id 관계형 2-홉으로 재설계해 진짜 양성 그래프 발견을 추격(재검토 선결). **어느 경우든 원 설계의 predicate-접속 합성 우위 가지는 폐기.**
