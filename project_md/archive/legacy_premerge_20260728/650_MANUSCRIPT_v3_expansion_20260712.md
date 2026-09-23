# 650_MANUSCRIPT — v3 종합 확장 (11쪽→20쪽) 기록, 2026-07-12

정본 원고: `manuscript/kiise_dbr_manuscript_v3.md` (v2 대체). DBR 제출본: `manuscript/kiise_dbr_manuscript_v3_DBR_review.{md,docx,pdf}` — **A4 20쪽(≤20 충족)**.
검증: 전체 스위트 40/40, F5 검증기(`verify_manuscript_v3.py`) **141/141**(원 127 + v3 구조/감사 가드 14).

## 방식 (다중 에이전트 교차 검증)
- 청사진 `manuscript/v3_expansion_blueprint.md`(불변 조항 7 + 삭감 우선순위) → 워크플로우 wf_d9bd89e4-bf9: **비평 3(reviewer-value/structure/evidence) → 작성 6(W1–W6) → 감사 12(수치/주장)**. Fable 한도로 실패한 감사 10건은 Opus 전환 후 resume(wf 동일 runId)로 완료.
- 초안 원문 보존: `manuscript/v3_working/named/`. 통합 스크립트: `scripts/integrate_v3_stage1.py`(앵커 삽입·표/그림 토큰 해소·34블록) + `integrate_v3_stage2_refs.py`(IEEE first-appearance 참고문헌 재번호, acorn=[23]→[9] 정합).

## 신규 시각 자료
- 표 1 VALU차별성 / 표 3 3채널 실물예시(캡션 "no parked vehicles"로 §6·§9 과언급 맹점 실체화) / 표 4 데이터셋요약(4워크로드+2코퍼스) / 표 6 UCA판정(대조 4건·CI) / 표 10 색인3축 / 표 11 사다리 / 표 13 가이드라인(지위 열). 표 5(계산비용)는 20쪽 맞춤 위해 산문화(제거).
- 그림 2 붕괴(VRU B0–B5 v1/strict/semantic) / 그림 4 UCA 산점(값수준 φ=Cramér's V, 계층색) / 그림 5 M9 짝지은 산점. 표/그림 전 본문 등장순(표1–13·그림1–6), 참고문헌 [1]–[31].

## 적대 감사 반영 (BLOCKER/MAJOR)
- 신규 수치 전건 디스크 재검증: qrels strict 6,809/semantic 24,872(=72.6%), tri-source 85q semantic 부호 26/30/29(mean −0.0158), v1 진단 수치(0.1851·0.9117·0.9935·419·parsed_vqa) — 전부 실측 일치.
- 확증/탐색적 분류 수정(확증=본 실험군 Holm 가족 한정; UCA는 CI와 무관하게 설계상 탐색). 독립성 격자 30(특성화) vs 질의 25(5×5) 구분 명문. 손익분기 per-predicate-후-중앙값 문구. 다각도 Idefics2 near-chance(0.145) 보조 분리(3모델 주결과 유지).
- **불변 조항 4 명확화(통합자 결정)**: "v1 순환 수치는 **§4 붕괴 진단 맥락(붕괴 표·그림·진단 서사)** 내부에서만 인용" — §4는 순환성 진단 절이므로 v1 수치를 진단 근거로 제시하는 것은 취지에 부합(타 절 결과 제시 금지는 유지).

## 잔여 (사람)
ForeSea 저자·공저자 직위/이메일/전화; (선택) 투고 공고의 초록 자수 규정 최종 확인.
