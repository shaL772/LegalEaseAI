from __future__ import annotations

from services.document_exporter import (
    format_docx,
    format_pdf,
    format_txt,
)


def test_txt_export() -> None:

    data = format_txt(
        "TEST — document"
    )

    assert (
        data
        == b"TEST - document"
    )


def test_docx_export() -> None:

    data = format_docx(
        (
            "EMPLOYMENT CONTRACT\n\n"
            "TERMS AND CONDITIONS\n"
            "1. Payment within 30 days"
        ),
        "Employment Contract",
        (
            "Payment within 30 days; "
            "Confidentiality must be maintained"
        ),
    )

    # DOCX is a ZIP-based file format
    assert data.startswith(
        b"PK"
    )

    assert len(data) > 1000


def test_pdf_export() -> None:

    data = format_pdf(
        (
            "LEASE AGREEMENT\n\n"
            "PARTIES\n"
            "Alice Smith"
        ),
        "Lease Agreement",
    )

    assert data.startswith(
        b"%PDF"
    )

    assert len(data) > 1000