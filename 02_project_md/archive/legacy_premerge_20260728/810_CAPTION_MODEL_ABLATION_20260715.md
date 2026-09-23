# 캡션 생성 모델 세대 비교 실험 명세

- 고정일: 2026-07-15
- 상태: 완료 (2026-07-16 07:05 KST)
- 실험 루트: `/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715`
- 논문 산출물: `2026_KIISE/paper_assets/20260715_caption_model_ablation`

## 1. 연구 질문

Qwen2.5-VL-7B로 구축한 검색 문서를 같은 크기대의 후속 Qwen VLM으로 교체하면 캡션의 생성 건전성, 비순환성, 실제 필터드 벡터 검색 성능이 개선되는가를 검증한다. 공개 VQA 벤치마크 점수는 모델 후보 선정 근거일 뿐 최종 판정 지표로 사용하지 않는다.

## 2. 비교 모델

| key | 모델 | 고정 revision | 로컬 경로 | 역할 |
|---|---|---|---|---|
| `qwen25vl_7b` | Qwen/Qwen2.5-VL-7B-Instruct | `cc594898...cfb5` | `/hdd2/huggingface_cache/...` | 기존 기준선 |
| `qwen3vl_8b` | Qwen/Qwen3-VL-8B-Instruct | `0c351dd0...ff3b` | `/hdd/models/Qwen3-VL-8B-Instruct` | 직접 세대 교체 |
| `qwen35_9b` | Qwen/Qwen3.5-9B | `c2022362...b9a` | `/hdd/models/Qwen3.5-9B` | 최신 소형 멀티모달 후보 |

Qwen3.6-27B는 fp16 가중치만 약 54GB로 2x RTX 3090의 모델별 단일 GPU 실행 예산과 동등하지 않으므로 주 비교군에서 제외한다. 이를 포함하려면 양자화 또는 모델 병렬이라는 별도 요인이 추가되므로 별도 상한 실험으로 취급해야 한다.

## 3. 고정 입력

모델 외 요인을 바꾸지 않기 위해 기존 Qwen2.5 캡션 코퍼스의 item ID와 실제 사용 프레임을 입력 매니페스트로 잠근다.

| 데이터셋 | 프레임/문서 | 검색 질의 | 정답 소스 |
|---|---:|---:|---|
| 522 tri-source | 3,000 | 85 | CVAT 사람 주석 |
| MEVA | 985 | 193 | DIVA 사람 활동 주석 |
| UCA | 6,432 | 135 | UCA 사람 문장 주석의 동결 렉시콘 판정 |

프롬프트, 최대 200,704 픽셀, 최대 110 생성 토큰, greedy decoding, fp16, PyTorch SDPA를 공통으로 고정한다. Qwen3.5는 검색 문서에 내부 추론이 섞이지 않도록 `enable_thinking=False`로 고정한다. 모델은 프레임 픽셀과 고정 프롬프트만 받으며 센서·predicate·정답 주석은 받지 않는다.

## 4. 실행 순서

1. `build_caption_ablation_inputs.py`: 입력 ID·프레임 존재·프롬프트 해시를 고정한다.
2. `run_caption_model_ablation.py`: 모델/데이터셋/샤드별 append-only JSONL을 생성한다. 오류 발생 시 해당 item을 기록하고 즉시 실패한다.
3. `audit_caption_ablation_output.py`: 100% coverage, 빈 캡션, 토큰 상한 도달, 반복, 프롬프트 복사, 기계 라벨 토큰을 검사한다. 토큰 상한 도달은 공통 110-token 예산에서 관측되는 모델별 품질 결과로 집계하고, 나머지 항목은 실행 중단 무결성 게이트로 사용한다.
4. 기존 canonical 빌더를 `--captions-path`, `--out-dir`로 실행해 모델별 A6 감사를 다시 수행한다.
5. 동일 BGE-M3로 문서와 질의를 다시 임베딩하고 동일 FAISS/BM25 B0-B5를 실행한다.
6. strict 및 semantic qrels로 모든 저장 랭킹을 다시 채점한다.
7. `analyze_caption_model_ablation.py`가 paired query bootstrap과 불변성 게이트를 집계한다.

## 5. 사전 고정 지표와 판정

주 지표는 데이터셋별 B2 vector-only, B4 prefilter-vector, B5 hybrid의 strict/semantic nDCG@10이다. 각 후속 모델과 Qwen2.5의 동일 질의 차이에 대해 10,000회 paired bootstrap 95% CI를 계산한다. Recall@10과 MRR은 보조 지표다.

캡션 생성기는 데이터셋 구조에 따라 장단점이 다를 수 있으므로 데이터셋별 결과를 우선 보고한다. 동일 모델이 세 데이터셋 모두에서 B2 semantic nDCG@10을 개선할 때만 보편적 우위라고 표현한다. 그렇지 않으면 도메인 의존 결과로 결론낸다.

## 6. 무결성 게이트

- 모델 간 `clips.parquet`, `metadata.parquet`, `queries.jsonl`, strict/semantic qrels 해시가 같아야 한다.
- BGE-M3 query embedding 해시가 같아야 한다.
- 문서와 무관한 B0 metadata-only 랭킹이 완전히 같아야 한다.
- 각 모델/데이터셋의 캡션 무결성 감사(coverage, ID 유일성, 빈 캡션, 라벨 토큰 누출, 프롬프트 복사, 과도 반복) 및 A6 감사가 통과해야 한다.
- 공통 110-token 상한 도달 건수와 비율은 모델별 품질 advisory로 반드시 보고하되, 이것만으로 lane을 조기 중단하지 않는다. 상한을 모델별로 늘리면 비교 조건이 달라지고, 상한 도달 모델을 제외하면 결과 의존 선택이 되기 때문이다.
- 하나라도 실패하면 모델 성능 비교를 유효 결과로 집계하지 않는다.

## 7. 해석 제한

이 실험은 캡션 생성 모델의 교체 효과를 평가하며, 프롬프트 자체의 과제 결합이나 448px 단일 프레임의 시간 상태 관측 한계를 제거하지 않는다. 최신 모델이 검색 성능을 개선하지 않더라도 그 결과는 일반 VLM 성능이 낮다는 뜻이 아니라, 해당 캡션 프롬프트와 검색 문서화 방식에서의 효과가 없다는 뜻이다.

## 8. 실행 상태

2026-07-15 01:57 KST 기준 입력 동결과 Qwen2.5 기준선 이관·캡션 감사·세 데이터셋 canonical/A6 재구축은 완료되었다. Qwen3-VL-8B와 Qwen3.5-9B 가중치도 `/hdd/models`에 revision 고정 상태로 저장되었다.

현재 두 RTX 3090은 별도 `Qwen3-VL-Embedding` train/validation 프로세스가 점유하고 있다. 이 프로세스는 중단하지 않았으며, 다음 두 사용자 systemd 서비스가 먼저 해제되는 GPU를 대기한다.

- `kiise-caption-ablation-generate.service`: 스모크 게이트 후 전체 캡션 생성·병합·감사
- `kiise-caption-ablation-finalize.service`: 9개 lane 완전성 확인 후 canonical·BGE-M3·B0-B5·dual-qrels·paired 분석

따라서 이 시점에는 후속 모델의 성능 결과를 주장하지 않는다. 최종 결과는 `2026_KIISE/paper_assets/20260715_caption_model_ablation/CAPTION_MODEL_ABLATION_RESULTS.md`와 `VERDICT.json`이 생성되고 무결성 게이트가 통과한 뒤에만 확정한다.

## 9. Amendment 1: 토큰 상한 도달의 게이트 분류

- 기록 시각: 2026-07-15 10:21 KST
- 관측 시점: Qwen3-VL-8B의 522 **2-item smoke만** 생성된 뒤이며, 전체 캡션 lane과 임베딩·색인·검색 결과는 생성 전이다.
- 관측 내용: 2개 중 1개가 공통 110-token 상한에 도달해 문장이 절단되었다. 모델 로딩, 생성, 병합, ID·누출·반복 검사는 정상이다.
- 변경: `no_token_limit_hits`를 실행 중단 무결성 게이트에서 비교 품질 advisory로 이동한다. 상한값 110, 프롬프트, 픽셀 예산, greedy decoding은 변경하지 않는다.
- 이유: 고정 예산에서 상한 도달률 자체가 모델의 장황성·지시 준수 결과다. 이 결과로 해당 모델을 조기 제외하거나 그 모델에만 예산을 늘리면 비교가 결과 의존적으로 변한다. 따라서 전체 lane을 실행하고 상한 도달 건수·비율을 최종 결과에 명시한다.

## 10. 실행 기록: 모델별 병렬 GPU lane

- 전환 시각: 2026-07-15 11:54 KST
- 전환 지점: Qwen3-VL-8B 522 append-only JSONL 533/3,000행. MEVA/UCA는 각 2-item smoke 완료 상태였다.
- 실행: validation 임베딩 재생성이 끝나 GPU 1이 해제된 뒤, Qwen3-VL-8B는 GPU 0에서 533행 이후를 재개하고 Qwen3.5-9B는 GPU 1에서 독립 smoke/full lane을 시작했다.
- 불변 조건: 입력 item, prompt, 448px 상당 pixel 예산, 110-token 상한, greedy, fp16, seed, 모델 revision, 모델별 출력 경로는 변경하지 않았다. JSONL은 item ID 기반 append-only 재개를 사용한다.
- 해석: 두 모델의 검색 품질 비교는 모델별로 완성된 캡션 코퍼스를 사용하므로 병렬 스케줄의 영향을 받지 않는다. 다만 생성 latency는 공유 CPU·스토리지 경합의 영향을 받을 수 있어 품질 판정 지표가 아닌 기술 통계로만 보고한다.

## 11. 실행 기록: Qwen3-VL UCA GPU 이전

- 전환 시각: 2026-07-16 03:00 KST
- 전환 조건: Qwen3.5-9B의 세 caption lane이 모두 생성·병합·무결성 감사를 통과해 GPU 1이 45 MiB 사용 상태로 해제되었고, GPU 0은 81--82C에서 software thermal slowdown이 지속되었다.
- 체크포인트: Qwen3-VL-8B UCA append-only JSONL 2,817/6,432행. 서비스 종료 전후 행 수가 같고, 2,817개 행 전체의 JSON 파싱과 item ID 유일성을 확인했다.
- 실행: GPU 0의 Qwen3-VL 서비스만 정상 종료한 뒤 같은 runner를 `--physical-gpu 1 --models qwen3vl_8b`로 다시 시작했다. 완료된 522·MEVA lane은 감사 결과를 근거로 건너뛰고 UCA의 미완료 item만 재개했다.
- 불변 조건: 모델 revision, 입력 item과 순서, 프레임, prompt, pixel 예산, 110-token 상한, greedy, fp16, seed, 출력 경로는 변경하지 않았다. 재개 후 첫 검증에서 2,870행까지 증가했고 오류 JSONL은 없었다.
- 해석: 전환 직전 로그의 누적 처리율은 약 0.138 image/s, 전환 후 초기 처리율은 약 0.255 image/s였다. 이는 열 상태와 실행 자원 차이를 포함한 운영 관측값이므로 모델 간 생성 속도 우위의 근거로 사용하지 않으며, latency는 계속 기술 통계로만 보고한다.

## 12. 완료 판정

- 완료 시각: 2026-07-16 07:05 KST
- 산출물: 9/9 caption 무결성 감사, 9/9 canonical/A6 감사, 9/9 BGE-M3 임베딩·B0--B5 검색·dual-qrels 평가, 72개 paired delta 행, 최종 `VERDICT.json`을 생성했다.
- 독립 재검증: canonical 비문서 파일 해시 15개 그룹, query embedding 해시 3개 그룹, B0 저장 랭킹 3개 그룹이 모델 간 일치했다. 36개 주 paired 비교 행은 모두 전체 질의 수를 포함하고 유한한 bootstrap 구간을 가졌다.
- 무결성 판정: PASS. 누락·추가·빈 캡션·기계 라벨 누출·프롬프트 복사·과도 반복 게이트와 A6 비순환성 감사를 모두 통과했다.
- 품질 advisory: WARN. 공통 110-token 상한 도달은 Qwen3-VL-8B 5,957/10,417건(57.19%), Qwen3.5-9B 3,709/10,417건(35.61%)이었다. 이는 실행 실패가 아니라 고정 생성 예산에서의 모델별 품질 결과다.
- 사전 주 판정: Qwen3.5-9B만 522·MEVA·UCA 세 데이터셋 모두에서 Qwen2.5-VL 대비 B2 semantic nDCG@10이 유의하게 증가했다. Qwen3-VL-8B는 522와 MEVA에서 증가했지만 UCA에서 유의하게 감소했으므로 보편적 우위로 판정하지 않는다.
- 상세 해설: `2026_KIISE/paper_assets/20260715_caption_model_ablation/CAPTION_MODEL_ABLATION_RESULTS_KO.md`
