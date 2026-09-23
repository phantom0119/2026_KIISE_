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
| **07** | [**`07_survey/`**](07_survey/) | **선행 문헌 조사 (8단계)**: 멀티모달 비디오 RAG 및 벡터 DB 관련 심층 리서치 보고서 |
| **08** | [**`08_presentations/`**](08_presentations/) | **학술 발표 자료 (9단계)**: 학술대회/워크숍 발표 슬라이드(`pptx`, `pdf`) 및 슬라이드 스펙 |
| **09** | [**`09_experiments_expansion/`**](09_experiments_expansion/) | **확장 연구 과제 (10단계)**: FreshEvidenceDB, GraphRAG, 유효성 감사 등 파생 실험 |

---

## 📑 주요 문서 상세 가이드

### 1. 연구 기록 및 정본 체계 (`02_project_md/`)
주제별 통합 정본 및 단계별 리뷰 대응 문서가 체계적으로 번호화되어 관리됩니다. (상세 안내: [02_project_md README](02_project_md/README.md))

| 구분 | 문서 파일 | 주요 내용 |
|---|---|---|
| **연구 총괄** | [00_MASTER_status_and_decisions.md](02_project_md/00_MASTER_status_and_decisions.md) | 연구 현황, 불변 규칙 28선, 용어 사전, 의사결정 로그 |
| **서론/연구질문** | [10_INTRODUCTION_motivation_and_RQ.md](02_project_md/10_INTRODUCTION_motivation_and_RQ.md) | 문제 제기, Research Gap, 확정 RQ 구조 (검증→설계→전파) |
| **관련 연구** | [20_RELATED_WORK.md](02_project_md/20_RELATED_WORK.md) | UCA/VALU 등 선행 연구 비교 매트릭스 및 차별성 |
| **방법론/검증** | [30_METHODOLOGY_and_verification.md](02_project_md/30_METHODOLOGY_and_verification.md) | 문제 정의, 사전등록 규칙, 검증 체계 및 실험 구조 감사 |
| **데이터셋 계보** | [40_DATASETS_and_provenance.md](02_project_md/40_DATASETS_and_provenance.md) | 실사용 8종 데이터셋, 비순환 구축 및 데이터 출처 계보 |
| **심사 의견 대응** | [60_REVIEW_response_and_supplements.md](02_project_md/60_REVIEW_response_and_supplements.md) | 심사 피드백 대응 종합 및 보강 실험 결과 |
| **리비전 감사** | [61 ~ 71 시리즈](02_project_md/) | RQ6 재현성 보강, 최종 체크리스트, 예산/지면 감축 계획 |
| **실험 정본** | [canonical/](02_project_md/canonical/) | RQ1~RQ6별 실험 정본 (EXP01 ~ EXP06) |
| **아카이브** | [archive/](02_project_md/archive/) | 이전 47개 레거시 원본 무손실 보존 |

### 2. 논문 및 심사 대응 (`05_manuscript/`)
- [**`0_main_paper.md`**](05_manuscript/0_main_paper.md): 최종 논문 원고 전문 (Markdown 정본)
- [**`paper_최종.pdf`**](05_manuscript/paper_최종.pdf): 최종 제출 논문 PDF
- [**`심사의견대응서.pdf`**](05_manuscript/심사의견대응서.pdf): 심사 의견별 반영 및 대응 보고서
- [**`ASSETS_INDEX.md`**](05_manuscript/ASSETS_INDEX.md): 논문에 포함된 그림(Figure 1~3) 및 표(Table 1~11) 에셋 매핑 인덱스

### 3. 사전 문헌 조사 (`07_survey/`)
- [**`deep-research-report_1.md` ~ `4.md`**](07_survey/): 멀티모달 비디오 RAG, 벡터 검색 최적화, 지식 그래프 융합 등에 관한 심층 서베이 보고서

### 4. 발표 자료 (`08_presentations/`)
- [**`kiise_vlmdb_deck_20260714.pptx`**](08_presentations/kiise_vlmdb_deck_20260714.pptx) / [**`pdf`**](08_presentations/kiise_vlmdb_deck_20260714.pdf): 슬라이드 덱
- [**`SLIDE_SPEC_for_external_agent_20260714.md`**](08_presentations/SLIDE_SPEC_for_external_agent_20260714.md): 발표 슬라이드 레이아웃 및 구성 명세서

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
- [데이터셋 명세](02_project_md/40_DATASETS_and_provenance.md)를 확인한 후, [`04_scripts/`](04_scripts/) 디렉터리의 벤치마크 및 평가 스크립트를 순차적으로 실행합니다.

---

## 🔒 데이터 및 대용량 파일 관리 정책
- GitHub 100MB 파일 크기 제한 및 저장소 경량화를 위해 대용량 벡터 파일(`*.fvecs`, `*.bin`, `*.npy`) 및 원시 데이터 캐시는 `.gitignore`를 통해 관리됩니다.
- 실험 재현에 필요한 데이터셋은 [`02_project_md/40_DATASETS_and_provenance.md`](02_project_md/40_DATASETS_and_provenance.md)의 계보 및 가이드를 참조하십시오.
