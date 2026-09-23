# FreshEvidenceDB P2 임시 저장소 정리 기록

- 정리일: 2026-08-07
- 결과 보존 확인: `RESULT_MANIFEST.sha256` 전 항목 검증 후 실행

## 삭제한 항목

- 공유 Weaviate에서 P2 전용 이름 규칙과 정확히 일치한 `FreshP2...` collection 18개
- 전용 container `fresh-p2-qdrant`
- 전용 container `fresh-p2-postgres`
- `fresh-p2-postgres`에만 연결된 anonymous Docker volume `485a6a1b9d4607ecd72ff310ccc030902bb596b1fcde5f75917849d6bff27dfa`

## 보존한 항목

- 공유 Weaviate의 기존 `Legalbench_naive_1024_0_weaviate_hnsw_none_m16_efc256`
- 공유 `qdrant`, `postgres`, `weaviate-1.35.3` container
- P0/P1 collection·table과 모든 문서·원자료
- P2 `results_p2a`~`results_p2d`, 코드, 사전등록, 최종 보고서와 SHA manifest

삭제한 live DB 상태와 anonymous volume은 복구할 수 없다. 재현에 필요한 논리 관측값·원자료·코드는 모두 파일로 보존되어 있으므로 전용 container를 다시 생성해 실험을 재실행할 수 있다.
