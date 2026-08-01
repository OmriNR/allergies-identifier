import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from scalar_fastapi import get_scalar_api_reference

from app import ollama_client, rag_service
from app.config import get_settings
from app.ingestion import UnsupportedDocumentError
from app.ollama_client import OllamaError, OllamaModelNotFoundError, OllamaUnreachableError
from app.schemas import (
    AllergyCheckRequest,
    AllergyCheckResponse,
    DocumentListResponse,
    DocumentUploadResponse,
    SearchQuery,
    SearchResponse,
)

TAGS_METADATA = [
    {"name": "Health", "description": "Liveness check."},
    {
        "name": "Documents",
        "description": "Ingest and manage the reference documents (allergen "
        "synonyms, cross-reactivity notes, etc.) used as RAG context.",
    },
    {"name": "Search", "description": "Raw semantic search over ingested documents."},
    {
        "name": "Allergies",
        "description": "The main endpoint: check a product's ingredients against "
        "a patient's known allergies.",
    },
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # Warm the embedding model + vector store, and ask Ollama to load the
    # model into memory now, so the first real request doesn't pay
    # cold-start latency.
    await asyncio.to_thread(rag_service.warm_up, settings)
    await ollama_client.warm_up(settings)
    yield


app = FastAPI(
    title="Allergy Identifier API",
    description=(
        "RAG API that searches ingested medical/ingredient documents and "
        "uses a local Ollama model to flag potential allergen matches "
        "against a patient's known allergies.\n\n"
        "Typical flow: `POST /documents` to ingest reference material (optional "
        "but recommended) → `POST /allergies/check` with a patient's allergies "
        "and a product's ingredients to get a risk assessment + notification."
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=TAGS_METADATA,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/scalar", include_in_schema=False)
async def scalar_docs() -> HTMLResponse:
    """Modern API reference UI (alternative to /docs and /redoc)."""
    return get_scalar_api_reference(openapi_url=app.openapi_url, title=app.title)


@app.get("/")
async def root():
    return {
        "name": "Allergy Identifier API",
        "docs": ["/docs", "/redoc", "/scalar"],
        "endpoints": [
            "GET /health",
            "POST /documents",
            "GET /documents",
            "DELETE /documents/{document_id}",
            "POST /search",
            "POST /allergies/check",
        ],
    }


@app.get("/health", tags=["Health"], summary="Health check")
async def health():
    return {"status": "ok"}


@app.post(
    "/documents",
    response_model=DocumentUploadResponse,
    status_code=201,
    tags=["Documents"],
    summary="Ingest a reference document",
    description="Upload a `.txt`, `.md`, or `.pdf` file. It's chunked and "
    "embedded into the local vector store, then available as retrieval "
    "context for `/search` and `/allergies/check`.",
)
async def upload_document(file: UploadFile):
    settings = get_settings()
    content = await file.read()

    if len(content) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File exceeds max upload size of {settings.max_upload_bytes} bytes.",
        )

    try:
        return await rag_service.ingest_document(
            settings,
            filename=file.filename or "upload",
            content_type=file.content_type or "application/octet-stream",
            content=content,
        )
    except UnsupportedDocumentError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get(
    "/documents",
    response_model=DocumentListResponse,
    tags=["Documents"],
    summary="List ingested documents",
)
async def list_documents():
    settings = get_settings()
    return await rag_service.list_documents(settings)


@app.delete(
    "/documents/{document_id}",
    status_code=204,
    tags=["Documents"],
    summary="Delete a document",
    description="Removes the document's metadata and all of its chunks from the vector store.",
)
async def delete_document(document_id: str):
    settings = get_settings()
    deleted = await rag_service.delete_document(settings, document_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found.")


@app.post(
    "/search",
    response_model=SearchResponse,
    tags=["Search"],
    summary="Semantic search over ingested documents",
)
async def search(request: SearchQuery):
    settings = get_settings()
    return await rag_service.search_documents(settings, request)


@app.post(
    "/allergies/check",
    response_model=AllergyCheckResponse,
    tags=["Allergies"],
    summary="Check ingredients against a patient's allergies",
    description="Retrieves supporting context from ingested documents (unless "
    "`use_documents` is false) and asks the local Ollama model to assess "
    "allergy risk, returning matched allergens with evidence and a "
    "ready-to-send patient notification. Identical requests are served from "
    "an in-process cache (see `cached` in the response).",
)
async def check_allergies(request: AllergyCheckRequest):
    if not request.ingredients_text and not request.use_documents:
        raise HTTPException(
            status_code=400,
            detail="Provide ingredients_text and/or set use_documents=true so "
            "there is something to analyze.",
        )

    settings = get_settings()
    try:
        return await rag_service.check_allergies(settings, request)
    except OllamaUnreachableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OllamaModelNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OllamaError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504, detail="Ollama took too long to respond."
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama returned an error: {exc.response.status_code}",
        ) from exc
