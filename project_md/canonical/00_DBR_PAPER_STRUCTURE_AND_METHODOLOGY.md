# DBR형 논문 구조와 연구 Methodology 정본

- 기준일: 2026-07-18
- 문서 지위: 논문 전체 구조와 방법론의 단일 정본
- 대상 원고: DBR 장문 원고. KDBC 제출본은 이 구조를 2–4쪽으로 축약한다.
- 결과 숫자의 상세 근거: [`experiments/`](experiments/)

---

## 0. 편집 형식의 채택 근거

### 0.1 확인 가능한 관행

- KDBC 2024 정규 논문은 정보과학회 학술대회 양식의 2–4쪽 국·영문 원고를 받았고, Database and Data Engineering 및 Data Intelligence and Science 트랙으로 구분되었다. 따라서 KDBC형 원고는 `서론–관련 연구–방법–실험–결론`을 짧게 압축하는 형식이 적합하다.  
  출처: [KDBC 2024 개최 안내](https://knuds.kangwon.ac.kr/ds/community/notice.do?articleNo=453608&mode=view&title=Korean+DataBase+Conference+2024+%28KDBC+2024%29+%EA%B0%9C%EC%B5%9C)
- 2024–2025년 데이터베이스연구(DBR) 게재 사례는 국·영문 제목·초록·주요어와 번호형 기술 섹션을 사용하는 장문 연구 논문 형식이다. 현재 공식 투고 규정은 A4, Word/HWP, 20쪽 이내, 첫 쪽 저자·소속·교신저자 정보, IEEE 계열 참고문헌 등의 제출 요건을 둔다.  
  출처: [2024년 DBR 게재 사례](https://www.kci.go.kr/kciportal/mobile/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003159989), [2025년 DBR 게재 사례 1](https://www.kci.go.kr/kciportal/mobile/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003240016), [2025년 DBR 게재 사례 2](https://www.kci.go.kr/kciportal/mobile/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003293173), [DBR 투고 규정](https://dbsociety.kr/dbr_submission_guide/), [DBR 보조 규정](https://dbsociety.kr/journal-submission-rules/)
- 2026 KDBC의 별도 공식 author guide는 2026-07-18 현재 이 문서가 독립 확인하지 못했다. 따라서 2024 형식을 2026 규정이라고 단정하지 않고, 실제 공고가 게시되면 분량과 표지 요건만 갱신한다.

### 0.2 본 연구가 채택할 장문 섹션 구조

```text
국문 제목·저자·소속·교신저자
국문 초록·주요어
영문 제목·Abstract·Keywords
1. 서론
2. 관련 연구
3. 문제 정의와 연구 질문
4. 연구 방법론
5. 데이터셋과 실험 환경
6. 실험 결과
7. 논의와 설계 지침
8. 타당성 위협과 한계
9. 결론
참고문헌
```

현재 v6 원고의 `비순환 워크로드 프로토콜`과 `순환성 진단`은 내용상 정확하지만, 논문화 구조에서는 3절 문제 정의와 4절 방법론 아래에 배치하는 편이 독자가 “무엇을 비교하는지–어떻게 타당성을 보장하는지–어떤 결과가 나왔는지”를 더 선명하게 따라갈 수 있다.

### 0.3 KDBC 단편 축약 구조

```text
1. 서론: 문제·공백·기여·RQ를 한 절에 통합
2. 관련 연구 및 문제 정의: 핵심 선행 3갈래와 순환성 정의
3. 제안 방법: tri-source, 이중 정답, 저장×검색×색인 설계공간
4. 실험: 522 주 결과 + 대표 외부 검증 + 한계
5. 결론
```

KDBC 단편에는 모든 ablation 표를 넣지 않는다. 순환성 직접 개입, 112구성 Pareto, real-vs-random predicate, 답변 전파 경계만 대표 결과로 남기고 상세 수치는 DBR 확장본 또는 부록을 가리킨다.

---

## 1. 연구 정체성

### 1.1 연구 대상

대규모 도시 감시 아카이브의 모든 영상을 질의마다 VLM에 입력하는 대신, 데이터베이스가 먼저 소수의 관련 클립·프레임을 검색하여 evidence packet을 만든다고 가정한다. 이 계층을 본 연구에서는 **evidence layer**라 부른다.

여기서 “VLM 앞단”은 사용자가 원본 영상 전체를 VLM에 직접 입력한다는 뜻이 아니다. 사용자의 자연어 질의와 명시적 구조화 조건은 먼저 **질의 서비스와 DB evidence layer**에 입력된다. 질의 서비스는 자연어 의미를 lexical/dense query로 만들고, 시간·카메라·신호 상태와 같은 hard predicate를 구조화 조건으로 유지한다. DB가 두 신호를 이용해 후보를 검색·필터링·정렬한 뒤, 상위 소수의 근거만 최종 VLM에 전달한다. VLM의 역할은 제한된 근거를 읽어 답변·요약·설명을 생성하는 것이다.

```text
오프라인·비동기 물질화
원본 영상 → clip/frame 샘플링 → pixel-only caption과 시각·텍스트·joint embedding
         ↘ sensor·spatiotemporal metadata
         ↘ media URI·timestamp·model/prompt provenance
                                      → 관계형 DB와 벡터 색인

온라인 질의
사용자 자연어 + 명시적 구조화 조건
  → query embedding/lexical query + predicate
  → prefilter·postfilter·vector/lexical retrieval·rank fusion
  → top-k evidence packet
  → 고정 VLM의 답변 생성
```

“전체 코퍼스”는 원본 비디오 자체만을 뜻하지 않는다. 원본은 파일 시스템 또는 객체 저장소에 보존하고, 질의 경로에는 clip/frame ID, 원본 참조, timestamp, sensor metadata, 캡션, 선택한 시각·텍스트·joint 벡터와 모델 provenance를 물질화한다. 본 연구의 RQ2와 RQ5는 이 표현을 모두 항상 저장하라고 요구하는 것이 아니라, 목적과 SLA에 따라 무엇을 물질화하고 색인할지를 선택하는 문제다.

evidence packet은 새로운 학습 데이터셋이 아니라 **한 질의에 대해 최종 VLM이 실제로 읽는 작은 검색 결과 묶음**이다. 최소 스키마는 다음과 같다.

| 필드 | 의미 |
|---|---|
| `query_id`, parsed intent | 원 질의와 semantic intent/hard predicate의 분해 |
| `clip_id`, `frame_id` | 근거의 안정적 식별자 |
| media URI, timestamp | 원본 영상·프레임에 재접근할 포인터와 시간 구간 |
| selected evidence | 캡션, 대표·복수 프레임 또는 짧은 clip |
| metadata facts | 검색에 사용한 외생 센서·시공간 사실 |
| retrieval trace | 검색 계획, 점수, 순위, 색인과 fusion 정보 |
| provenance | 데이터 생산자, 모델·revision·prompt와 변환 이력 |

원본 포인터와 timestamp를 포함하므로 캡션만으로 답할 수 없는 경우 선택 프레임이나 짧은 clip을 다시 확인할 수 있다. 다만 evidence packet의 구성은 검색 결과를 전달하는 인터페이스이며, 그 자체가 최종 답변 정확도를 보장하지 않는다.

### 1.2 핵심 연구 문제

질의 \(q=(q_s,p)\)는 자연어 의미 조건 \(q_s\)와 구조화 predicate \(p\)로 구성된다. 문서 집합 \(D\)에서 증거 표현 \(r\), 검색 계획 \(g\), 물리 색인 \(i\)를 선택할 때 본 연구의 목표는 다음 다목적 문제를 푸는 것이다.

\[
\max_{r,g,i}\; \bigl(Q_{\text{strict}}, Q_{\text{semantic}}, \text{ANN-fidelity}\bigr),
\qquad
\min_{r,g,i}\; \bigl(L_{p50},L_{p95},S,T_{\text{build}}\bigr)
\]

단, 다음 제약을 만족해야 한다.

1. predicate, 검색 문서와 relevance의 생성 계보가 순환하지 않는다.
2. hard constraint와 soft intent를 같은 정답 정의로 혼합하지 않는다.
3. 비호환 조합을 억지로 완전 요인설계에 넣지 않는다.
4. 검색·색인 계층 비용과 VLM 생성 비용을 분리한다.
5. 검색 개선을 최종 답변 개선으로 자동 등치하지 않는다.

따라서 본 연구의 답은 하나의 “최적 모델”이 아니라 사용자 목적과 SLA에 따른 Pareto 설계 규칙이다.

### 1.3 분석 단위

| 층 | 분석 단위 | 종속변수 |
|---|---|---|
| 워크로드 타당성 | 질의, `intent×facet` 군집, 데이터 계보 edge | nDCG 변화, 감사 pass/fail |
| 검색 계획 | 질의×전략 | strict/semantic nDCG@10, MRR, Recall@10 |
| 저장 표현 | clip×표현×질의 | 품질, vector 수, payload, 검색 지연 |
| ANN/DB | query×predicate×index×seed | exact-neighbor recall@10, short result, latency, size, build |
| VLM-QA | 문항×증거 조건×고정 생성기 | 정답 정확도, mediator hit, 시점 선택 효과 |

---

## 2. 문제 정의와 연구 질문

### RQ1. 평가 타당성

필터 predicate, 질의 템플릿, 검색 문서와 relevance가 같은 주석 계보에서 파생될 때 구조 비교가 어떻게 왜곡되는가? 소스 분리, 이중 정답과 기계 감사가 그 구성상 우위를 제거하는가?

### RQ2. 증거 표현

clip-caption, representative-frame, 단일 image+caption joint, multi-frame과 dual-index는 품질·지연·공간 사이에 어떤 절충을 형성하는가?

### RQ3. 메타데이터–벡터 결합 계획

predicate가 hard constraint인지 soft intent인지, 그리고 predicate–relevance 결합도가 어느 정도인지에 따라 vector-only, postfilter와 prefilter의 상대 효과는 어떻게 바뀌는가?

### RQ4. 검색 신호와 문서 물질화

metadata, BM25, dense text, visual, sparse–dense 또는 text–visual 융합 중 어떤 신호가 유효하며 캡션 생성기와 encoder 선택에 얼마나 민감한가?

### RQ5. 물리 색인과 배포

실측 predicate의 선택도와 임베딩 군집성 아래에서 Flat, HNSW, IVF-Flat, IVF-PQ, global, partial/local index 및 관계형·전용 엔진은 recall·latency·space·build를 어떻게 절충하는가?

### RQ6. VLM-QA 전파

검색 품질과 ANN fidelity의 차이는 고정 VLM 답변으로 언제 전파되며, 코퍼스 규모, 생성기의 지각 능력과 질문·답변 편향은 이 전파를 어떻게 제한하는가?

---

## 3. 전체 연구 설계

### 3.1 설계의 흐름

```text
Raw observations
├─ sensor/capture records ───────────────→ predicate P
├─ human CVAT/KPF activity annotation ──→ relevance Y
└─ pixels only ─→ VLM caption / embedding → searched document X
                         │
                         ▼
              canonical workload
       clips / documents / metadata / queries
              strict & semantic qrels
                         │
                         ▼
                  A6 validity gate
                         │ PASS
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
 representation     search plan      physical index
 C/F/J/M/D          B0–B5            Flat/HNSW/IVF/PQ
        └────────────────┼────────────────┘
                         ▼
            retrieval + cost measurement
                         │
                         ▼
              controlled VLM-QA gates
```

### 3.2 순환성의 형식화

문서 \(d\), predicate \(P\), relevance \(R\)와 query \(Q\) 사이에 다음 경로가 있으면 순환성으로 정의한다.

- **C1 — filter–answer circularity**: 정답 집합이 정의상 필터 통과 집합의 부분집합이어서 prefilter 우위가 구성상 보장된다.
- **C2 — document–answer circularity**: 정답을 만든 라벨이 검색 문서에 재진술되어 검색이 영상 의미 이해가 아니라 라벨 조회가 된다.
- **C3 — query/document template circularity**: 질의와 검색 문서가 같은 라벨 템플릿을 공유하여 표면 문자열만으로 정답을 회수한다.

순환성을 “세 채널 사이의 통계적 독립”과 혼동하지 않는다. 세 채널은 같은 실제 교통 장면을 관측하므로 자연 상관이 존재한다. 본 연구가 차단하는 것은 **정답 정보를 predicate나 searchable document로 직접 되먹임하는 계보 경로**다.

### 3.3 tri-source 생성 계보

522 주 워크로드에서는 다음 생산자를 분리한다.

| 역할 | 원천 | 생산자·카메라 | 정답 정보 접근 |
|---|---|---|---|
| predicate | 시간·신호·차량 밀도 센서 CSV | 카메라 10 계열 | 사람 relevance 라벨에 접근하지 않음 |
| relevance | CVAT 궤적·상태 주석 | 카메라 11/22 계열 사람 주석 | 센서 predicate를 정답 의미 정의에 사용하지 않음 |
| document | 중간 프레임의 픽셀-only VLM caption | Qwen2.5-VL 또는 고정 후속 캡셔너 | 센서·CVAT·qrels를 입력하지 않음 |

같은 교차로의 최근접 시각을 ±120초 창으로 조인한다. 조인 성공률은 90.18%, 시간차 중앙값은 0초다. 이는 동일 순간의 다른 뷰라는 근사이지 동일 픽셀 정합이 아니다.

### 3.4 canonical schema

| 테이블 | 주 키 | 필수 내용 |
|---|---|---|
| `clips` | `clip_id` | 데이터셋, 시간, 미디어 참조, provenance |
| `documents` | `document_id`, `clip_id` | 캡션 또는 표현 소스, producer, model/prompt hash |
| `metadata` | `clip_id`, `facet_key` | 센서·시공간 predicate 값과 source |
| `queries` | `query_id` | 자연어 의미 조건, `metadata_filter`, intent, facet, coupling |
| `qrels` | `query_id`, `target_id` | strict relevance |
| `qrels_semantic` | `query_id`, `target_id` | 의미 relevance |

522 정본은 3,000 clips, 3,000 documents, 85 queries, strict qrels 6,809행, semantic qrels 24,872행이다. 85질의는 5개 predicate와 5개 의미 정의의 기계적 교차곱에서 질의당 최소 양성 규칙을 적용해 만들며, 저결합 75개와 자연결합 10개로 구성된다.

### 3.5 이중 정답

의미 사건을 \(Y_s(d)\), predicate 만족을 \(P_f(d)\)라 하면 다음과 같이 정의한다.

\[
R_{\text{semantic}}(q,d)=Y_s(d)
\]

\[
R_{\text{strict}}(q,d)=Y_s(d)\land P_f(d)
\]

- strict는 사용자가 predicate를 반드시 지켜야 하는 **hard constraint** 계약이다.
- semantic은 predicate 밖의 의미 관련 문서도 정답인 **soft intent** 계약이다.

522 semantic 양성의 72.6%가 predicate 밖에 있으므로 prefilter가 semantic 정답을 제거할 가능성이 실재한다. 두 정답을 함께 보고해야 “필터는 항상 좋다”는 해석을 피할 수 있다.

### 3.6 predicate–relevance 결합도

predicate 값과 의미 사건의 모집단 연관을 Cramér's \(V\)로 계산한다. \(V<0.3\)은 저결합, \(V\ge 0.3\)은 자연결합으로 사전 구분한다. \(V\)는 방향 없는 쌍 속성이므로 필터의 효과 부호는 \(\Delta=B4-B2\)에서 읽는다.

질의 85개가 `intent×facet` 25개 쌍에 중첩되므로 다음 두 추론을 함께 보고한다.

1. 질의를 반복 단위로 한 paired query bootstrap
2. 25개 `intent×facet`을 반복 단위로 한 cluster bootstrap

cluster CI가 0을 포함하면 query CI가 양수 또는 음수여도 새 intent/facet 일반화는 탐색적으로 제한한다.

### 3.7 A6 기계 감사

canonical을 검색기에 넘기기 전에 다음을 전부 통과해야 한다.

1. filter key가 센서 predicate whitelist에만 속한다.
2. relevance key가 사람 주석 whitelist에만 속한다.
3. filter key와 relevance key의 교집합이 비어 있다.
4. metadata에 relevance 필드가 없다.
5. searchable document에 정답·facet 토큰 직접 누출이 0건이다.
6. relevance가 사전 정한 희소 밀도 범위에 있다.

감사는 계보 누출 차단을 보증하지만, 동일 장면 상관, 과제 관련 caption prompt, 설계 시점의 임계값 선택까지 보증하지 않는다.

---

## 4. 처리군과 독립변수

### 4.1 문서·증거 표현

최신 동일-encoder 공동 ablation은 Qwen3-VL-Embedding-2B, 2,048차원, L2 정규화를 공통으로 쓴다.

| ID | 표현 | clip당 벡터 | 결합 위치 |
|---|---|---:|---|
| C | 생성 caption | 1 | 단일 텍스트 |
| F | representative frame | 1 | 단일 이미지 |
| J | 같은 clip의 image+caption | 1 | encoder 내부 early fusion |
| JS | image+다른 clip의 caption | 1 | 정합성 음성 대조 |
| M | 최대 3개 frame | ≤3 | 검색 후 clip collapse |
| D | caption lane + multi-frame lane | 1+≤3 | RRF late fusion |

J와 JS는 metadata, relevance, qrels와 정답 렉시콘을 입력하지 않는다. JS는 seed 20260717의 고정점 없는 deterministic derangement다.

### 4.2 검색 계획

| ID | 계획 | 정의 |
|---|---|---|
| B0 | metadata-only | predicate 통과 clip을 의미 점수 없이 반환 |
| B1 | BM25 | 전체 caption에 대한 Okapi BM25 |
| B2 | vector-only | predicate 없이 전체 코퍼스 exact similarity |
| B3 | postfilter | 전역 top-200 인출 후 predicate 적용 |
| B4 | prefilter+vector | predicate 부분집합을 먼저 확정한 뒤 similarity |
| B5 | hybrid | 필터 통과 집합에서 BM25와 dense를 RRF \(k=60\)으로 결합 |

tri-source B0–B5 본 실험은 Qwen2.5-VL caption과 BGE-M3 1,024차원 exact Flat을 사용한다. 최신 표현 ablation은 Qwen3-VL-Embedding-2B 2,048차원에서 B2/B3/B4를 적용한다. 두 실험군은 질문이 다르므로 기준선 수치를 혼합하지 않는다.

### 4.3 물리 색인과 DB 계획

- Exact: Flat inner product
- Graph ANN: HNSW, search strength `ef`
- Partition ANN: IVF-Flat, `nprobe`
- Compressed ANN: IVF-PQ
- 관계형: PostgreSQL 16.14 + pgvector 0.8.4의 global HNSW + `WHERE`, relaxed iterative scan, predicate별 partial index
- 전용 엔진: Milvus와 Weaviate의 native filtered path 및 완화/fallback 체제

filtered-ANN은 exact top-10을 기준으로 recall@10을 계산한다. task qrels가 있는 3,000-clip 격자에서는 task nDCG와 Flat 대비 top-10 fidelity를 함께 계산한다.

### 4.4 실제 predicate와 무작위 대조

선택도 \(s\)가 같아도 실제 위치·시간·센서 predicate는 임베딩 공간에서 군집할 수 있다. 따라서 각 natural predicate에 같은 크기의 random mask를 짝지어 다음을 추정한다.

\[
\Delta_{\text{mask}} =
\text{Recall@10}_{\text{random same-}s}
-
\text{Recall@10}_{\text{real predicate}}
\]

이 값이 양수이면 random-mask 평가가 실측 predicate 성능을 낙관한 것이다. 부분집합 exact/prefilter와 공유 색인 postfilter/selector를 분리해 기전을 판별한다.

### 4.5 캡션 생성기

Qwen2.5-VL, Qwen3-VL, Qwen3.5를 같은 프레임, 프롬프트, greedy decoding, 110-token 상한과 BGE-M3 검색기로 비교한다. 이 실험은 caption generator를 DB의 **offline materialization 변수**로 다루며, 모델의 일반 VQA 능력 비교가 아니다.

---

## 5. 데이터셋과 역할 분리

| 데이터 | 정본 규모 | 역할 | 비순환 수준 |
|---|---:|---|---|
| AI Hub 522 교차로 | 검색 3,000 clips/85 q; ANN 143,830 frames | tri-source 헤드라인, 검색·표현·ANN | 완전 A6의 유일한 주 데이터 |
| 시내도로 CCTV | 132,521×512 real vectors, 1,000 holdout q | real predicate filtered-ANN, index Pareto, pgvector | task qrels 없는 predicate/index 코퍼스 |
| MEVA | 985 clips/193 q | 검색·표현 외부 검증 | 캡처 metadata+사람 activity+VLM document; 별도 물리 센서 없음 |
| MIRIS | PostgreSQL 59,019 frames | partial/local 및 hot/cold 정책 외부 검증 | proxy time segment; 검색 의미 qrels 없음 |
| UCA/UCF-Crime | 6,432 segments/135 q | 영어 이상행동 검색 외부 검증 | 센서 없는 2.5-channel |
| VRU-Accident | 1,000 docs/85 q, QA 600문항 | 순환성 수리 사례, 증거 사다리 | 완전 tri-source 아님 |
| 지능형 관제 CCTV | 269 docs/18 q | 순환성 수리 이식 | label/caption 계보 잔여 |
| 다각도 CCTV | 400-event answer sample | 시점 선택 | 검색 tri-source 아님 |

CityFlow-NL과 AI Hub 이상행동 CCTV는 구축 산출물이 있으나 현재 결과에서 사용하지 않으므로 논문 데이터셋 수에 포함하지 않는다.

---

## 6. 실행 절차

### 6.1 원천에서 canonical까지

1. 원본 영상·프레임, 센서 CSV와 사람 주석을 변경 없이 보존한다.
2. 센서·capture metadata를 predicate facet으로 파싱한다.
3. 사람 주석에서 의미 사건을 도출하되 predicate를 정답 의미 정의에 넣지 않는다.
4. 센서·주석을 보지 못한 captioner에 대표 프레임만 입력해 검색 문서를 만든다.
5. `clips/documents/metadata/queries/qrels`로 canonical을 조립한다.
6. A6가 실패하면 downstream 검색·색인 실험을 중단한다.
7. 데이터, 모델, prompt, seed, 입력 순서와 hash를 manifest에 고정한다.

### 6.2 임베딩과 저장

1. 질의 벡터는 처리군 사이에 공유한다.
2. 동일-encoder ablation에서는 C/F/J/M/D를 모두 Qwen3-VL-Embedding-2B 2,048차원으로 만든다.
3. J는 이미지와 같은 clip의 Qwen3.5 caption을 한 입력으로 넣는다.
4. 벡터는 float32로 저장하고 finite·shape·L2 norm·clip order를 검사한다.
5. multi-frame은 검색 후 clip별 최고 점수로 collapse하고, dual은 caption lane과 visual lane의 RRF를 포함한다.
6. vector payload와 serialized index 크기를 분리 기록한다.

### 6.3 검색·색인 실행

1. Flat exact를 표현 품질의 anchor로 실행한다.
2. B2/B3/B4를 strict와 semantic 양쪽으로 채점한다.
3. 호환 가능한 표현×계획×색인만 실행한다. 예를 들어 frame-only에 BM25를 붙이지 않는다.
4. 최신 격자는 112개 구성, 19,040 metric cells, 95,200 latency trials이다.
5. ANN은 Flat top-10 fidelity와 task score를 함께 기록한다.
6. 실제 predicate와 동일선택도 random mask를 같은 query/predicate 쌍에서 비교한다.
7. pgvector는 global off, relaxed iterative scan과 partial index를 분리한다.

### 6.4 VLM-QA 전파

1. 생성 모델·prompt·decoding을 고정하고 evidence condition만 바꾼다.
2. closed, distractor, dense, prefilter, oracle의 증거 사다리를 실행한다.
3. ANN 파라미터가 mediator인 증거 회수율을 실제로 바꾸는지 먼저 검사한다.
4. mediator 조작이 실패하면 본 VLM 실험을 시작하지 않는다.
5. 조작이 성공해도 VLM의 hit-vs-miss 지렛대가 없으면 중단한다.
6. 다중 시점에서는 사건을 고정하고 better/worse/random view만 바꾼다.

---

## 7. 평가 지표와 통계

### 7.1 품질

- 관련도 검색: nDCG@10, MRR, Recall@10, Hit@10
- ANN: exact-neighbor Recall@10, Flat 대비 task top-10 fidelity
- 답변: 다지선다/이진 정확도, evidence-hit 조건부 정확도, paired disagreement

### 7.2 시스템

- 검색 지연: p50, p95
- 저장: raw vector payload와 serialized index MB
- 구축: materialization time, index build time
- DB: short-result rate, predicate selectivity, scan mode

### 7.3 계측 경계

- 단일 스레드, 워밍업 후 반복 실행을 원칙으로 한다.
- 격리 지연 실험은 질의별 15회 중앙값을 사용한다. 공동 112구성 validation은 저장된 95,200 trials의 정의를 따른다.
- embedding 생성, 원본 evidence fetch와 VLM 생성은 검색 지연에서 제외한다.
- in-process FAISS와 client/server PostgreSQL의 절대 latency를 같은 숫자축에서 우열로 해석하지 않는다.

### 7.4 불확실성

- paired query bootstrap: 동일 질의의 처리군 차이
- `intent×facet` cluster bootstrap: 새 질의군 일반화
- predicate/facet family bootstrap: real-vs-random filtered-ANN
- Holm: 사전등록된 소수 확증 가족
- Benjamini–Hochberg: 저장 표현 등 다중 사후 대조
- seed robustness: ANN 색인을 seed마다 실제 재구축

효과크기, 95% CI, 반복 단위 수와 보정 후 q/p를 함께 보고한다. CI가 0을 포함하는 대조는 “차이가 없다”고 확정하지 않고 “검출되지 않았다”로 쓴다.

---

## 8. 무결성·재현 체계

### 8.1 공통 gate

- 입력 행 수, ID 유일성, join coverage
- vector shape, dtype, finite, L2 norm, clip order
- query/qrel hash와 treatment 사이 불변성
- filtered ranking의 predicate 위반 0건
- strict qrels가 semantic qrels와 predicate의 교집합인지 재계산
- raw ranking에서 metric 독립 재계산
- configuration/metric/latency cell 완전성
- seed와 model/prompt/input/output hash 저장

### 8.2 현재 통과한 검증

| 검증 | 상태 | 보증 범위 |
|---|---:|---|
| 전체 검증 suite | 40/40 PASS | 데이터·워크로드·환경·구형 원고 수치 |
| 최신 joint 검증 | 17/17 PASS | 단일 image+caption 처리, 112구성, qrel logic |
| ablation treatment/statistics | 12/12 PASS | 91구성 선행 격자의 treatment와 통계 |
| BGE 순환성 검증 | 12/12 PASS | BGE C1/C2 재계산 |
| Qwen 순환성 검증 | 10/10 PASS | 동일-Qwen treatment·ranking·bootstrap |
| 고정밀 ANN 5-seed | 8/8 PASS | 30 cells, monotonic recall, threshold |
| 독립 비판 감사 | 두 감사 모두 PASS_WITH_LIMITATIONS | 치명 오류 없음, 주장 강도 제한 |

검증 pass는 파일과 계산의 무결성을 보증할 뿐, 모든 데이터로의 보편성을 보증하지 않는다.

### 8.3 reproducibility contract

공개 패키지는 다음을 포함해야 한다.

- canonical workload와 qrel 정의
- predicate registry와 A6/A9 감사
- model snapshot, prompt, seed, hash manifest
- 사전등록과 amendment의 시간 순서
- raw per-query ranking/metric
- 결과 CSV와 그림 생성 코드
- 환경 manifest
- 중단된 실험과 음성 결과

원천 영상은 각 라이선스를 따르며 배포할 수 없는 경우 ID 목록, 파생 manifest와 재생성 스크립트를 제공한다.

---

## 9. 실험과 논문 섹션의 일대일 배치

| 논문 절 | 핵심 내용 | 정본 실험 문서 |
|---|---|---|
| 1 서론 | 문제, 순환성 함정, evidence-layer 공백, 기여 | 본 문서 §1–2 |
| 2 관련 연구 | filtered vector, multimodal RAG, VALU, benchmark validity, video DB | 본 문서 §10 |
| 3 문제 정의 | C1–C3, 목적함수, RQ1–RQ6 | 본 문서 §1–3 |
| 4 방법론 | tri-source, 이중 qrels, 설계 변수, 통계·gate | 본 문서 §3–8 |
| 5 데이터·환경 | 8개 실사용 역할, 모델·엔진·HW | 본 문서 §5 및 각 실험 문서 |
| 6.1 타당성 결과 | 수리 붕괴, C1/C2 통제 주입 | EXP01 |
| 6.2 검색 결과 | B0–B5, 결합도, UCA 이식 | EXP02 |
| 6.3 ANN/DB 결과 | real-vs-random, 엔진, index, partial/hot-cold | EXP03 |
| 6.4 표현 결과 | caption/frame/joint/multi/dual, captioner | EXP04 |
| 6.5 답변 결과 | 사다리, 시점, 세 전파 경계 | EXP05 |
| 6.6 외부·강건성 | MEVA, MIRIS, scale/seed, 감사 | EXP06 |
| 7 논의 | 목적·SLA별 Pareto 규칙 | 본 문서 §11 |
| 8 한계 | 구성·내적·외적·통계적 타당성 | 본 문서 §12 |
| 9 결론 | 질문별 답과 적용 범위 | 본 문서 §13 |

---

## 10. Related Work 집필 계약

관련 연구는 논문 목록을 나열하지 않고, 각 갈래가 본 연구의 어떤 축을 다루지 않았는지를 비교한다.

### 10.1 Filtered vector search와 vector index

- 다룰 것: prefilter, postfilter, selector/single-stage, HNSW/IVF/PQ, pgvector iterative scan, filtered graph.
- 공백: random mask 중심 평가가 실제 시공간 predicate의 군집 구조를 대표하는지 검증이 부족하다.
- 본 연구의 위치: 같은 선택도의 real-vs-random 짝 대조와 관계형·전용 엔진 교차 확인.

### 10.2 Multimodal/video retrieval와 RAG

- 다룰 것: CLIP 계열, video retrieval, multimodal RAG, evidence retrieval.
- 공백: 모델 품질 연구와 달리 storage unit×search plan×physical index×SLA를 한 설계공간에서 다루지 않는다.
- 본 연구의 위치: encoder를 고정하고 구조를 변화시킨다.

### 10.3 Surveillance video-language understanding

- 다룰 것: UCA/VALU, ForeSea, UrBench 등 감시 영상 이해·검색.
- 공백: 이들은 주로 어떤 모델이 이해하는지를 평가하며, 센서 predicate와 코퍼스 수준 물리 색인의 공동 문제는 핵심 대상이 아니다.
- 본 연구의 위치: 고정 VLM에 어떤 DB evidence가 전달되는지를 평가한다.

### 10.4 Benchmark validity와 contamination

- 다룰 것: annotation artifacts, train-test contamination, incomplete judgments.
- 공백: 필터 predicate·qrels·검색 문서 사이의 workload-internal circularity가 구조 비교 자체를 보장하는 문제.
- 본 연구의 위치: C1–C3 형식화, source separation, 직접 개입.

### 10.5 Video database와 integrated design space

- 다룰 것: video query acceleration, frame selection, scene graph/event query.
- 공백: 자연어+센서 predicate의 evidence representation, filtered ANN, DB 배포와 VLM-QA 전파를 동일 타당성 계약 아래 비교하는 연구가 부족하다.

Related Work의 마지막 문단은 다음 문장으로 닫는다.

> 기존 연구는 모델 이해, 비디오 질의 가속 또는 필터드 벡터 탐색의 개별 축을 진전시켰다. 본 연구는 이들을 대체하는 새 모델을 제안하지 않는다. 대신 고정된 모델 앞단의 evidence layer를 저장 표현–검색 계획–물리 색인의 공동 설계공간으로 만들고, 그 비교가 정답 계보에 의해 미리 결정되지 않았음을 기계적으로 감사한다.

---

## 11. 결과를 통합하는 설계 지침

| 운영 조건 | 우선 검토할 설계 | 근거의 지위 |
|---|---|---|
| predicate가 반드시 지켜져야 함 | prefilter 또는 predicate별 local index | strict에서 확증 |
| predicate가 soft intent이고 relevance와 저결합 | vector-only와 semantic 손실을 먼저 비교 | 탐색적 |
| caption이 질의 의미를 잘 포착 | 단일 caption 또는 joint로 비용 절감 | 데이터 의존 |
| 세밀한 시각 사건이 caption에서 누락·혼동 | multi-frame 또는 dual | 522에서 강한 점추정; 외부 일반화 제한 |
| 단일 벡터 예산 | joint를 caption/frame과 함께 Pareto 후보로 포함 | 점추정 우위, 군집 일반화 미확증 |
| 선택적·반복적인 real predicate | partial/local HNSW | 두 DB 코퍼스 실측 |
| 넓고 드문 predicate | global+postfilter/relaxed scan | 손익분기 규칙 |
| 메모리가 극단적으로 제한 | IVF-PQ를 고려하되 fidelity 손실 명시 | 품질 희생 |
| 검색 개선을 답변 개선으로 주장 | mediator·perception·task-bias 세 gate 통과 후에만 | 현재는 자동 전파 부정 |

본 연구는 “보편적으로 최적인 한 구성”을 제시하지 않는다. 사용자는 strict/semantic 목적, 허용 p95, 메모리, 구축 상각 가능 질의량을 선언한 뒤 Pareto 전선에서 선택해야 한다.

---

## 12. 타당성 위협과 한계

### 12.1 구성 타당성

- caption prompt가 과제 관련 범주의 서술을 요청하므로 task-aware prompt 결합이 남는다.
- cam10 센서와 cam11/22 주석은 producer가 분리되지만 같은 순간의 다른 뷰라 자연 상관이 있다.
- semantic qrels가 실제 사용자 relevance의 전 범위를 완전히 대표한다고 보장하지 않는다.

### 12.2 내적 타당성

- 초기 설계 과정의 정답 밀도 창, SESOI와 수리 대상 선택은 완전히 사전등록된 holdout 연구가 아니다.
- 최신 joint arm은 결과 전 amendment였지만, 기존 네 표현의 우선 대조 일부는 결과 후 정리했다.
- VRU·지능형 CCTV의 수리 전후 비교는 여러 요소가 함께 바뀌므로 하락분 전체를 순환성에 귀속할 수 없다.

### 12.3 외적 타당성

- 완전 센서 tri-source는 522 한 종이다.
- UCA는 2.5-channel, MEVA는 capture metadata를 사용하고 MIRIS는 proxy 시간 구간을 사용한다.
- 동일-encoder multi-frame 주효과는 독립 외부 task qrels에서 아직 재현되지 않았다.
- 143,830-vector 확장은 exact fidelity를 평가하며 대규모 task relevance qrels가 없다.
- 단일 호스트, 주간·평일, 고정 해상도와 제한된 model family다.

### 12.4 통계적 결론 타당성

- 결합도 \(V\)는 25쌍의 군집 속성이며 자연결합은 2쌍뿐이다.
- storage family의 cluster BH가 0.05를 넘는 비교를 보편 법칙으로 부르지 않는다.
- matched–shuffled joint CI가 0을 포함하므로 정확한 정렬의 인과 효과는 입증되지 않았다.
- VLM 전파 파일럿의 CI가 넓어 “효과가 정확히 0”이 아니라 “본 실험을 정당화할 지렛대를 검출하지 못함”으로 쓴다.

### 12.5 시스템 범위

- 24시간 stream insert/update/delete, online re-captioning과 재색인 비용은 측정하지 않았다.
- 캡션 생성 비용은 offline materialization으로 기록하지만 검색 latency에 합치지 않는다.
- shared-host single-thread latency는 상대 비교용이며 운영 클러스터의 절대 SLA 보장이 아니다.

본 연구가 직접 측정한 운영 근거는 표현별 벡터 수·payload, materialization 시간, serialized index 크기·구축 시간, 검색 p50/p95, 부분 색인의 상각 손익분기다. Motion/object/event gate로 일부 프레임만 비동기 캡셔닝하는 tiered ingestion, delta index merge, retention 기반 hot/warm/cold 저장은 합리적인 이식안이지만 본 연구가 검증한 결과로 표현하지 않는다.

24시간 현장 운용을 별도로 검증하려면 stream arrival rate, decode FPS, sampled-frame rate, caption GPU-seconds/hour, embedding throughput, insert/update amplification, index merge·삭제 비용, staleness와 end-to-end p95를 함께 측정해야 한다. 따라서 현재 원고에서는 “24시간 운영 가능성을 증명했다”거나 “전체 실시간 임베딩 비용을 해결했다”고 쓰지 않는다.

---

## 13. 결론 집필용 정본

### 13.1 질문별 답

- **RQ1:** 순환 경로 하나만 주입해도 nDCG가 크게 상승하므로 구조 비교 전에 계보 감사가 필요하다. tri-source와 A6는 label/source leakage 경로를 차단하지만 자연 상관까지 제거하지는 않는다.
- **RQ2:** 단일 전역 저장 우승자는 없다. joint는 단일벡터 중간 운용점이고 multi-frame은 522에서 품질이 높지만 더 많은 공간·지연을 쓴다.
- **RQ3:** hard constraint에서는 prefilter가 유리하고 soft intent에서는 손실이 가능하다. 효과는 결합도와 질의 믹스에 의존한다.
- **RQ4:** caption과 융합의 가치는 생성기·도메인에 민감하다. sparse 신호는 라벨 재진술을 제거하면 약해질 수 있다.
- **RQ5:** real predicate는 random mask보다 공유 ANN을 더 어렵게 만들며, 선택적·hot predicate에는 local/partial index가 안정적이다.
- **RQ6:** 좋은 evidence는 답변을 개선하지만 ANN 차이가 답변으로 전파되려면 mediator, perception과 task-bias gate를 모두 넘어야 한다.

### 13.2 논문 결론 문장

> 도시 감시 멀티모달 데이터베이스의 evidence layer는 임베딩 모델 하나로 환원되지 않는다. 정답 정보가 predicate와 검색 문서로 되먹임되지 않는 워크로드를 먼저 확립한 뒤, 증거 표현·필터 결합·물리 색인을 strict/semantic 목적과 지연·공간·구축비의 공동 축에서 선택해야 한다. 본 연구의 실측은 한 전역 최적보다 목적·SLA별 Pareto 설계를 지지하며, 검색 개선을 최종 VLM 답변 개선으로 확대하려면 별도의 전파 검증이 필요함을 보여준다.

---

## 14. 원고 작성 시 금지 문장

다음 표현은 현재 증거 범위를 넘으므로 사용하지 않는다.

- “본 방법은 보편적으로 최적이다.”
- “외부 데이터에서도 모든 효과가 증명되었다.”
- “대규모 task quality가 보장된다.”
- “joint의 이득은 올바른 image-caption 정렬 때문임을 입증했다.”
- “multi-frame이 모든 데이터에서 caption보다 우수하다.”
- “ANN recall 개선이 VLM 답변 정확도를 보장한다.”
- “A6가 세 채널의 통계적 독립을 증명한다.”
- “수리 전후의 하락분 전체가 순환성 때문이다.”
- “91/112개 격자는 완전 요인설계다.”
- “검증 pass가 외적 타당성을 보증한다.”
