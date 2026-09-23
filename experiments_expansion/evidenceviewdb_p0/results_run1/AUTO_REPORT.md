# EvidenceViewDB P0-A 자동 판정

- 판정: **STOP_NO_PHYSICAL_GAIN**
- 게이트: G0=True, G1=True, G2=True, G3=False, G4=True
- 질의: 776 (dev 464 / holdout 312)
- 주 문맥 예산: 4,096자

## 핵심 수치

- modal best view share: 0.4201
- unique winner share: {"naive1024": 0.24871134020618557, "naive256": 0.15979381443298968, "naive512": 0.14690721649484537, "rcts512": 0.34536082474226804}
- dev-selected single view: rcts512
- selected physical design: ['rcts512']
- category routing: {"contractnli": "rcts512", "cuad": "rcts512", "maud": "rcts512", "privacy_qa": "rcts512"}
- G2 oracle-single F1: 0.0479, 95% CI [0.0333, 0.0640]
- G3 selected-baseline F1: 0.0052, 95% CI [-0.0058, 0.0149]
- G3 coverage difference: 0.0453
- G3 precision difference: 0.0027, 95% CI [-0.0034, 0.0089]
- G4 5% update ratio: 0.016966

상세 수치와 과제별 결과는 `summary.json`, 질의별 원자료는 `per_query_metrics.csv`에 있다.
