"""Unit tests for app.services.mealdb — pure transformation logic, no DB or HTTP."""

from __future__ import annotations

import pytest

from app.services.mealdb import (
    _build_description,
    _extract_ingredients,
    parse_measure,
    transform_meal,
)

# ------------------------------------------------------------------
# Sample TheMealDB fixture
# ------------------------------------------------------------------


def _sample_meal(**overrides: object) -> dict:
    """Return a minimal TheMealDB meal dict with optional overrides."""
    meal: dict = {
        "idMeal": "52772",
        "strMeal": "Teriyaki Chicken Casserole",
        "strCategory": "Chicken",
        "strArea": "Japanese",
        "strInstructions": "Preheat oven to 350.\nCombine ingredients.",
        "strMealThumb": "https://www.themealdb.com/images/media/meals/wvpsxx1468256321.jpg",
        "strTags": "Meat,Casserole",
        "strYoutube": "https://www.youtube.com/watch?v=4aZr5hZXP_s",
        "strIngredient1": "soy sauce",
        "strIngredient2": "water",
        "strIngredient3": "brown sugar",
        "strIngredient4": "",
        "strMeasure1": "3/4 cup",
        "strMeasure2": "1/2 cup",
        "strMeasure3": "1/4 cup",
        "strMeasure4": "",
    }
    # Fill remaining ingredient/measure slots with empty strings
    for i in range(5, 21):
        meal.setdefault(f"strIngredient{i}", "")
        meal.setdefault(f"strMeasure{i}", "")
    meal.update(overrides)
    return meal


# ==================================================================
# TestParseMeasure
# ==================================================================


class TestParseMeasure:
    """Test parse_measure() with various real-world TheMealDB measure strings."""

    @pytest.mark.parametrize(
        ("input_str", "expected_qty", "expected_unit"),
        [
            # Simple numbers with units
            ("1 cup", 1.0, "cup"),
            ("2 tablespoons", 2.0, "tablespoons"),
            ("100 g", 100.0, "g"),
            # Fractions
            ("3/4 cup", 0.75, "cup"),
            ("1/2 teaspoon", 0.5, "teaspoon"),
            # Mixed numbers
            ("1 1/2 tsp", 1.5, "tsp"),
            ("2 1/4 cups", 2.25, "cups"),
            # Glued units
            ("300g", 300.0, "g"),
            ("200ml", 200.0, "ml"),
            # Bare number
            ("2", 2.0, None),
            # Descriptive measures
            ("To taste", None, "to taste"),
            ("Pinch", None, "pinch"),
            ("Drizzle", None, "drizzle"),
            # Empty
            ("", None, None),
        ],
    )
    def test_parse_measure(
        self, input_str: str, expected_qty: float | None, expected_unit: str | None
    ) -> None:
        qty, unit = parse_measure(input_str)
        if expected_qty is not None:
            assert qty == pytest.approx(expected_qty)
        else:
            assert qty is None
        assert unit == expected_unit

    def test_whitespace_only(self) -> None:
        assert parse_measure("   ") == (None, None)

    def test_unknown_descriptive(self) -> None:
        """Unknown text that can't be parsed as a number falls through to descriptive."""
        qty, unit = parse_measure("Some random text")
        assert qty is None
        assert unit == "some random text"


# ==================================================================
# TestExtractIngredients
# ==================================================================


class TestExtractIngredients:
    def test_extracts_non_empty_ingredients(self) -> None:
        meal = _sample_meal()
        ingredients = _extract_ingredients(meal)
        assert len(ingredients) == 3
        assert ingredients[0]["name"] == "soy sauce"
        assert ingredients[1]["name"] == "water"
        assert ingredients[2]["name"] == "brown sugar"

    def test_measure_parsing_applied(self) -> None:
        meal = _sample_meal()
        ingredients = _extract_ingredients(meal)
        # "3/4 cup" -> 0.75, "cup"
        assert ingredients[0]["quantity"] == pytest.approx(0.75)
        assert ingredients[0]["unit"] == "cup"

    def test_empty_meal(self) -> None:
        meal: dict = {}
        for i in range(1, 21):
            meal[f"strIngredient{i}"] = ""
            meal[f"strMeasure{i}"] = ""
        assert _extract_ingredients(meal) == []

    def test_none_values(self) -> None:
        """TheMealDB sometimes returns None instead of empty string."""
        meal: dict = {}
        for i in range(1, 21):
            meal[f"strIngredient{i}"] = None
            meal[f"strMeasure{i}"] = None
        assert _extract_ingredients(meal) == []

    def test_whitespace_only_ingredient_skipped(self) -> None:
        meal = _sample_meal(**{"strIngredient1": "   ", "strMeasure1": "1 cup"})
        ingredients = _extract_ingredients(meal)
        # "   " should be skipped, so only water and brown sugar remain
        assert len(ingredients) == 2
        assert ingredients[0]["name"] == "water"


# ==================================================================
# TestBuildDescription
# ==================================================================


class TestBuildDescription:
    def test_area_and_category(self) -> None:
        meal = _sample_meal()
        desc = _build_description(meal)
        assert "Japanese chicken dish" in desc

    def test_youtube_included(self) -> None:
        meal = _sample_meal()
        desc = _build_description(meal)
        assert "Video:" in desc
        assert "youtube.com" in desc

    def test_area_only(self) -> None:
        meal = _sample_meal(strCategory="")
        desc = _build_description(meal)
        assert "Japanese dish" in desc

    def test_category_only(self) -> None:
        meal = _sample_meal(strArea="")
        desc = _build_description(meal)
        assert "Chicken dish" in desc

    def test_empty_all(self) -> None:
        meal = _sample_meal(strArea="", strCategory="", strYoutube="")
        desc = _build_description(meal)
        assert desc == ""


# ==================================================================
# TestTransformMeal
# ==================================================================


class TestTransformMeal:
    def test_full_transformation(self) -> None:
        meal = _sample_meal()
        raw = transform_meal(meal)
        assert raw["title"] == "Teriyaki Chicken Casserole"
        assert raw["cuisine"] == "Japanese"
        assert raw["meal_type"] == "Chicken"
        assert raw["dietary_tags"] == "Meat,Casserole"
        assert raw["_image_url"].startswith("https://")
        assert len(raw["ingredients"]) == 3
        assert raw["prep_time_minutes"] is None
        assert raw["cook_time_minutes"] is None
        assert raw["servings"] is None
        assert raw["difficulty"] is None
        assert raw["calorie_estimate"] is None

    def test_missing_fields_use_none(self) -> None:
        meal = _sample_meal(strArea="", strCategory="", strTags="", strMealThumb="")
        raw = transform_meal(meal)
        assert raw["cuisine"] is None
        assert raw["meal_type"] is None
        assert raw["dietary_tags"] is None
        assert raw["_image_url"] is None

    def test_untitled_fallback(self) -> None:
        meal = _sample_meal(strMeal="")
        raw = transform_meal(meal)
        assert raw["title"] == "Untitled Recipe"

    def test_none_title_fallback(self) -> None:
        meal = _sample_meal(strMeal=None)
        raw = transform_meal(meal)
        assert raw["title"] == "Untitled Recipe"

    def test_instructions_preserved(self) -> None:
        meal = _sample_meal()
        raw = transform_meal(meal)
        assert "Preheat oven" in raw["instructions"]
        assert "Combine ingredients" in raw["instructions"]
