#!/usr/bin/env python3
"""시내도로 교통 CCTV JPG frames -> CLIP-512 embeddings, streamed from zips.
Stratified across zips (=locations/cameras) with temporally-spread sampling per
zip. Shardable across GPUs. Builds the scale corpus for the index-structure study.
"""
from __future__ import annotations
import argparse, glob, io, json, os, re, time, zipfile
from pathlib import Path
import numpy as np, torch

CLIP = "/hdd2/huggingface_cache/hub/models--openai--clip-vit-base-patch32"
TS = re.compile(r"(\d{8})_(\d{6})")


def parse_meta(entry: str):
    p = entry.split("/")
    m = TS.search(entry)
    return {"location": p[0] if p else "", "camera": p[1] if len(p) > 1 else "",
            "date": m.group(1) if m else "", "time": m.group(2) if m else ""}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", default=None, help="single zip (smoke)")
    ap.add_argument("--zips-file", default=None, help="newline list of zip paths (build)")
    ap.add_argument("--per-zip", type=int, default=0, help="max imgs per zip, temporally spread (0=all)")
    ap.add_argument("--limit", type=int, default=0, help="single-zip smoke cap")
    ap.add_argument("--batch", type=int, default=384)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor
    sp = sorted(glob.glob(CLIP + "/snapshots/*"))[0]
    model = CLIPModel.from_pretrained(sp).to(args.device).eval()
    proc = CLIPProcessor.from_pretrained(sp)

    @torch.no_grad()
    def embed(pils):
        px = proc(images=pils, return_tensors="pt").to(args.device)
        vo = model.vision_model(**px)
        e = model.visual_projection(vo.pooler_output)
        return (e / e.norm(dim=-1, keepdim=True)).cpu().numpy().astype("float32")

    if args.zips_file:
        zips = [l.strip() for l in open(args.zips_file) if l.strip()]
    else:
        zips = [args.zip]
    print(f"[build] {len(zips)} zips, per_zip={args.per_zip}, batch={args.batch}, dev={args.device}")

    embs, rows = [], []
    t0 = time.time(); done = 0
    for zi, zpath in enumerate(zips):
        try:
            zf = zipfile.ZipFile(zpath)
        except Exception as e:
            print(f"  [skip] {os.path.basename(zpath)}: {e}"); continue
        ents = sorted(n for n in zf.namelist() if n.lower().endswith((".jpg", ".jpeg", ".png")))
        if args.limit:
            ents = ents[: args.limit]
        elif args.per_zip and len(ents) > args.per_zip:
            idx = np.linspace(0, len(ents) - 1, args.per_zip).astype(int)  # temporally spread
            ents = [ents[i] for i in idx]
        for i in range(0, len(ents), args.batch):
            chunk = ents[i: i + args.batch]
            try:
                pils = [Image.open(io.BytesIO(zf.read(e))).convert("RGB") for e in chunk]
                embs.append(embed(pils))
                for e in chunk:
                    rows.append({"frame_id": f"{Path(zpath).stem}::{e}", **parse_meta(e)})
                done += len(chunk)
            except Exception as e:
                print(f"  [err] {os.path.basename(zpath)} batch{i}: {type(e).__name__} {e}")
        if (zi + 1) % 5 == 0 or zi == len(zips) - 1:
            el = time.time() - t0
            print(f"  zip {zi+1}/{len(zips)}  imgs={done}  {done/el:.0f} img/s  {el/60:.1f}min")
            np.save(out / "frame_embeddings.npy", np.vstack(embs))
            import pandas as pd; pd.DataFrame(rows).to_parquet(out / "frame_index.parquet")
    emb = np.vstack(embs) if embs else np.zeros((0, 512), "float32")
    np.save(out / "frame_embeddings.npy", emb)
    import pandas as pd; pd.DataFrame(rows).to_parquet(out / "frame_index.parquet")
    (out / "build_manifest.json").write_text(json.dumps({
        "n_images": int(emb.shape[0]), "dim": int(emb.shape[1]), "n_zips": len(zips),
        "per_zip": args.per_zip, "device": args.device, "seconds": round(time.time() - t0, 1),
        "img_per_sec": round(done / (time.time() - t0), 1), "clip": "openai/clip-vit-base-patch32",
    }, ensure_ascii=False, indent=2))
    print(f"\n[done] {emb.shape[0]} imgs x {emb.shape[1]} in {(time.time()-t0)/60:.1f}min -> {out}")


if __name__ == "__main__":
    main()
