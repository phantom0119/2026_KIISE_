# FreshEvidenceDB P1-B — 답변 영향·client crash 복구 사전등록

- 고정일: 2026-08-07
- 상태: **LOCKED BEFORE P1-B OUTCOME**
- 진입 근거: P1-A 자동 판정 `GO_P1B_ANSWER_AND_FAILURE_INJECTION`
- 목적: evidence version 오류가 실제 변경 사실의 답변 오류로 이어지는지, staged publication이 부분 쓰기·client crash·중복 retry 뒤에도 안전하게 복구되는지 판정한다.

## 1. 범위와 제한

P1-B는 실제 문서 수정에서 추출한 결정론적 cloze fact를 사용한다. LLM 생성 품질이나 자연 질의 분포를 주장하지 않는다. 질문의 정답은 revision diff에서 직접 고정하며, answerer는 검색 증거에 새 답·옛 답이 존재하는지만 판정한다.

장애 주입은 Qdrant/PostgreSQL 서버의 전원 장애가 아니라 **파생물 작성 client/worker의 crash와 재시작**이다. 저장소 자체의 process kill, network partition과 WAL 복구는 후속 P2 범위다.

## 2. changed-fact 추출

- P1-A에 고정한 Flask/Kubernetes revision pair 100개씩을 사용한다.
- 수정 전·후 문서를 word/punctuation token sequence로 비교한다.
- `replace` 구간 중 old/new answer가 각각 1–4 token이고 2–60자인 후보를 사용한다.
- old answer는 new 문서에 없어야 하고, new answer는 old 문서에 없어야 한다.
- 숫자, 버전, option, API identifier를 우선하고 이후 일반 영숫자 token을 사용한다.
- 새 문맥의 answer를 `____`로 치환한 cloze question을 만든다.
- answer 앞뒤 최대 24 token을 evidence로 보존한다.
- revision pair당 최대 1개, 도메인별 처음 40개를 사용한다.
- 어느 도메인이 40개 미만이면 `DATA_FAILURE`다.

## 3. 답변 판정

각 fact document는 old evidence(v1)와 new evidence(v2)를 가진다. 검색 결과의 evidence를 다음처럼 결정론적으로 답변으로 변환한다.

| evidence | answer label |
|---|---|
| new answer만 존재 | `CURRENT` |
| old answer만 존재 | `STALE` |
| old와 new 모두 존재 | `AMBIGUOUS` |
| 둘 다 없음 또는 필수 dense/sparse 계층 하나가 없음 | `MISSING` |

manifest가 v1이면 `STALE`이라는 이름의 old answer가 당시 current이므로 정답으로 채점한다. manifest가 v2이면 new answer만 `CURRENT` 정답이다. 즉 metric은 미래 정답을 미리 요구하지 않고, query snapshot이 선언한 세계와의 일치를 측정한다.

## 4. 답변 checkpoint 실험

도메인별 40 fact, 다음 네 protocol을 비교한다.

1. `cross_naive`
2. `cross_read_filter`
3. `cross_staged`
4. `pg_atomic`

각 fact update의 protocol별 externally visible phase 직후에 한 번씩 질의한다. phase에 같은 가중치를 부여하며 wall-clock production 발생률로 해석하지 않는다.

- naive/filter: initial, manifest publish, dense insert, sparse insert, dense old delete, sparse old delete
- staged: initial, dense stage, sparse stage, readiness audit, manifest publish, old-version GC
- pg_atomic: transaction 전, commit 후

주 지표는 v2 manifest가 활성화된 checkpoint의 `current-answer accuracy`다. 보조 지표로 snapshot answer accuracy, stale/ambiguous/missing answer rate를 모두 보고한다.

## 5. 장애 시나리오

`cross_staged`에서 도메인별 40 fact 전체를 대상으로 다음 다섯 scenario를 각각 독립 저장 공간에서 수행한다.

1. `partial_dense_crash`: v2 dense chunk 절반만 기록 후 client 종료·재연결
2. `dense_complete_crash`: v2 dense 전체 기록 후 client 종료·재연결
3. `sparse_complete_crash`: dense+sparse 기록 후 manifest 전환 전에 client 종료·재연결
4. `published_before_gc_crash`: manifest 전환 후 구버전 GC 전에 client 종료·재연결
5. `duplicate_retry`: dense+sparse staging과 manifest publish를 동일 ID로 두 번 실행

각 scenario에서 다음을 측정한다.

- crash 직후 query snapshot answer 오류
- idempotent recovery 후 answer 오류
- expected dense/sparse row count
- duplicate primary key/point 수
- orphan artifact 수
- recovery wall-clock time
- GC 후 current answer 유지 여부

pre-publish crash에서는 manifest v1과 old evidence가 유지되어야 한다. post-publish crash에서는 manifest v2와 준비된 new evidence가 보여야 한다. partial staging artifact는 active snapshot에서 보이지 않아야 한다.

## 6. 게이트

### B0 데이터·하니스

- 도메인별 fact 40개
- initial checkpoint snapshot answer accuracy 100%
- 모든 checkpoint/scenario 완료
- worker/client exception이 예상 주입 지점 밖에서는 0

### B1 답변 영향과 staged 유효성

- 두 도메인 모두 naive의 v2-active current-answer error ≥5%
- read-filter 대비 staged의 v2-active current-answer accuracy 개선 ≥5%p
- staged snapshot answer error ≤1%, Wilson 95% CI 상한 ≤2%
- pg_atomic snapshot answer error ≤1%, Wilson 95% CI 상한 ≤2%

### B2 client crash 안전성

- crash 직후 snapshot answer error 0
- recovery 후 snapshot answer error 0
- 두 시점을 합친 Wilson 95% CI 상한 ≤1%
- duplicate logical row/point 0
- active manifest가 참조하지만 readiness가 불완전한 fact 0
- GC 후 current answer error 0

### B3 복구 가능성

- 모든 scenario에서 recovery 완료
- scenario별 p95 recovery time을 보고
- 무한 retry, 수동 DB 수정 또는 전체 corpus rebuild가 필요한 scenario 0

## 7. 자동 판정

| 판정 | 조건 |
|---|---|
| `DATA_OR_HARNESS_FAILURE` | B0 실패 |
| `STOP_NO_ANSWER_LEVEL_VALUE` | B0 통과, B1 실패 |
| `STOP_RECOVERY_PROTOCOL_UNSAFE` | B0·B1 통과, B2 또는 B3 실패 |
| `GO_FRESHEVIDENCEDB_CORE_TOPIC` | B0·B1·B2·B3 통과 |

GO는 core research problem의 확정을 뜻한다. 상위 학회 수준 확정은 실제 서비스 trace, storage-server crash/network fault, native engine 기능과의 공정한 비교, 최신 문헌 재감사가 추가로 필요하다.

## 8. 금지 해석

- cloze accuracy를 일반 생성형 QA 정확도로 표현하지 않는다.
- phase checkpoint 평균을 운영 오류 발생률로 표현하지 않는다.
- client reconnect 성공을 database crash-consistency 보장으로 표현하지 않는다.
- PostgreSQL 단일 트랜잭션보다 우월하다고 표현하지 않는다.
- staging, two-phase publish, MVCC 자체를 신규 발명으로 표현하지 않는다.
