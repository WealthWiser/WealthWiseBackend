# from app.config import supabase

# def get_user_by_id(user_id: str):
#     return supabase.table("users").select("*").eq("id", user_id).execute()

# def get_transactions(user_id: str):
#     return {"table": "coming soon"}
#     # return supabase.table("transactions").select("*").eq("user_id", user_id).execute()

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

engine = create_async_engine(
    DATABASE_URL,
    connect_args={"ssl": True},
    echo=False,
    pool_pre_ping=True
)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
