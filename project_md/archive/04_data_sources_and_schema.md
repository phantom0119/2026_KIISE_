# 데이터 소스와 스키마 계획

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 데이터 소스 우선순위는 실제 확보 결과에 맞게 갱신되었다. 현재 VRU, AI Hub 지능형 CCTV, AI Hub 이상행동 CCTV, AI Hub 다각도 CCTV 생활안전, 시내도로 CCTV, 교차로신호체계, CityFlow-NL 원본이 확보되었고, 본문 핵심은 VRU/AI Hub 지능형 CCTV retrieval, 다각도 CCTV answer-level VLM, 시내도로 CCTV index benchmark로 구성한다. 최신 역할 분담은 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 목적

이 문서는 투고 전 최소 실험을 위해 어떤 데이터를 우선 사용할지, 접근이 막힐 경우 무엇으로 대체할지, 그리고 검색/grounding/VQA 평가를 위해 어떤 테이블 구조가 필요한지를 정리한다.

## 현재 데이터 저장 루트

원천 데이터는 워크스페이스 내부 경로처럼 보이도록 `Datasets` symlink로 관리한다.

| 구분 | 경로 |
|---|---|
| 논리 경로 | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets` |
| 물리 경로 | `/hdd2/KIISE_datasociety/Datasets` |
| 운영 manifest | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/manifests/dataset_inventory_20260706.md` |

실험 코드에서는 논리 경로를 사용한다. 실제 저장 장치를 바꾸는 경우 symlink만 갱신하면 된다.

## 데이터 소스 우선순위

| 우선순위 | 소스 | 장점 | 리스크 | 사용 방식 |
|---:|---|---|---|---|
| 1 | AI Hub 이상행동 CCTV 영상 | 국내 도시 감시 맥락과 가장 잘 맞음. 12가지 이상행동, 약 700시간 규모 설명 확인 | 로그인/신청/다운로드 제약 가능 | 접근 가능하면 주 실험 데이터 |
| 2 | AI City Challenge 2025 / WTS 계열 | 교통 안전 설명, 다중 카메라, video QA가 연구 질문과 직접 연결 | 데이터 신청/트랙별 접근 절차 확인 필요 | 국내 데이터 지연 시 대체 또는 보강 |
| 3 | VRU-Accident | 1K 사고 영상, 6K MCQ QA, dense scene description 제공 | 고정형 CCTV가 아니라 대시캠 | 원본 확보 완료. 2주 내 파일럿 주 데이터 |
| 4 | 공개 이미지/프레임 + 합성 사건 보고서 | 즉시 구축 가능 | 감시 영상 원자료의 현실성이 낮음 | 최후의 파일럿 실험 대체 |

## 최소 실험 데이터 단위

각 item은 다음 네 계층으로 연결되어야 한다.

| 계층 | 단위 | 예시 |
|---|---|---|
| visual item | clip 또는 frame | `clip_0001`, `frame_0001_0030` |
| event label | 사건/행동 라벨 | `fight`, `wander`, `accident`, `normal_flow` |
| metadata | 시간, 위치, 카메라, 환경 조건 | `cam_id`, `timestamp`, `weather`, `location_id` |
| text evidence | 라벨 설명, 캡션, 사건 보고서 | “오후 시간대 횡단보도 부근에서 보행자와 차량의 근접 상황이 발생함” |

## 권장 파일 구조

```text
Datasets/
  raw/
    videos/
    images/
    reports/
  processed/
    frames/
    captions.jsonl
    metadata.csv
    reports.jsonl
    queries.jsonl
    qrels.tsv
  indexes/
    bm25/
    vector/
  results/
    retrieval_metrics.csv
    latency_metrics.csv
    summary.md
```

## 논리 스키마

### `clip`

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `clip_id` | text primary key | 비디오 클립 ID |
| `source` | text | AIHub, AICity, VRU 등 |
| `path` | text | 원본 파일 경로 |
| `duration_sec` | real | 길이 |
| `event_label` | text | 대표 이벤트 라벨 |
| `split` | text | train/dev/test |

### `frame`

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `frame_id` | text primary key | 프레임 ID |
| `clip_id` | text | 소속 클립 |
| `timestamp_sec` | real | 클립 내 시간 |
| `path` | text | 프레임 이미지 경로 |
| `caption` | text | VLM 또는 규칙 기반 캡션 |
| `embedding_id` | text | 벡터 인덱스 키 |

### `event_report`

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `report_id` | text primary key | 보고서 ID |
| `clip_id` | text nullable | 직접 연결된 클립 |
| `text` | text | 사건 설명 또는 보고서 원문 |
| `event_label` | text | 사건 라벨 |
| `time_hint` | text nullable | 시간 힌트 |
| `location_hint` | text nullable | 장소 힌트 |

### `metadata`

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `item_id` | text | clip_id 또는 frame_id |
| `item_type` | text | clip/frame/report |
| `cam_id` | text nullable | 카메라 ID |
| `location_id` | text nullable | 위치 ID |
| `timestamp` | text nullable | ISO timestamp |
| `weather` | text nullable | 날씨 조건 |
| `scene_type` | text nullable | road/intersection/indoor 등 |
| `event_label` | text nullable | 이벤트 라벨 |

### `query`

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `query_id` | text primary key | 질의 ID |
| `task` | text | text_to_clip, metadata_retrieval, grounding, vqa |
| `query_text` | text | 자연어 질의 |
| `metadata_filter` | json | 시간/장소/이벤트 조건 |
| `answer` | text nullable | VQA 정답 |

### `qrels`

| 컬럼 | 타입 | 설명 |
|---|---|---|
| `query_id` | text | 질의 ID |
| `item_id` | text | 정답 clip/frame/report |
| `item_type` | text | clip/frame/report |
| `relevance` | integer | 0~3 relevance grade |
| `span_start_sec` | real nullable | grounding 시작 |
| `span_end_sec` | real nullable | grounding 종료 |

## 질의 생성 규칙

초기 질의는 완전 자동 생성보다 반자동 템플릿이 낫다. 실험 일관성과 라벨 연결이 중요하기 때문이다.

| 질의 유형 | 템플릿 |
|---|---|
| event-only | `{event_label} 장면을 찾아라` |
| time-filtered | `{time_hint}에 발생한 {event_label} 장면을 찾아라` |
| location-filtered | `{location_hint}에서 발생한 {event_label} 장면을 찾아라` |
| report-to-frame | `{report_text}`와 가장 관련 있는 프레임을 찾아라 |
| VQA | `이 장면에서 어떤 사건이 발생하고 있는가?` |

## 실험 실행 순서

1. clip/frame/report/metadata/qrels 파일을 먼저 만든다.
2. BM25 index를 report text와 caption에 대해 만든다.
3. vector index를 frame caption 또는 image embedding에 대해 만든다.
4. metadata-only, BM25-only, vector-only, vector+postfilter, prefilter+vector, hybrid를 같은 qrels로 평가한다.
5. 결과 CSV를 논문 표로 바로 변환할 수 있게 저장한다.

## 즉시 확인할 항목

- AI Hub 계정에서 이상행동 CCTV 샘플 다운로드 가능 여부.
- AI City Challenge/WTS 계열 데이터 접근 경로.
- VRU-Accident 기반 ingest/qrels 생성 스크립트 작성.
- 현재 시스템의 GPU/CPU 상태와 VLM embedding 생성 가능 여부.
- PostgreSQL/pgvector 사용 가능 여부. 불가능하면 FAISS+SQLite로 시작한다.

## 출처

- AI Hub 이상행동 CCTV 영상: https://www.aihub.or.kr/aihubdata/data/view.do?dataSetSn=171
- AI City Challenge 2025: https://www.aicitychallenge.org/2025-ai-city-challenge/
- VRU-Accident: https://arxiv.org/abs/2507.09815
