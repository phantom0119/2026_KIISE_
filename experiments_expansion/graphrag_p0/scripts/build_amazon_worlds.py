#!/usr/bin/env python3
"""P0 CPU pilot / domain 2: STaRK-Amazon synchronized worlds.

Canonical fact (2-hop): product P -[has_brand]- brand B -[brand_of]- product Q
  question : "Which other product is made by the brand of <P>?"   answer = Q
  worlds   : ORIGINAL (true Q) / COUNTERFACTUAL (product of a disjoint reserved
             pool, verified not co-branded and name-disjoint from any original)
Unlike PrimeKG, the entity strings here are REAL product titles, so this domain
is the stronger test of the leakage auditor (long, compositional, overlapping
names). Memory: node_info.pkl is ~5.4 GB on disk / ~21.7 GB resident; it is
loaded once, the needed subset is extracted, then released.
"""
from __future__ import annotations

import gc
import hashlib
import json
import pickle
import random
import re
import time
import zipfile
from collections import defaultdict
from pathlib import Path

import torch

P0 = Path(__file__).resolve().parents[1]
ZIP = Path("/hdd2/KIISE_datasociety/Datasets/graphrag_p0_data/stark_amazon/processed.zip")
SEED = 20260806
N_FACTS = 200
MAX_TITLE_WORDS = 12


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def short_title(t: str) -> str:
    w = re.sub(r"\s+", " ", str(t)).strip().split()
    return " ".join(w[:MAX_TITLE_WORDS])


def main() -> int:
    t0 = time.time()
    rng = random.Random(SEED)
    CACHE = "processed/cache/brand-category-color/"   # base skb has no brand edges
    with zipfile.ZipFile(ZIP) as z:
        with z.open(CACHE + "edge_index.pt") as f:
            ei = torch.load(f, map_location="cpu", weights_only=False)
        with z.open(CACHE + "edge_types.pt") as f:
            et = torch.load(f, map_location="cpu", weights_only=False)
        with z.open(CACHE + "edge_type_dict.pkl") as f:
            etd = pickle.load(f)
    id2name = etd if isinstance(next(iter(etd)), int) else {v: k for k, v in etd.items()}
    brand_ids = [i for i, n in id2name.items() if str(n) == "has_brand"]
    assert brand_ids, f"has_brand edge type not found in {etd}"
    src, dst = ei[0].numpy(), ei[1].numpy()
    mask = torch.isin(et, torch.tensor(brand_ids)).numpy()
    bs, bd = src[mask], dst[mask]

    prod2brand, brand2prod = {}, defaultdict(list)
    for a, b in zip(bs, bd):
        prod2brand[int(a)] = int(b)
        brand2prod[int(b)].append(int(a))

    cands = []
    for p, b in prod2brand.items():
        peers = [q for q in brand2prod[b] if q != p]
        if peers:
            cands.append((p, b, rng.choice(peers)))
    rng.shuffle(cands)
    cands = cands[: N_FACTS * 6]

    reserved = {q for _, _, q in cands[: N_FACTS * 3]}
    cf_pool_src = [q for _, _, q in cands[N_FACTS * 3:]]
    need = set()
    for p, b, q in cands[: N_FACTS * 3]:
        need |= {p, b, q}
    need |= set(cf_pool_src)

    with zipfile.ZipFile(ZIP) as z, z.open(CACHE + "node_info.pkl") as f:
        node_info = pickle.load(f)
    sub = {}
    for i in need:
        v = node_info.get(i, {})
        sub[i] = {"title": short_title(v.get("title", "")) or f"item {i}",
                  "brand": str(v.get("brand", "") or "")}
    del node_info
    gc.collect()

    cf_pool = [q for q in cf_pool_src if sub.get(q, {}).get("title")]
    reserved_norm = {norm(sub[q]["title"]) for q in reserved if sub.get(q)}
    cf_pool = [q for q in cf_pool
               if not any(r and (r in norm(sub[q]["title"]) or norm(sub[q]["title"]) in r)
                          for r in reserved_norm)]

    facts, seen = [], set()
    for p, b, q in cands:
        if len(facts) >= N_FACTS or not cf_pool:
            break
        if p in seen or p not in sub or q not in sub or b not in sub:
            continue
        # DEVIATION D3 (2026-08-06): real product titles truncate to identical
        # strings for near-duplicate variants of the same brand, which makes the
        # head itself leak the original answer (L1/L5 hits in run 1). Reject any
        # fact whose head/answer titles are mutually containing after norm.
        nh, nq = norm(sub[p]["title"]), norm(sub[q]["title"])
        if not nh or not nq or nh in nq or nq in nh:
            continue
        brand_name = sub[b]["title"] or sub[p]["brand"] or f"brand {b}"
        co = set(brand2prod[b])
        cf = next((c for c in (rng.choice(cf_pool) for _ in range(50)) if c not in co), None)
        if cf is None:
            continue
        seen.add(p)
        facts.append({
            "fact_id": hashlib.sha256(f"{p}|{b}|{q}".encode()).hexdigest()[:16],
            "domain": "stark_amazon_ecommerce",
            "head": sub[p]["title"], "head_type": "product",
            "mid": brand_name, "mid_type": "brand",
            "tail_original": sub[q]["title"],
            "tail_counterfactual": sub[cf]["title"], "tail_type": "product",
            "r1": "has_brand", "r2": "brand_of",
            "cf_namespace": "SYNTHETIC_CF__" + sub[cf]["title"],
            "question": f"Which other product is made by the brand of '{sub[p]['title']}'?",
        })

    def render(fact, world):
        tail = fact["tail_original"] if world == "original" else fact["tail_counterfactual"]
        h, m, t = fact["head"], fact["mid"], tail
        c1 = f"the product '{h}' is made by the brand {m}"
        c2 = f"the brand {m} also makes the product '{t}'"
        a1 = f"{c1.capitalize()}. {c2.capitalize()}."
        items = [f"{c1};", f"{c2};"]
        random.Random(SEED + int(fact["fact_id"][:8], 16) % 1000).shuffle(items)
        return {"world": world, "answer": tail,
                "A1_text": a1,
                "A1F_flat_triples": "Unordered facts: " + " ".join(items),
                "A2_graph_path": f"Connected path: {c1} -> {c2}.",
                "fact_set": sorted([(h, fact["r1"], m), (m, fact["r2"], t)]),
                "tokens": {}}

    rows = []
    for f in facts:
        r = dict(f)
        r["renderings"] = {w: render(f, w) for w in ("original", "counterfactual")}
        for w in r["renderings"]:
            ren = r["renderings"][w]
            ren["tokens"] = {k: len(ren[v].split()) for k, v in
                             (("A1", "A1_text"), ("A1F", "A1F_flat_triples"),
                              ("A2", "A2_graph_path"))}
        rows.append(r)

    with open(P0 / "results" / "worlds_amazon.jsonl", "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    toks = defaultdict(list)
    for r in rows:
        for ren in r["renderings"].values():
            for k, v in ren["tokens"].items():
                toks[k].append(v)
    stats = {"domain": "stark_amazon", "seed": SEED, "n_facts": len(rows),
             "n_candidate_paths": len(cands), "cf_pool_size": len(cf_pool),
             "token_means": {k: round(sum(v) / len(v), 1) for k, v in toks.items()},
             "peak_note": "node_info.pkl load ~21.7GB RSS, released after subset extraction",
             "wall_s": round(time.time() - t0, 1)}
    (P0 / "results" / "build_stats_amazon.json").write_text(json.dumps(stats, indent=2))
    (P0 / "manifests" / "canonical_fact_manifest_amazon.json").write_text(json.dumps(
        {"seed": SEED, "n_facts": len(rows), "fact_ids": [r["fact_id"] for r in rows],
         "note": "Counterfactual tails are EXPERIMENTAL SYNTHETIC associations."}, indent=2))
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
