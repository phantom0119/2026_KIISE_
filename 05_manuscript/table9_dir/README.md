# 표 9 프로비넌스 패키지 (B-4 제3 엔진 기전 재현)

## 1. 대상

**Caption 원문(현재 원고 기준):**

> **&lt;표 9&gt; 상용 벡터 데이터베이스(Milvus 및 Weaviate)에서의 조건 적용 방식에 따른 재현율 차이 비교**

- 원고: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/_archive_20260819/0_paper_script.md`
- 위치: 표 본체 288–296행, caption 298행, 관련 본문 서술 300행
- 소속: **5.2.5절 "물리 색인과 배포 평가 (RQ5)"**. 표 7(faiss)·표 8(pgvector)에서 확인한 "실측 시공간 조건에 의한 근사 색인 재현율 결손" 기전이 상용 엔진(Milvus v2.6.0 · Weaviate 1.35.3)의 네이티브 필터드 경로에서도 재현되는지의 확증/기술 결과(내부 실험명 B-4).
- 표 9의 Δ 정의: predicate 쌍별 **재현율(무작위 대조) − 재현율(실측 조건)**, recall@10, 동결 GT 기준. "시내도로"=코퍼스 A, "교차로"=코퍼스 B.

## 2. 수치 ↔ 원천 매핑

직접 원천은 `data/B4_results.csv`(분석 정본 스크립트 출력)이며, 행 번호는 헤더 포함 물리 행이다. Δ평균·n쌍은 원시 `data/engine_*.csv`에서 독립 재계산으로 교차 확인했다(§7).

| 원고 수치 (표 9) | 값 | 원천 파일(data/ 사본) | 파일 내 위치 |
|---|---|---|---|
| 행1 Weaviate 탐색 확대×시내도로: n쌍 | 24 | `data/B4_results.csv` | 8행(`w2-sweeping`,A), `n_pairs` |
| 행1: Δ | +0.0098 | `data/B4_results.csv` | 8행 `mean_delta` |
| 행1: 95% CI | [0.0049, 0.0159] | `data/B4_results.csv` | 8행 `ci_lo`,`ci_hi` |
| 행1: "Holm 보정 뒤 유의" | holm_p=7.28e-05 | `data/B4_results.csv` | 8행 `holm_p`,`holm_sig_05`=True |
| 행2 Milvus 그래프×교차로: n쌍 | 18 | `data/B4_results.csv` | 10행(`m1-graph`,B), `n_pairs` |
| 행2: Δ | +0.0028 | `data/B4_results.csv` | 10행 `mean_delta` |
| 행2: 95% CI | [0.0009, 0.0049] | `data/B4_results.csv` | 10행 `ci_lo`,`ci_hi` |
| 행2: "Holm 보정 뒤 유의" | holm_p=0.0224 | `data/B4_results.csv` | 10행 `holm_p`,`holm_sig_05`=True |
| 행3 Milvus 그래프×시내도로: n쌍 | 6 | `data/B4_results.csv` | 2행(`m1-graph`,A), `n_pairs` |
| 행3: Δ | +0.0140 | `data/B4_results.csv` | 2행 `mean_delta` |
| 행3: 95% CI | [0.0079, 0.0220] | `data/B4_results.csv` | 2행 `ci_lo`,`ci_hi` |
| 행3: "방향만 일치" | holm_p=0.0625 | `data/B4_results.csv` | 2행 `holm_p`(비유의; Wilcoxon n=6 입도 한계) |
| 행4 Weaviate 탐색 확대×교차로: n쌍 | 22 | `data/B4_results.csv` | 16행(`w2-sweeping`,B), `n_pairs` |
| 행4: Δ | +0.0006 | `data/B4_results.csv` | 16행 `mean_delta` |
| 행4: 95% CI | [0.0000, 0.0015] | `data/B4_results.csv` | 16행 `ci_lo`,`ci_hi` |
| 행5 Milvus 전수 전환×시내도로: n쌍 | 18 | `data/B4_results.csv` | 3행(`m1-BF`,A), `n_pairs` |
| 행5: Δ | +0.0006 | `data/B4_results.csv` | 3행 `mean_delta` |
| 행5: 95% CI | [0.0004, 0.0008] | `data/B4_results.csv` | 3행 `ci_lo`,`ci_hi` |
| 행6 Milvus 전수 전환×교차로: n쌍 | 4 | `data/B4_results.csv` | 11행(`m1-BF`,B, "n<5 — reported, not tested") |
| 행6: "재현율 ≥0.9986, Δ≤+0.0014" | 관측 상한 | `data/B4_RESULTS.md` 20행(완화 레인) + `data/engine_milvus_B.csv` | m1 natural 쌍 중 filtered-out≥0.93인 4쌍의 `recall_at_10`(양팔) 재계산; §7 참고(실측은 recall 1.0000·Δ 0.0000으로 인쇄 상한보다 강함) |
| 행7 Weaviate ACORN×교차로: n쌍 | 22 | `data/B4_results.csv` | 15행(`w3-acorn-cutoff0`,B), `n_pairs` |
| 행7: Δ | −0.0181 | `data/B4_results.csv` | 15행 `mean_delta` |
| 행7: 95% CI | [−0.046, +0.003] | `data/B4_results.csv` | 15행 `ci_lo`=−0.0459, `ci_hi`=0.0034 (원고는 소수 3자리 반올림) |

| 원고 수치 (본문 300행, 표 9 귀속) | 값 | 원천 파일 | 파일 내 위치 |
|---|---|---|---|
| "Holm 보정 후 유의한 손실은 최대 +0.0098(Weaviate 시내도로)" | +0.0098 | `data/B4_results.csv` | 8행 `mean_delta` (유의 2셀 중 최대: 0.0098 > 0.0028) |
| "Milvus 시내도로에서 더 큰 손실(+0.0140) … 표본이 6쌍" | +0.0140 / 6 | `data/B4_results.csv` | 2행 `mean_delta`,`n_pairs` |
| "필터링되는 비율이 약 92.3% 이상 … 전수 검색으로 전환" | 0.923 | `data/B4_RESULTS.md` 20행 + `data/engine_milvus_A.csv` | knowhere BF 경계 실측 괄호 (0.923, 0.934]: A의 m1 natural 쌍에서 그래프 체제 최대 filtered-out=0.9231, BF 체제 최소=0.9343 |
| "조건을 만족하는 벡터가 40,000개 미만일 때 … 전수 검색" | 40,000 | `data/engine_weaviate_A.csv`, `data/engine_weaviate_B.csv` | w1 행의 `flat_cutoff` 열 = 40000 (Weaviate flatSearchCutoff 서버 기본값) |
| "재현율 결손은 0.0014 이하로 대폭 감축" | 0.0014 | `data/B4_results.csv` 3행(`ci_hi` 상한 0.0008 포함) + `data/engine_milvus_A.csv`·`engine_milvus_B.csv` | BF 체제 A 18쌍·B 4쌍의 쌍별 최대 Δ=0.0014 (A에서 발생; B는 0.0000) |

## 3. 사용 데이터셋

- **코퍼스 A "시내도로"**: AI Hub 시내도로 주행영상 유래 프레임 코퍼스, CLIP 임베딩 132,521×512 + 텍스트 질의 1,000개(자기 제외 없음). 캐노니컬: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/{frame_embeddings.npy, queries.npy, frame_index.parquet}` (대용량, 미복사).
- **코퍼스 B "교차로"**: AI Hub 교차로(522 수집분) 프레임 코퍼스, CLIP 임베딩 143,830×512 + 이미지 질의 200개(`default_rng(20260710)` 첫 choice, 자기 제외; 인덱스는 `data/qidx_B.npy`로 동결·sha256 고정). 캐노니컬: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip/{frame_embeddings.npy, frame_index.parquet}` + `.../20260710/visual_sensor_join.parquet` (대용량, 미복사).
- **가공 산출물(스테이지-1 동결 입력)**: `data/inputs_A.npz`·`data/inputs_B.npz` — P1 잠금 predicate(실측 조건 A 24·B 22 natural + 합성) 및 동일 크기 무작위 대조 마스크(packed bool), 부분집합 내 exact top-10 GT(faiss FlatIP·자기 제외), 질의 행렬, M9 군집 공변량. 전처리는 L2 정규화 후 마스크·GT를 엔진 무관하게 로컬 계산해 동결한 것이 전부이며, 엔진은 검색만 수행한다.

## 4. 실험 체계

**스크립트(실행 순서, 절대경로):**

1. `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/export_engine_bench_inputs.py` — 스테이지 1: 엔진 무관 입력 동결(마스크·GT·질의·공변량 → `inputs_{A,B}.npz/_meta.csv`), P1 양방향 어서션, `--faiss-seed-check`
2. `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/run_engine_filtered_bench.py` — 스테이지 2: Milvus/Weaviate 적재·필터드 검색(`--engine --corpus [--conditions] [--smoke]`), G-ingest·G-filter 게이트, 원시 `engine_*.csv` 산출
3. `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/f7_control_replicates.py` — F7: 대조군 r=7 드로우 시드 민감도(표 9 외 보조 근거)
4. `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/analyze_engine_replication.py` — 스테이지 3: 확증 분석 정본 → `B4_results.csv`·`B4_mechanism.csv`·`B4_f7_seed_sensitivity.csv`

**모델·임베딩:** CLIP 512차원(코퍼스 임베딩은 상류 산출물 재사용, L2 정규화·IP metric). 생성 모델 없음.

**엔진·환경(고정):** Milvus standalone v2.6.0(pymilvus 3.0.0) · Weaviate 1.35.3(weaviate-client 4.22.0), 도커 기동, venv `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/envs/kiise-engines`(numpy 2.5.1). 색인은 faiss B-1 미러링: HNSW M(maxConnections)=32, efConstruction=200, 탐색 ef=64. 컬렉션 `kiise_{a,b}_b4`(Milvus)·`Kiise_{a,b}_b4`(Weaviate) 보존.

**시드·핵심 파라미터:** 대조군 마스크 `default_rng(20260712 + predicate_index)`(B-1의 20260710 스트림과 독립임을 선언); 부트스트랩 B=10,000, RNG seed 20260712; recall@10; Milvus BF 경계 상수 0.93(knowhere kHnswSearchKnnBFFilterThreshold, 실측 괄호 (0.923, 0.934]); Weaviate flatSearchCutoff 기본 40,000; 확증 가족 = {m1-graph, w2-sweeping}×{A,B} 4검정 Holm, 헤드라인은 predicate-부트스트랩 CI와 facet-가족 군집 부트스트랩 CI가 모두 0 배제일 때만.

**사전등록·결과 문서:**
- 프리레지: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/420_METHOD_prereg_pillarBE_design_20260710.md` — **Amendment 5**(147행~) 설계, **Amendment 5a**(167행~) 분석 전 재선언(m1-graph/m1-BF 분리, w1/w2/w3 재정의·w2→w3 재라벨, 확증 4가족, G-filter, 자연 predicate 한정)
- 결과 정본: `data/B4_RESULTS.md`(원본 `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260712_engine_replication/B4_RESULTS.md`)

## 5. 재현 방법

**(a) 원천 재실행(처음부터):**

```bash
# 0) Milvus v2.6.0 standalone + Weaviate 1.35.3 도커 기동, venv 활성화
source /home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/envs/kiise-engines/bin/activate
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts

# 1) 스테이지 1: 입력 동결 (P1 어서션 A29/B25 통과 필수)
python export_engine_bench_inputs.py --corpus A --faiss-seed-check
python export_engine_bench_inputs.py --corpus B --faiss-seed-check

# 2) 스테이지 2: 엔진 벤치 (G-ingest 비필터 recall>=0.95, G-filter 카운트 일치 게이트)
python run_engine_filtered_bench.py --engine milvus   --corpus A
python run_engine_filtered_bench.py --engine milvus   --corpus B
python run_engine_filtered_bench.py --engine weaviate --corpus A   # w1/w3 + w2는 sweeping 조건으로 별도(_w2sweep)
python run_engine_filtered_bench.py --engine weaviate --corpus B

# 3) F7 시드 민감도(보조) 후 스테이지 3: 확증 분석
python f7_control_replicates.py
python analyze_engine_replication.py
# → paper_assets/20260712_engine_replication/B4_results.csv 의 7개 레인
#   (w2-sweeping×A/B, m1-graph×A/B, m1-BF×A/B, w3-acorn-cutoff0×B)을 표 9로 전사
```

**(b) data/ 사본만으로 최소 재집계(엔진·GPU 불필요, pandas만):**

```python
import pandas as pd
D = "data/"  # 이 디렉터리 기준
def paired(df):
    real = df[df.kind != "control"].set_index("pair")
    ctrl = df[df.kind == "control"].set_index("pair")
    c = real.index.intersection(ctrl.index)
    d = pd.DataFrame({"kind": real.loc[c, "kind"].values,
                      "s": real.loc[c, "selectivity"].values,
                      "delta": ctrl.loc[c, "recall_at_10"].values - real.loc[c, "recall_at_10"].values,
                      "r_real": real.loc[c, "recall_at_10"].values,
                      "r_ctrl": ctrl.loc[c, "recall_at_10"].values})
    return d[d.kind == "natural"]

mA = paired(pd.read_csv(D+"engine_milvus_A.csv").query("condition=='m1'"))
mB = paired(pd.read_csv(D+"engine_milvus_B.csv").query("condition=='m1'"))
print("행1", paired(pd.read_csv(D+"engine_weaviate_A_w2sweep.csv").query("condition=='w2'")).delta.mean())  # +0.0098, n=24
print("행2", mB[(1-mB.s) < 0.93].delta.mean())   # +0.0028, n=18
print("행3", mA[(1-mA.s) < 0.93].delta.mean())   # +0.0140, n=6
print("행4", paired(pd.read_csv(D+"engine_weaviate_B.csv").query("condition=='w2'")).delta.mean())  # +0.0006, n=22
print("행5", mA[(1-mA.s) >= 0.93].delta.mean())  # +0.0006, n=18
b6 = mB[(1-mB.s) >= 0.93]                        # 행6: n=4, 양팔 recall min, Δ max
print("행6", len(b6), b6[["r_real","r_ctrl"]].min().min(), b6.delta.abs().max())
print("행7", paired(pd.read_csv(D+"engine_weaviate_B.csv").query("condition=='w3'")).delta.mean())  # -0.0181, n=22
```

부트스트랩 CI·Holm p까지 재현하려면 (a)의 `analyze_engine_replication.py`를 실행한다(모듈 전역 RNG(seed 20260712)를 레인 순서대로 소비하므로 CI 비트 동일 재현은 전체 스크립트 실행이 전제). 표 9 인쇄 CI는 `data/B4_results.csv` 셀과 자릿수 반올림만 다르다(행7 참조).

## 6. 포함 파일 목록

원 절대경로 접두는 `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/`이며, `20260712_engine_replication/` 전체(25개)와 `20260710_pillarB/`의 P1 잠금 3개를 원 파일명 그대로 복사했다.

| 원 절대경로(접두 생략) → 사본명 | 설명 |
|---|---|
| `20260712_engine_replication/B4_RESULTS.md` → `data/B4_RESULTS.md` | 결과 정본 요약(캐노니컬; 표 9 서사·완화 레인·경계 실측) |
| `20260712_engine_replication/B4_results.csv` → `data/B4_results.csv` | 확증+기술 전 레인 통계 — **표 9 직접 원천** |
| `20260712_engine_replication/B4_mechanism.csv` → `data/B4_mechanism.csv` | Δ↔GT-군집심도 Spearman(secondary) |
| `20260712_engine_replication/B4_f7_seed_sensitivity.csv` → `data/B4_f7_seed_sensitivity.csv` | M9 대조군 시드 민감도 요약(F7) |
| `20260712_engine_replication/engine_milvus_A.csv` → `data/engine_milvus_A.csv` | Milvus m1 원시(코퍼스 A, predicate×real/control recall·지연) — 행3·행5·경계 실측 원천 |
| `20260712_engine_replication/engine_milvus_A_manifest.json` → 동명 | Milvus A 적재·색인·게이트 기록(비필터 recall 0.997) |
| `20260712_engine_replication/engine_milvus_B.csv` → `data/engine_milvus_B.csv` | Milvus m1 원시(코퍼스 B) — 행2·행6 원천 |
| `20260712_engine_replication/engine_milvus_B_manifest.json` → 동명 | Milvus B 매니페스트(비필터 recall 1.0) |
| `20260712_engine_replication/engine_weaviate_A.csv` → `data/engine_weaviate_A.csv` | Weaviate A 원시 w1/w3(수집 당시 'w2' 행은 5a(2)에 따라 w3 재라벨) |
| `20260712_engine_replication/engine_weaviate_A_manifest.json` → 동명 | Weaviate A 매니페스트(비필터 recall 0.996) |
| `20260712_engine_replication/engine_weaviate_A_relabel_note.json` → 동명 | w2→w3 재라벨 이력(변경 기록) |
| `20260712_engine_replication/engine_weaviate_A_w2sweep.csv` → 동명 | 진짜 w2(sweeping+cutoff0) A 원시 — **행1 원천** |
| `20260712_engine_replication/engine_weaviate_A_w2sweep_manifest.json` → 동명 | w2 스윕 매니페스트 |
| `20260712_engine_replication/engine_weaviate_B.csv` → `data/engine_weaviate_B.csv` | Weaviate B 원시 w1/w2/w3 — 행4·행7 원천 |
| `20260712_engine_replication/engine_weaviate_B_manifest.json` → 동명 | Weaviate B 매니페스트 |
| `20260712_engine_replication/f7_replicates_A.csv` → 동명 | F7 대조군 r-드로우 원시(A) |
| `20260712_engine_replication/f7_replicates_B.csv` → 동명 | F7 대조군 r-드로우 원시(B) |
| `20260712_engine_replication/faiss_seedcheck_A.csv` → 동명 | faiss 신규-시드 재채점(A, M9 스팟체크) |
| `20260712_engine_replication/faiss_seedcheck_B.csv` → 동명 | faiss 신규-시드 재채점(B) |
| `20260712_engine_replication/inputs_A.npz` → 동명 | 동결 입력 A: 마스크 58·GT·질의 1,000×512·공변량 (3.4MB) |
| `20260712_engine_replication/inputs_A_meta.csv` → 동명 | A 마스크 메타(predicate·kind·selectivity·군집 공변량) |
| `20260712_engine_replication/inputs_B.npz` → 동명 | 동결 입력 B: 마스크 50·GT·질의 200×512·공변량 (1.0MB) |
| `20260712_engine_replication/inputs_B_meta.csv` → 동명 | B 마스크 메타 |
| `20260712_engine_replication/qidx_B.npy` → 동명 | B 질의 인덱스 200개(sha256 8635a761… 고정) |
| `20260712_engine_replication/retro_gates_report.json` → 동명 | 소급 게이트: qidx sha 재도출 일치, P1 양방향 A29/B25, G-filter 108/108 |
| `20260710_pillarB/P1_predicates_A.csv` → `data/P1_predicates_A.csv` | P1 predicate 잠금 테이블 A(상류 사본; 스테이지-1 어서션 대상) |
| `20260710_pillarB/P1_predicates_B.csv` → `data/P1_predicates_B.csv` | P1 predicate 잠금 테이블 B |
| `20260710_pillarB/P1_manifest.json` → `data/P1_manifest.json` | P1 잠금 매니페스트 |

**복사하지 않은 대용량/외부 원천(경로만):**

- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/frame_embeddings.npy`, `queries.npy`, `frame_index.parquet` — 코퍼스 A 임베딩·질의·메타(임베딩 덤프)
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip/frame_embeddings.npy`, `frame_index.parquet` 및 `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/visual_sensor_join.parquet` — 코퍼스 B 임베딩·조인 테이블
- `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260710_pillarB/filtered_ann_real_A.csv`, `filtered_ann_real_B.csv` — F7 레인이 참조하는 B-1 원 시드 faiss 결과(표 9 본체와 무관, 보조)
- 엔진 컬렉션 `kiise_{a,b}_b4`(Milvus)·`Kiise_{a,b}_b4`(Weaviate) — 도커 볼륨 내 보존(재실행 시 G-ingest 재통과 필수)

## 7. 검증

검증 방법: `data/` 사본만 읽어 (i) `B4_results.csv` 셀 직접 대조, (ii) 원시 `engine_*.csv`에서 분석 스크립트와 동일한 페어링·레인 분리 로직으로 Δ평균·n쌍 **독립 재계산**, (iii) 행6·경계·cutoff는 원시 값에서 직접 재계산. 총 **42개 체크 42 PASS** (2026-07-23 실행).

| 원고 수치 | data/ 사본 실측 | 판정 |
|---|---|---|
| 행1: 24쌍, +0.0098 [0.0049, 0.0159], Holm 유의 | n=24, 0.0098 [0.0049, 0.0159], holm_p=7.3e-05<0.05; 원시 재계산 Δ=0.0098/n=24 일치 | **PASS** |
| 행2: 18쌍, +0.0028 [0.0009, 0.0049], Holm 유의 | n=18, 0.0028 [0.0009, 0.0049], holm_p=0.0224<0.05; 원시 재계산 일치 | **PASS** |
| 행3: 6쌍, +0.0140 [0.0079, 0.0220], 방향만 일치 | n=6, 0.0140 [0.0079, 0.0220], holm_p=0.0625(비유의); 원시 재계산 일치 | **PASS** |
| 행4: 22쌍, +0.0006 [0.0000, 0.0015], 방향만 일치 | n=22, 0.0006 [0.0, 0.0015], holm_p=0.121(비유의); 원시 재계산 일치 | **PASS** |
| 행5: 18쌍, +0.0006 [0.0004, 0.0008] | n=18, 0.0006 [0.0004, 0.0008]; 원시 재계산 일치 | **PASS** |
| 행6: 4쌍, 재현율 ≥0.9986, Δ≤+0.0014 | 원시 B BF 4쌍: 양팔 min recall=1.0000(≥0.9986 충족), max Δ=0.0000(≤0.0014 충족) | **PASS** |
| 행7: 22쌍, −0.0181 [−0.046, +0.003] | n=22, −0.0181, CI [−0.0459, +0.0034] → 3자리 반올림 [−0.046, +0.003] 일치; 원시 재계산 일치 | **PASS** |
| 본문: "유의 손실 최대 +0.0098(Weaviate 시내도로)" | 유의 2셀 = 0.0098(w2×A) > 0.0028(m1-graph×B), 최대 일치 | **PASS** |
| 본문: "+0.0140 … 표본이 6쌍이라 방향 일치로만 보고" | 2행 mean_delta=0.014, n_pairs=6, holm 비유의 | **PASS** |
| 본문: "약 92.3% 이상 … 전수 검색 전환" | 원시 A m1 natural: 그래프 체제 최대 filtered-out=0.9231, BF 체제 최소=0.9343 → 경계 괄호 (0.923, 0.934], 하한 92.3% 일치 | **PASS** |
| 본문: "40,000개 미만일 때 … 전수 검색" | `engine_weaviate_{A,B}.csv` w1 행 `flat_cutoff`=40000 단일값 | **PASS** |
| 본문: "재현율 결손은 0.0014 이하" | BF 체제 쌍별 max Δ: A 18쌍=0.0014, B 4쌍=0.0000 → 전체 ≤0.0014 일치 | **PASS** |

**정직 유의사항 (불일치 아님):**

1. **행6의 인쇄 문구는 보수적 상한이다.** "재현율 ≥0.9986, Δ≤+0.0014"의 binding 값(0.9986/0.0014)은 A 18쌍(행5 레인)에서 관측된 것이고, 행6의 B 4쌍 자체는 recall 1.0000·Δ 0.0000이다. 원고 문구는 `B4_RESULTS.md` 20행의 A·B 통합 완화 레인 서술("A 18쌍·B 4쌍 양팔 recall≥0.9986, Δ≤0.0014")을 따른 것으로, B 4쌍에 대해 참이지만 더 강한 값이 성립한다.
2. **부트스트랩 CI는 정본 CSV 셀 대조로 검증했다.** Δ평균·n쌍·행6·경계·cutoff는 원시 파일에서 독립 재계산까지 일치시켰으나, CI 수치의 비트 동일 재계산은 `analyze_engine_replication.py`의 전역 RNG 소비 순서 재현이 필요해 수행하지 않았다(§5(b) 참고). 정본 CSV와 원고 인쇄값은 전 셀 일치(행7만 자릿수 반올림).
3. 표 9의 판정 열("Holm 보정 뒤 유의" 등)은 정본의 `holm_sig_05`·note와 1:1 대응하며 UNVERIFIED 항목은 없다.
