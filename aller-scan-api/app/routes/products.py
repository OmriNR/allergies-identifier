import re
from typing import Any
from uuid import UUID

from beanie.exceptions import RevisionIdWasChanged
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import errors

from .. import models, schemas

router = APIRouter()

@router.post("/", response_model=schemas.Product, status_code=status.HTTP_201_CREATED)
async def create_product(product_in: schemas.ProductCreate):
    barcode_product = await models.Product.find_one({"barcode": product_in.barcode})

    if barcode_product is not None:
        raise HTTPException(status_code=400, detail="Product already exist")

    product = models.Product(
        barcode=product_in.barcode,
        product_name=product_in.product_name,
        brand=product_in.brand,
        allergens=product_in.allergens,
        source=product_in.source
    )

    try:
        await product.create()
        return product
    except errors.DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with that barcode already exist"
        )

@router.post("/list_of_products", response_model=list[schemas.Product])
async def list_of_products(
    filters: schemas.ProductFilter,
    limit: int | None = 10,
    offset: int | None = 0,
):
    query: dict[str, Any] = {}

    if filters.brand is not None:
        query["brand"] = filters.brand

    if filters.product_name is not None:
        query["product_name"] = {
            "$regex": re.escape(filters.product_name),
            "$options": "i",
        }

    if filters.allergens is not None:
        query["allergens"] = {"$in": filters.allergens}

    products = await models.Product.find(query).skip(offset).limit(limit).to_list()
    return products

@router.get("/brands", response_model=list[str])
async def get_brands():
    brands = await models.Product.find_all().distinct("brand")
    return sorted(brand for brand in brands if brand is not None)

@router.get("/get_by_id/{product_id}", response_model=list[schemas.Product])
async def get_product_by_id(product_id: UUID):
    product = await models.Product.get(product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product

@router.get("/get_by_barcode/{product_barcode}", response_model=list[schemas.Product])
async def get_product_by_id(product_barcode: str):
    product = await models.Product.find_one({"bracode": product_barcode})

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return product

