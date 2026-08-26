import pytest

from ..factories import login_payload, user_payload


class TestRegistration:
    async def test_register_returns_201_with_public_fields(self, client):
        response = await client.post("/api/v1/users/", json=user_payload())

        assert response.status_code == 201, response.text
        body = response.json()
        assert body["name"] == "Jane Doe"
        assert body["email"] == "jane.doe@example.com"
        assert body["is_active"] is True
        assert "created_at" in body

    async def test_register_never_returns_password(self, client):
        response = await client.post("/api/v1/users/", json=user_payload())

        body = response.json()
        assert "password" not in body
        assert "hashed_password" not in body

    async def test_register_persists_hashed_password_not_plaintext(self, client):
        from app.models import User

        await client.post("/api/v1/users/", json=user_payload())

        stored = await User.find_one({"email": "jane.doe@example.com"})
        assert stored is not None
        assert stored.password != "StrongPassw0rd!"

    @pytest.mark.parametrize("missing_field", ["name", "email", "password"])
    async def test_register_missing_field_returns_422(self, client, missing_field):
        payload = user_payload()
        payload.pop(missing_field)

        response = await client.post("/api/v1/users/", json=payload)
        assert response.status_code == 422

    async def test_register_invalid_email_returns_422(self, client):
        response = await client.post(
            "/api/v1/users/", json=user_payload(email="not-an-email")
        )
        assert response.status_code == 422

    async def test_register_empty_name_returns_422(self, client):
        response = await client.post("/api/v1/users/", json=user_payload(name=""))
        assert response.status_code == 422

    async def test_register_short_password_returns_422(self, client):
        response = await client.post(
            "/api/v1/users/", json=user_payload(password="short")
        )
        assert response.status_code == 422

    async def test_register_duplicate_email_returns_409(self, client):
        await client.post("/api/v1/users/", json=user_payload())

        response = await client.post("/api/v1/users/", json=user_payload(name="Other"))
        assert response.status_code == 409

    async def test_register_duplicate_email_does_not_create_second_user(self, client):
        from app.models import User

        await client.post("/api/v1/users/", json=user_payload())
        await client.post("/api/v1/users/", json=user_payload(name="Other"))

        count = await User.find({"email": "jane.doe@example.com"}).count()
        assert count == 1


class TestLogin:
    async def test_login_with_correct_credentials_returns_token(
        self, client, registered_user
    ):
        response = await client.post(
            "/api/v1/login/access-token", data=login_payload(registered_user)
        )

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["token_type"] == "bearer"
        assert isinstance(body["access_token"], str) and body["access_token"]

    async def test_login_with_wrong_password_returns_401(self, client, registered_user):
        response = await client.post(
            "/api/v1/login/access-token",
            data=login_payload(registered_user, password="WrongPassword123"),
        )
        assert response.status_code == 401

    async def test_login_with_unknown_email_returns_401(self, client):
        response = await client.post(
            "/api/v1/login/access-token",
            data={"username": "nobody@example.com", "password": "whatever123"},
        )
        assert response.status_code == 401

    async def test_login_missing_password_returns_422(self, client, registered_user):
        response = await client.post(
            "/api/v1/login/access-token",
            data={"username": registered_user["email"]},
        )
        assert response.status_code == 422

    async def test_login_for_inactive_user_returns_400(self, client, registered_user):
        from app.models import User

        user = await User.find_one({"email": registered_user["email"]})
        user.is_active = False
        await user.save()

        response = await client.post(
            "/api/v1/login/access-token", data=login_payload(registered_user)
        )
        assert response.status_code == 400

    async def test_access_token_authenticates_subsequent_request(
        self, client, registered_user
    ):
        login_response = await client.post(
            "/api/v1/login/access-token", data=login_payload(registered_user)
        )
        token = login_response.json()["access_token"]

        me_response = await client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == registered_user["email"]
