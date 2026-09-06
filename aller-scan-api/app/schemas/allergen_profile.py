from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DetectedAllergen(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    allergen: str
    display_name: str
    triggered_by: list[str]


class AllergenProfile(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    barcode: str
    detected_allergens: list[DetectedAllergen]
    detection_source: str
    created_at: datetime
    updated_at: datetime


class AllergenCheckRequest(BaseModel):
    barcode: str
    ingredients: list[str]
    user_id: UUID | None = None


class AllergenCheckResponse(BaseModel):
    profile: AllergenProfile
    from_cache: bool
    matched_user_allergens: list[str] = []
    warning: bool = False
