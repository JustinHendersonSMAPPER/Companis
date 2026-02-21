from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class HouseholdCreate(BaseModel):
    name: str = Field(max_length=255)


class HouseholdResponse(BaseModel):
    id: str
    name: str
    owner_id: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FamilyMemberAdd(BaseModel):
    name: str = Field(max_length=255)
    user_id: str | None = None
    role: str = "member"
    dietary_notes: str | None = None


class FamilyMemberResponse(BaseModel):
    id: str
    household_id: str
    user_id: str | None
    name: str
    role: str
    dietary_notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class FamilyMemberUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
    dietary_notes: str | None = None
