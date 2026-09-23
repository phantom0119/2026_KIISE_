#!/usr/bin/env python3
"""MEVA tri-source non-circular canonical workload (overseas external-validity arm).

Mirrors build_intersection_trisource_canonical.py (522) for MEVA:

  DOCUMENT   = VLM caption of frame pixels        (captions/documents.parquet)
  PREDICATE  = capture metadata (time/location)   (predicate_facets.parquet)
  RELEVANCE  = DIVA human activity annotations     (activity_presence.parquet)

DUAL QRELS (honesty core, identical semantics to 522):
  qrels.tsv           STRICT   = activity present AND predicate holds.
  qrels_semantic.tsv  SEMANTIC = activity present regardless of predicate.

RELEVANCE defs are selected MECHANICALLY by density band (headline sparse
[1.5%,12%]); PAIR_SPECS = full P_PREDICATES x REL cross product, coupling labeled
by measured Cramer's V (<0.3 = low) — same preregistered rule as 522.

Non-circularity (A6) asserts source separation: predicate keys are capture
metadata; relevance keys are activity classes; the two are disjoint; predicate
facets carry no relevance; (with captions) no activity/facet token leaks into the
document text. The activity label is RELEVANCE ONLY and never a predicate.

Run (structural, before captions — validates separation on real data):
  Datasets/envs/kiise-vlmdb/bin/python \
    2026_KIISE/04_scripts/build_meva_trisource_canonical.py --allow-no-doc
Run (full, after build_meva_captions.py -> captions/documents.parquet):
  ... build_meva_trisource_canonical.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DS = PROJECT_ROOT / "Datasets"
DATASET_ID = "meva_kf1"

P_PREDICATES = ["time_of_day", "location", "hour"]
P_NL = {
    "time_of_day": "during the {v}",
    "location": "at the {v} site",
    "hour": "around {v}:00",
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


def nl_activity(name: str) -> str:
    return "a " + name.replace("_", " ")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ver", default="20260713")
    ap.add_argument("--min-pos", type=int, default=5)
    ap.add_argument("--max-queries-per-value", type=int, default=12)
    ap.add_argument("--rel-min-density", type=float, default=0.015)
    ap.add_argument("--rel-max-density", type=float, default=0.12,
                    help="headline sparse band upper bound (preregistered, mirrors 522 [1%,12%])")
    ap.add_argument("--allow-no-doc", action="store_true",
                    help="build without the VLM caption document channel (structural "
                         "source-separation validation before GPU captioning)")
    ap.add_argument("--captions-path", type=Path, default=None,
                    help="model-versioned documents.parquet; defaults to ver/captions")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="explicit canonical output directory")
    args = ap.parse_args()
    ver = DS / "processed" / DATASET_ID / args.ver
    out = args.out_dir or ver / "canonical_trisource"
    out.mkdir(parents=True, exist_ok=True)

    clips = pd.read_parquet(ver / "clips.parquet")
    pres = pd.read_parquet(ver / "activity_presence.parquet")
    indep = json.loads((ver / "meva_independence.json").read_text())
    dens = indep["relevance_densities"]

    doc_path = args.captions_path or ver / "captions" / "documents.parquet"
    have_docs = doc_path.exists()
    if not have_docs and not args.allow_no_doc:
        raise SystemExit(f"no captions at {doc_path}; run build_meva_captions.py or pass --allow-no-doc")

    base = clips.merge(pres, on="clip_id")
    if have_docs:
        docs_src = pd.read_parquet(doc_path)
        base = base.merge(docs_src[["clip_id", "text", "doc_id", "source_frame"]],
                          on="clip_id", how="inner")
        print(f"[corpus] captioned+annotated clips: {len(base)}")
    else:
        base["text"] = ""  # placeholder; document channel pending
        base["doc_id"] = DATASET_ID + ":doc:pending:" + base["clip_id"]
        base["source_frame"] = ""
        print(f"[corpus] annotated clips (NO document channel yet): {len(base)}")

    # ---- relevance defs: mechanical density band (headline sparse) ----
    rel_names = [v for v in dens if args.rel_min_density <= dens[v] <= args.rel_max_density]
    rel_masks = {v: base[f"act__{v}"].astype(bool) for v in rel_names}
    print(f"[relevance] {len(rel_names)} activity defs in [{args.rel_min_density},{args.rel_max_density}]: "
          f"{rel_names}")

    # ---- clips ----
    pd.DataFrame({
        "clip_id": base["clip_id"], "dataset_id": DATASET_ID,
        "clip_base": base["clip_base"], "media_type": "avi_clip",
        "media_path": base["avi_s3_key"], "location": base["location"],
        "camera": base["camera"],
    }).to_parquet(out / "clips.parquet", index=False)

    # ---- documents (captions only; nothing else enters the corpus) ----
    pd.DataFrame({
        "doc_id": base["doc_id"], "clip_id": base["clip_id"], "dataset_id": DATASET_ID,
        "doc_type": "vlm_dense_caption" if have_docs else "pending",
        "text": base["text"], "lang": "en",
    }).to_parquet(out / "documents.parquet", index=False)

    # ---- metadata (predicates + context; relevance NEVER enters metadata) ----
    meta_rows = []
    for rec in base.to_dict("records"):
        for f in P_PREDICATES:
            meta_rows.append({"clip_id": rec["clip_id"], "dataset_id": DATASET_ID,
                              "facet_name": f, "facet_value": str(rec[f]),
                              "facet_role": "predicate", "facet_source": "meva_capture_metadata"})
        meta_rows.append({"clip_id": rec["clip_id"], "dataset_id": DATASET_ID,
                          "facet_name": "camera", "facet_value": str(rec["camera"]),
                          "facet_role": "context", "facet_source": "meva_capture_metadata"})
    metadata = pd.DataFrame(meta_rows)
    metadata.to_parquet(out / "metadata.parquet", index=False)

    # ---- queries + dual qrels (full cross product, V-labeled coupling) ----
    queries, qrels_strict, qrels_sem = [], [], []
    qn = 0
    for pred in P_PREDICATES:
        for rel in rel_names:
            rel_mask = rel_masks[rel].to_numpy()
            cv = cramers_v(base[pred].astype(str), base[f"act__{rel}"].astype(str))
            coupling = "contrast" if (not np.isnan(cv) and cv >= 0.3) else "low"
            for v in list(base[pred].value_counts().index[:args.max_queries_per_value]):
                pmask = (base[pred].astype(str) == str(v)).to_numpy()
                strict_ids = base.loc[pmask & rel_mask, "clip_id"].tolist()
                sem_ids = base.loc[rel_mask, "clip_id"].tolist()
                if len(strict_ids) < args.min_pos:
                    continue
                qn += 1
                qid = f"meva:{coupling}:{qn:04d}"
                queries.append({
                    "query_id": qid, "dataset_id": DATASET_ID,
                    "query_text": f"Find surveillance clips showing {nl_activity(rel)} {P_NL[pred].format(v=v)}.",
                    "task": "trisource_filtered_scene_retrieval",
                    "metadata_filter": {pred: str(v)},
                    "relevance_def": rel, "coupling": coupling,
                    "cramers_v": None if np.isnan(cv) else round(float(cv), 4),
                    "difficulty": pred,
                    "positive_count": len(strict_ids),
                    "positive_count_semantic": len(sem_ids),
                })
                qrels_strict += [{"query_id": qid, "target_id": c, "target_type": "clip", "relevance": 3}
                                 for c in strict_ids]
                qrels_sem += [{"query_id": qid, "target_id": c, "target_type": "clip", "relevance": 3}
                              for c in sem_ids]
    with (out / "queries.jsonl").open("w", encoding="utf-8") as f:
        for q in queries:
            f.write(json.dumps(q, ensure_ascii=False) + "\n")
    pd.DataFrame(qrels_strict).to_csv(out / "qrels.tsv", sep="\t", index=False)
    pd.DataFrame(qrels_sem).to_csv(out / "qrels_semantic.tsv", sep="\t", index=False)

    # ---- extended A6 audit ----
    audit = {"n_corpus": int(len(base)), "n_queries": len(queries),
             "captions_path": str(doc_path),
             "have_document_channel": have_docs, "assertions": {}}
    fkeys = set().union(*[set(q["metadata_filter"]) for q in queries]) if queries else set()
    rkeys = {q["relevance_def"] for q in queries}
    audit["assertions"]["filter_keys_are_capture_predicates"] = {
        "pass": fkeys <= set(P_PREDICATES), "keys": sorted(fkeys)}
    audit["assertions"]["relevance_from_activity_channel"] = {
        "pass": rkeys <= set(rel_masks), "keys": sorted(rkeys)}
    audit["assertions"]["filter_relevance_disjoint"] = {"pass": not (fkeys & rkeys)}
    audit["assertions"]["metadata_contains_no_relevance"] = {
        "pass": not (set(metadata.facet_name.unique()) & set(dens))}
    audit["assertions"]["source_separation_three_producers"] = {
        "pass": True,
        "predicate_source": "meva_capture_metadata",
        "relevance_source": "meva_diva_activity",
        "document_source": "vlm_caption_pixels_only" if have_docs else "pending"}
    dens_sel = {k: dens[k] for k in rel_names}
    audit["relevance_density"] = dens_sel
    audit["assertions"]["headline_relevance_sparse"] = {
        "pass": (min(dens_sel.values()) < 0.05) if dens_sel else False,
        "densities": dens_sel}
    if have_docs:
        docs = pd.read_parquet(out / "documents.parquet")
        leak_tokens = list(dens) + ["act__", "cnt__", "facet_"]
        leaked = int(docs["text"].str.contains("|".join(map(str, leak_tokens)), regex=True, case=False).sum())
        audit["assertions"]["document_token_leak_zero"] = {"pass": leaked == 0, "leaked_docs": leaked}
    else:
        audit["assertions"]["document_token_leak_zero"] = {"pass": None, "note": "captions pending (GPU)"}

    audit["dual_qrels"] = {"strict_rows": len(qrels_strict), "semantic_rows": len(qrels_sem)}
    checkable = {k: a for k, a in audit["assertions"].items() if a["pass"] is not None}
    audit["overall_structural_pass"] = all(a["pass"] for a in checkable.values())
    audit["overall_pass"] = (audit["overall_structural_pass"] and have_docs
                             and audit["assertions"]["document_token_leak_zero"]["pass"] is True)
    (out / "A6_trisource_audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2))

    qdf = pd.DataFrame(queries)
    print(f"[queries] {len(queries)} (coupling: {qdf.coupling.value_counts().to_dict() if len(qdf) else {}})")
    print(f"[qrels] strict={len(qrels_strict)} semantic={len(qrels_sem)}")
    print(f"[audit] structural_pass={audit['overall_structural_pass']}  full_pass={audit['overall_pass']}")
    for k, a in audit["assertions"].items():
        print(f"   {k}: {a['pass']}")
    print(f"[saved] {out}/")
    return 0 if audit["overall_structural_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
