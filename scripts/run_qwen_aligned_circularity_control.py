#!/usr/bin/env python3
"""Run C1/C2 circularity controls in the same Qwen space as the joint grid.

Clean captions, fully qrel-label-contaminated captions, and query texts are
re-embedded in one Qwen3-VL-Embedding-2B session.  C1 changes only candidate
selection; C2 changes only appended qrel-definition clauses in documents.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import torch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CANONICAL = Path(
    "/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/"
    "qwen35_9b/522/canonical"
)
DEFAULT_EMBEDDINGS = (
    PROJECT_ROOT
    / "Datasets"
    / "processed"
    / "aihub_522_intersection"
    / "20260710"
    / "embeddings_qwen3vl2b_unified_qwen35captions"
)
DEFAULT_QWEN_ROOT = PROJECT_ROOT / "Qwen3-VL-Embedding"
DEFAULT_MODEL = DEFAULT_QWEN_ROOT / "models" / "Qwen3-VL-Embedding-2B"
DEFAULT_OUTPUT = (
    PROJECT_ROOT
    / "2026_KIISE"
    / "paper_assets"
    / "20260717_ablation_agent_crosscheck"
    / "qwen_aligned_circularity"
)
INSTRUCTION = "Represent the user's input."
MAX_RANK = 100
SCORINGS = ("strict", "semantic")
LABEL_PHRASES = {
    "parked_vehicle": "This clip shows a vehicle parked at the roadside.",
    "dense_frame": "This clip shows a very crowded scene with many vehicles at once.",
    "multiple_buses": "This clip shows two or more buses in view.",
    "stopped_vehicles": "This clip shows vehicles stopped in the roadway.",
    "two_plus_bikes": "This clip shows two or more bicycles or motorbikes in view.",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL)
    parser.add_argument("--embedding-root", type=Path, default=DEFAULT_EMBEDDINGS)
    parser.add_argument("--qwen-root", type=Path, default=DEFAULT_QWEN_ROOT)
    parser.add_argument("--model", type=Path, default=DEFAULT_MODEL)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--random-filter-reps", type=int, default=1000)
    parser.add_argument("--bootstrap-reps", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=20260717)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while value := handle.read(chunk):
            digest.update(value)
    return digest.hexdigest()


def sha256_strings(values: list[str]) -> str:
    digest = hashlib.sha256()
    for value in values:
        digest.update(value.encode("utf-8"))
        digest.update(b"\0")
    return digest.hexdigest()


def read_queries(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def positive_sets(path: Path) -> dict[str, set[str]]:
    frame = pd.read_csv(path, sep="\t")
    return {
        str(query_id): set(group["target_id"].astype(str))
        for query_id, group in frame.groupby("query_id", sort=False)
    }


def make_embedder(args: argparse.Namespace):
    sys.path.insert(0, str(args.qwen_root))
    from src.models.qwen3_vl_embedding import Qwen3VLEmbedder

    return Qwen3VLEmbedder(
        model_name_or_path=str(args.model),
        dtype=torch.bfloat16,
        attn_implementation="flash_attention_2",
        max_pixels=534600,
        default_instruction=INSTRUCTION,
    )


def process_with_backoff(model, texts: list[str], batch_size: int, label: str) -> np.ndarray:
    outputs: list[np.ndarray] = []
    position = 0
    active_batch = max(1, batch_size)
    while position < len(texts):
        batch = [{"text": text} for text in texts[position : position + active_batch]]
        try:
            value = model.process(batch).detach().float().cpu().numpy().astype("float32")
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            if active_batch == 1:
                raise
            active_batch = max(1, active_batch // 2)
            print(f"[{label}] CUDA OOM; batch={active_batch}", flush=True)
            continue
        outputs.append(value)
        position += len(batch)
        if position % max(100, active_batch) == 0 or position == len(texts):
            print(f"[{label}] {position}/{len(texts)}", flush=True)
    matrix = np.vstack(outputs).astype("float32")
    norms = np.linalg.norm(matrix, axis=1)
    if not np.isfinite(matrix).all() or float(np.max(np.abs(norms - 1.0))) > 5e-3:
        raise RuntimeError(f"Invalid {label} embeddings: norm={norms.min()}..{norms.max()}")
    # Match the joint-grid runner, which L2-normalizes persisted Qwen vectors
    # in float32 immediately before inner-product retrieval.
    matrix /= norms[:, None]
    return matrix


def token_length_audit(model, groups: dict[str, list[str]]) -> dict[str, Any]:
    result: dict[str, Any] = {"model_max_length": int(model.max_length)}
    for name, texts in groups.items():
        lengths: list[int] = []
        for start in range(0, len(texts), 128):
            conversations = [model.format_model_input(text=text) for text in texts[start : start + 128]]
            templated = model.processor.apply_chat_template(
                conversations, add_generation_prompt=True, tokenize=False
            )
            encoded = model.processor.tokenizer(
                templated, add_special_tokens=False, truncation=False, padding=False
            )["input_ids"]
            lengths.extend(len(value) for value in encoded)
        values = np.asarray(lengths, dtype=int)
        result[name] = {
            "min": int(values.min()),
            "median": float(np.median(values)),
            "max": int(values.max()),
            "over_model_max": int((values > model.max_length).sum()),
        }
    return result


def inject_full(documents: pd.DataFrame, semantic: dict[str, set[str]], queries: list[dict[str, Any]]) -> tuple[list[str], int]:
    by_definition: dict[str, set[str]] = {}
    for query in queries:
        definition = str(query["relevance_def"])
        positives = semantic[str(query["query_id"])]
        if definition in by_definition and by_definition[definition] != positives:
            raise AssertionError(f"Semantic qrels differ within definition: {definition}")
        by_definition[definition] = positives
    if set(by_definition) != set(LABEL_PHRASES):
        raise AssertionError("Unexpected relevance definitions")

    texts: list[str] = []
    edges = 0
    for row in documents.itertuples(index=False):
        additions = [
            LABEL_PHRASES[definition]
            for definition, positives in by_definition.items()
            if str(row.clip_id) in positives
        ]
        edges += len(additions)
        texts.append(" ".join([str(row.text or ""), *additions]).strip())
    return texts, edges


def ranking(scores: np.ndarray, clip_ids: np.ndarray, candidates: np.ndarray | None = None) -> list[str]:
    indices = np.arange(len(clip_ids), dtype=np.int64) if candidates is None else candidates
    ordered = sorted(
        ((str(clip_ids[index]), float(scores[index])) for index in indices),
        key=lambda pair: (-pair[1], pair[0]),
    )
    return [clip_id for clip_id, _ in ordered[:MAX_RANK]]


def metrics(result: list[str], positives: set[str]) -> dict[str, float]:
    gains = np.fromiter((1.0 if value in positives else 0.0 for value in result[:10]), dtype=float)
    discounts = 1.0 / np.log2(np.arange(2, len(gains) + 2))
    dcg = float(np.sum(gains * discounts))
    ideal_count = min(10, len(positives))
    idcg = float(np.sum(1.0 / np.log2(np.arange(2, ideal_count + 2)))) if ideal_count else 0.0
    relevant_ranks = [rank for rank, value in enumerate(result, start=1) if value in positives]
    return {
        "ndcg_at_10": dcg / idcg if idcg else 0.0,
        "mrr": 1.0 / relevant_ranks[0] if relevant_ranks else 0.0,
        "recall_at_10": float(sum(value in positives for value in result[:10]) / len(positives)) if positives else 0.0,
    }


def bootstrap(delta: np.ndarray, clusters: np.ndarray, reps: int, seed: int) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    query_idx = rng.integers(0, len(delta), size=(reps, len(delta)))
    query_means = delta[query_idx].mean(axis=1)
    unique, inverse = np.unique(clusters, return_inverse=True)
    sizes = np.bincount(inverse)
    cluster_means = np.asarray([delta[inverse == index].mean() for index in range(len(unique))])
    cluster_idx = rng.integers(0, len(unique), size=(reps, len(unique)))
    cluster_values = (cluster_means[cluster_idx] * sizes[cluster_idx]).sum(axis=1) / sizes[cluster_idx].sum(axis=1)
    return {
        "mean_delta": float(delta.mean()),
        "query_ci_lo": float(np.quantile(query_means, 0.025)),
        "query_ci_hi": float(np.quantile(query_means, 0.975)),
        "cluster_ci_lo": float(np.quantile(cluster_values, 0.025)),
        "cluster_ci_hi": float(np.quantile(cluster_values, 0.975)),
    }


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty; use --overwrite")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    documents = pd.read_parquet(args.canonical_root / "documents.parquet").reset_index(drop=True)
    queries = read_queries(args.canonical_root / "queries.jsonl")
    doc_index = pd.read_parquet(args.embedding_root / "document_index.parquet")
    query_index = pd.read_parquet(args.embedding_root / "query_index.parquet")
    if documents["doc_id"].tolist() != doc_index["doc_id"].tolist():
        raise AssertionError("Document/index misalignment")
    if [row["query_id"] for row in queries] != query_index["query_id"].tolist():
        raise AssertionError("Query/index misalignment")
    strict = positive_sets(args.canonical_root / "qrels.tsv")
    semantic = positive_sets(args.canonical_root / "qrels_semantic.tsv")
    qrels = {"strict": strict, "semantic": semantic}
    clean_texts = documents["text"].fillna("").astype(str).tolist()
    query_texts = [str(row["query_text"]) for row in queries]
    full_texts, injected_edges = inject_full(documents, semantic, queries)

    model = make_embedder(args)
    token_lengths = token_length_audit(
        model, {"clean_documents": clean_texts, "full_documents": full_texts, "queries": query_texts}
    )
    if any(value.get("over_model_max", 0) for value in token_lengths.values() if isinstance(value, dict)):
        raise AssertionError(f"Text truncation detected: {token_lengths}")
    clean_vectors = process_with_backoff(model, clean_texts, args.batch_size, "clean")
    full_vectors = process_with_backoff(model, full_texts, args.batch_size, "contaminated")
    query_vectors = process_with_backoff(model, query_texts, args.batch_size, "query")
    del model
    torch.cuda.empty_cache()

    np.save(args.output_dir / "clean_document_embeddings.npy", clean_vectors)
    np.save(args.output_dir / "full_document_embeddings.npy", full_vectors)
    np.save(args.output_dir / "query_embeddings.npy", query_vectors)
    full_documents = documents.copy()
    full_documents["text"] = full_texts
    full_documents.to_parquet(args.output_dir / "full_contaminated_documents.parquet", index=False)

    clip_ids = doc_index["clip_id"].astype(str).to_numpy()
    clean_scores = query_vectors @ clean_vectors.T
    full_scores = query_vectors @ full_vectors.T
    clusters = np.asarray(
        [f"{row['difficulty']}|{row['relevance_def']}" for row in queries], dtype=object
    )
    per_query_rows: list[dict[str, Any]] = []
    ranking_rows: list[dict[str, Any]] = []
    random_replicate_rows: list[dict[str, Any]] = []
    clip_to_index = {clip_id: index for index, clip_id in enumerate(clip_ids)}

    c1_values: dict[tuple[str, str], np.ndarray] = {}
    c2_values: dict[tuple[str, str], np.ndarray] = {}
    for scoring_pos, scoring in enumerate(SCORINGS):
        clean_metric = np.zeros(len(queries), dtype=float)
        oracle_metric = np.zeros(len(queries), dtype=float)
        full_metric = np.zeros(len(queries), dtype=float)
        random_matrix = np.zeros((args.random_filter_reps, len(queries)), dtype=float)
        for query_pos, query in enumerate(queries):
            qid = str(query["query_id"])
            positives = qrels[scoring][qid]
            clean_rank = ranking(clean_scores[query_pos], clip_ids)
            full_rank = ranking(full_scores[query_pos], clip_ids)
            positive_indices = np.asarray(sorted(clip_to_index[value] for value in positives), dtype=np.int64)
            oracle_rank = ranking(clean_scores[query_pos], clip_ids, positive_indices)
            clean_values = metrics(clean_rank, positives)
            oracle_values = metrics(oracle_rank, positives)
            full_values = metrics(full_rank, positives)
            clean_metric[query_pos] = clean_values["ndcg_at_10"]
            oracle_metric[query_pos] = oracle_values["ndcg_at_10"]
            full_metric[query_pos] = full_values["ndcg_at_10"]
            for experiment, condition, values in [
                ("C1", "qwen_clean", clean_values),
                ("C1", "oracle_qrel_filter", oracle_values),
                ("C2", "qwen_clean", clean_values),
                ("C2", "qwen_full_contamination", full_values),
            ]:
                per_query_rows.append(
                    {
                        "experiment": experiment,
                        "condition": condition,
                        "scoring": scoring,
                        "query_id": qid,
                        "cluster": clusters[query_pos],
                        **values,
                    }
                )
            if scoring == "semantic":
                for condition, values in [
                    ("qwen_clean", clean_rank),
                    ("oracle_qrel_filter", oracle_rank),
                    ("qwen_full_contamination", full_rank),
                ]:
                    for rank, clip_id in enumerate(values, start=1):
                        ranking_rows.append(
                            {"condition": condition, "query_id": qid, "rank": rank, "clip_id": clip_id}
                        )
            for rep in range(args.random_filter_reps):
                rng = np.random.default_rng(
                    np.random.SeedSequence([args.seed, 4101, scoring_pos, rep, query_pos])
                )
                candidates = np.sort(rng.choice(len(clip_ids), size=len(positives), replace=False))
                random_rank = ranking(clean_scores[query_pos], clip_ids, candidates)
                random_matrix[rep, query_pos] = metrics(random_rank, positives)["ndcg_at_10"]

        c1_values[(scoring, "qwen_clean")] = clean_metric
        c1_values[(scoring, "oracle_qrel_filter")] = oracle_metric
        c1_values[(scoring, "random_same_selectivity_mean")] = random_matrix.mean(axis=0)
        c2_values[(scoring, "qwen_clean")] = clean_metric
        c2_values[(scoring, "qwen_full_contamination")] = full_metric
        for rep, value in enumerate(random_matrix.mean(axis=1)):
            random_replicate_rows.append({"scoring": scoring, "replicate": rep, "mean_ndcg_at_10": value})

    summary_rows: list[dict[str, Any]] = []
    for (scoring, condition), values in {**c1_values, **c2_values}.items():
        experiment = "C2" if condition == "qwen_full_contamination" else "C1"
        if condition == "qwen_clean":
            summary_rows.extend(
                [
                    {"experiment": "C1", "condition": condition, "scoring": scoring, "ndcg_at_10": float(values.mean())},
                    {"experiment": "C2", "condition": condition, "scoring": scoring, "ndcg_at_10": float(values.mean())},
                ]
            )
        else:
            summary_rows.append(
                {"experiment": experiment, "condition": condition, "scoring": scoring, "ndcg_at_10": float(values.mean())}
            )

    contrast_rows: list[dict[str, Any]] = []
    for scoring_pos, scoring in enumerate(SCORINGS):
        for experiment, treatment, control, values in [
            (
                "C1",
                "oracle_qrel_filter",
                "qwen_clean",
                c1_values[(scoring, "oracle_qrel_filter")] - c1_values[(scoring, "qwen_clean")],
            ),
            (
                "C1",
                "oracle_qrel_filter",
                "random_same_selectivity_mean",
                c1_values[(scoring, "oracle_qrel_filter")] - c1_values[(scoring, "random_same_selectivity_mean")],
            ),
            (
                "C2",
                "qwen_full_contamination",
                "qwen_clean",
                c2_values[(scoring, "qwen_full_contamination")] - c2_values[(scoring, "qwen_clean")],
            ),
        ]:
            contrast_rows.append(
                {
                    "experiment": experiment,
                    "scoring": scoring,
                    "treatment": treatment,
                    "control": control,
                    **bootstrap(values, clusters, args.bootstrap_reps, args.seed + 500 + scoring_pos),
                }
            )

    per_query = pd.DataFrame(per_query_rows)
    summary = pd.DataFrame(summary_rows).drop_duplicates().sort_values(["experiment", "scoring", "condition"])
    contrasts = pd.DataFrame(contrast_rows)
    per_query.to_parquet(args.output_dir / "per_query_metrics.parquet", index=False)
    summary.to_csv(args.output_dir / "summary.csv", index=False)
    contrasts.to_csv(args.output_dir / "contrasts.csv", index=False)
    pd.DataFrame(ranking_rows).to_parquet(args.output_dir / "rankings_semantic.parquet", index=False)
    pd.DataFrame(random_replicate_rows).to_csv(args.output_dir / "random_filter_replicates.csv", index=False)

    frozen_clean = np.load(args.embedding_root / "document_embeddings.npy").astype("float32")
    frozen_queries = np.load(args.embedding_root / "query_embeddings.npy").astype("float32")
    frozen_clean /= np.linalg.norm(frozen_clean, axis=1, keepdims=True)
    frozen_queries /= np.linalg.norm(frozen_queries, axis=1, keepdims=True)
    clean_cosine = np.sum(frozen_clean * clean_vectors, axis=1)
    query_cosine = np.sum(frozen_queries * query_vectors, axis=1)
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "seed": args.seed,
        "model": str(args.model.resolve()),
        "model_family": "Qwen3-VL-Embedding-2B",
        "instruction": INSTRUCTION,
        "dimension": int(clean_vectors.shape[1]),
        "documents": len(documents),
        "queries": len(queries),
        "clusters": int(len(np.unique(clusters))),
        "random_filter_reps": args.random_filter_reps,
        "bootstrap_reps": args.bootstrap_reps,
        "injected_label_edges": injected_edges,
        "token_lengths": token_lengths,
        "same_model_session_clean_full_query": True,
        "clean_vs_frozen": {
            "document_mean_cosine": float(clean_cosine.mean()),
            "document_min_cosine": float(clean_cosine.min()),
            "query_mean_cosine": float(query_cosine.mean()),
            "query_min_cosine": float(query_cosine.min()),
        },
        "hashes": {
            "queries": sha256_file(args.canonical_root / "queries.jsonl"),
            "qrels": sha256_file(args.canonical_root / "qrels.tsv"),
            "qrels_semantic": sha256_file(args.canonical_root / "qrels_semantic.tsv"),
            "clean_texts": sha256_strings(clean_texts),
            "full_texts": sha256_strings(full_texts),
        },
        "interpretation": "Post-pilot controlled injection; not preregistered.",
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    def row(experiment: str, scoring: str, treatment: str, control: str) -> pd.Series:
        return contrasts[
            contrasts["experiment"].eq(experiment)
            & contrasts["scoring"].eq(scoring)
            & contrasts["treatment"].eq(treatment)
            & contrasts["control"].eq(control)
        ].iloc[0]

    c1 = row("C1", "semantic", "oracle_qrel_filter", "qwen_clean")
    c2 = row("C2", "semantic", "qwen_full_contamination", "qwen_clean")
    summary_lookup = summary.set_index(["experiment", "scoring", "condition"])["ndcg_at_10"]
    report = f"""# Qwen-aligned 순환성 통제 주입

- 동일 공간: Qwen3-VL-Embedding-2B, 2,048d
- 동일 workload: 주 91-config 격자와 같은 522 canonical, 3,000 clips / 85 queries
- clean/full/query를 한 model session에서 재임베딩
- 성격: post-pilot 통제 주입; 사전등록 아님

| 실험 | clean semantic nDCG@10 | treatment | treatment nDCG@10 | Δ [query 95% CI] | cluster 95% CI |
|---|---:|---|---:|---:|---:|
| C1 | {summary_lookup.loc[("C1", "semantic", "qwen_clean")]:.6f} | oracle qrel filter | {summary_lookup.loc[("C1", "semantic", "oracle_qrel_filter")]:.6f} | {c1.mean_delta:+.6f} [{c1.query_ci_lo:+.6f}, {c1.query_ci_hi:+.6f}] | [{c1.cluster_ci_lo:+.6f}, {c1.cluster_ci_hi:+.6f}] |
| C2 | {summary_lookup.loc[("C2", "semantic", "qwen_clean")]:.6f} | full document contamination | {summary_lookup.loc[("C2", "semantic", "qwen_full_contamination")]:.6f} | {c2.mean_delta:+.6f} [{c2.query_ci_lo:+.6f}, {c2.query_ci_hi:+.6f}] | [{c2.cluster_ci_lo:+.6f}, {c2.cluster_ci_hi:+.6f}] |

C1의 oracle=1은 qrel 자체를 후보 집합으로 사용한 구성상 상한이다. C2는 corpus/query/qrels/model을 고정하고 문서에 정답 정의 문장만 추가한 효과다. 두 결과 모두 순환 경로가 이 workload의 측정치를 부풀릴 수 있음을 보이지만, 과거 시스템 성능 차이 전체를 순환성에 귀속하지 않는다.
"""
    (args.output_dir / "RESULTS_KO.md").write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
