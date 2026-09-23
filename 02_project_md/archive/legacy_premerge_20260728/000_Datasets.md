# 본 연구 데이터셋 종합 명세 (Datasets Master Specification)

* **작성일**: 2026-07-15
* **관리 경로**: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/000_Datasets.md`
* **물리 데이터 위치**: `/hdd2/KIISE_datasociety/Datasets` (로컬 프로젝트의 `Datasets` 심볼릭 링크와 연결됨)

---

## 1. 데이터셋 전체 요약 및 역할

본 연구에서 실험 및 검증에 사용하는 데이터셋은 핵심 tri-source 워크로드부터 외부 검증, DB 인덱스 검증, 답변 전파 실험까지 역할에 따라 총 8종의 실사용 데이터셋과 2종의 보류 데이터셋으로 구성됩니다.

| 구분 | 데이터셋 | 로컬 경로 | 본 연구에서의 역할 | 멀티모달 여부 | 멀티모달 정의 및 구성 요소 |
|---|---|---|---|---|---|
| **핵심** | AI Hub 522 교차로 신호체계 | `Datasets/external/교차로신호체계`<br>`Datasets/processed/aihub_522_intersection/20260710` | 주력 tri-source 워크로드 | **강함 (Flagship)** | 영상/프레임 + VLM 캡션 + 센서·시공간 metadata + 사람 주석 qrels가 물리적으로 분리되어 연결됨 |
| **외부검증** | MEVA (해외 감시) | `Datasets/external/meva`<br>`Datasets/processed/meva_kf1/20260713` | 해외 CCTV 외적 타당성 검증 | **강함** | CCTV 프레임 + VLM 캡션 + capture metadata + 사람 activity annotation 연결 |
| **DB 검증** | MIRIS (Warsaw/Shibuya) | `Datasets/external/miris`<br>`Datasets/processed/miris_traffic/20260713` | partial/local index 정책 교차검증 | 제한적 | 영상 프레임 embedding + 시간·장소 predicate (VLM-QA qrels는 미포함) |
| **색인 코퍼스** | Sinnaedoro traffic (시내도로) | `Datasets/processed/sinnaedoro_traffic` | 132K급 filtered ANN 및 index benchmark | 제한적 | 프레임 embedding + 시공간 predicate (exact top-k 대비 recall 평가 중심) |
| **보조** | UCA (UCF-Crime 기반) | `Datasets/external/UCA_surveillance`<br>`Datasets/processed/uca_anchor/20260712` | 영어 이상행동 외부 검증 | 중간 (2.5채널) | 영상 프레임 + VLM 캡션 + 사람 문장 주석 + container metadata 연결 (독립 센서 없음) |
| **보조** | VRU-Accident (수리판) | `Datasets/processed/vru_accident/20260710_noncircular` | 순환 붕괴 대조, 답변 evidence 실험 | 중간 | 사고 영상 + keyframe + caption/document + metadata + qrels (고정 CCTV/독립 센서는 없음) |
| **보조** | AI Hub 지능형 CCTV (수리판) | `Datasets/processed/aihub_intelligent_cctv/20260710_noncircular` | 순환 붕괴 대조, 국내 CCTV 이식성 | 중간 | CCTV clip + keyframe + 사건 caption + metadata + qrels |
| **보조** | AI Hub 다각도 CCTV | `Datasets/processed/aihub_multi_angle_cctv/20260708` | 다중 시점 evidence 선택 / VLM 답변 실험 | **강함** | 동일 사건의 다중 view + evidence frame + VLM 답변 결과 연결 |
| **보류/과거** | AI Hub 이상행동 CCTV | `Datasets/processed/aihub_abnormal_cctv/20260707` | 과거 text/metadata baseline 비교 | 제한적 | canonical + text/metadata baseline (v3 최종 핵심 주장에서는 보조 또는 보류) |
| **보류/과거** | CityFlow-NL | `Datasets/processed/cityflow_nl` | annotation staging 수준만 존재 | 없음 | 프레임 및 qrels 누락으로 최종 원고 및 실험 미사용 |

---

## 2. 멀티모달 강도 및 비순환성 수준 분류

본 연구에서는 평가 워크로드의 타당성을 확보하기 위해 데이터셋별 비순환성 수준을 다음과 같이 정의하고 통제합니다.

```
[완전한 Tri-Source (물리 3채널 분리)]
         │ (AI Hub 522)
         ▼
[외부 검증용 멀티모달 (소스 결합)]
         │ (MEVA)
         ▼
[2.5채널 멀티모달 (센서 없음)]
         │ (UCA)
         ▼
[검색/답변 보조 멀티모달]
         │ (VRU-Accident, 지능형 CCTV, 다각도 CCTV)
         ▼
[색인/DB 검증용 코퍼스]
           (MIRIS, Sinnaedoro)
```

1. **완전한 핵심 멀티모달 tri-source (AI Hub 522)**: 
   * **필터(Predicate)**는 센서 기록 CSV(카메라 10), **정답(Relevance)**은 사람 CVAT 주석 XML(카메라 11/22), **검색 문서(Document)**는 VLM(Qwen2.5-VL)이 픽셀 정보만 보고 생성한 캡션에서 파생하여 세 채널이 물리적·생산 경로 수준에서 격리되었습니다.
2. **외부 검증용 멀티모달 (MEVA)**: 
   * 영상 프레임, VLM 캡션, capture metadata, 사람 activity annotation이 유기적으로 연결되어 있으나 522처럼 별도의 물리 센서가 개입하는 구조는 아닙니다.
3. **2.5채널 멀티모달 (UCA)**: 
   * 영상, VLM 캡션, 사람의 사건 문장 주석이 있으나, 독립적인 메타데이터 센서 채널은 부재합니다.
4. **검색/답변 보조 멀티모달 (VRU, 지능형 CCTV, 다각도 CCTV)**: 
   * 영상 및 keyframe, 캡션, 메타데이터, qrels 또는 VLM 답변 데이터가 결합되어 있으나, 순환성 붕괴 진단 및 최종 QA 성능 파급 효과 규명을 위한 서브 테스트베드로 한정해 활용합니다.
5. **색인/DB 검증용 (MIRIS, Sinnaedoro)**: 
   * 대용량 벡터 임베딩과 시공간 predicate 조건 중심이며, VLM-QA용 자연어 질의 정답(qrels)은 다루지 않는 시스템 검증 전용 데이터셋입니다.

---

## 3. 데이터셋별 구체적인 데이터 스키마 및 예시 데이터 (3행 샘플)

각 데이터셋 내부의 실제 데이터 포맷, 속성명(Column), 데이터 유형(Type), 그리고 3행 수준의 구체적 값 샘플 명세입니다.

### 3.1 AI Hub 522 교차로 신호체계 (Flagship)
* **시각 모달리티 (Frame)**: 도로 교통 교차로 카메라(`cam 11` 또는 `cam 22`)에서 촬영 및 추출된 고해상도 JPG 이미지 단위 (1920×1080)
  * *예시 경로*:
    * `101011_2021090813495200_0001.jpg` (101011번 카메라, 2021-09-08 13시 49분 촬영 비디오의 1번째 프레임)
    * `102022_2021090908474418_0002.jpg` (102022번 카메라, 2021-09-09 08시 47분 촬영 비디오의 2번째 프레임)
    * `103011_2021090815345833_0003.jpg` (103011번 카메라, 2021-09-08 15시 34분 촬영 비디오의 3번째 프레임)

* **구조화 메타데이터 (sensor_facets.parquet) [P-series / Predicate]**
  * *설명*: 교차로 신호제어기 센서(`cam 10`) 및 시간 기록 기반 메타데이터 테이블 (Parquet 포맷)
  * *스키마 및 샘플 3행*:
    | video_id (string) | intersection_id (string) | date (string) | hour (int) | time_of_day (string) | n_vehicles (int) | sig_has_yellow (bool) | sig_has_pedestrian (bool) |
    |---|---|---|---|---|---|---|---|
    | `101010_2021090813495200` | `101010` | `2021-09-08` | `13` | `afternoon` | `36` | `True` | `False` |
    | `102010_2021090908474418` | `102010` | `2021-09-09` | `8` | `morning` | `44` | `True` | `True` |
    | `103010_2021090815345833` | `103010` | `2021-09-08` | `15` | `afternoon` | `127` | `False` | `True` |

* **사람 주석 메타데이터 (annotation_video_facets.parquet) [R-series / Relevance]**
  * *설명*: 인간 작업자가 교차로 비디오 프레임 속 객체의 궤적 및 정차/주차 상태를 레이블링한 XML 파싱 결과물
  * *스키마 및 샘플 3행*:
    | visual_video_id (string) | n_objects (int) | n_stopped (int) | n_parked (int) | n_bus (int) | n_bike (int) |
    |---|---|---|---|---|---|
    | `101011_2021090813495200` | `5` | `3` | `0` | `1` | `0` |
    | `102011_2021090908474418` | `18` | `12` | `2` | `0` | `3` |
    | `103011_2021090815345833` | `45` | `1` | `5` | `2` | `1` |

* **검색 문서 (documents.parquet) [VLM 캡션]**
  * *설명*: Qwen2.5-VL 모델이 비디오 중간 프레임의 픽셀만 보고 생성한 자연어 장면 묘사 텍스트
  * *스키마 및 샘플 3행*:
    | doc_id (string) | clip_id (string) | text (string) | lang (string) |
    |---|---|---|---|
    | `522:doc:vlm_caption:101011_2021090813495200` | `522:clip:101011_2021090813495200` | `"The image shows an urban intersection with moderate traffic volume. Visible vehicle types include cars and a bus. There are no parked vehicles."` | `en` |
    | `522:doc:vlm_caption:102011_2021090908474418` | `522:clip:102011_2021090908474418` | `"Moderate traffic at an urban intersection during morning hours. Several cars are stopped at the signal. A motorcycle is visible on the right."` | `en` |
    | `522:doc:vlm_caption:103011_2021090815345833` | `522:clip:103011_2021090815345833` | `"The frame captures a busy road junction with high vehicle density. A public transit bus and multiple trucks are traveling through the yellow phase."` | `en` |

* **적합성 평가 기준 (qrels.tsv) [Strict Qrels]**
  * *설명*: 검색 쿼리 ID와 정답 매칭 클립 ID를 정의한 파일 (TSV 포맷)
  * *스키마 및 샘플 3행*:
    | query_id (string) | target_id (string) | relevance (int) |
    |---|---|---|
    | `q_01` (Find parked bus during morning) | `522:clip:101011_2021090813495200` | `3` |
    | `q_01` (Find parked bus during morning) | `522:clip:102011_2021090908474418` | `3` |
    | `q_02` (Find trucks during yellow signal) | `522:clip:103011_2021090815345833` | `3` |

---

### 3.2 AI Hub 시내도로 CCTV (sinnaedoro)
* **시각 모달리티 (Frame)**: 시내도로 CCTV 영상에서 추출된 단일 이미지 프레임 단위 (JPG 포맷, 1920×1080)
  * *예시 경로*: `processed/sinnaedoro_traffic/frames/CAM_1021_000001.jpg`, `CAM_3045_000002.jpg`

* **구조화 메타데이터 (frame_index.parquet)**
  * *설명*: 프레임별 공간 위치, 카메라 세션 및 날짜 메타데이터 (Parquet 포맷)
  * *스키마 및 샘플 3행*:
    | frame_id (string) | location (string) | camera_id (string) | date (string) |
    |---|---|---|---|
    | `f_000001` | `L_01` (시내사거리) | `CAM_1021` | `2021-08-01` |
    | `f_000002` | `L_02` (중리삼거리) | `CAM_3045` | `2021-08-02` |
    | `f_000003` | `L_01` (시내사거리) | `CAM_1021` | `2021-08-01` |

* **임베딩 및 질의 데이터 (frame_embeddings.npy / queries.npy)**
  * *설명*: 132,521개의 실제 프레임 이미지 및 1,000개 쿼리 이미지를 CLIP ViT-B/32 모델로 부동소수점 임베딩한 결과물 (Numpy 포맷)
  * *실물 데이터 예시*:
    * `frame_embeddings.npy`: `shape=(132521, 512), dtype=float32` (L2 정규화 완료된 512차원 실수형 벡터)
    * `queries.npy`: `shape=(1000, 512), dtype=float32`

---

### 3.3 MEVA (해외 활동 감시 데이터)
* **시각 모달리티 (Frame)**: 고정 감시카메라 AVI 동영상에서 1-fps로 분할하여 추출된 JPG 이미지 파일 (1920×1080)
  * *예시 경로*: `processed/meva_kf1/20260713/frames/2018-03-07.10-55-00.10-59-59.admin.G329_0240.jpg`

* **구조화 메타데이터 (predicate_facets.parquet) [Predicate]**
  * *설명*: 비디오 촬영 장치 및 리그가 물리적으로 보존한 파일명과 촬영 메타데이터
  * *스키마 및 샘플 3행*:
    | clip_base (string) | date (string) | weekday (string) | hour (int) | time_of_day (string) | location (string) | camera (string) | modality (string) |
    |---|---|---|---|---|---|---|---|
    | `2018-03-07.10-55-00.10-59-59.admin.G329` | `2018-03-07` | `Wednesday` | `10` | `morning` | `admin` | `G329` | `EO` (일반광학) |
    | `2018-03-08.14-10-00.14-14-59.school.G341` | `2018-03-08` | `Thursday` | `14` | `afternoon` | `school` | `G341` | `EO` (일반광학) |
    | `2018-03-09.22-30-00.22-34-59.street.G502` | `2018-03-09` | `Friday` | `22` | `night` | `street` | `G502` | `IR` (열화상/적외선) |

* **인간 행동 주석 (activity_presence.parquet) [Relevance]**
  * *설명*: Kitware 배포 주석 YAML 파일에서 추출한 각 비디오 클립 내 특정 행동(37종) 발생 여부 (이진형 범주 및 카운트 수치)
  * *스키마 및 샘플 3행*:
    | clip_base (string) | person_enters_scene (int) | vehicle_turns_left (int) | person_opens_door (int) | vehicle_drops_off_person (int) |
    |---|---|---|---|---|
    | `2018-03-07.10-55-00.10-59-59.admin.G329` | `1` | `0` | `1` | `0` |
    | `2018-03-08.14-10-00.14-14-59.school.G341` | `0` | `1` | `0` | `1` |
    | `2018-03-09.22-30-00.22-34-59.street.G502` | `1` | `1` | `0` | `0` |

---

### 3.4 MIRIS (Warsaw/Shibuya 교차로 비디오)
* **시각 모달리티 (Video)**: 폴란드 바르샤바 및 일본 시부야 교차로 교통 감시 고정식 MP4 동영상 파일
  * *예시 경로*: `Datasets/external/miris/data/warsaw/videos/video1.mp4`, `shibuya/videos/video3.mp4`

* **관계형 DB 적재 명세 (miris_frames2 테이블) [DB 검증]**
  * *설명*: PostgreSQL pgvector 모듈에 적재되어 부분 색인 성능을 측정하는 가변 릴레이션
  * *스키마 및 샘플 3행*:
    | id (int) | scene (text) | video (text) | tseg (int) | nobj (int) | embedding (vector(512)) |
    |---|---|---|---|---|---|
    | `0` | `warsaw` | `warsaw_video1` | `5` (초반부) | `12` (YOLO 검출 객체수) | `[-0.01243, 0.05421, ..., -0.0091]` |
    | `1` | `shibuya` | `shibuya_video3` | `18` (후반부) | `38` (YOLO 검출 객체수) | `[0.02450, -0.00192, ..., 0.0841]` |
    | `2` | `warsaw` | `warsaw_video1` | `5` (초반부) | `15` (YOLO 검출 객체수) | `[-0.01301, 0.05114, ..., -0.0084]` |

---

### 3.5 VRU-Accident (수리판)
* **시각 모달리티 (Frame)**: 대시캠 사고 블랙박스 비디오 스트림에서 추출된 대표 keyframe 이미지 (JPG 포맷)
  * *예시 경로*: `Datasets/processed/vru_accident/20260710_noncircular/keyframes/0001_mid.jpg`

* **구조화 메타데이터 (metadata.parquet) [Predicate]**
  * *설명*: 사고 블랙박스 영상 주변 환경을 레이블링한 메타데이터 테이블 (Parquet 포맷)
  * *스키마 및 샘플 3행*:
    | clip_id (string) | dataset_id (string) | facet_name (string) | facet_value (string) | facet_role (string) |
    |---|---|---|---|---|
    | `vru:clip:0001` | `vru_accident` | `weather_light` | `sunny` | `predicate` |
    | `vru:clip:0001` | `vru_accident` | `road_type` | `urban` | `predicate` |
    | `vru:clip:0001` | `vru_accident` | `location` | `intersection` | `predicate` |

* **검색 문서 (documents.parquet) [텍스트]**
  * *설명*: 비디오 내용에 부합하는 차량 충돌 사고 묘사 상세 캡션
  * *스키마 및 샘플 3행*:
    | doc_id (string) | clip_id (string) | doc_type (string) | text (string) | lang (string) |
    |---|---|---|---|---|
    | `vru:clip:0001:doc:dense_caption` | `vru:clip:0001` | `dense_caption` | `"A black sedan is traveling straight when a motorcycle cuts in from the right junction causing a side-impact collision."` | `en` |
    | `vru:clip:0002:doc:dense_caption` | `vru:clip:0002` | `dense_caption` | `"In rainy weather, a delivery truck skids on the wet asphalt and collides with the guardrail at the highway exit."` | `en` |
    | `vru:clip:0003:doc:dense_caption` | `vru:clip:0003` | `dense_caption` | `"At night, a pedestrian crossing the road is struck by a speeding vehicle at the pedestrian crossing."` | `en` |

* **질의 및 필터 조건 명세 (queries.jsonl)**
  * *설명*: 자연어 질의문과 필터링 규칙이 담긴 JSON Lines 파일
  * *스키마 및 샘플 3행*:
    1. `{"query_id": "vru2:nofilter:0001", "query_text": "Find videos where the accident type is vehicle-to-motorcycle.", "metadata_filter": {}, "relevance_def": "accident_type"}`
    2. `{"query_id": "vru2:weather_light:0002", "query_text": "Find videos where the accident type is vehicle-to-motorcycle, restricted to weather light = rainy.", "metadata_filter": {"weather_light": "rainy"}, "relevance_def": "accident_type"}`
    3. `{"query_id": "vru2:road_type:0003", "query_text": "Find videos where the accident type is vehicle-to-object, restricted to road type = highway.", "metadata_filter": {"road_type": "highway"}, "relevance_def": "accident_type"}`

---

### 3.6 UCA (UCF-Crime 기반 이상행동)
* **시각 모달리티 (Frame)**: UCF-Crime 영상 내 사건이 발생하는 타임스탬프 구간에서 표집해 추출한 JPG 이미지 (1920×1080)
  * *예시 경로*: `Datasets/processed/uca_anchor/20260712/frames/Abuse001_mid.jpg`, `Arson012_mid.jpg`

* **구조화 메타데이터 (metadata.parquet) [Predicate]**
  * *설명*: ffprobe 동영상 세부 특성 및 UCA 주석 타임스탬프 기반 메타데이터 테이블 (Parquet 포맷)
  * *스키마 및 샘플 3행*:
    | doc_id (string) | dataset_id (string) | facet_name (string) | facet_value (string) | facet_role (string) |
    |---|---|---|---|---|
    | `uca:doc:0001` | `uca_ucfcrime` | `video_class` | `Arrest` | `predicate` |
    | `uca:doc:0001` | `uca_ucfcrime` | `video_duration_bin` | `(60, 180]` | `predicate` |
    | `uca:doc:0001` | `uca_ucfcrime` | `event_position_bin` | `mid` (동영상 내 이벤트 시점) | `predicate` |

* **VLM 캡션 (documents.parquet) [텍스트]**
  * *설명*: Qwen2.5-VL 모델이 생성한 범죄/사고 묘사 캡션
  * *스키마 및 샘플 3행*:
    | doc_id (string) | clip_id (string) | text (string) | lang (string) |
    |---|---|---|---|
    | `uca:doc:vlm_caption:0001` | `uca:clip:0001` | `"Two police officers are putting handcuffs on a suspect next to a patrol car."` | `en` |
    | `uca:doc:vlm_caption:0002` | `uca:clip:0002` | `"Flames and thick black smoke are rising from the window of a residential building."` | `en` |
    | `uca:doc:vlm_caption:0003` | `uca:clip:0003` | `"A crowd of people is running in panic down a hallway inside a shopping mall."` | `en` |

* **질의 및 필터 조건 명세 (queries.jsonl)**
  * *스키마 및 샘플 3행*:
    1. `{"query_id": "uca:video_class:0001", "query_text": "Find scenes where a weapon is visible.", "metadata_filter": {"video_class": "Arrest"}, "relevance_def": "weapon"}`
    2. `{"query_id": "uca:video_duration_bin:0002", "query_text": "Find scenes where people are fighting or hitting each other.", "metadata_filter": {"video_duration_bin": "(60, 180]"}, "relevance_def": "fight"}`
    3. `{"query_id": "uca:event_position_bin:0003", "query_text": "Find scenes where someone falls to the ground.", "metadata_filter": {"event_position_bin": "mid"}, "relevance_def": "falls"}`

---

## 4. 전체 데이터셋 규모 및 생산자/임베딩 비교 (종합)

| 데이터셋/트랙 | 물리적 클립/프레임 수 | 검색 문서의 기원/생산자 | 문서 수 (Docs) | 질의 수 (Queries) | strict qrels 행수 | semantic qrels 행수 | 임베딩 사양 |
|---|---:|---|---:|---:|---:|---:|---|
| **522 검색 트랙** | 3,000 clips | 본 연구 Qwen2.5-VL 생성 | 3,000 | 85 | 6,809 | 24,872 | BGE-M3 (1,024d) |
| **522 색인 트랙** | 143,830 frames | (문서 없음) | - | - | - | - | CLIP ViT-B/32 (512d) |
| **Sinnaedoro real** | 132,521 frames | (문서 없음) | - | 1,000 | exact ANN GT | - | CLIP ViT-B/32 (512d) |
| **Sinnaedoro synthetic**| 1,000,000 vectors| (문서 없음) | - | 1,000 | exact ANN GT | - | 합성 CLIP-space (512d) |
| **MEVA** | 985 clips | 본 연구 Qwen2.5-VL 생성 | 985 | 193 | 4,405 | 17,205 | BGE-M3 (1,024d) + CLIP (512d) |
| **MIRIS rich** | 59,019 DB frames | (문서 없음) | - | 1,000 | exact filtered GT | - | CLIP ViT-B/32 (512d) |
| **VRU 수리판** | 1,000 clips | 외부 VRU dense caption | 1,000 | 85 | 3,744 | 9,703 | BGE-M3 (1,024d) |
| **지능형 CCTV 수리판** | 269 clips | 외부 JSON event_caption | 269 | 18 | 584 | 827 | BGE-M3 (1,024d) |
| **UCA** | 6,432 segments | 본 연구 Qwen2.5-VL 생성 | 6,432 | 135 | 7,709 | 41,435 | BGE-M3 (1,024d) |
| **다각도 canonical** | 4,500 events | 외부 JSON + 템플릿 파생 | 36,000 | 4,572 | 18,000 | - | (답변 실험은 프레임 입력) |

---

## 5. 본 연구 데이터셋들의 멀티모달성 판단 기준

본 연구의 데이터셋들은 단순히 비디오나 이미지를 단순 나열한 것이 아니며, 아래의 다차원 정보가 스키마 수준에서 조인되고 벡터화되어 처리되므로 완벽한 **멀티모달 데이터베이스 벤치마크**의 요건을 충족합니다.

* **시각 모달리티**: 실제 원천 영상 파일 및 시간축에서 정렬·추출된 keyframe 이미지군 (`frames/`, `keyframes/`, `frame_embeddings.npy` 형태로 materialize)
* **텍스트 모달리티**: 이미지 픽셀 정보만을 입력받아 off-line으로 작성된 VLM 장면 설명, 외부 도메인 특화 서술문, 자연어 질의문 (`documents.parquet`, `queries.jsonl`)
* **구조화 메타데이터**: 시간대, 타임스탬프, 물리 신호 제어 주기(신호등 상태), 도로 기하구조, 차량 및 보행자 밀도 등의 관계형 속성 테이블 (`metadata.parquet`, `sensor_facets.parquet`, `predicate_inventory.csv`)
* **정합 평가 데이터**: 모델의 편향적 레이블을 방지하기 위해 물리 카메라 채널이나 사람 전문가 주석에서 유도된 질의응답 정답셋 (`qrels.tsv`, `qrels_semantic.tsv`)
