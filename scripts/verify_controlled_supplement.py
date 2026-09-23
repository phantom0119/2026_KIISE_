#!/usr/bin/env python3
"""Regression checks for the 2026-07-23 controlled supplement."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROOT = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260723_controlled_supplement"
)
MANUSCRIPT = PROJECT_ROOT / "2026_KIISE" / "manuscript"


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def check_receipt(directory: Path) -> None:
    receipt = directory / "sha256.txt"
    if not receipt.exists():
        raise AssertionError(f"missing receipt: {receipt}")
    for line in receipt.read_text(encoding="utf-8").splitlines():
        expected, filename = line.split("  ", 1)
        observed = sha256_file(directory / filename)
        if observed != expected:
            raise AssertionError(f"hash mismatch: {directory / filename}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--require-e0", action="store_true")
    args = parser.parse_args()
    passed: list[str] = []

    protocol = json.loads((ROOT / "protocol_manifest.json").read_text(encoding="utf-8"))
    assert protocol["global_seed"] == 20260723
    check_receipt(ROOT)
    passed.append("protocol manifest, top-level reproducibility receipt, and frozen seed")

    s2_dir = ROOT / "s2_blocked_coupling"
    check_receipt(s2_dir)
    s2 = json.loads((s2_dir / "summary.json").read_text(encoding="utf-8"))
    assert s2["families"] == 25 and s2["queries"] == 85 and s2["intersections"] == 63
    assert not s2["promotion_gate"]["all_pass"]
    passed.append("S2 dimensions and no-promotion gate")

    s3_root = ROOT / "s3_cluster_mechanism"
    for corpus, predicates in (("A", 24), ("B", 22)):
        for method in ("hnsw", "ivf"):
            directory = s3_root / f"corpus_{corpus}_{method}"
            check_receipt(directory)
            summary = json.loads((directory / "summary.json").read_text(encoding="utf-8"))
            assert summary["natural_predicates"] == predicates
            assert summary["shuffle_repetitions"] == 100
            assert summary["synthetic_anchors"] == 10
            assert summary["gates"][method]["within_corpus_pass"]
            aggregate = pd.read_csv(directory / "aggregate.csv")
            natural = aggregate[aggregate["mask_type"] == "natural"]
            shuffled = aggregate[aggregate["mask_type"] == "shuffle"]
            synthetic = aggregate[aggregate["mask_type"] == "synthetic"]
            assert len(natural) == predicates
            assert len(shuffled) == predicates * 100
            assert len(synthetic) == 4 * 5 * 10
            natural_counts = natural.set_index("name")["count"]
            shuffled_counts = shuffled.groupby("name")["count"].agg(["min", "max"])
            assert (
                shuffled_counts["min"].eq(natural_counts)
                & shuffled_counts["max"].eq(natural_counts)
            ).all(), f"shuffle count changed in {directory}"
            assert aggregate["mask_sha256"].nunique() == len(aggregate)
    combined = json.loads((s3_root / "combined_summary.json").read_text(encoding="utf-8"))
    assert combined["all_four_cells_pass"]
    passed.append("S3 four cells, row counts, selectivity controls, and gates")

    s4_gate = ROOT / "s4_mcq_gate"
    check_receipt(s4_gate)
    gate_plan = pd.read_parquet(s4_gate / "gate_plan.parquet")
    assert len(gate_plan) == 1080
    assert not list(s4_gate.glob("gate_results_*.parquet"))
    s4_population = ROOT / "s4_retrieval_population"
    check_receipt(s4_population)
    s4 = json.loads((s4_population / "summary.json").read_text(encoding="utf-8"))
    assert not s4["categories"]["bus_count"]["retrieval_gate"]["all_pass"]
    assert not s4["categories"]["bike_count"]["retrieval_gate"]["all_pass"]
    passed.append("S4 fixed gate plan and principled pre-VLM stop")

    expected_pdf_hashes = {
        "paper_final.pdf": "a954978549694a081c67e27b070537dbd0305159c7b318a0299ba1a3ef3b7cfd",
        "DB연구_최종본양식.pdf": "28166b78ca9fe7f9b97a53355736a87e9e05e8a74d9baa22030375fb1cb961e4",
    }
    for filename, expected in expected_pdf_hashes.items():
        assert sha256_file(MANUSCRIPT / filename) == expected
    passed.append("submitted paper and template PDFs unchanged")

    e0_summary = ROOT / "e0_prompt_target_ablation" / "summary.json"
    if args.require_e0:
        assert e0_summary.exists(), "E0 is required but incomplete"
    if e0_summary.exists():
        e0 = json.loads(e0_summary.read_text(encoding="utf-8"))
        assert e0["primary"]["queries"] == 85
        assert e0["primary"]["families"] == 25
        assert abs(e0["primary"]["task_aware"] - 0.17003348904727908) < 1e-12
        assert abs(e0["primary"]["task_neutral"] - 0.08550832450219988) < 1e-12
        assert abs(e0["primary"]["relative_drop"] - 0.49710892259333894) < 1e-12
        assert e0["adverse_prompt_sensitivity_large_by_frozen_rule"]
        manifest = json.loads(
            (e0_summary.parent / "manifest.json").read_text(encoding="utf-8")
        )
        assert (
            manifest["input_sha256"]["base_queries"]
            == manifest["input_sha256"]["neutral_queries"]
            == "e7f7ac5c312de626ca964792fc7822bd2e7f39c1096ade3260b481f10c054a1f"
        )
        equalities = manifest["controlled_equalities"]
        assert equalities["caption_frame_identities"] == 3000
        assert equalities["queries_equal"]
        assert equalities["strict_qrels_equal_after_sort"]
        assert equalities["semantic_qrels_equal_after_sort"]
        assert equalities["metadata_equal_after_sort"]
        assert (
            manifest["prompt_sha256"]["base"]
            != manifest["prompt_sha256"]["neutral"]
        )
        check_receipt(e0_summary.parent)
        passed.append(
            "E0 generation controls, frames, queries, qrels, metadata, adverse gate, and receipt"
        )

    for item in passed:
        print(f"PASS  {item}")
    print(f"total={len(passed)} fail=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
