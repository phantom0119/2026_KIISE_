# EXP05 — 검색 증거의 VLM-QA 전파

- 대응 질문: RQ6
- 상태: 증거 사다리·다중 시점 완료, 색인→답변은 사전 게이트에 따라 정직 종결
- 결과 지위: evidence 품질 효과는 유지 관찰, 전파 경계는 조건부 음성 결과 [정정 2026-07-28: 제출 논문 paper_final.pdf §5.2.6은 근사 색인 재현율 차이의 답변 전파를 "표본 부족으로 탐색적(미확립)"으로 서술한다. 대외 주장은 이 표현을 따른다.]

## 1. 목적

검색 지표가 좋아졌다는 이유만으로 최종 VLM 답변도 좋아진다고 주장하지 않고, 다음 인과 사슬을 단계별로 검사한다.

```text
index/search treatment
  → 실제 evidence 회수 변화(mediator)
  → 고정 VLM이 evidence 차이를 지각
  → 편향되지 않은 질문에서 answer 변화
```

세 단계 중 하나라도 실패하면 index 효과를 answer 품질로 확대하지 않는다.

## 2. 실험 A — VRU 증거 사다리

### 2.1 설계

- 600개 다지선다 문항, 무작위 정확도 0.25
- 조건당 n=600
- top-3 captions
- temperature=0 greedy
- 같은 모델 안에서 evidence condition만 변경
- 생성기: Qwen2.5-7B, Llama-3-8B

### 2.2 처리군

| 조건 | 공급 증거 |
|---|---|
| closed | 질문과 선택지만 제공 |
| distractor | 무관 clip의 caption |
| vector-only | dense top-3 captions |
| prefilter | metadata 후보 제한 후 dense top-3 |
| oracle | 정답 clip의 caption |

prefilter 후보 수 중앙값은 29 clips다.

### 2.3 결과

| evidence | Qwen2.5-7B | Llama-3-8B |
|---|---:|---:|
| closed | 0.3083 | 0.3067 |
| distractor | 0.5383 | 0.5283 |
| vector-only | 0.6650 | 0.6650 |
| prefilter | 0.6800 | 0.6667 |
| oracle | 0.7467 | 0.6900 |

두 생성기 모두 `closed < distractor < vector-only ≤ prefilter < oracle` 순서를 보인다. 다만 prefilter−vector-only는 Qwen +0.0150, Llama +0.0017로 작으므로 검색 전략의 답변 우위를 주장하는 핵심 근거로 쓰지 않는다. 증거 유무·품질의 큰 격차가 핵심이다.

## 3. 실험 B — 다중 시점 evidence selection

### 3.1 설계

- AI Hub 다각도 CCTV
- 전체 평가 400 events, bbox 비대칭 핵심 stratum 250
- 사건과 질문을 고정하고 better view, worse view, both view를 비교
- 동일 prompt hash
- 모델: Qwen2.5-VL, Qwen2-VL, InternVL3-8B, Idefics2-8b 보조
- better−worse paired test
- both와 better의 TOST equivalence

### 3.2 결과

| model | both accuracy | better−worse | p | both≈better |
|---|---:|---:|---:|---:|
| Qwen2.5-VL | 0.2000 | +0.056 | 0.0016 | equivalent |
| Qwen2-VL | 0.3025 | +0.152 | 0.0002 | equivalent |
| InternVL3-8B | 0.2450 | +0.084 | 0.0002 | equivalent |
| Idefics2-8b | 0.1450 | +0.044 | 0.0256 | equivalent, marginal |

세 주 모델에서 better view가 worse view보다 유리하고 both는 better와 등가다. evidence packet은 clip ID만이 아니라 더 나은 시점·프레임 선택을 포함해야 한다. Idefics2는 chance 0.091에 가까워 보조 근거다.

## 4. 실험 C — ANN에서 답변으로의 전파 게이트

### 4.1 Gate 1: 1K caption

- VRU 1K captions
- 27 index configurations
- mediator: exact 대비 evidence-recall@3
- 관측 범위: 0.974–1.053
- 판정: manipulation FAIL

소형 코퍼스와 과밀 evidence에서 index parameter가 실제 공급 증거를 바꾸지 못했다. 사전 규칙에 따라 12–20 GPU-hour 본 VLM 실험을 시작하지 않았다.

### 4.2 Gate 2: 143K frame

- 522 visual 143K frames
- moment groups: 31,380
- mediator: moment-recall@3
- exact 0.1203
- mid HNSW relative 0.807
- strong IVF-PQ relative 0.451
- 판정: manipulation PASS

### 4.3 VLM mini-pilot

- 360 calls
- 주석 gold의 3 binary questions
- class balance 50/50
- exact vs strong degradation

결과:

- mediator hit rate 0.1222→0.0556
- accuracy given hit 0.5625
- accuracy given no-hit 0.5823
- hit−no-hit leverage -0.020, CI 약 ±0.13
- exact−strong answer accuracy +0.028
- paired disagreement 0.206

evidence 조작은 성공했지만 VLM이 미세한 448px CCTV 장면 차이를 답변에 활용하는 지렛대를 검출하지 못했다. 사전 중단 규칙에 따라 대규모 호출을 중단했다.

### 4.4 강 생성기 프로브

well-posed 질문에서 oracle accuracy 0.72로 지각 벽이 일부 완화됐다. 그러나 이진 질문은 yes-bias에 오염됐다. 전파가 관측되려면 질문·답변 분포까지 비오염이어야 한다.

## 5. 세 경계

| 경계 | 실패 조건 | 현재 관찰 |
|---|---|---|
| mediator/scale | index가 evidence를 바꾸지 않음 | VRU 1K에서 실패 |
| perception | evidence가 달라도 VLM이 사건을 구분하지 못함 | 522 143K mini-pilot |
| task/answer bias | 질문 형식·정답 분포가 모델 편향에 지배됨 | binary yes-bias |

전파 효과를 확증하려면 세 경계를 동시에 넘어야 한다. [정정 2026-07-28: 확정 용어에서 RQ6 3관문은 "관련 클립 회수(경계 1)→검색 문맥 인식(경계 2)→과제 편향(경계 3)"으로 부른다. 보고서·개정 원고에서는 이 명칭을 사용한다.]

## 6. 결과 지위와 허용 주장

### 허용

- 적절한 검색 증거는 closed-book보다 답변 정확도를 높인다.
- 무관 증거보다 정상 검색·oracle 증거가 더 유리하다.
- 다중 시점에서는 모든 view의 축적보다 better-view 선택이 중요할 수 있다.
- ANN 차이가 답변으로 전파되려면 mediator, perception과 task-bias 조건을 모두 만족해야 한다.
- 사전 게이트와 중단 규칙이 불필요한 GPU 호출과 과장된 결론을 막았다.

### 금지

- prefilter의 검색 우위가 답변에 강하게 전파됐다고 주장하지 않는다.
- mini-pilot을 “효과가 정확히 0”인 증명으로 쓰지 않는다.
- 다각도 CCTV에서 모든 추가 view가 무의미하다고 일반화하지 않는다.
- bbox 면적을 실제 visibility/occlusion ground truth라고 부르지 않는다.
- Idefics2를 강한 독립 재현으로 사용하지 않는다.
- 검색 nDCG 또는 ANN recall 상승이 VLM-QA 향상을 보장한다고 쓰지 않는다.

## 7. 원자산

- 증거 사다리:
  - `2026_KIISE/experiments_expansion/rag_vqa/results_full/summary_qwen.json`
  - `2026_KIISE/experiments_expansion/rag_vqa/results_full/summary_llama3.json`
  - 같은 디렉터리의 answer parquet
- 다중 시점:
  - `2026_KIISE/project_md/410_METHOD_prereg_multiview_answer_level_20260708.md`
  - `2026_KIISE/project_md/610_RESULTS_multiview_four_vlm_recheck_20260709.md` [정정 2026-07-28: `project_md/archive/legacy_premerge_20260728/`로 이관 — 본 문서 "레거시 결과 문서 흡수" 섹션 참조]
- ANN→answer:
  - `2026_KIISE/paper_assets/20260710_pillarB/e1_pilot_configs.csv`
  - `2026_KIISE/paper_assets/20260711_e1a/`
  - `2026_KIISE/paper_assets/20260713_index_answer/gmanip_gate.json`
  - `2026_KIISE/project_md/630_RESULTS_answer_coupling_closure_20260711.md` [정정 2026-07-28: `project_md/archive/legacy_premerge_20260728/`로 이관 — 본 문서 "레거시 결과 문서 흡수" 섹션 참조]

## 8. 변경 시 재실행 조건

- evidence condition 또는 top-k 변경
- QA question/choice 분포 변경
- generator snapshot·prompt·decoding 변경
- frame 해상도·view selection 기준 변경
- mediator 정의 변경
- index configuration ladder 변경
- gate threshold·SESOI·중단 규칙 변경

## 레거시 결과 문서 흡수 (2026-07-28)

SYNC 기준: `manuscript/paper_final.pdf`(2026-07-23 제출본, 총 21쪽=접수양식 1쪽+본문). RQ6 정본 서술 — 답변 정확도 31%(무증거)→53%(무관)→67%(벡터 검색)→75%(대상 설명문); 잘 보이는 단일 시점 +15.2%p, 두 시점 동시 무이득; 근사 색인 재현율 차이의 답변 전파는 표본 부족으로 탐색적(미확립).

### 610_RESULTS_multiview_four_vlm_recheck_20260709.md

(a) 한 줄 요약: 4-VLM 다중 시점 answer-level 결과의 최종 재검증 감사 — 산출물·manifest·수치 정합을 확인하고 초안 원고 2건(그림 6 캡션 완화, 모델 표 보강)을 즉시 수정한 기록.

(b) EXP 본문에 없는 고유 정보:
- 결과 디렉터리 4종과 스냅샷 해시: `multiview_answer_vlm_qwen25vl_400`(cc594898…), `multiview_answer_vlm_qwen2vl_400`(eed13092…), `multiview_answer_vlm_internvl3_400`(259a3b64…), `multiview_answer_vlm_idefics2_400`(2c426865…). 4개 모두 동일 prompt hash `b236a9f…` — 모델 간 prompt 차이 없음의 근거.
- 디렉터리별 보유 파일 3종: `vlm_answers.parquet`, `eval/multiview_answer_report.json`, `run_manifest.json`.
- gate 판정 열: 3주 모델 pass, Idefics2-8b pass/marginal.
- 재현성 각주: Qwen2.5/Qwen2의 `run_manifest.json`은 사후 reconstructed manifest(원실행 자동 기록 아님).
- symmetric control은 일부 class 표본이 작아 보조 대조군 한정.
- 초안 수정 이력: 그림 6 캡션 "metadata-aware 우위가 답변까지 전파" 제거→"evidence 품질 상승에 따른 답변 정확도 상승"으로 완화; 모델 표에 InternVL3-8B·Idefics2-8b 추가 및 Idefics2 참고문헌 [22] 추가; 2026-07-09 DBR review PDF(16쪽) 재생성.
- 금지 문장 목록 중 EXP §6에 없는 2건: "두 view에 상보 정보가 없다", "VLM이 CCTV event class를 전반적으로 잘 분류한다" — 금지 목록 확장분으로 유효.
- 인용 가능한 방어 문장 블록(bbox 면적 기반 시점 비대칭 조건 하 view evidence 공급이 답변 정확도를 유의하게 바꿈) 원문 보존.

(c) 상충과 정정:
- 문서의 표 20·그림 6/7·참고문헌 [19]-[22]·"16쪽" 등은 2026-07-09 시점 초안(`kiise_dbr_manuscript_v1_true_multimodal*`) 번호 체계다. 정본은 paper_final.pdf(2026-07-23, 총 21쪽)이며 다중 시점 결과는 §5.2.6(RQ6)에 "잘 보이는 단일 시점 +15.2%p(=Qwen2-VL better−worse +0.152), 두 시점 동시 무이득"으로 수록 — 구 번호·구 쪽수 인용 금지.
- 수치 표 자체(both_acc, better−worse, p, TOST)는 EXP §3.2와 완전 일치 — 수치 상충 없음.

(d) 아카이브 경로: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/610_RESULTS_multiview_four_vlm_recheck_20260709.md`

### 630_RESULTS_answer_coupling_closure_20260711.md

(a) 한 줄 요약: 색인 근사→답변 결합(E-1)의 2-스케일 정직 종결 기록 — 게이트 1 FAIL / 게이트 2 PASS / 미니 파일럿 중단 규칙 발동의 원 수치·프리레지 계보 정본.

(b) EXP 본문에 없는 고유 정보:
- 프리레지 계보: `420` §4 + Amendments 2·3·4; 스크립트 3종 `run_e1_manipulation_pilot.py`, `run_e1a_manipulation_pilot.py`, `run_e1a_vlm_minipilot.py`.
- 게이트 1 FAIL 원인 분해: evidence 과밀 334/1000 + 1K 규모에서 ANN≈exact.
- 게이트 2 config 명칭: mid=`hnsw_M8_ef1`(rel 0.807), strong=`ivfpq_m32_np8`(rel 0.451); moment group 31,380개의 evidence 중앙값 4.
- 미니 파일럿 질문별 절대 정확도(chance 0.5): bus 0.62–0.65 / stopped 0.57–0.60 / bikes 0.52–0.53≈chance — 448px 와이드샷 지각 한계의 질문 단위 근거.
- 검정력 계산: 쌍대 불일치율 0.206 기준 n=2,000이면 CI ±0.020 달성 가능했으나 지렛대 부재로 본실험 미착수.
- 파생 발견: 동일-카메라 배경 유사성으로 exact moment-recall@3가 12%에 그침 — 프레임 임베딩 단독 순간 검색의 구조적 한계(캡션 맹점과 짝을 이루는 채널 한계 시리즈).
- 게시 결정: E-2는 retrieval 패널만 게시(answer 패널 미게시).
- 결론 한정 명시: VLM 1종(Qwen2.5-VL)·질문 3종·448px 설정.

(c) 상충과 정정:
- "26-config 사다리" vs EXP §4.1 "27 index configurations": `e1_pilot_configs.csv` 실측 27행(첫 행 `flat_exact` 기준선 포함, rel 범위 0.9742–1.0526). exact 제외 ANN 사다리 26 + 기준선 1 = 27로 계수 관행 차이일 뿐 오류 아님. 통일 표기는 "기준선 포함 27 구성".
- "두 개의 벽" 프레임은 660 및 EXP §5의 "세 경계"(경계 3 답변-편향 신설)로 대체됨 — 구 프레임 인용 금지.
- "지렛대 부재로 본실험 무의미" 등 단정 표현은 정본 논문 §5.2.6의 "표본 부족으로 탐색적(미확립)" 서술로 완화해 인용(문서 자체의 정직성 주기도 "정확히 0이 아니라 크기 부재"로 이미 한정).

(d) 아카이브 경로: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/630_RESULTS_answer_coupling_closure_20260711.md`

### 660_GOAL3_regime_characterization_20260713.md

(a) 한 줄 요약: 목표 #3(구조→VLM-QA 전파)을 긍정 확증 대신 "세 경계" 체제 규명으로 확정하고 당시 v3 원고 §8.2로 승격한 종합 문서 — EXP §5 세 경계 표의 원 출처.

(b) EXP 본문에 없는 고유 정보:
- 경계 1 실측치: 522 143K에서 실제 filtered-ANN 구조가 양성-클립 재현율을 0.48 스프레드로 이동(prefilter 0.98 → postfilter K'1x 0.52); 자산 `paper_assets/20260713_index_answer/gmanip_gate.json`. EXP §4.2의 moment-recall 수치(exact 0.1203 등)와 별개의 실측이다.
- 경계 2 실측치: 동일 오라클 프레임의 물체-존재 질문에서 균형 정확도 Qwen2.5-VL 0.65 → InternVL3 0.72(EXP §4.4 "0.72"의 출처); "정지/정체" 질문은 단일 프레임 ill-posed로 세 VLM 모두 ~0.5 → 시간 정보 필요라는 질문-설계 경계; 자산 `paper_assets/20260712_perception_retest/PERCEPTION_RETEST.md`.
- 경계 3 실측치: InternVL3의 내용-유발 yes-편향 — distractor 프레임에 객체가 보이면 gold와 무관하게 64% "yes"; 판별력 distractor +0.009 vs oracle +0.452; 자산 `condb_internvl3.csv`; 경계 돌파 요건 = MC/값 질문(편향 회피) + per-target 답.
- 신규성 논거: 필터드-ANN/벡터DB 선행은 재현율에서 멈추고, RAG/VLM-QA 선행은 색인 구조를 조작 변수로 격리하지 않으며, 감시 VALU/UCA/ForeSea/UrBench는 모델 벤치마크 — 구조→VLM답변 전파의 체제 경계 규명은 선행 부재.
- 후속 경로: P8b(MC 확증)로 경계 3을 넘어 긍정 확증 재도전 가능(별도 프리레지·재검토 필요); 세 설계 kill(CC-FR·P8)을 문제 성질(retrieval-augmented VLM-QA의 4겹 오염)의 증거로 해석.
- 당시 검증 상태: F5 검증기 149/149(+8 경계 체크), DBR 20쪽 유지.

(c) 상충과 정정:
- "v3 원고 §8.2·표 12·§9·§11" 번호와 "DBR 20쪽"은 2026-07-13 초안 기준 — 정본 paper_final.pdf(2026-07-23, 총 21쪽)에서 해당 내용은 §5.2.6(RQ6)이며 지위는 "탐색적(미확립)". 구 절·표 번호 인용 금지(러닝 헤드 구제목 잔존 이슈와 동일 계열).
- 경계 명칭은 2026-07-28 확정 용어로 RQ6 3관문 = "관련 클립 회수→검색 문맥 인식→과제 편향" — 660의 스케일/지각(VLM 능력×질문)/답변-편향과 1:1 대응. 보고서·개정 원고에서는 확정 용어를 사용한다.
- 수치 상충 없음: 660의 rel 0.974–1.053, bikes 0.525, 0.72 등은 EXP 본문 및 630과 정합.

(d) 아카이브 경로: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/660_GOAL3_regime_characterization_20260713.md`
