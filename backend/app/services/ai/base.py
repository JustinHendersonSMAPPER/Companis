from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class AIService(ABC):
    @abstractmethod
    async def generate_recipes(
        self,
        prompt: str,
        available_ingredients: list[str],
        dietary_preferences: list[str],
        health_goals: list[str],
        family_dietary_notes: list[str],
        favorite_cuisines: list[str],
        max_results: int = 5,
        max_prep_time: int | None = None,
        cuisine: str | None = None,
    ) -> list[dict[str, Any]]:
        """Generate recipe suggestions based on user context."""

    @abstractmethod
    async def identify_ingredients_from_image(
        self, image_base64: str
    ) -> dict[str, Any]:
        """Identify ingredients from a camera image."""

    @abstractmethod
    async def suggest_substitutions(
        self,
        original_ingredient: str,
        dietary_restrictions: list[str],
        available_ingredients: list[str],
    ) -> list[dict[str, str]]:
        """Suggest ingredient substitutions."""

    @abstractmethod
    async def parse_voice_input(self, transcript: str) -> dict[str, Any]:
        """Parse voice input to extract ingredient names and quantities."""

    def _build_recipe_prompt(
        self,
        prompt: str,
        available_ingredients: list[str],
        dietary_preferences: list[str],
        health_goals: list[str],
        family_dietary_notes: list[str],
        favorite_cuisines: list[str],
        max_results: int,
        max_prep_time: int | None,
        cuisine: str | None,
    ) -> str:
        parts = [
            "You are Companis, a personalized eating lifestyle assistant. Generate recipe suggestions as JSON.",
            f"\nUser request: {prompt}",
            "\nAvailable ingredients: "
            f"{', '.join(available_ingredients) if available_ingredients else 'Not specified'}",
        ]

        if dietary_preferences:
            parts.append(
                f"\n*** CRITICAL SAFETY REQUIREMENT - ALLERGIES AND DIETARY RESTRICTIONS ***\n"
                f"The following dietary restrictions and allergies MUST be strictly respected.\n"
                f"Allergies are ABSOLUTE - NEVER include any ingredient that a user or family "
                f"member is allergic to, not even as an optional ingredient or substitution.\n"
                f"Dietary restrictions: {', '.join(dietary_preferences)}\n"
                f"Failure to respect these could cause serious harm."
            )
        if health_goals:
            parts.append(f"Health goals (give preference to): {', '.join(health_goals)}")
        if family_dietary_notes:
            parts.append(
                f"Family dietary notes (MUST respect - these may include allergies): "
                f"{', '.join(family_dietary_notes)}"
            )
        if favorite_cuisines:
            parts.append(f"Preferred cuisines: {', '.join(favorite_cuisines)}")
        if max_prep_time:
            parts.append(f"Maximum prep time: {max_prep_time} minutes")
        if cuisine:
            parts.append(f"Cuisine filter: {cuisine}")

        parts.append(f"\nReturn exactly {max_results} recipes as a JSON array.")
        parts.append(
            'Each recipe object must have: "title", "description", "instructions" (step by step), '
            '"cuisine", "meal_type", "prep_time_minutes", "cook_time_minutes", "servings", '
            '"difficulty", "dietary_tags" (comma-separated string), "calorie_estimate", '
            'and "ingredients" (array of objects with "name", "quantity", "unit", "is_optional", '
            '"substitution_notes").'
        )
        parts.append(
            "\nFor each ingredient, indicate if a substitution is available when the user "
            "doesn't have it. Prioritize recipes using available ingredients."
        )
        parts.append("\nRespond with ONLY the JSON array, no other text.")

        return "\n".join(parts)

    def _build_image_prompt(self) -> str:
        return (
            "Analyze this image and identify all food ingredients visible. "
            "Return a JSON object with: "
            '"ingredients" (array of ingredient names) and '
            '"confidence_scores" (object mapping each ingredient name to a confidence 0-1). '
            "Only return the JSON, no other text."
        )

    def _build_substitution_prompt(
        self,
        original: str,
        restrictions: list[str],
        available: list[str],
    ) -> str:
        return (
            f"Suggest substitutions for '{original}' in cooking. "
            f"Dietary restrictions: {', '.join(restrictions) if restrictions else 'none'}. "
            f"Available ingredients: {', '.join(available) if available else 'not specified'}. "
            'Return a JSON array of objects with "substitute", "notes", and "ratio". '
            "Only return the JSON array, no other text."
        )

    def _build_voice_parse_prompt(self, transcript: str) -> str:
        return (
            f"Parse this voice input about ingredients: '{transcript}'. "
            "Extract ingredient names, quantities, and units. "
            'Return a JSON object with "ingredients" as an array of objects, '
            'each with "name", "quantity" (number or null), and "unit" (string or null). '
            "Only return the JSON, no other text."
        )
