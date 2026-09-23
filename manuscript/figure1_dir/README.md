# 그림 1 관리 디렉터리 (figure1_dir)

## 1. 대상

- **캡션 원문(현재 원고 기준)**: **&lt;그림 1&gt; 비순환 평가 작업 부하, 벡터 데이터베이스 계층 설계 및 VLM 답변 전파 분석 파이프라인**
- **원고 내 위치**: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/0_main_paper.md`
  - 행 90: 그림 도입문("그림 1은 세 원천 자료의 분리부터 … 전체 절차를 나타낸다.")
  - 행 92: 이미지 참조 `![…](./Figure1.png)`
  - 행 94: 캡션
  - (주의) 원고 파일은 2026-07-23 17:51 기준으로 계속 수정 중이므로 행 번호는 이 시점 스냅숏이다.
- **소속 절/RQ**: 4장 방법론 도입부(행 88–94). 특정 RQ의 결과 그림이 아니라 **RQ1–RQ6 전체 연구 절차를 요약하는 개념 도식**이다. 도식 내부에 RQ1(순환성 검증), RQ2–RQ5(데이터베이스 계층 설계 축), RQ6(답변 효과 검증) 박스가 모두 포함된다.
- **그림 파일 자체**: `manuscript/Figure1.png` (1482×695 px, 96 DPI, RGBA, 285,312 bytes, md5 `06b2127ef4d48aaf8f8fa0d56bec4fbc`, 수정 시각 2026-07-22 21:13). 초기 변형 `manuscript/Figure1-1.png` (2536×1005 px, 144 DPI, 667,600 bytes, md5 `593d5dfc90edb9e1d2a981c27656cb23`, 2026-07-20 04:38)이 함께 존재한다.

## 2. 수치 ↔ 원천 매핑

그림 1은 **데이터 기반 그림이 아닌 개념 도식**으로, 원고 본문에 인쇄되는 실험 수치를 포함하지 않는다(도식 안의 "@10", "상위 10개" 등은 평가 규약 표기이다). 따라서 원 지시대로 수치 매핑 대신 **도식의 각 구성 요소가 원고 어느 절/행과 어떤 스크립트에 대응하는지**를 표로 기록한다. 행 번호는 `0_paper_script.md` 2026-07-23 17:51 스냅숏 기준.

| 도식 구성 요소(도식 내 문구) | 원고 대응 절/행 | 대응 스크립트(절대경로, `…` = `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE`) |
|---|---|---|
| 원천① 센서/메타데이터(시간, 위치, 신호 상태, 교통량) | §4.1 행 98, §5.1.1 행 143 | `…/scripts/build_intersection_signal_sensors.py`, `…/scripts/build_visual_sensor_join.py` |
| 원천② 영상 픽셀·프레임(영상 설명문, 이미지 벡터) | §4.1 행 98, §5.1.1 행 143 | `…/scripts/build_intersection_captions.py`, `…/scripts/build_intersection_frame_clip.py` |
| 원천③ 사람 주석(검색 정답 집합) | §4.1 행 98–99 | `…/scripts/build_intersection_annotation_facets.py` |
| 사용자 질의 예시("오전 10시경에 오토바이 2대…") | 원고 미출현 — 도식 전용 예시 문구 | (해당 없음) |
| 자연어 의미 조건 / 메타데이터 조건 분기 | §3 행 84, §5.1.1 행 144 | `…/scripts/build_intersection_trisource_canonical.py` |
| 생성 경로 분리 및 순환성 검증(RQ1) 박스: 직접 정보 재사용 검사·비순환 기준·정답 조건 주입·정답 라벨 재진술 주입 | §4.1 행 98–102, §5.2.1 행 175–196 | `…/scripts/build_intersection_trisource_canonical.py`(6종 자동 검사), `…/scripts/run_circularity_controlled_injection.py`, `…/scripts/verify_circularity_controlled_injection.py`, `…/scripts/run_qwen_aligned_circularity_control.py` |
| 데이터베이스 계층 — 검색용 데이터 구성(RQ2): 영상 설명문·대표 이미지·이중 색인·이미지·설명문 결합·여러 이미지 벡터 | §4.2 행 106, RQ2 정의 행 118, §5.2.2 행 198–220 | `…/scripts/run_storage_unit_benchmark.py`, `…/scripts/run_joint_storage_search_index.py`, `…/scripts/build_qwen3_joint_image_caption_assets.py` |
| 데이터베이스 계층 — 검색 계획(RQ3): 벡터 단독·혼합·검색 전/후 조건 적용 | §4.2 행 107, RQ3 정의 행 119, §5.2.3 행 222–254 | `…/scripts/run_retrieval_baselines.py`, `…/scripts/run_engine_filtered_bench.py` |
| 데이터베이스 계층 — 검색 신호와 순위 융합(RQ4): 메타데이터 단독·BM25 어휘·텍스트 벡터·RRF | §4.2, RQ4 정의, §5.2.4 | `…/scripts/run_retrieval_baselines.py`, `…/scripts/run_weighted_fusion_rerank_sweep.py` |
| 데이터베이스 계층 — 물리 색인과 배포(RQ5): Flat·HNSW·IVF-Flat·IVF-PQ / 전역·부분 색인 | §4.2 행 109–110, RQ5 정의 행 121, §5.2.5 행 263–320 | `…/scripts/run_index_structure_benchmark.py`, `…/scripts/run_filtered_ann_benchmark.py`, `…/scripts/run_filtered_ann_real_predicate.py`, `…/scripts/run_pgvector_ann_benchmark.py`, `…/scripts/run_pgvector_partial_index.py` |
| 정답 기준 박스: 의미론적 정답=사람 주석 / 엄격한 정답=센서 조건 ∩ 사람 주석 / ANN 정답=조건별 Flat 상위 10개 | §3 행 84, 표 1 행 137–139, §5.1.3 행 168(Recall@10) | `…/scripts/build_intersection_trisource_canonical.py`, `…/scripts/run_filtered_ann_benchmark.py` |
| 검색 품질·비용 평가 박스: nDCG@10·재현율@10·p50/p95 지연·저장 크기·구축 시간 | §5.1.3 행 168 | `…/scripts/run_significance_analysis.py`, 각 벤치마크 러너 공통 |
| 검색된 증거 집합(CCTV 썸네일 3장 + …) | 개념 표현. 썸네일은 AI Hub 교차로 CCTV 프레임 계열로 보이나 클립 식별자 미확인(§7 참조) | (해당 없음) |
| 답변 효과 검증(RQ6) 박스: 비교 내 답변 모델·프롬프트 고정, 증거 변경에 따른 전파 측정 → 최종 답변 | RQ6 정의 행 122, §5.2.6 행 322–329 | `…/scripts/run_rag_vqa.py`, `…/scripts/run_multiview_answer_vlm.py`, `…/scripts/eval_multiview_answer_vlm.py` |

## 3. 사용 데이터셋

그림 1 자체는 개념 도식이므로 **수치 산출에 사용된 데이터셋은 없다**. 도식이 묘사하는 파이프라인의 주 평가 데이터는 AI Hub 교차로 CCTV(원고 표 1, 행 136: 설명문 3,000개·질의 85개; 행 143: 센서 클립 32,880개·시각 클립 52,462개→47,098개 연결→시드 20260710으로 3,000개 층화 표집)이며, 캐노니컬 가공 산출물은 `…/scripts/build_intersection_trisource_canonical.py`가 생성하는 tri-source 코퍼스(metadata.parquet 등)이다. 도식 중앙 "검색된 증거 집합" 열에 삽입된 CCTV 썸네일 3장은 AI Hub 교차로 CCTV 프레임 계열로 보이나, PNG에 병합되어 있어 원본 클립 식별자는 확인하지 못했다(§7 UNVERIFIED 항목).

## 4. 실험 체계

- **그림 제작 체계(이 그림의 직접 원천)**:
  - 현재 게재본 `Figure1.png`(96 DPI)와 변형 `Figure1-1.png`(144 DPI)는 내보내기 DPI·스타일로 보아 **프레젠테이션 도구(PowerPoint 계열)에서 수작업 제작 후 PNG로 내보낸 것**으로 판단된다. **편집 가능 원본(pptx/드로잉 파일)은 저장소 전수 탐색에서 미확인 — 저자 보관 추정**. 저장소에는 git 커밋 이력도 없어 파일 시스템 시각(2026-07-20, 07-22)만이 제작 시점 근거다.
  - 프로그램 생성 전신(前身): `…/scripts/generate_manuscript_visuals_v6.py`의 `figure_1_pipeline()`이 만든 matplotlib 초안 `…/paper_assets/20260717_manuscript_visuals_v6/fig1_pipeline_noncircular_v6.png`(md5 `300b4f3e77d85eff31749adc831fb4a8`). 이 md5는 2026-07-18 원고 조판본의 삽입 이미지 `…/paper_assets/20260718_manuscript_content/media/rId30.png`와 **정확히 일치**하여, 07-18까지는 matplotlib 초안이 그림 1이었고 이후 수작업 도식으로 교체되었음을 보인다. 단, 현 시점 스크립트의 `figure_1_pipeline()`은 후속 개정으로 `fig1_system_architecture_v7` 파일명을 저장하므로, `fig1_pipeline_noncircular_v6.png`은 이 스크립트의 **이전 개정판** 산출물이다(개정 이력 미보존).
  - 발표 자료 `…/presentations/kiise_vlmdb_deck_20260714.pptx`(생성 스크립트 `…/scripts/build_deck_pptx.py`)의 내장 미디어 4개는 그림 1과 체크섬·크기가 모두 불일치 — 그림 1의 원천 아님.
- **도식이 묘사하는 실험 체계**(모델·파라미터는 원고 §5.1.2 행 146–164): 설명문 생성 Qwen2.5-VL-7B-Instruct 및 Qwen3.5-9B(최대 110토큰, 탐욕적 디코딩), 임베딩 BGE-M3(1,024차원)·CLIP ViT-B/32(512차원)·Qwen3-VL-Embedding-2B(2,048차원), 색인 HNSW(M=32, efConstruction=200, efSearch∈{64,256})·IVF(nlist=64, nprobe∈{8,32})·IVF-PQ(m=32, 6비트), 표집 시드 20260710, 총 112개 구성.
- **관련 사전등록/결과 문서**: `…/project_md/760_RESEARCH_FLOW_20260714.md`(도식이 시각화한 연구 흐름 서사; data/에 사본), `…/project_md/400_METHOD_experiment_system_masterplan_20260710.md`, `…/project_md/500_DATASETS_construction_noncircular_execution_20260710.md`, `…/project_md/430_METHOD_verification_framework_20260711.md`.

## 5. 재현 방법

**(a) 원천 재실행 경로(도식 다시 만들기)**

1. 현재 게재본과 동일한 편집본 재생성: **불가능(편집 가능 원본 미확인, 저자 보관 추정)**. 저자에게 pptx 원본을 요청하거나, 아래 초안 스크립트를 출발점으로 재작성해야 한다.
2. 프로그램 생성 초안(교체 전 버전) 계열 재생성:
   ```bash
   cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE
   python3 scripts/generate_manuscript_visuals_v6.py
   # → paper_assets/20260717_manuscript_visuals_v6/fig1_system_architecture_v7.{png,pdf,svg} 등 생성
   # (현 스크립트는 개정판이므로 fig1_pipeline_noncircular_v6.png 자체는 재생성되지 않음)
   ```
3. 도식 내용의 사실 근거(파이프라인 각 단계)는 §2 표의 스크립트들을 원고 §5.1.2 설정으로 실행하면 재검증된다.

**(b) data/ 사본만으로의 최소 재검증 경로**

```bash
# 도식 텍스트 요소 ↔ 원고 본문 정합 + 파일 무결성(md5/해상도/캡션 행) 일괄 재검증
python3 /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/figure1_dir/verify_figure1.py
# data/generate_manuscript_visuals_v6.py 의 figure_1_pipeline() 로 초안 도식 재현 가능(사본 단독 실행 시 matplotlib 필요)
```

## 6. 포함 파일 목록

**data/ 사본(2건)**

| 원 절대경로 | 사본명 | 설명 |
|---|---|---|
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/generate_manuscript_visuals_v6.py` | `data/generate_manuscript_visuals_v6.py` | 그림 1의 프로그램 생성 전신(matplotlib 초안 `figure_1_pipeline()`)을 포함한 원고 그림 일괄 생성 스크립트(현 개정판) |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/760_RESEARCH_FLOW_20260714.md` | `data/760_RESEARCH_FLOW_20260714.md` | 도식이 시각화한 연구 전체 흐름(배경→문제→설정→방법→결과) 서사 문서 |

**보조 파일**: `verify_figure1.py` — §7 검증을 재실행하는 스크립트(이 디렉터리 직속).

**복사하지 않은 파일(이미지/대용량 — 경로만 기재)**

| 절대경로 | 설명 |
|---|---|
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/Figure1.png` | 현재 원고 참조 도식(사용자 수정 `Figure1_dbr.png`과 동일, md5 `c71d8d28…`) |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/Figure1-1.png` | 이전 변형(667,600 bytes, md5 `593d5dfc…`; "검색 중 조건 적용", "지역 색인" 등 현재 원고에 없는 항목 포함) |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260717_manuscript_visuals_v6/fig1_pipeline_noncircular_v6.png` (및 동명 `.pdf`) | 교체 전 matplotlib 초안(md5 `300b4f3e…`) |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260718_manuscript_content/media/rId30.png` | 07-18 조판본에 삽입됐던 동일 초안 사본(md5 `300b4f3e…`, 위와 동일) |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260717_manuscript_visuals_v6/fig1_system_architecture_v7.{png,svg,pdf}` | 현 스크립트 개정판이 생성하는 대안 초안 |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/presentations/kiise_vlmdb_deck_20260714.pptx` | 발표 덱(내장 미디어 4개 모두 그림 1과 불일치 — 원천 아님을 확인한 근거로 기재) |

## 7. 2026-07-23 최초 검증 기록(이력)

검증 방법: `verify_figure1.py`를 2026-07-23 17:57(KST)에 실행하여, 도식(그림 1 PNG를 직접 판독)에 인쇄된 모든 텍스트 요소를 원고 스냅숏(행 번호 포함)과 대조하고 파일 무결성을 확인했다. 그림 1에는 실험 수치가 없으므로 수치 재계산 대신 **요소별 정합 검증**이다.

**(A) 파일 무결성**

| ID | 항목 | 결과 |
|---|---|---|
| A1 | 캡션 문구가 원고에 존재 | PASS (행 94) |
| A2 | `./Figure1.png` 참조가 원고에 존재 | PASS (행 92) |
| A3 | Figure1.png 존재·md5 `06b2127ef4d48aaf8f8fa0d56bec4fbc`·285,312 bytes | PASS |
| A4 | Figure1-1.png(변형) 존재·md5 `593d5dfc90edb9e1d2a981c27656cb23` | PASS |
| A5 | 해상도 1482×695, 96 DPI | PASS(기록) |

**(B) 도식 텍스트 요소 ↔ 원고 정합 (28항목 전수)**

| ID | 도식 요소 | 결과(원고 근거 행) |
|---|---|---|
| T01–T03 | RQ1 박스(정답 조건 주입 / 정답 라벨 재진술 주입 / 생성 경로 분리) | PASS (행 100, 100, 98) |
| T04–T05 | RQ2 제목·5개 저장 방식 | PASS (행 118, 106) — 비고: 도식 "여러 이미지 벡터" = 원고 "다중 이미지"(표기 상이, 동일 개념) |
| T06–T07 | RQ3 제목·4개 검색 계획 | PASS (행 119, 107) |
| T08–T09 | RQ4 제목·신호 4종(메타데이터 단독/BM25/벡터/RRF) | PASS (행 120, 108) |
| T10–T12 | RQ5 제목·색인 4종·전역/부분 색인 | PASS (행 121, 109, 110) |
| T13–T14 | RQ6 박스(답변 효과 검증 / 모델·프롬프트 고정) | PASS (행 90·322, 324) — 비고: RQ 정의 목록(행 122)은 "답변 전파(RQ6)", §5.2.6 제목은 "답변 효과 검증"으로 도식과 일치 |
| T15–T17 | 정답 기준 3종(의미론적/엄격한/ANN=조건별 Flat 상위 10) | PASS (행 84, 84, 137–139·168) — "상위 10개"는 표 1 "조건별 Flat 상위 이웃"+Recall@10 규약과 정합 |
| T18–T22 | 평가 지표 5종(nDCG@10/재현율@10/p50·p95/구축 시간/저장 크기) | PASS (행 168) — 비고: 도식 "저장 크기"는 원고의 "float32 벡터 페이로드 또는 직렬화된 색인 크기"의 축약 |
| T23–T27 | 세 원천·조건 이원화(센서 시간·신호·교통량/위치/픽셀 설명문/사람 주석/의미·메타데이터 조건) | PASS (행 143, 84, 98, 98–99, 84) |
| T28 | 그림 도입문 존재 | PASS (행 90) |
| T29 | 사용자 질의 예시 "오전 10시경에 오토바이 2대…" | 해당 없음 — 원고 미출현이 정상인 **도식 전용 예시 문구**(수치 아님) |

**UNVERIFIED 항목(정직 기록)**

1. **편집 가능 원본 미확인**: `Figure1.png`/`Figure1-1.png`의 pptx·드로잉 원본이 저장소에 없다(저자 보관 추정). 저장소 내 어떤 파일과도 체크섬이 일치하지 않음을 전수 확인했다.
2. **도식 내 CCTV 썸네일 3장의 원본 클립 식별자 미확인**: AI Hub 교차로 CCTV 프레임 계열로 보이나 PNG에 병합되어 있어 추적 불가.
3. `Figure1-1.png`(구 변형)에는 현재 원고에 없는 "검색 중 조건 적용", "지역 색인" 항목이 남아 있다. **게재본(Figure1.png)에는 없으므로 원고와의 불일치는 아니며**, 구 변형을 재사용하지 말 것.

**총괄: 검증 가능한 33항목(A 5 + B 28) 전부 PASS. 불일치 0건. 미확인(UNVERIFIED)은 위 제작 원천 관련 3건.**


## 8. 2026-08-11 용어 통일 재생성

- 사용자 수정본 `Figure1_dbr.png`를 원고 용어 통일 정본과 다시 대조하고, 원고가 실제 참조하는 `manuscript/Figure1.png`로 채택했다.
- RQ1의 그림 내부 표현은 절차명 전체를 반복하지 않고 수행 항목인 `생성 원천 분리`로 표시한다. 본문에서는 정식 명칭을 `비순환 평가 작업 부하 구성 절차`로 통일하고, `세 원천 분리 프로토콜`은 사용하지 않는다.
- 세 원천, 의미·메타데이터 조건, RQ1–RQ6, 상위 k개 검색 결과, 정답 기준, 검색 품질·비용 지표의 명칭과 화살표 흐름을 전수 점검했다. 현재 구조는 원천 분리·순환성 진단 → 벡터 데이터베이스 계층 설계 → 상위 검색 결과 → 답변 전파 진단·최종 답변의 주 흐름과 검색 품질·비용 평가의 분기 흐름을 구분한다.
- `patch_figure1_terms_20260809.py`에는 이전 명칭의 재유입을 막기 위해 RQ1 항목을 `생성 원천 분리`로 갱신했지만, 현행 최종본의 재생성 원본은 사용자 편집 파일 `Figure1_dbr.png`이다.
- 직전 원고 참조본은 `Figure1_pre_dbr_20260811.png`로 보존했다.
- 현행 `manuscript/Figure1.png`: md5 `c71d8d28444a1ed51fa18d75e03d824f`, 2451×1147, 약 144 DPI.
