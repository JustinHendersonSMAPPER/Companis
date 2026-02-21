from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from app.config import settings
from app.services.ai.base import AIService


class OpenAIService(AIService):
    def __init__(self) -> None:
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

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
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": system_prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "[]"
        result = json.loads(content)
        if isinstance(result, list):
            return result
        return result.get("recipes", [])

    async def identify_ingredients_from_image(
        self, image_base64: str
    ) -> dict[str, Any]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                            },
                        },
                        {"type": "text", "text": self._build_image_prompt()},
                    ],
                }
            ],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content or "{}")

    async def suggest_substitutions(
        self,
        original_ingredient: str,
        dietary_restrictions: list[str],
        available_ingredients: list[str],
    ) -> list[dict[str, str]]:
        prompt = self._build_substitution_prompt(
            original_ingredient, dietary_restrictions, available_ingredients
        )
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content or "[]"
        result = json.loads(content)
        if isinstance(result, list):
            return result
        return result.get("substitutions", [])

    async def parse_voice_input(self, transcript: str) -> dict[str, Any]:
        prompt = self._build_voice_parse_prompt(transcript)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
        )
        return json.loads(response.choices[0].message.content or "{}")
