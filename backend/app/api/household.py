from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_user_household_id
from app.database import get_db
from app.models.household import FamilyMember, Household
from app.models.user import User
from app.schemas.household import (
    FamilyMemberAdd,
    FamilyMemberResponse,
    FamilyMemberUpdate,
    HouseholdCreate,
    HouseholdResponse,
)

router = APIRouter()


@router.get("/", response_model=HouseholdResponse)
async def get_household(
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> Household:
    result = await db.execute(select(Household).where(Household.id == household_id))
    household = result.scalar_one_or_none()
    if household is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Household not found")
    return household


@router.post("/", response_model=HouseholdResponse, status_code=status.HTTP_201_CREATED)
async def create_household(
    data: HouseholdCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Household:
    household = Household(name=data.name, owner_id=current_user.id)
    db.add(household)
    await db.flush()

    member = FamilyMember(
        household_id=household.id,
        user_id=current_user.id,
        name=current_user.full_name,
        role="owner",
    )
    db.add(member)
    await db.flush()
    return household


@router.get("/members", response_model=list[FamilyMemberResponse])
async def get_members(
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> list[FamilyMember]:
    result = await db.execute(
        select(FamilyMember).where(FamilyMember.household_id == household_id)
    )
    return list(result.scalars().all())


@router.post(
    "/members",
    response_model=FamilyMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_member(
    data: FamilyMemberAdd,
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> FamilyMember:
    member = FamilyMember(
        household_id=household_id,
        user_id=data.user_id,
        name=data.name,
        role=data.role,
        dietary_notes=data.dietary_notes,
    )
    db.add(member)
    await db.flush()
    return member


@router.patch("/members/{member_id}", response_model=FamilyMemberResponse)
async def update_member(
    member_id: str,
    update_data: FamilyMemberUpdate,
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> FamilyMember:
    result = await db.execute(
        select(FamilyMember).where(
            FamilyMember.id == member_id,
            FamilyMember.household_id == household_id,
        )
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")

    if update_data.name is not None:
        member.name = update_data.name
    if update_data.role is not None:
        member.role = update_data.role
    if update_data.dietary_notes is not None:
        member.dietary_notes = update_data.dietary_notes

    await db.flush()
    return member


@router.delete("/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    member_id: str,
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(FamilyMember).where(
            FamilyMember.id == member_id,
            FamilyMember.household_id == household_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
