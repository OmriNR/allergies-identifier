"""Field-validation and persistence edge cases for app.models.user.User.

NOTE: `password` is not yet a field on User, but app/auth/auth.py already
reads `user.password`. These tests assume a required, write-only `password`
field will be added (see tests/README.md).
"""

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.models import User


def _valid_kwargs(**overrides):
    kwargs = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "password": "StrongPassw0rd!",
    }
    kwargs.update(overrides)
    return kwargs


def test_valid_user_has_expected_defaults():
    user = User(**_valid_kwargs())

    assert user.name == "Jane Doe"
    assert user.email == "jane.doe@example.com"
    assert user.avatar_url is None
    assert user.is_active is True
    assert isinstance(user.uuid, UUID)
    assert isinstance(user.created_at, datetime)
    assert user.created_at.tzinfo is not None


def test_two_users_get_different_uuids():
    first = User(**_valid_kwargs())
    second = User(**_valid_kwargs())

    assert first.uuid != second.uuid


@pytest.mark.parametrize("missing_field", ["name", "email", "password"])
def test_required_field_missing_raises(missing_field):
    kwargs = _valid_kwargs()
    kwargs.pop(missing_field)

    with pytest.raises(ValidationError):
        User(**kwargs)


@pytest.mark.parametrize(
    "invalid_email",
    ["not-an-email", "missing-domain@", "@missing-local.com", "spaces in@email.com", ""],
)
def test_invalid_email_format_raises(invalid_email):
    with pytest.raises(ValidationError):
        User(**_valid_kwargs(email=invalid_email))


def test_avatar_url_is_optional_and_can_be_set():
    user = User(**_valid_kwargs(avatar_url="https://example.com/avatar.png"))
    assert user.avatar_url == "https://example.com/avatar.png"


def test_is_active_can_be_overridden_to_false():
    user = User(**_valid_kwargs(is_active=False))
    assert user.is_active is False


def test_created_at_defaults_close_to_now():
    before = datetime.now(UTC)
    user = User(**_valid_kwargs())
    after = datetime.now(UTC)

    assert before <= user.created_at <= after


async def test_duplicate_email_rejected_on_insert(mongo_db):
    await User(**_valid_kwargs(email="dup@example.com")).insert()

    with pytest.raises(Exception):
        await User(**_valid_kwargs(email="dup@example.com")).insert()


async def test_email_uniqueness_is_case_sensitive_or_not_documented(mongo_db):
    """Documents current expected behavior: differently-cased emails are
    distinct values unless the API/model normalizes email casing itself."""
    await User(**_valid_kwargs(email="dup@example.com")).insert()

    same_but_different_case = User(**_valid_kwargs(email="Dup@Example.com"))
    await same_but_different_case.insert()

    count = await User.find_all().count()
    assert count == 2


async def test_duplicate_uuid_rejected_on_insert(mongo_db):
    from uuid import uuid4

    shared_uuid = uuid4()
    await User(**_valid_kwargs(email="a@example.com"), uuid=shared_uuid).insert()

    with pytest.raises(Exception):
        await User(**_valid_kwargs(email="b@example.com"), uuid=shared_uuid).insert()


async def test_can_fetch_user_by_email(mongo_db):
    await User(**_valid_kwargs(email="findme@example.com")).insert()

    found = await User.find_one({"email": "findme@example.com"})
    assert found is not None
    assert found.name == "Jane Doe"


async def test_find_by_unknown_email_returns_none(mongo_db):
    found = await User.find_one({"email": "nobody@example.com"})
    assert found is None
