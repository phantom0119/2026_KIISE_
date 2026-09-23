#!/usr/bin/env python3
"""Build a DBR review-manuscript package from the current Markdown draft.

The format follows the DBR "심사용 논문 작성 규정" checked on 2026-07-07:
- HWP or MS Word, A4, within 20 pages.
- No acknowledgments in the review manuscript.
- First page: Korean/English title, Korean/English authors, affiliation,
  position, detailed field, corresponding author contact.
- From the next page: no author/affiliation, title including English title,
  Korean abstract/keywords, English abstract/keywords, body, references,
  appendix if any.
- Font sizes: Korean title 18 pt, English title 12 pt, authors 8 pt,
  abstract title 12 pt, abstract/body text 9 pt, body headings 12 pt.
"""

from __future__ import annotations

import re
import subprocess
import json
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor, Twips


PROJECT_ROOT = Path(__file__).resolve().parents[3]
PACKAGE_ROOT = PROJECT_ROOT / "2026_KIISE"
MANUSCRIPT_DIR = PACKAGE_ROOT / "manuscript"

SRC_MD = MANUSCRIPT_DIR / "kiise_dbr_manuscript_v1_true_multimodal.md"
OUT_MD = MANUSCRIPT_DIR / "kiise_dbr_manuscript_v1_true_multimodal_DBR_review.md"
REF_DOCX = MANUSCRIPT_DIR / "dbr_review_reference_20260707.docx"
OUT_DOCX = MANUSCRIPT_DIR / "kiise_dbr_manuscript_v1_true_multimodal_DBR_review.docx"
OUT_PDF = MANUSCRIPT_DIR / "kiise_dbr_manuscript_v1_true_multimodal_DBR_review.pdf"
AUTHOR_INFO_JSON = MANUSCRIPT_DIR / "dbr_author_info_20260707.json"
TEMPLATE_MD = MANUSCRIPT_DIR / "dbr_review_template_20260707.md"
TEMPLATE_DOCX = MANUSCRIPT_DIR / "dbr_review_template_20260707.docx"

KOR_TITLE = "도시 교통·감시형 멀티모달 데이터베이스에서 시각-텍스트-메타데이터 Evidence 검색과 선택 구조의 성능 분석"
ENG_TITLE = (
    "Performance Analysis of Visual-Text-Metadata Evidence Retrieval and "
    "Selection in Urban Traffic and Surveillance Multimodal Databases"
)

FONT_KR = "Noto Sans CJK KR"
FONT_LATIN = "Times New Roman"
PAGE_BREAK_MARKER = "[DBR_PAGE_BREAK]"

DEFAULT_AUTHOR_INFO = {
    "kor_author_names": "[국문 저자명 입력]",
    "eng_author_names": "[English Author Name]",
    "kor_affiliation_position": "[국문 소속기관, 부서, 직위 입력]",
    "eng_affiliation_position": "[English affiliation, department, position]",
    "detailed_field": "데이터베이스, 정보검색, 멀티모달 데이터 관리",
    "corresponding_author_name": "[교신저자명 입력]",
    "corresponding_author_address": "[주소 입력]",
    "postal_code": "[우편번호 입력]",
    "phone": "[전화번호 입력]",
    "fax": "[FAX 번호 입력 또는 해당 없음]",
    "email": "[교신저자 이메일 입력]",
}


def set_run_font(run, size_pt: float | None = None, bold: bool | None = None) -> None:
    run.font.name = FONT_LATIN
    if size_pt is not None:
        run.font.size = Pt(size_pt)
    if bold is not None:
        run.bold = bold
    run.font.color.rgb = RGBColor(0, 0, 0)
    r_pr = run._element.get_or_add_rPr()
    r_fonts = r_pr.rFonts
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    r_fonts.set(qn("w:ascii"), FONT_LATIN)
    r_fonts.set(qn("w:hAnsi"), FONT_LATIN)
    r_fonts.set(qn("w:eastAsia"), FONT_KR)


def set_style_font(style, size_pt: float, bold: bool = False) -> None:
    style.font.name = FONT_LATIN
    style.font.size = Pt(size_pt)
    style.font.bold = bold
    style.font.color.rgb = RGBColor(0, 0, 0)
    r_pr = style.element.get_or_add_rPr()
    r_fonts = r_pr.rFonts
    if r_fonts is None:
        r_fonts = OxmlElement("w:rFonts")
        r_pr.append(r_fonts)
    r_fonts.set(qn("w:ascii"), FONT_LATIN)
    r_fonts.set(qn("w:hAnsi"), FONT_LATIN)
    r_fonts.set(qn("w:eastAsia"), FONT_KR)


def configure_section(section) -> None:
    section.page_width = Cm(21.0)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.0)
    section.bottom_margin = Cm(2.0)
    section.left_margin = Cm(2.0)
    section.right_margin = Cm(2.0)


def create_reference_docx() -> None:
    doc = Document()
    configure_section(doc.sections[0])

    style_specs = {
        "Normal": (9, False),
        "Body Text": (9, False),
        "Compact": (9, False),
        "Title": (18, True),
        "Subtitle": (12, True),
        "Author": (8, False),
        "Date": (8, False),
        "Abstract": (9, False),
        "Heading 1": (12, True),
        "Heading 2": (12, True),
        "Heading 3": (12, True),
        "Heading 4": (12, True),
        "Caption": (9, False),
        "Table Caption": (9, False),
        "Image Caption": (9, False),
        "Bibliography": (9, False),
    }
    for name, (size, bold) in style_specs.items():
        if name in doc.styles:
            set_style_font(doc.styles[name], size, bold)

    sample = doc.add_paragraph("DBR review reference style document")
    sample.alignment = WD_ALIGN_PARAGRAPH.CENTER
    for run in sample.runs:
        set_run_font(run, 9)
    doc.save(REF_DOCX)


def add_formatted_paragraph(
    doc: Document,
    text: str,
    size_pt: float,
    bold: bool = False,
    align=WD_ALIGN_PARAGRAPH.LEFT,
) -> None:
    para = doc.add_paragraph()
    para.alignment = align
    para.paragraph_format.space_before = Pt(0)
    para.paragraph_format.space_after = Pt(0)
    para.paragraph_format.line_spacing = 1.0
    run = para.add_run(text)
    set_run_font(run, size_pt, bold)


def create_blank_template() -> None:
    TEMPLATE_MD.write_text(
        """# [국문 제목]

[English Title]

국문 저자명: [국문 저자명 입력]

영문 저자명: [English Author Name]

소속기관 및 직위: [국문 소속기관, 부서, 직위 입력]

Affiliation and Position: [English affiliation, department, position]

논문의 세부분야: [세부분야 입력]

교신저자 성명: [교신저자명 입력]

교신저자 주소: [주소 입력]

우편번호: [우편번호 입력]

전화번호: [전화번호 입력]

FAX 번호: [FAX 번호 입력 또는 해당 없음]

E-mail: [교신저자 이메일 입력]

비고: 심사용 원고에는 감사의 글을 포함하지 않음.

[DBR_PAGE_BREAK]

# [국문 제목]

[English Title]

## 초록

[국문 요약 300~500자]

주요어: [국문 키워드 3~6개]

## Abstract

[English abstract 100~200 words]

Keywords: [English keywords 3~6]

## 1. 서론

[본문]

## 2. 관련 연구

### 2.1 [절 제목]

[본문]

## 3. 연구 방법

**\\<표 1\\> [표 제목]**

| 항목 | 설명 |
|---|---|
| [항목] | [설명] |

![\\<그림 1\\> [그림 제목]]([그림 파일 경로])

## 4. 실험 결과

[본문]

## 5. 결론

[본문]

## 참고문헌

[1] [참고문헌을 본문 인용 순서대로 기술]
""",
        encoding="utf-8",
    )

    doc = Document()
    configure_section(doc.sections[0])
    for name, (size, bold) in {
        "Normal": (9, False),
        "Title": (18, True),
        "Subtitle": (12, True),
        "Heading 1": (12, True),
        "Heading 2": (12, True),
        "Heading 3": (12, True),
    }.items():
        if name in doc.styles:
            set_style_font(doc.styles[name], size, bold)

    add_formatted_paragraph(doc, "[국문 제목]", 18, True, WD_ALIGN_PARAGRAPH.CENTER)
    add_formatted_paragraph(doc, "[English Title]", 12, True, WD_ALIGN_PARAGRAPH.CENTER)
    for line in [
        "국문 저자명: [국문 저자명 입력]",
        "영문 저자명: [English Author Name]",
        "소속기관 및 직위: [국문 소속기관, 부서, 직위 입력]",
        "Affiliation and Position: [English affiliation, department, position]",
        "논문의 세부분야: [세부분야 입력]",
        "교신저자 성명: [교신저자명 입력]",
        "교신저자 주소: [주소 입력]",
        "우편번호: [우편번호 입력]",
        "전화번호: [전화번호 입력]",
        "FAX 번호: [FAX 번호 입력 또는 해당 없음]",
        "E-mail: [교신저자 이메일 입력]",
        "비고: 심사용 원고에는 감사의 글을 포함하지 않음.",
    ]:
        add_formatted_paragraph(doc, line, 8)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)
    add_formatted_paragraph(doc, "[국문 제목]", 18, True, WD_ALIGN_PARAGRAPH.CENTER)
    add_formatted_paragraph(doc, "[English Title]", 12, True, WD_ALIGN_PARAGRAPH.CENTER)
    for heading, body in [
        ("초록", "[국문 요약 300~500자]"),
        ("Abstract", "[English abstract 100~200 words]"),
        ("1. 서론", "[본문]"),
        ("2. 관련 연구", "[본문]"),
        ("3. 연구 방법", "[본문]"),
        ("4. 실험 결과", "[본문]"),
        ("5. 결론", "[본문]"),
        ("참고문헌", "[1] [참고문헌을 본문 인용 순서대로 기술]"),
    ]:
        add_formatted_paragraph(doc, heading, 12, True)
        add_formatted_paragraph(doc, body, 9)

    doc.save(TEMPLATE_DOCX)


def strip_draft_header(text: str) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    skip_prefix = True
    for line in lines:
        if skip_prefix:
            if line.startswith("## 초록"):
                skip_prefix = False
                kept.append(line)
            continue
        kept.append(line)
    return "\n".join(kept).strip() + "\n"


def normalize_figure_paths(text: str) -> str:
    # Pandoc is executed from ROOT, so existing project-relative paths are valid.
    return text


def normalize_dbr_captions(text: str) -> str:
    text = re.sub(r"\*\*표\s+(\d+)\.\s*(.*?)\*\*", r"**\\<표 \1\\> \2**", text)
    text = re.sub(r"!\[그림\s+(\d+)\.\s*(.*?)\]\(", r"![\\<그림 \1\\> \2](", text)
    return text


def load_author_info() -> dict[str, str]:
    if not AUTHOR_INFO_JSON.exists():
        AUTHOR_INFO_JSON.write_text(
            json.dumps(DEFAULT_AUTHOR_INFO, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return DEFAULT_AUTHOR_INFO

    loaded = json.loads(AUTHOR_INFO_JSON.read_text(encoding="utf-8"))
    merged = DEFAULT_AUTHOR_INFO.copy()
    for key, value in loaded.items():
        if key in merged and str(value).strip():
            merged[key] = str(value).strip()
    return merged


def build_review_markdown() -> None:
    body = strip_draft_header(SRC_MD.read_text(encoding="utf-8"))
    body = normalize_figure_paths(body)
    body = normalize_dbr_captions(body)
    author = load_author_info()

    front_page = f"""# {KOR_TITLE}

{ENG_TITLE}

국문 저자명: {author["kor_author_names"]}

영문 저자명: {author["eng_author_names"]}

소속기관 및 직위: {author["kor_affiliation_position"]}

Affiliation and Position: {author["eng_affiliation_position"]}

논문의 세부분야: {author["detailed_field"]}

교신저자 성명: {author["corresponding_author_name"]}

교신저자 주소: {author["corresponding_author_address"]}

우편번호: {author["postal_code"]}

전화번호: {author["phone"]}

FAX 번호: {author["fax"]}

E-mail: {author["email"]}

비고: 심사용 원고에는 감사의 글을 포함하지 않음.

{PAGE_BREAK_MARKER}

# {KOR_TITLE}

{ENG_TITLE}

"""
    OUT_MD.write_text(front_page + body, encoding="utf-8")


def paragraph_text(paragraph) -> str:
    return re.sub(r"\s+", " ", paragraph.text).strip()


def enforce_paragraph_format(doc: Document) -> None:
    for section in doc.sections:
        configure_section(section)

    for para in doc.paragraphs:
        text = paragraph_text(para)
        para.paragraph_format.space_before = Pt(0)
        para.paragraph_format.space_after = Pt(0)
        para.paragraph_format.line_spacing = 1.0

        if PAGE_BREAK_MARKER in text:
            para.clear()
            para.add_run().add_break(WD_BREAK.PAGE)
            continue

        if text == KOR_TITLE:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.paragraph_format.space_after = Pt(6)
            for run in para.runs:
                set_run_font(run, 18, True)
            continue

        if text == ENG_TITLE:
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            para.paragraph_format.space_after = Pt(6)
            for run in para.runs:
                set_run_font(run, 12, True)
            continue

        if text in {"초록", "Abstract"}:
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT
            for run in para.runs:
                set_run_font(run, 12, True)
            continue

        if para.style and para.style.name.startswith("Heading"):
            para.paragraph_format.space_before = Pt(6)
            para.paragraph_format.space_after = Pt(3)
            for run in para.runs:
                set_run_font(run, 12, True)
            continue

        # First-page author/contact lines are explicitly required by DBR.
        if any(
            text.startswith(prefix)
            for prefix in [
                "국문 저자명:",
                "영문 저자명:",
                "소속기관 및 직위:",
                "Affiliation and Position:",
                "논문의 세부분야:",
                "교신저자 성명:",
                "교신저자 주소:",
                "우편번호:",
                "전화번호:",
                "FAX 번호:",
                "E-mail:",
                "비고:",
            ]
        ):
            for run in para.runs:
                set_run_font(run, 8, False)
            continue

        for run in para.runs:
            set_run_font(run, 9, run.bold)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    para.paragraph_format.space_before = Pt(0)
                    para.paragraph_format.space_after = Pt(0)
                    para.paragraph_format.line_spacing = 1.0
                    for run in para.runs:
                        set_run_font(run, 9, run.bold)


def rebuild_tables_native(doc: Document) -> None:
    """Replace pandoc's grid-less tables with native 'Table Grid' tables.

    Pandoc 2.x emits pipe tables without a <w:tblGrid>; this LibreOffice
    version then collapses every column, stacking each cell on its own line
    and inflating the page count. We extract the cell text/alignment and
    rebuild each table natively with proportional, content-based column
    widths so it renders as a proper grid.
    """
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    body = doc.element.body
    usable = 9360  # A4 text width in twips (21cm - 2*2cm margins)
    for old in [e for e in body.iter(qn("w:tbl"))]:
        data: list[list[str]] = []
        aligns: list[str] | None = None
        for tr in old.findall(qn("w:tr")):
            row, al = [], []
            for tc in tr.findall(qn("w:tc")):
                row.append("".join(t.text or "" for t in tc.iter(qn("w:t"))))
                jc = tc.find(".//" + qn("w:jc"))
                al.append(jc.get(qn("w:val")) if jc is not None else "left")
            data.append(row)
            if aligns is None:
                aligns = al
        if not data:
            continue
        ncol = max(len(r) for r in data)
        maxlen = [1] * ncol
        for r in data:
            for i, c in enumerate(r):
                maxlen[i] = max(maxlen[i], len(c) or 1)
        weights = [max(length, 4) ** 0.8 for length in maxlen]
        total = sum(weights)
        widths = [max(650, int(usable * w / total)) for w in weights]
        widths[-1] += usable - sum(widths)

        table = doc.add_table(rows=len(data), cols=ncol)
        table.style = "Table Grid"
        table.autofit = False
        tbl_pr = table._tbl.tblPr
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        tbl_pr.append(layout)
        tbl_w = OxmlElement("w:tblW")
        tbl_w.set(qn("w:type"), "dxa")
        tbl_w.set(qn("w:w"), str(usable))
        tbl_pr.append(tbl_w)
        grid = table._tbl.find(qn("w:tblGrid"))
        for grid_col, width in zip(grid.findall(qn("w:gridCol")), widths):
            grid_col.set(qn("w:w"), str(width))
        for ri, r in enumerate(data):
            for ci in range(ncol):
                cell = table.cell(ri, ci)
                tc_pr = cell._tc.get_or_add_tcPr()
                tc_w = tc_pr.find(qn("w:tcW"))
                if tc_w is None:
                    tc_w = OxmlElement("w:tcW")
                    tc_pr.append(tc_w)
                tc_w.set(qn("w:type"), "dxa")
                tc_w.set(qn("w:w"), str(widths[ci]))
                para = cell.paragraphs[0]
                para.paragraph_format.space_before = Pt(0)
                para.paragraph_format.space_after = Pt(0)
                para.paragraph_format.line_spacing = 1.0
                if aligns and ci < len(aligns) and aligns[ci] == "right":
                    para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                run = para.add_run(r[ci] if ci < len(r) else "")
                set_run_font(run, 9, ri == 0)
        old.addprevious(table._tbl)
        body.remove(old)


def build_docx_with_pandoc() -> None:
    cmd = [
        "pandoc",
        str(OUT_MD.relative_to(PROJECT_ROOT)),
        "--reference-doc",
        str(REF_DOCX.relative_to(PROJECT_ROOT)),
        "-o",
        str(OUT_DOCX.relative_to(PROJECT_ROOT)),
    ]
    subprocess.run(cmd, cwd=PROJECT_ROOT, check=True)
    doc = Document(OUT_DOCX)
    enforce_paragraph_format(doc)
    rebuild_tables_native(doc)
    doc.save(OUT_DOCX)


def build_pdf() -> None:
    subprocess.run(
        [
            "libreoffice",
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(MANUSCRIPT_DIR),
            str(OUT_DOCX),
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )


def main() -> None:
    create_reference_docx()
    create_blank_template()
    build_review_markdown()
    build_docx_with_pandoc()
    build_pdf()
    print(f"review markdown: {OUT_MD}")
    print(f"reference docx: {REF_DOCX}")
    print(f"blank template markdown: {TEMPLATE_MD}")
    print(f"blank template docx: {TEMPLATE_DOCX}")
    print(f"review docx: {OUT_DOCX}")
    print(f"review pdf: {OUT_PDF}")


if __name__ == "__main__":
    raise SystemExit("internal Word-formatting primitives; run make_dbr_complete_working_draft_v5.py")
