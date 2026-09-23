#!/usr/bin/env python3
"""Summarize the fixed-seed and multi-seed Qwen-2048 scale benchmark."""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROOT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260717_joint_optimization_validation"


def parse_args():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    return p.parse_args()


def config_name(row) -> str:
    if row.kind == "flat":
        return "Flat"
    if row.kind == "hnsw":
        return f"HNSW M{int(row.M)} ef{int(row.efSearch)}"
    if row.kind == "ivfflat":
        return f"IVF-Flat nlist{int(row.nlist)} np{int(row.nprobe)}"
    return f"IVF-PQ nlist{int(row.nlist)} m{int(row.m)} np{int(row.nprobe)}"


def pareto(frame: pd.DataFrame) -> np.ndarray:
    recall = frame.recall_at_10.to_numpy()
    latency = frame.p95_ms.to_numpy()
    storage = frame.index_mb.to_numpy()
    keep = np.ones(len(frame), bool)
    for i in range(len(frame)):
        dominate = (
            (recall >= recall[i]) & (latency <= latency[i]) & (storage <= storage[i])
            & ((recall > recall[i]) | (latency < latency[i]) | (storage < storage[i]))
        )
        dominate[i] = False
        keep[i] = not dominate.any()
    return keep


def main() -> int:
    args = parse_args()
    scaled_root = args.root / "qwen2048_scaled_index"
    seed_root = args.root / "qwen2048_seed_robustness"
    frame = pd.read_csv(scaled_root / "index_benchmark.csv")
    full = frame[frame.N == 143830].copy()
    full["config"] = [config_name(row) for row in full.itertuples(index=False)]
    full["pareto"] = pareto(full)
    flat_p95 = float(full[full.kind == "flat"].p95_ms.iloc[0])
    full["p95_speedup_vs_flat"] = flat_p95 / full.p95_ms
    full.to_csv(scaled_root / "full_scale_analyzed.csv", index=False)
    full[full.pareto].to_csv(scaled_root / "pareto_front.csv", index=False)

    high = full[full.recall_at_10 >= 0.98].sort_values(["p95_ms", "index_mb"])
    seed = pd.read_csv(seed_root / "seed_summary.csv")
    h_seed = seed[(seed.structure == "hnsw") & (seed.efSearch == 256)].iloc[0]
    i_seed = seed[(seed.structure == "ivfflat") & (seed.nprobe == 128)].iloc[0]
    h32 = full[(full.kind == "hnsw") & (full.M == 32) & (full.efSearch == 256)].iloc[0]
    h16 = full[(full.kind == "hnsw") & (full.M == 16) & (full.efSearch == 256)].iloc[0]
    pq = full[full.kind == "ivfpq"].sort_values("recall_at_10", ascending=False).iloc[0]
    report = f"""# Qwen3-VL 2,048차원 대규모 색인 검증

- corpus: 143,830 real frame vectors, query: 85 text vectors
- fixed construction seed: 20260717
- scale sweep: 10k, 50k, 100k, 143,830

## 최종 규모

- Flat: recall 1.0000, p95 {flat_p95:.3f} ms, {float(full[full.kind == 'flat'].index_mb.iloc[0]):.2f} MB
- HNSW M16/ef256: recall {h16.recall_at_10:.4f}, p95 {h16.p95_ms:.3f} ms, speedup {h16.p95_speedup_vs_flat:.1f}x
- HNSW M32/ef256: recall {h32.recall_at_10:.4f}, p95 {h32.p95_ms:.3f} ms, speedup {h32.p95_speedup_vs_flat:.1f}x
- best observed PQ recall: {pq.recall_at_10:.4f}, size {pq.index_mb:.2f} MB

## 3개 구축 시드 강건성

- HNSW M32/ef256 recall: mean {h_seed.recall_mean:.4f}, std {h_seed.recall_std:.4f}, range [{h_seed.recall_min:.4f}, {h_seed.recall_max:.4f}]
- IVF-Flat nlist1024/nprobe128 recall: mean {i_seed.recall_mean:.4f}, std {i_seed.recall_std:.4f}, range [{i_seed.recall_min:.4f}, {i_seed.recall_max:.4f}]

어느 후보도 3개 시드 모두에서 recall 0.99 이상을 보장하지 않았다. 따라서 단일 시드 점 추정치를
고정 보장으로 표현하지 않고, 고정밀 배치에서는 시드별 검증 또는 더 큰 efSearch/nprobe가 필요하다.
또한 기존 CLIP-512의 ef64 설정을 Qwen-2048에 그대로 이전할 수 없었다.
"""
    (scaled_root / "RESULTS_KO.md").write_text(report, encoding="utf-8")
    print(report)
    print("high-fidelity fixed-seed configurations")
    print(high[["config", "recall_at_10", "p95_ms", "index_mb", "build_s"]].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
