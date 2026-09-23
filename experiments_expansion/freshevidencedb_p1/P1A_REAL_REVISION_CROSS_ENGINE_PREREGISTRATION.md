# FreshEvidenceDB P1-A — 실제 개정 이력·교차 엔진 사전등록

- 고정일: 2026-08-07
- 상태: **LOCKED BEFORE OUTCOME EXPERIMENT**
- 선행 단계: P0 `CONDITIONAL_GO_REAL_REVISION_CROSS_ENGINE`
- 목적: P0의 합성 문서·강제 지연에서 관측한 오류가 실제 문서 개정 쌍과 실제 저장 연산 시간에서도 재현되는지 확인하고, PostgreSQL 통합 트랜잭션으로 충분한지 비교한다.
- 범위: P1-A는 evidence visibility와 시스템 비용을 측정한다. 생성 모델의 최종 답변 품질은 P1-A 통과 후 P1-B에서 수행한다.

## 1. 연구 질문

### RQ1

실제 문서의 수정 전·후 내용과 자연 청크 수를 사용하고 저장 phase 사이 인공 sleep을 제거해도, Qdrant dense index와 PostgreSQL catalog/sparse index의 순차 갱신에서 stale·mixed·missing evidence가 관측되는가?

### RQ2

읽을 때 manifest의 exact version을 요구하는 단순 필터가 stale·mixed 오류를 제거하면서도 current evidence missing을 1% 이하로 유지하는가?

### RQ3

변경분을 먼저 적재한 뒤 manifest를 전환하는 staged publication이 blue/green보다 적은 쓰기로 동일 snapshot을 제공하는가?

### RQ4

catalog, dense vector와 sparse evidence를 PostgreSQL의 한 트랜잭션에 넣으면 별도 cross-store protocol 없이 동일 보장을 제공하는가?

## 2. 고정 데이터

두 저장소 모두 공식 공개 Git 저장소이며 결과에는 원문 전체가 아니라 commit/path/hash, 청크 통계와 측정값만 남긴다.

| 도메인 | 저장소 | 고정 HEAD | 문서 경로 | 라이선스 |
|---|---|---|---|---|
| Python web framework | `https://github.com/pallets/flask.git` | `6a2f545bfd8ed31e19066a299296917e034aca58` | `docs/**` | BSD-3-Clause, `LICENSE.txt` SHA-256 `489a8e...d07ea` |
| container orchestration | `https://github.com/kubernetes/website.git` | `7ddeae4e0e52ce7dcb0e868106a9c15d8e3b8b02` | `content/en/docs/**` | CC-BY-4.0, `LICENSE` SHA-256 `9ba955...29411` |

### 2.1 revision pair 추출

- HEAD에서 가까운 non-merge commit부터 검사한다.
- 대상 확장자: Flask `.rst`, `.md`; Kubernetes `.md`.
- parent와 commit에 모두 존재하며 내용이 달라진 modified file만 후보로 한다.
- UTF-8로 해석 가능하고 각 버전의 본문이 200–100,000자여야 한다.
- 문단 기반 청킹 후 두 버전의 chunk sequence가 달라야 한다.
- 한 commit에서 path 순으로 최대 한 pair만 사용한다.
- 도메인별 처음 100개의 유효 pair를 고정한다.
- 각 pair는 독립 logical document로 취급한다. 동일 path의 다른 commit은 다른 `doc_id`가 된다.
- 선택 실패 또는 한 도메인 100개 미달은 결과를 보지 않고 `DATA_FAILURE`로 판정한다.

이 독립 pair 구성은 실제 문서의 자연 길이·변경·재청킹을 보존하지만, 하나의 운영 corpus가 겪는 시간별 update 빈도를 재현하지 않는다.

### 2.2 청킹과 임베딩

- Markdown/RST front matter와 연속 공백을 정규화한다.
- 빈 줄 경계 문단을 기본 단위로 한다.
- 40자 미만 문단은 다음 문단과 결합한다.
- 800자를 넘는 문단은 800자 고정 폭으로 나눈다.
- 문서당 최대 128 chunk; 초과 문서는 revision 후보에서 제외한다.
- `HashingVectorizer`, 384차원, word 1–2 gram, L2 normalization
- GPU와 학습 모델을 사용하지 않는다.

HashingVectorizer는 의미 검색 품질을 주장하기 위한 모델이 아니다. 두 엔진에 동일한 결정론적 vector를 제공하여 version visibility와 storage protocol만 격리한다.

## 3. 실행 환경

- Qdrant 1.15.5: `127.0.0.1:6333`
- PostgreSQL 16.14 + pgvector 0.8.4: `127.0.0.1:5433/vlmdb`
- Python `qdrant-client`, `psycopg 3`
- 실험 객체 접두사: Qdrant `freshevidencedb_p1a_`, PostgreSQL schema `fresh_p1a`
- 기존 collection/table은 읽거나 수정하지 않는다.

## 4. workload

- 도메인별 revision pair: 100개
- wave당 변경 문서: 10개, 도메인별 10 wave
- protocol/domain별 독립 반복: 3회
- query worker: 8개
- update 대상 문서 query 비중: 80%
- 나머지 20%는 아직 삭제되지 않은 전체 문서에서 균등 추출
- phase 사이 `sleep` 또는 인위적 지연: **없음**
- update wave 사이 cooldown: 결과 수집 종료 표식을 위한 5ms 이하의 고정 scheduler yield만 허용하며 update-window에서 제외
- 각 query는 시작 시 선택한 expected version을 끝까지 유지한다.

이 workload의 오류율은 변경 중인 문서에 질의를 집중한 조건부 stress rate다. production prevalence로 표현하지 않는다.

## 5. 비교 프로토콜

### A. `cross_naive`

1. PostgreSQL manifest를 v2로 commit
2. Qdrant에 v2 dense chunks upsert
3. PostgreSQL에 v2 sparse chunks commit
4. Qdrant에서 v1 삭제
5. PostgreSQL에서 v1 sparse 삭제

읽기는 version filter 없이 상위 evidence를 읽는다.

### B. `cross_read_filter`

쓰기 순서는 A와 동일하다. 질의 시작 시 manifest version을 읽고 Qdrant·PostgreSQL 양쪽에 exact version을 요구한다.

### C. `cross_staged`

1. Qdrant에 v2 dense chunks upsert
2. PostgreSQL에 v2 sparse chunks commit
3. 두 저장소의 row count/hash readiness 확인
4. PostgreSQL manifest를 v2로 commit
5. v1은 실험 종료까지 유지하고 GC 대상량만 계산

질의는 시작 시 읽은 manifest version을 snapshot token으로 사용한다.

### D. `cross_blue_green`

wave의 변경을 반영한 전체 도메인 snapshot을 새 epoch로 Qdrant·PostgreSQL에 기록하고 global epoch를 전환한다. 질의는 시작 시 고정한 epoch만 읽는다.

### E. `pg_atomic`

manifest, dense vector chunks, sparse `tsvector` chunks를 PostgreSQL schema 안에 둔다. v2 삽입, manifest 전환, v1 삭제를 한 transaction으로 commit한다. 질의는 `REPEATABLE READ READ ONLY` transaction에서 manifest와 두 evidence를 읽는다.

## 6. 질의와 오류 판정

질의는 `repo/path/commit`에서 만든 고유 probe와 해당 revision의 변경 문장 토큰을 사용한다. 모든 검색은 `doc_id`로 범위를 제한하고, dense/sparse 각 top-8의 payload version을 수집한다. 이는 문서 발견 성능이 아니라 한 logical document 안의 version visibility를 측정한다.

| 지표 | 정의 |
|---|---|
| stale | 관측 version < query snapshot version 또는 삭제 상태의 evidence |
| future | 관측 version > query snapshot version |
| mixed | 한 query의 dense/sparse 결과에 둘 이상의 version/epoch 존재 |
| missing | 활성 snapshot의 version이 dense 또는 sparse 필수 계층 중 하나에 없음 |
| answer-visible error | stale, future, mixed, missing 중 하나 |
| publish lag | manifest 전환까지의 wall-clock time |
| p95 query latency | update-window query latency |
| write amplification | 변경된 새 chunk를 dense+sparse에 한 번 쓰는 양 대비 실제 쓰기 행 |

P1-A의 missing은 dense와 sparse 중 하나라도 expected version을 제공하지 못하면 1이다. 하이브리드 검색이 한 계층만으로 fallback할 수 있더라도 증거 계층 readiness가 완전하지 않은 상태를 보수적으로 측정한다.

## 7. 통계와 보고

- protocol/domain/repeat별 모든 query event를 보존한다.
- 비율에는 Wilson 95% 신뢰구간을 보고한다.
- 반복별 결과를 숨기지 않는다.
- Flask와 Kubernetes 결과를 통합하기 전에 각각 보고한다.
- 0건은 0 확률이 아니라 Wilson 상한과 함께 보고한다.
- latency는 p50/p95/p99를 보고한다.
- raw CSV, aggregate JSON, revision manifest와 코드의 SHA-256을 고정한다.

## 8. 사전 게이트

### G0 — 데이터·하니스 무결성

- 도메인별 유효 revision pair 100개
- 모든 초기 steady-state query 오류 0
- protocol/domain/repeat별 10 wave 완료
- worker exception 0
- protocol/domain별 update-window query 500건 이상
- Qdrant/PostgreSQL row count와 payload hash audit 통과

미달 시 `DATA_OR_HARNESS_FAILURE`.

### G1 — 자연 revision에서 문제 재현

각 도메인의 `cross_naive`가 다음을 모두 만족한다.

- 3회 중 2회 이상 error rate ≥1%
- 통합 Wilson 95% CI 하한 >0.1%

어느 한 도메인이라도 미달하면 `STOP_NOT_ROBUST_ACROSS_DOMAINS`.

### G2 — 단순 필터 충분성

두 도메인의 `cross_read_filter`가 다음을 모두 만족하면 별도 staged protocol을 중단한다.

- error ≤1%
- missing ≤1%
- naive 대비 p95 증가 ≤15%

충족 시 `STOP_SIMPLE_FILTER_SUFFICIENT`.

### G3 — staged publication 유효성

각 도메인에서 다음을 모두 만족한다.

- error ≤1%
- Wilson 95% CI 상한 ≤2%
- read-filter보다 missing 최소 1%p 감소
- naive 대비 p95 증가 ≤20%

### G4 — blue/green 대비 비용 가치

- staged와 blue/green error 모두 ≤1%
- blue/green/staged write amplification 비율 ≥5

### G5 — 통합 MVCC 기준선

- 각 도메인의 `pg_atomic` error ≤1%
- 각 도메인의 Wilson 95% CI 상한 ≤2%

G5 통과는 FreshEvidenceDB 전체를 중단하는 조건이 아니다. 통합 DB 안에서는 native transaction으로 충분하며 연구 범위를 **이질적인 외부 파생 저장소가 필요한 배치**로 한정한다. G5 실패는 하니스 또는 isolation 설계 문제를 먼저 조사하므로 본 주제의 긍정 증거로 사용하지 않는다.

## 9. 자동 판정

| 판정 | 조건 |
|---|---|
| `DATA_OR_HARNESS_FAILURE` | G0 실패 또는 G5 실패 |
| `STOP_NOT_ROBUST_ACROSS_DOMAINS` | G0·G5 통과, G1 실패 |
| `STOP_SIMPLE_FILTER_SUFFICIENT` | G0·G1·G5 통과, G2 통과 |
| `STOP_STAGING_NO_SYSTEM_VALUE` | G0·G1·G5 통과, G2 실패, G3 또는 G4 실패 |
| `GO_P1B_ANSWER_AND_FAILURE_INJECTION` | G0·G1·G3·G4·G5 통과, G2 실패 |

## 10. 해석 제한

- actual revision text를 사용해도 query arrival은 stress workload이므로 운영 오류율이 아니다.
- 각 pair를 독립 logical document로 만든 결과를 실제 repository의 시간별 update 빈도로 해석하지 않는다.
- HashingVectorizer 결과를 최신 임베딩 모델의 검색 품질로 해석하지 않는다.
- `pg_atomic`이 성공하면 통합 DB 범위에서 신규성을 주장하지 않는다.
- staged publish와 manifest flip 자체를 신규 DB 알고리즘으로 주장하지 않는다.
- GO는 P1-B의 answer-level 평가와 crash/retry/GC 실험만 승인한다.
