#!/usr/bin/env python3
"""P0 CPU pilot / F2 + F7: evidence-delivery and fairness audit.

F2a oracle arms      : gold-support inclusion must be 100% by construction
                       (verified, not assumed: the answer-bearing triple must be
                        present in every oracle rendering of the active world)
F2b retrieved arms   : gold-support recall@k of a lexical retriever run over a
                       shared corpus of rendered evidence + distractors, measured
                       SEPARATELY for text-form (A1) and graph-form (A2) corpora
                       — CPU-only proxy for the retrieval-success factor that
                       H2 must not confound with representation.
F7  fairness         : fact-count parity (must be exact) and token-delta profile
                       (recorded; see report for the tolerance finding).
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

P0 = Path(__file__).resolve().parents[1]
KS = (1, 3, 5, 10)


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def recall_at_k(corpus: list[str], queries: list[str], gold_idx: list[int]) -> dict:
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True).fit(corpus + queries)
    C, Q = vec.transform(corpus), vec.transform(queries)
    sims = (Q @ C.T).toarray()
    order = np.argsort(-sims, axis=1)
    out = {}
    for k in KS:
        hits = [gold_idx[i] in order[i, :k] for i in range(len(queries))]
        out[f"recall@{k}"] = round(float(np.mean(hits)), 4)
    return out


def main() -> int:
    import sys
    domain = sys.argv[1] if len(sys.argv) > 1 else "primekg"
    t0 = time.time()
    rows = [json.loads(l) for l in open(P0 / "results" / f"worlds_{domain}.jsonl")]
    res = {"domain": domain, "n_facts": len(rows), "gates": {}}

    # ---- F2a: oracle gold-support inclusion (verified per fact/world/arm) ----
    ok = 0
    for r in rows:
        for w, ren in r["renderings"].items():
            ans = norm(ren["answer"])
            mid = norm(r["mid"])
            present = all(ans in norm(ren[a]) and mid in norm(ren[a])
                          for a in ("A1_text", "A1F_flat_triples", "A2_graph_path"))
            ok += present
    total = len(rows) * 2
    res["gates"]["F2a_oracle_gold_support_rate"] = round(ok / total, 4)
    res["gates"]["F2a_pass"] = (ok == total)

    # ---- F2b: retrieved-arm gold-support recall (text corpus vs graph corpus) ----
    # Shared corpus per world: every fact's rendering + all other facts act as
    # distractors (199 distractors per query) — a conservative small-corpus proxy.
    for world in ("original", "counterfactual"):
        for arm, key in (("text_A1", "A1_text"), ("graph_A2", "A2_graph_path")):
            corpus = [r["renderings"][world][key] for r in rows]
            queries = [r["question"] for r in rows]
            gold = list(range(len(rows)))
            res.setdefault("F2b_retrieval", {})[f"{world}|{arm}"] = recall_at_k(
                corpus, queries, gold)

    # ---- F7: fairness ----
    fp = all(len(r["renderings"]["original"]["fact_set"]) ==
             len(r["renderings"]["counterfactual"]["fact_set"]) == 2 for r in rows)
    tk = pd.DataFrame([{**ren["tokens"], "world": w, "fact_id": r["fact_id"]}
                       for r in rows for w, ren in r["renderings"].items()])
    spread = (tk[["A1", "A1F", "A2"]].max(axis=1) - tk[["A1", "A1F", "A2"]].min(axis=1))
    mean = tk[["A1", "A1F", "A2"]].mean(axis=1)
    rel = (spread / mean)
    res["gates"]["F7_fact_count_parity"] = bool(fp)
    res["gates"]["F7_token_rel_spread"] = {
        "median": round(float(rel.median()), 4), "max": round(float(rel.max()), 4),
        "frac_within_10pct": round(float((rel <= 0.10).mean()), 4),
        "means": {c: round(float(tk[c].mean()), 2) for c in ("A1", "A1F", "A2")},
    }
    res["gates"]["F7_pass_strict_10pct"] = bool(fp and (rel <= 0.10).all())
    res["wall_s"] = round(time.time() - t0, 1)

    pd.DataFrame([{"world_arm": k, **v} for k, v in res["F2b_retrieval"].items()]).to_csv(
        P0 / "results" / f"coverage_summary_{domain}.csv", index=False)
    (P0 / "results" / f"coverage_report_{domain}.json").write_text(json.dumps(res, indent=2))
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
