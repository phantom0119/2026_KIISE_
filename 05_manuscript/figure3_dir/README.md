# 그림 3 provenance 패키지 (figure3_dir)

## 1. 대상

- **캡션 원문** (원고 `manuscript/_archive_20260819/0_paper_script.md` **181행**, 2026-07-23 개정판 기준):
  > **&lt;그림 3&gt; 데이터베이스 계층 설계별 품질-지연 트레이드오프 분포. (a) 의미론적 정답, (b) 엄격한 정답**
- 그림 파일: `manuscript/Figure3.png` (2026-07-20 07:16 생성, 2패널 산점도 + 파레토 테두리)
- 이미지 참조 위치: 원고 179행(`![데이터베이스 계층 설계별 품질-지연 트레이드오프 분포](./Figure3.png)`), 도입 문장 177행, 본문 해설 197행.
- 소속: **§5.2.2 검색용 데이터 구성 평가 (RQ2)**. §4.2에서 정의한 검색용 데이터·검색 계획 16개 조합 × 물리 색인 7종 = **112개 구성**의 nDCG@10 대 p95 검색 지연 분포와 파레토 최적 경계(검은 테두리)를 (a) 의미론적 정답, (b) 엄격한 정답 두 패널로 보여준다.

## 2. 수치 ↔ 원천 매핑

원고에 인쇄된, 그림 3에 귀속되는 수치 전체:

| 원고 수치 (행) | 값 | 원천 파일 (data/ 사본) | 파일 내 위치 |
|---|---|---|---|
| 총 구성 수 (197행, 145행) | 112개 | `data/20260717_joint_image_caption_validation/configuration_summary.csv` | `config` 열 고유값 개수 = 112 |
| 데이터×계획 조합 (197행) | 16개 | 같은 파일 | (`representation`,`search_plan`) 고유 조합 = 16 |
| 물리 색인 설정 (197행) | 7개 | 같은 파일 | `index` 열 고유값 = flat, hnsw_ef64, hnsw_ef256, ivfflat_np8, ivfflat_np32, ivfpq6_np8, ivfpq6_np32 |
| 엄격한 정답에서 검색 전 조건 적용의 향상 (197행) | +0.161 | 같은 파일 | `multi_frame__B4_prefilter__flat`(strict) `ndcg_at_10`=0.26253 − `multi_frame__B2_vector__flat`(strict) 0.10141 = 0.1612 |
| 의미론적 정답에서의 하락 (197행) | −0.093 | 같은 파일 | `multi_frame__B2_vector__flat`(semantic) 0.35182 − `multi_frame__B4_prefilter__flat`(semantic) 0.25864 = 0.0932 |
| 질의 수 (145행 등) | 85개 | 같은 파일 + `manifest.json` | `queries` 열 = 85 / manifest `queries: 85` |
| 엄격한 정답 행 수 (145행) | 6,809행 | `data/20260717_joint_image_caption_validation/manifest.json` | 키 `qrels_strict` |
| 의미론적 정답 행 수 (145행) | 24,872행 | 같은 파일 | 키 `qrels_semantic` |
| 품질 측정 건수 (145행) | 19,040건 (112×85×2) | `data/20260717_joint_image_caption_validation/per_query_metrics.parquet` | 행 수 = 19,040 |
| 지연 반복 측정 (145행, 137행) | 95,200회 (질의당 10회) | `data/20260717_joint_image_caption_validation/latency_trials.parquet` | 행 수 = 95,200; manifest `latency.repeats: 10`, `warmup_rounds: 2` |
| 색인 구축 파라미터 (143행) | HNSW M=32·efC=200·efSearch 64/256, nlist=64·nprobe 8/32, PQ m=32·6비트 | `data/20260717_joint_image_caption_validation/manifest.json` | 키 `index_training` + `indexes` 이름 규약 |
| 사후 필터 후보군 (145행) | 상위 200개 | 같은 파일 | 키 `postfilter_vector_k: 200` |
| 파레토 테두리 점 (그림 내 시각 요소, 수치 미인쇄) | (a) 9개, (b) 19개 | `data/20260717_joint_image_caption_validation/pareto_front.csv` | 28행 = semantic 9 + strict 19; `analyzed_configuration_summary.csv`의 `pareto_quality_latency_storage` 플래그 합과 일치 |

참고: 그림 3의 개별 점 좌표(x=`latency_p95_ms`, y=`ndcg_at_10`, 색=`representation`, 모양=`search_plan`)는 모두 `configuration_summary.csv`의 224행(112 구성 × 정답 기준 2종)이다. 표 4의 다섯 구성 수치(0.181, 0.352 등)도 같은 파일의 `B2_vector`+`flat` 행에서 나오지만 표 4는 별도 패키지 대상이다.

## 3. 사용 데이터셋

- **원본**: AI Hub 교차로(522 다중각도 CCTV) 클립 **3,000개**, 질의 85개, 엄격한 정답 6,809행·의미론적 정답 24,872행.
  - 캐노니컬(동결): `/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/qwen35_9b/522/canonical`
  - 통합(unified) 임베딩: `/hdd2/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_unified_qwen35captions`
  - 결합(joint) 임베딩: `/hdd2/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_joint_image_caption_qwen35captions`
- **전처리**: 클립별 Qwen3.5-9B 설명문(최대 110토큰, 탐욕적 디코딩)과 대표/다중 정지화면을 Qwen3-VL-Embedding-2B 2,048차원 단일 벡터 공간에 매핑(L2 정규화)했고, 다중 이미지는 클립당 최대 3벡터(총 8,349벡터), 이중 색인은 설명문+다중 이미지 두 레인을 RRF(k=60)로 결합한다.

## 4. 실험 체계

- **사용 스크립트** (실행 순):
  1. `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/build_qwen3_joint_image_caption_assets.py` — joint image-caption 벡터 물질화
  2. `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/run_joint_storage_search_index.py` — 112개 호환 구성 격자 실행 → `configuration_summary.csv`, `per_query_metrics.parquet`, `latency_trials.parquet`, `rankings.parquet`, `manifest.json`
  3. `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/analyze_joint_optimization_validation.py` — 부트스트랩 10,000회·BH 보정·파레토 판정 → `analyzed_configuration_summary.csv`, `pareto_front.csv`, `analysis_manifest.json`
  4. 검증: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/scripts/verify_joint_image_caption_experiment.py` (독립 재검증 JSON/MD 산출)
- **모델·임베딩**: 설명문 Qwen3.5-9B, 임베딩 Qwen3-VL-Embedding-2B(2,048차원, L2 정규화), Faiss CPU 단일 스레드.
- **시드**: 실행·분석 공통 `seed=20260717` (부트스트랩 10,000회 동일 시드).
- **핵심 파라미터**: TOP_KS=[1,5,10,20], MAX_RANK=100, postfilter 후보 200, 지연 warmup 2회·반복 10회·질의 순서 무작위화, HNSW M=32/efC=200, IVF nlist=64, PQ m=32·6bit; 파레토 목적 = `ndcg_at_10` 최대화, `latency_p95_ms`·`index_mb` 최소화(정답 기준별 판정).
- **사전등록/결과 문서**:
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/820_JOINT_IMAGE_CAPTION_SINGLE_VECTOR_PROTOCOL_20260717.md` (프로토콜, §7에 실행기·산출물 명시)
  - `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/project_md/821_RESULTS_joint_image_caption_single_vector_20260717.md` (결과)

## 5. 재현 방법

**(A) 원천 재실행 경로** (동결 캐노니컬·임베딩 필요, /hdd·/hdd2 마운트 전제):

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE
# 1) joint 벡터 물질화(이미 존재하면 생략)
python3 scripts/build_qwen3_joint_image_caption_assets.py
# 2) 112개 구성 격자 실행 (출력: paper_assets/20260717_joint_image_caption_validation/)
python3 scripts/run_joint_storage_search_index.py
# 3) 통계 분석 + 파레토 판정
python3 scripts/analyze_joint_optimization_validation.py --seed 20260717
```

**(B) data/ 사본만으로 재집계·재작도하는 최소 경로** (그림의 모든 점·테두리 재현):

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/figure3_dir
python3 - <<'EOF'
import pandas as pd, matplotlib.pyplot as plt
an = pd.read_csv('data/20260717_joint_image_caption_validation/analyzed_configuration_summary.csv')
panels = [('semantic','(a) 의미론적 정답'), ('strict','(b) 엄격한 정답')]
rep_c = {'caption':'C0','representative_frame':'C1','joint_image_caption':'C2','multi_frame':'C3','dual':'C4'}
plan_m = {'B2_vector':'o','B3_postfilter':'s','B4_prefilter':'^','B5_lexical_vector_hybrid':'D'}
fig, axes = plt.subplots(1, 2, figsize=(11,4.5), sharey=True)
for ax,(sc,title) in zip(axes,panels):
    g = an[an.scoring==sc]
    for (rep,plan),part in g.groupby(['representation','search_plan']):
        ax.scatter(part.latency_p95_ms, part.ndcg_at_10, c=rep_c[rep], marker=plan_m[plan],
                   edgecolor=['black' if p else 'white' for p in part.pareto_quality_latency_storage],
                   linewidth=1.0, s=45)
    ax.set_xscale('log'); ax.set_title(title); ax.set_xlabel('p95 검색 지연 (밀리초, 로그 척도)')
axes[0].set_ylabel('nDCG@10')
fig.savefig('Figure3_reaggregated.png', dpi=200, bbox_inches='tight')
EOF
# 본문 수치 재확인 (112, +0.161, -0.093)
python3 - <<'EOF'
import pandas as pd
cs = pd.read_csv('data/20260717_joint_image_caption_validation/configuration_summary.csv')
print('configs:', cs.config.nunique())
nd = lambda p,s: float(cs[(cs.representation=='multi_frame')&(cs.search_plan==p)&(cs['index']=='flat')&(cs.scoring==s)].ndcg_at_10.iloc[0])
print('strict delta:', round(nd('B4_prefilter','strict')-nd('B2_vector','strict'),3))
print('semantic drop:', round(nd('B2_vector','semantic')-nd('B4_prefilter','semantic'),3))
EOF
```

주의: 현재 `manuscript/Figure3.png`(07-20 07:16)를 픽셀 단위로 재현하는 최종 작도 스크립트는 리포지터리에 보존되어 있지 않다(§7 참고). 위 (B)는 동일 데이터·동일 파레토 플래그로 그림의 정보 내용을 재현하는 최소 코드다.

## 6. 포함 파일 목록

`data/20260717_joint_image_caption_validation/` — 원 위치 `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260717_joint_image_caption_validation/` (원 파일명 유지):

| 사본 | 설명 |
|---|---|
| `configuration_summary.csv` | 112 구성 × 2 정답 기준 = 224행. 그림의 x(p95)·y(nDCG@10)·색·모양의 원천 |
| `analyzed_configuration_summary.csv` | 위 + BH q값·`pareto_quality_latency_storage` 플래그(검은 테두리 원천) |
| `pareto_front.csv` | 파레토 구성 28행(semantic 9, strict 19) |
| `manifest.json` | 실행 매니페스트: 시드 20260717, 85질의, 3,000클립, qrels 6,809/24,872, 색인 파라미터, 지연 프로토콜, 입력 해시 |
| `analysis_manifest.json` | 분석 매니페스트: 부트스트랩 10,000회, 파레토 목적, 입력 해시 |
| `per_query_metrics.parquet` | 질의 수준 결과 19,040행(=112×85×2, 원고 145행의 건수 그 자체) |
| `latency_trials.parquet` | 지연 원시 시행 95,200행(=112×85×10, 원고 145행의 반복 횟수 그 자체) |
| `rankings.parquet` | 구성별 검색 순위 760,746행(분석 스크립트 입력, 해시 대상) |
| `latency_summary.csv` / `quality_summary.csv` | 구성별 지연·품질 중간 집계 |
| `RESULTS_KO.md` | 실험 한국어 결과 요약 |
| `JOINT_IMAGE_CAPTION_VERIFICATION_KO.md`, `joint_image_caption_independent_verification.json` | 독립 재검증 기록 |

`data/qwen2048_high_recall_5seed/` — 원 위치 `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/paper_assets/20260717_ablation_agent_crosscheck/qwen2048_high_recall_5seed/`:

| 사본 | 설명 |
|---|---|
| `summary.csv`, `results.csv`, `manifest.json`, `RESULTS_KO.md`, `independent_verification.json` | 143,830벡터·5시드 고재현율 ANN 강건성 결과. `figure3_resources.zip`이 입력으로 명시하여 동봉하나, 현행 2패널 그림 3에는 **그려지지 않는다**(§7 비고) |

**복사하지 않은 대용량/외부 파일 (경로 참조만)**:

- 그림 원본: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/Figure3.png` (1.0MB, 대상 그 자체이므로 중복 복사 생략)
- 리소스 zip: `/home/explorer/vectorDB/experiments/db/KIISE_datasociety/2026_KIISE/manuscript/figure3_resources.zip` (zip 복사 금지 규칙)
- 임베딩 덤프: `/hdd2/KIISE_datasociety/Datasets/processed/aihub_522_intersection/20260710/embeddings_qwen3vl2b_unified_qwen35captions/`, 같은 경로의 `..._joint_image_caption_qwen35captions/`
- 동결 캐노니컬: `/hdd/KIISE_datasociety/experiments/caption_model_ablation/20260715/qwen35_9b/522/canonical/`

## 7. 검증

data/ 사본에서 python3(pandas)로 실제 재조회·재계산한 결과 (2026-07-23):

| # | 항목 (원고 행) | 원고 값 | 사본 재계산 | 판정 |
|---|---|---|---|---|
| 1 | 총 구성 수 (197, 145) | 112 | 112 (`config` 고유값) | PASS |
| 2 | 데이터×계획 조합 (197) | 16 | 16 | PASS |
| 3 | 물리 색인 설정 (197) | 7 | 7 | PASS |
| 4 | 질의 수 (145) | 85 | 85 | PASS |
| 5 | 엄격 정답 사전필터 향상 (197) | 0.161 | 0.26253−0.10141=0.1612→0.161 | PASS |
| 6 | 의미론적 정답 하락 (197) | 0.093 | 0.35182−0.25864=0.0932→0.093 | PASS |
| 7 | 엄격한 정답 행 수 (145) | 6,809 | 6,809 (`qrels_strict`) | PASS |
| 8 | 의미론적 정답 행 수 (145) | 24,872 | 24,872 (`qrels_semantic`) | PASS |
| 9 | 품질 측정 건수 (145) | 19,040 | 19,040 (parquet 행 수) | PASS |
| 10 | 지연 측정 횟수 (145) | 95,200 | 95,200 (parquet 행 수) | PASS |
| 11 | 클립 수 (174, 194) | 3,000 | 3,000 (manifest) | PASS |
| 12 | 지연 반복 10회 (137) | 10 | 10 (manifest) | PASS |
| 13 | 준비 실행 2회 (137) | 2 | 2 (manifest) | PASS |
| 14 | 사후필터 후보 200 (145) | 200 | 200 (manifest) | PASS |
| 15 | HNSW M=32 (143) | 32 | 32 | PASS |
| 16 | efConstruction=200 (143) | 200 | 200 | PASS |
| 17 | nlist=64 (143) | 64 | 64 | PASS |
| 18 | PQ m=32·6비트 (143) | 32/6 | 32/6 | PASS |
| 19 | 파레토 플래그 정합 (그림 테두리) | — | pareto_front 28행 = analyzed 플래그 합 28 (semantic 9 + strict 19) | PASS |

**총괄: 19/19 PASS.** 캡션의 패널 구성 "(a) 의미론적 정답, (b) 엄격한 정답"은 Figure3.png 패널 제목과 육안 대조로 일치를 확인했다.

**UNVERIFIED / 비고 (얼버무리지 않고 명시)**:

1. **최종 작도 스크립트 미보존**: 현행 2패널 `Figure3.png`(2026-07-20 07:16)를 생성한 스크립트는 `scripts/`·git 이력·`.omc/` 어디에서도 발견되지 않았다. `scripts/generate_manuscript_visuals_v6.py`의 `figure_6_joint_design()`(출력명 `fig3_storage_tradeoff_v7`)은 **다른 그림**(5점 저장량 산점도)이며 현행 Figure3.png와 md5가 불일치한다. 따라서 데이터→수치 provenance는 전부 검증됐지만, 픽셀 수준 렌더링 재현은 §5(B)의 재작도 코드로 갈음한다.
2. **qwen2048_high_recall_5seed의 귀속**: `figure3_resources.zip`이 이 summary.csv를 그림 3 입력으로 명시하나, 해당 데이터(143,830벡터 대규모 ANN, ef256–1024/nprobe128–512)는 현행 2패널 그림의 어떤 점과도 대응하지 않는다(그림 x축 최대 ~5ms, 112개 구성은 3,000클립 스케일). 대규모 색인 결과(원고 표 10 계열)에 속할 가능성이 높아 참고용으로만 동봉한다.


## 8. 2026-08-09 용어 재생성 (심사 대응 개정판) — 렌더 스크립트 보존 해결

- §7 비고 1(최종 작도 스크립트 미보존)을 해소: `render_figure3_terms_20260809.py`가 현행 그림의 정본 렌더 스크립트다. §5(B) 레시피와 동일 데이터(`data/.../analyzed_configuration_summary.csv`, 112구성×2기준, 파레토 28점)로 작도하며, 팔레트 5색은 구판 PNG 범례 스와치 실측값(#0282C9/#FDC307/#02B18F/#E082BF/#EA5603)이다.
- 범례 라벨을 개정 원고 용어로 교체: 클립 설명문→영상 설명문, 대표 정지화면→대표 이미지, 여러 정지화면→다중 이미지.
- 교체 전 제출본 백업: `Figure3_pre_terms_20260809.png`.
- 재실행: `python3 render_figure3_terms_20260809.py /path/to/Figure3.png`

## 9. 2026-08-16 파레토 판정 표기 보강

- 점 좌표·색·기호·검은 테두리 플래그와 축 범위는 유지했다.
- 가로축을 파레토 판정과 동일한 p95 검색 지연으로 변경했다.
- 그림의 목적을 즉시 확인할 수 있도록 `검색용 데이터·검색 계획·물리 색인에 따른 검색 품질–p95 지연 상충과 파레토 구성` 제목을 추가했다.
- 가로축 단위를 `ms`로 표기했다.
- 파레토 판정의 세 지표인 nDCG@10·p95 검색 지연·색인 크기를 그림 안에 명시했다.
- 범례를 `검은 테두리: 3지표 파레토`로 구체화했다.
- 현행 `manuscript/Figure3.png`: md5 `c7c750cbdbe658021c981e2457feeda0`, 1768×1010 RGBA PNG.
