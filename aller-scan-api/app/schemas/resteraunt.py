from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from ..models.resteraunt import Location, MenuItem

class ResterauntCreate(BaseModel):
    google_maps_id: str = Field(min_length=1)
    added_by: UUID
    resteraunt_name: str = Field(min_length=1)
    opening_times: list[str] = Field(min_length=1)
    location: Location
    menu_items: list[MenuItem] = Field(min_length=1)
    website_url: str | None = Field(default=None, min_length=1)
    properties: dict[str, bool] = {}

class ResterauntUpdate(BaseModel):
    opening_times: list[str] = Field(min_length=1)
    menu_items: list[MenuItem] = Field(min_length=1)
    website_url: str | None = Field(default=None, min_length=1)
    properties: dict[str, bool] = {}

class Resteraunt(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    added_by: UUID
    opening_times: list[str] = []
    location: Location
    website_url: str | None = None
    menu_items: list[MenuItem] = []
    properties: dict[str, bool] = {}
