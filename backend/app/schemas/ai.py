from __future__ import annotations

from pydantic import BaseModel


class VoiceInputRequest(BaseModel):
    transcript: str


class VoiceInputResponse(BaseModel):
    ingredients: list[ParsedIngredient]


class ParsedIngredient(BaseModel):
    name: str
    quantity: float | None = None
    unit: str | None = None


class SubstitutionRequest(BaseModel):
    ingredient: str
    dietary_restrictions: list[str] = []
    available_ingredients: list[str] = []


class SubstitutionResponse(BaseModel):
    substitute: str
    notes: str | None = None
    ratio: str | None = None
