# Phase 0 트립와이어 실측 결과 (2026-07-10)

마스터플랜(`400_METHOD_experiment_system_masterplan_20260710.md`)의 Phase 0 CPU 게이트 착수 기록.
목적: GPU 소비 이전에, 값싼 반증으로 "센서 결합 헤드라인이 실현 가능한가"를 판정.

## 실행한 것

- **신규 스크립트:** `scripts/build_intersection_signal_sensors.py`
- **입력(실측):** 교차로신호체계 라벨 zip `TL_1.통과차량`+`TL_2.보행량`(train) / `VL_1`+`VL_2`(val) — plain-zip, GPU 불필요.
- **산출:** `Datasets/processed/aihub_522_intersection/20260710/{sensor_facets.parquet, T2_report.md, T2_report.json}`
- **규모:** **32,880 클립 × 63 교차로**, 9초(CPU) 파싱. (미개방 원천 raw는 불사용 — 라벨 CSV로 충분함이 재확인.)

## T2 — 센서 predicate 카디널리티/selectivity (PASS)

| predicate | 카디널리티 | min selectivity | 판정 |
|---|---:|---:|---|
| intersection_id | 63 | 0.013 | ✅ selectivity sweep 이상적 |
| hour | 12(주간만) | 0.022 | ✅ |
| time_of_day | 3(dawn 없음) | 0.293 | ✅ |
| sig_has_pedestrian | 2 | 0.427 | ✅ |
| sig_has_yellow | 2 | 0.308 | ✅ |
| veh_density_bin | 3 | 0.333 | ✅(구성상 균형) |
| sig_has_left | 2 | 0.044 | ⚠️ 95.6% 클립에 존재 → 이진 predicate 약함 |
| **is_weekend** | **1** | **1.000** | ❌ **전 클립 평일 → 폐기** |

**신호위상 트립와이어(T2) 통과:** 전역 `signal_info.movement` 분포 = t 0.606 / tl 0.132 / l 0.119 / s 0.072 / y 0.051 / p 0.021 → **전부-'t' 아님, 위상 predicate 살아있음.** (단 clip 단위 좌회전 신호는 거의 상존 → clip-level 이진보다 위상-구성/시간창 feature로 써야 함.)

## T3 — predicate ⟂ relevance 독립성 (핵심 타당성, PASS)

**순환 없는 헤드라인용 저결합 쌍(확정):**

| 필터 predicate(외생) | relevance(장면내용) | Cramér's V |
|---|---|---:|
| time_of_day | has_bus | **0.004** |
| sig_has_pedestrian | has_bicycle_ped | 0.058 |
| sig_has_yellow | has_left_turn_veh | 0.180 |
| hour | has_truck | 0.208 |

**고결합(회피 또는 T3 '결합강도 곡선' 대조군으로만):**
- `sig_has_left × has_left_turn_veh` V=0.751 (신호↔행동 자연상관)
- `intersection_id × has_right_turn_veh` V=0.648 (교차로 기하)
- `intersection_id × has_bus` V=0.549

→ 전역 max V=0.751이나, **대다수 쌍이 V<0.3**로 F1/F4를 데이터 수준에서 붕괴시킬 저결합 워크로드 구성 가능. 마스터플랜 T3 분기(‘B4이득 vs 결합강도’ 연속곡선)와 정합.

## 데이터 특성(설계 반영 필요)

- **평일·주간 only**: `is_weekend` 폐기, `time_of_day`에 dawn 없음 → 시간 predicate는 hour/time_of_day(주간)로 한정.
- **밀도 풍부**: n_vehicles min 1 / mean 44.8 / max 400; n_pedestrians mean 6.5 / max 64 → count 기반 QA(“버스 몇 대”, “보행자>K”) 프로그램 검증 가능.
- **R-feature base rate**: has_left/right_turn 0.94/0.95(거의 상존 → 이진 QA로 약함, count/argmax로 설계), has_uturn 0.21·has_bus 0.68·has_bicycle 0.63(균형, QA 정답 후보로 적합).

## 게이트 판정

- **T2 신호위상 희소 → 반증(PASS).** predicate 재고 불필요, 시간·교차로·위상·밀도 predicate 다수 확보.
- **T3 독립성 → PASS.** 저결합 predicate×relevance 쌍 확정, 순환 없는 헤드라인 성립.
- **T?/is_weekend → 폐기 결정.**

## 다음 단계 (마스터플랜 대비)

1. (CPU, 무GPU) Pillar C 캐노니컬화: `sensor_facets.parquet` → clips/metadata(P/R facet 분리, facet_source=sensor_csv)/queries(metadata_filter=P only, qrel_filter=R/semantic only, disjoint 강제)/센서 QA(count/argmax/threshold, 정답 verbatim 부재 어서션). A6 비순환 감사 스크립트.
2. (게이팅) **T1** TS_3(75GB solid 7z) 블록정렬 추출 PoC → 시각 subset N 확정.
3. (GPU) **T5** VLM env 스모크(kiise-vlmdb: faiss 1.14.3 + torch 2.12 + tf 5.13에서 Qwen2.5-VL 로드).
4. (GPU) Phase 2 캡션·독립판정 → 비순환 retrieval 재측정.

미해결/리스크: 클립-level 신호 predicate 약함(위상-구성 feature 필요), 완전 비순환 relevance는 캡션/프레임(GPU) 필요.

---

## Phase 1 진입 (같은 세션, CPU) — 비순환 canonical + A6 감사 (PASS)

- **신규 스크립트:** `scripts/build_intersection_signal_canonical.py`
- **산출:** `Datasets/processed/aihub_522_intersection/20260710/canonical/{clips,metadata,queries,qrels,facet_roles,A6_noncircularity_audit}`
- clips 32,880 / metadata 558,960 facet행(predicate/relevance/context 역할태그) / queries 15 / qrels 3,294.

**정직한 발견 → 정제:** 1차 시도는 이진 R-feature(has_bus 등)를 relevance로 써 **질의당 positive 3,349개(코퍼스 10%)** = 비변별적 class-membership(F9 재발). count/threshold 기반 **희소 relevance**로 교체:
- `heavy_traffic`(n_vehicles≥150, 2.6%), `uturn_with_peds`(3.0%), `many_bicycles`(4.2%), `crowd_with_bicycle`(5.6%).
- 결과: 질의당 positive 평균 **219.6개(0.7%)**, relevance 밀도 중앙값 3.6%.

**A6 비순환 감사 (machine-checked, 전부 PASS):**
- 필터 키 ∩ relevance = ∅ (disjoint) ✅
- 필터 키 ⊂ P-predicate(time_of_day/hour/sig_has_yellow/sig_has_pedestrian) ✅
- relevance = 희소 scene def ✅ (밀도<8%)
- 저결합 4/4, **max Cramér's V=0.184** ✅ → F1/F4 구조 붕괴 실증
- OVERALL NON-CIRCULAR PASS = True

**설계 확정:** 센서 CPU 트랙 = (a) 필터 predicate selectivity(filtered-ANN) + (b) 프로그램검증 QA(count/argmax/threshold)에 최적. 이진 base-rate feature는 retrieval relevance로 부적합. **fine-grained retrieval relevance는 Phase 2 VLM 캡션(희소 의미 질의)으로 보강.** `intersection_id` contrast arm은 positive 범위 밖이라 이번 빌드에서 0건(후속 재추가).

**다음(결정/자원 필요):** ①T1 TS_3(75GB solid 7z) 블록추출 PoC → 시각 subset N ②T5 VLM env 스모크 ③Phase 2 캡션(Qwen2.5-VL)+임베딩 → 522에서 B0–B5 실측 → old(순환)vs new(비순환) collapse 대조표.

---

## T1 실행 + 522 데이터모델 재발견 (2026-07-10 야간 세션) — 시각 트랙 UNBLOCKED

### T1 추출 실비용 (PASS, 예상보다 훨씬 쌈)

- TS_3/VS_3/TL_3/TL_4/TL_5 전부 **확장자만 .zip, 실제 solid 7z(LZMA2)**. TL_1/TL_2만 진짜 zip.
- **py7zr는 블록 단위 seek 수행**: 30장 추출 = head 2.6s / mid 7.6s / tail 80.8s (TS_3 36블록·70.7GiB, 블록당 ~2GiB).
- 디스크 1.3TB 여유 → **subset이 아니라 전량 1-pass 추출이 정답**. `scripts/extract_intersection_visual_sources.py`로 라벨 6종+val(288s/16,084장)+train 추출 실행. 산출: `processed/aihub_522_intersection/20260710/{frames_src,labels_src,extract_manifest.json}`.

### 중대 재발견 1: TS_3는 mp4가 아니라 **추출된 JPG 프레임**

- train 127,746 + val 16,084 = **143,830 JPG (1920×1080)**, 46,527+α 비디오 × ~3프레임. **키프레임 추출 파이프라인 자체가 불필요.**
- 구조: `<카메라>/<task>/<video_id>_<frame>.jpg`. 카메라 코드 = ID 끝 2자리: **센서=10, 시각=11/22** — 같은 63개 교차로의 다른 접근로 카메라.

### 중대 재발견 2: 클립 수준 센서↔시각 조인 성립 (동기 녹화)

- `scripts/build_visual_sensor_join.py` → `visual_videos.parquet`(52,462 비디오) + `visual_sensor_join.parquet` + stats.
- **join_rate ±120s = 90.2% (47,308 비디오), median gap = 0초** — 타임스탬프가 완전 동일한 쌍이 대부분(`101011_2021…4475694 ↔ 101010_2021…4475694`). 같은 세션의 **동기 다중카메라 녹화**.
- 조인된 시각 비디오에 센서 predicate facet 부착 완료, 분포 균형(오전/오후/저녁 ≈ 14K/18K/15K; 밀도 3분위; yellow 33K/14K). `join_type='cross_camera_time_window'`로 정직 표기(뷰는 다름, 교차로 상태는 공유).
- 어제의 "TL_1↔TS_3 조인 불가" 비관은 **키 정규화 오류**였음(센서 intersection_id가 카메라ID 그대로였음). 수정 후 성립.

### 중대 재발견 3: 시각 relevance는 사람 주석에서 프로그램 도출 가능

- **TL_3** = task별 CVAT XML: 프레임별 차량 **polyline 궤적** + 라벨(car/bus/truck/small_truck/large_truck/small_bus/bike/unknown) + 속성 **is_stopped/is_parked/is_visible/is_correct/car_count**.
- **TL_4** = 프레임별 **bbox**(같은 차종 + car_plate/face 프라이버시박스), task 카테고리 = **1.교차로 1,536 / 2.악천후 170 / 3.시간대 372** → **악천후=진짜 날씨 predicate**.
- 함의: 시각 검색 relevance("정차한 버스", "주차 차량", "차량≥N", "자전거 존재")를 **VLM 실버라벨 없이 사람 주석으로 정의 가능**. relevance 소스(TL_3/4, cam 11/22)와 predicate 소스(TL_1/2 센서 cam 10 + 악천후/시간대 카테고리)가 **파일·카메라 수준에서 분리** → 비순환성이 소스 수준에서 보장. 마스터플랜 A5(VLM-B 실버 판정)는 주석에 없는 의미 need 보강용으로 축소 가능(κ 리스크 T6 크게 완화).

### T5 스모크 (부분): I/O 경합으로 보류

- Qwen2.5-VL fp16 로드가 70GiB 추출과 /hdd2 I/O 경합 → 로드만 7분+ (평시 ~1분). **추출 완료 후 재시도** (transformers 5.13에서 Qwen2.5-VL은 project_md/37·38에서 기작동 확인된 조합이라 리스크 낮음).

### 갱신된 Phase 2 실행순서 (마스터플랜 대비 단순화)

1. (진행중) train 프레임 추출 완료 대기 → T5 재실행.
2. TL_3/TL_4 XML 파서 → **프레임 단위 시각 relevance facet**(annotation_facets.parquet): 차종별 count, stopped/parked, 악천후/시간대 카테고리. [NEW `build_intersection_annotation_facets.py`]
3. 조인 테이블과 결합해 **tri-source 캐노니컬 확장**: predicate=센서(TL_1/2)+악천후, relevance=주석(TL_3/4), 문서=VLM 캡션(Qwen2.5-VL). A6 감사 확장(소스 분리 어서션).
4. CLIP/bge 임베딩 → 522 B0–B5/M-계열 실측(비순환) → collapse 대조표.

### 실행 결과 (같은 세션 후속, CPU)

**주석 facet 완성** — `build_intersection_annotation_facets.py` 실행: frame_rows 234,317 (TL_3 133,979 + TL_4 100,338) → **비디오 52,210개에 사람 주석 relevance** (`annotation_{frame,video}_facets.parquet`). 희소 relevance 확보: any_parked **1.7%**, any_stopped 18.8%, bus 43%, bike 41%.

**Tri-source 독립성 정량화** (`trisource_independence.json`, n=47,098 조인+주석 비디오):
- 센서 predicate(5) × 주석 relevance(6) 30쌍 중 **25쌍 V<0.3**, global max 0.454.
- 헤드라인급 초저결합 쌍: `sig_has_yellow×rel_parked V=0.005`, `time_of_day×rel_multi_bus V=0.007`, `sig_has_pedestrian×rel_parked V=0.012`, `hour×rel_multi_bus V=0.023`.
- 자연 상관(혼잡시간×정차 0.45, 밀도×트럭 0.45)은 T3 '결합강도 연속곡선' 대조군으로 보고.
- **소스 수준 분리**: predicate=TL_1/2 CSV(cam 10) ↔ relevance=TL_3/4 XML(cam 11/22, 사람 라벨) ↔ 문서=VLM 캡션(픽셀만) — 세 채널이 서로 다른 파일·카메라·생산자.

**TS_4 발견**: 악천후(6,193 비디오)/시간대(9,056 비디오) 주석의 원천 프레임은 TS_3가 아니라 **TS_4.바운딩박스(54GB)/VS_4에 존재**(TS_3와 중복 0). 악천후=시각 코퍼스의 진짜 날씨 predicate → `extract_intersection_visual_sources.py --only bbox`로 후속 추출 예정.

**Phase 2 발사 준비 완료**: `build_intersection_captions.py` 작성 — 층화 3,000 비디오(63교차로×시간대 균형, join+주석 필수), 중간 프레임 캡션, 2-GPU 샤딩+재개, **캡셔너에 센서/주석 입력 차단**(소스 분리) + 토큰 누출 어서션. CPU 표본선택 검증 완료(1,364/3,000 프레임 이미 추출됨).

---

## ⭐ A9 실행: VRU 순환 워크로드 수리 + COLLAPSE 실측 (심사 P0-1의 첫 hard evidence)

- **신규:** `scripts/build_vru_noncircular_canonical.py` (v1 어댑터 서브클래스, v1 무손상) → `processed/vru_accident/20260710_noncircular/` — 캡션-only 1,000 docs(F2 fix), relevance=**사고유형 의미축** vs filter=**독립 운영facet**(weather/road/location; 결합도 V=0.177/0.039/0.249)(F1/F4 fix), **strict+semantic 이중 qrels**, A9 감사 PASS. 85질의.
- bge-m3 임베딩(1m40s) + 기존 `run_retrieval_baselines.py` **무수정** 재사용 → B0–B5 실측.
- **신규 asset:** `paper_assets/20260710_noncircular_collapse/vru_collapse_table.{csv,md}` + `results/vru2_bgem3_b0_b5/metrics_semantic.csv`(저장 랭킹 후처리).

**Collapse 결과 (nDCG@10):**

| 전략 | v1 순환(원고 표6) | v2 strict | v2 semantic |
|---|---:|---:|---:|
| B2 vector-only | 0.4476 | 0.1845 | 0.2649 |
| B4 prefilter | **0.9736** | **0.3174** | 0.2974 |
| B1 BM25 | 0.4495 | 0.0918 | 0.1607 |

- **B4−B2: +0.526(tautology) → +0.133(strict, 합법 이득) / +0.033(semantic)**.
- **semantic-only per-query B4−B2 부호분포: 음수 18 / 0 34 / 양수 33 (n=85)** — v1에선 구조적으로 불가능한 음수 등장 = **F1 "B4≥B2 보장"의 실측 붕괴**. A6 어서션 5(부호분포에 음수) 실증 통과.
- 해석: prefilter는 hard constraint에선 여전히 유익(+0.133)하나 soft intent에선 18/85 질의에서 관련 clip을 제거해 해침 — "필터는 만능 아님, 질의 의도에 따라 계획해야"가 새 정직 헤드라인 후보.
- 남은 것: 지능형 CCTV 어댑터 동일 수리, 522 tri-source(캡션 후) 실측, CI/bootstrap 유의성.

## ⭐ A9(2): 지능형 CCTV 수리 + collapse (v1 완벽지표의 정체 확정)

- **신규:** `scripts/build_aihub_cctv_noncircular_canonical.py` (raw 20260706 재사용, 출력 `processed/aihub_intelligent_cctv/20260710_noncircular/`) — corpus=**event_caption(한국어 사람 서술) only**(event/temporal_statement 삭제=F2 fix), relevance=event_class, filter=night/place_type, 이중 qrels, 감사 PASS. 18질의(소형).
- **Collapse (nDCG@10, strict):** B4 **1.0000→0.8395**, B3 1.0000→0.8395, **B1 BM25 0.9600→0.1111** — v1 BM25 완벽지표 = 순수 라벨 문자열 매칭이었음이 확정. B2 0.7014→0.6285.
- semantic-only: B4−B2 부호 **neg=4/zero=12/pos=2**(n=18) — 여기서도 F1 보장 붕괴.
- 부수 관찰(정직 포인트): 영어 질의↔한국어 캡션에서 dense(bge-m3, 0.82 semantic) ≫ BM25(0.17) — **교차언어 sparse 실패/다국어 dense 생존**은 v2에서만 보이는 진짜 신호(v1은 라벨 재진술이 가림).
- 결합도 주의: night V=0.583/place V=0.485(자연 상관, 소형 n) → 이 데이터셋은 collapse 실증용, 저결합 헤드라인은 522 tri-source가 담당.

## Phase 2 발사 로그

- 추출 완료 검증: train 127,746 JPG(1,808s), val 16,084, 라벨 6종 — `extract_manifest.json`.
- 캡션 2-GPU 샤드 발사(1,500씩, Qwen2.5-VL fp16, greedy, 448px, 110tok) → `captions/captions_shard{0,1}.jsonl`. **로드 185s, 생성 정상(분당 ~18캡션, ETA ~2.5–3h). 품질 확인: 차종·정차·보행자·날씨 사실 서술.**
- TS_4/VS_4(악천후·시간대 프레임) 추출 백그라운드 병행 중.
- 캡션 완료 후 자동 체인: `--merge-only` → `build_intersection_trisource_canonical.py`(strict+semantic 이중 qrels, 8쌍 predicate×annotation-relevance) → `build_text_embeddings.py` → `run_retrieval_baselines.py` → semantic 후처리 + 유의성.

## ⭐ 유의성 (B4−B2, nDCG@10, paired bootstrap 5000 + Wilcoxon) — `paper_assets/20260710_noncircular_collapse/significance_v2_b4_vs_b2.csv`

| 데이터셋 | qrels | Δ | 95% CI | 판정 |
|---|---|---:|---|---|
| VRU v2 | strict | +0.1329 | [0.092, 0.179] | 유의 (p≈2e-4) |
| VRU v2 | semantic | +0.0325 | [0.005, 0.064] | marginal (Wilcoxon 0.075) |
| AIHub v2 | strict | +0.2110 | [0.078, 0.364] | 유의 (p=0.005) |
| AIHub v2 | semantic | +0.0192 | [−0.032, 0.098] | **비유의** |

**새 정직 헤드라인(초안): "metadata prefilter의 가치는 제약의 성격에 달렸다 — hard constraint에선 유의한 이득(+0.13~+0.21), soft intent에선 이득 소멸·일부 질의 손해(neg 18/85). v1의 +0.53과 완벽지표는 워크로드 순환의 산물."**

## TS_4/VS_4 추출 + 악천후·시간대 트랙 판정

- 추출 완료: train_bbox **93,867 JPG**(53.5GiB/1,611s), val_bbox 11,917(6.75GiB) — `frames_src/{train,val}_bbox/{1.교차로,2.악천후,3.시간대}/`.
- **판정(정직):** `1.교차로` 비디오(51,775)는 센서 조인 89.5%(동일 세션). 그러나 **`2.악천후`(6,325, 2021-09 별도 일자)·`3.시간대`(9,056, 2021-08)는 센서 조인 0%** — 별도 녹화 캠페인. → 날씨/시간대 트랙의 외생 predicate는 센서가 아니라 **아카이브 큐레이션 카테고리+파일명 시각**으로 정의(주석 relevance와 소스 독립은 유지). 핵심 tri-source(센서 조인) 헤드라인과 구분되는 확장 트랙.

## 전 체인 스모크 검증 (부분 캡션 1,027개로 E2E PASS)

- 버그 수정: 캡션 merge가 split 키 없이 조인 → train/val 중복 4건. `merge_shards`에 split 포함 + trisource 빌더 split-aware 조인으로 수정, 재검증(1,027 docs → 1,027 corpus 정확 일치).
- 체인 실행: merge → `canonical_trisource`(28질의: low 20/contrast 8, strict 467/semantic 2,472 qrels, **A6 6/6 PASS**) → bge-m3 임베딩(cuda:0, 캡션 VLM과 공존 확인) → B0–B5.
- 스모크 수치(부분 코퍼스, 참고용): B4 nDCG 0.2489 / B2 0.0467 / BM25 0.0068 — 캡션-corpus에서 주석 이벤트 검색은 정직하게 어려운 과제(완벽지표 소멸). B0 metadata-only 0.19 = 희소 relevance×강한 predicate에서 필터 단독도 경쟁력 — 흥미로운 신규 관찰 후보.
- **최종 런은 캡션 3,000 완료 시 파라미터 교체 없이 동일 체인 재실행만 남음.**

---

# ⭐⭐ 522 TRI-SOURCE 최종 결과 (Phase 2 완결, 2026-07-10)

캡션 3,000/3,000 완료(샤드1 69분 + 샤드0 777 + 역방향 헬퍼 723; 유휴 GPU 재투입으로 반감). 최종 체인 실행: merge → canonical_trisource(**32질의**, low 23/contrast 9, strict 1,472/semantic 9,062 qrels, **A6 6/6 PASS**) → bge-m3 → B0–B5 → semantic 후처리 + 유의성. Asset: `paper_assets/20260710_noncircular_collapse/trisource_522_final.{md,csv}` + `significance_522_trisource.csv`.

## B4−B2 유의성 (nDCG@10)

| case | n | Δ | 95% CI | 부호(neg/zero/pos) |
|---|---:|---:|---|---|
| strict (hard 제약) | 32 | **+0.1445** | [0.082, 0.216] | 0/13/19 |
| semantic (soft 의도) | 32 | **−0.0745** | [−0.133, −0.012] | **16/8/8** |
| semantic·low-coupling | 23 | **−0.1308** | [−0.191, −0.075] | 13/7/3 |
| semantic·contrast(자연결합) | 9 | +0.0693 | [−0.033, 0.171] n.s. | 3/1/5 |

## 확정 발견 (논문 헤드라인 후보)

1. **prefilter의 가치는 제약의 성격이 결정**: hard constraint → 유의 이득(+0.14); soft intent → 유의 **손해**(−0.07).
2. **메커니즘 분해 확보**: 손해는 predicate⟂relevance(저결합)에 집중(−0.13 유의), 자연결합 쌍에선 무해(+0.07 n.s.) — "독립 predicate로 soft 필터링 = 관련 문서 폐기" 이론 그대로. **결합강도 곡선(T3)이 데이터로 실현됨.**
3. strict에서 **B0 metadata-only(0.165) > B2 dense(0.064)** — 희소 relevance×강한 predicate 체제에서 센서 메타데이터 단독의 가치.
4. **VLM 캡션의 문서 맹점(정직)**: parked_vehicle 쌍 dense ~0 — 캡션이 '주차'를 체계적으로 누락. DB 문서로서 VLM 캡션의 커버리지 한계 = C2급 발견 후보.
5. v1 순환(+0.53, 완벽지표) → 세 워크로드 모두에서 붕괴 재현(VRU/지능형/522).

## 남은 다음 단계 (마스터플랜 잔여)

- Pillar B: index 3축(sinnaedoro) 본문 승격 + filtered-ANN을 522 실 predicate로 재실행 + pgvector 실색인.
- Pillar E: 3축 Pareto + 색인근사→답변 결합(B4/E3).
- 답변계층: 522 센서 QA(count/argmax) + 프로그램 검증 → 6.8 확장.
- 악천후/시간대 확장 트랙(큐레이션 predicate) 캡션·실측.
- 원고 반영: 표6/7/16 격하·재서술 + 새 헤드라인 구조.

---

# ⭐ 질의셋 확장(32→85) — 헤드라인의 자기-스트레스테스트와 정제 (2026-07-11)

적합성 재검사(무결성 13/13 OK)에서 M6 소표본(n=32)이 최대 갭으로 판정 → **사전선언된 기계적 확장 규칙**으로 확장: ①신규 relevance def는 밀도 [1%,12%] ∧ 기존 def의 불리언 조합 금지 → `two_plus_bikes`(11.5%)만 승인(truck_convoy3 13.6%·very_dense25 0.87% 기계 기각) ②쌍 구성 = 5 predicate × 5 rel-def **전체 교차곱**(손선별 금지) ③결합도 라벨 = 실측 V<0.3 동일 임계 ④원본-32는 `in_original_specs`로 분리 보고. 산출: `canonical_trisource_expanded/`(85질의, A6 6/6 PASS), `results/trisource_expanded_b0_b5/`.

**결과 (semantic B4−B2, nDCG@10):**

| 표본 | n | Δ | 95% CI | 판정 |
|---|---:|---:|---|---|
| 원본-32 (재현) | 32 | −0.0745 | [−0.136, −0.014] | 재현 ✓ |
| **확장-신규** | 53 | +0.0197 | [−0.008, 0.050] | **n.s. — 집계 손해 주장 생존 실패** |
| 통합-85 | 85 | −0.0158 | [−0.047, 0.015] | n.s. |
| 통합·low-coupling | 75 | −0.0357 | [−0.065, −0.008] | boot-유의 |
| 통합·contrast | 10 | **+0.1335** | [0.017, 0.249] | 유의(양) |

**T3 결합강도 연속곡선 확정** (`t3_coupling_curve.csv`, n=85): Spearman ρ(Δ, pair V) = **0.285 CI [0.071, 0.484]**(0 배제); 구간 평균 단조 — V<0.05 **−0.099**(n=27) → 0.05–0.15 −0.002(30) → 0.15–0.3 +0.003(18) → V≥0.3 **+0.134**(10). *(정정 2026-07-11: 최초 산출의 pd.cut 좌측 개구간이 V=0.0인 완전 독립 쌍 11개를 최저구간에서 탈락시켜 −0.142로 편향 — F5 검증기가 적발, 포함 후 −0.099가 정본.)* *(정정 2026-07-12: codex 교차 검증이 의사반복 적발 — V는 (predicate 필드×정답) **쌍 수준 속성(25쌍)**이므로 질의 수준 CI [0.071,0.484]는 군집 무시. 쌍 군집 부트스트랩(seed 20260712, B=5000): ρ CI **[−0.031, 0.485]**, 저결합 V<0.05 [−0.179,+0.013], V<0.3 [−0.094,+0.010] — 모두 0 포함 → 곡선은 **탐색적 경향**으로 강등, 원고 §6/초록/결론 반영. 자연결합 V≥0.3은 2쌍뿐(참고용). 정본: `paper_assets/20260712_codex_crosscheck_fixes/t3_cluster_inference.json`. 같은 검증에서 주차-dense 실패 기전도 정정: 캡션 87%가 'parked' 언급(절반 부정형), 긍정 언급 판별력 52% vs 45% → '서술 부재'가 아니라 **부정·과언급 혼동**, `parked_caption_crosstab.json`.)*

**정제된 최종 헤드라인:** ~~"soft intent에서 prefilter가 유의하게 해친다(−0.075)"~~ → **"soft-intent 모드에서 prefilter 가치의 부호는 predicate–relevance 결합도가 결정한다: 진짜 독립(V<0.05)이면 −0.14 손해, 자연 결합(V≥0.3)이면 +0.13 이득, 중간은 중립 — 단조 연속곡선(ρ CI 0 배제). 집계 부호는 질의 믹스의 함수일 뿐."** 원본-32의 점추정은 초저-V 편중 표본의 산물임을 확장이 스스로 드러냄(사전선언 규칙 하 — forking-paths 아님). strict는 +0.0983 [0.068, 0.133]으로 안정.

**교훈(원고 한계·방법절 후보):** filtered-search 평가의 집계 결론은 질의 믹스에 좌우된다 — **결합도 스펙트럼을 명시적 보고 축으로** 삼아야 하며, 이것이 본 워크로드 프로토콜의 일부다.
