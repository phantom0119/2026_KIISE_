#!/usr/bin/env python3
"""Verify Table 4 manuscript numbers against data/ copies in table4_dir."""
import csv, math
from pathlib import Path

D = Path("/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/table4_dir/data")

# manuscript numbers (0_paper_script.md L206-219, read 2026-07-23)
MS = {
    "caption":              dict(strict=0.063, sem=0.181, p50=1.15, mb=24.6),
    "representative_frame": dict(strict=0.063, sem=0.186, p50=1.21, mb=24.6, d=+0.005, lo=-0.075, hi=+0.079),
    "joint_image_caption":  dict(strict=0.079, sem=0.218, p50=1.24, mb=24.6, d=+0.037, lo=-0.005, hi=+0.074),
    "multi_frame":          dict(strict=0.101, sem=0.352, p50=3.65, mb=68.4, d=+0.171, lo=+0.018, hi=+0.316),
    "dual":                 dict(strict=0.089, sem=0.293, p50=4.96, mb=93.0, d=+0.112, lo=-0.004, hi=+0.228),
}
BODY = dict(multi_p_cluster=0.028, multi_q_bh=0.112, storage_family=4, queries=85)

rows = {}
with (D / "configuration_summary.csv").open() as f:
    for r in csv.DictReader(f):
        rows[(r["config"], r["scoring"])] = r

boot = {}
with (D / "paired_bootstrap_comparisons.csv").open() as f:
    for r in csv.DictReader(f):
        if r["family"] == "storage":
            boot[(r["candidate"], r["scoring"])] = r

def r3(x): return round(float(x), 3)
def r2(x): return round(float(x), 2)
def r1(x): return round(float(x), 1)

results = []
def chk(label, printed, raw_rounded, raw):
    ok = math.isclose(printed, raw_rounded, abs_tol=1e-9)
    results.append((label, printed, raw, "PASS" if ok else "FAIL"))

for name, m in MS.items():
    key = f"{name}__B2_vector__flat"
    s, q = rows[(key, "strict")], rows[(key, "semantic")]
    chk(f"{name} strict nDCG",  m["strict"], r3(s["ndcg_at_10"]), float(s["ndcg_at_10"]))
    chk(f"{name} semantic nDCG", m["sem"],   r3(q["ndcg_at_10"]), float(q["ndcg_at_10"]))
    chk(f"{name} p50 ms",        m["p50"],   r2(q["latency_p50_ms"]), float(q["latency_p50_ms"]))
    chk(f"{name} payload MB",    m["mb"],    r1(q["vector_payload_mb"]), float(q["vector_payload_mb"]))
    assert int(q["queries"]) == BODY["queries"], "query count mismatch"
    if "d" in m:
        b = boot[(key, "semantic")]
        chk(f"{name} Δ semantic",   m["d"],  r3(b["mean_delta"]),    float(b["mean_delta"]))
        chk(f"{name} cluster CI lo", m["lo"], r3(b["cluster_ci_lo"]), float(b["cluster_ci_lo"]))
        chk(f"{name} cluster CI hi", m["hi"], r3(b["cluster_ci_hi"]), float(b["cluster_ci_hi"]))

# body-text claims tied to Table 4
bm = boot[("multi_frame__B2_vector__flat", "semantic")]
chk("multi_frame p_cluster=0.028", BODY["multi_p_cluster"], r3(bm["p_cluster"]), float(bm["p_cluster"]))
chk("multi_frame BH q=0.112",      BODY["multi_q_bh"],      r3(bm["q_cluster_bh"]), float(bm["q_cluster_bh"]))
pq = float(bm["p_query"])
results.append(("multi_frame p_query<0.0001", "<0.0001", pq, "PASS" if pq < 0.0001 else "FAIL"))
n_storage_sem = sum(1 for (c, sc) in boot if sc == "semantic")
results.append(("BH family size = 4", 4, n_storage_sem, "PASS" if n_storage_sem == 4 else "FAIL"))
ratio_mb = float(rows[("multi_frame__B2_vector__flat", "semantic")]["vector_payload_mb"]) / \
           float(rows[("caption__B2_vector__flat", "semantic")]["vector_payload_mb"])
results.append(("저장량 '약 2.8배'", 2.8, round(ratio_mb, 3), "PASS" if abs(ratio_mb - 2.8) < 0.05 else "FAIL"))
ratio_p50 = float(rows[("multi_frame__B2_vector__flat", "semantic")]["latency_p50_ms"]) / \
            float(rows[("caption__B2_vector__flat", "semantic")]["latency_p50_ms"])
results.append(("p50 '3배 이상'", ">=3", round(ratio_p50, 3), "PASS" if ratio_p50 >= 3 else "FAIL"))

w = max(len(r[0]) for r in results)
npass = 0
for label, printed, raw, verdict in results:
    npass += verdict == "PASS"
    print(f"{label:<{w}} | 원고 {printed!s:>8} | 원천 {raw!s:>22} | {verdict}")
print(f"\n{npass}/{len(results)} PASS")
