# 표 5 관리 디렉터리 — 질의 구성 방식·결합도별 검색 전 조건 적용 효과(Δ)

## 1. 대상

- **캡션 원문(현재 원고 기준, `manuscript/_archive_20260819/0_paper_script.md` 236행):**
  **&lt;표 5&gt; 질의 구성 방식 및 조건-의미 결합도에 따른 검색 전 조건 적용의 효과(Δ) - 의미론적 정답 기준**
- **원고 내 위치:** 표 본문 226–234행(마크다운 표), 캡션 236행, 각주 238행(쌍 군집 부트스트랩·질의 수준 통계), 본문 해설 240–241행.
- **소속 절/RQ:** 5.2.3절 「검색 계획 평가 (RQ3)」. 검색 전 조건 적용(B4 prefilter)과 벡터 단독 검색(B2)의 의미론적 정답 nDCG@10 차이(Δ = B4 − B2)를 질의 표본(32/53/85)과 조건–의미 결합도(Cramér's V 밴드)로 층화한 표. 정본 실험 문서는 EXP02(RQ3·RQ4 대응)이다.

표에 인쇄된 행:

| 행 | Δ | 95% CI | 단위 |
|---|---:|---|---|
| 최초 표본 (32질의) | −0.0745 | [−0.136, −0.014] | 질의 |
| 확장 표본 (53질의) | +0.0197 | [−0.008, +0.050] | 질의 |
| 통합 표본 (85질의) | −0.0158 | [−0.047, +0.015] | 질의 |
| 저결합 V<0.3 (23쌍) | −0.0357 | [−0.094, +0.010] | 쌍(군집) |
| 고결합 V≥0.3 (2쌍) | +0.1335 | [+0.078, +0.356] | 쌍(군집) |

각주(238행): 전체 25쌍 군집 부트스트랩 5,000회; 고결합 질의 수준 Δ=+0.1335, 95% CI [+0.017, +0.249], 부트스트랩 p=0.024, Wilcoxon p=0.059(질의 10개 중 양수 7개); 고결합 군집 CI는 두 쌍 평균의 범위와 일치하는 참고 값.

## 2. 수치 ↔ 원천 매핑

| 원고 수치 | 원천 파일(data/ 사본) | 파일 내 위치 |
|---|---|---|
| Δ −0.0745 (32질의) | `data/significance_expanded.csv` | case=`원본-32 (재현)`, `delta` 열 |
| CI [−0.136, −0.014] | `data/significance_expanded.csv` | case=`원본-32 (재현)`, `ci` 열 `[-0.136,-0.014]` |
| Δ +0.0197 (53질의) | `data/significance_expanded.csv` | case=`확장-신규 (독립 확인)`, `delta` 열 |
| CI [−0.008, +0.050] | `data/significance_expanded.csv` | case=`확장-신규 (독립 확인)`, `ci` 열 |
| Δ −0.0158 (85질의) | `data/significance_expanded.csv` | case=`통합-85 (주 추정)`, `delta` 열 |
| CI [−0.047, +0.015] | `data/significance_expanded.csv` | case=`통합-85 (주 추정)`, `ci` 열 |
| Δ −0.0357 (저결합) | `data/significance_expanded.csv` case=`통합·low-coupling` `delta`; `data/t3_cluster_inference.json` `band V<0.3`→`mean` | 두 원천 일치 |
| CI [−0.094, +0.010] (저결합, 쌍 군집) | `data/t3_cluster_inference.json` | `band V<0.3`→`cluster_ci` = [−0.0941, 0.0098] (반올림) |
| 23쌍 (저결합) | `data/t3_cluster_inference.json` | `band V<0.3`→`n_pairs` = 23 |
| Δ +0.1335 (고결합) | `data/significance_expanded.csv` case=`통합·contrast` `delta`; `data/t3_cluster_inference.json` `band V>=0.3`→`mean` | 두 원천 일치 |
| CI [+0.078, +0.356] (고결합, 쌍 군집) | `data/t3_cluster_inference.json` | `band V>=0.3`→`cluster_ci` = [0.078, 0.3559] (반올림) |
| 2쌍 (고결합) | `data/t3_cluster_inference.json` | `band V>=0.3`→`n_pairs` = 2 |
| 질의 수 32/53/85 | `data/significance_expanded.csv` | 각 case 행의 `n` 열; `data/metrics_semantic.csv` `in_original_specs` True 32/False 53 재계산 일치 |
| 각주: 전체 25쌍 | `data/t3_cluster_inference.json` | `n_pairs`=25; `data/t3_coupling_curve.csv` (difficulty×relevance_def) 고유쌍 재계산 25 |
| 각주: 부트스트랩 5,000회 | `data/t3_cluster_inference.json` | `method` = "cluster bootstrap … B=5000, seed=20260712" |
| 각주: 질의 수준 CI [+0.017, +0.249] | `data/significance_expanded.csv` | case=`통합·contrast`, `ci` 열 `[0.017,0.249]` |
| 각주: 부트스트랩 p=0.024 | `data/significance_expanded.csv` | case=`통합·contrast`, `boot_p` = 0.0244 |
| 각주: Wilcoxon p=0.059 | `data/significance_expanded.csv` | case=`통합·contrast`, `wilcoxon_p` = 0.05934 |
| 각주: 질의 10개 중 양수 7개 | `data/significance_expanded.csv` | case=`통합·contrast`, `sign(neg/0/pos)` = `3/0/7`; `data/t3_coupling_curve.csv` V≥0.3 행 delta>0 재계산 7개 |
| 각주: 고결합 군집 CI = 두 쌍 평균의 범위 | `data/t3_coupling_curve.csv` | hour×stopped_vehicles 8질의 평균 +0.0780, time_of_day×stopped_vehicles 2질의 평균 +0.3559 → CI 끝점 [0.078, 0.3559]와 일치 |

고결합 2쌍의 구성(원천 확인 완료): `hour×stopped_vehicles` 8질의(`522vis:contrast:0035`–`0042`, 쌍 V=0.4478, 평균 Δ=+0.0780) + `time_of_day×stopped_vehicles` 2질의(`522vis:contrast:0009`–`0010`, 쌍 V=0.3993, 평균 Δ=+0.3559).

## 3. 사용 데이터셋

- **원본:** AI Hub 교차로 데이터셋(원고 [19]). 센서 채널(카메라 10) 클립 32,880개 + 시각 채널(카메라 11·22) 클립 52,462개에서 ±120초 센서 조인으로 47,098개 시각 클립을 확보하고, 교차로×시간대 층화·고정 시드 20260710으로 3,000개 클립을 표집. 원천 프레임/라벨: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/{frames_src,labels_src}` (실경로 `/hdd2/KIISE_datasociety/Datasets/...`, 대용량 미복사).
- **가공 산출물(캐노니컬):** `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded/` — Qwen2.5-VL-7B-Instruct 픽셀 전용 설명문 3,000문서, 85질의(수작업 32 + 사전선언 교차곱 기계 확장 53), strict qrels 6,809 / semantic qrels 24,872 (A6 감사 6/6 PASS). 전처리는 중간 프레임 1장→2–4문장·110토큰 탐욕 디코딩 캡션 생성과 3원천(센서 조건·픽셀 문서·주석 정답) 분리 결합이다.

## 4. 실험 체계

- **실행 스크립트(절대경로, `2026_KIISE/scripts/`):**
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_intersection_trisource_canonical.py` — 3원천 캐노니컬(85질의, 이중 qrels) 구축
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_text_embeddings.py` — BGE-M3 임베딩(1,024차원, L2 정규화, cuda:0, batch 32)
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/run_retrieval_baselines.py` — B0–B5 실행(FAISS `IndexFlatIP` + `rank_bm25.BM25Okapi`, top-100 평가, postfilter top-200, RRF k=60) → `results/trisource_expanded_b0_b5/`
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/verify_manuscript_numbers.py`, `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/run_full_verification_suite.py` — 표 5 수치 자동 대조(§6 표2+T3 블록)
- **모델·임베딩:** 문서=Qwen2.5-VL-7B-Instruct 캡션(fp16, greedy, 448px, 110토큰 상한); 검색 임베딩=BGE-M3(로컬 스냅샷 `Datasets/models/huggingface/BAAI--bge-m3`).
- **시드·파라미터:** 코퍼스 표집 시드 20260710; 쌍 군집 부트스트랩 B=5,000·시드 20260712; 질의 수준 paired bootstrap B=5,000 + Wilcoxon(정확한 시드는 기록 없음 — §7 참조); 결합도 밴드 임계 V<0.3 / V≥0.3 사전 선언.
- **사전등록/결과 문서(project_md/):**
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/canonical/experiments/EXP02_RETRIEVAL_PLAN_AND_COUPLING.md` (정본 실험 문서; data/에 사본 포함)
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/500_DATASETS_construction_noncircular_execution_20260710.md` (구축·실행 로그, 32→85 확장 규칙, 2026-07-11/07-12 정정 이력)
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/620_RESULTS_filtered_ann_real_predicates_20260710.md` (관련 부록)
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/codex_crosscheck_20260712/RESPONSE.md` (쌍 군집 추론 도입 경위 — 의사반복 정정)

## 5. 재현 방법

**(A) 원천 재실행 경로** (리포 루트 `/home/explorer/vectorDB/experiments/db/KIISE_datasociety`, `Datasets`는 `/hdd2/KIISE_datasociety/Datasets` 심링크):

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety
# 1) 캐노니컬(85질의) 구축 — 캡션 3,000개가 이미 있어야 함
python3 2026_KIISE/scripts/build_intersection_trisource_canonical.py   # → canonical_trisource_expanded/
# 2) BGE-M3 임베딩
python3 2026_KIISE/scripts/build_text_embeddings.py                    # → embeddings_trisource_expanded/bge-m3/
# 3) B0–B5 검색 실행
python3 2026_KIISE/scripts/run_retrieval_baselines.py                  # → results/trisource_expanded_b0_b5/
# 4) 유의성 집계(질의 수준 paired bootstrap 5000 + Wilcoxon; 표본·밴드 층화)
#    → significance_expanded.csv / t3_coupling_curve.csv (07-11 실행 체인의 후처리 단계, §7 비고 참조)
# 5) 쌍 군집 부트스트랩(B=5000, seed=20260712) → t3_cluster_inference.json
# 검증 스위트로 전체 대조:
python3 2026_KIISE/scripts/verify_manuscript_numbers.py
```

**(B) data/ 사본만으로 최소 재집계** (이 디렉터리에서 실행):

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/table5_dir/data
python3 - <<'EOF'
import pandas as pd, json
# 점추정 3종(32/53/85): 질의별 B4-B2 재계산
sm = pd.read_csv("metrics_semantic.csv")
pv = sm.pivot_table(index=["query_id","in_original_specs"], columns="strategy", values="ndcg_at_10").reset_index()
pv["d"] = pv["B4_prefilter_vector"] - pv["B2_vector_only"]
print("32:", round(pv[pv.in_original_specs].d.mean(),4), " 53:", round(pv[~pv.in_original_specs].d.mean(),4), " 85:", round(pv.d.mean(),4))
# 결합도 밴드 2종 + 쌍 수 + 고결합 부호/쌍 구성
t3 = pd.read_csv("t3_coupling_curve.csv"); t3["pair"]=t3.difficulty+"x"+t3.relevance_def
lo, hi = t3[t3.V<0.3], t3[t3.V>=0.3]
print("low:", round(lo.delta.mean(),4), f"({lo.pair.nunique()}쌍)", " high:", round(hi.delta.mean(),4), f"({hi.pair.nunique()}쌍) pos={(hi.delta>0).sum()}/10")
print(hi.groupby("pair").delta.mean().round(4).to_dict())
# CI·p값 재조회
print(pd.read_csv("significance_expanded.csv").to_string(index=False))
print(json.load(open("t3_cluster_inference.json")))
EOF
```

## 6. 포함 파일 목록

원천 디렉터리 `V = /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710` (실경로 `/hdd2/KIISE_datasociety/Datasets/...`), `R = /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE`.

| 원 절대경로 | 사본명 | 설명 |
|---|---|---|
| `V/results/trisource_expanded_b0_b5/significance_expanded.csv` | `data/significance_expanded.csv` | 표 5의 5행 전체 원천: 표본·밴드별 Δ, 질의 수준 95% CI, boot_p, Wilcoxon p, 부호 분포 |
| `R/paper_assets/20260712_codex_crosscheck_fixes/t3_cluster_inference.json` | `data/t3_cluster_inference.json` | 쌍 군집 부트스트랩(B=5000, seed=20260712) — 저·고결합 군집 CI와 쌍 수(23/2/25)의 정본 |
| `V/results/trisource_expanded_b0_b5/t3_coupling_curve.csv` | `data/t3_coupling_curve.csv` | 질의별(85) Δ·쌍 V·밴드 — 밴드 평균, 쌍 구성, 부호 수 재계산의 원천 |
| `V/results/trisource_expanded_b0_b5/metrics_semantic.csv` | `data/metrics_semantic.csv` | 전략×질의 의미론적 nDCG@10 등 지표 — 표본별 Δ 점추정 완전 재계산의 원천 |
| `V/results/trisource_expanded_b0_b5/metrics_summary.csv` | `data/metrics_summary.csv` | 전략×난이도 요약 지표(맥락용) |
| `V/results/trisource_expanded_b0_b5/run_manifest.json` | `data/run_manifest.json` | B0–B5 실행 매니페스트(전략, top-k, postfilter 200, 백엔드, 3,000문서/85질의/6,809 strict qrels) |
| `V/results/trisource_expanded_b0_b5/summary.md` | `data/summary.md` | 실행 직후 전략별 strict 요약·지연(맥락용) |
| `R/project_md/canonical/experiments/EXP02_RETRIEVAL_PLAN_AND_COUPLING.md` | `data/EXP02_RETRIEVAL_PLAN_AND_COUPLING.md` | 정본 실험 문서 — 설계·estimand·허용/금지 주장·원자산 경로 |

**미복사 대용량/이진 파일(경로 참조만):**
- `V/results/trisource_expanded_b0_b5/metrics_by_query.parquet` (strict 질의별 지표, parquet 정책상 미복사 — strict Δ+0.0983 재계산용)
- `V/results/trisource_expanded_b0_b5/retrieval_results.parquet` (원시 검색 결과 46,292행)
- `V/canonical_trisource_expanded/` (3.1MB: documents/queries/qrels 캐노니컬)
- `V/embeddings_trisource_expanded/bge-m3/` (13MB: `document_embeddings.npy` 3,000×1,024 등)
- `V/frames_src/`, `V/labels_src/`, `V/captions/` (원본 프레임 수십 GiB·라벨·캡션 샤드)

## 7. 검증

2026-07-23, data/ 사본을 python3(pandas)로 실제 재조회·재계산하여 원고(0_paper_script.md 226–241행) 수치와 대조했다. 방법 표기: **재계산**=사본의 질의/쌍 단위 원자료에서 다시 산출, **재조회**=사본에 저장된 값 직접 대조(부트스트랩 CI·p는 시드 고정 재실행 없이 저장값 대조).

| # | 원고 수치 | 사본 값 | 방법 | 판정 |
|---|---|---|---|---|
| 1 | Δ(32질의) −0.0745 | metrics_semantic 재계산 −0.0745; CSV delta −0.0745 | 재계산+재조회 | PASS |
| 2 | CI [−0.136, −0.014] | CSV ci `[-0.136,-0.014]` | 재조회 | PASS |
| 3 | Δ(53질의) +0.0197 | 재계산 +0.0197; CSV 0.0197 | 재계산+재조회 | PASS |
| 4 | CI [−0.008, +0.050] | CSV ci `[-0.008,0.050]` | 재조회 | PASS |
| 5 | Δ(85질의) −0.0158 | 재계산 −0.0158; CSV −0.0158 | 재계산+재조회 | PASS |
| 6 | CI [−0.047, +0.015] | CSV ci `[-0.047,0.015]` | 재조회 | PASS |
| 7 | Δ(저결합) −0.0357 | t3 V<0.3 재계산 −0.0357 (75질의); CSV·JSON −0.0357 | 재계산+재조회 | PASS |
| 8 | 저결합 군집 CI [−0.094, +0.010] | JSON cluster_ci [−0.0941, 0.0098] (반올림 일치) | 재조회 | PASS |
| 9 | Δ(고결합) +0.1335 | t3 V≥0.3 재계산 0.1335 (10질의); CSV·JSON 0.1335 | 재계산+재조회 | PASS |
| 10 | 고결합 군집 CI [+0.078, +0.356] | JSON cluster_ci [0.078, 0.3559] (반올림 일치) | 재조회 | PASS |
| 11 | 질의 수 32/53/85 | in_original_specs True 32 / False 53 / 계 85 | 재계산 | PASS |
| 12 | 쌍 수 저결합 23·고결합 2·전체 25 | t3 고유쌍 재계산 23/2/25; JSON n_pairs 일치 | 재계산+재조회 | PASS |
| 13 | 각주: 군집 부트스트랩 5,000회 | JSON method "…B=5000, seed=20260712" | 재조회 | PASS |
| 14 | 각주: 질의 수준 CI [+0.017, +0.249] | CSV 통합·contrast ci `[0.017,0.249]` | 재조회 | PASS |
| 15 | 각주: 부트스트랩 p=0.024 | CSV boot_p 0.0244 (반올림 일치) | 재조회 | PASS |
| 16 | 각주: Wilcoxon p=0.059 | CSV wilcoxon_p 0.05934 (반올림 일치) | 재조회 | PASS |
| 17 | 각주: 질의 10개 중 양수 7개 | t3 V≥0.3 delta>0 재계산 7개; CSV sign `3/0/7` | 재계산+재조회 | PASS |
| 18 | 각주: 고결합 구간이 두 쌍 평균의 범위와 일치 | 쌍 평균 재계산 +0.0780 / +0.3559 = CI 끝점 [0.078, 0.3559] | 재계산 | PASS |
| 19 | (제작 메모) 고결합 2쌍 구성 | hour×stopped_vehicles 8질의 +0.0780, time_of_day×stopped_vehicles 2질의 +0.3559 | 재계산 | PASS |

**총괄: 19/19 PASS. UNVERIFIED 없음.**

비고(정직 고지): 질의 수준 부트스트랩 CI·p(항목 2·4·6·14·15)는 `significance_expanded.csv`를 생성한 2026-07-11 후처리 단계의 독립 스크립트와 난수 시드가 리포에 보존되어 있지 않아 **동일 시드 재실행이 아닌 저장값 재조회**로 검증했다(알고리즘 자체는 project_md/500 문서에 paired bootstrap B=5,000 + Wilcoxon으로 기록, 점추정·표본수·부호는 전량 재계산 일치). 쌍 군집 CI(항목 8·10·13)는 시드 20260712가 method 문자열에 기록된 `t3_cluster_inference.json`을 정본으로 대조했다.
