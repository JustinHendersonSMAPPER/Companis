from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.ingredient import (
    BarcodeScanResult,
    CameraScanResult,
    HouseholdIngredientAdd,
    IngredientCreate,
)
from app.schemas.recipe import RecipeRatingCreate, RecipeSearchRequest, SubstitutionSuggestion
from app.schemas.shopping import ShoppingCartItemAdd
from app.schemas.user import UserCreate


class TestUserCreate:
    def test_valid_user_create(self) -> None:
        user = UserCreate(
            email="test@example.com",
            password="password123",
            full_name="Test User",
            terms_accepted=True,
        )
        assert user.email == "test@example.com"
        assert user.full_name == "Test User"
        assert user.terms_accepted is True

    def test_password_too_short(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="short",
                full_name="Test User",
                terms_accepted=True,
            )

    def test_invalid_email(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(
                email="not-an-email",
                password="password123",
                full_name="Test User",
                terms_accepted=True,
            )

    def test_empty_full_name(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="password123",
                full_name="",
                terms_accepted=True,
            )

    def test_terms_accepted_required(self) -> None:
        with pytest.raises(ValidationError):
            UserCreate(
                email="test@example.com",
                password="password123",
                full_name="Test User",
            )  # type: ignore[call-arg]


class TestRecipeRatingCreate:
    def test_valid_rating(self) -> None:
        rating = RecipeRatingCreate(score=4, review="Great recipe!")
        assert rating.score == 4

    def test_rating_too_low(self) -> None:
        with pytest.raises(ValidationError):
            RecipeRatingCreate(score=0)

    def test_rating_too_high(self) -> None:
        with pytest.raises(ValidationError):
            RecipeRatingCreate(score=6)

    def test_rating_no_review(self) -> None:
        rating = RecipeRatingCreate(score=3)
        assert rating.review is None


class TestRecipeSearchRequest:
    def test_valid_search(self) -> None:
        search = RecipeSearchRequest(prompt="Thai food")
        assert search.prompt == "Thai food"
        assert search.max_results == 5
        assert search.prefer_available_ingredients is True

    def test_empty_prompt(self) -> None:
        with pytest.raises(ValidationError):
            RecipeSearchRequest(prompt="")

    def test_max_results_bounds(self) -> None:
        with pytest.raises(ValidationError):
            RecipeSearchRequest(prompt="food", max_results=0)
        with pytest.raises(ValidationError):
            RecipeSearchRequest(prompt="food", max_results=25)

    def test_dietary_filter_list(self) -> None:
        search = RecipeSearchRequest(prompt="dinner", dietary_filter=["vegan", "gluten-free"])
        assert len(search.dietary_filter) == 2


class TestIngredientCreate:
    def test_valid_ingredient(self) -> None:
        ing = IngredientCreate(name="Chicken Breast")
        assert ing.name == "Chicken Breast"
        assert ing.category is None

    def test_ingredient_with_barcode(self) -> None:
        ing = IngredientCreate(name="Milk", barcode="1234567890")
        assert ing.barcode == "1234567890"


class TestHouseholdIngredientAdd:
    def test_add_by_name(self) -> None:
        item = HouseholdIngredientAdd(name="Sugar", quantity=2.0, unit="cups")
        assert item.name == "Sugar"
        assert item.source == "manual"

    def test_add_by_barcode(self) -> None:
        item = HouseholdIngredientAdd(barcode="1234567890", source="barcode")
        assert item.barcode == "1234567890"
        assert item.source == "barcode"


class TestShoppingCartItemAdd:
    def test_valid_item(self) -> None:
        item = ShoppingCartItemAdd(name="Milk", quantity=1.0, unit="gallon")
        assert item.name == "Milk"

    def test_item_minimal(self) -> None:
        item = ShoppingCartItemAdd(name="Eggs")
        assert item.quantity is None
        assert item.unit is None


class TestBarcodeScanResult:
    def test_found_result(self) -> None:
        result = BarcodeScanResult(
            barcode="123", ingredient=None, product_name="Milk", brand="Brand", found=True
        )
        assert result.found is True

    def test_not_found_result(self) -> None:
        result = BarcodeScanResult(
            barcode="123", ingredient=None, product_name=None, brand=None, found=False
        )
        assert result.found is False


class TestCameraScanResult:
    def test_scan_result(self) -> None:
        result = CameraScanResult(
            detected_ingredients=["tomato", "onion"],
            confidence_scores={"tomato": 0.95, "onion": 0.8},
        )
        assert len(result.detected_ingredients) == 2
        assert result.confidence_scores["tomato"] == 0.95


class TestSubstitutionSuggestion:
    def test_substitution(self) -> None:
        sub = SubstitutionSuggestion(
            original_ingredient="butter",
            substitute="coconut oil",
            notes="Use same amount",
            ratio="1:1",
        )
        assert sub.substitute == "coconut oil"
