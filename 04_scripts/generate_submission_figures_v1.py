#!/usr/bin/env python3
"""Generate submission-oriented figures for the v1 DBR manuscript."""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from PIL import Image
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260707_submission_figures"


def save_figure(fig: plt.Figure, name: str) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_DIR / f"{name}.png", dpi=220, bbox_inches="tight")
    fig.savefig(OUTPUT_DIR / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)


def draw_box(ax: plt.Axes, xy: tuple[float, float], text: str, width: float = 2.0, height: float = 0.55) -> None:
    x, y = xy
    patch = FancyBboxPatch(
        (x, y),
        width,
        height,
        boxstyle="round,pad=0.025,rounding_size=0.04",
        linewidth=1.2,
        edgecolor="#243447",
        facecolor="#f4f7fb",
    )
    ax.add_patch(patch)
    ax.text(x + width / 2, y + height / 2, text, ha="center", va="center", fontsize=8.6)


def draw_arrow(ax: plt.Axes, start: tuple[float, float], end: tuple[float, float]) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=12,
            linewidth=1.1,
            color="#34495e",
        )
    )


def pipeline_figure() -> None:
    fig, ax = plt.subplots(figsize=(11.8, 5.2))
    ax.axis("off")
    ax.set_xlim(0, 12.2)
    ax.set_ylim(0, 5.2)

    boxes = {
        "raw": (0.35, 3.8, "Raw MP4\n+ labels", 1.55),
        "canonical": (2.15, 3.8, "Canonical schema\nclip/doc/meta/query/qrels", 2.35),
        "frames": (4.95, 4.35, "Keyframes\nframe/time/thumb", 2.0),
        "visual": (7.25, 4.35, "CLIP visual-text\nframe/query vectors", 2.2),
        "text": (4.95, 3.2, "Text evidence\nBGE/E5 + BM25", 2.0),
        "meta": (4.95, 2.05, "Structured metadata\nfacet filters", 2.0),
        "retrieval": (7.25, 2.85, "Retrieval strategies\nM2/M4/M5/M6/IM1", 2.2),
        "rerank": (9.85, 2.85, "Evidence selection\nweighted RRF", 2.0),
        "packet": (9.85, 1.55, "Service packet\nframe/text/meta context", 2.0),
    }
    for key, (x, y, text, width) in boxes.items():
        draw_box(ax, (x, y), text, width=width)

    draw_arrow(ax, (1.9, 4.075), (2.15, 4.075))
    draw_arrow(ax, (4.5, 4.075), (4.95, 4.58))
    draw_arrow(ax, (4.5, 4.075), (4.95, 3.48))
    draw_arrow(ax, (4.5, 4.075), (4.95, 2.33))
    draw_arrow(ax, (6.95, 4.58), (7.25, 4.58))
    draw_arrow(ax, (6.95, 3.48), (7.25, 3.15))
    draw_arrow(ax, (6.95, 2.33), (7.25, 3.02))
    draw_arrow(ax, (9.45, 3.12), (9.85, 3.12))
    draw_arrow(ax, (10.85, 2.85), (10.85, 2.1))

    ax.text(
        0.4,
        0.55,
        "Controlled scope: no LLM/VLM generation in core evaluation; evidence-only retrieval and selection are evaluated.",
        fontsize=9,
        color="#2c3e50",
    )
    ax.set_title("Multimodal Evidence Retrieval and Selection Pipeline", fontsize=13, pad=12)
    save_figure(fig, "fig1_pipeline_v1")


def sensitivity_figure() -> None:
    data = pd.DataFrame(
        [
            ("VRU", 0, 0.9020),
            ("VRU", 1, 0.9810),
            ("VRU", 2, 0.9800),
            ("VRU", 3, 0.9680),
            ("AI Hub CCTV", 0, 0.9963),
            ("AI Hub CCTV", 1, 0.9963),
            ("AI Hub CCTV", 2, 1.0000),
            ("AI Hub CCTV", 3, 0.8327),
        ],
        columns=["dataset", "query_frame_seq", "recall_at_10"],
    )
    fig, ax = plt.subplots(figsize=(7.8, 4.4))
    width = 0.36
    xs = [0, 1, 2, 3]
    colors = {"VRU": "#2f6f9f", "AI Hub CCTV": "#b45f3c"}
    for offset, dataset in [(-width / 2, "VRU"), (width / 2, "AI Hub CCTV")]:
        sub = data[data["dataset"].eq(dataset)].sort_values("query_frame_seq")
        ax.bar([x + offset for x in xs], sub["recall_at_10"], width=width, label=dataset, color=colors[dataset])
        for x, y in zip([x + offset for x in xs], sub["recall_at_10"], strict=False):
            ax.text(x, y + 0.015, f"{y:.3f}", ha="center", va="bottom", fontsize=8)
    ax.set_ylim(0.75, 1.04)
    ax.set_xticks(xs)
    ax.set_xlabel("Image query frame sequence")
    ax.set_ylabel("Recall@10")
    ax.set_title("Image-to-Video Frame Position Sensitivity")
    ax.grid(axis="y", linestyle="--", alpha=0.35)
    ax.legend(loc="lower left")
    save_figure(fig, "fig2_image_query_sensitivity_v1")


def load_service_example(dataset_root: Path) -> pd.DataFrame:
    path = dataset_root / "service_testbed" / "rw_t4_v1_im1_top5" / "service_evidence_rows.parquet"
    df = pd.read_parquet(path)
    text_rows = df[df["query_type"].eq("text_metadata") & df["is_relevant"].eq(True)].copy()
    visual_rows = text_rows[text_rows["frame_source"].eq("retrieved_visual_frame")]
    if not visual_rows.empty:
        request_id = visual_rows.iloc[0]["request_id"]
    else:
        request_id = text_rows.iloc[0]["request_id"]
    return df[df["request_id"].eq(request_id)].sort_values("rank").head(3).reset_index(drop=True)


def evidence_packet_figure() -> None:
    examples = {
        "AI Hub CCTV": load_service_example(
            PROJECT_ROOT / "Datasets" / "processed" / "aihub_intelligent_cctv" / "20260706"
        ),
        "VRU": load_service_example(PROJECT_ROOT / "Datasets" / "processed" / "vru_accident" / "20260706"),
    }

    fig, axes = plt.subplots(2, 3, figsize=(10.5, 6.2))
    for row_idx, (dataset, rows) in enumerate(examples.items()):
        for col_idx, row in rows.iterrows():
            ax = axes[row_idx, col_idx]
            image_path = PROJECT_ROOT / str(row["thumbnail_path"])
            if not image_path.exists():
                image_path = Path(str(row["thumbnail_path"]))
            image = Image.open(image_path).convert("RGB")
            ax.imshow(image)
            ax.axis("off")
            title = f"{dataset} rank {int(row['rank'])}"
            ax.set_title(title, fontsize=9)
            clip = str(row["clip_id"]).split(":")[-1]
            text = f"clip={clip}\ntime={float(row['timestamp_sec']):.2f}s\nrelevant={bool(row['is_relevant'])}"
            ax.text(
                0.02,
                0.02,
                text,
                transform=ax.transAxes,
                fontsize=8,
                va="bottom",
                ha="left",
                color="white",
                bbox={"facecolor": "black", "alpha": 0.62, "pad": 3, "edgecolor": "none"},
            )
    fig.suptitle("Service-Level Evidence Packet Examples", fontsize=13)
    save_figure(fig, "fig3_service_evidence_examples_v1")


def write_caption_md() -> None:
    lines = [
        "# Submission Figure Assets v1",
        "",
        "| Figure | PNG | PDF | Manuscript role | Caption draft |",
        "|---|---|---|---|---|",
        "| Fig. 1 | `fig1_pipeline_v1.png` | `fig1_pipeline_v1.pdf` | Method overview | Overall pipeline from raw mp4 and labels to canonical schema, keyframes, CLIP/BGE/E5 embeddings, retrieval strategies, weighted evidence selection, and service-level evidence packets. |",
        "| Fig. 2 | `fig2_image_query_sensitivity_v1.png` | `fig2_image_query_sensitivity_v1.pdf` | Control analysis | Image-to-video Recall@10 under query frame positions 0, 1, 2, and 3. The main IM1 result uses query_frame_seq=2, while sensitivity shows frame-position dependence. |",
        "| Fig. 3 | `fig3_service_evidence_examples_v1.png` | `fig3_service_evidence_examples_v1.pdf` | Qualitative evidence | Example service evidence packets showing retrieved frame thumbnails, timestamps, clip identifiers, and relevance labels. |",
        "",
        "Use PNG for Word/HWP insertion and keep PDF as archival/vector-quality reference.",
    ]
    (OUTPUT_DIR / "figure_index.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.unicode_minus": False})
    pipeline_figure()
    sensitivity_figure()
    evidence_packet_figure()
    write_caption_md()
    print(f"output_dir={OUTPUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
