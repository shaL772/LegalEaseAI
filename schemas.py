from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class DocumentRequest(BaseModel):
    """
    Data received by POST /generate.
    """

    document_type: str = Field(
        ...,
        min_length=2,
        max_length=120,
    )

    parties: str = Field(
        ...,
        min_length=2,
        max_length=4000,
    )

    terms: str = Field(
        ...,
        min_length=2,
        max_length=10000,
    )

    effective_date: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    brand_name: str = Field(
        default="LegalEase",
        min_length=1,
        max_length=120,
    )

    @field_validator(
        "document_type",
        "parties",
        "terms",
        "effective_date",
        "brand_name",
    )
    @classmethod
    def clean_whitespace(
        cls,
        value: str,
    ) -> str:
        """
        Normalize unnecessary whitespace.
        """
        return " ".join(
            value.strip().split()
        )


class DocumentResponse(BaseModel):
    """
    Response returned by POST /generate.
    """

    success: bool
    document_type: str
    content: str
    model: str
    mocked: bool = False