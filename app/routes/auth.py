from fastapi import APIRouter, Depends
from fastapi.security import HTTPBearer
from app.utils.auth import verify_jwt

router = APIRouter()
security = HTTPBearer()

@router.get("/me")
def get_profile(token: str = Depends(security)):
    payload = verify_jwt(token.credentials)
    return {"user": payload}
