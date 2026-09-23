# 2026-07-23 통제 보강 실험 재현 안내

이 디렉터리는 투고 완료된 주 실험을 본 뒤 수행한 E0·S2–S4 후속 통제 분석의 판정용 산출물이다. 원 연구의 사전등록 자료가 아니다. 각 실험의 신규 판정용 결과를 만들기 전에 분석 규칙을 `project_md/912_SUPPLEMENT_CONTROL_PROTOCOL_FROZEN_20260723.md`와 `protocol_manifest.json`에 동결했으며, 성공·실패·중단 결과를 모두 보존했다.

## 1. 포함 자료

- `e0_prompt_target_ablation/`: 과제-인지/과제-중립 캡션의 대응 검색 결과, 진단 통계와 입력 해시
- `s2_blocked_coupling/`: 교차로 5-fold 차단 결과와 임계 민감도
- `s3_cluster_mechanism/`: 2개 코퍼스×HNSW/IVF-Flat의 선택도 보존 음성·양성 대조, 질의별 결과와 그림
- `s4_mcq_gate/`: 결과를 보지 않고 만든 3지선다 문항 계획
- `s4_retrieval_population/`: VLM 호출 전 과제 관련 검색 조작 게이트와 제외 사유
- `sha256.txt`: 이 디렉터리 최상위 파일의 해시. 각 하위 결과 디렉터리에는 별도의 `sha256.txt`가 있다.

원본 영상, 모델 가중치와 대용량 임베딩은 라이선스·용량 때문에 이 디렉터리에 복제하지 않는다. 필요한 입력의 경로와 SHA-256은 `protocol_manifest.json` 및 각 실험의 `manifest.json`에 기록되어 있다.

## 2. 실행 환경

- Python 3.10.20
- Faiss 1.14.3
- PyTorch/Transformers 환경: `Datasets/envs/kiise-vlmdb`
- E0 생성 모델: Qwen2.5-VL-7B-Instruct snapshot `cc594898137f460bfe9f0759e9844b3ce807cfb5`
- E0 임베딩: BGE-M3, 1,024차원, L2 정규화
- 공통 후속 분석 시드: `20260723`

아래 명령은 저장소 루트 `KIISE_datasociety/`에서 실행한다.

## 3. 판정 결과 검증

```bash
Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/verify_controlled_supplement.py --require-e0

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/verify_paper_script_numbers.py
```

2026-07-23 최종 상태는 보강 실험 6/6, 원고 수치·인용·게이트 68/68 통과다. 검증기는 투고 완료 PDF와 기본 양식 PDF의 SHA-256도 확인하므로 두 파일의 불변성을 함께 점검한다.

## 4. 실험별 재실행

### E0

GPU별 shard 생성 후 merge, canonical 재구축, BGE-M3 임베딩, 대응 분석 순서로 실행한다.

```bash
Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/build_intersection_captions.py \
  --shard 0/2 --device cuda:0 \
  --prompt-file 2026_KIISE/paper_assets/20260723_controlled_supplement/e0_task_neutral_prompt.txt \
  --out-dir Datasets/processed/aihub_522_intersection/20260710/captions_task_neutral_rerun

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/build_intersection_captions.py \
  --shard 1/2 --device cuda:1 \
  --prompt-file 2026_KIISE/paper_assets/20260723_controlled_supplement/e0_task_neutral_prompt.txt \
  --out-dir Datasets/processed/aihub_522_intersection/20260710/captions_task_neutral_rerun

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/build_intersection_captions.py --merge-only \
  --out-dir Datasets/processed/aihub_522_intersection/20260710/captions_task_neutral_rerun

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/build_intersection_trisource_canonical.py --expanded \
  --captions-path Datasets/processed/aihub_522_intersection/20260710/captions_task_neutral_rerun/documents.parquet \
  --out-dir Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded_task_neutral_rerun

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/build_text_embeddings.py \
  --canonical-root Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded_task_neutral_rerun \
  --model-id bge-m3 \
  --output-dir Datasets/processed/aihub_522_intersection/20260710/embeddings_trisource_expanded_task_neutral_rerun/bge-m3 \
  --device cuda:0 --batch-size 32

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/analyze_prompt_target_ablation.py \
  --neutral-canonical Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded_task_neutral_rerun \
  --neutral-embeddings Datasets/processed/aihub_522_intersection/20260710/embeddings_trisource_expanded_task_neutral_rerun/bge-m3 \
  --output-dir 2026_KIISE/paper_assets/20260723_controlled_supplement/e0_prompt_target_ablation_rerun
```

### S2

```bash
Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/run_coupling_blocked_validation.py \
  --output-dir 2026_KIISE/paper_assets/20260723_controlled_supplement/s2_blocked_coupling_rerun
```

### S3

```bash
Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/run_filtered_ann_cluster_mechanism.py \
  --corpus A --methods hnsw,ivf \
  --output-root 2026_KIISE/paper_assets/20260723_controlled_supplement/s3_cluster_mechanism_rerun

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/run_filtered_ann_cluster_mechanism.py \
  --corpus B --methods hnsw,ivf \
  --output-root 2026_KIISE/paper_assets/20260723_controlled_supplement/s3_cluster_mechanism_rerun
```

각 실행은 기존 판정 디렉터리 덮어쓰기를 기본적으로 거부한다. 재실행 비교가 필요하면 별도 `--output-dir` 또는 `--output-root`를 지정한다.

### S4

```bash
Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/prepare_s4_mcq_gate.py \
  --output-dir 2026_KIISE/paper_assets/20260723_controlled_supplement/s4_mcq_gate_rerun

Datasets/envs/kiise-vlmdb/bin/python \
  2026_KIISE/scripts/prepare_s4_retrieval_population.py \
  --output-dir 2026_KIISE/paper_assets/20260723_controlled_supplement/s4_retrieval_population_rerun
```

두 범주의 retrieval manipulation gate가 모두 실패했으므로 `run_s4_mcq_gate.py`와 대규모 VLM 답변 생성은 실행하지 않는 것이 동결 프로토콜을 따른 재현 결과다. `s4_mcq_gate/`에 결과 파일이 없는 것은 누락이 아니라 사전 중단 기준의 결과다.

## 5. 외부 공개 시 제외·확인 사항

- AI Hub 및 기타 원본 영상·주석은 각 이용약관에 따라 재배포 가능 범위를 별도로 확인한다.
- 공개 패키지는 스크립트, 프롬프트, query/qrels 식별자, 파생 집계, 질의별 결과, manifest와 해시를 우선 대상으로 한다.
- 심사 정책에 맞는 익명 또는 공개 URL은 이 로컬 패키지에 포함되어 있지 않다. URL을 확보하기 전에는 원고에 외부 공개 완료를 주장하지 않는다.
