#!/usr/bin/env python3
"""FreshEvidenceDB P0: reproduce cross-store RAG version races on CPU."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import sqlite3
import statistics
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import HashingVectorizer


SEED = 20260807
N_DOCS = 128
N_WAVES = 8
DOCS_PER_WAVE = 16
N_REPEATS = 5
N_WORKERS = 4
VECTOR_SIZE = 256
PREFIX = "freshevidencedb_p0_"
PROTOCOLS = ("naive_eager", "read_version_filter", "blue_green_epoch", "staged_manifest")


def stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> Tuple[float, float]:
    if total == 0:
        return (0.0, 1.0)
    p = successes / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def percentile(values: Sequence[float], q: float) -> float:
    return float(np.quantile(np.asarray(values, dtype=np.float64), q)) if values else float("nan")


class Corpus:
    def __init__(self) -> None:
        self.vectorizer = HashingVectorizer(
            n_features=VECTOR_SIZE,
            alternate_sign=False,
            norm="l2",
            analyzer="word",
            ngram_range=(1, 2),
        )

    @staticmethod
    def token(doc_id: int) -> str:
        return f"assetd{doc_id:03d}"

    def chunks(self, doc_id: int, version: int, update_kind: str = "initial") -> List[str]:
        key = self.token(doc_id)
        value = f"limit{doc_id:03d}v{version}"
        base = [
            f"{key} operating policy. The current control threshold is {value}. This statement is authoritative.",
            f"{key} implementation procedure for inspection, escalation, and incident handling under revision {version}.",
            f"{key} audit appendix describing reporting obligations and review cadence for revision {version}.",
        ]
        if update_kind == "rechunk" and version > 1:
            return [
                f"{key} operating policy revision {version}.",
                f"The current control threshold for {key} is {value}.",
                f"{key} implementation procedure for inspection and escalation.",
                f"{key} audit appendix for reporting and review cadence.",
            ]
        return base

    def query(self, doc_id: int) -> str:
        return f"{self.token(doc_id)} current control threshold"

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        return self.vectorizer.transform(texts).astype(np.float32).toarray()


class Stores:
    def __init__(self, collection: str, sqlite_path: Path, corpus: Corpus) -> None:
        assert collection.startswith(PREFIX)
        self.collection = collection
        self.sqlite_path = sqlite_path
        self.corpus = corpus
        self.qdrant = QdrantClient(url="http://127.0.0.1:6333", timeout=30)
        existing = {x.name for x in self.qdrant.get_collections().collections}
        if collection in existing:
            self.qdrant.delete_collection(collection)
        self.qdrant.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
        )
        for field in ("doc_id", "version", "epoch"):
            self.qdrant.create_payload_index(
                collection_name=collection,
                field_name=field,
                field_schema=models.PayloadSchemaType.INTEGER,
                wait=True,
            )
        if sqlite_path.exists():
            sqlite_path.unlink()
        self._init_sqlite()
        self.cache: Dict[Tuple, int] = {}
        self.cache_lock = threading.Lock()
        self.write_counts = Counter()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.sqlite_path, timeout=30, isolation_level=None)
        conn.execute("PRAGMA busy_timeout=30000")
        return conn

    def _init_sqlite(self) -> None:
        conn = self.connect()
        # Journal mode is a database-level setting. Reissuing this PRAGMA on
        # every reader connection turns reads into lock-taking operations and
        # can starve the writer under the intended concurrent workload.
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.executescript(
            """
            CREATE TABLE manifest(
                doc_id INTEGER PRIMARY KEY,
                active_version INTEGER NOT NULL,
                deleted INTEGER NOT NULL,
                epoch INTEGER NOT NULL
            );
            CREATE TABLE global_state(id INTEGER PRIMARY KEY CHECK(id=1), active_epoch INTEGER NOT NULL);
            INSERT INTO global_state(id, active_epoch) VALUES(1, 0);
            CREATE VIRTUAL TABLE sparse USING fts5(
                text,
                doc_id UNINDEXED,
                version UNINDEXED,
                epoch UNINDEXED,
                chunk_id UNINDEXED
            );
            """
        )
        conn.close()

    @staticmethod
    def point_id(doc_id: int, version: int, chunk_id: int, epoch: int, blue: bool) -> int:
        if blue:
            return epoch * 100_000_000 + doc_id * 10_000 + version * 100 + chunk_id
        return doc_id * 1_000_000 + version * 1_000 + chunk_id

    def insert_rows(
        self,
        rows: Sequence[Tuple[int, int, int, int, str]],
        *,
        blue: bool,
        dense: bool,
        sparse: bool,
    ) -> None:
        if not rows:
            return
        if dense:
            vectors = self.corpus.embed([row[4] for row in rows])
            points = []
            for row, vector in zip(rows, vectors):
                doc_id, version, epoch, chunk_id, text = row
                points.append(
                    models.PointStruct(
                        id=self.point_id(doc_id, version, chunk_id, epoch, blue),
                        vector=vector.tolist(),
                        payload={
                            "doc_id": doc_id,
                            "version": version,
                            "epoch": epoch,
                            "chunk_id": chunk_id,
                            "text": text,
                        },
                    )
                )
            self.qdrant.upsert(self.collection, points=points, wait=True)
            self.write_counts["dense_rows"] += len(rows)
        if sparse:
            conn = self.connect()
            conn.execute("BEGIN IMMEDIATE")
            conn.executemany(
                "INSERT INTO sparse(text,doc_id,version,epoch,chunk_id) VALUES(?,?,?,?,?)",
                [(text, doc_id, version, epoch, chunk_id) for doc_id, version, epoch, chunk_id, text in rows],
            )
            conn.commit()
            conn.close()
            self.write_counts["sparse_rows"] += len(rows)

    def delete_version(self, doc_ids: Sequence[int], version: int) -> None:
        if not doc_ids:
            return
        filt = models.Filter(
            must=[
                models.FieldCondition(key="doc_id", match=models.MatchAny(any=list(doc_ids))),
                models.FieldCondition(key="version", match=models.MatchValue(value=version)),
            ]
        )
        self.qdrant.delete(self.collection, points_selector=models.FilterSelector(filter=filt), wait=True)
        conn = self.connect()
        placeholders = ",".join("?" for _ in doc_ids)
        conn.execute("BEGIN IMMEDIATE")
        conn.execute(
            f"DELETE FROM sparse WHERE doc_id IN ({placeholders}) AND version=?",
            [*doc_ids, version],
        )
        conn.commit()
        conn.close()

    def initialize_manifest(self) -> None:
        conn = self.connect()
        conn.execute("BEGIN IMMEDIATE")
        conn.executemany(
            "INSERT INTO manifest(doc_id,active_version,deleted,epoch) VALUES(?,?,?,?)",
            [(doc_id, 1, 0, 0) for doc_id in range(N_DOCS)],
        )
        conn.commit()
        conn.close()

    def read_snapshot(self, doc_id: int) -> Tuple[int, bool, int]:
        conn = self.connect()
        conn.execute("BEGIN")
        version, deleted, epoch = conn.execute(
            "SELECT active_version,deleted,epoch FROM manifest WHERE doc_id=?", (doc_id,)
        ).fetchone()
        global_epoch = conn.execute("SELECT active_epoch FROM global_state WHERE id=1").fetchone()[0]
        conn.commit()
        conn.close()
        return int(version), bool(deleted), int(global_epoch if global_epoch is not None else epoch)

    def publish(
        self,
        changes: Sequence[Tuple[int, int, bool]],
        epoch: int,
        update_global: bool,
    ) -> None:
        conn = self.connect()
        conn.execute("BEGIN IMMEDIATE")
        conn.executemany(
            "UPDATE manifest SET active_version=?,deleted=?,epoch=? WHERE doc_id=?",
            [(version, int(deleted), epoch, doc_id) for doc_id, version, deleted in changes],
        )
        if update_global:
            conn.execute("UPDATE global_state SET active_epoch=? WHERE id=1", (epoch,))
        conn.commit()
        conn.close()
        self.write_counts["manifest_rows"] += len(changes) + int(update_global)

    def dense_query(
        self, doc_id: int, query: str, version: Optional[int], epoch: Optional[int]
    ) -> Optional[int]:
        must = [models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc_id))]
        if version is not None:
            must.append(models.FieldCondition(key="version", match=models.MatchValue(value=version)))
        if epoch is not None:
            must.append(models.FieldCondition(key="epoch", match=models.MatchValue(value=epoch)))
        vector = self.corpus.embed([query])[0]
        response = self.qdrant.query_points(
            collection_name=self.collection,
            query=vector,
            query_filter=models.Filter(must=must),
            search_params=models.SearchParams(exact=True),
            limit=1,
            with_payload=True,
        )
        if not response.points:
            return None
        return int(response.points[0].payload["version"])

    def sparse_query(
        self, doc_id: int, query: str, version: Optional[int], epoch: Optional[int]
    ) -> Optional[int]:
        term = self.corpus.token(doc_id)
        sql = "SELECT version FROM sparse WHERE sparse MATCH ? AND doc_id=?"
        params: List[object] = [term, doc_id]
        if version is not None:
            sql += " AND version=?"
            params.append(version)
        if epoch is not None:
            sql += " AND epoch=?"
            params.append(epoch)
        sql += " ORDER BY bm25(sparse) LIMIT 1"
        conn = self.connect()
        row = conn.execute(sql, params).fetchone()
        conn.close()
        return int(row[0]) if row else None

    def cache_get(self, key: Tuple) -> Optional[int]:
        with self.cache_lock:
            return self.cache.get(key)

    def cache_put(self, key: Tuple, version: int) -> None:
        with self.cache_lock:
            self.cache[key] = version

    def cache_invalidate_docs(self, doc_ids: Iterable[int]) -> None:
        docs = set(doc_ids)
        with self.cache_lock:
            for key in list(self.cache):
                if int(key[0]) in docs:
                    del self.cache[key]


class Experiment:
    def __init__(self, protocol: str, repeat: int, state_dir: Path) -> None:
        self.protocol = protocol
        self.repeat = repeat
        self.corpus = Corpus()
        collection = f"{PREFIX}{protocol}_r{repeat}_{SEED}"
        self.stores = Stores(collection, state_dir / f"{protocol}_r{repeat}.sqlite", self.corpus)
        self.results: List[dict] = []
        self.results_lock = threading.Lock()
        self.store_lock = threading.Lock()
        self.write_pending = threading.Event()
        self.stop = threading.Event()
        self.in_update = threading.Event()
        self.hot_docs: List[int] = list(range(N_DOCS))
        self.hot_lock = threading.Lock()
        self.errors: List[str] = []
        self.errors_lock = threading.Lock()
        self.plan = self._make_plan()
        self.active_versions = {doc_id: 1 for doc_id in range(N_DOCS)}
        self.deleted = set()
        self.update_durations: List[float] = []
        self.ideal_changed_rows = 0

    def _make_plan(self) -> List[List[Tuple[int, str]]]:
        rng = np.random.default_rng(SEED + self.repeat)
        permutation = rng.permutation(N_DOCS)
        plan = []
        for wave in range(N_WAVES):
            docs = permutation[wave * DOCS_PER_WAVE : (wave + 1) * DOCS_PER_WAVE]
            changes = []
            for position, doc_id in enumerate(docs):
                selector = (position + wave + self.repeat) % 10
                kind = "delete" if selector < 2 else "rechunk" if selector < 4 else "modify"
                changes.append((int(doc_id), kind))
            plan.append(changes)
        return plan

    def rows_for_doc(self, doc_id: int, version: int, epoch: int, kind: str) -> List[Tuple[int, int, int, int, str]]:
        if kind == "delete":
            return []
        return [
            (doc_id, version, epoch, chunk_id, text)
            for chunk_id, text in enumerate(self.corpus.chunks(doc_id, version, kind))
        ]

    def initialize(self) -> None:
        self.stores.initialize_manifest()
        rows = []
        for doc_id in range(N_DOCS):
            rows.extend(self.rows_for_doc(doc_id, 1, 0, "initial"))
        self.stores.insert_rows(rows, blue=self.protocol == "blue_green_epoch", dense=True, sparse=True)
        # Initial load is not update amplification.
        self.stores.write_counts.clear()

    def cache_key(self, doc_id: int, version: int, epoch: int) -> Tuple:
        if self.protocol == "naive_eager":
            return (doc_id,)
        if self.protocol == "blue_green_epoch":
            return (doc_id, "epoch", epoch)
        return (doc_id, "version", version)

    def one_query(self, doc_id: int, record: bool = True) -> dict:
        wait_start = time.perf_counter()
        while self.write_pending.is_set():
            time.sleep(0.0002)
        with self.store_lock:
            row = self._one_query_locked(doc_id, record)
        row["latency_ms"] += (time.perf_counter() - wait_start) * 1000.0 - row["latency_ms"]
        return row

    def _one_query_locked(self, doc_id: int, record: bool = True) -> dict:
        start = time.perf_counter()
        version, deleted, epoch = self.stores.read_snapshot(doc_id)
        query = self.corpus.query(doc_id)
        if self.protocol == "naive_eager":
            filter_version = None
            filter_epoch = None
        elif self.protocol == "blue_green_epoch":
            filter_version = None
            filter_epoch = epoch
        else:
            filter_version = version
            filter_epoch = None
        cache_key = self.cache_key(doc_id, version, epoch)
        cache_version = self.stores.cache_get(cache_key)
        dense_version = self.stores.dense_query(doc_id, query, filter_version, filter_epoch)
        sparse_version = self.stores.sparse_query(doc_id, query, filter_version, filter_epoch)
        candidate_for_cache = dense_version if dense_version is not None else sparse_version
        if cache_version is None and candidate_for_cache is not None:
            self.stores.cache_put(cache_key, candidate_for_cache)
            cache_version = candidate_for_cache
        observed = [v for v in (dense_version, sparse_version, cache_version) if v is not None]
        if deleted:
            stale = bool(observed)
            future = False
            missing = False
            mixed = len(set(observed)) > 1
        else:
            stale = any(v < version for v in observed)
            future = any(v > version for v in observed)
            mixed = len(set(observed)) > 1
            missing = version not in observed
        answer_error = stale or future or mixed or missing
        row = {
            "protocol": self.protocol,
            "repeat": self.repeat,
            "doc_id": doc_id,
            "expected_version": version,
            "expected_deleted": int(deleted),
            "expected_epoch": epoch,
            "dense_version": dense_version if dense_version is not None else "",
            "sparse_version": sparse_version if sparse_version is not None else "",
            "cache_version": cache_version if cache_version is not None else "",
            "stale": int(stale),
            "future": int(future),
            "mixed": int(mixed),
            "missing": int(missing),
            "answer_error": int(answer_error),
            "update_window": int(self.in_update.is_set()),
            "latency_ms": (time.perf_counter() - start) * 1000.0,
        }
        if record:
            with self.results_lock:
                self.results.append(row)
        return row

    def phase_call(self, function, *args, **kwargs):
        """Give an update phase priority without hiding inter-phase visibility windows."""
        self.write_pending.set()
        try:
            with self.store_lock:
                return function(*args, **kwargs)
        finally:
            self.write_pending.clear()

    def validate_steady_state(self) -> bool:
        rows = [self.one_query(doc_id, record=False) for doc_id in range(N_DOCS)]
        return all(row["answer_error"] == 0 for row in rows)

    def worker(self, worker_id: int) -> None:
        rng = random.Random(SEED + self.repeat * 100 + worker_id)
        try:
            while not self.stop.is_set():
                with self.hot_lock:
                    hot = list(self.hot_docs)
                if hot and rng.random() < 0.70:
                    doc_id = rng.choice(hot)
                else:
                    doc_id = rng.randrange(N_DOCS)
                self.one_query(doc_id)
                time.sleep(rng.uniform(0.0005, 0.0020))
        except Exception as exc:  # pragma: no cover - recorded in artifact
            with self.errors_lock:
                self.errors.append(f"worker {worker_id}: {type(exc).__name__}: {exc}")
            self.stop.set()

    def delay(self, rng: random.Random) -> None:
        time.sleep(rng.uniform(0.025, 0.045))

    def _changes(self, wave_plan: Sequence[Tuple[int, str]], epoch: int) -> Tuple[List[Tuple[int, int, bool]], List[Tuple[int, int, int, int, str]]]:
        manifest_changes = []
        new_rows = []
        for doc_id, kind in wave_plan:
            version = self.active_versions[doc_id] + 1
            deleted = kind == "delete"
            manifest_changes.append((doc_id, version, deleted))
            rows = self.rows_for_doc(doc_id, version, epoch, kind)
            new_rows.extend(rows)
            self.ideal_changed_rows += len(rows)
        return manifest_changes, new_rows

    def update_naive_or_filter(self, wave: int, wave_plan: Sequence[Tuple[int, str]], rng: random.Random) -> None:
        changes, new_rows = self._changes(wave_plan, wave)
        self.phase_call(self.stores.publish, changes, wave, update_global=False)
        self.delay(rng)
        self.phase_call(self.stores.insert_rows, new_rows, blue=False, dense=True, sparse=False)
        self.delay(rng)
        self.phase_call(self.stores.insert_rows, new_rows, blue=False, dense=False, sparse=True)
        self.delay(rng)
        self.phase_call(self.stores.delete_version, [doc_id for doc_id, _ in wave_plan], version=1)
        self.delay(rng)
        self.phase_call(self.stores.cache_invalidate_docs, [doc_id for doc_id, _ in wave_plan])
        for doc_id, version, deleted in changes:
            self.active_versions[doc_id] = version
            if deleted:
                self.deleted.add(doc_id)

    def update_staged(self, wave: int, wave_plan: Sequence[Tuple[int, str]], rng: random.Random) -> None:
        changes, new_rows = self._changes(wave_plan, wave)
        self.delay(rng)
        self.phase_call(self.stores.insert_rows, new_rows, blue=False, dense=True, sparse=False)
        self.delay(rng)
        self.phase_call(self.stores.insert_rows, new_rows, blue=False, dense=False, sparse=True)
        self.delay(rng)
        self.phase_call(self.stores.publish, changes, wave, update_global=False)
        self.delay(rng)
        for doc_id, version, deleted in changes:
            self.active_versions[doc_id] = version
            if deleted:
                self.deleted.add(doc_id)

    def update_blue(self, wave: int, wave_plan: Sequence[Tuple[int, str]], rng: random.Random) -> None:
        changes, changed_rows = self._changes(wave_plan, wave)
        next_versions = dict(self.active_versions)
        next_deleted = set(self.deleted)
        kind_by_doc = {doc_id: kind for doc_id, kind in wave_plan}
        for doc_id, version, deleted in changes:
            next_versions[doc_id] = version
            if deleted:
                next_deleted.add(doc_id)
        full_rows = []
        for doc_id in range(N_DOCS):
            if doc_id in next_deleted:
                continue
            kind = kind_by_doc.get(doc_id, "initial")
            full_rows.extend(self.rows_for_doc(doc_id, next_versions[doc_id], wave, kind))
        self.delay(rng)
        self.phase_call(self.stores.insert_rows, full_rows, blue=True, dense=True, sparse=False)
        self.delay(rng)
        self.phase_call(self.stores.insert_rows, full_rows, blue=True, dense=False, sparse=True)
        self.delay(rng)
        self.phase_call(self.stores.publish, changes, wave, update_global=True)
        self.delay(rng)
        self.active_versions = next_versions
        self.deleted = next_deleted

    def run(self) -> dict:
        self.initialize()
        steady_ok = self.validate_steady_state()
        threads = [threading.Thread(target=self.worker, args=(i,), daemon=True) for i in range(N_WORKERS)]
        for thread in threads:
            thread.start()
        rng = random.Random(SEED + self.repeat * 1000 + stable_int(self.protocol) % 1000)
        for wave, wave_plan in enumerate(self.plan, start=1):
            if self.stop.is_set():
                break
            with self.hot_lock:
                self.hot_docs = [doc_id for doc_id, _ in wave_plan]
            start = time.perf_counter()
            self.in_update.set()
            if self.protocol in ("naive_eager", "read_version_filter"):
                self.update_naive_or_filter(wave, wave_plan, rng)
            elif self.protocol == "staged_manifest":
                self.update_staged(wave, wave_plan, rng)
            elif self.protocol == "blue_green_epoch":
                self.update_blue(wave, wave_plan, rng)
            else:
                raise ValueError(self.protocol)
            self.in_update.clear()
            self.update_durations.append((time.perf_counter() - start) * 1000.0)
            time.sleep(0.015)
        time.sleep(0.08)
        self.stop.set()
        for thread in threads:
            thread.join(timeout=30)
        update_rows = [row for row in self.results if row["update_window"]]
        all_rows = list(self.results)
        summary = {
            "protocol": self.protocol,
            "repeat": self.repeat,
            "steady_ok": steady_ok,
            "worker_errors": list(self.errors),
            "waves_completed": len(self.update_durations),
            "queries_all": len(all_rows),
            "queries_update": len(update_rows),
            "error_rate_all": statistics.mean(row["answer_error"] for row in all_rows) if all_rows else 1.0,
            "error_rate_update": statistics.mean(row["answer_error"] for row in update_rows) if update_rows else 1.0,
            "stale_rate_update": statistics.mean(row["stale"] for row in update_rows) if update_rows else 1.0,
            "mixed_rate_update": statistics.mean(row["mixed"] for row in update_rows) if update_rows else 1.0,
            "missing_rate_update": statistics.mean(row["missing"] for row in update_rows) if update_rows else 1.0,
            "p50_latency_ms_update": percentile([row["latency_ms"] for row in update_rows], 0.50),
            "p95_latency_ms_update": percentile([row["latency_ms"] for row in update_rows], 0.95),
            "p95_update_wave_ms": percentile(self.update_durations, 0.95),
            "ideal_changed_rows": self.ideal_changed_rows,
            "dense_rows_written": self.stores.write_counts["dense_rows"],
            "sparse_rows_written": self.stores.write_counts["sparse_rows"],
            "manifest_rows_written": self.stores.write_counts["manifest_rows"],
        }
        summary["write_amplification"] = (
            (summary["dense_rows_written"] + summary["sparse_rows_written"])
            / max(1, 2 * summary["ideal_changed_rows"])
        )
        return summary


def aggregate(repeat_summaries: Sequence[dict], raw_rows: Sequence[dict]) -> dict:
    out = {}
    for protocol in PROTOCOLS:
        summaries = [row for row in repeat_summaries if row["protocol"] == protocol]
        rows = [row for row in raw_rows if row["protocol"] == protocol and row["update_window"]]
        errors = sum(int(row["answer_error"]) for row in rows)
        missing = sum(int(row["missing"]) for row in rows)
        stale = sum(int(row["stale"]) for row in rows)
        mixed = sum(int(row["mixed"]) for row in rows)
        ci = wilson_interval(errors, len(rows))
        out[protocol] = {
            "repeats": len(summaries),
            "steady_all_ok": all(row["steady_ok"] for row in summaries),
            "worker_errors": [error for row in summaries for error in row["worker_errors"]],
            "waves_completed": sum(row["waves_completed"] for row in summaries),
            "update_queries": len(rows),
            "error_count": errors,
            "answer_error_rate": errors / len(rows) if rows else 1.0,
            "answer_error_wilson_95ci": list(ci),
            "stale_rate": stale / len(rows) if rows else 1.0,
            "mixed_rate": mixed / len(rows) if rows else 1.0,
            "missing_rate": missing / len(rows) if rows else 1.0,
            "p50_latency_ms": percentile([float(row["latency_ms"]) for row in rows], 0.50),
            "p95_latency_ms": percentile([float(row["latency_ms"]) for row in rows], 0.95),
            "mean_write_amplification": statistics.mean(row["write_amplification"] for row in summaries),
            "repeat_error_rates": [row["error_rate_update"] for row in summaries],
            "repeats_at_or_above_5pct": sum(row["error_rate_update"] >= 0.05 for row in summaries),
        }
    return out


def decide(agg: dict, repeat_summaries: Sequence[dict]) -> Tuple[dict, str]:
    naive = agg["naive_eager"]
    vf = agg["read_version_filter"]
    blue = agg["blue_green_epoch"]
    staged = agg["staged_manifest"]
    g0 = all(
        values["steady_all_ok"]
        and not values["worker_errors"]
        and values["update_queries"] >= 300
        for values in agg.values()
    ) and all(row["waves_completed"] == N_WAVES for row in repeat_summaries)
    g1 = naive["repeats_at_or_above_5pct"] >= 4 and naive["answer_error_wilson_95ci"][0] > 0.01
    vf_overhead = vf["p95_latency_ms"] / naive["p95_latency_ms"] - 1.0
    g2 = vf["answer_error_rate"] <= 0.01 and vf["missing_rate"] <= 0.01 and vf_overhead <= 0.15
    staged_overhead = staged["p95_latency_ms"] / naive["p95_latency_ms"] - 1.0
    g3 = (
        staged["answer_error_rate"] <= 0.01
        and staged["answer_error_wilson_95ci"][1] <= 0.02
        and staged_overhead <= 0.15
        and vf["missing_rate"] - staged["missing_rate"] >= 0.05
    )
    write_ratio = blue["mean_write_amplification"] / max(staged["mean_write_amplification"], 1e-12)
    g4 = (
        write_ratio >= 5.0
        and blue["answer_error_rate"] <= 0.01
        and staged["answer_error_rate"] <= 0.01
    )
    gates = {
        "G0_harness": g0,
        "G1_reproducible_failure": g1,
        "G2_simple_filter_sufficient": g2,
        "G3_staged_manifest_effective": g3,
        "G4_blue_green_system_value": g4,
        "read_filter_p95_overhead": vf_overhead,
        "staged_p95_overhead": staged_overhead,
        "blue_to_staged_write_amp_ratio": write_ratio,
    }
    if not g0:
        decision = "DATA_OR_HARNESS_FAILURE"
    elif not g1:
        decision = "STOP_NO_REPRODUCIBLE_FAILURE"
    elif g2:
        decision = "STOP_SIMPLE_FILTER_SUFFICIENT"
    elif not (g3 and g4):
        decision = "STOP_STAGING_NOT_EFFECTIVE"
    else:
        decision = "CONDITIONAL_GO_REAL_REVISION_CROSS_ENGINE"
    return gates, decision


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    state_dir = output_dir / "state"
    state_dir.mkdir(parents=True, exist_ok=True)
    repeat_summaries = []
    raw_rows = []
    start = time.perf_counter()
    for protocol in PROTOCOLS:
        for repeat in range(N_REPEATS):
            experiment = Experiment(protocol, repeat, state_dir)
            summary = experiment.run()
            repeat_summaries.append(summary)
            raw_rows.extend(experiment.results)
            print(json.dumps({"protocol": protocol, "repeat": repeat, "error": summary["error_rate_update"]}))
    agg = aggregate(repeat_summaries, raw_rows)
    gates, decision = decide(agg, repeat_summaries)
    aggregate_result = {
        "protocol": {
            "seed": SEED,
            "documents": N_DOCS,
            "waves": N_WAVES,
            "docs_per_wave": DOCS_PER_WAVE,
            "repeats": N_REPEATS,
            "query_workers": N_WORKERS,
            "vector_size": VECTOR_SIZE,
            "runtime_seconds": time.perf_counter() - start,
        },
        "aggregate": agg,
        "gates": gates,
        "decision": decision,
    }
    fieldnames = list(raw_rows[0].keys())
    with (output_dir / "query_events.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(raw_rows)
    with (output_dir / "repeat_summary.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(repeat_summaries[0].keys()))
        writer.writeheader()
        writer.writerows(repeat_summaries)
    with (output_dir / "aggregate.json").open("w", encoding="utf-8") as handle:
        json.dump(aggregate_result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    report = [
        "# FreshEvidenceDB P0 자동 보고",
        "",
        f"- 판정: **{decision}**",
        f"- 게이트: `{json.dumps(gates, sort_keys=True)}`",
        "",
        "| protocol | update queries | error | stale | mixed | missing | p95 ms | write amp |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for protocol in PROTOCOLS:
        row = agg[protocol]
        report.append(
            f"| {protocol} | {row['update_queries']} | {row['answer_error_rate']:.4f} | "
            f"{row['stale_rate']:.4f} | {row['mixed_rate']:.4f} | {row['missing_rate']:.4f} | "
            f"{row['p95_latency_ms']:.2f} | {row['mean_write_amplification']:.2f} |"
        )
    report.extend(["", "상세 결과는 `aggregate.json`, 질의 이벤트는 `query_events.csv`에 있다.", ""])
    (output_dir / "AUTO_REPORT.md").write_text("\n".join(report), encoding="utf-8")
    print(json.dumps({"decision": decision, "gates": gates}, sort_keys=True))


if __name__ == "__main__":
    main()
