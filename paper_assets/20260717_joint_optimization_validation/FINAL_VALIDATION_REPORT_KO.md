# 저장·검색·색인 공동 최적화 검증 최종 보고서

- 상태: **실험 완료 / metric·무결성 32/32 + treatment·통계 12/12 PASS**
- 완료일: 2026-07-17 KST
- 주 데이터: AI Hub 522 교차로 3,000 clips, 85 queries
- 외부 데이터: MEVA 985 clips, 193 queries
- 통제 encoder: Qwen3-VL-Embedding-2B, 2,048차원
- 통합 격자: 4개 저장 표현 × 호환 검색 계획 × 7개 색인 설정 = 91 configurations

## 1. 무엇을 새로 검증했는가

기존 저장 비교는 caption에 BGE-M3, frame에 CLIP을 사용했기 때문에 저장 단위와 encoder 효과가
분리되지 않았다. 이번 실험에서는 query text, Qwen3.5 caption, representative frame, multi-frame을
모두 동일 Qwen3-VL-Embedding-2B 공간에 배치했다. 이후 같은 질의·정답·metadata에서 저장 표현,
filter placement, 색인 구조만 교차했다.

유효하지 않은 조합은 배제했다. 예를 들어 lexical hybrid는 caption 저장에만 적용했고,
frame-only 저장에 BM25를 억지로 결합하지 않았다. IVF/PQ는 모든 규모에서 centroid당 최소 39개
학습 벡터 조건을 만족하도록 nlist를 제한했다.

## 2. 동일 encoder 저장 표현 결과

522의 Flat/B2 semantic nDCG@10:

| 저장 표현 | semantic nDCG@10 | strict nDCG@10 | 직렬화 Flat 색인 |
|---|---:|---:|---:|
| caption | 0.1810 | 0.0626 | 24.58 MB |
| representative frame | 0.1865 | 0.0625 | 24.58 MB |
| multi-frame | **0.3518** | **0.1014** | 68.40 MB |
| dual caption+multi | 0.2933 | 0.0889 | 92.97 MB |

Multi-frame − caption semantic 차이는 +0.1708, query bootstrap 95% CI
[+0.0989, +0.2399], intent×facet cluster bootstrap CI [+0.0178, +0.3162]였다.
Strict 차이는 +0.0387, query CI [+0.0047, +0.0730], cluster CI [+0.0037, +0.0762]였다.

다만 storage family의 BH 보정 후 cluster q-value는 semantic 0.0852, strict 0.0888이다.
따라서 동일 encoder에서도 multi-frame의 큰 점 추정치와 paired-query 증거는 확인됐지만,
군집 family-wise 0.05 유의까지 충족했다고 과장하지 않는다. Representative frame과 caption 차이는
두 scoring 모두 신뢰구간이 0을 포함했다.

## 3. 검색 계획 결과

Multi-frame/Flat에서 B4 prefilter는 strict nDCG@10을 B2 0.1014에서 0.2625로 높였다.
차이 +0.1612의 query CI는 [+0.1289, +0.1952], cluster CI는 [+0.1048, +0.2093]이다.

반면 semantic nDCG@10은 B2 0.3518에서 B4 0.2586으로 낮아졌다. 차이는 -0.0932,
query CI [-0.1398, -0.0482], cluster CI [-0.1629, -0.0187]이다. 이는 오류가 아니라
strict qrels가 hard predicate까지 요구하고 semantic qrels가 장면 의미를 분리해 보는 설계의 결과다.
두 목표를 하나의 점수로 합쳐 단일 승자를 선언해서는 안 된다.

## 4. 3,000-clip 통합 색인 결과

Strict 점 추정치 최고는 `multi-frame + B4 + HNSW ef64`의 0.2685였지만 Flat 대비 차이의
95% CI가 0을 포함했고 exact-task top-10 fidelity가 0.8706에 불과했다. 따라서 이를 품질 개선으로
해석하지 않는다.

fidelity≥0.95 조건에서 `multi-frame + B4 + HNSW ef256`은 fidelity 0.9694,
strict nDCG@10 0.2615였다. 동일 조건의 Flat은 fidelity 1.0, strict 0.2625였다.
Semantic/high-fidelity 프로파일에서는 `multi-frame + B2 + HNSW ef256`이 nDCG@10 0.3518,
fidelity 0.9988이었다.

## 5. 143,830 Qwen-2048 벡터 대규모 색인 결과

고정 시드 20260717의 최종 규모 결과:

| 구성 | exact recall@10 | p95 | 크기 |
|---|---:|---:|---:|
| Flat | 1.0000 | 123.437 ms | 1,178.26 MB |
| HNSW M16/ef256 | 0.9859 | 2.978 ms | 1,199.01 MB |
| HNSW M32/ef256 | 0.9906 | 3.561 ms | 1,217.40 MB |
| IVF-Flat nlist1024/nprobe128 | 0.9965 | 18.884 ms | 1,187.80 MB |
| best observed IVF-PQ | 0.3094 | 2.123 ms 이하 | 20.85 MB |

HNSW M32/ef256은 Flat보다 p95 기준 34.7배 빨랐다. 그러나 3개 구축 시드 반복에서는
HNSW M32/ef256 recall 평균 0.9886, 범위 [0.9871, 0.9906], IVF-Flat nprobe128은
평균 0.9933, 범위 [0.9894, 0.9965]였다. 어느 후보도 세 시드 모두에서 0.99 이상을 보장하지 않았다.

후속 고정밀 ablation에서는 5개 seed(20260717–20260721)로 탐색 강도만 확장했다.

| 구성 | 5-seed recall 평균 | 최소 | 최대 | median p95 | 모든 seed ≥0.99 |
|---|---:|---:|---:|---:|---|
| HNSW M32/ef256 | 0.9894 | 0.9871 | 0.9918 | 3.179 ms | 아니오 |
| HNSW M32/ef512 | 0.9981 | 0.9965 | 1.0000 | 5.757 ms | **예** |
| HNSW M32/ef1024 | 1.0000 | 1.0000 | 1.0000 | 10.148 ms | **예** |
| IVF-Flat nprobe128 | 0.9932 | 0.9894 | 0.9965 | 21.155 ms | 아니오 |
| IVF-Flat nprobe256 | 0.9995 | 0.9988 | 1.0000 | 37.587 ms | **예** |
| IVF-Flat nprobe512 | 1.0000 | 1.0000 | 1.0000 | 68.580 ms | **예** |

따라서 관측한 5개 seed의 0.99 운영 균형점은 HNSW ef512다. Exact top-10이 필요하면
HNSW ef1024가 5/5 seed에서 1.0이었지만, 이는 현재 corpus·query·seed 범위의 관측 결과다.

따라서 기존 CLIP-512에서 유효했던 HNSW ef64 설정을 Qwen-2048에 그대로 이전할 수 없다.
고정밀 운영에서는 배치별 구축 검증, 더 큰 efSearch/nprobe, 또는 Flat exact anchor가 필요하다.
PQ는 크기를 크게 줄였지만 현재 설정의 recall이 너무 낮아 고정밀 검색 후보에서 제외한다.

## 6. MEVA 외부 동일 encoder 결과

MEVA B2 semantic nDCG@10은 caption 0.2827, frame 0.3066, dual 0.3517이었다.
Frame−caption semantic 차이 +0.0239의 query CI [-0.0053, +0.0535]와 cluster CI
[-0.0292, +0.0813]은 0을 포함한다. 반면 dual−caption 차이 +0.0690은 query CI
[+0.0510, +0.0875], activity×facet cluster CI [+0.0369, +0.1004]로 모두 양수였다.

MEVA는 clip당 동결 대표 프레임이 하나뿐이므로 이 결과는 caption 대 frame/dual 외부 검증이며,
522에서 관측한 multi-frame 저장 이점의 외부 재현으로 해석하지 않는다.

Storage-family BH 보정 cluster q-value는 frame−caption 0.4008, dual−caption <0.0001이다.

## 6A. 주 격자 정렬 Qwen 순환성 반복

기존 BGE-M3 순환성 실험과 주 Qwen 격자의 encoder 불연속을 제거하기 위해, 주 91-config와 같은
522 canonical·Qwen3-VL-Embedding-2B·query/qrels로 C1/C2를 반복했다. Clean/full/query를 한 model
session에서 재임베딩하고 주 격자와 같은 float32 L2 정규화를 적용했다.

- clean semantic nDCG@10: 0.181005로 주 격자 caption/B2/Flat과 일치
- C1 oracle filter: 1.000000, Δ +0.818995, query CI [+0.780200,+0.855287], cluster CI [+0.737950,+0.881682]
- C2 full document contamination: 0.853687, Δ +0.672682, query CI [+0.626129,+0.718190], cluster CI [+0.567532,+0.752005]

별도 구현이 입력 hash, 오염 문장 1,367 edges, embedding shape/norm, ranking, metric, bootstrap,
주 격자 clean anchor를 재계산해 10/10 gate PASS했다.

## 7. 최종 판단

“저장 방식 + 검색 방식 + 색인 방식의 단일 전역 최적 조합”은 존재하지 않았다.

- hard predicate 정확성이 우선이면 multi-frame + prefilter가 유리하다.
- semantic scene recall이 우선이면 multi-frame + unfiltered B2가 유리하다.
- 3,000-clip semantic/interactive 조건에서는 HNSW ef256이 높은 fidelity와 낮은 지연을 보였다.
- 143,830 Qwen-2048 벡터에서 HNSW는 빠르지만 시드별 recall 변동이 있고, IVF-Flat은 더 느리지만
  평균 recall이 높았다.
- 극단적 메모리 절약을 위한 현재 PQ 설정은 품질 손실이 너무 크다.

따라서 원고에는 보편적 “최적”이 아니라 목적함수와 SLA별 Pareto 선택으로 서술해야 한다.

## 8. 남은 한계

1. 143,830 규모 실험에는 task qrels가 없어 exact-neighbor fidelity만 측정했다.
2. Multi-frame 저장 효과의 외부 데이터 재현은 아직 없다.
3. 24시간 적재, 갱신, 삭제, 재색인, caption 생성 비용을 포함한 end-to-end 운영 실험은 아니다.
4. 지연은 공유 단일 호스트에서 측정했으므로 다른 하드웨어에 직접 일반화할 수 없다.
5. 522 storage cluster-bootstrap의 BH 보정 q-value는 0.05를 넘는다.
6. 실행 명세와 핵심 비교 지정은 사후 통합이며 사전등록이 아니다.

## 9. 검증 상태

첫 독립 검산기는 프로젝트 metric helper를 사용하지 않고 raw ranking에서 nDCG@10, MRR,
recall@10을 다시 계산했다. 522/MEVA 지표, ID·rank 무결성, 벡터 shape/norm/finite,
IVF 학습량, 고정 시드 manifest, 3-seed 완전성을 포함한 **지표 산술·데이터 무결성 32개 gate**가
모두 PASS했다. 이 32개 gate만으로 retrieval pipeline과 bootstrap을 독립 재현했다고 부르지는 않는다.

이를 보완한 treatment 검산기는 exact 91-cell 호환 격자, 382,193개 filtered ranking의 metadata
predicate 준수, strict=semantic∩predicate qrel 논리, 비-oracle 후보 집합, 77,350 latency trials,
paired mean delta, BH, MEVA BH, Flat empty-reference 처리까지 독립 점검해 12/12 PASS했다.
Qwen 순환성 10/10, 고정밀 5-seed ANN 8/8도 별도 PASS했다.

`agy`와 Claude의 독립 읽기 전용 감사 판정은 모두 `PASS_WITH_LIMITATIONS`였다. 두 감사 모두 치명적
설계 오류는 없다고 보았고, family-wise storage 유의성·사후 명세·외부 multi-frame 부재·scale qrels
부재에 맞춰 주장 수위를 제한할 것을 요구했다.
