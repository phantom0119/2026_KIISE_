# FreshEvidenceDB

> 영문 가제: **FreshEvidenceDB: Snapshot-Consistent Publication of Derived Evidence Across Heterogeneous RAG Stores**
>
> 국문 가제: **비동기 다중 저장소 RAG를 위한 증거 스냅샷 일관성 및 단계적 공개**

- 문서 상태: **P3 실행 완료 — 시스템 안전성 통과, 통합 DB 대비 비용 열세, 7B·사람 검수 보류**
- 최종 연구 주제 확정: **보류 — 이질적 외부 저장소가 강제되는 고위험 workload의 좁은 후보로만 유지**
- 최근 판정일: 2026-08-07
- 직접 근거: `freshevidencedb_p1/P1A_FINAL_REPORT_20260807.md`, `freshevidencedb_p1/P1B_FINAL_REPORT_20260807.md`, `freshevidencedb_p2/P2_FINAL_REPORT_20260807.md`, `freshevidencedb_p3/P3_FINAL_REPORT_20260807.md`

## 1. 한 문장 설명

FreshEvidenceDB는 원문이 수정·삭제되거나 파서·청킹·임베딩이 바뀔 때, 정본 DB와 dense·sparse·graph·cache에 흩어진 파생 증거를 먼저 준비한 뒤 동일 source epoch으로 공개하여, 한 RAG 답변이 오래된 증거나 서로 다른 버전의 증거를 섞어 읽지 않도록 하는 데이터베이스 계층이다.

## 2. 문제 배경

운영 RAG에서 한 문서의 내용은 하나의 저장소에만 있지 않다.

```text
원문 revision
  ├─ 파싱 결과
  ├─ 청크/명제/표 행
  ├─ dense embedding과 ANN index
  ├─ sparse/keyword index
  ├─ 지식 그래프의 node/edge
  └─ retrieval/answer cache
```

원문을 수정하거나 삭제해도 이 파생물은 동시에 바뀌지 않는다. 예를 들어 catalog는 v2를 활성화했지만 dense index는 v1, sparse index는 v2, cache는 v1일 수 있다. 이때 각 저장소는 자체적으로 정상이어도 한 질의는 존재하지 않는 혼합 세계를 읽는다.

단순히 각 결과에 `version=v2` 필터를 걸면 오래된 증거는 막을 수 있다. 그러나 v2 embedding이 아직 준비되지 않은 동안 정답 증거가 전부 사라진다. 반대로 전체 corpus를 blue/green으로 복제하면 일관성은 얻지만 작은 수정에도 전체 색인을 다시 쓰게 된다.

따라서 핵심 문제는 “더 좋은 임베딩”이 아니라 다음 DB 문제다.

> 비동기로 생성되는 이질적인 RAG 파생물에 대해, 질의 단위의 동일 snapshot을 낮은 publish 지연과 쓰기 비용으로 어떻게 제공할 것인가?

## 3. P0에서 실제로 확인한 것

P0는 문서 128개, 수정·재청킹·삭제 8 wave, query worker 4개, 독립 반복 5회로 수행했다. 실제 Qdrant dense index와 SQLite FTS5/catalog를 사용했다.

| 방식 | update-window 오류 | missing | p95 | 쓰기 증폭 |
|---|---:|---:|---:|---:|
| 순차 eager 갱신 | 70.19% | 25.65% | 31.12 ms | 1.00× |
| 읽기 버전 필터 | 15.19% | 15.19% | 31.65 ms | 1.00× |
| 전체 blue/green | 0% | 0% | 90.09 ms | 8.39× |
| staged manifest | 0% | 0% | 31.69 ms | 1.00× |

판정은 `CONDITIONAL_GO_REAL_REVISION_CROSS_ENGINE`이다. 즉 오류 발생 가능성과 최소 해결 방식은 확인했지만, 실제 발생률·엔진 일반성·답변 영향은 아직 검증하지 않았다.

### 3.1 P1-A 실제 revision·교차 엔진 결과

Flask와 Kubernetes 공식 문서의 실제 revision pair를 각각 100개 사용하고 인공 phase 지연을 제거했다.

| 도메인 | 방식 | update-window 오류 | p95 | 쓰기 증폭 |
|---|---|---:|---:|---:|
| Flask | 순차 cross-store | 76.34% | 53.28ms | 1.00× |
| Flask | exact version filter | 70.68% | 55.72ms | 1.00× |
| Flask | staged | 0% | 49.86ms | 1.00× |
| Flask | blue/green | 0% | 66.04ms | 9.97× |
| Flask | PostgreSQL atomic | 0% | 20.52ms | 1.00× |
| Kubernetes | 순차 cross-store | 73.73% | 55.80ms | 1.00× |
| Kubernetes | exact version filter | 70.71% | 55.93ms | 1.00× |
| Kubernetes | staged | 0% | 53.45ms | 1.00× |
| Kubernetes | blue/green | 0% | 70.43ms | 9.90× |
| Kubernetes | PostgreSQL atomic | 0% | 22.05ms | 1.00× |

이 비율은 변경 문서에 query를 80% 집중한 stress rate다. 운영 발생률이 아니다. P1-A의 핵심 결론은 오류가 강제 sleep 없이도 발생하며, 통합 PostgreSQL transaction이 가능한 배치에서는 native MVCC가 더 단순하고 빠르다는 것이다.

### 3.2 P1-B 답변·client crash 결과

실제 revision에서 도메인별 25개의 changed-answer cloze를 자동 추출해 각 externally visible phase를 동일 가중했다.

| 방식 | v2-active 최신 답변 정확도 | snapshot 오류 |
|---|---:|---:|
| 순차 cross-store | 20% | 66.67% |
| exact version filter | 60% | 33.33% |
| staged | 100% | 0% |
| PostgreSQL atomic | 100% | 0% |

5개 client crash/retry scenario를 2개 도메인에서 3회씩 수행한 결과, crash 직후·복구 후 1,500개 관측과 GC 후 750개 관측에서 오류 0건이었다. duplicate와 GC 후 orphan도 0건, recovery p95는 77.00ms였다.

자동 판정은 `GO_FRESHEVIDENCEDB_CORE_TOPIC`이다. 다만 cloze·phase 동일 가중치·client restart라는 제한 때문에 자연 생성 QA와 storage-server 장애는 P2에서 별도로 검증한다.

### 3.3 P2 적용 범위·교차 엔진·server fault·모델 결과

P2는 결과 실행 전에 사전등록과 구현 해시를 고정하고 네 개의 검증을 수행했다.

| 게이트 | 결과 | 핵심 수치 |
|---|---|---|
| 실제 timestamp 적용성 | `APPLICABLE_HIGH_TRAFFIC` | Kubernetes형 workload break-even 18.80qps, Flask 304.99qps |
| Weaviate 교차 엔진 | `CROSS_ENGINE_GENERALIZED` | naive/filter 오류 약 91.5–91.9%, staged 11,695건 오류 0 |
| 실제 server fault | `SERVER_FAULT_GATE_PASS` | 20회 kill/pause, restart·recovery 1,000건 오류 0, duplicate/orphan 0 |
| CPU 1B 모델 | `MODEL_GATE_INCONCLUSIVE` | current-only 최신 답변 32%로 competence 기준 70% 미달 |

전체 판정은 `CONDITIONAL_GO_NICHE_OR_MODEL_PENDING`이다. P2는 저장 문제의 엔진 일반성과 재기동 후 snapshot safety를 강화했지만, 모든 RAG에 필요한 문제임을 보이지 않았다. 적용성은 변경이 잦고 변경 문서가 집중 조회되는 workload에 한정되며, 1B 모델은 prompt를 따를 역량이 부족해 end-to-end 답변 가치를 판정하지 못했다.

Weaviate staged publication은 오류를 제거하는 대신 wave p95가 약 1.02–1.05초로 naive보다 길었다. server fault의 restart p95도 6.22초였으므로, 일관성뿐 아니라 publish lag와 availability가 이후 연구의 핵심 trade-off다.

### 3.4 P3 실제 trace·4-artifact·coordinator 결과

P3는 Wikimedia 실제 일별 user pageviews와 revision timestamp, dense·sparse·graph·cache 네 파생 저장소, 실제 coordinator와 저장소 장애, 유한 상태 검증을 추가했다.

| 게이트 | 결과 | 핵심 수치 |
|---|---|---|
| 공개 trace 적용성 | `TRACE_APPLICABILITY_PASS` | 4,306 page-day, 예상 62.31건/년; 97.56%가 ChatGPT page에 집중 |
| 4-artifact 안전성 | `FOUR_ARTIFACT_SAFETY_PASS` | eager 71.43%, filter 57.14%, staged 1,200건 오류 0 |
| 비용 정책 | `INTEGRATED_DB_PREFERRED` | staged update p95가 PostgreSQL atomic보다 99.12~126.49배 느림 |
| coordinator fault | `COORDINATOR_FAULT_PASS` | 28 scenario, 재기동·복구 snapshot 1,400건 오류 0 |
| 상태기계 | `STATE_MACHINE_SAFETY_PASS` | staged 54상태 위반 0, eager 반례 45개 |
| 7B·사람 QA | `MODEL_RESOURCE_PENDING` | 두 GPU 기존 작업 점유, 사람 검수 0/38 |

전체 사전등록 판정은 `CONDITIONAL_P3_TRACE_OR_HUMAN_PENDING`이다. 시스템 safety 가능성은 강화됐지만, 순차 cross-store coordinator의 비용이 통합 transaction보다 지나치게 크고 실제 노출 기대값도 한 인기 page에 편중됐다. 따라서 P3는 연구 주제를 확정한 실험이 아니라 **적용 범위를 이질적 외부 저장소가 반드시 필요한 고위험 서비스로 좁힌 실험**이다.

Wikimedia 결과는 실제 개별 RAG query와 stale answer 사건이 아니다. 일별 pageview aggregate 안에서 도착이 균등/Poisson이라는 가정과 P2의 오류창을 결합한 기대값이므로 운영 장애율로 표현하지 않는다.

## 4. 연구 질문

### RQ1. 실제 수정 이력에서 cross-store freshness 오류가 발생하는가?

실제 Git 문서와 법령·규정 개정 이력을 replay할 때 stale, mixed, missing evidence가 어느 조건에서 발생하는지 측정한다. update rate, artifact 생성 지연, 삭제·재청킹 비율에 따른 발생 곡선을 보고한다.

### RQ2. 단순 version filter와 native engine 기능으로 충분한가?

read-time filter, 엔진 native consistency, 통합 MVCC DB가 답변 정확도·가용성·지연 SLA를 모두 만족하는지 검증한다. 이들이 충분하면 별도 시스템 연구를 중단한다.

### RQ3. staged publication이 일관성과 비용을 함께 개선하는가?

변경분만 staging하고 manifest를 원자 전환할 때 stale/mixed/missing, publish lag, query tail latency, update throughput, write amplification을 blue/green 및 통합 DB와 비교한다.

### RQ4. 검색 오류가 최종 답변에 미치는 영향은 무엇인가?

동일 생성 모델과 prompt를 고정하고 최신 정답 정확도, 철회된 사실 사용률, 인용 provenance 정확도를 측정한다. Retrieval 지표의 차이가 실제 답변 차이로 이어지지 않으면 기여를 축소하거나 중단한다.

### RQ5. 실패 상황에서도 snapshot 보장이 유지되는가?

artifact 생성 실패, worker crash, 중복 retry, manifest 전환 직전/직후 장애, 지연된 삭제와 GC 상황에서 atomicity·idempotence·복구 시간을 검증한다.

## 5. 제안 시스템

### 5.1 핵심 메타데이터

| 객체 | 필수 필드 |
|---|---|
| source revision | `source_id`, `epoch`, `content_hash`, `commit_time`, `operation` |
| derived artifact | `artifact_id`, `source_id`, `epoch`, `type`, `generator_version`, `content_hash`, `state` |
| lineage edge | `parent_artifact`, `child_artifact`, `transformation`, `config_hash` |
| manifest | `source_id`, `active_epoch`, `required_artifact_set`, `publish_time` |
| query snapshot | `snapshot_token`, `manifest_epoch/vector`, `start_time` |

### 5.2 상태 전이

```text
NEW SOURCE EPOCH
      │
      ▼
  STAGING ── 파싱/청킹/임베딩/dense/sparse/graph/cache 준비
      │
      ├─ 일부 실패 ──> ABORTED 또는 RETRY
      │
      ▼
    READY ── 모든 필수 artifact와 hash/lineage 확인
      │
      ▼ atomic manifest publish
    ACTIVE
      │
      ▼ watermark 이후
   RETIRED ──> GC
```

### 5.3 질의 프로토콜

1. 질의 시작 시 manifest snapshot token을 한 번 읽는다.
2. dense, sparse, graph, cache 요청에 같은 token/epoch을 전달한다.
3. 모든 evidence가 허용된 snapshot에 속하는지 provenance를 검증한다.
4. 일부 저장소가 준비되지 않았다는 이유로 새 epoch와 구 epoch을 임의 혼합하지 않는다.
5. 요청 종료 후 token을 해제하고 GC watermark를 전진시킨다.

### 5.4 공개 프로토콜

1. source revision commit과 새 epoch 발급
2. 변경 영향 범위를 lineage DAG에서 계산
3. 필요한 파생물만 staging 영역에 생성
4. 저장소별 readiness와 checksum 기록
5. 필수 readiness vector가 충족되면 manifest를 원자 전환
6. 진행 중인 구 snapshot query가 종료될 때까지 구 artifact 유지
7. watermark 이후 구 artifact와 orphan을 회수

### 5.5 구현에서 새로워야 할 부분

staging과 pointer flip 자체는 알려진 DB 기법이다. 논문 기여가 되려면 다음 중 여러 항목이 필요하다.

- 이질적 저장소의 readiness를 하나의 answer-visible consistency 계약으로 연결
- source·parser·chunker·embedder·ACL 버전을 포함한 lineage 기반 영향 분석
- query snapshot token과 저장소별 capability가 다른 환경의 실행 프로토콜
- publish lag, availability, write amplification을 함께 최적화하는 정책
- crash/retry와 partial readiness에서 안전한 복구·GC
- retrieval 오류가 최종 답변 최신성과 근거성에 미치는 end-to-end benchmark

## 6. 비교 기준선

| 분류 | 기준선 |
|---|---|
| 무방비 | delete/upsert 또는 catalog-first eager update |
| 단순 방어 | read-time exact version filter |
| 복제 | 전체 corpus blue/green snapshot/alias 전환 |
| 통합 DB | PostgreSQL/pgvector 또는 SingleStore형 MVCC 구성 |
| 외부 vector DB | Qdrant, Weaviate 또는 Milvus의 native update/filter/consistency |
| 버전 인지 RAG | VersionRAG형 logical version routing |
| 제안 | lineage-aware staged artifact publication + query snapshot token |

## 7. 선행연구와 남는 공백

### 7.1 이미 점유된 범위

- [VersionRAG](https://arxiv.org/abs/2510.08109): 문서 버전 관계, 변경 추적과 version-sensitive QA
- [SingleStore-V](https://vldb.org/pvldb/vol17/p3772-chen.pdf): 통합 DB 내부의 MVCC 기반 vector update/delete와 consistent snapshot read
- [Fast Vector Search in PostgreSQL: A Decoupled Approach](https://www.cidrdb.org/cidr2026/papers/p2-liu.pdf): host DB와 분리 vector index 사이의 consistency mechanism
- [MCHRAG](https://dblp.org/rec/conf/mir/RenLZPL26.html): streaming corpus를 위한 증분 RAG indexing
- [StaleBench](https://zenodo.org/records/20710012): 문서 변경 이후 answer freshness, refresh policy, catch-up latency와 context position bias
- [FinCacheServe](https://arxiv.org/abs/2607.26076): 문서·evidence·tool·model dependency 기반 answer-cache consistency
- [FreshCache](https://arxiv.org/abs/2607.04281): semantic cache의 freshness risk와 stale reuse

따라서 version-aware QA, transactional vector update, incremental index, 일반적인 answer freshness 또는 cache consistency라는 표현만으로는 신규성이 없다.

### 7.2 현재 남은 후보 공백

현재 확인한 범위에서 좁게 남는 것은 다음 결합이다.

1. parser/embedding을 포함해 정본에서 파생된 여러 evidence store의 비동기 갱신
2. 한 답변이 동일 source epoch만 보도록 하는 cross-store publication/snapshot 계약
3. stale·mixed·missing을 검색 단계와 최종 답변 단계에서 함께 측정
4. blue/green, version filter, 통합 MVCC와의 비용·가용성 비교
5. crash/retry/GC/ACL·모델 migration을 포함한 수명주기 보장

이는 “최초”로 확정된 상태가 아니다. P3 최신 감사에서도 넓은 freshness 주장은 이미 점유된 것으로 확인됐다. 남는 후보는 여러 retrieval artifact의 readiness·lineage·cross-store publication과 recovery coordinator이며, 투고 전에는 월 단위 신규 논문을 다시 확인해야 한다.

## 8. P1 실험 설계

### 8.1 데이터셋

- 실제 Git revision이 있는 기술 문서 2개 도메인 이상
- 실제 개정 이력이 있는 법령·규정 1개 도메인 권장
- 도메인별 revision event 최소 100개
- 수정, 삭제, rename, split/merge, re-chunk를 포함
- 질문은 각 revision의 changed fact와 unchanged control fact를 함께 포함

VersionQA 등 외부 데이터는 라이선스를 확인한 뒤 보조 평가에만 사용한다. 라이선스가 불명확한 자료는 재배포하지 않는다.

### 8.2 저장 구성

1. Qdrant dense + SQLite FTS/catalog/cache
2. PostgreSQL+pgvector 통합 구성
3. 여력이 있으면 Weaviate 또는 Milvus 구성 추가
4. Graph index는 P1 핵심 결과가 나온 뒤 별도 ablation으로 추가

### 8.3 workload 요인

- update arrival rate
- embedding/index build 지연
- 질의와 갱신의 동시성
- changed-document query 비율
- revision 유형
- chunker/embedder/parser migration
- delete와 ACL revoke
- worker/storage failure 시점

### 8.4 지표

#### 정확성

- stale, future, mixed, missing evidence rate
- current fact answer accuracy
- revoked/deleted fact leakage
- citation source/epoch correctness

#### 시스템

- source commit-to-publish lag
- p50/p95/p99 query latency
- update throughput와 backlog
- write/read/space amplification
- recovery time, duplicate/orphan artifact, GC lag

#### 통계

- revision/document를 cluster로 처리
- 비율에는 Wilson 95% CI
- protocol 비교에는 동일 query/revision paired analysis
- domain과 engine에 대한 층화 결과를 전부 보고
- SESOI와 중단 기준을 P1 실행 전에 고정

### 8.5 P1 게이트

#### 진행

- 최소 두 실제 도메인·두 저장 구성에서 문제가 실질적으로 관측됨
- staged의 stale/mixed ≤1%
- 단순 filter보다 current answer accuracy +5%p 또는 동등 정확도에서 시스템 비용의 실질 개선
- naive 대비 p95 증가 ≤15%
- blue/green 대비 쓰기 증폭 최소 5배 감소
- crash/retry 이후 동일 epoch 보장

#### 중단

- 실제 workload에서 문제 발생률과 답변 영향이 모두 미미함
- exact version filter나 native engine 기능으로 충분함
- 통합 MVCC가 모든 대상 workload를 더 단순하고 싸게 해결함
- staged의 이익이 P0의 강제 delay에서만 나타남
- 새로운 기여 없이 기존 two-phase publish를 재구현하는 수준에 머묾

## 9. 개발 순서

1. 실제 revision replay loader와 changed-fact QA 작성
2. P1 사전등록과 문헌 재감사
3. Qdrant+SQLite 구성에서 P0를 실제 이력으로 재현
4. PostgreSQL+pgvector 통합 기준선 구현
5. snapshot token, readiness vector, manifest publish 최소 구현
6. crash/retry와 GC fault injection
7. 최종 답변 평가 연결
8. P1 게이트 통과 시에만 graph/cache/ACL/model migration 확대

## 10. 객관적 타당성 판정

| 항목 | 현재 판정 | 이유 |
|---|---|---|
| 문제 존재성 | 통과 | P0 및 실제 revision P1-A의 두 도메인에서 재현 |
| 단순 해법의 불충분성 | 통과 | 실제 revision에서 version filter missing 약 70.7% |
| 최소 해결 가능성 | 통과 | P1-A staged 14,040 update-window 질의 오류 0 |
| 시스템 trade-off | 통과 | blue/green 대비 쓰기 약 9.9배 절감 |
| 실제 revision 타당성 | 통과 | Flask·Kubernetes 공식 문서 각 100 revision pair |
| 통합 DB 기준선 | 통과 | PostgreSQL atomic 12,738 update-window 질의 오류 0 |
| 답변 수준 가치 | 제한적 통과 | changed-answer cloze에서 staged 100%, filter 60% |
| client crash 복구 | 통과 | 30 scenario run, 오류·중복·GC 후 orphan 0 |
| timestamp 기반 적용성 | 제한적 통과 | Kubernetes형 18.80qps, Flask형 304.99qps에서 하루 1건 예상 |
| vector engine 일반성 | 통과 | Weaviate staged 11,695 update-window 질의 오류 0 |
| server process 장애 | 통과 | kill/pause 20회, restart·recovery 1,000건 오류 0 |
| 4-artifact snapshot safety | 통과 | dense·sparse·graph·cache staged 1,200건 오류 0 |
| coordinator/storage fault | 통과 | P3 28 scenario, snapshot 1,400건 오류 0 |
| 축약 상태기계 safety | 통과 | staged 54 reachable state 위반 0, eager 반례 45개 |
| 공개 trace 적용성 | 제한적 통과 | 62.31건/년 기대값 중 97.56%가 ChatGPT page에 집중 |
| cross-store 비용 경쟁력 | 실패 | staged update p95가 PG atomic보다 99.12~126.49배 느림 |
| 자연 서비스 타당성 | 미확인 | 실제 개별 RAG query trace와 사람이 만든 자연 QA가 필요 |
| 생성 모델 답변 | 미확정 | CPU 1B competence 실패, P3 7B는 GPU 점유로 미실행 |
| 학술 신규성 | 조건부 | 넓은 freshness는 점유, cross-store artifact publication coordinator만 후보 |
| 핵심 연구 주제 | 좁은 조건부 유지 | 이질적 외부 저장소가 강제되는 고위험 workload만 후보 |
| 상위 학회용 전체 시스템 | 보류 | 비용 최적화·개별 trace·7B/사람 QA에서 재검증 필요 |

## 11. 현재 권고

FreshEvidenceDB를 **현재 최종 연구 주제로 확정하지 않는다.** P3에서 네 artifact의 snapshot safety, 장애 복구, 상태기계는 통과했지만, cross-store staged 갱신이 통합 PostgreSQL transaction보다 99.12~126.49배 느렸다. 통합 DB가 가능한 workload에는 FreshEvidenceDB를 권하지 않는다.

후속 작업은 이질적 외부 저장소가 반드시 필요한 고위험 서비스가 실제로 존재한다는 개별 query/update trace를 확보하고, 네 store 준비를 병렬화해 비용 gate를 다시 통과시키는 경우에만 수행한다. 동시에 GPU가 반환되면 사람이 검수한 자연 QA 30개 이상으로 locked 7B 평가를 완료한다. 이 세 조건 중 하나라도 실질적 근거를 만들지 못하면 EDBT급 주제가 아니라 재현 가능한 engineering/fault-study로 종료한다.

## 12. 관련 파일

- `freshevidencedb_p0/P0_FAILURE_REPRODUCTION_PREREGISTRATION.md`
- `freshevidencedb_p0/P0_FAILURE_REPRODUCTION_FINAL_REPORT_20260807.md`
- `freshevidencedb_p0/PRIOR_ART_BOUNDARY_20260807.md`
- `freshevidencedb_p0/run_failure_reproduction.py`
- `freshevidencedb_p0/results_run3/aggregate.json`
- `freshevidencedb_p0/results_run3/query_events.csv`
- `freshevidencedb_p0/results_run3/RESULT_MANIFEST.sha256`
- `freshevidencedb_p1/P1A_REAL_REVISION_CROSS_ENGINE_PREREGISTRATION.md`
- `freshevidencedb_p1/P1A_FINAL_REPORT_20260807.md`
- `freshevidencedb_p1/P1B_ANSWER_FAILURE_PREREGISTRATION.md`
- `freshevidencedb_p1/P1B_V1_1_DATA_AMENDMENT.md`
- `freshevidencedb_p1/P1B_FINAL_REPORT_20260807.md`
- `freshevidencedb_p1/results_run1/RESULT_MANIFEST.sha256`
- `freshevidencedb_p1/results_p1b_run1/RESULT_MANIFEST.sha256`
- `freshevidencedb_p2/P2_PRIOR_ART_AUDIT_20260807.md`
- `freshevidencedb_p2/P2_PREREGISTRATION_20260807.md`
- `freshevidencedb_p2/P2_IMPLEMENTATION_AMENDMENT_20260807.md`
- `freshevidencedb_p2/P2_FINAL_REPORT_20260807.md`
- `freshevidencedb_p2/PREREGISTRATION_LOCK.sha256`
- `freshevidencedb_p2/IMPLEMENTATION_LOCK.sha256`
- `freshevidencedb_p2/RESULT_MANIFEST.sha256`
- `freshevidencedb_p3/P3_PRIOR_ART_AND_ASSET_AUDIT_20260807.md`
- `freshevidencedb_p3/P3_PREREGISTRATION_20260807.md`
- `freshevidencedb_p3/P3_FINAL_REPORT_20260807.md`
- `freshevidencedb_p3/PREREGISTRATION_LOCK.sha256`
- `freshevidencedb_p3/IMPLEMENTATION_LOCK.sha256`
- `freshevidencedb_p3/IMPLEMENTATION_LOCK_V1_1.sha256`
- `freshevidencedb_p3/IMPLEMENTATION_LOCK_V1_2.sha256`
- `freshevidencedb_p3/RESULT_MANIFEST.sha256`
