from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.database import get_db
from app.models.recipe import Recipe, RecipeCollection, RecipeCollectionItem
from app.models.user import User
from app.schemas.collection import (
    CollectionAddRecipe,
    CollectionCreate,
    CollectionDetailResponse,
    CollectionItemResponse,
    CollectionResponse,
)

router = APIRouter()


@router.post("/", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    data: CollectionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeCollection:
    collection = RecipeCollection(
        user_id=current_user.id,
        name=data.name,
        description=data.description,
    )
    db.add(collection)
    await db.flush()
    return collection


@router.get("/", response_model=list[CollectionResponse])
async def list_collections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RecipeCollection]:
    result = await db.execute(
        select(RecipeCollection)
        .where(RecipeCollection.user_id == current_user.id)
        .order_by(RecipeCollection.created_at.desc())
    )
    return list(result.scalars().all())


@router.get("/{collection_id}", response_model=CollectionDetailResponse)
async def get_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeCollection:
    result = await db.execute(
        select(RecipeCollection)
        .where(
            RecipeCollection.id == collection_id,
            RecipeCollection.user_id == current_user.id,
        )
        .options(selectinload(RecipeCollection.items))
    )
    collection = result.scalar_one_or_none()
    if collection is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )
    return collection


@router.post(
    "/{collection_id}/recipes",
    response_model=CollectionItemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_recipe_to_collection(
    collection_id: str,
    data: CollectionAddRecipe,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeCollectionItem:
    collection_result = await db.execute(
        select(RecipeCollection).where(
            RecipeCollection.id == collection_id,
            RecipeCollection.user_id == current_user.id,
        )
    )
    if collection_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )

    recipe_result = await db.execute(select(Recipe).where(Recipe.id == data.recipe_id))
    if recipe_result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    existing = await db.execute(
        select(RecipeCollectionItem).where(
            RecipeCollectionItem.collection_id == collection_id,
            RecipeCollectionItem.recipe_id == data.recipe_id,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Recipe already in collection",
        )

    item = RecipeCollectionItem(
        collection_id=collection_id,
        recipe_id=data.recipe_id,
    )
    db.add(item)
    await db.flush()
    return item


@router.delete(
    "/{collection_id}/recipes/{recipe_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_recipe_from_collection(
    collection_id: str,
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    collection_result = await db.execute(
        select(RecipeCollection).where(
            RecipeCollection.id == collection_id,
            RecipeCollection.user_id == current_user.id,
        )
    )
    if collection_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )

    result = await db.execute(
        delete(RecipeCollectionItem).where(
            RecipeCollectionItem.collection_id == collection_id,
            RecipeCollectionItem.recipe_id == recipe_id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not in collection"
        )


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(RecipeCollection).where(
            RecipeCollection.id == collection_id,
            RecipeCollection.user_id == current_user.id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Collection not found"
        )
