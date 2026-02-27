from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_user_household_id
from app.database import get_db
from app.models.meal_plan import MealPlan
from app.models.recipe import Recipe, RecipeIngredient
from app.models.shopping import ShoppingCart, ShoppingCartItem
from app.models.user import User
from app.schemas.meal_plan import (
    MealPlanCreate,
    MealPlanResponse,
    MealPlanUpdate,
)

router = APIRouter()


@router.post("/", response_model=MealPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_meal_plan(
    data: MealPlanCreate,
    current_user: User = Depends(get_current_user),
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> MealPlan:
    result = await db.execute(select(Recipe).where(Recipe.id == data.recipe_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    meal_plan = MealPlan(
        household_id=household_id,
        recipe_id=data.recipe_id,
        meal_date=data.meal_date,
        meal_type=data.meal_type,
        servings=data.servings,
        notes=data.notes,
        created_by_user_id=current_user.id,
    )
    db.add(meal_plan)
    await db.flush()
    return meal_plan


@router.get("/", response_model=list[MealPlanResponse])
async def get_meal_plans(
    start_date: datetime = Query(..., description="Start date for meal plan range"),
    end_date: datetime = Query(..., description="End date for meal plan range"),
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> list[MealPlan]:
    result = await db.execute(
        select(MealPlan)
        .where(
            MealPlan.household_id == household_id,
            MealPlan.meal_date >= start_date,
            MealPlan.meal_date <= end_date,
        )
        .order_by(MealPlan.meal_date, MealPlan.meal_type)
    )
    return list(result.scalars().all())


@router.put("/{meal_plan_id}", response_model=MealPlanResponse)
async def update_meal_plan(
    meal_plan_id: str,
    update_data: MealPlanUpdate,
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> MealPlan:
    result = await db.execute(
        select(MealPlan).where(
            MealPlan.id == meal_plan_id,
            MealPlan.household_id == household_id,
        )
    )
    meal_plan = result.scalar_one_or_none()
    if meal_plan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found")

    if update_data.recipe_id is not None:
        recipe_result = await db.execute(
            select(Recipe).where(Recipe.id == update_data.recipe_id)
        )
        if recipe_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found"
            )
        meal_plan.recipe_id = update_data.recipe_id
    if update_data.meal_date is not None:
        meal_plan.meal_date = update_data.meal_date
    if update_data.meal_type is not None:
        meal_plan.meal_type = update_data.meal_type
    if update_data.servings is not None:
        meal_plan.servings = update_data.servings
    if update_data.notes is not None:
        meal_plan.notes = update_data.notes

    await db.flush()
    return meal_plan


@router.delete("/{meal_plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meal_plan(
    meal_plan_id: str,
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(MealPlan).where(
            MealPlan.id == meal_plan_id,
            MealPlan.household_id == household_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Meal plan not found"
        )


@router.post("/generate-shopping-list", response_model=list[dict[str, str | float | None]])
async def generate_shopping_list(
    start_date: datetime = Query(..., description="Start date for meal plan range"),
    end_date: datetime = Query(..., description="End date for meal plan range"),
    _current_user: User = Depends(get_current_user),
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, str | float | None]]:
    """Auto-generate shopping list items from meal plan recipes in a date range."""
    meal_plans_result = await db.execute(
        select(MealPlan)
        .where(
            MealPlan.household_id == household_id,
            MealPlan.meal_date >= start_date,
            MealPlan.meal_date <= end_date,
        )
    )
    meal_plans = meal_plans_result.scalars().all()

    if not meal_plans:
        return []

    recipe_ids = [mp.recipe_id for mp in meal_plans]
    ingredients_result = await db.execute(
        select(RecipeIngredient)
        .where(RecipeIngredient.recipe_id.in_(recipe_ids))
    )
    recipe_ingredients = ingredients_result.scalars().all()

    if not recipe_ingredients:
        return []

    # Get or create active shopping cart
    cart_result = await db.execute(
        select(ShoppingCart).where(
            ShoppingCart.household_id == household_id,
            ShoppingCart.is_active.is_(True),
        )
    )
    cart = cart_result.scalar_one_or_none()
    if cart is None:
        cart = ShoppingCart(household_id=household_id, name="Meal Plan Shopping List")
        db.add(cart)
        await db.flush()

    added_items: list[dict[str, str | float | None]] = []
    for ri in recipe_ingredients:
        item = ShoppingCartItem(
            cart_id=cart.id,
            ingredient_id=ri.ingredient_id,
            name=ri.name,
            quantity=ri.quantity,
            unit=ri.unit,
            added_from_recipe_id=ri.recipe_id,
        )
        db.add(item)
        added_items.append({
            "name": ri.name,
            "quantity": ri.quantity,
            "unit": ri.unit,
            "recipe_id": ri.recipe_id,
        })

    await db.flush()
    return added_items
