#!/usr/bin/env python3
"""Audit AI Hub 71953 canonical and evidence-frame artifacts."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def metadata_wide(metadata: pd.DataFrame) -> pd.DataFrame:
    return (
        metadata.pivot_table(index="clip_id", columns="facet_name", values="facet_value", aggfunc="first")
        .reset_index()
        .fillna("")
    )


def filter_clip_ids(wide: pd.DataFrame, filters: dict[str, Any]) -> set[str]:
    if not filters:
        return set(wide["clip_id"])
    mask = pd.Series(True, index=wide.index)
    for key, value in filters.items():
        if key not in wide.columns:
            return set()
        mask &= wide[key].eq(str(value))
    return set(wide.loc[mask, "clip_id"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--frame-root", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    clips = pd.read_parquet(args.canonical_root / "clips.parquet")
    views = pd.read_parquet(args.canonical_root / "views.parquet")
    evidence = pd.read_parquet(args.canonical_root / "evidence_frames.parquet")
    documents = pd.read_parquet(args.canonical_root / "documents.parquet")
    metadata = pd.read_parquet(args.canonical_root / "metadata.parquet")
    queries = pd.DataFrame(read_jsonl(args.canonical_root / "queries.jsonl"))
    qrels = pd.read_csv(args.canonical_root / "qrels.tsv", sep="\t")

    clip_ids = set(clips["clip_id"])
    query_ids = set(queries["query_id"])
    qrel_target_errors = sorted(set(qrels["target_id"]) - clip_ids)
    qrel_query_errors = sorted(set(qrels["query_id"]) - query_ids)

    view_counts = views.groupby("clip_id")["view"].nunique()
    missing_two_views = sorted(view_counts[view_counts.ne(2)].index.tolist())
    view_name_sets = views.groupby("clip_id")["view"].apply(lambda s: ",".join(sorted(set(map(str, s)))))
    missing_c1c2 = sorted(view_name_sets[view_name_sets.ne("c1,c2")].index.tolist())
    evidence_counts = evidence.groupby(["clip_id", "view"]).size()
    low_evidence_pairs = evidence_counts[evidence_counts.lt(1)].reset_index().to_dict("records")

    wide = metadata_wide(metadata)
    missing_filter_facets: list[dict[str, Any]] = []
    empty_filter_candidates = 0
    positive_not_in_filter = 0
    positives_by_query = {
        query_id: set(group["target_id"])
        for query_id, group in qrels.groupby("query_id", sort=False)
    }
    for row in queries.to_dict("records"):
        filters = row.get("metadata_filter") or {}
        missing = [key for key in filters if key not in wide.columns]
        if missing:
            missing_filter_facets.append({"query_id": row["query_id"], "missing": missing})
            continue
        candidates = filter_clip_ids(wide, filters)
        if not candidates:
            empty_filter_candidates += 1
        positives = positives_by_query.get(row["query_id"], set())
        if filters and not positives.issubset(candidates):
            positive_not_in_filter += 1

    frame_summary: dict[str, Any] = {
        "frame_root": str(args.frame_root) if args.frame_root else None,
        "frames": 0,
        "clips_with_frames": 0,
        "views_with_frames": 0,
        "missing_frame_files": None,
    }
    if args.frame_root is not None:
        frames = pd.read_parquet(args.frame_root / "frames.parquet")
        missing_frame_files = [path for path in frames["frame_path"].tolist() if not Path(path).exists()]
        frame_summary = {
            "frame_root": str(args.frame_root),
            "frames": int(len(frames)),
            "clips_with_frames": int(frames["clip_id"].nunique()) if not frames.empty else 0,
            "views_with_frames": int(frames[["clip_id", "view"]].drop_duplicates().shape[0]) if not frames.empty else 0,
            "missing_frame_files": int(len(missing_frame_files)),
        }

    audit = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "counts": {
            "clips": int(len(clips)),
            "views": int(len(views)),
            "evidence_frames": int(len(evidence)),
            "documents": int(len(documents)),
            "metadata_rows": int(len(metadata)),
            "queries": int(len(queries)),
            "qrels": int(len(qrels)),
            "distinct_event_classes": int(metadata[metadata["facet_name"].eq("event_class")]["facet_value"].nunique()),
        },
        "integrity": {
            "qrel_target_errors": len(qrel_target_errors),
            "qrel_query_errors": len(qrel_query_errors),
            "missing_two_views": len(missing_two_views),
            "missing_c1c2_view_pairs": len(missing_c1c2),
            "low_evidence_pairs": len(low_evidence_pairs),
            "missing_filter_facets": len(missing_filter_facets),
            "empty_filter_candidates": empty_filter_candidates,
            "positive_not_in_filter": positive_not_in_filter,
        },
        "frame_materialization": frame_summary,
        "pass": (
            not qrel_target_errors
            and not qrel_query_errors
            and not missing_two_views
            and not missing_c1c2
            and not missing_filter_facets
            and empty_filter_candidates == 0
            and positive_not_in_filter == 0
            and (frame_summary["missing_frame_files"] in {None, 0})
        ),
    }

    (args.output_dir / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# AI Hub 71953 Pipeline Audit",
        "",
        f"created_at: `{audit['created_at']}`",
        f"canonical_root: `{audit['canonical_root']}`",
        f"pass: `{audit['pass']}`",
        "",
        "## Counts",
        "",
        "| item | value |",
        "|---|---:|",
    ]
    for key, value in audit["counts"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Integrity", "", "| check | errors |", "|---|---:|"])
    for key, value in audit["integrity"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(["", "## Frame Materialization", "", "| item | value |", "|---|---:|"])
    for key, value in audit["frame_materialization"].items():
        lines.append(f"| {key} | {value} |")
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"output_dir={args.output_dir}")
    print(f"pass={audit['pass']}")
    print(f"clips={audit['counts']['clips']}")
    print(f"views={audit['counts']['views']}")
    print(f"evidence_frames={audit['counts']['evidence_frames']}")
    print(f"queries={audit['counts']['queries']}")
    print(f"qrels={audit['counts']['qrels']}")
    print(f"missing_frame_files={audit['frame_materialization']['missing_frame_files']}")
    return 0 if audit["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
