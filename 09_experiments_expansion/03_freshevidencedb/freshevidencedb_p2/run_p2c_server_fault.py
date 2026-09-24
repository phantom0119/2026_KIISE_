#!/usr/bin/env python3
"""FreshEvidenceDB P2-C: real Qdrant/PostgreSQL process-fault validation."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Sequence
from urllib.request import urlopen

import psycopg
from qdrant_client import QdrantClient, models


P1_DIR = Path(__file__).resolve().parent.parent / "freshevidencedb_p1"
sys.path.insert(0, str(P1_DIR))
from run_p1a_real_revision import VECTOR_SIZE, wilson_interval  # noqa: E402
from run_p1b_answer_failure import Fact, FactCorpus  # noqa: E402


PG_DSN = "host=127.0.0.1 port=15434 dbname=freshp2 user=freshp2 password=freshp2"
QDRANT_URL = "http://127.0.0.1:16333"
QDRANT_CONTAINER = "fresh-p2-qdrant"
POSTGRES_CONTAINER = "fresh-p2-postgres"
PG_SCHEMA = "fresh_p2c"
SCENARIOS = (
    "qdrant_kill_partial_stage",
    "qdrant_kill_ready_before_publish",
    "postgres_kill_before_sparse_commit",
    "postgres_kill_after_publish_before_gc",
    "qdrant_pause_timeout_retry",
)
REPEATS = 2


def docker(action: str, container: str) -> None:
    if container not in (QDRANT_CONTAINER, POSTGRES_CONTAINER):
        raise ValueError(f"refusing non-P2 container: {container}")
    subprocess.run(["docker", action, container], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)


def wait_qdrant(timeout_s: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{QDRANT_URL}/healthz", timeout=1.0) as response:
                if response.status == 200:
                    return
        except Exception:
            time.sleep(0.1)
    raise TimeoutError("P2 Qdrant did not recover")


def wait_postgres(timeout_s: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with psycopg.connect(PG_DSN, connect_timeout=1) as connection:
                connection.execute("SELECT 1")
            return
        except Exception:
            time.sleep(0.1)
    raise TimeoutError("P2 PostgreSQL did not recover")


class FaultStore:
    def __init__(self, run_key: str, corpus: FactCorpus) -> None:
        if not re.fullmatch(r"[a-z0-9_]+", run_key):
            raise ValueError(run_key)
        self.run_key = run_key
        self.corpus = corpus
        self.collection = f"fresh_p2c_{run_key}"
        self.manifest = f"{PG_SCHEMA}.{run_key}_manifest"
        self.sparse = f"{PG_SCHEMA}.{run_key}_sparse"
        self.pg = psycopg.connect(PG_DSN, autocommit=True)
        self.qdrant = QdrantClient(url=QDRANT_URL, timeout=5)
        self._create()

    def _create(self) -> None:
        with self.pg.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {PG_SCHEMA}")
            cur.execute(f"DROP TABLE IF EXISTS {self.sparse}")
            cur.execute(f"DROP TABLE IF EXISTS {self.manifest}")
            cur.execute(
                f"CREATE TABLE {self.manifest}(doc_id integer primary key,active_version integer not null,epoch integer not null)"
            )
            cur.execute(
                f"""
                CREATE TABLE {self.sparse}(
                    doc_id integer not null,version integer not null,epoch integer not null,
                    chunk_id integer not null,text text not null,probe text not null,
                    primary key(doc_id,version,epoch,chunk_id)
                )
                """
            )
        existing = {item.name for item in self.qdrant.get_collections().collections}
        if self.collection in existing:
            self.qdrant.delete_collection(self.collection)
        self.qdrant.create_collection(
            self.collection,
            vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE),
        )
        for field in ("doc_id", "version", "epoch"):
            self.qdrant.create_payload_index(
                self.collection, field, models.PayloadSchemaType.INTEGER, wait=True
            )

    def reconnect(self) -> None:
        try:
            self.pg.close()
        except Exception:
            pass
        try:
            self.qdrant.close()
        except Exception:
            pass
        self.pg = psycopg.connect(PG_DSN, autocommit=True)
        self.qdrant = QdrantClient(url=QDRANT_URL, timeout=5)

    def close(self) -> None:
        self.pg.close()
        self.qdrant.close()

    def rows(self, facts: Sequence[Fact], version: int):
        return [row for fact in facts for row in self.corpus.rows(fact.doc, version, 0)]

    def initialize(self, facts: Sequence[Fact]) -> None:
        with self.pg.transaction():
            with self.pg.cursor() as cur:
                cur.executemany(f"INSERT INTO {self.manifest} VALUES(%s,1,0)", [(f.fact_id,) for f in facts])
        rows = self.rows(facts, 1)
        self.insert_dense(rows)
        self.insert_sparse(rows)

    def point_id(self, row) -> str:
        doc_id, version, epoch, chunk_id, _, _ = row
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{self.run_key}:{doc_id}:{version}:{epoch}:{chunk_id}"))

    def insert_dense(self, rows) -> None:
        if not rows:
            return
        vectors = self.corpus.embed([f"{probe} {text}" for _, _, _, _, text, probe in rows])
        points = []
        for row, vector in zip(rows, vectors):
            doc_id, version, epoch, chunk_id, text, probe = row
            points.append(
                models.PointStruct(
                    id=self.point_id(row),
                    vector=vector.tolist(),
                    payload={
                        "doc_id": doc_id,
                        "version": version,
                        "epoch": epoch,
                        "chunk_id": chunk_id,
                        "probe": probe,
                        "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                    },
                )
            )
        self.qdrant.upsert(self.collection, points=points, wait=True)

    def insert_sparse(self, rows, connection=None) -> None:
        conn = connection or self.pg
        with conn.cursor() as cur:
            cur.executemany(
                f"""
                INSERT INTO {self.sparse}(doc_id,version,epoch,chunk_id,text,probe)
                VALUES(%s,%s,%s,%s,%s,%s)
                ON CONFLICT(doc_id,version,epoch,chunk_id)
                DO UPDATE SET text=excluded.text,probe=excluded.probe
                """,
                rows,
            )

    def publish(self, facts: Sequence[Fact]) -> None:
        with self.pg.transaction():
            with self.pg.cursor() as cur:
                cur.executemany(
                    f"UPDATE {self.manifest} SET active_version=2,epoch=1 WHERE doc_id=%s",
                    [(fact.fact_id,) for fact in facts],
                )

    def count(self, facts: Sequence[Fact], version: int) -> tuple[int, int]:
        ids = [fact.fact_id for fact in facts]
        filt = models.Filter(
            must=[
                models.FieldCondition(key="doc_id", match=models.MatchAny(any=ids)),
                models.FieldCondition(key="version", match=models.MatchValue(value=version)),
            ]
        )
        dense = int(self.qdrant.count(self.collection, count_filter=filt, exact=True).count)
        with self.pg.cursor() as cur:
            cur.execute(f"SELECT count(*) FROM {self.sparse} WHERE doc_id=ANY(%s) AND version=%s", (ids, version))
            sparse = int(cur.fetchone()[0])
        return dense, sparse

    def readiness(self, facts: Sequence[Fact], version: int = 2) -> bool:
        expected = len(facts)
        return self.count(facts, version) == (expected, expected)

    def delete_old(self, facts: Sequence[Fact]) -> None:
        ids = [fact.fact_id for fact in facts]
        filt = models.Filter(
            must=[
                models.FieldCondition(key="doc_id", match=models.MatchAny(any=ids)),
                models.FieldCondition(key="version", match=models.MatchValue(value=1)),
            ]
        )
        self.qdrant.delete(self.collection, models.FilterSelector(filter=filt), wait=True)
        with self.pg.transaction():
            with self.pg.cursor() as cur:
                cur.execute(f"DELETE FROM {self.sparse} WHERE doc_id=ANY(%s) AND version=1", (ids,))

    def snapshot_rows(self, facts: Sequence[Fact], checkpoint: str, scenario: str, repeat: int):
        output = []
        for fact in facts:
            with self.pg.cursor() as cur:
                cur.execute(f"SELECT active_version,epoch FROM {self.manifest} WHERE doc_id=%s", (fact.fact_id,))
                active_version, epoch = map(int, cur.fetchone())
                cur.execute(
                    f"SELECT count(*) FROM {self.sparse} WHERE doc_id=%s AND version=%s",
                    (fact.fact_id, active_version),
                )
                sparse_count = int(cur.fetchone()[0])
            filt = models.Filter(
                must=[
                    models.FieldCondition(key="doc_id", match=models.MatchValue(value=fact.fact_id)),
                    models.FieldCondition(key="version", match=models.MatchValue(value=active_version)),
                ]
            )
            dense_count = int(self.qdrant.count(self.collection, count_filter=filt, exact=True).count)
            correct = dense_count == 1 and sparse_count == 1
            output.append(
                {
                    "domain": fact.domain,
                    "scenario": scenario,
                    "repeat": repeat,
                    "checkpoint": checkpoint,
                    "fact_id": fact.fact_id,
                    "active_version": active_version,
                    "active_epoch": epoch,
                    "dense_count": dense_count,
                    "sparse_count": sparse_count,
                    "snapshot_error": int(not correct),
                    "incomplete_manifest_reference": int(not correct),
                }
            )
        return output


def run_one(corpus: FactCorpus, domain: str, scenario: str, repeat: int):
    facts = corpus.facts[domain]
    store = FaultStore(f"{domain}_{scenario}_r{repeat}", corpus)
    store.initialize(facts)
    new_rows = store.rows(facts, 2)
    expected_timeout = False
    crash_start = time.perf_counter()

    if scenario == "qdrant_kill_partial_stage":
        store.insert_dense(new_rows[: len(new_rows) // 2])
        docker("kill", QDRANT_CONTAINER); docker("start", QDRANT_CONTAINER); wait_qdrant(); store.reconnect()
    elif scenario == "qdrant_kill_ready_before_publish":
        store.insert_dense(new_rows)
        docker("kill", QDRANT_CONTAINER); docker("start", QDRANT_CONTAINER); wait_qdrant(); store.reconnect()
    elif scenario == "postgres_kill_before_sparse_commit":
        store.insert_dense(new_rows)
        tx = psycopg.connect(PG_DSN, autocommit=False)
        store.insert_sparse(new_rows, connection=tx)
        docker("kill", POSTGRES_CONTAINER)
        try:
            tx.commit()
        except Exception:
            pass
        tx.close()
        docker("start", POSTGRES_CONTAINER); wait_postgres(); store.reconnect()
    elif scenario == "postgres_kill_after_publish_before_gc":
        store.insert_dense(new_rows); store.insert_sparse(new_rows)
        if not store.readiness(facts):
            raise RuntimeError("pre-publish readiness failed")
        store.publish(facts)
        docker("kill", POSTGRES_CONTAINER); docker("start", POSTGRES_CONTAINER); wait_postgres(); store.reconnect()
    elif scenario == "qdrant_pause_timeout_retry":
        docker("pause", QDRANT_CONTAINER)
        try:
            temporary = QdrantClient(url=QDRANT_URL, timeout=1)
            try:
                temporary.get_collections()
            except Exception:
                expected_timeout = True
            finally:
                temporary.close()
        finally:
            docker("unpause", QDRANT_CONTAINER)
        wait_qdrant(); store.reconnect()
    else:
        raise ValueError(scenario)

    restart_ms = (time.perf_counter() - crash_start) * 1000.0
    rows = store.snapshot_rows(facts, "after_restart_before_recovery", scenario, repeat)
    recovery_start = time.perf_counter()
    store.insert_dense(new_rows)
    store.insert_sparse(new_rows)
    ready = store.readiness(facts)
    store.publish(facts)
    recovery_ms = (time.perf_counter() - recovery_start) * 1000.0
    rows.extend(store.snapshot_rows(facts, "after_recovery", scenario, repeat))
    dense_v2, sparse_v2 = store.count(facts, 2)
    store.delete_old(facts)
    rows.extend(store.snapshot_rows(facts, "after_gc", scenario, repeat))
    dense_v1, sparse_v1 = store.count(facts, 1)
    dense_v2_gc, sparse_v2_gc = store.count(facts, 2)
    audit = {
        "domain": domain,
        "scenario": scenario,
        "repeat": repeat,
        "restart_ms": restart_ms,
        "recovery_ms": recovery_ms,
        "readiness_ok": ready,
        "expected_pause_timeout_observed": expected_timeout if scenario == "qdrant_pause_timeout_retry" else True,
        "duplicate_logical_artifacts": max(0, dense_v2 - len(facts)) + max(0, sparse_v2 - len(facts)),
        "orphan_v1_after_gc": dense_v1 + sparse_v1,
        "v2_rows_after_gc": dense_v2_gc + sparse_v2_gc,
        "expected_v2_rows_after_gc": 2 * len(facts),
    }
    store.close()
    return rows, audit


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    wait_qdrant(); wait_postgres()
    corpus = FactCorpus(args.manifest.resolve())
    rows, audits = [], []
    for domain in sorted(corpus.facts):
        for scenario in SCENARIOS:
            for repeat in range(REPEATS):
                scenario_rows, audit = run_one(corpus, domain, scenario, repeat)
                rows.extend(scenario_rows); audits.append(audit)
                print(json.dumps(audit, sort_keys=True), flush=True)

    evaluated = [row for row in rows if row["checkpoint"] in ("after_restart_before_recovery", "after_recovery")]
    errors = sum(row["snapshot_error"] for row in evaluated)
    t3 = (
        len(audits) == 20
        and errors == 0
        and wilson_interval(errors, len(evaluated))[1] <= 0.01
        and sum(row["snapshot_error"] for row in rows if row["checkpoint"] == "after_gc") == 0
        and all(a["readiness_ok"] and a["expected_pause_timeout_observed"] for a in audits)
        and sum(a["duplicate_logical_artifacts"] for a in audits) == 0
        and sum(a["orphan_v1_after_gc"] for a in audits) == 0
        and sum(row["incomplete_manifest_reference"] for row in rows) == 0
    )
    aggregate = {
        "scenario_runs": len(audits),
        "crash_recovery_observations": len(evaluated),
        "snapshot_errors": errors,
        "snapshot_error_wilson_95ci": list(wilson_interval(errors, len(evaluated))),
        "after_gc_errors": sum(row["snapshot_error"] for row in rows if row["checkpoint"] == "after_gc"),
        "duplicates": sum(a["duplicate_logical_artifacts"] for a in audits),
        "orphans_after_gc": sum(a["orphan_v1_after_gc"] for a in audits),
        "incomplete_manifest_references": sum(row["incomplete_manifest_reference"] for row in rows),
        "recovery_p95_ms": sorted(a["recovery_ms"] for a in audits)[int(0.95 * (len(audits) - 1))],
        "T3": "SERVER_FAULT_GATE_PASS" if t3 else "STOP_SERVER_RECOVERY_UNSAFE",
    }
    out = args.output_dir.resolve(); out.mkdir(parents=True, exist_ok=True)
    with (out / "checkpoint_rows.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    with (out / "scenario_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(audits[0])); writer.writeheader(); writer.writerows(audits)
    (out / "aggregate.json").write_text(json.dumps(aggregate, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report = [
        "# P2-C 서버 장애 자동 보고", "", f"- T3: **{aggregate['T3']}**",
        f"- 시나리오 실행: {aggregate['scenario_runs']}",
        f"- restart/recovery 관측: {len(evaluated)}, 오류: {errors}, Wilson 상한: {aggregate['snapshot_error_wilson_95ci'][1]:.4%}",
        f"- duplicate: {aggregate['duplicates']}, orphan: {aggregate['orphans_after_gc']}",
        f"- recovery p95: {aggregate['recovery_p95_ms']:.2f} ms", "",
        "장애 중 서비스 가용성은 별도 지표이다. `after_restart_before_recovery`는 container가 다시 health/readiness를 통과한 직후를 뜻한다.",
    ]
    (out / "AUTO_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps(aggregate, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
