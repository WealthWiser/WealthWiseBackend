from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer
from app.utils.auth import verify_jwt
from app.aimodels.gemini_service import get_finance_response
import logging

router = APIRouter()
security = HTTPBearer()

logger = logging.getLogger(__name__)

@router.post("/query")
async def chat_with_bot(message: dict, token: str = Depends(security)):
    user = verify_jwt(token.credentials)
    if user:
        user_message = message.get("query")
        if not user_message:
            raise HTTPException(status_code=400, detail="Missing query in request")

        try:
            reply = await get_finance_response(user_message)
            if not reply:
                raise ValueError("Empty response from Gemini")

            # ✅ Apply formatting/length limits here
            # reply = format_message(reply)

            return {"reply": reply}

        except Exception as e:
            logger.error(f"Chatbot error: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="AI service unavailable right now. Please try again later.")
