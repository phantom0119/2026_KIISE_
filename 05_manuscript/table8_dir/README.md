# 표 8 관리 디렉터리 — pgvector 반복 스캔(iterative scan) 평가

## 1. 대상

**캡션 원문(현재 원고 기준, `manuscript/_archive_20260819/0_paper_script.md` 286행):**

> **&lt;표 8&gt; pgvector 반복 스캔 적용 시 메타데이터 조건별 검색 품질 및 지연 시간 비교 (시내도로 코퍼스, HNSW 색인. 부족률은 요청한 상위 10건 중 반환되지 못한 결과의 평균 비율)**

- 표 본문: 원고 279–284행 (4개 메타데이터 조건 × {기본 검색 재현율/부족률, 반복 스캔 재현율/부족률/p50}).
- 소속: **§5.2.5 물리 색인과 배포 평가 (RQ5)**. 표 8을 해설하는 본문 문단은 300행이며, 같은 문단의 **부분 색인(partial index) 문장**(선택도 0.011~0.774, 재현율 0.9812~0.9952, p50 0.407~0.454ms, 구축 0.38~39.15초, 크기 3.77~257.61MB, MIRIS 확장 장면 0.951~0.952)은 표 8 논의와 한 몸이므로 이 디렉터리에서 함께 관리한다.
- 실험 정체성: PostgreSQL 16.14 + pgvector 0.8.4의 전역 HNSW 색인(M=16)에서 `hnsw.iterative_scan = off`(기본 검색) vs `relaxed_order`(반복 스캔)를 4개 사전등록 조건(predicate)에 대해 비교.

## 2. 수치 ↔ 원천 매핑

표 8의 원천은 전부 `data/pgvector_filtered.csv`의 **`index=b3_hnsw_m16` 행(2~9행)**이다. 기본 검색=`iterative_scan=off` 행, 반복 스캔=`iterative_scan=relaxed_order` 행. 부족률(%)=`frac_short`×100.

| 원고 수치 (행) | 값 | 원천 파일(data/ 사본) | 파일 내 위치 (행 / 컬럼) |
|---|---|---|---|
| 장소=BC2000801 선택도 (281행) | 0.086 | data/pgvector_filtered.csv | 2행 `selectivity` (=data/P1_predicates_A.csv 2행 0.08644) |
| 〃 기본 재현율 | 0.121 | data/pgvector_filtered.csv | 2행 `recall_at_10`=0.1213 |
| 〃 기본 부족률 | 87.9% | data/pgvector_filtered.csv | 2행 `frac_short`=0.879 |
| 〃 반복 재현율 | 0.658 | data/pgvector_filtered.csv | 3행 `recall_at_10`=0.6584 |
| 〃 반복 부족률 | 5.8% | data/pgvector_filtered.csv | 3행 `frac_short`=0.058 |
| 〃 반복 p50 | 19.0 ms | data/pgvector_filtered.csv | 3행 `p50_ms`=18.964 |
| 장소=중동사거리 선택도 (282행) | 0.049 | data/pgvector_filtered.csv | 4행 `selectivity` (=P1_predicates_A.csv 3행 0.04851) |
| 〃 기본 재현율 | 0.034 | data/pgvector_filtered.csv | 4행 `recall_at_10`=0.0337 |
| 〃 기본 부족률 | 96.6% | data/pgvector_filtered.csv | 4행 `frac_short`=0.966 |
| 〃 반복 재현율 | 0.302 | data/pgvector_filtered.csv | 5행 `recall_at_10`=0.3021 |
| 〃 반복 부족률 | 50.8% | data/pgvector_filtered.csv | 5행 `frac_short`=0.508 |
| 〃 반복 p50 | 29.5 ms | data/pgvector_filtered.csv | 5행 `p50_ms`=29.512 |
| 시각=06 선택도 (283행) | 0.183 | data/pgvector_filtered.csv | 6행 `selectivity` (=P1_predicates_A.csv hour==06 0.18291) |
| 〃 기본 재현율 | 0.310 | data/pgvector_filtered.csv | 6행 `recall_at_10`=0.3103 |
| 〃 기본 부족률 | 75.0% | data/pgvector_filtered.csv | 6행 `frac_short`=0.75 |
| 〃 반복 재현율 | 0.984 | data/pgvector_filtered.csv | 7행 `recall_at_10`=0.9839 |
| 〃 반복 부족률 | 0.0% | data/pgvector_filtered.csv | 7행 `frac_short`=0.0 |
| 〃 반복 p50 | 1.01 ms | data/pgvector_filtered.csv | 7행 `p50_ms`=1.006 |
| 시각=06–18 선택도 (284행) | 0.774 | data/pgvector_filtered.csv | 8행 `selectivity` (=P1_predicates_A.csv daytime 0.7737) |
| 〃 기본 재현율 | 0.876 | data/pgvector_filtered.csv | 8행 `recall_at_10`=0.8761 |
| 〃 기본 부족률 | 14.2% | data/pgvector_filtered.csv | 8행 `frac_short`=0.142 |
| 〃 반복 재현율 | 0.994 | data/pgvector_filtered.csv | 9행 `recall_at_10`=0.9944 |
| 〃 반복 부족률 | 0.0% | data/pgvector_filtered.csv | 9행 `frac_short`=0.0 |
| 〃 반복 p50 | 0.44 ms | data/pgvector_filtered.csv | 9행 `p50_ms`=0.439 |
| 본문(300행) 시간 조건 "재현율 98% 이상 회복" | ≥0.98 | data/pgvector_filtered.csv | 7·9행 `recall_at_10`=0.9839, 0.9944 |
| 본문(300행) 장소 조건 "복구 30~65% 수준" | 0.302~0.658 | data/pgvector_filtered.csv | 3·5행 `recall_at_10` |
| 본문(300행) "지연 최대 29.51밀리초" | 29.51 ms | data/pgvector_filtered.csv | 5행 `p50_ms`=29.512 (relaxed_order 행 최대) |
| 본문(300행) 부분 색인 "6개" | 6 | data/pgvector_partial_vs_global.csv | `strategy=partial_local` 행 14~19행 (6행) |
| 본문(300행) 부분 색인 선택도 범위 | 0.011~0.774 | data/pgvector_partial_vs_global.csv | 14~19행 `selectivity` min=0.0109, max=0.7737 |
| 본문(300행) 부분 색인 재현율 | 0.9812~0.9952 | data/pgvector_partial_vs_global.csv | 17행(min)·19행(max) `recall_at_10` |
| 본문(300행) 부분 색인 p50 | 0.407~0.454 ms | data/pgvector_partial_vs_global.csv | 14행(min)·15행(max) `p50_ms` |
| 본문(300행) 부분 색인 구축 | 0.38~39.15 초 | data/pgvector_partial_vs_global.csv | 14행(min)·19행(max) `build_s` |
| 본문(300행) 부분 색인 크기 | 3.77~257.61 MB | data/pgvector_partial_vs_global.csv | 14행(min)·19행(max) `index_mb` |
| 본문(300행) MIRIS 확장 장면 재현율 저하 | 0.951~0.952 | data/pgvector_partial_vs_global_miris2.csv | `partial_local` 중 video IN(warsaw 3개)=0.9506, scene='warsaw'=0.9521 |
| 캡션 "시내도로 코퍼스" 규모·질의 수 | 132,521×512 / 질의 300개 | data/pgvector_manifest.json | `corpus`, `timing` 키 |

## 3. 사용 데이터셋

- **원본 데이터셋**: AI Hub 신내동 시내도로(sinnaedoro) CCTV 교통 영상 코퍼스. 프레임 132,521장 × CLIP ViT-B/32 512차원 임베딩(L2 정규화), 파일명에서 파싱한 장소(location)/일자(date)/시각(hour) 메타데이터.
  - 캐노니컬 경로(대용량, 미복사): `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/` — `frame_embeddings.npy`(271MB), `frame_index.parquet`(1.5MB), `queries.npy`(2.0MB, 평가 질의 벡터 1,000개 중 앞 300개를 타이밍/재현율 측정에 사용), `predicate_inventory.csv`.
- **가공 산출물(이 디렉터리에 사본)**: pgvector 측정 결과 CSV들(`pgvector_filtered.csv`, `pgvector_partial_vs_global*.csv`)과 매니페스트. 전처리는 임베딩·메타데이터를 pgvector 단일행 비정규화 테이블 `b3_frames(id, location, date, hour, embedding)`로 COPY 적재한 것이 전부이며, 재현율의 정답(GT)은 동일 연산자(`<#>`) 정확 seq-scan 검색이다.
- **MIRIS 확장 장면 문장의 원본**: MIRIS(SIGMOD) Warsaw+Shibuya 교차로 영상 12편 → 59,019 프레임 × 동일 CLIP 인코더 512차원, 풍부(공간/내용/시간) predicate 테이블 `miris_frames2`. 영상 저작권상 임베딩은 비재배포이며 수치 CSV만 남긴다(원 영상·임베딩 경로는 저장소 외부).

## 4. 실험 체계

- **사용 스크립트(절대경로)**
  - 표 8 본체: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/run_pgvector_ann_benchmark.py` — `pgvector_filtered.csv`/`pgvector_manifest.json`/`pgvector_ann_sweep.csv`를 생성하는 실제 러너(스크립트 220–222행에서 출력 확인). `run_pgvector_retrieval.py`는 표 8 원천이 아님.
  - 부분 색인 문장: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/run_pgvector_partial_index.py` — `pgvector_partial_vs_global*.csv` 생성(기본 out-name, `--table miris_frames2`로 MIRIS 변형).
  - MIRIS 적재 보조: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_miris_pgvector_rich.py` (miris_frames2 테이블 구축).
- **환경·모델·파라미터**
  - 서버: PostgreSQL 16.14 + pgvector 0.8.4 (docker `kiise-vlmdb-pgvector`, :5433, DSN `vlmdb/vlmdb`), `jit=off`, `max_parallel_maintenance_workers=0`.
  - 임베딩: CLIP ViT-B/32 512차원, L2 정규화 후 `<#>`(음의 내적)=코사인 동치(faiss-IP 동치).
  - 색인: 표 8은 전역 HNSW **M=16, ef_construction=200**(`b3_hnsw_m16`; CSV에는 IVF `b3_ivf_l1024` 행도 있으나 표에는 미사용). 부분 색인은 `CREATE INDEX ... USING hnsw ... WHERE p`.
  - 조건 4종: P1 사전등록(LOCKED) 코퍼스-A predicate 표에서 선정 — `location='BC2000801'`(0.086), `location='중동사거리'`(0.049), `hour=6`(0.183), `hour BETWEEN 6 AND 18`(0.774).
  - 타이밍: 단일 warm 커넥션, 질의 300개, 질의당 W=2 warm + R=5 반복의 중앙값 → 전 질의 p50/p95. 부족률=상위 k=10 중 미반환 비율 평균. 무작위 시드 `np.random.default_rng(20260710)`(스크립트 37행; 표 8 경로는 결정적 질의 집합이라 시드 영향 없음).
  - 경계: 클라이언트 왕복 계측 — faiss↔pgvector 절대 지연 비교 금지 [AMD-M3e].
- **사전등록/결과 문서(project_md/)**
  - 사전등록: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/420_METHOD_prereg_pillarBE_design_20260710.md` (§3 B-3 pgvector 실색인, M3 규정).
  - 결과: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/620_RESULTS_filtered_ann_real_predicates_20260710.md` (B-3 절 — 표 8 원결과), `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/720_RESULTS_db_design_storage_index_20260713.md` (P2 부분 색인 + MIRIS 재현). 두 문서는 data/에도 사본이 있다.

## 5. 재현 방법

**(A) 원천 재실행 경로(처음부터, docker pgvector 필요, 각 30–60분/10–20분)**

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety
# 0) pgvector 컨테이너 기동 (2026_KIISE/infra/docker-compose.pgvector.yml, :5433)
# 1) 표 8 본체: b3_frames 적재 + HNSW/IVF 구축 + off/relaxed_order 매트릭스
Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/scripts/run_pgvector_ann_benchmark.py
#    -> 2026_KIISE/paper_assets/20260710_pillarB/pgvector_filtered.csv 갱신
# 2) 부분 색인 문장: b3_frames 재사용
Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/scripts/run_pgvector_partial_index.py
#    -> 2026_KIISE/paper_assets/20260713_db_design/pgvector_partial_vs_global.csv
# 3) MIRIS 확장 장면 문장(선택): miris_frames2 구축(+miris_queries2.npy 생성) 후 동일 러너
Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/scripts/build_miris_pgvector_rich.py   # MIRIS 원영상 필요
Datasets/envs/kiise-vlmdb/bin/python 2026_KIISE/scripts/run_pgvector_partial_index.py \
  --table miris_frames2 \
  --query-npy Datasets/processed/miris_traffic/20260714/miris_queries2.npy \
  --predicates-sql "tseg BETWEEN 7 AND 7;video = 'warsaw_0';nobj >= 20;video IN ('warsaw_0','warsaw_1','warsaw_2');nobj >= 15;scene = 'warsaw'" \
  --out-name pgvector_partial_vs_global_miris2.csv \
  --manifest-name pgvector_partial_manifest_miris2.json \
  --corpus-label "miris_frames2 (59019 x 512, MIRIS warsaw+shibuya rich predicates (spatial/content/temporal))"
```

**(B) data/ 사본만으로 표 8 재집계(최소 경로, DB 불필요)**

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/table8_dir
python3 - <<'EOF'
import csv
rows=[r for r in csv.DictReader(open('data/pgvector_filtered.csv')) if r['index']=='b3_hnsw_m16']
by={(r['predicate'],r['iterative_scan']):r for r in rows}
for p,lab in [("location = 'BC2000801'","장소=BC2000801"),("location = '중동사거리'","장소=중동사거리"),
              ("hour = 6","시각=06"),("hour BETWEEN 6 AND 18","시각=06-18")]:
    o,rl=by[(p,'off')],by[(p,'relaxed_order')]
    print(f"{lab} ({float(o['selectivity']):.3f}) | {float(o['recall_at_10']):.3f} / "
          f"{float(o['frac_short'])*100:.1f}% | {float(rl['recall_at_10']):.3f} / "
          f"{float(rl['frac_short'])*100:.1f}% / {float(rl['p50_ms']):.2f} ms")
EOF
# 부분 색인 문장 범위: data/pgvector_partial_vs_global.csv에서 strategy=partial_local 6행의
# selectivity/recall_at_10/p50_ms/build_s/index_mb min~max를 취하면 원고 수치와 일치.
```

## 6. 포함 파일 목록

| 원 절대경로 → 사본명 (data/) | 설명 |
|---|---|
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260710_pillarB/pgvector_filtered.csv` → `pgvector_filtered.csv` | **표 8 원천.** 4 predicate × {HNSW-M16, IVF-1024} × {off, relaxed_order} 필터드 검색 측정 |
| `.../20260710_pillarB/pgvector_manifest.json` → `pgvector_manifest.json` | 표 8 실행 매니페스트(서버/코퍼스 132521×512/연산자/타이밍 300질의/GT 정의) |
| `.../20260710_pillarB/P1_predicates_A.csv` → `P1_predicates_A.csv` | 사전등록 LOCKED predicate 표 — 표 8 선택도 4개 값의 원출처 |
| `.../20260710_pillarB/P1_manifest.json` → `P1_manifest.json` | P1 predicate 추출 매니페스트 |
| `.../20260713_db_design/pgvector_partial_vs_global.csv` → `pgvector_partial_vs_global.csv` | **§5.2.5 부분 색인 문장 원천**(선택도 sweep 6조건, global off/relaxed vs partial_local) |
| `.../20260713_db_design/pgvector_partial_manifest.json` → `pgvector_partial_manifest.json` | 부분 색인 실험 매니페스트(전역 build 50.4s/333.5MB) |
| `.../20260713_db_design/pgvector_partial_vs_global_miris2.csv` → `pgvector_partial_vs_global_miris2.csv` | MIRIS 확장(rich) 장면 조건 — 본문 0.951~0.952의 원천 |
| `.../20260713_db_design/pgvector_partial_manifest_miris2.json` → `pgvector_partial_manifest_miris2.json` | MIRIS2 매니페스트(59,019×512, warsaw+shibuya) |
| `.../20260713_db_design/p2.log` → `p2.log` | 부분 색인 실행 로그(런 증적) |
| `.../20260713_db_design/miris_rich.log` → `miris_rich.log` | MIRIS2 구축·실행 로그(런 증적) |
| `.../2026_KIISE/project_md/620_RESULTS_filtered_ann_real_predicates_20260710.md` → `620_RESULTS_filtered_ann_real_predicates_20260710.md` | B-3 결과 요약 문서(표 8 해석의 캐노니컬 기록) |
| `.../2026_KIISE/project_md/720_RESULTS_db_design_storage_index_20260713.md` → `720_RESULTS_db_design_storage_index_20260713.md` | P2 부분 색인 + MIRIS 재현 결과 요약 문서 |

**미복사 대용량(경로 참조만)**

- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/frame_embeddings.npy` (271MB, 임베딩 원본)
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/frame_index.parquet` (1.5MB, 프레임 메타데이터 — parquet이라 미복사)
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/queries.npy` (2.0MB, 질의 벡터)
- MIRIS 원 영상·임베딩: 저작권상 비재배포(720 문서 §MIRIS 절 참조), 수치 CSV만 보존.

## 7. 검증

검증 방법: `data/` 사본을 python3(csv 모듈)로 실제 재조회하여 원고 표 8(279–284행)·본문 300행 수치와 대조했다(반올림 규칙: 재현율 3자리, 부족률 %, p50은 원고 표기 자릿수). **결과: 36/36 PASS, FAIL·UNVERIFIED 없음.**

| 검증 항목 | 원고 값 | data/ 재조회 값 | 판정 |
|---|---|---|---|
| 장소=BC2000801: 선택도/기본 재현율/기본 부족률 | 0.086 / 0.121 / 87.9% | 0.086 / 0.1213 / 0.879 | PASS |
| 장소=BC2000801: 반복 재현율/부족률/p50 | 0.658 / 5.8% / 19.0ms | 0.6584 / 0.058 / 18.964 | PASS |
| 장소=중동사거리: 선택도/기본 재현율/기본 부족률 | 0.049 / 0.034 / 96.6% | 0.049 / 0.0337 / 0.966 | PASS |
| 장소=중동사거리: 반복 재현율/부족률/p50 | 0.302 / 50.8% / 29.5ms | 0.3021 / 0.508 / 29.512 | PASS |
| 시각=06: 선택도/기본 재현율/기본 부족률 | 0.183 / 0.310 / 75.0% | 0.183 / 0.3103 / 0.75 | PASS |
| 시각=06: 반복 재현율/부족률/p50 | 0.984 / 0.0% / 1.01ms | 0.9839 / 0.0 / 1.006 | PASS |
| 시각=06–18: 선택도/기본 재현율/기본 부족률 | 0.774 / 0.876 / 14.2% | 0.774 / 0.8761 / 0.142 | PASS |
| 시각=06–18: 반복 재현율/부족률/p50 | 0.994 / 0.0% / 0.44ms | 0.9944 / 0.0 / 0.439 | PASS |
| 본문: 시간 조건 재현율 98% 이상 회복 | ≥0.98 | 0.9839, 0.9944 | PASS |
| 본문: 장소 복구 30~65% 수준 | 0.302~0.658 | 0.3021~0.6584 | PASS |
| 본문: 지연 최대 29.51ms | 29.51 | 29.512 (relaxed 행 최대) | PASS |
| 본문: 부분 색인 6개 | 6 | partial_local 6행 | PASS |
| 본문: 부분 색인 선택도 0.011~0.774 | 0.011~0.774 | 0.0109~0.7737 | PASS |
| 본문: 부분 색인 재현율 0.9812~0.9952 | 0.9812~0.9952 | 0.9812~0.9952 | PASS |
| 본문: 부분 색인 p50 0.407~0.454ms | 0.407~0.454 | 0.407~0.454 | PASS |
| 본문: 부분 색인 구축 0.38~39.15초 | 0.38~39.15 | 0.38~39.15 | PASS |
| 본문: 부분 색인 크기 3.77~257.61MB | 3.77~257.61 | 3.77~257.61 | PASS |
| 본문: MIRIS 확장 장면 0.951~0.952 | 0.951~0.952 | 0.9506, 0.9521 (miris2 최저 2건) | PASS |
| 캡션: 시내도로 132,521×512 / 질의 300개 | — | manifest `corpus`·`timing` 일치 | PASS |

주의: `pgvector_filtered.csv`에는 IVF(`b3_ivf_l1024`) 행 8개도 포함되나 표 8은 HNSW(`b3_hnsw_m16`) 행만 사용한다(캡션 "HNSW 색인" 명시와 일치). MIRIS 확장 장면 수치는 `pgvector_partial_vs_global_miris2.csv`(rich predicate 버전)가 원천이며, 비-rich 버전(`pgvector_partial_vs_global_miris.csv`, 미복사)의 partial 재현율은 전부 ≥0.9979라서 해당 문장과 무관함을 확인했다.
