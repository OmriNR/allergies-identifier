"""/api/v1/user-properties/* endpoints.

Actual contract (path-param based, no auth — matches the implementation in
app/routes/userProperties.py, which intentionally diverges from the
auth-based contract sketched in tests/README.md):

- GET  /user-properties/allergies/{userid}   404 until a preference exists.
- POST /user-properties/allergies            Body: {user_id, allergies}.
  404 if the user doesn't exist. 400 if a preference already exists (use PUT).
- PUT  /user-properties/allergies/{userid}    Body: {userid, allergies}.
  Replaces (not merges) the list. 404 if no preference exists yet.
- GET  /user-properties/scan-history/users/{userid}     404 if user unknown.
- POST /user-properties/scan-history          Body matches ScanHistoryCreate
  (user_id, product_id, barcode, product_name, brand?, status,
  detected_allergens?). 404 if the user or the product doesn't exist.
- GET  /user-properties/scan-history/products/{product_id}   404 if product
  unknown. Supports `limit` (default 20, 1-100).
"""

import uuid

import pytest

from app.models import Product

from ..factories import (
    allergy_preference_create_payload,
    allergy_preference_update_payload,
    product_payload,
    scan_history_payload,
    user_payload,
)


async def _register_user(client, **overrides):
    response = await client.post("/api/v1/users/", json=user_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()["uuid"]


async def _create_product(**overrides) -> Product:
    product = Product(**product_payload(**overrides))
    await product.insert()
    return product


class TestGetAllergyPreferences:
    async def test_unknown_user_returns_404(self, client):
        response = await client.get(f"/api/v1/user-properties/allergies/{uuid.uuid4()}")
        assert response.status_code == 404

    async def test_no_preference_yet_returns_404(self, client):
        userid = await _register_user(client)

        response = await client.get(f"/api/v1/user-properties/allergies/{userid}")
        assert response.status_code == 404

    async def test_returns_created_preference(self, client):
        userid = await _register_user(client)
        await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(userid),
        )

        response = await client.get(f"/api/v1/user-properties/allergies/{userid}")
        assert response.status_code == 200
        assert response.json()["allergies"] == ["peanuts", "shellfish"]


class TestCreateAllergyPreferences:
    async def test_unknown_user_returns_404(self, client):
        response = await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(uuid.uuid4()),
        )
        assert response.status_code == 404

    async def test_creates_preference(self, client):
        userid = await _register_user(client)

        response = await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(userid, allergies=["milk"]),
        )
        assert response.status_code == 201, response.text
        assert response.json()["allergies"] == ["milk"]

    async def test_duplicate_create_returns_400(self, client):
        userid = await _register_user(client)
        await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(userid),
        )

        response = await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(userid),
        )
        assert response.status_code == 400

    async def test_non_list_allergies_returns_422(self, client):
        userid = await _register_user(client)

        response = await client.post(
            "/api/v1/user-properties/allergies",
            json={"user_id": str(userid), "allergies": "peanuts"},
        )
        assert response.status_code == 422


class TestUpdateAllergyPreferences:
    async def test_no_existing_preference_returns_404(self, client):
        userid = await _register_user(client)

        response = await client.put(
            f"/api/v1/user-properties/allergies/{userid}",
            json=allergy_preference_update_payload(userid),
        )
        assert response.status_code == 404

    async def test_replaces_not_merges(self, client):
        userid = await _register_user(client)
        await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(userid, allergies=["peanuts"]),
        )

        response = await client.put(
            f"/api/v1/user-properties/allergies/{userid}",
            json=allergy_preference_update_payload(userid, allergies=["milk"]),
        )
        assert response.status_code == 200
        assert response.json()["allergies"] == ["milk"]

    async def test_get_reflects_previous_update(self, client):
        userid = await _register_user(client)
        await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(userid, allergies=["peanuts"]),
        )
        await client.put(
            f"/api/v1/user-properties/allergies/{userid}",
            json=allergy_preference_update_payload(userid, allergies=["milk"]),
        )

        response = await client.get(f"/api/v1/user-properties/allergies/{userid}")
        assert response.json()["allergies"] == ["milk"]

    async def test_empty_list_clears_preferences(self, client):
        userid = await _register_user(client)
        await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(userid, allergies=["peanuts"]),
        )

        response = await client.put(
            f"/api/v1/user-properties/allergies/{userid}",
            json=allergy_preference_update_payload(userid, allergies=[]),
        )
        assert response.status_code == 200
        assert response.json()["allergies"] == []

    async def test_non_list_allergies_returns_422(self, client):
        userid = await _register_user(client)
        await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(userid),
        )

        response = await client.put(
            f"/api/v1/user-properties/allergies/{userid}",
            json={"userid": str(userid), "allergies": "peanuts"},
        )
        assert response.status_code == 422

    async def test_preferences_isolated_per_user(self, client):
        userid_a = await _register_user(client)
        userid_b = await _register_user(client, email="second@example.com", name="Second User")

        await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(userid_a, allergies=["peanuts"]),
        )
        await client.post(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_create_payload(userid_b, allergies=["milk"]),
        )

        await client.put(
            f"/api/v1/user-properties/allergies/{userid_a}",
            json=allergy_preference_update_payload(userid_a, allergies=["shellfish"]),
        )

        response_b = await client.get(f"/api/v1/user-properties/allergies/{userid_b}")
        assert response_b.json()["allergies"] == ["milk"]


class TestCreateScanHistory:
    async def test_unknown_user_returns_404(self, client):
        product = await _create_product()

        response = await client.post(
            "/api/v1/user-properties/scan-history",
            json=scan_history_payload(uuid.uuid4(), product.id),
        )
        assert response.status_code == 404

    async def test_unknown_product_returns_404(self, client):
        userid = await _register_user(client)

        response = await client.post(
            "/api/v1/user-properties/scan-history",
            json=scan_history_payload(userid, uuid.uuid4()),
        )
        assert response.status_code == 404

    async def test_creates_scan_record(self, client):
        userid = await _register_user(client)
        product = await _create_product()

        response = await client.post(
            "/api/v1/user-properties/scan-history",
            json=scan_history_payload(userid, product.id),
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["barcode"] == "0123456789012"
        assert body["status"] == "dangerous"
        assert body["detected_allergens"] == ["peanuts"]
        assert body["user_id"] == str(userid)
        assert body["product_id"] == str(product.id)

    async def test_invalid_status_returns_422(self, client):
        userid = await _register_user(client)
        product = await _create_product()

        response = await client.post(
            "/api/v1/user-properties/scan-history",
            json=scan_history_payload(userid, product.id, status="unknown"),
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("missing_field", ["barcode", "product_name", "status"])
    async def test_missing_required_field_returns_422(self, client, missing_field):
        userid = await _register_user(client)
        product = await _create_product()

        payload = scan_history_payload(userid, product.id)
        payload.pop(missing_field)

        response = await client.post(
            "/api/v1/user-properties/scan-history", json=payload
        )
        assert response.status_code == 422

    async def test_detected_allergens_default_to_empty_list(self, client):
        userid = await _register_user(client)
        product = await _create_product()

        payload = scan_history_payload(userid, product.id, status="safe")
        payload.pop("detected_allergens")

        response = await client.post(
            "/api/v1/user-properties/scan-history", json=payload
        )
        assert response.status_code == 201
        assert response.json()["detected_allergens"] == []


class TestListScanHistoryByUser:
    async def test_unknown_user_returns_404(self, client):
        response = await client.get(
            f"/api/v1/user-properties/scan-history/users/{uuid.uuid4()}"
        )
        assert response.status_code == 404

    async def test_empty_when_no_scans(self, client):
        userid = await _register_user(client)

        response = await client.get(
            f"/api/v1/user-properties/scan-history/users/{userid}"
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_lists_only_own_scans(self, client):
        userid_a = await _register_user(client)
        userid_b = await _register_user(client, email="second@example.com", name="Second User")
        product = await _create_product()

        await client.post(
            "/api/v1/user-properties/scan-history",
            json=scan_history_payload(userid_a, product.id),
        )

        response_b = await client.get(
            f"/api/v1/user-properties/scan-history/users/{userid_b}"
        )
        assert response_b.json() == []

        response_a = await client.get(
            f"/api/v1/user-properties/scan-history/users/{userid_a}"
        )
        assert len(response_a.json()) == 1


class TestListScanHistoryByProduct:
    async def test_unknown_product_returns_404(self, client):
        response = await client.get(
            f"/api/v1/user-properties/scan-history/products/{uuid.uuid4()}"
        )
        assert response.status_code == 404

    async def test_empty_when_no_scans(self, client):
        product = await _create_product()

        response = await client.get(
            f"/api/v1/user-properties/scan-history/products/{product.id}"
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_lists_only_scans_for_that_product(self, client):
        userid = await _register_user(client)
        product_a = await _create_product(barcode="111")
        product_b = await _create_product(barcode="222")

        await client.post(
            "/api/v1/user-properties/scan-history",
            json=scan_history_payload(userid, product_a.id),
        )

        response_b = await client.get(
            f"/api/v1/user-properties/scan-history/products/{product_b.id}"
        )
        assert response_b.json() == []

        response_a = await client.get(
            f"/api/v1/user-properties/scan-history/products/{product_a.id}"
        )
        assert len(response_a.json()) == 1

    async def test_limit_restricts_result_count(self, client):
        userid = await _register_user(client)
        product = await _create_product()

        for _ in range(3):
            await client.post(
                "/api/v1/user-properties/scan-history",
                json=scan_history_payload(userid, product.id),
            )

        response = await client.get(
            f"/api/v1/user-properties/scan-history/products/{product.id}",
            params={"limit": 2},
        )
        assert response.status_code == 200
        assert len(response.json()) == 2

    @pytest.mark.parametrize("limit", [0, -1, 101])
    async def test_out_of_range_limit_returns_422(self, client, limit):
        product = await _create_product()

        response = await client.get(
            f"/api/v1/user-properties/scan-history/products/{product.id}",
            params={"limit": limit},
        )
        assert response.status_code == 422
