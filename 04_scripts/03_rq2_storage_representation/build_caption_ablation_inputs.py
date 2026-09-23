#!/usr/bin/env python3
"""Freeze the exact image inputs used by the caption-model ablation.

The ablation changes only the caption generator. Corpus membership, frame choice,
prompt, queries, predicates, relevance labels, and downstream text encoder remain
fixed. The existing Qwen2.5-VL artifacts define the locked corpus membership.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATASETS = PROJECT_ROOT / "Datasets"
DEFAULT_ROOT = Path("/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715")

PROMPTS = {
    "522": (
        "Describe this urban intersection CCTV frame in 2-4 factual sentences: "
        "overall traffic volume, visible vehicle types (cars, buses, trucks, "
        "two-wheelers), any stopped or parked vehicles, pedestrians or cyclists, "
        "and road/weather appearance. State only what is visible; no speculation."
    ),
    "meva": (
        "Describe this outdoor fixed surveillance camera frame in 2-4 factual "
        "sentences: the people present and what they appear to be doing, any "
        "vehicles, objects being carried, opened, or exchanged, doors or "
        "building entrances, and the general setting. State only what is "
        "visible; no speculation."
    ),
    "uca": (
        "Describe this surveillance camera frame in 2-4 factual sentences: "
        "the setting, the people visible and what they are doing, any "
        "vehicles or objects present, and anything notable happening."
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def build_522() -> pd.DataFrame:
    ver = DATASETS / "processed" / "aihub_522_intersection" / "20260710"
    docs = pd.read_parquet(ver / "captions" / "documents.parquet")
    return pd.DataFrame(
        {
            "dataset": "522",
            "item_id": docs["doc_id"],
            "source_doc_id": docs["doc_id"],
            "clip_id": docs["clip_id"],
            "visual_video_id": docs["visual_video_id"],
            "video_id": "",
            "split": docs["split"],
            "frame_path": docs["source_frame"].map(lambda p: str((ver / p).resolve())),
            "source_frame": docs["source_frame"],
            "baseline_caption": docs["text"],
            "prompt": PROMPTS["522"],
        }
    )


def build_meva() -> pd.DataFrame:
    ver = DATASETS / "processed" / "meva_kf1" / "20260713"
    docs = pd.read_parquet(ver / "captions" / "documents.parquet")
    return pd.DataFrame(
        {
            "dataset": "meva",
            "item_id": docs["doc_id"],
            "source_doc_id": docs["doc_id"],
            "clip_id": docs["clip_id"],
            "visual_video_id": "",
            "video_id": "",
            "split": "",
            "frame_path": docs["source_frame"].map(lambda p: str(Path(p).resolve())),
            "source_frame": docs["source_frame"],
            "baseline_caption": docs["text"],
            "prompt": PROMPTS["meva"],
        }
    )


def build_uca() -> pd.DataFrame:
    root = DATASETS / "processed" / "uca_anchor" / "20260712"
    docs = pd.read_parquet(root / "captions" / "documents.parquet")
    seg = pd.read_parquet(root / "segments.parquet")
    base = docs.merge(
        seg[["doc_id", "video_id", "split", "frame"]],
        on=["doc_id", "video_id", "split"],
        how="inner",
        validate="one_to_one",
    )
    return pd.DataFrame(
        {
            "dataset": "uca",
            "item_id": base["doc_id"],
            "source_doc_id": base["doc_id"],
            "clip_id": "",
            "visual_video_id": "",
            "video_id": base["video_id"],
            "split": base["split"],
            "frame_path": base["frame"].map(lambda p: str(Path(p).resolve())),
            "source_frame": base["frame"],
            "baseline_caption": base["caption"],
            "prompt": PROMPTS["uca"],
        }
    )


def validate(dataset: str, frame: pd.DataFrame) -> dict:
    if frame.empty:
        raise ValueError(f"{dataset}: locked input table is empty")
    if frame["item_id"].duplicated().any():
        dup = frame.loc[frame["item_id"].duplicated(), "item_id"].head().tolist()
        raise ValueError(f"{dataset}: duplicate item ids: {dup}")
    missing = frame.loc[~frame["frame_path"].map(lambda p: Path(p).is_file()), "frame_path"]
    if len(missing):
        raise FileNotFoundError(f"{dataset}: {len(missing)} frames missing; first={missing.iloc[0]}")
    prompts = frame["prompt"].drop_duplicates().tolist()
    if prompts != [PROMPTS[dataset]]:
        raise ValueError(f"{dataset}: prompt mismatch")
    if frame["baseline_caption"].fillna("").str.strip().eq("").any():
        raise ValueError(f"{dataset}: blank baseline caption")
    return {
        "dataset": dataset,
        "items": int(len(frame)),
        "unique_items": int(frame["item_id"].nunique()),
        "all_frames_exist": True,
        "prompt_sha256": hashlib.sha256(PROMPTS[dataset].encode()).hexdigest(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=DEFAULT_ROOT)
    args = parser.parse_args()
    input_root = args.output_root / "inputs"
    input_root.mkdir(parents=True, exist_ok=True)

    builders = {"522": build_522, "meva": build_meva, "uca": build_uca}
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_root": str(args.output_root),
        "membership_rule": "exact item ids and frames from the frozen Qwen2.5-VL corpus",
        "datasets": {},
    }
    for dataset, builder in builders.items():
        frame = builder().sort_values("item_id", kind="stable").reset_index(drop=True)
        stats = validate(dataset, frame)
        path = input_root / f"{dataset}_items.parquet"
        frame.to_parquet(path, index=False)
        stats["path"] = str(path)
        stats["sha256"] = sha256_file(path)
        manifest["datasets"][dataset] = stats
        print(f"[{dataset}] {len(frame)} locked frames -> {path}")

    (input_root / "input_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
