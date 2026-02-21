from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest
from jose import jwt

from app.config import settings
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_password_returns_string(self) -> None:
        hashed = hash_password("mysecretpassword")
        assert isinstance(hashed, str)
        assert hashed != "mysecretpassword"

    def test_hash_password_produces_different_hashes(self) -> None:
        hash1 = hash_password("samepassword")
        hash2 = hash_password("samepassword")
        assert hash1 != hash2  # bcrypt uses random salt

    def test_verify_password_correct(self) -> None:
        hashed = hash_password("testpassword123")
        assert verify_password("testpassword123", hashed) is True

    def test_verify_password_incorrect(self) -> None:
        hashed = hash_password("testpassword123")
        assert verify_password("wrongpassword", hashed) is False

    def test_verify_password_empty_string(self) -> None:
        hashed = hash_password("testpassword123")
        assert verify_password("", hashed) is False

    def test_hash_password_special_characters(self) -> None:
        password = "p@$$w0rd!#%^&*()"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_hash_password_unicode(self) -> None:
        password = "пароль"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_hash_password_long_password(self) -> None:
        # bcrypt truncates at 72 bytes, so use a password within that limit
        password = "a" * 70
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestAccessToken:
    def test_create_access_token_returns_string(self) -> None:
        token = create_access_token({"sub": "user123"})
        assert isinstance(token, str)

    def test_create_access_token_contains_subject(self) -> None:
        token = create_access_token({"sub": "user123"})
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["sub"] == "user123"

    def test_create_access_token_has_type(self) -> None:
        token = create_access_token({"sub": "user123"})
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["type"] == "access"

    def test_create_access_token_has_expiration(self) -> None:
        token = create_access_token({"sub": "user123"})
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert "exp" in payload

    def test_create_access_token_preserves_extra_data(self) -> None:
        token = create_access_token({"sub": "user123", "role": "admin"})
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["role"] == "admin"


class TestRefreshToken:
    def test_create_refresh_token_returns_string(self) -> None:
        token = create_refresh_token({"sub": "user123"})
        assert isinstance(token, str)

    def test_create_refresh_token_has_type(self) -> None:
        token = create_refresh_token({"sub": "user123"})
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        assert payload["type"] == "refresh"

    def test_refresh_token_expires_later_than_access(self) -> None:
        access = create_access_token({"sub": "user123"})
        refresh = create_refresh_token({"sub": "user123"})
        access_payload = jwt.decode(
            access, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        refresh_payload = jwt.decode(
            refresh, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        assert refresh_payload["exp"] > access_payload["exp"]


class TestDecodeToken:
    def test_decode_valid_access_token(self) -> None:
        token = create_access_token({"sub": "user123"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["type"] == "access"

    def test_decode_valid_refresh_token(self) -> None:
        token = create_refresh_token({"sub": "user123"})
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"

    def test_decode_invalid_token(self) -> None:
        payload = decode_token("invalid.token.string")
        assert payload is None

    def test_decode_empty_token(self) -> None:
        payload = decode_token("")
        assert payload is None

    def test_decode_expired_token(self) -> None:
        expired_data = {
            "sub": "user123",
            "exp": datetime.now(UTC) - timedelta(hours=1),
            "type": "access",
        }
        token = jwt.encode(expired_data, settings.secret_key, algorithm=settings.jwt_algorithm)
        payload = decode_token(token)
        assert payload is None

    def test_decode_token_wrong_secret(self) -> None:
        token = jwt.encode(
            {"sub": "user123", "type": "access"},
            "wrong-secret-key",
            algorithm=settings.jwt_algorithm,
        )
        payload = decode_token(token)
        assert payload is None
