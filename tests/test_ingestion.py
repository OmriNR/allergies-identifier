import pytest

from app.ingestion import UnsupportedDocumentError, chunk_text, extract_text


def test_extract_text_from_txt_bytes():
    assert extract_text("notes.txt", b"hello world") == "hello world"


def test_extract_text_unsupported_extension_raises():
    with pytest.raises(UnsupportedDocumentError):
        extract_text("archive.zip", b"PK\x03\x04")


def test_chunk_text_splits_long_input():
    paragraph = "word " * 60
    text = "\n\n".join(f"Paragraph {i}: {paragraph}" for i in range(5))

    chunks = chunk_text(text, chunk_size=200, overlap=20)

    assert len(chunks) > 1
    # every chunk should be reasonably close to the requested size (allowing
    # for the sentence/paragraph-boundary splitting and overlap prefix)
    assert all(len(c) <= 260 for c in chunks)


def test_chunk_text_empty_input_returns_no_chunks():
    assert chunk_text("   \n\n   ") == []


def test_chunk_text_short_input_returns_single_chunk():
    chunks = chunk_text("Short ingredient note.", chunk_size=800, overlap=120)
    assert chunks == ["Short ingredient note."]
