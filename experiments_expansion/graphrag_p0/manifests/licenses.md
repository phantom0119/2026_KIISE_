# 라이선스 및 데이터 카드 (P0 파일럿)

| 자산 | 출처 | 데이터 라이선스 | 코드 라이선스 | 재배포 |
|---|---|---|---|---|
| PrimeKG v2.1 | Harvard Dataverse doi:10.7910/DVN/IXA7BM | CC0 1.0 (공공 도메인 헌정) | MIT (mims-harvard/PrimeKG) | 가능 |
| STaRK-Amazon SKB | HuggingFace snap-stanford/stark | CC-BY-4.0 | MIT (snap-stanford/stark) | 출처 표시 조건 |

## ⚠ 합성 반사실 지식 경고 (v1.1 §수정7)

본 파일럿의 **반사실(counterfactual) 세계에 포함된 모든 사실은 실험용으로 인위 생성된 허위 연관**이며,
실제 의학·상거래 지식이 아니다. 특히 임상 도메인의 "약물–단백질–질병" 반사실 삼중항은
**의학적 사실이 아니므로 어떠한 임상적 판단에도 사용할 수 없다.**

- 반사실 항목은 매니페스트에서 `SYNTHETIC_CF__` 접두어 네임스페이스로 표기된다.
- 산출물 `results/worlds_*.jsonl`의 각 레코드는 `tail_original`(실제)과
  `tail_counterfactual`(합성 허위)을 명시적으로 분리 보관한다.
- 공개 배포 시 본 경고문을 데이터 카드 최상단에 포함한다.
