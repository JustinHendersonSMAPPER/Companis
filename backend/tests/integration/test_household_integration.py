from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHousehold:
    async def test_get_household(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        response = await client.get("/api/household/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "id" in data
        assert "owner_id" in data

    async def test_create_household(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/household/",
            json={"name": "My New Kitchen"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My New Kitchen"


@pytest.mark.asyncio
class TestFamilyMembers:
    async def test_get_members_includes_owner(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/household/members", headers=auth_headers)
        assert response.status_code == 200
        members = response.json()
        assert len(members) >= 1
        roles = [m["role"] for m in members]
        assert "owner" in roles

    async def test_add_family_member(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/household/members",
            json={
                "name": "Spouse User",
                "role": "member",
                "dietary_notes": "Allergic to shellfish",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Spouse User"
        assert data["role"] == "member"
        assert data["dietary_notes"] == "Allergic to shellfish"

    async def test_add_child_member(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/household/members",
            json={
                "name": "Child User",
                "role": "child",
                "dietary_notes": "No spicy food",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["role"] == "child"

    async def test_update_family_member(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = await client.post(
            "/api/household/members",
            json={"name": "Update Me", "role": "member"},
            headers=auth_headers,
        )
        member_id = create_resp.json()["id"]
        update_resp = await client.patch(
            f"/api/household/members/{member_id}",
            json={
                "name": "Updated Name",
                "dietary_notes": "Now vegetarian",
            },
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        data = update_resp.json()
        assert data["name"] == "Updated Name"
        assert data["dietary_notes"] == "Now vegetarian"

    async def test_remove_family_member(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = await client.post(
            "/api/household/members",
            json={"name": "To Remove", "role": "member"},
            headers=auth_headers,
        )
        member_id = create_resp.json()["id"]
        delete_resp = await client.delete(
            f"/api/household/members/{member_id}", headers=auth_headers
        )
        assert delete_resp.status_code == 204

    async def test_remove_nonexistent_member(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.delete(
            "/api/household/members/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_update_nonexistent_member(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.patch(
            "/api/household/members/nonexistent-id",
            json={"name": "Nope"},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_multiple_family_members(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        await client.post(
            "/api/household/members",
            json={"name": "Member A", "dietary_notes": "Nut allergy"},
            headers=auth_headers,
        )
        await client.post(
            "/api/household/members",
            json={"name": "Member B", "dietary_notes": "Vegan"},
            headers=auth_headers,
        )
        response = await client.get("/api/household/members", headers=auth_headers)
        members = response.json()
        # Owner + 2 added members
        assert len(members) >= 3
