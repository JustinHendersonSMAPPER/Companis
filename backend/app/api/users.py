from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import DietaryPreference, HealthGoal, User
from app.schemas.user import (
    DietaryPreferenceCreate,
    DietaryPreferenceResponse,
    HealthGoalCreate,
    HealthGoalResponse,
    UserResponse,
    UserUpdate,
)

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    if update_data.full_name is not None:
        current_user.full_name = update_data.full_name
    if update_data.avatar_url is not None:
        current_user.avatar_url = update_data.avatar_url
    await db.flush()
    return current_user


@router.get("/me/dietary-preferences", response_model=list[DietaryPreferenceResponse])
async def get_dietary_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DietaryPreference]:
    result = await db.execute(
        select(DietaryPreference).where(DietaryPreference.user_id == current_user.id)
    )
    return list(result.scalars().all())


@router.post(
    "/me/dietary-preferences",
    response_model=DietaryPreferenceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_dietary_preference(
    pref_data: DietaryPreferenceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DietaryPreference:
    pref = DietaryPreference(
        user_id=current_user.id,
        preference_type=pref_data.preference_type,
        value=pref_data.value,
        notes=pref_data.notes,
    )
    db.add(pref)
    await db.flush()
    return pref


@router.delete("/me/dietary-preferences/{pref_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_dietary_preference(
    pref_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(DietaryPreference).where(
            DietaryPreference.id == pref_id,
            DietaryPreference.user_id == current_user.id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Preference not found")


@router.get("/me/health-goals", response_model=list[HealthGoalResponse])
async def get_health_goals(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[HealthGoal]:
    result = await db.execute(
        select(HealthGoal).where(HealthGoal.user_id == current_user.id)
    )
    return list(result.scalars().all())


@router.post(
    "/me/health-goals",
    response_model=HealthGoalResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_health_goal(
    goal_data: HealthGoalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HealthGoal:
    goal = HealthGoal(
        user_id=current_user.id,
        goal_type=goal_data.goal_type,
        description=goal_data.description,
        target_value=goal_data.target_value,
    )
    db.add(goal)
    await db.flush()
    return goal


@router.delete("/me/health-goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_health_goal(
    goal_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(HealthGoal).where(
            HealthGoal.id == goal_id,
            HealthGoal.user_id == current_user.id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Health goal not found")
