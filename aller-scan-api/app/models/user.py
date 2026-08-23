from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import EmailStr, Field


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


class User(Document):
    uuid: Annotated[UUID, Field(default_factory=uuid4), Indexed(unique=True)]
    name: str
    email: Annotated[EmailStr, Indexed(unique=True)]
    avatar_url: str | None = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=get_datetime_utc)

    class Settings:
        name = "users"
