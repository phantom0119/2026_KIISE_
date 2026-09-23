#!/usr/bin/env python3
"""Check local resources required by the KIISE VLM-DB experiments."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASETS_ROOT = PROJECT_ROOT / "Datasets"
CANONICAL_ROOT = DATASETS_ROOT / "processed" / "vru_accident" / "20260706" / "canonical"
AIHUB_RAW_ROOT = DATASETS_ROOT / "raw" / "aihub_intelligent_cctv" / "20260706"
AIHUB_CANONICAL_ROOT = DATASETS_ROOT / "processed" / "aihub_intelligent_cctv" / "20260706" / "canonical"
ABNORMAL_RAW_ROOT = DATASETS_ROOT / "raw" / "aihub_abnormal_cctv" / "20260707"
ABNORMAL_CANONICAL_ROOT = (
    DATASETS_ROOT / "processed" / "aihub_abnormal_cctv" / "20260707" / "canonical"
)
VRU_PGVECTOR_RESULT_ROOT = DATASETS_ROOT / "processed" / "vru_accident" / "20260706" / "results" / "vru_bgem3_pgvector_p2_p4"


def module_exists(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def module_version(name: str) -> str | None:
    try:
        module = __import__(name)
    except Exception:
        return None
    return str(getattr(module, "__version__", "unknown"))


def count_jsonl(path: Path) -> int:
    with path.open(encoding="utf-8") as f:
        return sum(1 for _ in f)


def safe_count_parquet(path: Path, errors: dict[str, str]) -> int | None:
    try:
        return len(pd.read_parquet(path))
    except Exception as exc:
        errors[str(path)] = f"{type(exc).__name__}: {exc}"
        return None


def safe_count_csv(path: Path, errors: dict[str, str], **kwargs) -> int | None:
    try:
        return len(pd.read_csv(path, **kwargs))
    except Exception as exc:
        errors[str(path)] = f"{type(exc).__name__}: {exc}"
        return None


def safe_count_jsonl(path: Path, errors: dict[str, str]) -> int | None:
    try:
        return count_jsonl(path)
    except Exception as exc:
        errors[str(path)] = f"{type(exc).__name__}: {exc}"
        return None


def get_gpus() -> list[str]:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,driver_version",
                "--format=csv,noheader",
            ],
            text=True,
        )
    except Exception:
        return []
    return [line.strip() for line in out.splitlines() if line.strip()]


def main() -> int:
    errors: dict[str, str] = {}
    checks = {
        "environment": {
            "python_executable": sys.executable,
            "python_version": sys.version.split()[0],
            "pandas_version": module_version("pandas"),
            "pyarrow_version": module_version("pyarrow"),
        },
        "paths": {
            "datasets_root": str(DATASETS_ROOT.resolve()),
            "datasets_exists": DATASETS_ROOT.exists(),
            "canonical_root": str(CANONICAL_ROOT),
            "canonical_exists": CANONICAL_ROOT.exists(),
            "vru_hf_root_exists": (DATASETS_ROOT / "external" / "VRU-Accident_hf").exists(),
            "vru_video_root_exists": (DATASETS_ROOT / "raw" / "VRU-Accident" / "VRU_videos").exists(),
            "aihub_cctv_zip_root_exists": (
                DATASETS_ROOT / "external" / "지능형관제서비스CCTV영상데이터"
            ).exists(),
            "aihub_cctv_raw_root": str(AIHUB_RAW_ROOT),
            "aihub_cctv_raw_exists": AIHUB_RAW_ROOT.exists(),
            "aihub_cctv_canonical_root": str(AIHUB_CANONICAL_ROOT),
            "aihub_cctv_canonical_exists": AIHUB_CANONICAL_ROOT.exists(),
            "aihub_abnormal_zip_root_exists": (
                DATASETS_ROOT / "external" / "이상탐지" / "이상행동 CCTV 영상"
            ).exists(),
            "aihub_abnormal_raw_root": str(ABNORMAL_RAW_ROOT),
            "aihub_abnormal_raw_exists": ABNORMAL_RAW_ROOT.exists(),
            "aihub_abnormal_canonical_root": str(ABNORMAL_CANONICAL_ROOT),
            "aihub_abnormal_canonical_exists": ABNORMAL_CANONICAL_ROOT.exists(),
            "vru_pgvector_result_root": str(VRU_PGVECTOR_RESULT_ROOT),
            "vru_pgvector_result_exists": (VRU_PGVECTOR_RESULT_ROOT / "summary.md").exists(),
        },
        "canonical_counts": {},
        "aihub_cctv_raw_counts": {},
        "aihub_cctv_canonical_counts": {},
        "aihub_abnormal_raw_counts": {},
        "aihub_abnormal_canonical_counts": {},
        "python_modules": {},
        "gpus": get_gpus(),
        "read_errors": errors,
    }

    if CANONICAL_ROOT.exists():
        checks["canonical_counts"] = {
            "clips": safe_count_parquet(CANONICAL_ROOT / "clips.parquet", errors),
            "documents": safe_count_parquet(CANONICAL_ROOT / "documents.parquet", errors),
            "metadata_rows": safe_count_parquet(CANONICAL_ROOT / "metadata.parquet", errors),
            "queries": safe_count_jsonl(CANONICAL_ROOT / "queries.jsonl", errors),
            "qrels": safe_count_csv(CANONICAL_ROOT / "qrels.tsv", errors, sep="\t"),
        }

    if AIHUB_RAW_ROOT.exists():
        pair_manifest = AIHUB_RAW_ROOT / "clip_pairs.csv"
        checks["aihub_cctv_raw_counts"] = {
            "media_files": len(list((AIHUB_RAW_ROOT / "media").rglob("*.mp4"))),
            "label_files": len(list((AIHUB_RAW_ROOT / "labels").rglob("*.json"))),
            "paired_clips": safe_count_csv(pair_manifest, errors) if pair_manifest.exists() else None,
        }

    if AIHUB_CANONICAL_ROOT.exists():
        checks["aihub_cctv_canonical_counts"] = {
            "clips": safe_count_parquet(AIHUB_CANONICAL_ROOT / "clips.parquet", errors),
            "documents": safe_count_parquet(AIHUB_CANONICAL_ROOT / "documents.parquet", errors),
            "metadata_rows": safe_count_parquet(AIHUB_CANONICAL_ROOT / "metadata.parquet", errors),
            "queries": safe_count_jsonl(AIHUB_CANONICAL_ROOT / "queries.jsonl", errors),
            "qrels": safe_count_csv(AIHUB_CANONICAL_ROOT / "qrels.tsv", errors, sep="\t"),
            "bge_embeddings_exists": (
                AIHUB_CANONICAL_ROOT.parent / "embeddings" / "bge-m3" / "embedding_manifest.json"
            ).exists(),
            "e5_embeddings_exists": (
                AIHUB_CANONICAL_ROOT.parent / "embeddings" / "e5-large-v2" / "embedding_manifest.json"
            ).exists(),
            "bge_results_exists": (
                AIHUB_CANONICAL_ROOT.parent / "results" / "aihub_bgem3_faiss_b0_b5" / "summary.md"
            ).exists(),
            "e5_results_exists": (
                AIHUB_CANONICAL_ROOT.parent / "results" / "aihub_e5_faiss_b0_b5" / "summary.md"
            ).exists(),
        }

    if ABNORMAL_RAW_ROOT.exists():
        pair_manifest = ABNORMAL_RAW_ROOT / "clip_pairs.csv"
        zip_manifest = ABNORMAL_RAW_ROOT / "zip_manifest.csv"
        checks["aihub_abnormal_raw_counts"] = {
            "zip_files": safe_count_csv(zip_manifest, errors) if zip_manifest.exists() else None,
            "paired_clips": safe_count_csv(pair_manifest, errors) if pair_manifest.exists() else None,
            "label_files": len(list((ABNORMAL_RAW_ROOT / "labels").rglob("*.xml"))),
        }

    if ABNORMAL_CANONICAL_ROOT.exists():
        checks["aihub_abnormal_canonical_counts"] = {
            "clips": safe_count_parquet(ABNORMAL_CANONICAL_ROOT / "clips.parquet", errors),
            "documents": safe_count_parquet(ABNORMAL_CANONICAL_ROOT / "documents.parquet", errors),
            "metadata_rows": safe_count_parquet(ABNORMAL_CANONICAL_ROOT / "metadata.parquet", errors),
            "queries": safe_count_jsonl(ABNORMAL_CANONICAL_ROOT / "queries.jsonl", errors),
            "qrels": safe_count_csv(ABNORMAL_CANONICAL_ROOT / "qrels.tsv", errors, sep="\t"),
            "bge_embeddings_exists": (
                ABNORMAL_CANONICAL_ROOT.parent / "embeddings" / "bge-m3" / "embedding_manifest.json"
            ).exists(),
            "e5_embeddings_exists": (
                ABNORMAL_CANONICAL_ROOT.parent
                / "embeddings"
                / "e5-large-v2"
                / "embedding_manifest.json"
            ).exists(),
            "bge_results_exists": (
                ABNORMAL_CANONICAL_ROOT.parent
                / "results"
                / "abnormal_bgem3_faiss_b0_b5"
                / "summary.md"
            ).exists(),
            "e5_results_exists": (
                ABNORMAL_CANONICAL_ROOT.parent
                / "results"
                / "abnormal_e5_faiss_b0_b5"
                / "summary.md"
            ).exists(),
        }

    for module in [
        "pandas",
        "pyarrow",
        "numpy",
        "sklearn",
        "torch",
        "transformers",
        "sentence_transformers",
        "FlagEmbedding",
        "faiss",
        "rank_bm25",
        "psycopg",
        "pgvector",
        "huggingface_hub",
    ]:
        checks["python_modules"][module] = module_exists(module)

    print(json.dumps(checks, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
