from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CookingHistoryCreate(BaseModel):
    recipe_id: str
    servings_made: int | None = Field(default=None, ge=1)
    notes: str | None = None


class CookingHistoryResponse(BaseModel):
    id: str
    user_id: str
    recipe_id: str
    household_id: str
    servings_made: int | None
    notes: str | None
    cooked_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedCookingHistoryResponse(BaseModel):
    items: list[CookingHistoryResponse]
    total: int
    limit: int
    offset: int
