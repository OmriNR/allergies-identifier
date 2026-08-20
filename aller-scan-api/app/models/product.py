from datetime import UTC, datetime
from enum import Enum
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import Field


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


class ProductSource(str, Enum):
    MANUAL = "manual"
    EXTERNAL = "external"


class Product(Document):
    id: UUID = Field(default_factory=uuid4)
    barcode: Indexed(str, unique=True)
    product_name: str
    brand: str | None = None
    allergens: list[str] = []
    source: ProductSource = ProductSource.MANUAL
    created_at: datetime = Field(default_factory=get_datetime_utc)

    class Settings:
        name = "products"
