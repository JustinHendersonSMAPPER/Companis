"""Unit tests for the OAuth authentication service.

These tests mock httpx.AsyncClient and settings to verify that
the auth service correctly builds OAuth URLs and exchanges tokens
for user info without making real HTTP requests.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.auth import (
    FACEBOOK_AUTH_URL,
    FACEBOOK_TOKEN_URL,
    FACEBOOK_USERINFO_URL,
    GOOGLE_AUTH_URL,
    GOOGLE_TOKEN_URL,
    GOOGLE_USERINFO_URL,
    get_oauth_authorization_url,
    get_oauth_user_info,
)


# ---------------------------------------------------------------------------
# get_oauth_authorization_url tests
# ---------------------------------------------------------------------------


class TestGetOAuthAuthorizationUrl:
    @patch("app.services.auth.settings")
    def test_google_returns_url_with_correct_params(self, mock_settings: MagicMock) -> None:
        mock_settings.oauth_redirect_base_url = "http://localhost:8000"
        mock_settings.google_client_id = "google-client-id-123"

        url = get_oauth_authorization_url("google")

        assert url is not None
        assert url.startswith(GOOGLE_AUTH_URL)
        assert "client_id=google-client-id-123" in url
        assert "redirect_uri=http://localhost:8000/api/auth/oauth/google/callback" in url
        assert "response_type=code" in url
        assert "scope=openid email profile" in url
        assert "access_type=offline" in url

    @patch("app.services.auth.settings")
    def test_facebook_returns_url_with_correct_params(self, mock_settings: MagicMock) -> None:
        mock_settings.oauth_redirect_base_url = "http://localhost:8000"
        mock_settings.facebook_client_id = "facebook-client-id-456"

        url = get_oauth_authorization_url("facebook")

        assert url is not None
        assert url.startswith(FACEBOOK_AUTH_URL)
        assert "client_id=facebook-client-id-456" in url
        assert "redirect_uri=http://localhost:8000/api/auth/oauth/facebook/callback" in url
        assert "response_type=code" in url
        assert "scope=email,public_profile" in url

    @patch("app.services.auth.settings")
    def test_unknown_provider_returns_none(self, mock_settings: MagicMock) -> None:
        mock_settings.oauth_redirect_base_url = "http://localhost:8000"
        mock_settings.google_client_id = "some-id"
        mock_settings.facebook_client_id = "some-id"

        result = get_oauth_authorization_url("twitter")

        assert result is None

    @patch("app.services.auth.settings")
    def test_google_without_client_id_returns_none(self, mock_settings: MagicMock) -> None:
        mock_settings.oauth_redirect_base_url = "http://localhost:8000"
        mock_settings.google_client_id = ""

        result = get_oauth_authorization_url("google")

        assert result is None

    @patch("app.services.auth.settings")
    def test_facebook_without_client_id_returns_none(self, mock_settings: MagicMock) -> None:
        mock_settings.oauth_redirect_base_url = "http://localhost:8000"
        mock_settings.facebook_client_id = ""

        result = get_oauth_authorization_url("facebook")

        assert result is None


# ---------------------------------------------------------------------------
# get_oauth_user_info tests
# ---------------------------------------------------------------------------


def _mock_response(status_code: int, json_data: dict) -> MagicMock:
    """Create a mock HTTP response with the given status code and JSON data."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    return resp


@pytest.mark.asyncio
class TestGetOAuthUserInfoGoogle:
    @patch("app.services.auth.settings")
    @patch("httpx.AsyncClient")
    async def test_google_successful_flow(
        self, mock_client_cls: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.oauth_redirect_base_url = "http://localhost:8000"
        mock_settings.google_client_id = "g-client-id"
        mock_settings.google_client_secret = "g-client-secret"

        token_response = _mock_response(200, {"access_token": "google-access-token"})
        user_response = _mock_response(200, {
            "id": "google-user-123",
            "email": "user@gmail.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
        })

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = token_response
        mock_client_instance.get.return_value = user_response
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await get_oauth_user_info("google", "auth-code-123")

        assert result is not None
        assert result["id"] == "google-user-123"
        assert result["email"] == "user@gmail.com"
        assert result["name"] == "Test User"
        assert result["avatar_url"] == "https://example.com/photo.jpg"

        mock_client_instance.post.assert_called_once()
        call_kwargs = mock_client_instance.post.call_args
        assert call_kwargs[0][0] == GOOGLE_TOKEN_URL
        assert call_kwargs[1]["data"]["code"] == "auth-code-123"
        assert call_kwargs[1]["data"]["client_id"] == "g-client-id"
        assert call_kwargs[1]["data"]["client_secret"] == "g-client-secret"
        assert call_kwargs[1]["data"]["grant_type"] == "authorization_code"

        mock_client_instance.get.assert_called_once()
        get_call = mock_client_instance.get.call_args
        assert get_call[0][0] == GOOGLE_USERINFO_URL
        assert get_call[1]["headers"]["Authorization"] == "Bearer google-access-token"

    @patch("app.services.auth.settings")
    @patch("httpx.AsyncClient")
    async def test_google_failed_token_exchange(
        self, mock_client_cls: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.oauth_redirect_base_url = "http://localhost:8000"
        mock_settings.google_client_id = "g-client-id"
        mock_settings.google_client_secret = "g-client-secret"

        token_response = _mock_response(400, {"error": "invalid_grant"})

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = token_response
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await get_oauth_user_info("google", "bad-code")

        assert result is None

    @patch("app.services.auth.settings")
    @patch("httpx.AsyncClient")
    async def test_google_failed_user_info_fetch(
        self, mock_client_cls: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.oauth_redirect_base_url = "http://localhost:8000"
        mock_settings.google_client_id = "g-client-id"
        mock_settings.google_client_secret = "g-client-secret"

        token_response = _mock_response(200, {"access_token": "google-token"})
        user_response = _mock_response(401, {"error": "unauthorized"})

        mock_client_instance = AsyncMock()
        mock_client_instance.post.return_value = token_response
        mock_client_instance.get.return_value = user_response
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await get_oauth_user_info("google", "auth-code")

        assert result is None


@pytest.mark.asyncio
class TestGetOAuthUserInfoFacebook:
    @patch("app.services.auth.settings")
    @patch("httpx.AsyncClient")
    async def test_facebook_successful_flow(
        self, mock_client_cls: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.oauth_redirect_base_url = "http://localhost:8000"
        mock_settings.facebook_client_id = "fb-client-id"
        mock_settings.facebook_client_secret = "fb-client-secret"

        token_response = _mock_response(200, {"access_token": "fb-access-token"})
        user_response = _mock_response(200, {
            "id": "fb-user-789",
            "email": "user@facebook.com",
            "name": "Facebook User",
            "picture": {"data": {"url": "https://example.com/fb-photo.jpg"}},
        })

        mock_client_instance = AsyncMock()
        # Facebook uses GET for both token and user info
        mock_client_instance.get.side_effect = [token_response, user_response]
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await get_oauth_user_info("facebook", "fb-auth-code")

        assert result is not None
        assert result["id"] == "fb-user-789"
        assert result["email"] == "user@facebook.com"
        assert result["name"] == "Facebook User"
        assert result["avatar_url"] == "https://example.com/fb-photo.jpg"

        # Verify token exchange call
        first_get_call = mock_client_instance.get.call_args_list[0]
        assert first_get_call[0][0] == FACEBOOK_TOKEN_URL
        assert first_get_call[1]["params"]["code"] == "fb-auth-code"
        assert first_get_call[1]["params"]["client_id"] == "fb-client-id"
        assert first_get_call[1]["params"]["client_secret"] == "fb-client-secret"

        # Verify user info call
        second_get_call = mock_client_instance.get.call_args_list[1]
        assert second_get_call[0][0] == FACEBOOK_USERINFO_URL
        assert second_get_call[1]["params"]["access_token"] == "fb-access-token"
        assert "id,name,email,picture" in second_get_call[1]["params"]["fields"]

    @patch("app.services.auth.settings")
    @patch("httpx.AsyncClient")
    async def test_facebook_failed_token_exchange(
        self, mock_client_cls: MagicMock, mock_settings: MagicMock
    ) -> None:
        mock_settings.oauth_redirect_base_url = "http://localhost:8000"
        mock_settings.facebook_client_id = "fb-client-id"
        mock_settings.facebook_client_secret = "fb-client-secret"

        token_response = _mock_response(400, {"error": "invalid_code"})

        mock_client_instance = AsyncMock()
        mock_client_instance.get.return_value = token_response
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await get_oauth_user_info("facebook", "bad-code")

        assert result is None


@pytest.mark.asyncio
class TestGetOAuthUserInfoUnknownProvider:
    async def test_unknown_provider_returns_none(self) -> None:
        result = await get_oauth_user_info("twitter", "some-code")

        assert result is None
