from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from fastapi.security import HTTPBearer
from app.utils.auth import verify_jwt
from app.utils.transactions.read_pdf import extract_transactions_from_uploaded_bytes
from typing import Optional
router = APIRouter()
security = HTTPBearer()

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
            transactions = extract_transactions_from_uploaded_bytes(pdf_bytes, password)

            return JSONResponse(content=jsonable_encoder({"transactions": transactions}))
        except ValueError as ve:
            # For invalid password or custom errors raised by helper
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))