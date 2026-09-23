# FreshEvidenceDB P2 최신 선행연구 경계 감사

- 감사일: 2026-08-07
- 목적: P2 실행 전에 “답변 freshness”와 “dependency consistency”를 신규성으로 과장하지 않도록 위험 경쟁 연구를 다시 확인한다.

## 결론

2026년 6–7월 공개된 StaleBench와 FinCacheServe 때문에 FreshEvidenceDB의 넓은 freshness 주장은 더 이상 성립하지 않는다. 남는 후보 기여는 **이질적인 검색 저장소의 파생 artifact를 동일 source epoch으로 공개하고 storage/client failure에서 복구하는 시스템 계층**이다.

## 직접 경쟁·경계 연구

| 연구 | 점유 범위 | FreshEvidenceDB에 남는 범위 |
|---|---|---|
| [StaleBench](https://zenodo.org/records/20710012) | 문서 변경 이후 answer freshness, refresh policy, catch-up latency, exact-match 평가, 10개 open model의 context position bias | catalog·dense·sparse·graph/cache의 cross-store atomic publication과 server fault recovery는 주 기여가 아님 |
| [FinCacheServe](https://arxiv.org/abs/2607.26076) | 문서 version, evidence/tool fingerprint, model/config dependency로 answer cache 재사용을 보호; SEC trace와 Qwen2.5 평가 | answer cache dependency는 점유됨. 여러 retrieval index의 readiness·manifest snapshot·partial-write recovery가 남을 수 있음 |
| [VersionRAG](https://arxiv.org/abs/2510.08109) | 문서 version 관계와 version-sensitive QA | concurrent update/query의 cross-store publication이 아님 |
| [SingleStore-V](https://vldb.org/pvldb/vol17/p3772-chen.pdf) | 통합 DB 내부 vector update/delete, MVCC consistent read | 한 DB 밖의 parser/embedding/복수 index/cache는 범위 밖 |
| [PostgreSQL-V](https://www.cidrdb.org/cidr2026/papers/p2-liu.pdf) | PostgreSQL host metadata와 분리 vector index의 transactional consistency | answer-visible dense+sparse+graph+cache 묶음과 source lineage의 복구가 남는 경계 |
| [FreshCache](https://arxiv.org/abs/2607.04281) | open-web semantic cache의 freshness risk와 stale reuse | cache freshness 정책은 점유됨. retrieval artifact publication은 별개 |

## 금지 주장

- 최초의 RAG freshness benchmark
- 최초의 stale answer 측정
- 최초의 version/dependency-aware answer cache
- 최초의 transactional vector update
- 최초의 version-aware RAG
- staging 또는 two-phase publication의 발명

## P2가 입증해야 하는 것

1. Qdrant만이 아니라 Weaviate 기반 cross-store 배치에서도 문제가 재현된다.
2. 실제 process kill·일시적 network unavailability 뒤 active snapshot이 부분 artifact를 참조하지 않는다.
3. 실제 update timestamp와 측정된 update duration을 결합했을 때 적용 가치가 있는 workload 구간이 존재한다.
4. model이 충분히 유능할 때 complete current context가 missing/mixed context보다 최신 답변에 유리하다.
5. 통합 PostgreSQL transaction이 가능한 경우에는 FreshEvidenceDB가 필요 없음을 계속 명시한다.

이 다섯 조건 중 1–2가 실패하면 시스템 핵심을 중단한다. 3–4가 미확정이면 niche/conditional 주제로만 유지한다.
