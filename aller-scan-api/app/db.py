from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config import settings
from app.models import DOCUMENT_MODELS

client = AsyncMongoClient(settings.mongodb_uri)


async def init_db() -> None:
    await init_beanie(
        database=client[settings.mongodb_db_name],
        document_models=DOCUMENT_MODELS,
    )
