# gemini_service.py
import google.generativeai as genai
import os
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from openai import AsyncOpenAI


# --- Configuration & Initialization ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set.")

# Initialize the async client
client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# --- New Function ---

async def generate_structured_response_openai(prompt: str) -> str:
    """
    For one-off, complex prompts that require a structured JSON response.
    This function uses OpenAI's JSON mode for reliable output.
    """
    try:
        response = await client.chat.completions.create(
            model="gpt-3.5-turbo",  # Or "gpt-3.5-turbo" for a faster, cheaper option
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful financial advisor API that returns responses in valid JSON format."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        print(f"Error in generating structured response from OpenAI: {e}")
        # Return a stringified JSON error to maintain type consistency
        return json.dumps({"error": "Failed to get response from OpenAI", "details": str(e)})


# --- Configuration & Initialization ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")
genai.configure(api_key=GEMINI_API_KEY)

# Use a longer-lived model for better context in chats
model = genai.GenerativeModel("gemini-1.5-pro-latest")

# A simple in-memory store for active chat sessions.
# Key: user_id (str), Value: ChatSession object
chat_sessions = {}

# --- New Functions ---

async def generate_structured_response(prompt: str) -> str:
    """
    For one-off, complex prompts that require a structured response (e.g., JSON).
    This function does NOT use chat history.
    """
    try:
        # We run the synchronous SDK call in a thread pool to avoid blocking asyncio
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as pool:
            response = await loop.run_in_executor(
                pool,
                lambda: model.generate_content(prompt)
            )
        return response.text
    except Exception as e:
        print(f"Error in generating structured response: {e}")
        return ""

async def get_chat_response(user_id: str, user_message: str) -> str:
    """
    Handles conversational chat, maintaining history for each user.
    """
    global chat_sessions

    # Get or create a chat session for the user
    if user_id not in chat_sessions:
        # Define the chatbot's personality and instructions for the start of the conversation
        system_instruction = """
        You are WealthWise, a friendly and helpful financial assistant.
        Your primary role is to answer questions related to finance, investing, budgeting, and market trends in India.
        If a user asks a question unrelated to finance, politely steer the conversation back to financial topics.
        Keep your answers concise and easy to understand.
        """
        chat_sessions[user_id] = model.start_chat(
            history=[],
            # The system instruction is a better way to set the persona
            # We can now set it using the 'system_instruction' parameter with GenerativeModel
        )
        # For older versions or models without system_instruction, you can prime the history:
        # chat_sessions[user_id].history.append({'role': 'user', 'parts': ["Let's start our chat."]})
        # chat_sessions[user_id].history.append({'role': 'model', 'parts': [system_instruction]})

    chat = chat_sessions[user_id]

    try:
        # Asynchronously send the message
        response = await chat.send_message_async(user_message)
        return response.text
    except Exception as e:
        print(f"Error in chat response for user {user_id}: {e}")
        # Optional: clean up failed session
        # del chat_sessions[user_id]
        return "Sorry, I encountered a problem. Please try asking again."