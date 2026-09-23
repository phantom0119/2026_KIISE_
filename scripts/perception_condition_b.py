#!/usr/bin/env python3
"""P1-b: does the answer respond to EVIDENCE QUALITY? [condition-(b) probe, frozen]

The two walls failed because the answer did not respond to the mediator (index
degradation). This probes the full evidence gradient with the capable VLM
(InternVL3) on the same 180 items, WELL-POSED questions (bus, bikes; 'stopped'
is single-frame-ill-posed per P1 and reported separately):
  closed     — no frames (VLM priors only)
  distractor — a random OTHER video's frames (wrong evidence)
  oracle     — the item's own frames (right evidence)

FROZEN condition-(b): oracle_bal − closed_bal >= 0.15 (evidence matters) AND
oracle_bal > distractor_bal (answer responds to the RIGHT evidence -> retrieval/
index structure can move the answer). Output: paper_assets/20260712_perception_retest/condb_internvl3.{csv,json}

Run (kiise-vlmdb env): perception_condition_b.py --device cuda:0
"""
from __future__ import annotations
import argparse, json, re, time
from pathlib import Path
import numpy as np
import pandas as pd

R2 = Path(__file__).resolve().parents[1]
V = R2.parent / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
OUT = R2 / "paper_assets" / "20260712_perception_retest"
SNAP = "/hdd2/huggingface_cache/hub/models--OpenGVLab--InternVL3-8B-hf"
QTYPES = {
 "bus": "Is at least one bus visible in these frames? Answer strictly yes or no.",
 "bikes": "Are there two or more bicycles or motorbikes visible in these frames? Answer strictly yes or no.",
 "stopped": "Are any vehicles stopped or queued (not moving) in these frames? Answer strictly yes or no.",
}
QCLOSED = {  # closed-book has no frames -> phrase without "these frames"
 "bus": "In a typical urban intersection CCTV frame, is at least one bus visible? Answer strictly yes or no.",
 "bikes": "In a typical urban intersection CCTV frame, are there two or more bicycles or motorbikes? Answer strictly yes or no.",
 "stopped": "In a typical urban intersection CCTV frame, are any vehicles stopped or queued? Answer strictly yes or no.",
}


def snap_dir():
    p = Path(SNAP)
    return str(next((p / "snapshots").iterdir()) if (p / "snapshots").exists() else p)


def parse_yn(t):
    m = re.search(r"\b(yes|no)\b", t.strip().lower())
    return "yes" if (m and m.group(1) == "yes") else "no"


def bal(df, qts):
    g = df[df.qtype.isin(qts)]
    return round(float(((g.groupby("gold").correct.mean())).mean()), 3)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--max-pixels", type=int, default=200704)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(20260712)

    d = pd.read_parquet(R2 / "paper_assets/20260711_e1a/e1a_vlm_minipilot.parquet")
    items = d.drop_duplicates(["visual_video_id", "qtype"])[["visual_video_id", "qtype", "gold"]].reset_index(drop=True)
    fi = pd.read_parquet(V / "visual_embeddings_clip/frame_index.parquet")
    frames = {vid: [str(V / r) for r in g.sort_values("frame").relpath.tolist()][:3]
              for vid, g in fi.groupby("visual_video_id")}
    all_vids = [v for v in frames if len(frames[v]) >= 3]

    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor
    from PIL import Image
    snap = snap_dir()
    t0 = time.time()
    model = AutoModelForImageTextToText.from_pretrained(
        snap, torch_dtype=torch.float16, device_map=args.device).eval()
    proc = AutoProcessor.from_pretrained(snap)
    print(f"[load] InternVL3 {time.time()-t0:.0f}s", flush=True)

    def ask(imgs, q):
        if imgs:
            pil = [Image.open(p).convert("RGB") for p in imgs]
            content = [{"type": "image"} for _ in pil] + [{"type": "text", "text": q}]
            msg = [{"role": "user", "content": content}]
            prompt = proc.apply_chat_template(msg, add_generation_prompt=True)
            inp = proc(images=pil, text=prompt, return_tensors="pt").to(args.device, torch.float16)
        else:
            msg = [{"role": "user", "content": [{"type": "text", "text": q}]}]
            prompt = proc.apply_chat_template(msg, add_generation_prompt=True)
            inp = proc(text=prompt, return_tensors="pt").to(args.device)
        with torch.no_grad():
            out = model.generate(**inp, max_new_tokens=8, do_sample=False)
        return proc.batch_decode(out[:, inp["input_ids"].shape[1]:], skip_special_tokens=True)[0]

    rows = []
    t0 = time.time()
    for i, r in enumerate(items.itertuples(index=False)):
        own = frames.get(r.visual_video_id, [])
        if len(own) < 3:
            continue
        dvid = all_vids[int(rng.integers(len(all_vids)))]
        while dvid == r.visual_video_id:
            dvid = all_vids[int(rng.integers(len(all_vids)))]
        dist = frames[dvid]
        for mode, imgs, q in [("closed", None, QCLOSED[r.qtype]),
                              ("distractor", dist, QTYPES[r.qtype]),
                              ("oracle", own, QTYPES[r.qtype])]:
            pred = parse_yn(ask(imgs, q))
            rows.append({"mode": mode, "qtype": r.qtype, "gold": r.gold,
                         "pred": pred, "correct": int(pred == r.gold)})
        if (i + 1) % 30 == 0:
            print(f"  {i+1}/{len(items)}  {(i+1)/(time.time()-t0):.2f} it/s", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "condb_internvl3.csv", index=False)

    wp = ["bus", "bikes"]
    res = {"model": "internvl3", "well_posed": wp}
    for mode in ["closed", "distractor", "oracle"]:
        m = df[df.mode == mode]
        res[f"{mode}_wellposed_bal"] = bal(m, wp)
        res[f"{mode}_bikes_bal"] = bal(m, ["bikes"])
    gap = res["oracle_wellposed_bal"] - res["closed_wellposed_bal"]
    res["oracle_minus_closed"] = round(gap, 3)
    res["oracle_gt_distractor"] = bool(res["oracle_wellposed_bal"] > res["distractor_wellposed_bal"])
    res["condition_b_holds (gap>=0.15 AND oracle>distractor)"] = bool(gap >= 0.15 and res["oracle_gt_distractor"])
    (OUT / "condb_internvl3_summary.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())
