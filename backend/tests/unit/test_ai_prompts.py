from __future__ import annotations

from typing import Any

from app.services.ai.base import AIService


class ConcreteAIService(AIService):
    """Concrete implementation for testing base class prompt builders."""

    async def generate_recipes(self, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    async def identify_ingredients_from_image(self, image_base64: str) -> dict[str, Any]:
        return {}

    async def suggest_substitutions(
        self,
        original_ingredient: str,
        dietary_restrictions: list[str],
        available_ingredients: list[str],
    ) -> list[dict[str, str]]:
        return []

    async def parse_voice_input(self, transcript: str) -> dict[str, Any]:
        return {}


class TestBuildRecipePrompt:
    def setup_method(self) -> None:
        self.service = ConcreteAIService()

    def test_basic_prompt_structure(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="Make me pasta",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=3,
            max_prep_time=None,
            cuisine=None,
        )
        assert "Companis" in prompt
        assert "Make me pasta" in prompt
        assert "Return exactly 3 recipes" in prompt
        assert "JSON" in prompt

    def test_includes_available_ingredients(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="dinner",
            available_ingredients=["chicken", "rice", "broccoli"],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=5,
            max_prep_time=None,
            cuisine=None,
        )
        assert "chicken" in prompt
        assert "rice" in prompt
        assert "broccoli" in prompt

    def test_no_ingredients_shows_not_specified(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="dinner",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=5,
            max_prep_time=None,
            cuisine=None,
        )
        assert "Not specified" in prompt

    def test_allergy_enforcement_in_prompt(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="dinner",
            available_ingredients=[],
            dietary_preferences=["nut allergy", "gluten-free"],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=5,
            max_prep_time=None,
            cuisine=None,
        )
        assert "CRITICAL SAFETY REQUIREMENT" in prompt
        assert "ALLERGIES" in prompt
        assert "ABSOLUTE" in prompt
        assert "NEVER include" in prompt
        assert "nut allergy" in prompt
        assert "gluten-free" in prompt
        assert "serious harm" in prompt

    def test_health_goals_included(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="dinner",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=["lose weight", "lower cholesterol"],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=5,
            max_prep_time=None,
            cuisine=None,
        )
        assert "lose weight" in prompt
        assert "lower cholesterol" in prompt
        assert "give preference to" in prompt

    def test_family_dietary_notes_included(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="dinner",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=["son allergic to shellfish", "daughter is vegetarian"],
            favorite_cuisines=[],
            max_results=5,
            max_prep_time=None,
            cuisine=None,
        )
        assert "son allergic to shellfish" in prompt
        assert "daughter is vegetarian" in prompt
        assert "MUST respect" in prompt

    def test_max_prep_time_included(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="dinner",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=5,
            max_prep_time=30,
            cuisine=None,
        )
        assert "30 minutes" in prompt

    def test_cuisine_filter_included(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="dinner",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=5,
            max_prep_time=None,
            cuisine="Thai",
        )
        assert "Thai" in prompt

    def test_favorite_cuisines_included(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="dinner",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=["Italian", "Japanese"],
            max_results=5,
            max_prep_time=None,
            cuisine=None,
        )
        assert "Italian" in prompt
        assert "Japanese" in prompt

    def test_recipe_json_schema_documented(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="dinner",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=5,
            max_prep_time=None,
            cuisine=None,
        )
        assert "title" in prompt
        assert "instructions" in prompt
        assert "ingredients" in prompt
        assert "substitution_notes" in prompt


class TestBuildImagePrompt:
    def setup_method(self) -> None:
        self.service = ConcreteAIService()

    def test_image_prompt_structure(self) -> None:
        prompt = self.service._build_image_prompt()
        assert "ingredients" in prompt
        assert "confidence" in prompt
        assert "JSON" in prompt


class TestBuildSubstitutionPrompt:
    def setup_method(self) -> None:
        self.service = ConcreteAIService()

    def test_substitution_prompt_basic(self) -> None:
        prompt = self.service._build_substitution_prompt("butter", [], [])
        assert "butter" in prompt
        assert "substitute" in prompt

    def test_substitution_prompt_with_restrictions(self) -> None:
        prompt = self.service._build_substitution_prompt("butter", ["dairy-free", "vegan"], [])
        assert "dairy-free" in prompt
        assert "vegan" in prompt

    def test_substitution_prompt_with_available(self) -> None:
        prompt = self.service._build_substitution_prompt("butter", [], ["coconut oil", "margarine"])
        assert "coconut oil" in prompt
        assert "margarine" in prompt


class TestBuildVoiceParsePrompt:
    def setup_method(self) -> None:
        self.service = ConcreteAIService()

    def test_voice_prompt_includes_transcript(self) -> None:
        prompt = self.service._build_voice_parse_prompt("two cups of flour and three eggs")
        assert "two cups of flour and three eggs" in prompt
        assert "name" in prompt
        assert "quantity" in prompt
        assert "unit" in prompt
