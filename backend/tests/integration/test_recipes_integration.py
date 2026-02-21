from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from app.schemas.recipe import RecipeResponse, RecipeSearchResponse


def _mock_recipe_response() -> RecipeSearchResponse:
    """Create a mock recipe search response for testing."""
    return RecipeSearchResponse(
        recipes=[
            RecipeResponse(
                id="mock-recipe-1",
                title="Mock Thai Curry",
                description="A simple Thai curry",
                instructions="1. Cook curry paste\n2. Add coconut milk\n3. Add chicken",
                cuisine="Thai",
                meal_type="dinner",
                prep_time_minutes=15,
                cook_time_minutes=25,
                servings=4,
                difficulty="easy",
                image_url=None,
                source="ai_generated",
                dietary_tags="dairy-free",
                calorie_estimate=450,
                created_at="2024-01-01T00:00:00",
                recipe_ingredients=[
                    {
                        "name": "chicken breast",
                        "quantity": 500.0,
                        "unit": "g",
                        "is_optional": False,
                        "substitution_notes": None,
                    },
                    {
                        "name": "coconut milk",
                        "quantity": 400.0,
                        "unit": "ml",
                        "is_optional": False,
                        "substitution_notes": None,
                    },
                ],
                average_rating=None,
                user_rating=None,
                is_favorite=False,
            )
        ],
        missing_ingredients={},
        substitutions={},
    )


@pytest.mark.asyncio
class TestRecipeSearch:
    @patch("app.services.recipe.search_recipes_with_ai", new_callable=AsyncMock)
    async def test_search_recipes(
        self,
        mock_search: AsyncMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_search.return_value = _mock_recipe_response()
        response = await client.post(
            "/api/recipes/search",
            json={"prompt": "Thai curry", "max_results": 3},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "recipes" in data
        assert len(data["recipes"]) == 1
        assert data["recipes"][0]["title"] == "Mock Thai Curry"

    @patch("app.services.recipe.search_recipes_with_ai", new_callable=AsyncMock)
    async def test_search_recipes_with_filters(
        self,
        mock_search: AsyncMock,
        client: AsyncClient,
        auth_headers: dict[str, str],
    ) -> None:
        mock_search.return_value = _mock_recipe_response()
        response = await client.post(
            "/api/recipes/search",
            json={
                "prompt": "dinner",
                "max_results": 5,
                "max_prep_time_minutes": 30,
                "cuisine": "Thai",
                "dietary_filter": ["gluten-free"],
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_empty_prompt(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/recipes/search",
            json={"prompt": ""},
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_search_requires_auth(self, client: AsyncClient) -> None:
        response = await client.post(
            "/api/recipes/search",
            json={"prompt": "dinner"},
        )
        assert response.status_code in (401, 403)


@pytest.mark.asyncio
class TestRecipeRatingAndFavorites:
    async def test_get_nonexistent_recipe(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get(
            "/api/recipes/nonexistent-id",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_rate_nonexistent_recipe(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/recipes/nonexistent-id/rate",
            json={"score": 5},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_favorite_nonexistent_recipe(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.post(
            "/api/recipes/nonexistent-id/favorite",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_unfavorite_nonexistent_recipe(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.delete(
            "/api/recipes/nonexistent-id/favorite",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_get_empty_favorites(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        response = await client.get(
            "/api/recipes/favorites/list",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []
