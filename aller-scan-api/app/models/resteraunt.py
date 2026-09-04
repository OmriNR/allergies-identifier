from typing import Annotated
from uuid import UUID

from beanie import Document, Indexed
from pydantic import BaseModel
import pymongo

class Location(BaseModel):
    full_address: str
    coordinates: list[float] = []


class MenuItem(BaseModel):
    item_name: str
    category: str
    ingredients: list[str] = []
    allergens: list[str] = []


class Resteraunt(Document):
    id: str
    added_by: Annotated[UUID, Indexed()]
    opening_times: list[str] = []
    location: Location
    website_url: str | None = None
    menu_items: list[MenuItem] = []
    properties: dict[str, bool] = {}

    class Settings:
        name = "resteraunts"
        inexes = [
            [("location.coordinates", pymongo.GEOSPHERE)]
        ]
