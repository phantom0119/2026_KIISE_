#!/usr/bin/env python3
"""E-1(a) VLM mini-pilot [calibration BEFORE the full run — power + causal lever].

For n_items balanced items x {exact, strong-degraded} retrieval configs:
  - retrieve top-K frames for the item's query frame (self excluded)
  - show ONLY retrieved frames to a fixed VLM (Qwen2.5-VL, greedy)
  - binary scene question; gold = human-annotation channel of the query video
Measures: (i) acc per config, (ii) acc | mediator-hit vs no-hit (causal lever),
(iii) paired disagreement rate -> required n for SESOI 0.02 in the full run.

Question types (balanced gold 50/50 by stratified sampling):
  bus:     "at least one bus visible?"          gold = max_bus >= 1
  stopped: "any vehicles stopped/queued?"       gold = any_stopped
  bikes:   "two or more bicycles/motorbikes?"   gold = max_bike >= 2

Run:  ... run_e1a_vlm_minipilot.py --device cuda:0 --n-per-cell 30
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
V = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
OUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260711_e1a"
SNAP = "/hdd2/huggingface_cache/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/cc594898137f460bfe9f0759e9844b3ce807cfb5"
K = 3

QTYPES = {
    "bus": ("Is at least one bus visible in these frames? Answer strictly yes or no.",
            lambda a: a.max_bus >= 1),
    "stopped": ("Are any vehicles stopped or queued (not moving) in these frames? Answer strictly yes or no.",
                lambda a: bool(a.any_stopped)),
    "bikes": ("Are there two or more bicycles or motorbikes visible in these frames? Answer strictly yes or no.",
              lambda a: a.max_bike >= 2),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--n-per-cell", type=int, default=30, help="items per (qtype, gold) cell")
    ap.add_argument("--seed", type=int, default=20260711)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    import faiss
    X = np.load(V / "visual_embeddings_clip" / "frame_embeddings.npy").astype("float32")
    fi = pd.read_parquet(V / "visual_embeddings_clip" / "frame_index.parquet").reset_index(names="row")
    join = pd.read_parquet(V / "visual_sensor_join.parquet")
    ann = pd.read_parquet(V / "annotation_video_facets.parquet")
    jok = join[join.join_ok_120s][["visual_video_id", "split", "sensor_clip_id",
                                   "time_of_day", "hour"]]
    fi2 = fi.merge(jok, on=["visual_video_id", "split"], how="left")
    grp = fi2.dropna(subset=["sensor_clip_id"]).groupby("sensor_clip_id")["row"].apply(set)
    pool = jok.merge(ann, on=["visual_video_id", "split"])
    frames_by_vid = fi.groupby(["visual_video_id", "split"])["row"].apply(sorted)

    # ---- balanced item sampling ----
    items = []
    for qt, (question, gold_fn) in QTYPES.items():
        g = pool.copy()
        g["gold"] = g.apply(gold_fn, axis=1)
        for gv in (True, False):
            sub = g[g.gold == gv].sample(args.n_per_cell, random_state=args.seed)
            for _, r in sub.iterrows():
                rows = frames_by_vid.get((r.visual_video_id, r.split))
                if not rows:
                    continue
                qrow = rows[len(rows) // 2]
                ev = grp.get(r.sensor_clip_id, set()) - {qrow}
                items.append({"qtype": qt, "question": question, "gold": "yes" if gv else "no",
                              "visual_video_id": r.visual_video_id, "split": r.split,
                              "qrow": qrow, "evidence": ev})
    print(f"[items] {len(items)} (balanced)")

    # ---- retrieval under two locked configs ----
    lock = json.load(open(OUT / "e1a_locked_configs.json"))
    d = X.shape[1]
    faiss.omp_set_num_threads(0)
    def build(cfg):
        if cfg == "flat_exact":
            ix = faiss.IndexFlatIP(d); ix.add(X); return ix
        assert cfg.startswith("ivfpq"), cfg
        # cfg like ivfpq_nlist1024_m32_nprobe8
        toks = cfg.split("_")
        nlist = int(toks[1].replace("nlist", "")); m = int(toks[2].replace("m", ""))
        nprobe = int(toks[3].replace("nprobe", ""))
        qz = faiss.IndexFlatIP(d)
        ix = faiss.IndexIVFPQ(qz, d, nlist, m, 8, faiss.METRIC_INNER_PRODUCT)
        ix.train(X); ix.add(X); ix.nprobe = nprobe
        return ix
    configs = {"exact": build("flat_exact"), "strong": build(lock["strong"])}
    Q = X[[it["qrow"] for it in items]]
    retrieved = {}
    for name, ix in configs.items():
        _, I = ix.search(Q, K + 1)
        retrieved[name] = [[i for i in row if i != it["qrow"]][:K]
                           for row, it in zip(I, items)]
    row2path = dict(zip(fi.row, fi.relpath))

    # ---- VLM ----
    import torch
    from PIL import Image
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
    from qwen_vl_utils import process_vision_info
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        SNAP, torch_dtype=torch.float16, device_map=args.device).eval()
    proc = AutoProcessor.from_pretrained(SNAP)
    print("[vlm] loaded", flush=True)

    def answer(frame_rows, question):
        content = [{"type": "image", "image": f"file://{V / row2path[r]}",
                    "max_pixels": 448 * 448} for r in frame_rows]
        content.append({"type": "text", "text":
                        "These CCTV frames were retrieved from a video database as evidence. "
                        + question})
        msg = [{"role": "user", "content": content}]
        text = proc.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
        imgs, vids = process_vision_info(msg)
        inputs = proc(text=[text], images=imgs, videos=vids, return_tensors="pt").to(args.device)
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=4, do_sample=False)
        t = proc.batch_decode(out[:, inputs.input_ids.shape[1]:], skip_special_tokens=True)[0].lower()
        return "yes" if "yes" in t else ("no" if "no" in t else "?")

    rows = []
    t0 = time.time()
    for ci, (cname, rets) in enumerate(retrieved.items()):
        for i, (it, rr) in enumerate(zip(items, rets)):
            pred = answer(rr, it["question"])
            hit = bool(it["evidence"].intersection(rr))
            rows.append({"config": cname, "qtype": it["qtype"], "gold": it["gold"],
                         "pred": pred, "correct": int(pred == it["gold"]),
                         "mediator_hit": int(hit),
                         "visual_video_id": it["visual_video_id"]})
            if (i + 1) % 40 == 0:
                done = ci * len(items) + i + 1
                rate = done / (time.time() - t0)
                print(f"  {done}/{2*len(items)}  {rate:.2f} it/s", flush=True)
    df = pd.DataFrame(rows)
    df.to_parquet(OUT / "e1a_vlm_minipilot.parquet")

    # ---- calibration analysis ----
    print("\n=== acc per config ===")
    print(df.groupby("config").correct.mean().round(4).to_string())
    print("\n=== causal lever: acc | mediator hit vs no-hit (pooled) ===")
    print(df.groupby("mediator_hit").correct.mean().round(4).to_string())
    print("\n=== per qtype x config ===")
    print(df.pivot_table(index="qtype", columns="config", values="correct").round(3).to_string())
    piv = df.pivot_table(index=["visual_video_id", "qtype"], columns="config", values="correct")
    dis = float((piv["exact"] != piv["strong"]).mean())
    print(f"\npaired disagreement rate = {dis:.4f}")
    half = lambda n: 1.96 * np.sqrt(dis / n)
    for n in (2000, 4000, 6000, 10000):
        print(f"  n={n}: paired CI half-width ≈ {half(n):.4f}")
    mhit = df.groupby("config").mediator_hit.mean()
    print("\nmediator hit-rate per config:"); print(mhit.round(4).to_string())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
