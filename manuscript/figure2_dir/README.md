# 그림 2 관리 디렉터리 — AI Hub 교차로 정답 정보 통제 주입

## 1. 현행 그림

- 원고 위치: `manuscript/0_main_paper.md` 5.2.1절
- 캡션: **AI Hub 교차로의 정답 정보 통제 주입에 따른 의미론적 nDCG@10 변화**
- 파일: `manuscript/Figure2.png`
- 생성 함수: `scripts/generate_manuscript_visuals_v6.py::figure_2_circularity()`
- 구성: AI Hub 교차로 통제 주입 결과만 표시한다. 이전 그림의 VRU-Accident 전후 막대 패널은 표 3과의 중복 및 서로 다른 작업 부하의 전후 비교가 주는 오해를 줄이기 위해 제거했다.
- 현행 PNG: 1458×724, md5 `b897cf07bde873fd32b51cdc46fd8249`

## 2. 수치와 원천

그림은 모두 의미론적 정답 기준의 nDCG@10을 사용한다. 점 옆에는 `기준 대비 변화량 (조건별 점수)`를 표시한다.

| 그림 항목 | 표시값 | 원천 |
|---|---:|---|
| 정답 정보 미주입 기준 | 0.181 | `data/summary.csv`: `C1,qwen_clean,semantic` = 0.1810046055 |
| 무작위 대조 조건 | −0.061 (0.120) | `data/summary.csv`: random−clean = −0.0609633933 |
| 정답 조건 주입 | +0.819 (1.000) | `data/contrasts.csv`: C1 semantic `mean_delta` = 0.8189953945 |
| 정답 라벨 재진술 주입 | +0.673 (0.854) | `data/contrasts.csv`: C2 semantic `mean_delta` = 0.6726820382 |

정답 조건 주입과 정답 라벨 재진술 주입에는 두 부트스트랩 신뢰구간을 함께 표시한다.

| 조건 | 질의 95% 신뢰구간 | 조건–의미 쌍 군집 95% 신뢰구간 |
|---|---:|---:|
| 정답 조건 주입 | [0.780, 0.855] | [0.738, 0.882] |
| 정답 라벨 재진술 주입 | [0.626, 0.718] | [0.568, 0.752] |

무작위 대조 조건의 0.120은 동일 선택도의 무작위 조건 1,000회 평균이다. 원자료는 `data/random_filter_replicates.csv`이며, 의미론적 nDCG@10의 평균은 0.1200412122이다.

## 3. 실험 조건

- 코퍼스: AI Hub 교차로 검색 문서 3,000개
- 질의: 85개
- 설명문 생성 모델: Qwen3.5-9B
- 임베딩 모델: Qwen3-VL-Embedding-2B, 2,048차원, L2 정규화
- 통제 조건: 정답 정보 미주입, 정답 조건 주입, 정답 라벨 재진술 주입과 동일 선택도의 무작위 대조 조건
- 부트스트랩: 질의 단위 및 25개 조건–의미 쌍 군집 단위 각 10,000회
- 무작위 대조 조건: 1,000회

실행 스크립트는 `scripts/run_qwen_aligned_circularity_control.py`, 독립 검증 스크립트는 `scripts/verify_qwen_aligned_circularity.py`이다. `data/independent_verification.json`의 10개 검증 항목은 모두 통과했다.

## 4. 재생성

원자료에서 정본 그림을 생성한 뒤 원고 파일로 복사한다.

```bash
cd /home/explorer/vectorDB/experiments/db/KIISE_datasociety
python3 -c "import runpy; ns=runpy.run_path('2026_KIISE/scripts/generate_manuscript_visuals_v6.py'); ns['figure_2_circularity']()"
cp 2026_KIISE/paper_assets/20260717_manuscript_visuals_v6/fig2_circularity_integrated_v6.png 2026_KIISE/manuscript/Figure2.png
```

격리된 출력 디렉터리에서 확인하려면 다음 보조 스크립트를 사용한다.

```bash
python3 2026_KIISE/manuscript/figure2_dir/render_figure2_terms_20260809.py /tmp/kiise_figure2_redraw
```

## 5. 포함 자료

- `data/summary.csv`: 조건별 엄격한·의미론적 nDCG@10
- `data/contrasts.csv`: 평균 변화량과 질의·군집 부트스트랩 신뢰구간
- `data/manifest.json`: 입력 수, 모델, 반복 수와 해시
- `data/random_filter_replicates.csv`: 무작위 대조 조건 1,000회 원자료
- `data/per_query_metrics.parquet`: 조건별 질의 단위 지표
- `data/independent_verification.json`: 독립 재계산 결과
- `data/vru_collapse_table.csv`, `data/vru_collapse_table.md`, `data/metrics_semantic.csv`: 삭제된 구판 VRU-Accident 패널의 재현 자료로만 보존하며 현행 그림에는 사용하지 않는다.

## 6. 검증 결과

현행 그림의 기준값 1개, 조건별 점수 및 변화량 3쌍, 부트스트랩 신뢰구간 4개와 실험 규모를 원자료에서 다시 계산해 모두 일치함을 확인했다. 그림의 0.854는 원자료 0.8536866437을 소수 셋째 자리로 반올림한 값이며, 본문은 소수 넷째 자리인 0.8537로 표기한다.
