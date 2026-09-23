#!/usr/bin/env python3
"""Label-grounded lexical diagnostics for generated caption documents.

These diagnostics are deliberately secondary: the parser measures whether the
searchable text states a labeled concept, not full image-caption factuality.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROOT = Path("/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715")
DEFAULT_OUT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260715_caption_model_ablation"
MODELS = ["qwen25vl_7b", "qwen3vl_8b", "qwen35_9b"]


def binary_metrics(truth: np.ndarray, prediction: np.ndarray) -> dict:
    truth = truth.astype(bool)
    prediction = prediction.astype(bool)
    tp = int((truth & prediction).sum())
    tn = int((~truth & ~prediction).sum())
    fp = int((~truth & prediction).sum())
    fn = int((truth & ~prediction).sum())
    recall = tp / (tp + fn) if tp + fn else float("nan")
    specificity = tn / (tn + fp) if tn + fp else float("nan")
    precision = tp / (tp + fp) if tp + fp else float("nan")
    return {
        "n": len(truth),
        "prevalence": float(truth.mean()),
        "predicted_rate": float(prediction.mean()),
        "precision": precision,
        "recall": recall,
        "specificity": specificity,
        "balanced_accuracy": (recall + specificity) / 2,
        "tp": tp,
        "tn": tn,
        "fp": fp,
        "fn": fn,
    }


def stated_positive(text: str, concept: str) -> bool:
    if not re.search(concept, text, re.IGNORECASE):
        return False
    neg_before = rf"\b(?:no|not|without|none|neither)\b(?:\W+\w+){{0,5}}\W+(?:{concept})"
    neg_after = rf"(?:{concept})(?:\W+\w+){{0,4}}\W+\b(?:not|absent|visible)\b"
    if re.search(neg_before, text, re.IGNORECASE):
        return False
    if re.search(neg_after, text, re.IGNORECASE) and re.search(r"not\s+visible|none\s+visible|absent", text, re.I):
        return False
    return True


def analyze_522(root: Path) -> list[dict]:
    ann_path = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710" / "annotation_video_facets.parquet"
    ann = pd.read_parquet(ann_path)
    definitions = {
        "parked_vehicle": (lambda d: d["any_parked"].astype(bool), r"park(?:ed|ing)"),
        "stopped_vehicle": (lambda d: d["any_stopped"].astype(bool), r"stopp(?:ed|ing)|stationary|queued"),
        "bus_present": (lambda d: d["max_bus"] >= 1, r"\bbus(?:es)?\b"),
        "multiple_buses": (lambda d: d["max_bus"] >= 2, r"\bbuses\b|(?:two|2|multiple|several)\W+bus"),
        "two_plus_bikes": (lambda d: d["max_bike"] >= 2, r"\b(?:bicycles|motorbikes|motorcycles)\b|(?:two|2|multiple|several)\W+(?:bikes?|cycles?)"),
        "dense_frame": (lambda d: d["max_objects"] >= 20, r"\b(?:dense|congested|crowded|heavy|high)\W+(?:traffic|volume)|traffic\W+(?:congestion|jam)"),
    }
    rows = []
    for model in MODELS:
        caps = pd.read_parquet(root / model / "522" / "captions" / "caption_records.parquet")
        data = caps.merge(ann, on=["visual_video_id", "split"], how="inner", validate="one_to_one")
        for label, (truth_fn, pattern) in definitions.items():
            truth = truth_fn(data).to_numpy(bool)
            prediction = data["caption"].map(lambda text: stated_positive(str(text), pattern)).to_numpy(bool)
            rows.append({"dataset": "522", "model": model, "label": label, **binary_metrics(truth, prediction)})
    return rows


def analyze_uca(root: Path) -> list[dict]:
    sys.path.insert(0, str(PROJECT_ROOT / "2026_KIISE" / "scripts"))
    from build_uca_corpus import LEX  # noqa: WPS433

    uca_root = PROJECT_ROOT / "Datasets" / "processed" / "uca_anchor" / "20260712"
    rel = pd.read_parquet(uca_root / "relevance.parquet").set_index("doc_id")
    rows = []
    for model in MODELS:
        caps = pd.read_parquet(root / model / "uca" / "captions" / "caption_records.parquet").set_index("item_id")
        ids = caps.index.intersection(rel.index)
        texts = caps.loc[ids, "caption"].astype(str)
        for label, pattern in LEX.items():
            truth = rel.loc[ids, f"rel_{label}"].to_numpy(bool)
            prediction = texts.str.contains(pattern, case=False, regex=True).to_numpy(bool)
            rows.append({"dataset": "uca", "model": model, "label": label, **binary_metrics(truth, prediction)})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    result = pd.DataFrame([*analyze_522(args.root), *analyze_uca(args.root)])
    result.to_csv(args.output_dir / "caption_label_diagnostics.csv", index=False)
    print(result.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
