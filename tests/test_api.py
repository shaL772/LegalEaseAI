from __future__ import annotations

import os


# Force mock mode for tests
os.environ["MOCK_MODE"] = "true"


from fastapi.testclient import TestClient

from backend.main import app


client = TestClient(app)


def test_root() -> None:

    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["message"]


def test_health_mock_mode() -> None:

    response = client.get(
        "/health"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"

    assert data["mock_mode"] is True


def test_generate_document() -> None:

    payload = {
        "document_type": (
            "Freelance Work Contract"
        ),

        "parties": (
            "Jane Doe (Service Provider), "
            "TechNova Inc. (Client)"
        ),

        "terms": (
            "Payment within 30 days; "
            "Confidentiality must be maintained"
        ),

        "effective_date": (
            "2026-09-27"
        ),

        "brand_name": "LegalEase",
    }


    response = client.post(
        "/generate",
        json=payload,
    )


    assert (
        response.status_code == 200
    )


    data = response.json()


    assert data["success"] is True


    assert (
        "FREELANCE WORK CONTRACT"
        in data["content"]
    )


    assert (
        "Payment within 30 days"
        in data["content"]
    )


    assert (
        data["mocked"] is True
    )