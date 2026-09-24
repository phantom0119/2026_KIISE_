# [01] 인프라 환경 구축 가이드 (`01_infra/`)

본 디렉터리는 2026 KIISE 논문의 벡터 데이터베이스(Vector DB) 계층 실험을 위한 데이터베이스 인프라 구동 설정을 관리합니다. **가상 환경 구축(00_env) 완료 후 데이터베이스 기반 실험을 위해 확인해야 하는 01순위 단계**입니다.

---

## 📁 구성 파일 안내

| 파일명 | 형식 | 설명 및 용도 |
|---|---|---|
| [`docker-compose.pgvector.yml`](docker-compose.pgvector.yml) | Docker Compose | PostgreSQL 16 기반의 pgvector 공식 컨테이너를 구동하기 위한 명세 파일 |

---

## ⚙️ 컨테이너 및 접속 설정

- **이미지**: `pgvector/pgvector:pg16`
- **컨테이너명**: `kiise-vlmdb-pgvector`
- **호스트 포트 매핑**: `5433:5432` (기본 PostgreSQL 포트인 5432와의 충돌 방지)
- **접속 파라미터 (DSN)**:
  - Host: `127.0.0.1` (또는 `localhost`)
  - Port: `5433`
  - Database: `vlmdb`
  - User: `vlmdb`
  - Password: `vlmdb`
  - DSN 문자열: `host=127.0.0.1 port=5433 dbname=vlmdb user=vlmdb password=vlmdb`

---

## 🚀 인프라 실행 방법

저장소 최상위 루트(`2026_KIISE/`)에서 아래 명령어로 데이터베이스 컨테이너를 기동합니다.

```bash
# 백그라운드에서 pgvector 컨테이너 실행
docker compose -f 01_infra/docker-compose.pgvector.yml up -d

# 컨테이너 실행 상태 확인
docker ps --filter "name=kiise-vlmdb-pgvector"

# 컨테이너 중지
docker compose -f 01_infra/docker-compose.pgvector.yml down
```

---

## 🔗 연계 실험 스크립트 및 논문 결과

본 pgvector 인프라는 논문의 다음 실험 및 테이블 결과 도출에 직접 사용됩니다:

1. **논문 Table 1, Table 2, Table 8**:
   - [`build_miris_pgvector.py`](../04_scripts/01_canonical_and_preprocessing/build_miris_pgvector.py) / [`build_miris_pgvector_rich.py`](../04_scripts/01_canonical_and_preprocessing/build_miris_pgvector_rich.py): 비디오 키프레임 벡터 적재
   - [`run_pgvector_partial_index.py`](../04_scripts/05_rq5_filtered_ann_index/run_pgvector_partial_index.py): Predicate별 부분 HNSW 인덱스 성능 측정
   - [`run_pgvector_ann_benchmark.py`](../04_scripts/05_rq5_filtered_ann_index/run_pgvector_ann_benchmark.py): 인덱스 파라미터(lists, probes, m, ef_search)별 재현율/지연시간 벤치마크
   - [`run_pgvector_retrieval.py`](../04_scripts/05_rq5_filtered_ann_index/run_pgvector_retrieval.py): 벡터 검색 질의 실행
2. **확장 실험 (FreshEvidenceDB)**:
   - [`run_p1a_real_revision.py`](../09_experiments_expansion/03_freshevidencedb/freshevidencedb_p1/run_p1a_real_revision.py): 동적 갱신 환경 벡터 검색 평가

---

## ⚠️ 데이터 볼륨 마운트 참고사항
- 기본 설정에는 연구실 스토리지 경로(`/hdd2/KIISE_datasociety/Datasets/services/postgres_pgvector`)가 바인드 마운트되어 있습니다.
- 독립된 타 머신에서 실행할 경우, `docker-compose.pgvector.yml`의 volumes 항목을 Docker Named Volume(예: `pgdata:/var/lib/postgresql/data`) 또는 로컬 디렉터리로 수정하여 사용할 수 있습니다.
