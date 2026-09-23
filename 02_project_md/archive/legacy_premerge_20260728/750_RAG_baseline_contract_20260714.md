# 750 — 기본(분리) 방식 = 표준 RAG 확립 + 통합 방식 비교 계약 (2026-07-14)

목적: 통합(joint 임베딩) 방식은 타 전문가가 별도 수행. 우리는 **기본(분리) 방식이 보편적 RAG 표준임을 확립**하고, 이후 통합 방식과 **apples-to-apples 비교할 고정 기준(contract)** 을 못박는다. (외부 근거 조사 wf_88e90ff0 + 내부 하네스 실측)

## A. 기본 방식 = 표준 RAG 인가? → **예 (근거 확인)**

우리 방식 = 문서(VLM 캡션)→텍스트 임베딩(bge-m3)→벡터스토어 + 질의→임베딩→ANN + **센서/시공간 메타데이터=별도 구조화 필터** + 검색증거→고정 VLM.

**1) 표준 RAG 파이프라인 = 우리 구조** (LangChain·LlamaIndex·Haystack·원조 RAG Lewis 2020). 인덱싱(load→split→embed→store) + 질의(embed→ANN top-k→context→LLM). **구조화 조건을 "임베딩과 분리된 메타데이터 필터"로 처리 = 문서화된 표준**이지 커스텀 아님.
**2) 벡터DB 전수 확인**: pgvector·Milvus·Weaviate·Qdrant·Pinecone·Chroma·Elasticsearch **7종 모두 "filtered vector search"(내용=벡터, 메타=별도 필터)를 1급 기능으로 구현**. 메타데이터를 임베딩에 **융합하는 것은 프로덕션 표준이 아니라 신흥/연구**(Cohere Embed4·voyage-multimodal-3 등).
**3) 멀티모달**: caption-as-document는 주류 4계열 중 (a) — (a)caption-then-embed / (b)CLIP-직접 / (c)multi-vector(ColPali) / (d)joint 단일벡터. **(a)는 표준 옵션이나 유일은 아니고 "가장 단순·모듈러하지만 세밀한 시각·카운팅에 약함(lossy)"**.

**⇒ 우리 검색 아키텍처(embed+ANN+분리 메타필터) = 근-보편 RAG 표준 baseline. joint 단일임베딩 = 연구/실험 대안(타 전문가 몫).**

## B. 정직한 뉘앙스 (원고에 명시할 것)
- 아키텍처(분리+필터)는 **표준**이나, **"프레임→캡션→임베딩"(family a) 선택**은 4계열 중 하나 — 가장 단순·모듈러하되 lossy. (우리 실험이 독립적으로 그 lossy를 확인: **캡션 맹점**, MEVA frame-vector 우위). 즉 약점이 아니라 일관된 관측.
- "메타데이터 필터"는 표준이나 pre/post 변이 존재 → "filtered vector search / 메타데이터 필터링"으로 표기(특정 변이를 canonical로 확정 금지).

## C. 통합 방식 비교 계약 (고정 baseline — 이미 완비, 실측 확인)

| 항목 | 고정값 |
|---|---|
| 코퍼스 | 522 tri-source, **3,000 캡션 문서** (`canonical_trisource_expanded/documents.parquet`) |
| 질의 | **85** (`queries.jsonl`; low 75 + contrast 10) |
| 정답 | **이중** strict 6,810 / semantic 24,873 (`qrels.tsv`/`qrels_semantic.tsv`) |
| 지표 | `vlmdb_workload.metrics.evaluate_ranking` → nDCG@10·recall@10·MRR (strict+semantic) |
| **출력 계약** | 질의별 **clip_id 랭킹** = `[query_id, rank, clip_id, score]` (우리 `retrieval_results.parquet` 형식) |
| 현 baseline | B0 metadata-only 0.218 / **B2 vector-only 0.059(=필터없는 순수 dense=통합 직접 대응점)** / B4 prefilter+vector 0.157 / B5 hybrid 0.135 (nDCG@10 strict) |

**비교 방법**: 통합(joint) 방식은 **동일 85질의**에 대해 **위 clip_id 랭킹만** 산출 → **동일 `evaluate_ranking`·동일 이중 qrels**로 채점 → B0/B2/B4와 나란히 비교. 별도 재작업 불필요.

**공정성 주의**: joint 방식이 메타데이터를 벡터에 넣으면 **정확 필터 보장이 사라지고 순환성 위험**이 생기므로, 비교는 (i) **동일 비순환 qrels**로 채점하고 (ii) "정확 필터 보장 여부"를 별도 축으로 병기해야 apples-to-apples가 성립(하드 제약 strict 체제에서 특히).

## D. 상태
- ✅ 기본 방식 = 표준 RAG baseline 확립(외부 근거 + 내부 구조 확인).
- ✅ 비교 계약 고정(코퍼스·질의·이중정답·지표·출력형식·현 baseline 수치).
- 통합 방식은 이 계약에 랭킹을 맞춰 넣기만 하면 즉시 비교 가능.
- (선택) 원고 §2/§10에 A·B 포지셔닝 1문단 추가 시 심사 "왜 joint 아님?" 방어 완결.
