# 20_RELATED_WORK — 관련 연구 검토 통합본 (UCA/VALU 검토 + 관련연구 대비 기여 강화 설계)

## 1. 머리말

**문서 목적**: 관련 연구 검토(UCA/VALU 심층 검토, 3+1축 관련연구 지형, 기여 강화 설계안)를 하나로 통합하고, 제출 논문 §2의 최종 비교 구도(VideoRAG·CLIP·VBASE·ACORN은 축별 개별 발전, 본 연구는 통합 종단 측정 + 비순환 평가)와 정합하도록 정리한 관련 연구 정본이다.

**통합 출처** (원본은 아래 경로로 이관 예정):

| 원본 | 아카이브 경로 |
|---|---|
| 200_RELATED_uca_valu_review_20260710.md (2026-07-10) | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/200_RELATED_uca_valu_review_20260710.md` |
| 740_RELATED_reinforcement_design_review_20260714.md (2026-07-14) | `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/740_RELATED_reinforcement_design_review_20260714.md` |

**SYNC 기준: paper_final.pdf(2026-07-23) + 2026-07-28 검증 세션.** 수치·구도·용어가 소스와 상충하면 논문 정본을 우선하고, 의미 있는 이력은 `[정정 2026-07-28: ...]`로 남긴다.

**용어 적용 노트(2026-07-28 확정, 현 제출 PDF에는 미적용·보고서/개정 원고용)**: 본 문서는 '데이터베이스 계층'→'벡터 데이터베이스 계층'으로, 소스의 'evidence(-layer)' 계열 용어는 맥락에 따라 DB 반환=**상위 k 검색 결과**, VLM 입력=**검색 문맥(retrieved context)**, 정답 판정=**관련 클립/검색 정답 집합**으로 치환하여 기술한다. 소스 원문 인용부(영문 차별성 문장, 금지 표현 목록 등)는 이력 보존을 위해 원문 그대로 둔다.

---

## 2. 현행 정리

### 2.1 제출 논문 §2의 최종 비교 구도 (정본)

제출 논문(확정 국문 제목: "종단형 멀티모달 RAG 파이프라인 성능 향상을 위한 비순환 평가 및 검색 품질-비용에 대한 실증 연구") §2의 최종 구도는 다음과 같다.

- **VideoRAG·CLIP·VBASE·ACORN은 각각 축별 개별 발전**이다 — 비디오 RAG 파이프라인, 멀티모달 표현, DBMS-벡터 질의 통합, 조건부(hybrid) 벡터 검색이라는 개별 축을 각자 전진시켰다.
- **본 연구는 통합 종단 측정 + 비순환 평가**다 — 벡터 데이터베이스 계층의 다섯 설계 축(①검색용 데이터 ②검색 계획 ③검색 신호·순위 융합 ④물리 색인 ⑤배포)을 유효 조합 1×4+4×3=16 × 색인 설정 7 = **112 구성**으로 한 파이프라인 안에서 통제 비교하고, 평가 자체의 순환성을 RQ1에서 먼저 검증(비순환 평가)한 뒤 검색 품질-비용을 실증한다.

이 구도가 아래 모든 검토 내용의 상위 프레임이다. [정정 2026-07-28: 소스 검토(2026-07-10/14) 시점의 비교 구도는 "3축 지형(비디오 DB 시스템 / filtered vector search / 감시 VLM 벤치마크)"의 넓은 매트릭스였으나, 최종 제출본 §2는 VideoRAG·CLIP·VBASE·ACORN 4개 대표를 축별 발전으로 세우고 본 연구를 "통합 종단 측정 + 비순환 평가"로 대비시키는 압축 구도로 확정되었다. 3축 지형은 아래 §2.2에 심사 대응·개정용 배경 지식으로 전량 보존한다. 단, VideoRAG·CLIP 개별 검토 메모는 본 통합 대상 두 소스에는 없었다.]

### 2.2 관련 연구 지형 — 3+1축 인벤토리 (검토 기준: 2026-07-14 웹 확인)

**총괄 판정**: 동일 주제를 그대로 수행한 상위 학회/저널 논문은 확인되지 않는다. 다만 인접 상위권 연구가 세 축으로 강하게 존재하며, 본 연구는 "완전히 새로운 모든 것"이 아니라 세 축의 교차점에 위치한다.

> 기존 비디오 DB 연구는 객체·트랙·시공간 질의처리에 강하지만 VLM-QA용 검색 문맥 계층과 비순환 멀티모달 워크로드를 다루지 않는다.
> 기존 filtered vector search 연구는 vector+structured predicate의 알고리즘/시스템을 다루지만 감시 영상의 실제 메타데이터 조건, 저장 단위, VLM-QA 답변 연결을 다루지 않는다.
> 기존 감시 VLM 연구는 모델 이해·QA 성능을 평가하지만 DB의 저장·색인·검색 구조를 통제 비교하지 않는다.
> 본 연구는 이 세 축의 교차점에서, 고정 모델 환경의 벡터 데이터베이스 계층을 정확도·지연·저장 관점으로 평가한다.

#### 2.2.1 비디오 DB/시스템 질의처리

| 연구 | venue | 핵심 내용 | 본 연구와의 차이 |
|---|---|---|---|
| NoScope | PVLDB 2017 | 고정 카메라/감시 영상에서 NN query 비용을 줄이는 특화 모델 cascade | binary/object query 중심, 자연어+metadata+VLM-QA 아님 |
| Focus | OSDI 2018 | ingest-time approximate index와 query-time expensive CNN을 나눠 low-cost/low-latency video query 지원 | 객체 클래스 검색 중심, VLM 검색 문맥 구조 비교 아님 |
| BlazeIt | PVLDB 2020 | FrameQL로 video analytics aggregation/limit query 최적화 | declarative object/spatiotemporal query 중심 |
| MIRIS | SIGMOD 2020 | object track query를 추적과 질의처리로 통합 | 트랙 predicate 질의 |
| OTIF | SIGMOD 2022 | large video에서 general-purpose object tracks를 효율적으로 전처리 | track extraction/V-ETL 계열. 자연어+메타데이터+VLM-QA 아님 |
| EQUI-VOCAL | PVLDB 2023 | 사용자 피드백으로 compositional video event query를 합성 | scene graph/query synthesis 중심. 저장 단위·filtered vector DB 비교 아님 |

판정: 이 축은 본 연구의 DB 정당성을 뒷받침하는 필수 관련연구다. 직접 비교군이라기보다 "기존 VDBMS가 다루던 질의처리 문제를 VLM-QA용 검색 문맥 계층으로 확장한다"는 위치 설정에 사용한다. [정정 2026-07-28: 소스에는 "MIRIS를 index 정책 검증에 활용 가능", "MEVA/MIRIS는 외적타당성/구현 검증" 등 제2 데이터셋 트랙 구상이 있었으나, 최종 제출본의 실험은 AI Hub CCTV 정본 코퍼스(3,000 clips / 85 queries / strict qrels 6,809 / semantic qrels 24,872) 단일 코퍼스 체계이며 MEVA[20]는 클립 조작적 정의(데이터셋 배포 mp4 1파일=1클립)의 계보 방어 근거로만 쓰인다.]

#### 2.2.2 filtered vector search / vector DB

| 연구 | venue | 핵심 내용 | 본 연구와의 차이 |
|---|---|---|---|
| Filtered-DiskANN | WWW 2023 | filter-aware ANN graph로 filtered ANNS 지원 | 일반 ANN 알고리즘. 감시 메타데이터 조건·VLM-QA workload 아님 |
| VBASE | OSDI 2023 | vector similarity search와 relational query를 relaxed monotonicity로 통합 | DBMS+vector query 일반론. 영상 검색 문맥 계층 설계 아님. **최종 §2 대표 4개 중 하나** |
| ACORN | SIGMOD 2024 | HNSW 기반 predicate-agnostic hybrid search | 강한 직접 관련. 본 연구는 ACORN류를 발명하는 것이 아니라 실제 감시 메타데이터 조건에서 평가 편향과 설계 정책을 보임. **최종 §2 대표 4개 중 하나** |
| pgvector iterative scan | system feature | filtered vector search에서 충분한 결과가 나올 때까지 index scan 확장 | 관계형 DB 구현 실험과의 연결점(검토 시점 구상) |

판정: 본 연구의 색인·배포 축(최종 §4.2 축④⑤, RQ5)은 이 분야와 직접 연결된다. 차별점은 "새 filtered ANN 알고리즘"이 아니라, **실측 메타데이터·시공간 조건이 random-mask 평가와 다르게 작동하며 조건별 부분 색인 정책이 필요함을 실제 감시·교통 코퍼스에서 보였다**는 점이다. [정정 2026-07-28: 검토 시점의 "pgvector 백엔드 실측" 서술은 이력이며, 최종 제출본 RQ5의 시스템 준거는 Milvus/Weaviate다 — 필터율≥92.3% 또는 조건 만족 벡터<40,000이면 전수 검색 자동 전환. 확정 수치: 실측 군집 조건에서 전역 색인 재현율 손실 최대 0.627(무작위 대조는 최대 0.047 변동→과소평가), 조건별 부분 색인은 98.12~100% 회복, 배포 규칙=전역 재현율 목표 0.95 미달 시 부분 색인/전수 검색 + 색인 갱신 시점까지 예상 질의 수의 선택도별 손익분기.]

#### 2.2.3 감시·도시 VLM/Video-Language 벤치마크

| 연구 | venue/status | 핵심 내용 | 본 연구와의 차이 |
|---|---|---|---|
| UCA/VALU | CVPR 2024, TCSVT 2025 | 감시 video-language understanding 데이터셋과 모델 벤치마크 | 모델 이해 평가. DB 저장·색인·검색 구조 비교 아님 (심층 검토는 §2.3) |
| HAWK | NeurIPS 2024 | open-world video anomaly understanding, VLM QA/description | 모델/데이터셋 기여. 벡터 데이터베이스 계층 설계 아님 |
| UrBench | AAAI 2025 | multi-view urban scenario에서 LMM 평가 | 도시 LMM 벤치마크. 코퍼스 검색·vector DB 구현 아님 |
| ForeSea | arXiv 2026 | image+text query 기반 forensic surveillance video QA/retrieval | 주제는 매우 가깝지만, 검토(2026-07-14) 기준 top venue 게재 논문은 아님. DB 저장 단위·부분 색인·비순환 감사 중심은 아님 |

판정: UCA/VALU, HAWK, UrBench는 "감시·도시 도메인에서 VLM이 어렵다"는 동기 근거로 매우 중요하다. ForeSea는 최신 직접 인접 연구로 반드시 언급하되, 본 연구의 DB 시스템 기여와 구분해야 한다.

#### 2.2.4 GraphRAG / multimodal RAG (+1축)

| 연구 | 핵심 내용 | 본 연구와의 차이 |
|---|---|---|
| Microsoft GraphRAG | text corpus에서 entity/relation graph와 community summary를 이용한 RAG | 주로 텍스트 corpus의 전역 요약/QA. 감시 영상 메타데이터 조건 DB 구조 아님 |
| LightRAG | graph+vector를 결합한 경량 RAG | text/document RAG 중심 |
| RAG-Anything / multimodal graph RAG 계열 | multimodal document를 entity/graph로 연결 | multimodal document QA 중심. 도시 감시 영상 검색 문맥 계층의 storage/index 실험과 다름 |

판정: GraphRAG는 주력 비교축이 아니라 boundary/negative result로 두는 것이 안전하다. KG 실험은 새로운 독립 신호를 만들지 못했고, 센서/설명문 정보를 그래프로 재표현한 수준에 가깝다. [정정 2026-07-28: 이 권고는 최종 제출본에서 수치로 확정 이행되었다 — RQ4(§5.2.4): 전 신호 독립 이득 없음(메타 단독 0.218/0.217, BM25 0.017/0.050, 벡터 0.059/0.170, 혼합 RRF 0.133<벡터 0.154), 지식그래프 재조합 Lift 중앙값 0.002 무이득.]

### 2.3 UCA/VALU 심층 검토 (Yuan et al., IEEE TCSVT 35(1), 2025)

검토 대상: **"Surveillance Video-and-Language Understanding: From Small to Large Multimodal Models"**, DOI 10.1109/TCSVT.2024.3462433 (CVPR 2024 "Towards Surveillance Video-and-Language Understanding"의 저널 확장판). 원문: `survey/paper/Surveillance Video-and-Language Understanding_ From Small to Large Multimodal Models.pdf` (15쪽 전문 정독, 2026-07-10).

**한 줄 판정**: 직접 비교군(동일 지표 head-to-head)으로는 부적합 — 그들은 *모델*을 평가하는 이해(understanding) 벤치마크, 우리는 *저장·색인·검색 구조*를 평가하는 데이터관리 워크로드로 평가 단위가 다르다. 그러나 (a) 관련연구 필수 인용, (b) UCA 데이터셋의 외적타당성 활용, (c) 우리 차별성을 정의해 주는 대조점으로서 가치가 크다.

#### 2.3.1 논문 요지 (사실 정리)

- **UCA 데이터셋**: UCF-Crime(실세계 감시영상 1,900개, 128h) 중 저품질 46개 제외한 **1,854 비디오**에 **23,542개 문장 주석**(평균 20.15단어, 0.1초 단위 이벤트 타이밍, 주석 110.7h) 수작업 부여. 13개 이상행동 클래스+정상. train/val/test = 1,165/379/310.
- **5개 태스크 벤치마크**: ① TSGV(문장→비디오 내 구간 접지; CTRL/SCDM/A2C/2D-TAN/LGI/MMN/MomentDiff, C3D 특징) ② VC(캡셔닝; S2VT/RecNet/MARN/SGN/SwinBERT/CoCap) ③ DVC(TDA-CG/PDVC/UEDVC) ④ MAD(이상탐지; TEVAD + 자체 개선판: UCA-finetuned "Surveillance SwinBERT" 캡션 분기 추가로 AUC 83.1→85.3%) ⑤ MLLM VC(StableLM/MOSS/MiniGPT-4/VideoChat/VideoChat2 + VideoChat2 LoRA 파인튜닝(rank16/α32/8frames)으로 대폭 향상).
- **핵심 발견**: 일반 비디오에서 잘 되는 SOTA가 감시영상에서 일제히 저조(TSGV R@1 IoU0.3 대부분 <10%) — 장시간·저해상도·고정시점·중복성 때문. 도메인 캡셔너가 이상탐지를 돕는다.

#### 2.3.2 비교군 적합성 — 직접 비교는 NO, 적응 경로는 있음

| 그들의 태스크 | 우리 실험과의 관계 |
|---|---|
| TSGV (비디오 **내** 구간 접지) | 우리의 **코퍼스 수준 클립 검색**과 태스크 정의가 다름 — 질의당 후보가 "한 비디오의 시간축" vs "수천 클립 코퍼스". 직접 비교 불가 |
| VC/DVC (캡션 생성) | 우리 파이프라인에선 **검색용 데이터(영상 설명문) 구축 도구**에 해당(우리의 VLM 캡셔너 역할). 지표 비교 대상 아님 |
| MAD (이상탐지 AUC) | 우리 워크로드에 없는 태스크 |
| MLLM VC 벤치마크 | 우리의 답변 계층(고정 생성모델, 벡터 데이터베이스 계층이 반환하는 검색 문맥만 변경)과 목적이 반대 — 그들은 모델을 바꿔 비교, 우리는 모델을 고정 |

그들 실험엔 **벡터 색인·메타데이터 필터·저장/지연/비용 축이 전혀 없다**(모델 FLOPs/추론시간만 보고). 따라서 "비교군 테이블에 나란히 놓는" 사용은 성립하지 않는다.

**성립하는 사용 3가지**:
1. **관련연구 인용**: §2에 ForeSea·UrBench와 함께 "이해 벤치마크 vs 구조 벤치마크" 구분 축으로 배치. 그들의 "일반 SOTA가 감시영상에서 붕괴" 발견은 *모델 개선만으로는 부족하고 벡터 데이터베이스 계층(검색 문맥 공급 구조)이 필요하다*는 우리 동기를 외부 근거로 보강한다.
2. **우리 발견의 교차 확인**: 그들의 MAD 개선(도메인 캡셔너가 이상 프레임의 캡션 품질을 올려 AUC 상승)은 우리의 "VLM 설명문의 서술 맹점" 발견과 같은 축 — "설명문 품질이 다운스트림을 좌우한다"를 이해 태스크 쪽에서 재확인해주는 인용처.
3. **문서-채널 강건성 ablation 재료**(선택): 공개 시 그들의 finetuned VideoChat2/Surveillance-SwinBERT를 우리 캡셔너 대체로 써 "설명문 채널 인코더 민감도"를 측정 가능(가중치 공개 여부 미확인 — 착수 전 확인 필요).

#### 2.3.3 UCA 데이터셋 활용 — 검토 시점 판정과 최종 이행

**획득 가능성(확인 완료)**: 주석 txt/json 공개(GitHub 페이지), 원본 비디오는 UCF CRCV 직링크 zip(등록 불필요, ~37GB). *라이선스 주의: 논문은 Apache 2.0, 프로젝트 페이지는 "학술 연구 전용" — 원고에는 후자 기준으로 명기.*

검토 시점(2026-07-10) 변환 설계 스케치: 설명문=우리 파이프라인의 VLM 캡션(프레임 픽셀만, 채널 독립), 관련 클립 판정=UCA 사람 문장주석+0.1초 타이밍(주석자 채널, 채널 독립, segment-level GT 가능), 조건=클래스(13)·duration·이벤트 길이 bin. 단, 클래스 조건은 관련 클립 판정과 강결합(순환 재발 위험)이므로 비순환 감사·결합도 곡선(Cramér's V) 필수 적용, 저결합 조건(duration bin, 이벤트 위치 등)만 헤드라인. 이벤트 평균 16.9초 → event-centered 프레임 추출, 캡션 3–5K segment ≈ 2–3 GPU-h.

**무엇을 사주는가**: 영어·국제·심사자가 아는 벤치마크(UCF-Crime) 기반의 외적타당성 트랙; 장시간·저해상도·중복성이라는 새로운 스트레스 조건; segment-level 검색 GT.
**무엇을 못 사주는가**: 센서/시공간 조건 없음 → 정본 코퍼스의 센서 헤드라인을 대체·재현 불가. VQA도 없어 답변 계층은 캡션 기반 MCQ를 새로 구성해야 함.

[정정 2026-07-28: 검토 시점 판정은 "P2(인용은 지금, 채택은 조건부 — 심사 압박 또는 여력 발생 시)"였으나, 최종 제출본에는 **UCA 129질의 재현 세트가 RQ3(§5.2.3, 표5·6)에 실제 포함되어 4개 검증 항목 중 3개가 재현(3/4)**되었다. 즉 P2 어댑터 구상은 조건부 계획 단계를 넘어 부분 이행된 상태다. 37GB 전체 채택·segment-level GT 트랙은 여전히 후속 확장 후보다.]

#### 2.3.4 재현성 판정

| 항목 | 판정 | 근거 |
|---|---|---|
| 주석 데이터 | 양호 | txt+json 공개, 스플릿 문서화, 주석 가이드라인·검수 절차 상세(10명+검수 3명, 2개월) |
| 원본 비디오 | 양호 | UCF-Crime 직링크(등록 불필요) |
| 태스크 파이프라인 | 중간 | 베이스라인 7+6+3+α개가 2015–2023 개별 레거시 코드베이스; C3D(Sports1M)/I3D 특징 추출은 외부 저장소 의존(각주의 RTFM 링크). 구현 세팅 문단은 상세하나 전체 재실행은 수 주 규모 노동 |
| MLLM 실험 | 중간 | Ask-Anything(OpenGVLab) 기반, LoRA 설정 공개; finetuned 가중치 공개 여부 불명 |
| **우리 용도 기준** | **충분** | 우리는 그들 모델 zoo를 재현할 필요가 없고 데이터(주석+비디오)만 우리 정본 체인에 넣으면 됨 — 그 경로는 전부 우리 통제 하에 있음 |

#### 2.3.5 UCA/VALU 대비 차별성 명시문

| 축 | UCA/VALU (TCSVT'25) | 본 연구 |
|---|---|---|
| **평가 단위** | 어떤 **모델**이 감시영상을 이해하는가 (모델 벤치마크) | 어떤 **저장·색인·검색 구조**가 VLM-QA를 지원하는가 (**모델은 고정**, 구조만 변경하는 통제 실험) |
| **질의 모델** | 문장 → 비디오 내 구간(TSGV) / 캡션 생성 | **자연어 + 메타데이터 조건** → 코퍼스 수준 필터드 검색 (검색 전 조건/검색 후 조건/벡터 단독/혼합의 검색 계획) |
| **모달리티** | 비디오+언어 (2채널) | 비디오+언어+**구조화 메타데이터 레코드** (소스 수준 분리) |
| **평가 타당성 장치** | 사람 주석 GT (순환성 이슈 자체가 없는 태스크 구성) | **비순환 평가(RQ1)·이중 qrels(strict 6,809/semantic 24,872)·결합도 분석** — 워크로드 구성 자체의 타당성을 먼저 검증 |
| **시스템 축** | 모델 FLOPs·추론시간 | **색인 recall–latency–storage 축, 조건부 벡터 검색 계획, 근사 색인(HNSW/IVF)·배포(전역/부분 색인) 통제 비교** |
| **결론의 종류** | "감시영상은 어렵다, 도메인 파인튜닝이 돕는다" | "검색 전 조건의 가치는 제약의 성격과 조건-관련성 결합도가 결정한다" 류의 **구조 선택 가이드라인** |

원고용 차별성 문장(2026-07-10 초안, 원문 보존): *"UCA/VALU benchmarks what models understand about surveillance video; we benchmark what data-management structures deliver to a fixed VLM — retrieval plans, index structures, and storage back-ends under joint natural-language + sensor/spatiotemporal predicates, with workload validity itself machine-audited for non-circularity."*

**중복 리스크: 낮음(상보적).** 그들의 "최초 멀티모달 감시 데이터셋" 주장은 *비디오+언어* 범위 — 우리의 멀티모달 주장은 *구조화 메타데이터를 1급 DB facet으로 결합하고 종단 파이프라인을 통합 측정*하는 것이므로 표현만 구분하면 충돌 없음(§2에서 명시 구분).

### 2.4 본 연구의 확실한 결론 — 최종 제출본 수치로 SYNC

검토 시점(2026-07-14)에 "확실하게 주장 가능"으로 정리한 7개 결론을, 최종 제출본의 확정 수치로 갱신하여 보존한다.

1. **비순환 워크로드가 필요하다.** 필터·관련성 판정·문서가 같은 라벨에서 나오면 검색 전 조건의 우위가 구성상 보장될 수 있다. [정정 2026-07-28: 최종 수치(RQ1) — 순환 수정 전후 0.9736→0.3174(VRU), 1.0000→0.8395(지능형 관제); 통제 주입 실험 0.181→1.000(정답 필터)/0.854(라벨 재진술). 소스의 "522 tri-source 소스 분리" 서술은 검토 시점 프레이밍이며, 최종 정본 코퍼스는 3,000 clips / 85 queries다.]
2. **엄격(hard) 제약에서는 검색 전 조건이 강하다 — 단, '자명한 결과'로 해석한다.** [정정 2026-07-28: 최종 수치(RQ3, 표5·6) — 엄격 기준 검색 전 조건 Δ+0.0983 유의. 다만 최종 논문은 이를 성능 우위 주장이 아니라 '자명한 결과'로 해석한다. 소스의 "522와 MEVA에서 재현" 서술은 검토 시점 이력이며, 최종 재현 근거는 UCA 129질의 재현 세트 3/4다.]
3. **유연(soft) 의도에서는 검색 전 조건 효과를 과장하면 안 된다.** 의미적으로는 맞지만 메타데이터 조건을 만족하지 않는 결과가 유효할 수 있는 경우, 검색 전 조건이 관련 결과를 제거할 수 있다. 효과는 결합도와 질의 성격에 의존한다. [정정 2026-07-28: 최종 수치(RQ3) — 의미론 기준 벡터 단독 0.170 최고, 검색 전 조건 Δ=-0.0158 무의미; 고결합(V≥0.3) 부분군에서만 Δ+0.1335.]
4. **실제 조건은 random mask와 다르다.** 실제 메타데이터·시공간 조건은 임베딩 공간에서 군집성을 가지며, 동일 선택도 random mask로 근사 색인을 평가하면 재현율 손실을 과소평가한다. [정정 2026-07-28: 최종 수치(RQ5, 표7-10) — 실측 군집 조건에서 전역 색인 재현율 손실 최대 0.627, 무작위 대조는 최대 0.047 변동. 소스의 "recall 과대평가" 표현은 최종 논문의 "무작위 대조는 손실을 과소평가" 관점으로 통일.]
5. **저장 단위(검색용 데이터) 선택은 품질-비용 트레이드오프다.** [정정 2026-07-28: 소스의 "522 clip-caption Pareto 효율 / MEVA frame-vector 유리" 구도는 검토 시점 프레이밍이고, 최종 제출본 축①·RQ2(표4)의 확정 수치는 — 설명문 0.063/0.181/1.15ms/24.6MB 기준선; 다중 이미지(클립당 최대3) 0.101/0.352(의미론 Δ+0.171 유의)/3.65ms/68.4MB(저장 2.8배); 이중 색인(RRF k=60) 0.089/0.293/4.96ms/93.0MB(최고 비용); 저장 비교 전체 BH p=0.112. MEVA 저장 단위 실험은 최종 본문에 없다.]
6. **선택적 조건에서는 조건별 부분 색인 정책이 필요하다.** 선택적 조건에서 전역 색인은 재현율 또는 지연 문제를 만든다. [정정 2026-07-28: 최종 수치(RQ5) — 조건별 부분 색인 98.12~100% 회복; 배포 규칙=전역 재현율 목표 0.95 미달 시 부분 색인/전수 검색 + 색인 갱신 시점까지 예상 질의 수의 선택도별 손익분기; 실무 준거로 Milvus/Weaviate는 필터율≥92.3% 또는 조건 만족 벡터<40,000이면 전수 검색 자동 전환. 소스의 pgvector·hot/cold 표현은 검토 시점 이력.]
7. **검색 구조 차이가 답변 품질로 항상 직결되지는 않는다.** 검색 문맥 품질은 답변에 중요하지만, 코퍼스 규모·VLM 지각·답변 편향이 검색 효과의 전파를 제한한다. [정정 2026-07-28: 최종 수치(RQ6, §5.2.6) — 답변 정확도 31%(무증거)→53%(무관)→67%(벡터 검색)→75%(대상 설명문); 잘 보이는 단일 시점 +15.2%p, 두 시점 동시 제공은 무이득; 근사 색인 재현율 차이의 답변 전파는 표본 부족으로 탐색적(미확립). 2026-07-28 용어 결정에 따라 RQ6 3관문은 '관련 클립 회수→검색 문맥 인식→과제 편향'으로 표기.]

추가로, 검토 시점 결론에 없던 최종 확정 결론 하나를 병기한다: **검색 신호별 독립 이득은 없다(RQ4)** — 메타 단독 0.218/0.217, BM25 0.017/0.050, 벡터 0.059/0.170, 혼합 RRF 0.133<벡터 0.154; 지식그래프 재조합 Lift 중앙값 0.002 무이득. 이는 §2.2.4의 GraphRAG boundary 권고가 수치로 확정된 것이다.

### 2.5 기여 강화 설계안 — 이행 현황 포함

#### P0. 관련연구 대비 comparison matrix (검토 시점 제안, 전량 보존)

| 축 | 기존 VDBMS | 기존 filtered vector search | 기존 감시 VLM benchmark | 본 연구 |
|---|---|---|---|---|
| 평가 대상 | query processing / tracking | ANN+structured filters | VLM/model understanding | storage/index/retrieval structure |
| 질의 | object/track SQL류 | vector+attribute filter | QA/caption/grounding | natural language + sensor/spatiotemporal predicate |
| 데이터 | video frames/tracks | generic embeddings | surveillance video-language | video + caption + sensor metadata + qrels |
| 모델 | detector/tracker 최적화 | ANN index | VLM/LMM 성능 비교 | model fixed, DB structure varied |
| 지표 | latency/cost/F1 | recall/QPS/latency | QA/caption/grounding score | nDCG/recall/latency/storage/answer propagation |
| 타당성 | task-specific | filter benchmark | human annotation | non-circular audit, strict/semantic qrels |

[정정 2026-07-28: 최종 제출본 §2는 이 6×4 매트릭스 대신 VideoRAG·CLIP·VBASE·ACORN 4개 대표를 축별 개별 발전으로 세우는 압축 구도를 채택했다. 위 매트릭스는 심사 답변·개정 원고에서 확장 비교가 필요할 때의 재료로 보존한다.]

#### P0. Contribution 3문장 재고정 (검토 시점 제안, 전량 보존)

1. **Validity contribution**: source-separated non-circular multimodal surveillance retrieval workload.
2. **Design-space contribution**: storage unit, filter placement, hybrid retrieval, index structure를 accuracy·latency·storage로 비교.
3. **Operational DB contribution**: real-predicate filtered vector search에서 partial/local index와 hot/cold policy 도출.

이렇게 쓰면 "모델 논문이 아니다"가 분명해진다. [정정 2026-07-28: 최종 제출본에서 이 3분할은 (1) 비순환 평가(RQ1), (2) 다섯 설계 축 112 구성의 통합 종단 측정(RQ2-4·6), (3) 배포 규칙·부분 색인 손익분기(RQ5)로 대응 구현되었다.]

#### P1. Regime table (검토 시점 제안, 전량 보존 + SYNC 주석)

| regime | 권장 구조 | 근거(검토 시점) | SYNC 주석(2026-07-28) |
|---|---|---|---|
| hard constraint | prefilter/local candidate search | 522, MEVA strict | 최종: 엄격 기준 Δ+0.0983 유의하나 '자명한 결과'로 해석 |
| soft intent + low coupling | vector-only 또는 cautious filtering | semantic qrels | 최종: 벡터 단독 0.170 최고, Δ=-0.0158 무의미 |
| real correlated predicate | random-mask 평가 금지 | filtered-ANN collapse | 최종: 실측 손실 최대 0.627 vs 무작위 0.047 |
| selective predicate | partial/local index | pgvector, MIRIS | 최종: 부분 색인 98.12~100% 회복, Milvus/Weaviate 전수 검색 전환 규칙 |
| broad predicate | global+postfilter | hot/cold policy | 최종: 선택도별 손익분기 규칙으로 정식화 |
| caption weak domain | frame-vector | MEVA storage unit | 최종 본문 미채택(축①은 다중 이미지가 품질 우위, 저장 2.8배) |
| caption aligned domain | clip-caption | 522 storage unit | 최종: 설명문 구성이 비용 기준선(1.15ms/24.6MB) |

#### P1. 저장 단위 비교의 encoder confounding 보강안 (검토 시점 제안)

심사자가 "저장 단위가 아니라 encoder 차이 아닌가?"라고 물을 수 있으므로, CLIP text encoder로 설명문을 임베딩한 구성 추가 또는 caveat 명기를 제안했었다. [정정 2026-07-28: 최종 제출본 축①은 영상 설명문/대표 이미지/이미지·설명문 결합/다중 이미지/이중 색인의 5개 검색용 데이터 구성을 동일 파이프라인에서 비교하는 형태로 정리되었다. encoder confounding 보조 실험의 별도 수행 여부는 SYNC 기준 요약만으로는 확인되지 않으므로 개정 시 caveat 문구 존치 여부를 원문 대조로 확인할 것.]

#### P1. GraphRAG/KG boundary 처리 (이행 완료)

권장 문안(원문 보존): *"We also tested a KG-style extension, but when graph edges are derived from the same sensor/caption channels, the graph does not provide an independent retrieval signal. Therefore, we treat graph-structured retrieval as a boundary case rather than a primary baseline."*

[정정 2026-07-28: RQ4 Lift 중앙값 0.002 무이득으로 확정 이행. "GraphRAG보다 우수" 류 주장은 금지 목록(§2.6) 유지.]

#### P2. 네이티브 QA 데이터셋 추가는 선택 사항

HAWK, SurveillanceVQA, ForeSea류는 "VLM-QA" 이름에는 매력적이지만 DB 기여를 흐릴 수 있다. 추가한다면 목적은 "우리 벡터 데이터베이스 계층이 native QA 데이터에서도 도움이 되는가"의 소규모 sanity check 하나뿐이다. [정정 2026-07-28: 소스의 "2026-07-20 마감 기준" 서술은 이력이며 실제 제출은 2026-07-23(paper_final.pdf)이다. 제출본은 신규 QA 데이터셋 없이 정본 코퍼스+UCA 재현 세트로 마감되었고, 본 판정(선택 사항)은 후속 확장에도 그대로 유효하다.]

### 2.6 원고 표현 규칙 (전량 보존)

#### 좋은 표현 (검토 시점 문안 원문 보존)

> 본 연구는 감시 영상 이해 모델을 새로 제안하는 것이 아니라, 고정된 VLM/LLM 환경에서 DB evidence layer의 저장·색인·검색 구조가 검색 품질과 답변 지원 가능성에 미치는 영향을 평가한다.

> 기존 비디오 DB 연구가 객체·트랙 질의처리 비용을 줄이는 데 집중했다면, 본 연구는 자연어 의미 조건과 센서·시공간 predicate가 결합된 VLM-QA evidence retrieval workload를 다룬다.

> 기존 filtered vector search 연구가 일반 embedding과 attribute filter의 알고리즘 효율을 다룬다면, 본 연구는 실제 감시 센서 predicate가 만드는 correlation과 random-mask 평가 편향, 그리고 관계형 DB 구현 정책을 실측한다.

> 기존 감시 VLM benchmark가 어떤 모델이 영상을 이해하는가를 묻는다면, 본 연구는 모델을 고정한 상태에서 어떤 DB 구조가 좋은 증거를 전달하는가를 묻는다.

[정정 2026-07-28: 위 문안을 개정 원고에 쓸 때는 2026-07-28 용어 결정을 적용할 것 — 'DB evidence layer'→'벡터 데이터베이스 계층', 'evidence retrieval'→'검색 문맥 검색', '좋은 증거를 전달'→'좋은 검색 문맥을 전달'. 또한 셋째 문안의 '관계형 DB 구현 정책'은 최종 준거(Milvus/Weaviate 전환 규칙, 부분 색인 손익분기)로 갱신할 것.]

#### 피해야 할 표현 (금지 목록, 전량 보존)

- "최초의 멀티모달 감시 VLM-QA 연구"
- "GraphRAG보다 우수"
- "VLM-QA end-to-end 성능을 index가 결정"
- "MEVA/MIRIS도 522와 동일한 tri-source"
- "prefilter가 항상 최선"
- "저장 단위 효과가 encoder와 완전히 분리됨"

[주석 2026-07-28: 여섯 항목 모두 최종 제출본 기준으로도 유효한 금지다. 특히 "VLM-QA end-to-end 성능을 index가 결정"은 RQ6에서 근사 색인 재현율 차이의 답변 전파가 표본 부족으로 탐색적(미확립)이므로 계속 금지, "prefilter가 항상 최선"은 RQ3의 '자명한 결과' 해석·의미론 기준 무의미(Δ=-0.0158)와 정면 충돌하므로 계속 금지.]

### 2.7 액션 아이템 (검토 시점 → 현황)

| # | 검토 시점 액션 | 현황(2026-07-28) |
|---|---|---|
| 1 | §2에 UCA/VALU(TCSVT'25)+CVPR'24판 인용, ForeSea·UrBench와 함께 "이해 벤치마크 vs 구조 벤치마크" 구분 축 배치, 차별성 문장 사용 | 최종 §2는 VideoRAG·CLIP·VBASE·ACORN 압축 구도로 확정. UCA는 RQ3 재현 세트로 본문 진입. 인용 세부는 개정 시 원문 대조 |
| 2 | [P2] UCA 어댑터: 심사 압박 또는 여력 발생 시 실행(~37GB, 기존 체인 재사용) | 부분 이행 — UCA 129질의 재현 3/4이 제출본 RQ3에 포함. 전체 어댑터(segment-level GT)는 후속 확장 후보 유지 |
| 3 | [선택] finetuned 캡셔너 가중치 공개 확인 후 설명문 채널 민감도 실험 후보 | 미착수. 후속 확장 후보 유지 |
| 4 | `survey/paper/` PDF 보존, 관련연구 검토 문서는 200번대로 증번 | 본 통합으로 200·740은 `archive/legacy_premerge_20260728/`로 이관, 이후 관련연구 정본은 본 문서(20_RELATED_WORK.md) |
| 5 | 관련연구 comparison matrix·regime table·contribution 3분할·GraphRAG boundary·MEVA/MIRIS 표현 축소(740 §6 우선순위 1-6) | 구도·boundary·contribution 3분할은 최종 제출본에 대응 이행. 매트릭스/regime table 원안은 §2.5에 보존, MEVA는 클립 정의 계보[20]로만 사용 |

### 2.8 개정 시 주의(관련 연구 파트 관련)

- 러닝 헤드 p.7 이후 구제목 잔존 → 재제출/개정 시 수정 필요(관련 연구 파트와 무관하나 동일 개정 사이클에서 처리).
- 클립 조작적 정의는 "데이터셋 배포 mp4 1파일=1클립"이며 MEVA[20] 계보로 방어한다. TTA 사전 미등재·AI Hub 공식 페이지는 '영상(mp4)' 표기임에 유의 — 관련 연구 서술에서 UCA의 "video" 단위와 우리 "클립" 단위를 혼용하지 말 것.

---

## 3. 출처별 고유 내용 색인

### 3.1 `200_RELATED_uca_valu_review_20260710.md` (2026-07-10)
아카이브: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/200_RELATED_uca_valu_review_20260710.md`

이 파일에만 있던 핵심 내용:
- UCA/VALU 논문 서지 정보(TCSVT 35(1) 2025, DOI 10.1109/TCSVT.2024.3462433, CVPR'24 확장판)와 15쪽 전문 정독 사실, 원문 PDF 경로(`survey/paper/...`).
- UCA 데이터셋 상세 수치: 1,854 비디오/23,542 문장 주석/평균 20.15단어/0.1초 타이밍/주석 110.7h/13클래스/스플릿 1,165/379/310.
- 5개 태스크 벤치마크의 베이스라인 목록 전체(TSGV·VC·DVC·MAD·MLLM VC)와 Surveillance SwinBERT AUC 83.1→85.3%, VideoChat2 LoRA 설정(rank16/α32/8frames).
- 태스크별 비교 불가 사유 대응표(TSGV/VC·DVC/MAD/MLLM VC) 및 "성립하는 사용 3가지".
- UCA 획득·라이선스 실사(주석 GitHub 공개, UCF 직링크 ~37GB 등록 불필요, Apache 2.0 vs 학술 전용 불일치)와 2.5-source 변환 설계 스케치(클래스 조건-관련성 강결합 경고, Cramér's V 감사, 2–3 GPU-h 비용 추정).
- 재현성 4항목 판정표(주석/비디오 양호, 태스크 파이프라인·MLLM 중간, 우리 용도 충분).
- UCA/VALU 대비 6축 차별성 표와 영문 차별성 문장 초안, "최초 멀티모달 감시 데이터셋" 주장과의 중복 리스크 판정(낮음·상보적).
- 액션 아이템 4건(§2 인용 배치, P2 어댑터, 캡셔너 ablation, 200번대 증번 규칙).

### 3.2 `740_RELATED_reinforcement_design_review_20260714.md` (2026-07-14)
아카이브: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/740_RELATED_reinforcement_design_review_20260714.md`

이 파일에만 있던 핵심 내용:
- "동일 주제 상위 학회/저널 논문 미확인" 총괄 판정(2026-07-14 웹 확인 기준)과 세 축 교차점 위치 설정문 4문장.
- 비디오 DB/시스템 6편(NoScope/Focus/BlazeIt/MIRIS/OTIF/EQUI-VOCAL) venue·핵심·차이 표.
- filtered vector search 4항목(Filtered-DiskANN/VBASE/ACORN/pgvector iterative scan) 표 — 최종 §2 대표인 VBASE·ACORN의 검토 원천.
- 감시·도시 VLM 4편(UCA/VALU/HAWK/UrBench/ForeSea) 표와 ForeSea "top venue 아님" 상태 판정.
- GraphRAG/LightRAG/RAG-Anything 대비표와 KG boundary 처리 권장 영문 문안.
- 확실한 결론 7개 목록(비순환 필요/hard prefilter/soft 과장 금지/real≠random mask/저장 단위 데이터셋 의존/부분 색인 정책/답변 전파 비직결).
- P0 comparison matrix(6×4), P0 contribution 3문장(validity/design-space/operational), P1 regime table(7행), P1 encoder confounding 보강안(CLIP-text caption), P2 네이티브 QA 판정.
- 좋은 표현 4문안·피해야 할 표현 6항목(금지 목록), 최종 권고 우선순위 6항목.
- 검토 시점 프레이밍 이력: 522/MEVA/MIRIS 트랙, pgvector 백엔드, hot/cold 정책, tri-source 명명 — 최종 제출본과의 차이는 본문 [정정] 주석 참조.
