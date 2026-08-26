"""/api/v1/products/ endpoints.

Assumed contract (see tests/README.md):
- POST /api/v1/products/  creates a product manually. Requires auth.
- GET  /api/v1/products/{barcode}  looks a single product up by barcode.
  Public (no auth required) since barcode lookups are the core scan flow.
- GET  /api/v1/products/  lists/searches products, supports `q` (name
  substring, case-insensitive) and pagination via `limit`/`skip`.
"""

import pytest

from ..factories import product_payload


class TestCreateProduct:
    async def test_requires_authentication(self, client):
        response = await client.post("/api/v1/products/", json=product_payload())
        assert response.status_code == 401

    async def test_creates_product_with_manual_source(self, client, auth_headers):
        response = await client.post(
            "/api/v1/products/", json=product_payload(), headers=auth_headers
        )

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["barcode"] == "0123456789012"
        assert body["product_name"] == "Peanut Butter"
        assert body["source"] == "manual"

    async def test_allergens_default_to_empty_list(self, client, auth_headers):
        payload = product_payload()
        payload.pop("allergens")

        response = await client.post(
            "/api/v1/products/", json=payload, headers=auth_headers
        )
        assert response.status_code == 201
        assert response.json()["allergens"] == []

    @pytest.mark.parametrize("missing_field", ["barcode", "product_name"])
    async def test_missing_required_field_returns_422(
        self, client, auth_headers, missing_field
    ):
        payload = product_payload()
        payload.pop(missing_field)

        response = await client.post(
            "/api/v1/products/", json=payload, headers=auth_headers
        )
        assert response.status_code == 422

    async def test_duplicate_barcode_returns_409(self, client, auth_headers):
        await client.post(
            "/api/v1/products/", json=product_payload(), headers=auth_headers
        )

        response = await client.post(
            "/api/v1/products/",
            json=product_payload(product_name="Different Name"),
            headers=auth_headers,
        )
        assert response.status_code == 409


class TestGetProductByBarcode:
    async def test_existing_barcode_returns_product(self, client, auth_headers):
        await client.post(
            "/api/v1/products/", json=product_payload(), headers=auth_headers
        )

        response = await client.get("/api/v1/products/0123456789012")
        assert response.status_code == 200
        assert response.json()["product_name"] == "Peanut Butter"

    async def test_unknown_barcode_returns_404(self, client):
        response = await client.get("/api/v1/products/does-not-exist")
        assert response.status_code == 404


class TestListProducts:
    async def test_empty_list_when_no_products(self, client):
        response = await client.get("/api/v1/products/")
        assert response.status_code == 200
        assert response.json() == []

    async def test_lists_all_created_products(self, client, auth_headers):
        await client.post(
            "/api/v1/products/", json=product_payload(barcode="111"), headers=auth_headers
        )
        await client.post(
            "/api/v1/products/", json=product_payload(barcode="222"), headers=auth_headers
        )

        response = await client.get("/api/v1/products/")
        assert response.status_code == 200
        barcodes = {item["barcode"] for item in response.json()}
        assert barcodes == {"111", "222"}

    async def test_search_by_name_substring_case_insensitive(
        self, client, auth_headers
    ):
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="111", product_name="Peanut Butter"),
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="222", product_name="Almond Milk"),
            headers=auth_headers,
        )

        response = await client.get("/api/v1/products/", params={"q": "peanut"})
        assert response.status_code == 200
        names = [item["product_name"] for item in response.json()]
        assert names == ["Peanut Butter"]

    async def test_negative_limit_returns_422(self, client):
        response = await client.get("/api/v1/products/", params={"limit": -1})
        assert response.status_code == 422


# --- Below: tests for the endpoints as actually implemented today ---
# (distinct from the assumed-contract section above, which describes an
# intended API that these routes don't yet match).


class TestListOfProducts:
    async def test_no_filters_returns_all(self, client, auth_headers):
        await client.post(
            "/api/v1/products/", json=product_payload(barcode="111"), headers=auth_headers
        )
        await client.post(
            "/api/v1/products/", json=product_payload(barcode="222"), headers=auth_headers
        )

        response = await client.post("/api/v1/products/list_of_products", json={})
        assert response.status_code == 200, response.text
        barcodes = {item["barcode"] for item in response.json()}
        assert barcodes == {"111", "222"}

    async def test_filters_by_brand(self, client, auth_headers):
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="111", brand="Acme"),
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="222", brand="Other"),
            headers=auth_headers,
        )

        response = await client.post(
            "/api/v1/products/list_of_products", json={"brand": "Acme"}
        )
        assert response.status_code == 200, response.text
        barcodes = {item["barcode"] for item in response.json()}
        assert barcodes == {"111"}

    async def test_filters_by_name_substring_case_insensitive(
        self, client, auth_headers
    ):
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="111", product_name="Peanut Butter"),
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="222", product_name="Almond Milk"),
            headers=auth_headers,
        )

        response = await client.post(
            "/api/v1/products/list_of_products", json={"product_name": "peanut"}
        )
        assert response.status_code == 200, response.text
        names = [item["product_name"] for item in response.json()]
        assert names == ["Peanut Butter"]

    async def test_filters_by_allergens_matches_at_least_one(
        self, client, auth_headers
    ):
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="111", allergens=["peanuts"]),
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="222", allergens=["gluten", "soy"]),
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="333", allergens=["dairy"]),
            headers=auth_headers,
        )

        response = await client.post(
            "/api/v1/products/list_of_products",
            json={"allergens": ["peanuts", "soy"]},
        )
        assert response.status_code == 200, response.text
        barcodes = {item["barcode"] for item in response.json()}
        assert barcodes == {"111", "222"}

    async def test_combines_brand_name_and_allergens_filters(
        self, client, auth_headers
    ):
        await client.post(
            "/api/v1/products/",
            json=product_payload(
                barcode="111",
                brand="Acme",
                product_name="Peanut Butter",
                allergens=["peanuts"],
            ),
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/products/",
            json=product_payload(
                barcode="222",
                brand="Acme",
                product_name="Peanut Oil",
                allergens=["gluten"],
            ),
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/products/",
            json=product_payload(
                barcode="333",
                brand="Other",
                product_name="Peanut Butter",
                allergens=["peanuts"],
            ),
            headers=auth_headers,
        )

        response = await client.post(
            "/api/v1/products/list_of_products",
            json={
                "brand": "Acme",
                "product_name": "peanut",
                "allergens": ["peanuts"],
            },
        )
        assert response.status_code == 200, response.text
        barcodes = {item["barcode"] for item in response.json()}
        assert barcodes == {"111"}

    async def test_respects_limit_and_offset(self, client, auth_headers):
        for barcode in ["111", "222", "333"]:
            await client.post(
                "/api/v1/products/",
                json=product_payload(barcode=barcode),
                headers=auth_headers,
            )

        response = await client.post(
            "/api/v1/products/list_of_products",
            json={},
            params={"limit": 1, "offset": 1},
        )
        assert response.status_code == 200, response.text
        assert len(response.json()) == 1


class TestGetBrands:
    async def test_empty_list_when_no_products(self, client):
        response = await client.get("/api/v1/products/brands")
        assert response.status_code == 200
        assert response.json() == []

    async def test_returns_unique_sorted_brands_excluding_none(
        self, client, auth_headers
    ):
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="111", brand="Zeta"),
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="222", brand="Acme"),
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="333", brand="Acme"),
            headers=auth_headers,
        )
        await client.post(
            "/api/v1/products/",
            json=product_payload(barcode="444", brand=None),
            headers=auth_headers,
        )

        response = await client.get("/api/v1/products/brands")
        assert response.status_code == 200
        assert response.json() == ["Acme", "Zeta"]
