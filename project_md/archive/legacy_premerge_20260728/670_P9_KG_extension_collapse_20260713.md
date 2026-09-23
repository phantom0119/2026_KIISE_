# 670 — P9 그래프-구조(entity-KG) 확장: 사전등록→적대검토→KILL→정직 경계 확정, 2026-07-13

상태: **완료.** 사전등록(420 Amendment 9) → 3-렌즈 적대검토(BLOCKER 3 생존) → Amendment 9 판정(KILL "KG 우위" 가지) → PI 결정 A(정직 경계) → 붕괴 실측 영수증 → 원고 §7.4/§10 반영. GPU 미사용.

## 절차 규율 (CC-FR·P8 kill과 동일 패턴)
1. **사전등록** 420 Amendment 9: 경량 KG-as-index, 두 축(A6-KG 순환성 차단 + 질의유형×구조 비교), 게이트·SESOI·중단규칙.
2. **적대검토** 컴퓨트 전 3-렌즈(순환성-A6KG/질의유형-구조 공정성/구축-정직성) + 반증 파이프라인, 17 에이전트. **BLOCKER 3 전부 refuted=false**, MAJOR 7 생존. (`subagents/workflows/wf_b364e1b8-b13/`)
3. **판정** 420 "Amendment 9 판정": H-KG "합성 다중-홉 KG 우위" 가지 KILL — null-by-construction.
4. **PI 결정** = A(정직 경계로 확정). (B=관계형 2-홉 재설계는 보류→§10 향후과제)
5. **실측 영수증** `scripts/kg_collapse_receipt.py` → `paper_assets/20260713_kg/`.
6. **원고 반영** §7.4 신설 + §10 향후과제.

## 왜 KILL (컴퓨트 전 확정, 3 BLOCKER 수렴)
tri-source는 3채널(센서=필터/주석=정답/캡션=문서). A6-KG가 주석 엣지=0 강제 → KG 엣지 = 센서(=B0/B4)∪캡션(=B1/B2), **제3 신호 없음(구조적 강제)**. predicate측=B4 집합교차(정의상 동일); 캡션측=과잉언급+부정으로 바닥. "합성 다중-홉 우위"는 predicate축에 놓여 B4 홈그라운드 → 기전 부재.

## 실측 (동결 3게이트, 전부 TRUE → COLLAPSE_CONFIRMED)
- G-i: KG predicate 순회 ≡ B4 prefilter, 85q 집합-동일.
- G-ii: naive lift 중앙값 0.002<SESOI (bus 언급 97.4%·parked 부정 88.6%, 근-완전 그래프).
- G-iii: KG 엔티티-중첩-필터내 strict 0.176 < B0 0.218 (랜덤바닥 0.117).
- 정직 미묘함: 부정-인지 fix로 3/5 엔티티 lift~0.08 회복(bus/parked 죽음), 그래도 B0 아래 → 새 축 없음.

## 원고 반영 (F5 검증 유지)
§7.4 "구조 계열의 경계: entity-KG는 새 품질 축을 더하지 않는다" — A6-KG 감사(기여 #1 확장)·KG=B0/B4∪B1/B2 정직 baseline·경계 결과. §10 향후과제에 관계형 2-홉(Path B) 명시. verify_manuscript_v3.py에 KG 영수증 수치 체크 추가.

## Path B (보류, 향후과제)
intersection_id 관계형 2-홉만이 B4-표현불가 진짜 그래프 기전. dense/버스/주차 gold 비퇴화. 새 relevance 정의+자체 A6-KG 감사+재검토 선결 = 다-일 재설계. 별도 사전등록 필요.

## 교훈
CC-FR(κ 고아 신호)·P8(yes-편향 동어반복)에 이어 P9(제3 신호 부재)까지 — retrieval-augmented VLM-QA의 다겹 오염에서 야심찬 "이기는 구조" 설계가 적대검토에서 연속 KILL됨은 우연이 아니라 문제의 성질. 정직 경계 규명 자체가 기여(660과 동일 철학).
