#!/usr/bin/env python3
"""Audit true multimodal experiment artifacts and summarize manuscript-ready metrics."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS = PROJECT_ROOT / "Datasets"
OUTPUT_DIR = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260707_pipeline_audit"


DATASET_CONFIGS = {
    "vru_accident": {
        "root": DATASETS / "processed" / "vru_accident" / "20260706",
        "canonical": DATASETS / "processed" / "vru_accident" / "20260706" / "canonical",
        "keyframes": DATASETS / "processed" / "vru_accident" / "20260706" / "keyframes" / "clip4_full",
        "visual_embeddings": DATASETS
        / "processed"
        / "vru_accident"
        / "20260706"
        / "visual_embeddings"
        / "clip-vit-base-patch32_full",
        "text_results": DATASETS / "processed" / "vru_accident" / "20260706" / "results" / "vru_bgem3_faiss_b0_b5",
        "visual_results": DATASETS / "processed" / "vru_accident" / "20260706" / "results" / "visual_clip_full_m2_m4",
        "fusion_results": DATASETS / "processed" / "vru_accident" / "20260706" / "results" / "multimodal_fusion_clip_bgem3_m5_m6",
        "image_results": DATASETS / "processed" / "vru_accident" / "20260706" / "results" / "image_to_video_clip_full",
        "siglip_visual_embeddings": DATASETS
        / "processed"
        / "vru_accident"
        / "20260706"
        / "visual_embeddings"
        / "siglip-base-patch16-224_full",
        "siglip_visual_results": DATASETS / "processed" / "vru_accident" / "20260706" / "results" / "visual_siglip_full_m2_m4",
        "siglip_fusion_results": DATASETS
        / "processed"
        / "vru_accident"
        / "20260706"
        / "results"
        / "multimodal_fusion_siglip_bgem3_m5_m6",
        "siglip_image_results": DATASETS / "processed" / "vru_accident" / "20260706" / "results" / "image_to_video_siglip_full",
        "siglip_weighted_rerank": DATASETS
        / "processed"
        / "vru_accident"
        / "20260706"
        / "results"
        / "weighted_fusion_rerank_sweep_bgem3_siglip",
        "clip_k1_embeddings": DATASETS
        / "processed"
        / "vru_accident"
        / "20260706"
        / "visual_embeddings"
        / "clip-vit-base-patch32_k1_seq2",
        "clip_k2_embeddings": DATASETS
        / "processed"
        / "vru_accident"
        / "20260706"
        / "visual_embeddings"
        / "clip-vit-base-patch32_k2_seq1_2",
        "clip_k1_visual_results": DATASETS / "processed" / "vru_accident" / "20260706" / "results" / "visual_clip_k1_seq2_m2_m4",
        "clip_k2_visual_results": DATASETS
        / "processed"
        / "vru_accident"
        / "20260706"
        / "results"
        / "visual_clip_k2_seq1_2_m2_m4",
        "clip_k2_image_results": DATASETS
        / "processed"
        / "vru_accident"
        / "20260706"
        / "results"
        / "image_to_video_clip_k2_seq1_2",
        "weighted_rerank": DATASETS
        / "processed"
        / "vru_accident"
        / "20260706"
        / "results"
        / "weighted_fusion_rerank_sweep_bgem3_clip",
        "service_equal": DATASETS / "processed" / "vru_accident" / "20260706" / "service_testbed" / "m6_im1_top5",
        "service_rerank": DATASETS / "processed" / "vru_accident" / "20260706" / "service_testbed" / "rw_t4_v1_im1_top5",
    },
    "aihub_intelligent_cctv": {
        "root": DATASETS / "processed" / "aihub_intelligent_cctv" / "20260706",
        "canonical": DATASETS / "processed" / "aihub_intelligent_cctv" / "20260706" / "canonical",
        "keyframes": DATASETS / "processed" / "aihub_intelligent_cctv" / "20260706" / "keyframes" / "event4_full",
        "visual_embeddings": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "visual_embeddings"
        / "clip-vit-base-patch32_full",
        "text_results": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "aihub_bgem3_faiss_b0_b5",
        "visual_results": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "visual_clip_full_m2_m4",
        "fusion_results": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "multimodal_fusion_clip_bgem3_m5_m6",
        "image_results": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "image_to_video_clip_full",
        "siglip_visual_embeddings": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "visual_embeddings"
        / "siglip-base-patch16-224_full",
        "siglip_visual_results": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "visual_siglip_full_m2_m4",
        "siglip_fusion_results": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "multimodal_fusion_siglip_bgem3_m5_m6",
        "siglip_image_results": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "image_to_video_siglip_full",
        "siglip_weighted_rerank": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "weighted_fusion_rerank_sweep_bgem3_siglip",
        "clip_k1_embeddings": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "visual_embeddings"
        / "clip-vit-base-patch32_k1_seq2",
        "clip_k2_embeddings": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "visual_embeddings"
        / "clip-vit-base-patch32_k2_seq1_2",
        "clip_k1_visual_results": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "visual_clip_k1_seq2_m2_m4",
        "clip_k2_visual_results": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "visual_clip_k2_seq1_2_m2_m4",
        "clip_k2_image_results": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "image_to_video_clip_k2_seq1_2",
        "weighted_rerank": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "results"
        / "weighted_fusion_rerank_sweep_bgem3_clip",
        "service_equal": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "service_testbed"
        / "m6_im1_top5",
        "service_rerank": DATASETS
        / "processed"
        / "aihub_intelligent_cctv"
        / "20260706"
        / "service_testbed"
        / "rw_t4_v1_im1_top5",
    },
}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_metric_all(path: Path, strategy: str | None = None) -> dict[str, Any]:
    df = pd.read_csv(path)
    if "difficulty" in df.columns:
        df = df[df["difficulty"].eq("all")]
    if strategy:
        df = df[df["strategy"].eq(strategy)]
    if df.empty:
        return {}
    return df.iloc[0].to_dict()


def required_files(config: dict[str, Path]) -> list[Path]:
    return [
        config["canonical"] / "clips.parquet",
        config["canonical"] / "documents.parquet",
        config["canonical"] / "metadata.parquet",
        config["canonical"] / "queries.jsonl",
        config["canonical"] / "qrels.tsv",
        config["keyframes"] / "frame_manifest.json",
        config["keyframes"] / "frames.parquet",
        config["visual_embeddings"] / "visual_embedding_manifest.json",
        config["visual_embeddings"] / "frame_embeddings.npy",
        config["visual_embeddings"] / "query_text_embeddings.npy",
        config["visual_results"] / "metrics_summary.csv",
        config["fusion_results"] / "metrics_summary.csv",
        config["image_results"] / "metrics_summary.csv",
        config["siglip_visual_embeddings"] / "visual_embedding_manifest.json",
        config["siglip_visual_embeddings"] / "frame_embeddings.npy",
        config["siglip_visual_embeddings"] / "query_text_embeddings.npy",
        config["siglip_visual_results"] / "metrics_summary.csv",
        config["siglip_fusion_results"] / "metrics_summary.csv",
        config["siglip_image_results"] / "metrics_summary.csv",
        config["siglip_weighted_rerank"] / "metrics_summary.csv",
        config["clip_k1_embeddings"] / "visual_embedding_manifest.json",
        config["clip_k2_embeddings"] / "visual_embedding_manifest.json",
        config["clip_k1_visual_results"] / "metrics_summary.csv",
        config["clip_k2_visual_results"] / "metrics_summary.csv",
        config["clip_k2_image_results"] / "metrics_summary.csv",
        config["weighted_rerank"] / "metrics_summary.csv",
        config["service_equal"] / "service_packet_summary.csv",
        config["service_rerank"] / "service_packet_summary.csv",
    ]


def audit_dataset(name: str, config: dict[str, Path]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    file_rows = []
    for path in required_files(config):
        file_rows.append(
            {
                "dataset": name,
                "path": str(path.relative_to(PROJECT_ROOT)),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else None,
            }
        )

    keyframe_manifest = read_json(config["keyframes"] / "frame_manifest.json")
    visual_manifest = read_json(config["visual_embeddings"] / "visual_embedding_manifest.json")
    visual_m2 = read_metric_all(config["visual_results"] / "metrics_summary.csv", "M2_visual_vector_only")
    visual_m4 = read_metric_all(config["visual_results"] / "metrics_summary.csv", "M4_metadata_prefilter_visual")
    fusion_m6 = read_metric_all(config["fusion_results"] / "metrics_summary.csv", "M6_text_visual_metadata_rrf")
    image_im1 = pd.read_csv(config["image_results"] / "metrics_summary.csv").iloc[0].to_dict()
    rerank_best = pd.read_csv(config["weighted_rerank"] / "metrics_summary.csv").sort_values(
        ["hit_at_1", "ndcg_at_10"], ascending=False
    ).iloc[0].to_dict()
    service_equal = pd.read_csv(config["service_equal"] / "service_packet_summary.csv")
    service_rerank = pd.read_csv(config["service_rerank"] / "service_packet_summary.csv")
    service_equal_all = service_equal[service_equal["query_type"].eq("all")].iloc[0].to_dict()
    service_rerank_all = service_rerank[service_rerank["query_type"].eq("all")].iloc[0].to_dict()

    metric_row = {
        "dataset": name,
        "clips_with_frames": keyframe_manifest.get("clips_with_frames"),
        "keyframes": keyframe_manifest.get("frames"),
        "frame_errors": keyframe_manifest.get("errors"),
        "visual_model": visual_manifest.get("model_path_or_id"),
        "visual_embedding_dim": visual_manifest.get("embedding_dim"),
        "text_queries": visual_manifest.get("query_count"),
        "m2_recall_at_10": visual_m2.get("recall_at_10"),
        "m2_ndcg_at_10": visual_m2.get("ndcg_at_10"),
        "m4_recall_at_10": visual_m4.get("recall_at_10"),
        "m4_ndcg_at_10": visual_m4.get("ndcg_at_10"),
        "m6_recall_at_10": fusion_m6.get("recall_at_10"),
        "m6_ndcg_at_10": fusion_m6.get("ndcg_at_10"),
        "im1_queries": image_im1.get("queries"),
        "im1_recall_at_1": image_im1.get("recall_at_1"),
        "im1_recall_at_10": image_im1.get("recall_at_10"),
        "rerank_best_strategy": rerank_best.get("strategy"),
        "rerank_hit_at_1": rerank_best.get("hit_at_1"),
        "rerank_ndcg_at_10": rerank_best.get("ndcg_at_10"),
        "service_equal_top1": service_equal_all.get("top1_relevant_rate"),
        "service_equal_hit_at_k": service_equal_all.get("hit_at_k"),
        "service_rerank_top1": service_rerank_all.get("top1_relevant_rate"),
        "service_rerank_hit_at_k": service_rerank_all.get("hit_at_k"),
        "service_rerank_frame_coverage": service_rerank_all.get("frame_coverage"),
    }
    return file_rows, metric_row


def write_markdown(metrics: pd.DataFrame, files: pd.DataFrame, path: Path) -> None:
    failed = files[~files["exists"]]
    lines = [
        "# True Multimodal Pipeline Audit",
        "",
        f"created_at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Status",
        "",
        f"- required_files: `{len(files)}`",
        f"- missing_files: `{len(failed)}`",
        "",
        "## Manuscript Metrics",
        "",
        "| dataset | keyframes | M4 R@10 | M4 nDCG@10 | M6 R@10 | IM1 R@10 | rerank best | rerank Hit@1 | service top1 |",
        "|---|---:|---:|---:|---:|---:|---|---:|---:|",
    ]
    for row in metrics.to_dict("records"):
        lines.append(
            f"| {row['dataset']} | {int(row['keyframes'])} | {row['m4_recall_at_10']:.4f} | "
            f"{row['m4_ndcg_at_10']:.4f} | {row['m6_recall_at_10']:.4f} | "
            f"{row['im1_recall_at_10']:.4f} | {row['rerank_best_strategy']} | "
            f"{row['rerank_hit_at_1']:.4f} | {row['service_rerank_top1']:.4f} |"
        )
    lines.extend(["", "## Missing Files", ""])
    if failed.empty:
        lines.append("None.")
    else:
        for row in failed.to_dict("records"):
            lines.append(f"- `{row['path']}`")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    file_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []
    for name, config in DATASET_CONFIGS.items():
        files, metrics = audit_dataset(name, config)
        file_rows.extend(files)
        metric_rows.append(metrics)

    files_df = pd.DataFrame(file_rows)
    metrics_df = pd.DataFrame(metric_rows)
    files_df.to_csv(OUTPUT_DIR / "required_files_audit.csv", index=False)
    metrics_df.to_csv(OUTPUT_DIR / "manuscript_metrics_summary.csv", index=False)
    write_markdown(metrics_df, files_df, OUTPUT_DIR / "summary.md")
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_dir": str(OUTPUT_DIR.relative_to(PROJECT_ROOT)),
        "datasets": list(DATASET_CONFIGS),
        "required_files": int(len(files_df)),
        "missing_files": int((~files_df["exists"]).sum()),
        "advanced_ablation_summary_exists": (
            PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260707_advanced_ablation" / "summary.md"
        ).exists(),
    }
    (OUTPUT_DIR / "run_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"output_dir={OUTPUT_DIR}")
    print(f"missing_files={manifest['missing_files']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
