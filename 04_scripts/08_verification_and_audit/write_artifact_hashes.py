#!/usr/bin/env python3
"""Write a deterministic sha256.txt receipt for experiment output directories."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directories", type=Path, nargs="+")
    args = parser.parse_args()
    for directory in args.directories:
        if not directory.is_dir():
            raise NotADirectoryError(directory)
        files = sorted(
            path for path in directory.iterdir()
            if path.is_file() and path.name != "sha256.txt"
        )
        receipt = "\n".join(f"{sha256_file(path)}  {path.name}" for path in files) + "\n"
        (directory / "sha256.txt").write_text(receipt, encoding="utf-8")
        print(f"{directory}: {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
