"""Wraps the local Ollama call that reasons about ingredient/allergen matches.

Retrieval (the RAG part) happens in the vector store; this module only turns
retrieved context + a patient's allergy profile into a structured risk
assessment. It uses Ollama's structured-outputs support (the `format` field,
given a JSON schema) so the response is always valid JSON matching
ALLERGY_RESPONSE_SCHEMA, the same guarantee `output_config.format` gave us
on the Claude API.
"""

import json

import httpx

from app.config import Settings
from app.schemas import SearchResult

SYSTEM_PROMPT = """\
You are a clinical-safety assistant that cross-references ingredient lists \
and supporting medical/allergen reference text against a patient's known \
allergies.

Rules:
- Only flag allergens that are actually supported by the ingredients text \
or the supporting reference context you were given. Do not invent matches.
- Treat vague or high-risk labeling ("natural flavors", "spices", "may \
contain traces of X", shared-equipment warnings) as at least a "possible" \
risk with "low" or "medium" confidence rather than dismissing it — be \
conservative, this affects patient safety.
- Consider common allergen synonyms and known cross-reactivities (e.g. \
casein/whey -> milk, albumin -> egg, tree nut cross-reactivity) when the \
supporting reference context establishes them; do not assume cross-reactivity \
that isn't backed by the provided text.
- If no ingredients text or relevant context was provided, say so plainly in \
reasoning_summary and return risk_level "none" with is_safe true and an \
empty matches list — do not guess.
- Write notification_title and notification_message for the patient \
directly: short, clear, non-alarmist unless risk is confirmed, and \
actionable (what to avoid / what to double-check).
- Respond with ONLY the JSON object described by the schema — no prose \
before or after it.
"""

ALLERGY_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "risk_level": {"type": "string", "enum": ["none", "possible", "confirmed"]},
        "is_safe": {"type": "boolean"},
        "matches": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "allergen": {"type": "string"},
                    "matched_term": {"type": "string"},
                    "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                    "evidence": {"type": "string"},
                },
                "required": ["allergen", "matched_term", "confidence", "evidence"],
            },
        },
        "notification_title": {"type": "string"},
        "notification_message": {"type": "string"},
        "notification_severity": {"type": "string", "enum": ["none", "caution", "danger"]},
        "reasoning_summary": {"type": "string"},
    },
    "required": [
        "risk_level",
        "is_safe",
        "matches",
        "notification_title",
        "notification_message",
        "notification_severity",
        "reasoning_summary",
    ],
}

_client: httpx.AsyncClient | None = None


class OllamaError(RuntimeError):
    """Base error for problems talking to the local Ollama server."""


class OllamaUnreachableError(OllamaError):
    """Raised when the Ollama server can't be reached at all."""


class OllamaModelNotFoundError(OllamaError):
    """Raised when the configured model hasn't been pulled yet."""


def _get_client(settings: Settings) -> httpx.AsyncClient:
    global _client
    if _client is None or _client.base_url != httpx.URL(settings.ollama_base_url):
        _client = httpx.AsyncClient(
            base_url=settings.ollama_base_url,
            timeout=httpx.Timeout(settings.ollama_request_timeout, connect=5.0),
        )
    return _client


def _build_user_message(
    patient_allergies: list[str],
    product_name: str | None,
    ingredients_text: str | None,
    retrieved_context: list[SearchResult],
) -> str:
    parts = [f"Patient's known allergies: {', '.join(patient_allergies)}"]
    if product_name:
        parts.append(f"Product name: {product_name}")
    parts.append(
        "Ingredients text:\n"
        + (ingredients_text.strip() if ingredients_text else "(none provided)")
    )

    if retrieved_context:
        context_blocks = "\n\n".join(
            f"[Source: {r.filename}, chunk {r.chunk_index}]\n{r.text}"
            for r in retrieved_context
        )
        parts.append(
            "Supporting reference material retrieved from the medical document "
            f"store (may include allergen synonyms, cross-reactivity notes, or "
            f"clinical guidance):\n\n{context_blocks}"
        )
    else:
        parts.append("No supporting reference material was retrieved.")

    parts.append(
        "Assess the allergy risk and respond with JSON matching the required schema."
    )
    return "\n\n".join(parts)


async def _post_chat(settings: Settings, messages: list[dict], *, format_schema: dict | None) -> dict:
    client = _get_client(settings)
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "stream": False,
        "keep_alive": settings.ollama_keep_alive,
        "options": {
            "temperature": settings.ollama_temperature,
            "num_predict": settings.ollama_num_predict,
        },
    }
    # Ollama rejects `"think": true` outright (400) for models that don't
    # support thinking — so only set it when explicitly enabled, and never
    # send `false` either; omitting the key entirely is the only value that
    # works across both reasoning and plain instruct models.
    if settings.ollama_think:
        payload["think"] = True
    if format_schema is not None:
        payload["format"] = format_schema

    try:
        response = await client.post("/api/chat", json=payload)
    except httpx.ConnectError as exc:
        raise OllamaUnreachableError(
            f"Could not reach Ollama at {settings.ollama_base_url}. "
            "Is the container running and the port published?"
        ) from exc

    if response.status_code == 404:
        raise OllamaModelNotFoundError(
            f"Model '{settings.ollama_model}' is not available on the Ollama "
            f"server. Pull it first: `ollama pull {settings.ollama_model}`."
        )
    response.raise_for_status()
    return response.json()


async def analyze_allergy_risk(
    settings: Settings,
    patient_allergies: list[str],
    product_name: str | None,
    ingredients_text: str | None,
    retrieved_context: list[SearchResult],
) -> dict:
    user_message = _build_user_message(
        patient_allergies, product_name, ingredients_text, retrieved_context
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]

    body = await _post_chat(settings, messages, format_schema=ALLERGY_RESPONSE_SCHEMA)

    content = body.get("message", {}).get("content", "")
    if not content:
        raise OllamaError("Ollama returned an empty response.")

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise OllamaError(
            f"Ollama's response was not valid JSON despite the schema constraint: {exc}"
        ) from exc


async def warm_up(settings: Settings) -> None:
    """Best-effort: ping the server and load the model into memory so the
    first real request doesn't pay Ollama's cold-load latency. Never raises —
    logs are left to the caller/uvicorn if the server isn't reachable yet."""
    import logging

    logger = logging.getLogger("uvicorn.error")
    try:
        await _post_chat(
            settings,
            messages=[{"role": "user", "content": "Reply with just: ok"}],
            format_schema=None,
        )
    except OllamaError as exc:
        logger.warning("Ollama warm-up skipped: %s", exc)
    except httpx.HTTPStatusError as exc:
        logger.warning("Ollama warm-up skipped: HTTP %s", exc.response.status_code)
