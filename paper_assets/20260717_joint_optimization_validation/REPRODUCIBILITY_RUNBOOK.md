# 재현 실행 순서

작업 디렉터리:

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety
```

## 1. 522 동일 encoder 자산

```bash
CUDA_VISIBLE_DEVICES=0 Qwen3-VL-Embedding/.venv/bin/python \
  2026_KIISE/scripts/build_qwen3_unified_assets.py \
  --repair-missing --overwrite-text
```

## 2. 522 저장 × 검색 × 색인 격자

```bash
Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/run_joint_storage_search_index.py --overwrite

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/analyze_joint_optimization_validation.py
```

## 3. Qwen-2048 대규모 색인

```bash
Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/run_index_structure_benchmark.py \
  --corpus Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_unified_qwen35captions/frame_embeddings.npy \
  --queries Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_unified_qwen35captions/query_embeddings.npy \
  --real-n 143830 \
  --out 2026_KIISE/paper_assets/20260717_joint_optimization_validation/qwen2048_scaled_index \
  --n-queries 85 --scales 10000,50000,100000,143830 \
  --repeats 10 --warmup 3 --full-grid-at 143830 --seed 20260717

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/run_qwen2048_ann_seed_robustness.py

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/analyze_qwen2048_scaled_index.py
```

## 4. MEVA 외부 동일 encoder 통제

```bash
CUDA_VISIBLE_DEVICES=1 Qwen3-VL-Embedding/.venv/bin/python \
  2026_KIISE/scripts/build_qwen3_meva_unified_assets.py --overwrite

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/run_external_same_encoder_storage_control.py --overwrite
```

## 5. 독립 검산

```bash
Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/verify_joint_optimization_independently.py
```

성공 조건은 `independent_verification.json`의 `overall_pass: true`와 32/32 gate PASS다.

## 6. Ablation 교차감사 보강

```bash
# treatment, qrel logic, paired delta/BH, MEVA BH
Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/verify_ablation_treatment_integrity.py

# 주 격자와 동일 Qwen 공간의 C1/C2 (GPU)
CUDA_VISIBLE_DEVICES=0 Qwen3-VL-Embedding/.venv/bin/python \
  2026_KIISE/scripts/run_qwen_aligned_circularity_control.py --overwrite

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/verify_qwen_aligned_circularity.py

# 143,830-vector high-recall 5-seed search-strength ablation
Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/run_qwen2048_high_recall_robustness.py

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/verify_qwen2048_high_recall_robustness.py
```

추가 성공 조건은 treatment/statistics 12/12, Qwen circularity 10/10,
high-recall ANN 8/8 gate PASS다.

## 참고

- 모든 ANN 구조의 구축 시드는 명시적으로 고정한다.
- IVF/PQ는 `N >= 39 × nlist` 조건을 만족하지 않는 구성을 실행하지 않는다.
- latency는 embedding 생성과 index build를 제외한 search/filter/collapse/fusion 범위다.
- PQ 시드 반복은 기본적으로 제외한다. 고정 시드 recall이 낮아 high-fidelity 후보가 아니기 때문이다.
