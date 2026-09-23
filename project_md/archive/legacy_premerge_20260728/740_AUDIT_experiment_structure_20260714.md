# 740 — 실험 전체 구조 재점검 (디스크 실측 감사), 2026-07-14

방법: 20-에이전트 workflow(wf_2acc8236)가 데이터셋 10 + 실험축 9를 **디스크 실측**으로 독립 검증(논문 주장 아님). 데이터셋 감사 ↔ 축 감사 교차검증. 전 축 `real_measured`, 데이터셋 8/10 실사용.

## 1. 데이터셋 인벤토리 (확보 × 역할 × 실사용 × 어떻게)

| 데이터셋 | 크기 | 역할 | 사용 판정 | 어떻게(저장/검색/색인) |
|---|---|---|---|---|
| **aihub_522_intersection** | 142G | **헤드라인 tri-source + 색인코퍼스 B** | ✅ 결과에 쓰임 | 검색 B0–B5(§6, 85질의 expanded)·filtered-ANN 코퍼스B(143,830×512 CLIP, §7)·저장단위(§7.5)·KG붕괴(§7.4)·지각벽(§8). A6 6/6 PASS |
| **sinnaedoro_traffic** | 2.5G | 색인코퍼스 A | ✅ 결과에 쓰임 | 132,521×512 CLIP+1000질의. filtered-ANN 코퍼스A(§7.1)·색인3축 Pareto(§7.3)·pgvector b3_frames(§7.2·§7.5). **tri-source 아님(predicate-only, recall-only GT)** |
| **meva_kf1** | 638M | 외적타당성(검색+저장) | ✅ 결과에 쓰임 | 저장단위 P1(§7.5, 985클립)·B0–B5 검색 외적검증(§6). fit-2, 헤드라인 아님 |
| **miris_traffic** | 2.0M | 외적타당성(색인·배포) | ✅ 결과에 쓰임 | 59,019 CLIP프레임→pgvector miris_frames→P2/P3 교차검증(§7.5). tri-source 아님 |
| **vru_accident** | 265M | 붕괴데모(§4)+답변(§8) | ✅ 결과에 쓰임 | v1순환→수리 collapse(§4)·답변 증거사다리(§8). tri-source 아님(facet_source=parsed_vqa, A9 축소감사) |
| **uca_anchor (UCA)** | 176M | 외적타당성(검색) | ✅ 결과에 쓰임 | 135질의 B0–B5, 영어 이상행동 외적검증(§6, 사전등록 3/4). **2.5-채널**(센서 없음) |
| **aihub_intelligent_cctv** | 85M | 붕괴데모+이식성 | ✅ 결과에 쓰임 | v1순환(269클립 완벽지표)→수리 collapse(§4). A9 3-어서션 감사(full A6 아님), facet_source 100% label_json |
| **aihub_multi_angle_cctv** | 426M | 답변계층(다시점) | ✅ 결과에 쓰임 | 400-event bbox-비대칭 stratum→4 VLM 다시점 답변선택(§8.1). label 템플릿 캡션, qrels_semantic 없음 |
| **cityflow_nl** | 4.2M | (의도됐으나) **미사용** | ⚠️ 구축만 | annotation-only staging. **다운스트림 소비자 0, 프레임 0장 추출, qrels_semantic·A6 없음** |
| **aihub_abnormal_cctv** | 71M | (의도됐으나) **미사용·고아** | ⚠️ 미사용 | FAISS B0–B5 결과가 디스크에 실재하나 **v3가 안 씀(역할이 UCA로 재배정)**. tri-source 아님(label_xml 단일채널) |

**요약**: 확보 10종 중 **8종 실사용, 2종(cityflow_nl·abnormal_cctv) 미사용**. 완전 tri-source(full A6)는 **522 단독**; UCA는 2.5-채널; VRU·intelligent는 붕괴데모(설계상 순환→수리); 나머지는 색인코퍼스/외적타당성/답변계층.

## 2. 워크로드 동작 방식 (비순환 tri-source, 522)

```
raw 프레임 + CVAT 라벨(TL_3/4) + 센서 CSV(TL_1/2)
  → facets: sensor_facets.parquet(predicate) / annotation_video_facets.parquet(relevance)
            + Qwen2.5-VL 픽셀-only 캡션(document)
  → canonical_trisource_expanded/ : clips 3,000 / documents 3,000 / metadata 27,000
       queries 85(low 75 + contrast 10) / qrels(strict) 6,810 / qrels_semantic 24,873
  → A6_trisource_audit.json overall_pass=true (6/6: 필터키=센서 / relevance=주석 / 둘 disjoint /
       metadata에 relevance 無 / 세 producer 분리 / document 토큰누출 0)
  → bge-m3 임베딩(document+query) → run_retrieval_baselines(B0–B5)
```
- **세 채널**: PREDICATE=센서(time_of_day/hour/sig_has_yellow/sig_has_pedestrian/veh_density_bin) ⟂ RELEVANCE=사람주석 희소 scene(parked 2.3%/dense 2.2%/multi_bus 8.2%/bike 11.5%/stopped 21.2%) ⟂ DOCUMENT=Qwen2.5-VL 캡션.
- **이중 정답**: strict(필터∧의미) / semantic(의미만). semantic positive의 72.6%가 필터를 실패 → soft-intent에서 prefilter가 관련문서 제거 가능(비보장성 실측).
- 설계시 독립성: 30쌍 중 25쌍 V<0.3, global max 0.454(trisource_independence.json, 47,098 비디오).

## 3. 저장·검색·색인 비교 구조 (축 × 데이터셋 × 결과파일)

| 축 | 무엇을 비교 | 데이터셋(역할) | 결과파일(실재) |
|---|---|---|---|
| §6 검색 B0–B5 | metadata/BM25/vector/postfilter/**prefilter**/hybrid × strict·semantic × 결합도 | 522(헤드라인)·MEVA·UCA·VRU·intelligent·abnormal(순환데모) | results/trisource_expanded_b0_b5/{metrics_summary,metrics_semantic,significance_expanded,t3_coupling_curve}.csv |
| §4 붕괴 | v1순환 완벽지표 → 수리 붕괴 | VRU·intelligent | paper_assets/20260710_noncircular_collapse/* |
| §7.1 filtered-ANN | prefilter/postfilter/single-stage vs **동일선택도 무작위마스크 대조** | 코퍼스A(sinnaedoro 132K)·코퍼스B(522-visual 143K) | paper_assets/20260710_pillarB/filtered_ann_real_{A,B}.csv, P1_predicates_*.csv |
| §7.2 엔진 | pgvector·Milvus·Weaviate 네이티브 필터드 | sinnaedoro(b3_frames 실 Postgres)·코퍼스B | paper_assets/20260710_pillarB/pgvector_*.csv + 엔진 bench |
| §7.3 색인 3축 | Flat/IVF-Flat/HNSW/IVF-PQ × 스케일(1만→1M) Pareto | sinnaedoro corpus_real 132K + 1M aug + 522-visual B 143K | index_benchmark.csv/.parquet, fig_index_structure_pareto |
| §7.5 P1 저장단위 | clip-caption/frame-vector/multi-vector/dual | 522·MEVA | processed/{522,meva}/…/results/storage_unit/*.csv |
| §7.5 P2/P3 부분색인·hot/cold | global+WHERE vs partial index; N* 손익분기 | sinnaedoro b3_frames 132K·**MIRIS miris_frames 59K**(교차검증) | paper_assets/20260713_db_design/{pgvector_partial_vs_global,pgvector_partial_vs_global_miris,hotcold_policy,hotcold_miris_policy}.csv |
| §8 답변계층 | 고정 VLM에 증거 구성만 변경(검색과 분리) | VRU(증거사다리)·multi_angle(다시점)·522(지각벽 143K) | paper_assets 답변 assets, gmanip_gate.json |

## 4. 정직한 플래그 (감사 적발)

1. **cityflow_nl = 미사용**(구축만, 프레임 0장, 소비자 0). abnormal_cctv = **미사용·고아**(결과 실재하나 v3가 안 씀, 역할이 UCA로 재배정). → 논문에 등장 안 함이 맞으며, 저장 정리 대상 후보.
2. **완전 tri-source는 522 단독** — UCA는 2.5채널(센서 없음), VRU·intelligent는 붕괴데모(설계상 순환→수리, A9 축소감사), multi_angle·abnormal은 label 단일채널. 즉 "비순환 헤드라인"의 rigor는 522 1종에 의존(기존 알려진 최대 caveat, 원고 명시).
3. **stale 산출물**: sinnaedoro `filtered_ann/filtered_ann.csv`는 구(舊) 무작위마스크(실측은 paper_assets/20260710_pillarB로 대체). VRU 259M v1 결과트리(visual/fusion)는 v3 미소비. intelligent 84M 다수 미소비.
4. **원고 경로 정밀도(내가 삽입한 §7.5)**: MEVA 저장단위 원자산은 `processed/meva_kf1/…/results/storage_unit/`이고 pgvector P2/P3는 `paper_assets/20260713_db_design/` — §7.5 문장이 둘을 묶어 표기했으나 MEVA 특정 자산 위치를 더 정확히 분리 표기하면 좋음(경미).
5. **exec-doc 700 초기 수치 stale**: MEVA 1443클립/202질의는 캡션 전(前) 수치, 최종 on-disk는 985클립/193질의(700 하단에 SUPERSEDED로 정정됨).
6. **522 질의 3변형 존재**: 헤드라인=canonical_trisource_expanded(85q, 5×5 교차곱), 원본 canonical_trisource(32q, 손선별)는 §L144에서 selection-bias 자기교정으로 공개, canonical(15q)은 붕괴용 수리 v1.

**총평**: 저장·검색·색인 비교의 핵심 축은 전부 실측 결과파일로 뒷받침되며, 데이터셋→축 매핑이 교차검증에서 일치. 유일한 실질 미사용은 cityflow_nl·abnormal_cctv 2종(정리 후보), 유일한 구조적 caveat는 완전 tri-source 522 단독 의존(원고 명시).
