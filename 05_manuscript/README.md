# [05] 논문 원고 및 심사 대응 리비전 (`05_manuscript/`)

본 디렉터리는 한국정보과학회 논문지(DBR, Database Research) 2026 게재 확정 논문의 **정본 원고(`0_main_paper.md`), 최종 출판용 조판본(`paper_최종.pdf`), 심사의견 대응서(`심사의견대응서.pdf`) 및 본문에 수록된 모든 그림(3종)과 표(11종)의 기계 판정 증거 패키지(Evidence Packages)**를 총괄 관리합니다.

---

## 🧭 논문 기본 정보

- **논문 제목**: 도시 감시 멀티모달 데이터베이스의 저장과 색인 그리고 검색 구조와 시각 언어 모델(VLM) 질의응답과 비순환 워크로드 기반의 정확도와 지연 시간 그리고 비용 평가  
  *(Storage, Indexing, and Retrieval Structures for Multimodal Urban-Surveillance VLM-QA: A Non-Circular Workload Study of Accuracy, Latency, and Cost)*
- **게재 학술지**: 한국정보과학회 논문지 (DBR, Database Research)
- **저자**: 박천복, Eduardo Linares, 김승현, 서영균† (경북대학교 컴퓨터학부)
- **현행 정본 원고**: [`0_main_paper.md`](0_main_paper.md) (조판 정본 [`paper_최종.pdf`](paper_최종.pdf)와 100% 동기화 완료)

---

## 📂 핵심 정본 파일 목록

| 파일명 | 형식 | 설명 및 핵심 역할 |
|---|:---:|---|
| [**`0_main_paper.md`**](0_main_paper.md) | Markdown | **현행 정본 원고**. 심사위원 1·2의 수정 요구사항을 전면 반영하고 초록(499자) 및 정본 용어를 통일한 최종 마크다운 소스입니다. |
| [**`paper_최종.pdf`**](paper_최종.pdf) | PDF | **최종 게재 조판 PDF** (2026-08-19 10:10, 한국정보과학회 DBR 공식 2단 조판 게재 확정본). |
| [**`심사의견대응서.pdf`**](심사의견대응서.pdf) | PDF | **공식 심사의견 대응서**. 심사위원 1과 심사위원 2의 본문 수정·보강 요구에 대한 공저자 최종 답변서입니다. |
| [**`DB연구_최종본양식.pdf`**](DB연구_최종본양식.pdf) | PDF | 한국정보과학회 논문지(DBR) 공식 최종본 투고 편집 양식 및 스타일 가이드입니다. |
| [**`Figure1.png`**](Figure1.png) | PNG | **그림 1**. 비순환 평가 작업 부하, 벡터 데이터베이스 계층 설계 및 VLM 답변 전파 분석 파이프라인 개념도. |
| [**`Figure2.png`**](Figure2.png) | PNG | **그림 2**. RQ1 정답 누수 순환성 진단 및 C1/C2 통제 주입 전후 검색 품질 변화 ($0.181 \rightarrow 1.000$). |
| [**`Figure3.png`**](Figure3.png) | PNG | **그림 3**. RQ2 112개 구성의 품질-지연시간 분포 및 28개 파레토 최적점(Pareto Frontier) 2패널 도표. |
| [**`ASSETS_INDEX.md`**](ASSETS_INDEX.md) | Markdown | 14개 그림/표 자산 디렉터리의 원천 데이터 매핑 및 검증 결과 종합 색인 문서. |

---

## 📊 도표별 기계 판정 증거 패키지 (Evidence Packages)

본 원고에 수록된 모든 그림(3종)과 표(11종)는 **데이터 조작이나 반올림 오기를 원천 차단**하기 위해, 각각 전담 디렉터리(`figureN_dir/`, `tableN_dir/`) 내에 원천 결과 데이터 슬라이스 사본(`data/`)과 전담 `README.md`, 독립 검증 스크립트를 보유합니다.

### 1. 그림 자산 (Figures 1 ~ 3)

| 대상 | 전담 디렉터리 | 본문 위치 | 핵심 원천 및 검증 상태 |
|---|---|:---:|---|
| **그림 1** 파이프라인 개념도 | [`figure1_dir/`](figure1_dir/) | §4 도입 | 33개 텍스트 요소가 본문 정본 용어와 100% 일치 (`verify_figure1.py` 33/33 PASS) |
| **그림 2** 순환성 진단·통제 주입 | [`figure2_dir/`](figure2_dir/) | §5.2.1 (RQ1) | `vru_collapse_table.csv`, `qwen_aligned_circularity` 원천 바이트 동일 34/34 PASS |
| **그림 3** 품질-지연 분포·파레토 | [`figure3_dir/`](figure3_dir/) | §5.2.2 (RQ2) | 112개 구성 $\times$ 2대 정답 기준 = 224점, 28개 파레토 최적점 일치 19/19 PASS |

### 2. 표 자산 (Tables 1 ~ 11)

| 대상 | 전담 디렉터리 | 본문 위치 | 핵심 원천 및 검증 상태 |
|---|---|:---:|---|
| **표 1** 데이터셋 요약 | [`table1_dir/`](table1_dir/) | §5.1.1 | 8개 데이터셋 32,880 클립 실측 행 수 재계수 일치 (22/22 PASS) |
| **표 2** 실행 환경·변인 통제 | [`table2_dir/`](table2_dir/) | §5.1.2 | `environment_manifest.json` 및 5대 벤치마크 매니페스트 일치 (27/29 PASS) |
| **표 3** 수정 전후 검색 품질 | [`table3_dir/`](table3_dir/) | §5.2.1 (RQ1) | 비순환 수리 전후 C1/C2 주입 34개 지표 일치 (34/34 PASS) |
| **표 4** 저장 구성 5종 비교 | [`table4_dir/`](table4_dir/) | §5.2.2 (RQ2) | 5개 저장 단위 nDCG, 지연시간, 저장용량 및 부트스트랩 CI 일치 ([`verify_table4.py`](table4_dir/verify_table4.py) 38/38 PASS) |
| **표 5** 질의 표본·결합도 Δ | [`table5_dir/`](table5_dir/) | §5.2.3 (RQ3) | 85개 질의 수준 및 $V \ge 0.3$ 고결합 밴드 효과량 일치 (19/19 PASS) |
| **표 6** AI Hub ↔ UCA 일치성 | [`table6_dir/`](table6_dir/) | §5.2.3 (RQ3) | 영어권 이상행동 129질의 외적 타당성 3/4 재현 일치 (19/19 PASS) |
| **표 7** 실측 vs 무작위 Δ | [`table7_dir/`](table7_dir/) | §5.2.5 (RQ5) | Filtered-ANN 역설 및 선택도 적응 후보 폭 일치 (12/12 PASS) |
| **표 8** pgvector 부분 색인 | [`table8_dir/`](table8_dir/) | §5.2.5 (RQ5) | PostgreSQL pgvector 부분 색인의 100% 재현율 회복 실측 일치 (36/36 PASS) |
| **표 9** 3대 엔진 크로스 검증 | [`table9_dir/`](table9_dir/) | §5.2.5 (RQ5) | pgvector vs Milvus vs Weaviate 42개 지표 일치 (42/42 PASS) |
| **표 10** 물리 색인 프로파일 | [`table10_dir/`](table10_dir/) | §5.2.5 (RQ5) | 14.3만 대규모 벡터 4대 색인 Flat/HNSW/IVF-Flat/IVF-PQ 일치 ([`verify_table10.py`](table10_dir/verify_table10.py) 65/65 PASS) |
| **표 11** VLM 답변 정확도 | [`table11_dir/`](table11_dir/) | §5.2.6 (RQ6) | Qwen2.5-7B 및 Llama-3-8B 3관문 답변 전파율 및 인식의 벽 실측 ([`compute_percategory_gap.py`](table11_dir/data/compute_percategory_gap.py) 재현) |

---

## 🚀 기계 판정 검증 스크립트 실행

각 도표 디렉터리 내의 자체 검증기를 즉시 실행하여 수치 일치성을 확인할 수 있습니다.

```bash
# 1. 그림 1 본문 용어 및 파일 무결성 검증 (33/33 PASS)
python3 05_manuscript/figure1_dir/verify_figure1.py

# 2. 표 4 5대 저장 단위 수치 및 부트스트랩 CI 독립 검증 (38/38 PASS)
python3 05_manuscript/table4_dir/verify_table4.py

# 3. 표 10 대규모 물리 색인 벤치마크 수치 검증 (65/65 PASS)
python3 05_manuscript/table10_dir/verify_table10.py

# 4. 표 11 VLM 답변 정확도 범주별 갭 결정론적 재계산
python3 05_manuscript/table11_dir/data/compute_percategory_gap.py
```

---

## 📦 과거 초고 및 중간 이력 아카이브 (`_archive_20260819/`)

과거 마일스톤의 작성 이력 및 이전 PDF들은 현행 정본 문서와 혼동되지 않도록 `_archive_20260819/` 내에 안전하게 보존되어 있습니다:
- `0_paper_script.md`: 2026-07-23 최초 투고 원본 초고
- `1_paper_revision_backup_pre_audit39_20260817.md`: 개정 작업 중 중간 백업본
- `paper_0817.pdf`, `paper_0818.pdf`: 2026-08-19 최종 HWP 조판 이전의 중간 컴파일 PDF
- `심사의견대응서_최종_20260818.{md,pdf}`: 공저자 축약 이전의 초기 심사의견 대응서 버전
- `freeze_validation_20260707.{json,md}`: 2026-07-07 시점의 초기 아티팩트 동결 검증서
