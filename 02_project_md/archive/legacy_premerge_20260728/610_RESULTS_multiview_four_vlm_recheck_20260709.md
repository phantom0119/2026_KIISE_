# Four-VLM Multi-view Final Recheck

작성 기준일: 2026-07-09

## 판정

다른 에이전트의 보고는 핵심적으로 사실과 부합한다. 4개 VLM 결과 디렉터리, 평가 report, answer parquet, run manifest가 모두 존재하며, 보고된 주요 수치는 로컬 `multiview_answer_report.json`과 일치한다. 또한 이전 감사에서 요구했던 원고 정합성, manifest, 다각도 결과 반영도 대부분 수행되었다.

단, 본 재검증 과정에서 두 가지 작은 정합성 문제를 발견해 즉시 수정했다.

1. 그림 6 캡션의 “metadata-aware 우위가 답변까지 전파” 표현을 제거하고, “evidence 품질 상승에 따른 답변 정확도 상승”으로 완화했다.
2. 모델 표에 6.13절에서 실제 사용한 `InternVL3-8B`, `Idefics2-8b`를 추가하고, Idefics2 참고문헌 `[22]`를 추가했다.

수정 후 DBR review PDF를 재생성했으며, PDF는 16쪽으로 유지된다.

## 산출물 존재 확인

4개 VLM 결과 디렉터리는 모두 다음 파일을 보유한다.

- `vlm_answers.parquet`
- `eval/multiview_answer_report.json`
- `run_manifest.json`

| model dir | manifest | answers | eval report | snapshot | prompt hash |
|---|---:|---:|---:|---|---|
| `multiview_answer_vlm_qwen25vl_400` | yes | yes | yes | `cc594898137f460bfe9f0759e9844b3ce807cfb5` | `b236a9f...` |
| `multiview_answer_vlm_qwen2vl_400` | yes | yes | yes | `eed13092ef92e448dd6875b2a00151bd3f7db0ac` | `b236a9f...` |
| `multiview_answer_vlm_internvl3_400` | yes | yes | yes | `259a3b64a14623c0ec91a045cb43f7c5af5fa6af` | `b236a9f...` |
| `multiview_answer_vlm_idefics2_400` | yes | yes | yes | `2c42686c57fe21cf0348c9ce1077d094b72e7698` | `b236a9f...` |

동일 prompt hash가 유지되므로 모델 간 비교에서 prompt 차이는 없다.

## 수치 대조

| model | both_acc | gate | better-worse | p | both-better TOST |
|---|---:|---:|---:|---:|---:|
| Qwen2.5-VL | 0.2000 | pass | +0.056 | 0.0016 | equivalent |
| Qwen2-VL | 0.3025 | pass | +0.152 | 0.0002 | equivalent |
| InternVL3-8B | 0.2450 | pass | +0.084 | 0.0002 | equivalent |
| Idefics2-8b | 0.1450 | pass/marginal | +0.044 | 0.0256 | equivalent |

해석:

- 세 모델(Qwen2.5-VL, Qwen2-VL, InternVL3-8B)은 gate를 통과하고, better-view>worse-view가 명확하며, both-view는 better-view와 등가다.
- Idefics2-8b는 LLM backbone이 Mistral 계열이라 LLM-family independence를 보조하지만, both accuracy가 0.145로 chance 0.091에 가까워 강한 주 결과로 쓰면 안 된다.
- 따라서 본문 표 20은 3모델 중심으로 유지하고, Idefics2는 near-chance caveat와 함께 보조 근거로만 둔 현재 구성이 타당하다.

## 이전 제안 반영 여부

이전 감사에서 요구했던 항목별 상태:

| 요구 항목 | 상태 |
|---|---|
| 원고의 “LLM/VLM generation 미사용” 모순 제거 | 반영됨 |
| 모델 표에 answer-generation LLM/VLM 명시 | 반영됨, 본 재검증에서 InternVL/Idefics까지 추가 |
| “동기 촬영” 표현 제거 | 반영됨 |
| 다각도 결과를 초록/Abstract에 압축 반영 | 반영됨 |
| `run_manifest.json` 보강 | 4개 VLM 모두 존재 |
| 비-Qwen generic inference path | `run_multiview_answer_vlm.py`에 반영됨 |
| 표 20 n=400 오표기 수정 | 반영됨: 비대칭 stratum 250, 전체 평가집합 400으로 명시 |
| prefilter→answer 전파 과장 완화 | 본문은 완화됨. 본 재검증에서 그림 6 캡션도 수정 |
| Qwen 계열 한계 완화용 cross-model 복제 | InternVL3 반영, Idefics2 보조 반영 |

## 원고 상태

수정 후 재생성된 파일:

- Markdown: `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal.md`
- DBR review markdown: `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal_DBR_review.md`
- DBR review docx: `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal_DBR_review.docx`
- DBR review pdf: `2026_KIISE/manuscript/kiise_dbr_manuscript_v1_true_multimodal_DBR_review.pdf`

PDF 상태:

- 생성 시각: 2026-07-09 10:37 KST
- 페이지 수: 16
- 규정 상한 20쪽 이내

## 연구 취지 부합성

현재 4-VLM 다각도 실험은 본 연구 취지와 부합한다. 이유는 다음과 같다.

1. 본 연구의 핵심 thesis는 “AI 응답 품질은 모델만이 아니라 DB evidence retrieval/selection 구조에 좌우된다”이다.
2. 다각도 실험은 같은 모델과 같은 prompt를 고정하고, DB가 공급하는 view evidence만 바꾼다.
3. 검색-level 실험은 naive multi-view availability가 이득을 주지 않음을 보였고, answer-level 실험은 better-view selection이 답변 정확도를 높임을 보였다.
4. 따라서 “selection > availability/accumulation”이라는 논리로 기존 evidence selection thesis를 view 차원까지 확장한다.

현재 방어 가능한 문장:

> AI Hub 다각도 CCTV의 bbox 면적 기반 시점 비대칭 조건에서, 고정 VLM에 어떤 view evidence를 공급하는지가 답변 정확도를 유의하게 바꾼다. 서로 다른 vision encoder를 포함한 세 VLM에서 better-view는 worse-view보다 정확도가 높았고, both-view는 better-view 대비 추가 이득 없이 등가였다. 따라서 본 데이터와 모델 조건에서 다각도 CCTV DB의 역할은 모든 시점을 많이 쌓는 것이 아니라 더 나은 시점을 선택해 공급하는 것이다.

금지해야 할 문장:

- “다각도 CCTV는 일반적으로 무의미하다.”
- “두 view에 상보 정보가 없다.”
- “4개 모델 모두 강하게 일치했다.”
- “Idefics2로 강한 LLM-family independent 검증이 완료됐다.”
- “bbox 면적은 occlusion visibility를 직접 측정한다.”
- “VLM이 CCTV event class를 전반적으로 잘 분류한다.”

## 남은 위험

1. Idefics2는 near-chance이므로 보조 근거에 그쳐야 한다.
2. VLM 절대 정확도는 낮다. paired delta 중심으로만 주장해야 한다.
3. symmetric control은 일부 class 표본이 작다. 보조 대조군으로만 사용한다.
4. `run_manifest.json` 중 Qwen2.5/Qwen2는 사후 reconstructed manifest로 명시되어 있다. 재실행 가능성은 높지만, 엄밀히는 원실행 시 자동 manifest가 아니었다.
5. Idefics2 참고문헌은 본 재검증에서 새로 추가했으므로, 최종 reference formatting을 한번 더 육안 검수하는 것이 좋다.

## 최종 권고

이제 추가 대규모 실험보다 제출 전 품질관리로 넘어가는 것이 맞다.

우선순위:

1. PDF/Word 육안 검수: 표 20, 그림 6/7, 참고문헌 [19]-[22], 초록 길이
2. 제출용 저자 정보/소속/교신저자 정보 입력
3. `submission_materials_index.md`를 최신 4-VLM 상태로 갱신
4. 필요 시 Idefics2를 표 20에 넣지 않은 이유를 한계/본문 문장으로 유지

현재 상태는 연구 취지에 부합하며, 제출 방어 가능성이 이전보다 높아진 상태로 판단한다.
