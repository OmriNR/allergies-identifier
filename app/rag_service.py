"""Orchestrates ingestion, retrieval, and the Ollama allergy-risk call."""

import asyncio
import hashlib
import json
import threading

from cachetools import TTLCache

from app import ollama_client, vectorstore
from app.config import Settings
from app.ingestion import chunk_text, extract_text
from app.schemas import (
    AllergenMatch,
    AllergyCheckRequest,
    AllergyCheckResponse,
    DocumentListResponse,
    DocumentMetadata,
    DocumentUploadResponse,
    NotificationPayload,
    SearchQuery,
    SearchResponse,
    SearchResult,
    SourceRef,
)

_registry: vectorstore.DocumentRegistry | None = None
_registry_lock = threading.Lock()

_check_cache: TTLCache | None = None
_cache_lock = threading.Lock()


def _get_registry(settings: Settings) -> vectorstore.DocumentRegistry:
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = vectorstore.DocumentRegistry(settings.documents_registry_path)
    return _registry


def _get_cache(settings: Settings) -> TTLCache:
    global _check_cache
    if _check_cache is None:
        with _cache_lock:
            if _check_cache is None:
                _check_cache = TTLCache(
                    maxsize=settings.cache_max_size, ttl=settings.cache_ttl_seconds
                )
    return _check_cache


def warm_up(settings: Settings) -> None:
    """Force-initialize the embedding model and vector store at startup so the
    first real request doesn't pay cold-start latency."""
    vectorstore.get_collection(settings)
    _get_registry(settings)
    _get_cache(settings)


async def ingest_document(
    settings: Settings, filename: str, content_type: str, content: bytes
) -> DocumentUploadResponse:
    def _work() -> DocumentMetadata:
        text = extract_text(filename, content)
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise ValueError(f"No extractable text found in '{filename}'.")

        registry = _get_registry(settings)
        doc = registry.add(filename, content_type, len(chunks))
        vectorstore.add_document_chunks(settings, doc.id, filename, chunks)
        return doc

    doc = await asyncio.to_thread(_work)
    return DocumentUploadResponse(document=doc)


async def list_documents(settings: Settings) -> DocumentListResponse:
    registry = _get_registry(settings)
    docs = await asyncio.to_thread(registry.list)
    docs.sort(key=lambda d: d.created_at, reverse=True)
    return DocumentListResponse(documents=docs)


async def delete_document(settings: Settings, document_id: str) -> bool:
    registry = _get_registry(settings)

    def _work() -> bool:
        deleted = registry.delete(document_id)
        if deleted:
            vectorstore.delete_document_chunks(settings, document_id)
        return deleted

    return await asyncio.to_thread(_work)


async def search_documents(settings: Settings, request: SearchQuery) -> SearchResponse:
    def _work() -> list[SearchResult]:
        return vectorstore.query(
            settings,
            query_text=request.query,
            top_k=request.top_k,
            document_id=request.document_id,
        )

    results = await asyncio.to_thread(_work)
    return SearchResponse(results=results)


def _cache_key(request: AllergyCheckRequest) -> str:
    payload = {
        "allergies": sorted(a.strip().lower() for a in request.patient_allergies),
        "product_name": (request.product_name or "").strip().lower(),
        "ingredients_text": (request.ingredients_text or "").strip().lower(),
        "use_documents": request.use_documents,
        "document_ids": sorted(request.document_ids or []),
        "top_k": request.top_k,
    }
    raw = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


async def check_allergies(
    settings: Settings, request: AllergyCheckRequest
) -> AllergyCheckResponse:
    cache = _get_cache(settings)
    key = _cache_key(request)
    cached = cache.get(key)
    if cached is not None:
        return cached.model_copy(update={"cached": True})

    retrieved: list[SearchResult] = []
    if request.use_documents:
        query_text = " ".join(
            filter(
                None,
                [
                    request.product_name,
                    request.ingredients_text,
                    "allergens: " + ", ".join(request.patient_allergies),
                ],
            )
        )

        def _search() -> list[SearchResult]:
            return vectorstore.query(
                settings,
                query_text=query_text,
                top_k=request.top_k,
                document_ids=request.document_ids,
            )

        retrieved = await asyncio.to_thread(_search)

    result = await ollama_client.analyze_allergy_risk(
        settings,
        patient_allergies=request.patient_allergies,
        product_name=request.product_name,
        ingredients_text=request.ingredients_text,
        retrieved_context=retrieved,
    )

    response = AllergyCheckResponse(
        risk_level=result["risk_level"],
        is_safe=result["is_safe"],
        matches=[AllergenMatch(**m) for m in result["matches"]],
        notification=NotificationPayload(
            title=result["notification_title"],
            message=result["notification_message"],
            severity=result["notification_severity"],
        ),
        reasoning_summary=result["reasoning_summary"],
        sources=[
            SourceRef(
                document_id=r.document_id,
                filename=r.filename,
                chunk_index=r.chunk_index,
                excerpt=r.text[:280],
            )
            for r in retrieved
        ],
        cached=False,
    )

    cache[key] = response
    return response
