#!/usr/bin/env python3
"""Phase 2 (Pillar A/C): TRI-SOURCE non-circular canonical for the 522 visual track.

Assembles the three independent channels into one retrieval workload:

  DOCUMENT   = VLM caption of frame pixels        (captions/documents.parquet)
  PREDICATE  = sensor CSV facets via the synced   (visual_sensor_join.parquet)
               cross-camera join, cam x10
  RELEVANCE  = human CVAT annotation events,      (annotation_video_facets.parquet)
               cams x11/x22

Corpus = captioned videos only. Emits canonical_trisource/ compatible with the
existing chain (build_text_embeddings.py -> run_retrieval_baselines.py, which
requires query fields: query_text, metadata_filter, difficulty, positive_count).

DUAL QRELS (the honesty core):
  qrels.tsv           STRICT: relevant = annotation-event AND predicate holds.
                      Classic filtered-search GT; prefilter can only help here —
                      that is real system behavior, and we say so.
  qrels_semantic.tsv  SEMANTIC-ONLY: relevant = annotation-event regardless of
                      the predicate. Filter = soft user intent; prefiltering can
                      now REMOVE relevant clips -> B4 >= B2 is NOT structurally
                      guaranteed. This is the non-circular headline eval.

Extended A6 audit asserts: source separation (predicate keys from sensor facets;
relevance from annotation channel; both absent from document text), coupling
matrix from trisource_independence.json thresholds, sparse relevance density.

Run (after captions merged):
  Datasets/envs/kiise-vlmdb/bin/python \
    2026_KIISE/04_scripts/build_intersection_trisource_canonical.py
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DS = PROJECT_ROOT / "Datasets"
VER = DS / "processed" / "aihub_522_intersection" / "20260710"
DATASET_ID = "aihub_522_intersection_vis"

P_PREDICATES = ["time_of_day", "hour", "sig_has_yellow", "sig_has_pedestrian", "veh_density_bin"]


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
CONTEXT = ["intersection_id", "n_vehicles", "n_pedestrians", "sig_phase_set"]

# annotation-derived relevance events (sparse first = headline)
def REL_DEFS(df: pd.DataFrame) -> dict[str, pd.Series]:
    return {
        "parked_vehicle": df["any_parked"].astype(bool),              # ~1.9%
        "dense_frame": (df["max_objects"] >= 20),                     # ~2.2%
        "multiple_buses": (df["max_bus"] >= 2),                       # ~8.6%
        "stopped_vehicles": df["any_stopped"].astype(bool),           # ~20% dense-contrast
        # EXPANSION (preregistered rule 2026-07-11): density on the captioned base
        # must fall in [1%, 12%] and the def must NOT be a boolean combination of
        # existing defs. Admitted: two_plus_bikes (11.5%). Rejected mechanically:
        # truck_convoy3 (13.6% > 12%), very_dense25 (0.87% < 1%), combos.
        "two_plus_bikes": (df["max_bike"] >= 2),                      # ~11.5%
    }

R_NL = {
    "parked_vehicle": "a vehicle parked at the roadside",
    "dense_frame": "a very crowded scene with many vehicles at once",
    "multiple_buses": "two or more buses in view",
    "stopped_vehicles": "vehicles stopped in the roadway",
    "two_plus_bikes": "two or more bicycles or motorbikes in view",
}
P_NL = {
    "time_of_day": "during the {v}",
    "hour": "around {v}:00",
    "veh_density_bin": "under {v} sensor-measured traffic density",
    "sig_has_yellow": ("while a yellow signal phase occurs", "while no yellow signal phase occurs"),
    "sig_has_pedestrian": ("while a pedestrian signal phase is active", "while no pedestrian signal phase is active"),
}

# (predicate, relevance, coupling-tag from trisource_independence.json)
PAIR_SPECS = [
    ("sig_has_yellow", "parked_vehicle", "low"),        # V=0.005
    ("time_of_day", "multiple_buses", "low"),           # V=0.007
    ("sig_has_pedestrian", "parked_vehicle", "low"),    # V=0.012
    ("hour", "multiple_buses", "low"),                  # V=0.023
    ("time_of_day", "dense_frame", "low"),              # V=0.054
    ("veh_density_bin", "parked_vehicle", "low"),       # V=0.030
    ("hour", "stopped_vehicles", "contrast"),           # V=0.450 rush-hour coupling arm
    ("veh_density_bin", "dense_frame", "contrast"),     # sensor-density vs visual-density
]


def expanded_pair_specs(base: pd.DataFrame) -> list[tuple[str, str, str]]:
    """PREREGISTERED EXPANSION RULE (2026-07-11, mechanical — no hand-picking):
    full cross product P_PREDICATES x REL_DEFS; coupling label = measured
    Cramér's V on the captioned base with the SAME 0.3 threshold used for the
    original 8 specs ('low' if V<0.3 else 'contrast'). Query admission rules
    (min_pos, max per value) unchanged. Original-32 subset remains identifiable
    via query_id prefix for separate reporting."""
    rels = REL_DEFS(base)
    out = []
    for pred in P_PREDICATES:
        for rel, mask in rels.items():
            v = cramers_v(base[pred].astype(str), mask.astype(str))
            out.append((pred, rel, "low" if (np.isnan(v) or v < 0.3) else "contrast"))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ver", default=str(VER))
    ap.add_argument("--min-pos", type=int, default=5)
    ap.add_argument("--max-queries-per-value", type=int, default=12)
    ap.add_argument("--captions-path", type=Path, default=None,
                    help="model-versioned documents.parquet; defaults to ver/captions")
    ap.add_argument("--out-dir", type=Path, default=None,
                    help="explicit canonical output directory")
    ap.add_argument("--expanded", action="store_true",
                    help="preregistered mechanical expansion: full predicate x rel-def "
                         "cross product, V-labeled coupling; writes *_expanded dir")
    args = ap.parse_args()
    ver = Path(args.ver)
    out = args.out_dir or ver / (
        "canonical_trisource_expanded" if args.expanded else "canonical_trisource"
    )
    out.mkdir(parents=True, exist_ok=True)

    captions_path = args.captions_path or ver / "captions" / "documents.parquet"
    docs_src = pd.read_parquet(captions_path)
    join = pd.read_parquet(ver / "visual_sensor_join.parquet")
    ann = pd.read_parquet(ver / "annotation_video_facets.parquet")
    vv = pd.read_parquet(ver / "visual_videos.parquet")

    # ---- corpus = captioned videos with join + annotation ----
    doc_keys = ["visual_video_id", "clip_id", "text", "doc_id", "source_frame"]
    join_keys = ["visual_video_id"]
    if "split" in docs_src.columns:            # split-aware merge (post-fix captions)
        doc_keys.append("split")
        join_keys.append("split")
    base = (docs_src[doc_keys]
            .merge(join[join.join_ok_120s].drop(columns=["sensor_clip_id"]).rename(columns={"clip_id": "_x"}, errors="ignore"),
                   on=join_keys, how="inner", suffixes=("", "_j"))
            .merge(ann, on=["visual_video_id", "split"], how="inner")
            .merge(vv[["visual_video_id", "split", "intersection_id"]],
                   on=["visual_video_id", "split"], how="left"))
    base["vis_clip_id"] = DATASET_ID + ":" + base["split"] + ":" + base["visual_video_id"]
    base = base.drop_duplicates("vis_clip_id").reset_index(drop=True)
    rel_masks = {k: m for k, m in REL_DEFS(base).items()}
    print(f"[corpus] captioned+joined+annotated videos: {len(base)}")

    # ---- clips ----
    clips = pd.DataFrame({
        "clip_id": base["vis_clip_id"], "dataset_id": DATASET_ID,
        "visual_video_id": base["visual_video_id"], "split": base["split"],
        "media_type": "frame_set", "media_path": base["source_frame"],
        "media_exists": True,
    })
    clips.to_parquet(out / "clips.parquet", index=False)

    # ---- documents (captions only; nothing else enters the corpus) ----
    docs = pd.DataFrame({
        "doc_id": base["doc_id"], "clip_id": base["vis_clip_id"],
        "dataset_id": DATASET_ID, "doc_type": "vlm_dense_caption",
        "text": base["text"], "lang": "en",
    })
    docs.to_parquet(out / "documents.parquet", index=False)

    # ---- metadata (predicates + context; relevance NEVER enters metadata) ----
    meta_rows = []
    for rec in base.to_dict("records"):
        for f in P_PREDICATES:
            meta_rows.append({"clip_id": rec["vis_clip_id"], "dataset_id": DATASET_ID,
                              "facet_name": f, "facet_value": str(rec[f]),
                              "facet_role": "predicate", "facet_source": "sensor_csv_cross_camera"})
        for f in CONTEXT:
            if f in rec:
                meta_rows.append({"clip_id": rec["vis_clip_id"], "dataset_id": DATASET_ID,
                                  "facet_name": f, "facet_value": str(rec[f]),
                                  "facet_role": "context", "facet_source": "sensor_csv_cross_camera"})
    metadata = pd.DataFrame(meta_rows)
    metadata.to_parquet(out / "metadata.parquet", index=False)

    # ---- queries + dual qrels ----
    specs = expanded_pair_specs(base) if args.expanded else PAIR_SPECS
    orig_pairs = {(p, r) for p, r, _ in PAIR_SPECS}
    if args.expanded:
        print(f"[expanded] {len(specs)} pair specs (cross product), "
              f"coupling: {sum(1 for *_, c in specs if c=='low')} low / "
              f"{sum(1 for *_, c in specs if c=='contrast')} contrast")
    queries, qrels_strict, qrels_sem = [], [], []
    qn = 0
    for pred, rel, coupling in specs:
        rel_mask = rel_masks[rel].to_numpy()
        pvals = base[pred].value_counts()
        vals = list(pvals.index[:args.max_queries_per_value])
        for v in vals:
            pred_mask = (base[pred].astype(str) == str(v)).to_numpy()
            strict_ids = base.loc[pred_mask & rel_mask, "vis_clip_id"].tolist()
            sem_ids = base.loc[rel_mask, "vis_clip_id"].tolist()
            if len(strict_ids) < args.min_pos:
                continue
            cond = (P_NL[pred][0] if str(v) == "True" else P_NL[pred][1]) \
                if isinstance(P_NL[pred], tuple) else P_NL[pred].format(v=v)
            qn += 1
            qid = f"522vis:{coupling}:{qn:04d}"
            queries.append({
                "query_id": qid, "dataset_id": DATASET_ID,
                "query_text": f"Find CCTV clips showing {R_NL[rel]} {cond}.",
                "task": "trisource_filtered_scene_retrieval",
                "metadata_filter": {pred: str(v)},
                "relevance_def": rel, "coupling": coupling,
                "difficulty": pred,                    # runner groups by this
                "in_original_specs": (pred, rel) in orig_pairs,
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
             "captions_path": str(captions_path), "assertions": {}}
    fkeys = set().union(*[set(q["metadata_filter"]) for q in queries]) if queries else set()
    rkeys = {q["relevance_def"] for q in queries}
    audit["assertions"]["filter_keys_are_sensor_predicates"] = {
        "pass": fkeys <= set(P_PREDICATES), "keys": sorted(fkeys)}
    audit["assertions"]["relevance_from_annotation_channel"] = {
        "pass": rkeys <= set(rel_masks), "keys": sorted(rkeys)}
    audit["assertions"]["filter_relevance_disjoint"] = {"pass": not (fkeys & rkeys)}
    audit["assertions"]["metadata_contains_no_relevance"] = {
        "pass": not (set(metadata.facet_name.unique()) & set(rel_masks))}
    # document leak scan: relevance/facet tokens must not appear as machine tokens
    leak_tokens = ["any_parked", "max_objects", "sig_has_", "veh_density_bin", "rel__"]
    leaked = int(docs["text"].str.contains("|".join(leak_tokens), regex=True).sum())
    audit["assertions"]["document_token_leak_zero"] = {"pass": leaked == 0, "leaked_docs": leaked}
    dens = {k: round(float(m.mean()), 4) for k, m in rel_masks.items()}
    audit["relevance_density"] = dens
    audit["assertions"]["headline_relevance_sparse"] = {
        "pass": min(dens.values()) < 0.05, "densities": dens}
    audit["dual_qrels"] = {
        "strict_rows": len(qrels_strict), "semantic_rows": len(qrels_sem),
        "note": "strict: prefilter can only help (real filtered-search); "
                "semantic-only: B4>=B2 NOT guaranteed (non-circular headline)"}
    audit["overall_pass"] = all(a["pass"] for a in audit["assertions"].values())
    (out / "A6_trisource_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    qdf = pd.DataFrame(queries)
    print(f"[queries] {len(queries)} (coupling: {qdf.coupling.value_counts().to_dict() if len(qdf) else {}})")
    print(f"[qrels] strict={len(qrels_strict)} semantic={len(qrels_sem)}")
    print(f"[audit] overall_pass={audit['overall_pass']}")
    for k, a in audit["assertions"].items():
        print(f"   {k}: {a['pass']}")
    print(f"[saved] {out}/")
    return 0 if audit["overall_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
