"""Unit tests for OpenAIService.

These tests mock openai.AsyncOpenAI to verify that OpenAIService
correctly builds prompts, calls the OpenAI API, and parses responses
without requiring a live API key.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


SAMPLE_RECIPE = {
    "title": "Garlic Tomato Pasta",
    "description": "A simple pasta dish with fresh tomatoes and garlic.",
    "instructions": "1. Boil pasta. 2. Sauté garlic. 3. Add tomatoes. 4. Combine.",
    "cuisine": "Italian",
    "meal_type": "dinner",
    "prep_time_minutes": 10,
    "cook_time_minutes": 20,
    "servings": 2,
    "difficulty": "easy",
    "dietary_tags": "vegetarian",
    "calorie_estimate": 450,
    "ingredients": [
        {"name": "pasta", "quantity": "200", "unit": "g", "is_optional": False, "substitution_notes": ""},
        {"name": "tomatoes", "quantity": "3", "unit": "whole", "is_optional": False, "substitution_notes": ""},
    ],
}

SAMPLE_SUBSTITUTIONS = [
    {"substitute": "coconut oil", "notes": "Good for baking", "ratio": "1:1"},
    {"substitute": "margarine", "notes": "Direct replacement", "ratio": "1:1"},
]

SAMPLE_VOICE_PARSE = {
    "ingredients": [
        {"name": "flour", "quantity": 2, "unit": "cups"},
        {"name": "eggs", "quantity": 3, "unit": None},
    ]
}

SAMPLE_IMAGE_RESULT = {
    "ingredients": ["tomato", "onion", "garlic"],
    "confidence_scores": {"tomato": 0.95, "onion": 0.88, "garlic": 0.80},
}


def _make_openai_response(content: str | None) -> MagicMock:
    """Build a mock OpenAI response with response.choices[0].message.content."""
    message = MagicMock()
    message.content = content
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


@pytest.fixture
def mock_openai_client() -> AsyncMock:
    """Create a mock AsyncOpenAI client."""
    client = AsyncMock()
    client.chat = MagicMock()
    client.chat.completions = AsyncMock()
    client.chat.completions.create = AsyncMock()
    return client


@pytest.fixture
def openai_service(mock_openai_client: AsyncMock) -> Any:
    """Create an OpenAIService with a mocked client."""
    with (
        patch("app.config.settings.openai_api_key", "test-key"),
        patch("app.config.settings.openai_model", "gpt-test"),
        patch("app.services.ai.openai_service.AsyncOpenAI", return_value=mock_openai_client),
    ):
        from app.services.ai.openai_service import OpenAIService

        service = OpenAIService()
    service.client = mock_openai_client
    return service


@pytest.mark.asyncio
class TestOpenAIRecipeGeneration:
    async def test_generate_recipes_returns_list(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """generate_recipes should return a list when API returns a JSON array."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            json.dumps([SAMPLE_RECIPE])
        )
        result = await openai_service.generate_recipes(
            prompt="simple pasta",
            available_ingredients=["pasta", "tomatoes", "garlic"],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
        )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Garlic Tomato Pasta"

    async def test_generate_recipes_handles_wrapped_json(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """generate_recipes should unwrap {recipes: [...]} envelope."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            json.dumps({"recipes": [SAMPLE_RECIPE]})
        )
        result = await openai_service.generate_recipes(
            prompt="pasta",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
        )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Garlic Tomato Pasta"

    async def test_generate_recipes_none_content_falls_back_to_empty(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """generate_recipes should treat None content as empty list."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            None
        )
        result = await openai_service.generate_recipes(
            prompt="test",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
        )
        assert isinstance(result, list)
        assert len(result) == 0

    async def test_generate_recipes_passes_correct_model(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """generate_recipes should pass the configured model name."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            json.dumps([])
        )
        await openai_service.generate_recipes(
            prompt="test",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
        )
        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-test"

    async def test_generate_recipes_uses_json_response_format(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """generate_recipes should request response_format json_object."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            json.dumps([])
        )
        await openai_service.generate_recipes(
            prompt="test",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
        )
        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}

    async def test_generate_recipes_empty_list(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """generate_recipes should handle an empty list response."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            json.dumps([])
        )
        result = await openai_service.generate_recipes(
            prompt="exotic",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
        )
        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.asyncio
class TestOpenAIImageIdentification:
    async def test_identify_ingredients_from_image_returns_dict(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """identify_ingredients_from_image should return a dict."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            json.dumps(SAMPLE_IMAGE_RESULT)
        )
        result = await openai_service.identify_ingredients_from_image("base64data==")
        assert isinstance(result, dict)
        assert "ingredients" in result
        assert "tomato" in result["ingredients"]

    async def test_identify_ingredients_none_content_returns_empty_dict(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """identify_ingredients_from_image should return {} when content is None."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            None
        )
        result = await openai_service.identify_ingredients_from_image("base64data==")
        assert isinstance(result, dict)
        assert len(result) == 0

    async def test_identify_ingredients_sends_image_url_block(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """identify_ingredients_from_image should send an image_url content block."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            json.dumps(SAMPLE_IMAGE_RESULT)
        )
        await openai_service.identify_ingredients_from_image("abc123")
        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) == 1
        content = messages[0]["content"]
        assert content[0]["type"] == "image_url"
        assert "abc123" in content[0]["image_url"]["url"]


@pytest.mark.asyncio
class TestOpenAISubstitutions:
    async def test_suggest_substitutions_returns_list(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """suggest_substitutions should return a list of substitution dicts."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            json.dumps(SAMPLE_SUBSTITUTIONS)
        )
        result = await openai_service.suggest_substitutions(
            original_ingredient="butter",
            dietary_restrictions=["dairy-free"],
            available_ingredients=["coconut oil", "margarine"],
        )
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["substitute"] == "coconut oil"

    async def test_suggest_substitutions_handles_wrapped_json(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """suggest_substitutions should unwrap {substitutions: [...]} envelope."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            json.dumps({"substitutions": SAMPLE_SUBSTITUTIONS})
        )
        result = await openai_service.suggest_substitutions(
            original_ingredient="butter",
            dietary_restrictions=[],
            available_ingredients=[],
        )
        assert isinstance(result, list)
        assert len(result) == 2

    async def test_suggest_substitutions_none_content_falls_back(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """suggest_substitutions should treat None content as empty list."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            None
        )
        result = await openai_service.suggest_substitutions(
            original_ingredient="butter",
            dietary_restrictions=[],
            available_ingredients=[],
        )
        assert isinstance(result, list)
        assert len(result) == 0


@pytest.mark.asyncio
class TestOpenAIVoiceParsing:
    async def test_parse_voice_input_returns_dict(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """parse_voice_input should return a parsed ingredient dict."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            json.dumps(SAMPLE_VOICE_PARSE)
        )
        result = await openai_service.parse_voice_input(
            "two cups of flour and three eggs"
        )
        assert isinstance(result, dict)
        assert "ingredients" in result
        assert len(result["ingredients"]) == 2
        assert result["ingredients"][0]["name"] == "flour"

    async def test_parse_voice_input_none_content_returns_empty_dict(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """parse_voice_input should return {} when content is None."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            None
        )
        result = await openai_service.parse_voice_input("some text")
        assert isinstance(result, dict)
        assert len(result) == 0

    async def test_parse_voice_input_uses_json_response_format(
        self, openai_service: Any, mock_openai_client: AsyncMock
    ) -> None:
        """parse_voice_input should request response_format json_object."""
        mock_openai_client.chat.completions.create.return_value = _make_openai_response(
            json.dumps(SAMPLE_VOICE_PARSE)
        )
        await openai_service.parse_voice_input("some text")
        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}
        assert call_kwargs["model"] == "gpt-test"
