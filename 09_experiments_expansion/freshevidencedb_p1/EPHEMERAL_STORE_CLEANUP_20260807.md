# FreshEvidenceDB P1 임시 저장 객체 정리

- 정리일: 2026-08-07
- 대상: P1 실행 코드가 전용으로 생성한 저장 객체만

## 삭제 대상

- Qdrant collection: 이름이 정확히 `freshevidencedb_p1a_`로 시작하는 72개
- PostgreSQL schema: `fresh_p1a`
  - 실험 전 확인된 table 252개
  - 총 relation 크기 약 620MB

## 보존 대상

- `freshevidencedb_p0_` collection 20개
- 다른 모든 Qdrant collection
- PostgreSQL `public` schema와 기존 KIISE table
- Git revision source clone
- 사전등록, 코드, revision/fact manifest
- query/checkpoint raw CSV, aggregate JSON, SHA-256 manifest와 최종 보고서

## 복구 가능성

삭제 객체는 영구 서비스 데이터가 아니라 재현용 파생 index/table이다. 다음 명령으로 동일 HEAD·manifest에서 다시 만들 수 있다.

```bash
python run_p1a_real_revision.py --manifest revision_manifest.json --output-dir <new-output>
python run_p1b_answer_failure.py --fact-manifest changed_fact_manifest.json --output-dir <new-output>
```

원시 결과는 삭제하지 않았으므로 논문 통계와 판정은 그대로 재검증할 수 있다.
