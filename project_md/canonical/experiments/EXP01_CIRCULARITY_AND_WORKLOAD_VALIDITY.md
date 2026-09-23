# EXP01 — 순환성 통제와 워크로드 타당성

- 대응 질문: RQ1
- 상태: 완료
- 핵심 데이터: 522 3,000 clips/85 queries, VRU 1,000 clips, 지능형 CCTV 269 clips
- 결과 지위: 수리 전후 비교는 진단 사례, 통제 주입은 post-pilot 확립 관찰, A6는 기계 검증

## 1. 목적

초기 완벽 지표가 검색 구조의 우수성인지, 아니면 filter·document·qrels의 생성 계보가 만든 순환성인지 분리한다. 이를 위해 세 단계로 실험한다.

1. 초기 VRU·지능형 CCTV 워크로드의 코드 수준 순환 경로를 진단한다.
2. label-restating document와 answer-derived facet을 제거한 뒤 성능 붕괴를 확인한다.
3. 522에서 데이터·질의·정답·encoder를 고정하고 C1 또는 C2만 인위적으로 주입해 직접 효과를 추정한다.

## 2. 가설과 estimand

### H1 — C1 filter–answer circularity

정답 집합 자체를 후보 필터로 사용하면 clean vector-only보다 semantic nDCG@10이 상승한다.

\[
\Delta_{C1} =
\operatorname{nDCG@10}(\text{qrel-oracle filter})
-
\operatorname{nDCG@10}(\text{clean B2})
\]

동일 선택률 random mask는 단순 후보 축소 효과의 대조군이다.

### H2 — C2 document–answer circularity

정답 의미 라벨을 검색 문서에 재진술하면 clean document보다 semantic nDCG@10이 상승한다.

\[
\Delta_{C2} =
\operatorname{nDCG@10}(\text{label-restating document})
-
\operatorname{nDCG@10}(\text{clean document})
\]

### H3 — source-separated workload

522 tri-source canonical의 predicate, relevance와 searchable document 사이에 직접 label/source leakage edge가 없어야 한다.

## 3. 처리군

### 3.1 수리 전후 진단

| 조건 | filter | relevance | document |
|---|---|---|---|
| v1 순환 | VQA/사건 라벨에서 역파싱한 facet | 같은 VQA/사건 라벨 | 같은 라벨을 재진술한 facet statement 포함 |
| 수리 | 운영 facet 또는 의미와 분리된 조건 | 독립 의미축 | dense caption-only; label-restating statement 제거 |

이 비교는 filter·qrels·document를 동시에 수리하므로 인과 효과의 단일 추정이 아니다. “실제 개발 과정에서 오염을 제거하자 완벽 지표가 붕괴했다”는 진단 사례로만 쓴다.

### 3.2 C1 통제 주입

- clean: 전 코퍼스 B2 vector-only
- random: 각 질의 qrel-oracle 후보 수와 같은 크기의 무작위 후보 집합
- treatment: semantic qrel 집합 자체를 후보 집합으로 사용한 oracle filter

oracle의 nDCG=1은 모델 성능이 아니라 구성상 상한이다.

### 3.3 C2 통제 주입

- clean: 원래 픽셀-only caption
- treatment: 각 양성 문서에 해당 relevance definition을 자연어 문장으로 추가
- BGE 원 실험: BM25와 BGE-M3 양쪽을 평가
- 강건성: BM25 label-edge 오염률 0/25/50/75/100%
- Qwen 반복: Qwen3-VL-Embedding-2B 공간에서 clean/full/query를 한 session에서 재임베딩

부분 오염은 한 반복 안에서 중첩되게 표집한다. BM25 IDF와 길이 정규화 때문에 오염률에 대한 단조성은 검정하지 않는다.

## 4. 고정 조건

- 522 corpus membership: 3,000 clips
- queries: 85
- strict qrels: 6,809 data rows
- semantic qrels: 24,872 data rows
- metric, top-k와 tie-break
- C1에서는 document/query vector
- C2에서는 corpus membership, query, qrel, encoder configuration
- random seed와 bootstrap seed

BGE 실험과 Qwen 반복은 각각 내부 조건이 고정된 별도 replication이다. 두 clean score를 직접 차분하지 않는다.

## 5. 실행 절차

1. canonical ID·query·qrel hash를 manifest에 기록한다.
2. clean B2 또는 clean BM25 ranking을 재생성한다.
3. C1은 질의별 semantic qrel 수에 맞춘 random mask 1,000회와 qrel-oracle mask를 생성한다.
4. C2는 정답 label-edge를 문서에 추가하고 clean/full을 재임베딩 또는 재색인한다.
5. 질의별 raw ranking과 per-query metric을 저장한다.
6. paired query bootstrap 10,000회와 25개 `intent×facet` cluster bootstrap 10,000회를 실행한다.
7. 별도 verifier가 treatment 문장, embedding, ranking, metric, CI와 clean anchor를 재계산한다.

## 6. A6 gate

522 canonical은 다음 6개 assertion을 모두 통과해야 한다.

| assertion | 판정 |
|---|---:|
| filter keys가 센서 predicate whitelist | PASS |
| relevance keys가 사람 주석 whitelist | PASS |
| filter–relevance key disjoint | PASS |
| metadata에 relevance field 없음 | PASS |
| document label/facet token 직접 누출 0 | PASS |
| relevance density 희소성 | PASS |

A6가 보증하는 것은 직접적인 label/source leakage 차단이다. 같은 장면의 자연 상관과 task-aware caption prompt는 잔여 한계다.

## 7. 결과

### 7.1 수리 전후 붕괴

| 워크로드·전략 | v1 순환 | 수리 후 strict | 수리 후 semantic |
|---|---:|---:|---:|
| VRU B4 | 0.9736 | 0.3174 | 0.2974 |
| VRU B2 | 0.4476 | 0.1845 | 0.2649 |
| VRU BM25 | 0.4495 | 0.0918 | 0.1607 |
| 지능형 CCTV BM25 | 0.9600 | 0.1111 | 0.1667 |
| 지능형 CCTV B4 | 1.0000 | 0.8395 | 0.8395 |

VRU semantic의 B4−B2 부호는 음수 18/동률 34/양수 33으로, prefilter 우위의 구성상 보장이 해제되었다.

### 7.2 BGE-M3 통제 주입

| 실험 | clean | treatment | treatment score | Δ | query 95% CI | cluster 95% CI |
|---|---:|---|---:|---:|---:|---:|
| C1 BGE semantic | 0.170033 | qrel-oracle filter | 1.000000 | +0.829967 | [+0.792333,+0.866565] | [+0.747695,+0.912452] |
| C2 BGE semantic | 0.170033 | full label restatement | 0.801141 | +0.631108 | [+0.580243,+0.680292] | [+0.535840,+0.718070] |
| C2 BM25 semantic | 0.050068 | full label restatement | 0.745794 | +0.695726 | [+0.640215,+0.749209] | [+0.593401,+0.790481] |

C1 동일선택률 random filter 1,000회의 평균은 0.106752, replicate 95% 범위는 [0.085628,0.129290]이다.

BM25 부분 오염 평균은 25% 0.812707, 50% 0.804326, 75% 0.774791이다. 25%가 100%보다 높은 것은 IDF·문서길이 효과가 개입한 강건성 결과이며 단조 용량반응으로 해석하지 않는다.

### 7.3 주 격자 정렬 Qwen 반복

| 실험 | clean semantic | treatment | treatment score | Δ | query 95% CI | cluster 95% CI |
|---|---:|---|---:|---:|---:|---:|
| C1 Qwen | 0.181005 | qrel-oracle filter | 1.000000 | +0.818995 | [+0.780200,+0.855287] | [+0.737950,+0.881682] |
| C2 Qwen | 0.181005 | full label restatement | 0.853687 | +0.672682 | [+0.626129,+0.718190] | [+0.567532,+0.752005] |

Qwen C1 동일선택률 random filter 평균은 0.120041이다. verifier는 입력 hash, 1,367 label-edges, token truncation 0건, embedding/ranking/metric/bootstrap/anchor를 10/10 통과했다.

## 8. 결과 지위와 허용 주장

### 허용

- 순환 경로 하나만 추가해도 동일 workload의 측정치가 크게 상승할 수 있다.
- C1은 정답을 후보 집합으로 쓰면 평가가 구성상 포화됨을 정량화한다.
- C2 효과는 lexical BM25와 dense BGE, 주 Qwen 공간에서 모두 관측됐다.
- 구조 비교 전에 source lineage와 searchable document를 감사해야 한다.

### 금지

- 수리 전후 성능 하락분 전체가 순환성 때문이라고 귀속하지 않는다.
- oracle=1을 검색 방법의 성능이라고 부르지 않는다.
- post-pilot 통제 주입을 사전등록 확증 실험이라고 부르지 않는다.
- A6가 채널의 통계적 독립을 증명한다고 쓰지 않는다.
- 부분 오염 결과에 단조성을 주장하지 않는다.

## 9. 원자산

- 수리 붕괴: `2026_KIISE/paper_assets/20260710_noncircular_collapse/`
- BGE/BM25 C1·C2: `2026_KIISE/paper_assets/20260716_circularity_controlled_injection/`
- Qwen 반복: `2026_KIISE/paper_assets/20260717_ablation_agent_crosscheck/qwen_aligned_circularity/`
- A6 정본: `Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded/A6_trisource_audit.json`
- 실행기: `2026_KIISE/scripts/run_circularity_controlled_injection.py`
- Qwen 실행기: `2026_KIISE/scripts/run_qwen_aligned_circularity_control.py`
- 검증기: `2026_KIISE/scripts/verify_circularity_controlled_injection.py`, `verify_qwen_aligned_circularity.py`

## 10. 변경 시 재실행 조건

다음 중 하나라도 바뀌면 EXP01 전체 또는 해당 encoder replication을 다시 실행한다.

- query/qrel 정의
- label-restatement 문장
- document truncation 길이
- encoder snapshot·instruction·normalization
- random mask 생성 규칙
- tie-break 또는 nDCG 구현
- cluster 정의
