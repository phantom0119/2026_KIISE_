# 외부 자문(2026-08-06) 사실 검증 및 수용 판정

방법: 1-에이전트 원문 검증(ACL Anthology·vldb.org·Harvard Dataverse·arXiv 직접 fetch) + 로컬 자산 직접 확인. 전체 로그는 워크플로 wg4zmtpav 기록 참조.

## 1. 자문의 서지·사실 주장 검증 — 전부 통과

| 자문 주장 | 판정 | 핵심 확인 내용 |
|---|---|---|
| BRINK (EACL 2026 long, 2026.eacl-long.114) | **실재 확인** | Zhou et al. (Staab·Kharlamov 그룹). 규칙 근거 엣지 삭제 + 개체 라벨 익명화(정수 ID)로 암기 의존 측정, 3개 KG(Family/FB15k-237/Wikidata5m). arXiv 2508.08344 |
| KGHaluBench (Findings of EACL 2026, 2026.findings-eacl.206) | **실재 확인** | KG 기반 동적 질문 생성 + 인기도 편향을 난이도 보정으로 처리, 25개 모델 평가 |
| In-depth Analysis of Graph-based RAG (PVLDB 18 p5623) | 실재 확인 | CUHK-Shenzhen+Huawei, 이전 검증과 일치 |
| PVLDB Vol 20 일정(매월 1일 마감, 전월 25일 초록, ~2027-03) | **확인** | 추가: 포털은 전월 20일 오픈 |
| EA&B 아티팩트 요건 | **확인 — 예상보다 엄격** | "최초 제출 시점에 전체 재현 패키지 링크 필수(no excuses)" — 수락 후 공개 계획 불가 |
| PrimeKG 공개성 | 확인 | Harvard Dataverse, CC0 1.0, ~3.2GB, 무게이팅 |
| STaRK 공개성 | 확인 | 코드 MIT / 데이터 CC-BY-4.0 (HF). **주의: STaRK-Prime은 PrimeKG 파생 — 독립 2개 도메인으로 계산 금지** |
| 로컬 자산(RAG 하니스 有, GraphRAG·PrimeKG·Neo4j 無, GPU 2장 점유) | 로컬 직접 확인 일치 | vldb_extension에 hotpotqa/nq/finqa 베이스라인·데이터셋 존재, NetworkX 3.4.2 가용, PrimeKG/STaRK/GraphRAG 패키지 부재, GPU0 100%·GPU1 메모리 점유 |

**정직한 기록**: BRINK와 KGHaluBench는 본 세션의 이전 검증 스윕(2026-08-06 오전)이 **놓친** 논문이다. 당시 스윕은 WildGraphBench까지는 포착했으나 EACL 2026 계열을 커버하지 못했다. "기존 연구는 암기 통제를 전혀 하지 않는다"는 이전 서술은 이에 따라 철회하고, "그래프 모달리티 내부의 암기 통제는 존재(BRINK)하나 그래프·텍스트 동기화 통제는 부재"로 좁힌다.

## 2. 자문이 놓치거나 보태야 할 것 (검증 에이전트 추가 발견)

- **BRINK의 범위 한계**: triple-store KG + KGQA형 KG-RAG만 다루며, 동일 사실의 텍스트 표현 arm이 없고 문서 유래 GraphRAG(커뮤니티 요약형)를 다루지 않음 → 자문이 권고한 "동기화 반사실 요인 설계"는 arXiv 초록 전수 질의 기준 **미점유**(단, 세션 검색 예산 소진으로 arXiv 한정 — 본실험 등록 전 ACL Anthology/DBLP 재확인 필요).
- 2606.22419가 PrimeKG를 이미 사용 — 우리가 PrimeKG 도메인을 쓰면 재현 arm으로 명시적 포섭 필요(계획과 일치).

## 3. 자문 권고의 수용 판정

| 권고 | 수용 | 비고 |
|---|---|---|
| 환각 지표 6분해(정확성/근거지지/기억고집/모순/거부/검색지지) | **전면 수용** | 기존 단일 정의는 충실성-사실성 혼동 — 타당한 지적 |
| 단발 closed-book 제외 → 반복 프로브·연속 moderator | **전면 수용** | 회귀효과 지적 타당. 기보유 probe 인프라로 구현 가능 |
| oracle/retrieved 요인 분해(구조 효과 vs 시스템 효과) | **전면 수용** | 본 재설계의 최대 개선점 |
| 그래프·텍스트 동기화 반사실 세계 | **전면 수용** | 좁혀진 신규성의 핵심 |
| "결론 뒤집기 1건 필수" 제거 → 선행 주장 2~3개 사전 지정·3결과 동등 | **수용** | 기존 문서도 동치 전환을 병기했으나 자문 형식이 더 엄밀 |
| 사람 라벨 200~400 부족 → 파일럿에서 불일치율·ICC 측정 후 산정 | **수용** | 600~1,300쌍 추정은 파일럿으로 확정 |
| 사전 등록 2단계 분리(파일럿→본실험) | **수용** | 직전 계획과 방향 일치, 형식화 채택 |
| "리뷰어 공격 원천 차단/우선권 보증" 표현 완화 | **수용** | 부록 A 표현 수정 |
| 12월 제출은 공격적, 2027-01~02 현실적 | **수용** | EA&B 최초 제출 아티팩트 요건 감안 시 더욱 타당 |

## 4. 종합

자문의 판정 `CONDITIONAL GO — REDESIGN BEFORE MAIN PREREGISTRATION`을 **그대로 채택**한다. 연구 질문의 가치는 유지되나, 본실험 사전 등록은 P0 CPU 파일럿(`GRAPHRAG_P0_CPU_PREREGISTRATION.md`) 통과 후에만 작성한다.
