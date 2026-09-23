# 저장 × 검색 × 색인 통합 검증 결과

- 실행 완료: 2026-07-17T23:25:43+09:00
- 동결 조건: 3,000 clips, 85 queries, 동일 Qwen3-VL-Embedding-2B 2,048차원 공간
- 구성: 5개 저장 표현, 호환 검색 계획, 7개 색인 설정, 총 112개 구성
- 추론: 질의 bootstrap 10,000회 + intent×facet 25개 군집 bootstrap 10,000회

## 1. 동일 인코더 저장 표현 통제

Flat/B2에서 semantic nDCG@10은 caption 0.1810, 대표 프레임 0.1865,
multi-frame 0.3518, dual 0.2933, joint image-caption 0.2182였다. Multi-frame 대비 caption 차이는
질의 bootstrap +0.1708 [+0.0989, +0.2399], 군집 bootstrap +0.1708 [+0.0178, +0.3162]이다.

Strict nDCG@10에서도 multi-frame은 0.1014였고 caption 대비 차이는
질의 bootstrap +0.0387 [+0.0047, +0.0730], 군집 bootstrap +0.0387 [+0.0037, +0.0762]이다.
따라서 이전 CLIP/BGE 혼합 비교와 달리, 이 데이터에서는 동일 encoder 조건에서도 다중 프레임 저장의
semantic 이점이 관측됐다. 다만 storage family의 BH 보정 후 cluster q-value는 semantic
0.1123, strict 0.0592이므로, 군집 수준 결과를
family-wise 0.05 유의로 과장하지 않는다. 대표 프레임과 caption의 차이는 별도 비교표의 신뢰구간으로 판단한다.


단일 image-caption joint vector의 semantic nDCG@10은 0.2182, strict는
0.0794였다. Caption 대비 semantic 차이는 질의 bootstrap
+0.0372 [+0.0156, +0.0586], 군집 bootstrap +0.0372 [-0.0049, +0.0742]이며, strict 차이는
질의 bootstrap +0.0168 [-0.0014, +0.0364], 군집 bootstrap
+0.0168 [+0.0058, +0.0287]이다. 이 비교는 클립당 하나의 2,048차원 벡터라는 동일
저장 예산에서 수행된 early-fusion 대 caption-only 대조다.


## 2. 검색 계획 효과

Multi-frame/Flat에서 B4 prefilter의 strict nDCG@10은 0.2625로,
B2의 0.1014보다 높았다. 차이는 질의 bootstrap +0.1612 [+0.1289, +0.1952],
군집 bootstrap +0.1612 [+0.1048, +0.2093]이다. 반면 semantic-only 판단에서는 B2가 더 높아,
hard predicate 준수와 장면 의미 검색을 하나의 지표로 합쳐 단일 승자를 선언해서는 안 된다.

## 3. 색인 효과

Strict 품질 최고점은 `multi_frame + B4 + HNSW efSearch=64`의 0.2685였다.
Flat 대비 차이는 질의 bootstrap +0.0060 [-0.0044, +0.0164], 군집 bootstrap
+0.0060 [-0.0062, +0.0191]이며, p95 검색 지연은 1.080 ms,
직렬화 색인 크기는 70.66 MB였다. ANN의 작은 점 추정치 우위는 신뢰구간이
0을 포함하면 품질 향상으로 해석하지 않고 Flat 동등 범위의 근사 오차로 취급한다. 또한 이 구성의
exact-task top-10 fidelity는 0.8706에 불과하다. fidelity>=0.95를
요구하면 HNSW ef256은 0.9694, strict nDCG
0.2615이며, 현재 측정의 최고 strict 품질은 Flat 0.2625였다.

## 4. 결론

단일 전역 최적 조합은 존재하지 않았다. Strict/hard-constraint 목적과 semantic 목적의 승자가 달랐고,
메모리 10 MB 이하에서는 PQ 계열이 선택되지만 exact-ranking fidelity가 크게 낮아졌다. 따라서 본 결과는
`sla_profile_winners.csv`와 `pareto_front.csv`처럼 목적·제약별 선택으로 제시해야 한다.

## 5. 주의

- task-quality 공동 실험의 규모는 동결된 3,000 clips이다.
- 지연 측정은 manifest에 기록된 공유 호스트 부하에서 수행됐다.
- postfilter는 고정 top-200 vector 후보 예산이다.
- 색인 크기는 FAISS 직렬화 크기이며 indexed vector payload를 포함한다.
