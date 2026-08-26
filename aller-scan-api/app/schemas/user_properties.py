from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..models.user_properties import ScanStatus


class AllergyPreferenceCreate(BaseModel):
    user_id: UUID
    allergies: list[str]


class AllergyPreferenceUpdate(BaseModel):
    userid: UUID
    allergies: list[str]


class AllergyPreference(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    allergies: list[str]
    updated_at: datetime


class ScanHistoryCreate(BaseModel):
    user_id: UUID
    product_id: UUID
    barcode: str
    product_name: str
    brand: str | None = None
    status: ScanStatus
    detected_allergens: list[str] = []


class ScanHistory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    product_id: UUID
    barcode: str
    product_name: str
    brand: str | None = None
    status: ScanStatus
    detected_allergens: list[str]
    created_at: datetime
