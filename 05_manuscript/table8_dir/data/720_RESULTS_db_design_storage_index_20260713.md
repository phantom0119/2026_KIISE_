# 720 — DB 설계 실험 결과: 저장단위 / partial-index / hot·cold (2026-07-13)

710 우선순위 실행 결과. 저장단위(P1)·pgvector partial-index(P2)·hot/cold 정책(P3)을 522 + MEVA에서 측정. 정직성 규칙(600/620 계승): latency 격리·상대비교, FAISS↔pgvector 절대비교 금지.

---

## P1 — 저장 단위 비교 (clip-caption / frame-vector / multi-vector / dual-index)

`run_storage_unit_benchmark.py`. 동일 질의·qrels(strict+semantic)로 4 저장단위. clip-caption=bge-m3(1024d, 캡션텍스트); frame/multi=CLIP ViT-B/32(512d, 교차모달 텍스트질의→이미지프레임); dual=RRF(caption, multi). CLIP 시각arm 정상 검증(교차모달 cos 0.21–0.34, 질의별 변별).

### 522 (tri-source expanded, 85 질의, 3,000 clip / 8,349 frame)
| 저장단위 | n_vec | storage MB | p50 ms | p95 ms | nDCG@10 strict | nDCG@10 semantic |
|---|---:|---:|---:|---:|---:|---:|
| **clip-caption** | 3,000 | **12.3** | **0.59** | 0.73 | 0.0588 | **0.1692** |
| frame-vector | 8,349 | 17.1 | 0.84 | 0.94 | 0.0615 | 0.1681 |
| multi-vector | 8,349 | 17.1 | 3.87 | **14.95** | 0.0615 | 0.1681 |
| dual-index | 11,349 | 29.4 | 4.44 | 6.91 | 0.0613 | 0.1644 |
→ **clip-caption Pareto-최적**: 정확도 동등한데 최소 저장·최저 지연. 시각 프레임/멀티벡터는 정확도 이득 없이 저장·지연 증가.

### MEVA (985 clip / 985 mid-frame, 193 질의) — 외적타당성, 결과 반전
| 저장단위 | n_vec | storage MB | p50 ms | p95 ms | nDCG@10 strict | nDCG@10 semantic |
|---|---:|---:|---:|---:|---:|---:|
| clip-caption | 985 | 4.03 | 0.14 | 0.15 | 0.0270 | 0.1029 |
| **frame-vector** | 985 | **2.02** | 0.15 | 0.17 | **0.0429** | **0.1610** |
| multi-vector | 985 | 2.02 | 1.11 | 2.55 | 0.0429 | 0.1610 |
| dual-index | 1,970 | 6.05 | 1.37 | 4.78 | 0.0291 | 0.1145 |
→ **frame-vector Pareto-DOMINANT**: 정확도 ↑(sem 0.161 vs 캡션 0.103) **AND** 저장 절반(CLIP-512 < bge-m3-1024). MEVA 캡션이 미세 활동을 못 담아(700 캡션 맹점) 시각검색이 우월.

### P1 확정 발견 (DB 설계 지침)
1. **최적 저장단위는 데이터셋/인코더 정합에 의존** — 캡션 인코더가 질의의미와 잘 맞으면(522, task-tuned) clip-caption이 최저비용·동등정확 → Pareto-최적; 안 맞으면(MEVA, 캡션 맹점) 값싼 **CLIP frame-vector가 정확도·저장 양쪽 지배**.
2. **multi-vector(exhaustive max-sim)는 본 워크로드에서 정당화 안 됨** — frame-vector 대비 정확도 이득 0, 지연 6–7× (522 p95 15ms). ANN 프레임색인(top-N collapse)이 max-sim과 @10에서 동일.
3. **dual-index(RRF)는 모달리티 강도가 불균등하면 오히려 희석** — 두 arm 다 약한 522, 시각이 훨씬 강한 MEVA 모두에서 단일 우월 arm보다 낮음.
4. 정확도 절대값은 낮음(희소 활동 검색 난제, 700과 정합) — 본 실험 기여는 **정확도·지연·저장 3축 Pareto와 설계규칙**.

**caveat(원고 명시):** clip-caption(bge-m3 text) vs frame/multi(CLIP cross-modal)는 저장단위 선택이 인코더 선택을 내포함(실무적으로 캡션 저장=텍스트인코더, 프레임 저장=시각인코더). 인코더 격리 ablation이 아니라 **저장 설계 비교**로 스코프.

자산: `results/storage_unit/{storage_unit_summary,_metrics,_latency}.csv`; MEVA CLIP `embeddings/clip-vit-b32/`.

---

## P2 — pgvector partial/local index vs global+WHERE

`run_pgvector_partial_index.py`. b3_frames(sinnaedoro corpus_real 132,521×512) 재사용, pgvector 0.8.4 :5433, `<#>`(정규화 cos). recall=exact seq-scan 필터 GT 대비. 선택도 sweep 0.011→0.774. **global HNSW(m16,efC200) build 50.4s / 333.5MB(1개, 상각)** vs predicate별 **partial index(`CREATE INDEX ... WHERE p`)**.

| predicate(sel) | global off recall/p50 | global relaxed recall/p50 | **partial** recall/p50 | partial build/size |
|---|---|---|---|---|
| location(0.011) | 0.010 / 0.37ms | 0.167 / **31.8ms** | **0.986 / 0.41ms** | 0.4s / 3.8MB |
| hour 7-7(0.047) | 0.175 / 0.42ms | 0.895 / 6.89ms | **0.988 / 0.45ms** | 1.9s / 15.7MB |
| hour=6(0.183) | 0.313 / 0.38ms | 0.986 / 1.09ms | 0.990 / 0.41ms | 7.1s / 61MB |
| hour 6-9(0.260) | 0.395 / 0.43ms | 0.986 / 0.91ms | 0.981 / 0.42ms | 10.7s / 87MB |
| hour 6-12(0.473) | 0.667 / 0.39ms | 0.993 / 0.43ms | 0.983 / 0.42ms | 21s / 158MB |
| hour 6-18(0.774) | 0.879 / 0.39ms | 0.997 / 0.45ms | 0.995 / 0.42ms | 39s / 258MB |

### P2 발견
1. **global+WHERE는 선택도가 높아질수록 recall–latency 딜레마**: `iterative_scan=off`는 빠르나(p50~0.4ms) recall 붕괴(선택적일수록 심함, s=0.011서 0.010, frac_short 98%); `relaxed_order`는 recall 회복하나 **지연 폭증**(s=0.011서 31.8ms, s=0.047서 6.9ms). 즉 선택적 predicate에서 global은 "빠르지만 틀리거나(off) 맞지만 느림(relaxed)".
2. **partial/local index는 전 선택도서 recall ~0.98–0.995 AND 지연 상수 ~0.42ms** — 부분집합 위 clean ANN(frac_short 0). 대가 = predicate별 build(0.4→39s, 선택도 비례) + 저장(3.8→258MB).
3. 620의 "random-mask가 filtered-ANN 과대평가"와 정합: 실 predicate에서 global postfilter는 특히 선택적 필터에서 무너지며, **partial index가 이를 구조적으로 해소**.

## P3 — hot/cold predicate 운영 정책 (break-even)

`score_hotcold_policy.py`. served global = `relaxed_order`(recall 유지 경로). `N* = 1000·build_s / (L_global−L_partial)`, 품질강제 = global recall < 0.95.

| sel | global recall | partial recall | L_global | L_partial | build_s | **N\*** | 정책 |
|---|---|---|---|---|---|---|---|
| 0.011 | 0.167 | 0.986 | 31.8ms | 0.41ms | 0.38s | 12 | **LOCAL (품질강제)** |
| 0.047 | 0.895 | 0.988 | 6.89ms | 0.45ms | 1.87s | 291 | **LOCAL (품질강제)** |
| 0.183 | 0.986 | 0.990 | 1.09ms | 0.41ms | 7.14s | 10,594 | LOCAL if hot >10.6k q |
| 0.260 | 0.986 | 0.981 | 0.91ms | 0.42ms | 10.7s | 21,509 | LOCAL if hot >21.5k q |
| 0.473 | 0.993 | 0.983 | 0.43ms | 0.42ms | 21s | 2.1M | GLOBAL+postfilter |
| 0.774 | 0.997 | 0.995 | 0.45ms | 0.42ms | 39s | 1.2M | GLOBAL+postfilter |

### P3 설계규칙 (손익분기)
predicate p에 **local/partial index를 만들 것 ⟺ (품질) global recall(p) < 0.95, OR (상각) 예상 질의수 > N\*(p)**; 아니면 **global + postfilter**.
- **선택적(s ≲ 0.05): 품질강제 LOCAL** — global은 어떤 지연에서도 recall 미달(s=0.011서 31.8ms에 recall 0.167). 질의수 무관 build.
- **중간(s ~0.18–0.26): 상각 regime** — global recall 충분(≈0.99), local은 hot(>~1–2만 질의)일 때만 이득(build 7–11s를 ~0.5–0.7ms/q 이득으로 상각).
- **넓음(s ≳ 0.47): 항상 GLOBAL+postfilter** — global relaxed가 partial과 동급(0.43ms, recall 0.99), local은 N* 수백만이라 무의미.

자산: `paper_assets/20260713_db_design/{pgvector_partial_vs_global,hotcold_policy}.csv`, `hotcold_summary.json`, `p2.log`.

---

## P2/P3 교차검증 — MIRIS (SIGMOD 2020 교통교차로, 독립 재현)

`build_miris_pgvector.py` + 일반화된 `run_pgvector_partial_index.py --table miris_frames`. MIRIS(Warsaw+Shibuya 고정 교통교차로, MIT 주석; uav=드론·beach=비교통 제외) 12영상 → **59,019 프레임 CLIP ViT-B/32-512**(sinnaedoro와 동일 인코더) → pgvector. predicate=scene(location)+스트림세그먼트(hour 0–23). global HNSW build 26s/154MB. (영상 저작권상 임베딩 비재배포·수치만 보고.)

| predicate(sel) | global off recall/p50 | global relaxed recall/p50 | **partial** recall/p50 | partial build/size |
|---|---|---|---|---|
| hour=6(0.042) | 1.000 / **7.75ms** | 1.000 / 7.78ms | **1.000 / 0.34ms** | 0.6s / 6.4MB |
| hour 6-9(0.167) | 0.614 / 0.40ms | 0.996 / 0.68ms | 0.999 / 0.38ms | 2.8s / 25.6MB |
| hour 6-12(0.292) | 0.770 / 0.46ms | 0.994 / 0.58ms | 0.998 / 0.39ms | 5.5s / 44.9MB |
| hour 6-18(0.542) | 0.900 / 0.47ms | 0.996 / 0.54ms | 0.998 / 0.44ms | 11.7s / 83MB |
| hour 6-21(0.667) | 0.938 / 0.43ms | 0.997 / 0.50ms | 0.999 / 0.49ms | 15.8s / 102MB |

**hot/cold N\*** (`hotcold_miris_*`): 0.042→**81 q**, 0.167→9,495, 0.292→30,330, 0.542→119k, 0.667→1.4M. 품질강제=[] (테스트 범위 내 global recall 항상 ≥0.99).

### 교차검증 판정 — 핵심 3개 재현 ✓ + 정직한 차이
- **재현①: partial/local = 전 선택도 recall ~1.0 + 지연 상수 ~0.3–0.5ms** — sinnaedoro와 동일. ✓
- **재현②: global+WHERE의 recall–지연 딜레마** — `off`는 중선택도서 recall 저하(0.61–0.77), `relaxed`는 선택적일수록 지연↑(hour=6서 **7.75ms** vs partial 0.34ms = **23×**). ✓ 기전 동일.
- **재현③: hot/cold N\*가 선택도에 단조 증가**(선택적 81q → 넓음 1.4M q) — sinnaedoro와 동형. ✓
- **정직한 차이(refinement):** MIRIS 최선택 predicate가 0.042(sinnaedoro는 0.011까지 감)라, sinnaedoro가 보인 **극단적 recall 붕괴(0.011서 0.167)** 대신 MIRIS는 **지연 페널티 regime**(global이 recall은 유지하나 7.75ms로 느림; 플래너 scan-fallback)로 나타남. 즉 **partial index가 이기는 이유가 "recall" 또는 "latency" 중 무엇이 병목이냐에 따라 바뀌며**(둘 다 partial이 해소) — 정책 규칙("선택적/hot predicate엔 local")은 그대로, 근거만 데이터·플래너에 따라 recall↔latency로 이동. **오히려 정책의 강건성을 보강.**

**⇒ DB 설계 발견(P2/P3)이 독립 상위학회(SIGMOD) 교통 데이터셋에서 재현됨 = MEVA(검색)와 별개로 색인·배포 정책 축의 국제 외적타당성 확보.** 자산: `pgvector_partial_vs_global_miris.csv`, `hotcold_miris_policy.csv`, `p2p3_miris.log`.

---

## 강화된 기여 문장 (실측 반영본 — 원고 §Contribution 삽입 대기)
> 본 연구는 멀티모달 감시 데이터의 검색 정확도만 비교한 것이 아니라, **저장 단위·색인 구성·필터 결합 방식·관계형 DB 구현 방식**이 **정확도·지연·저장공간**에 미치는 영향을 함께 분석하였다. (i) **클립-캡션·프레임-벡터·다중-벡터·이중-색인** 저장단위를 두 데이터셋(국내 522·해외 MEVA)에서 비교하여, 최적 저장단위가 캡션-질의 정합에 의존함을 보였다(522는 clip-caption Pareto-최적, MEVA는 frame-vector 지배; multi-vector·dual은 이득 없음). (ii) 실제 센서·시공간 predicate에서 **global index+postfilter vs partial/local index**를 측정하여, global postfilter가 선택적 필터에서 recall–지연 딜레마에 빠지는 반면 partial index는 전 선택도서 recall ~0.99·지연 상수 ~0.4ms를 제공함을 정량화하였다. (iii) 이로부터 **local index를 언제 만들지에 대한 hot/cold 손익분기 규칙**(품질강제 s≲0.05, 상각 N\*)을 제시하여 **VLM-QA evidence layer의 데이터베이스 설계 지침**을 도출한다.
