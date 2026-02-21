from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.household import FamilyMember, Household
from app.models.user import User
from app.schemas.user import TokenRefresh, TokenResponse, UserCreate, UserLogin, UserResponse
from app.utils.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)

router = APIRouter()


@router.get("/terms")
async def get_terms() -> dict[str, str]:
    from app.schemas.legal import TERMS_AND_CONDITIONS

    return {"terms_text": TERMS_AND_CONDITIONS, "version": "1.0"}


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)) -> User:
    if not user_data.terms_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must accept the terms and conditions to create an account",
        )

    result = await db.execute(select(User).where(User.email == user_data.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        auth_provider="local",
        terms_accepted=True,
        terms_version="1.0",
    )
    db.add(user)
    await db.flush()

    household = Household(name=f"{user_data.full_name}'s Kitchen", owner_id=user.id)
    db.add(household)
    await db.flush()

    member = FamilyMember(
        household_id=household.id, user_id=user.id, name=user_data.full_name, role="owner"
    )
    db.add(member)
    await db.flush()

    return user


@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)) -> dict[str, str]:
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()

    if user is None or user.hashed_password is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return {
        "access_token": create_access_token({"sub": user.id}),
        "refresh_token": create_refresh_token({"sub": user.id}),
        "token_type": "bearer",
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh, db: AsyncSession = Depends(get_db)
) -> dict[str, str]:
    payload = decode_token(token_data.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )

    return {
        "access_token": create_access_token({"sub": user.id}),
        "refresh_token": create_refresh_token({"sub": user.id}),
        "token_type": "bearer",
    }


@router.post("/oauth/{provider}/callback", response_model=TokenResponse)
async def oauth_callback(
    provider: str,
    code: str,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    if provider not in ("google", "facebook"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported OAuth provider: {provider}",
        )

    from app.services.auth import get_oauth_user_info

    user_info = await get_oauth_user_info(provider, code)
    if user_info is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authenticate with OAuth provider",
        )

    result = await db.execute(
        select(User).where(
            User.auth_provider == provider,
            User.auth_provider_id == user_info["id"],
        )
    )
    user = result.scalar_one_or_none()

    if user is None:
        email_result = await db.execute(select(User).where(User.email == user_info["email"]))
        existing_user = email_result.scalar_one_or_none()
        if existing_user:
            existing_user.auth_provider = provider
            existing_user.auth_provider_id = user_info["id"]
            user = existing_user
        else:
            user = User(
                email=user_info["email"],
                full_name=user_info.get("name", ""),
                avatar_url=user_info.get("avatar_url"),
                auth_provider=provider,
                auth_provider_id=user_info["id"],
                is_verified=True,
            )
            db.add(user)
            await db.flush()

            household = Household(
                name=f"{user_info.get('name', 'My')}'s Kitchen", owner_id=user.id
            )
            db.add(household)
            await db.flush()

            member = FamilyMember(
                household_id=household.id,
                user_id=user.id,
                name=user_info.get("name", ""),
                role="owner",
            )
            db.add(member)
            await db.flush()

    return {
        "access_token": create_access_token({"sub": user.id}),
        "refresh_token": create_refresh_token({"sub": user.id}),
        "token_type": "bearer",
    }


@router.get("/oauth/{provider}/url")
async def get_oauth_url(provider: str) -> dict[str, str]:
    from app.services.auth import get_oauth_authorization_url

    url = get_oauth_authorization_url(provider)
    if url is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth not configured for provider: {provider}",
        )
    return {"authorization_url": url}
