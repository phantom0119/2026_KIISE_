# 680 — 데이터셋 기반 전면 재점검 (확보·구축·확장 가능성), 2026-07-13

상태: **완료.** 디스크 직접 실측 + 2 에이전트 병렬 심층(구축 적합성 / 국제 landscape). 세 질문에 답함.

## 요약 판정
- **확보**: 충분. 원천(external) ~1.6 TB + 가공(processed) 8종. 국제 benchmark도 다수 온디스크.
- **구축**: 헤드라인 **522가 비순환 tri-source·A6 6/6 기계감사 통과로 논문 준비 완료**. 나머지는 역할별(외적타당성 2.5채널 / v1 사례 2채널 / 답변계층 / 미사용) tier로 정직 강등. **플래그십 rigor(완전 A6·3소스)는 단일 데이터셋(522)에 의존** — 최대 구조적 caveat.
- **확장**: 가능. 국제 open·상위학회 후보(MEVA/VIRAT/TUMTraf/WTS)로 **외적 타당성·국제 비교가능성** 확보 가능하나, **제2의 깨끗한 tri-source 헤드라인은 거의 불가**(공개 데이터 대부분 caption/QA/label 단일 주석 pass).

## Q1. 확보 상태 (실측)
원천 external ~1.6T: 이상탐지 573G·다각도 483G·시내도로영상 320G·교차로신호(522원천) 198G·UCA 194G·CityFlow-NL 16G·지능형관제 13G·VRU 5.8G.
가공 8종: 522(142G)·sinnaedoro(2.5G)·uca_anchor·vru·multi_angle·intelligent·abnormal·cityflow_nl.

## Q2. 구축 적합성 (Agent A, 디스크 검증)
| 데이터셋 | 논문 역할 | A6/tri-source | 핵심 수치 | 공백 |
|---|---|---|---|---|
| **522 intersection** | **헤드라인**(§5.1·§6·§7·§8.2) | **A6 6/6 PASS**, 3채널(센서 cam10 ⟂ CVAT cam11/22 ⟂ Qwen2.5-VL 픽셀캡션) | q85·docs3000·metadata27000·qrels strict6809/sem24872 | 없음. 원고와 정확 일치 |
| sinnaedoro (색인A) | §7.1·§7.3 filtered-ANN | N/A(색인, 실측 predicate) | emb 132,521×512·q1000 | filtered_ann.csv는 random-mask 구舊산물(실측은 paper_assets/20260710_pillarB) |
| uca_anchor | **외적타당성**(§6, 탐색적) | A6-port PASS, **2.5채널** | docs6432·q135·qrels 7709/41435 | 센서채널 없음(정직 명시) |
| vru_accident | **v1 순환성 사례**(§4)+답변앵커(§8.1) | **A9 축소 3어서션**, 2채널 | docs1000·q85·qrels 3744/9703 | 완전A6 아님(역할상 적절) |
| multi_angle | **다시점 답변**(§8.1 400event) | A6 N/A(답변정확도 실험) | 400event; 4 VLM결과 | 4500클립 검색 canonical 미사용; Qwen manifest 사후재구성(명시) |
| intelligent_cctv | v1붕괴+이식성(§4) | A9 축소, 자연결합 | docs269·q18 | 소형, 붕괴데모용 |
| abnormal_cctv | **v3 미사용** | 無 | clips1968·q424 | 규칙상 보류(이식성만) |
| cityflow_nl | **v3 미사용** | 無, 약한 qrels | clips2339·q6465 | frame 미추출, raw-canonical만 |

색인코퍼스 B(522-visual) = 143,830×512. 둘 다 실측·임베딩·비순환 호환.

**가장 약한 고리**: ① 완전 A6는 522 단독 ② 다시점 manifest 사후재구성 ③ abnormal/cityflow 미사용 ④ sinnaedoro stale csv. 전부 명시됨·치명적 아님.

## Q3. 국제 확장 (Agent B, 온디스크+web)
**핵심**: 깨끗한 tri-source는 522가 사실상 유일(522는 AI-Hub 패키지가 센서CSV cam10 + 독립 CVAT cam11/22 + 픽셀캡션 3소스를 우연히 제공). 추가는 **외적타당성·국제 비교가능성**용.

**랭킹 shortlist (fit×feasibility)**:
1. **MEVA (WACV 2021) — 톱픽.** 고정 다중카메라 CCTV, **open CC-BY-4.0**, activity+camera+time 메타 분리가능. 노력: 주석 144h subset 다운→키프레임→predicate(카메라ID/시간/activity)→relevance(activity 주석)→VLM 캡션 문서→A6. 비한국·상위학회 고정CCTV에서 tri-source 재현 최선.
2. **TUMTraf VideoQA (ICML 2025).** 고정 노변 인프라(A9), 악천후, 국제 비교성. registration. QA=relevance라 분리 약함→"중결합 arm".
3. **VIRAT (CVPR 2011).** 완전 open 고정 지상감시 CCTV, event+bbox. 저마찰·구식/저해상만 단점.
4. **WTS (ECCV 2024/AI City).** 고정 overhead+ego, bbox+3D gaze. Google Form. caption+VQA 공동생산→다시점 arm 강화.
5. **UDVideoQA (arXiv 2026).** 고정 도시교차로 QA 대규모, HF. 분리 최약→외적타당성만.

**비적합(명시·제외)**: RoadSocial(소셜/혼합), VRU/DoTA/DADA/BDD(대시캠 ego), SUTD-TrafficQA(in-the-wild YouTube·QA-only), ShanghaiTech/XD-Violence(이상만/영화). DB학회(SIGMOD/VLDB)는 systems(SeeSaw/ExSample/Lava)지 데이터셋 아님→related work.

**caveats**: 결합도 곡선 재검정력화에 MEVA/TUMTraf가 최적(predicate×relevance 쌍 확대); 522 시간predicate 제한(평일·주간)→MEVA diurnal이 축 확장; VLM캡션 사각(parked)은 새 캡션데이터도 상속(그 자체 DB findings); 라이선스는 open·상위학회(MEVA/VIRAT/TUMTraf/WTS) 우선; 저장 여유 충분(주석 subset만).

## 다음 결정 (PI)
제2 A6 tri-source 외적타당성 arm으로 **MEVA** 추가가 최고 ROI(국제 비교성 + 결합도 재검정력). 각 추가 = 다운+키프레임+VLM 캡션 pass(~18캡션/분 2GPU)+A6 = 다-일. 미결정 시 현행(522 헤드라인 + UCA 외적)로도 논문 완결 가능.

## 부록 — 외부 추천 후보 7종 검증 (2026-07-13, 조사+적대적 반증 14에이전트, wf_8f5cb287-e2f)

다른 에이전트가 추천한 후보들을 우리 비순환 tri-source 프로토콜(소스 분리)로 검증. **결론: 7종 전부 제2의 깨끗한 tri-source 헤드라인 불가. usable_now=전부 false.** 소스 분리는 522가 사실상 유일.

| 후보 | 학회 | 온디스크 | 확보/라이선스 | 소스분리(검증후) | 적합 | 킬러 |
|---|---|---|---|---|---|---|
| **TUMTraf-VideoQA** | ICML 2025 | repo만 | a9 registration·CC-BY-NC-ND(재배포 차단) | **2채널(사실상 순환)** — 단일 semi-auto 파이프라인(predicate=relevance=네이티브캡션 1생산자) | weak(외적타당성만) | 게이트+ND, 센서predicate 없음 |
| **WTS/AICity T2** | ECCV 2024 | repo만(영상·캡션 0) | Google-Form 게이트 | 2.5→2채널(캡션+VQA 공동생산, 센서 없음·gaze는 query-불변) | weak(staged 동반) | 미확보+staged accident |
| **AICity2026 TAR** | AICity 2026 | 없음 | 주석 CC-BY-4.0 open이나 **영상 script게이트(Kaggle/GDrive/YT)** | **단일생산자**(Gemini→MSTED→Gemma 캐스케이드, **센서 0**, relevance=VLM 의사라벨) | **does_not_fit**(반증 UPHELD) | 센서채널 부재, 의사라벨 |
| **DAIR-V2X** | CVPR 2022 | 없음 | **중국 본토 외 다운로드 미해결(geo-gate)**·별도 NC | multisensor(생산자 분리 진짜)나 predicate=기하(GPS/캘리브), relevance=박스 파생(≈document 위험) | moderate→weak | geo-gate + LiDAR 파이프라인 없음 |
| **TUMTraf-V2X** | CVPR 2024 | 없음 | a9 registration·CC-BY-ND | 2~2.5채널(주석독립 센서메타=ego-pose/기하만, scene-semantic 아님; query셋 없음) | weak | ND + 질의·relevance 신설 |
| **CityFlow-NL** | CVPR 2019/AICity | **fully_local(16GB)** | 등록(폼 제거됨) | **2채널 결정론적 순환**(모든 질의 gold=동일 track UUID; task=text-to-vehicle-id) | weak(차량검색 외적) | 순환 구조적·현 canonical은 text-to-text |
| **AD군(nuScenes/Waymo/Argoverse/BDD)** | CVPR/NeurIPS 2019-20 | 없음 | Argoverse2만 open, 나머지 게이트 | 2.5채널(인식박스가 LiDAR+카메라 위에 그려짐=센서와 비독립) | weak | **ego/대시캠(고정CCTV 아님)** 도메인 불일치 |

**핵심 판정.** 추천의 2-arm 프레이밍(VLM-QA: TUMTraf/WTS / 멀티센서: DAIR-V2X/TUMTraf-V2X)은 방향은 맞으나 **양 arm 모두 우리 소스분리 바를 통과 못 함**: VLM-QA arm=단일주석pass(외적타당성 한정)+게이트/ND 재배포차단; 멀티센서 arm=생산자 분리는 진짜지만 predicate가 scene-semantic 아니고(기하), relevance를 박스에서 파생(≈document), 캡션·질의 신설, LiDAR 미사용(파이프라인 없음), **확보 자체 차단**(DAIR-V2X geo-gate/TUMTraf-V2X ND). **추천이 "높음"으로 본 TUMTraf/WTS는 우리 프로토콜엔 weak(외적타당성만).**

**MEVA 재확인.** 추천이 누락한 MEVA(WACV 2021, **open CC-BY-4.0**, 고정 38-cam CCTV, activity/camera/time 메타 독립 vs 생성캡션)가 여전히 fit×feasibility×라이선스에서 최선의 외적타당성 arm — 게이트·geo·ND·재배포 차단이 전무한 유일 후보. 단 MEVA도 제2 헤드라인 아닌 외적타당성(activity→derived relevance).

**권고.** ① 헤드라인 프레이밍 유지(522=유일 비순환 tri-source, 외적 arm 1개 추가) — 추천의 "안전한 프레이밍"은 옳음. ② 단 arm 선택은 **MEVA로 교정**(TUMTraf/WTS는 게이트+ND+외적한정이라 마찰 대비 이득 낮음; UCA 이미 2.5채널 외적 보유). ③ 멀티센서 "센서·저장·색인" arm(DAIR-V2X류)은 확보차단+LiDAR툴 부재+predicate 비의미 → **별도 논문**(추천의 "분리" 본능은 옳으나 블로커가 더 심함). ④ CityFlow-NL은 유일 온디스크지만 결정론적 순환 → 외적 차량검색 이상 불가.
