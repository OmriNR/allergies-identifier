"""Ingredient -> allergen matching.

Kept independent of the DB models and routes: the reference table
(app/data/allergen_reference.json) can be edited or extended without
touching this logic, and this logic can be reused for any string list
(product ingredients, a user's free-text allergy tags, ...).
"""

import json
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

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
