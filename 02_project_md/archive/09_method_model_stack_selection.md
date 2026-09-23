# 방법론 구성요소 선정 근거

작성 기준일: 2026-07-06

2026-07-09 최신 갱신: 모델 스택은 초기 optional 설계에서 실제 사용 범위가 확정되었다. Retrieval layer는 BGE-M3/E5와 CLIP/SigLIP 중심이고, answer-level control은 Qwen2.5/Llama LLM 및 Qwen2.5-VL/Qwen2-VL/InternVL3/Idefics2 VLM을 고정 모델로 사용한다. 최신 모델 사용 범위는 `22_model_stack_spec_and_usage_20260707.md`를 따른다.

## 목적

이 문서는 현재 확보한 `VRU-Accident` 데이터로 KIISE 데이타베이스연구 투고 실험을 수행할 때 사용할 Vector Database, sparse retrieval, embedding model, reranker, VLM/LLM을 선정하고, 심사 과정에서 "왜 이 방법과 모델을 선택했는가"에 답할 근거를 정리한다.

핵심 원칙은 다음과 같다.

1. 본 논문의 주된 변수는 모델 성능이 아니라 **metadata-aware retrieval architecture**다.
2. 따라서 모델은 최신 연구 커뮤니티에서 널리 쓰이거나 강한 benchmark 근거가 있는 것을 하나의 표준 선택으로 고정한다.
3. 모델 선택 자체가 논문을 복잡하게 만들지 않도록 main stack과 optional robustness stack을 분리한다.
4. 2주 내 투고 일정을 고려해 과도한 fine-tuning, 대규모 distributed vector DB, 장시간 video model inference는 피한다.

## 최종 권장 스택

| 계층 | 최종 선택 | 역할 | 선정 이유 |
|---|---|---|---|
| Vector DB | PostgreSQL 16 + pgvector | metadata table, vector column, HNSW/IVFFlat/exact search, SQL prefilter | DB 논문 맥락에 가장 적합. SQL `WHERE` 기반 metadata prefilter와 vector search 결합을 명확히 실험 가능 |
| ANN reference | FAISS | exact/ANN recall sanity check, pgvector 결과 검증 | dense vector search 연구의 사실상 표준. GPU/CPU index와 파라미터 통제가 쉬움 |
| Sparse retrieval | BM25 via Pyserini/Anserini | lexical baseline | SIGIR 계열 reproducible IR toolkit. BM25-only baseline 방어에 유리 |
| Text embedding | BAAI/bge-m3 | caption/query dense embedding | ACL Findings 2024. multilingual, dense/sparse/multi-vector, long input 지원. 한국어 논문/영어 데이터 혼합 상황에 안전 |
| Text embedding robustness | intfloat/e5-large-v2 | dense embedding sensitivity check | BEIR/MTEB 기반 강한 zero-shot retrieval 근거. bge-m3 결과가 특정 모델 의존인지 확인 |
| Reranker | BAAI/bge-reranker-v2-m3 | optional top-k reranking | bge-m3 계열 multilingual reranker. main result가 아니라 upper-bound 분석에만 사용 |
| Visual embedding | SigLIP2 or SigLIP keyframe embedding | optional image-text retrieval ablation | CLIP 계열보다 최신 V-L encoder. 단, main 실험은 VRU dense caption 기반 retrieval로 둔다 |
| Video foundation model | InternVideo2 | optional video embedding reference | ECCV 2024 video foundation model. 설치/추론 부담 때문에 관련연구 또는 확장 실험 후보 |
| VLM | InternVL3-8B | optional evidence-aware VQA | VRU-Accident benchmark에서 직접 평가된 open-source MLLM 계열. 24GB GPU에서 현실적인 크기 |
| VLM robustness | Qwen2.5-VL-7B-Instruct | optional VQA/caption robustness | 2025년 이후 video understanding, localization, long-video 기능 근거가 강한 open VLM |
| Closed-source upper bound | Gemini 1.5 Flash or GPT-4o-mini | optional upper-bound | VRU-Accident 논문에서 Gemini 계열 강세가 보고됨. 재현성/비용 문제로 필수 제외 |

## 선택하지 않는 것과 이유

| 후보 | 배제 또는 보류 이유 |
|---|---|
| Milvus/Qdrant/Weaviate 단독 사용 | production vector DB로 타당하지만, 본 논문에서는 DBMS 내부 metadata filter와 vector query의 결합 위치가 핵심이다. PostgreSQL+pgvector가 SQL prefilter/postfilter 비교를 더 투명하게 만든다. |
| 대형 embedding model only | Qwen3-Embedding-8B, NV-Embed-v2 등은 성능은 강하지만 2주 실험에서 비용과 추론 시간이 커진다. 본 논문은 embedding model SOTA가 아니라 retrieval architecture 분석이 목표다. |
| VLM fine-tuning | 데이터 규모와 일정상 불필요하다. 모델 학습을 넣으면 DB 논문 메시지가 약해지고 실험 리스크가 커진다. |
| full video embedding 중심 설계 | VRU-Accident는 dense caption과 VQA annotation이 이미 잘 갖춰져 있다. 2주 내에는 caption/query/metadata retrieval을 먼저 완성하고, visual/video embedding은 ablation으로만 둔다. |
| LLM 기반 query generation 중심 | 질의 생성에 LLM을 쓰면 qrels 편향과 재현성 문제가 생긴다. main query는 metadata facet 기반 template으로 생성한다. |

## Vector DB 선정

### 최종 선택: PostgreSQL + pgvector

본 연구의 핵심 비교는 다음 네 가지다.

1. vector-only 검색
2. vector top-N 이후 metadata post-filter
3. metadata pre-filter 이후 vector 검색
4. BM25 + dense vector + metadata hybrid fusion

이 비교는 SQL의 `WHERE` 절, relational metadata table, vector distance ordering을 함께 사용할 수 있어야 가장 명확하다. PostgreSQL+pgvector는 다음 이유로 적합하다.

- `clip`, `metadata`, `document`, `query`, `qrels`를 같은 DB 안에 둘 수 있다.
- `WHERE accident_type = ... AND road_type = ... ORDER BY embedding <=> query_embedding` 형태로 prefilter 실험을 직접 구성할 수 있다.
- HNSW, IVFFlat, exact scan을 바꿔 index trade-off를 측정할 수 있다.
- DBR 심사자에게 친숙한 relational DB 기반 실험으로 설명 가능하다.

다만 pgvector는 대규모 vector DB 시스템 자체의 성능을 대표하지 않는다. 따라서 논문에는 다음처럼 한계를 명시한다.

> 본 연구는 vector DB 제품 간 성능 비교가 아니라, 동일한 멀티모달 워크로드에서 metadata filter와 vector retrieval의 결합 방식이 검색 품질과 지연시간에 미치는 영향을 분석한다.

### 보조 선택: FAISS

FAISS는 vector search의 reference implementation으로 사용한다.

- pgvector 결과의 exact nearest-neighbor sanity check
- HNSW/Flat index 설정에 따른 recall-latency trade-off 확인
- DBMS query planner 영향과 ANN 자체 영향을 분리

논문에서는 FAISS를 주 시스템이 아니라 "ANN reference backend"로 둔다.

## Sparse Retrieval 선정

### 최종 선택: BM25 via Pyserini/Anserini

BM25는 dense embedding 이전부터 쓰인 강한 lexical retrieval baseline이다. 본 연구에서 BM25를 반드시 넣어야 하는 이유는 다음과 같다.

- VRU dense caption에는 `pedestrian`, `cyclist`, `intersection`, `rainy`, `urban`처럼 lexical match가 강한 단어가 많다.
- vector-only가 항상 이긴다는 단순 주장을 막고, sparse+dense hybrid의 실효성을 평가할 수 있다.
- Pyserini/Anserini는 SIGIR 2021 reproducible IR toolkit으로, "임의 구현"이라는 비판을 줄인다.

만약 설치 리스크가 있으면 1차 실험은 Python BM25로 수행하되, 원고에는 "Pyserini-compatible BM25 scoring" 또는 "Okapi BM25 implementation"으로 정확히 명시한다.

## Text Embedding 선정

### 최종 선택: BAAI/bge-m3

`bge-m3`를 main dense embedding model로 선택한다.

선정 근거:

- ACL Findings 2024 논문으로 공개된 최신 embedding 계열이다.
- 100개 이상 언어를 지원해, 영어 데이터셋과 한국어 논문/질의 확장 가능성을 동시에 방어할 수 있다.
- dense retrieval, sparse retrieval, multi-vector interaction을 하나의 모델군에서 지원한다.
- 최대 8192 token 입력을 지원해 VRU-Accident의 긴 dense caption을 잘 다룰 수 있다.
- open-weight라 재현 가능성이 높다.

본 연구에서는 bge-m3의 dense vector만 main으로 사용한다. sparse는 BM25로 분리한다. 이렇게 해야 sparse/dense/hybrid 구조의 차이를 해석하기 쉽다.

### Robustness baseline: intfloat/e5-large-v2

`e5-large-v2`는 robustness check로 적합하다.

- E5는 BEIR와 MTEB에서 강한 zero-shot retrieval 성능 근거가 있다.
- retrieval query/document prefix 방식이 명확해 재현성이 좋다.
- bge-m3 하나에 결과가 과도하게 의존한다는 비판을 줄일 수 있다.

단, 일정상 e5-large-v2는 모든 실험에 넣지 않고 핵심 table의 일부 조건에서만 비교한다.

## Visual/Video Embedding 선정

### Main policy: caption-first

현재 데이터는 원본 mp4와 함께 dense caption, VQA annotation이 이미 있다. 논문의 main retrieval evidence는 dense caption과 VQA-derived metadata로 둔다.

이 선택은 방어 가능하다.

- 본 논문은 VLM 모델을 새로 평가하는 것이 아니라, VLM/VQA를 지원하는 DB retrieval 구조를 평가한다.
- 실제 VLM-DB 시스템에서도 영상은 caption, object/event label, metadata, embedding으로 변환되어 검색된다.
- dense caption은 VRU-Accident benchmark에서 제공하는 정식 annotation이므로 임의 생성 caption보다 재현성이 높다.

### Optional ablation: SigLIP2/SigLIP keyframe embedding

시간이 허용되면 영상에서 1~3개 keyframe을 추출하고 SigLIP 계열 image-text embedding을 만든다.

권장 위치:

- main result가 아니라 ablation table
- 질문: "caption-only retrieval에 visual keyframe embedding을 추가하면 recall이 개선되는가?"

### 보류: InternVideo2

InternVideo2는 ECCV 2024 video foundation model로 연구 근거는 강하다. 하지만 설치, GPU memory, video batch inference 비용이 크다. 본 투고에서는 관련연구와 향후 확장 후보로 두고, 실제 실험에는 넣지 않는 편이 안전하다.

## VLM/LLM 선정

### Main experiment에서는 VLM을 필수로 두지 않는다

본 논문의 필수 실험은 retrieval이다. VQA는 다음 이유로 선택 실험이어야 한다.

- VLM 답변 품질은 model backbone의 영향을 크게 받아 DB 구조 기여를 흐릴 수 있다.
- VRU-Accident VQA는 정답 option이 이미 있어 retrieval hit@K만으로도 evidence lookup 평가가 가능하다.
- 2주 일정에서 VLM video inference는 병목이 될 가능성이 높다.

따라서 main table은 retrieval metrics로 구성하고, VLM은 "retrieved evidence가 VQA에 전달될 때의 proxy 또는 small-scale optional evaluation"으로 둔다.

### 선택 VLM: InternVL3-8B

InternVL3-8B는 다음 이유로 적합하다.

- VRU-Accident benchmark에서 직접 비교된 open-source MLLM 계열이다.
- VRU 공식 codebase도 InternVL3 계열 실행 예시를 제공한다.
- 8B 규모는 24GB GPU 환경에서 현실적으로 운영 가능하다.
- open-source라 재현성과 비용 측면에서 closed-source API보다 낫다.

### Robustness VLM: Qwen2.5-VL-7B-Instruct

Qwen2.5-VL-7B는 다음 경우에 보조로 쓴다.

- InternVL3 설치가 어렵거나 inference 속도가 지나치게 느릴 때
- video understanding과 temporal grounding 능력을 강조하고 싶을 때
- 최신 open VLM 계열과의 연결을 강화하고 싶을 때

### Closed-source upper bound

Gemini 1.5 Flash 또는 GPT-4o-mini는 upper-bound로만 둔다. 논문 본문에서는 비용, API version drift, 재현성 문제를 명시해야 한다. KIISE 투고에서는 open-source main result가 더 방어 가능하다.

## 실험 Baseline 정의

| ID | 구조 | 구현 |
|---|---|---|
| B0 | Metadata-only | SQL filter 후 빈도/기본 ranking |
| B1 | BM25-only | Pyserini/Anserini 또는 BM25 implementation |
| B2 | Dense vector-only | bge-m3 + pgvector HNSW |
| B3 | Dense vector + post-filter | vector top-N 검색 후 metadata 조건 적용 |
| B4 | Metadata pre-filter + dense vector | SQL `WHERE` 후 vector ordering |
| B5 | Hybrid sparse+dense+metadata | BM25와 vector rank를 RRF 또는 weighted sum으로 fusion |
| B6 optional | Hybrid + reranker | B5 top-50에 bge-reranker-v2-m3 적용 |
| B7 optional | Visual keyframe fusion | caption embedding + SigLIP keyframe embedding |

논문 main table은 B0~B5만으로 충분하다. B6/B7은 결과가 좋을 때만 추가한다.

## Query/Metadata 설계와 모델 의존성 최소화

VRU-Accident VQA의 `category`는 모든 영상에 동일하게 6개씩 존재하므로, 그대로 metadata로 쓰면 선택도 실험이 약하다. 반드시 `options`와 `answer`를 파싱해 실제 정답 facet을 만들어야 한다.

예시:

| category | answer option에서 추출할 facet |
|---|---|
| `weather and light` | `sunny day`, `rainy day`, `clear night` |
| `location` | `urban`, `rural`, `suburban` |
| `road type` | `arterials`, `intersection`, `T-junction` |
| `accident type` | `car hits pedestrian`, `car hits cyclist` |
| `accident reason` | causal phrase |
| `prevention method` | prevention phrase |

이렇게 만든 facet으로 weak/medium/strong selectivity query를 구성한다.

| 난도 | 예시 | 목적 |
|---|---|---|
| Weak | `Find videos where a car hits a pedestrian.` | semantic retrieval 기본 성능 |
| Medium | `Find urban intersection accidents involving a pedestrian.` | 1~2개 metadata 조건 |
| Strong | `Find rainy urban arterial-road accidents where a car hits a pedestrian.` | metadata selectivity stress test |

질의는 LLM 생성이 아니라 template 기반으로 만든다. LLM paraphrase는 optional robustness만 사용한다.

## 논문에 넣을 방어 문장 초안

> 본 연구의 목적은 특정 embedding model 또는 VLM backbone의 최고 성능을 주장하는 것이 아니라, 동일한 멀티모달 교통 안전 데이터베이스에서 metadata filter와 sparse/dense retrieval을 결합하는 방식이 검색 품질과 지연시간에 미치는 영향을 분석하는 것이다. 따라서 dense embedding에는 최근 multilingual retrieval에서 강한 성능과 재현성을 보이는 BGE-M3를 사용하고, BM25와 pgvector 기반 HNSW 검색을 표준 baseline으로 고정하였다. 또한 E5 및 reranker를 제한적 robustness 실험으로 사용하여 결론이 특정 embedding model에 과도하게 의존하지 않음을 확인한다.

## 구현 우선순위

1. `bge-m3` dense embedding + BM25 + pgvector/FAISS retrieval을 먼저 완성한다.
2. B0~B5의 Recall@K, MRR, nDCG, p50/p95 latency, index size를 산출한다.
3. e5-large-v2로 핵심 조건 일부를 재실행해 robustness를 확인한다.
4. 시간이 남으면 bge-reranker-v2-m3 또는 SigLIP keyframe ablation을 추가한다.
5. VLM은 main table 이후 optional evidence-aware VQA proxy로만 둔다.

## 주요 출처

- pgvector: https://github.com/pgvector/pgvector
- pgvector 0.8.0 release: https://www.postgresql.org/about/news/pgvector-080-released-2952/
- FAISS: https://github.com/facebookresearch/faiss
- FAISS paper: https://arxiv.org/abs/2401.08281
- Pyserini: https://github.com/castorini/pyserini
- Pyserini SIGIR 2021: https://dl.acm.org/doi/10.1145/3404835.3463238
- BGE-M3 ACL Findings 2024: https://aclanthology.org/2024.findings-acl.137/
- BGE-M3 model: https://huggingface.co/BAAI/bge-m3
- E5 paper: https://arxiv.org/abs/2212.03533
- e5-large-v2 model: https://huggingface.co/intfloat/e5-large-v2
- bge-reranker-v2-m3: https://huggingface.co/BAAI/bge-reranker-v2-m3
- Qwen2.5-VL: https://arxiv.org/abs/2502.13923
- InternVL3: https://arxiv.org/abs/2504.10479
- InternVL repository: https://github.com/OpenGVLab/InternVL
- VRU-Accident: https://github.com/Kimyounggun99/VRU-Accident
- VRU-Accident paper: https://arxiv.org/abs/2507.09815
- SigLIP2: https://arxiv.org/abs/2502.14786
- InternVideo2: https://arxiv.org/abs/2403.15377
