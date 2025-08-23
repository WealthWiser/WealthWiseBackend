from fastapi import FastAPI
from app.routes import auth, chat # user, finance

app = FastAPI(title="WealthWise Backend", version="1.0.0")

# # Register routes
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
# app.include_router(user.router, prefix="/user", tags=["User"])
# app.include_router(finance.router, prefix="/finance", tags=["Finance"])
app.include_router(chat.router, prefix="/chat", tags=["Chatbot"])

@app.get("/")
def root():
    return {"message": "WealthWise Backend is running 🚀"}
