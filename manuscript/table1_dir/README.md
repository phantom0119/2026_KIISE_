# 표 1 관리 디렉터리 (table1_dir)

작성일: 2026-07-23. 이 디렉터리는 원고 표 1(데이터셋 요약)의 모든 인쇄 수치를 원천 파일과 1:1로 연결하고, `data/` 사본만으로 재검증할 수 있게 만든 자기완결 패키지다.

## 1. 대상

- **Caption 원문(현재 원고 기준)**: `**<표 1> 주 평가 데이터와 목적별 보완 데이터의 구성 및 실험 역할**`
- **원고 파일**: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/0_main_paper.md`
- **원고 내 위치**: 표 본문 255–265행, 캡션 267행 (2026-08-13 개정판 기준)
- **소속 절/RQ**: §5.1.1 데이터셋 (실험 설정). 표 자체는 특정 RQ의 결과가 아니라 RQ1–RQ6 전체가 사용하는 8개 데이터셋·9개 실험 트랙의 규모와 역할을 요약한다. AI Hub 교차로는 검색 트랙(RQ1–RQ4)과 이미지 색인 트랙(RQ5·RQ6)으로 구분한다. 나머지 행은 VRU=RQ1·RQ6, 지능형 관제 CCTV=RQ1, MEVA=RQ2, UCA=RQ2·RQ3, 시내도로 이미지=RQ5, MIRIS=RQ5, 다각도 CCTV=RQ6에 대응한다.

## 2. 수치 ↔ 원천 매핑

표 1에 인쇄된 수치 22개 전부. "사본 경로"는 이 디렉터리의 `data/` 기준 상대경로.

| 행 | 인쇄 수치 | 원천 파일(사본 경로) | 파일 내 위치(행/컬럼/키) |
|---|---|---|---|
| AI Hub 교차로 검색 | 클립·설명문 각 3,000개 | `data/aihub_522_intersection/documents.parquet` | parquet 행 수 = 3,000, `clip_id` 고유값 수 = 3,000 |
| AI Hub 교차로 | 질의 85개 | `data/aihub_522_intersection/queries.jsonl` | JSONL 줄 수 = 85 |
| VRU-Accident | 설명문 1,000개 | `data/vru_accident_noncircular/documents.parquet` | parquet 행 수 = 1,000 (재구성본 v2) |
| VRU-Accident | 질의 85개 | `data/vru_accident_noncircular/queries.jsonl` | JSONL 줄 수 = 85 (재구성본 v2) |
| VRU-Accident | 답변 문항 600개 | `data/vru_rag_vqa/summary_qwen.json`, `summary_llama3.json` | 키 `n_per_config` = 600; 교차: `rag_vqa_qwen.parquet`·`rag_vqa_llama3.parquet` 각 3,000행 = 600문항×5조건, 6범주×각 100문항 균형 |
| 지능형 관제 CCTV | 설명문 269개 | `data/aihub_intelligent_cctv_noncircular/documents.parquet` | parquet 행 수 = 269 (재구성본 v2) |
| 지능형 관제 CCTV | 질의 18개 | `data/aihub_intelligent_cctv_noncircular/queries.jsonl` | JSONL 줄 수 = 18 (재구성본 v2) |
| MEVA | 클립 985개 | `data/meva_kf1/clips.parquet` | parquet 행 수 = 985 |
| MEVA | 질의 193개 | `data/meva_kf1/queries.jsonl` | JSONL 줄 수 = 193 |
| UCA/UCF-Crime | 세그먼트 6,432개 | `data/uca_anchor/clips.parquet` | parquet 행 수 = 6,432 |
| UCA/UCF-Crime | 질의 135개 | `data/uca_anchor/queries.jsonl` | JSONL 줄 수 = 135 |
| UCA/UCF-Crime | 분석 129개 | `data/uca_external/UCA_contrasts.json` | 키 `c1_strict_pooled_positive.detail.n` = 129, `c3_negative_semantic_signs_exist.n_semantic` = 129 (전체 135 − 정상영상 조건 5 − 퇴화 1) |
| 시내도로 이미지 | 벡터 132,521개 | `data/pillarB_predicates/P1_manifest.json` | 키 `corpusA.n_frames` = 132521; 교차: `data/_measurements_20260723.json`의 npy 헤더 실측 (132521, 512) |
| 시내도로 이미지 | 512차원 | `data/_measurements_20260723.json` | 캐노니컬 npy 헤더 실측 shape (132521, **512**) |
| 시내도로 이미지 | 실측 조건 29건 | `data/pillarB_predicates/P1_predicates_A.csv` | 데이터 행 수 = 29 (corpus=A_sinnaedoro, natural+composite) |
| AI Hub 교차로 이미지 | 벡터 143,830개 | `data/pillarB_predicates/P1_manifest.json` | 키 `corpusB.n_frames` = 143830; 교차: `data/_measurements_20260723.json`의 npy 헤더 실측 (143830, 512) |
| AI Hub 교차로 이미지 | 512차원 | `data/_measurements_20260723.json` | 캐노니컬 npy 헤더 실측 shape (143830, **512**) |
| AI Hub 교차로 이미지 | 실측 조건 25건 | `data/pillarB_predicates/P1_predicates_B.csv` | `kind != meta` 행 수 = 25 (natural 22 + composite 3; `(joined frames)` meta 행 1개는 조건이 아니라 조인 모집단 정의라 제외) |
| MIRIS | 벡터 59,019개 | `data/miris/pgvector_partial_manifest_miris2.json` | 키 `table` = "miris_frames2 (**59019** x 512, ...)" |
| MIRIS | 512차원 | `data/miris/pgvector_partial_manifest_miris2.json` | 키 `table` = "miris_frames2 (59019 x **512**, ...)" |
| 다각도 CCTV | 400사건 | `data/multi_angle/stratum_manifest.csv` | CSV 데이터 행 수 = 400 |
| 다각도 CCTV | 주 분석 250개 | `data/multi_angle/stratum_manifest.csv` | `stratum` 컬럼 == `asymmetric` 행 수 = 250 (symmetric 150) |

## 3. 사용 데이터셋

캐노니컬 루트: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/` (symlink → `/hdd2/KIISE_datasociety/Datasets/processed/`).

| 데이터셋 | 원본(이름·규모·경로) | 가공 산출물(캐노니컬 경로) | 전처리 요약 |
|---|---|---|---|
| AI Hub 교차로(522) | AI Hub 522 교차로 신호체계, 원본 archive 198G, `Datasets/external/교차로신호체계` | `Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded/` | 센서 CSV 32,880클립·시각 52,462클립을 ±120초 조인(47,098) 후 교차로×시간대 층화·시드 20260710으로 3,000클립 표집, 중간 프레임을 Qwen2.5-VL-7B 픽셀-only 캡션화 |
| VRU-Accident(재구성본) | VRU-Accident 영상 1,000개+HF 배포(dense caption 1,000·VQA 6,000), `Datasets/raw/VRU-Accident`·`Datasets/external/VRU-Accident_hf` | `Datasets/processed/vru_accident/20260710_noncircular/canonical/` | v1(문서 7,000·질의 244)에서 정답 유래 템플릿 문서를 제거하고 외부 dense caption 1,000개만 남긴 뒤 문서·조건·정답 필드 축 분리, 질의 85개 재구성 |
| 지능형 관제 CCTV(재구성본) | AI Hub 지능형관제 CCTV 13G에서 MP4/JSON 269쌍 선별, `Datasets/external/지능형관제서비스CCTV영상데이터` | `Datasets/processed/aihub_intelligent_cctv/20260710_noncircular/canonical/` | v1(문서 807·질의 133)에서 사건 라벨 템플릿 문서 제거, 외부 JSON `event_caption` 269개만 유지, 질의 18개 재구성 |
| MEVA | MEVA 주석 repo 7.6G(`Datasets/external/meva`) + 원격 S3 AVI(로컬 미보존) | `Datasets/processed/meva_kf1/20260713/canonical_trisource/` | KPF/DIVA 활동주석→정답, 촬영 위치·시각→조건, 중간 프레임의 Qwen2.5-VL 캡션→문서로 985클립·193질의 구성 |
| UCA/UCF-Crime | UCF-Crime 영상 194G + UCA 문장 주석(`Datasets/external/UCA_surveillance`) | `Datasets/processed/uca_anchor/20260712/canonical/` | 주석 사건 구간에서 video당 최대 4구간 등간 표집으로 6,432 세그먼트 프레임 추출, 픽셀-only 캡션 생성, 질의 135개(분석 129개) |
| 시내도로 이미지 | AI Hub 시내도로 CCTV JPG ZIP 320G, `Datasets/external/교통문제 해결을 위한 CCTV 교통 영상(시내도로)` | `Datasets/processed/sinnaedoro_traffic/corpus_real/` (`frame_embeddings.npy` 132,521×512) | ZIP 내부에서 위치·카메라·시간 분산 표집한 프레임을 CLIP ViT-B/32로 임베딩, 실측 predicate 29건 목록화 |
| AI Hub 교차로 이미지 | 위 522 원본의 주 트랙 JPG 143,830장 | `Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip/frame_embeddings.npy` (143,830×512) | 주 트랙 전 프레임 CLIP ViT-B/32 임베딩, 조인 센서 조건 25건 목록화 |
| MIRIS | MIRIS traffic 14G 중 Warsaw·Shibuya 12영상, `Datasets/external/miris` | PostgreSQL 표 `miris_frames2` 59,019행(+hold-out 질의 1,000×512는 `Datasets/processed/miris_traffic/20260713/`) | 6프레임 stride로 60,019프레임 CLIP 임베딩 후 1,000개를 질의로 유보, 59,019개를 pgvector에 적재 |
| 다각도 CCTV | AI Hub 다각도 CCTV 483G(4,500사건, 시점 c1/c2), `Datasets/external/21.다각도 CCTV 생활안전 데이터` | `Datasets/processed/aihub_multi_angle_cctv/20260708/samples/bbox_asymmetry_stratum/` | 경계 상자 면적 기반 시점 비대칭으로 400사건 표집(비대칭 층 250 + 대칭 150), 시점별 evidence 프레임 추출 |

## 4. 실험 체계

표 1은 결과 수치가 아니라 워크로드 규모의 선언이므로, "실험 체계"는 각 규모를 만든 구축 스크립트와 그 규모를 소비한 실험 스크립트를 뜻한다. 스크립트 루트: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/`.

- **522 검색 트랙**: `build_visual_sensor_join.py`(±120초 조인) → `build_intersection_captions.py`(Qwen2.5-VL-7B-Instruct snapshot `cc594898`, greedy, max 110 tokens, 표집 시드 20260710) → `build_intersection_trisource_canonical.py`(3,000문서·85질의). 임베딩 BGE-M3 1,024차원.
- **522 색인 트랙**: `build_intersection_frame_clip.py` — 주 트랙 143,830프레임 CLIP ViT-B/32 512차원.
- **VRU 재구성본**: `build_vru_noncircular_canonical.py`. 답변 600문항: `run_rag_vqa.py` — VQA 6,000문항(`data/vru_rag_vqa/vqa_joined.parquet`)에서 시드 **20260707**(스크립트 default), 6범주×100문항 균형 표집, 5개 증거 조건(closed/distractor/vector_only/prefilter/oracle), 생성 모델 Qwen2.5-7B-Instruct·Llama-3-8B-Instruct, 탐욕적 디코딩, 선택지 정확 일치 채점.
- **지능형 관제 CCTV 재구성본**: `build_aihub_cctv_noncircular_canonical.py`.
- **MEVA**: `build_meva_facets.py` → `build_meva_captions.py` → `build_meva_trisource_canonical.py`.
- **UCA**: `build_uca_corpus.py` → `caption_uca.py` → `analyze_uca_external.py`(분석 129질의 계약).
- **시내도로·522 이미지(RQ5)**: `build_sinnaedoro_visual.py`, `build_p1_predicate_tables.py`(조건 29/25건 동결, [AMD-B1] 2026-07-10 locked), `run_filtered_ann_real_predicate.py`, `run_filtered_ann_benchmark.py`.
- **MIRIS**: `build_miris_pgvector_rich.py`(6-stride, video당 최대 5,200), `run_pgvector_partial_index.py`. PostgreSQL 16/pgvector 0.8.4 :5433.
- **다각도 CCTV**: `build_bbox_asymmetry_stratum.py`(400사건·비대칭 250), `run_multiview_answer_vlm.py`(Qwen2.5-VL·Qwen2-VL·InternVL3-8B·Idefics2-8b, greedy, max_new_tokens 256).
- **사전등록/결과 문서**(`/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/`): `500_DATASETS_construction_noncircular_execution_20260710.md`(비순환 구축), `420_METHOD_prereg_pillarBE_design_20260710.md`(RQ5·RQ6 사전등록), `680_DATASET_foundation_audit_20260713.md`(데이터 기반 감사), `790_DATASET_TABLES_for_Notion_20260714.md`(데이터셋 구성표), `DATA_PROVENANCE_raw_vs_derived_20260715.md`(계보 정본, §6 규모표), `640_RESULTS_uca_external_20260712.md`(UCA 129 분석), `910_REVIEW_response_and_supplementary_design_20260723.md`(RQ6 600문항×5조건×2 LLM 확정 기록).

## 5. 재현 방법

### (a) data/ 사본만으로 표 1 수치 재집계 (최소 경로)

이 디렉터리에서 실행. pandas만 필요하다.

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/table1_dir
python3 - <<'EOF'
import pandas as pd, json
D="data"
print("522:", len(pd.read_parquet(f"{D}/aihub_522_intersection/documents.parquet")), "문서,",
      sum(1 for _ in open(f"{D}/aihub_522_intersection/queries.jsonl")), "질의")
print("VRU:", len(pd.read_parquet(f"{D}/vru_accident_noncircular/documents.parquet")), "문서,",
      sum(1 for _ in open(f"{D}/vru_accident_noncircular/queries.jsonl")), "질의,",
      json.load(open(f"{D}/vru_rag_vqa/summary_qwen.json"))["n_per_config"], "답변 문항")
print("CCTV:", len(pd.read_parquet(f"{D}/aihub_intelligent_cctv_noncircular/documents.parquet")), "문서,",
      sum(1 for _ in open(f"{D}/aihub_intelligent_cctv_noncircular/queries.jsonl")), "질의")
print("MEVA:", len(pd.read_parquet(f"{D}/meva_kf1/clips.parquet")), "클립,",
      sum(1 for _ in open(f"{D}/meva_kf1/queries.jsonl")), "질의")
print("UCA:", len(pd.read_parquet(f"{D}/uca_anchor/clips.parquet")), "세그먼트,",
      sum(1 for _ in open(f"{D}/uca_anchor/queries.jsonl")), "질의,",
      json.load(open(f"{D}/uca_external/UCA_contrasts.json"))["c1_strict_pooled_positive"]["detail"]["n"], "분석")
pm=json.load(open(f"{D}/pillarB_predicates/P1_manifest.json"))
pa=pd.read_csv(f"{D}/pillarB_predicates/P1_predicates_A.csv"); pb=pd.read_csv(f"{D}/pillarB_predicates/P1_predicates_B.csv")
print("시내도로:", pm["corpusA"]["n_frames"], "벡터,", len(pa), "조건")
print("522이미지:", pm["corpusB"]["n_frames"], "벡터,", len(pb[pb['kind']!='meta']), "조건")
print("MIRIS:", json.load(open(f"{D}/miris/pgvector_partial_manifest_miris2.json"))["table"])
sm=pd.read_csv(f"{D}/multi_angle/stratum_manifest.csv")
print("다각도:", len(sm), "사건, 주 분석", int((sm['stratum']=='asymmetric').sum()))
EOF
```

### (b) 원천 재실행 경로 (처음부터)

repo 루트 `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/`에서, 원본 archive(§3의 external 경로)가 마운트된 상태를 전제로:

1. **522**: `scripts/extract_intersection_visual_sources.py` → `build_intersection_signal_sensors.py` → `build_intersection_annotation_facets.py` → `build_visual_sensor_join.py` → `build_intersection_captions.py`(시드 20260710) → `build_intersection_trisource_canonical.py` ⇒ 3,000문서·85질의. `build_intersection_frame_clip.py` ⇒ 143,830×512 npy.
2. **VRU**: `build_vru_noncircular_canonical.py` ⇒ 1,000문서·85질의. `run_rag_vqa.py --seed 20260707` ⇒ 600문항×5조건×2모델 결과(`experiments_expansion/rag_vqa/results_full/`).
3. **지능형 관제 CCTV**: `build_aihub_cctv_noncircular_canonical.py` ⇒ 269문서·18질의.
4. **MEVA**: `build_meva_facets.py` → `build_meva_captions.py` → `build_meva_trisource_canonical.py` ⇒ 985클립·193질의 (원 AVI는 S3 재다운로드 필요).
5. **UCA**: `build_uca_corpus.py` → `caption_uca.py` ⇒ 6,432세그먼트·135질의; `analyze_uca_external.py` ⇒ 분석 129질의(`paper_assets/20260712_uca_external/UCA_contrasts.json`).
6. **시내도로**: `build_sinnaedoro_visual.py` ⇒ 132,521×512 npy; `build_p1_predicate_tables.py` ⇒ 조건 29/25건(`paper_assets/20260710_pillarB/P1_predicates_{A,B}.csv`).
7. **MIRIS**: `build_miris_pgvector_rich.py` ⇒ pgvector `miris_frames2` 59,019행; `run_pgvector_partial_index.py` ⇒ manifest.
8. **다각도**: `build_aihub_multi_angle_cctv_canonical.py` → `build_bbox_asymmetry_stratum.py` ⇒ 400사건(비대칭 250).
9. 산출된 규모를 (a)와 같은 방식으로 집계해 표 1의 마크다운 행을 작성한다.

## 6. 포함 파일 목록

`data/` 사본 (원 절대경로 → 사본명):

| 원 절대경로 | 사본 | 설명 |
|---|---|---|
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded/documents.parquet` | `data/aihub_522_intersection/documents.parquet` | 522 검색 문서 3,000행(Qwen2.5-VL 캡션) |
| `.../aihub_522_intersection/20260710/canonical_trisource_expanded/queries.jsonl` | `data/aihub_522_intersection/queries.jsonl` | 522 질의 85건 |
| `.../vru_accident/20260710_noncircular/canonical/documents.parquet` | `data/vru_accident_noncircular/documents.parquet` | VRU 재구성본 문서 1,000행 |
| `.../vru_accident/20260710_noncircular/canonical/queries.jsonl` | `data/vru_accident_noncircular/queries.jsonl` | VRU 재구성본 질의 85건 |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/experiments_expansion/rag_vqa/results_full/summary_qwen.json` | `data/vru_rag_vqa/summary_qwen.json` | RAG-VQA Qwen 요약(n_per_config=600) |
| `.../experiments_expansion/rag_vqa/results_full/summary_llama3.json` | `data/vru_rag_vqa/summary_llama3.json` | RAG-VQA Llama-3 요약(n_per_config=600) |
| `.../experiments_expansion/rag_vqa/results_full/rag_vqa_qwen.parquet` | `data/vru_rag_vqa/rag_vqa_qwen.parquet` | 문항 단위 결과 3,000행(600×5조건) |
| `.../experiments_expansion/rag_vqa/results_full/rag_vqa_llama3.parquet` | `data/vru_rag_vqa/rag_vqa_llama3.parquet` | 문항 단위 결과 3,000행(600×5조건) |
| `.../experiments_expansion/rag_vqa/vqa_joined.parquet` | `data/vru_rag_vqa/vqa_joined.parquet` | 표집 전 VQA 모집단 6,000문항 |
| `.../aihub_intelligent_cctv/20260710_noncircular/canonical/documents.parquet` | `data/aihub_intelligent_cctv_noncircular/documents.parquet` | 지능형 관제 CCTV 재구성본 문서 269행 |
| `.../aihub_intelligent_cctv/20260710_noncircular/canonical/queries.jsonl` | `data/aihub_intelligent_cctv_noncircular/queries.jsonl` | 지능형 관제 CCTV 재구성본 질의 18건 |
| `.../meva_kf1/20260713/canonical_trisource/clips.parquet` | `data/meva_kf1/clips.parquet` | MEVA 클립 985행 |
| `.../meva_kf1/20260713/canonical_trisource/queries.jsonl` | `data/meva_kf1/queries.jsonl` | MEVA 질의 193건 |
| `.../uca_anchor/20260712/canonical/clips.parquet` | `data/uca_anchor/clips.parquet` | UCA 세그먼트 6,432행 |
| `.../uca_anchor/20260712/canonical/queries.jsonl` | `data/uca_anchor/queries.jsonl` | UCA 질의 135건 |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260712_uca_external/UCA_contrasts.json` | `data/uca_external/UCA_contrasts.json` | UCA 대조 분석(n=129) |
| `.../paper_assets/20260710_pillarB/P1_predicates_A.csv` | `data/pillarB_predicates/P1_predicates_A.csv` | 시내도로 실측 조건 29건 목록 |
| `.../paper_assets/20260710_pillarB/P1_predicates_B.csv` | `data/pillarB_predicates/P1_predicates_B.csv` | 522 이미지 실측 조건 목록(meta 1행 + 조건 25행) |
| `.../paper_assets/20260710_pillarB/P1_manifest.json` | `data/pillarB_predicates/P1_manifest.json` | 코퍼스 A/B 프레임 수·선택도 범위 동결 manifest |
| `.../paper_assets/20260713_db_design/pgvector_partial_manifest_miris2.json` | `data/miris/pgvector_partial_manifest_miris2.json` | MIRIS pgvector 표 명세(59019×512) |
| `.../paper_assets/20260713_db_design/pgvector_partial_vs_global_miris2.csv` | `data/miris/pgvector_partial_vs_global_miris2.csv` | MIRIS 부분/전역 색인 결과(59,019행 표 대상) |
| `.../aihub_multi_angle_cctv/20260708/samples/bbox_asymmetry_stratum/stratum_manifest.csv` | `data/multi_angle/stratum_manifest.csv` | 다각도 400사건 표본(비대칭 250·대칭 150) |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/_archive_20260819/freeze_validation_20260707.md` | `data/docs/freeze_validation_20260707.md` | v1 규모 동결 검증(137 체크; VRU 244질의·7,000문서, CCTV 133질의·807문서 등 **정답 정보 재사용 제거 전** 기준 — 표 3 각주의 대조 근거) |
| `.../project_md/DATA_PROVENANCE_raw_vs_derived_20260715.md` | `data/docs/DATA_PROVENANCE_raw_vs_derived_20260715.md` | 데이터 계보 정본(§6 규모표가 표 1과 대응) |
| `.../project_md/790_DATASET_TABLES_for_Notion_20260714.md` | `data/docs/790_DATASET_TABLES_for_Notion_20260714.md` | 데이터셋별 파일 구성표 |
| `.../project_md/680_DATASET_foundation_audit_20260713.md` | `data/docs/680_DATASET_foundation_audit_20260713.md` | 데이터 기반 감사 |
| (본 검증에서 생성) | `data/_measurements_20260723.json` | 대용량 npy 헤더 실측 기록(132,521×512·143,830×512)과 MIRIS DB 미재계수 사유 |

복사하지 않은 대용량 파일(경로 참조만, 읽기 전용 실측 완료):

- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/frame_embeddings.npy` — 실측 shape (132521, 512), float32 약 271MB
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip/frame_embeddings.npy` — 실측 shape (143830, 512), float32 약 294MB
- PostgreSQL `miris_frames2` (포트 5433, 데이터 volume `Datasets/services/postgres_pgvector`) — 벡터 본체는 파일이 아니라 DB 표에만 존재
- 원본 archive 일체(`Datasets/external/...`, `Datasets/raw/...`; §3 표 참조) — 이미지·영상·zip이므로 복사 금지 대상

## 7. 검증

2026-07-23, `data/` 사본을 python3(pandas)로 실제 재조회한 결과. 판정 기준: 원고 인쇄 수치 == 사본 재계수.

| # | 행 | 원고 수치 | 사본 재계수 | 판정 |
|---|---|---:|---:|---|
| 1 | AI Hub 교차로 설명문 | 3,000 | 3,000 (`documents.parquet` 행 수) | PASS |
| 2 | AI Hub 교차로 질의 | 85 | 85 (`queries.jsonl` 줄 수) | PASS |
| 3 | VRU 설명문 | 1,000 | 1,000 | PASS |
| 4 | VRU 질의 | 85 | 85 | PASS |
| 5 | VRU 답변 문항 | 600 | 600 (`summary_qwen.json`·`summary_llama3.json` n_per_config; parquet 3,000행=600×5조건, 6범주×100 균형; 모집단 `vqa_joined.parquet` 6,000행) | PASS |
| 6 | 지능형 관제 CCTV 설명문 | 269 | 269 | PASS |
| 7 | 지능형 관제 CCTV 질의 | 18 | 18 | PASS |
| 8 | MEVA 클립 | 985 | 985 | PASS |
| 9 | MEVA 질의 | 193 | 193 | PASS |
| 10 | UCA 세그먼트 | 6,432 | 6,432 | PASS |
| 11 | UCA 질의 | 135 | 135 | PASS |
| 12 | UCA 분석 | 129 | 129 (`UCA_contrasts.json` 두 키 일치) | PASS |
| 13 | 시내도로 벡터 | 132,521 | 132,521 (P1_manifest `corpusA.n_frames`; 캐노니컬 npy 헤더 실측 (132521, 512) 일치) | PASS |
| 14 | 시내도로 차원 | 512 | 512 (캐노니컬 npy 헤더 실측; `data/` 사본 중에는 `_measurements_20260723.json`에 기록) | PASS |
| 15 | 시내도로 실측 조건 | 29 | 29 (`P1_predicates_A.csv` 데이터 행) | PASS |
| 16 | AI Hub 교차로 이미지 벡터 | 143,830 | 143,830 (P1_manifest `corpusB.n_frames`; npy 헤더 실측 일치) | PASS |
| 17 | AI Hub 교차로 이미지 차원 | 512 | 512 (npy 헤더 실측) | PASS |
| 18 | AI Hub 교차로 이미지 실측 조건 | 25 | 25 (`P1_predicates_B.csv`에서 kind≠meta 행; meta `(joined frames)` 1행 제외 규칙 적용) | PASS |
| 19 | MIRIS 벡터 | 59,019 | 59,019 (manifest `table` 문자열 "59019 x 512"; **DB 직접 count(*)는 psql 클라이언트 부재로 이번에 미수행** — DATA_PROVENANCE 5.4절의 2026-07-15 실측 59,019행 기록으로 교차 확인) | PASS(manifest 근거) |
| 20 | MIRIS 차원 | 512 | 512 (같은 manifest) | PASS(manifest 근거) |
| 21 | 다각도 사건 | 400 | 400 (`stratum_manifest.csv` 행 수) | PASS |
| 22 | 다각도 주 분석 | 250 | 250 (`stratum`==asymmetric 행 수; symmetric 150) | PASS |

**종합: 22/22 PASS. UNVERIFIED 없음.** 다만 #19–20은 디스크 파일 재계수가 아니라 동결 manifest·계보 문서 기록에 근거한 판정이고(벡터 본체가 PostgreSQL 서비스 상태에만 존재), #14·#17의 512차원은 대용량 npy를 복사하지 않았으므로 `data/` 사본 내부에서는 `_measurements_20260723.json`의 실측 기록으로만 재확인된다는 근거 수준 차이를 명시한다.

참고: `data/docs/freeze_validation_20260707.md`는 **v1(정답 정보 재사용 제거 전)** 규모(VRU 질의 244·문서 7,000, CCTV 질의 133·문서 807)를 동결한 문서다. 표 1은 재구성본(v2) 규모(85·1,000 / 18·269)를 인쇄하므로 이 문서와의 차이는 불일치가 아니라 원고 표 3의 정답 정보 재사용 제거 전후 비교에 서술된 의도된 변경이다.
