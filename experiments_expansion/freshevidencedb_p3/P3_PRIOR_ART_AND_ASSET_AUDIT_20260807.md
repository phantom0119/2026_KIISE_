# FreshEvidenceDB P3 선행연구·자산 감사

- 감사일: 2026-08-07
- 상태: P3 결과 실행 전

## 1. 최신 연구 경계

| 자료 | 이미 점유한 범위 | P3에 남는 범위 |
|---|---|---|
| [StaleBench](https://zenodo.org/records/20710012) | 문서 변경 이후 answer freshness, refresh/catch-up, 문맥 위치 편향 | 여러 검색 artifact의 cross-store publication과 crash recovery는 중심 기여가 아님 |
| [FinCacheServe](https://arxiv.org/abs/2607.26076) | 문서·evidence·tool·model dependency를 추적하는 answer-cache consistency | cache 단독 주장은 불가; dense+sparse+graph+cache의 answer-visible snapshot 결합만 후보 |
| [FreshCache](https://arxiv.org/abs/2607.04281) | 실제 web snapshot 기반 semantic-cache freshness risk | cache freshness와 갱신 정책은 점유됨 |
| [VersionRAG](https://arxiv.org/abs/2510.08109) | version-sensitive QA와 문서 변경 관계 | 동시 query/update의 이질 저장소 공개 계약은 별도 경계 |
| [SingleStore-V](https://vldb.org/pvldb/vol17/p3772-chen.pdf) | 통합 DB 안의 MVCC vector update/delete | 통합 DB로 해결되는 workload는 FreshEvidenceDB 대상에서 제외 |
| [PostgreSQL-V](https://www.cidrdb.org/cidr2026/papers/p2-liu.pdf) | host DB와 분리 vector index consistency | 4종 artifact readiness·lineage·cache/graph·복구까지 확장해야 차별화 가능 |

P3에서 허용되는 후보 주장은 다음뿐이다.

> 여러 트랜잭션 경계에 놓인 dense·sparse·graph·cache 파생 artifact를 동일 source epoch으로 공개하는 coordinator의 safety, recovery와 비용 정책

“최초의 RAG freshness”, “최초의 version-aware RAG”, “최초의 cache freshness”, “two-phase publish 발명”은 금지한다.

## 2. 실측 trace 후보

로컬에는 실제 운영 RAG query trace가 없다. 공개 대체 자료로 Wikimedia의 다음 두 공식 인터페이스를 사용한다.

- [Wikimedia Analytics Pageviews API](https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html): 실제 user pageview의 일별 집계
- [MediaWiki Revisions API](https://www.mediawiki.org/wiki/API:Revisions): page revision의 실제 timestamp

이는 실제 조회량과 수정 시각을 결합하지만 개별 query timestamp가 아니라 일별 집계다. 따라서 일중 uniform arrival 가정으로 계산한 **예상 노출량**이며 실제 stale-answer 사건 관측이 아니다.

## 3. 시스템 자산

- GPU: RTX 3090 2장 모두 타 장기 실험이 약 23.3GB씩 점유. 중단하지 않는다.
- 로컬 7–14B 모델: Qwen2.5-7B-Instruct, Llama-3 계열 8B, Qwen2.5-14B-Instruct 4-bit 등 존재.
- 공유 저장소: Qdrant 1.15.5, Weaviate 1.35.3, Elasticsearch 9.2.3, PostgreSQL/pgvector, Milvus 2.6.0. 공유 process는 중단하지 않는다.
- P3 fault 실험은 별도 container와 별도 port만 사용한다.
- 사람이 검수한 changed-fact 자연 QA는 존재하지 않는다. agent가 만든 질문은 human-reviewed로 표시하지 않는다.

## 4. P3가 해결해야 할 미확정 항목

1. 공개 실측 조회·수정 trace에서 문제가 무시할 수 없는가
2. graph와 cache를 추가해도 staged snapshot이 안전한가
3. 실제 coordinator crash, message reorder, store pause/kill에서 recovery 가능한가
4. 통합 PostgreSQL 대비 cross-store 비용이 허용 가능한가
5. finite-state exploration에서 safety invariant가 유지되는가
6. 7–14B model과 사람이 검수한 자연 QA에서 답변 효과가 확인되는가

6번은 GPU 자원과 실제 사람 검수가 모두 필요하다. 어느 하나가 없으면 해당 게이트는 통과로 기록하지 않는다.
