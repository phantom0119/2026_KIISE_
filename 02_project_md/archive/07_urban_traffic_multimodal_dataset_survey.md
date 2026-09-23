# 추가 조사: 도시 교통 CCTV·도로 안전 멀티모달 데이터셋

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 데이터셋 후보 조사와 2026-07-08 확보 메모는 유지하되, 최신 실행 결과로 AI Hub 다각도 CCTV answer-level VLM 실험과 시내도로 CCTV visual vector index benchmark가 완료되었다. 최신 종합 판정은 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 조사 범위

기존 `06_public_dataset_survey.md`는 도시 감시 전반을 다뤘다. 이 문서는 사용자가 요청한 대로 범위를 더 좁혀 다음 데이터만 우선 검토한다.

- 도시 CCTV, 교통 관제 CCTV, 교차로/횡단보도/국도/고속도로 카메라
- 보행자, 차량, 이륜차, 개인형 이동장치, 차로 위반, 신호 위반, 사고/near-miss
- 영상/이미지에 텍스트 설명, VQA, caption, CoT, 교통량/속도/신호/날씨/지도 메타데이터를 결합할 수 있는 데이터

자율주행 대시캠 데이터는 도메인이 조금 벗어나므로 fallback 또는 관련연구 후보로 낮춘다. 가장 좋은 데이터는 **고정형 CCTV 또는 roadside camera + 텍스트/VQA/grounding + 시공간 메타데이터**를 함께 갖는 데이터다.

## 현재 확보 및 저장 상태

2026-07-08 갱신: AI Hub 다각도 CCTV 생활안전 데이터, 시내도로 CCTV, 교차로신호체계, CityFlow-NL 원본 zip이 추가 확보되었다. 따라서 아래 조사 기록 중 “신청 필요” 또는 “승인이 오면 보강”이라는 표현은 2026-07-06 당시 판단이며, 최신 실험 판단은 `31_additional_dataset_need_review_20260708.md`와 `30_all_acquired_dataset_research_design_20260708.md`를 따른다.

연구 적합성 순위와 실제 확보 가능성은 분리해서 보아야 한다. 도시 CCTV/roadside 관점에서는 AI Hub 다각도 CCTV 생활안전 데이터, TUMTraffic-VideoQA, WTS가 더 강하다. 2026-07-08 현재 AI Hub 다각도 CCTV 생활안전 데이터는 `Datasets/external/21.다각도 CCTV 생활안전 데이터`에 확보 완료되어 본 연구의 main multimodal anchor가 되었다.

데이터 루트는 다음과 같다.

| 구분 | 경로 |
|---|---|
| 논리 경로 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets` |
| 물리 경로 | `/hdd2/KIISE_datasociety/Datasets` |
| 확보 현황 문서 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/08_dataset_storage_and_acquisition_status.md` |
| 운영 manifest | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/manifests/dataset_inventory_20260706.md` |

따라서 실제 2주 실험은 `AI Hub 다각도 CCTV 생활안전`을 main multimodal anchor로 삼고, `VRU-Accident`, `AI Hub 지능형 CCTV`, `시내도로 CCTV`, `교차로신호체계`, `CityFlow-NL`을 같은 스키마로 보강하는 방식이 가장 안전하다.

## 최종 우선순위

도시 교통 도메인만 기준으로 재정렬하면 다음 순서가 가장 좋다.

| 순위 | 데이터셋 | 왜 좋은가 | 리스크 |
|---:|---|---|---|
| 1 | AI Hub 다각도 CCTV 생활안전 데이터 | CCTV 기반, 비디오+텍스트+VQA+CoT, 이륜 이동수단 헬멧 미착용/인도주행/전동킥보드 등 교통 안전 이벤트 포함 | 확보 완료, main multimodal anchor |
| 2 | TUMTraffic/TUMTraf VideoQA | roadside traffic video, 85K QA, object captioning, spatio-temporal grounding, 날씨/이상상황 포함 | 국제 데이터, 실제 다운로드 절차 확인 필요 |
| 3 | WTS / AI City Track 2 | 고정 overhead view+ego view, pedestrian-centric traffic safety, dense description, VQA/captioning | challenge 접근 절차 |
| 4 | AI Hub 교차로 신호 체계·보행자·차량 이동 복합 데이터 | 교차로 CCTV 영상, 차량/보행량 CSV, 교통 신호/이동 데이터, 관제 서비스 맥락 | 텍스트/VQA 없음 |
| 5 | AI Hub 교통문제 해결용 CCTV 교통 영상(시내도로) | 시내도로 CCTV 505시간, bbox/tracking/segmentation, 날씨·시간대 분포 | 텍스트/VQA 없음, 안심존 가능 |
| 6 | AI Hub 교통사고 영상 데이터 | 사고대상·사고장소 라벨, 교차로/횡단보도/차대차/차대보행자 등 event label이 좋음 | 텍스트/VQA 없음 |
| 7 | InterAct VideoQA / UDVideoQA | 교차로 traffic monitoring VQA에 특화된 최신 데이터 | 공개/다운로드 상태 확인 필요 |
| 8 | VRU-Accident / RoadSocial | 도로 사고/road event VQA와 dense description이 강함 | CCTV 고정 관점과는 다름 |

2주 투고용으로는 **Plan A: AI Hub 다각도 CCTV 생활안전**, **Plan B: TUMTraffic-VideoQA 또는 WTS**, **Plan C: AI Hub 시내도로/교차로 CCTV + 합성 보고서**가 현실적이다.

## 국내: 도시 교통 CCTV·교차로 데이터

### AI Hub 다각도 CCTV 생활안전 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=71953 |
| 유형 | 텍스트, 비디오 |
| 규모 | 5,000건. 원천 1건은 서로 다른 각도 영상 2개 쌍, 개별 영상 10,000개 |
| 라벨 | VQA, 3단계 CoT reasoning, caption, event class |
| 교통 관련 이벤트 | 이륜 이동수단 헬멧 미착용, 이륜 이동수단 인도주행, 오토바이/자전거/전동킥보드 인도주행, 전동킥보드 2인 이상 주행 |
| 메타데이터 | filename, date, time, length, cctv_distribution, cctv_camera, cctv_angle, source, view 등 |
| 본 연구 적합성 | 최상. text-to-clip retrieval, text+metadata retrieval, evidence-aware VQA, multi-view retrieval 모두 가능 |

권장 사용법: 전체 11종 이벤트 중 교통 관련 subset만 분리해 **도시 교통 CCTV 생활안전 검색 워크로드**로 구성한다. 비교 실험은 `event class`, `date/time`, `camera angle/view`, `caption`, `question`을 이용하면 된다.

### AI Hub 교차로 신호 체계, 보행자, 차량 이동 복합 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=522 |
| 유형 | 교차로 영상, 정형 CSV, 도로차량/보행자 객체 라벨 |
| 규모 | 교차로 영상 36,549개, 통과차량 1,645,371개, 보행량 285,536개 |
| 라벨/메타데이터 | 통과차량, 횡단보도 보행량, 도로차량 포인트/폴리라인, bounding box, cuboid |
| 장점 | 교차로 CCTV, 차량/보행자/신호 체계가 한꺼번에 있어 metadata-aware retrieval 실험에 좋음 |
| 약점 | VQA/caption은 직접 생성해야 함 |
| 본 연구 적합성 | 높음. 교통량/보행량/신호 조건이 포함된 retrieval selectivity 실험에 유리 |

권장 사용법: `차량 많음`, `보행량 많음`, `정지 차량`, `역주행/돌발 가능 상황` 같은 템플릿 질의를 만들고, CSV 값을 metadata filter로 둔다.

### AI Hub 교통문제 해결을 위한 CCTV 교통 영상(시내도로)

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=165 |
| 유형 | 시내도로 CCTV 비디오/이미지 |
| 규모 | 총 505시간 동영상, 학습데이터 57만장 이미지 |
| 라벨 | detection 18만장, tracking 36만장, segmentation 3만장 |
| 메타데이터 | 악천후 영상 10% 이상, 시간대 새벽/오전/낮/밤, 차종 7종 |
| 장점 | 도시 교통 CCTV 원천으로 가장 직접적. 날씨·시간대 메타데이터가 명확 |
| 리스크 | AI Hub 안심존 절차 가능성, VQA/caption 없음 |
| 본 연구 적합성 | 높음. metadata selectivity stress test에 좋음 |

권장 사용법: `비 오는 밤 시내도로에서 오토바이가 포함된 장면`, `오전 출근시간 보행자와 대형버스가 함께 있는 장면`처럼 `weather/time/object class` 조합 질의를 만든다.

### AI Hub 교통문제 해결을 위한 CCTV 교통 영상(고속도로)

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=164 |
| 유형 | 고속도로 CCTV 비디오/이미지 |
| 규모 | 전국 50개 지점 고속도로 CCTV, 50만장 정제 이미지 |
| 라벨 | 차량 속도/교통량 측정용 AI 데이터 |
| 장점 | 고속도로 교통량/속도 분석, 관제 CCTV 맥락 |
| 약점 | 도시 교통보다는 고속도로. VQA/caption 없음 |
| 본 연구 적합성 | 중간. 시내도로 데이터 보조 또는 교통량 metadata 보강용 |

### AI Hub 교통사고 영상 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=597 |
| 유형 | 비디오, 이미지 |
| 규모 | 영상 21,895건, 이미지 3,284,250장 |
| 라벨 | 사고대상, 사고장소, bbox JSON |
| 교통 이벤트 | 차대차, 차대보행자, 차대자전거, 차대이륜차. 직선도로, 사거리교차로, 횡단보도, 회전교차로 등 |
| 장점 | event label과 location category가 좋아 retrieval qrels 생성이 쉬움 |
| 약점 | VQA/caption 직접 생성 필요 |
| 본 연구 적합성 | 높음. 사고/장소 조건부 retrieval에 강함 |

권장 사용법: `사거리교차로 신호등 있음`, `횡단보도 부근 차대보행자`, `직선도로 차대이륜차` 같은 구조화 질의 생성에 적합하다.

### AI Hub 국도 CCTV 영상을 통한 비정상주행 판별 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71566 |
| 유형 | 이미지 |
| 규모 | 약 2,117,886장 |
| 라벨 | bbox, polyline JSON |
| 이벤트 | 국도 CCTV 기반 비정상주행, 차선변경/차선물기 등 |
| 장점 | 교통법규·주행행태 이벤트를 만들기 좋음 |
| 약점 | 이미지 중심, 텍스트/VQA 없음 |
| 본 연구 적합성 | 중간~높음. 교통 안전 event filter용 보조 데이터 |

### AI Hub 교통법규 위반 상황 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71555 |
| 유형 | 이미지 |
| 규모 | 공공데이터포털 설명 기준 약 1,490,000장 |
| 이벤트 | 신호위반, 중앙선침범, 진로변경, 안전모 미착용 등 |
| 라벨 | polygon, box, polyline JSON |
| 장점 | 본 논문에서 "법규 위반 사건" class를 만들기 좋음 |
| 약점 | 영상/텍스트 부족 |
| 본 연구 적합성 | 중간. event label retrieval과 hard negative 구성에 유용 |

### AI Hub 교통법규 위반상황 데이터(업사이클링)

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71944 |
| 유형 | 텍스트, 이미지 |
| 생성 방식 | 합성데이터 |
| 장점 | 기존 교통법규 위반 데이터의 텍스트/이미지 업사이클링 버전이므로 멀티모달 검색에 더 잘 맞을 가능성 |
| 약점 | 신규 데이터라 실제 구조 확인 필요 |
| 본 연구 적합성 | 높을 수 있음. 접근 후 schema 확인 필요 |

### AI Hub 차로 위반 영상 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=628 |
| 유형 | 이미지 |
| 규모 | 80만건 이상 |
| 라벨 | 차선, 차량, 위반 여부 3개 class, segmentation JSON |
| 장점 | 차선 위반/전용차로 위반 event를 구성하기 쉬움 |
| 약점 | 영상/텍스트 없음 |
| 본 연구 적합성 | 중간. 교통 위반 event retrieval 보조용 |

### AI Hub 개인형 이동장치 안전 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=614 |
| 유형 | 이미지 |
| 도메인 | 개인형 이동장치, 도로교통, 보행안전 |
| 장점 | 다각도 CCTV 생활안전 데이터의 전동킥보드/이륜 이동수단 이벤트와 결합하기 좋음 |
| 약점 | 이미지 중심 |
| 본 연구 적합성 | 중간. PM safety class 보강용 |

### AI Hub 어린이 보호구역 내 등하교 및 시설물 영상 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71796 |
| 유형 | 텍스트, 이미지, 비디오 |
| 규모 | 2,103,741건 |
| 라벨 | bbox, segmentation, caption |
| 메타데이터 | CCTV/블랙박스, 맑음/흐림, 등교/하교/사고다발/야간 등 |
| 장점 | 보행자 안전, 어린이 보호구역, 날씨/시간대/상황 필터가 강함 |
| 리스크 | 어린이/보호구역 데이터라 접근·윤리 리스크 높음 |
| 본 연구 적합성 | 높지만 2주 실험에는 리스크 큼 |

### AI Hub CCTV 기반 차량정보 및 교통정보 계측 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71573 |
| 유형 | 이미지 |
| 규모 | 차량번호판 인식 1,001,657장, 차종외관 인식 1,007,219장 |
| 출처 | CCTV 녹화 영상 |
| 라벨 | bounding box JSON |
| 장점 | CCTV 기반 차량정보/교통정보 계측. 신호주기 생성, 미관측구간 교통흐름 예측과 연결 가능 |
| 약점 | 개인정보/번호판 비식별, 텍스트/VQA 없음 |
| 본 연구 적합성 | 중간. 객체/차종 metadata 보강용 |

### AI Hub 교통사고 모사 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71958 |
| 유형 | 3D, 텍스트 |
| 생성 방식 | 합성데이터 |
| 규모 | 교통사고 보고서 및 영상 1,500개, 라벨링 합성 데이터 300건, OpenDRIVE/OpenSCENARIO |
| 장점 | 사고 보고서와 시나리오 텍스트가 있어 report-to-scenario retrieval에 좋음 |
| 약점 | 실제 CCTV가 아니라 시뮬레이션/3D 중심 |
| 본 연구 적합성 | 보조. 합성 report와 사고 event schema 작성에 유용 |

## 국내 공개 포털·메타데이터 보강 데이터

| 데이터 | 위치 | 용도 |
|---|---|---|
| 성남시 교통약자 CCTV 이미지 데이터 | https://www.data.go.kr/data/100298956/linkedData.do | 교통약자 위치 라벨, 보행자 안전 class 보강 |
| 서울시 도시고속도로 CCTV 설치위치 | https://data.seoul.go.kr/dataList/OA-15273/F/1/datasetView.do | CCTV ID/좌표 metadata |
| VWorld 교통CCTV 속성정보 | https://www.vworld.kr/dev/v4dv_2ddataguide2_s002.do?svcIde=utiscctv | CCTV 위치/속성 metadata |
| 서울 TOPIS Open API | https://topis.seoul.go.kr/refRoom/openRefRoom_4.do | 속도/교통량/소통 metadata |
| 국토교통부 돌발상황정보 | https://www.data.go.kr/data/15040465/openapi.do | 사고/공사/통제/낙하물 event report |
| 기상청 단기예보 | https://www.data.go.kr/data/15084084/openapi.do | 날씨 filter |
| 표준노드링크 | https://www.data.go.kr/data/15025526/fileData.do | 도로 링크/노드 spatial join |

주의: 국내 포털 API는 원천 영상과 정확히 같은 카메라/시간으로 매칭되지 않을 수 있다. 이 경우 논문에서는 실제 운영 데이터 정합을 주장하지 말고, **metadata selectivity를 통제한 retrieval 구조 비교**로 사용해야 한다.

## 국제: 교통 CCTV·roadside·VideoQA 데이터

### TUMTraffic / TUMTraf VideoQA

| 항목 | 내용 |
|---|---|
| 위치 | https://traffix-videoqa.github.io/, https://arxiv.org/abs/2502.02449 |
| 유형 | roadside traffic video, MCQ QA, object captioning, spatio-temporal grounding |
| 규모 | 1,000 videos, 85,000 multiple-choice QA, 2,300 object captioning, 5,700 grounding annotations |
| 장점 | 본 주제의 retrieval, VQA, grounding을 모두 직접 지원 |
| 약점 | 한국 CCTV는 아니지만 roadside traffic scenario로 매우 근접 |
| 본 연구 적합성 | 최상. 국제 fallback 또는 비교 실험 1순위 |

권장 사용법: `QA question`을 query, `video/object caption`을 report/caption evidence, `grounding annotation`을 qrels로 변환한다. 국내 데이터 접근이 막히면 이 데이터 하나만으로도 논문 실험 구조를 만들 수 있다.

### WTS / Woven Traffic Safety Dataset

| 항목 | 내용 |
|---|---|
| 위치 | https://github.com/woven-visionai/wts-dataset, https://woven-visionai.github.io/wts-dataset-homepage/ |
| 유형 | pedestrian-centric traffic videos, fixed overhead camera + ego camera, dense description |
| 규모 | 1.2K+ staged video events, 130+ traffic scenarios. 2025 AI City 분석에 따르면 real-world pedestrian clips도 포함 |
| 장점 | fixed overhead camera가 있어 CCTV/관제 관점과 유사. pedestrian/vehicle behavior description이 강함 |
| 약점 | staged event 비중, challenge 접근 절차 |
| 본 연구 적합성 | 최상. 교통 안전 caption/retrieval 핵심 후보 |

### AI City Challenge Track 2

| 항목 | 내용 |
|---|---|
| 위치 | https://www.aicitychallenge.org/2025-track2/, https://www.aicitychallenge.org/2026-track2/ |
| 유형 | traffic safety captioning, VQA, multiple camera viewpoints |
| 2025 내용 | pedestrian accident 중심 fine-grained captioning, 사고 전 순간/정상 장면, location/attention/behavior/context 설명 |
| 2026 내용 | long-form captioning + VQA, pedestrian-involved accidents, multi-viewpoint |
| 장점 | 연구 동향 연결성이 매우 높음 |
| 약점 | challenge data access 필요 |
| 본 연구 적합성 | 최상. 관련연구와 실험 fallback 모두 가능 |

### AI City Challenge Track 3: Traffic Anomaly Reasoning

| 항목 | 내용 |
|---|---|
| 위치 | https://www.aicitychallenge.org/2026-track3/ |
| 유형 | transportation surveillance footage, anomalous event detection/reasoning/explanation |
| 장점 | 2026년 기준 "transportation surveillance footage"에서 설명 가능한 이상 이벤트 추론을 다룸 |
| 약점 | 2026 신규 track으로 데이터 접근·성숙도 확인 필요 |
| 본 연구 적합성 | 높음. 본 논문의 국제 동향/확장 방향에 매우 적합 |

### CityFlow-NL / AI City 2023 Natural Language Vehicle Retrieval

| 항목 | 내용 |
|---|---|
| 위치 | https://github.com/fredfung007/cityflow-nl, https://arxiv.org/abs/2101.04741 |
| 유형 | multi-camera vehicle tracks + natural language descriptions |
| 규모 | 2,498 vehicle tracks, 각 track 3개 자연어 설명, 530 query sets |
| 장점 | text-to-track retrieval이 이미 정의되어 있음 |
| 약점 | 사고/이상행동보다 차량 속성/이동 검색 중심 |
| 본 연구 적합성 | 높음. retrieval baseline 구현이 가장 쉬운 교통 CCTV 계열 |

### InterAct VideoQA

| 항목 | 내용 |
|---|---|
| 위치 | https://arxiv.org/abs/2507.14743, https://github.com/joe-rabbit/InterAct_VideoQA |
| 유형 | real-world traffic intersection VideoQA |
| 규모 | 8시간 교차로 영상, 10초 clip, 25,000+ QA pairs |
| 장점 | 교차로 traffic monitoring에 특화. 차량 상호작용, incident detection, spatiotemporal reasoning 포함 |
| 약점 | 최신 데이터라 다운로드와 라이선스 확인 필요 |
| 본 연구 적합성 | 높음. TUMTraffic-VideoQA 대체/보강 후보 |

### UDVideoQA

| 항목 | 내용 |
|---|---|
| 위치 | https://arxiv.org/abs/2602.21137, https://ud-videoqa.github.io/UD-VideoQA/UD-VideoQA/ |
| 유형 | city intersection traffic VideoQA |
| 규모 | 16시간 교통 footage, 1.7M frames, 28K QA pairs |
| 메타 | diverse traffic, weather, lighting conditions, privacy-preserving dynamic blur |
| 장점 | 실제 도시 교차로, 날씨/조명/동적 상호작용, reasoning taxonomy가 강함 |
| 약점 | 2026 신규 데이터. 접근성 확인 필요 |
| 본 연구 적합성 | 높음. 국제 최신 동향 근거로 매우 좋음 |

### TUMTraf V2X

| 항목 | 내용 |
|---|---|
| 위치 | https://tum-traffic-dataset.github.io/tumtraf-v2x/, https://github.com/tum-traffic-dataset/tum-traffic-dataset-dev-kit |
| 유형 | roadside + onboard camera/LiDAR, cooperative perception |
| 규모 | 2,000 labeled point clouds, 5,000 labeled images, 30K 3D boxes, track IDs, GPS/IMU |
| 장점 | roadside sensor 관점, traffic violations/near-miss/overtaking/U-turn 포함 |
| 약점 | 텍스트/VQA 없음 |
| 본 연구 적합성 | 중간~높음. metadata-rich infrastructure 데이터로 장기 확장에 좋음 |

### DAIR-V2X / V2X-Seq / Rope3D

| 데이터 | 위치 | 강점 | 약점 |
|---|---|---|---|
| DAIR-V2X | https://air.tsinghua.edu.cn/DAIR-V2X/english/index.html, https://github.com/AIR-THU/DAIR-V2X | vehicle-infrastructure multi-view/multi-modality, image+LiDAR, 2D/3D labels | VQA/text 없음 |
| V2X-Seq | https://github.com/AIR-THU/DAIR-V2X-Seq | sequential V2X, trajectories, vector maps, traffic lights | VQA/text 없음 |
| Rope3D | https://github.com/liyingying0113/rope3d-dataset-tools | roadside perception, 50K images, 1.5M 3D objects | VQA/text 없음 |

판정: 본 투고의 주 데이터보다는 관련연구 또는 metadata/schema 확장 근거로 쓰는 편이 좋다.

### SUTD-TrafficQA

| 항목 | 내용 |
|---|---|
| 위치 | https://sutdcv.github.io/SUTD-TrafficQA/, https://github.com/sutdcv/SUTD-TrafficQA |
| 유형 | traffic scene VideoQA |
| 규모 | 10,080 videos, 62,535 QA pairs |
| 장점 | 교통 VQA의 고전적 benchmark. QA 수가 많음 |
| 약점 | 고정형 CCTV/metadata보다는 in-the-wild traffic video QA |
| 본 연구 적합성 | 중간~높음. VQA fallback으로 유용 |

### RoadSocial

| 항목 | 내용 |
|---|---|
| 위치 | https://roadsocial.github.io/, https://huggingface.co/datasets/chiragp26/RoadSocial |
| 유형 | road event VideoQA from social videos |
| 규모 | 13.2K videos, 260K QA pairs, 414K social comments |
| 관점 | CCTV, handheld, drone 등 다양한 camera viewpoint |
| 장점 | road event QA와 hallucination robustness 실험에 강함 |
| 약점 | 소셜 비디오 기반이라 운영형 CCTV metadata는 약함 |
| 본 연구 적합성 | 중간~높음. road event VQA 보강용 |

### VRU-Accident

| 항목 | 내용 |
|---|---|
| 위치 | https://github.com/Kimyounggun99/VRU-Accident, https://huggingface.co/datasets/kyh9191/VRU-Accident |
| 유형 | dashcam accident video, VQA, dense description |
| 규모 | 1,000 accident videos, 6,000 MCQ QA, 1,000 dense scene descriptions |
| 장점 | 접근성이 좋고 VQA/description을 바로 retrieval evidence로 쓸 수 있음 |
| 약점 | 고정 CCTV가 아니라 대시캠 |
| 본 연구 적합성 | 중간. AI Hub 실패 시 빠른 fallback |

### DoTA / DADA-2000 / TU-DAT

| 데이터 | 위치 | 장점 | 약점 |
|---|---|---|---|
| DoTA | https://github.com/MoonBlvd/Detection-of-Traffic-Anomaly | 4,677 driving anomaly videos, temporal/spatial/category annotation | dashcam, text 없음 |
| DADA-2000 | https://github.com/JWFangit/LOTVS-DADA | 2,000 accident sequences, 54 accident categories, attention/accident annotation | dashcam |
| TU-DAT | https://www.kkant.net/TUDAT_description.html | roadside accident/anomaly videos, weather variety | 규모 작고 텍스트 없음 |

판정: 사고/이상상황 event label 보강용. 본 논문의 주 데이터보다는 hard negative 또는 관련연구 후보.

### 고정 교통 카메라 원천/추적 데이터

| 데이터 | 위치 | 강점 | 약점 |
|---|---|---|---|
| UA-DETRAC | https://arxiv.org/abs/1511.04136 | 100 traffic surveillance videos, 140K+ frames, vehicle bbox, illumination/type/occlusion | 텍스트/VQA 없음 |
| TRANCOS | https://gram.web.uah.es/data/datasets/trancos/index.html | public traffic surveillance camera images, vehicle counting | 이미지 1,244장으로 작음 |
| STREETS | https://databank.illinois.edu/datasets/IDB-3671567 | 4M+ images, 100 camera network, graph, incidents/counts | 텍스트/VQA 없음 |
| Bellevue Traffic Video Dataset | https://github.com/City-of-Bellevue/TrafficVideoDataset | 101시간, 5개 실제 교차로 traffic camera video | annotations 제한 |
| Traffic Signal Change Video Data | https://catalog.data.gov/dataset/traffic-signal-change-and-clearance-interval-pooled-fund-study-arizona-video-data | 신호 전환 구간 20초 교차로 영상, Arizona/Utah/Florida | VQA/text 없음 |

판정: DB 논문에서 "camera network metadata"나 latency 실험용 raw corpus로 유용하지만, 직접 논문 주 데이터로 삼기에는 텍스트 증거를 만들어야 한다.

## 실험 설계 관점의 데이터 매핑

| 태스크 | 최적 데이터 | 대체 데이터 |
|---|---|---|
| text-to-clip retrieval | 다각도 CCTV 생활안전, WTS, CityFlow-NL | TUMTraffic-VideoQA, InterAct |
| text+metadata retrieval | 다각도 CCTV 생활안전, 시내도로 CCTV, 교차로 복합 데이터 | TUMTraffic-VideoQA, UDVideoQA |
| report-to-frame/clip grounding | TUMTraffic-VideoQA, 지능형 관제 CCTV, WTS | 교통사고 영상 + 생성 보고서 |
| evidence-aware VQA | TUMTraffic-VideoQA, InterAct, UDVideoQA, SUTD-TrafficQA | VRU-Accident, RoadSocial |
| metadata selectivity stress test | 시내도로 CCTV, 교차로 복합 데이터, DLR-UT, STREETS | 다각도 CCTV 생활안전 |
| 다중 카메라 evidence bundle | 다각도 CCTV 생활안전, WTS, CityFlow-NL | TUMTraf V2X, DAIR-V2X |

## 2주 내 실행 권고

### 1안: 국내 교통 CCTV 중심

1. `다각도 CCTV 생활안전 데이터`에서 교통 관련 이벤트만 샘플링한다.
2. 부족한 교통량/날씨/시간 필드는 `시내도로 CCTV` 또는 `교차로 복합 데이터`의 metadata schema를 참고해 보강한다.
3. 실험 이름은 "도시 교통 CCTV 생활안전 검색 워크로드"로 잡는다.
4. VQA는 다각도 CCTV의 QA/CoT를 쓰고, retrieval 비교는 caption/question/event class 기반으로 한다.

장점: 국내 DBR 투고 맥락 최상.  
리스크: AI Hub 접근.

### 2안: 국제 roadside VideoQA 중심

1. `TUMTraffic-VideoQA`를 주 데이터로 쓴다.
2. QA를 query, object caption을 report, grounding annotation을 qrels로 변환한다.
3. WTS 또는 AI City Track 2를 관련연구/보조 실험으로 둔다.

장점: VQA/grounding/qrels가 이미 있어 가장 빠르게 논문 표가 나온다.  
리스크: 국내성은 약해지지만, 국제 연구 동향 부합성은 강하다.

### 3안: 교통 CCTV 원천 + 합성 보고서

1. `시내도로 CCTV`, `교차로 복합 데이터`, `교통사고 영상 데이터` 중 접근 가능한 것을 쓴다.
2. event label, weather/time/object class, location category로 template report를 생성한다.
3. 논문은 VQA보다 retrieval/metadata selectivity에 집중한다.

장점: 데이터베이스 연구 성격이 강하다.  
리스크: 텍스트 증거가 합성이므로 주장 강도를 낮춰야 한다.

## 결론

도시 교통 도메인으로 한정하면, 최종 후보는 다음처럼 정리된다.

1. **가장 주제에 맞는 국내 데이터**: AI Hub 다각도 CCTV 생활안전 데이터의 교통 안전 subset.
2. **가장 실험 완성도가 높은 국제 데이터**: TUMTraffic/TUMTraf VideoQA.
3. **가장 교통 CCTV다운 국내 원천 데이터**: AI Hub 교통문제 해결용 CCTV 교통 영상(시내도로) + 교차로 신호 체계/보행자/차량 이동 복합 데이터.
4. **사고/위반 이벤트 보강 데이터**: AI Hub 교통사고 영상, 교통법규 위반상황, 차로 위반, 국도 CCTV 비정상주행.
5. **관련연구와 국제성 강화 데이터**: WTS, AI City Track 2/3, CityFlow-NL, InterAct VideoQA, UDVideoQA.

따라서 논문 데이터 전략은 다음처럼 잡는 것이 가장 좋다.

> 국내 AI Hub 교통 CCTV 계열 데이터로 DB/metadata-aware retrieval의 국내성을 확보하고, TUMTraffic-VideoQA/WTS/AI City를 국제 멀티모달 교통 VideoQA 흐름의 비교 기준으로 배치한다.

이렇게 구성하면 기존 도시 감시 주제보다 더 좁고 선명한 제목을 쓸 수 있다.

권장 제목:

> 도시 교통 CCTV 멀티모달 데이터베이스에서 메타데이터 인지 하이브리드 검색 구조의 성능 분석

대체 제목:

> VLM 기반 교통 관제 질의응답을 위한 도시 CCTV 영상·사건·메타데이터 검색 워크로드 설계
