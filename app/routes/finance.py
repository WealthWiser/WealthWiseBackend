from fastapi import APIRouter, Depends
from app.database import get_transactions
from fastapi.security import HTTPBearer
from app.utils.auth import verify_jwt

router = APIRouter()
security = HTTPBearer()

@router.get("/summary")
def finance_summary(token: str = Depends(security)):
    user = verify_jwt(token.credentials)
    txns = get_transactions(user["id"]).data
    return {"summary": {"transactions": txns, "cashflow": "🚧 To be calculated"}}
