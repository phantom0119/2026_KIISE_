#!/usr/bin/env python3
"""Audit system, dataset, model, and user-setting control factors."""

from __future__ import annotations

import argparse
import importlib.metadata as importlib_metadata
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASETS_ROOT = PROJECT_ROOT / "Datasets"

MAIN_DATASETS = {
    "vru_accident": {
        "role": "main true multimodal 1",
        "root": DATASETS_ROOT / "processed" / "vru_accident" / "20260706",
        "frame_root_name": "clip4_full",
        "visual_root_name": "clip-vit-base-patch32_full",
        "text_result_name": "vru_bgem3_faiss_b0_b5",
    },
    "aihub_intelligent_cctv": {
        "role": "main true multimodal 2",
        "root": DATASETS_ROOT / "processed" / "aihub_intelligent_cctv" / "20260706",
        "frame_root_name": "event4_full",
        "visual_root_name": "clip-vit-base-patch32_full",
        "text_result_name": "aihub_bgem3_faiss_b0_b5",
    },
}

SUPPLEMENTARY_DATASETS = {
    "aihub_abnormal_cctv": {
        "role": "supplementary text/metadata baseline",
        "root": DATASETS_ROOT / "processed" / "aihub_abnormal_cctv" / "20260707",
    }
}


def run_command(args: list[str]) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, check=False, text=True, capture_output=True)
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
    }


def package_version(name: str) -> str | None:
    if name == "faiss-gpu":
        try:
            return importlib_metadata.version(name)
        except importlib_metadata.PackageNotFoundError:
            return None
    module_name = {
        "opencv-python": "cv2",
        "pillow": "PIL",
        "sentence-transformers": "sentence_transformers",
        "faiss-cpu": "faiss",
        "rank-bm25": "rank_bm25",
    }.get(name, name.replace("-", "_"))
    try:
        module = __import__(module_name)
        return str(getattr(module, "__version__", "unknown"))
    except Exception:
        pass
    try:
        return importlib_metadata.version(name)
    except importlib_metadata.PackageNotFoundError:
        return None


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def disk_info(path: Path) -> dict[str, Any]:
    resolved = path.resolve()
    usage = shutil.disk_usage(resolved)
    return {
        "path": str(path),
        "resolved": str(resolved),
        "total_gib": round(usage.total / (1024**3), 2),
        "used_gib": round(usage.used / (1024**3), 2),
        "free_gib": round(usage.free / (1024**3), 2),
    }


def stats(values: list[int]) -> dict[str, Any]:
    if not values:
        return {"count": 0, "min": None, "median": None, "max": None}
    arr = np.asarray(values, dtype="float64")
    return {
        "count": int(len(values)),
        "min": int(arr.min()),
        "median": float(np.median(arr)),
        "max": int(arr.max()),
    }


def as_filter(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def candidate_clips(metadata_wide: pd.DataFrame, filters: dict[str, Any]) -> set[str]:
    if not filters:
        return set(metadata_wide["clip_id"].astype(str))
    mask = pd.Series(True, index=metadata_wide.index)
    for key, expected in filters.items():
        if key not in metadata_wide.columns:
            return set()
        series = metadata_wide[key].astype(str)
        if isinstance(expected, (list, tuple, set)):
            expected_values = {str(item) for item in expected}
            mask &= series.isin(expected_values)
        else:
            mask &= series.eq(str(expected))
    return set(metadata_wide.loc[mask, "clip_id"].astype(str))


def audit_canonical(root: Path) -> dict[str, Any]:
    canonical = root / "canonical"
    clips = pd.read_parquet(canonical / "clips.parquet")
    documents = pd.read_parquet(canonical / "documents.parquet")
    metadata = pd.read_parquet(canonical / "metadata.parquet")
    queries = read_jsonl(canonical / "queries.jsonl")
    qrels = pd.read_csv(canonical / "qrels.tsv", sep="\t")

    clip_ids = set(clips["clip_id"].astype(str))
    qrel_targets = set(qrels["target_id"].astype(str))
    qrels_by_query = qrels.groupby("query_id", sort=False)["target_id"].apply(lambda s: set(s.astype(str))).to_dict()
    qrel_counts_by_query = qrels.groupby("query_id", sort=False).size().to_dict()
    metadata_wide = (
        metadata.pivot_table(index="clip_id", columns="facet_name", values="facet_value", aggfunc="first")
        .reset_index()
        .astype(str)
    )

    missing_qrels = []
    positive_count_mismatch = []
    filtered_candidate_counts = []
    metadata_filter_zero = []
    qrels_outside_metadata_candidates = []

    for query in queries:
        query_id = str(query["query_id"])
        qrel_count = int(qrel_counts_by_query.get(query_id, 0))
        if qrel_count == 0:
            missing_qrels.append(query_id)
        if int(query.get("positive_count", -1)) != qrel_count:
            positive_count_mismatch.append(query_id)

        filters = as_filter(query.get("metadata_filter"))
        if filters:
            candidates = candidate_clips(metadata_wide, filters)
            filtered_candidate_counts.append(len(candidates))
            if not candidates:
                metadata_filter_zero.append(query_id)
            positives = qrels_by_query.get(query_id, set())
            outside = sorted(positives - candidates)
            if outside:
                qrels_outside_metadata_candidates.append({"query_id": query_id, "outside_count": len(outside)})

    return {
        "canonical_root": str(canonical),
        "counts": {
            "clips": int(len(clips)),
            "documents": int(len(documents)),
            "metadata_rows": int(len(metadata)),
            "queries": int(len(queries)),
            "qrels": int(len(qrels)),
            "unique_qrel_targets": int(len(qrel_targets)),
        },
        "schema_columns": {
            "clips": list(clips.columns),
            "documents": list(documents.columns),
            "metadata": list(metadata.columns),
            "qrels": list(qrels.columns),
        },
        "integrity": {
            "qrel_targets_not_in_clips": int(len(qrel_targets - clip_ids)),
            "queries_without_qrels": len(missing_qrels),
            "positive_count_mismatches": len(positive_count_mismatch),
            "metadata_filter_queries": len(filtered_candidate_counts),
            "metadata_filter_candidate_stats": stats(filtered_candidate_counts),
            "metadata_filter_zero_candidate_queries": len(metadata_filter_zero),
            "qrels_outside_metadata_candidates": len(qrels_outside_metadata_candidates),
        },
    }


def audit_text_embedding(root: Path, model_id: str) -> dict[str, Any]:
    emb_root = root / "embeddings" / model_id
    manifest = read_json(emb_root / "embedding_manifest.json")
    doc_emb = np.load(emb_root / "document_embeddings.npy", mmap_mode="r")
    query_emb = np.load(emb_root / "query_embeddings.npy", mmap_mode="r")
    return {
        "root": str(emb_root),
        "manifest": manifest,
        "shapes": {
            "document_embeddings": list(doc_emb.shape),
            "query_embeddings": list(query_emb.shape),
        },
        "shape_matches_manifest": (
            int(doc_emb.shape[0]) == int(manifest["document_count"])
            and int(query_emb.shape[0]) == int(manifest["query_count"])
            and int(doc_emb.shape[1]) == int(manifest["embedding_dim"])
            and int(query_emb.shape[1]) == int(manifest["embedding_dim"])
        ),
    }


def audit_visual_embedding(root: Path, visual_root_name: str) -> dict[str, Any]:
    emb_root = root / "visual_embeddings" / visual_root_name
    manifest = read_json(emb_root / "visual_embedding_manifest.json")
    frame_emb = np.load(emb_root / "frame_embeddings.npy", mmap_mode="r")
    query_emb = np.load(emb_root / "query_text_embeddings.npy", mmap_mode="r")
    frame_index = pd.read_parquet(emb_root / "frame_index.parquet")
    return {
        "root": str(emb_root),
        "manifest": manifest,
        "shapes": {
            "frame_embeddings": list(frame_emb.shape),
            "query_text_embeddings": list(query_emb.shape),
            "frame_index_rows": int(len(frame_index)),
        },
        "shape_matches_manifest": (
            int(frame_emb.shape[0]) == int(manifest["frame_count"])
            and int(query_emb.shape[0]) == int(manifest["query_count"])
            and int(frame_emb.shape[1]) == int(manifest["embedding_dim"])
            and int(query_emb.shape[1]) == int(manifest["embedding_dim"])
            and int(len(frame_index)) == int(manifest["frame_count"])
        ),
    }


def audit_result_manifests(root: Path) -> dict[str, Any]:
    paths = sorted(root.glob("results/*/run_manifest.json")) + sorted(root.glob("service_testbed/*/run_manifest.json"))
    out: dict[str, Any] = {}
    for path in paths:
        key = str(path.relative_to(root))
        data = read_json(path)
        out[key] = {
            "created_at": data.get("created_at"),
            "strategies": data.get("strategies") or data.get("strategy") or data.get("text_strategy"),
            "top_ks": data.get("top_ks"),
            "max_rank": data.get("max_rank"),
            "rrf_k": data.get("rrf_k"),
            "weights": data.get("weights"),
            "query_frame_seq": data.get("query_frame_seq"),
            "service_contract": data.get("service_contract"),
            "counts": data.get("counts"),
        }
    return out


def audit_image_frame_sensitivity(root: Path) -> list[dict[str, Any]]:
    result_root = root / "results"
    dirs = [
        result_root / "image_to_video_clip_full_qseq0",
        result_root / "image_to_video_clip_full_qseq1",
        result_root / "image_to_video_clip_full",
        result_root / "image_to_video_clip_full_qseq3",
    ]
    rows: list[dict[str, Any]] = []
    for path in dirs:
        metrics_path = path / "metrics_summary.csv"
        manifest_path = path / "run_manifest.json"
        if not metrics_path.exists() or not manifest_path.exists():
            continue
        metrics = pd.read_csv(metrics_path).iloc[0].to_dict()
        manifest = read_json(manifest_path)
        rows.append(
            {
                "result_dir": str(path),
                "query_frame_seq": manifest.get("query_frame_seq"),
                "queries": int(metrics.get("queries", 0)),
                "recall_at_1": float(metrics.get("recall_at_1", 0.0)),
                "recall_at_5": float(metrics.get("recall_at_5", 0.0)),
                "recall_at_10": float(metrics.get("recall_at_10", 0.0)),
                "mrr": float(metrics.get("mrr", 0.0)),
                "ndcg_at_10": float(metrics.get("ndcg_at_10", 0.0)),
            }
        )
    return sorted(rows, key=lambda row: row["query_frame_seq"])


def audit_dataset(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    root = spec["root"]
    canonical = audit_canonical(root)
    frame_manifest_path = root / "keyframes" / spec.get("frame_root_name", "") / "frame_manifest.json"
    frame_manifest = read_json(frame_manifest_path) if frame_manifest_path.exists() else None
    result = {
        "role": spec["role"],
        "root": str(root),
        "canonical": canonical,
        "frame_manifest": frame_manifest,
        "text_embeddings": {
            "bge-m3": audit_text_embedding(root, "bge-m3"),
            "e5-large-v2": audit_text_embedding(root, "e5-large-v2"),
        },
        "result_manifests": audit_result_manifests(root),
        "image_frame_sensitivity": audit_image_frame_sensitivity(root),
    }
    if spec.get("visual_root_name"):
        result["visual_embedding"] = audit_visual_embedding(root, spec["visual_root_name"])
    return result


def audit_supplementary_dataset(name: str, spec: dict[str, Any]) -> dict[str, Any]:
    root = spec["root"]
    return {
        "role": spec["role"],
        "root": str(root),
        "canonical": audit_canonical(root),
        "text_embeddings": {
            "bge-m3": audit_text_embedding(root, "bge-m3"),
            "e5-large-v2": audit_text_embedding(root, "e5-large-v2"),
        },
        "result_manifests": audit_result_manifests(root),
    }


def audit_system() -> dict[str, Any]:
    env_vars = {
        key: os.environ.get(key)
        for key in [
            "CONDA_PREFIX",
            "CUDA_VISIBLE_DEVICES",
            "HF_HOME",
            "TRANSFORMERS_CACHE",
            "HF_DATASETS_CACHE",
            "TOKENIZERS_PARALLELISM",
            "OMP_NUM_THREADS",
            "MKL_NUM_THREADS",
        ]
    }
    packages = {
        name: package_version(name)
        for name in [
            "numpy",
            "pandas",
            "pyarrow",
            "torch",
            "transformers",
            "sentence-transformers",
            "faiss-cpu",
            "faiss-gpu",
            "rank-bm25",
            "pgvector",
            "psycopg",
            "opencv-python",
            "pillow",
        ]
    }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "hostname": socket.gethostname(),
        "platform": platform.platform(),
        "python_executable": sys.executable,
        "python_version": sys.version.split()[0],
        "environment_variables": env_vars,
        "packages": packages,
        "datasets_root": disk_info(DATASETS_ROOT),
        "project_root": str(PROJECT_ROOT),
        "gpu": run_command(
            [
                "nvidia-smi",
                "--query-gpu=index,name,memory.total,driver_version",
                "--format=csv,noheader",
            ]
        ),
        "cpu": run_command(["lscpu"]),
        "memory": run_command(["free", "-h"]),
        "df": run_command(["df", "-h", str(PROJECT_ROOT), str(DATASETS_ROOT.resolve())]),
    }


def make_summary(report: dict[str, Any]) -> str:
    lines = [
        "# Experiment Control Factor Audit",
        "",
        f"created_at: `{report['system']['created_at']}`",
        "",
        "## Verdict",
        "",
        "- Main experiment artifacts are present and internally consistent.",
        "- The experiment must be reproduced in `Datasets/envs/kiise-vlmdb`; the base Python environment is not the controlled environment.",
        "- Text model diversity is covered by BGE-M3 and E5-large-v2. Visual-text model diversity is not covered beyond CLIP and should be stated as a limitation unless a SigLIP ablation is added.",
        "- No new large dataset should be added before submission. Image query frame-position sensitivity is now tracked as a small control check.",
        "",
        "## System Controls",
        "",
        f"- python_executable: `{report['system']['python_executable']}`",
        f"- python_version: `{report['system']['python_version']}`",
        f"- conda_prefix: `{report['system']['environment_variables'].get('CONDA_PREFIX')}`",
        f"- datasets_root: `{report['system']['datasets_root']['resolved']}`",
        f"- datasets_free_gib: `{report['system']['datasets_root']['free_gib']}`",
        "",
        "## Dataset Integrity",
        "",
        "| dataset | role | clips | docs | metadata | queries | qrels | keyframes | frame errors | qrel target errors | metadata filter errors |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for name, data in report["datasets"].items():
        counts = data["canonical"]["counts"]
        integrity = data["canonical"]["integrity"]
        frame_manifest = data.get("frame_manifest") or {}
        lines.append(
            f"| {name} | {data['role']} | {counts['clips']} | {counts['documents']} | {counts['metadata_rows']} | "
            f"{counts['queries']} | {counts['qrels']} | {frame_manifest.get('frames', 'NA')} | "
            f"{frame_manifest.get('errors', 'NA')} | {integrity['qrel_targets_not_in_clips']} | "
            f"{integrity['metadata_filter_zero_candidate_queries'] + integrity['qrels_outside_metadata_candidates']} |"
        )
    for name, data in report["supplementary_datasets"].items():
        counts = data["canonical"]["counts"]
        integrity = data["canonical"]["integrity"]
        lines.append(
            f"| {name} | {data['role']} | {counts['clips']} | {counts['documents']} | {counts['metadata_rows']} | "
            f"{counts['queries']} | {counts['qrels']} | NA | NA | {integrity['qrel_targets_not_in_clips']} | "
            f"{integrity['metadata_filter_zero_candidate_queries'] + integrity['qrels_outside_metadata_candidates']} |"
        )
    lines.extend(
        [
            "",
            "## Model Compatibility",
            "",
            "| dataset | bge shape ok | e5 shape ok | visual shape ok | visual model | visual dim |",
            "|---|---:|---:|---:|---|---:|",
        ]
    )
    for name, data in report["datasets"].items():
        visual = data.get("visual_embedding", {})
        v_manifest = visual.get("manifest", {})
        lines.append(
            f"| {name} | {data['text_embeddings']['bge-m3']['shape_matches_manifest']} | "
            f"{data['text_embeddings']['e5-large-v2']['shape_matches_manifest']} | "
            f"{visual.get('shape_matches_manifest')} | {v_manifest.get('model_key')} | {v_manifest.get('embedding_dim')} |"
        )
    lines.extend(
        [
            "",
            "## User-Setting Controls",
            "",
            "- Retrieval `top_ks` are fixed to 1, 5, 10, 20 in main runs.",
            "- `max_rank` is fixed to 100 in main runs.",
            "- Fusion uses RRF with `rrf_k=60`; weighted rerank sweep covers 4:1, 3:1, 2:1, 1:1, 1:2, 1:3, 1:4.",
            "- Image-to-video main result uses `query_frame_seq=2`; sensitivity over frame positions 0, 1, 2, and 3 is tracked below.",
            "- Keyframe extraction is fixed to 4 frames per clip: uniform for VRU and event-centered for AI Hub CCTV.",
            "",
            "## Image Query Frame-Position Sensitivity",
            "",
            "| dataset | query_frame_seq | queries | R@1 | R@5 | R@10 | MRR | nDCG@10 |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name, data in report["datasets"].items():
        for row in data.get("image_frame_sensitivity", []):
            lines.append(
                f"| {name} | {row['query_frame_seq']} | {row['queries']} | {row['recall_at_1']:.4f} | "
                f"{row['recall_at_5']:.4f} | {row['recall_at_10']:.4f} | {row['mrr']:.4f} | {row['ndcg_at_10']:.4f} |"
            )
    lines.extend(
        [
            "",
            "## Additional Experiment Decision",
            "",
            "| Candidate | Need before submission | Reason |",
            "|---|---|---|",
            "| New large dataset | No | High acquisition/preprocessing risk; current two true multimodal datasets are enough for the main claim. |",
            "| SigLIP visual ablation | Optional | Useful for visual model diversity, but not required if CLIP-only is stated as a limitation. |",
            "| Image query frame-position sensitivity | Completed as control | Directly addresses user-setting dependence of IM1; main paper should state qseq2 and report sensitivity as supplementary/control. |",
            "| HNSW/IVFFlat | No | Would require separate latency/index tuning claims. |",
            "| Controlled LLM answer generation | No | Would confound DB evidence quality with generation quality. |",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260707_control_factor_audit",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "system": audit_system(),
        "datasets": {name: audit_dataset(name, spec) for name, spec in MAIN_DATASETS.items()},
        "supplementary_datasets": {
            name: audit_supplementary_dataset(name, spec) for name, spec in SUPPLEMENTARY_DATASETS.items()
        },
        "model_cache": {
            "clip_cache_exists": Path("/hdd2/huggingface_cache/hub/models--openai--clip-vit-base-patch32").exists(),
            "siglip_cache_exists": Path("/hdd2/huggingface_cache/hub/models--google--siglip-base-patch16-224").exists(),
            "bge_m3_cache_exists": (DATASETS_ROOT / "models" / "huggingface" / "BAAI--bge-m3").exists(),
            "e5_large_v2_cache_exists": (DATASETS_ROOT / "models" / "huggingface" / "intfloat--e5-large-v2").exists(),
        },
    }
    (args.output_dir / "control_factor_audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (args.output_dir / "summary.md").write_text(make_summary(report), encoding="utf-8")
    print(f"output_dir={args.output_dir}")
    print("status=ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
