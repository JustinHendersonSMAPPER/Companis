from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CollectionCreate(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = None


class CollectionResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class CollectionItemResponse(BaseModel):
    id: str
    collection_id: str
    recipe_id: str
    added_at: datetime

    model_config = {"from_attributes": True}


class CollectionDetailResponse(BaseModel):
    id: str
    user_id: str
    name: str
    description: str | None
    created_at: datetime
    items: list[CollectionItemResponse] = []

    model_config = {"from_attributes": True}


class CollectionAddRecipe(BaseModel):
    recipe_id: str
