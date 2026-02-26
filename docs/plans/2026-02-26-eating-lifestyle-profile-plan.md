# Eating Lifestyle Profile Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a comprehensive eating lifestyle profile system with health conditions, cooking preferences, flavor profiles, and AI prompt integration — transforming SousChefAI from a pantry tracker into a personalized eating lifestyle app.

**Architecture:** Three new database tables (health_conditions, cooking_preferences, flavor_profiles) with corresponding API endpoints, a backend health-condition-to-dietary-instruction mapping service, restructured AI prompt builder, redesigned ProfileView with collapsible sections, and a nudge banner on HomeView. Design doc: `docs/plans/2026-02-26-eating-lifestyle-profile-design.md`.

**Tech Stack:** Python 3.12, FastAPI, async SQLAlchemy (aiosqlite), Pydantic v2, Alembic, Vue 3 Composition API, TypeScript, Pinia

---

## Task 1: Backend Models — HealthCondition, CookingPreferences, FlavorProfile

**Files:**
- Create: `backend/app/models/profile.py`
- Modify: `backend/app/models/__init__.py`
- Modify: `backend/app/models/user.py` (add relationships)
- Test: `backend/tests/unit/test_profile_models.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_profile_models.py`:

```python
from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import CookingPreferences, FlavorProfile, HealthCondition
from app.models.user import User


@pytest.mark.asyncio
class TestHealthConditionModel:
    async def test_create_health_condition(self, db: AsyncSession, test_user: User) -> None:
        condition = HealthCondition(
            user_id=test_user.id,
            condition="high_cholesterol",
            strictness="strict",
        )
        db.add(condition)
        await db.flush()

        result = await db.execute(
            select(HealthCondition).where(HealthCondition.user_id == test_user.id)
        )
        saved = result.scalar_one()
        assert saved.condition == "high_cholesterol"
        assert saved.strictness == "strict"
        assert saved.notes is None
        assert saved.id is not None
        assert saved.created_at is not None
        assert saved.updated_at is not None

    async def test_health_condition_with_notes(self, db: AsyncSession, test_user: User) -> None:
        condition = HealthCondition(
            user_id=test_user.id,
            condition="hypertension",
            strictness="moderate",
            notes="Doctor recommended low sodium",
        )
        db.add(condition)
        await db.flush()

        result = await db.execute(
            select(HealthCondition).where(HealthCondition.user_id == test_user.id)
        )
        saved = result.scalar_one()
        assert saved.notes == "Doctor recommended low sodium"


@pytest.mark.asyncio
class TestCookingPreferencesModel:
    async def test_create_cooking_preferences(self, db: AsyncSession, test_user: User) -> None:
        prefs = CookingPreferences(
            user_id=test_user.id,
            health_importance="somewhat",
            cooking_attitude="its_fine",
            max_prep_time_minutes=30,
            skill_level="intermediate",
            budget_sensitivity="somewhat",
            meal_prep_openness="sometimes",
        )
        db.add(prefs)
        await db.flush()

        result = await db.execute(
            select(CookingPreferences).where(CookingPreferences.user_id == test_user.id)
        )
        saved = result.scalar_one()
        assert saved.cooking_attitude == "its_fine"
        assert saved.max_prep_time_minutes == 30
        assert saved.health_importance == "somewhat"

    async def test_cooking_preferences_nullable_prep_time(self, db: AsyncSession, test_user: User) -> None:
        prefs = CookingPreferences(user_id=test_user.id)
        db.add(prefs)
        await db.flush()

        result = await db.execute(
            select(CookingPreferences).where(CookingPreferences.user_id == test_user.id)
        )
        saved = result.scalar_one()
        assert saved.max_prep_time_minutes is None
        assert saved.cooking_attitude is None


@pytest.mark.asyncio
class TestFlavorProfileModel:
    async def test_create_flavor_profile(self, db: AsyncSession, test_user: User) -> None:
        flavor = FlavorProfile(
            user_id=test_user.id,
            spice_tolerance=2,
            sweetness=3,
            savory_umami=5,
            adventurousness=3,
            richness=4,
            herb_forward=2,
        )
        db.add(flavor)
        await db.flush()

        result = await db.execute(
            select(FlavorProfile).where(FlavorProfile.user_id == test_user.id)
        )
        saved = result.scalar_one()
        assert saved.spice_tolerance == 2
        assert saved.savory_umami == 5
        assert saved.updated_at is not None
```

Note: The `db` and `test_user` fixtures should be available from `conftest.py`. If the existing `conftest.py` does not have a `db` fixture (it uses `client` fixture instead), add these to `backend/tests/conftest.py`:

```python
@pytest.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_factory() as session:
        yield session
        await session.rollback()

@pytest.fixture
async def test_user(db: AsyncSession) -> User:
    from app.models.user import User
    user = User(
        email="testuser@example.com",
        hashed_password="fakehash",
        full_name="Test User",
    )
    db.add(user)
    await db.flush()
    return user
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_profile_models.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.models.profile'`

**Step 3: Write the models**

Create `backend/app/models/profile.py`:

```python
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class HealthCondition(Base):
    __tablename__ = "health_conditions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    condition: Mapped[str] = mapped_column(String(100), nullable=False)
    strictness: Mapped[str] = mapped_column(String(20), nullable=False, default="moderate")
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="health_conditions")


class CookingPreferences(Base):
    __tablename__ = "cooking_preferences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    health_importance: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cooking_attitude: Mapped[str | None] = mapped_column(String(30), nullable=True)
    max_prep_time_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    skill_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    budget_sensitivity: Mapped[str | None] = mapped_column(String(20), nullable=True)
    meal_prep_openness: Mapped[str | None] = mapped_column(String(20), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="cooking_preferences")


class FlavorProfile(Base):
    __tablename__ = "flavor_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    spice_tolerance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sweetness: Mapped[int | None] = mapped_column(Integer, nullable=True)
    savory_umami: Mapped[int | None] = mapped_column(Integer, nullable=True)
    adventurousness: Mapped[int | None] = mapped_column(Integer, nullable=True)
    richness: Mapped[int | None] = mapped_column(Integer, nullable=True)
    herb_forward: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="flavor_profile")
```

Add relationships to `backend/app/models/user.py` User class (after existing relationships):

```python
    health_conditions: Mapped[list["HealthCondition"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    cooking_preferences: Mapped["CookingPreferences | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
    flavor_profile: Mapped["FlavorProfile | None"] = relationship(
        back_populates="user", cascade="all, delete-orphan", uselist=False
    )
```

Add to imports in `backend/app/models/user.py` (TYPE_CHECKING block):

```python
from __future__ import annotations
# existing imports stay, the annotations import handles forward refs
```

Update `backend/app/models/__init__.py`:

```python
from app.models.profile import CookingPreferences, FlavorProfile, HealthCondition
# Add to __all__:
# "CookingPreferences",
# "FlavorProfile",
# "HealthCondition",
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_profile_models.py -v`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add backend/app/models/profile.py backend/app/models/__init__.py backend/app/models/user.py backend/tests/unit/test_profile_models.py backend/tests/conftest.py
git commit -m "feat: add HealthCondition, CookingPreferences, FlavorProfile models"
```

---

## Task 2: Backend — Health Condition to Dietary Mapping Service

**Files:**
- Create: `backend/app/services/health_mapping.py`
- Test: `backend/tests/unit/test_health_mapping.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_health_mapping.py`:

```python
from __future__ import annotations

import pytest

from app.services.health_mapping import (
    CONDITION_DIETARY_MAP,
    get_dietary_instructions,
)


class TestConditionDietaryMap:
    def test_all_conditions_have_entries(self) -> None:
        expected_conditions = [
            "high_cholesterol", "hypertension", "type_2_diabetes", "pre_diabetes",
            "high_triglycerides", "heart_disease", "kidney_concerns", "gout",
            "iron_deficiency", "digestive_sensitivity",
        ]
        for condition in expected_conditions:
            assert condition in CONDITION_DIETARY_MAP, f"Missing mapping for {condition}"

    def test_each_entry_has_required_keys(self) -> None:
        for condition, mapping in CONDITION_DIETARY_MAP.items():
            assert "avoid" in mapping, f"{condition} missing 'avoid'"
            assert "prefer" in mapping, f"{condition} missing 'prefer'"
            assert "ai_note" in mapping, f"{condition} missing 'ai_note'"
            assert isinstance(mapping["avoid"], list)
            assert isinstance(mapping["prefer"], list)
            assert isinstance(mapping["ai_note"], str)


class TestGetDietaryInstructions:
    def test_strict_conditions_in_hard_constraints(self) -> None:
        conditions = [{"condition": "high_cholesterol", "strictness": "strict"}]
        result = get_dietary_instructions(conditions)
        assert len(result["hard_avoid"]) > 0
        assert len(result["hard_prefer"]) > 0
        assert any("saturated fat" in item.lower() for item in result["hard_avoid"])

    def test_moderate_conditions_in_moderate_section(self) -> None:
        conditions = [{"condition": "hypertension", "strictness": "moderate"}]
        result = get_dietary_instructions(conditions)
        assert len(result["moderate_avoid"]) > 0
        assert any("sodium" in item.lower() for item in result["moderate_avoid"])
        assert len(result["hard_avoid"]) == 0

    def test_gentle_conditions_in_soft_section(self) -> None:
        conditions = [{"condition": "gout", "strictness": "gentle"}]
        result = get_dietary_instructions(conditions)
        assert len(result["gentle_notes"]) > 0
        assert len(result["hard_avoid"]) == 0
        assert len(result["moderate_avoid"]) == 0

    def test_multiple_conditions_combined(self) -> None:
        conditions = [
            {"condition": "high_cholesterol", "strictness": "strict"},
            {"condition": "hypertension", "strictness": "moderate"},
        ]
        result = get_dietary_instructions(conditions)
        assert len(result["hard_avoid"]) > 0
        assert len(result["moderate_avoid"]) > 0

    def test_empty_conditions_returns_empty(self) -> None:
        result = get_dietary_instructions([])
        assert result["hard_avoid"] == []
        assert result["hard_prefer"] == []
        assert result["moderate_avoid"] == []
        assert result["moderate_prefer"] == []
        assert result["gentle_notes"] == []

    def test_unknown_condition_skipped(self) -> None:
        conditions = [{"condition": "fake_condition", "strictness": "strict"}]
        result = get_dietary_instructions(conditions)
        assert result["hard_avoid"] == []
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_health_mapping.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write the implementation**

Create `backend/app/services/health_mapping.py`:

```python
"""Maps self-reported health conditions to concrete dietary instructions.

The AI never sees raw condition names — only dietary avoid/prefer lists.
This keeps user health data private and makes AI instructions more reliable
than letting the LLM interpret medical conditions.
"""

from __future__ import annotations

from typing import Any

CONDITION_DIETARY_MAP: dict[str, dict[str, Any]] = {
    "high_cholesterol": {
        "avoid": [
            "high saturated fat ingredients",
            "trans fats",
            "fried foods",
            "fatty red meat",
            "full-fat dairy",
        ],
        "prefer": [
            "lean proteins",
            "fish (especially fatty fish like salmon)",
            "olive oil",
            "nuts and seeds",
            "oats and whole grains",
            "beans and legumes",
        ],
        "ai_note": "Focus on heart-healthy fats (omega-3). Use olive oil instead of butter.",
    },
    "high_triglycerides": {
        "avoid": [
            "added sugars",
            "refined carbohydrates",
            "sugary sauces and glazes",
            "white bread and pastries",
            "sweetened beverages in recipes",
        ],
        "prefer": [
            "whole grains",
            "fatty fish (salmon, mackerel, sardines)",
            "fiber-rich foods",
            "vegetables",
            "legumes",
        ],
        "ai_note": "Minimize simple carbohydrates. Avoid recipes with heavy sugar components.",
    },
    "hypertension": {
        "avoid": [
            "high-sodium ingredients",
            "cured and processed meats",
            "heavy soy sauce usage",
            "pickled foods in large amounts",
            "canned soups or broths (use low-sodium versions)",
        ],
        "prefer": [
            "fresh herbs and spices for flavor instead of salt",
            "potassium-rich foods (bananas, sweet potatoes, spinach)",
            "DASH-diet friendly ingredients",
            "garlic and onions for flavor",
            "citrus juice as seasoning",
        ],
        "ai_note": "Use herbs, spices, and citrus instead of salt for flavor. DASH-diet principles.",
    },
    "type_2_diabetes": {
        "avoid": [
            "high glycemic foods",
            "refined sugars",
            "white bread and white rice in large amounts",
            "sugary sauces and dressings",
            "large portions of starchy foods",
        ],
        "prefer": [
            "low glycemic ingredients",
            "whole grains (brown rice, quinoa, whole wheat)",
            "non-starchy vegetables",
            "lean proteins",
            "healthy fats in moderation",
        ],
        "ai_note": "Balance carbohydrates across the meal. Pair carbs with protein and fiber.",
    },
    "pre_diabetes": {
        "avoid": [
            "refined carbohydrates",
            "sugary foods and dessert-heavy recipes",
            "large portions of starchy foods",
        ],
        "prefer": [
            "whole grains",
            "fiber-rich foods",
            "lean proteins",
            "non-starchy vegetables",
        ],
        "ai_note": "Same direction as diabetes management but less restrictive. Focus on whole foods.",
    },
    "heart_disease": {
        "avoid": [
            "saturated fats",
            "trans fats",
            "excess sodium",
            "fried foods",
            "processed meats",
        ],
        "prefer": [
            "Mediterranean-style ingredients",
            "fish and seafood",
            "fresh vegetables and fruits",
            "whole grains",
            "olive oil",
            "nuts in moderation",
        ],
        "ai_note": "Mediterranean diet principles. Combines cholesterol and blood pressure guidance.",
    },
    "kidney_concerns": {
        "avoid": [
            "very high-potassium foods in excess",
            "high-phosphorus additives",
            "excessive protein portions",
            "high-sodium ingredients",
        ],
        "prefer": [
            "moderate portion sizes",
            "selected fresh vegetables",
            "rice and pasta",
            "egg whites",
        ],
        "ai_note": "Keep portions moderate. Guidance varies by stage — stay general and balanced.",
    },
    "gout": {
        "avoid": [
            "organ meats (liver, kidney)",
            "excessive red meat",
            "shellfish in large amounts",
            "high-fructose ingredients",
            "beer or alcohol-based sauces",
        ],
        "prefer": [
            "low-fat dairy",
            "cherries and berries",
            "vitamin C rich foods",
            "vegetables",
            "whole grains",
        ],
        "ai_note": "Reduce purine-rich foods. Hydration-friendly recipes are a plus.",
    },
    "iron_deficiency": {
        "avoid": [],
        "prefer": [
            "iron-rich foods (lean red meat, spinach, lentils)",
            "fortified grains",
            "pair iron sources with vitamin C (citrus, peppers, tomatoes)",
            "dark leafy greens",
            "beans and legumes",
        ],
        "ai_note": "Include iron-absorption enhancing combos (iron + vitamin C in same meal).",
    },
    "digestive_sensitivity": {
        "avoid": [
            "high-FODMAP foods when possible",
            "very spicy dishes",
            "heavy cream-based sauces",
            "raw cruciferous vegetables in excess",
            "heavily processed foods",
        ],
        "prefer": [
            "cooked vegetables",
            "gentle spices (ginger, turmeric)",
            "easy-to-digest grains (rice, oats)",
            "lean proteins",
            "well-cooked meals over raw preparations",
        ],
        "ai_note": "Keep meals gentle on the stomach. Cooked over raw when possible.",
    },
}


def get_dietary_instructions(
    conditions: list[dict[str, str]],
) -> dict[str, list[str]]:
    """Translate health conditions into tiered dietary instructions.

    Args:
        conditions: List of dicts with 'condition' and 'strictness' keys.

    Returns:
        Dict with keys: hard_avoid, hard_prefer, moderate_avoid,
        moderate_prefer, gentle_notes — each a list of strings.
    """
    result: dict[str, list[str]] = {
        "hard_avoid": [],
        "hard_prefer": [],
        "moderate_avoid": [],
        "moderate_prefer": [],
        "gentle_notes": [],
    }

    for entry in conditions:
        condition = entry.get("condition", "")
        strictness = entry.get("strictness", "moderate")
        mapping = CONDITION_DIETARY_MAP.get(condition)

        if not mapping:
            continue

        if strictness == "strict":
            result["hard_avoid"].extend(mapping["avoid"])
            result["hard_prefer"].extend(mapping["prefer"])
        elif strictness == "moderate":
            result["moderate_avoid"].extend(mapping["avoid"])
            result["moderate_prefer"].extend(mapping["prefer"])
        else:  # gentle
            note = f"{mapping['ai_note']} Prefer: {', '.join(mapping['prefer'][:3])}"
            if mapping["avoid"]:
                note += f". Minimize: {', '.join(mapping['avoid'][:3])}"
            result["gentle_notes"].append(note)

    return result
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_health_mapping.py -v`
Expected: PASS (all 7 tests)

**Step 5: Commit**

```bash
git add backend/app/services/health_mapping.py backend/tests/unit/test_health_mapping.py
git commit -m "feat: add health condition to dietary instruction mapping service"
```

---

## Task 3: Backend — Pydantic Schemas for Profile Endpoints

**Files:**
- Create: `backend/app/schemas/profile.py`
- Test: `backend/tests/unit/test_profile_schemas.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_profile_schemas.py`:

```python
from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.profile import (
    CookingPreferencesResponse,
    CookingPreferencesUpdate,
    FlavorProfileResponse,
    FlavorProfileUpdate,
    HealthConditionCreate,
    HealthConditionResponse,
    HealthConditionUpdate,
    ProfileStalenessResponse,
)


class TestHealthConditionSchemas:
    def test_create_valid(self) -> None:
        schema = HealthConditionCreate(
            condition="high_cholesterol",
            strictness="strict",
        )
        assert schema.condition == "high_cholesterol"
        assert schema.strictness == "strict"
        assert schema.notes is None

    def test_create_with_notes(self) -> None:
        schema = HealthConditionCreate(
            condition="hypertension",
            strictness="moderate",
            notes="Runs in my family",
        )
        assert schema.notes == "Runs in my family"

    def test_create_invalid_condition(self) -> None:
        with pytest.raises(ValidationError):
            HealthConditionCreate(condition="not_a_real_condition", strictness="strict")

    def test_create_invalid_strictness(self) -> None:
        with pytest.raises(ValidationError):
            HealthConditionCreate(condition="high_cholesterol", strictness="maximum")

    def test_update_strictness_only(self) -> None:
        schema = HealthConditionUpdate(strictness="gentle")
        assert schema.strictness == "gentle"
        assert schema.notes is None


class TestCookingPreferencesSchemas:
    def test_update_partial(self) -> None:
        schema = CookingPreferencesUpdate(cooking_attitude="love_it")
        assert schema.cooking_attitude == "love_it"
        assert schema.skill_level is None

    def test_update_invalid_attitude(self) -> None:
        with pytest.raises(ValidationError):
            CookingPreferencesUpdate(cooking_attitude="maybe")

    def test_update_valid_prep_time(self) -> None:
        schema = CookingPreferencesUpdate(max_prep_time_minutes=30)
        assert schema.max_prep_time_minutes == 30


class TestFlavorProfileSchemas:
    def test_update_valid_range(self) -> None:
        schema = FlavorProfileUpdate(spice_tolerance=3, sweetness=1)
        assert schema.spice_tolerance == 3

    def test_update_out_of_range(self) -> None:
        with pytest.raises(ValidationError):
            FlavorProfileUpdate(spice_tolerance=6)

    def test_update_zero_invalid(self) -> None:
        with pytest.raises(ValidationError):
            FlavorProfileUpdate(spice_tolerance=0)


class TestProfileStalenessResponse:
    def test_staleness_structure(self) -> None:
        resp = ProfileStalenessResponse(
            health_conditions_stale=True,
            cooking_preferences_stale=False,
            flavor_profile_stale=False,
            health_conditions_updated_at="2026-01-01T00:00:00",
            cooking_preferences_updated_at=None,
            flavor_profile_updated_at=None,
        )
        assert resp.health_conditions_stale is True
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_profile_schemas.py -v`
Expected: FAIL with `ModuleNotFoundError`

**Step 3: Write the schemas**

Create `backend/app/schemas/profile.py`:

```python
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

VALID_CONDITIONS = [
    "high_cholesterol", "hypertension", "type_2_diabetes", "pre_diabetes",
    "high_triglycerides", "heart_disease", "kidney_concerns", "gout",
    "iron_deficiency", "digestive_sensitivity",
]

VALID_STRICTNESS = ["gentle", "moderate", "strict"]
VALID_COOKING_ATTITUDES = ["love_it", "its_fine", "necessary_evil", "hate_it"]
VALID_SKILL_LEVELS = ["beginner", "intermediate", "advanced"]
VALID_BUDGET_SENSITIVITY = ["not_a_factor", "somewhat", "very_important"]
VALID_MEAL_PREP = ["love_it", "sometimes", "no"]
VALID_HEALTH_IMPORTANCE = ["not_a_priority", "somewhat", "important", "very_important"]


# --- Health Conditions ---

class HealthConditionCreate(BaseModel):
    condition: Literal[
        "high_cholesterol", "hypertension", "type_2_diabetes", "pre_diabetes",
        "high_triglycerides", "heart_disease", "kidney_concerns", "gout",
        "iron_deficiency", "digestive_sensitivity",
    ]
    strictness: Literal["gentle", "moderate", "strict"] = "moderate"
    notes: str | None = None


class HealthConditionUpdate(BaseModel):
    strictness: Literal["gentle", "moderate", "strict"] | None = None
    notes: str | None = None


class HealthConditionResponse(BaseModel):
    id: str
    condition: str
    strictness: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Cooking Preferences ---

class CookingPreferencesUpdate(BaseModel):
    health_importance: Literal["not_a_priority", "somewhat", "important", "very_important"] | None = None
    cooking_attitude: Literal["love_it", "its_fine", "necessary_evil", "hate_it"] | None = None
    max_prep_time_minutes: int | None = Field(default=None, ge=5, le=180)
    skill_level: Literal["beginner", "intermediate", "advanced"] | None = None
    budget_sensitivity: Literal["not_a_factor", "somewhat", "very_important"] | None = None
    meal_prep_openness: Literal["love_it", "sometimes", "no"] | None = None


class CookingPreferencesResponse(BaseModel):
    id: str
    health_importance: str | None
    cooking_attitude: str | None
    max_prep_time_minutes: int | None
    skill_level: str | None
    budget_sensitivity: str | None
    meal_prep_openness: str | None
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Flavor Profile ---

class FlavorProfileUpdate(BaseModel):
    spice_tolerance: int | None = Field(default=None, ge=1, le=5)
    sweetness: int | None = Field(default=None, ge=1, le=5)
    savory_umami: int | None = Field(default=None, ge=1, le=5)
    adventurousness: int | None = Field(default=None, ge=1, le=5)
    richness: int | None = Field(default=None, ge=1, le=5)
    herb_forward: int | None = Field(default=None, ge=1, le=5)


class FlavorProfileResponse(BaseModel):
    id: str
    spice_tolerance: int | None
    sweetness: int | None
    savory_umami: int | None
    adventurousness: int | None
    richness: int | None
    herb_forward: int | None
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Profile Staleness ---

class ProfileStalenessResponse(BaseModel):
    health_conditions_stale: bool
    cooking_preferences_stale: bool
    flavor_profile_stale: bool
    health_conditions_updated_at: str | None
    cooking_preferences_updated_at: str | None
    flavor_profile_updated_at: str | None
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_profile_schemas.py -v`
Expected: PASS (all 11 tests)

**Step 5: Commit**

```bash
git add backend/app/schemas/profile.py backend/tests/unit/test_profile_schemas.py
git commit -m "feat: add Pydantic schemas for profile endpoints"
```

---

## Task 4: Backend — Profile API Endpoints

**Files:**
- Create: `backend/app/api/profile.py`
- Modify: `backend/app/api/__init__.py` or `backend/app/main.py` (register router)
- Test: `backend/tests/integration/test_profile_api.py`

**Step 1: Write the failing test**

Create `backend/tests/integration/test_profile_api.py`:

```python
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthConditionEndpoints:
    async def test_list_empty(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.get("/api/profile/health-conditions", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_add_condition(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.post(
            "/api/profile/health-conditions",
            json={"condition": "high_cholesterol", "strictness": "strict"},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["condition"] == "high_cholesterol"
        assert data["strictness"] == "strict"
        assert "id" in data

    async def test_add_duplicate_condition_rejected(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        await client.post(
            "/api/profile/health-conditions",
            json={"condition": "high_cholesterol", "strictness": "strict"},
            headers=auth_headers,
        )
        resp = await client.post(
            "/api/profile/health-conditions",
            json={"condition": "high_cholesterol", "strictness": "moderate"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_update_strictness(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        create_resp = await client.post(
            "/api/profile/health-conditions",
            json={"condition": "hypertension", "strictness": "strict"},
            headers=auth_headers,
        )
        condition_id = create_resp.json()["id"]
        resp = await client.patch(
            f"/api/profile/health-conditions/{condition_id}",
            json={"strictness": "moderate"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["strictness"] == "moderate"

    async def test_delete_condition(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        create_resp = await client.post(
            "/api/profile/health-conditions",
            json={"condition": "gout", "strictness": "gentle"},
            headers=auth_headers,
        )
        condition_id = create_resp.json()["id"]
        resp = await client.delete(
            f"/api/profile/health-conditions/{condition_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

    async def test_invalid_condition_rejected(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.post(
            "/api/profile/health-conditions",
            json={"condition": "fake_disease", "strictness": "strict"},
            headers=auth_headers,
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestCookingPreferencesEndpoints:
    async def test_get_empty_defaults(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.get("/api/profile/cooking-preferences", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["cooking_attitude"] is None

    async def test_update_preferences(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.patch(
            "/api/profile/cooking-preferences",
            json={"cooking_attitude": "its_fine", "skill_level": "intermediate"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["cooking_attitude"] == "its_fine"
        assert resp.json()["skill_level"] == "intermediate"

    async def test_partial_update_preserves_existing(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        await client.patch(
            "/api/profile/cooking-preferences",
            json={"cooking_attitude": "love_it", "skill_level": "advanced"},
            headers=auth_headers,
        )
        resp = await client.patch(
            "/api/profile/cooking-preferences",
            json={"budget_sensitivity": "somewhat"},
            headers=auth_headers,
        )
        data = resp.json()
        assert data["cooking_attitude"] == "love_it"
        assert data["budget_sensitivity"] == "somewhat"


@pytest.mark.asyncio
class TestFlavorProfileEndpoints:
    async def test_get_empty_defaults(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.get("/api/profile/flavor-profile", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["spice_tolerance"] is None

    async def test_update_flavor_profile(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.patch(
            "/api/profile/flavor-profile",
            json={"spice_tolerance": 2, "savory_umami": 5, "richness": 4},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["spice_tolerance"] == 2
        assert data["savory_umami"] == 5

    async def test_invalid_range_rejected(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.patch(
            "/api/profile/flavor-profile",
            json={"spice_tolerance": 6},
            headers=auth_headers,
        )
        assert resp.status_code == 422


@pytest.mark.asyncio
class TestProfileStaleness:
    async def test_staleness_no_profile_data(self, client: AsyncClient, auth_headers: dict[str, str]) -> None:
        resp = await client.get("/api/profile/staleness", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["health_conditions_stale"] is False
        assert data["cooking_preferences_stale"] is False
        assert data["flavor_profile_stale"] is False
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/integration/test_profile_api.py -v`
Expected: FAIL (404s — routes don't exist yet)

**Step 3: Write the API endpoints**

Create `backend/app/api/profile.py`:

```python
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.profile import CookingPreferences, FlavorProfile, HealthCondition
from app.models.user import User
from app.schemas.profile import (
    CookingPreferencesResponse,
    CookingPreferencesUpdate,
    FlavorProfileResponse,
    FlavorProfileUpdate,
    HealthConditionCreate,
    HealthConditionResponse,
    HealthConditionUpdate,
    ProfileStalenessResponse,
)

router = APIRouter()

HEALTH_STALE_DAYS = 60
GENERAL_STALE_DAYS = 90


# --- Health Conditions ---

@router.get("/health-conditions", response_model=list[HealthConditionResponse])
async def list_health_conditions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[HealthCondition]:
    result = await db.execute(
        select(HealthCondition).where(HealthCondition.user_id == current_user.id)
    )
    return list(result.scalars().all())


@router.post("/health-conditions", response_model=HealthConditionResponse, status_code=status.HTTP_201_CREATED)
async def add_health_condition(
    data: HealthConditionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HealthCondition:
    # Check for duplicate condition
    existing = await db.execute(
        select(HealthCondition).where(
            HealthCondition.user_id == current_user.id,
            HealthCondition.condition == data.condition,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Condition '{data.condition}' already exists",
        )

    condition = HealthCondition(
        user_id=current_user.id,
        condition=data.condition,
        strictness=data.strictness,
        notes=data.notes,
    )
    db.add(condition)
    await db.flush()
    await db.refresh(condition)
    return condition


@router.patch("/health-conditions/{condition_id}", response_model=HealthConditionResponse)
async def update_health_condition(
    condition_id: str,
    data: HealthConditionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> HealthCondition:
    result = await db.execute(
        select(HealthCondition).where(
            HealthCondition.id == condition_id,
            HealthCondition.user_id == current_user.id,
        )
    )
    condition = result.scalar_one_or_none()
    if not condition:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(condition, field, value)

    await db.flush()
    await db.refresh(condition)
    return condition


@router.delete("/health-conditions/{condition_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_health_condition(
    condition_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        delete(HealthCondition).where(
            HealthCondition.id == condition_id,
            HealthCondition.user_id == current_user.id,
        )
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Condition not found")


# --- Cooking Preferences ---

@router.get("/cooking-preferences", response_model=CookingPreferencesResponse)
async def get_cooking_preferences(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CookingPreferences:
    result = await db.execute(
        select(CookingPreferences).where(CookingPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = CookingPreferences(user_id=current_user.id)
        db.add(prefs)
        await db.flush()
        await db.refresh(prefs)
    return prefs


@router.patch("/cooking-preferences", response_model=CookingPreferencesResponse)
async def update_cooking_preferences(
    data: CookingPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CookingPreferences:
    result = await db.execute(
        select(CookingPreferences).where(CookingPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        prefs = CookingPreferences(user_id=current_user.id)
        db.add(prefs)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prefs, field, value)

    await db.flush()
    await db.refresh(prefs)
    return prefs


# --- Flavor Profile ---

@router.get("/flavor-profile", response_model=FlavorProfileResponse)
async def get_flavor_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FlavorProfile:
    result = await db.execute(
        select(FlavorProfile).where(FlavorProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = FlavorProfile(user_id=current_user.id)
        db.add(profile)
        await db.flush()
        await db.refresh(profile)
    return profile


@router.patch("/flavor-profile", response_model=FlavorProfileResponse)
async def update_flavor_profile(
    data: FlavorProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FlavorProfile:
    result = await db.execute(
        select(FlavorProfile).where(FlavorProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        profile = FlavorProfile(user_id=current_user.id)
        db.add(profile)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    await db.flush()
    await db.refresh(profile)
    return profile


# --- Profile Staleness ---

@router.get("/staleness", response_model=ProfileStalenessResponse)
async def get_profile_staleness(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileStalenessResponse:
    now = datetime.now(timezone.utc)

    # Health conditions: stale after 60 days
    hc_result = await db.execute(
        select(HealthCondition.updated_at)
        .where(HealthCondition.user_id == current_user.id)
        .order_by(HealthCondition.updated_at.desc())
        .limit(1)
    )
    hc_updated = hc_result.scalar_one_or_none()
    hc_stale = False
    if hc_updated:
        hc_aware = hc_updated.replace(tzinfo=timezone.utc) if hc_updated.tzinfo is None else hc_updated
        hc_stale = (now - hc_aware) > timedelta(days=HEALTH_STALE_DAYS)

    # Cooking preferences: stale after 90 days
    cp_result = await db.execute(
        select(CookingPreferences.updated_at).where(CookingPreferences.user_id == current_user.id)
    )
    cp_updated = cp_result.scalar_one_or_none()
    cp_stale = False
    if cp_updated:
        cp_aware = cp_updated.replace(tzinfo=timezone.utc) if cp_updated.tzinfo is None else cp_updated
        cp_stale = (now - cp_aware) > timedelta(days=GENERAL_STALE_DAYS)

    # Flavor profile: stale after 90 days
    fp_result = await db.execute(
        select(FlavorProfile.updated_at).where(FlavorProfile.user_id == current_user.id)
    )
    fp_updated = fp_result.scalar_one_or_none()
    fp_stale = False
    if fp_updated:
        fp_aware = fp_updated.replace(tzinfo=timezone.utc) if fp_updated.tzinfo is None else fp_updated
        fp_stale = (now - fp_aware) > timedelta(days=GENERAL_STALE_DAYS)

    return ProfileStalenessResponse(
        health_conditions_stale=hc_stale,
        cooking_preferences_stale=cp_stale,
        flavor_profile_stale=fp_stale,
        health_conditions_updated_at=hc_updated.isoformat() if hc_updated else None,
        cooking_preferences_updated_at=cp_updated.isoformat() if cp_updated else None,
        flavor_profile_updated_at=fp_updated.isoformat() if fp_updated else None,
    )


# --- Confirm Profile (reset nudge timer) ---

@router.post("/confirm-reviewed", status_code=status.HTTP_204_NO_CONTENT)
async def confirm_profile_reviewed(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """User confirms their profile is still accurate. Resets updated_at timestamps."""
    now = datetime.now(timezone.utc)

    await db.execute(
        update(HealthCondition)
        .where(HealthCondition.user_id == current_user.id)
        .values(updated_at=now)
    )
    await db.execute(
        update(CookingPreferences)
        .where(CookingPreferences.user_id == current_user.id)
        .values(updated_at=now)
    )
    await db.execute(
        update(FlavorProfile)
        .where(FlavorProfile.user_id == current_user.id)
        .values(updated_at=now)
    )
    await db.flush()
```

Register the router. Find where other routers are registered (likely `backend/app/main.py` or `backend/app/api/__init__.py`) and add:

```python
from app.api.profile import router as profile_router
app.include_router(profile_router, prefix="/api/profile", tags=["profile"])
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/integration/test_profile_api.py -v`
Expected: PASS (all 13 tests)

**Step 5: Commit**

```bash
git add backend/app/api/profile.py backend/tests/integration/test_profile_api.py
# Also add whatever file was modified to register the router
git commit -m "feat: add profile API endpoints for health conditions, cooking prefs, flavor profile"
```

---

## Task 5: Backend — Update Recipe Service to Collect Full Profile

**Files:**
- Modify: `backend/app/services/recipe.py` (add profile data collection helpers)
- Test: `backend/tests/unit/test_recipe_profile_context.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_recipe_profile_context.py`:

```python
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.profile import CookingPreferences, FlavorProfile, HealthCondition
from app.models.user import User
from app.services.recipe import (
    _get_user_cooking_preferences,
    _get_user_flavor_profile,
    _get_user_health_conditions,
)


@pytest.mark.asyncio
class TestProfileContextCollection:
    async def test_get_health_conditions(self, db: AsyncSession, test_user: User) -> None:
        db.add(HealthCondition(
            user_id=test_user.id, condition="high_cholesterol", strictness="strict",
        ))
        db.add(HealthCondition(
            user_id=test_user.id, condition="hypertension", strictness="moderate",
        ))
        await db.flush()

        conditions = await _get_user_health_conditions(test_user.id, db)
        assert len(conditions) == 2
        assert conditions[0]["condition"] == "high_cholesterol"
        assert conditions[0]["strictness"] == "strict"

    async def test_get_health_conditions_empty(self, db: AsyncSession, test_user: User) -> None:
        conditions = await _get_user_health_conditions(test_user.id, db)
        assert conditions == []

    async def test_get_cooking_preferences(self, db: AsyncSession, test_user: User) -> None:
        db.add(CookingPreferences(
            user_id=test_user.id,
            cooking_attitude="hate_it",
            max_prep_time_minutes=15,
            health_importance="very_important",
        ))
        await db.flush()

        prefs = await _get_user_cooking_preferences(test_user.id, db)
        assert prefs is not None
        assert prefs["cooking_attitude"] == "hate_it"
        assert prefs["max_prep_time_minutes"] == 15

    async def test_get_cooking_preferences_none(self, db: AsyncSession, test_user: User) -> None:
        prefs = await _get_user_cooking_preferences(test_user.id, db)
        assert prefs is None

    async def test_get_flavor_profile(self, db: AsyncSession, test_user: User) -> None:
        db.add(FlavorProfile(
            user_id=test_user.id, spice_tolerance=2, savory_umami=5,
        ))
        await db.flush()

        flavor = await _get_user_flavor_profile(test_user.id, db)
        assert flavor is not None
        assert flavor["spice_tolerance"] == 2
        assert flavor["savory_umami"] == 5

    async def test_get_flavor_profile_none(self, db: AsyncSession, test_user: User) -> None:
        flavor = await _get_user_flavor_profile(test_user.id, db)
        assert flavor is None
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_recipe_profile_context.py -v`
Expected: FAIL with `ImportError` (functions don't exist yet)

**Step 3: Add the helper functions to recipe.py**

Add these functions to `backend/app/services/recipe.py` (near the existing `_get_user_dietary_preferences` and `_get_user_health_goals` helpers):

```python
from app.models.profile import CookingPreferences, FlavorProfile, HealthCondition


async def _get_user_health_conditions(
    user_id: str, db: AsyncSession
) -> list[dict[str, str]]:
    result = await db.execute(
        select(HealthCondition.condition, HealthCondition.strictness).where(
            HealthCondition.user_id == user_id
        )
    )
    return [{"condition": row.condition, "strictness": row.strictness} for row in result.all()]


async def _get_user_cooking_preferences(
    user_id: str, db: AsyncSession
) -> dict[str, Any] | None:
    result = await db.execute(
        select(CookingPreferences).where(CookingPreferences.user_id == user_id)
    )
    prefs = result.scalar_one_or_none()
    if not prefs:
        return None
    return {
        "health_importance": prefs.health_importance,
        "cooking_attitude": prefs.cooking_attitude,
        "max_prep_time_minutes": prefs.max_prep_time_minutes,
        "skill_level": prefs.skill_level,
        "budget_sensitivity": prefs.budget_sensitivity,
        "meal_prep_openness": prefs.meal_prep_openness,
    }


async def _get_user_flavor_profile(
    user_id: str, db: AsyncSession
) -> dict[str, Any] | None:
    result = await db.execute(
        select(FlavorProfile).where(FlavorProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        return None
    return {
        "spice_tolerance": profile.spice_tolerance,
        "sweetness": profile.sweetness,
        "savory_umami": profile.savory_umami,
        "adventurousness": profile.adventurousness,
        "richness": profile.richness,
        "herb_forward": profile.herb_forward,
    }
```

Then update `search_recipes_with_ai()` to collect and pass this data (around line 36-54):

```python
    # Existing context gathering
    available_ingredients = await _get_household_ingredient_names(household_id, db)
    dietary_preferences = await _get_user_dietary_preferences(user_id, db)
    health_goals = await _get_user_health_goals(user_id, db)
    family_notes = await _get_family_dietary_notes(household_id, db)

    # New profile context
    health_conditions = await _get_user_health_conditions(user_id, db)
    cooking_prefs = await _get_user_cooking_preferences(user_id, db)
    flavor_profile = await _get_user_flavor_profile(user_id, db)

    all_dietary = dietary_preferences + dietary_filter

    ai_service = get_ai_service()
    raw_recipes = await ai_service.generate_recipes(
        prompt=prompt,
        available_ingredients=available_ingredients if prefer_available else [],
        dietary_preferences=all_dietary,
        health_goals=health_goals,
        health_conditions=health_conditions,
        cooking_preferences=cooking_prefs,
        flavor_profile=flavor_profile,
        family_dietary_notes=family_notes,
        favorite_cuisines=[],
        max_results=max_results,
        max_prep_time=max_prep_time,
        cuisine=cuisine,
    )
```

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_recipe_profile_context.py -v`
Expected: PASS (all 6 tests)

**Step 5: Commit**

```bash
git add backend/app/services/recipe.py backend/tests/unit/test_recipe_profile_context.py
git commit -m "feat: collect full user profile context for recipe generation"
```

---

## Task 6: Backend — Restructure AI Prompt Builder

**Files:**
- Modify: `backend/app/services/ai/base.py`
- Test: `backend/tests/unit/test_prompt_builder.py`

**Step 1: Write the failing test**

Create `backend/tests/unit/test_prompt_builder.py`:

```python
from __future__ import annotations

from app.services.ai.base import AIService


class ConcreteAIService(AIService):
    """Minimal concrete implementation for testing the prompt builder."""
    async def generate_recipes(self, **kwargs):
        return []
    async def identify_ingredients_from_image(self, image_base64):
        return {"detected_ingredients": [], "confidence_scores": {}}
    async def suggest_substitutions(self, **kwargs):
        return []
    async def parse_voice_input(self, transcript):
        return {"ingredients": []}


class TestBuildRecipePrompt:
    def setup_method(self):
        self.service = ConcreteAIService()

    def test_includes_hard_constraints_for_strict_conditions(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="healthy dinner",
            available_ingredients=[],
            dietary_preferences=["nuts"],
            health_goals=[],
            health_conditions=[{"condition": "high_cholesterol", "strictness": "strict"}],
            cooking_preferences=None,
            flavor_profile=None,
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=3,
            max_prep_time=None,
            cuisine=None,
        )
        assert "ABSOLUTE CONSTRAINTS" in prompt
        assert "saturated fat" in prompt.lower()

    def test_includes_moderate_conditions_section(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="dinner",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            health_conditions=[{"condition": "hypertension", "strictness": "moderate"}],
            cooking_preferences=None,
            flavor_profile=None,
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=3,
            max_prep_time=None,
            cuisine=None,
        )
        assert "MODERATE" in prompt
        assert "sodium" in prompt.lower()

    def test_includes_cooking_preferences(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="dinner",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            health_conditions=[],
            cooking_preferences={
                "health_importance": "very_important",
                "cooking_attitude": "hate_it",
                "max_prep_time_minutes": 15,
                "skill_level": "beginner",
                "budget_sensitivity": "very_important",
                "meal_prep_openness": "no",
            },
            flavor_profile=None,
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=3,
            max_prep_time=None,
            cuisine=None,
        )
        assert "USER PROFILE" in prompt
        assert "hate_it" in prompt or "minimum effort" in prompt.lower()
        assert "beginner" in prompt.lower()
        assert "budget" in prompt.lower()

    def test_includes_flavor_profile(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="dinner",
            available_ingredients=[],
            dietary_preferences=[],
            health_goals=[],
            health_conditions=[],
            cooking_preferences=None,
            flavor_profile={
                "spice_tolerance": 1,
                "sweetness": 3,
                "savory_umami": 5,
                "adventurousness": 2,
                "richness": 4,
                "herb_forward": 2,
            },
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=3,
            max_prep_time=None,
            cuisine=None,
        )
        assert "FLAVOR PREFERENCES" in prompt
        assert "Spice" in prompt
        assert "5" in prompt  # savory_umami value

    def test_empty_profile_still_generates_valid_prompt(self) -> None:
        prompt = self.service._build_recipe_prompt(
            prompt="quick lunch",
            available_ingredients=["chicken", "rice"],
            dietary_preferences=[],
            health_goals=[],
            health_conditions=[],
            cooking_preferences=None,
            flavor_profile=None,
            family_dietary_notes=[],
            favorite_cuisines=[],
            max_results=5,
            max_prep_time=None,
            cuisine=None,
        )
        assert "quick lunch" in prompt
        assert "chicken" in prompt
        assert "JSON" in prompt
```

**Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/unit/test_prompt_builder.py -v`
Expected: FAIL (signature mismatch — new params don't exist yet)

**Step 3: Update the prompt builder**

Modify `backend/app/services/ai/base.py` — update `_build_recipe_prompt()` signature and body:

```python
from app.services.health_mapping import get_dietary_instructions

def _build_recipe_prompt(
    self,
    prompt: str,
    available_ingredients: list[str],
    dietary_preferences: list[str],
    health_goals: list[str],
    health_conditions: list[dict[str, str]] | None = None,
    cooking_preferences: dict[str, Any] | None = None,
    flavor_profile: dict[str, Any] | None = None,
    family_dietary_notes: list[str] | None = None,
    favorite_cuisines: list[str] | None = None,
    max_results: int = 5,
    max_prep_time: int | None = None,
    cuisine: str | None = None,
) -> str:
    parts = []

    parts.append("You are SousChefAI, an expert cooking assistant that creates personalized recipes.")
    parts.append(f"\nUSER REQUEST: {prompt}")

    # === ABSOLUTE CONSTRAINTS ===
    hard_constraints = []
    if dietary_preferences:
        hard_constraints.append(
            "*** CRITICAL SAFETY REQUIREMENT - ALLERGIES AND DIETARY RESTRICTIONS ***\n"
            f"Dietary restrictions: {', '.join(dietary_preferences)}\n"
            "Allergies are ABSOLUTE - NEVER include any ingredient that a user or family member "
            "is allergic to, not even as an optional ingredient or substitution.\n"
            "Failure to respect these could cause serious harm."
        )

    if health_conditions:
        dietary_instructions = get_dietary_instructions(health_conditions)
        if dietary_instructions["hard_avoid"]:
            hard_constraints.append(
                "Strict health dietary constraints (MUST respect):\n"
                f"AVOID: {', '.join(dietary_instructions['hard_avoid'])}\n"
                f"PREFER: {', '.join(dietary_instructions['hard_prefer'])}"
            )

    if hard_constraints:
        parts.append("\n=== ABSOLUTE CONSTRAINTS (NEVER VIOLATE) ===")
        parts.extend(hard_constraints)

    # === MODERATE HEALTH CONDITIONS ===
    if health_conditions:
        dietary_instructions = get_dietary_instructions(health_conditions)
        if dietary_instructions["moderate_avoid"]:
            parts.append("\n=== HEALTH CONDITIONS (MODERATE - PREFER TO AVOID) ===")
            parts.append(
                f"Prefer to avoid: {', '.join(dietary_instructions['moderate_avoid'])}\n"
                f"Prefer to include: {', '.join(dietary_instructions['moderate_prefer'])}"
            )

    # === USER PROFILE ===
    if cooking_preferences:
        parts.append("\n=== USER PROFILE ===")
        cp = cooking_preferences
        if cp.get("health_importance"):
            parts.append(f"Healthy eating importance: {cp['health_importance']}")
        if cp.get("cooking_attitude"):
            attitude_desc = {
                "love_it": "Loves cooking - complex recipes welcome",
                "its_fine": "Cooking is fine - reasonable effort recipes",
                "necessary_evil": "Cooking is a chore - keep it simple and quick",
                "hate_it": "Hates cooking - absolute minimum effort, fewest steps possible",
            }
            parts.append(f"Cooking attitude: {attitude_desc.get(cp['cooking_attitude'], cp['cooking_attitude'])}")
        if cp.get("max_prep_time_minutes"):
            parts.append(f"Max prep+cook time: {cp['max_prep_time_minutes']} minutes")
        if cp.get("skill_level"):
            skill_desc = {
                "beginner": "Beginner - basic techniques only, clear instructions needed",
                "intermediate": "Intermediate - comfortable with most techniques",
                "advanced": "Advanced - any technique or complexity is fine",
            }
            parts.append(f"Skill level: {skill_desc.get(cp['skill_level'], cp['skill_level'])}")
        if cp.get("budget_sensitivity"):
            budget_desc = {
                "not_a_factor": "Budget is not a concern",
                "somewhat": "Prefers affordable ingredients when possible",
                "very_important": "Budget-focused - use affordable, common ingredients",
            }
            parts.append(f"Budget: {budget_desc.get(cp['budget_sensitivity'], cp['budget_sensitivity'])}")
        if cp.get("meal_prep_openness"):
            prep_desc = {
                "love_it": "Loves batch cooking and meal prep",
                "sometimes": "Open to meal prep for busy weeks",
                "no": "Prefers cooking fresh each time",
            }
            parts.append(f"Meal prep: {prep_desc.get(cp['meal_prep_openness'], cp['meal_prep_openness'])}")

    # === FLAVOR PREFERENCES ===
    if flavor_profile:
        fp = flavor_profile
        has_any = any(fp.get(k) is not None for k in [
            "spice_tolerance", "sweetness", "savory_umami",
            "adventurousness", "richness", "herb_forward",
        ])
        if has_any:
            parts.append("\n=== FLAVOR PREFERENCES (1=low, 5=high) ===")
            labels = {
                "spice_tolerance": "Spice tolerance",
                "sweetness": "Sweetness preference",
                "savory_umami": "Savory/Umami love",
                "adventurousness": "Adventurousness",
                "richness": "Richness (light to hearty)",
                "herb_forward": "Herb-forward preference",
            }
            for key, label in labels.items():
                val = fp.get(key)
                if val is not None:
                    parts.append(f"{label}: {val}/5")

    # === SOFT PREFERENCES ===
    soft_parts = []
    if health_goals:
        soft_parts.append(f"Health goals (give preference to): {', '.join(health_goals)}")
    if health_conditions:
        dietary_instructions = get_dietary_instructions(health_conditions)
        if dietary_instructions["gentle_notes"]:
            soft_parts.append(f"Gentle health notes: {'; '.join(dietary_instructions['gentle_notes'])}")
    if family_dietary_notes:
        soft_parts.append(
            "Family member dietary notes (MUST respect - these may include allergies): "
            + "; ".join(family_dietary_notes)
        )
    if favorite_cuisines:
        soft_parts.append(f"Preferred cuisines: {', '.join(favorite_cuisines)}")

    if soft_parts:
        parts.append("\n=== SOFT PREFERENCES ===")
        parts.extend(soft_parts)

    # === AVAILABLE INGREDIENTS ===
    if available_ingredients:
        parts.append(f"\nAvailable ingredients in pantry: {', '.join(available_ingredients)}")
        parts.append("Prefer recipes using these ingredients when possible.")

    # === FILTERS ===
    if max_prep_time:
        parts.append(f"\nMaximum total prep+cook time: {max_prep_time} minutes")
    if cuisine:
        parts.append(f"Cuisine filter: {cuisine}")

    # === OUTPUT FORMAT ===
    parts.append(f"\nReturn exactly {max_results} recipes as a JSON array.")
    parts.append(
        "Each recipe object must have: title, description, instructions, "
        "cuisine, meal_type, prep_time_minutes, cook_time_minutes, servings, "
        "difficulty, dietary_tags (comma-separated string), calorie_estimate (integer), "
        "and ingredients (array of objects with name, quantity, unit, is_optional, substitution_notes)."
    )
    parts.append(
        "For each ingredient, if a good substitution exists, include it in substitution_notes."
    )
    parts.append("Respond with ONLY the JSON array, no other text.")

    return "\n".join(parts)
```

Also update the `generate_recipes` abstract method signature and all concrete implementations (Ollama, Anthropic, OpenAI, Claude Local) to accept the new parameters and pass them through to `_build_recipe_prompt`. The concrete implementations just pass `**kwargs` through to the prompt builder, so add the new params to their signatures.

**Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/unit/test_prompt_builder.py -v`
Expected: PASS (all 5 tests)

**Step 5: Commit**

```bash
git add backend/app/services/ai/base.py backend/app/services/recipe.py backend/tests/unit/test_prompt_builder.py
# Also add any modified AI provider files (ollama.py, anthropic.py, etc.)
git commit -m "feat: restructure AI prompt builder with full profile context"
```

---

## Task 7: Frontend — TypeScript Types and API Functions

**Files:**
- Modify: `frontend/src/types/index.ts`
- Modify: `frontend/src/services/api.ts`

**Step 1: Add new types to `frontend/src/types/index.ts`**

Add at the end of the file, before the final export:

```typescript
// --- Eating Lifestyle Profile ---

export interface HealthCondition {
  id: string;
  condition: string;
  strictness: string; // "gentle" | "moderate" | "strict"
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CookingPreferencesData {
  id: string;
  health_importance: string | null;
  cooking_attitude: string | null;
  max_prep_time_minutes: number | null;
  skill_level: string | null;
  budget_sensitivity: string | null;
  meal_prep_openness: string | null;
  updated_at: string;
}

export interface FlavorProfileData {
  id: string;
  spice_tolerance: number | null;
  sweetness: number | null;
  savory_umami: number | null;
  adventurousness: number | null;
  richness: number | null;
  herb_forward: number | null;
  updated_at: string;
}

export interface ProfileStaleness {
  health_conditions_stale: boolean;
  cooking_preferences_stale: boolean;
  flavor_profile_stale: boolean;
  health_conditions_updated_at: string | null;
  cooking_preferences_updated_at: string | null;
  flavor_profile_updated_at: string | null;
}
```

**Step 2: Add API functions to `frontend/src/services/api.ts`**

Add a new `profileApi` group after the existing `usersApi`:

```typescript
import type {
  HealthCondition,
  CookingPreferencesData,
  FlavorProfileData,
  ProfileStaleness,
} from "@/types";

export const profileApi = {
  // Health conditions
  getHealthConditions: () =>
    api.get<HealthCondition[]>("/profile/health-conditions"),
  addHealthCondition: (data: { condition: string; strictness?: string; notes?: string }) =>
    api.post<HealthCondition>("/profile/health-conditions", data),
  updateHealthCondition: (id: string, data: { strictness?: string; notes?: string }) =>
    api.patch<HealthCondition>(`/profile/health-conditions/${id}`, data),
  removeHealthCondition: (id: string) =>
    api.delete(`/profile/health-conditions/${id}`),

  // Cooking preferences
  getCookingPreferences: () =>
    api.get<CookingPreferencesData>("/profile/cooking-preferences"),
  updateCookingPreferences: (data: Partial<Omit<CookingPreferencesData, "id" | "updated_at">>) =>
    api.patch<CookingPreferencesData>("/profile/cooking-preferences", data),

  // Flavor profile
  getFlavorProfile: () =>
    api.get<FlavorProfileData>("/profile/flavor-profile"),
  updateFlavorProfile: (data: Partial<Omit<FlavorProfileData, "id" | "updated_at">>) =>
    api.patch<FlavorProfileData>("/profile/flavor-profile", data),

  // Staleness & confirmation
  getStaleness: () =>
    api.get<ProfileStaleness>("/profile/staleness"),
  confirmReviewed: () =>
    api.post("/profile/confirm-reviewed"),
};
```

**Step 3: Commit**

```bash
git add frontend/src/types/index.ts frontend/src/services/api.ts
git commit -m "feat: add TypeScript types and API functions for eating lifestyle profile"
```

---

## Task 8: Frontend — Redesign ProfileView with Collapsible Sections

**Files:**
- Modify: `frontend/src/views/ProfileView.vue`
- Test: `frontend/src/views/__tests__/ProfileView.spec.ts` (if tests exist, update; otherwise create basic smoke test)

This is the largest frontend task. The ProfileView gets redesigned with collapsible sections for:
1. Your Priorities (health importance)
2. Health Conditions (checklist + strictness)
3. Cooking Style (attitude, time, skill)
4. Budget & Meal Prep
5. Flavor Profile (sliders)
6. Dietary Preferences (existing, moved here)
7. Health Goals (existing, moved here)

**Step 1: Write ProfileView.vue**

Rewrite `frontend/src/views/ProfileView.vue`. The component should:

- Import `profileApi` alongside existing `usersApi`
- Import all new types: `HealthCondition`, `CookingPreferencesData`, `FlavorProfileData`
- Use reactive refs for each section's data
- Load all sections in `onMounted` (parallel API calls)
- Each section is a collapsible `<details>` element with `<summary>`
- Health conditions section shows the medication info note
- Cooking preferences use radio button groups
- Flavor profile uses `<input type="range" min="1" max="5">`
- Auto-save: use `watch` with `debounce` for sliders, immediate saves for radio/checkbox changes
- Section headers show completion count

Key implementation patterns to follow (from existing codebase):
- Use `const { data } = await profileApi.getCookingPreferences()` pattern
- Use `ref<Type>()` for reactive state
- Error handling: `try/catch` with `error.value = "message"`
- Form validation: check required fields before API calls

The health conditions checklist should include this info note in the template:

```html
<div class="info-note">
  <p>
    <strong>Note:</strong> If you take medication for any of these conditions,
    you should still mark them. Medication manages symptoms but dietary choices
    still matter for your long-term health.
  </p>
</div>
```

Predefined conditions array for the checklist:

```typescript
const availableConditions = [
  { key: "high_cholesterol", label: "High Cholesterol" },
  { key: "hypertension", label: "High Blood Pressure / Hypertension" },
  { key: "type_2_diabetes", label: "Type 2 Diabetes" },
  { key: "pre_diabetes", label: "Pre-diabetes" },
  { key: "high_triglycerides", label: "High Triglycerides" },
  { key: "heart_disease", label: "Heart Disease" },
  { key: "kidney_concerns", label: "Kidney Concerns" },
  { key: "gout", label: "Gout" },
  { key: "iron_deficiency", label: "Iron Deficiency / Anemia" },
  { key: "digestive_sensitivity", label: "IBS / Digestive Sensitivity" },
] as const;
```

**Step 2: Run frontend type check**

Run: `cd frontend && npx vue-tsc --noEmit`
Expected: PASS (no type errors)

**Step 3: Run frontend lint**

Run: `cd frontend && npm run lint:check`
Expected: PASS

**Step 4: Commit**

```bash
git add frontend/src/views/ProfileView.vue
git commit -m "feat: redesign ProfileView with collapsible eating lifestyle sections"
```

---

## Task 9: Frontend — Nudge Banner on HomeView

**Files:**
- Create: `frontend/src/components/common/ProfileNudgeBanner.vue`
- Modify: `frontend/src/views/HomeView.vue`

**Step 1: Create ProfileNudgeBanner component**

Create `frontend/src/components/common/ProfileNudgeBanner.vue`:

```vue
<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { profileApi } from "@/services/api";
import type { ProfileStaleness } from "@/types";

const router = useRouter();
const visible = ref(false);
const staleness = ref<ProfileStaleness | null>(null);

const DISMISS_KEY = "profile_nudge_dismissed_at";

onMounted(async () => {
  // Check if dismissed recently (3 days)
  const dismissedAt = localStorage.getItem(DISMISS_KEY);
  if (dismissedAt) {
    const dismissDate = new Date(dismissedAt);
    const threeDaysAgo = new Date(Date.now() - 3 * 24 * 60 * 60 * 1000);
    if (dismissDate > threeDaysAgo) return;
  }

  try {
    const { data } = await profileApi.getStaleness();
    staleness.value = data;
    visible.value =
      data.health_conditions_stale ||
      data.cooking_preferences_stale ||
      data.flavor_profile_stale;
  } catch {
    // Silently fail — nudge is non-critical
  }
});

async function confirmAllGood(): Promise<void> {
  try {
    await profileApi.confirmReviewed();
    visible.value = false;
  } catch {
    visible.value = false;
  }
}

function reviewProfile(): void {
  visible.value = false;
  void router.push("/profile");
}

function dismiss(): void {
  localStorage.setItem(DISMISS_KEY, new Date().toISOString());
  visible.value = false;
}
</script>

<template>
  <div v-if="visible" class="nudge-banner">
    <p>Your eating profile was last updated a while ago. Still accurate?</p>
    <div class="nudge-actions">
      <button class="btn-secondary" @click="confirmAllGood">Yes, all good</button>
      <button class="btn-primary" @click="reviewProfile">Review it</button>
      <button class="btn-dismiss" @click="dismiss" aria-label="Dismiss">&times;</button>
    </div>
  </div>
</template>
```

**Step 2: Add to HomeView**

In `frontend/src/views/HomeView.vue`, import and add the component:

```typescript
import ProfileNudgeBanner from "@/components/common/ProfileNudgeBanner.vue";
```

Add to template (at the top, before the search area):

```html
<ProfileNudgeBanner />
```

**Step 3: Run frontend checks**

Run: `cd frontend && npx vue-tsc --noEmit && npm run lint:check`
Expected: PASS

**Step 4: Commit**

```bash
git add frontend/src/components/common/ProfileNudgeBanner.vue frontend/src/views/HomeView.vue
git commit -m "feat: add profile nudge banner to HomeView"
```

---

## Task 10: Alembic Migration

**Files:**
- Create: `backend/alembic/versions/<auto>_add_profile_tables.py` (auto-generated)

**Step 1: Generate migration**

```bash
cd backend && alembic revision --autogenerate -m "add health_conditions cooking_preferences flavor_profiles tables"
```

**Step 2: Review the generated migration**

Read the generated file in `backend/alembic/versions/`. Verify it creates three tables with the correct columns.

**Step 3: Apply migration**

```bash
cd backend && alembic upgrade head
```

**Step 4: Commit**

```bash
git add backend/alembic/versions/
git commit -m "chore: add alembic migration for profile tables"
```

---

## Task 11: Integration Test — Full Flow

**Files:**
- Test: `backend/tests/integration/test_profile_recipe_flow.py`

**Step 1: Write end-to-end test**

Create `backend/tests/integration/test_profile_recipe_flow.py`:

```python
from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestProfileRecipeFlow:
    """Test that profile data flows through to recipe generation."""

    async def test_set_profile_and_search_recipes(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        # Set up health conditions
        await client.post(
            "/api/profile/health-conditions",
            json={"condition": "high_cholesterol", "strictness": "strict"},
            headers=auth_headers,
        )

        # Set up cooking preferences
        await client.patch(
            "/api/profile/cooking-preferences",
            json={
                "health_importance": "very_important",
                "cooking_attitude": "its_fine",
                "max_prep_time_minutes": 30,
                "skill_level": "intermediate",
                "budget_sensitivity": "somewhat",
            },
            headers=auth_headers,
        )

        # Set up flavor profile
        await client.patch(
            "/api/profile/flavor-profile",
            json={"spice_tolerance": 3, "savory_umami": 5, "richness": 4},
            headers=auth_headers,
        )

        # Verify all data persists
        hc_resp = await client.get("/api/profile/health-conditions", headers=auth_headers)
        assert len(hc_resp.json()) == 1
        assert hc_resp.json()[0]["condition"] == "high_cholesterol"

        cp_resp = await client.get("/api/profile/cooking-preferences", headers=auth_headers)
        assert cp_resp.json()["cooking_attitude"] == "its_fine"

        fp_resp = await client.get("/api/profile/flavor-profile", headers=auth_headers)
        assert fp_resp.json()["savory_umami"] == 5

    async def test_staleness_check(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        resp = await client.get("/api/profile/staleness", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # No data = not stale (nothing to be stale about)
        assert data["health_conditions_stale"] is False

    async def test_confirm_reviewed(
        self, client: AsyncClient, auth_headers: dict[str, str]
    ) -> None:
        resp = await client.post("/api/profile/confirm-reviewed", headers=auth_headers)
        assert resp.status_code == 204
```

**Step 2: Run the test**

Run: `cd backend && python -m pytest tests/integration/test_profile_recipe_flow.py -v`
Expected: PASS

**Step 3: Run full test suite**

Run: `cd backend && python -m pytest -v`
Expected: ALL PASS (no regressions)

**Step 4: Commit**

```bash
git add backend/tests/integration/test_profile_recipe_flow.py
git commit -m "test: add integration test for full profile-to-recipe flow"
```

---

## Task 12: Final — Lint, Type Check, Full Test Run

**Step 1: Backend checks**

```bash
cd backend && ruff check . && ruff format --check . && python -m pytest -v
```

**Step 2: Frontend checks**

```bash
cd frontend && npm run lint:check && npm run type-check
```

**Step 3: Fix any issues found**

**Step 4: Final commit**

```bash
git commit -m "chore: fix lint and type check issues"
```
