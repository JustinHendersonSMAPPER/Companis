from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_user_household_id
from app.database import get_db
from app.models.cooking_history import CookingHistory
from app.models.recipe import Recipe
from app.models.user import User
from app.schemas.cooking_history import (
    CookingHistoryCreate,
    CookingHistoryResponse,
    PaginatedCookingHistoryResponse,
)

router = APIRouter()


@router.post("/", response_model=CookingHistoryResponse, status_code=status.HTTP_201_CREATED)
async def log_cooked_recipe(
    data: CookingHistoryCreate,
    current_user: User = Depends(get_current_user),
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> CookingHistory:
    result = await db.execute(select(Recipe).where(Recipe.id == data.recipe_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    entry = CookingHistory(
        user_id=current_user.id,
        recipe_id=data.recipe_id,
        household_id=household_id,
        servings_made=data.servings_made,
        notes=data.notes,
    )
    db.add(entry)
    await db.flush()
    return entry


@router.get("/", response_model=PaginatedCookingHistoryResponse)
async def get_cooking_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedCookingHistoryResponse:
    count_result = await db.execute(
        select(func.count()).select_from(CookingHistory).where(
            CookingHistory.user_id == current_user.id
        )
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(CookingHistory)
        .where(CookingHistory.user_id == current_user.id)
        .order_by(CookingHistory.cooked_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = list(result.scalars().all())

    return PaginatedCookingHistoryResponse(
        items=[CookingHistoryResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )
