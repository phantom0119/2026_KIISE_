# 820 — Image–Caption 단일 joint vector 비교 실험 프로토콜

- 고정일: 2026-07-17 KST, 신규 joint 검색 결과 산출 전
- 목적: 동일 클립의 대표 프레임과 생성 캡션을 하나의 Qwen3-VL 입력으로 공동 인코딩한 단일 벡터가 기존 단일모달·다중벡터·이중색인 표현과 형성하는 품질–지연–공간 절충을 측정한다.
- 주 데이터: AI Hub 522 교차로, 3,000 clips, 85 queries
- 정답: strict qrels 6,809행, semantic qrels 24,872행
- encoder: Qwen3-VL-Embedding-2B, 2,048d, BF16, FlashAttention2, `max_pixels=534600`
- 공통 instruction: `Represent the user's input.`
- 주의: 본 문서는 기존 91-config 결과 이후 제안된 신규 표현에 대한 결과 전 amendment다. 기존 저장 표현 결과 전체를 사전등록으로 소급하지 않는다.

## 1. 처리와 비교군

| ID | 표현 | 문서 입력 | clip당 벡터 | 결합 시점 | 역할 |
|---|---|---|---:|---|---|
| C | caption | 생성 캡션 | 1 | 없음 | 텍스트 단일벡터 기준 |
| F | representative frame | 대표 프레임 | 1 | 없음 | 시각 단일벡터 기준 |
| J | joint matched | 대표 프레임 + 그 클립의 캡션 | 1 | encoder 내부 early fusion | 신규 처리 |
| JS | joint shuffled | 대표 프레임 + 다른 클립의 캡션 | 1 | encoder 내부 early fusion | 정합성 음성 대조 |
| M | multi-frame | 클립당 최대 3프레임 | 최대 3 | 검색 후 clip collapse | 다중벡터 기준 |
| D | dual | caption lane + multi-frame lane | 1+최대 3 | RRF late fusion | 이중색인 기준 |

J와 JS는 `clip_id`의 이미지 순서를 고정한다. JS의 캡션은 seed 20260717의 deterministic derangement로 배정하고 fixed point를 0건으로 강제한다. J/JS 입력에는 metadata, relevance label, qrels, 정답 렉시콘을 넣지 않는다.

## 2. 가설과 estimand

### P1 — 동일 one-vector 예산의 표현 효과

- 비교: J−C, J−F
- anchor: B2 vector-only + Flat exact
- 주 estimand: query-paired semantic nDCG@10 차이
- 보조: strict nDCG@10, MRR, Recall@10, Hit@10
- 실무 SESOI: 절대 nDCG@10 0.02

판정은 점추정, query bootstrap 95% CI, `relevance_def × facet` cluster bootstrap CI를 함께 보고한다. family 내 BH 보정 q-value를 병기하며, cluster family-wise 0.05를 통과하지 않으면 보편 우위를 주장하지 않는다.

### P2 — 정합된 image–caption 결합의 식별

- 비교: J−JS
- anchor: B2 vector-only + Flat exact
- 주 estimand: semantic nDCG@10 차이
- 해석: J가 JS를 앞설 때만 두 모달리티의 올바른 clip-level 정합이 제공한 이득으로 해석한다.

JS가 C 또는 F보다 낮은 것은 음성 대조의 정상 결과이며, JS가 높으면 도메인 공통 어휘·추가 토큰·모델 편향 가능성을 진단한다.

### S1 — 압축 표현 대 다중 저장

- 비교: J 대 M, J 대 D
- 지표: strict/semantic nDCG@10, vector payload, serialized index MB, p50/p95, build time
- 지위: secondary cost–quality Pareto. 벡터 수가 다르므로 순수 표현 주효과가 아니다.

### S2 — 필터 계획 상호작용

- J에 B2 vector-only, B3 fixed-top-200 postfilter, B4 prefilter를 적용한다.
- strict와 semantic을 별도로 보고한다.
- hard predicate에서 B4 이득, soft semantic 목적에서 손실 가능성을 기존 표현과 같은 방식으로 평가한다.

### S3 — 물리 색인

- Flat, HNSW ef64/256, IVF-Flat nprobe8/32, IVF-PQ6 nprobe8/32
- ANN task metric은 matching Flat 대비 task top-10 fidelity와 함께 해석한다.
- 작은 ANN 점수 상승은 exact 결과 보존 오차로 간주하고 표현 품질 향상으로 해석하지 않는다.

## 3. 실행 행렬

1. 핵심 equal-budget 대조: C/F/J/JS × B2 × Flat.
2. 공동 설계공간: 기존 C/F/M/D에 J를 추가하고 호환 계획×7개 색인을 실행한다.
3. J는 B2/B3/B4와 호환되므로 신규 21개 구성, 전체 112개 구성이 된다.
4. JS는 음성 대조이므로 B2+Flat만 실행하며 전체 색인 격자에 넣지 않는다.

## 4. 고정 조건

- canonical clips, queries, strict/semantic qrels, query vectors를 변경하지 않는다.
- C/F/M/D/J의 query embedding은 기존 Qwen text-only 85×2,048 자산을 공유한다.
- J의 이미지와 F의 representative frame은 같은 `media_path`를 사용한다.
- J의 캡션과 C의 caption은 같은 Qwen3.5 canonical document text를 사용한다.
- J/C/F는 모두 3,000×2,048 float32 L2-normalized vector로 one-vector payload를 동일하게 한다.
- 검색 지연은 embedding 생성과 evidence fetch를 제외하고, 전처리 비용은 materialization manifest에 별도 기록한다.

## 5. 무결성 gate

1. clips/documents 3,000↔3,000 one-to-one join.
2. 대표 프레임 존재 3,000/3,000.
3. J caption match 3,000/3,000.
4. JS caption match 0/3,000.
5. vector shape `(3000, 2048)`, float32, finite 100%.
6. L2 norm 허용오차 5e-3 이내.
7. clip_id 순서가 기존 caption/frame index와 일치.
8. 모델·instruction·attention·max_pixels·input/output hash manifest 저장.
9. raw per-query ranking에서 지표 독립 재계산.
10. filtered ranking의 metadata predicate 위반 0건.

## 6. 주장 경계

- J가 C/F보다 높으면 동일 one-vector 예산에서 early fusion 이득을 주장할 수 있다.
- J가 JS보다 높지 않으면 “정합된 멀티모달 결합”의 이득으로 주장하지 않는다.
- J가 M/D보다 낮아도 단일벡터의 공간·지연 절감이 Pareto 전선을 만들면 유효한 DB 설계 결과다.
- J가 모든 기준보다 낮으면 단일벡터 압축에서 정보 손실이 발생한 음성 결과로 보고한다.
- 3,000-clip 결과를 143,830-vector task relevance로 일반화하지 않는다.
- 24시간 스트림의 지속 적재·삭제·재색인 비용은 이번 실험의 측정 범위 밖이며, clip당 joint materialization 시간만 보고한다.

## 7. 실행 산출물

- 물질화: `Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_joint_image_caption_qwen35captions/`
- shuffled 통제: 위 경로의 `_shuffled` suffix
- equal-budget 결과: `2026_KIISE/paper_assets/20260717_joint_image_caption_controls/`
- 112-config 결과: `2026_KIISE/paper_assets/20260717_joint_image_caption_validation/`
- 실행기:
  - `scripts/build_qwen3_joint_image_caption_assets.py`
  - `scripts/evaluate_joint_image_caption_controls.py`
  - `scripts/run_joint_storage_search_index.py`
  - `scripts/analyze_joint_optimization_validation.py`
