#!/usr/bin/env python3
"""Independent recomputation and integrity gates for the 20260717 validation."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROOT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260717_joint_optimization_validation"
CANONICAL_522 = Path(
    "/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/"
    "qwen35_9b/522/canonical"
)
CANONICAL_MEVA = Path(
    "/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/"
    "qwen35_9b/meva/canonical"
)
EMBED_522 = (
    PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
    / "embeddings_qwen3vl2b_unified_qwen35captions"
)
EMBED_MEVA = (
    PROJECT_ROOT / "Datasets" / "processed" / "meva_kf1" / "20260713"
    / "embeddings" / "qwen3vl2b-unified-qwen35captions"
)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    return p.parse_args()


def hash_file(path: Path, chunk: int = 8 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while data := handle.read(chunk):
            h.update(data)
    return h.hexdigest()


def positives(path: Path) -> dict[str, set[str]]:
    frame = pd.read_csv(path, sep="\t")
    return {str(qid): set(group["target_id"].astype(str)) for qid, group in frame.groupby("query_id", sort=False)}


def independent_metrics(ranking: list[str], relevant: set[str]) -> dict[str, float]:
    top = ranking[:10]
    hits = [1.0 if item in relevant else 0.0 for item in top]
    dcg = sum(hit / math.log2(rank + 1) for rank, hit in enumerate(hits, 1))
    ideal = min(10, len(relevant))
    idcg = sum(1.0 / math.log2(rank + 1) for rank in range(1, ideal + 1))
    first = next((rank for rank, item in enumerate(ranking, 1) if item in relevant), None)
    return {
        "ndcg_at_10": dcg / idcg if idcg else 0.0,
        "mrr": 1.0 / first if first else 0.0,
        "recall_at_10": len(set(top) & relevant) / len(relevant) if relevant else 0.0,
    }


def verify_run(root: Path, canonical: Path, expected_configs: int, expected_queries: int) -> tuple[list[dict], dict]:
    metrics = pd.read_parquet(root / "per_query_metrics.parquet")
    rankings = pd.read_parquet(root / "rankings.parquet")
    qids = [json.loads(line)["query_id"] for line in (canonical / "queries.jsonl").read_text().splitlines() if line.strip()]
    configs = metrics["config"].drop_duplicates().tolist()
    grouped = {
        (str(config), str(qid)): group.sort_values("rank")["clip_id"].astype(str).tolist()
        for (config, qid), group in rankings.groupby(["config", "query_id"], sort=False)
    }
    strict = positives(canonical / "qrels.tsv")
    semantic = positives(canonical / "qrels_semantic.tsv")
    recalculated = []
    for config in configs:
        for qid in qids:
            ranking = grouped.get((config, qid), [])
            for scoring, qrels in (("strict", strict), ("semantic", semantic)):
                recalculated.append(
                    {"config": config, "query_id": qid, "scoring": scoring, **independent_metrics(ranking, qrels[qid])}
                )
    independent = pd.DataFrame(recalculated)
    joined = metrics.merge(independent, on=["config", "query_id", "scoring"], suffixes=("_recorded", "_independent"))
    max_errors = {
        metric: float(np.max(np.abs(joined[f"{metric}_recorded"] - joined[f"{metric}_independent"])))
        for metric in ("ndcg_at_10", "mrr", "recall_at_10")
    }
    gates = [
        {"gate": "config_count", "pass": len(configs) == expected_configs, "observed": len(configs), "expected": expected_configs},
        {"gate": "query_count", "pass": len(qids) == expected_queries, "observed": len(qids), "expected": expected_queries},
        {"gate": "metric_row_count", "pass": len(metrics) == expected_configs * expected_queries * 2, "observed": len(metrics)},
        {"gate": "ndcg_recompute", "pass": max_errors["ndcg_at_10"] < 1e-12, "max_abs_error": max_errors["ndcg_at_10"]},
        {"gate": "mrr_recompute", "pass": max_errors["mrr"] < 1e-12, "max_abs_error": max_errors["mrr"]},
        {"gate": "recall_recompute", "pass": max_errors["recall_at_10"] < 1e-12, "max_abs_error": max_errors["recall_at_10"]},
        {
            "gate": "ranking_unique_within_query",
            "pass": not rankings.duplicated(["config", "query_id", "clip_id"]).any(),
            "duplicates": int(rankings.duplicated(["config", "query_id", "clip_id"]).sum()),
        },
        {
            "gate": "rank_bounds",
            "pass": bool((rankings["rank"] >= 1).all() and (rankings["rank"] <= 100).all()),
            "max_rank": int(rankings["rank"].max()),
        },
    ]
    return gates, {"max_errors": max_errors, "configs": len(configs), "queries": len(qids)}


def vector_gate(name: str, path: Path, expected_shape: tuple[int, int]) -> dict:
    value = np.load(path, mmap_mode="r")
    finite = True
    norm_min = float("inf")
    norm_max = float("-inf")
    for start in range(0, len(value), 4096):
        chunk = np.asarray(value[start : start + 4096], dtype="float32")
        finite = finite and bool(np.isfinite(chunk).all())
        norms = np.linalg.norm(chunk, axis=1)
        norm_min = min(norm_min, float(norms.min()))
        norm_max = max(norm_max, float(norms.max()))
    passed = tuple(value.shape) == expected_shape and value.dtype == np.float32 and finite and norm_min > 0.995 and norm_max < 1.005
    return {
        "gate": name,
        "pass": passed,
        "shape": list(value.shape),
        "dtype": str(value.dtype),
        "finite": finite,
        "norm_min": norm_min,
        "norm_max": norm_max,
    }


def main() -> int:
    args = parse_args()
    gates = []
    main_gates, main_info = verify_run(args.root, CANONICAL_522, 91, 85)
    gates.extend({"scope": "joint_522", **row} for row in main_gates)
    meva_root = args.root / "meva_same_encoder_control"
    meva_gates, meva_info = verify_run(meva_root, CANONICAL_MEVA, 9, 193)
    gates.extend({"scope": "meva", **row} for row in meva_gates)

    gates.extend(
        [
            {"scope": "assets_522", **vector_gate("query_vectors", EMBED_522 / "query_embeddings.npy", (85, 2048))},
            {"scope": "assets_522", **vector_gate("caption_vectors", EMBED_522 / "document_embeddings.npy", (3000, 2048))},
            {"scope": "assets_522", **vector_gate("representative_vectors", EMBED_522 / "representative_frame_embeddings.npy", (3000, 2048))},
            {"scope": "assets_522", **vector_gate("full_frame_vectors", EMBED_522 / "frame_embeddings.npy", (143830, 2048))},
            {"scope": "assets_meva", **vector_gate("query_vectors", EMBED_MEVA / "query_embeddings.npy", (193, 2048))},
            {"scope": "assets_meva", **vector_gate("caption_vectors", EMBED_MEVA / "document_embeddings.npy", (985, 2048))},
            {"scope": "assets_meva", **vector_gate("frame_vectors", EMBED_MEVA / "frame_embeddings.npy", (985, 2048))},
        ]
    )

    scaled_root = args.root / "qwen2048_scaled_index"
    scaled = pd.read_csv(scaled_root / "index_benchmark.csv")
    scaled_manifest = json.loads((scaled_root / "manifest.json").read_text())
    ivf = scaled[scaled["kind"].isin(["ivfflat", "ivfpq"])]
    gates.extend(
        [
            {"scope": "scaled_index", "gate": "row_count", "pass": len(scaled) == 34, "observed": len(scaled), "expected": 34},
            {
                "scope": "scaled_index",
                "gate": "ivf_training_minimum",
                "pass": bool((ivf["N"] >= 39 * ivf["nlist"]).all()),
                "minimum_ratio": float((ivf["N"] / ivf["nlist"]).min()),
            },
            {
                "scope": "scaled_index",
                "gate": "fixed_seed_manifest",
                "pass": scaled_manifest.get("seed") == 20260717,
                "observed": scaled_manifest.get("seed"),
            },
            {
                "scope": "scaled_index",
                "gate": "metric_bounds",
                "pass": bool(scaled["recall_at_10"].between(0, 1).all() and (scaled["p95_ms"] > 0).all()),
            },
        ]
    )

    seed_root = args.root / "qwen2048_seed_robustness"
    seed_results = pd.read_csv(seed_root / "seed_results.csv")
    seed_summary = pd.read_csv(seed_root / "seed_summary.csv")
    gates.extend(
        [
            {
                "scope": "seed_robustness",
                "gate": "three_seeds_per_config",
                "pass": bool((seed_summary["seeds"] == 3).all()),
                "seed_counts": sorted(seed_summary["seeds"].unique().tolist()),
            },
            {
                "scope": "seed_robustness",
                "gate": "seed_set",
                "pass": set(seed_results["seed"].astype(int)) == {20260717, 20260718, 20260719},
                "observed": sorted(seed_results["seed"].astype(int).unique().tolist()),
            },
            {
                "scope": "seed_robustness",
                "gate": "metric_bounds",
                "pass": bool(seed_results["recall_at_10"].between(0, 1).all()),
            },
        ]
    )

    # Manifests must point to the unchanged qrels used in independent recomputation.
    joint_manifest = json.loads((args.root / "manifest.json").read_text())
    meva_manifest = json.loads((meva_root / "manifest.json").read_text())
    gates.extend(
        [
            {
                "scope": "hashes",
                "gate": "joint_qrels_hash",
                "pass": joint_manifest["hashes"]["qrels"] == hash_file(CANONICAL_522 / "qrels.tsv"),
            },
            {
                "scope": "hashes",
                "gate": "meva_qrels_hash",
                "pass": meva_manifest["input_hashes"]["qrels"] == hash_file(CANONICAL_MEVA / "qrels.tsv"),
            },
        ]
    )

    overall = all(bool(row["pass"]) for row in gates)
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "verifier": "independent metric formulas; does not import project evaluation helpers",
        "overall_pass": overall,
        "passed": sum(bool(row["pass"]) for row in gates),
        "total": len(gates),
        "joint_info": main_info,
        "meva_info": meva_info,
        "gates": gates,
    }
    (args.root / "independent_verification.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# 독립 검산",
        "",
        f"- overall: **{'PASS' if overall else 'FAIL'}**",
        f"- gates: {payload['passed']}/{payload['total']}",
        "- 프로젝트 metric helper를 import하지 않고 raw ranking에서 nDCG/MRR/recall을 재계산했다.",
        "",
        "| scope | gate | result |",
        "|---|---|---|",
    ]
    lines.extend(f"| {row['scope']} | {row['gate']} | {'PASS' if row['pass'] else 'FAIL'} |" for row in gates)
    (args.root / "INDEPENDENT_VERIFICATION_KO.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"overall_pass": overall, "passed": payload["passed"], "total": payload["total"]}, indent=2))
    if not overall:
        failed = [row for row in gates if not row["pass"]]
        print(json.dumps(failed, ensure_ascii=False, indent=2))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
