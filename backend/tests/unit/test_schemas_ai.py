"""Unit tests for AI-related Pydantic schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.schemas.ai import (
    ParsedIngredient,
    SubstitutionRequest,
    SubstitutionResponse,
    VoiceInputRequest,
    VoiceInputResponse,
)


class TestVoiceInputRequest:
    def test_valid_request(self) -> None:
        req = VoiceInputRequest(transcript="two cups of flour")
        assert req.transcript == "two cups of flour"

    def test_empty_transcript(self) -> None:
        req = VoiceInputRequest(transcript="")
        assert req.transcript == ""

    def test_missing_transcript_raises(self) -> None:
        with pytest.raises(ValidationError):
            VoiceInputRequest()  # type: ignore[call-arg]


class TestParsedIngredient:
    def test_full_ingredient(self) -> None:
        ing = ParsedIngredient(name="flour", quantity=2.0, unit="cups")
        assert ing.name == "flour"
        assert ing.quantity == 2.0
        assert ing.unit == "cups"

    def test_name_only(self) -> None:
        ing = ParsedIngredient(name="salt")
        assert ing.name == "salt"
        assert ing.quantity is None
        assert ing.unit is None

    def test_missing_name_raises(self) -> None:
        with pytest.raises(ValidationError):
            ParsedIngredient()  # type: ignore[call-arg]


class TestVoiceInputResponse:
    def test_with_ingredients(self) -> None:
        resp = VoiceInputResponse(
            ingredients=[
                ParsedIngredient(name="flour", quantity=2, unit="cups"),
                ParsedIngredient(name="eggs", quantity=3),
            ]
        )
        assert len(resp.ingredients) == 2
        assert resp.ingredients[0].name == "flour"

    def test_empty_ingredients(self) -> None:
        resp = VoiceInputResponse(ingredients=[])
        assert len(resp.ingredients) == 0


class TestSubstitutionRequest:
    def test_full_request(self) -> None:
        req = SubstitutionRequest(
            ingredient="butter",
            dietary_restrictions=["dairy-free"],
            available_ingredients=["coconut oil"],
        )
        assert req.ingredient == "butter"
        assert req.dietary_restrictions == ["dairy-free"]
        assert req.available_ingredients == ["coconut oil"]

    def test_defaults(self) -> None:
        req = SubstitutionRequest(ingredient="butter")
        assert req.dietary_restrictions == []
        assert req.available_ingredients == []

    def test_missing_ingredient_raises(self) -> None:
        with pytest.raises(ValidationError):
            SubstitutionRequest()  # type: ignore[call-arg]


class TestSubstitutionResponse:
    def test_full_response(self) -> None:
        resp = SubstitutionResponse(
            substitute="coconut oil", notes="Good for baking", ratio="1:1"
        )
        assert resp.substitute == "coconut oil"
        assert resp.notes == "Good for baking"
        assert resp.ratio == "1:1"

    def test_defaults(self) -> None:
        resp = SubstitutionResponse(substitute="margarine")
        assert resp.notes is None
        assert resp.ratio is None
