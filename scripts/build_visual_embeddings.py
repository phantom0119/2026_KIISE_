#!/usr/bin/env python3
"""Build visual frame embeddings and cross-modal text-query embeddings."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.io import read_jsonl  # noqa: E402


MODEL_IDS = {
    "clip-vit-base-patch32": "openai/clip-vit-base-patch32",
    "siglip-base-patch16-224": "google/siglip-base-patch16-224",
}


def default_device() -> str:
    return "cuda" if torch.cuda.is_available() else "cpu"


def l2_normalize(array: np.ndarray) -> np.ndarray:
    norm = np.linalg.norm(array, axis=1, keepdims=True)
    norm[norm == 0] = 1.0
    return array / norm


def as_feature_tensor(features: Any) -> torch.Tensor:
    if isinstance(features, torch.Tensor):
        return features
    for attr in ["image_embeds", "text_embeds", "pooler_output", "last_hidden_state"]:
        value = getattr(features, attr, None)
        if isinstance(value, torch.Tensor):
            if attr == "last_hidden_state":
                return value[:, 0]
            return value
    if isinstance(features, (tuple, list)) and features and isinstance(features[0], torch.Tensor):
        return features[0]
    raise TypeError(f"Unsupported feature output type: {type(features).__name__}")


class VisionLanguageEmbeddingProvider:
    def __init__(self, model_key: str, model_path_or_id: str, device: str, cache_dir: Path | None = None) -> None:
        self.model_key = model_key
        self.model_path_or_id = model_path_or_id
        self.device = device
        self.cache_dir = cache_dir
        load_kwargs = {"cache_dir": str(cache_dir)} if cache_dir is not None else {}
        if model_key.startswith("clip"):
            from transformers import CLIPModel, CLIPProcessor

            self.processor = CLIPProcessor.from_pretrained(model_path_or_id, **load_kwargs)
            self.model = CLIPModel.from_pretrained(model_path_or_id, **load_kwargs).to(device)
        elif model_key.startswith("siglip"):
            from transformers import SiglipModel, SiglipProcessor

            self.processor = SiglipProcessor.from_pretrained(model_path_or_id, **load_kwargs)
            self.model = SiglipModel.from_pretrained(model_path_or_id, **load_kwargs).to(device)
        else:
            raise ValueError(f"Unsupported model key: {model_key}")
        self.model.eval()

    @torch.inference_mode()
    def encode_images(self, image_paths: list[str], batch_size: int) -> np.ndarray:
        vectors: list[np.ndarray] = []
        for start in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[start : start + batch_size]
            images = [Image.open(path).convert("RGB") for path in batch_paths]
            inputs = self.processor(images=images, return_tensors="pt").to(self.device)
            features = as_feature_tensor(self.model.get_image_features(**inputs))
            vectors.append(features.detach().cpu().float().numpy())
        return l2_normalize(np.vstack(vectors).astype("float32"))

    @torch.inference_mode()
    def encode_texts(self, texts: list[str], batch_size: int) -> np.ndarray:
        vectors: list[np.ndarray] = []
        for start in range(0, len(texts), batch_size):
            batch_texts = texts[start : start + batch_size]
            inputs = self.processor(text=batch_texts, padding=True, truncation=True, return_tensors="pt").to(self.device)
            features = as_feature_tensor(self.model.get_text_features(**inputs))
            vectors.append(features.detach().cpu().float().numpy())
        return l2_normalize(np.vstack(vectors).astype("float32"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, required=True)
    parser.add_argument("--frame-root", type=Path, required=True, help="Directory containing frames.parquet.")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-key", choices=sorted(MODEL_IDS), default="clip-vit-base-patch32")
    parser.add_argument("--model-path", default=None, help="Local path or HF model id. Defaults by model-key.")
    parser.add_argument("--cache-dir", type=Path, default=PROJECT_ROOT / "Datasets" / "models" / "huggingface")
    parser.add_argument("--device", default=default_device())
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty. Use --overwrite.")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    frames = pd.read_parquet(args.frame_root / "frames.parquet")
    queries = pd.DataFrame(read_jsonl(args.canonical_root / "queries.jsonl"))
    if frames.empty:
        raise ValueError(f"No frames found in {args.frame_root / 'frames.parquet'}")
    if queries.empty:
        raise ValueError(f"No queries found in {args.canonical_root / 'queries.jsonl'}")

    model_path_or_id = args.model_path or MODEL_IDS[args.model_key]
    provider = VisionLanguageEmbeddingProvider(args.model_key, str(model_path_or_id), args.device, args.cache_dir)

    frame_embeddings = provider.encode_images(frames["frame_path"].tolist(), args.batch_size)
    query_embeddings = provider.encode_texts(queries["query_text"].fillna("").tolist(), args.batch_size)

    np.save(args.output_dir / "frame_embeddings.npy", frame_embeddings)
    np.save(args.output_dir / "query_text_embeddings.npy", query_embeddings)
    frames[
        [
            "frame_id",
            "clip_id",
            "dataset_id",
            "frame_seq",
            "frame_index",
            "timestamp_sec",
            "frame_path",
            "media_path",
            "extraction_strategy",
        ]
    ].to_parquet(args.output_dir / "frame_index.parquet", index=False)
    queries[["query_id", "dataset_id", "query_text", "difficulty", "metadata_filter", "positive_count"]].to_json(
        args.output_dir / "query_index.jsonl",
        orient="records",
        lines=True,
        force_ascii=False,
    )

    manifest: dict[str, Any] = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "canonical_root": str(args.canonical_root),
        "frame_root": str(args.frame_root),
        "output_dir": str(args.output_dir),
        "model_key": args.model_key,
        "model_path_or_id": str(model_path_or_id),
        "cache_dir": str(args.cache_dir),
        "device": args.device,
        "batch_size": args.batch_size,
        "frame_count": int(len(frames)),
        "query_count": int(len(queries)),
        "embedding_dim": int(frame_embeddings.shape[1]),
        "normalize_embeddings": True,
        "files": {
            "frame_embeddings": "frame_embeddings.npy",
            "query_text_embeddings": "query_text_embeddings.npy",
            "frame_index": "frame_index.parquet",
            "query_index": "query_index.jsonl",
        },
    }
    (args.output_dir / "visual_embedding_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"output_dir={args.output_dir}")
    print(f"model_key={args.model_key}")
    print(f"device={args.device}")
    print(f"frame_count={len(frames)}")
    print(f"query_count={len(queries)}")
    print(f"embedding_dim={frame_embeddings.shape[1]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
