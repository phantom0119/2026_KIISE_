# 도메인 특화 증거 저장소 및 지식 그래프 RAG (EvidenceViewDB, IntentStore, Provenance GraphRAG)

본 디렉터리는 관제 비디오 및 멀티모달 서비스 환경에서 **고비용 VLM 연산 절감**, **서비스 의도 기반 증거 뷰 저장**, 그리고 **출처 추적 지식 그래프(Provenance GraphRAG)**를 다루는 확장 연구 산출물을 관리합니다.

---

## 📂 프로젝트별 구성 및 역할

### 1. EvidenceViewDB (`evidenceviewdb_p0/` & [`EvidenceViewDB.md`](EvidenceViewDB.md))
- **목적**: 비디오 관제 질의의 시공간 메타데이터 및 다중 해상도 프레임 표현을 "구체화 뷰(Materialized View)" 형태로 관리하여 중복 VLM 임베딩 비용을 최소화.
- **주요 코드**:
  - `run_p0a_cpu.py`: CPU 기반 프로토타입 실행 및 뷰 적중률 측정
  - `eval_p0_evidence_view.py`: 구체화 뷰 캐싱 대비 nDCG 및 지연 시간 트레이드오프 평가
  - `P0_REPORT.md`: 초기 타당성 및 비용 절감 리포트

### 2. IntentStore (`intentstore_p0_cpu/` & [`IntentStore_...md`](IntentStore_실시간%20위험%20분석을%20위한%20서비스%20의도%20기반%20멀티모달%20증거%20저장%20및%20추론%20계획.md))
- **목적**: 실시간 위험 분석 환경에서 서비스의 의도(Intent)별로 멀티모달 증거를 분할 저장하고 가중 융합(Weighted Fusion) 추론을 최적화.
- **주요 스크립트 (`scripts/`)**:
  - `analyze_safety_representation.py`: 안전 관제 도메인 표현형 성능 분석
  - `audit_safety_storage_costs.py`: 저장소 오버헤드 및 파레토 최적점 계산
  - `audit_safety_fusion_robustness.py`: 융합 가중치 변동에 대한 강건성 감사
  - `analyze_meva_replication.py`: MEVA 관제 데이터셋 기반 재현 실험

### 3. Provenance GraphRAG (`graphrag_p0/`, [`GraphRAG_FutureWork.md`](GraphRAG_FutureWork.md), [`TOPIC_VERIFY_PROVENANCE_GRAPHRAG_...md`](TOPIC_VERIFY_PROVENANCE_GRAPHRAG_20260806.md))
- **목적**: 멀티모달 RAG 답변의 인과적 신뢰성을 입증하기 위해, 검색된 클립과 외부 지식 간의 출처 계보(Provenance Graph)를 연결하고 검증.
- **주요 스크립트 (`scripts/`)**:
  - `build_synchronized_worlds.py`: 동기화된 가상 사실 그래프 구축
  - `audit_counterfactual_leakage.py`: 반사실적 정보 유출 및 편향 검증
  - `run_judge_substudy.py` & `run_model_pilot.py`: LLM 판정관 기반 인과성 검증
  - `estimate_power.py` & `measure_coverage.py`: 검정력 및 지식 커버리지 분석
