"""AI Hub abnormal behavior CCTV dataset adapter."""

from __future__ import annotations

import csv
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


DATASET_ID = "aihub_abnormal_cctv"

EVENT_TEXT = {
    "assault": "assault",
    "fight": "fight",
    "burglary": "burglary",
    "vandalism": "vandalism",
    "swoon": "swoon",
    "wander": "wandering",
    "trespass": "trespassing",
    "dump": "dumping",
    "robbery": "robbery",
    "datefight": "dating violence or harassment",
    "kidnap": "kidnapping",
    "drunken": "drunken behavior",
}


@dataclass(frozen=True)
class CanonicalBuildResult:
    output_dir: Path
    clips: int
    documents: int
    metadata_rows: int
    queries: int
    qrels: int
    missing_labels: int


class AIHubAbnormalCCTVAdapter:
    """Build canonical artifacts for AI Hub abnormal behavior CCTV clips."""

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
        pair_rows = self._read_pair_rows() if self.pair_manifest.exists() else []
        missing_labels = sum(1 for row in pair_rows if not row.get("label_path") or not Path(row["label_path"]).exists())
        labeled_pairs = len(pair_rows) - missing_labels
        return {
            "dataset_id": DATASET_ID,
            "raw_root": str(self.raw_root),
            "pair_manifest": str(self.pair_manifest),
            "paired_clips": len(pair_rows),
            "labeled_pairs": labeled_pairs,
            "missing_labels": missing_labels,
            "valid": labeled_pairs > 0,
        }

    def build(self, overwrite: bool = False) -> CanonicalBuildResult:
        validation = self.validate_raw()
        if not validation["valid"]:
            raise RuntimeError(f"AI Hub abnormal CCTV raw validation failed: {validation}")

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
                "semantic_facets": ["event_name", "event_variant", "primary_action"],
                "metadata_facets": ["daypart", "season", "weather", "inout", "location", "camera_id"],
                "min_support": 2,
            },
            "media_storage": "Videos are referenced by zip:// URIs and are not extracted.",
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
            missing_labels=int(validation["missing_labels"]),
        )

    def _read_pair_rows(self) -> list[dict[str, str]]:
        with self.pair_manifest.open(encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    def _load_records(self) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        seen_clip_ids: dict[str, int] = {}
        for pair in self._read_pair_rows():
            if not pair.get("label_path") or not Path(pair["label_path"]).exists():
                continue
            xml = self._parse_xml(Path(pair["label_path"]))
            filename_attrs = self._parse_filename(pair["file_name"])
            event_name = self._normalize_event(xml.get("event_name") or pair["event_en"])
            event_text = EVENT_TEXT.get(event_name, event_name.replace("_", " "))
            actions = sorted(set(xml["actions"]))
            primary_action = actions[0] if actions else ""
            action_set = ", ".join(actions)
            base_clip_id = pair["clip_id"]
            duplicate_idx = seen_clip_ids.get(base_clip_id, 0)
            seen_clip_ids[base_clip_id] = duplicate_idx + 1
            clip_id = base_clip_id if duplicate_idx == 0 else f"{base_clip_id}_{duplicate_idx + 1}"
            rows.append(
                {
                    "clip_id": clip_id,
                    "dataset_id": DATASET_ID,
                    "source_split": pair["split"],
                    "category_dir": pair["category_dir"],
                    "category_order": pair["category_order"],
                    "event_ko": pair["event_ko"],
                    "event_name": event_name,
                    "event_text": event_text,
                    "event_variant": filename_attrs.get("event_variant") or event_name,
                    "file_stem": pair["file_stem"],
                    "file_name": pair["file_name"],
                    "media_path": pair["media_uri"],
                    "media_zip_path": pair["media_zip_path"],
                    "media_entry": pair["media_entry"],
                    "media_size_bytes": int(pair["media_size_bytes"]),
                    "label_path": pair["label_path"],
                    "label_entry": pair["label_entry"],
                    "camera_id": filename_attrs.get("camera_id") or "",
                    "scene_id": filename_attrs.get("scene_id") or "",
                    "location": xml.get("location") or filename_attrs.get("location") or "",
                    "place_id": (xml.get("location") or filename_attrs.get("location") or "").lower(),
                    "season": self._normalize_value(xml.get("season") or filename_attrs.get("season") or ""),
                    "weather": self._normalize_value(xml.get("weather") or ""),
                    "daypart": self._normalize_value(xml.get("time") or filename_attrs.get("daypart") or ""),
                    "inout": self._normalize_value(xml.get("inout") or ""),
                    "population": self._safe_int(xml.get("population")),
                    "population_bucket": self._population_bucket(self._safe_int(xml.get("population"))),
                    "character": xml.get("character") or "",
                    "duration": xml.get("duration") or "",
                    "fps": self._safe_float(xml.get("fps")),
                    "frames": self._safe_int(xml.get("frames")),
                    "width": self._safe_int(xml.get("width")),
                    "height": self._safe_int(xml.get("height")),
                    "event_starttime": xml.get("event_starttime") or "",
                    "event_duration": xml.get("event_duration") or "",
                    "actions": action_set,
                    "primary_action": primary_action,
                    "action_count": len(actions),
                    "object_count": xml.get("object_count", 0),
                    "frame_span_count": xml.get("frame_span_count", 0),
                }
            )
        return pd.DataFrame(rows).sort_values("clip_id").reset_index(drop=True)

    def _build_clips(self, records: pd.DataFrame) -> pd.DataFrame:
        clips = records[
            [
                "clip_id",
                "dataset_id",
                "source_split",
                "event_name",
                "event_ko",
                "event_variant",
                "file_stem",
                "file_name",
                "media_path",
                "media_zip_path",
                "media_entry",
                "media_size_bytes",
                "label_path",
                "label_entry",
                "duration",
                "fps",
                "frames",
                "width",
                "height",
                "event_starttime",
                "event_duration",
            ]
        ].copy()
        clips["media_type"] = "video"
        clips["media_exists"] = True
        clips["label_exists"] = clips["label_path"].map(lambda path: Path(path).exists())
        return clips

    def _build_documents(self, records: pd.DataFrame) -> pd.DataFrame:
        rows = []
        for row in records.to_dict("records"):
            context = self._context_text(row)
            action_text = row["actions"] if row["actions"] else "not specified"
            rows.extend(
                [
                    {
                        "doc_id": f"{row['clip_id']}:doc:event_statement",
                        "clip_id": row["clip_id"],
                        "dataset_id": DATASET_ID,
                        "doc_type": "event_statement",
                        "text": (
                            f"CCTV abnormal behavior event: {row['event_text']} ({row['event_ko']}). "
                            f"Variant: {row['event_variant']}. Context: {context}. "
                            f"Observed actions include {action_text}."
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
                            f"The {row['event_text']} event starts at {row['event_starttime']} and lasts "
                            f"{row['event_duration']} in a {row['duration']} CCTV video."
                        ),
                        "lang": "en",
                        "source": row["label_path"],
                    },
                    {
                        "doc_id": f"{row['clip_id']}:doc:metadata_statement",
                        "clip_id": row["clip_id"],
                        "dataset_id": DATASET_ID,
                        "doc_type": "metadata_statement",
                        "text": (
                            f"The clip is recorded by camera {row['camera_id']} at {row['place_id']} "
                            f"during {row['daypart']} in {row['season']} weather {row['weather']}, "
                            f"{row['inout']} environment, population {row['population']}."
                        ),
                        "lang": "en",
                        "source": row["label_path"],
                    },
                ]
            )
        return pd.DataFrame(rows).drop_duplicates("doc_id").reset_index(drop=True)

    def _build_metadata(self, records: pd.DataFrame) -> pd.DataFrame:
        facets = [
            "event_name",
            "event_text",
            "event_ko",
            "event_variant",
            "primary_action",
            "actions",
            "camera_id",
            "scene_id",
            "location",
            "place_id",
            "season",
            "weather",
            "daypart",
            "inout",
            "population_bucket",
            "character",
            "resolution",
        ]
        rows = []
        for row in records.to_dict("records"):
            values = {facet: row.get(facet) for facet in facets}
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
                        "facet_source": "label_xml",
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
            query_id = f"aihub_abnormal:{difficulty}:{len(queries) + 1:04d}"
            mask = pd.Series([True] * len(table))
            for key, value in qrel_filters.items():
                if key not in table.columns:
                    return
                mask &= table[key].eq(value)
            targets = table.loc[mask, "clip_id"].tolist()
            if len(targets) < 2:
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
        for event_name, group in table.groupby("event_name"):
            if not event_name or len(group) < 2:
                continue
            event_text = group["event_text"].iloc[0] if "event_text" in group else EVENT_TEXT.get(event_name, event_name)
            event_ko = group["event_ko"].iloc[0] if "event_ko" in group else event_name
            add_query(
                f"Find CCTV videos showing {event_text} abnormal behavior ({event_ko}).",
                {"event_name": event_name},
                {},
                "weak",
                {"event_name": event_name},
            )

        if "primary_action" in table.columns:
            for action, group in table.groupby("primary_action"):
                if not action or len(group) < 2:
                    continue
                add_query(
                    f"Find CCTV videos where a person is {action}.",
                    {"primary_action": action},
                    {},
                    "weak",
                    {"primary_action": action},
                )

    def _add_medium_queries(self, table: pd.DataFrame, add_query) -> None:
        for facet, text_template in [
            ("daypart", "Find {facet_value} CCTV videos showing {event_text} abnormal behavior."),
            ("season", "Find CCTV videos in {facet_value} season showing {event_text} abnormal behavior."),
            ("inout", "Find {facet_value} CCTV videos showing {event_text} abnormal behavior."),
            ("location", "Find CCTV videos at {facet_value} showing {event_text} abnormal behavior."),
            ("camera_id", "Find CCTV videos from camera {facet_value} showing {event_text} abnormal behavior."),
        ]:
            if {"event_name", facet}.issubset(table.columns):
                grouped = table.groupby(["event_name", facet]).size().reset_index(name="support")
                for row in grouped.to_dict("records"):
                    if row["support"] < 2 or not row["event_name"] or not row[facet]:
                        continue
                    event_text = EVENT_TEXT.get(row["event_name"], row["event_name"])
                    add_query(
                        text_template.format(facet_value=row[facet], event_text=event_text),
                        {"event_name": row["event_name"], facet: row[facet]},
                        {facet: row[facet]},
                        "medium",
                        {"event_name": row["event_name"]},
                    )

    def _add_strong_queries(self, table: pd.DataFrame, add_query) -> None:
        combos = [
            ("event_name", "daypart", "inout"),
            ("event_name", "season", "location"),
            ("event_name", "daypart", "season"),
            ("event_name", "location", "camera_id"),
        ]
        for semantic, facet1, facet2 in combos:
            if {semantic, facet1, facet2}.issubset(table.columns):
                grouped = (
                    table.groupby([semantic, facet1, facet2])
                    .size()
                    .reset_index(name="support")
                    .sort_values(["support", semantic, facet1, facet2], ascending=[False, True, True, True])
                )
                for row in grouped.head(120).to_dict("records"):
                    if row["support"] < 2 or not row[semantic] or not row[facet1] or not row[facet2]:
                        continue
                    event_text = EVENT_TEXT.get(row[semantic], row[semantic])
                    add_query(
                        (
                            f"Find CCTV videos showing {event_text} abnormal behavior "
                            f"where {facet1} is {row[facet1]} and {facet2} is {row[facet2]}."
                        ),
                        {semantic: row[semantic], facet1: row[facet1], facet2: row[facet2]},
                        {facet1: row[facet1], facet2: row[facet2]},
                        "strong",
                        {semantic: row[semantic]},
                    )

    @staticmethod
    def _parse_xml(path: Path) -> dict[str, Any]:
        root = ET.parse(path).getroot()

        def find_text(xpath: str) -> str:
            node = root.find(xpath)
            return node.text.strip() if node is not None and node.text is not None else ""

        actions: list[str] = []
        frame_span_count = 0
        for action in root.findall(".//action"):
            name_node = action.find("actionname")
            if name_node is not None and name_node.text:
                actions.append(name_node.text.strip())
            frame_span_count += len(action.findall("frame"))

        return {
            "folder": find_text("folder"),
            "filename": find_text("filename"),
            "width": find_text("size/width"),
            "height": find_text("size/height"),
            "duration": find_text("header/duration"),
            "fps": find_text("header/fps"),
            "frames": find_text("header/frames"),
            "inout": find_text("header/inout"),
            "location": find_text("header/location"),
            "season": find_text("header/season"),
            "weather": find_text("header/weather"),
            "time": find_text("header/time"),
            "population": find_text("header/population"),
            "character": find_text("header/character"),
            "event_name": find_text("event/eventname"),
            "event_starttime": find_text("event/starttime"),
            "event_duration": find_text("event/duration"),
            "actions": actions,
            "object_count": len(root.findall("object")),
            "frame_span_count": frame_span_count,
        }

    @staticmethod
    def _parse_filename(file_name: str) -> dict[str, str]:
        stem = Path(file_name).stem
        pattern = re.compile(
            r"(?P<scene_id>.+?)_cam(?P<camera_id>[0-9]+)_(?P<event_variant>[a-z]+[0-9]*)_"
            r"(?P<location>place[0-9]+)_(?P<daypart>day|night)_(?P<season>spring|summer|fall|winter)$",
            re.IGNORECASE,
        )
        match = pattern.match(stem)
        if not match:
            return {"scene_id": stem}
        values = match.groupdict()
        values["camera_id"] = f"cam{values['camera_id']}"
        values["event_variant"] = values["event_variant"].lower()
        values["location"] = values["location"].upper()
        values["daypart"] = values["daypart"].lower()
        values["season"] = values["season"].lower()
        return values

    @staticmethod
    def _normalize_event(text: str) -> str:
        text = re.sub(r"[0-9]+$", "", str(text).strip().lower())
        text = text.replace("assult", "assault")
        return text

    @staticmethod
    def _normalize_value(text: str) -> str:
        return str(text).strip().lower()

    @staticmethod
    def _safe_int(value: Any) -> int:
        try:
            return int(float(value))
        except Exception:
            return 0

    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            return float(value)
        except Exception:
            return 0.0

    @staticmethod
    def _population_bucket(value: int) -> str:
        if value <= 0:
            return "unknown"
        if value == 1:
            return "single_person"
        if value <= 3:
            return "small_group"
        return "group"

    @staticmethod
    def _context_text(row: dict[str, Any]) -> str:
        parts = [
            row.get("inout", ""),
            row.get("place_id", ""),
            row.get("daypart", ""),
            row.get("season", ""),
            row.get("weather", ""),
            f"population {row.get('population', '')}",
            f"camera {row.get('camera_id', '')}",
        ]
        return ", ".join(part for part in parts if str(part).strip())

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
            "# AI Hub Abnormal CCTV Canonical Dataset Summary",
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
