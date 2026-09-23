#!/usr/bin/env python3
"""External MEVA same-encoder caption/frame/dual storage validation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import faiss
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0, str(PROJECT_ROOT / "2026_KIISE" / "src"))
from vlmdb_workload.metrics import evaluate_ranking  # noqa: E402
from vlmdb_workload.retrieval import filter_clip_ids, metadata_pivot  # noqa: E402


CANONICAL = Path(
    "/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/"
    "qwen35_9b/meva/canonical"
)
EMBEDDINGS = (
    PROJECT_ROOT / "Datasets" / "processed" / "meva_kf1" / "20260713"
    / "embeddings" / "qwen3vl2b-unified-qwen35captions"
)
OUTPUT = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260717_joint_optimization_validation"
    / "meva_same_encoder_control"
)
SEED = 20260717
MAX_RANK = 100
TOP_KS = [1, 5, 10, 20]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--canonical-root", type=Path, default=CANONICAL)
    p.add_argument("--embedding-root", type=Path, default=EMBEDDINGS)
    p.add_argument("--output-dir", type=Path, default=OUTPUT)
    p.add_argument("--bootstrap-reps", type=int, default=10000)
    p.add_argument("--latency-repeats", type=int, default=10)
    p.add_argument("--seed", type=int, default=SEED)
    p.add_argument("--overwrite", action="store_true")
    return p.parse_args()


def normalize(value: np.ndarray) -> np.ndarray:
    value = np.ascontiguousarray(value.astype("float32", copy=True))
    faiss.normalize_L2(value)
    return value


def load_queries(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def positives(path: Path) -> dict[str, set[str]]:
    frame = pd.read_csv(path, sep="\t")
    return {str(qid): set(group["target_id"].astype(str)) for qid, group in frame.groupby("query_id", sort=False)}


def rrf(first: list[str], second: list[str], k: int = 60) -> list[str]:
    scores: dict[str, float] = {}
    for ranking in (first, second):
        for rank, clip in enumerate(ranking, 1):
            scores[clip] = scores.get(clip, 0.0) + 1.0 / (k + rank)
    return [clip for clip, _ in sorted(scores.items(), key=lambda item: (-item[1], item[0]))[:MAX_RANK]]


def flat_size(index) -> int:
    with tempfile.NamedTemporaryFile(suffix=".faiss", delete=False) as handle:
        path = handle.name
    try:
        faiss.write_index(index, path)
        return os.path.getsize(path)
    finally:
        Path(path).unlink(missing_ok=True)


def bootstrap(delta, query_samples, cluster_samples, inverse, sizes):
    query_boot = delta[query_samples].mean(axis=1)
    means = np.array([delta[inverse == idx].mean() for idx in range(len(sizes))])
    cluster_boot = (means[cluster_samples] * sizes[cluster_samples]).sum(1) / sizes[cluster_samples].sum(1)
    qlo, qhi = np.quantile(query_boot, [0.025, 0.975])
    clo, chi = np.quantile(cluster_boot, [0.025, 0.975])
    return {
        "mean_delta": float(delta.mean()),
        "query_ci_lo": float(qlo),
        "query_ci_hi": float(qhi),
        "cluster_ci_lo": float(clo),
        "cluster_ci_hi": float(chi),
        "p_query": min(1.0, 2.0 * min(float((query_boot <= 0).mean()), float((query_boot >= 0).mean()))),
        "p_cluster": min(1.0, 2.0 * min(float((cluster_boot <= 0).mean()), float((cluster_boot >= 0).mean()))),
        "wins": int((delta > 1e-12).sum()),
        "ties": int((np.abs(delta) <= 1e-12).sum()),
        "losses": int((delta < -1e-12).sum()),
    }


def bh_adjust(values):
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    ranked = values[order]
    adjusted = np.minimum.accumulate(
        (ranked * len(values) / np.arange(1, len(values) + 1))[::-1]
    )[::-1]
    result = np.empty_like(adjusted)
    result[order] = np.clip(adjusted, 0.0, 1.0)
    return result


def sha256_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while data := handle.read(chunk):
            h.update(data)
    return h.hexdigest()


def main() -> int:
    args = parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    queries = load_queries(args.canonical_root / "queries.jsonl")
    qids = [str(row["query_id"]) for row in queries]
    clips = pd.read_parquet(args.canonical_root / "clips.parquet")
    metadata = pd.read_parquet(args.canonical_root / "metadata.parquet")
    d_index = pd.read_parquet(args.embedding_root / "document_index.parquet")
    f_index = pd.read_parquet(args.embedding_root / "frame_index.parquet")
    q_index = pd.read_parquet(args.embedding_root / "query_index.parquet")
    if qids != q_index["query_id"].astype(str).tolist():
        raise RuntimeError("MEVA query order mismatch")
    if d_index["clip_id"].astype(str).tolist() != f_index["clip_id"].astype(str).tolist():
        raise RuntimeError("MEVA caption/frame clip order mismatch")

    qvec = normalize(np.load(args.embedding_root / "query_embeddings.npy"))
    vectors = {
        "caption": normalize(np.load(args.embedding_root / "document_embeddings.npy")),
        "frame": normalize(np.load(args.embedding_root / "frame_embeddings.npy")),
    }
    clip_ids = d_index["clip_id"].astype(str).to_numpy()
    indexes = {}
    build_s = {}
    sizes = {}
    for name, matrix in vectors.items():
        start = time.perf_counter()
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        indexes[name] = index
        build_s[name] = time.perf_counter() - start
        sizes[name] = flat_size(index)

    wide = metadata_pivot(metadata)
    candidates = {
        qid: filter_clip_ids(wide, dict(row.get("metadata_filter") or {}))
        for qid, row in zip(qids, queries, strict=True)
    }
    allowed = {
        qid: np.flatnonzero(np.fromiter((clip in candidates[qid] for clip in clip_ids), bool, len(clip_ids)))
        for qid in qids
    }

    def lane_ranking(lane: str, qpos: int, plan: str) -> list[str]:
        qid = qids[qpos]
        if plan == "B4_prefilter":
            ids = allowed[qid]
            scores = vectors[lane][ids] @ qvec[qpos]
            order = ids[np.argsort(-scores, kind="mergesort")]
            return [str(clip_ids[idx]) for idx in order[:MAX_RANK]]
        k = min(len(clip_ids), 200 if plan == "B3_postfilter" else MAX_RANK)
        _, found = indexes[lane].search(qvec[qpos].reshape(1, -1), k)
        ranking = [str(clip_ids[idx]) for idx in found[0] if idx >= 0]
        if plan == "B3_postfilter":
            ranking = [clip for clip in ranking if clip in candidates[qid]]
        return ranking[:MAX_RANK]

    def retrieve(representation: str, plan: str, qpos: int) -> list[str]:
        if representation == "dual":
            return rrf(lane_ranking("caption", qpos, plan), lane_ranking("frame", qpos, plan))
        return lane_ranking(representation, qpos, plan)

    qrels = {"strict": positives(args.canonical_root / "qrels.tsv"), "semantic": positives(args.canonical_root / "qrels_semantic.tsv")}
    metric_rows = []
    latency_rows = []
    ranking_rows = []
    rng = np.random.default_rng(args.seed)
    faiss.omp_set_num_threads(1)
    for representation in ("caption", "frame", "dual"):
        for plan in ("B2_vector", "B3_postfilter", "B4_prefilter"):
            config = f"{representation}__{plan}__flat"
            rankings = {}
            for qpos, qid in enumerate(qids):
                ranking = retrieve(representation, plan, qpos)
                rankings[qid] = ranking
                for scoring, positives_by_query in qrels.items():
                    metric_rows.append(
                        {
                            "config": config,
                            "representation": representation,
                            "search_plan": plan,
                            "query_id": qid,
                            "scoring": scoring,
                            **evaluate_ranking(ranking, positives_by_query[qid], TOP_KS),
                        }
                    )
                for rank, clip in enumerate(ranking, 1):
                    ranking_rows.append({"config": config, "query_id": qid, "rank": rank, "clip_id": clip})
            for _ in range(2):
                for qpos in rng.permutation(len(qids)):
                    retrieve(representation, plan, int(qpos))
            for repeat in range(args.latency_repeats):
                for qpos in rng.permutation(len(qids)):
                    start = time.perf_counter_ns()
                    result = retrieve(representation, plan, int(qpos))
                    latency_rows.append(
                        {
                            "config": config,
                            "repeat": repeat,
                            "query_id": qids[int(qpos)],
                            "latency_ms": (time.perf_counter_ns() - start) / 1e6,
                            "result_count": len(result),
                        }
                    )

    metrics = pd.DataFrame(metric_rows)
    latency = pd.DataFrame(latency_rows)
    summary = (
        metrics.groupby(["config", "representation", "search_plan", "scoring"], sort=False)
        .agg(queries=("query_id", "size"), ndcg_at_10=("ndcg_at_10", "mean"), mrr=("mrr", "mean"), recall_at_10=("recall_at_10", "mean"))
        .reset_index()
    )
    lat_summary = latency.groupby("config")["latency_ms"].agg(
        latency_p50_ms="median", latency_p95_ms=lambda x: x.quantile(0.95)
    ).reset_index()
    cost_rows = []
    for representation in ("caption", "frame", "dual"):
        lane_names = ["caption", "frame"] if representation == "dual" else [representation]
        cost_rows.append(
            {
                "representation": representation,
                "index_mb": sum(sizes[name] for name in lane_names) / 1e6,
                "build_s": sum(build_s[name] for name in lane_names),
            }
        )
    summary = summary.merge(lat_summary, on="config").merge(pd.DataFrame(cost_rows), on="representation")

    query_frame = pd.DataFrame(queries)
    query_frame["cluster"] = query_frame["relevance_def"].astype(str) + "|" + query_frame["difficulty"].astype(str)
    clusters, inverse = np.unique(query_frame["cluster"], return_inverse=True)
    cluster_sizes = np.bincount(inverse)
    query_samples = rng.integers(0, len(qids), size=(args.bootstrap_reps, len(qids)), dtype=np.int16)
    cluster_samples = rng.integers(0, len(clusters), size=(args.bootstrap_reps, len(clusters)), dtype=np.int16)
    value_map = {
        (config, scoring): group.set_index("query_id").loc[qids]["ndcg_at_10"].to_numpy()
        for (config, scoring), group in metrics.groupby(["config", "scoring"], sort=False)
    }
    comparisons = []
    pairs = [
        ("storage", "frame__B2_vector__flat", "caption__B2_vector__flat"),
        ("storage", "dual__B2_vector__flat", "caption__B2_vector__flat"),
    ]
    for representation in ("caption", "frame", "dual"):
        pairs.append(("search", f"{representation}__B4_prefilter__flat", f"{representation}__B2_vector__flat"))
    for family, candidate, baseline in pairs:
        for scoring in ("strict", "semantic"):
            delta = value_map[(candidate, scoring)] - value_map[(baseline, scoring)]
            comparisons.append(
                {
                    "family": family,
                    "scoring": scoring,
                    "candidate": candidate,
                    "baseline": baseline,
                    "queries": len(qids),
                    "clusters": len(clusters),
                    **bootstrap(delta, query_samples, cluster_samples, inverse, cluster_sizes),
                }
            )
    comparisons = pd.DataFrame(comparisons)
    comparisons["q_query_bh"] = np.nan
    comparisons["q_cluster_bh"] = np.nan
    for (_family, _scoring), indices in comparisons.groupby(["family", "scoring"]).groups.items():
        comparisons.loc[indices, "q_query_bh"] = bh_adjust(comparisons.loc[indices, "p_query"])
        comparisons.loc[indices, "q_cluster_bh"] = bh_adjust(comparisons.loc[indices, "p_cluster"])

    metrics.to_parquet(args.output_dir / "per_query_metrics.parquet", index=False)
    pd.DataFrame(ranking_rows).to_parquet(args.output_dir / "rankings.parquet", index=False)
    latency.to_parquet(args.output_dir / "latency_trials.parquet", index=False)
    summary.to_csv(args.output_dir / "summary.csv", index=False)
    comparisons.to_csv(args.output_dir / "paired_bootstrap.csv", index=False)
    query_frame[["query_id", "relevance_def", "difficulty", "cluster"]].to_csv(args.output_dir / "query_clusters.csv", index=False)

    def get_summary(config, scoring):
        return summary[(summary.config == config) & (summary.scoring == scoring)].iloc[0]
    def get_comp(candidate, scoring):
        return comparisons[(comparisons.candidate == candidate) & (comparisons.scoring == scoring)].iloc[0]
    cap_sem = get_summary("caption__B2_vector__flat", "semantic")
    frame_sem = get_summary("frame__B2_vector__flat", "semantic")
    dual_sem = get_summary("dual__B2_vector__flat", "semantic")
    d_frame_sem = get_comp("frame__B2_vector__flat", "semantic")
    d_dual_sem = get_comp("dual__B2_vector__flat", "semantic")
    def p_display(value):
        return "<0.0001" if float(value) == 0.0 else f"{float(value):.4f}"
    report = f"""# MEVA 동일 인코더 외부 저장 표현 통제

- corpus: 985 clips, queries: 193, clusters: {len(clusters)}
- encoder: Qwen3-VL-Embedding-2B, 2,048d (query/caption/frame 동일)

Flat/B2 semantic nDCG@10은 caption {cap_sem.ndcg_at_10:.4f}, frame {frame_sem.ndcg_at_10:.4f},
dual {dual_sem.ndcg_at_10:.4f}였다. Frame-caption 차이는 {d_frame_sem.mean_delta:+.4f},
질의 bootstrap 95% CI [{d_frame_sem.query_ci_lo:+.4f}, {d_frame_sem.query_ci_hi:+.4f}],
activity×facet 군집 bootstrap 95% CI [{d_frame_sem.cluster_ci_lo:+.4f}, {d_frame_sem.cluster_ci_hi:+.4f}]이다.
Storage-family BH 보정 cluster q-value는 frame-caption {p_display(d_frame_sem.q_cluster_bh)},
dual-caption {p_display(d_dual_sem.q_cluster_bh)}이다. Dual-caption semantic 차이는
{d_dual_sem.mean_delta:+.4f}, 군집 CI [{d_dual_sem.cluster_ci_lo:+.4f}, {d_dual_sem.cluster_ci_hi:+.4f}]이다.

MEVA는 clip당 동결 대표 프레임이 하나이므로 multi-frame 저장 효과의 외부 검증이 아니라,
동일 encoder에서 caption 대 frame 표현 효과를 검증하는 실험이다.
"""
    (args.output_dir / "RESULTS_KO.md").write_text(report, encoding="utf-8")
    (args.output_dir / "manifest.json").write_text(
        json.dumps(
            {
                "created_at": datetime.now(timezone.utc).isoformat(),
                "canonical_root": str(args.canonical_root.resolve()),
                "embedding_root": str(args.embedding_root.resolve()),
                "seed": args.seed,
                "bootstrap_reps": args.bootstrap_reps,
                "latency_repeats": args.latency_repeats,
                "counts": {"clips": len(clips), "queries": len(qids), "clusters": len(clusters)},
                "input_hashes": {
                    "embedding_manifest": sha256_file(args.embedding_root / "embedding_manifest.json"),
                    "queries": sha256_file(args.canonical_root / "queries.jsonl"),
                    "qrels": sha256_file(args.canonical_root / "qrels.tsv"),
                    "qrels_semantic": sha256_file(args.canonical_root / "qrels_semantic.tsv"),
                },
                "caveat": "MEVA has one frozen representative frame per clip; this does not test multi-frame storage.",
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
