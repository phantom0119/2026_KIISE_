#!/usr/bin/env python3
"""MIRIS pgvector corpus with REAL predicates (spatial/content/temporal) for the
claim-3 proof: partial/local index beats global+WHERE on recall AND latency under
selective SPATIAL (camera) and CONTENT (vehicle count) predicates — not only the
synthetic time bucket of the first build.

Builds table `miris_frames2 (id, scene, video, tseg, nobj, embedding)` from MIRIS
warsaw+shibuya fixed traffic-intersection CCTV (same CLIP ViT-B/32 encoder):
  scene = warsaw|shibuya                          (coarse spatial)
  video = <scene>_<n>  (12 fixed camera-sessions) (fine SPATIAL predicate)  <-- closes the "위치" gap
  nobj  = per-frame detected object count (MIRIS YOLOv3 JSON tracks)  <-- REAL CONTENT predicate
  tseg  = temporal segment 0-23 within the stream (honest label, not "hour")
Holds out 1000 frames -> miris_queries2.npy. Keeps the original miris_frames intact.

License: MIRIS video is non-commercial research-only; embeddings not redistributed,
metrics only. Annotations MIT.

Run (GPU): Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/scripts/build_miris_pgvector_rich.py
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import cv2
import numpy as np
import torch
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DS = PROJECT_ROOT / "Datasets"
MIRIS = DS / "external" / "miris" / "data"
OUT = DS / "processed" / "miris_traffic" / "20260714"
DSN = "host=localhost port=5433 dbname=vlmdb user=vlmdb password=vlmdb"
SCENES = ["warsaw", "shibuya"]
STRIDE = 6
PER_VIDEO_CAP = 5200
CLIP_CACHE = str(DS / "models" / "huggingface")


def clip_model(device="cuda"):
    from transformers import CLIPModel, CLIPProcessor
    mid = "openai/clip-vit-base-patch32"
    return (CLIPModel.from_pretrained(mid, cache_dir=CLIP_CACHE).to(device).eval(),
            CLIPProcessor.from_pretrained(mid, cache_dir=CLIP_CACHE))


def embed(model, proc, pil, device):
    inp = proc(images=pil, return_tensors="pt").to(device)
    e = model.get_image_features(**inp)
    if not isinstance(e, torch.Tensor):
        vo = model.vision_model(pixel_values=inp["pixel_values"])
        e = model.visual_projection(vo.pooler_output)
    v = e.detach().cpu().float().numpy()
    return (v / np.clip(np.linalg.norm(v, axis=1, keepdims=True), 1e-8, None)).astype("float32")


def load_counts(scene, stem):
    """per-frame detected object count from MIRIS JSON (prefer <stem>.json over baseline)."""
    for name in (f"{stem}.json", f"{stem}-baseline.json"):
        p = MIRIS / scene / "json" / name
        if p.exists():
            X = json.load(open(p))
            return [len(x) if isinstance(x, list) else 0 for x in X]
    return []


def vec_literal(v):
    return "[" + ",".join(f"{x:.6f}" for x in v) + "]"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model, proc = clip_model(device)
    vecs, scenes, videos, tsegs, nobjs = [], [], [], [], []
    t0 = time.time()
    for scene in SCENES:
        for v in sorted((MIRIS / scene / "videos").glob("*.mp4")):
            counts = load_counts(scene, v.stem)
            cap = cv2.VideoCapture(str(v))
            kept, oidx = [], 0
            while True:
                if not cap.grab():
                    break
                if oidx % STRIDE == 0:
                    ok, fr = cap.retrieve()
                    if ok:
                        kept.append((fr, oidx))
                    if len(kept) >= PER_VIDEO_CAP:
                        break
                oidx += 1
            cap.release()
            n = len(kept)
            if n == 0:
                continue
            for b in range(0, n, 64):
                pil = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f, _ in kept[b:b + 64]]
                vecs.append(embed(model, proc, pil, device))
            for j, (_, oi) in enumerate(kept):
                scenes.append(scene)
                videos.append(f"{scene}_{v.stem}")
                tsegs.append(min(23, int(j / n * 24)))
                nobjs.append(int(counts[oi + 1]) if 0 <= oi + 1 < len(counts) else 0)
            print(f"  {scene}/{v.name}: {n} frames, nobj med~{int(np.median(nobjs[-n:]))} "
                  f"(elapsed {time.time()-t0:.0f}s, total {sum(len(x) for x in vecs)})", flush=True)
    X = np.vstack(vecs).astype("float32")
    scenes = np.array(scenes); videos = np.array(videos)
    tsegs = np.array(tsegs, int); nobjs = np.array(nobjs, int)
    N = len(X)
    print(f"[embed] {N}x{X.shape[1]} in {(time.time()-t0)/60:.1f} min; "
          f"nobj dist: >=15 {(nobjs>=15).mean():.3f}, >=20 {(nobjs>=20).mean():.3f}", flush=True)

    rng = np.random.default_rng(20260714)
    qi = rng.choice(N, size=min(1000, N // 10), replace=False)
    qm = np.zeros(N, bool); qm[qi] = True
    np.save(OUT / "miris_queries2.npy", X[qm])
    Xc = X[~qm]; sc, vd, ts, nb = scenes[~qm], videos[~qm], tsegs[~qm], nobjs[~qm]

    import psycopg
    conn = psycopg.connect(DSN, autocommit=True); cur = conn.cursor()
    cur.execute("SET maintenance_work_mem='2GB';")
    cur.execute("DROP TABLE IF EXISTS miris_frames2;")
    cur.execute(f"CREATE TABLE miris_frames2 (id int PRIMARY KEY, scene text, video text, "
                f"tseg int, nobj int, embedding vector({Xc.shape[1]}));")
    t1 = time.time()
    with cur.copy("COPY miris_frames2 (id, scene, video, tseg, nobj, embedding) FROM STDIN") as cp:
        for i in range(len(Xc)):
            cp.write_row((i, str(sc[i]), str(vd[i]), int(ts[i]), int(nb[i]), vec_literal(Xc[i])))
    cur.execute("ANALYZE miris_frames2;")
    print(f"[pg] miris_frames2 loaded {len(Xc)} rows in {time.time()-t1:.0f}s", flush=True)
    for col in ("scene", "video"):
        cur.execute(f"SELECT {col}, count(*) FROM miris_frames2 GROUP BY {col} ORDER BY 2 DESC LIMIT 4")
        print(f"  {col}:", cur.fetchall())
    print(f"[saved] {OUT}/miris_queries2.npy ; pg miris_frames2 ({len(Xc)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
