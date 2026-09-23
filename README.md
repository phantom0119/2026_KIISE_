# 2026 KIISE 데이터베이스연구회 연구 프로젝트 (2026_KIISE)

본 저장소는 멀티모달 비디오 RAG 및 벡터 데이터베이스 계층의 편향·순환성 검증과 최적화를 다룬 연구의 논문 원고, 문서화 정본, 실험 스크립트 및 발표 자료를 통합 관리하는 리포지토리입니다.

---

## 📂 디렉토리 구조 및 문서 통합 인덱스

```
2026_KIISE/
├── manuscript/             # 논문 최종 원고, 심사 대응서 및 그림/표 에셋
├── project_md/             # 연구 설계, 방법론, RQ별 분석, 심사 대응 정본 문서
├── survey/                 # 사전 문헌 조사 및 심층 리서치 보고서
├── presentations/          # 학술 발표 슬라이드(PPTX, PDF) 및 작성 스펙
├── paper_assets/           # 논문 수록 시각화 자료, 통계 표, 검증 스위트
├── src/                    # VLM-DB 워크로드 및 엔진 코어 소스코드
├── scripts/                # 실험 자동화, 평가 및 데이터 감사 스크립트
├── experiments_expansion/  # 확장 실험 (FreshEvidenceDB, GraphRAG, 검증 감사 등)
├── env/                    # 실험 환경 명세 (conda yml, requirements.txt)
└── infra/                  # 데이터베이스 인프라 설정 (docker-compose)
```

---

## 📑 주요 문서 가이드

### 1. 논문 및 심사 대응 (`manuscript/`)
- [**`0_main_paper.md`**](manuscript/0_main_paper.md): 최종 논문 원고 전문 (Markdown 정본)
- [**`paper_최종.pdf`**](manuscript/paper_최종.pdf): 최종 제출 논문 PDF
- [**`심사의견대응서.pdf`**](manuscript/심사의견대응서.pdf): 심사 의견별 반영 및 대응 보고서
- [**`ASSETS_INDEX.md`**](manuscript/ASSETS_INDEX.md): 논문에 포함된 그림(Figure 1~3) 및 표(Table 1~11) 에셋 매핑 인덱스

### 2. 연구 기록 및 정본 체계 (`project_md/`)
주제별 통합 정본 및 단계별 리뷰 대응 문서가 체계적으로 번호화되어 관리됩니다. (상세 안내: [project_md README](project_md/README.md))

| 구분 | 문서 파일 | 주요 내용 |
|---|---|---|
| **연구 총괄** | [00_MASTER_status_and_decisions.md](project_md/00_MASTER_status_and_decisions.md) | 연구 현황, 불변 규칙 28선, 용어 사전, 의사결정 로그 |
| **서론/연구질문** | [10_INTRODUCTION_motivation_and_RQ.md](project_md/10_INTRODUCTION_motivation_and_RQ.md) | 문제 제기, Research Gap, 확정 RQ 구조 (검증→설계→전파) |
| **관련 연구** | [20_RELATED_WORK.md](project_md/20_RELATED_WORK.md) | UCA/VALU 등 선행 연구 비교 매트릭스 및 차별성 |
| **방법론/검증** | [30_METHODOLOGY_and_verification.md](project_md/30_METHODOLOGY_and_verification.md) | 문제 정의, 사전등록 규칙, 검증 체계 및 실험 구조 감사 |
| **데이터셋 계보** | [40_DATASETS_and_provenance.md](project_md/40_DATASETS_and_provenance.md) | 실사용 8종 데이터셋, 비순환 구축 및 데이터 출처 계보 |
| **심사 의견 대응** | [60_REVIEW_response_and_supplements.md](project_md/60_REVIEW_response_and_supplements.md) | 심사 피드백 대응 종합 및 보강 실험 결과 |
| **리비전 감사** | [61 ~ 71 시리즈](project_md/) | RQ6 재현성 보강, 최종 체크리스트, 예산/지면 감축 계획 |
| **실험 정본** | [canonical/](project_md/canonical/) | RQ1~RQ6별 실험 정본 (EXP01 ~ EXP06) |
| **아카이브** | [archive/](project_md/archive/) | 이전 47개 레거시 원본 무손실 보존 |

### 3. 사전 문헌 조사 (`survey/`)
- [**`deep-research-report_1.md` ~ `4.md`**](survey/): 멀티모달 비디오 RAG, 벡터 검색 최적화, 지식 그래프 융합 등에 관한 심층 서베이 보고서

### 4. 발표 자료 (`presentations/`)
- [**`kiise_vlmdb_deck_20260714.pptx`**](presentations/kiise_vlmdb_deck_20260714.pptx) / [**`pdf`**](presentations/kiise_vlmdb_deck_20260714.pdf): 슬라이드 덱
- [**`SLIDE_SPEC_for_external_agent_20260714.md`**](presentations/SLIDE_SPEC_for_external_agent_20260714.md): 발표 슬라이드 레이아웃 및 구성 명세서

---

## 🛠️ 환경 구축 및 실행 안내

### 가상환경 설정
```bash
# Conda 환경 생성
conda env create -f env/experiment_environment.yml

# 또는 pip 의존성 설치
pip install -r env/experiment_requirements.txt
```

### 인프라 실행 (pgvector)
```bash
docker compose -f infra/docker-compose.pgvector.yml up -d
```

---

## 🔒 데이터 및 대용량 파일 관리 정책
- GitHub 100MB 파일 크기 제한 및 저장소 최적화를 위해 대용량 벡터 파일(`*.fvecs`, `*.bin`, `*.npy`) 및 원시 데이터 캐시는 `.gitignore`를 통해 관리됩니다.
- 실험 재현에 필요한 데이터셋은 [`40_DATASETS_and_provenance.md`](project_md/40_DATASETS_and_provenance.md)의 계보 및 가이드를 참조하십시오.
