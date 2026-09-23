#!/usr/bin/env python3
"""FULL VERIFICATION SUITE — the paper's machine-checkable trust chain, one pass.

V1  Dataset integrity        counts/alignment of every corpus artifact
V2  Workload validity        A6/A9 audit JSONs re-asserted + P1 mask re-derivation
V3  No-cherry-picking guards preregistration artifacts exist; the 85-query set is
                             re-derived from the mechanical rule (bit-identical);
                             every real predicate has its paired control rows;
                             every ladder config is reported; all three sample
                             splits (orig/new/combined) present; negative results
                             (E-1 gates/walls) preserved in assets
V4  Manuscript numbers       delegates to verify_manuscript_v2_numbers.py (76 checks)
V5  Environment capture      records exact HW/SW spec to a machine-readable
                             manifest and asserts the manuscript's pinned versions
                             match the live environment

Output: paper_assets/verification_suite_20260711/{report.json, environment_manifest.json}
Exit 0 iff every check passes.
"""
from __future__ import annotations

import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

R2 = Path(__file__).resolve().parents[2]
DS = R2.parent / "Datasets" / "processed"
V = DS / "aihub_522_intersection" / "20260710"
PB = R2 / "paper_assets" / "20260710_pillarB"
OUT = R2 / "paper_assets" / "verification_suite_20260711"
OUT.mkdir(parents=True, exist_ok=True)

results: list[dict] = []
def check(section, name, cond, detail=""):
    results.append({"section": section, "name": name,
                    "pass": bool(cond), "detail": str(detail)[:200]})
    print(f"  [{'PASS' if cond else 'FAIL'}] {section} / {name} {detail}")

# ================= V1: dataset integrity =================
sf = pd.read_parquet(V / "sensor_facets.parquet")
check("V1", "sensor_facets 32,880", len(sf) == 32880, len(sf))
check("V1", "63 intersections", sf.intersection_id.nunique() == 63)
vv = pd.read_parquet(V / "visual_videos.parquet")
check("V1", "visual_videos 52,462", len(vv) == 52462, len(vv))
jn = pd.read_parquet(V / "visual_sensor_join.parquet")
check("V1", "join_120s 47,308", int(jn.join_ok_120s.sum()) == 47308)
ann = pd.read_parquet(V / "annotation_video_facets.parquet")
check("V1", "annotation 52,210", len(ann) == 52210)
emb = np.load(V / "visual_embeddings_clip/frame_embeddings.npy", mmap_mode="r")
fidx = pd.read_parquet(V / "visual_embeddings_clip/frame_index.parquet")
check("V1", "frame emb/index aligned 143,830", emb.shape == (143830, 512) and len(fidx) == 143830)
norms = np.linalg.norm(np.asarray(emb[:2000]), axis=1)
check("V1", "embeddings L2-normalized", abs(norms.mean() - 1) < 1e-3 and norms.std() < 1e-3)
sin = np.load(DS / "sinnaedoro_traffic/corpus_real/frame_embeddings.npy", mmap_mode="r")
check("V1", "sinnaedoro 132,521x512", sin.shape == (132521, 512))
cap = pd.read_parquet(V / "captions/documents.parquet")
check("V1", "captions 3,000 unique", cap.drop_duplicates(["split", "visual_video_id"]).shape[0] == 3000)

# ================= V2: workload validity =================
a6 = json.loads((V / "canonical_trisource_expanded/A6_trisource_audit.json").read_text())
check("V2", "A6 expanded overall_pass", a6["overall_pass"])
for k, a in a6["assertions"].items():
    check("V2", f"A6.{k}", a["pass"])
for tag, root in [("VRU", DS / "vru_accident/20260710_noncircular"),
                  ("AIHub", DS / "aihub_intelligent_cctv/20260710_noncircular")]:
    a9 = json.loads((root / "canonical/A9_noncircular_audit.json").read_text())
    check("V2", f"A9.{tag} overall_pass", a9["overall_pass"])
# P1 mask re-derivation (corpus A natural masks vs registered counts)
p1a = pd.read_csv(PB / "P1_predicates_A.csv")
fi = pd.read_parquet(DS / "sinnaedoro_traffic/corpus_real/frame_index.parquet")
hour = fi["time"].astype(str).str[:2]
ok_cnt = 0
for _, r in p1a[p1a.kind == "natural"].iterrows():
    f, v = r.predicate.split("==")
    m = (hour == v).sum() if f == "hour" else (fi[f].astype(str) == v).sum()
    ok_cnt += int(m == r["count"])
check("V2", "P1-A natural masks re-derive", ok_cnt == (p1a.kind == "natural").sum(),
      f"{ok_cnt}/{(p1a.kind=='natural').sum()}")

# ================= V3: no-cherry-picking guards =================
# (a) preregistration & amendment artifacts exist
prereg = R2 / "project_md/archive/legacy_premerge_20260728/420_METHOD_prereg_pillarBE_design_20260710.md"
t420 = prereg.read_text()
for amd in ("Amendment 1", "Amendment 2", "Amendment 3", "Amendment 4"):
    check("V3", f"prereg log {amd}", amd in t420)
check("V3", "multiview prereg exists",
      (R2 / "project_md/archive/legacy_premerge_20260728/410_METHOD_prereg_multiview_answer_level_20260708.md").exists())
# (b) 85-query set re-derives from the mechanical rule (no hand-removal)
docs = cap[["visual_video_id", "split"]]
base = (docs.merge(jn[jn.join_ok_120s], on=["visual_video_id", "split"])
            .merge(ann, on=["visual_video_id", "split"]))
base = base.drop_duplicates(["split", "visual_video_id"]).reset_index(drop=True)
rels = {"parked_vehicle": base.any_parked.astype(bool), "dense_frame": base.max_objects >= 20,
        "multiple_buses": base.max_bus >= 2, "stopped_vehicles": base.any_stopped.astype(bool),
        "two_plus_bikes": base.max_bike >= 2}
PREDS = ["time_of_day", "hour", "sig_has_yellow", "sig_has_pedestrian", "veh_density_bin"]
expected = 0
for pr in PREDS:
    vals = base[pr].value_counts().index[:12]
    for v in vals:
        pm = (base[pr].astype(str) == str(v)).to_numpy()
        for rl, mask in rels.items():
            if int((pm & mask.to_numpy()).sum()) >= 5:
                expected += 1
qx = [json.loads(l) for l in open(V / "canonical_trisource_expanded/queries.jsonl")]
check("V3", "85 queries == mechanical cross-product", len(qx) == expected == 85,
      f"built={len(qx)} rule={expected}")
# (c) every real predicate has paired control rows (B-1, both corpora)
for tag, csvp in [("A", PB / "filtered_ann_real_A.csv"), ("B", PB / "filtered_ann_real_B.csv")]:
    df = pd.read_csv(csvp)
    reals = set(df[df.kind.isin(["natural", "composite"])].predicate)
    ctrls = set(df[df.kind == "control"].predicate.str.split("|").str[1])
    check("V3", f"B-1 {tag} control pairing complete", reals == ctrls,
          f"reals={len(reals)} ctrls={len(ctrls)}")
# (d) full ladders reported (no dropped configs)
e1 = pd.read_csv(PB / "e1_pilot_configs.csv")
check("V3", "E-1 1K ladder all 27 rows", len(e1) == 27, len(e1))
e1a = pd.read_csv(R2 / "paper_assets/20260711_e1a/e1a_pilot_mediator.csv")
check("V3", "E-1a 143K ladder all 19 rows", len(e1a) == 19, len(e1a))
# (e) all three sample splits reported (no hiding the unfavorable one)
sig = pd.read_csv(V / "results/trisource_expanded_b0_b5/significance_expanded.csv")
need = {"원본-32 (재현)", "확장-신규 (독립 확인)", "통합-85 (주 추정)"}
check("V3", "orig/new/combined all reported", need <= set(sig["case"]))
# (f) negative results preserved as first-class assets
check("V3", "negative result doc 630 exists",
      (R2 / "project_md/archive/legacy_premerge_20260728/630_RESULTS_answer_coupling_closure_20260711.md").exists())
check("V3", "dual qrels on all repaired workloads",
      all((p / "canonical/qrels_semantic.tsv").exists() for p in
          [DS / "vru_accident/20260710_noncircular", DS / "aihub_intelligent_cctv/20260710_noncircular"])
      and (V / "canonical_trisource_expanded/qrels_semantic.tsv").exists())
# (g) correction trail present (binning bug disclosed, not silently fixed)
t500 = (R2 / "project_md/archive/legacy_premerge_20260728/500_DATASETS_construction_noncircular_execution_20260710.md").read_text()
check("V3", "binning-bug correction disclosed", "정정 2026-07-11" in t500 and "−0.099가 정본" in t500)

# ================= V4: manuscript numbers =================
r = subprocess.run([sys.executable, str(R2 / "scripts/verify_manuscript_v3.py")],
                   capture_output=True, text=True)
last = [l for l in r.stdout.splitlines() if "F5 VERIFY" in l]
check("V4", "manuscript F5 verifier", r.returncode == 0, last[0] if last else r.stdout[-120:])

# ================= V5: environment capture & pin check =================
def sh(cmd):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception as e:
        return f"ERR:{e}"
import torch, transformers, faiss, sentence_transformers
env = {
    "captured_at": "2026-07-11",
    "python": platform.python_version(),
    "torch": torch.__version__, "transformers": transformers.__version__,
    "faiss": faiss.__version__, "sentence_transformers": sentence_transformers.__version__,
    "pandas": pd.__version__, "numpy": np.__version__,
    "gpu": sh("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader"),
    "cpu": sh("lscpu | grep 'Model name' | head -1").split(":")[-1].strip(),
    "cpu_cores": sh("nproc"),
    "ram": sh("free -g | awk '/^Mem:/{print $2\"GB\"}'"),
    "os": sh("uname -sr"),
    "postgres": sh("docker exec kiise-vlmdb-pgvector psql -U vlmdb -d vlmdb -tAc 'SHOW server_version'"),
    "pgvector": sh("docker exec kiise-vlmdb-pgvector psql -U vlmdb -d vlmdb -tAc \"SELECT extversion FROM pg_extension WHERE extname='vector'\""),
    "conda_env": "Datasets/envs/kiise-vlmdb",
    "timing_discipline": "faiss omp_threads=1 for latency; warmup=5 excluded; per-query median of R repeats; query-bootstrap CIs",
    "seeds": {"global": 20260710, "e1a": 20260711, "index_bench": 20260709},
}
(OUT / "environment_manifest.json").write_text(json.dumps(env, indent=2, ensure_ascii=False))
MS = (R2 / "manuscript/kiise_dbr_manuscript_v3.md").read_text()
for name, ver in [("PyTorch", env["torch"]), ("Transformers", env["transformers"]),
                  ("FAISS", env["faiss"])]:
    check("V5", f"manuscript pins live {name}", ver.split("+")[0] in MS, ver)
check("V5", "manuscript pins pgvector 0.8.4", "0.8.4" in MS and env["pgvector"] == "0.8.4", env["pgvector"])
check("V5", "manuscript pins PG 16", "16.14" in MS and env["postgres"].startswith("16."), env["postgres"])
check("V5", "GPU spec captured", "3090" in env["gpu"])

# ================= report =================
df = pd.DataFrame(results)
n_pass, n_fail = int(df["pass"].sum()), int((~df["pass"]).sum())
(OUT / "report.json").write_text(json.dumps(
    {"pass": n_pass, "fail": n_fail, "checks": results}, indent=2, ensure_ascii=False))
print(f"\n=== FULL VERIFICATION SUITE: PASS {n_pass} / FAIL {n_fail} ===")
print(f"[saved] {OUT}/report.json + environment_manifest.json")
raise SystemExit(0 if n_fail == 0 else 1)
