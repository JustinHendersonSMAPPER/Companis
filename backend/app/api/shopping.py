from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_user_household_id
from app.database import get_db
from app.models.shopping import ShoppingCart, ShoppingCartItem
from app.models.user import User
from app.schemas.shopping import (
    AddMissingIngredientsRequest,
    ShoppingCartCreate,
    ShoppingCartItemAdd,
    ShoppingCartItemResponse,
    ShoppingCartItemUpdate,
    ShoppingCartResponse,
)

router = APIRouter()


@router.get("/", response_model=list[ShoppingCartResponse])
async def get_carts(
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> list[ShoppingCart]:
    result = await db.execute(
        select(ShoppingCart)
        .where(ShoppingCart.household_id == household_id, ShoppingCart.is_active.is_(True))
        .options(selectinload(ShoppingCart.items))
    )
    return list(result.scalars().all())


@router.post("/", response_model=ShoppingCartResponse, status_code=status.HTTP_201_CREATED)
async def create_cart(
    data: ShoppingCartCreate,
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> ShoppingCart:
    cart = ShoppingCart(household_id=household_id, name=data.name)
    db.add(cart)
    await db.flush()

    result = await db.execute(
        select(ShoppingCart)
        .where(ShoppingCart.id == cart.id)
        .options(selectinload(ShoppingCart.items))
    )
    return result.scalar_one()


@router.post(
    "/{cart_id}/items",
    response_model=ShoppingCartItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_cart_item(
    cart_id: str,
    data: ShoppingCartItemAdd,
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> ShoppingCartItem:
    cart_result = await db.execute(
        select(ShoppingCart).where(
            ShoppingCart.id == cart_id,
            ShoppingCart.household_id == household_id,
        )
    )
    if cart_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    item = ShoppingCartItem(
        cart_id=cart_id,
        ingredient_id=data.ingredient_id,
        name=data.name,
        quantity=data.quantity,
        unit=data.unit,
        notes=data.notes,
        added_from_recipe_id=data.added_from_recipe_id,
    )
    db.add(item)
    await db.flush()
    return item


@router.patch("/{cart_id}/items/{item_id}", response_model=ShoppingCartItemResponse)
async def update_cart_item(
    cart_id: str,
    item_id: str,
    update_data: ShoppingCartItemUpdate,
    _household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> ShoppingCartItem:
    result = await db.execute(
        select(ShoppingCartItem).where(
            ShoppingCartItem.id == item_id,
            ShoppingCartItem.cart_id == cart_id,
        )
    )
    item = result.scalar_one_or_none()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if update_data.quantity is not None:
        item.quantity = update_data.quantity
    if update_data.unit is not None:
        item.unit = update_data.unit
    if update_data.notes is not None:
        item.notes = update_data.notes
    if update_data.is_purchased is not None:
        item.is_purchased = update_data.is_purchased

    await db.flush()
    return item


@router.delete("/{cart_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_cart_item(
    cart_id: str,
    item_id: str,
    _household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(ShoppingCartItem).where(
            ShoppingCartItem.id == item_id,
            ShoppingCartItem.cart_id == cart_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")


@router.post("/add-missing-ingredients", response_model=list[ShoppingCartItemResponse])
async def add_missing_ingredients(
    data: AddMissingIngredientsRequest,
    _current_user: User = Depends(get_current_user),
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> list[ShoppingCartItem]:
    result = await db.execute(
        select(ShoppingCart).where(
            ShoppingCart.household_id == household_id,
            ShoppingCart.is_active.is_(True),
        )
    )
    cart = result.scalar_one_or_none()

    if cart is None:
        cart = ShoppingCart(household_id=household_id, name="My Shopping List")
        db.add(cart)
        await db.flush()

    items: list[ShoppingCartItem] = []
    for name in data.ingredient_names:
        item = ShoppingCartItem(
            cart_id=cart.id,
            name=name,
            added_from_recipe_id=data.recipe_id,
        )
        db.add(item)
        items.append(item)

    await db.flush()
    return items
