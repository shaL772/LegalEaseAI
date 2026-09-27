from __future__ import annotations

import io
import re
import tempfile
from pathlib import Path

import requests
import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Inches, Pt
from fpdf import FPDF


# ============================================================
# CONFIGURATION
# ============================================================

APP_NAME = "LegalEaseAI"

BACKEND_URL = "http://127.0.0.1:8000"

GENERATE_URL = f"{BACKEND_URL}/generate"
HEALTH_URL = f"{BACKEND_URL}/health"


# ============================================================
# STREAMLIT PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="LegalEaseAI",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# SESSION STATE
# ============================================================

if "generated_document" not in st.session_state:
    st.session_state.generated_document = ""

if "current_document_type" not in st.session_state:
    st.session_state.current_document_type = ""

if "brand_name" not in st.session_state:
    st.session_state.brand_name = "LegalEase"

if "generation_complete" not in st.session_state:
    st.session_state.generation_complete = False

if "backend_health" not in st.session_state:
    st.session_state.backend_health = None

if "mock_mode" not in st.session_state:
    st.session_state.mock_mode = True


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 4px;
    }

    .subtitle {
        font-size: 17px;
        color: #b8bac4;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 24px;
        font-weight: 700;
        margin-top: 10px;
        margin-bottom: 15px;
    }

    .status-card {
        padding: 14px;
        border-radius: 10px;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .legal-warning {
        padding: 16px;
        border-radius: 10px;
        background-color: rgba(40, 100, 180, 0.20);
        border: 1px solid rgba(80, 150, 230, 0.30);
        color: #d9eaff;
        font-size: 14px;
    }

    .footer-text {
        text-align: center;
        color: #8f929d;
        font-size: 13px;
        line-height: 1.7;
        margin-top: 30px;
        padding-top: 20px;
        padding-bottom: 20px;
        border-top: 1px solid #363842;
    }

    .logo-container {
        text-align: center;
        margin-bottom: 20px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# LOGO CREATION
# ============================================================

def create_logo_png() -> bytes:
    """
    Create the LegalEase logo automatically using Pillow.

    This means the application does not depend on a separate
    logo image file.
    """

    width = 1000
    height = 300

    image = Image.new(
        "RGB",
        (width, height),
        "white",
    )

    draw = ImageDraw.Draw(image)

    # --------------------------------------------------------
    # Try to load a professional font.
    # --------------------------------------------------------

    font_paths = [
        r"C:\Windows\Fonts\georgiab.ttf",
        r"C:\Windows\Fonts\timesbd.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
    ]

    logo_font = None

    for font_path in font_paths:
        if Path(font_path).exists():
            try:
                logo_font = ImageFont.truetype(
                    font_path,
                    105,
                )
                break
            except Exception:
                pass

    if logo_font is None:
        logo_font = ImageFont.load_default()

    # --------------------------------------------------------
    # Draw scales of justice.
    # --------------------------------------------------------

    scale_color = (20, 20, 20)

    center_x = 160
    top_y = 55

    # Vertical pole
    draw.line(
        [
            (center_x, top_y),
            (center_x, 205),
        ],
        fill=scale_color,
        width=8,
    )

    # Base
    draw.line(
        [
            (95, 220),
            (225, 220),
        ],
        fill=scale_color,
        width=9,
    )

    draw.line(
        [
            (110, 235),
            (210, 235),
        ],
        fill=scale_color,
        width=9,
    )

    # Top horizontal beam
    draw.line(
        [
            (75, 65),
            (245, 65),
        ],
        fill=scale_color,
        width=8,
    )

    # Left support
    draw.line(
        [
            (105, 65),
            (80, 125),
        ],
        fill=scale_color,
        width=5,
    )

    draw.line(
        [
            (105, 65),
            (130, 125),
        ],
        fill=scale_color,
        width=5,
    )

    # Right support
    draw.line(
        [
            (215, 65),
            (190, 125),
        ],
        fill=scale_color,
        width=5,
    )

    draw.line(
        [
            (215, 65),
            (240, 125),
        ],
        fill=scale_color,
        width=5,
    )

    # Left bowl
    draw.arc(
        [
            55,
            105,
            155,
            165,
        ],
        0,
        180,
        fill=scale_color,
        width=5,
    )

    # Right bowl
    draw.arc(
        [
            145,
            105,
            245,
            165,
        ],
        0,
        180,
        fill=scale_color,
        width=5,
    )

    # --------------------------------------------------------
    # LegalEase text
    # --------------------------------------------------------

    draw.text(
        (285, 82),
        "LegalEase",
        fill=scale_color,
        font=logo_font,
    )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output = io.BytesIO()

    image.save(
        output,
        format="PNG",
    )

    return output.getvalue()


# ============================================================
# DISPLAY LOGO
# ============================================================

LOGO_BYTES = create_logo_png()

st.sidebar.image(
    LOGO_BYTES,
    width=215,
)

st.sidebar.markdown(
    """
    <div style="
        font-size: 15px;
        line-height: 1.7;
        margin-top: 10px;
    ">
        Generate structured legal documents
        from your requirements.
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.divider()


# ============================================================
# BACKEND HEALTH CHECK
# ============================================================

def get_backend_health():
    """
    Check whether the FastAPI backend is online.
    """

    try:
        response = requests.get(
            HEALTH_URL,
            timeout=5,
        )

        if response.status_code == 200:
            return response.json()

        return None

    except requests.RequestException:
        return None


health = get_backend_health()

st.session_state.backend_health = health


# ============================================================
# SIDEBAR BACKEND STATUS
# ============================================================

st.sidebar.subheader(
    "Backend Status"
)

if health:

    st.sidebar.success(
        "Backend Online"
    )

    version = health.get(
        "version",
        "Unknown",
    )

    st.sidebar.caption(
        f"Version: {version}"
    )

    mock_mode = bool(
        health.get(
            "mock_mode",
            True,
        )
    )

    st.session_state.mock_mode = mock_mode

    if mock_mode:
        st.sidebar.info(
            "Mock mode is currently enabled."
        )
    else:
        st.sidebar.success(
            "Gemini AI is enabled."
        )

else:

    st.sidebar.error(
        "Backend Offline"
    )

    st.sidebar.caption(
        "Start FastAPI on port 8000."
    )


# ============================================================
# MAIN HEADER
# ============================================================

st.markdown(
    '<div class="main-title">⚖️ AI-Powered Legal Document Generator</div>',
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="subtitle">
        Create, edit and download professionally formatted
        legal documents with LegalEaseAI.
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# GENERATION FORM
# ============================================================

st.markdown(
    '<div class="section-title">Create Your Legal Document</div>',
    unsafe_allow_html=True,
)

with st.container(border=True):

    document_type = st.text_input(
        "Document Type",
        placeholder=(
            "Example: Rental Agreement, "
            "Freelance Agreement, NDA"
        ),
    )

    parties = st.text_area(
        "Parties",
        placeholder=(
            "Example:\n"
            "Landlord: Priya Sharma\n"
            "Tenant: Rahul Kumar"
        ),
        height=120,
    )

    terms = st.text_area(
        "Terms and Conditions",
        placeholder=(
            "Enter the important terms, payment "
            "conditions, responsibilities, "
            "termination conditions, etc."
        ),
        height=220,
    )

    effective_date = st.text_input(
        "Effective Date",
        placeholder="Example: 2026-10-01",
    )

    brand_name = st.text_input(
        "Brand Name",
        value="LegalEase",
    )

    st.markdown("")

    generate_clicked = st.button(
        "✨ Generate Legal Document",
        width="stretch",
        type="primary",
    )


# ============================================================
# GENERATE DOCUMENT
# ============================================================

if generate_clicked:

    if not document_type.strip():
        st.error(
            "Please enter a document type."
        )
        st.stop()

    if not parties.strip():
        st.error(
            "Please enter the parties."
        )
        st.stop()

    if not terms.strip():
        st.error(
            "Please enter the terms and conditions."
        )
        st.stop()

    if not effective_date.strip():
        st.error(
            "Please enter the effective date."
        )
        st.stop()

    if not health:
        st.error(
            "The FastAPI backend is offline. "
            "Start the backend first."
        )
        st.stop()

    payload = {
        "document_type": document_type.strip(),
        "parties": parties.strip(),
        "terms": terms.strip(),
        "effective_date": effective_date.strip(),
        "brand_name": brand_name.strip()
        or "LegalEase",
    }

    with st.spinner(
        "Generating your legal document..."
    ):

        try:

            response = requests.post(
                GENERATE_URL,
                json=payload,
                timeout=120,
            )

            if response.status_code == 200:

                result = response.json()

                generated_content = result.get(
                    "content",
                    "",
                )

                if not generated_content:
                    st.error(
                        "The backend returned an empty document."
                    )
                    st.stop()

                st.session_state.generated_document = (
                    generated_content
                )

                st.session_state.current_document_type = (
                    document_type.strip()
                )

                st.session_state.brand_name = (
                    brand_name.strip()
                    or "LegalEase"
                )

                st.session_state.generation_complete = True

                st.success(
                    "Legal document generated successfully!"
                )

            elif response.status_code == 422:

                try:
                    error_data = response.json()
                    detail = error_data.get(
                        "detail",
                        "Invalid request.",
                    )
                except Exception:
                    detail = response.text

                st.error(
                    f"Validation error: {detail}"
                )

            else:

                try:
                    error_data = response.json()
                    detail = error_data.get(
                        "detail",
                        response.text,
                    )
                except Exception:
                    detail = response.text

                st.error(
                    f"Backend error "
                    f"({response.status_code}): "
                    f"{detail}"
                )

        except requests.RequestException as exc:

            st.error(
                f"Could not connect to the backend: {exc}"
            )


# ============================================================
# GENERATED DOCUMENT EDITOR
# ============================================================

if st.session_state.generated_document:

    st.divider()

    st.markdown(
        '<div class="section-title">Generated Document</div>',
        unsafe_allow_html=True,
    )

    edited_document = st.text_area(
        "Review and edit your document before downloading:",
        value=st.session_state.generated_document,
        height=600,
        key="document_editor",
    )

    # Keep the latest edited version in session state.
    st.session_state.generated_document = (
        edited_document
    )

    current_document_type = (
        st.session_state.current_document_type
        or "Legal Document"
    )


    # ========================================================
    # SAFE FILENAME
    # ========================================================

    def safe_filename(
        value: str,
    ) -> str:

        value = value.strip()

        if not value:
            value = "LegalEase_Document"

        value = re.sub(
            r"[^\w\s-]",
            "",
            value,
        )

        value = re.sub(
            r"\s+",
            "_",
            value,
        )

        return value[:100]


    filename_base = safe_filename(
        current_document_type
    )


    # ========================================================
    # DOCX CREATION
    # ========================================================

    def create_docx(
        document_text: str,
        document_type: str,
    ) -> bytes:

        document = Document()

        # ----------------------------------------------------
        # Page margins
        # ----------------------------------------------------

        section = document.sections[0]

        section.top_margin = Inches(0.7)
        section.bottom_margin = Inches(0.7)
        section.left_margin = Inches(0.8)
        section.right_margin = Inches(0.8)

        # ----------------------------------------------------
        # Logo
        # ----------------------------------------------------

        logo_stream = io.BytesIO(
            LOGO_BYTES
        )

        paragraph = document.add_paragraph()

        paragraph.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER
        )

        run = paragraph.add_run()

        run.add_picture(
            logo_stream,
            width=Inches(3.0),
        )

        # ----------------------------------------------------
        # Subtitle
        # ----------------------------------------------------

        subtitle = document.add_paragraph()

        subtitle.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER
        )

        run = subtitle.add_run(
            "AI-powered legal document drafting"
        )

        run.font.name = "Times New Roman"
        run.font.size = Pt(10)

        # ----------------------------------------------------
        # Divider
        # ----------------------------------------------------

        divider = document.add_paragraph()

        divider.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER
        )

        run = divider.add_run(
            "________________________________________________"
        )

        run.font.name = "Times New Roman"
        run.font.size = Pt(9)

        # ----------------------------------------------------
        # Document title
        # ----------------------------------------------------

        title = document.add_paragraph()

        title.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER
        )

        run = title.add_run(
            document_type.upper()
        )

        run.bold = True
        run.font.name = "Times New Roman"
        run.font.size = Pt(16)

        # ----------------------------------------------------
        # Content
        # ----------------------------------------------------

        for raw_line in document_text.splitlines():

            line = raw_line.rstrip()

            paragraph = document.add_paragraph()

            paragraph.paragraph_format.space_after = Pt(6)

            run = paragraph.add_run(
                line
            )

            run.font.name = "Times New Roman"
            run.font.size = Pt(11)

        # ----------------------------------------------------
        # Footer
        # ----------------------------------------------------

        footer = section.footer

        footer_paragraph = (
            footer.paragraphs[0]
        )

        footer_paragraph.alignment = (
            WD_ALIGN_PARAGRAPH.CENTER
        )

        footer_run = footer_paragraph.add_run(
            "LegalEaseAI | Review with a qualified "
            "legal professional before signing."
        )

        footer_run.font.name = (
            "Times New Roman"
        )

        footer_run.font.size = Pt(8)

        # ----------------------------------------------------
        # Save
        # ----------------------------------------------------

        output = io.BytesIO()

        document.save(
            output
        )

        return output.getvalue()


    # ========================================================
    # PDF CREATION
    # ========================================================

    def create_pdf(
        document_text: str,
        document_type: str,
    ) -> bytes:
        """
        Robust PDF generator.

        Handles:
        - Long lines
        - Long unbreakable strings
        - Signature underscores
        - Unicode punctuation
        - Indian rupee symbol
        - Automatic page breaks
        - LegalEase logo
        """

        pdf = FPDF(
            orientation="P",
            unit="mm",
            format="A4",
        )

        pdf.set_auto_page_break(
            auto=True,
            margin=20,
        )

        pdf.set_margins(
            left=20,
            top=20,
            right=20,
        )

        pdf.add_page()

        # ----------------------------------------------------
        # Text cleaning
        # ----------------------------------------------------

        def clean_pdf_text(
            text: str,
        ) -> str:

            replacements = {
                "₹": "INR ",
                "—": "-",
                "–": "-",
                "−": "-",
                "“": '"',
                "”": '"',
                "‘": "'",
                "’": "'",
                "…": "...",
                "\u00a0": " ",
                "\u200b": "",
                "\ufeff": "",
            }

            for old, new in replacements.items():
                text = text.replace(
                    old,
                    new,
                )

            text = (
                text
                .encode(
                    "latin-1",
                    errors="replace",
                )
                .decode("latin-1")
            )

            return text


        # ----------------------------------------------------
        # Break long tokens
        # ----------------------------------------------------

        def split_long_token(
            token: str,
            max_width: float,
            font_size: float,
        ) -> list[str]:

            if not token:
                return [""]

            pdf.set_font(
                "Helvetica",
                size=font_size,
            )

            result = []

            current = ""

            for character in token:

                test = (
                    current
                    + character
                )

                if (
                    pdf.get_string_width(
                        test
                    )
                    <= max_width
                ):
                    current = test

                else:

                    if current:
                        result.append(
                            current
                        )

                    current = character

            if current:
                result.append(
                    current
                )

            return result


        # ----------------------------------------------------
        # Safe line processing
        # ----------------------------------------------------

        def safe_lines(
            text: str,
            max_width: float,
            font_size: float,
        ) -> list[str]:

            text = clean_pdf_text(
                text
            )

            result = []

            for original_line in text.splitlines():

                # Prevent giant underscore sequences
                # from breaking fpdf2.
                original_line = re.sub(
                    r"_{5,}",
                    "____________________",
                    original_line,
                )

                # Replace tabs.
                original_line = (
                    original_line.replace(
                        "\t",
                        "    ",
                    )
                )

                # Preserve blank lines.
                if not original_line.strip():
                    result.append("")
                    continue

                words = original_line.split()

                current_line = ""

                for word in words:

                    chunks = split_long_token(
                        word,
                        max_width,
                        font_size,
                    )

                    for chunk in chunks:

                        if not current_line:
                            current_line = chunk
                            continue

                        candidate = (
                            current_line
                            + " "
                            + chunk
                        )

                        if (
                            pdf.get_string_width(
                                candidate
                            )
                            <= max_width
                        ):
                            current_line = candidate

                        else:

                            result.append(
                                current_line
                            )

                            current_line = chunk

                if current_line:
                    result.append(
                        current_line
                    )

            return result


        # ----------------------------------------------------
        # Logo
        # ----------------------------------------------------

        logo_temp = tempfile.NamedTemporaryFile(
            suffix=".png",
            delete=False,
        )

        logo_temp.write(
            LOGO_BYTES
        )

        logo_temp.close()

        logo_path = logo_temp.name

        try:

            pdf.image(
                logo_path,
                x=72,
                y=12,
                w=66,
            )

        except Exception:
            pass


        # ----------------------------------------------------
        # Header spacing
        # ----------------------------------------------------

        pdf.set_y(48)

        pdf.set_font(
            "Helvetica",
            "",
            9,
        )

        pdf.cell(
            0,
            6,
            "AI-powered legal document drafting",
            new_x="LMARGIN",
            new_y="NEXT",
            align="C",
        )

        pdf.ln(4)

        # Divider
        pdf.set_draw_color(
            150,
            150,
            150,
        )

        pdf.line(
            20,
            pdf.get_y(),
            190,
            pdf.get_y(),
        )

        pdf.ln(8)


        # ----------------------------------------------------
        # Document title
        # ----------------------------------------------------

        title = clean_pdf_text(
            document_type
        ).upper()

        pdf.set_font(
            "Helvetica",
            "B",
            15,
        )

        pdf.multi_cell(
            170,
            8,
            title,
            align="C",
        )

        pdf.ln(5)


        # ----------------------------------------------------
        # Document body
        # ----------------------------------------------------

        pdf.set_font(
            "Helvetica",
            "",
            11,
        )

        printable_width = (
            pdf.w
            - pdf.l_margin
            - pdf.r_margin
        )

        lines = safe_lines(
            document_text,
            printable_width,
            11,
        )

        for line in lines:

            if not line.strip():

                pdf.ln(5)

                continue

            # Extra safety check.
            if (
                pdf.get_string_width(line)
                > printable_width
            ):

                chunks = split_long_token(
                    line,
                    printable_width,
                    11,
                )

                for chunk in chunks:

                    pdf.multi_cell(
                        printable_width,
                        6,
                        chunk,
                        align="L",
                    )

            else:

                pdf.multi_cell(
                    printable_width,
                    6,
                    line,
                    align="L",
                )


        # ----------------------------------------------------
        # Footer
        # ----------------------------------------------------

        pdf.set_y(-18)

        pdf.set_font(
            "Helvetica",
            "",
            8,
        )

        pdf.set_text_color(
            100,
            100,
            100,
        )

        pdf.cell(
            0,
            5,
            "LegalEaseAI | Review with a qualified legal professional before signing.",
            align="C",
        )


        # ----------------------------------------------------
        # Generate bytes
        # ----------------------------------------------------

        pdf_output = pdf.output()

        if isinstance(
            pdf_output,
            bytearray,
        ):
            pdf_bytes = bytes(
                pdf_output
            )

        elif isinstance(
            pdf_output,
            bytes,
        ):
            pdf_bytes = pdf_output

        else:
            pdf_bytes = bytes(
                pdf_output
            )


        # ----------------------------------------------------
        # Delete temporary logo file
        # ----------------------------------------------------

        try:
            Path(
                logo_path
            ).unlink(
                missing_ok=True
            )
        except Exception:
            pass


        return pdf_bytes


    # ========================================================
    # DOWNLOAD SECTION
    # ========================================================

    st.divider()

    st.markdown(
        '<div class="section-title">⬇️ Download Document</div>',
        unsafe_allow_html=True,
    )

    st.write(
        "Choose the format you want to download:"
    )

    # --------------------------------------------------------
    # Prepare files
    # --------------------------------------------------------

    try:

        docx_data = create_docx(
            edited_document,
            current_document_type,
        )

    except Exception as exc:

        docx_data = None

        st.error(
            f"Could not prepare DOCX: {exc}"
        )


    try:

        pdf_data = create_pdf(
            edited_document,
            current_document_type,
        )

    except Exception as exc:

        pdf_data = None

        st.error(
            f"Could not prepare PDF: {exc}"
        )


    txt_data = edited_document.encode(
        "utf-8"
    )


    # --------------------------------------------------------
    # Three download buttons
    # --------------------------------------------------------

    col1, col2, col3 = st.columns(3)


    with col1:

        if docx_data is not None:

            st.download_button(
                label="📘 Download DOCX",
                data=docx_data,
                file_name=(
                    f"{filename_base}.docx"
                ),
                mime=(
                    "application/vnd.openxmlformats-officedocument."
                    "wordprocessingml.document"
                ),
                width="stretch",
                key="download_docx",
            )


    with col2:

        if pdf_data is not None:

            st.download_button(
                label="📕 Download PDF",
                data=pdf_data,
                file_name=(
                    f"{filename_base}.pdf"
                ),
                mime="application/pdf",
                width="stretch",
                key="download_pdf",
            )


    with col3:

        st.download_button(
            label="📄 Download TXT",
            data=txt_data,
            file_name=(
                f"{filename_base}.txt"
            ),
            mime="text/plain",
            width="stretch",
            key="download_txt",
        )


    st.caption(
        "DOCX is editable • PDF is print-ready • TXT contains plain text"
    )


    # ========================================================
    # MOCK MODE MESSAGE
    # ========================================================

    if st.session_state.mock_mode:

        st.info(
            "Mock mode is currently enabled. "
            "The document-generation pipeline is working, "
            "but Gemini AI has not been enabled yet."
        )

    else:

        st.success(
            "Gemini AI is currently enabled."
        )


# ============================================================
# FOOTER
# ============================================================

st.markdown(
    """
    <div class="footer-text">
        <strong>LegalEaseAI</strong><br>
        AI-powered legal document drafting<br><br>
        Always review generated legal documents with a
        qualified legal professional before relying on them.
    </div>
    """,
    unsafe_allow_html=True,
)