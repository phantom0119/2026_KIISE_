#!/usr/bin/env python3
"""Build canonical AI Hub 71953 multi-angle CCTV workload artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "03_src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.adapters.aihub_multi_angle_cctv import AIHubMultiAngleCCTVAdapter  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=PROJECT_ROOT / "Datasets",
        help="Logical Datasets root.",
    )
    parser.add_argument(
        "--source-root",
        type=Path,
        default=None,
        help="Raw AI Hub 71953 source root. Defaults to Datasets/external/21.다각도 CCTV 생활안전 데이터.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "Datasets" / "processed",
        help="Processed artifact root.",
    )
    parser.add_argument(
        "--dataset-version",
        default="20260708",
        help="Canonical dataset version label.",
    )
    parser.add_argument("--max-events", type=int, default=None, help="Optional smoke-test limit.")
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    adapter = AIHubMultiAngleCCTVAdapter(
        dataset_root=args.dataset_root,
        output_root=args.output_root,
        dataset_version=args.dataset_version,
        source_root=args.source_root,
        max_events=args.max_events,
    )
    result = adapter.build(overwrite=args.overwrite)
    print(f"output_dir={result.output_dir}")
    print(f"clips={result.clips}")
    print(f"views={result.views}")
    print(f"evidence_frames={result.evidence_frames}")
    print(f"documents={result.documents}")
    print(f"metadata_rows={result.metadata_rows}")
    print(f"queries={result.queries}")
    print(f"qrels={result.qrels}")
    print(f"missing_media_entries={result.missing_media_entries}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
