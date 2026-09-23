# FreshEvidenceDB 선행연구 경계

- 확인일: 2026-08-07
- 상태: P0 전 위험 감사

## 결론

`FreshEvidenceDB`라는 넓은 주제는 점유됐다. 연구 후보로 남길 수 있는 것은 아래의 좁은 시스템 문제다.

> 서로 다른 트랜잭션 경계를 가진 catalog, dense, sparse, graph, cache가 비동기로 갱신될 때 한 RAG 질의가 동일 source epoch의 증거만 읽도록 보장하는 cross-store publish/snapshot protocol과 answer-level 오류 측정

## 주요 충돌

| 연구 | 발표 상태 | 점유 범위 | 남는 경계 |
|---|---|---|---|
| [VersionRAG](https://arxiv.org/abs/2510.08109) | 2025 arXiv preprint | 버전 관계 그래프, 변경 추적, version-sensitive QA와 VersionQA | 동시 query/update, cross-store atomic publish, snapshot isolation이 주 평가가 아님 |
| [SingleStore-V](https://vldb.org/pvldb/vol17/p3772-chen.pdf) | PVLDB 2024 | vector update/delete, ACID, MVCC consistent read | 하나의 통합 DB 내부 보장. 외부 parser/embedding/복수 색인/cache 파이프라인은 범위 밖 |
| [Fast Vector Search in PostgreSQL: A Decoupled Approach](https://www.cidrdb.org/cidr2026/papers/p2-liu.pdf) | CIDR 2026 | host DB metadata와 분리 vector index의 consistency mechanism | dense 중심이며 answer-level 다중 증거 계층 혼합 오류 평가는 아님 |
| [MCHRAG](https://dblp.org/rec/conf/mir/RenLZPL26.html) | ICMR 2026 | streaming corpus의 효율적 증분 RAG indexing | 문서 파생물 전체의 snapshot publish가 아님 |

## 연구 가치가 생기는 조건

1. catalog와 각 색인은 개별적으로 정상인데도 한 질의가 cross-store mixed snapshot을 실제 관측한다.
2. 단순 version filter는 stale을 missing으로 바꿔 SLA/정답 오류를 남긴다.
3. full blue/green은 해결하지만 write amplification이 지나치게 크다.
4. staged publish가 두 문제를 함께 줄이고 두 번째 엔진에서도 재현된다.

하나라도 성립하지 않으면 학술 주제로 확대하지 않는다.

