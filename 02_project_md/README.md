# [02] 연구 기록 및 논문화 정본 인덱스 (`02_project_md/`)

본 디렉터리는 KIISE-DBR 2026 연구의 문제 정의, 실험 마스터플랜, 데이터셋 계보, RQ별 실증 결과 및 학회 심사위원 대응 문서를 체계적으로 관리합니다.

---

## 🌟 단일 마스터 정본 진입점 (Single Source of Truth)

> 👉 [**`00_KIISE_DBR_FINAL_MASTER_SPECIFICATION.md`**](00_KIISE_DBR_FINAL_MASTER_SPECIFICATION.md)
> 
> **최종 KIISE-DBR 논문을 완성하고 재현하기 위해 필요한 모든 핵심 지식**을 하나로 집약한 통합 정본 문서입니다.
> 
> - **주요 내용**: 확정 논문 정보 및 3대 공헌 / 실사용 8종 데이터셋 계보 / 벡터 DB 5대 설계 축(112개 구성) / RQ1~RQ6 실험 결과(표 1~11 수치 정본) / 심사위원(R1, R2) 피드백 대응 및 보강 실험 분석 / 실행 스크립트 매핑

---

## 📂 하위 디렉터리 구성 및 보관 체계

산재되어 있던 연구 문서들은 이력 보존과 탐색 편의를 위해 성격별로 다음과 같이 계층화되어 있습니다:

```
02_project_md/
├── 00_KIISE_DBR_FINAL_MASTER_SPECIFICATION.md  # ★ 연구 종합 마스터 정본 (단일 진입점)
├── README.md                                    # 본 인덱스 안내 문서
├── reviews_and_audits/                          # 2026-08 학술대회 심사 대응 및 최종 감사 문서군
├── canonical/                                   # RQ1~RQ6별 확정 실험 설계 및 정본 명세 (EXP01~EXP06)
├── legacy_thematic_202607/                      # 2026-07 주제별 통합본 6종 및 이관 지도
├── external_and_notes/                          # 타 논문(ECIR 2027), 세미나 노트 및 부속 자료
├── archive/                                     # 2026-07 이전 초기 레거시 원본 47편 (무손실 보존)
└── notion_dbr_2026/                             # 연구 노션 워크스페이스 마크다운 덤프
```

---

### 1. [`reviews_and_audits/`](reviews_and_audits/) (심사 대응 및 리비전 감사)
2026년 8월 KIISE-DBR 심사위원 피드백 대응 및 최종 원고 확정 과정에서 작성된 문서군입니다.
- **`60_REVIEW_response_and_supplements.md`**: 심사위원 의견별 1차 대응 및 보강 실험 종합
- **`61_REVIEWER_COMMENTS_CANONICAL.md`**: 심사위원 원문 코멘트 정본
- **`63_` / `66_REVIEW_RESPONSE_SUBMISSION_READY_20260817.md`**: 최종 제출용 심사의견 답변서 정본
- **`65_SUPPLEMENT_RQ6_REPRODUCIBILITY_20260817.md`**: RQ6 VLM QA 답변 전파 재현성 보강 명세
- **`67_` ~ `71_`**: 지면 축소 계획(69), 용어 및 실험 범위 감사(70), 최종 PDF 동기화 체크리스트(67)

### 2. [`canonical/`](canonical/) (실험별 정본 명세)
연구 가설과 실험 절차를 사전등록(Preregistration)한 RQ별 정본 디렉터리입니다.
- **`EXP01`**: 비순환성 진단 및 워크로드 타당성 (RQ1)
- **`EXP02`**: 검색 계획 비교 및 모달리티 결합 (RQ3, RQ4)
- **`EXP03`**: Predicate 필터링 ANN 및 물리 색인 배포 (RQ5)
- **`EXP04`**: 증거 표현 및 통합 임베딩 최적화 (RQ2)
- **`EXP05`**: 3관문 VLM QA 답변 전파 진단 (RQ6)
- **`EXP06`**: 외적 타당성 및 도메인 일반화 검증

### 3. [`legacy_thematic_202607/`](legacy_thematic_202607/) (2026-07 주제별 정리본)
2026년 7월 28일 1차 제출 시점에 작성되었던 6대 주제별 통합 정리본입니다.
- `00_MASTER`: 연구 현황, 불변 규칙 28선, 용어 사전, 결정 로그
- `10_INTRODUCTION`: 동기, Research Gap, RQ 구조
- `20_RELATED_WORK`: UCA/VALU 등 선행 연구 비교 매트릭스
- `30_METHODOLOGY`: 방법론, 검증 체계 및 구조 감사
- `40_DATASETS`: 8종 데이터셋 계보 및 비순환 구축 절차
- `MIGRATION_MAP_20260728.md`: 초기 47개 레거시 문서 이관 매핑표

### 4. [`external_and_notes/`](external_and_notes/) (부속 및 외부 연구 자료)
- `90_ECIR2027_multimodal_paper_intro_management.md`: ECIR 2027 벤치마크 논문 관련 별도 문서 (본 KIISE 논문과 별개)
- `KIISE-DBR_2026_Note.pdf` / `KIISE_DBR_2026_Notion_Import.zip`: 초기 연구 세미나 및 노션 연동 자료
- `paper_final.pdf`: 2026-07-23 초기 제출본 PDF (최종본은 [`05_manuscript/paper_최종.pdf`](../05_manuscript/paper_최종.pdf) 참조)
