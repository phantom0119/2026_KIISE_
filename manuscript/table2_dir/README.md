# 표 2 관리 디렉터리 — 공통 실행 환경과 변인 통제 명세

## 1. 대상

- **Caption 원문(현재 원고 기준)**: `**<표 2> 공통 실행 환경과 변인 통제 명세**`
- **원고 내 위치**: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/_archive_20260819/0_paper_script.md`
  - 도입 문단: 148행("표 2는 본 연구의 공통 실행 환경과 측정 명세를 요약한다. …")
  - 표 본문: 150–157행(헤더 2행 + 데이터 6행: 장비 / 소프트웨어 / 영상 설명문 생성 / 임베딩 / Faiss 통제 / pgvector 통제)
  - 캡션: 159행
- **소속 절/RQ**: 5.1.1절 뒤의 **5.1.2. 실행 환경**. 특정 RQ의 결과 표가 아니라 **모든 RQ(RQ1–RQ6)에 공통 적용되는 환경·통제 명세**이다. 표 안에서 RQ별 배정이 명시된 항목은 다음과 같다.
  - 영상 설명문 생성: Qwen2.5-VL-7B-Instruct(RQ3·RQ4, 생성 모델 비교 기준선), Qwen3.5-9B(RQ1 통제 주입·RQ2 표 4)
  - Faiss 통제: RQ2 준비 2회·반복 10회, RQ5 준비 실행 제외·반복 15회
  - pgvector 통제: 질의 300개(RQ5 시내도로 W2 R5 벤치마크)

## 2. 수치 ↔ 원천 매핑

표 2는 결과 수치가 아닌 **사양·설정 값**으로 구성된다. 원고에 인쇄된 모든 값을 아래에 매핑한다. 파일 경로는 이 디렉터리의 `data/` 사본 기준이다.

| 원고 값 | 원천 파일(data/ 사본) | 파일 내 위치(키/컬럼) |
|---|---|---|
| Intel i7-9700K | `data/verification_suite_20260711/environment_manifest.json` | `cpu` = "Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz" |
| 메모리 62GB | 같은 파일 | `ram` = "62GB" |
| RTX 3090 24GB 2대 | 같은 파일 | `gpu` = 2줄, 각 "NVIDIA GeForce RTX 3090, 24576 MiB" |
| Linux 5.15 | 같은 파일 | `os` = "Linux 5.15.0-139-generic" |
| Python 3.10.20 | 같은 파일 | `python` = "3.10.20" |
| Faiss 1.14.3 | 같은 파일 | `faiss` = "1.14.3" |
| PostgreSQL 16.14 | 같은 파일 | `postgres` = "16.14 (Debian 16.14-1.pgdg12+1)" |
| pgvector 0.8.4 | 같은 파일 | `pgvector` = "0.8.4" |
| Milvus 2.6.0 | `data/20260712_engine_replication/engine_milvus_A_manifest.json` | `version` = "server 2.6.0 / pymilvus 3.0.0" |
| Weaviate 1.35.3 | `data/20260712_engine_replication/engine_weaviate_A_manifest.json` | `version` = "server 1.35.3 / weaviate-client 4.22.0" |
| 중간 이미지 | (data/ 사본에 직접 기록 없음 — §7 참조) | 스크립트 근거: `scripts/build_intersection_captions.py` 69행 `middle_frame()` / 18행 주석 |
| 최대 110토큰 | `data/captions_qwen25vl_7b/caption_manifest_shard0.json`, `data/captions_qwen35_9b/caption_manifest_shard0of1.json`, `data/20260723_controlled_supplement/protocol_manifest.json` | `max_new_tokens` = 110 (세 파일 모두; supplement는 `e0.max_new_tokens`) |
| 탐욕적 디코딩 | 같은 세 파일 | `decoding` = "greedy" |
| Qwen2.5-VL-7B-Instruct | `data/captions_qwen25vl_7b/caption_manifest_shard0.json` | `snapshot` 경로에 "models--Qwen--Qwen2.5-VL-7B-Instruct" |
| Qwen3.5-9B | `data/captions_qwen35_9b/caption_manifest_shard0of1.json` | `model_id` = "Qwen/Qwen3.5-9B" |
| RQ1 통제 주입·RQ2 표 4 = Qwen3.5 설명문 배정 | `data/20260717_joint_image_caption_validation/manifest.json`, `data/20260717_ablation_agent_crosscheck/qwen_aligned_circularity/manifest.json` | `embedding_root`에 "qwen3vl2b_unified_qwen35captions"; 주입 manifest `dimension`=2048, `random_filter_reps`=1000 |
| BGE-M3 1,024차원 | `data/embeddings_trisource/bge-m3/embedding_manifest.json` | `model_id`="bge-m3", `embedding_dim`=1024 |
| CLIP ViT-B/32 512차원 | `data/visual_embeddings_clip/manifest.json` | `encoder`="openai/clip-vit-base-patch32", `dim`=512 |
| Qwen3-VL-Embedding-2B 2,048차원 | `data/embeddings_qwen3vl2b_unified_qwen35captions/embedding_manifest.json` | `model_family`="Qwen3-VL-Embedding-2B", `dimension`=2048 |
| L2 정규화 | 위 임베딩 manifest 3종 | `normalize_embeddings`=true / `l2_normalized`=true / `normalization`="L2 by model.process" |
| Faiss CPU 단일 스레드 | `data/verification_suite_20260711/environment_manifest.json`; `data/20260717_joint_image_caption_validation/manifest.json`; `data/20260710_pillarB/filtered_ann_real_A_manifest.json`(B 동일); `data/20260710_pillarB/index_grid_522visual/manifest.json` | `timing_discipline`에 "faiss omp_threads=1"; `latency.threads`=1; `faiss_threads_timing`=1; `faiss_threads_latency`=1 |
| RQ2 준비 2회·반복 10회 | `data/20260717_joint_image_caption_validation/manifest.json`(112개 구성 통합 실험), `data/20260717_joint_image_caption_controls/manifest.json` | `latency.warmup_rounds`=2, `latency.repeats`=10 / `latency.warmup`=2, `latency.repeats`=10 |
| RQ5 준비 실행 제외·반복 15회 | `data/20260710_pillarB/filtered_ann_real_A_manifest.json`, `..._B_manifest.json` | `repeats`=15, `warmup`="kept, excluded from stats [M2]" — 단, 표 10 규모 그리드는 반복 20회(§7 불일치 참조) |
| RRF(순위 융합) 시간 포함 | `data/20260717_joint_image_caption_validation/manifest.json` | `latency.scope` = "search, filter/collapse, and fusion; excludes embedding and build" |
| pgvector 단일 커넥션 | `data/20260710_pillarB/pgvector_manifest.json` | `timing`에 "single warm connection" |
| 실행 시점 컴파일 비활성화 | 같은 파일 | `timing`에 "jit=off" |
| 준비 2회·반복 5회 | 같은 파일 | `timing`에 "W=2 R=5" |
| 질의 300개 | 같은 파일 | `timing`에 "per-query median -> p50/p95 over 300 queries" |
| 왕복 시간 포함(pgvector) | 같은 파일 | `boundary` = "client-side round-trip; …" |

## 3. 사용 데이터셋

표 2 자체는 환경 명세이므로 데이터셋 수치를 직접 인쇄하지 않지만, 각 통제 항목이 걸려 있는 코퍼스는 다음과 같다.

- **AI Hub 교차로(주 평가)**: 클립 3,000개 설명문 코퍼스(질의 85개). 원본 47,098개 시각 클립에서 교차로×시간대 층화·시드 20260710으로 표집한 뒤, 각 클립의 **중간 이미지**를 VLM에 입력해 최대 110토큰 탐욕적 디코딩으로 설명문을 생성했다(Qwen2.5-VL 판: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/captions/`, Qwen3.5-9B 판: `/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/qwen35_9b/522/captions/`).
- **AI Hub 교차로 이미지 벡터**: 프레임 143,830개 × CLIP 512차원, L2 정규화(캐노니컬: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip/`). RQ5 규모 그리드·엔진 복제(코퍼스 B)에 사용.
- **시내도로(sinnaedoro) 이미지 벡터**: 132,521개 × CLIP 512차원, L2 정규화. pgvector 질의 300개 벤치마크와 filtered-ANN 코퍼스 A, Milvus/Weaviate 복제에 사용(pgvector 적재본은 docker `kiise-vlmdb-pgvector` :5433).
- **임베딩 가공 산출물(캐노니컬 경로)**: BGE-M3 문서 임베딩 `…/20260710/embeddings_trisource/bge-m3/`(3,000문서×1,024차원), Qwen3-VL-Embedding-2B 통합 임베딩 `/hdd2/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_unified_qwen35captions/`(2,048차원).

## 4. 실험 체계

- **사용 스크립트(절대경로, `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/`)**
  - `run_full_verification_suite.py` — 환경 캡처(`environment_manifest.json`)와 40개 검증 체크(`report.json`) 생성
  - `run_pgvector_ann_benchmark.py` — pgvector W2 R5·질의 300개 벤치마크와 `pgvector_manifest.json`
  - `run_filtered_ann_real_predicate.py` — RQ5 실측 조건 Faiss 벤치마크(반복 15회, 웜업 제외, 단일 스레드)
  - `run_index_structure_benchmark.py` — RQ5 규모 그리드(`index_grid_522visual`, 반복 20회 기본값)
  - `run_engine_filtered_bench.py` — Milvus/Weaviate 엔진 복제(버전 기록 포함)
  - `run_joint_storage_search_index.py` — RQ2 112개 구성 통합 실험(웜업 2회·반복 10회, 스레드 1)
  - `evaluate_joint_image_caption_controls.py` — RQ2 동일 예산 결합 통제(웜업 2·반복 10)
  - `build_intersection_captions.py` — Qwen2.5-VL 설명문 생성(중간 프레임, 110토큰, greedy)
  - `build_text_embeddings.py` / `build_visual_embeddings.py` — BGE-M3 / CLIP 임베딩과 manifest 생성
- **모델·임베딩**: Qwen2.5-VL-7B-Instruct(snapshot cc594898…), Qwen/Qwen3.5-9B(revision c2022362…), BGE-M3(BAAI--bge-m3, 1,024차원), openai/clip-vit-base-patch32(512차원), Qwen3-VL-Embedding-2B(2,048차원). 모두 L2 정규화.
- **시드**: 전역 20260710, index_bench 20260709, e1a 20260711(`environment_manifest.json`의 `seeds`), 설명문 생성 20260710(Qwen2.5-VL)·20260715(Qwen3.5-9B), RQ2 통합 실험 20260717.
- **관련 사전등록/결과 문서(project_md/)**: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/420_METHOD_prereg_pillarBE_design_20260710.md`(B·E 기둥 설계), `project_md/620_RESULTS_filtered_ann_real_predicates_20260710.md`(RQ5 실측 조건 결과), `project_md/740_AUDIT_experiment_structure_20260714.md`(실험 구조 감사), `project_md/canonical/experiments/EXP03_FILTERED_ANN_PHYSICAL_INDEX_AND_DEPLOYMENT.md`(RQ5 캐노니컬 명세).

## 5. 재현 방법

**(a) 원천 재실행 경로** — 표 2의 각 행을 처음부터 다시 산출하는 순서:

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE
# 1) 장비·소프트웨어 행: 환경 재캡처(environment_manifest.json 재생성)
python3 scripts/run_full_verification_suite.py
# 2) pgvector 통제 행: 단일 커넥션·jit=off·W2 R5·질의 300개
python3 scripts/run_pgvector_ann_benchmark.py
# 3) Faiss 통제 행(RQ5): 실측 조건 벤치마크, 반복 15회·웜업 통계 제외
python3 scripts/run_filtered_ann_real_predicate.py   # 코퍼스 A/B 각각
# 4) Faiss 통제 행(RQ2): 112개 구성 통합 실험, 웜업 2회·반복 10회
python3 scripts/run_joint_storage_search_index.py
# 5) Milvus/Weaviate 버전 행: 엔진 기동 후 복제 벤치마크(버전이 manifest에 기록됨)
python3 scripts/run_engine_filtered_bench.py
# 6) 설명문 생성 행: 중간 프레임·110토큰·greedy (사전 구축 작업)
python3 scripts/build_intersection_captions.py
```

**(b) data/ 사본만으로 재확인하는 최소 경로** — 재실행 없이 표 2의 모든 값을 사본에서 재조회:

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/table2_dir/data
python3 - <<'EOF'
import json
j = lambda p: json.load(open(p))
env = j('verification_suite_20260711/environment_manifest.json')
print(env['cpu'], env['ram'], env['os'], env['python'], env['faiss'], env['postgres'], env['pgvector'])
print(j('20260712_engine_replication/engine_milvus_A_manifest.json')['version'])
print(j('20260712_engine_replication/engine_weaviate_A_manifest.json')['version'])
c25 = j('captions_qwen25vl_7b/caption_manifest_shard0.json')
c35 = j('captions_qwen35_9b/caption_manifest_shard0of1.json')
print(c25['max_new_tokens'], c25['decoding'], c35['model_id'], c35['max_new_tokens'], c35['decoding'])
print(j('embeddings_trisource/bge-m3/embedding_manifest.json')['embedding_dim'],
      j('visual_embeddings_clip/manifest.json')['dim'],
      j('embeddings_qwen3vl2b_unified_qwen35captions/embedding_manifest.json')['dimension'])
val = j('20260717_joint_image_caption_validation/manifest.json')['latency']
print('RQ2:', val['threads'], val['warmup_rounds'], val['repeats'])
fa = j('20260710_pillarB/filtered_ann_real_A_manifest.json')
print('RQ5:', fa['faiss_threads_timing'], fa['repeats'], fa['warmup'])
print('pgvector:', j('20260710_pillarB/pgvector_manifest.json')['timing'])
EOF
```

## 6. 포함 파일 목록

원 절대경로 → `data/` 사본(원 파일명 유지, 동명 `manifest.json` 충돌 방지를 위해 원천 디렉터리 구조를 미러링).

| 원 절대경로 | 사본 | 설명 |
|---|---|---|
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/verification_suite_20260711/environment_manifest.json` | `data/verification_suite_20260711/environment_manifest.json` | 장비·소프트웨어 행의 1차 원천(CPU/RAM/GPU/OS/Python/Faiss/PG/pgvector, 시드, 타이밍 규율) |
| `…/paper_assets/verification_suite_20260711/report.json` | `data/verification_suite_20260711/report.json` | 40개 항목 검증 스위트 결과(40 PASS, L2 정규화·코퍼스 규모 체크 포함) |
| `…/paper_assets/20260710_pillarB/pgvector_manifest.json` | `data/20260710_pillarB/pgvector_manifest.json` | pgvector 통제 행 원천(단일 커넥션, jit=off, W2 R5, 질의 300개, 왕복 경계) |
| `…/paper_assets/20260710_pillarB/filtered_ann_real_A_manifest.json` | `data/20260710_pillarB/filtered_ann_real_A_manifest.json` | RQ5 실측 조건 Faiss 벤치(코퍼스 A 시내도로): 반복 15·웜업 통계 제외·스레드 1 |
| `…/paper_assets/20260710_pillarB/filtered_ann_real_B_manifest.json` | `data/20260710_pillarB/filtered_ann_real_B_manifest.json` | 위와 동일(코퍼스 B 교차로 시각) |
| `…/paper_assets/20260710_pillarB/index_grid_522visual/manifest.json` | `data/20260710_pillarB/index_grid_522visual/manifest.json` | RQ5 규모 그리드(표 10 계열) manifest — 반복 20회(§7 불일치 항목) |
| `…/paper_assets/20260712_engine_replication/engine_milvus_A_manifest.json` | `data/20260712_engine_replication/engine_milvus_A_manifest.json` | Milvus 2.6.0 버전 원천 |
| `…/paper_assets/20260712_engine_replication/engine_weaviate_A_manifest.json` | `data/20260712_engine_replication/engine_weaviate_A_manifest.json` | Weaviate 1.35.3 버전 원천 |
| `…/paper_assets/20260717_joint_image_caption_validation/manifest.json` | `data/20260717_joint_image_caption_validation/manifest.json` | RQ2 112개 구성 통합 실험: 스레드 1·웜업 2·반복 10, RRF 포함 측정 범위, Qwen3.5+Qwen3VL 배정 |
| `…/paper_assets/20260717_joint_image_caption_controls/manifest.json` | `data/20260717_joint_image_caption_controls/manifest.json` | RQ2 동일 예산 결합 통제: 웜업 2·반복 10·2,048차원 교차 확인 |
| `…/paper_assets/20260715_caption_model_ablation/caption_generation_stats.csv` | `data/20260715_caption_model_ablation/caption_generation_stats.csv` | 생성 모델별 110토큰 상한 도달 수 등 설명문 생성 통계 |
| `…/paper_assets/20260723_controlled_supplement/protocol_manifest.json` | `data/20260723_controlled_supplement/protocol_manifest.json` | 동결 보충 프로토콜: `e0`에 110토큰·greedy·Qwen2.5-VL snapshot 재확인 |
| `…/paper_assets/20260717_ablation_agent_crosscheck/qwen_aligned_circularity/manifest.json` | `data/20260717_ablation_agent_crosscheck/qwen_aligned_circularity/manifest.json` | RQ1 통제 주입(Qwen 정렬판): 2,048차원·무작위 필터 1,000회 — 표 2의 RQ 배정 근거 |
| `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/captions/caption_manifest_shard0.json` | `data/captions_qwen25vl_7b/caption_manifest_shard0.json` | Qwen2.5-VL 설명문 생성 manifest(110토큰, greedy, snapshot, 프롬프트) |
| `/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/qwen35_9b/522/captions/caption_manifest_shard0of1.json` | `data/captions_qwen35_9b/caption_manifest_shard0of1.json` | Qwen3.5-9B 설명문 생성 manifest(동일 프롬프트·110토큰·greedy) |
| `…/Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip/manifest.json` | `data/visual_embeddings_clip/manifest.json` | CLIP ViT-B/32 512차원·L2 정규화·143,830 프레임 |
| `…/Datasets/processed/aihub_522_intersection/20260710/embeddings_trisource/bge-m3/embedding_manifest.json` | `data/embeddings_trisource/bge-m3/embedding_manifest.json` | BGE-M3 1,024차원·정규화·3,000문서 |
| `…/Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_unified_qwen35captions/embedding_manifest.json` | `data/embeddings_qwen3vl2b_unified_qwen35captions/embedding_manifest.json` | Qwen3-VL-Embedding-2B 2,048차원·L2 정규화 |

**복사하지 않은 대용량 파일(경로 참조만)**:

- CLIP 프레임 임베딩: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/visual_embeddings_clip/frame_embeddings.npy`(143,830×512)
- BGE-M3 임베딩: `…/20260710/embeddings_trisource/bge-m3/document_embeddings.npy`, `query_embeddings.npy`
- Qwen3-VL 임베딩 루트: `/hdd2/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_unified_qwen35captions/`
- 모델 가중치: `/hdd2/huggingface_cache/hub/models--Qwen--Qwen2.5-VL-7B-Instruct/snapshots/cc594898…`, `/hdd/models/Qwen3.5-9B`, `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/Datasets/models/huggingface/BAAI--bge-m3`, `…/Qwen3-VL-Embedding/models/Qwen3-VL-Embedding-2B`
- 시내도로 코퍼스(pgvector 적재 원본): docker `kiise-vlmdb-pgvector` :5433의 `corpus_real` 132,521×512

## 7. 검증

`data/` 사본을 python3로 실제 재조회하여 원고(148–159행)의 모든 값과 대조했다(2026-07-23 수행, §5(b) 스크립트와 동일 로직).

| # | 원고 값 | 사본에서 읽은 값 | 판정 |
|---|---|---|---|
| 1 | Intel i7-9700K | "Intel(R) Core(TM) i7-9700K CPU @ 3.60GHz" | PASS |
| 2 | 메모리 62GB | "62GB" | PASS |
| 3 | RTX 3090 24GB 2대 | GPU 2개, 각 "RTX 3090, 24576 MiB" | PASS |
| 4 | Linux 5.15 | "Linux 5.15.0-139-generic" | PASS |
| 5 | Python 3.10.20 | "3.10.20" | PASS |
| 6 | Faiss 1.14.3 | "1.14.3" | PASS |
| 7 | PostgreSQL 16.14 | "16.14 (Debian 16.14-1.pgdg12+1)" | PASS |
| 8 | pgvector 0.8.4 | "0.8.4" | PASS |
| 9 | Milvus 2.6.0 | "server 2.6.0 / pymilvus 3.0.0" | PASS |
| 10 | Weaviate 1.35.3 | "server 1.35.3 / weaviate-client 4.22.0" | PASS |
| 11 | 중간 이미지 | 사본 manifest에는 프레임 선택 방식이 기록되어 있지 않음. `scripts/build_intersection_captions.py` 69행 `middle_frame()`·18행 주석("middle frame of each video is captioned")으로 확인 | **UNVERIFIED**(data 사본 기준; 스크립트 원문으로는 확인됨) |
| 12 | 최대 110토큰 | Qwen2.5-VL·Qwen3.5-9B·supplement `e0` 모두 `max_new_tokens`=110 | PASS |
| 13 | 탐욕적 디코딩 | 세 파일 모두 `decoding`="greedy" | PASS |
| 14 | Qwen2.5-VL-7B-Instruct | snapshot 경로 "models--Qwen--Qwen2.5-VL-7B-Instruct" | PASS |
| 15 | Qwen3.5-9B | `model_id`="Qwen/Qwen3.5-9B" | PASS |
| 16 | BGE-M3 1,024차원 | `embedding_dim`=1024, model_path BAAI--bge-m3 | PASS |
| 17 | CLIP ViT-B/32 512차원 | "openai/clip-vit-base-patch32", `dim`=512 | PASS |
| 18 | Qwen3-VL-Embedding-2B 2,048차원 | `dimension`=2048 | PASS |
| 19 | L2 정규화 | `normalize_embeddings`=true / `l2_normalized`=true / "L2 by model.process" | PASS |
| 20 | Faiss CPU 단일 스레드 | env "omp_threads=1"; RQ2 `threads`=1; RQ5 A/B `faiss_threads_timing`=1; 그리드 `faiss_threads_latency`=1 | PASS |
| 21 | RQ2 준비 2회·반복 10회 | validation `warmup_rounds`=2·`repeats`=10; controls `warmup`=2·`repeats`=10 | PASS |
| 22 | RQ5 준비 실행 제외·반복 15회 | filtered_ann_real A/B `repeats`=15, `warmup`="kept, excluded from stats [M2]" | PASS(단서 있음 — 아래 불일치) |
| 23 | (22의 단서) 표 10 규모 그리드 반복 횟수 | `index_grid_522visual/manifest.json` `repeats`=**20** | **FAIL/불일치** |
| 24 | RRF 시간 포함 | validation `latency.scope`="search, filter/collapse, and fusion; …" | PASS |
| 25 | pgvector 단일 커넥션 | "single warm connection" | PASS |
| 26 | 실행 시점 컴파일 비활성화 | "jit=off" | PASS |
| 27 | 준비 2회·반복 5회 | "W=2 R=5" | PASS |
| 28 | 질의 300개 | "over 300 queries" | PASS |
| 29 | RQ 배정(Qwen3.5→RQ1 주입·RQ2 표4) | validation `embedding_root`에 "qwen3vl2b_unified_qwen35captions"; 주입 manifest `dimension`=2048·`random_filter_reps`=1000 | PASS |

**집계: 실질 검증 항목 29건 중 27 PASS / 1 UNVERIFIED(#11) / 1 불일치(#23).**

**불일치·미확인 상세(얼버무리지 않음):**

1. **(#23, 불일치)** 표 2의 Faiss 통제 행은 "RQ5 준비 실행 제외·반복 15회"라고 쓰는데, 이는 RQ5의 **실측 조건 filtered-ANN 벤치마크**(`filtered_ann_real_A/B`, 반복 15회)에만 정확하다. RQ5에 속하는 **표 10 규모 그리드**(`index_grid_522visual`)는 반복 **20회**(웜업 폐기)로 측정되었고 이 사실은 표 2에도 원고 본문에도 적혀 있지 않다. 표 2 행이 RQ5의 모든 Faiss 측정을 포괄한다고 읽으면 부정확하므로, 저자는 "RQ5 실측 조건 15회, 규모 그리드 20회"로 나누어 쓰거나 각주로 구분할 것을 권한다.
2. **(#11, UNVERIFIED)** "중간 이미지"(클립의 중간 프레임 사용)는 복사한 어떤 결과/manifest 파일에도 기록되어 있지 않다. 생성 스크립트 `scripts/build_intersection_captions.py`의 `middle_frame()` 구현과 모듈 주석으로는 확인되지만, 데이터 산출물 기준의 독립 검증은 불가능하므로 UNVERIFIED로 남긴다.
3. **(참고)** `environment_manifest.json`의 `timing_discipline`에는 "warmup=5 excluded"라는 일반 문구가 있는데, 이는 검증 스위트 시점의 요약 문구이며 개별 벤치마크 manifest의 웜업 값(RQ2=2, RQ5=통계 제외, pgvector W=2)이 각 실험의 실제 기록이다. 상충이 아니라 기록 계층의 차이다.
4. **(참고)** Milvus/Weaviate 버전은 환경 manifest가 아니라 엔진 복제 manifest(2026-07-12)에서 확인된다. 표 2의 "전 과정 엔진·라이브러리 버전 고정" 문구 중 Milvus/Weaviate 부분의 근거 시점은 해당 복제 실험이다.
