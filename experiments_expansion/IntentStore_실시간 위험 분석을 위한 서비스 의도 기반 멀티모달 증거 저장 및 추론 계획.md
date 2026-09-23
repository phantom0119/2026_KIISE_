# IntentStore: 실시간 위험 분석을 위한 서비스 의도 기반 멀티모달 증거 저장 및 추론 계획

> 영문 연구명(권고): **IntentStore: Risk-Constrained Online Evidence Retention for SLA-Aware Multi-Service Video Analytics**  
> 설명형 부제: **What to Store and What to Run for Real-Time Risk Analytics**  
> 문서 상태: 통합 연구계획서 / 신규성 감사 반영본  
> 기준일: 2026-08-06 (Asia/Seoul)  
> 적용 범위: 멀티카메라 영상과 부가 센서·메타데이터를 사용하는 실시간 위험 감지, 이상 탐지, 사후 조사  
> 중요: 이 문서에서 제안하는 수치 목표는 **실험 결과가 아니라 사전 판정 기준**이다.

---

## 0. 결론부터 읽기

### 0.1 본 연구의 주제

IntentStore는 연속 유입되는 영상에 대해 모든 것을 동일하게 저장하고 모든 질의에 큰 VLM을 실행하는 대신, 서비스가 요구하는 위험 종류·응답 마감시간·오탐/미탐 비용·설명 증거를 명시한 **서비스 의도 계약(service-intent contract)** 을 입력받아 다음 두 결정을 온라인으로 내리는 시스템이다.

1. 각 영상 구간에서 원본 클립, 키프레임, 객체 궤적, 시각 임베딩, 구조화 캡션, 사건 그래프 가운데 무엇을 생성·보존·갱신·만료할 것인가?
2. 새 사건 또는 질의가 도착했을 때 경량 탐지기, 검색, 소형 VLM, 대형 VLM 가운데 어떤 실행 계획을 선택하고 언제 상위 모델 또는 사람에게 에스컬레이션할 것인가?

논문의 중심은 두 번째 결정보다 첫 번째 결정인 **위험 제약 온라인 증거 보존(risk-constrained online evidence retention)** 이다. 추론 cascade는 보존된 증거를 소비하는 실행 계층이며, 저장과 추론을 단순히 함께 묶었다는 사실 자체를 신규성으로 주장하지 않는다.

### 0.2 왜 필요한가

영상 캡션 하나를 벡터 데이터베이스에 넣는 방식은 범용 규칙이 아니다. 서비스에 따라 필요한 정보 단위가 다르다.

- 쓰러짐 감지는 자세 변화와 짧은 전후 원본 클립이 중요하다.
- 제한구역 체류는 객체 ID, 영역, 진입·이탈 시각을 담은 궤적 테이블이 유리하다.
- 연기·불꽃·충돌처럼 시각 세부가 중요한 사건은 텍스트 캡션만 남기면 증거가 손실될 수 있다.
- “어제 같은 차량이 다른 카메라에도 나타났는가?”에는 교차 카메라 임베딩과 시간·장소 관계가 중요하다.
- 새로운 정책이 사후에 추가되면 기존 캡션에 기록되지 않은 시각 세부를 다시 복구할 수 없다.

따라서 “멀티모달 데이터를 무엇으로 벡터화할 것인가”보다 먼저 물어야 할 질문은 **어떤 미래 서비스가 어떤 증거를 어느 품질·비용·시간 제약에서 필요로 하는가**이다. IntentStore는 이 질문을 데이터베이스의 물리 설계와 온라인 제어 문제로 바꾼다.

### 0.3 신규성에 대한 객관적 판정

**폭넓은 의미의 최초 연구는 아니다.** 2026년 7월 공개된 FOLIO는 미래 질의가 알려지지 않은 스트리밍 영상에서 무엇을 기억할지 직접 다루며, 2026년 8월 2일 공개된 PMMC는 미래 질문을 예상해 멀티모달 메모리를 미리 편성한다. VIVA는 2022년에 임베딩 캐시와 영상 저장·질의 실행의 공동 최적화를 제시했고, KathDB는 2026년에 멀티모달 DBMS, 계보, 모델·프롬프트 물리 대안을 제시했다. 그러므로 다음 주장은 사용할 수 없다.

- “미래 질의를 위한 영상 기억 최초”
- “멀티모달 증거 저장 최초”
- “저장과 추론 공동 최적화 최초”
- “모델 cascade 최초”
- “멀티모달 DBMS·계보 최초”
- “서비스 의도 또는 자연어 의도 기반 시스템 최초”

다만 2026-08-06 기준으로 확인한 공개 1차 자료에서는 다음 결합 문제를 명시적으로 정의하고 구현·평가한 연구를 찾지 못했다.

> **유한한 원본 영상 보존기간을 가진 안전 중요 다중 서비스 스트림에서, 서비스별 미탐·오탐 위험비용, p95/p99 응답 마감시간, 저장·GPU 예산, 증거 계보 요구, 워크로드 변화까지 함께 반영하여 영속 물리 증거 표현의 생성·보존·만료를 온라인으로 제어하는 문제**

이것은 “구성요소가 모두 처음”이라는 공백이 아니라, 기존 영상 DB·스트리밍 VLM·모델 cascade·멀티모달 메모리가 각각 따로 최적화한 목적을 **안전 위험과 증거 소실을 중심으로 새롭게 정식화한 공백**이다. 논문화 가능성은 남아 있지만, 통합 시스템을 만들었다는 설명만으로는 부족하다. 아래의 사전 게이트에서 저장 정책의 비지배성, 공동 제어의 실질 이득, 변화 적응성을 증명해야 한다.

### 0.4 최종 타당성 판정

**2026-08-06 P0-D 갱신 판정: 현재 설계 종료, 연구 주제 확정 금지.**

문헌상 문제의 실용적 필요와 조건부 신규성은 남아 있지만, 실제 연구 착수 여부를 결정하는 P0에서 양의 근거를 얻지 못했다.

- P0-C: 실제 안전 질의 103개에서 caption이 네 서비스군 모두의 최선 단일 표현이었고 JPEG frame보다 작았다.
- P0-D: 399개 다각도 사건에서 label-derived 구조 궤적 oracle과 rich visual을 비교했으나 서비스군에 따라 서로 다른 표현이 지지되는 비지배성이 없었다(`RESCUE_INCONCLUSIVE`).
- 좁은 결과: bbox가 큰 한 시점 3장은 두 시점 6장의 50.2% 바이트로 3/4 VLM에서 비열등했다. 이것은 view-selection 결과이지 범용 IntentStore의 증거가 아니다.
- 시스템 적합성: CPU 분석은 가능했고 신규 GPU를 사용하지 않았다. 그러나 양의 G1이 없으므로 GPU 본실험과 P1~P3는 승인하지 않는다.
- EDBT급 가능성: 현재 결과만으로 부족하다. caption-only 또는 단일 view-selection보다 복잡한 위험 제약 온라인 controller가 필요한 이유가 입증되지 않았다.

따라서 아래 설계는 **통과했다는 연구 계획이 아니라, 실패 기준과 재현 결과까지 보존한 종료된 설계 기록**으로 읽어야 한다. 재개하려면 자동 trajectory 추출, 독립 공개 데이터, caption-unseen 미래 질의를 갖춘 새 사전 등록 연구로 시작해야 한다.

---

## 1. 문제 배경

### 1.1 일반적인 멀티모달 벡터화란 하나의 규칙이 아니다

영상은 다음과 같이 서로 다른 단위로 표현할 수 있다.

| 표현 | 보존하는 정보 | 장점 | 주요 손실·위험 |
|---|---|---|---|
| 원본/짧은 원본 클립 | 픽셀, 시간 변화, 음성 | 가장 높은 재해석 가능성, 법적·시각적 증거 | 저장·전송·개인정보 비용이 큼 |
| 키프레임 | 선택 시점의 픽셀 | 원본보다 작고 VLM 입력이 쉬움 | 프레임 사이 동작과 사건 시작·종료 손실 |
| 객체·궤적 테이블 | 객체 종류, 위치, ID, 시간 | SQL·시공간 질의와 체류·이동 분석에 효율적 | 탐지되지 않은 객체와 외형 세부 손실 |
| 시각/영상 임베딩 | 신경망이 학습한 유사성 | 유사 사건·객체 검색에 효율적 | 정확한 의미 설명과 인과·수치 정보가 불명확 |
| 자연어/구조화 캡션 | 모델이 선택한 의미 요약 | 텍스트 검색·LLM 추론이 쉬움 | 언급하지 않은 사실은 사실상 소실, 환각 가능 |
| 사건 그래프 | 객체·행동·시간·장소 관계 | 다단계 관계·교차 카메라 추론에 유리 | 추출 비용, 그래프 오류 전파, 유지 비용 |
| 음향·센서 특징 | 충격음, 경보, 환경 센서 | 가려진 영상 사건 보완 | 센서 동기화와 별도 오탐 문제 |

여러 표현은 서로 대체재이면서 보완재다. 동일한 영상 구간에서 캡션이 잘 맞는 질의와 궤적이 잘 맞는 질의, 원본이 반드시 필요한 질의가 공존한다. 그러므로 “캡션을 만들어 임베딩하면 범용적으로 검색 가능하다”는 가정은 연구 가설일 뿐 일반 법칙이 아니다.

### 1.2 기존 시스템의 세 가지 불일치

1. **서비스와 저장 표현의 불일치**: 저장 시점에는 어떤 서비스가 미래에 추가될지 모른다. 너무 적게 남기면 새로운 위험 정책을 검증할 수 없고, 너무 많이 남기면 비용과 개인정보 노출이 커진다.
2. **모델 정확도와 안전 비용의 불일치**: 평균 F1이 같아도 화재 미탐과 단순 행동 오탐의 사회적 비용은 같지 않다. 평균 정확도 최적화가 안전 최적화는 아니다.
3. **배치 질의와 실시간 경보의 불일치**: 사후 QA는 수초~수분의 지연을 허용할 수 있지만 실시간 위험 경보는 p95/p99 마감시간을 지켜야 한다. 큰 VLM을 항상 호출하면 부하 급증 시 마감을 놓친다.

### 1.3 알려진 위험과 열린 집합 이상은 구분해야 한다

- **알려진 위험 감지**: 쓰러짐, 싸움, 침입, 충돌처럼 정책과 라벨이 명시된 사건을 찾는다. 서비스 의도와 위험비용을 비교적 직접 정의할 수 있다.
- **열린 집합 이상 탐지**: 학습 때 정의하지 않은 비정상 상황을 찾는다. “정상에서 벗어남”은 카메라·시간·장소에 따라 달라 불확실성이 크다.

IntentStore는 두 작업을 모두 지원할 수 있지만 같은 평가 문제로 섞지 않는다. 1차 논문에서는 알려진 위험·조합 사건을 주 실험으로 삼고, 열린 집합 이상은 일반화·불확실성 실험으로 분리한다.

---

## 2. 연구 문제 정의

### 2.1 서비스 의도 계약

서비스 (s)의 의도를 다음 튜플로 표현한다.

\[
I_s = \langle P_s, S_s, D_s, C^{FN}_s, C^{FP}_s, E_s, T^{raw}_s, A_s \rangle
\]

- (P_s): 사건 조건 또는 질의 술어. 예: “제한구역에서 사람이 30초 이상 체류”
- (S_s): 카메라·시간·공간 범위
- (D_s): 경보/응답 마감시간과 목표 백분위수
- (C^{FN}_s, C^{FP}_s): 미탐과 오탐의 상대 위험비용
- (E_s): 경보에 첨부해야 하는 증거 형식과 최소 근거 수준
- (T^{raw}_s): 원본 보존 허용기간 또는 금지 조건
- (A_s): 자동 경보, 보류, 사람 검토 등 허용 행동

이 계약은 사용자의 자연어 문장을 그대로 믿는 프롬프트가 아니다. 자연어 입력은 검증된 구조화 필드로 변환하고, 안전 관리자가 비용·마감·보존 정책을 승인한다.

### 2.2 증거 객체와 계보

각 영상 구간 (x_t)에서 생성 가능한 표현 집합을 (R)이라 한다.

\[
R = \{raw, keyframe, track, embedding, caption, event\_graph, audio\_feature\}
\]

각 증거 객체는 최소 다음 필드를 가진다.

```text
Evidence(
  evidence_id, camera_id, event_time_start, event_time_end,
  representation_type, uri_or_payload, source_segment_id,
  parent_evidence_ids, extractor_name, model_version,
  prompt_or_config_hash, confidence, created_at,
  valid_until, privacy_class, checksum
)
```

핵심은 캡션·그래프·임베딩을 “사실”로 저장하지 않고 **특정 원본과 특정 모델 실행에서 파생된 버전 있는 주장**으로 저장하는 것이다. 최종 경보는 원본 또는 허용된 근접 증거까지 추적할 수 있어야 한다.

### 2.3 온라인 의사결정

시간 (t), 표현 (r)에 대해 생성·보존 여부 (z_{t,r}\in\{0,1\}), 서비스 (s)의 추론 계획을 \(\pi_{s,t}\)라고 한다. 목표는 다음 비용을 최소화하는 것이다.

\[
\min_{z,\pi}\; \sum_{t,s}
\left(
C^{FN}_s FN_{s,t} + C^{FP}_s FP_{s,t}
+ C^{D}_s \mathbf{1}[L_{s,t}>D_s]
\right)
+ \lambda_S Cost_{storage}(z)
+ \lambda_G Cost_{gpu}(z,\pi)
+ \lambda_M Cost_{materialize}(z)
+ \lambda_R Cost_{rebuild}(z)
\]

다음 제약을 둔다.

\[
\sum_{t,r} size_{t,r} z_{t,r} \le B_{storage},\qquad
GPU(t) \le B_{gpu}(t),\qquad
P(L_{s,t}\le D_s) \ge \alpha_s
\]

또한 개인정보 정책에 의해 원본을 무기한 보존할 수 없으며, 필수 증거 계보가 없으면 고위험 자동 경보를 확정하지 못하게 한다.

### 2.4 논문의 중심 가설

> 서비스별 위험과 마감시간을 반영하여 여러 증거 표현의 한계효용을 온라인으로 추정하면, 단일 표현 고정 정책이나 모든 표현 저장 정책보다 같은 안전 품질에서 저장·GPU 비용과 마감 위반을 줄일 수 있다.

이 가설이 성립하려면 먼저 서비스마다 유리한 표현이 실제로 달라야 한다. 모든 서비스에서 하나의 표현이 항상 우월하면 IntentStore의 핵심 문제는 사라진다. 이 때문에 RQ1과 G1을 가장 먼저 검사한다.

---

## 3. 제안 시스템

### 3.1 전체 흐름

```text
카메라·센서 스트림
  -> 저비용 상시 연산(모션/탐지/추적/음향/기본 임베딩)
  -> 구간 분할 및 후보 증거 생성
  -> IntentStore 증거 카탈로그와 온라인 보존 제어기
       |- 생성: 어떤 표현을 지금 만들 것인가
       |- 보존: 무엇을 SSD/객체 저장소/DB에 남길 것인가
       |- 만료: 어떤 파생물과 원본을 언제 지울 것인가
       |- 갱신: 모델·정책 변화 때 무엇을 재계산할 것인가
  -> 서비스별 추론 계획기
       |- 구조 질의/벡터 검색
       |- 경량 모델
       |- 소형 VLM
       |- 대형 VLM 또는 사람 검토
  -> 증거가 연결된 경보·기권(abstention)·사후 조사 결과
```

### 3.2 Intent Catalog

서비스 의도, 발생 빈도, 최근 호출량, 중요도, 마감시간, 위험비용, 필요한 표현을 관리한다. 동일 카메라를 여러 서비스가 공유하므로 한 서비스에서 만든 궤적이나 키프레임을 다른 서비스가 재사용할 수 있다.

### 3.3 Evidence Catalog

원본과 파생 표현 사이의 계보, 크기, 생성비용, 품질 프로필, 유효기간, 모델 버전, 프라이버시 등급을 관리한다. 그래프 DB가 반드시 필요한 것은 아니다. 1차 구현은 관계형 계보 테이블과 벡터 DB를 결합하고, 사건 관계가 필요한 서비스에만 그래프 물질화를 선택한다.

### 3.4 Representation Profiler

검증 스트림에서 서비스 (s), 표현 집합 (R'), 추론 계획 (pi)마다 다음 프로필을 학습한다.

- 사건별 미탐·오탐과 신뢰구간
- 생성시간, 질의시간, GPU 초
- 저장 바이트와 쓰기 증폭
- 원본이 만료된 뒤 재질의 가능 범위
- 시간 경과·모델 변경에 따른 노후화
- 증거 충분성 및 원본 추적 가능 여부

프로필은 하나의 전역 평균이 아니라 데이터셋·카메라·시간대 또는 간단한 장면 문맥별로 유지한다.

### 3.5 Risk-Constrained Retention Controller

표현 (r)을 구간 (t)에 추가로 보존할 한계점수를 다음처럼 계산한다.

\[
Score(t,r) =
\underbrace{\sum_s p(s\mid h_t)\,\Delta Risk_{s,t,r}}_{예상 위험 감소}
+ \underbrace{Reuse_{t,r}+LatencyGain_{t,r}}_{재사용·마감 이득}
- \underbrace{\lambda_S Bytes_{t,r}TTL_{t,r}}_{저장 비용}
- \underbrace{\lambda_G GPUCreate_{t,r}}_{생성 비용}
- \underbrace{StalenessRisk_{t,r}}_{노후화 위험}
\]

(h_t)는 현재 장면 특징, 최근 서비스 호출, 사건 발생률, 부하를 포함한다. 예산 내에서 점수가 큰 표현을 보존하되, 고위험 서비스의 최소 증거 요구를 하드 제약으로 둔다.

#### 권고 알고리즘 단계

1. **Cold start**: 검증 데이터의 프로필로 서비스-표현 효용 행렬을 구성한다.
2. **Admission**: 새 구간 도착 시 모든 후보를 생성하지 않고 저비용 특징으로 한계효용을 예측한다.
3. **Budget allocation**: 제한된 시간창에서는 비용 제약 집합선택/knapsack으로 채택한다. 효용의 준부분모듈성이 관찰될 때만 그 가정을 사용한다.
4. **Expiration**: 남은 서비스 효용, 원본 TTL, 재생성 가능성, 노후화에 따라 제거한다.
5. **Refresh**: 모델 버전 또는 서비스 정책이 바뀌면 영향받는 계보 부분만 재계산한다.
6. **Online update**: 실제 경보 검증과 질의 결과를 이용해 프로필의 평균과 불확실성을 갱신한다.

처음부터 복잡한 강화학습을 사용하지 않는다. 해석 가능한 greedy/primal-dual 제어기를 주 방법으로 만들고, contextual bandit은 충분한 온라인 피드백이 확보될 때 비교 확장으로 사용한다.

### 3.6 SLA-Aware Inference Planner

계획기는 각 서비스에 대해 다음 후보를 비용 순으로 비교한다.

```text
P0: 구조화 메타데이터/궤적 질의만 실행
P1: 임베딩 검색 + 임계값 판정
P2: 경량 탐지기 또는 사건 전용 모델
P3: 검색된 증거 + 소형 VLM
P4: 원본/다중 증거 + 대형 VLM
P5: 사람 검토
```

각 계획의 위험 상한과 지연 예측을 이용해 가장 싼 실행 가능 계획을 선택한다. 불확실성이 높거나 고위험 사건이면 상위 계획으로 에스컬레이션한다. 마감시간이 임박했다고 근거가 약한 답을 확정해서는 안 되며, 이 경우 “미확정 경보+사람 검토”로 기권한다.

### 3.7 증거 기반 경보와 환각 통제

- 경보의 각 주장에 `evidence_id`를 연결한다.
- 캡션 또는 사건 그래프만으로 고위험 사실을 확정하지 않는다.
- 원본이 남아 있다면 최종 고위험 판정은 원본/키프레임으로 교차 확인한다.
- 원본이 만료되었고 파생 증거가 불충분하면 확신을 낮추거나 기권한다.
- VLM의 설명 유창성은 증거 정확도의 지표로 사용하지 않는다.
- 출처와 모델 버전이 다른 상충 증거를 감지하고 상위 모델 또는 사람에게 보낸다.

---

## 4. 연구 질문과 검증 가설

### RQ1. 서비스에 따라 최적 증거 표현이 실제로 다른가?

- H1: 적어도 두 서비스 계열에서 최적 표현 또는 표현 조합이 다르다.
- 핵심 비교: 원본/키프레임, 궤적, 임베딩, 캡션, 사건 그래프의 품질-비용 Pareto 전선.
- 의미: H1이 기각되면 동적 보존 제어의 필요성이 약해진다.

### RQ2. IntentStore는 같은 위험 품질에서 저장·GPU 비용을 줄이는가?

- H2: 모든 표현 물질화 대비 위험가중 품질의 실질적 열화 없이 총 저장+GPU 비용을 20% 이상 절감한다.
- H3: 단일 표현 고정 정책 대비 동일 예산에서 미탐 비용과 마감 위반을 줄인다.

### RQ3. 저장 정책과 추론 계획을 연계하는 것이 독립 최적화보다 나은가?

- H4: 저장을 먼저 고정하고 모델만 최적화하는 2단계 방식보다 공동 제어가 Pareto 전선을 개선한다.
- 주의: “공동 최적화 최초”가 아니라 안전 제약 하의 연계 효용을 검증한다.

### RQ4. 스트림 부하에서도 서비스별 SLA를 지키는가?

- H5: 정상·버스트 부하에서 p95/p99 경보 지연과 마감 위반율을 정적 큰 모델 정책보다 낮춘다.

### RQ5. 새 서비스·카메라·모델 변화에 적응하는가?

- H6: 정책 추가, 사건 빈도 변화, 장면 변화, 모델 교체 후 정적 정책보다 위험 효용을 빠르게 회복한다.

### RQ6. 증거 계보와 기권이 근거 없는 경보를 줄이는가?

- H7: 증거 검증과 기권을 사용하면 지원되지 않은 경보 비율이 감소하며, 허용 가능한 경보 coverage를 유지한다.

### RQ7. 데이터셋과 모델을 바꿔도 결론이 유지되는가?

- H8: 적어도 두 공개 데이터셋과 두 모델 계열에서 방법의 방향성과 Pareto 우위가 재현된다.

---

## 5. 구체적인 실험 설계

### 5.1 단계적 설계 원칙

한 번에 모든 데이터·표현·모델을 조합하면 원인 해석이 불가능하다. 다음 순서로 진행한다.

1. P0에서 표현 비지배성과 실질 이득 존재 여부를 조기 판정한다.
2. 통과하면 표현 프로필과 오프라인 oracle을 확립한다.
3. 그다음 온라인 제어기와 추론 계획기를 구현한다.
4. 마지막에 부하·변화·계보·공개 데이터 일반화를 평가한다.

### 5.2 데이터셋

| 구분 | 데이터 | 역할 | 주의사항 |
|---|---|---|---|
| 내부 예비 | VRU-Accident 원본 1,000개 영상 및 키프레임 약 4,020개 | 교통 위험·충돌·보행자 사건 P0 | 배포 권한을 별도 확인 |
| 내부 예비 | AI Hub 지능형 CCTV 원본 269개 및 키프레임 약 1,096개 | 쓰러짐·싸움·침입 등 P0 | AI Hub 원본 재배포 제한 때문에 대표 공개 artifact로 사용하지 않음 |
| 내부/기존 | MIRIS 계열 59,019×512 프레임 임베딩·메타데이터 | 교차 카메라·궤적·검색 부하 재사용 | 위험 사건 라벨 범위 확인 필요 |
| 공개 주축 1 | [UCF-Crime](https://www.crcv.ucf.edu/research/real-world-anomaly-detection-in-surveillance-videos/) | 128시간 장기 감시영상, 13개 이상 유형의 실세계 이상 | 약한/시간 라벨의 품질 차이 반영 |
| 공개 주축 2 | [UBnormal](https://openaccess.thecvf.com/content/CVPR2022/html/Acsintoae_UBnormal_New_Benchmark_for_Supervised_Open-Set_Video_Anomaly_Detection_CVPR_2022_paper.html) | 열린 집합 이상 일반화 | 합성 장면 특성을 외적 타당성 한계로 보고 |
| 공개 확장 | [AI City Challenge](https://www.aicitychallenge.org/) 공개 트랙 또는 WTS 계열 | 다중 카메라 교통·안전·시공간 서비스 | 해당 연도 데이터 이용조건과 라벨 공개 여부 확인 |
| 스트리밍 보조 | OVO-Bench/StreamingBench | FOLIO 계열 메모리 비교와 사후 QA | 위험 경보 주 데이터가 아니라 보조 실험 |

논문의 대표 결과는 재배포 가능한 공개 데이터 적어도 두 종을 포함해야 한다. 내부 데이터만으로는 EDBT급 재현성과 외적 타당성을 확보하기 어렵다.

### 5.3 증거 표현 arm

| ID | 표현 arm | 생성 내용 |
|---|---|---|
| R0 | Metadata | 카메라, 시간, 영역, 센서, 기본 사건 후보 |
| R1 | Raw/Clip | 사건 전후를 포함한 4/8/16초 원본 또는 재인코딩 클립 |
| R2 | Keyframe | 구간당 1/4/8장 또는 변화량 기반 동적 선택 |
| R3 | Track | 객체 종류·bbox·track ID·속도·영역·체류시간 |
| R4 | Embedding | 프레임/클립 임베딩과 벡터 인덱스 |
| R5 | Caption | 자유 캡션과 사건 슬롯 JSON을 구분 저장 |
| R6 | Event graph | 객체-행동-시간-장소-카메라 관계 및 출처 edge |

단일 arm뿐 아니라 현실적인 조합을 평가한다. 모든 (2^7) 조합을 전수 실행하지 않고, RQ1의 단일 표현 스크리닝 후 상위 조합과 정책이 선택한 조합만 본실험에 포함한다.

### 5.4 모델 계층

| 계층 | 후보 | 역할 |
|---|---|---|
| L0 | 모션, 장면 변화, 규칙, 오디오 피크 | 거의 항상 실행하는 저비용 필터 |
| L1 | YOLO 계열 탐지기·ByteTrack 계열 추적기·전용 이상 모델 | 객체/궤적/후보 사건 생성 |
| L2 | CLIP/SigLIP 계열 이미지·영상 임베더 | 검색·유사도·후보 축소 |
| L3 | 2B~3B급 VLM | 저비용 증거 판독과 구조화 |
| L4 | 7B급 VLM, 예: Qwen2.5-VL 계열 | 어려운 사건 확인·설명 |
| L5 | 사람 검토 | 고위험·근거 충돌·기권 사례 |

가능하면 영상 이상 이해 특화 모델([Holmes-VAU](https://openaccess.thecvf.com/content/CVPR2025/papers/Zhang_Holmes-VAU_Towards_Long-term_Video_Anomaly_Understanding_at_Any_Granularity_CVPR_2025_paper.pdf), [Anomize](https://openaccess.thecvf.com/content/CVPR2025/papers/Li_Anomize_Better_Open_Vocabulary_Video_Anomaly_Detection_CVPR_2025_paper.pdf)) 중 코드·라이선스·장비가 맞는 하나를 비교한다. 모든 최신 모델을 재학습하는 것이 목적은 아니다.

### 5.5 서비스 워크로드

#### 알려진 위험 서비스

- 낙상/쓰러짐: 2초 내 후보 경보, 미탐 비용 높음, 전후 클립 필요
- 싸움/폭력: 다인 행동과 시간 변화 필요, 오탐 검토 필요
- 화재/연기/침수: 시각 세부와 변화 필요, 높은 미탐 비용
- 도로 사고/위험 접근: 객체 관계·속도·충돌 전후 필요

#### 조합·관계 서비스

- 제한구역에 사람이 30초 이상 체류
- 물체를 두고 사람이 영역을 이탈
- 동일 차량/사람이 여러 카메라에서 순차 출현
- 혼잡도가 임계치를 넘은 뒤 넘어짐 발생

#### 열린 집합·사후 조사 서비스

- 정상 패턴과 다른 열린 집합 이상 후보
- “경보 직전 30초 동안 어떤 변화가 있었는가?”
- “같은 객체가 과거 다른 장소에서 포착되었는가?”

각 서비스는 `Intent Contract` JSON과 정답 판정 규칙을 함께 버전 관리한다.

### 5.6 스트림과 변화 시나리오

- 일정 부하: 카메라 수와 사건률 고정
- 주야간 변화: 영상 품질과 사건 빈도 변화
- 사건 burst: 여러 카메라에서 동시에 후보가 발생
- 정책 추가: 저장 당시 없던 새 서비스가 중간에 등록
- 정책 철회: 특정 서비스가 제거되어 관련 표현의 효용 감소
- 모델 교체: 임베더/탐지기/VLM 버전 변경
- 카메라 이동·날씨·조명 변화: 데이터 분포 변화
- 원본 만료: 1시간/1일/7일 등 가상 TTL 이후 파생 증거만 남음

실시간 카메라가 부족하면 기록 영상을 원래 FPS·1×·4×·8× 속도로 재생하여 재현 가능한 스트림으로 만든다.

### 5.7 비교 기준선

| 기준선 | 의미 |
|---|---|
| All-Materialize | 모든 원본/표현을 생성·보존하는 품질 상한, 비용 하한이 아님 |
| Raw-Only + On-Demand | 원본만 일정 기간 보존하고 질의 때 모두 생성 |
| Caption-Only | 캡션+텍스트 임베딩 중심의 일반적인 RAG 구성 |
| Embedding-Only | 시각/영상 임베딩과 메타데이터만 유지 |
| Track-Only | 탐지·궤적 테이블 중심 분석 |
| Static Best | 검증셋에서 고른 단일 최적 표현 조합을 고정 |
| Static Cascade | 경량→대형 모델의 고정 임계값 cascade |
| Storage-Then-Inference | 저장 정책을 먼저 정하고 그 위에서 추론만 최적화 |
| EVA/AIDB-style | 자주 쓰는 신경 UDF 결과 또는 일부 ML 열을 물질화하는 적응 구현 |
| iRAG-style | 원본을 보존하고 질의 시 필요한 세부만 추출 |
| FOLIO-style | 엔터티 중심 장기 의미 기억+시각 증거 캐시의 공개 구현 또는 충실한 재현 |
| SLO Scheduler | 저장 표현은 고정하고 부하·GPU 실행만 최적화 |
| Offline Oracle | 전체 미래 서비스·사건을 아는 최적/근사 상한 |

원 논문 코드가 없거나 적용 범위가 다른 경우 “원 시스템 재실행”이라고 쓰지 않고 **-style adapted baseline**으로 명확히 표기한다. 동일 모델·동일 입력·동일 품질 조건을 맞춘다.

### 5.8 주요 평가 지표

#### 주 지표

1. **위험가중 사건 손실**

\[
RiskLoss = \sum_s (C^{FN}_s FN_s + C^{FP}_s FP_s + C^D_s DeadlineMiss_s)
\]

2. **고정 품질·SLA에서 총 자원 비용**

\[
TotalCost = \lambda_S StorageBytes + \lambda_G GPUSeconds + \lambda_W WriteAmplification + \lambda_B RebuildCost
\]

주 분석은 고정 저장/GPU 예산과 p95 마감 제약 아래 위험가중 사건 손실을 비교한다. 보조 주 분석은 F1 열화가 2%p 이내인 비열등 조건에서 비용 절감률을 비교한다.

#### 품질 지표

- 사건 단위 precision, recall, F1, mAP/AUROC/AUPRC
- 서비스·위험 등급별 FN/FP
- 열린 집합에서 seen/unseen 이상 성능
- 사후 QA 정확도, evidence recall, temporal grounding IoU
- 경보의 출처 지원률, 상충 증거율, 기권 coverage-risk 곡선

#### 시스템 지표

- 수집→경보 end-to-end p50/p95/p99 지연
- 마감 위반율과 burst 복구시간
- 카메라당 FPS/처리량, GPU 초, GPU 메모리
- 저장 바이트/영상 시간, 쓰기 증폭, 색인 크기
- 표현 생성·갱신·만료 시간
- 모델/정책 변화 후 재물질화 범위와 비용
- 전력 측정이 가능하면 에너지/영상 시간

### 5.9 통계 분석

- 분석 단위는 프레임 수가 아니라 사건, 영상, 질의이다. 연속 프레임을 독립 표본으로 간주하는 의사 반복을 금지한다.
- 같은 사건에 여러 방법을 실행하는 paired design을 사용한다.
- 영상 또는 카메라 단위 cluster bootstrap으로 95% 신뢰구간을 계산한다.
- 이진 성공/실패는 paired bootstrap 또는 McNemar 검정을 사용한다.
- 여러 데이터셋·카메라를 합칠 때 dataset/camera를 군집 또는 random effect로 둔다.
- 다수 서비스·지표 검정은 Benjamini-Hochberg FDR을 적용하되 주 지표는 사전 등록한다.
- p-value만 보고하지 않고 절대 차이, 상대 차이, 신뢰구간, Pareto 전선을 함께 보고한다.
- “품질 차이가 없다”는 주장은 유의하지 않다는 결과가 아니라 TOST 비열등/동등성 검정으로 확인한다. 기본 비열등 한계는 사건 F1 2%p이며 P0 전에 확정한다.
- 위험비용 값은 단일 임의값에 의존하지 않도록 낮음/중간/높음 민감도 분석을 수행한다.

### 5.10 요인 실험과 ablation

#### 필수 ablation

- 서비스 의도 제거: 모든 서비스 동일 가중치
- 위험비용 제거: 평균 정확도만 최적화
- SLA 제거: 지연 제약 없이 비용만 최적화
- 계보/증거 검증 제거
- 온라인 갱신 제거: 초기 프로필 고정
- 표현 하나씩 제거: raw, track, embedding, caption, graph
- 저장과 추론 분리
- 미래 서비스 확률을 균등/최근 빈도/학습 예측으로 변경

#### 민감도

- 저장 예산 10/25/50/100%
- GPU 예산과 동시 스트림 수
- 원본 TTL 0/1시간/1일/7일
- 미탐:오탐 비용비
- 소형/대형 모델 조합
- 사건 빈도와 burst 크기

---

## 6. 조기 타당성 실험 P0: 2~3주

P0의 목적은 논문을 완성하는 것이 아니라 핵심 전제가 틀릴 때 빨리 중단하는 것이다.

### 6.1 범위

- 데이터: 보유 VRU-Accident, AI Hub CCTV의 재배포 없는 내부 예비 실험
- 서비스: 낙상/폭력 또는 사고/제한구역 체류/유사 사건 검색/사후 설명 등 4~5개
- 표현: 원본·키프레임, 궤적, 임베딩, 구조화 캡션의 네 계열
- 정책: All, Caption-only, Embedding-only, Raw on-demand, Static best, IntentStore greedy
- 스트림: 1×/4×/8× replay와 작은 burst
- 모델: 기존 탐지·임베딩 산출물을 최대한 재사용하고, 2B~3B 또는 7B VLM 하나만 추가

### 6.2 사전 게이트

#### G1. 표현 비지배성

적어도 두 서비스 계열에서 최적 표현/조합이 다르고 다음 중 하나를 만족해야 한다.

- 사건 품질 절대차 5%p 이상
- 같은 품질에서 비용 2배 이상 차이
- 원본 만료 후 답할 수 있는 서비스 범위의 실질적 차이

**실패 시:** 범용 IntentStore 제어기 주제를 중단한다. 단일 표현이 지배적이면 그 표현의 저장 시스템 또는 측정 논문으로 축소한다.

#### G2. 공동 제어의 실질 이득

다음 중 하나와 마감 위반 개선을 동시에 만족한다.

- All-Materialize 대비 F1 열화 2%p 이내에서 저장+GPU 비용 20% 이상 절감
- 같은 예산에서 사건 F1 5%p 이상 또는 위험손실 10% 이상 개선

**실패 시:** 통합 제어기 기여를 주장하지 않는다. 표현 벤치마크 결과가 충분할 때만 측정 논문으로 전환한다.

#### G3. 변화 적응

정책 추가 또는 사건 빈도 변화 뒤 IntentStore가 best static보다 위험효용을 개선하고, 사전 지정한 관측창 안에 안정화되어야 한다.

**실패 시:** “online/adaptive” 주장을 제거하고 정적 물리 설계 최적화로 축소한다.

#### G4. 증거성

고위험 경보가 허용된 원천 증거까지 추적되고, 증거 검증+기권이 지원되지 않은 경보를 줄여야 한다.

**실패 시:** 환각 완화 또는 설명 가능성 기여를 제거한다.

### 6.3 P0 산출물

```text
intentstore/
  preregistration/P0_PROTOCOL.md
  configs/intents/*.json
  manifests/datasets/*.json
  profiles/representation_service_matrix.parquet
  traces/replay_*.jsonl
  results/p0_event_level.parquet
  results/p0_system_metrics.parquet
  reports/P0_GATE_REPORT.md
```

게이트 결과는 성공/실패와 무관하게 보존한다. 이전 HCBGen 자연 워크로드 축이 G1에서 중단된 것처럼, 이 주제도 실패 기준을 사전에 고정한다.

### 6.4 2026-08-06 CPU 선행 검증 진행 상태

GPU를 사용하지 않고 기존 동결 산출물을 재분석한 기록은 [`intentstore_p0_cpu/INTENTSTORE_P0_CPU_LOG.md`](intentstore_p0_cpu/INTENTSTORE_P0_CPU_LOG.md)에 분리 보존한다.

- 1차 proxy: 522에서는 `stopped_vehicle`의 Qwen multi-frame−caption +0.1658(q=0.0445) 신호 하나만 남았고, 독립 MEVA는 정보성 승자 두 개를 확보하지 못해 `INCONCLUSIVE`였다.
- 2차 실제 안전 서비스 P0-C: VRU 85개와 AI Hub 18개 비순환 query contracts를 caption, 중앙 frame, CLIP 4-frame, fusion에서 같은 strict qrels로 비교했다.
- dynamic event에서 4-frame−caption은 −0.1993, 95% cluster CI [−0.3603, −0.1060], q=0.000020으로 설계 기대와 반대였다.
- scene state에서도 caption−4-frame은 +0.1904, cluster CI [+0.1029, +0.3492], q=0.041760이었다.
- caption은 dynamic, scene, filtered, open 네 군 모두의 최선 단일 arm이었다. 차순위와의 nDCG@10 마진은 0.1469~0.2393이었다.
- text:visual RRF를 8:1~1:4로 바꾼 24개 사후 강건성 셀에서도 caption 대비 양의 평균 이득은 하나도 없었다.
- 실제 artifact 저장량에서도 caption stack은 VRU 4.90 KiB/clip, AI Hub 4.13 KiB/clip로 JPEG frame arm보다 작았다. raw 대비 각각 637.5배, 12,246.6배 작았다.
- 입력 정합성은 `ALIGNMENT_PASS`였고 GPU·영상 decoding은 사용하지 않았다.
- 3차 단일 구제 게이트 P0-D: 다각도 안전 사건 400개 중 사건명 누설 1개를 제외한 399개에서 label-derived 3단계 COT와 4개 VLM의 두 시점 6-frame 출력을 비교했다.
- 구조 COT는 `attribute_count`에서 4/4, `path_mode`에서 3/4 VLM 대비 우세가 지지됐지만 `temporal_relation`은 0/4였고 시각 우세도 전체 0/12였다.
- 같은 VLM 안에서 서비스군별 구조/시각 우세가 갈리는 비지배성은 확인되지 않아 `RESCUE_INCONCLUSIVE`였다.
- asymmetric 249 clips의 보조 결과에서는 better 한 시점이 3/4 VLM에서 both 대비 비열등했고 JPEG는 50.2%여서 `VIEW_SELECTION_NARROW_PASS`였다.
- P0-D는 약 7~10초 CPU 분석으로 재실행했고 핵심 산출물 hash가 일치했다. 신규 GPU 작업은 없었다.

**최종 갱신 판정: `DO_NOT_CONFIRM_INTENTSTORE — CURRENT_RESEARCH_DESIGN_CLOSED`. 현재 범위의 범용 IntentStore는 연구 주제로 확정하지 않으며 P1~P3와 GPU 신규 생성을 중단한다.**

P0-D의 COT는 자동 trajectory가 아닌 label-derived oracle이고 미래 질의도 아니므로 전체 이론 공간을 과학적으로 기각한 것은 아니다. 그러나 합의한 한 번의 구제 게이트에서 주제 확정 근거를 얻지 못했으므로 현재 설계의 추가 실험은 승인하지 않는다. 구체적인 결과와 재개 조건은 [통합 실험 기록 §17~§20](intentstore_p0_cpu/INTENTSTORE_P0_CPU_LOG.md)에 고정했다.

---

## 7. 본실험 단계

### P1. 표현 프로파일러 구축(3~4주)

- 공개 데이터의 사건/질의 단위 정답 정리
- 표현별 생성 파이프라인과 계보 구현
- 서비스×표현×모델 품질·비용 행렬 작성
- 모든 표현을 가진 offline oracle 계산

### P2. 보존 제어기 구현(4~6주)

- greedy/primal-dual 제어기
- TTL·만료·갱신 정책
- 저장 예산과 고위험 최소 증거 제약
- offline oracle, static best와 비교

### P3. 추론 계획과 부하 실험(3~4주)

- 서비스별 후보 실행 계획 프로파일링
- p95/p99 예측과 admission control
- 동시 스트림·burst·GPU 부족 재현

### P4. 변화·새 서비스 실험(2~3주)

- 서비스 추가/제거
- 주야간·카메라 drift
- 모델 버전 변경과 선택적 재물질화

### P5. 계보·환각·사람 검토 실험(2~3주)

- 지원/미지원 주장 판정 rubric
- 기권 전후 coverage-risk
- 표본 이중 주석과 불일치 조정

### P6. 공개 재현·artifact(3~4주)

- 적어도 두 공개 데이터셋
- seed/config/container/manifest 공개
- 원본 배포가 불가한 데이터는 해시·변환 스크립트·집계 결과만 제공

총 연구기간은 P0 통과 후 약 6~9개월이 현실적이다. 모델을 새로 대규모 학습하거나 대규모 카메라 클러스터를 추가하면 더 길어진다.

---

## 8. 현재 시스템과의 호환성

### 8.1 2026-08-06 장비 스냅샷

| 자원 | 확인 상태 | 판정 |
|---|---|---|
| GPU | RTX 3090 24GB ×2 | 소형/양자화 7B급 추론과 파이프라인 실험 가능 |
| GPU 현재 사용 | GPU0 23,744MiB, GPU1 23,525MiB 사용 | 현재 즉시 대형 실험 불가. 기존 작업을 중단하지 말고 전용 시간창 필요 |
| RAM | 62GiB, available 약 31GiB | 중규모 DB·프로필 계산 가능 |
| Swap | 15GiB 중 약 15GiB 사용 | 메모리 압박 위험. 대규모 색인과 VLM 동시 실행 금지 |
| NVMe `/` | 916G 중 230G 가용 | 메타데이터·활성 인덱스·실험 결과 배치 |
| `/hdd2` | 3.6T 중 700G 가용 | 원본/중간 클립 배치 가능하나 여유 20% 부근 관리 필요 |

### 8.2 이미 가동 중인 저장 시스템

- PostgreSQL 16 + pgvector
- Weaviate 1.35.3
- Milvus 2.6.0 + MinIO/etcd
- Qdrant 1.15.5
- Elasticsearch 9.2.3

P0에서는 여러 DB를 동시에 비교하지 않는다. PostgreSQL을 서비스·계보·궤적 카탈로그로, 기존에 가장 안정적인 벡터 DB 하나를 임베딩 검색으로, 파일/MinIO를 원본·키프레임 저장으로 사용한다. DB 엔진 비교는 IntentStore의 핵심 RQ가 아니며 필요하면 후속 확장으로 둔다.

### 8.3 장비에 맞는 모델 운용

- 2B~3B VLM: 3090 한 장에서 프로토타입 운용 가능성이 높다.
- 7B VLM: 양자화 또는 짧은 프레임 입력으로 한 장 운용 가능성이 있으나 실제 p95 지연을 먼저 측정한다.
- 두 GPU 분산 대형 모델보다 GPU별 역할 분리(경량 연산/대형 확인)가 재현성과 동시성 실험에 유리하다.
- 전체 모델 재학습보다 공개 체크포인트 추론, 임계값 보정, 경량 adapter가 연구 목적에 맞다.
- GPU 확보 전에는 기존 임베딩·캡션·메타데이터로 표현 비지배성 분석과 schema 구현을 먼저 진행한다.

### 8.4 저장 배치 권고

- NVMe: 활성 관계형 DB, 벡터 인덱스, 최근 증거 캐시
- `/hdd2`: 원본과 재현 가능한 중간 산출물
- 모든 파생물: 원본 해시, 모델 버전, 설정 해시 포함
- 새 중간 산출물 생성 전 예상 최대 용량 계산
- 실험 종료 후 삭제 가능한 cache와 논문 재현에 필요한 artifact를 구분

### 8.5 호환성 최종 판정

현재 시스템은 **P0와 중규모 본실험에 적합**하다. 대규모 실시간 운영을 증명하는 생산 환경은 아니다. 논문에서는 “실시간 제품 배포”가 아니라 “재현 가능한 다중 스트림 replay에서 SLA를 평가한 연구 프로토타입”이라고 정확히 표현해야 한다.

---

## 9. 2026-08-06 최신성·선행연구 감사

### 9.1 조사 방법과 한계

조사 축은 다음과 같다.

- 영상 DBMS와 물리 저장·캐시·신경 UDF 물질화
- 모델 cascade, 비용/정확도 질의 최적화
- 스트리밍 영상 이해와 미래 질의 메모리
- 실시간 이상 감지와 edge/GPU SLO 스케줄링
- Video-RAG, 사건 그래프, 증거 기반 답변
- 멀티모달 DBMS와 계보

SIGMOD/PVLDB/CIDR/ICDE/CIKM/CVPR/PerCom의 공개 논문, 저자 원문 PDF, 공식 프로젝트 페이지와 arXiv의 2021~2026 공개 자료를 중심으로 확인했다. 그러나 “동일 연구가 존재하지 않는다”는 사실은 수학적으로 증명할 수 없다. 검색 색인 지연, 비공개 심사 중 논문, arXiv 없이 학회에 제출된 논문, 서로 다른 용어를 쓰는 논문이 사각지대다. 따라서 최종 제출 전 동일 검색을 다시 수행하고, `first` 대신 정확한 비교 범위를 명시한다.

### 9.2 가장 가까운 최근 연구

| 연구 | 이미 해결한 것 | IntentStore에 남는 차이 |
|---|---|---|
| [FOLIO, arXiv 2026-07-14](https://arxiv.org/abs/2607.13298) | 미래 질의가 알려지지 않은 스트리밍 영상에서 무엇을 기억할지 결정. 단기 시각 버퍼, 엔터티 중심 장기 의미 메모리, 시각 증거 캐시 | QA/기억 정확도와 메모리 비용이 중심. 서비스별 안전 위험, 경보 p95 SLO, 다중 서비스 공유, 원본 TTL과 영속 물리 표현 수명주기의 공동 제어는 다루지 않음 |
| [PMMC, arXiv 2026-08-02](https://arxiv.org/abs/2608.00962) | 미래 질문 후보를 예측하고 질의 조건 멀티모달 메모리 프로그램을 consolidation 시점에 편성·검증 | 장기 LVLM 상호작용 메모리. 라이브 위험 경보, 카메라 스트림 부하, 물리 저장 예산·만료·미탐 비용 문제와 다름 |
| [VIVA, CIDR 2022](https://vldb.org/cidrdb/2022/viva-an-end-to-end-system-for-interactive-video-analytics.html) | 임베딩 캐시, 혼합 데이터 질의 최적화, 영상 파일 관리와 가속기 실행 공동 고려 | 대화형/배치 영상 분석 비전. 안전 위험 계약, 유한 원본 보존, 온라인 다중 서비스 사건 스트림 제어가 아님 |
| [VIVA relational hints, PVLDB 2022](https://www.vldb.org/pvldb/vol16/p447-romero.pdf) | 모델 교체·필터·술어 순서를 최적화해 정확도 조건에서 복합 영상 질의 실행 개선 | 저장 표현 수명주기와 위험가중 실시간 경보가 아님 |
| [KathDB, CIDR 2026](https://vldb.org/cidrdb/papers/2026/p14-xiao.pdf) | 멀티모달 관계 뷰, 세밀 계보, function-as-operator, 모델·프롬프트 물리 대안과 비용/정확도 통계 | 범용 멀티모달 DBMS 비전. 스트리밍 보존 제어, 원본 만료, 안전 비용·SLA를 평가하지 않음 |
| [Task Cascades, arXiv 2026](https://arxiv.org/abs/2601.05536) | 처리 데이터 비율·모델·연산을 함께 고르는 cascade와 통계적 정확도 보장 | 문서/비정형 배치 처리 중심. 영상 스트림의 영속 상태와 서비스 위험·마감시간이 없음 |
| [Palimpzest, CIDR 2025](https://www.vldb.org/cidrdb/papers/2025/p12-liu.pdf) | 모델·프롬프트를 포함한 선언적 AI 데이터 파이프라인의 비용·품질 계획 탐색 | 라이브 영상 증거 보존과 안전 위험 최적화가 아님 |
| [LOTUS, PVLDB 2025](https://www.vldb.org/pvldb/vol18/p2851-patel.pdf) | 의미 연산자와 통계적 품질 제약 아래 비용 최적화 | 저장 수명주기·영상 위험 서비스가 아님 |
| [DocETL, PVLDB 2025](https://www.vldb.org/pvldb/vol18/p3035-shankar.pdf) | LLM 문서 처리 파이프라인의 품질 중심 rewrite | 문서 ETL이며 온라인 영상 보존·SLA가 아님 |
| [VOCAL-UDF, SIGMOD 2025](https://arxiv.org/abs/2408.02243) | 조합 영상 질의를 위한 프로그램/증류 모델 UDF 자동 생성과 능동학습 | 서비스 맞춤 질의는 지원하지만 증거를 무엇으로 얼마나 오래 남길지 결정하지 않음 |
| [EVA, SIGMOD 2022](https://sites.cc.gatech.edu/fac/Kishore.Ramachandran/pubs/EVA-SIGMOD-2022.pdf) | 신경 UDF 결과 물질화와 탐색 질의 간 재사용 | 위험·SLA·원본 만료를 반영한 다중 표현 온라인 보존이 아님 |
| [AIDB, DEEM 2024](https://experts.illinois.edu/en/publications/aidb-a-sparsely-materialized-database-for-queries-using-machine-l/) | ML 가상 열을 희소 물질화하는 DB | 스트리밍 영상 사건과 위험가중 정책이 아님 |
| [VSS, SIGMOD 2021](https://arxiv.org/abs/2103.16604) | 영상 타일/파일 물리 형식과 분석용 저장·캐시 선택 | 의미 증거 표현과 서비스 위험을 최적화하지 않음 |
| [iRAG, CIKM 2024](https://arxiv.org/abs/2404.12309) | 빠른 수집 후 질의 시점에 필요한 시각 세부를 추출 | 원본 장기 보존을 전제로 하며 원본 만료 전 무엇을 영속화할지 제어하지 않음 |
| [Cerberus, arXiv 2025](https://arxiv.org/abs/2510.16290) | 실시간 영상 이상 감지를 위한 2단계 cascade | 실행 지연·이상 감지가 중심이며 다중 증거 저장·사후 질의가 없음 |
| [OCTOPINF, PerCom 2025](https://arxiv.org/abs/2502.01277) | edge video inference의 workload-aware GPU 배치와 SLO 처리량 | 추론 스케줄링은 강하지만 어떤 증거를 보존할지 다루지 않음 |
| [VectraFlow, CIDR 2025](https://vldb.org/cidrdb/2025/vectraflow-integrating-vectors-into-stream-processing.html) | 감시를 포함한 연속 벡터 스트림의 low-latency filter/top-k/join | 벡터 외 증거 표현, 안전 위험, 원본 TTL, VLM cascade를 공동 제어하지 않음 |
| [Event-Causal RAG, arXiv 2026](https://arxiv.org/abs/2605.06185) | 스트리밍 사건 그래프와 벡터/그래프 이중 메모리 | 답변 추론이 중심. 실시간 위험 서비스별 물리 수명주기와 SLA 제어가 없음 |
| [CARVE/V-RAGBench, arXiv 2026](https://arxiv.org/abs/2606.13141) | Video-RAG에서 검색과 생성 분리, 청크별 모달리티·세분도 적응 | 질의 시 문맥 구성 문제이며 지속 스트림에서 증거 생성·만료 문제와 다름 |
| [VideoRAG, arXiv 2025](https://arxiv.org/abs/2502.01549) | 텍스트 그래프와 멀티모달 문맥을 결합한 영상 RAG | 저장·실시간 위험·SLA 제어가 아님 |

### 9.3 “이미 공표되었는가?”에 대한 정확한 답

1. **넓은 아이디어는 이미 공표되었다.** 무엇을 기억할지 선택하는 스트리밍 영상 메모리(FOLIO), 미래 질문 기반 사전 편성(PMMC), 저장과 영상 질의의 공동 고려(VIVA)가 존재한다.
2. **가장 직접적인 두 최신작 FOLIO와 PMMC는 현재 arXiv 공개본이다.** 공개 우선권과 선행기술로는 고려해야 하지만, 기준일 현재 해당 공개 페이지에서 동료심사 학회 게재는 확인되지 않는다.
3. **좁은 IntentStore 문제의 동일 구현·평가는 찾지 못했다.** 다만 이는 제한된 검색에 근거한 `not found`이지 존재 부재의 증명이 아니다.
4. **공백의 수명은 짧을 수 있다.** PMMC는 기준일 불과 4일 전에 공개되었다. 연구계획 공개, P0 조기 실행, 월별 문헌 감시가 필요하다.

### 9.4 논문에서 사용할 수 있는 신규성 문장

아직 실험을 통과하지 않았으므로 다음처럼 조건부로 작성한다.

> Existing systems separately optimize streaming video memory, neural query execution, model cascades, or multimodal provenance. IntentStore studies a distinct online data-management problem: retaining expiring multimodal evidence for multiple safety services under risk-weighted errors, tail-latency SLOs, storage/GPU budgets, and provenance constraints.

최종 선행연구 재감사 뒤에만 다음과 같이 제한된 `to our knowledge` 문장을 고려한다.

> To our knowledge, IntentStore is the first evaluated system to jointly control the lifetime of persistent multimodal evidence and its downstream escalation plans for multi-service safety video streams under explicit risk and tail-latency constraints.

`first` 문장이 없어도 논문은 가능하다. 더 안전하고 강한 기여는 “새 문제 정식화 + 알고리즘 + 재현 가능한 측정 + 기존 방법이 실패하는 조건”이다.

---

## 10. 연구 가치

### 10.1 학술적 타당성

- 멀티모달 저장 단위를 단순 파일/벡터가 아니라 **서비스가 소비하는 확률적·버전 있는 증거**로 정의한다.
- 질의 시점 최적화만 다룬 기존 시스템과 달리, 원본이 사라지기 전에 미래 서비스 효용을 고려해야 하는 비가역 결정을 다룬다.
- 평균 정확도가 아닌 위험가중 손실과 tail latency를 중심으로 데이터베이스 물리 설계를 평가한다.
- 새 서비스와 모델 변화가 파생 증거의 유효성에 미치는 영향을 선택적 갱신 문제로 연결한다.

### 10.2 사용성

- 운영자는 “어떤 임베딩을 써야 하는가” 대신 위험·마감·증거·보존 요구를 선언한다.
- 동일 스트림에서 여러 부서/서비스가 증거를 재사용할 수 있다.
- 새 서비스가 추가될 때 남아 있는 증거로 지원 가능 여부와 재계산 비용을 사전에 알 수 있다.
- 경보가 어느 원본·모델·설정에서 나왔는지 감사할 수 있다.

### 10.3 사회적 파급력

[AI City Challenge](https://www.aicitychallenge.org/)는 다중 카메라 교통·안전 분석에 국제적인 연구 수요가 지속됨을 보여준다. [NVIDIA Video Search and Summarization Blueprint](https://developer.nvidia.com/blog/build-a-video-search-and-summarization-agent-with-nvidia-ai-blueprint/)도 실시간/보관 영상, VLM, 벡터 DB, GraphRAG, 사용자 경보를 결합한 제품 수요를 명시한다. 이는 구성요소의 최초성을 입증하지는 않지만, 해결 대상의 실용성과 산업 관심을 뒷받침한다.

기대 효과는 다음과 같다.

- 위험 사건의 마감 내 탐지와 고위험 미탐 감소
- 모든 영상을 무기한 보존하지 않는 최소 데이터 원칙
- 제한된 GPU에서 서비스 우선순위에 맞춘 자원 사용
- 사후 감사·조사 때 증거 계보 제공
- 새 안전 정책 추가 시 전체 재처리를 피하는 선택적 갱신

### 10.4 미래 지향성

- 카메라 외에 음향, IoT, 레이더, 환경 센서로 증거 catalog를 확장할 수 있다.
- edge-cloud 분산 보존, 연합/프라이버시 보존 분석으로 확장할 수 있다.
- 모델이 바뀌어도 표현 효용 프로필과 계보를 갱신하는 지속적 물리 설계 문제로 확장할 수 있다.
- 사건 그래프는 관계 질의에만 선택적으로 물질화하므로 GraphRAG 유행에 종속되지 않는다.
- 장기적으로는 규정·개인정보 정책을 hard constraint로 포함한 정책 인식 데이터베이스가 될 수 있다.

### 10.5 부정적 파급과 안전장치

- 감시 확대와 목적 외 사용(function creep)
- 특정 집단·장소의 오탐 편향
- 자동 경보를 사실로 오인하는 운영 위험
- 원본·얼굴·차량 정보의 개인정보 노출
- 생성 캡션·그래프의 환각이 장기 기록으로 굳어지는 위험

대응 원칙은 최소 보존, 역할 기반 접근, 원본 TTL, 감사 로그, 모델/프롬프트 버전, 집단·장소별 오류 분석, 고위험 사람 검토, 파생 주장과 원천 증거의 분리다. “효율이 좋아졌다”는 이유로 더 많은 감시를 정당화해서는 안 된다.

---

## 11. 학회 수준과 투고 전략

### 11.1 EDBT급에 필요한 최소 구성

1. Intent contract와 증거 수명주기를 포함한 명확한 새 데이터 관리 문제
2. 단순 휴리스틱을 넘어선 온라인 보존 알고리즘 또는 제한된 조건의 근사/제약 만족 근거
3. 실제 구현과 end-to-end 재생 스트림 평가
4. 공개 데이터 적어도 두 종, 다중 서비스, 다중 표현
5. EVA/AIDB/VIVA/FOLIO/iRAG/정적 cascade/SLO scheduler 계열의 공정한 기준선
6. 위험 품질, tail latency, 저장, GPU, 갱신 비용을 함께 보고한 Pareto 분석
7. drift와 새 서비스에서의 적응 실험
8. 재현 가능한 코드·설정·trace·집계 artifact

이 조건을 만족하면 EDBT/ICDE 계열의 데이터 관리 시스템 연구로 설명할 수 있다.

### 11.2 PVLDB/SIGMOD급으로 올리려면

- 수백~수천 스트림 상당의 추적 가능한 scale-out 평가 또는 설득력 있는 부하 생성
- 강한 알고리즘 중심: 예를 들어 제약 온라인 집합선택의 성질, 근사 경계, 경험적 regret
- 데이터/워크로드 공개와 반복 가능한 시스템 artifact
- 독립 저장·독립 추론 최적화가 실패하는 메커니즘 분석
- 여러 모델·데이터셋에서 안정적인 효과와 비용 민감도
- 개인정보/원본 만료가 실제 최적 정책을 바꾸는 결과

### 11.3 연구로 인정받기 어려운 형태

- 캡션 생성 → 벡터 DB 저장 → VLM 답변 데모
- 최신 모델 여러 개의 정확도 순위표
- 서비스 요구를 프롬프트 한 줄로만 표현
- 내부 데이터 하나에서 평균 F1만 보고
- GraphRAG를 붙였다는 사실을 기여로 주장
- 비용 가중치를 결과에 맞춰 사후 조정
- 기존 시스템과의 차이를 “실시간”이라는 단어만으로 설명

### 11.4 권고 투고 포지셔닝

1차 목표는 **EDBT/ICDE 시스템 연구**로 잡고, P0와 P2 결과가 강하면 PVLDB 확장을 검토한다. 영상 이해 모델 자체가 기여가 되면 ACM Multimedia/CIKM이 대안이지만, 현재 설계의 핵심은 모델이 아니라 데이터 저장·물질화·온라인 자원 제어이므로 데이터베이스 학회 포지셔닝이 자연스럽다.

---

## 12. 이전 연구 자산과의 관계

### 12.1 HCBGen 자연 워크로드 주제와 분리

`p0_validity_audit`에서 자연 조건과 난이도 매칭 조건의 검색 난이도 차이가 사전 최소 효과 0.05에 미달해 기존 주제는 중단되었다. IntentStore는 HCBGen의 조건 생성기 또는 라이선스에 의존하지 않는다. 이전 결과는 “사전 게이트로 약한 전제를 빨리 중단한다”는 연구 운영 원칙만 계승한다.

### 12.2 KIISE-DBR 자산 재사용

- 기존 VRU/AI Hub 영상·키프레임·캡션·임베딩·qrels
- pgvector, Weaviate, Milvus, Qdrant 등 저장 인프라
- 기존 RAG VQA와 reranker 결과
- 다중 카메라 감시 Video-RAG 평가 설계
- 벡터 인덱스 수명주기 실험 코드

재사용은 연구 비용을 줄이지만 기존 논문의 결과를 신규 결과처럼 중복 보고해서는 안 된다. IntentStore의 신규 실험은 서비스 의도, 표현 보존 결정, 원본 TTL, SLA, 위험가중 손실을 새로 포함해야 한다.

### 12.3 GraphRAG의 위치

사건 그래프는 모든 영상의 기본 표현이 아니라 선택 가능한 물리 표현 R6이다. RQ1에서 관계 서비스에만 이득이 있는지, 생성·갱신 비용을 상쇄하는지 검증한다. 그래프가 지배적이지 않아도 IntentStore 논문은 성립해야 한다.

---

## 13. 실행 우선순위와 체크리스트

### 즉시 1주차

- [ ] 본 문서의 RQ·G1~G4를 PI와 확정
- [ ] 서비스 의도 JSON schema 작성
- [ ] 데이터별 배포·라이선스·라벨 범위 확인
- [x] 기존 원본/키프레임/임베딩/캡션의 clip/query/frame 정합성 매핑과 입력 hash 기록
- [x] GPU를 사용하지 않는 표현 크기·coverage 분석
- [ ] GPU 전용 시간창 확정; 현재 작업을 임의 중단하지 않음
- [ ] FOLIO·PMMC·VIVA를 포함한 선행연구 표를 저장소에서 버전 고정

### 2~3주차

- [ ] 4~5개 서비스의 사건 단위 정답과 비용 범위 확정
- [ ] 네 표현 계열의 품질·생성·저장·질의 비용 프로파일
- [ ] Static/All/On-demand/greedy 비교
- [ ] 1×/4×/8× replay의 p95 지연 측정
- [ ] cluster bootstrap과 비열등 분석
- [ ] 자동 G1~G4 보고서 생성

### P0 통과 뒤

- [ ] 공개 UCF-Crime/UBnormal 파이프라인
- [ ] 온라인 보존 제어기와 offline oracle
- [ ] 원본 TTL·새 서비스·모델 drift
- [ ] 계보 기반 경보와 기권
- [ ] 강한 기준선과 artifact

> 2026-08-06 상태: P0-C가 `SAFETY_G1_STOP_SIGNAL`이므로 “P0 통과 뒤” 항목은 실행 보류다.

### 월별 신규성 감사 검색어

```text
streaming video memory retention future queries
multimodal evidence retention video analytics
risk-aware video analytics database
SLA-aware multimodal query optimizer
joint storage inference video analytics
online neural materialization multimodal
service intent video database
expiring raw video evidence provenance
```

---

## 14. 성공·실패에 따른 논문 스토리

### 성공 시

> 서로 다른 안전 서비스는 서로 다른 증거 표현을 필요로 하며, 원본 만료와 tail-latency 제약 때문에 저장 결정은 비가역적이다. IntentStore의 위험 제약 온라인 보존 제어는 정적·단일 표현·질의 시점 최적화보다 동일 안전 품질에서 자원 비용과 마감 위반을 줄인다.

### G1만 성공하고 G2가 실패할 때

동적 표현의 필요성은 있으나 제어기의 이득이 부족하다. 여러 표현의 서비스별 비지배성과 기존 단일 표현 벤치마크의 한계를 보여주는 **측정/벤치마크 논문** 가능성을 별도 평가한다.

### G1이 실패할 때

모든 서비스에서 하나의 표현이 지배적이면 IntentStore 주제를 중단한다. 그 표현을 왜 지배적으로 만드는지, 어떤 조건에서 깨지는지에 대한 좁은 저장 연구만 남길 수 있다.

### G3가 실패할 때

온라인·미래 지향 주장을 제거하고, 알려진 서비스 집합을 위한 정적 위험 제약 물리 설계 논문으로 축소한다.

### 증거 기여가 실패할 때

환각 완화 주장을 삭제한다. 검색/정확도 향상이 곧 환각 완화는 아니며, 근거 지원률이 개선되지 않으면 이 기여는 성립하지 않는다.

---

## 15. 최종 권고

IntentStore는 “최근 아무도 생각하지 않은 완전 최초 주제”가 아니다. 오히려 FOLIO와 PMMC의 매우 최근 공개로 인해 멀티모달 기억·미래 질의 대응이 빠르게 경쟁 영역이 되었음이 확인되었다. 이 사실을 숨기거나 넓은 최초성을 주장하면 논문 위험이 커진다.

그럼에도 연구 가치는 남아 있다. 기존 연구는 주로 QA 정확도, 메모리 크기, 질의 실행 비용, GPU 스케줄링, 물질화 재사용 가운데 일부를 최적화한다. IntentStore가 겨냥하는 핵심은 **원본이 만료되는 실제 안전 스트림에서, 서로 다른 위험과 마감시간을 가진 여러 서비스가 미래에 사용할 증거를 지금 선택해야 하는 비가역 데이터 관리 문제**이다.

따라서 다음 원칙으로 진행한다.

1. 제목과 논문의 중심을 `risk-constrained online evidence retention`에 둔다.
2. 추론 cascade, GraphRAG, 벡터 DB는 구성요소이지 각각의 신규성 주장이 아니다.
3. P0에서 표현 비지배성과 20% 수준의 자원/품질 실질 이득을 먼저 검증한다.
4. 내부 데이터만으로 논문을 끝내지 않고 공개 데이터 두 종에서 재현한다.
5. 실시간은 평균 FPS가 아니라 p95/p99 마감 위반으로 평가한다.
6. 환각 완화는 evidence support와 abstention으로 직접 측정한다.
7. 최종 제출 직전에 최신 문헌을 다시 감사하고 폭넓은 `first` 표현을 사용하지 않는다.

이 조건을 지키면 IntentStore는 **실용적 수요가 있고, 현재 시스템에서 시작 가능하며, EDBT급 이상을 목표로 할 수 있는 조건부 고가치 연구 주제**다. 반대로 P0를 통과하지 못하면 과감히 중단해야 하며, 그 중단 가능성 자체가 연구 타당성을 해치는 것이 아니라 수개월의 잘못된 투자를 막는 안전장치다.

### 15.1 2026-08-06 실험 결과에 따른 운영 결론

위 문단은 P0 실행 전의 조건부 가치 평가다. P0-C에 이어 단 한 번의 P0-D 구제 게이트까지 실행했지만 주제 확정 조건을 충족하지 못했다.

- **주제 확정:** 하지 않음
- **현재 범위:** `CURRENT_RESEARCH_DESIGN_CLOSED`
- **GPU 본실험:** 승인하지 않음
- **EDBT/ICDE 가능성:** 현재 결과만으로는 부족함. caption-only보다 복잡한 시스템이 필요한 이유가 성립하지 않음
- **P0-D 기계 판정:** `RESCUE_INCONCLUSIVE`; 서비스별 구조/시각 비지배성 확인 실패
- **좁은 잔여 결과:** 정답 bbox 기반 better-view 선택은 3/4 VLM에서 both-view 대비 비열등하며 저장량 50.2%
- **재개 조건:** 자동 trajectory extractor, 독립 공개 데이터, caption-unseen 미래 질의를 먼저 확보하고 별도 protocol로 신규 연구를 시작

`RESCUE_INCONCLUSIVE`는 범용 가설이 거짓임을 입증한 것이 아니라 **수개월의 본실험을 승인할 양의 증거가 없다는 판정**이다. 같은 데이터에서 기준을 완화하거나 서비스군을 다시 나눠 통과를 찾지 않는다. 향후에는 oracle-free view selection, 자동 trajectory 표현, caption failure-boundary 가운데 하나를 독립된 좁은 연구로 재정의할 수 있다.

---

## 참고문헌 및 1차 자료

1. FOLIO: Focused Semantic Memory for Streaming Video Understanding, arXiv:2607.13298, 2026. <https://arxiv.org/abs/2607.13298>
2. PMMC: Prospective Multimodal Memory Compilation for Long-Term LVLM Agents, arXiv:2608.00962, 2026. <https://arxiv.org/abs/2608.00962>
3. VIVA: An End-to-End System for Interactive Video Analytics, CIDR 2022. <https://vldb.org/cidrdb/2022/viva-an-end-to-end-system-for-interactive-video-analytics.html>
4. Optimizing Video Analytics with Declarative Model Relationships, PVLDB 16(3), 2022. <https://www.vldb.org/pvldb/vol16/p447-romero.pdf>
5. KathDB: Explainable Multimodal Database Management System with Human-AI Collaboration, CIDR 2026. <https://vldb.org/cidrdb/papers/2026/p14-xiao.pdf>
6. Task Cascades for Efficient Unstructured Data Processing, arXiv:2601.05536, 2026. <https://arxiv.org/abs/2601.05536>
7. Palimpzest: Optimizing AI-Powered Analytics with Declarative Query Processing, CIDR 2025. <https://www.vldb.org/cidrdb/papers/2025/p12-liu.pdf>
8. LOTUS: Enabling Semantic Queries with LLMs over Tables of Unstructured and Structured Data, PVLDB 18, 2025. <https://www.vldb.org/pvldb/vol18/p2851-patel.pdf>
9. DocETL: Agentic Query Rewriting and Evaluation for Complex Document Processing, PVLDB 18, 2025. <https://www.vldb.org/pvldb/vol18/p3035-shankar.pdf>
10. VOCAL-UDF: A Video Organization and Interactive Compositional AnaLytics System with UDF Generation, SIGMOD 2025. <https://arxiv.org/abs/2408.02243>
11. EVA: A System for Efficient and Expressive Video Analytics, SIGMOD 2022. <https://sites.cc.gatech.edu/fac/Kishore.Ramachandran/pubs/EVA-SIGMOD-2022.pdf>
12. AIDB: A Sparsely Materialized Database for Queries Using Machine Learning Models, DEEM 2024. <https://experts.illinois.edu/en/publications/aidb-a-sparsely-materialized-database-for-queries-using-machine-l/>
13. VSS: A Storage System for Video Analytics, SIGMOD 2021. <https://arxiv.org/abs/2103.16604>
14. iRAG: An Incremental Retrieval Augmented Generation System for Videos, CIKM 2024. <https://arxiv.org/abs/2404.12309>
15. Cerberus: Efficient Inference for Video Anomaly Detection, arXiv:2510.16290, 2025. <https://arxiv.org/abs/2510.16290>
16. OCTOPINF: Workload-Aware Inference Serving for Edge Video Analytics, PerCom 2025. <https://arxiv.org/abs/2502.01277>
17. VectraFlow: Integrating Vectors into Stream Processing, CIDR 2025. <https://vldb.org/cidrdb/2025/vectraflow-integrating-vectors-into-stream-processing.html>
18. VideoLLM-online: Online Video Large Language Model for Streaming Video, 2024. <https://arxiv.org/abs/2406.11816>
19. RTV-Bench: Benchmarking Real-Time Video Understanding, 2025. <https://arxiv.org/abs/2505.02064>
20. Event-Causal RAG for Streaming Event Understanding, 2026. <https://arxiv.org/abs/2605.06185>
21. CARVE/V-RAGBench, 2026. <https://arxiv.org/abs/2606.13141>
22. VideoRAG: Retrieval-Augmented Generation over Video Corpus, 2025. <https://arxiv.org/abs/2502.01549>
23. Qwen2.5-VL Technical Report, 2025. <https://arxiv.org/abs/2502.13923>
24. Holmes-VAU, CVPR 2025. <https://openaccess.thecvf.com/content/CVPR2025/papers/Zhang_Holmes-VAU_Towards_Long-term_Video_Anomaly_Understanding_at_Any_Granularity_CVPR_2025_paper.pdf>
25. Anomize, CVPR 2025. <https://openaccess.thecvf.com/content/CVPR2025/papers/Li_Anomize_Better_Open_Vocabulary_Video_Anomaly_Detection_CVPR_2025_paper.pdf>
26. UBnormal, CVPR 2022. <https://openaccess.thecvf.com/content/CVPR2022/html/Acsintoae_UBnormal_New_Benchmark_for_Supervised_Open-Set_Video_Anomaly_Detection_CVPR_2022_paper.html>
27. UCF-Crime official dataset page. <https://www.crcv.ucf.edu/research/real-world-anomaly-detection-in-surveillance-videos/>
28. AI City Challenge official site. <https://www.aicitychallenge.org/>
29. NVIDIA Video Search and Summarization AI Blueprint. <https://developer.nvidia.com/blog/build-a-video-search-and-summarization-agent-with-nvidia-ai-blueprint/>
30. PVLDB 2027 Research Track scope. <https://vldb.org/2027/call-for-research-track.html>
