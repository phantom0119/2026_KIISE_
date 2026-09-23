#!/usr/bin/env python3
"""UCA external-validity corpus builder [prereg 420 Amendment 6 + 6a, FROZEN].

Implements, in order:
  G-B'   ffprobe every matched video; assert container_duration >=
         max(selected midpoint)+0.5s else CLAMP mid <- container-0.5 (count reported)
  SEG    per video: sort (timestamps, sentences) by (start, end); take indices
         round(linspace(0, n-1, min(n,4))); midpoint = round((s+e)/2, 1);
         DEDUP identical (video_id, midpoint) -> one document, sentences unioned
  FRAME  ffmpeg time-based seek (-ss mid), 1 frame, q:v 2; on failure retry at
         max(0, mid-1.0); still failing -> drop + report
  REL    10 frozen lexicons (Amendment 6a table, re.IGNORECASE) on unioned
         sentences -> relevance table (separate file; NEVER in metadata)
  META   video_class (14, no cap) / video_duration_bin (container terciles;
         the ONLY channel-clean headline field) / event_position_bin
         (mid/container terciles; annotation-timing channel, demoted)
  PILOT  50 segments with forced adversarial strata (longest video, near-end
         midpoints, both Normal id styles, >=1 per zip folder), seed 20260712

Outputs: Datasets/processed/uca_anchor/20260712/
  {segments.parquet, relevance.parquet, metadata.parquet, frames/*.jpg,
   pilot50.csv, build_manifest.json}
Run (any python3 with pandas+numpy; ffmpeg/ffprobe on PATH).
"""
from __future__ import annotations

import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

UCA = Path("/hdd2/KIISE_datasociety/Datasets/external/UCA_surveillance")
EXTR = UCA / "extracted"
OUT = Path("/hdd2/KIISE_datasociety/Datasets/processed/uca_anchor/20260712")
FRAMES = OUT / "frames"
FFMPEG = "/hdd2/KIISE_datasociety/Datasets/tools/ffmpeg"
FFPROBE = "/hdd2/KIISE_datasociety/Datasets/tools/ffprobe"

LEX = {  # Amendment 6a frozen table (left-anchored boundaries, IGNORECASE)
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


def ffprobe_dur(path: Path) -> float:
    r = subprocess.run(
        [FFPROBE, "-v", "error", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return -1.0


def extract_frame(video: Path, mid: float, out_jpg: Path) -> bool:
    for t in (mid, max(0.0, mid - 1.0)):
        r = subprocess.run(
            [FFMPEG, "-y", "-v", "error", "-ss", f"{t:.1f}", "-i", str(video),
             "-frames:v", "1", "-q:v", "2", str(out_jpg)], capture_output=True)
        if out_jpg.exists() and out_jpg.stat().st_size > 1024:
            return True
    return False


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    FRAMES.mkdir(exist_ok=True)
    id2m = json.loads((UCA / "id_to_member.json").read_text())
    vids = {}
    for sp in ["Train", "Val", "Test"]:
        d = json.loads((UCA / "repo/UCF Annotation/json" / f"UCFCrime_{sp}.json").read_text())
        for k, v in d.items():
            vids[k] = {**v, "split": sp}
    assert set(vids) == set(id2m), "id mapping/annotation mismatch"

    # ---- SEG: frozen selection + dedup ----
    docs = {}
    for vid, v in vids.items():
        ts = sorted(zip(v["timestamps"], v["sentences"]), key=lambda x: (x[0][0], x[0][1]))
        n = len(ts)
        idx = sorted(set(int(round(i)) for i in np.linspace(0, n - 1, min(n, 4))))
        for i in idx:
            (s, e), sent = ts[i]
            mid = round((s + e) / 2, 1)
            key = (vid, mid)
            docs.setdefault(key, {"video_id": vid, "midpoint": mid,
                                  "split": v["split"], "ann_duration": v["duration"],
                                  "sentences": []})["sentences"].append(sent)
    n_collapsed = sum(1 for _ in vids) and (
        sum(len(d["sentences"]) for d in docs.values()) - len(docs))
    print(f"[SEG] documents={len(docs)} collapsed_duplicates={n_collapsed}")

    # ---- G-B': container durations (parallel ffprobe) ----
    paths = {vid: EXTR / id2m[vid] for vid in vids}
    missing = [v for v, p in paths.items() if not p.exists()]
    assert not missing, f"extracted files missing: {missing[:5]}"
    with ThreadPoolExecutor(8) as ex:
        durs = dict(zip(paths, ex.map(ffprobe_dur, paths.values())))
    bad_probe = [v for v, d in durs.items() if d <= 0]
    assert not bad_probe, f"ffprobe failed: {bad_probe[:5]}"
    clamped = 0
    for key, d in docs.items():
        cdur = durs[d["video_id"]]
        d["container_duration"] = cdur
        if d["midpoint"] > cdur - 0.5:
            d["midpoint_clamped_from"] = d["midpoint"]
            d["midpoint"] = round(max(0.0, cdur - 0.5), 1)
            clamped += 1
    print(f"[G-B'] ffprobe ok for {len(durs)}; midpoints clamped={clamped}")

    # re-dedup after clamping (clamp can merge midpoints)
    merged = {}
    for d in docs.values():
        key = (d["video_id"], d["midpoint"])
        if key in merged:
            merged[key]["sentences"] += d["sentences"]
        else:
            merged[key] = d
    docs = merged
    print(f"[SEG] documents after clamp-merge={len(docs)}")

    # ---- FRAME extraction ----
    items = sorted(docs.values(), key=lambda d: (d["video_id"], d["midpoint"]))
    for i, d in enumerate(items):
        d["doc_id"] = f"uca:{d['video_id']}:{d['midpoint']:.1f}"
        d["frame"] = str(FRAMES / f"{i:05d}_{d['video_id']}_{d['midpoint']:.1f}.jpg")

    def work(d):
        return extract_frame(paths[d["video_id"]], d["midpoint"], Path(d["frame"]))
    with ThreadPoolExecutor(8) as ex:
        ok = list(ex.map(work, items))
    dropped = [d for d, o in zip(items, ok) if not o]
    items = [d for d, o in zip(items, ok) if o]
    print(f"[FRAME] extracted={len(items)} dropped={len(dropped)}")

    # ---- REL + META tables (separate files; A6-UCA (d)) ----
    cls_re = re.compile(r"([A-Za-z_]+?)\d")
    rel_rows, meta_rows, seg_rows = [], [], []
    cdurs = np.array([d["container_duration"] for d in items])
    ter = np.quantile(cdurs, [1 / 3, 2 / 3])
    for d in items:
        vid = d["video_id"]
        cls = cls_re.match(vid).group(1).rstrip("_")
        joined = " ".join(d["sentences"])
        rel_rows.append({"doc_id": d["doc_id"],
                         **{f"rel_{k}": bool(re.search(rx, joined, re.IGNORECASE))
                            for k, rx in LEX.items()}})
        dbin = "short" if d["container_duration"] <= ter[0] else \
               "long" if d["container_duration"] > ter[1] else "medium"
        pos = d["midpoint"] / max(d["container_duration"], 0.1)
        pbin = "early" if pos <= 1 / 3 else "late" if pos > 2 / 3 else "mid"
        meta_rows.append({"doc_id": d["doc_id"], "video_class": cls,
                          "video_duration_bin": dbin, "event_position_bin": pbin})
        seg_rows.append({k: d[k] for k in
                         ["doc_id", "video_id", "split", "midpoint",
                          "container_duration", "ann_duration", "frame"]}
                        | {"n_sentences": len(d["sentences"])})
    pd.DataFrame(seg_rows).to_parquet(OUT / "segments.parquet")
    pd.DataFrame(rel_rows).to_parquet(OUT / "relevance.parquet")
    pd.DataFrame(meta_rows).to_parquet(OUT / "metadata.parquet")
    # sentences stored ONLY on the relevance side (audit artifact, never a document)
    pd.DataFrame([{"doc_id": d["doc_id"], "sentences": d["sentences"]}
                  for d in items]).to_parquet(OUT / "annotation_sentences.parquet")

    # ---- PILOT 50 with forced adversarial strata ----
    df = pd.DataFrame(seg_rows)
    forced = set()
    longest = df.loc[df.container_duration.idxmax(), "doc_id"]
    forced.add(longest)
    near_end = df[df.midpoint > df.container_duration - 1.0].doc_id.tolist()
    forced.update(near_end[:8])
    for style in [r"Normal_Videos_\d", r"Normal_Videos\d"]:
        m = df[df.video_id.str.match(style)]
        if len(m):
            forced.add(m.iloc[0].doc_id)
    for folder in sorted({m.split("/")[2] for m in id2m.values()}):
        vids_f = [v for v, mm in id2m.items() if mm.split("/")[2] == folder]
        m = df[df.video_id.isin(vids_f)]
        if len(m):
            forced.add(m.iloc[0].doc_id)
    rng = np.random.default_rng(20260712)
    rest = df[~df.doc_id.isin(forced)]
    classes = pd.DataFrame(meta_rows).set_index("doc_id").video_class
    pick = []
    for cls in classes.unique():
        pool = rest[rest.doc_id.map(classes) == cls]
        if len(pool):
            pick.append(pool.iloc[int(rng.integers(len(pool)))].doc_id)
    pilot = list(forced) + [p for p in pick if p not in forced]
    pilot = pilot[:50] if len(pilot) >= 50 else pilot + \
        rest[~rest.doc_id.isin(pilot)].sample(50 - len(pilot),
                                              random_state=20260712).doc_id.tolist()
    pd.Series(sorted(pilot[:50])).to_csv(OUT / "pilot50.csv", index=False, header=False)

    manifest = {
        "date": "2026-07-12", "prereg": "420 Amendment 6+6a (frozen)",
        "documents": len(items), "collapsed_duplicates": int(n_collapsed),
        "clamped_midpoints": clamped, "dropped_frames": len(dropped),
        "dropped_ids": [d["doc_id"] for d in dropped][:20],
        "id_mapping": "id_to_member.json (49 collisions -> lexicographic first)",
        "duration_terciles": [round(float(t), 1) for t in ter],
        "lexicons_sha1_source": "Amendment 6a table",
        "pilot_forced_strata": {"longest": longest, "near_end": len(near_end),
                                "folders": len({m.split('/')[2] for m in id2m.values()})},
        "ffmpeg_version": "7.0.2-static (johnvansickle)",
        "license_note": "UCA/UCF-Crime academic research only (state in availability)",
    }
    (OUT / "build_manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"[saved] {OUT} (docs={len(items)}, pilot=50)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
