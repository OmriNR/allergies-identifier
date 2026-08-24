"""Shared pytest fixtures.

These tests describe the API this project intends to build; most will fail
(or error at collection) until the corresponding routes/models exist. See
tests/README.md for the assumed API contract and known pre-existing issues.
"""

import os

# The Settings classes require these env vars with no defaults. Setting them
# here (rather than relying on a .env file) keeps the test suite runnable in
# any environment without needing real secrets or a real Mongo instance.
os.environ.setdefault("PROJECT_NAME", "aller-scan-api-test")
os.environ.setdefault("FIRST_SUPERUSER", "admin@example.com")
os.environ.setdefault("FIRST_SUPERUSER_PASSWORD", "supersecret123")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("MONGO_HOST", "localhost")
os.environ.setdefault("MONGO_PORT", "27017")
os.environ.setdefault("MONGO_DB", "aller_scan_test")
os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGODB_DB_NAME", "aller_scan_test")

import pytest
import pytest_asyncio
from beanie import init_beanie
from httpx import ASGITransport, AsyncClient
from mongomock.database import Database as _MongoMockDatabase
from mongomock_motor import AsyncMongoMockClient

from app.models import DOCUMENT_MODELS

from .factories import login_payload, user_payload

# mongomock's list_collection_names() doesn't accept the
# authorizedCollections/nameOnly kwargs that beanie's newer init_beanie()
# passes through (a real pymongo AsyncMongoClient does accept them). Shim it
# so the mock DB can still be used to init Beanie.
_original_list_collection_names = _MongoMockDatabase.list_collection_names


def _list_collection_names(self, filter=None, session=None, **_ignored_kwargs):
    return _original_list_collection_names(self, filter=filter, session=session)


_MongoMockDatabase.list_collection_names = _list_collection_names


@pytest_asyncio.fixture
async def mongo_db():
    """A fresh in-memory Mongo database, wired up to Beanie, per test."""
    client = AsyncMongoMockClient()
    db = client["aller_scan_test"]
    await init_beanie(database=db, document_models=DOCUMENT_MODELS)
    yield db


@pytest_asyncio.fixture
async def app(mongo_db, monkeypatch):
    """The FastAPI app, with real DB startup replaced by the mock DB above."""
    import app.main as main_module

    async def _noop_init_db() -> None:
        return None

    monkeypatch.setattr(main_module, "init_db", _noop_init_db)
    return main_module.app


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def registered_user(client):
    """Registers a user via the API and returns the registration payload."""
    payload = user_payload()
    response = await client.post("/api/v1/users/", json=payload)
    assert response.status_code == 201, response.text
    return payload


@pytest_asyncio.fixture
async def auth_headers(client, registered_user):
    """Logs the registered_user in and returns Bearer auth headers."""
    response = await client.post(
        "/api/v1/login/access-token", data=login_payload(registered_user)
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
