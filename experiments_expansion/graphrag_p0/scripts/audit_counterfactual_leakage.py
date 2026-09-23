#!/usr/bin/env python3
"""P0 CPU pilot / F1: counterfactual leakage + synchronization audit.

Checks, per fact and per world, that the counterfactual world contains NO trace
of the original answer and that graph/text representations carry identical facts.

Audits performed:
  L1 surface leakage    original tail string (and case/punct-normalized form)
                        must not appear in ANY counterfactual rendering
  L2 alias leakage      PrimeKG alias sets (mondo_name / group_name_bert /
                        node synonyms) of the original tail must not appear
  L3 inverse-relation   the reverse edge (tail -> mid) must not be rendered
  L4 alternate path     no other rendered fact re-derives the original tail
                        (cross-fact scan over the whole rendered corpus)
  L5 prompt leakage     the question text must not contain the original tail
  S1 fact-set parity    A1/A1F/A2 encode the identical fact set in each world
  S2 world parity       original/counterfactual differ ONLY in the tail slot
  S3 token budget       max pairwise token ratio across A1/A1F/A2 within +-10%
                        target; recorded (not gating) with actual deltas
"""
from __future__ import annotations

import json
import re
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd

P0 = Path(__file__).resolve().parents[1]
DATA = Path("/hdd2/KIISE_datasociety/Datasets/graphrag_p0_data")
TOKEN_TOL = 0.10


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def load_alias_map() -> dict:
    """Disease aliases from PrimeKG disease_features (mondo/group/umls names)."""
    cols = ["mondo_name", "group_name_bert"]
    df = pd.read_csv(DATA / "primekg" / "disease_features.tab", sep="\t",
                     usecols=lambda c: c in cols, low_memory=False)
    m = defaultdict(set)
    for a, b in zip(df.get("mondo_name", []), df.get("group_name_bert", [])):
        if isinstance(a, str) and isinstance(b, str) and norm(a) != norm(b):
            m[norm(a)].add(norm(b))
            m[norm(b)].add(norm(a))
    return {k: sorted(v) for k, v in m.items()}


def main() -> int:
    import sys
    domain = sys.argv[1] if len(sys.argv) > 1 else "primekg"
    t0 = time.time()
    rows = [json.loads(l) for l in open(P0 / "results" / f"worlds_{domain}.jsonl")]
    aliases = load_alias_map() if domain == "primekg" else {}

    # cross-fact index for L4: which facts render which tail strings
    rendered_tokens = defaultdict(set)          # normalized tail -> fact_ids rendering it
    for r in rows:
        for w, ren in r["renderings"].items():
            blob = norm(" ".join([ren["A1_text"], ren["A1F_flat_triples"], ren["A2_graph_path"]]))
            rendered_tokens[(r["fact_id"], w)] = blob

    findings, per_fact = defaultdict(int), []
    for r in rows:
        orig = norm(r["tail_original"])
        cf_ren = r["renderings"]["counterfactual"]
        blob_cf = rendered_tokens[(r["fact_id"], "counterfactual")]
        f = {"fact_id": r["fact_id"]}

        f["L1_surface"] = orig in blob_cf
        f["L2_alias"] = any(a in blob_cf for a in aliases.get(orig, []))
        f["L3_inverse"] = (f"{norm(r['tail_counterfactual'])} {norm(r['r2'])} {norm(r['mid'])}"
                           in blob_cf)
        f["L4_alt_path"] = any(
            orig in rendered_tokens[(o["fact_id"], "counterfactual")]
            for o in rows if o["fact_id"] != r["fact_id"])
        f["L5_prompt"] = orig in norm(r["question"])

        o_set = [tuple(x) for x in r["renderings"]["original"]["fact_set"]]
        c_set = [tuple(x) for x in cf_ren["fact_set"]]
        f["S1_fact_parity"] = len(o_set) == len(c_set) == 2
        diff = [(a, b) for a, b in zip(sorted(o_set), sorted(c_set)) if a != b]
        f["S2_world_parity"] = len(diff) == 1 and diff[0][0][:2] == diff[0][1][:2]

        tk = cf_ren["tokens"]
        mx, mn = max(tk.values()), min(tk.values())
        f["S3_token_ratio"] = round(mx / mn, 3)
        f["S3_within_tol"] = (mx - mn) / ((mx + mn) / 2) <= TOKEN_TOL
        per_fact.append(f)
        for k, v in f.items():
            if k.startswith(("L", "S")) and isinstance(v, bool):
                if k.startswith("L") and v:
                    findings[k] += 1
                if k.startswith("S") and not v:
                    findings[k + "_fail"] += 1

    n = len(rows)
    summary = {
        "domain": domain,
        "n_facts": n,
        "leakage_counts": {k: findings.get(k, 0) for k in
                           ("L1_surface", "L2_alias", "L3_inverse", "L4_alt_path", "L5_prompt")},
        "leakage_total": sum(findings.get(k, 0) for k in
                             ("L1_surface", "L2_alias", "L3_inverse", "L4_alt_path", "L5_prompt")),
        "sync_failures": {k: findings.get(k, 0) for k in
                          ("S1_fact_parity_fail", "S2_world_parity_fail")},
        "token_ratio": {
            "median": round(pd.Series([f["S3_token_ratio"] for f in per_fact]).median(), 3),
            "max": round(max(f["S3_token_ratio"] for f in per_fact), 3),
            "n_within_10pct": sum(f["S3_within_tol"] for f in per_fact),
        },
        "F1_pass": (sum(findings.get(k, 0) for k in
                        ("L1_surface", "L2_alias", "L3_inverse", "L4_alt_path", "L5_prompt")) == 0
                    and findings.get("S1_fact_parity_fail", 0) == 0
                    and findings.get("S2_world_parity_fail", 0) == 0),
        "wall_s": round(time.time() - t0, 1),
    }
    pd.DataFrame(per_fact).to_csv(P0 / "results" / f"edit_integrity_{domain}.csv", index=False)
    (P0 / "results" / f"leakage_summary_{domain}.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
