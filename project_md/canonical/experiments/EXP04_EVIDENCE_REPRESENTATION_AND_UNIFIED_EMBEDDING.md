# EXP04 — 증거 표현, 통합 임베딩과 캡션 물질화

- 대응 질문: RQ2, RQ4, RQ5 일부
- 상태: 완료
- 최신 정본: 동일-Qwen 5개 표현, 112개 호환 구성
- 결과 지위: joint arm은 결과 전 amendment, 기존 4표현 우선 대조는 사후 정리, 전역 최적 주장은 금지
- [정정 2026-07-28: 확정 용어 결정에 따라 보고서·향후 개정 원고에서는 '증거 표현'을 '검색용 데이터 표현(저장 표현)'으로, latency 경계의 'evidence fetch'는 '검색 결과 원문 인출'로 표기한다. 제출본 paper_final.pdf(2026-07-23)에는 미적용]

## 1. 목적

같은 clip을 어떤 단위로 벡터화해 저장할지, image와 caption을 하나의 벡터로 결합할지, 다중 벡터 또는 이중 색인을 유지할지 비교한다. 표현 효과와 encoder 효과가 섞이지 않도록 최신 주 실험에서는 모든 표현과 질의를 같은 Qwen3-VL-Embedding-2B 공간에 맞춘다.

## 2. 비교군

| ID | 표현 | 입력 | clip당 벡터 | fusion |
|---|---|---|---:|---|
| C | caption | Qwen3.5 canonical caption | 1 | 없음 |
| F | representative frame | canonical 대표 프레임 | 1 | 없음 |
| J | joint matched | 같은 clip의 frame+caption | 1 | encoder 내부 early fusion |
| JS | joint shuffled | frame+다른 clip caption | 1 | 음성 대조 |
| M | multi-frame | clip당 최대 3프레임 | ≤3 | max-score clip collapse |
| D | dual | caption lane+multi-frame lane | 1+≤3 | RRF late fusion |

JS는 seed 20260717의 deterministic derangement이며 fixed point가 0이다. J/JS 입력에는 metadata, relevance, qrels와 정답 렉시콘이 없다.

## 3. 공통 조건

- data: 522 3,000 clips, 85 queries
- strict qrels: 6,809
- semantic qrels: 24,872
- encoder: Qwen3-VL-Embedding-2B
- output: 2,048d float32, L2 normalized
- inference: BF16, FlashAttention2
- instruction: `Represent the user's input.`
- `max_pixels=534600`
- C/F/J: 3,000×2,048, 동일 24.576MB vector payload
- query embeddings: 처리군 공통 85×2,048
- primary cell: B2 vector-only + Flat exact
- search latency에서 embedding generation과 evidence fetch 제외

J의 이미지와 F의 대표 프레임은 같은 `media_path`, J의 caption과 C의 텍스트는 같은 canonical document를 사용한다.

## 4. 가설과 estimand

### P1 — 동일 단일벡터 예산

- J−C, J−F
- primary: paired-query semantic nDCG@10
- secondary: strict nDCG@10, MRR, Recall@10, Hit@10
- SESOI: absolute nDCG@10 0.02

### P2 — 정확한 정합의 식별

- J−JS
- matched가 shuffled보다 유의하게 높을 때만 올바른 clip-level alignment의 인과 효과로 해석한다.

### S1 — 단일 압축 대 다중 저장

- J 대 M/D
- 품질, payload, serialized index, p50/p95, build를 공동 비교
- vector 수와 fusion이 다르므로 순수 표현 주효과가 아니라 Pareto 비교다.

### S2 — 검색 계획 상호작용

- 각 호환 표현에 B2/B3/B4
- strict/semantic을 분리

### S3 — 색인

- Flat
- HNSW ef64/256
- IVF-Flat nprobe8/32
- IVF-PQ6 nprobe8/32

## 5. 실행 행렬

1. C/F/J/JS × B2 × Flat의 equal-budget 대조
2. C/F/M/D/J × 호환 search plan × 7 indexes
3. JS는 음성 대조이므로 전체 격자에 넣지 않음
4. 비호환 cell을 제외한 총 112 configurations
5. 19,040 metric cells
6. 95,200 latency trials

이 행렬은 완전 요인설계가 아니다. C/F/J/M/D의 처리 의미를 유지할 수 있는 조합만 포함한다.

## 6. 무결성 gate

1. clips/documents 3,000↔3,000 join
2. representative frame 3,000/3,000 존재
3. J의 matched pair 3,000/3,000
4. JS fixed point 0, caption source 3,000개 유일
5. vector shape `(3000,2048)`, finite 100%
6. L2 norm tolerance 5e-3
7. clip order가 기존 index와 일치
8. model/instruction/attention/max_pixels/input/output hash
9. raw ranking에서 metric 재계산
10. filtered ranking의 predicate 위반 0
11. strict qrel logic 재계산

독립 verifier는 17/17을 통과했다.

## 7. equal-budget 결과

| 표현 | strict nDCG@10 | semantic nDCG@10 | p50 | p95 | payload |
|---|---:|---:|---:|---:|---:|
| caption | 0.0626 | 0.1810 | 1.146ms | 1.488ms | 24.576MB |
| representative frame | 0.0625 | 0.1865 | 1.172ms | 1.479ms | 24.576MB |
| joint matched | 0.0794 | 0.2182 | 1.138ms | 1.443ms | 24.576MB |
| joint shuffled | 0.0572 | 0.1958 | 1.170ms | 1.523ms | 24.576MB |

### 7.1 paired uncertainty

| 비교 | 평가 | Δ | query 95% CI | cluster 95% CI |
|---|---|---:|---:|---:|
| J−C | semantic | +0.0372 | [+0.0156,+0.0586] | [-0.0048,+0.0742] |
| J−C | strict | +0.0168 | [-0.0014,+0.0364] | [+0.0059,+0.0289] |
| J−F | semantic | +0.0317 | [+0.0030,+0.0614] | [-0.0165,+0.0836] |
| J−F | strict | +0.0169 | [-0.0049,+0.0403] | [+0.0001,+0.0358] |

joint는 85개 질의 평균에서 유효한 단일벡터 후보지만 semantic cluster CI가 0을 포함하므로 새 intent/facet에 대한 보편 우위는 확증되지 않았다.

### 7.2 matched–shuffled

| 평가 | J−JS Δ | query 95% CI | cluster 95% CI |
|---|---:|---:|---:|
| strict | +0.0223 | [-0.0095,+0.0555] | [-0.0120,+0.0611] |
| semantic | +0.0224 | [-0.0345,+0.0799] | [-0.0930,+0.1445] |

따라서 joint 점추정 상승을 “올바른 image-caption alignment가 원인”이라고 말할 수 없다. 입력 형식, caption 정보의 우세 또는 표본 변동이 남는다.

## 8. 다중벡터·dual과의 Pareto

| 표현 | strict | semantic | p50 | p95 | payload |
|---|---:|---:|---:|---:|---:|
| C | 0.0626 | 0.1810 | 1.155ms | 1.488ms | 24.576MB |
| F | 0.0625 | 0.1865 | 1.207ms | 1.529ms | 24.576MB |
| J | 0.0794 | 0.2182 | 1.243ms | 1.574ms | 24.576MB |
| M | 0.1014 | 0.3518 | 3.651ms | 4.274ms | 68.395MB |
| D | 0.0889 | 0.2933 | 4.959ms | 5.661ms | 92.971MB |

J는 M보다 semantic이 0.1336 낮지만 payload 64.07%, p95 63.18%가 작다. D보다 semantic이 0.0751 낮지만 payload 73.57%, p95 약 72.2%가 작다. J는 정확도 우승자가 아니라 단일벡터 비용과 다중모달 품질 사이의 중간 Pareto 후보다.

M−C semantic Δ는 +0.171, cluster CI [+0.018,+0.316]이지만 storage-family cluster BH q=0.112이므로 family-wise 0.05 확증으로 부르지 않는다.

## 9. 검색 계획 상호작용

joint/Flat 결과:

| 계획 | strict | semantic | p50 | p95 |
|---|---:|---:|---:|---:|
| B2 | 0.0794 | 0.2182 | 1.243ms | 1.574ms |
| B3 | 0.1805 | 0.1777 | 1.284ms | 1.603ms |
| B4 | 0.1861 | 0.1829 | 0.532ms | 1.137ms |

B4−B2:

- strict +0.1067, query CI [+0.0818,+0.1334], cluster CI [+0.0666,+0.1418]
- semantic -0.0353, query CI [-0.0648,-0.0059], cluster CI [-0.0676,-0.0024]

같은 joint 표현에서도 hard constraint와 soft semantic 목적이 반대 방향으로 움직인다.

## 10. joint 색인 결과

| index | semantic | p95 | size | exact-task top-10 fidelity |
|---|---:|---:|---:|---:|
| Flat | 0.2182 | 1.574ms | 24.576MB | 1.0000 |
| HNSW ef64 | 0.2193 | 0.312ms | 25.392MB | 0.9647 |
| HNSW ef256 | 0.2182 | 0.865ms | 25.392MB | 1.0000 |
| IVF-Flat np32 | 0.2182 | 0.810ms | 별도 manifest | 0.9988 |
| IVF-PQ np8 | 0.1928 | 0.142ms | 1.145MB | 0.3824 |

ANN score가 Flat보다 소폭 높은 경우는 근사 순위 교란이지 표현 품질 향상이 아니다. task fidelity와 함께 해석한다.

## 11. 캡션 생성기 ablation

### 11.1 고정 조건

- 동일 프레임
- 동일 task-aware prompt
- greedy decoding
- 110-token 상한
- 동일 BGE-M3 downstream retrieval
- 522, MEVA, UCA
- caption 무결성·A6 9/9

### 11.2 결과

| 데이터 | Qwen2.5-VL | Qwen3-VL score, Δ [95% CI] | Qwen3.5 score, Δ [95% CI] |
|---|---:|---:|---:|
| 522 | 0.1700 | 0.2419, +0.0719 [0.0288,0.1164] | 0.2722, +0.1022 [0.0348,0.1706] |
| MEVA | 0.1029 | 0.4541, +0.3513 [0.3024,0.4003] | 0.2710, +0.1681 [0.1441,0.1932] |
| UCA | 0.2504 | 0.2190, -0.0314 [-0.0587,-0.0037] | 0.3044, +0.0540 [0.0151,0.0920] |

Qwen3-VL은 MEVA에서 가장 높지만 UCA에서 하락한다. 최신 세대의 보편 우위가 아니라 caption materialization의 model×domain interaction이다. UCA token-limit 도달률은 Qwen3 85.52%, Qwen3.5 54.04%다.

## 12. 구형 혼합-encoder 결과의 취급

과거 저장 비교는 caption에 BGE-M3, frame에 CLIP을 사용하여 representation과 encoder가 섞였다. 이 결과는 실제 시스템 조합 기준선으로는 유지할 수 있지만 순수 저장 단위의 주효과로 해석하지 않는다. 최신 112구성 동일-Qwen 실험이 논문 주 결과의 정본이다.

## 13. 결과 지위와 허용 주장

### 허용

- joint는 같은 단일벡터 예산에서 caption/frame보다 높은 평균 점추정치를 보인다.
- joint는 multi/dual보다 품질은 낮고 비용은 작은 중간 운용점이다.
- multi-frame은 522에서 높은 semantic 품질을 보이나 더 많은 payload와 지연을 사용한다.
- 저장 표현의 선택은 strict/semantic 목적, latency와 space SLA에 의존한다.
- caption generator는 offline DB materialization의 중요한 변수이며 도메인 의존적이다.

### 금지

- 정확한 image-caption alignment가 joint 이득의 원인이라고 주장하지 않는다.
- multi-frame을 보편적 최적 표현으로 부르지 않는다.
- 112개 중 관측 최고점을 통계적으로 검증된 전역 최적이라고 부르지 않는다.
- dual을 순수 storage 효과로 부르지 않는다. RRF가 함께 바뀐다.
- 3K task 결과를 143K task relevance로 일반화하지 않는다.
- retrieval 향상을 최종 VLM 답변 향상으로 확대하지 않는다.

## 14. 원자산

- joint protocol: `2026_KIISE/project_md/820_JOINT_IMAGE_CAPTION_SINGLE_VECTOR_PROTOCOL_20260717.md`
- joint controls: `2026_KIISE/paper_assets/20260717_joint_image_caption_controls/`
- 112-grid: `2026_KIISE/paper_assets/20260717_joint_image_caption_validation/`
- joint materialization: `Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_joint_image_caption_qwen35captions/`
- caption ablation: `2026_KIISE/paper_assets/20260715_caption_model_ablation/`
- scripts:
  - `2026_KIISE/scripts/build_qwen3_joint_image_caption_assets.py`
  - `2026_KIISE/scripts/evaluate_joint_image_caption_controls.py`
  - `2026_KIISE/scripts/run_joint_storage_search_index.py`
  - `2026_KIISE/scripts/analyze_joint_optimization_validation.py`
  - `2026_KIISE/scripts/verify_joint_image_caption_experiment.py`

## 15. 변경 시 재실행 조건

- canonical caption 또는 representative frame 변경
- encoder snapshot·instruction·max_pixels·normalization 변경
- JS derangement 변경
- clip collapse 또는 dual RRF 규칙 변경
- search-plan/index 파라미터 변경
- vector payload 계산 단위 변경
- cluster family 또는 BH family 변경

## 레거시 결과 문서 흡수 (2026-07-28)

SYNC 기준: `manuscript/paper_final.pdf`(2026-07-23 제출본, 총 21쪽). 상충 판정 시 제출 논문 수치가 정본이다. 아래 아카이브 경로는 이관 예정 위치의 문서화이며, 이 흡수 시점에 원본 파일은 물리적으로 이동하지 않았다.

### A1. 750_RAG_baseline_contract_20260714.md

(a) 요약: 분리 방식(캡션→텍스트 임베딩 + 메타데이터 별도 필터)이 보편적 RAG 표준임을 외부 근거로 확립하고, joint 방식과의 apples-to-apples 비교 계약(코퍼스·질의·이중 qrels·지표·출력 형식·baseline 수치)을 고정한 문서.

(b) EXP04 본문에 없는 고유 정보:
- 벡터DB 7종(pgvector·Milvus·Weaviate·Qdrant·Pinecone·Chroma·Elasticsearch) 전수 확인 — filtered vector search(내용=벡터, 메타=별도 필터)가 전 제품 1급 기능. 메타데이터의 임베딩 융합은 프로덕션 표준이 아닌 신흥/연구(Cohere Embed4, voyage-multimodal-3 등). 외부 조사 근거 wf_88e90ff0.
- 멀티모달 검색 4계열 분류: (a) caption-then-embed / (b) CLIP-직접 / (c) multi-vector(ColPali) / (d) joint 단일벡터. 본 파이프라인의 caption-as-document는 (a)계열 — 가장 단순·모듈러하되 세밀한 시각·카운팅에 약한 lossy 선택이며, 이는 내부 실험의 캡션 맹점·frame-vector 우위 관측과 일관.
- 비교 출력 계약: 질의별 clip_id 랭킹 `[query_id, rank, clip_id, score]`(`retrieval_results.parquet` 형식)만 산출하면 동일 `vlmdb_workload.metrics.evaluate_ranking`·동일 이중 qrels로 즉시 채점 가능.
- BGE-M3 lane baseline 스냅샷(strict nDCG@10): B0 metadata-only 0.218 / B2 vector-only 0.059 / B4 prefilter+vector 0.157 / B5 hybrid 0.135.
- 공정성 원칙: joint가 메타데이터를 벡터에 넣으면 정확 필터 보장이 사라지고 순환성 위험 발생 → (i) 동일 비순환 qrels 채점 + (ii) "정확 필터 보장 여부"를 별도 축으로 병기해야 apples-to-apples 성립.
- 메타데이터 필터는 pre/post 변이가 존재하므로 특정 변이를 canonical로 확정하지 않고 "filtered vector search"로 표기하라는 표기 지침.

(c) 상충과 정정:
- qrels 행수 "strict 6,810 / semantic 24,873" → 정본·제출 논문은 strict 6,809 / semantic 24,872. 계약 문서 수치가 낡음.
- "B5 hybrid 0.135" → 제출 논문 RQ4는 혼합 RRF 0.133. 논문 수치가 정본(계약은 제출 전 스냅샷).
- "통합(joint 임베딩) 방식은 타 전문가가 별도 수행" → 낡음. joint는 2026-07-17 동일-Qwen 프로토콜(820/821)로 내부 수행 완료되어 제출 논문 다섯 설계 축 ①의 '이미지·설명문 결합'으로 반영됨. 단 실제 실현은 이 계약의 BGE-M3 lane 대비가 아니라 동일-Qwen equal-budget 대조(§7)였다.
- B4 0.157은 논문 RQ3 검색 전 조건 Δ+0.0983(0.059+0.0983≈0.157)과 정합 — 상충 아님.

(d) 아카이브: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/750_RAG_baseline_contract_20260714.md`

### A2. 750_UNIFIED_EMBEDDING_baseline_framing_20260714.md

(a) 요약: 단일 통합 임베딩 vector-only 검색을 비교군으로 추가하는 확장의 적합성 검토 — "모델 의존성 노출로 DB 설계 필요성을 정당화한다"는 프레이밍과 U 계열/DB 계열 실험 설계 제안.

(b) EXP04 본문에 없는 고유 정보:
- text-only single embedding(bge-m3, e5, Qwen3-Embedding, EmbeddingGemma, NV-Embed-v2, llama-embed-nemotron-8b)과 multimodal unified embedding(CLIP, SigLIP, Qwen3-VL-Embedding)의 구분 원칙. Llama/Gemma는 생성 LLM family 이름이므로 embedding 전용 모델명을 명시해야 한다는 주의.
- H1(단일 임베딩은 strong baseline이나 hard metadata constraint에 불충분)–H2(성능·실패 양상이 embedding model 선택에 민감)–H3(DB-aware 구조가 보완) 가설 체계와 검증 방법(모델 간 Kendall tau, per-query winner 분포, mixed-effects 분산 분석).
- 모델 후보 재고 상태: bge-m3 main, e5 robustness, CLIP main visual, SigLIP 로컬 확보, NV-Embed-v2·llama-embed-nemotron-8b 로컬 캐시 존재. 권장 최소 세트 4종(bge-m3 / NV-Embed 또는 nemotron / CLIP 또는 SigLIP / Qwen3-VL-Embedding).
- 미실행 결과표 설계: 표 A(모델 의존성), 표 B(단일 임베딩 vs DB-aware regime별 승자), 표 C(모델 쌍 Kendall tau@100 진단).
- 논문 프레이밍 문장(영/국문) 원문과 위험 4항(모델 우열 단정 금지, "단일 임베딩은 나쁘다" 금지, DB-aware 전승 주장 금지, 모델 비교 논문화 금지).

(c) 상충과 정정:
- Qwen3-VL-Embedding을 "추가 확보 후보"로 기재 → 낡음. 이후 Qwen3-VL-Embedding-2B가 본 EXP04 112구성 주 실험의 공통 encoder로 승격되어 이미 확보·사용됨.
- U2/U3 및 표 A/B/C의 다중 embedding 모델 의존성 비교는 미실행 제안으로 남았고 제출 논문 다섯 설계 축에 포함되지 않음. 향후 보강실험(S2-S4) 후보로만 유효.
- 문서 전반의 '증거(evidence unit)' 표기는 2026-07-28 확정 용어 결정에 따라 '검색용 데이터/검색 문맥/관련 클립'으로 치환 대상.
- '데이터베이스 계층' 계열 표현은 향후 원고에서 '벡터 데이터베이스 계층'으로 통일.

(d) 아카이브: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/750_UNIFIED_EMBEDDING_baseline_framing_20260714.md`

### A3. 810_CAPTION_MODEL_ABLATION_20260715.md

(a) 요약: 캡션 생성 VLM 세대 교체(Qwen2.5-VL-7B → Qwen3-VL-8B / Qwen3.5-9B) ablation의 사전 명세·실행 기록·완료 판정 — EXP04 §11 결과의 원 명세 문서.

(b) EXP04 본문에 없는 고유 정보:
- 모델 고정 revision(qwen25vl_7b `cc594898...cfb5`, qwen3vl_8b `0c351dd0...ff3b`, qwen35_9b `c2022362...b9a`)과 로컬 경로(`/hdd/models/...`). Qwen3.6-27B 제외 근거: fp16 약 54GB로 단일 RTX 3090 예산 초과, 포함 시 양자화/모델 병렬이라는 별도 요인 추가.
- 세 데이터셋 규모: 522 3,000프레임/85질의, MEVA 985프레임/193질의(DIVA 주석), UCA 6,432프레임/135질의(동결 렉시콘 판정).
- 생성 고정 조건 상세: 최대 200,704픽셀(448px 상당), 110-token 상한, greedy, fp16, PyTorch SDPA, Qwen3.5 `enable_thinking=False`.
- Amendment 1(07-15 10:21): 토큰 상한 도달을 실행 중단 게이트에서 품질 advisory로 재분류 — 상한 도달 모델 제외나 모델별 예산 증액은 결과 의존 선택이 되므로 금지한다는 논리.
- 전체 토큰 상한 도달률: Qwen3-VL-8B 5,957/10,417건(57.19%), Qwen3.5-9B 3,709/10,417건(35.61%). EXP04 §11.2에는 UCA 국한 수치(85.52%/54.04%)만 있음.
- 운영 기록: GPU lane 병렬화·이전(07-15 11:54, 07-16 03:00), GPU 0 thermal slowdown 81–82C, 처리율 0.138→0.255 image/s(품질 판정에 미사용), systemd 서비스 2종(`kiise-caption-ablation-generate/finalize.service`).
- 완료 검증 규모: 9/9×3종 감사, 72개 paired delta 행, 36개 주 paired 비교 행 전수 유한 CI, canonical 비문서 해시 15그룹·query embedding 해시 3그룹·B0 랭킹 3그룹 모델 간 일치.
- 경로: 실험 루트 `/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715`, 결과 `CAPTION_MODEL_ABLATION_RESULTS_KO.md`·`VERDICT.json`.

(c) 상충과 정정:
- 판정 상충 없음 — EXP04 §11.2와 동일(Qwen3.5-9B만 세 데이터셋 모두 B2 semantic nDCG@10 유의 개선, Qwen3-VL-8B는 UCA 유의 하락 → 보편 우위 아님, model×domain interaction).
- 해석 주의(상충 아님): 이 ablation의 downstream retrieval은 BGE-M3 + B0–B5 lane이며 EXP04 주 실험의 Qwen3-VL-Embedding-2B 112구성 lane과 encoder가 다르다. 두 lane의 수치를 직접 비교하지 않는다. 제출 논문 본문의 다섯 설계 축·112구성에는 이 ablation 수치가 포함되지 않음(보강 자산).

(d) 아카이브: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/810_CAPTION_MODEL_ABLATION_20260715.md`

### A4. 820_JOINT_IMAGE_CAPTION_SINGLE_VECTOR_PROTOCOL_20260717.md

(a) 요약: joint 단일벡터(J/JS) 비교의 결과 전 amendment 프로토콜 — 처리군·estimand·실행 행렬·무결성 게이트·주장 경계를 결과 산출 전에 고정. EXP04 §2–§6의 원 명세.

(b) EXP04 본문에 없는 고유 정보:
- 구성 산식 분해: 기존 91-config에 J의 신규 21구성(3계획×7색인)을 더해 112구성. 제출 논문 산식(1×4+4×3=16 × 7색인=112)과 동일 결과의 증분 분해.
- JS 음성 대조는 B2+Flat만 실행한다는 명시적 제한(전체 색인 격자 제외 근거).
- 판정 규칙 사전 고정: 점추정+query bootstrap CI+`relevance_def×facet` cluster CI에 family 내 BH 보정 q-value 병기, cluster family-wise 0.05 미통과 시 보편 우위 주장 금지.
- JS가 C/F보다 높게 나올 경우의 진단 절차(도메인 공통 어휘·추가 토큰·모델 편향 점검).
- 전처리 비용은 materialization manifest에 별도 기록, 검색 지연에서 제외.
- 일반화 금지 대상의 정확 수치: 143,830-vector task relevance(EXP04 본문은 "143K"로 축약).
- 24시간 스트림의 지속 적재·삭제·재색인 비용은 측정 범위 밖이며 clip당 joint materialization 시간만 보고한다는 범위 한정.

(c) 상충과 정정:
- 상충 없음 — strict 6,809/semantic 24,872, encoder·instruction·max_pixels 등 모두 정본·제출 논문과 일치. EXP04 무결성 게이트 11항은 이 문서 10항의 상위 집합(strict qrel logic 재계산 추가).

(d) 아카이브: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/820_JOINT_IMAGE_CAPTION_SINGLE_VECTOR_PROTOCOL_20260717.md`

### A5. 821_RESULTS_joint_image_caption_single_vector_20260717.md

(a) 요약: joint 단일벡터 실험의 결과 보고서 — EXP04 §7–§10 수치의 원 출처이며 제출 논문 표4 '이미지·설명문 결합' 행의 근거.

(b) EXP04 본문에 없는 고유 정보:
- materialization 비용 실측: joint matched GPU 827.45초(13.79분, 3.63 clips/s), shuffled 727.81초(12.13분, 4.12 clips/s).
- L2 norm 실측 범위: matched 0.9975–1.0025, shuffled 0.9974–1.0025.
- 상대 개선율: J−C semantic +20.53%, J−F semantic +16.98%(점추정).
- 불확실성 산정 상세: query bootstrap 10,000회 + intent×facet 25개 cluster bootstrap 10,000회.
- 색인 절충 정량: HNSW ef256은 Flat 대비 p95 45.05% 감소·직렬화 색인 3.32% 증가에 task score/top-10 fidelity 완전 보존; IVF-PQ는 색인 약 95.34% 축소에 fidelity 0.3824로 급락.
- 독립 검증 보고서 경로: `2026_KIISE/paper_assets/20260717_joint_image_caption_validation/JOINT_IMAGE_CAPTION_VERIFICATION_KO.md`(17개 검사 통과의 원 기록).

(c) 상충과 정정:
- 상충 없음 — 모든 수치가 EXP04 §7–§10과 동일하고, 제출 논문 표4의 반올림 값(설명문 0.063/0.181/1.15ms/24.6MB, 다중 이미지 0.101/0.352/3.65ms/68.4MB, 이중 색인 0.089/0.293/4.96ms/93.0MB) 및 RQ2 서술과 정합. 허용/보류 주장 경계도 §13과 일치.
- 표기 주의(상충 아님): 이 문서의 "저장 payload와 검색 지연은 사실상 같은 범위" 등 점추정 우위 서술은 §7.1의 cluster CI 0 포함 한계와 반드시 함께 인용한다.

(d) 아카이브: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/821_RESULTS_joint_image_caption_single_vector_20260717.md`

### 공통 용어 정정 (2026-07-28 확정, 제출 PDF 미적용)

- '데이터베이스 계층' → '벡터 데이터베이스 계층'.
- '증거' 전면 치환: DB 반환=상위 k 검색 결과, VLM 입력=검색 문맥(retrieved context), 정답 판정=관련 클립/검색 정답 집합. 위 레거시 문서들의 'evidence unit/증거' 표기는 인용 시 치환한다.
- 클립 조작적 정의: 데이터셋 배포 mp4 1파일=1클립(MEVA 계보로 방어).
