"""Unit tests for AnthropicService.

These tests mock anthropic.AsyncAnthropic to verify that AnthropicService
correctly builds prompts, calls the Anthropic API, and parses responses
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
        {
            "name": "pasta",
            "quantity": "200",
            "unit": "g",
            "is_optional": False,
            "substitution_notes": "",
        },
        {
            "name": "tomatoes",
            "quantity": "3",
            "unit": "whole",
            "is_optional": False,
            "substitution_notes": "",
        },
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


def _make_anthropic_response(text: str) -> MagicMock:
    """Build a mock Anthropic response with response.content[0].text."""
    block = MagicMock()
    block.text = text
    response = MagicMock()
    response.content = [block]
    return response


@pytest.fixture
def mock_anthropic_client() -> AsyncMock:
    """Create a mock AsyncAnthropic client."""
    client = AsyncMock()
    client.messages = AsyncMock()
    client.messages.create = AsyncMock()
    return client


@pytest.fixture
def anthropic_service(mock_anthropic_client: AsyncMock) -> Any:
    """Create an AnthropicService with a mocked client."""
    with (
        patch("app.config.settings.anthropic_api_key", "test-key"),
        patch("app.config.settings.anthropic_model", "claude-test"),
        patch("anthropic.AsyncAnthropic", return_value=mock_anthropic_client),
    ):
        from app.services.ai.anthropic import AnthropicService

        service = AnthropicService()
    service.client = mock_anthropic_client
    return service


@pytest.mark.asyncio
class TestAnthropicRecipeGeneration:
    async def test_generate_recipes_returns_list(
        self, anthropic_service: Any, mock_anthropic_client: AsyncMock
    ) -> None:
        """generate_recipes should return a list when API returns a JSON array."""
        mock_anthropic_client.messages.create.return_value = _make_anthropic_response(
            json.dumps([SAMPLE_RECIPE])
        )
        result = await anthropic_service.generate_recipes(
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
        self, anthropic_service: Any, mock_anthropic_client: AsyncMock
    ) -> None:
        """generate_recipes should unwrap {recipes: [...]} envelope."""
        mock_anthropic_client.messages.create.return_value = _make_anthropic_response(
            json.dumps({"recipes": [SAMPLE_RECIPE]})
        )
        result = await anthropic_service.generate_recipes(
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

    async def test_generate_recipes_passes_correct_model_and_max_tokens(
        self, anthropic_service: Any, mock_anthropic_client: AsyncMock
    ) -> None:
        """generate_recipes should pass model and max_tokens=4096."""
        mock_anthropic_client.messages.create.return_value = _make_anthropic_response(
            json.dumps([])
        )
        await anthropic_service.generate_recipes(
            prompt="test",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
        )
        mock_anthropic_client.messages.create.assert_called_once()
        call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        assert call_kwargs["model"] == "claude-test"
        assert call_kwargs["max_tokens"] == 4096

    async def test_generate_recipes_empty_list(
        self, anthropic_service: Any, mock_anthropic_client: AsyncMock
    ) -> None:
        """generate_recipes should handle an empty list response."""
        mock_anthropic_client.messages.create.return_value = _make_anthropic_response(
            json.dumps([])
        )
        result = await anthropic_service.generate_recipes(
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
class TestAnthropicImageIdentification:
    async def test_identify_ingredients_from_image_returns_dict(
        self, anthropic_service: Any, mock_anthropic_client: AsyncMock
    ) -> None:
        """identify_ingredients_from_image should return a dict of ingredients."""
        mock_anthropic_client.messages.create.return_value = _make_anthropic_response(
            json.dumps(SAMPLE_IMAGE_RESULT)
        )
        result = await anthropic_service.identify_ingredients_from_image("base64data==")
        assert isinstance(result, dict)
        assert "ingredients" in result
        assert "tomato" in result["ingredients"]

    async def test_identify_ingredients_passes_correct_max_tokens(
        self, anthropic_service: Any, mock_anthropic_client: AsyncMock
    ) -> None:
        """identify_ingredients_from_image should use max_tokens=2048."""
        mock_anthropic_client.messages.create.return_value = _make_anthropic_response(
            json.dumps(SAMPLE_IMAGE_RESULT)
        )
        await anthropic_service.identify_ingredients_from_image("base64data==")
        call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 2048
        assert call_kwargs["model"] == "claude-test"

    async def test_identify_ingredients_sends_image_block(
        self, anthropic_service: Any, mock_anthropic_client: AsyncMock
    ) -> None:
        """identify_ingredients_from_image should send an image content block."""
        mock_anthropic_client.messages.create.return_value = _make_anthropic_response(
            json.dumps(SAMPLE_IMAGE_RESULT)
        )
        await anthropic_service.identify_ingredients_from_image("abc123")
        call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        messages = call_kwargs["messages"]
        assert len(messages) == 1
        content = messages[0]["content"]
        assert content[0]["type"] == "image"
        assert content[0]["source"]["data"] == "abc123"
        assert content[0]["source"]["type"] == "base64"
        assert content[0]["source"]["media_type"] == "image/jpeg"


@pytest.mark.asyncio
class TestAnthropicSubstitutions:
    async def test_suggest_substitutions_returns_list(
        self, anthropic_service: Any, mock_anthropic_client: AsyncMock
    ) -> None:
        """suggest_substitutions should return a list of substitution dicts."""
        mock_anthropic_client.messages.create.return_value = _make_anthropic_response(
            json.dumps(SAMPLE_SUBSTITUTIONS)
        )
        result = await anthropic_service.suggest_substitutions(
            original_ingredient="butter",
            dietary_restrictions=["dairy-free"],
            available_ingredients=["coconut oil", "margarine"],
        )
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["substitute"] == "coconut oil"

    async def test_suggest_substitutions_handles_wrapped_json(
        self, anthropic_service: Any, mock_anthropic_client: AsyncMock
    ) -> None:
        """suggest_substitutions should unwrap {substitutions: [...]} envelope."""
        mock_anthropic_client.messages.create.return_value = _make_anthropic_response(
            json.dumps({"substitutions": SAMPLE_SUBSTITUTIONS})
        )
        result = await anthropic_service.suggest_substitutions(
            original_ingredient="butter",
            dietary_restrictions=[],
            available_ingredients=[],
        )
        assert isinstance(result, list)
        assert len(result) == 2

    async def test_suggest_substitutions_passes_correct_max_tokens(
        self, anthropic_service: Any, mock_anthropic_client: AsyncMock
    ) -> None:
        """suggest_substitutions should use max_tokens=1024."""
        mock_anthropic_client.messages.create.return_value = _make_anthropic_response(
            json.dumps(SAMPLE_SUBSTITUTIONS)
        )
        await anthropic_service.suggest_substitutions(
            original_ingredient="butter",
            dietary_restrictions=[],
            available_ingredients=[],
        )
        call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 1024


@pytest.mark.asyncio
class TestAnthropicVoiceParsing:
    async def test_parse_voice_input_returns_dict(
        self, anthropic_service: Any, mock_anthropic_client: AsyncMock
    ) -> None:
        """parse_voice_input should return a parsed ingredient dict."""
        mock_anthropic_client.messages.create.return_value = _make_anthropic_response(
            json.dumps(SAMPLE_VOICE_PARSE)
        )
        result = await anthropic_service.parse_voice_input("two cups of flour and three eggs")
        assert isinstance(result, dict)
        assert "ingredients" in result
        assert len(result["ingredients"]) == 2
        assert result["ingredients"][0]["name"] == "flour"

    async def test_parse_voice_input_passes_correct_max_tokens(
        self, anthropic_service: Any, mock_anthropic_client: AsyncMock
    ) -> None:
        """parse_voice_input should use max_tokens=1024."""
        mock_anthropic_client.messages.create.return_value = _make_anthropic_response(
            json.dumps(SAMPLE_VOICE_PARSE)
        )
        await anthropic_service.parse_voice_input("some text")
        call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
        assert call_kwargs["max_tokens"] == 1024
        assert call_kwargs["model"] == "claude-test"
