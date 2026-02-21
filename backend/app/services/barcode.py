from __future__ import annotations

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.ingredient import Ingredient
from app.schemas.ingredient import BarcodeScanResult, IngredientResponse


async def lookup_barcode(barcode: str, db: AsyncSession) -> BarcodeScanResult | None:
    result = await db.execute(select(Ingredient).where(Ingredient.barcode == barcode))
    existing = result.scalar_one_or_none()
    if existing:
        return BarcodeScanResult(
            barcode=barcode,
            ingredient=IngredientResponse.model_validate(existing),
            product_name=existing.name,
            brand=existing.brand,
            found=True,
        )

    product_data = await _fetch_openfoodfacts(barcode)
    if product_data is None:
        return None

    ingredient = Ingredient(
        name=product_data.get("product_name", "Unknown"),
        barcode=barcode,
        brand=product_data.get("brands"),
        category=product_data.get("categories"),
        image_url=product_data.get("image_url"),
        nutrition_info=str(product_data.get("nutriments", {})),
        common_allergens=product_data.get("allergens"),
    )
    db.add(ingredient)
    await db.flush()

    return BarcodeScanResult(
        barcode=barcode,
        ingredient=IngredientResponse.model_validate(ingredient),
        product_name=ingredient.name,
        brand=ingredient.brand,
        found=True,
    )


async def _fetch_openfoodfacts(barcode: str) -> dict | None:
    url = f"{settings.openfoodfacts_api_url}/product/{barcode}"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(url)
            if response.status_code != 200:
                return None
            data = response.json()
            if data.get("status") != 1:
                return None
            return data.get("product")
        except httpx.HTTPError:
            return None
