# FreshEvidenceDB P0 오류 재현 최종 보고서

- 수행일: 2026-08-07
- 자동 판정: **`CONDITIONAL_GO_REAL_REVISION_CROSS_ENGINE`**
- 연구 확정 판정: **조건부 진행 — 실제 수정 이력·두 번째 엔진 P1까지만 승인**
- 본실험/논문 확정 판정: **아직 아님**
- 실행 환경: CPU, Qdrant 1.15.5, SQLite 3.51 FTS5
- 고정 seed: 20260807
- 최종 실행 시간: 77.95초

## 1. 결론

오류는 재현됐다. 정본 카탈로그, dense index, sparse index와 cache를 순서대로 갱신하는 동안 질의가 들어오면, 개별 저장소가 정상이어도 한 답변이 서로 다른 버전의 증거를 함께 읽거나 현재 증거를 찾지 못했다.

또한 단순한 read-time version filter만으로는 충분하지 않았다. 이 필터는 stale·mixed evidence를 제거했지만 아직 색인이 완료되지 않은 최신 버전을 요구하면서 **15.19%의 evidence missing**을 만들었다. 반면 변경분을 먼저 staging하고 준비가 끝난 뒤 manifest를 전환한 방식은 update-window 질의 2,015건에서 관측 오류 0건, naive 대비 p95 지연 증가 1.83%, blue/green 대비 쓰기량 약 8.39분의 1이었다.

따라서 **cross-store snapshot publication 문제를 실제 시스템으로 더 검증할 실익은 있다.** 다만 P0는 의도적으로 갱신 단계 사이에 visibility window를 만든 합성 실험이다. 70.19%라는 naive 오류율은 운영 환경 발생률이 아니며, staged manifest는 데이터베이스의 알려진 staging·원자적 포인터 전환 원리를 RAG 파생 저장소에 적용한 것이다. 이 결과만으로 신규 시스템 논문이나 최종 연구 주제를 확정하지 않는다.

## 2. 무엇을 재현했는가

### 2.1 대상 오류

한 source revision에서 파생된 다음 자료가 서로 다른 트랜잭션 경계에서 비동기로 갱신되는 상황을 만들었다.

1. SQLite 정본 catalog의 active version
2. Qdrant dense vector evidence
3. SQLite FTS5 sparse evidence
4. process-local answer/evidence cache

질의가 갱신 도중 시작되면 다음 중 하나가 보이는지를 측정했다.

- stale evidence: 질의 snapshot보다 오래된 버전
- mixed-version evidence: 한 질의 안에서 dense·sparse·cache 버전이 불일치
- current evidence missing: 활성 문서의 해당 버전 증거가 아직 없음
- 삭제 문서의 구버전 cache/evidence 노출

### 2.2 통제 workload

- 문서 128개, 문서당 3개 청크
- 8개 update wave, wave당 16개 문서
- 수정, 재청킹, 삭제를 포함
- 프로토콜당 독립 반복 5회
- query worker 4개
- update 대상 문서 질의 비중 70%
- 총 질의 이벤트 10,002건

이 P0는 검색 자체의 실패를 배제하기 위해 문서 식별 질의를 사용했다. 즉 측정된 오류는 ANN recall이나 질의 해석 실패가 아니라 **version visibility 오류**다.

## 3. 비교한 네 가지 갱신 방식

| 방식 | 동작 | 기대 역할 |
|---|---|---|
| `naive_eager` | catalog 새 버전 활성화 → dense → sparse → 구버전 삭제 → cache 무효화 | 일반적인 비동기 delete/upsert 실패 상한 |
| `read_version_filter` | naive와 같은 쓰기 순서, 읽을 때 catalog 버전과 정확히 일치하는 증거만 허용 | 가장 단순한 방어책 |
| `blue_green_epoch` | 전체 활성 코퍼스의 새 snapshot을 만든 후 global pointer 전환 | 일관성은 강하지만 쓰기 비용이 큰 기준선 |
| `staged_manifest` | 변경분을 모든 파생 색인에 먼저 적재한 뒤 문서 manifest 전환 | 제안 방향의 최소 프로토타입 |

## 4. 결과

다음 비율은 모두 update window에서 시작된 질의를 기준으로 한다.

| 프로토콜 | 질의 수 | 답변 노출 오류 | stale | mixed | missing | p95 지연 | 쓰기 증폭 |
|---|---:|---:|---:|---:|---:|---:|---:|
| naive eager | 2,382 | **70.19%** | 70.19% | 30.73% | 25.65% | 31.12 ms | 1.00× |
| read version filter | 2,318 | **15.19%** | 0% | 0% | 15.19% | 31.65 ms | 1.00× |
| blue/green epoch | 2,034 | **0%** | 0% | 0% | 0% | 90.09 ms | 8.39× |
| staged manifest | 2,015 | **0%** | 0% | 0% | 0% | 31.69 ms | 1.00× |

### 4.1 반복 안정성

- naive error: 68.44%, 67.89%, 71.31%, 72.63%, 70.60%
- read-filter error: 14.96%, 15.15%, 15.70%, 15.70%, 14.41%
- blue/green error: 5회 모두 0%
- staged manifest error: 5회 모두 0%
- worker 오류: 전 프로토콜 0건
- 예정 wave: 20개 protocol-repeat 모두 8/8 완료

### 4.2 0건의 올바른 해석

staged manifest의 2,015건 중 관측 오류가 0건이지만 오류 확률이 수학적으로 0임을 뜻하지 않는다. Wilson 95% 신뢰구간 상한은 약 **0.190%**다. blue/green의 상한도 약 0.189%다.

## 5. 사전등록 게이트 판정

| 게이트 | 결과 | 근거 |
|---|---|---|
| G0 하니스 무결성 | 통과 | steady-state 오류 0, worker 오류 0, 모든 wave 완료, 표본 수 충족 |
| G1 문제 실재성 | 통과 | naive 5/5 반복에서 오류 ≥5%, 통합 95% CI [68.32%, 72.00%] |
| G2 단순 필터 충분성 | **실패** | stale은 제거했으나 missing/error 15.19%로 1% 기준 미달 |
| G3 staged manifest 유효성 | 통과 | 오류 0, CI 상한 0.190%, p95 증가 1.83%, missing 15.19%p 감소 |
| G4 blue/green 대비 가치 | 통과 | 두 방식 오류 0, staged의 쓰기량이 약 8.39배 적음 |

사전등록 규칙에 따른 자동 판정은 `CONDITIONAL_GO_REAL_REVISION_CROSS_ENGINE`이다.

## 6. 구현 중단 실행과 결과 선택

최종 결과를 보기 전에 하니스 문제로 두 번 실행을 중단했다.

1. v1.0: 각 reader가 SQLite WAL 모드를 재설정해 writer starvation 발생
2. v1.1: 공유 client/driver에서 query가 writer를 장시간 지연
3. v1.2: 개별 저장 phase에 writer-priority lock을 두고 phase 사이 visibility window는 유지

첫 두 실행은 하나의 protocol-repeat도 완료하지 못했고 최종 CSV·JSON·자동 판정도 생성하지 않았다. 중간 수치는 가설 판정에 사용하지 않았다. 수정 내용은 각각 결과 확인 전에 amendment로 기록했고 v1.2 코드 해시를 고정한 뒤 전체 실험을 처음부터 실행했다.

writer-priority lock 때문에 이 결과는 저장 연산 한가운데의 race가 아니라 **catalog publish, dense 준비, sparse 준비 등 완료된 phase 사이에 외부에서 관찰 가능한 상태**만 측정한다. 이는 연구 질문을 더 좁고 보수적으로 만든다.

## 7. 연구 가치 평가

### 7.1 확인된 가치

1. **문제 존재성:** 개별 저장소가 정상이어도 RAG 파생 저장소를 순차 갱신하면 답변에 보이는 cross-store inconsistency가 생긴다.
2. **단순 해법의 불충분성:** version equality filter는 stale을 missing으로 치환했다.
3. **구현 가능성:** staging 후 manifest 전환으로 P0 오류를 제거할 수 있었다.
4. **DB형 trade-off:** 전체 snapshot 복제와 변경분 staging 사이에 일관성·지연·쓰기 증폭의 측정 가능한 차이가 있다.

### 7.2 아직 입증되지 않은 가치

1. 실제 문서 수정 이력에서 이 오류가 얼마나 자주 발생하는가
2. 오류가 실제 RAG 최종 답변 정확도·근거성에 얼마나 영향을 주는가
3. Qdrant+SQLite 이외의 엔진에서도 같은 결과가 나는가
4. graph index, embedding model 교체, ACL 변경, crash/retry가 있을 때도 보장이 유지되는가
5. 기존 통합 MVCC 데이터베이스보다 별도 cross-store 프로토콜이 필요한 workload가 충분한가
6. staged manifest 이상의 새로운 프로토콜·비용 모델·복구 알고리즘이 필요한가

### 7.3 신규성 경계

넓은 주장은 이미 점유됐다.

- VersionRAG는 문서 버전 관계와 version-sensitive QA를 다룬다.
- SingleStore-V는 통합 DB 내부에서 MVCC 기반 vector update/delete와 consistent read를 제공한다.
- PostgreSQL-V는 host DB와 분리된 vector index의 transactional consistency를 다룬다.
- MCHRAG는 streaming RAG index의 증분 갱신을 다룬다.

따라서 FreshEvidenceDB를 “최초의 version-aware RAG”, “최초의 원자적 벡터 갱신” 또는 “최초의 incremental RAG”로 주장하지 않는다. 남는 후보 공백은 다음과 같다.

> 서로 다른 트랜잭션 경계를 가진 정본, dense, sparse, graph와 cache를 비동기로 갱신하면서도 한 RAG 질의가 동일 source epoch의 증거만 읽게 하는 cross-store publication protocol, 그리고 이 보장이 최종 답변의 최신성·정확성에 주는 효과

이 공백은 아직 **후보**이며 P1 문헌 재감사와 실험으로 확인해야 한다.

## 8. 연구 주제 확정 전 P1

### 8.1 목적

P1은 합성 visibility window에서 성립한 문제가 실제 revision workload와 다른 엔진에서도 관측되며, 단순 대안보다 답변 수준에서 이익이 있는지 판정한다.

### 8.2 권장 시스템 범위

- source epoch와 파생물 lineage: source → parse → chunk → embedding → dense/sparse/graph/cache
- artifact별 `STAGING/READY/ACTIVE/RETIRED` 상태
- 모든 필수 artifact가 준비된 뒤 원자적으로 전환하는 manifest
- 질의 시작 시 고정하는 snapshot token
- watermark 기반 구버전 GC
- crash/retry 후 idempotent recovery

### 8.3 데이터와 엔진

- 실제 Git tag/revision을 가진 기술 문서 2개 도메인 이상
- 실제 개정 이력이 있는 법령·규정 문서 1개 도메인 권장
- 도메인별 revision event 최소 100개
- Qdrant+SQLite cross-store 구성
- 두 번째 구성: PostgreSQL/pgvector 통합 MVCC 기준선 또는 Weaviate/Milvus 중 하나

### 8.4 P1 비교군

1. naive delete/upsert
2. read-time exact version filter
3. full blue/green alias/snapshot
4. staged manifest
5. 통합 transactional vector DB 기준선
6. 엔진이 제공하는 native consistency/update 기능

### 8.5 P1 주 지표

- stale/mixed/missing/future evidence
- current-answer accuracy 또는 deterministic exact fact accuracy
- citation provenance correctness
- source commit → answer-visible publish lag
- query p95/p99, update throughput, write amplification, 저장 공간
- crash injection 후 atomicity, recovery time, orphan artifact 수

LLM judge는 주 지표로 쓰지 않는다. 시간·수치·식별 가능한 사실은 결정론적으로 채점하고, 자유형 답변이 필요하면 사람 이중 주석을 사용한다.

### 8.6 P1 사전 중단 기준

다음 중 하나면 대규모 구현과 본논문을 중단한다.

- 실제 revision workload 두 도메인 모두에서 naive 오류가 1% 미만이고 답변 영향도 실질적으로 없음
- read-time filter가 오류·missing을 모두 1% 이하로 만들고 답변 품질 손실도 없음
- native engine 또는 통합 MVCC 기준선이 동일 요구를 낮은 비용으로 충족
- staged protocol의 p95 지연 증가가 15%를 넘거나 blue/green 대비 쓰기 이득이 5배 미만
- 최종 답변 current accuracy 개선이 5%p 미만이고 동등성 검정도 통과하지 못함
- crash/retry에서 stale 또는 mixed snapshot이 반복 재현됨

### 8.7 P1 통과 기준

최소 두 실제 도메인과 두 저장 구성에서 다음이 함께 성립해야 한다.

- naive 또는 단순 filter의 answer-visible 오류/결손이 실질적으로 존재
- staged publication의 stale·mixed 오류 ≤1%
- answer current accuracy가 단순 filter보다 최소 5%p 개선되거나, 동등한 정확도에서 publish lag/쓰기 비용을 유의미하게 절감
- naive 대비 p95 질의 지연 증가 ≤15%
- blue/green 대비 쓰기 증폭 최소 5배 절감
- crash/retry 뒤 동일 epoch 보장과 재현 가능한 복구

## 9. 최종 판정

**실제 구현을 계속할 가치는 있다.** 정확한 의미는 다음과 같다.

- 승인: 실제 revision workload를 연결하고 두 번째 엔진과 crash injection을 포함하는 최소 P1 프로토타입
- 보류: 전체 기능 제품, 대규모 GraphRAG 통합, 논문 주제 최종 확정
- 금지: P0의 70.19%를 운영 발생률로 인용하거나 staging/manifest 자체를 신규 알고리즘으로 주장

P1이 통과하면 `FreshEvidenceDB: Snapshot-Consistent Publication of Derived Evidence Across Heterogeneous RAG Stores`로 최종 주제화할 수 있다. 실패하면 이 후보도 EvidenceViewDB와 마찬가지로 중단한다.

## 10. 재현 자료

- 사전등록: `P0_FAILURE_REPRODUCTION_PREREGISTRATION.md`
- 구현 변경 기록: `P0_V1_1_IMPLEMENTATION_AMENDMENT.md`, `P0_V1_2_IMPLEMENTATION_AMENDMENT.md`
- 실행 코드: `run_failure_reproduction.py`
- 자동 판정: `results_run3/AUTO_REPORT.md`
- 집계: `results_run3/aggregate.json`
- 반복별 결과: `results_run3/repeat_summary.csv`
- 질의별 사건: `results_run3/query_events.csv`
- 결과 무결성: `results_run3/RESULT_MANIFEST.sha256`

`results_run1`과 `results_run2`는 중단 실행의 상태 DB만 보존하며 결과로 사용하지 않는다.
