# 연구 데이터셋 계보 및 명세: 원본, 파생물, 워크로드, 실험 사용 범위

- 기준일: 2026-07-15
- 상태: 현재 DBR 제출 원고 `kiise_dbr_manuscript_v3_DBR_review_sample_based.md`와 로컬 디스크를 대조한 정본 후보
- 물리 데이터 루트: `/hdd2/KIISE_datasociety/Datasets`
- 논리 데이터 루트: 프로젝트의 `Datasets` 심볼릭 링크
- 범위: 현재 v3 원고에서 결과에 사용한 8종과 구축 후 제외한 2종
- 수치 원칙: 별도 표시가 없으면 2026-07-15의 파일, manifest, parquet 행 수 또는 PostgreSQL 행 수를 직접 확인한 값

> 핵심 결론: 원본은 외부에서 받은 영상 또는 프레임, 외부 주석, 센서/트랙 기록이다. 본 연구는 이를 ① 추출·파싱·임베딩, ② 생성형 모델 산출, ③ 합성·proxy 라벨로 구분해 파생했다. 다만 모든 데이터셋이 세 유형을 모두 갖는 것은 아니며, 검색 문서의 생산자도 데이터셋마다 다르다. 522·MEVA·UCA의 검색 문서는 Qwen2.5-VL 생성 캡션이고, VRU와 지능형 CCTV의 수리판 문서는 외부 데이터셋이 제공한 캡션이다.

## 1. 문서의 판정 범위와 근거 수준

이 문서에서 말하는 "본 연구에서 사용"은 현재 v3 원고의 표, 수치, 그림 또는 답변 실험에 실제로 소비된 경우를 뜻한다. 단순 다운로드, canonical 구축, 과거 v1 결과 생성만으로는 현재 연구에 사용한 것으로 세지 않는다. 이 기준에 따라 실사용은 8종이고, CityFlow-NL과 AI Hub 이상행동 CCTV는 현재 v3에서는 제외된 구축물이다.

근거 수준은 다음과 같이 구분한다.

| 표기 | 의미 | 예 |
|---|---|---|
| 디스크 실측 | 현재 파일 또는 DB 테이블을 직접 확인 | `.npy` shape, parquet 행 수, PostgreSQL `count(*)`, `du` |
| manifest 확인 | 빌드가 남긴 JSON/CSV 기록을 확인 | 모델 snapshot, seed, prompt hash, source path |
| 코드 확인 | 생성 스크립트의 입력·변환·출력을 확인 | 층화 표집, 프레임 선택, tseg 계산식 |
| 원 배포문서 | 로컬에 보관된 외부 README/LICENSE의 진술 | UCA 규모, MIRIS 영상 이용 제한 |
| 미완전 | 산출물은 있으나 recipe, seed, checksum 또는 원 입력 목록이 불충분 | sinnaedoro 1M 합성 파일 |

이 문서는 외부 원본 전체의 의미 정확도나 라벨 품질을 다시 사람 검수했다는 뜻이 아니다. "사람 주석", "모델 검출", "본 연구 생성"을 가능한 한 분리해 기록한다.

## 2. 용어와 파생 유형

### 2.1 논리적 데이터 계층

| 계층 | 정의 | 이 연구의 예 |
|---|---|---|
| 원본(raw) | 외부 제공자가 배포한 관측물과 주석을 내용 변경 없이 보관한 것 | MP4/AVI/JPG ZIP, 센서 CSV, CVAT/KPF/JSON 주석 |
| staging | 원본 archive를 풀거나 일부 파일을 임시 선별한 사본 | 522 `frames_src/`, 지능형 CCTV `Datasets/raw/.../20260706` |
| 파생(derived) | 연구 코드가 원본 또는 다른 파생물에서 계산한 것 | facet, canonical, caption, embedding, synthetic vector |
| 워크로드(canonical) | 검색 평가를 위해 clip/document/metadata/query/qrels 계약으로 조립한 것 | `canonical_trisource_expanded/` |
| 서비스 상태 | 파일이 아니라 DB 엔진에 적재된 가변 상태 | PostgreSQL `b3_frames`, `miris_frames2` |
| 결과(result) | 워크로드를 입력으로 실행한 측정·응답 | metrics CSV, VLM answer parquet, figure |

`Datasets/external`, `Datasets/raw`, `Datasets/restricted`는 물리 namespace이고 위의 논리적 분류와 일대일 대응하지 않는다. 예를 들어 522 원본은 `external`에 있고, VRU 영상 원본은 `raw`에 있으며, 지능형 CCTV는 `external` 원본에서 선별한 269개 쌍을 `raw`에 다시 staging했다. 따라서 논문에서는 폴더명보다 생산자와 변환 여부로 raw/derived를 판정해야 한다.

### 2.2 파생 유형

| 유형 | 정의 | 관측 사실과의 관계 | 대표 산출물 |
|---|---|---|---|
| ① 추출·파싱·임베딩 | 원본 내용을 선택, 구조화하거나 고정 모델로 특징화 | 원 관측에 근거한 비생성적 변환. GPU·라이브러리에 따라 부동소수점 비트 단위 동일성은 별도 보장 필요 | archive 해제 JPG, facet parquet, BGE-M3/CLIP vector |
| ② AI 생성 | 생성형 모델이 픽셀 또는 증거를 보고 새 텍스트를 작성 | 원본 라벨이 아니며 오류·누락·과언급 가능 | Qwen2.5-VL 캡션, 답변 실험의 VLM 응답 |
| ③ 합성·proxy | 실제 관측값을 재표본·교란하거나 분석자가 대리 라벨을 부여 | 실측 관측으로 해석하면 안 됨 | sinnaedoro 1M jitter vector, MIRIS `tseg` 24버킷 |

임베딩은 신경망 산출이지만 새로운 사건 서술을 생성하지 않으므로 본 문서에서는 ①로 분류한다. 반대로 canonical 조립은 여러 채널을 결합하지만 새로운 영상 관측을 만들지는 않으므로 역시 ①이다. 본 연구는 영상과 메타데이터를 하나의 joint vector로 학습하거나 생성하지 않았다.

## 3. 전체 계보 구조도

모든 그림은 왼쪽 위에서 `1. 외부 원본 파일 -> 2. 연구 처리 -> 3. 현재 디스크/DB 산출물 -> 4. 논문에서 실제 사용` 순서로 읽는다. 파란색은 외부 제공 파일, 녹색은 추출·파싱·임베딩, 노란색은 본 연구의 AI 생성, 주황색은 합성·proxy, 회색은 현재 materialized 저장물, 연노란색 또는 분홍색은 실험 입력과 결과를 뜻한다. 그림의 파일 수는 archive 또는 실제 파일 수, 행 수는 parquet/DB 레코드 수, `N x D`는 N개 벡터와 D차원을 뜻하므로 서로 같은 단위로 더하지 않는다.

### 3.1 8개 실사용 데이터셋 전체 지도

![본 연구 데이터셋 전체 계보](../paper_assets/20260715_dataset_provenance/dataset_lineage_overview.svg)

- 편집 원본: `paper_assets/20260715_dataset_provenance/dataset_lineage_overview.dot`
- PNG: `paper_assets/20260715_dataset_provenance/dataset_lineage_overview.png`
- 전체 지도는 데이터셋 사이의 역할 차이를 빠르게 비교하는 용도이고, 파일 내부 값과 변환 순서는 아래 상세도를 정본으로 삼는다.

### 3.2 522 tri-source 상세 지도

![522 tri-source 상세 계보](../paper_assets/20260715_dataset_provenance/dataset_lineage_522_trisource.svg)

- 편집 원본: `paper_assets/20260715_dataset_provenance/dataset_lineage_522_trisource.dot`
- PNG: `paper_assets/20260715_dataset_provenance/dataset_lineage_522_trisource.png`
- 522의 3,000문서 검색 트랙과 143,830프레임 색인 트랙은 같은 원본을 쓰지만 평가 단위와 임베딩이 다르다.

### 3.3 AI Hub 시내도로 상세 지도

![AI Hub 시내도로 real/synthetic 계보](../paper_assets/20260715_dataset_provenance/dataset_lineage_sinnaedoro.svg)

이 그림은 132,521개의 실제 JPG 기반 CLIP 벡터와 100만 합성 벡터를 분리한다. 100만 벡터는 실제 JPG 100만 장을 뜻하지 않는다.

### 3.4 MEVA 상세 지도

![MEVA 데이터 계보](../paper_assets/20260715_dataset_provenance/dataset_lineage_meva.svg)

원 AVI는 S3에서 일시 내려받아 중간 JPG를 만든 뒤 삭제된다. 따라서 로컬 7.6G와 processed 638M만으로 전체 영상 원본이 보존됐다고 해석하지 않는다.

### 3.5 MIRIS 상세 지도

![MIRIS 데이터와 PostgreSQL 계보](../paper_assets/20260715_dataset_provenance/dataset_lineage_miris.svg)

`nobj`는 YOLOv3 검출 객체수이고, `tseg`는 영상 내부 상대 위치 24버킷이다. 실제 시계 시각 또는 사람 객체수 정답이 아니다.

### 3.6 VRU-Accident 상세 지도

![VRU-Accident 수리판 계보](../paper_assets/20260715_dataset_provenance/dataset_lineage_vru.svg)

검색 문서 1,000개는 외부 VRU 배포가 제공한 dense caption이다. 수리판은 VQA-derived template 문서를 제거했지만 522와 같은 생산자 수준 tri-source는 아니다.

### 3.7 AI Hub 지능형 관제 CCTV 상세 지도

![AI Hub 지능형 관제 CCTV 수리판 계보](../paper_assets/20260715_dataset_provenance/dataset_lineage_intelligent_cctv.svg)

외부 archive에서 선별한 MP4/JSON 269쌍을 staging하며, 검색 문서는 JSON에 이미 있던 `event_caption`이다. 본 연구 VLM이 새로 생성한 캡션이 아니다.

### 3.8 UCA/UCF-Crime 상세 지도

![UCA UCF-Crime 계보](../paper_assets/20260715_dataset_provenance/dataset_lineage_uca.svg)

raw MP4는 1,950개지만 UCA 문장 주석과 연결되는 영상은 1,854개다. 주석 사건 구간에서 만든 6,432개 중간 JPG를 픽셀-only VLM 캡션의 입력으로 사용한다.

### 3.9 AI Hub 다각도 CCTV 상세 지도

![AI Hub 다각도 CCTV 계보](../paper_assets/20260715_dataset_provenance/dataset_lineage_multiangle.svg)

외부 JSON+template에서 만든 검색 문서 36,000개와 400사건의 시점별 evidence를 보고 생성한 VLM 답변을 분리한다. 후자는 데이터셋 원본이나 검색 문서가 아니라 평가 결과다.

### 3.10 그림 재생성

아래 명령은 9개 `.dot` 원본과 고해상도 PNG/SVG를 동일 내용으로 다시 만든다.

```bash
python3 2026_KIISE/paper_assets/20260715_dataset_provenance/generate_dataset_lineage_diagrams.py --dpi 180
```

그림의 문구나 수치를 바꿀 때는 생성 스크립트를 먼저 수정한 뒤 재생성한다. 자동 생성된 개별 `.dot`만 직접 고치면 다음 실행에서 덮어써진다.

## 4. 데이터셋 범위와 현재 상태

### 4.1 현재 v3 결과에 실제 사용한 8종

| 데이터셋 | 논리적 원본의 로컬 위치 | 원본/파생 크기 실측 | 현재 핵심 단위 | v3에서의 역할 |
|---|---|---:|---|---|
| AI Hub 522 교차로 | `Datasets/external/교차로신호체계` | 198G / 142G | 검색 3,000 clips, 색인 143,830 frames | 헤드라인 tri-source, filtered-ANN 코퍼스 B, 저장단위, 답변 파일럿 |
| AI Hub 시내도로(sinnaedoro) | `Datasets/external/교통문제 해결을 위한 CCTV 교통 영상(시내도로)` | 320G / 2.5G | real 132,521 vectors, synthetic 1M | filtered-ANN 코퍼스 A, 색인 Pareto, pgvector 부분색인 |
| MEVA | `Datasets/external/meva`와 원격 S3 AVI | 로컬 주석 7.6G / 638M | 985 clips, 193 queries | 검색 외적 타당성, 저장단위 비교 |
| MIRIS | `Datasets/external/miris` | 14G / 파일 4.0M + DB | DB 59,019 rows씩 2개 표 | 부분색인·hot/cold 정책 외적 타당성 |
| VRU-Accident | `Datasets/raw/VRU-Accident`, `external/VRU-Accident_hf` | 3.0G + 5.8G / 수리판 6.1M | 1,000 docs, 85 queries | 순환 붕괴 대조, 증거 사다리 |
| AI Hub 지능형 관제 CCTV | `external/지능형관제서비스CCTV영상데이터`, staging `raw/.../20260706` | 13G / 수리판 1.5M | 269 docs, 18 queries | 순환 붕괴 대조, 국내 이식성 |
| UCA/UCF-Crime | `Datasets/external/UCA_surveillance` | 194G / 176M | 6,432 docs, 135 queries | 영어 이상행동 검색 외적 타당성 |
| AI Hub 다각도 CCTV | `Datasets/external/21.다각도 CCTV 생활안전 데이터` | 483G / 426M | 4,500 events, 답변 표본 400 events | 다중 시점 evidence 선택 |

크기는 `du -sh`의 현재 파일시스템 값이다. MEVA 원 AVI는 프레임 추출 뒤 삭제되므로 7.6G는 주석 repository 중심의 로컬 보관량이다. MIRIS 파생 크기 4.0M은 hold-out query 파일만 반영하며 벡터 본체는 PostgreSQL에 있다.

### 4.2 구축됐지만 현재 v3 결과에서는 제외한 2종

| 데이터셋 | 현재 상태 | 제외 이유 |
|---|---|---|
| CityFlow-NL | `processed/cityflow_nl` 4.2M, annotation staging만 존재 | 프레임 0장, 다운스트림 소비자 0, 현재 qrels/A6 없음 |
| AI Hub 이상행동 CCTV | 외부 archive 573G, processed 71M, 과거 B0-B5 결과 존재 | v3가 결과를 소비하지 않으며 역할이 UCA로 대체됨. label XML 단일 계보로 tri-source 아님 |

이 두 데이터셋을 논문 데이터셋 표에 포함하면 "실험에 사용"과 "준비만 함"이 섞인다. 확보 자원 목록에는 넣을 수 있지만 결과 데이터셋 수에는 포함하지 않는 것이 맞다.

## 5. 데이터셋별 상세 명세

### 5.1 AI Hub 522 교차로 신호체계

**원본과 관측 단위.** 로컬 원본은 198G의 Training/Validation archive다. 이 데이터에서 시각 원천은 MP4가 아니라 이미 프레임으로 분해된 JPG archive다. `TS_3/VS_3`은 도로차량 주 트랙, `TS_4/VS_4`는 악천후·시간대 bbox 확장 트랙이다. 센서 기록은 `TL_1/2`, `VL_1/2`에 들어 있고, `TS_1/2`, `VS_1/2`의 로컬 파일은 미개방 placeholder다. 사람 주석은 CVAT XML 형식의 `TL_3/4`, `VL_3/4`이며, `TL_5/VL_5` 큐보이드도 staging됐지만 현재 relevance와 canonical에는 쓰지 않는다.

**① 추출과 파싱.** `extract_intersection_visual_sources.py`는 solid archive를 순차 해제한다. 주 트랙은 143,830 JPG와 52,462 visual-video 그룹이고, 별도 bbox 트랙은 105,784 JPG다. 따라서 `frames_src/` 전체를 "143,830장"이라고 부르면 틀리며, 143,830은 `train/`+`val/` 주 트랙만의 수다. 센서 CSV 파싱은 32,880 클립과 63개 교차로를 만들고, 시간·시간대·신호위상·통과 차량수와 그 3분위 `veh_density_bin`을 저장한다. 주석 파싱은 프레임 234,317행과 video 52,210개를 생성한다.

**교차카메라 결합.** 센서 클립은 카메라 코드 `x10`, 주 시각·주석은 `x11/x22`다. `visual_sensor_join.parquet`은 같은 교차로의 최근접 시각을 ±120초 창으로 조인하며 실측 조인율은 90.18%, gap 중앙값은 0초다. 이것은 같은 세션의 교차카메라 정렬이지 동일 프레임의 픽셀-센서 정합을 뜻하지 않는다. 악천후·시간대 `TS_4/VS_4`는 별도 촬영 캠페인이어서 센서 조인율이 0%이고 헤드라인 canonical에서 제외한다.

**② 문서 생성.** 조인 성공과 TL_3 보유를 조건으로 `intersection_id × time_of_day` 층화 표집을 수행하고, seed 20260710으로 3,000 video를 선택한 뒤 각 video의 중간 프레임 한 장을 Qwen2.5-VL-7B-Instruct에 넣었다. 모델 snapshot은 `cc594898...`, 디코딩은 greedy, 최대 110 토큰, prompt SHA-1은 `3b9d8d45127aba00c2d2c7d5bbd7da8aad1140c8`이다. 캡셔너 입력에는 센서와 CVAT facet이 들어가지 않는다. 이 3,000개 캡션은 외부 원본 문서가 아니라 본 연구의 AI 생성 검색 문서다.

**canonical과 두 실험 트랙.** 검색 canonical은 3,000 clips, 3,000 AI 캡션 documents, metadata 27,000행, 85 queries, strict qrels 6,809행, semantic qrels 24,872행이다. BGE-M3은 문서 3,000×1,024와 질의 85×1,024를 만든다. 별도의 색인 트랙은 주 트랙 전 프레임 143,830개를 CLIP ViT-B/32 512차원으로 임베딩한다. 검색 트랙의 문서 단위와 색인 트랙의 프레임 단위를 혼용하면 안 된다.

**비순환성의 정확한 의미.** predicate는 센서 CSV, relevance는 사람 CVAT 주석, document는 픽셀-only AI 캡션에서 나온다. A6 감사 6/6은 필터 키와 relevance 키의 분리, relevance의 metadata 미유입, 기계 토큰 누출 0건, 희소 relevance를 확인한다. 이는 계보 경로가 분리됐다는 뜻이지 세 채널의 현상 자체가 통계적으로 독립이라는 뜻은 아니다. 실제로 세 채널은 같은 교차로 교통상황을 관측하므로 자연 상관이 있고, 30개 조합의 Cramér's V 최대는 0.454다.

**정본 경로.** 검색 결과의 입력 정본은 `canonical_trisource_expanded/`다. `canonical/` 15질의와 `canonical_trisource/` 32질의는 과거 또는 선택편향 진단 버전이므로 헤드라인 85질의와 섞지 않는다.

### 5.2 AI Hub 시내도로 CCTV(sinnaedoro)

**원본과 real corpus.** 외부 320G JPG ZIP을 `build_sinnaedoro_visual.py`가 ZIP 내부에서 직접 읽고 위치·카메라·시간에 걸쳐 분산 표집한 뒤 CLIP ViT-B/32로 임베딩했다. 현재 `corpus_real/frame_embeddings.npy`는 132,521×512 float32이고, `frame_index.parquet`은 동일한 132,521행이다. 직접 확인한 facet cardinality는 location 39, camera 16,107, date 51이며, 1,000×512 hold-out query vector가 별도로 있다.

**③ 1M 합성.** `corpus_aug_1m.npy`는 1,000,000×512 float32, 2,048,000,128 bytes다. 프로젝트 실행 문서는 real vector 재표본과 jitter로 만들었다고 기록하며 색인 스케일 sweep에만 사용한다. 132,521 이하 real 구간과 그 이상의 synthetic 구간은 결과에서 분리해야 한다. synthetic 1M에서 관찰한 latency나 메모리 수치는 시스템 스케일 결과이지 실제 CCTV 100만 프레임의 분포·라벨 결과가 아니다.

**관리상 한계.** 현재 `corpus_real/`에는 빌드 manifest가 없고 원 입력 ZIP 목록과 정확한 실행 인자가 보존되지 않았다. `corpus_aug_1m.npy`에도 생성 스크립트, seed, jitter 분포, source-index map, checksum manifest가 없다. shape와 파일은 검증되지만 1M을 원점에서 동일하게 재생성하는 계보는 불완전하다. 논문 수치는 사용할 수 있으나 공개 재현 패키지에서는 이 결손을 명시하고 manifest를 보강해야 한다.

**실험 역할.** real 132,521은 실제 시공간 predicate를 사용한 filtered-ANN, FAISS 색인 Pareto, PostgreSQL `b3_frames` 부분색인에 쓰였다. synthetic 1M은 색인 구조의 크기 확장 전용이다. 이 데이터셋에는 검색 의미 qrels나 AI 캡션 문서가 없으므로 tri-source 검색 워크로드라고 부르지 않는다.

### 5.3 MEVA

**원본과 로컬 보관.** 외부 주석·문서는 `external/meva/meva-data-repo`에 있고 로컬 크기는 7.6G다. 영상은 공개 S3의 `drops-123-r13` AVI를 필요할 때 내려받아 중간 프레임을 추출한 뒤 삭제한다. 따라서 현재 로컬은 "원 AVI 전체 보관" 상태가 아니며, 재구축에는 원격 S3 접근이 필요하다. 로컬 MEVA LICENSE는 MEVA 데이터셋을 CC BY 4.0으로 명시하지만, 배포 전에 영상과 주석 각각의 최신 원문 조건을 다시 확인해야 한다.

**①/② 파생.** KPF/DIVA activity와 파일명·capture metadata를 파싱해 predicate(location, hour, time_of_day)와 relevance activity를 분리했다. 최종 코퍼스는 성공적으로 프레임과 캡션이 materialize된 985 clips다. 각 clip의 중간 프레임을 Qwen2.5-VL-7B-Instruct가 픽셀만 보고 영어 캡션으로 생성했다. canonical은 documents 985, metadata 3,940행, queries 193, strict qrels 4,405행, semantic qrels 17,205행이고 A6 overall pass다. BGE-M3 985×1,024와 CLIP 985×512가 저장돼 있다.

**비순환성과 한계.** predicate producer는 capture metadata, relevance producer는 DIVA activity annotation, document producer는 VLM이다. 구조상 A6를 통과하지만 522처럼 별도의 물리 센서가 있는 세 채널은 아니다. 따라서 MEVA는 비순환 프로토콜의 외적 타당성 arm이며, 독립 센서 tri-source 헤드라인은 522에 한정한다. 또한 `meva_facets_stats.json`은 activity-positive clip 961개를 보고하지만 최종 materialized corpus는 985개다. 실행 문서가 이를 "961 activity clips scale-up, 985 corpus"로 병기하므로, 논문에서는 985 최종 코퍼스만 규모로 사용하고 961과의 선택 규칙 차이는 추후 manifest에서 해소해야 한다.

### 5.4 MIRIS

**원본.** `external/miris/data` 14G에서 Warsaw와 Shibuya의 고정 교통 영상 12개만 사용하며 beach와 UAV는 제외한다. 원 배포 README에 따르면 JSON detection/track은 사람이 직접 단 모든 프레임 정답이 아니라, 사람이 표시한 bbox 예제로 학습한 YOLOv3 모델의 검출과 추적 결과다. 따라서 `nobj`를 "실제 차량수 ground truth"라고 부르면 과장이고, "원 배포 YOLOv3 JSON의 프레임별 검출 객체수"가 정확하다.

**① 임베딩과 실제 predicate.** `build_miris_pgvector_rich.py`는 6프레임 stride와 video당 최대 5,200장으로 60,019프레임을 CLIP ViT-B/32 512차원으로 임베딩한다. 이 중 1,000개는 hold-out query로 파일에 저장하고 59,019개를 PostgreSQL `miris_frames2`에 적재한다. `scene`은 Warsaw/Shibuya, `video`는 파일명 기반 12개 카메라-세션, `nobj`는 JSON 검출 객체수다.

**③ 시간 proxy.** `tseg`는 각 video에서 보존된 프레임 순서를 24등분한 0-23 위치 bucket이다. 실제 촬영 시각이나 hour-of-day가 아니다. 구형 `miris_frames` 표의 열 이름은 `hour`지만 계산법은 동일한 위치 bucket이므로 논문에서는 "hour"로 해석하지 않는다. 후속 `miris_frames2`가 이를 `tseg`로 바로잡았다.

**현재 저장 상태.** 2026-07-15에 PostgreSQL `miris_frames`와 `miris_frames2`가 각각 59,019행으로 존재한다. `pg_total_relation_size`는 각각 약 161.6MiB와 162.1MiB다. DB 데이터 디렉터리는 `Datasets/services/postgres_pgvector` bind mount에 있으나, portable dump나 parquet vector snapshot은 없다. `processed/miris_traffic/20260713`과 `20260714`에는 각 1,000×512 query vector만 남는다. 이 상태는 서버 volume 손상 시 원 영상을 다시 임베딩해야 하므로 장기 보존에는 부족하다.

**실험 역할.** MIRIS는 의미 검색 qrels나 캡션 코퍼스가 아니라, 실제 공간/내용 predicate와 시간 proxy를 가진 부분색인·hot/cold 정책 교차검증 코퍼스다.

### 5.5 VRU-Accident

**원본.** 영상 1,000개는 `raw/VRU-Accident`에 있고, 외부 Hugging Face 배포물은 `external/VRU-Accident_hf`에 있다. HF 배포는 1,000 dense captions와 6,000 VQA를 제공한다. 이 문서는 본 연구가 Qwen으로 생성한 캡션이 아니라 외부 데이터셋이 제공한 `dense_caption`이다. 원 배포가 각 caption을 어떤 절차로 만들었는지는 원 논문을 인용해 설명해야 한다.

**v1과 수리판.** v1 canonical은 외부 caption과 VQA 정답에서 만든 facet statement를 합쳐 documents 7,000, queries 244를 만들었고, filter·qrels·문서가 같은 VQA 계보를 공유해 순환성이 있었다. 수리판 `20260710_noncircular`은 facet statement를 제거해 dense caption 1,000개만 남기고, relevance를 accident_type, filter를 weather_light/road_type/location으로 분리했다. 최종은 clips/documents 1,000, queries 85, strict qrels 3,744, semantic qrels 9,703이다.

**한계와 역할.** filter와 relevance가 논리적으로 분리됐어도 모두 같은 외부 VQA 계보에서 파싱됐으므로 522의 생산자 수준 분리보다 약하다. A9 감사는 이 한계를 명시하고 결합도 V를 보고한다. 현재 v3에서는 순환 워크로드 붕괴 사례와 고정 LLM 증거 사다리의 앵커로 사용한다.

### 5.6 AI Hub 지능형 관제 CCTV

**원본과 staging.** 외부 데이터 13G에서 MP4 269개와 JSON 269개를 선별해 `raw/aihub_intelligent_cctv/20260706`에 staging했다. `clip_pairs.csv`가 media-label 쌍을 고정하며 missing media와 label은 0이다. JSON의 `event_caption`은 외부 라벨에 이미 포함된 문서이고 본 연구의 AI 생성 캡션이 아니다.

**v1과 수리판.** v1은 event_caption 외에도 event class를 그대로 쓰는 template statement를 생성해 documents 807, queries 133을 만들었고 순환 지표를 만들었다. 수리판은 외부 `event_caption` 269개만 남기고 relevance=event_class, filter=night/place_type으로 분리한다. 최종은 queries 18, strict qrels 584, semantic qrels 827이다.

**한계와 역할.** 문서·filter·relevance의 원천이 모두 같은 외부 JSON label producer이므로 완전 tri-source가 아니다. v3에서는 순환 붕괴와 수리 후 국내 CCTV 이식성의 소형 대조로만 사용한다.

### 5.7 UCA/UCF-Crime

**원본.** UCA 주석은 UCF-Crime 1,854영상, 23,542문장, 110.7시간을 대상으로 사건 문장과 시작·종료 시각을 제공한다. 로컬 원본은 194G다. UCA README는 Apache-2.0과 연구용 사용을 함께 적고, 기반 UCF-Crime 영상의 조건은 별도이므로 재배포 범위는 두 원천을 함께 검토해야 한다.

**①/② 구축.** 주석 구간에서 video당 최대 4개 사건 구간을 등간 표집하고 중간 프레임을 materialize해 6,432문서를 구성했다. 중복 `(video, midpoint)` 58건은 병합했고 frame drop은 0이다. Qwen2.5-VL-7B-Instruct는 픽셀만 입력받고, 정답 렉시콘을 넣지 않은 prompt로 6,432개의 AI 캡션을 생성한다. canonical은 queries 135, strict qrels 7,709, semantic qrels 41,435, metadata 19,296행이고 BGE-M3은 문서 6,432×1,024와 질의 135×1,024다.

**2.5채널 한계.** relevance는 사람 문장주석의 동결 렉시콘, predicate는 video class·container duration과 일부 annotation timing, document는 VLM 캡션이다. 독립 센서가 없고 어떤 프레임이 코퍼스에 들어가는지도 annotation event span에 의존한다. 따라서 522와 같은 물리 3채널이 아니라 2.5채널 외적 타당성으로만 보고한다. `event_position_bin`은 content-free timing이라도 UCA annotation producer에서 나와 채널-청정 대조에서 강등됐다.

### 5.8 AI Hub 다각도 CCTV

**원본과 canonical.** 483G ZIP 안에 4,500사건, 사건당 c1/c2 총 9,000영상, JSON 4,500개가 있다. canonical은 clips 4,500, views 9,000, evidence frame rows 27,000, label-derived documents 36,000, metadata 63,000, queries 4,572를 담는다. 이 36,000문서는 외부 JSON 필드와 template에서 만든 staging 문서이며, 본 연구의 픽셀-only Qwen 캡션 코퍼스가 아니다.

**답변 실험 파생.** 현재 핵심 실험은 전역 검색이 아니라 bbox 가시성 비대칭에 따라 고른 400사건이다. 각 사건의 두 시점에서 최대 3장씩, 총 2,400 evidence frame을 추출했고 오류는 0이다. Qwen2.5-VL, Qwen2-VL, InternVL3, Idefics2가 closed/worse/better/both 조건에서 생성한 답변은 ② AI 생성이지만 데이터셋의 검색 문서가 아니라 평가 결과다.

**한계와 역할.** 두 시점 프레임이 동일 시각의 완전 동기 pair라고 보장하지 않으며, better/worse는 bbox 면적 기반이다. 데이터셋은 다중 시점 evidence 선택 실험에 쓰이고 tri-source 검색 헤드라인에는 쓰지 않는다.

## 6. canonical 규모와 생산자 비교

| 데이터셋/트랙 | clip/frame | 검색 문서 생산자 | documents | queries | strict qrels | semantic qrels | embedding |
|---|---:|---|---:|---:|---:|---:|---|
| 522 검색 | 3,000 clips | 본 연구 Qwen2.5-VL | 3,000 | 85 | 6,809 | 24,872 | BGE-M3 1,024d |
| 522 색인 | 143,830 frames | 문서 없음 | - | image/query 실험별 | - | - | CLIP 512d |
| sinnaedoro real | 132,521 frames | 문서 없음 | - | vector query 1,000 | exact ANN GT | - | CLIP 512d |
| sinnaedoro synthetic | 1,000,000 vectors | 문서 없음 | - | 위 query 재사용 | exact ANN GT | - | 합성 CLIP-space 512d |
| MEVA | 985 clips | 본 연구 Qwen2.5-VL | 985 | 193 | 4,405 | 17,205 | BGE 1,024d + CLIP 512d |
| MIRIS rich | 59,019 DB frames | 문서 없음 | - | hold-out 1,000 | exact filtered ANN GT | - | CLIP 512d |
| VRU 수리판 | 1,000 clips | 외부 VRU dense caption | 1,000 | 85 | 3,744 | 9,703 | BGE-M3 1,024d |
| 지능형 CCTV 수리판 | 269 clips | 외부 JSON event_caption | 269 | 18 | 584 | 827 | BGE-M3 1,024d |
| UCA | 6,432 segments | 본 연구 Qwen2.5-VL | 6,432 | 135 | 7,709 | 41,435 | BGE-M3 1,024d |
| 다각도 canonical | 4,500 events | 외부 JSON + template | 36,000 | 4,572 | 18,000 | 없음 | 답변 실험은 frame 입력 |

## 7. 비순환성 수준 비교

| 수준 | 데이터셋 | 가능한 주장 | 금지할 주장 |
|---|---|---|---|
| 물리 3채널, 센서 포함 | 522 | 센서 predicate, 사람주석 relevance, 픽셀-only 생성문서가 파일·카메라·생산 경로 수준에서 분리 | 세 현상이 통계적으로 완전 독립, 동일 프레임 센서 정합 |
| A6 구조 분리, 센서 없음 | MEVA | capture metadata/activity annotation/VLM 문서의 논리적 생산자 분리 | 522와 같은 독립 센서 tri-source |
| 2.5채널 | UCA | 문장주석 relevance, 큐레이션/container predicate, VLM 문서 분리와 잔여 결합 공개 | 완전 3채널, annotation-free membership |
| 수리된 단일 외부 라벨 계보 | VRU, 지능형 CCTV | 문서 재진술 제거, filter/relevance 키 분리, 수리 전후 붕괴 | 생산자 독립 tri-source |
| 색인 코퍼스 | sinnaedoro, MIRIS | 실제 프레임 벡터와 predicate 하 filtered-ANN 평가 | 의미 검색 relevance나 캡션 검색 일반화 |
| 답변 전용 | 다각도 CCTV | 시점별 evidence 공급 조건의 짝지은 답변 비교 | tri-source 검색 또는 완전 동기 다시점 |

## 8. 저장·관리 구조

### 8.1 현재 물리 구조

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

### 8.2 정본 선택 규칙

1. 522 검색은 `canonical_trisource_expanded` 85질의를 정본으로 쓴다.
2. VRU와 지능형 CCTV 검색은 `20260710_noncircular`만 현재 수리판으로 쓴다. `20260706`은 순환 붕괴를 보이는 역사 대조다.
3. MEVA는 최종 985 clips/193 queries 결과만 사용한다. 276 clips/73 queries 파일럿 수치는 superseded다.
4. MIRIS의 실제 공간·내용 predicate 보고에는 `miris_frames2`와 `*miris2*` 결과를 우선한다. 구형 `miris_frames.hour`는 실제 시각으로 해석하지 않는다.
5. sinnaedoro `filtered_ann/filtered_ann.csv`는 구 random-mask 결과다. 실 predicate 정본은 `paper_assets/20260710_pillarB/filtered_ann_real_A.csv`다.
6. CityFlow-NL과 이상행동 CCTV는 확보·구축 목록에는 남기되 현재 v3 실사용 수에는 넣지 않는다.

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

## 9. 논문에 바로 쓸 수 있는 산문형 데이터셋 명세

아래 문단은 현재 v3의 범위를 보존하면서 데이터 계보를 명시하도록 작성했다. 참고문헌 번호와 AI Hub 데이터 식별자는 최종 bibliography에 맞춰 붙여야 한다.

### 9.1 데이터셋 전체 범위

본 연구는 하나의 데이터셋에 모든 실험을 강제로 결합하지 않고, 연구 질문별로 데이터 역할을 분리하였다. 검색 전략과 비순환성의 주 실험에는 AI Hub 522 교차로 데이터로 구축한 3,000-클립 tri-source 워크로드를 사용하였고, MEVA와 UCA를 검색 외적 타당성에 사용하였다. 초기 순환 워크로드의 진단과 수리 전후 비교에는 VRU-Accident와 AI Hub 지능형 관제 CCTV를 사용하였다. 색인·필터·배포 실험에는 AI Hub 시내도로 CCTV의 실제 프레임 임베딩 132,521개와 522 프레임 임베딩 143,830개를 주 코퍼스로 사용하고 MIRIS로 부분색인 정책을 교차검증하였다. 답변 계층에서는 VRU-Accident의 증거 사다리와 AI Hub 다각도 CCTV의 400-사건 다중 시점 표본을 사용하였다. CityFlow-NL과 AI Hub 이상행동 CCTV는 구축 산출물이 존재하지만 현재 원고의 결과에는 사용하지 않았다.

### 9.2 522 tri-source 구축

AI Hub 522 원본은 미리 추출된 교차로 JPG 프레임, 센서 CSV, CVAT 사람 주석으로 구성된다. 본 연구는 센서 카메라 코드 x10의 기록을 predicate 채널로, 시각 카메라 x11/x22의 CVAT 주석을 relevance 채널로 사용하고, 같은 시각 카메라 프레임만 입력받은 Qwen2.5-VL 생성 캡션을 document 채널로 사용하였다. 교차로와 시각을 기준으로 ±120초 내의 교차카메라 스트림을 조인한 결과 주 시각 video의 90.18%가 센서 클립에 연결되었고, 조인 시각 차의 중앙값은 0초였다. 조인 성공 및 주석 보유 video에서 교차로와 시간대를 층화해 3,000개를 표집하고 각 video의 중간 프레임을 캡션화하였다. 최종 canonical은 3,000문서, 85질의, strict qrels 6,809행과 semantic qrels 24,872행으로 구성되며, A6 감사에서 필터·정답·문서의 계보 분리 6개 조건을 모두 통과하였다.

### 9.3 파생물의 정직한 구분

본 연구의 파생물은 세 종류로 관리하였다. 프레임 archive 해제, 센서·주석 facet 파싱, canonical 조립, BGE-M3 및 CLIP 임베딩은 원 관측을 재표현하는 변환 산출물이다. 반면 522·MEVA·UCA의 검색 캡션은 Qwen2.5-VL이 픽셀을 보고 생성한 문장으로 외부 원본 라벨이 아니다. 이 때문에 문서와 정답의 직접 재진술을 차단할 수 있지만, 주차나 미세 활동을 놓치거나 부정 표현을 혼동하는 캡션 오류가 남는다. 또한 시내도로의 100만 벡터는 실제 132,521개 벡터를 재표본·jitter한 합성 스케일 코퍼스이고, MIRIS의 `tseg`는 실제 시계가 아니라 video 내 위치를 24등분한 proxy다. 두 산출물은 실제 관측 라벨과 분리해 시스템 규모 또는 배포 정책 실험에만 사용하였다.

### 9.4 외부·수리 워크로드

MEVA에서는 KPF/DIVA 활동주석을 relevance로, 촬영 위치·시각 metadata를 predicate로, 중간 프레임의 Qwen2.5-VL 캡션을 문서로 사용하여 985클립·193질의의 A6 통과 워크로드를 구성하였다. 다만 별도의 물리 센서가 없으므로 522와 동등한 센서 tri-source가 아니라 외적 타당성 arm으로 해석하였다. UCA에서는 사람 문장주석과 UCF-Crime 영상을 6,432개 구간 문서로 정규화하고 픽셀-only 캡션을 생성했지만, 독립 센서가 없고 코퍼스 membership이 주석 구간에 의존하므로 2.5채널로 보고하였다. VRU와 지능형 CCTV는 외부 제공 캡션만 남기고 라벨 재진술 문서를 제거한 수리판을 사용했으나, filter와 relevance가 동일 외부 주석 계보에서 나온다는 한계를 유지하였다.

### 9.5 색인과 답변 데이터

색인 실험의 시내도로 코퍼스는 실제 CCTV JPG에서 얻은 CLIP 512차원 벡터 132,521개와 위치·날짜·시각 facet으로 구성된다. 100만 벡터 확장은 실제 벡터의 합성 증강이며 실제 데이터 규모로 주장하지 않았다. MIRIS는 Warsaw와 Shibuya 고정 카메라 영상에서 60,019개 프레임을 임베딩한 뒤 1,000개를 질의로 유보하고 59,019개를 PostgreSQL에 적재하였다. 공간 predicate는 scene/video, 내용 predicate는 원 배포 YOLOv3 JSON의 검출 객체수이며, `tseg`는 video 내 상대 위치 bucket이다. 다각도 CCTV 답변 실험은 4,500사건 중 bbox 가시성 비대칭을 갖는 400사건을 선정하고 두 시점에서 총 2,400 프레임을 추출하여, 동일 모델 내 worse/better/both evidence 조건의 짝지은 답변 차이를 평가하였다.

## 10. 기존 문서 검토에서 확인된 정정·보완 사항

기존 문서는 522, sinnaedoro, MEVA, MIRIS의 핵심 raw/derived 구분을 올바르게 잡았으나 논문 명세로는 다음 보완이 필요했다. 이 문서에 수정 반영했다.

1. "검색 대상 문서는 전부 AI 생성"은 과잉 일반화다. 522·MEVA·UCA에는 맞지만, VRU와 지능형 CCTV 수리판은 외부 제공 caption을 사용한다.
2. 522의 주 시각 원본은 영상이 아니라 미리 추출된 JPG archive다. 여기서 ①은 video decoding이 아니라 archive 해제다.
3. 522 `frames_src/`에는 주 트랙 143,830장 외에 bbox 확장 트랙 105,784장이 함께 있다.
4. MEVA 원 AVI는 로컬에 보존되지 않고 중간 프레임 추출 뒤 삭제된다. 현재 7.6G를 전체 영상 원본 크기로 읽으면 안 된다.
5. MEVA의 "961 activity-positive"와 최종 "985 materialized corpus"는 서로 다른 카운트이므로 단일 규모처럼 섞지 않는다.
6. MIRIS `nobj`는 원 배포 YOLOv3 검출 결과이고 사람 차량수 정답이 아니다. `tseg`와 구형 `hour`는 실제 시계가 아니다.
7. MIRIS 벡터 본체는 파일이 아니라 PostgreSQL 표에만 있어 현재 관리가 서비스 상태에 의존한다.
8. 구조적 A6 tri-source는 MEVA도 통과하지만, 독립 센서까지 갖춘 물리 3채널은 522만이다.
9. sinnaedoro real corpus와 1M synthetic의 완전한 생성 manifest가 없어 공개 재현성에 결손이 있다.
10. 현재 v3 참고문헌 목록에는 본문에서 사용하는 MEVA와 MIRIS의 직접 인용이 보이지 않는다. 최종 투고 전에 원 논문·공식 데이터 배포 문헌을 bibliography에 추가해야 한다.

## 11. 공개·윤리·재현 시 주의사항

1. AI Hub, UCF-Crime/UCA, MIRIS 등은 원 영상 재배포 조건이 서로 다르다. 원본, 프레임, 임베딩, 캡션을 동일한 공개 가능 범주로 간주하지 않는다.
2. MIRIS 로컬 README는 제공 영상의 저작권을 보유하지 않으며 비상업 연구용으로만 제공한다고 명시한다. "MIRIS 전체가 MIT"라고 포괄 표기하지 않는다.
3. MEVA 로컬 LICENSE는 CC BY 4.0을 명시하지만 attribution과 원 영상 범위를 최종 배포 시 재확인한다.
4. UCA annotation license와 기반 UCF-Crime 영상 조건을 분리해 기록한다.
5. 생성 캡션에는 모델 snapshot, prompt hash, decoding, seed를 남기고 원본 사람 라벨과 같은 필드에 저장하지 않는다.
6. synthetic/proxy 산출물은 파일명, manifest, 결과표의 regime 열에서 real과 분리한다.
7. 원본 archive에는 SHA-256 inventory가 없으므로 장기 재현을 위해 dataset-level checksum registry가 추가로 필요하다.
8. 절대 물리 경로는 manifest에 기록돼 있어도 실행 계약은 `Datasets/...` 논리 경로를 사용한다.

## 12. 최소 보완 과제

논문 제출 전 데이터 설명의 정확성을 위해 다음 네 항목을 우선 보완하는 것이 좋다.

1. `sinnaedoro_traffic/corpus_real/build_manifest.json`을 소급 작성해 원 ZIP 목록, 표집 규칙, model snapshot, 실행 인자, 파일 SHA-256을 기록한다.
2. `corpus_aug_1m.npy`의 생성 코드 또는 재현 notebook을 복구하고 seed, jitter 분포, source row mapping, 품질검사 결과를 manifest로 고정한다.
3. PostgreSQL `miris_frames2`를 portable parquet 또는 `pg_dump`로 동결하고 schema, row count, vector model snapshot을 함께 보관한다.
4. MEVA 961/985 카운트 차이를 clip-level selection manifest로 설명하고, 최종 985 clip ID를 checksum과 함께 동결한다.

이 네 항목은 현재 측정값을 무효화하는 결함은 아니지만, 제3자가 원점에서 같은 데이터셋을 재구축할 수 있는가라는 재현성 질문에는 직접 영향을 준다.
