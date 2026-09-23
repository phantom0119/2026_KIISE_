"""VRU-Accident dataset adapter.

This adapter converts the Hugging Face VRU-Accident clone into a canonical
clip-document-metadata-query-qrels workload. It intentionally avoids model
dependencies so that dataset normalization remains independent from embedding
and vector database choices.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DATASET_ID = "vru_accident"
OPTION_PATTERN = re.compile(r"([A-D])\.\s*")


CATEGORY_TO_FACET = {
    "weather and light": "weather_light",
    "location": "location",
    "road type": "road_type",
    "accident type": "accident_type",
    "accident reason": "accident_reason",
    "prevention method": "prevention_method",
}


FACET_LABEL = {
    "weather_light": "weather and lighting",
    "location": "location",
    "road_type": "road type",
    "accident_type": "accident type",
    "accident_reason": "accident cause",
    "prevention_method": "prevention method",
}


@dataclass(frozen=True)
class CanonicalBuildResult:
    output_dir: Path
    clips: int
    documents: int
    metadata_rows: int
    queries: int
    qrels: int
    missing_media: int


class VRUAccidentAdapter:
    """Build canonical artifacts for VRU-Accident."""

    def __init__(
        self,
        dataset_root: Path,
        output_root: Path,
        dataset_version: str,
    ) -> None:
        self.dataset_root = dataset_root
        self.output_root = output_root
        self.dataset_version = dataset_version
        self.hf_root = dataset_root / "external" / "VRU-Accident_hf"
        self.video_root = dataset_root / "raw" / "VRU-Accident"

    @property
    def output_dir(self) -> Path:
        return self.output_root / DATASET_ID / self.dataset_version / "canonical"

    def validate_raw(self) -> dict[str, Any]:
        parquet_root = self.hf_root / "data"
        caption_files = sorted(parquet_root.glob("*_caption-*.parquet"))
        vqa_files = sorted(parquet_root.glob("*_vqa-*.parquet"))
        media_files = sorted((self.video_root / "VRU_videos").glob("*/*.mp4"))
        return {
            "dataset_id": DATASET_ID,
            "hf_root": str(self.hf_root),
            "video_root": str(self.video_root),
            "caption_parquet_files": len(caption_files),
            "vqa_parquet_files": len(vqa_files),
            "media_files": len(media_files),
            "valid": bool(caption_files and vqa_files and media_files),
        }

    def build(self, overwrite: bool = False) -> CanonicalBuildResult:
        validation = self.validate_raw()
        if not validation["valid"]:
            raise RuntimeError(f"VRU-Accident raw validation failed: {validation}")

        out = self.output_dir
        out.mkdir(parents=True, exist_ok=True)
        if any(out.iterdir()) and not overwrite:
            raise FileExistsError(f"{out} is not empty. Use overwrite=True.")

        captions = self._load_caption_rows()
        vqa = self._load_vqa_rows()

        clips = self._build_clips(captions, vqa)
        documents = self._build_documents(captions, vqa)
        metadata = self._build_metadata(vqa)
        queries, qrels = self._build_queries_and_qrels(metadata)

        clips.to_parquet(out / "clips.parquet", index=False)
        documents.to_parquet(out / "documents.parquet", index=False)
        metadata.to_parquet(out / "metadata.parquet", index=False)
        self._write_jsonl(out / "queries.jsonl", queries)
        qrels.to_csv(out / "qrels.tsv", sep="\t", index=False)

        missing_media = int((~clips["media_exists"]).sum())
        manifest = {
            "dataset_id": DATASET_ID,
            "dataset_version": self.dataset_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_hf_root": str(self.hf_root),
            "source_video_root": str(self.video_root),
            "output_dir": str(out),
            "counts": {
                "clips": int(len(clips)),
                "documents": int(len(documents)),
                "metadata_rows": int(len(metadata)),
                "queries": int(len(queries)),
                "qrels": int(len(qrels)),
                "missing_media": missing_media,
            },
            "raw_validation": validation,
            "schema_files": [
                "clips.parquet",
                "documents.parquet",
                "metadata.parquet",
                "queries.jsonl",
                "qrels.tsv",
            ],
            "query_generation": {
                "single_facet_min_support": 2,
                "pair_min_support": 2,
                "triple_min_support": 2,
                "max_queries_per_group": {
                    "weak": 120,
                    "medium": 220,
                    "strong": 220,
                },
            },
        }
        (out / "dataset_manifest.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        self._write_summary(out, manifest, metadata, queries, qrels)

        return CanonicalBuildResult(
            output_dir=out,
            clips=len(clips),
            documents=len(documents),
            metadata_rows=len(metadata),
            queries=len(queries),
            qrels=len(qrels),
            missing_media=missing_media,
        )

    def _load_caption_rows(self) -> pd.DataFrame:
        rows = []
        for path in sorted((self.hf_root / "data").glob("*_caption-*.parquet")):
            df = pd.read_parquet(path)
            for row in df.to_dict("records"):
                video = self._normalize_video(row["video_path"])
                rows.append(
                    {
                        **video,
                        "caption": row["caption"],
                        "source_file": path.name,
                    }
                )
        return pd.DataFrame(rows)

    def _load_vqa_rows(self) -> pd.DataFrame:
        rows = []
        for path in sorted((self.hf_root / "data").glob("*_vqa-*.parquet")):
            df = pd.read_parquet(path)
            for idx, row in enumerate(df.to_dict("records")):
                video = self._normalize_video(row["video_path"])
                options = self._parse_options(row["options"])
                answer = str(row["answer"]).strip().upper()[:1]
                facet_name = CATEGORY_TO_FACET.get(row["category"], self._slug(row["category"]))
                facet_value = options.get(answer)
                rows.append(
                    {
                        **video,
                        "vqa_row_id": f"{video['clip_id']}:vqa:{idx}:{facet_name}",
                        "category": row["category"],
                        "facet_name": facet_name,
                        "question": row["question"],
                        "options": row["options"],
                        "answer": answer,
                        "answer_text": facet_value,
                        "source_file": path.name,
                    }
                )
        return pd.DataFrame(rows)

    def _build_clips(self, captions: pd.DataFrame, vqa: pd.DataFrame) -> pd.DataFrame:
        base = pd.concat(
            [
                captions[["clip_id", "subset", "video_stem", "media_path"]],
                vqa[["clip_id", "subset", "video_stem", "media_path"]],
            ],
            ignore_index=True,
        ).drop_duplicates("clip_id")
        base = base.sort_values("clip_id").reset_index(drop=True)
        base.insert(1, "dataset_id", DATASET_ID)
        base["source_split"] = "all"
        base["media_type"] = "video"
        base["duration_sec"] = pd.NA
        base["media_exists"] = base["media_path"].map(lambda p: Path(p).exists())
        return base[
            [
                "clip_id",
                "dataset_id",
                "source_split",
                "subset",
                "video_stem",
                "media_type",
                "media_path",
                "duration_sec",
                "media_exists",
            ]
        ]

    def _build_documents(self, captions: pd.DataFrame, vqa: pd.DataFrame) -> pd.DataFrame:
        caption_docs = []
        for row in captions.to_dict("records"):
            caption_docs.append(
                {
                    "doc_id": f"{row['clip_id']}:doc:dense_caption",
                    "clip_id": row["clip_id"],
                    "dataset_id": DATASET_ID,
                    "doc_type": "dense_caption",
                    "text": row["caption"],
                    "lang": "en",
                    "source": row["source_file"],
                }
            )

        facet_docs = []
        for row in vqa.to_dict("records"):
            if not row.get("answer_text"):
                continue
            label = FACET_LABEL.get(row["facet_name"], row["facet_name"].replace("_", " "))
            facet_docs.append(
                {
                    "doc_id": f"{row['clip_id']}:doc:vqa_facet:{row['facet_name']}",
                    "clip_id": row["clip_id"],
                    "dataset_id": DATASET_ID,
                    "doc_type": "vqa_facet_statement",
                    "text": f"{label}: {row['answer_text']}",
                    "lang": "en",
                    "source": row["source_file"],
                }
            )

        return pd.DataFrame(caption_docs + facet_docs).drop_duplicates("doc_id")

    def _build_metadata(self, vqa: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for row in vqa.to_dict("records"):
            if not row.get("answer_text"):
                continue
            rows.append(
                {
                    "clip_id": row["clip_id"],
                    "dataset_id": DATASET_ID,
                    "facet_name": row["facet_name"],
                    "facet_value": row["answer_text"],
                    "facet_source": "parsed_vqa",
                    "confidence": 1.0,
                    "raw_category": row["category"],
                    "raw_answer": row["answer"],
                    "raw_options": row["options"],
                }
            )
        metadata = pd.DataFrame(rows).drop_duplicates(["clip_id", "facet_name"])
        return metadata.sort_values(["clip_id", "facet_name"]).reset_index(drop=True)

    def _build_queries_and_qrels(self, metadata: pd.DataFrame) -> tuple[list[dict[str, Any]], pd.DataFrame]:
        facet_table = (
            metadata.pivot_table(
                index="clip_id",
                columns="facet_name",
                values="facet_value",
                aggfunc="first",
            )
            .reset_index()
            .fillna("")
        )

        queries: list[dict[str, Any]] = []
        qrels_rows: list[dict[str, Any]] = []

        def add_query(
            query_text: str,
            qrel_filters: dict[str, str],
            metadata_filters: dict[str, str],
            difficulty: str,
            semantic_filter: dict[str, str],
        ) -> None:
            query_id = f"vru:{difficulty}:{len(queries) + 1:04d}"
            mask = pd.Series([True] * len(facet_table))
            for key, value in qrel_filters.items():
                if key not in facet_table.columns:
                    return
                mask &= facet_table[key].eq(value)
            targets = facet_table.loc[mask, "clip_id"].tolist()
            if not targets:
                return
            queries.append(
                {
                    "query_id": query_id,
                    "dataset_id": DATASET_ID,
                    "query_text": query_text,
                    "task": "text_metadata_retrieval",
                    "metadata_filter": metadata_filters,
                    "semantic_filter": semantic_filter,
                    "qrel_filter": qrel_filters,
                    "difficulty": difficulty,
                    "positive_count": len(targets),
                }
            )
            for clip_id in targets:
                qrels_rows.append(
                    {
                        "query_id": query_id,
                        "target_id": clip_id,
                        "target_type": "clip",
                        "relevance": 3,
                    }
                )

        self._add_weak_queries(facet_table, add_query)
        self._add_medium_queries(facet_table, add_query)
        self._add_strong_queries(facet_table, add_query)

        qrels = pd.DataFrame(qrels_rows)
        return queries, qrels

    def _add_weak_queries(self, table: pd.DataFrame, add_query) -> None:
        query_specs = [
            ("accident_type", "Find videos where the accident type is {value}.", 40),
            ("accident_reason", "Find accidents caused by: {value}.", 20),
        ]
        for facet, template, limit in query_specs:
            if facet not in table.columns:
                continue
            values = table[facet].value_counts()
            for value, support in values.head(limit).items():
                if value and support >= 2:
                    add_query(
                        template.format(value=value),
                        {facet: value},
                        {},
                        "weak",
                        {facet: value},
                    )

    def _add_medium_queries(self, table: pd.DataFrame, add_query) -> None:
        pair_specs = [
            (
                ["accident_type", "road_type"],
                "Find videos where the accident type is {accident_type} on a {road_type} road.",
                ["road_type"],
            ),
            (
                ["accident_type", "location"],
                "Find {location} videos where the accident type is {accident_type}.",
                ["location"],
            ),
            (
                ["accident_type", "weather_light"],
                "Find videos recorded in {weather_light} where the accident type is {accident_type}.",
                ["weather_light"],
            ),
        ]
        added = 0
        for facets, template, metadata_facets in pair_specs:
            if any(f not in table.columns for f in facets):
                continue
            grouped = (
                table.groupby(facets)
                .size()
                .reset_index(name="support")
                .sort_values(["support", *facets], ascending=[False, True, True])
            )
            for row in grouped.to_dict("records"):
                if added >= 220:
                    return
                if row["support"] < 2 or any(not row[f] for f in facets):
                    continue
                qrel_filters = {f: row[f] for f in facets}
                metadata_filters = {f: row[f] for f in metadata_facets}
                semantic_filters = {f: row[f] for f in facets if f not in metadata_facets}
                add_query(template.format(**qrel_filters), qrel_filters, metadata_filters, "medium", semantic_filters)
                added += 1

    def _add_strong_queries(self, table: pd.DataFrame, add_query) -> None:
        facets = ["accident_type", "road_type", "location", "weather_light"]
        if any(f not in table.columns for f in facets):
            return
        grouped = (
            table.groupby(facets)
            .size()
            .reset_index(name="support")
            .sort_values(["support", *facets], ascending=[False, True, True, True, True])
        )
        added = 0
        for row in grouped.to_dict("records"):
            if added >= 220:
                return
            if row["support"] < 2 or any(not row[f] for f in facets):
                continue
            qrel_filters = {f: row[f] for f in facets}
            metadata_filters = {f: row[f] for f in ["road_type", "location", "weather_light"]}
            semantic_filters = {"accident_type": row["accident_type"]}
            add_query(
                (
                    "Find {weather_light} {location} accident videos on {road_type} "
                    "roads where the accident type is {accident_type}."
                ).format(**qrel_filters),
                qrel_filters,
                metadata_filters,
                "strong",
                semantic_filters,
            )
            added += 1

    def _normalize_video(self, raw_path: str) -> dict[str, str]:
        rel = str(raw_path).strip()
        if rel.startswith("./"):
            rel = rel[2:]
        path = Path(rel)
        if path.suffix == "":
            path = path.with_suffix(".mp4")
        parts = path.parts
        if len(parts) < 3 or parts[0] != "VRU_videos":
            raise ValueError(f"Unexpected VRU video path: {raw_path}")
        subset = parts[1]
        video_stem = Path(parts[2]).stem
        clip_id = f"{DATASET_ID}:{subset}:{video_stem}"
        media_path = self.video_root / path
        return {
            "clip_id": clip_id,
            "subset": subset,
            "video_stem": video_stem,
            "media_path": str(media_path),
        }

    @staticmethod
    def _parse_options(raw_options: str) -> dict[str, str]:
        text = str(raw_options)
        matches = list(OPTION_PATTERN.finditer(text))
        options: dict[str, str] = {}
        for idx, match in enumerate(matches):
            label = match.group(1)
            start = match.end()
            end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
            value = text[start:end].strip().strip(",").strip()
            options[label] = value
        return options

    @staticmethod
    def _slug(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")

    @staticmethod
    def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    @staticmethod
    def _write_summary(
        out: Path,
        manifest: dict[str, Any],
        metadata: pd.DataFrame,
        queries: list[dict[str, Any]],
        qrels: pd.DataFrame,
    ) -> None:
        query_df = pd.DataFrame(queries)
        lines = [
            "# VRU-Accident Canonical Dataset Summary",
            "",
            f"dataset_id: `{manifest['dataset_id']}`",
            f"dataset_version: `{manifest['dataset_version']}`",
            f"created_at: `{manifest['created_at']}`",
            "",
            "## Counts",
            "",
            "| artifact | count |",
            "|---|---:|",
        ]
        for key, value in manifest["counts"].items():
            lines.append(f"| {key} | {value} |")
        lines.extend(["", "## Metadata Facets", "", "| facet | distinct values | rows |", "|---|---:|---:|"])
        for facet, group in metadata.groupby("facet_name"):
            lines.append(f"| {facet} | {group['facet_value'].nunique()} | {len(group)} |")
        lines.extend(["", "## Queries", "", "| difficulty | queries | qrels | avg positives |", "|---|---:|---:|---:|"])
        if not query_df.empty:
            qrels_by_query = qrels.groupby("query_id").size()
            for difficulty, group in query_df.groupby("difficulty"):
                qrels_count = int(qrels_by_query.loc[group["query_id"]].sum())
                avg_pos = float(group["positive_count"].mean())
                lines.append(f"| {difficulty} | {len(group)} | {qrels_count} | {avg_pos:.2f} |")
        lines.append("")
        (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
