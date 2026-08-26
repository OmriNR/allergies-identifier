import pytest_asyncio


@pytest_asyncio.fixture(autouse=True)
async def _beanie_initialized(mongo_db):
    """Beanie Documents need init_beanie() to have run even just to be
    constructed (not only to be saved), so every model test needs this
    regardless of whether it touches the DB."""
    yield
