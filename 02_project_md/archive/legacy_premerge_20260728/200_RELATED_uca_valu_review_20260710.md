# 200_RELATED — UCA/VALU 논문 검토 (비교군·재현성·차별성 판정)

검토일: 2026-07-10 | 검토 대상: Yuan et al., **"Surveillance Video-and-Language Understanding: From Small to Large Multimodal Models"**, IEEE TCSVT 35(1), 2025. DOI 10.1109/TCSVT.2024.3462433. (CVPR 2024 "Towards Surveillance Video-and-Language Understanding" [22]의 저널 확장판)
원문: `survey/paper/Surveillance Video-and-Language Understanding_ From Small to Large Multimodal Models.pdf` (15쪽 전문 정독)

## 0. 한 줄 판정

**직접 비교군(동일 지표 head-to-head)으로는 부적합** — 그들은 *모델*을 평가하는 이해(understanding) 벤치마크, 우리는 *저장·색인·검색 구조*를 평가하는 데이터관리 워크로드로 평가 단위가 다르다. 그러나 **(a) 관련연구 필수 인용**, **(b) UCA 데이터셋의 외적타당성 확장 코퍼스 채택(후순위 P2)**, **(c) 우리 차별성을 정의해 주는 대조점**으로서 가치가 크다. 학생의 수집은 적절했다.

## 1. 논문 요지 (사실 정리)

- **UCA 데이터셋**: UCF-Crime(실세계 감시영상 1,900개, 128h) 중 저품질 46개 제외한 **1,854 비디오**에 **23,542개 문장 주석**(평균 20.15단어, 0.1초 단위 이벤트 타이밍, 주석 110.7h) 수작업 부여. 13개 이상행동 클래스+정상. train/val/test = 1,165/379/310.
- **5개 태스크 벤치마크**: ① TSGV(문장→비디오 내 구간 접지; CTRL/SCDM/A2C/2D-TAN/LGI/MMN/MomentDiff, C3D 특징) ② VC(캡셔닝; S2VT/RecNet/MARN/SGN/SwinBERT/CoCap) ③ DVC(TDA-CG/PDVC/UEDVC) ④ MAD(이상탐지; TEVAD + 자체 개선판: UCA-finetuned "Surveillance SwinBERT" 캡션 분기 추가로 AUC 83.1→85.3%) ⑤ MLLM VC(StableLM/MOSS/MiniGPT-4/VideoChat/VideoChat2 + **VideoChat2 LoRA 파인튜닝**(rank16/α32/8frames)으로 대폭 향상).
- **핵심 발견**: 일반 비디오에서 잘 되는 SOTA가 감시영상에서 일제히 저조(TSGV R@1 IoU0.3 대부분 <10%) — 장시간·저해상도·고정시점·중복성 때문. 도메인 캡셔너가 이상탐지를 돕는다.

## 2. 질문① 비교군으로 적합한가 → 직접 비교는 NO, 적응 경로는 있음

| 그들의 태스크 | 우리 실험과의 관계 |
|---|---|
| TSGV (비디오 **내** 구간 접지) | 우리의 **코퍼스 수준 clip/segment 검색**(B/M-계열)과 태스크 정의가 다름 — 질의당 후보가 "한 비디오의 시간축" vs "수만 클립 코퍼스". 직접 비교 불가 |
| VC/DVC (캡션 생성) | 우리 파이프라인에선 **문서 계층 구축 도구**에 해당(우리의 Qwen2.5-VL 캡셔너 역할). 지표 비교 대상 아님 |
| MAD (이상탐지 AUC) | 우리 워크로드에 없는 태스크 |
| MLLM VC 벤치마크 | 우리의 answer-layer(고정 생성모델, DB evidence만 변경)와 목적이 반대 — 그들은 모델을 바꿔 비교, 우리는 모델을 고정 |

그들 실험엔 **벡터 색인·메타데이터 필터·저장/지연/비용 축이 전혀 없다**(모델 FLOPs/추론시간만 보고). 따라서 "비교군 테이블에 나란히 놓는" 사용은 성립하지 않는다.

**성립하는 사용 3가지:**
1. **관련연구 인용**(즉시): §2에 ForeSea·UrBench와 함께 배치. 그들의 "일반 SOTA가 감시영상에서 붕괴" 발견은 *모델 개선만으로는 부족하고 DB/evidence 계층이 필요하다*는 우리 동기를 외부 근거로 보강한다.
2. **우리 발견의 교차 확인**: 그들의 MAD 개선(도메인 캡셔너가 이상 프레임의 캡션 품질을 올려 AUC 상승)은 우리의 **"VLM 캡션의 문서 맹점(주차 미서술)"** 발견과 같은 축 — "캡션 품질이 다운스트림을 좌우한다"를 이해 태스크 쪽에서 재확인해주는 인용처.
3. **문서-채널 강건성 ablation 재료**(선택): 공개 시 그들의 finetuned VideoChat2/Surveillance-SwinBERT를 우리 캡셔너 대체로 써 "문서 채널 인코더 민감도"를 측정 가능(가중치 공개 여부 미확인 — 착수 전 확인 필요).

## 3. 질문② 데이터셋 채택 가능성 → YES (외적타당성 확장, 우리 A6 패턴 그대로 적용 가능)

**획득 가능성 (확인 완료):** 주석 txt/json 공개(GitHub 페이지), 원본 비디오는 UCF CRCV 직링크 zip(등록 불필요, ~37GB). *라이선스 주의: 논문은 Apache 2.0, 프로젝트 페이지는 "학술 연구 전용" — 원고에는 후자 기준으로 명기.*

**우리 워크로드로의 변환 설계(스케치)** — 핵심: 우리의 tri-source 패턴에서 센서 채널만 빠진 **2.5-source 구성**이 자연스럽게 성립:
- 문서 = **우리 파이프라인의 VLM 캡션**(프레임 픽셀만) — 채널 독립
- relevance = **UCA 사람 문장주석 + 0.1초 타이밍**(주석자 채널) — 채널 독립, segment-level GT 가능
- predicate = 클래스(13)·duration·이벤트 길이 bin — **단, 클래스 predicate는 relevance와 강결합**(우리가 탈출한 순환의 재발 위험) → A6 감사·결합도 곡선(Cramér's V) 필수 적용, 저결합 predicate(duration bin, 이벤트 위치 등)만 헤드라인
- 규모: 이벤트 평균 16.9초 → event-centered 프레임 추출(AI Hub CCTV와 동일 패턴), 캡션 3–5K segment ≈ 2–3 GPU-h (522와 동급 비용)

**무엇을 사주는가**: 영어·국제·심사자가 아는 벤치마크(UCF-Crime) 기반의 **외적타당성 트랙**; 장시간·저해상도·중복성이라는 새로운 스트레스 조건; segment-level 검색 GT.
**무엇을 못 사주는가**: **센서/시공간 predicate 없음** → 우리의 센서 헤드라인(522)을 대체·재현 불가. VQA도 없어 answer-layer는 캡션 기반 MCQ를 새로 구성해야 함.

**우선순위 판정: P2 (인용은 지금, 채택은 조건부).** 000_MASTER §6-27 데이터셋 확정("신규 확보 불필요") 및 "국제 데이터셋은 related work/후속 확장" 규칙(구 31)과 정합하게 — Pillar B/E 완결이 먼저고, UCA 채택은 (a) 심사에서 외적타당성 지적이 실제로 나오거나 (b) 여력이 생겼을 때 실행한다. 실행 시 신규 어댑터 1개 + 기존 체인(캡션→A6→B0-B5) 재사용으로 충분.

## 4. 질문③ 재현성 → 데이터는 양호, 그들 모델 zoo는 노동집약(단, 우리에겐 불필요)

| 항목 | 판정 | 근거 |
|---|---|---|
| 주석 데이터 | ✅ 양호 | txt+json 공개, 스플릿 문서화, 주석 가이드라인·검수 절차 상세(10명+검수 3명, 2개월) |
| 원본 비디오 | ✅ 양호 | UCF-Crime 직링크(등록 불필요) |
| 태스크 파이프라인 | ⚠️ 중간 | 베이스라인 7+6+3+α개가 2015–2023 개별 레거시 코드베이스; C3D(Sports1M)/I3D 특징 추출은 외부 저장소 의존(각주의 RTFM 링크). 구현 세팅 문단은 상세하나 전체 재실행은 수 주 규모 노동 |
| MLLM 실험 | ⚠️ 중간 | Ask-Anything(OpenGVLab) 기반, LoRA 설정 공개; **finetuned 가중치 공개 여부 불명** |
| **우리 용도 기준** | ✅ **충분** | 우리는 그들 모델 zoo를 재현할 필요가 없고 **데이터(주석+비디오)만** 우리 canonical 체인에 넣으면 됨 — 그 경로는 전부 우리 통제 하에 있음 |

## 5. 질문④ 핵심 차이점 → 우리 차별성 명시문

| 축 | UCA/VALU (TCSVT'25) | 본 연구 |
|---|---|---|
| **평가 단위** | 어떤 **모델**이 감시영상을 이해하는가 (모델 벤치마크) | 어떤 **저장·색인·검색 구조**가 VLM-QA를 지원하는가 (**모델은 고정**, 구조만 변경하는 통제 실험) |
| **질의 모델** | 문장 → 비디오 내 구간(TSGV) / 캡션 생성 | **자연어 + 메타데이터 predicate** → 코퍼스 수준 필터드 검색 (prefilter/postfilter/single-stage 질의계획) |
| **모달리티** | 비디오+언어 (2채널) | 비디오+언어+**센서/시공간 구조화 레코드** (3채널, **소스 수준 독립**: 다른 카메라·다른 파일·다른 생산자) |
| **평가 타당성 장치** | 사람 주석 GT (순환성 이슈 자체가 없는 태스크 구성) | **비순환 감사(A6)·이중 qrels(strict/semantic)·결합도 연속곡선** — 워크로드 구성 자체의 타당성을 기계 검증 |
| **시스템 축** | 모델 FLOPs·추론시간 | **색인 recall–latency–size 3축, filtered-ANN 질의계획, pgvector 백엔드, 색인근사→답변 결합** |
| **결론의 종류** | "감시영상은 어렵다, 도메인 파인튜닝이 돕는다" | "prefilter 가치는 제약의 성격(hard/soft)과 predicate-relevance 결합도가 결정한다" 류의 **구조 선택 가이드라인** |

**원고에 쓸 차별성 문장(초안):** *"UCA/VALU benchmarks what models understand about surveillance video; we benchmark what data-management structures deliver to a fixed VLM — retrieval plans, index structures, and storage back-ends under joint natural-language + sensor/spatiotemporal predicates, with workload validity itself machine-audited for non-circularity."*

**중복 리스크: 낮음(상보적).** 그들의 "최초 멀티모달 감시 데이터셋" 주장은 *비디오+언어* 범위 — 우리의 멀티모달 주장은 *구조화 센서 레코드를 1급 DB facet으로 결합*하는 것이므로 표현만 구분하면 충돌 없음(§2에서 명시 구분할 것).

## 6. 액션 아이템

1. **[원고 재작성 시, F5 계열] §2 인용 추가**: 본 논문(TCSVT'25) + CVPR'24 판 [22] — ForeSea·UrBench와 함께 "이해 벤치마크 vs 구조 벤치마크" 구분 축으로 배치. 차별성 문장(§5) 사용.
2. **[P2] UCA 어댑터**: 심사 외적타당성 압박 또는 여력 발생 시 §3 스케치대로 실행(신규 획득 ~37GB, 기존 체인 재사용).
3. **[선택] 문서 채널 ablation**: 그들 finetuned 캡셔너 가중치 공개 여부 확인 후 캡셔너 민감도 실험 후보로.
4. `survey/paper/` PDF는 보존; 본 검토가 200번대(Related Work) 첫 문서 — 이후 관련연구 검토는 210, 220…으로 증번.
