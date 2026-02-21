from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ShoppingCartCreate(BaseModel):
    name: str = Field(default="My Shopping List", max_length=255)


class ShoppingCartResponse(BaseModel):
    id: str
    household_id: str
    name: str
    is_active: bool
    created_at: datetime
    items: list[ShoppingCartItemResponse] = []

    model_config = {"from_attributes": True}


class ShoppingCartItemAdd(BaseModel):
    ingredient_id: str | None = None
    name: str = Field(max_length=255)
    quantity: float | None = None
    unit: str | None = None
    notes: str | None = None
    added_from_recipe_id: str | None = None


class ShoppingCartItemResponse(BaseModel):
    id: str
    name: str
    quantity: float | None
    unit: str | None
    notes: str | None
    is_purchased: bool
    added_from_recipe_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ShoppingCartItemUpdate(BaseModel):
    quantity: float | None = None
    unit: str | None = None
    notes: str | None = None
    is_purchased: bool | None = None


class AddMissingIngredientsRequest(BaseModel):
    recipe_id: str
    ingredient_names: list[str]
