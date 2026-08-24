"""Field-validation and persistence edge cases for ScanHistory and
AllergyPreference (app.models.user_properties)."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models import AllergyPreference, ScanHistory, ScanStatus


def _valid_scan_kwargs(**overrides):
    kwargs = {
        "user_id": uuid4(),
        "product_id": uuid4(),
        "barcode": "0123456789012",
        "product_name": "Peanut Butter",
        "status": ScanStatus.DANGEROUS,
    }
    kwargs.update(overrides)
    return kwargs


def test_valid_scan_history_has_expected_defaults():
    scan = ScanHistory(**_valid_scan_kwargs())

    assert scan.brand is None
    assert scan.detected_allergens == []
    assert isinstance(scan.created_at, datetime)
    assert scan.created_at.tzinfo is not None


@pytest.mark.parametrize(
    "missing_field",
    ["user_id", "product_id", "barcode", "product_name", "status"],
)
def test_scan_history_required_field_missing_raises(missing_field):
    kwargs = _valid_scan_kwargs()
    kwargs.pop(missing_field)

    with pytest.raises(ValidationError):
        ScanHistory(**kwargs)


def test_scan_history_accepts_safe_status():
    scan = ScanHistory(**_valid_scan_kwargs(status="safe"))
    assert scan.status == ScanStatus.SAFE


def test_scan_history_rejects_invalid_status():
    with pytest.raises(ValidationError):
        ScanHistory(**_valid_scan_kwargs(status="maybe"))


def test_scan_history_rejects_non_uuid_user_id():
    with pytest.raises(ValidationError):
        ScanHistory(**_valid_scan_kwargs(user_id="not-a-uuid"))


async def test_multiple_scans_allowed_for_same_barcode(mongo_db):
    user_id = uuid4()
    await ScanHistory(**_valid_scan_kwargs(user_id=user_id, barcode="111")).insert()
    await ScanHistory(**_valid_scan_kwargs(user_id=user_id, barcode="111")).insert()

    count = await ScanHistory.find({"user_id": user_id, "barcode": "111"}).count()
    assert count == 2


async def test_scan_history_query_isolated_per_user(mongo_db):
    user_a = uuid4()
    user_b = uuid4()
    await ScanHistory(**_valid_scan_kwargs(user_id=user_a)).insert()
    await ScanHistory(**_valid_scan_kwargs(user_id=user_b)).insert()

    results = await ScanHistory.find({"user_id": user_a}).to_list()
    assert len(results) == 1
    assert results[0].user_id == user_a


def _valid_allergy_kwargs(**overrides):
    kwargs = {"user_id": uuid4()}
    kwargs.update(overrides)
    return kwargs


def test_allergy_preference_defaults_to_empty_allergy_list():
    preference = AllergyPreference(**_valid_allergy_kwargs())

    assert preference.allergies == []
    assert isinstance(preference.updated_at, datetime)


def test_allergy_preference_requires_user_id():
    with pytest.raises(ValidationError):
        AllergyPreference()


def test_allergy_preference_accepts_allergy_list():
    preference = AllergyPreference(
        **_valid_allergy_kwargs(allergies=["peanuts", "shellfish"])
    )
    assert preference.allergies == ["peanuts", "shellfish"]


async def test_duplicate_user_id_rejected_on_insert(mongo_db):
    user_id = uuid4()
    await AllergyPreference(**_valid_allergy_kwargs(user_id=user_id)).insert()

    with pytest.raises(Exception):
        await AllergyPreference(**_valid_allergy_kwargs(user_id=user_id)).insert()


async def test_can_fetch_allergy_preference_by_user_id(mongo_db):
    user_id = uuid4()
    await AllergyPreference(
        **_valid_allergy_kwargs(user_id=user_id, allergies=["milk"])
    ).insert()

    found = await AllergyPreference.find_one({"user_id": user_id})
    assert found is not None
    assert found.allergies == ["milk"]
