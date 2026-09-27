from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import router
from config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "AI-powered legal document "
        "drafting service."
    ),
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=[
        "GET",
        "POST",
        "OPTIONS",
    ],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict[str, str]:
    """
    Root endpoint.
    """
    return {
        "message": "LegalEase backend is running.",
        "docs": "/docs",
    }


app.include_router(router)