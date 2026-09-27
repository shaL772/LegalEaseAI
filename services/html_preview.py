from __future__ import annotations

import html
import re


def format_html_preview(text: str) -> str:
    """
    Convert generated document text
    into a styled HTML preview.
    """

    safe = html.escape(
        text.strip()
    )

    # Detect uppercase section headings
    safe = re.sub(
        r"(?m)^([A-Z][A-Z0-9 &/\-]{2,80})$",
        r"<h3>\1</h3>",
        safe,
    )

    # Detect numbered clauses
    safe = re.sub(
        r"(?m)^\s*([0-9]+)\.\s+(.*)$",
        r'<p class="clause">'
        r"<strong>\1.</strong> \2"
        r"</p>",
        safe,
    )

    # Paragraph spacing
    safe = safe.replace(
        "\n\n",
        "</p><p>",
    )

    # Single line breaks
    safe = safe.replace(
        "\n",
        "<br>",
    )

    return (
        '<div class="legal-preview">'
        f"<p>{safe}</p>"
        "</div>"
    )