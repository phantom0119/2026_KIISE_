# 630_RESULTS — 색인근사→답변 결합(E-1): 2-스케일 정직 종결

실행: 2026-07-10~11 | 프리레지: `420` §4 + Amendments 2·3·4 | Asset: `paper_assets/20260710_pillarB/e1_pilot_configs.csv`, `paper_assets/20260711_e1a/{e1a_pilot_mediator.csv, e1a_locked_configs.json, e1a_vlm_minipilot.parquet}`
스크립트: `run_e1_manipulation_pilot.py` / `run_e1a_manipulation_pilot.py` / `run_e1a_vlm_minipilot.py`

## 질문

색인 근사(ANN recall<1)가 고정 생성모델의 **답변 정확도**까지 전파되는가? (RQ-ALC의 답변축; "end-to-end에서 색인이 중요하다"는 통념의 검증)

## 게이트 설계가 낭비를 막은 경로

| 단계 | 설정 | 판정 | 절약 |
|---|---|---|---|
| 게이트 1 (Amd.2) | VRU 1K 캡션, evidence-recall@3, 26-config 사다리 | **FAIL — 전 config rel 0.974–1.053** (evidence 과밀 334/1000 + 1K≈exact) | 12–20 GPU-h |
| 게이트 2 (Amd.3) | 522-visual **143K 프레임**, moment-recall@3(순간그룹 31,380, evidence 중앙값 4) | **PASS** — exact 0.1203; mid=hnsw_M8_ef1(rel 0.807)·strong=ivfpq_m32_np8(rel 0.451) | — |
| 미니 파일럿 (Amd.4) | 360 VLM콜, 3 이진질문(주석 gold, 50/50 균형) × {exact, strong} | **중단 규칙 발동** — 인과 지렛대 null | 12–20 GPU-h |

## 핵심 수치 (미니 파일럿)

- **인과 지렛대**: acc|mediator-hit **0.5625** vs no-hit **0.5823** → 지렛대 −0.020, CI ≈ ±0.13 (0 포함).
- 매개변수 조작은 성공: hit-rate exact 0.1222 → strong 0.0556 (게이트 파일럿 0.1203과 정합).
- VLM 절대 정확도(chance 0.5): bus 0.62–0.65 / stopped 0.57–0.60 / **bikes 0.52–0.53 ≈ chance** — 448px CCTV 와이드샷의 미세 장면 지각 한계.
- Δacc(exact−strong)=+0.028, 쌍대 불일치율 0.206 → n=2,000이면 CI ±0.020 달성 가능했으나 **지렛대 부재로 본실험 무의미**.

## 결론 (원고 서술 확정)

**색인 선택의 답변축 효과는 본 체제들에서 두 개의 벽으로 차단된다:**
1. **Mediator 벽 (소형 코퍼스)** — 1K-문서 RAG에선 어떤 색인 열화도 evidence 전달을 바꾸지 못한다(과밀 evidence + 소규모 ANN≈exact).
2. **Perception 벽 (대형 코퍼스)** — 143K에선 색인 열화가 evidence 전달을 절반으로 줄여도(0.12→0.06), 고정 VLM의 미세 장면 지각이 병목이라 정확도로 전달되지 않는다.

→ "index 결과를 end-to-end VLM-QA 성능으로 과장 금지"라는 기존 통제 규칙(구19·24·39)의 **실증 근거**. 색인 효과를 답변에서 보려면 두 벽을 모두 넘는 설정(중형 코퍼스 × 굵은-입자 질문 × 고해상 지각)이 필요함을 정량 제시 — 이는 향후 연구 경계 조건이지 본 논문의 미달이 아니다.

## 파생 발견 (독립 보고 가치)

- **동일-카메라 배경 유사성**이 CCTV 프레임 임베딩 검색의 구조적 한계: 형제 프레임이 타 순간 동일-카메라 프레임에 묻혀 exact moment-recall@3가 12%에 불과 — "프레임 임베딩만으로 순간 검색"의 한계 정량화(캡션 맹점 발견과 짝을 이루는 문서/시각 채널 한계 시리즈).
- E-2는 **retrieval 패널만 게시** 확정(answer 패널 미게시 — 데이터가 지지하지 않음).

## 정직성 주기

- 모든 판정은 사전등록된 게이트·중단 규칙의 기계적 적용(사후 재량 없음). 미니 파일럿 n=360의 지렛대 CI(±0.13)는 넓다 — "지렛대가 정확히 0"이 아니라 "본실험을 정당화할 크기의 지렛대가 부재"가 정확한 서술.
- VLM 1종(Qwen2.5-VL)·질문 3종·448px 설정에 한정된 결론.
