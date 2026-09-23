#!/usr/bin/env python3
"""UCA document layer: Qwen2.5-VL captions of segment midpoint frames
[prereg 420 Amendment 6+6a; adapted from build_intersection_captions.py].

The captioner sees ONLY the frame pixels. The prompt is scene-generic and
contains NO term matched by any frozen relevance lexicon (checked at import).
Prompt-target coupling remains a disclosed 2.5-channel limitation (manuscript).

Run (per GPU, kiise-vlmdb env):
  caption_uca.py --device cuda:0 --shard 0/2 [--pilot]
  caption_uca.py --merge-only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

OUT_ROOT = Path("/hdd2/KIISE_datasociety/Datasets/processed/uca_anchor/20260712")
SNAP_DEFAULT = ("/hdd2/huggingface_cache/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/"
                "snapshots/cc594898137f460bfe9f0759e9844b3ce807cfb5")

PROMPT = ("Describe this surveillance camera frame in 2-4 factual sentences: "
          "the setting, the people visible and what they are doing, any "
          "vehicles or objects present, and anything notable happening.")

LEX = {  # must mirror build_uca_corpus.LEX (import avoided: keep script standalone)
    "falls": r"\b(fell|falls|falling|knocked down|collaps)",
    "fight": r"\b(fight|punch|kick|beat|hit(ting)?)",
    "fire": r"\b(fire|smoke|flame|burn)",
    "weapon": r"\b(gun|pistol|rifle|knife|weapon)",
    "running": r"\b(ran|runs?|running)\b",
    "crash": r"\b(crash|collid|collision|accident)",
    "money": r"\b(money|cash\b|register)",
    "door": r"\bdoors?\b",
    "take": r"\b(took|grabbed|picked up)",
    "enterexit": r"\b(entered|exited|left the)",
}
for _k, _rx in LEX.items():  # prompt purity assertion (Amendment 6)
    assert not re.search(_rx, PROMPT, re.IGNORECASE), f"prompt contains lexicon {_k}!"

# e1 paranoia guard: machine tokens that cannot arise from pixels
LABEL_KEY_TOKENS = ("video_class", "video_duration_bin", "event_position_bin",
                    "Normal_Videos", "RoadAccidents", "_x264")


def load_done(p: Path) -> set:
    if not p.exists():
        return set()
    return {json.loads(l)["doc_id"] for l in p.read_text().splitlines() if l.strip()}


def merge_shards() -> None:
    rows = []
    for shard in sorted((OUT_ROOT / "captions").glob("captions_shard*.jsonl")):
        for line in shard.read_text().splitlines():
            if line.strip():
                rows.append(json.loads(line))
    df = pd.DataFrame(rows).drop_duplicates("doc_id")
    df.to_parquet(OUT_ROOT / "captions" / "documents.parquet", index=False)
    print(f"[merge] {len(df)} caption docs")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default=SNAP_DEFAULT)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--shard", default="0/1")
    ap.add_argument("--pilot", action="store_true", help="G-C: pilot50 only")
    ap.add_argument("--max-new-tokens", type=int, default=110)
    ap.add_argument("--max-pixels", type=int, default=448 * 448)
    ap.add_argument("--merge-only", action="store_true")
    ap.add_argument("--reverse", action="store_true")
    args = ap.parse_args()
    (OUT_ROOT / "captions").mkdir(exist_ok=True)
    if args.merge_only:
        merge_shards()
        return 0

    seg = pd.read_parquet(OUT_ROOT / "segments.parquet")
    if args.pilot:
        pilot = set(pd.read_csv(OUT_ROOT / "pilot50.csv", header=None)[0])
        seg = seg[seg.doc_id.isin(pilot)]
    k, n = (int(x) for x in args.shard.split("/"))
    seg = seg.sort_values("doc_id").iloc[k::n]
    name = f"captions_pilot_shard{k}.jsonl" if args.pilot else f"captions_shard{k}.jsonl"
    out_jsonl = OUT_ROOT / "captions" / name
    done = load_done(out_jsonl)
    if not args.pilot:  # full run also skips pilot-covered docs
        for pp in (OUT_ROOT / "captions").glob("captions_pilot_shard*.jsonl"):
            done |= load_done(pp)
    todo = seg[~seg.doc_id.isin(done)]
    if args.reverse:
        todo = todo.iloc[::-1]
    print(f"[shard {args.shard}{' pilot' if args.pilot else ''}] "
          f"selected={len(seg)} done={len(done)} todo={len(todo)}", flush=True)
    if todo.empty:
        return 0

    import torch
    from transformers import AutoProcessor, Qwen2_5_VLForConditionalGeneration
    from qwen_vl_utils import process_vision_info
    t0 = time.time()
    model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        args.snapshot, torch_dtype=torch.float16, device_map=args.device).eval()
    proc = AutoProcessor.from_pretrained(args.snapshot)
    print(f"[load] {time.time()-t0:.0f}s", flush=True)

    (OUT_ROOT / "captions" / f"caption_manifest_shard{k}.json").write_text(json.dumps({
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": args.snapshot, "prompt": PROMPT,
        "prompt_sha1": hashlib.sha1(PROMPT.encode()).hexdigest(),
        "max_new_tokens": args.max_new_tokens, "max_pixels": args.max_pixels,
        "decoding": "greedy", "shard": args.shard, "pilot": args.pilot,
        "source_separation_note": "pixels only; no annotation/metadata input; "
                                  "prompt contains no lexicon-matched term",
    }, indent=2))

    t0 = time.time()
    with out_jsonl.open("a") as fout, torch.no_grad():
        for i, r in enumerate(todo.itertuples(index=False)):
            fpath = Path(r.frame)
            if not fpath.exists():
                continue
            msg = [{"role": "user", "content": [
                {"type": "image", "image": f"file://{fpath}", "max_pixels": args.max_pixels},
                {"type": "text", "text": PROMPT}]}]
            text = proc.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
            imgs, vids = process_vision_info(msg)
            inputs = proc(text=[text], images=imgs, videos=vids,
                          return_tensors="pt").to(args.device)
            out = model.generate(**inputs, max_new_tokens=args.max_new_tokens,
                                 do_sample=False)
            cap = proc.batch_decode(out[:, inputs.input_ids.shape[1]:],
                                    skip_special_tokens=True)[0].strip()
            assert not any(t in cap for t in LABEL_KEY_TOKENS), \
                f"label key leaked into caption?! {r.doc_id}"
            fout.write(json.dumps({"doc_id": r.doc_id, "video_id": r.video_id,
                                   "split": r.split, "caption": cap}) + "\n")
            fout.flush()
            if (i + 1) % 25 == 0:
                rate = (i + 1) / (time.time() - t0)
                print(f"  {i+1}/{len(todo)}  {rate:.2f} img/s  "
                      f"ETA {((len(todo)-i-1)/rate)/60:.0f} min", flush=True)
    print(f"[done] shard {args.shard}: {len(todo)} in {(time.time()-t0)/60:.1f} min",
          flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
