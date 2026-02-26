#!/usr/bin/env python3
"""Bulk-import recipes from TheMealDB into the Companis database.

Usage:
    python scripts/import_mealdb.py              # full import
    python scripts/import_mealdb.py --dry-run    # fetch + transform, no DB writes
    python scripts/import_mealdb.py --delay=1.0  # slower API polling
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Ensure the backend package is importable when running from the backend dir
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.models.recipe import Recipe
from app.services.mealdb import fetch_all_meals, transform_meal
from app.services.recipe import _save_recipe


async def _import(*, dry_run: bool, delay: float) -> None:
    settings = get_settings()
    db_url = settings.database_url
    print(f"Database: {db_url}")
    print(f"Dry run: {dry_run}")
    print(f"API delay: {delay}s")
    print()

    # Fetch all meals from TheMealDB
    print("Fetching meals from TheMealDB (a-z)...")
    raw_meals = await fetch_all_meals(delay=delay)
    print(f"Fetched {len(raw_meals)} unique meals")
    print()

    if not raw_meals:
        print("No meals fetched. Exiting.")
        return

    engine = create_async_engine(db_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    saved = 0
    skipped = 0
    errors = 0

    async with session_factory() as db:
        for i, meal in enumerate(raw_meals, 1):
            title = (meal.get("strMeal") or "Untitled").strip()
            try:
                # Check for duplicates
                existing = await db.execute(
                    select(Recipe.id).where(
                        Recipe.title == title,
                        Recipe.source == "themealdb",
                    )
                )
                if existing.scalar_one_or_none() is not None:
                    print(f"  [{i}/{len(raw_meals)}] SKIP (exists): {title}")
                    skipped += 1
                    continue

                raw = transform_meal(meal)
                image_url = raw.pop("_image_url", None)

                if dry_run:
                    ing_count = len(raw.get("ingredients", []))
                    print(f"  [{i}/{len(raw_meals)}] DRY-RUN OK: {title} ({ing_count} ingredients)")
                    saved += 1
                    continue

                await _save_recipe(raw, db, source="themealdb", image_url=image_url)
                print(f"  [{i}/{len(raw_meals)}] OK: {title}")
                saved += 1

            except Exception as exc:
                print(f"  [{i}/{len(raw_meals)}] ERROR: {title} — {exc}")
                errors += 1

        if not dry_run and saved > 0:
            await db.commit()
            print()
            print("Committed to database.")

    await engine.dispose()

    print()
    print("=" * 50)
    print(f"  Total fetched:  {len(raw_meals)}")
    print(f"  Saved:          {saved}")
    print(f"  Skipped (dup):  {skipped}")
    print(f"  Errors:         {errors}")
    print("=" * 50)


def main() -> None:
    parser = argparse.ArgumentParser(description="Import recipes from TheMealDB")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and transform without saving to the database",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.5,
        help="Delay between API requests in seconds (default: 0.5)",
    )
    args = parser.parse_args()
    asyncio.run(_import(dry_run=args.dry_run, delay=args.delay))


if __name__ == "__main__":
    main()
