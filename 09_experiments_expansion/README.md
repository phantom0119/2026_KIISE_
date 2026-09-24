# 09_experiments_expansion — 확장 연구 과제 및 차기 연구 포트폴리오

본 디렉터리는 2026 KIISE 데이터베이스연구회 본 논문의 검증을 완성하는 **보강 실험군**과, 향후 최상위 학술대회(VLDB, SIGMOD, ICDE 등) 투고를 위해 기획 및 프로토타이핑된 **차기 연구 과제 포트폴리오**를 통합 관리하는 연구 확장 아카이브입니다.

---

## 📂 5대 핵심 연구 테마 구조

```
09_experiments_expansion/
├── 01_kiise_supplementary_experiments/   # [테마 1] KIISE 본 논문 보강/확장 실험 (VQA 답변 계층, Reranker, 통계 검정)
├── 02_followup_topic_proposals/          # [테마 2] 차기 연구 기획, 대안 포트폴리오 및 학술대회 제안서
├── 03_freshevidencedb/                   # [테마 3] FreshEvidenceDB: 실시간 문서 개정 신선도 및 장애 복원력 연구
├── 04_multimodal_intent_and_graphrag/    # [테마 4] 도메인 특화 증거 뷰 저장(EvidenceViewDB, IntentStore) 및 GraphRAG
├── 05_workload_validity_audit/           # [테마 5] 워크로드 유효성 감사 및 난이도 통제 파이프라인
└── README.md                             # 본 마스터 인덱스 문서
```

---

## 📑 테마별 상세 가이드

### 1. [01_kiise_supplementary_experiments/](01_kiise_supplementary_experiments/)
- **역할**: KIISE 2026 본 논문([`05_manuscript/0_main_paper.md`](../05_manuscript/0_main_paper.md)) 수록 데이터 정본
- **주요 내용**:
  - `rag_vqa/`: LLM 답변 계층 VQA 실험 (Qwen2.5 / Llama 3 5대 조건 실측치, 표 11 정본)
  - `reranker/`: Cross-encoder (BGE-Reranker-v2-m3) 태스크 의존적 재정렬 효과 심화
  - `significance/`: 6대 주요 비교군 대상 부트스트랩 95% CI 및 Wilcoxon signed-rank 검정 표
  - `EXPANSION_RESULTS.md`: 2026-07 기준 확장 실험 종합 판정 보고서

### 2. [02_followup_topic_proposals/](02_followup_topic_proposals/)
- **역할**: 차기 최상위 학술대회(VLDB/SIGMOD/ICDE) 투고 제안서 및 청사진
- **주요 내용**:
  - `CONFERENCE_TOPIC_PROPOSAL_20260804.md`: 차기 학술대회 연구 트랙 종합 제안서
  - `ALT_TOPICS_PORTFOLIO_20260805.md`: 대안 연구 주제군 포트폴리오 및 타당성 비교
  - `TOPIC_REORGANIZATION_20260807.md`: 연구 주제 재편성 및 통합 로드맵
  - `PAPER3_DESIGN_20260807.md`: Paper 3 세부 실험 및 아키텍처 명세서
  - `CORAL_*`, `PRIOR_ART_*`: 지속적 개정 학습(CORAL) 및 선행 기술(AC-HNSW, PropagatedRAG) 분석

### 3. [03_freshevidencedb/](03_freshevidencedb/)
- **역할**: 실시간 문서 개정(Revision) 및 장애 상황에서의 벡터 DB 신선도·일관성 연구
- **주요 내용**:
  - `FreshEvidenceDB.md`: 시스템 아키텍처 및 연구 질문 정본
  - `freshevidencedb_p0/`: P0 장애 재현 실험 (오래된 스냅샷 노출, 개정 누락 결함)
  - `freshevidencedb_p1/`: P1 실환경 문서 개정(Kubernetes, Flask git 커밋) 및 답변 실패 측정
  - `freshevidencedb_p2/`: P2 다중 백엔드 노출, Weaviate, 서버 크래시 복구 및 모델 변경 평가
  - `freshevidencedb_p3/`: P3 Wikimedia 실제 편집 트레이스 및 자연어 QA 벤치마크

### 4. [04_multimodal_intent_and_graphrag/](04_multimodal_intent_and_graphrag/)
- **역할**: 관제 비디오 멀티모달 서비스 환경에서의 연산 절감 및 신뢰성 검증
- **주요 내용**:
  - `EvidenceViewDB.md` & `evidenceviewdb_p0/`: 비디오 구체화 뷰(Materialized View) 기반 중복 VLM 임베딩 절감
  - `IntentStore_...md` & `intentstore_p0_cpu/`: 서비스 의도 기반 증거 분할 저장 및 가중 융합
  - `GraphRAG_FutureWork.md` & `graphrag_p0/`: 출처 추적 지식 그래프(Provenance GraphRAG) 파이프라인

### 5. [05_workload_validity_audit/](05_workload_validity_audit/)
- **역할**: 벡터 검색 및 하이브리드 필터링 워크로드의 인위적 편향 검증
- **주요 내용**:
  - `p0_validity_audit/`: 자연 난이도(Natural) vs 매칭 난이도(Matched) 비교, HCBGen 기반 A/B 워크로드 감사

---

## 🔗 하위 호환성 (Backward Compatibility)
기존 스크립트([`04_scripts/`](../04_scripts/)) 및 논문 검증 코드([`verify_revision_numbers.py`](../04_scripts/08_verification_and_audit/verify_revision_numbers.py) 등)가 기존 경로로 접근하더라도 무중단 실행될 수 있도록, 디렉터리 내부에 상대 경로 기반 심볼릭 링크(`rag_vqa`, `reranker`, `significance`, `freshevidencedb_*`, `evidenceviewdb_p0`, `intentstore_p0_cpu`, `graphrag_p0`, `p0_validity_audit`)가 완벽히 배치되어 있습니다.
