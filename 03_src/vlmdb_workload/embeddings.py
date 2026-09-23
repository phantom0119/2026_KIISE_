"""Embedding providers and artifact builders."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .io import read_jsonl, write_json


@dataclass(frozen=True)
class EmbeddingBuildResult:
    output_dir: Path
    document_count: int
    query_count: int
    embedding_dim: int
    model_id: str
    device: str


class SentenceTransformerEmbeddingProvider:
    """SentenceTransformers-backed text embedding provider."""

    def __init__(
        self,
        model_id: str,
        model_path: Path,
        device: str,
        batch_size: int = 32,
        normalize_embeddings: bool = True,
    ) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_id = model_id
        self.model_path = model_path
        self.device = device
        self.batch_size = batch_size
        self.normalize_embeddings = normalize_embeddings
        self.model = SentenceTransformer(str(model_path), device=device)

    def encode(self, texts: list[str], *, is_query: bool) -> np.ndarray:
        prepared = [self._prepare_text(text, is_query=is_query) for text in texts]
        embeddings = self.model.encode(
            prepared,
            batch_size=self.batch_size,
            show_progress_bar=True,
            normalize_embeddings=self.normalize_embeddings,
            convert_to_numpy=True,
        )
        return embeddings.astype("float32")

    def _prepare_text(self, text: str, *, is_query: bool) -> str:
        clean = " ".join(str(text).split())
        if self.model_id.startswith("e5"):
            prefix = "query: " if is_query else "passage: "
            return prefix + clean
        return clean


def build_text_embeddings(
    canonical_root: Path,
    output_dir: Path,
    model_id: str,
    model_path: Path,
    device: str,
    batch_size: int,
    overwrite: bool = False,
) -> EmbeddingBuildResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"{output_dir} is not empty. Use overwrite=True.")

    documents = pd.read_parquet(canonical_root / "documents.parquet")
    queries = pd.DataFrame(read_jsonl(canonical_root / "queries.jsonl"))

    provider = SentenceTransformerEmbeddingProvider(
        model_id=model_id,
        model_path=model_path,
        device=device,
        batch_size=batch_size,
    )

    document_embeddings = provider.encode(documents["text"].fillna("").tolist(), is_query=False)
    query_embeddings = provider.encode(queries["query_text"].fillna("").tolist(), is_query=True)

    np.save(output_dir / "document_embeddings.npy", document_embeddings)
    np.save(output_dir / "query_embeddings.npy", query_embeddings)

    documents[["doc_id", "clip_id", "doc_type"]].to_parquet(output_dir / "document_index.parquet", index=False)
    queries[["query_id", "difficulty", "positive_count"]].to_parquet(output_dir / "query_index.parquet", index=False)

    manifest: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(canonical_root),
        "output_dir": str(output_dir),
        "model_id": model_id,
        "model_path": str(model_path),
        "device": device,
        "batch_size": batch_size,
        "normalize_embeddings": True,
        "document_count": int(len(documents)),
        "query_count": int(len(queries)),
        "embedding_dim": int(document_embeddings.shape[1]),
        "files": {
            "document_embeddings": "document_embeddings.npy",
            "query_embeddings": "query_embeddings.npy",
            "document_index": "document_index.parquet",
            "query_index": "query_index.parquet",
        },
    }
    write_json(output_dir / "embedding_manifest.json", manifest)

    return EmbeddingBuildResult(
        output_dir=output_dir,
        document_count=len(documents),
        query_count=len(queries),
        embedding_dim=document_embeddings.shape[1],
        model_id=model_id,
        device=device,
    )
