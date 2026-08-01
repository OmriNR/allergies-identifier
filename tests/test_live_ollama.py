"""End-to-end test against a real Ollama server — no mocking.

Automatically skipped if Ollama isn't reachable at OLLAMA_BASE_URL, so the
rest of the suite stays fast and runnable without any local infrastructure.
Run this explicitly once your dockerized Ollama is up and the model from
.env / OLLAMA_MODEL has been pulled:

    pytest tests/test_live_ollama.py -v
"""

import httpx
import pytest

from app.config import get_settings


def _ollama_reachable() -> bool:
    settings = get_settings()
    try:
        httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=2.0)
        return True
    except httpx.HTTPError:
        return False


pytestmark = pytest.mark.skipif(
    not _ollama_reachable(),
    reason="Ollama is not reachable at OLLAMA_BASE_URL — skipping live test.",
)


def test_live_allergy_check_flags_peanut_ingredient(client):
    resp = client.post(
        "/allergies/check",
        json={
            "patient_allergies": ["peanuts"],
            "product_name": "Peanut Sauce",
            "ingredients_text": "water, peanut butter, soy sauce",
            "use_documents": False,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_level"] in {"possible", "confirmed"}
    assert any("peanut" in m["allergen"].lower() for m in body["matches"])


def test_live_allergy_check_finds_no_risk_for_unrelated_allergen(client):
    resp = client.post(
        "/allergies/check",
        json={
            "patient_allergies": ["shellfish"],
            "product_name": "Plain Rice",
            "ingredients_text": "water, white rice, salt",
            "use_documents": False,
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_level"] == "none"
    assert body["is_safe"] is True
