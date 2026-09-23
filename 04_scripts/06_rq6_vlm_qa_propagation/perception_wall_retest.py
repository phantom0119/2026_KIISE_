#!/usr/bin/env python3
"""P1: perception-wall re-test with stronger VLMs [feasibility probe, frozen].

Question: is the perception wall (630: fixed VLM near-chance on fine-grained
CCTV scene questions, esp. bikes 0.525) a VLM-CAPABILITY artifact, or intrinsic
to the low-res frames + fine questions? We re-run the EXACT pilot items (same
180 (video, qtype, gold), same 3 binary questions) with ORACLE evidence (the
video's own 3 frames) across stronger/other VLMs.

Baseline (Qwen2.5-VL, retrieved frames, 630): bikes 0.525 / bus 0.633 / stopped 0.583.
FROZEN decision rule: the wall "lifts" for a model iff mean-acc >= 0.70 AND
bikes >= 0.65 (materially above the near-chance baseline; chance = 0.50).

Run (kiise-vlmdb env): perception_wall_retest.py --model internvl3 --device cuda:0
  models: qwen25vl | qwen2vl | internvl3 ; --max-pixels for resolution control.
"""
from __future__ import annotations
import argparse, json, re, time
from pathlib import Path
import pandas as pd

R2 = Path(__file__).resolve().parents[2]
V = R2.parent / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
OUT = R2 / "paper_assets" / "20260712_perception_retest"
HUB = "/hdd2/huggingface_cache/hub"
SNAP = {
 "qwen25vl": f"{HUB}/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/cc594898137f460bfe9f0759e9844b3ce807cfb5",
 "qwen2vl":  f"{HUB}/models--Qwen--Qwen2-VL-7B-Instruct",
 "internvl3": f"{HUB}/models--OpenGVLab--InternVL3-8B-hf",
}
QTYPES = {
 "bus": "Is at least one bus visible in these frames? Answer strictly yes or no.",
 "stopped": "Are any vehicles stopped or queued (not moving) in these frames? Answer strictly yes or no.",
 "bikes": "Are there two or more bicycles or motorbikes visible in these frames? Answer strictly yes or no.",
}


def snap_dir(key):
    p = Path(SNAP[key])
    if (p / "snapshots").exists():
        p = next((p / "snapshots").iterdir())
    return str(p)


def parse_yn(text):
    t = text.strip().lower()
    m = re.search(r"\b(yes|no)\b", t)
    return "yes" if (m and m.group(1) == "yes") else ("no" if m else ("yes" if "yes" in t else "no"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", choices=list(SNAP), required=True)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--max-pixels", type=int, default=448 * 448)
    ap.add_argument("--max-new-tokens", type=int, default=8)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    d = pd.read_parquet(R2 / "paper_assets/20260711_e1a/e1a_vlm_minipilot.parquet")
    items = d.drop_duplicates(["visual_video_id", "qtype"])[["visual_video_id", "qtype", "gold"]]
    fi = pd.read_parquet(V / "visual_embeddings_clip/frame_index.parquet")
    frames = {vid: [str(V / r) for r in g.sort_values("frame").relpath.tolist()][:3]
              for vid, g in fi.groupby("visual_video_id")}

    import torch
    snap = snap_dir(args.model)
    t0 = time.time()
    if args.model in ("qwen25vl", "qwen2vl"):
        from qwen_vl_utils import process_vision_info
        if args.model == "qwen25vl":
            from transformers import Qwen2_5_VLForConditionalGeneration as MC
        else:
            from transformers import Qwen2VLForConditionalGeneration as MC
        from transformers import AutoProcessor
        model = MC.from_pretrained(snap, torch_dtype=torch.float16, device_map=args.device).eval()
        proc = AutoProcessor.from_pretrained(snap)

        def ask(imgs, q):
            content = [{"type": "image", "image": f"file://{p}", "max_pixels": args.max_pixels} for p in imgs]
            content.append({"type": "text", "text": q})
            msg = [{"role": "user", "content": content}]
            text = proc.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
            ii, vi = process_vision_info(msg)
            inp = proc(text=[text], images=ii, videos=vi, return_tensors="pt").to(args.device)
            with torch.no_grad():
                out = model.generate(**inp, max_new_tokens=args.max_new_tokens, do_sample=False)
            return proc.batch_decode(out[:, inp.input_ids.shape[1]:], skip_special_tokens=True)[0]
    else:  # internvl3-hf
        from transformers import AutoModelForImageTextToText, AutoProcessor
        from PIL import Image
        model = AutoModelForImageTextToText.from_pretrained(
            snap, torch_dtype=torch.float16, device_map=args.device).eval()
        proc = AutoProcessor.from_pretrained(snap)

        def ask(imgs, q):
            pil = [Image.open(p).convert("RGB") for p in imgs]
            content = [{"type": "image"} for _ in pil] + [{"type": "text", "text": q}]
            msg = [{"role": "user", "content": content}]
            prompt = proc.apply_chat_template(msg, add_generation_prompt=True)
            inp = proc(images=pil, text=prompt, return_tensors="pt").to(args.device, torch.float16)
            with torch.no_grad():
                out = model.generate(**inp, max_new_tokens=args.max_new_tokens, do_sample=False)
            return proc.batch_decode(out[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0]
    print(f"[load] {args.model} in {time.time()-t0:.0f}s", flush=True)

    rows = []
    t0 = time.time()
    for i, r in enumerate(items.itertuples(index=False)):
        imgs = frames.get(r.visual_video_id, [])
        if not imgs:
            continue
        try:
            raw = ask(imgs, QTYPES[r.qtype])
        except Exception as e:
            raw = f"ERR:{e}"
        pred = parse_yn(raw)
        rows.append({"model": args.model, "visual_video_id": r.visual_video_id,
                     "qtype": r.qtype, "gold": r.gold, "pred": pred,
                     "correct": int(pred == r.gold), "raw": raw[:40]})
        if (i + 1) % 45 == 0:
            print(f"  {i+1}/{len(items)}  {(i+1)/(time.time()-t0):.2f} it/s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"retest_{args.model}.csv", index=False)
    acc = df.groupby("qtype").correct.mean()
    summ = {"model": args.model, "max_pixels": args.max_pixels, "n": len(df),
            "acc_bus": round(float(acc.get("bus", float('nan'))), 3),
            "acc_stopped": round(float(acc.get("stopped", float('nan'))), 3),
            "acc_bikes": round(float(acc.get("bikes", float('nan'))), 3),
            "acc_mean": round(float(df.correct.mean()), 3)}
    summ["wall_lifts (mean>=0.70 & bikes>=0.65)"] = bool(summ["acc_mean"] >= 0.70 and summ["acc_bikes"] >= 0.65)
    (OUT / f"retest_{args.model}_summary.json").write_text(json.dumps(summ, indent=2))
    print(json.dumps(summ, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
