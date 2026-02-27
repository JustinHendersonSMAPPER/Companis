from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_user_household_id
from app.database import get_db
from app.models.recipe import Recipe, RecipeRating, UserFavorite
from app.models.user import User
from app.schemas.recipe import (
    PaginatedFavoritesResponse,
    RecipeRatingCreate,
    RecipeRatingResponse,
    RecipeResponse,
    RecipeSearchRequest,
    RecipeSearchResponse,
)

router = APIRouter()


@router.post("/search", response_model=RecipeSearchResponse)
async def search_recipes(
    search: RecipeSearchRequest,
    current_user: User = Depends(get_current_user),
    household_id: str = Depends(get_user_household_id),
    db: AsyncSession = Depends(get_db),
) -> RecipeSearchResponse:
    from app.services.recipe import search_recipes_with_ai

    return await search_recipes_with_ai(
        prompt=search.prompt,
        user_id=current_user.id,
        household_id=household_id,
        max_results=search.max_results,
        prefer_available=search.prefer_available_ingredients,
        max_prep_time=search.max_prep_time_minutes,
        cuisine=search.cuisine,
        dietary_filter=search.dietary_filter,
        db=db,
    )


@router.get("/{recipe_id}", response_model=RecipeResponse)
async def get_recipe(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeResponse:
    # Query 1: Recipe with eagerly loaded ingredients
    result = await db.execute(
        select(Recipe)
        .where(Recipe.id == recipe_id)
        .options(selectinload(Recipe.recipe_ingredients))
    )
    recipe = result.scalar_one_or_none()
    if recipe is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    # Query 2: Combine avg rating, user rating, and favorite status into one query
    avg_rating_subq = (
        select(func.avg(RecipeRating.score))
        .where(RecipeRating.recipe_id == recipe_id)
        .correlate(None)
        .scalar_subquery()
    )
    user_rating_subq = (
        select(RecipeRating.score)
        .where(
            RecipeRating.recipe_id == recipe_id,
            RecipeRating.user_id == current_user.id,
        )
        .correlate(None)
        .scalar_subquery()
    )
    fav_subq = (
        select(func.count(UserFavorite.id))
        .where(
            UserFavorite.recipe_id == recipe_id,
            UserFavorite.user_id == current_user.id,
        )
        .correlate(None)
        .scalar_subquery()
    )
    meta_result = await db.execute(
        select(avg_rating_subq, user_rating_subq, fav_subq)
    )
    row = meta_result.one()
    avg_rating, user_rating, fav_count = row[0], row[1], row[2]

    ingredients = [
        {
            "name": ri.name,
            "quantity": ri.quantity,
            "unit": ri.unit,
            "is_optional": ri.is_optional,
            "substitution_notes": ri.substitution_notes,
        }
        for ri in recipe.recipe_ingredients
    ]

    return RecipeResponse(
        id=recipe.id,
        title=recipe.title,
        description=recipe.description,
        instructions=recipe.instructions,
        cuisine=recipe.cuisine,
        meal_type=recipe.meal_type,
        prep_time_minutes=recipe.prep_time_minutes,
        cook_time_minutes=recipe.cook_time_minutes,
        servings=recipe.servings,
        difficulty=recipe.difficulty,
        image_url=recipe.image_url,
        source=recipe.source,
        dietary_tags=recipe.dietary_tags,
        calorie_estimate=recipe.calorie_estimate,
        created_at=recipe.created_at,
        recipe_ingredients=ingredients,
        average_rating=float(avg_rating) if avg_rating else None,
        user_rating=user_rating,
        is_favorite=fav_count > 0,
    )


@router.post("/{recipe_id}/rate", response_model=RecipeRatingResponse)
async def rate_recipe(
    recipe_id: str,
    rating_data: RecipeRatingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RecipeRating:
    result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    existing = await db.execute(
        select(RecipeRating).where(
            RecipeRating.recipe_id == recipe_id,
            RecipeRating.user_id == current_user.id,
        )
    )
    existing_rating = existing.scalar_one_or_none()

    if existing_rating:
        existing_rating.score = rating_data.score
        existing_rating.review = rating_data.review
        await db.flush()
        return existing_rating

    rating = RecipeRating(
        recipe_id=recipe_id,
        user_id=current_user.id,
        score=rating_data.score,
        review=rating_data.review,
    )
    db.add(rating)
    await db.flush()
    return rating


@router.post("/{recipe_id}/favorite", status_code=status.HTTP_201_CREATED)
async def add_favorite(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    result = await db.execute(select(Recipe).where(Recipe.id == recipe_id))
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipe not found")

    existing = await db.execute(
        select(UserFavorite).where(
            UserFavorite.recipe_id == recipe_id,
            UserFavorite.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        return {"status": "already_favorited"}

    favorite = UserFavorite(recipe_id=recipe_id, user_id=current_user.id)
    db.add(favorite)
    await db.flush()
    return {"status": "favorited"}


@router.delete("/{recipe_id}/favorite", status_code=status.HTTP_204_NO_CONTENT)
async def remove_favorite(
    recipe_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(UserFavorite).where(
            UserFavorite.recipe_id == recipe_id,
            UserFavorite.user_id == current_user.id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Favorite not found")


@router.get("/favorites/list", response_model=PaginatedFavoritesResponse)
async def get_favorites(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaginatedFavoritesResponse:
    count_result = await db.execute(
        select(func.count())
        .select_from(UserFavorite)
        .where(UserFavorite.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Recipe)
        .join(UserFavorite, UserFavorite.recipe_id == Recipe.id)
        .where(UserFavorite.user_id == current_user.id)
        .options(selectinload(Recipe.recipe_ingredients))
        .order_by(UserFavorite.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    recipes = result.scalars().all()
    items = [
        RecipeResponse(
            id=r.id,
            title=r.title,
            description=r.description,
            instructions=r.instructions,
            cuisine=r.cuisine,
            meal_type=r.meal_type,
            prep_time_minutes=r.prep_time_minutes,
            cook_time_minutes=r.cook_time_minutes,
            servings=r.servings,
            difficulty=r.difficulty,
            image_url=r.image_url,
            source=r.source,
            dietary_tags=r.dietary_tags,
            calorie_estimate=r.calorie_estimate,
            created_at=r.created_at,
            recipe_ingredients=[
                {
                    "name": ri.name,
                    "quantity": ri.quantity,
                    "unit": ri.unit,
                    "is_optional": ri.is_optional,
                    "substitution_notes": ri.substitution_notes,
                }
                for ri in r.recipe_ingredients
            ],
            is_favorite=True,
        )
        for r in recipes
    ]
    return PaginatedFavoritesResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
