# P2 구현 점검 수정 기록

- 기록 시점: P2 결과 실행 전
- 사전등록 임계값·arm·반복 수 변경: 없음

Weaviate 1.35.3 API smoke test에서 `insert_many` 성공과 aggregate count 반영 직후에도 약 0.2초 동안 filtered vector query가 결과를 반환하지 않는 비동기 인덱싱 구간을 확인했다. 따라서 P2-B의 초기 적재와 staged readiness가 단순 객체 수뿐 아니라 실제 filtered vector searchability까지 확인하도록 polling을 추가했다.

이는 처치 결과를 본 뒤 한 수정이 아니라, 실험 harness가 "ready"를 잘못 정의해 staged protocol에 불리한 위음성을 만들지 않도록 한 결과 전 구현 점검이다. naive/read-filter arm에는 publication 이후 이러한 searchability barrier를 추가하지 않는다. 따라서 이 두 arm에서 발생하는 실재 비동기 인덱싱 구간은 측정 대상에 그대로 포함된다.
