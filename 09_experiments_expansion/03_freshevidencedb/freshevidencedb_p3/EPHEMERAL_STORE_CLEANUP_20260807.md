# P3 전용 임시 저장소 정리 기록

- 정리일: 2026-08-07
- 범위: P3가 직접 생성한 전용 live store만 해당

## 제거한 대상

| 대상 | 용도 | 처리 |
|---|---|---|
| `fresh-p3-postgres` | sparse/catalog 및 통합 transaction baseline | container와 전용 anonymous volume 제거 |
| `fresh-p3-qdrant` | dense artifact | container 제거 |
| `fresh-p3-elasticsearch` | graph artifact | container 제거 |
| `results_p3b/sqlite_live/` | 4-artifact 실험의 retrieval cache live DB | 제거 |
| `results_p3c/sqlite_live/` | fault 실험의 retrieval cache live DB | 제거 |
| `smoke_sqlite/`, `smoke_fault_sqlite/` | 구현 정찰용 live DB | 제거 |
| `__pycache__/` | Python bytecode cache | 제거 |

P3 전용 PostgreSQL anonymous volume과 SQLite live DB는 삭제되어 그 상태 자체는 복구할 수 없다. 대신 모든 판정에 사용한 입력, checkpoint 단위 CSV, fault audit CSV, 집계 JSON, API 원문 JSON, 실행 코드와 해시는 보존했다. 동일 이미지와 코드로 실험을 재실행할 수 있다.

## 보존·비접촉 확인

기존 공유 서비스 `qdrant`, `weaviate-1.35.3`, `milvus-*`, `kiise-vlmdb-pgvector`, `es01`과 GPU를 사용 중인 다른 실험은 중단·변경·삭제하지 않았다. 정리 직후 공유 container가 계속 실행 중임을 확인했다.
