# 750 — 단일 통합 임베딩 baseline 확장 프레이밍 검토 (2026-07-14)

## 1. 결론

단일 통합 임베딩 기반 벡터 검색을 비교군으로 추가하는 것은 본 연구에 **적합하다**.  
다만 프레이밍은 다음처럼 잡아야 한다.

> 본 연구는 통합 임베딩 모델이 무의미하다고 주장하는 것이 아니라,  
> 멀티모달 감시 데이터 검색에서 단일 벡터 공간에만 의존하면 성능이 embedding model 선택에 크게 좌우되고,  
> 센서·시공간 metadata와 저장 단위, 색인 구조를 명시적으로 다루는 DB 설계가 필요함을 보인다.

따라서 이 확장은 기존 연구 주제를 바꾸지 않는다. 오히려 기존 주제인 “저장·색인·검색 구조 비교”를 정당화하는 강한 baseline 축이 된다.

---

## 2. 용어 정리: "단일 통합 임베딩"은 무엇인가

반드시 다음 두 개를 구분해야 한다.

### A. Text-only single embedding

VLM caption이나 event text를 하나의 텍스트 임베딩 모델로 벡터화하고, query도 같은 모델로 벡터화해 검색한다.

예:

- BAAI/bge-m3
- intfloat/e5-large-v2
- Qwen3-Embedding
- EmbeddingGemma
- NV-Embed-v2
- llama-embed-nemotron-8b

이 방식은 현재 `clip-caption` / `B2 dense`와 가장 가깝다.

### B. Multimodal unified embedding

텍스트, 이미지, 영상 등을 같은 벡터 공간으로 매핑해 cross-modal 검색을 수행한다.

예:

- CLIP
- SigLIP
- Qwen3-VL-Embedding

이 방식은 `frame-vector`, `text-to-image/frame retrieval`, `image-to-video retrieval`과 가깝다.

중요: Llama/Gemma는 일반적으로 생성 LLM family 이름이다. “Llama/Gemma 임베딩”이라고 말하려면 각각의 embedding 전용 모델을 명시해야 한다. 예를 들어 Gemma는 EmbeddingGemma가 있고, Llama는 Meta 공식 Llama 자체보다 NVIDIA의 `llama-embed-nemotron-8b` 같은 Llama 기반 embedding 모델을 쓰는 표현이 더 정확하다.

---

## 3. 본 연구에 넣을 수 있는 핵심 가설

### H1. 단일 통합 임베딩 검색은 strong baseline이지만 항상 충분하지 않다

단일 vector-only 검색은 자연어 의미를 잘 잡을 수 있다. 그러나 도시 감시 검색에서는 다음 조건이 동시에 붙는다.

- 시간대
- 위치
- 신호 상태
- 차량/보행 밀도
- 특정 장면 사건
- 사람 주석 기반 relevance

이때 하나의 벡터 공간이 이 모든 구조화 조건을 안정적으로 반영한다고 보장할 수 없다.

### H2. 단일 vector-only 성능은 embedding model 선택에 민감하다

같은 query와 같은 corpus라도 embedding model이 바뀌면 ranking이 달라질 수 있다. 이 차이가 크다면, 단일 vector-only 방식은 DB 설계 원리라기보다 특정 모델 성능에 의존한 결과가 된다.

주의: "성능이 낮은 이유가 오직 모델 때문이다"라고 쓰면 안 된다. 정확한 표현은 다음이다.

> 단일 벡터 검색의 성능과 실패 양상은 embedding model에 크게 의존한다.

### H3. DB-aware structure는 model-dependent baseline의 한계를 보완한다

본 연구의 구조는 모델 하나의 의미 공간에 모든 것을 맡기지 않는다.

- metadata는 metadata table과 predicate로 명시적으로 관리
- 영상 evidence는 clip/frame/multi-vector/dual-index로 저장 단위를 비교
- filter는 prefilter/postfilter/single-stage/local index로 결합 위치를 비교
- 관계형 DB에서는 partial/local index와 hot/cold 정책까지 비교

따라서 "모델이 좋아지면 DB 구조 비교가 필요 없어지는가?"라는 질문에 대해:

> 아니다. 모델이 좋아질수록 vector-only baseline은 강해질 수 있지만, hard metadata constraint, selective predicate, storage/latency/cost trade-off는 여전히 DB 설계 문제로 남는다.

---

## 4. 권장 실험 설계

### 4.1 실험군 정의

#### U 계열: 단일 임베딩 baseline

| ID | 설명 | 모델 후보 |
|---|---|---|
| U1-caption-text | caption을 하나의 text embedding으로 검색 | bge-m3, e5, Qwen3-Embedding, EmbeddingGemma, NV-Embed, llama-embed-nemotron |
| U2-frame-vl | query text와 frame image를 같은 V-L embedding으로 검색 | CLIP, SigLIP, Qwen3-VL-Embedding |
| U3-video/clip-unified | 가능할 경우 clip/video 자체를 unified embedding으로 검색 | Qwen3-VL-Embedding |

#### DB 계열: 본 연구 구조

| ID | 설명 |
|---|---|
| D1 prefilter+vector | metadata 조건으로 먼저 후보를 제한 후 vector ranking |
| D2 postfilter | vector ranking 후 metadata 조건 적용 |
| D3 hybrid | sparse+dense+metadata 결합 |
| D4 storage-unit best | 522는 clip-caption, MEVA는 frame-vector 등 각 dataset의 Pareto 구조 |
| D5 partial/local index | 선택적 predicate에 대한 관계형 DB 구현 구조 |

### 4.2 공정 비교 원칙

모든 비교는 다음을 고정해야 한다.

- 같은 dataset
- 같은 query
- 같은 qrels
- 같은 top-k
- 같은 strict/semantic 평가
- 같은 evidence unit 정의
- 같은 latency 계측 경계

단일 임베딩 모델이 text-only인지 multimodal인지도 표에 분리해야 한다. text-only embedding과 multimodal embedding을 한 줄에서 직접 비교하면 해석이 흐려진다.

---

## 5. 증명해야 할 것

사용자가 제안한 4단계는 가능하지만, 문장을 조금 조정해야 한다.

### 원 제안 1

> 단일 통합 임베딩 결과물의 벡터 검색 결과가 상대적으로 좋지는 않다.

수정:

> 단일 통합 임베딩 기반 vector-only 검색은 strong baseline이지만, hard metadata constraint와 일부 fine-grained surveillance query에서는 충분하지 않다.

이렇게 써야 한다. 일부 최신 unified embedding이 특정 semantic query에서 본 시스템보다 나을 수 있기 때문이다.

### 원 제안 2

> 그 이유 중 하나는 AI 임베딩 모델의 성능에 지배적이기 때문이다.

수정:

> 단일 vector-only 검색의 성능과 실패 양상은 embedding model 선택에 크게 의존한다.

증명 방법:

- 모델별 nDCG@10/Recall@10/MRR 비교
- query-level paired bootstrap
- 모델 간 rank correlation 또는 Kendall tau
- per-query winner 분포
- model factor가 성능 분산을 얼마나 설명하는지 mixed-effects 분석

### 원 제안 3

> 본 시스템에서 설계한 방법이 더 잘 나왔다.

수정:

> 본 시스템의 DB-aware 구조는 hard constraint, selective predicate, storage/latency/cost trade-off에서 단일 vector-only baseline보다 안정적이다.

이는 strict qrels와 latency/storage 축에서 강하게 보일 가능성이 높다. semantic qrels에서는 vector-only가 이길 수 있으므로, 그 경우를 “soft intent에서는 filtering을 조심해야 한다”는 설계 지침으로 흡수한다.

### 원 제안 4

> 멀티모달 데이터셋 기반 검색은 어떤 방식으로 설계를 해야 효율적인지 가이드 제시.

이것은 본 연구의 결론과 정확히 맞는다. 최종 output은 “모델 순위표”가 아니라 “regime-specific design guide”가 되어야 한다.

---

## 6. 모델 후보 판단

### 이미 로컬에 있거나 현재 연구와 정합적인 모델

| 후보 | 역할 | 상태/비고 |
|---|---|---|
| bge-m3 | text embedding | 현재 main |
| e5-large-v2 | text embedding robustness | 현재 robustness |
| CLIP ViT-B/32 | image-text embedding | 현재 main visual |
| SigLIP base | image-text robustness | 로컬 확보, 과거 ablation 존재 |
| NV-Embed-v2 | text embedding | 로컬 cache 존재 |
| llama-embed-nemotron-8b | text embedding | 로컬 cache 존재 |

### 추가 확보 후보

| 후보 | 역할 | 주의 |
|---|---|---|
| Qwen3-Embedding | text embedding | caption/query text baseline 강화 |
| EmbeddingGemma | text embedding | Gemma 계열로 표현 가능 |
| Qwen3-VL-Embedding | multimodal unified embedding | 가장 직접적인 "통합 멀티모달 임베딩" baseline |

### 권장 최소 세트

마감과 실험 비용을 고려하면 다음이 현실적이다.

1. `bge-m3` — 기존 main.
2. `NV-Embed-v2` 또는 `llama-embed-nemotron-8b` — 강한 LLM-family text embedding.
3. `CLIP` 또는 `SigLIP` — 기존 multimodal visual-text baseline.
4. 가능하면 `Qwen3-VL-Embedding` — 진짜 unified multimodal embedding baseline.

Gemma 계열을 넣고 싶다면 `EmbeddingGemma`를 쓰되, 이는 text-only embedding임을 명확히 써야 한다.

---

## 7. 결과표 설계

### 표 A. 단일 임베딩 모델 의존성

| dataset | embedding model | modality | strict nDCG | semantic nDCG | p50 ms | storage MB |
|---|---|---|---:|---:|---:|---:|
| 522 | bge-m3 | caption-text |  |  |  |  |
| 522 | NV-Embed | caption-text |  |  |  |  |
| 522 | Qwen3-VL | unified V-L |  |  |  |  |
| MEVA | bge-m3 | caption-text |  |  |  |  |
| MEVA | NV-Embed | caption-text |  |  |  |  |
| MEVA | Qwen3-VL | unified V-L |  |  |  |  |

### 표 B. 단일 임베딩 vs DB-aware 구조

| regime | best single-vector | best DB-aware | winner | interpretation |
|---|---:|---:|---|---|
| hard constraint |  |  |  | metadata must be explicit |
| soft intent |  |  |  | filtering may remove semantic positives |
| selective predicate |  |  |  | partial/local index needed |
| caption weak domain |  |  |  | frame-vector can dominate |
| caption aligned domain |  |  |  | clip-caption efficient |

### 표 C. 모델 의존성 진단

| dataset | model pair | Kendall tau@100 | winner agreement | mean delta nDCG | interpretation |
|---|---|---:|---:|---:|---|
| 522 | bge vs NV-Embed |  |  |  |  |
| 522 | CLIP vs Qwen3-VL |  |  |  |  |
| MEVA | bge vs NV-Embed |  |  |  |  |
| MEVA | CLIP vs Qwen3-VL |  |  |  |  |

---

## 8. 논문 프레이밍 문장

권장 문장:

> A natural baseline is to map every multimodal item into a single embedding space and run vector search. We include this baseline explicitly, but show that its ranking quality is highly model-dependent and insufficient for hard sensor/spatiotemporal constraints. This motivates treating multimodal VLM-QA retrieval as a database design problem: evidence units, metadata predicates, filter placement, and index deployment must be designed explicitly rather than hidden inside a single embedding model.

국문 보고용:

> 일반적으로는 영상과 텍스트를 하나의 통합 임베딩 공간에 넣고 벡터 검색을 수행하면 충분하다고 생각할 수 있다. 그러나 본 연구에서는 이 방식의 성능이 사용하는 임베딩 모델에 크게 의존하고, 시간·위치·센서 조건처럼 반드시 만족해야 하는 조건에서는 단일 벡터 검색만으로 충분하지 않음을 비교한다. 따라서 멀티모달 감시 데이터 검색은 단순 vector search 문제가 아니라, 저장 단위·metadata filter·색인 구조·DB 실행 방식을 함께 설계해야 하는 문제로 프레이밍한다.

---

## 9. 위험 요소

1. **Qwen/Llama/Gemma를 같은 성격의 모델로 묶으면 안 된다.**  
   Qwen3-VL-Embedding은 multimodal unified embedding으로 볼 수 있지만, EmbeddingGemma와 llama-embed-nemotron은 text embedding에 가깝다.

2. **"단일 임베딩은 나쁘다"는 주장은 위험하다.**  
   최신 Qwen3-VL-Embedding 같은 모델이 일부 semantic query에서 강할 수 있다. 주장은 "단일 임베딩은 모델 의존적이고 hard metadata constraint에는 불충분하다"로 제한해야 한다.

3. **DB-aware 구조가 모든 지표에서 이긴다고 쓰면 안 된다.**  
   strict에서는 prefilter가 강하지만, semantic에서는 vector-only가 이길 수 있다. 이 차이를 설계 지침으로 해석해야 한다.

4. **모델 비교 논문처럼 보이면 안 된다.**  
   모델 순위표가 목적이 아니다. 모델 의존성을 보여줌으로써 DB 구조 설계의 필요성을 정당화하는 것이 목적이다.

---

## 10. 최종 권고

이 확장은 논문에 넣을 가치가 있다. 단, 위치는 "main contribution"이 아니라 "baseline stress test / model-dependence analysis"가 적절하다.

최종 프레임:

> 단일 통합 임베딩 vector-only 검색은 자연스러운 baseline이지만, 그 성능은 embedding model과 query regime에 민감하다. 본 연구는 이를 실험적으로 보이고, 멀티모달 감시 VLM-QA에서는 metadata predicate, 저장 단위, 색인 배치, partial/local index 같은 DB 설계 요소를 명시적으로 비교해야 함을 보인다.

