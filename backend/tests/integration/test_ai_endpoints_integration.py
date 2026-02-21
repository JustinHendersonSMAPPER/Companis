from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAIProviders:
    async def test_get_providers(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/ai/providers", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "current_provider" in data
        assert "available_providers" in data
        assert isinstance(data["available_providers"], list)
        assert len(data["available_providers"]) >= 4

    async def test_get_providers_requires_auth(self, client: AsyncClient) -> None:
        response = await client.get("/api/ai/providers")
        assert response.status_code in (401, 403)


@pytest.mark.asyncio
class TestHealthCheck:
    async def test_health_check(self, client: AsyncClient) -> None:
        response = await client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
