#!/usr/bin/env python3
"""Generate the compact S3 mechanism-control supplemental figure."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ROOT = (
    PROJECT_ROOT / "2026_KIISE" / "paper_assets"
    / "20260723_controlled_supplement" / "s3_cluster_mechanism"
)


def bootstrap_by_anchor(frame: pd.DataFrame, seed: int = 20260723, draws: int = 5000):
    anchors = sorted(frame["anchor"].unique())
    rng = np.random.default_rng(seed)
    rows = []
    for concentration, cell in frame.groupby("concentration"):
        by_anchor = cell.groupby("anchor")["recall_loss"].mean().reindex(anchors).to_numpy()
        sampled = by_anchor[rng.integers(0, len(by_anchor), size=(draws, len(by_anchor)))]
        means = sampled.mean(axis=1)
        rows.append(
            {
                "concentration": concentration,
                "mean": float(by_anchor.mean()),
                "lo": float(np.percentile(means, 2.5)),
                "hi": float(np.percentile(means, 97.5)),
            }
        )
    return pd.DataFrame(rows).sort_values("concentration")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    output = args.output or args.root / "s3_selectivity_preserving_controls.png"

    labels = [("A", "hnsw"), ("A", "ivf"), ("B", "hnsw"), ("B", "ivf")]
    colors = {"hnsw": "#2E74B5", "ivf": "#D9822B"}
    markers = {"A": "o", "B": "s"}
    fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.1), constrained_layout=True)

    ax = axes[0]
    rng = np.random.default_rng(20260723)
    for position, (corpus, method) in enumerate(labels):
        directory = args.root / f"corpus_{corpus}_{method}"
        negative = pd.read_csv(directory / "negative_control.csv")
        summary = json.loads((directory / "summary.json").read_text())[f"gates"][method][
            "negative_control"
        ]
        values = negative["natural_minus_shuffle"].to_numpy()
        jitter = rng.uniform(-0.11, 0.11, size=len(values))
        ax.scatter(
            position + jitter,
            values,
            s=16,
            alpha=0.52,
            color=colors[method],
            marker=markers[corpus],
            edgecolors="none",
        )
        mean = summary["mean_natural_minus_shuffle_loss"]
        lo, hi = summary["predicate_bootstrap_ci"]
        ax.errorbar(
            position,
            mean,
            yerr=[[mean - lo], [hi - mean]],
            fmt="_",
            markersize=18,
            linewidth=2.2,
            capsize=4,
            color="#20252B",
            zorder=5,
        )
    ax.axhline(0, color="#72777D", linewidth=1, linestyle="--")
    ax.set_xticks(range(4), ["A\nHNSW", "A\nIVF", "B\nHNSW", "B\nIVF"])
    ax.set_ylabel("Recall loss: natural mask − shuffled mask")
    ax.set_title("(a) Selectivity-preserving negative control", loc="left", fontweight="bold")
    ax.grid(axis="y", alpha=0.18)

    ax = axes[1]
    for corpus, method in labels:
        directory = args.root / f"corpus_{corpus}_{method}"
        aggregate = pd.read_csv(directory / "aggregate.csv")
        synthetic = aggregate[aggregate["mask_type"] == "synthetic"]
        curve = bootstrap_by_anchor(synthetic)
        label = f"Corpus {corpus} / {method.upper()}"
        linestyle = "-" if corpus == "A" else "--"
        ax.plot(
            curve["concentration"],
            curve["mean"],
            color=colors[method],
            linestyle=linestyle,
            marker=markers[corpus],
            linewidth=2,
            markersize=5,
            label=label,
        )
        ax.fill_between(
            curve["concentration"],
            curve["lo"],
            curve["hi"],
            color=colors[method],
            alpha=0.09,
        )
    ax.set_xlabel("Synthetic cluster concentration")
    ax.set_ylabel("Recall loss")
    ax.set_title("(b) Fixed-selectivity dose response", loc="left", fontweight="bold")
    ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylim(bottom=-0.02)
    ax.grid(alpha=0.18)
    ax.legend(frameon=False, fontsize=8, ncol=2, loc="upper left")

    fig.suptitle(
        "Filtered-ANN clustering mechanism controls (100 shuffles; 10 anchors)",
        fontsize=12,
        fontweight="bold",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=300, bbox_inches="tight")
    fig.savefig(output.with_suffix(".pdf"), bbox_inches="tight")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
