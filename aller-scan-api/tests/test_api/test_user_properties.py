import pytest

from ..factories import allergy_preference_payload, scan_history_payload, user_payload


class TestGetAllergyPreferences:
    async def test_requires_authentication(self, client):
        response = await client.get("/api/v1/user-properties/allergies")
        assert response.status_code == 401

    async def test_defaults_to_empty_list_for_new_user(self, client, auth_headers):
        response = await client.get(
            "/api/v1/user-properties/allergies", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["allergies"] == []


class TestUpdateAllergyPreferences:
    async def test_requires_authentication(self, client):
        response = await client.put(
            "/api/v1/user-properties/allergies", json=allergy_preference_payload()
        )
        assert response.status_code == 401

    async def test_sets_allergy_list(self, client, auth_headers):
        response = await client.put(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_payload(),
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["allergies"] == ["peanuts", "shellfish"]

    async def test_get_reflects_previous_update(self, client, auth_headers):
        await client.put(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_payload(),
            headers=auth_headers,
        )

        response = await client.get(
            "/api/v1/user-properties/allergies", headers=auth_headers
        )
        assert response.json()["allergies"] == ["peanuts", "shellfish"]

    async def test_update_replaces_not_merges(self, client, auth_headers):
        await client.put(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_payload(allergies=["peanuts"]),
            headers=auth_headers,
        )
        response = await client.put(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_payload(allergies=["milk"]),
            headers=auth_headers,
        )

        assert response.json()["allergies"] == ["milk"]

    async def test_empty_list_clears_preferences(self, client, auth_headers):
        await client.put(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_payload(allergies=["peanuts"]),
            headers=auth_headers,
        )
        response = await client.put(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_payload(allergies=[]),
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["allergies"] == []

    async def test_non_list_allergies_returns_422(self, client, auth_headers):
        response = await client.put(
            "/api/v1/user-properties/allergies",
            json={"allergies": "peanuts"},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_preferences_isolated_per_user(self, client):
        await client.post("/api/v1/users/", json=user_payload())
        await client.post(
            "/api/v1/users/",
            json=user_payload(email="second@example.com", name="Second User"),
        )

        from ..factories import login_payload

        login_a = await client.post(
            "/api/v1/login/access-token", data=login_payload(user_payload())
        )
        login_b = await client.post(
            "/api/v1/login/access-token",
            data=login_payload(user_payload(email="second@example.com")),
        )
        headers_a = {
            "Authorization": f"Bearer {login_a.json()['access_token']}"
        }
        headers_b = {
            "Authorization": f"Bearer {login_b.json()['access_token']}"
        }

        await client.put(
            "/api/v1/user-properties/allergies",
            json=allergy_preference_payload(allergies=["peanuts"]),
            headers=headers_a,
        )

        response_b = await client.get(
            "/api/v1/user-properties/allergies", headers=headers_b
        )
        assert response_b.json()["allergies"] == []


class TestCreateScanHistory:
    async def test_requires_authentication(self, client):
        response = await client.post(
            "/api/v1/user-properties/scan-history", json=scan_history_payload()
        )
        assert response.status_code == 401

    async def test_creates_scan_record(self, client, auth_headers):
        response = await client.post(
            "/api/v1/user-properties/scan-history",
            json=scan_history_payload(),
            headers=auth_headers,
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["barcode"] == "0123456789012"
        assert body["status"] == "dangerous"
        assert body["detected_allergens"] == ["peanuts"]

    async def test_invalid_status_returns_422(self, client, auth_headers):
        response = await client.post(
            "/api/v1/user-properties/scan-history",
            json=scan_history_payload(status="unknown"),
            headers=auth_headers,
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("missing_field", ["barcode", "product_name", "status"])
    async def test_missing_required_field_returns_422(
        self, client, auth_headers, missing_field
    ):
        payload = scan_history_payload()
        payload.pop(missing_field)

        response = await client.post(
            "/api/v1/user-properties/scan-history",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_detected_allergens_default_to_empty_list(self, client, auth_headers):
        payload = scan_history_payload(status="safe")
        payload.pop("detected_allergens")

        response = await client.post(
            "/api/v1/user-properties/scan-history",
            json=payload,
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["detected_allergens"] == []


class TestListScanHistory:
    async def test_requires_authentication(self, client):
        response = await client.get("/api/v1/user-properties/scan-history")
        assert response.status_code == 401

    async def test_empty_when_no_scans(self, client, auth_headers):
        response = await client.get(
            "/api/v1/user-properties/scan-history", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_lists_only_own_scans(self, client):
        await client.post("/api/v1/users/", json=user_payload())
        await client.post(
            "/api/v1/users/",
            json=user_payload(email="second@example.com", name="Second User"),
        )

        from ..factories import login_payload

        login_a = await client.post(
            "/api/v1/login/access-token", data=login_payload(user_payload())
        )
        login_b = await client.post(
            "/api/v1/login/access-token",
            data=login_payload(user_payload(email="second@example.com")),
        )
        headers_a = {
            "Authorization": f"Bearer {login_a.json()['access_token']}"
        }
        headers_b = {
            "Authorization": f"Bearer {login_b.json()['access_token']}"
        }

        await client.post(
            "/api/v1/user-properties/scan-history",
            json=scan_history_payload(),
            headers=headers_a,
        )

        response_b = await client.get(
            "/api/v1/user-properties/scan-history", headers=headers_b
        )
        assert response_b.json() == []


class TestGetScanHistoryById:
    async def test_unknown_id_returns_404(self, client, auth_headers):
        import uuid

        response = await client.get(
            f"/api/v1/user-properties/scan-history/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_returns_own_scan(self, client, auth_headers):
        create_response = await client.post(
            "/api/v1/user-properties/scan-history",
            json=scan_history_payload(),
            headers=auth_headers,
        )
        scan_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/user-properties/scan-history/{scan_id}", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["id"] == scan_id

    async def test_cannot_access_other_users_scan(self, client):
        await client.post("/api/v1/users/", json=user_payload())
        await client.post(
            "/api/v1/users/",
            json=user_payload(email="second@example.com", name="Second User"),
        )

        from ..factories import login_payload

        login_a = await client.post(
            "/api/v1/login/access-token", data=login_payload(user_payload())
        )
        login_b = await client.post(
            "/api/v1/login/access-token",
            data=login_payload(user_payload(email="second@example.com")),
        )
        headers_a = {
            "Authorization": f"Bearer {login_a.json()['access_token']}"
        }
        headers_b = {
            "Authorization": f"Bearer {login_b.json()['access_token']}"
        }

        create_response = await client.post(
            "/api/v1/user-properties/scan-history",
            json=scan_history_payload(),
            headers=headers_a,
        )
        scan_id = create_response.json()["id"]

        response = await client.get(
            f"/api/v1/user-properties/scan-history/{scan_id}", headers=headers_b
        )
        assert response.status_code in (403, 404)
