#!/usr/bin/env python3
"""v3 integration stage 1: insert the 6 drafts' blocks at their anchors,
clean annotations, resolve 표/그림 tokens to final numbers, add the 3 new
figure image lines, mark new [[ref:x]] citations for the stage-2 renumber.
Reference renumbering itself is stage 2 (integrate_v3_stage2_refs.py).

Input : manuscript v2 + manuscript/v3_working/named/{W*.md, W*.anchors.txt}
Output: manuscript/kiise_dbr_manuscript_v3.md  (+ diagnostics)
"""
from __future__ import annotations
import re
from pathlib import Path

R2 = Path(__file__).resolve().parents[1]
MS = R2 / "manuscript/kiise_dbr_manuscript_v2_noncircular.md"
WK = R2 / "manuscript/v3_working/named"
OUT = R2 / "manuscript/kiise_dbr_manuscript_v3.md"
FIGDIR = "2026_KIISE/paper_assets/20260712_v3_figures"

# ---- final numbering maps (body appearance order) ----
TBL = {"VALU차별성":1, "붕괴":2, "3채널예시":3, "데이터셋요약":4, "계산비용":5,
       "tri-source":6, "UCA판정":7, "M9":8, "pgvector":9, "전용엔진":10,
       "색인3축":11, "사다리":12, "가이드라인":14}   # 표13 = 두벽 (existing)
FIG = {"채널":1, "collapse":2, "결합도":3, "UCAscatter":4, "M9":5, "Pareto":6}

# new figure markdown (final concise captions; 표/그림 caption below image per DBR)
FIG_MD = {
 "collapse": (f"![⟦NF2⟧. 순환 워크로드의 붕괴(VRU, 전 전략 B0–B5, nDCG@10, n=85). "
   "회색은 v1(순환; 진단 목적으로만 인용), 진청은 수리 후 strict, 연청은 수리 후 semantic이다. "
   "붕괴 폭은 순환 노출 구조를 따라 층화된다: 필터·문서 채널의 순환을 모두 향유한 B3–B5가 0.647–0.688, "
   "문서 채널만 쓰는 B1–B2가 0.263–0.358, 문서 채널을 쓰지 않는 B0이 0.065다(strict 기준). "
   "제3 워크로드(522 tri-source)는 프로토콜로 처음부터 구축되어 v1 실행이 존재하지 않으므로 본 그림의 "
   f"대조 대상이 아니다.]({FIGDIR}/fig_collapse.png){{width=5.4in}}"),
 "UCAscatter": (f"![⟦NF4⟧. UCA 질의별 Δ(B4−B2, semantic 채점, nDCG@10) 대 값 수준 결합도"
   "(2×2 분할표에서 φ는 Cramér's V와 동치), 계층 색상(타이밍/컨테이너/라벨). 탐색적 결과다 — "
   "사전등록 판정은 대조 4건 중 3건 일치(표 7)이며 본 산점은 결합도–Δ 관계를 확증하지 않는다. "
   "라벨(class) 계층은 C1-재라벨링 계층으로, 고전적 prefilter 가치 재현의 근거로 인용하지 않는다.]"
   f"({FIGDIR}/fig_uca_scatter.png){{width=3.6in}}"),
 "M9": (f"![⟦NF5⟧. 실측 predicate와 동일-선택도 무작위 대조군의 짝지은 재현율 비교(방법×코퍼스). "
   "가로축은 무작위 대조군, 세로축은 실측 predicate의 재현율@10이며, 대각선 아래로의 수직 거리가 "
   "과대평가량이다. postfilter는 과잉 인출 폭 K′∈{1,2,4}× 계열을 겹쳐 그렸다. A는 predicate 29쌍, "
   f"B는 25쌍.]({FIGDIR}/fig_m9.png){{width=6.4in}}"),
}

def parse_anchors(p: Path):
    out = []
    for line in p.read_text().splitlines():
        m = re.match(r"ANCHOR:\s*(.*?)\s*==>\s*BLOCK:\s*(.*)$", line)
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
    return out

def clean_block(txt: str) -> str:
    txt = re.sub(r"【.*?】", "", txt, flags=re.S)              # drop src/note braces
    txt = re.sub(r"<!--.*?-->", "", txt, flags=re.S)          # drop html comments
    # drop writer meta lines
    keep = []
    for ln in txt.splitlines():
        s = ln.strip()
        if s.startswith(("## 삽입 블록", "캡션 초안", "(캡션 초안", "(캡션", "통합자 주",
                         "비고(", "통합자 참고", "1순위:", "2순위:", "3순위:")):
            continue
        keep.append(ln)
    txt = "\n".join(keep)
    # resolve table tokens to NEW-number sentinels (converted to '표 N' last)
    for name, n in TBL.items():
        txt = txt.replace(f"[[표:{name}]]", f"⟦NT{n}⟧")
    # figure tokens: a line that is ONLY [[그림:x]] -> image markdown; inline -> sentinel
    lines = []
    for ln in txt.splitlines():
        st = ln.strip()
        fig_only = re.fullmatch(r"\[\[그림:([^\]]+)\]\]", st)
        if fig_only and fig_only.group(1) in FIG_MD:
            lines.append(FIG_MD[fig_only.group(1)])
            continue
        for name, n in FIG.items():
            ln = ln.replace(f"[[그림:{name}]]", f"⟦NF{n}⟧")
        lines.append(ln)
    txt = "\n".join(lines)
    # mark new refs for stage 2
    txt = re.sub(r"\[\[ref:([a-z0-9\-]+)\]\]", r"⟦REF:\1⟧", txt)
    # collapse >2 blank lines, trim
    txt = re.sub(r"\n{3,}", "\n\n", txt).strip()
    return txt

def block_span(draft: str, cur_words: str, nxt_words: str | None) -> str:
    i = draft.find(cur_words)
    assert i >= 0, f"block start not found: {cur_words[:40]!r}"
    if nxt_words:
        j = draft.find(nxt_words, i + len(cur_words))
        assert j >= 0, f"next block start not found: {nxt_words[:40]!r}"
        return draft[i:j]
    return draft[i:]

def main():
    ms = MS.read_text()
    diagnostics = []
    for W in ["W1-intro-related", "W2-protocol-casestudy", "W3-datasets",
              "W4-exp1-uca", "W5-exp2", "W6-exp3-discussion"]:
        draft = (WK / f"{W}.md").read_text()
        anchors = parse_anchors(WK / f"{W}.anchors.txt")
        for k, (anchor, words) in enumerate(anchors):
            nxt = anchors[k+1][1] if k+1 < len(anchors) else None
            # trailer sentinels that mark end of the last block
            block = block_span(draft, words, nxt)
            block = clean_block(block)
            if not block:
                diagnostics.append(f"[skip empty] {W} #{k+1}")
                continue
            if anchor not in ms:
                diagnostics.append(f"[ANCHOR MISS] {W} #{k+1}: {anchor[:60]!r}")
                continue
            if ms.count(anchor) != 1:
                diagnostics.append(f"[ANCHOR x{ms.count(anchor)}] {W} #{k+1}: {anchor[:50]!r}")
                continue
            ms = ms.replace(anchor, anchor + "\n\n" + block, 1)
            diagnostics.append(f"[ok] {W} #{k+1} ({len(block)} ch) after {anchor[:34]!r}")

    # ---- renumber EXISTING hard 표/그림 numbers ----
    # At this point new-block numbers are ⟦NT#⟧/⟦NF#⟧ sentinels, so only the
    # original manuscript's plain '표 N'/'그림 N' are touched here.
    # existing tables: 표1->2, 표2->6, 표3->8, 표4->9, 표5->10, 표6->13
    for old, new in [(6,13),(5,10),(4,9),(3,8),(2,6),(1,2)]:
        ms = ms.replace(f"표 {old}", f"⟦T{new}⟧")
    ms = re.sub(r"⟦T(\d+)⟧", r"표 \1", ms)
    # existing figures: 그림2->3, 그림3->6 (그림1 stays)
    for old, new in [(3,6),(2,3)]:
        ms = ms.replace(f"그림 {old}", f"⟦F{new}⟧")
    ms = re.sub(r"⟦F(\d+)⟧", r"그림 \1", ms)
    # NOW convert new-block sentinels to final numbers
    ms = re.sub(r"⟦NT(\d+)⟧", r"표 \1", ms)
    ms = re.sub(r"⟦NF(\d+)⟧", r"그림 \1", ms)

    # ---- explicit audit/critic fixes ----
    fixes = [
     # W1 block2: 확증/탐색적 taxonomy broadened (audit-claim-W1 MAJOR)
     ("사전등록 검정 가족에서 유의한 결과는 **확증**으로, 조작 실패처럼 직접 실측으로 성립한 결과는 **확립 관찰**로, 신뢰구간이 0을 포함해 방향 가설로만 제시하는 결과는 **탐색적**으로, 파일럿 근거의 병목 후보는 **가설적**으로 표기한다(예: 6절의 결합도 곡선은 탐색적이고, 8절의 매개변수 벽은 확립 관찰, 지각 벽은 가설적이다). 이 구분은 수사가 아니라 사전등록·중단 규칙·기계 감사로 강제되는 보고 원칙이다(부록 A).",
      "본 실험군의 사전등록 Holm 검정 가족에서 유의한 결과는 **확증**으로, 조작 실패처럼 직접 실측으로 성립한 결과는 **확립 관찰**로, 방향 가설로만 제시하는 결과(신뢰구간이 0을 포함하거나 외적 타당성 이식처럼 개별 대조의 CI와 무관하게 설계상 탐색인 경우)는 **탐색적**으로, 파일럿 근거의 병목 후보는 **가설적**으로 표기한다(예: 6절의 결합도 곡선과 UCA 이식은 탐색적, 8절의 매개변수 벽은 확립 관찰, 지각 벽은 가설적이다). 이 구분은 수사가 아니라 사전등록 검정 가족·중단 규칙·군집 추론 규칙에 근거해 부여되는 보고 원칙이다(부록 A)."),
     # W1 block3: Milvus prefilter/single-stage reconciliation (audit MINOR)
     ("전용 엔진 Milvus는 비트셋 기반 prefilter를 네이티브 경로로 채택하고[[ref:milvus]]",
      "전용 엔진 Milvus는 predicate를 먼저 평가해 얻은 비트셋을 그래프 탐색 내부에서 적용하는 네이티브 경로(엔진 용어로는 prefilter, 본 분류로는 단일 단계 계열)를 채택하고[[ref:milvus]]"),
     # W1 block4: parked mechanism distinction (audit MINOR, 불변 조항 7)
     ("캡션 품질이 다운스트림을 좌우한다는 점에서 본 연구의 문서 채널 맹점 분석(6·9절)과 같은 축의 발견이다",
      "캡션 표현이 다운스트림 판별을 좌우한다는 점에서 같은 축의 발견이다 — 단, 본 연구의 맹점은 서술 누락이 아니라 과언급·부정 표현의 혼동이다(6절)"),
    ]
    for a, b in fixes:
        # the marker form ⟦REF:milvus⟧ replaced [[ref:milvus]] already; adjust fix strings
        a2 = a.replace("[[ref:milvus]]", "⟦REF:milvus⟧")
        b2 = b.replace("[[ref:milvus]]", "⟦REF:milvus⟧")
        if a2 in ms:
            ms = ms.replace(a2, b2, 1)
            diagnostics.append(f"[fix ok] {a2[:40]!r}")
        else:
            diagnostics.append(f"[FIX MISS] {a2[:50]!r}")

    # existing L143 "M9" leak -> plain wording
    if "M9" in ms:
        ms = ms.replace("(M9 과대평가)", "(과대평가)").replace("M9 대조", "무작위 대조")
        diagnostics.append("[note] residual 'M9' occurrences: %d" % ms.count("M9"))

    OUT.write_text(ms)
    (R2/"manuscript/v3_working/stage1_diagnostics.txt").write_text("\n".join(diagnostics))
    n_ok = sum(1 for d in diagnostics if d.startswith("[ok]"))
    n_bad = sum(1 for d in diagnostics if "MISS" in d or "x2" in d or "x0" in d)
    print(f"inserted {n_ok} blocks; problems={n_bad}")
    print("remaining tokens:",
          "표:[[", ms.count("[[표"), " 그림:[[", ms.count("[[그림"),
          " ⟦REF⟧:", len(re.findall(r"⟦REF:", ms)),
          " raw [[ref:", ms.count("[[ref:"))
    for d in diagnostics:
        if "MISS" in d or "x2" in d or "x0" in d or d.startswith("[skip"):
            print("  ", d)

if __name__ == "__main__":
    main()
