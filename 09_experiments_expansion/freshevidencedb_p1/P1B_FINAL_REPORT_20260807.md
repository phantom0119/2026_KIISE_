# FreshEvidenceDB P1-B 답변 영향·client crash 최종 보고서

- 수행일: 2026-08-07
- 자동 판정: **`GO_FRESHEVIDENCEDB_CORE_TOPIC`**
- 게이트 B0–B3: 모두 통과
- 최종 의미: **core research problem 확정, 상위 학회용 전체 시스템은 P2 조건부**

## 1. 결론

실제 revision에서 자동 추출한 변경 답변을 사용한 결정론적 cloze 평가에서, 순차 cross-store 갱신은 v2-active checkpoint의 최신 답변 정확도가 20%, 단순 version filter는 60%였다. staged publication과 PostgreSQL atomic transaction은 100%였다. 이 수치는 externally visible phase를 동일 가중한 값이며 wall-clock 운영 정확도가 아니다.

partial dense write, dense 완료, sparse 완료, publish 후 GC 전 crash, duplicate retry의 다섯 client 장애 시나리오를 두 도메인에서 3회씩 수행했다. crash 직후와 idempotent recovery 후 합계 1,500개 snapshot-answer 관측에서 오류 0건, GC 후 750개에서 오류 0건, 중복·고아 artifact 0건이었다. recovery p95는 77.00ms였다.

따라서 **이질적인 RAG 파생 저장소 사이에서 answer-visible snapshot을 공개하는 문제는 연구 주제로 계속할 실증 근거가 있다.** 다만 자동 cloze와 client restart만 통과했으므로 자연 QA·LLM, 실제 서비스 trace와 storage process/network 장애까지 확장하기 전에는 완성된 상위 학회 논문으로 평가하지 않는다.

## 2. 데이터 게이트 수정 기록

최초 사전등록은 도메인별 changed fact 40개를 요구했다. old answer가 new 문서 전체에 없고 new answer가 old 문서 전체에 없어야 한다는 엄격한 누설 방지 규칙에서 Flask 27개, Kubernetes 25개만 확보됐다. 첫 추출은 Flask에서 예외로 중단했으며 답변·장애 결과는 생성하지 않았다.

결과 확인 전에 v1.1 amendment를 작성해 목표를 25개로 낮추고 모든 protocol/scenario를 3회 반복했다. 누설 방지 규칙과 성공 임계값은 변경하지 않았다.

## 3. 답변 checkpoint 결과

도메인마다 fact 25개 × 3회 반복이다.

| 도메인 | 프로토콜 | 관측 | snapshot 오류 | v2-active 최신 답변 정확도 | missing | ambiguous |
|---|---|---:|---:|---:|---:|---:|
| Flask | cross naive | 450 | 66.67% | 20.00% | 33.33% | 33.33% |
| Flask | read filter | 450 | 33.33% | 60.00% | 33.33% | 0% |
| Flask | staged | 450 | 0% | 100% | 0% | 0% |
| Flask | pg atomic | 150 | 0% | 100% | 0% | 0% |
| Kubernetes | cross naive | 450 | 66.67% | 20.00% | 33.33% | 33.33% |
| Kubernetes | read filter | 450 | 33.33% | 60.00% | 33.33% | 0% |
| Kubernetes | staged | 450 | 0% | 100% | 0% | 0% |
| Kubernetes | pg atomic | 150 | 0% | 100% | 0% | 0% |

naive·filter의 비율이 두 도메인에서 정확히 같은 것은 protocol당 checkpoint 수와 동일 phase 가중치가 같기 때문이다. 이는 자연 query timing을 측정한 결과가 아니라 각 상태가 답변에 미치는 인과적 결과를 확인하는 state-machine 검사다.

staged 전체 900건의 0-error Wilson 95% 상한은 약 0.425%, pg atomic 전체 300건은 약 1.264%다. pg atomic을 도메인별 150건으로 분리하면 각 상한은 약 2.497%이므로, 도메인별 정밀도를 주장하려면 표본을 늘려야 한다.

## 4. 장애 주입 결과

| 항목 | 결과 |
|---|---:|
| scenario run | 30회 |
| crash 직후 + recovery 후 관측 | 1,500 |
| snapshot answer 오류 | 0 |
| Wilson 95% 상한 | 0.255% |
| GC 후 관측 | 750 |
| GC 후 오류 | 0 |
| duplicate row/point | 0 |
| GC 후 orphan artifact | 0 |
| readiness audit 실패 | 0 |
| recovery p50 | 41.54ms |
| recovery p95 | 77.00ms |

pre-publish crash에서는 manifest가 v1을 유지해 부분적으로 준비된 v2가 보이지 않았다. post-publish crash에서는 모든 v2 artifact가 이미 준비되어 있었으므로 v2가 보였다. 동일 ID upsert와 PostgreSQL primary key를 사용한 중복 retry는 추가 logical artifact를 만들지 않았다.

## 5. 게이트

| 게이트 | 결과 |
|---|---|
| B0 데이터·하니스 | 통과 |
| B1 답변 수준 가치 | 통과 |
| B2 client crash 안전성 | 통과 |
| B3 자동 복구 가능성 | 통과 |

자동 판정은 `GO_FRESHEVIDENCEDB_CORE_TOPIC`이다.

## 6. 연구 주제로서의 최종 범위

### 채택할 문제 정의

> 외부 vector, sparse, graph, cache 등 서로 다른 트랜잭션 경계를 가진 RAG 파생 저장소를 비동기로 갱신할 때, source-to-artifact lineage와 readiness를 추적하고 한 질의가 동일 source epoch의 증거만 읽도록 원자적으로 공개·복구하는 시스템

### 주장하면 안 되는 것

- version-aware RAG의 최초 제안
- transactional vector update의 최초 제안
- staging, two-phase publish 또는 MVCC의 발명
- PostgreSQL 통합 transaction보다 우월함
- 이번 cloze 결과가 일반 LLM QA 정확도를 대표함
- client reconnect 결과가 storage server crash-consistency를 증명함

## 7. P2 필수 작업

1. 실제 서비스 또는 재현 가능한 update/query trace로 phase 체류시간과 workload prevalence 측정
2. 사람이 검수한 changed-fact 질문 및 고정 LLM을 사용한 생성 답변 평가
3. Qdrant/PostgreSQL process kill, network partition, message reorder, timeout, coordinator crash
4. graph index, retrieval/answer cache, ACL revoke, parser/chunker/embedder migration 포함
5. PostgreSQL/pgvector 통합 기준선 외 Weaviate 또는 Milvus native 기능 비교
6. snapshot token, readiness vector, watermark와 GC의 정형 상태기계·안전성 명세
7. publish lag·query SLA·space/write amplification의 비용 정책
8. 최신 문헌 재감사와 동일 문제를 직접 다루는 시스템 존재 여부 확인

이 P2를 통과해야 EDBT 이상 시스템 논문으로서의 수준을 평가할 수 있다.

## 8. 재현 자료

- `P1B_ANSWER_FAILURE_PREREGISTRATION.md`
- `P1B_V1_1_DATA_AMENDMENT.md`
- `changed_fact_manifest.json`
- `build_changed_facts.py`
- `run_p1b_answer_failure.py`
- `results_p1b_run1/answer_checkpoints.csv`
- `results_p1b_run1/fault_checkpoints.csv`
- `results_p1b_run1/fault_audits.csv`
- `results_p1b_run1/aggregate.json`
- `results_p1b_run1/RESULT_MANIFEST.sha256`
