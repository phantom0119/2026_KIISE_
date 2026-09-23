#!/usr/bin/env python3
"""Build the page-unlimited, two-column DBR research working draft.

This working master deliberately retains the full procedural prose that the
20-page v4 review manuscript compresses. It also adds an auditable registry of
all datasets and experiment tracks, detailed caption-model results, controlled
circularity interventions, a same-encoder joint ablation, the operational
evidence-layer model, and a reusable claim-evidence bank. Generated tables read
the validated result artifacts directly; the v3/v4 text remains the historical
editorial base rather than the sole numerical source of truth.
"""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd
from docx.shared import Cm

import _dbr_complete_working_draft_base as v4


ROOT = Path(__file__).resolve().parents[3]
KIISE = ROOT / "2026_KIISE"
M = KIISE / "manuscript"
ASSET = KIISE / "paper_assets" / "20260715_caption_model_ablation"
JOINT = KIISE / "paper_assets" / "20260717_joint_optimization_validation"
CROSSCHECK = KIISE / "paper_assets" / "20260717_ablation_agent_crosscheck"
CIRCULARITY = CROSSCHECK / "qwen_aligned_circularity"
HIGH_RECALL = CROSSCHECK / "qwen2048_high_recall_5seed"
MEVA_CONTROL = JOINT / "meva_same_encoder_control"
V4_BUILD_BODY = v4.build_body

OUT_MD = M / "kiise_dbr_manuscript_v5_complete_research_working_draft.md"
OUT_DOCX = M / "kiise_dbr_manuscript_v5_complete_research_working_draft.docx"
OUT_PDF = M / "kiise_dbr_manuscript_v5_complete_research_working_draft.pdf"
REF_DOCX = M / "dbr_reference_v5_complete_working.docx"


# These four replacements exist solely to compress the submission manuscript.
# The working master retains the original v3 paragraphs in full.
COMPRESSION_PREFIXES = (
    "구축을 요약한다:",
    "게이트·중단의 판정 세부는",
    "심사자 재현 절차는",
    "이상의 한계를 타당성 위협의 네 범주",
)


def configure_section(section) -> None:
    """A4 research-working layout: readable margins, no page target."""
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)
    section.header_distance = Cm(0.9)
    section.footer_distance = Cm(0.9)


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def clean(value: object) -> str:
        if value is None:
            return "—"
        return str(value).replace("|", "\\|").replace("\n", " ")

    lines = ["| " + " | ".join(map(clean, headers)) + " |"]
    lines.append("|" + "|".join(["---"] * len(headers)) + "|")
    lines.extend("| " + " | ".join(clean(v) for v in row) + " |" for row in rows)
    return "\n".join(lines)


def select_one(frame: pd.DataFrame, **conditions: object) -> pd.Series:
    mask = pd.Series(True, index=frame.index)
    for column, value in conditions.items():
        mask &= frame[column].astype(str) == str(value)
    selected = frame[mask]
    if len(selected) != 1:
        raise RuntimeError(f"expected one row for {conditions}, got {len(selected)}")
    return selected.iloc[0]


def circularity_injection_section() -> str:
    summary = pd.read_csv(CIRCULARITY / "summary.csv")
    contrasts = pd.read_csv(CIRCULARITY / "contrasts.csv")

    clean = select_one(
        summary, experiment="C1", condition="qwen_clean", scoring="semantic"
    )
    oracle = select_one(
        summary, experiment="C1", condition="oracle_qrel_filter", scoring="semantic"
    )
    random_filter = select_one(
        summary,
        experiment="C1",
        condition="random_same_selectivity_mean",
        scoring="semantic",
    )
    c1 = select_one(
        contrasts,
        experiment="C1",
        scoring="semantic",
        treatment="oracle_qrel_filter",
        control="qwen_clean",
    )
    contaminated = select_one(
        summary,
        experiment="C2",
        condition="qwen_full_contamination",
        scoring="semantic",
    )
    c2 = select_one(
        contrasts,
        experiment="C2",
        scoring="semantic",
        treatment="qwen_full_contamination",
        control="qwen_clean",
    )

    return f"""### 4.1 동일 조건 통제 주입: 순환 경로만 바꾸면 지표가 포화된다

표 2의 수리 전후 비교는 질의와 정답 정의도 함께 바뀌므로, 관측 하락 전체를 순환성에 귀속할 수 없다. 이 식별 한계를 보완하기 위해 522의 3,000개 문서, 85개 질의, strict/semantic qrels와 Qwen3-VL-Embedding-2B 2,048차원 공간을 고정하고 순환 요소 하나만 주입했다. clean 문서·오염 문서·질의는 한 모델 세션에서 다시 임베딩하고 float32 L2 정규화를 동일하게 적용했다.

**C1 필터 순환성.** clean B2 semantic nDCG@10은 {clean.ndcg_at_10:.6f}이지만, 질의의 semantic qrel 집합을 후보 필터로 쓰는 oracle 처치는 {oracle.ndcg_at_10:.6f}으로 상승했다(Δ {c1.mean_delta:+.6f}; 질의 95% CI [{c1.query_ci_lo:+.6f}, {c1.query_ci_hi:+.6f}], 25개 질의군집 CI [{c1.cluster_ci_lo:+.6f}, {c1.cluster_ci_hi:+.6f}]). 반면 qrel을 보지 않고 후보 수만 맞춘 무작위 필터의 평균은 {random_filter.ndcg_at_10:.6f}이었다. 따라서 상승은 단순 후보 축소가 아니라 정답 집합을 후보 생성에 되먹임한 결과다.

**C2 문서 순환성.** 각 문서에 해당 클립의 정답 의미 라벨만 재진술한 1,367개 label-edge를 주입하자 semantic nDCG@10은 {clean.ndcg_at_10:.6f}에서 {contaminated.ndcg_at_10:.6f}으로 상승했다(Δ {c2.mean_delta:+.6f}; 질의 CI [{c2.query_ci_lo:+.6f}, {c2.query_ci_hi:+.6f}], 군집 CI [{c2.cluster_ci_lo:+.6f}, {c2.cluster_ci_hi:+.6f}]). 문서와 질의의 token truncation은 0건이었다.

별도 구현은 입력 hash, 주입 문장, 임베딩, 랭킹, 지표, bootstrap과 clean anchor를 독립 재계산해 10/10 gate를 통과했다. 이 개입은 **순환 경로가 측정치를 인위적으로 크게 부풀릴 수 있음**을 같은 Qwen 주 실험 공간에서 직접 보인다. 다만 과거 시스템의 성능 차이 전체가 순환성 때문이었다는 산술적 귀속이나, 모든 데이터셋에서 같은 효과 크기가 나온다는 일반화는 하지 않는다.
"""


def joint_ablation_section() -> str:
    storage = pd.read_csv(JOINT / "same_encoder_storage_control.csv")
    paired = pd.read_csv(JOINT / "paired_bootstrap_comparisons.csv")
    configs = pd.read_csv(JOINT / "configuration_summary.csv")
    fidelity = pd.read_csv(JOINT / "task_fidelity_corrected.csv")
    high = pd.read_csv(HIGH_RECALL / "summary.csv")
    meva = pd.read_csv(MEVA_CONTROL / "summary.csv")
    meva_paired = pd.read_csv(MEVA_CONTROL / "paired_bootstrap.csv")

    def storage_score(representation: str, scoring: str) -> float:
        return float(
            select_one(storage, representation=representation, scoring=scoring).ndcg_at_10
        )

    multi_sem = select_one(
        paired,
        family="storage",
        scoring="semantic",
        candidate="multi_frame__B2_vector__flat",
        baseline="caption__B2_vector__flat",
    )
    multi_strict = select_one(
        paired,
        family="storage",
        scoring="strict",
        candidate="multi_frame__B2_vector__flat",
        baseline="caption__B2_vector__flat",
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
    hnsw = select_one(
        configs,
        config="multi_frame__B4_prefilter__hnsw_ef64",
        scoring="strict",
    )
    hnsw_fidelity = select_one(
        fidelity, config="multi_frame__B4_prefilter__hnsw_ef64"
    )
    h512 = select_one(high, structure="hnsw", efSearch="512.0")
    ivf256 = select_one(high, structure="ivfflat", nprobe="256.0")
    meva_frame = select_one(
        meva_paired,
        family="storage",
        scoring="semantic",
        candidate="frame__B2_vector__flat",
    )
    meva_dual = select_one(
        meva_paired,
        family="storage",
        scoring="semantic",
        candidate="dual__B2_vector__flat",
    )

    return f"""### 7.7 동일 encoder 저장×검색×색인 공동 ablation

기존 7.5절의 저장 단위 비교는 caption에 BGE-M3, frame에 CLIP을 사용해 표현과 encoder 효과가 섞여 있었다. 이를 분리하기 위해 522의 동일 3,000 clips·85 queries·qrels를 유지하고 query, caption, representative frame과 143,830 frames를 모두 Qwen3-VL-Embedding-2B 2,048차원 공간에 정렬했다. 저장 표현 4종(caption, representative-frame, multi-frame max-sim, caption+multi-frame RRF), 호환 검색 계획(B2/B3/B4 및 caption B5), 색인 7종(Flat, HNSW 2, IVF-Flat 2, IVF-PQ 2)의 **호환 가능한 91개 구성**을 전부 실행했다. 비호환 cell을 억지로 채우지 않았으므로 완전 요인설계는 아니며, 결과 관측 뒤 정리한 핵심 비교는 “사후 우선 비교”이지 사전등록 확증 가족이 아니다.

**저장 주효과.** B2+Flat에서 semantic nDCG@10은 caption {storage_score("caption", "semantic"):.4f}, representative frame {storage_score("representative_frame", "semantic"):.4f}, multi-frame {storage_score("multi_frame", "semantic"):.4f}, dual {storage_score("dual", "semantic"):.4f}이었다(strict는 각각 {storage_score("caption", "strict"):.4f}, {storage_score("representative_frame", "strict"):.4f}, {storage_score("multi_frame", "strict"):.4f}, {storage_score("dual", "strict"):.4f}). Multi-frame−caption은 semantic Δ {multi_sem.mean_delta:+.4f}(질의 CI [{multi_sem.query_ci_lo:+.4f}, {multi_sem.query_ci_hi:+.4f}], 군집 CI [{multi_sem.cluster_ci_lo:+.4f}, {multi_sem.cluster_ci_hi:+.4f}]), strict Δ {multi_strict.mean_delta:+.4f}(질의 CI [{multi_strict.query_ci_lo:+.4f}, {multi_strict.query_ci_hi:+.4f}])의 큰 양의 점추정치를 보였다. 그러나 세 storage 대조를 한 가족으로 보정한 군집 BH q는 semantic {multi_sem.q_cluster_bh:.4f}, strict {multi_strict.q_cluster_bh:.4f}로 0.05를 넘는다. 따라서 이를 family-wise 유의한 일반 법칙으로 부르지 않고 522 내부의 강한 후보 신호로 보고한다. Dual은 저장 표현과 RRF 융합을 함께 바꾸므로 순수 storage 주효과가 아니다.

**검색 목적함수 상호작용.** Multi-frame에서 Flat B4는 B2 대비 strict를 {b4_strict.mean_delta:+.4f}(군집 CI [{b4_strict.cluster_ci_lo:+.4f}, {b4_strict.cluster_ci_hi:+.4f}]) 높였지만 semantic은 {b4_sem.mean_delta:+.4f}(군집 CI [{b4_sem.cluster_ci_lo:+.4f}, {b4_sem.cluster_ci_hi:+.4f}]) 낮췄다. 즉 같은 저장·색인에서도 hard constraint 충족과 scene-semantic 회수는 서로 다른 목적함수이며, 하나의 nDCG 승자를 “최적 검색 방식”으로 선언할 수 없다.

**색인과 규모.** 3,000-clip task 격자에서 multi-frame+B4+HNSW ef64의 strict 점추정치는 {hnsw.ndcg_at_10:.4f}로 Flat보다 높았지만 exact-result overlap은 {hnsw_fidelity.task_recall_to_exact_at_10:.4f}여서 통계적으로 검증된 승자로 채택하지 않았다. 별도의 143,830 real Qwen-2048 vector, 85-query, 5-seed 재구축에서는 HNSW M32/ef512가 평균 recall@10 {h512.recall_mean:.6f}, 최소 {h512.recall_min:.6f}, median p95 {h512.latency_p95_median_ms:.3f} ms로 5/5 seed에서 0.99를 넘었다. IVF-Flat nprobe256도 최소 {ivf256.recall_min:.6f}으로 gate를 통과했지만 median p95는 {ivf256.latency_p95_median_ms:.3f} ms였다. 이는 관측 범위의 exact-neighbor fidelity·지연 결과이며, 대규모 task qrels 품질이나 다른 데이터의 0.99를 보장하지 않는다.

**외부 same-encoder 대조.** 한 frame/clip만 제공되는 MEVA 985 clips·193 queries·57 clusters에서는 frame−caption semantic Δ가 {meva_frame.mean_delta:+.4f}, 군집 CI [{meva_frame.cluster_ci_lo:+.4f}, {meva_frame.cluster_ci_hi:+.4f}], BH q={meva_frame.q_cluster_bh:.4f}로 불확실했다. Dual−caption은 {meva_dual.mean_delta:+.4f}, 군집 CI [{meva_dual.cluster_ci_lo:+.4f}, {meva_dual.cluster_ci_hi:+.4f}]였으나 RRF 결합효과를 포함한다. MEVA는 encoder 격리와 도메인 경계를 점검하지만 multi-frame 외부 재현은 아니다.

결론은 단일 전역 최적 조합이 아니라 **목적·SLA별 Pareto 선택**이다. 522에서는 multi-frame이 품질 후보지만 저장량과 지연이 커지고, hard constraint에서는 B4가 strict를 높이는 대신 semantic을 낮추며, 높은 ANN fidelity는 search strength와 지연을 교환한다. 전체 수치와 주장 gate는 부록 I에 둔다.
"""


def latest_validation_appendix() -> str:
    storage = pd.read_csv(JOINT / "same_encoder_storage_control.csv")
    paired = pd.read_csv(JOINT / "paired_bootstrap_comparisons.csv")
    circular = pd.read_csv(CIRCULARITY / "summary.csv")
    circular_delta = pd.read_csv(CIRCULARITY / "contrasts.csv")
    high = pd.read_csv(HIGH_RECALL / "summary.csv")
    meva_paired = pd.read_csv(MEVA_CONTROL / "paired_bootstrap.csv")

    storage_rows: list[list[object]] = []
    label = {
        "caption": "caption",
        "representative_frame": "representative frame",
        "multi_frame": "multi-frame",
        "dual": "dual(RRF 포함)",
    }
    for representation in label:
        strict = select_one(storage, representation=representation, scoring="strict")
        semantic = select_one(storage, representation=representation, scoring="semantic")
        storage_rows.append(
            [
                label[representation],
                f"{strict.ndcg_at_10:.4f}",
                f"{semantic.ndcg_at_10:.4f}",
                f"{semantic.latency_p50_ms:.3f}",
                f"{semantic.vector_payload_mb:.1f}",
            ]
        )

    clean = select_one(
        circular, experiment="C1", condition="qwen_clean", scoring="semantic"
    )
    c1_value = select_one(
        circular,
        experiment="C1",
        condition="oracle_qrel_filter",
        scoring="semantic",
    )
    c2_value = select_one(
        circular,
        experiment="C2",
        condition="qwen_full_contamination",
        scoring="semantic",
    )
    c1_delta = select_one(
        circular_delta,
        experiment="C1",
        scoring="semantic",
        treatment="oracle_qrel_filter",
        control="qwen_clean",
    )
    c2_delta = select_one(
        circular_delta,
        experiment="C2",
        scoring="semantic",
        treatment="qwen_full_contamination",
        control="qwen_clean",
    )
    circular_rows = [
        [
            "C1 qrel-oracle filter",
            f"{clean.ndcg_at_10:.6f}",
            f"{c1_value.ndcg_at_10:.6f}",
            f"{c1_delta.mean_delta:+.6f}",
            f"[{c1_delta.query_ci_lo:+.6f}, {c1_delta.query_ci_hi:+.6f}]",
            f"[{c1_delta.cluster_ci_lo:+.6f}, {c1_delta.cluster_ci_hi:+.6f}]",
        ],
        [
            "C2 label-restating document",
            f"{clean.ndcg_at_10:.6f}",
            f"{c2_value.ndcg_at_10:.6f}",
            f"{c2_delta.mean_delta:+.6f}",
            f"[{c2_delta.query_ci_lo:+.6f}, {c2_delta.query_ci_hi:+.6f}]",
            f"[{c2_delta.cluster_ci_lo:+.6f}, {c2_delta.cluster_ci_hi:+.6f}]",
        ],
    ]

    multi_sem = select_one(
        paired,
        family="storage",
        scoring="semantic",
        candidate="multi_frame__B2_vector__flat",
    )
    meva_frame = select_one(
        meva_paired,
        family="storage",
        scoring="semantic",
        candidate="frame__B2_vector__flat",
    )
    h512 = select_one(high, structure="hnsw", efSearch="512.0")
    ivf256 = select_one(high, structure="ivfflat", nprobe="256.0")
    highlight_rows = [
        [
            "522 storage",
            "multi-frame−caption semantic",
            f"{multi_sem.mean_delta:+.4f}",
            f"[{multi_sem.cluster_ci_lo:+.4f}, {multi_sem.cluster_ci_hi:+.4f}]",
            f"cluster BH q={multi_sem.q_cluster_bh:.4f}; 522 후보 신호",
        ],
        [
            "MEVA storage",
            "one-frame−caption semantic",
            f"{meva_frame.mean_delta:+.4f}",
            f"[{meva_frame.cluster_ci_lo:+.4f}, {meva_frame.cluster_ci_hi:+.4f}]",
            f"cluster BH q={meva_frame.q_cluster_bh:.4f}; 불확실",
        ],
        [
            "143,830-vector index",
            "HNSW M32/ef512",
            f"mean {h512.recall_mean:.6f}",
            f"min {h512.recall_min:.6f}",
            f"5/5≥0.99; median p95 {h512.latency_p95_median_ms:.3f} ms",
        ],
        [
            "143,830-vector index",
            "IVF-Flat nprobe256",
            f"mean {ivf256.recall_mean:.6f}",
            f"min {ivf256.recall_min:.6f}",
            f"5/5≥0.99; median p95 {ivf256.latency_p95_median_ms:.3f} ms",
        ],
    ]

    metric_gate = pd.read_json(JOINT / "independent_verification.json", typ="series")
    treatment_gate = pd.read_json(
        CROSSCHECK / "treatment_integrity_verification.json", typ="series"
    )
    circular_gate = pd.read_json(
        CIRCULARITY / "independent_verification.json", typ="series"
    )
    high_gate = pd.read_json(
        HIGH_RECALL / "independent_verification.json", typ="series"
    )
    gate_rows = [
        [
            "Joint metric·artifact",
            f"{metric_gate.passed}/{metric_gate.total} PASS",
            "지표 산술, ranking/vector/hash/seed 무결성",
        ],
        [
            "Ablation treatment·statistics",
            f"{treatment_gate.passed}/{treatment_gate.total} PASS",
            "91-cell treatment, qrel 논리, latency 반복, delta/BH",
        ],
        [
            "Qwen-aligned circularity",
            f"{circular_gate.passed}/{circular_gate.total} PASS",
            "주입 문서, embedding, ranking, bootstrap, clean anchor",
        ],
        [
            "High-recall 5-seed",
            f"{high_gate.passed}/{high_gate.total} PASS",
            "30-cell grid, seed, monotonicity, threshold, prior anchor",
        ],
        [
            "agy·Claude 읽기 전용 감사",
            "각 PASS_WITH_LIMITATIONS",
            "치명 오류 없음; family-wise·외적 일반화·사후 명세 경계 일치",
        ],
    ]

    claim_rows = [
        [
            "순환 경로는 측정치를 부풀릴 수 있다",
            "Qwen C1/C2 단일요소 개입 + BGE 반복",
            "직접 개입·강건성",
            "과거 차이 전체를 순환성에 귀속 금지",
        ],
        [
            "동일 encoder에서 표현 효과가 달라진다",
            "522 B2+Flat storage 4종",
            "사후 우선 비교",
            "multi-frame 보편 우위·family-wise 0.05 주장 금지",
        ],
        [
            "필터 가치는 정답 계약에 의존한다",
            "B4−B2 strict/semantic, 522·MEVA",
            "통제 비교",
            "prefilter 항상 최적 금지",
        ],
        [
            "색인은 SLA별 선택해야 한다",
            "91-config Pareto + 143,830-vector 5-seed",
            "실측·exact fidelity",
            "대규모 task 품질·모든 구축 0.99 보장 금지",
        ],
        [
            "외부 데이터에서 경계가 달라진다",
            "MEVA same-encoder one-frame",
            "외적 통제",
            "multi-frame 외부 재현으로 호칭 금지",
        ],
        [
            "검산 결과가 산출물과 일치한다",
            "32/32 + 12/12 + 10/10 + 8/8, 이중 감사",
            "무결성·비판 감사",
            "외적 타당성·인과적 운반 가능성 보증으로 확대 금지",
        ],
    ]

    return f"""## 부록 I. 최신 ablation·통제 주입·검증 gate

이 부록은 2026-07-17에 완료한 보강 실험을 원시 결과에서 직접 재집계한다. 공동 ablation 프로토콜은 결과 관측 뒤 정리한 사후 통합 명세이며, 기존 Amendment 1–6a와 같은 사전등록 확증 실험으로 호칭하지 않는다.

**표 24. Qwen-aligned 순환성 통제 주입 (semantic nDCG@10)**

{markdown_table(['처치', 'clean', 'treatment', 'Δ', 'query 95% CI', 'cluster 95% CI'], circular_rows)}

**표 25. 동일 Qwen/B2/Flat 저장 표현 통제 (522, 85 queries)**

{markdown_table(['표현', 'strict nDCG@10', 'semantic nDCG@10', 'p50 ms', 'vector MB'], storage_rows)}

**표 26. 외부·규모 보강의 핵심 판정**

{markdown_table(['범위', '대조/구성', '점추정', '군집 CI 또는 최소값', '판정 경계'], highlight_rows)}

**검산 범위.** “PASS”는 각 검산기가 명시한 대상만 보증한다. 특히 32/32는 전체 pipeline이나 bootstrap을 독립 재실행했다는 뜻이 아니며, 별도 12/12 gate가 treatment와 통계를 보완한다.

{markdown_table(['검증층', '결과', '보장 범위'], gate_rows)}

**표 27. 최신 주장–증거–금지 경계**

{markdown_table(['허용 주장', '직접 증거', '지위', '금지 확대'], claim_rows)}

두 독립 감사자는 모두 치명적 설계 오류가 없다고 판정했으나 최종 상태를 PASS_WITH_LIMITATIONS로 두었다. 남은 공백은 외부 multi-frame 재현, 대규모 task qrels, 24시간 적재·갱신과 별도 사전등록 holdout이다. 이는 현재 내부 비교를 무효화하지 않지만 “보편적으로 최적”, “외부 데이터에서 일반 증명”, “대규모 task 품질 보장”을 주장하지 못하게 하는 실질적 경계다.
"""


def caption_detail_appendix() -> str:
    metrics = pd.read_csv(ASSET / "retrieval_metrics_all_models.csv")
    deltas = pd.read_csv(ASSET / "paired_model_deltas.csv")
    stats = pd.read_csv(ASSET / "caption_generation_stats.csv")

    model_label = {
        "qwen25vl_7b": "Qwen2.5-VL-7B",
        "qwen3vl_8b": "Qwen3-VL-8B",
        "qwen35_9b": "Qwen3.5-9B",
    }
    dataset_label = {"522": "522", "meva": "MEVA", "uca": "UCA"}
    strategy_label = {
        "B2_vector_only": "B2 vector-only",
        "B4_prefilter_vector": "B4 prefilter-vector",
        "B5_hybrid": "B5 hybrid",
    }

    main = metrics[
        metrics["strategy"].isin(strategy_label)
        & metrics["scoring"].isin(["strict", "semantic"])
    ].copy()
    rows: list[list[object]] = []
    for dataset in ["522", "meva", "uca"]:
        for model in ["qwen25vl_7b", "qwen3vl_8b", "qwen35_9b"]:
            row: list[object] = [dataset_label[dataset], model_label[model]]
            for scoring in ["strict", "semantic"]:
                for strategy in strategy_label:
                    hit = main[
                        (main.dataset.astype(str) == dataset)
                        & (main.model == model)
                        & (main.scoring == scoring)
                        & (main.strategy == strategy)
                    ]
                    row.append(f"{hit.iloc[0].ndcg_at_10:.4f}")
            rows.append(row)

    b2 = deltas[
        (deltas.strategy == "B2_vector_only")
        & (deltas.scoring == "semantic")
    ]
    delta_rows: list[list[object]] = []
    for candidate in ["qwen3vl_8b", "qwen35_9b"]:
        for dataset in ["522", "meva", "uca"]:
            hit = b2[
                (b2.candidate == candidate)
                & (b2.dataset.astype(str) == dataset)
            ].iloc[0]
            delta_rows.append(
                [
                    model_label[candidate],
                    dataset_label[dataset],
                    int(hit.queries),
                    f"{hit.mean_delta_ndcg10:+.4f}",
                    f"[{hit.ci_lo:+.4f}, {hit.ci_hi:+.4f}]",
                    f"{int(hit.wins)}/{int(hit.ties)}/{int(hit.losses)}",
                ]
            )

    stat_rows: list[list[object]] = []
    denominators = {"522": 3000, "meva": 985, "uca": 6432}
    for _, row in stats.iterrows():
        dataset = str(row.dataset)
        denom = denominators[dataset]
        hit_rate = 100.0 * int(row.token_limit_hit_count) / denom
        latency = "기준선 이관" if pd.isna(row.latency_ms_p50) else f"{row.latency_ms_p50:.0f}"
        stat_rows.append(
            [
                dataset_label[dataset],
                model_label[row.model],
                f"{row.word_count_mean:.1f}",
                f"{row.word_count_p95:.0f}",
                f"{int(row.token_limit_hit_count)}/{denom} ({hit_rate:.2f}%)",
                f"{100.0 * row.exact_duplicate_rate:.2f}%",
                int(row.machine_leak_count),
                latency,
            ]
        )

    return f"""## 부록 F. 캡션 생성기 ablation 전체 결과

본문 7.6절은 사전 고정 주 추정량만 제시한다. 이 부록은 동일 프레임·프롬프트·생성 예산과 동일 BGE-M3 검색기를 유지한 3 데이터셋 × 3 모델의 주 검색 전략 전체를 제공한다. B0 metadata-only는 모델 간 완전히 동일했고, 9/9 캡션 무결성·9/9 A6 감사와 36/36 주 paired 비교가 통과했다. 생성 지연은 GPU 열 상태와 병렬 실행 경합을 포함하므로 품질 우위의 근거가 아니다.

**표 19. 캡션 생성 모델별 B2·B4·B5 nDCG@10 전체표**

{markdown_table(['데이터', '캡셔너', 'strict B2', 'strict B4', 'strict B5', 'semantic B2', 'semantic B4', 'semantic B5'], rows)}

**표 20. Qwen2.5-VL 대비 B2 semantic paired 차이**

{markdown_table(['후보', '데이터', '질의', '평균 Δ', 'paired bootstrap 95% CI', '승/동/패'], delta_rows)}

**표 21. 캡션 길이·절단·무결성·생성 관측**

{markdown_table(['데이터', '캡셔너', '평균 단어', 'p95 단어', '110-token 상한 도달', '완전중복률', '기계라벨 누출', '생성 p50 ms'], stat_rows)}

Qwen3.5-9B는 고정 프롬프트·생성 예산으로 평가한 세 데이터셋의 B2 semantic을 모두 유의하게 개선해 사전 판정 규칙상 **본 실험 범위의 일관 개선** 조건을 충족했다. 이는 일반 VLM 우월성이나 다른 데이터·프롬프트·예산에 대한 보편 우위를 뜻하지 않는다. Qwen3-VL-8B는 522·MEVA에서는 향상했지만 UCA에서는 유의하게 하락했다. 또한 후속 모델의 UCA 상한 도달률이 높아, 더 최신 모델이 장문·절단 문제를 자동으로 해결하지 않음을 보인다. 캡셔너 선택은 clip-caption 표현의 물질화 비용·품질을 함께 바꾸는 DB 설계 변수다.
"""


PIPELINE_APPENDIX = """## 부록 D. 전체 파이프라인·용어·운영 경계

### D.1 사용자가 질의를 입력하는 위치

“VLM 앞단”은 VLM 자체가 원본 아카이브를 검색창처럼 직접 읽는다는 뜻이 아니다. 사용자의 자연어 질의는 먼저 **질의 서비스와 DB evidence layer**에 들어간다. 질의 서비스는 “주차 차량”과 같은 의미 요구를 텍스트 임베딩 또는 lexical query로 만들고, “오전·교차로 A·신호 상태” 같은 hard predicate를 구조화 조건으로 분리한다. DB는 이 두 신호로 후보를 검색·결합·정렬한다. 그 뒤 소수의 근거와 provenance만 최종 VLM에 전달하며, VLM은 이 제한된 근거를 읽고 답변·요약·설명을 생성한다.

```text
오프라인/비동기 물질화
원본 영상 → clip/frame 샘플링 → pixel-only 캡션 + 시각/텍스트 임베딩
         ↘ camera·time·sensor metadata ↘ URI·timestamp·provenance
                                      → DB/벡터 색인

온라인 질의
사용자 자연어 + 구조화 조건
  → query parsing/embedding
  → metadata filter + lexical/dense/visual retrieval + rank fusion
  → top-k evidence packet
  → 고정 VLM의 답변 생성
```

### D.2 “전체 코퍼스”에 저장되는 것

전체 코퍼스는 원본 비디오 파일만을 뜻하지 않는다. 원본은 객체 스토리지나 파일 시스템에 보존하고, 질의 경로에는 원본 참조와 다음 파생 표현을 물질화한다. (1) clip/frame ID, camera, timestamp, sensor·시공간 metadata, (2) clip의 대표 프레임을 픽셀만 보고 만든 VLM caption, (3) caption의 BGE-M3 텍스트 벡터, (4) 대표 또는 복수 frame의 CLIP 시각 벡터, (5) 임베딩·캡션 모델 revision과 생성 provenance, (6) Flat/HNSW/IVF/부분 색인의 물리 구조다. 모든 표현을 반드시 동시에 저장하는 것이 아니라, RQ2와 RQ5가 어떤 표현을 물질화할지를 선택하는 기준을 다룬다.

### D.3 evidence packet의 최소 스키마

**표 16. 최종 VLM에 전달되는 evidence packet 예시**

| 필드 | 의미 | 예시 |
|---|---|---|
| query_id·parsed intent | 원 질의와 의미/hard 조건 분해 | q17; parked vehicle; morning |
| clip/frame identity | 근거의 안정적 식별자 | clip_00312; frame_02 |
| source pointer | 원본 영상에 재접근할 URI | object URI 또는 로컬 경로 |
| camera·timestamp | 시공간 위치 | cam_07; 08:31:14–08:31:24 |
| retrieved evidence | 캡션, 선택 프레임 또는 복수 프레임 | top-3 caption + thumbnails |
| metadata facts | 검색에 사용한 외생 센서 사실 | signal=yellow; density=high |
| retrieval trace | 전략·점수·순위·색인 | B4; dense 0.71; rank 1; partial HNSW |
| provenance | 모델·revision·생성 경로 | Qwen3.5 caption; CLIP ViT-B/32 |

evidence packet은 새로운 학습 데이터셋이 아니라 **한 번의 질의에 대해 VLM이 실제로 읽을 작은 검색 결과 묶음**이다. 원본 포인터와 timestamp를 함께 넣어 캡션만으로 답할 수 없는 경우 선택 프레임이나 짧은 clip을 재확인할 수 있게 한다.

### D.4 24시간 운영에 대한 연구 범위와 안전한 해석

본 연구가 직접 측정한 것은 이미 물질화된 벡터·metadata에서의 검색, 색인 구축·크기, 부분 색인 상각과 고정 VLM 답변 전파다. 24시간 스트림 전체의 디코딩, 프레임 선택, VLM 캡셔닝, 임베딩 생성, 증분 색인 유지에 대한 end-to-end 비용은 직접 벤치마크하지 않았다. 따라서 “운영 가능성을 증명했다”거나 “VLM을 edge에서 돌리지 않아도 된다”는 결론은 낼 수 없다.

실무 이식안은 연구 결과로 확정된 부분과 운영 가설을 구분해야 한다. 실측 근거는 (a) 표현별 벡터 수·저장량, (b) global/partial 색인의 구축비·크기·질의 절감, (c) hot predicate의 상각 손익분기다. 반면 motion/object/event gate로 일부 프레임만 비동기 캡셔닝하는 tiered ingestion, delta index를 주기적으로 merge하는 정책, retention에 따른 hot/warm/cold 계층은 합리적 설계안이지만 본 논문의 실험 결과는 아니다. 후속 운영 실험은 stream arrival rate, decode FPS, sampled-frame rate, caption GPU-seconds/hour, embedding throughput, index update amplification, staleness와 end-to-end p95를 함께 측정해야 한다.
"""


REGISTRY_APPENDIX = """## 부록 E. 데이터·실험·주장 전체 레지스트리

### E.1 데이터셋 역할과 provenance 성숙도

**표 17. 확보 데이터 10종의 실제 역할과 원고 판정**

| 데이터셋 | 최종 규모/표현 | 채널 성숙도 | 실제 사용 | 원고 판정·제한 |
|---|---|---|---|---|
| AI Hub 522 교차로 | 3,000 clips; 8,349 frames; 색인 143,830×512; 85 queries | 완전 tri-source, A6 6/6 | B0–B5, 결합도, filtered-ANN, 저장단위, KG, 지각벽, 캡셔너 | 헤드라인; 완전 tri-source가 한 데이터에 의존 |
| Sinnaedoro traffic | 132,521×512; 1,000 queries | predicate-only/recall GT | real-vs-random ANN, 색인 3축, pgvector, partial index | 물리설계 코퍼스; QA·tri-source 주장 불가 |
| MEVA KF1 | 985 clips/frames; 193 queries | 외부 사람 활동 주석 + pixel caption | 외부 B0–B5, 저장단위, 캡셔너 | 외적 검색·표현 검증; 완전 tri-source 아님 |
| MIRIS traffic | 59,019 frame vectors | 색인·배포 전용 | global/partial, hot/cold 교차검증 | 물리설계 외적 검증; 검색 relevance 없음 |
| VRU Accident | 6,000 VQA; 답변실험 600/config | 수리 전 순환, 수리 후 A9 축소감사 | 순환 붕괴, evidence ladder | 구조 우수성은 수리판/답변 계층만; v1 성능은 진단용 |
| UCA/VALU anchor | 6,432 segments; 135 queries | 2.5-channel; 독립 센서 없음 | B0–B5 방향 대조, 캡셔너 | 3/4 사전대조; 완전 tri-source로 부르지 않음 |
| AI Hub 지능형 CCTV | 269 clips 수리판 | label_json 계보, A9 축소감사 | 순환 붕괴·이식성 | v1 완벽수치는 누수 진단용 |
| AI Hub 다각도 CCTV | 400-event stratum | 단일 label/template channel | 다중 시점 답변 선택 | 검색 구조·tri-source 주장 불가 |
| CityFlow-NL | annotation staging; 추출 frame 0 | 미완성 | downstream 소비 0 | 결과 주장 제외 |
| AI Hub 이상행동 CCTV | canonical 1,968 clips; 고아 FAISS 자산 | 단일 label XML | 최종 v3 미사용 | 결과 주장 제외; 시각 전체 실행은 feasibility만 |

### E.2 실험 트랙별 증거 지위

**표 18. 전체 실험·음성 결과·제외 실험의 주장 범위**

| 트랙 | 핵심 비교 | 대표 결과 | 증거 지위 | 원고 사용 |
|---|---|---|---|---|
| 순환 붕괴·통제 주입 | VRU·지능형 v1→수리; 522 Qwen C1/C2 | Qwen clean 0.181→oracle-filter 1.000 / label-document 0.854 | 직접 개입+강건성 | RQ1 핵심; 과거 차이 전체 귀속 금지 |
| 522 비순환 검색 | B0–B5; strict/semantic; 85q | hard/soft와 결합도에 따라 B4 효과 변화 | 확증+탐색 | RQ3–RQ4 헤드라인 |
| UCA 전이 | 사전 고정 4대조 | 3/4 방향 일치; 강결합 우위 실패 | 탐색적 외적 검증 | 실패 포함 유지 |
| MEVA 외부 검색 | B0–B5 | hard constraint와 caption blind spot 교차확인 | 외적 관찰 | 구조 보조 근거 |
| real-vs-random ANN | 실측 predicate vs 동일 선택도 mask | random mask가 recall 손실을 과소평가 | 확증 | RQ5 핵심 |
| 엔진 교차검증 | pgvector·Milvus·Weaviate | 엔진별 크기 차이 속 기전 재현 | 확증/관찰 | RQ5 |
| 색인 3축 | Flat/HNSW/IVF-Flat/IVF-PQ | latency–recall–size Pareto; Qwen-2048 5-seed 강화 | 관찰·exact fidelity | 대규모 task 품질로 확대 금지 |
| KG 경계 | A6-KG/entity-KG | 기존 metadata/text 채널로 환원 | 음성 결과 | 새 축 과장 방지 |
| 저장 단위(기존) | caption/frame/multi/dual, 혼합 encoder | 522 caption Pareto; MEVA frame 점추정 우위 | 역사적 설계 대비 | encoder와 표현 효과가 섞임 |
| 동일-encoder 공동 ablation | 4 storage × 호환 search × 7 index, 91 configs | 522 multi-frame 큰 점추정; B4 strict↑/semantic↓ | 사후 우선 비교 | family-wise·전역 최적 과장 금지 |
| MEVA 동일-encoder 대조 | caption/one-frame/dual | frame 효과 불확실; dual 양수 | 외적 통제 | multi-frame 재현 아님; dual은 RRF 포함 |
| partial/local | global+WHERE vs predicate index | 선택적 조건의 recall/latency 안정화 | 관찰 | RQ5 |
| hot/cold | build cost / latency saving | N*가 선택도·질의빈도에 따라 변함 | 정책 도출 | 스트리밍 자동운영 실증은 아님 |
| 캡셔너 | Qwen2.5/Qwen3/Qwen3.5 | Qwen3.5 세 데이터 공통 향상; 절단 잔존 | 사전 판정+관찰 | RQ2 강건성 |
| 증거 사다리 | closed→retrieved→oracle | 답변 정확도 0.308→0.665/0.680→0.747 | 관찰 | RQ6; VRU 정답계보 제한 |
| 다중 시점 | view selection × 고정 VLM 4종 | 시점 선택에 따른 답변 변화 | 관찰 | RQ6 보조 |
| index→answer gate | 1K·143K·perception wall | 조작 실패·파일럿 지렛대 부족 | 음성 결과 | 전파 비보장 핵심 |
| v1 visual/fusion | CLIP/SigLIP, M-series, RRF | 높은 값은 수리 전 qrels 상속 | 성능 주장 제외 | 구현·누수 진단 이력만 |
| v1 reranker | bge-reranker-v2-m3 | CCTV +0.136, VRU −0.007 | 성능 주장 제외 | 순환 qrels 상속; 재실험 후보 |
| v1 한국어 인코더 | BGE-M3 vs bge-m3-ko | vector 0.701→0.740; B4=1.000 | 성능 주장 제외 | 1.000 자체가 누수 경고 |
| abnormal visual 확장 | zip→frame→CLIP | 메커니즘만 확인, 전체 미완료 | feasibility | 실험 결과로 서술 금지 |

### E.3 수리 전 실험의 정확한 활용법

초기 M-series visual retrieval, SigLIP/CLIP 교체, multi-vector Max-Sim, weighted RRF, cross-encoder reranking, BGE-M3-KO 결과는 실제 코드와 산출물이 존재한다. 그러나 이 트랙은 v1의 순환 qrels를 상속했으므로 “추가 검색 방법 다섯 가지가 본 연구의 비순환 구조 우위를 증명했다”라고 쓸 수 없다. 논문에서 허용되는 용도는 세 가지다. 첫째, 순환성 감사가 왜 필요했는지를 보여주는 개발 이력이다. 둘째, 구현 가능한 후보 설계 공간의 목록이다. 셋째, 비순환 qrels로 재실행해야 할 후속 ablation의 우선순위다. 특히 한국어 인코더의 B4=1.000과 reranker의 큰 개선은 강건성의 증거가 아니라 누수 여부를 먼저 의심해야 하는 전형적 신호다.

### E.4 완결성 기준

“모든 실험을 반영한다”는 모든 산출물을 긍정 결과로 채택한다는 뜻이 아니다. 본 완전판은 성공, 실패, 조작 실패, 고아 산출물, staging-only 데이터와 수리 전 무효 비교를 모두 기록하되, 주장을 지지할 수 있는 증거의 지위를 함께 고정한다. 숫자 검증이 가능한 실측 결과는 본문/부록 표로, 파일럿이나 미완료 트랙은 범위·제외 사유로, 운영 제안은 검증 전 가설로 구분한다.
"""


FRAMING_APPENDIX = """## 부록 G. 논문 프레이밍·주장 은행

이 부록은 최종 제출본에서 길이에 따라 선택·압축할 수 있는 논리 단위다. 새로운 실험 결과를 추가하지 않으며, 본문과 다른 동기를 만들기 위한 문구 모음이 아니다.

### G.1 Motivation 확정본

1. **현실적 병목.** 장기간 축적된 고화질 CCTV 전체를 질의마다 VLM에 넣는 것은 컨텍스트 길이, GPU 연산, 응답 지연과 추론 비용 때문에 현실적이지 않다.
2. **DB evidence layer의 필요.** 질의 서비스는 원본을 직접 전부 읽지 않고, DB가 미리 물질화한 metadata·캡션·시각 벡터에서 소수의 clip/frame을 검색해야 한다. 최종 VLM은 원본 포인터, timestamp, 검색 점수와 provenance를 포함한 작은 evidence packet만 읽는다.
3. **구조 선택의 비자명성.** clip-caption·frame-vector·multi-vector·dual-index 표현, metadata/lexical/dense/visual 신호, prefilter/postfilter/single-stage 결합, Flat/HNSW/IVF와 global/partial/local 배포는 품질·지연·저장·구축비 사이에 서로 다른 절충을 만든다.
4. **평가 타당성의 선행 문제.** predicate·document·relevance가 같은 주석 계보에서 파생되면 특정 구조의 우위가 실험 전에 보장될 수 있다. 이 상태에서는 더 좋은 DB 설계를 찾는 것이 아니라 라벨을 재사용하는 구조를 찾게 된다.
5. **학계 공백.** 비디오 DB, filtered-vector search, 감시 VLM 연구는 각각 강한 축을 제공하지만, 실제 도시 predicate와 비순환 정답 아래에서 표현·필터 계획·색인·엔진·비용·답변 전파를 하나의 통제된 설계공간으로 연결한 평가는 드물다.
6. **연구 목표.** 먼저 비순환 평가가 구조적 우위 보장을 제거하는지 검증하고, 그 위에서 조건의 의미·선택도·분포·질의 빈도에 따른 evidence-layer 선택 기준과 VLM 답변으로의 전파 경계를 도출한다.

### G.2 Problem Statement

**전체 원본 데이터를 매번 VLM에 입력하는 대신, 필요한 증거를 더 낮은 검색 비용과 지연으로 선별하면서 검색 정확도와 답변 지원 가능성을 보존하려면 어떤 DB 표현·검색·색인·배포 구조를 선택해야 하며, 그 비교가 동일 주석 계보의 재사용으로 특정 구조에 유리하게 만들어지지 않았음을 어떻게 보장할 것인가?**

### G.3 Research Question의 절차적 순서

**RQ1 — 비순환 평가의 타당성.** 필터 predicate, 질의 템플릿, 검색 문서와 relevance label이 동일 주석 계보에서 파생되는 순환성은 검색 구조의 상대 성능을 어떻게 왜곡하며, tri-source separation·이중 정답·기계 감사는 구조적 우위 보장을 제거할 수 있는가?

**RQ2 — 증거 표현.** clip-caption, frame-vector, multi-vector와 dual-index는 검색 품질, 지연과 저장공간 사이에 어떤 절충을 형성하며, 캡션–질의 정합도와 캡셔너 선택은 최적 표현을 어떻게 바꾸는가?

**RQ3 — metadata–vector 결합.** predicate가 hard constraint인지 soft intent인지, 그리고 predicate–relevance 결합도가 어느 정도인지에 따라 vector-only, prefilter, postfilter와 single-stage 계획의 상대 효과는 어떻게 달라지는가?

**RQ4 — 검색 신호와 융합.** metadata, BM25, dense text, visual, sparse–dense와 text–visual 융합 중 어떤 신호가 표현·질의 유형에 적합하며, 라벨 재진술을 제거한 뒤에도 독립 이득을 제공하는가?

**RQ5 — 물리 색인과 배포.** 실측 predicate의 선택도·군집성과 질의 빈도 아래에서 Flat, HNSW, IVF-Flat, IVF-PQ, 관계형·전용 엔진과 global·partial·local·hot/cold 배포는 recall·latency·size·build cost를 어떻게 균형화하는가?

**RQ6 — VLM-QA 전파.** 검색 품질과 색인 재현율 차이는 최종 VLM-QA로 어느 정도 전파되며, 코퍼스 규모, VLM 지각, 질문 설계와 답변 편향은 이 전파를 어떻게 제한하는가?

RQ1은 나머지 비교의 성립 조건이므로 항상 먼저 온다. RQ2는 논리 저장 표현, RQ3–RQ4는 논리 검색 계획, RQ5는 물리 설계, RQ6은 하류 유효성을 차례로 다룬다. 정확도·지연·저장·구축비는 별도 RQ가 아니라 RQ2–RQ5의 공통 평가 축이다.

### G.4 Research Gap의 안전한 표현

- “비디오 DB는 VLM-QA를 전혀 다루지 않는다”가 아니라, 객체·트랙·시공간 질의가 중심이고 자유형 자연어+외생 metadata evidence packet의 전체 DB 설계공간은 주 평가 대상이 아니었다고 쓴다.
- “filtered ANN은 random mask만 쓴다”가 아니라, 실제 라벨과 clustering을 다룬 연구가 이미 있으므로 본 연구의 차이를 **실측 도시 predicate와 동일 선택도 mask의 짝 비교, DB 배포와 답변 계층의 연결**로 한정한다.
- “감시 VLM에는 검색이 없다”가 아니라 ForeSea 같은 검색 연계 연구를 인정하고, 모델 벤치마크와 DB 물리 변수의 통제 비교 사이의 공백을 제시한다.
- “최초”는 체계적 문헌조사로 입증하지 않는 한 피하고, “드물다”, “통합적으로 평가되지 않았다”, “본 연구는 교차점을 통제된 설계공간으로 정식화한다”를 사용한다.

### G.5 주장–증거–금지 문구 매트릭스

**표 22. 최종 원고에서 지켜야 할 주장 경계**

| 주장 | 허용 근거 | 허용 표현 | 금지/과장 표현 |
|---|---|---|---|
| 순환성은 평가를 왜곡 | 두 수리 사례 + Qwen/BGE C1·C2 통제 주입 | “순환 경로만 주입하면 지표가 크게 상승” | “과거 성능 차이 전체가 순환 때문”, “모든 benchmark가 순환” |
| prefilter 효과 | strict/semantic·결합도·외부 대조 | “hard constraint에서 유리, soft intent는 손실 가능” | “prefilter가 항상 최적” |
| 저장 단위 선택 | 522 동일-Qwen 4표현 + MEVA one-frame 통제 + 캡셔너 ablation | “522에서 multi-frame 후보 신호; 목적·SLA 의존” | “multi-frame 보편 최적”, “MEVA에서 외부 재현” |
| real predicate 필요 | real-vs-random paired ANN | “동일 선택도 mask와 거동 차이” | “기존 연구는 전부 random mask” |
| partial index 정책 | Sinnaedoro·MIRIS 실측 | “선택적·hot predicate에서 상각 가능” | “24시간 자동 운영을 검증” |
| 답변 전파 | VRU ladder + multiview + negative gates | “증거 품질은 중요하나 전파는 비보장” | “검색 nDCG 상승이 답변을 항상 향상” |
| 비용·지연 | 검색·색인 계층 계측 | “DB evidence-layer 비용” | “end-to-end VLM 서비스 비용” |

### G.6 Topic 한·영문

**English.** Designing Non-Circular Hybrid VLM–DB Retrieval Workloads and Comparing Evidence Representation, Filter Planning, Vector Indexing, and Deployment Structures for Multimodal Urban Surveillance.

**한국어.** 멀티모달 도시 감시 환경에서 VLM 질의응답용 근거를 검색하기 위해, 순환 누수를 차단한 하이브리드 VLM–DB 워크로드를 설계하고 증거 표현, metadata–vector 결합 계획, 벡터 색인과 배포 구조가 검색 정확도·지연·저장·구축비 및 최종 답변 전파에 미치는 영향을 비교한다.

### G.7 논문 한 문장 요약

본 연구는 **평가 계보를 먼저 수리한 뒤**, 자연어 의미와 외생 센서 조건이 결합된 도시 감시 질의에서 VLM용 evidence packet을 어떤 DB 표현·검색 계획·색인·배포 구조로 선별해야 하는지를 정확도·지연·공간·구축비와 최종 답변 전파 경계까지 함께 측정한다.
"""


ASSET_APPENDIX = """## 부록 H. 결과 자산·재집계 경로

아래 경로는 저장소 루트 `2026_KIISE/`를 기준으로 한다. 카메라레디 공개본에서는 라이선스가 허용하는 데이터와 익명화된 실행 manifest만 별도 패키지로 묶어야 한다. 이 표는 원고의 결과를 다시 계산하거나 제외 판정을 추적하기 위한 내부 작업 색인이다.

본 완전판 생성기는 `scripts/make_dbr_complete_working_draft_v5.py`다. 원고의 Markdown 표 19–21과 24–27은 결과 CSV/JSON을 실행 시점에 직접 읽어 생성하므로 수기 전사 오차를 피한다. 제출 길이로 다시 압축할 때는 이 working master에서 필요한 주장과 표를 선택한다.

**표 23. 실험군별 원시 결과·판정·검증 자산**

| 실험군 | 주 결과 경로 | 보조/판정 자산 | 원고 소비 |
|---|---|---|---|
| 순환 붕괴 | `paper_assets/20260710_noncircular_collapse/` | `vru_collapse_table.csv`, `significance_v2_b4_vs_b2.csv` | 4절·표 2 |
| Qwen 순환성 통제 주입 | `paper_assets/20260717_ablation_agent_crosscheck/qwen_aligned_circularity/` | summary·contrast·ranking·10/10 verifier | 4.1절·표 24 |
| 522 B0–B5·결합도 | `Datasets/processed/aihub_522_intersection/20260710/results/trisource_expanded_b0_b5/` | `significance_expanded.csv`, `t3_coupling_curve.csv` | 5–6절 |
| 522 A6·provenance | `Datasets/processed/aihub_522_intersection/20260710/canonical_trisource_expanded/` | `A6_trisource_audit.json`, provenance 문서 | 3·5절 |
| UCA 외부 대조 | `paper_assets/20260712_uca_external/` | `UCA_contrasts.json`, `UCA_query_deltas.csv` | 6절·표 6 |
| real-vs-random ANN | `paper_assets/20260710_pillarB/` | `filtered_ann_real_{A,B}.csv`, `B1_confirmatory_{A,B}.csv` | 7.1절 |
| pgvector | `paper_assets/20260710_pillarB/` | `pgvector_filtered.csv`, `pgvector_ann_sweep.csv` | 7.2절 |
| Milvus·Weaviate | `paper_assets/20260712_engine_replication/` | `B4_results.csv`, `B4_mechanism.csv`, F7 seed files | 7.2절 |
| 색인 3축 | `paper_assets/20260710_pillarB/` | `index_grid_*`, `E2_retrieval_pareto.csv` | 7.3절 |
| KG 경계 | `paper_assets/20260713_kg/` | `collapse_receipt.json`, `KG_COLLAPSE.md` | 7.4절 |
| 저장 단위 | `Datasets/processed/{aihub_522_intersection,meva_kf1}/.../results/storage_unit/` | `storage_unit_{summary,metrics,latency}.csv` | 7.5절 |
| partial·hot/cold | `paper_assets/20260713_db_design/` | Sinnaedoro·MIRIS global/partial와 policy CSV | 7.5절 |
| 캡셔너 | `paper_assets/20260715_caption_model_ablation/` | `VERDICT.json`, metrics·paired·audit·stats CSV | 7.6절·부록 F |
| 동일-Qwen 공동 ablation | `paper_assets/20260717_joint_optimization_validation/` | 91 configs, per-query/ranking/latency, 32/32 verifier | 7.7절·표 25–26 |
| MEVA 동일-encoder | `paper_assets/20260717_joint_optimization_validation/meva_same_encoder_control/` | summary·paired bootstrap·57 clusters | 7.7절·표 26 |
| 고정밀 ANN 5-seed | `paper_assets/20260717_ablation_agent_crosscheck/qwen2048_high_recall_5seed/` | 30-cell raw/summary·8/8 verifier | 7.7절·표 26 |
| treatment·통계·에이전트 감사 | `paper_assets/20260717_ablation_agent_crosscheck/` | 12/12 gate, agy·Claude 감사, 최종 교차검증 | 9절·부록 I |
| 답변 사다리 | `experiments_expansion/rag_vqa/results_full/` | Qwen·Llama parquet/summary JSON | 8.1절 |
| 다중 시점 | `paper_assets/20260707_submission_figures/` 및 원 결과 manifest | `fig_multiview_answer_ladder.*` | 8.1절 |
| index→answer | `paper_assets/20260710_pillarB/e1_pilot_configs.csv`, `paper_assets/20260711_e1a/` | `paper_assets/20260713_index_answer/gmanip_gate.json` | 8.2절 |
| 지각 재검증 | `paper_assets/20260712_perception_retest/` | `VERDICT.json`, 모델별 CSV/summary | 8.2절·한계 |
| 수리 전 reranker | `experiments_expansion/reranker/` | `experiments_expansion/EXPANSION_RESULTS.md` | 성능 주장 제외 |
| 수리 전 시각·융합 | `paper_assets/20260707_advanced_ablation/`, `paper_assets/20260707_true_multimodal_examples/` | v1 presentation/submission figures | 진단 이력만 |
| 기존 전 수치 재검증 | `scripts/verify_manuscript_numbers.py` | `paper_assets/verification_suite_20260711/report.json` | 기존 본문 164/164 PASS |
| 최신 working-master 검증 | `scripts/verify_working_master_latest.py` | joint/circularity/MEVA/high-recall 원자산 | 최신 수치·구조·주장 경계 |
"""


def replace_literal_once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"expected one literal passage, got {count}: {old[:100]}")
    return text.replace(old, new, 1)


def strengthen_latest_claims(text: str) -> str:
    text = replace_literal_once(
        text,
        "## 5. 데이터셋과 워크로드 구축",
        circularity_injection_section().strip()
        + "\n\n## 5. 데이터셋과 워크로드 구축",
    )
    text = replace_literal_once(
        text,
        "## 8. 실험 3 — 답변 계층",
        joint_ablation_section().strip() + "\n\n## 8. 실험 3 — 답변 계층",
    )

    text = re.sub(
        r"\*\*저장 단위\(정확도·지연·저장\)\.\*\*.*?"
        r"다만 이 비교는 저장 단위 선택이 인코더 선택\(캡션=텍스트, 프레임=시각\)을 "
        r"내포하는 설계 대비이며 인코더 격리 실험이 아니다\.",
        (
            "**저장 단위의 역사적 혼합-encoder 비교.** 같은 질의·이중 정답 아래 clip-caption"
            "(BGE-M3), frame-vector(CLIP), multi-vector와 dual-index를 비교한 초기 실험에서는 "
            "522 caption이 0.169·12.3MB·0.59ms로 Pareto에 있었고, MEVA one-frame은 0.161 대 "
            "caption 0.103의 점추정치를 보였다. 그러나 표현과 encoder를 동시에 바꿨으므로 이를 "
            "저장 단위의 순수 효과나 multi·dual의 보편적 무효성으로 해석할 수 없다. 이 결과는 "
            "설계 이력과 비용 기준선으로만 유지하며, 인코더를 Qwen으로 통일한 7.7절의 91-config "
            "공동 ablation을 RQ2의 주 통제로 사용한다."
        ),
        text,
        count=1,
        flags=re.DOTALL,
    )

    old_item5 = (
        "(5) 저장 단위는 캡션-질의 정합에 맞춰 고르고(정합 시 clip-caption, 아니면 frame-vector; "
        "multi·dual은 이득 없음), 관계형 부분 색인은 선택적 predicate에서 global+postfilter를 "
        "지배하므로 hot/cold 손익분기 N\\*로 배포하라 — 이 두 처방은 해외 MEVA·SIGMOD MIRIS에서 "
        "재현된다(7.5절)."
    )
    new_item5 = (
        "(5) 저장 단위는 목적·데이터·비용을 함께 보라. 혼합-encoder 비교는 설계 이력으로 한정하고, "
        "동일-Qwen 522에서는 multi-frame이 큰 품질 점추정치를 보였지만 storage-family 군집 BH "
        "q>0.05이고 저장·지연 비용이 증가했다. MEVA one-frame 효과는 불확실하며 multi-frame 외부 "
        "재현이 아니다. 따라서 단일 표현을 보편 최적으로 선언하지 말고 91개 호환 구성의 Pareto에서 "
        "strict/semantic·지연·공간 SLA별로 선택한다. 관계형 부분 색인은 선택적 predicate에서 "
        "global+postfilter를 지배하므로 hot/cold 손익분기 N\\*로 배포하라(7.5–7.7절)."
    )
    text = replace_literal_once(text, old_item5, new_item5)

    old_guide = (
        "| 저장 단위 선택(3축) | 캡션-질의 정합 시 clip-caption, 아니면 frame-vector; multi·dual 회피 | "
        "522 clip-caption Pareto(0.169·12.3MB·0.59ms), MEVA frame 지배(0.161 대 0.103·2.0 대 4.0MB), "
        "multi 지연 6–7× | 실측 | 7.5절 |"
    )
    new_guide = (
        "| 저장 단위 선택 | 목적·SLA별 Pareto; 522에서는 multi-frame을 품질 후보로 검토 | "
        "동일-Qwen B2+Flat semantic 0.352(multi) 대 0.181(caption), Δ +0.171; 군집 BH q=0.085, "
        "payload 68.4 대 24.6MB | 사후 우선 비교(보편 우위 아님) | 7.5–7.7절 |"
    )
    text = replace_literal_once(text, old_guide, new_guide)

    old_limit = (
        "다만 저장 단위 비교는 인코더 선택을 내포하는 설계 대비이며, 7.5절 확장 수치는 "
        "사전등록 확증 가족 밖의 실측·확립 관찰이다"
    )
    new_limit = (
        "기존 7.5절 저장 단위 비교의 encoder 혼입은 7.7절 동일-Qwen 통제가 522 범위에서 해소했지만, "
        "91-config 핵심 비교는 사후 통합 명세이며 storage-family 군집 BH q가 0.05를 넘는다"
    )
    text = replace_literal_once(text, old_limit, new_limit)

    old_external = (
        "7.5절의 저장 단위·부분 색인·배포 정책 확장 수치는 실측·확립 관찰로 사전등록 확증 가족 밖이며 "
        "결과 파일 대조로만 검증됨(원고 수치 검증기 V4 확장은 향후 과제);"
    )
    new_external = (
        "7.7절 동일-Qwen 91-config 결과는 522 내부의 사후 우선 비교이고, MEVA는 one-frame만 제공해 "
        "multi-frame 외부 재현이 아니며, 143,830-vector 실험은 task qrels 없이 exact-neighbor "
        "fidelity만 측정함;"
    )
    text = replace_literal_once(text, old_external, new_external)

    old_stats = (
        "결합도 곡선은 쌍 군집 CI가 0을 포함해 확증 미달 — 탐색적 지위 유지(6절·본 절);"
    )
    new_stats = (
        "결합도 곡선은 쌍 군집 CI가 0을 포함해 확증 미달 — 탐색적 지위 유지(6절·본 절); "
        "multi-frame−caption은 질의·군집 CI가 양수지만 storage-family 군집 BH q=0.085/0.089로 "
        "family-wise 0.05 확증이 아니며, 91-config 순위는 탐색적 Pareto로만 해석;"
    )
    text = replace_literal_once(text, old_stats, new_stats)

    validation_anchor = (
        "스위트가 직접 실행하는 40 체크(V1–V5)는 최근 실행에서 전부 통과했다(40 PASS / 0 FAIL)."
    )
    validation_addition = (
        validation_anchor
        + "\n\n2026-07-17 보강 실험은 별도 검산층을 추가했다. Joint verifier 32/32는 지표 산술·"
        "ranking/vector/hash/seed 무결성에 한정하고, treatment/statistics verifier 12/12가 정확한 "
        "91개 호환 구성, 15,470 metric cells, 77,350 latency trials, filtered ranking 382,193행의 "
        "predicate 위반 0건, qrel 논리, paired delta와 BH를 독립 확인했다. Qwen 순환성은 10/10, "
        "고정밀 5-seed ANN은 8/8을 통과했다. agy와 Claude의 서로 독립적인 읽기 전용 감사는 모두 "
        "PASS_WITH_LIMITATIONS였고 치명적 오류 없음과 주장 경계를 일치 판정했다. 이 검산은 산출물 "
        "무결성을 보증하지만 외적 타당성이나 사전등록 지위를 대신하지 않는다."
    )
    text = replace_literal_once(text, validation_anchor, validation_addition)

    text = replace_literal_once(
        text,
        "| 저장 단위 | 522·MEVA caption/frame/multi/dual | 포함 | 7.5절 |",
        (
            "| 저장 단위(혼합 encoder) | 522·MEVA caption/frame/multi/dual | 포함: 역사적 설계 대비 | 7.5절 |\n"
            "| 동일-encoder 공동 ablation | 522 4 storage×호환 search×7 index, 91 configs | 포함: 사후 우선 비교 | 7.7절 |\n"
            "| 순환성 통제 주입 | 522 Qwen C1 oracle-filter·C2 label-document | 포함: 직접 개입 | 4.1절 |"
        ),
    )

    text = replace_literal_once(
        text,
        "요컨대 RQ1은 3–4절, RQ2는 7.5–7.6절, RQ3–RQ4는 6절, RQ5는 7.1–7.5절, RQ6은 8절이 답한다.",
        (
            "요컨대 RQ1은 3–4.1절, RQ2는 7.5–7.7절, RQ3–RQ4는 6절, "
            "RQ5는 7.1–7.7절, RQ6은 8절이 답한다."
        ),
    )
    text = replace_literal_once(
        text,
        "남은 일도 명확하다:",
        (
            "동일-Qwen 통제와 순환성 직접 개입은 내부 타당성을 강화했지만, 보편 최적·외부 "
            "multi-frame 재현·대규모 task 품질을 증명하지는 않는다. 남은 일도 명확하다:"
        ),
    )
    return text


def wrap_wide_blocks(text: str) -> str:
    """Use full width for tables with five or more columns and key figures."""
    table_pat = re.compile(r"(?m)(^\*\*표\s+\d+[^\n]*\*\*\n\n(?:^\|.*\n)+)")

    def table_repl(match: re.Match[str]) -> str:
        block = match.group(1)
        rows = [line for line in block.splitlines() if line.startswith("|")]
        columns = max((line.count("|") - 1 for line in rows), default=0)
        number_match = re.search(r"\*\*표\s+(\d+)", block)
        number = int(number_match.group(1)) if number_match else -1
        # Some tables have only 2--4 columns but contain long examples, claims,
        # or paths. They overflow a single text column despite the low column
        # count, so treat semantic content width as well as column count.
        force_wide = number in {3, 15, 16, 22, 23, 24, 25, 26, 27}
        if columns < 5 and not force_wide:
            return block
        if number == 27:
            return f"{v4.FINAL_WIDE_START}\n\n{block}\n"
        prefix = f"{v4.PAGE_BREAK}\n\n" if number == 22 else ""
        return f"{prefix}{v4.WIDE_START}\n\n{block}\n{v4.WIDE_END}\n"

    text = table_pat.sub(table_repl, text)
    fig_pat = re.compile(r"(?m)(^!\[그림\s+\d+[^\n]*\]\([^\n]+\)(?:\{[^\n]+\})?\n)")

    def figure_repl(match: re.Match[str]) -> str:
        block = match.group(1)
        number_match = re.search(r"그림\s+(\d+)", block)
        number = int(number_match.group(1)) if number_match else -1
        if number in {1, 5, 6}:
            return f"{v4.WIDE_START}\n\n{block}\n{v4.WIDE_END}\n"
        return re.sub(r"\{width=[^}]+\}", "{width=3.0in}", block)

    return fig_pat.sub(figure_repl, text)


def build_body() -> str:
    original_replace = v4.replace_once
    original_wrap = v4.wrap_wide_blocks

    def keep_full_prose(text: str, pattern: str, replacement: str, flags=0) -> str:
        if any(pattern.startswith(prefix) for prefix in COMPRESSION_PREFIXES):
            # Confirm the source passage still exists so the skip cannot hide a
            # future source edit that invalidates this builder.
            if re.search(pattern, text, flags=flags) is None:
                raise RuntimeError(f"full-prose source passage missing: {pattern[:80]}")
            return text
        return original_replace(text, pattern, replacement, flags)

    try:
        v4.replace_once = keep_full_prose
        v4.wrap_wide_blocks = lambda text: text
        body = V4_BUILD_BODY()
    finally:
        v4.replace_once = original_replace
        v4.wrap_wide_blocks = original_wrap

    body = strengthen_latest_claims(body).rstrip()
    body += "\n\n" + PIPELINE_APPENDIX.strip()
    body += "\n\n" + REGISTRY_APPENDIX.strip()
    body += "\n\n" + caption_detail_appendix().strip()
    body += "\n\n" + FRAMING_APPENDIX.strip() + "\n"
    body += "\n\n" + ASSET_APPENDIX.strip() + "\n"
    body += "\n\n" + latest_validation_appendix().strip() + "\n"
    return wrap_wide_blocks(body)


def main() -> None:
    # Reuse the validated v4 Word pipeline while redirecting all artifacts and
    # replacing only the body/margins. The 20-page submission file is untouched.
    v4.OUT_MD = OUT_MD
    v4.OUT_DOCX = OUT_DOCX
    v4.OUT_PDF = OUT_PDF
    v4.REF_DOCX = REF_DOCX
    v4.configure_section = configure_section
    v4.build_body = build_body
    v4.main()


if __name__ == "__main__":
    main()
