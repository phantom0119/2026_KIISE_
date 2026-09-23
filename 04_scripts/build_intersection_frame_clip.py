#!/usr/bin/env python3
"""Pillar B-1 corpus B: CLIP ViT-B/32 embeddings for ALL extracted 522 frames.

Embeds frames_src/{train,val} (143,830 JPGs) with the SAME encoder (512-d,
L2-normalized) used for the sinnaedoro index corpus, so the two real corpora
are directly comparable in the filtered-ANN / index-structure benchmarks.

Output (mirrors sinnaedoro corpus_real layout):
  visual_embeddings_clip/frame_embeddings_shard{k}.npy  (+ index parquet)
  merge:  frame_embeddings.npy  (N×512 fp32, L2-normed)
          frame_index.parquet   (frame order: relpath, visual_video_id, split,
                                 intersection_id, cam_code, hour — join-ready)

Run (per GPU):
  ... build_intersection_frame_clip.py --device cuda:0 --shard 0/2
  ... build_intersection_frame_clip.py --device cuda:1 --shard 1/2
  ... build_intersection_frame_clip.py --merge-only
"""
from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DS = PROJECT_ROOT / "Datasets"
VER = DS / "processed" / "aihub_522_intersection" / "20260710"
OUT = VER / "visual_embeddings_clip"
MODEL_PATH = DS / "models" / "huggingface" / "models--openai--clip-vit-base-patch32"

VID_RE = re.compile(r"^(\d+)_(\d{14})\d*$")


def list_frames() -> pd.DataFrame:
    rows = []
    for split in ("train", "val"):
        root = VER / "frames_src" / split
        for p in sorted(root.rglob("*.jpg")):
            stem = p.stem
            vid, frame = stem.rsplit("_", 1)
            m = VID_RE.match(vid)
            cam = m.group(1) if m else ""
            ts = m.group(2) if m else ""
            rows.append({
                "relpath": str(p.relative_to(VER)), "split": split,
                "visual_video_id": vid, "frame": frame,
                "intersection_id": cam[:-2] if cam else "",
                "cam_code": cam[-2:] if cam else "",
                "hour": int(ts[8:10]) if len(ts) >= 10 else -1,
            })
    return pd.DataFrame(rows)


def resolve_model_dir() -> str:
    snaps = sorted((MODEL_PATH / "snapshots").glob("*"))
    return str(snaps[0]) if snaps else "openai/clip-vit-base-patch32"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--merge-only", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    frames = list_frames()
    frames.to_parquet(OUT / "frame_index_full.parquet", index=False)

    if args.merge_only:
        shards = sorted(OUT.glob("frame_embeddings_shard*.npy"))
        idxs = sorted(OUT.glob("frame_rows_shard*.npy"))
        embs, rows = [], []
        for e, i in zip(shards, idxs):
            embs.append(np.load(e)); rows.append(np.load(i))
        emb = np.concatenate(embs); order = np.concatenate(rows)
        # restore global frame order
        sort = np.argsort(order)
        emb = emb[sort]
        assert len(emb) == len(frames), f"{len(emb)} != {len(frames)}"
        np.save(OUT / "frame_embeddings.npy", emb.astype("float32"))
        frames.to_parquet(OUT / "frame_index.parquet", index=False)
        (OUT / "manifest.json").write_text(json.dumps({
            "encoder": "openai/clip-vit-base-patch32", "dim": int(emb.shape[1]),
            "n_frames": int(len(emb)), "l2_normalized": True,
            "consistent_with": "sinnaedoro corpus_real (same encoder/dim)"}, indent=2))
        print(f"[merge] {emb.shape} -> {OUT/'frame_embeddings.npy'}")
        return 0

    import torch
    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor

    def as_tensor(feat):
        """transformers 5.13: get_image_features returns BaseModelOutputWithPooling
        whose pooler_output IS already the projected 512-d feature (verified on
        disk vs sinnaedoro corpus dim). Do NOT re-project."""
        if isinstance(feat, torch.Tensor):
            v = feat
        else:
            v = getattr(feat, "image_embeds", None)
            if v is None:
                v = getattr(feat, "pooler_output", None)
            if not isinstance(v, torch.Tensor):
                raise TypeError(f"unexpected feature type: {type(feat)}")
        assert v.shape[-1] == 512, f"expected 512-d projected space, got {v.shape[-1]}"
        return v
    k, n = (int(x) for x in args.shard.split("/"))
    todo = frames.iloc[k::n]
    rows_idx = todo.index.to_numpy()
    mdir = resolve_model_dir()
    model = CLIPModel.from_pretrained(mdir).to(args.device).eval()
    proc = CLIPProcessor.from_pretrained(mdir)
    print(f"[shard {args.shard}] frames={len(todo)} device={args.device}", flush=True)

    out_e = OUT / f"frame_embeddings_shard{k}.npy"
    out_r = OUT / f"frame_rows_shard{k}.npy"
    from concurrent.futures import ThreadPoolExecutor
    pool = ThreadPoolExecutor(max_workers=8)

    def load(rp):
        # plain decode + convert (identical pixel path to sinnaedoro corpus builder);
        # only the CONCURRENCY differs, embeddings are unchanged
        return Image.open(VER / rp).convert("RGB")

    embs = []
    t0 = time.time()
    with torch.no_grad():
        for s in range(0, len(todo), args.batch_size):
            batch = todo.iloc[s:s + args.batch_size]
            imgs = list(pool.map(load, batch.relpath))
            inputs = proc(images=imgs, return_tensors="pt").to(args.device)
            feat = as_tensor(model.get_image_features(**inputs))
            feat = torch.nn.functional.normalize(feat, dim=-1)
            embs.append(feat.cpu().numpy().astype("float32"))
            if (s // args.batch_size) % 20 == 0:
                done = s + len(batch)
                rate = done / (time.time() - t0)
                print(f"  {done}/{len(todo)}  {rate:.0f} img/s  ETA {(len(todo)-done)/rate/60:.1f} min", flush=True)
    emb = np.concatenate(embs)
    np.save(out_e, emb); np.save(out_r, rows_idx)
    print(f"[done] shard {args.shard}: {emb.shape} in {(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
