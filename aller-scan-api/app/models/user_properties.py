from datetime import UTC, datetime
from enum import Enum
from typing import Annotated
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import Field


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


class ScanStatus(str, Enum):
    SAFE = "safe"
    DANGEROUS = "dangerous"


class ScanHistory(Document):
    id: UUID = Field(default_factory=uuid4)
    user_id: Annotated[UUID, Indexed()]
    product_id: Annotated[UUID, Indexed()]
    barcode: str
    product_name: str
    brand: str | None = None
    status: ScanStatus
    detected_allergens: list[str] = []
    created_at: datetime = Field(default_factory=get_datetime_utc)

    class Settings:
        name = "scan_history"


class AllergyPreference(Document):
    user_id: Annotated[UUID, Indexed(unique=True)]
    allergies: list[str] = []
    updated_at: datetime = Field(default_factory=get_datetime_utc)

    class Settings:
        name = "allergy_preferences"
