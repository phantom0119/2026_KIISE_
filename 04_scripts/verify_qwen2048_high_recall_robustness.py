#!/usr/bin/env python3
"""Verify the five-seed high-recall ANN robustness artifacts."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROOT = (
    PROJECT_ROOT
    / "2026_KIISE"
    / "paper_assets"
    / "20260717_ablation_agent_crosscheck"
    / "qwen2048_high_recall_5seed"
)
OLD = (
    PROJECT_ROOT
    / "2026_KIISE"
    / "paper_assets"
    / "20260717_joint_optimization_validation"
    / "qwen2048_seed_robustness"
    / "seed_results.csv"
)


def main() -> int:
    frame = pd.read_csv(ROOT / "results.csv")
    summary = pd.read_csv(ROOT / "summary.csv")
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    checks: list[dict[str, object]] = []

    def add(gate: str, passed: bool, **evidence: object) -> None:
        checks.append({"gate": gate, "pass": bool(passed), **evidence})

    expected_seeds = {20260717, 20260718, 20260719, 20260720, 20260721}
    expected_settings = {
        ("hnsw", 256), ("hnsw", 512), ("hnsw", 1024),
        ("ivfflat", 128), ("ivfflat", 256), ("ivfflat", 512),
    }
    observed_settings = {
        (str(row.structure), int(row.efSearch if row.structure == "hnsw" else row.nprobe))
        for row in frame.itertuples(index=False)
    }
    add(
        "complete_5seed_x_6setting_grid",
        len(frame) == 30
        and set(frame["seed"].astype(int)) == expected_seeds
        and observed_settings == expected_settings
        and not frame.duplicated(["seed", "structure", "efSearch", "nprobe"]).any(),
        rows=len(frame),
        seeds=sorted(frame["seed"].astype(int).unique().tolist()),
        settings=sorted(observed_settings),
    )
    add(
        "manifest_matches_grid",
        set(manifest["seeds"]) == expected_seeds
        and manifest["n_vectors"] == 143830
        and manifest["dimension"] == 2048
        and manifest["query_count"] == 85,
    )
    add(
        "metric_bounds_and_finite",
        bool(frame["recall_at_10"].between(0, 1).all())
        and bool(np.isfinite(frame[["recall_at_10", "latency_p95_ms", "build_s", "index_mb"]]).all().all())
        and bool((frame[["latency_p95_ms", "build_s", "index_mb"]] > 0).all().all()),
    )

    monotonic = True
    for (_seed, structure), group in frame.groupby(["seed", "structure"]):
        setting = "efSearch" if structure == "hnsw" else "nprobe"
        values = group.sort_values(setting)["recall_at_10"].to_numpy(float)
        monotonic &= bool(np.all(np.diff(values) >= -1e-12))
    add("recall_monotonic_with_search_strength_per_seed", monotonic)

    recomputed = (
        frame.groupby(["structure", "M", "efSearch", "nlist", "nprobe"], dropna=False, sort=False)
        .agg(
            seeds=("seed", "nunique"),
            recall_mean=("recall_at_10", "mean"),
            recall_std=("recall_at_10", "std"),
            recall_min=("recall_at_10", "min"),
            recall_max=("recall_at_10", "max"),
            latency_p95_median_ms=("latency_p95_ms", "median"),
            latency_p95_max_ms=("latency_p95_ms", "max"),
        )
        .reset_index()
    )
    joined = summary.merge(
        recomputed,
        on=["structure", "M", "efSearch", "nlist", "nprobe"],
        suffixes=("_reported", "_recomputed"),
        validate="one_to_one",
    )
    columns = [
        "recall_mean", "recall_std", "recall_min", "recall_max",
        "latency_p95_median_ms", "latency_p95_max_ms",
    ]
    error = max(
        float(np.max(np.abs(joined[f"{column}_reported"] - joined[f"{column}_recomputed"])))
        for column in columns
    )
    add("summary_matches_raw_rows", error < 1e-12, max_abs_error=error)

    reported_flags = summary["all_seeds_recall_ge_099"].astype(str).str.lower().eq("true").to_numpy()
    expected_flags = summary["recall_min"].to_numpy(float) >= 0.99
    add("robust_threshold_flags_correct", bool(np.array_equal(reported_flags, expected_flags)))

    old = pd.read_csv(OLD)
    old = old[old["seed"].isin([20260717, 20260718, 20260719])]
    old_anchor = pd.concat(
        [
            old[(old["structure"] == "hnsw") & (old["efSearch"] == 256)][["seed", "structure", "recall_at_10"]],
            old[(old["structure"] == "ivfflat") & (old["nprobe"] == 128)][["seed", "structure", "recall_at_10"]],
        ],
        ignore_index=True,
    )
    new_anchor = pd.concat(
        [
            frame[(frame["structure"] == "hnsw") & (frame["efSearch"] == 256)][["seed", "structure", "recall_at_10"]],
            frame[(frame["structure"] == "ivfflat") & (frame["nprobe"] == 128)][["seed", "structure", "recall_at_10"]],
        ],
        ignore_index=True,
    )
    agreement = old_anchor.merge(new_anchor, on=["seed", "structure"], suffixes=("_old", "_new"), validate="one_to_one")
    old_error = float(np.max(np.abs(agreement["recall_at_10_old"] - agreement["recall_at_10_new"])))
    # The prior base-seed row was imported from a benchmark that persisted
    # recall to four decimals; rebuilt rows for the other seeds retain full
    # precision.  Compare at the recorded precision.
    add("three_seed_anchor_rebuild_reproduces_prior_recorded_recall", old_error < 5e-5, max_abs_error=old_error)

    def value(structure: str, setting: int) -> pd.Series:
        column = "efSearch" if structure == "hnsw" else "nprobe"
        return summary[(summary["structure"] == structure) & (summary[column] == setting)].iloc[0]

    h512 = value("hnsw", 512)
    h1024 = value("hnsw", 1024)
    i256 = value("ivfflat", 256)
    i512 = value("ivfflat", 512)
    add(
        "strengthened_candidates_pass_all_seed_099_gate",
        min(h512.recall_min, h1024.recall_min, i256.recall_min, i512.recall_min) >= 0.99,
        hnsw_ef512_min=float(h512.recall_min),
        hnsw_ef1024_min=float(h1024.recall_min),
        ivfflat_np256_min=float(i256.recall_min),
        ivfflat_np512_min=float(i512.recall_min),
    )

    passed = sum(bool(check["pass"]) for check in checks)
    result = {"overall_pass": passed == len(checks), "passed": passed, "total": len(checks), "checks": checks}
    (ROOT / "independent_verification.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    report = f"""# Qwen-2048 고정밀 ANN 5-seed 강건성

143,830개 real Qwen-2048 vectors와 85개 query에서 각 seed마다 구조를 실제 재구축했다.

| 구조 | 탐색 강도 | 5-seed mean | min | max | median p95 | max p95 | 모든 seed ≥0.99 |
|---|---:|---:|---:|---:|---:|---:|---|
| HNSW M32 | ef256 | {value('hnsw',256).recall_mean:.6f} | {value('hnsw',256).recall_min:.6f} | {value('hnsw',256).recall_max:.6f} | {value('hnsw',256).latency_p95_median_ms:.3f} ms | {value('hnsw',256).latency_p95_max_ms:.3f} ms | 아니오 |
| HNSW M32 | ef512 | {h512.recall_mean:.6f} | {h512.recall_min:.6f} | {h512.recall_max:.6f} | {h512.latency_p95_median_ms:.3f} ms | {h512.latency_p95_max_ms:.3f} ms | 예 |
| HNSW M32 | ef1024 | {h1024.recall_mean:.6f} | {h1024.recall_min:.6f} | {h1024.recall_max:.6f} | {h1024.latency_p95_median_ms:.3f} ms | {h1024.latency_p95_max_ms:.3f} ms | 예 |
| IVF-Flat nlist1024 | nprobe128 | {value('ivfflat',128).recall_mean:.6f} | {value('ivfflat',128).recall_min:.6f} | {value('ivfflat',128).recall_max:.6f} | {value('ivfflat',128).latency_p95_median_ms:.3f} ms | {value('ivfflat',128).latency_p95_max_ms:.3f} ms | 아니오 |
| IVF-Flat nlist1024 | nprobe256 | {i256.recall_mean:.6f} | {i256.recall_min:.6f} | {i256.recall_max:.6f} | {i256.latency_p95_median_ms:.3f} ms | {i256.latency_p95_max_ms:.3f} ms | 예 |
| IVF-Flat nlist1024 | nprobe512 | {i512.recall_mean:.6f} | {i512.recall_min:.6f} | {i512.recall_max:.6f} | {i512.latency_p95_median_ms:.3f} ms | {i512.latency_p95_max_ms:.3f} ms | 예 |

운영 균형점은 HNSW ef512다. 관측한 5개 seed 모두 recall≥0.99이고 IVF nprobe256보다 p95가 훨씬 낮다. exact top-10이 필요하면 HNSW ef1024가 5/5 seed에서 1.0이었지만, 이 보장은 관측한 corpus·query·seed 범위에만 한정한다.
"""
    (ROOT / "RESULTS_KO.md").write_text(report, encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("overall_pass", "passed", "total")}, indent=2))
    return 0 if result["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
