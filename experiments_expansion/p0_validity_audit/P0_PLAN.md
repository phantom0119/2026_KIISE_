# 예비 타당성 실험(P0) 실행 계획 — 2026-08-05 착수

목적: "진짜 조건 vs 가짜 조건" 벤치마크 검증 연구(감사 문서 CORAL_PROBLEM_BACKGROUND...20260804.md의 P0)를 실행해 게이트 판정에 필요한 증거를 확보한다. 본 문서는 2026-08-05 정찰(3-에이전트, 내부 자산·공개 데이터·경쟁 코드) 결과를 반영한 실행 계획이다.

## 0. 한 줄 판정 목표 (게이트)

1. **G1**: 난이도(α-hardness)를 맞춘 합성 조건으로도 설명되지 않는 "진짜 조건만의 추가 어려움"이 남는가?
2. **G2**: 그 어려움이 최신 robust 방법(ACORN-γ, 엔진 안전 경로) 중 하나 이상에서도 SLA 관점에서 실질적인가?
3. **G3**: 내부 CCTV만이 아니라 공개 코퍼스(텍스트·이미지) 최소 1개씩에서도 재현되는가?

G1과 G2가 모두 실패하면 이 연구 주제를 중단한다(감사 문서 §8.1).

## 1. 일정 판정 (사용자 질문 "2~3주가 정확한가"에 대한 답)

- **순수 컴퓨트는 작다**: 내부 코퍼스는 13만~14만 벡터 규모라 정확 전수 계산이 초~분 단위, kNN 그래프 구축 10~30분/코퍼스, 방법 재실행은 시간 단위.
- **기간을 결정하는 것은 통합 작업 2건**: ① HCBGen(난이도 보정 생성기) 적응 — 최선 2~3일 / 현실 4~6일, ② ACORN 빌드 — 최선 1일 / 현실 2~4일.
- **결론**: 3개 작업 흐름을 병렬로 돌리면 **최선 7~9 근무일(약 1.5주), 현실 10~15 근무일(2~3주)**. "2~3주"는 버퍼가 아니라 통합 리스크를 포함한 현실 구간이며, 아래 단축 가정이 전부 성립하면 1.5주 내 종료 가능.
- **더 빠른 조기 종료 경로**: 게이트를 단계 판정한다. **내부 데이터만으로 G1을 1주차에 우선 판정** — 내부는 세 문제지 중 2개(진짜, 무작위)가 이미 완성돼 있어 HCBGen 적응만 되면 즉시 3-arm 비교가 가능하다. 1주차 G1이 "난이도 보정으로 전부 설명됨"이면 그 시점에 중단(≈1주 만에 결론). G1 통과 시에만 공개 데이터 복제(G3)로 2~3주차 진행.

### 단축 가정 (전부 성립 시 ~1.5주)
1. HCBGen의 사전 컴파일 바이너리 호환 문제(glibc 2.34 요구, 호스트는 2.31)를 Docker(우분투 22.04) 또는 파이썬 재구현(반나절)으로 즉시 우회
2. ACORN이 HCBGen에 내장된 파이썬 하니스(ACORN_build.py, Stanford 포크와 바이트 동일 확인됨)로 첫 시도에 빌드
3. 질의 모집단 결정(아래 §5 결정사항 1)이 첫날 확정
4. GPU 1장(현재 1장은 타 작업 22GB 점유) 사용 가능 유지

## 2. 정찰 확정 사실 (2026-08-05)

### 내부 자산 — 준비 완료
- 코퍼스 A(시내도로): `/hdd2/KIISE_datasociety/Datasets/processed/sinnaedoro_traffic/corpus_real/frame_embeddings.npy` (132,521×512 f4) + 질의 1,000 + 잠긴 predicate 29종(`paper_assets/20260710_pillarB/P1_predicates_A.csv`)
- 코퍼스 B(교차로): `.../aihub_522_intersection/20260710/visual_embeddings_clip/frame_embeddings.npy` (143,830×512) + 질의 200 + 잠긴 predicate 26종
- **세 문제지 중 2개 이미 존재**: 진짜 조건 + 같은 선택도 무작위 마스크(M9, 시드 고정) + 보너스로 위치 고정 양성 대조(S3)까지
- 재사용 스크립트: `2026_KIISE/scripts/run_filtered_ann_real_predicate.py`(방법 재실행), `run_filtered_ann_cluster_mechanism.py`(집합 밀집도 함수 포함), `run_engine_filtered_bench.py`(Milvus/Weaviate)
- 검증 앵커(재실행 결과 대조용): postfilter K'=4k 진짜 조건 recall A 0.306 / B 0.667 등 기존 CSV 일체
- 엔진 컨테이너 4종(pgvector:5433, Milvus 2.6, Weaviate 1.35.3, Qdrant) 가동 중
- **완료된 안전 조치(08-05)**: MIRIS 코퍼스(59,019×512, 컨테이너 안에만 존재하던 것)를 `Datasets/processed/miris_backup_20260805/`에 npy+메타데이터로 백업 완료

### 새로 작성해야 하는 코드 (P0-1, 총 2~3일 분량)
1. GLS(질의 주변 지역 선택도/전역 선택도, k=10/50/100/1000) — 전역 정확 top-K 계산 후 자명
2. 거리비 α-hardness — 같은 계산에서 파생
3. k번째 유효 항목의 전역 rank 깊이(무상한) — 기존 gt_cluster_med_rank는 중앙값·1000 상한이라 재계산 필요
4. predicate 집합의 kNN 그래프 conductance — scipy sparse로 (networkx는 규모상 불가)
5. 질의-predicate 쌍 단위 결과 저장 계층(기존 산출물은 predicate 집계뿐)

### 공개 데이터 (P0-2)
- **YFCC-10M** (이미지, 실측 태그): 전 파일 공개 CDN, 총 2.9GB, CC-BY 4.0, 등록 불필요. **08-05 다운로드 시작됨** → `Datasets/public_fanns/yfcc10m/`. GT 전수 계산은 fp16으로 3090 1장에 통째로 적재 가능, 수 분 규모.
- **arxiv-for-fanns** (텍스트, 실측 속성 11종): HuggingFace `SPCL/arxiv-for-fanns-large` 공개(46GB, 4096차원 270만 건). **주의: 전체 규모 인덱스 빌드는 RAM 96GB+ 필요, 이 호스트는 62GB** → P0에서는 -medium(100k) 또는 50만~100만 부표본으로 축소 실행(예비 판정에는 충분), 본실험에서 대형 서버(palisade2) 검토.
- MoReVec: 백업 옵션(라이선스 불명 + Google Drive 쿼터 리스크 — 저자 문의 전 사용 금지)

### 경쟁 코드 (P0-3/P0-4) — 스크래치패드에 클론 완료
- **HCBGen** (`scratchpad/repos/hardness_aware_fann_benchmarking`): 필요한 두 진입점(기존 데이터 Load 모드, MATCH-PDF 난이도 매칭) 실재 확인. 마찰 요소: ① glibc 2.34 요구 바이너리 2개 → Docker 우회 또는 파이썬 재구현, ② ACORN import 버그 1줄, ③ 미선언 의존성(pip 설치 가능), ④ 공개 코퍼스에서는 질의당 비용 때문에 predicate당 수백 질의로 부표본 필수. **라이선스 파일 없음 → 결과 발표 전 저자(SNU 그룹) 서면 허락 필요.**
- **ACORN** (`scratchpad/repos/ACORN`): Stanford FAISS 포크, 미유지보수(빌드 이슈 2건 미해결). 완화책: HCBGen이 동일 포크를 내장하며 파이썬 구동 하니스 제공. 대체재: Weaviate 내장 ACORN(이미 실험 이력 있음, 단 γ 조절 불가 — 엔진 arm으로만 인정).
- **RACORN-1** (`scratchpad/repos/racorn`): **공개 코드 발견**(github.com/naver/racorn, Apache-2.0). run_light.sh 스모크 테스트 ~40분. USearch 기반이므로 Stanford ACORN과 구현 상이함을 보고 시 명시.
- big-ann-benchmarks 하니스(`scratchpad/repos/big-ann-benchmarks`): YFCC 필터 트랙 표준 실행 1~2일, 자체 predicate 통합 +2~3일.

## 3. 작업 흐름 (3개 병렬)

| 흐름 | 내용 | 담당 리소스 | 일정 |
|---|---|---|---|
| W1 특성·내부 3-arm | P0-1 특성 코드 5종 작성·검증 → 내부 두 코퍼스 재계산 → HCBGen arm 생성 → G1 판정 | CPU + 파이썬 | 1~7일차 |
| W2 공개 데이터 | YFCC 수령 확인·포맷 리더 → arxiv-medium 수령 → predicate 사전 잠금 문서 → GT 전수 계산(GPU) | GPU 1장 + 디스크 | 1~5일차 |
| W3 경쟁 방법 | HCBGen 환경 수리(Docker/재구현) → ACORN 빌드(HCBGen 하니스 경유) → RACORN-1 스모크 → 엔진 arm 재확인 | CPU + Docker | 1~8일차 |

8~12일차: 공개 코퍼스 3-arm 실행(G3) + robust 방법 판정(G2) + 게이트 종합 보고서.

## 4. 사전 등록 원칙 (감사 문서 준수)

- predicate는 결과를 보기 전에 스키마 규칙으로 잠근다(내부는 기존 P1 등록부 재사용, 공개 코퍼스는 실행 전 본 폴더에 잠금 문서 작성).
- 게이트 판정 기준(효과 크기·SLA 임계)을 실행 전에 이 폴더에 기록한다.
- "자연 상관 ρ=0.62-0.895" 등 감사가 금지한 표현 사용 금지. 기호는 ρ_GLS와 ρ_Spearman으로 분리.

## 5. PI 결정 필요 사항 (병목 방지를 위해 조기 확정 요망)

1. **질의 모집단**: P0-1 재계산의 질의를 EXP03 ANN-충실도 계층(A 1,000 / B 200 프레임 질의)으로 확정할지. (권고: 예 — 기존 결과와 직접 대조 가능)
2. **arxiv 규모**: P0에서 -medium(100k) vs 부표본 50만~100만. (권고: medium으로 파이프라인 검증 후 부표본 확대)
3. **HCBGen 라이선스**: 저자 서면 문의 발송 시점(권고: 즉시 — 같은 그룹이 RACORN-1도 보유, 한 번에 문의)
4. **GPU 배정**: 타 작업이 점유 중인 3090 외 1장을 P0 전용으로 확보

## 6. 완료 기록

- [x] 2026-08-05: 정찰 3종 완료(내부 자산·공개 데이터·경쟁 코드), 본 계획 수립
- [x] 2026-08-05: MIRIS 컨테이너 → npy 안전 백업 (`miris_backup_20260805/`, 두 테이블 59,019×512 검증)
- [x] 2026-08-05: YFCC-10M 5개 파일 다운로드 백그라운드 시작
- [x] 2026-08-05: **W1 특성 계산 완료** (`scripts/w1_compute_workload_features.py` → `w1_features/`) — 코퍼스 A 29 predicate + B 25 predicate × (자연 1 + 무작위 대조 3) arm, 질의-쌍 단위 GLS(k=10/50/100/1000)·rank10 깊이·α_sim·conductance·compactness. **검증 통과**: 원본 M9 공변량 재현 최대 오차 A 0.1 / B 0.2(반올림 수준), B의 시드 질의 200개 선택까지 재현. 1차 발견은 `w1_features/FIRST_LOOK.md` — 자연 predicate는 국지 고갈(음의 ρ_GLS, A 중앙값 −1.0 / B −0.27), 무작위는 ρ≈0; A 자연 쌍 67%는 10번째 유효 항목이 postfilter 4× 예산 밖(무작위 0%); conductance 자연 0.18 vs 무작위 0.95. 감사의 수정 프레이밍(고갈이 기전)을 데이터가 지지.
- [x] 2026-08-05: **W2 데이터 수령 완료** — YFCC-10M 5파일 헤더 검증(1,000만×192 uint8), arxiv-for-fanns-medium 12파일 1.8GB 구조 검증(100,000×4096 fp32, 실측 속성 11종, GT 3종; 가변 길이 ivecs 주의사항은 `arxiv_fanns_medium/DOWNLOAD_MANIFEST.md`).
- [x] 2026-08-05: **W3 통합 3건 전부 성공** (스크래치패드 격리, 상세는 각 저장소의 REPRO.md/BUILD_NOTES.md):
  - HCBGen 가동: venv 구축, ACORN import 버그 패치, glibc 비호환 바이너리 2개를 파이썬 포팅으로 대체(전수 브루트포스 대조 단위시험 통과), 합성 데이터로 전 파이프라인(무작위 생성→난이도 추정→MATCH-PDF 매칭 생성→검증) 스모크 성공 — 목표 난이도 히스토그램 재현 확인. 주의: 추정기는 체크포인트(20/1000/5000...)에서만 저장, Post_Filtering에는 --dev_mode 필요, cwd=HCBGen_v2 고정.
  - ACORN 빌드 성공: 상류 이슈 #1 재현 후 CMake 1줄 패치로 해결, 최소 드라이버로 ACORN-γ 정확성 확인(10k×64, recall@10=0.993, 필터 위반 0). **주의: 현재 빌드는 최적화 플래그 없음 — 지연 측정 전 -DCMAKE_BUILD_TYPE=Release 재빌드 필수.**
  - arxiv-medium 수령·검증 완료(위 W2).
- [ ] 내부 코퍼스 HCBGen arm 생성(난이도 매칭 3번째 문제지) → 세 문제지 완성
- [ ] 방법 재실행: 저장된 대조 마스크(npz)로 질의-쌍 단위 recall을 특성과 짝짓기 (+ACORN-γ Release 재빌드 포함)
- [ ] G1 내부 판정 (1주차 목표 — 통합 리스크 해소로 일정 단축 가능성 높음)
- [ ] 공개 코퍼스 predicate 잠금 문서 + 3-arm 실행 → G2/G3 판정 + 종합 보고서

### 일정 갱신 (08-05 저녁)
착수일에 일정 변수 2개(HCBGen 적응 2~6일 예상, ACORN 빌드 1~4일 예상)가 모두 수 시간 내 해소됨 → **잔여 작업 기준 최선 경로(총 ~1.5주) 달성 확률이 크게 상승**. 남은 주요 변수는 HCBGen을 실제 512차원 CLIP 코퍼스에 적용할 때의 규모 문제(질의당 난이도 계산 비용 → predicate당 질의 부표본 프로토콜 필요)뿐.
