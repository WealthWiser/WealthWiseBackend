from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from typing import Literal, Optional
from app.utils.advice_generator import generate_investment_advice
from app.utils.auth import verify_jwt
from app.utils.transactions.read_pdf import extract_transactions_from_uploaded_bytes
from app.config import supabase
router = APIRouter()
security = HTTPBearer()

class AdviceRequest(BaseModel):
    risk_profile: Literal["Low", "Moderate", "High"]
    investment_goal: str = Field(..., example="Wealth Creation")
    investment_horizon: str = Field(..., example="Long-term (7+ years)")
# @router.get("/summary")
# def finance_summary(token: str = Depends(security)):
#     user = verify_jwt(token.credentials)
#     txns = get_transactions(user["id"]).data
#     return {"summary": {"transactions": txns, "cashflow": "🚧 To be calculated"}}


@router.post("/extract-transactions")
async def parse_transactions(token: str = Depends(security), pdf: UploadFile = File(...), password: Optional[str] = Form(None),):
    user = verify_jwt(token.credentials)
    if user:
        try:
            pdf_bytes = await pdf.read()
            # Use your helper function
            transactions = extract_transactions_from_uploaded_bytes(pdf_bytes, password=password, user_id=user['sub'])

            # now insert the transactions into the database
            rows = []
            for txn in transactions:
                rows.append({
                    "txn_date": txn['date'],
                    "description": txn["description"],
                    "debit": txn["debit"],
                    "credit": txn["credit"],
                    "amount": txn["amount"],
                    "balance": txn["balance"],
                    "user_id": txn["user_id"],
                    "category": txn["categories"],
                })

            response = supabase.table("transactions").insert(rows).execute()
            print(response)

            return JSONResponse(content=jsonable_encoder({"transactions": transactions}))
        except ValueError as ve:
            # For invalid password or custom errors raised by helper
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))



@router.post("/generate-advice", response_model=dict)
async def get_investment_advice(request: AdviceRequest, token: str = Depends(security)):
    """
    Generates personalized investment advice based on user profile, goals,
    and live market data.
    """
    try:
        user = verify_jwt(token.credentials)
        user_id = user.get('sub')
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Call the enhanced service with all the required parameters
        advice_data = await generate_investment_advice(
            user_id=user_id,
            risk_profile=request.risk_profile,
            investment_goal=request.investment_goal,
            investment_horizon=request.investment_horizon
        )

        if "error" in advice_data:
            raise HTTPException(status_code=503, detail=advice_data["error"])

        return advice_data

    except HTTPException as http_exc:
        # Re-raise HTTPException to let FastAPI handle it
        raise http_exc
    except Exception as e:
        print(f"An unexpected error occurred in generate-advice endpoint: {e}")
        raise HTTPException(status_code=500, detail="An unexpected internal error occurred.")