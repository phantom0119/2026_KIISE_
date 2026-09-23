#!/usr/bin/env python3
"""표 11 보조 분석: 무관 설명문(distractor) 이득의 범주별 분해.

입력: ../../table1_dir/data/vru_rag_vqa/rag_vqa_{qwen,llama3}.parquet
출력: percategory_closed_distractor.csv
결정적 계산(부트스트랩 없음): 범주별 정확도와 (distractor - closed) 차이.
"""
from pathlib import Path
import pandas as pd

HERE = Path(__file__).resolve().parent
SRC = HERE.parents[1] / "table1_dir" / "data" / "vru_rag_vqa"
rows = []
for model, f in [("qwen2.5-7b", "rag_vqa_qwen.parquet"), ("llama3-8b", "rag_vqa_llama3.parquet")]:
    df = pd.read_parquet(SRC / f)
    cat = df.pivot_table(index="category", columns="config", values="correct", aggfunc="mean")
    n = df[df.config == "closed"].groupby("category").size()
    for c in cat.index:
        rows.append({
            "model": model, "category": c, "n": int(n[c]),
            "closed_acc": round(cat.loc[c, "closed"], 4),
            "distractor_acc": round(cat.loc[c, "distractor"], 4),
            "gap_pp": round((cat.loc[c, "distractor"] - cat.loc[c, "closed"]) * 100, 1),
        })
out = pd.DataFrame(rows)
out.to_csv(HERE / "percategory_closed_distractor.csv", index=False)
print(out.to_string(index=False))
