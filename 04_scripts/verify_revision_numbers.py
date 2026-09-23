#!/usr/bin/env python3
"""Regression guard for manuscript/0_main_paper.md (심사 대응 개정판, 2026-08-09).

verify_paper_script_numbers.py에서 파생. 개정판에서 의도적으로 바꾼 문구 2건의 필수 문자열을
갱신하고, 표 11(RQ6 사다리 CI·대비)과 범주별 분해 검증을 추가했다.

Checks the contested headline numbers of the CURRENT manuscript against the
canonical artifacts identified in the 2026-07-23 verification sweep.
Replaces the retired verify_manuscript_numbers.py (which targets the deleted
v6 manuscript). Read-only; exits non-zero on any failure.
"""
import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MS = ROOT / "manuscript" / "0_main_paper.md"
PA = ROOT / "paper_assets"

checks = []


def check(name, ok, detail=""):
    checks.append((name, bool(ok), detail))


def approx(a, b, tol=5e-4):
    return abs(float(a) - float(b)) <= tol


text = MS.read_text(encoding="utf-8")

# 1) Banned stale numbers / phrases
for banned in [
    "0.418",
    "98.12",
    "16x7",
    "이미지 이미지",
    "용ㅇ",
    "평가 계약",
    "requires an end-to-end test",
    "caused by real-world data clustering",
    "수집 경로를 완전히 독립시킨",
    "각각 독립적으로 얻을 수 있어",
    "인접 단계의 대응 차이는 모두",
    "배제하고 결과의 통계적 유의성을 확보",
    "군집 강도를 직접 조작한 통제 실험은 수행하지 않았으므로",
    "증거 적중 표본을 확대한 대규모 생성 실험이 요구된다",
    "조건과 의미가 독립적인 저결합",
    "순수한 비순환 상태",
    "순환성이 배제된 평가 환경",
    "직렬화된 색인",
    "과제 형식의 발판",
    "성능 차이 무의미",
    "이것이 초록과 서론",
    "조건에 부합하는 결과를 제거한다",
    "관문",
    "게이트",
    "세 목적",
    "사전 필터 결합 설명문",
    "센서 유래 필드",
    "검색 정답 정의 필드",
    "정답 정의 필드",
    "내부 필드명",
    "메타데이터 조건 키",
    "사람 주석 유래 정의",
    "필드·토큰 누출",
    "라벨 경로",
    "다음 여섯 항목",
    "여섯 가지 자동 검사",
    "대규모 답변 모델 비교를 수행하지 않았다",
    "지능형 관제 CCTV / 벡터 단독 검색",
    "후보 수 감소가 아니라 정답 정보 재사용의 효과로 판정한다",
    "nDCG@10이 p50 검색 지연과 맺는 관계",
    "112개 호환 구성의 검색 품질-p95 지연 상충과 파레토 구성",
    "고결합 시 추가 이득 여부",
    "AI Hub 교차로와 UCA의 메타데이터 조건 적용 효과 일치성 비교",
    "고결합 조건의 추가 이득도 재현되지 않았다",
    "메타데이터 조건의 사용 목적이 검색 계획 선택의 기준임을 보여준다",
    "표 5는 질의 선정 방식과 조건–의미 결합도에 따른 효과량의 변화를 제시한다",
    "표 6은 AI Hub 교차로의 결과를 UCA/UCF-Crime 129질의에서 사전 고정한 네 방향으로 대조한다",
    "검색 전 조건 적용 우세 경향(탐색적, 2쌍 한정)",
    "AI Hub 교차로와 UCA/UCF-Crime의 검색 전 조건 적용 효과 방향 외부 대조",
    "도메인별 결합 구조의 효과량 Δ",
    "필수 제약·관심 단서별 검색 전 조건 적용 효과량 Δ의 외부 비교",
    "질의 선정 방식과 조건–의미 결합도에 따른 검색 전 조건 적용의 효과량 Δ(의미론적 정답 기준)",
    "필수 제약·관심 단서별 검색 전 조건 적용 효과량의 외부 방향 대조 (Δ, 95% 신뢰구간)",
    "외부 방향 대조",
    "교차곱 추가",
    "조건 교차곱",
]:
    check(f"manuscript does NOT contain '{banned}'", banned not in text)

# 2) Required corrected statements
for required in [
    "0.181에서 0.352",
    "재현율 0.9812-0.9952",
    "정답 조건 주입 시 5.5배, 정답 라벨 재진술 주입 시 4.7배",
    "고결합 분석도 2쌍에 그쳐 사전 승격 기준인 5쌍을 충족하지 못했다",
    "Qwen3.5-9B 설명문 코퍼스와 85개 질의",
    "그림 3과 표 4는 검색용 데이터 구성이 검색 품질·검색 지연·저장 비용을 함께 변화시키며, 정답 기준과 자원 제약에 따라 선택할 파레토 구성이 달라짐을 보여준다",
    "본 연구의 비용 결과는 벡터 데이터베이스 검색·색인 계층의 부분 비용으로 한정된다",
    "정답 정보 재사용의 인과 효과는 이어지는 통제 주입 실험에서 다른 요인을 고정하여 검증한다",
    "정답 정보 재사용 여부가 다른 작업 부하의 진단적 검색 품질 비교",
    "AI Hub 교차로의 정답 정보 통제 주입에 따른 의미론적 nDCG@10 변화",
    "112개 호환 구성의 nDCG@10–p95 검색 지연 분포",
    "검색용 데이터·검색 계획·물리 색인에 따른 검색 품질-p95 지연 상충과 파레토 구성",
    "메타데이터 조건의 사용 목적별 검색 계획 품질과 효과량 Δ",
    "본 절은 메타데이터 조건의 적용 시점과 순위화 방식에 따라 벡터 단독 검색, 검색 전 조건 적용, 검색 후 조건 적용과 혼합 검색의 품질을 비교한다",
    "필수 제약은 엄격한 정답으로, 관심 단서는 의미론적 정답으로 채점한다",
    "벡터 단독 0.059 · 검색 전 0.157 · 검색 후 0.152 · 혼합 0.135",
    "벡터 단독 0.170 · 검색 전 0.154 · 검색 후 0.150 · 혼합 0.133",
    "표 5의 핵심은 메타데이터 조건의 사용 목적에 따라 우선할 검색 계획이 달라진다는 점이다",
    "관심 단서의 Δ는 질의 선정 방식과 조건–의미 결합도에 따라 부호가 달라졌다",
    "연속 V와 Δ의 Spearman ρ는 0.383(95% 신뢰구간 [−0.088, 0.727])",
    "표 5에서 괄호 안의 ‘질의’와 ‘쌍’은 각각 질의 단위와 조건–의미 쌍 군집 단위의 부트스트랩 재표집을 뜻한다",
    "AI Hub 교차로는 필수 제약 85질의와 저결합 관심 단서 75질의를 사용했다",
    "UCA/UCF-Crime은 필수 제약 129질의와 영상 길이 구간 관심 단서 30질의를 사용했다",
    "필수 제약의 효과량은 두 데이터셋에서 모두 양수였고 신뢰구간이 0을 제외했다",
    "관심 단서는 두 데이터셋에서 음의 점 추정치를 보였지만 신뢰구간이 0을 포함했다",
    "이 결과는 사용 목적별 효과량의 부호와 불확실성을 비교하는 범위로 한정한다",
    "본 실험 범위에서 필수 제약에는 검색 전 조건 적용을 우선한다",
    "관심 단서에서는 벡터 단독 검색을 기본 계획으로 두고",
    "p50 / p95 검색 지연(ms)",
    "0.000 (기준)",
    "1.15 / 1.49",
    "1.21 / 1.53",
    "1.24 / 1.57",
    "3.65 / 4.27",
    "4.96 / 5.66",
    "벡터 검색 설명문 조건과의 차이에 대한 두 신뢰구간은 모두 0을 포함했다",
    "재현율@10(Recall@10)",
    "파레토 구성은 의미론적 정답에서 9개, 엄격한 정답에서 19개",
    "49.7% 상대 하락",
    "Spearman ρ는 0.383",
    "사전 승격 기준인 5쌍을 충족하지 못했다",
    "시내도로 +0.639",
    "교차로 +0.305",
    "버스 +0.8%포인트",
    "이륜차 −1.1%포인트",
    "RQ6에서는 4.3절과 5.1.3절에서 정의한 관련 클립 회수·검색 문맥 인식·과제 편향 통제의 세 단계 진단을 모두 적용했다",
    "보강 분석은 결과를 확인하기 전에",
    "10,594건과 21,509건",
    "2,112,000건과 1,186,364건",
    "['세 원천 분리 프로토콜' 사용 금지]",
    "비순환 평가 작업 부하 구성 절차 : 메타데이터 조건·검색 문서·검색 정답 집합",
    "검색 문서에 정답 라벨이 직접 포함되지 않았는지를 자동으로 확인한다",
    "검색 전 조건 적용 설명문",
    "의도적 열화 색인",
    # 제목 고정 (PI 지시 2026-08-10: 제출 제목 유지 — 접수양식·본문 각 1회, 총 2회 존재해야 함)
    "종단형 멀티모달 RAG 파이프라인 성능 향상을 위한 비순환 평가 및 검색 품질-비용에 대한 실증 연구",
    "An Empirical Study of Non-circular Evaluation and Retrieval Quality-Cost for Enhancing the Performance of End-to-End Multimodal RAG Pipeline",
]:
    check(f"manuscript contains '{required}'", required in text)

# 편집용 용어 표에는 구용어를 금지 항목으로 한 번 기록하되, 실제 논문 본문에서는 사용하지 않는다.
paper_body = text.split("\n---\n", 1)[1] if "\n---\n" in text else text

# 정확/열화 색인 용어는 조판 본문 첫 등장에만 영문을 병기하고 이후 한글로 고정한다.
index_term_definition = (
    "정확 색인(exact-search index)으로, "
    "IVF-PQ($nlist=1024$, $m=32$, 부분공간당 8비트, $nprobe=8$)를 "
    "의도적 열화 색인(intentionally degraded approximate index)으로 정의한다"
)
check(
    "paper body defines exact/degraded index terms once in Korean-first form",
    paper_body.count(index_term_definition) == 1
    and paper_body.find("정확 색인") == paper_body.find(index_term_definition),
)
check(
    "term table records the exact/degraded index style rule",
    "조판 본문의 첫 등장인 5.1.3절에서만 `한글 용어(영어 용어)`로 병기" in text,
)
check(
    "paper body identifies intentionally degraded index as a study-specific role",
    "의도적 열화 색인은 답변 전파 진단의 실험 역할명으로" in paper_body
    and "이 IVF-PQ 비교군에만 적용한다" in paper_body
    and "일반적인 근사 색인 계열의 명칭으로 확장하지 않는다" in paper_body,
)
check(
    "paper body uses each English index term exactly once",
    paper_body.count("exact-search index") == 1
    and paper_body.count("intentionally degraded approximate index") == 1,
)
index_term_tail = paper_body.split(index_term_definition, 1)[1] if index_term_definition in paper_body else ""
check(
    "paper body uses Korean-only index terms after the first definition",
    "exact-search index" not in index_term_tail
    and "intentionally degraded approximate index" not in index_term_tail,
)
check(
    "paper body contains no retired exact/degraded index variants",
    "degraded index" not in paper_body
    and "exact index" not in paper_body
    and "strong degradation" not in paper_body
    and "강열화 색인" not in paper_body
    and re.search(r"(?<!의도적 )열화 색인", paper_body) is None,
)

for token in ["아니라", "아닌", "아니며"]:
    check(
        f"paper body does NOT contain prohibited negative-contrast token '{token}'",
        token not in paper_body,
    )

for banned in [
    "과제-중립",
    "0.1700",
    "0.0855",
    "평균 생성 토큰",
    "110토큰 상한 도달 건수",
]:
    check(
        f"paper body does NOT contain retired prompt-sensitivity detail '{banned}'",
        banned not in paper_body,
    )
check(
    "paper body uses '과제-인지 프롬프트' only once as the 5.1.1 setup condition",
    paper_body.count("과제-인지 프롬프트") == 1,
)

rq1_results = paper_body.split("### 5.2.1.", 1)[1].split("### 5.2.2.", 1)[0]
check(
    "RQ1 results section does NOT contain prompt-sensitivity analysis",
    "프롬프트 민감도" not in rq1_results,
)
rq2_results = paper_body.split("### 5.2.2.", 1)[1].split("### 5.2.3.", 1)[0]
for retired_detail in [
    "설명문 생성 모델 비교",
    "UCA 54.04%",
    "엄격한 정답 기준에서는 검색 전 조건 적용이 벡터 단독 검색보다 nDCG@10을 0.161",
    "의미론적 정답 기준에서는 0.093 낮았다",
]:
    check(
        f"RQ2 results section does NOT contain non-core detail '{retired_detail}'",
        retired_detail not in rq2_results,
    )
rq3_results = paper_body.split("### 5.2.3.", 1)[1].split("### 5.2.4.", 1)[0]
check(
    "RQ3 uses one integrated three-column results table",
    rq3_results.count("**&lt;표 ") == 1
    and "| 분석 단계 | 비교 범위 | nDCG@10 또는 Δ [95% 신뢰구간] |" in rq3_results,
)
check(
    "RQ3 integrated table contains all four analysis stages",
    "**기본 계획 비교**" in rq3_results
    and "**질의 선정 방식 (관심 단서 Δ)**" in rq3_results
    and "**조건–의미 결합도 (관심 단서 Δ)**" in rq3_results
    and "**외부 데이터셋 비교 (Δ)**" in rq3_results,
)
check(
    "RQ3 table explicitly maps use purposes to relevance criteria",
    "필수 제약 (엄격한 정답, 85질의)" in rq3_results
    and "관심 단서 (의미론적 정답, 85질의)" in rq3_results,
)
rq3_table = rq3_results.split("| 분석 단계", 1)[1].split("**&lt;표 5&gt;", 1)[0]
check(
    "RQ3 external-comparison scope is moved from the table to prose",
    "| **외부 데이터셋 비교 (Δ)** | 필수 제약 |" in rq3_table
    and "|  | 관심 단서 |" in rq3_table
    and "필수 제약 (AI Hub 85질의" not in rq3_table
    and "관심 단서 (AI Hub 저결합 75질의" not in rq3_table,
)
for retired_table_field in [
    "| 결과 판정",
    "| 데이터셋·분석 범위",
    "| 분석 범위                            | 효과량 Δ",
    "| 사용 목적 | AI Hub 교차로",
]:
    check(
        f"RQ3 tables do NOT contain retired wide-layout field '{retired_table_field}'",
        retired_table_field not in rq3_results,
    )
for retired_detail in [
    "부트스트랩 p=0.024",
    "Wilcoxon",
    "10질의 중 7질의",
    "질의 수준 결합도 $V\\ge0.3$인 질의도 135개 중 3개",
    "최종 반환 문서 수가 부족",
    "Pre-filtering Drop",
    "순위가 정반대로",
    "교차 검증에서도 동일한",
    "의미론적 검색 품질이 저하될 수 있음을 재확인",
]:
    check(
        f"RQ3 results section does NOT contain non-core or misleading detail '{retired_detail}'",
        retired_detail not in rq3_results,
    )
check(
    "paper body reports prompt sensitivity exactly once as the 5.3 limitation",
    paper_body.count("프롬프트 민감도 대조") == 1
    and paper_body.count("49.7% 상대 하락") == 1,
)

kr_abstract_body = paper_body.split("## 요 약", 1)[1].split("**주제어", 1)[0]
en_abstract_body = paper_body.split("## Abstract", 1)[1].split("**Keywords", 1)[0]
conclusion_body = paper_body.split("# 6. 결론 및 향후 연구", 1)[1].split("# 참고 문헌", 1)[0]
for section_name, section_text in [
    ("Korean abstract", kr_abstract_body),
    ("English abstract", en_abstract_body),
    ("conclusion", conclusion_body),
]:
    check(
        f"{section_name} does NOT foreground prompt-sensitivity results",
        "프롬프트 민감도" not in section_text
        and "49.7%" not in section_text
        and "prompt independence" not in section_text,
    )

check(
    "paper body does NOT contain '세 원천 분리 프로토콜'",
    "세 원천 분리 프로토콜" not in paper_body,
)
check(
    "paper body does NOT contain banned term '수리'",
    "수리" not in paper_body,
)
check(
    "paper body does NOT contain banned term '엔진'",
    "엔진" not in paper_body,
)

# 2c) Abstract length & keyword-count rules (DBR: KR 300~500자, EN 100~200단어, 키워드 3~6개)
kr_m = re.search(r"## 요 약\n\n(.*?)\n\n\*\*주제어", text, re.S)
en_m = re.search(r"## Abstract\n\n(.*?)\n\n\*\*Keywords", text, re.S)
check("KR abstract section found", kr_m is not None)
check("EN abstract section found", en_m is not None)
if kr_m:
    kr = kr_m.group(1)
    check("KR abstract <=500 chars incl spaces", len(kr) <= 500, f"len={len(kr)}")
    check("KR abstract >=300 chars excl spaces", len(kr.replace(" ", "")) >= 300, f"len={len(kr.replace(' ', ''))}")
if en_m:
    en = en_m.group(1)
    check("EN abstract 100~200 words", 100 <= len(en.split()) <= 200, f"words={len(en.split())}")
kw_kr = re.search(r"\*\*주제어:\*\*(.*)", text)
kw_en = re.search(r"\*\*Keywords:\*\*(.*)", text)
for name, mm in [("KR keywords", kw_kr), ("EN keywords", kw_en)]:
    if mm:
        n_kw = len([k for k in mm.group(1).split(",") if k.strip()])
        check(f"{name} 3~6", 3 <= n_kw <= 6, f"n={n_kw}")
    else:
        check(f"{name} found", False)

# 2d) D1/D2 일관성: 본문에 '벡터' 없는 '데이터베이스 계층'과 용어로서의 '증거'가 없어야 함
import re as _re
bare_layer = [mtch.start() for mtch in _re.finditer(r"(?<!벡터 )데이터베이스 계층", text)]
check("no bare '데이터베이스 계층' (D1)", len(bare_layer) == 0, f"n={len(bare_layer)}")
ev_lines = [
    ln
    for ln in text.split("\n")
    if "증거" in ln
    and "[증거 i]" not in ln
    and "시스템 프롬프트는 `너는 CCTV 영상 증거를 분석하는 전문가다." not in ln
    and "구제목" not in ln
    and "증거 표현·색인" not in ln
]
check("no residual term '증거' (D2)", len(ev_lines) == 0, f"n={len(ev_lines)}")

# 2e) Title appears exactly twice (접수양식 + 본문) and no revised-title residue
check("KR title appears exactly 2x", text.count("종단형 멀티모달 RAG 파이프라인 성능 향상을 위한") == 2)
check("EN title appears exactly 2x", text.count("End-to-End Multimodal RAG Pipeline") == 2)
check("no revised-title residue", "멀티모달 영상 RAG 파이프라인을 위한" not in text and "Vector-Database-Layer" not in text)

# 2b) Citation/reference closure
body, refs = text.split("# 참고 문헌", maxsplit=1)
cited = {
    int(n)
    for group in re.findall(r"\[((?:\d+\s*,\s*)*\d+)\]", body)
    for n in re.findall(r"\d+", group)
}
declared = {int(n) for n in re.findall(r"(?m)^\[(\d+)\]", refs)}
check("references are contiguous [1]..[47]", declared == set(range(1, 48)), f"declared={sorted(declared)}")
check("every declared reference is cited in the body", declared <= cited, f"uncited={sorted(declared-cited)}")
check("body contains no undefined citation", cited <= declared, f"undefined={sorted(cited-declared)}")
check("invalid Holm DOI is absent", "doi:10.2307/4615733" not in refs)

# 본문에서 각 문헌이 처음 등장하는 순서가 참고문헌 번호 1→47과 일치해야 한다.
first_citation_order = []
for group in re.findall(r"\[((?:\d+\s*,\s*)*\d+)\]", body):
    for n in map(int, re.findall(r"\d+", group)):
        if n not in first_citation_order:
            first_citation_order.append(n)
check(
    "all references follow body first-appearance order",
    first_citation_order == list(range(1, 48)),
    f"order={first_citation_order}",
)
check(
    "first new reference is renumbered [16] Salemi-Zamani",
    re.search(r'(?m)^\[16\].*Salemi.*Zamani.*Evaluating Retrieval Quality', refs) is not None,
)
check(
    "second new reference is renumbered [17] Ramakrishnan et al.",
    re.search(r'(?m)^\[17\].*Ramakrishnan.*Overcoming Language Priors', refs) is not None,
)

# 3) Table 4 five storage configs vs canonical CSV
cfg_csv = PA / "20260717_joint_image_caption_validation" / "configuration_summary.csv"
expected_tbl4 = {
    "caption": (0.0626, 0.1810, 1.155, 1.488, 24.576),
    "representative_frame": (0.0625, 0.1865, 1.207, 1.529, 24.576),
    "joint_image_caption": (0.0794, 0.2182, 1.243, 1.574, 24.576),
    "multi_frame": (0.1014, 0.3518, 3.651, 4.274, 68.395),
    "dual": (0.0889, 0.2933, 4.959, 5.660, 92.971),
}
rows = {}
with cfg_csv.open() as f:
    for r in csv.DictReader(f):
        rows[(r["config"], r["scoring"])] = r
for name, (strict, sem, p50, p95, mb) in expected_tbl4.items():
    key = f"{name}__B2_vector__flat"
    s_row = rows.get((key, "strict"))
    m_row = rows.get((key, "semantic"))
    ok = (
        s_row is not None and m_row is not None
        and approx(s_row["ndcg_at_10"], strict)
        and approx(m_row["ndcg_at_10"], sem)
        and approx(m_row["latency_p50_ms"], p50, 5e-3)
        and approx(m_row["latency_p95_ms"], p95, 5e-3)
        and approx(m_row["vector_payload_mb"], mb, 5e-3)
    )
    check(
        f"Table4 {name} strict/semantic/p50/p95/MB",
        ok,
        f"expected {strict}/{sem}/{p50}/{p95}/{mb}",
    )

# 3b) Tables 5 and 6: RQ3 effects vs canonical CSV/JSON artifacts
t5_data = ROOT / "manuscript" / "table5_dir" / "data"
strict_plan_scores = {}
for line in (t5_data / "summary.md").read_text(encoding="utf-8").splitlines():
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if len(cells) == 7 and cells[0].startswith("B"):
        try:
            strict_plan_scores[cells[0]] = float(cells[-1])
        except ValueError:
            pass
for strategy, expected in [
    ("B2_vector_only", 0.059),
    ("B4_prefilter_vector", 0.157),
    ("B3_vector_postfilter", 0.152),
    ("B5_hybrid", 0.135),
]:
    check(
        f"RQ3 strict four-plan score {strategy}={expected:.3f}",
        strategy in strict_plan_scores
        and approx(strict_plan_scores[strategy], expected, 5e-4),
        f"actual={strict_plan_scores.get(strategy)}",
    )

semantic_plan_values = {}
with (t5_data / "metrics_semantic.csv").open() as f:
    for row in csv.DictReader(f):
        semantic_plan_values.setdefault(row["strategy"], []).append(float(row["ndcg_at_10"]))
for strategy, expected in [
    ("B2_vector_only", 0.170),
    ("B4_prefilter_vector", 0.154),
    ("B3_vector_postfilter", 0.150),
    ("B5_hybrid", 0.133),
]:
    values = semantic_plan_values.get(strategy, [])
    actual = sum(values) / len(values) if values else None
    check(
        f"RQ3 semantic four-plan score {strategy}={expected:.3f}",
        actual is not None and approx(actual, expected, 5e-4),
        f"actual={actual}",
    )

with (t5_data / "significance_expanded.csv").open() as f:
    t5_rows = {r["case"]: r for r in csv.DictReader(f)}
for case, expected_delta, expected_ci in [
    ("원본-32 (재현)", -0.0745, [-0.136, -0.014]),
    ("확장-신규 (독립 확인)", 0.0197, [-0.008, 0.050]),
    ("통합-85 (주 추정)", -0.0158, [-0.047, 0.015]),
]:
    row = t5_rows.get(case)
    actual_ci = json.loads(row["ci"]) if row else []
    check(
        f"Table5 source {case} delta/CI",
        row is not None
        and approx(row["delta"], expected_delta, 1e-6)
        and len(actual_ci) == 2
        and approx(actual_ci[0], expected_ci[0], 1e-6)
        and approx(actual_ci[1], expected_ci[1], 1e-6),
    )
t5_cluster = json.loads((t5_data / "t3_cluster_inference.json").read_text())
for band, expected_delta, expected_ci in [
    ("band V<0.3", -0.0357, [-0.0941, 0.0098]),
    ("band V>=0.3", 0.1335, [0.0780, 0.3559]),
]:
    row = t5_cluster[band]
    check(
        f"Table5 source {band} delta/cluster-CI",
        approx(row["mean"], expected_delta, 1e-6)
        and approx(row["cluster_ci"][0], expected_ci[0], 1e-6)
        and approx(row["cluster_ci"][1], expected_ci[1], 1e-6),
    )

t6_data = ROOT / "manuscript" / "table6_dir" / "data" / "20260712_uca_external"
t6 = json.loads((t6_data / "UCA_contrasts.json").read_text())
for key, node, expected_delta, expected_ci in [
    ("c1_strict_pooled_positive", "detail", 0.1501, [0.1235, 0.1790]),
    ("c2_semantic_container_negative", "detail", -0.0485, [-0.1300, 0.0210]),
    ("c4_label_gt_container_semantic", "label", -0.0558, [-0.1538, 0.0420]),
]:
    row = t6[key][node]
    check(
        f"Table6 source {key} delta/cluster-CI",
        approx(row["mean"], expected_delta, 1e-6)
        and approx(row["pair_ci"][0], expected_ci[0], 1e-6)
        and approx(row["pair_ci"][1], expected_ci[1], 1e-6),
    )
check(
    "Table6 source unfavorable-query count=68/129",
    t6["c3_negative_semantic_signs_exist"]["n_negative"] == 68
    and t6["c3_negative_semantic_signs_exist"]["n_semantic"] == 129,
)

for label, pattern in [
    ("initial sample", r"초기 수작업 표본 \(32질의\)\s*\|\s*−0\.0745 \[−0\.136, −0\.014\]"),
    ("additional sample", r"조건 조합 확장 표본 \(53질의\)\s*\|\s*\+0\.0197 \[−0\.008, \+0\.050\]"),
    ("combined sample", r"통합 표본 \(85질의\)\s*\|\s*−0\.0158 \[−0\.047, \+0\.015\]"),
    ("low coupling", r"저결합 V<0\.3 \(23쌍·75질의\)\s*\|\s*−0\.0357 \[−0\.094, \+0\.010\]"),
    ("high coupling", r"고결합 V≥0\.3 \(2쌍·10질의\)\s*\|\s*\+0\.1335 \[\+0\.078, \+0\.356\]"),
]:
    check(f"integrated RQ3 table row {label}", re.search(pattern, text) is not None)

# 4) RQ6 ladder accuracies (Qwen2.5-7B) vs official summary
sq = json.loads((ROOT / "experiments_expansion" / "rag_vqa" / "results_full" / "summary_qwen.json").read_text())
acc = sq["accuracy"]
for cond, val in [("closed", 0.3083), ("distractor", 0.5383), ("vector_only", 0.665), ("prefilter", 0.68), ("oracle", 0.7467)]:
    check(f"RQ6 ladder {cond}={val}", approx(acc[cond], val, 1e-4))
check("RQ6 n_per_config=600", sq["n_per_config"] == 600)

# 4b) Table 11: Llama ladder accuracies vs official summary
sl = json.loads((ROOT / "experiments_expansion" / "rag_vqa" / "results_full" / "summary_llama3.json").read_text())
for cond, val in [("closed", 0.3067), ("distractor", 0.5283), ("vector_only", 0.665), ("prefilter", 0.6667), ("oracle", 0.69)]:
    check(f"Table11 llama {cond}={val}", approx(sl["accuracy"][cond], val, 1e-4))

# 4c) Table 11: CI/대비 문자열 vs ladder_ci_analysis_20260723.json
ladder = json.loads((ROOT / "experiments_expansion" / "rag_vqa" / "results_full" / "ladder_ci_analysis_20260723.json").read_text())
def pct(x):
    return f"{x*100:.1f}"
for model_key, col in [("qwen2.5-7b", "qwen"), ("llama3-8b", "llama")]:
    for cond in ["closed", "distractor", "vector_only", "prefilter", "oracle"]:
        c = ladder[model_key]["conditions"][cond]
        s = f"{pct(c['acc'])} [{pct(c['ci95'][0])}, {pct(c['ci95'][1])}]"
        check(f"Table11 {col} {cond} acc+CI in text", s in text, s)
for model_key, col in [("qwen2.5-7b", "qwen"), ("llama3-8b", "llama")]:
    d = ladder[model_key]["paired_deltas"]["distractor-closed"]
    s = f"+{pct(d['delta'])} [{pct(d['ci95'][0])}, {pct(d['ci95'][1])}]"
    check(f"Table11 {col} distractor-closed delta+CI in text", s in text, s)

# 4d) 범주별 분해 (무관-없음 이득) vs percategory CSV
pc = ROOT / "manuscript" / "table11_dir" / "data" / "percategory_closed_distractor.csv"
gaps = {}
with pc.open() as f:
    for r in csv.DictReader(f):
        key = (r["model"], r["category"])
        gaps[key] = float(r["gap_pp"])
for (m, cat), expected in [(("qwen2.5-7b", "location"), 63.0), (("llama3-8b", "location"), 34.0),
                            (("qwen2.5-7b", "road type"), 40.0), (("llama3-8b", "road type"), 42.0),
                            (("qwen2.5-7b", "accident type"), -12.0), (("llama3-8b", "accident type"), -1.0)]:
    check(f"percategory {m}/{cat} gap={expected}", approx(gaps[(m, cat)], expected, 0.05))
for name, s in [
    ("separate diagnostic branches", "다만 세 단계는 동일한 데이터에서 연속 수행한 하나의 종단 실험이 아니다"),
    ("retrieval-gate stop", "따라서 두 코퍼스 모두 색인별 후속 답변 생성을 진행하지 않았다"),
    ("response-bias shift", "검색 문맥이 없을 때 Qwen2.5-7B-Instruct는 전체 600문항 중 42.0%에서 네 선택지 중 같은 위치의 답을 골랐다. 그 위치의 답이 정답인 문항은 21.2%였으며, 무관 설명문을 제공하자 같은 위치의 답을 고른 비율은 23.8%로 낮아졌다"),
    ("category directions", "장소·도로 유형 문항의 정확도는 Qwen2.5-7B-Instruct와 Llama-3-8B-Instruct에서 상승했고, 사고 유형 문항의 정확도는 Qwen2.5-7B-Instruct와 Llama-3-8B-Instruct에서 모두 하락했다"),
    ("bounded relevance interpretation", "다만 두 조건에서 제공한 설명문 수도 각각 3건과 1건으로 달라, 이 차이 전체를 설명문의 관련성만으로 해석할 수는 없다"),
    ("unestimated downstream effect", "따라서 본 결과만으로 색인 차이의 최종 답변 효과가 없다고 결론 내릴 수 없으며, 그 효과는 추정하지 못한 것으로 해석해야 한다"),
]:
    check(f"manuscript reports compact RQ6 {name}", s in text, s)

# 5) pgvector partial-index recall range 0.981~0.995 (sinnaedoro)
pv = PA / "20260713_db_design" / "pgvector_partial_vs_global.csv"
recalls = []
with pv.open() as f:
    for r in csv.DictReader(f):
        if r["strategy"].startswith("partial"):
            recalls.append(float(r["recall_at_10"]))
if recalls:
    check("partial-index recall min ~0.9812", approx(min(recalls), 0.9812, 2e-3), f"min={min(recalls):.4f}")
    check("partial-index recall max <= 0.9952+eps", max(recalls) <= 0.9962, f"max={max(recalls):.4f}")
else:
    check("partial-index rows found in pgvector_partial_vs_global.csv", False)

# 5b) Partial-index break-even examples vs hot/cold policy artifact
hc = PA / "20260713_db_design" / "hotcold_policy.csv"
breakeven = {}
with hc.open() as f:
    for r in csv.DictReader(f):
        breakeven[float(r["selectivity"])] = float(r["breakeven_queries_Nstar"])
for sel, expected in [(0.1829, 10593.5), (0.2601, 21509.1), (0.4734, 2112000.0), (0.7737, 1186363.6)]:
    check(
        f"partial-index break-even selectivity={sel}",
        sel in breakeven and approx(breakeven[sel], expected, 0.11),
        f"actual={breakeven.get(sel)} expected={expected}",
    )

# 6) Caption-model ablation delta on 522 (+0.1022)
abl = PA / "20260715_caption_model_ablation" / "retrieval_metrics_all_models.csv"
vals = {}
with abl.open() as f:
    for r in csv.DictReader(f):
        if r["dataset"] == "522" and r["scoring"] == "semantic" and r["strategy"] == "B2_vector_only":
            vals[r["model"]] = float(r["ndcg_at_10"])
q25, q35 = vals.get("qwen25vl_7b"), vals.get("qwen35_9b")
if q25 is not None and q35 is not None:
    check("ablation 522 delta +0.1022", approx(q35 - q25, 0.1022, 1e-3), f"delta={q35-q25:.4f}")
else:
    check("ablation rows located", False, f"models found: {sorted(vals)}")

# 6b) Caption-model paired deltas/CI and shared token-cap advisory reported in RQ2
paired_path = PA / "20260715_caption_model_ablation" / "paired_model_deltas.csv"
paired = {}
with paired_path.open() as f:
    for r in csv.DictReader(f):
        if (
            r["candidate"] == "qwen35_9b"
            and r["baseline"] == "qwen25vl_7b"
            and r["scoring"] == "semantic"
            and r["strategy"] == "B2_vector_only"
        ):
            paired[r["dataset"]] = (
                float(r["mean_delta_ndcg10"]),
                float(r["ci_lo"]),
                float(r["ci_hi"]),
            )
for dataset, expected, manuscript_fragment in [
    ("522", (0.1022, 0.0348, 0.1706), "+0.1022(95% 신뢰구간 [0.0348, 0.1706])"),
    ("meva", (0.1681, 0.1441, 0.1932), "MEVA +0.1681([0.1441, 0.1932])"),
    ("uca", (0.0540, 0.0151, 0.0920), "UCA +0.0540([0.0151, 0.0920])"),
]:
    actual = paired.get(dataset)
    check(
        f"ablation {dataset} paired delta/CI",
        actual is not None and all(approx(a, e, 1e-4) for a, e in zip(actual, expected)),
        f"actual={actual} expected={expected}",
    )
    check(
        f"manuscript reports ablation {dataset} delta/CI",
        manuscript_fragment in text,
        manuscript_fragment,
    )

caption_stats_path = PA / "20260715_caption_model_ablation" / "caption_generation_stats.csv"
q35_uca = None
with caption_stats_path.open() as f:
    for r in csv.DictReader(f):
        if r["model"] == "qwen35_9b" and r["dataset"] == "uca":
            q35_uca = int(r["token_limit_hit_count"])
            break
check("ablation UCA Qwen3.5 token-cap hits=3476", q35_uca == 3476, f"actual={q35_uca}")
check(
    "manuscript reports UCA Qwen3.5 token-cap rate=54.04%",
    "Qwen3.5-9B 설명문의 54.04%가 공통 110토큰 상한에 도달했다" in text,
)

# 7) Controlled supplement: artifact gates and exact manuscript-facing values
supp = PA / "20260723_controlled_supplement"
e0 = json.loads((supp / "e0_prompt_target_ablation" / "summary.json").read_text())
check("E0 aware nDCG=0.1700", approx(e0["primary"]["task_aware"], 0.170033, 1e-6))
check("E0 neutral nDCG=0.0855", approx(e0["primary"]["task_neutral"], 0.085508, 1e-6))
check("E0 relative drop=49.7%", approx(e0["primary"]["relative_drop"], 0.497109, 1e-6))
check("E0 adverse frozen gate passed", e0["adverse_prompt_sensitivity_large_by_frozen_rule"])

s2 = json.loads((supp / "s2_blocked_coupling" / "summary.json").read_text())
check("S2 rho=0.3826", approx(s2["primary_spearman"]["rho"], 0.382602, 1e-6))
check("S2 promotion gate failed", not s2["promotion_gate"]["all_pass"])
check(
    "S2 high-fold direction 5/5 positive",
    all(float(value) > 0 for value in s2["high_fold_mean_delta"].values()),
)

s3 = json.loads((supp / "s3_cluster_mechanism" / "combined_summary.json").read_text())
check("S3 all 2-corpus x 2-index cells pass", s3["all_four_cells_pass"])
for cell, expected in [
    ("A_hnsw", 0.638869),
    ("A_ivf", 0.676837),
    ("B_hnsw", 0.304548),
    ("B_ivf", 0.234416),
]:
    check(
        f"S3 {cell} natural-shuffle delta",
        approx(s3["cells"][cell]["natural_minus_shuffle_loss"], expected, 1e-6),
    )

s4 = json.loads((supp / "s4_retrieval_population" / "summary.json").read_text())
check("S4 eligible population=2739", s4["reconstruction"]["eligible_source_rows"] == 2739)
check(
    "S4 both task-relevant retrieval gates failed",
    not s4["categories"]["bus_count"]["retrieval_gate"]["all_pass"]
    and not s4["categories"]["bike_count"]["retrieval_gate"]["all_pass"],
)

n_fail = sum(1 for _, ok, _ in checks if not ok)
for name, ok, detail in checks:
    print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail and not ok else ""))
print(f"\ntotal={len(checks)} fail={n_fail}")
sys.exit(1 if n_fail else 0)
