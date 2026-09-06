from app.services.allergen_detection import detect_allergens


def test_detects_allergens_from_synonyms():
    matches = detect_allergens(["Whey", "Flour", "Soybeans"])
    by_key = {match.allergen: match for match in matches}

    assert set(by_key) == {"milk", "wheat_gluten", "soy"}
    assert by_key["milk"].display_name == "Milk / dairy"
    assert by_key["milk"].triggered_by == ["Whey"]
    assert by_key["wheat_gluten"].display_name == "Gluten / wheat"
    assert by_key["soy"].display_name == "Soy"


def test_ignores_unrelated_ingredients():
    matches = detect_allergens(["Water", "Sugar", "Salt"])
    assert matches == []


def test_collects_all_triggering_ingredients_per_allergen():
    matches = detect_allergens(["Whey", "Casein", "Milk powder"])
    assert len(matches) == 1
    assert matches[0].allergen == "milk"
    assert matches[0].triggered_by == ["Whey", "Casein", "Milk powder"]


def test_matches_synonym_embedded_in_a_longer_ingredient_phrase():
    matches = detect_allergens(["Enriched wheat flour"])
    assert [match.allergen for match in matches] == ["wheat_gluten"]


def test_empty_and_blank_terms_are_ignored():
    assert detect_allergens(["", "   "]) == []
