"""Text extraction and chunking for ingested medical documents."""

import io
import re

from pypdf import PdfReader

SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}


class UnsupportedDocumentError(ValueError):
    pass


def extract_text(filename: str, content: bytes) -> str:
    """Extract raw text from an uploaded document's bytes based on its extension."""
    lower = filename.lower()
    if any(lower.endswith(ext) for ext in SUPPORTED_PDF_EXTENSIONS):
        return _extract_pdf_text(content)
    if any(lower.endswith(ext) for ext in SUPPORTED_TEXT_EXTENSIONS):
        return content.decode("utf-8", errors="replace")
    raise UnsupportedDocumentError(
        f"Unsupported file type for '{filename}'. Supported: .txt, .md, .pdf"
    )


def _extract_pdf_text(content: bytes) -> str:
    reader = PdfReader(io.BytesIO(content))
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 120) -> list[str]:
    """Split text into overlapping chunks, breaking on paragraph/sentence boundaries
    where possible so retrieved context stays coherent."""
    text = re.sub(r"\r\n?", "\n", text).strip()
    if not text:
        return []

    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}" if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
        if len(paragraph) <= chunk_size:
            current = paragraph
        else:
            # Paragraph itself is too long — split on sentence boundaries.
            sentences = re.split(r"(?<=[.!?])\s+", paragraph)
            current = ""
            for sentence in sentences:
                candidate = f"{current} {sentence}".strip()
                if len(candidate) <= chunk_size:
                    current = candidate
                else:
                    if current:
                        chunks.append(current)
                    current = sentence[:chunk_size]

    if current:
        chunks.append(current)

    if overlap > 0 and len(chunks) > 1:
        chunks = _apply_overlap(chunks, overlap)

    return chunks


def _apply_overlap(chunks: list[str], overlap: int) -> list[str]:
    overlapped = [chunks[0]]
    for prev, current in zip(chunks, chunks[1:]):
        tail = prev[-overlap:]
        overlapped.append(f"{tail}\n{current}")
    return overlapped
