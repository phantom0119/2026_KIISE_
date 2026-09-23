#!/usr/bin/env python3
"""Build canonical staging artifacts for CityFlow-NL annotations.

This script intentionally builds an annotation-only canonical workload when
CityFlow image/video assets are not available locally. It records frame path
references and bounding boxes so that the workload can be upgraded to true
visual retrieval as soon as the AI City/CityFlow frame assets are obtained.
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frame_ref(frame_ref: str) -> dict[str, str]:
    parts = Path(frame_ref.replace("./", "")).parts
    # Expected: validation/S02/c006/img1/000001.jpg or train/S01/c003/img1/...
    parsed = {
        "frame_source_split": parts[0] if len(parts) > 0 else "",
        "scene_id": parts[1] if len(parts) > 1 else "",
        "camera_id": parts[2] if len(parts) > 2 else "",
        "image_subdir": parts[3] if len(parts) > 3 else "",
        "frame_file": parts[4] if len(parts) > 4 else "",
    }
    return parsed


def frame_number(frame_ref: str) -> int | None:
    stem = Path(frame_ref).stem
    try:
        return int(stem)
    except ValueError:
        return None


def track_clip_id(split: str, uuid: str) -> str:
    return f"cityflow_nl:{split}:{uuid}"


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")


def build_split_tracks(
    *,
    split: str,
    tracks: dict[str, Any],
    repo_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], int]:
    clips: list[dict[str, Any]] = []
    documents: list[dict[str, Any]] = []
    metadata: list[dict[str, Any]] = []
    present_frame_files = 0

    for uuid, rec in sorted(tracks.items()):
        frames = list(rec.get("frames", []))
        boxes = list(rec.get("boxes", []))
        first_ref = frames[0] if frames else ""
        last_ref = frames[-1] if frames else ""
        parsed = parse_frame_ref(first_ref) if first_ref else {
            "frame_source_split": "",
            "scene_id": "",
            "camera_id": "",
            "image_subdir": "",
            "frame_file": "",
        }
        first_num = frame_number(first_ref)
        last_num = frame_number(last_ref)
        present = sum((repo_root / ref).exists() for ref in frames)
        present_frame_files += present
        clip_id = track_clip_id(split, uuid)
        clips.append(
            {
                "clip_id": clip_id,
                "dataset_id": "cityflow_nl",
                "source_track_uuid": uuid,
                "split": split,
                "media_path": "",
                "first_frame_ref": first_ref,
                "last_frame_ref": last_ref,
                "frame_count": len(frames),
                "box_count": len(boxes),
                "first_frame_number": first_num,
                "last_frame_number": last_num,
                "scene_id": parsed["scene_id"],
                "camera_id": parsed["camera_id"],
                "frame_source_split": parsed["frame_source_split"],
                "visual_assets_available": present == len(frames) and len(frames) > 0,
                "present_frame_files": present,
            }
        )
        for facet, value in {
            "split": split,
            "scene_id": parsed["scene_id"],
            "camera_id": parsed["camera_id"],
            "frame_source_split": parsed["frame_source_split"],
            "has_nl": bool(rec.get("nl")),
            "has_nl_other_views": bool(rec.get("nl_other_views")),
            "visual_assets_available": present == len(frames) and len(frames) > 0,
        }.items():
            metadata.append(
                {
                    "clip_id": clip_id,
                    "dataset_id": "cityflow_nl",
                    "facet_name": facet,
                    "facet_value": str(value),
                }
            )
        for idx, text in enumerate(rec.get("nl", []), start=1):
            documents.append(
                {
                    "doc_id": f"{clip_id}:nl:{idx}",
                    "clip_id": clip_id,
                    "dataset_id": "cityflow_nl",
                    "doc_type": "natural_language_description",
                    "text": text,
                    "source": "nl",
                }
            )
        for idx, text in enumerate(rec.get("nl_other_views", []), start=1):
            documents.append(
                {
                    "doc_id": f"{clip_id}:nl_other:{idx}",
                    "clip_id": clip_id,
                    "dataset_id": "cityflow_nl",
                    "doc_type": "natural_language_other_view_description",
                    "text": text,
                    "source": "nl_other_views",
                }
            )
    return clips, documents, metadata, present_frame_files


def build_train_queries(train_tracks: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    queries: list[dict[str, Any]] = []
    qrels: list[dict[str, Any]] = []
    for uuid, rec in sorted(train_tracks.items()):
        clip_id = track_clip_id("train", uuid)
        for idx, text in enumerate(rec.get("nl", []), start=1):
            query_id = f"cityflow_nl:train_nl:{uuid}:{idx}"
            queries.append(
                {
                    "query_id": query_id,
                    "dataset_id": "cityflow_nl",
                    "query_text": text,
                    "task": "natural_language_vehicle_track_retrieval",
                    "metadata_filter": {},
                    "semantic_filter": {"source": "cityflow_nl_train_nl"},
                    "qrel_filter": {"source_track_uuid": uuid},
                    "difficulty": "nl_track",
                    "positive_count": 1,
                }
            )
            qrels.append(
                {
                    "query_id": query_id,
                    "target_id": clip_id,
                    "target_type": "clip",
                    "relevance": 3,
                }
            )
    return queries, qrels


def summarize_frame_refs(tracks: dict[str, Any]) -> dict[str, Any]:
    scenes = Counter()
    cameras = Counter()
    refs = 0
    for rec in tracks.values():
        for frame_ref in rec.get("frames", []):
            parsed = parse_frame_ref(frame_ref)
            scenes[parsed["scene_id"]] += 1
            cameras[f"{parsed['scene_id']}/{parsed['camera_id']}"] += 1
            refs += 1
    return {
        "frame_refs": refs,
        "unique_scenes": len(scenes),
        "unique_scene_cameras": len(cameras),
        "top_scenes": scenes.most_common(10),
        "top_scene_cameras": cameras.most_common(10),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--raw-zip", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    if args.output_dir.exists() and args.overwrite:
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    train_tracks = load_json(args.repo_root / "data" / "train-tracks.json")
    test_tracks = load_json(args.repo_root / "data" / "test-tracks.json")
    test_queries = load_json(args.repo_root / "data" / "test-queries.json")

    train_clips, train_docs, train_metadata, train_present = build_split_tracks(
        split="train",
        tracks=train_tracks,
        repo_root=args.repo_root,
    )
    test_clips, test_docs, test_metadata, test_present = build_split_tracks(
        split="test",
        tracks=test_tracks,
        repo_root=args.repo_root,
    )
    queries, qrels = build_train_queries(train_tracks)

    clips = pd.DataFrame([*train_clips, *test_clips])
    documents = pd.DataFrame([*train_docs, *test_docs])
    metadata = pd.DataFrame([*train_metadata, *test_metadata])
    qrels_df = pd.DataFrame(qrels)

    clips.to_parquet(args.output_dir / "clips.parquet", index=False)
    documents.to_parquet(args.output_dir / "documents.parquet", index=False)
    metadata.to_parquet(args.output_dir / "metadata.parquet", index=False)
    write_jsonl(args.output_dir / "queries.jsonl", queries)
    qrels_df.to_csv(args.output_dir / "qrels.tsv", sep="\t", index=False)

    train_ref_summary = summarize_frame_refs(train_tracks)
    test_ref_summary = summarize_frame_refs(test_tracks)
    raw_zip_available = args.raw_zip is not None and args.raw_zip.exists()
    manifest = {
        "dataset_id": "cityflow_nl",
        "dataset_version": "20260707",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_repo": "https://github.com/fredfung007/cityflow-nl",
        "repo_root": str(args.repo_root),
        "output_dir": str(args.output_dir),
        "license": "Apache-2.0 for cloned GitHub repository contents",
        "raw_zip_path": str(args.raw_zip) if args.raw_zip else "",
        "raw_zip_available": raw_zip_available,
        "raw_zip_size_bytes": args.raw_zip.stat().st_size if raw_zip_available else 0,
        "visual_asset_status": "frame path references exist in annotations, but image/video files are not present locally",
        "ai_city_download_status": "AIC 2023 Track 2 direct Google Drive download is listed on the official AI City Dataset Quick Access page; license acceptance required",
        "counts": {
            "train_tracks": len(train_tracks),
            "test_tracks": len(test_tracks),
            "test_queries_without_qrels": len(test_queries),
            "clips": int(len(clips)),
            "documents": int(len(documents)),
            "metadata_rows": int(len(metadata)),
            "train_queries": int(len(queries)),
            "qrels": int(len(qrels_df)),
            "present_frame_files": int(train_present + test_present),
        },
        "train_frame_refs": train_ref_summary,
        "test_frame_refs": test_ref_summary,
    }
    (args.output_dir / "dataset_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    raw_zip_status = (
        f"- AI City 2023 Track 2 원본 데이터 zip: 로컬 확보 완료 (`{args.raw_zip}`, {args.raw_zip.stat().st_size} bytes)"
        if raw_zip_available
        else "- AI City 2023 Track 2 원본 데이터 zip: 공식 Dataset Quick Access 페이지에서 직접 다운로드 링크 확인, 로컬 미확보"
    )
    lines = [
        "# CityFlow-NL Canonical Staging Summary",
        "",
        f"created_at: `{manifest['created_at']}`",
        "",
        "## Status",
        "",
        "- GitHub annotation repository: 확보 완료",
        raw_zip_status,
        "- 현재 canonical: annotation-only staging",
        "- true multimodal visual retrieval 투입 조건: zip 압축 해제, AVI frame extraction, frame refs 연결",
        "",
        "## Counts",
        "",
        "| item | count |",
        "|---|---:|",
    ]
    for key, value in manifest["counts"].items():
        lines.append(f"| {key} | {value} |")
    next_steps = [
        "1. 현재 zip을 `Datasets/raw/cityflow_nl/aicity2023_track2`에 압축 해제한다.",
        "2. zip 내부 `vdo.avi`에서 annotation이 참조하는 frame 또는 track crop을 추출한다.",
        "3. `train-tracks.json`/`test-tracks.json`의 frame refs와 실제 파일 경로를 매핑한다.",
        "4. track별 대표 프레임 또는 box crop을 생성한 뒤 CLIP/SigLIP embedding을 구축한다.",
        "5. 현재 canonical의 train NL queries/qrels를 사용해 natural-language vehicle-track retrieval을 수행한다.",
    ] if raw_zip_available else [
        "1. 공식 AI City Dataset Quick Access 페이지의 2023 Track 2 링크에서 `AICity23_Track2_NL_Retrieval.zip`을 다운로드한다.",
        "2. 다운로드한 zip을 `Datasets/external/cityflow_nl/aicity2023_track2`에 보존하고, 압축 해제본은 `Datasets/raw/cityflow_nl/aicity2023_track2`에 둔다.",
        "3. `train-tracks.json`/`test-tracks.json`의 frame refs와 실제 파일 경로를 매핑한다.",
        "4. track별 대표 프레임 또는 box crop을 생성한 뒤 CLIP/SigLIP embedding을 구축한다.",
        "5. 현재 canonical의 train NL queries/qrels를 사용해 natural-language vehicle-track retrieval을 수행한다.",
    ]
    lines.extend(
        [
            "",
            "## Use Decision",
            "",
            "현재 상태에서는 자연어 질의, track UUID, frame reference, bounding box annotation은 사용할 수 있다. 그러나 실제 이미지 파일이 없으므로 CLIP/SigLIP visual embedding 기반 true multimodal main experiment에는 아직 포함하면 안 된다.",
            "",
            "권장 절차:",
            "",
            *next_steps,
        ]
    )
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"output_dir={args.output_dir}")
    print(f"clips={len(clips)}")
    print(f"documents={len(documents)}")
    print(f"queries={len(queries)}")
    print(f"qrels={len(qrels_df)}")
    print(f"present_frame_files={train_present + test_present}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
