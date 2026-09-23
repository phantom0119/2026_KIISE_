#!/usr/bin/env python3
"""Validate the frozen experiment artifacts used by the KIISE manuscript."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_ROOT = PROJECT_ROOT / "Datasets"


@dataclass(frozen=True)
class CanonicalSpec:
    name: str
    root: Path
    clips: int
    documents: int
    metadata_rows: int
    queries: int
    qrels: int


@dataclass(frozen=True)
class EmbeddingSpec:
    name: str
    root: Path
    model_id: str
    document_count: int
    query_count: int
    embedding_dim: int = 1024


@dataclass(frozen=True)
class MetricSpec:
    result_name: str
    result_root: Path
    strategy: str
    metric: str
    expected: float
    tolerance: float = 5e-4


CANONICAL_SPECS = [
    CanonicalSpec(
        "VRU-Accident",
        DATASETS_ROOT / "processed" / "vru_accident" / "20260706" / "canonical",
        clips=1000,
        documents=7000,
        metadata_rows=6000,
        queries=244,
        qrels=5488,
    ),
    CanonicalSpec(
        "AI Hub intelligent CCTV",
        DATASETS_ROOT / "processed" / "aihub_intelligent_cctv" / "20260706" / "canonical",
        clips=269,
        documents=807,
        metadata_rows=2563,
        queries=133,
        qrels=1358,
    ),
    CanonicalSpec(
        "AI Hub abnormal CCTV",
        DATASETS_ROOT / "processed" / "aihub_abnormal_cctv" / "20260707" / "canonical",
        clips=1968,
        documents=5904,
        metadata_rows=33456,
        queries=424,
        qrels=21639,
    ),
]


EMBEDDING_SPECS = [
    EmbeddingSpec(
        f"{spec.name} / {model_id}",
        spec.root.parent / "embeddings" / model_id,
        model_id=model_id,
        document_count=spec.documents,
        query_count=spec.queries,
    )
    for spec in CANONICAL_SPECS
    for model_id in ["bge-m3", "e5-large-v2"]
]


METRIC_SPECS = [
    MetricSpec(
        "VRU bge-m3 FAISS",
        DATASETS_ROOT / "processed" / "vru_accident" / "20260706" / "results" / "vru_bgem3_faiss_b0_b5",
        "B2_vector_only",
        "ndcg_at_10",
        0.4476,
    ),
    MetricSpec(
        "VRU bge-m3 FAISS",
        DATASETS_ROOT / "processed" / "vru_accident" / "20260706" / "results" / "vru_bgem3_faiss_b0_b5",
        "B4_prefilter_vector",
        "ndcg_at_10",
        0.9736,
    ),
    MetricSpec(
        "VRU bge-m3 FAISS",
        DATASETS_ROOT / "processed" / "vru_accident" / "20260706" / "results" / "vru_bgem3_faiss_b0_b5",
        "B4_prefilter_vector",
        "recall_at_20",
        0.8591,
    ),
    MetricSpec(
        "VRU e5-large-v2 FAISS",
        DATASETS_ROOT / "processed" / "vru_accident" / "20260706" / "results" / "vru_e5_faiss_b0_b5",
        "B2_vector_only",
        "ndcg_at_10",
        0.3482,
    ),
    MetricSpec(
        "VRU e5-large-v2 FAISS",
        DATASETS_ROOT / "processed" / "vru_accident" / "20260706" / "results" / "vru_e5_faiss_b0_b5",
        "B4_prefilter_vector",
        "ndcg_at_10",
        0.8311,
    ),
    MetricSpec(
        "VRU pgvector",
        DATASETS_ROOT / "processed" / "vru_accident" / "20260706" / "results" / "vru_bgem3_pgvector_p2_p4",
        "P4_pgvector_prefilter_vector",
        "ndcg_at_10",
        0.9736,
    ),
    MetricSpec(
        "AI Hub intelligent bge-m3 FAISS",
        DATASETS_ROOT
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "aihub_bgem3_faiss_b0_b5",
        "B4_prefilter_vector",
        "ndcg_at_10",
        1.0000,
    ),
    MetricSpec(
        "AI Hub intelligent e5-large-v2 FAISS",
        DATASETS_ROOT
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "aihub_e5_faiss_b0_b5",
        "B4_prefilter_vector",
        "ndcg_at_10",
        0.9925,
    ),
    MetricSpec(
        "AI Hub abnormal bge-m3 FAISS",
        DATASETS_ROOT
        / "processed"
        / "aihub_abnormal_cctv"
        / "20260707"
        / "results"
        / "abnormal_bgem3_faiss_b0_b5",
        "B5_hybrid",
        "ndcg_at_10",
        0.9946,
    ),
    MetricSpec(
        "AI Hub abnormal e5-large-v2 FAISS",
        DATASETS_ROOT
        / "processed"
        / "aihub_abnormal_cctv"
        / "20260707"
        / "results"
        / "abnormal_e5_faiss_b0_b5",
        "B5_hybrid",
        "ndcg_at_10",
        0.9954,
    ),
]


def count_jsonl(path: Path) -> int:
    with path.open(encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def add_check(checks: list[dict[str, Any]], name: str, passed: bool, detail: str) -> None:
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def validate_canonical(checks: list[dict[str, Any]]) -> None:
    for spec in CANONICAL_SPECS:
        add_check(checks, f"{spec.name} canonical root", spec.root.exists(), str(spec.root))
        if not spec.root.exists():
            continue
        files = {
            "clips": spec.root / "clips.parquet",
            "documents": spec.root / "documents.parquet",
            "metadata": spec.root / "metadata.parquet",
            "queries": spec.root / "queries.jsonl",
            "qrels": spec.root / "qrels.tsv",
        }
        for label, path in files.items():
            add_check(checks, f"{spec.name} {label} file", path.exists(), str(path))
        if not all(path.exists() for path in files.values()):
            continue
        counts = {
            "clips": len(pd.read_parquet(files["clips"])),
            "documents": len(pd.read_parquet(files["documents"])),
            "metadata_rows": len(pd.read_parquet(files["metadata"])),
            "queries": count_jsonl(files["queries"]),
            "qrels": len(pd.read_csv(files["qrels"], sep="\t")),
        }
        expected = {
            "clips": spec.clips,
            "documents": spec.documents,
            "metadata_rows": spec.metadata_rows,
            "queries": spec.queries,
            "qrels": spec.qrels,
        }
        for key, value in expected.items():
            add_check(
                checks,
                f"{spec.name} {key} count",
                counts[key] == value,
                f"actual={counts[key]}, expected={value}",
            )


def validate_embeddings(checks: list[dict[str, Any]]) -> None:
    for spec in EMBEDDING_SPECS:
        manifest_path = spec.root / "embedding_manifest.json"
        add_check(checks, f"{spec.name} embedding manifest", manifest_path.exists(), str(manifest_path))
        for filename in ["document_embeddings.npy", "query_embeddings.npy", "document_index.parquet", "query_index.parquet"]:
            path = spec.root / filename
            add_check(checks, f"{spec.name} {filename}", path.exists(), str(path))
        if not manifest_path.exists():
            continue
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = {
            "model_id": spec.model_id,
            "document_count": spec.document_count,
            "query_count": spec.query_count,
            "embedding_dim": spec.embedding_dim,
        }
        for key, value in expected.items():
            add_check(
                checks,
                f"{spec.name} manifest {key}",
                manifest.get(key) == value,
                f"actual={manifest.get(key)}, expected={value}",
            )


def validate_metrics(checks: list[dict[str, Any]]) -> None:
    loaded: dict[Path, pd.DataFrame] = {}
    for spec in METRIC_SPECS:
        for filename in ["summary.md", "metrics_summary.csv", "run_manifest.json"]:
            path = spec.result_root / filename
            add_check(checks, f"{spec.result_name} {filename}", path.exists(), str(path))
        metrics_path = spec.result_root / "metrics_summary.csv"
        if not metrics_path.exists():
            continue
        if metrics_path not in loaded:
            loaded[metrics_path] = pd.read_csv(metrics_path)
        metrics = loaded[metrics_path]
        row = metrics[metrics["strategy"].eq(spec.strategy) & metrics["difficulty"].eq("all")]
        add_check(
            checks,
            f"{spec.result_name} {spec.strategy} all row",
            len(row) == 1,
            f"rows={len(row)}",
        )
        if len(row) != 1:
            continue
        actual = float(row.iloc[0][spec.metric])
        passed = abs(actual - spec.expected) <= spec.tolerance
        add_check(
            checks,
            f"{spec.result_name} {spec.strategy} {spec.metric}",
            passed,
            f"actual={actual:.6f}, expected={spec.expected:.4f}, tolerance={spec.tolerance}",
        )


def write_reports(checks: list[dict[str, Any]], output_json: Path, output_md: Path) -> None:
    passed = all(check["passed"] for check in checks)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "project_root": str(PROJECT_ROOT),
        "passed": passed,
        "total_checks": len(checks),
        "failed_checks": sum(1 for check in checks if not check["passed"]),
        "checks": checks,
    }
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Experiment Freeze Validation",
        "",
        f"created_at: `{report['created_at']}`",
        f"passed: `{passed}`",
        f"total_checks: `{report['total_checks']}`",
        f"failed_checks: `{report['failed_checks']}`",
        "",
        "| status | check | detail |",
        "|---|---|---|",
    ]
    for check in checks:
        status = "PASS" if check["passed"] else "FAIL"
        detail = str(check["detail"]).replace("|", "\\|")
        lines.append(f"| {status} | {check['name']} | `{detail}` |")
    output_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-json",
        type=Path,
        default=PROJECT_ROOT / "2026_KIISE" / "manuscript" / "_archive_20260819" / "freeze_validation_20260707.json",
    )
    parser.add_argument(
        "--output-md",
        type=Path,
        default=PROJECT_ROOT / "2026_KIISE" / "manuscript" / "_archive_20260819" / "freeze_validation_20260707.md",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    checks: list[dict[str, Any]] = []
    validate_canonical(checks)
    validate_embeddings(checks)
    validate_metrics(checks)
    write_reports(checks, args.output_json, args.output_md)

    failed = [check for check in checks if not check["passed"]]
    print(f"total_checks={len(checks)}")
    print(f"failed_checks={len(failed)}")
    print(f"output_json={args.output_json}")
    print(f"output_md={args.output_md}")
    if failed:
        for check in failed[:20]:
            print(f"FAIL {check['name']}: {check['detail']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
