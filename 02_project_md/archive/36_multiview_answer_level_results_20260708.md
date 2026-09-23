# Results: Answer-level Multi-view VLM Experiment (AI Hub 71953)

작성 기준일: 2026-07-08
사전등록: `project_md/35_multiview_answer_level_prereg_20260708.md` (실행 전 고정). 본 문서는 실행 후 수치·판정.
스크립트: `run_multiview_answer_vlm.py`(추론), `eval_multiview_answer_vlm.py`(gate/CI/TOST/verdict).
산출물: `Datasets/processed/aihub_multi_angle_cctv/20260708/results/multiview_answer_vlm_qwen25vl_400/{vlm_answers.parquet, eval/}`.

2026-07-09 최신 갱신: 본 문서의 앞부분은 Qwen2.5-VL primary run 결과이며, 최종 논문 claim은 아래 robustness 섹션과 `38_four_vlm_multiview_final_recheck_20260709.md`의 4-VLM 재검증을 함께 따른다. 최종 표현은 세 개의 강한 VLM(Qwen2.5-VL, Qwen2-VL, InternVL3-8B)에서 결론이 반복 관찰되었고, Idefics2-8b는 near-chance 보조 근거라는 범위로 제한한다.

## 설정 (사전등록대로 실행)
- 모델: **Qwen2.5-VL-7B-Instruct**, temperature=0, greedy, 프롬프트·후보순서·이미지패킷 고정.
- Task: **leakage-free 중립 closed-set** — 11 event_class 후보 중 택1(JSON). 원본 VQA 질문 미사용.
- 표본: bbox-비대칭 stratum **400 clip**(asym 250 ratio≥2 + sym 150 ratio<1.2), full canonical에서 균형 샘플.
- 조건: closed_book / worse_view_only / better_view_only / both_view. better=평균 bbox 큰 view.
- 품질: valid JSON **100%**, unmatched 0%, snap 0% (모두 exact match). n=400, chance=1/11=0.091.

## 결과 (n=400)

| 조건 | 정확도 | asym | sym |
|---|---:|---:|---:|
| closed_book | 0.100 | 0.104 | 0.093 |
| worse_view_only | 0.140 | 0.132 | 0.153 |
| better_view_only | 0.190 | 0.188 | 0.193 |
| both_view | 0.200 | 0.200 | 0.200 |

### GATE (해석 전 필수) — **PASS**
- both_view(0.200) > chance(0.091) ✅
- both_view − closed_book = **+0.096, CI[0.060, 0.132], p=0.0002** ✅ (CI excl 0)
- → **VLM이 한국어 CCTV 증거를 실제로 grounding함.** view 조건 비교 유효.

### 사전등록 비교 (asymmetric stratum, paired bootstrap 5000 + TOST vs SESOI 0.05)
| 비교 | Δ acc | 95% CI | 유의 | TOST 등가 | p |
|---|---:|---|:--:|:--:|---:|
| **better − worse** | **+0.056** | [0.020, 0.092] | **O** | X | 0.0016 |
| both − better | +0.012 | [−0.008, 0.036] | X | **O(등가)** | 0.41 |
| both − closed | +0.096 | [0.060, 0.132] | O | X | 0.0002 |

### Symmetric control (ratio<1.2)
| 비교 | Δ acc | 95% CI | 유의 |
|---|---:|---|:--:|
| better − worse (sym) | +0.040 | [−0.013, 0.100] | X (p=0.19) |
| both − better (sym) | +0.007 | [−0.020, 0.040] | X (등가) |

## 판정 (사전등록 규칙 자동 적용): **SELECT_BETTER_VIEW**

**better ≈ both > worse.** 즉:
1. **어느 view를 공급하느냐가 답변 정확도를 유의하게 좌우한다** — 기하적으로 잘 보이는(bbox 큰) view가 나쁜 view보다 **+0.056 유의**(p=0.0016).
2. **두 view를 모두 쌓아도(both) 최선 단일 view(better)보다 추가 이득이 없다** — TOST로 SESOI(0.05) 내 **등가 입증**(Δ+0.012).
3. Symmetric control에서 better−worse가 유의하지 않음(ns) → 비대칭 stratum의 효과가 **실제 visibility 비대칭에서 기인**함을 뒷받침(단, sym에서도 +0.040 방향성은 있음 = ratio<1.2도 완전 대칭 아님·n=150 검정력).

## 논문에 쓸 claim (primary run 기준)
> "고정 VLM(Qwen2.5-VL-7B)에서 DB가 어떤 view evidence를 공급하느냐가 답변 정확도를 좌우한다. 기하적으로 잘 보이는 view는 나쁜 view보다 유의하게 높은 정확도를 주지만(+0.056, p=0.0016), **두 view를 모두 공급하는 것은 최선 단일 view 대비 추가 이득이 없다(TOST 등가)**. 따라서 다각도 CCTV에서 DB의 역할은 view를 많이 쌓는 것이 아니라 **더 나은 view를 선택**하는 것이다."

## 검색-level 결과와의 일관된 서사 (thesis 강화)
- 검색-level(`run_multiview_evidence_selection.py`): naive dual-view 병합 = single view와 무차별, 겉보기 상보성은 max-of-two 착시(permutation control).
- answer-level(본 실험): both = better와 등가, **better > worse 유의**.
- **두 층 모두 "다각도를 쌓는 것(availability/quantity)"이 아니라 "좋은 evidence를 선택하는 것(selection)"이 답을 좌우**한다 → 논문 핵심 thesis(DB evidence SELECTION 구조가 답변 품질을 결정)를 검색·답변 양쪽에서 지지.

## 정직한 한계 (primary run 기준)
1. **절대 정확도 낮음(0.10–0.20)**: Qwen2.5-VL primary run에서 11-way 한국어 CCTV 분류가 3 keyframe·7B VLM에 어려웠다. 단, gate가 evidence 사용을 입증했고 모든 비교가 **within-model paired**라 상대 delta는 유효하다. 이후 Qwen2-VL과 InternVL3에서는 절대 정확도가 더 높았지만 여전히 class-general 고성능 주장은 하지 않는다.
2. **supporting_view 지표 무정보**: Qwen2.5-VL both_view에서 모델이 단일 view(c1/c2)를 지목한 경우 1건뿐(대개 "both"/"none") → primary run의 self-report grounding 검증은 신호가 약하다. Qwen2-VL/InternVL3에서는 보조 신호가 관찰되지만 주 결론은 accuracy delta에 둔다.
3. **better view = bbox 면적 proxy**(근접·크롭일 수 있음, 가림 아님) → "geometric visibility asymmetry"로 한정.
4. **모델 범위**: 최신 기준에서는 Qwen2-VL과 InternVL3 복제가 완료되었고, Idefics2는 near-chance 보조 근거다. 강한 LLM-family independent 복제는 여전히 후속 과제다.
5. symmetric control better−worse가 방향성(+0.040) 있음(ns) → 완전 대칭 아님·검정력.

## Robustness: 2nd VLM 복제 (Qwen2-VL-7B, 동일 400-clip·프롬프트·gate/TOST)

산출물: `results/multiview_answer_vlm_qwen2vl_400/{vlm_answers.parquet, eval/}`. valid JSON 98.4%(unmatched 2).

| 비교 | Qwen2.5-VL-7B (primary) | Qwen2-VL-7B (robustness) |
|---|---|---|
| acc closed/worse/better/both | 0.10 / 0.14 / 0.19 / 0.20 | 0.11 / 0.19 / 0.28 / 0.30 |
| GATE (both>chance & >closed) | PASS (Δ+0.096, p=2e-4) | PASS (Δ+0.204, p=2e-4) |
| better − worse (asym) | **+0.056 [0.02,0.09] p=0.0016** | **+0.152 [0.09,0.21] p=0.0002** |
| both − better (asym) | +0.012 TOST-equiv | +0.008 TOST-equiv |
| symmetric better−worse | +0.040 ns | −0.013 ns |
| supporting_view=better view | 1건(무정보) | **58.3% (12건, >50% chance)** |
| **VERDICT** | **SELECT_BETTER_VIEW** | **SELECT_BETTER_VIEW** |

**두 모델(다른 버전·가중치) 모두에서 결론이 복제됨**: gate 통과, better>worse 유의, both≈better 등가, symmetric-control null. Qwen2-VL은 효과가 더 크고(+0.152), supporting_view가 실제 better view와 58% 일치(모델이 더 나은 view를 스스로 인지)해 grounding 근거를 하나 더 제공.

### Cross-family 복제 (InternVL3-8B, 서로 다른 vision encoder InternViT)

산출물: `results/multiview_answer_vlm_internvl3_400/{vlm_answers.parquet, eval/, run_manifest.json(자동생성)}`. valid JSON 100%(unmatched 24=1.5%).

| 비교 (asym stratum) | InternVL3-8B |
|---|---|
| acc closed/worse/better/both | 0.104 / 0.164 / 0.248 / 0.256 |
| GATE (both>chance & >closed) | PASS (both−closed +0.152, p=2e-4) |
| better − worse | **+0.084 [0.04,0.13], p=0.0002** |
| both − better | +0.008 TOST-equiv (p=0.61) |
| symmetric better−worse | −0.013 ns |
| supporting_view=better view | **74.1% (27건)** — 3모델 중 최고 |
| VERDICT | SELECT_BETTER_VIEW |

**세 VLM(Qwen2.5-VL, Qwen2-VL, InternVL3-8B) 모두에서 결론 복제**: gate 통과, better>worse 유의, both≈better 등가, symmetric-control null. InternVL3은 **서로 다른 vision encoder(InternViT)**를 사용하므로, view-selection 결과의 핵심 축인 시각 경로에서 cross-model 재현을 제공 → "**쌓지 말고 선택하라**"가 시각 인코더 차원에서 강건.
- 정직한 범위: InternVL3은 시각 인코더는 독립이나 LLM backbone은 Qwen 계열 → LLM 계열까지 완전 독립(예: Mistral 기반) 복제는 아래 Idefics2 참고. 절대 정확도는 여전히 낮음(0.10–0.32).

### 완전 LLM-독립 복제 (Idefics2-8b = Mistral-7B LLM + SigLIP, 보조·near-chance)

산출물: `results/multiview_answer_vlm_idefics2_400/`. valid JSON 98.4%. **정직한 caveat: 이 모델은 한국어 CCTV 11-way에서 near-chance**(both 0.145 vs chance 0.091)이며 gate가 marginal.

| 비교 (asym stratum) | Idefics2-8b |
|---|---|
| acc closed/worse/better/both | 0.104 / 0.096 / 0.140 / 0.124 |
| GATE | marginal PASS (both−closed +0.037 on n=400, CI excl 0; asym both−closed +0.020 ns) |
| better − worse | **+0.044 [0.008,0.084], p=0.026 (유의)** |
| both − better | −0.016 TOST-equiv |
| symmetric better−worse | +0.027 ns |
| supporting_view=better | 55.8% (382/400 named) |
| VERDICT | SELECT_BETTER_VIEW |

**해석(정직)**: LLM 계열까지 완전 독립(Mistral)인 모델에서도 **better>worse 방향은 유의**하고 both≈better가 유지되어, "쌓지 말고 선택"이 LLM 계열 독립 축에서도 **시사적으로 재현**됨. 단 이 모델은 near-chance·gate marginal이라 **보조 근거**로만 사용하며, near-chance가 아닌 강한 LLM-독립 복제는 여전히 후속 과제. → 4모델 중 3모델(Qwen2.5-VL/Qwen2-VL/InternVL3)이 강하게, Idefics2가 약하게(near-chance) 동일 방향.

## No-go / 금지 (준수)
- "다각도는 일반적으로 무의미하다" 결론 **금지**(사전등록). 실제 결론은 "**쌓지 말고 선택하라**"이며, gate 통과·유의·등가검정·세 개의 강한 VLM 반복 관찰(Qwen2.5-VL/Qwen2-VL/InternVL3)로 방어한다. Idefics2는 LLM-family independence를 시사하는 near-chance 보조 근거로만 사용한다.
