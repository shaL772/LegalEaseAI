from __future__ import annotations

import io
import re

from pathlib import Path

from docx import Document

from docx.enum.text import (
    WD_ALIGN_PARAGRAPH,
)

from docx.enum.table import (
    WD_TABLE_ALIGNMENT,
)

from docx.oxml import OxmlElement

from docx.oxml.ns import qn

from docx.shared import (
    Inches,
    Pt,
)

from fpdf import FPDF

from PIL import (
    Image,
    ImageDraw,
    ImageFont,
)


# =========================================================
# PATHS
# =========================================================

ASSET_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
    / "assets"
)

LOGO_PATH = (
    ASSET_DIR
    / "legalease_logo.png"
)


# =========================================================
# TEXT SANITIZER
# =========================================================

def sanitize_text(
    text: str,
) -> str:
    """
    Convert typographic characters into
    ASCII-safe equivalents for exports.
    """

    replacements = {
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "–": "-",
        "—": "-",
        "…": "...",
        "•": "*",
        "©": "(c)",
        "®": "(R)",
        "™": "(TM)",
    }

    for old, new in replacements.items():

        text = text.replace(
            old,
            new,
        )

    return "".join(
        ch
        if ord(ch) < 128
        else "?"
        for ch in text
    )


# =========================================================
# LOGO
# =========================================================

def _ensure_logo() -> Path:
    """
    Create a basic LegalEase logo
    automatically when one does not exist.
    """

    ASSET_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if LOGO_PATH.exists():
        return LOGO_PATH

    image = Image.new(
        "RGB",
        (900, 250),
        "white",
    )

    draw = ImageDraw.Draw(
        image
    )

    font = None

    candidates = [
        "/usr/share/fonts/"
        "truetype/dejavu/"
        "DejaVuSans-Bold.ttf",

        "/usr/share/fonts/"
        "truetype/liberation2/"
        "LiberationSans-Bold.ttf",
    ]

    for candidate in candidates:

        candidate_path = Path(
            candidate
        )

        if candidate_path.exists():

            font = ImageFont.truetype(
                candidate,
                92,
            )

            break

    if font is None:

        font = ImageFont.load_default()


    # Logo box
    draw.rounded_rectangle(
        (20, 20, 230, 230),
        radius=40,
        outline="black",
        width=8,
    )


    # L
    draw.text(
        (85, 65),
        "L",
        fill="black",
        font=font,
        anchor="mm",
    )


    # LegalEase
    draw.text(
        (270, 70),
        "LegalEase",
        fill="black",
        font=font,
    )


    # Subtitle
    draw.text(
        (275, 170),
        "AI-powered legal drafting",
        fill="black",
        font=ImageFont.load_default(),
    )


    image.save(
        LOGO_PATH
    )

    return LOGO_PATH


# =========================================================
# DOCUMENT LINE CLASSIFIER
# =========================================================

def _paragraph_kind(
    line: str,
) -> str:

    stripped = line.strip()

    if not stripped:
        return "blank"

    if re.match(
        r"^\d+\.\s+",
        stripped,
    ):
        return "numbered"

    if stripped.startswith(
        ("* ", "- ", "• ")
    ):
        return "bullet"

    upper = stripped.upper()

    heading_words = {
        "PARTIES",
        "BACKGROUND",
        "RECITALS",
        "TERMS AND CONDITIONS",
        "CONFIDENTIALITY",
        "PAYMENT",
        "TERM AND TERMINATION",
        "SIGNATURES",
        "SIGNATURE",
        "GENERAL PROVISIONS",
        "DISCLAIMER",
    }

    if upper in heading_words:
        return "heading"

    if (
        len(stripped) <= 100
        and stripped == stripped.upper()
        and any(
            character.isalpha()
            for character in stripped
        )
    ):
        return "heading"

    return "body"


# =========================================================
# TERMS
# =========================================================

def _split_terms(
    terms: str | None,
) -> list[str]:

    if not terms:
        return []

    return [
        item.strip()
        for item in terms.split(";")
        if item.strip()
    ]


# =========================================================
# DOCX BORDER
# =========================================================

def _add_bottom_border(
    paragraph,
) -> None:

    p = paragraph._p

    p_pr = p.get_or_add_pPr()

    p_bdr = OxmlElement(
        "w:pBdr"
    )

    bottom = OxmlElement(
        "w:bottom"
    )

    bottom.set(
        qn("w:val"),
        "single",
    )

    bottom.set(
        qn("w:sz"),
        "6",
    )

    bottom.set(
        qn("w:space"),
        "1",
    )

    bottom.set(
        qn("w:color"),
        "888888",
    )

    p_bdr.append(
        bottom
    )

    p_pr.append(
        p_bdr
    )


# =========================================================
# DOCX EXPORT
# =========================================================

def format_docx(
    text: str,
    doc_type: str,
    terms: str | None = None,
    brand_name: str = "LegalEase",
) -> bytes:

    text = sanitize_text(
        text
    )

    doc = Document()

    section = doc.sections[0]

    section.top_margin = Inches(
        0.65
    )

    section.bottom_margin = Inches(
        0.65
    )

    section.left_margin = Inches(
        0.8
    )

    section.right_margin = Inches(
        0.8
    )


    # =====================================================
    # HEADER / LOGO
    # =====================================================

    logo_path = _ensure_logo()

    header = section.header

    paragraph = header.paragraphs[0]

    paragraph.alignment = (
        WD_ALIGN_PARAGRAPH.CENTER
    )

    paragraph.add_run().add_picture(
        str(logo_path),
        width=Inches(2.7),
    )


    # =====================================================
    # DEFAULT FONT
    # =====================================================

    normal = doc.styles["Normal"]

    normal.font.name = (
        "Times New Roman"
    )

    normal.font.size = Pt(11)


    # =====================================================
    # TITLE
    # =====================================================

    title = doc.add_paragraph()

    title.alignment = (
        WD_ALIGN_PARAGRAPH.CENTER
    )

    run = title.add_run(
        doc_type.title()
    )

    run.bold = True

    run.font.name = (
        "Times New Roman"
    )

    run.font.size = Pt(18)

    _add_bottom_border(
        title
    )


    # =====================================================
    # DOCUMENT CONTENT
    # =====================================================

    for raw_line in text.splitlines():

        kind = _paragraph_kind(
            raw_line
        )

        line = raw_line.strip()


        if kind == "blank":

            doc.add_paragraph()


        elif kind == "heading":

            paragraph = doc.add_paragraph()

            paragraph.paragraph_format.space_before = Pt(
                8
            )

            paragraph.paragraph_format.space_after = Pt(
                4
            )

            run = paragraph.add_run(
                line.rstrip(":")
            )

            run.bold = True

            run.font.name = (
                "Times New Roman"
            )

            run.font.size = Pt(12)


        elif kind == "numbered":

            paragraph = doc.add_paragraph(
                style="List Number"
            )

            paragraph.add_run(
                re.sub(
                    r"^\d+\.\s+",
                    "",
                    line,
                )
            )


        elif kind == "bullet":

            paragraph = doc.add_paragraph(
                style="List Bullet"
            )

            paragraph.add_run(
                re.sub(
                    r"^[*\-•]\s+",
                    "",
                    line,
                )
            )


        else:

            paragraph = doc.add_paragraph(
                line
            )

            paragraph.paragraph_format.line_spacing = (
                1.08
            )

            paragraph.paragraph_format.space_after = Pt(
                5
            )


    # =====================================================
    # TERMS TABLE
    # =====================================================

    if terms:

        table = doc.add_table(
            rows=1,
            cols=2,
        )

        table.alignment = (
            WD_TABLE_ALIGNMENT.CENTER
        )

        table.style = (
            "Table Grid"
        )

        table.rows[0].cells[0].text = (
            "No."
        )

        table.rows[0].cells[1].text = (
            "Key Term"
        )


        for index, term in enumerate(
            _split_terms(terms),
            start=1,
        ):

            cells = (
                table
                .add_row()
                .cells
            )

            cells[0].text = str(
                index
            )

            cells[1].text = sanitize_text(
                term
            )


    # =====================================================
    # FOOTER
    # =====================================================

    footer = section.footer

    footer_paragraph = (
        footer.paragraphs[0]
    )

    footer_paragraph.alignment = (
        WD_ALIGN_PARAGRAPH.CENTER
    )

    footer_run = (
        footer_paragraph.add_run(
            f"{brand_name} | "
            "AI-generated draft | "
            "Review with a qualified "
            "legal professional"
        )
    )

    footer_run.font.name = (
        "Times New Roman"
    )

    footer_run.font.size = Pt(8)


    # =====================================================
    # SAVE
    # =====================================================

    buffer = io.BytesIO()

    doc.save(
        buffer
    )

    return buffer.getvalue()


# =========================================================
# PDF CLASS
# =========================================================

class _LegalEasePDF(FPDF):

    def __init__(
        self,
        brand_name: str,
        logo_path: Path,
    ) -> None:

        super().__init__(
            orientation="P",
            unit="mm",
            format="A4",
        )

        self.brand_name = (
            brand_name
        )

        self.logo_path = (
            logo_path
        )

        self.set_auto_page_break(
            auto=True,
            margin=18,
        )


    def header(self) -> None:

        if self.logo_path.exists():

            self.image(
                str(self.logo_path),
                x=78,
                y=7,
                w=54,
            )

            self.ln(19)

        self.set_draw_color(
            180,
            180,
            180,
        )

        self.line(
            15,
            self.get_y(),
            195,
            self.get_y(),
        )

        self.ln(5)

        self.set_x(
            self.l_margin
        )


    def footer(self) -> None:

        self.set_y(
            -14
        )

        self.set_font(
            "Helvetica",
            size=7,
        )

        self.set_text_color(
            90,
            90,
            90,
        )

        self.cell(
            0,
            5,
            (
                f"{self.brand_name} | "
                "AI-generated draft | "
                f"Page {self.page_no()}"
            ),
            align="C",
        )


# =========================================================
# PDF EXPORT
# =========================================================

def format_pdf(
    text: str,
    doc_type: str,
    brand_name: str = "LegalEase",
) -> bytes:

    text = sanitize_text(
        text
    )

    logo_path = _ensure_logo()

    pdf = _LegalEasePDF(
        brand_name,
        logo_path,
    )

    pdf.add_page()

    pdf.set_text_color(
        25,
        25,
        25,
    )

    pdf.set_font(
        "Helvetica",
        "B",
        17,
    )

    pdf.multi_cell(
        pdf.epw,
        9,
        sanitize_text(
            doc_type.title()
        ),
        align="C",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.ln(5)


    # =====================================================
    # CONTENT
    # =====================================================

    for raw_line in text.splitlines():

        kind = _paragraph_kind(
            raw_line
        )

        line = raw_line.strip()


        if kind == "blank":

            pdf.ln(2)


        elif kind == "heading":

            pdf.set_font(
                "Helvetica",
                "B",
                11,
            )

            pdf.set_text_color(
                40,
                40,
                40,
            )

            pdf.multi_cell(
                pdf.epw,
                7,
                line.rstrip(":"),
                new_x="LMARGIN",
                new_y="NEXT",
            )

            pdf.set_font(
                "Helvetica",
                size=10.5,
            )


        elif kind == "numbered":

            pdf.set_font(
                "Helvetica",
                size=10.5,
            )

            content = re.sub(
                r"^\d+\.\s+",
                "",
                line,
            )

            pdf.multi_cell(
                pdf.epw,
                6.2,
                f"- {sanitize_text(content)}",
                new_x="LMARGIN",
                new_y="NEXT",
            )


        elif kind == "bullet":

            pdf.set_font(
                "Helvetica",
                size=10.5,
            )

            content = re.sub(
                r"^[*\-•]\s+",
                "",
                line,
            )

            pdf.multi_cell(
                pdf.epw,
                6.2,
                f"- {sanitize_text(content)}",
                new_x="LMARGIN",
                new_y="NEXT",
            )


        else:

            pdf.set_font(
                "Helvetica",
                size=10.5,
            )

            pdf.set_text_color(
                25,
                25,
                25,
            )

            pdf.multi_cell(
                pdf.epw,
                6.2,
                line,
                new_x="LMARGIN",
                new_y="NEXT",
            )


    output = pdf.output()

    return bytes(
        output
    )


# =========================================================
# TXT EXPORT
# =========================================================

def format_txt(
    text: str,
) -> bytes:

    return sanitize_text(
        text
    ).encode(
        "utf-8"
    )