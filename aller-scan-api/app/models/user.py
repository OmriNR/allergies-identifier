from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from beanie import Document, Indexed
from pydantic import EmailStr, Field


def get_datetime_utc() -> datetime:
    return datetime.now(UTC)


class User(Document):
    id: UUID = Field(default_factory=uuid4)
    name: str
    email: Annotated[EmailStr, Indexed(unique=True)]
    avatar_url: str | None = None
    created_at: datetime = Field(default_factory=get_datetime_utc)

    class Settings:
        name = "users"
