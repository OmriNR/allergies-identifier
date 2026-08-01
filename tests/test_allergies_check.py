import io

from app import ollama_client


def _check_payload(**overrides):
    payload = {
        "patient_allergies": ["peanuts"],
        "product_name": "Thai Peanut Sauce",
        "ingredients_text": "water, peanut butter, soy sauce",
        "use_documents": False,
    }
    payload.update(overrides)
    return payload


def test_check_requires_ingredients_or_documents(client):
    resp = client.post(
        "/allergies/check",
        json={"patient_allergies": ["peanuts"], "use_documents": False},
    )
    assert resp.status_code == 400


def test_check_returns_risk_assessment(client, mock_ollama_ok):
    resp = client.post("/allergies/check", json=_check_payload())

    assert resp.status_code == 200
    body = resp.json()
    assert body["risk_level"] == "confirmed"
    assert body["is_safe"] is False
    assert body["matches"][0]["allergen"] == "peanuts"
    assert body["notification"]["severity"] == "danger"
    assert body["cached"] is False


def test_check_is_served_from_cache_on_repeat_request(client, mock_ollama_ok):
    payload = _check_payload()

    first = client.post("/allergies/check", json=payload).json()
    assert first["cached"] is False

    second = client.post("/allergies/check", json=payload).json()
    assert second["cached"] is True
    assert second["risk_level"] == first["risk_level"]


def test_check_includes_sources_when_documents_are_used(client, mock_ollama_ok):
    content = b"Peanut allergens: peanut butter and peanut flour both contain peanut protein."
    client.post(
        "/documents",
        files={"file": ("peanut_ref.txt", io.BytesIO(content), "text/plain")},
    )

    resp = client.post(
        "/allergies/check",
        json=_check_payload(ingredients_text="peanut butter", use_documents=True),
    )

    assert resp.status_code == 200
    sources = resp.json()["sources"]
    assert len(sources) >= 1
    assert sources[0]["filename"] == "peanut_ref.txt"


def test_check_maps_ollama_unreachable_to_503(client, monkeypatch):
    async def _raise(*args, **kwargs):
        raise ollama_client.OllamaUnreachableError("Could not reach Ollama.")

    monkeypatch.setattr(ollama_client, "analyze_allergy_risk", _raise)

    resp = client.post("/allergies/check", json=_check_payload())
    assert resp.status_code == 503


def test_check_maps_model_not_found_to_503(client, monkeypatch):
    async def _raise(*args, **kwargs):
        raise ollama_client.OllamaModelNotFoundError("Model not pulled.")

    monkeypatch.setattr(ollama_client, "analyze_allergy_risk", _raise)

    resp = client.post("/allergies/check", json=_check_payload())
    assert resp.status_code == 503


def test_check_maps_generic_ollama_error_to_502(client, monkeypatch):
    async def _raise(*args, **kwargs):
        raise ollama_client.OllamaError("Response was not valid JSON.")

    monkeypatch.setattr(ollama_client, "analyze_allergy_risk", _raise)

    resp = client.post("/allergies/check", json=_check_payload())
    assert resp.status_code == 502
