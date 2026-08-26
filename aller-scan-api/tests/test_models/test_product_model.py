"""Field-validation and persistence edge cases for app.models.product.Product."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.models import Product, ProductSource


def _valid_kwargs(**overrides):
    kwargs = {
        "barcode": "0123456789012",
        "product_name": "Peanut Butter",
    }
    kwargs.update(overrides)
    return kwargs


def test_valid_product_has_expected_defaults():
    product = Product(**_valid_kwargs())

    assert product.barcode == "0123456789012"
    assert product.brand is None
    assert product.allergens == []
    assert product.source == ProductSource.MANUAL
    assert isinstance(product.created_at, datetime)
    assert product.created_at.tzinfo is not None


@pytest.mark.parametrize("missing_field", ["barcode", "product_name"])
def test_required_field_missing_raises(missing_field):
    kwargs = _valid_kwargs()
    kwargs.pop(missing_field)

    with pytest.raises(ValidationError):
        Product(**kwargs)


def test_allergens_defaults_to_empty_list_and_is_not_shared_between_instances():
    first = Product(**_valid_kwargs(barcode="111"))
    second = Product(**_valid_kwargs(barcode="222"))

    first.allergens.append("peanuts")

    assert first.allergens == ["peanuts"]
    assert second.allergens == []


def test_source_accepts_external_value():
    product = Product(**_valid_kwargs(source="external"))
    assert product.source == ProductSource.EXTERNAL


def test_source_rejects_invalid_value():
    with pytest.raises(ValidationError):
        Product(**_valid_kwargs(source="unknown-source"))


def test_two_products_get_different_ids():
    first = Product(**_valid_kwargs(barcode="111"))
    second = Product(**_valid_kwargs(barcode="222"))

    assert first.id != second.id


async def test_duplicate_barcode_rejected_on_insert(mongo_db):
    await Product(**_valid_kwargs(barcode="999")).insert()

    with pytest.raises(Exception):
        await Product(**_valid_kwargs(barcode="999", product_name="Other")).insert()


async def test_can_fetch_product_by_barcode(mongo_db):
    await Product(**_valid_kwargs(barcode="555", product_name="Almond Milk")).insert()

    found = await Product.find_one({"barcode": "555"})
    assert found is not None
    assert found.product_name == "Almond Milk"


async def test_find_by_unknown_barcode_returns_none(mongo_db):
    found = await Product.find_one({"barcode": "does-not-exist"})
    assert found is None


def test_allergens_list_preserves_order_and_duplicates_at_model_level():
    """The model itself does not dedupe/normalize allergens; any such
    business rule belongs in the API layer, not the raw Document."""
    product = Product(**_valid_kwargs(allergens=["peanuts", "peanuts", "milk"]))
    assert product.allergens == ["peanuts", "peanuts", "milk"]
