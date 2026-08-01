"""Shared pytest fixtures.

Every test gets a disposable Chroma store + document registry (so tests
never touch the real ./data directory) and a reset of the module-level
singletons that `app.vectorstore` / `app.rag_service` / `app.ollama_client`
cache across calls. The Ollama call itself is mocked in most tests via the
`mock_ollama_ok` fixture — see tests/test_live_ollama.py for the one test
that talks to a real Ollama server.
"""

import pytest
from fastapi.testclient import TestClient

from app import ollama_client, rag_service, vectorstore
from app.config import get_settings
from app.main import app


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    monkeypatch.setenv("CHROMA_PERSIST_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("DOCUMENTS_REGISTRY_PATH", str(tmp_path / "documents.json"))
    get_settings.cache_clear()

    # These modules cache client/collection/registry objects at module scope
    # (created once, reused across calls) — reset them so each test starts
    # from a clean slate that matches the settings above.
    vectorstore._client = None
    vectorstore._collection = None
    rag_service._registry = None
    rag_service._check_cache = None
    ollama_client._client = None

    yield

    get_settings.cache_clear()


@pytest.fixture
def client(isolated_settings):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_ollama_ok(monkeypatch):
    """Stub the Ollama call with a canned, schema-valid "confirmed risk"
    response so allergy-check tests don't depend on a running model."""

    async def _fake_analyze(
        settings, *, patient_allergies, product_name, ingredients_text, retrieved_context
    ):
        allergen = patient_allergies[0] if patient_allergies else "unknown"
        return {
            "risk_level": "confirmed",
            "is_safe": False,
            "matches": [
                {
                    "allergen": allergen,
                    "matched_term": "peanut butter",
                    "confidence": "high",
                    "evidence": "Ingredient list explicitly includes peanut butter.",
                }
            ],
            "notification_title": f"Do not consume: contains {allergen}",
            "notification_message": f"This product contains {allergen}.",
            "notification_severity": "danger",
            "reasoning_summary": "Explicit ingredient match found.",
        }

    monkeypatch.setattr(ollama_client, "analyze_allergy_risk", _fake_analyze)
    return _fake_analyze
