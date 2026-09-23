#!/usr/bin/env python3
"""Measure existing raw/keyframe/caption storage for the P0-C safety corpora."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

import analyze_safety_representation as base


ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PROJECT = Path("/home/explorer/vectorDB/experiments/db/KIISE_datasociety")


def resolve(path_value: str) -> Path:
    path = Path(path_value)
    return path if path.is_absolute() else PROJECT / path


def main() -> int:
    per_clip_rows = []
    missing = []
    for dataset, config in base.CONFIGS.items():
        canonical = Path(config["canonical"])
        visual = Path(config["visual"])
        clips = pd.read_parquet(canonical / "clips.parquet")
        documents = pd.read_parquet(canonical / "documents.parquet")
        frames = pd.read_parquet(visual / "frame_index.parquet")
        caption_bytes = (
            documents.assign(text_bytes=documents["text"].fillna("").map(lambda value: len(str(value).encode("utf-8"))))
            .groupby("clip_id")["text_bytes"]
            .sum()
            .to_dict()
        )
        frame_bytes: dict[str, list[tuple[int, int]]] = {}
        for row in frames[["clip_id", "frame_seq", "frame_path"]].to_dict("records"):
            path = resolve(str(row["frame_path"]))
            if not path.exists():
                missing.append(str(path))
                size = 0
            else:
                size = path.stat().st_size
            frame_bytes.setdefault(str(row["clip_id"]), []).append((int(row["frame_seq"]), int(size)))

        for row in clips[["clip_id", "media_path"]].to_dict("records"):
            clip_id = str(row["clip_id"])
            media = resolve(str(row["media_path"]))
            if not media.exists():
                missing.append(str(media))
                raw_bytes = 0
            else:
                raw_bytes = media.stat().st_size
            ordered = sorted(frame_bytes.get(clip_id, []))
            all_jpeg = sum(size for _, size in ordered)
            center_jpeg = next((size for seq, size in ordered if seq == 1), 0)
            text_bytes = int(caption_bytes.get(clip_id, 0))
            per_clip_rows.extend(
                [
                    {"dataset": dataset, "clip_id": clip_id, "arm": "raw_video", "bytes": raw_bytes},
                    {
                        "dataset": dataset,
                        "clip_id": clip_id,
                        "arm": "caption_stack",
                        "bytes": text_bytes + base.COSTS["caption"],
                    },
                    {
                        "dataset": dataset,
                        "clip_id": clip_id,
                        "arm": "center_frame_stack",
                        "bytes": center_jpeg + base.COSTS["center_frame"],
                    },
                    {
                        "dataset": dataset,
                        "clip_id": clip_id,
                        "arm": "visual_4frame_stack",
                        "bytes": all_jpeg + base.COSTS["visual_4frame"],
                    },
                    {
                        "dataset": dataset,
                        "clip_id": clip_id,
                        "arm": "fusion_stack",
                        "bytes": text_bytes + base.COSTS["caption"] + all_jpeg + base.COSTS["visual_4frame"],
                    },
                ]
            )

    per_clip = pd.DataFrame(per_clip_rows)
    summaries = []
    for dataset, group in per_clip.groupby("dataset"):
        raw_total = group[group["arm"].eq("raw_video")]["bytes"].sum()
        for arm, arm_group in group.groupby("arm"):
            total = int(arm_group["bytes"].sum())
            summaries.append(
                {
                    "dataset": dataset,
                    "arm": arm,
                    "clips": arm_group["clip_id"].nunique(),
                    "total_bytes": total,
                    "total_gib": total / (1024**3),
                    "mean_kib_per_clip": arm_group["bytes"].mean() / 1024,
                    "median_kib_per_clip": arm_group["bytes"].median() / 1024,
                    "p95_kib_per_clip": arm_group["bytes"].quantile(0.95) / 1024,
                    "raw_to_arm_ratio": raw_total / total if total else None,
                }
            )
    summary = pd.DataFrame(summaries)
    decision = {
        "status": "STORAGE_AUDIT_PASS" if not missing else "STORAGE_AUDIT_MISSING_FILES",
        "missing_file_count": len(missing),
        "scope": "existing artifact bytes; excludes DB overhead and generation/compute cost",
    }
    per_clip.to_csv(RESULTS / "safety_storage_per_clip.csv", index=False)
    summary.to_csv(RESULTS / "safety_storage_summary.csv", index=False)
    (RESULTS / "safety_storage_audit.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# P0-C 실제 저장량 감사",
        "",
        f"> 판정: **`{decision['status']}`**  ",
        "> 기존 파일의 byte 크기만 합산했다. 생성 GPU 비용, DB/FAISS 오버헤드, metadata/lineage 비용은 포함하지 않는다.",
        "",
        "| dataset | arm | clips | total GiB | mean KiB/clip | median KiB/clip | p95 KiB/clip | raw/arm |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.sort_values(["dataset", "total_bytes"], ascending=[True, False]).to_dict("records"):
        lines.append(
            f"| {row['dataset']} | {row['arm']} | {int(row['clips'])} | {row['total_gib']:.4f} | "
            f"{row['mean_kib_per_clip']:.2f} | {row['median_kib_per_clip']:.2f} | {row['p95_kib_per_clip']:.2f} | "
            f"{row['raw_to_arm_ratio']:.2f}× |"
        )
    lines.extend(
        [
            "",
            "## 해석",
            "",
            "- `caption_stack`: UTF-8 caption + BGE-M3 float32 vector",
            "- `center_frame_stack`: 중앙 JPEG 1장 + CLIP float32 vector",
            "- `visual_4frame_stack`: JPEG 4장 + CLIP vector 4개",
            "- `fusion_stack`: caption stack + visual 4-frame stack",
            "- 저장 절감 가능성은 시스템 연구의 비용 동기를 확인하지만, 서비스별 표현 비지배성이나 온라인 제어기 이득을 대신 증명하지 않는다.",
            "",
        ]
    )
    (ROOT / "P0_CPU_SAFETY_STORAGE_AUDIT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0 if not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())

