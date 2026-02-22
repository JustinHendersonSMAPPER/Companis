"""Unit tests for ClaudeLocalService.

These tests mock asyncio.create_subprocess_exec to verify that
ClaudeLocalService correctly invokes the Claude CLI, parses JSON
from its output, and handles errors without requiring the CLI to
be installed.
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

SAMPLE_RECIPE = {
    "title": "Garlic Tomato Pasta",
    "description": "Simple pasta dish.",
    "instructions": "1. Boil pasta. 2. Add sauce.",
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
    ],
}

SAMPLE_SUBSTITUTIONS = [
    {"substitute": "coconut oil", "notes": "Good for baking", "ratio": "1:1"},
]

SAMPLE_VOICE_PARSE = {
    "ingredients": [
        {"name": "flour", "quantity": 2, "unit": "cups"},
        {"name": "eggs", "quantity": 3, "unit": None},
    ]
}

SAMPLE_IMAGE_RESULT = {
    "ingredients": ["tomato", "onion"],
    "confidence_scores": {"tomato": 0.95, "onion": 0.87},
}


def _make_subprocess_mock(
    stdout: str, returncode: int = 0, stderr: str = ""
) -> AsyncMock:
    """Create a mock subprocess that returns the given stdout/stderr."""
    proc_mock = AsyncMock()
    proc_mock.communicate.return_value = (stdout.encode(), stderr.encode())
    proc_mock.returncode = returncode
    return proc_mock


@pytest.fixture
def claude_service() -> Any:
    """Create a ClaudeLocalService instance."""
    from app.services.ai.claude_local import ClaudeLocalService

    return ClaudeLocalService()


# ---------------------------------------------------------------------------
# settings.claude_local_model usage test
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestClaudeLocalModelFromSettings:
    @patch("asyncio.create_subprocess_exec")
    async def test_uses_settings_model_not_hardcoded(
        self, mock_exec: AsyncMock, claude_service: Any, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """_run_claude should use settings.claude_local_model, not a hardcoded value."""
        monkeypatch.setattr(
            "app.services.ai.claude_local.settings",
            type("FakeSettings", (), {"claude_local_model": "test-model-xyz"})(),
        )
        proc = _make_subprocess_mock("output")
        mock_exec.return_value = proc
        await claude_service._run_claude("test prompt")
        call_args = mock_exec.call_args[0]
        assert "test-model-xyz" in call_args


# ---------------------------------------------------------------------------
# _extract_json tests
# ---------------------------------------------------------------------------


class TestExtractJson:
    def test_extract_json_array(self, claude_service: Any) -> None:
        """_extract_json should extract a JSON array from surrounding text."""
        text = 'Here are some recipes: [{"title": "test"}] done.'
        result = claude_service._extract_json(text)
        assert isinstance(result, list)
        assert result[0]["title"] == "test"

    def test_extract_json_object(self, claude_service: Any) -> None:
        """_extract_json should extract a JSON object when no array is present."""
        text = 'Response: {"key": "value"} end.'
        result = claude_service._extract_json(text)
        assert isinstance(result, dict)
        assert result["key"] == "value"

    def test_extract_json_no_json_raises(self, claude_service: Any) -> None:
        """_extract_json should raise ValueError when no JSON is found."""
        with pytest.raises(ValueError, match="No JSON found"):
            claude_service._extract_json("no json here")

    def test_extract_json_pure_array(self, claude_service: Any) -> None:
        """_extract_json should handle text that is a pure JSON array."""
        text = json.dumps([SAMPLE_RECIPE])
        result = claude_service._extract_json(text)
        assert isinstance(result, list)
        assert len(result) == 1

    def test_extract_json_prefers_array_over_object(
        self, claude_service: Any
    ) -> None:
        """_extract_json should find [ before { when both exist."""
        text = 'prefix [{"a": 1}] suffix'
        result = claude_service._extract_json(text)
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# _run_claude tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestRunClaude:
    @patch("asyncio.create_subprocess_exec")
    async def test_run_claude_success(
        self, mock_exec: AsyncMock, claude_service: Any
    ) -> None:
        """_run_claude should return stripped stdout on success."""
        mock_exec.return_value = _make_subprocess_mock("  output text  ")
        result = await claude_service._run_claude("test prompt")
        assert result == "output text"
        mock_exec.assert_called_once()

    @patch("asyncio.create_subprocess_exec")
    async def test_run_claude_sends_prompt_via_stdin(
        self, mock_exec: AsyncMock, claude_service: Any
    ) -> None:
        """_run_claude should pass the prompt as stdin input."""
        proc = _make_subprocess_mock("ok")
        mock_exec.return_value = proc
        await claude_service._run_claude("my prompt text")
        proc.communicate.assert_called_once_with(input=b"my prompt text")

    @patch("asyncio.create_subprocess_exec")
    async def test_run_claude_failure_raises(
        self, mock_exec: AsyncMock, claude_service: Any
    ) -> None:
        """_run_claude should raise RuntimeError when the process fails."""
        mock_exec.return_value = _make_subprocess_mock(
            "", returncode=1, stderr="CLI error"
        )
        with pytest.raises(RuntimeError, match="Claude local CLI failed"):
            await claude_service._run_claude("test prompt")


# ---------------------------------------------------------------------------
# generate_recipes tests (mock _run_claude to isolate from _extract_json)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestClaudeLocalGenerateRecipes:
    async def test_generate_recipes_returns_list(
        self, claude_service: Any
    ) -> None:
        """generate_recipes should return a list of recipe dicts."""
        with patch.object(
            claude_service, "_run_claude", return_value=json.dumps([SAMPLE_RECIPE])
        ):
            result = await claude_service.generate_recipes(
                prompt="pasta recipe",
                available_ingredients=["pasta", "tomatoes"],
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

    async def test_generate_recipes_handles_wrapped_json(
        self, claude_service: Any
    ) -> None:
        """generate_recipes should unwrap {recipes: [...]} envelope."""
        with patch.object(
            claude_service,
            "_run_claude",
            return_value=json.dumps({"recipes": [SAMPLE_RECIPE]}),
        ):
            result = await claude_service.generate_recipes(
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

    async def test_generate_recipes_with_surrounding_text(
        self, claude_service: Any
    ) -> None:
        """generate_recipes should extract JSON even with surrounding text."""
        raw = f"Here are the recipes:\n{json.dumps([SAMPLE_RECIPE])}\nEnjoy!"
        with patch.object(claude_service, "_run_claude", return_value=raw):
            result = await claude_service.generate_recipes(
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

    async def test_generate_recipes_empty_list(
        self, claude_service: Any
    ) -> None:
        """generate_recipes should handle an empty list response."""
        with patch.object(claude_service, "_run_claude", return_value="[]"):
            result = await claude_service.generate_recipes(
                prompt="exotic",
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


# ---------------------------------------------------------------------------
# suggest_substitutions tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestClaudeLocalSubstitutions:
    async def test_suggest_substitutions_returns_list(
        self, claude_service: Any
    ) -> None:
        """suggest_substitutions should return a list of substitution dicts."""
        with patch.object(
            claude_service,
            "_run_claude",
            return_value=json.dumps(SAMPLE_SUBSTITUTIONS),
        ):
            result = await claude_service.suggest_substitutions(
                original_ingredient="butter",
                dietary_restrictions=["dairy-free"],
                available_ingredients=["coconut oil"],
            )
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["substitute"] == "coconut oil"

    async def test_suggest_substitutions_handles_wrapped_json(
        self, claude_service: Any
    ) -> None:
        """suggest_substitutions should unwrap {substitutions: [...]} envelope."""
        with patch.object(
            claude_service,
            "_run_claude",
            return_value=json.dumps({"substitutions": SAMPLE_SUBSTITUTIONS}),
        ):
            result = await claude_service.suggest_substitutions(
                original_ingredient="butter",
                dietary_restrictions=[],
                available_ingredients=[],
            )
        assert isinstance(result, list)
        assert len(result) == 1


# ---------------------------------------------------------------------------
# parse_voice_input tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestClaudeLocalVoiceParsing:
    async def test_parse_voice_input_returns_dict(
        self, claude_service: Any
    ) -> None:
        """parse_voice_input should return a parsed ingredient dict."""
        with (
            patch.object(
                claude_service,
                "_run_claude",
                return_value=json.dumps(SAMPLE_VOICE_PARSE),
            ),
            patch.object(
                claude_service,
                "_extract_json",
                return_value=SAMPLE_VOICE_PARSE,
            ),
        ):
            result = await claude_service.parse_voice_input("two cups of flour")
        assert isinstance(result, dict)
        assert "ingredients" in result
        assert len(result["ingredients"]) == 2
        assert result["ingredients"][0]["name"] == "flour"


# ---------------------------------------------------------------------------
# identify_ingredients_from_image tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestClaudeLocalImageIdentification:
    async def test_identify_ingredients_from_image_returns_dict(
        self, claude_service: Any
    ) -> None:
        """identify_ingredients_from_image should return a dict of ingredients."""
        with (
            patch.object(
                claude_service,
                "_run_claude",
                return_value=json.dumps(SAMPLE_IMAGE_RESULT),
            ),
            patch.object(
                claude_service,
                "_extract_json",
                return_value=SAMPLE_IMAGE_RESULT,
            ),
        ):
            result = await claude_service.identify_ingredients_from_image("base64data")
        assert isinstance(result, dict)
        assert "ingredients" in result
        assert "tomato" in result["ingredients"]

    async def test_identify_ingredients_includes_base64_length_in_prompt(
        self, claude_service: Any
    ) -> None:
        """identify_ingredients_from_image should mention base64 length in prompt."""
        mock_run = AsyncMock(return_value=json.dumps(SAMPLE_IMAGE_RESULT))
        with patch.object(claude_service, "_run_claude", mock_run):
            await claude_service.identify_ingredients_from_image("abcdef")
        prompt_arg = mock_run.call_args[0][0]
        assert "length: 6 chars" in prompt_arg
