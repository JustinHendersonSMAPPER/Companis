from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class IngredientCreate(BaseModel):
    name: str = Field(max_length=255)
    category: str | None = None
    barcode: str | None = None
    brand: str | None = None
    description: str | None = None
    common_allergens: str | None = None


class IngredientResponse(BaseModel):
    id: str
    name: str
    category: str | None
    barcode: str | None
    brand: str | None
    description: str | None
    image_url: str | None
    nutrition_info: str | None
    common_allergens: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class HouseholdIngredientAdd(BaseModel):
    ingredient_id: str | None = None
    name: str | None = Field(default=None, max_length=255)
    barcode: str | None = None
    quantity: float | None = None
    unit: str | None = None
    expiry_date: datetime | None = None
    source: str = "manual"


class HouseholdIngredientResponse(BaseModel):
    id: str
    household_id: str
    ingredient_id: str
    quantity: float | None
    unit: str | None
    expiry_date: datetime | None
    source: str
    created_at: datetime
    ingredient: IngredientResponse

    model_config = {"from_attributes": True}


class HouseholdIngredientUpdate(BaseModel):
    quantity: float | None = None
    unit: str | None = None
    expiry_date: datetime | None = None


class BarcodeScanResult(BaseModel):
    barcode: str
    ingredient: IngredientResponse | None
    product_name: str | None
    brand: str | None
    found: bool


class CameraScanRequest(BaseModel):
    image_base64: str


class CameraScanResult(BaseModel):
    detected_ingredients: list[str]
    confidence_scores: dict[str, float]


class PaginatedIngredientResponse(BaseModel):
    items: list[IngredientResponse]
    total: int
    limit: int
    offset: int


class PaginatedHouseholdIngredientResponse(BaseModel):
    items: list[HouseholdIngredientResponse]
    total: int
    limit: int
    offset: int
