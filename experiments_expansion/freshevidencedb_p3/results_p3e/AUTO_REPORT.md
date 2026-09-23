# P3-E 7B 자연화 QA 자원·검수 게이트 보고

- T5: **`MODEL_RESOURCE_PENDING`**
- CUDA 인식: `true`
- 실행 시 가용 GPU 메모리: 278,331,392 bytes(약 265.4 MiB)
- 다른 실험이 사용 중인 GPU: RTX 3090 2장, 각 약 23,324 MiB
- agent 품질 필터 통과 QA: 38개
- 사람 검수 완료 QA: 0개

Qwen2.5-7B-Instruct의 weight와 실행 코드는 준비했으나, 두 GPU 모두 기존 장기 실험이 점유 중이어서 모델 추론을 강행하지 않았다. 기존 작업을 중단하지 않는다는 사전등록 원칙을 지켰다.

또한 현재 질문은 source-aware 형태로 자동 자연화하고 agent가 품질을 걸러낸 수준이다. `human_reviewed=true`가 30개 미만이면 전체 모델 게이트를 통과할 수 없다는 사전등록 규칙에 따라, GPU가 비어 있었더라도 현재 T5는 `HUMAN_REVIEW_PENDING`을 벗어날 수 없다.

따라서 이 파일럿은 생성 모델의 최종 답변 효과에 대해 양성·음성 어느 결론도 제공하지 않는다. GPU가 반환된 뒤 동일 lock과 QA에서 Qwen2.5-7B-Instruct를 실행하고, 별도로 30개 이상을 사람이 이중 확인해야 한다.
