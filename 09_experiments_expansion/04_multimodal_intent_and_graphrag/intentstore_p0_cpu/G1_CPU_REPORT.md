# IntentStore G1 CPU 선행 검증 보고서

> 자동 생성: 2026-08-06T06:53:04.696283+00:00  
> 이 결과는 동결된 기존 검색 산출물의 CPU 재분석이며, 신규 GPU 추론을 수행하지 않았다.  
> 판정 범위: 위험 감지 전체가 아닌 시각·텍스트 검색 표현의 선행 screening.

## 자동 판정

- 상태: **CONTINUE_STRONG**
- 이유: At least one material cross-service ranking reversal was observed.
- 주 평가: `strict` `ndcg_at_10`
- 서로 다른 전체 승자: caption, dual, joint_image_caption, multi_frame
- 사전 기준을 충족한 승자: 없음
- strong reversal 수: 5

## 서비스별 승자

| 서비스 proxy | n | 승자 | 차순위 | 승자 평균 | 차순위 평균 | 차이 [95% CI] | payload 비율 | 품질 지지 | 비용 지지 |
|---|---:|---|---|---:|---:|---:|---:|---|---|
| buses | 20 | joint_image_caption | multi_frame | 0.0857 | 0.0811 | +0.0046 [-0.0450, +0.0567] | 0.359 | False | False |
| crowded_scene | 12 | caption | joint_image_caption | 0.2241 | 0.2038 | +0.0202 [-0.0176, +0.0532] | 1.000 | False | False |
| parked_vehicle | 15 | dual | joint_image_caption | 0.0120 | 0.0063 | +0.0056 [+0.0000, +0.0159] | 3.783 | False | False |
| stopped_vehicle | 17 | multi_frame | dual | 0.1894 | 0.1405 | +0.0489 [+0.0073, +0.0893] | 0.736 | False | False |
| two_wheeler | 21 | multi_frame | dual | 0.1208 | 0.1031 | +0.0177 [-0.0410, +0.0724] | 0.736 | False | False |

## 표현별 서비스 평균

아래 표는 검색 계획과 색인을 `B2_vector + flat`으로 고정한 strict nDCG@10이다.

| 서비스 proxy | caption | representative_frame | joint_image_caption | multi_frame | dual |
|---|---:|---:|---:|---:|---:|
| buses | 0.0614 | 0.0802 | 0.0857 | 0.0811 | 0.0598 |
| crowded_scene | 0.2241 | 0.1071 | 0.2038 | 0.1031 | 0.1354 |
| parked_vehicle | 0.0046 | 0.0000 | 0.0063 | 0.0000 | 0.0120 |
| stopped_vehicle | 0.0236 | 0.0787 | 0.0747 | 0.1894 | 0.1405 |
| two_wheeler | 0.0446 | 0.0517 | 0.0584 | 0.1208 | 0.1031 |

## 해석 제한

- 이 분석은 교통 CCTV 검색 의도 5종을 서비스 proxy로 사용한다.
- 궤적, 사건 그래프, 원본 TTL, 경보 F1, 위험비용, end-to-end SLA를 포함하지 않는다.
- 따라서 `CONTINUE_*`는 다음 CPU/공개 데이터 실험으로 진행할 근거이지 G1 최종 통과가 아니다.
- `STOP_SIGNAL`은 GPU를 투입하기 전에 연구 문제를 축소해야 한다는 경고다.

## 재현

```bash
python scripts/analyze_g1_service_representation.py
```
