# G1 판정 보고서 — 사전 등록 규칙(G1_DECISION_RULE.md) 적용

생성: 자동 (g1_analyze.py), bootstrap 5000회, SESOI 0.05

## 코퍼스 A

- 난이도 매칭 조작 확인: 1-Wasserstein=0.0058 (한계 0.1400) → 통과
- 자연 Post_Hardness: mean 0.571 std 0.280 / 매칭: mean 0.568 std 0.280

| method | R(자연) | R(매칭) | Δ_H [95% CI] | R(무작위) | Δ_R | 판정 기여 |
|---|---|---|---|---|---|---|
| postfilter_hnsw_K4x | 0.2621 | 0.2872 | -0.0251 [-0.0969,+0.0511] | 0.9033 | -0.6412 | X |
| single_stage_ivf_np8 | 0.2916 | 0.3221 | -0.0305 [-0.1254,+0.0743] | 0.9641 | -0.6725 | X |
| single_stage_ivf_np32 | 0.4614 | 0.5085 | -0.0471 [-0.1664,+0.0938] | 0.9985 | -0.5371 | X |

- 방법 순위(오름차순): 자연 ('postfilter_hnsw_K4x', 'single_stage_ivf_np8', 'single_stage_ivf_np32') / 매칭 ('postfilter_hnsw_K4x', 'single_stage_ivf_np8', 'single_stage_ivf_np32') → 동일

## 코퍼스 B

- 난이도 매칭 조작 확인: 1-Wasserstein=0.0024 (한계 0.0734) → 통과
- 자연 Post_Hardness: mean 0.307 std 0.147 / 매칭: mean 0.308 std 0.148

| method | R(자연) | R(매칭) | Δ_H [95% CI] | R(무작위) | Δ_R | 판정 기여 |
|---|---|---|---|---|---|---|
| postfilter_hnsw_K4x | 0.6402 | 0.6801 | -0.0399 [-0.1397,+0.0649] | 0.9475 | -0.3073 | X |
| single_stage_ivf_np8 | 0.7432 | 0.7727 | -0.0295 [-0.1282,+0.0744] | 0.9821 | -0.2389 | X |
| single_stage_ivf_np32 | 0.8713 | 0.8988 | -0.0275 [-0.0837,+0.0314] | 0.9977 | -0.1264 | X |

- 방법 순위(오름차순): 자연 ('postfilter_hnsw_K4x', 'single_stage_ivf_np8', 'single_stage_ivf_np32') / 매칭 ('postfilter_hnsw_K4x', 'single_stage_ivf_np8', 'single_stage_ivf_np32') → 동일

## 종합 판정

**G1 실패: 난이도 매칭으로 자연-합성 차이가 소멸 — 자연 워크로드 축 중단**

- SESOI 충족 방법 수: 0/6
- 순위 뒤집힘(두 코퍼스 일관): False