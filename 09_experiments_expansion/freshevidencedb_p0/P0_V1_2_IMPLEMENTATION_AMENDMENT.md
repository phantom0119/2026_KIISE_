# FreshEvidenceDB P0 v1.2 구현 수정안

- 기록일: 2026-08-07
- 시점: 최종 결과 생성 전, v1.1 `naive_eager` repeat 0 중단 후
- 변경하지 않은 항목: 코퍼스, update phase 순서, phase 간 지연, worker 4개, 반복 수, 지표, 게이트와 임계값

## 확인된 문제

v1.1은 WAL 재설정 문제를 제거했지만, 하나의 Python Qdrant client와 SQLite FTS writer를 네 thread가 동시에 호출했다. update phase가 continuous query 호출 뒤에서 장시간 대기하여 6 wave 이후 진행하지 못했다. 이는 측정 대상인 **phase 사이의 visibility gap**이 아니라 client/driver의 writer scheduling 문제다.

## 수정

- 개별 dense/sparse/catalog update phase에 writer-priority lock을 둔다.
- query는 한 phase 실행 자체와 겹치지 않지만, phase와 phase 사이 25–45 ms visibility window에는 기존과 같이 네 worker가 질의한다.
- query 한 건의 catalog→dense→sparse read도 같은 lock 안에서 수행해, 질의 도중 phase가 바뀌는 driver-level race를 제거한다.
- lock 대기시간은 질의 latency에 포함한다.

P0의 가설은 개별 저장 연산 중간이 아니라 `catalog published → dense ready → sparse ready → old deleted` 사이에 생기는 cross-store 상태를 대상으로 하므로 처치 정의는 유지된다. v1/v1.1 중단 실행에서는 최종 결과 파일이 생성되지 않았고 중간 수치는 판정에 사용하지 않는다.

