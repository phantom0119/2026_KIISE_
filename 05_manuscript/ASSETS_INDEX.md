# 원고 그림·표 자산 관리 디렉터리 총괄 (2026-07-23, 최종 갱신 2026-08-19)

**현행 정본 원고 = `0_main_paper.md`** (구 `1_paper_revision.md`, 2026-08-19 개명; 조판 정본 `paper_최종.pdf`와 전량 동기화 완료). 구버전 초안 및 중간 백업 자료는 저장소 경량화 및 최종본 단일 관리 정책에 따라 완전히 정리·배제되었습니다.

본 문서는 정본 원고의 모든 그림(3종)·표(11종)에 대응하는 관리 디렉터리의 색인이다.
각 디렉터리는 `data/`(원천 결과 파일 사본) + `README.md`(대상·수치↔원천 매핑·데이터셋·실험 체계·재현 방법·포함 파일·검증)로 구성된다.
대용량 파일(임베딩 npy/parquet 원본, 이미지 프레임 등)은 복사하지 않고 README에 절대경로로 참조한다.
수치 회귀 가드: `../scripts/verify_paper_script_numbers.py` (68/68 PASS, 2026-07-23).

| 대상 | 디렉터리 | 절/RQ | 핵심 원천 | 검증 결과 |
|---|---|---|---|---|
| 그림 1 파이프라인 개념도 | `figure1_dir/` | §4 도입 | 도식(데이터 무관); matplotlib 전신 `fig1_pipeline_noncircular_v6.png` 추적됨 | 33/33 문구 정합 PASS. **편집 가능 원본(pptx 등) 미확인 — 저자 보관 추정** |
| 그림 2 순환성 진단·통제 주입 | `figure2_dir/` | §5.2.1 RQ1 | `generate_manuscript_visuals_v6.py::figure_2_circularity()` + `vru_collapse_table.csv` + `qwen_aligned_circularity/{summary,contrasts}.csv`; Figure2.png과 렌더 산출물 바이트 동일 | 34/34 PASS (0.8540→0.8537 반올림 오류 발견→원고 정정 완료) |
| 그림 3 품질-지연 분포·파레토 | `figure3_dir/` | §5.2.2 RQ2 | `20260717_joint_image_caption_validation/{configuration_summary,pareto_front}.csv` (112구성×2기준=224점, 파레토 28점) | 19/19 PASS. 현 2패널 PNG의 렌더 스크립트 미보존 — README §5에 검증된 재현 레시피 수록 |
| 표 1 데이터셋 요약 | `table1_dir/` | §5.1.1 | 캐노니컬 데이터 실측(행수 재계수) + `freeze_validation` + `DATA_PROVENANCE` | 22/22 PASS (MIRIS 2건은 manifest 기반 — DB 내 테이블이라 재계수 불가) |
| 표 2 실행 환경·변인 통제 | `table2_dir/` | §5.1.2 | `environment_manifest.json` + 각 벤치 manifest 5종 | 27/29 PASS (RQ5 반복 15/20 분리 누락 발견→원고 정정 완료; '중간 이미지'는 스크립트 소스로만 확인) |
| 표 3 수정 전후 검색 품질 | `table3_dir/` | §5.2.1 RQ1 | `20260710_noncircular_collapse/` + v1/v2 캐노니컬 run 출력(2계층 대조) | 34/34 PASS (v2 semantic 재채점 일회성 스크립트 미보존 — 절차는 문서화됨) |
| 표 4 저장 구성 5종 비교 | `table4_dir/` | §5.2.2 RQ2 | `configuration_summary.csv` *__B2_vector__flat + `paired_bootstrap_comparisons.csv` | 38/38 PASS (`verify_table4.py` 동봉, 재실행 가능) |
| 표 5 질의 표본·결합도 Δ | `table5_dir/` | §5.2.3 RQ3 | `significance_expanded.csv`(질의 수준) + `t3_cluster_inference.json`(쌍-군집, B=5000 시드 20260712) | 19/19 PASS (고결합 2쌍 구성 = hour/time_of_day×stopped_vehicles 재확인) |
| 표 6 AI Hub↔UCA 일치성 | `table6_dir/` | §5.2.3 RQ3 | `20260712_uca_external/{UCA_contrasts.json,UCA_results.csv,UCA_query_deltas.csv}` | 19/19 PASS (V 표기가 질의 수준 φ임을 발견→원고에 '질의 수준' 한정어 추가) |
| 표 7 실측 vs 무작위 Δ | `table7_dir/` | §5.2.5 RQ5 | `20260710_pillarB/` B1 계열(직접 조회+원시 재계산+독립 부트스트랩 3중 검증) | 12/12 PASS (행 라벨 '상위 40개'가 실제로는 선택도 적응 후보 폭 52~612임을 발견→원고 정정 완료) |
| 표 8 pgvector 반복 스캔 | `table8_dir/` | §5.2.5 RQ5 | `pgvector_filtered.csv`(b3_hnsw_m16 행) + `pgvector_partial_vs_global*.csv`(부분 색인 문장 원천 포함) | 36/36 PASS (실제 러너 = `run_pgvector_ann_benchmark.py`) |
| 표 9 Milvus/Weaviate 재현 | `table9_dir/` | §5.2.5 RQ5 | `20260712_engine_replication/` (B4_results.csv + 원시 engine_*.csv 독립 재계산) | 42/42 PASS (행6은 보수적 상한 표기 — 교차로 BF 4쌍 자체는 recall 1.0000) |
| 표 10 물리 색인 프로파일 | `table10_dir/` | §5.2.5 RQ5 | 교차로: `index_grid_522visual/index_benchmark.csv`(N=142000); **시내도로: `Datasets/processed/sinnaedoro_traffic/index_benchmark/index_benchmark_from_log.csv`(N=131000) — 원천 해결** | 65/65 PASS (시내도로 CSV는 stdout 로그 재구성본; 4자리 재현율은 3자리 로그값의 0 패딩 — README에 명시) |

## 이번 패키징 검증에서 발견되어 원고에 반영한 정정 (2026-07-23)

1. §5.2.1: 재진술 주입 점수 0.8540 → **0.8537** (원천 0.85368664의 올바른 4자리 반올림; 서론의 0.854는 유효한 3자리 표기라 유지)
2. 표 2: "RQ5 준비 실행 제외·반복 15회" → "RQ5 실측 조건 반복 15회·대규모 색인 격자 반복 20회(준비 실행 제외)" (표 10 격자는 repeats=20)
3. 표 7 행 라벨: "전역 HNSW 상위 40개 검색 후 적용" → "전역 HNSW 검색 후 적용(선택도 적응 후보 폭)" (실제 K'=4×⌈k/s⌉, 52~612 범위; 고정 40은 어떤 조건에도 없음)
4. §5.2.3: "결합도 V≥0.3인 질의도" → "질의 수준 결합도 V≥0.3인 질의도" (UCA는 질의 수준 φ 기준 3개; 필드 수준 V 기준이면 17개라 모호성 제거)

## 2026-08-09 심사 대응 개정판 (`1_paper_revision.md`)

- 학술지 심사 의견 정본: `../project_md/61_REVIEWER_COMMENTS_CANONICAL.md`. 내부 추가 감사인 `../project_md/60_REVIEW_response_and_supplements.md`와 출처를 구분한다.
- 개정판 원고: `1_paper_revision.md` (원본 `0_paper_script.md`는 무수정 보존). 심사위원 1·2의 본문 수정 요구를 반영하고 용어·문체·전개를 정비했다. 페이지 머리말은 개정 PDF 생성 뒤 최종 확인해야 한다.
- 신규 자산: `table11_dir/` — 표 11(설명문 증거 조건별 VLM 답변 정확도, §5.2.6). 원천은 `table1_dir/data/vru_rag_vqa/` parquet + `experiments_expansion/rag_vqa/results_full/ladder_ci_analysis_20260723.json`(B=10,000, 시드 20260723) + 범주별 분해 CSV(재현 스크립트 동봉).
- 수치 회귀 가드(개정판 전용): `../scripts/verify_revision_numbers.py` (104/104 PASS, 2026-08-09). 원본 가드 68항목 + 표 11·범주별 분해 27항목 + 요약 분량·키워드 수·D1/D2 일관성 9항목.
- 2026-08-09 2차 수정(PI 승인): 요약(국문 499자)·Abstract(188단어) 전면 재작성(DBR 분량 규정 준수), 용어 결정 D1('벡터 데이터베이스 계층' — 본문 전면; **제목은 PI 지시(08-10)로 제출 제목 '종단형 멀티모달 RAG…' 유지**)·D2('증거'→관련 클립/검색 문맥, RQ6 3관문=관련 클립 회수·검색 문맥 인식·과제 편향) 일괄 적용. '증거' 잔존은 조판 주석의 구제목 인용과 실험 프롬프트 원문 '[증거 i]' 축어 기술 2곳뿐(의도적 보존).
- 2026-08-10 용어 통일 정본 표: `1_paper_revision.md` 최상단에 내부 편집용 정본 표(A 평가 체계 / B 다섯 설계 축 / C 데이터·정답 / D 지표·통계 / E 색인·실행 / F 표기 규칙, 총 40여 항목) 신설 — **조판 시 해당 구역 삭제**. 동시에 잔존 변형 6곳 정본화(서론 ¶1 '필터 검색 계획'→'검색 계획', ¶3 축 열거, §2 두 문장 다섯 축 정본 열거, §5.2.2 '검색용 데이터 구성', §5.2.1 지표값 '검색 품질'). 가드 109/109 유지.
## 2026-08-19 디렉터리 정리 및 정본 확정

- **개명**: `1_paper_revision.md` → **`0_main_paper.md`** (정식 핵심 문서). 참조 갱신 완료: `../scripts/verify_revision_numbers.py`, `figure1_dir/verify_figure1.py`, figure1·2/table1·3·11 README. 두 가드 재실행 정상(verify_revision_numbers 266검사 — 46 FAIL은 전부 구 감사본 문장을 기대하는 낡은 가드, 목록·사유는 메모리/이력 참조).
- **조판 정본**: `paper_최종.pdf`(2026-08-19 10:10, 공저자 HWP). `0_main_paper.md`는 이 PDF와 전량 동기화됨(사사 각주·저자 약력 포함). 심사 대응서 정본 = `심사의견대응서.pdf`(2026-08-19, 공저자 축약·재작성판; 구판 md/pdf는 아카이브 — **아카이브 md는 정본 대응서와 내용이 다름에 유의**).
- **구판 아카이브 정리**: 초기 마일스톤 초안(`0_paper_script.md`), 중간 백업본(`paper_0817.pdf`, `paper_0818.pdf` 등)은 최종본 경량화 지침에 따라 영구 삭제 정리 완료.
- **그림·표 실험 분리**: 그림/표 제작 실험은 각 `figureN_dir/`·`tableN_dir/`에서만 관리. `figure2_resources.zip`→`figure2_dir/`, `figure3_resources.zip`→`figure3_dir/`로 이동. 루트에는 원고가 참조하는 최종 산출물 `Figure1-3.png`만 유지.
- **루트 유지 파일**: `0_main_paper.md`, `paper_최종.pdf`, `심사의견대응서.pdf`, `Figure1-3.png`, `DB연구_최종본양식.pdf`(학회지 최종본 양식), 본 색인.

- 2026-08-09 그림 재생성(3종 모두 새 용어 반영 완료): 그림 1 = 국소 텍스트 패치 4곳(`figure1_dir/patch_figure1_terms_20260809.py`, 도식·썸네일 보존), 그림 2 = 원 스크립트 라벨 치환 재렌더('수정'→'수리', `figure2_dir/render_figure2_terms_20260809.py`), 그림 3 = 정본 렌더 스크립트 신설(`figure3_dir/render_figure3_terms_20260809.py`, §7 미보존 문제 해소). 교체 전 제출본은 각 `figureN_dir/FigureN_pre_terms_20260809.png`에 백업. 현행 md5: F1 `e4fa4426…`, F2 `1478ec17…`, F3 `06d43e8a…`.

## 미해결 항목 (저자 확인 필요)

- 그림 1 편집 가능 원본(손그림 대체본의 pptx/드로잉 파일) 소재 — 저자 보관 추정, 리포지토리 부재
- 그림 3 현행 2패널 PNG(07-20 07:16)의 정확한 렌더 스크립트 미보존 (데이터→수치 검증은 완결; 재현 레시피는 `figure3_dir/README.md` §5)
- 표 10 시내도로 행을 3자리 표기(0.997 등)로 바꿀지 여부 (현행 4자리는 로그 3자리의 0 패딩)
