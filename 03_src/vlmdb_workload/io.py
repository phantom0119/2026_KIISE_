"""Common IO helpers for canonical workload artifacts."""

from __future__ import annotations

import json
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


def write_json(path: Path, obj: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_canonical(canonical_root: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    clips = pd.read_parquet(canonical_root / "clips.parquet")
    documents = pd.read_parquet(canonical_root / "documents.parquet")
    metadata = pd.read_parquet(canonical_root / "metadata.parquet")
    queries = pd.DataFrame(read_jsonl(canonical_root / "queries.jsonl"))
    qrels = pd.read_csv(canonical_root / "qrels.tsv", sep="\t")
    return clips, documents, metadata, queries, qrels
