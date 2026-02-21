from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest
from httpx import AsyncClient


@pytest.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Register a user and return auth headers with access token."""
    await client.post(
        "/api/auth/register",
        json={
            "email": "testuser@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "terms_accepted": True,
        },
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "testuser@example.com", "password": "testpassword123"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def second_user_headers(client: AsyncClient) -> dict[str, str]:
    """Register a second user and return auth headers."""
    await client.post(
        "/api/auth/register",
        json={
            "email": "second@example.com",
            "password": "testpassword123",
            "full_name": "Second User",
            "terms_accepted": True,
        },
    )
    login_resp = await client.post(
        "/api/auth/login",
        json={"email": "second@example.com", "password": "testpassword123"},
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
