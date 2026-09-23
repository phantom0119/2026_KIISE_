#!/usr/bin/env python3
"""Verify the current working master, including the 2026-07-17 additions.

Run this script in the kiise-vlmdb environment. It first delegates the legacy
164-check verifier, then validates the latest controlled interventions, joint
ablation, external control, high-recall seed study, manuscript structure, and
claim boundaries against their source artifacts.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

import pandas as pd


KIISE = Path(__file__).resolve().parents[2]
SCRIPTS = KIISE / "scripts"
MANUSCRIPT = (
    KIISE
    / "manuscript"
    / "kiise_dbr_manuscript_v5_complete_research_working_draft.md"
)
DOCX = MANUSCRIPT.with_suffix(".docx")
PDF = MANUSCRIPT.with_suffix(".pdf")
JOINT = KIISE / "paper_assets" / "20260717_joint_optimization_validation"
CROSSCHECK = KIISE / "paper_assets" / "20260717_ablation_agent_crosscheck"
CIRCULARITY = CROSSCHECK / "qwen_aligned_circularity"
HIGH_RECALL = CROSSCHECK / "qwen2048_high_recall_5seed"
MEVA = JOINT / "meva_same_encoder_control"

passed: list[str] = []
failed: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    target = passed if condition else failed
    suffix = f" — {detail}" if detail else ""
    target.append(f"{name}{suffix}")


def close(name: str, observed: object, expected: float, tolerance: float = 5e-7) -> None:
    value = float(observed)
    check(
        name,
        abs(value - expected) <= tolerance,
        f"observed={value:.9f}, expected={expected:.9f}",
    )


def select_one(frame: pd.DataFrame, **conditions: object) -> pd.Series:
    mask = pd.Series(True, index=frame.index)
    for column, value in conditions.items():
        mask &= frame[column].astype(str) == str(value)
    selected = frame[mask]
    if len(selected) != 1:
        raise AssertionError(f"expected one row for {conditions}, got {len(selected)}")
    return selected.iloc[0]


# The historical source/manuscript checks remain authoritative for the original
# body. Use the same interpreter so the pinned parquet reader is retained.
legacy = subprocess.run(
    [sys.executable, str(SCRIPTS / "verify_manuscript_numbers.py")],
    cwd=KIISE.parent,
    capture_output=True,
    text=True,
)
check(
    "legacy manuscript verifier 164/164",
    legacy.returncode == 0
    and "PASS 164 / FAIL 0" in (legacy.stdout + legacy.stderr),
    (legacy.stdout + legacy.stderr).strip().splitlines()[-1],
)


# Joint 522 grid and same-encoder storage control.
config = pd.read_csv(JOINT / "configuration_summary.csv")
storage = pd.read_csv(JOINT / "same_encoder_storage_control.csv")
paired = pd.read_csv(JOINT / "paired_bootstrap_comparisons.csv")
fidelity = pd.read_csv(JOINT / "task_fidelity_corrected.csv")

check("joint grid has 91 configurations", config.config.nunique() == 91)
check("joint grid has 182 scoring summaries", len(config) == 182)
check(
    "joint grid covers 85 queries in every summary",
    set(config.queries.astype(int)) == {85},
)
close(
    "caption B2 Flat semantic anchor",
    select_one(storage, representation="caption", scoring="semantic").ndcg_at_10,
    0.181005,
)
close(
    "caption B2 Flat strict anchor",
    select_one(storage, representation="caption", scoring="strict").ndcg_at_10,
    0.062641,
)
close(
    "multi-frame B2 Flat semantic",
    select_one(storage, representation="multi_frame", scoring="semantic").ndcg_at_10,
    0.351787,
)
close(
    "multi-frame B2 Flat strict",
    select_one(storage, representation="multi_frame", scoring="strict").ndcg_at_10,
    0.101369,
)

multi_sem = select_one(
    paired,
    family="storage",
    scoring="semantic",
    candidate="multi_frame__B2_vector__flat",
    baseline="caption__B2_vector__flat",
)
multi_strict = select_one(
    paired,
    family="storage",
    scoring="strict",
    candidate="multi_frame__B2_vector__flat",
    baseline="caption__B2_vector__flat",
)
close("multi−caption semantic delta", multi_sem.mean_delta, 0.170783)
close("multi−caption semantic cluster CI low", multi_sem.cluster_ci_lo, 0.017792)
close("multi−caption semantic cluster BH q", multi_sem.q_cluster_bh, 0.0852)
close("multi−caption strict delta", multi_strict.mean_delta, 0.038728)
close("multi−caption strict cluster BH q", multi_strict.q_cluster_bh, 0.0888)

b4_strict = select_one(
    paired,
    family="search",
    scoring="strict",
    candidate="multi_frame__B4_prefilter__flat",
    baseline="multi_frame__B2_vector__flat",
)
b4_semantic = select_one(
    paired,
    family="search",
    scoring="semantic",
    candidate="multi_frame__B4_prefilter__flat",
    baseline="multi_frame__B2_vector__flat",
)
close("multi B4−B2 strict delta", b4_strict.mean_delta, 0.161163)
close("multi B4−B2 semantic delta", b4_semantic.mean_delta, -0.093236)
close(
    "multi B4 HNSW ef64 task fidelity",
    select_one(
        fidelity, config="multi_frame__B4_prefilter__hnsw_ef64"
    ).task_recall_to_exact_at_10,
    0.870588,
)


# Qwen-aligned controlled circularity intervention.
circular = pd.read_csv(CIRCULARITY / "summary.csv")
circular_delta = pd.read_csv(CIRCULARITY / "contrasts.csv")
close(
    "C1 Qwen clean semantic",
    select_one(
        circular, experiment="C1", condition="qwen_clean", scoring="semantic"
    ).ndcg_at_10,
    0.181005,
)
close(
    "C1 oracle semantic",
    select_one(
        circular,
        experiment="C1",
        condition="oracle_qrel_filter",
        scoring="semantic",
    ).ndcg_at_10,
    1.0,
)
close(
    "C1 random same-selectivity semantic",
    select_one(
        circular,
        experiment="C1",
        condition="random_same_selectivity_mean",
        scoring="semantic",
    ).ndcg_at_10,
    0.120041,
)
c1 = select_one(
    circular_delta,
    experiment="C1",
    scoring="semantic",
    treatment="oracle_qrel_filter",
    control="qwen_clean",
)
close("C1 oracle−clean delta", c1.mean_delta, 0.818995)
close("C1 cluster CI low", c1.cluster_ci_lo, 0.737950)
close(
    "C2 contaminated semantic",
    select_one(
        circular,
        experiment="C2",
        condition="qwen_full_contamination",
        scoring="semantic",
    ).ndcg_at_10,
    0.853687,
)
c2 = select_one(
    circular_delta,
    experiment="C2",
    scoring="semantic",
    treatment="qwen_full_contamination",
    control="qwen_clean",
)
close("C2 contaminated−clean delta", c2.mean_delta, 0.672682)
close("C2 cluster CI low", c2.cluster_ci_lo, 0.567532)


# Same-encoder external control.
meva_paired = pd.read_csv(MEVA / "paired_bootstrap.csv")
meva_frame = select_one(
    meva_paired,
    family="storage",
    scoring="semantic",
    candidate="frame__B2_vector__flat",
)
meva_dual = select_one(
    meva_paired,
    family="storage",
    scoring="semantic",
    candidate="dual__B2_vector__flat",
)
close("MEVA frame−caption semantic delta", meva_frame.mean_delta, 0.023937)
close("MEVA frame cluster CI low", meva_frame.cluster_ci_lo, -0.029209)
close("MEVA frame cluster BH q", meva_frame.q_cluster_bh, 0.4008)
close("MEVA dual−caption semantic delta", meva_dual.mean_delta, 0.069016)
close("MEVA dual cluster CI low", meva_dual.cluster_ci_lo, 0.036879)


# Five-seed high-recall index study.
high = pd.read_csv(HIGH_RECALL / "summary.csv")
check("high-recall study has six settings", len(high) == 6)
check("high-recall study has five seeds per setting", set(high.seeds) == {5})
h512 = select_one(high, structure="hnsw", efSearch="512.0")
ivf256 = select_one(high, structure="ivfflat", nprobe="256.0")
close("HNSW ef512 recall mean", h512.recall_mean, 0.998118)
close("HNSW ef512 recall minimum", h512.recall_min, 0.996471)
close("HNSW ef512 median p95", h512.latency_p95_median_ms, 5.757020)
check("HNSW ef512 passes all-seed 0.99 gate", bool(h512.all_seeds_recall_ge_099))
close("IVF nprobe256 recall minimum", ivf256.recall_min, 0.998824)
close("IVF nprobe256 median p95", ivf256.latency_p95_median_ms, 37.587413)


# Explicit verifier scopes.
for name, path, expected in [
    ("joint metric·artifact gate", JOINT / "independent_verification.json", 32),
    (
        "treatment·statistics gate",
        CROSSCHECK / "treatment_integrity_verification.json",
        12,
    ),
    (
        "Qwen circularity gate",
        CIRCULARITY / "independent_verification.json",
        10,
    ),
    ("high-recall seed gate", HIGH_RECALL / "independent_verification.json", 8),
]:
    receipt = json.loads(path.read_text())
    check(
        name,
        receipt["overall_pass"]
        and receipt["passed"] == expected
        and receipt["total"] == expected,
    )

treatment = json.loads(
    (CROSSCHECK / "treatment_integrity_verification.json").read_text()
)
predicate_gate = next(
    item
    for item in treatment["checks"]
    if item["gate"] == "filtered_rankings_obey_metadata_predicate"
)
check(
    "filtered ranking treatment has zero predicate violations",
    predicate_gate["checked_rows"] == 382193 and predicate_gate["violations"] == 0,
)


# Generated-manuscript structure and overclaim guards.
text = MANUSCRIPT.read_text()
tables = [int(value) for value in re.findall(r"\*\*\\?<표 (\d+)", text)]
check("table captions are sequential 1–27", tables == list(range(1, 28)))
appendices = re.findall(r"^## 부록 ([A-Z])\.", text, flags=re.MULTILINE)
check("appendices are sequential A–I", appendices == list("ABCDEFGHI"))
headings = [
    "### 4.1 동일 조건 통제 주입: 순환 경로만 바꾸면 지표가 포화된다",
    "### 7.7 동일 encoder 저장×검색×색인 공동 ablation",
    "## 부록 I. 최신 ablation·통제 주입·검증 gate",
]
check("latest sections are present", all(heading in text for heading in headings))
check(
    "latest sections occur in causal-to-design order",
    text.index(headings[0]) < text.index(headings[1]) < text.index(headings[2]),
)
check(
    "joint limitations are explicit",
    all(
        phrase in text
        for phrase in [
            "사후 우선 비교",
            "군집 BH q는 semantic 0.0852, strict 0.0888",
            "MEVA는 encoder 격리와 도메인 경계를 점검하지만 multi-frame 외부 재현은 아니다",
            "대규모 task qrels 품질이나 다른 데이터의 0.99를 보장하지 않는다",
        ]
    ),
)
check(
    "obsolete storage claims are absent",
    all(
        phrase not in text
        for phrase in [
            "multi·dual은 이득 없음",
            "MEVA frame 지배",
            "사전 고정된 보편 우위 조건",
        ]
    ),
)
check(
    "internal editorial notes are absent",
    all(
        phrase not in text
        for phrase in [
            "청사진 소유자",
            "작성자는 결정하지 않는다",
            "미개정 시 대안",
            "현행 조항 4",
        ]
    ),
)
check(
    "claim-evidence boundary table is present",
    "최신 주장–증거–금지 경계" in text
    and "과거 차이 전체를 순환성에 귀속 금지" in text
    and "대규모 task 품질·모든 구축 0.99 보장 금지" in text,
)
check(
    "formatting markers are balanced",
    text.count("[DBR_FULL_WIDTH_START]") == text.count("[DBR_FULL_WIDTH_END]")
    and text.count("[DBR_FINAL_FULL_WIDTH_START]") == 1
    and text.count("[DBR_BODY_TWO_COLUMNS]") == 1,
)


# Artifact-level packaging checks.
try:
    with zipfile.ZipFile(DOCX) as archive:
        bad_member = archive.testzip()
    check("DOCX zip integrity", bad_member is None)
except Exception as exc:  # pragma: no cover - reported as a gate failure
    check("DOCX zip integrity", False, str(exc))

pdfinfo = subprocess.run(
    ["pdfinfo", str(PDF)], capture_output=True, text=True
)
pages = re.search(r"^Pages:\s+(\d+)", pdfinfo.stdout, flags=re.MULTILINE)
page_size = re.search(r"^Page size:\s+(.+)$", pdfinfo.stdout, flags=re.MULTILINE)
check(
    "PDF is A4 and nonempty",
    pdfinfo.returncode == 0
    and pages is not None
    and int(pages.group(1)) > 0
    and page_size is not None
    and "A4" in page_size.group(1),
    f"pages={pages.group(1) if pages else 'unknown'}",
)


print(
    f"=== LATEST WORKING MASTER VERIFY: PASS {len(passed)} / "
    f"FAIL {len(failed)} ==="
)
for item in failed:
    print("  FAIL:", item)
raise SystemExit(0 if not failed else 1)
