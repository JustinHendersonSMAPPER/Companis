from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.config import AIProvider, settings
from app.models.user import User
from app.schemas.ingredient import CameraScanRequest, CameraScanResult

router = APIRouter()


@router.get("/providers")
async def get_providers(
    _current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    return {
        "current_provider": settings.ai_provider.value,
        "available_providers": [p.value for p in AIProvider],
    }


@router.post("/identify-ingredients", response_model=CameraScanResult)
async def identify_ingredients(
    scan_data: CameraScanRequest,
    _current_user: User = Depends(get_current_user),
) -> CameraScanResult:
    from app.services.ingredient import detect_ingredients_from_image

    return await detect_ingredients_from_image(scan_data.image_base64)


@router.post("/parse-voice-input")
async def parse_voice_input(
    transcript: str,
    _current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    from app.services.ai import get_ai_service

    ai_service = get_ai_service()
    return await ai_service.parse_voice_input(transcript)


@router.post("/suggest-substitutions")
async def suggest_substitutions(
    ingredient: str,
    dietary_restrictions: list[str] | None = None,
    available_ingredients: list[str] | None = None,
    _current_user: User = Depends(get_current_user),
) -> list[dict[str, str]]:
    from app.services.ai import get_ai_service

    ai_service = get_ai_service()
    return await ai_service.suggest_substitutions(
        original_ingredient=ingredient,
        dietary_restrictions=dietary_restrictions or [],
        available_ingredients=available_ingredients or [],
    )
