#!/usr/bin/env python3
"""Build canonical AI Hub intelligent CCTV workload artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.adapters.aihub_intelligent_cctv import AIHubIntelligentCCTVAdapter  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=PROJECT_ROOT / "Datasets",
        help="Logical Datasets root.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=PROJECT_ROOT / "Datasets" / "processed",
        help="Processed artifact root.",
    )
    parser.add_argument(
        "--dataset-version",
        default="20260706",
        help="Canonical dataset version label.",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    adapter = AIHubIntelligentCCTVAdapter(
        dataset_root=args.dataset_root,
        output_root=args.output_root,
        dataset_version=args.dataset_version,
    )
    result = adapter.build(overwrite=args.overwrite)
    print(f"output_dir={result.output_dir}")
    print(f"clips={result.clips}")
    print(f"documents={result.documents}")
    print(f"metadata_rows={result.metadata_rows}")
    print(f"queries={result.queries}")
    print(f"qrels={result.qrels}")
    print(f"missing_media={result.missing_media}")
    print(f"missing_labels={result.missing_labels}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
