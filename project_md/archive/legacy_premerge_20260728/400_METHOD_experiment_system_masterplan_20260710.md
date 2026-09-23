# 실험 체계 완성 마스터플랜 — Multimodal Urban Surveillance VLM-QA (주제 고정)

> 주제(LOCKED): "자연어 질의 + 메타데이터(센서/시공간) 조건이 함께 주어질 때, 어떤 저장·색인·검색 구조가 VLM 기반 QA를 더 정확·빠르게·저비용으로 지원하는가 — 이미지/영상 + 사건보고서 + 센서/시공간 메타데이터 결합."
> 본 문서는 논문 집필 전에 완성해야 할 **실험 기반 청사진**이다. 주장을 줄이지 않고, 그 주장을 유효하게 입증할 실험 체계를 완성하는 것이 목표다. 모든 경로·수치는 2026-07-10 디스크 실측으로 검증했다.

---

## 0. 한 줄 결론 — 지금 무엇이 부족하고 무엇을 하면 '완성'인가

**부족한 것은 데이터가 아니라 (1) 비순환(non-circular) 워크로드, (2) 실현된 센서/시공간 모달리티, (3) 3축(정확·지연·비용) 계측, 이 세 가지를 하나의 감사 가능한 실험 체계로 봉합하는 작업이다.** 현재 원고의 검색 헤드라인(표6/7/16)은 `metadata_filter ⊆ qrel_filter` 구조 때문에 `B4(prefilter) ≥ B2(vector)`가 코드로 보장되는 순환 결함(F1/F2/F4)을 안고 있고, 색인 3축 결과(index_benchmark)와 답변계층(6.8)·선택>축적(6.13)은 견고하지만 서로 접합되지 않은 채 흩어져 있으며, 센서/시공간 모달리티(F8)는 미실현, 지연·비용(F7)은 원고가 명시 철회한 상태다.

**'완성'의 정의:** 교차로신호체계(522) 실센서 CSV(TL_1/TL_2, 이미 디스크 상 plain-zip)를 QA 정답과 통계적으로 독립인 metadata predicate로 materialize하여 F1/F2/F4를 데이터 수준에서 붕괴시키고 → 그 위에서 검색구조 비교(B0–B5)·filtered-ANN·색인 3축(recall×latency×index_mb)·답변계층을 재측정하고 → 6.8/6.13을 diff-proven 불변 앵커로 접합하고 → 지향 3-RQ의 모든 셀이 non-circular·CI 붙은 실험 ≥1개로 채워졌음을 자동 검증기(per-query 재집계)가 PASS로 확인하면, 그때 논문 집필에 착수할 수 있다. **주제실현(센서 결합)과 결함해소(순환 제거)가 동일 작업**이라는 것이 이 계획의 중심 지렛대다.

**세 개의 트립와이어가 헤드라인의 존재 여부를 결정하므로 GPU를 쓰기 전에 CPU-only로 먼저 통과시켜야 한다:** ① TS_3(75GB 솔리드 7z) 블록정렬 추출 실비용, ② 센서 predicate ⟂ relevance 독립성(신호위상 다양성 포함), ③ human-gold κ·검정력. 이 셋 중 하나라도 막히면 시각 헤드라인은 정직한 대안 경로(§7 No-Go 분기)로 후퇴하되 **주제는 축소하지 않는다.**

---

## 1. 데이터셋 확정 판정 (사용자 질문 직답)

### 1.1 추가 신규 확보가 필요한가? → **NO (단호히).**

**필요한 것은 '신규 획득'이 아니라 'materialization + 비순환 통합'이다.** 디스크 실측 근거:

| 원천 | 상태(실측) | 판정 |
|---|---|---|
| 교차로신호체계 TL_1.통과차량.zip | **plain Zip 14.96MB, 29,234 CSV, 63 교차로** — `file`=Zip, GPU-0 즉시 파싱 | 확보완료·미가공 |
| 교차로신호체계 TL_2.보행량.zip | **plain Zip 9.65MB, 29,234 CSV** (pedestrian/bicycle/direction/TOD) | 확보완료·미가공 |
| TL_3/4/5 (도로차량/bbox/큐보이드 라벨) | Zip 17.6/17.9/115MB | 확보완료(옵션) |
| TS_3.도로차량(영상 원천) | **75.18GB, 실측 `file`=7-zip v0.4 (솔리드) — .zip 확장자지만 7z** | 확보완료·고비용 미가공 |
| TS_1/TS_2 통과차량·보행량 원천 | **각 22바이트 (미개방 placeholder)** | 미개방·**불필요**(라벨 CSV로 충분) |
| sinnaedoro corpus_real | **132,521×512 CLIP + frame_index[location,camera,date,time] 실측 완료** | 확보완료·가공완료 |
| MAIN QA (vru/다각도/지능형/이상) bge-m3 임베딩 | **7000/244, 36000/4572, 807/133, 5904/424 실측** | 확보완료·가공완료 |
| VLM/LLM 가중치 | **/hdd2/huggingface_cache/hub: Qwen2.5-VL-7B, Qwen2-VL-7B, InternVL3-8B-hf, Idefics2-8b, Qwen2.5-7B, Llama-3-8B, bge-reranker-v2-m3, Qwen3-Reranker-4B, NV-Embed-v2 모두 실재** | 확보완료 |

결론: **모든 원천이 디스크에 실재한다. 신규 외부 획득은 미개방 TS_1/TS_2 원천 수치뿐이며, 이는 라벨 CSV(TL_1/TL_2)로 대체 가능하므로 필요 없다.** 남은 작업은 전부 unzip/parse/extract/join과 워크로드 재설계다.

### 1.2 각 데이터셋의 확정 역할 + materialization 잔여작업

| 데이터셋 | 확정 역할 | Materialization 잔여작업 |
|---|---|---|
| **교차로신호체계(522)** | **SENSOR / true-multimodal 결합 HEADLINE** (RQ-M 핵심, F1/F2/F4/F8 동시 파괴) | TL_1/TL_2 CSV→센서 facet parquet(CPU 수십분); 캐노니컬(문서=정성 서술)·비순환 질의·QA gold; **시각(TS_3)은 PoC 후 층화 subset만**(§7 T1) |
| **VRU accident** | **MAIN — 답변계층(6.8) anchor + 순환 헤드라인 재측정 대조** | 어댑터 F2 분기 삭제 후 재빌드; 구(舊)vs신 collapse 대조표 |
| **다각도 CCTV** | **MAIN — 선택>축적(6.13) anchor** | KEEP(불변). `canonical_stratified_event_split_5` 실재 확인 |
| **지능형 CCTV** | **MAIN — 누수독립 재측정 anchor + reranker** | 어댑터 수리 재측정 |
| **시내도로(sinnaedoro)** | **INDEX-SCALE 3축 + 실-시공간 predicate filtered-ANN** | frame_index[location/camera/date/time] 실재 → 실-predicate 즉시 산출 |
| **이상행동 CCTV** | **일반화(schema portability)** — 도시교통 성능 일반화 금지, 이식성만 | 기존 재사용 |
| **CityFlow-NL** | **일반화(international, 후순위)** — DB 구조비교로만, leaderboard 주장 금지 | annotation canonical만 존재, visual 미추출(후속) |

### 1.3 센서/시공간(교차로신호체계) 실현 가능성 판정 + 리스크

**판정: 실현 가능 — 단, 2단 분리.**

- **텍스트/센서-predicate/QA 핵심경로 = 즉시 실현(GPU<1hr).** TL_1/TL_2가 plain-zip임이 실측 확인됐다. CSV 스키마(검증): TL_1 = `video_file, video_id, signal_info.movement, departure_time, car_type, lane, car_info.movement`; TL_2 = `pedestrian_info.{pedestrian_type, attribute, TOD, direction}`. `video_id`=`101010_2021090813495200`(교차로ID + YYYYMMDDHHMMSS). 여기서 차량대수·차종(car/small_truck)·차로(1–7)·보행/자전거·시각·요일·교차로ID predicate를 CSV 집계만으로 산출 가능. **이 predicate는 QA 정답과 원천 독립 → F1/F4 붕괴의 지렛대.**
- **시각(영상) 경로 = TS_3 솔리드 7z 롱폴에 게이팅.** TS_3는 75.18GB 솔리드 7z이므로 층화 subset 추출이 최악 전량 디코드에 수렴할 수 있다(§7 T1). **py7zr 1.1.3은 kiise-vlmdb env에 이미 설치돼 있음**(설계의 "py7zr 부재" 진단은 stale). 블록정렬 단일패스 PoC로 실비용을 재기 전엔 시각 subset N을 확정하지 않는다.

**리스크 3종:**
1. **신호위상 predicate 희소성 (트립와이어 T2).** 실측: 표본 클립 `101010_2021090813495200.csv`의 `signal_info.movement`와 `car_info.movement`가 **전 행 't'**. 신호위상(좌회전 'l' 등) predicate가 selectivity 범위를 못 낼 위험 → Phase 0에서 TL_1 **전수** 카디널리티를 CPU로 먼저 확인. 희소하면 차종·차로·차량밀도·시각 predicate로 headline 구성(주제 축소 아님, predicate 선택 문제).
2. **미개방 raw 공백.** TS_1/TS_2 = 22바이트 placeholder. 라벨 CSV만으로 predicate 구성되므로 **무영향**(검증됨).
3. **영상원천 처리비용.** TS_3 솔리드 디코드 40–76GB 순차 I/O 롱폴. 완화: 블록정렬 추출 + A/C/D 공유(중복추출 금지) + 시각 실패 시 frame-free 센서·텍스트 경로로 방어선 유지.

---

## 2. 완성해야 할 실험 체계 (pillar별 확정 build 순서)

> **거버넌스 결정 G1 (rq-coverage gap4 반영): Pillar A와 Pillar C는 동일 522 원천을 이중 빌드하므로 하나의 canonical로 병합한다.** 단일 경로 = 어댑터 `src/vlmdb_workload/adapters/aihub_522_intersection.py`, 산출 `Datasets/processed/aihub_522_intersection/<ver>/`. Pillar A의 비순환 감사·질의저작·relevance 판정은 이 canonical을 **소비하는 스텝**으로 재배치한다. `processed/intersection_signal/` 별도 빌드는 폐기.
> **거버넌스 결정 G2 (residual gap7 반영): Pillar B의 B5(522 센서 predicate를 sinnaedoro에 조인) = No-Go 확정.** 실측: sinnaedoro namespace(범박터널, cam BC100…, 2020-10)와 522 namespace(교차로 101010, 2021-09)는 완전 disjoint. 센서-predicate 헤드라인은 Pillar C 자체 코퍼스에서만, MAIN 일반화는 sinnaedoro **자체** 시공간 predicate(location/camera/date/time, 실재 확인)로만 한정.

### Pillar A — 비순환 워크로드 (해소: F1/F2/F4)
- **build_steps (병합 후 확정):**
  - A1(=C1과 통합) TL_1/TL_2 CSV→클립당 센서 facet parquet. **P계열(predicate, exogenous)**=교차로ID·time_of_day·요일·주말·신호위상존재(전수 검증 후) / **R계열(relevance)**=차량총수·차종·좌회전·보행량 분위수. `facet_source='sensor_csv'`. [NEW `scripts/build_intersection_signal_sensors.py`; zip 스트리밍은 `build_sinnaedoro_visual.py` 패턴 재사용]
  - A3 캡션 코퍼스: Qwen2.5-VL로 키프레임→**dense caption 단일 doc_type만**(정성 서술; **정답라벨 재진술 doc 절대 금지, verbatim 수치 금지 — D2 gate**). [NEW `scripts/build_intersection_captions.py`; `run_multiview_answer_vlm.py` VLM 인프라 재사용]
  - A4 비순환 질의셋: 의미 need만 담는 NL 질의 K≈250(사람검수) + gold 소표본(**κ가 아닌 검정력 기준으로 크기 확정** — Phase 0 파일럿). `metadata_filter=P계열`, `qrel_filter=R/semantic계열`, **두 컬럼셋 disjoint 스키마 강제.** [NEW `scripts/build_intersection_queries.py`; label_pilot 패턴 재사용]
  - A5 은(silver) relevance: InternVL3(캡셔너 Qwen2.5-VL과 **다른 패밀리**)가 **프레임만** 보고 판정(색인 캡션·CSV 미열람). **+ 캡션무관 CLIP/SigLIP 대조 arm 필수**(residual gap3: VLM 공유편향 격리). [NEW `scripts/judge_relevance_vlm.py`]
  - A6 비순환 감사 CI 어서션: (1) `keys(metadata_filter) ∩ keys(qrel_filter)=∅`, (2) `doc_type=='vqa_facet_statement'` 0건, (3) `facet_source=='sensor_csv'`, (4) predicate↔relevance Cramér's V/MI가 1.0 아님을 문서화, (5) B4−B2 Δrecall 부호분포에 음수 포함. **실패 시 빌드 중단.** [NEW `scripts/audit_workload_noncircularity.py`; `audit_experiment_control_factors.py` 패턴]
  - A7 텍스트 임베딩(bge-m3 + e5-large-v2). [REUSE `build_text_embeddings.py` 무수정]
  - A8 비순환 워크로드 위 B0–B5 + RRF + reranker 재측정 + filtered-ANN을 실 predicate로. [REUSE `run_retrieval_baselines.py`,`run_reranker_selection.py`; PATCH `retrieval.py`(predicate-conditioned metric), `run_filtered_ann_benchmark.py`(random→sensor mask)]
  - A9 구(舊) VRU/AIHub 어댑터 수리: `vru_accident.py` `_build_documents`의 facet_docs 분기 삭제(F2), qrel_filter를 의미축만으로 축소(F1/F4), 재빌드해 MRR/nDCG=1.0000 붕괴 대조표. [PATCH `src/vlmdb_workload/adapters/vru_accident.py`(+`aihub_intelligent_cctv.py`)]
- **산출:** non-circular canonical, `qrels.tsv`(독립판정), `audit_report.md`, `independence_matrix.csv`, `b4_minus_b2_sign.csv`, `old_vs_new_collapse.csv`
- **통제:** predicate=sensor_csv only; positives=predicate 무관 독립판정; 캡셔너≠판정기; 판정기 프레임만; **collapse 표는 human-gold nDCG 보존 동반 제시**(residual gap6).

### Pillar B — 저장·색인 (해소: F6, 부분 F1/F4)
- **build_steps:**
  - B1 MAIN QA 코퍼스 전부에 Flat/IVF-Flat/HNSW/IVF-PQ × recall@10·p50/p95/p99·index_mb·build_s. 소형 N에서 ANN≈exact 명시. [REUSE `run_index_structure_benchmark.py` 무수정 + wrapper]
  - B2 filtered-ANN을 sinnaedoro 실-시공간 predicate(location/camera/hour/date, **실재 확인**)로 재구성 + single_stage(IVF-Flat + IDSelectorBatch) method 추가. [NEW `scripts/run_filtered_ann_real_predicate.py`(fork)]
  - B3 pgvector 실 ANN 색인: `CREATE INDEX ... USING hnsw/ivfflat`, ef_search/probes/lists sweep, recall(vs pgvector-exact)·p50/p95·pg_relation_size. [EXTEND `run_pgvector_retrieval.py`; 컨테이너 kiise-vlmdb-pgvector :5433]
  - B4 **[헤드라인 연결]** 색인 근사→답변정확도: `run_rag_vqa.py`에 `--index{exact|hnsw:ef|ivfflat:nprobe|ivfpq:m}` 추가, 고정 LLM으로 recall↔accuracy 곡선. **코퍼스 고정 + gold-bearing-doc 회수율 분리 측정 + 드롭 문서 gold/distractor 로깅**(residual gap4). [EXTEND `run_rag_vqa.py` + `run_significance_analysis.py`]
  - ~~B5~~ **No-Go(G2)** — 삭제. 센서-predicate 색인은 Pillar C 코퍼스로 이관.
  - B6 §Storage-Indexing 원고 자산화(4 그림/표). [EXTEND `generate_retrieval_paper_assets.py`]
- **산출:** `paper_assets/storage_indexing/index_tradeoff_all.csv`, `filtered_ann_real.csv`, pgvector sweep, `recall_accuracy_curve.csv`
- **통제:** index.search만 격리·single-thread·warmup 폐기; recall=index fidelity(정답라벨 분리); 소형 N ANN≈exact 명시, crossover는 synthetic_aug로만 주장(honest framing, rq-coverage gap6).

### Pillar C — 센서/시공간 (해소: F1/F2/F4/F8) — **A와 병합된 canonical의 소유 pillar**
- **build_steps:** C1(=A1) 센서 raw parquet → C2 canonical(**문서=정성 센서 서사, verbatim 수치 금지**) → C3 프로그램검증 QA(count/argmax/threshold; **정답 수치가 어떤 doc에도 verbatim/근사변형 미등장 — 빌드 어서션**) → C4 행-정렬 attribute table + 명명 predicate×실selectivity → C5 TS_3 시각 subset(블록정렬, **PoC 후**) → C6 실-predicate filtered-ANN → C7 B0–B5 + 답변계층 → C8 독립성·누수 감사(MI/χ², B4<B2 실증, leakage_scan **문자열+단위변형+부분합 커버**). [NEW `aihub_522_intersection.py`, `build_intersection_signal_canonical.py`, `build_intersection_signal_qa.py`, `build_real_predicate_attributes.py`, `prepare_intersection_video_subset.py`, `run_filtered_ann_benchmark_real.py`; REUSE `retrieval.py`, `build_text_embeddings.py`, `extract_keyframes.py`]
- **산출:** 522 canonical/QA/attributes/predicates.json, `independence_report.md`, `f1_break_cases.csv`, `leakage_scan.json`, retrieval/rag_vqa 결과
- **통제(추가/강화):** predicate⟂relevance를 **가정 아닌 데이터로 검증**(Phase 0 tripwire); 결합강도를 **연속 축**으로 'B4이득 vs 결합강도' 곡선 보고(residual gap2 — 저결합만 cherry-pick 금지); 정답=CSV 집계(doc verbatim 부재); exclude=self 계승.

### Pillar D — 영상/시간축 (해소: video-naming, F2-visual/F4) — **OPTIONAL/비차단**
- **build_steps:** D1 조밀 프레임(`extract_keyframes.py`에 fps 옵션 + zip loader) → D2 시간표현 3변형(frame/pooling/segment; [NEW `pool_temporal_embeddings.py`]) → D3 검색품질×밀도 + temporal localization([REUSE `run_image_to_video_retrieval.py`,`evaluate_event_frame_grounding.py`]) → D4 밀도↔색인비용(Pillar B 결합) → D5 filtered-ANN을 sinnaedoro 실 time-of-day predicate로 교체 → D6 video-native VLM reader(**promote-or-limit 최소치: 1–2 VLM×2 frame count**, GPU 절감) → D7 사전등록 승격/한계 판정([REUSE `run_significance_analysis.py`]).
- **산출:** `paper_assets/pillarD/{retrieval_by_density,localization_by_density,index_cost_vs_density,filtered_ann_realpredicate,temporal_reader_vqa,temporal_promotion_verdict}.*`
- **통제:** 검색 pool=전체 clip 균일 dense(evidence-frame 주입 금지→F2); event window=GT로만(retriever 미제공→F1); near-dup 중복제거·holdout; **faiss는 kiise-vlmdb에 실재**(설계의 "어디서도 import 불가" 진단은 **오진** — 실측 faiss 1.14.3 확인).

### Pillar E — 지연·비용 3축 (해소: F7 + 미격리 wall-clock validity)
- **build_steps:** E1 검색계층 latency canonical화(env pin manifest, real vs synthetic_aug 라벨; [REUSE `run_index_structure_benchmark.py`]) → E2 VLM 답변 per-stage 계측(cuda.Event: retrieval_ms/prefill/gen_tokens/gpu_sec; [NEW `instrument_vlm_cost.py`]) → E3 ANN근사→answer 손실(색인만 스왑, **retrieval-민감 층 확보 필수**; [NEW `run_ann_answer_coupling.py`]) → E4 3축 join + Pareto/hypervolume → E5 cost 모델($/1k-query 대리, **절대 $ 비-headline·민감도 band만**).
- **산출:** `experiments_expansion/pillarE/{search_layer,vlm_cost,coupling,pareto,cost}/*`, `paper_assets/figures/fig_three_axis_pareto.png`
- **통제:** faiss threads=1·batch=1·warmup 폐기·taskset/clock pin; **latency 헤드라인을 'filter-plan별 격리 지연(prefilter vs postfilter vs single-stage, 동일 HW/backend)'로 재정의**(rq-coverage gap5, pgvector가 철회한 그 질문에 정직히 답); **3축→2축 붕괴 방지**: answer가 recall에 반응하는 층을 먼저 입증한 뒤에만 3축 headline.

### Pillar F — 통합·거버넌스 (해소: F5/F6/F9/F10 + 완성 보증)
- **build_steps:** F1 RQ 커버리지 매트릭스(project_md 24/30/40/41 + manifest 자동 파싱; [NEW `build_rq_coverage_matrix.py`]) → F2 데이터셋 역할표 → F3 표1-20·그림1-7 keep/재측정/승격/신규/진단격하 ledger → F4 결측·중복 감사(**+'동일 원천 이중 빌드' 탐지 규칙**, rq-coverage gap4) → F5 exit criteria 검증기(**manifest 존재만이 아니라 per-query parquet 재집계로 헤드라인 수치 재계산 대조**; [REUSE `validate_experiment_freeze.py`,`audit_true_multimodal_pipeline.py`]) → F6 서사 정합성 가드(원고 grep vs ledger).
- **산출:** `paper_assets/integration_matrix/{rq_coverage_matrix,dataset_roles,keep_discard_ledger,gap_dup_report}.*`, `paper_assets/completion_audit/{EXIT_CRITERIA.md,completion_status.json,consistency_check.md}`
- **통제:** GPU 0; exit MUST/NICE 등급화; 존재≠검증(재집계 강제).

---

## 3. 통합 실험 매트릭스 — [지향 3-RQ] × [데이터셋] × [실험] × [지표] × [현재상태] × [담당]

> 상태: ✅완료·재사용 / 🟡부분(수치있음·미접합 or 재측정필요) / 🔴신규 / ⛔No-Go

| 지향 RQ | 실험 | 데이터셋 | 지표 | 현재상태 | 담당 | 누수통제 핵심 |
|---|---|---|---|---|---|---|
| **RQ-S** 색인·검색구조 | B0–B5/M2–M6 검색전략 랭킹 | VRU + 지능형 | nDCG@10, MRR, Recall@10(+CI) | 🟡순환(F1-F4) → REMEASURE | A | qrel∩meta=∅, vqa_facet doc 제거 |
| **RQ-S** | Flat/IVF/HNSW/IVF-PQ 색인 비교 | 시내도로 132K real + 1M synth | recall@10·p50/p95·index_mb·build_s | ✅ 계산완료(`index_benchmark_from_log.csv`) → PROMOTE | B | search-only 격리; IVF-PQ 33× 압축(index_mb 8 vs 268) real@131K |
| **RQ-S** | filtered-ANN prefilter/postfilter/single-stage | 시내도로(실 시공간) + 522(실 센서) | recall@10·p50/p95 × selectivity 0.01–1.0 | 🟡random-mask(`filtered_ann.csv`) → 실predicate 교체 | B(개념)+C(센서)+D(시간) | predicate=QA독립 시공간/센서; GT=subset내 exact NN |
| **RQ-S** | 저장단위 정책(zip:// vs materialized, frame-as-clip vs frames) | 522 | materialized frame#, join rate, zip read cost | 🔴 | C | materialization policy(전량해제 금지) |
| **RQ-ALC** 정확·지연·비용 | 색인구조 3축 Pareto | 시내도로 | recall vs p50 vs index_mb (N=10K–1M) | 🟡수치있음·원고밖 → 접합 | E(on B) | latency=filter-plan별 격리; real/synth 분리 Pareto |
| **RQ-ALC** | 색인근사(recall<1)→answer 손실 | VRU VQA(+distractor arm) | Δacc vs Δrecall@10 vs Δp95 | 🔴헤드라인 연결 | B4/E3 | 코퍼스고정, gold-recall 분리, exclude=self, retrieval-민감층 |
| **RQ-ALC** | 검색층 offline cost proxy + $/1k | 전 corpus + VRU 생성 | GPU-sec/1k, candidate#, build_s, index_mb | 🔴 | E | 미격리 wall-clock 금지, 대리지표·민감도 band |
| **RQ-ALC** | 답변 정확도-비용 trade-off | 다각도 + VRU | accuracy vs context token/frame budget | 🟡(6.8/6.13 accuracy 有, 비용축 미연결) | E(+6.8/6.13) | 고정 생성모델·temp=0, evidence만 변경 |
| **RQ-M** 3-모달 결합 | **센서 predicate prefilter (핵심 HEADLINE)** | 522 (영상frame+센서서사+센서시계열) | nDCG@10, Recall@10, candidate#(+CI) | 🔴신규 headline | C | predicate⟂정답(TL_1/TL_2 실측) → F1/F4/F8 동시 파괴 |
| **RQ-M** | NL질의+센서조건 cross-modal 검색 | 522 | Recall@K, MRR | 🔴 | C | 관제형 결합질의, 템플릿-비의존 소셋 포함 |
| **RQ-M** | **답변계층 evidence ladder (KEEP)** | VRU + 지능형 | exact-match acc (n=600, 2 LLM) | ✅견고(closed 0.308→0.538→0.665→0.680→oracle 0.747) | KEEP/6.8 | exclude=self, closed/distractor 하한, diff-proven 불변 |
| **RQ-M** | **다각도 선택>축적 (KEEP)** | 다각도(400 stratum) | acc, better−worse CI, both TOST, permutation | ✅견고(`canonical_stratified_event_split_5` 실재) | KEEP/6.13 | 사전등록·TOST·permutation·4 VLM·full-frame |
| **RQ-M** | temporal/motion (video-native) | 522 + VRU | temporal grounding, segment Recall | 🔴OPTIONAL | D | event window=GT only, dense 균일 pool |
| **RQ-M** | **진짜 tri-modal 독립보고서 검증** | 522 + 독립서사 조인 | 채널간 MI(독립성) or 진짜 join Recall | 🔴**설계게이트**(gap1) | C+D7 | 보고서=센서/이미지 재인코딩 아님을 MI로 증명 or 진짜 join |
| **RQ-M** 일반화 | B0–B5 이식 | 이상행동(1,968) | nDCG@10, Recall@10 | ✅(표19) | 보강 | schema portability만, 성능 일반화 금지 |
| **RQ-M** 일반화 | NL vehicle-track retrieval | CityFlow-NL | Recall@K, MRR | 🟡(annotation만) | 후속 | leaderboard 주장 금지 |
| 지표 정직성 | nDCG/MRR 주지표화 + capped-Recall 병기 | 전체 검색 | capped-Recall, R-precision, positive-set 분포 | 🔴(F9 caveat 부재) | F규칙+A | 다수-positive Recall 상한 caveat 강제 |

---

## 4. 실행 로드맵 (의존·리스크 기준 Phase 순서)

> **원칙(3개 비평 합의): 프레임 게이팅된 것(A 비순환 relevance·B4/E3 answer-coupling·시각)을 뒤로, frame-free·재사용 자산(센서 CSV·텍스트 retrieval·B/E 색인 승격·F 매트릭스)을 앞으로. 트립와이어(T1/T2/T4/T5)는 GPU 소비 이전 CPU-only로 먼저 게이트.**

### Phase 0 — 트립와이어 게이트 (CPU-only, GPU 이전, ~1일)
- **목적:** 헤드라인 존재 여부·시각 스코프·환경을 값싼 반증으로 먼저 판정.
- **선행:** 없음.
- **산출/작업:**
  - **T1 (feasibility #1):** TS_3 블록정렬 단일패스 추출기 PoC — 목표 멤버를 solid-block 인덱스로 정렬, 50클립×k블록 실측 wall-clock. → 시각 subset N 확정 근거.
  - **T2 (rq-coverage #2 + residual #2):** TL_1/TL_2 **전수** CPU 파싱 → 각 센서 predicate 카디널리티/selectivity(**신호위상 't' 희소성 검증**) + predicate↔relevance Cramér's V/MI 행렬(소표본 손라벨 probe 대비). → 저결합 & 운영유의 headline 쌍이 충분히 남는지.
  - **T3 (residual #7):** B5 조인율 스팟체크 → **No-Go 공식 확정**(namespace disjoint 이미 확인), 센서 headline을 C 코퍼스로 lock, MAIN=시공간 predicate only.
  - **T4 (residual #1 + rq-coverage #3):** C2/C3 verbatim-leak 스캐너 설계 + 50쌍 gold 파일럿으로 κ 실현가능성·**필요 표본 검정력** 추정(selectivity bin당 최소 질의수 사전확약).
  - **T5 (feasibility #2):** 환경 스모크 — **kiise-vlmdb(faiss 1.14.3 + torch 2.12/cu130 + tf 5.13 실측 공존)**에서 Qwen2.5-VL 1종 로드+생성 테스트. tf 5.13에서 VLM 로더가 깨지면 `pip install faiss-cpu`를 nrf2(tf 4.57, known-good)에 설치하는 대안으로 전환. → B4/E3/D6 단일환경 확정.
  - **T6 (rq-coverage #4):** A/C를 단일 canonical 빌드로 병합(어댑터 경로 `aihub_522_intersection`로 단일화).
- **exit criteria:** T1 실비용 표 확보 / T2에서 headline-가능 predicate-질의 쌍 ≥ 사전확약 수 / T4 gold 검정력 산정 완료 / T5 스모크 PASS 1종 / T6 단일 경로 확정.
- **롱폴·트립와이어:** T1(솔리드 7z), T2(신호위상 희소). **T2 실패 → 시각 relevance가 센서버킷으로 후퇴·순환 재발 → §7 No-Go-B.**

### Phase 1 — Frame-free 척추 (unblocked, 고확실성 산출, ~2–3일 CPU + GPU<2hr)
- **목적:** 논문의 보장된 백본(센서 결합 텍스트 헤드라인 + 색인 3축 + 답변계층 접합)을 확정.
- **선행:** Phase 0 T2/T3/T4/T6.
- **산출:** 522 센서 canonical(C1→C2, 정성서사·verbatim금지) → 센서 QA(C3) → 텍스트 임베딩(C7) → B0–B5 retrieval + 답변계층(A8/C7); B/E 색인 승격(`index_benchmark_from_log.csv`·`filtered_ann.csv` → paper_assets, 신규계산 0); sinnaedoro 실-시공간 predicate filtered-ANN(B2/D5); Pillar F 통합매트릭스·역할표·ledger·gap감사(CPU).
- **exit criteria:** 522 canonical에서 A6/C8 감사 어서션 5종 PASS + verbatim-leak 0 + B4<B2 사례 실증; index 3축이 본문 표/그림 참조; F 매트릭스에 '없음(🔴)' 셀 목록화.
- **롱폴·트립와이어:** 없음(전부 재사용/plain-zip). **이 Phase만으로도 정직한 축소불가 논문 골격이 선다.**

### Phase 2 — 시각 비순환 (T1 PoC 게이팅, ~1–2 GPU-day)
- **목적:** A의 비순환 relevance 메커니즘(프레임 기반 독립 판정)을 실현.
- **선행:** Phase 0 T1(실비용)·T5(env), Phase 1 canonical.
- **산출:** 522 영상 subset 추출(블록정렬, A/C/D 공유) → 키프레임 → Qwen2.5-VL dense caption(A3) → CLIP/SigLIP 시각 임베딩; InternVL3 relevance 판정(A5) + human-gold κ/positive-class 게이트 + **CLIP 캡션무관 대조 arm**; A8 비순환 retrieval 재측정.
- **exit criteria:** κ(또는 positive-class precision) ≥ 게이트 & bin당 최소 질의수 충족; 캡션무관 arm이 색인구조 이득을 VLM 상관과 분리 확인.
- **롱폴·트립와이어:** TS_3 디코드 I/O; κ 미달 → gold-only 축소셋(검정력 사전산정된 크기) 또는 §7 No-Go-A.

### Phase 3 — Answer-coupling 헤드라인 + 3축 (T5 + Phase 2 게이팅, ~1 GPU-day)
- **목적:** "색인 근사화가 답변정확도에 미치는 영향" 인과연결 + 3축 Pareto + pgvector 재현.
- **선행:** T5 단일환경, Phase 2 캡션 코퍼스(distractor arm 포함).
- **산출:** B4/E3 recall↔accuracy(코퍼스 고정 + gold-recall 분리 + 드롭문서 로깅 + retrieval-민감 층); E4 3축 Pareto; E5 cost 모델; B3 pgvector ANN sweep.
- **exit criteria:** answer가 recall에 반응하는 층 ≥1 입증(3축 붕괴 아님); 곡선이 평평하면 '색인효과 없음'을 정직한 결과로 서술(억지 하락 금지); real 132K 근거 우선, synthetic은 보조 투영 라벨.
- **롱폴·트립와이어:** null 위험(캡션 recall-강건) → 사전등록; synthetic answer축 headline 금지(rq-coverage gap6).

### Phase 4 — 확장(NICE, 비차단, 여력 시)
- **목적:** temporal 승격 + 진짜 tri-modal + CityFlow 일반화.
- **선행:** Phase 2 프레임 자산.
- **산출:** D1–D7(promote-or-limit 최소 VLM); tri-modal 독립보고서 조인 or MI-독립 증명(gap1); CityFlow visual 추출.
- **exit criteria:** temporal Δ가 사전 SESOI 초과면 승격, 미달이면 명시 한계(E6 비차단); tri-modal은 진짜 join 성립 or MI-독립 증명 시에만 RQ-M headline에 편입.

### Phase 5 — 완성 감사·freeze
- **목적:** 논문 착수 게이트.
- **선행:** Phase 1–3(+선택 4).
- **산출:** F5 검증기(per-query 재집계로 헤드라인 수치 재계산 대조), F6 서사 정합성(원고 순환 수치가 실제 대체됐는지 grep).
- **exit criteria:** §5 체크리스트 MUST 전부 PASS.

---

## 5. '실험 체계 완성' 정의 (Exit Criteria 체크리스트)

> MUST(E1–E7·E9·E10)가 전부 PASS면 논문 집필 착수 가능. NICE(E8·E11)는 비차단.

- **[MUST] E1 — 비순환 재측정:** 522(A/C 병합) 및 수리 VRU에서 B0–B5 재측정 manifest 존재 + 델타 정직보고 + A6/C8 어서션(keys∩=∅, vqa_facet_statement 0건, facet_source=sensor_csv, B4−B2 부호분포에 음수) 5/5 PASS.
- **[MUST] E2 — 센서 결합 headline:** 522 센서 predicate(QA독립) 검색 실험 manifest 존재, RQ-M 결합 헤드라인이 순환 수치 아닌 실 센서 predicate 기반.
- **[MUST] E3 — verbatim-leak 0:** 색인 문서에 QA 정답 수치가 문자열/단위변형/부분합으로 미등장(leakage_scan.json PASS). **[residual gap1 하드게이트]**
- **[MUST] E4 — predicate⟂relevance 정량화:** Cramér's V/MI 행렬 산출, 'B4이득 vs 결합강도' 연속곡선 보고, bin당 최소 질의수 충족(cherry-pick 아님). **[residual/rq-coverage gap2]**
- **[MUST] E5 — 색인 3축 접합:** index_benchmark 3축(recall×latency×index_mb, real 132K 우선 + synthetic_aug 라벨)이 본문 표/그림에 참조.
- **[MUST] E6 — RQ-ALC 최소 커버:** answer accuracy + ≥1 cost proxy(candidate#/build_s/index_mb/token) 보고 + latency 범위선언; **answer가 recall에 반응하는 층 ≥1 입증**(3축 붕괴 아님).
- **[MUST] E7 — 6.8/6.13 diff-proven 불변:** 답변계층(closed 0.308→oracle 0.747, n=600, 2 LLM)·다각도 selection>accumulation 불변 확인.
- **[MUST] E9 — 지향 3-RQ 커버리지:** RQ-S/RQ-ALC/RQ-M 각각 non-circular·CI 실험 ≥1개(매트릭스 '없음' 0셀).
- **[MUST] E10 — 검증기 신뢰:** completion_status.json이 manifest 존재만이 아니라 **per-query parquet 재집계로 헤드라인 수치 재계산 대조** PASS(존재≠검증). B5 No-Go 문서화 포함.
- **[NICE] E8 — temporal:** D 결과 승격 or 명시 한계(비차단).
- **[NICE] E11 — tri-modal 독립성:** 보고서 채널이 센서/이미지 재인코딩 아님을 진짜 join or MI-독립으로 증명(gap1). 미증명 시 RQ-M headline을 이 워크로드에 lock 금지.
- **[MUST] E12 — 인용·재현성:** ForeSea/ForeSeaQA·UrBench 인용 + data/code availability statement.

---

## 6. 유지/재측정/승격/신규 분류표 — 기존 자산 처리

| 자산 | 분류 | 담당 | 근거·조치 |
|---|---|---|---|
| 표13 답변계층(6.8, `summary_qwen.json` 0.308→0.747) | **KEEP** | 6.8 | exclude=self·closed/distractor 하한·2 LLM, diff-proven 불변만 확인 |
| 표20 다각도 선택>축적(6.13, `canonical_stratified_event_split_5`) | **KEEP** | 6.13 | 사전등록·TOST·permutation·4 VLM·full-frame, 불변 |
| 표6/표7/표16 검색 헤드라인(순환 MRR/nDCG≈1.0) | **REMEASURE + DEMOTE-TO-DIAGNOSTIC** | A | qrel∩meta=∅ 재측정 or 진단 격하; 순환 수치 flagship 배제 |
| `index_benchmark_from_log.csv` (10K–1M, 55 config) | **PROMOTE** | B | 원고밖 고아 → §Storage-Indexing 본문 표/그림 편입(신규계산 0) |
| `filtered_ann.csv` (random-mask) | **PROMOTE(개념) + REMEASURE(실predicate)** | B+C+D | random-mask=개념검증 유지, 실 시공간/센서 predicate로 재측정 |
| pgvector(exact-only, `run_pgvector_retrieval.py`) | **REMEASURE(확장)** | B3 | HNSW/IVFFlat 실 색인 추가, recall-latency 재현 |
| reranker 결과(vru/지능형 `reranker_bge-m3.parquet`) | **KEEP + 접합** | A/B | 비순환 재측정 위에 재실행 |
| 다각도 evidence_frames/service_testbed | **KEEP** | 6.13/D | temporal(D) 프레임 자원으로 재사용 |
| VRU/AIHub 어댑터 facet_docs 분기 | **DROP(코드)** | A9 | F2 누수원 삭제 |
| 센서 결합·3축 Pareto·temporal·비순환 canonical | **NEW** | C/E/D/A | 신규 산출 |
| CityFlow-NL(annotation만) | **DEFER** | 후속 | visual 미추출, 후순위 |
| 이상행동 CCTV | **KEEP(일반화)** | 보강 | schema portability만 |

---

## 7. 리스크·트립와이어 — 실패 시 대안 (No-Go 분기)

| # | 트립와이어 | 판정 기준 | No-Go 분기 (주제 축소 없이) |
|---|---|---|---|
| **T1** | TS_3 솔리드 7z 롱폴 | 블록정렬 PoC wall-clock이 예산 초과(≫1일) | 시각 subset을 최소 층화(수백 클립)로 제한; **frame-free 센서·텍스트 헤드라인(Phase 1)으로 방어**; 시각은 정성 보강으로 강등 |
| **T2** | 신호위상 predicate 희소('t' 편중) | TL_1 전수에서 신호위상 selectivity 범위 불가 | 차종·차로·차량밀도·시각·보행 predicate로 headline 구성(predicate 교체, 주제 불변) |
| **T3** | predicate⟂relevance 붕괴(고결합) | 운영유의 질의가 predicate와 공선 | 'B4이득 vs 결합강도' **연속곡선 자체를 결과로**; 저결합=정직신호, 고결합=구조편향 명시 분해(배제 아님) |
| **T4** | 522↔sinnaedoro 조인(B5) | **이미 No-Go 확정**(namespace disjoint) | 센서-predicate=C 자체 코퍼스; MAIN 일반화=sinnaedoro 자체 시공간 predicate(실재) — **이미 계획에 반영** |
| **T5** | VLM-A↔VLM-B 공유편향 | retrieval성공 vs VLM 합의도 상관 과다 | CLIP/SigLIP 캡션무관 대조 arm으로 색인이득 격리; 게이트를 positive-class precision으로 |
| **T6** | human-gold κ 미달 | κ<게이트 or 검정력 부족 | 검정력 사전산정된 gold-only 축소셋; 무게중심을 6.8/6.13 + 센서결합으로 이동(주장 불변, 근거 강화) |
| **T7** | env 분절(faiss+VLM) | tf 5.13에서 VLM 로더 파손 | nrf2(tf 4.57)에 faiss-cpu 설치(known-good VLM); 커밋 전 스모크 필수 |
| **T8** | B4/E3 null(캡션 recall-강건) | recall↓해도 accuracy 평탄 | null 사전등록; 실 distractor-캡션 풀로 민감구간 확보; '소규모 감시코퍼스=ANN 불요'를 정직한 결과로 프레이밍(rq-coverage gap6) |
| **T9** | synthetic 1M 국소기하 왜곡 | 증강 kNN거리/LID가 real 132K와 이탈 | crossover를 증강방법 민감도 band로만; real 132K에서 관측된 regime만 강주장 |
| **T10** | GPU 경합(2×RTX3090 직렬 5–8일) | pillar 중첩으로 일정 붕괴 | 횡단 공유 스케줄; D6 최소치; 캡션 배치+짧은 max_new_tokens; Phase 1(CPU/저GPU) 우선 확정 |
| **T11** | tri-modal=2-modal+파생(gap1) | 보고서가 센서/이미지 재인코딩 | 독립 서사 조인 or MI-독립 증명 전엔 RQ-M headline을 이 워크로드에 lock 금지; Phase 1 센서결합은 유지 |

**메타 원칙:** 어떤 No-Go도 주제를 축소하지 않는다. 시각/κ/answer-coupling이 막히면 **frame-free 센서 결합(Phase 1) + 색인 3축(B/E 승격) + 6.8/6.13 앵커**가 축소불가한 정직 백본을 이미 구성하며, 야심찬 3-모달 프레임은 정성·한계 명시로 유지된다.

---

### 부록 — 검증된 핵심 사실 (2026-07-10 디스크 실측)
- 센서 원천 TL_1/TL_2 = **plain Zip(15/9.6MB, 각 29,234 CSV, 63 교차로)**; TL_1 cols `signal_info.movement/departure_time/car_type/lane/car_info.movement`(표본 movement 전 행 't' → T2), TL_2 `pedestrian_type/attribute/TOD/direction`. TS_3 = **75.18GB 솔리드 7z**; TS_1/TS_2 = 22바이트 미개방(불필요).
- sinnaedoro `corpus_real` = **132,521×512 CLIP**, `frame_index[frame_id,location,camera,date,time]` → 실 시공간 predicate 즉시 가능; 522와 namespace disjoint → **B5 No-Go**.
- index 3축 `index_benchmark_from_log.csv`: N=10K–1M, real≤131K + synthetic_aug≥300K, **IVF-PQ@131K recall 0.33–0.48 @ index_mb 8–12(vs flat 268MB, 33× 압축)** = real-data 저장 스토리; `filtered_ann.csv`=random-mask(교체대상).
- 답변계층 `summary_qwen.json`: **closed 0.3083 → distractor 0.5383 → vector 0.665 → prefilter 0.680 → oracle 0.7467**(n=600, topk=3, median_prefilter_candidates=29), llama3 병렬 존재.
- MAIN QA 규모: vru 7000/244, 다각도 36000/4572, 지능형 807/133, 이상 5904/424 (모두 807–36K → native ANN≈exact, honest framing 필요).
- env: **kiise-vlmdb = faiss 1.14.3 + torch 2.12.1/cu130 + transformers 5.13.0 + py7zr 1.1.3 + cuda(2 dev)**; nrf2 = torch 2.9/cu128 + tf 4.57.6, **faiss 부재**. VLM 전량 실재(`/hdd2/huggingface_cache/hub/`: Qwen2.5-VL-7B·Qwen2-VL-7B·InternVL3-8B-hf·Idefics2-8b·Qwen2.5-7B·Llama-3-8B·bge-reranker-v2-m3·Qwen3-Reranker-4B·NV-Embed-v2). 스크립트 53종·project_md 24/30/40/41·6.8/6.13 canonical 전부 실재.
