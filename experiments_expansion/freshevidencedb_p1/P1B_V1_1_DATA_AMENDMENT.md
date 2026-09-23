# FreshEvidenceDB P1-B v1.1 데이터 수정 기록

- 기록일: 2026-08-07
- 시점: changed-fact manifest 생성 단계, 답변 checkpoint·장애 주입 결과 생성 전
- 원 사전등록 해시: `af059e017abfa4d8800748b30431348624e47a2ff71f8fdafac3a0a1b51ba583`

## 중단 사실

원 사전등록은 도메인별 changed fact 40개를 요구했다. 고정한 100 revision pair와 다음 누설 방지 규칙을 적용한 결과 Flask 27개, Kubernetes 25개만 유효했다.

- old answer가 new 문서 전체에 없어야 함
- new answer가 old 문서 전체에 없어야 함
- 1–4 token의 명시적 `replace`여야 함

첫 manifest 작성은 Flask 27개에서 `RuntimeError`로 중단했고 결과 파일을 만들지 않았다. protocol 실행, 답변 accuracy, 장애 복구 결과는 아직 생성되지 않았다.

## 수정

1. 누설 방지·answer 길이·선택 순서는 변경하지 않는다.
2. 도메인별 목표를 양쪽이 충족하는 25개로 낮춘다.
3. 표본 감소를 보완하기 위해 모든 답변 checkpoint protocol과 장애 scenario를 seed가 다른 3회 독립 반복한다.
4. B1의 0-error Wilson 상한 ≤2%와 B2의 합동 상한 ≤1% 기준은 변경하지 않는다.
5. 반복은 저장 객체를 새로 초기화하며 같은 fact에 대한 단순 중복 질의가 아니라 독립 실행 단위로 보고한다.

이 수정은 가설 방향이나 성공 임계값을 결과에 맞춘 것이 아니라, 결과 생성 전 확인된 데이터 가용량에 맞춘 것이다. 최초의 40개 요구 실패는 최종 보고서에 함께 기록한다.
