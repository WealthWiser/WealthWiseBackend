from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db import LoginAudit
from typing import Optional

async def log_login_attempt(
    db: AsyncSession,
    user_id: Optional[str],
    success: bool,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
):
    audit = LoginAudit(
        user_id=user_id,
        success=success,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(audit)
    await db.commit()