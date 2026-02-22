"""Unit tests for the ingredient detection service.

These tests mock the AI service to verify that detect_ingredients_from_image
correctly processes AI results and builds CameraScanResult objects,
including the default confidence score fallback behavior.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.ingredient import CameraScanResult
from app.services.ingredient import detect_ingredients_from_image


@pytest.mark.asyncio
class TestDetectIngredientsFromImage:
    @patch("app.services.ingredient.get_ai_service")
    async def test_with_ingredients_and_confidence_scores(
        self, mock_get_ai_service: MagicMock
    ) -> None:
        mock_ai = AsyncMock()
        mock_ai.identify_ingredients_from_image.return_value = {
            "ingredients": ["tomato", "onion", "garlic"],
            "confidence_scores": {"tomato": 0.95, "onion": 0.88, "garlic": 0.72},
        }
        mock_get_ai_service.return_value = mock_ai

        result = await detect_ingredients_from_image("base64encodedimage")

        assert isinstance(result, CameraScanResult)
        assert result.detected_ingredients == ["tomato", "onion", "garlic"]
        assert result.confidence_scores == {"tomato": 0.95, "onion": 0.88, "garlic": 0.72}

        mock_ai.identify_ingredients_from_image.assert_called_once_with("base64encodedimage")

    @patch("app.services.ingredient.get_ai_service")
    async def test_with_ingredients_but_no_confidence_scores(
        self, mock_get_ai_service: MagicMock
    ) -> None:
        """When confidence_scores is empty, all ingredients default to 0.8."""
        mock_ai = AsyncMock()
        mock_ai.identify_ingredients_from_image.return_value = {
            "ingredients": ["pasta", "cheese"],
            "confidence_scores": {},
        }
        mock_get_ai_service.return_value = mock_ai

        result = await detect_ingredients_from_image("base64data")

        assert isinstance(result, CameraScanResult)
        assert result.detected_ingredients == ["pasta", "cheese"]
        assert result.confidence_scores == {"pasta": 0.8, "cheese": 0.8}

    @patch("app.services.ingredient.get_ai_service")
    async def test_with_ingredients_and_missing_confidence_key(
        self, mock_get_ai_service: MagicMock
    ) -> None:
        """When confidence_scores key is absent from result, default to 0.8."""
        mock_ai = AsyncMock()
        mock_ai.identify_ingredients_from_image.return_value = {
            "ingredients": ["rice", "beans"],
        }
        mock_get_ai_service.return_value = mock_ai

        result = await detect_ingredients_from_image("base64data")

        assert isinstance(result, CameraScanResult)
        assert result.detected_ingredients == ["rice", "beans"]
        assert result.confidence_scores == {"rice": 0.8, "beans": 0.8}

    @patch("app.services.ingredient.get_ai_service")
    async def test_with_empty_ingredients_list(self, mock_get_ai_service: MagicMock) -> None:
        mock_ai = AsyncMock()
        mock_ai.identify_ingredients_from_image.return_value = {
            "ingredients": [],
            "confidence_scores": {},
        }
        mock_get_ai_service.return_value = mock_ai

        result = await detect_ingredients_from_image("base64empty")

        assert isinstance(result, CameraScanResult)
        assert result.detected_ingredients == []
        assert result.confidence_scores == {}

    @patch("app.services.ingredient.get_ai_service")
    async def test_get_ai_service_is_called(self, mock_get_ai_service: MagicMock) -> None:
        """Verify that get_ai_service is called and its return value is used."""
        mock_ai = AsyncMock()
        mock_ai.identify_ingredients_from_image.return_value = {
            "ingredients": ["salt"],
            "confidence_scores": {"salt": 0.99},
        }
        mock_get_ai_service.return_value = mock_ai

        await detect_ingredients_from_image("test_image_data")

        mock_get_ai_service.assert_called_once()
        mock_ai.identify_ingredients_from_image.assert_called_once_with("test_image_data")
