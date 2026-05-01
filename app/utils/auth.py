from fastapi import HTTPException, status
from datetime import timedelta
import datetime
from jose import jwt, JWTError, ExpiredSignatureError
from google.oauth2 import id_token
from google.auth.transport import requests
from dotenv import load_dotenv
from typing import Any
import os
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
GOOGLE_CLIENT_ID = os.getenv("WEB_CLIENT_ID")

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not set")

def validate_google_idtoken(idtoken: str) -> dict[str, Any]:
    try:
        idinfo = id_token.verify_oauth2_token(idtoken, requests.Request(), GOOGLE_CLIENT_ID)
        user_email = idinfo.get('email')
        user_picture = idinfo.get('picture')
        google_sub_id = idinfo.get('sub')
        user_given_name = idinfo.get('given_name')
        user_family_name = idinfo.get('family_name')
        is_email_verified = idinfo.get('email_verified')
        if not is_email_verified: raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google email not verified")
        else:
            return {
                "g_email": user_email,
                "g_picture": user_picture,
                "g_sub_id": google_sub_id,
                "g_given_name": user_given_name,
                "g_family_name": user_family_name,
            }
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid Google Token")

def create_access_token(user_id: str) -> str:
    expire = datetime.datetime.now(datetime.timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "access"
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        return payload.get("sub")

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="TOKEN_EXPIRED"
        )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="INVALID_TOKEN"
    )
