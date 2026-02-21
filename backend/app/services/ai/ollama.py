from __future__ import annotations

import json
from typing import Any

from ollama import AsyncClient

from app.config import settings
from app.services.ai.base import AIService


class OllamaService(AIService):
    def __init__(self) -> None:
        self.client = AsyncClient(host=settings.ollama_base_url)
        self.model = settings.ollama_model

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
        system_prompt = self._build_recipe_prompt(
            prompt,
            available_ingredients,
            dietary_preferences,
            health_goals,
            family_dietary_notes,
            favorite_cuisines,
            max_results,
            max_prep_time,
            cuisine,
        )
        response = await self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": system_prompt}],
            format="json",
        )
        content = response["message"]["content"]
        result = json.loads(content)
        if isinstance(result, list):
            return result
        return result.get("recipes", [])

    async def identify_ingredients_from_image(
        self, image_base64: str
    ) -> dict[str, Any]:
        response = await self.client.chat(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": self._build_image_prompt(),
                    "images": [image_base64],
                }
            ],
            format="json",
        )
        return json.loads(response["message"]["content"])

    async def suggest_substitutions(
        self,
        original_ingredient: str,
        dietary_restrictions: list[str],
        available_ingredients: list[str],
    ) -> list[dict[str, str]]:
        prompt = self._build_substitution_prompt(
            original_ingredient, dietary_restrictions, available_ingredients
        )
        response = await self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format="json",
        )
        result = json.loads(response["message"]["content"])
        if isinstance(result, list):
            return result
        return result.get("substitutions", [])

    async def parse_voice_input(self, transcript: str) -> dict[str, Any]:
        prompt = self._build_voice_parse_prompt(transcript)
        response = await self.client.chat(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            format="json",
        )
        return json.loads(response["message"]["content"])
