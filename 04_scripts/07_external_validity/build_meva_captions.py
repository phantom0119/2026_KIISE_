#!/usr/bin/env python3
"""MEVA DOCUMENT channel = VLM dense captions of clip mid-frames.

Mirrors build_intersection_captions.py (522). The captioner sees ONLY the frame
pixels — no capture metadata, no activity annotations — preserving source-level
non-circularity (predicate = capture metadata; relevance = DIVA activity;
document = this caption).

Two phases (frame extraction is CPU+network and GPU-independent):
  --extract-only   download each 5-min .avi from the public MEVA S3 bucket,
                   grab the middle frame with OpenCV, write frames/<clip>.jpg,
                   then DELETE the .avi (only the small JPG is kept).
  --caption-only   caption the extracted frames with Qwen2.5-VL (needs GPU).
  (default runs extract-then-caption per clip.)

Both phases resume: extract skips clips whose JPG exists; caption skips clips
already in the shard jsonl. Sharding for 2 GPUs via --shard k/n.

Anti-leak guard: a build assertion rejects any caption that verbatim-contains an
activity class token (paranoia; the captioner never receives them).

Run (CPU, stage all frames in background):
  Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/04_scripts/build_meva_captions.py \
      --extract-only --n-clips 0
Run (GPU, when free):
  ... build_meva_captions.py --caption-only --device cuda:0 --shard 0/1
Then merge:
  ... build_meva_captions.py --merge-only
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DS = PROJECT_ROOT / "Datasets"
DATASET_ID = "meva_kf1"
S3 = "https://mevadata-public-01.s3.amazonaws.com"
SNAP_DEFAULT = "/hdd2/huggingface_cache/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/cc594898137f460bfe9f0759e9844b3ce807cfb5"

PROMPT = ("Describe this outdoor fixed surveillance camera frame in 2-4 factual "
          "sentences: the people present and what they appear to be doing, any "
          "vehicles, objects being carried, opened, or exchanged, doors or "
          "building entrances, and the general setting. State only what is "
          "visible; no speculation.")

# activity-class tokens must never appear verbatim in a caption (anti-leak)
LEAK_TOKENS = ("person_", "vehicle_", "hand_interacts")


def select_clips(ver: Path, n_clips: int, seed: int, with_activity_only: bool = False) -> pd.DataFrame:
    clips = pd.read_parquet(ver / "clips.parquet")
    if with_activity_only:
        clips = clips[clips["has_activity"]].copy()
    clips = clips.sort_values("clip_id").reset_index(drop=True)
    if n_clips and n_clips < len(clips):  # stratify by location
        g = clips.groupby("location", group_keys=False)
        per = max(1, round(n_clips / clips.location.nunique()))
        clips = g.apply(lambda d: d.sample(min(len(d), per), random_state=seed)).reset_index(drop=True)
        if len(clips) > n_clips:
            clips = clips.sample(n_clips, random_state=seed).reset_index(drop=True)
    return clips.sort_values("clip_id").reset_index(drop=True)


def extract_frame(avi_key: str, jpg_path: Path, tmp_dir: Path) -> bool:
    import cv2
    tmp = tmp_dir / (jpg_path.stem + ".avi")
    try:
        r = subprocess.run(["curl", "-sS", "--max-time", "600", "-o", str(tmp),
                            f"{S3}/{avi_key}"], capture_output=True)
        if r.returncode != 0 or not tmp.exists() or tmp.stat().st_size < 10000:
            return False
        cap = cv2.VideoCapture(str(tmp))
        n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, max(0, n // 2))
        ok, frame = cap.read()
        if not ok and n == 0:  # fallback: read first decodable frame
            cap.release(); cap = cv2.VideoCapture(str(tmp)); ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            return False
        jpg_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(jpg_path), frame)
        return True
    finally:
        if tmp.exists():
            tmp.unlink()


def load_done(jsonl: Path) -> set[str]:
    done = set()
    if jsonl.exists():
        for line in jsonl.read_text(encoding="utf-8").splitlines():
            try:
                done.add(json.loads(line)["clip_id"])
            except Exception:
                continue
    return done


def merge_shards(cap_dir: Path) -> None:
    rows = []
    for sh in sorted(cap_dir.glob("captions_shard*.jsonl")):
        for line in sh.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    df = pd.DataFrame(rows).drop_duplicates("clip_id")
    docs = pd.DataFrame({
        "doc_id": DATASET_ID + ":doc:vlm_caption:" + df["clip_id"],
        "clip_id": df["clip_id"], "dataset_id": DATASET_ID,
        "doc_type": "vlm_dense_caption", "text": df["caption"], "lang": "en",
        "source_frame": df["frame_path"],
    })
    docs.to_parquet(cap_dir / "documents.parquet", index=False)
    print(f"[merge] {len(docs)} caption docs -> {cap_dir/'documents.parquet'}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ver", default="20260713")
    ap.add_argument("--n-clips", type=int, default=0, help="0 = all corpus clips; else stratified subset")
    ap.add_argument("--seed", type=int, default=20260713)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--snapshot", default=SNAP_DEFAULT)
    ap.add_argument("--max-new-tokens", type=int, default=110)
    ap.add_argument("--max-pixels", type=int, default=448 * 448)
    ap.add_argument("--with-activity-only", action="store_true",
                    help="restrict corpus to clips with >=1 DIVA activity (drops empty background clips)")
    ap.add_argument("--extract-only", action="store_true")
    ap.add_argument("--caption-only", action="store_true")
    ap.add_argument("--merge-only", action="store_true")
    args = ap.parse_args()
    ver = DS / "processed" / DATASET_ID / args.ver
    frames_dir = ver / "frames"
    cap_dir = ver / "captions"
    tmp_dir = ver / "_avi_tmp"
    cap_dir.mkdir(parents=True, exist_ok=True); tmp_dir.mkdir(parents=True, exist_ok=True)

    if args.merge_only:
        merge_shards(cap_dir); return 0

    sel = select_clips(ver, args.n_clips, args.seed, args.with_activity_only)
    k, n = (int(x) for x in args.shard.split("/"))
    sel = sel.iloc[k::n].reset_index(drop=True)
    sel["frame_path"] = sel["clip_base"].map(lambda b: str((frames_dir / f"{b}.jpg")))
    print(f"[shard {args.shard}] clips={len(sel)}  extract_only={args.extract_only} caption_only={args.caption_only}",
          flush=True)

    # ---- extract phase (CPU + network) ----
    if not args.caption_only:
        n_ok = n_skip = n_fail = 0
        t0 = time.time()
        for i, r in enumerate(sel.itertuples(index=False)):
            jpg = Path(r.frame_path)
            if jpg.exists():
                n_skip += 1; continue
            ok = extract_frame(r.avi_s3_key, jpg, tmp_dir)
            n_ok += int(ok); n_fail += int(not ok)
            if (i + 1) % 20 == 0:
                rate = (i + 1) / (time.time() - t0)
                print(f"  extract {i+1}/{len(sel)}  ok={n_ok} skip={n_skip} fail={n_fail}  "
                      f"{rate:.2f} clip/s", flush=True)
        print(f"[extract] ok={n_ok} skip={n_skip} fail={n_fail} in {(time.time()-t0)/60:.1f} min", flush=True)
        if args.extract_only:
            return 0

    # ---- caption phase (GPU) ----
    import torch
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
    from qwen_vl_utils import process_vision_info
    out_jsonl = cap_dir / f"captions_shard{k}.jsonl"
    done = set()  # global resume across all shard files (robust to re-partitioning)
    for sh in cap_dir.glob("captions_shard*.jsonl"):
        done |= load_done(sh)
    todo = sel[~sel.clip_id.isin(done)]
    todo = todo[todo.frame_path.map(lambda p: Path(p).exists())]
    print(f"[caption] todo={len(todo)} (done={len(done)})", flush=True)
    if todo.empty:
        return 0
    t0 = time.time()
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.snapshot, torch_dtype=torch.float16, device_map=args.device).eval()
    proc = AutoProcessor.from_pretrained(args.snapshot)
    print(f"[load] {time.time()-t0:.0f}s", flush=True)
    (cap_dir / f"caption_manifest_shard{k}.json").write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(), "snapshot": args.snapshot,
        "prompt": PROMPT, "max_new_tokens": args.max_new_tokens, "decoding": "greedy",
        "source_separation_note": "captioner sees frame pixels only",
    }, ensure_ascii=False, indent=2))

    t0 = time.time()
    with out_jsonl.open("a", encoding="utf-8") as fout, torch.no_grad():
        for i, r in enumerate(todo.itertuples(index=False)):
            msg = [{"role": "user", "content": [
                {"type": "image", "image": f"file://{r.frame_path}", "max_pixels": args.max_pixels},
                {"type": "text", "text": PROMPT}]}]
            text = proc.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
            imgs, vids = process_vision_info(msg)
            inputs = proc(text=[text], images=imgs, videos=vids, return_tensors="pt").to(args.device)
            gen = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
            cap = proc.batch_decode(gen[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0].strip()
            assert not any(t in cap for t in LEAK_TOKENS), f"activity token leaked: {cap[:80]}"
            fout.write(json.dumps({"clip_id": r.clip_id, "clip_base": r.clip_base,
                                   "frame_path": r.frame_path, "caption": cap}, ensure_ascii=False) + "\n")
            fout.flush()
            if (i + 1) % 25 == 0:
                rate = (i + 1) / (time.time() - t0)
                print(f"  caption {i+1}/{len(todo)}  {rate:.2f} img/s", flush=True)
    print(f"[caption] {len(todo)} in {(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
