from __future__ import annotations

import asyncio
import json
from typing import Any

from app.config import settings
from app.services.ai.base import AIService


class ClaudeLocalService(AIService):
    """Uses locally installed Claude Code CLI for AI inference."""

    async def _run_claude(self, prompt: str) -> str:
        proc = await asyncio.create_subprocess_exec(
            "claude",
            "--print",
            "--model",
            settings.claude_local_model,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate(input=prompt.encode())
        if proc.returncode != 0:
            error_msg = stderr.decode().strip()
            msg = f"Claude local CLI failed: {error_msg}"
            raise RuntimeError(msg)
        return stdout.decode().strip()

    def _extract_json(self, text: str) -> Any:
        start = text.find("[")
        end = text.rfind("]") + 1
        if start == -1:
            start = text.find("{")
            end = text.rfind("}") + 1
        if start == -1:
            msg = "No JSON found in response"
            raise ValueError(msg)
        return json.loads(text[start:end])

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
        response = await self._run_claude(system_prompt)
        result = self._extract_json(response)
        if isinstance(result, list):
            return result
        return result.get("recipes", [])

    async def identify_ingredients_from_image(
        self, image_base64: str
    ) -> dict[str, Any]:
        prompt = (
            f"{self._build_image_prompt()}\n\n"
            f"[Image data provided as base64, length: {len(image_base64)} chars]"
        )
        response = await self._run_claude(prompt)
        return self._extract_json(response)

    async def suggest_substitutions(
        self,
        original_ingredient: str,
        dietary_restrictions: list[str],
        available_ingredients: list[str],
    ) -> list[dict[str, str]]:
        prompt = self._build_substitution_prompt(
            original_ingredient, dietary_restrictions, available_ingredients
        )
        response = await self._run_claude(prompt)
        result = self._extract_json(response)
        if isinstance(result, list):
            return result
        return result.get("substitutions", [])

    async def parse_voice_input(self, transcript: str) -> dict[str, Any]:
        prompt = self._build_voice_parse_prompt(transcript)
        response = await self._run_claude(prompt)
        return self._extract_json(response)
