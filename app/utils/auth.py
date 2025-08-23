import jwt
import os
from fastapi import HTTPException
from dotenv import load_dotenv
load_dotenv()
SECRET = os.getenv("JWT_SECRET")
ALGORITHM = "HS256"
def verify_jwt(token: str):
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGORITHM], audience="authenticated")
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
