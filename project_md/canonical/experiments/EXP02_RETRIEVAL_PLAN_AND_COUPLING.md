# EXP02 — 검색 계획과 predicate–relevance 결합도

- 대응 질문: RQ3, RQ4
- 상태: 완료
- 주 데이터: 522 tri-source, 3,000 documents/85 queries
- 결과 지위: strict B4−B2는 확증, 연속 결합도 곡선은 탐색적

## 1. 목적

자연어 의미 조건과 구조화 predicate를 어느 단계에서 결합해야 하는지 평가한다. 특히 하나의 관련도 점수로 hard constraint와 soft intent를 섞지 않고, filter의 가치가 predicate–relevance 결합도와 어떻게 달라지는지 측정한다.

## 2. 고정 입력

- documents: Qwen2.5-VL-7B pixel-only captions 3,000개
- queries: 85개
- embeddings: BGE-M3, documents 3,000×1,024와 queries 85×1,024, L2 normalization
- dense engine: FAISS `IndexFlatIP`
- lexical engine: Okapi BM25
- rank depth: top-100 평가
- postfilter oversampling: top-200 고정
- hybrid: RRF \(k=60\)
- strict qrels: 6,809
- semantic qrels: 24,872

## 3. 처리군

| ID | 처리 | 의미 |
|---|---|---|
| B0 | metadata-only | predicate 판별력만 측정 |
| B1 | BM25 | 필터 없는 어휘 기준선 |
| B2 | vector-only | 필터 없는 dense 기준선 |
| B3 | postfilter | 전역 dense top-200 후 predicate |
| B4 | prefilter+vector | predicate 부분집합 exact dense |
| B5 | hybrid | 필터 부분집합의 BM25+dense RRF |

B0의 동순위는 clip ID의 결정론적 순서로 처리한다. B3와 B4는 같은 predicate evaluator를 공유한다.

## 4. 주 estimand

### 4.1 hard constraint

\[
\Delta_{\text{strict}}=
\operatorname{nDCG@10}_{\text{strict}}(B4)
-
\operatorname{nDCG@10}_{\text{strict}}(B2)
\]

strict qrels는 predicate를 정답 계약에 포함하므로 prefilter의 실용적 가치를 측정한다.

### 4.2 soft intent

\[
\Delta_{\text{semantic}}=
\operatorname{nDCG@10}_{\text{semantic}}(B4)
-
\operatorname{nDCG@10}_{\text{semantic}}(B2)
\]

semantic qrels에서는 predicate 밖 관련 문서를 제거하는 손실이 가능하다.

### 4.3 coupling

각 `intent×facet` 쌍의 모집단 Cramér's \(V\)와 질의별 \(\Delta_{\text{semantic}}\) 관계를 본다. \(V<0.3\)과 \(V\ge0.3\)을 사전 밴드로 사용한다.

## 5. 실행 절차

1. 5 predicate×5 intent 교차곱에서 최소 양성 규칙을 적용해 85질의를 재도출한다.
2. A6와 qrel logic을 통과시킨다.
3. B0–B5를 동일 canonical에서 실행한다.
4. strict와 semantic을 별도 metric table로 만든다.
5. B4−B2의 per-query paired difference를 계산한다.
6. query bootstrap과 25쌍 cluster bootstrap을 함께 계산한다.
7. 원본 32, 기계 확장 53, 통합 85를 분리 보고한다.
8. 질의별 부호 음/0/양과 결합도 band를 보존한다.

## 6. 결과

### 6.1 전체 전략

| 전략 | strict nDCG@10 | semantic nDCG@10 | 해석 |
|---|---:|---:|---|
| B0 metadata-only | 0.218 | 0.217 | 희소 사건·강한 predicate에서 센서 자체가 강함 |
| B1 BM25 | 0.017 | — | label restatement 제거 후 lexical signal 약화 |
| B2 vector-only | 0.059 | 0.170 | semantic 목적의 dense 기준선 |
| B3 postfilter | 0.152 | — | 소형 코퍼스의 top-200가 거의 포화 |
| B4 prefilter | 0.157 | 0.154 | strict 향상, semantic에서는 B2 하회 |
| B5 hybrid | 0.135 | — | 약한 BM25가 dense를 희석 |

semantic B1/B3/B5의 상세 수치는 원자산을 사용하며 표를 만들 때 다시 집계한다. 위 표의 `—`는 미실행이 아니라 이 문서에서 헤드라인으로 고정하지 않았다는 뜻이다.

### 6.2 B4−B2

| 표본 | semantic Δ [query 95% CI] |
|---|---:|
| 최초 수작업 32질의 | -0.0745 [-0.136,-0.014] |
| 기계 확장 53질의 | +0.0197 [-0.008,+0.050] |
| 통합 85질의 | -0.0158 [-0.047,+0.015] |
| 저결합 \(V<0.3\), n=75 | -0.0357 [-0.065,-0.008] |
| 자연결합 \(V\ge0.3\), n=10 | +0.1335 [+0.017,+0.249] |

strict 통합 Δ는 +0.0983 [0.068,0.133]이다.

밴드는 25쌍에 군집되어 있다. pair-cluster CI는 저결합 [-0.094,+0.010], 자연결합 [0.078,0.356]이며 자연결합은 2쌍뿐이다. 따라서 query CI만 보고 저결합 손실을 확증하지 않는다.

### 6.3 결합도 경향

- 질의 수준 Spearman \(\rho=0.285\)
- pair 평균 \(\rho=0.272\)
- pair-cluster \(\rho\) CI [-0.03,0.48]
- \(V<0.05\) 평균 Δ -0.099, n=27
- \(0.05\le V<0.15\) -0.002
- \(0.15\le V<0.3\) +0.003
- \(V\ge0.3\) +0.134

방향은 결합도가 커질수록 prefilter 손실이 줄거나 이득으로 바뀌는 경향과 정합하지만 cluster CI가 0을 포함하므로 탐색적이다.

### 6.4 자기 교정

- 원본 32: 음수 16/0 8/양수 8
- 신규 53: 음수 10/0 22/양수 21
- 통합 85: 음수 26/0 30/양수 29

초기 수작업 질의가 초저결합 손해 영역을 과대표집했으며, 사전선언된 교차곱 확장이 헤드라인을 -0.075에서 -0.016 비유의로 교정했다. 이 정정 자체가 기계적 질의 생성과 표본 분리 보고의 필요성을 보여준다.

## 7. 메커니즘 진단

주차 사건에서 dense 검색이 약한 이유를 caption 누락 하나로 설명하지 않는다.

- 3,000 captions 중 2,596개(87%)가 `parked`를 언급
- 그중 1,242개가 부정 표현
- 긍정 언급률은 주석 양성 52%, 음성 45%

즉 과언급과 부정문 표현 혼동 때문에 caption이 사건을 판별하지 못한다. 이는 문서 물질화 설계 문제이며 EXP04의 captioner ablation과 연결된다.

## 8. 결과 지위와 허용 주장

### 허용

- hard predicate 계약에서 B4는 B2를 유의하게 앞선다.
- semantic 목적에서는 통합 평균 우위가 검출되지 않았고 저결합에서 손실 가능성이 있다.
- 필터 효과는 관련도 계약과 질의 믹스에 의존한다.
- 결합도–효과 관계는 방향성 있는 탐색 가설이다.
- 기계적 질의 확장이 초기 selection bias를 드러냈다.

### 금지

- “prefilter는 항상 최적” 또는 “vector-only는 항상 최적”이라고 쓰지 않는다.
- low-coupling query CI만으로 새 intent/facet 일반화를 확증하지 않는다.
- \(V\)를 인과변수로 해석하지 않는다.
- B0의 높은 strict score를 semantic understanding으로 부르지 않는다.
- B3≈B4의 소형 3K 결과를 143K filtered-ANN에도 적용하지 않는다.

## 9. 원자산

- canonical: `Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded/`
- 결과: `Datasets/processed/aihub_522_intersection/20260710/results/trisource_expanded_b0_b5/`
- 요약: `2026_KIISE/paper_assets/20260710_noncircular_collapse/trisource_522_final_metrics.csv`
- significance/coupling: 위 결과 디렉터리의 `significance_expanded.csv`, `t3_coupling_curve.csv`
- 구축·실행 기록: `2026_KIISE/project_md/500_DATASETS_construction_noncircular_execution_20260710.md`

## 10. 변경 시 재실행 조건

- query 교차곱 또는 최소 양성 임계 변경
- strict/semantic qrel 정의 변경
- caption corpus·BGE snapshot 변경
- postfilter top-200 또는 RRF \(k\) 변경
- coupling 계산 모집단·임계 변경
- cluster 정의·bootstrap 또는 multiple-comparison family 변경

## 레거시 결과 문서 흡수 (2026-07-28)

paper_final.pdf(2026-07-23 제출본) SYNC 기준으로 아래 레거시 문서를 이 정본에 흡수한다. 원본은 (d)의 아카이브 경로에 보존한다.

### 670_P9_KG_extension_collapse_20260713.md

(a) 한 줄 요약: P9 entity-KG(그래프-구조) 확장을 사전등록(420 Amendment 9)→3-렌즈 적대검토→실측 3게이트로 검증해 "KG-as-index는 새 품질 축을 더하지 않는다"(COLLAPSE_CONFIRMED)로 KILL하고 정직 경계로 확정한 기록. 제출 논문 RQ4(§5.2.4)의 "지식그래프 재조합 Lift 중앙값 0.002 무이득" 문장의 실측 근거 문서다.

(b) EXP02 본문에 없는 고유 정보(수치·판정·절차·경로):

- 절차 규율: 사전등록 420 Amendment 9(경량 KG-as-index, 두 축=A6-KG 순환성 차단+질의유형×구조 비교, 게이트·SESOI 0.05·중단규칙) → 컴퓨트 전 3-렌즈 적대검토 17 에이전트, BLOCKER 3 전부 refuted=false·MAJOR 7 생존(`subagents/workflows/wf_b364e1b8-b13/`) → "합성 다중-홉 KG 우위" 가지 KILL(null-by-construction) → PI 결정 A(정직 경계 확정, B=관계형 2-홉 재설계는 보류). GPU 미사용.
- KILL 기전: tri-source 3채널(센서=필터/주석=정답/캡션=문서)에서 A6-KG가 주석 엣지=0을 강제하므로 KG 엣지=센서(=B0/B4)∪캡션(=B1/B2), 제3 신호 부재는 구조적 강제. 영수증 R1 채널 출처: sensor-facet edges 15,000 / caption-entity(긍정) edges 8,560 / annotation edges 0.
- 실측 3게이트(동결, 전부 TRUE→COLLAPSE_CONFIRMED):
  - G-i: KG predicate 순회 ≡ B4 prefilter, 85질의 집합-동일.
  - G-ii: naive lift 중앙값 0.002 < SESOI 0.05 (bus 언급률 97.4%, parked 부정 표현 88.6% — 근-완전 그래프라 엔티티 존재가 판별력 없음).
  - G-iii: KG 엔티티-중첩-필터내 strict nDCG 0.176(semantic 0.174) < B0 0.218 (필터내 랜덤 바닥 0.117, KG−B0=−0.042).
- 부정-인지(negation-aware) 수정의 한계: affirmative lift 중앙값 0.083으로 5개 유효 엔티티 중 3개(two_wheeler 0.083/dense 0.091/stopped 0.094)만 회복, bus 0.032·parked 0.001은 회복 불가이며 전체가 여전히 B0 아래 → 새 품질 축 아님. 본 문서 §7의 과언급+부정문 진단을 KG 축에서 정량 재확인한 것.
- 경로: 영수증 스크립트 `scripts/kg_collapse_receipt.py`, 산출물 `paper_assets/20260713_kg/`(collapse_receipt.json, collapse_receipt_entities.csv, collapse_receipt_perquery.csv, KG_COLLAPSE.md).
- Path B(보류→향후과제): intersection_id 관계형 2-홉만이 B4-표현불가 진짜 그래프 기전(dense/버스/주차 gold 비퇴화). 새 relevance 정의+자체 A6-KG 감사+재검토 선결, 별도 사전등록 필요.
- 교훈: CC-FR(κ 고아 신호)·P8(yes-편향 동어반복)·P9(제3 신호 부재) 연속 KILL — 다겹 오염된 retrieval-augmented VLM-QA에서 "이기는 구조" 설계가 적대검토에서 연속 붕괴하는 것은 우연이 아니라 문제의 성질이며, 정직 경계 규명 자체가 기여.

(c) 상충 서술과 정정:

- "원고 반영 §7.4 신설 + §10 향후과제"의 절 번호는 2026-07-13 당시 원고(verify_manuscript_v3.py 시대) 기준이다. 제출 정본 paper_final.pdf(2026-07-23)에서 이 결과는 RQ4 §5.2.4("전 신호 독립 이득 없음 … 지식그래프 재조합 Lift 중앙값 0.002 무이득")에 위치하며, §7.4라는 절 번호는 제출본 구조와 대응하지 않는다. Path B 향후과제 언급 위치도 제출본 기준으로 재확인 필요.
- 수치 상충 없음: lift 중앙값 0.002, strict 0.176 < B0 0.218, 랜덤 바닥 0.117, bus 97.4%, parked 부정 88.6% 모두 `paper_assets/20260713_kg/collapse_receipt.json`과 대조 일치하며 논문 RQ4 서술과 정합(2026-07-28 검증).

(d) 아카이브 경로: /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/670_P9_KG_extension_collapse_20260713.md
