#!/usr/bin/env python3
"""P3-C: coordinator SIGKILL, message reorder, and dedicated store faults."""

from __future__ import annotations

import argparse
import csv
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import psycopg
import requests


HERE = Path(__file__).resolve().parent
P1_DIR = HERE.parent / "freshevidencedb_p1"
sys.path.insert(0, str(P1_DIR)); sys.path.insert(0, str(HERE))
from run_p1a_real_revision import wilson_interval  # noqa: E402
from run_p1b_answer_failure import FactCorpus  # noqa: E402
from run_p3b_four_artifact import ARTIFACTS, ES_URL, PG_DSN, PG_SCHEMA, QDRANT_URL, FourStore  # noqa: E402


CONTAINERS = {"qdrant":"fresh-p3-qdrant","postgres":"fresh-p3-postgres","es":"fresh-p3-elasticsearch"}
SCENARIOS = (
    "coord_after_dense", "coord_after_sparse", "coord_after_graph", "coord_after_cache",
    "coord_after_ready", "coord_after_publish", "reorder_cache_first", "reorder_graph_first",
    "qdrant_pause", "es_pause", "qdrant_kill", "postgres_kill", "es_kill", "all_stores_kill",
)


def docker(action: str, key: str) -> None:
    if key not in CONTAINERS: raise ValueError(key)
    subprocess.run(["docker", action, CONTAINERS[key]], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def wait_services(timeout=45.0):
    deadline=time.monotonic()+timeout
    pending={"qdrant","postgres","es"}
    while pending and time.monotonic()<deadline:
        if "qdrant" in pending:
            try:
                with urlopen(f"{QDRANT_URL}/healthz",timeout=1) as r:
                    if r.status==200:pending.remove("qdrant")
            except Exception:pass
        if "postgres" in pending:
            try:
                with psycopg.connect(PG_DSN,connect_timeout=1) as c:c.execute("select 1");pending.remove("postgres")
            except Exception:pass
        if "es" in pending:
            try:
                response=requests.get(f"{ES_URL}/_cluster/health",timeout=1)
                payload=response.json() if response.status_code==200 else {}
                if payload.get("status") in ("yellow","green") and not payload.get("timed_out",False):pending.remove("es")
            except Exception:pass
        if pending:time.sleep(.1)
    if pending:raise TimeoutError(f"services not ready: {pending}")


def stage(store, facts, kind):
    {"dense":store.insert_dense,"sparse":store.insert_sparse,"graph":store.insert_graph,"cache":store.insert_cache}[kind](facts,2)


def create_journal(store, run_key):
    table=f"{PG_SCHEMA}.{run_key}_journal"
    with store.pg.cursor() as cur:
        cur.execute(f"DROP TABLE IF EXISTS {table}")
        cur.execute(f"CREATE TABLE {table}(id integer primary key,status text not null,ready text[] not null)")
        cur.execute(f"INSERT INTO {table} VALUES(1,'STAGING',ARRAY[]::text[])")
    return table


def worker(args):
    corpus=FactCorpus(args.manifest.resolve());facts=corpus.facts[args.domain]
    store=FourStore(args.run_key,corpus,args.sqlite_dir,create=False);table=f"{PG_SCHEMA}.{args.run_key}_journal"
    order=args.order.split(",")
    for index,kind in enumerate(order,1):
        stage(store,facts,kind)
        with store.pg.cursor() as cur:cur.execute(f"UPDATE {table} SET ready=array_append(ready,%s) WHERE id=1 AND NOT (%s=ANY(ready))",(kind,kind))
        if args.crash_point==f"after_{kind}" or args.crash_point==f"after_{index}":os.kill(os.getpid(),signal.SIGKILL)
    with store.pg.cursor() as cur:cur.execute(f"UPDATE {table} SET status='READY' WHERE id=1")
    if args.crash_point=="after_ready":os.kill(os.getpid(),signal.SIGKILL)
    if not store.readiness(facts):raise RuntimeError("worker readiness failed")
    with store.pg.transaction():
        store.publish(facts)
        with store.pg.cursor() as cur:cur.execute(f"UPDATE {table} SET status='PUBLISHED' WHERE id=1")
    if args.crash_point=="after_publish":os.kill(os.getpid(),signal.SIGKILL)
    store.close();return 0


def safe_close(store):
    try:store.close()
    except Exception:pass


def run_scenario(corpus, manifest, domain, scenario, sqlite_dir):
    facts=corpus.facts[domain];run_key=f"{domain}_{scenario}";store=FourStore(run_key,corpus,sqlite_dir);store.initialize(facts);create_journal(store,run_key)
    crash_start=time.perf_counter();expected_crash=True
    coord={
        "coord_after_dense":("dense,sparse,graph,cache","after_dense"),
        "coord_after_sparse":("dense,sparse,graph,cache","after_sparse"),
        "coord_after_graph":("dense,sparse,graph,cache","after_graph"),
        "coord_after_cache":("dense,sparse,graph,cache","after_cache"),
        "coord_after_ready":("dense,sparse,graph,cache","after_ready"),
        "coord_after_publish":("dense,sparse,graph,cache","after_publish"),
        "reorder_cache_first":("cache,dense,sparse,graph","after_2"),
        "reorder_graph_first":("graph,cache,sparse,dense","after_2"),
    }
    if scenario in coord:
        order,point=coord[scenario]
        cmd=[sys.executable,str(Path(__file__).resolve()),"--worker","--manifest",str(manifest),"--domain",domain,"--run-key",run_key,"--sqlite-dir",str(sqlite_dir),"--order",order,"--crash-point",point]
        result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        expected_crash=result.returncode==-signal.SIGKILL
    else:
        stage(store,facts,"dense");stage(store,facts,"sparse")
        if scenario=="qdrant_pause":
            docker("pause","qdrant")
            try:
                try:urlopen(f"{QDRANT_URL}/healthz",timeout=1);expected_crash=False
                except Exception:expected_crash=True
            finally:docker("unpause","qdrant")
        elif scenario=="es_pause":
            docker("pause","es")
            try:
                try:requests.get(f"{ES_URL}/_cluster/health",timeout=1).raise_for_status();expected_crash=False
                except Exception:expected_crash=True
            finally:docker("unpause","es")
        elif scenario.endswith("_kill"):
            targets=[scenario.removesuffix("_kill")]
            if scenario=="all_stores_kill":targets=["qdrant","postgres","es"]
            for key in targets:docker("kill",key)
            for key in targets:docker("start",key)
        else:raise ValueError(scenario)
    wait_services();safe_close(store);store=FourStore(run_key,corpus,sqlite_dir,create=False)
    restart_ms=(time.perf_counter()-crash_start)*1000
    before=store.query_rows(facts,"staged_all",0,"after_restart_before_recovery")
    recovery_start=time.perf_counter()
    for kind in ARTIFACTS:stage(store,facts,kind)
    ready=store.readiness(facts)
    if not ready:raise RuntimeError("recovery readiness failed")
    with store.pg.transaction():store.publish(facts)
    recovery_ms=(time.perf_counter()-recovery_start)*1000
    after=store.query_rows(facts,"staged_all",0,"after_recovery")
    store.gc_old(facts);gc=store.query_rows(facts,"staged_all",0,"after_gc")
    # deterministic IDs/PKs imply one logical version per artifact; audit via observed version sets.
    duplicate=0;orphan=0
    for fact in facts:
        for kind in ARTIFACTS:
            if store.versions(fact,kind,2)!={2}:duplicate+=1
            if store.versions(fact,kind,1):orphan+=1
    with store.pg.cursor() as cur:cur.execute(f"SELECT status,ready FROM {PG_SCHEMA}.{run_key}_journal WHERE id=1");journal=cur.fetchone()
    audit={"domain":domain,"scenario":scenario,"expected_failure_observed":expected_crash,"readiness_ok":ready,"restart_ms":restart_ms,"recovery_ms":recovery_ms,"snapshot_errors":sum(r["snapshot_error"] for r in before+after),"gc_errors":sum(r["snapshot_error"] for r in gc),"duplicates":duplicate,"orphans":orphan,"journal_status_before_recovery":journal[0] if journal else "MISSING","journal_ready_count":len(journal[1]) if journal else -1}
    safe_close(store);return before+after+gc,audit


def parent_main(args):
    wait_services();out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True);sqlite_dir=out/"sqlite_live";corpus=FactCorpus(args.manifest.resolve());rows=[];audits=[]
    for domain in sorted(corpus.facts):
        for scenario in SCENARIOS:
            rr,aa=run_scenario(corpus,args.manifest.resolve(),domain,scenario,sqlite_dir);rows+=rr;audits.append(aa);print(json.dumps(aa,sort_keys=True),flush=True)
    evaluated=[r for r in rows if r["checkpoint"] in ("after_restart_before_recovery","after_recovery")];errors=sum(r["snapshot_error"] for r in evaluated)
    gate=len(audits)>=20 and errors==0 and wilson_interval(errors,len(evaluated))[1]<=.01 and all(a["expected_failure_observed"] and a["readiness_ok"] and a["gc_errors"]==0 and a["duplicates"]==0 and a["orphans"]==0 for a in audits)
    result={"scenario_runs":len(audits),"snapshot_observations":len(evaluated),"snapshot_errors":errors,"snapshot_error_wilson_95ci":list(wilson_interval(errors,len(evaluated))),"gc_errors":sum(a["gc_errors"] for a in audits),"duplicates":sum(a["duplicates"] for a in audits),"orphans":sum(a["orphans"] for a in audits),"restart_p95_ms":sorted(a["restart_ms"] for a in audits)[int(.95*(len(audits)-1))],"recovery_p95_ms":sorted(a["recovery_ms"] for a in audits)[int(.95*(len(audits)-1))],"T4":"COORDINATOR_FAULT_PASS" if gate else "COORDINATOR_FAULT_FAIL"}
    with (out/"checkpoint_rows.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with (out/"fault_audits.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(audits[0]));w.writeheader();w.writerows(audits)
    (out/"aggregate.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    (out/"AUTO_REPORT.md").write_text("\n".join(["# P3-C fault 자동 보고","",f"- T4: **{result['T4']}**",f"- scenario runs: {result['scenario_runs']}",f"- snapshot observations/errors: {result['snapshot_observations']}/{errors}",f"- restart p95: {result['restart_p95_ms']:.2f}ms",f"- recovery p95: {result['recovery_p95_ms']:.2f}ms",""])+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))


def parse_args():
    p=argparse.ArgumentParser();p.add_argument("--manifest",required=True,type=Path);p.add_argument("--output-dir",type=Path);p.add_argument("--worker",action="store_true");p.add_argument("--domain");p.add_argument("--run-key");p.add_argument("--sqlite-dir",type=Path);p.add_argument("--order");p.add_argument("--crash-point");return p.parse_args()


if __name__=="__main__":
    args=parse_args();sys.exit(worker(args) if args.worker else parent_main(args))
