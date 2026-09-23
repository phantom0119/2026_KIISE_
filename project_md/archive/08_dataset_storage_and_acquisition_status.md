# 데이터 저장소 구축 및 확보 현황

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 데이터 확보는 완료 상태로 보며, 이후 AI Hub 다각도 CCTV는 fixed VLM multi-view answer-level 실험까지, 시내도로 CCTV는 132K real CLIP vector와 1M scale ANN benchmark까지 진행되었다. 최신 데이터셋 구축 체계와 본문 사용 범위는 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 결론

2026-07-08 갱신: AI Hub 다각도 CCTV 생활안전 데이터, 시내도로 CCTV, 교차로신호체계, CityFlow-NL 원본 zip이 추가 확보되었다. 따라서 본 문서의 초기 결론보다 최신 상태가 크게 개선되었고, 현재 본 연구에 필요한 멀티모달 데이터셋 확보는 완료로 판정한다. 최신 판단은 `31_additional_dataset_need_review_20260708.md`와 `30_all_acquired_dataset_research_design_20260708.md`를 기준으로 한다.

따라서 2주 투고 일정에서는 다음 전략이 가장 안전하다.

1. 다각도 CCTV를 main multimodal anchor로 두고, VQA/CoT/evidence 기반 retrieval과 answer grounding을 구성한다.
2. VRU-Accident와 AI Hub 지능형 CCTV의 기존 결과를 anchor baseline으로 유지한다.
3. 시내도로 CCTV, 교차로신호체계, CityFlow-NL은 full extraction이 아니라 zip streaming/sample adapter 기반 확장 실험으로 반영한다.
4. WTS/TUMTraffic은 related work 또는 optional extension으로 둔다.

## 저장 경로

| 구분 | 경로 | 설명 |
|---|---|---|
| 프로젝트 논리 경로 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets` | 논문 코드와 문서에서 사용할 기본 경로 |
| 실제 물리 경로 | `/hdd2/KIISE_datasociety/Datasets` | 대용량 데이터 저장 위치 |
| 연결 방식 | symlink | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets -> /hdd2/KIISE_datasociety/Datasets` |
| 운영 manifest | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/manifests/dataset_inventory_20260706.md` | 확보/제한/검증 현황 |

실험 스크립트에는 물리 경로 대신 항상 논리 경로 `Datasets`를 쓰는 편이 좋다. 이후 `/hdd`로 옮기더라도 symlink만 바꾸면 코드 수정 없이 유지할 수 있다.

## 확보 완료 데이터

### VRU-Accident

| 항목 | 내용 |
|---|---|
| 원본 데이터 | 확보 완료 |
| 위치 | `Datasets/external/VRU-Accident_hf` |
| 영상 추출 위치 | `Datasets/raw/VRU-Accident/VRU_videos` |
| canonical 산출물 | `Datasets/processed/vru_accident/20260706/canonical` |
| 코드 저장소 | `Datasets/external/VRU-Accident_repo` |
| 데이터 규모 | 1,000개 mp4, 6,000 VQA, 1,000 dense caption |
| 검증 | parquet 로드 성공, zip 내부 1,000 mp4 확인, 추출 영상과 parquet 경로 missing 0, canonical query 244개/qrels 5,488개 생성 |

이 데이터는 대시캠 사고 영상이라 "도시 CCTV"의 고정 카메라 조건에는 완전히 맞지 않는다. 하지만 사고/취약도로이용자/질의응답/상세 캡션이 모두 있어, **metadata-aware hybrid retrieval 구조의 최소 실험**에는 가장 즉시성이 높다.

권장 사용:

- `video_path`를 `clip.path`로 정규화한다.
- VQA의 `category`를 `event_label` 또는 `question_category` metadata로 둔다.
- dense caption을 BM25 및 vector index의 text evidence로 사용한다.
- VQA question을 query로 쓰고, 같은 `video_path`를 qrels 정답으로 둔다.

현재 구현에서는 VQA의 `options`와 `answer`를 파싱해 `weather_light`, `location`, `road_type`, `accident_type`, `accident_reason`, `prevention_method` facet을 만들었다. 이 facet으로 weak/medium/strong 난도의 metadata-aware retrieval query를 생성했다.

### CityFlow-NL

| 항목 | 내용 |
|---|---|
| 확보 범위 | natural language track annotation JSON |
| 위치 | `Datasets/external/cityflow_nl/cityflow-nl` |
| canonical staging | `Datasets/processed/cityflow_nl/20260707/canonical` |
| repo commit | `d79e27ed74ac4ae88f4784cd2f8679f1399f8fa2` |
| 규모 | train track 2,155건, test track 184건, test query 184건, train-derived query/qrels 6,465건 |
| 한계 | 원본 zip은 확보·검증 완료. zip 내부는 `vdo.avi` 중심이므로 `img1/*.jpg` frame extraction 필요 |

이 데이터는 비디오 원본이 없는 상태이므로 주 실험 데이터로 두기보다, text-to-track retrieval schema와 qrels 변환기의 보조 검증에 적합하다. 2026-07-07 기준 annotation-only canonical 변환은 완료했지만, 실제 frame file 검출 수가 0이므로 true multimodal visual retrieval 결과로 쓰면 안 된다.

### AI Hub 지능형 관제 서비스 CCTV 영상 데이터

| 항목 | 내용 |
|---|---|
| 압축 원본/라벨 루트 | `Datasets/external/지능형관제서비스CCTV영상데이터` |
| 실험용 raw 루트 | `Datasets/raw/aihub_intelligent_cctv/20260706` |
| canonical 산출물 | `Datasets/processed/aihub_intelligent_cctv/20260706/canonical` |
| retrieval 결과 | `Datasets/processed/aihub_intelligent_cctv/20260706/results` |
| 상태 | 압축 원본 확보, mp4/json 추출 정리 완료, canonical 변환 및 bge-m3/e5 B0~B5 보강 실험 완료 |
| 크기 | 압축 원본 약 13G, 실험용 raw 약 13G |
| 구성 | Training/Validation, 원천 mp4 zip 31개, 라벨 json zip 31개 |
| 검증 | zip 62개 오류 0, mp4 269개, json 269개, paired clips 269개, missing 0 |
| 정리 스크립트 | `2026_KIISE/scripts/prepare_aihub_cctv_raw.py` |

이 데이터는 국내 CCTV 성격이 강해 VRU-Accident baseline의 대시캠 편향을 보완한다. 현재 `AIHubIntelligentCCTVAdapter`로 `event_caption`, `event_class`, `event_frame`, `night`, `width/height/frame_count`를 canonical schema로 변환했고, bge-m3/e5-large-v2 기반 B0~B5 retrieval까지 실행했다. 논문에서는 main result보다 국내 CCTV 보강 실험 및 외적 타당성 근거로 배치하는 것이 안전하다.

### 코드·구조 참고용 저장소

| 데이터셋 | 위치 | 현재 상태 |
|---|---|---|
| WTS | `Datasets/external/WTS_repo` | README, 평가/전처리 코드 확보. 원본 영상은 Form 승인 필요 |
| SUTD-TrafficQA | `Datasets/external/SUTD-TrafficQA_repo` | sample annotation과 reader 확보. 전체 dataset request 필요 |
| TUMTraffic-VideoQA baseline | `Datasets/external/TUMTraffic-VideoQA_baseline_repo` | baseline code와 expected layout 확보. dataset registration 필요 |
| UDVideoQA finetune | `Datasets/external/UDVideoQA_finetune_repo` | inference/fine-tuning code 확보. 원본 dataset 접근 확인 필요 |

## 신청 또는 등록 필요 데이터

| 우선순위 | 데이터셋 | 왜 중요한가 | 현재 상태 |
|---:|---|---|---|
| 완료 | AI Hub 다각도 CCTV 생활안전 데이터 | 텍스트+비디오, VQA, CoT, caption이 있어 도시 CCTV 멀티모달 DB 실험에 가장 적합 | `Datasets/external/21.다각도 CCTV 생활안전 데이터` |
| 선택 | WTS | fixed overhead camera와 vehicle ego view, caption/VQA가 있어 traffic safety retrieval에 강함 | `Datasets/restricted/WTS` |
| 선택 | TUMTraffic-VideoQA | roadside traffic video, QA, captioning, grounding annotation을 모두 제공 | `Datasets/restricted/TUMTraffic-VideoQA` |
| 완료 | AI Hub CCTV 교통 영상(시내도로) | 국내 도시 교통 CCTV 원천성과 weather/time/object metadata가 좋음 | `Datasets/external/교통문제 해결을 위한 CCTV 교통 영상(시내도로)` |
| 완료 | AI Hub 교차로 신호 체계·보행자·차량 이동 복합 데이터 | 교차로 영상, 차량/보행량 CSV, 신호/이동 정보가 metadata selectivity 실험에 좋음 | `Datasets/external/교차로신호체계` |
| 선택 | SUTD-TrafficQA/RoadSocial | traffic/road VideoQA 보조 실험에 적합 | 각각 `restricted/` 또는 repo-only |

## 논문 실험 설계 반영

현재 데이터 상태를 기준으로 논문 실험은 다음처럼 잡는 것이 좋다.

| 실험 | 즉시 사용 데이터 | 측정 지표 |
|---|---|---|
| text-to-clip retrieval | VRU-Accident caption/VQA | Recall@K, MRR, nDCG |
| category metadata filter | VRU-Accident VQA category | filter selectivity, Recall@K, latency |
| hybrid retrieval | caption BM25 + dense vector + category prefilter/postfilter | Recall-latency trade-off |
| domestic CCTV extension | AI Hub 지능형 CCTV event caption/metadata | 동일 canonical schema 적용 가능성, 국내 CCTV 보강 성능 |
| evidence-aware VQA lookup | VQA question -> candidate clip -> answer/evidence | accuracy proxy, hit@K |
| text-to-track schema sanity check | CityFlow-NL annotation | query/track/qrels 변환 가능성 |

강한 주장은 "VRU-Accident가 도시 CCTV 데이터다"가 아니라, **교통 안전 멀티모달 영상 DB에서 텍스트 증거와 구조화 metadata를 함께 다루는 검색 구조의 재현 가능한 평가 프로토콜**을 제시했다는 쪽으로 둬야 한다. 도시 CCTV 원천 데이터가 승인되면 같은 프로토콜을 적용해 외적 타당성을 보강한다.

## 출처

- VRU-Accident Hugging Face: https://huggingface.co/datasets/kyh9191/VRU-Accident
- VRU-Accident GitHub: https://github.com/Kimyounggun99/VRU-Accident
- WTS GitHub: https://github.com/woven-visionai/wts-dataset
- WTS project page: https://woven-visionai.github.io/wts-dataset-homepage/
- CityFlow-NL GitHub: https://github.com/fredfung007/cityflow-nl
- AI City Dataset Quick Access: https://www.aicitychallenge.org/ai-city-challenge-dataset-access/
- AI City 2023 Track 2 Download: https://www.aicitychallenge.org/2023-track2-download/
- SUTD-TrafficQA GitHub: https://github.com/sutdcv/SUTD-TrafficQA
- TUMTraffic-VideoQA: https://arxiv.org/abs/2502.02449
- AI Hub 다각도 CCTV 생활안전 데이터: https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=71953
- AI Hub CCTV 교통 영상(시내도로): https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=165
- AI Hub 교차로 신호 체계·보행자·차량 이동 복합 데이터: https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=522
