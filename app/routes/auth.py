from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import timedelta
import datetime

from app.database import get_db
from app.models.db import User, RefreshToken
from app.models.auth import (
    SignupRequest,
    LoginRequest,
    TokenResponse,
    RefreshRequest,
)
from app.utils.security import hash_password, verify_password
from app.utils.auth import create_access_token
from app.utils.login_audit import log_login_attempt
from app.utils.refresh_tokens import (
    generate_refresh_token,
    hash_refresh_token,
)
from app.utils.dependencies import get_current_user_id

router = APIRouter()
REFRESH_TOKEN_EXPIRE_DAYS = 30

@router.post("/signup", response_model=TokenResponse)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db)):
    existing = await db.execute(
        select(User).where(User.email == data.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        dob=data.dob,
        country=data.country,
        gender=data.gender
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    access_token = create_access_token(str(user.id))
    refresh_token = generate_refresh_token()

    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=datetime.datetime.now(datetime.timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )

    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, request:Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.email == data.email)
    )
    user = result.scalar_one_or_none()
    success = user and verify_password(data.password, user.password_hash)
    await log_login_attempt(
        db=db,
        user_id=str(user.id) if user else None,
        success=bool(success),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(str(user.id))
    refresh_token = generate_refresh_token()
    await db.execute(
        update(RefreshToken)
        .where(
            RefreshToken.user_id == user.id,
            RefreshToken.revoked == False
        )
        .values(revoked=True)
    )
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(refresh_token),
            expires_at=datetime.datetime.now(datetime.timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    token_hash = hash_refresh_token(data.refresh_token)

    result = await db.execute(
        select(RefreshToken).where(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False,
            RefreshToken.expires_at > datetime.datetime.now(datetime.timezone.utc),
        )
    )

    stored = result.scalar_one_or_none()

    if not stored:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    stored.revoked = True
    new_refresh_token = generate_refresh_token()
    new_refresh_hash = hash_refresh_token(new_refresh_token)

    db.add(
        RefreshToken(
            user_id=stored.user_id,
            token_hash=new_refresh_hash,
            expires_at=datetime.datetime.now(datetime.timezone.utc)
            + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
        )
    )

    await db.commit()

    new_access_token = create_access_token(str(stored.user_id))

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )

@router.post("/logout")
async def logout(
    data: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    token_hash = hash_refresh_token(data.refresh_token)

    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    token = result.scalar_one_or_none()

    if token:
        token.revoked = True
        await db.commit()

    return {"message": "Logged out successfully"}

@router.get("/me")
async def me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "created_at": user.created_at,
    }
