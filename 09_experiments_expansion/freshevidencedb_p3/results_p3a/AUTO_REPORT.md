# P3-A Wikimedia 실측 trace 자동 보고

- T1: **TRACE_APPLICABILITY_PASS**
- page/day: 11 / 4,306
- 실제 user views: 41,007,031
- 실제 revisions: 1,740
- 예상 unsafe observations/year: 62.3135

| page | views | revisions | expected/year |
|---|---:|---:|---:|
| ChatGPT | 37,586,447 | 821 | 60.7918 |
| Large_language_model | 1,226,073 | 525 | 1.2971 |
| Retrieval-augmented_generation | 502,015 | 82 | 0.0876 |
| PostgreSQL | 323,996 | 52 | 0.0367 |
| Kubernetes | 330,423 | 49 | 0.0327 |
| Docker_(software) | 344,899 | 39 | 0.0274 |
| Vector_database | 107,511 | 54 | 0.0112 |
| Elasticsearch | 298,190 | 17 | 0.0105 |
| Neo4j | 65,912 | 66 | 0.0099 |
| Redis | 156,893 | 25 | 0.0071 |
| Flask_(web_framework) | 64,214 | 10 | 0.0015 |
| Qdrant | 458 | 0 | 0.0000 |

실제 개별 query timestamp가 아니라 일별 집계에 일중 uniform arrival을 적용한 기대값이다.
