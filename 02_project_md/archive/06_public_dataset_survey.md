# 공개 데이터셋 조사: 도시 감시형 멀티모달 VLM-DB 연구용

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 이 문서는 데이터셋 후보 조사 기록으로 보존한다. 실제 확보 상태는 이후 크게 진전되어 AI Hub 다각도 CCTV 생활안전, 시내도로 CCTV, 교차로신호체계, CityFlow-NL까지 확보되었고, 최신 실험 반영 범위는 `30_all_acquired_dataset_research_design_20260708.md`와 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 조사 목적

`01_topic_selection_rationale.md`의 최종 주제는 다음 문제를 다룬다.

> 이미지/영상, 사건 보고서, 센서·시공간 메타데이터가 결합된 도시 감시 데이터에서 VLM 질의응답을 지원하려면 어떤 저장·색인·검색 구조가 정확도, 지연시간, 비용을 가장 잘 균형화하는가?

따라서 좋은 데이터셋은 단순히 영상이 많은 것보다 다음 조건을 많이 만족해야 한다.

| 기준 | 의미 |
|---|---|
| 영상/이미지 | CCTV, 교통 카메라, 대시캠, 다중 시점 영상 |
| 사건 라벨 | 침입, 배회, 싸움, 사고, 침수, 비정상 주행 등 |
| 텍스트 증거 | caption, QA, CoT, dense description, 사건 설명 |
| 메타데이터 | 시간, 장소, 카메라, 시점, 날씨, 도로/교차로, 센서값 |
| grounding | 구간 태깅, bbox, segmentation, temporal span, track |
| 접근성 | 즉시 다운로드, AI Hub 신청, 안심존, challenge 신청 여부 |

## 현재 확보 및 저장 상태

대용량 데이터는 `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets`에서 관리한다. 이 경로는 실제로 `/hdd2/KIISE_datasociety/Datasets`를 가리키는 symlink다.

현재 원본까지 확보된 데이터는 `VRU-Accident`이며, 영상 1,000개, VQA 6,000건, dense caption 1,000건을 로컬에서 검증했다. 세부 경로와 제한 데이터셋 신청 상태는 다음 문서를 기준으로 한다.

- [08_dataset_storage_and_acquisition_status.md](/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/08_dataset_storage_and_acquisition_status.md)
- [dataset_inventory_20260706.md](/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/manifests/dataset_inventory_20260706.md)

## 최종 권장 조합

2주 안에 논문 실험을 완성하려면 다음 순서가 가장 안전하다.

| 우선순위 | 데이터 | 판단 |
|---:|---|---|
| 1 | AI Hub 다각도 CCTV 생활안전 데이터 | 본 주제와 가장 직접적으로 일치. 비디오+텍스트+VQA+CoT+다중 시점+메타데이터가 있음 |
| 2 | AI Hub 지능형 관제 서비스 CCTV 영상 데이터 | 300건으로 작지만 실제 CCTV, 구간태깅, 캡션 JSON이 있어 파일럿에 좋음 |
| 3 | AI Hub 이상행동 CCTV 영상 | 국내 CCTV 이상행동 대규모 원천. 텍스트 증거는 직접 생성해야 함 |
| 4 | VRU-Accident | Hugging Face/GitHub 접근성이 좋고 VQA/dense description이 있어 즉시 실험 fallback에 좋음 |
| 5 | WTS / AI City Challenge Track 2 | 다중 시점 교통 안전 caption/VQA 연구와 직접 연결. 신청 또는 다운로드 절차 확인 필요 |

권장 실험 조합은 다음이다.

- 국내 주실험: `다각도 CCTV 생활안전 데이터` 또는 `지능형 관제 서비스 CCTV 영상 데이터`
- 국내 대규모 보강: `이상행동 CCTV 영상`
- 국제 fallback: `VRU-Accident`
- 국제 비교/관련연구: `WTS`, `AI City Challenge Track 2`
- 메타데이터 보강: `기상청 단기예보`, `국토교통부 돌발상황정보`, `서울 TOPIS`, `VWorld/표준노드링크`

## 1순위 국내 데이터셋

### AI Hub 다각도 CCTV 생활안전 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=71953 |
| 유형 | 텍스트, 비디오 |
| 규모 | 5,000건. 원천데이터 1건은 서로 다른 각도 영상 2개 쌍으로 구성되어 개별 영상은 10,000개 |
| 라벨 | VQA, 3단계 CoT reasoning, caption, event class |
| 이벤트 | 침입, 스토킹, 싸움, 헬멧 미착용, 인도주행, 전동킥보드 2인 이상 주행 등 11종 생활안전 상황 |
| 메타데이터 | filename, width, height, date, time, length, cctv_distribution, cctv_camera, cctv_angle, source, view |
| 장점 | 본 연구의 `영상+텍스트+VQA+다중 시점+metadata filter` 요건을 가장 잘 만족 |
| 리스크 | 2026년 신규 개방 데이터. 내국인 신청 조건 및 실제 다운로드 가능 여부 확인 필요 |
| 적합 태스크 | text-to-clip retrieval, text+metadata retrieval, evidence-aware VQA, multi-view grounding |

판정: **최우선 주 데이터셋**. 접근만 되면 기존 `AI Hub 이상행동 CCTV 영상`보다 본 연구 주제에 더 정확히 맞는다.

### AI Hub 지능형 관제 서비스 CCTV 영상 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=71850 |
| 유형 | 비디오 |
| 규모 | 실제 CCTV 영상 300건 |
| 라벨 | 구간태깅, 캡션, JSON |
| 이벤트 | 침입, 싸움, 쓰러짐, 군집, 인파밀집, 침수 |
| 장점 | 실제 지자체/공공기관 CCTV 기반, 사건 구간과 캡션이 있어 파일럿 워크로드 구성 쉬움 |
| 리스크 | 규모가 작음. 내국인 데이터 신청 필요 |
| 적합 태스크 | retrieval-only 파일럿, report-to-frame grounding, latency/cost 비교 |

판정: **2주 실험에 매우 적합**. 작은 규모가 오히려 빠른 투고 일정에는 장점이다.

### AI Hub 이상행동 CCTV 영상

| 항목 | 내용 |
|---|---|
| 위치 | https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=171 |
| 유형 | 비디오 |
| 규모 | 12종 이상행동, 8,436컷, 약 717시간 |
| 이벤트 | 폭행, 싸움, 절도, 기물파손, 실신, 배회, 침입, 투기, 강도, 데이트폭력/추행, 납치, 주취행동 |
| 장점 | 국내 CCTV 이상행동 도메인 대표 데이터. 규모와 사건 다양성이 큼 |
| 약점 | QA/caption/사건 보고서는 직접 생성해야 할 가능성이 큼 |
| 적합 태스크 | event label retrieval, synthetic report-to-clip retrieval, metadata selectivity 실험 |

판정: **대규모 원천 보강용**. 본 연구의 텍스트 증거는 반자동 생성이 필요하다.

### AI Hub 어린이 보호구역 내 등하교 및 시설물 영상 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71796 |
| 유형 | 텍스트, 이미지, 비디오 |
| 규모 | 2,103,741건 |
| 라벨 | bbox, segmentation, caption |
| 메타데이터 | CCTV/블랙박스, 맑음/흐림, 등교/하교/사고다발/야간 등 분포 |
| 장점 | 시간대·날씨·상황 메타데이터가 분명해 metadata selectivity 실험에 좋음 |
| 리스크 | 안심존/심의형 접근 가능성. 어린이 데이터라 윤리·활용 제약을 강하게 확인해야 함 |
| 적합 태스크 | metadata filter, text+metadata retrieval, 안전구역 이벤트 분석 |

판정: **메타데이터 실험에는 강하지만 접근·윤리 리스크가 큼**.

### AI Hub 교통사고 영상 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=597 |
| 유형 | 비디오, 이미지 |
| 규모 | 영상 21,895건, 이미지 3,284,250장 |
| 라벨 | 사고대상, 사고장소, bbox JSON |
| 장점 | 사고대상/사고장소 분포가 있어 metadata condition을 만들기 쉬움 |
| 약점 | VQA/caption은 제공 핵심이 아니므로 직접 생성 필요 |
| 적합 태스크 | text-to-accident retrieval, location/event metadata filter, hard negative 구성 |

판정: **교통 사고 도메인 보강용**. 국내 사고 데이터의 양이 필요한 경우 유용하다.

### AI Hub 부산시 침수위험 복합 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71793 |
| 유형 | CCTV 이미지, 시계열 센서, segmentation |
| 규모 | 27,516장 |
| 메타데이터 | 10분/1시간/3시간 강우, 강우 관측소 좌표, 하천수위, 빗물받이 수위, 조위, 침수위험정보 |
| 장점 | 본 연구의 `영상+센서/시계열 metadata` 문제에 가장 잘 맞는 재난 데이터 |
| 약점 | 비디오보다 이미지 중심. 안심존/IRB 절차 가능성 |
| 적합 태스크 | sensor-aware retrieval, metadata selectivity stress test, 침수 event retrieval |

판정: **DB 논문성 강화용 보조 데이터**. 메타데이터 필터 실험에는 매우 좋다.

### AI Hub 공원 주요시설 및 불법행위 감시 CCTV 영상 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=477 |
| 유형 | 비디오, 이미지 |
| 규모 | 불법행위 270시간, 정상행위 10시간, 불법객체 36,000장/30시간, 정상객체 21,600장/18시간 |
| 메타데이터 | 촬영 시간, 촬영 날씨, 비식별화 |
| 장점 | 공원 CCTV라는 도시 감시 맥락이 강하고 시간/날씨 조건이 있음 |
| 약점 | VQA/caption 중심 데이터는 아님 |
| 적합 태스크 | event retrieval, weather/time metadata filtering |

판정: **국내 CCTV 보조 데이터**.

### AI Hub 국도 CCTV 영상을 통한 비정상주행 판별 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71566 |
| 유형 | 이미지 |
| 규모 | 약 2,117,886장 |
| 라벨 | bbox, polyline JSON |
| 장점 | 국도 CCTV, 차선변경/차선물기 등 비정상 주행 상황 |
| 약점 | 이미지 중심이고 언어 라벨은 약함 |
| 적합 태스크 | metadata-only/vector-only 이미지 검색, 교통 안전 event filter |

판정: **교통 CCTV 이미지 검색 보조용**.

### AI Hub 멀티 영상 동일 상황 및 객체 식별 데이터

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=71467 |
| 유형 | 비디오, 이미지 |
| 규모 | 547,763장 |
| 라벨 | bbox, re-id, 위험/이상상황 ROI |
| 이벤트 | 쓰러짐, 위험상황, 차량 손괴, 자전거/킥보드 사고, 침입, 응급상황 등 |
| 장점 | 멀티 영상 동일 상황/객체 식별이라 다중 카메라 evidence bundle 설계에 좋음 |
| 약점 | 텍스트/QA 중심이 아님 |
| 적합 태스크 | multi-view evidence retrieval, object/event re-identification |

판정: **멀티카메라 retrieval 보조용**.

### AI Hub CCTV 추적 영상

| 항목 | 내용 |
|---|---|
| 위치 | https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=160 |
| 유형 | 이미지, mp4/json(xml) 설명 있음 |
| 규모 | 50만 이미지, 객체추적 6종 총 500시간 이상 |
| 도메인 | 도시철도역 CCTV, 동일 인물 및 차량 추적 |
| 장점 | 추적/re-identification 계층을 만들 수 있음 |
| 약점 | 사건 보고서/VQA와는 거리가 있음 |
| 적합 태스크 | track retrieval, camera/time metadata filter |

판정: **객체 추적형 보조 데이터**.

## 2순위 국제 데이터셋

### VRU-Accident

| 항목 | 내용 |
|---|---|
| 위치 | https://github.com/Kimyounggun99/VRU-Accident, https://huggingface.co/datasets/kyh9191/VRU-Accident |
| 유형 | 대시캠 사고 비디오, VQA, dense description |
| 규모 | 1,000 real-world accident videos, 6,000 multiple-choice VQA pairs, 1,000 dense accident scene descriptions |
| 장점 | Hugging Face/GitHub 경로가 있어 AI Hub 접근 실패 시 즉시 fallback 가능성이 높음 |
| 약점 | CCTV 고정 카메라가 아니라 대시캠 중심. 한국 도메인은 아님 |
| 적합 태스크 | VQA, dense description retrieval, accident scene grounding |

판정: **가장 현실적인 국제 fallback**.

### WTS / Woven Traffic Safety Dataset

| 항목 | 내용 |
|---|---|
| 위치 | https://github.com/woven-visionai/wts-dataset, https://woven-visionai.github.io/wts-dataset-homepage/ |
| 유형 | 교통 안전 비디오, 다중 시점, dense description |
| 규모 | 1.2K+ video events, 130+ traffic scenarios |
| 장점 | overhead/fixed view와 ego view가 함께 있어 도시 감시형 다중 시점에 가까움 |
| 약점 | staged traffic event 성격이 있으며 다운로드 절차 확인 필요 |
| 적합 태스크 | fine-grained video captioning, text-to-clip retrieval, multi-view evidence |

판정: **논문 주제와 매우 잘 맞는 국제 비교 데이터**.

### AI City Challenge Track 2: Traffic Safety Description and Analysis

| 항목 | 내용 |
|---|---|
| 위치 | https://www.aicitychallenge.org/2025-track2/, https://www.aicitychallenge.org/2026-track2/, https://www.aicitychallenge.org/ai-city-challenge-dataset-access/ |
| 유형 | traffic safety captioning, VQA, multi-camera/view |
| 장점 | 최신 VLM 교통 안전 연구 흐름과 직접 연결 |
| 약점 | challenge 신청/접근 절차가 있을 수 있음 |
| 적합 태스크 | traffic safety VQA, caption retrieval, 사고 전후 상황 설명 |

판정: **관련연구와 국제성 강화에 필수**.

### CityFlow / CityFlow-NL

| 항목 | 내용 |
|---|---|
| 위치 | https://github.com/fredfung007/cityflow-nl, https://www.aicitychallenge.org/2023-data-and-evaluation/ |
| 유형 | 다중 카메라 교통 영상, 자연어 기반 차량 검색 |
| 규모 | 2,498 vehicle tracks, 각 track 3개 NL description, 530 query sets |
| 장점 | text-to-track retrieval benchmark가 이미 정식화되어 있어 검색 실험을 빠르게 만들 수 있음 |
| 약점 | 사건/위험상황보다는 차량 속성·이동 검색 중심 |
| 적합 태스크 | text-to-clip/track retrieval baseline, sparse+dense retrieval 비교 |

판정: **retrieval 방법 검증용으로 좋음**.

### DoTA

| 항목 | 내용 |
|---|---|
| 위치 | https://github.com/MoonBlvd/Detection-of-Traffic-Anomaly |
| 유형 | driving video anomaly |
| 규모 | 4,677 videos |
| 라벨 | temporal, spatial, categorical annotations |
| 장점 | when-where-what anomaly detection이라 grounding 논문 설계에 좋음 |
| 약점 | 대시캠 중심이며 caption/VQA는 없음 |
| 적합 태스크 | report-to-frame grounding, temporal/spatial event retrieval |

판정: **grounding 보강용 국제 데이터**.

### ROAD / ROAD-R

| 항목 | 내용 |
|---|---|
| 위치 | https://github.com/gurkirt/road-dataset, https://sites.google.com/view/road-r/dataset |
| 유형 | autonomous driving road event |
| 규모 | ROAD-R 기준 22개 장영상, 각 약 8분 |
| 라벨 | road event = agent/action/location, linked bounding boxes over time |
| 장점 | event를 구조화된 triplet으로 제공하므로 DB 스키마 설계에 좋음 |
| 약점 | 규모가 작고 CCTV가 아니라 차량 관점 |
| 적합 태스크 | event schema, temporal grounding, structured metadata retrieval |

판정: **event 모델링 참고 데이터**.

### MEVA

| 항목 | 내용 |
|---|---|
| 위치 | https://mevadata.org/, https://registry.opendata.aws/mevadata/ |
| 유형 | multi-camera surveillance activity dataset |
| 공개 규모 | AWS 공개 릴리스 기준 약 328시간, 516GB, 4,259 clips, UAV 4.6시간 |
| 메타데이터 | camera models, site map, GPS tracks |
| 장점 | 실제 멀티카메라 감시 데이터베이스 연구에 가장 가까운 국제 대규모 데이터 |
| 약점 | 크고 무겁다. 2주 실험에는 과함 |
| 적합 태스크 | 장기 확장판, metadata-aware multi-camera retrieval |

판정: **국제 확장판용**. 2주 투고에는 샘플만 사용하거나 related work로 두는 편이 낫다.

### VIRAT

| 항목 | 내용 |
|---|---|
| 위치 | https://viratdata.org/ |
| 유형 | real-world surveillance event recognition |
| 라벨 | DIVA annotation 기준 46 activity types, 7 object types |
| 장점 | 감시 영상 event recognition의 고전적 공개 benchmark |
| 약점 | 텍스트/QA는 없음. 다운로드 agreement 확인 필요 |
| 적합 태스크 | activity label retrieval, event grounding baseline |

판정: **감시 도메인 국제 baseline**.

### UCF-Crime

| 항목 | 내용 |
|---|---|
| 위치 | https://www.crcv.ucf.edu/projects/real-world/ |
| 유형 | surveillance anomaly videos |
| 규모 | 1,900 long untrimmed videos, 약 128시간 |
| 이벤트 | 13 anomaly classes: abuse, arrest, arson, assault, burglary, explosion, fighting, road accident, robbery, shooting, stealing, shoplifting, vandalism 등 |
| 장점 | 이상행동/범죄 CCTV 이벤트의 국제 표준격 데이터 |
| 약점 | frame-level/metadata/text evidence가 약해 본 연구에는 가공 필요 |
| 적합 태스크 | event-only retrieval, hard negative, 약라벨 실험 |

판정: **이상행동 대체 데이터**.

### ShanghaiTech Campus

| 항목 | 내용 |
|---|---|
| 위치 | https://svip-lab.github.io/dataset/campus_dataset.html |
| 유형 | campus surveillance anomaly |
| 규모 | 13 scenes, 130 abnormal events, 270K+ training frames |
| 라벨 | pixel-level ground truth |
| 장점 | 공간 grounding 평가에 유용 |
| 약점 | 텍스트/QA와 메타데이터가 약함 |
| 적합 태스크 | anomaly grounding, visual evidence precision |

판정: **grounding 보조용**.

### BDD100K / BDD-X

| 항목 | BDD100K | BDD-X |
|---|---|---|
| 위치 | https://bair.berkeley.edu/blog/2018/05/30/bdd/ | https://github.com/JinkyuKimUCB/BDD-X-dataset |
| 유형 | driving videos | driving videos with description/explanation |
| 규모 | 100,000 videos, 각 약 40초 | 6,970 videos, 77시간, 26K activities |
| 메타데이터 | weather, time of day, GPS/IMU | day/night, highway/city/countryside 등 설명 |
| 장점 | weather/time metadata가 좋아 필터 실험에 적합 | 텍스트 설명이 있어 retrieval/RAG에 적합 |
| 약점 | 도시 CCTV가 아니라 대시캠 | 사건 감시보다 운전 행동 설명 |

판정: **metadata filter와 텍스트 설명 fallback**.

### nuScenes 계열: nuScenes, NuScenes-QA, Talk2Car, DriveLM

| 데이터 | 위치 | 장점 | 약점 |
|---|---|---|---|
| nuScenes | https://www.nuscenes.org/ | 6 cameras, LiDAR, radar, GPS, IMU, map | 감시 CCTV 아님 |
| NuScenes-QA | https://github.com/qiantianwen/NuScenes-QA | 34K scenes, 460K QA | nuScenes 의존 |
| Talk2Car | https://talk2car.github.io/ | 자연어 command와 visual grounding | command 중심 |
| DriveLM | https://github.com/opendrivelab/drivelm | graph VQA, driving reasoning | 자율주행 중심 |

판정: **VQA/grounding 방법론 참고용**. 본 투고 주 데이터로 쓰기에는 도메인이 다소 벗어난다.

## 메타데이터 보강용 공개 API/데이터

본 연구는 metadata-aware retrieval이 핵심이므로, 영상 데이터에 부족한 시간·장소·날씨·교통량 정보를 외부 공개 데이터로 보강할 수 있다.

| 데이터/API | 위치 | 용도 |
|---|---|---|
| 서울 TOPIS Open API | https://topis.seoul.go.kr/refRoom/openRefRoom_4.do | 서울 교통 속도, 교통 현황, 교통 예보 |
| 서울시 실시간 도로 소통 정보 | https://www.data.go.kr/data/15058364/openapi.do | 링크 ID, 속도, 여행시간 |
| 국토교통부 교통소통정보 | https://www.data.go.kr/data/15040463/openapi.do | 고속도로/국도 구간 평균 속도 |
| 국토교통부 돌발상황정보 | https://www.data.go.kr/data/15040465/openapi.do | 사고, 고장, 낙하물, 침수, 공사 등 event report |
| 경찰청 교통돌발정보서비스 | https://www.data.go.kr/data/15088841/openapi.do | 사고/공사/통제, 위치 좌표 |
| 기상청 단기예보 조회서비스 | https://www.data.go.kr/data/15084084/openapi.do | 초단기실황, 단기예보, 5km 격자 날씨 |
| 국토교통부 표준노드링크 | https://www.data.go.kr/data/15025526/fileData.do | 도로망 링크/노드, 공간 join |
| VWorld 2D 지도 API | https://www.data.go.kr/data/3052419/openapi.do | 지도 시각화, 공간정보 |
| VWorld 교통CCTV 속성정보 | https://www.vworld.kr/dev/v4dv_2ddataguide2_s002.do?svcIde=utiscctv | 교통 CCTV 위치/속성 조회 |
| 서울시 도시고속도로 CCTV 설치위치 | https://data.seoul.go.kr/dataList/OA-15273/F/1/datasetView.do | CCTV ID, 설치 지점명, 좌표 |

주의: 외부 API는 실제 영상 데이터와 동일한 장소/시간으로 정확히 매칭되지 않을 수 있다. 논문에서는 "실제 운영 로그와의 정합"이 아니라 "metadata-aware retrieval operator의 선택도 실험"으로 프레이밍하는 것이 안전하다.

## 데이터셋별 연구 적합도 요약

| 데이터 | 영상 | 텍스트 | QA | 메타데이터 | Grounding | 접근성 | 총평 |
|---|---:|---:|---:|---:|---:|---:|---|
| AI Hub 다각도 CCTV 생활안전 | 상 | 상 | 상 | 상 | 중 | 중 | 최우선 |
| AI Hub 지능형 관제 CCTV | 중 | 중 | 중 | 중 | 상 | 중 | 2주 파일럿 최적 |
| AI Hub 이상행동 CCTV | 상 | 하 | 하 | 중 | 중 | 중 | 대규모 보강 |
| AI Hub 어린이 보호구역 2023 | 상 | 중 | 하 | 상 | 상 | 하 | 메타데이터 우수, 접근 리스크 |
| AI Hub 교통사고 영상 | 상 | 하 | 하 | 중 | 중 | 중 | 사고 도메인 보강 |
| AI Hub 부산 침수위험 | 중 | 하 | 하 | 최상 | 상 | 하 | 센서 metadata 실험 최상 |
| VRU-Accident | 중 | 상 | 상 | 중 | 중 | 상 | 국제 fallback 최상 |
| WTS | 상 | 상 | 중 | 중 | 중 | 중 | 국제 비교 최상 |
| AI City Track 2 | 상 | 상 | 상 | 중 | 중 | 중 | 관련연구 핵심 |
| CityFlow-NL | 상 | 상 | 하 | 중 | 중 | 중 | retrieval baseline |
| DoTA | 상 | 하 | 하 | 중 | 상 | 상 | grounding 보강 |
| MEVA | 최상 | 하 | 하 | 상 | 상 | 중 | 국제 확장판 |
| VIRAT | 상 | 하 | 하 | 중 | 상 | 중 | 감시 baseline |
| UCF-Crime | 상 | 하 | 하 | 하 | 중 | 상 | event-only 보강 |
| BDD100K/BDD-X | 상 | 중 | 하 | 상 | 중 | 중 | metadata/text fallback |

## 2주 내 추천 실행안

### Plan A: AI Hub 다각도 CCTV 생활안전 데이터 접근 가능

1. 500~1,000건 영상쌍만 샘플링한다.
2. `question`, `caption_text`, `event_class`, `date`, `time`, `cctv_distribution`, `cctv_angle`, `source`, `view`를 DB 스키마로 변환한다.
3. text-to-clip retrieval, text+metadata retrieval, VQA evidence retrieval을 구성한다.
4. B0~B6 구조를 selectivity별로 비교한다.

### Plan B: 다각도 데이터 접근 실패, 지능형 관제 CCTV 가능

1. 300건 전체를 사용한다.
2. 구간태깅/캡션 JSON을 evidence text로 사용한다.
3. query를 event/time/location template로 반자동 생성한다.
4. retrieval-only 논문으로 축소하되, grounding Hit@k를 추가한다.

### Plan C: AI Hub 접근 전반 실패

1. VRU-Accident를 주 데이터로 사용한다.
2. dense description을 report, VQA question을 query, video id를 clip, 사고 유형을 event_label로 둔다.
3. WTS 또는 CityFlow-NL을 retrieval 보조 실험으로 붙인다.
4. 논문 제목에서 "국내 CCTV" 대신 "도시 교통 안전 멀티모달 데이터"로 보수화한다.

## 최종 판단

공개 데이터셋 조사는 충분히 가능하며, 현재 기준으로는 데이터 확보 전략을 다음처럼 바꾸는 것이 맞다.

1. 기존 1순위였던 `AI Hub 이상행동 CCTV 영상`보다 `AI Hub 다각도 CCTV 생활안전 데이터`를 최우선으로 올린다.
2. 2주 일정의 안정성을 위해 `AI Hub 지능형 관제 서비스 CCTV 영상 데이터`를 실험용 최소 데이터셋으로 둔다.
3. AI Hub 접근이 하루 이상 지연되면 `VRU-Accident`로 즉시 전환한다.
4. `부산시 침수위험 복합 데이터`, `서울 TOPIS`, `국토교통부 돌발상황정보`, `기상청 단기예보`는 metadata selectivity 실험의 보강재로 쓴다.
5. 국제성은 WTS, AI City Track 2, CityFlow-NL, MEVA, VIRAT, DoTA를 관련연구와 대체 실험 후보로 배치하면 충분하다.

본 논문에서 가장 강한 데이터 기반 메시지는 다음이다.

> 최근 공개된 도시 감시/교통 안전 데이터는 이미 비디오, 캡션, VQA, CoT, 시간·장소·카메라 메타데이터를 포함하는 방향으로 진화하고 있다. 따라서 VLM 성능 평가만으로는 부족하며, 이질적 evidence를 어떤 저장·색인·검색 구조로 결합할 것인지가 독립적인 데이터베이스 연구 문제가 된다.
