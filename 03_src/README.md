# [03] 코어 소스코드 라이브러리 (`03_src/`)

본 디렉터리는 2026 KIISE 연구 논문의 실험 구동을 위한 핵심 Python 라이브러리 패키지를 관리합니다. **실험 재현 시 가상환경 구축(00_env), 인프라 기동(01_infra), 연구 설계 확인(02_project_md) 후 코드 레벨에서 확인해야 하는 03순위 단계**입니다.

---

## 📁 패키지 안내

- [**`vlmdb_workload/`**](vlmdb_workload/): **VLM-DB 워크로드 및 실험 엔진 코어 패키지**
  - **I/O 및 데이터 파싱**: 5대 표준 Canonical 아티팩트(`clips`, `documents`, `metadata`, `queries`, `qrels`) 로더
  - **임베딩 파이프라인**: SentenceTransformers 기반 텍스트 임베딩 생성기
  - **검색 베이스라인**: B0(메타 단독)부터 B5(하이브리드 RRF)까지 6대 검색 전략 구현체
  - **평가 지표 엔진**: Recall@k, Hit@k, MRR, nDCG@k 정밀 산출
  - **데이터셋 어댑터**: VRU, AI Hub 지능형 관제, 다각도 CCTV 생활안전 원천 데이터 정규화 모듈

자세한 패키지 구조 및 모듈별 API 명세는 [**`vlmdb_workload/README.md`**](vlmdb_workload/README.md)를 참조하십시오.
