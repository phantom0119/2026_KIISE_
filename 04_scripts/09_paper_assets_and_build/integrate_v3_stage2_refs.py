#!/usr/bin/env python3
"""v3 integration stage 2: IEEE first-appearance reference renumbering.

Handles: existing [N] citations + new ⟦REF:key⟧ markers. Canonicalizes
'acorn' -> existing entry [23] (moved-not-new). Protects the 4 hour-range
brackets ([06,18],[11,14],[17,19],[8,18]) that look like citation groups.
Rewrites body citations and rebuilds the reference list in new order.
"""
from __future__ import annotations
import re
from pathlib import Path

R2 = Path(__file__).resolve().parents[2]
F = R2 / "manuscript/kiise_dbr_manuscript_v3.md"
HOUR = {"[06,18]", "[11,14]", "[17,19]", "[8,18]"}
CANON = {"acorn": "23"}   # acorn citation == existing entry [23]
CITE = re.compile(r"⟦REF:([a-z0-9\-]+)⟧|\[(\d{1,2}(?:,\d{1,2})*)\]")

def main():
    ms = F.read_text()
    head, refsec = ms.split("## 참고문헌", 1)
    # reference list lines (after '## 참고문헌'), tail = 부록 onward
    lines = refsec.splitlines()
    # find where 부록 starts
    tail_idx = next((i for i, l in enumerate(lines) if l.startswith("## 부록")), len(lines))
    reflines = lines[1:tail_idx]           # skip the blank after header
    tail = "\n".join(lines[tail_idx:])

    # ---- build entry map: canonical old-id -> text (without leading tag) ----
    entry = {}
    for l in reflines:
        l = l.strip()
        if not l:
            continue
        m = re.match(r"\[(\d+)\]\s+(.*)", l)
        if m:
            entry[m.group(1)] = m.group(2)
            continue
        m = re.match(r"⟦REF:([a-z0-9\-]+)⟧\s+(.*)", l)
        if m:
            entry[m.group(1)] = m.group(2)
    assert len(entry) == 31, f"expected 31 entries, got {len(entry)}"

    # ---- first-appearance scan over body (head) ----
    order = []
    seen = set()
    def note(cid):
        if cid not in seen:
            seen.add(cid); order.append(cid)
    for m in CITE.finditer(head):
        if m.group(1):                      # ⟦REF:key⟧
            note(CANON.get(m.group(1), m.group(1)))
        else:
            if m.group(0) in HOUR:
                continue
            for d in m.group(2).split(","):
                note(d)
    # any entry never cited? (shouldn't happen) -> append at end
    for k in entry:
        note(k)
    assert len(order) == 31, f"order has {len(order)} ids"
    newnum = {cid: i + 1 for i, cid in enumerate(order)}

    # ---- rewrite body citations ----
    def repl(m):
        if m.group(1):
            cid = CANON.get(m.group(1), m.group(1))
            return f"[{newnum[cid]}]"
        if m.group(0) in HOUR:
            return m.group(0)
        nums = [newnum[d] for d in m.group(2).split(",")]
        return "[" + ",".join(str(n) for n in nums) + "]"
    new_head = CITE.sub(repl, head)

    # ---- rebuild reference list in new order ----
    inv = {v: k for k, v in newnum.items()}
    out = ["## 참고문헌", ""]
    for n in range(1, 32):
        out.append(f"[{n}] {entry[inv[n]]}")
    new_ref = "\n".join(out)

    F.write_text(new_head.rstrip() + "\n\n" + new_ref + "\n\n" + tail)
    # report
    changed = [(inv[n], n) for n in range(1, 32) if inv[n] != str(n)]
    print(f"renumbered {len(order)} refs; {len(changed)} moved")
    print("old->new (moved only):")
    for old, new in changed:
        print(f"  {old:>18} -> {new}")
    # sanity: no residual markers, citations within range
    assert "⟦REF" not in F.read_text(), "residual REF marker!"
    print("no residual ⟦REF⟧ markers.")

if __name__ == "__main__":
    main()
