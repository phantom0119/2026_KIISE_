# FreshEvidenceDB P3 최종 주제 확정 사전등록

- 고정일: 2026-08-07
- 상태: **LOCKED BEFORE P3 OUTCOMES**
- 선행 판정: P2 `CONDITIONAL_GO_NICHE_OR_MODEL_PENDING`
- 원칙: 기존 GPU 작업과 공유 DB를 중단·삭제하지 않는다. 결과를 본 뒤 임계값·arm·표본을 바꾸지 않는다.

## 1. P3-A 공개 실측 trace

### 데이터

- 기간: 2025-08-01 00:00 UTC–2026-07-31 23:59 UTC
- 영어 Wikipedia 12개 기술 페이지: `Kubernetes`, `Flask_(web_framework)`, `PostgreSQL`, `Elasticsearch`, `Redis`, `Neo4j`, `Docker_(software)`, `Retrieval-augmented_generation`, `Large_language_model`, `Vector_database`, `ChatGPT`, `Qdrant`
- 조회: `all-access/user/daily` pageviews
- 수정: MediaWiki revision timestamp
- 동일 URL 응답 원문, 요청 시각, SHA-256 보존

### 계산

- P2에서 더 큰 p50 unsafe exposure인 0.062469초/update를 모든 page에 적용한다.
- 일별 예상 노출: `edits_day × user_views_day / 86400 × 0.062469`
- 실제 개별 query timestamp가 없으므로 Poisson/uniform day 가정의 기대값으로만 해석한다.

### T1

- 유효 page 8개 이상, page-day 2,400개 이상, revision 총 50개 이상
- 전체 예상 unsafe observation이 연 1건 이상
- page 3개 이상이 연 0.05건 이상

통과 `TRACE_APPLICABILITY_PASS`, 미달 `TRACE_LOW_INCIDENT_OR_AGGREGATION_LIMIT`.

## 2. P3-B 4-artifact 저장·비용

### 데이터·저장소

- P1 changed fact 25개 × Flask/Kubernetes
- dense: P3 전용 Qdrant
- sparse/catalog: P3 전용 PostgreSQL
- graph: P3 전용 Elasticsearch edge document
- retrieval cache: fsync SQLite
- artifact별 deterministic ID와 `(source_id,version,epoch,type,hash,state)` 기록

### protocol

1. `eager`: manifest v2 공개 후 dense→sparse→graph→cache
2. `read_filter`: eager와 같은 쓰기, 모든 artifact에 exact version filter
3. `staged_all`: 4종 search/read 가능성 확인 후 manifest 원자 전환
4. `pg_atomic_all`: dense/sparse/graph/cache 대응 행과 manifest를 한 PostgreSQL transaction에 기록

- 도메인/protocol별 3회
- 외부 표시 checkpoint를 동일 가중
- phase 사이 인공 sleep 없음

### T2 안전성

- eager 또는 filter 오류 ≥5%
- staged_all snapshot 오류 0, Wilson 95% 상한 ≤1%
- graph/cache 누락·stale 0, readiness 실패 0
- pg_atomic_all 오류 0

통과 `FOUR_ARTIFACT_SAFETY_PASS`.

### T3 비용·정책

- update elapsed, query p95, logical/physical writes, live bytes를 전부 보고
- staged_all update p95가 pg_atomic_all의 10배 이하이면 `CROSS_STORE_COST_FEASIBLE`, 초과하면 `INTEGRATED_DB_PREFERRED`
- 실제 trace page별로 `expected_error_cost`와 `added_publish_lag_cost`의 break-even error-cost ratio를 보고한다.
- 통합 DB가 가능한 경우 pg_atomic을 기본 권고한다. 비용 결과는 safety 실패를 덮지 않는다.

## 3. P3-C coordinator·storage fault

### 시나리오

- 실제 subprocess coordinator `SIGKILL`: dense 후, sparse 후, graph 후, cache 후, READY 후, publish 후 GC 전
- message order: 4 artifact의 고정 permutation 6개
- store unavailability: Qdrant pause, Elasticsearch pause
- storage restart: Qdrant kill, PostgreSQL kill, Elasticsearch kill, 세 store 동시 kill
- 각 시나리오 2개 도메인, 최소 20 run

### recovery

- durable journal에서 active epoch·artifact readiness를 재구성
- deterministic upsert 재시도
- 모든 required artifact의 실제 read/search 검증 뒤 publish
- publish 후 crash는 v2를 유지하고 GC만 재개

### T4

- restart 직후·recovery 후 snapshot 오류 0, 합동 Wilson 95% 상한 ≤1%
- incomplete active manifest 0, duplicate 0, GC 후 orphan 0
- 전 scenario 자동 복구

통과 `COORDINATOR_FAULT_PASS`.

장애 중 availability와 재기동 후 snapshot safety를 구분해 보고한다.

## 4. P3-D finite-state model checking

- artifact 4개, active epoch, ready set, coordinator journal, crash/retry/publish/GC/query transition을 명시한다.
- BFS로 reachable state를 exhaustive 탐색한다.
- invariant: active epoch의 required artifact가 전부 ready·live, query가 epoch를 혼합하지 않음, GC가 active artifact를 제거하지 않음.
- staged protocol은 violation 0이어야 한다.
- sanity control인 eager publish는 최소 1개 counterexample을 생성해야 한다.

통과 `STATE_MACHINE_SAFETY_PASS`.

## 5. P3-E 7B 자연화 QA

### 질문

- P1 changed fact 중 답 문자열과 문맥 품질 자동 기준을 통과한 최소 30개
- cloze 원문을 source-aware 자연 문장 질문으로 변환하되 old/new 정답은 manifest에서 고정
- agent 검토와 사람 검수를 별도 열로 기록
- `human_reviewed=true`가 30개 미만이면 full model gate는 `HUMAN_REVIEW_PENDING`

### 모델·arm

- Qwen2.5-7B-Instruct, GPU BF16, temperature 0
- `current_only`, `missing`, `mixed_old_last`, `mixed_new_last`
- constrained `A/B/U` decoding 또는 첫-token logit으로 형식 오류를 제거

### T5

- current-only 최신 답변 정확도 ≥80%
- missing의 U 정확도 ≥70%
- current-only와 missing의 최신 답변 정확도 차이 ≥30%p
- mixed 순서 차이 ≤10%p
- 사람 검수 질문 ≥30개

모델 수치만 통과하고 사람 검수가 없으면 `MODEL_PASS_HUMAN_REVIEW_PENDING`; GPU가 없으면 `MODEL_RESOURCE_PENDING`; 전부 통과하면 `MODEL_HUMAN_QA_PASS`.

## 6. 전체 판정

| 판정 | 조건 |
|---|---|
| `STOP_SYSTEM_SAFETY_FAILURE` | T2 또는 T4 또는 state-machine gate 실패 |
| `ENGINEERING_NOTE_LOW_APPLICABILITY` | 안전성 통과, T1 low incident, 모델 또는 사람 gate 미통과 |
| `CONDITIONAL_P3_TRACE_OR_HUMAN_PENDING` | 안전성 통과, T1 통과, 모델/GPU/사람 gate 미통과 |
| `GO_P3_RESEARCH_TOPIC` | T1·T2·T4·state-machine·T5 전부 통과 |

`GO_P3_RESEARCH_TOPIC`도 EDBT 수락을 보장하지 않는다. 실제 enterprise trace, 다른 vendor engine과 full coordinator prototype은 본 논문에 추가로 필요하다.
