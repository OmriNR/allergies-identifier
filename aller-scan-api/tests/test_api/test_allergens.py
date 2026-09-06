"""/api/v1/allergens/check endpoint: detect-or-reuse allergen profiles and
cross-check them against a user's allergy preferences."""

from ..factories import (
    allergen_check_payload,
    allergy_preference_create_payload,
    user_payload,
)


async def _create_user_uuid(client) -> str:
    response = await client.post("/api/v1/users/", json=user_payload())
    assert response.status_code == 201, response.text
    return response.json()["uuid"]


class TestCheckAllergens:
    async def test_detects_allergens_from_ingredients(self, client):
        response = await client.post(
            "/api/v1/allergens/check", json=allergen_check_payload()
        )
        assert response.status_code == 200, response.text

        body = response.json()
        assert body["from_cache"] is False
        detected = {a["allergen"]: a for a in body["profile"]["detected_allergens"]}
        assert set(detected) == {"milk", "wheat_gluten", "soy"}
        assert detected["milk"]["triggered_by"] == ["Whey"]

    async def test_second_check_reuses_saved_profile_without_reanalyzing(self, client):
        first = await client.post(
            "/api/v1/allergens/check", json=allergen_check_payload()
        )
        assert first.json()["from_cache"] is False

        second = await client.post(
            "/api/v1/allergens/check",
            json=allergen_check_payload(ingredients=["Water", "Sugar"]),
        )
        assert second.status_code == 200, second.text
        body = second.json()

        assert body["from_cache"] is True
        detected = {a["allergen"] for a in body["profile"]["detected_allergens"]}
        assert detected == {"milk", "wheat_gluten", "soy"}
        assert body["profile"]["id"] == first.json()["profile"]["id"]

    async def test_warns_when_user_allergy_matches_detected_allergen(self, client):
        user_id = await _create_user_uuid(client)
        await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(user_id, allergies=["milk"]),
        )

        response = await client.post(
            "/api/v1/allergens/check",
            json=allergen_check_payload(user_id=user_id),
        )
        assert response.status_code == 200, response.text
        body = response.json()

        assert body["warning"] is True
        assert body["matched_user_allergens"] == ["Milk / dairy"]

    async def test_no_warning_when_user_has_no_matching_allergy(self, client):
        user_id = await _create_user_uuid(client)
        await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(user_id, allergies=["shellfish"]),
        )

        response = await client.post(
            "/api/v1/allergens/check",
            json=allergen_check_payload(barcode="999", user_id=user_id),
        )
        assert response.status_code == 200, response.text
        body = response.json()

        assert body["warning"] is False
        assert body["matched_user_allergens"] == []
