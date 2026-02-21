from __future__ import annotations

from app.schemas.ingredient import CameraScanResult
from app.services.ai import get_ai_service


async def detect_ingredients_from_image(image_base64: str) -> CameraScanResult:
    ai_service = get_ai_service()
    result = await ai_service.identify_ingredients_from_image(image_base64)

    ingredients = result.get("ingredients", [])
    confidence_scores = result.get("confidence_scores", {})

    if not confidence_scores and ingredients:
        confidence_scores = dict.fromkeys(ingredients, 0.8)

    return CameraScanResult(
        detected_ingredients=ingredients,
        confidence_scores=confidence_scores,
    )
