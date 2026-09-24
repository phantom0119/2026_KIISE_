# 차기 연구 기획 및 학술대회 제안 포트폴리오 (Follow-up Topics & Conference Proposals)

본 디렉터리는 KIISE 2026 논문 완결 후 차기 최상위 학술대회(VLDB, SIGMOD, ICDE 등) 투고를 목적으로 집중 수립된 **후속 연구 기획서, 대안 포트폴리오, 선행 기술 분석 및 청사진**을 보관합니다.

---

## 📂 수록 문서 목록 및 역할

| 파일명 | 크기 | 주요 내용 및 목적 |
|---|:---:|---|
| [**`CONFERENCE_TOPIC_PROPOSAL_20260804.md`**](CONFERENCE_TOPIC_PROPOSAL_20260804.md) | 108 KB | **차기 학술대회 주제 제안서 종합본**: 멀티모달 비디오 RAG 및 실시간 벡터 DB 한계 극복을 위한 3개 핵심 트랙 제안 |
| [**`ALT_TOPICS_PORTFOLIO_20260805.md`**](ALT_TOPICS_PORTFOLIO_20260805.md) | 44 KB | **대안 연구 주제 포트폴리오**: FreshEvidenceDB, EvidenceViewDB, IntentStore 등 연구 주제별 장단점 및 실현 가능성 비교 |
| [**`TOPIC_REORGANIZATION_20260807.md`**](TOPIC_REORGANIZATION_20260807.md) | 179 KB | **연구 주제 재편성 및 통합 로드맵**: 선행 실험 결과를 반영한 차기 논문 시리즈 구조 개편 정본 |
| [**`PAPER3_DESIGN_20260807.md`**](PAPER3_DESIGN_20260807.md) | 35 KB | **Paper 3 설계 명세서**: 신선도 보장 및 개정 추적 벡터 데이터베이스 아키텍처 세부 설계 |
| [**`CORAL_PROBLEM_BACKGROUND_RELATED_WORK_AND_REVISED_EXPERIMENT_DESIGN_20260804.md`**](CORAL_PROBLEM_BACKGROUND_RELATED_WORK_AND_REVISED_EXPERIMENT_DESIGN_20260804.md) | 44 KB | **CORAL 문제 배경 및 관련 연구**: Continuous Online Revision & Adaptive Learning 설계 배경 및 개정 실험 체계 |
| [**`RESEARCH_PLAN_CORAL_20260804.md`**](RESEARCH_PLAN_CORAL_20260804.md) | 18 KB | **CORAL 연구 계획서**: 지속적 개정 워크로드 환경에서의 실험 목표 및 마일스톤 |
| [**`RESEARCH_PLAN_CORAL_EXPLAINED_AND_TREND_REVIEW_20260804.md`**](RESEARCH_PLAN_CORAL_EXPLAINED_AND_TREND_REVIEW_20260804.md) | 40 KB | **CORAL 트렌드 리뷰 및 상세 설명**: 최신 비디오 RAG 및 스트리밍 인덱싱 트렌드 분석 |
| [**`PRIOR_ART_ACHNSW_20260804.md`**](PRIOR_ART_ACHNSW_20260804.md) | 79 KB | **AC-HNSW 선행 기술 분석**: Attribute-Conditioned HNSW의 구조적 한계와 극복 방안 분석 |
| [**`PRIOR_ART_PROPAGATEDRAG_20260804.md`**](PRIOR_ART_PROPAGATEDRAG_20260804.md) | 74 KB | **PropagatedRAG 선행 기술 분석**: 지식 전파 및 그래프 전파 기반 RAG의 병목점 분석 |
| [**`compass_artifact_wf_text_markdown.md`**](compass_artifact_wf_text_markdown.md) | 26 KB | **Compass 아티팩트 및 연구 방향**: 워크플로우 텍스트 및 연구 로드맵 정리 |

---

## 🎯 연구 기획 핵심 축
1. **신선도 및 동적 개정 (Freshness & Continuous Revision)**: 지식 베이스의 실시간 변경 및 삭제를 일관성 있게 흡수하는 벡터 색인 (`FreshEvidenceDB`로 실체화)
2. **서비스 의도 및 다중 모달 뷰 최적화 (Intent & Multi-view Optimization)**: 고비용 VLM 추론을 최소화하기 위한 사전 구체화 뷰 및 의도 기반 라우팅 (`EvidenceViewDB`, `IntentStore`로 실체화)
3. **출처 검증 및 인과성 추적 (Provenance & Causality)**: 검색된 증거의 신뢰성과 환각 방지를 위한 지식 그래프 융합 (`GraphRAG`로 실체화)
