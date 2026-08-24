"""Payload builders for the assumed API contract (see tests/README.md)."""

from typing import Any


def user_payload(**overrides: Any) -> dict:
    payload = {
        "name": "Jane Doe",
        "email": "jane.doe@example.com",
        "password": "StrongPassw0rd!",
    }
    payload.update(overrides)
    return payload


def login_payload(user: dict, **overrides: Any) -> dict:
    payload = {
        "username": user["email"],
        "password": user["password"],
    }
    payload.update(overrides)
    return payload


def product_payload(**overrides: Any) -> dict:
    payload = {
        "barcode": "0123456789012",
        "product_name": "Peanut Butter",
        "brand": "Acme",
        "allergens": ["peanuts"],
    }
    payload.update(overrides)
    return payload


def allergy_preference_payload(**overrides: Any) -> dict:
    payload = {
        "allergies": ["peanuts", "shellfish"],
    }
    payload.update(overrides)
    return payload


def scan_history_payload(**overrides: Any) -> dict:
    payload = {
        "barcode": "0123456789012",
        "product_name": "Peanut Butter",
        "brand": "Acme",
        "status": "dangerous",
        "detected_allergens": ["peanuts"],
    }
    payload.update(overrides)
    return payload
