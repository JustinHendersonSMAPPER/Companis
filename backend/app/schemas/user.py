from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    terms_accepted: bool = Field(
        description="User must accept terms and conditions to register"
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: str | None = None
    avatar_url: str | None = None


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    avatar_url: str | None
    auth_provider: str
    is_active: bool
    is_verified: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class DietaryPreferenceCreate(BaseModel):
    preference_type: str = Field(max_length=100)
    value: str = Field(max_length=255)
    notes: str | None = None


class DietaryPreferenceResponse(BaseModel):
    id: str
    preference_type: str
    value: str
    notes: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class HealthGoalCreate(BaseModel):
    goal_type: str = Field(max_length=100)
    description: str
    target_value: str | None = None


class HealthGoalResponse(BaseModel):
    id: str
    goal_type: str
    description: str
    target_value: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenRefresh(BaseModel):
    refresh_token: str
