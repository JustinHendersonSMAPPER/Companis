"""Unit tests for the recipe search service.

These tests mock the AI service, database helper functions, and _save_recipe
to verify that search_recipes_with_ai correctly orchestrates recipe generation,
identifies missing ingredients, captures substitutions, and returns a properly
structured RecipeSearchResponse.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.recipe import RecipeSearchResponse, SubstitutionSuggestion
from app.services.recipe import search_recipes_with_ai


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


SAMPLE_RAW_RECIPE: dict = {
    "title": "Test Pasta",
    "description": "A test recipe",
    "instructions": "Cook it",
    "cuisine": "Italian",
    "meal_type": "dinner",
    "prep_time_minutes": 15,
    "cook_time_minutes": 20,
    "servings": 4,
    "difficulty": "easy",
    "dietary_tags": "none",
    "calorie_estimate": 400,
    "ingredients": [
        {"name": "pasta", "quantity": 200, "unit": "g", "is_optional": False, "substitution_notes": ""},
        {"name": "truffle oil", "quantity": 1, "unit": "tbsp", "is_optional": False, "substitution_notes": "use olive oil instead"},
        {"name": "parsley", "quantity": 1, "unit": "tbsp", "is_optional": True, "substitution_notes": ""},
    ],
}


def _make_recipe_mock(
    recipe_id: str = "recipe-1",
    title: str = "Test Pasta",
    description: str = "A test recipe",
    instructions: str = "Cook it",
    cuisine: str = "Italian",
    meal_type: str = "dinner",
    prep_time_minutes: int = 15,
    cook_time_minutes: int = 20,
    servings: int = 4,
    difficulty: str = "easy",
    image_url: str | None = None,
    source: str = "ai_generated",
    dietary_tags: str = "none",
    calorie_estimate: int = 400,
) -> MagicMock:
    """Create a mock Recipe model object as returned by _save_recipe."""
    recipe = MagicMock()
    recipe.id = recipe_id
    recipe.title = title
    recipe.description = description
    recipe.instructions = instructions
    recipe.cuisine = cuisine
    recipe.meal_type = meal_type
    recipe.prep_time_minutes = prep_time_minutes
    recipe.cook_time_minutes = cook_time_minutes
    recipe.servings = servings
    recipe.difficulty = difficulty
    recipe.image_url = image_url
    recipe.source = source
    recipe.dietary_tags = dietary_tags
    recipe.calorie_estimate = calorie_estimate
    recipe.created_at = datetime(2024, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    return recipe


# ---------------------------------------------------------------------------
# search_recipes_with_ai tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSearchRecipesWithAI:
    @patch("app.services.recipe._get_family_dietary_notes", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_health_goals", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_dietary_preferences", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_household_ingredient_names", new_callable=AsyncMock, return_value=["pasta", "tomatoes"])
    @patch("app.services.recipe._save_recipe", new_callable=AsyncMock)
    @patch("app.services.recipe.get_ai_service")
    async def test_basic_flow_returns_recipe_search_response(
        self,
        mock_get_ai: MagicMock,
        mock_save: AsyncMock,
        mock_ingredients: AsyncMock,
        mock_prefs: AsyncMock,
        mock_goals: AsyncMock,
        mock_notes: AsyncMock,
    ) -> None:
        raw = {
            "title": "Test Pasta",
            "description": "A test recipe",
            "instructions": "Cook it",
            "cuisine": "Italian",
            "meal_type": "dinner",
            "prep_time_minutes": 15,
            "cook_time_minutes": 20,
            "servings": 4,
            "difficulty": "easy",
            "dietary_tags": "none",
            "calorie_estimate": 400,
            "ingredients": [
                {"name": "pasta", "quantity": 200, "unit": "g", "is_optional": False, "substitution_notes": ""},
                {"name": "tomatoes", "quantity": 2, "unit": "pcs", "is_optional": False, "substitution_notes": ""},
            ],
        }
        mock_ai = AsyncMock()
        mock_ai.generate_recipes.return_value = [raw]
        mock_get_ai.return_value = mock_ai
        mock_save.return_value = _make_recipe_mock()

        db = AsyncMock()
        result = await search_recipes_with_ai(
            prompt="pasta recipe",
            user_id="user-1",
            household_id="household-1",
            max_results=5,
            prefer_available=True,
            max_prep_time=None,
            cuisine=None,
            dietary_filter=[],
            db=db,
        )

        assert isinstance(result, RecipeSearchResponse)
        assert len(result.recipes) == 1
        assert result.recipes[0].title == "Test Pasta"
        assert result.recipes[0].id == "recipe-1"
        assert result.recipes[0].source == "ai_generated"

        mock_ingredients.assert_called_once_with("household-1", db)
        mock_prefs.assert_called_once_with("user-1", db)
        mock_goals.assert_called_once_with("user-1", db)
        mock_notes.assert_called_once_with("household-1", db)

    @patch("app.services.recipe._get_family_dietary_notes", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_health_goals", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_dietary_preferences", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_household_ingredient_names", new_callable=AsyncMock, return_value=["pasta"])
    @patch("app.services.recipe._save_recipe", new_callable=AsyncMock)
    @patch("app.services.recipe.get_ai_service")
    async def test_missing_ingredients_identified_correctly(
        self,
        mock_get_ai: MagicMock,
        mock_save: AsyncMock,
        mock_ingredients: AsyncMock,
        mock_prefs: AsyncMock,
        mock_goals: AsyncMock,
        mock_notes: AsyncMock,
    ) -> None:
        """Ingredients not in the household and without substitution notes are missing."""
        raw = {
            "title": "Saffron Pasta",
            "description": "A test recipe",
            "instructions": "Cook it",
            "cuisine": "Italian",
            "meal_type": "dinner",
            "prep_time_minutes": 15,
            "cook_time_minutes": 20,
            "servings": 4,
            "difficulty": "easy",
            "dietary_tags": "none",
            "calorie_estimate": 400,
            "ingredients": [
                {"name": "pasta", "quantity": 200, "unit": "g", "is_optional": False, "substitution_notes": ""},
                {"name": "saffron", "quantity": 1, "unit": "pinch", "is_optional": False, "substitution_notes": ""},
            ],
        }
        mock_ai = AsyncMock()
        mock_ai.generate_recipes.return_value = [raw]
        mock_get_ai.return_value = mock_ai
        mock_save.return_value = _make_recipe_mock(recipe_id="recipe-missing")

        db = AsyncMock()
        result = await search_recipes_with_ai(
            prompt="saffron pasta",
            user_id="user-1",
            household_id="household-1",
            max_results=5,
            prefer_available=True,
            max_prep_time=None,
            cuisine=None,
            dietary_filter=[],
            db=db,
        )

        assert "recipe-missing" in result.missing_ingredients
        assert "saffron" in result.missing_ingredients["recipe-missing"]
        assert "pasta" not in result.missing_ingredients["recipe-missing"]

    @patch("app.services.recipe._get_family_dietary_notes", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_health_goals", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_dietary_preferences", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_household_ingredient_names", new_callable=AsyncMock, return_value=["pasta"])
    @patch("app.services.recipe._save_recipe", new_callable=AsyncMock)
    @patch("app.services.recipe.get_ai_service")
    async def test_substitutions_captured_when_notes_present(
        self,
        mock_get_ai: MagicMock,
        mock_save: AsyncMock,
        mock_ingredients: AsyncMock,
        mock_prefs: AsyncMock,
        mock_goals: AsyncMock,
        mock_notes: AsyncMock,
    ) -> None:
        """Unavailable ingredients with substitution_notes go to substitutions, not missing."""
        mock_ai = AsyncMock()
        mock_ai.generate_recipes.return_value = [SAMPLE_RAW_RECIPE]
        mock_get_ai.return_value = mock_ai
        mock_save.return_value = _make_recipe_mock(recipe_id="recipe-sub")

        db = AsyncMock()
        result = await search_recipes_with_ai(
            prompt="pasta with truffle",
            user_id="user-1",
            household_id="household-1",
            max_results=5,
            prefer_available=True,
            max_prep_time=None,
            cuisine=None,
            dietary_filter=[],
            db=db,
        )

        assert "recipe-sub" in result.substitutions
        subs = result.substitutions["recipe-sub"]
        assert len(subs) >= 1
        assert any(s.original_ingredient == "truffle oil" for s in subs)
        truffle_sub = next(s for s in subs if s.original_ingredient == "truffle oil")
        assert truffle_sub.substitute == "use olive oil instead"
        assert isinstance(truffle_sub, SubstitutionSuggestion)

    @patch("app.services.recipe._get_family_dietary_notes", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_health_goals", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_dietary_preferences", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_household_ingredient_names", new_callable=AsyncMock, return_value=["pasta", "tomato", "garlic"])
    @patch("app.services.recipe._save_recipe", new_callable=AsyncMock)
    @patch("app.services.recipe.get_ai_service")
    async def test_prefer_available_passes_ingredients_to_ai(
        self,
        mock_get_ai: MagicMock,
        mock_save: AsyncMock,
        mock_ingredients: AsyncMock,
        mock_prefs: AsyncMock,
        mock_goals: AsyncMock,
        mock_notes: AsyncMock,
    ) -> None:
        mock_ai = AsyncMock()
        mock_ai.generate_recipes.return_value = []
        mock_get_ai.return_value = mock_ai

        db = AsyncMock()
        await search_recipes_with_ai(
            prompt="quick dinner",
            user_id="user-1",
            household_id="household-1",
            max_results=5,
            prefer_available=True,
            max_prep_time=None,
            cuisine=None,
            dietary_filter=[],
            db=db,
        )

        call_kwargs = mock_ai.generate_recipes.call_args[1]
        assert call_kwargs["available_ingredients"] == ["pasta", "tomato", "garlic"]

    @patch("app.services.recipe._get_family_dietary_notes", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_health_goals", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_dietary_preferences", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_household_ingredient_names", new_callable=AsyncMock, return_value=["pasta", "tomato"])
    @patch("app.services.recipe._save_recipe", new_callable=AsyncMock)
    @patch("app.services.recipe.get_ai_service")
    async def test_prefer_available_false_passes_empty_list(
        self,
        mock_get_ai: MagicMock,
        mock_save: AsyncMock,
        mock_ingredients: AsyncMock,
        mock_prefs: AsyncMock,
        mock_goals: AsyncMock,
        mock_notes: AsyncMock,
    ) -> None:
        mock_ai = AsyncMock()
        mock_ai.generate_recipes.return_value = []
        mock_get_ai.return_value = mock_ai

        db = AsyncMock()
        await search_recipes_with_ai(
            prompt="surprise me",
            user_id="user-1",
            household_id="household-1",
            max_results=5,
            prefer_available=False,
            max_prep_time=None,
            cuisine=None,
            dietary_filter=[],
            db=db,
        )

        call_kwargs = mock_ai.generate_recipes.call_args[1]
        assert call_kwargs["available_ingredients"] == []

    @patch("app.services.recipe._get_family_dietary_notes", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_health_goals", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_dietary_preferences", new_callable=AsyncMock, return_value=["vegetarian"])
    @patch("app.services.recipe._get_household_ingredient_names", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._save_recipe", new_callable=AsyncMock)
    @patch("app.services.recipe.get_ai_service")
    async def test_dietary_filter_combined_with_user_preferences(
        self,
        mock_get_ai: MagicMock,
        mock_save: AsyncMock,
        mock_ingredients: AsyncMock,
        mock_prefs: AsyncMock,
        mock_goals: AsyncMock,
        mock_notes: AsyncMock,
    ) -> None:
        mock_ai = AsyncMock()
        mock_ai.generate_recipes.return_value = []
        mock_get_ai.return_value = mock_ai

        db = AsyncMock()
        await search_recipes_with_ai(
            prompt="healthy meals",
            user_id="user-1",
            household_id="household-1",
            max_results=5,
            prefer_available=True,
            max_prep_time=None,
            cuisine=None,
            dietary_filter=["gluten-free", "dairy-free"],
            db=db,
        )

        call_kwargs = mock_ai.generate_recipes.call_args[1]
        dietary = call_kwargs["dietary_preferences"]
        assert "vegetarian" in dietary
        assert "gluten-free" in dietary
        assert "dairy-free" in dietary

    @patch("app.services.recipe._get_family_dietary_notes", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_health_goals", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_dietary_preferences", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_household_ingredient_names", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._save_recipe", new_callable=AsyncMock)
    @patch("app.services.recipe.get_ai_service")
    async def test_empty_recipe_results(
        self,
        mock_get_ai: MagicMock,
        mock_save: AsyncMock,
        mock_ingredients: AsyncMock,
        mock_prefs: AsyncMock,
        mock_goals: AsyncMock,
        mock_notes: AsyncMock,
    ) -> None:
        mock_ai = AsyncMock()
        mock_ai.generate_recipes.return_value = []
        mock_get_ai.return_value = mock_ai

        db = AsyncMock()
        result = await search_recipes_with_ai(
            prompt="impossible recipe",
            user_id="user-1",
            household_id="household-1",
            max_results=5,
            prefer_available=True,
            max_prep_time=None,
            cuisine=None,
            dietary_filter=[],
            db=db,
        )

        assert isinstance(result, RecipeSearchResponse)
        assert result.recipes == []
        assert result.missing_ingredients == {}
        assert result.substitutions == {}
        mock_save.assert_not_called()

    @patch("app.services.recipe._get_family_dietary_notes", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_health_goals", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_dietary_preferences", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_household_ingredient_names", new_callable=AsyncMock, return_value=["pasta"])
    @patch("app.services.recipe._save_recipe", new_callable=AsyncMock)
    @patch("app.services.recipe.get_ai_service")
    async def test_recipe_response_fields_populated_from_saved_recipe(
        self,
        mock_get_ai: MagicMock,
        mock_save: AsyncMock,
        mock_ingredients: AsyncMock,
        mock_prefs: AsyncMock,
        mock_goals: AsyncMock,
        mock_notes: AsyncMock,
    ) -> None:
        raw = {
            "title": "Gourmet Pasta",
            "description": "A fancy dish",
            "instructions": "Cook with care",
            "cuisine": "Italian",
            "meal_type": "dinner",
            "prep_time_minutes": 30,
            "cook_time_minutes": 45,
            "servings": 2,
            "difficulty": "medium",
            "dietary_tags": "vegetarian",
            "calorie_estimate": 550,
            "ingredients": [
                {"name": "pasta", "quantity": 300, "unit": "g", "is_optional": False, "substitution_notes": ""},
            ],
        }
        mock_ai = AsyncMock()
        mock_ai.generate_recipes.return_value = [raw]
        mock_get_ai.return_value = mock_ai
        mock_save.return_value = _make_recipe_mock(
            recipe_id="recipe-gourmet",
            title="Gourmet Pasta",
            description="A fancy dish",
            instructions="Cook with care",
            cuisine="Italian",
            meal_type="dinner",
            prep_time_minutes=30,
            cook_time_minutes=45,
            servings=2,
            difficulty="medium",
            dietary_tags="vegetarian",
            calorie_estimate=550,
        )

        db = AsyncMock()
        result = await search_recipes_with_ai(
            prompt="gourmet pasta",
            user_id="user-1",
            household_id="household-1",
            max_results=5,
            prefer_available=True,
            max_prep_time=None,
            cuisine=None,
            dietary_filter=[],
            db=db,
        )

        recipe_resp = result.recipes[0]
        assert recipe_resp.id == "recipe-gourmet"
        assert recipe_resp.title == "Gourmet Pasta"
        assert recipe_resp.cuisine == "Italian"
        assert recipe_resp.meal_type == "dinner"
        assert recipe_resp.prep_time_minutes == 30
        assert recipe_resp.cook_time_minutes == 45
        assert recipe_resp.servings == 2
        assert recipe_resp.difficulty == "medium"
        assert recipe_resp.calorie_estimate == 550
        assert recipe_resp.source == "ai_generated"

    @patch("app.services.recipe._get_family_dietary_notes", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_health_goals", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_dietary_preferences", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_household_ingredient_names", new_callable=AsyncMock, return_value=["pasta"])
    @patch("app.services.recipe._save_recipe", new_callable=AsyncMock)
    @patch("app.services.recipe.get_ai_service")
    async def test_optional_ingredient_not_marked_missing(
        self,
        mock_get_ai: MagicMock,
        mock_save: AsyncMock,
        mock_ingredients: AsyncMock,
        mock_prefs: AsyncMock,
        mock_goals: AsyncMock,
        mock_notes: AsyncMock,
    ) -> None:
        """Optional ingredients that are not available should not appear in missing."""
        raw = {
            "title": "Simple Pasta",
            "description": "Basic dish",
            "instructions": "Boil and serve",
            "cuisine": "Italian",
            "meal_type": "lunch",
            "prep_time_minutes": 10,
            "cook_time_minutes": 15,
            "servings": 2,
            "difficulty": "easy",
            "dietary_tags": "none",
            "calorie_estimate": 300,
            "ingredients": [
                {"name": "pasta", "quantity": 200, "unit": "g", "is_optional": False, "substitution_notes": ""},
                {"name": "parmesan", "quantity": 50, "unit": "g", "is_optional": True, "substitution_notes": ""},
            ],
        }
        mock_ai = AsyncMock()
        mock_ai.generate_recipes.return_value = [raw]
        mock_get_ai.return_value = mock_ai
        mock_save.return_value = _make_recipe_mock(recipe_id="recipe-opt")

        db = AsyncMock()
        result = await search_recipes_with_ai(
            prompt="simple pasta",
            user_id="user-1",
            household_id="household-1",
            max_results=5,
            prefer_available=True,
            max_prep_time=None,
            cuisine=None,
            dietary_filter=[],
            db=db,
        )

        assert "recipe-opt" not in result.missing_ingredients

    @patch("app.services.recipe._get_family_dietary_notes", new_callable=AsyncMock, return_value=["kid allergic to shellfish"])
    @patch("app.services.recipe._get_user_health_goals", new_callable=AsyncMock, return_value=["high-protein"])
    @patch("app.services.recipe._get_user_dietary_preferences", new_callable=AsyncMock, return_value=["halal"])
    @patch("app.services.recipe._get_household_ingredient_names", new_callable=AsyncMock, return_value=["chicken", "rice"])
    @patch("app.services.recipe._save_recipe", new_callable=AsyncMock)
    @patch("app.services.recipe.get_ai_service")
    async def test_ai_called_with_correct_parameters(
        self,
        mock_get_ai: MagicMock,
        mock_save: AsyncMock,
        mock_ingredients: AsyncMock,
        mock_prefs: AsyncMock,
        mock_goals: AsyncMock,
        mock_notes: AsyncMock,
    ) -> None:
        mock_ai = AsyncMock()
        mock_ai.generate_recipes.return_value = []
        mock_get_ai.return_value = mock_ai

        db = AsyncMock()
        await search_recipes_with_ai(
            prompt="chicken rice bowl",
            user_id="user-1",
            household_id="household-1",
            max_results=3,
            prefer_available=True,
            max_prep_time=30,
            cuisine="Asian",
            dietary_filter=["no-pork"],
            db=db,
        )

        mock_ai.generate_recipes.assert_called_once()
        call_kwargs = mock_ai.generate_recipes.call_args[1]
        assert call_kwargs["prompt"] == "chicken rice bowl"
        assert call_kwargs["available_ingredients"] == ["chicken", "rice"]
        assert "halal" in call_kwargs["dietary_preferences"]
        assert "no-pork" in call_kwargs["dietary_preferences"]
        assert call_kwargs["health_goals"] == ["high-protein"]
        assert call_kwargs["family_dietary_notes"] == ["kid allergic to shellfish"]
        assert call_kwargs["max_results"] == 3
        assert call_kwargs["max_prep_time"] == 30
        assert call_kwargs["cuisine"] == "Asian"
        assert call_kwargs["favorite_cuisines"] == []

    @patch("app.services.recipe._get_family_dietary_notes", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_health_goals", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_user_dietary_preferences", new_callable=AsyncMock, return_value=[])
    @patch("app.services.recipe._get_household_ingredient_names", new_callable=AsyncMock, return_value=["pasta"])
    @patch("app.services.recipe._save_recipe", new_callable=AsyncMock)
    @patch("app.services.recipe.get_ai_service")
    async def test_ingredient_availability_flag_set_correctly(
        self,
        mock_get_ai: MagicMock,
        mock_save: AsyncMock,
        mock_ingredients: AsyncMock,
        mock_prefs: AsyncMock,
        mock_goals: AsyncMock,
        mock_notes: AsyncMock,
    ) -> None:
        """Verify is_available is True for household ingredients, False otherwise."""
        mock_ai = AsyncMock()
        mock_ai.generate_recipes.return_value = [SAMPLE_RAW_RECIPE]
        mock_get_ai.return_value = mock_ai
        mock_save.return_value = _make_recipe_mock(recipe_id="recipe-avail")

        db = AsyncMock()
        result = await search_recipes_with_ai(
            prompt="truffle pasta",
            user_id="user-1",
            household_id="household-1",
            max_results=5,
            prefer_available=True,
            max_prep_time=None,
            cuisine=None,
            dietary_filter=[],
            db=db,
        )

        recipe_ings = result.recipes[0].recipe_ingredients
        pasta_ing = next(i for i in recipe_ings if i.name == "pasta")
        truffle_ing = next(i for i in recipe_ings if i.name == "truffle oil")

        assert pasta_ing.is_available is True
        assert truffle_ing.is_available is False
        assert truffle_ing.has_substitution is True
        assert pasta_ing.has_substitution is False
