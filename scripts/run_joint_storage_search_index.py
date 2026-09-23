#!/usr/bin/env python3
"""Run the compatible storage x search-plan x index grid on frozen 522 data.

This experiment deliberately avoids invalid Cartesian cells.  Caption storage
supports lexical-vector hybrid search; representative-frame, joint
image-caption, and multi-frame storage support vector-only/postfilter/prefilter
plans; dual storage fuses the caption and multi-frame vector lanes.  All vector
lanes use the same frozen Qwen3-VL-Embedding-2B query space.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import faiss
import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi


PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "2026_KIISE" / "src"))
from vlmdb_workload.metrics import evaluate_ranking  # noqa: E402
from vlmdb_workload.retrieval import filter_clip_ids, metadata_pivot, tokenize  # noqa: E402


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
DEFAULT_OUTPUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260717_joint_optimization_validation"
TOP_KS = [1, 5, 10, 20]
MAX_RANK = 100
POSTFILTER_VECTOR_K = 200
SEED = 20260717


@dataclass
class Lane:
    name: str
    vectors: np.ndarray
    clip_ids: np.ndarray
    max_vectors_per_clip: int


@dataclass
class IndexVariant:
    name: str
    family: str
    index: Any
    search_kwargs: dict[str, Any]
    build_s: float
    index_bytes: int


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--canonical-root", type=Path, default=DEFAULT_CANONICAL)
    p.add_argument("--embedding-root", type=Path, default=DEFAULT_EMBEDDINGS)
    p.add_argument(
        "--joint-embedding-root",
        type=Path,
        help="Optional directory containing joint_embeddings.npy and joint_index.parquet",
    )
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--latency-repeats", type=int, default=10)
    p.add_argument("--latency-warmup", type=int, default=2)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--overwrite", action="store_true")
    return p.parse_args()


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while data := f.read(chunk):
            h.update(data)
    return h.hexdigest()


def index_size(index) -> int:
    with tempfile.NamedTemporaryFile(suffix=".faiss", delete=False) as handle:
        path = handle.name
    try:
        faiss.write_index(index, path)
        return os.path.getsize(path)
    finally:
        Path(path).unlink(missing_ok=True)


def normalize(matrix: np.ndarray) -> np.ndarray:
    value = np.ascontiguousarray(matrix.astype("float32", copy=True))
    faiss.normalize_L2(value)
    return value


def build_family(lane: Lane, family: str, seed: int) -> list[IndexVariant]:
    vectors = lane.vectors
    dim = vectors.shape[1]
    faiss.omp_set_num_threads(0)
    start = time.perf_counter()
    if family == "flat":
        index = faiss.IndexFlatIP(dim)
        index.add(vectors)
        variants = [("flat", {})]
    elif family == "hnsw":
        index = faiss.IndexHNSWFlat(dim, 32, faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = 200
        index.hnsw.rng = faiss.RandomGenerator(seed)
        index.add(vectors)
        variants = [("hnsw_ef64", {"efSearch": 64}), ("hnsw_ef256", {"efSearch": 256})]
    elif family == "ivfflat":
        index = faiss.IndexIVFFlat(faiss.IndexFlatIP(dim), dim, 64, faiss.METRIC_INNER_PRODUCT)
        index.cp.seed = seed
        index.train(vectors)
        index.add(vectors)
        variants = [("ivfflat_np8", {"nprobe": 8}), ("ivfflat_np32", {"nprobe": 32})]
    elif family == "ivfpq":
        # Six-bit PQ is used because the smallest lane has only 3,000 vectors;
        # 8-bit PQ would violate FAISS's recommended >=39*256 training points.
        index = faiss.IndexIVFPQ(faiss.IndexFlatIP(dim), dim, 64, 32, 6, faiss.METRIC_INNER_PRODUCT)
        index.cp.seed = seed
        index.pq.cp.seed = seed
        index.train(vectors)
        index.add(vectors)
        variants = [("ivfpq6_np8", {"nprobe": 8}), ("ivfpq6_np32", {"nprobe": 32})]
    else:
        raise ValueError(family)
    build_s = time.perf_counter() - start
    size = index_size(index)
    return [IndexVariant(name, family, index, kwargs, build_s, size) for name, kwargs in variants]


def selector_params(variant: IndexVariant, allowed: np.ndarray | None):
    selector = None
    if allowed is not None:
        ids = np.ascontiguousarray(allowed.astype("int64", copy=False))
        selector = faiss.IDSelectorBatch(len(ids), faiss.swig_ptr(ids))
    if variant.family == "flat":
        params = faiss.SearchParameters()
    elif variant.family == "hnsw":
        params = faiss.SearchParametersHNSW()
        params.efSearch = int(variant.search_kwargs["efSearch"])
    else:
        params = faiss.SearchParametersIVF()
        params.nprobe = int(variant.search_kwargs["nprobe"])
        params.ensure_topk_full = True
    if selector is not None:
        params.sel = selector
    return params, selector


def search_variant(
    variant: IndexVariant,
    query: np.ndarray,
    k: int,
    allowed: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    k = max(1, min(int(k), int(len(allowed) if allowed is not None else variant.index.ntotal)))
    params, selector = selector_params(variant, allowed)
    scores, ids = variant.index.search(np.ascontiguousarray(query.reshape(1, -1)), k, params=params)
    _ = selector  # Keep the SWIG-owned selector alive through search.
    return scores[0], ids[0]


def collapse(scores: np.ndarray, ids: np.ndarray, clip_ids: np.ndarray, candidate: set[str] | None) -> list[str]:
    ranking: list[str] = []
    seen: set[str] = set()
    for _score, idx in zip(scores, ids, strict=False):
        if idx < 0:
            continue
        clip = str(clip_ids[int(idx)])
        if clip in seen or (candidate is not None and clip not in candidate):
            continue
        seen.add(clip)
        ranking.append(clip)
        if len(ranking) >= MAX_RANK:
            break
    return ranking


def rrf(rankings: list[list[str]], k: int = 60) -> list[str]:
    score: dict[str, float] = {}
    for ranking in rankings:
        for rank, clip in enumerate(ranking, start=1):
            score[clip] = score.get(clip, 0.0) + 1.0 / (k + rank)
    return [clip for clip, _ in sorted(score.items(), key=lambda item: (-item[1], item[0]))[:MAX_RANK]]


def load_workload(args: argparse.Namespace):
    canonical = args.canonical_root
    embeddings = args.embedding_root
    clips = pd.read_parquet(canonical / "clips.parquet")
    documents = pd.read_parquet(canonical / "documents.parquet")
    metadata = pd.read_parquet(canonical / "metadata.parquet")
    queries = [json.loads(line) for line in (canonical / "queries.jsonl").read_text().splitlines() if line.strip()]
    q_index = pd.read_parquet(embeddings / "query_index.parquet")
    d_index = pd.read_parquet(embeddings / "document_index.parquet")
    if [row["query_id"] for row in queries] != q_index["query_id"].tolist():
        raise RuntimeError("Query embedding order differs from frozen query order")
    if documents["doc_id"].tolist() != d_index["doc_id"].tolist():
        raise RuntimeError("Caption embedding order differs from frozen document order")

    query_vectors = normalize(np.load(embeddings / "query_embeddings.npy"))
    caption_vectors = normalize(np.load(embeddings / "document_embeddings.npy"))
    representative_vectors = normalize(np.load(embeddings / "representative_frame_embeddings.npy"))
    representative_index = pd.read_parquet(embeddings / "representative_frame_index.parquet")
    if representative_index["clip_id"].tolist() != clips["clip_id"].tolist():
        raise RuntimeError("Representative-frame order differs from canonical clip order")

    frame_index = pd.read_parquet(embeddings / "frame_index.parquet")
    corpus_clips = set(clips["clip_id"].astype(str))
    keep = frame_index["clip_id"].astype(str).isin(corpus_clips).to_numpy()
    source = np.load(embeddings / "frame_embeddings.npy", mmap_mode="r")
    multi_vectors = normalize(source[keep])
    multi_index = frame_index.loc[keep].reset_index(drop=True)
    if multi_index["clip_id"].nunique() != len(clips):
        raise RuntimeError("Not every frozen clip has multi-frame evidence")
    max_frames = int(multi_index.groupby("clip_id").size().max())

    lanes = {
        "caption": Lane("caption", caption_vectors, d_index["clip_id"].astype(str).to_numpy(), 1),
        "representative_frame": Lane(
            "representative_frame", representative_vectors, representative_index["clip_id"].astype(str).to_numpy(), 1
        ),
        "multi_frame": Lane("multi_frame", multi_vectors, multi_index["clip_id"].astype(str).to_numpy(), max_frames),
    }
    if args.joint_embedding_root is not None:
        joint_root = args.joint_embedding_root
        joint_index = pd.read_parquet(joint_root / "joint_index.parquet")
        joint_vectors = normalize(np.load(joint_root / "joint_embeddings.npy"))
        if len(joint_index) != len(clips) or tuple(joint_vectors.shape) != (len(clips), query_vectors.shape[1]):
            raise RuntimeError(
                f"Joint asset size differs: index={len(joint_index)}, vectors={joint_vectors.shape}, "
                f"expected={(len(clips), query_vectors.shape[1])}"
            )
        if joint_index["clip_id"].astype(str).tolist() != clips["clip_id"].astype(str).tolist():
            raise RuntimeError("Joint image-caption order differs from canonical clip order")
        if "caption_match" in joint_index and not joint_index["caption_match"].astype(bool).all():
            raise RuntimeError("The main joint lane must contain matched image-caption pairs only")
        lanes["joint_image_caption"] = Lane(
            "joint_image_caption",
            joint_vectors,
            joint_index["clip_id"].astype(str).to_numpy(),
            1,
        )
    return clips, documents, metadata, queries, query_vectors, lanes


def positives(path: Path) -> dict[str, set[str]]:
    frame = pd.read_csv(path, sep="\t")
    return {str(qid): set(group["target_id"].astype(str)) for qid, group in frame.groupby("query_id", sort=False)}


def compatible_plans(representation: str) -> list[str]:
    if representation == "caption":
        return ["B2_vector", "B3_postfilter", "B4_prefilter", "B5_lexical_vector_hybrid"]
    return ["B2_vector", "B3_postfilter", "B4_prefilter"]


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty; pass --overwrite")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    clips, documents, metadata, queries, query_vectors, lanes = load_workload(args)
    qids = [str(row["query_id"]) for row in queries]
    metadata_wide = metadata_pivot(metadata)
    candidates = {
        qid: filter_clip_ids(metadata_wide, dict(row.get("metadata_filter") or {}))
        for qid, row in zip(qids, queries, strict=True)
    }
    strict = positives(args.canonical_root / "qrels.tsv")
    semantic = positives(args.canonical_root / "qrels_semantic.tsv")

    tokenized_docs = [tokenize(text) for text in documents["text"].fillna("")]
    bm25_start = time.perf_counter()
    bm25 = BM25Okapi(tokenized_docs)
    bm25_build_s = time.perf_counter() - bm25_start
    caption_clip_ids = lanes["caption"].clip_ids
    bm25_cache: dict[str, list[str]] = {}
    for row in queries:
        qid = str(row["query_id"])
        scores = bm25.get_scores(tokenize(str(row["query_text"]))).astype("float32")
        order = np.argsort(-scores, kind="mergesort")
        bm25_cache[qid] = [
            str(caption_clip_ids[idx]) for idx in order if str(caption_clip_ids[idx]) in candidates[qid]
        ][:MAX_RANK]

    allowed_cache: dict[tuple[str, str], np.ndarray] = {}
    for lane_name, lane in lanes.items():
        for qid in qids:
            allowed_cache[(lane_name, qid)] = np.flatnonzero(
                np.fromiter((clip in candidates[qid] for clip in lane.clip_ids), dtype=bool, count=len(lane.clip_ids))
            ).astype("int64")

    index_variants: dict[str, dict[str, IndexVariant]] = {}
    index_stats: list[dict[str, Any]] = []
    for lane_name, lane in lanes.items():
        index_variants[lane_name] = {}
        for family in ("flat", "hnsw", "ivfflat", "ivfpq"):
            print(f"[build] lane={lane_name} family={family} n={len(lane.vectors)} d={lane.vectors.shape[1]}", flush=True)
            for variant in build_family(lane, family, args.seed):
                index_variants[lane_name][variant.name] = variant
                index_stats.append(
                    {
                        "lane": lane_name,
                        "index": variant.name,
                        "family": family,
                        "n_vectors": len(lane.vectors),
                        "dimension": lane.vectors.shape[1],
                        "build_s": variant.build_s,
                        "index_bytes": variant.index_bytes,
                        "index_mb": variant.index_bytes / 1e6,
                        **variant.search_kwargs,
                    }
                )

    index_names = list(index_variants["caption"])
    if not all(list(index_variants[name]) == index_names for name in lanes):
        raise RuntimeError("Index grids differ across lanes")

    def vector_lane_ranking(lane_name: str, index_name: str, qpos: int, plan: str) -> list[str]:
        lane = lanes[lane_name]
        variant = index_variants[lane_name][index_name]
        qid = qids[qpos]
        if plan == "B3_postfilter":
            scores, ids = search_variant(variant, query_vectors[qpos], POSTFILTER_VECTOR_K)
            return collapse(scores, ids, lane.clip_ids, candidates[qid])
        if plan in ("B4_prefilter", "B5_lexical_vector_hybrid"):
            allowed = allowed_cache[(lane_name, qid)]
            if len(allowed) == 0:
                return []
            k = min(len(allowed), MAX_RANK * lane.max_vectors_per_clip)
            scores, ids = search_variant(variant, query_vectors[qpos], k, allowed)
            return collapse(scores, ids, lane.clip_ids, None)
        k = min(len(lane.vectors), MAX_RANK * lane.max_vectors_per_clip)
        scores, ids = search_variant(variant, query_vectors[qpos], k)
        return collapse(scores, ids, lane.clip_ids, None)

    def retrieve(representation: str, plan: str, index_name: str, qpos: int) -> list[str]:
        qid = qids[qpos]
        if representation == "dual":
            caption_rank = vector_lane_ranking("caption", index_name, qpos, plan)
            frame_rank = vector_lane_ranking("multi_frame", index_name, qpos, plan)
            return rrf([caption_rank, frame_rank])
        ranking = vector_lane_ranking(representation, index_name, qpos, plan)
        if plan == "B5_lexical_vector_hybrid":
            return rrf([bm25_cache[qid], ranking])
        return ranking

    rankings: dict[str, dict[str, list[str]]] = {}
    metric_rows: list[dict[str, Any]] = []
    ranking_rows: list[dict[str, Any]] = []
    latency_rows: list[dict[str, Any]] = []
    rng = np.random.default_rng(args.seed)
    representations = ["caption", "representative_frame"]
    if "joint_image_caption" in lanes:
        representations.append("joint_image_caption")
    representations.extend(["multi_frame", "dual"])

    faiss.omp_set_num_threads(1)
    for index_name in index_names:
        for representation in representations:
            for plan in compatible_plans(representation):
                config = f"{representation}__{plan}__{index_name}"
                print(f"[evaluate] {config}", flush=True)
                rankings[config] = {}
                for qpos, qid in enumerate(qids):
                    ranking = retrieve(representation, plan, index_name, qpos)
                    rankings[config][qid] = ranking
                    for scoring, qrels in (("strict", strict), ("semantic", semantic)):
                        values = evaluate_ranking(ranking, qrels.get(qid, set()), TOP_KS)
                        metric_rows.append(
                            {
                                "config": config,
                                "representation": representation,
                                "search_plan": plan,
                                "index": index_name,
                                "query_id": qid,
                                "scoring": scoring,
                                "candidate_clips": len(candidates[qid]),
                                **values,
                            }
                        )
                    for rank, clip in enumerate(ranking, start=1):
                        ranking_rows.append(
                            {"config": config, "query_id": qid, "rank": rank, "clip_id": clip}
                        )

                for warm in range(args.latency_warmup):
                    for qpos in rng.permutation(len(qids)):
                        retrieve(representation, plan, index_name, int(qpos))
                for repeat in range(args.latency_repeats):
                    for order, qpos in enumerate(rng.permutation(len(qids))):
                        start = time.perf_counter_ns()
                        result = retrieve(representation, plan, index_name, int(qpos))
                        elapsed = (time.perf_counter_ns() - start) / 1e6
                        latency_rows.append(
                            {
                                "config": config,
                                "repeat": repeat,
                                "order": order,
                                "query_id": qids[int(qpos)],
                                "latency_ms": elapsed,
                                "result_count": len(result),
                            }
                        )

    metrics = pd.DataFrame(metric_rows)
    latency = pd.DataFrame(latency_rows)
    quality = (
        metrics.groupby(["config", "representation", "search_plan", "index", "scoring"], sort=False)
        .agg(
            queries=("query_id", "size"),
            ndcg_at_10=("ndcg_at_10", "mean"),
            mrr=("mrr", "mean"),
            recall_at_10=("recall_at_10", "mean"),
            hit_at_10=("hit_at_10", "mean"),
        )
        .reset_index()
    )
    latency_summary = (
        latency.groupby("config", sort=False)["latency_ms"]
        .agg(
            latency_mean_ms="mean",
            latency_p50_ms="median",
            latency_p95_ms=lambda values: values.quantile(0.95),
            latency_p99_ms=lambda values: values.quantile(0.99),
        )
        .reset_index()
    )
    stats = pd.DataFrame(index_stats)
    stats.to_csv(args.output_dir / "index_build_stats.csv", index=False)

    config_cost_rows = []
    for config in quality["config"].drop_duplicates():
        representation, plan, index_name = config.split("__", 2)
        lane_names = ["caption", "multi_frame"] if representation == "dual" else [representation]
        selected = stats[(stats["lane"].isin(lane_names)) & (stats["index"].eq(index_name))]
        config_cost_rows.append(
            {
                "config": config,
                "vector_payload_mb": sum(lanes[name].vectors.nbytes for name in lane_names) / 1e6,
                "index_mb": selected["index_mb"].sum(),
                "build_s": selected["build_s"].sum() + (bm25_build_s if plan == "B5_lexical_vector_hybrid" else 0.0),
            }
        )
    costs = pd.DataFrame(config_cost_rows)
    summary = quality.merge(latency_summary, on="config").merge(costs, on="config")

    # Vector-level ANN fidelity and end-task top-10 overlap against the matching Flat configuration.
    fidelity_rows: list[dict[str, Any]] = []
    for lane_name, lane in lanes.items():
        flat = index_variants[lane_name]["flat"]
        exact_ids = [search_variant(flat, query_vectors[i], 10)[1] for i in range(len(qids))]
        for index_name, variant in index_variants[lane_name].items():
            overlaps = []
            for i, truth in enumerate(exact_ids):
                estimate = search_variant(variant, query_vectors[i], 10)[1]
                overlaps.append(len(set(truth.tolist()) & set(estimate.tolist())) / 10.0)
            fidelity_rows.append(
                {"lane": lane_name, "index": index_name, "vector_recall_at_10": float(np.mean(overlaps))}
            )
    for config, by_query in rankings.items():
        representation, plan, index_name = config.split("__", 2)
        flat_config = f"{representation}__{plan}__flat"
        overlaps = []
        for qid in qids:
            truth = rankings[flat_config][qid][:10]
            estimate = by_query[qid][:10]
            # Some postfilter runs legitimately return fewer than ten clips.
            # Fidelity is recall against the available exact ranking, not a
            # penalty for the search plan's fixed candidate budget itself.
            denominator = max(1, len(truth))
            overlaps.append(len(set(estimate) & set(truth)) / denominator)
        fidelity_rows.append(
            {
                "lane": representation,
                "search_plan": plan,
                "index": index_name,
                "task_rank_overlap_at_10": float(np.mean(overlaps)),
            }
        )

    metrics.to_parquet(args.output_dir / "per_query_metrics.parquet", index=False)
    pd.DataFrame(ranking_rows).to_parquet(args.output_dir / "rankings.parquet", index=False)
    latency.to_parquet(args.output_dir / "latency_trials.parquet", index=False)
    quality.to_csv(args.output_dir / "quality_summary.csv", index=False)
    latency_summary.to_csv(args.output_dir / "latency_summary.csv", index=False)
    costs.to_csv(args.output_dir / "configuration_costs.csv", index=False)
    summary.to_csv(args.output_dir / "configuration_summary.csv", index=False)
    pd.DataFrame(fidelity_rows).to_csv(args.output_dir / "index_fidelity.csv", index=False)
    summary[
        summary["index"].eq("flat") & summary["search_plan"].eq("B2_vector")
    ].to_csv(args.output_dir / "same_encoder_storage_control.csv", index=False)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "experiment": "compatible storage x search x index joint validation",
        "canonical_root": str(args.canonical_root.resolve()),
        "embedding_root": str(args.embedding_root.resolve()),
        "joint_embedding_root": (
            str(args.joint_embedding_root.resolve()) if args.joint_embedding_root is not None else None
        ),
        "seed": args.seed,
        "queries": len(qids),
        "clips": len(clips),
        "qrels_strict": sum(len(values) for values in strict.values()),
        "qrels_semantic": sum(len(values) for values in semantic.values()),
        "representations": representations,
        "compatible_search_plans": {name: compatible_plans(name) for name in representations},
        "indexes": index_names,
        "index_training": {"nlist": 64, "pq_m": 32, "pq_nbits": 6, "hnsw_M": 32, "hnsw_efConstruction": 200},
        "max_rank": MAX_RANK,
        "postfilter_vector_k": POSTFILTER_VECTOR_K,
        "latency": {
            "threads": 1,
            "repeats": args.latency_repeats,
            "warmup_rounds": args.latency_warmup,
            "randomized_query_order": True,
            "scope": "search, filter/collapse, and fusion; excludes embedding and build",
            "host_loadavg": list(os.getloadavg()),
        },
        "counts": {name: {"vectors": len(lane.vectors), "max_vectors_per_clip": lane.max_vectors_per_clip} for name, lane in lanes.items()},
        "hashes": {
            "embedding_manifest": sha256_file(args.embedding_root / "embedding_manifest.json"),
            "joint_embedding_manifest": (
                sha256_file(args.joint_embedding_root / "embedding_manifest.json")
                if args.joint_embedding_root is not None
                else None
            ),
            "queries": sha256_file(args.canonical_root / "queries.jsonl"),
            "qrels": sha256_file(args.canonical_root / "qrels.tsv"),
            "qrels_semantic": sha256_file(args.canonical_root / "qrels_semantic.tsv"),
        },
        "caveats": [
            "The joint task-quality grid is evaluated at the frozen 3,000-clip scale.",
            "Postfilter uses a fixed top-200 vector candidate budget.",
            "Index size is serialized FAISS size and includes indexed vector payload.",
            "Joint image-caption vectors are single-vector early-fusion representations.",
            "Latency was measured under the recorded shared-host load and must not be generalized to other hardware.",
        ],
    }
    (args.output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"[done] configs={summary['config'].nunique()} rows={len(metrics)} -> {args.output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
