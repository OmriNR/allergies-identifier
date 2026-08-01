# Allergy Identifier API

A RAG (retrieval-augmented generation) API for detecting potential allergens in
ingredient lists / medical documents and notifying a patient about the risk.

## How it works

1. **Ingest** — medical documents / ingredient references (`.txt`, `.md`, `.pdf`)
   are chunked and embedded locally with Chroma's built-in ONNX MiniLM model
   (CPU-only, no network round trip per request) and stored in an on-disk
   Chroma vector store.
2. **Retrieve** — when checking a product, the API does a semantic search over
   the stored documents for content relevant to the ingredients + the
   patient's allergies (e.g. allergen synonyms, cross-reactivity notes).
3. **Reason & notify** — the ingredients text plus retrieved context is sent
   to a local model served by **Ollama** (`qwen2.5:7b-instruct` by default)
   with a JSON schema passed via Ollama's structured-outputs `format` field,
   so the model always returns a validated risk assessment: matched
   allergens, confidence, evidence, and a ready-to-send patient notification.
   Everything — embeddings and reasoning — runs locally; no external API
   calls are made.

Speed is handled at every layer: local (non-network) embeddings, both the
vector store's embedding model and the Ollama model are warmed up at process
startup (Ollama's `keep_alive` then keeps the model resident in memory so it
isn't reloaded between requests), blocking I/O runs in a thread pool so the
event loop stays free, and identical allergy checks are served from an
in-process TTL cache.

## Setup

```bash
python -m venv .venv
.venv/Scripts/activate   # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env     # or `copy` on Windows
```

### Ollama

This API expects an Ollama server reachable at `OLLAMA_BASE_URL` (default
`http://localhost:11434`). If you're running Ollama in Docker, make sure the
container is started (`docker start <container-name>`) and the port is
published (`-p 11434:11434`).

**Model choice:** the default is `qwen3:4b` — pick whatever's already pulled
in your container and reliably follows JSON-schema / structured-output
constraints, since this API depends on that for every response. Check what
you have with:

```bash
docker exec -it <ollama-container-name> ollama list
```

To pull a different one:

```bash
docker exec -it <ollama-container-name> ollama pull qwen2.5:7b-instruct
```

then set `OLLAMA_MODEL=qwen2.5:7b-instruct` in `.env`. `qwen2.5:7b-instruct`
and `qwen3:4b` both handle structured outputs well; for higher accuracy on
more capable hardware (e.g. a GPU), `qwen2.5:14b-instruct` is a solid step up.

## Run

```bash
uvicorn app.main:app --reload
```

The API is served at `http://127.0.0.1:8000`.

## API Documentation

Three interactive doc UIs are generated automatically from the code (routes,
Pydantic schemas, field descriptions/examples) — no separate doc file to
keep in sync:

| UI | URL | Notes |
| --- | --- | --- |
| **Scalar** | `http://127.0.0.1:8000/scalar` | Modern reference UI, has a built-in request builder/tester |
| Swagger UI | `http://127.0.0.1:8000/docs` | FastAPI's default, also has a "Try it out" tester |
| ReDoc | `http://127.0.0.1:8000/redoc` | Read-only, cleanest for just browsing the schema |

The raw OpenAPI schema is at `http://127.0.0.1:8000/openapi.json` if you want
to feed it to another tool (Postman, an SDK generator, etc.).

## Using the API

With the server running (and Ollama up — see below):

1. **(Optional but recommended) Ingest reference material.** Anything about
   allergen synonyms, cross-reactivity, or labeling conventions that should
   inform the risk assessment:

   ```bash
   curl -X POST http://127.0.0.1:8000/documents \
     -F "file=@allergen_reference.txt"
   ```

2. **(Optional) Sanity-check retrieval** with a plain semantic search before
   running a full check:

   ```bash
   curl -X POST http://127.0.0.1:8000/search \
     -H "Content-Type: application/json" \
     -d '{"query": "milk protein synonyms casein whey", "top_k": 3}'
   ```

3. **Run the actual allergy check** — the main endpoint. Give it the
   patient's known allergies and the product's ingredients:

   ```bash
   curl -X POST http://127.0.0.1:8000/allergies/check \
     -H "Content-Type: application/json" \
     -d '{
       "patient_allergies": ["peanuts", "shellfish"],
       "product_name": "Thai Peanut Sauce",
       "ingredients_text": "water, peanut butter, soy sauce, natural flavors, spices"
     }'
   ```

   Read `risk_level` / `is_safe` for a quick verdict, `matches` for the
   per-allergen evidence, and `notification` for a ready-to-display alert.
   Set `"use_documents": false` in the request if you only want the
   ingredients text analyzed, without pulling in any ingested reference docs.

4. **Manage ingested documents** as needed — `GET /documents` to list them,
   `DELETE /documents/{document_id}` to remove one.

See the [Endpoints](#endpoints) section below for the full request/response
shapes, or just open `/scalar` and try requests interactively.

## Testing

```bash
pip install -r requirements-dev.txt
pytest
```

The suite covers every endpoint (health, document upload/list/delete,
search, allergy-check) plus the pure ingestion/chunking logic. It's fully
self-contained: each test gets a disposable Chroma store, and the Ollama
call is mocked with a canned schema-valid response, so `pytest` runs fast
and doesn't need Ollama running.

`tests/test_live_ollama.py` is the exception — it exercises the real Ollama
call end-to-end and is auto-skipped unless Ollama is reachable at
`OLLAMA_BASE_URL`. Once your container is up and the model is pulled:

```bash
pytest tests/test_live_ollama.py -v
```

## Endpoints

| Method | Path                        | Description                                   |
| ------ | --------------------------- | ---------------------------------------------- |
| GET    | `/health`                   | Health check                                   |
| POST   | `/documents`                | Upload & ingest a document (multipart `file`)  |
| GET    | `/documents`                | List ingested documents                        |
| DELETE | `/documents/{document_id}`  | Delete a document and its chunks               |
| POST   | `/search`                   | Semantic search over ingested documents        |
| POST   | `/allergies/check`          | Run an allergy-risk check (the main endpoint)  |

### Example: ingest a reference document

```bash
curl -X POST http://127.0.0.1:8000/documents \
  -F "file=@allergen_reference.txt"
```

### Example: check a product against a patient's allergies

```bash
curl -X POST http://127.0.0.1:8000/allergies/check \
  -H "Content-Type: application/json" \
  -d '{
    "patient_allergies": ["peanuts", "shellfish"],
    "product_name": "Thai Peanut Sauce",
    "ingredients_text": "water, peanut butter, soy sauce, natural flavors, spices"
  }'
```

Response shape:

```json
{
  "risk_level": "confirmed",
  "is_safe": false,
  "matches": [
    {
      "allergen": "peanuts",
      "matched_term": "peanut butter",
      "confidence": "high",
      "evidence": "Ingredient list explicitly includes peanut butter."
    }
  ],
  "notification": {
    "title": "Do not consume: contains peanuts",
    "message": "This product lists peanut butter as an ingredient, which matches your peanut allergy. Avoid this product.",
    "severity": "danger"
  },
  "reasoning_summary": "...",
  "sources": [],
  "cached": false
}
```

## Configuration

All settings are environment variables (see `.env.example`):

- `OLLAMA_BASE_URL` (default `http://localhost:11434`), `OLLAMA_MODEL`
  (default `qwen2.5:7b-instruct`)
- `OLLAMA_TEMPERATURE` (default `0.2` — kept low since this is a
  fact-checking task, not creative generation), `OLLAMA_NUM_PREDICT` (output
  token cap), `OLLAMA_KEEP_ALIVE` (how long Ollama keeps the model loaded
  in memory between requests), `OLLAMA_REQUEST_TIMEOUT`
- `CHROMA_PERSIST_DIR`, `DOCUMENTS_REGISTRY_PATH` — local storage locations
- `CHUNK_SIZE`, `CHUNK_OVERLAP`, `DEFAULT_TOP_K` — retrieval tuning
- `CACHE_TTL_SECONDS`, `CACHE_MAX_SIZE` — allergy-check response cache

## Notes / limitations

- Single-process design: the document registry is a JSON file and the
  response cache is in-memory. Fine for local/dev use; swap in a real
  database and a shared cache (e.g. Redis) before running multiple workers.
- Structured-output enforcement quality depends on the Ollama model — smaller
  models occasionally still deviate from the schema. `analyze_allergy_risk`
  will raise a clear error (surfaced as a 502) rather than silently returning
  malformed data if that happens.
- This is a decision-support tool, not a medical device — always defer to a
  qualified professional and the product's official label for actual
  consumption decisions.
