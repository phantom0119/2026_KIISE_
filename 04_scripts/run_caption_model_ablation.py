#!/usr/bin/env python3
"""Generate versioned captions for the locked caption-model ablation corpus.

Each run is append-only and resumable. A shard fails immediately on an inference
error after recording the offending item, preventing silent corpus shrinkage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


DEFAULT_ROOT = Path("/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715")
MODEL_SPECS = {
    "qwen25vl_7b": {
        "model_id": "Qwen/Qwen2.5-VL-7B-Instruct",
        "revision": "cc594898137f460bfe9f0759e9844b3ce807cfb5",
        "path": Path("/hdd2/huggingface_cache/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/cc594898137f460bfe9f0759e9844b3ce807cfb5"),
        "model_type": "qwen2_5_vl",
        "image_patch_size": 14,
        "enable_thinking": None,
    },
    "qwen3vl_8b": {
        "model_id": "Qwen/Qwen3-VL-8B-Instruct",
        "revision": "0c351dd01ed87e9c1b53cbc748cba10e6187ff3b",
        "path": Path("/hdd/models/Qwen3-VL-8B-Instruct"),
        "model_type": "qwen3_vl",
        "image_patch_size": 16,
        "enable_thinking": None,
    },
    "qwen35_9b": {
        "model_id": "Qwen/Qwen3.5-9B",
        "revision": "c202236235762e1c871ad0ccb60c8ee5ba337b9a",
        "path": Path("/hdd/models/Qwen3.5-9B"),
        "model_type": "qwen3_5",
        "image_patch_size": 16,
        "enable_thinking": False,
    },
}

LEAK_TOKENS = {
    "522": ("sig_has_", "veh_density_bin", "ped_density_bin", "any_parked", "max_objects"),
    "meva": ("person_", "vehicle_", "hand_interacts", "act__", "cnt__", "facet_"),
    "uca": (
        "video_class",
        "video_duration_bin",
        "event_position_bin",
        "Normal_Videos",
        "RoadAccidents",
        "_x264",
    ),
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at {path}:{line_number}") from exc
    return rows


def done_ids(out_dir: Path) -> set[str]:
    done: set[str] = set()
    for path in out_dir.glob("captions_shard*.jsonl"):
        done.update(row["item_id"] for row in load_jsonl(path))
    return done


def local_revision(model_path: Path) -> str | None:
    metadata = model_path / ".cache" / "huggingface" / "download" / "config.json.metadata"
    if metadata.exists():
        return metadata.read_text(encoding="utf-8").splitlines()[0].strip()
    if model_path.parent.name == "snapshots":
        return model_path.name
    return None


def validate_model_files(spec: dict) -> dict:
    model_path = spec["path"]
    required = [model_path / "config.json", model_path / "model.safetensors.index.json"]
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"incomplete model download: {missing}")
    revision = local_revision(model_path)
    if revision and revision != spec["revision"]:
        raise ValueError(
            f"model revision mismatch for {spec['model_id']}: {revision} != {spec['revision']}"
        )
    return {
        "local_revision": revision,
        "config_sha256": sha256_file(model_path / "config.json"),
        "weight_index_sha256": sha256_file(model_path / "model.safetensors.index.json"),
    }


def clean_caption(text: str) -> str:
    text = text.strip()
    # Thinking is disabled for Qwen3.5. Keep a defensive parser so any unexpected
    # reasoning markup cannot silently become a searchable document.
    if "</think>" in text:
        text = text.split("</think>", 1)[1].strip()
    text = re.sub(r"^<think>\s*", "", text).strip()
    return text


def validate_caption(dataset: str, item_id: str, caption: str) -> None:
    if not caption:
        raise ValueError(f"{item_id}: blank caption")
    if any(token.lower() in caption.lower() for token in LEAK_TOKENS[dataset]):
        raise ValueError(f"{item_id}: machine/label token leaked into caption")


def write_documents(dataset: str, frame: pd.DataFrame, out_dir: Path) -> None:
    if dataset == "522":
        docs = pd.DataFrame(
            {
                "doc_id": frame["source_doc_id"],
                "clip_id": frame["clip_id"],
                "visual_video_id": frame["visual_video_id"],
                "split": frame["split"],
                "dataset_id": "aihub_522_intersection",
                "doc_type": "vlm_dense_caption",
                "text": frame["caption"],
                "lang": "en",
                "source_frame": frame["source_frame"],
            }
        )
    elif dataset == "meva":
        docs = pd.DataFrame(
            {
                "doc_id": frame["source_doc_id"],
                "clip_id": frame["clip_id"],
                "dataset_id": "meva_kf1",
                "doc_type": "vlm_dense_caption",
                "text": frame["caption"],
                "lang": "en",
                "source_frame": frame["source_frame"],
            }
        )
    else:
        docs = pd.DataFrame(
            {
                "doc_id": frame["source_doc_id"],
                "video_id": frame["video_id"],
                "split": frame["split"],
                "caption": frame["caption"],
            }
        )
    docs.to_parquet(out_dir / "documents.parquet", index=False)


def merge_shards(args: argparse.Namespace, items: pd.DataFrame) -> int:
    out_dir = args.output_root / args.model_key / args.dataset / "captions"
    rows = []
    for path in sorted(out_dir.glob("captions_shard*.jsonl")):
        rows.extend(load_jsonl(path))
    if not rows:
        raise FileNotFoundError(f"no caption shards under {out_dir}")
    generated = pd.DataFrame(rows)
    conflicts = generated.groupby("item_id")["caption"].nunique()
    if (conflicts > 1).any():
        raise ValueError(f"conflicting duplicate captions: {conflicts[conflicts > 1].index[:5].tolist()}")
    generated = generated.drop_duplicates("item_id", keep="last")
    expected = items if args.limit is None else items.head(args.limit)
    missing = sorted(set(expected.item_id) - set(generated.item_id))
    extra = sorted(set(generated.item_id) - set(expected.item_id))
    if missing or extra:
        raise ValueError(f"coverage mismatch: missing={len(missing)} extra={len(extra)}")
    merged = expected.drop(columns=["baseline_caption"]).merge(
        generated[["item_id", "caption", "elapsed_ms", "input_tokens", "output_tokens", "origin"]],
        on="item_id",
        how="left",
        validate="one_to_one",
    )
    merged.to_parquet(out_dir / "caption_records.parquet", index=False)
    write_documents(args.dataset, merged, out_dir)
    print(f"[merge] {len(merged)} complete captions -> {out_dir / 'documents.parquet'}")
    return 0


def import_baseline(args: argparse.Namespace, items: pd.DataFrame) -> int:
    if args.model_key != "qwen25vl_7b":
        raise ValueError("--import-baseline is valid only for qwen25vl_7b")
    out_dir = args.output_root / args.model_key / args.dataset / "captions"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "captions_shard0of1.jsonl"
    with out_path.open("w", encoding="utf-8") as handle:
        for row in items.itertuples(index=False):
            validate_caption(args.dataset, row.item_id, row.baseline_caption)
            handle.write(
                json.dumps(
                    {
                        "item_id": row.item_id,
                        "caption": row.baseline_caption,
                        "elapsed_ms": None,
                        "input_tokens": None,
                        "output_tokens": None,
                        "origin": "frozen_existing_qwen25_artifact",
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"[baseline] imported {len(items)} frozen captions -> {out_path}")
    return merge_shards(args, items)


def generate(args: argparse.Namespace, items: pd.DataFrame, spec: dict) -> int:
    import numpy as np
    import torch
    import transformers
    from qwen_vl_utils import process_vision_info
    from transformers import AutoConfig, AutoModelForImageTextToText, AutoProcessor

    model_checks = validate_model_files(spec)
    config = AutoConfig.from_pretrained(spec["path"], local_files_only=True)
    if config.model_type != spec["model_type"]:
        raise ValueError(f"model type mismatch: {config.model_type} != {spec['model_type']}")

    shard_k, shard_n = (int(value) for value in args.shard.split("/"))
    if not 0 <= shard_k < shard_n:
        raise ValueError(f"invalid shard {args.shard}")
    selected = items.iloc[shard_k::shard_n].copy()
    if args.limit is not None:
        selected = items.head(args.limit).iloc[shard_k::shard_n].copy()
    out_dir = args.output_root / args.model_key / args.dataset / "captions"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"captions_shard{shard_k}of{shard_n}.jsonl"
    completed = done_ids(out_dir)
    todo = selected[~selected.item_id.isin(completed)]
    print(
        f"[{args.model_key}/{args.dataset}/{args.shard}] selected={len(selected)} "
        f"done_global={len(completed)} todo={len(todo)}",
        flush=True,
    )
    if todo.empty:
        return 0

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)
    load_started = time.perf_counter()
    model = AutoModelForImageTextToText.from_pretrained(
        spec["path"],
        local_files_only=True,
        dtype=torch.float16,
        device_map=args.device,
        low_cpu_mem_usage=True,
        attn_implementation="sdpa",
    ).eval()
    processor = AutoProcessor.from_pretrained(spec["path"], local_files_only=True)
    load_seconds = time.perf_counter() - load_started
    print(f"[load] {load_seconds:.1f}s model_type={config.model_type}", flush=True)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "model_key": args.model_key,
        "model_id": spec["model_id"],
        "revision": spec["revision"],
        "model_path": str(spec["path"]),
        **model_checks,
        "dataset": args.dataset,
        "input_manifest": str(args.input_root / f"{args.dataset}_items.parquet"),
        "input_manifest_sha256": sha256_file(args.input_root / f"{args.dataset}_items.parquet"),
        "prompt": str(items.prompt.iloc[0]),
        "prompt_sha256": hashlib.sha256(str(items.prompt.iloc[0]).encode()).hexdigest(),
        "max_pixels": args.max_pixels,
        "max_new_tokens": args.max_new_tokens,
        "decoding": "greedy",
        "dtype": "float16",
        "attention_implementation": "sdpa",
        "seed": args.seed,
        "shard": args.shard,
        "image_patch_size": spec["image_patch_size"],
        "enable_thinking": spec["enable_thinking"],
        "source_separation": "frame pixels and frozen prompt only",
        "python": platform.python_version(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(torch.device(args.device)),
        "load_seconds": load_seconds,
    }
    (out_dir / f"caption_manifest_shard{shard_k}of{shard_n}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    error_path = out_dir / f"errors_shard{shard_k}of{shard_n}.jsonl"

    started = time.perf_counter()
    with out_path.open("a", encoding="utf-8") as handle, torch.inference_mode():
        for index, row in enumerate(todo.itertuples(index=False), start=1):
            try:
                message = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "image": f"file://{row.frame_path}",
                                "max_pixels": args.max_pixels,
                            },
                            {"type": "text", "text": row.prompt},
                        ],
                    }
                ]
                template_kwargs = {"tokenize": False, "add_generation_prompt": True}
                if spec["enable_thinking"] is not None:
                    template_kwargs["enable_thinking"] = spec["enable_thinking"]
                prompt_text = processor.apply_chat_template(message, **template_kwargs)
                vision = process_vision_info(message, image_patch_size=spec["image_patch_size"])
                images, videos = vision[:2]
                model_inputs = processor(
                    text=[prompt_text], images=images, videos=videos, return_tensors="pt"
                ).to(args.device)
                item_started = time.perf_counter()
                generated = model.generate(
                    **model_inputs,
                    max_new_tokens=args.max_new_tokens,
                    do_sample=False,
                    use_cache=True,
                )
                elapsed_ms = (time.perf_counter() - item_started) * 1000
                output_ids = generated[:, model_inputs.input_ids.shape[1] :]
                caption = clean_caption(
                    processor.batch_decode(output_ids, skip_special_tokens=True)[0]
                )
                validate_caption(args.dataset, row.item_id, caption)
                record = {
                    "item_id": row.item_id,
                    "caption": caption,
                    "elapsed_ms": round(elapsed_ms, 3),
                    "input_tokens": int(model_inputs.input_ids.shape[1]),
                    "output_tokens": int(output_ids.shape[1]),
                    "origin": "generated",
                }
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
                handle.flush()
            except Exception as exc:
                with error_path.open("a", encoding="utf-8") as errors:
                    errors.write(
                        json.dumps(
                            {
                                "created_at": datetime.now(timezone.utc).isoformat(),
                                "item_id": row.item_id,
                                "error_type": type(exc).__name__,
                                "error": str(exc),
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                raise
            if index % args.log_every == 0:
                rate = index / (time.perf_counter() - started)
                eta_minutes = (len(todo) - index) / max(rate, 1e-9) / 60
                print(
                    f"  {index}/{len(todo)} {rate:.3f} img/s ETA={eta_minutes:.1f} min",
                    flush=True,
                )
    print(f"[done] {len(todo)} captions in {(time.perf_counter() - started) / 60:.1f} min")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-key", required=True, choices=sorted(MODEL_SPECS))
    parser.add_argument("--dataset", required=True, choices=["522", "meva", "uca"])
    parser.add_argument("--input-root", type=Path, default=DEFAULT_ROOT / "inputs")
    parser.add_argument("--output-root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--device", default="cuda:0")
    parser.add_argument("--shard", default="0/1")
    parser.add_argument("--seed", type=int, default=20260715)
    parser.add_argument("--max-new-tokens", type=int, default=110)
    parser.add_argument("--max-pixels", type=int, default=448 * 448)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--log-every", type=int, default=25)
    parser.add_argument("--merge-only", action="store_true")
    parser.add_argument("--import-baseline", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = args.input_root / f"{args.dataset}_items.parquet"
    items = pd.read_parquet(input_path).sort_values("item_id", kind="stable").reset_index(drop=True)
    if args.import_baseline:
        return import_baseline(args, items)
    if args.merge_only:
        return merge_shards(args, items)
    return generate(args, items, MODEL_SPECS[args.model_key])


if __name__ == "__main__":
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
    raise SystemExit(main())
