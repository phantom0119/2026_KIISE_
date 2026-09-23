#!/usr/bin/env python3
"""표 10 (조건 없는 두 실측 코퍼스 물리 색인 프로파일) — data/ 사본만으로 원고 수치 전수 대조.

원고: manuscript/_archive_20260819/0_paper_script.md L303-318 (캡션 L318).
판정 규칙: 원고 인쇄 자릿수 d 에 대해 |원고값 - 원천값| <= 0.5*10^-d + 1e-9 (반올림 일치).
"""
import csv, json, pathlib

D = pathlib.Path(__file__).parent / "data"

def load(fname):
    with open(D / fname) as f:
        return list(csv.DictReader(f))

def get(rows, **cond):
    out = []
    for r in rows:
        ok = True
        for k, v in cond.items():
            cell = r.get(k, "")
            if v is None:
                ok &= (cell == "" or cell is None)
            else:
                ok &= (cell not in ("", None) and float(cell) == v)
        if ok:
            out.append(r)
    assert len(out) == 1, (cond, len(out))
    return out[0]

def dec(s):  # 인쇄 소수 자릿수
    return len(s.split(".")[1]) if "." in s else 0

sin = [r for r in load("index_benchmark_from_log.csv") if r["N"] == "131000"]
crx = [r for r in load("index_benchmark.csv") if r["N"] == "142000"]

def sel(rows, kind, **kw):
    return get([r for r in rows if r["kind"] == kind], **kw)

# (라벨, 행선택, 원고값[recall, p50, p95, build, mb] — 원고 인쇄 문자열 그대로)
CASES = [
    ("시내도로 Flat",              sel(sin, "flat"),                              ["1.0000", "13.43", "14.37", "0.11", "268.0"]),
    ("시내도로 HNSW(M=16)",        sel(sin, "hnsw", M=16, efSearch=64),           ["0.9970", "0.041", "0.055", "34.8", "287.0"]),
    ("시내도로 HNSW(M=32)",        sel(sin, "hnsw", M=32, efSearch=64),           ["0.9970", "0.044", "0.062", "36.5", "304.0"]),
    ("시내도로 IVF-Flat(np=8)",    sel(sin, "ivfflat", nlist=1024, nprobe=8),     ["0.9940", "0.113", "0.144", "13.9", "271.0"]),
    ("시내도로 IVF-PQ(m=64,np=8)", sel(sin, "ivfpq", m=64, nprobe=8),             ["0.4810", "0.135", "0.158", "26.1", "12.0"]),
    ("시내도로 IVF-PQ(m=32,np=8)", sel(sin, "ivfpq", m=32, nprobe=8),             ["0.3340", "0.129", "0.153", "25.9", "8.0"]),
    ("교차로 Flat",                sel(crx, "flat"),                              ["1.0000", "14.18", "15.34", "0.12", "290.8"]),
    ("교차로 HNSW(M=16)",          sel(crx, "hnsw", M=16, efSearch=64),           ["0.9994", "0.044", "0.061", "44.3", "311.3"]),
    ("교차로 HNSW(M=32)",          sel(crx, "hnsw", M=32, efSearch=64),           ["0.9992", "0.047", "0.069", "47.1", "329.5"]),
    ("교차로 IVF-Flat(np=8)",      sel(crx, "ivfflat", nlist=1024, nprobe=8),     ["0.9971", "0.116", "0.165", "15.1", "294.1"]),
    ("교차로 IVF-PQ(m=64,np=8)",   sel(crx, "ivfpq", m=64, nprobe=8),             ["0.4938", "0.134", "0.172", "27.9", "12.9"]),
    ("교차로 IVF-PQ(m=32,np=8)",   sel(crx, "ivfpq", m=32, nprobe=8),             ["0.3489", "0.131", "0.157", "27.1", "8.3"]),
]
COLS = ["recall_at_10", "p50_ms", "p95_ms", "build_s", "index_mb"]

npass = nfail = 0
for label, row, ms_vals in CASES:
    for col, ms in zip(COLS, ms_vals):
        src = float(row[col])
        tol = 0.5 * 10 ** (-dec(ms)) + 1e-9
        ok = abs(float(ms) - src) <= tol
        npass += ok; nfail += (not ok)
        print(f"{'PASS' if ok else 'FAIL'} {label:28s} {col:12s} 원고={ms:>7s} 원천={row[col]:>8s}")

# 캡션 규모 수치
mani = json.load(open(D / "manifest.json"))
for name, cond in [("교차로 원본 풀 143,830", mani["n_vectors"] == 143830),
                   ("교차로 고정 규모 142,000 (manifest.scales)", 142000 in mani["scales"]),
                   ("교차로 CSV N=142000 행 존재", len(crx) > 0),
                   ("시내도로 CSV N=131000 행 존재", len(sin) > 0),
                   ("시내도로 원본 풀 132,521 (600_RESULTS 문서 기재)",
                    "132,521" in open(D / "600_RESULTS_index_structure_benchmark_20260709.md").read())]:
    ok = bool(cond); npass += ok; nfail += (not ok)
    print(f"{'PASS' if ok else 'FAIL'} 캡션: {name}")

print(f"\nTOTAL PASS={npass} FAIL={nfail}")
