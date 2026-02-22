"""TheMealDB fetch and transformation utilities.

Fetches recipes from the free TheMealDB API (test key ``"1"``) and transforms
them into the dict format expected by ``_save_recipe()`` in the recipe service.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any

import httpx

logger = logging.getLogger(__name__)

BASE_URL = "https://www.themealdb.com/api/json/v1/1"

# Descriptive measures that have no meaningful numeric quantity
_DESCRIPTIVE_MEASURES: set[str] = {
    "to taste",
    "to serve",
    "to garnish",
    "as needed",
    "pinch",
    "drizzle",
    "dash",
    "handful",
    "bunch",
    "sprig",
    "sprigs",
    "leaves",
    "leaf",
    "garnish",
    "splash",
}


# ------------------------------------------------------------------
# Measure parsing
# ------------------------------------------------------------------


def parse_measure(measure: str) -> tuple[float | None, str | None]:
    """Parse a TheMealDB measure string into (quantity, unit).

    Handles patterns like:
    - "1 cup"
    - "3/4 cup"
    - "1 1/2 tsp"
    - "300g"
    - "200ml"
    - "To taste"
    - ""
    """
    if not measure:
        return None, None

    text = measure.strip()
    if not text:
        return None, None

    # Check for descriptive measures (case-insensitive)
    if text.lower() in _DESCRIPTIVE_MEASURES:
        return None, text.lower()

    # Pattern: "1 1/2 tsp" (mixed number with fraction)
    mixed = re.match(r"^(\d+)\s+(\d+)/(\d+)\s*(.*)$", text)
    if mixed:
        try:
            whole = int(mixed.group(1))
            num = int(mixed.group(2))
            den = int(mixed.group(3))
            if den != 0:
                qty = whole + num / den
                unit = mixed.group(4).strip() or None
                return qty, unit
        except (ValueError, ZeroDivisionError):
            pass

    # Pattern: "3/4 cup" (fraction)
    frac = re.match(r"^(\d+)/(\d+)\s*(.*)$", text)
    if frac:
        try:
            num = int(frac.group(1))
            den = int(frac.group(2))
            if den != 0:
                qty = num / den
                unit = frac.group(3).strip() or None
                return qty, unit
        except (ValueError, ZeroDivisionError):
            pass

    # Pattern: "300g", "200ml" (number glued to unit)
    glued = re.match(r"^([\d.]+)\s*([a-zA-Z]+.*)$", text)
    if glued:
        try:
            qty = float(glued.group(1))
            unit = glued.group(2).strip() or None
            return qty, unit
        except ValueError:
            pass

    # Pattern: "1 cup", "2.5 tablespoons" (number then unit)
    spaced = re.match(r"^([\d.]+)\s+(.+)$", text)
    if spaced:
        try:
            qty = float(spaced.group(1))
            unit = spaced.group(2).strip() or None
            return qty, unit
        except ValueError:
            pass

    # Pattern: bare number "2", "1.5"
    try:
        return float(text), None
    except ValueError:
        pass

    # Unparseable — treat as descriptive
    return None, text.lower()


# ------------------------------------------------------------------
# Ingredient extraction
# ------------------------------------------------------------------


def _extract_ingredients(meal: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract ingredient dicts from TheMealDB's strIngredient1-20 / strMeasure1-20."""
    ingredients: list[dict[str, Any]] = []
    for i in range(1, 21):
        name = (meal.get(f"strIngredient{i}") or "").strip()
        if not name:
            continue
        measure_str = (meal.get(f"strMeasure{i}") or "").strip()
        quantity, unit = parse_measure(measure_str)
        ingredients.append(
            {
                "name": name,
                "quantity": quantity,
                "unit": unit,
                "is_optional": False,
                "substitution_notes": None,
            }
        )
    return ingredients


# ------------------------------------------------------------------
# Description builder
# ------------------------------------------------------------------


def _build_description(meal: dict[str, Any]) -> str:
    """Build a description string from area, category, and YouTube link."""
    parts: list[str] = []
    area = (meal.get("strArea") or "").strip()
    category = (meal.get("strCategory") or "").strip()
    if area and category:
        parts.append(f"{area} {category.lower()} dish")
    elif area:
        parts.append(f"{area} dish")
    elif category:
        parts.append(f"{category} dish")

    youtube = (meal.get("strYoutube") or "").strip()
    if youtube:
        parts.append(f"Video: {youtube}")

    return ". ".join(parts) if parts else ""


# ------------------------------------------------------------------
# Meal transformation
# ------------------------------------------------------------------


def transform_meal(meal: dict[str, Any]) -> dict[str, Any]:
    """Transform a TheMealDB meal dict into the format expected by _save_recipe()."""
    tags_raw = (meal.get("strTags") or "").strip()
    dietary_tags = tags_raw if tags_raw else None

    return {
        "title": (meal.get("strMeal") or "Untitled Recipe").strip(),
        "description": _build_description(meal) or None,
        "instructions": (meal.get("strInstructions") or "").strip(),
        "cuisine": (meal.get("strArea") or "").strip() or None,
        "meal_type": (meal.get("strCategory") or "").strip() or None,
        "prep_time_minutes": None,
        "cook_time_minutes": None,
        "servings": None,
        "difficulty": None,
        "dietary_tags": dietary_tags,
        "calorie_estimate": None,
        "ingredients": _extract_ingredients(meal),
        # These are passed as keyword args to _save_recipe(), not in the dict:
        "_image_url": (meal.get("strMealThumb") or "").strip() or None,
    }


# ------------------------------------------------------------------
# API fetching
# ------------------------------------------------------------------


async def fetch_all_meals(
    *,
    delay: float = 0.5,
    timeout: float = 30.0,
) -> list[dict[str, Any]]:
    """Fetch all meals from TheMealDB by iterating the search-by-letter endpoint (a-z).

    Args:
        delay: Seconds to wait between requests (be polite to the API).
        timeout: HTTP request timeout in seconds.

    Returns:
        List of raw TheMealDB meal dicts.
    """
    all_meals: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    async with httpx.AsyncClient(timeout=timeout) as client:
        for letter in "abcdefghijklmnopqrstuvwxyz":
            url = f"{BASE_URL}/search.php?f={letter}"
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json()
            except (httpx.HTTPError, ValueError):
                logger.warning("Failed to fetch letter '%s', skipping", letter)
                continue

            meals = data.get("meals") or []
            for meal in meals:
                meal_id = meal.get("idMeal")
                if meal_id and meal_id not in seen_ids:
                    seen_ids.add(meal_id)
                    all_meals.append(meal)

            if letter != "z":
                await asyncio.sleep(delay)

    logger.info("Fetched %d unique meals from TheMealDB", len(all_meals))
    return all_meals
