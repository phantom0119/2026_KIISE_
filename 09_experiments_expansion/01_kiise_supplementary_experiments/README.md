# KIISE 2026 본 논문 보강 및 확장 실험 (Supplementary Expansion Experiments)

본 디렉터리는 2026 KIISE 데이터베이스연구회 최종 논문([`05_manuscript/0_main_paper.md`](../../05_manuscript/0_main_paper.md))의 핵심 주장 및 검증을 뒷받침하는 **보강·확장 실험 정본 산출물**을 관리합니다.

---

## 📂 디렉터리 구성 및 역할

```
01_kiise_supplementary_experiments/
├── EXPANSION_RESULTS.md          # 2026-07 확장 실험 4대 과제 종합 판정 보고서
├── rag_vqa/                      # ⭐1 통제된 LLM 답변 계층 VQA 실험 (표 11 정본)
│   ├── results_full/             # 600문항 5조건 Qwen2.5 / Llama 3 실측치 및 사다리 CI 분석
│   ├── results_smoke/            # 스모크 테스트 결과
│   └── vqa_joined.parquet        # 표집 전 VRU VQA 6,000문항 결합 정본
├── reranker/                     # ⭐3 신경망 Reranker (BGE-Reranker-v2-m3) 심화 실험
│   ├── vru_accident/             # VRU-Accident facet 질의 재정렬 결과 (nDCG@10, Hit@1)
│   └── aihub_intelligent_cctv/   # AI Hub 지능형 CCTV 의미 caption 재정렬 결과
└── significance/                 # 7 통계적 엄밀성 검정 (표 5~6 등 주요 비교 6종)
    ├── significance_table.csv    # Paired Bootstrap 95% CI 및 Wilcoxon signed-rank 검정 수치
    └── significance_table.md     # 통계적 유의성 표 Markdown 버전
```

---

## 🔬 주요 실험 상세

### 1. 통제된 LLM 답변 계층 (`rag_vqa/`)
- **실행 스크립트**: [`04_scripts/06_rq6_vlm_qa_propagation/run_rag_vqa.py`](../../04_scripts/06_rq6_vlm_qa_propagation/run_rag_vqa.py)
- **논문 반영**: 본문 §5.2.6 [**표 11: 설명문 증거 조건별 VLM 답변 정확도**](../../05_manuscript/0_main_paper.md) 및 [`05_manuscript/table11_dir/`](../../05_manuscript/table11_dir/)
- **핵심 발견**:
  - LLM 모델(`Qwen2.5-7B-Instruct`, `Meta-Llama-3-8B-Instruct`)을 고정하고 DB evidence 구성만 변경(closed, distractor, vector_only, prefilter, oracle)했을 때, 검색 증거의 품질에 따라 downstream 답변 정확도가 단조 증가함을 실측으로 증명.
  - 사다리 부트스트랩 신뢰구간 분석 결과: [`results_full/ladder_ci_analysis_20260723.json`](rag_vqa/results_full/ladder_ci_analysis_20260723.json)

### 2. 신경망 Reranker 심화 실험 (`reranker/`)
- **실행 스크립트**: [`04_scripts/04_rq3_rq4_retrieval_fusion/run_reranker_selection.py`](../../04_scripts/04_rq3_rq4_retrieval_fusion/run_reranker_selection.py)
- **핵심 발견**:
  - `BAAI/bge-reranker-v2-m3` 기반 Cross-encoder 재정렬 효과는 데이터셋의 태스크 특성에 크게 의존(Task-dependent).
  - 의미 기반 서술형 질의(AI Hub 지능형 CCTV)에서는 nDCG@10이 +0.136 대폭 향상되었으나, 구조화된 facet 질의(VRU)에서는 추가 이득이 없어 "구조적 메타데이터 필터링의 필수성"을 규명함.

### 3. 통계적 유의성 검정 (`significance/`)
- **실행 스크립트**: [`04_scripts/08_verification_and_audit/run_significance_analysis.py`](../../04_scripts/08_verification_and_audit/run_significance_analysis.py)
- **핵심 발견**:
  - 논문의 주요 6대 비교(VRU/AI Hub 텍스트 B4 vs B2, 시각 M4 vs M2, Rerank 결합 vs Equal) 전 항목에서 95% CI가 0을 배제하고 Wilcoxon $p \ll 0.05$로 통계적 유의성 완전 확보.
