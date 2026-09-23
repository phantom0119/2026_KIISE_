#!/usr/bin/env python3
"""Run pgvector exact-search baselines for a canonical workload."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import psycopg
from pgvector.psycopg import register_vector
from psycopg import sql


PROJECT_ROOT = Path(__file__).resolve().parents[3]
SRC_ROOT = PROJECT_ROOT / "2026_KIISE" / "03_src"
sys.path.insert(0, str(SRC_ROOT))

from vlmdb_workload.io import load_canonical, write_json  # noqa: E402
from vlmdb_workload.metrics import evaluate_ranking  # noqa: E402


STRATEGIES = ["P2_pgvector_vector_only", "P4_pgvector_prefilter_vector"]


@dataclass(frozen=True)
class PgVectorRunResult:
    output_dir: Path
    table_prefix: str
    queries: int
    result_rows: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--canonical-root",
        type=Path,
        default=PROJECT_ROOT / "Datasets" / "processed" / "vru_accident" / "20260706" / "canonical",
    )
    parser.add_argument(
        "--embedding-root",
        type=Path,
        default=PROJECT_ROOT / "Datasets" / "processed" / "vru_accident" / "20260706" / "embeddings" / "bge-m3",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT
        / "Datasets"
        / "processed"
        / "vru_accident"
        / "20260706"
        / "results"
        / "vru_bgem3_pgvector_p2_p4",
    )
    parser.add_argument("--table-prefix", default=None)
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=5433)
    parser.add_argument("--dbname", default="vlmdb")
    parser.add_argument("--user", default="vlmdb")
    parser.add_argument("--password", default="vlmdb")
    parser.add_argument("--top-ks", default="1,5,10,20")
    parser.add_argument("--max-rank", type=int, default=100)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--reuse-tables", action="store_true")
    return parser.parse_args()


def safe_identifier(value: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()
    if not safe:
        raise ValueError(f"Cannot build safe SQL identifier from: {value}")
    if safe[0].isdigit():
        safe = f"t_{safe}"
    return safe[:48]


def default_table_prefix(canonical_root: Path, embedding_root: Path) -> str:
    dataset_id = canonical_root.parents[2].name
    version = canonical_root.parents[0].name
    model_id = embedding_root.name
    return safe_identifier(f"{dataset_id}_{version}_{model_id}")


def connect(args: argparse.Namespace) -> psycopg.Connection:
    conn = psycopg.connect(
        host=args.host,
        port=args.port,
        dbname=args.dbname,
        user=args.user,
        password=args.password,
    )
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    conn.commit()
    return conn


def table_names(prefix: str) -> dict[str, sql.Identifier]:
    return {
        "documents": sql.Identifier(f"{prefix}_documents"),
        "metadata": sql.Identifier(f"{prefix}_metadata"),
    }


def prepare_tables(
    conn: psycopg.Connection,
    prefix: str,
    documents: pd.DataFrame,
    metadata: pd.DataFrame,
    doc_embeddings: np.ndarray,
    *,
    overwrite: bool,
    reuse_tables: bool,
) -> dict[str, float]:
    names = table_names(prefix)
    dim = int(doc_embeddings.shape[1])
    timings: dict[str, float] = {}

    if overwrite and not reuse_tables:
        with conn.cursor() as cur:
            for name in names.values():
                cur.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(name))
        conn.commit()

    exists = conn.execute(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema='public' AND table_name=%s)",
        (f"{prefix}_documents",),
    ).fetchone()[0]
    if exists and reuse_tables:
        return {"table_load_sec": 0.0, "reused_tables": 1.0}
    if exists and not overwrite:
        raise FileExistsError(f"pgvector tables with prefix {prefix!r} already exist. Use --overwrite or --reuse-tables.")

    start = time.perf_counter()
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                """
                CREATE TABLE {} (
                  doc_id text PRIMARY KEY,
                  clip_id text NOT NULL,
                  doc_type text NOT NULL,
                  text text NOT NULL,
                  embedding vector({})
                )
                """
            ).format(names["documents"], sql.SQL(str(dim)))
        )
        cur.execute(
            sql.SQL(
                """
                CREATE TABLE {} (
                  clip_id text NOT NULL,
                  facet_name text NOT NULL,
                  facet_value text NOT NULL
                )
                """
            ).format(names["metadata"])
        )

        doc_rows = [
            (
                row["doc_id"],
                row["clip_id"],
                row["doc_type"],
                str(row["text"]),
                doc_embeddings[idx],
            )
            for idx, row in documents.reset_index(drop=True).iterrows()
        ]
        cur.executemany(
            sql.SQL("INSERT INTO {} (doc_id, clip_id, doc_type, text, embedding) VALUES (%s, %s, %s, %s, %s)").format(
                names["documents"]
            ),
            doc_rows,
        )
        metadata_rows = [
            (row["clip_id"], row["facet_name"], str(row["facet_value"]))
            for _, row in metadata.iterrows()
        ]
        cur.executemany(
            sql.SQL("INSERT INTO {} (clip_id, facet_name, facet_value) VALUES (%s, %s, %s)").format(names["metadata"]),
            metadata_rows,
        )
        cur.execute(sql.SQL("CREATE INDEX {} ON {} (clip_id)").format(sql.Identifier(f"{prefix}_documents_clip_idx"), names["documents"]))
        cur.execute(
            sql.SQL("CREATE INDEX {} ON {} (facet_name, facet_value, clip_id)").format(
                sql.Identifier(f"{prefix}_metadata_facet_idx"),
                names["metadata"],
            )
        )
    conn.commit()
    timings["table_load_sec"] = time.perf_counter() - start
    timings["reused_tables"] = 0.0
    return timings


def candidate_clips(conn: psycopg.Connection, prefix: str, filters: dict[str, Any]) -> list[str] | None:
    if not filters:
        return None
    names = table_names(prefix)
    current: set[str] | None = None
    with conn.cursor() as cur:
        for facet_name, facet_value in filters.items():
            rows = cur.execute(
                sql.SQL("SELECT clip_id FROM {} WHERE facet_name = %s AND facet_value = %s").format(names["metadata"]),
                (facet_name, str(facet_value)),
            ).fetchall()
            values = {row[0] for row in rows}
            current = values if current is None else current & values
            if not current:
                return []
    return sorted(current or [])


def pgvector_search(
    conn: psycopg.Connection,
    prefix: str,
    query_vector: np.ndarray,
    *,
    candidates: list[str] | None,
    max_rank: int,
) -> list[tuple[str, float]]:
    names = table_names(prefix)
    vector = np.asarray(query_vector, dtype=np.float32)
    with conn.cursor() as cur:
        if candidates == []:
            return []
        if candidates is None:
            rows = cur.execute(
                sql.SQL(
                    """
                    SELECT clip_id, max(1 - (embedding <=> %s)) AS score
                    FROM {}
                    GROUP BY clip_id
                    ORDER BY score DESC, clip_id ASC
                    LIMIT %s
                    """
                ).format(names["documents"]),
                (vector, max_rank),
            ).fetchall()
        else:
            rows = cur.execute(
                sql.SQL(
                    """
                    SELECT clip_id, max(1 - (embedding <=> %s)) AS score
                    FROM {}
                    WHERE clip_id = ANY(%s)
                    GROUP BY clip_id
                    ORDER BY score DESC, clip_id ASC
                    LIMIT %s
                    """
                ).format(names["documents"]),
                (vector, candidates, max_rank),
            ).fetchall()
    return [(row[0], float(row[1])) for row in rows]


def summarize_metrics(metrics_by_query: pd.DataFrame) -> pd.DataFrame:
    metric_cols = [
        col
        for col in metrics_by_query.columns
        if col.startswith("recall_at_") or col.startswith("hit_at_") or col in {"mrr", "ndcg_at_10"}
    ]
    rows = []
    for (strategy, difficulty), group in metrics_by_query.groupby(["strategy", "difficulty"], sort=False):
        row = {"strategy": strategy, "difficulty": difficulty, "queries": len(group)}
        row.update({col: group[col].mean() for col in metric_cols})
        rows.append(row)
    for strategy, group in metrics_by_query.groupby("strategy", sort=False):
        row = {"strategy": strategy, "difficulty": "all", "queries": len(group)}
        row.update({col: group[col].mean() for col in metric_cols})
        rows.append(row)
    return pd.DataFrame(rows)


def summarize_latency(metrics_by_query: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for strategy, group in metrics_by_query.groupby("strategy", sort=False):
        rows.append(
            {
                "strategy": strategy,
                "queries": len(group),
                "latency_mean_ms": group["latency_ms"].mean(),
                "latency_p50_ms": group["latency_ms"].quantile(0.50),
                "latency_p95_ms": group["latency_ms"].quantile(0.95),
            }
        )
    return pd.DataFrame(rows)


def write_summary_md(output_dir: Path, metrics_summary: pd.DataFrame, latency_summary: pd.DataFrame) -> None:
    all_rows = metrics_summary[metrics_summary["difficulty"].eq("all")].copy()
    metric_cols = ["recall_at_1", "recall_at_5", "recall_at_10", "recall_at_20", "mrr", "ndcg_at_10"]
    lines = [
        "# pgvector Retrieval Summary",
        "",
        f"created_at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Overall Metrics",
        "",
        "| strategy | recall_at_1 | recall_at_5 | recall_at_10 | recall_at_20 | mrr | ndcg_at_10 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for _, row in all_rows.iterrows():
        values = " | ".join(f"{row[col]:.4f}" for col in metric_cols)
        lines.append(f"| {row['strategy']} | {values} |")
    lines.extend(
        [
            "",
            "## Latency",
            "",
            "| strategy | mean ms | p50 ms | p95 ms |",
            "|---|---:|---:|---:|",
        ]
    )
    for _, row in latency_summary.iterrows():
        lines.append(
            f"| {row['strategy']} | {row['latency_mean_ms']:.3f} | {row['latency_p50_ms']:.3f} | {row['latency_p95_ms']:.3f} |"
        )
    output_dir.joinpath("summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(args: argparse.Namespace) -> PgVectorRunResult:
    top_ks = [int(value) for value in args.top_ks.split(",") if value.strip()]
    table_prefix = safe_identifier(args.table_prefix) if args.table_prefix else default_table_prefix(args.canonical_root, args.embedding_root)
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    if any(output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{output_dir} is not empty. Use --overwrite.")

    clips, documents, metadata, queries, qrels = load_canonical(args.canonical_root)
    doc_embeddings = np.load(args.embedding_root / "document_embeddings.npy").astype("float32")
    query_embeddings = np.load(args.embedding_root / "query_embeddings.npy").astype("float32")
    embedding_manifest = json.loads((args.embedding_root / "embedding_manifest.json").read_text(encoding="utf-8"))

    positives_by_query = {
        query_id: set(group["target_id"])
        for query_id, group in qrels.groupby("query_id", sort=False)
    }

    conn = connect(args)
    table_timings = prepare_tables(
        conn,
        table_prefix,
        documents,
        metadata,
        doc_embeddings,
        overwrite=args.overwrite,
        reuse_tables=args.reuse_tables,
    )

    result_rows: list[dict[str, Any]] = []
    metric_rows: list[dict[str, Any]] = []

    try:
        for query_pos, query in queries.reset_index(drop=True).iterrows():
            query_id = query["query_id"]
            positives = positives_by_query.get(query_id, set())
            filters = dict(query["metadata_filter"] or {})
            query_vector = query_embeddings[query_pos]

            per_strategy: dict[str, dict[str, Any]] = {}
            start = time.perf_counter()
            vector_ranking = pgvector_search(conn, table_prefix, query_vector, candidates=None, max_rank=args.max_rank)
            per_strategy["P2_pgvector_vector_only"] = {
                "ranking": vector_ranking,
                "latency_ms": (time.perf_counter() - start) * 1000.0,
            }

            start = time.perf_counter()
            candidates = candidate_clips(conn, table_prefix, filters)
            prefilter_ranking = pgvector_search(conn, table_prefix, query_vector, candidates=candidates, max_rank=args.max_rank)
            per_strategy["P4_pgvector_prefilter_vector"] = {
                "ranking": prefilter_ranking,
                "latency_ms": (time.perf_counter() - start) * 1000.0,
            }

            for strategy, payload in per_strategy.items():
                ranking = [clip_id for clip_id, _score in payload["ranking"]]
                metrics = evaluate_ranking(ranking, positives, top_ks)
                metric_rows.append(
                    {
                        "strategy": strategy,
                        "query_id": query_id,
                        "difficulty": query["difficulty"],
                        "positive_count": int(query["positive_count"]),
                        "latency_ms": payload["latency_ms"],
                        **metrics,
                    }
                )
                for rank, (clip_id, score) in enumerate(payload["ranking"], start=1):
                    result_rows.append(
                        {
                            "strategy": strategy,
                            "query_id": query_id,
                            "rank": rank,
                            "clip_id": clip_id,
                            "score": score,
                            "is_relevant": clip_id in positives,
                        }
                    )
    finally:
        conn.close()

    results = pd.DataFrame(result_rows)
    metrics_by_query = pd.DataFrame(metric_rows)
    metrics_summary = summarize_metrics(metrics_by_query)
    latency_summary = summarize_latency(metrics_by_query)

    results.to_parquet(output_dir / "retrieval_results.parquet", index=False)
    metrics_by_query.to_parquet(output_dir / "metrics_by_query.parquet", index=False)
    metrics_summary.to_csv(output_dir / "metrics_summary.csv", index=False)
    latency_summary.to_csv(output_dir / "latency_summary.csv", index=False)
    write_json(
        output_dir / "run_manifest.json",
        {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "canonical_root": str(args.canonical_root),
            "embedding_root": str(args.embedding_root),
            "output_dir": str(output_dir),
            "table_prefix": table_prefix,
            "embedding_manifest": embedding_manifest,
            "strategies": STRATEGIES,
            "top_ks": top_ks,
            "max_rank": args.max_rank,
            "pgvector_backend": "PostgreSQL 16 + pgvector exact cosine search",
            "table_timings": table_timings,
            "counts": {
                "clips": int(len(clips)),
                "documents": int(len(documents)),
                "queries": int(len(queries)),
                "qrels": int(len(qrels)),
                "result_rows": int(len(results)),
            },
        },
    )
    write_summary_md(output_dir, metrics_summary, latency_summary)

    return PgVectorRunResult(output_dir=output_dir, table_prefix=table_prefix, queries=len(queries), result_rows=len(results))


def main() -> int:
    args = parse_args()
    result = run(args)
    print(f"output_dir={result.output_dir}")
    print(f"table_prefix={result.table_prefix}")
    print(f"queries={result.queries}")
    print(f"result_rows={result.result_rows}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
