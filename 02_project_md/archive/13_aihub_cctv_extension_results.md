# AI Hub 지능형 CCTV 보강 실험

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 본 문서는 AI Hub 지능형 CCTV의 text/metadata 확장 결과를 기록한다. 이후 동일 데이터셋에서 keyframe visual retrieval, fusion, image-to-video, service packet까지 확장되었고, 별도 AI Hub 다각도 CCTV에서는 fixed VLM multi-view answer-level 실험이 완료되었다. 최신 해석은 `21_true_multimodal_execution_status_20260707.md`와 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 목적

VRU-Accident는 교통 안전 VideoQA와 dense caption을 즉시 사용할 수 있다는 장점이 있지만, 대시캠 사고 영상 중심이다. AI Hub 지능형 관제 서비스 CCTV 영상 데이터는 국내 고정형 CCTV 생활안전 이벤트를 포함하므로, 본 연구의 "도시 감시형 멀티모달 데이터베이스" 주장을 보강하는 확장 데이터셋으로 사용한다.

## 현재 상태

| 항목 | 경로/값 |
|---|---|
| raw 정리본 | `Datasets/raw/aihub_intelligent_cctv/20260706` |
| canonical 산출물 | `Datasets/processed/aihub_intelligent_cctv/20260706/canonical` |
| bge-m3 embedding | `Datasets/processed/aihub_intelligent_cctv/20260706/embeddings/bge-m3` |
| e5-large-v2 embedding | `Datasets/processed/aihub_intelligent_cctv/20260706/embeddings/e5-large-v2` |
| bge-m3 결과 | `Datasets/processed/aihub_intelligent_cctv/20260706/results/aihub_bgem3_faiss_b0_b5` |
| e5-large-v2 결과 | `Datasets/processed/aihub_intelligent_cctv/20260706/results/aihub_e5_faiss_b0_b5` |

## Canonical 규모

| artifact | count |
|---|---:|
| clips | 269 |
| documents | 807 |
| metadata rows | 2,563 |
| retrieval queries | 133 |
| qrels | 1,358 |
| missing media | 0 |
| missing labels | 0 |

query 난도:

| difficulty | queries | qrels | avg positives |
|---|---:|---:|---:|
| weak | 22 | 537 | 24.41 |
| medium | 59 | 558 | 9.46 |
| strong | 52 | 263 | 5.06 |

## 구현

| 구성요소 | 파일 |
|---|---|
| raw zip 정리 | `2026_KIISE/scripts/prepare_aihub_cctv_raw.py` |
| canonical adapter | `2026_KIISE/src/vlmdb_workload/adapters/aihub_intelligent_cctv.py` |
| canonical build script | `2026_KIISE/scripts/build_aihub_cctv_canonical.py` |

adapter는 `event_caption`, `event_class`, `event_frame`, `night`, `date`, `flood_level`, `place_type`, `crowd_context`를 canonical schema로 변환한다. 질의 생성은 VRU와 동일하게 의미 조건과 metadata 조건을 분리한다.

## 실행 명령

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/prepare_aihub_cctv_raw.py
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_aihub_cctv_canonical.py --overwrite
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_text_embeddings.py \
  --canonical-root Datasets/processed/aihub_intelligent_cctv/20260706/canonical \
  --model-id bge-m3 \
  --batch-size 16 \
  --overwrite
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/run_retrieval_baselines.py \
  --canonical-root Datasets/processed/aihub_intelligent_cctv/20260706/canonical \
  --embedding-root Datasets/processed/aihub_intelligent_cctv/20260706/embeddings/bge-m3 \
  --output-dir Datasets/processed/aihub_intelligent_cctv/20260706/results/aihub_bgem3_faiss_b0_b5 \
  --overwrite
```

## bge-m3 결과

| strategy | recall@10 | recall@20 | MRR | nDCG@10 | mean latency |
|---|---:|---:|---:|---:|---:|
| B0 metadata-only | 0.7296 | 0.7708 | 0.6472 | 0.6985 | 0.010 ms |
| B1 BM25-only | 0.8524 | 0.9380 | 0.9570 | 0.9600 | 14.289 ms |
| B2 vector-only | 0.6565 | 0.8423 | 0.7332 | 0.7014 | 13.469 ms |
| B3 vector postfilter | 0.8644 | 0.9404 | 1.0000 | 1.0000 | 3.475 ms |
| B4 prefilter vector | 0.8644 | 0.9404 | 1.0000 | 1.0000 | 3.296 ms |
| B5 hybrid | 0.8639 | 0.9393 | 1.0000 | 0.9977 | 17.131 ms |

## e5-large-v2 결과

| strategy | recall@10 | recall@20 | MRR | nDCG@10 | mean latency |
|---|---:|---:|---:|---:|---:|
| B0 metadata-only | 0.7296 | 0.7708 | 0.6472 | 0.6985 | 0.010 ms |
| B1 BM25-only | 0.8524 | 0.9380 | 0.9570 | 0.9600 | 14.470 ms |
| B2 vector-only | 0.7551 | 0.9016 | 0.8138 | 0.8042 | 13.644 ms |
| B3 vector postfilter | 0.8632 | 0.9380 | 0.9927 | 0.9925 | 3.540 ms |
| B4 prefilter vector | 0.8632 | 0.9380 | 0.9927 | 0.9925 | 3.312 ms |
| B5 hybrid | 0.8632 | 0.9380 | 0.9927 | 0.9925 | 17.471 ms |

## 해석

- 국내 CCTV 데이터에서도 metadata-aware 전략 B3/B4/B5가 vector-only보다 높다.
- AI Hub 데이터는 label caption과 event metadata가 강하게 정렬되어 있어, BM25-only도 매우 강하다.
- 데이터 규모가 269 clips로 작고 postfilter 후보 수가 충분히 크기 때문에 B3와 B4가 거의 동일하게 나온다. 이 결과는 main claim보다는 "국내 CCTV 데이터에도 동일 프로토콜 적용 가능"이라는 보강 근거로 쓰는 것이 안전하다.
- 논문 본문에서는 VRU를 main result, AI Hub를 external validity 및 국내 CCTV 보강 실험으로 배치하는 것이 적절하다.
