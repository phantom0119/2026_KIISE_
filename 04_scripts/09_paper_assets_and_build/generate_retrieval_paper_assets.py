#!/usr/bin/env python3
"""Generate paper-ready tables and figures from retrieval baseline results."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402


PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROCESSED_ROOT = PROJECT_ROOT / "Datasets" / "processed" / "vru_accident" / "20260706"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "2026_KIISE" / "paper_assets" / "20260706"

STRATEGY_ORDER = [
    "B0_metadata_only",
    "B1_bm25_only",
    "B2_vector_only",
    "B3_vector_postfilter",
    "B4_prefilter_vector",
    "B5_hybrid",
]

STRATEGY_LABELS = {
    "B0_metadata_only": "B0 Metadata",
    "B1_bm25_only": "B1 BM25",
    "B2_vector_only": "B2 Vector",
    "B3_vector_postfilter": "B3 Postfilter",
    "B4_prefilter_vector": "B4 Prefilter",
    "B5_hybrid": "B5 Hybrid",
}

MODEL_LABELS = {
    "bge-m3": "bge-m3",
    "e5-large-v2": "e5-large-v2",
}

DIFFICULTY_ORDER = ["weak", "medium", "strong", "all"]


@dataclass(frozen=True)
class ResultInput:
    model_id: str
    result_root: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--bge-result-root",
        type=Path,
        default=DEFAULT_PROCESSED_ROOT / "results" / "vru_bgem3_faiss_b0_b5",
    )
    parser.add_argument(
        "--e5-result-root",
        type=Path,
        default=DEFAULT_PROCESSED_ROOT / "results" / "vru_e5_faiss_b0_b5",
    )
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    return parser.parse_args()


def load_result(input_: ResultInput) -> tuple[pd.DataFrame, pd.DataFrame]:
    metrics_path = input_.result_root / "metrics_summary.csv"
    latency_path = input_.result_root / "latency_summary.csv"
    if not metrics_path.exists():
        raise FileNotFoundError(metrics_path)
    if not latency_path.exists():
        raise FileNotFoundError(latency_path)

    metrics = pd.read_csv(metrics_path)
    latency = pd.read_csv(latency_path)
    for df in [metrics, latency]:
        df.insert(0, "model_id", input_.model_id)
        df.insert(1, "model_label", MODEL_LABELS.get(input_.model_id, input_.model_id))
        df["strategy_label"] = df["strategy"].map(STRATEGY_LABELS).fillna(df["strategy"])
        df["strategy_order"] = df["strategy"].map({s: i for i, s in enumerate(STRATEGY_ORDER)})
    return metrics, latency


def ensure_dirs(output_root: Path) -> tuple[Path, Path]:
    tables_dir = output_root / "tables"
    figures_dir = output_root / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    return tables_dir, figures_dir


def fmt_value(value: object) -> str:
    if isinstance(value, (float, np.floating)):
        return f"{value:.4f}"
    if isinstance(value, (int, np.integer)):
        return str(value)
    return str(value)


def write_markdown_table(path: Path, df: pd.DataFrame, columns: list[str], headers: list[str]) -> None:
    rows = [[fmt_value(row[col]) for col in columns] for _, row in df.iterrows()]
    widths = [
        max(len(headers[idx]), *(len(row[idx]) for row in rows)) if rows else len(headers[idx])
        for idx in range(len(headers))
    ]
    lines = []
    lines.append("| " + " | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))) + " |")
    lines.append("| " + " | ".join("-" * widths[i] for i in range(len(headers))) + " |")
    for row in rows:
        lines.append("| " + " | ".join(row[i].ljust(widths[i]) for i in range(len(headers))) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_latex_table(path: Path, df: pd.DataFrame, columns: list[str], headers: list[str]) -> None:
    latex_df = df[columns].copy()
    latex_df.columns = headers
    for col in latex_df.columns:
        if pd.api.types.is_float_dtype(latex_df[col]):
            latex_df[col] = latex_df[col].map(lambda value: f"{value:.4f}")
    path.write_text(latex_df.to_latex(index=False, escape=True), encoding="utf-8")


def build_tables(metrics: pd.DataFrame, latency: pd.DataFrame, tables_dir: Path) -> dict[str, str]:
    outputs: dict[str, str] = {}
    overall = (
        metrics[metrics["difficulty"].eq("all")]
        .merge(
            latency[
                [
                    "model_id",
                    "strategy",
                    "latency_mean_ms",
                    "latency_p50_ms",
                    "latency_p95_ms",
                ]
            ],
            on=["model_id", "strategy"],
            how="left",
        )
        .sort_values(["model_id", "strategy_order"])
        .reset_index(drop=True)
    )
    overall_out = overall[
        [
            "model_id",
            "strategy_label",
            "recall_at_10",
            "recall_at_20",
            "mrr",
            "ndcg_at_10",
            "latency_mean_ms",
            "latency_p95_ms",
        ]
    ]
    overall_csv = tables_dir / "table_overall_retrieval_metrics.csv"
    overall_md = tables_dir / "table_overall_retrieval_metrics.md"
    overall_tex = tables_dir / "table_overall_retrieval_metrics.tex"
    overall_out.to_csv(overall_csv, index=False)
    write_markdown_table(
        overall_md,
        overall_out,
        list(overall_out.columns),
        ["Model", "Strategy", "R@10", "R@20", "MRR", "nDCG@10", "Mean ms", "P95 ms"],
    )
    write_latex_table(
        overall_tex,
        overall_out,
        list(overall_out.columns),
        ["Model", "Strategy", "R@10", "R@20", "MRR", "nDCG@10", "Mean ms", "P95 ms"],
    )
    outputs["overall_csv"] = str(overall_csv)
    outputs["overall_md"] = str(overall_md)
    outputs["overall_tex"] = str(overall_tex)

    by_difficulty = (
        metrics[metrics["difficulty"].isin(["weak", "medium", "strong"])]
        .sort_values(["model_id", "difficulty", "strategy_order"])
        .reset_index(drop=True)
    )
    difficulty_out = by_difficulty[
        [
            "model_id",
            "difficulty",
            "strategy_label",
            "queries",
            "recall_at_10",
            "recall_at_20",
            "mrr",
            "ndcg_at_10",
        ]
    ]
    difficulty_csv = tables_dir / "table_difficulty_retrieval_metrics.csv"
    difficulty_md = tables_dir / "table_difficulty_retrieval_metrics.md"
    difficulty_tex = tables_dir / "table_difficulty_retrieval_metrics.tex"
    difficulty_out.to_csv(difficulty_csv, index=False)
    write_markdown_table(
        difficulty_md,
        difficulty_out,
        list(difficulty_out.columns),
        ["Model", "Difficulty", "Strategy", "Queries", "R@10", "R@20", "MRR", "nDCG@10"],
    )
    write_latex_table(
        difficulty_tex,
        difficulty_out,
        list(difficulty_out.columns),
        ["Model", "Difficulty", "Strategy", "Queries", "R@10", "R@20", "MRR", "nDCG@10"],
    )
    outputs["difficulty_csv"] = str(difficulty_csv)
    outputs["difficulty_md"] = str(difficulty_md)
    outputs["difficulty_tex"] = str(difficulty_tex)

    latency_out = (
        latency.sort_values(["model_id", "strategy_order"])
        [
            [
                "model_id",
                "strategy_label",
                "queries",
                "latency_mean_ms",
                "latency_p50_ms",
                "latency_p95_ms",
            ]
        ]
        .reset_index(drop=True)
    )
    latency_csv = tables_dir / "table_latency_summary.csv"
    latency_md = tables_dir / "table_latency_summary.md"
    latency_tex = tables_dir / "table_latency_summary.tex"
    latency_out.to_csv(latency_csv, index=False)
    write_markdown_table(
        latency_md,
        latency_out,
        list(latency_out.columns),
        ["Model", "Strategy", "Queries", "Mean ms", "P50 ms", "P95 ms"],
    )
    write_latex_table(
        latency_tex,
        latency_out,
        list(latency_out.columns),
        ["Model", "Strategy", "Queries", "Mean ms", "P50 ms", "P95 ms"],
    )
    outputs["latency_csv"] = str(latency_csv)
    outputs["latency_md"] = str(latency_md)
    outputs["latency_tex"] = str(latency_tex)
    return outputs


def save_figure(fig: plt.Figure, path_without_suffix: Path) -> dict[str, str]:
    png = path_without_suffix.with_suffix(".png")
    pdf = path_without_suffix.with_suffix(".pdf")
    fig.savefig(png, dpi=220, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    return {"png": str(png), "pdf": str(pdf)}


def plot_overall_quality(metrics: pd.DataFrame, figures_dir: Path) -> dict[str, str]:
    overall = metrics[metrics["difficulty"].eq("all")].copy()
    overall = overall.sort_values(["model_id", "strategy_order"])
    strategies = [STRATEGY_LABELS[s] for s in STRATEGY_ORDER]
    x = np.arange(len(strategies))
    width = 0.36

    fig, axes = plt.subplots(1, 2, figsize=(12.5, 4.2), sharex=True)
    for axis, metric, ylabel in [
        (axes[0], "recall_at_10", "Recall@10"),
        (axes[1], "ndcg_at_10", "nDCG@10"),
    ]:
        for idx, model_id in enumerate(sorted(overall["model_id"].unique())):
            subset = overall[overall["model_id"].eq(model_id)].set_index("strategy")
            values = [subset.loc[strategy, metric] for strategy in STRATEGY_ORDER]
            offset = (idx - 0.5) * width
            axis.bar(x + offset, values, width=width, label=MODEL_LABELS.get(model_id, model_id))
        axis.set_ylabel(ylabel)
        axis.set_ylim(0, 1.05)
        axis.grid(axis="y", alpha=0.25)
        axis.set_xticks(x)
        axis.set_xticklabels(strategies, rotation=28, ha="right")
    axes[0].legend(frameon=False, loc="upper left")
    fig.suptitle("Overall Retrieval Quality by Strategy")
    fig.tight_layout()
    return save_figure(fig, figures_dir / "fig_overall_quality_by_strategy")


def plot_latency(latency: pd.DataFrame, figures_dir: Path) -> dict[str, str]:
    latency = latency.sort_values(["model_id", "strategy_order"])
    strategies = [STRATEGY_LABELS[s] for s in STRATEGY_ORDER]
    x = np.arange(len(strategies))
    width = 0.36

    fig, axis = plt.subplots(figsize=(8.2, 4.2))
    for idx, model_id in enumerate(sorted(latency["model_id"].unique())):
        subset = latency[latency["model_id"].eq(model_id)].set_index("strategy")
        values = [subset.loc[strategy, "latency_mean_ms"] for strategy in STRATEGY_ORDER]
        offset = (idx - 0.5) * width
        axis.bar(x + offset, values, width=width, label=MODEL_LABELS.get(model_id, model_id))
    axis.set_yscale("log")
    axis.set_ylabel("Mean latency (ms, log scale)")
    axis.set_xticks(x)
    axis.set_xticklabels(strategies, rotation=28, ha="right")
    axis.grid(axis="y", alpha=0.25)
    axis.legend(frameon=False, loc="upper left")
    axis.set_title("Retrieval Latency by Strategy")
    fig.tight_layout()
    return save_figure(fig, figures_dir / "fig_latency_by_strategy")


def plot_difficulty_heatmap(metrics: pd.DataFrame, figures_dir: Path) -> dict[str, str]:
    difficulties = ["weak", "medium", "strong"]
    fig, axes = plt.subplots(1, 2, figsize=(12.8, 4.6), sharey=True, constrained_layout=True)
    model_ids = sorted(metrics["model_id"].unique())
    for axis, model_id in zip(axes, model_ids):
        subset = metrics[
            metrics["model_id"].eq(model_id) & metrics["difficulty"].isin(difficulties)
        ].copy()
        pivot = subset.pivot(index="strategy", columns="difficulty", values="ndcg_at_10")
        matrix = np.array([[pivot.loc[strategy, diff] for diff in difficulties] for strategy in STRATEGY_ORDER])
        image = axis.imshow(matrix, vmin=0, vmax=1, cmap="viridis")
        axis.set_title(MODEL_LABELS.get(model_id, model_id))
        axis.set_xticks(np.arange(len(difficulties)))
        axis.set_xticklabels(difficulties)
        axis.set_yticks(np.arange(len(STRATEGY_ORDER)))
        axis.set_yticklabels([STRATEGY_LABELS[s] for s in STRATEGY_ORDER])
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                axis.text(j, i, f"{matrix[i, j]:.2f}", ha="center", va="center", color="white")
    fig.colorbar(image, ax=axes.ravel().tolist(), shrink=0.82, label="nDCG@10")
    fig.suptitle("nDCG@10 by Query Difficulty")
    return save_figure(fig, figures_dir / "fig_difficulty_ndcg_heatmap")


def plot_recall_latency_tradeoff(metrics: pd.DataFrame, latency: pd.DataFrame, figures_dir: Path) -> dict[str, str]:
    overall = metrics[metrics["difficulty"].eq("all")].merge(
        latency[["model_id", "strategy", "latency_mean_ms"]],
        on=["model_id", "strategy"],
        how="left",
    )
    fig, axis = plt.subplots(figsize=(7.4, 4.8))
    markers = {"bge-m3": "o", "e5-large-v2": "s"}
    for model_id, group in overall.groupby("model_id"):
        axis.scatter(
            group["latency_mean_ms"],
            group["recall_at_10"],
            s=70,
            marker=markers.get(model_id, "o"),
            label=MODEL_LABELS.get(model_id, model_id),
        )
        for _, row in group.iterrows():
            axis.annotate(
                row["strategy_label"].split()[0],
                (row["latency_mean_ms"], row["recall_at_10"]),
                textcoords="offset points",
                xytext=(4, 5),
                fontsize=8,
            )
    axis.set_xscale("log")
    axis.set_xlabel("Mean latency (ms, log scale)")
    axis.set_ylabel("Recall@10")
    axis.set_ylim(0, 0.85)
    axis.grid(alpha=0.25)
    axis.legend(frameon=False, loc="lower right")
    axis.set_title("Recall-Latency Trade-off")
    fig.tight_layout()
    return save_figure(fig, figures_dir / "fig_recall_latency_tradeoff")


def write_summary(
    output_root: Path,
    metrics: pd.DataFrame,
    latency: pd.DataFrame,
    table_outputs: dict[str, str],
    figure_outputs: dict[str, dict[str, str]],
) -> None:
    overall = metrics[metrics["difficulty"].eq("all")].merge(
        latency[["model_id", "strategy", "latency_mean_ms"]],
        on=["model_id", "strategy"],
        how="left",
    )
    best_rows = []
    for model_id, group in overall.groupby("model_id"):
        best = group.sort_values(["ndcg_at_10", "recall_at_10"], ascending=False).iloc[0]
        best_rows.append(best)

    lines = [
        "# Retrieval Paper Assets",
        "",
        f"created_at: `{datetime.now(timezone.utc).isoformat()}`",
        "",
        "## Best Overall Strategies",
        "",
        "| model | best strategy | recall@10 | nDCG@10 | mean latency ms |",
        "|---|---|---:|---:|---:|",
    ]
    for row in best_rows:
        lines.append(
            "| {model} | {strategy} | {r10:.4f} | {ndcg:.4f} | {lat:.3f} |".format(
                model=row["model_id"],
                strategy=row["strategy_label"],
                r10=row["recall_at_10"],
                ndcg=row["ndcg_at_10"],
                lat=row["latency_mean_ms"],
            )
        )
    lines.extend(
        [
            "",
            "## Tables",
            "",
        ]
    )
    for name, path in table_outputs.items():
        rel = Path(path).relative_to(output_root)
        lines.append(f"- `{name}`: `{rel}`")

    lines.extend(["", "## Figures", ""])
    for name, paths in figure_outputs.items():
        png_rel = Path(paths["png"]).relative_to(output_root)
        pdf_rel = Path(paths["pdf"]).relative_to(output_root)
        lines.append(f"- `{name}`: `{png_rel}`, `{pdf_rel}`")

    lines.extend(
        [
            "",
            "## Paper Interpretation",
            "",
            "- Metadata-aware strategies B3/B4/B5 consistently outperform BM25-only and vector-only baselines.",
            "- bge-m3 favors B4 metadata prefilter + vector search in nDCG@10.",
            "- e5-large-v2 favors B5 hybrid retrieval, showing that the modular protocol can expose model-dependent backend choices.",
            "- The recall-latency trade-off figure should be used to frame the contribution as a database query planning problem, not only an embedding benchmark.",
        ]
    )
    (output_root / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    result_inputs = [
        ResultInput("bge-m3", args.bge_result_root),
        ResultInput("e5-large-v2", args.e5_result_root),
    ]

    metrics_parts = []
    latency_parts = []
    for input_ in result_inputs:
        metrics, latency = load_result(input_)
        metrics_parts.append(metrics)
        latency_parts.append(latency)

    metrics_all = pd.concat(metrics_parts, ignore_index=True)
    latency_all = pd.concat(latency_parts, ignore_index=True)

    output_root = args.output_root
    tables_dir, figures_dir = ensure_dirs(output_root)
    table_outputs = build_tables(metrics_all, latency_all, tables_dir)
    figure_outputs = {
        "overall_quality": plot_overall_quality(metrics_all, figures_dir),
        "latency": plot_latency(latency_all, figures_dir),
        "difficulty_ndcg": plot_difficulty_heatmap(metrics_all, figures_dir),
        "recall_latency_tradeoff": plot_recall_latency_tradeoff(metrics_all, latency_all, figures_dir),
    }
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_root": str(output_root),
        "inputs": [{"model_id": item.model_id, "result_root": str(item.result_root)} for item in result_inputs],
        "tables": table_outputs,
        "figures": figure_outputs,
    }
    (output_root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_summary(output_root, metrics_all, latency_all, table_outputs, figure_outputs)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
