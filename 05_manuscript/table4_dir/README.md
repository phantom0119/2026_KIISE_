# 표 4 관리 디렉터리 (provenance package)

작성일: 2026-07-23. 이 디렉터리는 원고 표 4를 재구축·검증하는 데 필요한 캐노니컬 원천 사본과 재현 절차를 자체 완결적으로 담는다.

## 1. 대상

- **Caption 원문** (원고 기준, `manuscript/_archive_20260819/0_paper_script.md` 214행):
  **&lt;표 4&gt; 검색용 데이터별 품질·지연·저장량 비교 (벡터 단독 검색, Flat, 질의 85개)**
- **표 본문 위치**: `0_paper_script.md` 206–212행(표), 214행(캡션). 표를 직접 인용·해석하는 본문은 200행, 217–219행.
- **소속**: 5.2.2절 "검색용 데이터 구성 평가 (RQ2)". 다섯 가지 검색용 데이터 구성(영상 설명문 / 대표 이미지 / 이미지·설명문 결합 / 다중 이미지 / 이중 색인)을 벡터 단독 검색(B2)·Flat 전수 검색으로 통제한 채 비교한다.
- 그림 2(b)의 비순환 기준선 0.1810(원고 196행)도 본 패키지의 caption 행과 동일한 앵커(같은 코퍼스·임베딩)를 공유한다.

## 2. 수치 ↔ 원천 매핑

원천 파일은 모두 이 디렉터리의 `data/` 사본 경로다. `configuration_summary.csv`의 행 키는 `{표현}__B2_vector__flat`이며, strict/semantic 두 행이 지연·저장량 컬럼을 공유한다.

### 2.1 표 4 본체 (206–212행)

| 원고 값 | 의미 | 원천 파일 | 파일 내 위치 (행번호 / 컬럼) | 원천 원값 |
|---:|---|---|---|---:|
| 0.063 | 영상 설명문 strict nDCG@10 | data/configuration_summary.csv | L2 (`caption__B2_vector__flat`, scoring=strict) / `ndcg_at_10` | 0.06264 |
| 0.181 | 영상 설명문 semantic nDCG@10 | data/configuration_summary.csv | L3 (동일 키, scoring=semantic) / `ndcg_at_10` | 0.18100 |
| 1.15 | 영상 설명문 p50 (ms) | data/configuration_summary.csv | L2–L3 / `latency_p50_ms` | 1.15482 |
| 24.6 | 영상 설명문 저장량 (MB) | data/configuration_summary.csv | L2–L3 / `vector_payload_mb` | 24.576 |
| 0.063 | 대표 이미지 strict | data/configuration_summary.csv | L10 (`representative_frame__…`, strict) / `ndcg_at_10` | 0.06252 |
| 0.186 | 대표 이미지 semantic | data/configuration_summary.csv | L11 / `ndcg_at_10` | 0.18649 |
| +0.005 [−0.075, +0.079] | 대표 이미지 Δ [군집 95% CI] | data/paired_bootstrap_comparisons.csv | L3 (family=storage, semantic, candidate=representative_frame) / `mean_delta`, `cluster_ci_lo`, `cluster_ci_hi` | 0.00549 [−0.07507, +0.07916] |
| 1.21 | 대표 이미지 p50 | data/configuration_summary.csv | L10–L11 / `latency_p50_ms` | 1.20699 |
| 24.6 | 대표 이미지 저장량 | data/configuration_summary.csv | L10–L11 / `vector_payload_mb` | 24.576 |
| 0.079 | 이미지·설명문 결합 strict | data/configuration_summary.csv | L16 (`joint_image_caption__…`, strict) / `ndcg_at_10` | 0.07943 |
| 0.218 | 이미지·설명문 결합 semantic | data/configuration_summary.csv | L17 / `ndcg_at_10` | 0.21816 |
| +0.037 [−0.005, +0.074] | 결합 Δ [군집 CI] | data/paired_bootstrap_comparisons.csv | L5 (storage, semantic, joint_image_caption) / 동일 3개 컬럼 | 0.03716 [−0.00486, +0.07419] |
| 1.24 | 결합 p50 | data/configuration_summary.csv | L16–L17 / `latency_p50_ms` | 1.24292 |
| 24.6 | 결합 저장량 | data/configuration_summary.csv | L16–L17 / `vector_payload_mb` | 24.576 |
| 0.101 | 다중 이미지 strict | data/configuration_summary.csv | L22 (`multi_frame__…`, strict) / `ndcg_at_10` | 0.10137 |
| 0.352 | 다중 이미지 semantic | data/configuration_summary.csv | L23 / `ndcg_at_10` | 0.35179 |
| +0.171 [+0.018, +0.316] | 다중 이미지 Δ [군집 CI] | data/paired_bootstrap_comparisons.csv | L7 (storage, semantic, multi_frame) / 동일 3개 컬럼 | 0.17078 [+0.01779, +0.31618] |
| 3.65 | 다중 이미지 p50 | data/configuration_summary.csv | L22–L23 / `latency_p50_ms` | 3.65144 |
| 68.4 | 다중 이미지 저장량 | data/configuration_summary.csv | L22–L23 / `vector_payload_mb` | 68.39501 |
| 0.089 | 이중 색인 strict | data/configuration_summary.csv | L28 (`dual__…`, strict) / `ndcg_at_10` | 0.08888 |
| 0.293 | 이중 색인 semantic | data/configuration_summary.csv | L29 / `ndcg_at_10` | 0.29327 |
| +0.112 [−0.004, +0.228] | 이중 색인 Δ [군집 CI] | data/paired_bootstrap_comparisons.csv | L9 (storage, semantic, dual) / 동일 3개 컬럼 | 0.11226 [−0.00391, +0.22756] |
| 4.96 | 이중 색인 p50 | data/configuration_summary.csv | L28–L29 / `latency_p50_ms` | 4.95901 |
| 93.0 | 이중 색인 저장량 | data/configuration_summary.csv | L28–L29 / `vector_payload_mb` | 92.97101 |
| 85 | 질의 수 (캡션 표기) | data/configuration_summary.csv, data/manifest.json | 모든 행 `queries` 컬럼 / manifest `queries` 키 | 85 |

### 2.2 표 4를 인용하는 본문 수치 (218–219행)

| 원고 값 | 의미 | 원천 파일 | 파일 내 위치 | 원천 원값 |
|---:|---|---|---|---:|
| p=0.028 | 다중 이미지 군집 부트스트랩 양측 p | data/paired_bootstrap_comparisons.csv | L7 / `p_cluster` | 0.0284 |
| p&lt;0.0001 | 다중 이미지 질의 수준 p | data/paired_bootstrap_comparisons.csv | L7 / `p_query` (10,000회 재표집에서 0회) | 0.0 |
| q=0.112 | 다중 이미지 BH 보정 q값 | data/paired_bootstrap_comparisons.csv | L7 / `q_cluster_bh` | 0.11227 |
| 저장 방식 4개 비교 (BH 가족 크기) | 원고 219행·171행 | data/paired_bootstrap_comparisons.csv | family=storage & scoring=semantic 행 수 (L3, L5, L7, L9) | 4 |
| 약 2.8배 | 저장량 증가 배수 (파생) | data/configuration_summary.csv | 68.39501 / 24.576 | 2.783 |
| 3배 이상 | p50 증가 배수 (파생) | data/configuration_summary.csv | 3.65144 / 1.15482 | 3.162 |
| k=60 | 이중 색인 RRF 상수 (설정값) | data/RESULTS_KO.md, 원고 163행 | 프로토콜 설정(산출물 아님) | 60 |

## 3. 사용 데이터셋

- **원본 데이터셋**: AI Hub "지능형 교통 관제(교차로)" 522 도메인 CCTV 클립 3,000개. 비순환(3원천 분리) 워크로드로 질의 85개, 엄격한 정답 6,809행, 의미론적 정답 24,872행 고정 (data/manifest.json의 `clips`/`queries`/`qrels_*` 및 SHA-256 해시 참조).
- **캐노니컬 가공 산출물** (대용량, 경로 참조만):
  - 코퍼스·질의·정답 고정본: `/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/qwen35_9b/522/canonical`
  - 단일모달 임베딩(캡션·프레임·다중 프레임): `/hdd2/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_unified_qwen35captions`
  - joint image+caption 임베딩: `/hdd2/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_joint_image_caption_qwen35captions`
- **전처리 요약**: 클립별 중간 프레임에서 Qwen3.5-9B로 최대 110토큰 탐욕적 디코딩 설명문을 사전 생성하고, 설명문·이미지(및 둘의 early-fusion 결합)를 Qwen3-VL-Embedding-2B(2,048차원, L2 정규화)로 인코딩하였다. 다중 이미지는 클립당 최대 3벡터(총 8,349개), 이중 색인은 설명문 lane + 다중 이미지 lane을 RRF(k=60)로 늦은 결합한다.

## 4. 실험 체계

- **사용 스크립트** (절대경로):
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_qwen3_joint_image_caption_assets.py` — joint image+caption 벡터 생성(치환 음성 대조 포함)
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/run_joint_storage_search_index.py` — 저장×검색 계획×색인 호환 그리드 실행 → `configuration_summary.csv`, `per_query_metrics.parquet`, `latency_trials.parquet` 등 산출
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/analyze_joint_optimization_validation.py` — 대응 부트스트랩·BH 보정·파레토 분석 → `paired_bootstrap_comparisons.csv`, `analysis_manifest.json`
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/verify_joint_optimization_independently.py` — 17개 검사 독립 재계산 → `joint_image_caption_independent_verification.json`
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/verify_paper_script_numbers.py` — 원고 수치 상시 가드. §3 블록(71행 부근 "Table 4 five storage configs vs canonical CSV")이 표 4의 5개 구성 strict/semantic/p50/MB를 캐노니컬 CSV와 대조한다.
- **모델·임베딩**: 설명문 생성 Qwen3.5-9B(110토큰 상한, 탐욕적 디코딩), 임베딩 Qwen3-VL-Embedding-2B 2,048차원(BF16, FlashAttention2, `max_pixels=534600`, instruction "Represent the user's input."), L2 정규화.
- **시드·핵심 파라미터**: seed=20260717, 부트스트랩 10,000회(질의 85개 재표집 + intent×facet 25군집 재표집), BH 보정은 family×scoring 단위(storage 가족 4개 비교), Flat 전수 검색, CPU 단일 스레드, 준비 2회·반복 10회, postfilter 후보 200(표 4는 B2 벡터 단독만 사용), max_rank=100.
- **사전등록/결과 문서**:
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/820_JOINT_IMAGE_CAPTION_SINGLE_VECTOR_PROTOCOL_20260717.md` — 결과 산출 전 고정 프로토콜(비교군·estimand·SESOI·BH 규칙)
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/821_RESULTS_joint_image_caption_single_vector_20260717.md` — 실행 결과 요약(무결성 검사 17개 통과 포함)

## 5. 재현 방법

### (A) 원천 재실행 경로 (처음부터)

```bash
ROOT=/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE
# 1) joint image+caption 벡터 생성 (GPU, /hdd2 임베딩 루트 필요; matched + shuffled)
python3 $ROOT/scripts/build_qwen3_joint_image_caption_assets.py            # --resume 지원
# 2) 저장×검색×색인 호환 그리드 실행 (출력 디렉터리를 표 4 캐노니컬 경로로 지정)
python3 $ROOT/scripts/run_joint_storage_search_index.py \
    --output-dir $ROOT/paper_assets/20260717_joint_image_caption_validation --overwrite
# 3) 부트스트랩·BH·파레토 분석
python3 $ROOT/scripts/analyze_joint_optimization_validation.py \
    --root $ROOT/paper_assets/20260717_joint_image_caption_validation
# 4) 독립 검증 + 원고 수치 가드
python3 $ROOT/scripts/verify_joint_optimization_independently.py
python3 $ROOT/scripts/verify_paper_script_numbers.py                       # §3 = 표 4 가드
```

주의: `run_joint_storage_search_index.py`의 기본 출력 경로 상수는 `20260717_joint_optimization_validation`이므로, 캐노니컬 경로 재현 시 위와 같이 `--output-dir`를 명시해야 한다.

### (B) data/ 사본만으로 재집계하는 최소 경로

```bash
# 표 4의 38개 수치(표 본체 + 관련 본문 p/q/배수) 전체 PASS/FAIL 대조
python3 /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/table4_dir/verify_table4.py
```

또는 수동 재조회: `data/configuration_summary.csv`에서 `config`가 `{caption,representative_frame,joint_image_caption,multi_frame,dual}__B2_vector__flat`인 행의 `ndcg_at_10`(scoring별), `latency_p50_ms`, `vector_payload_mb`를 반올림하고, `data/paired_bootstrap_comparisons.csv`에서 `family=storage, scoring=semantic` 4개 행의 `mean_delta`, `cluster_ci_lo/hi`, `p_cluster`, `p_query`, `q_cluster_bh`를 대조한다. 점 추정 평균의 독립 재계산은 `data/per_query_metrics.parquet`(질의×구성 nDCG), p50 재계산은 `data/latency_trials.parquet`(95,200회 시행 원자료 중 해당 구성), 순위 원자료는 `data/rankings.parquet`로 가능하다.

## 6. 포함 파일 목록

원 절대경로 접두: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260717_joint_image_caption_validation/` (모든 사본은 원 파일명 유지)

| 원 파일 → 사본 (data/) | 설명 |
|---|---|
| configuration_summary.csv | 구성×정답기준별 nDCG/MRR/Recall/지연/저장량 요약. 표 4 점 추정·p50·MB의 직접 원천 |
| paired_bootstrap_comparisons.csv | 대응 부트스트랩 Δ·질의/군집 CI·p·BH q. 표 4 Δ 열과 본문 p=0.028, q=0.112의 직접 원천 |
| latency_summary.csv | 구성별 지연 분포 요약(p50/p95/p99) |
| quality_summary.csv | 구성별 품질 지표 상세 |
| configuration_costs.csv | 구성별 저장·색인 비용 상세 |
| query_clusters.csv | 질의 85개 → 25개 intent×facet 군집 매핑(군집 부트스트랩 정의) |
| same_encoder_storage_control.csv | 동일 인코더 저장 방식 통제 비교 보조표 |
| per_query_metrics.parquet | 질의×구성 수준 지표 원자료(점 추정 독립 재계산용, 83KB) |
| latency_trials.parquet | 지연 반복 측정 원자료(p50 독립 재계산용, 1.1MB) |
| rankings.parquet | 검색 순위 원자료(nDCG 원천 재계산용, 1.3MB) |
| manifest.json | 실험 매니페스트: 시드·코퍼스 규모·색인 파라미터·입력 해시·주의사항 |
| analysis_manifest.json | 분석 매니페스트: 부트스트랩 10,000회·25군집·BH 규칙·입력 해시 |
| RESULTS_KO.md | 실행 당시 한국어 결과 요약 |
| JOINT_IMAGE_CAPTION_VERIFICATION_KO.md | 독립 검증 한국어 요약 |
| joint_image_caption_independent_verification.json | 독립 검증기 17개 검사 결과 |

디렉터리 최상위: `verify_table4.py` — 본 패키지 §7 검증 스크립트(사본 기준 재조회).

**복사하지 않은 대용량/외부 파일 (경로 참조만)**:

- `/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/qwen35_9b/522/canonical` — 코퍼스·질의·정답 고정본
- `/hdd2/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_unified_qwen35captions` — 단일모달 임베딩 덤프
- `/hdd2/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_joint_image_caption_qwen35captions` — joint 임베딩 덤프

## 7. 검증

검증 방법: `verify_table4.py`가 **data/ 사본**을 직접 읽어 원고(2026-07-23 판, 206–219행) 수치와 대조. 반올림 규약은 nDCG·Δ·CI 소수 3자리, p50 소수 2자리, MB 소수 1자리. 실행 결과 **38/38 PASS, FAIL/UNVERIFIED 없음**.

| 검증 항목 | 원고 값 | 사본 원값 | 판정 |
|---|---:|---:|---|
| 영상 설명문 strict / semantic / p50 / MB | 0.063 / 0.181 / 1.15 / 24.6 | 0.06264 / 0.18100 / 1.15482 / 24.576 | PASS |
| 대표 이미지 strict / semantic / p50 / MB | 0.063 / 0.186 / 1.21 / 24.6 | 0.06252 / 0.18649 / 1.20699 / 24.576 | PASS |
| 대표 이미지 Δ [군집 CI] | +0.005 [−0.075, +0.079] | 0.00549 [−0.07507, +0.07916] | PASS |
| 이미지·설명문 결합 strict / semantic / p50 / MB | 0.079 / 0.218 / 1.24 / 24.6 | 0.07943 / 0.21816 / 1.24292 / 24.576 | PASS |
| 결합 Δ [군집 CI] | +0.037 [−0.005, +0.074] | 0.03716 [−0.00486, +0.07419] | PASS |
| 다중 이미지 strict / semantic / p50 / MB | 0.101 / 0.352 / 3.65 / 68.4 | 0.10137 / 0.35179 / 3.65144 / 68.39501 | PASS |
| 다중 이미지 Δ [군집 CI] | +0.171 [+0.018, +0.316] | 0.17078 [+0.01779, +0.31618] | PASS |
| 이중 색인 strict / semantic / p50 / MB | 0.089 / 0.293 / 4.96 / 93.0 | 0.08888 / 0.29327 / 4.95901 / 92.97101 | PASS |
| 이중 색인 Δ [군집 CI] | +0.112 [−0.004, +0.228] | 0.11226 [−0.00391, +0.22756] | PASS |
| 본문: 다중 이미지 군집 p=0.028 | 0.028 | 0.0284 | PASS |
| 본문: 다중 이미지 질의 p&lt;0.0001 | &lt;0.0001 | 0.0 (10,000회 중 0회) | PASS |
| 본문: BH q=0.112 | 0.112 | 0.11227 | PASS |
| 본문: BH 가족 = 저장 방식 4개 비교 | 4 | storage×semantic 4행 | PASS |
| 본문: 저장량 "약 2.8배" | 2.8 | 2.783 | PASS |
| 본문: p50 "3배 이상" | ≥3 | 3.162 | PASS |
| 캡션: 질의 85개 | 85 | 85 (`queries` 컬럼·manifest) | PASS |

비고: 상기 기록 외에 표 4가 인쇄하는 수치는 없다. 기존 상시 가드(`scripts/verify_paper_script_numbers.py` §3)도 같은 5개 구성을 동일 캐노니컬 CSV 원본과 대조하므로 이중 안전망이 유지된다.
