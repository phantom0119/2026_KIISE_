# FreshEvidenceDB P2 사전등록 — 적용 범위·교차 엔진·서버 장애·모델 답변

- 고정일: 2026-08-07
- 상태: **LOCKED BEFORE P2 OUTCOMES**
- 선행 판정: P1-B `GO_FRESHEVIDENCEDB_CORE_TOPIC`
- 실행 원칙: 공용 Qdrant/PostgreSQL container를 중단하지 않는다. P2 server fault는 전용 `fresh-p2-qdrant:16333`, `fresh-p2-postgres:15434`만 사용한다.

## 1. P2 질문

### P2-RQ1 적용 범위

공식 문서 Git commit timestamp와 P1에서 실측한 update duration을 결합하면, naive/filter 오류가 실제 시간 중 차지하는 노출과 updated-document query rate별 예상 오류는 어느 정도인가?

### P2-RQ2 vector engine 일반성

Qdrant 대신 Weaviate 1.35.3을 dense store로 사용하고 PostgreSQL sparse/catalog와 결합해도 순차 갱신 오류와 version-filter missing이 재현되며 staged publication이 이를 제거하는가?

### P2-RQ3 storage failure

Qdrant/PostgreSQL process kill과 일시적 Qdrant unavailability가 staging/publish 도중 발생해도 query가 마지막 complete epoch만 읽고 idempotent recovery가 가능한가?

### P2-RQ4 생성 모델

실제 changed fact에서 만든 선택형 자연 문장 질문에 대해, current-only evidence는 missing 또는 mixed-version evidence보다 최신 답변 정확도가 높은가? source epoch metadata가 context position bias를 완화하는가?

## 2. P2-A timestamp-calibrated exposure

### 데이터

- P1 revision manifest의 Flask 100, Kubernetes 100 pair
- unique commit timestamp: Git object의 committer timestamp
- P1-A repeat summary의 protocol/domain별 wave duration과 conditional error
- 한 P1 wave는 10 document update이므로 per-document duration은 wave duration/10으로 근사

### 계산

- `update_rate_per_day = unique_commit_count / trace_days`
- `error_seconds_per_update = per_doc_update_seconds × conditional_error_rate`
- `time_exposure_fraction = update_rate_per_day × error_seconds_per_update / 86400`
- updated-document cohort query rate `r ∈ {0.1,1,10,20,100}` qps에서 `expected_errors_per_day = update_rate_per_day × error_seconds_per_update × r`
- 하루 1건 오류를 만드는 break-even qps를 보고한다.

### 해석 게이트 T1

- 어느 한 도메인에서 naive 또는 filter의 break-even이 20 qps 이하이면 `APPLICABLE_HIGH_TRAFFIC`.
- 두 도메인 모두 20 qps 초과이면 `NICHE_OR_BATCH_ONLY`.

T1은 시스템 안전성의 중단 조건이 아니라 적용 범위를 정하는 조건이다. 실제 query trace가 없으므로 production incidence를 주장하지 않는다.

## 3. P2-B Weaviate 교차 엔진

### 데이터·workload

- 도메인별 P1 revision pair의 처음 50개
- 실제 old/new 전문, P1과 동일한 paragraph chunking과 HashingVectorizer 384차원
- protocol: `weaviate_naive`, `weaviate_read_filter`, `weaviate_staged`
- 도메인/protocol별 3회 반복
- 5 wave × wave당 10 document
- query worker 4개, hot update document query 80%
- phase 사이 인공 sleep 0
- dense: 공유 Weaviate의 `FreshP2...` 전용 collection
- catalog/sparse: P2 전용 PostgreSQL container

### 지표·게이트 T2

- steady-state 오류 0, worker exception 0, 모든 wave 완료, protocol/domain별 update query 300건 이상
- 두 도메인의 naive가 3회 중 2회 이상 error ≥1%, Wilson 하한 >0.1%
- 두 도메인의 read filter가 error/missing >1%
- 두 도메인의 staged error ≤1%, Wilson 상한 ≤2%
- staged가 filter보다 missing을 최소 1%p 줄임

통과: `CROSS_ENGINE_GENERALIZED`. 실패: `STOP_BACKEND_SPECIFIC_OR_HARNESS`.

## 4. P2-C process/network fault

### 전용 환경

- Qdrant 1.15.5 container `fresh-p2-qdrant`, host port 16333
- PostgreSQL 16.14 + pgvector 0.8.4 container `fresh-p2-postgres`, host port 15434
- P1 changed fact 중 도메인별 25개
- scenario별 2회 반복

### 시나리오

1. `qdrant_kill_partial_stage`: 새 dense의 절반 기록 후 Qdrant `SIGKILL`, restart
2. `qdrant_kill_ready_before_publish`: dense 완료 후 Qdrant `SIGKILL`, restart
3. `postgres_kill_before_sparse_commit`: dense 완료 후 PostgreSQL `SIGKILL`, restart
4. `postgres_kill_after_publish_before_gc`: dense+sparse ready와 manifest commit 후 PostgreSQL `SIGKILL`, restart
5. `qdrant_pause_timeout_retry`: Qdrant pause 동안 stage 요청 실패, unpause 후 retry

### 복구 규칙

- pre-publish failure: manifest는 v1, v1 artifact 유지
- recovery: 동일 deterministic ID로 stage 재시도 → readiness 확인 → manifest v2 publish
- post-publish failure: v2 artifact readiness 재확인 후 GC 재개
- retry와 recovery는 full corpus rebuild를 사용하지 않는다.

### 게이트 T3

- failure 직후 snapshot-answer error 0
- recovery 후 error 0, 합동 Wilson 95% 상한 ≤1%
- GC 후 error 0
- duplicate logical artifact 0, GC 후 orphan 0
- active manifest가 incomplete artifact를 참조한 건 0
- 20 scenario run 모두 자동 복구

통과: `SERVER_FAULT_GATE_PASS`. 실패: `STOP_SERVER_RECOVERY_UNSAFE`.

## 5. P2-D CPU model answer gate

### 모델·이유

- GPU는 타 실험이 점유하므로 중단하지 않는다.
- 로컬 `Llama-3.2-1B-Instruct`를 CPU float32/bfloat16 가능 범위에서 사용한다.
- 이 결과는 low-resource pipeline gate이며 대표 7–14B LLM 결론이 아니다.

### 데이터와 arm

- P1 changed fact 25개 × 2 domain = 50
- old/new answer option 순서는 seed로 교차 균형화
- `current_only`: epoch 2 evidence만 제공
- `missing`: evidence 없음, 정답은 `U`(insufficient)
- `mixed_old_last`: epoch 2와 epoch 1 evidence, old evidence가 뒤
- `mixed_new_last`: epoch 1과 epoch 2 evidence, new evidence가 뒤
- prompt는 가장 큰 `source_epoch`의 evidence를 사용하고 없으면 U를 출력하도록 명시
- temperature 0, 최대 새 token 4

### 지표·게이트 T4

- competence: current_only 최신 답변 정확도 ≥70%
- competence 실패 시 `MODEL_GATE_INCONCLUSIVE`
- competence 통과 시 current_only가 missing의 최신 답변 accuracy보다 ≥20%p 높음
- mixed 두 순서의 정확도 차이 ≤15%p이면 epoch metadata가 position sensitivity를 제한한 것으로 기록
- 차이 >15%p이면 position-sensitive로 기록하되 FreshEvidenceDB의 storage gate 실패로 해석하지 않는다.

## 6. 전체 판정

| 판정 | 조건 |
|---|---|
| `DATA_OR_HARNESS_FAILURE` | 데이터·환경 무결성 실패 |
| `STOP_BACKEND_SPECIFIC_OR_HARNESS` | T2 실패 |
| `STOP_SERVER_RECOVERY_UNSAFE` | T2 통과, T3 실패 |
| `CONDITIONAL_GO_NICHE_OR_MODEL_PENDING` | T2·T3 통과, T1 niche 또는 T4 inconclusive |
| `GO_P2_SYSTEM_PROTOTYPE` | T2·T3 통과, T1 applicable, T4 competence/answer gate 통과 |

`GO_P2_SYSTEM_PROTOTYPE`도 EDBT 수락 가능성을 보장하지 않는다. 실제 query trace, 사람 검수 QA, 7–14B 모델, graph/cache/ACL와 coordinator protocol은 본 시스템 평가에 추가해야 한다.

## 7. 결과 해석 제한

- Git update timestamp는 실제지만 query timestamp는 scenario grid다.
- Weaviate 실험은 외부 engine 일반성 한 점이지 모든 vector DB의 증명이 아니다.
- Docker SIGKILL은 machine/power loss와 동일하지 않다.
- CPU 1B 모델을 대표 LLM으로 일반화하지 않는다.
- FinCacheServe의 answer-cache dependency consistency와 FreshEvidenceDB의 retrieval artifact publication을 구분한다.
