"""AI Hub intelligent CCTV dataset adapter."""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DATASET_ID = "aihub_intelligent_cctv"

EVENT_CLASS_TEXT = {
    "Crowd": "crowd density",
    "Falldown": "fall-down",
    "Fight": "fight",
    "Flood": "flood",
    "Gathering": "gathering",
    "Invasion": "intrusion",
}

EVENT_CLASS_KO = {
    "Crowd": "인파밀집",
    "Falldown": "쓰러짐",
    "Fight": "싸움",
    "Flood": "침수",
    "Gathering": "군집",
    "Invasion": "침입",
}

PLACE_TEXT = {
    "alley": "alley",
    "intersection": "intersection",
    "road": "main road",
    "other": "other place",
}

FLOOD_LEVEL_TEXT = {
    "0": "flood level 0",
    "1": "flood level 1",
    "2": "flood level 2",
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
    missing_labels: int


class AIHubIntelligentCCTVAdapter:
    """Build canonical artifacts for AI Hub intelligent CCTV clips."""

    def __init__(
        self,
        dataset_root: Path,
        output_root: Path,
        dataset_version: str,
    ) -> None:
        self.dataset_root = dataset_root
        self.output_root = output_root
        self.dataset_version = dataset_version
        self.raw_root = dataset_root / "raw" / DATASET_ID / dataset_version
        self.pair_manifest = self.raw_root / "clip_pairs.csv"

    @property
    def output_dir(self) -> Path:
        return self.output_root / DATASET_ID / self.dataset_version / "canonical"

    def validate_raw(self) -> dict[str, Any]:
        media_files = sorted((self.raw_root / "media").rglob("*.mp4"))
        label_files = sorted((self.raw_root / "labels").rglob("*.json"))
        pair_rows = self._read_pair_rows() if self.pair_manifest.exists() else []
        missing_media = sum(1 for row in pair_rows if not Path(row["media_path"]).exists())
        missing_labels = sum(1 for row in pair_rows if not Path(row["label_path"]).exists())
        return {
            "dataset_id": DATASET_ID,
            "raw_root": str(self.raw_root),
            "pair_manifest": str(self.pair_manifest),
            "media_files": len(media_files),
            "label_files": len(label_files),
            "paired_clips": len(pair_rows),
            "missing_media": missing_media,
            "missing_labels": missing_labels,
            "valid": bool(pair_rows and media_files and label_files and missing_media == 0 and missing_labels == 0),
        }

    def build(self, overwrite: bool = False) -> CanonicalBuildResult:
        validation = self.validate_raw()
        if not validation["valid"]:
            raise RuntimeError(f"AI Hub intelligent CCTV raw validation failed: {validation}")

        out = self.output_dir
        out.mkdir(parents=True, exist_ok=True)
        if any(out.iterdir()) and not overwrite:
            raise FileExistsError(f"{out} is not empty. Use overwrite=True.")

        records = self._load_records()
        clips = self._build_clips(records)
        documents = self._build_documents(records)
        metadata = self._build_metadata(records)
        queries, qrels = self._build_queries_and_qrels(metadata)

        clips.to_parquet(out / "clips.parquet", index=False)
        documents.to_parquet(out / "documents.parquet", index=False)
        metadata.to_parquet(out / "metadata.parquet", index=False)
        self._write_jsonl(out / "queries.jsonl", queries)
        qrels.to_csv(out / "qrels.tsv", sep="\t", index=False)

        manifest = {
            "dataset_id": DATASET_ID,
            "dataset_version": self.dataset_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_raw_root": str(self.raw_root),
            "pair_manifest": str(self.pair_manifest),
            "output_dir": str(out),
            "counts": {
                "clips": int(len(clips)),
                "documents": int(len(documents)),
                "metadata_rows": int(len(metadata)),
                "queries": int(len(queries)),
                "qrels": int(len(qrels)),
                "missing_media": int(validation["missing_media"]),
                "missing_labels": int(validation["missing_labels"]),
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
                "semantic_facets": ["event_class", "event_slug"],
                "metadata_facets": ["night", "date", "place_type", "flood_level", "crowd_context"],
                "min_support": 2,
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
            missing_media=int(validation["missing_media"]),
            missing_labels=int(validation["missing_labels"]),
        )

    def _read_pair_rows(self) -> list[dict[str, str]]:
        with self.pair_manifest.open(encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def _load_records(self) -> pd.DataFrame:
        rows = []
        for pair in self._read_pair_rows():
            label = json.loads(Path(pair["label_path"]).read_text(encoding="utf-8"))
            metadata = label["metadata"]
            annotations = label["annotations"]
            event_attrs = self._parse_event_slug(pair["event_slug"])
            event_frames = annotations.get("event_frame") or []
            first_frame = event_frames[0] if event_frames else [None, None]
            event_class = str(annotations["event_class"])
            rows.append(
                {
                    "clip_id": pair["clip_id"],
                    "dataset_id": DATASET_ID,
                    "source_split": pair["split"],
                    "event_slug": pair["event_slug"],
                    "event_name": pair["event_name"],
                    "event_class": event_class,
                    "event_class_text": EVENT_CLASS_TEXT.get(event_class, self._slug(event_class)),
                    "event_class_ko": EVENT_CLASS_KO.get(event_class, pair["event_name"]),
                    "media_path": pair["media_path"],
                    "label_path": pair["label_path"],
                    "file_stem": pair["file_stem"],
                    "file_name": metadata["file_name"],
                    "width": int(metadata["width"]),
                    "height": int(metadata["height"]),
                    "frame_count": int(metadata["frame_count"]),
                    "data_speed": float(metadata["data_speed"]),
                    "bit_speed": int(metadata["bit_speed"]),
                    "cctv_distribution": metadata["cctv_distribution"],
                    "date": str(metadata["date"]),
                    "night": "true" if bool(metadata["night"]) else "false",
                    "event_start_frame": first_frame[0],
                    "event_end_frame": first_frame[1],
                    "event_length_sec": float(annotations["event_length"]),
                    "event_caption": str(annotations["event_caption"]).strip(),
                    "depersonalization": "true" if bool(annotations["depersonalization"]) else "false",
                    **event_attrs,
                }
            )
        return pd.DataFrame(rows).sort_values("clip_id").reset_index(drop=True)

    def _build_clips(self, records: pd.DataFrame) -> pd.DataFrame:
        clips = records[
            [
                "clip_id",
                "dataset_id",
                "source_split",
                "event_slug",
                "event_name",
                "event_class",
                "file_stem",
                "media_path",
                "label_path",
                "width",
                "height",
                "frame_count",
                "event_start_frame",
                "event_end_frame",
                "event_length_sec",
            ]
        ].copy()
        clips["media_type"] = "video"
        clips["duration_sec"] = pd.NA
        clips["media_exists"] = clips["media_path"].map(lambda path: Path(path).exists())
        clips["label_exists"] = clips["label_path"].map(lambda path: Path(path).exists())
        return clips[
            [
                "clip_id",
                "dataset_id",
                "source_split",
                "event_slug",
                "event_name",
                "event_class",
                "file_stem",
                "media_type",
                "media_path",
                "label_path",
                "duration_sec",
                "width",
                "height",
                "frame_count",
                "event_start_frame",
                "event_end_frame",
                "event_length_sec",
                "media_exists",
                "label_exists",
            ]
        ]

    def _build_documents(self, records: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for row in records.to_dict("records"):
            daypart = "night" if row["night"] == "true" else "daytime"
            context_parts = [f"{daypart} CCTV"]
            if row.get("place_type"):
                context_parts.append(PLACE_TEXT.get(row["place_type"], row["place_type"]))
            if row.get("flood_level"):
                context_parts.append(FLOOD_LEVEL_TEXT.get(row["flood_level"], f"flood level {row['flood_level']}"))
            if row.get("crowd_context"):
                context_parts.append(row["crowd_context"].replace("_", " "))

            rows.extend(
                [
                    {
                        "doc_id": f"{row['clip_id']}:doc:event_caption",
                        "clip_id": row["clip_id"],
                        "dataset_id": DATASET_ID,
                        "doc_type": "event_caption",
                        "text": row["event_caption"],
                        "lang": "ko",
                        "source": row["label_path"],
                    },
                    {
                        "doc_id": f"{row['clip_id']}:doc:event_statement",
                        "clip_id": row["clip_id"],
                        "dataset_id": DATASET_ID,
                        "doc_type": "event_statement",
                        "text": (
                            f"CCTV safety event: {row['event_class_text']} ({row['event_class_ko']}). "
                            f"Dataset label: {row['event_name']}. "
                            f"Context: {', '.join(context_parts)}."
                        ),
                        "lang": "en-ko",
                        "source": row["label_path"],
                    },
                    {
                        "doc_id": f"{row['clip_id']}:doc:temporal_statement",
                        "clip_id": row["clip_id"],
                        "dataset_id": DATASET_ID,
                        "doc_type": "temporal_statement",
                        "text": (
                            f"The event class is {row['event_class_text']} and it occurs from frame "
                            f"{row['event_start_frame']} to {row['event_end_frame']} on date {row['date']}."
                        ),
                        "lang": "en",
                        "source": row["label_path"],
                    },
                ]
            )
        return pd.DataFrame(rows).drop_duplicates("doc_id").reset_index(drop=True)

    def _build_metadata(self, records: pd.DataFrame) -> pd.DataFrame:
        metadata_facets = [
            "event_class",
            "event_class_text",
            "event_group",
            "event_slug",
            "event_name",
            "night",
            "date",
            "depersonalization",
            "resolution",
            "place_type",
            "flood_level",
            "crowd_context",
        ]
        rows = []
        for row in records.to_dict("records"):
            values = {facet: row.get(facet) for facet in metadata_facets}
            values["resolution"] = f"{row['width']}x{row['height']}"
            for facet_name, facet_value in values.items():
                if facet_value is None or str(facet_value) == "":
                    continue
                rows.append(
                    {
                        "clip_id": row["clip_id"],
                        "dataset_id": DATASET_ID,
                        "facet_name": facet_name,
                        "facet_value": str(facet_value),
                        "facet_source": "label_json",
                        "confidence": 1.0,
                    }
                )
        return pd.DataFrame(rows).drop_duplicates(["clip_id", "facet_name"]).reset_index(drop=True)

    def _build_queries_and_qrels(self, metadata: pd.DataFrame) -> tuple[list[dict[str, Any]], pd.DataFrame]:
        table = (
            metadata.pivot_table(index="clip_id", columns="facet_name", values="facet_value", aggfunc="first")
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
            query_id = f"aihub_cctv:{difficulty}:{len(queries) + 1:04d}"
            mask = pd.Series([True] * len(table))
            for key, value in qrel_filters.items():
                if key not in table.columns:
                    return
                mask &= table[key].eq(value)
            targets = table.loc[mask, "clip_id"].tolist()
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

        self._add_weak_queries(table, add_query)
        self._add_medium_queries(table, add_query)
        self._add_strong_queries(table, add_query)

        return queries, pd.DataFrame(qrels_rows)

    def _add_weak_queries(self, table: pd.DataFrame, add_query) -> None:
        for event_class, group in table.groupby("event_class"):
            if not event_class or len(group) < 2:
                continue
            event_text = EVENT_CLASS_TEXT.get(event_class, event_class)
            event_ko = EVENT_CLASS_KO.get(event_class, event_class)
            add_query(
                f"Find CCTV videos showing a {event_text} event ({event_ko}).",
                {"event_class": event_class},
                {},
                "weak",
                {"event_class": event_class},
            )

        for event_slug, group in table.groupby("event_slug"):
            if not event_slug or len(group) < 2:
                continue
            event_name = group["event_name"].iloc[0]
            add_query(
                f"Find CCTV videos labeled as {event_name} ({event_slug.replace('_', ' ')}).",
                {"event_slug": event_slug},
                {},
                "weak",
                {"event_slug": event_slug},
            )

    def _add_medium_queries(self, table: pd.DataFrame, add_query) -> None:
        if "night" in table.columns:
            grouped = table.groupby(["event_class", "night"]).size().reset_index(name="support")
            for row in grouped.to_dict("records"):
                if row["support"] < 2 or not row["event_class"]:
                    continue
                daypart = "night" if row["night"] == "true" else "daytime"
                event_text = EVENT_CLASS_TEXT.get(row["event_class"], row["event_class"])
                add_query(
                    f"Find {daypart} CCTV videos showing a {event_text} event.",
                    {"event_class": row["event_class"], "night": row["night"]},
                    {"night": row["night"]},
                    "medium",
                    {"event_class": row["event_class"]},
                )

        if {"event_class", "date"}.issubset(table.columns):
            grouped = (
                table.groupby(["event_class", "date"])
                .size()
                .reset_index(name="support")
                .sort_values(["support", "event_class", "date"], ascending=[False, True, True])
            )
            for row in grouped.head(80).to_dict("records"):
                if row["support"] < 2 or not row["event_class"]:
                    continue
                event_text = EVENT_CLASS_TEXT.get(row["event_class"], row["event_class"])
                add_query(
                    f"Find CCTV videos from date {row['date']} showing a {event_text} event.",
                    {"event_class": row["event_class"], "date": row["date"]},
                    {"date": row["date"]},
                    "medium",
                    {"event_class": row["event_class"]},
                )

        if {"event_class", "place_type"}.issubset(table.columns):
            grouped = table.groupby(["event_class", "place_type"]).size().reset_index(name="support")
            for row in grouped.to_dict("records"):
                if row["support"] < 2 or not row["place_type"]:
                    continue
                event_text = EVENT_CLASS_TEXT.get(row["event_class"], row["event_class"])
                place_text = PLACE_TEXT.get(row["place_type"], row["place_type"])
                add_query(
                    f"Find {event_text} CCTV videos recorded at a {place_text}.",
                    {"event_class": row["event_class"], "place_type": row["place_type"]},
                    {"place_type": row["place_type"]},
                    "medium",
                    {"event_class": row["event_class"]},
                )

    def _add_strong_queries(self, table: pd.DataFrame, add_query) -> None:
        if {"event_class", "night", "date"}.issubset(table.columns):
            grouped = (
                table.groupby(["event_class", "night", "date"])
                .size()
                .reset_index(name="support")
                .sort_values(["support", "event_class", "night", "date"], ascending=[False, True, True, True])
            )
            for row in grouped.head(80).to_dict("records"):
                if row["support"] < 2 or not row["event_class"]:
                    continue
                daypart = "night" if row["night"] == "true" else "daytime"
                event_text = EVENT_CLASS_TEXT.get(row["event_class"], row["event_class"])
                add_query(
                    f"Find {daypart} CCTV videos from date {row['date']} showing a {event_text} event.",
                    {"event_class": row["event_class"], "night": row["night"], "date": row["date"]},
                    {"night": row["night"], "date": row["date"]},
                    "strong",
                    {"event_class": row["event_class"]},
                )

        flood_facets = {"event_class", "flood_level", "place_type", "night"}
        if flood_facets.issubset(table.columns):
            grouped = (
                table[table["event_class"].eq("Flood")]
                .groupby(["flood_level", "place_type", "night"])
                .size()
                .reset_index(name="support")
            )
            for row in grouped.to_dict("records"):
                if row["support"] < 2 or not row["flood_level"] or not row["place_type"]:
                    continue
                daypart = "night" if row["night"] == "true" else "daytime"
                level_text = FLOOD_LEVEL_TEXT.get(row["flood_level"], f"flood level {row['flood_level']}")
                place_text = PLACE_TEXT.get(row["place_type"], row["place_type"])
                add_query(
                    f"Find {daypart} CCTV flood videos at {level_text} in a {place_text}.",
                    {
                        "event_class": "Flood",
                        "flood_level": row["flood_level"],
                        "place_type": row["place_type"],
                        "night": row["night"],
                    },
                    {
                        "flood_level": row["flood_level"],
                        "place_type": row["place_type"],
                        "night": row["night"],
                    },
                    "strong",
                    {"event_class": "Flood"},
                )

    @staticmethod
    def _parse_event_slug(event_slug: str) -> dict[str, str]:
        if event_slug.startswith("flood_level"):
            match = re.match(r"flood_level([0-9]+)_(.+)", event_slug)
            if match:
                return {
                    "event_group": "flood",
                    "flood_level": match.group(1),
                    "place_type": match.group(2),
                    "crowd_context": "",
                }
        if event_slug.startswith("crowd_density_"):
            return {
                "event_group": "crowd_density",
                "flood_level": "",
                "place_type": "",
                "crowd_context": event_slug.replace("crowd_density_", ""),
            }
        if event_slug == "crowd":
            return {"event_group": "gathering", "flood_level": "", "place_type": "", "crowd_context": ""}
        return {"event_group": event_slug, "flood_level": "", "place_type": "", "crowd_context": ""}

    @staticmethod
    def _slug(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")

    @staticmethod
    def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
        with path.open("w", encoding="utf-8") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")

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
            "# AI Hub Intelligent CCTV Canonical Dataset Summary",
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
