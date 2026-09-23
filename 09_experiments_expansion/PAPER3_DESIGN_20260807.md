# 논문 3 연구 설계서 — 답변율 교란(Answer-Rate Confounding)

> 작성 2026-08-07 | 판정: **CONDITIONAL-GO (프레이밍 강제 변경)** — 2주차 게이트 통과 시 본격 진행
> **2026-08-07 개정**: 초록 수준 재조사 결과 반영. 원래의 1번 주장이 *Nature* 논문에 선점되어 **논문의 판매 문장을 교체**했다. §1·§5·§7 변경. 상세는 §5.
> 선행 문서: TOPIC_REORGANIZATION_20260807.md, EvidenceViewDB.md(기각), CLAIM_MAP.md(ECIR)

---

## 1. 연구 목적

> ⚠ **아래 "한 문장"은 2026-08-07에 교체되었다.** 구 버전("순위가 답변율 순위임을 *보인다*")은 Kalai et al., *Nature* 653:1047-1051 (2026)이 이미 소유한 주장이다. 발견을 파는 논문은 성립하지 않는다. **계측과 정량화를 파는 논문으로 전환한다.**

**한 문장(신)**: 답변율 교란은 이미 알려져 있고 교정법까지 실무에 배포되어 있지만, **그 교정이 실제로 무엇을 바꾸는지를 아무도 공표한 적이 없다.** 우리는 (i) 그것을 40개 설정 격자에서 수치로 공표하고, (ii) 교란을 드러내는 **적합성 검사 도구**(퇴화 시스템 투입)를 만들며, (iii) 기존 결측 처리가 놓친 **내생적 자기선택(endogenous self-selection)** 추정 문제로 정식화한다.

**구 버전(폐기)**: ~~LLM 판사 점수로 RAG 설정을 비교할 때, 그 순위가 "답변 품질" 순위가 아니라 "얼마나 자주 답했는가" 순위임을 보이고…~~ — "보인다"는 선점됨.

**왜 필요한가**: 실무에서 청크 크기·top-k·리랭커를 고를 때 LLM 판사 평균 점수를 비교하는 것이 표준 관행이다(벤더 4곳이 문서로 지시). 이 설정들은 **답변 품질만이 아니라 "답을 할 수 있는지"를 함께 바꾼다.** 거부한 질의가 평균에서 조용히 빠지면 집계가 오염된다. **여기까지는 선행 연구가 이미 말했다.** 남은 공백은 그 다음이다 — 교정을 적용하면 **순위가 얼마나 바뀌는가**? Vectara는 교정을 적용하지만 교정 전 순위를 공개하지 않으며, *Nature*는 사전 채점 규칙만 처방하고 사후 교정도 순위 변화도 다루지 않는다. **"얼마나"에 답한 문헌이 없다.**

**⚠ 방향 중립 서술 강제(§5.7)**: "거부가 점수를 부풀린다"고 쓰지 말 것. Vectara의 실측은 **반대 방향**이었다(답변율 낮은 모델이 환각률 상위). 올바른 문장은 **"집계가 답변율에 의해 교란되며 방향은 사전 예측 불가"**이고, 우리 격자에서 관측된 양의 방향은 **전제가 아니라 결과**로 제시한다.

**범위상의 결정적 사실**: 감사한 모든 선행 사례가 **모델 간** 비교다. **설정 간** 비교에 이 문제를 적용한 사례는 하나도 없다(§5.7).

## 2. 검증된 예비 결과 (31,040행 재계산 완료)

40개 설정 × 776개 질의, LegalBench-RAG, Prometheus-7B 판사, 5점 정확성 척도.

| 측정 | 값 |
|---|---|
| 원 점수 순위 vs **답변율** 순위 (Spearman) | **+0.976** (p=1.1e-26) |
| 원 점수 순위 vs **교정 품질** 순위 | **+0.483** |
| chunk_size → 답변율 (η²) | 0.641 |
| chunk_size → 원 점수 평균 (η²) | 0.737 |
| chunk_size → 질의 내 교정 품질 (η²) | 0.192 (p=0.011) |
| 10계단 이상 이동한 설정 | **17 / 40** |
| 원 점수 38위 설정의 교정 후 순위 | **1위** |
| 원 점수 상위 5개 중 생존 | 2개 |

**폐기된 주장(중요)**: "답변한 경우만 보면 품질 차이가 사라진다"는 **거짓**이다. 단순 조건부 비교는 0.05로 보이지만, 이는 설정마다 답한 질의 집합이 다르기 때문(선택 편향). **같은 질의 안에서 비교하면 0.19로 되살아나며**, 30개 이상 설정이 공통으로 답한 233개 질의에서는 0.363(p=0.0005)이다. 초안에 "flat"이라 쓰면 데이터 보유자 한 명에게 무너진다(중단 기준 K9).

## 3. 실험 방법

### 3.1 1단계 — 기존 데이터 재분석 (CPU, 1~2주차)

- **E1 거부 분류기 검증** (선행 필수): 현재 독립변수가 문자열 매칭(정확 일치 50.9%)이다. 300건을 답변율 십분위로 층화해 사람이 3분류(명시 거부/애매한 회피/실질 답변) 라벨링, 정밀도·재현율·카파 보고. **모든 headline을 검증된 분류기로 재계산.**
- **E2 선택 편향 보정**: 질의 고정효과(708개 질의, 15,204행), 주성층화(k≥30 → 233질의), Lee 경계, 질의 단위 부트스트랩 CI, leave-one-config-out.
- **E3 순위 발산·위험-커버리지**: 40행 표(원 평균/답변율/단순 조건부/교정 품질과 각 순위), 설정별 위험-커버리지 곡선, AURC.
- **E4 효용 민감도**: 거부의 가치 u를 1~5로 스윕해 순위 교차점 제시. "척도 역전" 프레이밍을 **숨은 규범 파라미터의 명시**로 대체.
- **E5 출처 감사**: 모든 수치를 31,040행 그리드 / 18,624행 tail로 분리 표기. 오염된 tail 수치(거부-충실성 상관 +0.979 등)를 격리하고 정상 그리드 값(0.800/0.611)으로 대체.

### 3.2 2단계 — 신규 실험 (GPU, 3~4주차)

- **E6 널 시스템 적합성 검사**: 항상거부 / 무검색 / 질문복창 3종을 LegalBench-RAG + HotpotQA + NQ + FinQA에 투입, 5-판사 패널로 채점(~5.4만 호출). *기존 closedbook arm이 이미 무검색 널이라 무료 복제 arm으로 활용.*
- **E7 상용 도구 검사**: **stock RAGAS 0.4.2 + stock DeepEval 4.1.5**에 동일 널 시스템 투입. (DeepEval은 별도 venv 필요, 200건 스모크 테스트 선행 필수.)
  - **E7a(2026-08-07 신설, 최우선)**: RAGAS의 `faithfulness`(거부→NaN, 분모에서 삭제)와 `answer_relevancy`(거부→0점, 분모 유지)의 **집계 의미론 불일치**를 동일 입력으로 실증한다. 같은 거부 응답이 한 지표에서는 사라지고 다른 지표에서는 0점이 되므로, 두 지표를 함께 보고하는 표준 관행에서 **거부율이 두 지표를 반대 방향으로 민다.** 이것이 (e)의 논문 수준 알맹이다(§5.7). 부수 확인: `n_scored`·커버리지가 출력에 존재하지 않음, `__repr__`이 nanmean만 출력.
  - **E7b**: DeepEval `ignore_errors` / `skip_on_missing_params` 조합 4가지에서 동일 널 시스템의 최종 점수가 어떻게 달라지는지 표로 제시(문서에 없는 동작이므로 실측이 유일한 근거).
  - **E7c(2026-08-07 신설)**: **교차 라이브러리 집계 의미론 표.** 소스로 확정된 3개(RAGAS·Opik·Braintrust)가 미채점 항목을 분모에서 제거한다는 사실을 코드 인용과 함께 표로 제시하고, 동일 널 시스템 입력에 대한 실제 출력 숫자를 나란히 둔다. Braintrust는 **분모 `count`를 계산한 뒤 요약에서 버린다**는 점을 별도로 강조(§5.8). LangSmith·Galileo는 "서버측 비공개"로 표에 명시하되 결론에 사용하지 않는다.
- **E8 프롬프트 arm**: 관대한 지시문으로 12개 설정 재실행 — 현상이 지시문 한 줄의 산물인지 검정.
- **E9 판사 복제**: 답변율 층화 12개 설정을 5개 판사로 재채점, 판사별 순위 발산 재현 여부.

### 3.3 산출물

보고 규칙 모듈(`rag_report`): 평균 대신 **(커버리지, 선택적 위험) 쌍**, AURC, `n_scored/n_total`, 널 시스템 적합성 검사, 효용 민감도 곡선. + RAGAS 이슈 #2806 후속 정량화 보고.

## 4. 기대 결과 (사전 등록 양방향)

> **2026-08-07 개정**: 서사 열을 재작성했다. 구 버전은 "리더보드는 커버리지 순위"를 강한 결과로 삼았으나 이는 *Nature* 2026이 소유한 주장이다(§5.2). 모든 서사를 **정량화·계측** 언어로 교체한다.

| 시나리오 | 결과 | 논문 서사 |
|---|---|---|
| 순위 발산 유지(현재 0.48) + 널 시스템이 실제 설정보다 상위 | **강한 결과** | 처방된 교정의 **비용을 최초로 수치화**(17/40 설정 ≥10계단 이동) + 프레임워크 적합성 실패를 계측기로 입증 |
| 순위 발산 유지 + 널 시스템은 정상 처리 | **중간** | 도구는 통과, 그럼에도 교정 전후 격차는 크다 → **정량화 + 내생 결측 추정량**만으로 승부(보고 규칙은 기여로 열거 금지, §5.2-d) |
| 순위 발산 소멸(0.85↑) | **중단** | 2주차 게이트 K2에서 조기 종료 |
| 관대한 프롬프트에서 소멸 | 축소 | 짧은 부정 결과 노트 |
| 타 리더보드가 교정 전/후를 이미 공표한 것이 발견됨 | **중단·재설계** | K11 발동 — 판매 문장 무효 |

## 5. 신규성 검증 — **초록 수준 재조사 완료 (2026-08-07)**

이전 판의 "⚠ 검증 한계"를 해소했다. OpenAlex 초록 검색(24개 질의), **ACL Anthology 전체 XML 127,461편 초록 정규식 조사**, Semantic Scholar 불리언 대량 조회, 기존 점유자 3편의 인용 추적을 수행했다. **결과는 이전 판보다 나쁘다. 다섯 개 하위 주장 중 둘이 죽었다.**

### 5.1 판정 요약

| 하위 주장 | 판정 | 근거 |
|---|---|---|
| (a) 거부/답변율이 자동 평가 집계를 교란한다 | **점유됨 (치명)** | *Nature* 2026 + ACL 2025 + Findings EACL 2023 |
| (b) 퇴화 시스템을 RAG 평가 **프레임워크**에 적합성 검사로 투입 | **생존 (최강)** | 전 색인 무점유 |
| (c) 답변율 차이를 통계적으로 보정 | **부분 점유 + 실무 배포됨** | Vectara가 이미 시행 중 |
| (d) 커버리지·답변율 보고 규칙 | **점유됨 (6방향)** | 기여로 열거 금지 |
| (e) RAGAS/DeepEval 집계 결함 정량화 | **생존 (근거 얇음)** | 논문 수준 무점유 |

### 5.2 죽은 주장 — 직접 검증한 원문

**(a) 사망.** Kalai, Nachum, Vempala & Zhang, "Evaluating large language models for accuracy incentivizes hallucinations," ***Nature* 653(8116):1047-1051 (2026)**, doi 10.1038/s41586-026-10549-w. **본인이 Crossref로 직접 확인**: 초록에 "dominant headline metrics such as accuracy systematically reward guessing over admitting uncertainty"가 그대로 있다. 이것이 우리가 팔려던 문장이다. RAG 특정형도 이미 있다 — **UAEval4RAG (ACL 2025 Long, arXiv 2412.12300)**, 본인이 arXiv API로 초록 확인: "We conduct experiments with various RAG components, including retrieval models, rewriting methods, rerankers, language models, and prompting strategies" + "unanswered ratio and acceptable ratio metrics". **우리와 같은 손잡이를 돌리고 같은 비율을 보고한다.** 선구자는 Selective-LAMA(Findings EACL 2023).
→ **차별점(유일)**: UAEval4RAG는 *진짜 답할 수 없는* 질의의 거부 능력을 평가한다. 우리는 *답할 수 있는* 질의에서의 거부가 품질 집계를 오염시키는 문제를 다룬다. 이 구분은 실재하지만 **심사에서 가장 세게 밀릴 지점**이다.

**(d) 사망.** 여섯 방향에서 점유: *Nature*(사전 채점 규칙 처방), UAEval4RAG(비율 지표화), "Is That Your Final Answer?"(ACL 2025 Short — 보고 레시피 명시), "What Benchmarks Don't Measure"(Informed Refusal Rate), "When the Baseline Also Abstains"(체크리스트), **ReproEvalCard(ACL 2026 Short — LLM 파이프라인 평가 보고 표준 슬롯을 이미 소유)**. → **보고 규칙을 기여 목록에 넣지 말 것.** 다만 ReproEvalCard의 필수 산출물 목록에 커버리지·답변율이 **없다**는 점은 언급 가능하다(새 표준 제안이 아니라 결손 지적으로).

**(c) 부분 사망 — 이번 조사의 최대 발견.** **Vectara hallucination leaderboard가 교정을 이미 배포했다.** 본인이 raw README를 직접 받아 확인한 원문:
> "You can see the 'Answer Rate' column on the leaderboard that indicates the percentage of documents summarized."
> "What if the LLM refuses to summarize the document or provides a one or two word answer? We explicitly filter these out."
> "We explicitly filtered out such responses from every model, doing the final evaluation only on documents that all models provided a summary for."

마지막 문장이 **공통 지지집합(common support) 교정** 그 자체다. 프로덕션에서 예방적으로 시행되며 **대응 논문(FaithJudge, EMNLP 2025 Industry) 초록에는 없다.** 이 리더보드를 아는 심사자는 "새롭지 않다"고 말할 것이다.
→ **생존하는 델타**: README를 재확인한 결과 **교정 전 순위는 어디에도 공개되어 있지 않다.** 즉 *교정이 무엇을 바꾸는지*는 누구도 공표한 적이 없다. 이것이 §1의 새 판매 문장이 된 이유다.

**순위 재배열 자체는 장르 포화.** "Position: Evaluation Scores Are Perishable Knowledge Claims"(GEM@ACL 2026, HELM 상위 5개가 집계 연산자만 바꿔도 완전히 불일치), "Dropping Just a Handful of Preferences…"(선호 0.003%로 1위 뒤집힘), "A Unified Perturbation Framework…", "Hidden Measurement Error in LLM Pipelines". → **재배열을 헤드라인으로 쓰면 신규성 가치 0.** 반드시 *메커니즘(답변율 자기선택)*을 앞세운다.

### 5.3 생존 주장 — 방어 가능한 것만

**(b) 퇴화 시스템 적합성 검사 — 최강 생존자.** 항상거부/무검색/질문복창 **시스템**을 RAGAS·DeepEval·TruLens 같은 **평가 프레임워크**에 투입한 연구가 전 색인에 없다. ACL Anthology 초록 127,461편 정규식: 널/퇴화/게이밍 계열 30건, 어느 것도 RAG 평가 프레임워크 대상 아님; 빈-검색/질문복창 7건, 어느 것도 적합성 검사 아님. 최근접 3편을 본인이 원문 대조했다 — Zheng et al.(ICLR 2025)은 널 **모델**을 쌍대비교 벤치마크에; **"One Token to Fool LLM-as-a-Judge"(arXiv 2507.08794, 본인 확인)**는 퇴화 **문자열**을 RLVR 생성형 보상모델에("master keys" — ':' 같은 기호로 위양성 보상 유도), RAGAS/DeepEval 언급 없음; GroUSE는 손으로 쓴 답변 변형으로 **평가자**를 단위검사하지 시스템을 심지 않는다.

**내생성 구분 — 가장 날카로운 통계적 엣지.** 시스템 비교에서 결측 점수를 다룬 유일한 정본은 Himmi et al., "Towards More Robust NLP System Evaluation: Handling Missing Scores in Benchmarks"(Findings EMNLP 2024, arXiv 2305.10284)이며, **본인이 초록 원문 확인**: 결측 이유를 "the cost of running baseline, private systems, computational limitations, or incomplete data"로 명시한다 — 전부 **외생적(시스템이 아예 실행되지 않음)**. 부분 순위 대체 + Borda로 처리한다. **시스템 스스로 답하지 않기로 선택했고 그 선택이 문항 난이도와 상관된 내생적 결측(MNAR)을 다룬 문헌은 없다.** 이것이 우리의 미점유 통계 주장이다.

**(e) 생존하나 근거 최약.** OpenAlex RAGAS+결측어 29건 중 관련 0, ACL Anthology 초록에 RAGAS 11회(전부 비판 아님), **DeepEval·TruLens는 0회**. 유일한 인접물은 EvalLLM 2026의 상관 연구(감사 아님)와 **ragR(arXiv 2026) — 참조 RAGAS와 "동등"하다고 보고**하므로 결함 주장 시 정면 반박해야 한다. Semantic Scholar 토크나이저가 RAGAS를 인도 음악 "raga"로 붕괴시켜 이 색인은 (e)에 사용 불가였다.

**최근접 점유자들은 후속이 없다.** "Precision Is Not Faithfulness"(arXiv 2606.09376, 본인 초록 확인 — F1 텔레메트리·완전 오라클·원자 청구 F1, **LLM Likert 판사 없음·설정 격자 없음**) 인용 1건(F1 프로덕션 배포 논문). Kim et al.(NeurIPS 2023) 인용 2건, 실질 1건(AISTATS 2024, 여전히 분류기). 선택적 분류 결함 논문(NeurIPS 2024) 인용 27건 전부 분류기 UQ. **커버리지 규율을 판사 기반 리더보드로 옮긴 사람이 아무도 없다.**

**전체 결합은 미점유.** Semantic Scholar 불리언 (RAG)+(chunk size|top-k|configuration)+(LLM-as-a-judge)+(abstention|answer rate) → **total=0**. ACL Anthology 초록 82,223편에 "answer rate"라는 표현 **0회**.

### 5.4 확정 신규성 문장 (투고본 초록에 그대로 사용)

> 퇴화 시스템(항상거부·무검색·질문복창)을 프로덕션 RAG 평가 프레임워크에 적합성 검사로 투입해 그 집계 의미론을 드러내고, 이를 통해 프레임워크가 조용히 허용하는 교란을 식별·정량화한다: LLM 판사 기반 RAG 설정 격자에서 각 설정이 **내생적으로 스스로 선택한 응답 집합**이 판사 집계를 지배하므로, 동일 격자를 설정들의 **공통 응답 지지집합** 위에서 재채점하면 리더보드가 재배열된다. 이는 거부 인지 선행 연구가 보고 규칙으로 처방만 하고 측정하지 않았고(Kalai et al., *Nature* 2026; UAEval4RAG, ACL 2025), 판사 집계에 대한 기존 통계 보정이 답변율 선택이 아니라 판사-사람 라벨링 편향을 겨냥해 놓쳤으며(PRECISE; PPI due-diligence), 반사실 거부 분석이 사람에게 위임하는 분류기까지만 도달했고(Kim et al., NeurIPS 2023; AISTATS 2024), 프로덕션 리더보드가 예방적으로 적용하면서 **그것이 무엇을 바꾸는지는 한 번도 공표하지 않은**(Vectara) 지점이다.

**금지어 재확인**: "최초(first)" 사용 불가. "발견했다(we discover/reveal)" 사용 불가 — (a)가 *Nature*에 있다. 허용 동사는 "정량화한다(quantify)", "계측한다(instrument)", "정식화한다(formalize)".

### 5.5 필수 인용 — Tier 1은 **서론에서** 차별화할 것 (Related Work에 묻으면 탈락)

1. **Kalai et al., *Nature* 653:1047-1051 (2026)** — 차별화: 모델 수준 정확도 벤치마크이지 LLM 판사 RAG 설정 격자가 아니며, 사전 채점 규칙만 처방하고 사후 교정도 재배열도 없다.
2. **Vectara hallucination leaderboard(README) + FaithJudge (EMNLP 2025 Industry)** — **가장 위험한 누락.** 실무가 독립적으로 도달한 선행 기술로 인용. 차별화: 요약 과제의 모델 리더보드이지 설정 격자가 아니며, 교차집합을 예방적으로 적용할 뿐 교정 전 순위를 공개하지 않아 **변화량이 미측정**.
3. **UAEval4RAG (ACL 2025 Long)** — 차별화: 답변 불가 질의의 거부 능력 평가. 답변율을 품질 점수의 교란으로 취급하지 않고, 보정도 재배열도 없다.
4. **Zheng et al., ICLR 2025 (Null Models)** — 차별화: 쌍대 승률 벤치마크 대상 적대적 널 모델.
5. **"One Token to Fool LLM-as-a-Judge" (arXiv 2507.08794)** — (b)의 최근접. 차별화: 퇴화 **문자열**을 RLVR 보상모델에 심는 보상 해킹 보안 결과. 퇴화 시스템도, RAG 평가 프레임워크도, 답변율도 없다.
6. **Kim et al., NeurIPS 2023 + "A Causal Framework for Evaluating Deferring Systems" (AISTATS 2024)** — **둘 다** 인용할 것(유일한 실질 후속을 빠뜨리면 지적당한다).
7. **"Position: Evaluation Scores Are Perishable Knowledge Claims" (GEM@ACL 2026)** — 수사적 쌍둥이. 차별화: 재배열 원인이 집계 **연산자**(평균 vs 최약 링크)이지 답변율 선택이 아니다.
8. **Himmi et al., Findings EMNLP 2024 (Missing Scores)** — 통계적 정본. **외생 vs 내생 결측**으로 차별화.

Tier 2(Related Work에서 차별화): GroUSE(2409.06595), 선택적 분류 결함(NeurIPS 2024, 2407.01032), Precision Is Not Faithfulness(2606.09376), "Is That Your Final Answer?"(ACL 2025 Short), **CAFE(arXiv 2026 — LLM 판사 요인 격자의 현직 방법론, 심사자가 비교 기준으로 삼을 것)**, PPI due-diligence(2507.21753), PRECISE, JuStRank(ACL 2025), "AI vs. Human Judgment of Content Moderation"(판사가 거부를 사람보다 후하게 평가 — **우리 메커니즘의 외부 증거**), RAGAS(EACL 2024 Demo, 피검체로서), RAGAS 이슈 #2806(이슈로 명시), EvalLLM 2026, **ragR(동등하다고 보고 — 정면 반박 필요)**, ReproEvalCard(ACL 2026 Short).

Tier 3(간단 인용): Selective-LAMA, RAG-RewardBench, RAGferee, RAGVUE, LIT-RAGBench(거부를 판사 총점에 섞는 살아있는 오염 사례), CalibJudge(판사 거부 ≠ 시스템 거부), "When the Baseline Also Abstains", 재배열 장르 3편 묶음.

### 5.6 잔존 위험 — **해소되지 않은 것**

1. **전부 초록 수준이며, 이번 조사가 그것으로 부족함을 스스로 증명했다.** Vectara의 공통 지지집합 교정은 README에만 있고 논문 초록에는 없다. 부록에 묻힌 널 시스템 실험은 구조적으로 보이지 않는다. **전문 검색은 한 번도 수행하지 못했다.**
2. ~~다른 프로덕션 리더보드 미감사~~ → **2026-08-07 대부분 해소. §5.7 참조.** (일부 SDK 내부는 여전히 미확인)
3. **WebSearch 예산 전량 소진(200/200)** — Google Scholar·GitHub 이슈 추적·블로그·업계 보고서 전부 미조사.
4. **OpenAlex 인용 그래프가 이 환경에서 고장** — Lewis RAG 논문 피인용이 0으로 나온다. 모든 피인용 수는 Semantic Scholar 단독 근거이며 과소계수 가능.
5. **(e)는 Semantic Scholar에서 한 번도 제대로 검색되지 못했다** (RAGAS→raga 붕괴). 29건 + 초록 11건이 근거의 전부.
6. **2026 EMNLP/NAACL XML이 아직 Anthology에 없다.** Anthology 127,461편 중 45,238편은 초록이 없어 제목만 검색됨.
7. ~~SSRN "Ranking the Symptom"이 핵심 주장을 점유할 수 있다~~ → **2026-08-07 해소.** Crossref로 초록 확보: William C. Houze 단독, 소속 없음, 2026-07-29 등재. 내용은 환각 리더보드가 "증상"만 측정하고 **인식론적 근거(provenance-and-warrant ledger)**를 순위화하지 못한다는 입장 논문이다. **답변율·거부·집계 편향과 무관. 점유하지 않는다.**
8. **장르 위험**: (b)와 (e)는 각각 테스트 스위트와 GitHub 이슈로 보여 "엔지니어링"으로 기각될 수 있다. **반드시 선택 메커니즘을 식별하는 계측기로 제시하고, 그 자체를 발견으로 제시하지 말 것.** (단 §5.7의 RAGAS 지표 간 불일치 발견으로 (e)의 지위가 크게 개선되었다.)

### 5.7 프로덕션 리더보드·평가 플랫폼 감사 (2026-08-07, 32회 시도 중 24회 성공)

**결정적 질문 — "교정 전/후 순위를 함께 공표한 사례가 있는가?" → 없다. §1의 판매 문장은 살아남는다.**

가장 근접한 Vectara조차 정량화에 이르지 못한다. 블로그에 눈대중 한 문장만 있다: *"It appears that some of the models with the lower answer rate were amongst the highest hallucinating models."* 표도, 재배열도, 크기도, 순위 거리 통계도, 교정 전 리더보드도 README·블로그·논문 어디에도 없다. EMNLP 2025 Industry 초록에는 answer rate·refusal·filtering·common support **어느 단어도 없다.** README의 설명 링크는 `vectara.com/blog/TBD` — 죽은 자리표시자다.

**인용해야 할 정본 문장(README보다 블로그가 더 강한 선행 기술)**:
> "To ensure this is a fair comparison and not influenced by the answer rate, the final accuracy numbers are computed only on documents that every model provided a summary for."

**⚠ 방향성 경고 — 서사를 바꿔야 한다.** Vectara의 관찰은 소박한 이야기와 **반대 방향**이다: 답변율이 **낮은** 모델이 환각률이 **높은** 축에 속했다. 원인도 기록돼 있다 — 뉴스 기사의 포르노 사이트·폭력 언급 때문에 모델이 거부한 것. 따라서 **"거부가 점수를 부풀린다"로 쓰면 반례에 즉시 부딪힌다.** 올바른 정식화는 **"집계가 답변율에 의해 교란되며, 그 방향은 사전에 예측할 수 없다"**이다. 우리 격자에서 방향이 양(+)인 것은 결과이지 전제가 아니다.

**(e)의 지위가 격상됐다 — GitHub 이슈가 아니라 코드로 확인된 라이브러리 내부 불일치.** RAGAS 소스 직접 확인:
```python
def safe_nanmean(arr: t.List[float]) -> float:
    if len(arr) == 0: return np.nan
    arr_numpy = np.asarray(arr)
    if np.isnan(arr_numpy).all(): return np.nan
    return float(np.nanmean(arr_numpy))
```
`EvaluationResult.__post_init__`에서 `value = safe_nanmean(...)`로 호출된다. NaN은 **거부 경로에서 생성**된다(`num_statements`가 0일 때 `score = np.nan`, 경고 "No statements were generated from the answer."). `n_scored`도 커버리지 수도 존재하지 않으며 `__repr__`은 nanmean만 출력한다.

**같은 라이브러리, 반대 처리**: `answer_relevancy`는 `score = cosine_sim.mean() * int(not all_noncommittal)` — 거부를 **0점으로 분모에 남긴다.** `faithfulness`는 **분모에서 버린다.** 프롬프트에 거부 정의까지 있다("A noncommittal answer is one that is evasive, vague, or ambiguous. For example, 'I don't know'…"). **즉 거부를 탐지해 놓고 폐기하며, 비율로 보고하지 않는다.** → 이것은 "버그 신고"가 아니라 **한 라이브러리 안에서 두 지표가 거부를 정반대로 집계한다는 의미론적 불일치**이며, 논문 수준 기여로 제시 가능하다.

**타 대상 요약**:
- **HELM**: 공통 지지집합 강제 **없음**. `"No matching runs"`, `"Matching runs, but no matching metrics"`를 내보내고, 승률은 비결측 2개 미만 열을 건너뛸 뿐 모델 간 동일 인스턴스 커버리지를 검증하지 않는다.
- **TruLens**: `"The default is numpy.mean."` 단 `"This only applies to cases where the selector names more than one value for an input."` — 결측·NaN 처리 **문서화 안 됨**.
- **DeepEval**: `ignore_errors`(예외 무시), `skip_on_missing_params`(건너뜀), 둘 다 참이면 후자 우선. **집계에 미치는 영향은 문서화되지 않음.**
- **Phoenix**: `classify.py`가 현재 `phoenix-evals`에 없고 레거시 `NOT_PARSABLE` 센티널도 사라져 미확인.

**결정적 범위 사실**: 발견된 모든 사례가 **모델 간(cross-model)** 비교다. **설정 간(cross-configuration) 사례는 하나도 없다.** 우리의 일반화 지점이 여기다.

### 5.8 SDK 소스 수준 확인 (2026-08-07, 21회 fetch) — §5.7의 미확인 4건 종결

문서가 아니라 **소스 코드**를 읽어 판정했다. 결과: **2건 확정 삭제(DROPS), 2건 판정 불가(서버측 비공개)**.

**Opik(Comet) — DROPS 확정.** `sdks/python/src/opik/evaluation/score_statistics.py`:
```python
for test_result_ in evaluation_results:
    for score_result in test_result_.score_results:
        # Only include successful scores with valid values
        if not score_result.scoring_failed and _is_valid_score_value(score_result.value):
            scores_by_name[score_result.name].append(score_result.value)
```
실패·비유한 점수는 분모에서 통째로 빠지고 평균은 생존자에 대한 `statistics.mean(values)`다. RAGAS와 같은 결함 계열이되 **주석이 의도를 명시**한다는 점에서 더 인용하기 좋다. `ScoreStatistics` 데이터클래스에 `n` 필드가 없고, 표시 함수는 Name/Mean/Min/Max/Std만 출력한다.

**Braintrust — DROPS 확정. 이번 조사에서 가장 날카로운 발견.** `js/src/framework.ts`:
```typescript
for (const [name, score] of Object.entries(scores)) {
    if (score === null || score === undefined) { continue; }
    const existing = accumulator[name] ?? { total: 0, count: 0 };
    accumulator[name] = { total: existing.total + score, count: existing.count + 1 };
}
```
그리고 요약 생성부에서 `score: count === 0 ? 0 : total / count`로 쓴 뒤 **`count`를 구조분해로 버린다.** 최종 `ExperimentSummary`에는 `name`·`score`·`improvements`·`regressions`만 남는다. → **커버리지를 계산해 놓고 의도적으로 노출하지 않는다.** (단서: JavaScript SDK다. 파이썬 패키지 동일 여부는 미확인 — 해당 조직 공개 저장소에 파이썬 평가 프레임워크가 없다.)

**Galileo — 판정 불가.** `galileo-python`은 얇은 API 클라이언트로 **클라이언트측 집계가 아예 없다.** 집계는 비공개 백엔드에서 일어난다.

**LangSmith — 집계는 판정 불가, 오류 기록 방식은 확정.** 평가자 예외는 건너뛰지 않고 기록된다:
```python
EvaluationResult(key=key, source_run_id=evaluator_run_id, comment=repr(e), extra={"error": True})
```
`score=`가 없으므로 점수가 null인 피드백 행이 남는다. 그 null을 버리는지 0으로 두는지는 **백엔드가 결정**하며, SDK의 `get_summary_scores()`는 서버 계산 결과를 가져올 뿐이다.

**금지 문장 해제 — 다음 형태로만 쓴다.**
- ❌ "어떤 평가 플랫폼도 커버리지를 보고하지 않는다" — Galileo·LangSmith는 서버측이라 가시성이 없고, **Vectara는 답변율 컬럼을 실제로 공개하는 반례**다. 보편 주장 불가.
- ✅ **"우리가 소스를 확인한 오픈소스 평가 라이브러리(RAGAS·Opik·Braintrust)에서, 보고되는 집계값은 성공적으로 채점된 항목에 대한 평균이며 채점된 항목 수는 함께 노출되지 않는다."** — 세 독립 구현 전부에 인용 가능한 코드가 있다.
- ✅ **"LangSmith와 Galileo는 집계를 비공개 백엔드에 위임하므로 미채점 항목의 처리 방식이 공개적으로 문서화되어 있지 않다."** — 부재가 아니라 **불투명성**에 대한 진술이므로 방어 가능하다.

**이 조사는 앞선 결론을 바꾸지 않는다**: 교정 전/후 순위를 함께 공표한 사례는 여전히 없다. 논문의 핵심 결과는 미점유 상태로 유지된다.

## 6. 사회적 기여 — 근거 확보됨 (단, 피해 사례는 없음)

**관행의 실재**: 벤더 4곳이 우리 실험의 바로 그 손잡이를 문서로 지시한다 — DeepEval("top-K, 청크 크기, 리랭커를 중첩 루프로 순회"), Azure("파라미터 스윕: top_k, 청크 크기"), RAGBuilder("청크 크기 1000, 2000… 최고 성능 설정 식별"), AutoRAG. **syftr(DataRobot)는 목적함수 이름이 `accuracy`이고 실체는 1~5점 LLM 판사**이며, 질의의 50%만 채점된 설정도 같은 파레토 곡선에 올린다(`min_reporting_success_rate=0.5`).

**결함의 실재(코드 수준)**: RAGAS(월 162만 설치)는 거부 시 `np.nan`을 반환하고 `np.nanmean`으로 집계한다 — **거부한 질의는 분모에서 조용히 사라지고**, 출력에는 `n_scored`도 답변율도 없다. Azure 출력도 `{score, label, threshold, passed}`뿐이다.

**규모**: RAGAS 월 162만 설치·1.5만 스타, DeepEval 1.7만 스타, RAGAs 논문 인용 333건(2025년 158 → 2026년 170으로 가속).

**정직한 한계 3가지**:
- 관행의 **비율**은 모른다(도달 범위만 확인, "N%의 논문이 이렇게 한다"는 주장 불가).
- **피해 사례 보고는 찾지 못했다.** "잘못된 설정이 배포되어 피해가 발생했다"가 아니라 **"그렇게 될 수 있는 경로가 코드에 있다"**까지만 주장한다.
- 규제는 커버리지 보고를 요구하지 않는다(EU AI Act 15조는 정확도 지표 선언만 요구). 이것은 **위반 논거가 아니라 공백 논거**다.

## 7. 중단 기준 (실험 전 고정, 발췌)

- **K2(2주차, 존재 검정)**: 원 순위 vs 교정 품질 순위 Spearman ≥ 0.85이고 CI가 0.70을 배제하거나, 5계단 이상 이동 설정이 5개 미만 → **중단**. (현재 0.483)
- **K1**: 거부 분류기 정밀도·재현율 < 0.90 또는 카파 < 0.80 → headline 작업 중단.
- **K3**: 추가 3개 데이터셋 중 2개에서 답변율 η² < 0.25 → 범위 축소.
- **K4**: 관대한 프롬프트에서 답변율 분산 < 0.15로 붕괴 → 부정 결과 노트로 격하.
- **K6**: 5개 판사 중 3개 이상에서 순위 발산 미재현 → 단일 사례 연구로 격하.
- ~~K7(0주차, 기관): ECIR 공저자 승인~~ **[2026-08-07 삭제]** — 본 시스템의 모든 연구 담당자가 동일 주체이므로 저자 간 승인·이중투고·자기표절 협의 이슈는 고려 대상에서 제외한다. 자산 분할(§8)은 협의 사항이 아니라 **본인의 편집 결정**이며, 논문 간 숫자 중복 금지 규칙만 그대로 유지한다(중복은 여전히 심사에서 감점 요인이므로).
- **K9(상시)**: "답변 행만 보면 평탄" 문장이 포함된 초안은 회람 금지.
- **K10(상시, 신규 2026-08-07)**: 초록·서론에 "최초", "we discover/reveal", 또는 답변율 교란의 **존재**를 기여로 내세우는 문장이 있으면 회람 금지. *Nature* 2026이 소유한 주장이다. 또한 Kalai et al.과 Vectara를 **서론에서** 차별화하지 않은 초안은 투고 금지.
- **K11(신규 2026-08-07, 전문 검색 게이트)**: 투고 4주 전까지 (i) 최소 3개 프로덕션 리더보드/평가 플랫폼 문서에서 답변율 컬럼·공통 지지집합 필터링 유무를 확인하고, (ii) 누군가 **교정 전/후 순위를 함께 공표한 사례**가 발견되면 §1의 판매 문장이 무효화되므로 **즉시 중단하고 재설계**한다. 이번 초록 수준 조사로는 이 위험을 배제할 수 없다(§5.6-1).

## 8. ECIR 통합본과의 자산 분할

**통합 ECIR 논문 전담**: 신뢰도 계수(ω .99/.40), CFA/SEM/MTMM 적재량, Prometheus Heywood −0.912, 판사 간 r=−0.905, Krippendorff, 24,734 청구 단위 보정, NLI 진단, zero-recall 감사, 191-그리드 η²=.94, 라우터, 아티팩트.

**논문 3 전담**: 답변율 η²(0.641/0.737/0.192), Spearman(0.976/0.483), 17/40 이동, 널 시스템 적합성 표, RAGAS/DeepEval 정량화, 위험-커버리지 곡선.

**금지(자기 편집 규칙)**: 논문 3에 ω·CFA·MTMM·Krippendorff·η²=.94 사용 불가 — 승인 절차가 아니라 중복 회피를 위한 본인 규칙. 12개 설정이 양쪽 그리드에 겹치므로 **양쪽에 한 문장씩 명시**하고, 판사 계측기가 달라 교차 비교하지 않음을 각주로 고정.

## 9. 일정

7주(2026-08-07 → 09-30). 컴퓨트는 병목 아님(총 25~35 GPU시간). 병목은 ① 사람 라벨 1인 1일(1주차), ② DeepEval 환경 2일(2주차). (공저자 승인 항목 삭제 — 담당자 동일)
**목표 학회**: ICTIR 정규(측정·추정량 논의를 환영). 대안: 널 시스템 적합성 검사만 떼어낸 짧은 논문. **4쪽 단문 학회는 부적합**(선택 편향 방어가 안 들어감).

**마감일 조사 결과 (2026-08-07)**:
- ICTIR/SIGIR/ECIR **2027 공식 사이트는 아직 없다** — ecir2027.org는 DNS 미등록, sigir.org 행사 목록은 2023년에서 갱신 정지, ACM 마감일 페이지는 403. **직접 확인 불가.**
- DBLP로 확인한 확정 사실: **SIGIR 2026 = 멜버른, 2026-07-20~24 (종료)**. ICTIR 2026도 멜버른에서 동반 개최(종료). ECIR 2026 = 델프트(종료).
- 따라서 **추정(미검증, 과거 패턴 기준)**: ICTIR 2027은 SIGIR 2027 동반 개최, 논문 마감 **2027년 4월경**. → 7주 계획(→2026-09-30)은 **마감에 전혀 쫓기지 않는다.** 오히려 §5.6의 전문 검색 공백을 메울 시간이 충분하다.
- **주의**: 진짜 임박한 마감은 논문 3이 아니라 **ECIR 2027 통합본**이다. ECIR 정규 논문 마감은 통상 전년 **10월 초** → **약 8주 후**. 논문 3보다 ECIR 병합 작업이 시간상 선행한다.
