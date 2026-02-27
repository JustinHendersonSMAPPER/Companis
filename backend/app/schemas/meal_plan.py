from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class MealPlanCreate(BaseModel):
    recipe_id: str
    meal_date: datetime
    meal_type: str = Field(max_length=20)  # breakfast, lunch, dinner, snack
    servings: int = Field(default=2, ge=1)
    notes: str | None = None


class MealPlanUpdate(BaseModel):
    recipe_id: str | None = None
    meal_date: datetime | None = None
    meal_type: str | None = Field(default=None, max_length=20)
    servings: int | None = Field(default=None, ge=1)
    notes: str | None = None


class MealPlanResponse(BaseModel):
    id: str
    household_id: str
    recipe_id: str
    meal_date: datetime
    meal_type: str
    servings: int
    notes: str | None
    created_by_user_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class MealPlanDateRangeRequest(BaseModel):
    start_date: datetime
    end_date: datetime
