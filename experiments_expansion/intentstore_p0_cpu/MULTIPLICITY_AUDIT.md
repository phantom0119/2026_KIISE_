# IntentStore G1-CPU 다중성 감사

> 최초 결과 확인 뒤 추가한 사후 유효성 보정이다. 사전 등록 분석으로 해석하지 않는다.

- 판정: **FDR_INCONCLUSIVE**
- paired sign-flip randomization: 테스트당 200,000회
- BH-FDR family: 50개 비교
- q<0.05 비교: 1개
- FDR 확인 reversal: 0개

## q<0.05인 서비스-표현쌍

| 서비스 proxy | 표현 A | 표현 B | A−B | p | q(BH) |
|---|---|---|---:|---:|---:|
| stopped_vehicle | caption | multi_frame | -0.1658 | 0.000889996 | 0.0444998 |

## 확인된 reversal

없음. 최초 `CONTINUE_STRONG`은 보정 후 확정되지 않았다.

## 해석

이 감사는 다중 비교 위양성 위험을 낮춘다. 여전히 단일 데이터셋의 검색 proxy이며 IntentStore G1 최종 판정은 아니다.
