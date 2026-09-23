#!/usr/bin/env python3
"""Phase 2 (Pillar A3/C2): VLM dense captions = the DOCUMENT layer for 522 visual corpus.

Captions a stratified subset of joined+annotated visual videos with Qwen2.5-VL.
The caption is the ONLY searchable document for the visual track — the captioner
sees NOTHING but the frame pixels (no sensor CSVs, no TL_3/4 annotations, no
facet values), preserving source-level non-circularity:

  predicate  = sensor CSV (camera x10) + env category      [filter side]
  relevance  = human CVAT annotations (cameras x11/x22)     [target side]
  document   = VLM caption of the frame pixels              [searched side]

Anti-leak guard: the prompt asks for a factual scene description; a build
assertion rejects any caption that verbatim-contains a sensor facet token like
'sig_has_yellow' (paranoia-level; the captioner never receives them anyway).

Sampling: stratified over (intersection_id x time_of_day) among videos with
join_ok_120s AND TL_3 annotation; middle frame of each video is captioned.

Supports 2-GPU sharding + resume:
  --device cuda:0 --shard 0/2   (writes captions_shard0.jsonl; rerun skips done)

Run (per GPU):
  Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/04_scripts/build_intersection_captions.py \
      --device cuda:0 --shard 0/2 --n-videos 3000
  ... --device cuda:1 --shard 1/2 ...
Then merge:  ... --merge-only
"""
from __future__ import annotations

import argparse
import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DS = PROJECT_ROOT / "Datasets"
VER = DS / "processed" / "aihub_522_intersection" / "20260710"
SNAP_DEFAULT = "/hdd2/huggingface_cache/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/cc594898137f460bfe9f0759e9844b3ce807cfb5"

DEFAULT_PROMPT = ("Describe this urban intersection CCTV frame in 2-4 factual sentences: "
                  "overall traffic volume, visible vehicle types (cars, buses, trucks, "
                  "two-wheelers), any stopped or parked vehicles, pedestrians or cyclists, "
                  "and road/weather appearance. State only what is visible; no speculation.")


def select_videos(n_videos: int, seed: int) -> pd.DataFrame:
    join = pd.read_parquet(VER / "visual_sensor_join.parquet")
    ann = pd.read_parquet(VER / "annotation_video_facets.parquet")
    vv = pd.read_parquet(VER / "visual_videos.parquet")
    pool = (join[join.join_ok_120s]
            .merge(ann[["split", "visual_video_id"]], on=["split", "visual_video_id"])
            .merge(vv[["split", "visual_video_id", "intersection_id", "frame_relpaths", "n_frames"]],
                   on=["split", "visual_video_id"]))
    # stratify: intersection x time_of_day, proportional with per-cell cap
    cells = pool.groupby(["intersection_id", "time_of_day"], observed=True)
    per_cell = max(1, int(round(n_videos / max(1, cells.ngroups))))
    sel = (cells.apply(lambda g: g.sample(min(len(g), per_cell), random_state=seed))
           .reset_index(drop=True))
    if len(sel) > n_videos:
        sel = sel.sample(n_videos, random_state=seed).reset_index(drop=True)
    return sel.sort_values(["split", "visual_video_id"]).reset_index(drop=True)


def middle_frame(relpaths: list[str]) -> str:
    rp = sorted(relpaths)
    return rp[len(rp) // 2]


def load_done(out_jsonl: Path) -> set[str]:
    done = set()
    if out_jsonl.exists():
        for line in out_jsonl.read_text(encoding="utf-8").splitlines():
            try:
                done.add(json.loads(line)["visual_video_id"])
            except Exception:
                continue
    return done


def merge_shards(out_dir: Path) -> None:
    rows = []
    for shard in sorted(out_dir.glob("captions_shard*.jsonl")):
        for line in shard.read_text(encoding="utf-8").splitlines():
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    df = pd.DataFrame(rows).drop_duplicates(["split", "visual_video_id"])
    docs = pd.DataFrame({
        "doc_id": df.apply(lambda r: f"aihub_522_intersection:doc:vlm_caption:{r['split']}:{r['visual_video_id']}", axis=1),
        "clip_id": df["clip_id"], "visual_video_id": df["visual_video_id"],
        "split": df["split"],
        "dataset_id": "aihub_522_intersection", "doc_type": "vlm_dense_caption",
        "text": df["caption"], "lang": "en", "source_frame": df["frame_relpath"],
    })
    docs.to_parquet(out_dir / "documents.parquet", index=False)
    print(f"[merge] {len(docs)} caption docs -> {out_dir/'documents.parquet'}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", default=SNAP_DEFAULT)
    ap.add_argument("--device", default="cuda:0")
    ap.add_argument("--shard", default="0/1", help="k/n shard of the selected videos")
    ap.add_argument("--n-videos", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=20260710)
    ap.add_argument("--max-new-tokens", type=int, default=110)
    ap.add_argument("--max-pixels", type=int, default=448 * 448)
    ap.add_argument("--out-dir", default=str(VER / "captions"))
    prompt_group = ap.add_mutually_exclusive_group()
    prompt_group.add_argument(
        "--prompt", default=None,
        help="caption prompt; omitted means the original task-aware prompt")
    prompt_group.add_argument(
        "--prompt-file", default=None,
        help="UTF-8 text file containing the complete caption prompt")
    ap.add_argument("--merge-only", action="store_true")
    ap.add_argument("--reverse", action="store_true",
                    help="process the shard back-to-front (idle-GPU helper)")
    ap.add_argument("--out-name", default=None,
                    help="override output jsonl name (default captions_shard<k>.jsonl)")
    ap.add_argument("--extra-done", default=None,
                    help="also skip videos already present in this jsonl (snapshot)")
    args = ap.parse_args()
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    if args.merge_only:
        merge_shards(out_dir)
        return 0
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    else:
        prompt = args.prompt if args.prompt is not None else DEFAULT_PROMPT
    if not prompt:
        raise ValueError("caption prompt must not be empty")

    k, n = (int(x) for x in args.shard.split("/"))
    if n < 1 or not 0 <= k < n:
        raise ValueError(f"invalid --shard {args.shard!r}; expected k/n with 0 <= k < n")
    sel = select_videos(args.n_videos, args.seed)
    sel = sel.iloc[k::n].reset_index(drop=True)
    out_jsonl = out_dir / (args.out_name or f"captions_shard{k}.jsonl")
    done = load_done(out_jsonl)
    if args.extra_done:
        done |= load_done(Path(args.extra_done))
    todo = sel[~sel.visual_video_id.isin(done)]
    if args.reverse:
        todo = todo.iloc[::-1]
    print(f"[shard {args.shard}] selected={len(sel)} done={len(done)} todo={len(todo)}", flush=True)
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

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "snapshot": args.snapshot,
        "prompt_sha1": hashlib.sha1(prompt.encode()).hexdigest(),
        "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
        "prompt": prompt, "max_new_tokens": args.max_new_tokens,
        "max_pixels": args.max_pixels, "decoding": "greedy", "seed": args.seed,
        "n_videos_target": args.n_videos, "shard": args.shard,
        "source_separation_note": "captioner sees frame pixels only; no sensor/annotation input",
    }
    (out_dir / f"caption_manifest_shard{k}.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    SENSOR_TOKENS = ("sig_has_", "veh_density_bin", "ped_density_bin")  # paranoia guard
    t0 = time.time()
    with out_jsonl.open("a", encoding="utf-8") as fout, torch.no_grad():
        for i, r in enumerate(todo.itertuples(index=False)):
            frame_rel = middle_frame(list(r.frame_relpaths))
            fpath = VER / frame_rel
            if not fpath.exists():
                continue
            msg = [{"role": "user", "content": [
                {"type": "image", "image": f"file://{fpath}", "max_pixels": args.max_pixels},
                {"type": "text", "text": prompt}]}]
            text = proc.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
            imgs, vids = process_vision_info(msg)
            inputs = proc(text=[text], images=imgs, videos=vids, return_tensors="pt").to(args.device)
            out = model.generate(**inputs, max_new_tokens=args.max_new_tokens, do_sample=False)
            cap = proc.batch_decode(out[:, inputs.input_ids.shape[1]:],
                                    skip_special_tokens=True)[0].strip()
            assert not any(t in cap for t in SENSOR_TOKENS), "sensor token leaked into caption?!"
            fout.write(json.dumps({
                "visual_video_id": r.visual_video_id, "clip_id": r.sensor_clip_id,
                "split": r.split, "frame_relpath": frame_rel, "caption": cap,
            }, ensure_ascii=False) + "\n")
            fout.flush()
            if (i + 1) % 25 == 0:
                rate = (i + 1) / (time.time() - t0)
                print(f"  {i+1}/{len(todo)}  {rate:.2f} img/s  ETA {((len(todo)-i-1)/rate)/60:.0f} min", flush=True)
    print(f"[done] shard {args.shard}: {len(todo)} captions in {(time.time()-t0)/60:.1f} min", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
