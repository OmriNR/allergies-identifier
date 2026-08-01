import io


def _upload(client, filename: str, content: bytes, content_type: str = "text/plain"):
    return client.post(
        "/documents", files={"file": (filename, io.BytesIO(content), content_type)}
    )


def test_upload_list_delete_document_roundtrip(client):
    content = (
        b"Milk allergens: casein, whey, and lactalbumin are derived from milk protein.\n\n"
        b"Soy allergens: soy lecithin and edamame both contain soy protein."
    )
    upload_resp = _upload(client, "allergen_reference.txt", content)
    assert upload_resp.status_code == 201
    doc = upload_resp.json()["document"]
    assert doc["filename"] == "allergen_reference.txt"
    assert doc["chunk_count"] >= 1

    list_resp = client.get("/documents")
    assert list_resp.status_code == 200
    assert any(d["id"] == doc["id"] for d in list_resp.json()["documents"])

    delete_resp = client.delete(f"/documents/{doc['id']}")
    assert delete_resp.status_code == 204

    list_after = client.get("/documents").json()["documents"]
    assert all(d["id"] != doc["id"] for d in list_after)


def test_delete_unknown_document_returns_404(client):
    resp = client.delete("/documents/does-not-exist")
    assert resp.status_code == 404


def test_upload_unsupported_file_type_returns_400(client):
    resp = _upload(client, "malware.exe", b"binary junk", "application/octet-stream")
    assert resp.status_code == 400


def test_upload_oversized_file_returns_413(client, monkeypatch):
    from app.config import get_settings

    monkeypatch.setenv("MAX_UPLOAD_BYTES", "10")
    get_settings.cache_clear()

    resp = _upload(client, "small.txt", b"this is definitely more than ten bytes")
    assert resp.status_code == 413


def test_search_returns_relevant_chunk(client):
    content = b"Milk allergens: casein, whey, and lactalbumin are all derived from milk protein."
    _upload(client, "milk.txt", content)

    resp = client.post("/search", json={"query": "casein whey milk protein", "top_k": 3})
    assert resp.status_code == 200
    results = resp.json()["results"]
    assert len(results) >= 1
    assert "milk" in results[0]["text"].lower()


def test_search_with_no_documents_returns_empty_results(client):
    resp = client.post("/search", json={"query": "anything at all", "top_k": 3})
    assert resp.status_code == 200
    assert resp.json()["results"] == []


def test_search_rejects_empty_query(client):
    resp = client.post("/search", json={"query": "", "top_k": 3})
    assert resp.status_code == 422
