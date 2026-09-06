from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import BaseModel, Field


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


class DetectedAllergen(BaseModel):
    allergen: str
    display_name: str
    triggered_by: list[str] = []


class AllergenProfile(Document):
    id: UUID = Field(default_factory=uuid4)
    barcode: Annotated[str, Indexed(unique=True)]
    detected_allergens: list[DetectedAllergen] = []
    detection_source: str
    created_at: datetime = Field(default_factory=get_datetime_utc)
    updated_at: datetime = Field(default_factory=get_datetime_utc)

    class Settings:
        name = "allergen_profiles"
