"""GET/PATCH /api/v1/users/me.

Assumed contract (see tests/README.md): reading and partially updating the
authenticated user's own profile. `email` is not editable through this
endpoint.
"""


class TestGetMe:
    async def test_requires_authentication(self, client):
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_rejects_garbage_token(self, client):
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": "Bearer not-a-real-token"}
        )
        assert response.status_code == 401

    async def test_rejects_malformed_auth_header(self, client, auth_headers):
        token = auth_headers["Authorization"].removeprefix("Bearer ")
        response = await client.get(
            "/api/v1/users/me", headers={"Authorization": token}
        )
        assert response.status_code == 401

    async def test_returns_current_user_profile(
        self, client, auth_headers, registered_user
    ):
        response = await client.get("/api/v1/users/me", headers=auth_headers)

        assert response.status_code == 200
        body = response.json()
        assert body["email"] == registered_user["email"]
        assert body["name"] == registered_user["name"]
        assert "password" not in body


class TestUpdateMe:
    async def test_requires_authentication(self, client):
        response = await client.patch("/api/v1/users/me", json={"name": "New Name"})
        assert response.status_code == 401

    async def test_updates_name(self, client, auth_headers):
        response = await client.patch(
            "/api/v1/users/me", json={"name": "New Name"}, headers=auth_headers
        )

        assert response.status_code == 200
        assert response.json()["name"] == "New Name"

    async def test_partial_update_leaves_other_fields_untouched(
        self, client, auth_headers, registered_user
    ):
        response = await client.patch(
            "/api/v1/users/me",
            json={"avatar_url": "https://example.com/a.png"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        body = response.json()
        assert body["avatar_url"] == "https://example.com/a.png"
        assert body["name"] == registered_user["name"]

    async def test_empty_name_rejected(self, client, auth_headers):
        response = await client.patch(
            "/api/v1/users/me", json={"name": ""}, headers=auth_headers
        )
        assert response.status_code == 422

    async def test_email_field_is_ignored_or_rejected(
        self, client, auth_headers, registered_user
    ):
        """Changing email via this endpoint isn't part of the contract: the
        email must either stay the same or the request must be rejected."""
        response = await client.patch(
            "/api/v1/users/me",
            json={"email": "changed@example.com"},
            headers=auth_headers,
        )

        if response.status_code == 200:
            assert response.json()["email"] == registered_user["email"]
        else:
            assert response.status_code in (400, 403, 422)

    async def test_update_does_not_affect_other_users(self, client):
        from ..factories import login_payload, user_payload

        await client.post("/api/v1/users/", json=user_payload())
        await client.post(
            "/api/v1/users/",
            json=user_payload(email="second@example.com", name="Second User"),
        )

        login_response = await client.post(
            "/api/v1/login/access-token",
            data=login_payload(user_payload()),
        )
        headers = {
            "Authorization": f"Bearer {login_response.json()['access_token']}"
        }

        await client.patch(
            "/api/v1/users/me", json={"name": "Changed"}, headers=headers
        )

        from app.models import User

        other = await User.find_one({"email": "second@example.com"})
        assert other.name == "Second User"
