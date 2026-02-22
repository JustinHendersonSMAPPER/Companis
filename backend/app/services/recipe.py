from __future__ import annotations

import logging
import re
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

logger = logging.getLogger(__name__)


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
        try:
            recipe = await _save_recipe(raw, db)
        except Exception:
            logger.exception("Failed to save recipe: %s", raw.get("title", "unknown"))
            continue

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

            # Use _parse_quantity for consistent handling of messy AI output
            quantity, unit = _parse_quantity(ing.get("quantity"), ing.get("unit"))
            ingredient_schemas.append(
                RecipeIngredientSchema(
                    name=ing_name,
                    quantity=quantity,
                    unit=unit,
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


async def _save_recipe(
    raw: dict[str, Any],
    db: AsyncSession,
    *,
    source: str = "ai_generated",
    image_url: str | None = None,
) -> Recipe:
    # AI models may return instructions as a list of steps or a single string
    instructions = raw.get("instructions", "")
    if isinstance(instructions, list):
        instructions = "\n".join(str(s) for s in instructions)

    # dietary_tags may arrive as a list instead of a comma-separated string
    dietary_tags = raw.get("dietary_tags")
    if isinstance(dietary_tags, list):
        dietary_tags = ",".join(str(t) for t in dietary_tags)

    # description may arrive as a list
    description = raw.get("description")
    if isinstance(description, list):
        description = " ".join(str(s) for s in description)

    recipe = Recipe(
        title=str(raw.get("title", "Untitled Recipe"))[:500],
        description=description,
        instructions=instructions,
        cuisine=_safe_str(raw.get("cuisine")),
        meal_type=_safe_str(raw.get("meal_type")),
        prep_time_minutes=_safe_int(raw.get("prep_time_minutes")),
        cook_time_minutes=_safe_int(raw.get("cook_time_minutes")),
        servings=_safe_int(raw.get("servings")),
        difficulty=_safe_str(raw.get("difficulty")),
        dietary_tags=dietary_tags,
        calorie_estimate=_safe_int(raw.get("calorie_estimate")),
        image_url=image_url,
        source=source,
    )
    db.add(recipe)
    await db.flush()

    for ing in raw.get("ingredients", []):
        quantity, unit = _parse_quantity(ing.get("quantity"), ing.get("unit"))
        recipe_ingredient = RecipeIngredient(
            recipe_id=recipe.id,
            name=ing.get("name", ""),
            quantity=quantity,
            unit=unit,
            is_optional=ing.get("is_optional", False),
            substitution_notes=ing.get("substitution_notes"),
        )
        db.add(recipe_ingredient)

    await db.flush()
    return recipe


def _safe_int(value: Any) -> int | None:
    """Coerce a value to int, returning None on failure."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    try:
        return int(float(str(value).strip()))
    except (ValueError, TypeError):
        return None


def _safe_str(value: Any) -> str | None:
    """Coerce a value to str, returning None for empty/None."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _parse_quantity(raw_quantity: Any, raw_unit: str | None) -> tuple[float | None, str | None]:
    """Extract a numeric quantity and unit from AI output.

    AI models may return quantity as a number, a numeric string, or a string
    like "1 pound" with the unit embedded.  This function normalises all cases
    into a (float | None, str | None) pair suitable for the database.
    """
    if raw_quantity is None:
        return None, raw_unit

    # Already numeric
    if isinstance(raw_quantity, (int, float)):
        return float(raw_quantity), raw_unit

    raw_quantity = str(raw_quantity).strip()
    if not raw_quantity:
        return None, raw_unit

    # Try pure numeric string first ("200", "2.5")
    try:
        return float(raw_quantity), raw_unit
    except ValueError:
        pass

    # Try to split "1 pound" / "2.5 cups" into number + unit
    match = re.match(r"^([\d.]+)\s+(.+)$", raw_quantity)
    if match:
        try:
            num = float(match.group(1))
            parsed_unit = match.group(2).strip()
            # Prefer the parsed unit over an empty/missing raw_unit
            final_unit = raw_unit if raw_unit else parsed_unit
            return num, final_unit
        except ValueError:
            pass

    # Fraction-like patterns ("1/2 cup")
    frac_match = re.match(r"^(\d+)/(\d+)\s*(.*)$", raw_quantity)
    if frac_match:
        try:
            num = int(frac_match.group(1)) / int(frac_match.group(2))
            parsed_unit = frac_match.group(3).strip()
            final_unit = raw_unit if raw_unit else (parsed_unit or None)
            return num, final_unit
        except (ValueError, ZeroDivisionError):
            pass

    # Unparseable — store as None quantity, put original text in unit for context
    return None, raw_unit or raw_quantity


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
    result = await db.execute(select(HealthGoal.description).where(HealthGoal.user_id == user_id))
    return list(result.scalars().all())


async def _get_family_dietary_notes(household_id: str, db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(FamilyMember.dietary_notes).where(
            FamilyMember.household_id == household_id,
            FamilyMember.dietary_notes.isnot(None),
        )
    )
    return list(result.scalars().all())
