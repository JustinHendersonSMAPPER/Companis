from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestIngredientCRUD:
    async def test_create_ingredient(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/ingredients/",
            json={"name": "Chicken Breast", "category": "protein"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Chicken Breast"
        assert data["category"] == "protein"
        assert "id" in data

    async def test_create_ingredient_with_barcode(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/ingredients/",
            json={"name": "Organic Milk", "barcode": "0123456789", "brand": "DairyFarm"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["barcode"] == "0123456789"
        assert data["brand"] == "DairyFarm"

    async def test_search_ingredients(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        await client.post(
            "/api/ingredients/",
            json={"name": "Broccoli"},
            headers=auth_headers,
        )
        await client.post(
            "/api/ingredients/",
            json={"name": "Brown Rice"},
            headers=auth_headers,
        )
        response = await client.get(
            "/api/ingredients/search?q=bro",
            headers=auth_headers,
        )
        assert response.status_code == 200
        results = response.json()
        assert len(results) >= 2
        names = [r["name"] for r in results]
        assert "Broccoli" in names
        assert "Brown Rice" in names

    async def test_search_ingredients_no_results(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get(
            "/api/ingredients/search?q=zzzznonexistent",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []


@pytest.mark.asyncio
class TestHouseholdIngredients:
    async def test_get_empty_household_ingredients(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get("/api/ingredients/household", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_add_household_ingredient_by_name(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/ingredients/household",
            json={
                "name": "Sugar",
                "quantity": 2.0,
                "unit": "cups",
                "source": "manual",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["quantity"] == 2.0
        assert data["unit"] == "cups"
        assert data["source"] == "manual"
        assert data["ingredient"]["name"] == "Sugar"

    async def test_add_multiple_household_ingredients(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        await client.post(
            "/api/ingredients/household",
            json={"name": "Flour", "quantity": 5.0, "unit": "cups"},
            headers=auth_headers,
        )
        await client.post(
            "/api/ingredients/household",
            json={"name": "Eggs", "quantity": 12.0, "unit": "count"},
            headers=auth_headers,
        )
        response = await client.get("/api/ingredients/household", headers=auth_headers)
        assert len(response.json()) == 2

    async def test_update_household_ingredient(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = await client.post(
            "/api/ingredients/household",
            json={"name": "Butter", "quantity": 1.0, "unit": "stick"},
            headers=auth_headers,
        )
        item_id = create_resp.json()["id"]
        update_resp = await client.patch(
            f"/api/ingredients/household/{item_id}",
            json={"quantity": 3.0, "unit": "sticks"},
            headers=auth_headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["quantity"] == 3.0
        assert update_resp.json()["unit"] == "sticks"

    async def test_delete_household_ingredient(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        create_resp = await client.post(
            "/api/ingredients/household",
            json={"name": "Salt", "quantity": 1.0, "unit": "tbsp"},
            headers=auth_headers,
        )
        item_id = create_resp.json()["id"]
        delete_resp = await client.delete(
            f"/api/ingredients/household/{item_id}", headers=auth_headers
        )
        assert delete_resp.status_code == 204

        get_resp = await client.get("/api/ingredients/household", headers=auth_headers)
        assert len(get_resp.json()) == 0

    async def test_delete_nonexistent_household_ingredient(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.delete(
            "/api/ingredients/household/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_update_nonexistent_household_ingredient(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.patch(
            "/api/ingredients/household/nonexistent-id",
            json={"quantity": 5.0},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_household_ingredients_isolated_between_users(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        second_user_headers: dict[str, str],
    ) -> None:
        await client.post(
            "/api/ingredients/household",
            json={"name": "Garlic", "quantity": 3.0, "unit": "cloves"},
            headers=auth_headers,
        )
        response = await client.get("/api/ingredients/household", headers=second_user_headers)
        assert len(response.json()) == 0

    async def test_add_ingredient_requires_name_or_id(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/ingredients/household",
            json={"quantity": 1.0, "unit": "cups"},
            headers=auth_headers,
        )
        assert response.status_code == 400
