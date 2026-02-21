from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestUserProfile:
    async def test_get_profile(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/users/me", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "testuser@example.com"
        assert data["full_name"] == "Test User"

    async def test_update_profile_name(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.patch(
            "/api/users/me",
            json={"full_name": "Updated Name"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Updated Name"

    async def test_update_profile_avatar(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.patch(
            "/api/users/me",
            json={"avatar_url": "https://example.com/avatar.png"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["avatar_url"] == "https://example.com/avatar.png"

    async def test_profile_persists_after_update(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        await client.patch(
            "/api/users/me",
            json={"full_name": "Persisted Name"},
            headers=auth_headers,
        )
        response = await client.get("/api/users/me", headers=auth_headers)
        assert response.json()["full_name"] == "Persisted Name"


@pytest.mark.asyncio
class TestDietaryPreferences:
    async def test_get_empty_preferences(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get(
            "/api/users/me/dietary-preferences", headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_add_dietary_preference(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/users/me/dietary-preferences",
            json={"preference_type": "allergy", "value": "peanuts", "notes": "Severe allergy"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["preference_type"] == "allergy"
        assert data["value"] == "peanuts"
        assert data["notes"] == "Severe allergy"
        assert "id" in data

    async def test_add_multiple_preferences(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        await client.post(
            "/api/users/me/dietary-preferences",
            json={"preference_type": "allergy", "value": "peanuts"},
            headers=auth_headers,
        )
        await client.post(
            "/api/users/me/dietary-preferences",
            json={"preference_type": "restriction", "value": "gluten-free"},
            headers=auth_headers,
        )
        response = await client.get(
            "/api/users/me/dietary-preferences", headers=auth_headers
        )
        assert len(response.json()) == 2

    async def test_delete_dietary_preference(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = await client.post(
            "/api/users/me/dietary-preferences",
            json={"preference_type": "allergy", "value": "shellfish"},
            headers=auth_headers,
        )
        pref_id = create_resp.json()["id"]
        delete_resp = await client.delete(
            f"/api/users/me/dietary-preferences/{pref_id}", headers=auth_headers
        )
        assert delete_resp.status_code == 204

        get_resp = await client.get(
            "/api/users/me/dietary-preferences", headers=auth_headers
        )
        assert len(get_resp.json()) == 0

    async def test_delete_nonexistent_preference(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.delete(
            "/api/users/me/dietary-preferences/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_preferences_isolated_between_users(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        second_user_headers: dict[str, str],
    ) -> None:
        await client.post(
            "/api/users/me/dietary-preferences",
            json={"preference_type": "allergy", "value": "nuts"},
            headers=auth_headers,
        )

        response = await client.get(
            "/api/users/me/dietary-preferences", headers=second_user_headers
        )
        assert len(response.json()) == 0


@pytest.mark.asyncio
class TestHealthGoals:
    async def test_get_empty_goals(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/users/me/health-goals", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_add_health_goal(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/users/me/health-goals",
            json={
                "goal_type": "weight_loss",
                "description": "Lose 10 pounds",
                "target_value": "150",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["goal_type"] == "weight_loss"
        assert data["description"] == "Lose 10 pounds"
        assert data["target_value"] == "150"

    async def test_add_multiple_goals(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        await client.post(
            "/api/users/me/health-goals",
            json={"goal_type": "weight_loss", "description": "Lose weight"},
            headers=auth_headers,
        )
        await client.post(
            "/api/users/me/health-goals",
            json={"goal_type": "cholesterol", "description": "Lower cholesterol"},
            headers=auth_headers,
        )
        response = await client.get("/api/users/me/health-goals", headers=auth_headers)
        assert len(response.json()) == 2

    async def test_delete_health_goal(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = await client.post(
            "/api/users/me/health-goals",
            json={"goal_type": "fitness", "description": "Run daily"},
            headers=auth_headers,
        )
        goal_id = create_resp.json()["id"]
        delete_resp = await client.delete(
            f"/api/users/me/health-goals/{goal_id}", headers=auth_headers
        )
        assert delete_resp.status_code == 204

        get_resp = await client.get("/api/users/me/health-goals", headers=auth_headers)
        assert len(get_resp.json()) == 0

    async def test_delete_nonexistent_goal(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.delete(
            "/api/users/me/health-goals/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404
