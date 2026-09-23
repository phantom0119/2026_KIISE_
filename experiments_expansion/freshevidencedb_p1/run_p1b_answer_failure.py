#!/usr/bin/env python3
"""FreshEvidenceDB P1-B: deterministic answer checkpoints and client crash recovery."""

from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

import numpy as np
import psycopg
from qdrant_client import QdrantClient, models
from sklearn.feature_extraction.text import HashingVectorizer

from run_p1a_real_revision import (
    N_REPEATS,
    PG_DSN,
    TOP_K,
    VECTOR_SIZE,
    RevisionDoc,
    Stores,
    wilson_interval,
)


ANSWER_PROTOCOLS = ("cross_naive", "cross_read_filter", "cross_staged", "pg_atomic")
FAULT_SCENARIOS = (
    "partial_dense_crash",
    "dense_complete_crash",
    "sparse_complete_crash",
    "published_before_gc_crash",
    "duplicate_retry",
)


@dataclass(frozen=True)
class Fact:
    domain: str
    fact_id: int
    old_answer: str
    new_answer: str
    question: str
    doc: RevisionDoc


class FactCorpus:
    def __init__(self, manifest_path: Path) -> None:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.vectorizer = HashingVectorizer(
            n_features=VECTOR_SIZE,
            alternate_sign=False,
            norm="l2",
            analyzer="word",
            ngram_range=(1, 2),
        )
        self.facts: dict[str, list[Fact]] = {}
        self.domains: dict[str, list[RevisionDoc]] = {}
        for domain, data in payload["domains"].items():
            facts = []
            for item in data["facts"]:
                doc = RevisionDoc(
                    doc_id=int(item["fact_id"]),
                    probe=item["probe"],
                    commit=item["commit"],
                    parent=item["parent"],
                    path=item["path"],
                    old_chunks=(item["old_evidence"],),
                    new_chunks=(item["new_evidence"],),
                )
                facts.append(
                    Fact(
                        domain=domain,
                        fact_id=int(item["fact_id"]),
                        old_answer=item["old_answer"],
                        new_answer=item["new_answer"],
                        question=item["question"],
                        doc=doc,
                    )
                )
            if len(facts) != 25:
                raise RuntimeError(f"{domain}: expected 25 facts, got {len(facts)}")
            self.facts[domain] = facts
            self.domains[domain] = [fact.doc for fact in facts]

    def embed(self, texts: Sequence[str]) -> np.ndarray:
        return self.vectorizer.transform(texts).astype(np.float32).toarray()

    def rows(self, doc: RevisionDoc, version: int, epoch: int) -> list[tuple[int, int, int, int, str, str]]:
        source = doc.old_chunks if version == 1 else doc.new_chunks
        return [(doc.doc_id, version, epoch, index, text, doc.probe) for index, text in enumerate(source)]


def initialize(store: Stores, corpus: FactCorpus, facts: Sequence[Fact], *, pg_atomic: bool) -> None:
    docs = [fact.doc for fact in facts]
    store.initialize_manifest(docs)
    rows = [row for doc in docs for row in corpus.rows(doc, 1, 0)]
    if pg_atomic:
        with store.pg.transaction():
            store.insert_postgres(rows, include_vector=True, connection=store.pg, count=False)
    else:
        store.insert_qdrant(rows, count=False)
        with store.pg.transaction():
            store.insert_postgres(rows, include_vector=False, connection=store.pg, count=False)
    store.write_counts.clear()


def version_sets(store: Stores, fact: Fact, protocol: str) -> tuple[int, int, set[int], set[int]]:
    if protocol == "pg_atomic":
        conn = store.worker_pg()
        conn.execute("BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY")
        try:
            expected, _, epoch = store.read_manifest(fact.doc.doc_id, connection=conn)
            dense = store.postgres_dense_versions(fact.doc, conn)
            sparse = store.postgres_sparse_versions(fact.doc, None, None, connection=conn)
            conn.execute("COMMIT")
        except Exception:
            conn.execute("ROLLBACK")
            raise
        return expected, epoch, dense, sparse
    expected, _, epoch = store.read_manifest(fact.doc.doc_id)
    filter_version = None if protocol == "cross_naive" else expected
    dense = store.qdrant_versions(fact.doc, filter_version, None)
    sparse = store.postgres_sparse_versions(fact.doc, filter_version, None)
    return expected, epoch, dense, sparse


def answer_row(
    store: Stores,
    fact: Fact,
    protocol: str,
    repeat: int,
    checkpoint: str,
    experiment_kind: str,
    scenario: str = "",
) -> dict:
    start = time.perf_counter()
    expected, epoch, dense, sparse = version_sets(store, fact, protocol)
    observed = dense | sparse
    layer_missing = expected not in dense or expected not in sparse
    if layer_missing or not observed:
        label = "MISSING"
    elif observed == {1}:
        label = "OLD_ONLY"
    elif observed == {2}:
        label = "NEW_ONLY"
    else:
        label = "AMBIGUOUS"
    snapshot_correct = not layer_missing and observed == {expected}
    current_correct = expected == 2 and snapshot_correct
    return {
        "experiment_kind": experiment_kind,
        "domain": fact.domain,
        "protocol": protocol,
        "scenario": scenario,
        "repeat": repeat,
        "checkpoint": checkpoint,
        "fact_id": fact.fact_id,
        "commit": fact.doc.commit,
        "path": fact.doc.path,
        "expected_version": expected,
        "expected_epoch": epoch,
        "dense_versions": ";".join(map(str, sorted(dense))),
        "sparse_versions": ";".join(map(str, sorted(sparse))),
        "answer_label": label,
        "snapshot_correct": int(snapshot_correct),
        "current_correct": int(current_correct),
        "latency_ms": (time.perf_counter() - start) * 1000.0,
    }


def query_all(
    store: Stores,
    facts: Sequence[Fact],
    protocol: str,
    repeat: int,
    checkpoint: str,
    experiment_kind: str,
    scenario: str = "",
) -> list[dict]:
    return [answer_row(store, fact, protocol, repeat, checkpoint, experiment_kind, scenario) for fact in facts]


def all_rows(corpus: FactCorpus, facts: Sequence[Fact], version: int, epoch: int = 0) -> list[tuple[int, int, int, int, str, str]]:
    return [row for fact in facts for row in corpus.rows(fact.doc, version, epoch)]


def delete_old(store: Stores, facts: Sequence[Fact]) -> None:
    ids = [fact.fact_id for fact in facts]
    store.delete_qdrant(ids, 1)
    with store.pg.transaction():
        store.delete_postgres(ids, 1, connection=store.pg)


def run_answer_protocol(corpus: FactCorpus, domain: str, protocol: str, repeat: int) -> list[dict]:
    facts = corpus.facts[domain]
    run_key = f"ans_{domain}_{protocol}_r{repeat}"
    store = Stores(run_key, protocol, corpus)
    initialize(store, corpus, facts, pg_atomic=protocol == "pg_atomic")
    rows = query_all(store, facts, protocol, repeat, "initial", "answer")
    new_rows = all_rows(corpus, facts, 2, 0)
    changes = [(fact.fact_id, 2) for fact in facts]
    if protocol in ("cross_naive", "cross_read_filter"):
        store.publish(changes, 1)
        rows.extend(query_all(store, facts, protocol, repeat, "manifest_published", "answer"))
        store.insert_qdrant(new_rows)
        rows.extend(query_all(store, facts, protocol, repeat, "dense_inserted", "answer"))
        with store.pg.transaction():
            store.insert_postgres(new_rows, include_vector=False, connection=store.pg)
        rows.extend(query_all(store, facts, protocol, repeat, "sparse_inserted", "answer"))
        store.delete_qdrant([fact.fact_id for fact in facts], 1)
        rows.extend(query_all(store, facts, protocol, repeat, "dense_old_deleted", "answer"))
        with store.pg.transaction():
            store.delete_postgres([fact.fact_id for fact in facts], 1, connection=store.pg)
        rows.extend(query_all(store, facts, protocol, repeat, "sparse_old_deleted", "answer"))
    elif protocol == "cross_staged":
        store.insert_qdrant(new_rows)
        rows.extend(query_all(store, facts, protocol, repeat, "dense_staged", "answer"))
        with store.pg.transaction():
            store.insert_postgres(new_rows, include_vector=False, connection=store.pg)
        rows.extend(query_all(store, facts, protocol, repeat, "sparse_staged", "answer"))
        if not store.readiness([fact.doc for fact in facts], 2, 0):
            raise RuntimeError("staged readiness failed")
        rows.extend(query_all(store, facts, protocol, repeat, "readiness_verified", "answer"))
        store.publish(changes, 1)
        rows.extend(query_all(store, facts, protocol, repeat, "manifest_published", "answer"))
        delete_old(store, facts)
        rows.extend(query_all(store, facts, protocol, repeat, "old_version_gc", "answer"))
    elif protocol == "pg_atomic":
        store.atomic_update([fact.doc for fact in facts], 1)
        rows.extend(query_all(store, facts, protocol, repeat, "transaction_committed", "answer"))
    else:
        raise ValueError(protocol)
    store.close_worker_clients()
    store.close()
    return rows


def reconnect(store: Stores) -> None:
    store.close_worker_clients()
    store.local = threading.local()
    store.pg.close()
    store.qdrant.close()
    store.pg = psycopg.connect(PG_DSN, autocommit=True)
    store.qdrant = QdrantClient(url="http://127.0.0.1:6333", timeout=60)


def artifact_audit(store: Stores, facts: Sequence[Fact], version: int) -> tuple[int, int]:
    ids = [fact.fact_id for fact in facts]
    filt = models.Filter(
        must=[
            models.FieldCondition(key="doc_id", match=models.MatchAny(any=ids)),
            models.FieldCondition(key="version", match=models.MatchValue(value=version)),
        ]
    )
    dense = int(store.qdrant.count(store.collection, count_filter=filt, exact=True).count)
    with store.pg.cursor() as cur:
        cur.execute(f"SELECT count(*) FROM {store.q_artifact} WHERE doc_id = ANY(%s) AND version=%s", (ids, version))
        sparse = int(cur.fetchone()[0])
    return dense, sparse


def run_fault_scenario(corpus: FactCorpus, domain: str, scenario: str, repeat: int) -> tuple[list[dict], dict]:
    facts = corpus.facts[domain]
    run_key = f"fault_{domain}_{scenario}_r{repeat}"
    store = Stores(run_key, "cross_staged", corpus)
    initialize(store, corpus, facts, pg_atomic=False)
    new_rows = all_rows(corpus, facts, 2, 0)
    changes = [(fact.fact_id, 2) for fact in facts]
    expected_rows = len(new_rows)
    if scenario == "partial_dense_crash":
        store.insert_qdrant(new_rows[: len(new_rows) // 2])
    elif scenario == "dense_complete_crash":
        store.insert_qdrant(new_rows)
    elif scenario == "sparse_complete_crash":
        store.insert_qdrant(new_rows)
        with store.pg.transaction():
            store.insert_postgres(new_rows, include_vector=False, connection=store.pg)
    elif scenario == "published_before_gc_crash":
        store.insert_qdrant(new_rows)
        with store.pg.transaction():
            store.insert_postgres(new_rows, include_vector=False, connection=store.pg)
        if not store.readiness([fact.doc for fact in facts], 2, 0):
            raise RuntimeError("pre-publish readiness failed")
        store.publish(changes, 1)
    elif scenario == "duplicate_retry":
        for _ in range(2):
            store.insert_qdrant(new_rows)
            with store.pg.transaction():
                store.insert_postgres(new_rows, include_vector=False, connection=store.pg)
        store.publish(changes, 1)
        store.publish(changes, 1)
    else:
        raise ValueError(scenario)
    reconnect(store)
    rows = query_all(store, facts, "cross_staged", repeat, "after_crash", "fault", scenario)
    recovery_start = time.perf_counter()
    store.insert_qdrant(new_rows)
    with store.pg.transaction():
        store.insert_postgres(new_rows, include_vector=False, connection=store.pg)
    readiness = store.readiness([fact.doc for fact in facts], 2, 0)
    store.publish(changes, 1)
    recovery_ms = (time.perf_counter() - recovery_start) * 1000.0
    rows.extend(query_all(store, facts, "cross_staged", repeat, "after_recovery", "fault", scenario))
    dense_v2, sparse_v2 = artifact_audit(store, facts, 2)
    delete_old(store, facts)
    rows.extend(query_all(store, facts, "cross_staged", repeat, "after_gc", "fault", scenario))
    dense_v1, sparse_v1 = artifact_audit(store, facts, 1)
    dense_after, sparse_after = artifact_audit(store, facts, 2)
    audit = {
        "domain": domain,
        "scenario": scenario,
        "repeat": repeat,
        "expected_v2_rows": expected_rows,
        "dense_v2_before_gc": dense_v2,
        "sparse_v2_before_gc": sparse_v2,
        "dense_v2_after_gc": dense_after,
        "sparse_v2_after_gc": sparse_after,
        "dense_v1_after_gc": dense_v1,
        "sparse_v1_after_gc": sparse_v1,
        "duplicate_rows": max(0, dense_v2 - expected_rows) + max(0, sparse_v2 - expected_rows),
        "orphan_rows_after_gc": dense_v1 + sparse_v1,
        "readiness_ok": readiness,
        "recovery_ms": recovery_ms,
    }
    store.close_worker_clients()
    store.close()
    return rows, audit


def proportion(rows: Sequence[dict], field: str, value: int = 1) -> float:
    return sum(int(row[field]) == value for row in rows) / len(rows) if rows else float("nan")


def aggregate(answer_rows: list[dict], fault_rows: list[dict], audits: list[dict]) -> tuple[dict, dict, str]:
    domains = sorted({row["domain"] for row in answer_rows})
    answer_agg = {}
    for domain in domains:
        answer_agg[domain] = {}
        for protocol in ANSWER_PROTOCOLS:
            rows = [row for row in answer_rows if row["domain"] == domain and row["protocol"] == protocol]
            errors = sum(1 - int(row["snapshot_correct"]) for row in rows)
            active = [row for row in rows if int(row["expected_version"]) == 2]
            answer_agg[domain][protocol] = {
                "observations": len(rows),
                "snapshot_error_rate": errors / len(rows),
                "snapshot_error_wilson_95ci": list(wilson_interval(errors, len(rows))),
                "v2_active_observations": len(active),
                "v2_current_accuracy": proportion(active, "current_correct"),
                "v2_current_error_rate": 1.0 - proportion(active, "current_correct"),
                "missing_rate": sum(row["answer_label"] == "MISSING" for row in rows) / len(rows),
                "ambiguous_rate": sum(row["answer_label"] == "AMBIGUOUS" for row in rows) / len(rows),
                "stale_old_only_when_v2": sum(
                    row["answer_label"] == "OLD_ONLY" and int(row["expected_version"]) == 2 for row in rows
                ) / max(1, len(active)),
            }
    fault_eval = [row for row in fault_rows if row["checkpoint"] in ("after_crash", "after_recovery")]
    fault_errors = sum(1 - int(row["snapshot_correct"]) for row in fault_eval)
    gc_rows = [row for row in fault_rows if row["checkpoint"] == "after_gc"]
    fault_agg = {
        "crash_recovery_observations": len(fault_eval),
        "crash_recovery_errors": fault_errors,
        "crash_recovery_error_rate": fault_errors / len(fault_eval),
        "crash_recovery_wilson_95ci": list(wilson_interval(fault_errors, len(fault_eval))),
        "after_gc_observations": len(gc_rows),
        "after_gc_errors": sum(1 - int(row["snapshot_correct"]) for row in gc_rows),
        "duplicate_rows": sum(int(row["duplicate_rows"]) for row in audits),
        "orphan_rows_after_gc": sum(int(row["orphan_rows_after_gc"]) for row in audits),
        "readiness_all_ok": all(row["readiness_ok"] for row in audits),
        "recovery_p50_ms": float(np.quantile([row["recovery_ms"] for row in audits], 0.50)),
        "recovery_p95_ms": float(np.quantile([row["recovery_ms"] for row in audits], 0.95)),
        "scenario_runs": len(audits),
    }
    initial_rows = [row for row in answer_rows if row["checkpoint"] == "initial"]
    b0 = len(domains) == 2 and all(
        len({row["fact_id"] for row in answer_rows if row["domain"] == domain}) == 25 for domain in domains
    ) and all(row["snapshot_correct"] for row in initial_rows)
    staged_all = [row for row in answer_rows if row["protocol"] == "cross_staged"]
    pg_all = [row for row in answer_rows if row["protocol"] == "pg_atomic"]
    staged_errors = sum(1 - int(row["snapshot_correct"]) for row in staged_all)
    pg_errors = sum(1 - int(row["snapshot_correct"]) for row in pg_all)
    b1 = all(
        answer_agg[domain]["cross_naive"]["v2_current_error_rate"] >= 0.05
        and answer_agg[domain]["cross_staged"]["v2_current_accuracy"]
        - answer_agg[domain]["cross_read_filter"]["v2_current_accuracy"] >= 0.05
        for domain in domains
    ) and (
        staged_errors / len(staged_all) <= 0.01
        and wilson_interval(staged_errors, len(staged_all))[1] <= 0.02
        and pg_errors / len(pg_all) <= 0.01
        and wilson_interval(pg_errors, len(pg_all))[1] <= 0.02
    )
    b2 = (
        fault_errors == 0
        and wilson_interval(fault_errors, len(fault_eval))[1] <= 0.01
        and fault_agg["after_gc_errors"] == 0
        and fault_agg["duplicate_rows"] == 0
        and fault_agg["orphan_rows_after_gc"] == 0
        and fault_agg["readiness_all_ok"]
    )
    b3 = len(audits) == len(domains) * len(FAULT_SCENARIOS) * N_REPEATS and all(
        row["recovery_ms"] > 0 for row in audits
    )
    gates = {"B0_data_harness": b0, "B1_answer_value": b1, "B2_client_crash_safety": b2, "B3_recovery": b3}
    if not b0:
        decision = "DATA_OR_HARNESS_FAILURE"
    elif not b1:
        decision = "STOP_NO_ANSWER_LEVEL_VALUE"
    elif not (b2 and b3):
        decision = "STOP_RECOVERY_PROTOCOL_UNSAFE"
    else:
        decision = "GO_FRESHEVIDENCEDB_CORE_TOPIC"
    return {"answer": answer_agg, "fault": fault_agg}, gates, decision


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fact-manifest", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    corpus = FactCorpus(args.fact_manifest.resolve())
    answer_rows: list[dict] = []
    fault_rows: list[dict] = []
    audits: list[dict] = []
    started = time.perf_counter()
    for domain in sorted(corpus.facts):
        for protocol in ANSWER_PROTOCOLS:
            for repeat in range(N_REPEATS):
                rows = run_answer_protocol(corpus, domain, protocol, repeat)
                answer_rows.extend(rows)
                print(json.dumps({"kind": "answer", "domain": domain, "protocol": protocol, "repeat": repeat}), flush=True)
        for scenario in FAULT_SCENARIOS:
            for repeat in range(N_REPEATS):
                rows, audit = run_fault_scenario(corpus, domain, scenario, repeat)
                fault_rows.extend(rows)
                audits.append(audit)
                print(
                    json.dumps(
                        {
                            "kind": "fault",
                            "domain": domain,
                            "scenario": scenario,
                            "repeat": repeat,
                            "recovery_ms": audit["recovery_ms"],
                        }
                    ),
                    flush=True,
                )
    aggregate_result, gates, decision = aggregate(answer_rows, fault_rows, audits)
    payload = {
        "protocol": {
            "facts_per_domain": 25,
            "repeats": N_REPEATS,
            "answer_protocols": list(ANSWER_PROTOCOLS),
            "fault_scenarios": list(FAULT_SCENARIOS),
            "runtime_seconds": time.perf_counter() - started,
        },
        "aggregate": aggregate_result,
        "gates": gates,
        "decision": decision,
    }
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    write_csv(output / "answer_checkpoints.csv", answer_rows)
    write_csv(output / "fault_checkpoints.csv", fault_rows)
    write_csv(output / "fault_audits.csv", audits)
    (output / "aggregate.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# FreshEvidenceDB P1-B 자동 보고",
        "",
        f"- 판정: **{decision}**",
        f"- 게이트: `{json.dumps(gates, sort_keys=True)}`",
        "",
        "| domain | protocol | observations | snapshot error | v2 current accuracy | missing | ambiguous |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for domain, protocol_rows in aggregate_result["answer"].items():
        for protocol in ANSWER_PROTOCOLS:
            row = protocol_rows[protocol]
            lines.append(
                f"| {domain} | {protocol} | {row['observations']} | {row['snapshot_error_rate']:.4f} | "
                f"{row['v2_current_accuracy']:.4f} | {row['missing_rate']:.4f} | {row['ambiguous_rate']:.4f} |"
            )
    fault = aggregate_result["fault"]
    lines.extend(
        [
            "",
            f"- crash/recovery observations: {fault['crash_recovery_observations']}",
            f"- crash/recovery errors: {fault['crash_recovery_errors']}",
            f"- duplicate rows: {fault['duplicate_rows']}",
            f"- orphan rows after GC: {fault['orphan_rows_after_gc']}",
            f"- recovery p95: {fault['recovery_p95_ms']:.2f} ms",
            "",
        ]
    )
    (output / "AUTO_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"decision": decision, "gates": gates}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
