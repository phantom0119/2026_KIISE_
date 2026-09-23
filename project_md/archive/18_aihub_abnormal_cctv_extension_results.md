# AI Hub 이상행동 CCTV 보강 실험

작성 기준일: 2026-07-07

2026-07-09 최신 갱신: AI Hub 이상행동 CCTV는 최신 원고에서도 label-aligned text/metadata 보조 baseline 역할로 유지한다. 본문 핵심 수치는 VRU/AI Hub 지능형 CCTV retrieval, AI Hub 다각도 CCTV VLM answer-level, 시내도로 CCTV index benchmark가 담당한다. 최신 데이터셋 역할은 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 목적

`이상행동 CCTV 영상` 데이터는 국내 고정형 CCTV 환경에서 폭행, 싸움, 절도, 기물파손, 실신, 배회, 침입, 투기, 강도, 데이트폭력및추행, 납치, 주취행동과 같은 생활안전 이벤트를 포함한다. 본 연구에서는 VRU-Accident의 교통 사고 중심 주장을 대체하지 않고, 도시 감시형 CCTV 라벨 데이터에서도 동일한 `clip-document-metadata-query-qrels` schema와 retrieval protocol이 작동하는지 확인하는 보강 데이터셋으로 사용한다.

## 원본 관리 전략

원본 데이터는 573GB 규모의 zip 파일 묶음이며 내부에 mp4 영상과 XML 라벨이 함께 들어 있다. 전체 영상을 압축 해제하면 저장소 사용량이 급증하므로, 원본 zip은 그대로 보존하고 XML 라벨만 raw 영역에 추출하였다. 각 영상은 `zip://<zip_path>!<entry>` URI로 참조한다.

| 항목 | 경로/값 |
|---|---|
| 원본 zip root | `Datasets/external/이상탐지/이상행동 CCTV 영상` |
| raw 정리본 | `Datasets/raw/aihub_abnormal_cctv/20260707` |
| canonical 산출물 | `Datasets/processed/aihub_abnormal_cctv/20260707/canonical` |
| bge-m3 embedding | `Datasets/processed/aihub_abnormal_cctv/20260707/embeddings/bge-m3` |
| e5-large-v2 embedding | `Datasets/processed/aihub_abnormal_cctv/20260707/embeddings/e5-large-v2` |
| bge-m3 결과 | `Datasets/processed/aihub_abnormal_cctv/20260707/results/abnormal_bgem3_faiss_b0_b5` |
| e5-large-v2 결과 | `Datasets/processed/aihub_abnormal_cctv/20260707/results/abnormal_e5_faiss_b0_b5` |

## Raw 정리 결과

| item | count |
|---|---:|
| zip files | 24 |
| zip bytes | 614,551,301,175 |
| zip entries | 3,954 |
| mp4 entries | 1,977 |
| xml entries | 1,977 |
| paired clips | 1,977 |
| pairs with label | 1,968 |
| errors | 9 |

9개 XML은 대응 mp4가 없어 canonical workload에서 제외하였다. 모두 `02.싸움(fight)/inside_croki_01.zip` 내부 `22-1/*.xml` 항목이며, 상세 로그는 `Datasets/raw/aihub_abnormal_cctv/20260707/prepare_errors.csv`에 남겼다.

## Canonical 규모

| artifact | count |
|---|---:|
| clips | 1,968 |
| documents | 5,904 |
| metadata rows | 33,456 |
| retrieval queries | 424 |
| qrels | 21,639 |
| missing labels | 9 |

query 난도:

| difficulty | queries | qrels | avg positives |
|---|---:|---:|---:|
| weak | 27 | 3,935 | 145.74 |
| medium | 134 | 9,838 | 73.42 |
| strong | 263 | 7,866 | 29.91 |

metadata facet은 `event_name`, `event_text`, `event_ko`, `event_variant`, `primary_action`, `actions`, `camera_id`, `scene_id`, `location`, `place_id`, `season`, `weather`, `daypart`, `inout`, `population_bucket`, `character`, `resolution`로 구성하였다.

## 구현

| 구성요소 | 파일 |
|---|---|
| raw zip 정리 | `2026_KIISE/scripts/prepare_aihub_abnormal_cctv_raw.py` |
| canonical adapter | `2026_KIISE/src/vlmdb_workload/adapters/aihub_abnormal_cctv.py` |
| canonical build script | `2026_KIISE/scripts/build_aihub_abnormal_cctv_canonical.py` |
| 공통 embedding build | `2026_KIISE/scripts/build_text_embeddings.py` |
| 공통 retrieval baseline | `2026_KIISE/scripts/run_retrieval_baselines.py` |

adapter는 XML header의 시간, 장소, 계절, 날씨, 실내외, 인원, 등장인물 정보와 event/action annotation을 canonical metadata로 변환한다. 질의는 event/action 중심의 weak query, context metadata가 결합된 medium query, event/action/context가 함께 들어간 strong query로 생성한다.

## 실행 명령

```bash
conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/prepare_aihub_abnormal_cctv_raw.py --overwrite

conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_aihub_abnormal_cctv_canonical.py --overwrite

conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_text_embeddings.py \
  --canonical-root Datasets/processed/aihub_abnormal_cctv/20260707/canonical \
  --model-id bge-m3 \
  --batch-size 16 \
  --overwrite

conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/run_retrieval_baselines.py \
  --canonical-root Datasets/processed/aihub_abnormal_cctv/20260707/canonical \
  --embedding-root Datasets/processed/aihub_abnormal_cctv/20260707/embeddings/bge-m3 \
  --output-dir Datasets/processed/aihub_abnormal_cctv/20260707/results/abnormal_bgem3_faiss_b0_b5 \
  --overwrite

conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/build_text_embeddings.py \
  --canonical-root Datasets/processed/aihub_abnormal_cctv/20260707/canonical \
  --model-id e5-large-v2 \
  --batch-size 16 \
  --overwrite

conda run -p Datasets/envs/kiise-vlmdb python 2026_KIISE/scripts/run_retrieval_baselines.py \
  --canonical-root Datasets/processed/aihub_abnormal_cctv/20260707/canonical \
  --embedding-root Datasets/processed/aihub_abnormal_cctv/20260707/embeddings/e5-large-v2 \
  --output-dir Datasets/processed/aihub_abnormal_cctv/20260707/results/abnormal_e5_faiss_b0_b5 \
  --overwrite
```

## bge-m3 결과

| strategy | recall@10 | recall@20 | MRR | nDCG@10 | mean latency |
|---|---:|---:|---:|---:|---:|
| B0 metadata-only | 0.0776 | 0.1498 | 0.1944 | 0.1840 | 0.071 ms |
| B1 BM25-only | 0.3904 | 0.6247 | 0.9979 | 0.9970 | 115.064 ms |
| B2 vector-only | 0.2114 | 0.3543 | 0.7044 | 0.6451 | 103.039 ms |
| B3 vector postfilter | 0.3770 | 0.6058 | 0.9641 | 0.9624 | 4.846 ms |
| B4 prefilter vector | 0.3770 | 0.6063 | 0.9641 | 0.9624 | 30.387 ms |
| B5 hybrid | 0.3901 | 0.6256 | 0.9977 | 0.9946 | 144.244 ms |

## e5-large-v2 결과

| strategy | recall@10 | recall@20 | MRR | nDCG@10 | mean latency |
|---|---:|---:|---:|---:|---:|
| B0 metadata-only | 0.0776 | 0.1498 | 0.1944 | 0.1840 | 0.070 ms |
| B1 BM25-only | 0.3904 | 0.6247 | 0.9979 | 0.9970 | 112.541 ms |
| B2 vector-only | 0.2268 | 0.3868 | 0.7493 | 0.7115 | 100.090 ms |
| B3 vector postfilter | 0.3841 | 0.6142 | 0.9849 | 0.9832 | 4.688 ms |
| B4 prefilter vector | 0.3848 | 0.6188 | 0.9849 | 0.9840 | 28.049 ms |
| B5 hybrid | 0.3905 | 0.6259 | 0.9977 | 0.9954 | 139.211 ms |

## 해석

- 이 데이터셋은 XML event/action label과 query term이 직접 정렬되어 있어 BM25와 hybrid가 매우 강하다. 따라서 이 결과를 embedding model 우수성 주장으로 쓰면 부적절하다.
- 그럼에도 B2 vector-only는 bge-m3 기준 nDCG@10 0.6451, e5-large-v2 기준 0.7115에 머무는 반면, B4/B5는 0.9840 이상까지 올라간다. 즉 국내 이상행동 CCTV 라벨 환경에서도 metadata-aware retrieval 구조는 vector-only를 보완한다.
- B3와 B4 차이가 작게 나온 이유는 질의와 라벨의 lexical 정렬이 강하고, 현재 후보 수 설정에서 postfilter가 relevant 후보를 충분히 포함하기 때문이다. 이 결과는 prefilter 우위의 주장을 약화시키기보다, 데이터셋 조건에 따라 sparse/hybrid가 강한 구간이 있음을 보여주는 보강 분석으로 해석한다.
- 논문 본문에서는 VRU-Accident를 main result로 유지하고, AI Hub 지능형 CCTV와 이상행동 CCTV를 국내 CCTV external validity 및 schema portability 근거로 배치하는 것이 안전하다.
