from __future__ import annotations

import json
from typing import Any

import anthropic

from app.config import settings
from app.services.ai.base import AIService


class AnthropicService(AIService):
    def __init__(self) -> None:
        self.client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_model

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
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{"role": "user", "content": system_prompt}],
        )
        content = response.content[0].text
        result = json.loads(content)
        if isinstance(result, list):
            return result
        return result.get("recipes", [])

    async def identify_ingredients_from_image(
        self, image_base64: str
    ) -> dict[str, Any]:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64,
                            },
                        },
                        {"type": "text", "text": self._build_image_prompt()},
                    ],
                }
            ],
        )
        return json.loads(response.content[0].text)

    async def suggest_substitutions(
        self,
        original_ingredient: str,
        dietary_restrictions: list[str],
        available_ingredients: list[str],
    ) -> list[dict[str, str]]:
        prompt = self._build_substitution_prompt(
            original_ingredient, dietary_restrictions, available_ingredients
        )
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        result = json.loads(response.content[0].text)
        if isinstance(result, list):
            return result
        return result.get("substitutions", [])

    async def parse_voice_input(self, transcript: str) -> dict[str, Any]:
        prompt = self._build_voice_parse_prompt(transcript)
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return json.loads(response.content[0].text)
