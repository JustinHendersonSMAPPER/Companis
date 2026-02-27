"""Test data seeder for E2E tests."""
import uuid
from datetime import datetime, timezone

from app.database import AsyncSession
from app.models.user import User
from app.models.household import Household, FamilyMember
from app.models.ingredient import Ingredient, HouseholdIngredient
from app.utils.security import hash_password


async def seed_e2e_data(session: AsyncSession) -> dict:
    """Seed database with realistic test data. Returns created entity IDs."""
    # Create test user
    user_id = str(uuid.uuid4())
    household_id = str(uuid.uuid4())

    password_hash = hash_password("TestPassword123")

    user = User(
        id=user_id,
        email="e2e-test@companis.app",
        full_name="Test Chef",
        hashed_password=password_hash,
        is_active=True,
        is_verified=True,
        terms_accepted=True,
    )
    session.add(user)
    await session.flush()

    household = Household(
        id=household_id,
        name="Test Kitchen",
        owner_id=user_id,
    )
    session.add(household)
    await session.flush()

    member = FamilyMember(
        id=str(uuid.uuid4()),
        household_id=household_id,
        user_id=user_id,
        name="Test Chef",
        role="owner",
    )
    session.add(member)

    # Add common pantry ingredients
    pantry_items = ["Salt", "Pepper", "Olive Oil", "Garlic", "Onion", "Butter", "Eggs", "Milk", "Flour", "Sugar"]
    for item_name in pantry_items:
        ing_id = str(uuid.uuid4())
        ingredient = Ingredient(id=ing_id, name=item_name, category="Pantry Staple")
        session.add(ingredient)
        await session.flush()

        household_ing = HouseholdIngredient(
            id=str(uuid.uuid4()),
            household_id=household_id,
            ingredient_id=ing_id,
            quantity=1.0,
            unit="pcs",
            source="seed",
            added_by_user_id=user_id,
        )
        session.add(household_ing)

    await session.commit()

    return {
        "user_id": user_id,
        "household_id": household_id,
        "email": "e2e-test@companis.app",
        "password": "TestPassword123",
    }
