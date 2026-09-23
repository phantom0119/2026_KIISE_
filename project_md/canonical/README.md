# 연구 논문화 정본 인덱스

- 기준일: 2026-07-18
- **[현행화 2026-07-28]** 제출 정본은 `../../manuscript/paper_final.pdf`(2026-07-23)이다. 본 README의 §9 상태와 v6 파일 표기는 07-18 시점 기록이며, 수치·구조 충돌 시 paper_final.pdf가 우선한다. EXP02–EXP06에는 "레거시 결과 문서 흡수 (2026-07-28)" 섹션이 추가되었다(상위 `../MIGRATION_MAP_20260728.md` 참조). 2026-07-28 확정 용어 결정(벡터 데이터베이스 계층, '증거'→검색 문맥/관련 클립 체계)은 개정 원고용이며 제출 PDF에는 미적용이다.
- 적용 대상: DBR 장문 원고를 정본으로 하고 KDBC 단편 원고로 축약 가능한 연구 문서
- 현재 원고: [`../../manuscript/kiise_dbr_manuscript_v6_submission_revision.md`](../../manuscript/kiise_dbr_manuscript_v6_submission_revision.md)
- 원칙: 이 디렉터리의 8개 문서만 현재 논문화 정본으로 편집한다. 상위 `project_md/`의 기존 문서는 실행 이력·근거·정정 계보이며 신규 본문을 중복 작성하지 않는다.

## 1. 무엇부터 읽는가

1. 논문의 전체 논리와 Methodology를 이해하거나 집필할 때:
   [`00_DBR_PAPER_STRUCTURE_AND_METHODOLOGY.md`](00_DBR_PAPER_STRUCTURE_AND_METHODOLOGY.md)
2. 특정 실험을 재실행·수정·심사 대응할 때:
   아래 실험 설계 문서 중 해당 파일
3. 숫자를 원고에 인용할 때:
   각 실험 문서의 `결과 지위와 허용 주장` 및 `원자산`을 함께 확인

## 2. 정본 문서 지도

| 문서 | 담당 범위 | 대응 RQ |
|---|---|---|
| [`00_DBR_PAPER_STRUCTURE_AND_METHODOLOGY.md`](00_DBR_PAPER_STRUCTURE_AND_METHODOLOGY.md) | DBR/KDBC 논문 구조, 문제 정의, 전체 Methodology, 공통 통계·재현 규칙, 섹션별 집필 계약 | RQ1–RQ6 |
| [`EXP01_CIRCULARITY_AND_WORKLOAD_VALIDITY.md`](experiments/EXP01_CIRCULARITY_AND_WORKLOAD_VALIDITY.md) | C1–C3 순환성, VRU/CCTV 수리, 522 통제 주입, tri-source와 A6 | RQ1 |
| [`EXP02_RETRIEVAL_PLAN_AND_COUPLING.md`](experiments/EXP02_RETRIEVAL_PLAN_AND_COUPLING.md) | B0–B5, strict/semantic 이중 정답, predicate–relevance 결합도 | RQ3–RQ4 |
| [`EXP03_FILTERED_ANN_PHYSICAL_INDEX_AND_DEPLOYMENT.md`](experiments/EXP03_FILTERED_ANN_PHYSICAL_INDEX_AND_DEPLOYMENT.md) | real-vs-random predicate, ANN, 엔진, Flat/HNSW/IVF/PQ, partial/local, hot/cold | RQ5 |
| [`EXP04_EVIDENCE_REPRESENTATION_AND_UNIFIED_EMBEDDING.md`](experiments/EXP04_EVIDENCE_REPRESENTATION_AND_UNIFIED_EMBEDDING.md) | caption/frame/joint/multi/dual, 동일-Qwen 112구성, 캡션 생성기 ablation | RQ2, RQ4–RQ5 |
| [`EXP05_VLM_QA_PROPAGATION.md`](experiments/EXP05_VLM_QA_PROPAGATION.md) | 증거 사다리, 다중 시점, 색인→증거→답변 전파 게이트 | RQ6 |
| [`EXP06_EXTERNAL_VALIDATION_AND_ROBUSTNESS.md`](experiments/EXP06_EXTERNAL_VALIDATION_AND_ROBUSTNESS.md) | UCA·MEVA·MIRIS 외부 검증, 규모·seed·교차감사, 일반화 경계 | 전 RQ의 외적 타당성 |

## 3. 현재 연구를 한 문장으로 정의

> 본 연구는 새로운 VLM을 학습하는 연구가 아니라, 도시 감시 멀티모달 아카이브에서 고정된 VLM에 공급할 증거를 데이터베이스가 어떤 단위로 저장하고, 자연어 의미 검색과 센서·시공간 predicate를 어떤 순서로 결합하며, 어떤 물리 색인과 배포 정책으로 실행해야 하는지를 비순환 워크로드에서 정확도·지연·공간·구축비의 공동 설계 문제로 평가하는 연구이다.

## 4. 연구 과정의 논리적 순서

```text
공개 데이터·선행 시스템 조사
  → 초기 B0–B5 워크로드 구축
  → 완벽 지표의 순환성(C1–C3) 발견
  → 수리 전후 붕괴 + 동일조건 통제 주입
  → 522 tri-source 워크로드와 A6 감사 구축
  → 검색 계획·결합도 비교
  → 실측 predicate filtered-ANN·물리 색인·DB 배포 비교
  → 동일 encoder의 저장 표현·통합 임베딩 공동 ablation
  → 외부 데이터·scale·seed 강건성 확인
  → 증거 검색 개선의 VLM-QA 전파 경계 검증
  → 단일 우승자가 아닌 목적·SLA별 Pareto 설계 지침 도출
```

## 5. 정본 수치 규칙

- 522 canonical은 `3,000 clips / 85 queries / strict qrels 6,809 / semantic qrels 24,872`다.
- `qrels.tsv`와 `qrels_semantic.tsv`의 `wc -l` 값 `6,810/24,873`은 헤더를 포함한다. 본문에는 데이터 행 수인 `6,809/24,872`만 쓴다.
- 최신 동일-encoder 공동 ablation은 `5 representations / 3 compatible search plans / 7 indexes / 112 valid configurations`다.
- 과거 91구성은 `joint_image_caption` 추가 전 선행 격자다. 최신 원고에서는 112구성을 정본으로 쓴다.
- BGE-M3 순환성 실험과 Qwen 정렬 반복은 별도 실험이다. `0.170033`과 `0.181005`를 같은 기준선으로 혼합하지 않는다.
- 522의 3,000-caption 검색 트랙과 143,830-frame ANN 트랙은 평가 단위·encoder·정답이 다르다.

## 6. 주장 등급

| 등급 | 사용 조건 | 원고 표현 |
|---|---|---|
| 확증 | 실행 전 가족·estimand·판정 규칙 고정, 적절한 반복 단위와 다중비교 보정 통과 | “유의하게”, “확증했다” |
| 확립 관찰 | 조작·무결성·재계산은 통과했으나 사전등록 확증 가족은 아님 | “관측했다”, “실측했다” |
| 탐색적 | CI가 0을 포함하거나 외부 이식·소표본·사후 대조 | “경향을 보였다”, “탐색적으로” |
| 가설적 | 병목 후보 또는 후속 실험 설계 근거 | “가능성이 있다”, “향후 검증한다” |
| 금지 | 실험이 직접 지지하지 않는 확대 주장 | “보편적으로 최적”, “모든 데이터에서 보장”, “답변 품질까지 보장” |

## 7. 레거시 문서의 취급

상위 `project_md/`의 000–900 문서는 삭제하지 않는다. 이유는 다음과 같다.

- 사전등록과 amendment의 시간 순서를 보존한다.
- 음성 결과와 중단 규칙의 적용 기록을 보존한다.
- 스크립트·원자산이 기존 파일명을 참조하는 경우를 깨지 않는다.
- 잘못된 수치가 왜 정정되었는지 추적할 수 있게 한다.

다만 신규 논문 문장은 이 정본 문서군에서만 작성한다. 레거시 문서와 정본이 충돌하면 실제 원자산, 검증 manifest, 최신 v6 원고 순으로 판정한다.

## 8. Manuscript 디렉터리 관리 계약

`2026_KIISE/manuscript/`에는 다음 네 파일만 유지한다.

| 파일 | 역할 |
|---|---|
| `DB연구_Sample.pdf` | 학회 제공 조판 참고 샘플 |
| `kiise_dbr_manuscript_v6_submission_revision.md` | 최신 원고 소스 |
| `kiise_dbr_manuscript_v6_submission_revision.docx` | 최신 편집·제출용 Word |
| `kiise_dbr_manuscript_v6_submission_revision.pdf` | 최신 렌더링 검사용 PDF |

v5 working draft의 부록 D–I, 구조 강화 기록, v5/v6 검증 Markdown과 manuscript README의 유효 정보는 이 canonical 문서군에 통합했다. 주요 대응 관계는 다음과 같다.

| 과거 manuscript 정보 | 현재 정본 |
|---|---|
| Motivation·RQ·Research Gap·주장 경계 | `00_DBR_PAPER_STRUCTURE_AND_METHODOLOGY.md` |
| 사용자 질의 위치·전체 코퍼스·evidence packet·24시간 운영 경계 | `00_DBR_PAPER_STRUCTURE_AND_METHODOLOGY.md` §1.1, §12.5 |
| 전체 실험 포함·제외와 데이터 역할 | 본 README 및 EXP01–EXP06 |
| 91구성 선행 ablation과 최신 112구성 | EXP04 |
| 캡션 생성기 전체 결과 | EXP04 |
| 외부·scale·seed·감사 결과 | EXP06 |
| 제출 형식과 검증 상태 | 본 README §9 |

삭제 전 교차 분석한 Markdown의 판정은 다음과 같다.

| 과거 파일 | 판정 |
|---|---|
| `_internal_dbr_base.md` | v5 생성 중간본; v6와 canonical 방법론으로 대체 |
| `kiise_dbr_manuscript_v5_complete_research_working_draft.md` | 부록 D–I의 유효 정보를 위 대응표에 따라 통합; 91구성 수치는 112구성으로 갱신 |
| `kiise_dbr_manuscript_v5_complete_research_working_draft_VALIDATION.md` | v5 조판·수치 검증 이력; 최신 제출 상태가 아니므로 폐기 |
| `MANUSCRIPT_STRUCTURE_STRENGTHENING_20260717.md` | RQ–증거 매핑과 주장 경계를 §2·§9·EXP01–EXP06에 최신화 |
| `kiise_dbr_manuscript_v6_submission_revision_VALIDATION.md` | 유효한 형식 계약과 명령을 §9에 통합; 14쪽·91구성 서술은 15쪽·112구성으로 교정 |
| `manuscript/README.md` | 디렉터리 정책을 본 §8로 이전 |

`_internal_*`, v5 원고, validation report, reference DOCX와 저자정보 JSON은 최종 논문 버전이 아니므로 manuscript에 보존하지 않는다. 재생성 중간 파일은 `paper_assets/20260718_manuscript_build_support/`에서 관리한다.

## 9. 최신 제출본 상태와 재생성

- 최신 검증: `PASS_WITH_METADATA_PENDING`
- PDF: A4 15쪽, 본문 2단
- 객체: 표 15개, 그림 6개
- 자동 형식 검사: 80 PASS, 0 FAIL
- 실험 검증: 최신 joint 17/17 PASS
- 남은 행정정보: 박천복·Eduardo Linares·김승현의 직위, 교신저자 전화번호

현재 그림 6과 표 12는 joint image+caption을 포함한 5개 표현·112개 호환 구성 결과를 사용한다. 과거 검증 문서의 “14쪽”, “91개 구성”은 폐기된 중간 상태다.

```bash
python 2026_KIISE/scripts/generate_manuscript_visuals_v6.py
python 2026_KIISE/scripts/make_dbr_submission_revision_v6.py
python 2026_KIISE/scripts/verify_dbr_submission_revision_v6.py
Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/verify_joint_image_caption_experiment.py
```

Parquet 원자산 검증은 `Datasets/envs/kiise-vlmdb` 환경을 사용한다. 시스템 기본 Python의 다른
`pyarrow` 버전은 기존 Parquet metadata와 호환되지 않을 수 있다.
