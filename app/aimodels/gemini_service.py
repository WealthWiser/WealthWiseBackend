# gemini_service.py
import google.generativeai as genai
import os, asyncio
from concurrent.futures import ThreadPoolExecutor

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel("gemini-1.5-flash")

executor = ThreadPoolExecutor()

async def get_finance_response(user_message: str) -> str:
    prompt = f"""
    You are WealthWise Finance Chatbot. Answer only finance-related questions.
    User: {user_message}
    """

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(executor, model.generate_content, prompt)
    return response.text
