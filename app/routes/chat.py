# chat.py
from fastapi import APIRouter, Depends, HTTPException, Body
from fastapi.security import HTTPBearer
from app.utils.auth import verify_jwt
from app.aimodels.openai_service import get_chat_response_openai
import logging
from pydantic import BaseModel

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)

# Define a Pydantic model for the request body for better validation
class ChatQuery(BaseModel):
    query: str

@router.post("/query")
async def chat_with_bot(payload: ChatQuery, token: str = Depends(security)):
    user = verify_jwt(token.credentials)

    # Use the unique user ID from the JWT as the session ID
    user_id = user.get('sub')
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    try:
        # 👇 Call the new function with the user_id and the message
        reply = await get_chat_response_openai(user_id=user_id, user_message=payload.query)

        if not reply:
            raise ValueError("Empty response from the AI service")

        return {"reply": reply}

    except Exception as e:
        logger.error(f"Chatbot error for user {user_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="AI service unavailable. Please try again later.")