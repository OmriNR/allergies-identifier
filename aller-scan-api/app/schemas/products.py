from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ..models.product import ProductSource


class ProductCreate(BaseModel):
    barcode: str
    product_name: str
    brand: str | None = None
    allergens: list[str] = []
    source: ProductSource = ProductSource.MANUAL


class Product(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    barcode: str
    product_name: str
    brand: str | None = None
    allergens: list[str] = []
    source: ProductSource = ProductSource.MANUAL
    created_at: datetime


class ProductFilter(BaseModel):
    brand: str | None = None
    product_name: str | None = None
    allergens: list[str] | None = None
