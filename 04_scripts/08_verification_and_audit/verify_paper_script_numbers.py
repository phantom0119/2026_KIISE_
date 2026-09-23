#!/usr/bin/env python3
"""Regression guard for manuscript/_archive_20260819/0_paper_script.md (v3 revision, 2026-07-23).

Checks the contested headline numbers of the CURRENT manuscript against the
canonical artifacts identified in the 2026-07-23 verification sweep.
Replaces the retired verify_manuscript_numbers.py (which targets the deleted
v6 manuscript). Read-only; exits non-zero on any failure.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MS = ROOT / "manuscript" / "_archive_20260819" / "0_paper_script.md"
PA = ROOT / "paper_assets"

checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))


def approx(a, b, tol=5e-4):
    return abs(float(a) - float(b)) <= tol


text = MS.read_text(encoding="utf-8")

# 1) Banned stale numbers / phrases
for banned in [
    "0.418",
    "98.12",
    "16x7",
    "이미지 이미지",
    "용ㅇ",
    "평가 계약",
    "requires an end-to-end test",
    "caused by real-world data clustering",
    "수집 경로를 완전히 독립시킨",
    "각각 독립적으로 얻을 수 있어",
    "인접 단계의 대응 차이는 모두",
    "배제하고 결과의 통계적 유의성을 확보",
    "군집 강도를 직접 조작한 통제 실험은 수행하지 않았으므로",
    "증거 적중 표본을 확대한 대규모 생성 실험이 요구된다",
    "조건과 의미가 독립적인 저결합",
    "순수한 비순환 상태",
    "순환성이 배제된 평가 환경",
]:
    check(f"manuscript does NOT contain '{banned}'", banned not in text)

# 2) Required corrected statements
for required in [
    "0.181에서 0.352",
    "재현율 0.9812~0.9952",
    "정답 조건 주입 시 5.5배, 라벨 재진술 시 4.7배",
    "탐색적, 2쌍 한정",
    "Qwen3.5-9B 설명문 코퍼스와 85개 질의",
    "종단 비용이 아닌 데이터베이스 검색·색인 계층의 부분 비용",
    "표 3의 하락 전체를 누출 제거의 인과 효과로 귀속할 수 없으며",
    "95% 신뢰구간 [−2.0, 5.0], p=0.448",
    "UCA 54.04%",
    "과제-인지 0.1700에서 과제-중립 0.0855",
    "49.7% 상대 하락",
    "Spearman ρ는 0.383",
    "사전 승격 기준인 5개에 못 미쳤다",
    "자연 손실−shuffle 손실은 시내도로 +0.639",
    "교차로 +0.305",
    "bus +0.8%포인트",
    "bike −1.1%포인트",
    "대규모 VLM 호출을 수행하지 않았다",
    "원 연구의 사전등록 실험이 아니라 후속 통제 분석",
]:
    check(f"manuscript contains '{required}'", required in text)

# 2b) Citation/reference closure
body, refs = text.split("# 참고 문헌", maxsplit=1)
cited = {int(n) for n in re.findall(r"\[(\d+)\]", body)}
declared = {int(n) for n in re.findall(r"(?m)^\[(\d+)\]", refs)}
check("references are contiguous [1]..[40]", declared == set(range(1, 41)), f"declared={sorted(declared)}")
check("every declared reference is cited in the body", declared <= cited, f"uncited={sorted(declared-cited)}")
check("body contains no undefined citation", cited <= declared, f"undefined={sorted(cited-declared)}")
check("invalid Holm DOI is absent", "doi:10.2307/4615733" not in refs)

# 3) Table 4 five storage configs vs canonical CSV
cfg_csv = PA / "20260717_joint_image_caption_validation" / "configuration_summary.csv"
expected_tbl4 = {
    "caption": (0.0626, 0.1810, 1.155, 24.576),
    "representative_frame": (0.0625, 0.1865, 1.207, 24.576),
    "joint_image_caption": (0.0794, 0.2182, 1.243, 24.576),
    "multi_frame": (0.1014, 0.3518, 3.651, 68.395),
    "dual": (0.0889, 0.2933, 4.959, 92.971),
}
rows = {}
with cfg_csv.open() as f:
    for r in csv.DictReader(f):
        rows[(r["config"], r["scoring"])] = r
for name, (strict, sem, p50, mb) in expected_tbl4.items():
    key = f"{name}__B2_vector__flat"
    s_row = rows.get((key, "strict"))
    m_row = rows.get((key, "semantic"))
    ok = (
        s_row is not None and m_row is not None
        and approx(s_row["ndcg_at_10"], strict)
        and approx(m_row["ndcg_at_10"], sem)
        and approx(m_row["latency_p50_ms"], p50, 5e-3)
        and approx(m_row["vector_payload_mb"], mb, 5e-3)
    )
    check(f"Table4 {name} strict/semantic/p50/MB", ok, f"expected {strict}/{sem}/{p50}/{mb}")

# 4) RQ6 ladder accuracies (Qwen2.5-7B) vs official summary
sq = json.loads((ROOT / "experiments_expansion" / "rag_vqa" / "results_full" / "summary_qwen.json").read_text())
acc = sq["accuracy"]
for cond, val in [("closed", 0.3083), ("distractor", 0.5383), ("vector_only", 0.665), ("prefilter", 0.68), ("oracle", 0.7467)]:
    check(f"RQ6 ladder {cond}={val}", approx(acc[cond], val, 1e-4))
check("RQ6 n_per_config=600", sq["n_per_config"] == 600)

# 5) pgvector partial-index recall range 0.981~0.995 (sinnaedoro)
pv = PA / "20260713_db_design" / "pgvector_partial_vs_global.csv"
recalls = []
with pv.open() as f:
    for r in csv.DictReader(f):
        if r["strategy"].startswith("partial"):
            recalls.append(float(r["recall_at_10"]))
if recalls:
    check("partial-index recall min ~0.9812", approx(min(recalls), 0.9812, 2e-3), f"min={min(recalls):.4f}")
    check("partial-index recall max <= 0.9952+eps", max(recalls) <= 0.9962, f"max={max(recalls):.4f}")
else:
    check("partial-index rows found in pgvector_partial_vs_global.csv", False)

# 6) Caption-model ablation delta on 522 (+0.1022)
abl = PA / "20260715_caption_model_ablation" / "retrieval_metrics_all_models.csv"
vals = {}
with abl.open() as f:
    for r in csv.DictReader(f):
        if r["dataset"] == "522" and r["scoring"] == "semantic" and r["strategy"] == "B2_vector_only":
            vals[r["model"]] = float(r["ndcg_at_10"])
q25, q35 = vals.get("qwen25vl_7b"), vals.get("qwen35_9b")
if q25 is not None and q35 is not None:
    check("ablation 522 delta +0.1022", approx(q35 - q25, 0.1022, 1e-3), f"delta={q35-q25:.4f}")
else:
    check("ablation rows located", False, f"models found: {sorted(vals)}")

# 7) Controlled supplement: artifact gates and exact manuscript-facing values
supp = PA / "20260723_controlled_supplement"
e0 = json.loads((supp / "e0_prompt_target_ablation" / "summary.json").read_text())
check("E0 aware nDCG=0.1700", approx(e0["primary"]["task_aware"], 0.170033, 1e-6))
check("E0 neutral nDCG=0.0855", approx(e0["primary"]["task_neutral"], 0.085508, 1e-6))
check("E0 relative drop=49.7%", approx(e0["primary"]["relative_drop"], 0.497109, 1e-6))
check("E0 adverse frozen gate passed", e0["adverse_prompt_sensitivity_large_by_frozen_rule"])

s2 = json.loads((supp / "s2_blocked_coupling" / "summary.json").read_text())
check("S2 rho=0.3826", approx(s2["primary_spearman"]["rho"], 0.382602, 1e-6))
check("S2 promotion gate failed", not s2["promotion_gate"]["all_pass"])
check(
    "S2 high-fold direction 5/5 positive",
    all(float(value) > 0 for value in s2["high_fold_mean_delta"].values()),
)

s3 = json.loads((supp / "s3_cluster_mechanism" / "combined_summary.json").read_text())
check("S3 all 2-corpus x 2-index cells pass", s3["all_four_cells_pass"])
for cell, expected in [
    ("A_hnsw", 0.638869),
    ("A_ivf", 0.676837),
    ("B_hnsw", 0.304548),
    ("B_ivf", 0.234416),
]:
    check(
        f"S3 {cell} natural-shuffle delta",
        approx(s3["cells"][cell]["natural_minus_shuffle_loss"], expected, 1e-6),
    )

s4 = json.loads((supp / "s4_retrieval_population" / "summary.json").read_text())
check("S4 eligible population=2739", s4["reconstruction"]["eligible_source_rows"] == 2739)
check(
    "S4 both task-relevant retrieval gates failed",
    not s4["categories"]["bus_count"]["retrieval_gate"]["all_pass"]
    and not s4["categories"]["bike_count"]["retrieval_gate"]["all_pass"],
)

n_fail = sum(1 for _, ok, _ in checks if not ok)
for name, ok, detail in checks:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))
print(f"\ntotal={len(checks)} fail={n_fail}")
sys.exit(1 if n_fail else 0)
