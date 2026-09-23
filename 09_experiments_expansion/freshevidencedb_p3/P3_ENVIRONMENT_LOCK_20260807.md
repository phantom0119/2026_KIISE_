# P3 실행 환경 고정

- PostgreSQL/pgvector image: `pgvector/pgvector:pg16`, `sha256:b295c2aa92725ecaaa58ffb6664035b45076318d8ca93ae4a9b0994481862f7d`
- Qdrant image: `qdrant/qdrant:v1.15.5`, `sha256:0ad2e23181e5646b286253c04cea23f07040ca313cc377d9fa7b21db184b6406`
- Elasticsearch image: `docker.elastic.co/elasticsearch/elasticsearch:9.2.3`, `sha256:47addb8c32ef58ebafc37a2b583e29aa0fdbb264ce41a0807dfff210b252aca0`
- 전용 container/port: `fresh-p3-postgres:15435`, `fresh-p3-qdrant:17333/17334`, `fresh-p3-elasticsearch:19201/19301`
- Python: torch `2.9.0+cu128`, transformers `4.57.6`, psycopg `3.3.2`, Elasticsearch client `9.3.0`
- model: `Qwen/Qwen2.5-7B-Instruct`, snapshot `a09a35458c702b33eeacc393d103063234e8bc28`
- Wikimedia trace period: 2025-08-01–2026-07-31 UTC

공유 Qdrant·Weaviate·Elasticsearch·PostgreSQL과 타 GPU 작업은 P3 실행 대상이 아니다.
