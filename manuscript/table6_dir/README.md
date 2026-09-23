# 표 6 관리 디렉터리 — AI Hub 교차로 vs UCA 메타데이터 조건 적용 효과 일치성 비교

이 디렉터리는 원고 표 6 하나를 처음부터 다시 만들거나 수치를 감사할 수 있도록, 캐노니컬 원천 파일 사본(`data/`)과 전 수치 대조 결과를 담은 자기완결 패키지다.

## 1. 대상

- **Caption 원문(현재 원고 기준)**: `**\<표 6\> AI Hub 교차로와 UCA의 메타데이터 조건 적용 효과 일치성 비교**`
- **원고 파일**: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/_archive_20260819/0_paper_script.md`
- **원고 내 위치**: 표 본문 243–248행, 캡션 250행, 해설 문단 252행. 표를 예고하는 문장은 239행("표 5와 표 6에 … 제시한다")과 241행("외부 데이터셋에서 재현되지 않았으므로(표 6)").
- **소속 절/RQ**: 5.2.3 검색 계획 평가 (**RQ3**) — 검색 전 조건 적용(prefilter) 효과가 외부 데이터셋 UCA/UCF-Crime에서 방향 재현되는지의 외적 타당성 점검. 판정 규칙은 사전등록(420 Amendment 6/6a)의 동결 대조 4건, "4건 중 3건 이상 일치 시 방향 일치".

표 6 인쇄 수치(4행 × 2열):

| 검증 항목 | AI Hub 결과 | UCA 결과 |
|---|---|---|
| 필수 제약의 효과 (엄격한 정답 Δ) | +0.0983 (향상) | +0.1501 (향상) |
| 관심 단서의 효과 (저결합 의미론적 Δ) | −0.0357 (하락) | −0.0485 (하락) |
| 검색 전 조건 적용이 불리한 질의 비율 | 30.6% (26/85) | 52.7% (68/129) |
| 고결합 시 추가 이득 여부 | +0.1335 > −0.0357 | −0.0558 < −0.0485 |

해설 문단(252행)에 병기된 수치: UCA 전체 135질의, 정상 영상 조건 5개 + 퇴화 질의 1개 제외 → 129질의 분석, Δ=+0.1501 [쌍-군집 95% CI 0.124, 0.179], Δ=−0.0485 [−0.130, 0.021], Δ=−0.0558 [−0.154, 0.042], 결합도 V≥0.3 질의 135개 중 3개.

## 2. 수치 ↔ 원천 매핑

Δ는 모두 nDCG@10의 (검색 전 조건 적용 − 벡터 단독 검색), 즉 전략 코드 B4−B2의 질의별 차이 평균이다.

| 원고 수치 (행) | 값 | 원천 파일 (data/ 사본 경로) | 파일 내 위치 (행/컬럼/키) |
|---|---|---|---|
| 표 6 R1 AI Hub | +0.0983 | `data/trisource_expanded_b0_b5/metrics_by_query.parquet` | strict 채점 질의별 nDCG@10을 (query_id × strategy)로 피벗 후 `mean(B4_prefilter_vector − B2_vector_only)` = 0.09826 (n=85) |
| 표 6 R1 UCA | +0.1501 | `data/20260712_uca_external/UCA_contrasts.json` | 키 `c1_strict_pooled_positive.detail.mean` (n=129) |
| 252행 R1 UCA CI | [0.124, 0.179] | `data/20260712_uca_external/UCA_contrasts.json` | 키 `c1_strict_pooled_positive.detail.pair_ci` = [0.1235, 0.179] (0.1235→0.124 반올림) |
| 표 6 R2 AI Hub | −0.0357 | `data/trisource_expanded_b0_b5/significance_expanded.csv` | 행 `통합·low-coupling`, 컬럼 `delta` (n=75질의/23쌍). 교차 확인: `data/20260712_codex_crosscheck_fixes/t3_cluster_inference.json` 키 `band V<0.3.mean`; 재계산: `data/trisource_expanded_b0_b5/t3_coupling_curve.csv`에서 `V<0.3` 행의 `delta` 평균 |
| 표 6 R2 UCA | −0.0485 | `data/20260712_uca_external/UCA_contrasts.json` | 키 `c2_semantic_container_negative.detail.mean` (n=30, duration_bin 컨테이너 계층) |
| 252행 R2 UCA CI | [−0.130, 0.021] | `data/20260712_uca_external/UCA_contrasts.json` | 키 `c2_semantic_container_negative.detail.pair_ci` = [−0.13, 0.021] |
| 표 6 R3 AI Hub | 30.6% (26/85) | `data/trisource_expanded_b0_b5/metrics_semantic.csv` | semantic 채점 질의별 B4−B2 델타 중 음수 26개 / 85개 = 30.588…% . 교차 확인: `significance_expanded.csv` 행 `통합-85 (주 추정)` 컬럼 `sign(neg/0/pos)` = 26/30/29 |
| 표 6 R3 UCA | 52.7% (68/129) | `data/20260712_uca_external/UCA_contrasts.json` | 키 `c3_negative_semantic_signs_exist` → `n_negative`=68, `n_semantic`=129 (68/129 = 52.713…%). 재계산: `data/20260712_uca_external/UCA_query_deltas.csv`에서 scoring=semantic ∧ ¬degenerate ∧ ¬normal_stratum 풀의 `delta<0` 개수 |
| 표 6 R4 AI Hub | +0.1335 (> −0.0357) | `data/trisource_expanded_b0_b5/significance_expanded.csv` | 행 `통합·contrast`, 컬럼 `delta` (V≥0.3, n=10질의/2쌍). 교차 확인: `t3_cluster_inference.json` 키 `band V>=0.3.mean`; 재계산: `t3_coupling_curve.csv` `V>=0.3` 행 `delta` 평균. 비교 대상 −0.0357은 R2와 동일 원천 |
| 표 6 R4 UCA | −0.0558 (< −0.0485) | `data/20260712_uca_external/UCA_contrasts.json` | 키 `c4_label_gt_container_semantic.label.mean` (n=69, video_class 라벨 계층); `holds: false` = "재현되지 않음" 판정. 비교 대상 −0.0485는 R2와 동일 원천 |
| 252행 R4 UCA CI | [−0.154, 0.042] | `data/20260712_uca_external/UCA_contrasts.json` | 키 `c4_label_gt_container_semantic.label.pair_ci` = [−0.1538, 0.042] |
| 252행 전체 135질의 | 135 | `data/uca_anchor_20260712/queries.jsonl` | 행 수 = 135. 교차 확인: `UCA_query_deltas.csv` semantic 고유 query_id 135 |
| 252행 정상 영상 조건 5개 | 5 | `data/20260712_uca_external/UCA_query_deltas.csv` | 컬럼 `normal_stratum`=True 고유 질의 5개 |
| 252행 퇴화 질의 1개 | 1 | `data/20260712_uca_external/UCA_query_deltas.csv` | 컬럼 `degenerate`=True 고유 질의 1개 (RoadAccidents×crash) |
| 252행 129질의 분석 | 129 | `data/20260712_uca_external/UCA_query_deltas.csv` | 135 − 5 − 1 = 129 (¬degenerate ∧ ¬normal_stratum 풀) |
| 252행 V≥0.3 질의 3개 | 3/135 | `data/20260712_uca_external/UCA_query_deltas.csv` | 컬럼 `coupling`="natural"(질의 자체 2×2 값-수준 phi ≥ 0.3) 고유 질의 3개 = `phi_value_level ≥ 0.3`인 3개. 주의: 필드-수준 Cramér's V 컬럼(`V_field_level`)로 세면 17개 — 원고의 "V≥0.3"은 질의 수준 결합도 라벨(값-수준 phi) 기준이다(`scripts/build_uca_workload.py` L140의 동결 규칙) |

## 3. 사용 데이터셋

- **AI Hub 교차로 (원본)**: AI Hub "교차로 위험(522) CCTV" 데이터 — 영상 32,880클립·교차로 63개소, 센서/주석/영상 3원천. 가공 캐노니컬: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded/` (3,000클립 Qwen2.5-VL-7B-Instruct 설명문 코퍼스, 85질의, 엄격 qrels 6,809행·의미론 qrels 24,872행). 전처리: 생산자 수준 3원천 분리로 순환성을 제거하고, 최소 양성 5개 규칙으로 32→85질의로 확장했다.
- **UCA/UCF-Crime (원본)**: UCA 주석 1,854 비디오·23,542문장 + UCF-Crimes.zip 96GB 원영상(비트 정확 검증). 가공 캐노니컬: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/uca_anchor/20260712/` (실경로 `/hdd2/KIISE_datasociety/Datasets/processed/uca_anchor/20260712/`, 심링크) — 6,432 세그먼트 문서(비디오당 ≤4 이벤트), Qwen2.5-VL 픽셀 전용 캡션, 135질의, 이중 qrels(strict 7,709행). 전처리: 렉시콘 무접촉 프롬프트로 캡션을 생성하고 A6 누출 감사(라벨키 0건·렉시콘 8-gram 중복 0건)를 통과시킨 뒤, 퇴화 1질의와 Normal 계층 5질의를 분석 풀에서 분리했다.

## 4. 실험 체계

- **사용 스크립트(절대경로)**:
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_intersection_trisource_canonical.py` — AI Hub 3원천 확장 워크로드(`canonical_trisource_expanded`) 구축
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/run_retrieval_baselines.py` — 두 레인 공통 B0–B5 전략 실행기(결과 디렉터리 `trisource_expanded_b0_b5/`, `uca_b0_b5/` 생성)
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_uca_corpus.py`, `.../caption_uca.py`, `.../build_uca_workload.py` — UCA 세그먼트 코퍼스·캡션·135질의 워크로드 구축(결합도 라벨 규칙: 값-수준 phi<0.3→low, ≥0.3→natural)
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/analyze_uca_external.py` — 동결 대조 4건(c1–c4) 판정 및 `UCA_contrasts.json`/`UCA_results.csv`/`UCA_query_deltas.csv` 산출(시드 `np.random.default_rng(20260712)`, 쌍/렉시콘 군집 부트스트랩 B=5,000)
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/verify_manuscript_numbers.py` — 저장소 전체 수치 가드(표 6 관련 체크 포함)
- **모델·임베딩**: 설명문 생성 Qwen2.5-VL-7B-Instruct(두 레인 공통, RQ3 통제 변인), 임베딩 BGE-M3(`BAAI--bge-m3`, dim 1024, normalize, batch 32, cuda:0), 벡터 검색 `faiss.IndexFlatIP`(Flat 전수), 어휘 검색 `rank_bm25.BM25Okapi`, B3/B4/B5는 외부 메타데이터 필터.
- **시드·핵심 파라미터**: 부트스트랩 시드 20260712·B=5,000(UCA 및 AI Hub 쌍-군집 추론 공통, `t3_cluster_inference.json`의 `method` 키 참조: predicate-field × relevance 25쌍), top_k∈{1,5,10,20}, max_rank 100, postfilter_doc_k 200, 지표 nDCG@10. UCA 1차 풀 = ¬퇴화 ∧ ¬Normal 계층(129질의), 판정 규칙 "4건 중 ≥3건 → 방향 일치"(실제 3/4 성립, c4 불성립).
- **사전등록/결과 문서(project_md/)**: `project_md/420_METHOD_prereg_pillarBE_design_20260710.md`(Amendment 6/6a 사전등록), `project_md/640_RESULTS_uca_external_20260712.md`(표 6 원천 결과 문서, `data/project_md/`에 사본), `project_md/630_RESULTS_answer_coupling_closure_20260711.md`(AI Hub 결합도 폐쇄), `project_md/430_METHOD_verification_framework_20260711.md`(검증 프레임).

## 5. 재현 방법

**(A) 원천 재실행 경로(처음부터)**

```bash
# 0) 환경: kiise-vlmdb conda env (pandas, numpy, faiss, rank_bm25), GPU 1장
# 1) AI Hub 레인 — 확장 워크로드 구축 + BGE-M3 임베딩 + B0–B5 실행
python3 scripts/build_intersection_trisource_canonical.py --expanded
python3 scripts/run_retrieval_baselines.py  # canonical_trisource_expanded → results/trisource_expanded_b0_b5/
#    → significance_expanded.csv(질의 표본·결합도 밴드 델타), t3_coupling_curve.csv 산출
# 2) AI Hub 쌍-군집 추론(−0.0357/+0.1335의 군집 CI) → paper_assets/20260712_codex_crosscheck_fixes/t3_cluster_inference.json
# 3) UCA 레인 — 코퍼스/캡션/워크로드 구축 후 동일 실행기
python3 scripts/build_uca_corpus.py && python3 scripts/caption_uca.py
python3 scripts/build_uca_workload.py       # 135질의 + 이중 qrels + A6 감사
python3 scripts/run_retrieval_baselines.py  # uca_anchor/.../results/uca_b0_b5/
python3 scripts/analyze_uca_external.py     # → paper_assets/20260712_uca_external/{UCA_contrasts.json,...}
# 4) 전 수치 가드
python3 scripts/verify_manuscript_numbers.py
```

**(B) data/ 사본만으로 재집계하는 최소 경로** (이 디렉터리에서 실행, pandas+pyarrow만 필요)

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/table6_dir
python3 - <<'EOF'
import json, pandas as pd
# R1 AI Hub: strict Δ(B4−B2) = +0.0983
mq = pd.read_parquet("data/trisource_expanded_b0_b5/metrics_by_query.parquet")
ps = mq.pivot_table(index="query_id", columns="strategy", values="ndcg_at_10")
print("R1 AIHub", round((ps.B4_prefilter_vector - ps.B2_vector_only).mean(), 4))
# R2/R4 AI Hub: −0.0357 / +0.1335 (+ 군집 CI)
se = pd.read_csv("data/trisource_expanded_b0_b5/significance_expanded.csv").set_index("case")
print("R2 AIHub", se.loc["통합·low-coupling","delta"], "R4 AIHub", se.loc["통합·contrast","delta"])
cj = json.load(open("data/20260712_codex_crosscheck_fixes/t3_cluster_inference.json"))
print("cluster CI", cj["band V<0.3"]["cluster_ci"], cj["band V>=0.3"]["mean"])
# R3 AI Hub: 26/85
sm = pd.read_csv("data/trisource_expanded_b0_b5/metrics_semantic.csv")
pv = sm.pivot_table(index="query_id", columns="strategy", values="ndcg_at_10")
d = (pv.B4_prefilter_vector - pv.B2_vector_only).dropna()
print("R3 AIHub", int((d<0).sum()), "/", len(d))
# UCA 열 전체: c1–c4 + CI
uc = json.load(open("data/20260712_uca_external/UCA_contrasts.json"))
print("R1 UCA", uc["c1_strict_pooled_positive"]["detail"]["mean"], uc["c1_strict_pooled_positive"]["detail"]["pair_ci"])
print("R2 UCA", uc["c2_semantic_container_negative"]["detail"]["mean"], uc["c2_semantic_container_negative"]["detail"]["pair_ci"])
print("R3 UCA", uc["c3_negative_semantic_signs_exist"]["n_negative"], "/", uc["c3_negative_semantic_signs_exist"]["n_semantic"])
print("R4 UCA", uc["c4_label_gt_container_semantic"]["label"]["mean"], uc["c4_label_gt_container_semantic"]["label"]["pair_ci"])
# 252행 카운트: 135 / 5 / 1 / 129 / V>=0.3 3개
qd = pd.read_csv("data/20260712_uca_external/UCA_query_deltas.csv")
uq = qd[qd.scoring=="semantic"].drop_duplicates("query_id")
print("counts", len(uq), int(uq.normal_stratum.sum()), int(uq.degenerate.sum()),
      len(uq)-int(uq.normal_stratum.sum())-int(uq.degenerate.sum()), int((uq.coupling=="natural").sum()))
EOF
```

## 6. 포함 파일 목록

`data/` 하위는 원천 디렉터리 구조를 보존한 서브폴더로 정리했고 파일명은 원본 그대로다.

| 원 절대경로 | 사본 | 설명 |
|---|---|---|
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260712_uca_external/UCA_contrasts.json` | `data/20260712_uca_external/UCA_contrasts.json` | UCA 동결 대조 c1–c4 판정 + 쌍-군집 CI — 표 6 UCA 열의 1차 원천 |
| `.../paper_assets/20260712_uca_external/UCA_results.csv` | `data/20260712_uca_external/UCA_results.csv` | UCA 전략 풀 nDCG@10 요약(B0–B5 × strict/semantic) |
| `.../paper_assets/20260712_uca_external/UCA_query_deltas.csv` | `data/20260712_uca_external/UCA_query_deltas.csv` | UCA 질의별 B4−B2 델타 + 계층/결합도 플래그(135질의 × 2채점) |
| `.../paper_assets/20260712_codex_crosscheck_fixes/t3_cluster_inference.json` | `data/20260712_codex_crosscheck_fixes/t3_cluster_inference.json` | AI Hub 쌍-군집 부트스트랩(B=5,000, seed 20260712) — −0.0357/+0.1335의 군집 CI |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/results/trisource_expanded_b0_b5/significance_expanded.csv` | `data/trisource_expanded_b0_b5/significance_expanded.csv` | AI Hub 표본·밴드별 Δ/CI/부호(26/30/29) — 표 5·표 6 AI Hub 열 원천 |
| `.../results/trisource_expanded_b0_b5/metrics_by_query.parquet` | `data/trisource_expanded_b0_b5/metrics_by_query.parquet` | AI Hub strict 질의별 지표(+0.0983 재계산용) |
| `.../results/trisource_expanded_b0_b5/metrics_semantic.csv` | `data/trisource_expanded_b0_b5/metrics_semantic.csv` | AI Hub semantic 질의별 지표(26/85 재계산용) |
| `.../results/trisource_expanded_b0_b5/metrics_summary.csv` | `data/trisource_expanded_b0_b5/metrics_summary.csv` | AI Hub 전략별 요약 지표 |
| `.../results/trisource_expanded_b0_b5/t3_coupling_curve.csv` | `data/trisource_expanded_b0_b5/t3_coupling_curve.csv` | AI Hub 질의별 결합도 V·델타 곡선(밴드 평균 재계산용) |
| `.../results/trisource_expanded_b0_b5/retrieval_results.parquet` | `data/trisource_expanded_b0_b5/retrieval_results.parquet` | AI Hub B0–B5 순위 원본(qrels로 nDCG 전체 재계산 가능) |
| `.../results/trisource_expanded_b0_b5/run_manifest.json` | `data/trisource_expanded_b0_b5/run_manifest.json` | AI Hub 실행 매니페스트(모델 경로·백엔드·파라미터·행 수) |
| `.../results/trisource_expanded_b0_b5/summary.md` | `data/trisource_expanded_b0_b5/summary.md` | AI Hub 실행 요약 메모 |
| `.../20260710/canonical_trisource_expanded/queries.jsonl` | `data/canonical_trisource_expanded/queries.jsonl` | AI Hub 85질의 정의(결합도 라벨 포함) |
| `.../20260710/canonical_trisource_expanded/qrels.tsv` | `data/canonical_trisource_expanded/qrels.tsv` | AI Hub 엄격 qrels 6,809행 |
| `.../20260710/canonical_trisource_expanded/qrels_semantic.tsv` | `data/canonical_trisource_expanded/qrels_semantic.tsv` | AI Hub 의미론 qrels 24,872행 |
| `.../20260710/canonical_trisource_expanded/A6_trisource_audit.json` | `data/canonical_trisource_expanded/A6_trisource_audit.json` | AI Hub 워크로드 누출 감사 영수증 |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/uca_anchor/20260712/results/uca_b0_b5/metrics_by_query.parquet` | `data/uca_b0_b5/metrics_by_query.parquet` | UCA 질의별 지표(analyze_uca_external.py 입력) |
| `.../uca_anchor/20260712/results/uca_b0_b5/metrics_summary.csv` | `data/uca_b0_b5/metrics_summary.csv` | UCA 전략별 요약 지표 |
| `.../uca_anchor/20260712/results/uca_b0_b5/retrieval_results.parquet` | `data/uca_b0_b5/retrieval_results.parquet` | UCA B0–B5 순위 원본 |
| `.../uca_anchor/20260712/results/uca_b0_b5/run_manifest.json` | `data/uca_b0_b5/run_manifest.json` | UCA 실행 매니페스트(6,432문서·135질의·qrels 7,709) |
| `.../uca_anchor/20260712/results/uca_b0_b5/summary.md` | `data/uca_b0_b5/summary.md` | UCA 실행 요약 메모 |
| `.../uca_anchor/20260712/build_manifest.json` | `data/uca_anchor_20260712/build_manifest.json` | UCA 코퍼스/워크로드 구축 매니페스트 |
| `.../uca_anchor/20260712/canonical/A6_UCA_audit.json` | `data/uca_anchor_20260712/A6_UCA_audit.json` | UCA 누출 감사(라벨키 0·렉시콘 8-gram 0) 영수증 |
| `.../uca_anchor/20260712/canonical/workload_table.csv` | `data/uca_anchor_20260712/workload_table.csv` | UCA 135질의 워크로드 표(계층·결합도) |
| `.../uca_anchor/20260712/canonical/queries.jsonl` | `data/uca_anchor_20260712/queries.jsonl` | UCA 135질의 정의 |
| `.../uca_anchor/20260712/canonical/qrels.tsv` | `data/uca_anchor_20260712/qrels.tsv` | UCA 엄격 qrels |
| `.../uca_anchor/20260712/canonical/qrels_semantic.tsv` | `data/uca_anchor_20260712/qrels_semantic.tsv` | UCA 의미론 qrels |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/640_RESULTS_uca_external_20260712.md` | `data/project_md/640_RESULTS_uca_external_20260712.md` | UCA 외적 타당성 결과 문서(표 6 서사 원천) |

**복사하지 않은 대용량/제외 파일(경로만 참조)**:

- `/hdd2/KIISE_datasociety/Datasets/processed/uca_anchor/20260712/frames/` (138MB, 프레임 이미지) 및 `embeddings/bge-m3/*.npy` (26MB, 임베딩 덤프)
- UCF-Crimes.zip 원영상 96GB(라이선스 학술 전용; 위치는 `data/uca_anchor_20260712/build_manifest.json` 참조)
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/uca_anchor/20260712/canonical/{documents,clips,metadata}.parquet` 및 `captions/` — 코퍼스 본문(수치 재계산에 불필요)
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded/{documents,clips,metadata}.parquet` 및 `embeddings_trisource_expanded/` — AI Hub 코퍼스 본문·임베딩
- 모델 가중치: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/models/huggingface/BAAI--bge-m3`

## 7. 검증

검증 방법: 아래 각 수치를 `data/` 사본에서 python3(pandas/json)로 실제 재조회·재계산하여 원고(2026-07-23 현재 `0_paper_script.md`)와 대조했다. 총 35개 검사 전부 실행했고 결과는 다음과 같다.

| 원고 수치 | data/ 재조회·재계산 값 | 판정 |
|---|---|---|
| R1 AI Hub +0.0983 | metrics_by_query.parquet 재계산 0.098265 (n=85) | PASS |
| R1 UCA +0.1501 | UCA_contrasts.json c1.mean = 0.1501 (n=129) | PASS |
| 252행 [0.124, 0.179] | c1.pair_ci = [0.1235, 0.179] (0.1235→0.124 반올림 일치) | PASS |
| R2 AI Hub −0.0357 | significance_expanded.csv 통합·low-coupling = −0.0357; t3_cluster_inference.json band V<0.3 mean = −0.0357; t3_coupling_curve.csv 재계산 −0.035674 | PASS |
| (표 5 병기 CI [−0.094, +0.010]) | t3_cluster_inference.json band V<0.3 cluster_ci = [−0.0941, 0.0098] | PASS |
| R2 UCA −0.0485 | c2.mean = −0.0485 (n=30) | PASS |
| 252행 [−0.130, 0.021] | c2.pair_ci = [−0.13, 0.021] | PASS |
| R3 AI Hub 30.6% (26/85) | metrics_semantic.csv 재계산: 음수 26 / 전체 85 = 30.588% → 30.6%; significance_expanded.csv sign 26/30/29 일치 | PASS |
| R3 UCA 52.7% (68/129) | c3 = 68/129 = 52.713% → 52.7%; UCA_query_deltas.csv 풀(¬퇴화∧¬Normal, semantic) 재계산 n=129·음수 68 | PASS |
| R4 AI Hub +0.1335 | significance_expanded.csv 통합·contrast = 0.1335; band V>=0.3 mean = 0.1335; t3_coupling_curve.csv 재계산 0.133548 | PASS |
| R4 AI Hub 비교식 +0.1335 > −0.0357 | 상기 두 값으로 성립 | PASS |
| R4 UCA −0.0558 | c4.label.mean = −0.0558 (n=69); c4.holds = false → "재현 안 됨" 서술과 일치 | PASS |
| R4 UCA 비교식 −0.0558 < −0.0485 | 상기 두 값으로 성립 | PASS |
| 252행 [−0.154, 0.042] | c4.label.pair_ci = [−0.1538, 0.042] (−0.1538→−0.154 반올림 일치) | PASS |
| 252행 UCA 전체 135질의 | queries.jsonl 135행; UCA_query_deltas.csv semantic 고유 질의 135 | PASS |
| 252행 정상 영상 조건 5개 제외 | UCA_query_deltas.csv normal_stratum=True 고유 질의 5 | PASS |
| 252행 퇴화 질의 1개 제외 | UCA_query_deltas.csv degenerate=True 고유 질의 1 | PASS |
| 252행 129질의 분석 | 135 − 5 − 1 = 129 = 재계산 풀 크기 | PASS |
| 252행 V≥0.3 질의 135개 중 3개 | UCA_query_deltas.csv coupling="natural" 고유 질의 3 (= phi_value_level≥0.3인 3개: video_class×fire 2건, video_class×crash 1건) | PASS* |

**PASS\* 각주(정직 보고)**: "V≥0.3 질의 3개"는 질의 수준 결합도 라벨 기준(질의 자체 2×2 값-수준 phi, `build_uca_workload.py` L140 동결 규칙 `phi<0.3→low, ≥0.3→natural`)으로만 3개다. 같은 CSV의 필드-수준 Cramér's V 컬럼(`V_field_level`)에 ≥0.3을 적용하면 17개가 되므로, 원고의 기호 "V"를 필드-수준 V로 읽으면 수치가 달라진다. AI Hub 쪽 결합도 밴드(V<0.3/V≥0.3)와 표기가 통일되어 있으나 UCA 쪽 연산 정의는 값-수준 phi라는 점을 원고 저자가 인지할 필요가 있다.

**종합: 19개 원고 수치 항목(재계산 검사 35건) 중 19건 PASS, FAIL 0건, UNVERIFIED 0건.** 반올림 외 불일치 없음. 표 6의 모든 셀과 252행 해설 문단의 모든 수치가 data/ 사본에서 재현된다.
