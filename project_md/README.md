# project_md 인덱스 — 연구 기록과 논문화 정본

> **2026-07-28 주제별 통합 완료.** 최상위에는 주제별 통합 정리본 6개 + 별도 논문 문서 1개만 유지한다.
> 논문 구조·Methodology·실험별 정본은 여전히 [`canonical/`](canonical/README.md)이 관리한다(EXP01–EXP06).
> 제출 정본은 `../manuscript/paper_final.pdf`(2026-07-23, 접수양식 1쪽 + 본문)이다.
> 통합 이전의 원본 47개는 `archive/legacy_premerge_20260728/`에 무손실 보존했다(이관 지도: [MIGRATION_MAP_20260728.md](MIGRATION_MAP_20260728.md)).

## 문서 지도 (2026-07-28 이후)

| 파일 | 주제 | 통합한 구 문서 |
|---|---|---|
| [00_MASTER_status_and_decisions.md](00_MASTER_status_and_decisions.md) | 연구 현황·불변 규칙 28·용어 사전·결정 로그·원고 버전 이력 (국문 단일 진입점) | 000_MASTER, 010_OVERVIEW_EN, 020_GLOSSARY, 650 |
| [10_INTRODUCTION_motivation_and_RQ.md](10_INTRODUCTION_motivation_and_RQ.md) | 서론 정본 — 동기·사회적 문제·Research Gap·확정 RQ 구조(검증→설계→전파) | 000_Introduction, 100, 770, 780, 800 |
| [20_RELATED_WORK.md](20_RELATED_WORK.md) | 관련 연구 검토 — UCA/VALU, 기여 강화 매트릭스, §2 최종 비교 구도 | 200, 740_RELATED |
| [30_METHODOLOGY_and_verification.md](30_METHODOLOGY_and_verification.md) | 문제 정의·방법론·사전등록(410/420 규칙 전량)·검증 체계·실험 구조 감사 | 300, 400, 410, 420, 430, 710, 740_AUDIT, 760×2, 810_blueprint |
| [40_DATASETS_and_provenance.md](40_DATASETS_and_provenance.md) | 데이터셋 정본 — 실사용 8종/제외 2종, 비순환 구축, raw/파생 계보, 코퍼스 정본 수치 | 000_Datasets, 500, 680, 690, 730, 790, DATA_PROVENANCE |
| [60_REVIEW_response_and_supplements.md](60_REVIEW_response_and_supplements.md) | 심사 대응·보강 실험 (910–914 **원문 verbatim 보존**, 912 FROZEN 무변경) | 910, 911, 912, 913, 914 |
| [90_ECIR2027_multimodal_paper_intro_management.md](90_ECIR2027_multimodal_paper_intro_management.md) | ⚠ **별도 논문**(ECIR 2027 멀티모달 벤치마크) — 본 KIISE 연구와 다른 문서 | 구 900 (개명만) |

## 실험 기록은 어디에 있는가

레거시 결과 문서(600–670, 700, 720, 750×2, 810_CAPTION, 820, 821)는 `canonical/experiments/EXP02–EXP06`의
**"레거시 결과 문서 흡수 (2026-07-28)"** 섹션에 고유 내용·정정·아카이브 경로가 정리되었다.

| RQ | 정본 문서 | 흡수된 레거시 |
|---|---|---|
| RQ1 | EXP01_CIRCULARITY | (해당 없음 — 기존 정본 유지) |
| RQ3–RQ4 | EXP02_RETRIEVAL_PLAN | 670(KG 붕괴) |
| RQ5 | EXP03_FILTERED_ANN | 600, 620, 720 |
| RQ2 | EXP04_EVIDENCE_REPRESENTATION | 750_RAG, 750_UNIFIED, 810_CAPTION, 820, 821 |
| RQ6 | EXP05_VLM_QA_PROPAGATION | 610, 630, 660 |
| 외적 타당성 | EXP06_EXTERNAL_VALIDATION | 640, 700 |

## SYNC 기준과 확정 용어 (2026-07-28)

모든 통합본은 `paper_final.pdf`(2026-07-23)를 수치·구조의 정본으로 삼아 정정되었다
(다섯 설계 축, 검색 계획 4종, 검색 신호 4종, 112 구성, 코퍼스 3,000/85/6,809/24,872).
2026-07-28 확정 용어 결정 — **현 제출 PDF에는 미적용, 개정 원고·보고서용**:

1. '데이터베이스 계층' → **벡터 데이터베이스 계층**
2. '증거' 전면 치환 → 상위 k 검색 결과(DB 반환) / 검색 문맥(VLM 입력) / 관련 클립·검색 정답 집합(정답 판정); RQ6 3관문 = 관련 클립 회수 → 검색 문맥 인식 → 과제 편향
3. 클립 조작적 정의: 데이터셋 배포 mp4 1파일 = 1클립 (MEVA[20] 계보로 방어)
4. 러닝 헤드 p.7 이후 구제목 잔존 → 재제출/개정 시 수정

상세는 [00_MASTER_status_and_decisions.md](00_MASTER_status_and_decisions.md)의 결정 로그 참조.

## 아카이브

- `archive/legacy_premerge_20260728/` — 2026-07-28 통합 전 원본 47개 (무손실, 수정 금지). 사전등록 시간 순서·음성 결과·정정 계보의 근거. 스크립트 참조 경로도 이 위치로 갱신됨(410·420·500·630·912).
- `archive/` (기존 02–40) — 여정 1–4막 36편. v1 검색 수치(B0–B5)는 순환 결함으로 **인용 금지**.

레거시 문서와 통합본이 충돌하면 실제 원자산 → 검증 manifest → paper_final.pdf → canonical 순으로 판정한다.
