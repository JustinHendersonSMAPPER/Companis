from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestShoppingCart:
    async def test_get_empty_carts(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        response = await client.get("/api/shopping/", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_cart(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        response = await client.post(
            "/api/shopping/",
            json={"name": "Weekly Groceries"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Weekly Groceries"
        assert data["is_active"] is True
        assert data["items"] == []

    async def test_create_cart_default_name(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/shopping/",
            json={},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["name"] == "My Shopping List"

    async def test_list_carts(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        await client.post(
            "/api/shopping/",
            json={"name": "Cart One"},
            headers=auth_headers,
        )
        await client.post(
            "/api/shopping/",
            json={"name": "Cart Two"},
            headers=auth_headers,
        )
        response = await client.get("/api/shopping/", headers=auth_headers)
        assert len(response.json()) == 2


@pytest.mark.asyncio
class TestShoppingCartItems:
    async def _create_cart(self, client: AsyncClient, auth_headers: dict[str, str]) -> str:
        resp = await client.post(
            "/api/shopping/",
            json={"name": "Test Cart"},
            headers=auth_headers,
        )
        return resp.json()["id"]

    async def test_add_item_to_cart(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        cart_id = await self._create_cart(client, auth_headers)
        response = await client.post(
            f"/api/shopping/{cart_id}/items",
            json={"name": "Milk", "quantity": 1.0, "unit": "gallon"},
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Milk"
        assert data["quantity"] == 1.0
        assert data["unit"] == "gallon"
        assert data["is_purchased"] is False

    async def test_add_multiple_items(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        cart_id = await self._create_cart(client, auth_headers)
        await client.post(
            f"/api/shopping/{cart_id}/items",
            json={"name": "Eggs", "quantity": 12.0, "unit": "count"},
            headers=auth_headers,
        )
        await client.post(
            f"/api/shopping/{cart_id}/items",
            json={"name": "Bread", "quantity": 1.0, "unit": "loaf"},
            headers=auth_headers,
        )
        response = await client.get("/api/shopping/", headers=auth_headers)
        cart = next(c for c in response.json() if c["id"] == cart_id)
        assert len(cart["items"]) == 2

    async def test_update_cart_item(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        cart_id = await self._create_cart(client, auth_headers)
        item_resp = await client.post(
            f"/api/shopping/{cart_id}/items",
            json={"name": "Butter"},
            headers=auth_headers,
        )
        item_id = item_resp.json()["id"]
        response = await client.patch(
            f"/api/shopping/{cart_id}/items/{item_id}",
            json={"quantity": 2.0, "unit": "sticks"},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["quantity"] == 2.0
        assert response.json()["unit"] == "sticks"

    async def test_mark_item_purchased(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        cart_id = await self._create_cart(client, auth_headers)
        item_resp = await client.post(
            f"/api/shopping/{cart_id}/items",
            json={"name": "Sugar"},
            headers=auth_headers,
        )
        item_id = item_resp.json()["id"]
        response = await client.patch(
            f"/api/shopping/{cart_id}/items/{item_id}",
            json={"is_purchased": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json()["is_purchased"] is True

    async def test_remove_cart_item(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        cart_id = await self._create_cart(client, auth_headers)
        item_resp = await client.post(
            f"/api/shopping/{cart_id}/items",
            json={"name": "Cheese"},
            headers=auth_headers,
        )
        item_id = item_resp.json()["id"]
        delete_resp = await client.delete(
            f"/api/shopping/{cart_id}/items/{item_id}",
            headers=auth_headers,
        )
        assert delete_resp.status_code == 204

    async def test_remove_nonexistent_item(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        cart_id = await self._create_cart(client, auth_headers)
        response = await client.delete(
            f"/api/shopping/{cart_id}/items/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_add_item_to_nonexistent_cart(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/shopping/nonexistent-cart/items",
            json={"name": "Milk"},
            headers=auth_headers,
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestAddMissingIngredients:
    async def test_add_missing_ingredients_creates_cart(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/shopping/add-missing-ingredients",
            json={
                "recipe_id": "fake-recipe-id",
                "ingredient_names": ["basil", "oregano", "mozzarella"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        items = response.json()
        assert len(items) == 3
        names = [i["name"] for i in items]
        assert "basil" in names
        assert "oregano" in names
        assert "mozzarella" in names

    async def test_add_missing_ingredients_uses_existing_cart(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        await client.post(
            "/api/shopping/",
            json={"name": "Existing Cart"},
            headers=auth_headers,
        )
        response = await client.post(
            "/api/shopping/add-missing-ingredients",
            json={
                "recipe_id": "fake-recipe-id",
                "ingredient_names": ["tomato", "onion"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert len(response.json()) == 2

    async def test_carts_isolated_between_users(
        self,
        client: AsyncClient,
        auth_headers: dict[str, str],
        second_user_headers: dict[str, str],
    ) -> None:
        await client.post(
            "/api/shopping/",
            json={"name": "User1 Cart"},
            headers=auth_headers,
        )
        response = await client.get("/api/shopping/", headers=second_user_headers)
        assert len(response.json()) == 0
