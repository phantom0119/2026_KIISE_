#!/usr/bin/env python3
"""Verify manuscript numbers by re-aggregating the underlying result files.

Exit 0 only if ALL checks pass. Each check: (name, recomputed, quoted, tol).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

R2 = Path(__file__).resolve().parents[2]           # 2026_KIISE
DS = R2.parent / "Datasets" / "processed"
PB = R2 / "paper_assets" / "20260710_pillarB"
NC = R2 / "paper_assets" / "20260710_noncircular_collapse"
E1A = R2 / "paper_assets" / "20260711_e1a"
V = DS / "aihub_522_intersection" / "20260710"

ok, fail = [], []
def chk(name, got, want, tol=5e-4):
    got = float(got)
    (ok if abs(got - want) <= tol else fail).append(f"{name}: got {got:.4f} want {want}")

# ---------- §4 표1 collapse ----------
cc = pd.read_csv(NC / "vru_collapse_table.csv").set_index("strategy")
chk("T1 VRU B4 v1", cc.loc["B4_prefilter_vector", "v1_circular_ndcg10"], 0.9736)
chk("T1 VRU B4 strict", cc.loc["B4_prefilter_vector", "v2_strict_ndcg10"], 0.3174)
chk("T1 VRU B4 sem", cc.loc["B4_prefilter_vector", "v2_semantic_ndcg10"], 0.2974)
chk("T1 VRU B2 v1", cc.loc["B2_vector_only", "v1_circular_ndcg10"], 0.4476)
chk("T1 VRU B2 strict", cc.loc["B2_vector_only", "v2_strict_ndcg10"], 0.1845)
chk("T1 VRU B2 sem", cc.loc["B2_vector_only", "v2_semantic_ndcg10"], 0.2649)
chk("T1 VRU B1 strict", cc.loc["B1_bm25_only", "v2_strict_ndcg10"], 0.0918)
chk("T1 VRU B1 sem", cc.loc["B1_bm25_only", "v2_semantic_ndcg10"], 0.1607)
acc_s = pd.read_csv(DS / "aihub_intelligent_cctv/20260710_noncircular/results/acctv2_bgem3_b0_b5/metrics_summary.csv")
acc_all = acc_s[acc_s.difficulty == "all"].set_index("strategy")
chk("T1 AIHub B1 strict", acc_all.loc["B1_bm25_only", "ndcg_at_10"], 0.1111, 1e-3)
chk("T1 AIHub B4 strict", acc_all.loc["B4_prefilter_vector", "ndcg_at_10"], 0.8395, 1e-3)
acc_sem = pd.read_csv(DS / "aihub_intelligent_cctv/20260710_noncircular/results/acctv2_bgem3_b0_b5/metrics_semantic.csv")
g = acc_sem.groupby("strategy").ndcg_at_10.mean()
chk("§4 AIHub sem B1", g["B1_bm25_only"], 0.1667, 1e-3)
chk("§4 ko dense sem B2", g["B2_vector_only"], 0.82, 0.01)
# VRU semantic sign 18/85
vs = pd.read_csv(DS / "vru_accident/20260710_noncircular/results/vru2_bgem3_b0_b5/metrics_semantic.csv")
p = vs.pivot_table(index="query_id", columns="strategy", values="ndcg_at_10")
d = (p["B4_prefilter_vector"] - p["B2_vector_only"]).dropna()
chk("§4 sign neg", int((d < 0).sum()), 18, 0); chk("§4 sign zero", int((d == 0).sum()), 34, 0)

# ---------- §5 dataset stats ----------
sf = pd.read_parquet(V / "sensor_facets.parquet")
chk("§5 clips", len(sf), 32880, 0); chk("§5 intersections", sf.intersection_id.nunique(), 63, 0)
js = json.load(open(V / "visual_sensor_join_stats.json"))
chk("§5 join rate", js["join_rate_120s"], 0.9018, 1e-3)
chk("§5 median gap", js["median_gap_sec"], 0.0)
cap = pd.read_parquet(V / "captions/documents.parquet"); chk("§5 captions", len(cap), 3000, 0)
qx = [json.loads(l) for l in open(V / "canonical_trisource_expanded/queries.jsonl")]
chk("§5 nq", len(qx), 85, 0)
chk("§5 low", sum(1 for q in qx if q["coupling"] == "low"), 75, 0)
# rel densities on captioned base
join = pd.read_parquet(V / "visual_sensor_join.parquet")
ann = pd.read_parquet(V / "annotation_video_facets.parquet")
base = (cap[["visual_video_id", "split"]].merge(join[join.join_ok_120s], on=["visual_video_id", "split"])
        .merge(ann, on=["visual_video_id", "split"]))
chk("§5 parked", base.any_parked.astype(bool).mean(), 0.023, 2e-3)
chk("§5 dense", (base.max_objects >= 20).mean(), 0.022, 2e-3)
chk("§5 buses2", (base.max_bus >= 2).mean(), 0.082, 2e-3)
chk("§5 stopped", base.any_stopped.astype(bool).mean(), 0.212, 2e-3)
chk("§5 bikes2", (base.max_bike >= 2).mean(), 0.115, 2e-3)
p1a = pd.read_csv(PB / "P1_predicates_A.csv"); nat = p1a[p1a.kind == "natural"]
chk("§5 P1A nat lo", nat.selectivity.min(), 0.026, 1e-3); chk("§5 P1A nat hi", nat.selectivity.max(), 0.183, 1e-3)

# ---------- §6 표2 + T3 ----------
se = pd.read_csv(V / "results/trisource_expanded_b0_b5/significance_expanded.csv").set_index("case")
chk("T2 orig", se.loc["원본-32 (재현)", "delta"], -0.0745, 1e-3)
chk("T2 new", se.loc["확장-신규 (독립 확인)", "delta"], 0.0197, 1e-3)
chk("T2 comb", se.loc["통합-85 (주 추정)", "delta"], -0.0158, 1e-3)
chk("T2 low", se.loc["통합·low-coupling", "delta"], -0.0357, 1e-3)
chk("T2 contrast", se.loc["통합·contrast", "delta"], 0.1335, 1e-3)
t3 = pd.read_csv(V / "results/trisource_expanded_b0_b5/t3_coupling_curve.csv")
rho = t3.delta.rank().corr(t3.V.rank()); chk("§6 T3 rho", rho, 0.285, 5e-3)
# 2026-07-12 codex cross-check: pair-level (cluster) inference — pair = predicate field x relevance
t3["pair"] = t3.difficulty + "|" + t3.relevance_def
pa = t3.groupby("pair").agg(V=("V", "first"), delta=("delta", "mean"))
chk("§6 T3 pair-agg rho", pa.delta.rank().corr(pa.V.rank()), 0.272, 5e-3)
chk("§6 T3 n pairs", t3.pair.nunique(), 25, 0)
cj = json.loads((R2 / "paper_assets/20260712_codex_crosscheck_fixes/t3_cluster_inference.json").read_text())
chk("§6 cluster rho CI lo", cj["rho_cluster_ci"][0], -0.031, 2e-3)
chk("§6 cluster rho CI hi", cj["rho_cluster_ci"][1], 0.485, 2e-3)
chk("§6 low-band cluster CI hi>0", float(cj["band V<0.05"]["cluster_ci"][1] > 0), 1, 0)
pk = json.loads((R2 / "paper_assets/20260712_codex_crosscheck_fixes/parked_caption_crosstab.json").read_text())
chk("§6 parked mention 2596", pk["mention_parked"], 2596, 0)
chk("§6 parked negated 1242", pk["negated_mention"], 1242, 0)
b = t3[t3.V < 0.05].delta.mean(); chk("§6 T3 bin1", b, -0.099, 2e-3)
b4 = t3[t3.V >= 0.3].delta.mean(); chk("§6 T3 bin4", b4, 0.134, 2e-3)
sm = pd.read_csv(V / "results/trisource_expanded_b0_b5/metrics_semantic.csv")
strict = pd.read_parquet(V / "results/trisource_expanded_b0_b5/metrics_by_query.parquet")
ps = strict.pivot_table(index="query_id", columns="strategy", values="ndcg_at_10")
chk("§6 strict delta", (ps["B4_prefilter_vector"] - ps["B2_vector_only"]).mean(), 0.0983, 1e-3)
sag = strict.groupby("strategy").ndcg_at_10.mean()
chk("§6 B0 strict", sag["B0_metadata_only"], 0.218, 2e-3)
chk("§6 B2 strict", sag["B2_vector_only"], 0.059, 2e-3)

# ---------- §7 filtered-ANN ----------
m9A = pd.read_csv(PB / "B1_m9_control_A.csv").set_index("method")
m9B = pd.read_csv(PB / "B1_m9_control_B.csv").set_index("method")
chk("T3 A post", m9A.loc["postfilter_hnsw_K4x", "ctrl_minus_real"], 0.611, 1e-3)
chk("T3 B post", m9B.loc["postfilter_hnsw_K4x", "ctrl_minus_real"], 0.289, 1e-3)
chk("T3 A ss8", m9A.loc["single_stage_ivf_batch_np8", "ctrl_minus_real"], 0.627, 1e-3)
chk("T3 B ss32", m9B.loc["single_stage_ivf_batch_np32", "ctrl_minus_real"], 0.116, 1e-3)
chk("T3 A prefh", m9A.loc["prefilter_hnsw_ef64", "ctrl_minus_real"], 0.017, 1e-3)
cfA = pd.read_csv(PB / "B1_confirmatory_A.csv")
r = cfA[(cfA.band == "low(<0.05)") & cfA.pair.str.startswith("prefilter_hnsw_ef64 - postfilter")]
chk("§7 conf A low", float(r.delta.iloc[0]), 0.767, 1e-3)
A = pd.read_csv(PB / "filtered_ann_real_A.csv"); B = pd.read_csv(PB / "filtered_ann_real_B.csv")
rA = A[A.kind.isin(["natural", "composite"])]; rB = B[B.kind.isin(["natural", "composite"])]
chk("§7 A prefh recall", rA[rA.method == "prefilter_hnsw_ef64"].recall_at_10.mean(), 0.983, 1e-3)
chk("§7 B prefh recall", rB[rB.method == "prefilter_hnsw_ef64"].recall_at_10.mean(), 0.997, 1e-3)
chk("§7 A prefh p50", rA[rA.method == "prefilter_hnsw_ef64"].p50_ms.mean(), 0.038, 2e-3)
# K' sensitivity + escalation
k1 = rA[rA.method == "postfilter_hnsw_K1x"].recall_at_10.mean(); k4 = rA[rA.method == "postfilter_hnsw_K4x"].recall_at_10.mean()
chk("§7 A K' gain", k4 - k1, 0.065, 3e-3)
chk("§7 A escal", rA[rA.method == "single_stage_ivf_batch_np128"].predicate.nunique(), 25, 0)
# breakeven
ph = rA[rA.method == "prefilter_hnsw_ef64"]; pf = rA[rA.method == "prefilter_flat"]
jj = ph.merge(pf, on="predicate", suffixes=("_h", "_f"))
be = (jj.build_s_h * 1e3 / (jj.p50_ms_f - jj.p50_ms_h)).median()
chk("§7 A breakeven", be, 1869, 30)
# pgvector
pg = pd.read_csv(PB / "pgvector_ann_sweep.csv")
chk("§7 pg exact", float(pg[pg["index"] == "exact_seqscan"].p50_ms.iloc[0]), 218.2, 1.0)
pf4 = pd.read_csv(PB / "pgvector_filtered.csv")
r = pf4[(pf4["index"] == "b3_hnsw_m16") & pf4.predicate.str.contains("중동") & (pf4.iterative_scan == "relaxed_order")]
chk("T4 중동 relaxed", float(r.recall_at_10.iloc[0]), 0.302, 1e-3)
r = pf4[(pf4["index"] == "b3_hnsw_m16") & (pf4.predicate == "hour = 6") & (pf4.iterative_scan == "relaxed_order")]
chk("T4 hour relaxed", float(r.recall_at_10.iloc[0]), 0.984, 1e-3)
# grids + pareto
g5 = pd.read_csv(PB / "index_grid_522visual/index_benchmark.csv")
h = g5[(g5.N == 142000) & (g5.kind == "hnsw") & (g5.M == 32) & (g5.efSearch == 64)]
chk("§7 grid hnsw", float(h.recall_at_10.iloc[0]), 0.9992)
e2 = pd.read_csv(PB / "E2_retrieval_pareto.csv")
chk("§7 front", int(e2.pareto_front.sum()), 12, 0)

# ---------- §8 ----------
sq = json.load(open(R2 / "experiments_expansion/rag_vqa/results_full/summary_qwen.json"))
chk("§8 closed", sq["accuracy"]["closed"], 0.3083); chk("§8 oracle", sq["accuracy"]["oracle"], 0.7467)
sl = json.load(open(R2 / "experiments_expansion/rag_vqa/results_full/summary_llama3.json"))
chk("§8 llama oracle", sl["accuracy"]["oracle"], 0.69, 1e-3)
e1 = pd.read_csv(PB / "e1_pilot_configs.csv")
chk("T5 1K min rel", e1[e1.config != "flat_exact"].rel.min(), 0.974, 2e-3)
chk("T5 1K max rel", e1[e1.config != "flat_exact"].rel.max(), 1.053, 2e-3)
ep = pd.read_csv(E1A / "e1a_pilot_mediator.csv").set_index("config")
chk("T5 143K exact", ep.loc["flat_exact", "moment_recall@3"], 0.1203)
mp = pd.read_parquet(E1A / "e1a_vlm_minipilot.parquet")
lever = mp[mp.mediator_hit == 1].correct.mean() - mp[mp.mediator_hit == 0].correct.mean()
chk("T5 lever", lever, -0.020, 3e-3)
chk("T5 strong hit", mp[mp.config == "strong"].mediator_hit.mean(), 0.0556, 2e-3)

# ---------- manuscript-text guards (B1 recurrence + review fixes) ----------
MS = (
    R2
    / "manuscript"
    / "kiise_dbr_manuscript_v6_submission_revision.md"
).read_text()
def txt(name, cond):
    (ok if cond else fail).append(f"{name}")
txt(
    "TXT no internal B0-B5 strategy codes",
    __import__("re").search(r"(?<![A-Z0-9])B[0-5](?![A-Z0-9])", MS) is None,
)
txt("TXT no stale -0.14@", "−0.14 @" not in MS)
txt("TXT §8 low/high coupling effects", "저결합" in MS and "−0.0357" in MS and "고결합" in MS and "+0.1335" in MS)
txt("TXT cluster CI disclosed", "쌍 군집 95% 신뢰구간 [−0.031, +0.485]" in MS)
txt("TXT coupling exploratory", "결합도에 따른 차이는 확정된 효과가 아니라 탐색적 경향" in MS)
txt("TXT table7 cluster footnote", "쌍 군집 단위로 계산하면 저결합의 신뢰구간이 0을 포함" in MS)
txt("TXT caption task-coupling limitation", "완전한 과제 독립 문서는 아니다" in MS and "의미가 유사한 표현은 남을 수 있다" in MS)
txt("TXT perception wall partly-lifted", "InternVL3-8B 후속 점검" in MS and "균형 정확도 약 72%" in MS)
txt("TXT UCA citations", "UCA/UCF-Crime[20,21]" in MS)
txt("TXT prompt-target coupling disclosed", "프롬프트는 정답 라벨을 입력받지 않지만" in MS and "과제 관련 범주를 요청" in MS)
txt("TXT limited-sample scope disclosed", "고결합 표본이 두 쌍" in MS and "정답 적중 수도 적었으며" in MS)
txt("TXT F7 seed robustness", "일곱 무작위 시드" in MS and "최대 변동 범위는 0.047" in MS)
# ---- B-4 third-engine replication (2026-07-12, Amendment 5/5a) ----
b4 = pd.read_csv(R2 / "paper_assets/20260712_engine_replication/B4_results.csv")
def b4row(lane, corpus):
    r = b4[(b4.lane == lane) & (b4.corpus == corpus)]
    assert len(r) == 1, (lane, corpus, len(r)); return r.iloc[0]
w2a = b4row("w2-sweeping", "A")
chk("B4 w2xA delta", w2a.mean_delta, 0.0098, 5e-4)
chk("B4 w2xA headline", float(bool(w2a.headline_pass)), 1, 0)
m1b = b4row("m1-graph", "B")
chk("B4 m1xB delta", m1b.mean_delta, 0.0028, 5e-4)
chk("B4 m1xB headline", float(bool(m1b.headline_pass)), 1, 0)
chk("B4 m1xA delta", b4row("m1-graph", "A").mean_delta, 0.0140, 5e-4)
chk("B4 w2xB delta", b4row("w2-sweeping", "B").mean_delta, 0.0006, 5e-4)
chk("B4 ACORN B sign-flip", b4row("w3-acorn-cutoff0", "B").mean_delta, -0.0181, 5e-4)
mech = pd.read_csv(R2 / "paper_assets/20260712_engine_replication/B4_mechanism.csv")
mrho = mech[(mech.lane == "m1-graph") & (mech.corpus == "B")].iloc[0]
chk("B4 mechanism rho", mrho.rho, 0.676, 2e-3)
f7 = pd.read_csv(R2 / "paper_assets/20260712_engine_replication/B4_f7_seed_sensitivity.csv")
chk("B4 F7 max range", f7.max_range.max(), 0.047, 2e-3)
chk("B4 F7 draws", int(f7.n_draws.max()), 7, 0)
txt("TXT B4 table present", "<표 11\\> 전용 엔진의 실측·무작위 조건 재현율 차이" in MS and "재현율 Δ(무작위−실측)" in MS)
txt("TXT answer-propagation boundaries", "증거 회수·VLM 인식·과제 편향" in MS)
txt(
    "TXT B4 boundary disclosed",
    "92.3–93.4%" in MS and "40,000개 미만일 때 전수 검색" in MS,
)
txt("TXT B4 ACORN inversion", "ACORN[30]에서는 차이의 부호가 바뀌었다" in MS and "과대 또는 과소평가" in MS)
txt("TXT B4 no cross-engine latency", "절대 지연 시간은 같은 엔진 안에서만 비교" in MS)
# ---- UCA external validity (2026-07-12, Amendment 6/6a) ----
uc = json.loads((R2 / "paper_assets/20260712_uca_external/UCA_contrasts.json").read_text())
chk("UCA c1 strict delta", uc["c1_strict_pooled_positive"]["detail"]["mean"], 0.1501, 5e-4)
chk("UCA c1 pair ci lo", uc["c1_strict_pooled_positive"]["detail"]["pair_ci"][0], 0.1235, 5e-3)
chk("UCA c2 semantic container", uc["c2_semantic_container_negative"]["detail"]["mean"], -0.0485, 5e-4)
chk("UCA c3 negatives", uc["c3_negative_semantic_signs_exist"]["n_negative"], 68, 0)
chk("UCA c3 n", uc["c3_negative_semantic_signs_exist"]["n_semantic"], 129, 0)
chk("UCA tally 3of4", uc["tally"], 3, 0)
chk("UCA verdict", float(bool(uc["verdict_direction_consistent"])), 1, 0)
chk("UCA c4 fails", float(bool(uc["c4_label_gt_container_semantic"]["holds"])), 0, 0)
ur = pd.read_csv(R2 / "paper_assets/20260712_uca_external/UCA_results.csv")
b2s = float(ur[(ur.strategy=="B2_vector_only")&(ur.scoring=="semantic")].mean_ndcg10_primary.iloc[0])
b4s = float(ur[(ur.strategy=="B4_prefilter_vector")&(ur.scoring=="semantic")].mean_ndcg10_primary.iloc[0])
chk("UCA B2 semantic", b2s, 0.2470, 5e-4)
chk("UCA B4 semantic", b4s, 0.1998, 5e-4)
au = json.loads(Path("/hdd2/KIISE_datasociety/Datasets/processed/uca_anchor/20260712/canonical/A6_UCA_audit.json").read_text())
chk("UCA audit pass", float(bool(au["overall_pass"])), 1, 0)
chk("UCA e2 zero", au["e2_lexicon_8gram_overlap_count"], 0, 0)
txt("TXT UCA section present", "### 8.3 UCA 외부 대조" in MS and "세 건 이상 일치할 때 방향이 일치" in MS)
txt("TXT UCA c4 honest", "사건 클래스 조건의 우위는 재현되지 않았다" in MS and "−0.0558" in MS)
txt("TXT UCA scope kr", "탐색적 근거로 한정" in MS)
txt("TXT UCA scope en", "limited exploratory external contrast" in MS or "탐색적 근거로 한정" in MS)
txt("TXT data release scope", "원천 데이터는 각 라이선스를 따르며" in MS)
txt("TXT UCA future updated", "결합도가 0.3 이상인 질의도 전체 135개 중 3개" in MS and "고결합 표본" in MS)
txt("TXT abstract random-predicate control kr", "동일 선택도의 무작위 조건" in MS)
txt("TXT abstract random-predicate control en", "random predicates of equal selectivity" in MS)
txt("TXT no 'three workloads' claim", "reproduced across three workloads" not in MS)
txt("TXT UCA leakage audit", "라벨 키의 직접 재사용" in MS and "연속 8토큰 중복은 0건" in MS)
txt("TXT Idefics2 disclosed", "Idefics2-8B" in MS and "무작위 선택 수준인 9.1%에 가까워 보조 결과" in MS)
txt("TXT no link-misparse [n](", __import__("re").search(r"(?<!!)\[\d+\]\(", MS) is None)  # 브래킷 인용+괄호 연쇄 금지
txt("TXT fig3 exists+ref", "manuscript/Figure3.png" in MS and (R2/"manuscript/Figure3.png").exists())
txt("TXT fig1 exists+ref", "manuscript/Figure1.png" in MS and (R2/"manuscript/Figure1.png").exists())
txt("TXT fig2 exists+ref", "fig2_circularity_integrated_v6.png" in MS and (R2/"paper_assets/20260717_manuscript_visuals_v6/fig2_circularity_integrated_v6.png").exists())
txt("TXT refs first-appearance order", "[1] J.-B. Alayrac" in MS and "[61] Hugging Face" in MS)
txt(
    "TXT wall2 softened",
    "효과 부재를 뜻하지 않으며" in MS and "표본이 부족해" in MS,
)
txt(
    "TXT lever precision note",
    "답변 민감도를 판정할 표본이 부족해 대규모 생성을 중단" in MS,
)
# ---- submission structural + audit-fix guards ----
import re as _re
tbls=[int(m) for m in _re.findall(r"\*\*\\<표 (\d+)\\>", MS)]
txt("submission tables 1..12 sequential", tbls==list(range(1,13)))
figs=[int(m) for m in _re.findall(r"\*\*\\<그림 (\d+)\\>", MS)]
txt("submission figures 1..3 sequential", figs==list(range(1,4)))
txt("submission reflist 1..61", all(f"[{n}] " in MS for n in range(1, 62)) and "[62]" not in MS)
txt("submission no residual tokens", "[[표" not in MS and "[[그림" not in MS and "⟦" not in MS)
txt("submission qrels 6809/24872", "엄격한 정답 6,809행" in MS and "의미론적 정답 24,872행" in MS)
txt("submission sign 26/30/29", "더 낮은 질의 26개, 같은 질의 30개와 더 높은 질의 29개" in MS)
txt("submission UCA verdict table", "표 8" in MS and "+0.1501" in MS)
txt("submission evidence-ladder result", "대상 클립 설명문을 제공하면 69–75%" in MS)
txt(
    "submission conclusion and limitations structure",
    "## 11. 결론 및 한계" in MS
    and "## 12." not in MS
    and "종합 논의와 조건부 설계 원리" not in MS,
)
txt("submission taxonomy fix (UCA exploratory)", "탐색적 근거로 한정" in MS)
txt("submission idefics2 near-chance separated", "정확도 14.5%로 무작위 선택 수준인 9.1%에 가까워 보조 결과" in MS)
txt("submission compatibility grid disambiguated", "호환 조합 112개" in MS and "그림 3은 표 5의 112개 호환 구성 전체" in MS)
txt(
    "submission caption limitation disclosed",
    "과제 관련 범주를 요청하므로 완전한 과제 독립 문서는 아니다" in MS,
)
txt("submission systems taxonomy cites", all(f"[{n}]" in MS for n in [6,7,8,9]))
# ---- goal#3 three-boundary elevation (2026-07-13, P1/condb/gmanip assets) ----
import pandas as _pd
_cb=_pd.read_csv(R2/"paper_assets/20260712_perception_retest/condb_internvl3.csv")
_wp=_cb[_cb.qtype.isin(["bus","bikes"])]
def _disc(mode):
    m=_wp[_wp["mode"]==mode]
    return (m[m.gold=='yes'].pred=='yes').mean()-(m[m.gold=='no'].pred=='yes').mean()
chk("EP distractor discrimination +0.009", float(_disc("distractor")), 0.009, 6e-3)
chk("EP oracle discrimination +0.452", float(_disc("oracle")), 0.452, 6e-3)
_rt=_pd.read_csv(R2/"paper_assets/20260712_perception_retest/retest_internvl3.csv")
_rwp=_rt[_rt.qtype.isin(["bus","bikes"])]
_bal=(_rwp.groupby("gold").correct.mean().mean())
chk("EP internvl3 well-posed balanced 0.717", float(_bal), 0.717, 6e-3)
import json as _json
_gm=_json.loads((R2/"paper_assets/20260713_index_answer/gmanip_gate.json").read_text())
chk("EP gmanip structure recall spread 0.48", _gm["structure_recall_spread"], 0.48, 0.02)
txt("EP three-stage analysis", "증거 회수·VLM 인식·과제 편향" in MS)
txt("EP boundary-3 answer bias", "이진 응답 편향도 남았다" in MS)
txt("EP perception partly lifts", "균형 정확도 약 72%" in MS and "약 73%로 무관한 증거의 약 50%보다 높았지만" in MS)
txt("EP conclusion three-stage", "분리한 검증이 필요" in MS)
# ---- P9 entity-KG collapse (2026-07-13, Amendment 9 판정, §7.4) ----
_kg = json.loads((R2 / "paper_assets/20260713_kg/collapse_receipt.json").read_text())
chk("KG R4 KG==B4 all queries", float(bool(_kg["R4_KG_eq_B4_predicate_set_identity_all_queries"])), 1, 0)
_r5 = _kg["R5_kg_entity_overlap_within_filter"]
chk("KG entity-overlap strict 0.176", _r5["ndcg_strict_mean"], 0.176, 2e-3)
chk("KG random-filter floor 0.117", _r5["random_within_filter_floor_strict"], 0.117, 2e-3)
chk("KG B0 floor 0.218", _r5["B0_metadata_floor_strict_manuscript"], 0.218, 2e-3)
chk("KG median naive lift 0.002", _kg["gate"]["median_naive_lift(Amd.9 as-specified)"], 0.002, 2e-3)
chk("KG COLLAPSE_CONFIRMED", float(bool(_kg["gate"]["COLLAPSE_CONFIRMED (all three, as-specified naive design)"])), 1, 0)
_ke = _pd.read_csv(R2 / "paper_assets/20260713_kg/collapse_receipt_entities.csv").set_index("entity")
chk("KG bus mention 0.974", float(_ke.loc["bus", "mention_rate_naive"]), 0.974, 2e-3)
chk("KG pedestrian mention 0.981", float(_ke.loc["pedestrian", "mention_rate_naive"]), 0.981, 2e-3)
chk("KG parked negated 0.886", float(_ke.loc["parked", "negated_share_of_mentions"]), 0.886, 2e-3)
txt("KG §9.4 heading", "### 9.4 지식그래프 저장 구조의 보조 점검" in MS)
txt("KG §9.4 methodology", "센서 조건과 설명문 개체로 만든 지식그래프" in MS)
txt("KG §9.4 no independent channel", "독립적인 검색 이득을 확인하지 못했다" in MS)
txt(
    "KG §9.4 numbers",
    all(
        s in MS
        for s in [
            "중앙값 0.002",
            "nDCG@10은 0.176",
            "메타데이터 단독 검색 0.218",
        ]
    ),
)
txt("KG §9.4 established observation", "기존 신호의 재조합만으로" in MS)
txt(
    "real-time workload future work",
    "실시간 영상 유입과 메타데이터 갱신이 지속되는 동적 데이터베이스 워크로드" in MS
    and "p95/p99 꼬리 지연" in MS
    and "결과 신선도" in MS,
)
print(f"=== MANUSCRIPT NUMBER VERIFY: PASS {len(ok)} / FAIL {len(fail)} ===")
for f in fail:
    print("  FAIL:", f)
raise SystemExit(0 if not fail else 1)
