#!/usr/bin/env python3
"""Download Hugging Face model assets into the project model cache."""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import snapshot_download


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATASETS_ROOT = PROJECT_ROOT / "Datasets"
MODEL_ROOT = DATASETS_ROOT / "models" / "huggingface"

DEFAULT_MODELS = [
    "BAAI/bge-m3",
    "intfloat/e5-large-v2",
]

OPTIONAL_MODELS = [
    "BAAI/bge-reranker-v2-m3",
]


DEFAULT_IGNORE_PATTERNS = [
    "onnx/*",
    "openvino/*",
    "*.onnx",
    "*.onnx_data",
    "*.safetensors",
    "flax_model.msgpack",
    "tf_model.h5",
    "imgs/*",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Also download optional reranker assets.",
    )
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        help="Additional Hugging Face model repo id. Can be repeated.",
    )
    return parser.parse_args()


def local_name(repo_id: str) -> str:
    return repo_id.replace("/", "--")


def main() -> int:
    args = parse_args()
    DATASETS_ROOT.joinpath("cache", "huggingface").mkdir(parents=True, exist_ok=True)
    DATASETS_ROOT.joinpath("cache", "transformers").mkdir(parents=True, exist_ok=True)
    MODEL_ROOT.mkdir(parents=True, exist_ok=True)

    os.environ.setdefault("HF_HOME", str(DATASETS_ROOT / "cache" / "huggingface"))
    os.environ.setdefault("HF_HUB_CACHE", str(MODEL_ROOT))
    os.environ.setdefault("TRANSFORMERS_CACHE", str(DATASETS_ROOT / "cache" / "transformers"))

    models = [*DEFAULT_MODELS, *args.model]
    if args.include_optional:
        models.extend(OPTIONAL_MODELS)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_root": str(MODEL_ROOT),
        "models": [],
    }

    for repo_id in models:
        target_dir = MODEL_ROOT / local_name(repo_id)
        path = snapshot_download(
            repo_id=repo_id,
            local_dir=target_dir,
            local_dir_use_symlinks=False,
            ignore_patterns=DEFAULT_IGNORE_PATTERNS,
        )
        manifest["models"].append(
            {
                "repo_id": repo_id,
                "local_dir": str(Path(path).resolve()),
            }
        )
        print(f"{repo_id} -> {Path(path).resolve()}")

    manifest_path = DATASETS_ROOT / "manifests" / "model_assets_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"manifest={manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
