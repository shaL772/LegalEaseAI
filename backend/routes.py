from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ai_core.gemini_generator import GeminiDocumentGenerator
from config import settings
from schemas import DocumentRequest, DocumentResponse


router = APIRouter()


def _generator() -> GeminiDocumentGenerator:
    """
    Safely initialize the Gemini generator.
    """
    try:
        return GeminiDocumentGenerator()
    except RuntimeError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc


@router.get("/health")
def health() -> dict[str, object]:
    """
    Health-check endpoint.
    """
    configured = bool(
        settings.mock_mode
        or settings.gemini_api_key
    )

    return {
        "status": "ok",
        "app": settings.app_name,
        "version": settings.app_version,
        "ai_configured": configured,
        "mock_mode": settings.mock_mode,
        "model": settings.gemini_model,
    }


@router.post(
    "/generate",
    response_model=DocumentResponse,
)
def generate_document(
    request: DocumentRequest,
) -> DocumentResponse:
    generator = _generator()

    try:
        content = generator.generate_document(
            document_type=request.document_type,
            parties=request.parties,
            terms=request.terms,
            effective_date=request.effective_date,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Document generation failed: "
                f"{exc}"
            ),
        ) from exc

    if len(content) > settings.max_document_chars:
        raise HTTPException(
            status_code=502,
            detail=(
                "Generated document exceeded "
                "the configured size limit."
            ),
        )

    return DocumentResponse(
        success=True,
        document_type=request.document_type,
        content=content,
        model=settings.gemini_model,
        mocked=settings.mock_mode,
    )