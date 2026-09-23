# Additional Dataset Need Review

작성 기준일: 2026-07-08

2026-07-09 최신 판정: 추가 데이터셋 확보 필요성은 계속 "없음"이다. 이후 작업으로 AI Hub 다각도 CCTV는 canonical evidence DB와 answer-level VLM view-selection 실험까지 완료되었고, 시내도로 CCTV는 132K real CLIP vector 기반 ANN 색인 구조 벤치마크까지 완료되었다. 따라서 현재 병목은 데이터 추가 확보가 아니라 제출 전 문서 정합성, 표·그림·참고문헌 검수, 결과 해석의 과장 방지다. 최신 종합은 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 결론

AI Hub `다각도 CCTV 생활안전 데이터`가 `/hdd2/KIISE_datasociety/Datasets/external/21.다각도 CCTV 생활안전 데이터`에 확보되어 있으므로, 본 연구에 필요한 멀티모달 데이터셋 확보는 완료로 판정한다.

현재 추가로 반드시 확보해야 하는 데이터셋은 없다. 남은 핵심 작업은 추가 수집이 아니라, 확보된 데이터셋 기반 결과를 제출 패키지에 일관되게 반영하고 재현성 manifest와 원고 표현을 점검하는 것이다.

## 다각도 CCTV 확보 검증 요약

| 항목 | 값 |
|---|---:|
| local path | `Datasets/external/21.다각도 CCTV 생활안전 데이터` |
| size | 483G |
| zip files | 44 |
| openable zip files | 44 |
| source mp4 entries | 9,000 |
| label json entries | 4,500 |
| source event ids | 4,500 |
| label event ids | 4,500 |
| camera views per event | 2 (`c1`, `c2`) |
| label without source | 0 |
| source without label | 0 |

상세 검증 기록은 `Datasets/manifests/aihub_71953_multi_angle_cctv_audit_20260708.md`를 기준으로 한다.

## 현재 확보 데이터셋의 멀티모달 충족성

| 축 | 현재 확보 데이터셋 | 충족 모달리티 | 판단 |
|---|---|---|---|
| multi-view CCTV VQA/evidence | AI Hub 다각도 CCTV 생활안전 | c1/c2 mp4, question, answer, caption, CoT, evidence frame/object/bbox JSON | 핵심 충족 |
| 국내 CCTV event video | AI Hub 지능형 관제 CCTV, 이상행동 CCTV | mp4, JSON/XML event label, key frame/evidence 추출 가능 | 충족 |
| 도시 교통 visual archive | 시내도로 교통 CCTV 원천, `101...` 라벨 패키지 | JPG frame archive, bbox/segmentation/tracking JSON | 충족 |
| 자연어 교통 검색 benchmark | CityFlow-NL / AI City Track 2 | AVI, vehicle track, natural language query/annotation | 충족 |
| 사고/교통 안전 QA | VRU-Accident | mp4, VQA, dense caption | 충족 |
| 구조화 로그/운영 메타데이터 | 교차로신호체계 | CSV log, object/visual archive, metadata filter | 충족 |

따라서 본 연구는 단순히 “비디오를 벡터화한 검색”이 아니라, 다음 검색 단위를 모두 갖춘다.

1. 자연어 질의 to 영상/프레임 evidence
2. 자연어 VQA/CoT label to LLM answer grounding
3. single-view vs multi-view CCTV evidence fusion
4. 이미지 질의 to 유사 프레임/이벤트 evidence
5. 메타데이터 필터 to 후보 축소 후 vector rerank
6. 구조화 로그/라벨 to evidence packet 구성
7. visual vector index structure benchmark와 filtered ANN selectivity 실험

## 추가 확보 필요성 판정

| 후보 | 필요도 | 판단 |
|---|---:|---|
| AI Hub 다각도 CCTV 생활안전 데이터 | 완료 | 본 연구 main multimodal anchor로 편입 |
| WTS Dataset | 선택 | 보행자 중심 traffic video로 국제성 보강 가능. 접근 신청형이므로 본 투고 필수 아님 |
| TUMTraf / TUM Traffic Dataset | 선택 | roadside camera+LiDAR+calibration+OpenLABEL로 3D metadata 연구 확장 가능. 본 투고 범위에는 과함 |
| TUMTraffic-VideoQA | 선택 | traffic scene VQA/grounding 비교에 유효. 이미 확보한 다각도 CCTV와 VRU로 핵심 실험 가능 |

## 본 연구에서 다각도 CCTV가 해결하는 결함

이전 실험 설계의 가장 큰 약점은 “진짜 멀티모달 상용 검색 서비스”라고 주장하기에는 동일 사건에 대한 다중 시점, 자연어 질의, 답변, 근거 프레임/객체가 한 데이터셋 안에서 동시에 닫히지 않는다는 점이었다.

다각도 CCTV 데이터는 이 결함을 직접 해결한다.

| 결함 | 다각도 CCTV로 해결되는 방식 |
|---|---|
| 단일 영상 또는 단일 프레임 검색에 가까움 | 한 event마다 `c1`, `c2` 두 CCTV view 제공 |
| LLM 답변 근거 평가가 약함 | question, answer, caption, CoT, evidence text 제공 |
| evidence grounding이 불명확함 | frame_id, obj_id, bbox, object label 제공 |
| 한국형 CCTV 서비스 맥락이 약함 | 생활안전/이륜이동수단/침입/스토킹/싸움 등 국내 CCTV event class 제공 |
| DB 연구 기여가 모델 성능 비교로 흐를 위험 | view, event class, camera, angle, time metadata를 prefilter/fusion/selectivity 실험에 사용 가능 |

## 최종 결정

1. 본 연구의 데이터셋 확보 단계는 완료로 본다.
2. 다각도 CCTV는 optional extension이 아니라 main anchor dataset으로 사용한다.
3. 추가 데이터셋 수집은 중단하고, adapter/canonical schema/qrels/index/evaluation 구현 결과를 원고와 제출 색인에 정합적으로 반영한다.
4. WTS, TUMTraf, TUMTraffic-VideoQA는 논문 related work와 future extension으로만 둔다.
5. 2주 일정의 성공 조건은 “더 많은 데이터셋”이 아니라 “현재 확보 데이터에서 동일한 멀티모달 DB 검색·선택·색인 메커니즘이 일관되게 동작함을 보이는 것”이다.

## 출처

- AI Hub, 다각도 CCTV 생활안전 데이터: https://aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&dataSetSn=71953
- WTS: Woven Traffic Safety Dataset: https://woven-visionai.github.io/wts-dataset-homepage/
- TUM Traffic Dataset Development Kit: https://github.com/tum-traffic-dataset/tum-traffic-dataset-dev-kit
- TUMTraffic-VideoQA: https://arxiv.org/abs/2502.02449
