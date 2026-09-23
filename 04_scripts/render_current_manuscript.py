#!/usr/bin/env python3
"""Render the current revision Markdown without regenerating its contents."""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

import _dbr_complete_working_draft_base as formatter


MANUSCRIPT_DIR = ROOT / "2026_KIISE" / "manuscript"
SOURCE = MANUSCRIPT_DIR / "kiise_dbr_manuscript_v6_submission_revision.md"
OUTPUT_DOCX = (
    MANUSCRIPT_DIR / "kiise_dbr_manuscript_v6_submission_revision_visuals.docx"
)
OUTPUT_PDF = (
    MANUSCRIPT_DIR / "kiise_dbr_manuscript_v6_submission_revision_visuals.pdf"
)
CANONICAL_DOCX = (
    MANUSCRIPT_DIR / "kiise_dbr_manuscript_v6_submission_revision.docx"
)
CANONICAL_PDF = (
    MANUSCRIPT_DIR / "kiise_dbr_manuscript_v6_submission_revision.pdf"
)
REFERENCE_DOCX = (
    ROOT
    / "2026_KIISE"
    / "paper_assets"
    / "20260718_manuscript_build_support"
    / "dbr_current_visual_reference.docx"
)


def titles(markdown: str) -> tuple[str, str]:
    lines = [line.strip() for line in markdown.splitlines()]
    heading_indexes = [i for i, line in enumerate(lines) if line.startswith("# ")]
    if not heading_indexes:
        raise RuntimeError("Korean title heading was not found")
    first = heading_indexes[0]
    korean = lines[first][2:].strip()
    english = next(
        line
        for line in lines[first + 1 :]
        if line and not line.startswith(("#", "|", "["))
    )
    return korean, english


def validate_markdown(markdown: str) -> None:
    table_numbers = [
        int(value) for value in re.findall(r"(?m)^\*\*\\<표 (\d+)\\>", markdown)
    ]
    figure_numbers = [
        int(value) for value in re.findall(r"\\<그림 (\d+)\\>", markdown)
    ]
    if table_numbers != list(range(1, len(table_numbers) + 1)):
        raise RuntimeError(f"table numbering is not sequential: {table_numbers}")
    if figure_numbers != list(range(1, len(figure_numbers) + 1)):
        raise RuntimeError(f"figure numbering is not sequential: {figure_numbers}")
    if markdown.count(formatter.WIDE_START) != markdown.count(formatter.WIDE_END):
        raise RuntimeError("full-width section markers are unbalanced")


def main() -> None:
    markdown = SOURCE.read_text(encoding="utf-8")
    validate_markdown(markdown)
    korean_title, english_title = titles(markdown)

    formatter.OUT_MD = SOURCE
    formatter.OUT_DOCX = OUTPUT_DOCX
    formatter.OUT_PDF = OUTPUT_PDF
    formatter.REF_DOCX = REFERENCE_DOCX
    formatter.KOR_TITLE = korean_title
    formatter.ENG_TITLE = english_title
    formatter.DOC_FONT_KR = "NanumMyeongjo"
    formatter.DOC_FONT_LATIN = "Liberation Serif"

    REFERENCE_DOCX.parent.mkdir(parents=True, exist_ok=True)
    formatter.create_reference_docx()
    formatter.build_initial_docx()
    formatter.polish_docx()
    formatter.build_pdf()
    shutil.copy2(OUTPUT_DOCX, CANONICAL_DOCX)
    shutil.copy2(OUTPUT_PDF, CANONICAL_PDF)
    print(f"source: {SOURCE}")
    print(f"docx: {OUTPUT_DOCX}")
    print(f"pdf: {OUTPUT_PDF}")
    print(f"canonical docx: {CANONICAL_DOCX}")
    print(f"canonical pdf: {CANONICAL_PDF}")


if __name__ == "__main__":
    main()
