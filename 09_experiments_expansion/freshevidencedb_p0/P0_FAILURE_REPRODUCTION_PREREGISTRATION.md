# FreshEvidenceDB P0 — 비동기 RAG 갱신 오류 재현 사전등록

- 고정일: 2026-08-07 (결과 확인 전)
- 상태: **LOCKED BEFORE EXPERIMENT**
- 실행 범위: CPU, 로컬 Qdrant 1.15.5, SQLite 3.51 FTS5
- 목적: FreshEvidenceDB를 연구 주제로 설계하기 전에, 다중 저장 계층의 비동기 갱신이 실제 stale/mixed-version evidence 오류를 만들며 단순 기준선으로 충분히 해결되지 않는지 판정한다.

## 1. 좁힌 연구 질문

> 정본 카탈로그, dense vector index, sparse index와 answer/evidence cache가 서로 다른 시점에 갱신될 때, 한 질의가 서로 다른 문서 버전의 증거를 함께 관찰하는가? 발생한다면 read-time version filter나 corpus blue/green rebuild보다 적은 쓰기로 이를 제거할 수 있는가?

P0는 “버전 문서를 더 잘 이해한다”거나 “증분 임베딩이 빠르다”는 주장을 검정하지 않는다. 대상은 **한 질의가 읽는 파생 저장 계층 간 snapshot consistency**다.

## 2. 선행연구로 이미 점유된 주장

- VersionRAG(arXiv 2510.08109): 문서 버전 관계, 변경 추적, version-sensitive QA
- SingleStore-V(PVLDB 2024): MVCC, 원자적 vector update/delete, consistent snapshot read
- PostgreSQL-V(CIDR 2026): host DB와 분리된 vector index의 transactional consistency
- MCHRAG(ICMR 2026): streaming RAG index의 효율적 증분 삽입

따라서 다음 표현은 금지한다.

- 최초의 version-aware RAG
- 최초의 transactional vector update
- 최초의 incremental RAG index
- 최초의 stale RAG 해결

남을 수 있는 공백은 **서로 다른 저장 시스템에서 파생된 복수 증거 색인을 답변 단위의 동일 epoch으로 공개하는 문제**뿐이다.

## 3. P0 데이터와 저장 계층

### 3.1 통제 코퍼스

- 문서 128개
- 문서별 3개 청크
- 각 문서는 고유 식별 토큰과 현재 정책값을 가진다.
- 8회 update wave, wave당 16개 문서
- update 유형: 값 수정, 청크 재구성, 삭제
- query는 문서 식별자를 포함하며, P0는 문서 발견이 아니라 version visibility를 격리한다.

통제 코퍼스는 자연 변경 이력의 대체물이 아니다. P0 통과 시 실제 Git/법령 revision history로 외부 검증해야 한다.

### 3.2 실제 저장 계층

1. SQLite catalog: 문서별 정본 active version/epoch
2. Qdrant dense index: CPU HashingVectorizer 256차원, cosine search
3. SQLite FTS5 sparse index
4. process-local cache

Qdrant에는 `freshevidencedb_p0_` 접두사의 격리 컬렉션만 생성한다. 기존 컬렉션은 읽거나 수정하지 않는다.

## 4. 비교 프로토콜

### A. `naive_eager`

1. catalog에서 새 버전을 먼저 활성화한다.
2. dense 새 버전 삽입
3. sparse 새 버전 삽입
4. dense/sparse 구버전 삭제
5. cache 무효화

질의는 버전 필터를 사용하지 않는다. 일반적인 delete/upsert 비동기 파이프라인의 실패 상한이다.

### B. `read_version_filter`

갱신 순서는 A와 같지만, 질의가 시작할 때 catalog active version을 읽고 dense/sparse/cache에 동일 버전을 요구한다. stale 혼합은 막을 수 있으나 새 버전이 아직 색인되지 않은 구간에는 evidence missing이 발생할 수 있다.

### C. `blue_green_epoch`

각 wave에서 전체 활성 코퍼스의 새 snapshot을 dense/sparse에 다시 기록한 뒤 global epoch pointer를 한 번 전환한다. 일관성 기준선이며 전체 코퍼스 재기록 비용을 가진다.

### D. `staged_manifest`

변경 문서의 새 버전을 dense/sparse에 먼저 staging하고 준비가 끝난 뒤 문서별 manifest를 전환한다. 질의는 시작 시 manifest snapshot을 한 번 읽고 두 색인에 동일 버전을 요구한다. 구버전은 P0 동안 유지하고 이후 GC 대상으로 계산한다.

## 5. 동시성 workload

- 프로토콜별 독립 반복: 5회
- query worker: 4개
- wave: 8회
- update phase 사이 지연: seed 기반 10–30 ms
- update 대상 문서 query 비중: 70%, 나머지 문서 30%
- query 시작 시 읽은 catalog/manifest version을 해당 질의의 snapshot 기준으로 고정
- 각 프로토콜 시작 전 steady-state 128문서 정합성 검사

## 6. 지표

| 지표 | 정의 |
|---|---|
| stale evidence | snapshot보다 낮은 버전 또는 삭제 문서의 증거 반환 |
| future evidence | snapshot보다 높은 버전의 증거 반환 |
| mixed-version evidence | dense/sparse/cache가 둘 이상의 버전을 한 질의에 반환 |
| current evidence missing | 활성 문서인데 snapshot 버전 증거가 하나도 없음 |
| answer-visible error | stale/future/mixed/missing 중 하나 또는 삭제 문서의 answer cache hit |
| p50/p95 latency | 질의 wall-clock latency |
| write amplification | 변경 문서의 이상적 신규 청크 수 대비 dense+sparse 기록 행 수 |
| publish lag | catalog source commit부터 해당 snapshot이 오류 없이 읽히기까지 시간 |

주 지표는 update window 안에서 시작한 질의의 `answer-visible error`다. 전체 질의 결과도 함께 보고한다.

## 7. 게이트

### G0 — 하니스 무결성

- update 전 steady-state error 0건
- Qdrant/FTS 행과 payload version 정합
- 각 프로토콜에서 예정된 8 wave 완료
- 프로토콜별 최소 300개의 update-window 질의

### G1 — 문제 실재성

`naive_eager`가 다음을 만족해야 한다.

- 5회 중 4회 이상에서 update-window answer-visible error rate ≥ 5%
- 5회 통합 Wilson 95% CI 하한 > 1%

미달 시 `STOP_NO_REPRODUCIBLE_FAILURE`.

### G2 — 단순 version filter의 충분성

`read_version_filter`가 다음을 모두 만족하면 새 시스템은 불필요하다.

- answer-visible error rate ≤ 1%
- current evidence missing ≤ 1%
- naive 대비 p95 latency 증가 ≤ 15%

충족 시 `STOP_SIMPLE_FILTER_SUFFICIENT`.

### G3 — staged manifest의 유효성

다음을 모두 만족해야 한다.

- update-window answer-visible error rate ≤ 1%
- Wilson 95% CI 상한 ≤ 2%
- naive 대비 p95 latency 증가 ≤ 15%
- read-version-filter 대비 missing 감소 ≥ 5%p

### G4 — blue/green 대비 시스템 가치

- staged manifest write amplification이 blue/green보다 최소 5배 낮음
- 두 방식 모두 일관성 오류 ≤ 1%

### 자동 판정

| 판정 | 조건 |
|---|---|
| `DATA_OR_HARNESS_FAILURE` | G0 실패 |
| `STOP_NO_REPRODUCIBLE_FAILURE` | G0 통과, G1 실패 |
| `STOP_SIMPLE_FILTER_SUFFICIENT` | G1 통과, G2 통과 |
| `STOP_STAGING_NOT_EFFECTIVE` | G1 통과, G2 실패, G3 또는 G4 실패 |
| `CONDITIONAL_GO_REAL_REVISION_CROSS_ENGINE` | G0·G1·G3·G4 통과, G2 실패 |

## 8. 해석 제한

- 통제 코퍼스 결과를 실제 production incidence로 표현하지 않는다.
- 강제로 둔 phase delay를 자연 발생률로 해석하지 않는다.
- Qdrant+SQLite 결과를 모든 엔진에 일반화하지 않는다.
- staged manifest가 성공해도 MVCC의 신규 발명으로 주장하지 않는다.
- GO는 실제 revision history와 두 번째 엔진에서의 확인 실험만 승인한다.

