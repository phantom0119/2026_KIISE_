#!/usr/bin/env python3
"""CPU-only safety-service representation audit for IntentStore P0-C."""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SEED = 20260806
N_RANDOMIZATION = 200_000
N_BOOTSTRAP = 20_000
MAX_RANK = 100
RRF_K = 60
MIN_EFFECT = 0.05
QUALITY_FLOOR = 0.05

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"

PROCESSED = Path("/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed")
CONFIGS = {
    "VRU": {
        "canonical": PROCESSED / "vru_accident/20260710_noncircular/canonical",
        "visual": PROCESSED / "vru_accident/20260706/visual_embeddings/clip-vit-base-patch32_full",
        "text_results": PROCESSED / "vru_accident/20260710_noncircular/results/vru2_bgem3_b0_b5",
        "semantic_facet": "accident_type",
    },
    "AIHUB": {
        "canonical": PROCESSED / "aihub_intelligent_cctv/20260710_noncircular/canonical",
        "visual": PROCESSED / "aihub_intelligent_cctv/20260706/visual_embeddings/clip-vit-base-patch32_full",
        "text_results": PROCESSED / "aihub_intelligent_cctv/20260710_noncircular/results/acctv2_bgem3_b0_b5",
        "semantic_facet": "event_class",
    },
}

COSTS = {
    "caption": 4096,
    "center_frame": 2048,
    "visual_4frame": 8192,
    "fusion": 12288,
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_queries(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalize_rows(array: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(array, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    return array / norms


def as_tensor(features: Any) -> Any:
    import torch

    if isinstance(features, torch.Tensor):
        return features
    for attr in ("text_embeds", "pooler_output", "last_hidden_state"):
        value = getattr(features, attr, None)
        if isinstance(value, torch.Tensor):
            return value[:, 0] if attr == "last_hidden_state" else value
    if isinstance(features, (tuple, list)) and features and isinstance(features[0], torch.Tensor):
        return features[0]
    raise TypeError(f"Unsupported CLIP output: {type(features).__name__}")


def encode_clip_texts(texts: list[str]) -> tuple[np.ndarray, dict[str, Any]]:
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    import torch
    from transformers import CLIPModel, CLIPProcessor

    torch.set_num_threads(min(8, os.cpu_count() or 1))
    model_id = "openai/clip-vit-base-patch32"
    started = time.perf_counter()
    processor = CLIPProcessor.from_pretrained(model_id, local_files_only=True, use_fast=False)
    model = CLIPModel.from_pretrained(model_id, local_files_only=True).to("cpu").eval()
    vectors: list[np.ndarray] = []
    with torch.inference_mode():
        for start in range(0, len(texts), 32):
            inputs = processor(
                text=texts[start : start + 32],
                padding=True,
                truncation=True,
                return_tensors="pt",
            )
            features = as_tensor(model.get_text_features(**inputs))
            vectors.append(features.detach().cpu().float().numpy())
    result = normalize_rows(np.vstack(vectors).astype("float32"))
    meta = {
        "model_id": model_id,
        "device": str(next(model.parameters()).device),
        "local_files_only": True,
        "query_count": len(texts),
        "embedding_dim": int(result.shape[1]),
        "seconds": time.perf_counter() - started,
        "torch_threads": torch.get_num_threads(),
        "cuda_visible_devices": os.environ.get("CUDA_VISIBLE_DEVICES", "<unset>"),
    }
    return result, meta


def metadata_map(metadata: pd.DataFrame) -> tuple[dict[str, dict[str, str]], dict[str, set[str]]]:
    by_clip: dict[str, dict[str, str]] = {}
    for row in metadata[["clip_id", "facet_name", "facet_value"]].to_dict("records"):
        by_clip.setdefault(str(row["clip_id"]), {})[str(row["facet_name"])] = str(row["facet_value"])
    all_by_facet: dict[str, set[str]] = {}
    for clip_id, facets in by_clip.items():
        for facet, value in facets.items():
            all_by_facet.setdefault(f"{facet}\0{value}", set()).add(clip_id)
    return by_clip, all_by_facet


def candidates_for(filters: dict[str, Any], clip_ids: set[str], lookup: dict[str, set[str]]) -> set[str]:
    candidates = set(clip_ids)
    for facet, value in filters.items():
        candidates &= lookup.get(f"{facet}\0{value}", set())
    return candidates


def rank_visual(
    scores: np.ndarray,
    frame_index: pd.DataFrame,
    candidates: set[str],
    frame_mode: str,
) -> list[str]:
    if frame_mode == "center":
        eligible = frame_index["frame_seq"].eq(1).to_numpy() & frame_index["clip_id"].isin(candidates).to_numpy()
    else:
        eligible = frame_index["clip_id"].isin(candidates).to_numpy()
    order = np.argsort(-scores, kind="mergesort")
    best: dict[str, float] = {}
    for idx in order.tolist():
        if not eligible[idx]:
            continue
        clip_id = str(frame_index.iloc[idx]["clip_id"])
        if clip_id not in best:
            best[clip_id] = float(scores[idx])
        if len(best) >= MAX_RANK:
            break
    return sorted(best, key=lambda clip: (-best[clip], clip))[:MAX_RANK]


def evaluate(ranking: list[str], positives: set[str]) -> dict[str, float]:
    top = ranking[:10]
    gains = np.asarray([1.0 if clip in positives else 0.0 for clip in top], dtype="float64")
    discounts = 1.0 / np.log2(np.arange(2, 2 + len(gains))) if len(gains) else np.asarray([])
    dcg = float(np.sum(gains * discounts))
    ideal_count = min(10, len(positives))
    ideal = float(np.sum(1.0 / np.log2(np.arange(2, 2 + ideal_count)))) if ideal_count else 0.0
    relevant = int(gains.sum())
    return {
        "ndcg_at_10": dcg / ideal if ideal else 0.0,
        "hit_at_10": float(relevant > 0),
        "recall_at_10": relevant / len(positives) if positives else 0.0,
    }


def rrf(left: list[str], right: list[str]) -> list[str]:
    scores: dict[str, float] = {}
    for ranking in (left, right):
        for rank, clip_id in enumerate(ranking, start=1):
            scores[clip_id] = scores.get(clip_id, 0.0) + 1.0 / (RRF_K + rank)
    return sorted(scores, key=lambda clip: (-scores[clip], clip))[:MAX_RANK]


def infer_event_type(
    positives: set[str],
    facet: str,
    clip_meta: dict[str, dict[str, str]],
) -> str:
    values = {clip_meta[clip][facet] for clip in positives if clip in clip_meta and facet in clip_meta[clip]}
    if len(values) != 1:
        raise ValueError(f"Expected one {facet} among positives, got {sorted(values)}")
    return next(iter(values))


def event_family(dataset: str, event_type: str) -> str:
    if dataset == "VRU":
        return "dynamic_event"
    if event_type.lower() in {"falldown", "fight", "invasion"}:
        return "dynamic_event"
    return "scene_state"


def signflip_pvalue(diff: np.ndarray, rng: np.random.Generator) -> float:
    observed = abs(float(diff.mean()))
    exceed = 0
    completed = 0
    chunk = 10_000
    while completed < N_RANDOMIZATION:
        size = min(chunk, N_RANDOMIZATION - completed)
        signs = rng.choice(np.asarray([-1.0, 1.0]), size=(size, len(diff)))
        sampled = np.abs((signs * diff).mean(axis=1))
        exceed += int(np.count_nonzero(sampled >= observed - 1e-15))
        completed += size
    return (exceed + 1.0) / (N_RANDOMIZATION + 1.0)


def bootstrap_ci(diff: np.ndarray, rng: np.random.Generator) -> tuple[float, float]:
    indices = rng.integers(0, len(diff), size=(N_BOOTSTRAP, len(diff)))
    means = diff[indices].mean(axis=1)
    return float(np.quantile(means, 0.025)), float(np.quantile(means, 0.975))


def cluster_bootstrap(
    diff: np.ndarray,
    clusters: np.ndarray,
    rng: np.random.Generator,
) -> tuple[float, float, float, int]:
    frame = pd.DataFrame({"diff": diff, "cluster": clusters})
    cluster_means = frame.groupby("cluster", sort=True)["diff"].mean().to_numpy()
    indices = rng.integers(0, len(cluster_means), size=(N_BOOTSTRAP, len(cluster_means)))
    means = cluster_means[indices].mean(axis=1)
    return (
        float(cluster_means.mean()),
        float(np.quantile(means, 0.025)),
        float(np.quantile(means, 0.975)),
        len(cluster_means),
    )


def bh_adjust(pvalues: list[float]) -> list[float]:
    values = np.asarray(pvalues, dtype="float64")
    order = np.argsort(values)
    adjusted = np.empty(len(values), dtype="float64")
    running = 1.0
    for reverse_rank in range(len(values) - 1, -1, -1):
        idx = order[reverse_rank]
        rank = reverse_rank + 1
        running = min(running, values[idx] * len(values) / rank)
        adjusted[idx] = running
    return adjusted.tolist()


def build_dataset(
    dataset: str,
    config: dict[str, Any],
    query_embeddings: np.ndarray,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    canonical = Path(config["canonical"])
    visual = Path(config["visual"])
    text_root = Path(config["text_results"])
    queries = read_queries(canonical / "queries.jsonl")
    metadata = pd.read_parquet(canonical / "metadata.parquet")
    qrels = pd.read_csv(canonical / "qrels.tsv", sep="\t")
    frame_index = pd.read_parquet(visual / "frame_index.parquet").reset_index(drop=True)
    frame_embeddings = np.load(visual / "frame_embeddings.npy").astype("float32")
    text_results = pd.read_parquet(text_root / "retrieval_results.parquet")

    if len(query_embeddings) != len(queries):
        raise ValueError(f"{dataset}: query embedding count mismatch")
    if len(frame_embeddings) != len(frame_index):
        raise ValueError(f"{dataset}: frame embedding count mismatch")

    clip_meta, facet_lookup = metadata_map(metadata)
    clip_ids = set(clip_meta)
    positives_by_query = {
        str(query_id): set(group["target_id"].astype(str))
        for query_id, group in qrels.groupby("query_id", sort=False)
    }
    text_lookup: dict[tuple[str, str], list[str]] = {}
    for (strategy, query_id), group in text_results.groupby(["strategy", "query_id"], sort=False):
        text_lookup[(str(strategy), str(query_id))] = group.sort_values("rank")["clip_id"].astype(str).tolist()

    rows: list[dict[str, Any]] = []
    visual_seconds = 0.0
    for pos, query in enumerate(queries):
        query_id = str(query["query_id"])
        filters = dict(query.get("metadata_filter") or {})
        candidates = candidates_for(filters, clip_ids, facet_lookup)
        positives = positives_by_query[query_id]
        text_strategy = "B2_vector_only" if not filters else "B4_prefilter_vector"
        caption_rank = text_lookup[(text_strategy, query_id)][:MAX_RANK]

        start = time.perf_counter()
        scores = frame_embeddings @ query_embeddings[pos]
        center_rank = rank_visual(scores, frame_index, candidates, "center")
        visual_rank = rank_visual(scores, frame_index, candidates, "all")
        visual_seconds += time.perf_counter() - start
        fusion_rank = rrf(caption_rank, visual_rank)

        event_type = infer_event_type(positives, str(config["semantic_facet"]), clip_meta)
        common = {
            "dataset": dataset,
            "query_id": query_id,
            "difficulty": str(query["difficulty"]),
            "event_type": event_type,
            "event_family": event_family(dataset, event_type),
            "contract_family": "open_event" if not filters else "context_filtered",
            "cluster": f"{dataset}|{event_type}",
            "positive_count": len(positives),
            "candidate_count": len(candidates),
        }
        for representation, ranking in {
            "caption": caption_rank,
            "center_frame": center_rank,
            "visual_4frame": visual_rank,
            "fusion": fusion_rank,
        }.items():
            rows.append(
                {
                    **common,
                    "representation": representation,
                    "vector_bytes_per_clip": COSTS[representation],
                    **evaluate(ranking, positives),
                }
            )

    audit = {
        "dataset": dataset,
        "query_count": len(queries),
        "clip_count": len(clip_ids),
        "frame_count": len(frame_index),
        "visual_flat_scan_seconds": visual_seconds,
        "input_hashes": {
            "queries": sha256(canonical / "queries.jsonl"),
            "qrels": sha256(canonical / "qrels.tsv"),
            "metadata": sha256(canonical / "metadata.parquet"),
            "frame_embeddings": sha256(visual / "frame_embeddings.npy"),
            "frame_index": sha256(visual / "frame_index.parquet"),
            "text_retrieval_results": sha256(text_root / "retrieval_results.parquet"),
        },
    }
    return rows, audit


def service_mask(frame: pd.DataFrame, service: str) -> pd.Series:
    if service in {"dynamic_event", "scene_state"}:
        return frame["event_family"].eq(service)
    return frame["contract_family"].eq(service)


def make_service_means(per_query: pd.DataFrame) -> pd.DataFrame:
    rows = []
    services = ["dynamic_event", "scene_state", "context_filtered", "open_event"]
    for service in services:
        part = per_query[service_mask(per_query, service)]
        for representation, group in part.groupby("representation", sort=False):
            rows.append(
                {
                    "service": service,
                    "representation": representation,
                    "queries": group["query_id"].nunique(),
                    "event_clusters": group["cluster"].nunique(),
                    "mean_ndcg_at_10": group["ndcg_at_10"].mean(),
                    "mean_hit_at_10": group["hit_at_10"].mean(),
                    "mean_recall_at_10": group["recall_at_10"].mean(),
                    "supported_query_rate": group["ndcg_at_10"].ge(QUALITY_FLOOR).mean(),
                    "vector_bytes_per_clip": COSTS[str(representation)],
                }
            )
    return pd.DataFrame(rows)


def make_primary_tests(per_query: pd.DataFrame) -> pd.DataFrame:
    specs = [
        ("H1", "dynamic_event", "visual_4frame", "caption"),
        ("H2", "scene_state", "caption", "visual_4frame"),
        ("H3", "context_filtered", "fusion", "caption"),
        ("H4", "all", "visual_4frame", "center_frame"),
    ]
    pivot = per_query.pivot(index="query_id", columns="representation", values="ndcg_at_10")
    meta = per_query.drop_duplicates("query_id").set_index("query_id")
    rows = []
    for offset, (test_id, service, left, right) in enumerate(specs):
        ids = meta.index if service == "all" else meta.index[service_mask(meta.reset_index(), service).to_numpy()]
        diff = (pivot.loc[ids, left] - pivot.loc[ids, right]).to_numpy(dtype="float64")
        clusters = meta.loc[ids, "cluster"].to_numpy()
        rng = np.random.default_rng(SEED + offset * 1000)
        ci_low, ci_high = bootstrap_ci(diff, rng)
        cluster_mean, cluster_low, cluster_high, n_clusters = cluster_bootstrap(diff, clusters, rng)
        rows.append(
            {
                "test_id": test_id,
                "service": service,
                "left": left,
                "right": right,
                "queries": len(diff),
                "event_clusters": n_clusters,
                "mean_diff": diff.mean(),
                "ci_low": ci_low,
                "ci_high": ci_high,
                "cluster_mean_diff": cluster_mean,
                "cluster_ci_low": cluster_low,
                "cluster_ci_high": cluster_high,
                "p_value": signflip_pvalue(diff, rng),
            }
        )
    result = pd.DataFrame(rows)
    result["q_value_bh"] = bh_adjust(result["p_value"].tolist())
    result["expected_support_query"] = (
        result["mean_diff"].ge(MIN_EFFECT)
        & result["q_value_bh"].lt(0.05)
        & result["ci_low"].gt(0)
    )
    result["expected_support_cluster"] = result["expected_support_query"] & result["cluster_ci_low"].gt(0)
    result["opposite_material_support"] = (
        result["mean_diff"].le(-MIN_EFFECT)
        & result["q_value_bh"].lt(0.05)
        & result["ci_high"].lt(0)
        & result["cluster_ci_high"].lt(0)
    )
    return result


def make_pareto(service_means: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for service, group in service_means.groupby("service", sort=False):
        records = group.to_dict("records")
        for row in records:
            dominated = any(
                other["vector_bytes_per_clip"] <= row["vector_bytes_per_clip"]
                and other["mean_ndcg_at_10"] >= row["mean_ndcg_at_10"]
                and (
                    other["vector_bytes_per_clip"] < row["vector_bytes_per_clip"]
                    or other["mean_ndcg_at_10"] > row["mean_ndcg_at_10"]
                )
                for other in records
                if other["representation"] != row["representation"]
            )
            rows.append({**row, "pareto": not dominated})
    return pd.DataFrame(rows)


def decide(tests: pd.DataFrame, service_means: pd.DataFrame) -> dict[str, Any]:
    support = dict(zip(tests["test_id"], tests["expected_support_cluster"], strict=False))
    query_support = dict(zip(tests["test_id"], tests["expected_support_query"], strict=False))
    informative = service_means[
        service_means["queries"].ge(10) & service_means["mean_ndcg_at_10"].ge(QUALITY_FLOOR)
    ]
    single = informative[informative["representation"].isin(["caption", "center_frame", "visual_4frame"])]
    winners = {}
    margins = {}
    for service, group in single.groupby("service"):
        ordered = group.sort_values("mean_ndcg_at_10", ascending=False)
        if len(ordered) >= 2:
            winners[service] = str(ordered.iloc[0]["representation"])
            margins[service] = float(ordered.iloc[0]["mean_ndcg_at_10"] - ordered.iloc[1]["mean_ndcg_at_10"])

    distinct_material = (
        winners.get("dynamic_event") is not None
        and winners.get("scene_state") is not None
        and winners["dynamic_event"] != winners["scene_state"]
        and margins.get("dynamic_event", 0.0) >= MIN_EFFECT
        and margins.get("scene_state", 0.0) >= MIN_EFFECT
    )

    fusion_gain = {}
    for service, group in service_means.groupby("service"):
        values = group.set_index("representation")["mean_ndcg_at_10"].to_dict()
        best_single = max(values.get("caption", 0.0), values.get("center_frame", 0.0), values.get("visual_4frame", 0.0))
        fusion_gain[service] = float(values.get("fusion", 0.0) - best_single)

    same_winner = len(set(winners.values())) == 1 and len(winners) == 4
    all_material = len(margins) == 4 and all(value >= MIN_EFFECT for value in margins.values())
    no_fusion_value = all(value < 0.02 for value in fusion_gain.values())

    if support.get("H1", False) and support.get("H2", False) and distinct_material:
        status = "SAFETY_G1_PROVISIONAL_PASS"
    elif same_winner and all_material and no_fusion_value:
        status = "SAFETY_G1_STOP_SIGNAL"
    elif any(support.values()) or any(query_support.values()) or distinct_material:
        status = "SAFETY_G1_CONTINUE"
    else:
        status = "SAFETY_G1_INCONCLUSIVE"
    return {
        "status": status,
        "cluster_confirmed_tests": [key for key, value in support.items() if bool(value)],
        "query_contract_confirmed_tests": [key for key, value in query_support.items() if bool(value)],
        "best_single_by_service": winners,
        "best_single_margin_by_service": margins,
        "distinct_material_single_winners": bool(distinct_material),
        "fusion_gain_over_best_single": fusion_gain,
        "decision_precedence": "PROVISIONAL_PASS > STOP_SIGNAL > CONTINUE > INCONCLUSIVE",
        "post_result_logic_correction": True,
        "topic_confirmation": "NOT_FINAL",
        "required_next_gate": "multi-service replay with raw TTL, risk/SLA constraints, and best-static comparison",
    }


def render_report(
    manifest: dict[str, Any],
    service_means: pd.DataFrame,
    tests: pd.DataFrame,
    pareto: pd.DataFrame,
    decision: dict[str, Any],
) -> str:
    lines = [
        "# IntentStore P0-C 안전 서비스 표현 검증 보고서",
        "",
        f"> 자동 판정: **`{decision['status']}`**  ",
        "> 범위: 실제 안전 검색 질의에서 G1 표현 비지배성만 검사. 연구 주제 최종 확정은 아님.",
        "",
        "## 1. 실행 무결성",
        "",
        f"- CLIP query embedding 장치: `{manifest['clip_query_encoding']['device']}`",
        f"- offline/local-only: `{manifest['clip_query_encoding']['local_files_only']}`",
        f"- 질의: {manifest['counts']['queries']}개, 평가 행: {manifest['counts']['metric_rows']}개",
        "- 기존 frame/caption embedding과 순위를 읽기 전용으로 재사용했으며 영상 decoding이나 GPU 추론은 수행하지 않았다.",
        "",
        "## 2. 서비스군별 결과",
        "",
        "| service | representation | queries | event clusters | nDCG@10 | Hit@10 | support rate | vector B/clip | Pareto |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    joined = service_means.merge(
        pareto[["service", "representation", "pareto"]], on=["service", "representation"], how="left"
    )
    for row in joined.to_dict("records"):
        lines.append(
            f"| {row['service']} | {row['representation']} | {int(row['queries'])} | {int(row['event_clusters'])} | "
            f"{row['mean_ndcg_at_10']:.4f} | {row['mean_hit_at_10']:.4f} | {row['supported_query_rate']:.4f} | "
            f"{int(row['vector_bytes_per_clip'])} | {'yes' if row['pareto'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## 3. 사전 고정 주 검정",
            "",
            "| ID | service | contrast | n | clusters | mean diff | query 95% CI | cluster 95% CI | p | q(BH) | expected support | opposite support |",
            "|---|---|---|---:|---:|---:|---|---|---:|---:|---|---|",
        ]
    )
    for row in tests.to_dict("records"):
        lines.append(
            f"| {row['test_id']} | {row['service']} | {row['left']}−{row['right']} | {int(row['queries'])} | "
            f"{int(row['event_clusters'])} | {row['mean_diff']:+.4f} | [{row['ci_low']:+.4f}, {row['ci_high']:+.4f}] | "
            f"[{row['cluster_ci_low']:+.4f}, {row['cluster_ci_high']:+.4f}] | {row['p_value']:.6f} | "
            f"{row['q_value_bh']:.6f} | {'yes' if row['expected_support_cluster'] else 'no'} | "
            f"{'yes' if row['opposite_material_support'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "## 4. 판정",
            "",
            f"- 상태: **`{decision['status']}`**",
            f"- query-contract 지지 검정: `{', '.join(decision['query_contract_confirmed_tests']) or '없음'}`",
            f"- 독립 event cluster까지 지지된 검정: `{', '.join(decision['cluster_confirmed_tests']) or '없음'}`",
            f"- 서비스별 최선 단일 arm: `{json.dumps(decision['best_single_by_service'], ensure_ascii=False)}`",
            f"- fusion의 최선 단일 arm 대비 이득: `{json.dumps(decision['fusion_gain_over_best_single'], ensure_ascii=False)}`",
            "- 최초 실행의 `CONTINUE`는 STOP 조건과의 중첩을 잘못 처리한 자동 판정 우선순위 버그였다. 임계값 변경 없이 `STOP_SIGNAL`을 먼저 적용하도록 사후 수정했다.",
            "- 연구 주제 최종 확정: **아직 아님**. 이 결과는 저장 형식 선택의 필요조건만 다룬다.",
            "",
            "## 5. 해석 한계",
            "",
            "1. CLIP과 BGE-M3를 비교하므로 형식만이 아니라 encoder를 포함한 표현 stack 비교다.",
            "2. 네 frame max는 순서·궤적을 이해하지 않는다.",
            "3. 같은 event type의 조건 변형 질의가 반복되므로 query CI보다 cluster CI를 최종 일반화에 우선한다.",
            "4. vector payload만 비교했고 생성 비용, JPEG, 문자열, DB 오버헤드는 제외했다.",
            "5. 실제 원본 삭제 뒤 새 detector/VLM을 재실행한 실험이 아니므로 미래 서비스 완전성을 증명하지 않는다.",
            "",
            "## 6. 다음 게이트",
            "",
            "같은 stream에 두 개 이상의 안전 서비스를 동시에 replay하고, raw TTL 뒤의 사건 F1·위험가중 손실·p95 deadline miss·저장/GPU 비용을 측정한다. `IntentStore`가 `best-static`보다 품질/SLA 제약을 지키면서 자원을 절감할 때만 연구 주제를 확정한다.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    query_blocks = {name: read_queries(Path(config["canonical"]) / "queries.jsonl") for name, config in CONFIGS.items()}
    all_texts = [query["query_text"] for name in CONFIGS for query in query_blocks[name]]
    embeddings, encoding_meta = encode_clip_texts(all_texts)

    all_rows: list[dict[str, Any]] = []
    audits = []
    cursor = 0
    for name, config in CONFIGS.items():
        count = len(query_blocks[name])
        block = embeddings[cursor : cursor + count]
        np.save(RESULTS / f"safety_clip_query_embeddings_{name.lower()}.npy", block)
        rows, audit = build_dataset(name, config, block)
        all_rows.extend(rows)
        audits.append(audit)
        cursor += count

    per_query = pd.DataFrame(all_rows)
    service_means = make_service_means(per_query)
    tests = make_primary_tests(per_query)
    pareto = make_pareto(service_means)
    decision = decide(tests, service_means)

    manifest = {
        "protocol": "P0_CPU_SAFETY_PROTOCOL.md",
        "seed": SEED,
        "randomization_draws": N_RANDOMIZATION,
        "bootstrap_draws": N_BOOTSTRAP,
        "max_rank": MAX_RANK,
        "rrf_k": RRF_K,
        "minimum_effect": MIN_EFFECT,
        "quality_floor": QUALITY_FLOOR,
        "costs": COSTS,
        "clip_query_encoding": encoding_meta,
        "datasets": audits,
        "counts": {"queries": int(per_query["query_id"].nunique()), "metric_rows": len(per_query)},
    }

    per_query.to_csv(RESULTS / "safety_per_query_metrics.csv", index=False)
    service_means.to_csv(RESULTS / "safety_service_means.csv", index=False)
    tests.to_csv(RESULTS / "safety_primary_tests.csv", index=False)
    pareto.to_csv(RESULTS / "safety_pareto.csv", index=False)
    (RESULTS / "safety_source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (RESULTS / "safety_decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (ROOT / "P0_CPU_SAFETY_REPORT.md").write_text(
        render_report(manifest, service_means, tests, pareto, decision), encoding="utf-8"
    )
    print(json.dumps(decision, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
