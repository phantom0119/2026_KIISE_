#!/usr/bin/env python3
"""Create deterministic stratified clip samples for AI Hub 71953."""

from __future__ import annotations

import argparse
import json
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


def metadata_wide(metadata: pd.DataFrame) -> pd.DataFrame:
    return (
        metadata.pivot_table(index="clip_id", columns="facet_name", values="facet_value", aggfunc="first")
        .reset_index()
        .fillna("")
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--per-event-class-split", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20260708)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    if args.output_dir.exists() and args.overwrite:
        shutil.rmtree(args.output_dir)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    clips = pd.read_parquet(args.canonical_root / "clips.parquet")
    metadata = pd.read_parquet(args.canonical_root / "metadata.parquet")
    wide = metadata_wide(metadata)
    table = clips[["clip_id"]].merge(wide, on="clip_id", how="left").fillna("")
    required = {"source_split", "event_class"}
    missing = required - set(table.columns)
    if missing:
        raise ValueError(f"Missing required facets: {sorted(missing)}")

    rng = random.Random(args.seed)
    sampled_rows: list[dict[str, Any]] = []
    stratum_rows: list[dict[str, Any]] = []
    grouped = table.groupby(["event_class", "source_split"], sort=True)
    for (event_class, source_split), group in grouped:
        clip_ids = sorted(map(str, group["clip_id"].tolist()))
        rng.shuffle(clip_ids)
        selected = sorted(clip_ids[: min(args.per_event_class_split, len(clip_ids))])
        stratum_rows.append(
            {
                "event_class": event_class,
                "source_split": source_split,
                "available": len(clip_ids),
                "selected": len(selected),
            }
        )
        for clip_id in selected:
            sampled_rows.append(
                {
                    "clip_id": clip_id,
                    "event_class": event_class,
                    "source_split": source_split,
                }
            )

    sample = pd.DataFrame(sampled_rows).sort_values(["event_class", "source_split", "clip_id"]).reset_index(drop=True)
    strata = pd.DataFrame(stratum_rows).sort_values(["event_class", "source_split"]).reset_index(drop=True)
    sample.to_csv(args.output_dir / "clip_sample.csv", index=False)
    strata.to_csv(args.output_dir / "strata_summary.csv", index=False)
    (args.output_dir / "clip_ids.txt").write_text("\n".join(sample["clip_id"].tolist()) + "\n", encoding="utf-8")

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "output_dir": str(args.output_dir),
        "sampling_policy": "Balanced deterministic sample by event_class x source_split.",
        "per_event_class_split": args.per_event_class_split,
        "seed": args.seed,
        "source_clips": int(len(clips)),
        "sampled_clips": int(len(sample)),
        "strata": int(len(strata)),
        "min_selected_per_stratum": int(strata["selected"].min()) if not strata.empty else 0,
        "max_selected_per_stratum": int(strata["selected"].max()) if not strata.empty else 0,
    }
    (args.output_dir / "sample_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    lines = [
        "# AI Hub 71953 Stratified Clip Sample",
        "",
        f"created_at: `{manifest['created_at']}`",
        f"policy: `{manifest['sampling_policy']}`",
        "",
        "| item | value |",
        "|---|---:|",
        f"| source_clips | {manifest['source_clips']} |",
        f"| sampled_clips | {manifest['sampled_clips']} |",
        f"| strata | {manifest['strata']} |",
        f"| per_event_class_split | {manifest['per_event_class_split']} |",
        f"| seed | {manifest['seed']} |",
        "",
        "## Strata",
        "",
        "| event_class | source_split | available | selected |",
        "|---|---|---:|---:|",
    ]
    for row in strata.to_dict("records"):
        lines.append(
            f"| {row['event_class']} | {row['source_split']} | {row['available']} | {row['selected']} |"
        )
    (args.output_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"output_dir={args.output_dir}")
    print(f"source_clips={manifest['source_clips']}")
    print(f"sampled_clips={manifest['sampled_clips']}")
    print(f"strata={manifest['strata']}")
    print(f"seed={manifest['seed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
