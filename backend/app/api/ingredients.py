from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_user_household_id
from app.database import get_db
from app.models.ingredient import HouseholdIngredient, Ingredient
from app.models.user import User
from app.schemas.ingredient import (
    BarcodeScanResult,
    CameraScanRequest,
    CameraScanResult,
    HouseholdIngredientAdd,
    HouseholdIngredientResponse,
    HouseholdIngredientUpdate,
    IngredientCreate,
    IngredientResponse,
    PaginatedIngredientResponse,
    PaginatedHouseholdIngredientResponse,
)

router = APIRouter()


@router.get("/search", response_model=PaginatedIngredientResponse)
async def search_ingredients(
    q: str,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> PaginatedIngredientResponse:
    count_result = await db.execute(
        select(func.count())
        .select_from(Ingredient)
        .where(Ingredient.name.ilike(f"%{q}%"))
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Ingredient)
        .where(Ingredient.name.ilike(f"%{q}%"))
        .order_by(Ingredient.name)
        .limit(limit)
        .offset(offset)
    )
    items = list(result.scalars().all())
    return PaginatedIngredientResponse(
        items=[IngredientResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post("/", response_model=IngredientResponse, status_code=status.HTTP_201_CREATED)
async def create_ingredient(
    ingredient_data: IngredientCreate,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> Ingredient:
    ingredient = Ingredient(
        name=ingredient_data.name,
        category=ingredient_data.category,
        barcode=ingredient_data.barcode,
        brand=ingredient_data.brand,
        description=ingredient_data.description,
        common_allergens=ingredient_data.common_allergens,
    )
    db.add(ingredient)
    await db.flush()
    return ingredient


@router.get("/household", response_model=PaginatedHouseholdIngredientResponse)
async def get_household_ingredients(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> PaginatedHouseholdIngredientResponse:
    count_result = await db.execute(
        select(func.count())
        .select_from(HouseholdIngredient)
        .where(HouseholdIngredient.household_id == household_id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(HouseholdIngredient)
        .where(HouseholdIngredient.household_id == household_id)
        .options(selectinload(HouseholdIngredient.ingredient))
        .order_by(HouseholdIngredient.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    items = list(result.scalars().all())
    return PaginatedHouseholdIngredientResponse(
        items=[HouseholdIngredientResponse.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/household",
    response_model=HouseholdIngredientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_household_ingredient(
    data: HouseholdIngredientAdd,
    current_user: User = Depends(get_current_user),
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> HouseholdIngredient:
    ingredient_id = data.ingredient_id

    if ingredient_id is None and data.barcode:
        from app.services.barcode import lookup_barcode

        barcode_result = await lookup_barcode(data.barcode, db)
        if barcode_result and barcode_result.ingredient:
            ingredient_id = barcode_result.ingredient.id

    if ingredient_id is None and data.name:
        ingredient = Ingredient(name=data.name, barcode=data.barcode)
        db.add(ingredient)
        await db.flush()
        ingredient_id = ingredient.id

    if ingredient_id is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide ingredient_id, name, or barcode",
        )

    household_ingredient = HouseholdIngredient(
        household_id=household_id,
        ingredient_id=ingredient_id,
        quantity=data.quantity,
        unit=data.unit,
        expiry_date=data.expiry_date,
        added_by_user_id=current_user.id,
        source=data.source,
    )
    db.add(household_ingredient)
    await db.flush()

    result = await db.execute(
        select(HouseholdIngredient)
        .where(HouseholdIngredient.id == household_ingredient.id)
        .options(selectinload(HouseholdIngredient.ingredient))
    )
    return result.scalar_one()


@router.patch("/household/{item_id}", response_model=HouseholdIngredientResponse)
async def update_household_ingredient(
    item_id: str,
    update_data: HouseholdIngredientUpdate,
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> HouseholdIngredient:
    result = await db.execute(
        select(HouseholdIngredient)
        .where(
            HouseholdIngredient.id == item_id,
            HouseholdIngredient.household_id == household_id,
        )
        .options(selectinload(HouseholdIngredient.ingredient))
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if update_data.quantity is not None:
        item.quantity = update_data.quantity
    if update_data.unit is not None:
        item.unit = update_data.unit
    if update_data.expiry_date is not None:
        item.expiry_date = update_data.expiry_date

    await db.flush()
    return item


@router.delete("/household/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_household_ingredient(
    item_id: str,
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(HouseholdIngredient).where(
            HouseholdIngredient.id == item_id,
            HouseholdIngredient.household_id == household_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


@router.get("/barcode/{barcode}", response_model=BarcodeScanResult)
async def scan_barcode(
    barcode: str,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> BarcodeScanResult:
    from app.services.barcode import lookup_barcode

    result = await lookup_barcode(barcode, db)
    if result is None:
        return BarcodeScanResult(
            barcode=barcode, ingredient=None, product_name=None, brand=None, found=False
        )
    return result


@router.post("/camera-scan", response_model=CameraScanResult)
async def camera_scan(
    scan_data: CameraScanRequest,
    _current_user: User = Depends(get_current_user),
) -> CameraScanResult:
    from app.services.ingredient import detect_ingredients_from_image

    return await detect_ingredients_from_image(scan_data.image_base64)
