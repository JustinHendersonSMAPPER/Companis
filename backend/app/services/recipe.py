from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.household import FamilyMember
from app.models.ingredient import HouseholdIngredient, Ingredient
from app.models.recipe import Recipe, RecipeIngredient
from app.models.user import DietaryPreference, HealthGoal
from app.schemas.recipe import (
    RecipeIngredientSchema,
    RecipeResponse,
    RecipeSearchResponse,
    SubstitutionSuggestion,
)
from app.services.ai import get_ai_service


async def search_recipes_with_ai(
    prompt: str,
    user_id: str,
    household_id: str,
    max_results: int,
    prefer_available: bool,
    max_prep_time: int | None,
    cuisine: str | None,
    dietary_filter: list[str],
    db: AsyncSession,
) -> RecipeSearchResponse:
    available_ingredients = await _get_household_ingredient_names(household_id, db)
    dietary_preferences = await _get_user_dietary_preferences(user_id, db)
    health_goals = await _get_user_health_goals(user_id, db)
    family_notes = await _get_family_dietary_notes(household_id, db)

    all_dietary = dietary_preferences + dietary_filter

    ai_service = get_ai_service()
    raw_recipes = await ai_service.generate_recipes(
        prompt=prompt,
        available_ingredients=available_ingredients if prefer_available else [],
        dietary_preferences=all_dietary,
        health_goals=health_goals,
        family_dietary_notes=family_notes,
        favorite_cuisines=[],
        max_results=max_results,
        max_prep_time=max_prep_time,
        cuisine=cuisine,
    )

    recipes: list[RecipeResponse] = []
    missing_ingredients: dict[str, list[str]] = {}
    substitutions: dict[str, list[SubstitutionSuggestion]] = {}

    available_lower = {ing.lower() for ing in available_ingredients}

    for raw in raw_recipes:
        recipe = await _save_recipe(raw, db)
        recipe_missing: list[str] = []
        recipe_subs: list[SubstitutionSuggestion] = []

        ingredient_schemas: list[RecipeIngredientSchema] = []
        for ing in raw.get("ingredients", []):
            ing_name = ing.get("name", "")
            is_available = ing_name.lower() in available_lower
            has_sub = bool(ing.get("substitution_notes"))

            if not is_available and not ing.get("is_optional", False):
                if has_sub:
                    recipe_subs.append(
                        SubstitutionSuggestion(
                            original_ingredient=ing_name,
                            substitute=ing.get("substitution_notes", ""),
                            notes=f"Substitute available for {ing_name}",
                        )
                    )
                else:
                    recipe_missing.append(ing_name)

            ingredient_schemas.append(
                RecipeIngredientSchema(
                    name=ing_name,
                    quantity=ing.get("quantity"),
                    unit=ing.get("unit"),
                    is_optional=ing.get("is_optional", False),
                    substitution_notes=ing.get("substitution_notes"),
                    is_available=is_available,
                    has_substitution=has_sub,
                )
            )

        recipe_response = RecipeResponse(
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
            recipe_ingredients=ingredient_schemas,
        )
        recipes.append(recipe_response)

        if recipe_missing:
            missing_ingredients[recipe.id] = recipe_missing
        if recipe_subs:
            substitutions[recipe.id] = recipe_subs

    return RecipeSearchResponse(
        recipes=recipes,
        missing_ingredients=missing_ingredients,
        substitutions=substitutions,
    )


async def _save_recipe(raw: dict[str, Any], db: AsyncSession) -> Recipe:
    recipe = Recipe(
        title=raw.get("title", "Untitled Recipe"),
        description=raw.get("description"),
        instructions=raw.get("instructions", ""),
        cuisine=raw.get("cuisine"),
        meal_type=raw.get("meal_type"),
        prep_time_minutes=raw.get("prep_time_minutes"),
        cook_time_minutes=raw.get("cook_time_minutes"),
        servings=raw.get("servings"),
        difficulty=raw.get("difficulty"),
        dietary_tags=raw.get("dietary_tags"),
        calorie_estimate=raw.get("calorie_estimate"),
        source="ai_generated",
    )
    db.add(recipe)
    await db.flush()

    for ing in raw.get("ingredients", []):
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.id,
            name=ing.get("name", ""),
            quantity=ing.get("quantity"),
            unit=ing.get("unit"),
            is_optional=ing.get("is_optional", False),
            substitution_notes=ing.get("substitution_notes"),
        )
        db.add(recipe_ingredient)

    await db.flush()
    return recipe


async def _get_household_ingredient_names(household_id: str, db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(Ingredient.name)
        .join(HouseholdIngredient, HouseholdIngredient.ingredient_id == Ingredient.id)
        .where(HouseholdIngredient.household_id == household_id)
    )
    return list(result.scalars().all())


async def _get_user_dietary_preferences(user_id: str, db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(DietaryPreference.value).where(DietaryPreference.user_id == user_id)
    )
    return list(result.scalars().all())


async def _get_user_health_goals(user_id: str, db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(HealthGoal.description).where(HealthGoal.user_id == user_id)
    )
    return list(result.scalars().all())


async def _get_family_dietary_notes(household_id: str, db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(FamilyMember.dietary_notes)
        .where(
            FamilyMember.household_id == household_id,
            FamilyMember.dietary_notes.isnot(None),
        )
    )
    return list(result.scalars().all())
