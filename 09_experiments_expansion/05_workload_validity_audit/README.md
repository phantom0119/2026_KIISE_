# 워크로드 유효성 및 난이도 감사 (Workload Validity & Hardness Audit)

본 디렉터리는 벡터 유사도 검색 및 하이브리드 필터링 워크로드에서 발생할 수 있는 **인위적 편향(Artificial Bias)**과 **난이도 불균형(Hardness Imbalance)**을 통제하고, 공정한 비교 기준을 정립하기 위한 감사 파이프라인(`p0_validity_audit`)을 관리합니다.

---

## 📂 디렉터리 구성 및 역할

```
05_workload_validity_audit/
└── p0_validity_audit/
    ├── G1_DECISION_RULE.md      # 워크로드 수락/기각 의사결정 규칙 정본
    ├── P0_PLAN.md               # 감사 실행 계획 및 세부 가설
    ├── P0_CONCLUSION.md         # 감사 최종 결론 및 데이터셋 적합성 판정
    ├── scripts/                 # 유효성 감사 및 특성 분석 스크립트
    │   ├── w1_compute_workload_features.py  # 술어/페어 단위 난이도 특성 계산
    │   ├── g1_prep_hcbgen_inputs.py         # HCBGen 벤치마크 입력 벡터 및 페이로드 생성
    │   ├── g1_run_methods.py                # 자연 난이도 vs 매칭 난이도 검색 실행
    │   ├── g1_analyze.py                    # 결과 집계 및 재현율(Recall) 통계 분석
    │   └── g1_hcbgen_chain.sh               # 전체 감사 파이프라인 자동화 쉘스크립트
    ├── g1/                      # A/B 워크로드별 실험 데이터 및 결과 보고서
    │   ├── G1_REPORT.md         # G1 종합 감사 보고서
    │   ├── g1_stats.json        # 통계 요약 지표
    │   ├── A/                   # 워크로드 A (자연 분포, 매칭 분포, 페이로드, 재현율)
    │   └── B/                   # 워크로드 B (자연 분포, 매칭 분포, 페이로드, 재현율)
    └── w1_features/             # W1 워크로드 특성 분석 산출물
        ├── FIRST_LOOK.md        # 1차 탐색적 분석 요약
        ├── summary_A.json / B.json
        └── pair_features_*.parquet
```

---

## 🔬 핵심 분석 내용
1. **자연 난이도 vs 매칭 난이도 (Natural vs Matched Hardness)**:
   - 질의-문서 간 임베딩 거리 및 필터 선택도(Selectivity)가 특정 검색 기법에 유리하게 왜곡되지 않도록 난이도 분포를 매칭하여 재검증.
2. **G1 의사결정 규칙 적용**:
   - 워크로드 간 재현율 차이가 실제 알고리즘의 우위인지, 아니면 워크로드 자체의 난이도 편차에서 기인한 것인지를 통계적으로 분리 검정.
