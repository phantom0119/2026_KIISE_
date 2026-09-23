#!/usr/bin/env python3
"""Answer-level multi-view VLM experiment (AI Hub 71953). Pre-reg: project_md/archive/legacy_premerge_20260728/410_METHOD_prereg_multiview_answer_level_20260708.md (구 35).

Leakage-free NEUTRAL closed-set event-type classification. A fixed VLM
(Qwen2.5-VL-7B-Instruct, temp=0) is given evidence frames under 4 view
conditions and must pick the event_class from 11 candidates -> JSON.

Conditions: closed_book (no images), worse_view_only, better_view_only, both_view.
better/worse view = larger/smaller mean bbox area (from the stratum manifest).
"""
from __future__ import annotations
import argparse, json, re, time, sys, hashlib
from datetime import datetime
from pathlib import Path
import pandas as pd, torch

ROOT = Path(__file__).resolve().parents[3]
SEED = 20260708
CONDITIONS = ["closed_book", "worse_view_only", "better_view_only", "both_view"]


def build_candidates(classes):
    import random
    r = random.Random(SEED)
    c = list(classes)
    r.shuffle(c)
    return c


def match_class(ec, valid_classes):
    """Conservative, auditable mapping of a raw prediction to a candidate.
    valid_classes is the ORDERED shown candidate list (index N -> valid_classes[N-1]).
    exact; else 'N' or 'N) text' index; else UNIQUE verbatim substring; else None."""
    ec = ec.strip()
    if ec in valid_classes:
        return ec, "exact"
    mnum = re.match(r"^\s*(\d{1,2})\)?\s*(.*)$", ec)
    if mnum:
        idx = int(mnum.group(1)); rest = mnum.group(2).strip()
        if rest in valid_classes:
            return rest, "exact"
        if 1 <= idx <= len(valid_classes):
            return valid_classes[idx - 1], "index"
    subs = [v for v in valid_classes if v and v in ec]
    if len(subs) == 1:
        return subs[0], "snap_substr"
    return None, ("ambiguous" if subs else "unmatched")


def parse_json(text, valid_classes):
    m = re.search(r"\{.*\}", text, re.S)
    o = None
    if m:
        try:
            o = json.loads(m.group(0))
        except Exception:
            o = None
    if o is None:
        mm = re.search(r'"event_class"\s*:\s*"([^"]+)"', text)
        if not mm:
            return None, "no_json"
        o = {"event_class": mm.group(1)}
        status = "regex_json"
    else:
        status = "ok"
    ec = str(o.get("event_class", "")).strip()
    matched, mstatus = match_class(ec, valid_classes)
    return {"event_class": matched, "raw_pred": ec, "match": mstatus,
            "confidence": o.get("confidence"), "supporting_view": str(o.get("supporting_view", "")).strip(),
            "rationale": str(o.get("rationale", ""))[:300]}, status


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stratum-manifest", required=True)
    ap.add_argument("--frame-root", required=True)
    ap.add_argument("--model-path", default="/hdd2/huggingface_cache/hub/models--Qwen--Qwen2.5-VL-7B-Instruct")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="0=all clips (smoke test with small N first)")
    ap.add_argument("--max-new-tokens", type=int, default=256)
    ap.add_argument("--device", default="cuda:0")
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    man = pd.read_parquet(args.stratum_manifest)
    frames = pd.read_parquet(Path(args.frame_root) / "frames.parquet")
    fpaths = {}  # (clip_id, view) -> [jpg paths sorted]
    pcol = "frame_path" if "frame_path" in frames else "media_path"
    for (cid, v), g in frames.sort_values(["clip_id", "view", "frame_seq"]).groupby(["clip_id", "view"]):
        fpaths[(str(cid), str(v))] = [str(p) for p in g[pcol].tolist()]
    # only clips whose frames are materialized
    have = {c for (c, _v) in fpaths}
    man = man[man.clip_id.astype(str).isin(have)].reset_index(drop=True)
    if args.limit:
        man = man.head(args.limit)
    classes = sorted(man.event_class.dropna().unique().tolist())
    if len(classes) < 11:  # fall back to full canonical class list
        cl = pd.read_parquet(Path(args.frame_root).parents[2] / "canonical/clips.parquet")
        classes = sorted(cl.event_class.dropna().unique().tolist())
    cands = build_candidates(classes)
    cand_block = "\n".join(f"{i+1}) {c}" for i, c in enumerate(cands))
    print(f"[data] {len(man)} clips materialized, {len(cands)} candidate classes")

    from transformers import AutoConfig, AutoProcessor
    arch = (AutoConfig.from_pretrained(args.model_path).architectures or [""])[0]
    is_qwen = "Qwen2_5_VL" in arch or "Qwen2VL" in arch
    if "Qwen2_5_VL" in arch:
        from transformers import Qwen2_5_VLForConditionalGeneration as VLM
    elif "Qwen2VL" in arch:
        from transformers import Qwen2VLForConditionalGeneration as VLM
    else:
        from transformers import AutoModelForImageTextToText as VLM
    process_vision_info = None
    if is_qwen:
        from qwen_vl_utils import process_vision_info
    print(f"[model] {arch} (qwen={is_qwen}) <- {args.model_path}")
    model = VLM.from_pretrained(args.model_path, torch_dtype=torch.float16, device_map=args.device).eval()
    proc = AutoProcessor.from_pretrained(args.model_path)

    Q = ("다음은 하나의 사건에 대한 CCTV 증거이다. 제시된 증거만 보고, 아래 후보 중 "
         "이 증거에서 관찰되는 사건 유형 하나를 고르라.\n후보:\n" + cand_block +
         '\n반드시 아래 형식의 JSON 하나만 출력하라(다른 말 금지). '
         'event_class에는 번호가 아니라 후보의 전체 텍스트를 그대로 적어라:\n'
         '{"event_class": "<후보 텍스트 그대로>", "confidence": <0~1 숫자>, '
         '"supporting_view": "c1|c2|both|none 중 하나", "rationale": "<한 문장 근거>"}')
    SYS = "너는 CCTV 영상 증거를 분석하는 전문가다. 제시된 이미지 증거만 근거로 판단한다."

    def content_for(cond, cid, better, worse):
        items = []
        if cond == "worse_view_only":
            items.append({"type": "text", "text": f"[카메라 {worse} 증거]"})
            items += [{"type": "image", "image": "file://" + p} for p in fpaths.get((cid, worse), [])]
        elif cond == "better_view_only":
            items.append({"type": "text", "text": f"[카메라 {better} 증거]"})
            items += [{"type": "image", "image": "file://" + p} for p in fpaths.get((cid, better), [])]
        elif cond == "both_view":
            for v in ("c1", "c2"):  # real names so supporting_view is interpretable; order fixed c1,c2
                items.append({"type": "text", "text": f"[카메라 {v} 증거]"})
                items += [{"type": "image", "image": "file://" + p} for p in fpaths.get((cid, v), [])]
        items.append({"type": "text", "text": Q})
        return items

    from PIL import Image as _PImage
    def _imgs_from_msg(msg):
        out = []
        for m in msg:
            c = m.get("content")
            if isinstance(c, list):
                for it in c:
                    if isinstance(it, dict) and it.get("type") == "image":
                        out.append(_PImage.open(str(it["image"]).replace("file://", "")).convert("RGB"))
        return out or None

    @torch.no_grad()
    def ask(cond, cid, better, worse):
        msg = [{"role": "system", "content": SYS},
               {"role": "user", "content": content_for(cond, cid, better, worse)}]
        text = proc.apply_chat_template(msg, tokenize=False, add_generation_prompt=True)
        if is_qwen:
            imgs, vids = process_vision_info(msg)
            inp = proc(text=[text], images=imgs, videos=vids, padding=True, return_tensors="pt").to(args.device)
            gen = model.generate(**inp, max_new_tokens=args.max_new_tokens, do_sample=False, temperature=None, top_p=None, top_k=None)
        else:
            imgs = _imgs_from_msg(msg)
            inp = proc(text=[text], images=imgs, padding=True, return_tensors="pt").to(args.device)
            gen = model.generate(**inp, max_new_tokens=args.max_new_tokens, do_sample=False)
        trimmed = gen[0][inp.input_ids.shape[1]:]
        return proc.decode(trimmed, skip_special_tokens=True)

    rows = []
    ckpt = out / "vlm_answers_partial.parquet"
    t0 = time.time()
    for i, r in man.iterrows():
        cid = str(r.clip_id); better = str(r.better_view); worse = str(r.worse_view)
        for cond in CONDITIONS:
            raw = ask(cond, cid, better, worse)
            p, status = parse_json(raw, cands)
            p = p or {}
            rows.append({"clip_id": cid, "condition": cond, "stratum": r.stratum,
                         "event_class_gold": r.event_class, "area_ratio": float(r.area_ratio),
                         "better_view": better, "worse_view": worse,
                         "pred_event_class": p.get("event_class"), "raw_pred": p.get("raw_pred"),
                         "match": p.get("match"), "confidence": p.get("confidence"),
                         "supporting_view": p.get("supporting_view"), "rationale": p.get("rationale"),
                         "valid_json": status == "ok", "parse_status": status,
                         "correct": bool(p.get("event_class") is not None and p.get("event_class") == r.event_class),
                         "raw_output": raw[:500]})
        if (i + 1) % 20 == 0:
            pd.DataFrame(rows).to_parquet(ckpt)
            acc = pd.DataFrame(rows).groupby("condition")["correct"].mean().to_dict()
            print(f"  {i+1}/{len(man)} clips ({(time.time()-t0)/(i+1):.1f}s/clip) acc={ {k: round(v,3) for k,v in acc.items()} }")
    df = pd.DataFrame(rows)
    df.to_parquet(out / "vlm_answers.parquet")
    (out / "candidates.json").write_text(json.dumps({"candidates": cands, "seed": SEED}, ensure_ascii=False, indent=2))
    # reproducibility manifest
    import transformers
    try:
        import qwen_vl_utils as _qvu; qvu_ver = getattr(_qvu, "__version__", "unknown")
    except Exception:
        qvu_ver = "n/a"
    manifest = {
        "created_at": datetime.now().isoformat(), "script": str(Path(__file__).resolve()),
        "model_path": str(args.model_path), "resolved_snapshot": Path(args.model_path).name,
        "model_architecture": arch,
        "decoding": {"do_sample": False, "temperature": 0, "greedy": True, "max_new_tokens": args.max_new_tokens},
        "prompt": {"system": SYS, "user_template": Q, "prompt_sha256": hashlib.sha256((SYS + "\n" + Q).encode()).hexdigest()},
        "candidates": cands, "candidate_seed": SEED, "conditions": CONDITIONS,
        "frame_root": str(args.frame_root), "stratum_manifest": str(args.stratum_manifest),
        "n_clips": int(man.clip_id.nunique()), "device": args.device, "argv": sys.argv,
        "versions": {"python": sys.version.split()[0], "torch": torch.__version__,
                     "transformers": transformers.__version__, "qwen_vl_utils": qvu_ver},
    }
    (out / "run_manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    if ckpt.exists():
        ckpt.unlink()
    print("\n=== accuracy by condition ===")
    print(df.groupby("condition")["correct"].agg(["mean", "count"]).reindex(CONDITIONS).round(4).to_string())
    print("invalid JSON rate:", round(1 - df.valid_json.mean(), 4))
    print("saved ->", out)


if __name__ == "__main__":
    main()
