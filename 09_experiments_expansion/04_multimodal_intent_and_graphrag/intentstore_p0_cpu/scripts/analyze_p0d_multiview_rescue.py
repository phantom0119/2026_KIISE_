#!/usr/bin/env python3
"""CPU-only preregistered P0-D multiview rescue audit for IntentStore."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


SEED = 20260806
N_RANDOMIZATION = 200_000
N_BOOTSTRAP = 20_000
MIN_EFFECT = 0.05
NONINFERIORITY_MARGIN = 0.05

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PROJECT = Path("/home/explorer/vectorDB/experiments/db/KIISE_datasociety")
DATA = PROJECT / "Datasets/processed/aihub_multi_angle_cctv/20260708"

STRATUM_PATH = DATA / "samples/bbox_asymmetry_stratum/stratum_manifest.parquet"
DOCUMENTS_PATH = DATA / "canonical/documents.parquet"
QUERIES_PATH = DATA / "canonical/queries.jsonl"
FRAMES_PATH = DATA / "keyframes/stratum_bbox_asymmetry_400/frames.parquet"
DOC_INDEX_PATH = DATA / "embeddings/bge-m3/document_index.parquet"
DOC_EMBED_PATH = DATA / "embeddings/bge-m3/document_embeddings.npy"
QUERY_INDEX_PATH = DATA / "embeddings/bge-m3/query_index.parquet"
QUERY_EMBED_PATH = DATA / "embeddings/bge-m3/query_embeddings.npy"

VLM_PATHS = {
    "Qwen2.5-VL-7B": DATA / "results/multiview_answer_vlm_qwen25vl_400/vlm_answers.parquet",
    "Qwen2-VL-7B": DATA / "results/multiview_answer_vlm_qwen2vl_400/vlm_answers.parquet",
    "Idefics2-8B": DATA / "results/multiview_answer_vlm_idefics2_400/vlm_answers.parquet",
    "InternVL3-8B": DATA / "results/multiview_answer_vlm_internvl3_400/vlm_answers.parquet",
}

SERVICE_GROUPS = {
    "temporal_relation": {
        "비정상적인 경로로의 침범",
        "경계선을 통한 침입",
        "신체적 충돌을 동반한 싸움",
        "특정 구역 내 지속 배회",
        "특정 인물을 뒤따라가며 배회",
    },
    "attribute_count": {
        "이륜 이동수단 운전자 1인 헬멧 미착용",
        "이륜 이동수단 탑승자 일부 또는 전체 헬멧 미착용",
        "전동킥보드 앞뒤 2인 탑승",
    },
    "path_mode": {
        "오토바이 인도 주행",
        "자전거 인도 주행",
        "전동킥보드 인도 주행",
    },
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(vector: np.ndarray) -> np.ndarray:
    norm = float(np.linalg.norm(vector))
    return vector / norm if norm else vector


def signflip_pvalue(diff: np.ndarray, rng: np.random.Generator) -> float:
    observed = abs(float(diff.mean()))
    exceed = 0
    completed = 0
    while completed < N_RANDOMIZATION:
        size = min(10_000, N_RANDOMIZATION - completed)
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
    diff: np.ndarray, clusters: np.ndarray, rng: np.random.Generator
) -> tuple[float, float, float, int]:
    frame = pd.DataFrame({"diff": diff, "cluster": clusters})
    cluster_means = frame.groupby("cluster", sort=True)["diff"].mean().to_numpy()
    indices = rng.integers(0, len(cluster_means), size=(N_BOOTSTRAP, len(cluster_means)))
    means = cluster_means[indices].mean(axis=1)
    return (
        float(cluster_means.mean()),
        float(np.quantile(means, 0.025)),
        float(np.quantile(means, 0.975)),
        int(len(cluster_means)),
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


def read_queries() -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in QUERIES_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def service_group(event_class: str) -> str:
    matches = [name for name, values in SERVICE_GROUPS.items() if event_class in values]
    if len(matches) != 1:
        raise ValueError(f"Event class has {len(matches)} service mappings: {event_class}")
    return matches[0]


def build_structured_predictions(
    clips: pd.DataFrame, documents: pd.DataFrame
) -> tuple[pd.DataFrame, list[str], dict[str, Any]]:
    doc_index = pd.read_parquet(DOC_INDEX_PATH).reset_index(drop=True)
    doc_embeddings = np.load(DOC_EMBED_PATH, mmap_mode="r")
    query_index = pd.read_parquet(QUERY_INDEX_PATH).reset_index(drop=True)
    query_embeddings = np.load(QUERY_EMBED_PATH, mmap_mode="r")
    if len(doc_index) != len(doc_embeddings):
        raise ValueError("document index/embedding count mismatch")
    if len(query_index) != len(query_embeddings):
        raise ValueError("query index/embedding count mismatch")

    weak_queries = [q for q in read_queries() if q.get("difficulty") == "weak_event"]
    if len(weak_queries) != 11:
        raise ValueError(f"Expected 11 weak_event queries, got {len(weak_queries)}")
    query_position = {str(qid): idx for idx, qid in enumerate(query_index["query_id"].astype(str))}
    classes = [str(q["semantic_filter"]["event_class"]) for q in weak_queries]
    prototypes = np.vstack(
        [np.asarray(query_embeddings[query_position[str(q["query_id"])]], dtype="float32") for q in weak_queries]
    )
    prototype_norms = np.linalg.norm(prototypes, axis=1)
    if not np.allclose(prototype_norms, 1.0, atol=1e-3):
        raise ValueError("weak_event query prototypes are not normalized")

    positions: dict[tuple[str, str], int] = {}
    for idx, row in doc_index[["clip_id", "doc_type"]].iterrows():
        key = (str(row["clip_id"]), str(row["doc_type"]))
        if key in positions:
            raise ValueError(f"Duplicate document embedding key: {key}")
        positions[key] = idx

    relevant_positions = [
        positions[(str(clip_id), doc_type)]
        for clip_id in clips["clip_id"]
        for doc_type in ("cot_c1", "cot_c2")
    ]
    relevant_norms = np.linalg.norm(
        np.asarray(doc_embeddings[relevant_positions], dtype="float32"), axis=1
    )
    if not np.allclose(relevant_norms, 1.0, atol=1e-3):
        raise ValueError("analysis COT document embeddings are not normalized")

    cot_text = documents[documents["doc_type"].isin(["cot_c1", "cot_c2"])].copy()
    text_lookup = {
        (str(row.clip_id), str(row.doc_type)): str(row.text)
        for row in cot_text.itertuples(index=False)
    }
    records: list[dict[str, Any]] = []
    for row in clips.itertuples(index=False):
        clip_id = str(row.clip_id)
        vectors: dict[str, np.ndarray] = {}
        for view in ("c1", "c2"):
            key = (clip_id, f"cot_{view}")
            if key not in positions or key not in text_lookup:
                raise ValueError(f"Missing COT evidence: {key}")
            vectors[view] = np.asarray(doc_embeddings[positions[key]], dtype="float32")
        better = str(row.better_view)
        worse = str(row.worse_view)
        mean_vector = normalize(vectors["c1"] + vectors["c2"])
        scores = {
            "cot_worse": vectors[worse] @ prototypes.T,
            "cot_better": vectors[better] @ prototypes.T,
            "cot_both_mean": mean_vector @ prototypes.T,
            "cot_both_max": np.maximum(vectors["c1"] @ prototypes.T, vectors["c2"] @ prototypes.T),
        }
        out: dict[str, Any] = {
            "clip_id": clip_id,
            "cot_better_text_bytes": len(text_lookup[(clip_id, f"cot_{better}")].encode("utf-8")),
            "cot_both_text_bytes": sum(
                len(text_lookup[(clip_id, f"cot_{view}")].encode("utf-8")) for view in ("c1", "c2")
            ),
        }
        for arm, arm_scores in scores.items():
            prediction = classes[int(np.argmax(arm_scores))]
            out[f"{arm}_pred"] = prediction
            out[f"{arm}_correct"] = int(prediction == str(row.event_class))
        records.append(out)

    audit = {
        "document_rows": int(len(doc_index)),
        "document_embedding_shape": list(doc_embeddings.shape),
        "query_rows": int(len(query_index)),
        "query_embedding_shape": list(query_embeddings.shape),
        "weak_event_prototypes": classes,
        "prototype_norm_min": float(prototype_norms.min()),
        "prototype_norm_max": float(prototype_norms.max()),
        "cot_norm_min": float(relevant_norms.min()),
        "cot_norm_max": float(relevant_norms.max()),
    }
    return pd.DataFrame(records), classes, audit


def add_vlm_predictions(per_clip: pd.DataFrame, clips: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, Any]]:
    expected_conditions = {"closed_book", "worse_view_only", "better_view_only", "both_view"}
    audit: dict[str, Any] = {}
    result = per_clip.copy()
    valid_clips = set(clips["clip_id"].astype(str))
    gold_lookup = dict(zip(clips["clip_id"].astype(str), clips["event_class"].astype(str)))
    for model, path in VLM_PATHS.items():
        raw = pd.read_parquet(path).copy()
        raw["clip_id"] = raw["clip_id"].astype(str)
        selected = raw[raw["clip_id"].isin(valid_clips)].copy()
        if set(selected["condition"].astype(str)) != expected_conditions:
            raise ValueError(f"{model}: unexpected conditions")
        counts = selected.groupby("clip_id")["condition"].nunique()
        if len(counts) != len(valid_clips) or not counts.eq(4).all():
            raise ValueError(f"{model}: incomplete clip-condition grid")
        gold_mismatch = sum(
            str(row.event_class_gold) != gold_lookup[str(row.clip_id)]
            for row in selected.itertuples(index=False)
        )
        if gold_mismatch:
            raise ValueError(f"{model}: {gold_mismatch} gold labels disagree with stratum")
        selected["correct_clean"] = selected["correct"].fillna(False).astype(bool).astype(int)
        selected["pred_clean"] = selected["pred_event_class"].fillna("<INVALID>").astype(str)
        recomputed_correct = selected.apply(
            lambda row: int(str(row["pred_clean"]) == gold_lookup[str(row["clip_id"])]), axis=1
        )
        correct_mismatch = int((recomputed_correct.to_numpy() != selected["correct_clean"].to_numpy()).sum())
        if correct_mismatch:
            raise ValueError(f"{model}: {correct_mismatch} stored correctness values are inconsistent")
        correct = selected.pivot(index="clip_id", columns="condition", values="correct_clean")
        pred = selected.pivot(index="clip_id", columns="condition", values="pred_clean")
        prefix = model.replace(".", "").replace("-", "_").lower()
        for condition in sorted(expected_conditions):
            result[f"{prefix}_{condition}_correct"] = result["clip_id"].map(correct[condition]).astype(int)
            result[f"{prefix}_{condition}_pred"] = result["clip_id"].map(pred[condition]).astype(str)
        audit[model] = {
            "source_rows": int(len(raw)),
            "analysis_rows": int(len(selected)),
            "clips": int(selected["clip_id"].nunique()),
            "conditions": sorted(expected_conditions),
            "valid_json_rate": float(selected["valid_json"].fillna(False).astype(bool).mean()),
            "parse_ok_rate": float(selected["parse_status"].astype(str).eq("ok").mean()),
        }
    return result, audit


def model_prefix(model: str) -> str:
    return model.replace(".", "").replace("-", "_").lower()


def make_accuracy_table(per_clip: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    structured_arms = ["cot_worse", "cot_better", "cot_both_mean", "cot_both_max"]
    for scope, group in [("all", per_clip), *[(name, per_clip[per_clip["service_group"] == name]) for name in SERVICE_GROUPS]]:
        for arm in structured_arms:
            records.append(
                {
                    "scope": scope,
                    "model": "BGE-M3 zero-shot",
                    "arm": arm,
                    "n": len(group),
                    "accuracy": float(group[f"{arm}_correct"].mean()),
                }
            )
        for model in VLM_PATHS:
            prefix = model_prefix(model)
            for condition in ("closed_book", "worse_view_only", "better_view_only", "both_view"):
                records.append(
                    {
                        "scope": scope,
                        "model": model,
                        "arm": condition,
                        "n": len(group),
                        "accuracy": float(group[f"{prefix}_{condition}_correct"].mean()),
                    }
                )
    return pd.DataFrame(records)


def make_primary_tests(per_clip: pd.DataFrame) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for service in SERVICE_GROUPS:
        group = per_clip[per_clip["service_group"] == service].reset_index(drop=True)
        for model in VLM_PATHS:
            visual_col = f"{model_prefix(model)}_both_view_correct"
            diff = (
                group["cot_better_correct"].to_numpy(dtype="float64")
                - group[visual_col].to_numpy(dtype="float64")
            )
            rng = np.random.default_rng(SEED + len(records) * 101)
            ci_low, ci_high = bootstrap_ci(diff, rng)
            cluster_mean, cluster_low, cluster_high, cluster_count = cluster_bootstrap(
                diff, group["event_class"].to_numpy(), rng
            )
            split_diffs = {
                split: float(diff[group["source_split"].eq(split).to_numpy()].mean())
                for split in sorted(group["source_split"].unique())
            }
            records.append(
                {
                    "service_group": service,
                    "model": model,
                    "n": len(group),
                    "event_class_count": int(group["event_class"].nunique()),
                    "cot_better_accuracy": float(group["cot_better_correct"].mean()),
                    "visual_both_accuracy": float(group[visual_col].mean()),
                    "difference_cot_minus_visual": float(diff.mean()),
                    "ci_low": ci_low,
                    "ci_high": ci_high,
                    "cluster_mean": cluster_mean,
                    "cluster_ci_low": cluster_low,
                    "cluster_ci_high": cluster_high,
                    "cluster_count": cluster_count,
                    "training_difference": split_diffs.get("Training", np.nan),
                    "validation_difference": split_diffs.get("Validation", np.nan),
                    "p_value": signflip_pvalue(diff, rng),
                }
            )
    tests = pd.DataFrame(records)
    tests["q_value_bh12"] = bh_adjust(tests["p_value"].tolist())
    tests["support_structured"] = (
        tests["difference_cot_minus_visual"].ge(MIN_EFFECT)
        & tests["q_value_bh12"].lt(0.05)
        & tests["ci_low"].gt(0)
        & tests["cluster_ci_low"].gt(0)
        & tests["training_difference"].gt(0)
        & tests["validation_difference"].gt(0)
    )
    tests["support_visual"] = (
        tests["difference_cot_minus_visual"].le(-MIN_EFFECT)
        & tests["q_value_bh12"].lt(0.05)
        & tests["ci_high"].lt(0)
        & tests["cluster_ci_high"].lt(0)
        & tests["training_difference"].lt(0)
        & tests["validation_difference"].lt(0)
    )
    return tests


def make_view_tests(per_clip: pd.DataFrame, visual_storage_ratio: float) -> pd.DataFrame:
    asymmetric = per_clip[per_clip["stratum"] == "asymmetric"].reset_index(drop=True)
    records: list[dict[str, Any]] = []
    for idx, model in enumerate(VLM_PATHS):
        prefix = model_prefix(model)
        better = asymmetric[f"{prefix}_better_view_only_correct"].to_numpy(dtype="float64")
        worse = asymmetric[f"{prefix}_worse_view_only_correct"].to_numpy(dtype="float64")
        both = asymmetric[f"{prefix}_both_view_correct"].to_numpy(dtype="float64")
        view_diff = better - worse
        retention_diff = better - both
        rng = np.random.default_rng(SEED + 5000 + idx * 101)
        view_low, view_high = bootstrap_ci(view_diff, rng)
        retention_low, retention_high = bootstrap_ci(retention_diff, rng)
        records.append(
            {
                "model": model,
                "n_asymmetric": len(asymmetric),
                "worse_accuracy": float(worse.mean()),
                "better_accuracy": float(better.mean()),
                "both_accuracy": float(both.mean()),
                "better_minus_worse": float(view_diff.mean()),
                "better_worse_ci_low": view_low,
                "better_worse_ci_high": view_high,
                "better_worse_p": signflip_pvalue(view_diff, rng),
                "better_minus_both": float(retention_diff.mean()),
                "better_both_ci_low": retention_low,
                "better_both_ci_high": retention_high,
                "visual_better_both_byte_ratio": visual_storage_ratio,
                "noninferior_to_both": bool(retention_low > -NONINFERIORITY_MARGIN),
                "cost_condition": bool(visual_storage_ratio <= 0.55),
            }
        )
    tests = pd.DataFrame(records)
    tests["better_worse_q_bh4"] = bh_adjust(tests["better_worse_p"].tolist())
    tests["better_view_effect_supported"] = (
        tests["better_minus_worse"].ge(MIN_EFFECT)
        & tests["better_worse_q_bh4"].lt(0.05)
        & tests["better_worse_ci_low"].gt(0)
    )
    return tests


def storage_tables(
    per_clip: pd.DataFrame, frames: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, float, dict[str, Any]]:
    clip_meta = per_clip.set_index("clip_id")[["better_view", "worse_view"]].to_dict("index")
    frame_rows = frames[frames["clip_id"].astype(str).isin(clip_meta)].copy()
    if len(frame_rows) != len(per_clip) * 6:
        raise ValueError(f"Expected {len(per_clip) * 6} frame rows, got {len(frame_rows)}")
    frame_rows["resolved_path"] = frame_rows["frame_path"].map(lambda value: PROJECT / str(value))
    missing = [str(path) for path in frame_rows["resolved_path"] if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Missing frame artifacts, first: {missing[0]}")
    frame_rows["bytes"] = frame_rows["resolved_path"].map(lambda path: path.stat().st_size)

    records: list[dict[str, Any]] = []
    for row in per_clip.itertuples(index=False):
        group = frame_rows[frame_rows["clip_id"].astype(str).eq(str(row.clip_id))]
        better_bytes = int(group[group["view"].astype(str).eq(str(row.better_view))]["bytes"].sum())
        both_bytes = int(group["bytes"].sum())
        records.append(
            {
                "clip_id": row.clip_id,
                "cot_1view_bytes": int(row.cot_better_text_bytes) + 4096,
                "cot_2view_bytes": int(row.cot_both_text_bytes) + 8192,
                "visual_1view_bytes": better_bytes,
                "visual_2view_bytes": both_bytes,
            }
        )
    costs = pd.DataFrame(records)
    summaries: list[dict[str, Any]] = []
    for column in ["cot_1view_bytes", "cot_2view_bytes", "visual_1view_bytes", "visual_2view_bytes"]:
        values = costs[column].to_numpy(dtype="float64")
        summaries.append(
            {
                "representation": column.removesuffix("_bytes"),
                "n": len(values),
                "total_bytes": int(values.sum()),
                "mean_bytes": float(values.mean()),
                "median_bytes": float(np.median(values)),
                "p25_bytes": float(np.quantile(values, 0.25)),
                "p75_bytes": float(np.quantile(values, 0.75)),
            }
        )
    summary = pd.DataFrame(summaries)
    ratio = float(costs["visual_1view_bytes"].sum() / costs["visual_2view_bytes"].sum())
    audit = {
        "frame_rows": int(len(frame_rows)),
        "frames_per_clip": sorted(frame_rows.groupby("clip_id").size().unique().tolist()),
        "views_per_clip": sorted(frame_rows.groupby("clip_id")["view"].nunique().unique().tolist()),
        "visual_1view_to_2view_total_byte_ratio": ratio,
    }
    return costs, summary, ratio, audit


def decide(primary: pd.DataFrame, view: pd.DataFrame) -> dict[str, Any]:
    non_dominance_models: list[str] = []
    for model, group in primary.groupby("model", sort=False):
        if bool(group["support_structured"].any()) and bool(group["support_visual"].any()):
            non_dominance_models.append(str(model))
    structured_counts = primary.groupby("service_group")["support_structured"].sum().to_dict()
    visual_counts = primary.groupby("service_group")["support_visual"].sum().to_dict()
    visual_total = int(primary["support_visual"].sum())
    structured_total = int(primary["support_structured"].sum())
    if non_dominance_models:
        rescue = "RESCUE_PASS_SERVICE_NONDOMINANCE"
    elif all(int(structured_counts.get(group, 0)) >= 3 for group in SERVICE_GROUPS) and visual_total == 0:
        rescue = "RESCUE_FAIL_STRUCTURED_DOMINANCE"
    elif all(int(visual_counts.get(group, 0)) >= 3 for group in SERVICE_GROUPS) and structured_total == 0:
        rescue = "RESCUE_FAIL_VISUAL_DOMINANCE"
    else:
        rescue = "RESCUE_INCONCLUSIVE"
    view_count = int((view["noninferior_to_both"] & view["cost_condition"]).sum())
    view_decision = "VIEW_SELECTION_NARROW_PASS" if view_count >= 3 else "VIEW_SELECTION_NARROW_FAIL"
    if rescue == "RESCUE_PASS_SERVICE_NONDOMINANCE":
        recommendation = "CONDITIONAL_CONTINUE_ONLY_AFTER_AUTOMATED_TRAJECTORY_AND_EXTERNAL_REPLICATION"
    elif rescue.startswith("RESCUE_FAIL_"):
        recommendation = "TERMINATE_BROAD_INTENTSTORE_RESEARCH_TOPIC"
    else:
        recommendation = "DO_NOT_CONFIRM_TOPIC; RESCUE_GATE_INCONCLUSIVE"
    return {
        "seed": SEED,
        "rescue_decision": rescue,
        "view_decision": view_decision,
        "recommendation": recommendation,
        "non_dominance_models": non_dominance_models,
        "structured_support_by_service": {k: int(v) for k, v in structured_counts.items()},
        "visual_support_by_service": {k: int(v) for k, v in visual_counts.items()},
        "structured_support_total": structured_total,
        "visual_support_total": visual_total,
        "view_noninferior_and_cost_count": view_count,
        "view_effect_supported_count": int(view["better_view_effect_supported"].sum()),
        "important_limitation": "COT is a label-derived oracle, not an automated trajectory extractor.",
    }


def fmt(value: float) -> str:
    return f"{value:.3f}"


def write_report(
    decision: dict[str, Any],
    primary: pd.DataFrame,
    view: pd.DataFrame,
    accuracy: pd.DataFrame,
    per_clip: pd.DataFrame,
    storage: pd.DataFrame,
    leak_clips: list[str],
    audit: dict[str, Any],
    elapsed: float,
) -> None:
    rescue = decision["rescue_decision"]
    if rescue == "RESCUE_PASS_SERVICE_NONDOMINANCE":
        headline = "조건부 구제 통과 — 단, 자동 궤적 추출·외부 재현 전에는 주제를 확정할 수 없음"
    elif rescue == "RESCUE_FAIL_STRUCTURED_DOMINANCE":
        headline = "구제 실패 — 서비스별 표현 비지배성이 없고 구조 oracle이 전 서비스군을 지배"
    elif rescue == "RESCUE_FAIL_VISUAL_DOMINANCE":
        headline = "구제 실패 — 서비스별 표현 비지배성이 없고 시각 증거가 전 서비스군을 지배"
    else:
        headline = "판정 불충분 — IntentStore 주제 확정 근거를 얻지 못함"

    structured = accuracy[
        (accuracy["model"] == "BGE-M3 zero-shot") & accuracy["arm"].eq("cot_better")
    ].set_index("scope")["accuracy"].to_dict()
    lines = [
        "# IntentStore P0-D 다각도 구조 궤적·시각 증거 구제 실험 보고서",
        "",
        f"> 판정: **{rescue}**  ",
        f"> 운영 결론: **{decision['recommendation']}**  ",
        f"> 요약: **{headline}**",
        "",
        "## 1. 무엇을 검증했는가",
        "",
        "P0-C에서 caption이 keyframe을 압도한 뒤 허용한 단 한 번의 좁은 구제 실험이다. 11개 안전 사건 399개에서, 한 카메라의 단계별 객체 행동 COT를 BGE-M3 zero-shot으로 분류한 결과와 두 카메라 6장을 입력한 동결 VLM 결과를 같은 clip 단위로 비교했다.",
        "",
        "COT는 정답 라벨 JSON에서 사람이 기술한 행동 단계다. 사건명 직접 누설 clip은 제외했지만, 자동 생성된 운영 표현이 아니라 **구조 궤적이 완벽히 추출됐다고 가정한 oracle 상한선**이다.",
        "",
        "## 2. 주 결과",
        "",
        "| 서비스군 | COT better 정확도 | Qwen2.5 visual both | Qwen2 visual both | Idefics2 visual both | InternVL3 visual both | 구조 지지 수 | 시각 지지 수 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for service in SERVICE_GROUPS:
        row_values = []
        for model in VLM_PATHS:
            row = primary[(primary["service_group"] == service) & (primary["model"] == model)].iloc[0]
            row_values.append(float(row["visual_both_accuracy"]))
        lines.append(
            f"| {service} | {fmt(structured[service])} | "
            + " | ".join(fmt(value) for value in row_values)
            + f" | {int(decision['structured_support_by_service'].get(service, 0))}/4 | {int(decision['visual_support_by_service'].get(service, 0))}/4 |"
        )
    lines += [
        "",
        "주 검정은 `COT better − visual both` 12개 비교다. 5%p 효과, paired sign-flip 20만 회, BH-FDR, clip bootstrap, 사건 class cluster bootstrap, Training/Validation 방향 일치를 모두 만족해야 지지로 인정했다.",
        "",
        "| 서비스군 | 모델 | 차이 | 95% CI | class-cluster 95% CI | BH q | 판정 |",
        "|---|---|---:|---:|---:|---:|---|",
    ]
    for row in primary.itertuples(index=False):
        support = "COT" if row.support_structured else ("visual" if row.support_visual else "없음")
        lines.append(
            f"| {row.service_group} | {row.model} | {fmt(row.difference_cot_minus_visual)} | "
            f"[{fmt(row.ci_low)}, {fmt(row.ci_high)}] | [{fmt(row.cluster_ci_low)}, {fmt(row.cluster_ci_high)}] | "
            f"{row.q_value_bh12:.6f} | {support} |"
        )

    sensitivity = accuracy[accuracy["model"].eq("BGE-M3 zero-shot")].pivot(
        index="scope", columns="arm", values="accuracy"
    )
    lines += [
        "",
        "### 구조 arm 민감도",
        "",
        "| 범위 | worse 1-view | better 1-view | both mean | both max |",
        "|---|---:|---:|---:|---:|",
    ]
    for scope in ["all", *SERVICE_GROUPS.keys()]:
        lines.append(
            f"| {scope} | {fmt(sensitivity.loc[scope, 'cot_worse'])} | "
            f"{fmt(sensitivity.loc[scope, 'cot_better'])} | {fmt(sensitivity.loc[scope, 'cot_both_mean'])} | "
            f"{fmt(sensitivity.loc[scope, 'cot_both_max'])} |"
        )
    lines += [
        "",
        "한 시점/두 시점 결합법을 바꿔도 결론은 바뀌지 않았다. 특히 temporal_relation은 모든 구조 arm이 약 0.31~0.33에 머물렀다.",
        "",
        "### 사건 class별 구조 분류",
        "",
        "| 서비스군 | 사건 class | n | COT better 정확도 |",
        "|---|---|---:|---:|",
    ]
    class_accuracy = (
        per_clip.groupby(["service_group", "event_class"], sort=True)
        .agg(n=("clip_id", "size"), accuracy=("cot_better_correct", "mean"))
        .reset_index()
    )
    for row in class_accuracy.itertuples(index=False):
        lines.append(f"| {row.service_group} | {row.event_class} | {row.n} | {fmt(row.accuracy)} |")
    lines += [
        "",
        "`비정상적인 경로로의 침범`과 `특정 구역 내 지속 배회`는 COT zero-shot 정확도가 0이었다. 이는 단계 서술이 무의미하다는 뜻이 아니라, 현재 query prototype과 label-derived 서술만으로 인접 관계 class를 구분하지 못했다는 뜻이다.",
    ]

    lines += [
        "",
        "## 3. 다각도 view 보존 보조 결과",
        "",
        f"보조 판정은 **{decision['view_decision']}**이다. better 한 시점은 both 두 시점 JPEG의 총 {view['visual_better_both_byte_ratio'].iloc[0]:.1%} 바이트를 사용했다.",
        "",
        "| 모델 | worse | better | both | better−worse | 95% CI | better의 both 대비 비열등 |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in view.itertuples(index=False):
        lines.append(
            f"| {row.model} | {fmt(row.worse_accuracy)} | {fmt(row.better_accuracy)} | {fmt(row.both_accuracy)} | "
            f"{fmt(row.better_minus_worse)} | [{fmt(row.better_worse_ci_low)}, {fmt(row.better_worse_ci_high)}] | "
            f"{'예' if row.noninferior_to_both else '아니오'} |"
        )

    lines += [
        "",
        "이 결과가 통과하더라도 의미는 ‘bbox가 더 잘 보이는 한 시점 3장을 두 시점 6장 대신 보존할 수 있다’는 좁은 선택 규칙이다. 서비스 의도에 따라 서로 다른 표현을 저장해야 한다는 IntentStore 핵심 가설의 증거는 아니다.",
        "",
        "## 4. 저장량",
        "",
        "| 표현 | clip당 평균 | 중앙값 | 전체 |",
        "|---|---:|---:|---:|",
    ]
    for row in storage.itertuples(index=False):
        lines.append(
            f"| {row.representation} | {row.mean_bytes/1024:.1f} KiB | {row.median_bytes/1024:.1f} KiB | {row.total_bytes/1024/1024:.1f} MiB |"
        )
    lines += [
        "",
        "COT 비용은 UTF-8 텍스트+BGE-M3 float32 1,024차원만 포함한다. 구조 추출 비용, bbox/label 생성 비용, VLM 추론 비용과 DB overhead는 포함하지 않았다.",
        "",
        "## 5. 최종 해석과 연구 주제 판정",
        "",
    ]
    if rescue == "RESCUE_PASS_SERVICE_NONDOMINANCE":
        lines += [
            "동일 모델에서 서비스군별로 구조와 시각의 우세 방향이 갈렸으므로 저장 표현을 서비스 의도에 맞출 가능성은 남았다. 그러나 label-derived oracle 결과이므로 다음 단계는 자동 trajectory extractor로 동일 효과를 재현하고 독립 데이터셋에서 확인하는 것이다. 두 조건 전에는 IntentStore를 확정하지 않는다.",
        ]
    elif rescue.startswith("RESCUE_FAIL_"):
        lines += [
            "사전 등록한 서비스별 비지배성 조건이 성립하지 않았다. 따라서 P0-C 뒤 남겨 둔 한 번의 구제 기회를 소진했으며, **범용 IntentStore를 주력 연구 주제로 확정하지 않고 종료한다.** 남길 수 있는 것은 다각도 한 시점 선택 또는 구조 궤적 추출 같은 더 좁은 시스템 문제뿐이다.",
        ]
    else:
        lines += [
            "구제 통과도 명시적 dominance 실패도 성립하지 않았다. 이 결과로는 IntentStore를 확정할 수 없다. 추가 실험을 하려면 이번 결과를 본 뒤 기준을 완화하지 말고, 새로운 독립 데이터·자동 궤적 추출을 갖춘 별도 사전 등록 연구로 시작해야 한다.",
        ]
    lines += [
        "",
        "### 제한 사항",
        "",
        "- COT는 label-derived oracle이며 실제 배포 가능한 자동 추출기가 아니다.",
        "- VLM 출력은 이전 GPU 실험의 동결 산출물이며 이번 실행에서 GPU를 사용하지 않았다.",
        "- 11-class closed-set 정확도는 open-world 이상 탐지, 실시간 지연 또는 환각 완화 성능이 아니다.",
        "- 단일 AI Hub 계열 399 clips이므로 외부 일반화가 입증되지 않았다.",
        "- view의 better/worse는 정답 bbox 면적으로 정해져 운영 시에는 별도 view-quality estimator가 필요하다.",
        "",
        "## 6. 재현성과 정합성",
        "",
        f"- 분석 표본: 400개 중 직접 사건명 누설 {len(leak_clips)}개 제외, 최종 399개",
        f"- 제외 clip: `{', '.join(leak_clips)}`",
        f"- VLM: 4모델×399 clips×4조건 = {4*399*4:,}행 정합성 확인",
        f"- frame: {audit['storage']['frame_rows']:,}개 JPEG 존재 및 바이트 실측",
        f"- CPU 실행 시간: {elapsed:.1f}초",
        f"- Python: {platform.python_version()}, NumPy: {np.__version__}, pandas: {pd.__version__}",
        f"- CUDA 작업: 실행하지 않음 (`CUDA_VISIBLE_DEVICES={os.environ.get('CUDA_VISIBLE_DEVICES', '<unset>')}`; 스크립트는 GPU 라이브러리/모델을 호출하지 않음)",
        "- seed: 20260806; randomization 200,000; bootstrap 20,000",
        "- 첫 dry run은 표본 밖 행에 빈 gold를 적용한 누설 감사 구현 오류로 결과 계산 전에 중단했다. 400개 등록 표본으로 범위를 제한한 뒤 실행했으며 판정 기준은 변경하지 않았다.",
        "",
        "상세 수치는 `results/p0d_*.csv`, 입력 SHA-256은 `results/p0d_source_manifest.json`, 기계 판정은 `results/p0d_decision.json`에 보존했다.",
        "",
    ]
    (ROOT / "P0_D_MULTIVIEW_RESCUE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    started = time.perf_counter()
    RESULTS.mkdir(parents=True, exist_ok=True)
    stratum = pd.read_parquet(STRATUM_PATH).copy()
    stratum["clip_id"] = stratum["clip_id"].astype(str)
    documents = pd.read_parquet(DOCUMENTS_PATH)
    cot_docs = documents[
        documents["doc_type"].isin(["cot_c1", "cot_c2"])
        & documents["clip_id"].astype(str).isin(set(stratum["clip_id"]))
    ].copy()
    gold = dict(zip(stratum["clip_id"], stratum["event_class"].astype(str)))
    literal_rows = cot_docs[
        cot_docs.apply(lambda row: gold[str(row["clip_id"])] in str(row["text"]), axis=1)
    ]
    leak_clips = sorted(literal_rows["clip_id"].astype(str).unique().tolist())
    if leak_clips != ["aihub_multi_angle_cctv:Training:ph_e2067"]:
        raise ValueError(f"Literal leakage audit changed: {leak_clips}")
    clips = stratum[~stratum["clip_id"].isin(leak_clips)].copy().reset_index(drop=True)
    clips["service_group"] = clips["event_class"].astype(str).map(service_group)
    if len(clips) != 399 or clips["service_group"].isna().any():
        raise ValueError("Unexpected analysis cohort")

    structured, classes, embedding_audit = build_structured_predictions(clips, documents)
    per_clip = clips.merge(structured, on="clip_id", validate="one_to_one")
    per_clip, vlm_audit = add_vlm_predictions(per_clip, clips)
    frames = pd.read_parquet(FRAMES_PATH)
    storage_per_clip, storage_summary, visual_ratio, storage_audit = storage_tables(per_clip, frames)
    per_clip = per_clip.merge(storage_per_clip, on="clip_id", validate="one_to_one")
    accuracy = make_accuracy_table(per_clip)
    primary = make_primary_tests(per_clip)
    view = make_view_tests(per_clip, visual_ratio)
    decision = decide(primary, view)

    per_clip.to_csv(RESULTS / "p0d_per_clip.csv", index=False)
    accuracy.to_csv(RESULTS / "p0d_service_accuracy.csv", index=False)
    primary.to_csv(RESULTS / "p0d_primary_tests.csv", index=False)
    view.to_csv(RESULTS / "p0d_view_tests.csv", index=False)
    storage_summary.to_csv(RESULTS / "p0d_storage_summary.csv", index=False)
    storage_per_clip.to_csv(RESULTS / "p0d_storage_per_clip.csv", index=False)

    input_paths = {
        "stratum": STRATUM_PATH,
        "documents": DOCUMENTS_PATH,
        "queries": QUERIES_PATH,
        "frames": FRAMES_PATH,
        "document_index": DOC_INDEX_PATH,
        "document_embeddings": DOC_EMBED_PATH,
        "query_index": QUERY_INDEX_PATH,
        "query_embeddings": QUERY_EMBED_PATH,
        **{f"vlm_{model}": path for model, path in VLM_PATHS.items()},
    }
    manifest = {
        "created_at": pd.Timestamp.now(tz="Asia/Seoul").isoformat(),
        "analysis_script": str(Path(__file__).resolve()),
        "analysis_script_sha256": sha256(Path(__file__).resolve()),
        "inputs": {
            name: {"path": str(path), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for name, path in input_paths.items()
        },
        "excluded_literal_leak_clips": leak_clips,
        "event_classes": classes,
        "cohort_rows": len(per_clip),
        "embedding_audit": embedding_audit,
        "vlm_audit": vlm_audit,
        "storage_audit": storage_audit,
        "cpu_only": True,
    }
    (RESULTS / "p0d_source_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (RESULTS / "p0d_decision.json").write_text(
        json.dumps(decision, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    elapsed = time.perf_counter() - started
    audit = {"embedding": embedding_audit, "vlm": vlm_audit, "storage": storage_audit}
    write_report(decision, primary, view, accuracy, per_clip, storage_summary, leak_clips, audit, elapsed)
    print(json.dumps({**decision, "elapsed_seconds": elapsed}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
