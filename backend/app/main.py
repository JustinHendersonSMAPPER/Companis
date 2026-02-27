from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.ai import router as ai_router
from app.api.auth import router as auth_router
from app.api.collections import router as collections_router
from app.api.cooking_history import router as cooking_history_router
from app.api.household import router as household_router
from app.api.ingredients import router as ingredients_router
from app.api.meal_plan import router as meal_plan_router
from app.api.recipes import router as recipes_router
from app.api.shopping import router as shopping_router
from app.api.users import router as users_router
from app.config import settings
from app.database import init_db


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered recipe assistant that helps you cook with what you have",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/users", tags=["Users"])
app.include_router(ingredients_router, prefix="/api/ingredients", tags=["Ingredients"])
app.include_router(recipes_router, prefix="/api/recipes", tags=["Recipes"])
app.include_router(household_router, prefix="/api/household", tags=["Household"])
app.include_router(shopping_router, prefix="/api/shopping", tags=["Shopping"])
app.include_router(meal_plan_router, prefix="/api/meal-plan", tags=["Meal Plan"])
app.include_router(cooking_history_router, prefix="/api/cooking-history", tags=["Cooking History"])
app.include_router(collections_router, prefix="/api/collections", tags=["Collections"])
app.include_router(ai_router, prefix="/api/ai", tags=["AI"])


@app.get("/api/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
