# 912 — 후속 보강 실험 통제 프로토콜(결과 확인 전 동결)

- 동결 시각: 2026-07-23T17:48:31+09:00
- 적용 범위: 아래 E0·S2·S3·S4의 **신규 산출물**
- 성격: 원 논문의 사전등록이 아니라, 원 결과를 본 뒤 수행하는 후속 보강 실험의 분석 프로토콜이다.
- 변경 원칙: 실행 전 오류 수정은 변경 사유와 diff를 남긴다. 첫 결과 파일 생성 후에는 데이터 손상·코드 오류를 제외하고 주 추정량, 제외 기준, 검정 가족, 성공 기준을 바꾸지 않는다.
- 보고 원칙: 성공·실패·무효 게이트를 모두 보존한다. 결과가 불리하더라도 파일을 삭제하거나 선택 보고하지 않는다.

### 프로토콜 개정 기록

- v1, 17:48:31 KST: E0·S2의 전체 규칙과 S3·S4의 최초 규칙 동결.
- v1.1, S3 전체 산출물 생성 전: S3 exact-GT 계산 fallback과 코퍼스별 음성·양성 gate를 수치로 명확화. 축소 smoke 결과는 판정에서 제외.
- v1.2, S4 VLM 및 retrieval 결과 생성 전: S4를 top-1 nearest-neighbor evidence classification으로 한정하고, 표본 수·distractor matching·TL_3 단일 라벨·retrieval manipulation gate를 명확화.
- 위 개정은 해당 실험의 첫 **판정용** 결과 전에 이루어졌다. 먼저 끝난 다른 실험의 결과를 해당 개정의 threshold 선택에 사용하지 않았다.

## 1. 반드시 통제할 요인

| 통제 영역 | 고정 또는 차단할 요인 | 이유 | 구현 |
|---|---|---|---|
| 데이터 | 코퍼스 버전, 3,000개 clip 표본, 85개 질의, strict/semantic qrels | 표본·정답 변경과 처치 효과의 혼합 방지 | 입력 경로와 SHA-256 기록 |
| 생성 모델 | Qwen2.5-VL-7B snapshot, pixel budget, decoding, token budget, seed | 프롬프트 외 생성 조건 고정 | E0에서 prompt만 변경 |
| 표현 모델 | BGE-M3 snapshot, pooling, 정규화, dtype | 캡션 차이와 encoder 차이 분리 | 기존 embedding 스크립트·설정 재사용 |
| 검색 | exact inner-product, K=10, tie 처리, self-exclusion | ANN 오차와 검색 계획 효과 분리 | E0·S2는 Flat exact만 사용 |
| 공간 상관 | 같은 교차로 및 근접 시각의 복수 카메라 | 관측치를 독립 표본으로 과대 계수할 위험 | intersection 단위 fold·bootstrap; time은 보조 block |
| 프롬프트-표적 결합 | 기존 프롬프트의 bus/truck/two-wheeler/stopped 등 평가 범주 열거 | 문서 생성 단계가 평가 과제를 미리 아는 효과 | 과제-중립 프롬프트 E0 |
| 선택도 | predicate 통과 개수 | 선택도와 embedding 군집도의 혼합 방지 | S3의 자연 mask와 shuffle/synthetic mask는 동일한 n 유지 |
| 질의 | 동일 query vector, 동일 query 순서, 동일 query family | 질의 난이도 차이 방지 | paired query 분석 |
| 색인 | 같은 vector, build seed, M/efConstruction/efSearch 또는 IVF 설정 | index stochasticity·탐색 강도 혼합 방지 | 한 번 만든 index를 mask 대조 간 재사용 |
| 생성 답변 | VLM snapshot, prompt, frame 수·순서, max tokens, parser | retrieval 외 답변 조건 변경 방지 | S4에서 고정 manifest |
| 표집 | 모집단 층 크기와 표집 확률 | 불일치 층 과표집으로 ATE 왜곡 방지 | S4에서 inclusion probability 저장·가중 복원 |
| 반복·다중성 | seed, bootstrap B, 1차/2차 결과, 검정 가족 | 결과를 본 뒤 유리한 분석 선택 방지 | 아래에 사전 지정 |
| 실패 | decode 실패, 누락 frame, 빈 필터, qrel 부족 | 선택적 제외 방지 | 이유 코드와 분모를 전부 출력 |

### 1.1 고정 입력의 SHA-256

| 입력 | SHA-256 |
|---|---|
| `canonical_trisource_expanded/queries.jsonl` | `e7f7ac5c312de626ca964792fc7822bd2e7f39c1096ade3260b481f10c054a1f` |
| `embeddings_trisource_expanded/bge-m3/document_embeddings.npy` | `bf0614273dccff59333c96ebb91b87eb821d9fe85668f153e2d6d6abd9d77708` |
| `visual_embeddings_clip/frame_embeddings.npy` | `6add5013ba9c4033a014da0bab51a434f4fa6e2ee33b364f1a6689331ccc5716` |
| `sinnaedoro_traffic/corpus_real/frame_embeddings.npy` | `40e80ea12fd4f95f95a0a4cb656f98d6162071fddf4160bf2c7997181ff4278b` |
| `paper_assets/20260711_e1a/e1a_locked_configs.json` | `81d5fde76a6f986c8bd51226597e83cb7cba4abcd24e086b7127c3d6c656c4ff` |
| `paper_assets/20260712_perception_retest/condb_internvl3.csv` | `2d1c1a7f5d16ca59531176b05e51141a469cfd69648a50e7403bad85150f125c` |

## 2. 실행 순서와 게이트

1. **E0 프롬프트-표적 결합 대조**를 가장 먼저 수행한다.
2. E0과 병행해 **S2 교차로 차단 재분석**, **S3 선택도 보존 기전 대조**를 수행한다.
3. **S4는 문항 타당도 게이트**를 통과한 뒤에만 대규모 VLM 호출을 수행한다.
4. 각 실험은 `manifest.json`, item/query-level 결과, 요약, 실행 로그를 함께 보존한다.
5. 원고의 주장 승격은 단일 p값이 아니라 각 절의 사전 성공 기준을 모두 충족할 때만 검토한다.

## 3. E0 — 과제-중립 캡션 프롬프트 대조

### 3.1 질문과 처치

- 질문: 본문의 비순환 검색 결과가 평가 범주를 열거한 캡션 프롬프트에 의존하는가?
- 통제군: 기존 과제-인지 프롬프트.
- 처치군의 동결 프롬프트:

> Describe this urban CCTV frame in 2-4 factual sentences using only directly visible evidence. Mention the scene, objects, actions, and spatial relations that are visually salient. Do not use external metadata or infer causes, intentions, or events beyond the image.

- 두 군에서 고정: 동일 3,000개 중간 frame, Qwen2.5-VL-7B snapshot
  `cc594898137f460bfe9f0759e9844b3ce807cfb5`, `max_pixels=200704`,
  `max_new_tokens=110`, greedy decoding, seed `20260710`.
- captioner 입력은 frame pixel과 해당 prompt뿐이다. sensor·annotation·query·qrel은 입력하지 않는다.

### 3.2 1차 추정량과 검정

- 동일 85개 질의와 semantic qrels에서 과제-중립 minus 과제-인지의 B2 exact nDCG@10 paired 차이.
- 질의 family `(predicate, relevance_def)`를 군집으로 하는 bootstrap 10,000회, seed `20260723`.
- 함께 보고: 평균 차이, 95% CI, 질의별 win/tie/loss, 원점수 두 개.
- B4 exact는 2차 결과다. strict qrels, MRR@10, Recall@20도 2차 결과이며 Holm 보정한다.
- 캡션 길이(문자·공백 token), 빈 문자열, 110-token 상한 도달률, 평가 범주 단어의 출현률을 진단 결과로 전량 보고한다. 길이는 처치의 가능한 매개이므로 사후 공변량 보정으로 주 추정량을 대체하지 않는다.

### 3.3 판정

- 이 실험은 prompt 비의존성을 “증명”하지 않는다.
- 과제-중립 B2 semantic의 저하가 원 점수의 10%를 넘거나 paired CI 상한이 `-0.03 nDCG`보다 작으면 prompt 민감성을 실질적으로 큰 것으로 판정한다.
- 반대 방향까지 포함한 진단으로 paired CI가 `[-0.03,+0.03]`의 한쪽 바깥에 완전히 놓이는지도 함께 보고한다. 이는 과제-인지 prompt의 이득 판정과 분리한다.
- 그 외에는 “이 한 과제-중립 프롬프트에 대한 강건성”만 보고한다. 비열등성 주장은 사전 검정력이 부족하므로 사용하지 않는다.

## 4. S2 — 교차로 차단 결합도 검증

### 4.1 분석 지위

- 85개 질의와 기존 결과를 이미 보았으므로 확증 실험이 아니다.
- 목적은 동일 시각·교차로 상관을 차단했을 때 표 5의 방향이 유지되는지 평가하는 **차단 강건성 분석**이다.
- 기존 결과를 본 뒤 `min_pos`를 낮추거나 새 의미 정의를 추가하지 않는다.

### 4.2 fold와 포함 규칙

- 분석 단위: 고정된 25개 `(predicate, relevance_def)` family.
- 5-fold를 `intersection_id`의 안정 hash와 seed `20260723`으로 할당한다. 어떤 query outcome도 fold 생성에 사용하지 않는다.
- 각 fold에서 Cramér's V는 나머지 4개 fold에서만 계산하고, B2/B4 nDCG 차이는 held-out intersection에서만 계산한다.
- held-out B4 후보가 10개 미만이거나 held-out semantic positive가 5개 미만인 query는 해당 fold에서 `insufficient_support`로 기록한다. threshold를 낮추지 않는다.
- 동일 시각 결합의 보조 분석은 `(intersection_id, date-hour)` block bootstrap으로 수행한다.

### 4.3 결과와 다중성

- 1차: train V를 연속값으로 둔 held-out `Δ=B4-B2 semantic nDCG@10`과의 Spearman 상관. 25개 family 군집 bootstrap 10,000회.
- 2차: train V band `low <0.15`, `mid 0.15–<0.30`, `high ≥0.30`의 held-out 평균 Δ.
- 임계 `0.15/0.20/0.25/0.30/0.35` 스윕은 민감도 그림으로만 사용하며 유의성 선택에 사용하지 않는다.
- 고결합 유의 문구의 승격 조건: 유효 high family 5개 이상, 평균 Δ의 family-cluster CI가 0을 배제, 방향이 5개 fold 중 4개 이상에서 동일. 미충족 시 현 원고의 “탐색적, 2쌍 한정”을 유지한다.

## 5. S3 — 선택도 보존 군집 기전 대조

### 5.1 고정 조건

- 1차 코퍼스: Sinnae-doro A, 2차 독립 반복: AI Hub 522 B.
- 질의·vector·index는 고정한다. `K=10`, primary는 HNSW `M=32`,
  `efConstruction=200`, `efSearch=64`, postfilter `K'=4×ceil(K/s)`이다.
- 2차 index는 IVF-Flat `nlist=1024`, `nprobe=8` selector다. 사용한 Faiss 1.14.3의 training seed 기본값은 `1234`다.
- exact subset GT는 full exact top-L을 필터링해 만든다. `L=5000`에서 적격 10개를 못 찾는 질의가 0.5%를 넘을 때만 L을 결과와 무관하게 두 배씩 늘린다. `L=40000`에서도 gate를 못 넘는 합성 mask는 해당 subset에 대한 Flat exact 검색으로 전환하고 이를 manifest에 기록한다.

### 5.2 음성 대조: label shuffle

- 각 자연 predicate mask의 통과 개수 `n`을 정확히 보존한 무작위 mask 100개를 만든다.
- seed는 `20260723 + predicate_index*1000 + repeat`로 고정한다.
- 1차 결과: 자연 mask의 recall loss가 shuffle null 분포에서 차지하는 양측 permutation p와 z-score.
- predicate를 한 가족으로 Holm 보정한다. 자연 mask의 선택도와 shuffle의 선택도는 bit 수준으로 같아야 하며, 불일치 시 실행을 실패 처리한다.
- 코퍼스별 음성 대조 gate는 predicate별 `자연 손실−shuffle 평균 손실`의 predicate-bootstrap 95% CI 하한이 0보다 크고, predicate의 절반 이상에서 차이가 양수인 경우다. 개별 Holm 결과는 진단용이며 gate를 대체하지 않는다.

### 5.3 양성 대조: 합성 군집 강도

- 선택도 `s={0.05,0.10,0.20,0.40}`, 집중도 `c={0,0.25,0.50,0.75,1.0}`,
  고정 anchor 10개를 사용한다.
- 각 mask는 `round(c*n)`개의 anchor 최근접 vector와 나머지 uniform vector로 구성하며 총 `n`을 정확히 보존한다.
- anchor는 문서 index의 안정 hash 순서에서 고르며 query·recall 결과를 사용하지 않는다.
- 1차 결과: 집중도와 recall loss의 용량-반응 기울기(코퍼스별 anchor 군집 bootstrap).
- 코퍼스별 양성 대조 gate는 anchor별 within-selectivity 기울기 평균의 anchor-bootstrap 95% CI 하한이 0보다 큰 경우다.
- “군집이 원인” 표현의 승격 조건: 위 음성·양성 gate가 **각각 두 코퍼스에서 모두** 통과해야 한다. 하나라도 실패하면 “연관” 표현을 유지한다.

## 6. S4 — ANN→답변 전파

### 6.1 문항 타당도 게이트

- 기존 이진 yes/no 질문은 내용 유발 yes 편향 때문에 주 분석에서 제외한다.
- frame annotation으로 정답을 얻을 수 있는 3지선다 값 질문만 사용한다:
  `bus_count={0,1,2+}`, `bike_count={0,1,2+}`.
- 이 실험의 범위는 **top-1 검색 증거를 VLM이 값으로 판독하는 nearest-neighbor evidence classification**이다. 자유형 다중 문서 RAG 전체로 일반화하지 않는다.
- 클래스별 60개, category별 180개의 균형 표본에서 oracle source frame, class-mismatched distractor, closed/no-image 조건을 비교한다.
- distractor는 다른 class를 가지되 가능한 경우 같은 `intersection_id×hour`, 다음으로 같은 intersection, 다음으로 같은 hour에서 고른다. 이 계층과 실패를 item별 기록한다.
- prompt, 보기 순서, parser를 고정하며 보기 순서는 item hash로 균형화한다.
- 게이트: oracle macro accuracy의 95% CI 하한이 `1/3`보다 크고,
  oracle이 distractor보다 최소 10%p 높으며, 어떤 단일 예측 class도 70%를 넘지 않는다.
- bus와 bike 중 게이트를 통과한 category만 본 실험에 진입한다. 둘 다 실패하면 S4는 `invalid_measurement`로 중단한다.

### 6.2 retrieval 처치와 추정량

- exact index와 `e1a_locked_configs.json`의 strong degradation을 고정한다.
- source frame을 query로 사용하고 self-exclusion 뒤 top-1 frame만 VLM 증거로 제시한다. gold는 source frame의 TL_3 frame annotation class다.
- 검색 코퍼스도 TL_3 frame annotation이 있는 frame으로 한정해 source·evidence class 정의를 동일하게 유지한다. 원 E1A의 seed `20260711`로 뽑은 video 표본과 중간 frame 규칙을 재구성하되, TL_3 source가 없는 항목은 결과와 무관한 `missing_source_annotation`으로 기록한다.
- category별 검색 조작 gate는 `exact class-match−strong class-match ≥5%p`이고 `exact-hit/strong-miss`가 200건 이상인 경우다. 통과하지 못한 category는 답변 전파 본 실험에 넣지 않는다.
- 모집단 전체를 먼저 검색해 `exact_hit/strong_hit` 4개 층의 크기를 기록한다.
- 불일치 층을 과표집하되 item의 포함확률을 저장한다.
- 1차 추정량: 원 질의 분포의 inverse-probability-weighted paired accuracy 차이.
- 2차 추정량: `exact_hit != strong_hit` 층의 조건부 paired accuracy 차이.
- McNemar exact test와 intersection-cluster bootstrap 95% CI를 함께 보고한다.

### 6.3 검정력과 중단

- 본 호출 전 10% 고정 pilot에서 paired discordance를 추정한다. pilot item은 본 분석에서 제외한다.
- 최소 관심 효과는 원 분포 `5%p`, 불일치 층 `10%p`, 양측 alpha `0.05`, power `0.80`이다.
- 필요한 VLM 호출 수가 가용 frame 또는 사전 상한 4,000 item-pairs를 넘으면 full run을 하지 않고 `underpowered`로 보고한다.
- 원 분포 효과가 검출되지 않고 불일치 층만 검출되면 “불일치 층에서의 조건부 전파”로만 서술한다.

## 7. 산출물과 원고 반영 규칙

- 루트: `paper_assets/20260723_controlled_supplement/`
- 각 실험: `manifest.json`, `per_item.parquet` 또는 `per_query.csv`,
  `summary.json`, `run.log`, `sha256.txt`.
- 원고 `manuscript/0_paper_script.md`는 검증이 끝날 때까지 수정하지 않는다.
- 기존 투고본 `manuscript/paper_final.pdf`와 기본 양식
  `manuscript/DB연구_최종본양식.pdf`는 어떤 경우에도 변경하지 않는다.
- 보강 결과가 원 주장에 불리하면 한계와 함께 동일하게 반영한다.
