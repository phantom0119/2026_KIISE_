#!/usr/bin/env python3
"""⭐2 3rd multimodal dataset: zip-aware keyframe + CLIP visual embeddings for
AI Hub 이상행동 CCTV. Produces the same visual_embeddings/ layout that
run_visual_retrieval_baselines.py consumes.
"""
from __future__ import annotations
import argparse, glob, json, zipfile, tempfile, os, time
from pathlib import Path
import numpy as np, pandas as pd, torch

ROOT = Path(__file__).resolve().parents[3]
DS = ROOT / "Datasets/processed/aihub_abnormal_cctv/20260707"
RAW = ROOT / "Datasets/raw/aihub_abnormal_cctv/20260707"
CLIP = "/hdd2/huggingface_cache/hub/models--openai--clip-vit-base-patch32"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=0, help="0=all clips, else first N")
    ap.add_argument("--frames", type=int, default=4)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--out", default=str(DS / "visual_embeddings/clip-vit-base-patch32_full"))
    ap.add_argument("--ckpt-every", type=int, default=100)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    import cv2
    from PIL import Image
    from transformers import CLIPModel, CLIPProcessor
    sp = sorted(glob.glob(CLIP + "/snapshots/*"))[0]
    model = CLIPModel.from_pretrained(sp).to(args.device).eval()
    proc = CLIPProcessor.from_pretrained(sp)

    clips = pd.read_parquet(DS / "canonical/clips.parquet")
    pairs = pd.read_csv(RAW / "clip_pairs.csv")[["clip_id", "media_zip_path", "media_entry"]]
    df = clips[["clip_id"]].merge(pairs, on="clip_id", how="inner")
    if args.n:
        df = df.head(args.n)
    print(f"[data] {len(df)} clips to process, {args.frames} frames each")

    @torch.no_grad()
    def embed_images(pils):
        px = proc(images=pils, return_tensors="pt").to(args.device)
        vo = model.vision_model(**px)
        e = model.visual_projection(vo.pooler_output)
        return (e / e.norm(dim=-1, keepdim=True)).cpu().numpy()

    frame_rows, embs = [], []
    ckpt = out / "frame_embeddings_partial.npy"
    t0 = time.time(); done = 0; errors = 0
    for i, r in df.iterrows():
        try:
            with zipfile.ZipFile(r["media_zip_path"]) as z:
                with z.open(r["media_entry"]) as src, tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                    tmp.write(src.read()); mp4 = tmp.name
            cap = cv2.VideoCapture(mp4)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
            idxs = np.linspace(0, max(total - 1, 0), args.frames, dtype=int)
            pils = []
            for kf, fidx in enumerate(idxs):
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(fidx))
                ok, fr = cap.read()
                if not ok:
                    fr = np.zeros((224, 224, 3), np.uint8)
                pils.append(Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).resize((224, 224)))
                frame_rows.append({"frame_id": f"{r['clip_id']}:kf{kf:02d}", "clip_id": r["clip_id"],
                                   "frame_index": int(fidx), "timestamp_sec": float(fidx) / fps})
            cap.release(); os.unlink(mp4)
            embs.append(embed_images(pils))
            done += 1
        except Exception as e:
            errors += 1
            print(f"  [err] {r['clip_id'][:40]}: {type(e).__name__} {e}")
        if done and done % args.ckpt_every == 0:
            np.save(ckpt, np.vstack(embs))
            pd.DataFrame(frame_rows).to_parquet(out / "frame_index_partial.parquet")
            print(f"  {done}/{len(df)} clips ({(time.time()-t0)/done:.1f}s/clip, {errors} err)")
    frame_emb = np.vstack(embs) if embs else np.zeros((0, 512), np.float32)
    np.save(out / "frame_embeddings.npy", frame_emb)
    pd.DataFrame(frame_rows).to_parquet(out / "frame_index.parquet")

    # query text embeddings (CLIP text encoder)
    q = [json.loads(l) for l in (DS / "canonical/queries.jsonl").read_text().splitlines()]
    qdf = pd.DataFrame(q)

    @torch.no_grad()
    def embed_text(texts):
        out_ = []
        for k in range(0, len(texts), 64):
            tk = proc(text=texts[k:k+64], return_tensors="pt", padding=True, truncation=True, max_length=77).to(args.device)
            to = model.text_model(**tk)
            e = model.text_projection(to.pooler_output)
            e = e / e.norm(dim=-1, keepdim=True)
            out_.append(e.cpu().numpy())
        return np.vstack(out_)
    qemb = embed_text(qdf["query_text"].tolist())
    np.save(out / "query_text_embeddings.npy", qemb)
    qdf[["query_id"]].to_json(out / "query_index.jsonl", orient="records", lines=True)
    (out / "visual_embedding_manifest.json").write_text(json.dumps({
        "model_id": "clip-vit-base-patch32", "frames_per_clip": args.frames,
        "clips_done": done, "clips_error": errors, "frame_count": len(frame_rows),
        "query_count": int(len(qdf)), "embedding_dim": int(frame_emb.shape[1] if frame_emb.size else 512),
    }, indent=2))
    for p in [ckpt, out / "frame_index_partial.parquet"]:
        if p.exists(): p.unlink()
    print(f"\n[done] {done} clips, {errors} err, {len(frame_rows)} frames, {len(qdf)} queries in {(time.time()-t0)/60:.1f} min -> {out}")


if __name__ == "__main__":
    main()
