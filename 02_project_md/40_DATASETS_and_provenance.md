# 40 — 데이터셋 정본과 계보 (DATASETS and Provenance) 통합 정리본

## 0. 머리말

이 문서는 본 연구(2026 KIISE DBR 제출)의 **사용 데이터 목록·규모·역할·계보(raw/파생)·비순환 구축 절차**에 관한 단일 정본으로, 기존 데이터셋 관련 문서 7종을 통합·정정한 것이다.

**통합 출처** (원본은 아래 아카이브 경로로 이관):

| # | 원본 문서 | 아카이브 경로 |
|---|---|---|
| S1 | 000_Datasets.md (2026-07-15, 종합 명세) | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/000_Datasets.md` |
| S2 | 500_DATASETS_construction_noncircular_execution_20260710.md (비순환 구축 실행 로그) | `.../archive/legacy_premerge_20260728/500_DATASETS_construction_noncircular_execution_20260710.md` |
| S3 | 680_DATASET_foundation_audit_20260713.md (기반 전면 재점검) | `.../archive/legacy_premerge_20260728/680_DATASET_foundation_audit_20260713.md` |
| S4 | 690_DATASET_overseas_verify_extend_20260713.md (해외 검증·확장 조사) | `.../archive/legacy_premerge_20260728/690_DATASET_overseas_verify_extend_20260713.md` |
| S5 | 730_DATASET_landscape_expanded_20260713.md (확장 landscape) | `.../archive/legacy_premerge_20260728/730_DATASET_landscape_expanded_20260713.md` |
| S6 | 790_DATASET_TABLES_for_Notion_20260714.md (파일 구성표) | `.../archive/legacy_premerge_20260728/790_DATASET_TABLES_for_Notion_20260714.md` |
| S7 | DATA_PROVENANCE_raw_vs_derived_20260715.md (계보 정본 후보) | `.../archive/legacy_premerge_20260728/DATA_PROVENANCE_raw_vs_derived_20260715.md` |

**SYNC 기준: paper_final.pdf(2026-07-23 제출본, `manuscript/paper_final.pdf`, 총 21쪽=접수양식 1쪽+본문) + 2026-07-28 검증 세션.** 수치·해석이 출처 문서와 상충하면 논문 정본을 우선하고, 의미 있는 이력은 `[정정 2026-07-28: ...]` 형태로 남긴다. 확정 제목(국문): "종단형 멀티모달 RAG 파이프라인 성능 향상을 위한 비순환 평가 및 검색 품질-비용에 대한 실증 연구" (영문: An Empirical Study of Non-circular Evaluation and Retrieval Quality-Cost for Enhancing the Performance of End-to-End Multimodal RAG Pipeline).

---

# 제1부. 현행 정리

## 1. 데이터셋 총괄 — 실사용 8종 + 제외 2종, 논문 표 1 대응

"본 연구에서 사용"의 판정 기준(S7): **제출 원고의 표·수치·그림 또는 답변 실험에 실제로 소비된 경우만** 사용으로 센다. 단순 다운로드, canonical 구축, 과거 v1 결과 생성만으로는 세지 않는다. 이 기준으로 **실사용 8종(데이터셋 패키지 기준), 제외 2종**이다.

논문 표 1은 AI Hub 522 패키지의 두 트랙을 별도 행으로 표기한다: **"AI Hub 교차로"(주평가, 검색 트랙)** 와 **"AI Hub 교차로 이미지"(보완, 색인 트랙)**. 따라서 패키지 기준 8종 = 논문 표 1 기준 9행(주평가 1 + 보완 8: VRU/지능형관제/MEVA/UCA/시내도로/AIHub교차로이미지/MIRIS/다각도)이다.

| 논문 표 1 표기 | 내부 명칭 / 정본 경로 | 역할(논문 기준) | 규모 정본 |
|---|---|---|---|
| **AI Hub 교차로 (주평가)** | 522 검색 트랙 / `Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded/` | 비순환 tri-source 주평가 워크로드 (RQ1–RQ4) | **3,000 clips / 85 queries / strict qrels 6,809 / semantic qrels 24,872** |
| AI Hub 교차로 이미지 (보완) | 522 색인 트랙 / `visual_embeddings_clip/` | 물리 색인·배포 실험 (RQ5) | 143,830 frames, CLIP ViT-B/32 512d |
| VRU (보완) | VRU-Accident 수리판 / `Datasets/processed/vru_accident/20260710_noncircular/` | 순환 붕괴 대조(RQ1), 답변 사다리(RQ6) | 1,000 docs / 85 q / 3,744 / 9,703 |
| 지능형관제 (보완) | AI Hub 지능형 관제 CCTV 수리판 / `Datasets/processed/aihub_intelligent_cctv/20260710_noncircular/` | 순환 붕괴 대조(RQ1), 국내 이식성 | 269 docs / 18 q / 584 / 827 |
| MEVA (보완) | `Datasets/processed/meva_kf1/20260713/` | 해외 CCTV 외적 타당성 | 985 clips / 193 q / 4,405 / 17,205 |
| UCA (보완) | `Datasets/processed/uca_anchor/20260712/` | 영어 이상행동 외적 타당성 | 6,432 docs / 135 q(canonical) / 7,709 / 41,435 — 논문 RQ3 재현 보고는 **129질의, 3/4 재현** |
| 시내도로 (보완) | sinnaedoro / `Datasets/processed/sinnaedoro_traffic/` | filtered-ANN·색인·배포 (RQ5) | real 132,521 frames + synthetic 1,000,000 vectors, query 1,000 |
| MIRIS (보완) | `Datasets/processed/miris_traffic/20260713/` + PostgreSQL `miris_frames2` | 부분 색인·hot/cold 정책 교차검증 (RQ5) | DB 59,019 rows + hold-out query 1,000 |
| 다각도 (보완) | AI Hub 다각도 CCTV / `Datasets/processed/aihub_multi_angle_cctv/20260708/` | 다중 시점 검색 문맥 선택·VLM 답변 (RQ6) | 4,500 events (답변 표본 400 events, 2,400 frames) |

**제외 2종** (구축물은 존재하나 결과 미소비 — 확보 목록에는 남기되 결과 데이터셋 수에 포함 금지):

| 데이터셋 | 현재 상태 | 제외 이유 |
|---|---|---|
| CityFlow-NL | `processed/cityflow_nl` 4.2M, annotation staging만 존재 | 프레임 0장, 다운스트림 소비자 0, 현재 qrels/A6 없음 (+ 결정론적 순환 구조: 모든 질의 gold=동일 track UUID) |
| AI Hub 이상행동 CCTV | 외부 archive 573G, processed 71M, 과거 B0–B5 결과 존재 | 원고가 결과를 소비하지 않으며 역할이 UCA로 대체됨. label XML 단일 계보로 tri-source 아님 |

**코퍼스 정본 수치와 `wc -l` 헤더 주의사항.** 주평가 코퍼스 정본은 **3,000 / 85 / 6,809 / 24,872**다. 이 수치는 **헤더를 제외한 데이터 행 수** 기준이다. `qrels.tsv`·`qrels_semantic.tsv` 등 TSV/CSV를 `wc -l`로 실측하면 헤더 1행이 포함되어 정본보다 1 크게 나올 수 있다(예: strict qrels `wc -l` 6,810 = 헤더 1 + 데이터 6,809). 검증·감사 시 반드시 헤더 여부를 확인하고 데이터 행 수로 대조한다.

## 2. 2026-07-28 확정 용어·조작적 정의 (현 제출 PDF 미적용 — 보고서·향후 개정 원고용)

아래 결정은 전량 보존한다(요약 금지).

- **'데이터베이스 계층' → '벡터 데이터베이스 계층'** 으로 전면 개칭.
- **'증거' 전면 치환**: DB 반환 = **상위 k 검색 결과**, VLM 입력 = **검색 문맥(retrieved context)**, 정답 판정 = **관련 클립/검색 정답 집합**. RQ6 3관문 = **'관련 클립 회수 → 검색 문맥 인식 → 과제 편향'**.
- **클립 조작적 정의**: 데이터셋 배포 **mp4 1파일 = 1클립** (MEVA[20] 계보로 방어; TTA 사전 미등재·AI Hub 공식 페이지는 '영상(mp4)' 표기임에 유의).
  - 주의(실측 정합): 522의 로컬 시각 원천은 mp4가 아니라 **사전 추출 JPG archive**다(§5.1). 클립 정의는 AI Hub 공식 배포 표기('영상(mp4)') 기준이므로, 522에서는 "배포 영상 1편(video_id) = 1클립"으로 읽는다.
- **러닝 헤드 p.7 이후 구제목 잔존** → 재제출/개정 시 수정 필요.

## 3. 멀티모달 강도·비순환성 수준 분류

### 3.1 강도 사다리

```
[완전한 Tri-Source (물리 3채널 분리)]      ← AI Hub 522
[외부 검증용 멀티모달 (소스 결합)]          ← MEVA
[2.5채널 멀티모달 (센서 없음)]             ← UCA
[검색/답변 보조 멀티모달]                  ← VRU-Accident, 지능형 CCTV, 다각도 CCTV
[색인/DB 검증용 코퍼스]                    ← MIRIS, Sinnaedoro
[보류/과거 baseline]                      ← 이상행동 CCTV (제외), CityFlow-NL (제외)
```

1. **완전한 핵심 멀티모달 tri-source (522)**: 필터(Predicate)=센서 기록 CSV(카메라 10), 정답(Relevance)=사람 CVAT 주석 XML(카메라 11/22), 검색 문서(Document)=VLM(Qwen2.5-VL)이 픽셀만 보고 생성한 캡션 — 세 채널이 물리적·생산 경로 수준에서 격리.
2. **외부 검증용 멀티모달 (MEVA)**: 영상 프레임·VLM 캡션·capture metadata·사람 activity annotation이 연결되나, 522처럼 별도 물리 센서가 개입하는 구조는 아님.
3. **2.5채널 멀티모달 (UCA)**: 영상·VLM 캡션·사람 사건 문장 주석은 있으나 독립 메타데이터 센서 채널 부재.
4. **검색/답변 보조 (VRU, 지능형, 다각도)**: 영상·keyframe·캡션·메타데이터·qrels 또는 VLM 답변이 결합되나, 순환 붕괴 진단·QA 파급 규명 서브 테스트베드로 한정.
5. **색인/DB 검증용 (MIRIS, Sinnaedoro)**: 대용량 벡터 임베딩 + 시공간 predicate 중심, VLM-QA 자연어 qrels 없음.

### 3.2 비순환성 수준별 "가능한 주장 / 금지할 주장" (전량 보존)

| 수준 | 데이터셋 | 가능한 주장 | 금지할 주장 |
|---|---|---|---|
| 물리 3채널, 센서 포함 | 522 | 센서 predicate, 사람주석 relevance, 픽셀-only 생성문서가 파일·카메라·생산 경로 수준에서 분리 | 세 현상이 통계적으로 완전 독립, 동일 프레임 센서 정합 |
| A6 구조 분리, 센서 없음 | MEVA | capture metadata/activity annotation/VLM 문서의 논리적 생산자 분리 | 522와 같은 독립 센서 tri-source |
| 2.5채널 | UCA | 문장주석 relevance, 큐레이션/container predicate, VLM 문서 분리와 잔여 결합 공개 | 완전 3채널, annotation-free membership |
| 수리된 단일 외부 라벨 계보 | VRU, 지능형 CCTV | 문서 재진술 제거, filter/relevance 키 분리, 수리 전후 붕괴 | 생산자 독립 tri-source |
| 색인 코퍼스 | sinnaedoro, MIRIS | 실제 프레임 벡터와 predicate 하 filtered-ANN 평가 | 의미 검색 relevance나 캡션 검색 일반화 |
| 답변 전용 | 다각도 CCTV | 시점별 검색 문맥 공급 조건의 짝지은 답변 비교 | tri-source 검색 또는 완전 동기 다시점 |

### 3.3 멀티모달성 판단 기준 (스키마 수준 근거)

| 기준 | 설명 | 본 연구에서의 구현 |
|---|---|---|
| 시각 모달리티 | 실제 영상, 프레임, keyframe, CCTV clip | `frames/*.jpg`, `keyframes/`, `frame_index.parquet`, `frame_embeddings.npy` |
| 텍스트 모달리티 | VLM caption, 사건 설명, 질의 문장 | `documents.parquet`, `captions/*.jsonl`, `queries.jsonl` |
| 구조화 metadata | 시간, 위치, 신호, 밀도, 카메라, 장소 등 | `metadata.parquet`, `sensor_facets.parquet`, `predicate_inventory.csv` |
| 정답/평가 모달리티 | 사람 주석 또는 annotation 기반 qrels | `qrels.tsv`, `qrels_semantic.tsv`, `activity_presence.parquet`, `annotation_*_facets.parquet` |
| 검색 연결성 | query가 text/vector/metadata를 함께 사용 | B0–B5, prefilter/postfilter/hybrid, storage-unit 실험 |
| DB 관점 | 저장 단위, 색인, 필터 결합 방식 비교 가능 | `embeddings/*`, `visual_embeddings/*`, `results/storage_unit/*`, pgvector 결과 |

## 4. raw/파생 계보 체계 (①변환 / ②AI생성 / ③합성 — 전량 보존)

### 4.1 논리적 데이터 계층

| 계층 | 정의 | 이 연구의 예 |
|---|---|---|
| 원본(raw) | 외부 제공자가 배포한 관측물·주석을 내용 변경 없이 보관 | MP4/AVI/JPG ZIP, 센서 CSV, CVAT/KPF/JSON 주석 |
| staging | 원본 archive를 풀거나 일부 파일을 임시 선별한 사본 | 522 `frames_src/`, 지능형 CCTV `Datasets/raw/.../20260706` |
| 파생(derived) | 연구 코드가 원본 또는 다른 파생물에서 계산한 것 | facet, canonical, caption, embedding, synthetic vector |
| 워크로드(canonical) | 검색 평가를 위해 clip/document/metadata/query/qrels 계약으로 조립 | `canonical_trisource_expanded/` |
| 서비스 상태 | 파일이 아니라 DB 엔진에 적재된 가변 상태 | PostgreSQL `b3_frames`, `miris_frames2` |
| 결과(result) | 워크로드를 입력으로 실행한 측정·응답 | metrics CSV, VLM answer parquet, figure |

`Datasets/external`, `Datasets/raw`, `Datasets/restricted`는 **물리 namespace**이고 위 논리 분류와 일대일 대응하지 않는다(522 원본은 `external`, VRU 영상 원본은 `raw`, 지능형 CCTV는 `external`→`raw` staging). 논문에서는 폴더명이 아니라 **생산자와 변환 여부**로 raw/derived를 판정한다.

### 4.2 파생 유형

| 유형 | 정의 | 관측 사실과의 관계 | 대표 산출물 |
|---|---|---|---|
| ① 추출·파싱·임베딩 | 원본 내용을 선택·구조화하거나 고정 모델로 특징화 | 원 관측에 근거한 비생성적 변환. GPU·라이브러리에 따라 부동소수점 비트 단위 동일성은 별도 보장 필요 | archive 해제 JPG, facet parquet, BGE-M3/CLIP vector |
| ② AI 생성 | 생성형 모델이 픽셀 또는 검색 문맥을 보고 새 텍스트를 작성 | 원본 라벨이 아니며 오류·누락·과언급 가능 | Qwen2.5-VL 캡션, 답변 실험의 VLM 응답 |
| ③ 합성·proxy | 실제 관측값을 재표본·교란하거나 분석자가 대리 라벨을 부여 | 실측 관측으로 해석하면 안 됨 | sinnaedoro 1M jitter vector, MIRIS `tseg` 24버킷 |

판정 원칙: 임베딩은 신경망 산출이지만 새 사건 서술을 생성하지 않으므로 ①. canonical 조립은 여러 채널을 결합하지만 새 영상 관측을 만들지 않으므로 ①. 본 연구는 영상과 메타데이터를 하나의 joint vector로 학습·생성하지 않았다.

검색 문서 생산자는 데이터셋마다 다르다: **522·MEVA·UCA = 본 연구 Qwen2.5-VL 생성(②)**, **VRU·지능형 CCTV 수리판 = 외부 배포 캡션(raw 파싱, ①)**. "검색 대상 문서는 전부 AI 생성"이라는 서술은 과잉 일반화이므로 금지.

계보 구조도(정본 그림): `paper_assets/20260715_dataset_provenance/dataset_lineage_*.{dot,svg,png}` 9종. 재생성은 `python3 2026_KIISE/paper_assets/20260715_dataset_provenance/generate_dataset_lineage_diagrams.py --dpi 180` (자동 생성 `.dot`만 직접 고치면 다음 실행에서 덮어써짐 — 스크립트를 먼저 수정).

## 5. 데이터셋별 상세 정본 명세

### 5.1 AI Hub 522 교차로 신호체계 (Flagship)

- **원본**: 로컬 198G Training/Validation archive. 시각 원천은 MP4가 아니라 **사전 추출 JPG archive**(`TS_3/VS_3` 주 트랙, `TS_4/VS_4` 악천후·시간대 bbox 확장 트랙). 센서 기록 `TL_1/2`·`VL_1/2`(plain zip), 사람 주석 `TL_3/4`·`VL_3/4`(CVAT XML), `TL_5/VL_5` 큐보이드는 staging만. `TS_1/2`·`VS_1/2` 로컬 파일은 미개방 placeholder. 나머지 대형 archive는 확장자만 .zip인 solid 7z(LZMA2).
- **① 추출·파싱**: 주 트랙 **143,830 JPG**(train 127,746 + val 16,084, 1920×1080) / 52,462 visual-video 그룹; 별도 bbox 트랙 105,784 JPG(따라서 `frames_src/` 전체를 "143,830장"이라 부르면 틀림). 센서 CSV 파싱 = 32,880 클립 × 63 교차로. 주석 파싱 = 프레임 234,317행, video 52,210개.
- **교차카메라 결합**: 센서=카메라 코드 `x10`, 시각·주석=`x11/x22`. ±120초 창 조인율 **90.18%(47,308 비디오), gap 중앙값 0초** — 같은 세션의 동기 다중카메라 녹화(`join_type='cross_camera_time_window'`, 뷰는 다름·교차로 상태는 공유). 악천후(6,325)·시간대(9,056) 캠페인은 **센서 조인 0%**(별도 촬영)라 헤드라인 canonical에서 제외.
- **② 문서 생성**: 조인 성공+TL_3 보유 조건에서 `intersection_id × time_of_day` 층화, seed 20260710으로 3,000 video 표집, 각 video 중간 프레임 1장을 Qwen2.5-VL-7B-Instruct(snapshot `cc594898...`, greedy, 최대 110 토큰, prompt SHA-1 `3b9d8d45127aba00c2d2c7d5bbd7da8aad1140c8`)로 캡션화. **캡셔너 입력에 센서·CVAT facet 미포함**(소스 분리 + 토큰 누출 어서션).
- **canonical (정본)**: 3,000 clips / 3,000 AI 캡션 documents / metadata 27,000행 / **85 queries / strict 6,809 / semantic 24,872**. BGE-M3 문서 3,000×1,024·질의 85×1,024. 색인 트랙은 별도로 143,830 frames × CLIP 512d — **검색 트랙의 문서 단위와 색인 트랙의 프레임 단위를 혼용 금지**.
- **비순환성의 정확한 의미**: A6 감사 6/6은 계보 경로 분리(필터 키↔relevance 키 분리, relevance의 metadata 미유입, 기계 토큰 누출 0건, 희소 relevance)를 확인하는 것이지, 세 채널 현상의 통계적 독립을 뜻하지 않는다. 실제 30개 조합의 Cramér's V 최대 0.454(자연 상관 존재).
- **정본 경로 규칙**: 검색 결과 입력 정본은 `canonical_trisource_expanded/`(85질의). `canonical/`(15질의)·`canonical_trisource/`(32질의)는 과거/선택편향 진단 버전 — 헤드라인과 혼용 금지.
- **핵심 스키마(요약)**: `sensor_facets.parquet`(video_id, intersection_id, date, hour, time_of_day, n_vehicles, sig_has_yellow, sig_has_pedestrian, ...), `annotation_video_facets.parquet`(visual_video_id, n_objects, n_stopped, n_parked, n_bus, n_bike, ...), `documents.parquet`(doc_id, clip_id, text, lang), `qrels.tsv`(query_id, target_id, relevance). 3행 실물 샘플은 아카이브된 S1 §3.1 참조.
- **논문 접점(SYNC)**: RQ1 통제 주입 실험 0.181→**1.000(정답 필터)/0.854(라벨 재진술)**. RQ2(표4) 저장 단위: 설명문 0.063/0.181/1.15ms/24.6MB 기준; **다중 이미지(클립당 최대 3) 0.101/0.352(Δ+0.171 유의)/3.65ms/68.4MB(2.8배)**; 이중 색인(RRF k=60) 0.089/0.293/4.96ms/93.0MB(최고 비용); 저장 비교 전체 BH p=0.112. RQ3·RQ4는 §7 이력 참조.

### 5.2 AI Hub 시내도로 CCTV (sinnaedoro)

- **원본·real corpus**: 외부 320G JPG ZIP을 `build_sinnaedoro_visual.py`가 ZIP 내부에서 직접 읽어 위치·카메라·시간 분산 표집 후 CLIP ViT-B/32 임베딩. `corpus_real/frame_embeddings.npy` = **132,521×512 float32**, `frame_index.parquet` 동일 행수. facet cardinality: location 39, camera 16,107, date 51. hold-out query 1,000×512.
- **③ 1M 합성**: `corpus_aug_1m.npy` = 1,000,000×512 float32 (2,048,000,128 bytes). real vector 재표본+jitter로 생성, **색인 스케일 sweep 전용**. real(≤132,521)과 synthetic 구간은 결과에서 분리. synthetic에서 관찰한 latency·메모리는 시스템 스케일 결과이지 실제 CCTV 100만 프레임의 분포·라벨 결과가 아님.
- **관리상 한계**: `corpus_real/` 빌드 manifest 부재(원 입력 ZIP 목록·실행 인자 미보존), `corpus_aug_1m.npy`의 생성 스크립트·seed·jitter 분포·source-index map·checksum 부재. shape·파일은 검증되나 원점 재생성 계보 불완전 — 공개 재현 패키지에서 명시·보강 필요.
- **역할(SYNC, RQ5)**: real 132,521 = 실 predicate filtered-ANN, FAISS 색인 Pareto(Flat/HNSW M=32·efC=200·efSearch{64,256}/IVF-Flat nlist=64·nprobe{8,32}/IVF-PQ m=32·6bit), PostgreSQL `b3_frames` 부분 색인. 논문 RQ5 정본: **실측 군집 조건에서 전역 색인 재현율 손실 최대 0.627(무작위 대조는 최대 0.047 변동 → 무작위 마스크 평가는 과소평가)**; 조건별 부분 색인 98.12~100% 회복; 배포 규칙 = 전역 재현율 목표 0.95 미달 시 부분 색인/전수 검색 + 색인 갱신 시점까지 예상 질의 수의 선택도별 손익분기; Milvus/Weaviate는 필터율≥92.3% 또는 조건 만족 벡터<40,000이면 전수 검색 자동 전환. 이 데이터셋에는 의미 qrels·AI 캡션 문서가 없으므로 tri-source 검색 워크로드라 부르지 않는다.

### 5.3 MEVA

- **원본·보관**: 주석·문서는 `external/meva/meva-data-repo`(로컬 7.6G). 영상은 공개 S3 `drops-123-r13` AVI를 필요 시 내려받아 중간 프레임 추출 후 삭제 — **로컬 7.6G를 전체 영상 원본 보관량으로 읽으면 안 됨**(재구축에 원격 S3 필요). 로컬 LICENSE는 CC BY 4.0 명시(배포 전 영상·주석 각각 원문 조건 재확인).
- **①/② 파생**: KPF/DIVA activity + 파일명·capture metadata 파싱 → predicate(location, hour, time_of_day) / relevance(activity) 분리. 최종 코퍼스 **985 clips**(중간 프레임 + Qwen2.5-VL 픽셀-only 영어 캡션). canonical: documents 985 / metadata 3,940행 / **queries 193 / strict 4,405 / semantic 17,205**, A6 overall PASS. BGE-M3 985×1,024 + CLIP 985×512.
- **비순환성·한계**: predicate 생산자=capture metadata, relevance=DIVA 사람 활동주석, document=VLM — 구조상 A6 통과하나 **522 같은 독립 물리 센서 3채널은 아님** → 외적 타당성 arm. `meva_facets_stats.json`의 activity-positive 961 vs 최종 materialized 985는 서로 다른 카운트 — 논문 규모는 985만 사용, 961과의 선택 규칙 차이는 manifest로 추후 해소.
- **순환 리스크 규율(금지 규칙, 전량 보존)**: 활동클래스는 사람주석 계보 → **relevance로만 쓰고 절대 predicate로 재주입 금지**. predicate는 GPS/cam/time(물리 독립)에서만 도출. UAV(이동카메라) 클립은 고정 CCTV 프레이밍 위반 → 제외.
- **논문 접점**: 522 결론의 해외 CCTV 외적 검증 + 저장 단위 비교(522와 결과 반전 확인 — 저장 단위 이득의 코퍼스 의존성 근거). 2026-07-28 결정으로 **클립 조작적 정의의 인용 계보(MEVA[20])** 로도 사용.

### 5.4 MIRIS

- **원본**: `external/miris/data` 14G 중 Warsaw·Shibuya 고정 교통 영상 12개만 사용(beach·UAV 제외). 원 배포 README 기준 JSON detection/track은 사람 bbox 예제로 학습한 **YOLOv3 모델의 검출·추적 결과** — `nobj`를 "실제 차량수 ground truth"라 부르면 과장이며 "원 배포 YOLOv3 JSON의 프레임별 검출 객체수"가 정확.
- **① 임베딩·실 predicate**: 6프레임 stride·video당 최대 5,200장으로 60,019 프레임 CLIP 512d 임베딩 → 1,000 hold-out query + **59,019행 PostgreSQL `miris_frames2` 적재**. `scene`=Warsaw/Shibuya, `video`=12 카메라-세션, `nobj`=JSON 검출 객체수.
- **③ 시간 proxy**: `tseg` = video 내 프레임 순서 24등분 위치 bucket(0–23). **실제 촬영 시각·hour-of-day 아님.** 구형 `miris_frames.hour` 열도 동일 계산이므로 "hour"로 해석 금지(후속 `miris_frames2`가 `tseg`로 정정).
- **저장 상태**: `miris_frames`·`miris_frames2` 각 59,019행(약 161.6/162.1 MiB), bind mount `Datasets/services/postgres_pgvector`. portable dump·parquet snapshot 없음 → 서버 volume 손상 시 재임베딩 필요(장기 보존 부족).
- **역할(RQ5)**: 의미 qrels·캡션 코퍼스가 아니라 실제 공간/내용 predicate + 시간 proxy를 가진 **부분 색인·hot/cold 정책 교차검증** 코퍼스. [정정 2026-07-28: S5(730, 07-13) 시점에는 SIGMOD 2020 related-work 후보로 발굴된 상태였으나, 이후 실사용 8종(DB 검증)으로 승격되어 논문 표 1에 포함됨.]

### 5.5 VRU-Accident (수리판)

- **원본**: 영상 1,000개 `raw/VRU-Accident`, HF 배포 `external/VRU-Accident_hf`(1,000 dense captions + 6,000 VQA). 검색 문서는 **외부 배포 dense caption**(본 연구 Qwen 생성 아님) — 원 캡션 생성 절차는 원 논문 인용으로 설명.
- **v1→수리판**: v1 canonical은 외부 caption+VQA 파생 facet statement로 documents 7,000/queries 244를 만들었고 filter·qrels·문서가 같은 VQA 계보 공유 = 순환. 수리판 `20260710_noncircular`는 facet statement 제거(캡션-only 1,000 docs, F2 fix), relevance=**accident_type**, filter=**weather_light/road_type/location**(결합도 V=0.177/0.039/0.249, F1/F4 fix), strict+semantic 이중 qrels, A9 감사 PASS. 최종 1,000 docs / **85 q / 3,744 / 9,703**.
- **한계·역할**: filter와 relevance가 논리적으로 분리됐어도 모두 같은 외부 VQA 계보 파싱이므로 522의 생산자 수준 분리보다 약함(A9는 이 한계 명시). 역할 = 순환 붕괴 사례(RQ1: **0.9736→0.3174**)와 고정 LLM **검색 문맥 사다리** 앵커(RQ6: 답변 정확도 **31%(무증거)→53%(무관)→67%(벡터 검색)→75%(대상 설명문)**; 근사 색인 재현율 차이의 답변 전파는 표본 부족으로 탐색적·미확립).

### 5.6 AI Hub 지능형 관제 CCTV (수리판)

- **원본·staging**: 외부 13G에서 MP4 269 + JSON 269 선별 → `raw/aihub_intelligent_cctv/20260706` staging(`clip_pairs.csv`로 쌍 고정, missing 0). `event_caption`은 외부 라벨에 이미 포함된 문서(본 연구 AI 생성 아님).
- **v1→수리판**: v1은 event class 그대로 쓰는 template statement 포함 documents 807/queries 133 = 순환 지표. 수리판은 외부 `event_caption` 269개만 유지, relevance=event_class, filter=night/place_type. 최종 **18 q / 584 / 827**.
- **한계·역할**: 문서·filter·relevance 원천이 모두 같은 외부 JSON label 생산자 → 완전 tri-source 아님. 결합도 주의: night V=0.583/place V=0.485(자연 상관, 소형 n) → collapse 실증 전용, 저결합 헤드라인은 522 담당. RQ1 정본: **1.0000→0.8395**. 부수 관찰(정직 포인트): 영어 질의↔한국어 캡션에서 dense(bge-m3, semantic 0.82) ≫ BM25(0.17) — 교차언어 sparse 실패/다국어 dense 생존은 수리판에서만 보이는 진짜 신호.

### 5.7 UCA / UCF-Crime

- **원본**: UCA 주석 = UCF-Crime 1,854영상·23,542문장·110.7시간 (raw MP4는 1,950개지만 주석 연결 영상은 1,854개). 로컬 194G. UCA README는 Apache-2.0과 연구용 사용을 함께 적으며 기반 UCF-Crime 영상 조건은 별도 — 재배포 범위는 두 원천 함께 검토.
- **①/② 구축**: 주석 구간에서 video당 최대 4개 사건 구간 등간 표집·중간 프레임 materialize → **6,432 문서**(중복 `(video, midpoint)` 58건 병합, frame drop 0). Qwen2.5-VL 픽셀-only 캡션(정답 렉시콘 미주입 prompt). canonical: **queries 135 / strict 7,709 / semantic 41,435 / metadata 19,296행**, BGE-M3 6,432×1,024 + 135×1,024.
- **2.5채널 한계**: relevance=사람 문장주석의 동결 렉시콘, predicate=video class·container duration·일부 annotation timing, document=VLM 캡션. 독립 센서 없음 + 코퍼스 membership이 annotation event span에 의존 → 522와 같은 물리 3채널이 아니라 **2.5채널 외적 타당성**으로만 보고. `event_position_bin`은 content-free timing이라도 UCA annotation 생산자에서 나와 채널-청정 대조에서 강등.
- [정정 2026-07-28: 논문 정본(RQ3)의 UCA 재현 보고는 **129질의 기준 3/4 재현**이다. canonical 구축분은 135질의이므로, 135→129 제외 규칙(필터/적격성)을 재현 문서에 명시해야 한다. 수치 인용 시 논문 기준 129를 우선한다.]

### 5.8 AI Hub 다각도 CCTV

- **원본·canonical**: 483G ZIP에 4,500사건 × c1/c2 총 9,000영상 + JSON 4,500. canonical: clips 4,500 / views 9,000 / evidence-frame rows 27,000 / label-derived documents 36,000 / metadata 63,000 / queries 4,572. 이 36,000 문서는 **외부 JSON 필드+template의 staging 문서**이며 픽셀-only Qwen 캡션 코퍼스가 아님.
- **답변 실험 파생**: bbox 가시성 비대칭 기준 **400사건** 선정, 두 시점 × 최대 3장 = **2,400 검색 문맥 프레임**(오류 0). Qwen2.5-VL·Qwen2-VL·InternVL3·Idefics2가 closed/worse/better/both 조건 답변 생성 — ② AI 생성이지만 데이터셋 검색 문서가 아니라 **평가 결과**.
- **한계·역할**: 두 시점 프레임의 완전 동기 pair 보장 없음, better/worse는 bbox 면적 기반. tri-source 검색 헤드라인에는 사용 금지. 논문 접점(RQ6, SYNC): **잘 보이는 단일 시점 +15.2%p, 두 시점 동시 제공 무이득**. (4,500클립 검색 canonical은 미사용; Qwen manifest 사후 재구성은 명시된 한계.)

## 6. canonical 규모·생산자 비교 (정본 표)

| 데이터셋/트랙 | clip/frame | 검색 문서 생산자 | documents | queries | strict qrels | semantic qrels | embedding |
|---|---:|---|---:|---:|---:|---:|---|
| 522 검색 | 3,000 clips | 본 연구 Qwen2.5-VL | 3,000 | 85 | 6,809 | 24,872 | BGE-M3 1,024d |
| 522 색인 | 143,830 frames | 문서 없음 | - | 실험별 image/query | - | - | CLIP 512d |
| sinnaedoro real | 132,521 frames | 문서 없음 | - | 1,000 | exact ANN GT | - | CLIP 512d |
| sinnaedoro synthetic | 1,000,000 vectors | 문서 없음 | - | 위 query 재사용 | exact ANN GT | - | 합성 CLIP-space 512d |
| MEVA | 985 clips | 본 연구 Qwen2.5-VL | 985 | 193 | 4,405 | 17,205 | BGE-M3 1,024d + CLIP 512d |
| MIRIS rich | 59,019 DB frames | 문서 없음 | - | hold-out 1,000 | exact filtered ANN GT | - | CLIP 512d |
| VRU 수리판 | 1,000 clips | 외부 VRU dense caption | 1,000 | 85 | 3,744 | 9,703 | BGE-M3 1,024d |
| 지능형 CCTV 수리판 | 269 clips | 외부 JSON event_caption | 269 | 18 | 584 | 827 | BGE-M3 1,024d |
| UCA | 6,432 segments | 본 연구 Qwen2.5-VL | 6,432 | 135 | 7,709 | 41,435 | BGE-M3 1,024d |
| 다각도 canonical | 4,500 events | 외부 JSON + template | 36,000 | 4,572 | 18,000 | 없음 | 답변 실험은 frame 입력 |

**논문 실험 설계와의 접점(SYNC).** 벡터 데이터베이스 계층의 다섯 설계 축(§4.2)과 구성 산식 **유효 데이터-계획 조합 1×4+4×3=16 × 색인 설정 7 = 112 구성**은 방법 문서 관할이나, 데이터 관점 대응은 다음과 같다: ①검색용 데이터(영상 설명문/대표 이미지/이미지·설명문 결합/다중 이미지(클립당 최대 3)/설명문·이미지 이중 색인(RRF k=60)) = 522 검색 트랙의 캡션·프레임 파생물; ②검색 계획(벡터 단독/검색 전 조건/검색 후 조건(상위 200 후보)/혼합(영상 설명문 전용)) = predicate 채널; ③검색 신호·순위 융합(메타데이터 단독/BM25/벡터/BM25-벡터 RRF); ④물리 색인(Flat/HNSW/IVF-Flat/IVF-PQ) = 색인 코퍼스(522 색인·sinnaedoro); ⑤배포(전역/조건별 부분 색인) = sinnaedoro·MIRIS.

## 7. 비순환 워크로드 구축 실행 이력 (2026-07-10~12, 규칙류 전량 보존)

### 7.1 Phase 0 — 센서 predicate 트립와이어 (T2/T3, CPU)

입력: 교차로신호체계 라벨 zip `TL_1.통과차량`+`TL_2.보행량`(train) / `VL_1`+`VL_2`(val). 산출: `sensor_facets.parquet` 32,880 클립 × 63 교차로(9초 CPU 파싱, 미개방 원천 raw 불사용).

**T2 — predicate 카디널리티/selectivity (PASS):**

| predicate | 카디널리티 | min selectivity | 판정 |
|---|---:|---:|---|
| intersection_id | 63 | 0.013 | selectivity sweep 이상적 |
| hour | 12(주간만) | 0.022 | 통과 |
| time_of_day | 3(dawn 없음) | 0.293 | 통과 |
| sig_has_pedestrian | 2 | 0.427 | 통과 |
| sig_has_yellow | 2 | 0.308 | 통과 |
| veh_density_bin | 3 | 0.333 | 통과(구성상 균형) |
| sig_has_left | 2 | 0.044 | 95.6% 클립에 존재 → 이진 predicate 약함 |
| **is_weekend** | **1** | **1.000** | **전 클립 평일 → 폐기** |

신호위상 트립와이어 통과: 전역 `signal_info.movement` 분포 t 0.606 / tl 0.132 / l 0.119 / s 0.072 / y 0.051 / p 0.021 — 전부-'t' 아님. 단 clip 단위 좌회전 신호는 거의 상존 → clip-level 이진보다 위상-구성/시간창 feature로 사용.

데이터 특성(설계 반영): 평일·주간 only(is_weekend 폐기, dawn 없음); n_vehicles min 1/mean 44.8/max 400, n_pedestrians mean 6.5/max 64(count 기반 QA 프로그램 검증 가능); R-feature base rate has_left/right_turn 0.94/0.95(이진 QA 약함→count/argmax 설계), has_uturn 0.21·has_bus 0.68·has_bicycle 0.63(균형).

**T3 — predicate ⟂ relevance 독립성 (PASS):** 저결합 쌍 확정 — `time_of_day×has_bus` V=0.004, `sig_has_pedestrian×has_bicycle_ped` 0.058, `sig_has_yellow×has_left_turn_veh` 0.180, `hour×has_truck` 0.208. 고결합(회피 또는 결합강도 곡선 대조군 전용) — `sig_has_left×has_left_turn_veh` 0.751, `intersection_id×has_right_turn_veh` 0.648, `intersection_id×has_bus` 0.549. 대다수 쌍 V<0.3 → 순환 없는 헤드라인 성립.

### 7.2 Phase 1 — 비순환 canonical + A6 감사 (PASS)

1차 시도의 정직한 발견: 이진 R-feature(has_bus 등)를 relevance로 쓰면 질의당 positive 3,349개(코퍼스 10%) = 비변별적 class-membership. → count/threshold 기반 **희소 relevance**로 교체: `heavy_traffic`(n_vehicles≥150, 2.6%), `uturn_with_peds`(3.0%), `many_bicycles`(4.2%), `crowd_with_bicycle`(5.6%) — 질의당 positive 평균 219.6개(0.7%), relevance 밀도 중앙값 3.6%.

**A6 비순환 감사 어서션 (machine-checked, 전량 보존):**
- 필터 키 ∩ relevance = ∅ (disjoint)
- 필터 키 ⊂ P-predicate(time_of_day/hour/sig_has_yellow/sig_has_pedestrian)
- relevance = 희소 scene def (밀도<8%)
- 저결합 4/4, max Cramér's V=0.184
- OVERALL NON-CIRCULAR PASS = True

설계 확정: 센서 CPU 트랙 = (a) 필터 predicate selectivity(filtered-ANN) + (b) 프로그램 검증 QA(count/argmax/threshold)에 최적. 이진 base-rate feature는 retrieval relevance로 부적합. fine-grained retrieval relevance는 VLM 캡션(희소 의미 질의)으로 보강.

### 7.3 T1 실행 + 522 데이터모델 재발견 3건

1. **TS_3는 mp4가 아니라 추출된 JPG 프레임**: train 127,746 + val 16,084 = 143,830 JPG, 46,527+α 비디오 × ~3프레임 — 키프레임 추출 파이프라인 불필요. 카메라 코드 = ID 끝 2자리(센서=10, 시각=11/22).
2. **클립 수준 센서↔시각 조인 성립(동기 녹화)**: join_rate ±120s = 90.2%(47,308 비디오), median gap 0초. "TL_1↔TS_3 조인 불가" 비관은 키 정규화 오류였음(수정 후 성립).
3. **시각 relevance는 사람 주석에서 프로그램 도출 가능**: TL_3=CVAT polyline 궤적+차종 라벨+is_stopped/is_parked 등, TL_4=프레임 bbox(악천후 170/시간대 372 카테고리 포함 → 악천후=진짜 날씨 predicate). relevance 소스(TL_3/4, cam 11/22)와 predicate 소스(TL_1/2 센서 cam 10)가 파일·카메라 수준에서 분리 → 비순환성이 소스 수준에서 보장.

주석 facet 완성: frame_rows 234,317(TL_3 133,979 + TL_4 100,338) → 52,210 비디오에 사람 주석 relevance. 희소 relevance: any_parked 1.7%, any_stopped 18.8%, bus 43%, bike 41%. Tri-source 독립성(n=47,098): 센서 predicate(5)×주석 relevance(6) 30쌍 중 25쌍 V<0.3, global max 0.454; 초저결합 쌍 `sig_has_yellow×rel_parked` V=0.005, `time_of_day×rel_multi_bus` 0.007, `sig_has_pedestrian×rel_parked` 0.012, `hour×rel_multi_bus` 0.023. TS_4/VS_4 악천후·시간대 프레임은 별도 캠페인(센서 조인 0%) → 큐레이션 predicate 확장 트랙으로 구분.

### 7.4 A9 — 순환 워크로드 수리 + collapse 실측 (RQ1 정본)

**VRU (v1 어댑터 서브클래스, v1 무손상):**

| 전략 | v1 순환 | v2 strict | v2 semantic |
|---|---:|---:|---:|
| B2 vector-only | 0.4476 | 0.1845 | 0.2649 |
| **B4 prefilter** | **0.9736** | **0.3174** | 0.2974 |
| B1 BM25 | 0.4495 | 0.0918 | 0.1607 |

B4−B2: +0.526(tautology) → +0.133(strict, 합법 이득)/+0.033(semantic). semantic per-query 부호분포 음수 18/0 34/양수 33 (n=85) — v1에서 구조적으로 불가능한 음수 등장 = "B4≥B2 보장"의 실측 붕괴.

**지능형 CCTV:** B4 **1.0000→0.8395**, B3 1.0000→0.8395, B1 BM25 0.9600→0.1111(v1 완벽지표 = 순수 라벨 문자열 매칭 확정), B2 0.7014→0.6285. semantic 부호 neg 4/zero 12/pos 2 (n=18).

**유의성 (B4−B2, nDCG@10, paired bootstrap 5000 + Wilcoxon):**

| 데이터셋 | qrels | Δ | 95% CI | 판정 |
|---|---|---:|---|---|
| VRU v2 | strict | +0.1329 | [0.092, 0.179] | 유의 (p≈2e-4) |
| VRU v2 | semantic | +0.0325 | [0.005, 0.064] | marginal (Wilcoxon 0.075) |
| AIHub v2 | strict | +0.2110 | [0.078, 0.364] | 유의 (p=0.005) |
| AIHub v2 | semantic | +0.0192 | [−0.032, 0.098] | 비유의 |

[정정 2026-07-28: 논문 정본(RQ1)은 수정 전후 **0.9736→0.3174(VRU), 1.0000→0.8395(지능형 관제)** 를 헤드라인으로 쓰고, 추가로 **통제 주입 실험 0.181→1.000(정답 필터)/0.854(라벨 재진술)** 로 순환 기전을 통제 조건에서 재현했다. 위 표들은 그 산출 이력이다.]

### 7.5 522 tri-source 최종(32질의) + 확장(85질의)

**32질의 최종 (canonical_trisource, strict 1,472/semantic 9,062, A6 6/6 PASS):** strict Δ+0.1445 [0.082, 0.216] / semantic Δ−0.0745 [−0.133, −0.012] / semantic·low-coupling Δ−0.1308 / contrast Δ+0.0693 n.s. 확정 발견 5항(이력): ①prefilter 가치는 제약의 성격이 결정 ②손해는 저결합에 집중(결합강도 곡선의 데이터 실현) ③strict에서 B0 metadata-only(0.165) > B2 dense(0.064) ④VLM 캡션의 문서 맹점(parked 쌍 dense ~0) ⑤v1 순환 붕괴 3워크로드 재현.

**질의셋 확장 32→85 — 사전선언된 기계적 확장 규칙 (전량 보존):**
1. 신규 relevance def는 밀도 [1%,12%] ∧ 기존 def의 불리언 조합 금지 → `two_plus_bikes`(11.5%)만 승인(truck_convoy3 13.6%·very_dense25 0.87% 기계 기각)
2. 쌍 구성 = 5 predicate × 5 rel-def **전체 교차곱**(손선별 금지)
3. 결합도 라벨 = 실측 V<0.3 동일 임계
4. 원본-32는 `in_original_specs`로 분리 보고

산출: `canonical_trisource_expanded/`(85질의, A6 6/6 PASS), `results/trisource_expanded_b0_b5/`.

**확장 결과 (semantic B4−B2, nDCG@10):**

| 표본 | n | Δ | 95% CI | 판정 |
|---|---:|---:|---|---|
| 원본-32 (재현) | 32 | −0.0745 | [−0.136, −0.014] | 재현 |
| 확장-신규 | 53 | +0.0197 | [−0.008, 0.050] | n.s. — 집계 손해 주장 생존 실패 |
| 통합-85 | 85 | **−0.0158** | [−0.047, 0.015] | n.s. |
| 통합·low-coupling | 75 | −0.0357 | [−0.065, −0.008] | boot-유의 |
| 통합·contrast | 10 | **+0.1335** | [0.017, 0.249] | 유의(양) |

**T3 결합강도 곡선과 정정 이력 (전량 보존):** 최초 산출 Spearman ρ(Δ, pair V)=0.285 CI [0.071, 0.484], 구간 평균 단조(V<0.05 −0.099(n=27) → 0.05–0.15 −0.002(30) → 0.15–0.3 +0.003(18) → V≥0.3 +0.134(10)).
- *(정정 2026-07-11: 최초 산출의 pd.cut 좌측 개구간이 V=0.0 완전 독립 쌍 11개를 최저구간에서 탈락시켜 −0.142로 편향 — F5 검증기 적발, 포함 후 −0.099가 정본.)*
- *(정정 2026-07-12: codex 교차 검증이 의사반복 적발 — V는 (predicate 필드×정답) 쌍 수준 속성(25쌍)이므로 질의 수준 CI는 군집 무시. 쌍 군집 부트스트랩(seed 20260712, B=5000): ρ CI [−0.031, 0.485], 저결합 V<0.05 [−0.179,+0.013], V<0.3 [−0.094,+0.010] — 모두 0 포함 → 곡선은 **탐색적 경향**으로 강등. 자연결합 V≥0.3은 2쌍뿐(참고용). 정본: `paper_assets/20260712_codex_crosscheck_fixes/t3_cluster_inference.json`. 같은 검증에서 주차-dense 실패 기전 정정: 캡션 87%가 'parked' 언급(절반 부정형), 긍정 언급 판별력 52% vs 45% → '서술 부재'가 아니라 부정·과언급 혼동, `parked_caption_crosstab.json`.)*
- **[정정 2026-07-28: 논문 정본(RQ3, 표5·6)의 최종 프레이밍 — 엄격 기준 검색 전 조건 Δ+0.0983 유의(단 '자명한 결과'로 해석); 의미론 기준 벡터 단독 0.170 최고, Δ=−0.0158 무의미; 고결합(V≥0.3) Δ+0.1335; UCA 129질의 재현 3/4. 중간 시점의 "−0.075 손해" 및 "단조 연속곡선(ρ CI 0 배제)" 헤드라인은 확장·군집 추론·논문 확정 과정에서 순차 강등된 이력이다.]**
- **[정정 2026-07-28: RQ4 정본(§5.2.4) — 전 신호 독립 이득 없음: 메타 단독 0.218/0.217, BM25 0.017/0.050, 벡터 0.059/0.170, 혼합 RRF 0.133 < 벡터 0.154; 지식그래프 재조합 Lift 중앙값 0.002 무이득. 32질의 시점의 "B0 0.165 > B2 0.064"는 85질의 정본 수치(0.218/0.059)로 대체된 이력이다.]**

교훈(방법론 규칙): filtered-search 평가의 집계 결론은 질의 믹스에 좌우된다 — **결합도 스펙트럼을 명시적 보고 축으로** 삼아야 하며, 이것이 본 워크로드 프로토콜의 일부다.

## 8. 저장·관리 구조와 정본 선택 규칙

### 8.1 물리 구조

```text
Datasets -> /hdd2/KIISE_datasociety/Datasets
├── external/      외부 archive, repo, 원 배포 데이터
├── raw/           일부 데이터셋의 해제·선별 staging 또는 영상 원본
├── restricted/    접근 제약 데이터 후보
├── processed/     버전이 붙은 canonical, frame, facet, embedding, result
├── models/        고정 모델 가중치
├── cache/         재생성 가능한 모델 cache
├── services/      PostgreSQL 등 상태 저장 volume
└── envs/          실행 conda 환경

2026_KIISE/
├── scripts/       변환·평가 코드
├── project_md/    설계·실행·계보 문서
├── paper_assets/  동결 결과표·그림·검증 리포트
└── manuscript/    현재 원고와 제출본
```

원천 규모 실측(2026-07-13): external ~1.6T — 이상탐지 573G · 다각도 483G · 시내도로 320G · 교차로신호(522) 198G · UCA 194G · CityFlow-NL 16G · 지능형관제 13G · VRU 5.8G. processed 8종: 522(142G)·sinnaedoro(2.5G)·uca_anchor·vru·multi_angle·intelligent·abnormal·cityflow_nl.

### 8.2 정본 선택 규칙 (전량 보존)

1. 522 검색은 `canonical_trisource_expanded` 85질의를 정본으로 쓴다.
2. VRU와 지능형 CCTV 검색은 `20260710_noncircular`만 현재 수리판으로 쓴다. `20260706`은 순환 붕괴를 보이는 역사 대조다.
3. MEVA는 최종 985 clips/193 queries 결과만 사용한다. 276 clips/73 queries 파일럿 수치는 superseded다.
4. MIRIS의 실제 공간·내용 predicate 보고에는 `miris_frames2`와 `*miris2*` 결과를 우선한다. 구형 `miris_frames.hour`는 실제 시각으로 해석하지 않는다.
5. sinnaedoro `filtered_ann/filtered_ann.csv`는 구 random-mask 결과다. 실 predicate 정본은 `paper_assets/20260710_pillarB/filtered_ann_real_A.csv`다.
6. CityFlow-NL과 이상행동 CCTV는 확보·구축 목록에는 남기되 현재 실사용 수에는 넣지 않는다.

### 8.3 재현 entry point와 감사 파일

| 데이터셋 | 주요 구축 코드 | 정본 감사/manifest |
|---|---|---|
| 522 | `extract_intersection_visual_sources.py`, `build_intersection_signal_sensors.py`, `build_intersection_annotation_facets.py`, `build_visual_sensor_join.py`, `build_intersection_captions.py`, `build_intersection_trisource_canonical.py`, `build_intersection_frame_clip.py` | `canonical_trisource_expanded/A6_trisource_audit.json`, caption/embedding/visual manifest |
| sinnaedoro | `build_sinnaedoro_visual.py`, `run_index_structure_benchmark.py`, `build_p1_predicate_tables.py` | `paper_assets/20260710_pillarB/P1_manifest.json`; corpus/1M build manifest는 미완전 |
| MEVA | `build_meva_facets.py`, `build_meva_captions.py`, `build_meva_trisource_canonical.py` | `canonical_trisource/A6_trisource_audit.json`, caption/embedding manifest |
| MIRIS | `build_miris_pgvector.py`, `build_miris_pgvector_rich.py`, `run_pgvector_partial_index.py` | `paper_assets/20260713_db_design/pgvector_partial_manifest_miris2.json` |
| VRU | `build_vru_noncircular_canonical.py` | `canonical/A9_noncircular_audit.json` |
| 지능형 CCTV | `build_aihub_cctv_noncircular_canonical.py` | `canonical/A9_noncircular_audit.json` |
| UCA | `build_uca_corpus.py`, `caption_uca.py`, `analyze_uca_external.py` | `build_manifest.json`, `canonical/A6_UCA_audit.json`, caption/embedding manifest |
| 다각도 CCTV | `build_aihub_multi_angle_cctv_canonical.py`, `build_bbox_asymmetry_stratum.py`, `materialize_aihub_multi_angle_evidence_frames.py`, `run_multiview_answer_vlm.py` | canonical/stratum/frame/run manifest |

### 8.4 데이터셋별 파일 구성 인벤토리 (요약; 전체 표는 아카이브 S6)

- **522**: 원천 `external/교차로신호체계/{1.Training,2.Validation}/{원천,라벨링}데이터/*.zip`; 파생 `sensor_facets.parquet`, `visual_sensor_join.parquet`, `annotation_{video,frame}_facets.parquet`, `captions/`, `canonical_trisource_expanded/{clips,documents,metadata,queries.jsonl,qrels.tsv,qrels_semantic.tsv,A6_trisource_audit.json}`, `embeddings_trisource_expanded/bge-m3/`, `visual_embeddings_clip/{frame_embeddings.npy,frame_index.parquet}`, `results/{trisource_expanded_b0_b5,storage_unit}/`.
- **MEVA**: `external/meva/meva-data-repo`(주석·LICENSE), `processed/meva_kf1/20260713/{activity_presence.parquet,predicate_facets.parquet,frames/,captions/,canonical_trisource/,embeddings/,results/{meva_bgem3_b0_b5,storage_unit}/}`.
- **MIRIS**: `external/miris/{ytstream-dataset.zip,data/README.txt,download.log}`, `processed/miris_traffic/20260713/`(query vector), PostgreSQL 적재본, `paper_assets/20260713_db_design/{pgvector_partial_vs_global_miris.csv,hotcold_miris_policy.csv}`.
- **sinnaedoro**: `corpus_real/{frame_embeddings.npy,frame_index.parquet,predicate_inventory.csv,queries.npy}`, `index_benchmark/`, `filtered_ann/`(구산물, §8.2 규칙 5), `corpus300k_shard{0,1}`, `corpus_aug_1m.npy`.
- **UCA**: `external/UCA_surveillance/{UCF_Crimes.zip,repo}`, `processed/uca_anchor/20260712/{annotation_sentences.parquet,relevance.parquet,frames/,captions/,canonical/,results/}`.
- **VRU**: `processed/vru_accident/20260706/`(v1 역사 대조), `20260710_noncircular/`(수리판), `visual_embeddings/{clip,siglip}*`, `embeddings/{bge-m3,e5-large-v2}`, `service_testbed/*/service_packets.jsonl`.
- **지능형 CCTV**: `20260706/`(v1) + `20260710_noncircular/`(수리판), keyframes, embeddings, service packets.
- **다각도**: `canonical*/{views.parquet,evidence_frames.parquet}`, `canonical_stratified_event_split_5/`, `results/{multiview_answer_vlm_*,answer_grounding_*}`.

## 9. 기존 문서 검토에서 확인된 정정·보완 사항 (전량 보존, 2026-07-28 주석 포함)

1. "검색 대상 문서는 전부 AI 생성"은 과잉 일반화다. 522·MEVA·UCA에는 맞지만, VRU와 지능형 CCTV 수리판은 외부 제공 caption을 사용한다.
2. 522의 주 시각 원본은 영상이 아니라 미리 추출된 JPG archive다. 여기서 ①은 video decoding이 아니라 archive 해제다.
3. 522 `frames_src/`에는 주 트랙 143,830장 외에 bbox 확장 트랙 105,784장이 함께 있다.
4. MEVA 원 AVI는 로컬에 보존되지 않고 중간 프레임 추출 뒤 삭제된다. 현재 7.6G를 전체 영상 원본 크기로 읽으면 안 된다.
5. MEVA의 "961 activity-positive"와 최종 "985 materialized corpus"는 서로 다른 카운트이므로 단일 규모처럼 섞지 않는다.
6. MIRIS `nobj`는 원 배포 YOLOv3 검출 결과이고 사람 차량수 정답이 아니다. `tseg`와 구형 `hour`는 실제 시계가 아니다.
7. MIRIS 벡터 본체는 파일이 아니라 PostgreSQL 표에만 있어 현재 관리가 서비스 상태에 의존한다.
8. 구조적 A6 tri-source는 MEVA도 통과하지만, 독립 센서까지 갖춘 물리 3채널은 522만이다.
9. sinnaedoro real corpus와 1M synthetic의 완전한 생성 manifest가 없어 공개 재현성에 결손이 있다.
10. ~~현재 참고문헌 목록에는 MEVA와 MIRIS의 직접 인용이 보이지 않는다.~~ [정정 2026-07-28: 제출본(paper_final)에서 MEVA는 참고문헌 **[20]** 으로 인용되어 클립 조작적 정의의 계보 방어에 사용된다. MIRIS 직접 인용 여부는 개정 시 재확인 필요.]

## 10. 공개·윤리·재현 시 주의사항 (전량 보존)

1. AI Hub, UCF-Crime/UCA, MIRIS 등은 원 영상 재배포 조건이 서로 다르다. 원본, 프레임, 임베딩, 캡션을 동일한 공개 가능 범주로 간주하지 않는다.
2. MIRIS 로컬 README는 제공 영상의 저작권을 보유하지 않으며 비상업 연구용으로만 제공한다고 명시한다. "MIRIS 전체가 MIT"라고 포괄 표기하지 않는다.
3. MEVA 로컬 LICENSE는 CC BY 4.0을 명시하지만 attribution과 원 영상 범위를 최종 배포 시 재확인한다.
4. UCA annotation license와 기반 UCF-Crime 영상 조건을 분리해 기록한다.
5. 생성 캡션에는 모델 snapshot, prompt hash, decoding, seed를 남기고 원본 사람 라벨과 같은 필드에 저장하지 않는다.
6. synthetic/proxy 산출물은 파일명, manifest, 결과표의 regime 열에서 real과 분리한다.
7. 원본 archive에는 SHA-256 inventory가 없으므로 장기 재현을 위해 dataset-level checksum registry가 추가로 필요하다.
8. 절대 물리 경로는 manifest에 기록돼 있어도 실행 계약은 `Datasets/...` 논리 경로를 사용한다.

## 11. 최소 보완 과제 (전량 보존, 미완)

1. `sinnaedoro_traffic/corpus_real/build_manifest.json`을 소급 작성해 원 ZIP 목록, 표집 규칙, model snapshot, 실행 인자, 파일 SHA-256을 기록한다.
2. `corpus_aug_1m.npy`의 생성 코드 또는 재현 notebook을 복구하고 seed, jitter 분포, source row mapping, 품질검사 결과를 manifest로 고정한다.
3. PostgreSQL `miris_frames2`를 portable parquet 또는 `pg_dump`로 동결하고 schema, row count, vector model snapshot을 함께 보관한다.
4. MEVA 961/985 카운트 차이를 clip-level selection manifest로 설명하고, 최종 985 clip ID를 checksum과 함께 동결한다.

## 12. 해외·확장 데이터셋 landscape 판정 (종결)

세 차례 조사(S3 부록 14에이전트 / S4 43에이전트 / S5 80에이전트, 누적 후보 100+)의 일관 결론:

- **제2의 깨끗한 비순환 tri-source 헤드라인은 해외에 없다 — 522 단독.** 522는 AI-Hub 패키지가 센서 CSV(cam10) + 독립 CVAT(cam11/22) + 픽셀캡션 3소스를 우연히 제공한, 사실상 유일한 소스 분리 사례다.
- **외적타당성 arm 채택 = MEVA** (WACV 2021, CC-BY-4.0 원문 확인, 무서명 S3 `s3://mevadata-public-01`, 한국 다운로드 확인, 게이트·geo·ND 전무). 백업: **LUMPI**(IV 2022, 고정 3카메라+5 LiDAR 교차로, CC-BY-NC-3.0 — ND 아님, 직접 다운로드), MEVID(MEVA 위 identity relevance 층), QVHighlights(NeurIPS 2021, 네이티브 멀티모달 일반화 1순위), MS-COCO(최정결 라이선스, 이미지-텍스트), VIRAT/VATEX/ActivityNet-Cap·DiDeMo/CC3M·12M(각 제약 명시).
- 두 갈래 결정(이력): 갈래 A=도메인일치 감시 arm(MEVA 주+LUMPI 백업, 권장·채택됨), 갈래 B=네이티브 멀티모달 타도메인 일반화 arm(QVHighlights/MS-COCO — 감시 도메인 아님+tri-source 붕괴, 미채택).
- 주요 탈락 사유(요약; 상세는 아카이브 S4·S5): 라이선스 -ND/재배포 금지(TUMTraf 계열, WTS, Rope3D, CityFlow/V2, MSR-VTT, WILDTRACK, Ko-PER), 도메인 불일치 ego/대시캠/웹(DAIR-V2X, NuPlanQA, DoTA/DADA, DRAMA, VidOR, Flickr30k 등), 확보 하드실패(IPS300+, SUTD-TrafficQA, RoadSocial, PANDA, WebVid, TVR, INTERACTION/inD/SIND 등), venue 미달(arXiv-only). AD군(nuScenes/Waymo/Argoverse/BDD)은 ego 도메인 불일치.
- S5(730) 추가 발굴로 남은 사각 확인: 우리 corpus에 없는 축 = 오디오(Urbansas CC-BY, MAVAD)·열화상/LiDAR(R-LiViT CC0, AAU RainSnow)·네이티브 QA(HAWK, SurveillanceVQA-589K MIT)·**DB학회 비디오-질의 벤치(MIRIS/OTIF/EQUI-VOCAL — SIGMOD/PVLDB)**. 편입 값어치 top3: ①MIRIS/OTIF/EQUI-VOCAL related-work 인용(최고 ROI) ②Urbansas/R-LiViT 모달리티 확장(선택) ③HAWK/SurveillanceVQA 네이티브 QA(선택·보조). 배포형 파생 산출물에 안전한 라이선스는 R-LiViT·Urbansas·MIRIS·EQUI-VOCAL·SurveillanceVQA뿐.
- [정정 2026-07-28: S5 시점 "MIRIS는 related-work 인용용" 판정은 이후 갱신됨 — MIRIS는 실제 처리(`processed/miris_traffic/20260713`)를 거쳐 **실사용 8종(RQ5 부분 색인 교차검증)** 으로 승격되어 논문 표 1에 포함된다.]
- landscape는 종결 판정(2 sweep, venue·지역·모달리티 교차 커버). 새 후보는 대부분 (a)기존 소스 재주석 (b)단일모달 (c)ego/드론.

## 13. PI 확인 필요 / 미해결 사항

1. **UCA 질의 수 불일치**: canonical 135질의 vs 논문 RQ3 보고 129질의(3/4 재현). 135→129 제외 규칙을 재현 문서에 명시 필요. 인용은 논문 기준 129 우선.
2. **클립 정의 정합**: 2026-07-28 확정 "배포 mp4 1파일=1클립"과 522 로컬 원천이 사전 추출 JPG archive라는 실측 사이의 서술 정합(= "배포 영상 1편(video_id)=1클립"으로 읽는 각주) — 개정 원고 반영 필요.
3. **MEVA 961/985 카운트**: selection manifest 미작성 (§11-4).
4. **sinnaedoro manifest 결손**: §11-1·2 미완.
5. **MIRIS pg_dump 동결**: §11-3 미완. MIRIS 직접 인용 여부 재확인(§9-10).
6. **러닝 헤드 구제목 잔존**(p.7 이후): 재제출/개정 시 수정.
7. 2026-07-28 확정 용어('벡터 데이터베이스 계층', '증거' 치환)는 현 제출 PDF 미적용 — 향후 개정 원고·보고서에서만 사용.

---

# 제2부. 출처별 고유 내용 색인

각 원본에만 있던(또는 그 문서가 정본이던) 핵심 내용과 아카이브 경로. 통합본에 승계된 내용은 위 절 번호로 표시.

### S1 — 000_Datasets.md
아카이브: `.../archive/legacy_premerge_20260728/000_Datasets.md`
- **데이터셋별 실물 스키마 + 3행 샘플 데이터 전량** (522 sensor/annotation/documents/qrels, sinnaedoro frame_index·embeddings shape, MEVA predicate/activity, MIRIS `miris_frames2` 릴레이션 샘플, VRU metadata/documents/queries.jsonl, UCA metadata/captions/queries.jsonl) — 통합본 §5에는 요약만 승계, 실물 샘플은 아카이브가 정본.
- 물리 데이터 위치 선언(`/hdd2/KIISE_datasociety/Datasets` ↔ `Datasets` 심볼릭 링크) → §8.1.
- 멀티모달 강도 사다리 도식과 5단 분류 서술 → §3.1.
- 전체 규모·생산자 비교표(§4) → 통합본 §6 (S7 표와 동일 수치로 합본).

### S2 — 500_DATASETS_construction_noncircular_execution_20260710.md
아카이브: `.../archive/legacy_premerge_20260728/500_DATASETS_construction_noncircular_execution_20260710.md`
- Phase 0 T2/T3 트립와이어 실측표(is_weekend 폐기, 신호위상 분포) → §7.1.
- A6 감사 어서션 목록·희소 relevance 교체 이력(질의당 positive 3,349→219.6) → §7.2.
- T1 추출 실비용(py7zr 블록 seek, head 2.6s/mid 7.6s/tail 80.8s), solid 7z 판별, 전량 1-pass 추출 결정 — 이 문서에만 있음.
- 522 재발견 3건(JPG 프레임/동기 조인 90.2%/사람 주석 relevance) → §7.3.
- A9 VRU·지능형 collapse 표와 유의성 표 → §7.4 (RQ1 산출 이력).
- 32질의 최종 결과·확정 발견 5항, 32→85 사전선언 확장 규칙 4항, T3 곡선의 07-11/07-12 이중 정정 이력 → §7.5.
- 캡션 발사 로그(2-GPU 샤딩, 분당 ~18캡션, 로드 185s), 전 체인 스모크(부분 캡션 1,027 E2E), TS_4/VS_4 추출 수치(train_bbox 93,867/val_bbox 11,917) — 실행 세부는 아카이브가 정본.

### S3 — 680_DATASET_foundation_audit_20260713.md
아카이브: `.../archive/legacy_premerge_20260728/680_DATASET_foundation_audit_20260713.md`
- 확보·구축·확장 3질문 감사 프레임과 요약 판정("플래그십 rigor는 522 단일 의존" caveat) → §12.
- 원천/가공 디스크 실측치(external ~1.6T 세부) → §8.1.
- Q2 구축 적합성 표(데이터셋×논문 역할×A6 상태×공백 — "가장 약한 고리" 4항) — 세부는 아카이브 정본.
- 부록: 외부 추천 후보 7종 적대적 반증(TUMTraf-VideoQA/WTS/AICity2026 TAR/DAIR-V2X/TUMTraf-V2X/CityFlow-NL/AD군 — 전부 usable_now=false) 및 2-arm 프레이밍 교정 권고 → §12에 요약 승계.

### S4 — 690_DATASET_overseas_verify_extend_20260713.md
아카이브: `.../archive/legacy_premerge_20260728/690_DATASET_overseas_verify_extend_20260713.md`
- 36-finalist 3게이트(학회·확보·멀티모달) 검증 방법론과 채택 1/백업 8/탈락 27 비교표 전량.
- **MEVA 하드 검증 세부**: 라이선스 원문 URL(`mevadata.org/resources/MEVA-data-license.txt`), 무서명 S3 명령, KF1 ~330h/470GB, 주석 공개창 ~22h, 통합 레시피 6단계 → §12·§5.3에 요지 승계.
- MEVA 순환 리스크 금지 규칙(activity=relevance 전용) → §5.3 전량 보존.
- 신규 발굴 LUMPI/MEVID/QVHighlights 상세와 갈래 A/B 결정 프레임 → §12.
- 탈락 27종의 사유별 명단 전량 — 아카이브 정본.

### S5 — 730_DATASET_landscape_expanded_20260713.md
아카이브: `.../archive/legacy_premerge_20260728/730_DATASET_landscape_expanded_20260713.md`
- 카테고리 A–G 신규 발굴 표 전량(감시 VLM-QA/오디오-비주얼/노변 멀티센서/DB학회 벤치/차량ReID/사고·이상/한국 AI-Hub 신규) — 아카이브 정본.
- **MIRIS 최초 발굴 기록**(SIGMOD 2020, MIT) — 이후 실사용 승격의 출발점 [§12 정정 참조].
- 편입 값어치 top3와 라이선스 안전 목록(R-LiViT·Urbansas·MIRIS·EQUI-VOCAL·SurveillanceVQA) → §12.
- 커버리지 종결 판정(2 sweep 100+ 후보) → §12.

### S6 — 790_DATASET_TABLES_for_Notion_20260714.md
아카이브: `.../archive/legacy_premerge_20260728/790_DATASET_TABLES_for_Notion_20260714.md`
- **8개 데이터셋 파일 구성표 전량**(구성/실제 파일/내용/역할 4열) — 통합본 §8.4에는 요약만 승계, 전체 표는 아카이브 정본.
- 522 원천 zip 계열 명세(TL_* = 통과차량/보행량/도로차량/바운딩박스/큐보이드) → §5.1.
- MEVA storage-unit "522와 결과 반전 확인" 관찰 → §5.3.
- 보고서용 한 문장 3종(짧은 설명/정확한 설명/주의 표현) — 아카이브 정본.
- VRU·지능형의 v1(20260706)+수리판(20260710) 이중 경로 표기 → §8.2 규칙 2.

### S7 — DATA_PROVENANCE_raw_vs_derived_20260715.md
아카이브: `.../archive/legacy_premerge_20260728/DATA_PROVENANCE_raw_vs_derived_20260715.md`
- raw/①변환/②AI생성/③합성 구분 체계와 논리 계층 표 → §4 전량 보존.
- 실사용 8종/제외 2종 판정 기준("결과에 소비된 경우만") → §1 전량 보존.
- 근거 수준 5등급 표(디스크 실측/manifest/코드/원 배포문서/미완전) — 아카이브 정본.
- 계보 구조도 9종(.dot/.svg/.png)과 재생성 명령 → §4.2.
- 데이터셋별 상세 명세(§5)·정본 선택 규칙(§8.2)·정정 10항(§9)·윤리 8항(§10)·보완 과제 4항(§11) → 통합본에 전량 승계.
- 논문용 산문형 데이터셋 명세 5문단(§9.1–9.5) — 개정 원고 작성 시 아카이브에서 재사용(단, 2026-07-28 확정 용어와 UCA 129질의 정정을 반영해 갱신할 것).
