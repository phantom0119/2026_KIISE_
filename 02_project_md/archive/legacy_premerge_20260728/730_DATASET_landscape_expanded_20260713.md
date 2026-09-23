# 730 — 도시감시·교통 CCTV 멀티모달 데이터셋 확장 landscape (2026-07-13)

PI 추가 지시("더 없는지")에 대한 광역 재조사. 80-에이전트 workflow(wf_8eaa88fc), 6개 각도(교통이상·감시QA·멀티카메라·지역교통·스마트시티/오디오/열화상·DB학회) × 신규발굴→적대검증. 690의 36-후보 known-list를 자동 dedup.

## 한 줄 답
**신규 적합 32 + 부분적합 38 발굴. "리네임된 기존것"은 1개(FineVAU)뿐.** 첫 sweep이 tri-source·고정CCTV 바에 맞춰져 **이상+언어/QA, 오디오, DB학회 비디오-질의, 지역·멀티센서** 계열을 대거 누락했음. 우리 522+MEVA가 없는 축(오디오·열화상·LiDAR·네이티브 QA·DB-질의 벤치)을 이들이 채움.

## 신규 발굴 — 카테고리별 (venue / 모달리티 / 확보)

### A. 감시 VLM-QA·이상+언어 (고정CCTV + 네이티브 텍스트/QA) — 가장 직접 관련·최신 top-venue
| 데이터셋 | 학회 | 모달리티 | 확보 | 주의 |
|---|---|---|---|---|
| **HAWK** | NeurIPS 2024 | 이상영상(대부분 고정)+언어서술+QA 8k+motion | HF 공개(무게이트) | 이상-일반, 7개 VAD소스 집계(+DoTA ego) |
| **Vad-R1/Vad-Reasoning** | NeurIPS 2025 | 고정감시+CoT추론+QA+시간라벨 | HF/GitHub 공개 | UCF-Crime/XD-Violence/ShanghaiTech 집계 |
| **SurveillanceVQA-589K** | arXiv 2025 | 고정감시+589K QA+사람캡션 | **MIT**, HF 2.3GB | MSAD/**MEVA/UCA** 집계(우리것 중복) |

### B. 오디오-비주얼 (우리 corpus에 전무한 AUDIO 축 추가)
| 데이터셋 | 학회 | 모달리티 | 확보 |
|---|---|---|---|
| **Urbansas** | ICASSP 2022 | 고정카메라+스테레오오디오+차량bbox+음향이벤트 | **CC-BY-4.0**, Zenodo 9.7GB |
| **MAVAD** | IEEE ICIP 2024 | 고정노변+동기오디오+11이상클래스(Malta 3cam) | GitLab 공개(라이선스 미명시) |
| **StreetAware** | Sensors 2023 | 3 Brooklyn 교차로 video+audio+LiDAR | NYU 공개 |

### C. 노변 멀티센서 (열화상/LiDAR/레이더 — 센서융합 축)
| 데이터셋 | 학회 | 모달리티 | 확보 |
|---|---|---|---|
| **R-LiViT** | ICCV 2025 | 노변 LiDAR+RGB+**열IR**, 독일 3교차로, 주야 | **CC0(퍼블릭도메인)** 공개 ⭐ |
| **V2X-Radar**(I split) | NeurIPS 2025 D&B | 노변 카메라+LiDAR+**4D레이더**+날씨/시간 | openmpd.com 등록게이트 |
| **AAU RainSnow** | T-ITS 2019 | 노변 RGB+**열IR**, 덴마크 7교차로, 우/설/야 | Kaggle 공개 |
| **BAAI-VANJEE** | arXiv 2021 | 노변 LiDAR+2카메라, 중국 교차로/고속 | BAAI포털 등록 |
| **LLVIP** | ICCVW 2021 | 거리 RGB+**열IR** 페어, 보행자 | GitHub(비상업) |

### D. DB/시스템 학회 고정카메라 비디오-질의 벤치 — **우리 DB 기여와 직결(related-work)**
| 데이터셋 | 학회 | 내용 | 확보 |
|---|---|---|---|
| **MIRIS** | **SIGMOD 2020** | 고정 교차로(Warsaw/Tokyo)+트랙궤적+9 시공간 트랙질의 스펙 | **MIT** 공개 ⭐ |
| **OTIF** | **SIGMOD 2022** | 고정 교통/도시 카메라+다객체트랙+메타 | 공개 zip |
| **EQUI-VOCAL** | **PVLDB 2023** | 고정 교차로(Warsaw) 합성 이벤트질의+scene graph+질의언어 | MIT 공개 |
| Ekya/Bellevue | NSDI 2022 | 5 폴마운트 어안 교차로캠+자동라벨+드리프트 | 공개(GDrive) |
| NoScope/BlazeIt | VLDB 2017 | 고정 웹캠/CCTV 피드(교차로/광장) | 공개 |

### E. 멀티카메라 도시·차량ReID + 구조화 메타 (벡터DB 속성검색)
| 데이터셋 | 학회 | 특징 | 확보 |
|---|---|---|---|
| **VeRi-776** | ICME 2016 | 고정 20교차로 차량ReID+**번호판텍스트**+속성+시간+카메라geo | 이메일게이트 |
| VERI-Wild | CVPR 2019 | 174 고정캠 차량ReID+시간/날씨 | 이메일게이트 |
| **MTMMC** | CVPR 2024 | 고정 16캠 RGB+**열IR** 인물추적+시간/날씨/계절 | 협약게이트(비교통) |
| WebCamT/CityCam | CVPR 2017 | 212 고정 도시캠+차종/수/속도/날씨/시간 | 사이트폐쇄, GitHub미러 |

### F. 고정감시 사고/이상 (이벤트주석, 대개 텍스트 없음)
ACCIDENT(CVPRW'25, 실+CARLA, Kaggle공개) · TADS(J.Supercomp'24, +eye-gaze, 중국geo) · TU-DAT(Sensors'25, +환경메타+궤적, 무라이선스) · UBnormal(CVPR'22, 합성+픽셀마스크, CC-BY-NC-ND) · MSAD(NeurIPS D&B'24, video-only).

### G. 한국 AI-Hub 미보유 신규
**고속도로 CCTV 교통영상(dataSetSn=164, 505h)** +bbox/seg+날씨/시간/도로/차로/밀도메타 · **차종/연식/번호판(플레이트 OCR 텍스트)** — 둘 다 내국인 계정 게이트.

## 우리 연구 편입 값어치 top 3
1. **DB 기여 강화용(최고 ROI, 신규실험 불요): MIRIS/OTIF/EQUI-VOCAL 인용** — SIGMOD/VLDB의 "고정카메라 비디오 위 필터드 질의" 벤치. 우리 P2/P3(partial-index·hot/cold)와 710 강화 기여문장의 **related-work 근거**로 직접 삽입.
2. **모달리티 확장(선택): Urbansas(CC-BY, 오디오) 또는 R-LiViT(CC0, 열IR+LiDAR)** — 522/MEVA에 없는 **오디오/열화상** 축. 라이선스 가장 깨끗(각 CC-BY/CC0).
3. **네이티브 QA 감시셋(선택): HAWK(NeurIPS'24) / SurveillanceVQA-589K(MIT)** — VLM-생성 아닌 **사람 QA층**. 단 MEVA/UCA 소스 중복·이상일반이라 제2헤드라인 아닌 보조.

## 커버리지 판정
- **이 공간은 이제 매우 촘촘히 훑였음**(2 sweep 합계 후보 ~100+, venue·지역·모달리티 교차). 남은 사각은 거의 없고, 신규는 대부분 (a)기존 소스 재주석(HAWK/Vad-R1/SurveillanceVQA) (b)단일모달(대다수 지역 교통셋) (c)ego/드론.
- **우리 corpus가 실제로 못 가진 축 = 오디오·열화상·LiDAR·네이티브QA·DB-질의벤치** → 위 top3가 그 공백을 정확히 메움. **제2의 깨끗한 비순환 tri-source 헤드라인은 여전히 없음**(690 결론 유지); 신규는 모달리티 확장 또는 related-work 보강용.
- 정직: 위 다수가 라이선스 미명시/게이트 → 배포형 파생 산출물엔 CC0/CC-BY/MIT인 **R-LiViT·Urbansas·MIRIS·EQUI-VOCAL·SurveillanceVQA**만 안전.

전체 검증 데이터: workflow wf_8eaa88fc journal (73 검증후보). 690(1차 36) + 730(2차 70)로 landscape 종결.
