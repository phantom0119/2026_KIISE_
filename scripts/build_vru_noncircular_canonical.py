#!/usr/bin/env python3
"""Pillar A9: repaired (non-circular) VRU-Accident workload, NEW version dir.

The original VRU canonical (20260706) is circular (review F1/F2/F4):
  F2  corpus contains vqa_facet_statement docs restating the answer labels
  F1  metadata_filter facets are a subset of the SAME facets defining qrels
  F4  relevance == template facet match, so prefilter guarantees B4 >= B2

This builder subclasses the v1 adapter WITHOUT modifying it (v1 outputs stay
for the old-vs-new collapse table) and emits 20260710_noncircular:

  documents  = dense captions ONLY (facet statements dropped)         [F2 fix]
  relevance  = SEMANTIC axis only: accident_type membership           [F4 fix]
  filter     = a DIFFERENT operational facet (weather/road/location)  [F1 fix]
               never accident_type
  dual qrels = qrels.tsv (strict: type AND filter — legitimate filtered
               search, prefilter may help) + qrels_semantic.tsv (type only —
               prefilter may REMOVE relevant clips; non-circular headline)

Caveat kept honest: in VRU both channels are VQA-derived (same annotators),
unlike 522 where predicate/relevance come from different cameras/files. The
audit therefore reports the coupling V(accident_type, filter facet) per pair.

Run:
  Datasets/envs/kiise-vlmdb/bin/python \
    2026_KIISE/scripts/build_vru_noncircular_canonical.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.adapters.vru_accident import VRUAccidentAdapter, DATASET_ID  # noqa: E402

FILTER_FACETS = ["weather_light", "road_type", "location"]   # operational axis
SEMANTIC_FACET = "accident_type"                              # relevance axis


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


class VRUNonCircularAdapter(VRUAccidentAdapter):
    """v2: caption-only corpus + semantic-vs-filter axis separation + dual qrels."""

    def _build_documents(self, captions: pd.DataFrame, vqa: pd.DataFrame) -> pd.DataFrame:
        docs = []
        for row in captions.to_dict("records"):
            docs.append({
                "doc_id": f"{row['clip_id']}:doc:dense_caption",
                "clip_id": row["clip_id"], "dataset_id": DATASET_ID,
                "doc_type": "dense_caption", "text": row["caption"],
                "lang": "en", "source": row["source_file"],
            })
        return pd.DataFrame(docs).drop_duplicates("doc_id")   # NO facet statements (F2)

    def _build_queries_and_qrels(self, metadata: pd.DataFrame):
        table = (metadata.pivot_table(index="clip_id", columns="facet_name",
                                      values="facet_value", aggfunc="first")
                 .reset_index().fillna(""))
        queries, qrels_strict, qrels_sem = [], [], []
        coupling = {}
        qn = 0
        types = table[SEMANTIC_FACET].value_counts()
        for facet in FILTER_FACETS:
            if facet not in table.columns:
                continue
            coupling[facet] = round(cramers_v(table[SEMANTIC_FACET], table[facet]), 3)
        for atype, support in types.items():
            if not atype or support < 5:
                continue
            sem_ids = table.loc[table[SEMANTIC_FACET].eq(atype), "clip_id"].tolist()
            # (a) no-filter semantic baseline query
            qn += 1
            qid = f"vru2:nofilter:{qn:04d}"
            queries.append({
                "query_id": qid, "dataset_id": DATASET_ID,
                "query_text": f"Find videos where the accident type is {atype}.",
                "task": "noncircular_semantic_retrieval",
                "metadata_filter": {}, "relevance_def": SEMANTIC_FACET,
                "coupling": "none", "difficulty": "nofilter",
                "positive_count": len(sem_ids), "positive_count_semantic": len(sem_ids),
            })
            qrels_strict += [{"query_id": qid, "target_id": c, "target_type": "clip", "relevance": 3} for c in sem_ids]
            qrels_sem += [{"query_id": qid, "target_id": c, "target_type": "clip", "relevance": 3} for c in sem_ids]
            # (b) filtered variants on an INDEPENDENT facet
            for facet in FILTER_FACETS:
                if facet not in table.columns:
                    continue
                sub = table[table[SEMANTIC_FACET].eq(atype)]
                for v, n in sub[facet].value_counts().items():
                    if not v or n < 5:
                        continue
                    strict_ids = sub.loc[sub[facet].eq(v), "clip_id"].tolist()
                    qn += 1
                    qid = f"vru2:{facet}:{qn:04d}"
                    queries.append({
                        "query_id": qid, "dataset_id": DATASET_ID,
                        "query_text": (f"Find videos where the accident type is {atype}, "
                                       f"restricted to {facet.replace('_', ' ')} = {v}."),
                        "task": "noncircular_filtered_retrieval",
                        "metadata_filter": {facet: v},
                        "relevance_def": SEMANTIC_FACET,
                        "coupling": f"V={coupling.get(facet)}",
                        "difficulty": facet,
                        "positive_count": len(strict_ids),
                        "positive_count_semantic": len(sem_ids),
                    })
                    qrels_strict += [{"query_id": qid, "target_id": c, "target_type": "clip", "relevance": 3} for c in strict_ids]
                    qrels_sem += [{"query_id": qid, "target_id": c, "target_type": "clip", "relevance": 3} for c in sem_ids]
        self._coupling = coupling
        return queries, pd.DataFrame(qrels_strict), pd.DataFrame(qrels_sem)

    def build(self, overwrite: bool = False):
        validation = self.validate_raw()
        if not validation["valid"]:
            raise RuntimeError(f"VRU raw validation failed: {validation}")
        out = self.output_dir
        out.mkdir(parents=True, exist_ok=True)
        if any(out.iterdir()) and not overwrite:
            raise FileExistsError(f"{out} not empty; use --overwrite")
        captions = self._load_caption_rows()
        vqa = self._load_vqa_rows()
        clips = self._build_clips(captions, vqa)
        documents = self._build_documents(captions, vqa)
        metadata = self._build_metadata(vqa)
        queries, qrels, qrels_sem = self._build_queries_and_qrels(metadata)

        clips.to_parquet(out / "clips.parquet", index=False)
        documents.to_parquet(out / "documents.parquet", index=False)
        metadata.to_parquet(out / "metadata.parquet", index=False)
        with (out / "queries.jsonl").open("w", encoding="utf-8") as f:
            for q in queries:
                f.write(json.dumps(q, ensure_ascii=False) + "\n")
        qrels.to_csv(out / "qrels.tsv", sep="\t", index=False)
        qrels_sem.to_csv(out / "qrels_semantic.tsv", sep="\t", index=False)

        # audit
        doc_types = documents["doc_type"].value_counts().to_dict()
        audit = {
            "assertions": {
                "no_facet_statement_docs": {"pass": "vqa_facet_statement" not in doc_types,
                                            "doc_types": doc_types},
                "filter_never_semantic": {"pass": all(
                    SEMANTIC_FACET not in q["metadata_filter"] for q in queries)},
                "dual_qrels_present": {"pass": len(qrels) > 0 and len(qrels_sem) > 0},
            },
            "coupling_v_accident_type_vs_filter": self._coupling,
            "counts": {"clips": len(clips), "documents": len(documents),
                       "queries": len(queries), "qrels_strict": len(qrels),
                       "qrels_semantic": len(qrels_sem)},
            "caveat": "both channels VQA-derived (same annotators) — weaker separation than 522 tri-source; coupling V reported per filter facet",
        }
        audit["overall_pass"] = all(a["pass"] for a in audit["assertions"].values())
        (out / "A9_noncircular_audit.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        return audit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset-root", type=Path,
                    default=PROJECT_ROOT / "Datasets")
    ap.add_argument("--output-root", type=Path,
                    default=PROJECT_ROOT / "Datasets" / "processed")
    ap.add_argument("--version", default="20260710_noncircular")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    adapter = VRUNonCircularAdapter(
        dataset_root=args.dataset_root, output_root=args.output_root,
        dataset_version=args.version)
    audit = adapter.build(overwrite=args.overwrite)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    print(f"[saved] {adapter.output_dir}")
    return 0 if audit["overall_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
