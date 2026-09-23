# CityFlow-NL 확보 가능성 및 로컬 구축 상태

작성 기준일: 2026-07-08

2026-07-09 최신 갱신: CityFlow-NL은 annotation canonical과 raw zip 확보 상태로 유지하되, 최신 본문 핵심 수치에는 포함하지 않는다. 본문 핵심은 VRU/AI Hub 지능형 CCTV retrieval, AI Hub 다각도 CCTV answer-level VLM, 시내도로 CCTV index benchmark로 방어한다. CityFlow-NL은 natural-language vehicle retrieval 확장 후보와 후속 visual materialization 대상으로 둔다. 최신 종합 판단은 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 결론

CityFlow-NL은 현재 시스템에서 **annotation repository는 직접 확보 완료**했고, 2026-07-08 기준 **AI City 2023 Track 2 원본 데이터 zip도 로컬 확보 및 무결성 검증을 완료**했다. 단, zip 내부에는 CityFlow-NL annotation의 `img1/*.jpg` frame 파일이 직접 들어 있지 않고 카메라별 `vdo.avi`가 들어 있으므로, 아직 true multimodal 본실험에 바로 투입할 수는 없다. 다음 단계는 AVI에서 annotation이 참조하는 frame 또는 track crop을 추출하는 것이다.

즉시 사용 가능한 범위:

- train/test track UUID
- frame reference path
- bounding box annotation
- train track별 자연어 설명
- test natural language query
- train split 기반 weak qrels

아직 사용하면 안 되는 범위:

- CLIP/SigLIP visual embedding 기반 CityFlow-NL true multimodal 검색
- image-to-track retrieval
- frame crop 기반 vehicle retrieval
- 본문 main result의 시각 검색 성능 표

이 범위를 넘어서려면 AI City 2023 Track 2 원본 zip을 압축 해제하고, annotation의 frame reference가 실제 추출 프레임 파일로 resolve되는지 검증해야 한다.

## 공식 확보 가능성 확인

| 항목 | 확인 결과 |
|---|---|
| CityFlow-NL GitHub repository | 공개 접근 가능, clone 완료 |
| repository license | Apache-2.0 |
| repository 내용 | `train-tracks.json`, `test-tracks.json`, `test-queries.json`, baseline code |
| 원본 frame/video | repository에 포함되지 않음 |
| AI City 2023 Track 2 download page | `AICity23_Track2_NL_Retrieval.zip` Google Drive 직접 다운로드 링크 제공 |
| AI City dataset access | 공식 Dataset Quick Access 페이지는 목록 내 데이터셋의 password protection이 제거됐다고 안내 |

근거:

- CityFlow-NL GitHub README는 train split 2,155개 track, test split 184개 track, test query 184개를 설명하고, `frames` 값이 CityFlow Benchmark frame path라고 명시한다.
- AI City Dataset Quick Access 페이지는 2023 Track 2 `Tracked-Vehicle Retrieval by Natural Language Descriptions`를 직접 다운로드 가능 목록에 포함한다.
- AI City 2023 Track 2 download page는 `AICity23_Track2_NL_Retrieval.zip` Google Drive 링크와 data license agreement를 제공한다.
- Google Form request page는 deprecated로 표시되어 있고, 최신 데이터셋 접근 페이지를 사용하라고 안내한다.

## 로컬 저장 경로

| 구분 | 경로 | 상태 |
|---|---|---|
| 논리 데이터 루트 | `Datasets` | `/hdd2/KIISE_datasociety/Datasets` symlink |
| GitHub annotation repo | `Datasets/external/cityflow_nl/cityflow-nl` | 확보 완료 |
| repo commit | `d79e27ed74ac4ae88f4784cd2f8679f1399f8fa2` | 확인 완료 |
| canonical staging | `Datasets/processed/cityflow_nl/20260707/canonical` | 생성 완료 |
| 변환 스크립트 | `2026_KIISE/scripts/build_cityflow_nl_canonical.py` | 생성 및 실행 완료 |
| 원본 zip 실제 위치 | `/hdd2/KIISE_datasociety/Datasets/external/CityFlow-NL_repo/AICity23_Track2_NL_Retrieval.zip` | 확보 및 `unzip -tq` 검증 완료 |
| 원본 zip 표준 symlink | `Datasets/external/cityflow_nl/aicity2023_track2/AICity23_Track2_NL_Retrieval.zip` | 생성 완료 |
| 원본 frame/video root | `Datasets/raw/cityflow_nl/aicity2023_track2` | 압축 해제 예정 |
| raw zip validation report | `Datasets/manifests/cityflow_nl_zip_validation_20260708.md` | 생성 완료 |

## 로컬 검증 결과

실행 명령:

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_cityflow_nl_canonical.py \
  --repo-root Datasets/external/cityflow_nl/cityflow-nl \
  --output-dir Datasets/processed/cityflow_nl/20260707/canonical \
  --overwrite
```

출력 요약:

| 산출물 | 수량 |
|---|---:|
| train tracks | 2,155 |
| test tracks | 184 |
| test queries without qrels | 184 |
| canonical clips | 2,339 |
| canonical documents | 24,749 |
| canonical metadata rows | 16,373 |
| train-derived queries | 6,465 |
| train-derived qrels | 6,465 |
| present frame files | 0 |

생성 파일:

| 파일 | 역할 |
|---|---|
| `clips.parquet` | track 단위 clip record |
| `documents.parquet` | NL description과 other-view description |
| `metadata.parquet` | split, scene, camera, frame source, asset availability facet |
| `queries.jsonl` | train NL description 기반 retrieval query |
| `qrels.tsv` | query -> positive track weak qrel |
| `dataset_manifest.json` | 확보 상태, 원천 repo, raw zip 확보 상태, frame extraction 미완료 상태 |
| `summary.md` | 사람이 읽는 요약 |

검증 명령에서 Parquet/JSONL/TSV 로드는 성공했다. 다만 annotation의 frame reference 218,252건 중 실제 로컬 이미지 파일로 확인된 항목은 0건이므로, 현재 상태를 true multimodal로 주장하면 실험 설계 오류가 된다.

## 현재 연구에서의 사용 판정

CityFlow-NL은 본 연구에 적합한 데이터셋이다. 이유는 다음과 같다.

- 도시 교통 카메라 기반 차량 retrieval 문제다.
- 자연어 질의가 주어지고 차량 track을 rank하는 검색 문제이므로, 본 연구의 query-document-evidence retrieval 구조와 잘 맞는다.
- frame path, bounding box, camera/scene 정보를 포함하므로 원본 frame을 확보하면 visual-text-metadata 통합 검색 실험으로 확장하기 좋다.
- AI City/CVPR Workshop 계열 challenge 데이터라 국제 연구 맥락을 방어하기 좋다.

그러나 현재 확보 상태에서는 다음처럼 제한해야 한다.

| 용도 | 사용 여부 | 이유 |
|---|---|---|
| schema adapter 검증 | 가능 | clip/document/metadata/query/qrels 변환 가능 |
| natural language-to-track text retrieval sanity check | 가능 | train NL description과 positive track qrels가 있음 |
| true multimodal main result | 불가 | `img1/*.jpg` 또는 track crop 추출 전 |
| visual embedding ablation | 불가 | crop/keyframe 생성 미완료 |
| image query experiment | 불가 | 이미지 query/source frame 추출 미완료 |
| 논문 본문 main table 추가 | 보류 | raw zip은 있으나 visual evidence materialization 전이라 주장이 약함 |

## raw zip 검증 후 편입 절차

raw zip은 확보 및 검증됐으므로 다음 순서로 편입한다.

1. 원본 zip은 `Datasets/external/cityflow_nl/aicity2023_track2`에 보존한다.
2. 압축 해제본은 `Datasets/raw/cityflow_nl/aicity2023_track2`에 둔다.
3. zip 내부 `vdo.avi`에서 annotation이 참조하는 frame 또는 track crop을 추출한다.
4. 추출 프레임은 `train/S01/c003/img1/000001.jpg` 같은 CityFlow-NL frame reference layout에 맞춘다.
5. `train-tracks.json`과 `test-tracks.json`의 `frames` 경로가 실제 파일로 resolve되는지 검사한다.
6. track별 대표 frame 또는 bounding box crop을 생성한다.
7. CLIP/SigLIP image encoder로 frame/crop embedding을 생성한다.
8. text query embedding과 visual track embedding을 같은 retrieval protocol에서 비교한다.
9. metadata prefilter 조건으로 split, scene, camera, time/frame range를 단계적으로 추가한다.
10. MRR, Recall@5, Recall@10과 본 연구의 evidence packet completeness를 함께 측정한다.

편입 후 실험 지위:

- CityFlow-NL은 VRU/AI Hub CCTV와 달리 `natural language vehicle-track retrieval`이라는 명시적 benchmark task를 제공하므로, 본 연구의 국제성 보강 실험으로 적합하다.
- 단, benchmark 규칙상 CityFlow Benchmark에서 사전학습된 모델 사용 금지 조건이 있으므로, 논문에서는 사용 모델의 pretraining source를 명확히 분리해야 한다.

## 다음 조치

1. 압축 해제 후 필요한 frame 또는 crop을 추출한다.
2. `present_frame_files`가 0이 아닌지 먼저 audit한 뒤 visual embedding pipeline에 투입한다.
3. frame reference mapping이 실패하면 CityFlow-NL은 계속 annotation-only 보조 검증으로 유지한다.

권장 명령:

```bash
unzip -t Datasets/external/cityflow_nl/aicity2023_track2/AICity23_Track2_NL_Retrieval.zip
mkdir -p Datasets/raw/cityflow_nl/aicity2023_track2
unzip -q Datasets/external/cityflow_nl/aicity2023_track2/AICity23_Track2_NL_Retrieval.zip \
  -d Datasets/raw/cityflow_nl/aicity2023_track2
```

## 확인 출처

- CityFlow-NL GitHub: https://github.com/fredfung007/cityflow-nl
- AI City Dataset Quick Access: https://www.aicitychallenge.org/ai-city-challenge-dataset-access/
- AI City 2023 Track 2 Download: https://www.aicitychallenge.org/2023-track2-download/
