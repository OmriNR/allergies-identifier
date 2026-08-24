from typing import Any
from uuid import UUID

from beanie.exceptions import RevisionIdWasChanged
from fastapi import APIRouter, Depends, HTTPException, status
from pymongo import errors

from .. import models, schemas
from ..auth.auth import (
    get_current_active_user,
    get_hashed_password,
)

router = APIRouter()

@router.post("/", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
async def register_user(user_in: schemas.UserCreate):
    hashed_password = get_hashed_password(user_in.password)

    user = models.User(
        name=user_in.name,
        email=user_in.email,
        password=hashed_password,
    )

    try:
        await user.create()
        return user
    except errors.DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with that email already exists."
        )


@router.get("/me", response_model=schemas.User)
async def get_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user


@router.get("", response_model=list[schemas.User])
async def get_users(
    limit: int | None = 10,
    offset: int | None = 0
):
    users = await models.User.find_all().skip(offset).limit(limit).to_list()
    return users

@router.patch("/me", response_model=schemas.User)
async def update_profile(
    update: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_active_user),
) -> Any:
    
    update_data = update.model_dump(exclude_unset=True)
    current_user = current_user.model_copy(update=update_data)
    try:
        await current_user.save()
        return current_user
    except (errors.DuplicateKeyError, RevisionIdWasChanged):
        raise HTTPException(
            status_code=400, detail="User with that email already exists."
        )

@router.delete("/me", response_model=schemas.User)
async def delete_me(user: models.User = Depends(get_current_active_user)):
    await user.delete()
    return user

@router.patch("/{userid}", response_model=schemas.User)
async def update_user(
    userid: UUID,
    update: schemas.UserUpdate
) -> Any:
    
    user = await models.User.find_one({"uuid": userid})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = update.model_dump(exclude=True)

    try:
        if update_data["password"]:
            update_data["password"] = get_hashed_password(update_data["password"])
    except KeyError:
        pass

    updated_user = user.model_copy(update=update_data)

    try:
        await updated_user.save()
        return updated_user
    except (errors.DuplicateKeyError, RevisionIdWasChanged):
        raise HTTPException(
            status_code=400, detail="User with that email already exists."
        )

@router.get("/{userid}", response_model=schemas.User)
async def get_user(
    userid: UUID
):
    user = await models.User.find_one({"uuid": userid})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.delete("/{userid}", response_model=schemas.User)
async def delete_user(
    userid: UUID
):
    user = await models.User.find_one({"uuid": userid})
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await user.delete()
    return user
