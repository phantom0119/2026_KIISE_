#!/usr/bin/env python3
"""Prepare the frozen, class-balanced S4 three-class perception gate.

No model output is read here. Selection is deterministic and outcome-blind.
Distractors have a different class and are matched, in order, on
intersection+hour, intersection, hour, or globally.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from itertools import permutations
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VER = PROJECT_ROOT / "Datasets" / "processed" / "aihub_522_intersection" / "20260710"
DEFAULT_OUT = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets"
    / "20260723_controlled_supplement" / "s4_mcq_gate"
)
CLASS_ORDER = ("0", "1", "2+")
CATEGORIES = {
    "bus_count": {
        "column": "n_bus",
        "phrases": {"0": "no buses", "1": "one bus", "2+": "two or more buses"},
        "question": "How many buses are visible in this CCTV frame?",
    },
    "bike_count": {
        "column": "n_bike",
        "phrases": {
            "0": "no bicycles or motorbikes",
            "1": "one bicycle or motorbike",
            "2+": "two or more bicycles or motorbikes",
        },
        "question": "How many bicycles or motorbikes are visible in this CCTV frame?",
    },
}


def sha256_file(path: Path, chunk_size: int = 1 << 20) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def stable_hash(*parts: object) -> str:
    return hashlib.sha256(":".join(map(str, parts)).encode()).hexdigest()


def to_class(value: float) -> str:
    if value < 0.5:
        return "0"
    if value < 1.5:
        return "1"
    return "2+"


def option_payload(category: str, item_id: str) -> tuple[str, str]:
    options = list(permutations(CLASS_ORDER))
    order = options[int(stable_hash("option", category, item_id), 16) % len(options)]
    labels = ("A", "B", "C")
    phrases = CATEGORIES[category]["phrases"]
    rendered = "; ".join(f"{label}) {phrases[value]}" for label, value in zip(labels, order))
    mapping = {label: value for label, value in zip(labels, order)}
    prompt = (
        f"{CATEGORIES[category]['question']} Choose exactly one: {rendered}. "
        "Answer with only A, B, or C."
    )
    return prompt, json.dumps(mapping, sort_keys=True)


def choose_distractor(pool: pd.DataFrame, source: pd.Series, category: str) -> tuple[pd.Series, str]:
    candidates = pool[
        (pool[category] != source[category])
        & (pool["row"] != source["row"])
        & (pool["visual_video_id"] != source["visual_video_id"])
    ]
    levels = [
        ("intersection_hour", (candidates["intersection_id"] == source["intersection_id"])
         & (candidates["hour"] == source["hour"])),
        ("intersection", candidates["intersection_id"] == source["intersection_id"]),
        ("hour", candidates["hour"] == source["hour"]),
        ("global", pd.Series(True, index=candidates.index)),
    ]
    for level, mask in levels:
        eligible = candidates[mask]
        if len(eligible):
            order = eligible.apply(
                lambda row: stable_hash(
                    "distractor", category, source["item_id"], row["row"]
                ),
                axis=1,
            )
            return eligible.loc[order.idxmin()], level
    raise RuntimeError(f"no class-mismatched distractor for {source['item_id']} {category}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--items-per-class", type=int, default=60)
    parser.add_argument("--seed", type=int, default=20260723)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    if args.output_dir.exists() and any(args.output_dir.iterdir()) and not args.overwrite:
        raise FileExistsError(f"{args.output_dir} is not empty; pass --overwrite")
    args.output_dir.mkdir(parents=True, exist_ok=True)

    annotation_path = VER / "annotation_frame_facets.parquet"
    frame_index_path = VER / "visual_embeddings_clip" / "frame_index.parquet"
    hashes = {
        "annotation_frame_facets.parquet": sha256_file(annotation_path),
        "frame_index.parquet": sha256_file(frame_index_path),
    }
    expected = {
        "annotation_frame_facets.parquet": "4c9bbefb6be3d989d359ffc510fe9b36403caab270b90e0c468bd888b7b0a663",
        "frame_index.parquet": "f8aba458c5b0712ea3439dc4905372354afe3da9b832023c5b0baad8920210a4",
    }
    if hashes != expected:
        raise ValueError(f"frozen input hash mismatch: {hashes}")

    annotations = pd.read_parquet(annotation_path)
    annotations = annotations[annotations["ann_source"] == "TL_3_polyline"][
        ["split", "visual_video_id", "frame", "n_bus", "n_bike"]
    ].copy()
    frame_index = pd.read_parquet(frame_index_path).reset_index(names="row")
    frame = frame_index.merge(
        annotations,
        on=["split", "visual_video_id", "frame"],
        how="inner",
        validate="one_to_one",
    )
    frame = frame.dropna(subset=["n_bus", "n_bike"]).copy()
    frame["item_id"] = (
        frame["split"].astype(str) + ":" + frame["visual_video_id"].astype(str)
        + ":" + frame["frame"].astype(str)
    )
    for category, spec in CATEGORIES.items():
        frame[category] = frame[spec["column"]].map(to_class)

    rows: list[dict] = []
    selected_source_rows: set[int] = set()
    for category in CATEGORIES:
        for class_value in CLASS_ORDER:
            eligible = frame[
                (frame[category] == class_value)
                & (~frame["row"].isin(selected_source_rows))
            ].copy()
            eligible["_stable"] = eligible["item_id"].map(
                lambda item_id: stable_hash(args.seed, category, class_value, item_id)
            )
            selected = eligible.sort_values("_stable").head(args.items_per_class)
            if len(selected) != args.items_per_class:
                raise ValueError(
                    f"not enough {category}={class_value}: {len(selected)} < {args.items_per_class}"
                )
            for _, source in selected.iterrows():
                prompt, option_map = option_payload(category, source["item_id"])
                distractor, match_level = choose_distractor(frame, source, category)
                selected_source_rows.add(int(source["row"]))
                common = {
                    "item_id": source["item_id"],
                    "category": category,
                    "gold_class": class_value,
                    "source_row": int(source["row"]),
                    "source_relpath": source["relpath"],
                    "source_intersection_id": str(source["intersection_id"]),
                    "source_hour": int(source["hour"]),
                    "option_map": option_map,
                    "prompt": prompt,
                }
                rows.extend(
                    [
                        {
                            **common,
                            "condition": "closed",
                            "evidence_row": -1,
                            "evidence_relpath": None,
                            "distractor_match_level": None,
                        },
                        {
                            **common,
                            "condition": "distractor",
                            "evidence_row": int(distractor["row"]),
                            "evidence_relpath": distractor["relpath"],
                            "evidence_class": distractor[category],
                            "distractor_match_level": match_level,
                        },
                        {
                            **common,
                            "condition": "oracle",
                            "evidence_row": int(source["row"]),
                            "evidence_relpath": source["relpath"],
                            "evidence_class": class_value,
                            "distractor_match_level": None,
                        },
                    ]
                )

    plan = pd.DataFrame(rows)
    if plan.duplicated(["item_id", "category", "condition"]).any():
        raise AssertionError("duplicate gate item-condition")
    counts = plan.groupby(["category", "gold_class", "condition"]).size()
    if not (counts == args.items_per_class).all():
        raise AssertionError(f"unbalanced gate plan: {counts.to_dict()}")
    distractors = plan[plan["condition"] == "distractor"]
    if (distractors["evidence_class"] == distractors["gold_class"]).any():
        raise AssertionError("distractor with the same class")

    manifest = {
        "script": Path(__file__).name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "parameters": {
            "items_per_class": args.items_per_class,
            "seed": args.seed,
            "categories": list(CATEGORIES),
            "classes": list(CLASS_ORDER),
            "conditions": ["closed", "distractor", "oracle"],
        },
        "input_sha256": hashes,
        "rows": int(len(plan)),
        "unique_source_items": int(plan[["item_id", "category"]].drop_duplicates().shape[0]),
        "distractor_match_counts": distractors["distractor_match_level"].value_counts().to_dict(),
        "option_order_rule": "one of six permutations selected by sha256(category,item_id)",
        "selection_uses_model_outputs": False,
    }
    plan.to_parquet(args.output_dir / "gate_plan.parquet", index=False)
    (args.output_dir / "gate_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
