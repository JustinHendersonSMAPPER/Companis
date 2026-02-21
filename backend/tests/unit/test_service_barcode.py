"""Unit tests for the barcode lookup service.

These tests mock httpx.AsyncClient for OpenFoodFacts API calls and
AsyncSession for database operations, verifying that barcode lookup
correctly handles existing ingredients, external API results, and
various failure modes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.barcode import _fetch_openfoodfacts, lookup_barcode


# ---------------------------------------------------------------------------
# _fetch_openfoodfacts tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestFetchOpenFoodFacts:
    @patch("app.services.barcode.settings")
    @patch("httpx.AsyncClient")
    async def test_successful_response(
        self, mock_client_cls: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.openfoodfacts_api_url = "https://world.openfoodfacts.org/api/v2"

        product_data = {
            "product_name": "Organic Pasta",
            "brands": "TestBrand",
            "categories": "Pasta",
            "image_url": "https://example.com/pasta.jpg",
            "nutriments": {"energy": 350},
            "allergens": "gluten",
        }
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 1, "product": product_data}

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await _fetch_openfoodfacts("1234567890123")

        assert result is not None
        assert result["product_name"] == "Organic Pasta"
        assert result["brands"] == "TestBrand"
        assert result["categories"] == "Pasta"

        mock_client_instance.get.assert_called_once_with(
            "https://world.openfoodfacts.org/api/v2/product/1234567890123"
        )

    @patch("app.services.barcode.settings")
    @patch("httpx.AsyncClient")
    async def test_non_200_status(
        self, mock_client_cls: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.openfoodfacts_api_url = "https://world.openfoodfacts.org/api/v2"

        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await _fetch_openfoodfacts("0000000000000")

        assert result is None

    @patch("app.services.barcode.settings")
    @patch("httpx.AsyncClient")
    async def test_status_not_1_in_response(
        self, mock_client_cls: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.openfoodfacts_api_url = "https://world.openfoodfacts.org/api/v2"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": 0, "product": None}

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = mock_response
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await _fetch_openfoodfacts("9999999999999")

        assert result is None

    @patch("app.services.barcode.settings")
    @patch("httpx.AsyncClient")
    async def test_http_error_exception(
        self, mock_client_cls: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.openfoodfacts_api_url = "https://world.openfoodfacts.org/api/v2"

        mock_client_instance = AsyncMock()
        mock_client_instance.get.side_effect = httpx.HTTPError("Connection refused")
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await _fetch_openfoodfacts("1111111111111")

        assert result is None


# ---------------------------------------------------------------------------
# lookup_barcode tests
# ---------------------------------------------------------------------------


def _make_mock_ingredient(
    ingredient_id: str = "ing-001",
    name: str = "Test Ingredient",
    barcode: str = "1234567890123",
    brand: str | None = "TestBrand",
    category: str | None = "TestCategory",
    image_url: str | None = "https://example.com/img.jpg",
    nutrition_info: str | None = "{}",
    common_allergens: str | None = None,
    description: str | None = None,
) -> MagicMock:
    """Create a mock Ingredient model instance."""
    ingredient = MagicMock()
    ingredient.id = ingredient_id
    ingredient.name = name
    ingredient.barcode = barcode
    ingredient.brand = brand
    ingredient.category = category
    ingredient.image_url = image_url
    ingredient.nutrition_info = nutrition_info
    ingredient.common_allergens = common_allergens
    ingredient.description = description
    ingredient.created_at = datetime(2024, 1, 1, tzinfo=timezone.utc)
    return ingredient


@pytest.mark.asyncio
class TestLookupBarcode:
    async def test_ingredient_exists_in_db(self) -> None:
        """When an ingredient with the barcode exists in DB, return it directly."""
        existing = _make_mock_ingredient(
            name="Existing Pasta",
            barcode="1234567890123",
            brand="PastaBrand",
        )

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = existing

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        result = await lookup_barcode("1234567890123", mock_db)

        assert result is not None
        assert result.barcode == "1234567890123"
        assert result.product_name == "Existing Pasta"
        assert result.brand == "PastaBrand"
        assert result.found is True

    @patch("app.services.barcode.BarcodeScanResult")
    @patch("app.services.barcode.IngredientResponse")
    @patch("app.services.barcode._fetch_openfoodfacts")
    async def test_not_in_db_found_in_openfoodfacts(
        self,
        mock_fetch: AsyncMock,
        mock_ingredient_response: MagicMock,
        mock_barcode_result: MagicMock,
    ) -> None:
        """When not in DB but found on OpenFoodFacts, create ingredient and return."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = MagicMock()
        mock_db.execute = AsyncMock(return_value=mock_result)
        mock_db.add = MagicMock()
        mock_db.flush = AsyncMock()

        mock_fetch.return_value = {
            "product_name": "API Pasta",
            "brands": "ApiBrand",
            "categories": "Pasta",
            "image_url": "https://example.com/api-pasta.jpg",
            "nutriments": {"energy": 350},
            "allergens": "gluten",
        }

        mock_validated = MagicMock()
        mock_ingredient_response.model_validate.return_value = mock_validated
        mock_scan_result = MagicMock()
        mock_barcode_result.return_value = mock_scan_result

        result = await lookup_barcode("5555555555555", mock_db)

        assert result is mock_scan_result
        mock_db.add.assert_called_once()
        mock_db.flush.assert_called_once()

    @patch("app.services.barcode._fetch_openfoodfacts")
    async def test_not_found_anywhere(self, mock_fetch: AsyncMock) -> None:
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        mock_fetch.return_value = None

        result = await lookup_barcode("0000000000000", mock_db)

        assert result is None
        mock_db.add.assert_not_called()
