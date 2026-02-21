"""Unit tests for OllamaService.

These tests mock the ollama.AsyncClient to verify that OllamaService
correctly builds prompts, calls the client, and parses responses
without requiring a live Ollama instance.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
from ollama._types import ChatResponse, Message


def _make_chat_response(content: str) -> ChatResponse:
    """Create a ChatResponse with the given JSON content string."""
    return ChatResponse(
        model="tinyllama",
        created_at="2024-01-01T00:00:00Z",
        done=True,
        message=Message(role="assistant", content=content),
    )


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
        {"name": "garlic", "quantity": "2", "unit": "cloves", "is_optional": False, "substitution_notes": ""},
        {"name": "olive oil", "quantity": "2", "unit": "tbsp", "is_optional": False, "substitution_notes": ""},
    ],
}

SAMPLE_SUBSTITUTIONS = [
    {"substitute": "coconut oil", "notes": "Good for baking, adds slight coconut flavor", "ratio": "1:1"},
    {"substitute": "margarine", "notes": "Direct replacement in most recipes", "ratio": "1:1"},
]

SAMPLE_VOICE_PARSE = {
    "ingredients": [
        {"name": "flour", "quantity": 2, "unit": "cups"},
        {"name": "eggs", "quantity": 3, "unit": None},
    ]
}


@pytest.fixture
def mock_ollama_client() -> AsyncMock:
    """Create a mock ollama.AsyncClient."""
    return AsyncMock()


@pytest.fixture
def ollama_service(mock_ollama_client: AsyncMock) -> Any:
    """Create an OllamaService with a mocked client."""
    with (
        patch("app.config.settings.ollama_base_url", "http://localhost:11434"),
        patch("app.config.settings.ollama_model", "tinyllama"),
        patch("ollama.AsyncClient", return_value=mock_ollama_client),
    ):
        from app.services.ai.ollama import OllamaService

        service = OllamaService()
    # Replace the client with our mock after construction
    service.client = mock_ollama_client
    return service


@pytest.mark.asyncio
class TestOllamaRecipeGeneration:
    async def test_generate_recipes_returns_list(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """generate_recipes should return a list of recipe dicts."""
        mock_ollama_client.chat.return_value = _make_chat_response(
            json.dumps([SAMPLE_RECIPE])
        )
        result = await ollama_service.generate_recipes(
            prompt="simple pasta recipe",
            available_ingredients=["pasta", "tomatoes", "garlic", "olive oil"],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
            max_prep_time=None,
            cuisine=None,
        )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Garlic Tomato Pasta"

    async def test_generate_recipes_calls_chat_with_json_format(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """generate_recipes should call ollama client.chat with format='json'."""
        mock_ollama_client.chat.return_value = _make_chat_response(json.dumps([]))
        await ollama_service.generate_recipes(
            prompt="dinner",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
            max_prep_time=None,
            cuisine=None,
        )
        mock_ollama_client.chat.assert_called_once()
        call_kwargs = mock_ollama_client.chat.call_args
        assert call_kwargs.kwargs.get("format") == "json" or call_kwargs[1].get("format") == "json"

    async def test_generate_recipes_with_dietary_preferences(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """generate_recipes should include dietary preferences in the prompt."""
        mock_ollama_client.chat.return_value = _make_chat_response(json.dumps([]))
        await ollama_service.generate_recipes(
            prompt="dinner recipe",
            available_ingredients=["rice", "vegetables", "tofu"],
            dietary_preferences=["vegan"],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
            max_prep_time=None,
            cuisine=None,
        )
        call_kwargs = mock_ollama_client.chat.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        prompt_text = messages[0]["content"]
        assert "vegan" in prompt_text

    async def test_generate_recipes_with_cuisine_filter(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """generate_recipes should include cuisine filter in the prompt."""
        mock_ollama_client.chat.return_value = _make_chat_response(json.dumps([]))
        await ollama_service.generate_recipes(
            prompt="dinner",
            available_ingredients=["chicken", "rice"],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
            max_prep_time=30,
            cuisine="Italian",
        )
        call_kwargs = mock_ollama_client.chat.call_args
        messages = call_kwargs.kwargs.get("messages") or call_kwargs[1].get("messages")
        prompt_text = messages[0]["content"]
        assert "Italian" in prompt_text
        assert "30 minutes" in prompt_text

    async def test_generate_recipes_handles_wrapped_json(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """generate_recipes should handle responses wrapped in {recipes: [...]}."""
        mock_ollama_client.chat.return_value = _make_chat_response(
            json.dumps({"recipes": [SAMPLE_RECIPE]})
        )
        result = await ollama_service.generate_recipes(
            prompt="pasta",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
            max_prep_time=None,
            cuisine=None,
        )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["title"] == "Garlic Tomato Pasta"


@pytest.mark.asyncio
class TestOllamaSubstitutions:
    async def test_suggest_substitutions_returns_list(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """suggest_substitutions should return a list of substitution dicts."""
        mock_ollama_client.chat.return_value = _make_chat_response(
            json.dumps(SAMPLE_SUBSTITUTIONS)
        )
        result = await ollama_service.suggest_substitutions(
            original_ingredient="butter",
            dietary_restrictions=["dairy-free"],
            available_ingredients=["coconut oil", "margarine", "olive oil"],
        )
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["substitute"] == "coconut oil"

    async def test_suggest_substitutions_empty_restrictions(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """suggest_substitutions should work with empty restrictions."""
        mock_ollama_client.chat.return_value = _make_chat_response(
            json.dumps([{"substitute": "almond flour", "notes": "Lower gluten", "ratio": "1:1"}])
        )
        result = await ollama_service.suggest_substitutions(
            original_ingredient="all-purpose flour",
            dietary_restrictions=[],
            available_ingredients=[],
        )
        assert isinstance(result, list)
        assert len(result) == 1

    async def test_suggest_substitutions_handles_wrapped_json(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """suggest_substitutions should handle {substitutions: [...]} wrapper."""
        mock_ollama_client.chat.return_value = _make_chat_response(
            json.dumps({"substitutions": SAMPLE_SUBSTITUTIONS})
        )
        result = await ollama_service.suggest_substitutions(
            original_ingredient="butter",
            dietary_restrictions=["dairy-free"],
            available_ingredients=[],
        )
        assert isinstance(result, list)
        assert len(result) == 2


@pytest.mark.asyncio
class TestOllamaVoiceParsing:
    async def test_parse_voice_input_returns_dict(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """parse_voice_input should return a parsed ingredient dict."""
        mock_ollama_client.chat.return_value = _make_chat_response(
            json.dumps(SAMPLE_VOICE_PARSE)
        )
        result = await ollama_service.parse_voice_input(
            "two cups of flour and three eggs"
        )
        assert isinstance(result, dict)
        assert "ingredients" in result
        assert len(result["ingredients"]) == 2
        assert result["ingredients"][0]["name"] == "flour"

    async def test_parse_complex_voice_input(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """parse_voice_input should handle complex multi-ingredient input."""
        complex_response = {
            "ingredients": [
                {"name": "chicken breast", "quantity": 0.5, "unit": "pound"},
                {"name": "onion", "quantity": 1, "unit": None},
                {"name": "soy sauce", "quantity": 0.25, "unit": "cup"},
            ]
        }
        mock_ollama_client.chat.return_value = _make_chat_response(
            json.dumps(complex_response)
        )
        result = await ollama_service.parse_voice_input(
            "I have half a pound of chicken breast, one onion, "
            "and about a quarter cup of soy sauce"
        )
        assert isinstance(result, dict)
        assert len(result["ingredients"]) == 3


@pytest.mark.asyncio
class TestOllamaResponseParsing:
    """Verify that OllamaService correctly parses various response formats."""

    async def test_recipe_response_has_expected_keys(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """Recipes returned should preserve all expected fields."""
        mock_ollama_client.chat.return_value = _make_chat_response(
            json.dumps([SAMPLE_RECIPE])
        )
        result = await ollama_service.generate_recipes(
            prompt="make me a quick soup",
            available_ingredients=["chicken broth", "noodles", "carrots"],
            dietary_preferences=[],
            health_goals=["low sodium"],
            family_dietary_notes=[],
            favorite_cuisines=["American"],
            max_results=1,
            max_prep_time=20,
            cuisine=None,
        )
        assert len(result) == 1
        recipe = result[0]
        assert "title" in recipe
        assert "ingredients" in recipe
        assert "instructions" in recipe
        assert "cuisine" in recipe

    async def test_empty_recipe_list(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """generate_recipes should handle an empty list response."""
        mock_ollama_client.chat.return_value = _make_chat_response(json.dumps([]))
        result = await ollama_service.generate_recipes(
            prompt="exotic dish",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
            max_prep_time=None,
            cuisine=None,
        )
        assert isinstance(result, list)
        assert len(result) == 0

    async def test_uses_correct_model(
        self, ollama_service: Any, mock_ollama_client: AsyncMock
    ) -> None:
        """OllamaService should call ollama with the configured model name."""
        mock_ollama_client.chat.return_value = _make_chat_response(json.dumps([]))
        await ollama_service.generate_recipes(
            prompt="test",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=1,
            max_prep_time=None,
            cuisine=None,
        )
        call_kwargs = mock_ollama_client.chat.call_args
        model_arg = call_kwargs.kwargs.get("model") or call_kwargs[1].get("model")
        assert model_arg == "tinyllama"
