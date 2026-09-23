"""AI Hub 71953 multi-angle CCTV life-safety dataset adapter."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import pandas as pd


DATASET_ID = "aihub_multi_angle_cctv"
DEFAULT_SOURCE_ROOT = Path("external") / "21.다각도 CCTV 생활안전 데이터"


@dataclass(frozen=True)
class CanonicalBuildResult:
    output_dir: Path
    clips: int
    views: int
    evidence_frames: int
    documents: int
    metadata_rows: int
    queries: int
    qrels: int
    missing_media_entries: int


class AIHubMultiAngleCCTVAdapter:
    """Build event-level canonical artifacts for multi-view CCTV VQA data.

    The raw dataset is kept compressed. This adapter streams label JSON files
    from zip archives and records source video entries as zip:// URIs. Visual
    frames can then be materialized selectively from `evidence_frames.parquet`.
    """

    def __init__(
        self,
        dataset_root: Path,
        output_root: Path,
        dataset_version: str,
        source_root: Path | None = None,
        max_events: int | None = None,
    ) -> None:
        self.dataset_root = dataset_root
        self.output_root = output_root
        self.dataset_version = dataset_version
        self.source_root = source_root or dataset_root / DEFAULT_SOURCE_ROOT
        self.max_events = max_events

    @property
    def output_dir(self) -> Path:
        return self.output_root / DATASET_ID / self.dataset_version / "canonical"

    def validate_raw(self) -> dict[str, Any]:
        zips = sorted(self.source_root.rglob("*.zip"))
        source_zips = [p for p in zips if "01.원천데이터" in str(p)]
        label_zips = [p for p in zips if "02.라벨링데이터" in str(p)]
        openable = 0
        bad: list[str] = []
        mp4_entries = 0
        json_entries = 0
        for path in zips:
            try:
                with ZipFile(path) as zf:
                    openable += 1
                    for info in zf.infolist():
                        if info.is_dir():
                            continue
                        lower = info.filename.lower()
                        if lower.endswith(".mp4"):
                            mp4_entries += 1
                        elif lower.endswith(".json"):
                            json_entries += 1
            except Exception:
                bad.append(str(path))
        return {
            "dataset_id": DATASET_ID,
            "source_root": str(self.source_root),
            "zip_files": len(zips),
            "source_zips": len(source_zips),
            "label_zips": len(label_zips),
            "openable_zips": openable,
            "bad_zips": bad,
            "mp4_entries": mp4_entries,
            "json_entries": json_entries,
            "valid": bool(zips and not bad and source_zips and label_zips and mp4_entries and json_entries),
        }

    def build(self, overwrite: bool = False) -> CanonicalBuildResult:
        validation = self.validate_raw()
        if not validation["valid"]:
            raise RuntimeError(f"AI Hub multi-angle CCTV raw validation failed: {validation}")

        out = self.output_dir
        out.mkdir(parents=True, exist_ok=True)
        if any(out.iterdir()) and not overwrite:
            raise FileExistsError(f"{out} is not empty. Use overwrite=True.")

        records, views, evidence_frames, missing_media_entries = self._load_records()
        clips = self._build_clips(records, evidence_frames)
        documents = self._build_documents(records)
        metadata = self._build_metadata(records)
        queries, qrels = self._build_queries_and_qrels(records, metadata)

        clips.to_parquet(out / "clips.parquet", index=False)
        pd.DataFrame(views).to_parquet(out / "views.parquet", index=False)
        pd.DataFrame(evidence_frames).to_parquet(out / "evidence_frames.parquet", index=False)
        documents.to_parquet(out / "documents.parquet", index=False)
        metadata.to_parquet(out / "metadata.parquet", index=False)
        self._write_jsonl(out / "queries.jsonl", queries)
        qrels.to_csv(out / "qrels.tsv", sep="\t", index=False)

        manifest = {
            "dataset_id": DATASET_ID,
            "dataset_version": self.dataset_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source_root": str(self.source_root),
            "output_dir": str(out),
            "counts": {
                "clips": int(len(clips)),
                "views": int(len(views)),
                "evidence_frames": int(len(evidence_frames)),
                "documents": int(len(documents)),
                "metadata_rows": int(len(metadata)),
                "queries": int(len(queries)),
                "qrels": int(len(qrels)),
                "missing_media_entries": int(missing_media_entries),
            },
            "raw_validation": validation,
            "schema_files": [
                "clips.parquet",
                "views.parquet",
                "evidence_frames.parquet",
                "documents.parquet",
                "metadata.parquet",
                "queries.jsonl",
                "qrels.tsv",
            ],
            "query_generation": {
                "instance_vqa": "Original label question is used as query; target is the same event.",
                "group_queries": "Event-class and split/event-class group queries provide broader retrieval workloads.",
                "no_question_text_in_documents": True,
            },
            "media_storage": "Videos are referenced by zip:// URIs. Only evidence frames should be materialized.",
            "multimodal_design": {
                "clip_unit": "event",
                "view_unit": "c1/c2 CCTV video",
                "evidence_unit": "view-specific frame/object/bbox row",
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
            views=len(views),
            evidence_frames=len(evidence_frames),
            documents=len(documents),
            metadata_rows=len(metadata),
            queries=len(queries),
            qrels=len(qrels),
            missing_media_entries=missing_media_entries,
        )

    def _load_records(self) -> tuple[pd.DataFrame, list[dict[str, Any]], list[dict[str, Any]], int]:
        rows: list[dict[str, Any]] = []
        views: list[dict[str, Any]] = []
        evidence_rows: list[dict[str, Any]] = []
        missing_media_entries = 0
        source_index_cache: dict[Path, set[str]] = {}

        label_zips = [
            path
            for path in sorted(self.source_root.rglob("*.zip"))
            if "02.라벨링데이터" in str(path)
        ]
        for label_zip in label_zips:
            split = self._split_from_path(label_zip)
            category = self._category_from_zip(label_zip)
            source_zip = self._source_zip_for_label_zip(label_zip)
            source_entries = self._zip_entries(source_zip, source_index_cache) if source_zip.exists() else set()
            with ZipFile(label_zip) as zf:
                json_infos = [info for info in zf.infolist() if not info.is_dir() and info.filename.lower().endswith(".json")]
                for info in sorted(json_infos, key=lambda x: x.filename):
                    if self.max_events is not None and len(rows) >= self.max_events:
                        break
                    obj = json.loads(zf.read(info).decode("utf-8-sig"))
                    event_dir = Path(info.filename).parent.name
                    event_id = Path(info.filename).stem
                    clip_id = f"{DATASET_ID}:{split}:{event_id}"
                    annotations = obj.get("annotations", {})
                    event_class = str(annotations.get("event_class") or self._event_class_from_category(category))
                    question = str(annotations.get("question") or "").strip()
                    answer = str(annotations.get("answer") or "").strip()
                    caption = annotations.get("caption") or {}
                    evidence = annotations.get("evidence") or {}
                    video_rows = sorted(obj.get("videos") or [], key=lambda row: str(row.get("view", "")))

                    view_names: list[str] = []
                    view_caption_texts: dict[str, str] = {}
                    view_cot_texts: dict[str, str] = {}
                    view_evidence_texts: dict[str, str] = {}
                    date_values: list[str] = []
                    time_values: list[str] = []
                    cameras: list[str] = []
                    angles: list[str] = []
                    distributions: list[str] = []
                    sources: list[str] = []
                    lengths: list[float] = []
                    widths: list[int] = []
                    heights: list[int] = []

                    for video in video_rows:
                        view = str(video.get("view") or Path(video.get("filename", "")).stem.split("_")[-1])
                        filename = str(video.get("filename") or f"{event_id}_{view}.mp4")
                        media_entry = f"{event_dir}/{filename}"
                        media_exists = media_entry in source_entries
                        missing_media_entries += 0 if media_exists else 1
                        media_uri = f"zip://{source_zip}!{media_entry}"
                        view_names.append(view)
                        cameras.append(str(video.get("cctv_camera") or ""))
                        angles.append(str(video.get("cctv_angle") or ""))
                        distributions.append(str(video.get("cctv_distribution") or ""))
                        sources.append(str(video.get("source") or ""))
                        date_values.append(str(video.get("date") or ""))
                        time_values.append(str(video.get("time") or ""))
                        lengths.append(self._safe_float(video.get("length")))
                        widths.append(self._safe_int(video.get("width")))
                        heights.append(self._safe_int(video.get("height")))

                        cap = caption.get(view, {}) if isinstance(caption, dict) else {}
                        view_caption_texts[view] = str(cap.get("caption_text") or "").strip()
                        view_cot_texts[view] = self._cot_to_text(cap.get("cot") or {})
                        ev = evidence.get(view, {}) if isinstance(evidence, dict) else {}
                        view_evidence_texts[view] = str(ev.get("evidence_text") or "").strip()

                        views.append(
                            {
                                "clip_id": clip_id,
                                "dataset_id": DATASET_ID,
                                "event_id": event_id,
                                "source_split": split,
                                "category": category,
                                "view": view,
                                "media_path": media_uri,
                                "source_zip_path": str(source_zip),
                                "media_entry": media_entry,
                                "media_exists": media_exists,
                                "filename": filename,
                                "width": self._safe_int(video.get("width")),
                                "height": self._safe_int(video.get("height")),
                                "date": str(video.get("date") or ""),
                                "time": str(video.get("time") or ""),
                                "length_sec": self._safe_float(video.get("length")),
                                "cctv_distribution": str(video.get("cctv_distribution") or ""),
                                "cctv_camera": str(video.get("cctv_camera") or ""),
                                "cctv_angle": str(video.get("cctv_angle") or ""),
                                "source": str(video.get("source") or ""),
                            }
                        )

                        for evidence_row in self._evidence_rows_for_view(
                            clip_id=clip_id,
                            event_id=event_id,
                            split=split,
                            category=category,
                            view=view,
                            media_uri=media_uri,
                            source_zip=source_zip,
                            media_entry=media_entry,
                            evidence=ev,
                        ):
                            evidence_rows.append(evidence_row)

                    event_frame_values = [
                        int(row["frame_index"])
                        for row in evidence_rows
                        if row["clip_id"] == clip_id and row.get("frame_index") is not None
                    ]
                    rows.append(
                        {
                            "clip_id": clip_id,
                            "dataset_id": DATASET_ID,
                            "source_split": split,
                            "event_id": event_id,
                            "category": category,
                            "event_group": category.split("_", 1)[0],
                            "event_class": event_class,
                            "question": question,
                            "answer": answer,
                            "label_path": f"zip://{label_zip}!{info.filename}",
                            "label_zip_path": str(label_zip),
                            "label_entry": info.filename,
                            "source_zip_path": str(source_zip),
                            "views": ",".join(sorted(set(view_names))),
                            "view_count": len(set(view_names)),
                            "date": self._first_nonempty(date_values),
                            "time": self._first_nonempty(time_values),
                            "time_bucket": self._time_bucket(self._first_nonempty(time_values)),
                            "camera_pair": "|".join(cameras),
                            "angle_pair": "|".join(angles),
                            "distribution_pair": "|".join(distributions),
                            "source_pair": "|".join(sources),
                            "duration_sec_max": max(lengths) if lengths else None,
                            "width_max": max(widths) if widths else None,
                            "height_max": max(heights) if heights else None,
                            "event_start_frame": min(event_frame_values) if event_frame_values else None,
                            "event_end_frame": max(event_frame_values) if event_frame_values else None,
                            "caption_c1": view_caption_texts.get("c1", ""),
                            "caption_c2": view_caption_texts.get("c2", ""),
                            "cot_c1": view_cot_texts.get("c1", ""),
                            "cot_c2": view_cot_texts.get("c2", ""),
                            "evidence_text_c1": view_evidence_texts.get("c1", ""),
                            "evidence_text_c2": view_evidence_texts.get("c2", ""),
                        }
                    )
                if self.max_events is not None and len(rows) >= self.max_events:
                    break

        records = pd.DataFrame(rows).sort_values("clip_id").reset_index(drop=True)
        return records, views, evidence_rows, missing_media_entries

    def _build_clips(self, records: pd.DataFrame, evidence_frames: list[dict[str, Any]]) -> pd.DataFrame:
        evidence_df = pd.DataFrame(evidence_frames)
        evidence_count = (
            evidence_df.groupby("clip_id").size().rename("evidence_frame_rows").reset_index()
            if not evidence_df.empty
            else pd.DataFrame(columns=["clip_id", "evidence_frame_rows"])
        )
        clips = records.merge(evidence_count, on="clip_id", how="left")
        clips["evidence_frame_rows"] = clips["evidence_frame_rows"].fillna(0).astype(int)
        clips["media_type"] = "multi_view_video"
        clips["media_path"] = "multi_view_zip"
        clips["duration_sec"] = clips["duration_sec_max"]
        clips["media_exists"] = clips["view_count"].ge(2)
        clips["label_exists"] = True
        keep = [
            "clip_id",
            "dataset_id",
            "source_split",
            "event_id",
            "category",
            "event_group",
            "event_class",
            "media_type",
            "media_path",
            "label_path",
            "duration_sec",
            "width_max",
            "height_max",
            "event_start_frame",
            "event_end_frame",
            "view_count",
            "views",
            "evidence_frame_rows",
            "media_exists",
            "label_exists",
        ]
        return clips[keep].rename(columns={"width_max": "width", "height_max": "height"})

    def _build_documents(self, records: pd.DataFrame) -> pd.DataFrame:
        rows: list[dict[str, Any]] = []
        for row in records.to_dict("records"):
            context = (
                f"event class: {row['event_class']}; views: {row['views']}; "
                f"date: {row['date']}; time bucket: {row['time_bucket']}; cameras: {row['camera_pair']}."
            )
            doc_specs = [
                ("answer", row["answer"], "ko"),
                ("caption_c1", row["caption_c1"], "ko"),
                ("caption_c2", row["caption_c2"], "ko"),
                ("cot_c1", row["cot_c1"], "ko"),
                ("cot_c2", row["cot_c2"], "ko"),
                ("evidence_c1", row["evidence_text_c1"], "ko"),
                ("evidence_c2", row["evidence_text_c2"], "ko"),
                (
                    "event_statement",
                    f"다각도 CCTV 생활안전 사건이다. {row['event_class']} 상황이며 {context}",
                    "ko",
                ),
            ]
            for doc_type, text, lang in doc_specs:
                clean = " ".join(str(text or "").split())
                if not clean:
                    continue
                rows.append(
                    {
                        "doc_id": f"{row['clip_id']}:doc:{doc_type}",
                        "clip_id": row["clip_id"],
                        "dataset_id": DATASET_ID,
                        "doc_type": doc_type,
                        "text": clean,
                        "lang": lang,
                        "source": row["label_path"],
                    }
                )
        return pd.DataFrame(rows).drop_duplicates("doc_id").reset_index(drop=True)

    def _build_metadata(self, records: pd.DataFrame) -> pd.DataFrame:
        facets = [
            "source_split",
            "event_id",
            "category",
            "event_group",
            "event_class",
            "views",
            "view_count",
            "date",
            "time_bucket",
            "camera_pair",
            "angle_pair",
            "distribution_pair",
            "source_pair",
            "resolution",
        ]
        rows: list[dict[str, Any]] = []
        for row in records.to_dict("records"):
            values = {facet: row.get(facet) for facet in facets}
            values["resolution"] = f"{row.get('width_max')}x{row.get('height_max')}"
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

    def _build_queries_and_qrels(
        self,
        records: pd.DataFrame,
        metadata: pd.DataFrame,
    ) -> tuple[list[dict[str, Any]], pd.DataFrame]:
        table = (
            metadata.pivot_table(index="clip_id", columns="facet_name", values="facet_value", aggfunc="first")
            .reset_index()
            .fillna("")
        )
        question_by_clip = {row["clip_id"]: row["question"] for row in records.to_dict("records")}
        event_by_clip = {row["clip_id"]: row["event_class"] for row in records.to_dict("records")}

        queries: list[dict[str, Any]] = []
        qrels_rows: list[dict[str, Any]] = []

        def add_query(
            query_text: str,
            targets: list[str],
            metadata_filters: dict[str, str],
            difficulty: str,
            semantic_filter: dict[str, str],
            task: str = "text_metadata_retrieval",
        ) -> None:
            if not targets:
                return
            query_id = f"aihub71953:{difficulty}:{len(queries) + 1:05d}"
            queries.append(
                {
                    "query_id": query_id,
                    "dataset_id": DATASET_ID,
                    "query_text": query_text,
                    "task": task,
                    "metadata_filter": metadata_filters,
                    "semantic_filter": semantic_filter,
                    "qrel_filter": {"target_clip_ids": targets[:20]} if len(targets) <= 20 else semantic_filter,
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

        for clip_id, question in question_by_clip.items():
            if not question:
                continue
            event_class = event_by_clip.get(clip_id, "")
            add_query(
                question,
                [clip_id],
                {"event_class": event_class} if event_class else {},
                "instance_vqa",
                {"event_class": event_class, "clip_id": clip_id},
                "vqa_evidence_lookup",
            )

        for event_class, group in table.groupby("event_class"):
            if not event_class or len(group) < 2:
                continue
            targets = group["clip_id"].tolist()
            add_query(
                f"'{event_class}' 상황이 발생한 다각도 CCTV 사건을 찾아라.",
                targets,
                {},
                "weak_event",
                {"event_class": event_class},
            )

        if {"source_split", "event_class"}.issubset(table.columns):
            for (split, event_class), group in table.groupby(["source_split", "event_class"]):
                if not split or not event_class or len(group) < 2:
                    continue
                add_query(
                    f"{split} 분할에서 '{event_class}' 상황이 발생한 CCTV 사건을 찾아라.",
                    group["clip_id"].tolist(),
                    {"source_split": split},
                    "medium_split_event",
                    {"event_class": event_class},
                )

        if {"time_bucket", "event_class"}.issubset(table.columns):
            grouped = (
                table.groupby(["time_bucket", "event_class"])
                .size()
                .reset_index(name="support")
                .sort_values(["support", "time_bucket", "event_class"], ascending=[False, True, True])
            )
            for row in grouped.head(120).to_dict("records"):
                if row["support"] < 2 or not row["time_bucket"] or not row["event_class"]:
                    continue
                mask = table["time_bucket"].eq(row["time_bucket"]) & table["event_class"].eq(row["event_class"])
                add_query(
                    f"{row['time_bucket']} 시간대에 '{row['event_class']}' 상황이 발생한 CCTV 사건을 찾아라.",
                    table.loc[mask, "clip_id"].tolist(),
                    {"time_bucket": row["time_bucket"]},
                    "strong_time_event",
                    {"event_class": row["event_class"]},
                )

        return queries, pd.DataFrame(qrels_rows)

    def _evidence_rows_for_view(
        self,
        *,
        clip_id: str,
        event_id: str,
        split: str,
        category: str,
        view: str,
        media_uri: str,
        source_zip: Path,
        media_entry: str,
        evidence: dict[str, Any],
    ) -> list[dict[str, Any]]:
        frame_ids = evidence.get("frame_id") or []
        obj_ids = evidence.get("obj_id") or []
        bboxes = evidence.get("obj_bbox") or []
        labels = evidence.get("obj_label") or []
        text = str(evidence.get("evidence_text") or "").strip()
        rows: list[dict[str, Any]] = []
        for idx, frame_id in enumerate(frame_ids):
            bbox = bboxes[idx] if idx < len(bboxes) else None
            if isinstance(bbox, list) and len(bbox) >= 4:
                x1, y1, x2, y2 = [self._safe_int(v) for v in bbox[:4]]
            else:
                x1 = y1 = x2 = y2 = None
            rows.append(
                {
                    "evidence_id": f"{clip_id}:{view}:ev{idx:02d}",
                    "clip_id": clip_id,
                    "dataset_id": DATASET_ID,
                    "event_id": event_id,
                    "source_split": split,
                    "category": category,
                    "view": view,
                    "frame_seq": idx,
                    "frame_index": self._safe_int(frame_id),
                    "timestamp_sec": None,
                    "obj_id": str(obj_ids[idx]) if idx < len(obj_ids) else "",
                    "obj_label": str(labels[idx]) if idx < len(labels) else "",
                    "bbox_x1": x1,
                    "bbox_y1": y1,
                    "bbox_x2": x2,
                    "bbox_y2": y2,
                    "evidence_text": text,
                    "media_path": media_uri,
                    "source_zip_path": str(source_zip),
                    "media_entry": media_entry,
                    "extraction_strategy": "label_evidence_frame",
                }
            )
        return rows

    def _zip_entries(self, path: Path, cache: dict[Path, set[str]]) -> set[str]:
        if path not in cache:
            with ZipFile(path) as zf:
                cache[path] = {info.filename for info in zf.infolist() if not info.is_dir()}
        return cache[path]

    def _source_zip_for_label_zip(self, label_zip: Path) -> Path:
        name = label_zip.name
        if name.startswith("TL_"):
            source_name = "TS_" + name[3:]
            return label_zip.parent.parent / "01.원천데이터" / source_name
        if name.startswith("VL_"):
            source_name = "VS_" + name[3:]
            return label_zip.parent.parent / "01.원천데이터" / source_name
        return label_zip

    @staticmethod
    def _split_from_path(path: Path) -> str:
        parts = path.parts
        if "Training" in parts:
            return "Training"
        if "Validation" in parts:
            return "Validation"
        return "unknown"

    @staticmethod
    def _category_from_zip(path: Path) -> str:
        stem = path.stem
        if stem.startswith(("TL_", "TS_", "VL_", "VS_")):
            return stem[3:]
        return stem

    @staticmethod
    def _event_class_from_category(category: str) -> str:
        return category.split("_")[-1] if "_" in category else category

    @staticmethod
    def _cot_to_text(cot: dict[str, Any]) -> str:
        if not isinstance(cot, dict):
            return ""
        return " ".join(f"{key}: {value}" for key, value in sorted(cot.items()))

    @staticmethod
    def _first_nonempty(values: list[str]) -> str:
        for value in values:
            if value:
                return value
        return ""

    @staticmethod
    def _time_bucket(value: str) -> str:
        try:
            hour = int(str(value).split(":", 1)[0])
        except Exception:
            return ""
        if 5 <= hour < 12:
            return "morning"
        if 12 <= hour < 17:
            return "afternoon"
        if 17 <= hour < 21:
            return "evening"
        return "night"

    @staticmethod
    def _safe_int(value: Any) -> int | None:
        try:
            if value is None or value == "":
                return None
            return int(float(value))
        except Exception:
            return None

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except Exception:
            return None

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
            "# AI Hub 71953 Multi-Angle CCTV Canonical Summary",
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
        lines.extend(
            [
                "",
                "## Multimodal Contract",
                "",
                "- `clips.parquet` is event-level.",
                "- `views.parquet` stores `c1/c2` source video URIs.",
                "- `evidence_frames.parquet` stores frame/object/bbox evidence for visual grounding.",
                "- Source mp4 files remain compressed and are referenced by `zip://...!entry`.",
            ]
        )
        (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
