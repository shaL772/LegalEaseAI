from __future__ import annotations

import os

from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


class Settings(BaseModel):
    app_name: str = os.getenv(
        "APP_NAME",
        "LegalEaseAI",
    )

    app_version: str = os.getenv(
        "APP_VERSION",
        "1.0.0",
    )

    gemini_api_key: str = os.getenv(
        "GEMINI_API_KEY",
        "",
    )

    gemini_model: str = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash",
    )

    mock_mode: bool = os.getenv(
        "MOCK_MODE",
        "true",
    ).lower() in {
        "1",
        "true",
        "yes",
        "on",
    }

    max_document_chars: int = int(
        os.getenv(
            "MAX_DOCUMENT_CHARS",
            "20000",
        )
    )


settings = Settings()