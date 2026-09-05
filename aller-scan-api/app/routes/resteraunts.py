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
    resteraunt = await models.Resteraunt.get(resteraunt_id)

    if resteraunt is None:
        raise HTTPException(status_code=404, detail="Resteraunt not found")

    updated_data = update.model_dump(exclude=True)

    updated_resteraunt = resteraunt.model_copy(update=updated_data)

    try:
        await updated_resteraunt.save()
        return updated_resteraunt
    except (errors.DuplicateKeyError, RevisionIdWasChanged):
        raise HTTPException(status_code=400, detail="Resteraunt with that google id is already exist")
    

@router.delete("/{resteraunt_id}", response_model=schemas.Resteraunt)
async def delete_resteraunt(reseraunt_id: str):
    resteraunt = await models.Resteraunt.get(reseraunt_id)

    if resteraunt is None:
         raise HTTPException(status_code=404, detail="resteraunt not found")

    await resteraunt.delete()

    return resteraunt


@router.get("/nearby", response_model=list[schemas.Resteraunt])
async def get_nearby(
    latitude: float = Query(..., ge=-90, le=90, description="User latitude"),
    longitude: float = Query(..., ge=-180, le=180, description="User longitude"),
    radius_meters: float = Query(1000.0, gt=0, description="radius in meters")):
        close_restaurants = await models.Resteraunt.find(
            {
                "location.coordinates": {
                    "$near": {
                        "$geometry": {
                            "type": "Point",
                            "coordinates": [longitude, latitude]
                        },
                        "$maxDistance": radius_meters
                    }
                }
            }
        ).to_list()

        if len(close_restaurants) == 0:
            raise HTTPException(status_code=404, detail="Close resteraunts were not found, please increase the radius")

        return close_restaurants

@router.get("/{resteraunt_id}", response_model=schemas.Resteraunt)
async def get_by_id(resteraunt_id: str):
    resteraunt = await models.Resteraunt.get(resteraunt_id)

    if resteraunt is None:
        raise HTTPException(status_code=404, detail="resteraunt not found")

    return resteraunt
