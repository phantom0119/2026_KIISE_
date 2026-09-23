#!/usr/bin/env python3
"""Build a pgvector corpus from MIRIS (SIGMOD 2020) fixed traffic-intersection video,
for the P2/P3 DB-design cross-validation (partial vs global index; hot/cold policy).

Traffic scenes only: warsaw + shibuya (uav=drone and beach=non-traffic excluded to
keep the fixed-traffic-CCTV framing). Frames sampled every --stride, CLIP ViT-B/32
embedded (SAME encoder/dim as sinnaedoro corpus_real, for a fair cross-dataset
comparison), loaded into pgvector table `miris_frames (id, location, hour, embedding)`
with:
  location = scene (warsaw / shibuya)              -- categorical spatial predicate
  hour     = temporal segment 0-23 of the stream   -- honest stream-segment bucket
             (each video's kept frames span 0-23 evenly), a spatiotemporal predicate
A held-out 1000 frames -> miris_queries.npy for ANN-recall queries.

NOTE (license): MIRIS videos are non-commercial research-only (copyright not owned by
authors); we use them for INTERNAL cross-validation and report metrics only — the
derived embeddings are NOT redistributed. Annotations/queries are MIT.

Run (GPU): Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/scripts/build_miris_pgvector.py
"""
from __future__ import annotations

import time
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DS = PROJECT_ROOT / "Datasets"
MIRIS = DS / "external" / "miris" / "data"
OUT = DS / "processed" / "miris_traffic" / "20260713"
DSN = "host=localhost port=5433 dbname=vlmdb user=vlmdb password=vlmdb"
SCENES = ["warsaw", "shibuya"]
STRIDE = 6
PER_VIDEO_CAP = 5200
CLIP_CACHE = str(DS / "models" / "huggingface")


def clip_model(device="cuda"):
    from transformers import CLIPModel, CLIPProcessor
    mid = "openai/clip-vit-base-patch32"
    proc = CLIPProcessor.from_pretrained(mid, cache_dir=CLIP_CACHE)
    model = CLIPModel.from_pretrained(mid, cache_dir=CLIP_CACHE).to(device).eval()
    return model, proc


def embed_images(model, proc, pil_imgs, device):
    inp = proc(images=pil_imgs, return_tensors="pt").to(device)
    emb = model.get_image_features(**inp)
    if not isinstance(emb, torch.Tensor):
        vo = model.vision_model(pixel_values=inp["pixel_values"])
        emb = model.visual_projection(vo.pooler_output)
    v = emb.detach().cpu().float().numpy()
    v /= np.clip(np.linalg.norm(v, axis=1, keepdims=True), 1e-8, None)
    return v.astype("float32")


def vec_literal(v):
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, proc = clip_model(device)
    vecs, locs, hours = [], [], []
    t0 = time.time()
    for scene in SCENES:
        vids = sorted((MIRIS / scene / "videos").glob("*.mp4"))
        for v in vids:
            cap = cv2.VideoCapture(str(v))
            kept_frames, idx = [], 0
            while True:
                ok = cap.grab()
                if not ok:
                    break
                if idx % STRIDE == 0:
                    ret, fr = cap.retrieve()
                    if ret:
                        kept_frames.append(fr)
                    if len(kept_frames) >= PER_VIDEO_CAP:
                        break
                idx += 1
            cap.release()
            nkept = len(kept_frames)
            if nkept == 0:
                continue
            # CLIP embed in batches
            for b in range(0, nkept, 64):
                batch = kept_frames[b:b + 64]
                pil = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in batch]
                vecs.append(embed_images(model, proc, pil, device))
            for j in range(nkept):
                locs.append(scene)
                hours.append(min(23, int(j / max(1, nkept) * 24)))
            print(f"  {scene}/{v.name}: kept {nkept} frames "
                  f"(elapsed {time.time()-t0:.0f}s, total {sum(len(x) for x in vecs)})", flush=True)
    X = np.vstack(vecs).astype("float32")
    locs = np.array(locs); hours = np.array(hours, dtype=int)
    N = len(X)
    print(f"[embed] {N} frames x {X.shape[1]} in {(time.time()-t0)/60:.1f} min", flush=True)

    # hold out 1000 queries
    rng = np.random.default_rng(20260713)
    qidx = rng.choice(N, size=min(1000, N // 10), replace=False)
    qmask = np.zeros(N, bool); qmask[qidx] = True
    Q = X[qmask]
    np.save(OUT / "miris_queries.npy", Q)
    Xc, locc, hourc = X[~qmask], locs[~qmask], hours[~qmask]
    print(f"[split] corpus={len(Xc)} queries={len(Q)}", flush=True)

    # load into pgvector
    import psycopg
    conn = psycopg.connect(DSN, autocommit=True)
    cur = conn.cursor()
    cur.execute("SET maintenance_work_mem = '2GB';")
    cur.execute("DROP TABLE IF EXISTS miris_frames;")
    cur.execute(f"CREATE TABLE miris_frames (id int PRIMARY KEY, location text, hour int, "
                f"embedding vector({Xc.shape[1]}));")
    t1 = time.time()
    with cur.copy("COPY miris_frames (id, location, hour, embedding) FROM STDIN") as cp:
        for i in range(len(Xc)):
            cp.write_row((i, str(locc[i]), int(hourc[i]), vec_literal(Xc[i])))
    cur.execute("ANALYZE miris_frames;")
    print(f"[pg] loaded {len(Xc)} rows in {time.time()-t1:.0f}s", flush=True)
    # selectivity preview
    cur.execute("SELECT location, count(*) FROM miris_frames GROUP BY location")
    print("  location dist:", cur.fetchall())
    print(f"[saved] {OUT}/miris_queries.npy ; pg table miris_frames ({len(Xc)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
