# 2026 KIISE 데이터베이스연구회 연구 프로젝트 (2026_KIISE)

본 저장소는 멀티모달 비디오 RAG 및 벡터 데이터베이스 계층의 편향·순환성 검증과 최적화를 다룬 연구의 논문 원고, 문서화 정본, 실험 스크립트 및 발표 자료를 통합 관리하는 리포지토리입니다.

모든 디렉터리는 **실험 재현(Reproducibility) 시 확인하고 실행해야 하는 우선순위 순서(`00_` ~ `09_`)**로 구조화되어 있습니다.

---

## 📂 우선순위별 디렉토리 구조 및 문서 인덱스

| 순서 | 디렉터리 | 역할 및 재현 워크플로우 단계 |
|:---:|---|---|
| **00** | [**`00_env/`**](00_env/) | **가상 환경 구축 (1단계)**: Python 3.10 가상환경 및 필수 라이브러리 설치 |
| **01** | [**`01_infra/`**](01_infra/) | **인프라 기동 (2단계)**: PostgreSQL 16 + pgvector 데이터베이스 컨테이너 구동 |
| **02** | [**`02_project_md/`**](02_project_md/) | **연구 설계/데이터셋 명세 (3단계)**: 연구 질문(RQ), 불변 규칙, 데이터셋 계보 및 사전등록 규칙 |
| **03** | [**`03_src/`**](03_src/) | **코어 엔진 소스코드 (4단계)**: `vlmdb_workload` 패키지 (어댑터, 임베딩, 검색, 평가 지표) |
| **04** | [**`04_scripts/`**](04_scripts/) | **실험 실행 스크립트 (5단계)**: 벤치마크 수행, 데이터 전처리, 색인 구축 및 결과 생성 |
| **05** | [**`05_manuscript/`**](05_manuscript/) | **논문 원고 및 최종 결과 (6단계)**: 최종 원고(`0_main_paper.md`), 심사의견 대응서, 검증 기준치 |
| **06** | [**`06_paper_assets/`**](06_paper_assets/) | **논문 에셋 및 시각화 (7단계)**: 본문 수록 도표, 생성 그래프, 파이프라인 감사 산출물 |
| **07** | [**`07_survey/`**](07_survey/) | **선행 문헌 조사 (8단계)**: 최종 논문 인용 선행 연구 45건 원본 PDF 및 마스터 카탈로그 |
| **09** | [**`09_experiments_expansion/`**](09_experiments_expansion/) | **확장 연구 및 차기 과제 (9단계)**: 본 논문 보강 실험(표 11), FreshEvidenceDB, 차기 제안서 |

---

## 📑 주요 문서 상세 가이드

### 1. 연구 기록 및 종합 마스터 정본 (`02_project_md/`)
- 🌟 [**`00_KIISE_DBR_FINAL_MASTER_SPECIFICATION.md`**](02_project_md/00_KIISE_DBR_FINAL_MASTER_SPECIFICATION.md): **최종 논문 완성 및 재현을 위한 단일 종합 마스터 정본 (Single Source of Truth)**
  - 논문 개요 & 3대 공헌 / 8종 실사용 데이터셋 계보 / 벡터 DB 5대 설계 축(112개 구성) / RQ1~RQ6 실험 정본(표 1~11 수치) / 심사위원(R1, R2) 피드백 대응 및 보강 실험 분석 / 실행 스크립트 매핑
- [**`reviews_and_audits/`**](02_project_md/reviews_and_audits/): 2026-08 학술대회 심사 대응 및 최종 감사 문서군 (`60_REVIEW` ~ `71_`)
- [**`canonical/`**](02_project_md/canonical/): RQ1~RQ6별 사전등록 실험 정본 명세 (EXP01 ~ EXP06)
- [**`legacy_thematic_202607/`**](02_project_md/legacy_thematic_202607/): 2026-07 주제별 정리본 (00_MASTER, 10_INTRO, 20_RELATED, 30_METHOD, 40_DATASETS)
- [**`external_and_notes/`**](02_project_md/external_and_notes/): 타 논문(ECIR 2027), 세미나 노트 및 부속 자료
- 상세 안내: [02_project_md README](02_project_md/README.md)

### 2. 논문 및 심사 대응 (`05_manuscript/`)
- [**`0_main_paper.md`**](05_manuscript/0_main_paper.md): 최종 논문 원고 전문 (Markdown 정본)
- [**`paper_최종.pdf`**](05_manuscript/paper_최종.pdf): 최종 제출 논문 PDF
- [**`심사의견대응서.pdf`**](05_manuscript/심사의견대응서.pdf): 심사 의견별 반영 및 대응 보고서
- [**`ASSETS_INDEX.md`**](05_manuscript/ASSETS_INDEX.md): 논문에 포함된 그림(Figure 1~3) 및 표(Table 1~11) 에셋 매핑 인덱스

### 3. 선행 연구 문헌 아카이브 (`07_survey/`)
- [**`07_survey/README.md`**](07_survey/README.md): 최종 논문 인용번호 `[1]` ~ `[45]`와 1:1 매칭된 45건의 원본 논문 PDF 및 기술 명세서 전수 카탈로그
- [**`00_early_research_reports/`**](07_survey/00_early_research_reports/): 연구 초기 심층 리서치 보고서(`deep-research-report_1.md` ~ `4.md`)

### 4. 확장 연구 과제 및 차기 연구 포트폴리오 (`09_experiments_expansion/`)
- [**`09_experiments_expansion/README.md`**](09_experiments_expansion/README.md): 5대 연구 테마 마스터 인덱스
- [**`01_kiise_supplementary_experiments/`**](09_experiments_expansion/01_kiise_supplementary_experiments/): LLM 답변 계층 VQA 실험(표 11 정본), 신경망 Reranker 심화, 부트스트랩 95% CI 검정
- [**`02_followup_topic_proposals/`**](09_experiments_expansion/02_followup_topic_proposals/): 차기 학술대회 제안서, 대안 연구 주제 포트폴리오 및 선행 기술 분석
- [**`03_freshevidencedb/`**](09_experiments_expansion/03_freshevidencedb/): 실시간 문서 개정 신선도, 일관성 및 장애 복원력 벡터 DB 연구
- [**`04_multimodal_intent_and_graphrag/`**](09_experiments_expansion/04_multimodal_intent_and_graphrag/): EvidenceViewDB, IntentStore, Provenance GraphRAG
- [**`05_workload_validity_audit/`**](09_experiments_expansion/05_workload_validity_audit/): 워크로드 유효성 감사 및 난이도 편향 통제 파이프라인

---

## 🛠️ 실험 재현 퀵스타트 (순서대로 실행)

### [00단계] 가상환경 구축
```bash
# Conda 환경 생성 (권장)
conda env create -f 00_env/experiment_environment.yml
conda activate kiise-vlmdb

# 또는 pip 직접 설치
pip install -r 00_env/experiment_requirements.txt
```

### [01단계] 인프라 컨테이너 기동
```bash
# pgvector 백엔드 컨테이너 실행
docker compose -f 01_infra/docker-compose.pgvector.yml up -d
```

### [02~04단계] 데이터셋 확인 및 스크립트 실행
- [데이터셋 명세](02_project_md/00_KIISE_DBR_FINAL_MASTER_SPECIFICATION.md#2-비순환-데이터셋-구축-계보-datasets--provenance)를 확인한 후, [`04_scripts/`](04_scripts/) 디렉터리의 벤치마크 및 평가 스크립트를 순차적으로 실행합니다.

---

## 🔒 데이터 및 대용량 파일 관리 정책
- GitHub 100MB 파일 크기 제한 및 저장소 경량화를 위해 대용량 벡터 파일(`*.fvecs`, `*.bin`, `*.npy`) 및 원시 데이터 캐시는 `.gitignore`를 통해 관리됩니다.
- 실험 재현에 필요한 데이터셋은 [`02_project_md/00_KIISE_DBR_FINAL_MASTER_SPECIFICATION.md`](02_project_md/00_KIISE_DBR_FINAL_MASTER_SPECIFICATION.md#2-비순환-데이터셋-구축-계보-datasets--provenance)의 계보 및 가이드를 참조하십시오.
