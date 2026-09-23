# 전체 확보 데이터셋 반영 연구 설계

작성 기준일: 2026-07-08

2026-07-09 최신 판정: 본 문서의 계층형 설계는 유지하되, 이후 실행 결과로 AI Hub 다각도 CCTV의 answer-level VLM view-selection 실험과 시내도로 CCTV 기반 index structure benchmark가 추가 완료되었다. 따라서 최신 상태는 "전체 확보 데이터셋을 공통 schema에 편입하는 설계"에서 한 단계 진행되어, `VRU/AI Hub 지능형 CCTV full pipeline + AI Hub 다각도 CCTV multi-view answer layer + 시내도로 CCTV ANN 색인 구조 벤치마크`가 논문 본문을 지탱하는 구조다. 최신 종합 판단은 `40_latest_dataset_and_experiment_synthesis_20260709.md`, 다각도 최종 결과는 `38_four_vlm_multiview_final_recheck_20260709.md`, 색인 구조 결과는 `39_index_structure_benchmark_results_20260709.md`를 따른다.

## 결론

새로 확보한 데이터셋은 모두 본 연구에 반영한다. 다만 모든 데이터를 동일한 깊이로 full visual embedding까지 돌리는 방식은 2주 투고 일정과 저장소 I/O 관점에서 위험하다. 본 연구의 설계 원칙은 다음처럼 고정한다.

> 모든 확보 데이터셋을 `공통 evidence database schema`에 편입하되, 데이터셋별 모달리티와 라벨 품질에 맞춰 main result, traffic CCTV extension, metadata/log extension, robustness extension으로 역할을 나눈다.

이렇게 하면 “데이터셋을 많이 모았다”가 아니라, “서로 다른 도시 감시 데이터 유형을 하나의 DB 검색 실험 체계로 통합했다”는 데이터베이스 논문다운 주장을 만들 수 있다.

## 연구 프레임 재정의

기존 본문은 VRU-Accident와 AI Hub 지능형 CCTV 2개를 true multimodal main으로 두었다. 새 데이터 확보 이후에는 다음 프레임으로 확장한다.

### 기존 프레임

```text
video clip + text label + metadata
  -> keyframe
  -> visual/text/metadata retrieval
  -> answer-ready evidence
```

### 확장 프레임

```text
heterogeneous urban surveillance assets
  - video clips
  - frame/image archives
  - object labels
  - tracking labels
  - NL vehicle-track queries
  - abnormal event XML
  - intersection traffic/pedestrian CSV
  - cuboid/bbox/road-object annotations

  -> canonical evidence database
       clips / frames / documents / metadata / queries / qrels
       zip:// and frame:// logical media URI
       visual evidence materialization policy

  -> retrieval strategies
       text-only
       visual-only
       metadata prefilter + visual
       text+visual fusion
       image-to-video / image-to-frame
       sensor/log metadata filtering

  -> service-level evidence packet
       frame or clip evidence
       timestamp or frame id
       camera/site metadata
       label/report text
       structured facets
```

핵심 기여 문장:

> 본 연구는 도시 CCTV/교통 데이터가 영상, 이미지 프레임, 자연어 설명, 객체 라벨, 교차로 로그처럼 서로 다른 형태로 축적될 때, 이를 공통 evidence database schema로 정규화하고 metadata-aware multimodal retrieval 구조가 데이터셋 유형별로 어떻게 작동하는지 분석한다.

## 데이터셋별 연구 역할

| 데이터셋 | 로컬 경로 | 모달리티 | 연구 내 역할 | 본문 사용 방식 |
|---|---|---|---|---|
| VRU-Accident | `Datasets/external/VRU-Accident_hf` | mp4, VQA, dense caption | 기존 교통 안전 video QA baseline | 기존 main 결과 유지, traffic safety reference |
| AI Hub 지능형 CCTV | `Datasets/external/지능형관제서비스CCTV영상데이터` | mp4, event JSON | 국내 CCTV event main | 기존 true multimodal main 유지 |
| AI Hub 다각도 CCTV 생활안전 | `Datasets/external/21.다각도 CCTV 생활안전 데이터` | multi-view mp4, Korean question/answer/caption/CoT, evidence JSON | multi-view evidence DB 및 answer-level view selection anchor | canonical 전체 구축, stratum 400 answer-level VLM 평가 |
| CityFlow-NL / AI City Track 2 | `Datasets/external/CityFlow-NL_repo`, `Datasets/external/cityflow_nl/aicity2023_track2` | AVI, vehicle tracks, NL queries | 국제 NL vehicle retrieval benchmark | track-level visual/text extension |
| 시내도로 교통 CCTV 원천 | `Datasets/external/교통문제 해결을 위한 CCTV 교통 영상(시내도로)` | JPG frame archives | visual vector index structure benchmark | real 132K CLIP corpus, 1M scale ANN benchmark |
| 시내도로 교통 CCTV 라벨/추가 | `Datasets/external/101.교통문제 해결을 위한 CCTV 교통 데이터(시내도로)` | JPG, JSON labels | 위 원천과 결합할 label source | bbox/segmentation/tracking metadata qrels |
| 교차로신호체계 | `Datasets/external/교차로신호체계` | CSV, 7z image/label archives | sensor/log + visual metadata extension | structured filter/selectivity experiment |
| 이상행동 CCTV | `Datasets/external/이상탐지/이상행동 CCTV 영상` | mp4, XML | cross-domain CCTV robustness | 생활안전 CCTV 보조 visual/text robustness |
| `07.지능형...` 중복본 | `Datasets/external/07.지능형 관제 서비스 CCTV 영상 데이터` | mp4, JSON | 중복 검증 evidence | 2026-07-08 삭제 완료. 실험 데이터로 중복 반영하지 않음 |

중복본은 “모두 사용” 대상에서 제외하고 2026-07-08 삭제 완료했다. 이유는 같은 데이터셋을 두 번 넣으면 표본 수를 부풀리는 평가 누수가 생기기 때문이다. 대신 중복 판정 결과를 데이터 관리 실험의 reproducibility/curation evidence로 기록한다.

## 연구 질문 확장

| RQ | 질문 | 사용 데이터셋 |
|---|---|---|
| RQ1 | metadata prefilter는 text/visual vector-only보다 도시 감시 evidence 검색을 안정화하는가? | VRU, 지능형 CCTV, 다각도 CCTV, 시내도로 CCTV, 이상행동 CCTV |
| RQ2 | image-to-video/image-to-frame 검색은 실제 CCTV evidence lookup으로 동작하는가? | VRU, 지능형 CCTV, 다각도 CCTV, CityFlow-NL, 시내도로 CCTV |
| RQ3 | 자연어 vehicle-track retrieval에서도 frame/crop materialization과 metadata filter가 효과적인가? | CityFlow-NL |
| RQ4 | 대량 이미지 archive + 별도 JSON 라벨 구조를 canonical DB schema로 편입할 수 있는가? | 시내도로 CCTV 원천 + `101...` 라벨 |
| RQ5 | 교차로 CSV/log와 영상/객체 라벨을 함께 다룰 때 metadata selectivity가 retrieval 후보 수와 품질을 어떻게 바꾸는가? | 교차로신호체계 |
| RQ6 | 생활안전 CCTV처럼 라벨 어휘가 강하게 정렬된 데이터에서도 sparse/hybrid와 visual evidence는 어떤 역할 분담을 하는가? | 이상행동 CCTV |
| RQ7 | 서로 다른 공개/승인형 데이터셋을 같은 DB workload로 통합할 때 병목은 모델보다 데이터 materialization, facet alignment, qrels construction인가? | 전체 |
| RQ8 | 같은 사건을 두 CCTV view로 관측할 때, view를 많이 쌓는 것과 더 좋은 view를 선택하는 것 중 무엇이 답변 정확도에 유리한가? | 다각도 CCTV 생활안전 |
| RQ9 | 대량 visual vector corpus에서 Flat, IVF, HNSW, IVF-PQ는 정확도·지연·메모리·빌드 비용을 어떻게 trade-off하는가? | 시내도로 CCTV |

## Canonical Schema 확장

기존 `clips/documents/metadata/queries/qrels`는 유지하되, 신규 데이터셋을 위해 frame-level evidence table을 명시적으로 추가한다.

### `frames.parquet`

| 컬럼 | 설명 |
|---|---|
| `frame_id` | 전역 frame ID |
| `clip_id` | 연결 clip 또는 sequence ID |
| `dataset_id` | 데이터셋 ID |
| `media_uri` | `zip://...!entry`, `frame://...`, 또는 실제 jpg/mp4 경로 |
| `source_archive` | 원천 zip/7z 경로 |
| `archive_entry` | 압축 내부 entry |
| `frame_index` | 영상 내 frame 번호 또는 이미지 sequence 번호 |
| `timestamp_sec` | 영상 기반이면 timestamp |
| `site_id` | 교차로/카메라/장소 ID |
| `camera_id` | camera identifier |
| `width`, `height` | 이미지 크기 |
| `materialized_path` | 실제 추출된 keyframe/crop 경로. 없으면 null |

### `objects.parquet`

| 컬럼 | 설명 |
|---|---|
| `object_id` | 객체 annotation ID |
| `frame_id` | frame 연결 |
| `clip_id` | clip/sequence 연결 |
| `class_name` | vehicle, pedestrian 등 |
| `bbox` | `[x1,y1,x2,y2]` |
| `track_id` | tracking label이 있으면 사용 |
| `segmentation_ref` | segmentation label이 있으면 참조 |
| `cuboid_ref` | cuboid label이 있으면 참조 |
| `source_label_uri` | JSON/XML/CSV label source |

기존 retrieval 스크립트는 `clips` 중심이므로, 신규 대량 이미지 데이터는 먼저 `frame-as-clip` 방식으로 canonical을 만든다. 이후 시간이 허용되면 `frames/objects` table을 별도로 사용한다.

## 데이터셋별 구체 실험 설계

### A. 기존 main: VRU + AI Hub 지능형 CCTV

목적:

- 이미 완성된 true multimodal retrieval 결과를 논문 backbone으로 유지한다.
- 새 데이터셋 추가로 논문 구조가 흔들리지 않도록 anchor 역할을 한다.

사용 실험:

| 실험 | 상태 | 본문 역할 |
|---|---|---|
| B0-B5 text/metadata | 완료 | baseline |
| M2/M4 visual text-to-video | 완료 | metadata prefilter 효과 |
| M5/M6 text+visual fusion | 완료 | multimodal fusion |
| IM1 image-to-video | 완료 | 이미지 질의 |
| service evidence packet | 완료 | answer-ready evidence |

본문 표현:

- “full visual pipeline이 완성된 anchor datasets”
- “다른 신규 데이터셋의 sample/extension 결과와 비교되는 기준선”

### B. CityFlow-NL: 자연어 vehicle-track retrieval

현재 상태:

- annotation repo 확보
- AI City 2023 Track 2 raw zip 확보 및 무결성 검증 완료
- zip 내부는 `vdo.avi`; annotation은 `img1/*.jpg` frame reference 사용
- 다음 작업은 AVI에서 representative frame/crop 추출

실험 단위:

| 항목 | 설계 |
|---|---|
| clip 단위 | vehicle track |
| visual evidence | track별 대표 frame 1-4개 또는 bbox crop |
| text evidence | `nl`, `nl_other_views` |
| query | train NL description 기반 query 6,465개 중 sample/full |
| qrels | query -> source track |
| metadata | split, scene_id, camera_id, frame range |

권장 구현:

1. 모든 frame을 추출하지 않는다.
2. track별 `frames` 중 first/mid/last 또는 bbox가 큰 frame을 1-4개 선택한다.
3. `vdo.avi`에서 해당 frame만 추출하고 bbox crop도 선택적으로 만든다.
4. CLIP/SigLIP image embedding을 track-level로 aggregate한다.
5. text query -> visual track, text query -> NL document, fusion 검색을 비교한다.

실험군:

| ID | 전략 | 목적 |
|---|---|---|
| C1 | text BM25/dense over NL documents | annotation text만 썼을 때 상한 |
| C2 | CLIP text -> visual crop/frame | 실제 multimodal retrieval |
| C3 | metadata prefilter(scene/camera) + visual | DB prefilter 효과 |
| C4 | text+visual RRF | NL document와 visual evidence 결합 |

핵심 주장:

- CityFlow-NL은 국제 benchmark 성격이 있어 “해외 연구 맥락”을 강화한다.
- 다만 challenge 규칙과 사전학습 데이터 이슈가 있으므로, benchmark leaderboard 성능 주장이 아니라 DB retrieval 구조 비교로 제한한다.

### C. 시내도로 교통 CCTV: 국내 도시 교통 이미지 검색 extension

대상 경로:

- 원천: `Datasets/external/교통문제 해결을 위한 CCTV 교통 영상(시내도로)`
- 라벨/추가: `Datasets/external/101.교통문제 해결을 위한 CCTV 교통 데이터(시내도로)`

현재 확인:

- 원천 zip 131개, JPG 483,882개
- 라벨/추가 zip 7개, JPG 31,200개, JSON 222개
- 두 경로는 중복이 아니며 함께 사용해야 한다.

실험 단위:

| 항목 | 설계 |
|---|---|
| clip/frame 단위 | 이미지 frame 또는 short sequence |
| visual evidence | zip 내부 JPG sample |
| text evidence | JSON label에서 object/site/task summary 생성 |
| query | “교차로/지점/객체/annotation type” 기반 자연어 질의 |
| qrels | 같은 label JSON이 가리키는 frame 또는 같은 sequence |
| metadata | split, task(Bbox/Segmentation/Tracking), site, sequence, object class |

왜 중요한가:

- 이 데이터셋이 본 연구의 도시 교통 CCTV 주장을 가장 직접적으로 강화한다.
- 기존 AI Hub 지능형 CCTV는 생활안전 이벤트 중심이고, VRU는 대시캠 성격이 있다. 시내도로 CCTV는 고정형 도로 CCTV 이미지라 도메인 적합성이 높다.

권장 workload:

| 규모 | 내용 | 이유 |
|---|---|---|
| pilot | label JSON 222개 전체 + 연결 가능한 source image sample | schema 파악과 qrels 생성 |
| paper-safe | site/task별 stratified 1,000-3,000 frames | 2주 내 visual embedding 가능 |
| appendix-scale | 10,000 frames | 시간이 남을 때 robustness |
| no-go | 483,882 JPG 전체 해제/임베딩 | 일정·I/O 리스크 과다 |

실험군:

| ID | 전략 | 목적 |
|---|---|---|
| U1 | metadata-only | site/task/object filter selectivity |
| U2 | image-to-frame | query image로 같은 sequence/site frame 검색 |
| U3 | text-to-frame visual | “cars at intersection”, “pedestrian crossing” 등 텍스트-이미지 검색 |
| U4 | metadata prefilter + visual | CCTV 운영 조건 결합 |
| U5 | label text + visual fusion | JSON label summary와 frame embedding 결합 |

본문 활용:

- “newly acquired urban-road CCTV extension”
- 기존 두 main dataset 결과와 같은 방향의 prefilter/fusion 효과가 나오는지 확인하는 외적 타당성 실험.

### D. 교차로신호체계: 구조화 로그/교차로 metadata extension

현재 상태:

- CSV 라벨 zip 일부는 바로 읽을 수 있음
- 큰 원천/라벨 일부는 실제 7z archive인데 `.zip` 확장자
- 22바이트 `(미개방).zip`은 empty placeholder
- 현재 시스템에는 `7z/py7zr` 없음

실험 단위:

| 항목 | 설계 |
|---|---|
| clip/frame 단위 | 교차로 site-time window |
| sensor/log evidence | 통과차량, 보행량 CSV |
| visual/object evidence | 도로차량, bbox, cuboid archive |
| query | 특정 시간/교차로/교통량/보행량 조건 |
| qrels | 조건을 만족하는 site-time row 또는 linked frame |
| metadata | site_id, timestamp, vehicle_count, pedestrian_count, object_count |

실험군:

| ID | 전략 | 목적 |
|---|---|---|
| I1 | structured metadata-only | DB filter/selectivity baseline |
| I2 | metadata + text report | CSV row를 자연어 report로 변환해 retrieval |
| I3 | metadata prefilter + visual/object sample | 7z 처리 후 가능 |
| I4 | cross-dataset filter transfer | 시내도로 CCTV site/time metadata와 유사 facet 비교 |

논문 내 역할:

- “멀티모달”을 영상+텍스트에 한정하지 않고, 도시 DB에서 중요한 sensor/log modality까지 확장한다.
- DB 논문으로서 강점이 커진다. 모델 성능보다 schema/facet/selectivity/query planning을 강조할 수 있다.

필요 리소스:

- `p7zip` 또는 `py7zr`
- 우선 CSV zip 4개만 사용해 metadata workload를 만들고, 7z visual archive는 후속 sample extraction으로 둔다.

### E. 이상행동 CCTV: cross-domain CCTV robustness

현재 상태:

- zip 24개 정상
- 내부 mp4 1,977개, XML 1,977개
- 기존 XML 기반 canonical/text baseline 구축 완료

실험 확장:

| 항목 | 설계 |
|---|---|
| visual sample | event category별 5-10개 mp4에서 keyframe 추출 |
| query | event/action/location/daypart 자연어 질의 |
| qrels | XML event/action facet 기반 |
| metrics | B0-B5, sample M2/M4, evidence packet coverage |

논문 내 역할:

- 도시 교통 주장을 직접 강화하지는 않지만, “감시형 CCTV 데이터 일반화”를 보여준다.
- 라벨 어휘가 질의와 강하게 정렬된 경우 sparse/hybrid가 강하다는 대조군 역할을 한다.

### F. 지능형 관제 CCTV 중복본

`07.지능형 관제 서비스 CCTV 영상 데이터`는 `지능형관제서비스CCTV영상데이터`와 byte-level 동일하여 2026-07-08 삭제 완료했다. 논문 실험에는 중복 투입하지 않는다.

사용 방식:

- 데이터 관리 감사 결과로만 사용한다.
- “동일 데이터 중복 저장은 evaluation sample duplication과 storage waste를 만들 수 있으므로 dedup audit를 수행했다”는 재현성 관리 근거로 쓴다.

## 통합 실험 매트릭스

| Dataset group | Raw coverage | Canonical | Text/metadata | Visual | Image query | Sensor/log | Paper table |
|---|---:|---:|---:|---:|---:|---:|---|
| VRU | 완료 | 완료 | 완료 | 완료 | 완료 | 없음 | main |
| AI Hub 지능형 CCTV | 완료 | 완료 | 완료 | 완료 | 완료 | 없음 | main |
| AI Hub 다각도 CCTV | zip 완료 | 신규 adapter 필요 | question/answer/caption/CoT 가능 | multi-view mp4 sample 가능 | 가능 | 없음 | main |
| CityFlow-NL | zip 완료 | annotation 완료 | 가능 | frame/crop 필요 | 가능 예정 | 없음 | extension |
| 시내도로 CCTV | zip 완료 | 신규 adapter 필요 | JSON label 가능 | JPG sample 가능 | 가능 | 없음 | extension main |
| 교차로신호체계 | zip/7z 완료 | 신규 adapter 필요 | CSV 가능 | 7z 필요 | 가능 예정 | 가능 | metadata extension |
| 이상행동 CCTV | zip 완료 | 완료 | 완료 | sample 필요 | 가능 예정 | 없음 | robustness |
| 중복 `07...` | 완료 | 불필요 | 불필요 | 불필요 | 불필요 | 없음 | dedup audit |

2026-07-08 실행 갱신: AI Hub 다각도 CCTV는 신규 adapter 구현과 canonical 변환, evidence frame materialization, bge-m3 text baseline, SigLIP visual baseline, service evidence packet 생성까지 완료했다. 세부 결과는 `32_aihub71953_multimodal_anchor_execution_20260708.md`를 기준으로 한다.

## 논문 구조 반영안

### 3장 데이터셋

표 1을 다음처럼 확장한다.

| 유형 | 데이터셋 | 역할 |
|---|---|---|
| Anchor video datasets | VRU, AI Hub 지능형 CCTV, AI Hub 다각도 CCTV | full true multimodal result |
| Urban traffic CCTV extension | 시내도로 CCTV + 101 label package | 국내 고정형 교통 CCTV extension |
| International NL retrieval | CityFlow-NL | natural language vehicle-track retrieval |
| Sensor/log extension | 교차로신호체계 | metadata/log selectivity |
| Robustness CCTV | 이상행동 CCTV | label-aligned CCTV robustness |
| Curation evidence | duplicate `07...` | dedup audit |

### 4장 방법론

기존 방법론에 다음을 추가한다.

- `zip://` logical media URI
- frame materialization policy
- stratified sampling policy
- dataset-specific adapter but common schema
- exact duplicate audit
- modality coverage audit

### 5장 실험 설계

full-scale 결과와 extension 결과를 분리한다.

| 계층 | 실험 | 조건 |
|---|---|---|
| Level 1 | completed full pipeline | VRU, AI Hub 지능형 CCTV |
| Level 2 | traffic CCTV sample extension | 시내도로 CCTV |
| Level 3 | benchmark track extension | CityFlow-NL |
| Level 4 | metadata/log extension | 교차로신호체계 |
| Level 5 | robustness extension | 이상행동 CCTV |

### 6장 결과

결과 표는 “한 표에 모든 것을 몰아넣지 않는다.” 다음처럼 나눈다.

| 표 | 내용 |
|---|---|
| Table A | modality/data coverage audit |
| Table B | full pipeline retrieval result |
| Table C | new dataset canonicalization success and sample workload size |
| Table D | traffic CCTV/CityFlow extension retrieval result |
| Table E | metadata/log selectivity result |
| Table F | storage/materialization cost and dedup result |

## 2주 일정 기준 실행 우선순위

모든 데이터셋을 논문에 반영하되, 실행 깊이는 차등화한다.

### Day 1-2: 신규 데이터셋 adapter audit

1. 시내도로 CCTV label JSON 222개 schema 분석
2. source JPG와 label JSON join key 탐색
3. CityFlow-NL representative frame extraction 스크립트 작성
4. 교차로 CSV 4개 zip schema 분석
5. 이상행동 CCTV visual sample 후보 추출

### Day 3-4: canonical sample workload 생성

| 데이터셋 | 목표 산출물 |
|---|---|
| 시내도로 CCTV | `Datasets/processed/urban_road_cctv/20260708/canonical_sample` |
| CityFlow-NL | `Datasets/processed/cityflow_nl/20260708/visual_sample` |
| 교차로신호체계 | `Datasets/processed/intersection_signal/20260708/canonical_csv` |
| 이상행동 CCTV | `Datasets/processed/aihub_abnormal_cctv/20260708/visual_sample` |

### Day 5-6: retrieval extension 실행

| 실험 | 데이터셋 | 목표 |
|---|---|---|
| U1-U5 | 시내도로 CCTV | 교통 CCTV extension 결과 |
| C1-C4 | CityFlow-NL | NL vehicle retrieval extension |
| I1-I2 | 교차로신호체계 | metadata/log selectivity |
| A-M2/A-M4 sample | 이상행동 CCTV | CCTV robustness visual sample |

### Day 7: 통합 분석

- 기존 main 결과와 extension 결과를 한 해석으로 묶는다.
- “모든 데이터셋에서 같은 결론”을 강요하지 않는다.
- 데이터셋별로 metadata/filter/visual/text의 역할이 달라진다는 DB 관점의 통찰을 정리한다.

### Day 8-10: 원고 반영

- 3장 데이터셋 표 확장
- 4장 canonical schema/materialization policy 추가
- 6장 extension 결과 추가
- 7장 한계에 full-scale 미실행 범위 명시

## 평가 지표

### Retrieval 품질

| 지표 | 사용처 |
|---|---|
| Recall@K | 모든 qrels 기반 검색 |
| MRR | rank-sensitive retrieval |
| nDCG@10 | graded qrels 또는 multiple positives |
| Hit@K | service evidence packet |

### DB/시스템 지표

| 지표 | 사용처 |
|---|---|
| candidate count after prefilter | metadata selectivity |
| materialized frame count | storage/I/O cost |
| zip read latency | archive-native retrieval cost |
| embedding build time | model/resource cost |
| duplicate bytes removed | data curation contribution |
| missing media/reference rate | dataset integrity |

### 데이터셋 적합성 지표

| 지표 | 설명 |
|---|---|
| modality coverage | visual/text/metadata/log/query/qrels 존재 여부 |
| label-to-media join rate | label이 실제 media와 연결되는 비율 |
| qrels construction success | query 생성 후 정답 target이 존재하는 비율 |
| evidence packet completeness | frame/timestamp/text/metadata를 모두 반환하는 비율 |

## 본문에서 강하게 주장할 수 있는 것

1. 서로 다른 도시 감시 데이터셋을 공통 evidence DB schema로 통합했다.
2. 대량 CCTV 원천은 전체 해제가 아니라 materialization policy와 logical URI로 관리해야 한다.
3. metadata prefilter는 text retrieval뿐 아니라 visual retrieval과 image retrieval에서도 중요한 query planning 수단이다.
4. 교통 CCTV/vehicle retrieval/log metadata/생활안전 CCTV는 서로 다른 modality imbalance를 가지므로, 단일 모델 성능보다 DB schema와 evidence selection이 중요하다.
5. 중복 데이터 감사와 미개방 placeholder 판정은 대량 데이터베이스 연구에서 재현성과 비용 통제의 일부다.

## 피해야 할 주장

1. 모든 1.2TB 데이터를 full visual embedding으로 처리했다.
2. 모든 신규 데이터셋에서 동일한 retrieval metric을 완전 비교했다.
3. 교차로신호체계의 7z 원천을 이미 처리했다.
4. `07...` 중복본을 별도 데이터셋처럼 넣어 표본 수를 늘렸다.
5. 생활안전 이상행동 CCTV 결과를 도시 교통 CCTV 성능으로 일반화했다.

## 즉시 구현해야 할 작업

| 우선순위 | 작업 | 산출물 |
|---:|---|---|
| 1 | 시내도로 CCTV JSON label schema profiler | label key inventory, join key 후보 |
| 2 | 시내도로 CCTV zip streaming sample canonical builder | `urban_road_cctv` sample canonical |
| 3 | CityFlow-NL AVI representative frame/crop extractor | track sample frames/crops |
| 4 | 교차로 CSV schema profiler | intersection CSV metadata canonical |
| 5 | 이상행동 CCTV visual sample extractor | category-balanced keyframes |
| 6 | 신규 데이터셋 extension 결과 표 생성 | paper asset table |
| 7 | 원고 3/4/6/7장 재작성 | DBR review manuscript update |

## 최종 설계 판단

모든 새 데이터셋을 연구에 넣는 것은 맞다. 단, 논문에서의 “사용”은 다음 세 가지 수준으로 나누어야 한다.

1. **Full result 사용**: 이미 full visual/text/metadata pipeline이 끝난 VRU와 AI Hub 지능형 CCTV.
2. **Extension result 사용**: 시내도로 CCTV, CityFlow-NL, 이상행동 CCTV에서 stratified sample 또는 representative frame 기반 검색 결과.
3. **DB/system evidence 사용**: 교차로신호체계와 중복 데이터 감사에서 schema, metadata selectivity, materialization cost, deduplication 결과.

이 설계가 가장 방어 가능하다. 데이터셋을 전부 반영하면서도, 2주 일정에서 실험 무결성을 잃지 않고, DB 논문으로서 “대량 멀티모달 데이터 관리와 검색 구조”라는 주제를 강화할 수 있다.
