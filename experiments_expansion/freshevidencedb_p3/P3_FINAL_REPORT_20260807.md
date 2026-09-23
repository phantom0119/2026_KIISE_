# FreshEvidenceDB P3 실제 trace·4-artifact·장애·상태기계 최종 보고서

- 수행일: 2026-08-07
- 사전등록 자동 판정: **`CONDITIONAL_P3_TRACE_OR_HUMAN_PENDING`**
- 시스템 안전성: T2·T4·상태기계 통과
- 적용성: T1 형식상 통과, 단일 인기 page 의존도가 매우 큼
- 비용 정책: T3 **`INTEGRATED_DB_PREFERRED`**
- 모델·사람 게이트: T5 **`MODEL_RESOURCE_PENDING`**, 사람 검수 0/38
- 연구 주제 결론: **EDBT급 최종 주제로 확정하지 않는다. 이질적 외부 저장소가 강제되는 고위험 서비스의 좁은 후보로만 유지한다.**

## 1. 결론

P3는 FreshEvidenceDB의 핵심 프로토콜이 dense·sparse·graph·cache 네 파생 저장소를 동일 epoch으로 안전하게 공개하고 장애 후 복구할 수 있음을 보였다. Flask와 Kubernetes 실제 revision에서 eager 공개는 checkpoint 오류가 71.43%, exact version filter도 57.14%였지만 staged 공개는 도메인별 600건에서 오류 0이었다. 실제 subprocess coordinator `SIGKILL`, 저장소 pause/kill, 메시지 순서 교란을 포함한 28개 실행의 재기동·복구 snapshot 1,400건도 오류 0이었다. 유한 상태 탐색에서도 staged protocol의 도달 상태 54개에 위반이 없었고 eager control에서는 45개 반례가 나왔다.

그러나 연구 주제 확정에 더 중요한 비용 결과는 부정적이다. staged 4-store 갱신 p95는 1.39~1.46초로, 한 PostgreSQL transaction에 네 논리 artifact를 함께 쓰는 기준선 11.55~14.05ms보다 **99.12~126.49배 느렸다**. 두 방식 모두 오류 0이므로 통합 DB를 쓸 수 있는 workload에는 별도 coordinator의 실익이 없다. 사전등록 규칙에 따라 T3는 `INTEGRATED_DB_PREFERRED`다.

공개 trace도 범용성을 입증하지 못했다. Wikipedia의 실제 일별 user pageviews 41,007,031건과 revision 1,740건을 결합한 연간 예상 unsafe observation은 62.31건이었으나, 이 중 **97.56%가 ChatGPT 한 페이지**에서 나왔다. 이는 실제 개별 RAG 질의와 stale answer를 관측한 결과가 아니라, 일별 집계 안에서 질의 도착이 균등/Poisson이라는 가정으로 계산한 기대값이다.

마지막으로 Qwen2.5-7B-Instruct 평가는 다른 장기 실험이 두 RTX 3090을 모두 사용해 실행하지 않았고, 사람 검수도 0/38이다. 따라서 end-to-end 답변 개선은 여전히 미확정이다. P3 실행 자체는 정상 종료했지만 사전등록의 전체 `GO_P3_RESEARCH_TOPIC` 조건은 충족하지 못했다.

## 2. 사전등록·무결성

- 최신 선행연구·자산·공유 서비스 상태를 `P3_PRIOR_ART_AND_ASSET_AUDIT_20260807.md`에 기록했다.
- 결과 확인 전에 가설, arm, 임계값, 전체 판정표를 `P3_PREREGISTRATION_20260807.md`와 `PREREGISTRATION_LOCK.sha256`로 고정했다.
- Elasticsearch bulk 문서 구조 수정은 첫 outcome 전에 `P3_IMPLEMENTATION_AMENDMENT_20260807.md`로 기록했다.
- Wikimedia API의 HTTP 429 처리와 응답 cache는 5개 정찰 응답 뒤 전체 gate 실행 전에 `P3_EXECUTION_AMENDMENT_20260807.md`로 기록했다.
- Elasticsearch restart readiness를 yellow/green까지 기다리도록 한 수정은 불완전 smoke run 뒤 결과 파일 생성 전에 `P3_EXECUTION_AMENDMENT_V1_2_20260807.md`로 기록했다.
- 위 변경은 arm, 표본 수, SESOI, 판정 임계값을 바꾸지 않았다. 각 버전의 구현 해시는 `IMPLEMENTATION_LOCK*.sha256`에 보존했다.
- P0 및 P1의 과거 result manifest는 전부 재검증됐다. P2 manifest에서는 P3 결과를 반영해 계속 갱신하는 상위 통합 문서 `../FreshEvidenceDB.md` 한 항목만 예상대로 달라졌고, P2 내부의 보고서·코드·원자료·결과·lock은 모두 일치했다. 과거 P2 manifest는 수정하지 않고 당시 snapshot 증거로 보존한다.

## 3. P3-A 공개 실측 trace

영어 Wikipedia 기술 페이지 12개에 대해 2025-08-01부터 2026-07-31까지 실제 `user` pageviews와 revision timestamp를 수집했다. 조회 원문 JSON과 SHA-256을 보존했다. 계산에는 P2의 더 큰 unsafe exposure p50인 0.062469초/update를 고정 적용했다. 데이터 정의는 [Wikimedia Pageviews API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html)와 [MediaWiki Revisions API](https://www.mediawiki.org/wiki/API:Revisions)를 따른다.

| 항목 | 결과 |
|---|---:|
| 유효 page | 11개 |
| page-day | 4,306 |
| 실제 user views | 41,007,031 |
| 실제 revisions | 1,740 |
| 연간 예상 unsafe observations | 62.3135 |
| 연 0.05건 이상 page | 3개 |
| T1 | `TRACE_APPLICABILITY_PASS` |

| page | views | revisions | 예상 unsafe/year |
|---|---:|---:|---:|
| ChatGPT | 37,586,447 | 821 | 60.7918 |
| Large language model | 1,226,073 | 525 | 1.2971 |
| Retrieval-augmented generation | 502,015 | 82 | 0.0876 |
| 나머지 8개 유효 page 합계 | 1,692,496 | 312 | 0.1369 |

T1은 사전 임계값을 정확히 통과했지만, 세 번째 page인 RAG가 0.0876건이고 전체 값은 ChatGPT에 집중됐다. 따라서 이 결과는 “고인기·고변경 source에서 stale 노출 가능성이 무시할 수 없다”는 근거이지 “일반 기술 문서 RAG에서 흔하다”는 근거가 아니다. 실제 query timestamp도 없으므로 observed incident라고 표현하지 않는다.

## 4. P3-B 네 파생 artifact의 안전성과 비용

P3 전용 Qdrant(dense), PostgreSQL(sparse/catalog), Elasticsearch(graph), fsync SQLite(retrieval cache)에 도메인별 25 changed facts를 기록했다. `eager`, `read_filter`, `staged_all`, `pg_atomic_all`을 각 3회 실행했고 외부 표시 checkpoint를 동일 가중했다.

| 도메인 | 방식 | 오류/관측 | 오류율 | update p95 |
|---|---|---:|---:|---:|
| Flask | eager | 375/525 | 71.43% | 1,189.67ms |
| Flask | read filter | 300/525 | 57.14% | 1,175.50ms |
| Flask | staged all | 0/600 | 0%, 95% 상한 0.636% | 1,461.16ms |
| Flask | PostgreSQL atomic | 0/150 | 0% | 11.55ms |
| Kubernetes | eager | 375/525 | 71.43% | 1,183.35ms |
| Kubernetes | read filter | 300/525 | 57.14% | 1,163.26ms |
| Kubernetes | staged all | 0/600 | 0%, 95% 상한 0.636% | 1,392.76ms |
| Kubernetes | PostgreSQL atomic | 0/150 | 0% | 14.05ms |

- T2: **`FOUR_ARTIFACT_SAFETY_PASS`**
- T3: **`INTEGRATED_DB_PREFERRED`**
- staged/PG update p95 비율: Flask 126.49배, Kubernetes 99.12배

`read_filter`는 v2가 없는 동안 missing을 일으키고 graph/cache의 동시성을 보장하지 못했다. `staged_all`은 모든 store의 실제 read/search 가능성을 확인한 뒤 manifest를 바꿔 이 오류를 제거했다. 하지만 이 구현은 네 network store를 순차 준비하므로 긴 publish lag를 지불했다. 같은 artifact를 단일 DB transaction에 둘 수 있다면 native MVCC가 명백한 기본값이다.

P3-A trace와 결합한 비용 정책에서도 ChatGPT만 예상 오류 60.79건/년, 추가 staged lag 1,124.72초/년, break-even 오류 비용 18.50 publish-second로 상대적으로 유리했다. LLM page는 554.50, RAG는 1,283.03, PostgreSQL page는 1,941.15였다. 이 비율은 서비스별 실제 오류 피해 비용을 측정한 값이 아니며 정책 민감도 지표로만 사용한다.

## 5. P3-C coordinator·저장소 장애

실제 subprocess coordinator를 dense, sparse, graph, cache, READY, publish 뒤에 각각 `SIGKILL`했다. cache/graph 우선 reorder, Qdrant·Elasticsearch pause, Qdrant·PostgreSQL·Elasticsearch 개별 kill과 세 store 동시 kill도 포함했다. 14 scenario × 2 domains를 실행했다.

| 항목 | 결과 |
|---|---:|
| scenario run | 28 |
| restart 직후 + recovery snapshot | 1,400 |
| snapshot 오류 | 0 |
| 합동 Wilson 95% 상한 | 0.2736% |
| duplicate / orphan / GC 오류 | 0 / 0 / 0 |
| recovery p95 | 1,141.43ms |
| store restart p95 | 27,683.17ms |
| T4 | `COORDINATOR_FAULT_PASS` |

durable journal, deterministic upsert, readiness 재검증은 재기동 후 안전성을 유지했다. 다만 restart p95 27.68초는 고가용성에 실패할 수 있는 수준이다. 이 실험은 snapshot safety와 자동 복구를 보였을 뿐, store가 죽어 있는 동안의 서비스 연속성, machine/power loss, quorum durability를 입증하지 않는다.

## 6. P3-D 유한 상태 검증

| protocol | reachable states | invariant violations |
|---|---:|---:|
| staged | 54 | 0 |
| eager sanity control | 99 | 45 |

T-state는 **`STATE_MACHINE_SAFETY_PASS`**다. eager의 최소 반례는 artifact가 하나도 준비되지 않은 상태에서 `publish_v2`가 active epoch을 바꾸는 한 단계 경로다. 이 검증은 축약 상태기계에 대한 exhaustive BFS이며, 실제 분산 시스템의 모든 network interleaving이나 구현 버그를 증명 범위에 포함하지 않는다.

## 7. P3-E 7B 자연화 QA

| 항목 | 결과 |
|---|---:|
| agent 품질 필터 통과 질문 | 38 |
| 사람 검수 | 0 |
| 실행 시 GPU 가용 메모리 | 약 265.4MiB |
| Qwen2.5-7B 실행 | 미실행 |
| T5 | `MODEL_RESOURCE_PENDING` |

두 RTX 3090은 각각 약 23.3GiB를 사용하는 기존 장기 실험이 점유하고 있었다. 이를 중단하지 않는다는 사전등록 원칙에 따라 7B 추론을 강행하지 않았다. 질문도 사람이 검수한 자연 질문이 아니라 source-aware 자동 자연화 cloze에 가깝다. 사람 검수 30개 조건도 미달했으므로 T5의 양성·음성 효과를 주장할 수 없다.

## 8. 전체 판정

| 게이트 | 결과 | 해석 |
|---|---|---|
| T1 공개 trace | `TRACE_APPLICABILITY_PASS` | 형식상 통과, 97.56% 단일 page 집중·일별 기대값 |
| T2 4-artifact safety | `FOUR_ARTIFACT_SAFETY_PASS` | staged가 mixed/missing 제거 |
| T3 비용 | `INTEGRATED_DB_PREFERRED` | staged가 PG atomic보다 99.12~126.49배 느림 |
| T4 장애 | `COORDINATOR_FAULT_PASS` | 재기동 후 안전, restart p95 27.68초 |
| 상태기계 | `STATE_MACHINE_SAFETY_PASS` | 축약 모델에서 staged 위반 0 |
| T5 모델·사람 | `MODEL_RESOURCE_PENDING` | 7B 미실행, 사람 검수 0/38 |

사전등록 전체 판정은 **`CONDITIONAL_P3_TRACE_OR_HUMAN_PENDING`**이다. 판정명에 `TRACE`가 들어가지만 T1 자체는 통과했다. 실질적인 보류 사유는 (1) trace가 한 인기 page와 일별 도착 가정에 의존하고, (2) 통합 DB 비용 기준선에 크게 패하며, (3) 모델·사람 gate가 미완료라는 점이다.

## 9. 연구 가치·신규성 재판정

[StaleBench](https://zenodo.org/records/20710012)는 RAG answer freshness와 refresh/catch-up을, [FinCacheServe](https://arxiv.org/abs/2607.26076)는 answer cache의 evidence/tool/model dependency consistency를, [FreshCache](https://arxiv.org/abs/2607.04281)는 semantic cache freshness risk를 이미 다룬다. [VersionRAG](https://arxiv.org/abs/2510.08109)는 version-sensitive retrieval/QA를 다루며, [SingleStore-V](https://vldb.org/pvldb/vol17/p3772-chen.pdf)와 [PostgreSQL-V](https://www.cidrdb.org/cidr2026/papers/p2-liu.pdf)는 통합·분리 vector index의 일관성 기준선을 제공한다.

따라서 “RAG freshness”, “버전 인지 검색”, “transactional vector update” 자체는 신규 주제가 아니다. 현재 남는 후보는 다음의 좁은 시스템 문제다.

> 트랜잭션 경계가 서로 다른 dense·sparse·graph·cache 저장소가 반드시 공존하는 환경에서, source epoch별 readiness·lineage를 추적하고 한 답변이 동일 epoch만 보도록 공개·복구하며 비용과 가용성까지 최적화하는 coordinator

P3는 이 coordinator의 safety 가능성을 지지한다. 그러나 순차 prototype의 비용은 매우 크고 통합 DB가 더 낫다. 그러므로 “최초”라고 주장하거나 EDBT급 주제로 확정할 증거는 아직 없다.

## 10. 연구 주제 확정 전에 필요한 최소 후속 작업

1. QA 38개 중 최소 30개를 도메인 지식이 있는 사람이 검수하고, 어색한 cloze·링크/철자 교체 위주의 문항을 실제 서비스형 질문으로 교체한다.
2. 현재 GPU 작업 종료 뒤 locked Qwen2.5-7B-Instruct를 실행해 T5를 판정한다. 결과가 기준 미달이면 end-to-end 기여를 축소하거나 중단한다.
3. Wikipedia 일별 aggregate가 아니라 개별 query/update timestamp가 있는 공개 또는 내부 RAG trace에서 실제 stale/mixed answer 사건을 측정한다.
4. 네 store 준비를 병렬화하고 비동기 barrier·batching을 구현해 99~126배 publish 비용을 줄인 뒤 T3를 다시 판정한다.
5. 통합 PostgreSQL, vendor-native alias/snapshot, cross-store coordinator를 동일 network·durability 조건에서 비교한다.
6. 위 작업 뒤에도 integrated baseline 대비 실질적 이익이 없으면 FreshEvidenceDB를 최종 주제가 아니라 재현 가능한 engineering/fault-study로 종료한다.

## 11. 재현 자료

- 사전등록·감사: `P3_PRIOR_ART_AND_ASSET_AUDIT_20260807.md`, `P3_PREREGISTRATION_20260807.md`
- 변경 이력: `P3_IMPLEMENTATION_AMENDMENT_20260807.md`, `P3_EXECUTION_AMENDMENT_20260807.md`, `P3_EXECUTION_AMENDMENT_V1_2_20260807.md`
- 실행 코드: `run_p3a_wikimedia_trace.py`, `run_p3b_four_artifact.py`, `run_p3c_faults.py`, `run_p3d_model_check.py`, `build_p3e_natural_qa.py`, `run_p3e_qwen7b.py`
- 결과: `results_p3a/`~`results_p3e/`, `qa_review.csv`, `qa_review.json`
- 무결성: `PREREGISTRATION_LOCK.sha256`, `IMPLEMENTATION_LOCK*.sha256`, `RESULT_MANIFEST.sha256`
