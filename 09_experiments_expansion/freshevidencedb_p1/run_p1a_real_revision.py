#!/usr/bin/env python3
"""FreshEvidenceDB P1-A: real revisions, Qdrant/PostgreSQL, and native MVCC."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
import statistics
import subprocess
import threading
import time
import uuid
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Sequence

import numpy as np
import psycopg
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import HashingVectorizer

from build_revision_pairs import chunks, normalize, sha256_text


SEED = 20260807
VECTOR_SIZE = 384
N_REPEATS = 3
N_WORKERS = 8
DOCS_PER_WAVE = 10
N_WAVES = 10
TOP_K = 8
PREFIX = "freshevidencedb_p1a_"
PG_SCHEMA = "fresh_p1a"
PG_DSN = "host=127.0.0.1 port=5433 dbname=vlmdb user=vlmdb password=vlmdb"
PROTOCOLS = (
    "cross_naive",
    "cross_read_filter",
    "cross_staged",
    "cross_blue_green",
    "pg_atomic",
)


def stable_int(text: str) -> int:
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def percentile(values: Sequence[float], q: float) -> float:
    return float(np.quantile(np.asarray(values, dtype=np.float64), q)) if values else float("nan")


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if total == 0:
        return (0.0, 1.0)
    p = successes / total
    denom = 1.0 + z * z / total
    center = (p + z * z / (2 * total)) / denom
    half = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denom
    return max(0.0, center - half), min(1.0, center + half)


def vector_literal(vector: np.ndarray) -> str:
    return "[" + ",".join(f"{float(value):.8g}" for value in vector) + "]"


def git_show(repo: Path, revision: str, path: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo), "show", f"{revision}:{path}"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return normalize(proc.stdout.decode("utf-8", errors="strict"))


@dataclass(frozen=True)
class RevisionDoc:
    doc_id: int
    probe: str
    commit: str
    parent: str
    path: str
    old_chunks: tuple[str, ...]
    new_chunks: tuple[str, ...]


class Corpus:
    def __init__(self, manifest_path: Path) -> None:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.vectorizer = HashingVectorizer(
            n_features=VECTOR_SIZE,
            alternate_sign=False,
            norm="l2",
            analyzer="word",
            ngram_range=(1, 2),
        )
        self.domains: dict[str, list[RevisionDoc]] = {}
        for domain, data in payload["domains"].items():
            repo = Path(data["repo_path"])
            docs = []
            for pair in data["pairs"]:
                old_text = git_show(repo, pair["parent"], pair["path"])
                new_text = git_show(repo, pair["commit"], pair["path"])
                if sha256_text(old_text) != pair["old_sha256"] or sha256_text(new_text) != pair["new_sha256"]:
                    raise RuntimeError(f"revision content drift: {domain} {pair['commit']} {pair['path']}")
                old_chunks = tuple(chunks(old_text))
                new_chunks = tuple(chunks(new_text))
                if len(old_chunks) != pair["old_chunks"] or len(new_chunks) != pair["new_chunks"]:
                    raise RuntimeError(f"chunk drift: {domain} {pair['commit']} {pair['path']}")
                docs.append(
                    RevisionDoc(
                        doc_id=int(pair["doc_id"]),
                        probe=pair["probe"],
                        commit=pair["commit"],
                        parent=pair["parent"],
                        path=pair["path"],
                        old_chunks=old_chunks,
                        new_chunks=new_chunks,
                    )
                )
            if len(docs) != 100:
                raise RuntimeError(f"{domain}: expected 100 docs, got {len(docs)}")
            self.domains[domain] = docs

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        return self.vectorizer.transform(texts).astype(np.float32).toarray()

    @staticmethod
    def indexed_text(doc: RevisionDoc, text: str) -> str:
        return f"{doc.probe} {text}"

    def rows(self, doc: RevisionDoc, version: int, epoch: int) -> list[tuple[int, int, int, int, str, str]]:
        source = doc.old_chunks if version == 1 else doc.new_chunks
        return [
            (doc.doc_id, version, epoch, chunk_id, text, doc.probe)
            for chunk_id, text in enumerate(source)
        ]


class Stores:
    def __init__(self, run_key: str, protocol: str, corpus: Corpus) -> None:
        if not re.fullmatch(r"[a-z0-9_]+", run_key):
            raise ValueError(run_key)
        self.run_key = run_key
        self.protocol = protocol
        self.corpus = corpus
        self.collection = f"{PREFIX}{run_key}_{SEED}"
        if not self.collection.startswith(PREFIX):
            raise ValueError(self.collection)
        self.manifest_table = f"{run_key}_manifest"
        self.artifact_table = f"{run_key}_artifacts"
        self.global_table = f"{run_key}_global"
        self.write_counts = Counter()
        self.readiness_ok = True
        self.local = threading.local()
        self.qdrant = QdrantClient(url="http://127.0.0.1:6333", timeout=60)
        self.pg = psycopg.connect(PG_DSN, autocommit=True)
        self._initialize_storage()

    @property
    def q_manifest(self) -> str:
        return f"{PG_SCHEMA}.{self.manifest_table}"

    @property
    def q_artifact(self) -> str:
        return f"{PG_SCHEMA}.{self.artifact_table}"

    @property
    def q_global(self) -> str:
        return f"{PG_SCHEMA}.{self.global_table}"

    def _initialize_storage(self) -> None:
        with self.pg.cursor() as cur:
            cur.execute("CREATE SCHEMA IF NOT EXISTS fresh_p1a")
            for table in (self.artifact_table, self.manifest_table, self.global_table):
                cur.execute(f"DROP TABLE IF EXISTS {PG_SCHEMA}.{table}")
            cur.execute(
                f"""
                CREATE TABLE {self.q_manifest}(
                    doc_id INTEGER PRIMARY KEY,
                    active_version INTEGER NOT NULL,
                    deleted BOOLEAN NOT NULL DEFAULT FALSE,
                    epoch INTEGER NOT NULL
                )
                """
            )
            cur.execute(
                f"""
                CREATE TABLE {self.q_global}(
                    id INTEGER PRIMARY KEY CHECK(id=1),
                    active_epoch INTEGER NOT NULL
                )
                """
            )
            cur.execute(f"INSERT INTO {self.q_global}(id,active_epoch) VALUES(1,0)")
            cur.execute(
                f"""
                CREATE TABLE {self.q_artifact}(
                    doc_id INTEGER NOT NULL,
                    version INTEGER NOT NULL,
                    epoch INTEGER NOT NULL,
                    chunk_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    probe TEXT NOT NULL,
                    embedding vector({VECTOR_SIZE}),
                    search tsvector GENERATED ALWAYS AS
                        (to_tsvector('simple', probe || ' ' || text)) STORED,
                    PRIMARY KEY(doc_id,version,epoch,chunk_id)
                )
                """
            )
            cur.execute(f"CREATE INDEX {self.artifact_table}_lookup ON {self.q_artifact}(doc_id,version,epoch)")
            cur.execute(f"CREATE INDEX {self.artifact_table}_search ON {self.q_artifact} USING GIN(search)")
        if self.protocol != "pg_atomic":
            existing = {item.name for item in self.qdrant.get_collections().collections}
            if self.collection in existing:
                self.qdrant.delete_collection(self.collection)
            self.qdrant.create_collection(
                collection_name=self.collection,
                vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
            )
            for field in ("doc_id", "version", "epoch"):
                self.qdrant.create_payload_index(
                    collection_name=self.collection,
                    field_name=field,
                    field_schema=models.PayloadSchemaType.INTEGER,
                    wait=True,
                )

    def worker_pg(self) -> psycopg.Connection:
        conn = getattr(self.local, "pg", None)
        if conn is None or conn.closed:
            conn = psycopg.connect(PG_DSN, autocommit=True)
            self.local.pg = conn
        return conn

    def worker_qdrant(self) -> QdrantClient:
        client = getattr(self.local, "qdrant", None)
        if client is None:
            client = QdrantClient(url="http://127.0.0.1:6333", timeout=60)
            self.local.qdrant = client
        return client

    def close_worker_clients(self) -> None:
        conn = getattr(self.local, "pg", None)
        if conn is not None and not conn.closed:
            conn.close()
        client = getattr(self.local, "qdrant", None)
        if client is not None:
            client.close()

    def close(self) -> None:
        self.pg.close()
        self.qdrant.close()

    def initialize_manifest(self, docs: Sequence[RevisionDoc]) -> None:
        with self.pg.transaction():
            with self.pg.cursor() as cur:
                cur.executemany(
                    f"INSERT INTO {self.q_manifest}(doc_id,active_version,deleted,epoch) VALUES(%s,1,FALSE,0)",
                    [(doc.doc_id,) for doc in docs],
                )

    @staticmethod
    def point_id(run_key: str, row: tuple[int, int, int, int, str, str]) -> str:
        doc_id, version, epoch, chunk_id, _, _ = row
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{run_key}:{doc_id}:{version}:{epoch}:{chunk_id}"))

    def insert_qdrant(self, rows: Sequence[tuple[int, int, int, int, str, str]], *, count: bool = True) -> None:
        if not rows:
            return
        indexed = [f"{probe} {text}" for _, _, _, _, text, probe in rows]
        vectors = self.corpus.embed(indexed)
        for start in range(0, len(rows), 256):
            batch_rows = rows[start : start + 256]
            batch_vectors = vectors[start : start + 256]
            points = []
            for row, vector in zip(batch_rows, batch_vectors):
                doc_id, version, epoch, chunk_id, text, probe = row
                points.append(
                    models.PointStruct(
                        id=self.point_id(self.run_key, row),
                        vector=vector.tolist(),
                        payload={
                            "doc_id": doc_id,
                            "version": version,
                            "epoch": epoch,
                            "chunk_id": chunk_id,
                            "probe": probe,
                            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                        },
                    )
                )
            self.qdrant.upsert(self.collection, points=points, wait=True)
        if count:
            self.write_counts["dense_rows"] += len(rows)
            self.write_counts["physical_rows"] += len(rows)

    def insert_postgres(
        self,
        rows: Sequence[tuple[int, int, int, int, str, str]],
        *,
        include_vector: bool,
        connection: Optional[psycopg.Connection] = None,
        count: bool = True,
    ) -> None:
        if not rows:
            return
        conn = connection or self.pg
        vector_values = self.corpus.embed([f"{probe} {text}" for _, _, _, _, text, probe in rows]) if include_vector else None
        values = []
        for index, row in enumerate(rows):
            doc_id, version, epoch, chunk_id, text, probe = row
            embedding = vector_literal(vector_values[index]) if vector_values is not None else None
            values.append((doc_id, version, epoch, chunk_id, text, probe, embedding))
        with conn.cursor() as cur:
            cur.executemany(
                f"""
                INSERT INTO {self.q_artifact}(doc_id,version,epoch,chunk_id,text,probe,embedding)
                VALUES(%s,%s,%s,%s,%s,%s,%s::vector)
                ON CONFLICT(doc_id,version,epoch,chunk_id) DO UPDATE SET
                    text=EXCLUDED.text, probe=EXCLUDED.probe, embedding=EXCLUDED.embedding
                """,
                values,
            )
        if count:
            self.write_counts["sparse_rows"] += len(rows)
            if include_vector:
                self.write_counts["dense_rows"] += len(rows)
            self.write_counts["physical_rows"] += len(rows)

    def publish(self, changes: Sequence[tuple[int, int]], epoch: int, *, update_global: bool = False) -> None:
        with self.pg.transaction():
            with self.pg.cursor() as cur:
                cur.executemany(
                    f"UPDATE {self.q_manifest} SET active_version=%s,epoch=%s WHERE doc_id=%s",
                    [(version, epoch, doc_id) for doc_id, version in changes],
                )
                if update_global:
                    cur.execute(f"UPDATE {self.q_global} SET active_epoch=%s WHERE id=1", (epoch,))
        self.write_counts["manifest_rows"] += len(changes) + int(update_global)

    def delete_qdrant(self, doc_ids: Sequence[int], version: int) -> None:
        filt = models.Filter(
            must=[
                models.FieldCondition(key="doc_id", match=models.MatchAny(any=list(doc_ids))),
                models.FieldCondition(key="version", match=models.MatchValue(value=version)),
            ]
        )
        self.qdrant.delete(self.collection, points_selector=models.FilterSelector(filter=filt), wait=True)

    def delete_postgres(self, doc_ids: Sequence[int], version: int, *, connection: Optional[psycopg.Connection] = None) -> None:
        conn = connection or self.pg
        with conn.cursor() as cur:
            cur.execute(f"DELETE FROM {self.q_artifact} WHERE doc_id = ANY(%s) AND version=%s", (list(doc_ids), version))

    def read_manifest(self, doc_id: int, *, connection: Optional[psycopg.Connection] = None) -> tuple[int, bool, int]:
        conn = connection or self.worker_pg()
        with conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT m.active_version,m.deleted,g.active_epoch
                FROM {self.q_manifest} m CROSS JOIN {self.q_global} g
                WHERE m.doc_id=%s AND g.id=1
                """,
                (doc_id,),
            )
            row = cur.fetchone()
        return int(row[0]), bool(row[1]), int(row[2])

    def qdrant_versions(
        self,
        doc: RevisionDoc,
        version: Optional[int],
        epoch: Optional[int],
    ) -> set[int]:
        must = [models.FieldCondition(key="doc_id", match=models.MatchValue(value=doc.doc_id))]
        if version is not None:
            must.append(models.FieldCondition(key="version", match=models.MatchValue(value=version)))
        if epoch is not None:
            must.append(models.FieldCondition(key="epoch", match=models.MatchValue(value=epoch)))
        query = self.corpus.embed([doc.probe])[0]
        response = self.worker_qdrant().query_points(
            collection_name=self.collection,
            query=query,
            query_filter=models.Filter(must=must),
            search_params=models.SearchParams(exact=True),
            limit=TOP_K,
            with_payload=True,
        )
        return {int(point.payload["version"]) for point in response.points}

    def postgres_sparse_versions(
        self,
        doc: RevisionDoc,
        version: Optional[int],
        epoch: Optional[int],
        *,
        connection: Optional[psycopg.Connection] = None,
    ) -> set[int]:
        conn = connection or self.worker_pg()
        sql = f"SELECT version FROM {self.q_artifact} WHERE doc_id=%s AND search @@ plainto_tsquery('simple',%s)"
        params: list[object] = [doc.doc_id, doc.probe]
        if version is not None:
            sql += " AND version=%s"
            params.append(version)
        if epoch is not None:
            sql += " AND epoch=%s"
            params.append(epoch)
        sql += " ORDER BY ts_rank(search,plainto_tsquery('simple',%s)) DESC, version ASC, chunk_id ASC LIMIT %s"
        params.extend([doc.probe, TOP_K])
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return {int(row[0]) for row in cur.fetchall()}

    def postgres_dense_versions(self, doc: RevisionDoc, connection: psycopg.Connection) -> set[int]:
        query = vector_literal(self.corpus.embed([doc.probe])[0])
        with connection.cursor() as cur:
            cur.execute(
                f"""
                SELECT version FROM {self.q_artifact}
                WHERE doc_id=%s AND embedding IS NOT NULL
                ORDER BY embedding <=> %s::vector, version ASC, chunk_id ASC
                LIMIT %s
                """,
                (doc.doc_id, query, TOP_K),
            )
            return {int(row[0]) for row in cur.fetchall()}

    def readiness(self, docs: Sequence[RevisionDoc], version: int, epoch: int) -> bool:
        ids = [doc.doc_id for doc in docs]
        expected = sum(len(doc.new_chunks if version == 2 else doc.old_chunks) for doc in docs)
        filt = models.Filter(
            must=[
                models.FieldCondition(key="doc_id", match=models.MatchAny(any=ids)),
                models.FieldCondition(key="version", match=models.MatchValue(value=version)),
                models.FieldCondition(key="epoch", match=models.MatchValue(value=epoch)),
            ]
        )
        dense_count = self.qdrant.count(self.collection, count_filter=filt, exact=True).count
        with self.pg.cursor() as cur:
            cur.execute(
                f"SELECT count(*) FROM {self.q_artifact} WHERE doc_id = ANY(%s) AND version=%s AND epoch=%s",
                (ids, version, epoch),
            )
            sparse_count = int(cur.fetchone()[0])
        ok = dense_count == expected and sparse_count == expected
        self.readiness_ok = self.readiness_ok and ok
        return ok

    def atomic_update(self, docs: Sequence[RevisionDoc], epoch: int) -> None:
        rows = [row for doc in docs for row in self.corpus.rows(doc, 2, epoch)]
        ids = [doc.doc_id for doc in docs]
        with self.pg.transaction():
            self.insert_postgres(rows, include_vector=True, connection=self.pg)
            with self.pg.cursor() as cur:
                cur.executemany(
                    f"UPDATE {self.q_manifest} SET active_version=2,epoch=%s WHERE doc_id=%s",
                    [(epoch, doc_id) for doc_id in ids],
                )
                cur.execute(f"DELETE FROM {self.q_artifact} WHERE doc_id = ANY(%s) AND version=1", (ids,))
        self.write_counts["manifest_rows"] += len(ids)


class Experiment:
    def __init__(self, corpus: Corpus, domain: str, protocol: str, repeat: int) -> None:
        self.corpus = corpus
        self.domain = domain
        self.protocol = protocol
        self.repeat = repeat
        self.docs = corpus.domains[domain]
        self.run_key = f"{domain}_{protocol}_r{repeat}"
        self.stores = Stores(self.run_key, protocol, corpus)
        self.results: list[dict] = []
        self.results_lock = threading.Lock()
        self.hot_lock = threading.Lock()
        self.hot_docs = list(self.docs)
        self.in_update = threading.Event()
        self.stop = threading.Event()
        self.errors: list[str] = []
        self.errors_lock = threading.Lock()
        self.wave_durations: list[float] = []
        self.ideal_changed_rows = 0
        self.waves_completed = 0
        self.active_versions = {doc.doc_id: 1 for doc in self.docs}

    def initial_rows(self) -> list[tuple[int, int, int, int, str, str]]:
        return [row for doc in self.docs for row in self.corpus.rows(doc, 1, 0)]

    def initialize(self) -> None:
        self.stores.initialize_manifest(self.docs)
        rows = self.initial_rows()
        if self.protocol == "pg_atomic":
            with self.stores.pg.transaction():
                self.stores.insert_postgres(rows, include_vector=True, connection=self.stores.pg, count=False)
        else:
            self.stores.insert_qdrant(rows, count=False)
            with self.stores.pg.transaction():
                self.stores.insert_postgres(rows, include_vector=False, connection=self.stores.pg, count=False)
        self.stores.write_counts.clear()

    def one_query(self, doc: RevisionDoc, *, record: bool = True) -> dict:
        start = time.perf_counter()
        if self.protocol == "pg_atomic":
            conn = self.stores.worker_pg()
            conn.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
            try:
                expected, deleted, epoch = self.stores.read_manifest(doc.doc_id, connection=conn)
                dense = self.stores.postgres_dense_versions(doc, conn)
                sparse = self.stores.postgres_sparse_versions(doc, None, None, connection=conn)
                conn.execute("COMMIT")
            except Exception:
                conn.execute("ROLLBACK")
                raise
        else:
            expected, deleted, epoch = self.stores.read_manifest(doc.doc_id)
            if self.protocol == "cross_naive":
                filter_version, filter_epoch = None, None
            elif self.protocol == "cross_blue_green":
                filter_version, filter_epoch = None, epoch
            else:
                filter_version, filter_epoch = expected, None
            dense = self.stores.qdrant_versions(doc, filter_version, filter_epoch)
            sparse = self.stores.postgres_sparse_versions(doc, filter_version, filter_epoch)
        observed = dense | sparse
        stale = bool(observed) if deleted else any(version < expected for version in observed)
        future = False if deleted else any(version > expected for version in observed)
        mixed = len(observed) > 1
        missing = False if deleted else expected not in dense or expected not in sparse
        error = stale or future or mixed or missing
        row = {
            "domain": self.domain,
            "protocol": self.protocol,
            "repeat": self.repeat,
            "doc_id": doc.doc_id,
            "commit": doc.commit,
            "path": doc.path,
            "expected_version": expected,
            "expected_epoch": epoch,
            "dense_versions": ";".join(map(str, sorted(dense))),
            "sparse_versions": ";".join(map(str, sorted(sparse))),
            "stale": int(stale),
            "future": int(future),
            "mixed": int(mixed),
            "missing": int(missing),
            "answer_error": int(error),
            "update_window": int(self.in_update.is_set()),
            "latency_ms": (time.perf_counter() - start) * 1000.0,
        }
        if record:
            with self.results_lock:
                self.results.append(row)
        return row

    def validate_steady(self) -> bool:
        return all(self.one_query(doc, record=False)["answer_error"] == 0 for doc in self.docs)

    def worker(self, worker_id: int) -> None:
        rng = random.Random(SEED + stable_int(self.run_key) % 100_000 + worker_id)
        try:
            while not self.stop.is_set():
                with self.hot_lock:
                    hot = list(self.hot_docs)
                doc = rng.choice(hot if hot and rng.random() < 0.80 else self.docs)
                self.one_query(doc)
                time.sleep(rng.uniform(0.0005, 0.0015))
        except Exception as exc:
            with self.errors_lock:
                self.errors.append(f"worker {worker_id}: {type(exc).__name__}: {exc}")
            self.stop.set()
        finally:
            self.stores.close_worker_clients()

    def changed_rows(self, docs: Sequence[RevisionDoc], epoch: int) -> list[tuple[int, int, int, int, str, str]]:
        rows = [row for doc in docs for row in self.corpus.rows(doc, 2, epoch)]
        self.ideal_changed_rows += len(rows)
        return rows

    def update_cross_naive_or_filter(self, docs: Sequence[RevisionDoc], epoch: int) -> None:
        changes = [(doc.doc_id, 2) for doc in docs]
        rows = self.changed_rows(docs, 0)
        self.stores.publish(changes, epoch)
        self.stores.insert_qdrant(rows)
        with self.stores.pg.transaction():
            self.stores.insert_postgres(rows, include_vector=False, connection=self.stores.pg)
        ids = [doc.doc_id for doc in docs]
        self.stores.delete_qdrant(ids, 1)
        with self.stores.pg.transaction():
            self.stores.delete_postgres(ids, 1, connection=self.stores.pg)

    def update_staged(self, docs: Sequence[RevisionDoc], epoch: int) -> None:
        rows = self.changed_rows(docs, 0)
        self.stores.insert_qdrant(rows)
        with self.stores.pg.transaction():
            self.stores.insert_postgres(rows, include_vector=False, connection=self.stores.pg)
        if not self.stores.readiness(docs, 2, 0):
            raise RuntimeError(f"readiness failed: {self.domain} wave {epoch}")
        self.stores.publish([(doc.doc_id, 2) for doc in docs], epoch)

    def update_blue(self, docs: Sequence[RevisionDoc], epoch: int) -> None:
        changed_ids = {doc.doc_id for doc in docs}
        for doc in docs:
            self.active_versions[doc.doc_id] = 2
        self.ideal_changed_rows += sum(len(doc.new_chunks) for doc in docs)
        rows = []
        for doc in self.docs:
            version = self.active_versions[doc.doc_id]
            rows.extend(self.corpus.rows(doc, version, epoch))
        self.stores.insert_qdrant(rows)
        with self.stores.pg.transaction():
            self.stores.insert_postgres(rows, include_vector=False, connection=self.stores.pg)
        self.stores.publish([(doc_id, 2) for doc_id in sorted(changed_ids)], epoch, update_global=True)

    def update_pg_atomic(self, docs: Sequence[RevisionDoc], epoch: int) -> None:
        self.ideal_changed_rows += sum(len(doc.new_chunks) for doc in docs)
        self.stores.atomic_update(docs, epoch)

    def run(self) -> dict:
        self.initialize()
        steady_ok = self.validate_steady()
        threads = [threading.Thread(target=self.worker, args=(worker,), daemon=True) for worker in range(N_WORKERS)]
        for thread in threads:
            thread.start()
        for wave in range(N_WAVES):
            if self.stop.is_set():
                break
            docs = self.docs[wave * DOCS_PER_WAVE : (wave + 1) * DOCS_PER_WAVE]
            with self.hot_lock:
                self.hot_docs = list(docs)
            self.in_update.set()
            start = time.perf_counter()
            try:
                if self.protocol in ("cross_naive", "cross_read_filter"):
                    self.update_cross_naive_or_filter(docs, wave + 1)
                elif self.protocol == "cross_staged":
                    self.update_staged(docs, wave + 1)
                elif self.protocol == "cross_blue_green":
                    self.update_blue(docs, wave + 1)
                elif self.protocol == "pg_atomic":
                    self.update_pg_atomic(docs, wave + 1)
                else:
                    raise ValueError(self.protocol)
                self.waves_completed += 1
            except Exception as exc:
                with self.errors_lock:
                    self.errors.append(f"writer: {type(exc).__name__}: {exc}")
                self.stop.set()
            finally:
                self.wave_durations.append((time.perf_counter() - start) * 1000.0)
                self.in_update.clear()
            time.sleep(0.005)
        time.sleep(0.03)
        self.stop.set()
        for thread in threads:
            thread.join(timeout=30)
        update_rows = [row for row in self.results if row["update_window"]]
        summary = {
            "domain": self.domain,
            "protocol": self.protocol,
            "repeat": self.repeat,
            "steady_ok": steady_ok,
            "readiness_ok": self.stores.readiness_ok,
            "worker_errors": list(self.errors),
            "waves_completed": self.waves_completed,
            "queries_all": len(self.results),
            "queries_update": len(update_rows),
            "error_rate_update": statistics.mean(row["answer_error"] for row in update_rows) if update_rows else 1.0,
            "stale_rate_update": statistics.mean(row["stale"] for row in update_rows) if update_rows else 1.0,
            "mixed_rate_update": statistics.mean(row["mixed"] for row in update_rows) if update_rows else 1.0,
            "missing_rate_update": statistics.mean(row["missing"] for row in update_rows) if update_rows else 1.0,
            "p50_latency_ms_update": percentile([row["latency_ms"] for row in update_rows], 0.50),
            "p95_latency_ms_update": percentile([row["latency_ms"] for row in update_rows], 0.95),
            "p99_latency_ms_update": percentile([row["latency_ms"] for row in update_rows], 0.99),
            "p50_wave_ms": percentile(self.wave_durations, 0.50),
            "p95_wave_ms": percentile(self.wave_durations, 0.95),
            "ideal_changed_rows": self.ideal_changed_rows,
            "dense_rows_written": self.stores.write_counts["dense_rows"],
            "sparse_rows_written": self.stores.write_counts["sparse_rows"],
            "physical_rows_written": self.stores.write_counts["physical_rows"],
            "manifest_rows_written": self.stores.write_counts["manifest_rows"],
        }
        summary["write_amplification"] = (
            (summary["dense_rows_written"] + summary["sparse_rows_written"])
            / max(1, 2 * summary["ideal_changed_rows"])
        )
        self.stores.close()
        return summary


def aggregate(repeat_rows: Sequence[dict], events: Sequence[dict]) -> dict:
    output: dict[str, dict[str, dict]] = {}
    for domain in sorted({row["domain"] for row in repeat_rows}):
        output[domain] = {}
        for protocol in PROTOCOLS:
            summaries = [row for row in repeat_rows if row["domain"] == domain and row["protocol"] == protocol]
            rows = [
                row for row in events
                if row["domain"] == domain and row["protocol"] == protocol and row["update_window"]
            ]
            errors = sum(int(row["answer_error"]) for row in rows)
            output[domain][protocol] = {
                "repeats": len(summaries),
                "steady_all_ok": all(row["steady_ok"] for row in summaries),
                "readiness_all_ok": all(row["readiness_ok"] for row in summaries),
                "worker_errors": [error for summary in summaries for error in summary["worker_errors"]],
                "waves_completed": sum(row["waves_completed"] for row in summaries),
                "update_queries": len(rows),
                "error_count": errors,
                "answer_error_rate": errors / len(rows) if rows else 1.0,
                "answer_error_wilson_95ci": list(wilson_interval(errors, len(rows))),
                "stale_rate": sum(int(row["stale"]) for row in rows) / len(rows) if rows else 1.0,
                "mixed_rate": sum(int(row["mixed"]) for row in rows) / len(rows) if rows else 1.0,
                "missing_rate": sum(int(row["missing"]) for row in rows) / len(rows) if rows else 1.0,
                "p50_latency_ms": percentile([float(row["latency_ms"]) for row in rows], 0.50),
                "p95_latency_ms": percentile([float(row["latency_ms"]) for row in rows], 0.95),
                "p99_latency_ms": percentile([float(row["latency_ms"]) for row in rows], 0.99),
                "mean_write_amplification": statistics.mean(row["write_amplification"] for row in summaries),
                "mean_physical_rows": statistics.mean(row["physical_rows_written"] for row in summaries),
                "repeat_error_rates": [row["error_rate_update"] for row in summaries],
                "repeats_at_or_above_1pct": sum(row["error_rate_update"] >= 0.01 for row in summaries),
            }
    return output


def decide(agg: dict, repeat_rows: Sequence[dict]) -> tuple[dict, str]:
    domains = sorted(agg)
    g0 = all(
        agg[domain][protocol]["steady_all_ok"]
        and agg[domain][protocol]["readiness_all_ok"]
        and not agg[domain][protocol]["worker_errors"]
        and agg[domain][protocol]["update_queries"] >= 500
        and agg[domain][protocol]["waves_completed"] == N_REPEATS * N_WAVES
        for domain in domains
        for protocol in PROTOCOLS
    )
    g1 = all(
        agg[domain]["cross_naive"]["repeats_at_or_above_1pct"] >= 2
        and agg[domain]["cross_naive"]["answer_error_wilson_95ci"][0] > 0.001
        for domain in domains
    )
    filter_details = {}
    g2_parts = []
    for domain in domains:
        naive = agg[domain]["cross_naive"]
        filtered = agg[domain]["cross_read_filter"]
        overhead = filtered["p95_latency_ms"] / naive["p95_latency_ms"] - 1.0
        filter_details[domain] = overhead
        g2_parts.append(
            filtered["answer_error_rate"] <= 0.01
            and filtered["missing_rate"] <= 0.01
            and overhead <= 0.15
        )
    g2 = all(g2_parts)
    staged_details = {}
    g3_parts = []
    for domain in domains:
        naive = agg[domain]["cross_naive"]
        filtered = agg[domain]["cross_read_filter"]
        staged = agg[domain]["cross_staged"]
        overhead = staged["p95_latency_ms"] / naive["p95_latency_ms"] - 1.0
        staged_details[domain] = overhead
        g3_parts.append(
            staged["answer_error_rate"] <= 0.01
            and staged["answer_error_wilson_95ci"][1] <= 0.02
            and filtered["missing_rate"] - staged["missing_rate"] >= 0.01
            and overhead <= 0.20
        )
    g3 = all(g3_parts)
    write_ratios = {
        domain: agg[domain]["cross_blue_green"]["mean_write_amplification"]
        / max(agg[domain]["cross_staged"]["mean_write_amplification"], 1e-12)
        for domain in domains
    }
    g4 = all(
        write_ratios[domain] >= 5.0
        and agg[domain]["cross_blue_green"]["answer_error_rate"] <= 0.01
        and agg[domain]["cross_staged"]["answer_error_rate"] <= 0.01
        for domain in domains
    )
    g5 = all(
        agg[domain]["pg_atomic"]["answer_error_rate"] <= 0.01
        and agg[domain]["pg_atomic"]["answer_error_wilson_95ci"][1] <= 0.02
        for domain in domains
    )
    gates = {
        "G0_data_harness": g0,
        "G1_real_revision_failure": g1,
        "G2_simple_filter_sufficient": g2,
        "G3_staged_effective": g3,
        "G4_blue_green_cost_value": g4,
        "G5_pg_atomic_baseline": g5,
        "read_filter_p95_overhead": filter_details,
        "staged_p95_overhead": staged_details,
        "blue_to_staged_write_amp_ratio": write_ratios,
    }
    if not g0 or not g5:
        decision = "DATA_OR_HARNESS_FAILURE"
    elif not g1:
        decision = "STOP_NOT_ROBUST_ACROSS_DOMAINS"
    elif g2:
        decision = "STOP_SIMPLE_FILTER_SUFFICIENT"
    elif not (g3 and g4):
        decision = "STOP_STAGING_NO_SYSTEM_VALUE"
    else:
        decision = "GO_P1B_ANSWER_AND_FAILURE_INJECTION"
    return gates, decision


def write_outputs(output_dir: Path, repeat_rows: list[dict], events: list[dict], payload: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "query_events.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(events[0]))
        writer.writeheader()
        writer.writerows(events)
    with (output_dir / "repeat_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(repeat_rows[0]))
        writer.writeheader()
        writer.writerows(repeat_rows)
    (output_dir / "aggregate.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# FreshEvidenceDB P1-A 자동 보고",
        "",
        f"- 판정: **{payload['decision']}**",
        f"- 게이트: `{json.dumps(payload['gates'], sort_keys=True)}`",
        "",
        "| domain | protocol | update queries | error | stale | mixed | missing | p95 ms | write amp |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for domain, protocols in payload["aggregate"].items():
        for protocol in PROTOCOLS:
            row = protocols[protocol]
            lines.append(
                f"| {domain} | {protocol} | {row['update_queries']} | {row['answer_error_rate']:.4f} | "
                f"{row['stale_rate']:.4f} | {row['mixed_rate']:.4f} | {row['missing_rate']:.4f} | "
                f"{row['p95_latency_ms']:.2f} | {row['mean_write_amplification']:.2f} |"
            )
    lines.extend(["", "상세 결과는 `aggregate.json`, 질의별 결과는 `query_events.csv`에 있다.", ""])
    (output_dir / "AUTO_REPORT.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    corpus = Corpus(args.manifest.resolve())
    repeat_rows: list[dict] = []
    events: list[dict] = []
    started = time.perf_counter()
    for domain in sorted(corpus.domains):
        for protocol in PROTOCOLS:
            for repeat in range(N_REPEATS):
                experiment = Experiment(corpus, domain, protocol, repeat)
                summary = experiment.run()
                repeat_rows.append(summary)
                events.extend(experiment.results)
                print(
                    json.dumps(
                        {
                            "domain": domain,
                            "protocol": protocol,
                            "repeat": repeat,
                            "queries": summary["queries_update"],
                            "error": summary["error_rate_update"],
                            "worker_errors": summary["worker_errors"],
                        },
                        sort_keys=True,
                    ),
                    flush=True,
                )
    agg = aggregate(repeat_rows, events)
    gates, decision = decide(agg, repeat_rows)
    payload = {
        "protocol": {
            "seed": SEED,
            "domains": sorted(corpus.domains),
            "revision_pairs_per_domain": 100,
            "waves": N_WAVES,
            "docs_per_wave": DOCS_PER_WAVE,
            "repeats": N_REPEATS,
            "query_workers": N_WORKERS,
            "top_k": TOP_K,
            "vector_size": VECTOR_SIZE,
            "artificial_interphase_delay_ms": 0,
            "runtime_seconds": time.perf_counter() - started,
        },
        "aggregate": agg,
        "gates": gates,
        "decision": decision,
    }
    write_outputs(args.output_dir.resolve(), repeat_rows, events, payload)
    print(json.dumps({"decision": decision, "gates": gates}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
