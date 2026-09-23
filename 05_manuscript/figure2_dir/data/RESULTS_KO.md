# Qwen-aligned 순환성 통제 주입

- 동일 공간: Qwen3-VL-Embedding-2B, 2,048d
- 동일 workload: 주 91-config 격자와 같은 522 canonical, 3,000 clips / 85 queries
- clean/full/query를 한 model session에서 재임베딩
- 성격: post-pilot 통제 주입; 사전등록 아님

| 실험 | clean semantic nDCG@10 | treatment | treatment nDCG@10 | Δ [query 95% CI] | cluster 95% CI |
|---|---:|---|---:|---:|---:|
| C1 | 0.181005 | oracle qrel filter | 1.000000 | +0.818995 [+0.780200, +0.855287] | [+0.737950, +0.881682] |
| C2 | 0.181005 | full document contamination | 0.853687 | +0.672682 [+0.626129, +0.718190] | [+0.567532, +0.752005] |

C1의 oracle=1은 qrel 자체를 후보 집합으로 사용한 구성상 상한이다. C2는 corpus/query/qrels/model을 고정하고 문서에 정답 정의 문장만 추가한 효과다. 두 결과 모두 순환 경로가 이 workload의 측정치를 부풀릴 수 있음을 보이지만, 과거 시스템 성능 차이 전체를 순환성에 귀속하지 않는다.
