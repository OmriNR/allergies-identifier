from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=1)
    email: EmailStr
    password: str = Field(min_length=8)


class UserUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    avatar_url: str | None = None


class User(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uuid: UUID
    name: str
    email: EmailStr
    avatar_url: str | None = None
    is_active: bool
    created_at: datetime
