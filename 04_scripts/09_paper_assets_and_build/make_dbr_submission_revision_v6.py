#!/usr/bin/env python3
"""Build the DBR v6 review-submission revision.

The v5 working master is intentionally page-unlimited.  This builder selects
its submission-level evidence, keeps the official type sizes, replaces all six
figures, and removes internal appendices so the review file can be checked
against the DBR A4/20-page contract.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm

import _dbr_complete_working_draft_base as v4


ROOT = Path(__file__).resolve().parents[3]
V4_BUILD_BODY = v4.build_body
V4_POLISH_DOCX = v4.polish_docx
KIISE = ROOT / "2026_KIISE"
M = KIISE / "manuscript"
VISUALS = KIISE / "paper_assets" / "20260717_manuscript_visuals_v6"
JOINT = KIISE / "paper_assets" / "20260717_joint_image_caption_validation"
JOINT_CONTROLS = KIISE / "paper_assets" / "20260717_joint_image_caption_controls"
LEGACY_JOINT = KIISE / "paper_assets" / "20260717_joint_optimization_validation"
CROSSCHECK = KIISE / "paper_assets" / "20260717_ablation_agent_crosscheck"
CIRCULARITY = CROSSCHECK / "qwen_aligned_circularity"
HIGH_RECALL = CROSSCHECK / "qwen2048_high_recall_5seed"
MEVA_CONTROL = LEGACY_JOINT / "meva_same_encoder_control"

OUT_MD = M / "kiise_dbr_manuscript_v6_submission_revision.md"
OUT_DOCX = M / "kiise_dbr_manuscript_v6_submission_revision.docx"
OUT_PDF = M / "kiise_dbr_manuscript_v6_submission_revision.pdf"
BUILD_SUPPORT = KIISE / "paper_assets" / "20260718_manuscript_build_support"
REF_DOCX = BUILD_SUPPORT / "dbr_reference_v6_submission.docx"
AUTHOR_JSON = BUILD_SUPPORT / "dbr_author_info.json"


def table_block(text: str, number: int) -> str:
    """Return one complete Markdown table, including its caption."""
    pattern = re.compile(
        rf"(?m)^\*\*표\s+{number}(?:\.|\s)[^\n]*\*\*\n\n(?:^\|.*\n)+"
    )
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise RuntimeError(f"expected one table {number}, got {len(matches)}")
    return matches[0].rstrip()


def section(text: str, start: str, end: str) -> str:
    a = text.index(start)
    b = text.index(end, a)
    return text[a:b].rstrip()


def select_one(frame: pd.DataFrame, **conditions: object) -> pd.Series:
    mask = pd.Series(True, index=frame.index)
    for column, value in conditions.items():
        mask &= frame[column].astype(str) == str(value)
    selected = frame[mask]
    if len(selected) != 1:
        raise RuntimeError(f"expected one row for {conditions}, got {len(selected)}")
    return selected.iloc[0]


def fig(number: int, stem: str, caption: str, width: str) -> str:
    path = f"2026_KIISE/paper_assets/20260717_manuscript_visuals_v6/{stem}.png"
    return f"![그림 {number}. {caption}]({path}){{width={width}}}"


def protocol_section() -> str:
    return f"""## 3. 비순환 워크로드 프로토콜

필터드 검색 워크로드를 질의 Q, 문서 D, predicate P와 정답 R로 표시한다. 본 연구는 다음 세 경로를 순환성으로 정의한다. C1은 필터 키가 정답 정의 키에 포함되어 정답 집합이 항상 필터 부분집합 안에 놓이는 경우다. 이때 strict 채점의 prefilter 우위는 데이터와 무관한 항진명제가 된다. C2는 R을 정의한 라벨을 D가 재진술하여 검색을 장면 이해가 아닌 라벨 조회로 환원하는 경우이고, C3은 질의가 같은 라벨 템플릿에서 생성되는 경우다.

이를 차단하기 위해 predicate는 카메라 10의 센서 기록, relevance는 카메라 11/22의 사람 주석, document는 센서·주석에 접근하지 못한 픽셀-only VLM 캡션에서 생산한다(그림 1). A6 감사는 필터·정답 키의 소스 화이트리스트와 교집합 공집합, metadata의 정답 필드 부재, 문서의 정답·facet 토큰 누출 0건, 희소 정답 밀도를 매 빌드에서 확인한다. 이 원칙은 저장 표현, 검색 계획, 물리 색인과 최종 답변을 같은 평가 계보 위에서 비교하게 한다.

{fig(1, "fig1_pipeline_noncircular_v6", "비순환 evidence-layer 파이프라인. 독립 소스에서 워크로드를 구성하고 A6 감사를 통과한 뒤 저장 표현·검색 계획·색인과 답변 계층을 평가한다. 점선은 순환성만 되주입하는 C1/C2 통제 실험이다.", "5.5in")}

동일 실행을 두 사용자 계약으로 채점한다. strict 정답은 의미 조건과 predicate를 모두 만족하는 문서이고, semantic 정답은 predicate와 무관하게 의미 조건만 만족하는 문서다. 따라서 strict에서 필터는 hard constraint이지만 semantic에서는 관련 문서를 제거할 수 있다. 522의 qrels는 strict 6,809행, semantic 24,872행이며 의미 양성의 72.6%가 predicate 밖에 있다.

predicate–relevance 결합도는 질의 표집 전 모집단의 Cramér's V로 계산한다. V<0.3과 V≥0.3을 각각 저결합·자연결합으로 사전 구분하되, V는 방향이 없는 쌍 수준 속성이므로 효과 부호는 Δ(B4-B2)에서 읽고 구간 추정은 쌍 군집을 존중한다. 이중 정답, 결합도 스펙트럼과 A6를 함께 사용함으로써 “필터가 항상 이긴다”는 구성상 보장을 제거한다."""


def circularity_section(t2: str) -> str:
    summary = pd.read_csv(CIRCULARITY / "summary.csv")
    contrasts = pd.read_csv(CIRCULARITY / "contrasts.csv")
    clean = select_one(
        summary, experiment="C1", condition="qwen_clean", scoring="semantic"
    )
    random_filter = select_one(
        summary,
        experiment="C1",
        condition="random_same_selectivity_mean",
        scoring="semantic",
    )
    oracle = select_one(
        summary, experiment="C1", condition="oracle_qrel_filter", scoring="semantic"
    )
    contaminated = select_one(
        summary,
        experiment="C2",
        condition="qwen_full_contamination",
        scoring="semantic",
    )
    c1 = select_one(
        contrasts,
        experiment="C1",
        scoring="semantic",
        treatment="oracle_qrel_filter",
        control="qwen_clean",
    )
    c2 = select_one(
        contrasts,
        experiment="C2",
        scoring="semantic",
        treatment="qwen_full_contamination",
        control="qwen_clean",
    )
    return f"""## 4. 순환성 진단과 통제 주입

초기 VRU·지능형 CCTV 워크로드는 VQA 정답에서 역파싱한 facet을 metadata, 질의와 qrels에 재사용하고 같은 라벨의 재진술 문서를 색인했다. 따라서 C1–C3가 동시에 성립했다. 캡션-only 문서, 독립 운영 facet, 의미축 정답과 이중 qrels로 수리하자 완벽 지표가 현실 수준으로 붕괴했다(표 2). VRU semantic의 질의별 B4-B2 부호가 음수 18/동률 34/양수 33으로 바뀐 점은 필터 우위 보장이 실제로 해제됐음을 보인다. 다만 수리 과정에서 정답 정의도 바뀌었으므로 과거 하락분 전체를 순환성에 산술 귀속하지 않는다.

{t2}

이 식별 한계를 보완하기 위해 522의 문서 3,000개, 질의 85개, qrels와 Qwen3-VL-Embedding-2B 2,048차원 공간을 고정하고 순환 요소 하나만 주입했다. C1에서 clean B2 semantic은 {clean.ndcg_at_10:.3f}, 같은 선택도의 무작위 필터 평균은 {random_filter.ndcg_at_10:.3f}였으나 qrel-oracle 필터는 {oracle.ndcg_at_10:.3f}이었다(Δ={c1.mean_delta:+.3f}; 질의 95% CI [{c1.query_ci_lo:+.3f}, {c1.query_ci_hi:+.3f}], 25개 군집 CI [{c1.cluster_ci_lo:+.3f}, {c1.cluster_ci_hi:+.3f}]). C2에서 정답 의미 라벨을 문서에 재진술하자 {clean.ndcg_at_10:.3f}에서 {contaminated.ndcg_at_10:.3f}으로 상승했다(Δ={c2.mean_delta:+.3f}; 질의 CI [{c2.query_ci_lo:+.3f}, {c2.query_ci_hi:+.3f}], 군집 CI [{c2.cluster_ci_lo:+.3f}, {c2.cluster_ci_hi:+.3f}]). 입력 hash·주입 문장·랭킹·bootstrap을 독립 재계산한 10/10 gate도 통과했다.

{fig(2, "fig2_circularity_integrated_v6", "순환성의 진단과 직접 개입. (a) 수리 전후 전략별 붕괴, (b) 동일-Qwen 공간의 clean·동일선택도 무작위·C1·C2 점수, (c) clean 대비 효과와 질의/군집 bootstrap 95% CI.", "5.5in")}

수리 전후 비교와 동일조건 개입은 서로 다른 질문에 답한다. 전자는 실제 개발 과정에서 오염 노출에 따라 붕괴가 층화됨을 보이고, 후자는 다른 조건을 고정해 순환 경로만으로 지표가 크게 상승할 수 있음을 직접 식별한다. 이 결과는 모든 벤치마크의 효과 크기가 같다는 보편 주장이 아니라, 구조 비교 전에 계보 감사를 수행해야 한다는 방법론적 근거다."""


def dataset_section(t3: str, t4: str) -> str:
    return f"""## 5. 데이터셋과 워크로드

### 5.1 헤드라인 tri-source 522

본 연구는 AI Hub 교차로 데이터 중 조인과 주석이 모두 존재하는 영상 클립에서 3,000개를 층화 표집하고, 각 클립의 중간 프레임 한 장을 Qwen2.5-VL-7B 모델에 입력하여 영상 설명문(클립 캡션)을 생성했다. 질의는 메타데이터 조건 필드 5종(시간대, 시각, 황색 신호, 보행 신호, 센서 교통 밀도)과 의미 정의 5종(주차 차량, 개체 20개 이상, 버스 2대 이상, 정차 차량, 이륜차 2대 이상)의 전체 교차 조합에 최소 양성 규칙을 적용하여 총 85개(저결합 75개, 자연결합 10개)를 구축했다. 

검색 결과는 사용 목적에 따라 엄격한 정답(strict)과 의미론적 정답(semantic)의 두 평가 계약으로 채점한다. 표 3은 한 질의에서 strict와 semantic 판정이 갈라지는 실제 기록을 보여준다.

{t3}

### 5.2 수리·외부 워크로드와 색인 코퍼스

VRU 1,000클립과 지능형 CCTV 269클립은 순환성 수리 사례 및 답변 실험에 사용한다. UCA는 6,432 세그먼트·135질의의 2.5-channel 외부 대조로, 독립 센서 채널이 없어 완전 tri-source로 부르지 않는다. 물리 색인 실험은 시내도로 132,521×512와 522 프레임 143,830×512를 사용하며 관련도 대신 동일 predicate의 exact top-10 대비 recall@10을 측정한다. P1 등록표는 실측 natural/composite predicate를 결과 전에 고정하고, 같은 선택도의 무작위 mask를 짝 대조군으로 생성한다.

{t4}

### 5.3 계측과 통계

검색은 고정 환경의 단일 스레드 실행으로 워밍업 뒤 반복 15회의 질의별 중앙값을 집계한다. 다른 계측 경계의 절대 latency는 비교하지 않으며 보고 비용은 캡션 생성이 아닌 검색·색인 계층으로 제한한다. 관련도 지표는 nDCG@10·MRR·recall@10, ANN은 exact-neighbor recall@10을 사용한다. 질의 또는 사전 정의 군집 bootstrap 95% CI, 사전등록 가족의 Holm 보정, 다중 사후 대조의 BH 보정을 구분한다. 모든 핵심 비교는 질의 수, 군집 수, 효과와 CI를 함께 보고한다."""


def filtered_index_section(t7: str, t8: str, t9: str, t10: str, t11: str) -> str:
    storage = pd.read_csv(JOINT / "same_encoder_storage_control.csv")
    paired = pd.read_csv(JOINT / "paired_bootstrap_comparisons.csv")
    joint_controls = pd.read_csv(JOINT_CONTROLS / "paired_bootstrap_comparisons.csv")
    high = pd.read_csv(HIGH_RECALL / "summary.csv")
    meva = pd.read_csv(MEVA_CONTROL / "paired_bootstrap.csv")

    labels = {
        "caption": "caption",
        "representative_frame": "representative frame",
        "joint_image_caption": "image+caption joint",
        "multi_frame": "multi-frame",
        "dual": "dual (RRF 포함)",
    }
    storage_rows = []
    for representation, label in labels.items():
        strict = select_one(storage, representation=representation, scoring="strict")
        semantic = select_one(storage, representation=representation, scoring="semantic")
        if representation == "caption":
            effect = "기준"
        else:
            contrast = select_one(
                paired,
                family="storage",
                scoring="semantic",
                candidate=f"{representation}__B2_vector__flat",
                baseline="caption__B2_vector__flat",
            )
            effect = (
                f"{contrast.mean_delta:+.3f} "
                f"[{contrast.cluster_ci_lo:+.3f}, {contrast.cluster_ci_hi:+.3f}]"
            )
        storage_rows.append(
            "| "
            + " | ".join(
                [
                    label,
                    f"{strict.ndcg_at_10:.3f} / {semantic.ndcg_at_10:.3f}",
                    effect,
                    f"{semantic.latency_p50_ms:.2f} / {semantic.vector_payload_mb:.1f}",
                ]
            )
            + " |"
        )
    t12 = """**표 12. 동일-Qwen B2+Flat 저장 표현 ablation (n=85; Δ와 95% CI는 caption 대비 25개 질의군집 bootstrap)**

| 저장 표현 | strict / semantic nDCG@10 | semantic Δ [군집 CI] | p50(ms) / payload(MB) |
|---|---:|---:|---:|
""" + "\n".join(storage_rows)

    multi_sem = select_one(
        paired,
        family="storage",
        scoring="semantic",
        candidate="multi_frame__B2_vector__flat",
        baseline="caption__B2_vector__flat",
    )
    joint_sem = select_one(
        paired,
        family="storage",
        scoring="semantic",
        candidate="joint_image_caption__B2_vector__flat",
        baseline="caption__B2_vector__flat",
    )
    joint_shuffle_sem = select_one(
        joint_controls,
        candidate="joint_matched",
        baseline="joint_shuffled",
        scoring="semantic",
    )
    b4_strict = select_one(
        paired,
        family="search",
        scoring="strict",
        candidate="multi_frame__B4_prefilter__flat",
        baseline="multi_frame__B2_vector__flat",
    )
    b4_sem = select_one(
        paired,
        family="search",
        scoring="semantic",
        candidate="multi_frame__B4_prefilter__flat",
        baseline="multi_frame__B2_vector__flat",
    )
    h512 = select_one(high, structure="hnsw", efSearch="512.0")
    ivf256 = select_one(high, structure="ivfflat", nprobe="256.0")
    meva_frame = select_one(
        meva,
        family="storage",
        scoring="semantic",
        candidate="frame__B2_vector__flat",
    )

    t10 = t10.replace(
        "'전선'은 (p95, 재현율) 2축 지배 판정으로 그림 6와 동일 — 전체 46구성 중 전선 12",
        "'전선'은 (p95, 재현율) 2축 지배 판정 — 전체 46구성 중 12개",
    )
    t11 = """**표 11. 캡션 생성 모델별 B2 semantic nDCG@10과 Qwen2.5-VL 대비 변화**

| 데이터 | Qwen2.5-VL | Qwen3-VL: 점수, Δ [95% CI] | Qwen3.5: 점수, Δ [95% CI] |
|---|---:|---:|---:|
| 522 | 0.1700 | 0.2419, +0.0719 [0.0288, 0.1164] | **0.2722, +0.1022 [0.0348, 0.1706]** |
| MEVA | 0.1029 | **0.4541, +0.3513 [0.3024, 0.4003]** | 0.2710, +0.1681 [0.1441, 0.1932] |
| UCA | 0.2504 | 0.2190, -0.0314 [-0.0587, -0.0037] | **0.3044, +0.0540 [0.0151, 0.0920]** |"""

    return f"""## 7. 실험 2 — filtered-ANN, 저장 표현과 물리 색인

### 7.1 실측 predicate 대 동일선택도 무작위 mask

시내도로 A와 522 프레임 B에서 부분집합 Flat/HNSW, 전역 HNSW postfilter와 IVF selector를 비교했다. 같은 선택도라도 실측 predicate의 통과 벡터는 임베딩 공간에 군집하므로 무작위 mask보다 전역 순위 깊은 곳에 놓였다. 그 결과 무작위 mask는 postfilter·IVF recall을 최대 +0.63 과대평가했지만 부분집합 색인은 차이가 거의 없었다(표 7). 확증 가족의 prefilter-postfilter 격차는 A 저·중선택도와 B 중·고선택도에서 Holm 유의했다.

{v4.WIDE_START}

{t7}

{fig(5, "fig5_real_vs_random_v6", "실측 predicate와 동일선택도 무작위 mask 비교. (a) 방법별 실측 recall@10, (b) 무작위-실측 짝 차이와 bootstrap 95% CI.", "5.5in")}

{v4.WIDE_END}

결손은 질의별 exact 이웃의 전역 중앙순위와 양의 상관을 보였다(A ρ=0.699/0.780, B 0.616/0.895). K'를 4배로 늘려도 실측 recall은 A 0.306, B 0.667에 머문 반면 무작위 대조는 0.917/0.956에 도달했다. 즉 문제는 선택도만이 아니라 predicate와 표현 공간의 군집 구조다. 핫 predicate는 부분집합 HNSW, 콜드는 지역 Flat, 재구축할 수 없으면 bitmap selector가 안전한 기본값이다.

### 7.2 관계형·전용 엔진 교차 확인

pgvector HNSW의 사후 WHERE는 선택적·군집형 predicate에서 short result를 만들었다. relaxed iterative scan은 약결합 hour를 0.984–0.994까지 회복했으나 위치 predicate는 0.302–0.658에 머물고 p50 19.0–29.5ms를 지불했다(표 8). Milvus와 Weaviate는 각각 높은 filtered-out 비율의 brute-force 전환과 40K 미만 flat fallback으로 이를 완화한다. 완화 밖 그래프 체제에서는 같은 방향의 작은 잔여 결손이 남았고, ACORN은 통과 노드의 군집을 이용해 부호가 역전되는 경향을 보였다(표 9). 따라서 무작위 mask만으로 엔진을 평가하면 naive 계획은 낙관, 구조 인지 완화는 비관으로 왜곡될 수 있다.

{v4.WIDE_START}

{t8}

{t9}

### 7.3 색인 3축

두 실 코퍼스의 비필터 Flat·HNSW·IVF-Flat·IVF-PQ 그리드에서 recall, p50/p95, 구축 시간과 크기를 동시에 측정했다. 131K/142K에서 HNSW ef64는 recall 0.997/0.9992, p50 0.041/0.047ms로 Flat보다 약 300배 빨랐다. IVF-PQ는 22–35배 작지만 recall 0.33–0.49였다. HNSW의 지연 이득은 메모리 7–13%와 구축 35–47초로, PQ의 공간 이득은 큰 recall 손실로 지불된다(표 10).

{t10}

{v4.WIDE_END}

### 7.4 그래프 계열의 음성 결과

A6-KG는 센서 predicate 엣지와 픽셀-only 캡션 개체 엣지만 허용하고 정답 주석 엣지를 0건으로 강제했다. 이 조건에서 KG의 신호는 B0/B4 metadata와 B1/B2 caption의 재조합으로 환원됐다. 캡션 개체는 부정문을 포함해 거의 전 문서를 연결했고 리프트 중앙값은 0.002였다. entity-overlap KG의 strict nDCG@10은 0.176으로 B0 0.218을 넘지 못했다. 이는 “KG가 불필요하다”는 보편 결론이 아니라, 본 캡션 워크로드에서 새 품질 축을 제공하지 못한 경계 결과다.

### 7.5 부분 색인·배포와 혼합-encoder 기준선

pgvector 부분 색인은 선택도 0.011에서도 recall 0.98–0.99와 p50 0.41–0.42ms를 유지했지만 predicate별 0.4–39초 구축과 3.8–258MB를 요구했다. 배포 규칙은 global recall<0.95이거나 예상 질의 수가 N*=1000×build_s/latency_gain_ms를 넘으면 지역/부분 색인을 만들고, 아니면 global+postfilter를 쓰는 것이다. 이 경향은 MIRIS 59,019 프레임에서도 재현됐다. 기존 caption(BGE-M3) 대 frame(CLIP) 비교는 표현과 encoder가 섞인 설계 기준선이므로 순수 저장 주효과로 해석하지 않는다.

### 7.6 캡션 생성기 ablation

Qwen2.5-VL, Qwen3-VL과 Qwen3.5의 동일 프레임·프롬프트·110-token 상한·BGE-M3 검색기를 고정하고 문서만 바꿨다. 9/9 캡션 무결성·A6 감사와 모든 paired 비교를 통과했다. Qwen3.5는 세 데이터 모두 기준선을 개선했지만, Qwen3-VL은 UCA에서 하락했다(표 11). 이는 캡셔너가 DB 물질화 변수임을 보이되 다른 프롬프트·예산의 보편 우위를 뜻하지 않는다. UCA token 상한 도달률(Qwen3 85.52%, Qwen3.5 54.04%)은 최신 모델도 절단을 자동 해결하지 않음을 보인다.

{v4.WIDE_START}

{t11}

### 7.7 동일-encoder 저장×검색×색인 공동 ablation

522의 3,000 clips·85 queries·qrels를 유지하고 caption, representative frame, 단일 image+caption joint, multi-frame과 dual을 모두 Qwen3-VL-Embedding-2B 2,048차원 공간에 정렬했다. Joint는 대표 프레임과 같은 clip의 Qwen3.5 캡션을 한 멀티모달 입력으로 인코딩한 클립당 단일 벡터다. 호환 가능한 저장 5종×검색 계획×색인 7종의 112개 구성, 19,040 metric cells와 95,200 latency trials을 실행했다. 완전 요인설계가 아니며 기존 네 표현의 핵심 대조는 결과 후 정리한 사후 우선 비교이고, joint arm은 결과를 보기 전 별도 프로토콜 amendment로 동결했다.

{t12}

동일한 단일 이천사십팔 차원의 벡터 예산에서 [결합 표현](joint)의 의미론적 [누적 정규화 할인 이득](nDCG@10)은 [캡션 표현](caption)보다 {joint_sem.mean_delta:+.3f} 높았으나 군집 신뢰구간 [{joint_sem.cluster_ci_lo:+.3f}부터 {joint_sem.cluster_ci_hi:+.3f}까지]은 영을 포함했다. 또한 매칭되거나 뒤섞인 결합 표현 간의 차이인 {joint_shuffle_sem.mean_delta:+.3f}의 군집 신뢰구간 [{joint_shuffle_sem.cluster_ci_lo:+.3f}부터 {joint_shuffle_sem.cluster_ci_hi:+.3f}까지]도 영을 포함하므로 이미지와 캡션 간의 정확한 정렬이 성능 향상의 원인이라고 주장하지 않는다. 결합 표현은 캡션이나 프레임 표현보다 높은 점수 추정치와 동일한 [전송량](payload)을 제공하지만, 다중 프레임이나 이중 색인 방식에 비해서는 품질이 낮고 공간과 지연 시간은 더 작게 소요되는 중간적 운용점이라 할 수 있다. [다중 프레임 캡션](multi-frame caption)의 의미론적 델타 값은 {multi_sem.mean_delta:+.3f}이고 군집 신뢰구간 [{multi_sem.cluster_ci_lo:+.3f}부터 {multi_sem.cluster_ci_hi:+.3f}까지]을 나타내었으나 저장 방식 제품군 군집의 [벤자미니 호흐베르크](Benjamini-Hochberg) 유의 확률 큐 값은 {multi_sem.q_cluster_bh:.3f}로 영점영오를 넘었다. 동일한 다중 프레임과 [플랫](Flat) 구조 결합에서 사전 필터 기반 검색과 벡터 단독 검색 방식의 차이는 엄격한 채점 기준에서는 {b4_strict.mean_delta:+.3f}의 차이를 보였고 의미론적 채점 기준에서는 {b4_sem.mean_delta:+.3f}의 차이를 보여 평가 기준에 따라 방향이 다르게 갈렸다. 따라서 저장 표현과 검색 계획의 선택은 목적 함수에 깊이 의존한다.

{fig(6, "fig6_joint_tradeoff_seed_v6", "공동 설계공간과 색인 강건성. (a,b) 112개 호환 구성의 semantic/strict 품질-지연 분포, (c) 143,830 Qwen 벡터의 5-seed recall@10과 p95.", "5.5in")}

{v4.WIDE_END}

별도의 십사만 삼천팔백삼십 개의 실제 [큐웬](Qwen) 벡터와 다섯 개의 무작위 초깃값 환경에서 [계층형 탐색 가능 소세계](HNSW) 탐색 크기를 오백십이로 설정했을 때 평균 재현율은 {h512.recall_mean:.6f}이고 최소 재현율은 {h512.recall_min:.6f}이며 중앙값 구십오 백분위수 지연 시간은 {h512.latency_p95_median_ms:.3f} 밀리초였다. 아울러 [역색인 파일 플랫](IVF-Flat) 구조의 탐색 버킷 수를 이백오십육으로 설정한 경우도 최소 재현율은 {ivf256.recall_min:.6f}이었으나 구십오 백분위수 지연 시간은 {ivf256.latency_p95_median_ms:.3f} 밀리초였다. [미바](MEVA) 데이터셋의 단일 프레임 캡션 효과는 {meva_frame.mean_delta:+.3f}이고 군집 신뢰구간 [{meva_frame.cluster_ci_lo:+.3f}부터 {meva_frame.cluster_ci_hi:+.3f}까지]을 보여 불확실하였으므로 다중 프레임 방식의 효과가 외부에서 재현된 것으로 보기 어렵다. 결론적으로 전역적인 단일 우승 구조는 존재하지 않으며, 엄격하거나 의미론적인 목적과 지연 시간과 저장 공간에 대한 [서비스 수준 계약](Service Level Agreement)별 [파레토](Pareto) 선택을 수행해야 한다."""


def answer_section(t12: str, t13: str) -> str:
    t13_new = re.sub(r"\*\*표 13(?:\.|\s)", "**표 14. ", t13, count=1)
    t12_new = re.sub(r"\*\*표 12(?:\.|\s)", "**표 13. ", t12, count=1)
    return f"""## 8. 실험 3 — 최종 VLM-QA 전파

### 8.1 증거 품질과 시점 선택

VRU 600문항의 고정 생성기에서 closed-book, BM25, dense, hybrid, oracle 증거 사다리를 비교했다. 검색 증거는 답변 정확도를 Qwen 0.3083에서 0.6650, Llama 0.2300에서 0.6800으로 높였고 oracle은 0.7467/0.6900이었다(표 13). 따라서 좋은 증거는 답변에 유효하지만 검색 nDCG의 모든 차이가 자동 전파된다는 뜻은 아니다. 다중 카메라 실험에서도 무작위 뷰보다 최적 뷰 선택이 일관되게 유리해 evidence packet이 클립 ID뿐 아니라 시점·프레임 선택을 포함해야 함을 보였다.

{v4.PAGE_BREAK}

{v4.WIDE_START}

{t12_new}

### 8.2 색인 근사의 전파 경계

전파 실험은 사전 게이트로 불필요한 생성 호출을 막았다. 1K 캡션에서 27개 색인 구성의 상대 evidence-recall@3가 0.974–1.053에 갇혀 조작이 성립하지 않았다. 143K 프레임에서는 moment-recall@3가 0.120에서 0.056으로 하락했지만 360호출 파일럿의 적중-비적중 답변 차이는 -0.020(약 ±0.13)으로 지각 지렛대가 없었다. 강한 생성기 프로브는 well-posed 질문에서 오라클 0.72로 지각 벽을 일부 해제했으나 이진 질문은 yes-bias에 오염됐다.

{t13_new}

{v4.WIDE_END}

색인→답변 효과가 관측되려면 색인 파라미터가 실제 증거 회수를 바꾸고, 생성기가 그 시각 차이를 인식하며, 질문·답변 분포가 편향되지 않아야 한다. 본 실험은 검색·색인 절충을 end-to-end 답변 품질로 확대 해석할 수 없다는 음성 결과를 남긴다."""


def discussion_section(t14: str) -> str:
    t15 = re.sub(r"\*\*표 14(?:\.|\s)", "**표 15. ", t14, count=1)
    old_row = (
        "| 저장 단위 선택(3축) | 캡션-질의 정합 시 clip-caption, 아니면 frame-vector; multi·dual 회피 | "
        "522 clip-caption Pareto(0.169·12.3MB·0.59ms), MEVA frame 지배(0.161 대 0.103·2.0 대 4.0MB), "
        "multi 지연 6–7× | 실측 | 7.5절 |"
    )
    new_row = (
        "| 저장 단위 선택 | strict/semantic·지연·공간별 Pareto에서 선택 | 동일-Qwen B2+Flat semantic "
        "caption 0.181, joint 0.218, multi 0.352; joint는 단일 벡터 24.6MB, multi는 68.4MB | "
        "joint 결과 전 amendment·나머지 사후 우선 비교 | 7.7절 |"
    )
    if old_row not in t15:
        raise RuntimeError("table 15 storage row not found")
    t15 = t15.replace(old_row, new_row, 1)
    t15 = t15.replace("표 14", "표 15")
    return f"""## 9. 논의

결과는 네 선택 규칙으로 요약된다. 첫째, hard predicate에서는 prefilter를 우선하되 soft intent에서는 semantic 손실과 결합도를 함께 본다. 둘째, 실제 predicate 분포를 동일선택도 무작위 mask로 대체하지 말고, 반복되는 선택적 조건은 부분/지역 색인으로 상각한다. 셋째, 저장·검색·색인은 한 축씩 고립된 승자를 고르지 말고 호환 구성의 목적·SLA별 Pareto에서 선택한다. 넷째, 검색 개선을 VLM 답변 개선으로 간주하지 말고 증거 회수·지각·과제 편향 게이트를 별도로 검증한다(표 15).

{t15}

수치 신뢰성은 원자산 재집계로 확인했다. 기존 검증 스위트는 40/40과 원고 수치 164/164를 통과했다. 보강 실험에서는 기존 joint 32/32, 신규 단일 image+caption 17/17, treatment/statistics 12/12, 순환성 10/10, 5-seed ANN 8/8을 통과했다. 독립 읽기 전용 감사도 치명적 오류는 없으나 외적 타당성·사전등록 지위를 제한해야 한다는 데 일치했다. 이 검산은 산출물 무결성을 보증할 뿐 보편성을 대신하지 않는다."""


def replace_section_figures(text: str) -> str:
    text = re.sub(
        r"!\[그림 3\.[^\n]*\]\([^)]+\)\{width=[^}]+\}",
        fig(
            3,
            "fig3_coupling_inference_v6",
            "522 결합도 분석. (a) predicate-relevance V와 semantic B4-B2, (b) 결합도 밴드별 평균 효과와 pair-cluster 95% CI. 군집 CI가 0을 포함하므로 탐색적으로 해석한다.",
            "3.0in",
        ),
        text,
        count=1,
    )
    text = re.sub(
        r"!\[그림 4\.[^\n]*\]\([^)]+\)\{width=[^}]+\}",
        fig(
            4,
            "fig4_uca_external_v6",
            "UCA 외부 대조. (a) B0-B5 strict/semantic nDCG@10, (b) 사전 고정 대조의 B4-B2 효과와 pair bootstrap 95% CI. 네 대조 중 세 방향이 일치했다.",
            "5.0in",
        ),
        text,
        count=1,
    )
    return text


def wrap_wide_blocks(text: str) -> str:
    table_pat = re.compile(
        r"(?m)(^\*\*표\s+\d+[^\n]*\*\*\n\n(?:^\|.*\n)+)"
    )
    wide_tables = {1, 2, 3, 4, 15}

    def table_repl(match: re.Match[str]) -> str:
        block = match.group(1)
        hit = re.search(r"\*\*표\s+(\d+)", block)
        number = int(hit.group(1)) if hit else -1
        if number not in wide_tables:
            return block
        if number == 15:
            # Keep the discussion, limitations, and conclusion in the same
            # one-column section so a split table does not leave a blank page
            # remainder. Return to two columns immediately before references.
            return f"{v4.FINAL_WIDE_START}\n\n{block}\n"
        return f"{v4.WIDE_START}\n\n{block}\n{v4.WIDE_END}\n"

    text = table_pat.sub(table_repl, text)
    fig_pat = re.compile(
        r"(?m)(^!\[그림\s+\d+[^\n]*\]\([^\n]+\)(?:\{[^\n]+\})?\n)"
    )

    def fig_repl(match: re.Match[str]) -> str:
        block = match.group(1)
        hit = re.search(r"그림\s+(\d+)", block)
        number = int(hit.group(1)) if hit else -1
        if number in {1, 2}:
            # LibreOffice can retain the XObject but clip an inline full-width
            # image to zero height when a continuous section starts too close
            # to the page bottom. Starting these key figures on a fresh page
            # makes the DOCX and exported PDF agree and prevents silent loss.
            return (
                f"{v4.PAGE_BREAK}\n\n{v4.WIDE_START}\n\n"
                f"{block}\n{v4.WIDE_END}\n"
            )
        return block

    text = fig_pat.sub(fig_repl, text)
    return text


def build_body() -> str:
    original_wrap = v4.wrap_wide_blocks
    try:
        v4.wrap_wide_blocks = lambda text: text
        source = V4_BUILD_BODY()
    finally:
        v4.wrap_wide_blocks = original_wrap

    prefix = source[: source.index("## 3. 비순환 워크로드 프로토콜")].rstrip()
    prefix = prefix.replace("호환 가능한 91개 구성", "호환 가능한 112개 구성")
    prefix = prefix.replace("jointly evaluate 91 compatible", "jointly evaluate 112 compatible")
    prefix = prefix.replace(
        "clip-caption, frame-vector, multi-vector 또는 dual-index",
        "clip-caption, frame-vector, 단일 image+caption joint, multi-vector 또는 dual-index",
    )
    prefix = prefix.replace(
        "clip-caption, frame-vector, multi-vector와 dual-index 구성은",
        "clip-caption, frame-vector, 단일 image+caption joint, multi-vector와 dual-index 구성은",
    )
    prefix = prefix.replace(
        "증거 표현×검색 계획×ANN 색인 91개 구성을",
        "증거 표현×검색 계획×ANN 색인 112개 구성을",
    )
    sec6 = section(
        source,
        "## 6. 실험 1 — 검색 전략과 결합도 스펙트럼",
        "## 7. 실험 2 — 실측 predicate 하의 filtered-ANN과 색인 3축",
    )
    sec6 = replace_section_figures(sec6)
    compact_t5 = """**표 5. tri-source B4-B2, semantic 채점 (nDCG@10)**

| 표본 | Δ [95% CI] |
|---|---:|
| 최초 32질의 | -0.0745 [-0.136, -0.014] |
| 확장 53질의 | +0.0197 [-0.008, +0.050] |
| 통합 85질의 | -0.0158 [-0.047, +0.015] |
| 저결합 V<0.3 (n=75) | -0.0357 [-0.065, -0.008] |
| 자연결합 V≥0.3 (n=10) | +0.1335 [+0.017, +0.249] |"""
    sec6 = sec6.replace(
        table_block(source, 5),
        f"{v4.WIDE_START}\n\n{compact_t5}",
        1,
    )
    t6 = table_block(source, 6)
    sec6 = sec6.replace(t6, f"{t6}\n\n{v4.WIDE_END}", 1)
    sec10 = section(source, "## 10. 한계와 향후 연구", "## 11. 결론")
    sec11 = section(source, "## 11. 결론", "## 참고문헌")
    references = section(source, "## 참고문헌", "## 부록 A. 재현성")

    t = {number: table_block(source, number) for number in range(1, 15)}
    body = "\n\n".join(
        [
            prefix,
            protocol_section(),
            circularity_section(t[2]),
            dataset_section(t[3], t[4]),
            sec6,
            filtered_index_section(t[7], t[8], t[9], t[10], t[11]),
            answer_section(t[12], t[13]),
            discussion_section(t[14]),
            sec10,
            sec11.replace(
                "RQ1은 3–4절, RQ2는 7.5–7.6절, RQ3–RQ4는 6절, "
                "RQ5는 7.1–7.5절, RQ6은 8절",
                "RQ1은 3–4절, RQ2는 7.5–7.7절, RQ3–RQ4는 6절, "
                "RQ5는 7.1–7.7절, RQ6은 8절",
            ),
            references,
        ]
    )
    body = renumber_references_by_first_appearance(body.strip() + "\n")
    # Table 1 lives in the retained introduction and remains untouched.
    return wrap_wide_blocks(body)


def renumber_references_by_first_appearance(text: str) -> str:
    """Rebuild the reference list in first-citation order.

    The build source keeps stable internal reference identifiers so that
    sections can be assembled independently.  The submission manuscript must
    instead number references by their first appearance in the final body.
    """
    marker = "\n## 참고문헌\n"
    if text.count(marker) != 1:
        raise RuntimeError("expected exactly one reference section")
    body, reference_text = text.split(marker, 1)

    entries: dict[int, str] = {}
    for match in re.finditer(r"(?m)^\[(\d+)\]\s+(.+)$", reference_text):
        old_number = int(match.group(1))
        entry = match.group(2).strip()
        if old_number in entries and entries[old_number] != entry:
            raise RuntimeError(f"conflicting duplicate reference [{old_number}]")
        entries[old_number] = entry

    citation_pattern = re.compile(r"\[([0-9]+(?:\s*,\s*[0-9]+)*)\]")
    first_appearance: list[int] = []
    for match in citation_pattern.finditer(body):
        for value in re.split(r"\s*,\s*", match.group(1)):
            old_number = int(value)
            if old_number not in first_appearance:
                first_appearance.append(old_number)

    missing = [number for number in first_appearance if number not in entries]
    if missing:
        raise RuntimeError(f"citations without reference entries: {missing}")

    mapping = {
        old_number: new_number
        for new_number, old_number in enumerate(first_appearance, start=1)
    }

    def replace_citation(match: re.Match[str]) -> str:
        old_numbers = [
            int(value) for value in re.split(r"\s*,\s*", match.group(1))
        ]
        new_numbers = sorted(mapping[number] for number in old_numbers)
        return "[" + ",".join(str(number) for number in new_numbers) + "]"

    body = citation_pattern.sub(replace_citation, body)
    references = "\n\n".join(
        f"[{mapping[old_number]}] {entries[old_number]}"
        for old_number in first_appearance
    )
    return body.rstrip() + "\n\n## 참고문헌\n\n" + references + "\n"


def set_table_widths_cm(table, widths_cm: list[float]) -> None:
    """Set an explicit fixed-width grid that LibreOffice also preserves."""
    if len(table.columns) != len(widths_cm):
        raise RuntimeError(
            f"table width profile has {len(widths_cm)} values for "
            f"{len(table.columns)} columns"
        )
    table.autofit = False
    table.allow_autofit = False
    grid_cols = list(table._tbl.tblGrid.gridCol_lst)
    if len(grid_cols) != len(widths_cm):
        raise RuntimeError(
            f"table grid has {len(grid_cols)} columns, expected {len(widths_cm)}"
        )
    for grid_col, width_cm in zip(grid_cols, widths_cm):
        grid_col.set(qn("w:w"), str(round(width_cm * 567)))
    for row in table.rows:
        for cell, width_cm in zip(row.cells, widths_cm):
            cell.width = Cm(width_cm)
            tc_pr = cell._tc.get_or_add_tcPr()
            tc_w = tc_pr.find(qn("w:tcW"))
            if tc_w is None:
                tc_w = OxmlElement("w:tcW")
                tc_pr.append(tc_w)
            tc_w.set(qn("w:w"), str(round(width_cm * 567)))
            tc_w.set(qn("w:type"), "dxa")


def polish_docx_v6() -> None:
    """Apply the common DBR typography, then v6-specific result-table widths."""
    V4_POLISH_DOCX()
    doc = Document(OUT_DOCX)
    # The first DOCX table contains author information; result table numbers
    # therefore match their indices.  Table 15 needs a deliberate grid because
    # automatic width inference otherwise collapses its short final column.
    if len(doc.tables) != 16:
        raise RuntimeError(f"expected author table + 15 result tables, got {len(doc.tables)}")
    set_table_widths_cm(doc.tables[15], [2.8, 4.1, 6.4, 2.2, 1.8])
    doc.save(OUT_DOCX)


def validate_assets() -> None:
    expected = [
        "fig1_pipeline_noncircular_v6.png",
        "fig2_circularity_integrated_v6.png",
        "fig3_coupling_inference_v6.png",
        "fig4_uca_external_v6.png",
        "fig5_real_vs_random_v6.png",
        "fig6_joint_tradeoff_seed_v6.png",
    ]
    missing = [name for name in expected if not (VISUALS / name).is_file()]
    if missing:
        raise RuntimeError(f"missing v6 visual assets: {missing}")


def main() -> None:
    validate_assets()
    BUILD_SUPPORT.mkdir(parents=True, exist_ok=True)
    v4.OUT_MD = OUT_MD
    v4.OUT_DOCX = OUT_DOCX
    v4.OUT_PDF = OUT_PDF
    v4.REF_DOCX = REF_DOCX
    v4.AUTHOR_JSON = AUTHOR_JSON
    v4.DOC_FONT_KR = "NanumMyeongjo"
    v4.DOC_FONT_LATIN = "Liberation Serif"
    v4.build_body = build_body
    v4.polish_docx = polish_docx_v6
    v4.main()


if __name__ == "__main__":
    main()
