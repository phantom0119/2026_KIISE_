# Pre-registration: Answer-level Multi-view VLM Experiment (AI Hub 71953)

작성 기준일: 2026-07-08
상태: **CONVERGED / LOCKED** (Claude + codex 조건부 승인 합의). 이 문서는 실험 실행 **전에** 확정되며, 실행 후 수치는 별도 결과 문서에 기록한다. 해석 규칙은 결과를 보기 전에 고정한다.

2026-07-09 최신 갱신: 본 사전등록 설계는 실행 완료되었다. Qwen2.5-VL primary 결과는 `36_multiview_answer_level_results_20260708.md`, Qwen2-VL/InternVL3/Idefics2를 포함한 최종 4-VLM 재검증은 `610_RESULTS_multiview_four_vlm_recheck_20260709.md`를 따른다. 최신 결론은 세 개의 강한 VLM에서 `better-view > worse-view`, `both-view ≈ better-view`가 반복되고, Idefics2는 near-chance 보조 근거로만 둔다는 범위다.

## 0. 배경 (왜 answer-level인가)
- 논문 thesis: LLM/VLM 답변 품질은 모델이 아니라 **DB가 어떤 evidence를 골라 공급하느냐**에 좌우된다.
- retrieval-level 다각도 실험은 이미 완료 = **통제된 negative** (`run_multiview_evidence_selection.py`): naive dual-view 병합 ≈ single view(Hit@1/MRR CI incl 0), 겉보기 view-상보성은 **max-of-two 착시**(permutation control `pseudo_oracle_view`가 이득의 88–92% 재현, 잔차 CI incl 0, 2 인코더).
- 적대적 검증(3 lens, high conf): null은 유효하나 **AI Hub 71953 evidence layer가 라벨링상 대칭**(4,500 clip 전부 view당 정확히 3 human-bbox frame, single-view-only 사건 0개)이라 retrieval은 진짜 다각도 이점에 **구조적으로 blind**. 유일한 방어 경로 = **answer-level VLM 실험 on view-asymmetry stratum**.

## 1. Task (leakage-free 중립 질의) — codex 조건1 수용
- 질의(고정): "다음은 하나의 사건에 대한 CCTV 증거이다. 제시된 증거만 보고 관찰되는 사건 유형을 아래 후보 중 하나로 고르라."
- 후보: 11개 event_class 전체(순서는 seed=20260708로 고정 셔플, 모든 조건 동일).
- 출력(JSON): `{event_class, confidence(0-1), supporting_view(c1|c2|both|none), rationale}`.
- 정답 = 해당 clip의 실제 event_class. **원본 VQA 질문 사용 금지**(event_class를 문장에 담아 leakage 유발). 프롬프트에 후보 목록 외 event_class 노출 금지.

## 2. 조건 (better/worse view) — codex 조건2 수용
- clip별 **better_view = 평균 bbox 면적이 큰 view**, worse_view = 작은 view.
- **closed_book** (추가 A): 이미지 없음, 질의+후보만 → VLM prior floor.
- **worse_view_only**: worse view의 evidence frame(3장)만.
- **better_view_only**: better view의 evidence frame(3장)만.
- **both_view**: 두 view evidence(6장).
- strata: **asymmetric(ratio≥2) = MAIN**, **symmetric(ratio<1.2) = CONTROL**.

## 3. 표본 — codex 조건3 **정정**
- 디스크 실측(clip×view 평균 bbox 면적, ratio=큰/작은): full 4,500 중 ratio≥2 = **1,536(34.1%)** (codex의 1,934/43% 아님); subset-110 중 = **30(27.3%)** → **검정력 부족**.
- 결정: **full canonical에서 새로 materialize**. asymmetric 250 + symmetric 150 = **400 clip**, 11 class × Train/Val 균형, seed 20260708. 조건당 400문항, paired.
- 목표 검정력: SESOI |Δacc|<0.05에서 paired 비교가 의미 있도록 stratum당 n≥150.

## 4. 지표 — codex 조건4 + 추가
- 조건별 event_class exact-match 정확도.
- Δ(better−worse), Δ(both−better), Δ(any evidence−closed_book).
- invalid-JSON / hallucination(후보 밖 답) 비율.
- **supporting_view 일치율** — both_view 조건에**만** 적용(추가 C): 모델이 지목한 view가 실제 better view와 일치하는가.
- paired bootstrap 95% CI(5000) + Wilcoxon; null 주장 시 **TOST 등가검정 vs SESOI |Δacc|<0.05**(추가 B).

## 5. 모델·프롬프트 고정 — codex 조건5 수용
- **Qwen2.5-VL-7B-Instruct** (다운로드 후 resolved commit 기록·pin). temperature=0, greedy, max_new_tokens 고정, 프롬프트 템플릿·이미지 리사이즈·후보 순서(고정 seed) 모든 조건 동일. GPU: 2×RTX3090.

## 6. Go/No-Go GATE (추가 A) — 해석 전에 반드시 통과
view delta 해석 **전에**: (i) both_view acc > chance(1/11≈0.091), **그리고** (ii) both_view > closed_book (CI excl 0). 하나라도 실패 → **VLM이 한국어 CCTV evidence를 grounding하지 못함** → view 조건 비교는 무효, **VLM-limitation으로 보고**(데이터셋 결론 아님).

## 7. 사전등록 해석 규칙 — codex 조건6 수용
- **both > better** (CI excl 0, Δ>SESOI): 다각도 evidence가 answer-level 추가 이득.
- **better ≈ both > worse**: DB는 view를 쌓지 말고 **좋은 view를 선택**해야.
- **모두 등가**(TOST가 SESOI 내 등가 입증): 현재 데이터/모델에서 view 다각도가 답변 품질로도 **미관측**(데이터·모델 조건부).
- **gate 실패**: VLM-limitation, view 해석 무효.
- **금지(어떤 경우에도)**: "다각도는 일반적으로 무의미하다."

## 8. 산출물(작업 범위) — codex 요청 수용
`build_bbox_asymmetry_stratum.py` → stratum manifest; view-condition evidence packet; VLM 추론 스크립트; JSON parsing/eval; paired bootstrap CI + TOST; symmetric control; 최종 claim/no-go 문서.

## 9. 알려진 위험(사전 명시)
- bbox 면적 큰 view = "더 잘 보임"의 proxy일 뿐(가림이 아니라 근접/크롭일 수 있음) → 결론은 "geometric visibility asymmetry"로 한정.
- 두 view는 시간 비동기(median 2.03s, 26% 무overlap) → both_view는 "서로 다른 순간 2 카메라". packet 설명에 명시.
- 11-way 분류가 3 keyframe으로 가능한지 자체가 불확실 → gate가 이를 검출.
- VLM의 한국어 CCTV 역량 미검증 → gate로 방어.
