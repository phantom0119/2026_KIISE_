#!/usr/bin/env python3
"""P0 CPU pilot / F0: asset audit — sizes, SHA-256, licenses, schema probes.

Streams large files (chunked hashing, no full load) per the v1.1 constraint.
Writes manifests/source_manifest.json + results/asset_audit.json.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path

P0 = Path(__file__).resolve().parents[1]
DATA = Path("/hdd2/KIISE_datasociety/Datasets/graphrag_p0_data")
EXPECTED = {  # byte sizes verified from provider APIs 2026-08-06
    "primekg/kg.csv": 981_751_236,
    "primekg/nodes.tab": 8_893_757,
    "primekg/drug_features.tab": 10_030_011,
    "primekg/disease_features.tab": 113_534_270,
    "stark_amazon/processed.zip": 3_524_776_983,
}
LICENSES = {
    "primekg": {"data": "CC0 1.0", "source": "Harvard Dataverse doi:10.7910/DVN/IXA7BM v2.1",
                "code": "MIT (github.com/mims-harvard/PrimeKG)"},
    "stark_amazon": {"data": "CC-BY-4.0", "source": "HF snap-stanford/stark skb/amazon",
                     "code": "MIT (github.com/snap-stanford/stark)"},
}


def sha256_stream(path: Path, chunk: int = 1 << 22) -> tuple[str, int]:
    h, n = hashlib.sha256(), 0
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
            n += len(b)
    return h.hexdigest(), n


def probe_primekg(path: Path, n: int = 5) -> dict:
    with open(path, newline="") as f:
        r = csv.reader(f)
        header = next(r)
        rows = [next(r) for _ in range(n)]
    return {"header": header, "sample_rows": rows}


def count_lines(path: Path) -> int:
    n = 0
    with open(path, "rb") as f:
        while True:
            b = f.read(1 << 22)
            if not b:
                break
            n += b.count(b"\n")
    return n


def probe_zip(path: Path) -> dict:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        infos = [{"name": i.filename, "size": i.file_size} for i in z.infolist()[:40]]
    return {"n_entries": len(names), "entries_head": infos}


def main() -> int:
    t0 = time.time()
    out = {"generated": "2026-08-06", "gate": "F0", "files": [], "licenses": LICENSES}
    complete = True
    for rel, exp in EXPECTED.items():
        p = DATA / rel
        rec = {"path": str(p), "expected_bytes": exp}
        if not p.exists():
            rec.update(status="MISSING")
            complete = False
        else:
            actual = p.stat().st_size
            rec["actual_bytes"] = actual
            rec["size_match"] = (actual == exp)
            if actual != exp:
                rec["status"] = "INCOMPLETE"
                complete = False
            else:
                digest, _ = sha256_stream(p)
                rec.update(status="OK", sha256=digest)
                if rel.endswith("kg.csv"):
                    rec["schema"] = probe_primekg(p)
                    rec["n_lines"] = count_lines(p)
                elif rel.endswith(".zip"):
                    rec["zip"] = probe_zip(p)
        out["files"].append(rec)
    out["all_complete"] = complete
    out["wall_s"] = round(time.time() - t0, 1)
    (P0 / "results").mkdir(exist_ok=True)
    (P0 / "manifests").mkdir(exist_ok=True)
    (P0 / "results" / "asset_audit.json").write_text(json.dumps(out, indent=2))
    (P0 / "manifests" / "source_manifest.json").write_text(json.dumps(
        {"files": [{k: r.get(k) for k in ("path", "actual_bytes", "sha256", "status")}
                   for r in out["files"]], "licenses": LICENSES}, indent=2))
    print(json.dumps({"all_complete": complete, "wall_s": out["wall_s"],
                      "statuses": {r["path"].split("/")[-1]: r["status"] for r in out["files"]}},
                     indent=2))
    return 0 if complete else 1


if __name__ == "__main__":
    raise SystemExit(main())
