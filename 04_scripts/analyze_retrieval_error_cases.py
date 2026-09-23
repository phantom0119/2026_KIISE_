#!/usr/bin/env python3
"""Generate query-level error analysis for the retrieval experiments."""

from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "03_src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.io import read_jsonl  # noqa: E402


METRIC_COLUMNS = [
    "recall_at_1",
    "recall_at_5",
    "recall_at_10",
    "recall_at_20",
    "mrr",
    "ndcg_at_10",
    "hit_at_10",
    "latency_ms",
]

FAISS_STRATEGIES = [
    "B0_metadata_only",
    "B1_bm25_only",
    "B2_vector_only",
    "B3_vector_postfilter",
    "B4_prefilter_vector",
    "B5_hybrid",
]

PGVECTOR_STRATEGIES = [
    "P2_pgvector_vector_only",
    "P4_pgvector_prefilter_vector",
]

DISPLAY_STRATEGIES = [
    "B1_bm25_only",
    "B2_vector_only",
    "B3_vector_postfilter",
    "B4_prefilter_vector",
    "B5_hybrid",
]

STRATEGY_NAMES = {
    "B0_metadata_only": "B0 metadata",
    "B1_bm25_only": "B1 BM25",
    "B2_vector_only": "B2 vector",
    "B3_vector_postfilter": "B3 postfilter",
    "B4_prefilter_vector": "B4 prefilter",
    "B5_hybrid": "B5 hybrid",
    "P2_pgvector_vector_only": "P2 pgvector vector",
    "P4_pgvector_prefilter_vector": "P4 pgvector prefilter",
}

IMPORTANT_FACETS = [
    "accident_type",
    "location",
    "road_type",
    "weather_light",
    "accident_reason",
    "prevention_method",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=PROJECT_ROOT / "Datasets" / "processed" / "vru_accident" / "20260706" / "canonical",
    )
    parser.add_argument(
        "--faiss-result-root",
        type=Path,
        default=PROJECT_ROOT
        / "Datasets"
        / "processed"
        / "vru_accident"
        / "20260706"
        / "results"
        / "vru_bgem3_faiss_b0_b5",
    )
    parser.add_argument(
        "--pgvector-result-root",
        type=Path,
        default=PROJECT_ROOT
        / "Datasets"
        / "processed"
        / "vru_accident"
        / "20260706"
        / "results"
        / "vru_bgem3_pgvector_p2_p4",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260706" / "error_analysis",
    )
    parser.add_argument("--cases-per-type", type=int, default=3)
    parser.add_argument("--top-results", type=int, default=5)
    return parser.parse_args()


def json_compact(value: Any) -> str:
    if isinstance(value, float) and math.isnan(value):
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def truncate(text: Any, limit: int = 180) -> str:
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."


def markdown_table(rows: list[dict[str, Any]], columns: list[str]) -> str:
    if not rows:
        return "_No rows._\n"
    header = "| " + " | ".join(columns) + " |"
    sep = "| " + " | ".join(["---"] * len(columns)) + " |"
    body = []
    for row in rows:
        values = []
        for col in columns:
            value = row.get(col, "")
            if isinstance(value, float):
                value = f"{value:.4f}"
            value = str(value).replace("\n", " ").replace("|", "\\|")
            values.append(value)
        body.append("| " + " | ".join(values) + " |")
    return "\n".join([header, sep, *body]) + "\n"


def load_queries(canonical_root: Path) -> pd.DataFrame:
    queries = pd.DataFrame(read_jsonl(canonical_root / "queries.jsonl"))
    for col in ["metadata_filter", "semantic_filter", "qrel_filter"]:
        if col not in queries:
            queries[col] = [{} for _ in range(len(queries))]
    queries["metadata_filter_text"] = queries["metadata_filter"].map(json_compact)
    queries["semantic_filter_text"] = queries["semantic_filter"].map(json_compact)
    queries["qrel_filter_text"] = queries["qrel_filter"].map(json_compact)
    return queries


def load_metric_wide(metrics_path: Path, strategies: list[str]) -> pd.DataFrame:
    metrics = pd.read_parquet(metrics_path)
    metrics = metrics[metrics["strategy"].isin(strategies)].copy()
    index_cols = ["query_id", "difficulty", "positive_count"]
    wide = metrics.pivot_table(index=index_cols, columns="strategy", values=METRIC_COLUMNS, aggfunc="first")
    wide.columns = [f"{strategy}__{metric}" for metric, strategy in wide.columns]
    return wide.reset_index()


def add_query_deltas(wide: pd.DataFrame) -> pd.DataFrame:
    out = wide.copy()
    pairs = [
        ("B4_prefilter_vector", "B2_vector_only", "b4_minus_b2"),
        ("B4_prefilter_vector", "B3_vector_postfilter", "b4_minus_b3"),
        ("B5_hybrid", "B4_prefilter_vector", "b5_minus_b4"),
        ("B1_bm25_only", "B2_vector_only", "b1_minus_b2"),
        ("B2_vector_only", "B1_bm25_only", "b2_minus_b1"),
    ]
    for left, right, prefix in pairs:
        for metric in ["recall_at_10", "recall_at_20", "mrr", "ndcg_at_10", "hit_at_10", "latency_ms"]:
            lcol = f"{left}__{metric}"
            rcol = f"{right}__{metric}"
            if lcol in out and rcol in out:
                out[f"{prefix}__{metric}"] = out[lcol] - out[rcol]
    return out


def summarize_by_difficulty(query_wide: pd.DataFrame) -> pd.DataFrame:
    rows = []
    difficulty_order = ["weak", "medium", "strong"]
    for difficulty in difficulty_order:
        group = query_wide[query_wide["difficulty"].eq(difficulty)]
        if group.empty:
            continue
        row: dict[str, Any] = {
            "difficulty": difficulty,
            "queries": len(group),
            "avg_positive_count": group["positive_count"].mean(),
        }
        for strategy in FAISS_STRATEGIES:
            for metric in ["recall_at_10", "ndcg_at_10", "mrr", "latency_ms"]:
                row[f"{strategy}__{metric}"] = group[f"{strategy}__{metric}"].mean()
        rows.append(row)
    return pd.DataFrame(rows)


def build_metadata_lookup(metadata: pd.DataFrame) -> dict[str, dict[str, str]]:
    wide = metadata.pivot_table(index="clip_id", columns="facet_name", values="facet_value", aggfunc="first")
    return wide.fillna("").to_dict(orient="index")


def build_caption_lookup(documents: pd.DataFrame) -> dict[str, str]:
    docs = documents.copy()
    dense = docs[docs["doc_type"].eq("dense_caption")]
    if dense.empty:
        dense = docs
    dense = dense.drop_duplicates("clip_id", keep="first")
    return dict(zip(dense["clip_id"], dense["text"], strict=False))


def metadata_summary(metadata_lookup: dict[str, dict[str, str]], clip_id: str) -> str:
    values = metadata_lookup.get(clip_id, {})
    parts = []
    for facet in IMPORTANT_FACETS:
        value = values.get(facet)
        if value:
            parts.append(f"{facet}={truncate(value, 55)}")
    return "; ".join(parts)


def query_metric_row(row: pd.Series) -> list[dict[str, Any]]:
    rows = []
    for strategy in DISPLAY_STRATEGIES:
        rows.append(
            {
                "strategy": STRATEGY_NAMES[strategy],
                "R@10": row.get(f"{strategy}__recall_at_10", 0.0),
                "Hit@10": row.get(f"{strategy}__hit_at_10", 0.0),
                "MRR": row.get(f"{strategy}__mrr", 0.0),
                "nDCG@10": row.get(f"{strategy}__ndcg_at_10", 0.0),
                "latency_ms": row.get(f"{strategy}__latency_ms", 0.0),
            }
        )
    return rows


def top_result_rows(
    retrieval: pd.DataFrame,
    query_id: str,
    strategy: str,
    metadata_lookup: dict[str, dict[str, str]],
    caption_lookup: dict[str, str],
    top_n: int,
) -> list[dict[str, Any]]:
    subset = retrieval[retrieval["query_id"].eq(query_id) & retrieval["strategy"].eq(strategy)].sort_values("rank")
    rows = []
    for item in subset.head(top_n).itertuples(index=False):
        rows.append(
            {
                "rank": int(item.rank),
                "rel": "Y" if bool(item.is_relevant) else "N",
                "clip_id": item.clip_id,
                "score": float(item.score),
                "metadata": truncate(metadata_summary(metadata_lookup, item.clip_id), 220),
                "caption": truncate(caption_lookup.get(item.clip_id, ""), 220),
            }
        )
    return rows


def select_cases(query_wide: pd.DataFrame, cases_per_type: int) -> pd.DataFrame:
    selectors: list[tuple[str, str, Callable[[pd.DataFrame], pd.DataFrame]]] = [
        (
            "vector_failure_recovered_by_prefilter",
            "B2 vector-only has no relevant item in top-10, but B4 metadata prefilter has a hit.",
            lambda df: df[
                df["B2_vector_only__hit_at_10"].eq(0.0)
                & df["B4_prefilter_vector__hit_at_10"].eq(1.0)
            ].sort_values(["b4_minus_b2__ndcg_at_10", "b4_minus_b2__recall_at_10"], ascending=False),
        ),
        (
            "prefilter_beats_postfilter",
            "B4 searches inside the filtered candidate set and outperforms B3 post-filtering.",
            lambda df: df[
                (df["b4_minus_b3__recall_at_10"] > 0.0)
                | (df["b4_minus_b3__ndcg_at_10"] > 0.05)
            ].sort_values(["b4_minus_b3__ndcg_at_10", "b4_minus_b3__recall_at_10"], ascending=False),
        ),
        (
            "hybrid_beats_prefilter",
            "B5 hybrid gains over B4, usually when lexical evidence complements dense retrieval.",
            lambda df: df[
                (df["b5_minus_b4__recall_at_20"] > 0.0)
                | (df["b5_minus_b4__mrr"] > 0.01)
            ].sort_values(["b5_minus_b4__mrr", "b5_minus_b4__recall_at_20"], ascending=False),
        ),
        (
            "lexical_beats_vector",
            "BM25 outperforms vector-only on the query, showing lexical baseline is necessary.",
            lambda df: df[
                df["b1_minus_b2__ndcg_at_10"] > 0.10
            ].sort_values(["b1_minus_b2__ndcg_at_10", "b1_minus_b2__recall_at_10"], ascending=False),
        ),
        (
            "remaining_hard_case",
            "Even B4 prefilter has no relevant item in top-10 or very low nDCG.",
            lambda df: df[
                df["B4_prefilter_vector__hit_at_10"].eq(0.0)
                | (df["B4_prefilter_vector__ndcg_at_10"] < 0.30)
            ].sort_values(["B4_prefilter_vector__ndcg_at_10", "B4_prefilter_vector__recall_at_10"], ascending=True),
        ),
        (
            "weak_query_control",
            "Weak queries have no metadata filter, so B2/B3/B4 should be almost identical.",
            lambda df: df[
                df["difficulty"].eq("weak")
                & (df["b4_minus_b2__ndcg_at_10"].abs() < 1e-9)
                & (df["b4_minus_b2__recall_at_10"].abs() < 1e-9)
            ].sort_values(["positive_count", "B4_prefilter_vector__ndcg_at_10"], ascending=[False, False]),
        ),
    ]

    frames = []
    used: set[str] = set()
    for case_type, description, selector in selectors:
        selected = selector(query_wide)
        selected = selected[~selected["query_id"].isin(used)].head(cases_per_type).copy()
        if selected.empty:
            continue
        selected.insert(0, "case_type", case_type)
        selected.insert(1, "case_description", description)
        selected.insert(2, "case_rank", range(1, len(selected) + 1))
        used.update(selected["query_id"].tolist())
        frames.append(selected)
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def backend_consistency(faiss_wide: pd.DataFrame, pg_wide: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    merged = faiss_wide.merge(pg_wide, on=["query_id", "difficulty", "positive_count"], how="inner")
    comparisons = [
        ("P2_pgvector_vector_only", "B2_vector_only", "p2_minus_b2"),
        ("P4_pgvector_prefilter_vector", "B4_prefilter_vector", "p4_minus_b4"),
    ]
    rows = []
    detail = merged[["query_id", "difficulty", "positive_count"]].copy()
    for left, right, prefix in comparisons:
        for metric in ["recall_at_10", "recall_at_20", "mrr", "ndcg_at_10", "hit_at_10", "latency_ms"]:
            lcol = f"{left}__{metric}"
            rcol = f"{right}__{metric}"
            diff_col = f"{prefix}__{metric}"
            detail[diff_col] = merged[lcol] - merged[rcol]
            rows.append(
                {
                    "comparison": f"{STRATEGY_NAMES[left]} vs {STRATEGY_NAMES[right]}",
                    "metric": metric,
                    "mean_diff": detail[diff_col].mean(),
                    "mean_abs_diff": detail[diff_col].abs().mean(),
                    "max_abs_diff": detail[diff_col].abs().max(),
                }
            )
    return pd.DataFrame(rows), detail


def aggregate_failure_modes(query_wide: pd.DataFrame) -> pd.DataFrame:
    rows = []
    definitions = [
        (
            "B2 top-10 miss recovered by B4",
            query_wide["B2_vector_only__hit_at_10"].eq(0.0)
            & query_wide["B4_prefilter_vector__hit_at_10"].eq(1.0),
        ),
        (
            "B4 beats B3 in Recall@10",
            query_wide["b4_minus_b3__recall_at_10"] > 0.0,
        ),
        (
            "B5 beats B4 in Recall@20",
            query_wide["b5_minus_b4__recall_at_20"] > 0.0,
        ),
        (
            "BM25 beats vector by nDCG@10 > 0.10",
            query_wide["b1_minus_b2__ndcg_at_10"] > 0.10,
        ),
        (
            "B4 still misses top-10",
            query_wide["B4_prefilter_vector__hit_at_10"].eq(0.0),
        ),
    ]
    for name, mask in definitions:
        subset = query_wide[mask]
        rows.append(
            {
                "mode": name,
                "queries": len(subset),
                "share": len(subset) / len(query_wide) if len(query_wide) else 0.0,
                "weak": int(subset["difficulty"].eq("weak").sum()) if not subset.empty else 0,
                "medium": int(subset["difficulty"].eq("medium").sum()) if not subset.empty else 0,
                "strong": int(subset["difficulty"].eq("strong").sum()) if not subset.empty else 0,
            }
        )
    return pd.DataFrame(rows)


def write_summary(
    output_dir: Path,
    query_wide: pd.DataFrame,
    difficulty_summary: pd.DataFrame,
    failure_modes: pd.DataFrame,
    backend_summary: pd.DataFrame,
    case_index: pd.DataFrame,
    retrieval: pd.DataFrame,
    metadata_lookup: dict[str, dict[str, str]],
    caption_lookup: dict[str, str],
    top_results: int,
) -> None:
    lines: list[str] = [
        "# Retrieval Error Case Analysis",
        "",
        f"created_at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Main Findings",
        "",
    ]

    b2 = query_wide["B2_vector_only__ndcg_at_10"].mean()
    b4 = query_wide["B4_prefilter_vector__ndcg_at_10"].mean()
    b5 = query_wide["B5_hybrid__ndcg_at_10"].mean()
    recovered = int(
        (
            query_wide["B2_vector_only__hit_at_10"].eq(0.0)
            & query_wide["B4_prefilter_vector__hit_at_10"].eq(1.0)
        ).sum()
    )
    b4_beats_b3 = int((query_wide["b4_minus_b3__recall_at_10"] > 0.0).sum())
    b4_misses = int(query_wide["B4_prefilter_vector__hit_at_10"].eq(0.0).sum())

    lines.extend(
        [
            f"- B4 metadata prefilter improves mean nDCG@10 from B2 vector-only `{b2:.4f}` to `{b4:.4f}`.",
            f"- B5 hybrid reaches mean nDCG@10 `{b5:.4f}`, but B4 is simpler and has lower latency in the current run.",
            f"- B4 recovers `{recovered}` queries where B2 had no relevant item in top-10.",
            f"- B4 has higher Recall@10 than B3 postfilter on `{b4_beats_b3}` queries.",
            f"- B4 still misses top-10 on `{b4_misses}` queries; these are the main qualitative failure cases.",
            "",
            "## Failure Mode Counts",
            "",
            markdown_table(
                failure_modes.to_dict(orient="records"),
                ["mode", "queries", "share", "weak", "medium", "strong"],
            ),
            "## Difficulty Summary",
            "",
        ]
    )

    difficulty_rows = []
    for row in difficulty_summary.to_dict(orient="records"):
        difficulty_rows.append(
            {
                "difficulty": row["difficulty"],
                "queries": int(row["queries"]),
                "avg_pos": row["avg_positive_count"],
                "B2_R@10": row.get("B2_vector_only__recall_at_10", 0.0),
                "B4_R@10": row.get("B4_prefilter_vector__recall_at_10", 0.0),
                "B2_nDCG": row.get("B2_vector_only__ndcg_at_10", 0.0),
                "B4_nDCG": row.get("B4_prefilter_vector__ndcg_at_10", 0.0),
                "B4_latency": row.get("B4_prefilter_vector__latency_ms", 0.0),
            }
        )
    lines.extend(
        [
            markdown_table(
                difficulty_rows,
                ["difficulty", "queries", "avg_pos", "B2_R@10", "B4_R@10", "B2_nDCG", "B4_nDCG", "B4_latency"],
            ),
            "## pgvector Consistency",
            "",
            markdown_table(
                backend_summary.to_dict(orient="records"),
                ["comparison", "metric", "mean_diff", "mean_abs_diff", "max_abs_diff"],
            ),
            "## Representative Cases",
            "",
        ]
    )

    for item in case_index.to_dict(orient="records"):
        query_id = item["query_id"]
        lines.extend(
            [
                f"### {item['case_type']} #{int(item['case_rank'])}: `{query_id}`",
                "",
                item["case_description"],
                "",
                f"- difficulty: `{item['difficulty']}`",
                f"- positives: `{int(item['positive_count'])}`",
                f"- query: {item['query_text']}",
                f"- semantic_filter: `{item['semantic_filter_text']}`",
                f"- metadata_filter: `{item['metadata_filter_text']}`",
                "",
                "Metrics:",
                "",
                markdown_table(
                    query_metric_row(pd.Series(item)),
                    ["strategy", "R@10", "Hit@10", "MRR", "nDCG@10", "latency_ms"],
                ),
            ]
        )
        for strategy in ["B2_vector_only", "B4_prefilter_vector", "B5_hybrid"]:
            lines.extend(
                [
                    f"Top-{top_results} results for {STRATEGY_NAMES[strategy]}:",
                    "",
                    markdown_table(
                        top_result_rows(
                            retrieval,
                            query_id,
                            strategy,
                            metadata_lookup,
                            caption_lookup,
                            top_results,
                        ),
                        ["rank", "rel", "clip_id", "score", "metadata", "caption"],
                    ),
                    "",
                ]
            )
    (output_dir / "summary.md").write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    queries = load_queries(args.canonical_root)
    documents = pd.read_parquet(args.canonical_root / "documents.parquet")
    metadata = pd.read_parquet(args.canonical_root / "metadata.parquet")
    faiss_retrieval = pd.read_parquet(args.faiss_result_root / "retrieval_results.parquet")

    faiss_wide = load_metric_wide(args.faiss_result_root / "metrics_by_query.parquet", FAISS_STRATEGIES)
    pg_wide = load_metric_wide(args.pgvector_result_root / "metrics_by_query.parquet", PGVECTOR_STRATEGIES)
    query_wide = add_query_deltas(faiss_wide).merge(
        queries[
            [
                "query_id",
                "query_text",
                "metadata_filter_text",
                "semantic_filter_text",
                "qrel_filter_text",
            ]
        ],
        on="query_id",
        how="left",
    )

    difficulty_summary = summarize_by_difficulty(query_wide)
    failure_modes = aggregate_failure_modes(query_wide)
    backend_summary, backend_detail = backend_consistency(faiss_wide, pg_wide)
    case_index = select_cases(query_wide, args.cases_per_type)

    metadata_lookup = build_metadata_lookup(metadata)
    caption_lookup = build_caption_lookup(documents)

    query_wide.to_csv(args.output_dir / "query_delta_summary.csv", index=False)
    difficulty_summary.to_csv(args.output_dir / "difficulty_error_summary.csv", index=False)
    failure_modes.to_csv(args.output_dir / "failure_mode_summary.csv", index=False)
    backend_summary.to_csv(args.output_dir / "pgvector_faiss_consistency_summary.csv", index=False)
    backend_detail.to_csv(args.output_dir / "pgvector_faiss_consistency_by_query.csv", index=False)
    case_index.to_csv(args.output_dir / "representative_case_index.csv", index=False)

    write_summary(
        output_dir=args.output_dir,
        query_wide=query_wide,
        difficulty_summary=difficulty_summary,
        failure_modes=failure_modes,
        backend_summary=backend_summary,
        case_index=case_index,
        retrieval=faiss_retrieval,
        metadata_lookup=metadata_lookup,
        caption_lookup=caption_lookup,
        top_results=args.top_results,
    )

    print(f"output_dir={args.output_dir}")
    print(f"queries={len(query_wide)}")
    print(f"case_rows={len(case_index)}")
    print(f"failure_modes={len(failure_modes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
