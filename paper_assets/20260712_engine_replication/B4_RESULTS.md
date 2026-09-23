# B-4 제3 엔진 기전 재현 — 결과 정본 (2026-07-12)

프리레지: 420 Amendment 5 + 5a (3-렌즈 적대 검토 8건 확정 반영 후 확증 계산).
엔진: Milvus v2.6.0(pymilvus 3.0.0) · Weaviate 1.35.3(client 4.22.0), venv `Datasets/envs/kiise-engines`(numpy 2.5.1).
데이터: B-1 동결 GT(`inputs_{A,B}.npz`; qidx_B sha256 8635a761…), P1 양방향 어서션 A29/B25, G-ingest(비필터 recall 0.996/0.997)·G-filter(엔진 카운트 108/108 일치) 전 게이트 통과.

## 확증 (Holm 4-가족: {m1-graph, w2-sweeping}×{A,B}, 자연 predicate, Δ=recall(ctrl)−recall(real))

| 셀 | n쌍 | Δ평균 | predicate CI | facet-가족 CI | Holm p | 헤드라인(이중 CI+Holm) |
|---|---|---|---|---|---|---|
| **Weaviate w2-sweeping × A** | 24 | **+0.0098** | [0.0049, 0.0159] | [0.0037, 0.0265] | **0.00007** | **PASS** |
| **Milvus m1-graph × B** | 18 | **+0.0028** | [0.0009, 0.0049] | [0.0005, 0.0047] | **0.0224** | **PASS** |
| Milvus m1-graph × A | 6 | +0.0140 | [0.0079, 0.0220] | [0.0099, 0.0322] | 0.0625 | 방향 일치(n=6, Wilcoxon 입도 한계) |
| Weaviate w2-sweeping × B | 22 | +0.0006 | [0.0000, 0.0015] | [0.0002, 0.0017] | 0.121 | 방향 일치(효과 극소) |

4/4 셀 방향 일치(실측 predicate 결손 > 무작위), 2/4 Holm-유의. **크기는 faiss naive 계획(+0.61/+0.29)의 1/40~1/200** — 재현의 본질은 "엔진도 무너진다"가 아니라 **"기전은 실재하며, 상용 엔진은 그것을 알고 다층 완화를 배치했고, 완화 밖 체제에 잔여 결손이 남는다"**.

## 완화 레인 (기술; 혼입 금지 분리)

- **Milvus BF 폴백**: filtered-out ≥ ~0.93(knowhere 상수; 본 데이터 경계 (0.923, 0.934] 실측)에서 무성 exact 전환 — A 18쌍·B 4쌍 양팔 recall≥0.9986, Δ≤0.0014. 설정 불가·비문서화 선택도 절벽.
- **Weaviate flat cutoff**: subset<40,000 brute-force — A 26쌍·B 16쌍 recall≈1.0 (w1 기본).
- **Weaviate ACORN(w3, cutoff=0)**: 이질적·**부호 역전 경향**(A +0.0025 n.s., B −0.0181 [−0.046,+0.003]); 기전 상관 **음수**(ρ −0.396/−0.304) — ACORN은 필터-통과 진입점·다중 홉 확장으로 **군집을 역이용**해 무작위 마스크가 오히려 불리. 무작위-마스크 벤치마크는 이 경로에서 부호까지 왜곡한다.
- 합성 predicate(기술): m1-graph-composite A +0.0116, w2-composite A +0.0090 — 자연과 정합.

## 기전 (secondary)

Milvus m1-graph×B: Δ↔GT-군집심도 Spearman **ρ=0.676 (p=0.002, n=18)** — faiss(B-1: 0.70/0.78)와 같은 기전이 그래프 체제에 잔존. Weaviate sweeping ρ=+0.25~0.31(n.s.), ACORN ρ 음수.

## 지연 (엔진 내 상대 서술만; 클라이언트 RT p50 중앙값)

Weaviate A: sweeping 14.2ms vs acorn 5.3ms — sweeping의 준-exact 재현율은 ~2.7× 지연 대가(B에선 4.4 vs 5.2 동급). Milvus ~3ms. **엔진 간 절대 비교 금지(계측 경계 상이).**

## F7 — M9 대조군 시드 민감도 (r=7 드로우: B-1 원 시드 + 20260712 r0 + r1..5)

대조군 재현율의 드로우 간 SD: postfilter K1x 평균 0.0050(A)/0.0102(B), 최대 범위 0.028/0.047; single-stage 평균 SD ≤0.002. **M9 과대평가(+0.29~+0.63) 대비 1~2자릿수 작음 → M9 결론은 대조군 무작위성에 견고.** (`B4_f7_seed_sensitivity.csv`)

## 파일

`B4_results.csv`(확증+기술 전 레인), `B4_mechanism.csv`, `B4_f7_seed_sensitivity.csv`, `engine_{milvus,weaviate}_{A,B}*.csv|manifest.json`, `retro_gates_report.json`, `engine_weaviate_A_relabel_note.json`(w2→w3 재라벨 이력), 리뷰 산출물 wf_1ad02af8-bf5.
컬렉션 `kiise_{a,b}_b4`(Milvus)·`Kiise_{a,b}_b4`(Weaviate)는 보존(재실행 시 G-ingest 재통과 필수).
