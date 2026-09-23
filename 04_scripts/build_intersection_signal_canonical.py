#!/usr/bin/env python3
"""Pillar C1->C4 (CPU): canonical schema + NON-CIRCULAR workload for 522 sensor data.

Consumes sensor_facets.parquet (from build_intersection_signal_sensors.py) and emits
the canonical clip/metadata/query/qrels skeleton with an ENFORCED separation:

  metadata_filter keys  = P-series (EXOGENOUS predicates: time_of_day, hour,
                          intersection_id, signal-phase presence)  ->  the FILTER
  qrel relevance        = R-series (SCENE CONTENT: has_bus, has_truck, has_uturn,
                          has_bicycle_ped, ...)                    ->  the TARGET

Because the two key sets are disjoint AND the chosen (P,R) pairs are low-coupling
(Cramér's V measured in T2), applying the metadata filter gives NO structural
advantage for finding the semantic target. This BREAKS F1 ("B4 >= B2 guaranteed")
and F4 ("query == relevance facet") by construction. The A6 audit asserts it.

Documents (captions) and embeddings are Phase-2 (GPU) and are intentionally NOT
built here; this establishes the auditable non-circular backbone on CPU.

Relevance here is the PROGRAMMATIC (Pillar C3) track: gold = sensor aggregate,
verifiable without a model. A frame/caption VLM must later EXPRESS these features
for retrieval to succeed — that is the Phase-2/3 validation, not the gold source.

Run:
  Datasets/envs/kiise-vlmdb/bin/python \
    2026_KIISE/04_scripts/build_intersection_signal_canonical.py \
    [--facets <sensor_facets.parquet>] [--out <dir>] [--max-queries-per-value 12]
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DS = PROJECT_ROOT / "Datasets"
DEFAULT_VER = DS / "processed" / "aihub_522_intersection" / "20260710"
DATASET_ID = "aihub_522_intersection"

# ---- facet roles (drives the disjoint filter/relevance separation) ----
P_PREDICATES = ["intersection_id", "time_of_day", "hour",
                "sig_has_yellow", "sig_has_pedestrian"]          # exogenous -> FILTER
CONTEXT = ["date", "weekday", "n_vehicles", "n_pedestrians",
           "veh_density_bin", "ped_density_bin", "sig_phase_set", "n_lanes_used"]

# SPARSE, discriminative relevance definitions (scene events), measured density in
# the T2 probe. Binary base-rate features (has_bus ~0.68) gave degenerate ~10%
# positive sets; these count/conjunction defs give ~2.5-5.5% and stay independent
# of the exogenous predicates. Each is a boolean mask over the facet frame.
def RELEVANCE_DEFS(df):
    b = lambda c: df[c].astype(bool)
    return {
        "heavy_traffic":       (df["n_vehicles"] >= 150),                          # ~2.6%
        "uturn_with_peds":     b("has_uturn_veh") & (df["n_pedestrians"] >= 15),   # ~3.0%
        "many_bicycles":       (df["n_bicycle_ped"] >= 5),                          # ~4.2%
        "crowd_with_bicycle":  (df["n_pedestrians"] >= 20) & b("has_bicycle_ped"), # ~5.6%
    }
R_NL = {
    "heavy_traffic": "heavy vehicle traffic (a large number of vehicles at once)",
    "uturn_with_peds": "a vehicle making a U-turn while pedestrians are present",
    "many_bicycles": "several bicycles among the pedestrians",
    "crowd_with_bicycle": "a crowd of pedestrians that includes a cyclist",
}

# Non-circular (predicate, relevance) specs. Low-coupling pairs = headline; the
# intersection_id pair is the T3 coupling CONTRAST arm (kept, not dropped).
PAIR_SPECS = [
    ("time_of_day", "heavy_traffic", "low"),
    ("hour", "crowd_with_bicycle", "low"),
    ("sig_has_yellow", "uturn_with_peds", "low"),
    ("sig_has_pedestrian", "many_bicycles", "low"),
    ("intersection_id", "heavy_traffic", "contrast"),   # V~0.6 geometry coupling
]
P_NL = {
    "time_of_day": "during the {v}",
    "hour": "around {v}:00",
    "intersection_id": "at intersection {v}",
    "sig_has_yellow": ("when a yellow signal phase occurs", "when no yellow signal phase occurs"),
    "sig_has_pedestrian": ("when a pedestrian signal phase occurs", "when no pedestrian signal phase occurs"),
}


def cramers_v(a: pd.Series, b: pd.Series) -> float:
    t = pd.crosstab(a, b).to_numpy(float)
    if min(t.shape) < 2:
        return float("nan")
    r = t.sum(1, keepdims=True); c = t.sum(0, keepdims=True); e = r @ c / t.sum()
    chi = np.where(e > 0, (t - e) ** 2 / e, 0.0).sum()
    n = t.sum(); rr, kk = t.shape
    ph = max(0.0, chi / n - (kk - 1) * (rr - 1) / (n - 1))
    rc = rr - (rr - 1) ** 2 / (n - 1); kc = kk - (kk - 1) ** 2 / (n - 1)
    d = min(kc - 1, rc - 1)
    return float(np.sqrt(ph / d)) if d > 0 else float("nan")


def build_metadata(df: pd.DataFrame) -> pd.DataFrame:
    """Long-form facets. Predicates + context come from columns; relevance defs are
    the derived sparse scene-event booleans (role='relevance')."""
    rows = []
    rel_masks = RELEVANCE_DEFS(df)
    df = df.copy()
    for name, mask in rel_masks.items():
        df[f"rel__{name}"] = mask.astype(bool)
    role_of = {**{f: "predicate" for f in P_PREDICATES},
               **{f"rel__{n}": "relevance" for n in rel_masks}}
    facets = set(P_PREDICATES) | set(CONTEXT) | {f"rel__{n}" for n in rel_masks}
    for rec in df.to_dict("records"):
        for f in facets:
            if f not in rec:
                continue
            rows.append({
                "clip_id": rec["clip_id"], "dataset_id": DATASET_ID,
                "facet_name": f, "facet_value": str(rec[f]),
                "facet_role": role_of.get(f, "context"),
                "facet_source": "sensor_csv", "confidence": 1.0,
            })
    return pd.DataFrame(rows)


def build_queries_qrels(df: pd.DataFrame, max_per_value: int, min_pos: int, max_pos: int):
    rel_masks = {n: m.to_numpy() for n, m in RELEVANCE_DEFS(df).items()}
    idx = df["clip_id"].to_numpy()
    queries, qrels = [], []

    def add(qid, qtext, mfilter, rel_name, positives, coupling, pair):
        if not (min_pos <= len(positives) <= max_pos):
            return False
        queries.append({
            "query_id": qid, "dataset_id": DATASET_ID, "query_text": qtext,
            "task": "sensor_filtered_scene_retrieval",
            "metadata_filter": mfilter,                       # keys ⊂ P_PREDICATES
            "qrel_filter": {"relevance_def": rel_name},       # NOT a predicate key (disjoint!)
            "coupling": coupling, "pair": pair, "positive_count": len(positives),
        })
        for cid in positives:
            qrels.append({"query_id": qid, "target_id": cid, "target_type": "clip", "relevance": 3})
        return True

    qn = 0
    for pred, rel, coupling in PAIR_SPECS:
        if pred not in df.columns or rel not in rel_masks:
            continue
        rel_mask = rel_masks[rel]
        pvals = df[pred].value_counts()
        cand_values = list(pvals.index[:max_per_value]) if len(pvals) > max_per_value else list(pvals.index)
        for v in cand_values:
            pred_mask = (df[pred].astype(str) == str(v)).to_numpy()
            positives = idx[pred_mask & rel_mask].tolist()
            if isinstance(P_NL.get(pred), tuple):
                cond = P_NL[pred][0] if str(v) == "True" else P_NL[pred][1]
            else:
                cond = P_NL.get(pred, "with {v}").format(v=v)
            qtext = f"Find clips showing {R_NL[rel]} {cond}."
            qn += 1
            add(f"522:{coupling}:{qn:04d}", qtext, {pred: str(v)}, rel, positives, coupling, f"{pred}|{rel}")
    return queries, qrels


def a6_audit(queries, df, out: Path) -> dict:
    """Assert non-circularity structurally; report predicate-relevance independence."""
    rel_masks = {n: m.to_numpy() for n, m in RELEVANCE_DEFS(df).items()}
    report = {"n_queries": len(queries), "assertions": {}, "coupling_summary": {}, "independence": {}}
    # A6-1: metadata_filter keys are predicates, never a relevance def
    bad = [q["query_id"] for q in queries
           if (set(q["metadata_filter"].keys()) & set(rel_masks.keys()))
           or (q["qrel_filter"]["relevance_def"] in q["metadata_filter"])]
    report["assertions"]["filter_relevance_key_disjoint"] = {"pass": len(bad) == 0, "violations": bad[:10]}
    # A6-2: all filter keys are P-predicates; all relevance are named scene defs
    fkeys_all = set().union(*[set(q["metadata_filter"].keys()) for q in queries]) if queries else set()
    rkeys_all = {q["qrel_filter"]["relevance_def"] for q in queries}
    report["assertions"]["filter_keys_are_predicates"] = {"pass": fkeys_all <= set(P_PREDICATES), "keys": sorted(fkeys_all)}
    report["assertions"]["relevance_keys_are_scene"] = {"pass": rkeys_all <= set(rel_masks.keys()), "keys": sorted(rkeys_all)}
    # A6-3: independence of each (pred, relevance-def) pair + positive-set density
    pairs = {(q["pair"], q["coupling"]) for q in queries}
    for pair, coupling in sorted(pairs):
        pred, rel = pair.split("|")
        v = cramers_v(df[pred].astype(str), pd.Series(rel_masks[rel]).astype(str))
        dens = float(rel_masks[rel].mean())
        report["independence"][pair] = {"cramers_v": None if np.isnan(v) else round(v, 3),
                                        "coupling": coupling, "rel_density": round(dens, 4)}
    lowV = [p for p, d in report["independence"].items() if d["cramers_v"] is not None and d["cramers_v"] < 0.3]
    report["coupling_summary"] = {"n_pairs": len(report["independence"]),
                                  "n_low_coupling(<0.3)": len(lowV),
                                  "max_v": max((d["cramers_v"] or 0) for d in report["independence"].values()) if report["independence"] else None}
    # A6-4: positive sets are discriminative (median density of relevance defs < 8%)
    med_density = float(np.median([rel_masks[n].mean() for n in rel_masks]))
    report["assertions"]["relevance_is_sparse"] = {"pass": med_density < 0.08, "median_rel_density": round(med_density, 4)}
    report["overall_pass"] = bool(report["assertions"]["filter_relevance_key_disjoint"]["pass"]
                                  and report["assertions"]["filter_keys_are_predicates"]["pass"]
                                  and report["assertions"]["relevance_keys_are_scene"]["pass"]
                                  and report["assertions"]["relevance_is_sparse"]["pass"]
                                  and len(lowV) >= 3)
    (out / "A6_noncircularity_audit.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--facets", default=str(DEFAULT_VER / "sensor_facets.parquet"))
    ap.add_argument("--out", default=str(DEFAULT_VER / "canonical"))
    ap.add_argument("--max-queries-per-value", type=int, default=12)
    ap.add_argument("--min-positives", type=int, default=10)
    ap.add_argument("--max-positives", type=int, default=800)
    ap.add_argument("--seed", type=int, default=20260710)
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(args.facets)

    # clips.parquet
    clips = df[["clip_id", "video_id", "split", "source_folder", "intersection_id", "date"]].copy()
    clips["dataset_id"] = DATASET_ID
    clips["media_type"] = "video"
    # media_path: intersection source video (TS_3 members); materialized in Phase 2
    clips["media_ref"] = clips["intersection_id"] + "/" + clips["video_id"] + ".mp4"
    clips["media_exists"] = False  # Phase-2 extraction pending
    clips.to_parquet(out / "clips.parquet", index=False)

    # metadata.parquet (long, role-tagged)
    metadata = build_metadata(df)
    metadata.to_parquet(out / "metadata.parquet", index=False)

    # queries + qrels (non-circular)
    queries, qrels = build_queries_qrels(df, args.max_queries_per_value, args.min_positives, args.max_positives)
    with (out / "queries.jsonl").open("w", encoding="utf-8") as f:
        for q in queries:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    pd.DataFrame(qrels).to_csv(out / "qrels.tsv", sep="\t", index=False)

    # facet roles + manifest
    (out / "facet_roles.json").write_text(json.dumps(
        {"predicate_P": P_PREDICATES, "relevance_defs": list(RELEVANCE_DEFS(df).keys()), "context": CONTEXT,
         "note": "metadata_filter keys must ⊂ predicate_P; qrel relevance is a named sparse scene def (disjoint from predicates)"},
        ensure_ascii=False, indent=2), encoding="utf-8")

    # A6 audit
    audit = a6_audit(queries, df, out)

    # report
    qdf = pd.DataFrame(queries)
    print(f"[clips]     {len(clips)}")
    print(f"[metadata]  {len(metadata)} facet rows ({metadata['facet_role'].value_counts().to_dict()})")
    print(f"[queries]   {len(queries)}  (by coupling: {qdf['coupling'].value_counts().to_dict() if len(qdf) else {}})")
    print(f"[qrels]     {len(qrels)} rows; avg positives/query: {np.mean([q['positive_count'] for q in queries]):.1f}")
    print("\n=== A6 NON-CIRCULARITY AUDIT ===")
    print(f"  filter⟂relevance keys disjoint : {audit['assertions']['filter_relevance_key_disjoint']['pass']}")
    print(f"  filter keys ⊂ P-predicates     : {audit['assertions']['filter_keys_are_predicates']['pass']} {audit['assertions']['filter_keys_are_predicates']['keys']}")
    print(f"  relevance keys ⊂ scene defs    : {audit['assertions']['relevance_keys_are_scene']['pass']} {audit['assertions']['relevance_keys_are_scene']['keys']}")
    print(f"  relevance is sparse (<8% med)  : {audit['assertions']['relevance_is_sparse']['pass']} (median density={audit['assertions']['relevance_is_sparse']['median_rel_density']})")
    print(f"  low-coupling pairs (<0.3)      : {audit['coupling_summary']['n_low_coupling(<0.3)']}/{audit['coupling_summary']['n_pairs']}  max_V={audit['coupling_summary']['max_v']}")
    print(f"  >>> OVERALL NON-CIRCULAR PASS  : {audit['overall_pass']}")
    print("\n  per-pair independence (Cramér's V) / positive density:")
    for pair, d in audit["independence"].items():
        print(f"    {pair:36s} V={d['cramers_v']}  density={d['rel_density']}  ({d['coupling']})")
    print(f"\n[saved] {out}/ {{clips,metadata,queries,qrels,facet_roles,A6_noncircularity_audit}}")
    print("[note] documents(captions)+embeddings = Phase-2 GPU; media_exists=False until TS_3 extraction.")
    return 0 if audit["overall_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
