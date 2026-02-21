from __future__ import annotations

from app.schemas.legal import TERMS_AND_CONDITIONS


class TestTermsAndConditions:
    def test_terms_not_empty(self) -> None:
        assert len(TERMS_AND_CONDITIONS) > 0

    def test_terms_contains_ai_disclaimer(self) -> None:
        assert "AI-GENERATED CONTENT" in TERMS_AND_CONDITIONS

    def test_terms_contains_allergy_warning(self) -> None:
        assert "ALLERGY" in TERMS_AND_CONDITIONS
        assert "allergen" in TERMS_AND_CONDITIONS.lower()

    def test_terms_contains_liability_limitation(self) -> None:
        assert "LIMITATION OF LIABILITY" in TERMS_AND_CONDITIONS

    def test_terms_contains_user_responsibility(self) -> None:
        assert "USER RESPONSIBILITY" in TERMS_AND_CONDITIONS

    def test_terms_contains_no_medical_advice(self) -> None:
        assert "NO MEDICAL" in TERMS_AND_CONDITIONS

    def test_terms_contains_indemnification(self) -> None:
        assert "INDEMNIFICATION" in TERMS_AND_CONDITIONS

    def test_terms_contains_assumption_of_risk(self) -> None:
        assert "ASSUMPTION OF RISK" in TERMS_AND_CONDITIONS

    def test_terms_mentions_independently_verify(self) -> None:
        assert "INDEPENDENTLY VERIFY" in TERMS_AND_CONDITIONS

    def test_terms_mentions_healthcare_professionals(self) -> None:
        assert "healthcare" in TERMS_AND_CONDITIONS.lower()
