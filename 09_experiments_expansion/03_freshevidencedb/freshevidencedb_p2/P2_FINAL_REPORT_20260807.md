# FreshEvidenceDB P2 적용 범위·교차 엔진·서버 장애·모델 답변 최종 보고서

- 수행일: 2026-08-07
- 자동 판정: **`CONDITIONAL_GO_NICHE_OR_MODEL_PENDING`**
- 시스템 게이트: T1·T2·T3 통과
- 모델 게이트: T4 `MODEL_GATE_INCONCLUSIVE`
- 의미: **핵심 시스템 문제는 유지하되, EDBT급 전체 논문 확정 전 실제 trace·유능한 LLM·확장 artifact 평가가 필요**

## 1. 결론

P2는 P1에서 남긴 세 가지 주요 의문 중 두 가지를 해소했다. 첫째, 순차 공개와 version filter의 오류는 Qdrant에만 국한되지 않았다. Weaviate와 PostgreSQL을 결합한 두 공식 문서 도메인에서도 재현됐고, filtered vector searchability까지 확인한 staged publication은 update-window 11,695건에서 오류 0건이었다. 둘째, 전용 Qdrant/PostgreSQL process를 실제로 kill·restart하거나 Qdrant를 pause한 20회에서 재기동 직후·복구 후 snapshot 오류, 중복, 고아 artifact, 불완전 manifest 참조가 없었다.

적용성은 제한적이다. 실제 Git commit timestamp와 P1 오류창을 결합한 계산에서 Kubernetes형 workload는 변경 문서 질의 약 18.8qps에서 하루 1건의 예상 오류에 도달했지만, Flask형 workload는 약 305qps가 필요했다. 이는 모든 RAG가 아니라 **변경이 잦고 변경 문서가 집중 조회되며, 서로 다른 트랜잭션 경계의 검색 저장소를 함께 써야 하는 서비스**가 목표라는 뜻이다.

CPU Llama-3.2-1B는 current-only arm에서도 최신 답변 정확도 32%로 사전 역량 기준 70%에 미달했다. 출력 형식 불이행도 34%였으므로, 이 모델 결과는 저장 방식의 답변 효과를 반증하지도 입증하지도 못한다. 따라서 사전등록 규칙에 따라 최종 판정은 `GO_P2_SYSTEM_PROTOTYPE`이 아니라 `CONDITIONAL_GO_NICHE_OR_MODEL_PENDING`이다.

## 2. 문서·무결성 감사

- P0 및 P1-A/P1-B의 원자료·입력·결과 SHA manifest를 재검증했고 불일치가 없었다.
- P2 사전등록과 최신 선행연구 감사는 결과 실행 전에 `PREREGISTRATION_LOCK.sha256`로 고정했다.
- Weaviate API smoke test에서 비동기 인덱싱을 확인한 뒤, 결과를 보기 전에 searchability polling을 추가하고 `P2_IMPLEMENTATION_AMENDMENT_20260807.md`에 기록했다. arm·반복 수·임계값은 바꾸지 않았다.
- 실행 코드·P1 입력·Llama model weight는 `IMPLEMENTATION_LOCK.sha256`로 고정했고 실행 직전 전부 일치했다.
- P2-A~D 원자료와 집계는 `RESULT_MANIFEST.sha256`로 보존한다.

## 3. P2-A 실제 timestamp 기반 노출량

| 도메인 | 관측 update/day | 방식 | 오류초/update(p50) | 하루 1건 break-even | 20qps 예상 오류/day |
|---|---:|---|---:|---:|---:|
| Flask | 0.0676 | naive | 0.04848초 | 304.99qps | 0.0656 |
| Flask | 0.0676 | filter | 0.04679초 | 316.01qps | 0.0633 |
| Kubernetes | 0.8811 | naive | 0.06036초 | 18.80qps | 1.0637 |
| Kubernetes | 0.8811 | filter | 0.06247초 | 18.17qps | 1.1008 |

T1은 `APPLICABLE_HIGH_TRAFFIC`이다. 다만 18.80qps는 사전 경계 20qps에 가깝고, query timestamp는 실측 trace가 아니라 scenario grid다. 이 결과를 실제 장애 발생률로 표현하면 안 된다. Flask와 같이 update가 드문 corpus에서는 가치가 작다.

## 4. P2-B Weaviate 교차 엔진

도메인별 실제 revision pair 50개, protocol별 3회, 총 18개 실행을 수행했다. 전체 질의는 15,801건이고 아래 표는 실제 update-window 질의만 집계한다.

| 도메인 | 방식 | update 질의 | 오류 | missing | 오류 95% CI 상한 | query p95 |
|---|---|---:|---:|---:|---:|---:|
| Flask | naive | 735 | 91.97% | 91.97% | 93.73% | 21.69ms |
| Flask | read filter | 647 | 91.50% | 91.50% | 93.41% | 24.77ms |
| Flask | staged | 6,085 | 0% | 0% | 0.063% | 14.23ms |
| Kubernetes | naive | 1,236 | 91.91% | 91.91% | 93.30% | 24.65ms |
| Kubernetes | read filter | 872 | 91.63% | 91.63% | 93.29% | 26.10ms |
| Kubernetes | staged | 5,610 | 0% | 0% | 0.068% | 17.74ms |

T2는 `CROSS_ENGINE_GENERALIZED`이다. 특히 Weaviate는 객체 count 반영과 vector searchability 사이에 비동기 구간이 있었다. manifest를 먼저 v2로 바꾸면 version filter는 이 구간에서 v2를 찾지 못했다. staged 방식은 실제 filtered vector query가 가능해진 뒤 공개했다.

대가도 있다. staged의 wave p95는 Flask 1,016.7ms, Kubernetes 1,048.9ms로 naive의 254.9ms와 452.8ms보다 길었다. 이는 오류를 제거한 대신 publish lag를 늘린 결과다. staged arm의 update 질의 수가 많은 것도 이 barrier 시간이 길기 때문이므로, 서로 다른 query 수의 비율을 직접적인 운영 발생률로 비교하지 않는다.

## 5. P2-C 실제 server fault

| 항목 | 결과 |
|---|---:|
| scenario run | 20회 |
| restart 직후 + recovery 후 관측 | 1,000 |
| snapshot 오류 | 0 |
| Wilson 95% 상한 | 0.383% |
| GC 후 관측/오류 | 500 / 0 |
| duplicate logical artifact | 0 |
| GC 후 orphan | 0 |
| incomplete manifest reference | 0 |
| restart p50 / p95 | 1.55초 / 6.22초 |
| artifact recovery p95 | 33.30ms |

T3는 `SERVER_FAULT_GATE_PASS`다. `SIGKILL` 이전의 Qdrant partial/dense-complete stage, PostgreSQL sparse transaction 전, publish 후 GC 전, Qdrant pause timeout을 모두 포함했다. deterministic ID와 PostgreSQL primary key를 사용한 재시도는 idempotent했다.

중요한 제한은 `after_restart_before_recovery`가 container health/readiness 복구 직후라는 점이다. process가 죽어 있는 동안 query availability는 없으며, pause timeout은 약 6.22초 걸렸다. 이 실험은 재기동 이후 snapshot safety를 보인 것이지 고가용성이나 machine/power-loss durability를 증명한 것이 아니다.

## 6. P2-D CPU 1B 모델

| arm | n | task accuracy | 최신 답변 accuracy | invalid 출력 |
|---|---:|---:|---:|---:|
| current-only | 50 | 32% | 32% | 34% |
| missing | 50 | 4% | 26% | 48% |
| mixed, old last | 50 | 30% | 30% | 42% |
| mixed, new last | 50 | 38% | 38% | 30% |

- current-only − missing 최신 답변 차이: +6%p
- mixed 순서 차이: 8%p
- T4: `MODEL_GATE_INCONCLUSIVE`

current-only가 사전 역량 기준 70%에 크게 못 미쳤으므로 +6%p와 순서 차이를 가설 검정 결과로 해석하지 않는다. 최대 4-token 생성에서 단일 문자 지시를 따르지 않은 비율이 높았다. 다음 모델 평가는 GPU가 확보된 뒤 7–14B instruction model, constrained decoding 또는 full-answer extraction, 사람 검수 자연 질문으로 다시 설계해야 한다. 이 수정은 본실험 사전등록 전에 해야 한다.

## 7. 자동 게이트와 최종 판정

| 게이트 | 결과 | 해석 |
|---|---|---|
| T1 적용성 | `APPLICABLE_HIGH_TRAFFIC` | Kubernetes형 workload만 경계 통과, 민감한 결과 |
| T2 교차 엔진 | `CROSS_ENGINE_GENERALIZED` | Weaviate에서도 재현, staged 0-error |
| T3 server fault | `SERVER_FAULT_GATE_PASS` | 재기동 후 snapshot·recovery 안전성 통과 |
| T4 모델 답변 | `MODEL_GATE_INCONCLUSIVE` | 1B model competence 실패 |

전체 자동 판정은 **`CONDITIONAL_GO_NICHE_OR_MODEL_PENDING`**이다.

이는 “주제를 폐기”한다는 뜻이 아니다. 저장 시스템의 문제 존재성·교차 엔진 일반성·복구 가능성은 통과했다. 그러나 지금 상태를 EDBT급 전체 논문으로 확정하면 안 된다. 적용 workload가 좁고, end-to-end 모델 효과가 미확정이며, coordinator·graph/cache/ACL·비용 최적화가 아직 구현되지 않았기 때문이다.

## 8. 최신 연구 경계와 주장 범위

- [StaleBench](https://zenodo.org/records/20710012)는 answer freshness, refresh policy, catch-up과 position bias를 이미 다룬다.
- [FinCacheServe](https://arxiv.org/abs/2607.26076)는 evidence/tool/model dependency를 추적하는 answer-cache consistency를 다룬다.
- [FreshCache](https://arxiv.org/abs/2607.04281)는 semantic cache의 freshness risk를 다룬다.
- VersionRAG, SingleStore-V, PostgreSQL-V 때문에 version-aware QA와 transactional vector update도 신규 주장이 아니다.

따라서 남는 후보 기여는 다음으로 한정한다.

> 서로 다른 트랜잭션 경계를 가진 dense·sparse·graph·cache 파생 artifact의 readiness와 lineage를 추적하고, 한 답변이 동일 source epoch만 읽도록 공개·복구하는 coordinator와 그 비용 정책

P2는 이 좁은 문제의 실증 기반을 강화했지만 “최초”나 학회 수락 가능성을 확정하지 않는다.

## 9. 최종 연구 확정 전 필수 P3

1. 실제 update/query trace 1개 이상으로 P2-A의 18–20qps 경계 재검증
2. GPU 7–14B instruction model과 사람 검수 자연 QA로 T4 재수행
3. dense+sparse 외 graph/cache/ACL revoke 또는 embedding migration 중 최소 2종 포함
4. coordinator crash, message reorder, network partition, host/power-loss에 가까운 durability fault 추가
5. publish lag·query SLA·storage/write amplification을 함께 최적화하는 정책과 통합 PostgreSQL 기준선 비교
6. snapshot token, readiness vector, retry·GC 상태기계의 safety property를 명세하고 model checking 또는 systematic fault exploration 수행

P3의 1–3이 통과하기 전에는 “최종 연구 주제 확정”이 아니라 **조건부 시스템 프로토타입 후보**로 관리한다.

## 10. 재현 자료

- `P2_PRIOR_ART_AUDIT_20260807.md`
- `P2_PREREGISTRATION_20260807.md`
- `P2_IMPLEMENTATION_AMENDMENT_20260807.md`
- `PREREGISTRATION_LOCK.sha256`
- `IMPLEMENTATION_LOCK.sha256`
- `run_p2a_exposure.py`
- `run_p2b_weaviate.py`
- `run_p2c_server_fault.py`
- `run_p2d_model.py`
- `results_p2a/`, `results_p2b/`, `results_p2c/`, `results_p2d/`
- `RESULT_MANIFEST.sha256`
