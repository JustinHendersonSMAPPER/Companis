from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class RecipeIngredientSchema(BaseModel):
    name: str
    quantity: float | None = None
    unit: str | None = None
    is_optional: bool = False
    substitution_notes: str | None = None
    is_available: bool | None = None
    has_substitution: bool | None = None


class RecipeCreate(BaseModel):
    title: str = Field(max_length=500)
    description: str | None = None
    instructions: str
    cuisine: str | None = None
    meal_type: str | None = None
    prep_time_minutes: int | None = None
    cook_time_minutes: int | None = None
    servings: int | None = None
    difficulty: str | None = None
    dietary_tags: str | None = None
    calorie_estimate: int | None = None
    ingredients: list[RecipeIngredientSchema] = []


class RecipeResponse(BaseModel):
    id: str
    title: str
    description: str | None
    instructions: str
    cuisine: str | None
    meal_type: str | None
    prep_time_minutes: int | None
    cook_time_minutes: int | None
    servings: int | None
    difficulty: str | None
    image_url: str | None
    source: str
    dietary_tags: str | None
    calorie_estimate: int | None
    created_at: datetime
    recipe_ingredients: list[RecipeIngredientSchema] = []
    average_rating: float | None = None
    user_rating: int | None = None
    is_favorite: bool = False

    model_config = {"from_attributes": True}


class RecipeSearchRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=1000)
    max_results: int = Field(default=5, ge=1, le=20)
    prefer_available_ingredients: bool = True
    max_prep_time_minutes: int | None = None
    cuisine: str | None = None
    dietary_filter: list[str] = []


class RecipeSearchResponse(BaseModel):
    recipes: list[RecipeResponse]
    missing_ingredients: dict[str, list[str]] = {}
    substitutions: dict[str, list[SubstitutionSuggestion]] = {}


class SubstitutionSuggestion(BaseModel):
    original_ingredient: str
    substitute: str
    notes: str | None = None
    ratio: str | None = None


class RecipeRatingCreate(BaseModel):
    score: int = Field(ge=1, le=5)
    review: str | None = None


class RecipeRatingResponse(BaseModel):
    id: str
    recipe_id: str
    user_id: str
    score: int
    review: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedFavoritesResponse(BaseModel):
    items: list[RecipeResponse]
    total: int
    limit: int
    offset: int
