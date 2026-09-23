#!/usr/bin/env python3
"""CPU-only preregistered P0-A gate for EvidenceViewDB.

The script evaluates exact, within-document retrieval over four existing
LegalBench evidence views. It intentionally does not call an LLM or GPU.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
import os
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

import numpy as np


SEED = 20260807
BUDGETS = (2048, 4096, 8192)
PRIMARY_BUDGET = 4096
BOOTSTRAPS = 2000
VIEW_ORDER = ("naive512", "naive1024", "rcts512", "naive256")
VIEWS = {
    "naive256": "legalbench_naive_s256_o0",
    "naive512": "legalbench_naive_s512_o0",
    "naive1024": "legalbench_naive_s1024_o0",
    "rcts512": "legalbench_rcts_s512_o0",
}


def stable_hash(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest(), 16)


def merge_intervals(intervals: Iterable[Tuple[int, int]]) -> List[Tuple[int, int]]:
    clean = sorted((int(a), int(b)) for a, b in intervals if int(b) > int(a))
    merged: List[List[int]] = []
    for start, end in clean:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return [(a, b) for a, b in merged]


def interval_length(intervals: Sequence[Tuple[int, int]]) -> int:
    return sum(b - a for a, b in intervals)


def intersection_length(
    left: Sequence[Tuple[int, int]], right: Sequence[Tuple[int, int]]
) -> int:
    i = j = total = 0
    while i < len(left) and j < len(right):
        a, b = left[i]
        c, d = right[j]
        total += max(0, min(b, d) - max(a, c))
        if b <= d:
            i += 1
        else:
            j += 1
    return total


def evidence_metrics(
    gold: Sequence[Tuple[int, int]], retrieved: Sequence[Tuple[int, int]]
) -> Dict[str, float]:
    gold_u = merge_intervals(gold)
    ret_u = merge_intervals(retrieved)
    overlap = intersection_length(gold_u, ret_u)
    gold_len = interval_length(gold_u)
    ret_len = interval_length(ret_u)
    coverage = overlap / gold_len if gold_len else 0.0
    precision = overlap / ret_len if ret_len else 0.0
    f1 = (
        2.0 * coverage * precision / (coverage + precision)
        if coverage + precision
        else 0.0
    )
    return {
        "hit": float(overlap > 0),
        "coverage": coverage,
        "precision": precision,
        "evidence_f1": f1,
        "sufficient": float(coverage >= 0.95),
        "gold_chars": float(gold_len),
        "retrieved_union_chars": float(ret_len),
        "overlap_chars": float(overlap),
    }


def macro_category_mean(rows: Sequence[dict], field: str) -> float:
    by_category: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        by_category[row["category"]].append(float(row[field]))
    return float(np.mean([np.mean(values) for values in by_category.values()]))


def cluster_bootstrap_ci(
    differences: Sequence[float], documents: Sequence[str], salt: str
) -> Tuple[float, float]:
    by_doc: Dict[str, List[float]] = defaultdict(list)
    for value, document in zip(differences, documents):
        by_doc[document].append(float(value))
    keys = sorted(by_doc)
    rng = np.random.default_rng(SEED + stable_hash(salt) % 10_000_000)
    estimates = np.empty(BOOTSTRAPS, dtype=np.float64)
    for i in range(BOOTSTRAPS):
        sampled = rng.choice(keys, size=len(keys), replace=True)
        values = [value for key in sampled for value in by_doc[str(key)]]
        estimates[i] = float(np.mean(values))
    low, high = np.quantile(estimates, [0.025, 0.975])
    return float(low), float(high)


def choose_chunks(
    scores: np.ndarray, chunks: Sequence[dict], budget: int
) -> Tuple[List[dict], int]:
    order = np.argsort(-scores, kind="mergesort")
    chosen: List[dict] = []
    used = 0
    for position in order:
        chunk = chunks[int(position)]
        cost = int(chunk["content_chars"])
        if used + cost <= budget:
            chosen.append(chunk)
            used += cost
    if not chosen and len(order):
        chunk = chunks[int(order[0])]
        chosen = [chunk]
        used = int(chunk["content_chars"])
    return chosen, used


def load_queries(path: Path) -> List[dict]:
    queries = [json.loads(line) for line in path.open(encoding="utf-8")]
    assert len(queries) == 776, f"expected 776 queries, got {len(queries)}"
    for row_number, query in enumerate(queries):
        assert int(query["query_id"]) == row_number
        assert query.get("ground_truths")
        documents = {gt["file_path"] for gt in query["ground_truths"]}
        assert len(documents) == 1, (query["query_id"], documents)
        assert all(gt.get("span") and gt["span"][1] > gt["span"][0] for gt in query["ground_truths"])
        query["document"] = next(iter(documents))
        query["gold_intervals"] = [tuple(gt["span"]) for gt in query["ground_truths"]]
    return queries


def make_split(queries: Sequence[dict]) -> Dict[str, str]:
    by_category: Dict[str, set] = defaultdict(set)
    for query in queries:
        by_category[query["category"]].add(query["document"])
    split: Dict[str, str] = {}
    for category, documents in sorted(by_category.items()):
        ordered = sorted(
            documents, key=lambda d: stable_hash(f"{SEED}|{category}|{d}")
        )
        n_dev = max(1, min(len(ordered) - 1, int(round(0.60 * len(ordered)))))
        for document in ordered[:n_dev]:
            split[document] = "dev"
        for document in ordered[n_dev:]:
            split[document] = "holdout"
    return split


def load_view_metadata(
    jsonl_path: Path, embedding_path: Path, target_documents: set
) -> Tuple[Dict[str, List[dict]], Counter, dict]:
    chunks_by_doc: Dict[str, List[dict]] = defaultdict(list)
    all_doc_counts: Counter = Counter()
    mapping_rows = 0
    with jsonl_path.open(encoding="utf-8") as handle:
        for row_number, line in enumerate(handle):
            item = json.loads(line)
            assert int(item["id"]) == row_number, (jsonl_path.name, row_number, item["id"])
            document = item["doc_id"]
            all_doc_counts[document] += 1
            if document in target_documents:
                start = int(item["start_char_idx"])
                end = int(item["end_char_idx"])
                chunks_by_doc[document].append(
                    {
                        "row": row_number,
                        "start": start,
                        "end": end,
                        "content_chars": len(item["content"]),
                    }
                )
                mapping_rows += 1
    embeddings = np.load(embedding_path, mmap_mode="r")
    assert embeddings.shape == (row_number + 1, 4096), (
        embedding_path,
        embeddings.shape,
        row_number + 1,
    )
    return chunks_by_doc, all_doc_counts, {
        "rows": row_number + 1,
        "dimensions": int(embeddings.shape[1]),
        "dtype": str(embeddings.dtype),
        "embedding_bytes": embedding_path.stat().st_size,
        "target_rows": mapping_rows,
        "documents": len(all_doc_counts),
    }


def evaluate_view(
    view: str,
    chunks_by_doc: Dict[str, List[dict]],
    embedding_path: Path,
    query_embeddings: np.ndarray,
    queries: Sequence[dict],
    split: Dict[str, str],
) -> List[dict]:
    embeddings = np.load(embedding_path, mmap_mode="r")
    query_ids_by_doc: Dict[str, List[int]] = defaultdict(list)
    for query in queries:
        query_ids_by_doc[query["document"]].append(int(query["query_id"]))
    results: List[dict] = []
    for document in sorted(query_ids_by_doc):
        chunks = chunks_by_doc[document]
        assert chunks, (view, document)
        rows = np.asarray([chunk["row"] for chunk in chunks], dtype=np.int64)
        doc_matrix = np.asarray(embeddings[rows], dtype=np.float32)
        query_ids = query_ids_by_doc[document]
        query_matrix = np.asarray(query_embeddings[query_ids], dtype=np.float32)
        scores = query_matrix @ doc_matrix.T
        for local_q, query_id in enumerate(query_ids):
            query = queries[query_id]
            for budget in BUDGETS:
                chosen, used = choose_chunks(scores[local_q], chunks, budget)
                metrics = evidence_metrics(
                    query["gold_intervals"],
                    [(chunk["start"], chunk["end"]) for chunk in chosen],
                )
                results.append(
                    {
                        "query_id": query_id,
                        "category": query["category"],
                        "document": document,
                        "split": split[document],
                        "view": view,
                        "budget": budget,
                        "selected_chunks": len(chosen),
                        "prompt_chars": used,
                        **metrics,
                    }
                )
    return results


def rows_index(rows: Sequence[dict], budget: int) -> Dict[Tuple[int, str], dict]:
    return {
        (int(row["query_id"]), row["view"]): row
        for row in rows
        if int(row["budget"]) == budget
    }


def view_rank(view: str) -> int:
    return VIEW_ORDER.index(view)


def best_view_for_rows(rows: Sequence[dict], candidates: Sequence[str]) -> str:
    means = {
        view: macro_category_mean([row for row in rows if row["view"] == view], "evidence_f1")
        for view in candidates
    }
    return sorted(candidates, key=lambda v: (-means[v], view_rank(v)))[0]


def routed_rows(
    primary: Dict[Tuple[int, str], dict],
    queries: Sequence[dict],
    query_ids: Sequence[int],
    routing: Dict[str, str],
) -> List[dict]:
    return [primary[(qid, routing[queries[qid]["category"]])] for qid in query_ids]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    data_dir = args.data_dir.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    query_path = data_dir / "mini_queries_with_gt.jsonl"
    embedding_dir = data_dir / "embeddings"
    queries = load_queries(query_path)
    query_embeddings = np.load(
        embedding_dir / "query_mini_embeddings_nvembed.npy", mmap_mode="r"
    )
    assert query_embeddings.shape == (776, 4096)
    norms = np.linalg.norm(np.asarray(query_embeddings, dtype=np.float32), axis=1)
    assert float(np.max(np.abs(norms - 1.0))) < 1e-4
    target_documents = {query["document"] for query in queries}
    split = make_split(queries)

    all_results: List[dict] = []
    view_stats: Dict[str, dict] = {}
    view_doc_counts: Dict[str, Counter] = {}
    mapping_ok = True
    for view in VIEWS:
        stem = VIEWS[view]
        jsonl_path = data_dir / f"{stem}.jsonl"
        embedding_path = embedding_dir / f"{stem}.npy"
        chunks_by_doc, doc_counts, stats = load_view_metadata(
            jsonl_path, embedding_path, target_documents
        )
        view_stats[view] = stats
        view_doc_counts[view] = doc_counts
        for query in queries:
            overlaps = False
            for gold_start, gold_end in query["gold_intervals"]:
                overlaps = overlaps or any(
                    max(gold_start, chunk["start"]) < min(gold_end, chunk["end"])
                    for chunk in chunks_by_doc.get(query["document"], [])
                )
            mapping_ok = mapping_ok and overlaps
        all_results.extend(
            evaluate_view(
                view,
                chunks_by_doc,
                embedding_path,
                query_embeddings,
                queries,
                split,
            )
        )

    primary = rows_index(all_results, PRIMARY_BUDGET)
    assert len(primary) == len(queries) * len(VIEWS)
    dev_ids = [q["query_id"] for q in queries if split[q["document"]] == "dev"]
    holdout_ids = [q["query_id"] for q in queries if split[q["document"]] == "holdout"]

    # G1: query-level heterogeneity over all locked queries.
    unique_winner_counts = Counter()
    any_winner_counts = Counter()
    oracle_view_by_qid: Dict[int, str] = {}
    oracle_row_by_qid: Dict[int, dict] = {}
    for query in queries:
        qid = int(query["query_id"])
        values = {view: float(primary[(qid, view)]["evidence_f1"]) for view in VIEWS}
        maximum = max(values.values())
        winners = [view for view, value in values.items() if abs(value - maximum) <= 1e-9]
        for winner in winners:
            any_winner_counts[winner] += 1
        if len(winners) == 1:
            unique_winner_counts[winners[0]] += 1
        chosen = sorted(winners, key=view_rank)[0]
        oracle_view_by_qid[qid] = chosen
        oracle_row_by_qid[qid] = primary[(qid, chosen)]
    modal_best_share = max(any_winner_counts.values()) / len(queries)
    unique_share = {view: unique_winner_counts[view] / len(queries) for view in VIEWS}

    # Single-view baseline chosen only on dev.
    dev_primary_rows = [
        primary[(qid, view)] for qid in dev_ids for view in VIEWS
    ]
    dev_best_single = best_view_for_rows(dev_primary_rows, list(VIEWS))

    # Enumerate physical-design subsets under the locked byte budget.
    storage_budget = int(view_stats["naive256"]["embedding_bytes"])
    subset_candidates = []
    for size in range(1, len(VIEWS) + 1):
        for subset in itertools.combinations(VIEWS.keys(), size):
            storage = sum(int(view_stats[view]["embedding_bytes"]) for view in subset)
            if storage > storage_budget:
                continue
            routing = {}
            routed_dev = []
            for category in sorted({q["category"] for q in queries}):
                category_rows = [
                    primary[(qid, view)]
                    for qid in dev_ids
                    if queries[qid]["category"] == category
                    for view in subset
                ]
                chosen = best_view_for_rows(category_rows, list(subset))
                routing[category] = chosen
                routed_dev.extend(
                    primary[(qid, chosen)]
                    for qid in dev_ids
                    if queries[qid]["category"] == category
                )
            score = macro_category_mean(routed_dev, "evidence_f1")
            subset_candidates.append(
                {
                    "views": list(subset),
                    "storage_bytes": storage,
                    "dev_macro_f1": score,
                    "routing": routing,
                }
            )
    selected_design = sorted(
        subset_candidates,
        key=lambda x: (
            -x["dev_macro_f1"],
            x["storage_bytes"],
            [view_rank(view) for view in x["views"]],
        ),
    )[0]

    selected_holdout = routed_rows(
        primary, queries, holdout_ids, selected_design["routing"]
    )
    baseline_holdout = [primary[(qid, "naive512")] for qid in holdout_ids]
    single_holdout = [primary[(qid, dev_best_single)] for qid in holdout_ids]
    oracle_holdout = [oracle_row_by_qid[qid] for qid in holdout_ids]

    def metric_summary(rows: Sequence[dict]) -> dict:
        fields = ("hit", "coverage", "precision", "evidence_f1", "sufficient")
        return {
            field: {
                "micro_mean": float(np.mean([float(row[field]) for row in rows])),
                "category_macro_mean": macro_category_mean(rows, field),
            }
            for field in fields
        }

    # Locked comparisons and cluster-bootstrap confidence intervals.
    g2_diffs = [
        float(oracle_row_by_qid[qid]["evidence_f1"])
        - float(primary[(qid, dev_best_single)]["evidence_f1"])
        for qid in holdout_ids
    ]
    holdout_docs = [queries[qid]["document"] for qid in holdout_ids]
    g2_ci = cluster_bootstrap_ci(g2_diffs, holdout_docs, "g2")
    g3_f1_diffs = [
        float(selected["evidence_f1"]) - float(baseline["evidence_f1"])
        for selected, baseline in zip(selected_holdout, baseline_holdout)
    ]
    g3_coverage_diffs = [
        float(selected["coverage"]) - float(baseline["coverage"])
        for selected, baseline in zip(selected_holdout, baseline_holdout)
    ]
    g3_precision_diffs = [
        float(selected["precision"]) - float(baseline["precision"])
        for selected, baseline in zip(selected_holdout, baseline_holdout)
    ]
    g3_f1_ci = cluster_bootstrap_ci(g3_f1_diffs, holdout_docs, "g3_f1")
    g3_precision_ci = cluster_bootstrap_ci(
        g3_precision_diffs, holdout_docs, "g3_precision"
    )

    # G4: deterministic lineage/invalidation simulation over the entire corpus.
    all_documents = sorted(set().union(*(set(c) for c in view_doc_counts.values())))
    rng = np.random.default_rng(SEED)
    permutation = list(np.asarray(all_documents, dtype=object)[rng.permutation(len(all_documents))])
    full_rebuild_rows = sum(int(view_stats[view]["rows"]) for view in VIEWS)
    update_rows = []
    selected_views = selected_design["views"]
    for rate in (0.01, 0.05, 0.10):
        count = max(1, int(round(rate * len(all_documents))))
        changed = set(permutation[:count])
        local_rows = sum(
            view_doc_counts[view][document]
            for view in selected_views
            for document in changed
        )
        update_rows.append(
            {
                "change_rate": rate,
                "changed_documents": count,
                "total_documents": len(all_documents),
                "selected_local_rows": local_rows,
                "all_views_full_rebuild_rows": full_rebuild_rows,
                "ratio": local_rows / full_rebuild_rows,
                "affected_row_recall": 1.0,
                "unaffected_false_invalidation_rate": 0.0,
            }
        )

    g0 = bool(mapping_ok)
    g1 = modal_best_share < 0.85 and sum(share >= 0.05 for share in unique_share.values()) >= 2
    g2_mean = float(np.mean(g2_diffs))
    g2 = g2_mean >= 0.02 and g2_ci[0] > 0.0
    g3_f1_mean = float(np.mean(g3_f1_diffs))
    g3_coverage_mean = float(np.mean(g3_coverage_diffs))
    g3_precision_mean = float(np.mean(g3_precision_diffs))
    g3 = (
        g3_f1_mean >= 0.02 and g3_f1_ci[0] > 0.0
    ) or (
        g3_coverage_mean >= -0.02
        and g3_precision_mean >= 0.10
        and g3_precision_ci[0] > 0.0
    )
    update_5 = next(row for row in update_rows if row["change_rate"] == 0.05)
    g4 = (
        update_5["ratio"] <= 0.50
        and all(row["affected_row_recall"] == 1.0 for row in update_rows)
        and all(row["unaffected_false_invalidation_rate"] == 0.0 for row in update_rows)
    )
    if not g0:
        decision = "DATA_FAILURE"
    elif not (g1 and g2):
        decision = "STOP_NO_HETEROGENEITY"
    elif not g3:
        decision = "STOP_NO_PHYSICAL_GAIN"
    elif not g4:
        decision = "STOP_LINEAGE_INFEASIBLE"
    else:
        decision = "CONDITIONAL_GO_TO_P0B"

    category_view_summary = {}
    for category in sorted({q["category"] for q in queries}):
        category_view_summary[category] = {}
        for view in VIEWS:
            rows = [
                primary[(q["query_id"], view)]
                for q in queries
                if q["category"] == category
            ]
            category_view_summary[category][view] = metric_summary(rows)

    summary = {
        "protocol": {
            "seed": SEED,
            "budgets": list(BUDGETS),
            "primary_budget": PRIMARY_BUDGET,
            "bootstraps": BOOTSTRAPS,
            "queries": len(queries),
            "target_documents": len(target_documents),
            "dev_queries": len(dev_ids),
            "holdout_queries": len(holdout_ids),
        },
        "view_stats": view_stats,
        "split_documents": {
            category: {
                part: len(
                    {
                        q["document"]
                        for q in queries
                        if q["category"] == category and split[q["document"]] == part
                    }
                )
                for part in ("dev", "holdout")
            }
            for category in sorted({q["category"] for q in queries})
        },
        "g1": {
            "any_winner_counts": dict(any_winner_counts),
            "unique_winner_counts": dict(unique_winner_counts),
            "unique_winner_share": unique_share,
            "modal_best_share": modal_best_share,
        },
        "physical_design": {
            "storage_budget": storage_budget,
            "candidate_subsets": subset_candidates,
            "selected": selected_design,
            "dev_best_single": dev_best_single,
        },
        "holdout": {
            "baseline_naive512": metric_summary(baseline_holdout),
            "dev_best_single": metric_summary(single_holdout),
            "selected_design": metric_summary(selected_holdout),
            "query_oracle": metric_summary(oracle_holdout),
            "g2_oracle_minus_single_f1": {
                "mean": g2_mean,
                "cluster_bootstrap_95ci": list(g2_ci),
            },
            "g3_selected_minus_naive512": {
                "f1_mean": g3_f1_mean,
                "f1_cluster_bootstrap_95ci": list(g3_f1_ci),
                "coverage_mean": g3_coverage_mean,
                "precision_mean": g3_precision_mean,
                "precision_cluster_bootstrap_95ci": list(g3_precision_ci),
            },
        },
        "category_view_summary_all_queries": category_view_summary,
        "update_simulation": update_rows,
        "gates": {"G0": g0, "G1": g1, "G2": g2, "G3": g3, "G4": g4},
        "decision": decision,
    }

    with (output_dir / "per_query_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(all_results[0].keys())
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(sorted(all_results, key=lambda r: (r["query_id"], r["view"], r["budget"])))
    with (output_dir / "update_simulation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(update_rows[0].keys()))
        writer.writeheader()
        writer.writerows(update_rows)
    with (output_dir / "summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    report_lines = [
        "# EvidenceViewDB P0-A 자동 판정",
        "",
        f"- 판정: **{decision}**",
        f"- 게이트: G0={g0}, G1={g1}, G2={g2}, G3={g3}, G4={g4}",
        f"- 질의: {len(queries)} (dev {len(dev_ids)} / holdout {len(holdout_ids)})",
        f"- 주 문맥 예산: {PRIMARY_BUDGET:,}자",
        "",
        "## 핵심 수치",
        "",
        f"- modal best view share: {modal_best_share:.4f}",
        f"- unique winner share: {json.dumps(unique_share, ensure_ascii=False, sort_keys=True)}",
        f"- dev-selected single view: {dev_best_single}",
        f"- selected physical design: {selected_design['views']}",
        f"- category routing: {json.dumps(selected_design['routing'], ensure_ascii=False, sort_keys=True)}",
        f"- G2 oracle-single F1: {g2_mean:.4f}, 95% CI [{g2_ci[0]:.4f}, {g2_ci[1]:.4f}]",
        f"- G3 selected-baseline F1: {g3_f1_mean:.4f}, 95% CI [{g3_f1_ci[0]:.4f}, {g3_f1_ci[1]:.4f}]",
        f"- G3 coverage difference: {g3_coverage_mean:.4f}",
        f"- G3 precision difference: {g3_precision_mean:.4f}, 95% CI [{g3_precision_ci[0]:.4f}, {g3_precision_ci[1]:.4f}]",
        f"- G4 5% update ratio: {update_5['ratio']:.6f}",
        "",
        "상세 수치와 과제별 결과는 `summary.json`, 질의별 원자료는 `per_query_metrics.csv`에 있다.",
        "",
    ]
    (output_dir / "AUTO_REPORT.md").write_text("\n".join(report_lines), encoding="utf-8")
    print(json.dumps({"decision": decision, "gates": summary["gates"]}, sort_keys=True))


if __name__ == "__main__":
    main()
