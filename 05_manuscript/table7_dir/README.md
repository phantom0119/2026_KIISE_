# 표 7 관리 디렉터리 — 실제 시공간 군집 조건 vs 무작위 대조 조건의 근사 색인 재현율 왜곡 효과(Δ)

## 1. 대상

- **Caption 원문(현재 원고 기준)**: `**<표 7> 실제 시공간 군집 조건과 무작위 대조 조건 간의 근사 색인 재현율 왜곡 효과(Δ) 비교**`
- **원고 내 위치**: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/_archive_20260819/0_paper_script.md`
  - 표 본문: 267–273행, caption: 275행
  - 표를 소개하는 본문 문장: 265행("표 7은 실제 환경에서 수집된 장소·시간 등의 메타데이터 조건이 근사 색인(ANN)의 검색 재현율에 미치는 성능 영향을…"), 후속 설명: 277행
- **소속 절/RQ**: §5.2.5 "물리 색인과 배포 평가 (RQ5)"
- **표의 내용**: 실측 메타데이터 조건(predicate)과 동일 선택도(s)의 무작위 대조 조건 간 Recall@10 짝지은 차이 Δ(=대조군−실측; 실측 조건에서의 재현율 결손 = 무작위 대조 방법론의 과대평가량)를 5개 조건 적용 방식 × 2개 코퍼스(시내도로 n=29쌍, 교차로 n=25쌍)에서 비교. 사전등록 M9 설계.

## 2. 수치 ↔ 원천 매핑

원고 표기 행 이름 ↔ 원천 method 명 대응: 전역 HNSW 검색 후 적용=`postfilter_hnsw_K4x`, IVF 탐색 중 적용(nprobe=8/32)=`single_stage_ivf_batch_np8`/`np32`, 조건별 부분집합 HNSW=`prefilter_hnsw_ef64`, 조건별 부분집합 Flat=`prefilter_flat`. 시내도로=코퍼스 A, 교차로=코퍼스 B.

| 원고 수치 (267–273행) | 원천 파일(data/ 사본) | 파일 내 위치 |
|---|---|---|
| 시내도로 n=29쌍 | `data/B1_m9_control_A.csv` | `n_pairs` 컬럼(전 행 29); 원시 검증: `data/filtered_ann_real_A.csv`의 natural+composite predicate 고유 수=29 |
| 교차로 n=25쌍 | `data/B1_m9_control_B.csv` | `n_pairs` 컬럼(전 행 25); 원시 검증: `data/filtered_ann_real_B.csv`의 natural+composite predicate 고유 수=25 |
| +0.611 [0.554, 0.661] | `data/B1_m9_control_A.csv` | 4행 `postfilter_hnsw_K4x`, `ctrl_minus_real`=0.611, `ci` |
| +0.289 [0.219, 0.359] | `data/B1_m9_control_B.csv` | 4행 `postfilter_hnsw_K4x`, `ctrl_minus_real`=0.289, `ci` |
| +0.627 [0.550, 0.699] | `data/B1_m9_control_A.csv` | 5행 `single_stage_ivf_batch_np8`, `ctrl_minus_real`=0.6269, `ci` |
| +0.217 [0.144, 0.294] | `data/B1_m9_control_B.csv` | 5행 `single_stage_ivf_batch_np8`, `ctrl_minus_real`=0.2173, `ci` |
| +0.498 [0.407, 0.585] | `data/B1_m9_control_A.csv` | 6행 `single_stage_ivf_batch_np32`, `ctrl_minus_real`=0.4976, `ci` |
| +0.116 [0.072, 0.159] | `data/B1_m9_control_B.csv` | 6행 `single_stage_ivf_batch_np32`, `ctrl_minus_real`=0.1155, `ci` |
| +0.017 [0.012, 0.023] | `data/B1_m9_control_A.csv` | 3행 `prefilter_hnsw_ef64`, `ctrl_minus_real`=0.017, `ci` |
| +0.004 [0.002, 0.006] | `data/B1_m9_control_B.csv` | 3행 `prefilter_hnsw_ef64`, `ctrl_minus_real`=**0.0035**, `ci` (원고는 소수 3자리 반올림 0.0035→0.004; 원시 정밀값 +0.00352이므로 3자리 반올림 표기로 정당) |
| Δ=0 (검정 불능), 시내도로 | `data/B1_m9_control_A.csv` | 2행 `prefilter_flat`, `ctrl_minus_real`=0.0, `sig`="(Δ≡0, no test)" |
| Δ=0 (검정 불능), 교차로 | `data/B1_m9_control_B.csv` | 2행 `prefilter_flat`, `ctrl_minus_real`=0.0, `sig`="(Δ≡0, no test)" |
| 행 라벨 "nprobe=8", "nprobe=32" | `data/B1_m9_control_{A,B}.csv` | method 명 `..._np8` / `..._np32` 접미사와 일치 |
| 행 라벨 "상위 40개" | `data/filtered_ann_real_{A,B}.csv` | **불일치** — `kprime` 컬럼 참조. §7 참고 |

동일 수치의 2차 원천(사람이 읽는 요약): `data/B1_analysis_A.md` §"M9"(18–23행), `data/B1_analysis_B.md` §"M9"(18–23행), `data/620_RESULTS_filtered_ann_real_predicates_20260710.md`의 M9 표(18–24행).

## 3. 사용 데이터셋

- **코퍼스 A(시내도로, sinnaedoro)**: 실측 CCTV 프레임 132,521개 × 512차원 CLIP 임베딩. 원본 가공 산출물(캐노니컬):
  `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/` — `frame_embeddings.npy`(259MB), `frame_index.parquet`(1.5MB, location/date/time 메타데이터), `queries.npy`(2.0MB, 텍스트 질의 1,000개 임베딩), `predicate_inventory.csv`.
- **코퍼스 B(교차로, AI Hub 522 intersection)**: 실측 프레임 143,830개 × 512차원 CLIP 임베딩, 센서 조인 89.96%(미조인 프레임은 facet-NULL로 조건 불통과 처리). 캐노니컬:
  `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip/`(567MB: `frame_embeddings.npy`, `frame_index.parquet`) + `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/visual_sensor_join.parquet`(1MB). 질의는 확증층 이미지 200프레임(held-out, self 제외).
- **전처리 요약**: 각 코퍼스의 프레임을 CLIP 512-d로 임베딩한 뒤, A는 시공간 메타(location/date/hour), B는 센서 메타(time_of_day/signal/density/hour)에서 P1 등록 predicate(자연+복합, A 29개·B 25개)를 도출하고 각 predicate에 동일 선택도의 무작위 마스크 대조군을 짝지었다(M9). GT는 조건 부분집합 내 exact top-10(self 제외).

## 4. 실험 체계

- **러너 스크립트**: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/run_filtered_ann_real_predicate.py` (`--corpus A` / `--corpus B`)
- **분석 스크립트**: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/analyze_filtered_ann_results.py` (M9 표·확증 가족·Holm 보정 산출)
- **모델·임베딩**: CLIP 512차원(코퍼스 임베딩·질의 임베딩 동일 공간). 벡터 색인은 faiss CPU — prefilter_flat / prefilter_hnsw(efSearch=64) / postfilter_hnsw(K'∈{1,2,4}×⌈k/s⌉, 표 7은 K4x) / single-stage IVF(IDSelectorBatch nprobe 8/32, recall<0.9 시 np128 에스컬레이션, s≥0.25에 Bitmap 변형).
- **시드**: NumPy RNG `20260710`(러너·분석 공통). k=10, 지연 측정 단일 스레드·반복 15회(워밍업 5 제외), 방법 순서 predicate 블록별 무작위화.
- **통계**: 짝지은 부호 검정(정규 근사) + predicate 수준 부트스트랩 CI 5,000회, 방법 5개 가족 Holm 보정(표 7의 Δ는 전부 Holm 유의, prefilter_flat은 Δ≡0으로 검정 불능).
- **사전등록/결과 문서**:
  - 사전등록: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/420_METHOD_prereg_pillarBE_design_20260710.md` §1 + Amendments(M1/M2/M4/M5/M9, P1 LOCK)
  - 결과: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/620_RESULTS_filtered_ann_real_predicates_20260710.md` (사본: `data/620_RESULTS_filtered_ann_real_predicates_20260710.md`)

## 5. 재현 방법

**(가) 원천 재실행 경로(수 시간 소요, 임베딩 원본 필요)**

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE
# 1) 두 코퍼스 벤치마크 실행 → paper_assets/20260710_pillarB/filtered_ann_real_{A,B}.csv 생성
python3 scripts/run_filtered_ann_real_predicate.py --corpus A
python3 scripts/run_filtered_ann_real_predicate.py --corpus B
# 2) M9 분석 → B1_m9_control_{A,B}.csv, B1_analysis_{A,B}.md 생성
python3 scripts/analyze_filtered_ann_results.py
# 3) 표 7 = B1_m9_control_{A,B}.csv의 ctrl_minus_real·ci 컬럼을 소수 3자리 반올림해 전재
```

**(나) data/ 사본만으로 재집계하는 최소 경로(수 초 소요)**

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/table7_dir/data
python3 - <<'EOF'
import pandas as pd
for c, name in [('A','시내도로'), ('B','교차로')]:
    df = pd.read_csv(f'filtered_ann_real_{c}.csv')
    real = df[df['kind'].isin(['natural','composite'])]
    ctrl = df[df['kind']=='control'].copy()
    ctrl['base'] = ctrl['predicate'].str.split('|').str[1]
    print(f'== {name} (n={real.predicate.nunique()}쌍)')
    for m in ['postfilter_hnsw_K4x','single_stage_ivf_batch_np8',
              'single_stage_ivf_batch_np32','prefilter_hnsw_ef64','prefilter_flat']:
        r = real[real['method']==m].set_index('predicate')['recall_at_10']
        k = ctrl[ctrl['method']==m].set_index('base')['recall_at_10']
        print(f'  {m:28s} Δ(대조군-실측) = {(k - r).dropna().mean():+.4f}')
EOF
# CI는 B1_m9_control_{A,B}.csv의 ci 컬럼에서 직접 조회(부트스트랩 5,000회, 시드 20260710 산출본)
```

## 6. 포함 파일 목록

원 절대경로 접두어 `paper_assets/…` = `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260710_pillarB/`. 사본명은 모두 원본 파일명 그대로.

| 원 절대경로 → 사본명 | 설명 |
|---|---|
| `paper_assets/…/B1_m9_control_A.csv` → `data/B1_m9_control_A.csv` | **표 7 직접 원천(시내도로)**: 방법별 Δ(ctrl_minus_real)·CI·Holm p |
| `paper_assets/…/B1_m9_control_B.csv` → `data/B1_m9_control_B.csv` | **표 7 직접 원천(교차로)**: 동일 구조 |
| `paper_assets/…/filtered_ann_real_A.csv` → `data/filtered_ann_real_A.csv` | 시내도로 원시 결과: predicate(실측·대조군·복합)×방법별 recall@10/CI/지연/kprime |
| `paper_assets/…/filtered_ann_real_B.csv` → `data/filtered_ann_real_B.csv` | 교차로 원시 결과: 동일 구조 |
| `paper_assets/…/filtered_ann_real_A_manifest.json` → `data/filtered_ann_real_A_manifest.json` | 시내도로 실행 매니페스트(N=132,521, dim=512, k=10, 질의 1,000, efSearch=64, M9 대조군) |
| `paper_assets/…/filtered_ann_real_B_manifest.json` → `data/filtered_ann_real_B_manifest.json` | 교차로 실행 매니페스트(N=143,830, 질의 200 이미지 확증층) |
| `paper_assets/…/B1_analysis_A.md` → `data/B1_analysis_A.md` | 시내도로 분석 요약(M9 표·확증 가족·메커니즘 ρ) |
| `paper_assets/…/B1_analysis_B.md` → `data/B1_analysis_B.md` | 교차로 분석 요약(동일 구조) |
| `paper_assets/…/B1_confirmatory_A.csv` → `data/B1_confirmatory_A.csv` | 시내도로 확증 가족(s-밴드×방법쌍) — 표 7 자체는 아니나 동일 사전등록 가족의 맥락 |
| `paper_assets/…/B1_confirmatory_B.csv` → `data/B1_confirmatory_B.csv` | 교차로 확증 가족(동일 구조) |
| `paper_assets/…/P1_predicates_A.csv` → `data/P1_predicates_A.csv` | 시내도로 P1 LOCK predicate 목록(29개: 이름·종류·건수·선택도) |
| `paper_assets/…/P1_predicates_B.csv` → `data/P1_predicates_B.csv` | 교차로 P1 LOCK predicate 목록(25개) |
| `paper_assets/…/P1_manifest.json` → `data/P1_manifest.json` | P1 등록 매니페스트(2026-07-10 LOCK, s-범위) |
| `project_md/620_RESULTS_filtered_ann_real_predicates_20260710.md` → `data/620_RESULTS_filtered_ann_real_predicates_20260710.md` | Pillar B-1 결과 정본 문서(M9 헤드라인 표 = 표 7 원형) |

**복사하지 않은 대용량/임베딩 파일(경로 참조만)**:

- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/frame_embeddings.npy` (259MB, 임베딩 덤프)
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/frame_index.parquet` (1.5MB, parquet)
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/queries.npy` (2.0MB, 질의 임베딩)
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/predicate_inventory.csv` (4KB, 데이터셋 측 인벤토리)
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip/` (567MB, 임베딩 덤프+인덱스 parquet)
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/visual_sensor_join.parquet` (1MB, parquet 조인 테이블)

## 7. 검증

2026-07-23, data/ 사본에서 실제 재조회·재계산(§5-나 코드 + `ci` 문자열 직접 대조, 반올림은 round-half-up 소수 3자리). 원시 `filtered_ann_real_{A,B}.csv`에서 실측(natural+composite)−대조군(CTRL) 쌍별 recall@10 차이 평균을 독립 재계산한 값과, 요약 `B1_m9_control_{A,B}.csv`의 수록값, 원고 인쇄값 3자를 대조했다.

| 원고 수치 | 사본 재조회/재계산 값 | 판정 |
|---|---|---|
| 시내도로 n=29쌍 | 원시 CSV 실측 predicate 29개, 대조군 29개 (1:1 짝) | PASS |
| 교차로 n=25쌍 | 원시 CSV 실측 predicate 25개, 대조군 25개 | PASS |
| 전역 HNSW 검색 후 적용, 시내도로 +0.611 [0.554, 0.661] | 원시 재계산 +0.61100 / m9 CSV 0.611 [0.554,0.661] | PASS |
| 전역 HNSW 검색 후 적용, 교차로 +0.289 [0.219, 0.359] | 원시 재계산 +0.28896 / m9 CSV 0.289 [0.219,0.359] | PASS |
| IVF nprobe=8, 시내도로 +0.627 [0.550, 0.699] | 원시 재계산 +0.62686 / m9 CSV 0.6269 [0.550,0.699] | PASS |
| IVF nprobe=8, 교차로 +0.217 [0.144, 0.294] | 원시 재계산 +0.21732 / m9 CSV 0.2173 [0.144,0.294] | PASS |
| IVF nprobe=32, 시내도로 +0.498 [0.407, 0.585] | 원시 재계산 +0.49762 / m9 CSV 0.4976 [0.407,0.585] | PASS |
| IVF nprobe=32, 교차로 +0.116 [0.072, 0.159] | 원시 재계산 +0.11552 / m9 CSV 0.1155 [0.072,0.159] | PASS |
| 부분집합 HNSW, 시내도로 +0.017 [0.012, 0.023] | 원시 재계산 +0.01702 / m9 CSV 0.017 [0.012,0.023] | PASS |
| 부분집합 HNSW, 교차로 +0.004 [0.002, 0.006] | 원시 재계산 +0.00352 / m9 CSV 0.0035 [0.002,0.006] — 3자리 반올림 0.00352→0.004 | PASS |
| 부분집합 Flat, 시내도로 Δ=0 (검정 불능) | 원시 재계산 +0.00000 / m9 CSV "(Δ≡0, no test)" | PASS |
| 부분집합 Flat, 교차로 Δ=0 (검정 불능) | 원시 재계산 +0.00000 / m9 CSV "(Δ≡0, no test)" | PASS |

**종합: 12/12 수치 PASS.** CI는 부트스트랩 저장본(`B1_m9_control_*.csv`)과 문자열 완전 일치이며, 독립 시드의 재부트스트랩(5,000회)으로도 전 구간 ±0.003 이내에서 재현됨을 확인했다.

**불일치(수치 아님, 행 라벨) — MISMATCH**: 원고 269행의 행 라벨 "전역 HNSW **상위 40개** 검색 후 적용"은 원천과 불일치한다. 해당 방법 `postfilter_hnsw_K4x`의 후보 인출 폭 K'는 고정 40(=4×k)이 아니라 **선택도 적응형 K'=4×⌈k/s⌉**로, 사본 `filtered_ann_real_A.csv`의 `kprime` 컬럼 실측치는 52–612, `filtered_ann_real_B.csv`는 64–352 범위다(값 40은 어느 predicate에도 없음). Δ 수치 자체는 위와 같이 전부 원천과 일치하므로, 라벨 문구만 "전역 HNSW 상위 K'=4×⌈k/s⌉개 검색 후 적용" 등으로 수정하면 된다.
