# FreshEvidenceDB P0 v1.1 구현 수정안

- 기록일: 2026-08-07
- 시점: 첫 결과 파일 생성 전, `naive_eager` repeat 0 실행 중단 후
- 변경하지 않은 항목: 데이터 규모, update 순서, worker 수, phase delay, 지표, 게이트, 임계값

## 중단 원인

첫 실행은 SQLite 연결을 열 때마다 `PRAGMA journal_mode=WAL`을 다시 실행했다. 이 명령은 단순 read 설정이 아니라 database-level journal mode 확인/전환을 수행하므로, 네 query worker가 매 질의마다 lock-taking operation을 만들었다. 그 결과 wave 5 이후 sparse writer가 장시간 대기했다.

중단 시점에는 최종 CSV/JSON/자동 판정이 생성되지 않았고, 프로토콜 하나의 repeat도 완료되지 않았다. 관찰된 중간 상태를 가설 판정에 사용하지 않는다.

## 수정

- WAL과 `synchronous=NORMAL` 설정을 DB 초기화 시 한 번만 수행한다.
- query connection은 `busy_timeout`만 설정한다.

이는 실험 처치나 판정 규칙이 아니라 하니스의 비의도적 writer starvation을 제거하는 구현 수정이다. 수정 후 코드를 새 해시로 고정하고 전체 실험을 처음부터 다시 실행한다.

