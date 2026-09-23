# 표 3 관리 디렉터리 (table3_dir)

## 1. 대상

- **캡션 원문(현재 원고 기준)**: `**<표 3> 정답 정보 재사용 제거 전후 작업 부하의 진단적 검색 품질 비교 (nDCG@10)**`
- **원고 내 위치**: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/0_main_paper.md` 5.2.1절
- **소속 절 / RQ**: 5.2.1절 "비순환 평가 작업 부하 검증 결과 (RQ1)". 정답 정보 재사용 제거 전후에 작업 부하도 함께 변경된 두 데이터셋을 진단적으로 비교한다. 두 데이터셋 모두 검색 전 조건 적용·벡터 단독 검색·BM25 어휘 검색의 동일한 세 검색 방식을 제시한다.
- **표 원문(163–169행)**:

| 데이터셋·검색 방식 | 제거 전 기존 정답 | 제거 후 엄격한 정답 | 제거 후 의미론적 정답 |
|---|---:|---:|---:|
| VRU-Accident / 검색 전 조건 적용 | 0.9736 | 0.3174 | 0.2974 |
| VRU-Accident / 벡터 단독 검색 | 0.4476 | 0.1845 | 0.2649 |
| VRU-Accident / BM25 어휘 검색 | 0.4495 | 0.0918 | 0.1607 |
| 지능형 관제 CCTV / 검색 전 조건 적용 | 1.0000 | 0.8395 | 0.8395 |
| 지능형 관제 CCTV / 벡터 단독 검색 | 0.7014 | 0.6285 | 0.8203 |
| 지능형 관제 CCTV / BM25 어휘 검색 | 0.9600 | 0.1111 | 0.1667 |

전략 명칭 매핑: 검색 전 조건 적용 = `B4_prefilter_vector`, 벡터 단독 검색 = `B2_vector_only`, BM25 어휘 검색 = `B1_bm25_only`.

## 2. 수치 ↔ 원천 매핑

표 3의 18개 수치 셀. 1차 원천은 실행 산출물이며, VRU-Accident 3개 행은 `vru_collapse_table.csv`에도 동일 값이 요약되어 있다.

| 값 | 원천 파일(data/ 사본) | 파일 내 위치 |
|---|---|---|
| 0.9736 (VRU B4 수정 전) | `data/vru_bgem3_faiss_b0_b5/metrics_summary.csv` | `strategy=B4_prefilter_vector, difficulty=all` 행, `ndcg_at_10` 열 (0.973607) / 요약: `data/20260710_noncircular_collapse/vru_collapse_table.csv` 6행 `v1_circular_ndcg10` |
| 0.3174 (VRU B4 strict) | `data/vru2_bgem3_b0_b5/metrics_summary.csv` | `B4_prefilter_vector, all` 행, `ndcg_at_10` (0.317351) / 요약: `vru_collapse_table.csv` 6행 `v2_strict_ndcg10` |
| 0.2974 (VRU B4 semantic) | `data/vru2_bgem3_b0_b5/metrics_semantic.csv` | `strategy=B4_prefilter_vector` 85개 질의 행의 `ndcg_at_10` 평균 (0.297354) / 요약: `vru_collapse_table.csv` 6행 `v2_semantic_ndcg10` |
| 0.4476 (VRU B2 수정 전) | `data/vru_bgem3_faiss_b0_b5/metrics_summary.csv` | `B2_vector_only, all` 행, `ndcg_at_10` (0.447586) / 요약: `vru_collapse_table.csv` 4행 |
| 0.1845 (VRU B2 strict) | `data/vru2_bgem3_b0_b5/metrics_summary.csv` | `B2_vector_only, all` 행, `ndcg_at_10` (0.184474) |
| 0.2649 (VRU B2 semantic) | `data/vru2_bgem3_b0_b5/metrics_semantic.csv` | `B2_vector_only` 85개 질의 평균 (0.264894) |
| 0.4495 (VRU B1 수정 전) | `data/vru_bgem3_faiss_b0_b5/metrics_summary.csv` | `B1_bm25_only, all` 행, `ndcg_at_10` (0.449470) / 요약: `vru_collapse_table.csv` 3행 |
| 0.0918 (VRU B1 strict) | `data/vru2_bgem3_b0_b5/metrics_summary.csv` | `B1_bm25_only, all` 행, `ndcg_at_10` (0.091848) |
| 0.1607 (VRU B1 semantic) | `data/vru2_bgem3_b0_b5/metrics_semantic.csv` | `B1_bm25_only` 85개 질의 평균 (0.160748) |
| 0.9600 (CCTV B1 수정 전) | `data/aihub_bgem3_faiss_b0_b5/metrics_summary.csv` | `B1_bm25_only, all` 행, `ndcg_at_10` (0.959984) |
| 0.1111 (CCTV B1 strict) | `data/acctv2_bgem3_b0_b5/metrics_summary.csv` | `B1_bm25_only, all` 행, `ndcg_at_10` (0.111111) |
| 0.1667 (CCTV B1 semantic) | `data/acctv2_bgem3_b0_b5/metrics_semantic.csv` | `B1_bm25_only` 18개 질의 평균 (0.166667) |
| 1.0000 (CCTV B4 수정 전) | `data/aihub_bgem3_faiss_b0_b5/metrics_summary.csv` | `B4_prefilter_vector, all` 행, `ndcg_at_10` (1.0) |
| 0.8395 (CCTV B4 strict) | `data/acctv2_bgem3_b0_b5/metrics_summary.csv` | `B4_prefilter_vector, all` 행, `ndcg_at_10` (0.839489) |
| 0.8395 (CCTV B4 semantic) | `data/acctv2_bgem3_b0_b5/metrics_semantic.csv` | `B4_prefilter_vector` 18개 질의 평균 (0.839489) |
| 0.7014 (CCTV B2 제거 전) | `data/aihub_bgem3_faiss_b0_b5/metrics_summary.csv` | `B2_vector_only, all` 행, `ndcg_at_10` (0.701405) |
| 0.6285 (CCTV B2 strict) | `data/acctv2_bgem3_b0_b5/metrics_summary.csv` | `B2_vector_only, all` 행, `ndcg_at_10` (0.628516) |
| 0.8203 (CCTV B2 semantic) | `data/acctv2_bgem3_b0_b5/metrics_semantic.csv` | `B2_vector_only` 18개 질의 평균 (0.820273) |

해설 문단(원고 173행)의 워크로드 규모 수치:

| 값 | 원천 파일(data/ 사본) | 파일 내 위치 |
|---|---|---|
| VRU 수정 전 질의 244개 | `data/vru_bgem3_faiss_b0_b5/run_manifest.json` | `counts.queries` = 244 |
| VRU 수정 전 문서 7,000개 | `data/vru_bgem3_faiss_b0_b5/run_manifest.json` | `counts.documents` = 7000 |
| VRU 수정 후 질의 85개 | `data/vru2_bgem3_b0_b5/run_manifest.json` | `counts.queries` = 85 (질의 정의: `data/canonical_v2_vru/queries.jsonl` 85행) |
| VRU 수정 후 문서 1,000개 | `data/vru2_bgem3_b0_b5/run_manifest.json` | `counts.documents` = 1000 |
| CCTV 수정 전 질의 133개 | `data/aihub_bgem3_faiss_b0_b5/run_manifest.json` | `counts.queries` = 133 |
| CCTV 수정 전 문서 807개 | `data/aihub_bgem3_faiss_b0_b5/run_manifest.json` | `counts.documents` = 807 |
| CCTV 수정 후 질의 18개 | `data/acctv2_bgem3_b0_b5/run_manifest.json` | `counts.queries` = 18 (질의 정의: `data/canonical_v2_acctv/queries.jsonl` 18행) |
| CCTV 수정 후 문서 269개 | `data/acctv2_bgem3_b0_b5/run_manifest.json` | `counts.documents` = 269 |

## 3. 사용 데이터셋

- **VRU-Accident** (외부 VQA 데이터셋): 원본 `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/raw/VRU-Accident/` (약 3.0GB, 영상+VQA 라벨).
  - v1 순환판(수정 전): `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/vru_accident/20260706/canonical/` — 질의 244개·문서 7,000개(클립 1,000개, facet-statement 문서 포함, 질의·필터·정답이 같은 VQA 라벨에서 유래 → 순환).
  - v2 비순환판(수정 후): `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/vru_accident/20260710_noncircular/canonical/` — 질의 85개·문서 1,000개(캡션-only 코퍼스, relevance=사고유형 의미축, filter=독립 운영 facet[weather/road/location]). 정답 유래 템플릿 문서를 제거하고 문서·조건·정답의 필드 축을 분리하는 전처리를 거쳤다.
- **AI Hub 지능형 관제 CCTV**: 원본 `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/raw/aihub_intelligent_cctv/` (약 13GB).
  - v1 순환판: `.../Datasets/processed/aihub_intelligent_cctv/20260706/canonical/` — 질의 133개·문서 807개(클립 269개, 라벨 재진술 문서 포함).
  - v2 비순환판: `.../Datasets/processed/aihub_intelligent_cctv/20260710_noncircular/canonical/` — 질의 18개·문서 269개(클립당 캡션 1건). v1 raw 쌍(clip_pairs.csv)을 읽되 라벨 재진술을 제거하고 세 채널(문서/조건/정답)을 필드 수준에서 분리했으며, 비순환성은 `A9_noncircular_audit.json` 감사로 확인한다(사본: `data/canonical_v2_vru/`, `data/canonical_v2_acctv/`).
- 주의: 정답 정보 재사용을 제거한 두 작업 부하도 여전히 같은 주석 계보(VRU=동일 VQA 주석, CCTV=동일 JSON 주석)에 의존하므로, AI Hub 교차로의 세 원천 분리와 동등하지 않다.

## 4. 실험 체계

- **사용 스크립트** (절대경로, 모두 존재 확인):
  - v2 캐노니컬 구축: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_vru_noncircular_canonical.py`, `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_aihub_cctv_noncircular_canonical.py` (CCTV 빌더는 v1 raw 버전 `20260706`의 clip_pairs.csv를 입력으로 새 캐노니컬 버전 기록)
  - v1 캐노니컬 구축: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_vru_canonical.py`, `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_aihub_cctv_canonical.py`
  - 임베딩: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_text_embeddings.py`
  - 검색 실행: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/run_retrieval_baselines.py`
  - 수치 검증(기존): `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/verify_manuscript_numbers.py` (T1 블록이 이 표를 검증)
- **모델·임베딩**: BGE-M3 (`model_path=/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/models/huggingface/BAAI--bge-m3`), 1,024차원, `normalize_embeddings=true`; v2 실행 device=cuda:1/batch 32, v1 실행 device=cuda/batch 16 (각 `run_manifest.json`의 `embedding_manifest`에 기록).
- **검색 백엔드·파라미터**: `vector_backend=faiss.IndexFlatIP`(Flat 전수), `bm25_backend=rank_bm25.BM25Okapi`, `top_ks=[1,5,10,20]`, `max_rank=100`, `postfilter_doc_k=200`, B3/B4/B5는 외부 메타데이터 필터. 전략 B0–B5 중 표 3은 B1/B2/B4만 인쇄.
- **시드**: 이 표의 산출 경로는 결정적(Flat 전수 검색+BM25, 템플릿 질의 생성)이어서 run_manifest에 별도 난수 시드가 기록되어 있지 않다. (원고 125행의 시드 20260710은 AI Hub 교차로 3,000클립 표집용이며 이 표와 무관.)
- **실행 시각**: v1 VRU 2026-07-06T08:08Z, v1 CCTV 2026-07-06T08:52Z, v2 VRU 2026-07-09T19:24Z, v2 CCTV 2026-07-09T19:32Z (각 run_manifest.json `created_at`).
- **관련 결과/사전등록 문서** (project_md):
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/canonical/experiments/EXP01_CIRCULARITY_AND_WORKLOAD_VALIDITY.md` — RQ1 실험 정본. §7.1에 기존 5개 행, §8에 허용·금지 주장을 기록한다. 추가한 CCTV 벡터 단독 검색 행은 실행 산출물에서 재집계했다. (사본: `data/project_md/`)
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/500_DATASETS_construction_noncircular_execution_20260710.md` — 정답 정보 재사용 제거 작업 부하의 실행 기록. (사본: `data/project_md/`)

## 5. 재현 방법

**(A) 원천 재실행 경로 (처음부터)**

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety
S=2026_KIISE/scripts
# 1) v2 비순환 캐노니컬 구축 (v1 raw/캐노니컬이 이미 있다는 전제)
python3 $S/build_vru_noncircular_canonical.py            # -> Datasets/processed/vru_accident/20260710_noncircular/canonical
python3 $S/build_aihub_cctv_noncircular_canonical.py     # -> Datasets/processed/aihub_intelligent_cctv/20260710_noncircular/canonical
# 2) BGE-M3 임베딩 (v1·v2 각각)
python3 $S/build_text_embeddings.py  # canonical_root/모델 인자는 스크립트 인자 참조 (bge-m3)
# 3) B0–B5 베이스라인 실행 (v1·v2 각각) -> metrics_summary.csv(strict), retrieval_results.parquet
python3 $S/run_retrieval_baselines.py  # canonical/embedding/output 인자 지정
# 4) semantic 평가: 저장 랭킹(retrieval_results.parquet) + qrels_semantic.tsv 후처리 -> metrics_semantic.csv
#    (vru_collapse_table.md 재현 절차 참조; MEVA용 동일 패턴 스크립트 $S/score_meva_semantic.py)
# 5) 대조표 집계 -> paper_assets/20260710_noncircular_collapse/vru_collapse_table.csv
# 6) 검증: python3 $S/verify_manuscript_numbers.py (T1 블록)
```

**(B) data/ 사본만으로 재집계하는 최소 경로**

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/table3_dir
python3 - <<'EOF'
import csv
from collections import defaultdict
def strict(p):   # difficulty=all 행의 ndcg_at_10
    return {r['strategy']: float(r['ndcg_at_10'])
            for r in csv.DictReader(open(p)) if r['difficulty'] == 'all'}
def sem(p):      # 질의별 ndcg_at_10 매크로 평균
    a = defaultdict(list)
    for r in csv.DictReader(open(p)): a[r['strategy']].append(float(r['ndcg_at_10']))
    return {s: sum(v)/len(v) for s, v in a.items()}
v1v, v1c = strict('data/vru_bgem3_faiss_b0_b5/metrics_summary.csv'), strict('data/aihub_bgem3_faiss_b0_b5/metrics_summary.csv')
v2v, v2c = strict('data/vru2_bgem3_b0_b5/metrics_summary.csv'),    strict('data/acctv2_bgem3_b0_b5/metrics_summary.csv')
sv,  sc  = sem('data/vru2_bgem3_b0_b5/metrics_semantic.csv'),      sem('data/acctv2_bgem3_b0_b5/metrics_semantic.csv')
for name, s, a, b, c in [('VRU/검색전조건','B4_prefilter_vector',v1v,v2v,sv), ('VRU/벡터단독','B2_vector_only',v1v,v2v,sv),
                         ('VRU/BM25','B1_bm25_only',v1v,v2v,sv), ('CCTV/검색전조건','B4_prefilter_vector',v1c,v2c,sc),
                         ('CCTV/벡터단독','B2_vector_only',v1c,v2c,sc), ('CCTV/BM25','B1_bm25_only',v1c,v2c,sc)]:
    print(f"{name}: {a[s]:.4f}  {b[s]:.4f}  {c[s]:.4f}")
EOF
# 출력 6행이 원고 표 3의 18개 수치 셀과 일치해야 한다.
```

## 6. 포함 파일 목록

원 절대경로 접두어 `B=/home/explorer/vectorDB/experiments/db/KIISE_datasociety`, `P=$B/Datasets/processed`. 사본은 원 파일명을 유지하고 하위 디렉터리로 충돌을 구분한다.

| 원 절대경로 | 사본 | 설명 |
|---|---|---|
| `$B/2026_KIISE/paper_assets/20260710_noncircular_collapse/vru_collapse_table.csv` | `data/20260710_noncircular_collapse/vru_collapse_table.csv` | VRU v1↔v2 대조 집계표(표 3 VRU 3행의 9개 셀 원천 요약) |
| `.../vru_collapse_table.md` | `data/20260710_noncircular_collapse/vru_collapse_table.md` | 위 표의 주석판(재현 절차·결합도 V 포함) |
| `.../significance_v2_b4_vs_b2.csv` | `data/20260710_noncircular_collapse/significance_v2_b4_vs_b2.csv` | v2 B4−B2 유의성(VRU 85질의, CCTV 18질의) — 표 3 보조 근거 |
| `.../significance_522_trisource.csv` | `data/20260710_noncircular_collapse/significance_522_trisource.csv` | (문맥용) 522 3원천 32질의 B4−B2 유의성 — 표 3 수치 아님 |
| `.../trisource_522_final.md` | `data/20260710_noncircular_collapse/trisource_522_final.md` | (문맥용) 522 3원천 최종 결과 — 표 3 수치 아님 |
| `.../trisource_522_final_metrics.csv` | `data/20260710_noncircular_collapse/trisource_522_final_metrics.csv` | (문맥용) 위 metrics | 
| `$P/vru_accident/20260710_noncircular/results/vru2_bgem3_b0_b5/metrics_summary.csv` | `data/vru2_bgem3_b0_b5/metrics_summary.csv` | VRU v2 strict nDCG@10 (difficulty=all 행이 표 값) |
| `.../vru2_bgem3_b0_b5/metrics_semantic.csv` | `data/vru2_bgem3_b0_b5/metrics_semantic.csv` | VRU v2 semantic 질의별 지표(85질의×6전략) |
| `.../vru2_bgem3_b0_b5/latency_summary.csv` | `data/vru2_bgem3_b0_b5/latency_summary.csv` | VRU v2 지연(참고) |
| `.../vru2_bgem3_b0_b5/run_manifest.json` | `data/vru2_bgem3_b0_b5/run_manifest.json` | VRU v2 실행 명세(백엔드·파라미터·counts) |
| `.../vru2_bgem3_b0_b5/summary.md` | `data/vru2_bgem3_b0_b5/summary.md` | VRU v2 요약 |
| `$P/aihub_intelligent_cctv/20260710_noncircular/results/acctv2_bgem3_b0_b5/metrics_summary.csv` | `data/acctv2_bgem3_b0_b5/metrics_summary.csv` | CCTV v2 strict nDCG@10 |
| `.../acctv2_bgem3_b0_b5/metrics_semantic.csv` | `data/acctv2_bgem3_b0_b5/metrics_semantic.csv` | CCTV v2 semantic 질의별 지표(18질의×6전략) |
| `.../acctv2_bgem3_b0_b5/latency_summary.csv` | `data/acctv2_bgem3_b0_b5/latency_summary.csv` | CCTV v2 지연(참고) |
| `.../acctv2_bgem3_b0_b5/run_manifest.json` | `data/acctv2_bgem3_b0_b5/run_manifest.json` | CCTV v2 실행 명세 |
| `.../acctv2_bgem3_b0_b5/summary.md` | `data/acctv2_bgem3_b0_b5/summary.md` | CCTV v2 요약 |
| `$P/vru_accident/20260706/results/vru_bgem3_faiss_b0_b5/metrics_summary.csv` | `data/vru_bgem3_faiss_b0_b5/metrics_summary.csv` | VRU v1(수정 전) nDCG@10 |
| `.../vru_bgem3_faiss_b0_b5/latency_summary.csv` | `data/vru_bgem3_faiss_b0_b5/latency_summary.csv` | VRU v1 지연(참고) |
| `.../vru_bgem3_faiss_b0_b5/run_manifest.json` | `data/vru_bgem3_faiss_b0_b5/run_manifest.json` | VRU v1 실행 명세(질의 244·문서 7,000) |
| `.../vru_bgem3_faiss_b0_b5/summary.md` | `data/vru_bgem3_faiss_b0_b5/summary.md` | VRU v1 요약 |
| `$P/aihub_intelligent_cctv/20260706/results/aihub_bgem3_faiss_b0_b5/metrics_summary.csv` | `data/aihub_bgem3_faiss_b0_b5/metrics_summary.csv` | CCTV v1(수정 전) nDCG@10 |
| `.../aihub_bgem3_faiss_b0_b5/latency_summary.csv` | `data/aihub_bgem3_faiss_b0_b5/latency_summary.csv` | CCTV v1 지연(참고) |
| `.../aihub_bgem3_faiss_b0_b5/run_manifest.json` | `data/aihub_bgem3_faiss_b0_b5/run_manifest.json` | CCTV v1 실행 명세(질의 133·문서 807) |
| `.../aihub_bgem3_faiss_b0_b5/summary.md` | `data/aihub_bgem3_faiss_b0_b5/summary.md` | CCTV v1 요약 |
| `$P/vru_accident/20260710_noncircular/canonical/A9_noncircular_audit.json` | `data/canonical_v2_vru/A9_noncircular_audit.json` | VRU v2 비순환 감사 결과 |
| `.../20260710_noncircular/canonical/queries.jsonl` | `data/canonical_v2_vru/queries.jsonl` | VRU v2 질의 85개 정의 |
| `.../20260710_noncircular/canonical/qrels.tsv` | `data/canonical_v2_vru/qrels.tsv` | VRU v2 엄격한 정답 |
| `.../20260710_noncircular/canonical/qrels_semantic.tsv` | `data/canonical_v2_vru/qrels_semantic.tsv` | VRU v2 의미론적 정답 |
| `$P/aihub_intelligent_cctv/20260710_noncircular/canonical/A9_noncircular_audit.json` | `data/canonical_v2_acctv/A9_noncircular_audit.json` | CCTV v2 비순환 감사 결과 |
| `.../20260710_noncircular/canonical/queries.jsonl` | `data/canonical_v2_acctv/queries.jsonl` | CCTV v2 질의 18개 정의 |
| `.../20260710_noncircular/canonical/qrels.tsv` | `data/canonical_v2_acctv/qrels.tsv` | CCTV v2 엄격한 정답 |
| `.../20260710_noncircular/canonical/qrels_semantic.tsv` | `data/canonical_v2_acctv/qrels_semantic.tsv` | CCTV v2 의미론적 정답 |
| `$P/vru_accident/20260706/canonical/dataset_manifest.json` | `data/canonical_v1_vru/dataset_manifest.json` | VRU v1 캐노니컬 명세 |
| `$P/vru_accident/20260706/canonical/summary.md` | `data/canonical_v1_vru/summary.md` | VRU v1 캐노니컬 요약 |
| `$P/vru_accident/20260706/canonical/queries.jsonl` | `data/canonical_v1_vru/queries.jsonl` | VRU v1 질의 244개 정의 |
| `$P/aihub_intelligent_cctv/20260706/canonical/dataset_manifest.json` | `data/canonical_v1_acctv/dataset_manifest.json` | CCTV v1 캐노니컬 명세 |
| `$P/aihub_intelligent_cctv/20260706/canonical/summary.md` | `data/canonical_v1_acctv/summary.md` | CCTV v1 캐노니컬 요약 |
| `$P/aihub_intelligent_cctv/20260706/canonical/queries.jsonl` | `data/canonical_v1_acctv/queries.jsonl` | CCTV v1 질의 133개 정의 |
| `$B/2026_KIISE/project_md/canonical/experiments/EXP01_CIRCULARITY_AND_WORKLOAD_VALIDITY.md` | `data/project_md/EXP01_CIRCULARITY_AND_WORKLOAD_VALIDITY.md` | RQ1 실험 정본의 기존 5개 행과 해석 범위 |
| `$B/2026_KIISE/project_md/500_DATASETS_construction_noncircular_execution_20260710.md` | `data/project_md/500_DATASETS_construction_noncircular_execution_20260710.md` | 정답 정보 재사용 제거 작업 부하의 실행 기록 |

**복사하지 않은 대용량/이진 파일 (경로 참조만)**:

- 질의별 원시 랭킹: `$P/vru_accident/20260710_noncircular/results/vru2_bgem3_b0_b5/retrieval_results.parquet`, `metrics_by_query.parquet` (CCTV v2·v1 두 run 디렉터리에도 동일 파일명 존재) — semantic 재계산의 원시 입력이지만 parquet이므로 미복사
- 캐노니컬 코퍼스 parquet: `$P/{vru_accident,aihub_intelligent_cctv}/{20260706,20260710_noncircular}/canonical/{clips,documents,metadata}.parquet`
- 임베딩: `$P/{vru_accident,aihub_intelligent_cctv}/{20260706,20260710_noncircular}/embeddings/bge-m3/{document_embeddings.npy,query_embeddings.npy,...}`
- 원본 데이터: `$B/Datasets/raw/VRU-Accident/` (약 3.0GB), `$B/Datasets/raw/aihub_intelligent_cctv/` (약 13GB)
- 임베딩 모델: `$B/Datasets/models/huggingface/BAAI--bge-m3/`

## 7. 검증

검증 방법: 이 디렉터리의 data/ 사본만 읽어 원고 값과 대조했다. VRU-Accident 3개 행은 집계표와 실행 산출물로 이중 검증하고, 지능형 관제 CCTV 3개 행은 실행 산출물에서 재집계했다. 새로 추가한 벡터 단독 검색 3개 값을 포함한 18개 수치 셀이 모두 소수 넷째 자리에서 일치한다.

| 검증 항목 | 원고 값 | 사본 재조회 값 | 판정 |
|---|---:|---:|---|
| VRU/검색전조건 수정 전 — collapse.csv | 0.9736 | 0.9736 | PASS |
| VRU/검색전조건 strict — collapse.csv | 0.3174 | 0.3174 | PASS |
| VRU/검색전조건 semantic — collapse.csv | 0.2974 | 0.2974 | PASS |
| VRU/벡터단독 수정 전 — collapse.csv | 0.4476 | 0.4476 | PASS |
| VRU/벡터단독 strict — collapse.csv | 0.1845 | 0.1845 | PASS |
| VRU/벡터단독 semantic — collapse.csv | 0.2649 | 0.2649 | PASS |
| VRU/BM25 수정 전 — collapse.csv | 0.4495 | 0.4495 | PASS |
| VRU/BM25 strict — collapse.csv | 0.0918 | 0.0918 | PASS |
| VRU/BM25 semantic — collapse.csv | 0.1607 | 0.1607 | PASS |
| VRU/검색전조건 수정 전 — v1 run 재조회 | 0.9736 | 0.973607 | PASS |
| VRU/벡터단독 수정 전 — v1 run 재조회 | 0.4476 | 0.447586 | PASS |
| VRU/BM25 수정 전 — v1 run 재조회 | 0.4495 | 0.449470 | PASS |
| CCTV/BM25 수정 전 — v1 run 재조회 | 0.9600 | 0.959984 | PASS |
| CCTV/검색전조건 수정 전 — v1 run 재조회 | 1.0000 | 1.000000 | PASS |
| CCTV/벡터단독 제거 전 — v1 run 재조회 | 0.7014 | 0.701405 | PASS |
| VRU/검색전조건 strict — v2 run 재조회 | 0.3174 | 0.317351 | PASS |
| VRU/벡터단독 strict — v2 run 재조회 | 0.1845 | 0.184474 | PASS |
| VRU/BM25 strict — v2 run 재조회 | 0.0918 | 0.091848 | PASS |
| CCTV/BM25 strict — v2 run 재조회 | 0.1111 | 0.111111 | PASS |
| CCTV/검색전조건 strict — v2 run 재조회 | 0.8395 | 0.839489 | PASS |
| CCTV/벡터단독 strict — v2 run 재조회 | 0.6285 | 0.628516 | PASS |
| VRU/검색전조건 semantic — 85질의 평균 재계산 | 0.2974 | 0.297354 | PASS |
| VRU/벡터단독 semantic — 85질의 평균 재계산 | 0.2649 | 0.264894 | PASS |
| VRU/BM25 semantic — 85질의 평균 재계산 | 0.1607 | 0.160748 | PASS |
| CCTV/BM25 semantic — 18질의 평균 재계산 | 0.1667 | 0.166667 | PASS |
| CCTV/검색전조건 semantic — 18질의 평균 재계산 | 0.8395 | 0.839489 | PASS |
| CCTV/벡터단독 semantic — 18질의 평균 재계산 | 0.8203 | 0.820273 | PASS |
| VRU 수정 전 질의 244 — run_manifest | 244 | 244 | PASS |
| VRU 수정 전 문서 7,000 — run_manifest | 7000 | 7000 | PASS |
| CCTV 수정 전 질의 133 — run_manifest | 133 | 133 | PASS |
| CCTV 수정 전 문서 807 — run_manifest | 807 | 807 | PASS |
| VRU 수정 후 질의 85 — run_manifest | 85 | 85 | PASS |
| VRU 수정 후 문서 1,000 — run_manifest | 1000 | 1000 | PASS |
| CCTV 수정 후 질의 18 — run_manifest | 18 | 18 | PASS |
| CCTV 수정 후 문서 269 — run_manifest | 269 | 269 | PASS |
| VRU semantic 질의 수 85 — metrics_semantic 행 수 | 85 | 85 | PASS |
| CCTV semantic 질의 수 18 — metrics_semantic 행 수 | 18 | 18 | PASS |

미해결 사항(수치 불일치 아님): v2의 `metrics_semantic.csv`를 생성한 일회성 후처리 스크립트(저장 랭킹+qrels_semantic.tsv 재채점)가 `2026_KIISE/scripts/`에 별도 파일로 남아 있지 않다(동일 패턴의 MEVA용 `score_meva_semantic.py`만 존재). 산출물 자체는 위와 같이 표 값과 정확히 일치한다.
