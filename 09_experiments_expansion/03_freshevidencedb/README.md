# FreshEvidenceDB — 문서 개정 신선도 및 장애 복원력 벡터 DB 연구

본 디렉터리는 지식 베이스의 빈번한 문서 개정(Revision) 및 비정상 노출·서버 장애 상황에서 벡터 데이터베이스의 **검색 신선도(Freshness)**, **일관성(Consistency)**, **장애 복원력(Fault-tolerance)**을 정량적으로 평가하고 해결하기 위한 연구 산출물을 관리합니다.

---

## 📂 디렉터리 구성 및 역할

```
03_freshevidencedb/
├── FreshEvidenceDB.md            # 시스템 개요, 아키텍처 및 연구 질문(RQ) 명세서
├── freshevidencedb_p0/           # P0: 장애 재현 (Failure Reproduction)
│   ├── P0_FAILURE_REPRODUCTION_PREREGISTRATION.md
│   ├── P0_FAILURE_REPRODUCTION_FINAL_REPORT_20260807.md
│   ├── run_failure_reproduction.py
│   └── results_run1 ~ run3/      # 오래된 스냅샷 노출, 개정 누락 결함 재현 로그
├── freshevidencedb_p1/           # P1: 실환경 문서 개정 및 답변 실패 (Real Revision & Answer Failure)
│   ├── P1A_REAL_REVISION_CROSS_ENGINE_PREREGISTRATION.md
│   ├── P1B_ANSWER_FAILURE_PREREGISTRATION.md
│   ├── run_p1a_real_revision.py  # Kubernetes / Flask 실제 git 커밋 개정 추적
│   ├── run_p1b_answer_failure.py # 개정 지연으로 인한 LLM 환각/답변 실패 측정
│   ├── results_run1/             # 교차 엔진(pgvector, Qdrant, Milvus) 평가 결과
│   └── results_p1b_run1/         # 실제 QA 실패 및 신선도 감사 로그
├── freshevidencedb_p2/           # P2: 다중 백엔드 노출, 장애 주입 및 모델 테스트
│   ├── P2_PREREGISTRATION_20260807.md
│   ├── P2_FINAL_REPORT_20260807.md
│   ├── run_p2a_exposure.py       # 노출 창(Exposure Window) 측정
│   ├── run_p2b_weaviate.py       # Weaviate 실시간 개정 파이프라인
│   ├── run_p2c_server_fault.py   # 서버 비정상 재기동 및 crash-recovery 테스트
│   └── run_p2d_model.py          # 임베딩 모델 변경에 따른 재색인 비용 평가
└── freshevidencedb_p3/           # P3: 실환경 트레이스(Wikimedia) 및 대규모 자연어 QA
    ├── P3_FINAL_REPORT_20260807.md
    ├── run_p3a_wikimedia_trace.py # Wikimedia 실제 편집 스트림 트레이스 재생
    ├── run_p3b_four_artifact.py   # 4대 아티팩트 결합 평가
    ├── run_p3c_faults.py          # 장애 내구성 감사
    ├── build_p3e_natural_qa.py    # 자연어 QA 벤치마크 생성
    └── results_p3c ~ p3e/         # 체크포인트 및 집계 보고서
```

---

## 🔬 핵심 연구 기여 및 성과
1. **신선도 결함의 정량화**: 색인 비동기 빌드 중 오래된 벡터(Stale vector) 반환율 및 일관성 위반 창(Exposure Window)을 최초로 정량 실측.
2. **교차 엔진 벤치마크**: PostgreSQL(pgvector), Weaviate, SQLite 등 주요 엔진 간 실시간 개정 흡수율 및 복구 시간 비교.
3. **다운스트림 영향 검증**: 색인 신선도 지연이 RAG 답변의 사실 오류(Factuality Error)로 직결되는 현상을 실환경 Git 문서 개정 데이터를 통해 실증.
