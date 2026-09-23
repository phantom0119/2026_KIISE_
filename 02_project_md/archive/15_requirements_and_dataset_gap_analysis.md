# 요구사항 재분류와 추가 데이터셋 필요성 분석

작성 기준일: 2026-07-07

2026-07-09 최신 갱신: 요구사항 재분류의 방향은 유지하되, 이후 데이터 확보와 실험 실행이 진행되어 추가 데이터셋 확보 병목은 해소되었다. 최신 기준에서는 데이터 추가가 아니라 원고 정합성, claim scope, 표·그림·참고문헌 검수가 병목이다. 최신 판정은 `31_additional_dataset_need_review_20260708.md`와 `40_latest_dataset_and_experiment_synthesis_20260709.md`를 따른다.

## 결론

이전 조사 문서의 “미지 항목은 실제 투고 전 반드시 확정해야 하는 시스템 요구사항”이라는 문장은 **운영 시스템 논문**을 전제로 할 때는 맞지만, 현재 투고하려는 **워크로드/저장·색인 구조 비교 실험 논문**에는 그대로 적용하면 과도하다.

현재 연구의 핵심 주장은 다음이다.

> 도시 감시형 멀티모달 데이터에서 자연어 질의와 metadata filter가 결합될 때, BM25/vector-only보다 metadata-aware retrieval과 DB prefilter 구조가 더 나은 recall-latency 균형을 보이는가?

따라서 투고 전 반드시 확정해야 하는 것은 “실제 도시 관제센터 운영 요구사항”이 아니라, **논문 실험에서 통제되는 데이터·질의·평가·실행환경 요구사항**이다.

## 가정/미지 항목 재분류

| 항목 | 기존 상태 | 본 연구에서의 필요성 | 판정 |
|---|---|---|---|
| 데이터 모달리티 | 가정 | 영상, caption/report text, metadata는 필요. 센서 로그·지도·기상은 있으면 좋지만 필수 아님 | 부분 필수 |
| 질의 형태 | 가정 | 자연어 질의 + metadata filter는 필수. 이미지 질의는 현재 논문 범위에서는 선택 | 필수/선택 분리 |
| 운영 환경 | 미지 | 실제 관제 운영환경은 불필요. 실험환경은 확정 필요 | 운영 미필수, 실험환경 필수 |
| 카메라 수/일일 유입량 | 미지 | throughput/capacity planning을 주장하지 않으면 불필요 | 선택 |
| 저장 보존 기간 | 미지 | 장기 보존정책 연구가 아니므로 불필요. 저장 cost 논의는 artifact 크기로 대체 가능 | 선택 |
| 개인정보 비식별화 정책 | 미지 | 공개/비식별 데이터 사용 사실과 한계 명시는 필수. 기관 운영정책 확정은 불필요 | 윤리 명시 필수 |
| 어노테이션 가용성 | 가정 | qrels 생성 가능성과 label 신뢰성은 필수 | 필수 |
| 응답 형태 | 가정 | retrieval 논문에서는 top-k evidence clip/document가 필수. VLM 답변 생성은 선택 | evidence 필수, 답변 생성 선택 |

## 반드시 확정해야 하는 항목

KIISE DBR 투고 전 실제로 확정해야 하는 항목은 아래 7개다.

| 항목 | 현재 상태 | 필요 조치 |
|---|---|---|
| 주 데이터셋 | VRU-Accident | main result로 확정 |
| 국내 CCTV 보강 데이터셋 | AI Hub 지능형 CCTV, AI Hub 이상행동 CCTV | extension result로 확정 |
| canonical schema | 구현 완료 | 논문 Method 섹션에 명시 |
| query/qrels 생성 방식 | 구현 완료 | semantic filter와 metadata filter 분리 근거 명시 |
| 비교 baseline | B0~B5, pgvector P2/P4 | 표/그림에 반영 |
| 실행환경 | 로컬 GPU, conda, Docker pgvector | 실험환경 표로 고정 |
| 개인정보/윤리 | 공개/비식별 데이터 사용 | 실제 관제 데이터가 아님을 한계로 명시 |

## 반드시 확정하지 않아도 되는 항목

아래 항목은 실제 운영 시스템을 배포하거나 capacity planning 논문으로 쓸 때 필요하다. 현재 투고 범위에서는 “한계 및 향후 연구”로 넘기는 것이 맞다.

| 항목 | 이유 |
|---|---|
| 실제 관제센터 운영환경 | 본 연구는 운영 배포가 아니라 retrieval workload와 backend 비교 |
| 실제 카메라 수/일일 유입량 | throughput claim을 하지 않으면 불필요 |
| 저장 보존 기간 | retention policy 연구가 아니며, artifact storage cost 정도만 기록하면 충분 |
| 기관별 개인정보 처리정책 | 공개/비식별 데이터만 사용하므로 실제 기관정책 확정은 불필요 |
| 이미지 질의 | text+metadata retrieval만으로 현재 연구질문 성립 |
| 센서 로그 | metadata-aware retrieval을 보이기 위한 충분조건이지만 필요조건은 아님 |

## 현재 확보 데이터셋으로 가능한 주장

현재 확보된 데이터셋과 결과만으로 가능한 주장은 다음까지다.

| 주장 | 가능 여부 | 근거 |
|---|---|---|
| metadata-aware retrieval이 vector-only보다 강하다 | 가능 | VRU, AI Hub 모두 B3/B4/B5 우위 |
| SQL metadata prefilter + vector search가 DB backend에서 동작한다 | 가능 | pgvector P4가 FAISS B4 품질 재현 |
| 국내 CCTV 데이터에도 동일 canonical protocol을 적용할 수 있다 | 가능 | AI Hub 지능형 CCTV와 이상행동 CCTV canonical/retrieval 완료 |
| 센서 로그까지 포함한 완전한 도시 관제 DB를 평가했다 | 불가 | 현재 센서 로그 없음 |
| 이미지 질의 또는 VLM answer generation까지 평가했다 | 불가 | 현재 text evidence retrieval 중심 |
| 실제 관제센터 운영 규모의 throughput/cost를 평가했다 | 불가 | 카메라 수/일일 유입량/retention 미정 |

## 추가 데이터셋 필요성

추가 데이터셋은 “논문 성립에 필요한가?”와 “주장 확장에 유리한가?”를 나눠 판단해야 한다.

### 필수 여부

현재 상태에서 KIISE DBR 투고 자체를 위해 **추가 데이터셋은 필수는 아니다**.

이미 확보한 데이터셋:

| 데이터셋 | 역할 | 현재 상태 |
|---|---|---|
| VRU-Accident | main retrieval benchmark | canonical, embedding, B0~B5, pgvector 완료 |
| AI Hub 지능형 관제 CCTV | 국내 CCTV extension | raw, canonical, bge/e5 B0~B5 완료 |
| AI Hub 이상행동 CCTV | 국내 이상행동 CCTV extension | zip/XML raw 정리, canonical, bge/e5 B0~B5 완료 |

다만 논문의 표현은 조정해야 한다. “센서 로그, 지도·기상 메타데이터까지 포함한 완전한 도시 관제 시스템”이 아니라, **영상 이벤트, caption/report text, 구조화 event/time/context metadata를 결합한 VLM-DB retrieval workload**로 써야 한다.

## 추가 확보 우선순위

2026-07-08 갱신: AI Hub 다각도 CCTV 생활안전 데이터, 시내도로 CCTV, 교차로신호체계가 external 원본으로 확보되었다. 따라서 아래의 “추가 확보 우선순위”는 과거 gap 분석 기록이며, 최신 의사결정은 `31_additional_dataset_need_review_20260708.md`의 “데이터셋 확보 완료” 판정을 따른다.

### 1순위: AI Hub 교차로 신호 체계·보행자·차량 이동 복합 데이터

| 항목 | 판단 |
|---|---|
| 필요 이유 | 현재 부족한 센서/정형 로그 축을 보강 |
| 기대 효과 | 통과차량, 보행량, 신호/이동 CSV를 metadata selectivity 실험에 사용 가능 |
| 논문 기여 | “영상 + 정형 교통 로그” 결합으로 DB 논문성 강화 |
| 리스크 | 텍스트/VQA가 없어 caption/report는 생성 또는 템플릿 필요 |
| 우선도 | 높음 |

공식 설명 기준 이 데이터는 교차로 CCTV 영상, 통과차량 CSV, 보행량 CSV, 도로차량 XML 등을 포함한다. 따라서 “센서 로그/정형 로그가 없다”는 현재 약점을 가장 직접적으로 보완한다.

### 2순위: AI Hub 다각도 CCTV 생활안전 데이터

최신 상태: 확보 완료. `Datasets/external/21.다각도 CCTV 생활안전 데이터`를 main multimodal anchor로 사용한다.

| 항목 | 판단 |
|---|---|
| 필요 이유 | text+video+VQA+CoT+caption을 갖춘 가장 강한 국내 CCTV 멀티모달 후보 |
| 기대 효과 | 현재 text retrieval 중심 실험을 VQA/evidence answer까지 확장 가능 |
| 논문 기여 | 국내 멀티뷰 CCTV VLM-DB benchmark 주장 강화 |
| 리스크 | 약 482GB급 대용량, 신청/다운로드/전처리 시간 부담 |
| 우선도 | 높음, 단 이번 투고에는 optional |

공식 AI Hub 페이지 기준 2025 구축, 2026-06 갱신 데이터이며 텍스트와 비디오 유형, LMM 생성 방식으로 제공된다.

### 3순위: TUMTraffic-VideoQA

| 항목 | 판단 |
|---|---|
| 필요 이유 | 국제 roadside traffic VideoQA benchmark |
| 기대 효과 | 해외 수준 학회 관심사와 직접 연결 |
| 논문 기여 | 1,000 videos, 85K QA, captioning, grounding 기반의 국제 비교 근거 |
| 리스크 | 원본 데이터 접근/등록 절차, 현재 투고 일정 내 확보 불확실 |
| 우선도 | 중간~높음 |

논문 공개 정보 기준 1,000 videos, 85,000 QA, 2,300 object captioning, 5,700 grounding annotation을 제공한다.

### 4순위: WTS

| 항목 | 판단 |
|---|---|
| 필요 이유 | fixed overhead camera + ego view + traffic safety caption/VQA |
| 기대 효과 | 보행자 중심 교통 안전 이벤트의 fine-grained caption 보강 |
| 논문 기여 | multi-view traffic safety evidence retrieval 확장 |
| 리스크 | 신청/다운로드 절차, staged event 성격 |
| 우선도 | 중간 |

공식 GitHub 설명 기준 1.2K video events, 130+ traffic scenarios, videos/captions/VQA/3D gaze/bbox를 포함한다.

### 5순위: AI Hub 교통사고 영상 데이터

| 항목 | 판단 |
|---|---|
| 필요 이유 | 교통사고 이벤트와 객체/장소 label 규모 확장 |
| 기대 효과 | 차대차, 차대보행자, 차대이륜차, 횡단보도 등 사고 qrels 강화 |
| 논문 기여 | VRU-Accident의 국제/대시캠 편향을 국내 사고 데이터로 보완 |
| 리스크 | 텍스트/VQA 없음. caption/report 생성 필요 |
| 우선도 | 중간 |

## 추가 데이터셋이 실제로 필요한 경우

아래 주장을 논문에 넣으려면 추가 데이터셋이 필요하다.

| 넣고 싶은 주장 | 필요한 데이터셋 |
|---|---|
| 센서 로그까지 포함한 도시 관제 DB | AI Hub 522 교차로 복합 데이터 |
| VQA/CoT answer generation까지 평가 | AI Hub 71953 다각도 CCTV 또는 TUMTraffic-VideoQA |
| 국제 roadside traffic benchmark와 직접 비교 | TUMTraffic-VideoQA, WTS |
| 국내 교통사고 대규모 event label 평가 | AI Hub 597 교통사고 영상 데이터 |
| 이미지 질의 또는 visual embedding 평가 | AI Hub 165/597/71953, keyframe extraction, CLIP/SigLIP 추가 |

## 투고 전략

2주 일정에서는 다음 전략이 가장 안전하다.

1. 현재 확보한 VRU-Accident, AI Hub 지능형 CCTV, AI Hub 이상행동 CCTV 결과를 논문 본문에 사용한다.
2. “미지” 운영 요구사항은 실제 시스템 배포 요구가 아니라 한계와 향후 연구로 명시한다.
3. 추가 데이터셋은 논문 실험의 필수 조건이 아니라 확장 가능성으로 둔다.
4. 단 하나만 더 확보한다면 AI Hub 522를 우선한다. 이유는 현재 부족한 정형 교통 로그/센서 로그 축을 가장 직접적으로 보완하기 때문이다.
5. VQA 중심 실험은 AI Hub 71953 확보 완료로 수행 가능하다. TUMTraffic-VideoQA는 이번 투고의 필수 경로로 두지 않는다.

## 최종 권고

현재 논문 제목과 주장을 아래처럼 조정하면 추가 데이터셋 없이도 방어 가능하다.

> 도시 감시형 영상 이벤트 데이터에서 메타데이터 인지 하이브리드 검색 구조의 성능 분석

피해야 할 표현:

- “센서 로그와 지도·기상 메타데이터를 모두 포함한 통합 도시 관제 시스템”
- “실제 관제센터 운영 규모 검증”
- “이미지 질의와 VLM 답변 생성을 포함한 완전한 VLM-DB”

사용 가능한 표현:

- “영상 이벤트, 사건 caption/report, 구조화 metadata를 결합한 canonical retrieval workload”
- “metadata selectivity에 따른 BM25/vector/pgvector prefilter 구조 비교”
- “국내 CCTV 2종과 국제 사고 VideoQA 데이터에 동일 프로토콜 적용”

## 참고한 주요 출처

- AI Hub 다각도 CCTV 생활안전 데이터: https://www.aihub.or.kr/aihubdata/data/view.do?aihubDataSe=data&dataSetSn=71953
- AI Hub 교차로 신호 체계·보행자·차량 이동 복합 데이터: https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=522
- TUMTraffic-VideoQA: https://arxiv.org/abs/2502.02449
- WTS dataset GitHub: https://github.com/woven-visionai/wts-dataset
- AI Hub 교통사고 영상 데이터: https://aihub.or.kr/aihubdata/data/view.do?dataSetSn=597
