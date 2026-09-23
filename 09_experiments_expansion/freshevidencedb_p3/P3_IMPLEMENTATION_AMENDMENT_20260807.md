# P3 결과 전 구현 점검 수정 기록

- 기록 시점: P3 outcome 실행 전
- 사전등록 arm·표본·게이트 변경: 없음

전용 Elasticsearch 9.2.3 smoke test에서 bulk helper의 action 최상위 `version` 필드가 사용자 문서 필드가 아니라 Elasticsearch internal versioning metadata로 해석되어 400 오류가 발생했다. graph 문서의 사용자 필드를 `_source` 아래에 명시하도록 수정했다. 실험 결과는 생성되지 않았고 격리 smoke index/collection/table은 삭제했다.
