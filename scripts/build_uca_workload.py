#!/usr/bin/env python3
"""UCA canonical workload builder [prereg 420 Amendment 6+6a, FROZEN].

Consumes build_uca_corpus.py outputs + caption_uca.py documents and emits the
project-standard canonical format (mirrors canonical_trisource_expanded):
  canonical/{clips,documents,metadata}.parquet, queries.jsonl,
  qrels.tsv (strict = lexicon AND predicate), qrels_semantic.tsv (lexicon only),
  A6_UCA_audit.json, workload_table.csv

Frozen rules applied here:
  - queries = (field value x lexicon) with strict positives >=5 AND >=5 distinct
    videos [6a(7)]; video_class uncapped 14 values; Normal_Videos legal but its
    queries tagged high-selectivity stratum [6a(9)]
  - coupling label = per-value phi (query's own 2x2), field-level Cramer's V kept
    as a descriptive column [6a(5)]; stratum = label_stratum (video_class) /
    container_clean (video_duration_bin) / annotation_timing (event_position_bin)
  - degeneracy screen for class-field queries: outside-class semantic positives
    <10 OR containment >0.9 -> flagged, separated in analysis [6a(3)]
  - A6-UCA audit: (a)-(f) + predicate-provenance table + e1 label-key hard /
    e2 lexicon-term-8gram hard / e3 generic verbatim 8-gram reported (abort >2%)
    + corpus-membership disclosure [6a(4)(8)]
Run (kiise-vlmdb env).
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/hdd2/KIISE_datasociety/Datasets/processed/uca_anchor/20260712")
CAN = ROOT / "canonical"
DSID = "uca_ucfcrime"

from build_uca_corpus import LEX  # frozen table (same directory)

QUERY_PHRASE = {  # one frozen English phrase per lexicon [Amendment 6]
    "falls": "Find scenes where someone falls to the ground.",
    "fight": "Find scenes where people are fighting or hitting each other.",
    "fire": "Find scenes with fire or smoke.",
    "weapon": "Find scenes where a weapon is visible.",
    "running": "Find scenes where someone is running.",
    "crash": "Find scenes of a vehicle crash.",
    "money": "Find scenes involving money or a cash register.",
    "door": "Find scenes where someone interacts with a door.",
    "take": "Find scenes where someone takes or grabs an item.",
    "enterexit": "Find scenes where someone enters or leaves a place.",
}
FIELD_STRATUM = {"video_class": "label_stratum",
                 "video_duration_bin": "container_clean",
                 "event_position_bin": "annotation_timing"}
PROVENANCE = {"video_class": "UCF-Crime curation (video id prefix; producer=CRCV authors)",
              "video_duration_bin": "container ffprobe duration (producer=this pipeline, exogenous)",
              "event_position_bin": "UCA annotation timestamps (producer=UCA annotators; "
                                    "TIMING only, content-free; DEMOTED per 6a(4))"}


def cramers_v(a: pd.Series, b: pd.Series) -> float:
    ct = pd.crosstab(a, b).to_numpy().astype(float)
    n = ct.sum()
    if n == 0:
        return 0.0
    exp = ct.sum(1, keepdims=True) @ ct.sum(0, keepdims=True) / n
    chi2 = ((ct - exp) ** 2 / np.where(exp == 0, 1, exp)).sum()
    r, c = ct.shape
    denom = n * (min(r - 1, c - 1) or 1)
    return float(np.sqrt(chi2 / denom))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--captions-path", type=Path, default=None,
                        help="model-versioned documents.parquet; defaults to root/captions")
    parser.add_argument("--out-dir", type=Path, default=None,
                        help="explicit canonical output directory")
    args = parser.parse_args()
    root = args.root
    can = args.out_dir or root / "canonical"
    captions_path = args.captions_path or root / "captions" / "documents.parquet"
    can.mkdir(parents=True, exist_ok=True)
    seg = pd.read_parquet(root / "segments.parquet")
    rel = pd.read_parquet(root / "relevance.parquet").set_index("doc_id")
    meta = pd.read_parquet(root / "metadata.parquet").set_index("doc_id")
    caps = pd.read_parquet(captions_path).set_index("doc_id")
    sents = pd.read_parquet(root / "annotation_sentences.parquet").set_index("doc_id")
    # corpus = captioned segments only (disclosure: membership is annotation-driven)
    ids = [i for i in seg.doc_id if i in caps.index]
    seg = seg.set_index("doc_id").loc[ids]
    print(f"[corpus] captioned documents = {len(ids)}")

    def cid(i):
        return f"{DSID}:{seg.loc[i,'split']}:{i.split(':',1)[1]}"
    clips = pd.DataFrame({
        "clip_id": [cid(i) for i in ids], "dataset_id": DSID,
        "visual_video_id": seg.loc[ids, "video_id"].values,
        "split": seg.loc[ids, "split"].values, "media_type": "frame",
        "media_path": seg.loc[ids, "frame"].values, "media_exists": "True"})
    docs = pd.DataFrame({
        "doc_id": [f"{DSID}:doc:vlm_caption:{i}" for i in ids],
        "clip_id": clips.clip_id.values, "dataset_id": DSID,
        "doc_type": "vlm_dense_caption",
        "text": caps.loc[ids, "caption"].values, "lang": "en"})
    mrows = []
    for i, c in zip(ids, clips.clip_id):
        for f in FIELD_STRATUM:
            mrows.append({"clip_id": c, "dataset_id": DSID, "facet_name": f,
                          "facet_value": str(meta.loc[i, f]),
                          "facet_role": "predicate", "facet_source": PROVENANCE[f]})
    metadata = pd.DataFrame(mrows)

    # ---- queries + dual qrels ----
    lex_cols = {k: rel.loc[ids, f"rel_{k}"].to_numpy() for k in LEX}
    vids_arr = seg.loc[ids, "video_id"].to_numpy()
    queries, qrels, qrels_sem, table = [], [], [], []
    qn = 0
    for field in FIELD_STRATUM:
        fv = meta.loc[ids, field].astype(str).to_numpy()
        for val in sorted(pd.unique(fv)):
            pmask = fv == val
            for lx, lmask in lex_cols.items():
                strict = pmask & lmask
                if strict.sum() < 5 or len(set(vids_arr[strict])) < 5:
                    continue
                qn += 1
                qid = f"uca:{field}:{qn:04d}"
                phi = cramers_v(pd.Series(pmask), pd.Series(lmask))
                fieldV = cramers_v(pd.Series(fv), pd.Series(lmask))
                out_pos = int((~pmask & lmask).sum())
                contain = float(strict.sum() / lmask.sum())
                degen = (field == "video_class") and (out_pos < 10 or contain > 0.9)
                queries.append({
                    "query_id": qid, "dataset_id": DSID,
                    "query_text": QUERY_PHRASE[lx],
                    "task": "uca_external_filtered_scene_retrieval",
                    "metadata_filter": {field: val}, "relevance_def": lx,
                    "coupling": "low" if phi < 0.3 else "natural",
                    "difficulty": field, "stratum": FIELD_STRATUM[field],
                    "normal_stratum": bool(val == "Normal_Videos"),
                    "degenerate": bool(degen),
                    "phi_value_level": round(phi, 4), "V_field_level": round(fieldV, 4),
                    "positive_count": int(strict.sum()),
                    "positive_count_semantic": int(lmask.sum()),
                    "distinct_videos": int(len(set(vids_arr[strict])))})
                for arr, sink in [(strict, qrels), (lmask, qrels_sem)]:
                    for c in clips.clip_id.values[arr]:
                        sink.append({"query_id": qid, "target_id": c,
                                     "target_type": "clip", "relevance": 3})
                table.append({k: queries[-1][k] for k in
                              ["query_id", "difficulty", "relevance_def", "stratum",
                               "normal_stratum", "degenerate", "phi_value_level",
                               "V_field_level", "positive_count",
                               "positive_count_semantic", "distinct_videos"]}
                             | {"filter_value": val, "containment": round(contain, 3),
                                "outside_positives": out_pos})

    # ---- A6-UCA audit ----
    doc_texts = docs.text.str.lower().tolist()
    sent_join = [" ".join(sents.loc[i, "sentences"]).lower() for i in ids]
    label_keys = ["video_class", "video_duration_bin", "event_position_bin",
                  "_x264", "normal_videos", "roadaccidents"] + \
                 [c.lower() for c in ["Abuse", "Arrest", "Arson", "Assault", "Burglary",
                                      "Explosion", "Shoplifting", "Vandalism"]]
    # e1: machine/label keys must not appear in documents (word forms that cannot
    # arise from pixels; common words like 'fighting','robbery','stealing','shooting'
    # are pixel-describable and excluded from the hard list — disclosed)
    e1_hits = sum(1 for t in doc_texts for k in
                  ["video_class", "video_duration_bin", "event_position_bin",
                   "_x264", "normal_videos", "roadaccidents"] if k in t)

    def grams(s, n=8):
        w = re.findall(r"[a-z']+", s)
        return {" ".join(w[j:j + n]) for j in range(len(w) - n + 1)}
    lex_pat = re.compile("|".join(f"(?:{r})" for r in LEX.values()), re.IGNORECASE)
    e2_hits, e3_hits = [], []
    for i, (dt, st) in enumerate(zip(doc_texts, sent_join)):
        common = grams(dt) & grams(st)
        if not common:
            continue
        lexy = [g for g in common if lex_pat.search(g)]
        if lexy:
            e2_hits.append((ids[i], lexy[:2]))
        else:
            e3_hits.append(ids[i])
    e3_rate = len(e3_hits) / len(ids)
    rel_density = {k: float(v.mean()) for k, v in lex_cols.items()}
    audit = {
        "a_filter_keys_in_declared_fields": sorted({q["difficulty"] for q in queries}) ==
            sorted(FIELD_STRATUM),
        "b_relevance_defs_frozen": sorted({q["relevance_def"] for q in queries}) ==
            sorted(k for k in LEX if any(q["relevance_def"] == k for q in queries)),
        "c_key_disjoint": not (set(FIELD_STRATUM) & set(LEX)),
        "d_metadata_has_no_relevance": not any(
            f.startswith("rel_") or f in LEX for f in metadata.facet_name.unique()),
        "e1_label_key_leak_count": e1_hits,
        "e1_pass": e1_hits == 0,
        "e2_lexicon_8gram_overlap_count": len(e2_hits),
        "e2_pass": len(e2_hits) == 0,
        "e2_examples": e2_hits[:5],
        "e3_generic_8gram_overlap_rate": round(e3_rate, 5),
        "e3_within_abort_threshold_2pct": e3_rate <= 0.02,
        "e3_affected_docs": len(e3_hits),
        "f_admitted_densities_in_window": {k: round(v, 4) for k, v in rel_density.items()},
        "f_pass": all(0.01 <= v <= 0.12 for v in rel_density.values()),
        "predicate_provenance": PROVENANCE,
        "membership_disclosure": "corpus membership (which frames become documents) "
                                 "is annotation-driven (UCA event spans)",
        "captions_path": str(captions_path),
        "lexical_overlap_note": "pixel-mediated unigram overlap is legal by design "
                                "(2.5-channel residual, disclosed)",
    }
    audit["overall_pass"] = all([audit["a_filter_keys_in_declared_fields"],
                                 audit["b_relevance_defs_frozen"], audit["c_key_disjoint"],
                                 audit["d_metadata_has_no_relevance"], audit["e1_pass"],
                                 audit["e2_pass"], audit["e3_within_abort_threshold_2pct"],
                                 audit["f_pass"]])

    # ---- write ----
    clips.to_parquet(can / "clips.parquet", index=False)
    docs.to_parquet(can / "documents.parquet", index=False)
    metadata.to_parquet(can / "metadata.parquet", index=False)
    with (can / "queries.jsonl").open("w") as f:
        for q in queries:
            f.write(json.dumps(q) + "\n")
    pd.DataFrame(qrels).to_csv(can / "qrels.tsv", sep="\t", index=False)
    pd.DataFrame(qrels_sem).to_csv(can / "qrels_semantic.tsv", sep="\t", index=False)
    (can / "A6_UCA_audit.json").write_text(json.dumps(audit, indent=2))
    tdf = pd.DataFrame(table)
    tdf.to_csv(can / "workload_table.csv", index=False)
    n_lex = tdf.relevance_def.nunique()
    n_fields = tdf.difficulty.nunique()
    lowpower = n_lex < 5 or n_fields < 2
    print(f"[workload] queries={len(queries)} lexicons={n_lex} fields={n_fields} "
          f"degenerate={int(tdf.degenerate.sum())} normal_stratum={int(tdf.normal_stratum.sum())}")
    print(f"[audit] overall_pass={audit['overall_pass']} e2={len(e2_hits)} "
          f"e3_rate={e3_rate:.4f} lowpower={lowpower}")
    return 0 if audit["overall_pass"] and not lowpower else 1


if __name__ == "__main__":
    raise SystemExit(main())
