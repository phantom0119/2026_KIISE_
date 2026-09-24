#!/usr/bin/env python3
"""P3-B: four-artifact publication safety and cost comparison."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sqlite3
import statistics
import sys
import time
import uuid
from pathlib import Path
from typing import Sequence

import psycopg
from elasticsearch import Elasticsearch, helpers
from qdrant_client import QdrantClient, models


P1_DIR = Path(__file__).resolve().parent.parent / "freshevidencedb_p1"
sys.path.insert(0, str(P1_DIR))
from run_p1a_real_revision import VECTOR_SIZE, percentile, wilson_interval  # noqa: E402
from run_p1b_answer_failure import Fact, FactCorpus  # noqa: E402


PG_DSN = "host=127.0.0.1 port=15435 dbname=freshp3 user=freshp3 password=freshp3"
QDRANT_URL = "http://127.0.0.1:17333"
ES_URL = "http://127.0.0.1:19201"
PG_SCHEMA = "fresh_p3b"
PROTOCOLS = ("eager", "read_filter", "staged_all", "pg_atomic_all")
REPEATS = 3
ARTIFACTS = ("dense", "sparse", "graph", "cache")


class FourStore:
    def __init__(self, run_key: str, corpus: FactCorpus, sqlite_dir: Path, pg_only: bool = False, create: bool = True) -> None:
        if not re.fullmatch(r"[a-z0-9_]+", run_key): raise ValueError(run_key)
        self.run_key = run_key; self.corpus = corpus; self.pg_only = pg_only
        self.collection = f"fresh_p3b_{run_key}"
        self.index = f"fresh-p3b-{run_key.replace('_', '-') }"
        self.manifest = f"{PG_SCHEMA}.{run_key}_manifest"
        self.sparse = f"{PG_SCHEMA}.{run_key}_sparse"
        self.atomic = f"{PG_SCHEMA}.{run_key}_atomic"
        self.pg = psycopg.connect(PG_DSN, autocommit=True)
        self.qdrant = None if pg_only else QdrantClient(url=QDRANT_URL, timeout=30)
        self.es = None if pg_only else Elasticsearch(ES_URL, request_timeout=30)
        sqlite_dir.mkdir(parents=True, exist_ok=True)
        self.cache_path = sqlite_dir / f"{run_key}.sqlite"
        if create and self.cache_path.exists(): self.cache_path.unlink()
        self.cache = sqlite3.connect(self.cache_path)
        self.cache.execute("PRAGMA journal_mode=WAL"); self.cache.execute("PRAGMA synchronous=FULL")
        if create:
            self._create()

    def _create(self) -> None:
        with self.pg.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {PG_SCHEMA}")
            for table in (self.atomic, self.sparse, self.manifest): cur.execute(f"DROP TABLE IF EXISTS {table}")
            cur.execute(f"CREATE TABLE {self.manifest}(doc_id integer primary key,active_version integer not null,epoch integer not null)")
            cur.execute(f"CREATE TABLE {self.sparse}(doc_id integer,version integer,epoch integer,text text,primary key(doc_id,version,epoch))")
            cur.execute(f"CREATE TABLE {self.atomic}(doc_id integer,version integer,epoch integer,type text,payload text,primary key(doc_id,version,epoch,type))")
        self.cache.execute("CREATE TABLE artifacts(doc_id integer,version integer,epoch integer,payload text,primary key(doc_id,version,epoch))")
        self.cache.commit()
        if self.pg_only: return
        existing = {x.name for x in self.qdrant.get_collections().collections}
        if self.collection in existing: self.qdrant.delete_collection(self.collection)
        self.qdrant.create_collection(self.collection, vectors_config=models.VectorParams(size=VECTOR_SIZE, distance=models.Distance.COSINE))
        for field in ("doc_id", "version", "epoch"):
            self.qdrant.create_payload_index(self.collection, field, models.PayloadSchemaType.INTEGER, wait=True)
        if self.es.indices.exists(index=self.index): self.es.indices.delete(index=self.index)
        self.es.indices.create(index=self.index, mappings={"properties": {"doc_id":{"type":"integer"},"version":{"type":"integer"},"epoch":{"type":"integer"},"payload":{"type":"text"}}})

    def close(self) -> None:
        self.cache.close(); self.pg.close()
        if self.qdrant is not None: self.qdrant.close()
        if self.es is not None: self.es.close()

    def initialize(self, facts: Sequence[Fact]) -> None:
        with self.pg.transaction():
            with self.pg.cursor() as cur: cur.executemany(f"INSERT INTO {self.manifest} VALUES(%s,1,0)", [(f.fact_id,) for f in facts])
        if self.pg_only:
            self.insert_atomic_rows(facts, 1, connection=self.pg); return
        self.insert_dense(facts, 1); self.insert_sparse(facts, 1); self.insert_graph(facts, 1); self.insert_cache(facts, 1)

    def insert_dense(self, facts: Sequence[Fact], version: int) -> None:
        texts = [f.doc.old_chunks[0] if version == 1 else f.doc.new_chunks[0] for f in facts]
        vectors = self.corpus.embed([f"{f.doc.probe} {t}" for f,t in zip(facts,texts)])
        points=[]
        for fact,text,vector in zip(facts,texts,vectors):
            points.append(models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL,f"{self.run_key}:dense:{fact.fact_id}:{version}")),vector=vector.tolist(),payload={"doc_id":fact.fact_id,"version":version,"epoch":version-1,"text":text}))
        self.qdrant.upsert(self.collection, points=points, wait=True)

    def insert_sparse(self, facts: Sequence[Fact], version: int) -> None:
        rows=[(f.fact_id,version,version-1,f.doc.old_chunks[0] if version==1 else f.doc.new_chunks[0]) for f in facts]
        with self.pg.transaction():
            with self.pg.cursor() as cur: cur.executemany(f"INSERT INTO {self.sparse} VALUES(%s,%s,%s,%s) ON CONFLICT(doc_id,version,epoch) DO UPDATE SET text=excluded.text",rows)

    def insert_graph(self, facts: Sequence[Fact], version: int) -> None:
        actions=[]
        for fact in facts:
            payload=f"source:{fact.fact_id}->answer:{fact.old_answer if version==1 else fact.new_answer}"
            actions.append({"_index":self.index,"_id":f"{fact.fact_id}-{version}","_source":{"doc_id":fact.fact_id,"version":version,"epoch":version-1,"payload":payload}})
        helpers.bulk(self.es,actions,refresh="wait_for")

    def insert_cache(self, facts: Sequence[Fact], version: int) -> None:
        rows=[(f.fact_id,version,version-1,json.dumps({"answer":f.old_answer if version==1 else f.new_answer},sort_keys=True)) for f in facts]
        self.cache.executemany("INSERT INTO artifacts VALUES(?,?,?,?) ON CONFLICT(doc_id,version,epoch) DO UPDATE SET payload=excluded.payload",rows);self.cache.commit()

    def insert_atomic_rows(self, facts: Sequence[Fact], version: int, connection) -> None:
        rows=[]
        for fact in facts:
            text=fact.doc.old_chunks[0] if version==1 else fact.doc.new_chunks[0]
            answer=fact.old_answer if version==1 else fact.new_answer
            for kind,payload in (("dense",text),("sparse",text),("graph",f"source:{fact.fact_id}->answer:{answer}"),("cache",json.dumps({"answer":answer},sort_keys=True))):
                rows.append((fact.fact_id,version,version-1,kind,payload))
        with connection.cursor() as cur:
            cur.executemany(f"INSERT INTO {self.atomic} VALUES(%s,%s,%s,%s,%s) ON CONFLICT(doc_id,version,epoch,type) DO UPDATE SET payload=excluded.payload",rows)

    def publish(self, facts: Sequence[Fact], connection=None) -> None:
        conn=connection or self.pg
        with conn.cursor() as cur: cur.executemany(f"UPDATE {self.manifest} SET active_version=2,epoch=1 WHERE doc_id=%s",[(f.fact_id,) for f in facts])

    def versions(self, fact: Fact, kind: str, version_filter):
        if self.pg_only:
            sql=f"SELECT version FROM {self.atomic} WHERE doc_id=%s AND type=%s";params=[fact.fact_id,kind]
            if version_filter is not None: sql+=" AND version=%s";params.append(version_filter)
            with self.pg.cursor() as cur: cur.execute(sql,params);return {int(x[0]) for x in cur.fetchall()}
        if kind=="dense":
            must=[models.FieldCondition(key="doc_id",match=models.MatchValue(value=fact.fact_id))]
            if version_filter is not None: must.append(models.FieldCondition(key="version",match=models.MatchValue(value=version_filter)))
            filt=models.Filter(must=must);return {int(p.payload["version"]) for p in self.qdrant.scroll(self.collection,scroll_filter=filt,limit=10,with_payload=True,with_vectors=False)[0]}
        if kind=="sparse":
            sql=f"SELECT version FROM {self.sparse} WHERE doc_id=%s";params=[fact.fact_id]
            if version_filter is not None: sql+=" AND version=%s";params.append(version_filter)
            with self.pg.cursor() as cur: cur.execute(sql,params);return {int(x[0]) for x in cur.fetchall()}
        if kind=="graph":
            filters=[{"term":{"doc_id":fact.fact_id}}]
            if version_filter is not None: filters.append({"term":{"version":version_filter}})
            response=self.es.search(index=self.index,size=10,query={"bool":{"filter":filters}},source=["version"])
            return {int(hit["_source"]["version"]) for hit in response["hits"]["hits"]}
        sql="SELECT version FROM artifacts WHERE doc_id=?";params=[fact.fact_id]
        if version_filter is not None: sql+=" AND version=?";params.append(version_filter)
        return {int(x[0]) for x in self.cache.execute(sql,params).fetchall()}

    def active(self, fact: Fact) -> int:
        with self.pg.cursor() as cur: cur.execute(f"SELECT active_version FROM {self.manifest} WHERE doc_id=%s",(fact.fact_id,));return int(cur.fetchone()[0])

    def readiness(self, facts: Sequence[Fact]) -> bool:
        return all(all(self.versions(fact,kind,2)=={2} for kind in ARTIFACTS) for fact in facts)

    def query_rows(self, facts: Sequence[Fact], protocol: str, repeat: int, checkpoint: str):
        output=[]
        for fact in facts:
            active=self.active(fact);vf=active if protocol in ("read_filter","staged_all","pg_atomic_all") else None
            observed={kind:self.versions(fact,kind,vf) for kind in ARTIFACTS}
            correct=all(values=={active} for values in observed.values())
            output.append({"domain":fact.domain,"protocol":protocol,"repeat":repeat,"checkpoint":checkpoint,"fact_id":fact.fact_id,"active_version":active,**{f"{k}_versions":";".join(map(str,sorted(v))) for k,v in observed.items()},"snapshot_error":int(not correct),"graph_error":int(observed['graph']!={active}),"cache_error":int(observed['cache']!={active})})
        return output

    def gc_old(self, facts: Sequence[Fact]) -> None:
        ids=[f.fact_id for f in facts]
        if self.pg_only:
            with self.pg.transaction():
                with self.pg.cursor() as cur:cur.execute(f"DELETE FROM {self.atomic} WHERE doc_id=ANY(%s) AND version=1",(ids,))
            return
        filt=models.Filter(must=[models.FieldCondition(key="doc_id",match=models.MatchAny(any=ids)),models.FieldCondition(key="version",match=models.MatchValue(value=1))])
        self.qdrant.delete(self.collection,models.FilterSelector(filter=filt),wait=True)
        with self.pg.transaction():
            with self.pg.cursor() as cur:cur.execute(f"DELETE FROM {self.sparse} WHERE doc_id=ANY(%s) AND version=1",(ids,))
        self.es.delete_by_query(index=self.index,query={"term":{"version":1}},refresh=True)
        self.cache.execute("DELETE FROM artifacts WHERE version=1");self.cache.commit()


def run_one(corpus: FactCorpus, domain: str, protocol: str, repeat: int, sqlite_dir: Path):
    facts=corpus.facts[domain];store=FourStore(f"{domain}_{protocol}_r{repeat}",corpus,sqlite_dir,pg_only=protocol=="pg_atomic_all")
    store.initialize(facts); rows=store.query_rows(facts,protocol,repeat,"initial")
    start=time.perf_counter();readiness=True
    if protocol in ("eager","read_filter"):
        with store.pg.transaction():store.publish(facts)
        rows+=store.query_rows(facts,protocol,repeat,"manifest_published")
        for kind,fn in (("dense",store.insert_dense),("sparse",store.insert_sparse),("graph",store.insert_graph),("cache",store.insert_cache)):
            fn(facts,2);rows+=store.query_rows(facts,protocol,repeat,f"{kind}_inserted")
        update_ms=(time.perf_counter()-start)*1000
        store.gc_old(facts);rows+=store.query_rows(facts,protocol,repeat,"old_gc")
    elif protocol=="staged_all":
        for kind,fn in (("dense",store.insert_dense),("sparse",store.insert_sparse),("graph",store.insert_graph),("cache",store.insert_cache)):
            fn(facts,2);rows+=store.query_rows(facts,protocol,repeat,f"{kind}_staged")
        readiness=store.readiness(facts);rows+=store.query_rows(facts,protocol,repeat,"readiness_checked")
        if not readiness:raise RuntimeError("readiness failed")
        with store.pg.transaction():store.publish(facts)
        update_ms=(time.perf_counter()-start)*1000
        rows+=store.query_rows(facts,protocol,repeat,"manifest_published")
        store.gc_old(facts);rows+=store.query_rows(facts,protocol,repeat,"old_gc")
    else:
        with store.pg.transaction():
            store.insert_atomic_rows(facts,2,store.pg);store.publish(facts,store.pg);store.pg.execute(f"DELETE FROM {store.atomic} WHERE version=1")
        update_ms=(time.perf_counter()-start)*1000
        rows+=store.query_rows(facts,protocol,repeat,"atomic_committed")
    logical_bytes=sum(len(f.doc.old_chunks[0])+len(f.doc.new_chunks[0])+len(f.old_answer)+len(f.new_answer) for f in facts)*4
    summary={"domain":domain,"protocol":protocol,"repeat":repeat,"observations":len(rows),"errors":sum(r["snapshot_error"] for r in rows),"error_rate":sum(r["snapshot_error"] for r in rows)/len(rows),"graph_errors":sum(r["graph_error"] for r in rows),"cache_errors":sum(r["cache_error"] for r in rows),"readiness_ok":readiness,"update_ms":update_ms,"logical_bytes":logical_bytes,"writes":len(facts)*9}
    store.close();return rows,summary


def main():
    parser=argparse.ArgumentParser();parser.add_argument("--manifest",required=True,type=Path);parser.add_argument("--trace-aggregate",type=Path);parser.add_argument("--output-dir",required=True,type=Path);args=parser.parse_args()
    out=args.output_dir.resolve();out.mkdir(parents=True,exist_ok=True);corpus=FactCorpus(args.manifest.resolve());rows=[];summaries=[]
    for domain in sorted(corpus.facts):
        for protocol in PROTOCOLS:
            for repeat in range(REPEATS):
                r,s=run_one(corpus,domain,protocol,repeat,out/"sqlite_live");rows+=r;summaries.append(s);print(json.dumps(s,sort_keys=True),flush=True)
    agg={}
    for domain in sorted(corpus.facts):
        agg[domain]={}
        for protocol in PROTOCOLS:
            rr=[r for r in rows if r["domain"]==domain and r["protocol"]==protocol];ss=[s for s in summaries if s["domain"]==domain and s["protocol"]==protocol];errors=sum(r["snapshot_error"] for r in rr)
            agg[domain][protocol]={"observations":len(rr),"errors":errors,"error_rate":errors/len(rr),"error_wilson_95ci":list(wilson_interval(errors,len(rr))),"graph_errors":sum(r["graph_error"] for r in rr),"cache_errors":sum(r["cache_error"] for r in rr),"readiness_all_ok":all(s["readiness_ok"] for s in ss),"update_p50_ms":statistics.median(s["update_ms"] for s in ss),"update_p95_ms":percentile([s["update_ms"] for s in ss],.95)}
    t2=all((agg[d]["eager"]["error_rate"]>=.05 or agg[d]["read_filter"]["error_rate"]>=.05) and agg[d]["staged_all"]["errors"]==0 and agg[d]["staged_all"]["error_wilson_95ci"][1]<=.01 and agg[d]["staged_all"]["graph_errors"]==0 and agg[d]["staged_all"]["cache_errors"]==0 and agg[d]["staged_all"]["readiness_all_ok"] and agg[d]["pg_atomic_all"]["errors"]==0 for d in agg)
    ratios={d:agg[d]["staged_all"]["update_p95_ms"]/max(.001,agg[d]["pg_atomic_all"]["update_p95_ms"]) for d in agg};t3=max(ratios.values())<=10
    policy=[]
    if args.trace_aggregate and args.trace_aggregate.exists():
        trace=json.loads(args.trace_aggregate.read_text());delta_s=statistics.mean(max(0,agg[d]["staged_all"]["update_p50_ms"]-agg[d]["pg_atomic_all"]["update_p50_ms"])/1000 for d in agg)
        for page in trace["pages"]:
            expected=page["expected_unsafe_observations_year"];added=page["revisions"]*delta_s
            policy.append({"page":page["page"],"expected_errors_year":expected,"added_publish_lag_seconds_year":added,"break_even_error_cost_per_publish_second":None if expected==0 else added/expected})
    result={"aggregate":agg,"cost_ratios_staged_vs_pg":ratios,"policy":policy,"T2":"FOUR_ARTIFACT_SAFETY_PASS" if t2 else "FOUR_ARTIFACT_SAFETY_FAIL","T3":"CROSS_STORE_COST_FEASIBLE" if t3 else "INTEGRATED_DB_PREFERRED"}
    with (out/"checkpoint_rows.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    with (out/"repeat_summary.csv").open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(summaries[0]));w.writeheader();w.writerows(summaries)
    (out/"aggregate.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    lines=["# P3-B 4-artifact 자동 보고","",f"- T2: **{result['T2']}**",f"- T3: **{result['T3']}**","","| domain | protocol | error | update p95 ms |","|---|---|---:|---:|"]
    for d in agg:
        for p in PROTOCOLS:lines.append(f"| {d} | {p} | {agg[d][p]['error_rate']:.3f} | {agg[d][p]['update_p95_ms']:.2f} |")
    (out/"AUTO_REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8");print(json.dumps({"T2":result["T2"],"T3":result["T3"]},sort_keys=True))


if __name__=="__main__":main()
