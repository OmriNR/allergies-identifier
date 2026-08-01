"""Local, on-disk vector store for ingested medical documents.

Uses Chroma's built-in ONNX MiniLM embedding function — it runs fully
on-CPU with no network round-trip per request, which keeps ingestion and
retrieval fast without adding a heavy ML dependency like torch.
"""

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

from app.config import Settings
from app.schemas import DocumentMetadata, SearchResult

COLLECTION_NAME = "medical_documents"

_client: chromadb.ClientAPI | None = None
_collection = None
_client_lock = threading.Lock()


def get_collection(settings: Settings):
    """Lazily create (once) and return the shared Chroma collection.

    Safe to call from multiple threads (e.g. via asyncio.to_thread) — the
    client/collection are created once and cached.
    """
    global _client, _collection
    if _collection is not None:
        return _collection

    with _client_lock:
        if _collection is None:
            Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
            _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
            embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            _collection = _client.get_or_create_collection(
                name=COLLECTION_NAME,
                embedding_function=embedding_fn,
                # Cosine distance keeps the similarity score bounded (0-1) below;
                # Chroma's default L2 distance is unbounded and not comparable
                # across queries.
                metadata={"hnsw:space": "cosine"},
            )
    return _collection


def add_document_chunks(
    settings: Settings,
    document_id: str,
    filename: str,
    chunks: list[str],
) -> None:
    collection = get_collection(settings)
    ids = [f"{document_id}::{i}" for i in range(len(chunks))]
    metadatas = [
        {"document_id": document_id, "filename": filename, "chunk_index": i}
        for i in range(len(chunks))
    ]
    collection.add(ids=ids, documents=chunks, metadatas=metadatas)


def query(
    settings: Settings,
    query_text: str,
    top_k: int,
    document_id: str | None = None,
    document_ids: list[str] | None = None,
) -> list[SearchResult]:
    collection = get_collection(settings)
    if collection.count() == 0:
        return []

    where = None
    if document_id:
        where = {"document_id": document_id}
    elif document_ids:
        where = {"document_id": {"$in": document_ids}}

    result = collection.query(
        query_texts=[query_text],
        n_results=min(top_k, collection.count()),
        where=where,
    )

    out: list[SearchResult] = []
    documents = result.get("documents") or [[]]
    metadatas = result.get("metadatas") or [[]]
    distances = result.get("distances") or [[]]
    for text, meta, distance in zip(documents[0], metadatas[0], distances[0]):
        # Chroma returns a cosine distance by default; convert to a 0-1 similarity score.
        score = max(0.0, 1.0 - distance)
        out.append(
            SearchResult(
                text=text,
                score=round(score, 4),
                document_id=meta["document_id"],
                filename=meta["filename"],
                chunk_index=meta["chunk_index"],
            )
        )
    return out


def delete_document_chunks(settings: Settings, document_id: str) -> None:
    collection = get_collection(settings)
    collection.delete(where={"document_id": document_id})


class DocumentRegistry:
    """Small JSON-backed registry of ingested-document metadata.

    Chroma has no first-class "list distinct documents" query, so we track
    document-level metadata (filename, chunk count, upload time) separately.
    """

    def __init__(self, path: str):
        self._path = Path(path)
        self._lock = threading.Lock()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write({})

    def _read(self) -> dict:
        if not self._path.exists():
            return {}
        with open(self._path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data: dict) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)

    def add(self, filename: str, content_type: str, chunk_count: int) -> DocumentMetadata:
        with self._lock:
            data = self._read()
            document_id = uuid.uuid4().hex
            record = {
                "id": document_id,
                "filename": filename,
                "content_type": content_type,
                "chunk_count": chunk_count,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            data[document_id] = record
            self._write(data)
            return DocumentMetadata(**record)

    def list(self) -> list[DocumentMetadata]:
        with self._lock:
            data = self._read()
        return [DocumentMetadata(**record) for record in data.values()]

    def get(self, document_id: str) -> DocumentMetadata | None:
        with self._lock:
            data = self._read()
        record = data.get(document_id)
        return DocumentMetadata(**record) if record else None

    def delete(self, document_id: str) -> bool:
        with self._lock:
            data = self._read()
            if document_id not in data:
                return False
            del data[document_id]
            self._write(data)
            return True
