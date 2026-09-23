# FreshEvidenceDB P1-A 실제 개정·교차 엔진 최종 보고서

- 수행일: 2026-08-07
- 판정: **`GO_P1B_ANSWER_AND_FAILURE_INJECTION`**
- 모든 사전 게이트: 통과
- 인공 phase 지연: 0ms
- 실행 환경: Qdrant 1.15.5, PostgreSQL 16.14, pgvector 0.8.4, CPU HashingVectorizer 384차원

## 1. 결론

P0의 오류는 합성 문서나 강제 sleep에만 존재한 현상이 아니었다. 공식 Flask 문서 100개와 Kubernetes 영문 문서 100개의 실제 수정 전·후 쌍을 사용하고, 저장 연산 사이의 인공 지연을 제거해도 Qdrant dense와 PostgreSQL sparse/catalog의 순차 갱신에서 오류가 반복됐다.

단순 exact-version filter는 stale와 mixed evidence를 없앴지만 새 버전 파생물이 모두 준비되기 전에 manifest가 바뀌면서 Flask 70.68%, Kubernetes 70.71%의 필수 evidence missing을 남겼다. staged publication은 두 도메인 합계 update-window 질의 14,040건에서 오류 0건이었다. 전체 blue/green도 오류 0건이었으나 staged보다 쓰기량이 약 9.90–9.97배 많았다.

PostgreSQL 한 트랜잭션에 catalog·vector·sparse evidence를 넣은 `pg_atomic`도 12,738건에서 오류 0건이었고 p95 query latency가 가장 낮았다. 따라서 FreshEvidenceDB는 통합 DB를 대체하는 범용 시스템이 아니라, 외부 vector DB와 별도 sparse/graph/cache를 함께 유지해야 하는 이질적 RAG 배치만 대상으로 해야 한다.

## 2. 실제 revision 데이터

| 도메인 | revision pair | 서로 다른 commit | 서로 다른 path | 평균 새 청크 | 평균 새 문서 길이 |
|---|---:|---:|---:|---:|---:|
| Flask | 100 | 100 | 39 | 43.52 | 7,599자 |
| Kubernetes | 100 | 100 | 72 | 47.20 | 11,657자 |

- Flask HEAD: `6a2f545bfd8ed31e19066a299296917e034aca58`
- Kubernetes website HEAD: `7ddeae4e0e52ce7dcb0e868106a9c15d8e3b8b02`
- 각 pair는 실제 parent/commit의 modified document다.
- 각 pair를 독립 logical document로 구성했으므로 repository의 시간별 update prevalence를 재현한 것은 아니다.

## 3. 결과

아래 오류율은 변경 중인 문서에 query를 80% 집중한 stress workload의 조건부 비율이다.

| 도메인 | 프로토콜 | update 질의 | 오류 | stale | mixed | missing | p95 | 쓰기 증폭 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| Flask | cross naive | 6,256 | 76.34% | 76.34% | 68.33% | 76.04% | 53.28ms | 1.00× |
| Flask | read filter | 6,263 | 70.68% | 0% | 0% | 70.68% | 55.72ms | 1.00× |
| Flask | staged | 6,749 | 0% | 0% | 0% | 0% | 49.86ms | 1.00× |
| Flask | blue/green | 50,739 | 0% | 0% | 0% | 0% | 66.04ms | 9.97× |
| Flask | pg atomic | 5,974 | 0% | 0% | 0% | 0% | 20.52ms | 1.00× |
| Kubernetes | cross naive | 7,374 | 73.73% | 73.64% | 65.64% | 73.23% | 55.80ms | 1.00× |
| Kubernetes | read filter | 7,603 | 70.71% | 0% | 0% | 70.71% | 55.93ms | 1.00× |
| Kubernetes | staged | 7,291 | 0% | 0% | 0% | 0% | 53.45ms | 1.00× |
| Kubernetes | blue/green | 52,279 | 0% | 0% | 0% | 0% | 70.43ms | 9.90× |
| Kubernetes | pg atomic | 6,764 | 0% | 0% | 0% | 0% | 22.05ms | 1.00× |

staged 0건의 도메인별 Wilson 95% 상한은 Flask 0.0569%, Kubernetes 0.0527%다. pg atomic의 상한은 각각 0.0643%, 0.0568%다.

## 4. 게이트

| 게이트 | 결과 | 근거 |
|---|---|---|
| G0 데이터·하니스 | 통과 | 도메인별 100 pair, steady 오류 0, 30/30 wave, worker 오류 0 |
| G1 실제 revision 오류 | 통과 | 두 도메인·모든 반복에서 naive 오류 1% 이상 |
| G2 단순 필터 충분성 | 실패 | missing 약 70.7% |
| G3 staged 유효성 | 통과 | 오류 0, latency 기준과 missing 감소 기준 통과 |
| G4 blue/green 대비 비용 | 통과 | staged의 쓰기량 약 9.9배 절감 |
| G5 통합 MVCC | 통과 | pg atomic 오류 0 |

## 5. 올바른 해석

### 확인된 것

- 자연 문서의 길이와 재청킹에서도 cross-store visibility window가 실제 저장 연산만으로 생긴다.
- read-time version equality는 availability 문제를 해결하지 못한다.
- prepare-before-publish가 full snapshot 복제보다 적은 쓰기로 일관성을 제공할 수 있다.
- 모든 파생물을 하나의 PostgreSQL transaction에 넣을 수 있다면 native MVCC가 더 단순하고 빠르다.

### 확인되지 않은 것

- 운영 query/update arrival에서의 실제 발생률
- 일반 생성형 QA의 정확도 영향
- cache·graph·ACL·embedding migration
- storage server crash, network partition, coordinator failure
- Qdrant 이외 vector DB에서의 일반성

## 6. 다음 판정

사전등록 규칙에 따라 answer checkpoint와 client crash/retry를 다루는 P1-B만 승인한다. 이 결과만으로 논문 시스템 전체를 확정하지 않는다.

## 7. 재현 자료

- `P1A_REAL_REVISION_CROSS_ENGINE_PREREGISTRATION.md`
- `DATASET_LOCK.txt`
- `revision_manifest.json`
- `build_revision_pairs.py`
- `run_p1a_real_revision.py`
- `results_run1/query_events.csv`
- `results_run1/repeat_summary.csv`
- `results_run1/aggregate.json`
- `results_run1/RESULT_MANIFEST.sha256`
