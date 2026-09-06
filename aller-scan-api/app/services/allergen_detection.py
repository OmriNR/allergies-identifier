"""Ingredient -> allergen matching, plus the profile cache and user
cross-check that sit on top of it. Shared by the /allergens/check endpoint
and the product-scan flow so both compute allergen warnings the same way.
"""

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from uuid import UUID

REFERENCE_PATH = Path(__file__).resolve().parent.parent / "data" / "allergen_reference.json"

DETECTION_SOURCE = "allergen_reference_v1"


@dataclass
class AllergenMatch:
    allergen: str
    display_name: str
    triggered_by: list[str] = field(default_factory=list)


@lru_cache(maxsize=1)
def _reference() -> dict:
    return json.loads(REFERENCE_PATH.read_text(encoding="utf-8"))


def detect_allergens(terms: list[str]) -> list[AllergenMatch]:
    """Match a list of free-text terms (ingredients, allergy tags, ...)
    against the allergen reference table via substring containment on the
    normalized text.

    ponytail: naive substring matching, no tokenization/stemming. Fine for
    the curated synonym lists here; upgrade to token-based matching if
    short synonyms (e.g. "milk") start producing false positives.
    """
    matches: dict[str, AllergenMatch] = {}

    for term in terms:
        normalized = term.strip().lower()
        if not normalized:
            continue

        for allergen_key, info in _reference().items():
            if not any(synonym in normalized for synonym in info["synonyms"]):
                continue

            match = matches.setdefault(
                allergen_key,
                AllergenMatch(allergen=allergen_key, display_name=info["display_name"]),
            )
            match.triggered_by.append(term)

    return list(matches.values())


async def get_or_create_profile(barcode: str, terms: list[str]):
    """Return the cached allergen profile for a barcode, detecting and
    saving one from `terms` (e.g. product ingredients/allergen tags) if
    none exists yet."""
    from ..models.allergen_profile import AllergenProfile, DetectedAllergen

    profile = await AllergenProfile.find_one({"barcode": barcode})
    if profile is not None:
        return profile

    matches = detect_allergens(terms)
    profile = AllergenProfile(
        barcode=barcode,
        detected_allergens=[
            DetectedAllergen(
                allergen=match.allergen,
                display_name=match.display_name,
                triggered_by=match.triggered_by,
            )
            for match in matches
        ],
        detection_source=DETECTION_SOURCE,
    )
    await profile.create()
    return profile


async def matched_user_allergens(profile, user_id: UUID | None) -> list[str]:
    """Display names of the profile's detected allergens that also appear
    in the given user's allergy preferences. Empty if no user or no
    preference is set."""
    from ..models.user_properties import AllergyPreference

    if user_id is None:
        return []

    preference = await AllergyPreference.find_one({"user_id": user_id})
    if preference is None:
        return []

    user_allergen_keys = {match.allergen for match in detect_allergens(preference.allergies)}
    return [
        detected.display_name
        for detected in profile.detected_allergens
        if detected.allergen in user_allergen_keys
    ]
