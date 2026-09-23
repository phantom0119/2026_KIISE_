# 710 — DB 기여 강화 실험 우선순위 (PI 피드백, 2026-07-13)

상태: **LOCKED 지시.** 논문 결론을 "정말 강하게" 만들기 위한 추가 실험 우선순위. 새 데이터셋·새 모델보다 **저장 단위 + partial/local index 실험**이 게재 가능성·DB 기여도를 가장 크게 올린다는 PI 판단. MEVA 실험은 이 과정에 자연 통합(저장단위·partial-index를 522와 MEVA 양쪽에서).

## 우선순위 (PI)
1. **저장 단위 비교 (1순위, 최고 ROI)** — `clip-caption` vs `frame-vector` vs `multi-vector` vs `dual-index`. 저장 단위가 정확도·지연·저장공간에 미치는 영향.
2. **pgvector partial / partitioned index (2순위)** — `global index + WHERE(postfilter)` vs `partial/local index`(predicate별). recall·지연·build·storage 비교.
3. **hot/cold predicate 운영 정책 (3순위)** — 언제 local index를 만들고 언제 global+postfilter를 쓸지 **손익분기(break-even)** 제시(선택도 × 질의빈도 × build 상각).
4. **외적 타당성 데이터셋 (4순위)** — 시간 있으면 MEVA, 아니면 현행 유지. → **이미 MEVA tri-source 구축·A6 PASS 완료(700)**, 1·2순위 실험에 MEVA를 제2 데이터셋으로 포함.
5. **추가 모델 (5순위, 필수 아님)** — reranker upper bound 정도만 선택.

## 강화된 기여 문장 (반영 목표, 원고 §Contribution)
> 본 연구는 멀티모달 감시 데이터의 검색 정확도만 비교한 것이 아니라, **저장 단위, 색인 구성, 필터 결합 방식, 관계형 DB 구현 방식**이 **정확도·지연·저장공간**에 미치는 영향을 함께 분석하였다. 특히 **클립 단위 저장, 프레임 단위 저장, 다중 벡터 저장**의 차이를 비교하고, 실제 센서·시공간 predicate에서 **global index, postfilter, local/partial index**의 성능 차이를 측정함으로써 **VLM-QA evidence layer의 데이터베이스 설계 지침**을 제시한다.

## 통합 원칙
- 저장단위(1)·partial-index(2)는 **522(sinnaedoro/tri-source) + MEVA** 양쪽에서 측정 → MEVA가 외적타당성(4)을 자연 충족.
- 색인구조 3축(Flat/IVF/HNSW/PQ, 기존 600/620)은 재사용; 신규 축 = 저장단위 + partial/local + hot/cold 정책.
- 정직성 규칙(600/620 계승): latency는 격리·상대비교만, FAISS↔pgvector 절대비교 금지, real predicate 상관붕괴 caveat, 1M synthetic 라벨분리.

## 실행 계획 (recon 후 확정 — 아래 채움)
- P1 저장단위: 522/MEVA에서 clip-caption(현) / frame-vector(CLIP frame) / multi-vector(clip=K frames, max-sim) / dual-index(text+visual RRF) → nDCG·latency·index MB·recall@10, 동일 질의·qrels.
- P2 partial-index: pgvector global HNSW+WHERE vs 실 predicate별 partial index(`CREATE INDEX ... WHERE`) → recall·p50/p95·build·size, selectivity sweep.
- P3 hot/cold 정책: build 상각 모델 — local index 손익분기 질의수 N*(s, build_cost, per-query 이득). 도표.
