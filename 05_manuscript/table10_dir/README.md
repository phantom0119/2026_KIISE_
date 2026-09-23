# 표 10 프로비넌스 패키지 (table10_dir)

## 1. 대상

- **캡션 원문 (현재 원고 기준, `manuscript/_archive_20260819/0_paper_script.md` L318):**
  > **&lt;표 10&gt; 조건이 없는 두 실측 코퍼스의 물리 색인 품질 및 비용 비교 (각 행의 규모는 원본 벡터 풀 132,521개와 143,830개에서 고정한 실제 벤치마크 규모 131,000개와 142,000개이며 반올림 값이 아님)**
- **표 본문 위치:** `0_paper_script.md` L303–L317 (12행 × 4수치열: 재현율@10, p50/p95(ms), 구축(초), 크기(MB)).
- **소속 절/RQ:** 5.2.5 "물리 색인과 배포 평가 (RQ5)". 표 10은 조건(메타데이터 필터) 개입이 없는 기본 물리 색인 프로파일의 기준선이며, L320의 배포 기준(전역 재현율 0.95 미달 시 부분 색인/전수 검색 활성화) 논거의 출발점이다.

## 2. 수치 ↔ 원천 매핑

두 원천 CSV의 행 선택 규칙: **시내도로 = `data/index_benchmark_from_log.csv`의 N=131000 행**, **교차로 = `data/index_benchmark.csv`의 N=142000 행**. 원고의 HNSW 행은 efSearch=64 행, IVF-Flat/IVF-PQ 행은 nlist=1024·nprobe=8 행이다(원고 라벨에는 efSearch·nlist 생략). 파일 내 위치는 헤더 포함 1-기준 행 번호.

| 원고 값 (행 라벨) | 원천 파일 (data/ 사본) | 파일 내 위치 (행 / 컬럼) |
|---|---|---|
| 시내도로 Flat: 1.0000 / 13.43 / 14.37 / 0.11 / 268.0 | `data/index_benchmark_from_log.csv` | 17행 (N=131000, kind=flat) / recall_at_10=1.0, p50_ms=13.426, p95_ms=14.373, build_s=0.11, index_mb=268.0 |
| 시내도로 HNSW(M=16): 0.9970 / 0.041 / 0.055 / 34.8 / 287.0 | `data/index_benchmark_from_log.csv` | 31행 (hnsw, M=16, efSearch=64) / 0.997, 0.041, 0.055, 34.76, 287.0 |
| 시내도로 HNSW(M=32): 0.9970 / 0.044 / 0.062 / 36.5 / 304.0 | `data/index_benchmark_from_log.csv` | 34행 (hnsw, M=32, efSearch=64) / 0.997, 0.044, 0.062, 36.49, 304.0 |
| 시내도로 IVF-Flat(nprobe=8): 0.9940 / 0.113 / 0.144 / 13.9 / 271.0 | `data/index_benchmark_from_log.csv` | 23행 (ivfflat, nlist=1024, nprobe=8) / 0.994, 0.113, 0.144, 13.9, 271.0 |
| 시내도로 IVF-PQ(m=64): 0.4810 / 0.135 / 0.158 / 26.1 / 12.0 | `data/index_benchmark_from_log.csv` | 38행 (ivfpq, m=64, nprobe=8) / 0.481, 0.135, 0.158, 26.07, 12.0 |
| 시내도로 IVF-PQ(m=32): 0.3340 / 0.129 / 0.153 / 25.9 / 8.0 | `data/index_benchmark_from_log.csv` | 36행 (ivfpq, m=32, nprobe=8) / 0.334, 0.129, 0.153, 25.94, 8.0 |
| 교차로 Flat: 1.0000 / 14.18 / 15.34 / 0.12 / 290.8 | `data/index_benchmark.csv` | 17행 (N=142000, kind=flat) / 1.0, 14.1843, 15.3358, 0.116, 290.82 |
| 교차로 HNSW(M=16): 0.9994 / 0.044 / 0.061 / 44.3 / 311.3 | `data/index_benchmark.csv` | 31행 (hnsw, M=16, efSearch=64) / 0.9994, 0.0435, 0.0607, 44.343, 311.31 |
| 교차로 HNSW(M=32): 0.9992 / 0.047 / 0.069 / 47.1 / 329.5 | `data/index_benchmark.csv` | 34행 (hnsw, M=32, efSearch=64) / 0.9992, 0.0473, 0.0693, 47.067, 329.47 |
| 교차로 IVF-Flat(nprobe=8): 0.9971 / 0.116 / 0.165 / 15.1 / 294.1 | `data/index_benchmark.csv` | 23행 (ivfflat, nlist=1024, nprobe=8) / 0.9971, 0.116, 0.1649, 15.105, 294.06 |
| 교차로 IVF-PQ(m=64): 0.4938 / 0.134 / 0.172 / 27.9 / 12.9 | `data/index_benchmark.csv` | 38행 (ivfpq, m=64, nprobe=8) / 0.4938, 0.1343, 0.172, 27.886, 12.85 |
| 교차로 IVF-PQ(m=32): 0.3489 / 0.131 / 0.157 / 27.1 / 8.3 | `data/index_benchmark.csv` | 36행 (ivfpq, m=32, nprobe=8) / 0.3489, 0.1311, 0.1573, 27.09, 8.31 |
| 캡션: 원본 벡터 풀 132,521 (시내도로) | `data/600_RESULTS_index_structure_benchmark_20260709.md` | 9행 "real 132,521 벡터"; 실물 확인은 §7 참조 (`corpus_real/frame_embeddings.npy` shape=(132521, 512)) |
| 캡션: 원본 벡터 풀 143,830 (교차로) | `data/manifest.json` | 키 `n_vectors`=143830 |
| 캡션: 고정 벤치마크 규모 131,000 | `data/index_benchmark_from_log.csv` | N 컬럼 값 131000 (17–38행) — `--scales` 인자로 고정한 표집 규모 |
| 캡션: 고정 벤치마크 규모 142,000 | `data/manifest.json` + `data/index_benchmark.csv` | `scales`=[10000,50000,100000,142000]; N 컬럼 값 142000 |

## 3. 사용 데이터셋

- **시내도로 (AI Hub 시내도로 교통 CCTV):** JPG 프레임을 원천 131개 zip에서 위치·카메라·시간 층화 스트리밍으로 추출해 CLIP ViT-B/32 (512차원)로 임베딩한 **132,521 벡터** (16,107 카메라 / 39 위치). 캐노니컬 산출물: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/frame_embeddings.npy` (shape 132521×512; `Datasets`는 `/hdd2/KIISE_datasociety/Datasets` 심링크). 별도 held-out 질의 1,000개는 같은 디렉터리의 `queries.npy`.
- **교차로 (AI Hub 522 교차로 CCTV):** 교차로 영상 프레임을 동일 인코더(CLIP ViT-B/32, 512차원)로 임베딩한 **143,830 벡터**. 캐노니컬 산출물: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip/frame_embeddings.npy`. 벤치마크 시 1,000개 질의를 코퍼스에서 무작위 분리(고정 시드) 후 잔여 풀에서 규모를 고정.
- 전처리 요약: 프레임 추출 → CLIP 임베딩 → L2 정규화(코사인=내적) → 질의 1,000개 분리 → `--scales`로 고정한 규모(…,131000 / …,142000)만큼 풀 앞에서 절단. 규모 131,000/142,000은 반올림 표기가 아니라 스크립트 인자로 고정된 실제 색인 벡터 수다(질의 1,000개 분리 후 풀 이하의 라운드 규모).

## 4. 실험 체계

- **벤치마크 스크립트:** `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/run_index_structure_benchmark.py` — FAISS CPU 전용. 구조만 변수(Flat / IVF-Flat(nlist 256·1024·4096 × nprobe 1·8·32·128) / HNSW(M 16·32 × efSearch 16·64·256, efConstruction 200) / IVF-PQ(nlist 1024, m 32·64, nbits 8)). 정확도=exact Flat 대비 ANN-recall@10 (k=10), 지연=`index.search`만 단일 스레드 격리 계측(warmup 5 폐기, repeats 20 × 질의 1,000, p50/p95/p99), 구축=전 스레드 벽시계, 크기=직렬화 바이트. metric=inner_product(정규화 코사인).
- **코퍼스 구축 스크립트:** `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_sinnaedoro_visual.py` (시내도로), `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/extract_intersection_visual_sources.py`·`build_visual_embeddings.py` (교차로 계열).
- **모델·임베딩:** CLIP ViT-B/32, 512차원, 두 코퍼스 동일 인코더. 생성 모델 불사용(순수 색인 벤치마크).
- **시드·파라미터:** 질의 분리 시드 20260709 (`np.random.default_rng(20260709)`; 스크립트 기본 `--seed`(색인 학습용)는 현행본 기준 20260717, 교차로 manifest에는 seed 키가 없어 당시 실행본의 기록은 부재). k=10, n_queries=1000, repeats=20, warmup=5, faiss_threads_latency=1.
- **결과 문서 (project_md/):**
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/600_RESULTS_index_structure_benchmark_20260709.md` — 시내도로 색인 3축 결과(사본 동봉).
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/620_RESULTS_filtered_ann_real_predicates_20260710.md` — §B-2에 교차로(522-visual) 복제 그리드 기록(사본 동봉).
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/420_METHOD_prereg_pillarBE_design_20260710.md` — 사전등록: 시내도로 `index_benchmark_from_log.csv`를 "신규 계산 0"으로 본문 자산화하기로 한 결정(L31).
  - 검증 스크립트 `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/verify_manuscript_numbers.py` L138–140이 교차로 그리드의 HNSW(M=32) 0.9992를 상시 대조.

## 5. 재현 방법

**(A) 원천 재실행 경로 (처음부터):**
```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE
# 1) 시내도로: 코퍼스 구축(원천 zip 필요) 후 벤치마크
python3 scripts/build_sinnaedoro_visual.py   # → Datasets/processed/sinnaedoro_traffic/corpus_real/
python3 scripts/run_index_structure_benchmark.py \
  --corpus ../Datasets/processed/sinnaedoro_traffic/corpus_real/frame_embeddings.npy \
  --queries ../Datasets/processed/sinnaedoro_traffic/corpus_real/queries.npy \
  --scales 10000,50000,100000,131000 --full-grid-at 131000 \
  --repeats 20 --out <출력디렉터리>
# 2) 교차로: manifest.json 기록과 동일 인자
python3 scripts/run_index_structure_benchmark.py \
  --corpus ../Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip/frame_embeddings.npy \
  --scales 10000,50000,100000,142000 --full-grid-at 142000 \
  --n-queries 1000 --repeats 20 --out <출력디렉터리>
```
주의: 지연·구축 시간은 하드웨어 의존이라 절대값은 동일 기기(CPU FAISS, 단일 스레드 계측)에서만 재현된다. recall·index_mb는 기기 무관. 시내도로 실행의 정확한 원 커맨드라인은 보존되어 있지 않다(§7 참고).

**(B) data/ 사본만으로 재집계 (최소 경로):**
```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/table10_dir
python3 verify_table10.py   # 표 10의 60개 셀 + 캡션 규모 5건 전수 대조(PASS/FAIL 출력)
```
또는 수동으로: `data/index_benchmark_from_log.csv`에서 N=131000 행, `data/index_benchmark.csv`에서 N=142000 행을 필터하고, kind=flat / hnsw(efSearch=64) / ivfflat(nlist=1024, nprobe=8) / ivfpq(nprobe=8, m∈{32,64}) 행의 recall_at_10, p50_ms, p95_ms, build_s, index_mb를 원고 자릿수로 반올림해 대조한다.

## 6. 포함 파일 목록

| 원 절대경로 | 사본명 | 설명 |
|---|---|---|
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/index_benchmark/index_benchmark_from_log.csv` | `data/index_benchmark_from_log.csv` | 시내도로 색인 벤치마크 결과(10K–1M, 55 config). 표 10 좌측 6행의 원천(N=131000). 실행 로그에서 재구성된 CSV. |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260710_pillarB/index_grid_522visual/index_benchmark.csv` | `data/index_benchmark.csv` | 교차로(522-visual) 색인 벤치마크 결과(10K–142K, 38 config). 표 10 우측 6행의 원천(N=142000). |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260710_pillarB/index_grid_522visual/manifest.json` | `data/manifest.json` | 교차로 실행 manifest — corpus 경로, n_vectors=143830, scales(142000 고정 표집 근거), n_queries=1000, repeats=20. |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/600_RESULTS_index_structure_benchmark_20260709.md` | `data/600_RESULTS_index_structure_benchmark_20260709.md` | 시내도로 결과 문서 — 코퍼스 132,521 규모·스케일 축(13.1만=real max)·방법 기록. |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/620_RESULTS_filtered_ann_real_predicates_20260710.md` | `data/620_RESULTS_filtered_ann_real_predicates_20260710.md` | §B-2에 교차로 복제 그리드(142K, 38 config) 요약 기록. |

**복사하지 않은 대용량/제외 파일 (경로 참조만):**
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/frame_embeddings.npy` — 시내도로 임베딩 원본 (271MB, 132521×512 float32).
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/queries.npy` — held-out 질의 1,000×512 (2MB, 임베딩 덤프라 제외).
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/frame_index.parquet` — 프레임 메타데이터 (parquet, 1.5MB).
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip/frame_embeddings.npy` — 교차로 임베딩 원본 (294MB, 143830×512 float32).
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260710_pillarB/index_grid_522visual/index_benchmark.parquet` — 교차로 CSV와 동일 내용의 parquet (12KB).
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_aug_1m.npy` — 합성 증강 1M 벡터(표 10 미사용).

## 7. 검증

`verify_table10.py`(data/ 사본만 사용)로 2026-07-23 실행. 판정: 원고 인쇄 자릿수 반올림 일치(|원고−원천| ≤ 0.5×10^−d). **총 65건 PASS / 0건 FAIL.**

| 검증 항목 | 건수 | 판정 |
|---|---|---|
| 시내도로 6행 × 5수치 (recall/p50/p95/build/크기) | 30 | **PASS** (전건) |
| 교차로 6행 × 5수치 | 30 | **PASS** (전건) |
| 캡션 143,830 (manifest `n_vectors`) | 1 | **PASS** |
| 캡션 142,000 (manifest `scales` + CSV N열) | 1+1 | **PASS** |
| 캡션 131,000 (CSV N열) | 1 | **PASS** |
| 캡션 132,521 (600 문서 기재) | 1 | **PASS** |

추가로 data/ 밖 실물 재확인(2026-07-23): `corpus_real/frame_embeddings.npy` shape=(132521, 512), `aihub_522_intersection/.../frame_embeddings.npy` shape=(143830, 512), `queries.npy` shape=(1000, 512) — 캡션의 두 원본 풀 수치와 정확히 일치.

**정직 고지 (불일치 아님, 정밀도·기록 한계):**
1. **시내도로 recall 4째 자리는 표기 패딩** — 원천 `index_benchmark_from_log.csv`는 실행 로그 stdout(소수 3자리 출력)에서 재구성된 파일이라 recall이 3자리(0.997 등)까지만 존재한다. 원고의 0.9970/0.9940/0.4810/0.3340은 3자리 값의 0-패딩이며 4째 자리의 독립 근거는 없다(교차로 측은 4자리 원본과 완전 일치).
2. **시내도로 실행의 원본 manifest.json·parquet·stdout 로그는 미보존** — 산출 디렉터리에 `index_benchmark_from_log.csv`만 남아 있고, 로그→CSV 재구성 사실은 `project_md/420_METHOD_prereg_pillarBE_design_20260710.md` L31에 기록되어 있다. 따라서 131,000 고정 표집의 1차 근거는 CSV N열과 600 문서(스케일 축 "13.1만(real max)")이며, 교차로처럼 manifest로 교차 확인할 수는 없다 → 이 항목만 **간접 검증**(수치 자체는 전건 PASS).
3. 교차로 manifest에는 `seed` 키가 없다(당시 스크립트 버전이 seed를 manifest에 기록하기 전). 질의 분리 시드 20260709는 스크립트 코드의 고정값으로 확인.
