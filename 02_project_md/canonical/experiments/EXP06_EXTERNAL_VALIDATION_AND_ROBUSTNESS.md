# EXP06 — 외부 타당성, 규모·seed 강건성과 교차감사

- 대응 범위: RQ1–RQ6의 일반화 경계
- 상태: UCA·MEVA·MIRIS·scale/seed 완료
- 최종 판정: PASS_WITH_LIMITATIONS

## 1. 목적

522 한 데이터셋의 관측을 보편 법칙으로 확대하지 않고, 다른 국가·도메인·DB 코퍼스·규모·seed에서 무엇이 재현되고 무엇이 실패하는지 분리한다.

## 2. 데이터 역할

| 데이터 | 규모 | 이식하는 축 | 이식하지 않는 축 |
|---|---:|---|---|
| UCA/UCF-Crime | 6,432 segments, 135 queries | B0–B5, hard/soft, 결합도 방향 | 독립 물리 센서 tri-source |
| MEVA | 985 clips, 193 queries | 검색·저장 표현의 외부 결과 | 522와 동일한 센서 채널 |
| MIRIS | 59,019 DB rows | partial/local, hot/cold 정책 | semantic retrieval qrels |
| Qwen 143,830 | real vectors, 5 seeds | ANN high-recall stability | 대규모 semantic task quality |

각 외부 데이터는 특정 축만 검증한다. 하나의 데이터가 연구 전체를 외부 재현했다고 쓰지 않는다.

## 3. UCA 2.5-channel 이식

### 3.1 생성 계보

- document: UCF-Crime event frame을 본 pixel-only caption, 6,432개
- relevance: UCA 사람 문장 주석의 결과 전 동결 10종 lexicon
- predicate: duration/container/class/position metadata
- 한계: 독립 센서가 없고 position은 annotation timing과 결합되어 2.5-channel

frame drop, label-key leakage와 lexicon 8-gram 누출은 0건이다.

### 3.2 사전 판정 규칙

네 대조 중 3개 이상이 522와 같은 방향이면 “방향 일치”로 판정한다.

| 대조 | UCA 결과 | 판정 |
|---|---:|---:|
| strict B4−B2 > 0 | +0.1501, pair CI [0.124,0.179] | 성립 |
| clean duration semantic B4−B2 < 0 | -0.0485, CI 0 포함 | 성립, 부호만 |
| semantic 질의별 음수 존재 | 68/129 음수 | 성립 |
| 강결합 class가 container보다 우수 | -0.0558 vs -0.0485 | 불성립 |

3/4 방향 일치다. c4 실패는 결합도 효과를 도메인 보편 법칙으로 부르지 못하게 한다.

## 4. MEVA 이식

### 4.1 canonical

- 985 clips/documents
- 193 queries
- strict qrels 4,405
- semantic qrels 17,205
- predicate: capture location/hour/time-of-day
- relevance: DIVA activity
- document: pixel-only caption
- A6 overall PASS

MEVA는 별도 물리 센서가 없으므로 522와 같은 완전 tri-source가 아니다.

### 4.2 검색

최종 985-scale B0–B5는 파일럿의 유의성을 자기 교정했다. 522에서 관찰한 hard-constraint prefilter의 방향은 재현되지만 caption–event 정합과 semantic 결과의 크기는 달라진다. 초기 소표본 결과는 superseded이며 최종 985/193 결과만 사용한다.

### 4.3 저장 표현

동일 encoder 외부 대조:

- frame−caption semantic Δ +0.0239
- cluster CI [-0.0292,+0.0813]
- storage BH cluster q=0.4008
- dual−caption semantic Δ +0.0690
- cluster CI [+0.0369,+0.1004]
- storage BH cluster q<0.0001

one-frame의 우위는 불확실하다. dual은 표현뿐 아니라 RRF fusion을 함께 바꾸므로 순수 storage replication이 아니다. 따라서 MEVA가 522 multi-frame 효과를 외부 재현했다고 말하지 않는다.

## 5. MIRIS DB 정책 이식

MIRIS의 scene와 상대 stream segment predicate에서 pgvector global/partial을 재실행했다.

- partial recall 0.998–1.000
- partial p50 0.34–0.49ms
- global은 선택적 조건에서 recall 또는 scan latency 병목
- \(N^*\)가 선택도에 따라 81→9,495→30,330→119K→1.4M으로 증가

partial/local의 안정성과 hot/cold 손익분기 형태는 재현됐다. 다만 `tseg`는 실제 시계 시간이 아니라 상대 구간 proxy다.

## 6. 규모와 seed

### 6.1 규모

- 522 task grid: 3,000 clips, task qrels
- real ANN: 132,521/143,830 CLIP vectors
- Qwen ANN: 143,830×2,048
- synthetic scale: 1M vectors, actual 1M frames가 아님

3K 결과는 task quality를, 143K/1M은 ANN fidelity와 시스템 비용을 측정한다. 축을 혼합하지 않는다.

### 6.2 5-seed high-recall

seed마다 index를 새로 구축했다.

- HNSW ef512: mean 0.998118, min 0.996471, median p95 5.757ms
- HNSW ef1024: 5/5 recall 1.0, median p95 10.148ms
- IVF-Flat np256: mean 0.999529, min 0.998824, median p95 37.587ms

관측 범위의 high-recall 운영점은 HNSW ef512다. 다른 corpus/query/build에 대한 보장은 아니다.

## 7. 교차감사

두 독립 비판 감사는 모두 `PASS_WITH_LIMITATIONS`, 치명적 설계 오류 없음으로 판정했다.

### 7.1 감사에서 발견·수정한 항목

- multi-frame+B3+Flat의 empty exact reference를 fidelity 평균에서 제외
- 기존 32/32의 보증 범위를 metric·artifact integrity로 한정
- treatment/statistics 12/12 추가
- MEVA BH 보정 재계산
- BGE와 주 Qwen 격자의 encoder 불연속을 Qwen C1/C2 반복으로 보강
- 3-seed를 high-recall 5-seed로 보강
- 사후 통합 명세를 preregistered confirmatory로 부르지 않도록 수정

### 7.2 검증층

| 층 | 결과 | 보증 |
|---|---:|---|
| joint metric/artifact | 32/32 | ranking/vector/hash/seed와 metric 산술 |
| treatment/statistics | 12/12 | grid, qrel logic, treatment, BH |
| BGE circularity | 12/12 | C1/C2 독립 재계산 |
| Qwen circularity | 10/10 | aligned treatment·CI·anchor |
| high-recall seeds | 8/8 | 30 cells·summary·threshold |
| latest joint arm | 17/17 | pairing, 112-grid, raw metric |

## 8. 일반화 판정표

| 주장 | 외부·강건성 판정 |
|---|---|
| hard constraint에서 filter 가치 | UCA 방향 재현, MEVA 방향 정합 |
| low/high coupling의 연속 법칙 | UCA c4 실패, 탐색적 유지 |
| real predicate가 random mask보다 어려움 | 두 실 코퍼스·복수 엔진에서 재현 |
| partial/local이 선택적 predicate에 유리 | 시내도로와 MIRIS에서 재현 |
| multi-frame 저장 우위 | 522 강한 점추정, 외부 task replication 부재 |
| joint 정렬의 인과 효과 | matched-shuffled 비유의, 미입증 |
| high-recall HNSW 설정 | 143,830 Qwen 5 seeds에서 강건 |
| ANN 향상의 답변 전파 | 세 경계 때문에 보장되지 않음 |

## 9. 결과 지위와 허용 주장

### 허용

- 연구의 일부 방향은 다른 도메인·DB 코퍼스에서 재현됐고 일부는 실패했다.
- UCA는 3/4 방향 일치의 탐색적 외부 이식이다.
- MIRIS는 partial/hot-cold 정책의 독립 DB 교차검증이다.
- seed·scale 보강은 관측 설정의 ANN 안정성을 높인다.
- 남은 공백은 현재 결과를 무효화하지 않지만 외적 타당성과 확증 강도를 제한한다.

### 금지

- “외부 데이터에서도 연구 전체가 증명됐다”고 쓰지 않는다.
- UCA/MEVA를 완전 센서 tri-source라고 부르지 않는다.
- MEVA가 multi-frame 주효과를 재현했다고 쓰지 않는다.
- 143K/1M ANN 결과를 대규모 task quality 보장으로 부르지 않는다.
- independent audit를 peer review 또는 보편성 증명으로 부르지 않는다.
- 5 seeds를 모든 seed에 대한 보장으로 확대하지 않는다.

## 10. 남은 공백

1. 독립 외부 데이터의 동일-Qwen multi-frame task ablation
2. 143,830-vector corpus의 대규모 task relevance qrels
3. 24시간 insert/update/delete/re-caption/re-index 비용
4. 별도 preregistered holdout 확증 연구
5. task-agnostic caption prompt 대조
6. 더 많은 자연결합 intent×facet 쌍

이 항목은 향후 연구이며 현재 논문의 치명적 결함으로 표현하지 않는다.

## 11. 원자산

- UCA: `2026_KIISE/paper_assets/20260712_uca_external/` 및 `project_md/640_RESULTS_uca_external_20260712.md` [정정 2026-07-28: 흡수 후 `project_md/archive/legacy_premerge_20260728/640_RESULTS_uca_external_20260712.md`로 아카이브]
- MEVA: `Datasets/processed/meva_kf1/`, `project_md/700_MEVA_integration_execution_20260713.md` [정정 2026-07-28: 흡수 후 `project_md/archive/legacy_premerge_20260728/700_MEVA_integration_execution_20260713.md`로 아카이브]
- MIRIS/DB: `2026_KIISE/paper_assets/20260713_db_design/`
- cross audit: `2026_KIISE/paper_assets/20260717_ablation_agent_crosscheck/`
- 최종 보고: `2026_KIISE/paper_assets/20260717_ablation_agent_crosscheck/FINAL_CROSS_VALIDATION_REPORT_KO.md`

## 12. 변경 시 재실행 조건

- external canonical/query/qrel/lexicon 변경
- caption model·prompt·encoder 변경
- external comparison acceptance rule 변경
- BH family·cluster definition 변경
- scale corpus composition 또는 synthetic generation 변경
- ANN seed/build/search 설정 변경
- verifier 또는 claim-status 규칙 변경

## 레거시 결과 문서 흡수 (2026-07-28)

SYNC 기준: `manuscript/paper_final.pdf`(2026-07-23 제출본). 두 레거시 문서의 확정 수치는 본문 §3(UCA)·§4(MEVA)에 이미 반영되어 있다. 이 섹션은 본문에 없는 고유 계보·수치·경로를 보존하고 상충 서술을 정정한다.

### A. `640_RESULTS_uca_external_20260712.md`

**(a) 한 줄 요약**: UCA/UCF-Crime 2.5채널 외적 타당성 워크로드의 구축 게이트·A6 감사·동결 4대조 판정(3/4 방향 일치) 결과 보고 — 본문 §3의 원천 문서.

**(b) 본문에 없는 고유 정보**
- 프리레지 계보: 420 Amendment 6+6a(3-렌즈 검토 wf_d349a707-48e 12건 확정 반영); 판정 규칙 "≥3/4 = 방향 일치"는 Amendment 6a(6)에서 동결.
- 원천 규모·정합: UCA 주석 1,854 비디오·23,542 문장(G-A 정합); UCF-Crimes.zip 96GB 비트 정확; G-B 전단사 — Normal 49 id 중복은 동일 파일, 사전순 규칙 동결 `id_to_member.json`, 미매칭 47=UCA 제외분.
- 코퍼스 구축 세부: 비디오당 ≤4 이벤트 linspace, (video,midpoint) 중복 58 붕괴; G-B′ ffprobe 1,854·클램프 7; 프레임 드롭 0; ffmpeg 7.0.2-static.
- 캡션 게이트: Qwen2.5-VL, 렉시콘 무접촉 프롬프트 sha1 고정; G-C 파일럿 50 통과(중앙 84.5 토큰, 기계 토큰 누출 0); 2×3090.
- 질의 산식과 n=129 도출: 구축 135 = 렉시콘 10 전부 채택 × 필드 3(strict 양성 ≥5 ∧ 비디오 ≥5); Normal 계층 5질의 분리 + 퇴화 스크린 1건 봉쇄(RoadAccidents×crash, 봉쇄 0.904 — 사전 예측 그대로) → 분석 대조 n=129.
- A6-UCA 감사 세부: e1 라벨키 0 · e2 렉시콘-8gram 0 · e3 일반 8gram 0.02% ≪ 2%.
- c1 보조 레인: lex-boot CI [0.111,0.197], 비디오-중복제거 +0.142, 3-레인 부호 일치.
- c3 대응 기준값: 522는 18/85 음수(UCA 68/129와 대비).
- 전략 풀 성능(nDCG@10): semantic에서 B2 vector-only 0.247 최고 > B4 0.200 > B1 BM25 0.139; strict에선 B4 0.203 > B2 0.053. 퇴화 쌍 Δ≡0.0(혼입 시 가짜 재현 신호였을 것), Normal 고선택도 계층 +0.076(분리). 절대 성능이 522보다 낮음은 UCA 논문의 "일반 SOTA 저조" 관찰과 정합.
- 한계 세부: event_position_bin은 주석-타이밍 채널로 강등, 코퍼스 멤버십 주석 주도, 라이선스 학술 전용.
- 정본 산출물 경로: `paper_assets/20260712_uca_external/{UCA_contrasts.json, UCA_results.csv, UCA_query_deltas.csv}`; 워크로드 `Datasets/processed/uca_anchor/20260712/`(canonical + `A6_UCA_audit.json` + `workload_table.csv`).

**(c) 상충·정정**
- 실질 상충 없음. 본문 §2의 "135 queries"와 제출 논문 RQ3의 "UCA 129질의"는 상충이 아니라 구축 135 − Normal 분리 5 − 퇴화 봉쇄 1 = 분석 129의 관계다(도출은 640이 보존).
- 640의 확정 수치(c1 +0.1501, c2 −0.0485, c3 68/129, c4 −0.0558 vs −0.0485, 3/4 판정)는 본문 §3.2 및 paper_final RQ3("UCA 129질의 재현 3/4")과 전부 일치.

**(d) 아카이브 경로**: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/640_RESULTS_uca_external_20260712.md`

### B. `700_MEVA_integration_execution_20260713.md`

**(a) 한 줄 요약**: MEVA tri-source 통합 실행 로그 — 확보·파이프라인·소스분리 매핑에서 시작해 276-clip 파일럿(SUPERSEDED)을 거쳐 985/193 확정 스케일업(본문 §4.1 정본 수치)에 이르는 자기교정 전 과정 기록.

**(b) 본문에 없는 고유 정보**
- 확보·라이선스: Kitware GitLab `meva-data-repo` shallow clone → `Datasets/external/meva/meva-data-repo/`(7.6G); 영상 공개 S3 `s3://mevadata-public-01/drops-123-r13/`(무서명 https, CC-BY-4.0 → 파생 VLM 캡션 재배포 합법); avi는 프레임 추출 후 삭제, 저장은 JPG만.
- 스크립트 3종(522 미러): `build_meva_facets.py` / `build_meva_trisource_canonical.py` / `build_meva_captions.py`(추출·캡션 2-phase, 샤딩, resume) — 재실행 커맨드 포함.
- 소스분리 매핑 세부: PREDICATE=capture 메타(time_of_day·location·hour, `facet_source=meva_capture_metadata`) / RELEVANCE=DIVA 37클래스 중 19 희소활동(밀도 1.5–12%) / DOCUMENT=Qwen2.5-VL 픽셀-only 캡션. 활동라벨 predicate 재주입 금지, UAV 제외, EO만 존재→modality predicate 폐기(522 is_weekend와 동일 처리).
- 모집단 세부: 1,443 주석클립 중 961 활동≥1(985 corpus의 모집단); 위치 school 711/bus 417/hospital 187/admin 128; 24 카메라; 질의 193 = low-coupling 191 + contrast 2; 전 질의 low-coupling maxV=0.2138(522 maxV 0.454보다 깨끗한 분리).
- 확정 B0–B5 전량(strict/semantic nDCG@10, bge-m3 1024-dim): B0 0.144/0.138, B1 0.047/0.173, B2 0.027/0.103, B3 0.117/0.112, B4 0.120/0.114, B5 0.125/0.118. B4−B2 semantic n=193 Δ=+0.0115 CI[−0.010,+0.033](0 포함), sign 54/62/77; low n=191 +0.0114; strict Δ≈+0.093. 결과 `results/meva_bgem3_b0_b5/`, 무인 드라이버 `scale_driver.log`.
- 파일럿 기록(SUPERSEDED 명시 보존): 276 clips/73질의(추출 실패 24=S3 키 부재), semantic B4−B2 +0.0394 CI[+0.010,+0.068], 캡션 평균 501자, qrels strict 583/semantic 1,563.
- 확정 해석 4항: ① strict prefilter 이득(B4 0.120 ≫ B2 0.027) ② strict metadata ≫ weak-dense(B0 0.144 ≫ B2 0.027) ③ VLM 캡션 문서 맹점(미세 DIVA 활동 미서술 = 522 주차 미서술 맹점과 동형) ④ soft-intent·독립 predicate에서 prefilter 효과 ≈0(522 refined 결론의 독립 재현).
- 명시적 철회 기록: 파일럿의 "base-retriever 강도가 prefilter 부호를 +로 만드는 2번째 축" 해석은 스케일 null로 철회. 남는 강건 축 = (i) 제약 성격 hard/soft, (ii) 문서채널이 relevance를 담는 정도.
- 비용 실측: 985 프레임 8-shard 추출 73분 + 2-GPU 캡션 36분; 전체 1,443 기준 ~245GB transfer(~16h 추정, 1 clip/40s).

**(c) 상충·정정**
- 문서 헤더 상태문 "문서채널(VLM 캡션)만 GPU-대기"는 stale — 같은 문서 하단에서 당일 완료·전체 A6 7/7 PASS로 갱신됨. 최종 상태는 본문 §4.1이 정본.
- 초기 구조 검증 단계 수치(코퍼스 1,443, 질의 202, strict 4,899/semantic 19,714, A6 구조 6/6)는 캡션 전 단계 값이다. 정본은 985 clips/193 queries/strict 4,405/semantic 17,205·A6 7/7(본문 §4.1과 일치). 202/4,899/19,714를 canonical로 인용 금지.
- 파일럿 semantic B4−B2 유의(+0.0394, CI 0 배제)는 소표본 아티팩트로 스케일에서 소멸(+0.0115, 0 포함) — 본문 §4.2 "초기 소표본 결과 superseded" 서술과 일치하며 원문 자체에도 SUPERSEDED 표기가 있다.
- paper_final과 상충 없음: 제출 논문 본문 주장에 MEVA 검색 수치는 미사용. 2026-07-28 확정 용어 결정의 클립 조작적 정의("배포 파일 1개=1클립", MEVA 계보로 방어)에 대해 700의 MEVA 클립 단위 기록(배포 5분 avi 1파일=1클립)이 근거 자산.

**(d) 아카이브 경로**: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/archive/legacy_premerge_20260728/700_MEVA_integration_execution_20260713.md`
