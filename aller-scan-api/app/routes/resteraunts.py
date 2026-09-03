from typing import Any

from beanie.exceptions import RevisionIdWasChanged
from fastapi import APIRouter, HTTPException, Query, status
from pymongo import errors

from .. import schemas, models

router = APIRouter()

@router.post("/", response_model=schemas.Resteraunt, status_code=status.HTTP_201_CREATED)
async def create_resteraunt(resteraunt_in: schemas.ResterauntCreate):
    existing_resteraunt = await models.Resteraunt.get(resteraunt_in.google_maps_id)

    if existing_resteraunt is not None:
        raise HTTPException(status_code=400, detail="Resteraunt already exist")

    resteraunt = models.Resteraunt(
        id=resteraunt_in.google_maps_id,
        added_by=resteraunt_in.added_by,
        opening_times=resteraunt_in.opening_times,
        location=resteraunt_in.location,
        website_url=resteraunt_in.website_url,
        menu_items=resteraunt_in.menu_items,
        properties=resteraunt_in.properties,
    )

    try:
        await resteraunt.create()
        return resteraunt
    except errors.DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Resteraunt with that google_maps_id already exist"
        )

@router.put("/{resteraunt_id}", response_model=schemas.Resteraunt)
async def update_resteraunt(resteraunt_id: str, update: schemas.ResterauntUpdate):
    return "check"

@router.delete("/{resteraunt_id}", response_model=schemas.Resteraunt)
async def delete_resteraunt(reseraunt_id: str):
    return "check"


@router.get("get_by_id/{resteraunt_id}", response_model=schemas.Resteraunt)
async def get_by_id(resteraunt_id: str):
    return "check"

@router.post("get_closest/radius:{radius}", response_model=list[schemas.Resteraunt])
async def get_closest_by_radius(radius: float, location: models.Location):
    return "check"
