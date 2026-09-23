# P9 entity-KG 붕괴 영수증 (2026-07-13, 420 Amendment 9 판정)

상태: **COLLAPSE_CONFIRMED (명세대로의 naive 설계, 세 게이트 전부).** 컴퓨트 전 3-렌즈 적대검토(wf_b364e1b8-b13, 17 에이전트, BLOCKER 3 생존)가 죽인 H-KG "KG 우위" 가지를 저비용 CPU 측정으로 실측 영수증화. GPU 불필요. PI 결정 = **A(정직 경계로 확정)**.

산출물: `collapse_receipt.json`, `collapse_receipt_perquery.csv`(85q), `collapse_receipt_entities.csv`. 스크립트 `scripts/kg_collapse_receipt.py` (kiise-vlmdb env, 동결 규칙).

## 한 줄 결론
> entity-KG(clip↔센서-facet↔캡션-엔티티)는 **B0/B4(센서) ∪ B1/B2(캡션)의 재조합**이며, tri-source의 3채널 중 주석 채널을 A6-KG가 배제하므로 **제3 신호 채널이 구조적으로 없다**. predicate측은 정의상 B4와 동일, 캡션측은 과잉언급+부정으로 바닥. 따라서 "합성 다중-홉에서 KG 우위"는 null-by-construction — CC-FR(Amd.7)·P8(Amd.8)과 동일 붕괴류.

## 세 게이트 (전부 실측 확증)

| 게이트 | 판정 | 근거 |
|---|---|---|
| **G-i** KG predicate 순회 ≡ B4 prefilter 집합 | ✅ TRUE | 85 질의 전부 집합-동일(같은 센서 facet에 대한 교차) → strict에서 KG=B4 정의상 |
| **G-ii** 캡션-엔티티 채널이 명세대로(naive) 죽음 | ✅ TRUE | naive lift 중앙값 **0.002** < SESOI 0.05; bus 언급 **97.4%**·parked 부정 **88.6%** → 근-완전 그래프(bus 노드가 97% 클립 연결), 비판별 |
| **G-iii** KG가 B0 메타데이터 바닥을 SESOI만큼 못 넘음 | ✅ TRUE | KG 엔티티-중첩-필터내 strict **0.176** < B0 **0.218**(랜덤-필터내 바닥 0.117보다 +0.059지만 메타 바닥 아래) |

**⇒ COLLAPSE_CONFIRMED = TRUE.**

## 정직한 미묘함 (over-claim 방지)
"캡션 채널이 완전히 죽었다"고 과장하지 않는다. 리뷰어가 요구한 **부정-인지(affirmative-only) 추출 fix**를 적용하면 3/5 엔티티가 약한 신호를 회복한다(lift affirmative: dense 0.091·stopped 0.094·two_wheeler 0.083; 단 **bus 0.032·parked 0.001 여전히 죽음**). 그러나 그 신호로도 KG는 여전히 B0 바닥 아래(0.176<0.218)라 **새 품질 축을 만들지 못한다**. 즉 붕괴는 "채널 완전 무신호"가 아니라 "채널이 메타 바닥을 넘길 만큼 강하지 못함"이 정확한 기전. parked는 렉시콘/부정 처리와 무관하게 바닥(§6 parked 과잉언급 사각지대와 일치).

## 엔티티 채널 상세 (`collapse_receipt_entities.csv`)
| 엔티티 | rel_def | 언급률(naive) | 부정 비중 | lift(naive) | lift(affirmative) |
|---|---|---:|---:|---:|---:|
| bus | multiple_buses | 0.974 | 0.335 | 0.002 | 0.032 |
| two_wheeler | two_plus_bikes | 0.850 | 0.768 | −0.002 | 0.083 |
| parked | parked_vehicle | 0.865 | 0.886 | −0.000 | 0.001 |
| dense | dense_frame | 0.112 | 0.012 | 0.089 | 0.091 |
| stopped | stopped_vehicles | 0.374 | 0.546 | 0.050 | 0.094 |

## 살린 방어 가능 코어 (원고 반영 대상)
1. **A6-KG 비순환 그래프-구축 감사** — 비순환 프로토콜(기여 #1)을 그래프 백엔드로 확장: 엣지-출처를 센서·캡션 채널로만 강제, 주석-채널 엣지=0 기계검증(영수증 R1: 센서 27,000 predicate 엣지 ∪ 캡션 affirmative 엣지, 주석 엣지 0). 방법론 기여이지 검색-방법 기여가 아님.
2. **KG-as-index = 정직한 구조 baseline** — B0/B4∪B1/B2 재조합으로 명시(≈B4 strict, <B0 전반). 새 색인/알고리즘 아님.
3. **경계/음성 결과** — "캡션 기반 멀티모달 코퍼스에서 entity-KG 검색은 sparse-entity-match로 붕괴하고 캡션의 과잉언급+부정 때문에 dense/메타 바닥에 지배당한다; 그래프 계열은 새 품질 축을 더하지 않는다." 프로젝트 정직 바에 부합하는 경계 발견.

## Path B (PI가 A 선택 → 보류, 향후과제)
`intersection_id`(facet_role=context, 3000/3000, 63값)를 traverse하는 관계형 2-홉("X 보인 클립과 같은 교차로")은 B4가 구조적으로 표현 불가한 유일한 진짜 그래프 기전. gold 비퇴화: dense_frame·multiple_buses·parked_vehicle(퇴화 제외: stopped 100%·two_plus_bikes 90%). 단 seed가 여전히 noisy 캡션 채널 의존 + 새 relevance 정의 + 자체 A6-KG 감사·재검토 선결 → 다-일 재설계. §10 향후과제로 명시.
