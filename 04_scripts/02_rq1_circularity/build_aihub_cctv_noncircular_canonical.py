#!/usr/bin/env python3
"""Pillar A9(2): repaired (non-circular) AI Hub intelligent-CCTV workload.

The v1 canonical (20260706) produced the manuscript's PERFECT scores
(Table 6: B3/B4 MRR = nDCG@10 = 1.0000) via two circular mechanisms:
  F2  corpus docs 'event_statement'/'temporal_statement' restate the
      event_class label verbatim, and queries use the same label strings
  F1  metadata_filter facets are a subset of the qrel-defining facets

v2 (this builder; v1 untouched for the collapse table):
  documents  = Korean event_caption ONLY (human scene description)   [F2 fix]
  relevance  = event_class membership (semantic axis)                [F4 fix]
  filter     = night / place_type (operational axis, never event_*)  [F1 fix]
  dual qrels = qrels.tsv (strict: class AND filter) +
               qrels_semantic.tsv (class only; prefilter unguaranteed)

Note: captions are Korean; bge-m3 is multilingual so B2 remains meaningful,
and this matches the manuscript's own ko-encoder track (§6.10).

Run:
  Datasets/envs/kiise-vlmdb/bin/python \
    2026_KIISE/04_scripts/build_aihub_cctv_noncircular_canonical.py
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "03_src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.adapters.aihub_intelligent_cctv import (  # noqa: E402
    AIHubIntelligentCCTVAdapter, DATASET_ID, EVENT_CLASS_TEXT, EVENT_CLASS_KO)

FILTER_FACETS = ["night", "place_type"]      # operational axis
SEMANTIC_FACET = "event_class"               # relevance axis


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


class AIHubCCTVNonCircularAdapter(AIHubIntelligentCCTVAdapter):
    """Reads RAW pairs from the v1 raw version but writes a NEW canonical version."""

    def __init__(self, dataset_root: Path, output_root: Path,
                 dataset_version: str, raw_version: str = "20260706") -> None:
        super().__init__(dataset_root, output_root, dataset_version)
        # decouple: raw stays at the ingested version, output gets the new label
        self.raw_root = dataset_root / "raw" / DATASET_ID / raw_version
        self.pair_manifest = self.raw_root / "clip_pairs.csv"

    def _build_documents(self, records: pd.DataFrame) -> pd.DataFrame:
        rows = [{
            "doc_id": f"{r['clip_id']}:doc:event_caption",
            "clip_id": r["clip_id"], "dataset_id": DATASET_ID,
            "doc_type": "event_caption", "text": r["event_caption"],
            "lang": "ko", "source": r["label_path"],
        } for r in records.to_dict("records")]
        return pd.DataFrame(rows).drop_duplicates("doc_id").reset_index(drop=True)

    def _build_queries_and_qrels(self, metadata: pd.DataFrame):
        table = (metadata.pivot_table(index="clip_id", columns="facet_name",
                                      values="facet_value", aggfunc="first")
                 .reset_index().fillna(""))
        queries, qrels_strict, qrels_sem = [], [], []
        coupling = {f: round(cramers_v(table[SEMANTIC_FACET], table[f]), 3)
                    for f in FILTER_FACETS if f in table.columns}
        qn = 0
        for ec, support in table[SEMANTIC_FACET].value_counts().items():
            if not ec or support < 5:
                continue
            nl = f"{EVENT_CLASS_TEXT.get(ec, ec)} ({EVENT_CLASS_KO.get(ec, ec)})"
            sem_ids = table.loc[table[SEMANTIC_FACET].eq(ec), "clip_id"].tolist()
            qn += 1
            qid = f"acctv2:nofilter:{qn:04d}"
            queries.append({
                "query_id": qid, "dataset_id": DATASET_ID,
                "query_text": f"Find CCTV videos showing a {nl} event.",
                "task": "noncircular_semantic_retrieval",
                "metadata_filter": {}, "relevance_def": SEMANTIC_FACET,
                "coupling": "none", "difficulty": "nofilter",
                "positive_count": len(sem_ids), "positive_count_semantic": len(sem_ids),
            })
            qrels_strict += [{"query_id": qid, "target_id": c, "target_type": "clip", "relevance": 3} for c in sem_ids]
            qrels_sem += [{"query_id": qid, "target_id": c, "target_type": "clip", "relevance": 3} for c in sem_ids]
            for facet in FILTER_FACETS:
                if facet not in table.columns:
                    continue
                sub = table[table[SEMANTIC_FACET].eq(ec)]
                for v, n in sub[facet].value_counts().items():
                    if not v or n < 5:
                        continue
                    strict_ids = sub.loc[sub[facet].eq(v), "clip_id"].tolist()
                    cond = ("at night" if (facet, v) == ("night", "true")
                            else "in daytime" if (facet, v) == ("night", "false")
                            else f"at {v} locations")
                    qn += 1
                    qid = f"acctv2:{facet}:{qn:04d}"
                    queries.append({
                        "query_id": qid, "dataset_id": DATASET_ID,
                        "query_text": f"Find CCTV videos showing a {nl} event {cond}.",
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
            raise RuntimeError(f"raw validation failed: {validation}")
        out = self.output_dir
        out.mkdir(parents=True, exist_ok=True)
        if any(out.iterdir()) and not overwrite:
            raise FileExistsError(f"{out} not empty; use --overwrite")
        records = self._load_records()
        clips = self._build_clips(records)
        documents = self._build_documents(records)
        metadata = self._build_metadata(records)
        queries, qrels, qrels_sem = self._build_queries_and_qrels(metadata)

        clips.to_parquet(out / "clips.parquet", index=False)
        documents.to_parquet(out / "documents.parquet", index=False)
        metadata.to_parquet(out / "metadata.parquet", index=False)
        with (out / "queries.jsonl").open("w", encoding="utf-8") as f:
            for q in queries:
                f.write(json.dumps(q, ensure_ascii=False) + "\n")
        qrels.to_csv(out / "qrels.tsv", sep="\t", index=False)
        qrels_sem.to_csv(out / "qrels_semantic.tsv", sep="\t", index=False)

        doc_types = documents["doc_type"].value_counts().to_dict()
        audit = {
            "assertions": {
                "caption_only_corpus": {"pass": set(doc_types) == {"event_caption"},
                                        "doc_types": doc_types},
                "filter_never_semantic": {"pass": all(
                    not (set(q["metadata_filter"]) & {"event_class", "event_class_text",
                                                      "event_slug", "event_name", "event_group"})
                    for q in queries)},
                "dual_qrels_present": {"pass": len(qrels) > 0 and len(qrels_sem) > 0},
            },
            "coupling_v_event_class_vs_filter": self._coupling,
            "counts": {"clips": len(clips), "documents": len(documents),
                       "queries": len(queries), "qrels_strict": len(qrels),
                       "qrels_semantic": len(qrels_sem)},
        }
        audit["overall_pass"] = all(a["pass"] for a in audit["assertions"].values())
        (out / "A9_noncircular_audit.json").write_text(
            json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        return audit


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--version", default="20260710_noncircular")
    ap.add_argument("--raw-version", default="20260706")
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    adapter = AIHubCCTVNonCircularAdapter(
        dataset_root=PROJECT_ROOT / "Datasets",
        output_root=PROJECT_ROOT / "Datasets" / "processed",
        dataset_version=args.version, raw_version=args.raw_version)
    audit = adapter.build(overwrite=args.overwrite)
    print(json.dumps(audit, ensure_ascii=False, indent=2))
    print(f"[saved] {adapter.output_dir}")
    return 0 if audit["overall_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
