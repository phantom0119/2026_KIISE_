#!/usr/bin/env python3
"""Build a deterministic agent-curated, explicitly not-human-reviewed QA sheet."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


EXCLUDE = {
    "flask": {1, 2, 8, 21, 22},
    "kubernetes": {0, 13, 14, 15, 17, 18, 19},
}


def main():
    p=argparse.ArgumentParser();p.add_argument("--manifest",required=True,type=Path);p.add_argument("--output",required=True,type=Path);args=p.parse_args()
    source=json.loads(args.manifest.read_text(encoding="utf-8"));rows=[]
    for domain,data in source["domains"].items():
        for fact in data["facts"]:
            if fact["fact_id"] in EXCLUDE.get(domain,set()):continue
            natural=(
                f"In the current version of `{fact['path']}`, the documentation contains the following passage "
                f"with one exact span omitted. What text belongs in the blank?\n\n{fact['question']}"
            )
            rows.append({
                "qa_id":f"{domain}-{fact['fact_id']:02d}","domain":domain,"fact_id":fact["fact_id"],
                "path":fact["path"],"question":natural,"old_answer":fact["old_answer"],"new_answer":fact["new_answer"],
                "old_evidence":fact["old_evidence"],"new_evidence":fact["new_evidence"],
                "agent_quality_checked":True,"human_reviewed":False,"human_reviewer":"","human_notes":"",
            })
    if len(rows)<30:raise RuntimeError(f"only {len(rows)} quality-filtered QA")
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    meta={"qa_count":len(rows),"human_reviewed":0,"status":"AGENT_CURATED_HUMAN_REVIEW_PENDING","exclusion_ids":{k:sorted(v) for k,v in EXCLUDE.items()}}
    args.output.with_suffix(".json").write_text(json.dumps(meta,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps(meta,sort_keys=True))


if __name__=="__main__":main()
