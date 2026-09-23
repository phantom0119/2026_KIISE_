#!/usr/bin/env python3
"""P0 CPU pilot / F1-F2-F7: canonical fact table -> synchronized worlds.

Design (per v1.1 amendment):
  canonical fact = a 2-hop path  (head) -[r1]- (mid) -[r2]- (tail)
  question       = "which <tail_type> is reached from <head> via <mid>?" style,
                   answer = tail entity (the EDITED slot in the CF world)
  worlds         = ORIGINAL (true tail) and COUNTERFACTUAL (substituted tail
                   of the same type, verified non-adjacent to head/mid)
  representations, generated from the SAME canonical fact in each world:
    A1  natural-language sentences (text evidence)
    A1F flat triples, order-shuffled, connectivity/path order removed
    A2  ordered graph path with explicit connectivity markers
  Every representation carries the SAME fact set (F7 fact-count parity) and
  token counts are recorded for the +-10% budget check.

Counterfactual entity names are namespaced 'SYNTHETIC_CF__<name>' ONLY in the
manifest bookkeeping; the rendered evidence uses a real same-type entity name
so the task stays natural — the synthetic-ness is recorded per fact and the
data card marks the whole CF world as experimental synthetic knowledge.

Domain 1: PrimeKG (CC0). Domain 2: STaRK-Amazon (CC-BY-4.0) handled by the
same schema via --domain amazon (loads product graph + titles).

Outputs (per domain): manifests/canonical_fact_manifest.json,
results/worlds_<domain>.jsonl, results/build_stats_<domain>.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import time
from collections import defaultdict
from pathlib import Path

import pandas as pd

P0 = Path(__file__).resolve().parents[1]
DATA = Path("/hdd2/KIISE_datasociety/Datasets/graphrag_p0_data")
SEED = 20260806
N_FACTS = 200          # >=150 required by F0; 200 gives margin for audit drops
CF_PREFIX = "SYNTHETIC_CF__"

# Relation phrasing for natural-language rendering (PrimeKG)
REL_PHRASE = {
    "drug_protein": "targets the protein",
    "disease_protein": "is associated with the protein",
    "drug_effect": "can cause the side effect",
    "disease_phenotype_positive": "presents the phenotype",
    "protein_protein": "interacts with the protein",
    "indication": "is indicated for",
    "contraindication": "is contraindicated for",
    "off-label use": "is used off-label for",
}


def phrase(rel: str) -> str:
    return REL_PHRASE.get(rel, f"has relation '{rel}' with")


def load_primekg_pairs() -> tuple[pd.DataFrame, dict]:
    """Load the two relation slices used to form 2-hop paths."""
    usecols = ["relation", "x_type", "x_name", "y_type", "y_name"]
    keep_r1, keep_r2 = "drug_protein", "disease_protein"
    parts = []
    for ch in pd.read_csv(DATA / "primekg" / "kg.csv", usecols=usecols, chunksize=2_000_000):
        parts.append(ch[ch.relation.isin([keep_r1, keep_r2])])
    df = pd.concat(parts, ignore_index=True)
    # normalize direction: r1 drug->protein, r2 protein->disease
    r1 = df[(df.relation == keep_r1) & (df.x_type == "drug") & (df.y_type == "gene/protein")]
    r2 = df[(df.relation == keep_r2) & (df.x_type == "gene/protein") & (df.y_type == "disease")]
    return r1, r2


def build_primekg_facts(rng: random.Random) -> tuple[list[dict], dict]:
    r1, r2 = load_primekg_pairs()
    # adjacency for leakage checks
    prot2dis = defaultdict(set)
    for p, d in zip(r2.x_name, r2.y_name):
        prot2dis[p].add(d)
    drug2prot = defaultdict(set)
    for dr, p in zip(r1.x_name, r1.y_name):
        drug2prot[dr].add(p)
    drug2dis = defaultdict(set)
    for dr, ps in drug2prot.items():
        for p in ps:
            drug2dis[dr] |= prot2dis[p]
    all_dis = sorted({d for s in prot2dis.values() for d in s})

    cands = []
    for dr, ps in drug2prot.items():
        for p in sorted(ps):
            for d in sorted(prot2dis.get(p, ())):
                cands.append((dr, p, d))
    rng.shuffle(cands)

    # DEVIATION D1 (2026-08-06): reserve a CF-only tail pool disjoint from every
    # fact's ORIGINAL tail, so no fact's true answer can surface inside another
    # fact's counterfactual world (cross-fact leakage L4 observed in run 1).
    prelim_tails, seen = [], set()
    for dr, p, d in cands:
        if dr not in seen:
            seen.add(dr)
            prelim_tails.append(d)
        if len(prelim_tails) >= N_FACTS * 3:
            break
    # D1b: substring-safe exclusion — disease names are compositional
    # ("anemia" is inside "aplastic anemia"), so a CF tail must neither contain
    # nor be contained by any original tail after normalization.
    def _n(s: str) -> str:
        import re as _re
        return _re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()

    reserved_norm = {_n(d) for d in prelim_tails}
    cf_pool = [d for d in all_dis
               if not any(r in _n(d) or _n(d) in r for r in reserved_norm)]

    facts, seen_heads = [], set()
    for dr, p, d in cands:
        if len(facts) >= N_FACTS:
            break
        if dr in seen_heads:          # one fact per head entity -> independent clusters
            continue
        # counterfactual tail: same type, NOT reachable from head or mid,
        # and never any fact's original answer (D1)
        forbidden = drug2dis[dr] | prot2dis[p]
        for _ in range(50):
            cf = rng.choice(cf_pool)
            if cf not in forbidden:
                break
        else:
            continue
        seen_heads.add(dr)
        facts.append({
            "fact_id": hashlib.sha256(f"{dr}|{p}|{d}".encode()).hexdigest()[:16],
            "domain": "primekg_clinical",
            "head": dr, "head_type": "drug",
            "mid": p, "mid_type": "gene/protein",
            "tail_original": d, "tail_counterfactual": cf, "tail_type": "disease",
            "r1": "drug_protein", "r2": "disease_protein",
            "cf_namespace": CF_PREFIX + cf,
            "question": f"Which disease is associated with the protein that the drug {dr} targets?",
        })
    stats = {"n_candidate_paths": len(cands), "n_drugs": len(drug2prot),
             "n_proteins": len(prot2dis), "n_diseases": len(all_dis)}
    return facts, stats


def build_amazon_facts(rng: random.Random) -> tuple[list[dict], dict]:
    """STaRK-Amazon: product -[has_brand]- brand -[also_used_by]- product.
    Loaded from the lightweight edge tensors + node_info (streamed via torch)."""
    import pickle
    import zipfile
    import torch
    zpath = DATA / "stark_amazon" / "processed.zip"
    with zipfile.ZipFile(zpath) as z:
        with z.open("processed/edge_index.pt") as f:
            edge_index = torch.load(f, map_location="cpu", weights_only=False)
        with z.open("processed/edge_types.pt") as f:
            edge_types = torch.load(f, map_location="cpu", weights_only=False)
        with z.open("processed/edge_type_dict.pkl") as f:
            edge_type_dict = pickle.load(f)
    inv = {v: k for k, v in edge_type_dict.items()} if isinstance(
        list(edge_type_dict.keys())[0], int) else edge_type_dict
    stats = {"n_edges": int(edge_index.shape[1]), "edge_types": str(edge_type_dict)[:300]}
    return [], stats            # node_info (5.4GB) deferred — see report


def render(fact: dict, world: str) -> dict:
    """Produce A1 / A1F / A2 renderings for one fact in one world."""
    tail = fact["tail_original"] if world == "original" else fact["tail_counterfactual"]
    h, m, t = fact["head"], fact["mid"], tail
    t1, t2 = fact["r1"], fact["r2"]
    triples = [(h, t1, m), (m, t2, t)]
    # DEVIATION D2 (2026-08-06): lexically-matched renderings. All three arms use
    # the SAME entity strings and the SAME relation wording; they differ only in
    # (i) notation (prose vs itemized) and (ii) whether path order/connectivity is
    # expressed. Run 1 used compressed symbolic forms, giving a 1.5x token ratio
    # that would have confounded structure with evidence length (S3 0/200).
    clause1 = f"the drug {h} {phrase(t1)} {m}"
    clause2 = f"the protein {m} {phrase(t2)} {t}"
    # D2b: minimal structural markers so the arms differ by ~1 token of markup
    # each; residual token deltas are recorded and carried as a covariate.
    a1 = f"{clause1.capitalize()}. {clause2.capitalize()}."
    items = [f"{clause1};", f"{clause2};"]                 # A1F: unordered set
    random.Random(SEED + int(fact["fact_id"][:8], 16) % 1000).shuffle(items)
    a1f = "Unordered facts: " + " ".join(items)
    a2 = f"Connected path: {clause1} -> {clause2}."
    return {"world": world, "answer": tail,
            "A1_text": a1, "A1F_flat_triples": a1f, "A2_graph_path": a2,
            "fact_set": sorted(triples),
            "tokens": {k: len(v.split()) for k, v in
                       (("A1", a1), ("A1F", a1f), ("A2", a2))}}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domain", choices=["primekg", "amazon"], default="primekg")
    args = ap.parse_args()
    t0 = time.time()
    rng = random.Random(SEED)
    if args.domain == "primekg":
        facts, dstats = build_primekg_facts(rng)
    else:
        facts, dstats = build_amazon_facts(rng)

    rows = []
    for f in facts:
        rec = dict(f)
        rec["renderings"] = {w: render(f, w) for w in ("original", "counterfactual")}
        rows.append(rec)

    outp = P0 / "results" / f"worlds_{args.domain}.jsonl"
    with open(outp, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    tok = defaultdict(list)
    for r in rows:
        for w, ren in r["renderings"].items():
            for k, v in ren["tokens"].items():
                tok[k].append(v)
    stats = {"domain": args.domain, "seed": SEED, "n_facts": len(rows),
             "source_stats": dstats,
             "token_means": {k: round(sum(v) / len(v), 1) for k, v in tok.items()} if tok else {},
             "fact_count_parity": all(
                 len(r["renderings"]["original"]["fact_set"]) ==
                 len(r["renderings"]["counterfactual"]["fact_set"]) == 2 for r in rows),
             "wall_s": round(time.time() - t0, 1)}
    (P0 / "results" / f"build_stats_{args.domain}.json").write_text(json.dumps(stats, indent=2))
    (P0 / "manifests" / f"canonical_fact_manifest_{args.domain}.json").write_text(json.dumps(
        {"seed": SEED, "n_facts": len(rows), "schema": list(facts[0].keys()) if facts else [],
         "fact_ids": [r["fact_id"] for r in rows],
         "cf_namespace_prefix": CF_PREFIX,
         "note": "Counterfactual tails are EXPERIMENTAL SYNTHETIC knowledge, not medical fact."},
        indent=2))
    print(json.dumps(stats, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
