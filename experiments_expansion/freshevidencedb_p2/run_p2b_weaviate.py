#!/usr/bin/env python3
"""FreshEvidenceDB P2-B: Weaviate + PostgreSQL real-revision validation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import random
import re
import statistics
import sys
import threading
import time
import uuid
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import psycopg
import weaviate
from weaviate.classes.config import Configure, DataType, Property
from weaviate.classes.data import DataObject
from weaviate.classes.query import Filter


P1_DIR = Path(__file__).resolve().parent.parent / "freshevidencedb_p1"
sys.path.insert(0, str(P1_DIR))
from run_p1a_real_revision import Corpus, RevisionDoc, percentile, stable_int, wilson_interval  # noqa: E402


SEED = 20260807
PG_DSN = "host=127.0.0.1 port=15434 dbname=freshp2 user=freshp2 password=freshp2"
PG_SCHEMA = "fresh_p2b"
PROTOCOLS = ("weaviate_naive", "weaviate_read_filter", "weaviate_staged")
N_REPEATS = 3
N_WORKERS = 4
N_DOCS = 50
DOCS_PER_WAVE = 10
N_WAVES = 5
TOP_K = 8


class Store:
    def __init__(self, collection_name: str, table_base: str, corpus: Corpus) -> None:
        if not re.fullmatch(r"[a-z0-9_]+", table_base):
            raise ValueError(table_base)
        self.collection_name = collection_name
        self.table_base = table_base
        self.corpus = corpus
        self.client = weaviate.connect_to_local(host="127.0.0.1", port=8080, grpc_port=50051)
        self.pg = psycopg.connect(PG_DSN, autocommit=True)
        self.local = threading.local()
        self.manifest = f"{PG_SCHEMA}.{table_base}_manifest"
        self.sparse = f"{PG_SCHEMA}.{table_base}_sparse"
        self.global_table = f"{PG_SCHEMA}.{table_base}_global"
        self._init()

    def _init(self) -> None:
        existing = self.client.collections.list_all(simple=True)
        if self.collection_name in existing:
            self.client.collections.delete(self.collection_name)
        self.collection = self.client.collections.create(
            self.collection_name,
            vector_config=Configure.Vectors.self_provided(),
            properties=[
                Property(name="doc_id", data_type=DataType.INT, index_filterable=True),
                Property(name="version", data_type=DataType.INT, index_filterable=True),
                Property(name="epoch", data_type=DataType.INT, index_filterable=True),
                Property(name="chunk_id", data_type=DataType.INT),
                Property(name="probe", data_type=DataType.TEXT),
                Property(name="text_sha256", data_type=DataType.TEXT),
            ],
        )
        with self.pg.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {PG_SCHEMA}")
            for suffix in ("manifest", "sparse", "global"):
                cur.execute(f"DROP TABLE IF EXISTS {PG_SCHEMA}.{self.table_base}_{suffix}")
            cur.execute(
                f"CREATE TABLE {self.manifest}(doc_id integer primary key,active_version integer not null,epoch integer not null)"
            )
            cur.execute(f"CREATE TABLE {self.global_table}(id integer primary key,active_epoch integer not null)")
            cur.execute(f"INSERT INTO {self.global_table} VALUES(1,0)")
            cur.execute(
                f"""
                CREATE TABLE {self.sparse}(
                    doc_id integer not null,version integer not null,epoch integer not null,
                    chunk_id integer not null,text text not null,probe text not null,
                    search tsvector generated always as (to_tsvector('simple',probe||' '||text)) stored,
                    primary key(doc_id,version,epoch,chunk_id)
                )
                """
            )
            cur.execute(f"CREATE INDEX {self.table_base}_sparse_lookup ON {self.sparse}(doc_id,version,epoch)")
            cur.execute(f"CREATE INDEX {self.table_base}_sparse_fts ON {self.sparse} USING GIN(search)")

    def worker_resources(self):
        pg = getattr(self.local, "pg", None)
        if pg is None or pg.closed:
            pg = psycopg.connect(PG_DSN, autocommit=True)
            self.local.pg = pg
        client = getattr(self.local, "client", None)
        if client is None:
            client = weaviate.connect_to_local(host="127.0.0.1", port=8080, grpc_port=50051)
            self.local.client = client
        return pg, client.collections.get(self.collection_name)

    def close_worker(self) -> None:
        pg = getattr(self.local, "pg", None)
        if pg is not None and not pg.closed:
            pg.close()
        client = getattr(self.local, "client", None)
        if client is not None:
            client.close()

    def close(self) -> None:
        self.close_worker()
        self.pg.close()
        self.client.close()

    def initialize_manifest(self, docs: Sequence[RevisionDoc]) -> None:
        with self.pg.transaction():
            with self.pg.cursor() as cur:
                cur.executemany(f"INSERT INTO {self.manifest} VALUES(%s,1,0)", [(doc.doc_id,) for doc in docs])

    def insert_dense(self, rows, *, count: bool = True) -> int:
        if not rows:
            return 0
        vectors = self.corpus.embed([f"{probe} {text}" for _, _, _, _, text, probe in rows])
        inserted = 0
        for start in range(0, len(rows), 200):
            objects = []
            for row, vector in zip(rows[start : start + 200], vectors[start : start + 200]):
                doc_id, version, epoch, chunk_id, text, probe = row
                object_id = uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{self.collection_name}:{doc_id}:{version}:{epoch}:{chunk_id}",
                )
                objects.append(
                    DataObject(
                        uuid=object_id,
                        vector=vector.tolist(),
                        properties={
                            "doc_id": doc_id,
                            "version": version,
                            "epoch": epoch,
                            "chunk_id": chunk_id,
                            "probe": probe,
                            "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                        },
                    )
                )
            result = self.collection.data.insert_many(objects)
            if result.has_errors:
                raise RuntimeError(f"Weaviate insert errors: {result.errors}")
            inserted += len(objects)
        return inserted

    def insert_sparse(self, rows) -> int:
        if not rows:
            return 0
        with self.pg.transaction():
            with self.pg.cursor() as cur:
                cur.executemany(
                    f"""
                    INSERT INTO {self.sparse}(doc_id,version,epoch,chunk_id,text,probe)
                    VALUES(%s,%s,%s,%s,%s,%s)
                    ON CONFLICT(doc_id,version,epoch,chunk_id) DO UPDATE SET text=excluded.text,probe=excluded.probe
                    """,
                    rows,
                )
        return len(rows)

    def publish(self, docs: Sequence[RevisionDoc], epoch: int) -> None:
        with self.pg.transaction():
            with self.pg.cursor() as cur:
                cur.executemany(
                    f"UPDATE {self.manifest} SET active_version=2,epoch=%s WHERE doc_id=%s",
                    [(epoch, doc.doc_id) for doc in docs],
                )

    def read_manifest(self, doc_id: int) -> tuple[int, int]:
        pg, _ = self.worker_resources()
        with pg.cursor() as cur:
            cur.execute(f"SELECT active_version,epoch FROM {self.manifest} WHERE doc_id=%s", (doc_id,))
            row = cur.fetchone()
        return int(row[0]), int(row[1])

    def dense_versions(self, doc: RevisionDoc, version: Optional[int]) -> set[int]:
        _, collection = self.worker_resources()
        filt = Filter.by_property("doc_id").equal(doc.doc_id)
        if version is not None:
            filt = filt & Filter.by_property("version").equal(version)
        response = collection.query.near_vector(
            self.corpus.embed([doc.probe])[0].tolist(),
            filters=filt,
            limit=TOP_K,
            return_properties=["version"],
        )
        return {int(obj.properties["version"]) for obj in response.objects}

    def sparse_versions(self, doc: RevisionDoc, version: Optional[int]) -> set[int]:
        pg, _ = self.worker_resources()
        sql = f"SELECT version FROM {self.sparse} WHERE doc_id=%s AND search @@ plainto_tsquery('simple',%s)"
        params: list[object] = [doc.doc_id, doc.probe]
        if version is not None:
            sql += " AND version=%s"
            params.append(version)
        sql += " ORDER BY version,chunk_id LIMIT %s"
        params.append(TOP_K)
        with pg.cursor() as cur:
            cur.execute(sql, params)
            return {int(row[0]) for row in cur.fetchall()}

    def delete_old(self, docs: Sequence[RevisionDoc]) -> None:
        for doc in docs:
            filt = Filter.by_property("doc_id").equal(doc.doc_id) & Filter.by_property("version").equal(1)
            self.collection.data.delete_many(where=filt)
        with self.pg.transaction():
            with self.pg.cursor() as cur:
                cur.execute(f"DELETE FROM {self.sparse} WHERE doc_id=ANY(%s) AND version=1", ([d.doc_id for d in docs],))

    def readiness(self, docs: Sequence[RevisionDoc], version: int) -> bool:
        expected = sum(len(doc.new_chunks if version == 2 else doc.old_chunks) for doc in docs)
        dense = 0
        for doc in docs:
            filt = Filter.by_property("doc_id").equal(doc.doc_id) & Filter.by_property("version").equal(version)
            dense += int(self.collection.aggregate.over_all(filters=filt, total_count=True).total_count)
        with self.pg.cursor() as cur:
            cur.execute(
                f"SELECT count(*) FROM {self.sparse} WHERE doc_id=ANY(%s) AND version=%s",
                ([doc.doc_id for doc in docs], version),
            )
            sparse = int(cur.fetchone()[0])
        return dense == expected and sparse == expected

    def wait_searchable(self, docs: Sequence[RevisionDoc], version: int, timeout_s: float = 15.0) -> bool:
        """Wait for Weaviate's asynchronous vector index to expose every staged document."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if all(version in self.dense_versions(doc, version) for doc in docs):
                return True
            time.sleep(0.02)
        return False

    def wait_ready(self, docs: Sequence[RevisionDoc], version: int, timeout_s: float = 15.0) -> bool:
        """Require both durable row counts and actual filtered vector searchability."""
        deadline = time.monotonic() + timeout_s
        while time.monotonic() < deadline:
            if self.readiness(docs, version) and self.wait_searchable(docs, version, timeout_s=0.25):
                return True
            time.sleep(0.02)
        return False


class Experiment:
    def __init__(self, corpus: Corpus, domain: str, protocol: str, repeat: int) -> None:
        self.corpus = corpus
        self.domain = domain
        self.protocol = protocol
        self.repeat = repeat
        self.docs = corpus.domains[domain][:N_DOCS]
        title = "".join(word.title() for word in protocol.split("_"))
        self.collection_name = f"FreshP2{domain.title()}{title}R{repeat}"
        self.store = Store(self.collection_name, f"{domain}_{protocol}_r{repeat}", corpus)
        self.results = []
        self.results_lock = threading.Lock()
        self.hot_docs = list(self.docs)
        self.hot_lock = threading.Lock()
        self.in_update = threading.Event()
        self.stop = threading.Event()
        self.errors = []
        self.wave_durations = []
        self.writes = 0
        self.ideal = 0

    def rows(self, docs: Sequence[RevisionDoc], version: int):
        return [row for doc in docs for row in self.corpus.rows(doc, version, 0)]

    def initialize(self) -> None:
        self.store.initialize_manifest(self.docs)
        rows = self.rows(self.docs, 1)
        self.store.insert_dense(rows, count=False)
        self.store.insert_sparse(rows)
        if not self.store.wait_ready(self.docs, 1):
            raise RuntimeError("initial Weaviate rows did not become searchable")
        self.writes = 0

    def query(self, doc: RevisionDoc, record: bool = True):
        start = time.perf_counter()
        expected, epoch = self.store.read_manifest(doc.doc_id)
        filt = None if self.protocol == "weaviate_naive" else expected
        dense = self.store.dense_versions(doc, filt)
        sparse = self.store.sparse_versions(doc, filt)
        observed = dense | sparse
        stale = any(version < expected for version in observed)
        future = any(version > expected for version in observed)
        mixed = len(observed) > 1
        missing = expected not in dense or expected not in sparse
        row = {
            "domain": self.domain,
            "protocol": self.protocol,
            "repeat": self.repeat,
            "doc_id": doc.doc_id,
            "expected_version": expected,
            "expected_epoch": epoch,
            "dense_versions": ";".join(map(str, sorted(dense))),
            "sparse_versions": ";".join(map(str, sorted(sparse))),
            "stale": int(stale),
            "future": int(future),
            "mixed": int(mixed),
            "missing": int(missing),
            "answer_error": int(stale or future or mixed or missing),
            "update_window": int(self.in_update.is_set()),
            "latency_ms": (time.perf_counter() - start) * 1000.0,
        }
        if record:
            with self.results_lock:
                self.results.append(row)
        return row

    def worker(self, worker_id: int):
        rng = random.Random(SEED + stable_int(self.collection_name) % 100000 + worker_id)
        try:
            while not self.stop.is_set():
                with self.hot_lock:
                    hot = list(self.hot_docs)
                doc = rng.choice(hot if rng.random() < 0.8 else self.docs)
                self.query(doc)
                time.sleep(rng.uniform(0.0005, 0.0015))
        except Exception as exc:
            self.errors.append(f"worker {worker_id}: {type(exc).__name__}: {exc}")
            self.stop.set()
        finally:
            self.store.close_worker()

    def run(self):
        self.initialize()
        steady = all(not self.query(doc, False)["answer_error"] for doc in self.docs)
        threads = [threading.Thread(target=self.worker, args=(i,), daemon=True) for i in range(N_WORKERS)]
        for thread in threads:
            thread.start()
        readiness_ok = True
        waves = 0
        for wave in range(N_WAVES):
            docs = self.docs[wave * DOCS_PER_WAVE : (wave + 1) * DOCS_PER_WAVE]
            rows = self.rows(docs, 2)
            self.ideal += len(rows)
            with self.hot_lock:
                self.hot_docs = list(docs)
            self.in_update.set()
            start = time.perf_counter()
            try:
                if self.protocol in ("weaviate_naive", "weaviate_read_filter"):
                    self.store.publish(docs, wave + 1)
                    self.writes += self.store.insert_dense(rows)
                    self.writes += self.store.insert_sparse(rows)
                    self.store.delete_old(docs)
                else:
                    self.writes += self.store.insert_dense(rows)
                    self.writes += self.store.insert_sparse(rows)
                    ok = self.store.wait_ready(docs, 2)
                    readiness_ok = readiness_ok and ok
                    if not ok:
                        raise RuntimeError("readiness mismatch")
                    self.store.publish(docs, wave + 1)
                waves += 1
            except Exception as exc:
                self.errors.append(f"writer: {type(exc).__name__}: {exc}")
                self.stop.set()
            finally:
                self.wave_durations.append((time.perf_counter() - start) * 1000.0)
                self.in_update.clear()
            time.sleep(0.005)
            if self.stop.is_set():
                break
        time.sleep(0.03)
        self.stop.set()
        for thread in threads:
            thread.join(timeout=30)
        update = [row for row in self.results if row["update_window"]]
        summary = {
            "domain": self.domain,
            "protocol": self.protocol,
            "repeat": self.repeat,
            "steady_ok": steady,
            "readiness_ok": readiness_ok,
            "worker_errors": list(self.errors),
            "waves_completed": waves,
            "queries_update": len(update),
            "error_rate": statistics.mean(r["answer_error"] for r in update) if update else 1.0,
            "stale_rate": statistics.mean(r["stale"] for r in update) if update else 1.0,
            "mixed_rate": statistics.mean(r["mixed"] for r in update) if update else 1.0,
            "missing_rate": statistics.mean(r["missing"] for r in update) if update else 1.0,
            "p95_latency_ms": percentile([r["latency_ms"] for r in update], 0.95),
            "p95_wave_ms": percentile(self.wave_durations, 0.95),
            "write_amplification": self.writes / max(1, 2 * self.ideal),
        }
        self.store.close()
        return summary


def aggregate(summaries, events):
    output = {}
    for domain in sorted({row["domain"] for row in summaries}):
        output[domain] = {}
        for protocol in PROTOCOLS:
            reps = [row for row in summaries if row["domain"] == domain and row["protocol"] == protocol]
            rows = [row for row in events if row["domain"] == domain and row["protocol"] == protocol and row["update_window"]]
            errors = sum(row["answer_error"] for row in rows)
            output[domain][protocol] = {
                "update_queries": len(rows),
                "error_rate": errors / len(rows) if rows else 1.0,
                "error_wilson_95ci": list(wilson_interval(errors, len(rows))),
                "stale_rate": sum(row["stale"] for row in rows) / len(rows) if rows else 1.0,
                "mixed_rate": sum(row["mixed"] for row in rows) / len(rows) if rows else 1.0,
                "missing_rate": sum(row["missing"] for row in rows) / len(rows) if rows else 1.0,
                "p95_latency_ms": percentile([row["latency_ms"] for row in rows], 0.95),
                "repeat_error_rates": [row["error_rate"] for row in reps],
                "repeats_at_or_above_1pct": sum(row["error_rate"] >= 0.01 for row in reps),
                "steady_all_ok": all(row["steady_ok"] for row in reps),
                "readiness_all_ok": all(row["readiness_ok"] for row in reps),
                "worker_errors": [e for row in reps for e in row["worker_errors"]],
                "waves_completed": sum(row["waves_completed"] for row in reps),
            }
    g0 = all(
        output[d][p]["steady_all_ok"] and output[d][p]["readiness_all_ok"]
        and not output[d][p]["worker_errors"] and output[d][p]["update_queries"] >= 300
        and output[d][p]["waves_completed"] == N_REPEATS * N_WAVES
        for d in output for p in PROTOCOLS
    )
    t2 = g0 and all(
        output[d]["weaviate_naive"]["repeats_at_or_above_1pct"] >= 2
        and output[d]["weaviate_naive"]["error_wilson_95ci"][0] > 0.001
        and output[d]["weaviate_read_filter"]["error_rate"] > 0.01
        and output[d]["weaviate_read_filter"]["missing_rate"] > 0.01
        and output[d]["weaviate_staged"]["error_rate"] <= 0.01
        and output[d]["weaviate_staged"]["error_wilson_95ci"][1] <= 0.02
        and output[d]["weaviate_read_filter"]["missing_rate"] - output[d]["weaviate_staged"]["missing_rate"] >= 0.01
        for d in output
    )
    return output, {"G0": g0, "T2": "CROSS_ENGINE_GENERALIZED" if t2 else "STOP_BACKEND_SPECIFIC_OR_HARNESS"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    corpus = Corpus(args.manifest.resolve())
    summaries, events = [], []
    for domain in sorted(corpus.domains):
        for protocol in PROTOCOLS:
            for repeat in range(N_REPEATS):
                exp = Experiment(corpus, domain, protocol, repeat)
                summary = exp.run()
                summaries.append(summary)
                events.extend(exp.results)
                print(json.dumps({"domain":domain,"protocol":protocol,"repeat":repeat,"error":summary["error_rate"],"errors":summary["worker_errors"]}), flush=True)
    agg, gates = aggregate(summaries, events)
    out = args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True)
    with (out/"query_events.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(events[0]));w.writeheader();w.writerows(events)
    with (out/"repeat_summary.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
    payload={"aggregate":agg,"gates":gates}
    (out/"aggregate.json").write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    lines=["# P2-B Weaviate 자동 보고","",f"- T2: **{gates['T2']}**","","| domain | protocol | queries | error | missing | p95 ms |","|---|---|---:|---:|---:|---:|"]
    for d in agg:
        for p in PROTOCOLS:
            r=agg[d][p];lines.append(f"| {d} | {p} | {r['update_queries']} | {r['error_rate']:.4f} | {r['missing_rate']:.4f} | {r['p95_latency_ms']:.2f} |")
    lines.append("");(out/"AUTO_REPORT.md").write_text("\n".join(lines),encoding="utf-8")
    print(json.dumps(gates,sort_keys=True),flush=True)


if __name__ == "__main__":
    main()
