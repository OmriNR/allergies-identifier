from beanie import init_beanie
from pymongo import AsyncMongoClient

from app.config.config import settings
from app.models import DOCUMENT_MODELS

client = AsyncMongoClient(
    settings.MONGO_HOST,
    settings.MONGO_PORT,
    username=settings.MONGO_USER,
    password=settings.MONGO_PASSWORD,
)


async def init_db() -> None:
    await init_beanie(
        database=client[settings.MONGO_DB],
        document_models=DOCUMENT_MODELS,
    )
