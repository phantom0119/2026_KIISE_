# 690 — 해외 멀티모달 비교 데이터셋: 독립 검증 + 확장 조사 (2026-07-13)

상태: **완료.** `680` 감사 이후 추가 지시("이 외에 더 조사 — 상위학회 수준이면서 본 연구에서 '멀티모달'로 확실하게 사용 가능한지 검토")에 대한 응답.
방법: 43-에이전트 워크플로(wf_86fb10c0) — 6개 웹서치 lens(이전 CV-편중 sweep이 덜 본 각도 포함) → 적대적 검증 **36 finalist** ×(학회·확보·멀티모달 3게이트, 반증 우선). 결과: **채택 1 / 백업 8 / 탈락 27.** 이전 680 주장은 신선 근거로 재검증하고, 놓친 후보(DB/IR/멀티미디어 학회·네이티브 영상+텍스트 벤치마크)를 새로 발굴.

"멀티모달 사용 가능"의 판정 기준(본 연구 고유): 비순환 tri-source — **필터=센서/시공간 기록 ⟂ 정답=사람주석 ⟂ 문서=픽셀만 본 VLM캡션**, 고정 CCTV 도메인(ego/대시캠 아님), 이중 strict/semantic qrels, 기계 감사. 확보 기준(하드): **지금 한국에서 다운로드 가능** + **-ND 아님**(파생 캡션 재배포 가능해야 함).

---

## 한 줄 결론

**MEVA(WACV 2021)가 여전히 정답이다 — 680의 결론을 독립 재검증이 확증했고, 여기에 세 가지를 더했다:** ① MEVA를 재현 가능한 수준으로 하드-검증(정확 라이선스 파일·무서명 S3·한국 다운로드 확인), ② **새 도메인일치 백업 LUMPI(IV 2022, 고정 다중카메라+LiDAR 교차로, CC-BY-NC-3.0, 직접 다운로드)** — 680에 없던 후보, ③ "네이티브 멀티모달(텍스트 생성 불필요)" 요구 시의 일반화 arm 메뉴(1순위 **QVHighlights**, 최정결 라이선스 **MS-COCO**). **어떤 후보도 제2의 깨끗한 tri-source 헤드라인은 아니다**(fit type 1은 522 단독). 해외 건은 **외적타당성 arm(fit 2)** 또는 **일반화 arm(fit 3)** 역할.

---

## 상위 후보 비교표 (채택 + 백업 8)

| # | 데이터셋 | 학회(검증) | 라이선스 / 확보 | 네이티브 모달리티 → 생성필요 | fit | 점수 | 판정 |
|---|---|---|---|---|---|---:|---|
| 1 | **MEVA (KF1/ActEV)** | **WACV 2021** ✓ | **CC-BY-4.0**(라이선스 원문 확인), 무서명 S3(`s3://mevadata-public-01`), 한국 OK | 고정 38-cam RGB+열IR 영상 · GPS · cam/time 메타 · DIVA 활동주석(bbox/37클래스) → **텍스트=VLM생성** | 2 외적타당성 | **83** | **채택** |
| 2 | **LUMPI** | IV 2022 ✓ | CC-BY-**NC**-3.0(-ND 아님), LUH 저장소 직접 다운, 한국 OK | 3고정카메라 영상 · **5 LiDAR 포인트클라우드** · 3D bbox 트랙 · 날씨/광량(세션) → 텍스트·활동라벨 생성 | 2 외적타당성 | 64 | 백업(신규·강력) |
| 3 | MEVID | WACV 2023 ✓ | CC-BY-4.0(MEVA 픽셀), 무서명 S3 | 고정 33-cam 영상 · **인물ID 트랙릿** · outfit/cam/frame → 텍스트 생성 | 2(보강용) | 61 | 백업(MEVA 위에 얹는 relevance 층) |
| 4 | **QVHighlights** | **NeurIPS 2021** ✓(top) | CC-BY-NC-SA(-ND 아님), UNC 직접 tar + 8GB CLIP feat, 한국 OK | **영상 · 사람작성 자연어 질의 · moment span · saliency** → 문서=VLM생성 | 3 일반화 | 60 | 백업(네이티브 멀티모달 1순위) |
| 5 | MS-COCO(Captions) | ECCV 2014 ✓(top) | **CC-BY-4.0**(주석), 게이트/지오 없음 | **이미지 · 5 사람캡션 · 80-객체 bbox/mask** → (교차모달 검색엔 생성 불필요) | 3 일반화 | 57 | 백업(최정결·즉시가용, 영상 아님) |
| 6 | VIRAT(Ground2.0+DIVA) | CVPR 2011 ✓(top) | **재배포제한 사용협약**(-ND급) + 종료시 파생물 파기 | 고정 지상감시 영상 · 46 활동라벨 · 트랙 · 구조적 시공간 → 텍스트 생성 | 2 | 55 | 백업(MEVA에 지배됨·재배포 플래그) |
| 7 | VATEX | ICCV 2019 ✓(top) | CC-BY-4.0(캡션·I3D feat), **원영상=YouTube 링크로트** | 사람캡션(EN/ZH) · I3D feat · (원영상 재호스팅X) → 문서 생성(원영상 필요) | 3 | 55 | 백업(feature-only는 순환·비준수) |
| 8 | ActivityNet-Cap / DiDeMo | ICCV 2017 ✓(top) | 주석·feat 개방, 원영상 YouTube(링크로트) | 영상/feat · 자연어 시간주석 → 문서 생성 | 3 | 34 | 백업(웹영상·relevance≈document 순환) |
| 9 | Conceptual Captions(CC3M/12M) | ACL'18/CVPR'21 ✓(top) | 개방(NC/ND 없음), HF 픽셀미러 | 이미지 · 웹 alt-text → 문서·predicate·relevance 전부 생성 | 3 | 32 | 백업(웹이미지·구조적 순환, 색인 스케일 스트레스용만) |

정직 주: 점수는 "해외 비교 데이터셋 1개"로서의 적합도. 4–9는 도메인 불일치 또는 tri-source 붕괴(필터 producer 없음/relevance≈document)로 **일반화 arm(fit 3)** 한정 — 헤드라인 발견의 외적타당성은 못 싣고 색인/검색 구조의 일반화만 보일 수 있음.

---

## 1위 심층 — MEVA (외적타당성 arm)

**확보(재현 가능):** `aws s3 ls --no-sign-request s3://mevadata-public-01/` — AWS Open Data, 계정·등록·지오게이트 없음, 한국 다운로드 확인. 라이선스 = **CC-BY-4.0**(원문 `mevadata.org/resources/MEVA-data-license.txt`, NC·ND 없음 → **파생 VLM캡션 재배포 합법**). 공개 KF1 ~330h/470GB 영상 + DIVA/KPF 활동주석은 Kitware `meva-data-repo` GitHub(별도 호스트).

**tri-source 매핑(522와 동형):**
- **필터 predicate** = GPS 로그 + camera-id + timestamp(+시간대/날씨 파생) — 물리센서/메타 producer(독립).
- **정답 relevance** = DIVA/ActEV 사람 활동주석(bbox/트랙 + 37 활동클래스) — 별도 사람주석 producer.
- **문서 document** = 픽셀만 본 VLM 캡션(메타 누출 차단).
- **순환 리스크(주의):** 활동클래스는 사람주석 계보 → **relevance로만 쓰고 절대 predicate로 재주입 금지**. predicate는 GPS/cam/time(물리 독립)에서만 도출. 이 규율 하에서 세 채널 = 센서 vs 사람주석 vs VLM 세 producer로 비순환. UAV(이동카메라) 클립은 고정CCTV 프레이밍 위반 → 제외.

**통합 레시피(중간~상당, 잘 정의됨):** ① 무서명 S3로 KF1 subset(작업셋 = 주석 붙은 ~22h 공개창 + GPS) → ② Kitware KPF/YAML 파싱(bbox+활동 relevance) → ③ 표본 프레임 VLM 캡션 pass(문서 채널) → ④ CLIP 임베딩 + Flat/IVF/HNSW/IVF-PQ 색인 벤치 → ⑤ GPS+cam+time predicate 테이블 → ⑥ strict/semantic 이중 qrels + A6 비순환 감사(predicate-source ≠ relevance-source ≠ document-source). 주비용 = 캡션 pass + KPF 파싱. 라이선스 블로커 없음.

**한계(정직):** 텍스트 문서는 생성(=fit 2의 정의이지 결함 아님); 주석 공개창이 ~22h로 모듬; 470GB 다운로드 물류. **제2 헤드라인 아님** — predicate/relevance producer 분리는 분석자가 설계한 것(두 개의 네이티브 독립 워크로드가 아님).

---

## 새로 발굴한 것 (680에 없던 것)

- **LUMPI (IV 2022) — 가장 값진 신규 후보.** 하노버 교차로의 **고정 3카메라 + 5 LiDAR** 다관점 인프라(ego/대시캠 아님). CC-BY-**NC**-3.0(-**ND 아님** → 파생 캡션 재배포 가능), `data.uni-hannover.de/vault/ikg/busch/LUMPI/`에서 login 없이 직접 다운(labels.zip 1.04G·test_data.zip 838M+). **LiDAR라는 진짜 제2 센서 producer**를 가져 MEVA보다 모달리티 축이 하나 많음. 약점: 학회 tier가 MEVA보다 한 단계 아래(IV<CVPR/ICCV), 네이티브 활동택소노미 없음(predicate는 궤적파생), 날씨/광량 메타가 세션단위로 coarse. → **MEVA의 대안/제2 현장(second-site) 백업**으로 최적, 특히 "센서·저장·색인" 축을 LiDAR로 강화하고 싶을 때.
- **MEVID (WACV 2023).** MEVA와 동일 픽셀 + 인물ID 트랙릿 주석. 독립 제2 코퍼스는 아니고, **MEVA arm 위에 identity relevance 층을 얹어** tri-source를 강화하는 보강재. 단 ID gold가 반자동(ReID 모델→사람보정)이라 의사라벨 성격 + appearance캡션↔identity 결합(순환 주의).
- **일반화 arm 메뉴(네이티브 멀티모달, 텍스트 생성 불필요):** **QVHighlights(NeurIPS 2021)** = 네이티브 영상+자연어질의+saliency, 직접 다운, -ND 아님 → top-venue 네이티브 멀티모달 검색 벤치 1순위. **MS-COCO(ECCV 2014)** = 라이선스 가장 정결(CC-BY-4.0)·즉시가용, 단 이미지-텍스트(영상·감시 아님). 둘 다 **tri-source는 붕괴**(센서 predicate 없음/질의·정답 1-pass) → 색인·검색 구조 일반화만 가능, 헤드라인 비순환 발견은 못 실음.

---

## ⚑ PI가 골라야 할 단 하나의 결정 — 두 갈래

"멀티모달로 확실하게"의 해석이 갈림:

- **갈래 A — 도메인일치 감시 arm (fit 2, 권장).** MEVA(주) [+ LUMPI(대안/제2현장)]. 영상+센서+주석은 **네이티브**, 텍스트(문서)만 522처럼 VLM 생성. → **헤드라인 발견의 외적타당성/국제 비교가능성**을 그대로 확보. tri-source 프로토콜 전부 재현 가능. "텍스트가 생성"이라는 점만 감수.
- **갈래 B — 네이티브 멀티모달·타도메인 일반화 arm (fit 3).** QVHighlights 또는 MS-COCO. **텍스트가 네이티브**(생성 불필요)라 "확실히 멀티모달"이 가장 문자 그대로 성립하고 학회 tier도 top. 그러나 **감시 도메인 아님 + tri-source 붕괴** → 색인/검색 구조의 일반화만 보이고 비순환 워크로드 헤드라인은 못 실음.

**권고:** 본 연구의 기여축(비순환 tri-source 감시 워크로드)을 지키려면 **갈래 A = MEVA 주 + LUMPI 백업**. "네이티브 멀티모달"을 별도로 반드시 보이고 싶으면 **QVHighlights를 fit-3 일반화 arm으로 추가**(헤드라인엔 못 쓴다고 명시). 둘을 겸하는 것도 가능(MEVA=외적타당성, QVHighlights=색인 일반화).

---

## 왜 탈락했나 (27 — 공간이 커버됐음을 보이기 위한 요약)

**라이선스 -ND/재배포 금지(파생 캡션 재배포 불가):** TUMTraf VideoQA(ICML 2025, CC-BY-NC-ND/SA — *논문상 최적합이나 라이선스가 킬러*), TUMTraf Intersection/A9/V2X(ITSC'23 등, CC-BY-NC-ND), WTS(ECCV 2024, "원형/변형/결합 배포 불가"), Rope3D(CVPR 2022, 기관협약), CityFlow/V2(CVPR 2019, NVIDIA 비재배포), MSR-VTT(CVPR 2016, 무허가 웹스크랩), WILDTRACK(CVPR 2018, 연구전용), Ko-PER(ITSC 2014, 라이선스 부재=all-rights-reserved).
**도메인 불일치(ego/대시캠 또는 웹/일반):** DAIR-V2X(CVPR'22, ego 혼합), NuPlanQA(ICCV'25, 서라운드 대시캠), DoTA/DADA-2000(대시캠), DRAMA/DRAMA-X(WACV'23, 대시캠), CityLLaVA·Bench2Drive-QA(ego/폐루프), VidOR/VidVRD(웹영상), Re-LAION-5B(웹이미지), Flickr30k(소비자사진).
**확보 하드-실패(지금 다운 불가):** IPS300+(ICRA'22, 중국전용 호스트·비밀번호벽), SUTD-TrafficQA(CVPR'21, Zenodo 승인폼), RoadSocial(CVPR'25, X/Twitter 스크랩·링크로트), PANDA(CVPR'20, 호스트 사망), WebVid-2M/10M(ICCV'21, Shutterstock C&D로 철거), TVR(ECCV'20, TV 저작권), INTERACTION/inD/SIND(픽셀·영상 미공개→문서채널 불가), ForeSea/ForeSeaQA(ECCV 2026, 미공개), CrashSight-VQA(CVPR'26 WS, 데이터 미공개).
**학회 tier 미달(arXiv-only):** UDVideoQA(arXiv 2602.21137), InterAct-VideoQA(arXiv 2507.14743).

---

## 680 대비 바로잡은 / 새로 확증한 점

- **MEVA:** 680은 "open CC-BY-4.0"만 명시 → 본 검증이 **라이선스 원문 파일 + 무서명 S3 접근법 + 한국 다운로드**까지 하드-확인(재현 가능). WACV 2021 저자·DOI·arXiv 모두 확증.
- **TUMTraf-VideoQA:** 680은 "ICML 2025·ND·weak"로 두었는데, 본 검증이 **venue·domain·소스분리에서 실은 후보군 최상위**임을 재확인하되 **라이선스(-ND/-NC)가 유일 킬러**임을 분명히 함(= 재배포 안 하는 내부실험만이면 재고 여지 있으나, 배포형 벤치 산출물엔 부적합).
- **신규 후보 3종 추가:** LUMPI(도메인일치 백업·LiDAR·정결 다운로드), MEVID(MEVA 보강층), QVHighlights(네이티브 멀티모달 일반화 1순위) — 680의 CV-편중 sweep이 놓친 IV/DB-IR/검색벤치 계열.
- **결론 방향 불변 확증:** "제2의 깨끗한 tri-source 헤드라인은 해외에 없다(522 단독), 해외는 외적타당성/일반화 arm" — 36-finalist 전수에서 재확인.
