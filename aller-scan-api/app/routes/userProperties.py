from typing import Any
from uuid import UUID

from beanie.exceptions import RevisionIdWasChanged
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo import errors

from .. import models, schemas

router = APIRouter()

@router.get("/allergies/{userid}", response_model=schemas.AllergyPreference)
async def get_allergy_preference_by_user(userid: UUID):
    allergy_perference = await models.AllergyPreference.find_one({"user_id": userid})

    if allergy_perference is None:
        raise HTTPException(status_code=404, detail="Allergy perference of user was not found, please create")
    return allergy_perference

@router.put("/allergies/{userid}", response_model=schemas.AllergyPreference)
async def update_allergy_preference(
    userid: UUID,
    update: schemas.AllergyPreferenceUpdate
) -> Any:
    allergy_perference = await models.AllergyPreference.find_one({"user_id": userid})

    if allergy_perference is None:
        raise HTTPException(status_code=404, detail="Perference not found")

    updated_perference = allergy_perference.model_copy(update={"allergies": update.allergies})

    try:
        await updated_perference.save()
        return updated_perference
    except (errors.DuplicateKeyError, RevisionIdWasChanged):
        raise HTTPException(
            status_code=400, detail="Perference of this user already exists"
        )

@router.post("/allergies", response_model=schemas.AllergyPreference, status_code=status.HTTP_201_CREATED)
async def create_perference(perference_in: schemas.AllergyPreferenceCreate):

    user = await models.User.find_one({"uuid": perference_in.user_id})

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    exist_perference = await models.AllergyPreference.find_one({"user_id": perference_in.user_id})

    if exist_perference is not None:
        raise HTTPException(status_code=400, detail="Can't create new perference with user that already has, please use the update endpoint")

    perference = models.AllergyPreference(
        user_id=perference_in.user_id,
        allergies=perference_in.allergies
    )

    try:
        await perference.create()
        return perference
    except errors.DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Can't create perference twice"
        )

@router.get("/scan-history/users/{userid}", response_model=list[schemas.ScanHistory])
async def get_scan_history_by_user(userid: UUID):
    user = await models.User.find_one({"uuid": userid})

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return await models.ScanHistory.find({"user_id": userid}).to_list()

@router.post("/scan-history", response_model=schemas.ScanHistory, status_code=status.HTTP_201_CREATED)
async def create_scan_history(scan_in: schemas.ScanHistoryCreate):
    user = await models.User.find_one({"uuid": scan_in.user_id})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    product = await models.Product.get(scan_in.product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    scan = models.ScanHistory(
        user_id=scan_in.user_id,
        product_id=scan_in.product_id,
        barcode=scan_in.barcode,
        product_name=scan_in.product_name,
        brand=scan_in.brand,
        status=scan_in.status,
        detected_allergens=scan_in.detected_allergens,
    )
    await scan.create()
    return scan

@router.get("/scan-history/products/{product_id}", response_model=list[schemas.ScanHistory])
async def get_scan_history_by_product(
    product_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
):
    product = await models.Product.get(product_id)

    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    return await models.ScanHistory.find({"product_id": product_id}).limit(limit).to_list()