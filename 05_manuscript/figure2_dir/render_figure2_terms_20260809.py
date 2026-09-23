#!/usr/bin/env python3
"""그림 2 재생성 (개정판 정본 용어 반영).

Figure2.png은 scripts/generate_manuscript_visuals_v6.py::figure_2_circularity()의
산출물과 바이트 동일함이 확인된 그림이다(figure2_dir/README.md). 정본 생성
스크립트가 AI Hub 교차로 통제 주입 결과만 표시하는지 확인한 뒤 그림을
재생성한다. 데이터와 팔레트는 동일하며, 원 아카이브
(paper_assets/20260717_manuscript_visuals_v6/)를 덮어쓰지 않도록 출력을 격리한다.

실행: python3 render_figure2_terms_20260809.py <출력디렉터리>
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
KIISE = HERE.parents[1]
SRC = KIISE / "04_scripts" / "09_paper_assets_and_build" / "generate_manuscript_visuals_v6.py"
if not SRC.exists():
    SRC = KIISE / "scripts" / "generate_manuscript_visuals_v6.py"
OUTDIR = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "out_terms_20260809"

code = SRC.read_text(encoding="utf-8")
assert "무작위 대조 조건" in code
assert "정답 조건 주입" in code
assert "정답 라벨\\n재진술 주입" in code
assert "정답 정보 미주입 기준 대비 Δ nDCG@10" in code
old_out = 'OUT = KIISE / "paper_assets" / "20260717_manuscript_visuals_v6"'
assert old_out in code
code = code.replace(old_out, f'OUT = Path({str(OUTDIR)!r})')

ns = {"__name__": "gen_visuals_terms_20260809", "__file__": str(SRC)}
exec(compile(code, str(SRC) + " (terms patched)", "exec"), ns)
ns["figure_2_circularity"]()
pngs = sorted(OUTDIR.glob("fig2_circularity*.png"))
assert pngs, "fig2 출력 없음"
print("saved:", *pngs)
