from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from sqlalchemy import select, update
from app.utils.dependencies import get_current_user_id
from app.models.db import User

router = APIRouter()

@router.get("/me")
async def me(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    print(user)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "id": str(user.id),
        "name": user.first_name,
        "email": user.email,
        "created_at": user.created_at,
        "gender": user.gender,
        "country": user.country,
        "dob" : user.dob,
    }