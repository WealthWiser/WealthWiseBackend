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
    GoogleLoginRequest,
)
from app.utils.security import hash_password, verify_password
from app.utils.auth import create_access_token, validate_google_idtoken
from app.utils.login_audit import log_login_attempt
from app.utils.refresh_tokens import (
    generate_refresh_token,
    hash_refresh_token,
)

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

@router.post("/google", response_model=TokenResponse)
async def googleSignin(data: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    try:
        user = validate_google_idtoken(data.id_token) # user's email is verified and data is sent now
        #  check if user with user['g_email'] exits in db
        existing_user = await db.execute(select(User).where(User.email == user['g_email']))
        existing_user = existing_user.scalar_one_or_none()
        # CASE A: user's email is there in DB(users)
        if existing_user:
            # since user's email is there in the DB user mush have a password account before now connecting his google account
            # we also need to check if he has a google login data in the table auth_user_providers
            # case 1: User is first time google sign in
                # link the user_id as a foreign key in auth_user_providers
                # insert the user's data into the table auth_user_providers return {jwt,refresh_token}
            # case 2: User is not first time google sing in
                #  verify the user's sub update the profile picture etc send the data back
                #  send the jwt and refresh now
            pass

        # CASE B: user's emails is not there in DB(users)
        else:
            #
            pass

        pass
    except Exception:
        print(Exception)
        return HTTPException(status_code=500, detail="Server Error")

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
