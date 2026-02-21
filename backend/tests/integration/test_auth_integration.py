from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthFlow:
    async def test_full_registration_flow(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
                "terms_accepted": True,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert data["auth_provider"] == "local"
        assert data["is_active"] is True
        assert "id" in data

    async def test_register_without_terms(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
                "terms_accepted": False,
            },
        )
        assert response.status_code == 400
        assert "terms" in response.json()["detail"].lower()

    async def test_register_creates_household(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/household/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "Kitchen" in data["name"]

    async def test_register_creates_family_member(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/household/members", headers=auth_headers)
        assert response.status_code == 200
        members = response.json()
        assert len(members) >= 1
        assert members[0]["role"] == "owner"

    async def test_login_returns_tokens(self, client: AsyncClient) -> None:
        await client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "testpassword123",
                "full_name": "Login User",
                "terms_accepted": True,
            },
        )
        response = await client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "testpassword123"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(self, client: AsyncClient) -> None:
        await client.post(
            "/api/auth/register",
            json={
                "email": "login@example.com",
                "password": "testpassword123",
                "full_name": "Login User",
                "terms_accepted": True,
            },
        )
        response = await client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/auth/login",
            json={"email": "nobody@example.com", "password": "password123"},
        )
        assert response.status_code == 401

    async def test_refresh_token(self, client: AsyncClient) -> None:
        await client.post(
            "/api/auth/register",
            json={
                "email": "refresh@example.com",
                "password": "testpassword123",
                "full_name": "Refresh User",
                "terms_accepted": True,
            },
        )
        login_resp = await client.post(
            "/api/auth/login",
            json={"email": "refresh@example.com", "password": "testpassword123"},
        )
        refresh_token = login_resp.json()["refresh_token"]
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_with_invalid_token(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert response.status_code == 401

    async def test_get_terms(self, client: AsyncClient) -> None:
        response = await client.get("/api/auth/terms")
        assert response.status_code == 200
        data = response.json()
        assert "terms_text" in data
        assert "version" in data
        assert data["version"] == "1.0"
        assert len(data["terms_text"]) > 0

    async def test_protected_endpoint_without_token(self, client: AsyncClient) -> None:
        response = await client.get("/api/users/me")
        assert response.status_code in (401, 403)

    async def test_protected_endpoint_with_invalid_token(self, client: AsyncClient) -> None:
        response = await client.get(
            "/api/users/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert response.status_code == 401
