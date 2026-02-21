from __future__ import annotations

from typing import Any

import httpx

from app.config import settings

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

FACEBOOK_AUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
FACEBOOK_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
FACEBOOK_USERINFO_URL = "https://graph.facebook.com/me"


def get_oauth_authorization_url(provider: str) -> str | None:
    redirect_uri = f"{settings.oauth_redirect_base_url}/api/auth/oauth/{provider}/callback"

    if provider == "google" and settings.google_client_id:
        params = {
            "client_id": settings.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
        }
        return f"{GOOGLE_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    if provider == "facebook" and settings.facebook_client_id:
        params = {
            "client_id": settings.facebook_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "email,public_profile",
        }
        return f"{FACEBOOK_AUTH_URL}?{'&'.join(f'{k}={v}' for k, v in params.items())}"

    return None


async def get_oauth_user_info(provider: str, code: str) -> dict[str, Any] | None:
    redirect_uri = f"{settings.oauth_redirect_base_url}/api/auth/oauth/{provider}/callback"

    if provider == "google":
        return await _get_google_user_info(code, redirect_uri)
    if provider == "facebook":
        return await _get_facebook_user_info(code, redirect_uri)
    return None


async def _get_google_user_info(code: str, redirect_uri: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
        )
        if token_resp.status_code != 200:
            return None

        access_token = token_resp.json().get("access_token")
        user_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if user_resp.status_code != 200:
            return None

        data = user_resp.json()
        return {
            "id": data["id"],
            "email": data["email"],
            "name": data.get("name", ""),
            "avatar_url": data.get("picture"),
        }


async def _get_facebook_user_info(code: str, redirect_uri: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient() as client:
        token_resp = await client.get(
            FACEBOOK_TOKEN_URL,
            params={
                "code": code,
                "client_id": settings.facebook_client_id,
                "client_secret": settings.facebook_client_secret,
                "redirect_uri": redirect_uri,
            },
        )
        if token_resp.status_code != 200:
            return None

        access_token = token_resp.json().get("access_token")
        user_resp = await client.get(
            FACEBOOK_USERINFO_URL,
            params={
                "fields": "id,name,email,picture",
                "access_token": access_token,
            },
        )
        if user_resp.status_code != 200:
            return None

        data = user_resp.json()
        return {
            "id": data["id"],
            "email": data.get("email", ""),
            "name": data.get("name", ""),
            "avatar_url": data.get("picture", {}).get("data", {}).get("url"),
        }
